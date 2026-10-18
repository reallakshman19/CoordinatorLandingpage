'use strict';
// WP-L5: display the committed example, NEVER claim live v3.6 acceptance.
function renderV36Scoreboard(host, data) {
  if (!host || !data || typeof data !== 'object') return;
  const card = el('section', 'card v36-scoreboard');
  card.id = 'v36-scoreboard';
  card.appendChild(el('h2', '', 'v3.6 source-backed scoreboard · synthetic fixture'));
  card.appendChild(el('p', 'note',
    'SYNTHETIC FIXTURE · Common test data, not live project status. ECO-08 pilot NOT_RUN.'));
  const state = String(data.status || 'UNKNOWN');
  card.appendChild(el('div', state === 'ERROR' ? 'badge badge-red' : 'badge badge-grey',
    state));
  const reason = String(data.reason || 'not_recorded');
  card.appendChild(el('p', 'note', 'Source state: ' + reason));
  if (state !== 'SYNTHETIC_FIXTURE') {
    card.appendChild(el('p', 'v36-unknown',
      state === 'ERROR' ? 'ERROR · unusable pinned artifact' :
        'UNKNOWN · pinned artifact not available'));
    const fallback = data.title_fallback;
    if (fallback && fallback.label === 'derived from title') {
      card.appendChild(el('p', 'note',
        'derived from title · ' + String(fallback.done ?? 0) + '/' +
        String(fallback.count ?? 0) +
        ' · fallback only, not verified evidence or Owner acceptance'));
    }
    host.appendChild(card);
    return;
  }
  card.appendChild(el('p', 'note', 'Pinned source: ' +
    String(data.source_path || 'UNKNOWN') + ' · SHA-256 ' +
    String(data.source_sha256 || 'UNKNOWN')));
  card.appendChild(el('p', 'note', 'Fixture parent: ' +
    String(data.source_parent || 'UNKNOWN') + ' · registered project parent: ' +
    String(data.registry_parent || 'UNKNOWN') +
    ' · different scopes; no automatic attribution.'));
  const stats = [
    ['E · native evidence in fixture',
     String(data.E?.current ?? 'UNKNOWN') + ' / ' +
       String(data.E?.tasks ?? 'UNKNOWN') + ' · not a passing test'],
    ['A · category coverage', String(data.A?.status || 'UNKNOWN') +
     ' · ' + String(data.A?.required_categories ?? 'UNKNOWN') +
     ' required categories'],
    ['V · externally verified', String(data.V?.status || 'UNKNOWN')],
    ['Owner acceptance', String(data.acceptance?.status || 'UNKNOWN')],
  ];
  for (const [name, value] of stats) {
    const field = el('div', 'v36-scoreboard-field');
    field.appendChild(el('strong', '', name + ': '));
    field.appendChild(el('span', '', value));
    card.appendChild(field);
  }
  const tasks = Array.isArray(data.tasks) ? data.tasks : [];
  const wrap = el('div', 'table-wrap');
  const table = el('table', 'v36-scoreboard-table');
  const thead = el('thead');
  const headers = el('tr');
  for (const k of ['Task', 'E', 'A', 'V', 'Acceptance'])
    headers.appendChild(el('th', '', k));
  thead.appendChild(headers);
  table.appendChild(thead);
  const tbody = el('tbody');
  for (const row of tasks) {
    const tr = el('tr');
    for (const key of ['task_id','E','A','V','acceptance'])
      tr.appendChild(el('td', '', String(row?.[key] || 'UNKNOWN')));
    tbody.appendChild(tr);
  }
  table.appendChild(tbody);
  wrap.appendChild(table);
  card.appendChild(wrap);
  host.appendChild(card);
}
