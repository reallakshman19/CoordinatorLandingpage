'use strict';
const fs = require('node:fs'), Module = require('node:module'), path = require('node:path');
const root = process.env.ORACLE_REPO_ROOT || path.resolve(__dirname, '../../..');
const file = path.join(root, 'tests/dashboard.test.cjs');
const originalRead = fs.readFileSync;
if (process.env.ORACLE_MUTANT === 'hardcoded-one') {
 fs.readFileSync = function (p, ...args) {
  const result = originalRead.call(this,p,...args);
  return String(p).endsWith('/site/js/dashboard.js') && typeof result === 'string'
   ? result.replace("source.projects.length + (source.projects.length === 1 ? ' project' : ' projects')", "'1 project'") : result;
 };
}
const challenge = `
for (const [label,count,catalogCount] of [['empty source',0,2],['two projects',2,0],['conflicting auxiliary catalog',2,1]]) {
 test('Oracle count challenge: '+label,async()=>{
  const s=source(); s.projects=Array.from({length:count},(_,i)=>({project:'p'+i}));
  const h=harness(s); h.context.state.projects=Array.from({length:catalogCount},(_,i)=>({project:'aux'+i}));
  await h.context.renderDashboard(h.app);
  assert(h.all().some(e=>e.textContent===count+(count===1?' project':' projects')+' · coordinator cycles in project view'));
  h.context.stopDashboard();
 });
}
test('Oracle capture challenge: fresh capture does not refresh stale direct activity',async()=>{
 const s=source([row({observation:{state:'WORKING',observed_at:iso(-40)}})]);
 const h=harness(s); h.context.state.buildInfo.source_capture_at=iso(0);
 await h.context.renderDashboard(h.app);
 assert.equal(M.snapshot(s,now,false).rows[0].activityAge,40*60000);
 assert.equal(M.snapshot(s,now,false).rows[0].light,'yellow');
 assert(h.all().some(e=>e.textContent==='● YELLOW'));
 h.advance(120000);
 assert(h.all().some(e=>e.textContent.includes('42:00 ago')));
 assert.equal(h.fetches,1); h.context.stopDashboard();
});
`;
const m = new Module(file,module);m.filename=file;m.paths=Module._nodeModulePaths(path.dirname(file));
m._compile(originalRead.call(fs,file,'utf8')+'\n'+challenge,file);
