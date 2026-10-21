/* Read-only dashboard projection. Source lights are only retained or downgraded. */
(function (root) {
  'use strict';
  const FRESH = 30 * 60 * 1000;
  function time(value) {
    if (typeof value !== 'string' || !/^\d{4}-\d\d-\d\dT\d\d:\d\d(?::\d\d(?:\.\d+)?)?(?:Z|[+-]\d\d:\d\d)$/.test(value)) return null;
    const n = Date.parse(value);
    return Number.isFinite(n) ? n : null;
  }
  function age(value, now) {
    const t = time(value);
    return t !== null && t <= now ? now - t : null;
  }
  function duration(ms) {
    if (!Number.isFinite(ms) || ms < 0) return 'UNKNOWN';
    const s = Math.floor(ms / 1000), h = Math.floor(s / 3600);
    return (h ? String(h).padStart(2, '0') + ':' : '') +
      String(Math.floor(s / 60) % 60).padStart(2, '0') + ':' + String(s % 60).padStart(2, '0');
  }
  function instant(value) {
    const t = time(value);
    return t === null ? 'UNKNOWN' : new Intl.DateTimeFormat('en-GB', {
      timeZone: 'Asia/Dubai', day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false,
    }).format(t);
  }
  function due(value, now) {
    const t = time(value);
    if (t === null) return { at: null, text: 'Not recorded', late: false };
    const d = t - now;
    return { at: value, late: d < 0, text: d === 0 ? 'DUE NOW' : (d < 0 ? 'LATE ' : 'in ') + duration(Math.abs(d)) };
  }
  function coverage(source) {
    const rows = source?.instances, c = source?.coverage;
    return source?.schema === 'status_bar.v1' && Array.isArray(rows) &&
      Array.isArray(source.projects) && c?.complete === true &&
      c.expected === rows.length && c.projected === rows.length &&
      rows.every(r => r && typeof r.key === 'string' && r.key) && new Set(rows.map(r => r.key)).size === rows.length;
  }
  function workGroup(row) {
    if (row.retired) return 'Retired';
    if (row.standby) return 'Standby';
    if (row.complete) return 'Done reported';
    const raw = String(row.work_state || '').toLowerCase(), state = row.dimensions?.work?.state;
    if (/park|\bhold\b/.test(raw)) return 'Parked / held';
    if (state === 'blocked') return 'Blocked';
    if (state === 'waiting' || /wait|pending/.test(raw)) return 'Waiting';
    if (state === 'running' || /^(working|running|in.progress)\b/.test(raw)) return 'Working';
    return 'Unknown';
  }
  function projectRow(row, source, now) {
    const monitor = row.dimensions?.monitoring || {}, timer = row.timer || {};
    const observedAge = age(row.observation?.observed_at, now);
    const monitorAge = age(monitor.last_evaluation, now), snapshotAge = age(source.as_of, now);
    const monitorLimit = time(monitor.next_due);
    const current = coverage(source) && snapshotAge !== null && snapshotAge <= FRESH &&
      observedAge !== null && observedAge <= FRESH && monitorAge !== null && monitorAge <= FRESH &&
      monitor.state === 'fresh' && (monitorLimit === null || monitorLimit >= now);
    const grantEnd = time(row.grant?.expires_at || row.grant?.until);
    const light = ['green', 'yellow', 'red', 'grey'].includes(row.light) ? row.light : 'yellow';
    const safeLight = light === 'green' && (!current || (grantEnd !== null && grantEnd <= now)) ? 'yellow' : light;
    const timerAge = age(timer.checked_at, now), recordedDue = time(timer.next_due);
    const checked = time(timer.checked_at);
    const scheduled = timer.state === 'ACTIVE' && checked !== null && checked <= now && recordedDue !== null && recordedDue > checked;
    const timerFresh = timerAge !== null && timerAge <= FRESH;
    const timerState = timerFresh && timer.state === 'PAUSED' ? 'PAUSED' :
      timerFresh && scheduled && recordedDue > now ? 'ON' : 'UNKNOWN';
    const work = row.work && typeof row.work === 'object' ? row.work : {};
    const started = time(work.state_since), ended = row.complete ? time(work.completed_at) : now;
    const elapsed = started !== null && ended !== null && started <= ended && ended <= now ? ended - started : null;
    const report = row.latest_report?.status === 'REPORTED' ? row.latest_report : {};
    const evidenceAt = time(report.at) === null ? null : report.at;
    return { key: row.key, raw: row, project: String(row.project || 'UNKNOWN'),
      name: String(row.alias || row.role || row.instance_id8 || 'Unidentified declaration'),
      group: workGroup(row), light: safeLight,
      lightReason: safeLight !== light ? 'Positive observation stale, incomplete, or expired; refresh source' : String(row.light_reason || 'Source projection'),
      activity: row.observation?.observed_at, activityAge: observedAge,
      evidenceAt, evidenceAge: age(evidenceAt, now), report,
      elapsed, timerState, timerChecked: timer.checked_at, lastTick: timer.last_tick,
      next: scheduled ? due(timer.next_due, now) : { at: null, late: false, text: timerState === 'PAUSED' ? 'Paused' : 'Not scheduled' },
      monitor: due(monitor.next_due, now), monitorAt: monitor.last_evaluation,
      stateSince: work.state_since, completedAt: work.completed_at };
  }
  function snapshot(source, realNow, benchmark) {
    const valid = source?.schema === 'status_bar.v1' && Array.isArray(source.instances) && Array.isArray(source.projects);
    const frozen = time(source?.as_of), now = benchmark ? frozen : realNow;
    if (!valid || !Number.isFinite(now)) return { valid: false, rows: [], now: realNow, full: false };
    return { valid: true, full: coverage(source), now, frozen: !!benchmark,
      rows: source.instances.filter(r => r && typeof r === 'object').map(r => projectRow(r, source, now)) };
  }
  const api = { time, age, duration, instant, due, coverage, workGroup, projectRow, snapshot };
  root.OTMDashboard = api;
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
})(typeof globalThis === 'undefined' ? window : globalThis);
