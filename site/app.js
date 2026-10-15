/**
 * app.js — Team Protocol Owner Dashboard
 *
 * Pure vanilla JS, no frameworks.
 * Hash routing: #home, #project/<name>, #agent/<id8>, #timeline,
 *               #decision/<project>/<id>, #owner-inputs, #protocol,
 *               #benchmarks, #benchmark/<project>
 *
 * Data is loaded from site/data/*.json (pre-built by the GHA workflow).
 * In benchmark mode, data comes from site/data/benchmarks/*.json.
 *
 * IMPORTANT: this page never claims acceptance. It shows agent claims,
 * verdicts and Owner decisions, labelled as such.
 */

'use strict';

// ── Constants ─────────────────────────────────────────────
const REPO = 'reallakshman19/CoordinatorLandingpage';
const NEW_ISSUE_BASE = `https://github.com/${REPO}/issues/new`;
const DATA_BASE = 'data/';
const BM_DATA_BASE = 'data/benchmarks/';

// ── State ──────────────────────────────────────────────────
const state = {
  projects: [],          // from projects.json
  timelines: {},         // { projectName: [events] }
  evidenceCache: {},     // { id8: agentData }
  benchmarkMode: false,
  benchmarkProject: null,
  dataBuiltAt: null,
  protocolMd: null,
};

// ── DOM helpers ────────────────────────────────────────────
const $ = id => document.getElementById(id);
const el = (tag, cls, text) => {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (text != null) e.textContent = text;
  return e;
};
const html = (tag, cls, h) => {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (h) e.innerHTML = h;
  return e;
};
const cloneTemplate = id => document.getElementById(id).content.cloneNode(true);

// ── Data loading ───────────────────────────────────────────
async function fetchJSON(url) {
  try {
    const r = await fetch(url);
    if (!r.ok) return null;
    return await r.json();
  } catch { return null; }
}

async function loadProjects() {
  const base = state.benchmarkMode ? BM_DATA_BASE : DATA_BASE;
  const data = await fetchJSON(base + 'projects.json');
  if (!data) return;
  state.projects = data;
  state.dataBuiltAt = data[0]?.built_at ?? null;
}

async function loadTimeline(projectName) {
  if (state.timelines[projectName]) return state.timelines[projectName];
  const base = state.benchmarkMode ? BM_DATA_BASE : DATA_BASE;
  const data = await fetchJSON(base + `timeline-${projectName}.json`);
  if (!data) return [];
  state.timelines[projectName] = data.events || [];
  return state.timelines[projectName];
}

async function loadEvidence(id8) {
  if (state.evidenceCache[id8]) return state.evidenceCache[id8];
  const base = state.benchmarkMode ? BM_DATA_BASE : DATA_BASE;
  const data = await fetchJSON(base + `evidence-${id8}.json`);
  if (!data) return null;
  state.evidenceCache[id8] = data;
  return data;
}

async function loadProjectDetail(projectName) {
  const base = state.benchmarkMode ? BM_DATA_BASE : DATA_BASE;
  return await fetchJSON(base + `project-${projectName}.json`);
}

// ── URL helpers ────────────────────────────────────────────
function ownerInputURL(opts = {}) {
  const params = new URLSearchParams({
    template: 'owner-input.yml',
    ...(opts.title ? { title: opts.title } : {}),
    ...(opts.labels ? { labels: opts.labels } : { labels: 'owner-input' }),
  });
  return `${NEW_ISSUE_BASE}?${params}`;
}

function groundURL(id8, project) {
  return ownerInputURL({
    title: `[Owner input] GROUND agent ${id8} (${project})`,
    labels: 'owner-input',
  });
}

function suggestURL(id8, project) {
  return ownerInputURL({
    title: `[Owner input] SUGGEST action for agent ${id8} (${project})`,
    labels: 'owner-input',
  });
}

