'use strict';
async function renderL4Improvements(app, name) {
  const ctx = await l4Context(name);
  const box = l4Frame(app, 'improvements', 'Improvements register', ctx);
  if (!ctx.summary) return;
  const source = ctx.detail.improvements ?? ctx.summary.improvements;
  if (!Array.isArray(source) || !source.length) {
    if (source?.status === 'ERROR') l4Line(box,'Schema error',source.errors);
    l4Unknown(box, 'Improvement register');
    return;
  }
  for (const row of source) {
    const card = el('section','card l4-improvement');
    if (!row || row.status === 'ERROR') {
      l4Line(card, 'Schema ERROR', row?.errors);
      l4Line(card, 'Raw record', row?.raw);
      box.appendChild(card);continue;
    }
    card.appendChild(el('h2', '', l4Text(row.id) + ' · ' + l4Text(row.title)));
    for (const key of ['author','disposition','reason','revisit_if',
                       'implemented_in','observed_result','retain'])
      l4Line(card, key, row[key]);
    l4Link(card,'Implementation evidence',row.implemented_in,ctx.repo);
    box.appendChild(card);
  }
}
