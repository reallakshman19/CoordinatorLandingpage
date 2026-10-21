'use strict';
let dashboardCleanup = () => {};
function stopDashboard() { dashboardCleanup(); dashboardCleanup = () => {}; }

async function renderDashboard(app) {
  stopDashboard();
  const M = OTMDashboard, root = el('section', 'otm-dashboard');
  root.setAttribute('aria-label', 'Operational Dashboard');
  app.replaceChildren(root);
  root.append(el('h1', '', 'Dashboard'), el('p', 'note', 'Loading existing status and timing records…'));
  const source = await fetchJSON((state.benchmarkMode ? BM_DATA_BASE : DATA_BASE) + 'status-bar.json', { cache: 'no-store' });
  if (!root.isConnected) return;
  state.statusBar = source;
  const initial = M.snapshot(source, Date.now(), state.benchmarkMode);
  root.replaceChildren(el('h1', '', 'Dashboard'));
  if (!initial.valid) { root.append(el('p', 'otm-yellow', 'UNKNOWN · status-bar projection unavailable or invalid.')); return; }
  const sourceProjects = Array.isArray(state.projects) ? state.projects : [];
  let mode = 'state';
  const clock = el('div', 'otm-clock'), monitor = el('div', 'otm-strip');
  const attention = el('div', 'otm-attention'), list = el('div', 'otm-roster');
  const toolbar = el('div', 'otm-toolbar'), buttons = [];
  for (const choice of ['state', 'project']) {
    const b = el('button', 'btn btn-small', 'By ' + choice);
    b.type = 'button'; b.setAttribute('aria-pressed', String(choice === mode));
    b.addEventListener('click', () => { mode = choice; buttons.forEach(x => x.setAttribute('aria-pressed', String(x === b))); rebuild(); });
    buttons.push(b); toolbar.append(b);
  }
  const coverage = el('span', initial.full ? 'note' : 'otm-yellow',
    (initial.full ? 'Full' : 'INCOMPLETE / UNKNOWN') + ' roster · ' + initial.rows.length + ' declarations');
  toolbar.append(coverage);
  const legend = el('p', 'note', '● Green: current source-backed status · ● Yellow: attention / unknown · ● Red: blocked / conflict · ● Grey: held / neutral. A red check clock means overdue, not agent failure.');
  root.append(clock, toolbar, monitor, attention, list, legend);
  const views = [], projectGroups = [];
  function field(label, cls) {
    const box = el('div', 'otm-field ' + (cls || ''));
    box.append(el('span', 'otm-field-label', label));
    const value = el('span', 'otm-value'); box.append(value); return { box, value };
  }
  function link(parent, label, href) { const a = el('a', 'btn btn-small', label); a.href = href; parent.append(a); }
  function sourceLink(parent, label, url, project) {
    const allowed = [REPO, sourceProjects.find(p => p.project === project)?.repository];
    const match = typeof url === 'string' && /^https:\/\/github\.com\/([^/]+\/[^/]+)\/(?:issues|pull)\/\d+(?:#issuecomment-\d+)?$/.exec(url);
    if (match && allowed.includes(match[1])) link(parent, label, url);
  }
  function makeRow(row, index, opened) {
    const details = el('details', 'otm-agent'); details.dataset.key = row.key + ':' + index;
    details.open = opened.has(details.dataset.key);
    const summary = el('summary', 'otm-row'), signal = el('span', 'otm-signal');
    const identity = el('div', 'otm-identity');
    identity.append(el('strong', '', row.project + ' / ' + row.name +
      (row.raw.generation == null ? '' : ' · g' + row.raw.generation)), el('span', 'note', String(row.report.task || row.raw.work_state || 'Work not recorded')));
    const work = field('Work'), activity = field('Evidence / observation'), elapsed = field('Time in state');
    const timer = field('Timer'), check = field('Next scheduled check');
    summary.append(signal, identity, work.box, activity.box, elapsed.box, timer.box, check.box);
    const detail = el('div', 'otm-detail'), timing = el('div', 'otm-timing'), next = el('p', '');
    const basis = el('p', 'note'), actions = el('div', 'otm-actions');
    next.textContent = 'Reported next: ' + (row.report.next || row.raw.work?.next_action || row.raw.work?.next || 'Not recorded; inspect project and existing Next Move records.') +
      (row.report.blocker ? ' · Reported blocker: ' + row.report.blocker : '');
    link(actions, 'Project / decisions', '#project/' + encodeURIComponent(row.project));
    link(actions, 'Existing Next Moves', '#next-moves');
    if (/^[0-9a-f]{8}$/.test(String(row.raw.instance_id8 || ''))) {
      link(actions, 'Project-qualified evidence', (state.benchmarkMode ? BM_DATA_BASE : DATA_BASE) +
        'evidence-' + encodeURIComponent(row.project) + '-' + row.raw.instance_id8 + '.json');
    }
    sourceLink(actions, 'Timer source', row.raw.timer?.source_ref, row.project);
    sourceLink(actions, 'Observation source', row.raw.observation?.source_ref, row.project);
    sourceLink(actions, 'Latest report', row.report.source_ref, row.project);
    detail.append(timing, next, basis, actions); details.append(summary, detail);
    views.push({ key: row.key, index, details, signal, work: work.value, activity: activity.value,
      elapsed: elapsed.value, timer: timer.value, check: check.value, timing, basis });
    return details;
  }
  function rebuild() {
    const opened = new Set(views.filter(v => v.details.open).map(v => v.details.dataset.key));
    views.length = 0; projectGroups.length = 0; list.replaceChildren();
    const current = M.snapshot(source, Date.now(), state.benchmarkMode);
    const groups = new Map();
    current.rows.forEach((r, index) => { const key = mode === 'state' ? r.group : r.project; if (!groups.has(key)) groups.set(key, []); groups.get(key).push({ r, index }); });
    const order = ['Working', 'Waiting', 'Blocked', 'Parked / held', 'Done reported', 'Standby', 'Unknown', 'Retired'];
    const names = [...groups.keys()].sort((a, b) => mode === 'state' ? order.indexOf(a) - order.indexOf(b) : a.localeCompare(b));
    for (const name of names) {
      const header = el('h2', 'otm-group', name + ' · ' + groups.get(name).length);
      if (mode === 'project') {
        const signal = el('span', 'otm-signal'), timing = el('span', 'note');
        header.append(signal, timing); projectGroups.push({ name, signal, timing });
      }
      list.append(header);
      for (const { r, index } of groups.get(name)) list.append(makeRow(r, index, opened));
    }
    tick();
  }
  function tick() {
    const current = M.snapshot(source, Date.now(), state.benchmarkMode);
    clock.textContent = (current.frozen ? 'BENCHMARK · frozen at ' : 'Device clock · ') + M.instant(new Date(current.now).toISOString()) + ' Dubai (+04:00)';
    monitor.replaceChildren();
    const capture = state.benchmarkMode ? null : state.buildInfo?.source_capture_at;
    monitor.append(el('span', '', 'Source snapshot: ' + M.instant(source.as_of)),
      el('span', '', 'Capture age: ' + M.duration(M.age(capture, current.now))));
    monitor.append(el('span', '', source.projects.length + (source.projects.length === 1 ? ' project' : ' projects') + ' · coordinator cycles in project view'));
    const overdue = current.rows.filter(r => r.next.late);
    attention.textContent = overdue.length + ' scheduled checks overdue · ' + current.rows.filter(r => r.timerState === 'UNKNOWN').length + ' timer observations unknown';
    attention.className = 'otm-attention ' + (overdue.length ? 'otm-red' : 'otm-yellow');
    for (const g of projectGroups) {
      const project = source.projects.find(p => p.project === g.name), context = sourceProjects.find(p => p.project === g.name);
      const members = current.rows.filter(r => r.project === g.name);
      let light = ['green', 'yellow', 'red', 'grey'].includes(project?.light) ? project.light : 'yellow';
      if (light === 'green' && (!current.full || members.some(r => r.light !== 'green'))) light = 'yellow';
      g.signal.className = 'otm-signal otm-' + light; g.signal.textContent = ' ● ' + light.toUpperCase();
      const first = members.filter(r => r.next.at).sort((a, b) => M.time(a.next.at) - M.time(b.next.at))[0];
      g.timing.textContent = ' · last coordinator cycle ' + M.instant(context?.last_cycle_at) +
        ' · ' + M.duration(M.age(context?.last_cycle_at, current.now)) + ' ago' +
        (first ? ' · next check: ' + first.name + ' ' + first.next.text : ' · no scheduled check recorded');
    }
    for (const v of views) {
      const r = current.rows[v.index];
      v.signal.className = 'otm-signal otm-' + r.light; v.signal.textContent = '● ' + r.light.toUpperCase();
      v.signal.setAttribute('aria-label', r.light + ': ' + r.lightReason);
      v.work.textContent = r.group;
      v.activity.textContent = r.evidenceAt ? 'Reported ' + M.instant(r.evidenceAt) + ' · ' + M.duration(r.evidenceAge) + ' ago' :
        'Observed ' + M.instant(r.activity) + ' · ' + M.duration(r.activityAge) + ' ago';
      if (r.evidenceAt && r.activityAge !== null) v.activity.textContent += '\nObserved ' + M.instant(r.activity) + ' · ' + M.duration(r.activityAge) + ' ago';
      v.elapsed.textContent = M.duration(r.elapsed) + (r.raw.complete && r.elapsed !== null ? ' (frozen)' : '');
      v.timer.textContent = r.timerState; v.check.textContent = (r.next.at ? M.instant(r.next.at) + ' · ' : '') + r.next.text;
      v.check.className = 'otm-value ' + (r.next.late ? 'otm-red' : '');
      v.timing.textContent = 'Direct activity observed: ' + M.instant(r.activity) + ' · Timer checked: ' + M.instant(r.timerChecked) + ' · last tick: ' + M.instant(r.lastTick) +
        ' · state since (reported): ' + M.instant(r.stateSince) + ' · last monitor evaluation: ' + M.instant(r.monitorAt) +
        ' · monitor freshness limit (not a scheduled check): ' + M.instant(r.monitor.at) + ' · ' + r.monitor.text;
      v.basis.textContent = 'L: existing status_bar.v1 projection · ' + r.lightReason + '. Authority: ' +
        String(r.raw.dimensions?.execution_authority?.state || 'unknown') + '. Browser: ' + String(r.raw.browser?.result || 'UNKNOWN') +
        '. Summary: deterministic template. M: no memory attached. Completion is separate from acceptance.';
    }
  }
  rebuild();
  const interval = window.setInterval(() => { if (!root.isConnected) { window.clearInterval(interval); return; } tick(); }, 1000);
  const visible = () => { if (!document.hidden && root.isConnected) tick(); };
  document.addEventListener('visibilitychange', visible);
  dashboardCleanup = () => { window.clearInterval(interval); document.removeEventListener('visibilitychange', visible); };
}