function decisionURL(project, decisionId) {
  return ownerInputURL({
    title: `[Owner input] DECISION ${decisionId} (${project})`,
    labels: 'owner-input',
  });
}

function postToTeamURL(project, type) {
  return ownerInputURL({
    title: `[Owner input] ${type} (${project})`,
    labels: 'owner-input',
  });
}

// ── Formatting helpers ─────────────────────────────────────
function fmtTime(ts) {
  if (!ts) return '';
  try {
    const d = new Date(ts);
    // Dubai = UTC+4
    const du = new Date(d.getTime() + 4 * 3600000);
    const pad = n => String(n).padStart(2, '0');
    return `${pad(du.getUTCHours())}:${pad(du.getUTCMinutes())} +04`;
  } catch { return ts; }
}

function fmtDateTime(ts) {
  if (!ts) return '';
  try {
    const d = new Date(ts);
    const du = new Date(d.getTime() + 4 * 3600000);
    const y = du.getUTCFullYear();
    const mo = String(du.getUTCMonth() + 1).padStart(2, '0');
    const day = String(du.getUTCDate()).padStart(2, '0');
    const h = String(du.getUTCHours()).padStart(2, '0');
    const m = String(du.getUTCMinutes()).padStart(2, '0');
    return `${day}/${mo}/${y} ${h}:${m} +04`;
  } catch { return ts; }
}

function agentStateBadge(status) {
  const map = {
    active: ['🟢', 'badge-green', 'active'],
    retired: ['⚫', 'badge-grey', 'retired'],
    stopped: ['🔴', 'badge-red', 'stopped'],
    error: ['🔴', 'badge-red', 'error'],
    waiting: ['🟡', 'badge-yellow', 'waiting'],
  };
  const [icon, cls, text] = map[status] || ['', 'badge-grey', status];
  const b = el('span', `badge ${cls}`);
  b.textContent = `${icon} ${text}`;
  return b;
}

function proofGradeBadge(grade) {
  const map = {
    CI: 'badge-green',
    READBACK: 'badge-blue',
    LOCAL: 'badge-yellow',
    'CLAIM-ONLY': 'badge-grey',
    OWNER: 'badge-purple',
  };
  return el('span', `badge ${map[grade] || 'badge-grey'}`, grade);
}

function verdictEl(verdict) {
  if (!verdict) return null;
  const d = el('div', 'verdict-row');
  if (verdict.includes('ALIGNED')) d.classList.add('verdict-aligned');
  else if (verdict.includes('CORRECTED')) d.classList.add('verdict-corrected');
  else if (verdict.includes('ESCALATE')) d.classList.add('verdict-escalate');
  d.textContent = `OwnerTeammember: ${verdict}`;
  return d;
}

