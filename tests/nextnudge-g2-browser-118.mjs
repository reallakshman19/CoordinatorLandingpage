// G2 real-browser pilot of a local, disposable PR checkout via Chrome DevTools Protocol.
// Real pointer and keyboard events; no production issues, writes, agent impersonation or release.
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import http from 'node:http';
import {spawn,spawnSync} from 'node:child_process';
import {once} from 'node:events';
import {createHash} from 'node:crypto';
const root=path.resolve(new URL('..',import.meta.url).pathname);
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const chromeCandidates=[process.env.CHROME_BIN,'chromium','google-chrome','google-chrome-stable','chromium-browser'].filter(Boolean);
const browser=chromeCandidates.find(p=>spawnSync('which',[p],{encoding:'utf8'}).status===0);
async function server(){
  const mime={'.html':'text/html','.mjs':'text/javascript','.js':'text/javascript','.json':'application/json','.css':'text/css','.md':'text/plain'};
  const web=http.createServer((req,res)=>{
    const pathname=decodeURIComponent(new URL(req.url,'http://localhost').pathname);
    const file=path.resolve(root,'.'+pathname);
    if(!file.startsWith(root+path.sep)){res.writeHead(403).end();return;}
    fs.readFile(file,(err,data)=>{if(err){res.writeHead(404).end();return;}
      res.writeHead(200,{'Content-Type':mime[path.extname(file)]||'application/octet-stream',
        'Cache-Control':'no-store'});res.end(data);});
  });
  web.listen(0,'127.0.0.1');await once(web,'listening');
  return {web,url:'http://127.0.0.1:'+web.address().port+'/site/nextnudge/index.html'};
}
async function chromiumTab(profile,child){
  for(let i=0;i<200;i++){
    if(child.exitCode!==null)throw Error('Chromium exited before DevTools: '+child.exitCode);
    try{
      const port=Number(fs.readFileSync(path.join(profile,'DevToolsActivePort'),'utf8').split('\n')[0]);
      if(Number.isSafeInteger(port)&&port>0){
        const response=await fetch('http://127.0.0.1:'+port+'/json/list');
        const page=(await response.json()).find(x=>x.type==='page'&&x.url.includes('nextnudge'));
        if(page)return page;
      }
    }catch{}await sleep(250);
  }
  throw Error('Chromium DevTools endpoint unavailable after profile startup');
}
async function cleanBrowser(child,web,profile,ws){
  ws?.close();child.kill('SIGKILL');
  if(child.exitCode===null)await Promise.race([once(child,'exit').catch(()=>{}),sleep(5000)]);
  web.close();
  try{fs.rmSync(profile,{recursive:true,force:true,maxRetries:15,retryDelay:200});}
  catch(e){console.log('G2_PROFILE_CLEANUP_WARNING '+e.message);}
}

