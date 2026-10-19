import test from 'node:test';
import assert from 'node:assert/strict';
import {gzipSync} from 'node:zlib';
import {newThread,serialize,parse} from '../site/nextnudge/revamp/thread.mjs';
import {applyAction,unpackAction} from '../scripts/nextnudge_action_apply.mjs';
import {sweepUnreceipted} from '../scripts/nextnudge_apply.mjs';
const repo='reallakshman19/CoordinatorLandingpage',sha='a'.repeat(40);
const target={repository:repo,issue:110,agent:'pilot-agent'};
const thread=()=>newThread({id:'NN-20261019-173000-aa11',title:'Transport check',goal:'Actual matching return'});
const move={id:'ACTION-1',kind:'task',delivery:'sent',packet:'Read the source. Start your reply with ACK ACTION-1.',
  returnLine:'',digest:'',evidence:'',gap:'',decision:'',archive:'',note:''};
const request=t=>({v:1,operation:'send',target,move,delta:{v:3,id:t.id,baseSha:sha,expectedCount:t.moves.length,moves:[]}});
const encode=x=>'```nextnudge-thread-action\n'+gzipSync(JSON.stringify(x)).toString('base64')+'\n```';
function harness(t=thread()){
  const h={reads:0,posts:0,writes:0,comments:[],saved:'',receipt:'',source:serialize(t)};
  h.args={issue:{user:{login:'reallakshman19'},state:'open',labels:[{name:'nextnudge-save'}],body:encode(request(t))},
    owner:'reallakshman19',read:async()=>{h.reads++;return {sha,content:h.source};},
    write:async(_path,text)=>{h.writes++;h.saved=text;},
    listComments:async()=>h.comments,
    postComment:async(_target,body)=>{h.posts++;const c={body,html_url:'https://github.com/'+repo+'/issues/110#issuecomment-100',
      created_at:'2026-10-19T17:30:00Z',user:{login:'github-actions[bot]'}};h.comments.push(c);return c;},
    comment:async body=>{h.receipt=body;},close:async()=>{}};
  return h;
}
test('NN110 action: unauthorized/closed requests perform zero provider operations',async()=>{
  for(const patch of [{user:{login:'other'}},{state:'closed'}]){
    const h=harness();h.args.issue={...h.args.issue,...patch};
    assert.equal(await applyAction(h.args),'IGNORED');assert.equal(h.reads+h.posts+h.writes,0);
  }
});
test('NN110 action: malformed paths, external repositories and private chat values fail before read/post',async()=>{
  for(const edit of [x=>{x.delta.id='../elsewhere';},x=>{x.target={...target,repository:'other/project'};},
    x=>{x.move={...move,packet:'https://chatgpt.com/c/private'};}]){
    const h=harness(),r=request(thread());edit(r);h.args.issue.body=encode(r);
    assert.equal(await applyAction(h.args),'REJECTED');assert.equal(h.reads+h.posts+h.writes,0);
  }
});
test('NN110 action: stale SHA never sends; successful action appends exact packet and real receipt',async()=>{
  const stale=harness();stale.args.read=async()=>({sha:'b'.repeat(40),content:stale.source});
  assert.equal(await applyAction(stale.args),'REJECTED');assert.equal(stale.posts+stale.writes,0);
  assert.match(stale.receipt,/NEEDS RELOAD/);
  const h=harness();assert.equal(await applyAction(h.args),'SAVED');
  assert.equal(h.posts,1);assert.equal(h.writes,1);
  const saved=parse(h.saved);assert.equal(saved.moves[0].packet,move.packet);
  assert.match(saved.moves[0].evidence,/#issuecomment-100$/);
});
test('NN110 action: a failed record reports real delivery, and retry recovers without posting twice',async()=>{
  const h=harness(),write=h.args.write;h.args.write=async()=>{throw Error('CAS conflict');};
  assert.equal(await applyAction(h.args),'DELIVERED_NOT_RECORDED');
  assert.match(h.receipt,/#issuecomment-100/);assert.equal(h.posts,1);
  h.args.write=write;
  assert.equal(await applyAction(h.args),'SAVED');assert.equal(h.posts,1);assert.equal(h.writes,1);
});
test('NN110 action: changed retry content is refused rather than posted under the same identity',async()=>{
  const h=harness();await applyAction(h.args);
  const r=request(thread());r.move={...move,packet:'Changed instructions under old ID'};h.args.issue.body=encode(r);
  assert.equal(await applyAction(h.args),'REJECTED');assert.equal(h.posts,1);
  assert.match(h.receipt,/Changed retry packet/);
});
test('NN110 action: fetch keeps wrong ACK/agent unlinked, then appends actual raw return and comment URL',async()=>{
  const h=harness();await applyAction(h.args);h.source=h.saved;
  const t=parse(h.saved),r={v:1,operation:'fetch',target,moveId:move.id,
    delta:{v:3,id:t.id,baseSha:sha,expectedCount:t.moves.length,moves:[]}};
  h.args.issue.body=encode(r);h.comments.push({body:'ACK WRONG\nFROM: pilot-agent'});
  assert.equal(await applyAction(h.args),'WAITING');
  h.comments.push({body:'ACK ACTION-1\nFROM: pilot-agent\nActual result',
    html_url:'https://github.com/'+repo+'/issues/110#issuecomment-101',created_at:'2026-10-19T17:31:00Z'});
  assert.equal(await applyAction(h.args),'SAVED');
  const reply=parse(h.saved).moves.at(-1);assert.equal(reply.answers,'ACTION-1');
  assert.match(reply.replyText,/Actual result/);assert.match(reply.evidence,/#issuecomment-101$/);
});
test('NN110 action: duplicate or oversized envelopes cannot be accepted as one request',()=>{
  const body=encode(request(thread()));assert.throws(()=>unpackAction(body+'\n'+body),/one action packet/);
  assert.throws(()=>unpackAction('x'.repeat(100001)),/Invalid action body/);
});
test('NN110 action: legacy snapshot sweeps cannot close queued thread actions',async()=>{
  const candidate={number:5,state:'open',user:{login:'reallakshman19'},labels:[{name:'nextnudge-save'}],body:encode(request(thread()))};
  let mutations=0;
  const count=await sweepUnreceipted({owner:'reallakshman19',currentIssueNumber:10,
    listOpenIssues:async page=>page===1?[candidate]:[],listComments:async()=>[],
    commentIssue:async()=>{mutations++;},closeIssue:async()=>{mutations++;}});
  assert.equal(count,0);assert.equal(mutations,0);
});
