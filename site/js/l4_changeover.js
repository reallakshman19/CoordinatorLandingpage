'use strict';
function l4MarkdownEscape(value) {
  const text = l4Text(value).replace(/\r?\n/g, ' ');
  return text.replace(/([\\\x60*_{}\[\]()#+.!>|~-])/g, '\\$1');
}
function l4SuccessorBrief(ctx, succession) {
  const fields = [
    '# Successor brief · ' + l4MarkdownEscape(ctx.projectName),
    '',
    '## Custody and authority',
    'Projection only; not a verified approval or execution instruction.',
    'Project: ' + l4MarkdownEscape(ctx.projectName),
    'Repository: ' + l4MarkdownEscape(ctx.repo),
    'Outgoing: ' + l4MarkdownEscape(succession.outgoing),
    'Incoming: ' + l4MarkdownEscape(succession.incoming),
    'Method: ' + l4MarkdownEscape(succession.method),
    'Phase: ' + l4MarkdownEscape(succession.phase),
    'Custody: ' + l4MarkdownEscape(succession.custody),
    '',
    '## Handover references',
  ];
  for (const k of ['1a','1b','2']) {
    const raw = succession.links?.[k];
    const source = allowedExternalLink(raw,ctx.repo) ||
      allowedExternalLink(raw,REPO);
    fields.push(k + ': ' + (source || 'UNKNOWN'));
  }
  fields.push('','## Pending sends');
  const sends = succession.pending_sends;
  if (Array.isArray(sends) && sends.length)
    for (const s of sends) fields.push('- ' + l4MarkdownEscape(s));
  else fields.push('UNKNOWN');
  fields.push('','## Unrecorded interval',
    'From checkpoint: ' + l4MarkdownEscape(succession.unrecorded_interval?.from_checkpoint),
    'To departure: ' + l4MarkdownEscape(succession.unrecorded_interval?.to_departure),
    '','## Evidence sources');
  const status = ctx.summary.source_refs?.status_issue;
  fields.push('Status issue: ' + (allowedExternalLink(status,ctx.repo) ||
    allowedExternalLink(status,REPO) || 'UNKNOWN'));
  return fields.join('\n') + '\n';
}
async function renderL4Changeover(app, name) {
  const ctx = await l4Context(name);
  const box = l4Frame(app, 'changeover', 'Changeover and succession', ctx);
  if (!ctx.summary) return;
  const row = ctx.detail.succession ?? ctx.summary.succession;
  if (!row || Array.isArray(row) || row.status === 'ERROR' ||
      typeof row !== 'object') {
    if (row?.status === 'ERROR') l4Line(box,'Schema error',row.errors);
    l4Unknown(box, 'Succession record');
    return;
  }
  for (const key of ['outgoing','incoming','method','phase','custody'])
    l4Line(box,key,row[key]);
  for (const key of ['1a','1b','2']) {
    const div = l4Line(box,'Stage '+key,row.links?.[key]);
    l4Link(div,'Source link',row.links?.[key],ctx.repo);
  }
  l4Line(box,'Pending sends',row.pending_sends);
  l4Line(box,'From checkpoint',row.unrecorded_interval?.from_checkpoint);
  l4Line(box,'To departure',row.unrecorded_interval?.to_departure);
  const button = el('button','btn btn-small','Copy successor brief');
  button.id = 'l4-copy-brief';
  button.type = 'button';
  const notice = el('span','note l4-copy-result');
  button.addEventListener('click',async() => {
    const markdown = l4SuccessorBrief(ctx,row);
    try {
      if (!navigator.clipboard?.writeText) throw new Error('Clipboard unavailable');
      await navigator.clipboard.writeText(markdown);
      notice.textContent = 'Copied · no GitHub or agent action performed';
    } catch {
      notice.textContent = 'Copy unavailable · no successor message sent';
    }
  });
  box.appendChild(button);box.appendChild(notice);
}
