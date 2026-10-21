/**
 * progress_page.js — "Progress page" tab: one sub-tab per project progress view.
 * The sub-tabs are listed in site/progress-data/projects.json (today one: "G9v3.5 Pilot Progress"); adding a project needs no code change. It holds the children (topics) of the pilot, for example
 * "G9v3.5 Physics pilot-NLM", plus the shared tooling. Each topic has three views:
 * My actions (what the Owner must do), Progress (milestones and stages) and Grounding fixtures.
 * An Overview shows every topic side by side.
 *
 * Data: JSON files in a folder tree beside the site, site/progress-data/<project>/index.json (project, chats,
 * topic list) and <topic>/{meta,stages,actions,fixtures}.json. OTM rewrites them at each event; the page
 * fetches them again every two minutes, so a change shows after the next Pages build.
 * Public repository: chat ids appear as id8 only and no ChatGPT chat is ever linked.
 * Read-only: this view never posts or changes a stage. "Send to OTM" (and the + and - on a fixture) only
 * open GitHub's Owner Reply form with text filled in; the Owner submits it.
 * Routes: #progress-page, #progress-page/<page>, #progress-page/<page>/<topic>[/<view>]
 *   topic: overview (default) or a topic key; view: actions | progress | fixtures
 */

'use strict';

// The sub-tabs come from progress-data/projects.json; this entry is only the fallback if that file cannot be read.
const PP_DEFAULT_PAGES = [
  { key: 'g9v35', label: 'G9v3.5 Pilot Progress', project: 'g9v35', data: 'progress-data/g9v35' },
];
async function ppPages() {
  try {
    const r = await fetch('progress-data/projects.json', { cache: 'no-cache' });
    if (!r.ok) throw new Error(String(r.status));
    const j = await r.json();
    const list = (j.projects || [])
      .filter(p => p && /^[a-z0-9][a-z0-9-]*$/.test(p.key || '') && p.label)
      .sort((a, b) => (a.order || 0) - (b.order || 0))
      .map(p => ({ key: p.key, label: p.label, project: p.project || p.key,
        mode: p.mode === 'standalone-oracle' ? 'standalone-oracle' : 'coordinator',
        data: `progress-data/${p.key}` }));
    if (list.length) return list;
  } catch { /* use the fallback below */ }
  return PP_DEFAULT_PAGES;
}
const PP_SITE = 'https://reallakshman19.github.io/CoordinatorLandingpage/';
const PP_POLL_MS = 120000;
const PP_VIEWS = [['actions', 'My actions'], ['progress', 'Progress'], ['fixtures', 'Grounding fixtures']];
const PP_FIX_LEFT = [
  ['repository', 'Repository / project link'], ['issues', 'Issue / assignment links'],
  ['pullRequests', 'Pull request / candidate links'], ['roadmap', 'Roadmap / governing documents'],
  ['highRoi', 'High ROI: proposed and implemented'], ['future', 'Future improvements'],
];
const PP_FIX_RIGHT = [
  ['intent', 'Owner intent'], ['inputs', 'Other inputs, files and source notes'],
  ['knownIssues', 'Known issues'], ['pending', 'Pending items'],
];
const PP_SYM = { VERIFIED: '✓', SUBMITTED: '↑', IN_PROGRESS: '◐', BLOCKED: '!', NOT_STARTED: '○', STALE: '↻', UNKNOWN: '?', NOT_APPLICABLE: '–', PARTIAL: '◑' };
const PP_CLS = { VERIFIED: 'pp-ok', SUBMITTED: 'pp-sbm', IN_PROGRESS: 'pp-wip', BLOCKED: 'pp-blk', NOT_STARTED: 'pp-idle', STALE: 'pp-wip', UNKNOWN: 'pp-idle', NOT_APPLICABLE: 'pp-idle', PARTIAL: 'pp-sbm' };
const PP_FIX_CLS = { implemented: 'pp-ok', proposed: 'pp-sbm', open: 'pp-blk', waiting: 'pp-idle', planned: 'pp-idle' };
const PP_LABELS = [['who', 'Who'], ['do', 'Do'], ['why', 'Why'], ['files', 'Files'], ['status', 'Status'], ['still', 'Still current'], ['waits', 'Waits for'], ['result', 'Result'], ['done', 'Done when'], ['next', 'Next']];
const PP_NUMWORD = ['zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine'];
const ppState = { timer: null, bundle: null, drawnSig: '' };

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
function ppMilestones(P) {
  const stages = ppList(P.stages);
  return ppList((P.topic || {}).milestones).map(m => {
    const its = stages.filter(s => s.milestone === m.id);
    return Object.assign({}, m, { state: ppRollup(its.map(s => s.state)), total: its.length,
      ok: its.filter(s => s.state === 'VERIFIED').length });
  });
}
function ppOpenActions(P) { return ppList(P.actions).filter(a => a.status === 'open'); }

