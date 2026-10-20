import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {gzipSync} from 'node:zlib';
import {newThread,serialize,parse,currentState,assertPublic} from '../site/nextnudge/revamp/thread.mjs';
import {newProject,addThread,updateFixtures,conflicts,assertAppendOnly} from '../site/nextnudge/revamp/project-model.mjs';
import {localProjects,persistProject,projectForThread,recordProjectSha,prepareProjectSave,discoverProjects} from '../site/nextnudge/revamp/project-store.mjs';
import {readGrounding,effectiveGrounding,groundingMove,groundingPanel,projectGroundingText} from '../site/nextnudge/revamp/grounding.mjs';
import {workspaceMove,defaults} from '../site/nextnudge/revamp/workspace.mjs';
import {projectsMarkup,projectMarkup} from '../site/nextnudge/revamp/screens.mjs';
import {unpackProject,applyProjectIssue} from '../scripts/nextnudge_project_apply.mjs';
import {PROJECT_HEADINGS} from '../site/nextnudge/fixtures.mjs';
const A='a'.repeat(40),B='b'.repeat(40);
const id=x=>'NN-20261020-120000-'+x;
const project=(x,name)=>newProject(name,'NP-20261020-120000-'+x);
const agent=(x,name)=>newThread({id:id(x),title:'Owner intent '+x,agent:name,goal:'Keep the actual result',doneWhen:['Acceptance evidence']});
const sent=packet=>({id:'TASK-1',kind:'task',delivery:'sent',packet,returnLine:'',digest:'',evidence:'',gap:'',decision:'',archive:'',note:''});
const memory=()=>{const map=new Map();return {getItem:k=>map.get(k)??null,setItem:(k,v)=>map.set(k,v),removeItem:k=>map.delete(k)};};
test('AC1 navigation structure and pre-existing workspaces and v2 Archive',()=>{
  const app=fs.readFileSync(new URL('../site/nextnudge/revamp/app.mjs',import.meta.url),'utf8');
  const a=agent('a001','Alpha'),p=addThread(project('b001','Project A'),a);
  assert.match(app,/view:'projects'/);assert.match(projectsMarkup({},{}),/v2 Archive/);
  assert.match(projectMarkup(p,{[a.id]:a}),/project-grounding/);
  const tabs=fs.readFileSync(new URL('../site/nextnudge/revamp/workspace-nav.mjs',import.meta.url),'utf8');
  for(const mode of ['Overview','Ground','Task','Correction','Reconcile'])assert.ok(tabs.includes(mode));
});
test('AC2 shared project context, cross-project isolation, 17 active optional fields, independent Ground',()=>{
  const old=globalThis.localStorage;globalThis.localStorage=memory();
  try{
    const a=agent('a001','Alpha'),b=agent('b001','Beta'),c=agent('c001','Alpha');
    let p=addThread(addThread(project('b001','A'),a),b);
    p=updateFixtures(p,{'1f':'Shared context','1a':'https://github.com/a/b/issues/3'},'2026-10-20T01:00:00Z');
    persistProject(p);persistProject(addThread(project('b002','B'),c));
    assert.equal(effectiveGrounding(a)['1f'],'Shared context');
    assert.equal(effectiveGrounding(b)['1f'],'Shared context');
    assert.deepEqual(effectiveGrounding(c),{});
    assert.deepEqual(readGrounding(a),{});
    const html=groundingPanel(null,p.fixtures,false,p);
    assert.equal((html.match(/<textarea /g)||[]).length,PROJECT_HEADINGS.length);
    assert.match(html,/project-grounding-form/);
    assert.match(projectGroundingText(p),/Shared context/);
    const m=workspaceMove(a,'ground',{brief:'Agent A orientation'},'G-1');
    assert.deepEqual(JSON.parse(m.note.slice('WORKSPACE_V1:'.length)).fixtures,p.fixtures);
    assert.equal(defaults(a,'ground').issue,'https://github.com/a/b/issues/3');
  }finally{globalThis.localStorage=old;}
});
test('AC3 AC6 duplicate prevention and historical collisions preserved',()=>{
  const a=agent('a001','Worker'),b=agent('b001','Worker');
  const p=addThread(project('b001','Project A'),a);
  assert.throws(()=>addThread(p,b),/already has a project thread/);
  const legacy=addThread(p,b,{legacy:true});
  assert.equal(conflicts(legacy).length,1);
  assert.deepEqual(legacy.threads.map(x=>x.id),[a.id,b.id]);
  assert.throws(()=>addThread(legacy,a,{legacy:true}),/already in project/);
});
test('AC4 old exact packets and Grounding Fixtures versions are not rewritten',()=>{
  const a=agent('a001','Worker');a.moves.push(sent('exact bytes\n  preserved\n'));
  a.moves.push(groundingMove(a,{'1f':'Older fixture'},'OLD-1'));
  const bytes=serialize(a);
  const p=updateFixtures(addThread(project('b001','Project A'),a,{legacy:true}),{'1f':'Shared newer'},'2026-10-20T01:00:00Z');
  assert.equal(parse(bytes).moves[0].packet,'exact bytes\n  preserved\n');
  assert.equal(readGrounding(parse(bytes))['1f'],'Older fixture');
  assert.equal(p.fixtures['1f'],'Shared newer');
  assert.equal(updateFixtures(p,{'1f':'Shared newer'}),null);
  assert.throws(()=>assertAppendOnly(p,{...p,snapshots:[]}),/history changed/);
});
test('AC5 AC8 Owner-only project writer, wrong SHA, privacy and no-op contrast',async()=>{
  const p=updateFixtures(project('b001','Project A'),{'3':'Golden fixtures'},'2026-10-20T01:00:00Z');
  const packet={v:1,id:p.id,baseSha:null,project:p};
  const fence=String.fromCharCode(96).repeat(3);
  const body=val=>fence+'nextnudge-project-save\n'+gzipSync(JSON.stringify(val)).toString('base64')+'\n'+fence;
  assert.deepEqual(unpackProject(body(packet)),packet);
  const issue={number:10,user:{login:'owner'},state:'open',labels:[{name:'nextnudge-save'}],body:body(packet)};
  const writes=[],receipts=[];let closed=0;
  const h={read:async()=>null,write:async(...args)=>writes.push(args),
    comment:async msg=>receipts.push(msg),close:async()=>{closed++;}};
  assert.equal(await applyProjectIssue({issue,owner:'owner',...h}),'SAVED');
  assert.equal(writes.length,1);assert.equal(JSON.parse(writes[0][1]).fixtures['3'],'Golden fixtures');
  assert.equal(await applyProjectIssue({issue:{...issue,user:{login:'other'}},owner:'owner',...h}),'IGNORED');
  assert.equal(writes.length,1);
  assert.equal(await applyProjectIssue({issue:{...issue,body:body({...packet,baseSha:A})},owner:'owner',...h}),'NEEDS RELOAD');
  assert.equal(writes.length,1);assert.match(receipts.at(-1),/Nothing written/);assert.equal(closed,2);
  assert.throws(()=>updateFixtures(p,{'1':'https://chatgpt.com/c/private'}),/Private chat URL/);
});
test('AC8 GitHub readback, stale draft survival and no-op save',async()=>{
  const oldFetch=globalThis.fetch,oldStorage=globalThis.localStorage;
  globalThis.localStorage=memory();const p=project('b001','A'),source=Buffer.from(JSON.stringify(p)).toString('base64');
  globalThis.fetch=async url=>url.includes('/projects/NP-')?
    {ok:true,status:200,json:async()=>({sha:A,encoding:'base64',content:source})}:
    {ok:true,status:200,json:async()=>[{name:p.id+'.json'}]};
  try{
    assert.deepEqual(await discoverProjects(),{imported:1,conflicts:0});
    await assert.rejects(prepareProjectSave(p),/Nothing new/);
    const next=updateFixtures(p,{'3':'Device draft'},'2026-10-20T01:00:00Z');
    persistProject(next);recordProjectSha(p.id,B);
    await assert.rejects(prepareProjectSave(next),/NEEDS RELOAD/);
    assert.equal(localProjects()[p.id].fixtures['3'],'Device draft');
    recordProjectSha(p.id,A);
    const prepared=await prepareProjectSave(next);
    assert.match(prepared.url,/nextnudge-project-save/);
  }finally{globalThis.fetch=oldFetch;globalThis.localStorage=oldStorage;}
});
test('AC7 AC9 unchanged security and workflow guards',()=>{
  const a=agent('a001','Agent');a.hold='Owner HOLD';assert.equal(currentState(a),'Your move');
  assert.throws(()=>assertPublic({'1f':'https://chatgpt.com/c/private'}),/Private chat URL/);
});

