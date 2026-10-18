import {HEADINGS,PHASES,appendOnly} from './fixtures.mjs';
import {esc,options,link} from './util.mjs';
function item(key,row) {
  const immutable=row&&appendOnly(key);
  return `<form class="fixture-item" data-fixture="${key}" data-row="${row?.id||''}">
    <label>Item / finding<textarea name="text" required ${immutable?'disabled':''}>${esc(row?.text||'')}</textarea></label>
    <label>Source link<input name="url" type="url" value="${esc(row?.url||'')}" ${immutable?'disabled':''}>${link(row?.url)}</label>
    <label>Source status<select name="status" ${immutable?'disabled':''}>${options(['UNKNOWN','RECORDED','NEEDS_REVIEW'].map(x=>[x,x]),row?.status||'UNKNOWN')}</select></label>
    ${key==='1d'&&row?'<label>Owner-approved update basis<input name="approvalNote" required placeholder="Source / reason for the approved update"></label>':''}
    <div class="actions">${immutable?'<span class="pill">Append-only record</span>':'<button>'+ (row?'Record update':'Add item')+'</button>'}
    ${row?`<button type="button" data-action="delete-fixture" data-key="${key}" data-id="${row.id}">Remove item</button>`:''}</div>
    ${row?.source?`<details><summary>Pulled from ${esc(row.source.run)}</summary><p>Project ${esc(row.source.project)} · Heading ${esc(row.source.heading)} · Row ${esc(row.source.row)} · Revision ${row.source.revision} · ${esc(row.source.pulledAt)}. Snapshot copied for review; later source changes are not silently inherited.</p></details>`:''}
  </form>`;
}
export function fixtures(db,r,phase) {
  const sources=db.runs.filter(s=>s.id!==r.id&&!s.deleted&&s.createdAt<=r.createdAt);
  return `<section class="panel"><span class="eyebrow">GROUNDING FIXTURES</span><h2>Ground once. Reconcile as you go.</h2>
    <p>Fill from the initial prompt and original sources. UNKNOWN is visible, not proof. Pull earlier material as a traceable snapshot.</p>
    <nav class="phase-tabs">${Object.entries(PHASES).map(([id,label])=>`<button data-action="phase" data-id="${id}" class="${phase===id?'active':''}">${label}</button>`).join('')}</nav>
    ${HEADINGS.filter(([group])=>group===phase).map(([,key,label])=>`<details class="fixture-section" open><summary>${key}. ${label}</summary>
      <div class="pull-row"><select aria-label="Earlier run for ${key}" data-source="${key}"><option value="">Pull from an earlier NextNudge…</option>${options(sources.map(s=>[s.id,`${db.projects.find(p=>p.id===s.projectId)?.name} / ${s.title} · ${s.id}`]),'')}</select>
      <button data-action="pull-fixtures" data-key="${key}">Pull this heading</button></div>
      ${r.fixtures[key].filter(x=>!x.deleted).map(row=>item(key,row)).join('')}
      <details class="add-item"><summary>＋ Add item</summary>${item(key,null)}</details>
      ${r.fixtures[key].some(x=>x.deleted)?'<small>Removed entries remain in the export and history.</small>':''}
    </details>`).join('')}</section>`;
}
