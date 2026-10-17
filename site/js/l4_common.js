'use strict';
// WP-L4 read-only DOM primitives; no HTML interpretation or authority inference.
function l4Known(value) {
  return value !== null && value !== undefined && String(value).trim() !== '';
}
function l4Text(value) {
  if (!l4Known(value)) return 'UNKNOWN';
  if (typeof value === 'object') return JSON.stringify(value);
  return String(value);
}
function l4Line(parent, name, value) {
  const row = el('div', 'l4-field');
  row.appendChild(el('strong', '', name + ': '));
  row.appendChild(el('span', l4Known(value) ? '' : 'l4-unknown', l4Text(value)));
  parent.appendChild(row);
  return row;
}
function l4Link(parent, label, value, repo) {
  const safe = allowedExternalLink(value, repo) || allowedExternalLink(value, REPO);
  if (!safe) return null;
  const a = el('a', 'btn btn-small', label);
  a.href = safe;
  a.target = '_blank';
  a.rel = 'noopener noreferrer';
  parent.appendChild(a);
  return a;
}
function l4Unknown(parent, what) {
  parent.appendChild(el('p', 'note l4-unknown', what + ': UNKNOWN — not recorded'));
}
async function l4Context(projectName) {
  const safe = typeof projectName === 'string' &&
    /^[A-Za-z0-9][A-Za-z0-9._-]*$/.test(projectName);
  const summary = safe ? state.projects.find(p => p.project === projectName) : null;
  const detail = summary ? await loadProjectDetail(projectName) : null;
  return {projectName, summary, detail: detail || {}, repo: summary?.repository || ''};
}
function l4Frame(app, view, heading, ctx) {
  const page = el('section', 'l4-view');
  page.id = 'l4-' + view;
  page.appendChild(el('h1', '', heading));
  page.appendChild(el('p', 'note', 'Read-only projection · records are not authorization or verified acceptance.'));
  if (ctx.summary) {
    const a = el('a', 'btn btn-small', 'Back to project');
    a.href = '#project/' + encodeURIComponent(ctx.projectName);
    page.appendChild(a);
  } else l4Unknown(page, 'Project');
  app.replaceChildren(page);
  return page;
}
function l4FieldSource(ctx, value) {
  return l4Link(ctx.page, 'Recorded source', value, ctx.repo);
}
