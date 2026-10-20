import {newThread,freshId,parse,serialize,archiveRun,currentState,activeIntent,activeAgent,validate,assertPublic} from './thread.mjs';
import {sentMove,amendValues,agentChange,ownerForm,agentForm,sentForm} from './editor.mjs';
import {threadsMarkup,projectsMarkup,projectMarkup} from './screens.mjs';
import {newProject,addThread,updateFixtures} from './project-model.mjs';
import {localProjects,persistProject,projectForThread,projectSha,recordProjectSha,readRemoteProject,discoverProjects,prepareProjectSave} from './project-store.mjs';
import {groundingPanel,readGrounding,projectGroundingText} from './grounding.mjs';
import {makeReply,openAgents} from './reply.mjs';
import {makeSeal,sealForm} from './seal.mjs';
import {moveMarkup} from './move-view.mjs';
import {askInline} from '../inline-question.mjs';
import {localThreads,persist,persistMove,chatLink,readRemote,prepareSave,exportThread} from './save.mjs';
import {featureAction,installFeatures,renderGrounding,restoreDraft,composerExtras,returnControls} from './features.mjs';
import {clearComposer} from './composer.mjs';
import {workspaceNav,MODES} from './workspace-nav.mjs';
import {workspaceAction,installWorkspaces,workspaceMarkup,openWorkspace,checkWorkspacePacket,clearSentWorkspace} from './workspace-ui.mjs';
const NLM='NN-20261018-171656-66d2';
const state={threads:localThreads(),projects:localProjects(),active:null,activeProject:null,view:'projects',draft:null,editor:null,checks:{},lastReply:'',message:''};
const $=q=>document.querySelector(q);
const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const v=id=>$('#'+id)?.value||'';
const t=()=>state.threads[state.active];
const intent=()=>activeIntent(t());
const notice=s=>{state.message=s;$('#notice').textContent=s;};
const emptyMove=(id,kind)=>({id,kind,delivery:'draft',packet:'',returnLine:'',digest:'',
  evidence:'',gap:'',decision:'',archive:'',note:''});
function put(thread) {
  validate(thread);state.threads[thread.id]=thread;persist(thread);state.active=thread.id;
}
function activeProject(){return state.projects[state.activeProject]||null;}
function putProject(project){
  persistProject(project);state.projects[project.id]=project;state.activeProject=project.id;
}
function projectForActive(){
  return state.active?projectForThread(state.active,state.projects):null;
}
const projectDraftKey='nextnudge.project.grounding.drafts.v1';
function projectDrafts(){try{return JSON.parse(localStorage.getItem(projectDraftKey)||'{}');}catch{return {};}}
function groundingFormValues(form){
  return Object.fromEntries([...new FormData(form)].filter(([key])=>key.startsWith('ground-'))
    .map(([key,value])=>[key.slice(7),value]));
}
function renderProjects(){ $('#panel').innerHTML=projectsMarkup(state.projects,state.threads); }
function renderProject(){const p=activeProject();if(!p){state.view='projects';return renderProjects();}
  $('#panel').innerHTML=projectMarkup(p,state.threads,state.projects);}
