'use strict';
async function renderL4Sources(app, name) {
  const ctx = await l4Context(name);
  const box = l4Frame(app, 'sources', 'Sources and benchmarks', ctx);
  if (!ctx.summary) return;
  const value = ctx.detail.originals ?? ctx.summary.originals;
  if (!Array.isArray(value) || !value.length) {
    if (value?.status === 'ERROR') l4Line(box, 'Schema error', value.errors);
    l4Unknown(box, 'Original source inventory');
    return;
  }
  const table = el('table', 'l4-sources-table');
  const header = el('tr');
  for (const h of ['Original', 'Path', 'Class', 'Hash', 'Custody'])
    header.appendChild(el('th', '', h));
  table.appendChild(header);
  for (const valueRow of value) {
    const row = el('tr');
    if (!valueRow || valueRow.status === 'ERROR') {
      const cell = el('td', 'l4-error', 'ERROR: ' + l4Text(valueRow?.errors));
      cell.colSpan = 5; row.appendChild(cell);
      table.appendChild(row); continue;
    }
    row.appendChild(el('td', '', l4Text(valueRow.name)));
    row.appendChild(el('td', '', l4Text(valueRow.path)));
    const category = el('td');
    category.appendChild(el('span',
      valueRow.class === 'MISSING' ? 'badge badge-red' : 'badge badge-grey',
      l4Text(valueRow.class)));
    row.appendChild(category);
    row.appendChild(el('td', '', l4Text(valueRow.sha256 || valueRow.sha)));
    row.appendChild(el('td', '', l4Text(valueRow.custody)));
    table.appendChild(row);
  }
  const wrapper = el('div','table-wrap');
  wrapper.appendChild(table);box.appendChild(wrapper);
}
