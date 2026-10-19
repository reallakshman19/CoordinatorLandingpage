import test from 'node:test';
import assert from 'node:assert/strict';
import {newThread,serialize,parse,validate,activeAgent,currentState} from '../site/nextnudge/revamp/thread.mjs';
import {makeReply,replyAcks,replyWarnings,replyLabel,moveRole,moveAgent,
  openMoves,openAgents} from '../site/nextnudge/revamp/reply.mjs';
import {sentMove,sentForm} from '../site/nextnudge/revamp/editor.mjs';
import {gzipSync} from 'node:zlib';
import {applyIssue} from '../scripts/nextnudge_thread_apply.mjs';

const ID='NN-20261019-010101-aa01';
const thread=()=>newThread({id:ID,title:'Pilot',goal:'Owner outcome',agent:'Judge A',
  inScope:'Read-only',outScope:'No edits',doneWhen:['Evidence reviewed']});
const move=(id,agent,role)=>({id,kind:'task',delivery:'sent',packet:'Task '+id,
  returnLine:'',digest:'',evidence:'',gap:'',decision:'',archive:'',note:'',
  ...(agent?{agent}:{}),...(role?{role}:{})});

test('R3 G1: matching reply ACK creates answers, unrecognized ACK is retained and warns',()=>{
  const x=thread();x.moves.push(move('TASK-1'));
  const yes=makeReply(x,'ACK TASK-1\nResults done',{id:'REPLY-1'});
  assert.equal(yes.move.answers,'TASK-1');assert.deepEqual(yes.warnings,[]);
  const no=makeReply(x,'ACK UNKNOWN-1\nIndependent result',{id:'REPLY-2'});
  assert.equal(no.move.answers,undefined);
  assert.ok(no.warnings.includes('ACK tag not found'));
  x.moves.push(no.move,yes.move);
  const y=parse(serialize(x));
  assert.equal(y.moves.at(-1).answers,'TASK-1');
  assert.equal(openMoves(y).length,0);
});
test('R3 G2: blank reconciled task needs note; filled and compose-task remain valid',()=>{
  const x=thread(),draft={id:'TASK-1',kind:'task',requiresTask:true};
  const blank='Intent: Owner outcome\nOne bounded task:\n\nAuthoritative inputs: pointer';
  assert.throws(()=>sentMove(x,draft,blank),/blank/);
  const allowed=sentMove(x,draft,blank,{override_note:'Owner approved exact designer packet'});
  assert.equal(allowed.override_note,'Owner approved exact designer packet');
  assert.equal(parse(serialize({...x,moves:[allowed]})).moves[0].override_note,allowed.override_note);
  const filled=blank.replace('One bounded task:\n\n','One bounded task:\nDo one bounded verification.\n');
  assert.equal(sentMove(x,draft,filled).override_note,undefined);
  assert.equal(sentMove(x,{id:'TASK-2',kind:'task',requiresTask:false},
    'Designed compose task without an empty task slot').id,'TASK-2');
  assert.match(sentForm('Judge A'),/name="override_note"/);
});
test('R3 G3: first nonempty line multiple case-sensitive ACK tags and BOM',()=>{
  assert.deepEqual(replyAcks('\n\nACK TASK-1 and ACK JUDGE-2\nACK LATE-3'),
    {primary:'TASK-1',also:['JUDGE-2']});
  assert.deepEqual(replyAcks('\uFEFFACK TASK-1 and ACK JUDGE-2'),
    {primary:'TASK-1',also:['JUDGE-2']});
  assert.deepEqual(replyAcks('ACK TASK-1'),{primary:'TASK-1',also:[]});
  assert.deepEqual(replyAcks('ack TASK-1'),{primary:'',also:[]});
  assert.deepEqual(replyAcks('BLACK TASK-1'),{primary:'',also:[]});
  const x=thread();x.moves.push(move('TASK-1'));
  const r=makeReply(x,'\uFEFFACK TASK-1 and ACK JUDGE-2\nEvidence',{id:'REPLY-1'});
  assert.equal(r.move.answers,'TASK-1');
  assert.deepEqual(r.move.also_acks,['JUDGE-2']);
});
test('R3 G4: byte-identical raw reply incl BOM; warnings only for actual anomalies',()=>{
  const x=thread();x.moves.push(move('TASK-1'));
  const raw='\uFEFFACK TASK-1\nÃ mismatch â€ evidence\nSame result\nSame result\n';
  const r=makeReply(x,raw,{id:'REPLY-1'});
  assert.equal(r.move.replyText,raw);
  assert.deepEqual(r.warnings,[
    'Leading BOM in reply','Possible garbled text encoding','Duplicate non-empty lines']);
  const y=parse(serialize({...x,moves:[...x.moves,r.move]}));
  assert.equal(Buffer.compare(Buffer.from(y.moves.at(-1).replyText),Buffer.from(raw)),0);
  assert.equal(y.moves.at(-1).returnLine,'\uFEFFACK TASK-1');
  assert.deepEqual(replyWarnings('ACK TASK-1\nClean result'),[]);
  assert.throws(()=>makeReply(x,'x'.repeat(90001)),/Invalid reply text/);
});
test('R3 G6: simultaneous generator and judge, roles/agents, old worker and unchanged active agent',()=>{
  const x=thread();x.moves.push(move('GENERATE-1','Generator B','generator'));
  x.moves.push(move('JUDGE-1','Judge A','judge'));
  assert.deepEqual(openAgents(x),['Generator B','Judge A']);
  assert.equal(moveRole(x.moves[0]),'generator');
  assert.equal(moveRole(move('OLD-1')),'worker');
  assert.equal(moveAgent(x,move('OLD-1')),'Judge A');
  assert.equal(activeAgent(x),'Judge A');
  assert.equal(currentState(x),'Waiting on agent');
  x.moves.push(makeReply(x,'ACK GENERATE-1',{id:'REPLY-1'}).move);
  assert.deepEqual(openAgents(x),['Judge A']);
  x.moves.push(makeReply(x,'ACK JUDGE-1',{id:'REPLY-2'}).move);
  assert.deepEqual(openAgents(x),['Judge A']);
  assert.match(sentForm('Judge A'),/generator/);
  assert.match(sentForm('Judge A'),/name="agent"/);
  assert.deepEqual(parse(serialize(x)).moves[0].role,'generator');
});
test('R3 G8: label defaults UNKNOWN, round-trips, and rejects invalid labels',()=>{
  const x=thread();x.moves.push(move('TASK-1'));
  const old={...makeReply(x,'ACK TASK-1',{id:'OLD-R'}).move};
  delete old.label;assert.equal(replyLabel(old),'UNKNOWN');
  for(const label of ['UNKNOWN','INDEPENDENT','SELF-ASSESSED','NOT BLIND']){
    const m=makeReply(x,'ACK TASK-1',{id:'REPLY-'+label.replace(/ /g,'-'),label}).move;
    assert.equal(m.label,label);
    assert.equal(parse(serialize({...x,moves:[...x.moves,m]})).moves.at(-1).label,label);
  }
  assert.throws(()=>makeReply(x,'ACK TASK-1',{label:''}),/assessment label/);
  assert.doesNotThrow(()=>validate({...x,moves:[...x.moves,old]}));
});
test('R3 schema: old 14-move thread remains readable; new fields reach SHA-guarded issue writer',async()=>{
  const x=thread();
  for(let i=0;i<13;i++)x.moves.push(move('LEGACY-'+i));
  x.moves.push(makeReply(x,'ACK LEGACY-11',{id:'REPLY-14',label:'INDEPENDENT'}).move);
  assert.equal(parse(serialize(x)).moves.length,14);
  const {moves,...header}=x,delta={v:3,id:ID,baseSha:null,expectedCount:0,header,moves};
  const tick=String.fromCharCode(96).repeat(3);
  const body=tick+'nextnudge-thread-save\n'+gzipSync(JSON.stringify(delta)).toString('base64')+'\n'+tick;
  const issue={user:{login:'reallakshman19'},state:'open',labels:[{name:'nextnudge-save'}],body};
  let text='',receipt='';
  const args={issue,owner:'reallakshman19',read:async()=>null,
    write:async(_path,raw)=>{text=raw;},comment:async msg=>{receipt=msg;},close:async()=>{}};
  assert.equal(await applyIssue(args),'SAVED');assert.match(receipt,/SAVED/);
  assert.equal(parse(text).moves.at(-1).answers,'LEGACY-11');
  const changed={...args,read:async()=>({sha:'f'.repeat(40),content:text})};
  assert.equal(await applyIssue(changed),'NEEDS RELOAD');
});
