'use strict';

function wp13MoveTitle(m) {
  return String(m.id || 'unknown') + ' · ' + String(m.kind || 'unknown') +
    ' · ' + String(m.state || 'unknown');
}
function wp13MoveItem(m) {
  const li = el('li', 'wp13-move-row');
  li.appendChild(el('span', '', wp13MoveTitle(m)));
  if (m.self_approved) li.appendChild(el('span','badge badge-grey','self-approved'));
  for (const flag of m.flags || []) {
    if (flag === 'self-approved' && m.self_approved) continue;
    li.appendChild(el('span','badge badge-grey',String(flag)));
  }
  return li;
}
function wp13ReadOnly(container, view, agentId = null) {
  if (!container) return;
  container.replaceChildren();
  container.appendChild(el('h2', '', agentId ?
    'Next Move for agent (read-only)' : 'Next Move (read-only)'));
  if (!view) {
    container.appendChild(el('p','note','No Next Move projection available.'));
    return;
  }
  const criticality = el('p', 'wp13-criticality');
  criticality.appendChild(el('span', 'badge badge-grey wp13-criticality-badge',
    'Criticality: ' + String(view.criticality || 'critical')));
  criticality.appendChild(el('span', '',
    ' · Approver: ' + String(view.approver_tier || 'Owner only')));
  container.appendChild(criticality);
  if (!view.pilot) {
    container.appendChild(el('p','note','Next Move pilot not enabled for this project.'));
    return;
  }
  const own = agentId ? view.agents?.[agentId] : view;
  const counter = own?.task_cycle || view.task_cycle;
  container.appendChild(el('p','wp13-task-cycle',
    counter?.label || 'task cycle unknown — no GO recorded'));
  // UEM: show agent-declared plans and source-linked Next Move states only.
  const uem = view.ultra_economy;
  if (uem?.enabled) {
    const pane = el('div','wp13-uem');
    pane.appendChild(el('h3','','UltraEconomyMode · read-only'));
    pane.appendChild(el('p','note','Cycle limit: '+String(uem.max_cycles)+' · no chat/timer dispatch by this page'));
    const rows = Object.entries(uem.agents || {}).filter(([id])=>!agentId || id===agentId);
    for (const [id,task] of rows) {
      const item = el('div','wp13-uem-task');
      item.appendChild(el('strong','',id+' · '+String(task.task || 'no start')+' · '+String(task.state)));
      if (task.planned_outcome) item.appendChild(el('p','','Planned: '+task.planned_outcome));
      if (task.expected_next) item.appendChild(el('p','','Expected next: '+task.expected_next));
      if (task.known_blocker) item.appendChild(el('p','','Known blocker: '+task.known_blocker));
      if (task.move_id) item.appendChild(el('p','','Matched Next Move: '+task.move_id+' ('+task.move_state+')'));
      if (task.followup?.next_due_at) item.appendChild(el('p','','Follow-up due: '+task.followup.next_due_at));
      item.appendChild(el('p','note',task.may_proceed ? 'Delivered move recorded; agent must recheck authority before action.' : 'No autonomous action authorized.'));
      pane.appendChild(item);
    }
    if (!rows.length) pane.appendChild(el('p','note','No registered agent evidence yet.'));
    container.appendChild(pane);
  }
  const names = ['active','queue'];
  for (const name of names) {
    const section = el('div','wp13-move-group');
    section.appendChild(el('h3','',name === 'active' ? 'Active dispatch' : 'Queue'));
    const list = el('ul');
    const items = Array.isArray(own?.[name]) ? own[name] : [];
    for (const item of items) list.appendChild(wp13MoveItem(item));
    if (!items.length) list.appendChild(el('li','note','None recorded'));
    section.appendChild(list);
    container.appendChild(section);
  }
  const flags = Array.isArray(view.flags) ? view.flags : [];
  const flagBox = el('div','wp13-flags');
  flagBox.appendChild(el('strong','','Flags: '));
  flagBox.appendChild(el('span','',flags.length ? flags.join(' · ') : 'none'));
  container.appendChild(flagBox);
  // EVALUATED is actual only when present in moves.jsonl, never a proposed row.
  const evalPanel = el('div','wp15-evaluator-panel');
  evalPanel.appendChild(el('h3','', 'Evaluator cross-check · read-only'));
  evalPanel.appendChild(el('p','wp15-last-evaluated',
    'Last recorded EVALUATED: ' + String(view.evaluator_at || 'none recorded')));
  evalPanel.appendChild(el('p','wp15-evaluator-stale',
    'Evaluator stale: ' + ((view.flags || []).includes('evaluator stale') ? 'yes' : 'no')));
  evalPanel.appendChild(el('p','wp15-not-acted',
    'Detected, not acted on: ' + ((view.flags || []).includes('detected, not acted on') ? 'yes' : 'no')));
  const cross = view.evaluator_cross_check || {status:'not_recorded',mismatches:[]};
  evalPanel.appendChild(el('p','wp15-cross-check',
    'Evaluator output: ' + String(cross.status || 'not_recorded') +
    ' · observed: ' + String(cross.observed_at || 'none') +
    ' · mismatches: ' + (Array.isArray(cross.mismatches) && cross.mismatches.length ?
      cross.mismatches.join(', ') : 'none or unavailable')));
  evalPanel.appendChild(el('p','note',
    'EVALUATED proposal is not a recorded heartbeat; only a committed moves.jsonl row counts.'));
  container.appendChild(evalPanel);
  if (!agentId) {
    const bad = Array.isArray(view.rejected) ? view.rejected : [];
    const rejected = el('div','wp13-rejected');
    rejected.appendChild(el('strong','','Rejected records: ' + bad.length));
    for (const item of bad) rejected.appendChild(el('p','note',
      String(item.id) + ' — ' + (item.reasons || []).join(', ')));
    container.appendChild(rejected);
  }
}
async function renderNextMoves(app) {
  const frag = cloneTemplate('tpl-next-moves');
  app.replaceChildren(frag);
  const board = $('wp13-board');
  for (const p of state.projects) {
    const v = p.next_move;
    const section = el('section','card wp13-board-project');
    section.appendChild(el('h2','',String(p.project)));
    const body = el('div','card-body');
    wp13ReadOnly(body,v);
    section.appendChild(body);
    if (v?.pilot) {
      const phases = el('div','wp13-board-phases');
      for (const [phase, ids] of Object.entries(v.board || {})) {
        const part = el('p','wp13-board-phase');
        part.appendChild(el('strong','',phase + ': '));
        part.appendChild(el('span','',Array.isArray(ids) && ids.length ?
          ids.join(', ') : '—'));
        phases.appendChild(part);
      }
      section.appendChild(phases);
      const actions=el('div','wp14-board-controls');
      wp14Controls(actions,p);
      section.appendChild(actions);
    }
    board.appendChild(section);
  }
}


