import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {gzipSync} from 'node:zlib';
import {newThread,parse,serialize,validate,archiveRun,currentState,closureMet,reconcile,assertPublic,activeIntent} from '../site/nextnudge/revamp/thread.mjs';
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
  for(const secret of ['https://chatgpt.com/share/secret','https://gemini.google.com/app/secret',
    'https://claude.ai/chat/secret','https://poe.com/chat/secret']) {
    x.moves[0].packet=secret;
    assert.throws(()=>validate(x),/Private chat URL/,secret);
  }
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

test('Close is a Reconcile-only decision; Unknown and Not met never show Done',()=>{
  const x=example(),criteria=x.doneWhen;
  const close=(checks,note)=>({...move(M,'close','Close packet'),note:
    'OWNER_CLOSE_CHECKS:'+JSON.stringify({criteria,checks})});
  const reply={...move('NN-20261019-010103-ff55','reply',''),delivery:'draft',returnLine:'ACK completed'};
  const page=fs.readFileSync(new URL('../site/nextnudge/revamp/app.mjs',import.meta.url),'utf8');
  assert.doesNotMatch(page,/data-action="compose-close"/);
  assert.match(page,/Close via Reconcile/);
  for(const checks of [['met','unknown'],['not met','met']]){
    assert.throws(()=>reconcile({checks,decision:'close',criteria,
      nudgeId:M,goal:x.goal}),/cannot close/);
    x.moves=[close(checks),reply];
    assert.equal(closureMet(x,x.moves[0]),false);
    assert.notEqual(currentState(x),'Done');
  }
  x.moves=[{...move(M,'close'),note:''},reply];
  assert.notEqual(currentState(x),'Done','forged Close without a review receipt');
  const approved=reconcile({checks:['met','met'],decision:'close',criteria,
    nudgeId:M,goal:x.goal});
  x.moves=[close(approved.closure.checks),reply];
  assert.equal(currentState(x),'Done');
  x.doneWhen=['Owner changed acceptance']; // old review can no longer close new outcome
  assert.notEqual(currentState(x),'Done');
});
test('privacy: schemeless, encoded and AI Studio chat references are refused client and server',async()=>{
  const secrets=['chatgpt.com/c/x','claude.ai/chat/x',
    'https%3A%2F%2Fchatgpt.com%2Fc%2Fx','aistudio.google.com/prompts/abc'];
  const header=example();delete header.moves;
  const original=example();let written=0;
  for(const field of ['packet','digest'])for(const secret of secrets){
    const candidate={...move(),[field]:'Agent output '+secret};
    const local={...original,moves:[candidate]};
    assert.throws(()=>validate(local),/Private chat URL/,field+' '+secret);
    const payload={v:3,id:ID,baseSha:null,expectedCount:0,header,moves:[candidate]};
    const body='Owner review\n'+encode(payload);
    assert.throws(()=>unpack(body),/Private chat URL/,field+' '+secret);
    const issue={user:{login:'reallakshman19'},state:'open',labels:[{name:'nextnudge-save'}],body};
    let receipt='';
    const result=await applyIssue({issue,owner:'reallakshman19',read:async()=>null,
      write:async()=>{written++;},comment:async v=>{receipt=v;},close:async()=>{}});
    assert.equal(result,'REJECTED');assert.match(receipt,/Private chat URL/);
  }
  assert.equal(written,0,'privacy rejection must not write any thread');
});
test('reserved metadata injected into a packet is rejected by client and server before write',async()=>{
  const header=example();delete header.moves;
  for(const marker of ['<!-- nn3:header','<!-- nn3:move']){
    const item={...move(),packet:'Original work\n'+marker+'\n{"fake":true}\n'};
    assert.throws(()=>serialize({...example(),moves:[item]}),/Reserved thread metadata marker/);
    const issue={user:{login:'reallakshman19'},state:'open',
      labels:[{name:'nextnudge-save'}],body:'Review\n'+encode({
        v:3,id:ID,baseSha:null,expectedCount:0,header,moves:[item]})};
    let writes=0,receipt='';
    const status=await applyIssue({issue,owner:'reallakshman19',read:async()=>null,
      write:async()=>{writes++;},comment:async v=>{receipt=v;},close:async()=>{}});
    assert.equal(status,'REJECTED');assert.equal(writes,0);
    assert.match(receipt,/Reserved thread metadata marker/);
  }
});
test('Windows CRLF converts safely to LF and LF source preserves packet bytes',()=>{
  const seed=fs.readFileSync(new URL('threads/NN-20261018-171656-66d2.md',root),'utf8');
  const converted=parse(seed.replace(/\n/g,'\r\n'));
  assert.equal(converted.hold,'Owner HOLD');
  assert.equal(serialize(converted),seed);
  const raw='First line\nSecond line\n'+String.fromCharCode(0x2603);
  const x=example();x.moves.push(move(M,'task',raw));
  assert.equal(parse(serialize(x)).moves[0].packet,raw);
  const attrs=fs.readFileSync(new URL('../.gitattributes',import.meta.url),'utf8');
  assert.match(attrs,/site\/nextnudge-data\/threads\/\*\.md text eol=lf/);
});


