import test from 'node:test';
import assert from 'node:assert/strict';
import {gzipSync} from 'node:zlib';
import {newThread,serialize} from '../site/nextnudge/revamp/thread.mjs';
import {newProject,addThread} from '../site/nextnudge/revamp/project-model.mjs';
import {localProjects,localProjectIssues,persistProject,assertProjectAgent,verifyProjectThreads} from '../site/nextnudge/revamp/project-store.mjs';
import {prepareAction} from '../site/nextnudge/revamp/transport-request.mjs';
import {applyProjectIssue} from '../scripts/nextnudge_project_apply.mjs';
import {applyAction} from '../scripts/nextnudge_action_apply.mjs';
import {applyIssue as applyThreadIssue} from '../scripts/nextnudge_thread_apply.mjs';
import {loadRemoteProjects,checkManagedSend} from '../scripts/nextnudge_project_guard.mjs';
const A='a'.repeat(40),B='b'.repeat(40),fence=String.fromCharCode(96).repeat(3);
const memory=()=>{const rows=new Map();return {getItem:key=>rows.get(key)??null,
  setItem:(key,val)=>rows.set(key,val),raw:rows};};
const one=()=>newThread({id:'NN-20261020-141500-a001',title:'G1',goal:'Keep G1 identity',agent:'G1'});
const two=()=>newThread({id:'NN-20261020-141500-a002',title:'G2',goal:'Keep G2 identity',agent:'G2'});
const members=()=>{const t1=one(),t2=two();
  return {t1,t2,p:addThread(addThread(newProject('ALPHA','NP-20261020-141500-f001'),t1),t2)};};