class CDP{
  constructor(ws){this.ws=ws;this.seq=0;this.pending=new Map();this.errors=[];ws.addEventListener('message',evt=>{
    const m=JSON.parse(evt.data);
    if(m.method==='Runtime.exceptionThrown')this.errors.push(JSON.stringify(m.params.exceptionDetails));
    if(m.id){const p=this.pending.get(m.id);if(p){this.pending.delete(m.id);if(m.error)p.reject(Error(m.error.message));else p.resolve(m.result);}}
  });}
  send(method,params={}){const id=++this.seq;return new Promise((resolve,reject)=>{this.pending.set(id,{resolve,reject});this.ws.send(JSON.stringify({id,method,params}));});}
  async eval(expr){const x=await this.send('Runtime.evaluate',{expression:expr,returnByValue:true,awaitPromise:true});
    if(x.exceptionDetails)throw Error('Browser expression: '+JSON.stringify(x.exceptionDetails));
    return x.result?.value;}
  async until(expr,timeout=12000){const start=Date.now();while(Date.now()-start<timeout){if(await this.eval(expr))return;await sleep(150);}throw Error('Browser timed out: '+expr);}
  async click(selector){
    const bounds=await this.eval('(()=>{const x=document.querySelector('+JSON.stringify(selector)+');if(!x)return null;x.scrollIntoView({block:"center"});const b=x.getBoundingClientRect();return {x:b.left+b.width/2,y:b.top+b.height/2,w:b.width,h:b.height};})()');
    if(!bounds||bounds.w<1||bounds.h<1)throw Error('Not visible for pointer: '+selector);
    const {x,y}=bounds;await this.send('Input.dispatchMouseEvent',{type:'mouseMoved',x,y});
    await this.send('Input.dispatchMouseEvent',{type:'mousePressed',x,y,button:'left',clickCount:1});
    await this.send('Input.dispatchMouseEvent',{type:'mouseReleased',x,y,button:'left',clickCount:1});}
  async type(selector,text){await this.click(selector);await this.send('Input.insertText',{text});}
  async snap(label){const html=await this.eval('document.querySelector("#panel")?.innerText.slice(0,800)');
    const route=await this.eval('window.location.search');return {label,route,view:html};}
}
test('P01/P02/P03 actual Chromium pointer-flow, project editor and agent fixtures (candidate checkout, local-only)',{timeout:110000},async t=>{
  if(!browser){console.log('P01_BROWSER_NOT_RUN Chrome/Chromium executable absent');t.skip('Browser executable unavailable');return;}
  const {web,url}=await server(),profile=fs.mkdtempSync(path.join(os.tmpdir(),'nn118-g2-'));
  const cp=spawn(browser,['--headless=new','--no-sandbox','--disable-dev-shm-usage','--disable-gpu',
    '--window-size=1300,1000','--remote-debugging-port=0','--user-data-dir='+profile,url],{stdio:'ignore'});
  const trace=[];let cdp;
  try{
    const info=await chromiumTab(profile,cp);
    const ws=new WebSocket(info.webSocketDebuggerUrl);
    await new Promise((resolve,reject)=>{ws.addEventListener('open',resolve,{once:true});ws.addEventListener('error',reject,{once:true});});
    cdp=new CDP(ws);await cdp.send('Runtime.enable');await cdp.send('Page.enable');
    const version=await cdp.send('Browser.getVersion');trace.push({browser:version.product,url});
    await cdp.until('document.querySelector("#panel h2")?.textContent==="Projects"',18000);
    trace.push(await cdp.snap('P01: Projects landed'));
    await cdp.type('#new-project input[name="name"]','P118-ALPHA');
    await cdp.click('#new-project button[type="submit"]');
    await cdp.until('document.querySelector("#panel h2")?.textContent==="P118-ALPHA"');
    trace.push(await cdp.snap('P01: selected ALPHA'));
    await cdp.type('#new-thread input[name="agent"]','P118-G1');
    await cdp.type('#new-thread input[name="title"]','G1 pilot task');
    await cdp.type('#new-thread textarea[name="goal"]','Preserve the Owner intent');
    await cdp.click('#new-thread button[type="submit"]');
    await cdp.until('!!document.querySelector("nav.workspace-tabs")');
    trace.push(await cdp.snap('P01: agent G1 Overview'));
    for(const mode of ['ground','task','correction','reconcile']){
      await cdp.click('[data-action="workspace-'+mode+'"]');
      await cdp.until('document.querySelector("[aria-current=page]")?.dataset.action==="workspace-'+mode+'"');
      trace.push(await cdp.snap('P01: '+mode));
    }
    await cdp.click('[data-action="thread"]');await cdp.until('document.querySelector("[aria-current=page]")?.dataset.action==="thread"');
    await cdp.click('[data-action="back"]');await cdp.until('document.querySelector("#panel h2")?.textContent==="P118-ALPHA"');
    await cdp.click('[data-action="project-grounding"]');await cdp.until('!!document.querySelector("#project-grounding-form")');
    await cdp.type('#project-grounding-form textarea[name="ground-1f"]','P118-ALPHA-ONLY-GROUND');
    await cdp.click('#project-grounding-form button[type="submit"]');
    await cdp.until('!!JSON.parse(localStorage.getItem("nextnudge.projects.v1"))[Object.keys(JSON.parse(localStorage.getItem("nextnudge.projects.v1")))[0]].fixtures["1f"]');
    trace.push(await cdp.snap('P02: ALPHA fixture saved'));
    await cdp.click('[data-action="project"]');
    await cdp.type('#new-thread input[name="agent"]','P118-G2');
    await cdp.type('#new-thread input[name="title"]','G2 pilot task');
    await cdp.type('#new-thread textarea[name="goal"]','Check shared context');
    await cdp.click('#new-thread button[type="submit"]');
    await cdp.click('[data-action="workspace-ground"]');
    await cdp.until('!!document.querySelector("#workspace-form")');
    const brief=await cdp.eval('document.querySelector("#workspace-form [name=brief]")?.value');
    assert.equal(brief,'P118-ALPHA-ONLY-GROUND');
    trace.push(await cdp.snap('P02: G2 sees shared ALPHA context'));
    await cdp.send('Page.reload',{ignoreCache:true});
    await cdp.until('document.querySelector("#workspace-form [name=brief]")?.value==="P118-ALPHA-ONLY-GROUND"',18000);
    trace.push(await cdp.snap('P02: G2 after real browser reload'));
    await cdp.click('[data-action="thread"]');await cdp.click('[data-action="back"]');
    await cdp.until('document.querySelector("#panel h2")?.textContent==="P118-ALPHA"');
    await cdp.type('#new-thread input[name="agent"]','P118-G1');
    await cdp.type('#new-thread input[name="title"]','ILLEGAL duplicate G1');
    await cdp.type('#new-thread textarea[name="goal"]','Should never be created');
    await cdp.click('#new-thread button[type="submit"]');
    await cdp.until('document.querySelector("#notice")?.textContent.includes("already has a project thread")');
    trace.push(await cdp.snap('P04: duplicate ALPHA/G1 blocked'));
    const alphaCount=await cdp.eval('Object.values(JSON.parse(localStorage.getItem("nextnudge.projects.v1"))).find(p=>p.name==="P118-ALPHA").threads.length');
    assert.equal(alphaCount,2,'failed duplicate must not add a thread');
    await cdp.click('[data-action="project-grounding"]');
    await cdp.click('#project-grounding-form textarea[name="ground-1f"]');
    await cdp.send('Input.dispatchKeyEvent',{type:'keyDown',key:'a',code:'KeyA',modifiers:2,windowsVirtualKeyCode:65});
    await cdp.send('Input.dispatchKeyEvent',{type:'keyUp',key:'a',code:'KeyA',modifiers:2,windowsVirtualKeyCode:65});
    await cdp.send('Input.insertText',{text:'P118-ALPHA-ONLY-GROUND-V2'});
    await cdp.click('#project-grounding-form button[type="submit"]');
    const alphaV2=await cdp.eval('Object.values(JSON.parse(localStorage.getItem("nextnudge.projects.v1"))).find(p=>p.name==="P118-ALPHA").fixtures["1f"]');
    assert.equal(alphaV2,'P118-ALPHA-ONLY-GROUND-V2');
    trace.push(await cdp.snap('P02: second local shared fixture version'));
    await cdp.click('[data-action="project"]');await cdp.click('[data-action="projects"]');
    await cdp.until('document.querySelector("#panel h2")?.textContent==="Projects"');
    await cdp.type('#new-project input[name="name"]','P118-BETA');await cdp.click('#new-project button[type="submit"]');
    await cdp.until('document.querySelector("#panel h2")?.textContent==="P118-BETA"');
    await cdp.type('#new-thread input[name="agent"]','P118-G1');
    await cdp.type('#new-thread input[name="title"]','BETA agent task');
    await cdp.type('#new-thread textarea[name="goal"]','Maintain project isolation');
    await cdp.click('#new-thread button[type="submit"]');
    await cdp.click('[data-action="workspace-ground"]');
    await cdp.until('!!document.querySelector("#workspace-form")');
    const beta=await cdp.eval('document.querySelector("#workspace-form [name=brief]")?.value');
    assert.notEqual(beta,'P118-ALPHA-ONLY-GROUND');
    const locally=await cdp.eval('JSON.parse(localStorage.getItem("nextnudge.projects.v1"))');
    const entries=Object.values(locally);
    assert.equal(entries.length,2);
    assert.equal(entries.find(p=>p.name==='P118-ALPHA').fixtures['1f'],'P118-ALPHA-ONLY-GROUND-V2');
    assert.deepEqual(entries.find(p=>p.name==='P118-BETA').fixtures,{});
    trace.push(await cdp.snap('P03: BETA separate G1 thread, no ALPHA context'));
    await cdp.click('[data-action="thread"]');await cdp.click('[data-action="back"]');
    await cdp.click('[data-action="project-grounding"]');
    await cdp.type('#project-grounding-form textarea[name="ground-1f"]','P118-BETA-NEVER-IN-ALPHA');
    await cdp.click('#project-grounding-form button[type="submit"]');
    await cdp.click('[data-action="project"]');
    const betaG1=await cdp.eval('Object.values(JSON.parse(localStorage.getItem("nextnudge.projects.v1"))).find(p=>p.name==="P118-BETA").threads[0].id');
    await cdp.click('[data-open="'+betaG1+'"]');
    await cdp.click('[data-action="workspace-ground"]');
    await cdp.until('!!document.querySelector("#workspace-form [name=brief]")');
    const betaPreservedDraft=await cdp.eval('document.querySelector("#workspace-form [name=brief]")?.value');
    assert.equal(betaPreservedDraft,'','BETA previous blank unsent Ground draft remains unsent');
    await cdp.click('[data-action="grounding"]');
    await cdp.until('!!document.querySelector("#project-grounding-form")');
    const betaLibrary=await cdp.eval('document.querySelector("#project-grounding-form [name=ground-1f]")?.value');
    assert.equal(betaLibrary,'P118-BETA-NEVER-IN-ALPHA','BETA current shared fixture matches owner edit');
    assert.notEqual(betaLibrary,'P118-ALPHA-ONLY-GROUND-V2');
    trace.push(await cdp.snap('P03: BETA/G1 sees current BETA library; old Ground draft preserved'));
    await cdp.click('[data-action="project"]');await cdp.click('[data-action="projects"]');
    const alphaG2=await cdp.eval('Object.values(JSON.parse(localStorage.getItem("nextnudge.projects.v1"))).find(p=>p.name==="P118-ALPHA").threads[1].id');
    const alphaID=await cdp.eval('Object.values(JSON.parse(localStorage.getItem("nextnudge.projects.v1"))).find(p=>p.name==="P118-ALPHA").id');
    await cdp.click('[data-project="'+alphaID+'"]');await cdp.click('[data-open="'+alphaG2+'"]');
    await cdp.click('[data-action="workspace-ground"]');
    await cdp.until('!!document.querySelector("#workspace-form [name=brief]")');
    const preservedDraft=await cdp.eval('document.querySelector("#workspace-form [name=brief]")?.value');
    assert.equal(preservedDraft,'P118-ALPHA-ONLY-GROUND','G2 existing unsent local Ground draft is preserved');
    await cdp.click('[data-action="grounding"]');
    await cdp.until('!!document.querySelector("#project-grounding-form")');
    const liveGrounding=await cdp.eval('document.querySelector("#project-grounding-form [name=ground-1f]")?.value');
    assert.equal(liveGrounding,'P118-ALPHA-ONLY-GROUND-V2','Shared ALPHA library reflects V2 despite old local draft');
    assert.notEqual(liveGrounding,'P118-BETA-NEVER-IN-ALPHA');
    trace.push(await cdp.snap('P03: ALPHA/G2 sees current V2 fixture; existing Ground draft preserved'));
    assert.deepEqual(cdp.errors,[],'No uncaught browser JavaScript exceptions');
    const shot=await cdp.send('Page.captureScreenshot',{format:'png',captureBeyondViewport:false});
    const digest=createHash('sha256').update(Buffer.from(shot.data,'base64')).digest('hex');
    console.log('P01_P03_REAL_BROWSER_TRACE '+JSON.stringify({events:trace,uncaughtErrors:cdp.errors,screenshotSha256:digest}));
  }finally{await cleanBrowser(cp,web,profile,cdp?.ws);}
});