test('FIX2 chat-host privacy: client and server refuse leaks but allow GitHub evidence',async()=>{
  const refused=[
    'chatgpt.com/c/x','claude.ai/chat/x',
    'https%3A%2F%2Fchatgpt.com%2Fc%2Fx',
    'aistudio.google.com/prompts/example',
    '100% sure https%3A%2F%2Fchatgpt.com%2Fc%2Fx',
    'https%3A%2F%2Fchatgpt.com%2Fc%2Fx 100%',
    '50% confident https%253A%252F%252Fchatgpt.com%252Fc%252Fx',
    'https://chatgpt.com/g/g-p-123-name/c/68f0',
    'chatgpt.com/g/g-p-123-name/c/68f0',
    'https://chat.openai.com/g/g-p-123-name/c/68f0',
    'chat.openai.com/g/g-p-123-name/c/68f0',
    'https://chatgpt.com/share/id',
    'HTTPS://CHATGPT.COM/C/X',
    'https://chatg\u200Bpt.com/c/x',
    'https://chatgpt.com/\u200Bc/x',
    'https://claude.ai/chat/x',
    'https://gemini.google.com/app/x',
    'https://aistudio.google.com/prompts/x',
    'https://antigravity.google.com/chat/x',
    'https://copilot.microsoft.com/chat/x',
    'https://chat.mistral.ai/chat/x',
    'https://grok.com/chat/x',
    'https://chat.deepseek.com/chat/x'
  ];
  const allowed=[
    'chatgpt.com',
    'github.com/o/r/pull/1',
    'https://github.com/o/r/blob/main/docs/chat/readme.md',
    'https://github.com/o/r/blob/main/conversations/answer.md',
    'https://github.com/o/r/blob/main/docs/antigravity-notes.md',
    '100% sure'
  ];
  const header=example();delete header.moves;
  const testItem=(field,value)=>({...move(),[field]:'Agent supplied: '+value});
  const runServer=async item=>{
    const p={v:3,id:ID,baseSha:null,expectedCount:0,header,moves:[item]};
    const issue={user:{login:'reallakshman19'},state:'open',
      labels:[{name:'nextnudge-save'}],body:'Owner review\n'+encode(p)};
    let writes=0,receipt='';
    const status=await applyIssue({issue,owner:'reallakshman19',
      read:async()=>null,write:async()=>{writes++;},
      comment:async v=>{receipt=v;},close:async()=>{}});
    return {status,writes,receipt,body:issue.body};
  };
  for(const field of ['packet','digest']){
    for(const value of refused){
      const item=testItem(field,value);
      assert.throws(()=>validate({...example(),moves:[item]}),/Private chat URL/,
        'client '+field+' '+value);
      const server=await runServer(item);
      assert.throws(()=>unpack(server.body),/Private chat URL/,'unpack '+field+' '+value);
      assert.equal(server.status,'REJECTED','server '+field+' '+value);
      assert.equal(server.writes,0,'no saved private URL '+field+' '+value);
    }
    for(const value of allowed){
      const item=testItem(field,value);
      assert.doesNotThrow(()=>validate({...example(),moves:[item]}),'client '+field+' '+value);
      const server=await runServer(item);
      assert.doesNotThrow(()=>unpack(server.body),'unpack '+field+' '+value);
      assert.equal(server.status,'SAVED','server '+field+' '+value);
      assert.equal(server.writes,1,'GitHub evidence can be saved: '+value);
    }
  }
});
test('FIX2 Reconcile keeps selected check verdicts through redraw',()=>{
  const app=fs.readFileSync(new URL('../site/nextnudge/revamp/app.mjs',import.meta.url),'utf8');
  assert.match(app,/state\.checks=checks/);
  assert.match(app,/\(state\.checks\[j\]\|\|'unknown'\)===v/);
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
