'use strict';
async function renderL4Understanding(app, name) {
  const ctx = await l4Context(name);
  const box = l4Frame(app, 'understanding', 'Project understanding', ctx);
  if (!ctx.summary) return;
  const detail = ctx.detail, p = ctx.summary, reg = detail.registry || {};
  const parent = (p.lineage || detail.lineage || []).find(
    row => row && row.kind === 'parent_issue' && row.status === 'AVAILABLE');
  if (parent) {
    l4Line(box, 'Root issue', parent.title || parent.issue_number);
    l4Link(box, 'Root issue source', parent.url, ctx.repo);
  } else l4Unknown(box, 'Root issue intent');
  const sourceIntent = p.intent || detail.intent || {};
  if (sourceIntent.status === 'AVAILABLE' && l4Known(sourceIntent.text)) {
    l4Line(box, 'Root Owner intent text', sourceIntent.text);
    if (sourceIntent.truncated)
      box.appendChild(el('span', 'note', 'Root intent truncated at ' +
        String(sourceIntent.limit_chars || 'bounded') + ' characters.'));
    l4Link(box, 'Root intent source', sourceIntent.source, ctx.repo);
  } else {
    l4Unknown(box, 'Root intent text');
    box.appendChild(el('p', 'note',
      'Root intent unavailable: ' + String(sourceIntent.reason || 'not captured')));
  }
  const sourceAmendments = p.amendments || detail.amendments || {};
  const inbox = el('section', 'l4-inbox-amendments');
  inbox.appendChild(el('h2', '', 'Project-linked #1 amendment records'));
  inbox.appendChild(el('p', 'note',
    'Source-linked coordination records; not independent proof of Owner approval.'));
  if (sourceAmendments.status === 'UNKNOWN' || !sourceAmendments.status) {
    l4Unknown(inbox, 'Project #1 amendments');
    inbox.appendChild(el('p', 'note', 'Reason: ' +
      (sourceAmendments.reason === 'inbox_1_not_fetched' ||
       !sourceAmendments.status ? 'inbox #1 not fetched' :
       String(sourceAmendments.reason))));
  } else if (sourceAmendments.status === 'NONE_FOUND') {
    inbox.appendChild(el('p', 'note', 'No project-referenced records in captured #1.'));
  } else {
    for (const entry of (Array.isArray(sourceAmendments.records)
      ? sourceAmendments.records : [])) {
      const record = el('div', 'l4-amendment');
      const span = el(entry.superseded ? 's' : 'span', '', String(entry.text || 'UNKNOWN'));
      record.appendChild(span);
      if (entry.truncated) record.appendChild(el('span', 'note', ' · truncated'));
      record.appendChild(el('span', 'note', ' · ' +
        String(entry.attribution || 'UNVERIFIED_AUTHOR')));
      l4Link(span, 'Source record', entry.source, REPO);
      inbox.appendChild(record);
    }
    if (sourceAmendments.truncated) inbox.appendChild(el('p', 'note',
      'List truncated: ' + String(sourceAmendments.records?.length || 0) +
      ' of ' + String(sourceAmendments.total_matching || 'UNKNOWN') + ' matching records'));
  }
  box.appendChild(inbox);
  const intent = reg.workflow?.owner_words || p.workflow?.owner_words;
  if (l4Known(intent)) l4Line(box, 'Recorded Owner/workflow intent', intent);
  else l4Unknown(box, 'Owner intent');
  const note = el('section', 'l4-amendments');
  note.appendChild(el('h2', '', 'Owner amendments and supersessions'));
  const decisions = Array.isArray(reg.standing_owner_decisions)
    ? reg.standing_owner_decisions : [];
  let count = 0;
  for (const record of decisions) {
    const value = typeof record === 'string' ? record
      : record && typeof record === 'object'
      ? String(record.text || record.owner_words || record.words || '') : '';
    if (!value.trim()) continue;
    const row = el('div', 'l4-amendment');
    const superseded = /supersed/i.test(value) ||
      (record && typeof record === 'object' && !!record.superseded_by);
    const line = superseded ? el('s') : el('span');
    line.appendChild(el('span', '', value));
    const source = typeof record === 'object'
      ? (record.source || record.source_ref || record.url) : null;
    l4Link(line, 'Source record', source, ctx.repo);
    row.appendChild(line);
    if (superseded) row.appendChild(el('span', 'badge badge-grey', 'Superseded'));
    note.appendChild(row); count++;
  }
  // The inbox can contain Owner amendments, but a generic inbox URL alone
  // is not proof of any specific amendment.
  if (count) l4Link(note, 'Coordination inbox', p.source_refs?.inbox, REPO);
  if (!count) l4Unknown(note, 'Source-linked amendments');
  box.appendChild(note);
}