// ── data ──────────────────────────────────────────────────
function ppHash(text) {
  let h = 5381;
  for (let i = 0; i < text.length; i++) h = ((h << 5) + h + text.charCodeAt(i)) | 0;
  return (h >>> 0).toString(36);
}
async function ppJson(path) {
  const r = await fetch(path, { cache: 'no-cache' });
  if (!r.ok) throw new Error(`${path}: HTTP ${r.status}`);
  const text = await r.text();
  return { data: JSON.parse(text), text };
}
async function ppBundle(page) {
  const idx = await ppJson(`${page.data}/index.json`);
  const topics = {}, errors = {};
  let sig = ppHash(idx.text);
  await Promise.all((idx.data.topics || []).filter(t => !t.planned).map(async t => {
    try {
      const parts = await Promise.all(['meta', 'stages', 'actions', 'fixtures'].map(n => ppJson(`${page.data}/${t.key}/${n}.json`)));
      const [meta, stages, actions, fixtures] = parts.map(p => p.data);
      topics[t.key] = { topic: Object.assign({ key: t.key, updatedAt: t.updatedAt }, meta), stages, actions, fixtures };
      sig += parts.map(p => ppHash(p.text)).join('');
    } catch (e) { errors[t.key] = e.message; }
  }));
  return { index: idx.data, topics, errors, sig: sig + '|' + Object.keys(errors).join(',') };
}

