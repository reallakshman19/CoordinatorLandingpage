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


async function boot(){
  const {web,url}=await server(),profile=fs.mkdtempSync(path.join(os.tmpdir(),'nn118-g2-delta-'));
  const cp=spawn(browser,['--headless=new','--no-sandbox','--disable-dev-shm-usage','--disable-gpu',
    '--window-size=1300,1000','--remote-debugging-port=0','--user-data-dir='+profile,url],{stdio:'ignore'});
  const info=await chromiumTab(profile,cp),ws=new WebSocket(info.webSocketDebuggerUrl);
  await new Promise((resolve,reject)=>{ws.addEventListener('open',resolve,{once:true});ws.addEventListener('error',reject,{once:true});});
  const cdp=new CDP(ws);await cdp.send('Runtime.enable');await cdp.send('Page.enable');
  await cdp.until('document.querySelector("#panel h2")?.textContent==="Projects"',18000);
  return {cdp,cp,web,profile,version:(await cdp.send('Browser.getVersion')).product};
}
async function fill(cdp,selector,value){
  await cdp.click(selector);
  await cdp.send('Input.dispatchKeyEvent',{type:'keyDown',key:'a',code:'KeyA',modifiers:2,windowsVirtualKeyCode:65});
  await cdp.send('Input.dispatchKeyEvent',{type:'keyUp',key:'a',code:'KeyA',modifiers:2,windowsVirtualKeyCode:65});
  if(value)await cdp.send('Input.insertText',{text:value});
  else await cdp.send('Input.dispatchKeyEvent',{type:'char',text:'',key:'Backspace',code:'Backspace',windowsVirtualKeyCode:8});
}
async function choose(cdp,selector,value){
  await cdp.eval('(()=>{const x=document.querySelector('+JSON.stringify(selector)+');if(!x)throw Error("Missing select");x.value='+JSON.stringify(value)+';x.dispatchEvent(new Event("change",{bubbles:true}));return x.value;})()');
}
const read=async cdp=>cdp.eval('({projects:JSON.parse(localStorage.getItem("nextnudge.projects.v1")||"{}"),threads:JSON.parse(localStorage.getItem("nextnudge.threads.v3")||"{}"),drafts:JSON.parse(localStorage.getItem("nextnudge.workspace.drafts.v1")||"{}")})');
const sha=p=>createHash('sha256').update(p,'utf8').digest('hex');
async function makeProject(cdp,name){
  await fill(cdp,'#new-project input[name=name]',name);await cdp.click('#new-project button[type=submit]');
  await cdp.until('document.querySelector("#panel h2")?.textContent==='+JSON.stringify(name));
  return Object.values((await read(cdp)).projects).find(p=>p.name===name).id;
}
async function makeThread(cdp,agent,title){
  await fill(cdp,'#new-thread input[name=agent]',agent);
  await fill(cdp,'#new-thread input[name=title]',title);
  await fill(cdp,'#new-thread textarea[name=goal]','P118 test Owner goal '+agent);
  await cdp.click('#new-thread button[type=submit]');
  await cdp.until('document.querySelector("#panel h2")?.textContent==='+JSON.stringify(title));
  const ts=Object.values((await read(cdp)).threads);return ts.find(x=>x.title===title).id;
}
test('G2 delta P02 P03 P04 P05 P09 P10 + Master Log: real Chromium local-only interactions post-122',{timeout:160000},async t=>{
  if(!browser){t.skip('Chromium binary unavailable');return;}
  const b=await boot(),{cdp}=b,trace=[];
  try{
    const aId=await makeProject(cdp,'P118-ALPHA');
    await cdp.click('[data-action="project-grounding"]');
    await fill(cdp,'[name=ground-1a]','https://github.com/reallakshman19/CoordinatorLandingpage/issues/118');
    await fill(cdp,'[name=ground-1f]','P118-ALPHA-ONLY-GROUND');
    await fill(cdp,'[name=ground-5]','P118-ALPHA-TESTS-V1');
    assert.equal(await cdp.eval('!!document.querySelector("[name=ground-6a]")'),false,'retired 6a must not be active');
    await cdp.click('#project-grounding-form button[type=submit]');
    assert.equal((await read(cdp)).projects[aId].fixtures['5'],'P118-ALPHA-TESTS-V1');
    trace.push('P02 ALPHA owner fixture V1 saved locally, active heading 5');
    await cdp.click('[data-action="project"]');
    const g1=await makeThread(cdp,'P118-G1','G1 post122 task');
    await cdp.click('[data-action="workspace-ground"]');
    await fill(cdp,'#workspace-form textarea[name=brief]','P118 ALPHA G1 source orientation');
    await cdp.click('#workspace-form button[type=submit]');
    const ground=(await read(cdp)).threads[g1].moves.find(m=>m.note?.startsWith('WORKSPACE_V1:'));
    assert.ok(ground,'G1 saved separate Ground workspace');
    await cdp.click('[data-action="workspace-task"]');
    await fill(cdp,'#workspace-form textarea[name=task]','Inspect ALPHA structural outputs');
    await fill(cdp,'#workspace-form textarea[name=deliverable]','One bounded technical report');
    await fill(cdp,'#workspace-form textarea[name=success]','Output verified with provenance');
    await choose(cdp,'#workspace-form select[name=groundId]',ground.id);
    await cdp.click('[data-action="workspace-build"]');
    await cdp.until('!!document.querySelector("#packet")');
    const packet1=await cdp.eval('document.querySelector("#packet").value');
    assert.match(packet1,/P118-ALPHA-ONLY-GROUND/);
    assert.match(packet1,/P118-ALPHA-TESTS-V1/);
    assert.doesNotMatch(packet1,/P118-BETA-NEVER-IN-ALPHA/);
    await cdp.click('[data-action="record-sent"]');
    await cdp.until('!!document.querySelector("#sent-confirm")');
    await cdp.click('#sent-confirm [name=approved]');
    await cdp.click('#sent-confirm button[type=submit]');
    await cdp.until('JSON.parse(localStorage.getItem("nextnudge.threads.v3"))['+JSON.stringify(g1)+'].moves.some(m=>m.delivery==="sent")');
    const sent=(await read(cdp)).threads[g1].moves.find(m=>m.delivery==='sent');
    const frozenHash=sha(sent.packet);
    assert.equal(sent.packet,packet1);
    trace.push({case:'P05 G1 local MANUALLY MARKED sent (not real transport)',id:sent.id,sha256:frozenHash,bytes:Buffer.byteLength(sent.packet)});
    await cdp.click('[data-action="thread"]');await cdp.click('[data-action="back"]');
    await cdp.until('document.querySelector("#panel h2")?.textContent==="P118-ALPHA"');
    const g2=await makeThread(cdp,'P118-G2','G2 post122 independent draft');
    await cdp.click('[data-action="workspace-task"]');
    await fill(cdp,'#workspace-form textarea[name=task]','P118 G2 UNSENT DRAFT ONLY');
    await cdp.click('[data-action="workspace-ground"]');
    await cdp.click('[data-action="workspace-task"]');
    assert.equal(await cdp.eval('document.querySelector("#workspace-form [name=task]").value'),'P118 G2 UNSENT DRAFT ONLY','G2 unsent draft survives mode switch');
    assert.equal((await read(cdp)).threads[g2].moves.length,0,'G2 draft never lands in G1 history');
    trace.push('P05 G2 unsent workspace draft independent and retained');
    await cdp.click('[data-action="thread"]');await cdp.click('[data-action="back"]');
    await cdp.until('document.querySelector("#panel h2")?.textContent==="P118-ALPHA"');
    await fill(cdp,'#new-thread input[name=agent]','P118-G1');
    await fill(cdp,'#new-thread input[name=title]','ILLEGAL second G1');
    await fill(cdp,'#new-thread textarea[name=goal]','duplicate should reject');
    await cdp.click('#new-thread button[type=submit]');
    await cdp.until('document.querySelector("#new-thread-error")?.textContent.includes("already")');
    assert.equal((await read(cdp)).projects[aId].threads.length,2,'duplicate cannot create third ALPHA thread');
    assert.ok(await cdp.eval('document.activeElement?.id==="new-thread-error"'),'inline duplicate alert receives focus');
    trace.push('P04 duplicate ALPHA/G1 blocked without losing ALPHA/G2');
    await cdp.click('[data-action="project-grounding"]');
    await fill(cdp,'#project-grounding-form [name=ground-5]','P118-ALPHA-V2-ADDED-AFTER-FIRST-SEND');
    await cdp.click('#project-grounding-form button[type=submit]');
    const p2=(await read(cdp)).projects[aId];
    assert.equal(p2.snapshots.length,2);
    await cdp.click('[data-action="project"]');
    await cdp.click('[data-open="'+g2+'"]');
    await cdp.click('[data-action="workspace-task"]');
    assert.equal(await cdp.eval('document.querySelector("#workspace-form [name=task]").value'),'P118 G2 UNSENT DRAFT ONLY','V2 cannot erase G2 unsent draft');
    await cdp.click('[data-action="workspace-ground"]');
    await fill(cdp,'#workspace-form textarea[name=brief]','G2 new grounding after V2');
    await cdp.click('[data-action="workspace-build"]');
    await cdp.until('!!document.querySelector("#packet")');
    const packet2=await cdp.eval('document.querySelector("#packet").value');
    assert.match(packet2,/P118-ALPHA-V2-ADDED-AFTER-FIRST-SEND/);
    assert.doesNotMatch(packet2,/P118-ALPHA-TESTS-V1/);
    const stillSent=(await read(cdp)).threads[g1].moves.find(m=>m.id===sent.id);
    assert.equal(sha(stillSent.packet),frozenHash,'G1 original sent bytes unchanged after project fixture V2');
    assert.equal(stillSent.packet,packet1);
    trace.push({case:'P10 latest G2 Ground gets V2; old G1 immutable',newGroundMarker:'P118-ALPHA-V2-ADDED-AFTER-FIRST-SEND',oldMove:sent.id,oldSha:frozenHash,newDraftSha:sha(packet2)});
    await cdp.click('[data-action="thread"]');await cdp.click('[data-action="back"]');
    await cdp.click('[data-action="master-log"]');
    await cdp.until('!!document.querySelector(".master-log-item")');
    const summary=await cdp.eval('({heading:document.querySelector("#panel h2")?.textContent,items:[...document.querySelectorAll(".master-log-item")].map(x=>({text:x.textContent,href:x.querySelector("a")?.getAttribute("href")}))})');
    assert.ok(summary.items.some(x=>x.href.includes('move='+sent.id)&&x.text.includes('Inspect ALPHA structural outputs')));
    assert.ok(summary.items.some(x=>x.href.includes('move='+ground.id)&&x.text.includes('P118 ALPHA G1 source orientation')));
    assert.ok(summary.items.every(x=>!x.text.includes('P118-BETA-NEVER-IN-ALPHA')));
    assert.ok(summary.items.every(x=>!x.text.includes('P118 G2 UNSENT DRAFT ONLY')),'unsent draft cannot masquerade as an activity record');
    const wanted=summary.items.find(x=>x.href.includes('move='+sent.id));
    assert.ok(wanted.href.includes('thread='+g1));
    assert.ok(!wanted.href.includes('thread='+g2),'wrong G2 deep link must not point to G1 Task');
    trace.push({case:'NN121 Master Log renders genuine local move sources, not G2 draft',g1Task:sent.id,href:wanted.href,items:summary.items.length});
    const beforeNav=(await read(cdp)).threads[g1].moves.length;
    await cdp.click('.master-log-item a[href*="move='+sent.id+'"]');
    await cdp.until('!!document.querySelector("#move-'+sent.id+'")',18000);
    assert.equal(await cdp.eval('new URL(location.href).searchParams.get("move")'),sent.id);
    assert.equal((await read(cdp)).threads[g1].moves.length,beforeNav,'opening deep link cannot add logging moves');
    trace.push('NN121 exact item pointer navigation and no navigation-event side effects');
    await cdp.click('[data-action="owner-edit"]');
    await fill(cdp,'#owner-amend [name=hold]','P118-HOLD-SENDING');
    await fill(cdp,'#owner-amend [name=checks]','One verified acceptance check');
    await cdp.click('#owner-amend [name=approved]');
    await cdp.click('#owner-amend button[type=submit]');
    await cdp.until('document.querySelector("#panel")?.textContent.includes("P118-HOLD-SENDING")');
    assert.equal(await cdp.eval('!!document.querySelector("[data-action=compose-task]")'),false,'HOLD hides send/compose actions');
    await cdp.click('[data-action="owner-edit"]');
    await fill(cdp,'#owner-amend [name=hold]',' ');
    await cdp.click('#owner-amend [name=approved]');
    await cdp.click('#owner-amend button[type=submit]');
    await cdp.until('!!document.querySelector("[data-action=compose-task]")');
    trace.push('P09 Owner-confirmed HOLD blocks compose; only Owner amendment clears HOLD');
    await cdp.click('[data-action="back"]');await cdp.click('[data-action="project-grounding"]');
    await fill(cdp,'#project-grounding-form [name=ground-1f]','https%3A%2F%2Fchatgpt.com%2Fc%2Fnot-public');
    await cdp.click('#project-grounding-form button[type=submit]');
    await cdp.until('document.querySelector("#notice")?.textContent.includes("Private chat URL found")');
    assert.equal((await read(cdp)).projects[aId].fixtures['1f'],'P118-ALPHA-ONLY-GROUND');
    assert.match(await cdp.eval('localStorage.getItem("nextnudge.project.grounding.drafts.v1")'),/chatgpt/,'rejected local draft survives');
    trace.push('P09 encoded private-chat URL rejected; project unchanged and device draft retained');
    await cdp.click('[data-action="project"]');await cdp.click('[data-action="projects"]');
    const bId=await makeProject(cdp,'P118-BETA');
    await cdp.click('[data-action="project-grounding"]');
    await fill(cdp,'#project-grounding-form [name=ground-1f]','P118-BETA-NEVER-IN-ALPHA');
    await cdp.click('#project-grounding-form button[type=submit]');
    await cdp.click('[data-action="project"]');
    const betaG1=await makeThread(cdp,'P118-G1','BETA same-name G1 valid');
    await cdp.click('[data-action="workspace-ground"]');
    await fill(cdp,'#workspace-form textarea[name=brief]','BETA only G1');
    await cdp.click('[data-action="workspace-build"]');
    const betaPacket=await cdp.eval('document.querySelector("#packet")?.value');
    assert.match(betaPacket,/P118-BETA-NEVER-IN-ALPHA/);
    assert.doesNotMatch(betaPacket,/P118-ALPHA-ONLY-GROUND|P118-ALPHA-V2-ADDED-AFTER-FIRST-SEND/);
    assert.equal((await read(cdp)).projects[bId].threads[0].id,betaG1);
    trace.push({case:'P03 and P04 BETA G1 permitted, BETA packet excludes ALPHA',betaId:betaG1,betaPacketSha:sha(betaPacket)});
    assert.deepEqual(cdp.errors,[]);
    console.log('G2_POST122_REAL_BROWSER_DELTA '+JSON.stringify({head:'13432ab7e23e30a1dbe2246d03d0802f6aff1ff9',version:b.version,trace,g1,g2,aId,bId,betaG1,oldSentPacketSha256:frozenHash,oldSentMoveId:sent.id,oldSentBytes:Buffer.byteLength(packet1,'utf8'),newG2GroundDraftSha256:sha(packet2),noRemoteWrites:true}));
  }finally{await cleanBrowser(b.cp,b.web,b.profile,cdp.ws);}
});

