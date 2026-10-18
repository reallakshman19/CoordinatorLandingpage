'use strict';

function decisionProvenance(item) {
  const text = typeof item === 'string' ? item : String(item?.text || '');
  if (text.toLowerCase().includes('(delegated)')) return 'delegated (OwnerTeammember)';
  if ((item && typeof item === 'object' && typeof item.owner_words === 'string' &&
       item.owner_words.trim()) || /Owner(?:'s)? words:\s*["“]/i.test(text)) return 'Owner';
  return 'unverified';
}
function allowedExternalLink(url, repository) {
  if (typeof url !== 'string' || typeof repository !== 'string' ||
      !/^[A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+$/.test(repository)) return null;
  return /^https:\/\/github\.com\/[A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+\/(issues|pull)\/\d+(?:#issuecomment-\d+)?$/.test(url) &&
    url.startsWith('https://github.com/' + repository + '/') ? url : null;
}
function autoResponseStatus(entry) {
  if (!entry || !['yes','no','critical'].includes(entry.allowed) ||
      typeof entry.until !== 'string') return 'UNKNOWN';
  // "forever" is an explicit recorded end date, not an invalid timestamp.
  const deadline = entry.until.trim().toLowerCase() === 'forever'
    ? Infinity : Date.parse(entry.until);
  if (Number.isNaN(deadline)) return 'UNKNOWN';
  if (deadline <= Date.now()) return 'EXPIRED';
  return entry.allowed === 'no' ? 'NOT_ALLOWED' : 'IN_SCOPE';
}
function renderAutoResponseTable(container, projects) {
  const wrap = el('div','table-wrap'), table = el('table','auto-response-table');
  const head = el('thead'), headings = el('tr');
  for (const caption of ['Project','Who may answer routine questions','Scope','Until',
                         'Critical tier rules']) headings.appendChild(el('th','',caption));
  head.appendChild(headings); table.appendChild(head);
  const body = el('tbody');
  for (const p of projects) {
    // Each list entry is an independent delegation scope. Old dicts remain
    // one scope; missing declarations still display an UNKNOWN row.
    const scopes = Array.isArray(p.auto_response)
      ? p.auto_response : [p.auto_response];
    for (const response of scopes) {
      if (response != null && (typeof response !== 'object' ||
          Array.isArray(response))) continue;
      const tr = el('tr'), current = autoResponseStatus(response);
      const rules = response?.critical_rules ||
        'Critical requests require an Owner decision. No delegation recorded.';
      const who = current === 'EXPIRED' ? 'EXPIRED — no current delegation' :
        current !== 'IN_SCOPE' ? 'No confirmed routine delegation' :
        response.allowed === 'critical'
          ? 'Delegated team — routine only; critical to Owner'
          : 'Delegated team — within recorded scope';
      tr.appendChild(el('td','',String(p.project)));
      const whoCell = el('td','auto-response-who');
      whoCell.appendChild(el('span','',who));
      if (response?.allowed === 'critical' &&
          /not authorised|not authorized/i.test(response?.owner_words || '')) {
        whoCell.firstElementChild.textContent = 'No automatic response — Owner required';
      }
      if (response?.allowed)
        whoCell.appendChild(el('span','badge badge-grey auto-response-allowed',
                               String(response.allowed)));
      if (current === 'EXPIRED') whoCell.appendChild(el('span','badge badge-red','EXPIRED'));
      tr.appendChild(whoCell);
      tr.appendChild(el('td','',String(response?.scope || 'Not recorded')));
      tr.appendChild(el('td','',String(response?.until || 'Not recorded')));
      tr.appendChild(el('td','',String(rules)));
      body.appendChild(tr);
    }
  }
  table.appendChild(body); wrap.appendChild(table); container.appendChild(wrap);
}


function wp12HoldBanner(where, hold) {
  if (!where || !hold?.active) return;
  const div = el('div', 'hold-visibility-banner');
  div.appendChild(el('strong', '', 'HOLD — work paused'));
  div.appendChild(el('span', '', 'Since: ' + (hold.since || 'not recorded')));
  if (hold.owner_words) div.appendChild(
    el('span', '', 'Recorded Owner words: ' + hold.owner_words));
  if (hold.recorded) div.appendChild(
    el('span', '', 'Registry HOLD note: ' + hold.recorded));
  where.appendChild(div);
}

function wp12ReportingTree(where, agents) {
  if (!where) return;
  const rows = Array.isArray(agents) ? agents : [];
  if (!rows.length) {
    where.appendChild(el('p', 'note', 'No agent reporting lines recorded.'));
    return;
  }
  const byId = new Map(rows.filter(a => /^[0-9a-f]{8}$/.test(a.chat_id8))
    .map(a => [a.chat_id8, a]));
  const list = el('ul', 'wp12-reporting-list');
  const rendered = new Set();
  const write = (a, visited) => {
    const li = el('li', 'wp12-reporting-agent');
    li.appendChild(el('span', '', String(a.alias || a.chat_id8) +
      ' · ' + String(a.status || 'unknown') + ' · ' + String(a.chat_id8)));
    rendered.add(a.chat_id8);
    const children = rows.filter(x => x.reports_to === a.chat_id8 &&
      x.chat_id8 !== a.chat_id8 && !visited.has(x.chat_id8) &&
      !rendered.has(x.chat_id8));
    if (children.length) {
      const sub = el('ul');
      for (const child of children) {
        const next = new Set(visited); next.add(child.chat_id8);
        sub.appendChild(write(child, next));
      }
      li.appendChild(sub);
    }
    return li;
  };
  for (const agent of rows) {
    if ((!agent.reports_to || !byId.has(agent.reports_to) ||
         agent.reports_to === agent.chat_id8) && !rendered.has(agent.chat_id8))
      list.appendChild(write(agent, new Set([agent.chat_id8])));
  }
  // Cycles have no root. Do not drop their agents: display every unrendered
  // node with an explicit warning, without attempting cyclic recursion.
  const unrendered = rows.filter(a => !rendered.has(a.chat_id8));
  if (unrendered.length) {
    where.appendChild(el('p', 'note wp12-reporting-cycle',
      'reporting cycle — recorded agents shown without inferred hierarchy'));
    for (const agent of unrendered) {
      const li = el('li', 'wp12-reporting-agent');
      li.appendChild(el('span', '', String(agent.alias || agent.chat_id8) +
        ' · ' + String(agent.status || 'unknown') + ' · ' + String(agent.chat_id8)));
      list.appendChild(li);
    }
  }
  where.appendChild(list);
}

function wp12ChildProgress(where, progress, repository) {
  if (!where) return;
  if (!progress || progress.status === 'not_recorded') {
    where.appendChild(el('p','note','No v3.6 child issues registered.'));
    return;
  }
  if (progress.status !== 'known') {
    where.appendChild(el('p', 'note', 'v3.6 child progress UNKNOWN — not all titles verified.'));
    return;
  }
  where.appendChild(el('strong','wp12-child-total',
    'v3.6 child progress · derived from title (not E/acceptance): ' + progress.done + '/' + progress.total + ' DONE'));
  for (const item of progress.items || []) {
    const safe = allowedExternalLink(item.url, repository);
    if (!safe || !safe.includes('/issues/')) continue;
    const a = el('a','wp12-child-link',String(item.state) + ' · ' + String(item.title));
    a.href = safe; a.target = '_blank'; a.rel = 'noopener noreferrer';
    where.appendChild(a);
  }
}

function wp12HeadStatus(where, info, repository) {
  if (!where || !info || info.status === 'not_recorded') return;
  const wording = info.status === 'superseded'
    ? 'evidence superseded (head moved)'
    : info.status === 'current' ? 'Evidence head matches current PR head'
    : 'Evidence head UNKNOWN (no verified current PR head)';
  where.appendChild(el('span',info.status === 'superseded'
    ? 'badge badge-yellow wp12-evidence-superseded'
    : 'badge badge-grey wp12-evidence-status', wording));
  const link = allowedExternalLink(info.pr_url, repository);
  if (link && link.includes('/pull/')) {
    const a = el('a', 'btn btn-small wp12-head-pr-link', 'Source PR (read-only) →');
    a.href = link; a.rel = 'noopener noreferrer'; a.target = '_blank';
    where.appendChild(a);
  }
}
function wp12HasHostedRun(item, repository) {
  // A self-labelled [CI] is not proof. Even a linked run must belong to
  // the registry's owning repository, not a different project's workflow.
  if (typeof repository !== 'string') return false;
  return Array.isArray(item?.proofs) && item.proofs.some(p => {
    const text = String(p?.line || '');
    const links = text.matchAll(/https:\/\/github\.com\/([A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+)\/actions\/runs\/\d+\b/g);
    for (const link of links) {
      if (link[1].toLowerCase() === repository.toLowerCase()) return true;
    }
    return false;
  });
}


// WP13 P1: visualization only; every text field comes from validated publisher
// projection. No composer, approver button, scheduler or write interaction.

function traceSafeGitHubURL(url) {
  if (typeof url !== 'string') return null;
  const match = /^https:\/\/github\.com\/([A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+)\/(?:(?:issues|pull)\/\d+(?:#issuecomment-\d+)?|blob\/[0-9a-f]{40}\/logs\/[A-Za-z0-9._-]+\/(?:inputs\/OI-\d{8}-\d{6}-[0-9a-f]{4}\.json|receipts\.jsonl)(?:#L\d+)?)$/.exec(url);
  const permitted = new Set([REPO, ...state.projects.map(p => p.repository)]);
  return match && permitted.has(match[1]) ? url : null;
}

async function renderTrace(app, numberRaw) {
  const frag = cloneTemplate('tpl-trace');
  app.innerHTML = '';
  app.appendChild(frag);
  const number = String(numberRaw || '');
  const inputs = await loadOwnerInputs();
  const item = /^(?:\d+|OI-\d{8}-\d{6}-[0-9a-f]{4})$/.test(number) && Array.isArray(inputs)
    ? inputs.find(x => String(x.id || x.number) === number) : null;
  $('trace-back').href = '#owner-inputs';
  if (!item) {
    $('trace-title').textContent = 'Request not found';
    $('trace-explanation').textContent = inputs === null
      ? 'The request records are unavailable. Nothing can be confirmed.'
      : 'No recorded Owner input matches this number.';
    return;
  }
  $('trace-title').textContent = 'Follow request #' + number;
  $('trace-subtitle').textContent = 'What: ' + String(item.text || 'Request') +
    ' · For: ' + String(item.target || 'the team');
  const status = ownerInputState(item);
  $('trace-status').appendChild(ownerStatusBadge(status));
  if (item.is_outsider) {
    $('trace-status').appendChild(el('span', 'badge badge-grey', 'OUTSIDER · UNVERIFIED'));
  }
  const steps = item.trace?.steps || {};
  const specs = [
    ['posted', 'Posted', 'Owner'],
    ['ack', 'ACK', 'TeamCoordinator'],
    ['sent', 'Sent to agent', 'TeamCoordinator'],
    ['evidence', 'Agent evidence', 'agent'],
    ['check', 'Check', 'checker'],
    ['result', 'Result', 'TeamCoordinator']
  ];
  for (const [key, label, who] of specs) {
    const li = el('li', 'trace-step');
    li.dataset.step = key;
    li.appendChild(el('strong', 'trace-step-name', label));
    const datum = steps[key];
    const safe = traceSafeGitHubURL(datum?.url);
    if (safe && datum?.at) {
      const a = el('a', 'trace-proof-link',
        (key === 'result' && datum.accepted === false)
          ? 'Recorded note (not accepted)' : 'View recorded link →');
      a.href = safe;
      a.rel = 'noopener noreferrer';
      a.target = '_blank';
      li.appendChild(a);
      li.appendChild(el('span', 'trace-step-time', fmtDateTime(datum.at)));
    } else {
      li.appendChild(el('span', 'trace-waiting', 'waiting for ' + who));
      li.appendChild(el('span', 'trace-step-time', 'time not recorded'));
    }
    $('trace-steps').appendChild(li);
  }
  $('trace-explanation').textContent =
    'Why this status: ' + String(item.trace?.why ||
      'No confirmed explanation was published with this input.');
  $('trace-disclaimer').textContent =
    'These are recorded links, not proof of completion or Owner approval. ' +
    'If a step has no linked record, it says who we are waiting for.';
}

// ── Protocol view ──────────────────────────────────────────
