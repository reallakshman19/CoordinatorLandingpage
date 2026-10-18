import {children} from './model.mjs';
import {esc,labels,options,link} from './util.mjs';
function tree(run,parent=null,depth=0) {
  return run.nodes.filter(n=>n.parent===parent&&!n.deleted).map(n=>`
    <button class="step ${run.selected===n.id?'selected':''}" style="padding-left:${12+depth*14}px"
      data-action="select-step" data-id="${n.id}">
      <span class="dot">${n.status==='accepted'?'✓':n.status==='revision'?'!':'○'}</span>
      <span>${esc(n.label)}<small>${labels[n.status]}</small></span>
    </button>${tree(run,n.id,depth+1)}`).join('');
}
function message(m) {
  return `<article class="message ${m.by==='Owner'?'instructor':''}">
    <div class="by">${m.by==='Owner'?'INSTRUCTOR':'AGENT · MANUALLY RELAYED'}</div>
    <div class="text">${esc(m.text)}</div>${link(m.proof)}
    <small>Recorded ${esc(m.at)}${m.by==='Agent'?' · Reply time '+esc(m.repliedAt||'UNKNOWN'):''}</small>
  </article>`;
}
export function workbench(db,r,n) {
  const disabled=r.paused||r.archived;
  const draft=r.drafts[n.id]||{};
  const pending=children(r,n.id).filter(c=>c.status!=='accepted');
  return `<div class="workbench"><aside class="tree"><h3>YOUR LADDER · ALL STEPS OPEN</h3>
    ${tree(r)}<button data-action="add-step">＋ Add nudge</button>
    <p class="legend">Choose any step. Corrections still require parent re-review.</p></aside>
    <section class="workspace"><div class="stage-head"><div><h2>${esc(n.label)}</h2>
      <small>${n.id} · ${n.type}</small></div><span class="pill">${labels[n.status]}</span></div>
    <div class="conversation"><div class="lanes"><span>AGENT</span><span>INSTRUCTOR</span></div>
      ${message({by:'Owner',text:n.instruction,at:n.sentAt||'Not marked sent'})}
      <div class="delivery"><button data-action="copy-step" ${disabled?'disabled':''}>Copy for chat</button>
      <button data-action="send-step" ${disabled||n.sentAt?'disabled':''}>Mark sent</button>
      <small>${n.sentAt?'Owner recorded sending at '+esc(n.sentAt):'Copying is not sending.'}</small></div>
      ${n.messages.map(message).join('')}
      ${children(r,n.id).map(c=>`<button data-action="select-step" data-id="${c.id}">↳ ${esc(c.label)} · ${labels[c.status]}</button>`).join('')}
      ${pending.length?`<p>${pending.length} correction branch(es) await resolution.</p>`:''}
      ${n.status==='submitted'&&children(r,n.id).length&&!pending.length?'<p>Children resolved. Recheck this parent before accepting it.</p>':''}
    </div>
    <form id="reply-form" class="composer"><div class="composer-top"><span>RECORD FOR ${n.id}</span>
      <select name="by" data-draft="by" aria-label="Reply author">${options([['Owner','Instructor (Owner)'],['Agent','Agent — exact relayed words']],draft.by||'Owner')}</select></div>
      <textarea name="text" data-draft="text" aria-label="Reply text" placeholder="Record feedback, paste the agent’s exact reply, or describe a correction…" ${disabled?'disabled':''}>${esc(draft.text||'')}</textarea>
      <div class="field-grid"><label>Evidence URL — optional<input name="proof" data-draft="proof" type="url" value="${esc(draft.proof||'')}"></label>
      <label>Actual agent reply time — optional<input name="repliedAt" data-draft="repliedAt" type="datetime-local" value="${esc(draft.repliedAt||'')}"></label></div>
      <small>Reply time uses your browser’s timezone and is stored in UTC. Blank means UNKNOWN.</small>
      <div class="actions"><button type="button" data-action="correction" ${disabled?'disabled':''}>＋ Correction child</button>
      <button type="button" data-action="accept-step" ${disabled||n.status!=='submitted'||pending.length?'disabled':''}>${n.parent?'Accept correction':'Review & accept'}</button>
      <button class="primary" type="submit" ${disabled?'disabled':''}>Record locally</button></div>
    </form></section></div>`;
}
export function history(db,r) {
  return `<section class="panel"><h2>Append-only history</h2><p>Owner-recorded activity. No NextMove authority or automatic delivery proof.</p>
    <div class="table-scroll"><table><thead><tr><th>UTC time</th><th>Actor</th><th>State / step</th><th>Note / proof</th></tr></thead><tbody>
    ${db.events.filter(e=>e.run===r.id).slice().reverse().map(e=>`<tr><td>${esc(e.at)}</td><td>${e.by}</td><td>${esc(e.state)}<small>${esc(e.step||r.id)}</small></td><td>${esc(e.note)} ${link(e.proof)}<details><summary>Full record</summary><pre>${esc(JSON.stringify(e,null,2))}</pre></details></td></tr>`).join('')}
    </tbody></table></div></section>`;
}