test('G2 P06 authentic v3 imported/attached, reload, Master Log links; archived v2 separately converted in Chromium',{timeout:100000},async t=>{
  if(!browser){t.skip('Chromium binary unavailable');return;}
  const {parse}=await import('../site/nextnudge/revamp/thread.mjs');
  const file=path.join(root,'site/nextnudge-data/threads/NN-20261019-165622-6810.md');
  const historic=parse(fs.readFileSync(file,'utf8'));
  const receipts=historic.moves.filter(m=>m.delivery==='sent'&&m.packet).map(m=>({id:m.id,sha256:sha(m.packet),bytes:Buffer.byteLength(m.packet,'utf8')}));
  assert.ok(receipts.length,'authentic historic saved packet missing');
  const b=await boot(),{cdp}=b;
  try{
    const alpha=await makeProject(cdp,'P118-ALPHA-IMPORT');
    await cdp.send('DOM.enable');
    const doc=await cdp.send('DOM.getDocument',{depth:1});
    const target=await cdp.send('DOM.querySelector',{nodeId:doc.root.nodeId,selector:'#import-file'});
    assert.ok(target.nodeId);
    await cdp.send('DOM.setFileInputFiles',{nodeId:target.nodeId,files:[file]});
    await cdp.until('document.querySelector("#panel h2")?.textContent==='+JSON.stringify(historic.title),14000);
    const once=(await read(cdp)).threads[historic.id];
    assert.equal(once.moves.length,historic.moves.length);
    assert.deepEqual(once.moves.filter(m=>m.delivery==='sent'&&m.packet).map(m=>({id:m.id,sha256:sha(m.packet),bytes:Buffer.byteLength(m.packet,'utf8')})),receipts);
    assert.equal(once.moves.filter(m=>m.note?.startsWith('GROUNDING_FIXTURES_V1:')).length,2);
    await cdp.click('[data-action="back"]');
    await cdp.click('[data-project="'+alpha+'"]');
    assert.ok(await cdp.eval('!!document.querySelector("#attach-thread")'));
    await cdp.click('details:has(#attach-thread) > summary');
    await choose(cdp,'#attach-thread select[name=thread]',historic.id);
    await cdp.click('#attach-thread button[type=submit]');
    await cdp.until('JSON.parse(localStorage.getItem("nextnudge.projects.v1"))['+JSON.stringify(alpha)+'].threads.some(x=>x.id==='+JSON.stringify(historic.id)+')');
    await cdp.send('Page.reload',{ignoreCache:true});
    await cdp.until('document.querySelector("#panel h2")?.textContent.includes("P118-ALPHA-IMPORT")',18000);
    if(await cdp.eval('document.querySelector("#panel h2")?.textContent.startsWith("Master Log")'))
      await cdp.click('[data-action="project"]');
    await cdp.click('[data-action="master-log"]');
    await cdp.until('!!document.querySelector(".master-log-item")');
    const linked=await cdp.eval('Array.from(document.querySelectorAll(".master-log-item a")).map(a=>a.getAttribute("href"))');
    assert.ok(linked.some(h=>h.includes('thread='+historic.id)&&h.includes('move='+receipts[0].id)));
    const post=(await read(cdp)).threads[historic.id];
    assert.deepEqual(post.moves.filter(m=>m.delivery==='sent'&&m.packet).map(m=>({id:m.id,sha256:sha(m.packet),bytes:Buffer.byteLength(m.packet,'utf8')})),receipts);
    assert.equal(post.moves.length,historic.moves.length);
    await cdp.click('[data-action="project"]');await cdp.click('[data-action="projects"]');
    await cdp.click('details summary');await cdp.click('details details summary');
    await cdp.click('[data-action=archive-list]');
    await cdp.until('document.querySelectorAll("#archive-runs [data-convert]").length>0');
    const id=await cdp.eval('document.querySelector("#archive-runs [data-convert]").dataset.convert');
    await cdp.click('#archive-runs details summary');
    await cdp.click('#archive-runs [data-convert]');
    await cdp.until('document.querySelector("#panel h2")?.textContent!=="Projects"');
    const after=(await read(cdp)).threads;
    assert.ok(after[id],'v2 Archive converted to a new thread');
    assert.equal(after[historic.id].moves.length,historic.moves.length);
    assert.deepEqual(cdp.errors,[]);
    console.log('G2_POST122_P06_REAL_BROWSER '+JSON.stringify({version:b.version,historicThreadId:historic.id,projectId:alpha,historicMoves:historic.moves.length,oldGroundSnapshots:2,receipts,linkedMove:receipts[0].id,conversionThreadId:id,remoteCustody:'NOT_RUN'}));
  }finally{await cleanBrowser(b.cp,b.web,b.profile,cdp.ws);}
});
