import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {newThread,currentState,serialize,parse} from '../site/nextnudge/revamp/thread.mjs';
import {makeReply,openMoves} from '../site/nextnudge/revamp/reply.mjs';

const repo='reallakshman19/CoordinatorLandingpage';
const source='https://github.com/'+repo+'/issues/110';
const thread=()=>newThread({id:'NN-20261019-170000-110a',title:'Simple grounding',
  agent:'pilot-agent',goal:'Keep the real Owner outcome',inScope:'Read-only pilot',
  outScope:'No product edits',doneWhen:['Actual matching reply retained']});
const move=(id,kind='task',note='')=>({id,kind,delivery:'sent',packet:'Task '+id,
  returnLine:'',digest:'',evidence:'',gap:'',decision:'',archive:'',note});
const memory=()=>{const db=new Map();return {getItem:k=>db.get(k)??null,setItem:(k,v)=>db.set(k,v),removeItem:k=>db.delete(k)};};

test('NN110: current thread exposes Grounding Fixtures without restoring the old ladder',()=>{
  const page=fs.readFileSync(new URL('../site/nextnudge/revamp/app.mjs',import.meta.url),'utf8');
  assert.match(page,/Grounding Fixtures/);
  assert.match(page,/grounding/);
  assert.doesNotMatch(page,/from ['"]\.\.\/workspace\.mjs/);
});
test('NN110: a late reply leaves the newer task waiting; unmatched ACK cannot answer it',()=>{
  const t=thread();t.moves.push(move('old'),move('current'));
  t.moves.push(makeReply(t,'ACK old\nEarlier result',{id:'late'}).move);
  assert.equal(currentState(t),'Waiting on agent');
  t.moves.push(makeReply(t,'ACK unknown\nUnrelated result',{id:'unmatched'}).move);
  assert.equal(currentState(t),'Waiting on agent');
  assert.deepEqual(openMoves(t).map(m=>m.id),['current']);
  t.moves.push(makeReply(t,'ACK current\nActual current result',{id:'right'}).move);
  assert.equal(currentState(t),'Your move');
});
test('NN110: Done requires a reply to the exact close move, not an older task',()=>{
  const t=thread();t.moves.push(move('old'));
  t.moves.push(makeReply(t,'ACK old\nDone',{id:'old-return'}).move);
  t.moves.push(move('close-now','close','OWNER_CLOSE_CHECKS:'+JSON.stringify({criteria:t.doneWhen,checks:['met']})));
  t.moves.push(makeReply(t,'ACK old\nLate repeat',{id:'late'}).move);
  assert.equal(currentState(t),'Waiting on agent');
  t.moves.push(makeReply(t,'ACK close-now\nFinal pointer',{id:'close-return'}).move);
  assert.equal(currentState(t),'Done');
});
test('NN110: grounding is one source-bound snapshot per save; sent history stays unchanged',async()=>{
  const {groundingMove,readGrounding,groundingText}=await import('../site/nextnudge/revamp/grounding.mjs');
  const t=thread();t.moves.push(move('sent'));
  const original=serialize(t);
  const values={'1a':source,'1f':'I will restore simple context.','3':'UNKNOWN'};
  t.moves.push(groundingMove(t,values,'ground-1'));
  assert.deepEqual(readGrounding(parse(serialize(t))),values);
  assert.equal(t.moves.length,2,'one update is one move, not one manual record per field');
  assert.equal(serialize({...t,moves:t.moves.slice(0,1)}),original);
  assert.match(groundingText(t),/I will restore simple context/);
  assert.equal(groundingMove(t,values,'unchanged'),null,'unchanged save adds no history');
  assert.throws(()=>groundingMove(t,{'not-a-heading':'invented'}),/heading/);
  assert.throws(()=>groundingMove(t,{'1':'https://chatgpt.com/c/private'}),/Private chat URL/);
});
test('NN110: unsent composers persist separately per thread and can be cleared on send',async()=>{
  const {rememberComposer,restoreComposer,clearComposer}=await import('../site/nextnudge/revamp/composer.mjs');
  const storage=memory(),a=thread().id,b='NN-20261019-170001-110b';
  const draft={id:'draft-1',kind:'task',packet:'An unfinished exact packet'};
  rememberComposer(a,draft,storage);
  assert.deepEqual(restoreComposer(a,storage),draft);
  assert.equal(restoreComposer(b,storage),null);
  clearComposer(a,storage);assert.equal(restoreComposer(a,storage),null);
});
test('NN110: GitHub transport posts once, retains exact packet and attaches the matching named return',async()=>{
  const {sendNudge,fetchReturn}=await import('../site/nextnudge/revamp/transport.mjs');
  const t=thread(),m=move('pilot-1'),target={repository:repo,issue:110,agent:'pilot-agent'};
  const comments=[];let posts=0;
  const api={listComments:async()=>comments,postComment:async(_target,body)=>{
    posts++;const c={body,html_url:source+'#issuecomment-123',created_at:'2026-10-19T17:00:00Z',user:{login:'github-actions[bot]'}};comments.push(c);return c;
  }};
  const sent=await sendNudge(t,m,target,api);assert.equal(posts,1);
  assert.equal(sent.packet,m.packet);assert.equal(sent.evidence,source+'#issuecomment-123');
  assert.match(comments[0].body,/^TO: pilot-agent/);
  assert.deepEqual(await sendNudge(t,m,target,api),sent);assert.equal(posts,1,'recovery cannot duplicate a posted packet');
  t.moves.push(sent);
  comments.push({body:'ACK wrong\nFROM: pilot-agent',html_url:source+'#issuecomment-124'});
  comments.push({body:'ACK pilot-1\nFROM: other-agent',html_url:source+'#issuecomment-125'});
  assert.equal(await fetchReturn(t,'pilot-1',api),null);
  comments.push({body:'ACK pilot-1\nFROM: pilot-agent\nRead-only result',html_url:source+'#issuecomment-126',created_at:'2026-10-19T17:01:00Z'});
  const reply=await fetchReturn(t,'pilot-1',api);assert.equal(reply.answers,'pilot-1');
  assert.equal(reply.evidence,source+'#issuecomment-126');assert.match(reply.replyText,/Read-only result/);
  t.moves.push(reply);assert.equal(await fetchReturn(t,'pilot-1',api),null,'same comment is not imported twice');
});
test('NN110: transport respects HOLD and rejects changed retries and unsupported repository targets before posting',async()=>{
  const {sendNudge}=await import('../site/nextnudge/revamp/transport.mjs');
  const t=thread(),target={repository:repo,issue:110,agent:'pilot-agent'};let posts=0;
  const api={listComments:async()=>[],postComment:async()=>{posts++;}};
  t.hold='Owner HOLD';await assert.rejects(sendNudge(t,move('p'),target,api),/HOLD/);
  t.hold='';await assert.rejects(sendNudge(t,move('p'),{...target,repository:'another/repo'},api),/repository/);
  assert.equal(posts,0);
});
