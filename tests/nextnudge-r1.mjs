import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {gzipSync} from 'node:zlib';
import {newThread,parse,serialize,validate,archiveRun,currentState,reconcile,assertPublic,activeIntent} from '../site/nextnudge/revamp/thread.mjs';
import {delta,applyDelta,issueUrl} from '../site/nextnudge/revamp/save.mjs';
import {applyIssue,ownerIssue,unpack} from '../scripts/nextnudge_thread_apply.mjs';
const ID='NN-20261019-010101-ab12',M='NN-20261019-010102-cd34';
const root=new URL('../site/nextnudge-data/',import.meta.url);
const example=()=>newThread({id:ID,title:'Steering test',agent:'Validator',
  goal:'Owner goal: verify scientific demand',inScope:'read only',outScope:'fixes',
  doneWhen:['Evidence-backed matching','Boundary cases checked']});
const move=(id=M,kind='task',packet='One task\nACK '+M+'\n')=>({
  id,kind,delivery:'sent',packet,returnLine:'',digest:'',evidence:'',gap:'',decision:'',archive:'',note:''});
const encode=p=>String.fromCharCode(96).repeat(3)+'nextnudge-thread-save\n'+gzipSync(JSON.stringify(p)).toString('base64')+
  '\n'+String.fromCharCode(96).repeat(3);
