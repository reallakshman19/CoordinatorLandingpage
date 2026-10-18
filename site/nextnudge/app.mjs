import {bootstrap,cache,KEY} from './storage.mjs';
import {action,importFile} from './actions.mjs';
import {submitForm,changed} from './forms.mjs';
import {workbench,history} from './workspace.mjs';
import {prepare} from './prepare.mjs';
import {fixtures} from './fixture-view.mjs';
import {protocol} from './protocol.mjs';
import {$,esc,options,notice} from './util.mjs';
const s={db:null,baseSha:null,dirty:false,prepared:null,projectId:null,runId:null,
  tab:'work',phase:'onboarding',showArchived:false,conflict:false};
function save(dirty=true) {
  if(s.conflict)throw Error('Another tab changed the draft. Reload first.');
  if(dirty)s.dirty=true;
  try{cache(s);}catch{notice('Browser storage failed. Export immediately; your changes are not saved.');}
  $('#save-state').textContent=s.dirty?'Browser draft · not committed':'Repository snapshot';
}
function selection() {
  const db=s.db;if(!db)return {};
  const project=db.projects.find(p=>p.id===s.projectId)||db.projects[0];
  s.projectId=project?.id;
  const runs=db.runs.filter(r=>r.projectId===s.projectId&&!r.deleted&&(s.showArchived||!r.archived));
  const run=runs.find(r=>r.id===s.runId)||runs[0];s.runId=run?.id;
  if(run&&!run.nodes.some(n=>n.id===run.selected&&!n.deleted))run.selected=run.nodes.find(n=>!n.deleted)?.id;
  return {project,runs,run,node:run?.nodes.find(n=>n.id===run.selected)};
}
function ctx(){return {s,...selection(),save,render};}
function render() {
  if(!s.db)return;
  const {run:r,node:n,runs}=selection();
  $('#project-select').innerHTML=options(s.db.projects.map(p=>[p.id,p.name+' · '+p.id]),s.projectId);
  $('#run-select').innerHTML=options(runs.map(r=>[r.id,r.title+' · '+r.id+(r.archived?' [archived]':'')]),s.runId);
  $('#save-state').textContent=s.dirty?'Browser draft · not committed':'Repository snapshot';
  $('#new-run').disabled=!s.projectId;
  $('#run-info').innerHTML=r?`<div><h2>${esc(r.title)}</h2><p>${esc(r.aim)}</p><small>${r.projectId} / ${r.id}</small></div>
    <div class="actions"><span class="pill">${r.nodes.filter(n=>!n.parent&&!n.deleted&&n.status==='accepted').length}/${r.nodes.filter(n=>!n.parent&&!n.deleted).length} steps reviewed</span>
    <button data-action="pause">${r.paused?'Resume':'Pause'}</button><button data-action="archive">${r.archived?'Unarchive':'Archive'}</button><button data-action="delete-run">Delete</button></div>`:'';
  $('#tabs').innerHTML=[['work','Workbench'],['prepare','Prepare the Ladder'],['fixtures','Grounding Fixtures'],['history','History'],['protocol','Nudge Protocol']].map(([id,label])=>`<button data-action="tab" data-id="${id}" class="${s.tab===id?'active':''}">${label}</button>`).join('');
  const scroll=$('#content').scrollTop;
  if(s.tab==='protocol')$('#content').innerHTML=protocol();
  else if(!r)$('#content').innerHTML='<div class="panel"><h2>Create a NextNudge to begin.</h2><p>Projects group independent task runs. Archive preserves them for later transfer.</p></div>';
  else if(s.tab==='fixtures')$('#content').innerHTML=fixtures(s.db,r,s.phase);
  else if(s.tab==='history')$('#content').innerHTML=history(s.db,r);
  else if(s.tab==='prepare')$('#content').innerHTML=n?prepare(s.db,r,n):'<button data-action="add-step">Add your first step</button>';
  else $('#content').innerHTML=n?workbench(s.db,r,n):'<button data-action="add-step">Add your first step</button>';
  $('#content').scrollTop=scroll;
}
async function guarded(fn) {
  try {await fn();}catch(e){notice(e.message);}
}
document.addEventListener('click',e=>{
  const target=e.target.closest('[data-action]');
  if(target)guarded(()=>action(target.dataset.action,target,ctx()));
});
document.addEventListener('submit',e=>{
  e.preventDefault();guarded(()=>submitForm(e.target,ctx()));
});
document.addEventListener('change',e=>{
  if(['restore-file','profile-file'].includes(e.target.id)) {
    const file=e.target.files[0],kind=e.target.id==='profile-file'?'profiles':'backup';
    guarded(()=>importFile(file,kind,ctx()));e.target.value='';return;
  }
  if(e.target.matches('#project-select,#run-select,#show-archived,[data-profile],[data-check]'))guarded(()=>changed(e.target,ctx()));
});
document.addEventListener('input',e=>{
  if(!e.target.dataset.draft||s.conflict)return;
  const {run,node}=selection();run.drafts[node.id]??={};
  run.drafts[node.id][e.target.dataset.draft]=e.target.value;save();
});
window.addEventListener('storage',e=>{
  if(e.key===KEY){s.conflict=true;notice('Another tab changed the draft. Export your copy, then reload before editing.');}
});
$('#close-dialog').onclick=()=>$('#create-dialog').close();
try{Object.assign(s,await bootstrap());render();if(s.warning)notice(s.warning);}
catch(e){notice(e.message);}