function renderProjectGrounding(){
  const p=activeProject();if(!p)throw Error('Select a project first');
  const draft=projectDrafts()[p.id],saved=p.fixtures;
  const keys=new Set([...Object.keys(draft||{}),...Object.keys(saved)]);
  const isDiff=!!draft&&[...keys].some(k=>String(draft[k]||'').trim()!==(saved[k]||''));
  $('#panel').innerHTML=groundingPanel(null,draft||saved,isDiff,p);
}
function renderLegacyGrounding(){
  const x=t(),history=x.moves.filter(m=>m.note?.startsWith('GROUNDING_FIXTURES_V1:'));
  $('#panel').innerHTML='<div class="heading"><button data-action="thread">← Thread</button><h2>Historical Grounding Fixtures · read-only</h2></div>'+
    '<p>This unassigned legacy thread has no project library. Select a project and explicitly attach the thread to edit shared fixtures. No historical grounding was merged.</p>'+
    history.map(m=>'<details><summary>'+esc(m.id)+' · saved historical snapshot</summary><pre>'+
      esc(JSON.stringify(JSON.parse(m.note.slice('GROUNDING_FIXTURES_V1:'.length)),null,2))+'</pre></details>').join('');
}
function renderThreads(){ $('#panel').innerHTML=threadsMarkup(state.threads); }
function renderThread() {
  const x=t(),i=intent(),last=x.moves.at(-1),hold=!!i.hold;
  if(!state.draft){const saved=restoreDraft(x);if(saved&&!x.moves.some(m=>m.id===saved.id))state.draft=saved;}
  const older=x.moves.slice(0,-1);
  $('#panel').innerHTML='<div class="heading"><button data-action="back">← '+(state.activeProject?'Project':'Projects')+'</button><h2>'+esc(x.title)+'</h2>'+
    '<button data-action="export">Export Markdown</button></div>'+
    workspaceNav('overview')+
    '<section class="intent"><strong>📌 Owner Intent</strong><p class="intent-goal">'+esc(i.goal||'UNKNOWN')+'</p>'+
    '<p class="intent-meta"><strong>Agent:</strong> '+esc(activeAgent(x)||'UNKNOWN')+(i.hold?' · <span class="hold-badge"><strong>HOLD:</strong> '+esc(i.hold)+'</span>':' · <strong>Owner constraint:</strong> None')+(openAgents(x).length>1?' · <small>Open agents: '+esc(openAgents(x).join(' · '))+'</small>':'')+'</p>'+
    '<details class="intent-details"><summary>Scope and done-when details ('+(i.doneWhen.length?i.doneWhen.length+' criteria':'not set')+')</summary>'+
    '<p><strong>Done-when:</strong> '+(i.doneWhen.length?i.doneWhen.map((c,j)=>(j+1)+'. '+esc(c)).join(' · '):'UNKNOWN — Owner must define')+'</p>'+
    '<p><strong>Scope:</strong> '+esc(i.inScope||'UNKNOWN')+' · <strong>Out:</strong> '+esc(i.outScope||'UNKNOWN')+'</p></details>'+
    '<div><button data-action="owner-edit">Owner: amend intent / checks / HOLD</button> '+
    (state.activeProject?'<span class="small">Project agent identity fixed; create another agent thread to transfer work.</span>':'<button data-action="agent-edit">Change agent</button>')+'</div></section><section id="editor"></section>'+ 
    '<details><summary>Earlier moves ('+older.length+')</summary>'+older.map(m=>moveMarkup(x,m,esc)).join('')+'</details>'+ 
    '<details><summary>Historical thread grounding ('+x.moves.filter(m=>m.note?.startsWith('GROUNDING_FIXTURES_V1:')).length+' snapshots) · read-only</summary>'+
    x.moves.filter(m=>m.note?.startsWith('GROUNDING_FIXTURES_V1:')).map(m=>'<details><summary>'+esc(m.id)+'</summary><pre>'+
      esc(JSON.stringify(JSON.parse(m.note.slice('GROUNDING_FIXTURES_V1:'.length)),null,2))+'</pre></details>').join('')+
    '</details>'+
    '<section class="current"><h3>Current move · '+esc(currentState(x))+'</h3>'+
    (last?moveMarkup(x,last,esc):'<p>No nudge sent yet.</p>')+
    (hold?'<div class="hold" role="alert"><strong>⛔ OWNER HOLD ACTIVE:</strong> '+esc(i.hold)+' — sending instructions is blocked until the Owner amends or removes this constraint.</div>':
      '<div class="actions"><button data-action="compose-task" class="primary">Task</button>'+
      '<button data-action="compose-ground">Ground</button>'+
      '<button data-action="compose-correction">Correction</button>'+
      '<button data-action="review" title="Close via Reconcile">Reconcile</button></div>')+
    '<section id="composer"></section>'+
    returnControls(x)+
    '<details class="fallback-reply"><summary>Manual reply entry (fallback if not using GitHub return)</summary>'+
    '<label>Paste agent reply or return line <textarea id="reply" rows="6" maxlength="90000" placeholder="ACK ... SAVED ..."></textarea></label>'+ 
    '<label>Public evidence URL (optional) <input id="evidence" placeholder="https://github.com/..."></label>'+
    '<label>Result label<select id="reply-label">'+['UNKNOWN','INDEPENDENT','SELF-ASSESSED','NOT BLIND'].map(v=>'<option>'+v+'</option>').join('')+'</select></label>'+ 
    '<button data-action="record-reply">Record return digest</button></details>'+
    '<details class="thread-utilities"'+(state.editor==='seal'?' open':'')+'><summary>Utilities & Notes (private chat, dated note, sealed note)</summary>'+
    '<label>Private chat link (device only) <input id="chat" type="url" placeholder="https://..." value="'+esc(chatLink(x.id))+'"></label>'+
    '<button data-action="save-chat">Keep link on device</button>'+
    '<label>Free-form dated note (no reopening gate) <input id="note" placeholder="Short note"></label>'+
    '<button data-action="note">Add note</button> '+
    '<button data-action="seal-open">Sealed note</button><section id="seal-host"></section></details></section>'+
    '<section class="save"><button data-action="github-save" class="primary">One-click GitHub save · append only</button>'+
    '<a id="save-link" target="_blank" rel="noopener noreferrer" hidden>Open prepared save issue</a>'+
    '<button data-action="reload">Compare with GitHub</button>'+
    '<p>Owner-only issue submission, expected SHA, rejected saves keep this draft.</p></section>';
  if(state.editor==='owner')$('#editor').innerHTML=ownerForm(i);
  if(state.editor==='agent')$('#editor').innerHTML=agentForm(activeAgent(x));
  if(state.editor==='seal'){
    const host=$('#seal-host');if(host){
      host.innerHTML=sealForm(x,esc);
      const target=host.querySelector('textarea,select');if(target){target.focus();
        target.scrollIntoView({behavior:window.matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth',block:'nearest'});}
    }
  }
  if(state.draft?.workspaceMode){
    $('#composer').innerHTML='<button data-action="workspace-'+esc(state.draft.workspaceMode)+'">Resume '+esc(state.draft.workspaceMode)+' packet in its workspace</button>';
  }else if(state.draft)renderComposer();
}
function renderComposer() {
  const d=state.draft;if(!d)return;
  $('#composer').innerHTML='<h3>Draft '+esc(d.kind)+' · '+esc(d.id)+'</h3>'+
    '<p>Guidance: <a target="_blank" rel="noopener noreferrer" href="https://github.com/reallakshman19/Common/tree/main/skills/agent-work">current agent-work</a>. Follow the project’s selected standalone protocol and record the revision read.</p>'+
    '<label>Exact packet to copy / edit<textarea id="packet" rows="14">'+esc(d.packet)+'</textarea></label>'+
    '<p class="small">Pre-send: one task · intent quoted · observable result · ACK return line · unknowns allowed.</p>'+
    '<div class="composer-actions"><button data-action="copy-packet" class="primary">Copy exact packet</button> '+
    '<button data-action="record-sent">Record manually sent packet</button> '+
    '<span id="packet-status" class="packet-status" role="status" aria-live="polite"></span></div>'+
    '<label id="fallback-box" hidden>Manual copy fallback<textarea id="fallback" readonly hidden rows="8"></textarea></label>'+composerExtras(t(),d);
  if(state.editor==='send')$('#composer').insertAdjacentHTML('beforeend',sentForm(activeAgent(t())));
}
function render() {
  $('#notice').textContent=state.message;
  if(state.view==='projects')renderProjects();
  else if(state.view==='project')renderProject();
  else if(state.view==='project-grounding')renderProjectGrounding();
  else if(state.view==='legacy-grounding')renderLegacyGrounding();
  else if(state.view==='threads')renderThreads();
  else if(state.view==='grounding')$('#panel').innerHTML=renderGrounding(t());
  else if(state.view==='thread')renderThread();
  else if(state.view==='workspace'){
    $('#panel').innerHTML=workspaceMarkup({state,t});
    if(state.draft)renderComposer();
  }
}
function append(move) {
  const x=persistMove(t(),move);
  state.threads[x.id]=x;state.active=x.id;
  if(move.delivery==='sent'){
    try{clearSentWorkspace({state,t},move);clearComposer(x.id);}
    catch(e){state.message='Sent history saved; old device packet backup retained: '+e.message;}
  }
  state.draft=null;state.editor=null;render();
}
async function archiveList() {
  const response=await fetch('../nextnudge-data/workbench.json',{cache:'no-store'});
  if(!response.ok)throw Error('Archive unavailable');
  const db=await response.json();
  $('#archive-runs').innerHTML=db.runs.map(r=>'<details><summary>'+esc(r.title)+
    '</summary><p><strong>Historical aim:</strong> '+esc(r.aim)+'</p>'+
    '<p>These statuses are historical claims, not proof of Owner acceptance.</p>'+
    '<ol>'+r.nodes.map(n=>'<li><strong>'+esc(n.label)+'</strong> · historical '+esc(n.status)+
    ' · '+esc((n.messages?.[0]?.text||'No reply').slice(0,300))+'</li>').join('')+'</ol>'+
    '<button data-convert="'+esc(r.id)+'">Convert summary to a thread</button></details>').join('');
}
async function convert(id) {
  const response=await fetch('../nextnudge-data/workbench.json',{cache:'no-store'});
  const db=await response.json(),run=db.runs.find(r=>r.id===id);
  if(!run)throw Error('Archived run not found');
  if(state.threads[id]&&!(await askInline({title:'Replace converted thread',message:'This replaces your local draft.',accept:'Replace'})).ok)return;
  const x=archiveRun(run);
  put(x);state.view='thread';render();
}
async function onAction(action,target) {
  if(await workspaceAction(action,{state,t,append,render,notice}))return;
  if(await featureAction(action,{state,t,append,render,notice}))return;
  const x=t(),i=x?intent():null;
  if(action==='projects'){state.view='projects';state.activeProject=null;state.draft=null;return render();}
  if(action==='project'){state.view='project';state.draft=null;return render();}
  if(action==='project-grounding'){state.view='project-grounding';state.draft=null;return render();}
  if(action==='back'){state.view=state.activeProject?'project':'projects';state.draft=null;state.editor=null;return render();}
  if(action==='copy-project-grounding'){
    const p=activeProject(),text=projectGroundingText(p,groundingFormValues($('#project-grounding-form')));
    try{await navigator.clipboard.writeText(text);notice('Project grounding copied. Copy does not send.');}
    catch{const box=document.createElement('textarea');box.value=text;box.readOnly=true;
      $('#project-grounding-form').appendChild(box);box.select();notice('Clipboard denied; selected manual copy text.');}
    return;
  }
  if(action==='project-save'){
    const p=activeProject();if(!p)throw Error('Select a project');
    const win=window.open('about:blank','_blank');
    try{const prepared=await prepareProjectSave(p);
      if(win){win.opener=null;win.location.replace(prepared.url);}
      else{const a=document.createElement('a');a.href=prepared.url;a.target='_blank';a.rel='noopener noreferrer';
        a.textContent='Open prepared project save';$('#panel').append(a);}
      notice('Owner review request prepared ('+prepared.chars+' URL characters). Device draft retained until confirmed GitHub readback.');
    }catch(e){win?.close();throw e;}
    return;
  }
  if(action==='project-reload'){
    const p=activeProject(),remote=await readRemoteProject(p.id);
    if(!remote.project)return notice('Project not yet on GitHub. Device draft retained.');
    if(!(await askInline({title:'GitHub project readback',message:'Replace local project draft with the GitHub version? Unsaved local changes must be exported or recovered separately.',accept:'Replace'})).ok)return;
    putProject(remote.project);recordProjectSha(p.id,remote.sha);
    state.view='project';notice('GitHub project readback verified at SHA '+remote.sha.slice(0,10)+'.');return render();
  }
  if(action==='thread'){state.view='thread';state.draft=null;state.editor=null;return render();}
  if(action==='export')return exportThread(x);
  if(action==='archive-list')return archiveList();
  if(action==='load-id') {
    const input=await askInline({title:'Load thread',label:'NextNudge thread ID',accept:'Load'});
    if(!input.ok)return;const id=input.value;
    const remote=await readRemote(id);if(!remote.thread)throw Error('Not found');
    if(state.threads[id]&&!(await askInline({title:'Replace local thread',message:'Replace this device draft with the GitHub version?',accept:'Replace'})).ok)return;
    put(remote.thread);state.activeProject=projectForThread(id,state.projects)?.id||null;
    state.view='thread';return render();
  }
  if(action==='import')return $('#import-file').click();
  if(action==='save-chat'){chatLink(x.id,v('chat'));return notice('Private chat link kept on this device only.');}
  if(action==='convert')return convert(target.dataset.convert);
  if(action==='owner-edit'||action==='agent-edit') {
    state.editor=action==='owner-edit'?'owner':'agent';render();return;
  }
  if(action==='cancel-edit'){state.editor=null;return render();}
  if(action==='seal-open'){state.editor='seal';return render();}
  if(action==='note') {if(!v('note').trim())throw Error('Enter a note');
    const m=emptyMove(freshId(),'amendment');m.note=new Date().toISOString().slice(0,10)+': '+v('note');append(m);return;}
  if(action==='record-reply'){
    const text=v('reply'),evidence=v('evidence');
    if(evidence&&!/^https:\/\/github\.com\//.test(evidence))throw Error('Only public GitHub evidence links can be persisted');
    const {move,warnings}=makeReply(x,text,{label:v('reply-label')||'UNKNOWN',evidence});
    append(move);if(warnings.length)notice(warnings.join('; '));return;
  }
  if(action==='copy-packet'||action==='record-sent'){
    if(i.hold)throw Error('Owner HOLD');
    const text=v('packet')||state.draft?.packet;
    if(!text)throw Error('No packet');assertPublic(text);state.draft.packet=text;
    if(action==='copy-packet'){
      const setPacketStatus=s=>{const el=$('#packet-status');if(el)el.textContent=s;};
      try{
        await navigator.clipboard.writeText(text);
        setPacketStatus('Packet copied. Copy does not send.');notice('Exact packet copied to clipboard. Copy does not imply sending.');
      }catch{
        const fb=$('#fallback'),box=$('#fallback-box');if(box)box.hidden=false;
        if(fb){fb.hidden=false;fb.value=text;fb.focus();fb.select();}
        setPacketStatus('Clipboard denied; use selected manual fallback below.');notice('Clipboard denied; use selected manual-copy text below.');
      }
      return;
    }
    state.editor='send';renderComposer();return;
  }
  if(action==='github-save') {
    // Open within the click before async fetch; never clear local state until verified.
    const win=window.open('about:blank','_blank');
    try{
      const out=await prepareSave(x);
      if(win){win.opener=null;win.location.replace(out.url);}
      else {const a=$('#save-link');a.href=out.url;a.hidden=false;}
      notice('Review and submit Owner save issue ('+out.chars+' URL characters). Draft retained until GitHub verifies it.');
    }catch(e){win?.close();throw e;}
    return;
  }
  if(action==='reload') {
    const result=await readRemote(x.id);
    if(!result.thread)return notice('No GitHub file yet. Local draft retained.');
    if(!(await askInline({title:'Reload from GitHub',message:'Replace local draft with GitHub content?',accept:'Replace'})).ok)return;
    put(result.thread);return render();
  }
}
document.addEventListener('click',e=>{
  const target=e.target.closest('[data-action],[data-open],[data-convert],[data-project]');if(!target)return;
  const action=target.dataset.action|| (target.dataset.open?'open':target.dataset.project?'project-select':'convert');
  if(action==='open'){
    const id=target.dataset.open;
    (async()=>{if(!state.threads[id]){const remote=await readRemote(id);if(!remote.thread)throw Error('Thread not found on GitHub');put(remote.thread);}
      state.active=id;state.activeProject=projectForThread(id,state.projects)?.id||null;
      state.view='thread';state.draft=null;render();})().catch(err=>notice(err.message));return;
  }
  if(target.dataset.project){state.activeProject=target.dataset.project;state.view='project';state.draft=null;render();return;}
  onAction(action,target).catch(err=>notice(err.message));
});
document.addEventListener('input',event=>{
  if(!event.target.closest?.('#project-grounding-form'))return;
  try{
    const rows=projectDrafts();rows[state.activeProject]=groundingFormValues($('#project-grounding-form'));
    localStorage.setItem(projectDraftKey,JSON.stringify(rows));
    const status=$('.grounding-status');if(status)status.textContent='Unsaved device draft';
  }catch(e){notice('Project grounding draft storage failed: '+e.message+'. Copy before leaving.');}
});
document.addEventListener('submit',async e=>{
  const form=e.target;if(!['new-project','new-thread','attach-thread','project-grounding-form','owner-amend','agent-change','sent-confirm','seal-form'].includes(form.id))return;
  e.preventDefault();
  try{
    const values=new FormData(form);
    if(form.id==='new-project'){
      const p=newProject(values.get('name').trim());putProject(p);state.view='project';render();return;
    }
    if(form.id==='project-grounding-form'){
      const p=activeProject(),next=updateFixtures(p,groundingFormValues(form));
      if(next)putProject(next);
      const rows=projectDrafts();delete rows[p.id];
      try{localStorage.setItem(projectDraftKey,JSON.stringify(rows));}catch{}
      render();notice(next?'Project grounding saved locally as one version. Save project to GitHub for sharing.':'Project grounding unchanged; no history added.');return;
    }
    if(form.id==='attach-thread'){
      const id=values.get('thread'),thread=state.threads[id],p=activeProject();
      if(!thread)throw Error('Thread is not on this device; load it first');
      if(projectForThread(id,state.projects))throw Error('Thread already belongs to a project');
      putProject(addThread(p,{id,agent:activeAgent(thread)||'UNKNOWN'},{legacy:true}));
      state.view='project';render();return;
    }
    if(form.id==='new-thread'){
      const x=newThread({title:values.get('title').trim(),goal:values.get('goal').trim(),agent:values.get('agent').trim()});
      if(state.view==='project'){
        const p=activeProject();
        if(!p)throw Error('Select a project');
        const next=addThread(p,x);
        put(x);putProject(next);
      }else{put(x);state.activeProject=null;}
      state.view='thread';render();return;
    }
    if(form.id==='owner-amend'){
      if(values.get('approved')!=='on')throw Error('Explicit Owner confirmation required');
      const next=amendValues(Object.fromEntries(values));
      const m=emptyMove(freshId(),'amendment');m.note='OWNER_INTENT_CHANGE:'+JSON.stringify(next);
      append(m);return;
    }
    if(form.id==='agent-change'){
      if(projectForActive())throw Error('Project thread identity is fixed. Create/select the other agent thread; existing history is preserved.');
      const m=agentChange(values.get('agent'));
      chatLink(t().id,'');append(m);
      notice('Agent changed. Add the new private chat link for this agent.');return;
    }
    if(form.id==='seal-form'){
      const move=await makeSeal(t(),{text:values.get('text'),names:values.get('names')});
      append(move);return;
    }
    if(form.id==='sent-confirm'){
      if(values.get('approved')!=='on')throw Error('Explicit Owner confirmation required');
      if(intent().hold)throw Error('Owner HOLD prevents sending');
      checkWorkspacePacket({state,t});
      const text=v('packet')||state.draft?.packet;
      assertPublic(text);
      const move=sentMove(t(),state.draft,text,{role:values.get('role')||'worker',
        agent:values.get('agent')||activeAgent(t()),override_note:values.get('override_note')||''});
      const i=intent();
      if(move.kind==='close'){
        const proof=state.draft.closure;
        if(!proof||!i.doneWhen.length||JSON.stringify(proof.criteria)!==JSON.stringify(i.doneWhen)||
          proof.checks.length!==i.doneWhen.length||!proof.checks.every(c=>c==='met'))
          throw Error('Close requires Reconcile with every Owner done-when Met');
      }
      append(move);
    }
  }catch(err){notice(err.message);}
});
$('#import-file').addEventListener('change',async e=>{
  const file=e.target.files?.[0];if(!file)return;
  try{const x=parse(await file.text());put(x);state.activeProject=projectForThread(x.id,state.projects)?.id||null;state.view='thread';render();}
  catch(err){notice(err.message);}e.target.value='';
});
async function init(){
  try{
    const found=await discoverProjects();state.projects=localProjects();
    if(found.conflicts)state.message=found.conflicts+' project GitHub revisions differ from device drafts; compare before writing.';
  }catch(e){state.message='Project GitHub discovery unavailable: '+e.message+'. Device drafts retained.';}
  if(!state.threads[NLM]){
    try{const r=await fetch('../nextnudge-data/threads/'+NLM+'.md');
      if(r.ok){const seed=parse(await r.text());put(seed);}}catch{}
  }
  const requested=new URLSearchParams(window.location.search).get('thread');
  if(requested){
    try{if(!state.threads[requested]){const remote=await readRemote(requested);if(remote.thread)put(remote.thread);}
      if(state.threads[requested]){
        state.active=requested;
        try{state.activeProject=projectForThread(requested,state.projects)?.id||null;}
        catch(e){state.message=e.message;state.activeProject=null;}
        const mode=new URLSearchParams(window.location.search).get('workspace');
        if(MODES.includes(mode))return openWorkspace({state,t,append,render,notice},mode);
        state.view='thread';return render();
      }
    }catch(e){notice(e.message);}
  }
  state.view='projects';render();
}
installFeatures({state,t,append,render,notice});
installWorkspaces({state,t,append,render,notice});
init();
