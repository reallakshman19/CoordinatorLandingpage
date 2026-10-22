const {el, ppSafeUrl, ppRich, ppLink, ppSendUrl, PP_FIX_LEFT, PP_FIX_RIGHT, PP_FIX_CLS} = await import('./helpers.mjs' + new URL(import.meta.url).search);
function ppFixLink(ctx, text, sign, title) {
  const a = el('a', 'pp-pm', sign);
  a.href = ppSendUrl(ctx, text);
  a.target = '_blank';
  a.rel = 'noopener noreferrer';
  a.title = title;
  a.setAttribute('aria-label', title);
  return a;
}
function ppFixSection(page, topicKey, key, label, entries) {
  const ctx = { project: page.project, page: page.key, topic: topicKey, view: 'fixtures',
    mode: page.mode, replyTo: page.replyTo, type: 'INFO',
    label: `INFO fixture ${topicKey}/${key}`, card: key, option: 'fixture' };
  const s = el('section', 'pp-fsec');
  const h = el('div', 'pp-fhead');
  h.appendChild(el('h4', '', label));
  if (page.replyTo?.kind === 'github-issue') h.appendChild(ppFixLink(ctx, `FIXTURE ${topicKey}/${key} ADD: `, '+', 'Propose an addition (opens the GitHub Owner Reply form)'));
  s.appendChild(h);
  const items = Array.isArray(entries) ? entries : [];
  if (!items.length) { s.appendChild(el('p', 'pp-fnone', 'None recorded yet.')); return s; }
  const ul = el('ul', 'pp-flist');
  items.forEach(e => {
    const li = el('li');
    const line = el('div', 'pp-fline');
    const u = ppSafeUrl(e.u);
    const long = !!e.n || String(e.t || '').length > 110;   // a long entry stays plain text with a small source link
    const text = u && !long ? ppLink(u, e.t || e.u, 'pp-ftext') : ppRich(el('span', 'pp-ftext'), e.t);
    line.appendChild(text);
    if (u && long) line.appendChild(ppLink(u, 'source', 'pp-fsrc'));
    if (e.s) line.appendChild(el('span', 'pp-st ' + (PP_FIX_CLS[e.s] || 'pp-idle'), String(e.s).toUpperCase()));
    if (page.replyTo?.kind === 'github-issue') line.appendChild(ppFixLink(ctx, `FIXTURE ${topicKey}/${key} REMOVE: ${e.t || ''}`, '−', 'Propose removing this entry (opens the GitHub Owner Reply form)'));
    li.appendChild(line);
    if (e.n) li.appendChild(ppRich(el('div', 'pp-fnote'), e.n));
    ul.appendChild(li);
  });
  s.appendChild(ul);
  return s;
}
function ppDrawFixtures(root, page, topicKey, P) {
  const fx = P.fixtures || {};
  root.appendChild(el('p', 'pp-intro', page.mode === 'standalone-oracle'
    ? 'MANDATORY AGENT ONBOARDING: read this Grounding fixture and the Standalone Oracle Engineering Relay Protocol before starting. Post a real source-backed onboarding receipt in the owning task; Owner authorization is separate. This page cannot dispatch, approve or alter anything.'
    : 'What a new agent or Oracle should read first for this topic. OTM keeps it current. The + and − open GitHub\'s Owner Reply form with the change filled in; nothing changes until OTM applies it and you confirm.'));
  const grid = el('div', 'pp-fixgrid');
  [['Project sources', PP_FIX_LEFT], ['Starting context', PP_FIX_RIGHT]].forEach(([title, defs]) => {
    const col = el('section', 'card pp-fixcol');
    col.appendChild(el('h3', '', title));
    defs.forEach(([key, label]) => col.appendChild(ppFixSection(page, topicKey, key, label, fx[key])));
    grid.appendChild(col);
  });
  root.appendChild(grid);
}

export {ppDrawFixtures};
