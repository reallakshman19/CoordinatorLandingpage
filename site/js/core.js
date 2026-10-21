/**
 * app.js — Team Protocol Owner Dashboard
 *
 * Pure vanilla JS, no frameworks.
 * Hash routing: #home, #project/<name>, #agent/<id8>, #timeline,
 *               #decision/<project>/<id>, #owner-inputs, #protocol,
 *               #benchmarks, #benchmark/<project>, #progress-page[/<page>[/<view>]]
 *
 * Data is loaded from site/data/*.json (pre-built by the GHA workflow).
 * In benchmark mode, data comes from site/data/benchmarks/*.json.
 *
 * IMPORTANT: this page never claims acceptance. It shows agent claims,
 * verdicts and Owner decisions, labelled as such.
 */

'use strict';

// ── Constants ─────────────────────────────────────────────
const REPO = 'reallakshman19/CoordinatorLandingpage';
const NEW_ISSUE_BASE = `https://github.com/${REPO}/issues/new`;
const DATA_BASE = 'data/';
const BM_DATA_BASE = 'data/benchmarks/';
// Read the commit stamped into this HTML, not the newest data fetch.
const LOADED_SITE_VERSION = document.querySelector('meta[name="site-version"]')?.content || null;

// ── State ──────────────────────────────────────────────────
const state = {
  projects: [],          // from projects.json
  timelines: {},         // { projectName: [events] }
  evidenceCache: {},     // { id8: agentData }
  benchmarkMode: false,
  benchmarkProject: null,
  dataBuiltAt: null,
  protocolMd: null,
  ownerInputs: null,
  ownerInputsLoaded: false,
  buildInfo: null,
  buildSignature: null,
  statusBar: null,
  pollInFlight: false,
  decisionDraft: null, // uncommitted form prefill, NEVER a recorded Owner answer
};

// ── DOM helpers ────────────────────────────────────────────
const $ = id => document.getElementById(id);
const el = (tag, cls, text) => {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (text != null) e.textContent = text;
  return e;
};
const html = (tag, cls, h) => {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (h) e.innerHTML = h;
  return e;
};
const cloneTemplate = id => document.getElementById(id).content.cloneNode(true);

// ── Data loading ───────────────────────────────────────────
async function fetchJSON(url, options = {}) {
  try {
    const r = await fetch(url, options);
    if (!r.ok) return null;
    return await r.json();
  } catch { return null; }
}

async function loadProjects() {
  const base = state.benchmarkMode ? BM_DATA_BASE : DATA_BASE;
  const data = await fetchJSON(base + 'projects.json', { cache: 'no-store' });
  if (!data) return;
  state.projects = data;
  state.dataBuiltAt = (!state.benchmarkMode && state.buildInfo?.built_at) || data[0]?.built_at || null;
}

async function loadTimeline(projectName) {
  if (state.timelines[projectName]) return state.timelines[projectName];
  const base = state.benchmarkMode ? BM_DATA_BASE : DATA_BASE;
  const data = await fetchJSON(base + `timeline-${projectName}.json`);
  if (!data) return [];
  state.timelines[projectName] = data.events || [];
  return state.timelines[projectName];
}

async function loadEvidence(id8) {
  if (state.evidenceCache[id8]) return state.evidenceCache[id8];
  const base = state.benchmarkMode ? BM_DATA_BASE : DATA_BASE;
  const data = await fetchJSON(base + `evidence-${id8}.json`);
  if (!data) return null;
  state.evidenceCache[id8] = data;
  return data;
}

async function loadProjectDetail(projectName) {
  const base = state.benchmarkMode ? BM_DATA_BASE : DATA_BASE;
  return await fetchJSON(base + `project-${projectName}.json`);
}

async function loadOwnerInputs() {
  if (state.benchmarkMode) return [];
  if (state.ownerInputsLoaded) return state.ownerInputs;
  const data = await fetchJSON(DATA_BASE + 'owner-inputs.json');
  state.ownerInputs = Array.isArray(data) ? data : null;
  state.ownerInputsLoaded = true;
  return state.ownerInputs;
}

// Read deployed build-info, not source repository commit timestamps.
// Poll every 60s, but fetch heavy JSON ONLY on a changed build signature.
// The page never sets published_at or asserts a deployment finished itself.
async function pollBuildInfo(initial = false) {
  if (state.pollInFlight) return false;
  state.pollInFlight = true;
  try {
    const info = await fetchJSON('build-info.json?read=' + Date.now(),
                                 { cache: 'no-store' });
    if (!info || typeof info !== 'object' ||
        typeof info.built_at !== 'string' ||
        typeof info.source_commit !== 'string' ||
        typeof info.run_id === 'undefined') return false;
    // A newer deployment may change JavaScript and CSS. Do not quietly run
    // old code on new data or discard an Owner's unfinished form.
    if (/^[0-9a-f]{8}$/.test(LOADED_SITE_VERSION || '') &&
        /^[0-9a-f]{8}$/.test(info.site_version || '') &&
        info.site_version !== LOADED_SITE_VERSION) {
      const banner = $('site-update-banner');
      const reload = $('site-update-reload');
      if (banner && reload) {
        const dest = new URL(window.location.href);
        dest.searchParams.set('v', info.site_version);
        reload.href = dest.toString(); // fresh index URL, same hash/route
        banner.hidden = false;
      }
      return false; // Owner decides when to reload; no background navigation
    }
    const signature = JSON.stringify([
      info.source_commit, info.source_capture_at, info.built_at,
      info.run_id, info.live_file_sha256,
    ]);
    if (state.buildSignature === signature) return false;
    const hadBuild = state.buildSignature !== null;
    state.buildInfo = info;
    state.buildSignature = signature;
    if (state.benchmarkMode) return false; // frozen snapshot stays frozen
    state.dataBuiltAt = info.built_at;
    if (hadBuild && !initial) {
      state.projects = [];
      state.timelines = {};
      state.evidenceCache = {};
    state.statusBar = null;
      state.ownerInputs = null;
      state.ownerInputsLoaded = false;
      await render(); // keep the current route, only refresh changed version
    }
    return hadBuild;
  } finally {
    state.pollInFlight = false;
  }
}


