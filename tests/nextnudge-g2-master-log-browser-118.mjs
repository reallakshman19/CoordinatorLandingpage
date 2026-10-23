import {updateFixtures,validateProject} from '../site/nextnudge/revamp/project-model.mjs';
import {groundingPanel,projectGroundingText} from '../site/nextnudge/revamp/grounding.mjs';
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




import {newThread} from '../site/nextnudge/revamp/thread.mjs';
import {newProject,addThread} from '../site/nextnudge/revamp/project-model.mjs';
const makeThread=(id,agent)=>newThread({id,title:'P118 '+agent+' activity',agent,goal:'Validate owner outcome',doneWhen:['Acceptance check']});
const makeMove=(id,kind,extra={})=>({id,kind,delivery:['task','correction'].includes(kind)?'sent':'draft',
 packet:['task','correction'].includes(kind)?'One bounded task:\nP118 activity '+id:'',
 returnLine:'',digest:'',evidence:'',gap:'',decision:'',archive:'',note:'',...extra});
test('NN121 G2 real Chromium Master Log multi-agent fidelity and P09 premature Close rejection',{timeout:70000},async t=>{
 if(!browser){t.skip('Chromium unavailable');return;}
 const {web,url}=await server(),profile=fs.mkdtempSync(path.join(os.tmpdir(),'nn118-master-'));
 const cp=spawn(browser,['--headless=new','--no-sandbox','--disable-dev-shm-usage','--disable-gpu','--window-size=1300,1000','--remote-debugging-port=0','--user-data-dir='+profile,url],{stdio:'ignore'});
 let cdp;
 try{
  const info=await chromiumTab(profile,cp),ws=new WebSocket(info.webSocketDebuggerUrl);
  await new Promise((resolve,reject)=>{ws.addEventListener('open',resolve,{once:true});ws.addEventListener('error',reject,{once:true});});
  cdp=new CDP(ws);await cdp.send('Runtime.enable');await cdp.send('Page.enable');
  const version=(await cdp.send('Browser.getVersion')).product;
  await cdp.until('document.querySelector("#panel h2")?.textContent==="Projects"');
  const g1=makeThread('NN-20261020-165501-a001','P118-G1'),g2=makeThread('NN-20261020-165502-a002','P118-G2'),beta=makeThread('NN-20261020-165503-b003','P118-G1');
  const task='NN-20261020-165601-c001',reply='NN-20261020-165602-c002',g2task='NN-20261020-165603-c003';
  g1.moves.push(makeMove(task,'task',{packet:'One bounded task:\nP118 G1 inspect source'}));
  g1.moves.push(makeMove(reply,'reply',{answers:task,returnLine:'ACK '+task+' FROM: P118-G1'}));
  g1.moves.push(makeMove('NN-20261020-165604-c004','correction',{packet:'One bounded task:\nCorrect P118 observed mismatch'}));
  g1.moves.push(makeMove('NN-20261020-165605-c005','amendment',{note:'WORKSPACE_V1:'+JSON.stringify({mode:'reconcile',
   values:{decision:'request evidence',nextTask:'Reconcile G1 outcome',basis:'["Acceptance check"]'},
   owner:{goal:'Validate owner outcome',doneWhen:['Acceptance check'],inScope:'',outScope:'',hold:''}})}));
  const sealed='P118-PUBLIC-SEALED-NOTE-DO-NOT-SUMMARIZE';
  g1.moves.push(makeMove('NN-20261020-165606-c006','sealed',{
    text:sealed,names:task,sha256:createHash('sha256').update(sealed).digest('hex'),createdAt:'2026-10-20T16:56:06.000Z'}));
  g2.moves.push(makeMove(g2task,'task',{packet:'One bounded task:\nP118 G2 independent test'}));
  g2.moves.push(makeMove('NN-20261020-165607-c007','amendment',{note:'WORKSPACE_V1:'+JSON.stringify({mode:'correction',
   values:{claim:'G2 original claim',expected:'G2 correction expected'},owner:{goal:'Validate owner outcome',doneWhen:['Acceptance check'],inScope:'',outScope:'',hold:''}})}));
  beta.moves.push(makeMove('NN-20261020-165608-c008','task',{packet:'One bounded task:\nP118-BETA-NEVER-IN-ALPHA'}));
  const a=addThread(addThread(newProject('P118-ALPHA-LOG','NP-20261020-165500-a001'),g1),g2);
  a.threads.push({id:'NN-20261020-165500-ffff',agent:'P118-MISSING',legacy:true});
  const b=addThread(newProject('P118-BETA-LOG','NP-20261020-165500-b001'),beta);
  const projs=JSON.stringify({[a.id]:a,[b.id]:b}),threads=JSON.stringify({[g1.id]:g1,[g2.id]:g2,[beta.id]:beta});
  await cdp.eval('(()=>{localStorage.setItem("nextnudge.projects.v1",'+JSON.stringify(projs)+');localStorage.setItem("nextnudge.threads.v3",'+JSON.stringify(threads)+');return true;})()');
  await cdp.send('Page.reload',{ignoreCache:true});
  await cdp.until('document.querySelector("#panel h2")?.textContent==="Projects"',18000);
  await cdp.click('[data-project="'+a.id+'"]');await cdp.click('[data-action=master-log]');
  await cdp.until('document.querySelectorAll(".master-log-item").length>=7',18000);
  const w=await cdp.eval('({text:document.querySelector("#panel").textContent,items:[...document.querySelectorAll(".master-log-item")].map(x=>({header:x.querySelector("strong")?.textContent,href:x.querySelector("a")?.getAttribute("href"),preview:x.querySelector("p")?.textContent})),missing:document.querySelector("section[role=status]")?.textContent})');
  for(const name of ['P118-G1 · Task','P118-G1 · Agent reply','P118-G1 · Correction','P118-G1 · reconcile saved','P118-G2 · Task','P118-G2 · correction saved'])
    assert.ok(w.items.some(x=>x.header?.toLowerCase()===name.toLowerCase()),'Missing source-derived kind '+name);
  assert.match(w.missing||'',/P118-MISSING/);
  assert.match(w.text,/Incomplete source coverage/);
  assert.ok(!w.text.includes(sealed),'Sealed note text must never be summarized');
  assert.ok(!w.text.includes('P118-BETA-NEVER-IN-ALPHA'),'BETA must never appear in ALPHA log');
  const link=w.items.find(x=>x.href?.includes('move='+task));
  assert.ok(link?.href.includes('thread='+g1.id)&&!link.href.includes('thread='+g2.id));
  await cdp.click('.master-log-item a[href*="move='+task+'"]');
  await cdp.until('!!document.querySelector("#move-'+task+'")',18000);
  assert.equal(await cdp.eval('new URL(location.href).searchParams.get("move")'),task);
  assert.equal(await cdp.eval('JSON.parse(localStorage.getItem("nextnudge.threads.v3"))['+JSON.stringify(g1.id)+'].moves.length'),g1.moves.length,'read-only navigation');
  await cdp.click('[data-action=workspace-reconcile]');
  await cdp.until('!!document.querySelector("#workspace-form [name=target]")');
  await cdp.eval('(()=>{const s=document.querySelector("#workspace-form [name=target]");s.value='+JSON.stringify(reply)+';s.dispatchEvent(new Event("change",{bubbles:true}));return s.value;})()');
  await cdp.click('#workspace-form [name=nextTask]');await cdp.send('Input.insertText',{text:'Unverified closure request'});
  await cdp.eval('(()=>{const s=document.querySelector("#workspace-form [name=decision]");s.value="close";s.dispatchEvent(new Event("change",{bubbles:true}));return s.value;})()');
  await cdp.click('[data-action=workspace-build]');
  await cdp.until('document.querySelector("#notice")?.textContent.includes("cannot close") || document.querySelector("#notice")?.textContent.includes("not built")');
  const guard=await cdp.eval('document.querySelector("#notice").textContent');
  assert.match(guard,/cannot close|NOT.*MET|missing|UNKNOWN/i);
  assert.deepEqual(cdp.errors,[]);
  console.log('G2_NN121_MASTER_LOG_AND_P09_BROWSER '+JSON.stringify({version,source:'13432ab7e23e30a1dbe2246d03d0802f6aff1ff9',items:w.items,missing:w.missing,taskMove:task,exactDeepLink:link.href,closureNotice:guard,remoteWrites:false,evidenceLevel:'local synthetic source records and real pointer UI only'}));
 }finally{await cleanBrowser(cp,web,profile,cdp?.ws);}
});

