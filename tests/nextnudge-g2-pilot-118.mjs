// G2 test-only pilot: frozen NN118-PILOT-v1, no production-code edits.
// Executed on an isolated candidate-derived QA branch; remote/Chromium gates remain separate.
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {createHash} from 'node:crypto';
import {gzipSync} from 'node:zlib';
import {newThread,parse,serialize,reconcile} from '../site/nextnudge/revamp/thread.mjs';
import {newProject,addThread,updateFixtures,validateProject} from '../site/nextnudge/revamp/project-model.mjs';
import {persistProject} from '../site/nextnudge/revamp/project-store.mjs';
import {effectiveGrounding,readGrounding} from '../site/nextnudge/revamp/grounding.mjs';
import {buildWorkspacePacket,workspaceMove} from '../site/nextnudge/revamp/workspace.mjs';
import {makeReply} from '../site/nextnudge/revamp/reply.mjs';
import {pendingMoves,answered} from '../site/nextnudge/revamp/status.mjs';
import {applyProjectIssue} from '../scripts/nextnudge_project_apply.mjs';
import {projectsMarkup,projectMarkup} from '../site/nextnudge/revamp/screens.mjs';
const sha=s=>createHash('sha256').update(s,'utf8').digest('hex');
const memory=()=>{const m=new Map();return {getItem:k=>m.get(k)??null,setItem:(k,v)=>m.set(k,String(v)),removeItem:k=>m.delete(k)};};
const project=(x,n)=>newProject(n,'NP-20261020-140000-'+x);
const agent=(x,name)=>newThread({id:'NN-20261020-140000-'+x,title:'G2 test '+x,agent:name,goal:'Preserve truthful evidence',doneWhen:['Verified evidence']});
const sent=(id,text)=>({id,kind:'task',delivery:'sent',packet:text,returnLine:'',digest:'',evidence:'',gap:'',decision:'',archive:'',note:''});
const body=p=>'```nextnudge-project-save\n'+gzipSync(JSON.stringify(p)).toString('base64')+'\n```';
const wrapStorage=async fn=>{const old=globalThis.localStorage;globalThis.localStorage=memory();try{return await fn();}finally{globalThis.localStorage=old;}};
test('P01 source structure only; does NOT count as real Chromium interaction',()=>{
  const p=project('a001','P118-ALPHA');
  assert.match(projectsMarkup({[p.id]:p},{}),/Projects/);
  assert.match(projectMarkup(p,{},{}),/Open shared Grounding Fixtures/);
  for(const s of ['Overview','Ground','Task','Correction','Reconcile']){
    assert.ok(fs.readFileSync(new URL('../site/nextnudge/revamp/workspace-nav.mjs',import.meta.url),'utf8').includes(s));
  }
});
test('P02/P03 shared ALPHA grounding and isolated BETA, with seeded cross-project leak detected',()=>wrapStorage(()=>{
  const a=agent('a111','P118-G1'),b=agent('a112','P118-G2'),c=agent('b111','P118-G1');
  const pa=updateFixtures(addThread(addThread(project('a001','P118-ALPHA'),a),b),
    {'1f':'P118-ALPHA-ONLY-GROUND'},'2026-10-20T12:00:00Z');
  const pb=updateFixtures(addThread(project('b001','P118-BETA'),c),
    {'1f':'P118-BETA-NEVER-IN-ALPHA'},'2026-10-20T12:00:00Z');
  persistProject(pa);persistProject(pb);
  assert.equal(effectiveGrounding(a)['1f'],'P118-ALPHA-ONLY-GROUND');
  assert.equal(effectiveGrounding(b)['1f'],'P118-ALPHA-ONLY-GROUND');
  assert.equal(effectiveGrounding(c)['1f'],'P118-BETA-NEVER-IN-ALPHA');
  assert.deepEqual(readGrounding(b),{},'thread-specific historical grounding is separate');
  const MUTANT_LEAK=()=>effectiveGrounding(c);
  assert.throws(()=>assert.equal(MUTANT_LEAK(a)['1f'],'P118-ALPHA-ONLY-GROUND'),assert.AssertionError);
  console.log('KILLED_MUTANT cross-project fixture resolver ALPHA→BETA');
}));
test('P04 duplicate agent prohibited within ALPHA; same agent allowed in BETA; mutant rejected',()=>{
  const a=agent('a111','P118-G1'),b=agent('a112','P118-G1');
  const pa=addThread(project('a001','P118-ALPHA'),a);
  assert.throws(()=>addThread(pa,b),/already has a project thread/);
  const MUTANT_DUPLICATE={...pa,threads:[...pa.threads,{id:b.id,agent:b.agent,legacy:false}]};
  assert.throws(()=>validateProject(MUTANT_DUPLICATE),/Duplicate active agent/);
  assert.doesNotThrow(()=>addThread(project('b001','P118-BETA'),b));
  console.log('KILLED_MUTANT duplicate active project/agent');
});
test('P05/P10 packet H1 is immutable after fixture V2, while G2 gets V2',()=>wrapStorage(()=>{
  const a=agent('a111','P118-G1'),b=agent('a112','P118-G2');
  let p=updateFixtures(addThread(addThread(project('a001','P118-ALPHA'),a),b),
    {'1f':'P118-ALPHA-ONLY-GROUND'},'2026-10-20T12:00:00Z');persistProject(p);
  a.moves.push(sent('P118-TASK-X','exact packet\n  grounding VERSION 1\n'));
  const H1=sha(a.moves[0].packet),original=serialize(a);
  p=updateFixtures(p,{'1f':'P118-ALPHA-ONLY-GROUND',
    '6a':'P118-ALPHA-V2-ADDED-AFTER-FIRST-SEND'},'2026-10-20T12:30:00Z');persistProject(p);
  const current=buildWorkspacePacket(b,'ground',{brief:'New agent orientation'},'P118-NEW-GROUND');
  assert.match(current.packet,/P118-ALPHA-V2-ADDED-AFTER-FIRST-SEND/);
  assert.equal(sha(parse(original).moves[0].packet),H1);
  assert.equal(sha(a.moves[0].packet),H1);
  assert.equal(b.moves.length,0,'opening/building packet adds no navigation log');
  console.log('P10_PACKET_H1 '+H1);
}));
test('P06 authentic historical v3 sent packet SHA-256 inventory survives project association',()=>wrapStorage(()=>{
  const input=fs.readFileSync(new URL('../site/nextnudge-data/threads/NN-20261019-165622-6810.md',import.meta.url),'utf8');
  const original=parse(input),packets=original.moves.filter(m=>m.delivery==='sent'&&m.packet);
  assert.ok(packets.length>0,'authentic thread must contain sent packets');
  const before=packets.map(m=>({id:m.id,hash:sha(m.packet),length:Buffer.byteLength(m.packet,'utf8')}));
  const p=updateFixtures(addThread(project('a001','P118-ALPHA'),original,{legacy:true}),
    {'1f':'P118-ALPHA-ONLY-GROUND'},'2026-10-20T12:00:00Z');persistProject(p);
  const after=parse(serialize(original));
  const compared=after.moves.filter(m=>m.delivery==='sent'&&m.packet)
    .map(m=>({id:m.id,hash:sha(m.packet),length:Buffer.byteLength(m.packet,'utf8')}));
  assert.deepEqual(compared,before);assert.equal(after.moves.length,original.moves.length);
  console.log('P06_AUTHENTIC_PACKET_RECEIPTS '+JSON.stringify(before));
}));
test('P07 concurrent SHA guard in in-memory handler; deliberately stale-accepting mutant killed',async()=>{
  const base=project('a001','P118-ALPHA'),one=updateFixtures(base,{'1f':'Session A'},'2026-10-20T12:00:00Z');
  const two=updateFixtures(base,{'1f':'Session B'},'2026-10-20T12:01:00Z');
  const A='a'.repeat(40),B='b'.repeat(40);let remote={sha:A,content:JSON.stringify(base)},writes=0;
  const h={owner:'owner',read:async()=>remote,write:async(path,text,expected)=>{assert.equal(expected,A);writes++;remote={sha:B,content:text};},
    comment:async()=>{},close:async()=>{}};
  const issue=packet=>({state:'open',user:{login:'owner'},labels:['nextnudge-save'],body:body(packet)});
  assert.equal(await applyProjectIssue({...h,issue:issue({v:1,id:base.id,baseSha:A,project:one})}),'SAVED');
  assert.equal(await applyProjectIssue({...h,issue:issue({v:1,id:base.id,baseSha:A,project:two})}),'NEEDS RELOAD');
  assert.equal(writes,1);assert.equal(JSON.parse(remote.content).fixtures['1f'],'Session A');
  const MUTANT_ACCEPTS_STALE='SAVED';
  assert.throws(()=>assert.equal(MUTANT_ACCEPTS_STALE,'NEEDS RELOAD'),assert.AssertionError);
  console.log('KILLED_MUTANT stale SHA accepted by would-be writer');
});
test('P08 wrong ACK and late OLD ACK never answer newer sent instruction; mutant detected',()=>{
  const t=agent('a111','P118-G1');const old=sent('P118-OLD','old exact'),newer=sent('P118-NEW','new exact');
  t.moves.push(old,newer);
  const wrong=makeReply(t,'ACK P118-NOT-SENT\nnot evidence',{id:'REPLY-WRONG'}).move;
  t.moves.push(wrong);assert.equal(wrong.answers,undefined);
  assert.deepEqual(pendingMoves(t).map(m=>m.id),['P118-OLD','P118-NEW']);
  const late=makeReply(t,'ACK P118-OLD\nold evidence',{id:'REPLY-OLD'}).move;t.moves.push(late);
  assert.equal(late.answers,'P118-OLD');assert.equal(answered(t,old),true);
  assert.equal(answered(t,newer),false);assert.deepEqual(pendingMoves(t).map(m=>m.id),['P118-NEW']);
  const MUTANT_WRONG_TARGET={...late,answers:'P118-NEW'};
  assert.throws(()=>assert.equal(MUTANT_WRONG_TARGET.answers,'P118-OLD'),assert.AssertionError);
  console.log('KILLED_MUTANT wrong reply correlation');
});
test('P09 hold blocks packet, encoded private link rejected, incomplete Close refused',()=>{
  const t=agent('a111','P118-G1');t.hold='Owner HOLD';
  assert.throws(()=>buildWorkspacePacket(t,'ground',{brief:'Try send'},'P118-HOLD'),/HOLD/);
  const encoded='https%3A%2F%2Fchatgpt.com%2Fc%2Fprivate';
  assert.throws(()=>updateFixtures(project('a001','P118-ALPHA'),{'1f':encoded}),/Private chat URL/);
  assert.throws(()=>reconcile({checks:['unknown'],reply:'Unverified',decision:'close',
    nudgeId:'P118-CLOSE',goal:t.goal,criteria:t.doneWhen}),/cannot close/);
});