// WP10: report registry scopes but do not create delegated authority.

function ownerInputURL(opts = {}) {
  const params = new URLSearchParams({
    template: 'owner-input.yml',
    ...(opts.title ? { title: opts.title } : {}),
    ...(opts.labels ? { labels: opts.labels } : { labels: 'owner-input' }),
  });
  return `${NEW_ISSUE_BASE}?${params}`;
}

function groundURL(id8, project) {
  return ownerInputURL({
    title: `[Owner input] GROUND agent ${id8} (${project})`,
    labels: 'owner-input',
  });
}

function suggestURL(id8, project) {
  return ownerInputURL({
    title: `[Owner input] SUGGEST action for agent ${id8} (${project})`,
    labels: 'owner-input',
  });
}

function decisionURL(project, decisionId) {
  return ownerInputURL({
    title: `[Owner input] DECISION ${decisionId} (${project})`,
    labels: 'owner-input',
  });
}

function postToTeamURL(project, type) {
  return ownerInputURL({
    title: `[Owner input] ${type} (${project})`,
    labels: 'owner-input',
  });
}

// ── Formatting helpers ─────────────────────────────────────

function navigate(hash) {
  window.location.hash = hash;
}

function parseHash(h) {
  const parts = h.replace(/^#/, '').split('/');
  return {
    view: parts[0] || 'home',
    arg1: parts[1],
    arg2: parts[2],
  };
}

async function render() {
  const { view, arg1, arg2 } = parseHash(window.location.hash);

  // Update nav tabs
  document.querySelectorAll('.nav-tab').forEach(t => {
    t.classList.toggle('active', t.dataset.view === view);
  });

  const app = $('app');
  if (view === 'nextnudge' && !state.benchmarkMode &&
      app.querySelector('#nextnudge-frame')) return;
  app.innerHTML = '<div class="loading"><span class="spinner"></span> Loading…</div>';

  // Ensure projects are loaded
  if (!state.projects.length) {
    await loadProjects();
  }

  switch (view) {
    case 'home': await renderHome(app); break;
    case 'project': await renderProject(app, arg1); break;
    case 'understanding': await renderL4Understanding(app, arg1); break;
    case 'people': await renderL4People(app, arg1); break;
    case 'engineering-history': await renderL4EngineeringHistory(app, arg1); break;
    case 'sources': await renderL4Sources(app, arg1); break;
    case 'improvements': await renderL4Improvements(app, arg1); break;
    case 'changeover': await renderL4Changeover(app, arg1); break;
    case 'agent': await renderAgent(app, arg1, arg2); break;
    case 'timeline': await renderTimeline(app, arg1); break;
    case 'next-moves': await renderNextMoves(app); break;
    case 'nextnudge':
      await (await import(new URL('nextnudge/host.mjs', document.baseURI)))
        .renderNextNudge(app, state.benchmarkMode, LOADED_SITE_VERSION);
      break;
    case 'status-bar': await renderStatusBar(app); break;
    case 'progress-page': await renderProgressPage(app, arg1, arg2); break;
    case 'decision': await renderDecision(app, arg1, arg2); break;
    case 'owner-inputs': await renderOwnerInputs(app); break;
    case 'trace': await renderTrace(app, arg1); break;
    case 'protocol': await renderProtocol(app); break;
    case 'benchmarks': await renderBenchmarks(app); break;
    default: await renderHome(app);
  }
}

// ── Home view ──────────────────────────────────────────────

function init() {
  const nudgeTab = el('button', 'nav-tab', 'NextNudge · Beta');
  nudgeTab.dataset.view = 'nextnudge';
  nudgeTab.setAttribute('role', 'tab');
  $('nav-tabs').appendChild(nudgeTab);
  // Nav tab clicks
  document.querySelectorAll('.nav-tab').forEach(tab => {
    tab.addEventListener('click', () => {
      navigate('#' + tab.dataset.view);
    });
  });

  // Exit benchmark
  $('exit-benchmark').addEventListener('click', () => {
    state.benchmarkMode = false;
    state.benchmarkProject = null;
    state.projects = [];
    state.timelines = {};
    state.evidenceCache = {};
    state.statusBar = null;
    state.ownerInputs = null;
    state.ownerInputsLoaded = false;
    $('benchmark-banner').classList.remove('visible');
    navigate('#home');
  });

  // Hash change → re-render
  window.addEventListener('hashchange', render);

  // Initial build-info readback then static route rendering.
  if (!window.location.hash) window.location.hash = '#home';
  pollBuildInfo(true).catch(() => false).finally(() => render());
  window.setInterval(() => { pollBuildInfo().catch(() => false); }, 60000);
}

document.addEventListener('DOMContentLoaded', init);
