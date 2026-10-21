'use strict';
const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const M = require('../site/js/dashboard-model.js');
const now = Date.parse('2026-10-21T06:00:00Z');
const iso = offset => new Date(now + offset * 60000).toISOString();
function row(overrides = {}) {
  return { key: 'p/workstream:main/instance:agent:0', project: 'p', alias: 'Worker',
    instance_id8: '12345678', work_state: 'WORKING', light: 'green',
    observation: { state: 'WORKING', observed_at: iso(-2) },
    dimensions: { work: { state: 'running' }, monitoring: { state: 'fresh', last_evaluation: iso(-10), next_due: iso(20) }, execution_authority: { state: 'allowed' } },
    timer: { state: 'ACTIVE', checked_at: iso(-1), last_tick: iso(-1), next_due: iso(1) }, ...overrides };
}
function source(rows = [row()]) {
  return { schema: 'status_bar.v1', as_of: iso(-1), projects: [{ project: 'p' }],
    coverage: { complete: true, expected: rows.length, projected: rows.length }, instances: rows };
}
test('timezone-less timestamps, silence, and missing state starts never become activity or duration', () => {
  assert.equal(M.time('07:34'), null); assert.equal(M.time('2026-10-21T07:34:00'), null);
  const s = source([row({ observation: null })]);
  const r = M.snapshot(s, now, false).rows[0];
  assert.equal(r.activityAge, null); assert.equal(r.elapsed, null); assert.equal(r.light, 'yellow');
  assert.equal(M.duration(null), 'UNKNOWN');
});
test('scheduled due crosses to late; monitor freshness boundary never becomes a scheduled check', () => {
  assert.equal(M.snapshot(source(), now, false).rows[0].next.text, 'in 01:00');
  const due = M.snapshot(source(), now + 60000, false).rows[0];
  assert.equal(due.next.text, 'DUE NOW'); assert.equal(due.timerState, 'UNKNOWN');
  const late = M.snapshot(source(), now + 120000, false).rows[0];
  assert.equal(late.next.text, 'LATE 01:00'); assert.equal(late.next.late, true);
  const r = M.snapshot(source([row({ timer: { state: 'UNKNOWN' } })]), now, false).rows[0];
  assert.equal(r.next.at, null); assert.equal(r.monitor.at, iso(20));
  assert.equal(r.next.text, 'Not scheduled');
});
test('future or stale observations, incomplete roster, duplicate identities and expired grants cannot stay green', () => {
  assert.equal(M.snapshot(source(), now + 31 * 60000, false).rows[0].light, 'yellow');
  const future = row({ observation: { observed_at: iso(1) } });
  assert.equal(M.snapshot(source([future]), now, false).rows[0].light, 'yellow');
  const s = source(); s.coverage.complete = false;
  assert.equal(M.snapshot(s, now, false).rows[0].light, 'yellow');
  assert.equal(M.coverage(source([row(), row()])), false);
  const expired = row({ grant: { expires_at: iso(-1) } });
  assert.equal(M.snapshot(source([expired]), now, false).rows[0].light, 'yellow');
});
test('paused timers do not accrue overdue; ON is distinct from reported work', () => {
  const r = row({ timer: { state: 'PAUSED', checked_at: iso(-1), next_due: iso(-5) } });
  const projected = M.snapshot(source([r]), now, false).rows[0];
  assert.equal(projected.timerState, 'PAUSED'); assert.equal(projected.next.late, false);
  const unknown = row({ light: 'yellow', observation: null });
  const p = M.snapshot(source([unknown]), now, false).rows[0];
  assert.equal(p.timerState, 'ON'); assert.equal(p.light, 'yellow');
});
test('reported completion duration freezes; missing completion time is not guessed', () => {
  const r = row({ complete: true, work: { state_since: iso(-40), completed_at: iso(-3) } });
  assert.equal(M.snapshot(source([r]), now, false).rows[0].elapsed, 37 * 60000);
  assert.equal(M.snapshot(source([r]), now + 10 * 60000, false).rows[0].elapsed, 37 * 60000);
  r.work.completed_at = undefined;
  assert.equal(M.snapshot(source([r]), now, false).rows[0].elapsed, null);
});
test('benchmarks freeze at source as_of; invalid frozen time fails closed', () => {
  const a = M.snapshot(source(), now, true), b = M.snapshot(source(), now + 9e7, true);
  assert.equal(a.now, b.now); assert.equal(a.rows[0].next.text, b.rows[0].next.text);
  const s = source(); s.as_of = '07:34'; assert.equal(M.snapshot(s, now, true).valid, false);
});
test('same id8 in different projects preserves declarations and does not mutate input', () => {
  const s = source([row(), row({ key: 'q/workstream:main/instance:agent:0', project: 'q' })]);
  const before = JSON.stringify(s), p = M.snapshot(s, now, false);
  assert.equal(p.rows.length, 2); assert.notEqual(p.rows[0].key, p.rows[1].key);
  assert.equal(JSON.stringify(s), before);
});
test('reported evidence is useful timing without becoming a direct activity observation', () => {
  const r = row({ observation: null, latest_report: { status: 'REPORTED', at: iso(-3), task: 'PR review', next: 'Publish verdict' } });
  const p = M.snapshot(source([r]), now, false).rows[0];
  assert.equal(p.evidenceAge, 180000); assert.equal(p.activityAge, null);
  assert.equal(p.report.task, 'PR review'); assert.equal(p.light, 'yellow');
});