// Simple Markdown → HTML (just enough for the protocol)
function markdownToHTML(md) {
  let h = escapeHtml(md);
  // Code blocks
  h = h.replace(/```(?:\w+)?\n([\s\S]*?)```/g, (_, c) =>
    `<pre><code>${c}</code></pre>`);
  // Inline code
  h = h.replace(/`([^`]+)`/g, '<code>$1</code>');
  // Headers
  h = h.replace(/^#### (.+)$/gm, '<h4>$1</h4>');
  h = h.replace(/^### (.+)$/gm, '<h3>$1</h3>');
  h = h.replace(/^## (.+)$/gm, '<h2>$1</h2>');
  h = h.replace(/^# (.+)$/gm, '<h1>$1</h1>');
  // Bold / italic
  h = h.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
  h = h.replace(/\*([^*]+)\*/g, '<em>$1</em>');
  // Tables (simple)
  h = h.replace(/(\|[^\n]+\|\n)(\|[-| ]+\|\n)((?:\|[^\n]+\|\n)*)/g, (_, head, sep, rows) => {
    const th = head.split('|').filter(Boolean).map(c =>
      `<th>${c.trim()}</th>`).join('');
    const trs = rows.trim().split('\n').map(r =>
      '<tr>' + r.split('|').filter(Boolean).map(c =>
        `<td>${c.trim()}</td>`).join('') + '</tr>'
    ).join('');
    return `<div class="table-wrap"><table><thead><tr>${th}</tr></thead><tbody>${trs}</tbody></table></div>`;
  });
  // Links
  h = h.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>');
  // Blockquote
  h = h.replace(/^&gt; (.+)$/gm, '<blockquote>$1</blockquote>');
  // Horizontal rule
  h = h.replace(/^---$/gm, '<hr>');
  // Lists
  h = h.replace(/^- (.+)$/gm, '<li>$1</li>');
  h = h.replace(/(<li>[\s\S]*?<\/li>)(?!\n<li>)/g, '<ul>$1</ul>');
  // Paragraphs
  h = h.replace(/\n\n([^<])/g, '\n<p>$1');
  return h;
}

function escapeHtml(text) {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

// ── Router ─────────────────────────────────────────────────
function navigate(hash) {
  window.location.hash = hash;
}

function parseHash(h) {
  const parts = h.replace(/^#/, '').split('/');
  return {
    view: parts[0] || 'home',
    arg1: parts[1],
    arg2: parts[2],
  };
}

async function render() {
  const { view, arg1, arg2 } = parseHash(window.location.hash);

  // Update nav tabs
  document.querySelectorAll('.nav-tab').forEach(t => {
    t.classList.toggle('active', t.dataset.view === view);
  });

  const app = $('app');
  app.innerHTML = '<div class="loading"><span class="spinner"></span> Loading…</div>';

  // Ensure projects are loaded
  if (!state.projects.length) {
    await loadProjects();
  }

  switch (view) {
    case 'home': await renderHome(app); break;
    case 'project': await renderProject(app, arg1); break;
    case 'agent': await renderAgent(app, arg1, arg2); break;
    case 'timeline': await renderTimeline(app, arg1); break;
    case 'decision': await renderDecision(app, arg1, arg2); break;
    case 'owner-inputs': await renderOwnerInputs(app); break;
    case 'protocol': await renderProtocol(app); break;
    case 'benchmarks': await renderBenchmarks(app); break;
    default: await renderHome(app);
  }
}

// ── Home view ──────────────────────────────────────────────
async function renderHome(app) {
  const frag = cloneTemplate('tpl-home');
  app.innerHTML = '';
  app.appendChild(frag);

  // Needs-you
  const nyList = $('needs-you-list');
  const nySection = $('needs-you');
  let nyCount = 0;

  state.projects.forEach(p => {
    const ood = p.open_owner_decisions || [];
    ood.forEach(d => {
      const li = el('li');
      li.innerHTML = `<strong>${d.id}</strong> — ${escapeHtml(d.ask)} `;
      const link = el('a', 'btn btn-small');
      link.textContent = 'Decision card →';
      link.href = `#decision/${p.project}/${encodeURIComponent(d.id)}`;
      li.appendChild(link);
      nyList.appendChild(li);
      nyCount++;
    });
    // Owner inputs (open)
    if (p.is_benchmark) return; // no live inputs in benchmark
  });

  if (nyCount === 0) nySection.classList.add('empty');

  // Liveness strip
  if (state.dataBuiltAt) {
    $('data-built-at').textContent = `Data: ${fmtDateTime(state.dataBuiltAt)}`;
  }

  // Projects table
  const tbody = $('projects-tbody');
  if (!state.projects.length) {
    tbody.innerHTML = `<tr><td colspan="6" class="empty-state">No projects loaded</td></tr>`;
  }
  state.projects.forEach(p => {
    const ctrl = p.control || {};
    const agentsActive = (p.agents || []).filter(a => a.status === 'active').length;
    const agentsRetired = (p.agents || []).filter(a => a.status === 'retired').length;

    const hold = ctrl.hold;
    const healthEl = hold
      ? `<span class="badge badge-purple">⏸ HOLD</span>`
      : `<span class="badge badge-green">▶ running</span>`;

    const lastCycle = '—'; // would come from coordinator evidence

    const tr = el('tr');
    tr.innerHTML = `
      <td><a href="#project/${p.project}">${escapeHtml(p.project)}</a></td>
      <td>${escapeHtml(ctrl.coordinator || '—')}<br>
          <span class="badge badge-grey" style="margin-top:3px">epoch ${ctrl.epoch || 1}</span></td>
      <td>${agentsActive} active, ${agentsRetired} retired</td>
      <td>${healthEl}</td>
      <td>${lastCycle}</td>
      <td>
        <a href="#project/${p.project}" class="btn btn-small">View →</a>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

// ── Project view ───────────────────────────────────────────
async function renderProject(app, projectName) {
  if (!projectName) { navigate('#home'); return; }
  const proj = state.projects.find(p => p.project === projectName);
  if (!proj) { app.innerHTML = `<div class="empty-state">Project "${escapeHtml(projectName)}" not found.</div>`; return; }

  const detail = await loadProjectDetail(projectName);
  const frag = cloneTemplate('tpl-project');
  app.innerHTML = '';
  app.appendChild(frag);

  $('back-to-home').addEventListener('click', () => navigate('#home'));
  $('project-title').textContent = projectName;

  const ctrl = proj.control || detail?.registry?.control || {};
  const hold = ctrl.hold;
  if (hold) {
    const hb = $('project-hold-badge');
    hb.innerHTML = `<span class="badge badge-purple">⏸ HOLD — ${escapeHtml(hold.owner_words || '')}</span>`;
  }

  // Workflow card
  const wf = proj.workflow || detail?.registry?.workflow || {};
  $('workflow-words').textContent = wf.owner_words
    ? `"${wf.owner_words}"`
    : '(no workflow card)';

  const stepsEl = $('workflow-steps');
  (wf.loop || []).forEach(step => {
    const d = el('div', 'workflow-step');
    d.textContent = step;
    stepsEl.appendChild(d);
  });

  if (wf.current) {
    $('workflow-current').textContent = `Current: ${JSON.stringify(wf.current)}`;
  }

  // Agents table
  const tbody = $('agents-tbody');
  const agents = proj.agents || [];
  if (!agents.length) {
    tbody.innerHTML = `<tr><td colspan="6" class="empty-state">No agents</td></tr>`;
  }
  agents.forEach(a => {
    const tr = el('tr');
    const genBadge = `<span class="badge badge-grey">g${a.generation}</span>`;
    const retiredNote = a.retired
      ? `<br><span class="badge badge-grey" style="font-size:0.72rem">retired ${fmtDateTime(a.retired)}</span>`
      : '';

    const tnum = a.evidence_thread_num;
    const threadLink = tnum
      ? `<a href="https://github.com/${REPO}/issues/${tnum}" target="_blank" rel="noopener">#${tnum}</a>`
      : '—';

    tr.innerHTML = `
      <td>
        <a href="#agent/${projectName}/${a.chat_id8}">
          ${escapeHtml(a.role)}${a.alias ? ` (${escapeHtml(a.alias)})` : ''}
        </a>
        <br><code style="font-size:0.78rem;color:var(--text-3)">${a.chat_id8}</code>
        ${retiredNote}
      </td>
      <td>${genBadge}</td>
      <td id="agent-state-${a.chat_id8}"></td>
      <td>${threadLink}</td>
      <td><code style="font-size:0.75rem;word-break:break-all">${escapeHtml(a.branch || '—')}</code></td>
      <td><a href="#agent/${projectName}/${a.chat_id8}" class="btn btn-small">Evidence →</a></td>
    `;
    const stateCell = tr.querySelector(`#agent-state-${a.chat_id8}`);
    stateCell.appendChild(agentStateBadge(a.status));
    tbody.appendChild(tr);
  });

  // Leases
  const leasesBody = $('leases-body');
  const leases = proj.leases || detail?.leases || [];
  const sod = detail?.registry?.standing_owner_decisions || [];
  const leaseEntries = leases.length
    ? leases
    : sod.filter(d => d.toLowerCase().includes('lease'));

  if (leaseEntries.length) {
    leaseEntries.forEach(l => {
      const d = el('div', 'lease-row');
      d.textContent = typeof l === 'string' ? l : JSON.stringify(l);
      leasesBody.appendChild(d);
    });
  } else {
    leasesBody.innerHTML = '<div class="lease-row" style="color:var(--text-3)">No active leases recorded</div>';
  }

  // Outside writes
  const owSection = $('outside-writes-section');
  const ows = proj.outside_writes || [];
  if (ows.length) {
    const h2 = el('h2', '', 'Outside writes');
    h2.style.cssText = 'font-size:1rem;margin:16px 0 8px';
    owSection.appendChild(h2);
    ows.forEach(w => {
      const d = el('div', 'outside-write-flag');
      d.innerHTML = `⚠ Outside write: ${escapeHtml(typeof w === 'string' ? w.slice(0, 200) : JSON.stringify(w))}`;
      owSection.appendChild(d);
    });
  }

  // Open decisions
  const odSection = $('open-decisions-list');
  const ood = proj.open_owner_decisions || detail?.registry?.open_owner_decisions || [];
  if (!ood.length) {
    odSection.innerHTML = '<p style="color:var(--text-3);font-size:0.85rem">No open decisions.</p>';
  } else {
    ood.forEach(d => {
      const card = el('div', 'decision-card');
      card.innerHTML = `
        <div class="decision-card-header">
          <span class="decision-card-id">${escapeHtml(d.id)}</span>
          <span class="decision-card-ask">${escapeHtml(d.ask)}</span>
        </div>
        <div class="decision-card-body">
          ${d.link ? `<a href="${escapeHtml(d.link)}" target="_blank" rel="noopener" class="btn btn-small">Evidence →</a>` : ''}
          <a href="#decision/${projectName}/${encodeURIComponent(d.id)}" class="btn btn-small" style="margin-left:6px">Decision card →</a>
        </div>
      `;
      odSection.appendChild(card);
    });
  }

  // Post to team button
  const postBtn = $('post-btn');
  if (state.benchmarkMode) {
    postBtn.style.display = 'none';
  } else {
    postBtn.href = postToTeamURL(projectName, 'INFO');
  }
}

