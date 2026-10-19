import {activeAgent,activeIntent,currentState} from './thread.mjs';
const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
export function packet(id,kind,body,i,options={}) {
  const common=['[Owner · NextNudge '+id+']','Owner intent: '+i.goal,
    'Owner done-when: '+(i.doneWhen.join(' | ')||'UNKNOWN — ask Owner'),
    'In scope: '+i.inScope,'Out of scope: '+i.outScope,
    'Uncertainty: report UNKNOWN; never substitute an assumption.',
    'COMPLETE describes this bounded task, not Owner-outcome acceptance.'];
  const prefix=kind==='task'?'Purpose:\n'+i.goal+'\nOne bounded task:\n'+body+
    '\nAuthoritative inputs:\n'+(options.inputs||'UNKNOWN')+'\nBoundaries:\n'+(options.boundaries??i.inScope)+'\nSuccess criteria:\n'+(options.success||i.doneWhen.join(' | ')||'UNKNOWN')+
    '\nUncertainty handling:\nState missing facts and blocked actions.\nEvidence and continuation:\nReturn artifacts, limits and next feasible action.':
    kind==='ground'?'Restate the Owner intent and done-when in your own words. State your first step and unknowns.\n'+body:
    kind==='correction'?'Quote the incorrect claim, identify the input interpretation, give the redo scope.\n'+body:
    kind==='close'?'The Owner outcome checks were verified. Return the final PR/file/comment pointer.\n'+body:body;
  return [...common,prefix,'Start your reply with ACK '+id+'.'].join('\n\n');
}
export function threadsMarkup(threads) {
  const rows=Object.values(threads).sort((a,b)=>b.id.localeCompare(a.id));
  return '<h2>Threads</h2><p>One intent, one current move. Drafts stay on this device.</p>'+
    '<form id="new-thread"><label>Intent title <input name="title" required maxlength="120"></label>'+
    '<label>Owner goal, in their words <textarea name="goal" required></textarea></label>'+
    '<label>Agent <input name="agent" placeholder="Agent or UNKNOWN"></label>'+
    '<button type="submit">Create thread</button></form>'+
    '<div class="thread-list">'+rows.map(x=>'<button data-open="'+esc(x.id)+'" class="thread-row">'+
      '<strong>'+esc(x.title)+'</strong><span>'+esc(activeAgent(x)||'UNKNOWN')+' · '+esc(currentState(x))+
      (activeIntent(x).hold?' · '+esc(activeIntent(x).hold):'')+'</span></button>').join('')+'</div>'+
    '<div class="archive"><details><summary>v2 Archive · read-only + Convert</summary>'+
    '<p>Original v2 database is retained unchanged. Historical statuses do not prove acceptance.</p>'+
    '<button data-action="archive-list">List v2 runs for conversion</button><div id="archive-runs"></div>'+
    '<p><a href="v2.html" target="_blank" rel="noopener noreferrer">Open original v2 workbench (historical interface)</a></p></details></div>'+
    '<p><button data-action="load-id">Load existing GitHub thread by ID</button> '+
    '<button data-action="import">Import Markdown thread</button></p>';
}