// ── Send to OTM: opens the Owner Reply form on GitHub, prefilled ──
// Nothing is posted from this page and no token is involved. The Owner ticks "I am the Owner" and submits.
function ppOwnerRecipient(ctx) {
  return ctx && ctx.mode === 'standalone-oracle' ? 'Oracle' : 'OwnerTeammember';
}
function ppSendUrl(ctx, text) {
  const type = ctx.type || 'DECISION';
  const label = ctx.label || `${type} ${ctx.topic ? ctx.topic + ':' : ''}${ctx.card}/${ctx.option}`;
  const params = new URLSearchParams({
    template: 'owner-reply.yml',
    title: `[Owner input] ${label} (${ctx.project})`,
    labels: 'owner-input',
    project: ctx.project,
    target: ppOwnerRecipient(ctx),
    type,
    text,
    evidence_link: `${PP_SITE}#progress-page/${ctx.page}/${ctx.topic || 'overview'}/${ctx.view || 'actions'}`,
  });
  return `${NEW_ISSUE_BASE}?${params}`;
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
function ppReplyBox(text, ctx) {
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
  const row = el('div', 'pp-sendrow');
  row.appendChild(b);
  if (ctx) {
    const a = el('a', 'btn btn-small btn-primary', `Send to ${ctx.mode === 'standalone-oracle' ? 'Oracle' : 'OTM'}`);
    a.href = ppSendUrl(ctx, text);
    a.target = '_blank';
    a.rel = 'noopener noreferrer';
    a.title = 'Opens GitHub with this reply filled in the Owner Reply form';
    row.appendChild(a);
    row.appendChild(el('span', 'pp-sendhint', 'Opens GitHub with this reply filled in. Tick "I am the Owner", then Submit new issue.'));
  }
  w.appendChild(pre); w.appendChild(row);
  return w;
}
function ppOption(o, a, ctx) {
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
  if (o.reply) body.appendChild(ppReplyBox(o.reply, Object.assign({}, ctx, { card: a.id, option: o.key })));
  d.appendChild(body);
  return d;
}
function ppActionCard(a, ctx, tag) {
  const c = el('article', 'card pp-dcard');
  c.id = `pp-act-${ctx.topic || 'x'}-${a.id}`;
  const head = el('div', 'pp-dhead');
  if (tag) head.appendChild(el('span', 'pp-topicchip', tag));
  (a.stages || []).forEach(s => head.appendChild(el('span', 'pp-sid', s)));
  head.appendChild(el('span', 'pp-who pp-you', 'YOU'));
  head.appendChild(el('h3', '', a.title || a.id));
  c.appendChild(head);
  if (a.lead) c.appendChild(ppRich(el('p', 'pp-lead'), a.lead));
  (a.tables || []).forEach(t => c.appendChild(ppTable(t)));
  if (a.ask) c.appendChild(ppRich(el('p', 'pp-ask'), a.ask));
  (a.options || []).forEach(o => c.appendChild(ppOption(o, a, ctx)));
  if (a.links && a.links.length) {
    const n = el('p', 'note', 'Links: ');
    a.links.forEach((l, i) => { if (i) n.appendChild(document.createTextNode(', ')); n.appendChild(ppLink(l.u, l.l)); });
    c.appendChild(n);
  }
  return c;
}
function ppAllCard(open, ctx) {
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
  c.appendChild(ppReplyBox(`All ${word}: ${parts.join(' ')}`, Object.assign({}, ctx, { card: 'ALL', option: 'suggested' })));
  return c;
}
function ppPlainList(items) {
  const ul = el('ul', 'pp-plain');
  items.forEach(fn => ul.appendChild(fn()));
  return ul;
}

// ── topic view 1: My actions ──────────────────────────────
function ppDrawActions(root, page, topicKey, P) {
  const ctx = { project: page.project, page: page.key, topic: topicKey, view: 'actions', mode: page.mode };
  const open = ppOpenActions(P);
  const done = ppList(P.actions).filter(a => a.status === 'done');
  const sec = el('div', 'pp-sec');
  sec.appendChild(el('h2', '', 'Do now'));
  if (!open.length) {
    sec.appendChild(el('div', 'pp-empty', 'Nothing waits on you in this topic. When an agent or OTM needs a decision, it appears here with the files involved and a reply to copy.'));
  } else {
    sec.appendChild(el('p', 'pp-intro', `${open.length} open. Each card says what to reply. Paste your reply in the chat with OTM, or use Send to OTM, and OTM records it and moves the work on.`));
    open.forEach(a => sec.appendChild(ppActionCard(a, ctx)));
    const all = ppAllCard(open, ctx);
    if (all) sec.appendChild(all);
  }
  root.appendChild(sec);

  const covered = {};
  open.forEach(a => (a.stages || []).forEach(s => { covered[s] = true; }));
  const coming = ppList(P.stages).filter(s => s.actor === 'YOU' && s.state !== 'VERIFIED' && !covered[s.id]);
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

// ── topic view 2: Progress ────────────────────────────────
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

// ── topic view 3: Grounding fixtures ──────────────────────
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
    mode: page.mode, type: 'INFO',
    label: `INFO fixture ${topicKey}/${key}`, card: key, option: 'fixture' };
  const s = el('section', 'pp-fsec');
  const h = el('div', 'pp-fhead');
  h.appendChild(el('h4', '', label));
  h.appendChild(ppFixLink(ctx, `FIXTURE ${topicKey}/${key} ADD: `, '+', 'Propose an addition (opens the GitHub Owner Reply form)'));
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
    line.appendChild(ppFixLink(ctx, `FIXTURE ${topicKey}/${key} REMOVE: ${e.t || ''}`, '−', 'Propose removing this entry (opens the GitHub Owner Reply form)'));
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

// ── overview ──────────────────────────────────────────────
function ppDrawOverview(root, page, B) {
  const topics = (B.index.topics || []).slice().sort((a, b) => (a.order || 0) - (b.order || 0));
  const open = [];
  topics.forEach(t => { const P = B.topics[t.key]; if (P) ppOpenActions(P).forEach(a => open.push({ t, a })); });

  const need = el('div', 'pp-sec');
  need.appendChild(el('h2', '', 'Needs you, across topics'));
  if (!open.length) {
    need.appendChild(el('div', 'pp-empty', 'Nothing waits on you in any topic.'));
  } else {
    const ul = el('ul', 'pp-plain');
    open.forEach(({ t, a }) => {
      const li = el('li');
      const head = el('div', 'pp-pt');
      head.appendChild(el('span', 'pp-topicchip', t.label));
      head.appendChild(document.createTextNode(' ' + (a.title || a.id)));
      li.appendChild(head);
      const go = el('a', 'btn btn-small', 'Open the card');
      go.href = `#progress-page/${page.key}/${t.key}/actions`;
      li.appendChild(go);
      ul.appendChild(li);
    });
    need.appendChild(ul);
    const all = ppAllCard(open.map(x => x.a), { project: page.project, page: page.key, topic: '', view: 'actions', mode: page.mode });
    if (all) need.appendChild(all);
  }
  root.appendChild(need);

  const sec = el('div', 'pp-sec');
  sec.appendChild(el('h2', '', 'Topics'));
  const ids = [];
  topics.forEach(t => { const P = B.topics[t.key]; if (P) ppMilestones(P).forEach(m => { if (!ids.includes(m.id)) ids.push(m.id); }); });
  ids.sort();
  const wrap = el('div', 'table-wrap pp-tw');
  const tb = el('table', 'pp-table pp-matrix');
  const hr = el('tr');
  ['Topic', ...ids, 'Verified', 'Blocked', 'Next on you'].forEach(c => hr.appendChild(el('th', '', c)));
  tb.appendChild(el('thead')).appendChild(hr);
  const body = el('tbody');
  topics.forEach(t => {
    const P = B.topics[t.key];
    const row = el('tr');
    const first = el('td');
    const a = el('a', 'pp-toplink', (P && P.topic && P.topic.title) || t.title || t.label);
    a.href = `#progress-page/${page.key}/${t.key}/progress`;
    first.appendChild(a);
    row.appendChild(first);
    if (!P) {
      const td = el('td', 'pp-planned', B.errors[t.key] ? 'Could not load: ' + B.errors[t.key] : t.planned ? 'Planned: no data yet' : 'Loading');
      td.colSpan = ids.length + 3;
      row.appendChild(td);
    } else {
      const ms = ppMilestones(P);
      ids.forEach(id => {
        const m = ms.find(x => x.id === id);
        const td = el('td', 'pp-mcell');
        if (m) {
          const c = el('span', 'pp-mini ' + PP_CLS[m.state], PP_SYM[m.state]);
          c.title = `${m.id} ${m.name}: ${m.state}, ${m.ok} of ${m.total} verified`;
          td.appendChild(c);
        } else td.textContent = '–';
        row.appendChild(td);
      });
      const stages = ppList(P.stages);
      row.appendChild(el('td', '', `${stages.filter(s => s.state === 'VERIFIED').length} of ${stages.length}`));
      row.appendChild(el('td', '', String(stages.filter(s => s.state === 'BLOCKED').length)));
      const o = ppOpenActions(P)[0];
      row.appendChild(el('td', '', o ? o.title : '–'));
    }
    body.appendChild(row);
  });
  tb.appendChild(body);
  wrap.appendChild(tb);
  sec.appendChild(wrap);
  sec.appendChild(el('p', 'note', 'Each topic is a child of the pilot and has its own My actions, Progress and Grounding fixtures. Shared tooling holds what every topic depends on. A new topic, for example Motion in 1D, appears here as soon as OTM creates it.'));
  root.appendChild(sec);
}

// ── page frame ────────────────────────────────────────────
function ppLiveBadge(badge, project, err) {
  const m = project || {};
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
function ppDrawProject(body, page, topic, view, st) {
  body.textContent = '';
  const B = st.bundle;
  const project = B && B.index && B.index.project;
  const head = el('div', 'pp-top');
  const titles = el('div');
  titles.appendChild(el('h2', 'pp-title', (project && project.title) || page.label));
  titles.appendChild(el('p', 'pp-sub', (project && project.subtitle) || ''));
  head.appendChild(titles);
  const badges = el('div', 'pp-badges');
  const live = el('span', 'pp-badge');
  live.id = 'pp-live';
  ppLiveBadge(live, project, st.error);
  badges.appendChild(live);
  badges.appendChild(el('span', 'pp-badge', 'Read-only'));
  head.appendChild(badges);
  body.appendChild(head);

  if (st.error) body.appendChild(el('div', 'pp-banner pp-bad', `Could not refresh: ${st.error}.` + (B ? ' Showing the last data received.' : '')));
  else if (project && project.updatedAt) {
    const age = Math.round((Date.now() - new Date(project.updatedAt).getTime()) / 60000);
    if (age > (project.staleAfterMin || 120)) {
      const writer = page.mode === 'standalone-oracle' ? 'the designated Oracle' : 'OTM';
      body.appendChild(el('div', 'pp-banner', `${writer} has not published an update for ${ppAgeText(age)}, so the states below may be out of date.`));
    }
  }
  if (st.loading || !B) {
    body.appendChild(el('div', 'loading', 'Loading live progress…'));
    return;
  }

  const topics = (B.index.topics || []).slice().sort((a, b) => (a.order || 0) - (b.order || 0));
  const bar = el('div', 'pp-topics');
  bar.setAttribute('role', 'tablist');
  bar.setAttribute('aria-label', 'Topics of the pilot');
  const totalOpen = topics.reduce((n, t) => n + (B.topics[t.key] ? ppOpenActions(B.topics[t.key]).length : 0), 0);
  const chip = (key, label, count, disabled) => {
    const b = el('button', 'pp-topic' + (key === topic ? ' active' : ''), label);
    b.type = 'button';
    b.setAttribute('role', 'tab');
    b.setAttribute('aria-selected', key === topic ? 'true' : 'false');
    if (disabled) { b.disabled = true; b.title = 'Planned: no data yet'; }
    if (count != null) b.appendChild(el('span', 'pp-count' + (count ? '' : ' pp-zero'), String(count)));
    b.addEventListener('click', () => navigate(key === 'overview' ? `#progress-page/${page.key}/overview` : `#progress-page/${page.key}/${key}/${view}`));
    return b;
  };
  bar.appendChild(chip('overview', 'Overview', totalOpen, false));
  topics.forEach(t => {
    const P = B.topics[t.key];
    bar.appendChild(chip(t.key, t.label, P ? ppOpenActions(P).length : null, !!t.planned));
  });
  body.appendChild(bar);

  const panel = el('div', 'pp-panel');
  if (topic === 'overview') {
    ppDrawOverview(panel, page, B);
  } else {
    const P = B.topics[topic];
    if (!P) {
      panel.appendChild(el('div', 'pp-empty', B.errors[topic] ? `Could not load this topic: ${B.errors[topic]}` : 'This topic has no data yet.'));
    } else {
      const th = el('div', 'pp-thead');
      th.appendChild(el('h3', '', P.topic.title || topic));
      if (P.topic.subtitle) th.appendChild(el('p', 'pp-sub', P.topic.subtitle));
      panel.appendChild(th);
      const tabs = el('div', 'pp-tabs');
      tabs.setAttribute('role', 'tablist');
      PP_VIEWS.forEach(([key, label]) => {
        const b = el('button', 'pp-tab' + (key === view ? ' active' : ''), label);
        b.type = 'button';
        b.setAttribute('role', 'tab');
        b.setAttribute('aria-selected', key === view ? 'true' : 'false');
        if (key === 'actions') { const n = ppOpenActions(P).length; b.appendChild(el('span', 'pp-count' + (n ? '' : ' pp-zero'), String(n))); }
        b.addEventListener('click', () => navigate(`#progress-page/${page.key}/${topic}/${key}`));
        tabs.appendChild(b);
      });
      panel.appendChild(tabs);
      const inner = el('div', 'pp-panel');
      if (view === 'progress') ppDrawProgress(inner, page, topic, P, B.index.chats);
      else if (view === 'fixtures') ppDrawFixtures(inner, page, topic, P);
      else ppDrawActions(inner, page, topic, P);
      panel.appendChild(inner);
    }
  }
  body.appendChild(panel);
  body.appendChild(el('p', 'note pp-foot', page.mode === 'standalone-oracle'
    ? `Standalone Oracle mode: agents must read their topic Grounding fixtures before starting; the Oracle maintains source-backed stages and a public audit under ${page.data}/; the Owner approves adoption. This is a read-only view, never a task runner.`
    : `Stage states are written by OTM, the Owner's teammate session, at each event, into JSON files under ${page.data}/ (index.json and one folder per topic) and read from there every two minutes. The stage list is inferred from the Oracle's packets. This page changes nothing on GitHub.`));
}

async function renderProgressPage(app, pageKey, a2, a3) {
  if (ppState.timer) { clearInterval(ppState.timer); ppState.timer = null; }
  const pages = await ppPages();
  const page = pages.find(p => p.key === pageKey) || pages[0];
  const isView = v => PP_VIEWS.some(x => x[0] === v);
  let topic = 'overview', view = 'actions';
  if (a2 && !isView(a2)) {
    topic = a2; view = isView(a3) ? a3 : (page.mode === 'standalone-oracle' ? 'fixtures' : 'actions');
  }   // an old link with only a view opens the overview
  app.textContent = '';
  const root = el('section', 'pp');
  root.id = 'view-progress-page';
  root.appendChild(el('h1', '', 'Progress page'));
  const subtabs = el('div', 'pp-subtabs');
  subtabs.setAttribute('role', 'tablist');
  subtabs.setAttribute('aria-label', 'Progress pages');
  pages.forEach(p => {
    const b = el('button', 'pp-subtab' + (p === page ? ' active' : ''), p.label);
    b.type = 'button';
    b.setAttribute('role', 'tab');
    b.setAttribute('aria-selected', p === page ? 'true' : 'false');
    b.addEventListener('click', () => navigate(`#progress-page/${p.key}/overview`));
    subtabs.appendChild(b);
  });
  root.appendChild(subtabs);
  const body = el('div', 'pp-body');
  root.appendChild(body);
  app.appendChild(root);

  const draw = st => { ppDrawProject(body, page, topic, view, st); };
  draw(ppState.bundle ? { bundle: ppState.bundle } : { loading: true });
  ppState.drawnSig = ppState.bundle ? ppState.bundle.sig : '';
  const load = async () => {
    try {
      const b = await ppBundle(page);
      ppState.bundle = b;
      if (b.sig !== ppState.drawnSig) { ppState.drawnSig = b.sig; draw({ bundle: b }); }
      else ppLiveBadge(document.getElementById('pp-live') || el('span'), b.index.project);
    } catch (e) {
      draw({ error: e.message, bundle: ppState.bundle });
    }
  };
  await load();
  ppState.timer = setInterval(() => {
    if (!location.hash.startsWith('#progress-page') || document.hidden) return;
    load();
  }, PP_POLL_MS);
}