// ── Agent view ─────────────────────────────────────────────
async function renderAgent(app, projectName, id8) {
  if (!projectName || !id8) { navigate('#home'); return; }

  const frag = cloneTemplate('tpl-agent');
  app.innerHTML = '';
  app.appendChild(frag);

  $('back-to-project').addEventListener('click', () => navigate(`#project/${projectName}`));

  const evData = await loadEvidence(id8);
  const agent = evData?.agent;

  if (!agent) {
    app.innerHTML = `<div class="empty-state">No evidence data found for agent ${escapeHtml(id8)}.</div>`;
    return;
  }

  $('agent-title').textContent = `${agent.role} · ${id8}`;
  const badges = $('agent-badges');
  badges.appendChild(agentStateBadge(agent.status));
  if (agent.generation) {
    badges.appendChild(el('span', 'badge badge-grey', `gen ${agent.generation}`));
  }

  // Action buttons
  if (state.benchmarkMode) {
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
async function renderTimeline(app, projectFilter) {
  const frag = cloneTemplate('tpl-timeline');
  app.innerHTML = '';
  app.appendChild(frag);

  // Load all timelines
  const allEvents = [];
  for (const p of state.projects) {
    const events = await loadTimeline(p.project);
    events.forEach(e => { allEvents.push({ ...e, _project: p.project }); });
  }

  allEvents.sort((a, b) => (a.ts || '').localeCompare(b.ts || ''));

  // Check if any are reconstructed
  const anyReconstructed = allEvents.some(e => e.reconstructed);
  if (anyReconstructed) {
    $('tl-reconstructed-note').style.display = '';
  }

  // Populate project filter
  const projFilter = $('tl-project-filter');
  state.projects.forEach(p => {
    const o = el('option', '', p.project);
    o.value = p.project;
    projFilter.appendChild(o);
  });
  if (projectFilter) projFilter.value = projectFilter;

  // Populate actor filter
  const actorFilter = $('tl-actor-filter');
  const actors = [...new Set(allEvents.map(e => e.actor).filter(Boolean))];
  actors.forEach(a => {
    const o = el('option', '', a);
    o.value = a;
    actorFilter.appendChild(o);
  });

  let selectedEvent = null;

  function renderEvents() {
    const proj = projFilter.value;
    const actor = actorFilter.value;
    const type = $('tl-type-filter').value;
    const text = $('tl-text-filter').value.toLowerCase();

    const filtered = allEvents.filter(e =>
      (!proj || e._project === proj || e.project === proj) &&
      (!actor || e.actor === actor) &&
      (!type || e.type === type) &&
      (!text || JSON.stringify(e).toLowerCase().includes(text))
    );

    const container = $('timeline-events');
    container.innerHTML = '';

    if (!filtered.length) {
      container.innerHTML = '<div class="empty-state">No events match the filters.</div>';
      return;
    }

    filtered.forEach(ev => {
      const row = el('div', 'tl-event' + (ev.reconstructed ? ' reconstructed' : ''));

      const ts = el('span', 'tl-ts', fmtDateTime(ev.ts));
      const actor = el('span', 'tl-actor', ev.actor || '');
      const text = el('span', 'tl-text');

      // Text summary
      let summary = '';
      switch (ev.type) {
        case 'TASK_EVIDENCE':
          summary = `TASK EVIDENCE #${ev.seq} — ${ev.task || ''} [${ev.status || ''}]`;
          break;
        case 'VERDICT':
          summary = `Verdict: ${ev.verdict || ''}`;
          break;
        case 'COORDINATOR_EVIDENCE':
          summary = `COORDINATOR EVIDENCE cycle ${ev.cycle || '?'} epoch ${ev.epoch || '?'}`;
          if (ev.time_corrected) summary += ' [time-corrected]';
          if (ev.needs_you_count > 0) summary += ` — NEEDS YOU (${ev.needs_you_count})`;
          break;
        case 'FOR_TC':
          summary = `FOR TeamCoordinator: ${(ev.text || '').slice(0, 80)}`;
          break;
        case 'CONTROL_EPOCH':
          summary = `CONTROL EPOCH: ${(ev.text || '').slice(0, 80)}`;
          break;
        case 'OWNER_DECISION':
          summary = `Owner decision: ${(ev.text || '').slice(0, 80)}`;
          break;
        case 'OUTSIDE_WRITE':
          summary = `⚠ Outside write: ${(ev.text || '').slice(0, 80)}`;
          break;
        default:
          summary = ev.type + (ev.text ? ': ' + String(ev.text).slice(0, 60) : '');
      }
      text.textContent = summary;

      // Type badge
      const typeBadge = el('span', `badge badge-grey tl-badge`, ev.type?.replace(/_/g, ' '));

      if (ev.reconstructed) {
        const rb = el('span', 'reconstructed-label', 'reconstructed');
        row.appendChild(ts);
        row.appendChild(actor);
        row.appendChild(text);
        row.appendChild(rb);
        row.appendChild(typeBadge);
      } else {
        row.appendChild(ts);
        row.appendChild(actor);
        row.appendChild(text);
        row.appendChild(typeBadge);
      }

      // Click → show raw
      row.addEventListener('click', () => {
        selectedEvent = ev;
        const rawPanel = $('tl-raw-panel');
        const rawText = $('tl-raw-text');
        rawPanel.style.display = '';
        rawText.textContent = JSON.stringify(ev, null, 2);
        row.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
      });

      container.appendChild(row);
    });
  }

  [$('tl-project-filter'), $('tl-actor-filter'),
   $('tl-type-filter'), $('tl-text-filter')].forEach(f => {
    f.addEventListener('change', renderEvents);
    f.addEventListener('input', renderEvents);
  });

  renderEvents();
}

// ── Decision card view ─────────────────────────────────────
async function renderDecision(app, projectName, decisionId) {
  const frag = cloneTemplate('tpl-decision-card');
  app.innerHTML = '';
  app.appendChild(frag);

  $('back-from-decision').addEventListener('click', () => navigate(`#project/${projectName}`));

  const proj = state.projects.find(p => p.project === projectName);
  const ood = proj?.open_owner_decisions || [];
  const d = ood.find(x => x.id === decodeURIComponent(decisionId));

  if (!d) {
    app.innerHTML = `<div class="empty-state">Decision "${escapeHtml(decisionId)}" not found in ${escapeHtml(projectName)}.</div>`;
    return;
  }

  $('dc-id').textContent = d.id;
  $('dc-ask').textContent = d.ask;

  if (d.link) {
    $('dc-links').innerHTML = `<a href="${escapeHtml(d.link)}" target="_blank" rel="noopener" class="btn btn-small">Evidence →</a>`;
  }

  if (state.benchmarkMode) {
    $('dc-answer-btn').style.display = 'none';
  } else {
    $('dc-answer-btn').href = decisionURL(projectName, d.id);
  }
}

// ── Owner inputs view ──────────────────────────────────────
async function renderOwnerInputs(app) {
  const frag = cloneTemplate('tpl-owner-inputs');
  app.innerHTML = '';
  app.appendChild(frag);

  $('new-input-btn').href = ownerInputURL();
  if (state.benchmarkMode) {
    $('new-input-btn').style.display = 'none';
  }

  const list = $('oi-list');
  const count = $('oi-count');

  // In real mode: would fetch owner-inputs.json
  // In benchmark mode: show a simulated handled example
  if (state.benchmarkMode) {
    const simEx = el('div', 'oi-row');
    simEx.innerHTML = `
      <span class="oi-state"><span class="badge badge-green">handled</span></span>
      <span class="oi-type">DECISION</span>
      <span class="oi-text">Approve the 13 difficulty corrections confirmed by both g1 agents (G9-DIFF-13). Option A.
        <br><em style="font-size:0.78rem;color:var(--text-3)">Handler receipt (simulated): HANDLED: 13 corrections approved. Routed to validator g2 for implementation.</em>
      </span>
      <span class="oi-ts">15 Oct 08:20 +04</span>
    `;
    list.appendChild(simEx);
    count.textContent = '1 (simulated)';
    return;
  }

  const ownerInputs = await fetchJSON(DATA_BASE + 'owner-inputs.json') || [];
  count.textContent = `${ownerInputs.length}`;

  if (!ownerInputs.length) {
    list.innerHTML = `<div style="padding:20px 16px;color:var(--text-3);font-size:0.875rem">
      No owner inputs yet. Use the "New input" button to post one.
    </div>`;
    return;
  }

  ownerInputs.forEach(inp => {
    const row = el('div', 'oi-row');
    const stateBadge = inp.state === 'handled'
      ? `<span class="badge badge-green">handled</span>`
      : inp.state === 'acknowledged'
      ? `<span class="badge badge-yellow">acknowledged</span>`
      : `<span class="badge badge-blue">open</span>`;

    row.innerHTML = `
      <span class="oi-state">${stateBadge}</span>
      <span class="oi-type">${escapeHtml(inp.type || '')}</span>
      <span class="oi-text">${escapeHtml(inp.text || '')}
        ${inp.receipt ? `<br><em style="font-size:0.78rem;color:var(--text-3)">${escapeHtml(inp.receipt)}</em>` : ''}
      </span>
      <span class="oi-ts">${fmtDateTime(inp.ts)}</span>
    `;
    list.appendChild(row);
  });
}

// ── Protocol view ──────────────────────────────────────────
async function renderProtocol(app) {
  const frag = cloneTemplate('tpl-protocol');
  app.innerHTML = '';
  app.appendChild(frag);

  if (!state.protocolMd) {
    // Try to load the protocol markdown
    try {
      const r = await fetch('../protocol/TEAM_PROTOCOL.md');
      if (r.ok) state.protocolMd = await r.text();
    } catch { /* ok */ }

    if (!state.protocolMd) {
      try {
        const r = await fetch('protocol/TEAM_PROTOCOL.md');
        if (r.ok) state.protocolMd = await r.text();
      } catch { /* ok */ }
    }
  }

  const mdEl = $('protocol-md');
  const tocEl = $('toc-list');

  if (!state.protocolMd) {
    mdEl.innerHTML = `<div class="empty-state">Protocol file not found. <a href="https://github.com/${REPO}/blob/main/protocol/TEAM_PROTOCOL.md" target="_blank" rel="noopener">View on GitHub →</a></div>`;
    return;
  }

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
async function renderBenchmarks(app) {
  const frag = cloneTemplate('tpl-benchmarks');
  app.innerHTML = '';
  app.appendChild(frag);

  const list = $('benchmarks-list');

  const benchmarks = [
    {
      project: 'grade9-pilot',
      snapshot: '2026-10-15',
      note: 'Grade 9 pilot — with events.jsonl, two coordinator epochs, two agent generations.',
    },
    {
      project: 'imo-ab-test',
      snapshot: '2026-10-15',
      note: 'IMO AB test — no events.jsonl (timeline reconstructed from threads + inbox). Includes FAIL→fix→PASS chain, outside write, role conflict, superseded Owner words.',
    },
  ];

  benchmarks.forEach(bm => {
    const row = el('div');
    row.style.cssText = 'padding:14px 16px;border-bottom:1px solid var(--border)';
    row.innerHTML = `
      <div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap">
        <strong>${escapeHtml(bm.project)}</strong>
        <span class="badge badge-yellow">snapshot ${escapeHtml(bm.snapshot)}</span>
      </div>
      <p style="font-size:0.85rem;color:var(--text-2);margin:6px 0">${escapeHtml(bm.note)}</p>
      <button class="btn btn-small bm-load-btn" data-project="${bm.project}">
        Load this benchmark
      </button>
    `;
    list.appendChild(row);
  });

  list.querySelectorAll('.bm-load-btn').forEach(btn => {
    btn.addEventListener('click', async () => {
      const project = btn.dataset.project;
      state.benchmarkMode = true;
      state.benchmarkProject = project;
      state.projects = [];
      state.timelines = {};
      state.evidenceCache = {};

      // Update banner
      const banner = $('benchmark-banner');
      banner.classList.add('visible');
      banner.querySelector('#exit-benchmark') || 0;

      await loadProjects();
      navigate('#home');
    });
  });
}

// ── Init ───────────────────────────────────────────────────
function init() {
  // Nav tab clicks
  document.querySelectorAll('.nav-tab').forEach(tab => {
    tab.addEventListener('click', () => {
      navigate('#' + tab.dataset.view);
    });
  });

  // Exit benchmark
  $('exit-benchmark').addEventListener('click', () => {
    state.benchmarkMode = false;
    state.benchmarkProject = null;
    state.projects = [];
    state.timelines = {};
    state.evidenceCache = {};
    $('benchmark-banner').classList.remove('visible');
    navigate('#home');
  });

  // Hash change → re-render
  window.addEventListener('hashchange', render);

  // Initial render
  if (!window.location.hash) window.location.hash = '#home';
  render();
}

document.addEventListener('DOMContentLoaded', init);
