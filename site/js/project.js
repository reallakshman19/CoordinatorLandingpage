'use strict';

function renderG8Disagreement(target, data, repository) {
  if (!target || !data || data.status !== 'DISAGREEMENT' || data.flag !== true) return;
  const card = el('div','card');
  card.appendChild(el('div','card-header','DISAGREEMENT · Issue status vs PR state'));
  const body = el('div','card-body');
  body.appendChild(el('p','note','Conflicting source observations; no winner selected or status automatically changed.'));
  const issue = allowedExternalLink(data.issue_url,repository) || allowedExternalLink(data.issue_url,REPO);
  if (issue) {
    const a=el('a','btn btn-small','Issue STATE: '+String(data.issue_status || 'UNKNOWN'));
    a.href=issue;a.target='_blank';a.rel='noopener noreferrer';
    body.appendChild(a);
  }
  for (const p of (Array.isArray(data.prs)?data.prs:[])) {
    if (p.comparison !== 'CONTRADICTION') continue;
    const url=allowedExternalLink(p.url,repository);
    if (!url) continue;
    const a=el('a','btn btn-small','PR: '+String(p.pr_status || 'UNKNOWN'));
    a.href=url;a.target='_blank';a.rel='noopener noreferrer';
    body.appendChild(a);
  }
  card.appendChild(body);target.appendChild(card);
}

