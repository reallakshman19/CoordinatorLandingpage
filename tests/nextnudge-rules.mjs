import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import * as m from '../site/nextnudge/model.mjs';
import {validate,validateProfiles} from '../site/nextnudge/schema.mjs';
import {esc} from '../site/nextnudge/util.mjs';
const profiles=JSON.parse(await readFile(new URL('../site/nextnudge/profiles.json',import.meta.url)));
function setup() {
  const db={formatVersion:2,revision:0,profiles:structuredClone(profiles),projects:[],runs:[],events:[]};
  const p=m.newProject(db,'Real task'),r=m.newRun(db,p.id,'Custom run','Preserve the Owner aim');
  return {db,p,r,n:r.nodes[0]};
}
test('custom ladders have no future locks; labels and counts vary',()=>{
  const {db,r}=setup();
  for(let i=0;i<8;i++)m.newStep(db,r,'Midcycle '+i,'Reconcile against fixtures');
  assert.equal(r.nodes.length,10);assert(r.nodes.every(n=>n.status==='ready'));
  m.removeStep(db,r,r.nodes.at(-1));assert.equal(r.nodes.filter(n=>!n.deleted).length,9);
  m.reply(db,r,r.nodes[7],{by:'Agent',text:'Starting midcycle now'});
  assert.equal(r.nodes[7].status,'submitted');validate(db);
});
test('copy is not send; sent instructions and destination are frozen',()=>{
  const {db,r,n}=setup();r.chatId8='1234abcd';
  m.copied(db,r,n,m.packet(r,n));assert.equal(n.sentAt,null);
  m.markSent(db,r,n);const sent=n.sentText;
  assert.equal(n.status,'sent');assert.equal(n.sentChatId8,'1234abcd');
  assert.throws(()=>m.markSent(db,r,n));
  assert.throws(()=>m.editStep(db,r,n,{label:'changed',instruction:'changed',type:'next_step'}));
  r.aim='Later amended aim';assert.equal(m.packet(r,n),sent);validate(db);
});
test('editing after copy requires a new copy',()=>{
  const {db,r,n}=setup();r.chatId8='1234abcd';m.copied(db,r,n,m.packet(r,n));
  m.editStep(db,r,n,{label:'New label',instruction:'New instruction',type:'next_step'});
  assert.throws(()=>m.markSent(db,r,n));
});
test('manual replies retain exact text and separate clocks; wrong ACK fails',()=>{
  const {db,r,n}=setup();const exact=`ACK ${n.id}\n  exact agent text  `;
  m.reply(db,r,n,{by:'Agent',text:exact,repliedAt:'2026-10-18T08:00:00Z'});
  assert.equal(n.messages[0].text,exact);assert.equal(n.messages[0].relayed,true);
  assert.equal(n.messages[0].repliedAt,'2026-10-18T08:00:00.000Z');
  assert.notEqual(n.messages[0].at,n.messages[0].repliedAt);
  assert.throws(()=>m.reply(db,r,n,{by:'Agent',text:'ACK NN-20261018-010101-dead wrong step'}));
  m.reply(db,r,n,{by:'Agent',text:'No source timestamp available'});
  assert.equal(n.messages.at(-1).repliedAt,null);validate(db);
});
test('nested correction requires parent re-review and never auto-accepts',()=>{
  const {db,r,n}=setup();m.reply(db,r,n,{by:'Agent',text:'Result needs work'});
  const c=m.correction(db,r,n,'Fix','Correct the result');
  const sub=m.correction(db,r,c,'Prerequisite','Resolve missing input');
  assert.throws(()=>m.accept(db,r,n,'Cannot bypass child'));
  m.reply(db,r,sub,{by:'Agent',text:'Input resolved'});m.accept(db,r,sub,'Reviewed with gaps');
  assert.equal(c.status,'ready');assert.throws(()=>m.accept(db,r,c,'No result yet'));
  m.reply(db,r,c,{by:'Agent',text:'Corrected'});m.accept(db,r,c,'Reviewed with gaps');
  assert.equal(n.status,'submitted');m.accept(db,r,n,'Parent rechecked with gaps');
  assert.equal(n.status,'accepted');validate(db);
});
test('evidence optional but checklist gaps require an explicit note',()=>{
  const {db,r,n}=setup();m.reply(db,r,n,{by:'Agent',text:'Done'});
  assert.throws(()=>m.accept(db,r,n));
  n.checks['Coding:ci']='Needs correction';assert.throws(()=>m.accept(db,r,n,'A note cannot waive a correction'));
  n.checks['Coding:ci']='Proceed with gap';m.accept(db,r,n,'CI not available; retain gap');
  assert(db.events.at(-1).data.gaps.length);validate(db);
});
test('fixtures transfer preserves provenance, is idempotent and append-only where required',()=>{
  const {db,p,r}=setup();m.fixture(db,r,'1e',{text:'Original intent',url:'',status:'RECORDED'});
  assert.throws(()=>m.fixture(db,r,'1e',{text:'overwrite',url:''},r.fixtures['1e'][0].id));
  m.fixture(db,r,'1d',{text:'Roadmap',url:'',status:'RECORDED'});
  assert.throws(()=>m.fixture(db,r,'1d',{text:'change',url:''},r.fixtures['1d'][0].id));
  const next=m.newRun(db,p.id,'Successor','Recover intent');
  assert.equal(m.pull(db,next,'1e',r.id),1);assert.equal(m.pull(db,next,'1e',r.id),0);
  assert.equal(next.fixtures['1e'][0].source.run,r.id);
  assert.equal(next.fixtures['1e'][0].status,'NEEDS_REVIEW');
  m.removeFixture(db,next,'1e',next.fixtures['1e'][0].id);
  assert(next.fixtures['1e'][0].deleted);validate(db);
});
test('history is append-only across replies, revisions and lifecycle',()=>{
  const {db,r,n}=setup();const prefix=JSON.stringify(db.events);
  m.reply(db,r,n,{by:'Agent',text:'Result'});m.lifecycle(db,r,'pause');
  assert.throws(()=>m.reply(db,r,n,{by:'Agent',text:'Should stop'}));
  m.lifecycle(db,r,'pause');m.lifecycle(db,r,'archive');m.lifecycle(db,r,'delete');
  assert.equal(JSON.stringify(db.events.slice(0,JSON.parse(prefix).length)),prefix);validate(db);
});
test('restore rejects injected IDs, cycles, unsafe URLs and invalid profiles',()=>{
  const {db,r,n}=setup();validate(db);
  for(const field of ['project','run','step']) {
    const copy=structuredClone(db);
    (field==='project'?copy.projects[0]:field==='run'?copy.runs[0]:copy.runs[0].nodes[0]).id='x" onmouseover="alert(1)';
    assert.throws(()=>validate(copy));
  }
  n.parent=n.id;assert.throws(()=>validate(db));n.parent=null;
  assert.throws(()=>m.reply(db,r,n,{by:'Agent',text:'x',proof:'javascript:alert(1)'}));
  assert.throws(()=>validate(JSON.parse('{"formatVersion":2,"__proto__":{"polluted":true}}')));
  assert.throws(()=>validateProfiles({formatVersion:1,profiles:{'<img>':[]}}));
  assert.equal(esc('<img onerror="x">'),'&lt;img onerror=&quot;x&quot;&gt;');
});
test('profile JSON supports additional task types without fixed template names',()=>{
  const {db,r,n}=setup();db.profiles.profiles.Research=[{id:'sources',question:'Source grounded?',example:'Read original',evidence:'Link'}];
  r.profiles=['Research'];validate(db);assert.equal(m.checklist(db,r)[0].key,'Research:sources');
});
