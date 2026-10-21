/**
 * progress_page.js — "Progress page" tab: one sub-tab per project progress view.
 * Today there is one: "G9v3.5 Pilot Progress", with two views, "My actions" and "Progress".
 *
 * Data: the body of a GitHub issue (a ```json block that OTM rewrites at each event), read live
 * from the browser, so a change shows within a couple of minutes without a Pages deploy.
 * Public repository: chat ids appear as id8 only and no ChatGPT chat is ever linked.
 * Read-only: this view never posts, accepts or changes a stage. Replies are copied, not sent.
 * Routes: #progress-page, #progress-page/g9v35, #progress-page/g9v35/progress
 */

'use strict';

const PP_PAGES = [
  { key: 'g9v35', label: 'G9v3.5 Pilot Progress', issue: 138 },
];
const PP_POLL_MS = 120000;
const PP_FRESH_MS = 60000;
const PP_SYM = { VERIFIED: '✓', SUBMITTED: '↑', IN_PROGRESS: '◐', BLOCKED: '!', NOT_STARTED: '○', STALE: '↻', UNKNOWN: '?', NOT_APPLICABLE: '–', PARTIAL: '◑' };
const PP_CLS = { VERIFIED: 'pp-ok', SUBMITTED: 'pp-sbm', IN_PROGRESS: 'pp-wip', BLOCKED: 'pp-blk', NOT_STARTED: 'pp-idle', STALE: 'pp-wip', UNKNOWN: 'pp-idle', NOT_APPLICABLE: 'pp-idle', PARTIAL: 'pp-sbm' };
const PP_LABELS = [['who', 'Who'], ['do', 'Do'], ['why', 'Why'], ['files', 'Files'], ['status', 'Status'], ['still', 'Still current'], ['waits', 'Waits for'], ['result', 'Result'], ['done', 'Done when'], ['next', 'Next']];
const PP_NUMWORD = ['zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine'];
const ppState = { timer: null, cache: {}, drawnKey: {} };

