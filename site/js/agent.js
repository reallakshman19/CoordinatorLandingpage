'use strict';

const FRESHNESS = new Set(['RUNNING-observed', 'STALE', 'UNKNOWN', 'HOLD']);
const OWNER_STATES = new Set(['OPEN', 'ACKNOWLEDGED', 'NEEDS_CLARIFICATION', 'HANDLED', 'SUPERSEDED']);
function freshState(p) {
  if (p && p.control && p.control.hold) return 'HOLD';
  return p && FRESHNESS.has(p.freshness_status) ? p.freshness_status : 'UNKNOWN';
}
function freshnessBadge(status) {
  const classes = {'RUNNING-observed': 'badge-green', STALE: 'badge-yellow',
                   UNKNOWN: 'badge-grey', HOLD: 'badge-purple'};
  return el('span', 'badge ' + (classes[status] || 'badge-grey'), status);
}
function summarizeFreshness(projects) {
  if (!projects.length) return 'UNKNOWN';
  const all = projects.map(freshState);
  if (all.includes('HOLD')) return 'HOLD';
  if (all.includes('UNKNOWN')) return 'UNKNOWN';
  if (all.includes('STALE')) return 'STALE';
  return all.every(s => s === 'RUNNING-observed') ? 'RUNNING-observed' : 'UNKNOWN';
}
function safeReceipt(inp) {
  if (inp?.source_kind === 'json_file') return traceSafeGitHubURL(inp.receipt);
  const match = /^https:\/\/github\.com\/reallakshman19\/CoordinatorLandingpage\/issues\/([0-9]+)#issuecomment-([0-9]+)$/.exec(inp && inp.receipt);
  return match && Number(match[1]) === Number(inp.number) ? match[0] : null;
}
function ownerInputState(inp) {
  const status = String(inp && (inp.status || inp.state) || '').toUpperCase();
  if (!OWNER_STATES.has(status)) return 'OPEN';
  return status === 'HANDLED' && !safeReceipt(inp) ? 'NEEDS_CLARIFICATION' : status;
}
function ownerStatusBadge(status) {
  const classes = {OPEN: 'badge-blue', ACKNOWLEDGED: 'badge-yellow',
                   NEEDS_CLARIFICATION: 'badge-red', HANDLED: 'badge-green',
                   SUPERSEDED: 'badge-grey'};
  return el('span', 'badge ' + (classes[status] || 'badge-grey'), status);
}



