import {HEADINGS,PHASES} from '../fixtures.mjs';
import {freshId,activeIntent,assertPublic,validate} from './thread.mjs';
const PREFIX='GROUNDING_FIXTURES_V1:';
const keys=new Set(HEADINGS.map(([,key])=>key));
const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));

function checked(values){
  if(!values||typeof values!=='object'||Array.isArray(values))throw Error('Invalid grounding');
  const out={};
  for(const [key,text] of Object.entries(values)){
    if(!keys.has(key))throw Error('Unknown grounding heading');
    if(typeof text!=='string'||text.length>12000)throw Error('Grounding item too long');
    if(text.trim())out[key]=text.trim();
  }
  if(JSON.stringify(out).length>85000)throw Error('Grounding snapshot too long');
  assertPublic(out);return out;
}
export function readGrounding(thread){
  const last=[...thread.moves].reverse().find(m=>m.kind==='amendment'&&m.note.startsWith(PREFIX));
  return last?checked(JSON.parse(last.note.slice(PREFIX.length))):{};
}
export function groundingMove(thread,values,id=freshId()){
  const next=checked(values),before=readGrounding(thread);
  if(HEADINGS.every(([,key])=>(before[key]||'')===(next[key]||'')))return null;
  const move={id,kind:'amendment',delivery:'draft',packet:'',returnLine:'',digest:'',
    evidence:'',gap:'',decision:'',archive:'',note:PREFIX+JSON.stringify(next)};
  validate({...thread,moves:[...thread.moves,move]});return move;
}
export function groundingSummary(move){
  if(!move.note?.startsWith(PREFIX))return null;
  return 'Grounding updated · '+Object.keys(checked(JSON.parse(move.note.slice(PREFIX.length)))).length+' headings';
}
export function groundingText(thread){
  const i=activeIntent(thread),values=readGrounding(thread);
  return ['Project grounding · '+thread.id,'Owner goal: '+i.goal,
    'In scope: '+i.inScope,'Out of scope: '+i.outScope,'HOLD: '+(i.hold||'OFF'),
    ...HEADINGS.filter(([,key])=>values[key]).map(([,key,label])=>key+'. '+label+'\n'+values[key])].join('\n\n');
}
export function groundingPanel(thread,values=readGrounding(thread),hasDraft=false){
  const linkKeys=new Set(['1a','1b','1c','1d']);
  const actionsBar='<div class="grounding-actions">'+
    '<button type="submit" class="primary">Save grounding</button> '+
    '<button type="button" data-action="copy-grounding">Copy grounding for agent</button> '+
    '<span class="grounding-status" role="status" aria-live="polite">'+(hasDraft?'Unsaved device draft restored':'')+'</span></div>';
  return '<div class="heading"><button data-action="thread">← Thread</button><h2>Grounding Fixtures</h2></div>'+
    '<nav aria-label="Thread sections"><button data-action="thread">Thread</button> <button data-action="grounding" aria-current="page">Grounding Fixtures</button></nav>'+
    '<p>Keep reusable context here. Blank means UNKNOWN. Edits stay on this device while typing. &quot;Save grounding&quot; creates one local snapshot in thread history. Publish to GitHub on Thread page.'+(hasDraft?' <strong class="draft-indicator">(Unsaved device draft restored)</strong>':'')+'</p>'+
    '<form id="grounding-form">'+actionsBar+Object.entries(PHASES).map(([phase,label])=>
      '<details'+(phase==='onboarding'?' open':'')+'><summary>'+esc(label)+'</summary>'+
      HEADINGS.filter(([p])=>p===phase).map(([,key,title])=>
        '<label>'+esc(key+'. '+title)+
        (linkKeys.has(key)?
          '<textarea name="ground-'+key+'" rows="1" class="compact-textarea" maxlength="12000" placeholder="UNKNOWN — optional URL or reference">'+esc(values[key]||'')+'</textarea>':
          '<textarea name="ground-'+key+'" rows="3" maxlength="12000" placeholder="UNKNOWN — optional notes and source links">'+esc(values[key]||'')+'</textarea>')+
        '</label>').join('')+'</details>').join('')+
    actionsBar+
    '<p class="small">Saved updates stay in thread history. Public GitHub saves exclude private chat links.</p></form>';
}