// WP14 pilot-only GitHub Contents new-file prefill. A click opens a *draft*
// Owner-input file; neither a committed OI nor a typed role is an APPROVED
// transition. The authenticated author still commits; the coordinator must
// validate and record the resulting transition separately.
const WP14_DISPATCH_KINDS = ['next_step','course_correction','new_requirement',
  'ground','reconcile','handover_trigger','buddy_1a','buddy_1b','buddy_2',
  'label_request','skill_alignment','status_check'];
function wp14RequestURL(project, type, payload, date = new Date(), bytes = null) {
  const p = state.projects.find(x => x.project === project);
  if (!p || project !== 'landing-live' || p.repository !== REPO ||
      !p.next_move?.pilot || state.benchmarkMode) {
    throw new Error('Next Move compose/approve is restricted to the landing-live pilot.');
  }
  if (!['NEXT_MOVE_COMPOSE','NEXT_MOVE_APPROVAL'].includes(type))
    throw new Error('Unsupported Next Move request.');
  return ownerJSONCommitURL({
    project, target:'TeamCoordinator', type, text:JSON.stringify(payload),
    replaces:''
  },date,bytes);
}
function wp14MoveDraft(project, values, date = new Date(), bytes = null) {
  const p=state.projects.find(x => x.project===project);
  if (!p || project!=='landing-live' || p.repository!==REPO || !p.next_move?.pilot)
    throw new Error('Not a registered Next Move pilot.');
  const kind=String(values.kind || '');
  if (!WP14_DISPATCH_KINDS.includes(kind)) throw new Error('Invalid dispatch kind.');
  const from=String(values.from || '').trim(),to=String(values.to || '').trim();
  const text=String(values.text || '').trim(),triggerInput=String(values.trigger || '').trim();
  let trigger=triggerInput;
  if (triggerInput.startsWith('{')) {
    try {
      const parsed=JSON.parse(triggerInput);
      if (parsed?.type!=='uem_end' || !/^[A-Za-z0-9_.-]{1,80}$/.test(parsed.task) ||
          !Number.isInteger(parsed.cycle) || parsed.cycle<1 || parsed.cycle>5 ||
          !Number.isInteger(parsed.end_comment_id) || parsed.end_comment_id<1 ||
          Object.keys(parsed).sort().join(',')!=='cycle,end_comment_id,task,type')
        throw new Error('Invalid UEM trigger object');
      trigger=parsed;
    } catch { throw new Error('Invalid UEM JSON trigger. Select current evidence again.'); }
  }
  const head=String(values.head || '').trim(),source=String(values.evidence || '').trim();
  const supersedes=String(values.supersedes || '').trim();
  if (!/^[0-9a-f]{8}$/.test(from) || !/^[0-9a-f]{8}$/.test(to) ||
      !/^[0-9a-f]{40}$/i.test(head) || !/^https:\/\/github\.com\/reallakshman19\/CoordinatorLandingpage\/issues\/\d+$/.test(source) ||
      !text || text.length>600 || !triggerInput || triggerInput.length>240 ||
      (typeof trigger==='string' && trigger.length>100) ||
      supersedes && !/^NM-\d{8}-\d{6}-[0-9a-f]{4}$/.test(supersedes)) {
    throw new Error('Supply valid id8s, source issue, assessed 40-hex head, trigger and task.');
  }
  if (!/^[0-9a-f]{40}$/i.test(String(p.registry_blob_sha || '')))
    throw new Error('Registry source SHA missing; cannot compose a basis.');
  const stamp=date.toISOString().replace(/[-:]/g,'').replace('T','-').slice(0,15);
  const rnd=Array.from(bytes || crypto.getRandomValues(new Uint8Array(2)))
    .map(n=>n.toString(16).padStart(2,'0')).join('');
  const record={id:'NM-'+stamp+'-'+rnd,project,class:'Dispatch',kind,
    from:{role:'TeamCoordinator',id8:from},to:{role:'implementer',id8:to},
    text,basis:{evidence:source,head,registry_sha:p.registry_blob_sha},
    trigger,supersedes:supersedes || null,evidence_format:'TASK EVIDENCE v2',
    created_at:date.toISOString()};
  return wp14RequestURL(project,'NEXT_MOVE_COMPOSE',{move:record},date,bytes);
}
function wp14ApprovalDraft(project, move, role, id8, date=new Date(),bytes=null) {
  const p=state.projects.find(x=>x.project===project);
  if (!p || project!=='landing-live' || !p.next_move?.pilot || p.repository!==REPO ||
      !p.next_move.moves?.some(m=>m.id===move.id && m.state==='PUBLISHED'))
    throw new Error('Only published moves in the landing-live pilot can request approval.');
  if (!['Owner','OwnerTeammember'].includes(role) ||
      (p.next_move.criticality!=='normal' && role!=='Owner'))
    throw new Error('Approver tier forbids the requested role.');
  if (!/^[0-9a-f]{8}$/.test(String(id8)))
    throw new Error('Approver chat id8 is required.');
  const payload={move:move.id,by:{role,id8},at:date.toISOString(),
    request_only:true};
  return wp14RequestURL(project,'NEXT_MOVE_APPROVAL',payload,date,bytes);
}