// Minimal DOM execution harness. It checks integration/lifecycle, not browser layout.
class Element {
  constructor(tag) { this.tag = tag; this.children = []; this.dataset = {}; this.attrs = {}; this.events = {}; this.open = false; this.textContent = ''; }
  append(...children) { children.forEach(c => { c.parent = this; this.children.push(c); }); }
  replaceChildren(...children) { this.children.forEach(c => c.parent = null); this.children = []; this.append(...children); }
  setAttribute(k, v) { this.attrs[k] = v; }
  addEventListener(k, fn) { this.events[k] = fn; }
  get isConnected() { return this.attached || !!this.parent?.isConnected; }
}
function harness(data = source()) {
  let ms = now, pending, fetches = 0, nextId = 0;
  const intervals = new Map(), listeners = new Map();
  const app = new Element('main'); app.attached = true;
  const el = (tag, cls, text) => { const e = new Element(tag); e.className = cls || ''; e.textContent = text || ''; return e; };
  const context = { OTMDashboard: M, el, REPO: 'owner/control', DATA_BASE: 'data/', BM_DATA_BASE: 'data/benchmarks/',
    state: { benchmarkMode: false, projects: [{ project: 'p', repository: 'owner/product', last_cycle_at: iso(-10) }], buildInfo: { source_capture_at: iso(-1) } },
    Date: class extends Date { static now() { return ms; } },
    document: { hidden: false, addEventListener: (k, f) => listeners.set(k, f), removeEventListener: k => listeners.delete(k) },
    window: { setInterval: f => { intervals.set(++nextId, f); return nextId; }, clearInterval: i => intervals.delete(i) },
    fetchJSON: async url => { fetches++; assert.equal(url, 'data/status-bar.json'); return pending ? await pending : data; } };
  vm.createContext(context); vm.runInContext(fs.readFileSync(path.join(__dirname, '../site/js/dashboard.js'), 'utf8'), context);
  function all(e = app) { return [e, ...e.children.flatMap(c => all(c))]; }
  return { app, context, all, intervals, listeners, get fetches() { return fetches; },
    advance: delta => { ms += delta; [...intervals.values()].forEach(f => f()); },
    defer: p => pending = p };
}
test('real renderer ticks without network polling, preserves expansion on regroup, and cleans up on exit', async () => {
  const h = harness(); await h.context.renderDashboard(h.app);
  const details = h.all().find(e => e.tag === 'details'); details.open = true;
  const project = h.all().find(e => e.tag === 'button' && e.textContent === 'By project'); project.events.click();
  assert.equal(h.all().find(e => e.tag === 'details').open, true);
  const hrefs = h.all().filter(e => e.tag === 'a').map(e => e.href);
  assert(hrefs.includes('data/evidence-p-12345678.json'));
  h.advance(120000);
  assert(h.all().some(e => e.textContent.includes('LATE 01:00')));
  assert.equal(h.fetches, 1); assert.equal(h.intervals.size, 1);
  h.context.stopDashboard(); assert.equal(h.intervals.size, 0); assert.equal(h.listeners.size, 0);
});
test('late fetch after navigation cannot install a view or interval; hostile source strings stay text', async () => {
  const h = harness(source([row({ alias: '<img src=x onerror=alert(1)>' })]));
  let finish; h.defer(new Promise(resolve => finish = resolve));
  const render = h.context.renderDashboard(h.app); h.app.replaceChildren(); finish(source()); await render;
  assert.equal(h.intervals.size, 0); assert.equal(h.app.children.length, 0);
  const safe = harness(source([row({ alias: '<img src=x onerror=alert(1)>' })]));
  await safe.context.renderDashboard(safe.app);
  assert(safe.all().some(e => e.textContent.includes('<img src=x')));
  assert.equal(safe.all().filter(e => e.tag === 'img').length, 0);
  safe.context.stopDashboard();
});
test('navigation and asset wiring point to the production Dashboard consumer', () => {
  const html = fs.readFileSync(path.join(__dirname, '../site/index.html'), 'utf8');
  const core = fs.readFileSync(path.join(__dirname, '../site/js/core.js'), 'utf8');
  assert(html.includes('data-view="dashboard"'));
  assert(html.indexOf('js/dashboard-model.js') < html.indexOf('js/dashboard.js'));
  assert(core.includes("case 'dashboard': await renderDashboard(app); break;"));
  assert(core.indexOf('stopDashboard();') < core.indexOf("app.innerHTML = '<div class=\"loading\""));
});
test('source outage leaves an explicit unknown view with no timer interval', async () => {
  const h = harness(null); await h.context.renderDashboard(h.app);
  assert(h.all().some(e => e.textContent.includes('projection unavailable')));
  assert.equal(h.intervals.size, 0);
});
