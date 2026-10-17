'use strict';

function wp14Controls(container, project) {
  if (!container) return;
  container.replaceChildren();
  if (project.project !== 'landing-live' || project.repository !== REPO ||
      !project.next_move?.pilot || state.benchmarkMode) return;
  container.appendChild(el('h3','','Next Move · compose a request'));
  container.appendChild(el('p','note',
    'GitHub opens a prefilled Owner-input JSON file. Review and commit there. This is not a published move or approval, and nothing is sent to an agent.'));
  const form=el('form','wp14-compose-form');
  const fields=[
    ['kind','Kind','select',WP14_DISPATCH_KINDS],
    ['from','Coordinator chat id8','input'],
    ['to','Recipient chat id8','input'],
    ['head','Assessed commit SHA (40 hex)','input'],
    ['evidence','Evidence issue URL','input'],
    ['trigger','GO or trigger','input'],
    ['text','Task instruction','textarea'],
    ['supersedes','Supersedes NM id (optional)','input'],
  ];
  const values={};
  for (const [name,label,tag,choices] of fields) {
    const wrapper=el('label','wp14-field',label);
    const field=el(tag,'wp14-'+name);
    field.name=name;field.setAttribute('aria-label',label);
    if (choices) for (const choice of choices) {
      const opt=el('option','',choice);opt.value=choice;field.appendChild(opt);
    }
    if (name==='evidence')field.value='https://github.com/'+REPO+'/issues/22';
    if (name==='to' && project.agents?.length)field.value=project.agents.find(a=>a.status==='active')?.chat_id8||'';
    if (name==='text')field.maxLength=600;
    wrapper.appendChild(field);form.appendChild(wrapper);values[name]=field;
  }
  // The agent already supplied context at TASK START and END. Populate only a
  // reviewable draft; no approval, GitHub write, or chat dispatch occurs here.
  const uemRows=Object.entries(project.next_move.ultra_economy?.agents || {})
    .filter(([id,task])=>Number.isInteger(task?.end_comment_id) &&
      task?.task && Number.isInteger(task?.cycle) && task?.state!=='NOT_ACTIVE');
  if (project.next_move.ultra_economy?.enabled && uemRows.length) {
    const apply=el('button','btn btn-small wp14-uem-prefill','Use latest UEM task evidence');
    apply.type='button';
    apply.addEventListener('click',()=>{
      const [id,task]=uemRows.slice().sort((a,b)=>
        String(b[1].ended_at || '').localeCompare(String(a[1].ended_at || '')))[0];
      const agent=(project.agents||[]).find(a=>a.chat_id8===id);
      if (!agent || !/^https:\/\/github\.com\/reallakshman19\/CoordinatorLandingpage\/issues\/\d+$/.test(agent.evidence_thread_url || '')) {
        result.textContent='Current registered evidence issue not available; cannot prefill.';
        return;
      }
      values.to.value=id;
      values.evidence.value=agent.evidence_thread_url;
      const assessed=agent.evidence_head_status?.current_head || '';
      values.head.value=/^[0-9a-f]{40}$/i.test(assessed) ? assessed : '';
      const trigger={type:'uem_end',task:task.task,cycle:task.cycle,
        end_comment_id:task.end_comment_id};
      values.trigger.value=JSON.stringify(trigger);
      const blocked=/BLOCKED|FAILED/i.test(task.claim_status || '') ||
        /\bHOLD\b/i.test(task.not_done || '');
      values.kind.value=blocked?'status_check':'next_step';
      values.text.value=(
        'Task '+task.task+' ('+String(task.claim_status || 'UNKNOWN')+
        '). Expected: '+String(task.expected_next || 'UNKNOWN')+
        '. Agent next: '+String(task.next_claim || 'UNKNOWN')+
        '. Blocker: '+String(task.known_blocker || 'UNKNOWN')+
        '. Remaining: '+String(task.not_done || 'UNKNOWN')
      ).slice(0,600);
      result.textContent=values.head.value
        ? 'Review every prefilled claim, blocker, head and authority before opening a draft.'
        : 'Current PR HEAD unavailable: verify and enter it before composing.';
    });
    form.appendChild(apply);
  }
  const submit=el('button','btn btn-small wp14-compose-submit','Open proposed move on GitHub');
  submit.type='submit';form.appendChild(submit);
  const result=el('p','note wp14-compose-result');result.setAttribute('role','status');
  form.appendChild(result);
  form.addEventListener('submit',e=>{
    e.preventDefault();
    try {
      const data={};
      for (const [name,field] of Object.entries(values))data[name]=field.value;
      const request=wp14MoveDraft(project.project,data);
      window.open(request.url,'_blank','noopener,noreferrer');
      result.textContent='Draft '+request.record.id+' opened; no move was created.';
    } catch(error) { result.textContent=String(error.message); }
  });
  container.appendChild(form);
  container.appendChild(el('h3','','Request approval for a published dispatch'));
  const published=(project.next_move.moves||[]).filter(m=>m.class==='Dispatch'&&m.state==='PUBLISHED');
  if (!published.length)container.appendChild(el('p','note','No published dispatch requires approval.'));
  for (const move of published) {
    const row=el('div','wp14-approval-row');
    row.appendChild(el('span','',move.id+' · '+move.kind));
    const roles=el('select','wp14-approver-role');
    for (const role of project.next_move.criticality==='normal'
         ? ['Owner','OwnerTeammember']:['Owner']) {
      const opt=el('option','',role);opt.value=role;roles.appendChild(opt);
    }
    const id=el('input','wp14-approver-id8');id.placeholder='Approver chat id8';
    id.setAttribute('aria-label','Approver chat id8');
    const button=el('button','btn btn-small wp14-approval-submit','Request approval on GitHub');
    button.type='button';
    const status=el('span','note wp14-approval-result');
    button.addEventListener('click',()=>{
      try {
        const req=wp14ApprovalDraft(project.project,move,roles.value,id.value);
        window.open(req.url,'_blank','noopener,noreferrer');
        status.textContent=(id.value===move.from.id8?'self-approval requested · ':'')+
          'Not approved until an authorized transition is verified.';
      } catch(error) {status.textContent=String(error.message);}
    });
    row.append(roles,id,button,status);container.appendChild(row);
  }
  container.appendChild(el('p','note',
    'Role labels are requests, not identity proof. Critical projects are outside this pilot. The validator checks Owner/OTM tier and refuses unverified approvals.'));
}



