import {newThread,freshId,parse,serialize,archiveRun,currentState,reconcile,activeIntent,validate,assertPublic} from './thread.mjs';
import {localThreads,persist,chatLink,readRemote,prepareSave,exportThread} from './save.mjs';
const NLM='NN-20261018-171656-66d2';
const state={threads:localThreads(),active:null,view:'threads',draft:null,checks:{},lastReply:'',message:''};
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
function packet(id,kind,body) {
  const i=intent();
  const common=['[Owner · NextNudge '+id+']','Owner intent: '+i.goal,
    'Owner done-when: '+(i.doneWhen.join(' | ')||'UNKNOWN — ask Owner'),
    'In scope: '+i.inScope,'Out of scope: '+i.outScope,
    'Uncertainty: report UNKNOWN; never substitute an assumption.',
    'COMPLETE describes this bounded task, not Owner-outcome acceptance.'];
  const prefix=kind==='task'?'Purpose:\n'+i.goal+'\nOne bounded task:\n'+body+
    '\nAuthoritative inputs:\nUNKNOWN\nBoundaries:\n'+i.inScope+'\nSuccess criteria:\n'+(i.doneWhen.join(' | ')||'UNKNOWN')+
    '\nUncertainty handling:\nState missing facts and blocked actions.\nEvidence and continuation:\nReturn artifacts, limits and next feasible action.':
    kind==='ground'?'Restate the Owner intent and done-when in your own words. State your first step and unknowns.\n'+body:
    kind==='correction'?'Quote the incorrect claim, identify the input interpretation, give the redo scope.\n'+body:
    kind==='close'?'The Owner outcome checks were verified. Return the final PR/file/comment pointer.\n'+body:body;
  return [...common,prefix,'Start your reply with ACK '+id+'.'].join('\n\n');
}
function renderThreads() {
  const rows=Object.values(state.threads).sort((a,b)=>b.id.localeCompare(a.id));
  $('#panel').innerHTML='<h2>Threads</h2><p>One intent, one current move. Drafts stay on this device.</p>'+
    '<form id="new-thread"><label>Intent title <input name="title" required maxlength="120"></label>'+
    '<label>Owner goal, in their words <textarea name="goal" required></textarea></label>'+
    '<label>Agent <input name="agent" placeholder="Agent or UNKNOWN"></label>'+
    '<button type="submit">Create thread</button></form>'+
    '<div class="thread-list">'+rows.map(x=>'<button data-open="'+esc(x.id)+'" class="thread-row">'+
      '<strong>'+esc(x.title)+'</strong><span>'+esc(x.agent||'UNKNOWN')+' · '+esc(currentState(x))+
      (activeIntent(x).hold?' · '+esc(activeIntent(x).hold):'')+'</span></button>').join('')+'</div>'+
    '<div class="archive"><details><summary>v2 Archive · read-only + Convert</summary>'+
    '<p>Original v2 database is retained unchanged. Historical statuses do not prove acceptance.</p>'+
    '<button data-action="archive-list">List v2 runs for conversion</button><div id="archive-runs"></div>'+
    '<p><a href="v2.html" target="_blank" rel="noopener noreferrer">Open original v2 workbench (historical interface)</a></p></details></div>'+
    '<p><button data-action="load-id">Load existing GitHub thread by ID</button> '+
    '<button data-action="import">Import Markdown thread</button></p>';
}
function renderThread() {
  const x=t(),i=intent(),last=x.moves.at(-1),hold=!!i.hold;
  const older=x.moves.slice(0,-1);
  $('#panel').innerHTML='<div class="heading"><button data-action="back">← Threads</button><h2>'+esc(x.title)+'</h2>'+
    '<button data-action="export">Export Markdown</button></div>'+
    '<section class="intent"><strong>📌 Owner Intent</strong><p>'+esc(i.goal||'UNKNOWN')+'</p>'+
    '<p><strong>Done-when:</strong> '+(i.doneWhen.length?i.doneWhen.map((c,j)=>(j+1)+'. '+esc(c)).join(' · '):'UNKNOWN — Owner must define')+'</p>'+
    '<p><strong>Scope:</strong> '+esc(i.inScope||'UNKNOWN')+' · <strong>Out:</strong> '+esc(i.outScope||'UNKNOWN')+'</p>'+
    '<p><strong>Agent:</strong> '+esc(x.agent||'UNKNOWN')+' · <strong>Owner constraint:</strong> '+esc(i.hold||'None')+'</p>'+
    '<button data-action="owner-edit">Owner: amend intent / checks / HOLD</button></section>'+
    '<details><summary>Earlier moves ('+older.length+')</summary>'+older.map(m=>'<p><strong>'+esc(m.kind)+
      '</strong> '+esc(m.id)+' · '+esc(m.returnLine||m.note||'No reply')+'</p>').join('')+'</details>'+
    '<section class="current"><h3>Current move · '+esc(currentState(x))+'</h3>'+
    (last?'<p>Last: '+esc(last.kind)+' · '+esc(last.id)+' · '+esc(last.returnLine||last.note||'Awaiting reply')+'</p>':'<p>No nudge sent yet.</p>')+
    (hold?'<p class="hold">HOLD: '+esc(i.hold)+' — no further packets may be sent until the Owner changes this constraint.</p>':
      '<div class="actions"><button data-action="compose-ground">Ground</button>'+
      '<button data-action="compose-task">Task</button>'+
      '<button data-action="compose-correction">Correction</button><button data-action="review">Close via Reconcile</button>'+
      '<button data-action="review">Reconcile</button></div>')+
    '<label>Private chat link (device only) <input id="chat" type="url" placeholder="https://..." value="'+esc(chatLink(x.id))+'"></label>'+
    '<button data-action="save-chat">Keep link on device</button>'+
    '<label>Paste agent reply or return line <textarea id="reply" rows="5" placeholder="ACK ... SAVED ..."></textarea></label>'+
    '<label>Public evidence URL (optional) <input id="evidence" placeholder="https://github.com/..."></label>'+
    '<button data-action="record-reply">Record return digest</button>'+
    '<label>Free-form dated note (no reopening gate) <input id="note" placeholder="Short note"></label>'+
    '<button data-action="note">Add note</button></section>'+
    '<section id="composer"></section>'+
    '<section class="save"><button data-action="github-save">One-click GitHub save · append only</button>'+
    '<a id="save-link" target="_blank" rel="noopener noreferrer" hidden>Open prepared save issue</a>'+
    '<button data-action="reload">Compare with GitHub</button>'+
    '<p>Owner-only issue submission, expected SHA, rejected saves keep this draft.</p></section>';
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
}
function renderReview() {
  const x=t(),i=intent(),reply=[...x.moves].reverse().find(m=>m.kind==='reply');
  $('#panel').innerHTML='<div class="heading"><button data-action="thread">← Thread</button><h2>Reconcile</h2></div>'+
    '<section class="intent"><strong>Owner outcome</strong><p>'+esc(i.goal)+'</p>'+
    '<p>Task COMPLETE never accepts this outcome.</p></section>'+
    '<div class="review-grid"><section><h3>Agent claim and evidence</h3><pre>'+esc(reply?.returnLine||'No reply yet')+'</pre>'+
    '<p>'+esc(reply?.digest||'UNKNOWN')+'</p><p>'+esc(reply?.evidence||'Evidence UNKNOWN')+'</p>'+
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
function append(move) {const x=t();x.moves.push(move);put(x);state.draft=null;render();}
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
  if(state.threads[id]&&!confirm('Replace local draft of converted run?'))return;
  const x=archiveRun(run);
  put(x);state.view='thread';render();
}
async function onAction(action,target) {
  const x=t(),i=x?intent():null;
  if(action==='back'){state.view='threads';state.draft=null;return render();}
  if(action==='thread'){state.view='thread';state.draft=null;return render();}
  if(action==='export')return exportThread(x);
  if(action==='archive-list')return archiveList();
  if(action==='load-id') {
    const id=prompt('Existing NextNudge thread ID:');if(!id)return;
    const remote=await readRemote(id);if(!remote.thread)throw Error('Not found');
    if(state.threads[id]&&!confirm('Replace local draft with GitHub version?'))return;
    put(remote.thread);state.view='thread';return render();
  }
  if(action==='import')return $('#import-file').click();
  if(action==='save-chat'){chatLink(x.id,v('chat'));return notice('Private chat link kept on this device only.');}
  if(action==='convert')return convert(target.dataset.convert);
  if(action==='owner-edit') {
    if(!confirm('Owner decision required: amend the authoritative intent?'))return;
    const goal=prompt('Owner goal',i.goal);if(goal===null)return;
    const criteria=prompt('Done-when: at most 5 checks, one per line. Blank = UNKNOWN.',i.doneWhen.join('\n'));if(criteria===null)return;
    const hold=prompt('Owner constraint / HOLD (blank to release)',i.hold);if(hold===null)return;
    const next={goal,doneWhen:criteria.split('\n').map(s=>s.trim()).filter(Boolean),
      inScope:i.inScope,outScope:i.outScope,hold};
    if(next.doneWhen.length>5)throw Error('At most five checks');
    const m=emptyMove(freshId(),'amendment');
    m.note='OWNER_INTENT_CHANGE:'+JSON.stringify(next);
    append(m);return;
  }
  if(action==='note') {if(!v('note').trim())throw Error('Enter a note');
    const m=emptyMove(freshId(),'amendment');m.note=new Date().toISOString().slice(0,10)+': '+v('note');append(m);return;}
  if(action==='record-reply'){
    const text=v('reply');if(!text.trim())throw Error('Paste a reply');
    assertPublic(text);
    const evidence=v('evidence');if(evidence&&!/^https:\/\/github\.com\//.test(evidence))throw Error('Only public GitHub evidence links can be persisted');
    const m=emptyMove(freshId(),'reply');m.returnLine=text.split(/\r?\n/).find(z=>/\bACK\b|\bSAVED\b/.test(z))?.slice(0,300)||text.split(/\r?\n/)[0].slice(0,300);
    m.digest=text.slice(0,300);m.evidence=evidence;m.note='Reply recorded against '+(x.moves.filter(m=>m.delivery==='sent').at(-1)?.id||'UNKNOWN');
    append(m);return;
  }
  if(action.startsWith('compose-')) {
    if(action==='compose-close'){state.view='review';state.draft=null;return render();}
    if(i.hold)throw Error('Owner HOLD prevents new packet');
    const kind=action.slice(8),id=freshId();
    state.draft={id,kind,packet:packet(id,kind,'Write one observable deliverable; name the source and return proof.')};
    render();return;
  }
  if(action==='review'){state.view='review';state.draft=null;return render();}
  if(action==='draft-decision'){
    if(i.hold)throw Error('Owner HOLD');
    const checks=[...document.querySelectorAll('.check')].map(q=>q.value),decision=v('decision');
    const id=freshId(),r=[...x.moves].reverse().find(m=>m.kind==='reply');
    state.reviewGap=v('gap');
    state.draft={id,...reconcile({checks,decision,reply:r?.returnLine||'UNKNOWN',gap:state.reviewGap,
      nudgeId:id,goal:i.goal,criteria:i.doneWhen,agent:x.agent})};
    render();return;
  }
  if(action==='copy-packet'||action==='record-sent'){
    if(i.hold)throw Error('Owner HOLD');const text=v('packet')||state.draft?.packet;
    if(!text)throw Error('No packet');assertPublic(text);state.draft.packet=text;
    if(action==='copy-packet'){
      try{await navigator.clipboard.writeText(text);notice('Packet copied. Copy does not imply sending.');}
      catch {$('#fallback').hidden=false;$('#fallback').value=text;$('#fallback').select();notice('Clipboard denied; use selected manual-copy text.');}
      return;
    }
    if(state.draft.kind==='close'){
      const proof=state.draft.closure;
      if(!proof||!i.doneWhen.length||JSON.stringify(proof.criteria)!==JSON.stringify(i.doneWhen)||
         proof.checks.length!==i.doneWhen.length||!proof.checks.every(c=>c==='met'))
        throw Error('Close requires Reconcile with every Owner done-when Met');
    }
    if(!confirm('Confirm you manually sent this exact packet to the agent.'))return;
    const m=emptyMove(state.draft.id,state.draft.kind);m.packet=text;m.delivery='sent';m.decision=state.draft.kind;
    if(m.kind==='close')m.note='OWNER_CLOSE_CHECKS:'+JSON.stringify(state.draft.closure);
    m.gap=state.draft.gap||'';append(m);return;
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
    if(!confirm('Replace this device draft with GitHub? Cancel to keep it.'))return;
    put(result.thread);return render();
  }
}
document.addEventListener('click',e=>{
  const target=e.target.closest('[data-action],[data-open],[data-convert]');if(!target)return;
  const action=target.dataset.action|| (target.dataset.open?'open':'convert');
  if(action==='open'){state.active=target.dataset.open;state.view='thread';state.draft=null;render();return;}
  onAction(action,target).catch(err=>notice(err.message));
});
document.addEventListener('submit',e=>{
  if(e.target.id!=='new-thread')return;e.preventDefault();
  try{const form=new FormData(e.target);
    const x=newThread({title:form.get('title').trim(),goal:form.get('goal').trim(),agent:form.get('agent').trim()});
    put(x);state.view='thread';render();
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
