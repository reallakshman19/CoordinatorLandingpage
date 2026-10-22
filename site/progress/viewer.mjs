// PRG-CORE-1 Stage 2. Portable version-isolated module graph.
const v = new URL(import.meta.url).search;
const {el, PP_VIEWS, ppOpenActions, ppFmtTime, ppAgeText} = await import('./helpers.mjs' + v);
const {ppPages, ppBundle} = await import('./data.mjs' + v);
const {ppDrawActions} = await import('./actions.mjs' + v);
const {ppDrawProgress} = await import('./progress.mjs' + v);
const {ppDrawFixtures} = await import('./fixtures.mjs' + v);
const {ppDrawOverview} = await import('./overview.mjs' + v);
let navigate = hash => { window.location.hash = hash; };
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

export async function mountProgress(root, {base, projectsUrl, route, navigate: go, enrichers} = {}) {
  void enrichers; // reserved for the optional P2 bridge; the core never calls it.
  const css = new URL('./progress.css' + v, import.meta.url).href;
  let style = document.querySelector('link[data-progress-style]');
  if (!style) {
    style = document.createElement('link'); style.rel = 'stylesheet';
    style.dataset.progressStyle = 'true'; document.head.appendChild(style);
  }
  if (style.href !== css) style.href = css;
  navigate = typeof go === 'function' ? go : hash => { window.location.hash = hash; };
  const dataBase = String(base || new URL('../progress-data', import.meta.url).href).replace(/\/$/, '');
  const pages = await ppPages(projectsUrl || dataBase + '/projects.json', dataBase);
  const fields = String(route || location.hash || '#progress-page').replace(/^#/, '').split('/');
  const page = pages.find(p => p.key === fields[1]) || pages[0];
  const isView = key => PP_VIEWS.some(([v]) => v === key);
  const topic = fields[2] && !isView(fields[2]) ? fields[2] : 'overview';
  const view = topic === 'overview' ? 'actions' :
    isView(fields[3]) ? fields[3] : page.mode === 'standalone-oracle' ? 'fixtures' : 'actions';
  let timer = null, disposed = false, bundle = null, drawnSig = '';
  root.textContent = '';
  const panel = el('section', 'pp'); panel.id = 'view-progress-page';
  panel.appendChild(el('h1', '', 'Progress page'));
  const tabs = el('div', 'pp-subtabs');
  tabs.setAttribute('role','tablist'); tabs.setAttribute('aria-label','Progress pages');
  pages.forEach(p => {
    const b = el('button', 'pp-subtab' + (p === page ? ' active' : ''), p.label);
    b.type='button'; b.setAttribute('role','tab');
    b.setAttribute('aria-selected',p === page ? 'true':'false');
    b.addEventListener('click',()=>navigate('#progress-page/'+p.key+'/overview'));
    tabs.appendChild(b);
  });
  panel.appendChild(tabs);
  const body = el('div','pp-body'); panel.appendChild(body); root.appendChild(panel);
  const draw = st => { if (!disposed) ppDrawProject(body, page, topic, view, st); };
  draw({loading:true});
  async function load() {
    try {
      const next = await ppBundle(page);
      if (disposed) return;
      bundle = next;
      if (next.sig !== drawnSig) { drawnSig = next.sig; draw({bundle:next}); }
      else ppLiveBadge(body.querySelector('#pp-live') || el('span'), next.index.project);
    } catch(e) { draw({error:e.message, bundle}); }
  }
  await load();
  if (!disposed) timer = setInterval(() => {
    if (document.hidden || !root.isConnected) return;
    load();
  }, 120000);
  return () => { disposed=true; if(timer) clearInterval(timer); };
}