test('AC3/AC4 ambiguous legacy project associations keep original thread snapshots readable',()=>{
  const old=globalThis.localStorage;globalThis.localStorage=memory();
  try{
    const t=agent('a001','Worker');t.moves.push(groundingMove(t,{'1f':'Historical only'},'HIST-1'));
    const a=addThread(project('b001','A'),t,{legacy:true});
    const b=addThread(project('b002','B'),t,{legacy:true});
    persistProject(a);persistProject(b);
    assert.throws(()=>projectForThread(t.id),/Ambiguous project association/);
    assert.equal(effectiveGrounding(t)['1f'],'Historical only','never guess a project or leak its fixtures');
    assert.equal(parse(serialize(t)).moves.length,1);
  }finally{globalThis.localStorage=old;}
});
test('AC8 quota failure preserves previous committed project and pending draft for recovery',()=>{
  const old=globalThis.localStorage,raw=memory();globalThis.localStorage=raw;
  try{
    const p=project('b001','A');persistProject(p);
    const next=updateFixtures(p,{'1f':'Unsaved owner notes'},'2026-10-20T01:00:00Z');
    globalThis.localStorage={...raw,setItem:(key,value)=>{
      if(key==='nextnudge.projects.v1')throw Error('Storage quota');
      return raw.setItem(key,value);
    }};
    assert.throws(()=>persistProject(next),/Storage quota/);
    assert.deepEqual(localProjects()[p.id].fixtures,{},'last committed project survives');
    assert.equal(next.fixtures['1f'],'Unsaved owner notes','editable object retained for copy or retry');
    globalThis.localStorage=raw;persistProject(next);
    assert.equal(localProjects()[p.id].fixtures['1f'],'Unsaved owner notes');
  }finally{globalThis.localStorage=old;}
});