test('P10 post-122 operation adaptation: archived 6a stays in original snapshots but not active 5-derived packets',()=>{
 const p0=newProject('P118-HISTORICAL-6A','NP-20261020-170000-d001');
 const p1=updateFixtures(p0,{'6a':'P118-6A-EXISTING-HISTORICAL','5':'P118-V1-CRITERIA'},'2026-10-20T17:00:00Z');
 const old=JSON.stringify(p1.snapshots[0]);
 const p2=updateFixtures(p1,{'5':'P118-V2-CRITERIA'},'2026-10-20T17:01:00Z');
 assert.equal(validateProject(p2),p2);
 assert.equal(p2.fixtures['6a'],'P118-6A-EXISTING-HISTORICAL');
 assert.equal(JSON.stringify(p2.snapshots[0]),old);
 assert.equal(p2.snapshots.length,2);
 const active=projectGroundingText(p2);
 assert.match(active,/P118-V2-CRITERIA/);
 assert.doesNotMatch(active,/P118-6A-EXISTING-HISTORICAL/);
 const html=groundingPanel(null,p2.fixtures,false,p2);
 assert.match(html,/Historical retired Midcycle context/);
 assert.match(html,/P118-6A-EXISTING-HISTORICAL/);
 assert.doesNotMatch(html,/name="ground-6a"/);
 assert.throws(()=>validateProject({...p2,fixtures:{'5':'P118-V2-CRITERIA'}}),/mismatch/);
 console.log('P118_HISTORICAL_6A_CUSTODY '+JSON.stringify({originalSnapshotUnchanged:true,retained6a:p2.fixtures['6a'],latest5:p2.fixtures['5'],newPacket6aAbsent:true,activeEditor6aAbsent:true}));
});
