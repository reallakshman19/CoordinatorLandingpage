import {checklist} from './model.mjs';
import {esc,options} from './util.mjs';
import {getPrivateChat} from './storage.mjs';
export function prepare(db,r,n) {
  return `<section class="panel prepare"><span class="eyebrow">PREPARE THE LADDER</span>
    <h2>Your task. Your sequence.</h2><p>All steps are available. Sent or answered instructions are frozen; use a correction to change them.</p>
    <form id="run-settings"><div class="field-grid"><label>Task title<input name="title" value="${esc(r.title)}" required></label>
    <label>Agent chat ID — 8 hex characters<input name="chatId8" pattern="[a-fA-F0-9]{8}" value="${esc(r.chatId8)}"></label></div>
    <label>Owner aim<textarea name="aim" required>${esc(r.aim)}</textarea></label>
    <label>Sent by<select name="sentBy">${options([['Owner','Owner'],['TeamCoordinator','TeamCoordinator']],r.sentBy||'Owner')}</select></label>
    <label>Agent chat URL — device-only, excluded from shared snapshots<input type="url" name="privateChat" value="${esc(getPrivateChat(r.id))}"></label>
    <button>Record settings</button></form>
    <h3>Agent session change</h3><p>Record a new destination session and why the earlier one cannot be used. The prior session remains in history.</p>
    <form id="session-change-form"><label>New 8-character session ID<input name="newSessionId" pattern="[a-fA-F0-9]{8}" required></label>
      <label>Reason<input name="reason" required placeholder="Chat unreadable"></label>
      <button type="submit">Record session change</button></form>
    <h3>Checklist profiles</h3><div class="protocol-options">${Object.keys(db.profiles.profiles).map(p=>`<label><input type="checkbox" data-profile="${esc(p)}" ${r.profiles.includes(p)?'checked':''}>${esc(p)}</label>`).join('')}</div>
    <div class="actions"><button data-action="import-profiles">Import profile JSON</button><button data-action="export-profiles">Export profile JSON</button></div>
    <h3>Instructor guide · ${esc(n.label)}</h3><p>Select a step in the workspace to review its checklist here. Examples and evidence suggestions are configurable.</p>
    ${checklist(db,r).map(q=>`<div class="guide-row"><div><strong>${esc(q.question)}</strong><small>${esc(q.profile)} · ${esc(q.example)}</small><small>Optional support: ${esc(q.evidence)}</small></div><select data-check="${esc(q.key)}" aria-label="${esc(q.question)}">${options([['','Unreviewed'],...['Addressed','Needs correction','Proceed with gap','Not applicable'].map(x=>[x,x])],n.checks[q.key]||'')}</select></div>`).join('')}
    <h3>Editable steps</h3>${r.nodes.filter(n=>!n.deleted).map(step=>stepForm(step)).join('')}
    <button data-action="add-step">＋ Add another nudge</button>
  </section>`;
}
function stepForm(n) {
  const frozen=n.sentAt||n.messages.length;
  return `<form class="step-editor" data-step-edit="${n.id}"><small>${n.id}${frozen?' · FROZEN':''}</small>
    <div class="field-grid"><label>Label<input name="label" value="${esc(n.label)}" ${frozen?'disabled':''} required></label>
    <label>Type<select name="type" ${frozen?'disabled':''}>${options(['new_requirement','ground','next_step','course_correction'].map(x=>[x,x]),n.type)}</select></label></div>
    <label>Instruction<textarea name="instruction" ${frozen?'disabled':''}>${esc(n.instruction)}</textarea></label>
    <div class="actions"><button ${frozen?'disabled':''}>Record changes</button><button type="button" data-action="delete-step" data-id="${n.id}" ${frozen?'disabled':''}>Delete step</button></div>
  </form>`;
}
