'use strict';
async function renderL4EngineeringHistory(app, name) {
  const ctx = await l4Context(name);
  const box = l4Frame(app, 'engineering-history', 'Engineering history', ctx);
  if (!ctx.summary) return;
  const events = await loadTimeline(name);
  const section = el('section', 'l4-history');
  section.appendChild(el('h2', '', 'Recorded OTM, TC and engineering evidence'));
  if (!events.length) l4Unknown(section, 'Project event history');
  else {
    for (const event of events.slice().sort((a,b) =>
      String(a.ts || '').localeCompare(String(b.ts || '')))) {
      const row = el('div', 'l4-history-event');
      l4Line(row, 'Actor', event.actor);
      l4Line(row, 'Type', event.type);
      l4Line(row, 'Recorded time', event.ts);
      const summary = event.text || event.body || event.summary;
      if (summary) l4Line(row, 'Evidence', String(summary).slice(0,450));
      const source = event.comment_url || event.source_url || event.url ||
        event.source_ref;
      l4Link(row, 'Event source', source, ctx.repo);
      section.appendChild(row);
    }
  }
  box.appendChild(section);
  const chain = el('section','l4-generation-chain');
  chain.appendChild(el('h2', '', 'Contribution chain by generation'));
  const agents = Array.isArray(ctx.summary.agents) ? ctx.summary.agents : [];
  if (!agents.length) l4Unknown(chain, 'Generational contributions');
  else for (const agent of agents.slice().sort((a,b) =>
    Number(a.generation || 0) - Number(b.generation || 0))) {
    const item = el('div', 'l4-generation');
    l4Line(item, 'Generation', agent.generation);
    l4Line(item, 'Actor', agent.alias || agent.role);
    l4Line(item, 'Agent id', agent.chat_id8);
    l4Link(item, 'Registered evidence', agent.evidence_thread_url, ctx.repo);
    chain.appendChild(item);
  }
  box.appendChild(chain);
}
