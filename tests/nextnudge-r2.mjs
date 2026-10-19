import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {gzipSync} from 'node:zlib';
import {applyIssue} from '../scripts/nextnudge_thread_apply.mjs';
import {newThread,parse,serialize,currentState,activeIntent,activeAgent,
  reconcile,validate} from '../site/nextnudge/revamp/thread.mjs';
import {ackTag,boundedTaskFilled,sentMove,amendValues,agentChange,
  ownerForm,agentForm,sentForm} from '../site/nextnudge/revamp/editor.mjs';

const ID='NN-20261019-111111-aaaa',M='NN-20261019-111112-bbbb';
const make=()=>newThread({id:ID,title:'NLM live pilot',agent:'First agent',goal:'Owner outcome',
  doneWhen:['Original check'],inScope:'Audit only',outScope:'No edits'});
const move=(id=M,kind='task',delivery='sent')=>({id,kind,delivery,
  packet:delivery==='sent'?'Packet': '',returnLine:'',digest:'',
  evidence:'',gap:'',decision:'',archive:'',note:''});
const draft={id:M,kind:'task',packet:'',gap:'',requiresTask:false};

test('R2 G1: ACK tag from pasted packet becomes the move id, exact packet survives',()=>{
  const x=make(),p='Designed prompt\nStart your reply with ACK NLM-P3.\nEnd';
  assert.equal(ackTag(p),'NLM-P3');
  assert.equal(ackTag('- Start your reply with ACK NLM-P4.'),'NLM-P4');
  assert.equal(ackTag('Reply with ACK NLM-P5'),'NLM-P5');
  assert.equal(ackTag('ACK NLM-P6'),'NLM-P6');
  const m=sentMove(x,draft,p);assert.equal(m.id,'NLM-P3');
  x.moves.push(m);
  const y=parse(serialize(x));
  assert.equal(y.moves[0].id,'NLM-P3');assert.equal(y.moves[0].packet,p);
  assert.throws(()=>sentMove(x,{...draft,id:'NN-20261019-111113-abcd'},p),/Duplicate ACK tag/);
  assert.equal(ackTag('No ACK line here'),null);
  assert.equal(sentMove(x,{...draft,id:'NN-20261019-111114-cdef'},'Different text').id,
    'NN-20261019-111114-cdef');
  assert.throws(()=>ackTag('ACK A-1\nACK B-2'),/Conflicting ACK tags/);
});
test('R2 G2: every decision shows intent once, explicit gap and blank task, then accepts a filled task',()=>{
  const x=make(),gap='Observed source mismatch, not a new instruction';
  const decisions=['continue','correct','request evidence','change direction','close'];
  for(const decision of decisions){
    const r=reconcile({nudgeId:M,goal:x.goal,agent:'First agent',decision,gap,
      reply:'ACK P2',criteria:x.doneWhen,
      checks:[decision==='close'?'met':decision==='correct'?'not met':'unknown']});
    assert.equal(r.packet.split(x.goal).length-1,1,decision);
    assert.match(r.packet,/Observed gap:\nObserved source mismatch/);
    assert.match(r.packet,/One bounded task:\n\nAuthoritative inputs:/);
    assert.equal(boundedTaskFilled(r.packet),false);
    assert.throws(()=>sentMove(x,{id:M,kind:r.kind,gap:r.gap,
      requiresTask:true,closure:r.closure},r.packet),/One bounded task is blank/);
    const edited=r.packet.replace('One bounded task:\n\n',
      'One bounded task:\nCompare actual repo evidence with the reply.\n');
    assert.equal(boundedTaskFilled(edited),true);
    const m=sentMove(x,{id:M,kind:r.kind,gap:r.gap,requiresTask:true,
      closure:r.closure},edited);
    assert.equal(m.gap,gap);
    assert.equal(m.packet,edited);
  }
});
test('R2 G3: exact user gap is persisted verbatim; check assessment remains separate',()=>{
  const gap='  Actual gap: A2 vs A3\nNext evidence required, no prefix.  ';
  const x=make();
  const r=reconcile({nudgeId:M,goal:x.goal,checks:['not met'],criteria:x.doneWhen,
    decision:'change direction',gap});
  assert.equal(r.gap,gap);
  assert.match(r.packet,/Observed gap:\n  Actual gap:/);
  const edited=r.packet.replace('One bounded task:\n\n','One bounded task:\nVerify the A2 file.\n');
  x.moves.push(sentMove(x,{...draft,kind:r.kind,gap:r.gap,requiresTask:true},edited));
  assert.equal(parse(serialize(x)).moves[0].gap,gap);
  assert.doesNotMatch(parse(serialize(x)).moves[0].gap,/Propose revised direction/);
});
test('R2 G4: agent changes and free notes do not change Waiting on agent',()=>{
  const x=make();x.moves.push(move());
  assert.equal(currentState(x),'Waiting on agent');
  const a=agentChange('Second agent','NN-20261019-111113-cccc');
  x.moves.push(a);
  assert.equal(activeAgent(x),'Second agent');
  assert.equal(currentState(x),'Waiting on agent');
  x.moves.push({...move('NN-20261019-111114-dddd','amendment','draft'),
    note:'2026-10-19: Agent is working'});
  assert.equal(currentState(x),'Waiting on agent');
  assert.equal(parse(serialize(x)).moves.at(-2).kind,'agent');
  assert.equal(activeAgent(parse(serialize(x))),'Second agent');
  x.moves.push({...move('NN-20261019-111115-eeee','reply','draft'),returnLine:'ACK task done'});
  assert.equal(currentState(x),'Your move');
  const app=fs.readFileSync(new URL('../site/nextnudge/revamp/app.mjs',import.meta.url),'utf8');
  assert.match(app,/chatLink\(t\(\)\.id,''\)/);
  assert.match(agentForm('First agent'),/id="agent-change"/);
  assert.throws(()=>agentChange('  '),/valid new agent/);
});
test('R2 G5: editable Scope and Out are stored as append-only Owner amendment',()=>{
  const x=make(),oldScope=x.inScope,oldOut=x.outScope;
  const next=amendValues({goal:x.goal,checks:'Original check',inScope:'Two audited modules',
    outScope:'No deployments',hold:''});
  x.moves.push({...move(M,'amendment','draft'),
    note:'OWNER_INTENT_CHANGE:'+JSON.stringify(next)});
  const y=parse(serialize(x));
  assert.equal(activeIntent(y).inScope,'Two audited modules');
  assert.equal(activeIntent(y).outScope,'No deployments');
  assert.equal(y.inScope,oldScope);assert.equal(y.outScope,oldOut);
  assert.match(ownerForm(activeIntent(y)),/name="inScope"/);
  assert.match(ownerForm(activeIntent(y)),/name="outScope"/);
  assert.equal(activeIntent(make()).inScope,'Audit only');
});
test('R2 G6: five multiline done-when checks round-trip; sixth refused and forms confirm inline',()=>{
  const x=make(),checks=['Read input','Compare weight','Review units','Verify browser','Owner evidence'];
  const next=amendValues({goal:'Revised goal',checks:checks.join('\n'),
    inScope:'Inputs',outScope:'New features',hold:'HOLD only on release'});
  assert.deepEqual(next.doneWhen,checks);
  const html=ownerForm(next);
  assert.ok(html.includes(checks.join('\n')),'Textarea contains actual newlines');
  assert.match(html,/name="approved" required/);
  assert.match(html,/type="submit">Save amendment/);
  assert.match(sentForm(),/name="approved" required/);
  assert.match(sentForm(),/Save sent packet/);
  x.moves.push({...move(M,'amendment','draft'),
    note:'OWNER_INTENT_CHANGE:'+JSON.stringify(next)});
  assert.deepEqual(activeIntent(parse(serialize(x))).doneWhen,checks);
  assert.throws(()=>amendValues({...next,checks:[...checks,'Sixth'].join('\n')}),/At most five/);
  const app=fs.readFileSync(new URL('../site/nextnudge/revamp/app.mjs',import.meta.url),'utf8');
  assert.doesNotMatch(app,/prompt\('Owner goal'|confirm\('Confirm you manually sent/);
  assert.match(app,/form.id==='owner-amend'/);
  assert.match(app,/form.id==='sent-confirm'/);
  assert.match(app,/values.get\('approved'\)/);
});
test('R2 G5+G6: real owner-only GitHub issue save retains scope/out and five newline criteria',async()=>{
  const x=make(),criteria=['One','Two','Three','Four','Five'];
  const next=amendValues({goal:'Amended intent',checks:criteria.join('\n'),
    inScope:'Updated in scope',outScope:'Updated out of scope',hold:''});
  x.moves.push({...move(M,'amendment','draft'),
    note:'OWNER_INTENT_CHANGE:'+JSON.stringify(next)});
  const {moves,...header}=x;
  const payload={v:3,id:ID,baseSha:null,expectedCount:0,header,moves};
  const tick=String.fromCharCode(96).repeat(3);
  const body='Approved save\n'+tick+'nextnudge-thread-save\n'+
    gzipSync(JSON.stringify(payload)).toString('base64')+'\n'+tick;
  let saved='',receipt='';
  const issue={user:{login:'reallakshman19'},state:'open',
    labels:[{name:'nextnudge-save'}],body};
  const status=await applyIssue({issue,owner:'reallakshman19',read:async()=>null,
    write:async(_,text)=>{saved=text;},comment:async s=>{receipt=s;},close:async()=>{}});
  assert.equal(status,'SAVED');assert.match(receipt,/SAVED:/);
  const y=parse(saved),intent=activeIntent(y);
  assert.deepEqual(intent.doneWhen,criteria);
  assert.equal(intent.inScope,'Updated in scope');
  assert.equal(intent.outScope,'Updated out of scope');
  assert.equal(y.inScope,'Audit only','original frozen thread header stays unchanged');
});
test('R2 preserves original seed, byte exactness, and existing browser model schema',()=>{
  const md=fs.readFileSync(new URL('../site/nextnudge-data/threads/NN-20261018-171656-66d2.md',import.meta.url),'utf8');
  const old=parse(md);assert.equal(serialize(old),md);assert.equal(validate(old),old);
  const x=make();x.moves.push(move());
  assert.equal(parse(serialize(x)).moves[0].packet,'Packet');
});