function ownerJSONCommitURL(values, date = new Date(), randomBytes = null) {
  const project = String(values.project || '');
  if (!state.projects.some(p => p.project === project && (p.repository === REPO || p.is_benchmark === true || !!p.benchmark_snapshot)) ||
      !/^[A-Za-z0-9][A-Za-z0-9._-]*$/.test(project))
    throw new Error('Choose a listed project (hub only; external projects are read-only).');
  const target = String(values.target || '').trim();
  const type = String(values.type || '').trim();
  const message = String(values.text || '').trim();
  const replaces = String(values.replaces || '').trim();
  if (!target || target.length > 160 || !type || type.length > 64 ||
      !message || message.length > 1500) throw new Error('Enter a target, type and message.');
  if (replaces && !/^OI-\d{8}-\d{6}-[0-9a-f]{4}$/.test(replaces))
    throw new Error('The replacement ID is invalid.');
  const stamp = date.toISOString().replace(/[-:]/g, '').replace('T', '-').slice(0, 15);
  const bytes = randomBytes || crypto.getRandomValues(new Uint8Array(2));
  const rnd = Array.from(bytes).map(n => n.toString(16).padStart(2, '0')).join('');
  const id = 'OI-' + stamp + '-' + rnd;
  const record = {id, project, target, type, text: message,
                  replaces: replaces || null, created_at: date.toISOString()};
  const path = 'logs/' + project + '/inputs/' + id + '.json';
  const commitMessage = 'Owner input ' + id + ' via landing page';
  const url = 'https://github.com/' + REPO + '/new/main?filename=' +
    encodeURIComponent(path) + '&value=' + encodeURIComponent(JSON.stringify(record, null, 2)) +
    '&message=' + encodeURIComponent(commitMessage);
  if (url.length >= 7000) throw new Error('Request too long. Shorten the message.');
  return {url, record, path};
}

// WP9: decision answers remain unverified until a real associated JSON file
// has been committed and read back. A draft, popup and git link are NOT receipts.

function setupJSONInputForm() {
  const form = $('oi-json-form'), projects = $('oi-json-project');
  if (!form || !projects) return;
  for (const p of state.projects.filter(p => p.repository === REPO || p.is_benchmark === true || !!p.benchmark_snapshot)) {
    const opt = el('option', '', p.project);
    opt.value = p.project;
    projects.appendChild(opt);
  }
  if (state.benchmarkMode) { form.style.display = 'none'; return; }
  if (state.decisionDraft) {
    const draft = state.decisionDraft;
    projects.value = draft.project;
    $('oi-json-target').value = draft.target;
    $('oi-json-type').value = draft.type;
    $('oi-json-text').value = draft.text;
    $('oi-json-replaces').value = draft.replaces || '';
    $('oi-json-result').textContent =
      'Decision prepared · GitHub opens — click Commit changes twice. ' +
      'Only a committed file can appear as answered, waiting for receipt.';
  }
  form.addEventListener('submit', event => {
    event.preventDefault();
    try {
      const result = ownerJSONCommitURL({
        project: projects.value, target: $('oi-json-target').value,
        type: $('oi-json-type').value, text: $('oi-json-text').value,
        replaces: $('oi-json-replaces').value,
      });
      window.open(result.url, '_blank', 'noopener,noreferrer');
      $('oi-json-result').textContent = 'GitHub opened with ' + result.record.id +
        '. Review the JSON and click Commit changes. Nothing is posted until then.';
    } catch (error) {
      $('oi-json-result').textContent = error.message;
    }
  });
}