async function renderProject(app, projectName) {
  if (!projectName) { navigate('#home'); return; }
  // Even a tampered published registry must not turn a hash into a data path.
  const safeProject = /^[A-Za-z0-9][A-Za-z0-9._-]*$/.test(projectName);
  const proj = safeProject ? state.projects.find(p => p.project === projectName) : null;
  if (!proj) {
    app.replaceChildren(el('div', 'empty-state', `Project "${projectName}" not found.`));
    return;
  }

  const detail = await loadProjectDetail(projectName);
  const frag = cloneTemplate('tpl-project');
  app.innerHTML = '';
  app.appendChild(frag);

  $('back-to-home').addEventListener('click', () => navigate('#home'));
  $('project-title').textContent = projectName;
  const l4Links = el('nav','l4-project-links');
  l4Links.setAttribute('aria-label','Project history views');
  for (const [view,label] of [
    ['understanding','Understanding'],['people','People'],
    ['engineering-history','History'],['sources','Original sources'],
    ['improvements','Improvements'],['changeover','Changeover']
  ]) {
    const link = el('a','btn btn-small',label);
    link.href = '#' + view + '/' + encodeURIComponent(projectName);
    l4Links.appendChild(link);
  }
  $('project-title').parentNode.appendChild(l4Links);
  renderG8Disagreement($('g8-disagreement'),
    proj.status_merge_disagreement || detail?.status_merge_disagreement,
    proj.repository);

  const ctrl = proj.control || detail?.registry?.control || {};
  wp13ReadOnly($('wp13-project-moves'), proj.next_move || detail?.next_move);
  wp14Controls($('wp14-project-controls'), proj);
  wp12HoldBanner($('wp12-project-hold'),proj.hold_report || detail?.hold_report);
  wp12ReportingTree($('wp12-reporting-tree'),proj.reporting_tree || detail?.reporting_tree);
  wp12ChildProgress($('wp12-child-progress'),proj.child_progress || detail?.child_progress,
                    proj.repository);
  wp12HeadStatus($('wp12-head-status'),proj.evidence_head_status ||
                 detail?.evidence_head_status, proj.repository);
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

  renderAutoResponseTable($('auto-response-project'), [proj]);
  const external = $('external-project-links');
  if (proj.repository !== REPO) {
    external.appendChild(el('h2', '', 'Owning repository links (read-only)'));
    if (/^[A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+$/.test(proj.repository)) {
      const owning = el('a', 'btn btn-small external-project-repo',
        'Repository: ' + proj.repository + ' (read-only) →');
      owning.href = 'https://github.com/' + proj.repository;
      owning.target = '_blank'; owning.rel = 'noopener noreferrer';
      external.appendChild(owning);
    }
    const links = Array.isArray(proj.external_links) ? proj.external_links : [];
    if (!links.length) external.appendChild(el('p','note','No verified owning issue or PR links.'));
    for (const item of links) {
      const url = allowedExternalLink(item.url, proj.repository);
      if (!url) continue;
      const link = el('a','btn btn-small external-project-link',
                      String(item.kind) + ' · View on GitHub (read-only) →');
      link.href = url; link.target = '_blank'; link.rel = 'noopener noreferrer';
      external.appendChild(link);
    }
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
    const threadHref = allowedExternalLink(a.evidence_thread_url, proj.repository);
    const threadLink = threadHref
      ? `<a class="agent-evidence-thread" href="${escapeHtml(threadHref)}" target="_blank" rel="noopener noreferrer">#${tnum}</a>`
      : (proj.repository === REPO && tnum
        ? `<a class="agent-evidence-thread" href="https://github.com/${REPO}/issues/${tnum}" target="_blank" rel="noopener noreferrer">#${tnum}</a>`
        : '—');

    tr.innerHTML = `
      <td>
        <a href="#agent/${escapeHtml(encodeURIComponent(projectName))}/${escapeHtml(encodeURIComponent(a.chat_id8))}">
          ${escapeHtml(a.role)}${a.alias ? ` (${escapeHtml(a.alias)})` : ''}
        </a>
        <br><code style="font-size:0.78rem;color:var(--text-3)">${escapeHtml(a.chat_id8)}</code>
        ${retiredNote}
      </td>
      <td>${genBadge}</td>
      <td class="agent-state"></td>
      <td>${threadLink}</td>
      <td><code style="font-size:0.75rem;word-break:break-all">${escapeHtml(a.branch || '—')}</code></td>
      <td><a href="#agent/${escapeHtml(encodeURIComponent(projectName))}/${escapeHtml(encodeURIComponent(a.chat_id8))}" class="btn btn-small">Evidence →</a></td>
    `;
    const stateCell = tr.querySelector(".agent-state");
    stateCell.appendChild(agentStateBadge(a.status));
    if (a.chat_end_risk || a.chat_end_seen ||
        (a.handover_meter != null && Number(a.handover_meter) >= 80)) {
      const risk = el('span','badge badge-red chat-end-risk','chat-end risk');
      risk.title = 'Handover needed: registry meter 80%+ or chat_end_seen.';
      stateCell.appendChild(risk);
    }
    const takeover = allowedExternalLink(a.handover, proj.repository) ||
      allowedExternalLink(a.handover, REPO);
    if (takeover) {
      const link = el('a','btn btn-small agent-takeover-link','Takeover handover →');
      link.href = takeover; link.target = '_blank'; link.rel = 'noopener noreferrer';
      tr.lastElementChild.appendChild(link);
    }
    tbody.appendChild(tr);
  });

  // Leases
  const leasesBody = $('leases-body');
  const leases = proj.leases || detail?.leases || [];
  const sod = detail?.registry?.standing_owner_decisions || [];
  const leaseEntries = leases.length
    ? leases
    : sod.filter(d => (typeof d === 'string' ? d : JSON.stringify(d)).toLowerCase().includes('lease'));

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
    const inputs = await loadOwnerInputs();
    for (const d of ood) {
      const card = el('div', 'decision-card');
      const visibleAsk = await displayedDecisionAsk(d);
      card.innerHTML = `
        <div class="decision-card-header">
          <span class="decision-card-id">${escapeHtml(d.id)}</span>
          <span class="decision-card-ask">${escapeHtml(visibleAsk)}</span>
          <span class="needs-plain">No answer recorded yet. Owner action needed.</span>
          <span class="decision-asked">${escapeHtml(decisionAskedText(d))}</span>
        </div>
        <div class="decision-card-body">
          ${d.link ? `<a href="${escapeHtml(d.link)}" target="_blank" rel="noopener" class="btn btn-small">Evidence →</a>` : ''}
          <a href="#decision/${escapeHtml(encodeURIComponent(projectName))}/${escapeHtml(encodeURIComponent(d.id))}" class="btn btn-small" style="margin-left:6px">Decision card →</a>
        </div>
      `;
      renderDecisionAnswers(card.querySelector('.decision-card-body'),
        projectName, d, visibleAsk, inputs);
      odSection.appendChild(card);
    }
  }

  // Standing Owner decisions (read-only record; superseded entries labelled as such)
  const sodSection = $('standing-decisions-section');
  const sodEntries = detail?.registry?.standing_owner_decisions || [];
  if (sodEntries.length) {
    const h2 = el('h2', '', 'Standing Owner decisions');
    h2.style.cssText = 'font-size:1rem;margin:0 0 8px';
    sodSection.appendChild(h2);
    const note = el('p', 'note', 'Read-only record of Owner words still in effect, including superseded entries (labelled). Agent claims are not included here.');
    note.style.marginBottom = '8px';
    sodSection.appendChild(note);
    sodEntries.forEach(entry => {
      const d = el('div');
      d.style.cssText = 'padding:6px 10px;border-left:3px solid var(--border);margin-bottom:6px;font-size:0.85rem;word-break:break-word';
      const text = typeof entry === 'string' ? entry : JSON.stringify(entry);
      // Highlight superseded entries
      d.appendChild(el('span', 'badge badge-grey decision-provenance',
                       decisionProvenance(entry)));
      if (text.toLowerCase().includes('supersedes')) {
        d.style.borderColor = 'var(--warn)';
        d.appendChild(el('span', 'badge badge-yellow', 'superseded'));
        d.appendChild(document.createTextNode(text));
      } else {
        d.appendChild(document.createTextNode(text));
      }
      sodSection.appendChild(d);
    });
  }

  // Post to team button
  const postBtn = $('post-btn');
  if (state.benchmarkMode || (proj.repository !== REPO && !proj.is_benchmark && !proj.benchmark_snapshot)) {
    postBtn.style.display = 'none'; // external projects are read-only
  } else {
    postBtn.href = postToTeamURL(projectName, 'INFO');
  }
}

// ── Agent view ─────────────────────────────────────────────