async function renderAgent(app, projectName, id8) {
  if (!projectName || !id8) { navigate('#home'); return; }
  // Hash arguments must be trusted identities before they reach a fetch URL.
  // Invalid values are displayed as text, never interpreted as markup.
  if (!/^[A-Za-z0-9][A-Za-z0-9._-]*$/.test(projectName) ||
      !state.projects.some(p => p.project === projectName) ||
      !/^[0-9a-f]{8}$/.test(id8)) {
    let shown = id8;
    try { shown = decodeURIComponent(id8); } catch { /* literal input */ }
    app.replaceChildren(el('div', 'empty-state',
      'Invalid agent reference: ' + String(shown)));
    return;
  }

  const frag = cloneTemplate('tpl-agent');
  app.innerHTML = '';
  app.appendChild(frag);

  $('back-to-project').addEventListener('click', () => navigate(`#project/${projectName}`));

  const evData = await loadEvidence(id8);
  const agent = evData?.agent;

  if (!agent || evData.project !== projectName || agent.chat_id8 !== id8) {
    app.innerHTML = `<div class="empty-state">No evidence data found for agent ${escapeHtml(id8)}.</div>`;
    return;
  }

  $('agent-title').textContent = `${agent.role} · ${id8}`;
  const nextOwner = state.projects.find(p => p.project === projectName);
  wp13ReadOnly($('wp13-agent-moves'), nextOwner?.next_move, id8);
  if (agent.status === 'hold') {
    const owning = state.projects.find(p => p.project === projectName);
    wp12HoldBanner($('wp12-agent-hold'), owning?.hold_report ||
      {active: true, since: '', owner_words: '', recorded: ''});
  }
  const badges = $('agent-badges');
  badges.appendChild(agentStateBadge(agent.status));
  const owningRepo = state.projects.find(p => p.project === projectName)?.repository;
  wp12HeadStatus(badges, agent.evidence_head_status, owningRepo);
  if (agent.generation) {
    badges.appendChild(el('span', 'badge badge-grey', `gen ${agent.generation}`));
  }

  // Action buttons
  if (state.benchmarkMode || (state.projects.find(p => p.project === projectName)?.repository !== REPO &&
      !state.projects.find(p => p.project === projectName)?.is_benchmark &&
      !state.projects.find(p => p.project === projectName)?.benchmark_snapshot)) {
    $('agent-action-buttons').style.display = 'none';
  } else {
    $('btn-ground').href = groundURL(id8, projectName);
    $('btn-suggest').href = suggestURL(id8, projectName);
  }

  const evidence = agent.evidence || [];
  const evBlocks = evidence.filter(e => e.type === 'evidence');
  $('evidence-count').textContent = `${evBlocks.length} blocks`;

  const chain = $('evidence-chain');
  if (!evidence.length) {
    chain.innerHTML = '<div class="empty-state">No evidence blocks yet.</div>';
    return;
  }

  // Render evidence blocks with interleaved verdicts
  let i = 0;
  while (i < evidence.length) {
    const item = evidence[i];

    if (item.type === 'evidence') {
      const rowEl = el('div', 'evidence-row');
      const header = el('div', 'evidence-row-header');
      header.setAttribute('role', 'button');
      header.setAttribute('tabindex', '0');
      header.setAttribute('aria-expanded', 'false');

      const seq = el('span', 'evidence-seq', `#${item.seq}`);
      const task = el('span', 'evidence-task');
      const taskId = item.task?.split(' ')[0] || '';
      const taskTitle = item.task?.slice(taskId.length).trim() || '';
      task.innerHTML = `<code style="font-size:0.78rem">${escapeHtml(taskId)}</code> ${escapeHtml(taskTitle)}`;

      const statusBadge = el('span', `badge ${statusBadgeCls(item.status)}`, item.status);
      const ts = el('span', 'evidence-ts', fmtDateTime(item.ts));
      const icon = el('span', 'evidence-expand-icon', '▶');

      header.appendChild(seq);
      header.appendChild(task);
      header.appendChild(statusBadge);
      header.appendChild(el('span', 'badge badge-grey wp12-evidence-hosting',
        wp12HasHostedRun(item, owningRepo) ? 'hosted CI link claimed' : 'local only'));
      header.appendChild(ts);
      header.appendChild(icon);

      // Detail
      const detail = el('div', 'evidence-detail');

      // Proofs
      if (item.proofs?.length) {
        const proofSection = el('div');
        proofSection.innerHTML = '<strong>Proof:</strong>';
        const ul = el('ul', '', null);
        item.proofs.forEach(p => {
          const li = el('li');
          li.style.marginBottom = '3px';
          li.innerHTML = escapeHtml(p.line) + ' ';
          li.appendChild(proofGradeBadge(p.grade));
          ul.appendChild(li);
        });
        proofSection.appendChild(ul);
        detail.appendChild(proofSection);
      }

      // Tests
      if (item.tests) {
        const t = el('div');
        t.style.marginTop = '8px';
        t.innerHTML = `<strong>Tests:</strong> ${escapeHtml(item.tests)}`;
        detail.appendChild(t);
      }

      // Would be wrong if
      if (item.would_be_wrong) {
        const w = el('div');
        w.style.marginTop = '8px';
        w.innerHTML = `<strong>Would be wrong if:</strong> ${escapeHtml(item.would_be_wrong)}`;
        detail.appendChild(w);
      }

      // Needs Owner
      if (item.needs_owner && item.needs_owner !== 'none') {
        const no = el('div');
        no.style.cssText = 'margin-top:8px;background:var(--warn-bg);padding:6px 10px;border-radius:4px';
        no.innerHTML = `<strong>Needs Owner:</strong> ${escapeHtml(item.needs_owner)}`;
        detail.appendChild(no);
      }

      // Raw block link
      const rawBtn = el('button', 'btn btn-small', 'Show raw block');
      rawBtn.style.marginTop = '10px';
      let rawOpen = false;
      const rawPre = el('pre');
      rawPre.textContent = item.raw || '';
      rawPre.style.display = 'none';
      rawBtn.addEventListener('click', () => {
        rawOpen = !rawOpen;
        rawPre.style.display = rawOpen ? 'block' : 'none';
        rawBtn.textContent = rawOpen ? 'Hide raw block' : 'Show raw block';
      });
      detail.appendChild(rawBtn);
      detail.appendChild(rawPre);

      // Note: labels are agent claims
      const claimNote = el('div', 'claim-note',
        'Proof grades (CI / READBACK / LOCAL / CLAIM-ONLY) are this agent\'s own labels. ' +
        'OwnerTeammember verdicts appear below each block. Nothing here is acceptance.');
      detail.appendChild(claimNote);

      rowEl.appendChild(header);
      rowEl.appendChild(detail);

      // Collect following verdicts
      let j = i + 1;
      while (j < evidence.length && evidence[j].type !== 'evidence') {
        const sub = evidence[j];
        if (sub.type === 'verdict') {
          const v = verdictEl(sub.verdict);
          if (v) rowEl.appendChild(v);
        } else if (sub.type === 'retired') {
          const retEl = el('div', 'verdict-row');
          retEl.style.color = 'var(--text-3)';
          retEl.textContent = 'Agent RETIRED — no further messages';
          rowEl.appendChild(retEl);
        }
        j++;
      }

      // Toggle expand
      const toggle = () => {
        const open = detail.classList.toggle('open');
        icon.textContent = open ? '▼' : '▶';
        header.setAttribute('aria-expanded', String(open));
      };
      header.addEventListener('click', toggle);
      header.addEventListener('keydown', e => {
        if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); toggle(); }
      });

      chain.appendChild(rowEl);
      i = j;
    } else {
      i++;
    }
  }
}

function statusBadgeCls(status) {
  const map = {
    DONE: 'badge-green',
    PARTIAL: 'badge-yellow',
    BLOCKED: 'badge-purple',
    FAILED: 'badge-red',
  };
  return map[status] || 'badge-grey';
}

// ── Timeline view ──────────────────────────────────────────
