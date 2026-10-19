import {newThread,freshId,parse,serialize,archiveRun,currentState,reconcile,activeIntent,activeAgent,validate,assertPublic} from './thread.mjs';
import {sentMove,amendValues,agentChange,ownerForm,agentForm,sentForm} from './editor.mjs';
import {packet as packetTemplate,threadsMarkup} from './screens.mjs';
import {makeReply,replyLabel,openAgents} from './reply.mjs';
import {makeSeal,sealForm} from './seal.mjs';
import {moveMarkup} from './move-view.mjs';
import {askInline} from '../inline-question.mjs';
const packet=(id,kind,body)=>packetTemplate(id,kind,body,intent());
import {localThreads,persist,chatLink,readRemote,prepareSave,exportThread} from './save.mjs';
const NLM='NN-20261018-171656-66d2';
const state={threads:localThreads(),active:null,view:'threads',draft:null,editor:null,checks:{},lastReply:'',message:''};
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
function renderThreads(){ $('#panel').innerHTML=threadsMarkup(state.threads); }
function renderThread() {
  const x=t(),i=intent(),last=x.moves.at(-1),hold=!!i.hold;
  const older=x.moves.slice(0,-1);
  $('#panel').innerHTML='<div class="heading"><button data-action="back">← Threads</button><h2>'+esc(x.title)+'</h2>'+
    '<button data-action="export">Export Markdown</button></div>'+
    '<section class="intent"><strong>📌 Owner Intent</strong><p>'+esc(i.goal||'UNKNOWN')+'</p>'+
    '<p><strong>Done-when:</strong> '+(i.doneWhen.length?i.doneWhen.map((c,j)=>(j+1)+'. '+esc(c)).join(' · '):'UNKNOWN — Owner must define')+'</p>'+
    '<p><strong>Scope:</strong> '+esc(i.inScope||'UNKNOWN')+' · <strong>Out:</strong> '+esc(i.outScope||'UNKNOWN')+'</p>'+
    '<p><strong>Agent:</strong> '+esc(activeAgent(x)||'UNKNOWN')+' · <strong>Open agents:</strong> '+esc(openAgents(x).join(' · '))+' · <strong>Owner constraint:</strong> '+esc(i.hold||'None')+'</p>'+ 
    '<button data-action="owner-edit">Owner: amend intent / checks / HOLD</button> '+
    '<button data-action="agent-edit">Change agent</button></section><section id="editor"></section>'+ 
    '<details><summary>Earlier moves ('+older.length+')</summary>'+older.map(m=>moveMarkup(x,m,esc)).join('')+'</details>'+ 
    '<section class="current"><h3>Current move · '+esc(currentState(x))+'</h3>'+
    (last?moveMarkup(x,last,esc):'<p>No nudge sent yet.</p>')+
    (hold?'<p class="hold">HOLD: '+esc(i.hold)+' — no further packets may be sent until the Owner changes this constraint.</p>':
      '<div class="actions"><button data-action="compose-ground">Ground</button>'+
      '<button data-action="compose-task">Task</button>'+
      '<button data-action="compose-correction">Correction</button><button data-action="review">Close via Reconcile</button>'+
      '<button data-action="review">Reconcile</button></div>')+
    '<label>Private chat link (device only) <input id="chat" type="url" placeholder="https://..." value="'+esc(chatLink(x.id))+'"></label>'+
    '<button data-action="save-chat">Keep link on device</button>'+
    '<label>Paste agent reply or return line <textarea id="reply" rows="10" maxlength="90000" placeholder="ACK ... SAVED ..."></textarea></label>'+ 
    '<label>Public evidence URL (optional) <input id="evidence" placeholder="https://github.com/..."></label>'+
    '<label>Result label<select id="reply-label">'+['UNKNOWN','INDEPENDENT','SELF-ASSESSED','NOT BLIND'].map(v=>'<option>'+v+'</option>').join('')+'</select></label>'+ 
    '<button data-action="record-reply">Record return digest</button> '+
    '<button data-action="seal-open">Sealed note</button><section id="seal-host"></section>'+ 
    '<label>Free-form dated note (no reopening gate) <input id="note" placeholder="Short note"></label>'+
    '<button data-action="note">Add note</button></section>'+
    '<section id="composer"></section>'+
    '<section class="save"><button data-action="github-save">One-click GitHub save · append only</button>'+
    '<a id="save-link" target="_blank" rel="noopener noreferrer" hidden>Open prepared save issue</a>'+
    '<button data-action="reload">Compare with GitHub</button>'+
    '<p>Owner-only issue submission, expected SHA, rejected saves keep this draft.</p></section>';
  if(state.editor==='owner')$('#editor').innerHTML=ownerForm(i);
  if(state.editor==='agent')$('#editor').innerHTML=agentForm(activeAgent(x));
  if(state.editor==='seal')$('#seal-host').innerHTML=sealForm(x,esc);
  if(state.draft)renderComposer();
}
function renderComposer() {
  const d=state.draft;if(!d)return;
  $('#composer').innerHTML='<h3>Draft '+esc(d.kind)+' · '+esc(d.id)+'</h3>'+
    '<p>Based on <a target="_blank" rel="noopener noreferrer" href="https://github.com/reallakshman19/Common/tree/2ce2a2aa/skills/nudge-designer">Nudge Designer @2ce2a2aa</a>.</p>'+
    '<label>Exact packet to copy / edit<textarea id="packet" rows="14">'+esc(d.packet)+'</textarea></label>'+
    '<p class="small">Pre-send: one task · intent quoted · observable result · ACK return line · unknowns allowed.</p>'+
    '<button data-action="copy-packet">Copy exact packet</button> '+
    '<button data-action="record-sent">Record manually sent packet</button>'+
    '<label>Manual copy fallback<textarea id="fallback" readonly hidden rows="8"></textarea></label>';
  if(state.editor==='send')$('#composer').insertAdjacentHTML('beforeend',sentForm(activeAgent(t())));
}
function renderReview() {
  const x=t(),i=intent(),reply=[...x.moves].reverse().find(m=>m.kind==='reply');
  $('#panel').innerHTML='<div class="heading"><button data-action="thread">← Thread</button><h2>Reconcile</h2></div>'+
    '<section class="intent"><strong>Owner outcome</strong><p>'+esc(i.goal)+'</p>'+
    '<p>Task COMPLETE never accepts this outcome.</p></section>'+
    '<div class="review-grid"><section><h3>Agent claim and evidence</h3><pre>'+esc(reply?.returnLine||'No reply yet')+'</pre>'+
    '<p>Assessment: '+esc(replyLabel(reply||{}))+'</p><p>'+esc(reply?.digest||'UNKNOWN')+'</p><p>'+esc(reply?.evidence||'Evidence UNKNOWN')+'</p>'+ 
    '<label>Observed gap or needed evidence<textarea id="gap">'+esc(state.reviewGap||'')+'</textarea></label></section>'+
    '<section><h3>Owner done-when (independent of task)</h3>'+
    (i.doneWhen.length?i.doneWhen.map((q,j)=>'<label>'+esc(q)+'<select class="check" data-check="'+j+'">'+
      ['unknown','met','not met'].map(v=>'<option value="'+v+'"'+((state.checks[j]||'unknown')===v?' selected':'')+'>'+v+'</option>').join('')+'</select></label>').join(''):
      '<p>UNKNOWN: Owner has not confirmed done-when. Do not infer or close.</p>')+
    '<label>Next decision<select id="decision">'+['request evidence','correct','continue','change direction','close'].map(v=>'<option>'+v+'</option>').join('')+'</select></label>'+
    '<button data-action="draft-decision">Draft next nudge</button></section></div>'+
    '<p>Compare claim to original sources. Check input encoding and interpretation before blaming an agent. Distinguish drift, new issue and assumption conflict. A hash or receipt is not acceptance.</p>'+
    '<section id="composer"></section>';
  if(state.draft)renderComposer();
}
function render() {
  $('#notice').textContent=state.message;
  if(state.view==='threads')renderThreads();
  else if(state.view==='thread')renderThread();
  else renderReview();
}
function append(move) {const x=t();x.moves.push(move);put(x);state.draft=null;state.editor=null;render();}
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
  const x=t(),i=x?intent():null;
  if(action==='back'){state.view='threads';state.draft=null;state.editor=null;return render();}
  if(action==='thread'){state.view='thread';state.draft=null;state.editor=null;return render();}
  if(action==='export')return exportThread(x);
  if(action==='archive-list')return archiveList();
  if(action==='load-id') {
    const input=await askInline({title:'Load thread',label:'NextNudge thread ID',accept:'Load'});
    if(!input.ok)return;const id=input.value;
    const remote=await readRemote(id);if(!remote.thread)throw Error('Not found');
    if(state.threads[id]&&!(await askInline({title:'Replace local thread',message:'Replace this device draft with the GitHub version?',accept:'Replace'})).ok)return;
    put(remote.thread);state.view='thread';return render();
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
  if(action.startsWith('compose-')) {
    if(action==='compose-close'){state.view='review';state.draft=null;return render();}
    if(i.hold)throw Error('Owner HOLD prevents new packet');
    const kind=action.slice(8),id=freshId();
    state.draft={id,kind,packet:packet(id,kind,'Write one observable deliverable; name the source and return proof.')};
    state.editor=null;render();return;
  }
  if(action==='review'){state.view='review';state.draft=null;state.editor=null;return render();}
  if(action==='draft-decision'){
    if(i.hold)throw Error('Owner HOLD');
    const checks=[...document.querySelectorAll('.check')].map(q=>q.value),decision=v('decision');
    state.checks=checks; // Retain selections when the proposed packet re-renders Reconcile.
    const id=freshId(),r=[...x.moves].reverse().find(m=>m.kind==='reply');
    state.reviewGap=v('gap');
    state.draft={id,...reconcile({checks,decision,reply:r?.returnLine||'UNKNOWN',gap:state.reviewGap,
      nudgeId:id,goal:i.goal,criteria:i.doneWhen,agent:activeAgent(x)}),requiresTask:true};
    render();return;
  }
  if(action==='copy-packet'||action==='record-sent'){
    if(i.hold)throw Error('Owner HOLD');
    const text=v('packet')||state.draft?.packet;
    if(!text)throw Error('No packet');assertPublic(text);state.draft.packet=text;
    if(action==='copy-packet'){
      try{await navigator.clipboard.writeText(text);notice('Packet copied. Copy does not imply sending.');}
      catch {$('#fallback').hidden=false;$('#fallback').value=text;$('#fallback').select();notice('Clipboard denied; use selected manual-copy text.');}
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
  const target=e.target.closest('[data-action],[data-open],[data-convert]');if(!target)return;
  const action=target.dataset.action|| (target.dataset.open?'open':'convert');
  if(action==='open'){state.active=target.dataset.open;state.view='thread';state.draft=null;render();return;}
  onAction(action,target).catch(err=>notice(err.message));
});
document.addEventListener('submit',async e=>{
  const form=e.target;if(!['new-thread','owner-amend','agent-change','sent-confirm','seal-form'].includes(form.id))return;
  e.preventDefault();
  try{
    const values=new FormData(form);
    if(form.id==='new-thread'){
      const x=newThread({title:values.get('title').trim(),goal:values.get('goal').trim(),agent:values.get('agent').trim()});
      put(x);state.view='thread';render();return;
    }
    if(form.id==='owner-amend'){
      if(values.get('approved')!=='on')throw Error('Explicit Owner confirmation required');
      const next=amendValues(Object.fromEntries(values));
      const m=emptyMove(freshId(),'amendment');m.note='OWNER_INTENT_CHANGE:'+JSON.stringify(next);
      append(m);return;
    }
    if(form.id==='agent-change'){
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
  try{const x=parse(await file.text());put(x);state.view='thread';render();}
  catch(err){notice(err.message);}e.target.value='';
});
async function init(){
  if(!state.threads[NLM]){
    try{const r=await fetch('../nextnudge-data/threads/'+NLM+'.md');
      if(r.ok){const seed=parse(await r.text());put(seed);}}catch{}
  }
  state.view='threads';render();
}
init();
