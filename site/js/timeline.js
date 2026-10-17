'use strict';

function decisionAnswerText(decision, visibleAsk, answer) {
  const cleanId = String(decision.id || '');
  if (!/^[A-Za-z0-9][A-Za-z0-9_-]{0,95}$/.test(cleanId))
    throw new Error('Decision identifier cannot be safely submitted.');
  const cleanAnswer = String(answer || '').replace(/\s+/g, ' ').trim();
  // WP7's public projection currently shows the first 300 characters.
  // Keep the identifying quote in that projection even for an Other answer.
  if (!cleanAnswer || cleanAnswer.length > 140)
    throw new Error('Enter an answer of at most 140 characters.');
  const ask = String(visibleAsk || decision.ask || '').replace(/\s+/g, ' ').trim();
  // Bound the quote: even a long question must remain within the 1500-byte
  // form limit; the GitHub new-file URL has a separate 7000-char guard.
  return cleanId + ': ' + cleanAnswer + '\nQuestion: "' + ask.slice(0, 700) + '"';
}
function recordedDecisionAnswer(project, decision, inputs) {
  if (!Array.isArray(inputs)) return null;  // unavailable is UNKNOWN
  const id = String(decision.id || '');
  return inputs.filter(row =>
    row && row.source_kind === 'json_file' &&
    row.project === project &&
    row.type === 'DECISION' && row.target === 'TeamCoordinator' &&
    row.is_outsider === false &&
    ['OWNER', 'MEMBER', 'COLLABORATOR'].includes(row.author_association) &&
    Array.isArray(row.flags) && row.flags.length === 0 &&
    /^[0-9a-f]{40}$/.test(String(row.source_commit || '')) &&
    !!traceSafeGitHubURL(row.issue_url) &&
    typeof row.text === 'string' && row.text.startsWith(id + ': ') &&
    /\nQuestion: "/.test(row.text) &&
    ['OPEN','ACKNOWLEDGED','NEEDS_CLARIFICATION','HANDLED'].includes(ownerInputState(row))
  ).sort((a,b) => String(b.ts || '').localeCompare(String(a.ts || '')))[0] || null;
}
function decisionRecordedState(project, decision, inputs) {
  const row = recordedDecisionAnswer(project, decision, inputs);
  if (!row) return null;
  return ownerInputState(row) === 'HANDLED' && safeReceipt(row)
    ? 'linked handler receipt recorded · not Owner approval'
    : 'answered, waiting for receipt';
}
function renderDecisionAnswers(container, project, decision, visibleAsk, inputs) {
  const wrapper = el('div', 'decision-answers');
  if (state.benchmarkMode) return wrapper;
  const recorded = decisionRecordedState(project, decision, inputs);
  if (recorded) {
    wrapper.appendChild(el('div', 'decision-answer-state', recorded));
  }
  for (const choice of ['Accept', 'Hold', 'Other…']) {
    const wording = {Accept: 'Accept this decision', Hold: 'Put on hold',
                     'Other…': 'Write another answer…'};
    const button = el('button', 'btn btn-small decision-answer-btn', wording[choice]);
    button.type = 'button';
    button.dataset.choice = choice === 'Other…' ? 'Other' : choice;
    button.dataset.decisionId = String(decision.id);
    button.dataset.project = project;
    button.addEventListener('click', () => {
      try {
        let answer = choice;
        if (choice === 'Other…') {
          const typed = window.prompt('Your answer to ' + decision.id + ':', '');
          if (typed === null) return; // cancel is a NO-OP
          if (!typed.trim()) throw new Error('Enter an answer before continuing.');
          answer = 'Other: ' + typed.trim();
        }
        const data = {
          project, target: 'TeamCoordinator', type: 'DECISION',
          text: decisionAnswerText(decision, visibleAsk, answer), replaces: ''
        };
        const prepared = ownerJSONCommitURL(data);
        // Synchronous user gesture: keep the new tab eligible for popup.
        state.decisionDraft = data;
        window.open(prepared.url, '_blank', 'noopener,noreferrer');
        navigate('#owner-inputs');
        // We do not change decision status until a real committed source is
        // published and its author passes the pre-existing provenance gate.
      } catch (error) {
        const message = container.querySelector('.decision-answer-error')
          || el('span', 'decision-answer-error');
        message.textContent = String(error.message || 'Unable to prepare an answer.');
        wrapper.appendChild(message);
      }
    });
    wrapper.appendChild(button);
  }
  wrapper.appendChild(el('p', 'decision-commit-hint',
    'GitHub opens — click Commit changes twice. Your answer is not sent until you commit.'));
  container.appendChild(wrapper);
  return wrapper;
}


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
          summary = `Decision record: ${(ev.text || '').slice(0, 80)}`;
          break;
        case 'OUTSIDE_WRITE':
          summary = `⚠ Outside write: ${(ev.text || '').slice(0, 80)}`;
          break;
        default:
          summary = ev.type + (ev.text ? ': ' + String(ev.text).slice(0, 60) : '');
      }
      text.textContent = summary;
      if (ev.type === 'OWNER_DECISION') {
        const label = decisionProvenance(ev);
        row.appendChild(el('span','badge badge-grey decision-provenance',
          label === 'unverified' ? (ev.decision_label || 'unverified') : label));
      }

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
  $('dc-ask').textContent = await displayedDecisionAsk(d);
  $('dc-ask').appendChild(el('div', 'needs-plain',
    'No answer recorded yet. Owner action needed.'));
  $('dc-ask').appendChild(el('div', 'decision-asked', decisionAskedText(d)));

  if (d.link) {
    $('dc-links').innerHTML = `<a href="${escapeHtml(d.link)}" target="_blank" rel="noopener" class="btn btn-small">Evidence →</a>`;
  }

  // Native GitHub issue path remains as an explicit fallback, not the
  // main decision answer flow. It does not mark the card as answered.
  if (state.benchmarkMode) {
    $('dc-answer-btn').style.display = 'none';
  } else {
    $('dc-answer-btn').href = decisionURL(projectName, d.id);
    $('dc-answer-btn').textContent = 'GitHub issue (backup)';
  }
  renderDecisionAnswers($('dc-links').parentElement, projectName, d,
    await displayedDecisionAsk(d), await loadOwnerInputs());
}

// ── Owner inputs view ──────────────────────────────────────