test('P06 negative browser control: ambiguous legacy thread remains navigable without choosing either project',{timeout:30000},async t=>{
  if(!browser){t.skip('Browser executable unavailable');return;}
  const {web,url}=await server(),profile=fs.mkdtempSync(path.join(os.tmpdir(),'nn118-g2-collision-'));
  const cp=spawn(browser,['--headless=new','--no-sandbox','--disable-dev-shm-usage','--disable-gpu',
    '--window-size=1250,900','--remote-debugging-port=0','--user-data-dir='+profile,url],{stdio:'ignore'});
  let cdp;
  try{
    const info=await chromiumTab(profile,cp);
    const ws=new WebSocket(info.webSocketDebuggerUrl);
    await new Promise((resolve,reject)=>{ws.addEventListener('open',resolve,{once:true});ws.addEventListener('error',reject,{once:true});});
    cdp=new CDP(ws);await cdp.send('Runtime.enable');await cdp.send('Page.enable');
    await cdp.until('document.querySelector("#panel h2")?.textContent==="Projects"');
    const record=await cdp.eval(`(()=>{
      const threads=JSON.parse(localStorage.getItem('nextnudge.threads.v3')||'{}');
      const original=Object.values(threads)[0];if(!original)throw Error('Historical seeded thread missing');
      const ids=['NP-20261020-140000-a001','NP-20261020-140000-b001'];
      const row={id:original.id,agent:original.agent||'P118-LEGACY',legacy:true};
      const projects=Object.fromEntries(ids.map((id,index)=>[id,{
        version:1,id,name:index?'P118-BETA':'P118-ALPHA',
        threads:[row],fixtures:{},snapshots:[]}]));
      localStorage.setItem('nextnudge.projects.v1',JSON.stringify(projects));
      return {threadId:original.id,threadTitle:original.title,projects:ids};
    })()`);
    await cdp.send('Page.reload',{ignoreCache:true});
    await cdp.until('document.querySelector("#panel h2")?.textContent==="Projects"');
    await cdp.click('[data-project="'+record.projects[0]+'"]');
    await cdp.until('document.querySelector("#panel h2")?.textContent==="P118-ALPHA"');
    await cdp.click('[data-open="'+record.threadId+'"]');
    await sleep(300);
    const observed=await cdp.eval('({heading:document.querySelector("#panel h2")?.textContent,notice:document.querySelector("#notice")?.textContent,historyVisible:document.querySelector("#panel")?.textContent.includes("Earlier moves")})');
    console.log('P06_AMBIGUOUS_LEGACY_BROWSER_WITNESS '+JSON.stringify({record,observed}));
    assert.equal(observed.heading,record.threadTitle,
      'A multiply-associated legacy thread must remain readable, with unresolved project custody flagged');
    assert.equal(observed.historyVisible,true,'Sent history remains navigable without choosing a project');
  }finally{await cleanBrowser(cp,web,profile,cdp?.ws);}
});

