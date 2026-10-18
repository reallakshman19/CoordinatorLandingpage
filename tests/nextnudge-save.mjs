import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {gzipSync} from 'node:zlib';
import {createHash} from 'node:crypto';
import {buildDelta,applyDelta,fingerprint,prepareIssueSave} from '../site/nextnudge/repository.mjs';
import {applyIssue,ownerIssue,unpack,sweepUnreceipted,SUPERSEDED_RECEIPT} from '../scripts/nextnudge_apply.mjs';
import {event} from '../site/nextnudge/model.mjs';
import {action} from '../site/nextnudge/actions.mjs';
import {packet as chatPacket} from '../site/nextnudge/model.mjs';

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
test('rejecting clipboard exposes the exact read-only preselected chat packet and GitHub JSON',async()=>{
  const elements=new Map();
  globalThis.document={querySelector:q=>{
    if(!elements.has(q))elements.set(q,{
      hidden:true,readOnly:true,value:'',textContent:'',focused:0,selected:0,
      focus(){this.focused++;},select(){this.selected++;}
    });
    return elements.get(q);
  }};
  Object.defineProperty(globalThis,'navigator',{
    configurable:true,value:{clipboard:{writeText:async()=>{throw Error('Write permission denied');}}}
  });
  globalThis.fetch=async()=>({ok:true,json:async()=>({
    sha:A,encoding:'base64',content:Buffer.from(JSON.stringify(base)).toString('base64')
  })});
  const db=structuredClone(base),r=db.runs[0],n=r.nodes[0];
  const expectedChat=chatPacket(r,n);
  const state={db,baseSha:A,prepared:null,dirty:true,conflict:false};
  let saves=0,renders=0;
  const ctx={s:state,run:r,node:n,save:()=>{saves++;},render:()=>{renders++;}};
  await action('copy-step',{},ctx);
  const field=elements.get('#chat-manual-packet');
  assert.equal(field.value,expectedChat);
  assert.equal(field.hidden,false);
  assert.equal(field.readOnly,true);
  assert.equal(field.focused,1);
  assert.equal(field.selected,1);
  assert.equal(elements.get('#chat-manual-select').hidden,false);
  assert.equal(n.copied.text,expectedChat);
  assert.match(elements.get('#notice').textContent,/Clipboard denied/);
  assert.equal(saves,1);
  assert.equal(renders,1);
  await action('select-chat-packet',{},ctx);
  assert.equal(field.selected,2);
  assert.equal(field.value,expectedChat);

  const exactJSON=JSON.stringify(db,null,2)+'\n';
  await action('github-prepare',{},ctx);
  const githubField=elements.get('#github-manual-json');
  assert.equal(githubField.value,exactJSON);
  assert.equal(githubField.readOnly,true);
  assert.equal(githubField.hidden,false);
  assert.equal(githubField.focused,1);
  assert.equal(githubField.selected,1);
  assert.equal(elements.get('#github-manual-select').hidden,false);
  assert.equal(state.prepared,await fingerprint(db));
  assert.match(elements.get('#notice').textContent,/Clipboard permission denied/);
  await action('select-github-json',{},ctx);
  assert.equal(githubField.selected,2);
  assert.equal(githubField.value,exactJSON);

  const html=fs.readFileSync(new URL('../site/nextnudge/index.html',import.meta.url),'utf8');
  for(const id of ['chat-manual-packet','github-manual-json']){
    assert.match(html,new RegExp('<textarea[^>]+id="'+id+'"[^>]*readonly'));
  }
  assert.match(html,/data-action="select-chat-packet"/);
  assert.match(html,/data-action="select-github-json"/);
});
test('delta handles new and deleted IDs, changed runs, and optional profile updates',async()=>{
  const db=structuredClone(base);
  const removed=db.runs.shift().id;
  db.runs[0].title+=' revised';
  const newRun=structuredClone(db.runs[0]);
  // Deterministically make a distinct schema-valid run and its node IDs.
  const unique=i=>'NN-20261018-213000-'+String(i).padStart(4,'0');
  newRun.id=unique(1);newRun.title='New independent run';
  newRun.nodes=newRun.nodes.map((n,i)=>({...n,id:unique(i+2),parent:null}));
  newRun.selected=newRun.nodes[0]?.id;
  newRun.fixtures=Object.fromEntries(Object.keys(newRun.fixtures).map(key=>[key,[]]));
  newRun.drafts={};
  db.runs.push(newRun);
  db.profiles.profiles.Extra=[];
  event(db,null,null,'BULK_UPDATED','Upsert/delete/profile qualification.');
  const p=await packetFor(db);
  assert(p.delta.runs.deleted.includes(removed));
  assert(Object.hasOwn(p.delta.runs.upsert,newRun.id));
  assert(Object.hasOwn(p.delta,'profiles'));
  assert.deepEqual(applyDelta(base,p),db);
});
test('late compare-and-swap conflict never reports SAVED',async()=>{
  const h=harness();h.writeCurrent=async()=>{const e=Error('raced');e.status=409;throw e;};
  const result=await applyIssue({issue:issue(await packetFor()),owner:'reallakshman19',...h});
  assert.equal(result,'NEEDS RELOAD');
  assert.match(h.comments[0],/changed during the commit/);
  assert.equal(h.closes.length,1);
});
test('sweep receipts only older unreceipted owner saves, never current or newer pending',async()=>{
  const owner='reallakshman19';
  const candidate=(number,login=owner,labels=['nextnudge-save'])=>({
    number,state:'open',user:{login},labels:labels.map(name=>({name}))
  });
  const items=[
    candidate(1),candidate(2),candidate(3),candidate(4),candidate(5),
    candidate(6,'outsider'),candidate(7,owner,['other']),candidate(8),
    {...candidate(9),pull_request:{url:'pr'}},candidate(10),candidate(11),
  ];
  const comments=new Map([
    [2,[{user:{login:'github-actions[bot]'},body:'SAVED: authentic commit'}]],
    [3,[{user:{login:'github-actions[bot]'},body:'NEEDS RELOAD: stale blob'}]],
    [4,[{user:{login:'github-actions[bot]'},body:'REJECTED: bad packet'}]],
    [5,[{user:{login:'outsider'},body:'SAVED: spoofed receipt'}]],
  ]);
  const calls=[],receiptWrites=[],closes=[];
  const fake={
    owner,currentIssueNumber:10,
    listOpenIssues:async page=>{calls.push('issues:'+page);
      return page===1?items:[];},
    listComments:async(number,page)=>{calls.push('comments:'+number+':'+page);
      return page===1?(comments.get(number)||[]):[];},
    commentIssue:async(number,body)=>{receiptWrites.push({number,body});
      comments.set(number,[{user:{login:'github-actions[bot]'},body}]);},
    closeIssue:async number=>{closes.push(number);const entry=items.find(x=>x.number===number);
      entry.state='closed';}
  };
  assert.equal(await sweepUnreceipted(fake),3);
  assert.deepEqual(receiptWrites.map(x=>x.number),[1,5,8]);
  assert.deepEqual(closes,[1,5,8]);
  assert(receiptWrites.every(x=>x.body===SUPERSEDED_RECEIPT));
  assert.match(SUPERSEDED_RECEIPT,/^NEEDS RELOAD: this save was superseded before it ran\. Nothing was written\. Prepare a fresh save\.$/);
  assert(!closes.includes(10),'current issue must not be closed');
  assert(!closes.includes(11),'newer pending issue must not be closed');
  assert(calls.includes('issues:2'));
  assert.equal(await sweepUnreceipted(fake),0,'second sweep must be idempotent');
  assert.deepEqual(closes,[1,5,8]);
});
test('sweep snapshots all open issue pages before closing, preventing skipped saves',async()=>{
  const owner='reallakshman19';
  const items=Array.from({length:120},(_,i)=>({
    number:i+1,state:'open',user:{login:owner},labels:[{name:'nextnudge-save'}]
  }));
  const readPages=[],writes=[],closes=[];
  const count=await sweepUnreceipted({
    owner,currentIssueNumber:122,
    listOpenIssues:async page=>{
      readPages.push(page);
      return items.filter(x=>x.state==='open').slice((page-1)*100,page*100);
    },
    listComments:async()=>[],
    commentIssue:async(n,body)=>{writes.push(n);assert.equal(body,SUPERSEDED_RECEIPT);},
    closeIssue:async n=>{closes.push(n);items[n-1].state='closed';}
  });
  assert.deepEqual(readPages,[1,2,3]);
  assert.equal(count,120);
  assert.equal(new Set(writes).size,120);
  assert.deepEqual(closes,Array.from({length:120},(_,i)=>i+1));
  assert.equal(items.filter(x=>x.state==='open').length,0);
});
test('sweep finds a receipt on later comment pages and leaves the issue untouched',async()=>{
  const owner='reallakshman19',closed=[];
  const count=await sweepUnreceipted({
    owner,currentIssueNumber:4,
    listOpenIssues:async page=>page===1?[{
      number:3,state:'open',user:{login:owner},labels:['nextnudge-save']
    }]:[],
    listComments:async(_number,page)=>page===1?
      [{user:{login:'other'},body:'A comment but not a receipt'}]:
      page===2?[{user:{login:'github-actions[bot]'},body:'SAVED: r1'}]:[],
    commentIssue:async()=>{throw Error('must not append a second receipt');},
    closeIssue:async n=>closed.push(n)
  });
  assert.equal(count,0);
  assert.deepEqual(closed,[]);
});
test('closed issue cannot write if superseded sweep closed it before its run starts',async()=>{
  const packet=await packetFor(),h=harness();
  assert.equal(await applyIssue({
    issue:{...issue(packet),state:'closed'},owner:'reallakshman19',...h
  }),'IGNORED');
  assert.equal(h.writes.length+h.comments.length+h.closes.length,0);
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