// ── helpers ───────────────────────────────────────────────
function ppRich(node, text) {
  String(text == null ? '' : text).split('`').forEach((part, i) => {
    if (!part) return;
    if (i % 2 === 1) node.appendChild(el('code', '', part));
    else node.appendChild(document.createTextNode(part));
  });
  return node;
}
function ppSafeUrl(u) { return typeof u === 'string' && /^https:\/\//.test(u) ? u : ''; }
function ppLink(href, text, cls) {
  const u = ppSafeUrl(href);
  const a = el(u ? 'a' : 'span', cls || '', text);
  if (u) { a.href = u; a.target = '_blank'; a.rel = 'noopener noreferrer'; }
  return a;
}
function ppList(obj) {
  return Object.keys(obj || {}).map(k => Object.assign({}, obj[k], { id: k }))
    .sort((a, b) => (a.order || 0) - (b.order || 0));
}
function ppFmtTime(iso) {
  const d = new Date(iso);
  if (isNaN(d.getTime())) return '';
  try {
    return new Intl.DateTimeFormat('en-GB', { timeZone: 'Asia/Dubai', day: 'numeric', month: 'short',
      hour: '2-digit', minute: '2-digit', hour12: false }).format(d) + ' Dubai';
  } catch { return d.toISOString(); }
}
function ppAgeText(min) { return min < 60 ? `${min} min` : `${Math.floor(min / 60)} h ${min % 60} min`; }
function ppRollup(states) {
  if (!states.length) return 'NOT_STARTED';
  if (states.includes('BLOCKED')) return 'BLOCKED';
  if (states.every(s => s === 'VERIFIED' || s === 'NOT_APPLICABLE')) return 'VERIFIED';
  if (states.includes('IN_PROGRESS')) return 'IN_PROGRESS';
  if (states.includes('STALE') || states.includes('UNKNOWN')) return 'UNKNOWN';
  if (states.includes('SUBMITTED')) return 'SUBMITTED';
  if (states.every(s => s === 'NOT_STARTED')) return 'NOT_STARTED';
  return 'PARTIAL';
}

// ── data ──────────────────────────────────────────────────
async function ppLoad(page) {
  const cached = ppState.cache[page.key];
  if (cached && Date.now() - cached.fetchedAt < PP_FRESH_MS) return cached;
  const r = await fetch(`https://api.github.com/repos/${REPO}/issues/${page.issue}`,
    { headers: { Accept: 'application/vnd.github+json' }, cache: 'no-store' });
  if (!r.ok) {
    throw new Error(r.status === 403 || r.status === 429
      ? 'GitHub is limiting requests from this network; it retries by itself' : `GitHub answered ${r.status}`);
  }
  const issue = await r.json();
  const m = /```json\s*([\s\S]*?)```/.exec(issue.body || '');
  if (!m) throw new Error('the data issue has no JSON block yet');
  const data = JSON.parse(m[1]);
  const result = { data, fetchedAt: Date.now(), issueUpdated: issue.updated_at };
  ppState.cache[page.key] = result;
  return result;
}

// ── shared pieces ─────────────────────────────────────────
function ppTable(t) {
  const wrap = el('div', 'table-wrap pp-tw');
  const tb = el('table', 'pp-table');
  const tr = el('tr');
  (t.cols || []).forEach(c => tr.appendChild(el('th', '', c)));
  tb.appendChild(el('thead')).appendChild(tr);
  const body = el('tbody');
  (t.rows || []).forEach(r => {
    const row = el('tr');
    r.forEach((cell, i) => row.appendChild(ppRich(el('td', t.mono && t.mono[i] ? 'pp-mono' : ''), cell)));
    body.appendChild(row);
  });
  tb.appendChild(body);
  wrap.appendChild(tb);
  return wrap;
}
function ppReplyBox(text) {
  const w = el('div', 'pp-replybox');
  const pre = el('pre', 'pp-reply', text);
  const b = el('button', 'btn btn-small', 'Copy reply');
  b.type = 'button';
  b.addEventListener('click', async () => {
    const done = msg => { b.textContent = msg; setTimeout(() => { b.textContent = 'Copy reply'; }, 2400); };
    try { await navigator.clipboard.writeText(text); done('Copied'); }
    catch {
      const range = document.createRange();
      range.selectNodeContents(pre);
      const sel = window.getSelection();
      sel.removeAllRanges(); sel.addRange(range);
      done('Selected: press Ctrl+C');
    }
  });
  w.appendChild(pre); w.appendChild(b);
  return w;
}
function ppOption(o) {
  const d = el('div', 'pp-opt' + (o.suggested ? ' pp-rec' : ''));
  const lab = el('div', 'pp-olabel');
  lab.appendChild(el('b', '', o.label || o.key));
  if (o.suggested) lab.appendChild(el('span', 'pp-rectag', 'suggested'));
  d.appendChild(lab);
  const body = el('div', 'pp-obody');
  if (o.body) body.appendChild(ppRich(el('p'), o.body));
  if (o.steps && o.steps.length) {
    const ol = el('ol', 'pp-steps');
    o.steps.forEach(s => ol.appendChild(ppRich(el('li'), s)));
    body.appendChild(ol);
  }
  if (o.reply) body.appendChild(ppReplyBox(o.reply));
  d.appendChild(body);
  return d;
}
function ppActionCard(a) {
  const c = el('article', 'card pp-dcard');
  c.id = 'pp-act-' + a.id;
  const head = el('div', 'pp-dhead');
  (a.stages || []).forEach(s => head.appendChild(el('span', 'pp-sid', s)));
  head.appendChild(el('span', 'pp-who pp-you', 'YOU'));
  head.appendChild(el('h3', '', a.title || a.id));
  c.appendChild(head);
  if (a.lead) c.appendChild(ppRich(el('p', 'pp-lead'), a.lead));
  (a.tables || []).forEach(t => c.appendChild(ppTable(t)));
  if (a.ask) c.appendChild(ppRich(el('p', 'pp-ask'), a.ask));
  (a.options || []).forEach(o => c.appendChild(ppOption(o)));
  if (a.links && a.links.length) {
    const n = el('p', 'note', 'Links: ');
    a.links.forEach((l, i) => { if (i) n.appendChild(document.createTextNode(', ')); n.appendChild(ppLink(l.u, l.l)); });
    c.appendChild(n);
  }
  return c;
}
function ppAllCard(open) {
  const parts = [];
  open.forEach(a => {
    const o = (a.options || []).find(x => x.suggested);
    if (o) parts.push(o.short || o.reply);
  });
  if (parts.length < 2) return null;
  const word = PP_NUMWORD[parts.length] || String(parts.length);
  const c = el('article', 'card pp-dcard pp-all');
  c.appendChild(el('h3', '', `Answer all ${word} at once`));
  c.appendChild(el('p', 'pp-lead', 'This joins the suggested reply of each open card. Fill any square brackets, then send it to OTM.'));
  c.appendChild(ppReplyBox(`All ${word}: ${parts.join(' ')}`));
  return c;
}
function ppPlainList(items) {
  const ul = el('ul', 'pp-plain');
  items.forEach(fn => ul.appendChild(fn()));
  return ul;
}

// ── view 1: My actions ────────────────────────────────────
function ppDrawActions(root, D) {
  const acts = ppList(D.actions);
  const open = acts.filter(a => a.status === 'open');
  const done = acts.filter(a => a.status === 'done');
  const sec = el('div', 'pp-sec');
  sec.appendChild(el('h2', '', 'Do now'));
  if (!open.length) {
    sec.appendChild(el('div', 'pp-empty', 'Nothing waits on you right now. When an agent or OTM needs a decision, it appears here with the files involved and a reply to copy.'));
  } else {
    sec.appendChild(el('p', 'pp-intro', `${open.length} open. Each card says what to reply. Paste your reply in the chat with OTM, and OTM records it and moves the work on.`));
    open.forEach(a => sec.appendChild(ppActionCard(a)));
    const all = ppAllCard(open);
    if (all) sec.appendChild(all);
  }
  root.appendChild(sec);

  const covered = {};
  open.forEach(a => (a.stages || []).forEach(s => { covered[s] = true; }));
  const coming = ppList(D.stages).filter(s => s.actor === 'YOU' && s.state !== 'VERIFIED' && !covered[s.id]);
  if (coming.length) {
    const cs = el('div', 'pp-sec');
    cs.appendChild(el('h2', '', 'Coming up for you'));
    cs.appendChild(ppPlainList(coming.map(s => () => {
      const li = el('li');
      const t = el('div', 'pp-pt');
      t.appendChild(el('span', 'pp-sid', s.id + ' '));
      t.appendChild(document.createTextNode(s.name || s.id));
      li.appendChild(t);
      if (s.sub) li.appendChild(ppRich(el('div', 'pp-ps'), s.sub));
      const det = s.detail || {};
      if (det.do) li.appendChild(ppRich(el('div', 'pp-ps'), 'Do: ' + det.do));
      if (det.waits) li.appendChild(ppRich(el('div', 'pp-ps'), 'Waits for: ' + det.waits));
      return li;
    })));
    root.appendChild(cs);
  }
  if (done.length) {
    const ds = el('div', 'pp-sec');
    ds.appendChild(el('h2', '', 'Answered'));
    ds.appendChild(ppPlainList(done.map(a => () => {
      const li = el('li');
      li.appendChild(el('div', 'pp-pt', a.title || a.id));
      const ans = a.answer || {};
      if (ans.text) li.appendChild(ppRich(el('div', 'pp-ps'), 'Your answer: ' + ans.text));
      const meta = el('div', 'pp-ps');
      if (ans.at) meta.appendChild(document.createTextNode('Recorded ' + ppFmtTime(ans.at) + '. '));
      if (ans.ref) meta.appendChild(ppLink(ans.ref, 'Record on GitHub'));
      if (meta.childNodes.length) li.appendChild(meta);
      return li;
    })));
    root.appendChild(ds);
  }
}

// ── view 2: Progress ──────────────────────────────────────
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
function ppDrawProgress(root, D) {
  const stages = ppList(D.stages);
  if (!stages.length) { root.appendChild(el('div', 'pp-empty', 'OTM has not written the stage list yet.')); return; }
  const sec = el('div', 'pp-sec');
  sec.appendChild(el('h2', '', 'Milestones'));
  const strip = el('div', 'pp-mstrip');
  strip.setAttribute('role', 'list');
  ppList((D.meta || {}).milestones).forEach((m, i) => {
    const its = stages.filter(s => s.milestone === m.id);
    const st = ppRollup(its.map(s => s.state));
    if (i) { const ch = el('span', 'pp-chev', '›'); ch.setAttribute('aria-hidden', 'true'); strip.appendChild(ch); }
    const card = el('div', 'pp-mcard ' + (PP_CLS[st] || 'pp-idle'));
    card.setAttribute('role', 'listitem');
    if (m.full) card.title = m.full;
    const mh = el('div', 'pp-mh');
    const ic = el('span', 'pp-mic', PP_SYM[st] || '?');
    ic.setAttribute('aria-hidden', 'true');
    mh.appendChild(ic);
    mh.appendChild(document.createTextNode(m.id));
    card.appendChild(mh);
    card.appendChild(el('div', 'pp-mn', m.name || m.id));
    card.appendChild(el('div', 'pp-ms', st));
    card.appendChild(el('div', 'pp-mc', `${its.filter(s => s.state === 'VERIFIED').length} of ${its.length} verified`));
    strip.appendChild(card);
  });
  sec.appendChild(strip);
  const tally = { VERIFIED: 0, SUBMITTED: 0, BLOCKED: 0, NOT_STARTED: 0, other: 0 };
  stages.forEach(s => { if (s.state in tally) tally[s.state]++; else tally.other++; });
  sec.appendChild(el('p', 'pp-counts', `${tally.VERIFIED} verified · ${tally.SUBMITTED} submitted · ${tally.BLOCKED} blocked · ${tally.NOT_STARTED} not started${tally.other ? ` · ${tally.other} other` : ''} of ${stages.length} inferred stages. A stage count on a partial list, not a delivery percentage.`));
  root.appendChild(sec);

  const wrap = el('div', 'pp-lanewrap');
  let buf = null;
  ppList((D.meta || {}).lanes).forEach(ln => {
    const its = stages.filter(s => s.lane === ln.id);
    if (!its.length) return;
    if (ln.parallel) {
      if (!buf) {
        wrap.appendChild(el('div', 'pp-fork', 'Fork: lanes run in parallel'));
        buf = el('div', 'pp-lanes');
        wrap.appendChild(buf);
      }
      buf.appendChild(ppLaneCard(ln, its, D.chats));
    } else {
      if (buf) { wrap.appendChild(el('div', 'pp-fork', 'Join: both lanes feed the last step (inferred)')); buf = null; }
      wrap.appendChild(ppLaneCard(ln, its, D.chats));
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

// ── page frame ────────────────────────────────────────────
function ppLiveBadge(badge, meta, err) {
  const m = meta || {};
  let cls = 'pp-badge', text;
  if (!m.updatedAt) { text = err ? 'No data' : 'Waiting for data'; }
  else {
    const age = Math.max(0, Math.round((Date.now() - new Date(m.updatedAt).getTime()) / 60000));
    const stale = age > (m.staleAfterMin || 120);
    cls += stale ? ' pp-stale' : ' pp-live';
    text = (stale ? `Not updated for ${ppAgeText(age)}, last ` : 'Live, updated ') + ppFmtTime(m.updatedAt) + (m.updatedBy ? ' by ' + m.updatedBy : '');
  }
  badge.className = cls;
  badge.textContent = text;
}
function ppDrawPilot(body, page, tab, st) {
  body.textContent = '';
  const D = st.data && st.data.data;
  const head = el('div', 'pp-top');
  const titles = el('div');
  titles.appendChild(el('h2', 'pp-title', (D && D.meta && D.meta.title) || page.label));
  titles.appendChild(el('p', 'pp-sub', (D && D.meta && D.meta.subtitle) || ''));
  head.appendChild(titles);
  const badges = el('div', 'pp-badges');
  const live = el('span', 'pp-badge');
  live.id = 'pp-live';
  ppLiveBadge(live, D && D.meta, st.error);
  badges.appendChild(live);
  badges.appendChild(el('span', 'pp-badge', 'Read-only'));
  head.appendChild(badges);
  body.appendChild(head);

  const tabs = el('div', 'pp-tabs');
  tabs.setAttribute('role', 'tablist');
  const openCount = D ? ppList(D.actions).filter(a => a.status === 'open').length : 0;
  [['actions', 'My actions'], ['progress', 'Progress']].forEach(([key, label]) => {
    const b = el('button', 'pp-tab' + (key === tab ? ' active' : ''), label);
    b.type = 'button';
    b.setAttribute('role', 'tab');
    b.setAttribute('aria-selected', key === tab ? 'true' : 'false');
    if (key === 'actions') b.appendChild(el('span', 'pp-count' + (openCount ? '' : ' pp-zero'), String(openCount)));
    b.addEventListener('click', () => navigate(`#progress-page/${page.key}/${key}`));
    tabs.appendChild(b);
  });
  body.appendChild(tabs);

  if (st.error) body.appendChild(el('div', 'pp-banner pp-bad', `Could not refresh: ${st.error}.` + (D ? ' Showing the last data received.' : '')));
  else if (D && D.meta && D.meta.updatedAt) {
    const age = Math.round((Date.now() - new Date(D.meta.updatedAt).getTime()) / 60000);
    if (age > (D.meta.staleAfterMin || 120)) body.appendChild(el('div', 'pp-banner', `OTM has not written an update for ${ppAgeText(age)}, so the states below may be out of date.`));
  }
  const panel = el('div', 'pp-panel');
  if (st.loading) panel.appendChild(el('div', 'loading', 'Loading live progress…'));
  else if (!D) panel.appendChild(el('div', 'pp-empty', 'No data to show yet.'));
  else if (tab === 'progress') ppDrawProgress(panel, D);
  else ppDrawActions(panel, D);
  body.appendChild(panel);
  body.appendChild(el('p', 'note pp-foot', 'Stage states are written by OTM, the Owner\'s teammate session, at each event, and read from GitHub issue #' + page.issue + ' every two minutes. The stage list is inferred from the Oracle\'s packets. This page changes nothing on GitHub.'));
}

async function renderProgressPage(app, pageKey, tabKey) {
  if (ppState.timer) { clearInterval(ppState.timer); ppState.timer = null; }
  const page = PP_PAGES.find(p => p.key === pageKey) || PP_PAGES[0];
  const tab = tabKey === 'progress' ? 'progress' : 'actions';
  app.textContent = '';
  const root = el('section', 'pp');
  root.id = 'view-progress-page';
  root.appendChild(el('h1', '', 'Progress page'));
  const subtabs = el('div', 'pp-subtabs');
  subtabs.setAttribute('role', 'tablist');
  subtabs.setAttribute('aria-label', 'Progress pages');
  PP_PAGES.forEach(p => {
    const b = el('button', 'pp-subtab' + (p === page ? ' active' : ''), p.label);
    b.type = 'button';
    b.setAttribute('role', 'tab');
    b.setAttribute('aria-selected', p === page ? 'true' : 'false');
    b.addEventListener('click', () => navigate(`#progress-page/${p.key}/${tab}`));
    subtabs.appendChild(b);
  });
  root.appendChild(subtabs);
  const body = el('div', 'pp-body');
  root.appendChild(body);
  app.appendChild(root);

  const draw = st => { ppDrawPilot(body, page, tab, st); };
  const cacheKey = r => r ? `${r.issueUpdated}|${(r.data.meta || {}).updatedAt}` : '';
  const known = ppState.cache[page.key];
  draw(known ? { data: known } : { loading: true });
  ppState.drawnKey[page.key] = cacheKey(known);
  const load = async () => {
    try {
      const r = await ppLoad(page);
      if (cacheKey(r) !== ppState.drawnKey[page.key]) { ppState.drawnKey[page.key] = cacheKey(r); draw({ data: r }); }
      else ppLiveBadge(document.getElementById('pp-live') || el('span'), r.data.meta);
    } catch (e) {
      draw({ error: e.message, data: ppState.cache[page.key] });
    }
  };
  await load();
  ppState.timer = setInterval(() => {
    if (!location.hash.startsWith('#progress-page') || document.hidden) return;
    load();
  }, PP_POLL_MS);
}
