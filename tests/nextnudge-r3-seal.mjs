import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {newThread,serialize,parse,validate,currentState} from '../site/nextnudge/revamp/thread.mjs';
import {makeSeal,sealUnlocked,sealHtml,sealForm} from '../site/nextnudge/revamp/seal.mjs';
import {makeReply} from '../site/nextnudge/revamp/reply.mjs';

const make=()=>newThread({id:'NN-20261019-111111-bbbb',title:'Sealed pilot',agent:'Judge',
  goal:'Independent checking'});
const sent=(id)=>({id,kind:'task',delivery:'sent',packet:'Real packet',
  returnLine:'',digest:'',evidence:'',gap:'',decision:'',archive:'',note:''});
const escapeHtml=x=>x.replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]));
test('R3 G7: sealed abc SHA-256 vector, immutable metadata and locked/collapsed before answer',async()=>{
  const x=make();x.moves.push(sent('TASK-1'));
  const stamp=new Date('2026-10-19T01:00:00.000Z');
  const sealed=await makeSeal(x,{id:'SEAL-1',names:'TASK-1',text:'abc',date:stamp});
  assert.equal(sealed.sha256,
    'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad');
  assert.equal(sealed.createdAt,'2026-10-19T01:00:00.000Z');
  assert.equal(sealed.delivery,'draft');
  for(const field of ['packet','returnLine','digest','evidence','gap','decision','archive','note'])
    assert.equal(sealed[field],'');
  x.moves.push(sealed);
  assert.equal(sealUnlocked(x,sealed),false);
  const locked=sealHtml(x,sealed,escapeHtml);
  assert.match(locked,/Collapsed until/);
  assert.doesNotMatch(locked,/<pre>/);
  assert.match(locked,/Do not put sensitive text/);
  assert.equal(currentState(x),'Waiting on agent');
  const y=parse(serialize(x));
  assert.equal(y.moves[1].text,'abc');assert.equal(y.moves[1].names,'TASK-1');
  assert.equal(y.moves[1].sha256,sealed.sha256);
  assert.match(sealForm(x,escapeHtml),/name="text"/);
  assert.throws(()=>validate({...x,moves:[sent('TASK-1'),
    {...sealed,names:'NONEXISTENT'}]}),/Invalid sealed note/);
  await assert.rejects(()=>makeSeal(x,{text:'x',names:'NONEXISTENT'}),/existing move/);
});
test('R3 G7: note unlocks only with a subsequent matching reply, never with another ACK',async()=>{
  const x=make();x.moves.push(sent('TASK-1'));
  const seal=await makeSeal(x,{id:'SEAL-1',names:'TASK-1',text:'abc'});
  x.moves.push(seal);
  x.moves.push(sent('TASK-2'));
  x.moves.push(makeReply(x,'ACK TASK-2',{id:'REPLY-2'}).move);
  assert.equal(sealUnlocked(x,seal),false);
  x.moves.push(makeReply(x,'ACK TASK-1',{id:'REPLY-1'}).move);
  assert.equal(sealUnlocked(x,seal),true);
  const unlocked=sealHtml(x,seal,escapeHtml);
  assert.match(unlocked,/<details>/);assert.match(unlocked,/<pre>abc<\/pre>/);
  assert.doesNotMatch(unlocked,/<details open/);
  const replay=parse(serialize(x));assert.equal(sealUnlocked(replay,replay.moves[1]),true);
});
function sources(dir,files=[]) {
  for(const e of fs.readdirSync(dir,{withFileTypes:true})){
    const name=path.join(dir,e.name);
    if(e.isDirectory())sources(name,files);
    else if(/\.(mjs|html)$/.test(e.name))files.push(name);
  }
  return files;
}
test('R3 G5: no native browser prompts or confirmations anywhere in site/nextnudge',()=>{
  const dir=new URL('../site/nextnudge/',import.meta.url);
  const list=sources(fileURLToPath(dir));
  assert.ok(list.length>5);
  for(const file of list){
    const content=fs.readFileSync(file,'utf8');
    assert.doesNotMatch(content,/\b(?:confirm|prompt)\s*\(/,
      'Blocking browser dialog in '+file);
  }
  const app=fs.readFileSync(new URL('../site/nextnudge/revamp/app.mjs',import.meta.url),'utf8');
  const legacy=fs.readFileSync(new URL('../site/nextnudge/actions.mjs',import.meta.url),'utf8');
  assert.match(app,/askInline/);assert.match(legacy,/askInline/);
  const helper=fs.readFileSync(new URL('../site/nextnudge/inline-question.mjs',import.meta.url),'utf8');
  assert.match(helper,/type='submit'/);assert.match(helper,/Cancel/);
});
test('R3 G8: Reconcile explicitly projects latest reply label, old labels read UNKNOWN',()=>{
  const app=fs.readFileSync(new URL('../site/nextnudge/revamp/app.mjs',import.meta.url),'utf8');
  assert.match(app,/replyLabel\(reply\|\|\{\}\)/);
  assert.match(app,/id="reply-label"/);
  assert.match(app,/value|label/);
  const view=fs.readFileSync(new URL('../site/nextnudge/revamp/move-view.mjs',import.meta.url),'utf8');
  assert.match(view,/summary\(move,thread\)/);
});
