import {groundingPanel,groundingMove,groundingText,readGrounding} from './grounding.mjs';
import {rememberComposer,restoreComposer} from './composer.mjs';
import {prepareAction} from './transport-request.mjs';
import {activeAgent,activeIntent} from './thread.mjs';
import {REPO} from './save.mjs';
const DRAFTS='nextnudge.grounding.drafts.v1';
const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const $=q=>document.querySelector(q);
function drafts(){try{return JSON.parse(localStorage.getItem(DRAFTS)||'{}');}catch{return {};}}
function groundingValues(form){
  return Object.fromEntries([...new FormData(form)].filter(([key])=>key.startsWith('ground-'))
    .map(([key,value])=>[key.slice(7),value]));
}
export function renderGrounding(thread){
  const draft=drafts()[thread.id];
  return groundingPanel(thread,draft||readGrounding(thread));
}
export function restoreDraft(thread){return restoreComposer(thread.id);}
export function composerExtras(thread,draft){
  rememberComposer(thread.id,draft);
  const issue=readGrounding(thread)['1a']?.match(/\/issues\/(\d+)/)?.[1]||'';
  return '<section class="github-delivery"><h4>GitHub delivery</h4>'+
    '<p>Owner submits one prepared issue; the existing workflow posts and records this exact packet. Target repository: '+esc(REPO)+'.</p>'+
    '<label>Target issue number<input id="delivery-issue" type="number" min="1" value="'+esc(draft.targetIssue||issue)+'"></label>'+
    '<label>Named agent<input id="delivery-agent" maxlength="200" value="'+esc(draft.targetAgent||activeAgent(thread))+'"></label>'+
    '<button data-action="send-github">Send via GitHub…</button><p id="delivery-link"></p></section>';
}
export function returnControls(thread){
  const sent=thread.moves.filter(m=>m.delivery==='sent'&&m.note?.startsWith('GITHUB_SEND_V1:'));
  if(!sent.length)return '';
  return '<section><label>GitHub packet<select id="return-move">'+sent.map(m=>
    '<option value="'+esc(m.id)+'">'+esc(m.id)+' · '+esc(m.agent)+'</option>').reverse().join('')+
    '</select></label><button data-action="fetch-github">Fetch GitHub return…</button><p id="delivery-link"></p></section>';
}
async function prepareDelivery(action,ctx){
  const {state,t,notice}=ctx,thread=t();
  if(action==='send-github'&&activeIntent(thread).hold)throw Error('Owner HOLD');
  const win=window.open('about:blank','_blank');
  try{
    const options=action==='send-github'?{draft:state.draft,packet:$('#packet')?.value||state.draft?.packet,
      issue:$('#delivery-issue')?.value,agent:$('#delivery-agent')?.value}:{moveId:$('#return-move')?.value};
    if(action==='send-github'){
      Object.assign(state.draft,{packet:options.packet,targetIssue:options.issue,targetAgent:options.agent});
      rememberComposer(thread.id,state.draft);
    }
    const out=await prepareAction(thread,action==='send-github'?'send':'fetch',options);
    if(win){win.opener=null;win.location.replace(out.url);}
    else {const a=document.createElement('a');a.href=out.url;a.target='_blank';a.rel='noopener noreferrer';
      a.textContent='Open prepared GitHub request';$('#delivery-link')?.replaceChildren(a);}
    notice('Review and submit the Owner request. Delivery is not yet confirmed; compare with GitHub after the workflow receipt.');
  }catch(e){win?.close();throw e;}
}
export async function featureAction(action,ctx){
  if(action==='grounding'){ctx.state.view='grounding';ctx.render();return true;}
  if(action==='copy-grounding'){
    const thread=ctx.t(),preview=groundingMove(thread,groundingValues($('#grounding-form')));
    const text=groundingText(preview?{...thread,moves:[...thread.moves,preview]}:thread);
    try{await navigator.clipboard.writeText(text);ctx.notice('Grounding copied. Copy does not send.');}
    catch{const box=document.createElement('textarea');box.value=text;box.readOnly=true;
      $('#grounding-form').appendChild(box);box.select();ctx.notice('Use the selected manual-copy text.');}
    return true;
  }
  if(['send-github','fetch-github'].includes(action)){await prepareDelivery(action,ctx);return true;}
  return false;
}
export function installFeatures(ctx){
  document.addEventListener('input',event=>{
    try{
      if(event.target.id==='packet'&&ctx.state.draft){
        ctx.state.draft.packet=event.target.value;rememberComposer(ctx.t().id,ctx.state.draft);
      }
      if(event.target.closest('#grounding-form')){
        const rows=drafts();rows[ctx.t().id]=groundingValues($('#grounding-form'));
        localStorage.setItem(DRAFTS,JSON.stringify(rows));
      }
    }catch(e){ctx.notice('Browser draft storage failed: '+e.message+'. Copy/export before leaving.');}
  });
  document.addEventListener('submit',event=>{
    if(event.target.id!=='grounding-form')return;event.preventDefault();
    try{
      const thread=ctx.t(),move=groundingMove(thread,groundingValues(event.target));
      const rows=drafts();delete rows[thread.id];
      if(move)ctx.append(move);
      localStorage.setItem(DRAFTS,JSON.stringify(rows));
      ctx.notice(move?'Grounding saved locally as one update. Save to GitHub for durable sharing.':'Grounding unchanged; no history entry added.');
    }catch(e){ctx.notice(e.message);}
  });
}
