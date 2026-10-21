import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import * as m from '../site/nextnudge/model.mjs';
import {action,downloadText} from '../site/nextnudge/actions.mjs';
import {migrate} from '../site/nextnudge/migrate.mjs';
import {validate} from '../site/nextnudge/schema.mjs';
import {workbench} from '../site/nextnudge/workspace.mjs';
import {prepare} from '../site/nextnudge/prepare.mjs';
const profiles=JSON.parse(fs.readFileSync(new URL('../site/nextnudge/profiles.json',import.meta.url)));
function setup() {
  const db={formatVersion:2,revision:0,profiles:structuredClone(profiles),projects:[],runs:[],events:[]};
  const project=m.newProject(db,'NLM pilot'),r=m.newRun(db,project.id,'NLM validator','Grade 9 review');
  return {db,r,p1:r.nodes[0],p2:r.nodes[1]};
}
function acceptance() {
  const {db,r,p1}=setup();
  const p3=m.newStep(db,r,'P3','Confirm 39 tiles');
  m.reply(db,r,p3,{by:'Agent',text:'SAVED-P3 · rows=39 · FULFILLED=39'});
  r.selected=p3.id;
  const s={db,tab:'work',conflict:false};
  let saved=0,rendered=0;
  return {db,r,p1,p3,s,ctx:{s,run:r,node:p3,save:()=>saved++,render:()=>rendered++},
    counts:()=>({saved,rendered})};
}
test('W9 accept targets the selected P3 and cannot alter P1 or another data-id',async()=>{
  const x=acceptance();
  await assert.rejects(()=>action('accept-step',{dataset:{id:x.p1.id}},x.ctx),/selection changed/i);
  assert.equal(x.p1.status,'ready');
  assert.equal(x.p3.status,'submitted');
  x.r.drafts[x.p3.id]={reviewNote:'Independent review: 39/39 checks'};
  await action('accept-step',{dataset:{id:x.p3.id}},x.ctx);
  assert.equal(x.p3.status,'accepted');
  assert.equal(x.p1.status,'ready');
});
test('W9 accept saves the dedicated Instructor note, not a reply draft',async()=>{
  const x=acceptance();
  x.r.drafts[x.p3.id]={text:'Unsaved agent message',reviewNote:'Instructor checked all 39 rows'};
  await action('accept-step',{dataset:{id:x.p3.id}},x.ctx);
  assert.equal(x.p3.acceptance.note,'Instructor checked all 39 rows');
  assert.equal(x.db.events.at(-1).state,'ACCEPTED');
  assert.equal(x.db.events.at(-1).note,'Instructor checked all 39 rows');
  assert.equal(x.r.drafts[x.p3.id].text,'Unsaved agent message');
  assert.equal(x.r.drafts[x.p3.id].reviewNote,'');
  validate(x.db);
});
test('W9 accept stays on same P3 and same Workbench tab',async()=>{
  const x=acceptance();
  x.r.drafts[x.p3.id]={reviewNote:'Checked'};
  await action('accept-step',{dataset:{id:x.p3.id}},x.ctx);
  assert.equal(x.r.selected,x.p3.id);
  assert.equal(x.s.tab,'work');
  assert.deepEqual(x.counts(),{saved:1,rendered:1});
  assert.match(workbench(x.db,x.r,x.p3),/Acceptance note for selected step/);
});
test('W10/W6 replies record typed source and return-file path, size, SHA-256',()=>{
  const {db,r,p1}=setup(),sha='a'.repeat(64);
  m.reply(db,r,p1,{by:'Agent',text:'SAVED-P1 · rows=39',
    source:'return_file',returnPath:'reports/p1.md',returnBytes:'4089',returnSha256:sha});
  assert.equal(p1.messages[0].source,'return_file');
  assert.deepEqual(p1.messages[0].returnFile,{path:'reports/p1.md',bytes:4089,sha256:sha});
  assert.throws(()=>m.reply(db,r,p1,{by:'Agent',text:'x',source:'return_file',
    returnPath:'a.md',returnBytes:'',returnSha256:sha}),/requires path/);
  m.reply(db,r,p1,{by:'Owner',text:'Partial capture',source:'relayed_summary'});
  assert.equal(p1.messages[1].source,'relayed_summary');
  m.reply(db,r,p1,{by:'Owner',text:'Exact chat words'});
  assert.equal(p1.messages[2].source,'chat_words');
  validate(db);
});
test('W7 SHA-256 matches exact packet bytes and Mark sent retains it',async()=>{
  const {db,r,p1}=setup();
  r.chatId8='deadbeef';r.selected=p1.id;
  const exact=m.packet(r,p1),sha=await m.fingerprintText(exact);
  assert.equal(sha,await m.packetSha256(r,p1));
  m.copied(db,r,p1,exact,sha);
  m.markSent(db,r,p1);
  assert.equal(p1.sentPacketSha256,sha);
  assert.match(workbench(db,r,p1),/Packet SHA-256:/);
  validate(db);
});
test('W8 session change preserves before/after and reason as run event',()=>{
  const {db,r}=setup();r.chatId8='deadbeef';
  m.sessionChanged(db,r,'4d2f61e6','chat unreadable');
  assert.equal(r.chatId8,'4d2f61e6');
  const e=db.events.at(-1);
  assert.equal(e.state,'AGENT_SESSION_CHANGED');
  assert.deepEqual(e.data,{from:'deadbeef',to:'4d2f61e6'});
  assert.equal(e.note,'chat unreadable');
  assert.throws(()=>m.sessionChanged(db,r,'4d2f61e6','again'),/differ/);
  assert.match(prepare(db,r,r.nodes[0]),/session-change-form/);
  validate(db);
});
test('W11 independent verification records actor, recomputation, MATCH/MISMATCH and note',()=>{
  const {db,r,p1}=setup();m.reply(db,r,p1,{by:'Agent',text:'39 rows'});
  m.verifyReply(db,r,p1,0,{checkedBy:'OTM',recomputed:'39 row count',result:'MATCH',note:'Oracle agrees'});
  assert.equal(p1.messages[0].verification.checkedBy,'OTM');
  assert.equal(p1.messages[0].verification.result,'MATCH');
  assert.equal(db.events.at(-1).state,'REPLY_VERIFIED');
  m.verifyReply(db,r,p1,0,{checkedBy:'Reviewer B',recomputed:'source hash',result:'MISMATCH',note:'Different hash'});
  assert.equal(p1.messages[0].verification.result,'MISMATCH');
  assert.match(workbench(db,r,p1),/Record independent check/);
  validate(db);
});
test('W5 fixed SAVED-P3 line extracts key=value pairs without corrupting original reply',()=>{
  const {db,r,p1}=setup(),raw='SAVED-P3 · rows=39 · FULFILLED=39 · file=nlm.md';
  m.reply(db,r,p1,{by:'Agent',text:raw});
  assert.equal(p1.messages[0].text,raw);
  assert.deepEqual(p1.messages[0].savedLine,{tag:'SAVED-P3',
    fields:{rows:'39',FULFILLED:'39',file:'nlm.md'}});
  assert.equal(m.parseSavedLine('Nothing saved'),null);
  assert.throws(()=>m.parseSavedLine('SAVED-P3 rows=39 rows=40'),/Duplicate/);
  validate(db);
});
test('W2 configured sender appears in packet header and old saves default to Owner',()=>{
  const {db,r,p1}=setup();
  assert.match(m.packet(r,p1),/^\[Owner · NextNudge/);
  r.sentBy='TeamCoordinator';
  assert.match(m.packet(r,p1),/^\[TeamCoordinator · NextNudge/);
  assert.match(prepare(db,r,p1),/name="sentBy"/);
  validate(db);
  delete r.sentBy;
  assert.match(m.packet(r,p1),/^\[Owner · NextNudge/);
  validate(db);
});
test('W12 packet file export is byte-identical and named with step ID',async()=>{
  const {db,r,p1}=setup();r.selected=p1.id;
  const exact=m.packet(r,p1);
  const originalURL=globalThis.URL.createObjectURL,originalDocument=globalThis.document;
  let bytes,filename;
  globalThis.URL.createObjectURL=blob=>{bytes=blob;return 'blob:test';};
  globalThis.document={createElement:()=>({
    set href(x){this.url=x;},set download(x){filename=x;},click(){}
  })};
  try {
    await action('packet-file',{dataset:{id:p1.id}},
      {s:{db,conflict:false},run:r,node:p1,save:()=>{},render:()=>{}});
    assert.equal(filename,p1.id+'.md');
    assert.equal(await bytes.text(),exact);
    assert.equal(await m.fingerprintText(await bytes.text()),await m.packetSha256(r,p1));
  } finally {
    globalThis.URL.createObjectURL=originalURL;globalThis.document=originalDocument;
  }
});
test('W13 waiting-on timer flags quiet Sent after 30 min and clears on reply',()=>{
  const {db,r,p1}=setup();
  const anchor=Date.parse('2026-10-19T00:00:00Z');
  p1.status='sent';p1.sentAt=new Date(anchor).toISOString();
  assert.equal(m.waitingOn(r,anchor+30*60000)[0].quiet,false);
  assert.equal(m.waitingOn(r,anchor+31*60000)[0].quiet,true);
  assert.equal(m.waitingOn(r,anchor+31*60000)[0].elapsedMinutes,31);
  m.reply(db,r,p1,{by:'Agent',text:'Here is the result'});
  assert.deepEqual(m.waitingOn(r,anchor+31*60000),[]);
});
test('W14 status history has previous/new state, actor, time; reversion requires reason',()=>{
  const {db,r,p1}=setup();r.sentBy='TeamCoordinator';
  m.reply(db,r,p1,{by:'Agent',text:'Done'});
  let e=db.events.filter(x=>x.state==='STATUS_CHANGED').at(-1);
  assert.equal(e.data.from,'ready');assert.equal(e.data.to,'submitted');
  assert.equal(e.by,'TeamCoordinator');assert(Number.isFinite(Date.parse(e.at)));
  m.accept(db,r,p1,'Reviewed with gaps');
  assert.equal(p1.status,'accepted');
  assert.throws(()=>m.revertStatus(db,r,p1,''),/reason/);
  m.revertStatus(db,r,p1,'Acceptance accidental');
  assert.equal(p1.status,'submitted');
  assert.equal(db.events.at(-1).state,'STATUS_REVERTED');
  assert.equal(db.events.at(-1).note,'Acceptance accidental');
  assert.throws(()=>m.revertStatus(db,r,p1,'twice'),/No unreverted/);
  validate(db);
});
test('W15 run JSON contains statuses, exact packet/reply SHA-256 and waiting list',async()=>{
  const {db,r,p1}=setup();
  r.chatId8='deadbeef';const msg='SAVED-P1 · rows=39';
  const raw=m.packet(r,p1),sha=await m.fingerprintText(raw);
  m.copied(db,r,p1,raw,sha);m.markSent(db,r,p1);
  m.reply(db,r,p1,{by:'Agent',text:msg});
  const other=r.nodes[1];
  other.status='sent';other.sentAt='2026-10-19T00:00:00.000Z';
  const summary=await m.runSummary(db,r,Date.parse('2026-10-19T01:00:00Z'));
  assert.equal(summary.runId,r.id);
  assert.equal(summary.steps[0].packetSha256,sha);
  assert.deepEqual(summary.steps[0].replySha256s,[await m.fingerprintText(msg)]);
  assert.equal(summary.waitingOn[0].id,other.id);
  assert(!JSON.stringify(summary).includes('https://private-chat'));
});
test('backward compatibility: old version-2 source loads without field injection or data loss',()=>{
  const old=JSON.parse(fs.readFileSync(new URL('fixtures/nextnudge-issue97-pilot.json',import.meta.url)));
  const before=JSON.stringify(old);
  assert.equal(migrate(old,profiles),old);
  assert.equal(JSON.stringify(old),before);
  assert.equal(validate(old),old);
  for(const run of old.runs) {
    assert.equal(run.sentBy,undefined);
    assert.equal(run.sentBy||'Owner','Owner');
    for(const node of run.nodes)for(const message of node.messages)
      assert.equal(message.source||'chat_words','chat_words');
  }
});
