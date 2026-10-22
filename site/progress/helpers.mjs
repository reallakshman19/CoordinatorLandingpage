// DOM-safe shared renderer primitives; all user data enters through textContent.
export function el(tag, cls, text) { const n=document.createElement(tag); if(cls) n.className=cls; if(text!=null) n.textContent=text; return n; }
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
function ppOwnerRecipient(ctx) {
  return ctx && ctx.mode === 'standalone-oracle' ? 'Oracle' : (ctx.replyTo?.target || 'OwnerTeammember');
}
function ppSendUrl(ctx, text) {
  const cfg = ctx.replyTo || {kind: 'none'};
  if (cfg.kind !== 'github-issue') return '';
  const type = ctx.type || 'DECISION';
  const label = ctx.label || `${type} ${ctx.topic ? ctx.topic + ':' : ''}${ctx.card}/${ctx.option}`;
  const params = new URLSearchParams({
    template: cfg.template,
    title: `[Owner input] ${label} (${ctx.project})`,
    labels: 'owner-input',
    project: ctx.project,
    target: ppOwnerRecipient(ctx),
    type,
    text,
    evidence_link: `${cfg.site}#progress-page/${ctx.page}/${ctx.topic || 'overview'}/${ctx.view || 'actions'}`,
  });
  return `https://github.com/${cfg.repo}/issues/new?${params}`;
}

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
  if (ctx?.replyTo?.kind === 'github-issue') {
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


export { PP_VIEWS, PP_FIX_LEFT, PP_FIX_RIGHT, PP_SYM, PP_CLS, PP_FIX_CLS, PP_LABELS, PP_NUMWORD, ppRich, ppSafeUrl, ppLink, ppList, ppFmtTime, ppAgeText, ppRollup, ppMilestones, ppOpenActions, ppOwnerRecipient, ppSendUrl, ppTable, ppReplyBox, ppOption, ppActionCard, ppAllCard, ppPlainList };
