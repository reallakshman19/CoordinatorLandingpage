import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {prepareSave,fingerprint,readRepository} from '../site/nextnudge/repository.mjs';
import {validate} from '../site/nextnudge/schema.mjs';
import {migrate} from '../site/nextnudge/migrate.mjs';
const db=JSON.parse(fs.readFileSync(new URL('fixtures/nextnudge-issue97-pilot.json',import.meta.url)));
function remote(value,sha='a'.repeat(40)) {
  return {ok:true,json:async()=>({sha,encoding:'base64',content:Buffer.from(JSON.stringify(value)).toString('base64')})};
}
test('real issue pilot validates and distinguishes implementation from rehearsal',()=>{
  validate(db);assert.equal(db.runs.length,2);
  assert(db.runs[0].fixtures['1a'][0].url.endsWith('/issues/97'));
  assert(db.runs[1].fixtures['1a'][0].source.run===db.runs[0].id);
  assert(!db.events.some(e=>e.state==='SENT'||e.state==='ACCEPTED'));
});
test('save refuses a changed base and prepares exact data without writing',async()=>{
  const requests=[];globalThis.fetch=async(url,opts)=>{requests.push(opts);return remote(db);};
  await assert.rejects(()=>prepareSave(db,'b'.repeat(40)),/changed|unknown/);
  const prepared=await prepareSave(db,'a'.repeat(40));
  assert.deepEqual(JSON.parse(prepared.text),db);
  assert.equal(prepared.digest,await fingerprint(db));
  assert(requests.every(o=>!o.method||o.method==='GET'));
});
test('readback detects unsaved or changed content; network error is explicit',async()=>{
  globalThis.fetch=async()=>remote(db);
  assert.equal((await readRepository()).sha,'a'.repeat(40));
  const changed=structuredClone(db);changed.projects[0].name='new draft';
  assert.notEqual(await fingerprint(db),await fingerprint(changed));
  globalThis.fetch=async()=>({ok:false,status:403});
  await assert.rejects(()=>readRepository(),/403/);
});
test('legacy migration removes future locks and preserves honest unknown times',()=>{
  const runId=crypto.randomUUID(),nodeId=crypto.randomUUID();
  const old={schemaVersion:1,runs:[{id:runId,title:'Legacy',aim:'Recover work',types:['Conceptual'],
    nodes:[{id:nodeId,title:'Any custom nudge',instruction:'Do work',index:2,parent:null,status:'locked',messages:[]}],selected:nodeId,drafts:{}}]};
  const migrated=migrate(old,db.profiles);validate(migrated);
  assert.equal(migrated.runs[0].nodes[0].status,'ready');
  assert.equal(migrated.runs[0].nodes[0].sentAt,null);
  old.runs[0].nodes[0].id='x" onclick="alert(1)';
  assert.throws(()=>migrate(old,db.profiles));
});

test('live repository data is schema-valid without pinning mutable run or event counts',()=>{
  const live=JSON.parse(fs.readFileSync(new URL('../site/nextnudge-data/workbench.json',import.meta.url)));
  assert.equal(validate(live),live);
});
