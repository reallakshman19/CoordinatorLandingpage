const {el, ppList, ppRich, ppLink, ppMilestones, PP_CLS, PP_SYM, PP_LABELS} = await import('./helpers.mjs' + new URL(import.meta.url).search);
function ppRow(s, chats) {
  const li = el('li', 'pp-row ' + (PP_CLS[s.state] || 'pp-idle'));
  li.id = 'pp-row-' + s.id;
  const ic = el('span', 'pp-ic', PP_SYM[s.state] || '?');
  ic.setAttribute('aria-hidden', 'true');
  li.appendChild(ic);
  const main = el('div', 'pp-rmain');
  const t = el('div', 'pp-rname');
  t.appendChild(el('span', 'pp-sid', s.id));
  t.appendChild(document.createTextNode(s.name || s.id));
  if (s.cond) t.appendChild(el('span', 'pp-tag', s.cond));
  main.appendChild(t);
  if (s.sub) main.appendChild(ppRich(el('div', 'pp-rsub'), s.sub));
  const chips = el('div', 'pp-chips');
  const actor = s.actor && s.actor !== '-' ? s.actor : '';
  if (actor) chips.appendChild(el('span', 'pp-chip ' + (actor === 'YOU' ? 'pp-you' : 'pp-who'), 'NEXT: ' + actor));
  (s.chats || []).forEach(k => {
    const c = (chats || {})[k];
    if (!c) return;
    const text = `${c.label} · ${c.id8}`;
    const chip = c.url ? ppLink(c.url, text + ' ↗', 'pp-chip pp-chat') : el('span', 'pp-chip pp-chat', text);
    chip.title = c.note || 'ChatGPT chat id (first 8 characters)';
    chips.appendChild(chip);
  });
  (s.refs || []).forEach(r => chips.appendChild(ppLink(r.u, r.l, 'pp-chip')));
  if (chips.childNodes.length) main.appendChild(chips);
  if (s.detail) {
    const d = el('details', 'pp-det');
    d.appendChild(el('summary', '', 'Details'));
    const dl = el('dl', 'pp-act');
    PP_LABELS.forEach(([key, label]) => {
      if (s.detail[key]) { dl.appendChild(el('dt', '', label)); dl.appendChild(ppRich(el('dd'), s.detail[key])); }
    });
    d.appendChild(dl);
    main.appendChild(d);
  }
  li.appendChild(main);
  li.appendChild(el('span', 'pp-rstate', s.state || ''));
  return li;
}
function ppLaneCard(ln, stages, chats) {
  const c = el('section', 'card pp-lane');
  const h = el('header', 'pp-lhead');
  h.appendChild(el('h3', '', ln.title || ln.id));
  const ms = [];
  stages.forEach(s => { if (s.milestone && !ms.includes(s.milestone)) ms.push(s.milestone); });
  if (ms.length) h.appendChild(el('span', 'pp-range', ms.join(' · ')));
  c.appendChild(h);
  if (ln.sub) c.appendChild(el('p', 'pp-lsub', ln.sub));
  const ul = el('ul', 'pp-rows');
  stages.forEach(s => ul.appendChild(ppRow(s, chats)));
  c.appendChild(ul);
  return c;
}
function ppMilestoneCard(m) {
  const card = el('div', 'pp-mcard ' + (PP_CLS[m.state] || 'pp-idle'));
  card.setAttribute('role', 'listitem');
  if (m.full) card.title = m.full;
  const mh = el('div', 'pp-mh');
  const ic = el('span', 'pp-mic', PP_SYM[m.state] || '?');
  ic.setAttribute('aria-hidden', 'true');
  mh.appendChild(ic);
  mh.appendChild(document.createTextNode(m.id));
  card.appendChild(mh);
  card.appendChild(el('div', 'pp-mn', m.name || m.id));
  card.appendChild(el('div', 'pp-ms', m.state));
  card.appendChild(el('div', 'pp-mc', `${m.ok} of ${m.total} verified`));
  return card;
}
function ppDrawProgress(root, page, topicKey, P, chats) {
  const stages = ppList(P.stages);
  if (!stages.length) { root.appendChild(el('div', 'pp-empty', 'OTM has not written the stage list for this topic yet.')); return; }
  const sec = el('div', 'pp-sec');
  sec.appendChild(el('h2', '', 'Milestones'));
  const strip = el('div', 'pp-mstrip');
  strip.setAttribute('role', 'list');
  ppMilestones(P).forEach((m, i) => {
    if (i) { const ch = el('span', 'pp-chev', '›'); ch.setAttribute('aria-hidden', 'true'); strip.appendChild(ch); }
    strip.appendChild(ppMilestoneCard(m));
  });
  sec.appendChild(strip);
  const tally = { VERIFIED: 0, SUBMITTED: 0, BLOCKED: 0, NOT_STARTED: 0, other: 0 };
  stages.forEach(s => { if (s.state in tally) tally[s.state]++; else tally.other++; });
  sec.appendChild(el('p', 'pp-counts', `${tally.VERIFIED} verified · ${tally.SUBMITTED} submitted · ${tally.BLOCKED} blocked · ${tally.NOT_STARTED} not started${tally.other ? ` · ${tally.other} other` : ''} of ${stages.length} inferred stages. A stage count on a partial list, not a delivery percentage.`));
  root.appendChild(sec);

  const wrap = el('div', 'pp-lanewrap');
  let buf = null;
  ppList((P.topic || {}).lanes).forEach(ln => {
    const its = stages.filter(s => s.lane === ln.id);
    if (!its.length) return;
    if (ln.parallel) {
      if (!buf) {
        wrap.appendChild(el('div', 'pp-fork', 'Fork: lanes run in parallel'));
        buf = el('div', 'pp-lanes');
        wrap.appendChild(buf);
      }
      buf.appendChild(ppLaneCard(ln, its, chats));
    } else {
      if (buf) { wrap.appendChild(el('div', 'pp-fork', 'Join: both lanes feed the last step (inferred)')); buf = null; }
      wrap.appendChild(ppLaneCard(ln, its, chats));
    }
  });
  root.appendChild(wrap);

  const lg = el('div', 'pp-sec');
  lg.appendChild(el('h2', '', 'How to read it'));
  const ul = el('ul', 'pp-legend');
  [['VERIFIED', 'The proof the stage needs is in hand and still applies.'], ['SUBMITTED', 'Output exists. The checking it needs is not complete.'],
   ['BLOCKED', 'A decision or prerequisite is stopping it.'], ['NOT_STARTED', 'A known stage with no sign of a start.']].forEach(([k, text]) => {
    const li = el('li', PP_CLS[k]);
    li.appendChild(el('span', 'pp-ic', PP_SYM[k]));
    const sp = el('span');
    sp.appendChild(el('strong', '', k + ' '));
    sp.appendChild(document.createTextNode(text));
    li.appendChild(sp);
    ul.appendChild(li);
  });
  lg.appendChild(ul);
  lg.appendChild(el('p', 'note', 'A milestone is BLOCKED if any of its stages is, else it takes the weakest state of its stages. Chat chips show the ChatGPT chat id (first 8 characters) that owns a stage; this public page never links a chat.'));
  root.appendChild(lg);
}

export {ppDrawProgress};
