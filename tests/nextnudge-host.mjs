import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
import {renderNextNudge} from '../site/nextnudge/host.mjs';
function element(tag='div') {
  return {tag,dataset:{},style:{},children:[],classList:{toggle(){},remove(){}},
    appendChild(e){this.children.push(e);},setAttribute(k,v){this[k]=v;},
    addEventListener(){},replaceChildren(...values){this.children=values;},querySelector(){return null;}};
}
function dashboard() {
  const nav=element(),app=element(),exit=element();let clears=0;
  Object.defineProperty(app,'innerHTML',{set(){clears++;}});
  const frame=element('iframe');app.querySelector=()=>frame;
  const document={baseURI:'https://example.test/CoordinatorLandingpage/',
    querySelector:()=>null,querySelectorAll:()=>nav.children,createElement:element,
    getElementById:id=>id==='nav-tabs'?nav:id==='app'?app:exit,addEventListener(){}};
  const context=vm.createContext({document,URL,console,window:{location:{hash:'#nextnudge'},addEventListener(){},setInterval(){}}});
  const path=process.env.NEXTNUDGE_CORE||new URL('../site/js/core.js',import.meta.url);
  vm.runInContext(fs.readFileSync(path,'utf8'),context);
  vm.runInContext('state.projects=[{}]; pollBuildInfo=async()=>false; renderHome=async()=>{};',context);
  return {context,nav,app,clears:()=>clears};
}
test('dashboard navigation registers NextNudge',async()=>{
  const h=dashboard();vm.runInContext('render=async()=>{}; init();',h.context);
  assert(h.nav.children.some(n=>n.dataset.view==='nextnudge'&&n.textContent==='NextNudge · Beta'));
});
test('dashboard refresh preserves an existing NextNudge frame and draft DOM',async()=>{
  const h=dashboard();await vm.runInContext('render()',h.context);assert.equal(h.clears(),0);
});
test('host uses local assets and blocks benchmark editing',()=>{
  globalThis.document={baseURI:'https://example.test/CoordinatorLandingpage/',createElement:element};
  const app=element();renderNextNudge(app,false,'abc12345');
  assert.equal(app.children[0].src,'https://example.test/CoordinatorLandingpage/nextnudge/index.html?v=abc12345');
  renderNextNudge(app,true,'abc12345');assert(!app.children.some(x=>x.tag==='iframe'));
  assert.match(app.children[0].textContent,/benchmark/);
});
