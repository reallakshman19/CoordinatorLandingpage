import test from 'node:test';
import assert from 'node:assert/strict';
import {newThread} from '../site/nextnudge/revamp/thread.mjs';
import {groundingPanel,readGrounding} from '../site/nextnudge/revamp/grounding.mjs';
import {HEADINGS} from '../site/nextnudge/fixtures.mjs';
import {installFeatures} from '../site/nextnudge/revamp/features.mjs';
const thread=()=>newThread({id:'NN-20261019-173100-aa11',title:'Grounding UI',goal:'Preserve context'});
test('NN110 UI: all original headings remain optional and text is escaped',()=>{
  const html=groundingPanel(thread(),{'1f':'<script>do not run</script>'});
  assert.equal((html.match(/<textarea /g)||[]).length,HEADINGS.length);
  for(const [,key] of HEADINGS)assert.ok(html.includes('name="ground-'+key+'"'));
  assert.match(html,/&lt;script&gt;/);assert.doesNotMatch(html,/<script>/);
  assert.doesNotMatch(html,/textarea[^>]*required/);
});
test('NN110 UI: typing creates no log entries; a single submit saves all context and rejects private links',()=>{
  const originals={document:globalThis.document,FormData:globalThis.FormData,localStorage:globalThis.localStorage};
  const handlers={},store=new Map(),t=thread(),form={id:'grounding-form',fields:[['ground-1f','My task'],['ground-1a','https://github.com/reallakshman19/CoordinatorLandingpage/issues/110']]};
  globalThis.document={addEventListener:(name,handler)=>{handlers[name]=handler;},querySelector:()=>form};
  globalThis.FormData=class{constructor(f){this.rows=f.fields;}[Symbol.iterator](){return this.rows[Symbol.iterator]();}};
  globalThis.localStorage={getItem:k=>store.get(k)||null,setItem:(k,v)=>store.set(k,v)};
  let notice='';
  try{
    installFeatures({state:{},t:()=>t,append:m=>t.moves.push(m),render:()=>{},notice:s=>{notice=s;}});
    handlers.input({target:{id:'field',closest:()=>form}});
    assert.equal(t.moves.length,0,'no per-keystroke history');
    handlers.submit({target:form,preventDefault:()=>{}});
    assert.equal(t.moves.length,1);assert.equal(readGrounding(t)['1f'],'My task');
    handlers.submit({target:form,preventDefault:()=>{}});assert.equal(t.moves.length,1,'unchanged save is silent');
    form.fields=[['ground-1f','https://chatgpt.com/c/private']];
    handlers.submit({target:form,preventDefault:()=>{}});
    assert.equal(t.moves.length,1);assert.match(notice,/Private chat URL/);
  }finally{Object.assign(globalThis,originals);}
});
