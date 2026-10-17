'use strict';

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

// The screen uses Muscat (+04) clocks. Never turn missing or malformed
// source timestamps into a plausible-looking time.
function sourceTime(ts) {
  if (!ts || !Number.isFinite(new Date(ts).getTime())) return 'unknown';
  return fmtTime(ts);
}
function ownerActivityText(inp) {
  return 'posted ' + sourceTime(inp.ts) + ' · updated ' + sourceTime(inp.updated_at);
}
function decisionAskedAt(d) {
  return d.asked_at || d.created_at || d.ts || null;
}
function decisionAskedText(d) {
  const asked = decisionAskedAt(d);
  return asked && sourceTime(asked) !== 'unknown'
    ? 'Asked at ' + sourceTime(asked)
    : 'Asked at: not recorded in source';
}
async function loadProtocolSource() {
  if (state.protocolMd) return state.protocolMd;
  for (const url of ['protocol/TEAM_PROTOCOL.md', '../protocol/TEAM_PROTOCOL.md']) {
    try {
      const res = await fetch(url, { cache: 'no-store' });
      if (res.ok) { state.protocolMd = await res.text(); return state.protocolMd; }
    } catch { /* next source path */ }
  }
  return null;
}
async function currentProtocolVersion() {
  const md = await loadProtocolSource();
  const match = md?.match(/^#\s+Team protocol\s+(v\d+(?:\.\d+)+)\b/im);
  return match ? match[1] : null;
}
async function displayedDecisionAsk(d) {
  if (d.id !== 'PROTO-FREEZE') return String(d.ask || 'Decision');
  const version = await currentProtocolVersion();
  // Keep the original historic ask in the registry. Never silently turn
  // that into a new approval for a later protocol version.
  return version
    ? 'Review freeze of current Team protocol ' + version +
      ' (from protocol source; original request remains in registry)'
    : 'Current protocol version UNKNOWN — read source before any freeze';
}

function agentStateBadge(status) {
  const map = {
    active: ['🟢', 'badge-green', 'active'],
    retired: ['⚫', 'badge-grey', 'retired'],
    stopped: ['🔴', 'badge-red', 'stopped'],
    error: ['🔴', 'badge-red', 'error'],
    waiting: ['🟡', 'badge-yellow', 'waiting'],
    standby: ['⚪', 'badge-grey', 'standby'],
    hold: ['🟣', 'badge-purple', 'hold'],
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


async function renderHome(app) {
  const frag = cloneTemplate('tpl-home');
  app.innerHTML = '';
  app.appendChild(frag);

  const newInput = $('home-new-input');
  newInput.href = '#owner-inputs';
  if (state.benchmarkMode) newInput.hidden = true;
  const nyList = $('needs-you-list');
  const nySection = $('needs-you');
  const inputs = await loadOwnerInputs();
  if (inputs === null && !state.benchmarkMode) {
    nyList.appendChild(el('li', 'needs-unknown',
      'Owner-inputs source unavailable · UNKNOWN · cannot presume handled.'));
  } else {
    for (const inp of inputs) {
      const status = ownerInputState(inp);
      // Missing/foreign GitHub association is never an Owner input in Needs-you.
      if (inp.is_outsider === true ||
          !['OWNER', 'MEMBER', 'COLLABORATOR'].includes(inp.author_association)) continue;
      if (status === 'HANDLED' || status === 'SUPERSEDED') continue;
      const li = el('li', 'needs-input');
      li.appendChild(el('strong', '', 'Owner input ' + String(inp.id || ('#' + inp.number) || '—') + ' '));
      li.appendChild(ownerStatusBadge(status));
      if (inp.protected_action) {
        li.appendChild(el('span', 'badge badge-grey', 'UNVERIFIED · no action'));
      }
      const what = String(inp.text || inp.type || 'Request').slice(0, 140);
      li.appendChild(el('div', 'needs-plain', 'What: ' + what +
        ' · For: ' + String(inp.target || 'the team') +
        ' · Waiting for: ' + String(inp.trace?.waiting_for || 'TeamCoordinator')));
      li.appendChild(el('div', 'owner-clock', ownerActivityText(inp)));
      const trace = el('a', 'btn btn-small', 'Trace →');
      trace.href = '#trace/' + encodeURIComponent(String(inp.id || inp.number));
      li.appendChild(trace);
      const link = el('a', 'btn btn-small', 'View input →');
      link.href = '#owner-inputs';
      li.appendChild(link);
      nyList.appendChild(li);
    }
  }
  for (const p of state.projects) {
    for (const d of p.open_owner_decisions || []) {
      const li = el('li', 'needs-pending');
      li.appendChild(el('strong', '', String(d.id || 'Decision')));
      li.appendChild(el('div', 'needs-plain',
        'Decision needed: ' + await displayedDecisionAsk(d) +
        ' · Waiting for: Owner to answer'));
      li.appendChild(el('div', 'owner-clock',
        'posted ' + sourceTime(decisionAskedAt(d)) +
        ' · updated ' + sourceTime(d.updated_at || decisionAskedAt(d))));
      const link = el('a', 'btn btn-small', 'Trace →');
      link.href = '#decision/' + encodeURIComponent(p.project) +
        '/' + encodeURIComponent(d.id || '');
      li.appendChild(link);
      renderDecisionAnswers(li, p.project, d, await displayedDecisionAsk(d), inputs);
      nyList.appendChild(li);
    }
  }
  if (!nyList.children.length) nySection.classList.add('empty');

  // Captured cycle state, never inferred uptime from absence of HOLD.
  // Each coordinator is shown beside its own project; a single global
  // STALE label would hide which project's observation is old.
  const coordinatorList = $('live-coordinators');
  if (!state.projects.length) {
    coordinatorList.appendChild(el('span', 'live-item',
      'Projects · coordinator status UNKNOWN'));
  }
  state.projects.forEach(p => {
    const observed = freshState(p);
    const line = el('div', 'live-item coordinator-by-project');
    const dot = el('span', 'dot ' + ({
      'RUNNING-observed': 'dot-green', STALE: 'dot-yellow',
      UNKNOWN: 'dot-grey', HOLD: 'dot-purple'
    }[observed] || 'dot-grey'));
    line.appendChild(dot);
    line.appendChild(el('span', '', String(p.project) + ' · ' +
      String(p.control?.coordinator || 'coordinator not recorded') +
      ' · ' + observed +
      (p.last_cycle_at ? ' · last update ' + fmtDateTime(p.last_cycle_at) :
       ' · last update unknown')));
    coordinatorList.appendChild(line);
  });
  // Even accepted GitHub contributors share one account across team roles.
  // This is evidence of a scoped post, not proof of coordinator identity.
  const limit = el('span', 'liveness-limit',
    'Observed GitHub post only: outsider comments are excluded by OWNER/MEMBER/COLLABORATOR author association. Team roles share one GitHub account, so the actual role cannot be distinguished.');
  limit.style.cssText = 'display:block;flex-basis:100%;width:100%;font-size:0.72rem;color:var(--text-3);overflow-wrap:anywhere';
  $('liveness-strip').appendChild(limit);
  $('live-otm').className = 'dot dot-grey';
  $('live-otm-time').textContent = 'UNKNOWN (no independent observation)';
  $('live-gh').className = 'dot dot-grey';
  if (state.dataBuiltAt) {
    $('data-built-at').textContent =
      'data built ' + fmtTime(state.dataBuiltAt) + ' · from build-info, not live uptime';
  }

  renderAutoResponseTable($('auto-response-home'), state.projects);

  // Projects table
  const tbody = $('projects-tbody');
  if (!state.projects.length) {
    tbody.innerHTML = `<tr><td colspan="6" class="empty-state">No projects loaded</td></tr>`;
  }
  state.projects.forEach(p => {
    const ctrl = p.control || {};
    const agentsActive = (p.agents || []).filter(a => a.status === 'active').length;
    const agentsRetired = (p.agents || []).filter(a => a.status === 'retired').length;
    const agentsStandby = (p.agents || []).filter(a => a.status === 'standby').length;
    const agentsHold = (p.agents || []).filter(a => a.status === 'hold').length;

    const healthEl = freshnessBadge(freshState(p)).outerHTML;
    const lastCycle = p.last_cycle_at ? fmtDateTime(p.last_cycle_at) : '—';

    const tr = el('tr');
    tr.innerHTML = `
      <td><a href="#project/${escapeHtml(encodeURIComponent(p.project))}">${escapeHtml(p.project)}</a></td>
      <td>${escapeHtml(ctrl.coordinator || '—')}<br>
          <span class="badge badge-grey" style="margin-top:3px">epoch ${ctrl.epoch || 1}</span></td>
      <td>${agentsActive} active, ${agentsStandby} standby, ${agentsHold} hold, ${agentsRetired} retired</td>
      <td>${healthEl}</td>
      <td>${lastCycle}</td>
      <td>
        <a href="#project/${escapeHtml(encodeURIComponent(p.project))}" class="btn btn-small">View →</a>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

// ── Project view ───────────────────────────────────────────