// ── Router ─────────────────────────────────────────────────

async function renderOwnerInputs(app) {
  const frag = cloneTemplate('tpl-owner-inputs');
  app.innerHTML = '';
  app.appendChild(frag);

  $('new-input-btn').href = ownerInputURL();
  setupJSONInputForm();
  if (state.benchmarkMode) {
    $('new-input-btn').style.display = 'none';
  }

  const list = $('oi-list');
  const count = $('oi-count');

  if (state.benchmarkMode) {
    count.textContent = 'frozen snapshot';
    list.appendChild(el('div', 'oi-row',
      'Owner input receipts are not part of this frozen benchmark. No handled state inferred.'));
    return;
  }

  const inputs = await loadOwnerInputs();
  if (inputs === null) {
    count.textContent = 'UNKNOWN';
    list.appendChild(el('div', 'oi-row',
      'Owner-inputs source unavailable · cannot confirm a receipt or action.'));
    return;
  }
  const trusted = inputs.filter(inp => inp.is_outsider !== true &&
    ['OWNER', 'MEMBER', 'COLLABORATOR'].includes(inp.author_association));
  const outsiders = inputs.filter(inp => !trusted.includes(inp));
  count.textContent = String(trusted.length);
  if (!inputs.length) {
    list.appendChild(el('div', 'oi-row',
      'No captured Owner inputs. Missing evidence is never considered handled.'));
    return;
  }

  if (!trusted.length) {
    list.appendChild(el('div', 'oi-row',
      'No captured Owner-associated inputs. Outside submissions are shown separately.'));
  }
  if (outsiders.length) {
    $('oi-outsider-panel').style.display = '';
    $('oi-outsider-count').textContent = String(outsiders.length);
  }
  for (const inp of inputs) {
    const outsider = !trusted.includes(inp);
    const status = ownerInputState(inp);
    const row = el('div', 'oi-row');
    row.dataset.issue = String(inp.id || inp.number || '');
    row.appendChild(el('span', 'oi-state')).appendChild(ownerStatusBadge(status));
    if (outsider) {
      row.appendChild(el('span', 'badge badge-grey', 'OUTSIDER'));
      row.appendChild(el('span', 'badge badge-grey', 'UNVERIFIED'));
    }
    row.appendChild(el('span', 'oi-type', String(inp.type || 'OWNER_INPUT')));
    const message = el('div', 'oi-text');
    message.appendChild(el('div', '', String(inp.text || '')));
    if (outsider) {
      message.appendChild(el('div', 'oi-pending',
        'GitHub author_association: ' + String(inp.author_association || 'MISSING') +
        ' · untrusted submission, not an Owner instruction'));
    }
    if (inp.protected_action) {
      message.appendChild(el('span', 'badge badge-grey',
        'UNVERIFIED · no action authorized'));
    }
    if (inp.review && inp.review.state) {
      message.appendChild(el('span', 'badge badge-grey',
        'Review metadata: ' + String(inp.review.state) + ' · not Owner approval'));
    }
    const receipt = !outsider && status === 'HANDLED' ? safeReceipt(inp) : null;
    if (receipt) {
      const a = el('a', 'oi-receipt', 'Linked handler receipt →');
      a.href = receipt;
      a.target = '_blank';
      a.rel = 'noopener noreferrer';
      message.appendChild(a);
    } else {
      message.appendChild(el('span', 'oi-pending',
        status === 'SUPERSEDED' ? 'Superseded · not effective' :
        'pending · no linked handler receipt'));
    }
    const trace = el('a', 'btn btn-small', 'Trace →');
    trace.href = '#trace/' + encodeURIComponent(String(inp.id || inp.number || ''));
    message.appendChild(trace);
    const issue = el('a', 'oi-issue-link', inp.source_kind === 'json_file'
      ? 'Committed JSON →' : 'Issue #' + String(inp.number || '—') + ' →');
    issue.href = inp.source_kind === 'json_file'
      ? (traceSafeGitHubURL(inp.issue_url) || '#owner-inputs')
      : 'https://github.com/' + REPO + '/issues/' + encodeURIComponent(String(inp.number || ''));
    issue.target = '_blank';
    issue.rel = 'noopener noreferrer';
    message.appendChild(issue);
    row.appendChild(message);
    const clocks = el('span', 'oi-ts owner-clock', ownerActivityText(inp));
    clocks.title = 'Posted: ' + (inp.ts && sourceTime(inp.ts) !== 'unknown'
      ? fmtDateTime(inp.ts) : 'unknown') + ' · Last update: ' +
      (inp.updated_at && sourceTime(inp.updated_at) !== 'unknown'
      ? fmtDateTime(inp.updated_at) : 'unknown');
    row.appendChild(clocks);
    (outsider ? $('oi-outsider-list') : list).appendChild(row);
  }
}


// ── Owner request trace (read-only, recorded links only) ─────
