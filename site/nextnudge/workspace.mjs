import {children,waitingOn} from './model.mjs';
import {esc,labels,options,link} from './util.mjs';
function tree(run,parent=null,depth=0) {
  return run.nodes.filter(n=>n.parent===parent&&!n.deleted).map(n=>`
    <button class="step ${run.selected===n.id?'selected':''}" style="padding-left:${12+depth*14}px"
      data-action="select-step" data-id="${n.id}">
      <span class="dot">${n.status==='accepted'?'✓':n.status==='revision'?'!':'○'}</span>
      <span>${esc(n.label)}<small>${labels[n.status]}</small></span>
    </button>${tree(run,n.id,depth+1)}`).join('');
}
function message(m,index) {
  return `<article class="message ${m.by==='Owner'?'instructor':''}">
    <div class="by">${m.by==='Owner'?'INSTRUCTOR':'AGENT · MANUALLY RELAYED'}</div>
    <div class="text">${esc(m.text)}</div>${link(m.proof)}
    <small>Recorded ${esc(m.at)}${m.by==='Agent'?' · Reply time '+esc(m.repliedAt||'UNKNOWN'):''} · Source ${esc(m.source||'chat_words')}</small>
    ${m.returnFile?`<small>Return file: ${esc(m.returnFile.path)} · ${m.returnFile.bytes} bytes · SHA-256 ${esc(m.returnFile.sha256)}</small>`:''}
    ${m.savedLine?`<small>${esc(m.savedLine.tag)} · ${esc(JSON.stringify(m.savedLine.fields))}</small>`:''}
    ${m.verification?`<small>Verified by ${esc(m.verification.checkedBy)} · ${esc(m.verification.recomputed)} · ${esc(m.verification.result)} · ${esc(m.verification.note)}</small>`:''}
    ${index===undefined?'':`<form class="reply-verification" data-reply-verify="${index}">
      <label>Verified by<input name="checkedBy" required maxlength="300" value="${esc(m.verification?.checkedBy||'')}"></label>
      <label>Recomputed<input name="recomputed" required maxlength="2000" value="${esc(m.verification?.recomputed||'')}"></label>
      <label>Result<select name="result">${options([['MATCH','MATCH'],['MISMATCH','MISMATCH']],m.verification?.result||'MATCH')}</select></label>
      <label>Verification note<input name="note" maxlength="5000" value="${esc(m.verification?.note||'')}"></label>
      <button type="submit">Record independent check</button></form>`}
  </article>`;
}
export function workbench(db,r,n) {
  const disabled=r.paused||r.archived;
  const draft=r.drafts[n.id]||{};
  const pending=children(r,n.id).filter(c=>c.status!=='accepted');
  const waiting=waitingOn(r).find(x=>x.id===n.id);
  return `<div class="workbench"><aside class="tree"><h3>YOUR LADDER · ALL STEPS OPEN</h3>
    ${tree(r)}<button data-action="add-step">＋ Add nudge</button>
    <p class="legend">Choose any step. Corrections still require parent re-review.</p></aside>
    <section class="workspace"><div class="stage-head"><div><h2>${esc(n.label)}</h2>
      <small>${n.id} · ${n.type}</small></div><span class="pill">${labels[n.status]}</span></div>
    <div class="conversation"><div class="lanes"><span>AGENT</span><span>INSTRUCTOR</span></div>
      ${message({by:'Owner',text:n.instruction,at:n.sentAt||'Not marked sent'})}
      <div class="delivery"><button data-action="copy-step" ${disabled?'disabled':''}>Copy for chat</button>
      <button data-action="packet-file" data-id="${n.id}">Save packet .md</button>
      <small>Packet SHA-256: <output id="packet-sha256" data-step="${n.id}">Calculating…</output></small>
      <button data-action="send-step" ${disabled||n.sentAt?'disabled':''}>Mark sent</button>
      <small>${n.sentAt?'Recorded sent at '+esc(n.sentAt):'Copying is not sending.'}</small>
      ${waiting?`<small class="waiting-time" data-sent-at="${esc(n.sentAt)}">Waiting ${waiting.elapsedMinutes} min ${waiting.quiet?'· QUIET >30 min':''}</small>`:''}</div>
      ${n.messages.map((m,i)=>message(m,i)).join('')}
      ${children(r,n.id).map(c=>`<button data-action="select-step" data-id="${c.id}">↳ ${esc(c.label)} · ${labels[c.status]}</button>`).join('')}
      ${pending.length?`<p>${pending.length} correction branch(es) await resolution.</p>`:''}
      ${n.status==='submitted'&&children(r,n.id).length&&!pending.length?'<p>Children resolved. Recheck this parent before accepting it.</p>':''}
    </div>
    <form id="reply-form" class="composer"><div class="composer-top"><span>RECORD FOR ${n.id}</span>
      <select name="by" data-draft="by" aria-label="Reply author">${options([['Owner','Instructor (Owner)'],['Agent','Agent — exact relayed words']],draft.by||'Owner')}</select></div>
      <textarea name="text" data-draft="text" aria-label="Reply text" placeholder="Record feedback, paste the agent’s exact reply, or describe a correction…" ${disabled?'disabled':''}>${esc(draft.text||'')}</textarea>
      <div class="field-grid"><label>Reply source<select name="source" data-draft="source">
        ${options([['chat_words','Chat words'],['return_file','Return file'],['relayed_summary','Relayed summary']],draft.source||'chat_words')}</select></label>
      <label>Return file path<input name="returnPath" data-draft="returnPath" value="${esc(draft.returnPath||'')}"></label>
      <label>Return file bytes<input name="returnBytes" data-draft="returnBytes" type="number" min="0" step="1" value="${esc(draft.returnBytes||'')}"></label>
      <label>Return file SHA-256<input name="returnSha256" data-draft="returnSha256" pattern="[a-fA-F0-9]{64}" value="${esc(draft.returnSha256||'')}"></label></div>
      <div class="field-grid"><label>Evidence URL — optional<input name="proof" data-draft="proof" type="url" value="${esc(draft.proof||'')}"></label>
      <label>Actual agent reply time — optional<input name="repliedAt" data-draft="repliedAt" type="datetime-local" value="${esc(draft.repliedAt||'')}"></label></div>
      <small>Reply time uses your browser’s timezone and is stored in UTC. Blank means UNKNOWN. For return-file source, provide path, bytes and SHA-256. SAVED lines are parsed automatically.</small>
      <label>Review / acceptance note (separate from reply)
        <textarea name="reviewNote" data-draft="reviewNote" aria-label="Acceptance note for selected step">${esc(draft.reviewNote||'')}</textarea></label>
      ${n.acceptance?`<small>Accepted: ${esc(n.acceptance.note)} · ${esc(n.acceptance.by)} · ${esc(n.acceptance.at)}</small>`:''}
      <div class="actions"><button type="button" data-action="correction" ${disabled?'disabled':''}>＋ Correction child</button>
      <button type="button" data-action="accept-step" data-id="${n.id}" ${disabled||n.status!=='submitted'||pending.length?'disabled':''}>${n.parent?'Accept correction':'Review & accept'}</button>
      <button type="button" data-action="revert-status" data-id="${n.id}" ${disabled?'disabled':''}>Revert last status (reason required)</button>
      <button class="primary" type="submit" ${disabled?'disabled':''}>Record locally</button></div>
    </form></section></div>`;
}
export function history(db,r) {
  return `<section class="panel"><h2>Append-only history</h2><p>Owner-recorded activity. No NextMove authority or automatic delivery proof.</p>
    <div class="table-scroll"><table><thead><tr><th>UTC time</th><th>Actor</th><th>State / step</th><th>Note / proof</th></tr></thead><tbody>
    ${db.events.filter(e=>e.run===r.id).slice().reverse().map(e=>`<tr><td>${esc(e.at)}</td><td>${e.by}</td><td>${esc(e.state)}<small>${esc(e.step||r.id)}</small></td><td>${esc(e.note)} ${link(e.proof)}<details><summary>Full record</summary><pre>${esc(JSON.stringify(e,null,2))}</pre></details></td></tr>`).join('')}
    </tbody></table></div></section>`;
}
