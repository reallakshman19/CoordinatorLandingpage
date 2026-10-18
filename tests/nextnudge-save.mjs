import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {gzipSync} from 'node:zlib';
import {createHash} from 'node:crypto';
import {buildDelta,applyDelta,fingerprint,prepareIssueSave} from '../site/nextnudge/repository.mjs';
import {applyIssue,ownerIssue,unpack} from '../scripts/nextnudge_apply.mjs';
import {event} from '../site/nextnudge/model.mjs';
import {action} from '../site/nextnudge/actions.mjs';

const base=JSON.parse(fs.readFileSync(new URL('fixtures/nextnudge-issue97-pilot.json',import.meta.url),'utf8'));
const A='a'.repeat(40),B='b'.repeat(40);
function changed() {
  const db=structuredClone(base);
  db.projects[0].name+=' · saved';
  event(db,null,null,'SAVED_DRAFT','Save test added a source-bound event.');
  return db;
}
async function packetFor(db=changed()) {
  return {v:1,baseSha:A,baseRevision:base.revision,revision:db.revision,
    digest:await fingerprint(db),delta:buildDelta(base,db)};
}
function body(packet) {
  return 'NextNudge request\n\n```nextnudge-save\n'+
    gzipSync(JSON.stringify(packet)).toString('base64')+'\n```';
}
function issue(packet,user='reallakshman19') {
  return {number:123,body:body(packet),user:{login:user},labels:[{name:'nextnudge-save'}]};
}
function harness(source=base,sha=A) {
  const writes=[],comments=[],closes=[];
  return {writes,comments,closes,
    readCurrent:async()=>({db:structuredClone(source),sha}),
    writeCurrent:async(text,oldSha,revision,no)=>{
      writes.push({text,oldSha,revision,no});
      return {url:'https://github.com/reallakshman19/CoordinatorLandingpage/commit/abc'};
    },
    comment:async text=>comments.push(text),close:async()=>closes.push(true)};
}
test('good packet reconstructs exact digest-backed committed JSON bytes',async()=>{
  const next=changed(),packet=await packetFor(next),h=harness();
  assert.deepEqual(applyDelta(base,packet),next);
  const result=await applyIssue({issue:issue(packet),owner:'reallakshman19',...h});
  assert.equal(result,'SAVED');
  assert.equal(h.writes.length,1);
  assert.equal(h.writes[0].text,JSON.stringify(next,null,2)+'\n');
  assert.equal(h.writes[0].oldSha,A);
  assert.match(h.comments[0],/^SAVED: https:\/\/github.com\/.* · revision /);
  assert.equal(h.closes.length,1);
  assert.equal(await fingerprint(JSON.parse(h.writes[0].text)),packet.digest);
});
test('a stale base issues NEEDS RELOAD and writes nothing',async()=>{
  const h=harness(base,B),packet=await packetFor();
  assert.equal(await applyIssue({issue:issue(packet),owner:'reallakshman19',...h}),'NEEDS RELOAD');
  assert.equal(h.writes.length,0);
  assert.match(h.comments[0],/NEEDS RELOAD: GitHub changed since your draft/);
  assert.equal(h.closes.length,1);
});
test('schema violation and digest mismatch are independently rejected',async()=>{
  const bad=await packetFor();
  bad.delta.projects.upsert[base.projects[0].id].name=100;
  const h=harness();
  assert.equal(await applyIssue({issue:issue(bad),owner:'reallakshman19',...h}),'REJECTED');
  assert.match(h.comments[0],/REJECTED: Invalid backup/);
  const mismatch=await packetFor();mismatch.digest='0'.repeat(64);
  const h2=harness();
  assert.equal(await applyIssue({issue:issue(mismatch),owner:'reallakshman19',...h2}),'REJECTED');
  assert.match(h2.comments[0],/digest mismatch/);
  assert.equal(h.writes.length+h2.writes.length,0);
});
test('unauthorized author is ignored before packet decode or GitHub write',async()=>{
  const h=harness(),external=issue(await packetFor(),'outside-user');
  external.body='attack input';
  assert.equal(ownerIssue(external,'reallakshman19'),false);
  assert.equal(await applyIssue({issue:external,owner:'reallakshman19',...h}),'IGNORED');
  assert.equal(h.writes.length+h.comments.length+h.closes.length,0);
});
test('oversized decoded, malformed base64, and duplicate code blocks are rejected',async()=>{
  const p=await packetFor();
  const tooLarge=structuredClone(p);
  tooLarge.delta.events[0].note='Z'.repeat(201000);
  assert.throws(()=>unpack(body(tooLarge)),/200 KB/);
  assert.throws(()=>unpack('x\n```nextnudge-save\n@@@\n```'),/expected one|base64/);
  assert.throws(()=>unpack(body(p)+'\n'+body(p)),/expected one/);
});
test('browser gzip packet roundtrips; narrow editor fallback activates over 7500 chars',async()=>{
  const roundtrip=changed();
  const prepared={base,digest:await fingerprint(roundtrip)};
  const result=await prepareIssueSave(roundtrip,prepared,A);
  assert(result.url.startsWith('https://github.com/reallakshman19/CoordinatorLandingpage/issues/new?'));
  const parsed=new URL(result.url);
  assert.equal(parsed.searchParams.get('labels'),'nextnudge-save');
  assert.equal(unpack(parsed.searchParams.get('body')).digest,prepared.digest);
  const draft=structuredClone(base);
  // Incompressible but schema-valid evidence; large packets must use the editor.
  const random=Array.from({length:460},(_,i)=>createHash('sha256').update('seed-'+i).digest('hex')).join('');
  event(draft,null,null,'LARGE_NOTE',random);
  const elements=new Map();
  globalThis.document={querySelector:q=>{
    if(!elements.has(q))elements.set(q,{hidden:true,value:'',textContent:''});
    return elements.get(q);
  }};
  let closed=0,copied='';
  globalThis.window={open:()=>({close:()=>{closed++;},location:{replace:()=>{throw Error('unexpected redirect');}}})};
  Object.defineProperty(globalThis,'navigator',{value:{clipboard:{writeText:async text=>{copied=text;}}},configurable:true});
  globalThis.fetch=async()=>({ok:true,json:async()=>({
    sha:A,encoding:'base64',content:Buffer.from(JSON.stringify(base)).toString('base64')
  })});
  const s={db:draft,baseSha:A,prepared:null,dirty:true,conflict:false};
  await action('github-save',{}, {s,save:()=>{},render:()=>{}});
  assert.equal(closed,1);
  assert.equal(elements.get('#github-editor').hidden,false);
  assert.equal(copied,JSON.stringify(draft,null,2)+'\n');
  assert.equal(s.prepared,await fingerprint(draft));
  assert.match(elements.get('#notice').textContent,/7,500-character URL limit/);
});
test('workflow does not interpolate GitHub issue text into any shell command',()=>{
  const workflow=fs.readFileSync(new URL('../.github/workflows/nextnudge-save.yml',import.meta.url),'utf8');
  const code=fs.readFileSync(new URL('../scripts/nextnudge_apply.mjs',import.meta.url),'utf8');
  assert.match(workflow,/github\.event\.issue\.user\.login == github\.repository_owner/);
  assert.match(workflow,/issues:\s*\n\s*types: \[opened\]/);
  assert.match(workflow,/contents: write/);
  assert.match(workflow,/issues: write/);
  assert.doesNotMatch(workflow,/\$\{\{\s*github\.event\.issue\.body/);
  assert.match(workflow,/run: node scripts\/nextnudge_apply\.mjs/);
  assert.match(code,/api\('issues\/'\+number\)/);
  assert.doesNotMatch(workflow,/run:\s*\|[^]*github\.event\.issue\.body/);
});
