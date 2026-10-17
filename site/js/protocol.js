'use strict';

async function renderProtocol(app) {
  const frag = cloneTemplate('tpl-protocol');
  app.innerHTML = '';
  app.appendChild(frag);

  await loadProtocolSource();

  const mdEl = $('protocol-md');
  const tocEl = $('toc-list');

  if (!state.protocolMd) {
    mdEl.innerHTML = `<div class="empty-state">Protocol file not found. <a href="https://github.com/${REPO}/blob/main/protocol/TEAM_PROTOCOL.md" target="_blank" rel="noopener">View on GitHub →</a></div>`;
    return;
  }

  const sourceHeader = state.protocolMd.match(/^#\s+(.+)$/m);
  const sourceStatus = state.protocolMd.match(/^Status:\s*\*\*(.+?)\*\*/m);
  $('protocol-label').textContent = sourceStatus ?
    'Protocol ' + sourceStatus[1].trim() :
    sourceHeader ? sourceHeader[1].trim() : 'Protocol · source label UNKNOWN';

  mdEl.innerHTML = markdownToHTML(state.protocolMd);

  // Build TOC from rendered h2/h3
  mdEl.querySelectorAll('h2, h3').forEach((h, i) => {
    const id = `protocol-section-${i}`;
    h.id = id;
    const li = el('li');
    const a = el('a');
    a.href = '#' + id;
    a.textContent = h.textContent;
    if (h.tagName === 'H3') li.style.paddingLeft = '12px';
    li.appendChild(a);
    tocEl.appendChild(li);
  });
}

// ── Benchmarks view ────────────────────────────────────────
