import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {newThread,validate} from '../site/nextnudge/revamp/thread.mjs';
import * as saved from '../site/nextnudge/revamp/save.mjs';
import {groundingMove,readGrounding} from '../site/nextnudge/revamp/grounding.mjs';
import {installFeatures,renderGrounding} from '../site/nextnudge/revamp/features.mjs';

const DRAFTS='nextnudge.grounding.drafts.v1';
const source=fs.readFileSync(new URL('../site/nextnudge/revamp/app.mjs',import.meta.url),'utf8');
// Execute the real app commit consumer; only rendering is replaced by a witness.
const putSource=source.slice(source.indexOf('function put(thread)'),source.indexOf('function renderThreads()'));
const appendSource=source.slice(source.indexOf('function append(move)'),source.indexOf('async function archiveList()'));
function fixture(options={}){
  const thread=newThread({id:'NN-20261020-000000-aa11',title:'Storage safety',goal:'Preserve edits'});
  if(options.existing)thread.moves.push(groundingMove(thread,{'1f':'Existing context'},'BASE'));
  const text=options.existing?' Existing context ':'Important unsaved context\nSecond reference';
  const map=new Map([[saved.LOCAL,JSON.stringify({[thread.id]:thread})],
    [DRAFTS,JSON.stringify({[thread.id]:{'1f':text}})]]);
  const original=Object.fromEntries(['document','localStorage','FormData'].map(k=>[k,globalThis[k]]));
  const handlers={},statuses=[{textContent:''},{textContent:''}],writes=[];
  const form={id:'grounding-form',fields:[['ground-1f',text]]};
  const state={threads:{[thread.id]:thread},active:thread.id,draft:null,editor:null};
  let rendered='',notice='';
  globalThis.localStorage={getItem:k=>map.get(k)??null,setItem:(k,v)=>{
    writes.push({key:k,draftPresent:!!JSON.parse(map.get(DRAFTS)||'{}')[thread.id]});
    if(k===saved.LOCAL&&options.snapshotFail)throw Error('Snapshot quota exceeded');
    if(k===DRAFTS&&options.cleanupFail)throw Error('Draft cleanup unavailable');
    map.set(k,v);
  }};
  globalThis.FormData=class{constructor(f){return new Map(f.fields);}};
  globalThis.document={addEventListener:(name,fn)=>handlers[name]=fn,
    querySelector:()=>form,querySelectorAll:()=>statuses};
  const t=()=>state.threads[state.active],render=()=>{rendered=renderGrounding(t());};
  render();
  const append=new Function('state','t','validate','persist','persistMove','clearComposer','render',
    putSource+'\n'+appendSource+'\nreturn append;')(
      state,t,validate,saved.persist,saved.persistMove,()=>{},render);
  installFeatures({state,t,append,render,notice:s=>{notice=s;}});
  return {thread,options,writes,statuses,t,map,form,
    submit:()=>handlers.submit({target:form,preventDefault(){}}),
    reload:()=>saved.localThreads()[thread.id],
    draft:()=>JSON.parse(map.get(DRAFTS)||'{}')[thread.id],
    html:()=>rendered,notice:()=>notice,
    restore:()=>Object.assign(globalThis,original)};
}

test('Storage116: save retains backup until persistence, then cleans it without mutating old history',()=>{
  const f=fixture();try{
    f.submit();
    assert.equal(f.writes.find(x=>x.key===saved.LOCAL)?.draftPresent,true);
    assert.equal(f.thread.moves.length,0);
    assert.equal(f.t().moves.length,1);
    assert.equal(readGrounding(f.reload())['1f'],f.form.fields[0][1]);
    assert.equal(f.draft(),undefined);
    assert.doesNotMatch(f.html(),/Unsaved device draft restored/);
    assert.match(f.statuses[0].textContent,/saved locally/);
  }finally{f.restore();}
});
test('Storage116: failed write preserves active history, persisted history and recoverable draft',()=>{
  const f=fixture({snapshotFail:true});try{
    f.submit();
    assert.equal(f.t(),f.thread);
    assert.equal(f.t().moves.length,0,'failed writes must not mutate active history');
    assert.equal(f.reload().moves.length,0);
    assert.equal(f.draft()['1f'],f.form.fields[0][1]);
    assert.match(f.notice(),/Snapshot quota exceeded/);
    assert.doesNotMatch(f.notice(),/saved locally/);
  }finally{f.restore();}
});
test('Storage116: retry after failed save commits once; unchanged save adds nothing',()=>{
  const f=fixture({snapshotFail:true});try{
    f.submit();f.options.snapshotFail=false;f.submit();
    assert.equal(f.reload().moves.length,1);
    assert.equal(f.t().moves.length,1);
    assert.equal(f.draft(),undefined);
    f.submit();
    assert.equal(f.reload().moves.length,1);
    assert.match(f.notice(),/unchanged/);
  }finally{f.restore();}
});
test('Storage116: cleanup failure retains backup after commit and retry does not duplicate snapshot',()=>{
  const f=fixture({cleanupFail:true});try{
    f.submit();
    assert.equal(f.reload().moves.length,1,'snapshot must commit before optional cleanup');
    assert.equal(f.t().moves.length,1);
    assert.equal(f.draft()['1f'],f.form.fields[0][1]);
    assert.match(f.notice(),/saved locally/);
    assert.match(f.notice(),/backup retained/i);
    assert.doesNotMatch(f.html(),/Unsaved device draft restored/);
    f.options.cleanupFail=false;f.submit();
    assert.equal(f.reload().moves.length,1);
    assert.equal(f.draft(),undefined);
    assert.match(f.notice(),/unchanged/);
  }finally{f.restore();}
});
test('Storage116: normalized unchanged draft refreshes banner without another snapshot',()=>{
  const f=fixture({existing:true});try{
    f.submit();
    assert.equal(f.reload().moves.length,1);
    assert.equal(f.draft(),undefined);
    assert.doesNotMatch(f.html(),/Unsaved device draft restored/);
    assert.match(f.notice(),/unchanged/);
  }finally{f.restore();}
});