const issue=body=>({number:99,user:{login:'owner'},state:'open',labels:[{name:'nextnudge-save'}],body});
const packetBody=(kind,packet)=>fence+kind+'\n'+gzipSync(JSON.stringify(packet)).toString('base64')+'\n'+fence;
test('F1 managed agent G2 cannot send from G1 thread, but legacy flexibility remains',()=>{
  const {t1,t2,p}=members(),projects={[p.id]:p};
  assert.throws(()=>assertProjectAgent(t1,'G2',projects),/Project agent mismatch/);
  assert.equal(assertProjectAgent(t1,'  g1 ',projects),'G1');
  assert.equal(assertProjectAgent(t2,'G2',projects),'G2');
  assert.equal(serialize(t1),serialize(one()));
  assert.equal(assertProjectAgent(one(),'G2',{}),null);
  assert.throws(()=>checkManagedSend(t1,'G2',projects),/Project agent mismatch/);
});
test('F1 browser GitHub preparation rejects mismatched agent before network',async()=>{
  const store=memory(),old=globalThis.localStorage,oldFetch=globalThis.fetch;
  globalThis.localStorage=store;let network=0;globalThis.fetch=async()=>{network++;throw Error('unexpected');};
  try{
    const {t1,p}=members();persistProject(p);
    const draft={id:'TASK-1',kind:'task',packet:'Task. Start your reply with ACK TASK-1.'};
    await assert.rejects(prepareAction(t1,'send',{draft,packet:draft.packet,issue:118,agent:'G2'}),/Project agent mismatch/);
    assert.equal(network,0);assert.equal(t1.moves.length,0);
  }finally{globalThis.localStorage=old;globalThis.fetch=oldFetch;}
});
test('F1 GitHub action consumer rejects cross-agent send without posting',async()=>{
  const {t1,p}=members();
  const move={id:'TASK-1',kind:'task',delivery:'sent',packet:'Task. Start your reply with ACK TASK-1.',
    returnLine:'',digest:'',evidence:'',gap:'',decision:'',archive:'',note:'',agent:'G2'};
  const packet={v:1,operation:'send',target:{repository:'reallakshman19/CoordinatorLandingpage',issue:118,agent:'G2'},
    delta:{v:3,id:t1.id,baseSha:A,expectedCount:0,moves:[]},move};
  let posts=0,writes=0;const receipts=[];
  const result=await applyAction({issue:issue(packetBody('nextnudge-thread-action',packet)),owner:'owner',
    projects:{[p.id]:p},read:async()=>({sha:A,content:serialize(t1)}),
    postComment:async()=>{posts++;},listComments:async()=>[],write:async()=>{writes++;},
    comment:async msg=>receipts.push(msg),close:async()=>{}});
  assert.equal(result,'REJECTED');assert.equal(posts+writes,0);
  assert.match(receipts[0],/Project agent mismatch/);
});
test('F1 manual thread-save consumer rejects G2 sent packet on G1 thread',async()=>{
  const {t1,p}=members();
  const sent={id:'TASK-1',kind:'task',delivery:'sent',packet:'Task. ACK TASK-1.',
    returnLine:'',digest:'',evidence:'',gap:'',decision:'',archive:'',note:'',agent:'G2'};
  const packet={v:3,id:t1.id,baseSha:A,expectedCount:0,moves:[sent]};
  let writes=0;const receipts=[];
  const result=await applyThreadIssue({issue:issue(packetBody('nextnudge-thread-save',packet)),owner:'owner',
    projects:{[p.id]:p},read:async()=>({sha:A,content:serialize(t1)}),
    write:async()=>{writes++;},comment:async msg=>receipts.push(msg),close:async()=>{}});
  assert.equal(result,'REJECTED');assert.equal(writes,0);
  assert.match(receipts[0],/Project agent mismatch/);
});
test('F2 project publication rejects missing member, then succeeds after thread-first save',async()=>{
  const {t1,t2,p}=members(),packet={v:1,id:p.id,baseSha:null,project:p};
  const fixtures={[t1.id]:{sha:A,content:serialize(t1)},[t2.id]:{sha:B,content:serialize(t2)}};
  let writes=0;const receipts=[];let omitted=t2.id;
  const call=()=>applyProjectIssue({issue:issue(packetBody('nextnudge-project-save',packet)),
    owner:'owner',read:async path=>{
      if(path.endsWith('.json'))return null;
      const id=path.split('/').at(-1).replace('.md','');
      return id===omitted?null:fixtures[id]||null;
    },write:async()=>{writes++;},comment:async msg=>receipts.push(msg),close:async()=>{}});
  assert.equal(await call(),'REJECTED');assert.equal(writes,0);
  assert.match(receipts.at(-1),/THREAD_FIRST.*G2/);
  omitted=null;
  assert.equal(await call(),'SAVED');assert.equal(writes,1);
});
test('F2 preflight missing remote thread keeps device project membership intact',async()=>{
  const {p,t1,t2}=members();let reads=[];
  await assert.rejects(verifyProjectThreads(p,async id=>{
    reads.push(id);return id===t1.id?{thread:t1,sha:A}:{thread:null,sha:null};
  }),/Save thread G2.*before saving this project/);
  assert.deepEqual(reads,[t1.id,t2.id]);assert.equal(p.threads.length,2);
  assert.equal(await verifyProjectThreads(p,async id=>({thread:id===t1.id?t1:t2,sha:A})),true);
});
test('F3 corrupt project entry is isolated without deleting raw or valid project data',()=>{
  const old=globalThis.localStorage,store=memory();globalThis.localStorage=store;
  try{
    const {p}=members(),bad={version:999,diagnostic:'preserve bytes'},key='nextnudge.projects.v1';
    store.setItem(key,JSON.stringify({BAD:bad,[p.id]:p}));
    assert.deepEqual(Object.keys(localProjects()),[p.id]);
    assert.deepEqual(localProjectIssues(),{invalid:1,unreadable:false});
    const next=newProject('Beta','NP-20261020-141500-f002');persistProject(next);
    assert.deepEqual(JSON.parse(store.getItem(key)).BAD,bad);
    assert.deepEqual(Object.keys(localProjects()).sort(),[next.id,p.id].sort());
    store.setItem(key,'{broken-json!');
    assert.deepEqual(localProjects(),{});assert.deepEqual(localProjectIssues(),{invalid:1,unreadable:true});
    assert.throws(()=>persistProject(next),/original bytes preserved/);
    assert.equal(store.getItem(key),'{broken-json!');
  }finally{globalThis.localStorage=old;}
});
test('F1 remote authority loads canonical project snapshots, rejecting malformed data',async()=>{
  const {p,t1}=members(),files=[{name:p.id+'.json'},{name:'.gitkeep'}];
  const api=async path=>path.endsWith('/projects?ref=main')?files:{
    encoding:'base64',sha:A,content:Buffer.from(JSON.stringify(p)).toString('base64')};
  const projects=await loadRemoteProjects(api);
  assert.equal(Object.keys(projects).length,1);
  assert.throws(()=>checkManagedSend(t1,'G2',projects),/Project agent mismatch/);
  await assert.rejects(loadRemoteProjects(async path=>path.endsWith('/projects?ref=main')?files:{
    encoding:'base64',sha:A,content:Buffer.from('{corrupt').toString('base64')}),SyntaxError);
});
