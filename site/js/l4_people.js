'use strict';
async function renderL4People(app, name) {
  const ctx = await l4Context(name);
  const box = l4Frame(app, 'people', 'People and responsibility', ctx);
  if (!ctx.summary) return;
  const p = ctx.summary, reg = ctx.detail.registry || {};
  const ctrl = p.control || reg.control || {};
  const roles = [
    {label: 'OwnerTeammember', identity: null,
     source: p.source_refs?.inbox, authority: 'Evidence and Owner relay'},
    {label: 'TeamCoordinator', identity: ctrl.current_coordinator?.holder ||
     ctrl.coordinator, source: ctrl.current_coordinator?.control_ref ||
     ctrl.control_post || p.source_refs?.status_issue,
     authority: 'Coordinator actions are subject to Owner control'},
  ];
  for (const role of roles) {
    const card = el('section', 'card l4-role');
    card.appendChild(el('h2', '', role.label));
    l4Line(card, 'Recorded holder', role.identity);
    l4Line(card, 'Responsibility', role.authority);
    if (!l4Link(card, 'Evidence behind role', role.source, ctx.repo))
      l4Unknown(card, 'Role source');
    box.appendChild(card);
  }
  const oracle = el('section', 'card l4-oracle');
  oracle.appendChild(el('h2', '', 'Oracle'));
  oracle.appendChild(el('p', 'note', 'none · advises only, never authorizes.'));
  oracle.appendChild(el('p', 'note', 'An advisory actor is not inferred from absent records.'));
  box.appendChild(oracle);
}