test('NLM seed is a compact summary with immutable v2 archive refs and Owner HOLD',()=>{
  const md=fs.readFileSync(new URL('threads/NN-20261018-171656-66d2.md',root),'utf8');
  assert.ok(Buffer.byteLength(md,'utf8')<15000);
  const x=parse(md);assert.equal(x.hold,'Owner HOLD');assert.equal(x.doneWhen.length,0);
  assert.equal(x.moves.length,4);assert.ok(x.moves.every(m=>m.archive.includes('workbench.json#')));
  assert.ok(x.moves.every(m=>!m.packet));
  assert.equal(serialize(x),md);
  console.log('NLM_THREAD_BYTES='+Buffer.byteLength(md,'utf8'));
});
test('v2 JSON remains unchanged and readable with NLM run',()=>{
  const db=JSON.parse(fs.readFileSync(new URL('workbench.json',root),'utf8'));
  assert.equal(db.formatVersion,2);
  const run=db.runs.find(r=>r.id==='NN-20261018-171656-66d2');
  assert.ok(run);assert.equal(run.nodes.length,5);
  const x=archiveRun(run);assert.equal(x.doneWhen.length,0);
  assert.equal(x.moves.length,4);assert.equal(x.hold,'Owner HOLD');
});
test('exact sent packets are byte-for-byte stable after export/import',()=>{
  const x=example(),raw='## Move\n~~~~~~\nSpecial characters ≤, ñ, ²\nLine two\n';
  x.moves.push(move(M,'task',raw));
  const y=parse(serialize(x));
  assert.equal(y.moves[0].packet,raw);
  assert.equal(Buffer.compare(Buffer.from(y.moves[0].packet),Buffer.from(raw)),0);
  assert.equal(serialize(y),serialize(x));
});
test('Not met quotes the gap; Unknown requests evidence, never correction',()=>{
  const base={nudgeId:M,goal:'Compare physical meaning',reply:'ACK old; wrong encoding',
    agent:'Validator',criteria:['Q19 correctly decoded','Independent units check']};
  const correction=reconcile({...base,checks:['not met','met'],decision:'correct',gap:'Q19 decoded as UTF-8'});
  assert.equal(correction.kind,'correction');assert.match(correction.packet,/Q19 correctly decoded/);
  assert.match(correction.packet,/UTF-8/);
  const ask=reconcile({...base,checks:['unknown','met'],decision:'request evidence'});
  assert.equal(ask.kind,'evidence');assert.match(ask.packet,/UNKNOWN/);
  assert.match(ask.packet,/Q19 correctly decoded/);
  assert.throws(()=>reconcile({...base,checks:['unknown','met'],decision:'close'}),/cannot close/);
});
test('thread outcome and task completion are independent',()=>{
  const x=example();x.moves.push(move());assert.equal(currentState(x),'Waiting on agent');
  x.moves.push({...move('NN-20261019-010103-ff55','reply',''),delivery:'draft',returnLine:'COMPLETE task only'});
  assert.equal(currentState(x),'Your move');
});
test('Owner amendment does not erase original intent or modify earlier packets',()=>{
  const x=example(),original=x.goal;
  x.moves.push({...move(),kind:'amendment',packet:'',delivery:'draft',
    note:'OWNER_INTENT_CHANGE:'+JSON.stringify({goal:'Owner revised outcome',doneWhen:['A observable']})});
  const p=parse(serialize(x));
  assert.equal(p.goal,original);assert.equal(activeIntent(p).goal,'Owner revised outcome');
});
test('no private chat URL can be persisted, even if pasted in reply or packet',()=>{
  const x=example();
  x.moves.push({...move(),kind:'reply',packet:'',delivery:'draft',
    digest:'Agent discussion https://chatgpt.com/c/secret-session'});
  assert.throws(()=>validate(x),/Private chat URL/);
  x.moves[0].digest='No private URL';x.moves[0].evidence='https://github.com/example/evidence';
  assert.doesNotThrow(()=>assertPublic(x));
  x.moves[0].packet='https://claude.ai/chat/abc';
  assert.throws(()=>validate(x),/Private chat URL/);
});
test('append-only delta refuses changed history and stale header',()=>{
  const old=example(),next=structuredClone(old);
  next.moves.push(move());
  const d=delta(next,old,'a'.repeat(40));assert.equal(d.moves.length,1);
  assert.deepEqual(parse(applyDelta(old,d)),next);
  old.moves.push(move());assert.throws(()=>delta(next,old,'a'.repeat(40)),/Nothing new/);
  next.moves[0].packet='altered';assert.throws(()=>delta(next,old,'a'.repeat(40)),/history changed/);
});
test('one-click encoded issue URL is measured at actual length',async()=>{
  const x=example();x.moves.push(move());
  const packet=delta(x,null,null),url=await issueUrl(packet);
  assert.ok(url.length<=7500);assert.match(url,/nextnudge-save/);
  const db=JSON.parse(fs.readFileSync(new URL('workbench.json',root),'utf8'));
  const historical=db.runs.find(r=>r.id==='NN-20261018-171656-66d2');
  const realP2=historical.nodes.find(n=>n.id==='NN-20261018-181514-e812').sentText;
  const large=example();large.moves.push(move(M,'task',realP2));
  const actual=await issueUrl(delta(large,null,null));
  assert.ok(actual.length<=7500,'Actual pilot packet does not fit one-click save');
  console.log('MAX_SAVE_URL_CHARS='+Math.max(url.length,actual.length));
  const body=decodeURIComponent(url.split('&body=')[1]);
  assert.equal(unpack(body).id,ID);
});
test('fixture issue applies a real thread file, with owner guard and SHA rejection',async()=>{
  const x=example();x.moves.push(move());
  const p=delta(x,null,null),body='Owner submit\n'+encode(p);
  const issue={user:{login:'reallakshman19'},state:'open',labels:[{name:'nextnudge-save'}],body};
  assert.ok(ownerIssue(issue,'reallakshman19'));
  let saved=null,receipt='',closed=false;
  const harness={issue,owner:'reallakshman19',read:async()=>null,
    write:async(path,text,sha)=>{assert.equal(path,'site/nextnudge-data/threads/'+ID+'.md');
      assert.equal(sha,null);saved=text;},
    comment:async x=>{receipt=x;},close:async()=>{closed=true;}};
  assert.equal(await applyIssue(harness),'SAVED');
  assert.equal(parse(saved).moves[0].packet,x.moves[0].packet);
  assert.match(receipt,/SAVED:/);assert.ok(closed);
  const bad={...harness,read:async()=>({sha:'a'.repeat(40),content:saved})};
  assert.equal(await applyIssue(bad),'NEEDS RELOAD');
  assert.deepEqual(x.moves,[move()]); // local draft remains unchanged
  assert.equal(await applyIssue({...harness,issue:{...issue,user:{login:'outsider'}}}),'IGNORED');
});
test('all NextNudge R1 touched source files have at most 300 physical lines',()=>{
  const root=new URL('../',import.meta.url);
  const files=['site/nextnudge/index.html','site/nextnudge/v2.html',
    'site/nextnudge/revamp/thread.mjs','site/nextnudge/revamp/save.mjs',
    'site/nextnudge/revamp/app.mjs','site/nextnudge/revamp/style.css',
    'scripts/nextnudge_thread_apply.mjs',
    'scripts/nextnudge_apply.mjs','tests/nextnudge-r1.mjs'];
  for(const path of files){
    const lines=fs.readFileSync(new URL(path,root),'utf8').split('\n').length;
    assert.ok(lines<=300,path+' is '+lines+' lines');
  }
});