test('P06 authentic v3 import exact-byte preservation and v2 Archive/Convert in real Chromium',{timeout:75000},async t=>{
  if(!browser){t.skip('Browser executable unavailable');return;}
  const {parse}=await import('../site/nextnudge/revamp/thread.mjs');
  const input=path.join(root,'site/nextnudge-data/threads/NN-20261019-165622-6810.md');
  const original=parse(fs.readFileSync(input,'utf8'));
  const receipts=original.moves.filter(m=>m.delivery==='sent'&&m.packet)
    .map(m=>({id:m.id,length:Buffer.byteLength(m.packet,'utf8'),
      hash:createHash('sha256').update(m.packet,'utf8').digest('hex')}));
  assert.ok(receipts.length>0,'authentic historical file must contain exact sent packets');
  const {web,url}=await server(),profile=fs.mkdtempSync(path.join(os.tmpdir(),'nn118-g2-import-'));
  const cp=spawn(browser,['--headless=new','--no-sandbox','--disable-dev-shm-usage','--disable-gpu',
    '--window-size=1300,1000','--remote-debugging-port=0','--user-data-dir='+profile,url],{stdio:'ignore'});
  let cdp;
  try{
    const info=await chromiumTab(profile,cp),ws=new WebSocket(info.webSocketDebuggerUrl);
    await new Promise((resolve,reject)=>{ws.addEventListener('open',resolve,{once:true});ws.addEventListener('error',reject,{once:true});});
    cdp=new CDP(ws);await cdp.send('Runtime.enable');await cdp.send('Page.enable');await cdp.send('DOM.enable');
    await cdp.until('document.querySelector("#panel h2")?.textContent==="Projects"');
    const doc=await cdp.send('DOM.getDocument',{depth:1});
    const inputNode=await cdp.send('DOM.querySelector',{nodeId:doc.root.nodeId,selector:'#import-file'});
    assert.ok(inputNode.nodeId);
    await cdp.send('DOM.setFileInputFiles',{nodeId:inputNode.nodeId,files:[input]});
    await cdp.until('document.querySelector("#panel h2")?.textContent==='+JSON.stringify(original.title),12000);
    const actual=await cdp.eval('(()=>{const t=JSON.parse(localStorage.getItem("nextnudge.threads.v3"))['+
      JSON.stringify(original.id)+'];return {id:t.id,title:t.title,moveCount:t.moves.length,packets:t.moves.filter(m=>m.delivery==="sent"&&m.packet).map(m=>({id:m.id,packet:m.packet})),legacy:t.moves.filter(m=>m.note?.startsWith("GROUNDING_FIXTURES_V1:")).length};})()');
    assert.equal(actual.id,original.id);assert.equal(actual.moveCount,original.moves.length);
    assert.deepEqual(actual.packets.map(p=>({id:p.id,length:Buffer.byteLength(p.packet,'utf8'),
      hash:createHash('sha256').update(p.packet,'utf8').digest('hex')})),receipts);
    assert.equal(actual.legacy,original.moves.filter(m=>m.note?.startsWith('GROUNDING_FIXTURES_V1:')).length);
    assert.deepEqual(cdp.errors,[],'No JS exception importing a real preserved v3 file');
    console.log('P06_AUTHENTIC_CHROMIUM_IMPORT '+JSON.stringify({id:original.id,moveCount:actual.moveCount,legacy:actual.legacy,receipts}));
    await cdp.click('[data-action="back"]');await cdp.until('document.querySelector("#panel h2")?.textContent==="Projects"');
    await cdp.click('details summary');
    await cdp.until('!!document.querySelector("[data-action=archive-list]")');
    const archiveToggle=await cdp.eval('(()=>{const b=document.querySelector("[data-action=archive-list]");return b?.closest("details")?.querySelector("summary")?.textContent;})()');
    assert.match(archiveToggle,/v2 Archive/);
    await cdp.click('details details summary');
    await cdp.click('[data-action="archive-list"]');
    await cdp.until('document.querySelectorAll("#archive-runs [data-convert]").length>0');
    const convertedId=await cdp.eval('document.querySelector("#archive-runs [data-convert]")?.dataset.convert');
    await cdp.click('#archive-runs details summary');
    await cdp.click('#archive-runs [data-convert]');
    await cdp.until('document.querySelector("#panel h2")?.textContent!=="Projects"');
    const post=await cdp.eval('(()=>{const ts=JSON.parse(localStorage.getItem("nextnudge.threads.v3"));return {ids:Object.keys(ts),converted:ts['+JSON.stringify(convertedId)+']?.moves?.length,original:ts['+JSON.stringify(original.id)+']?.moves?.length};})()');
    assert.equal(post.original,original.moves.length,'conversion cannot overwrite imported v3');
    assert.ok(post.ids.includes(convertedId),'v2 conversion retained as new separate thread');
    console.log('P06_V2_ARCHIVE_CONVERT_CHROMIUM '+JSON.stringify({convertedId,post}));
  }finally{await cleanBrowser(cp,web,profile,cdp?.ws);}
});
