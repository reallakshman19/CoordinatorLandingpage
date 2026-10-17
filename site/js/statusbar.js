'use strict';

function wp16Light(value) {
  const name=['green','yellow','red','grey'].includes(value)?value:'yellow';
  return el('span','wp16-light wp16-'+name,name.toUpperCase());
}
function wp16Row(body,cells,key) {
  const tr=el('tr','wp16-row');
  if(key)tr.dataset.instanceKey=key;
  for(const value of cells){
    const td=el('td','');
    if(value && typeof value==='object' && value.nodeType)td.appendChild(value);
    else td.textContent=String(value??'');
    tr.appendChild(td);
  }
  body.appendChild(tr);
}
function wp16CoordinatorCell(record){
  const info=record && typeof record==='object'?record:{};
  const valid=['NORMAL','ACTING'].includes(info.mode) &&
              typeof info.holder==='string' && info.holder.trim();
  const cell=el('span','wp16-coordinator',
    valid?info.holder+' · '+info.mode:'UNKNOWN');
  const ref=String(info.control_ref||'');
  if(valid && /^https:\/\/github\.com\/[A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+\/(?:issues|pull)\/[1-9][0-9]*#issuecomment-[1-9][0-9]*$/.test(ref)){
    const a=el('a','wp16-control-ref','CONTROL');
    a.href=ref;a.target='_blank';a.rel='noopener noreferrer';
    cell.append(el('span','note',' · '),a);
  }
  return cell;
}
function wp16Observation(record,kind){
  const info=record && typeof record==='object'?record:{};
  const state=kind==='timer'
    ?(['ACTIVE','PAUSED'].includes(info.state)?info.state:'UNKNOWN')
    :(['UP','DOWN'].includes(info.result)?info.result:'UNKNOWN');
  return state;
}
async function renderStatusBar(app){
  app.replaceChildren(cloneTemplate('tpl-status-bar'));
  const source=await fetchJSON(
    (state.benchmarkMode?BM_DATA_BASE:DATA_BASE)+'status-bar.json',{cache:'no-store'});
  state.statusBar=source;
  const cover=$('wp16-coverage');
  if(!source || source.schema!=='status_bar.v1' ||
     !Array.isArray(source.projects) || !Array.isArray(source.instances)){
    cover.textContent='UNKNOWN · status-bar projection unavailable; no green status.';
    return;
  }
  const c=source.coverage||{};
  const full=c.complete===true && c.expected===source.instances.length &&
             c.projected===source.instances.length;
  cover.textContent='Selected-roster coverage: '+String(c.projected??'?')+
    '/'+String(c.expected??'?')+' · '+String(c.percent??'?')+'% · '+
    (full?'FULL':'INCOMPLETE / UNKNOWN');
  if(!full)cover.classList.add('wp16-coverage-incomplete');
  for(const p of source.projects){
    const cv=p.selected_roster_coverage||{};
    wp16Row($('wp16-ot-rows'),[
      p.project,wp16Light(full?p.light:'yellow'),
      p.complete?'COMPLETE (separate)':'—',
      String(cv.projected??0)+'/'+String(cv.expected??'?'),
      p.active_count??0,
      (p.dependencies?.blocked||[]).concat(p.dependencies?.unknown||[]).join(', ')||'none verified',
      p.reason||'unknown',wp16CoordinatorCell(p.coordinator)]);
  }
  for(const r of source.instances){
    let link=el('span','note','no registered id8');
    if(/^[0-9a-f]{8}$/.test(String(r.instance_id8||'')) &&
       r.chat_link==='https://chatgpt.com/c/'+r.instance_id8){
      link=el('a','wp16-chat-id8',r.instance_id8);
      link.href=r.chat_link;link.target='_blank';link.rel='noopener noreferrer';
      link.title='id8-only chat reference; full private chat ID is not stored';
    }
    const mon=r.dimensions?.monitoring||{},auth=r.dimensions?.execution_authority||{};
    const timer=r.timer||{},browser=r.browser||{};
    const timerState=wp16Observation(timer,'timer');
    const browserState=wp16Observation(browser,'browser');
    const timerTimes='last tick '+String(timerState==='UNKNOWN'?'UNKNOWN':timer.last_tick||'UNKNOWN')+
      ' · next due '+String(timerState==='UNKNOWN'?'UNKNOWN':timer.next_due||'UNKNOWN');
    const browserCheck=browserState+' · checked '+
      String(browserState==='UNKNOWN'?'UNKNOWN':browser.checked_at||'UNKNOWN');
    wp16Row($('wp16-tc-rows'),[
      r.project,r.workstream,String(r.kind)+' · '+String(r.alias||r.role),
      link,r.generation==null?'unknown':'g'+r.generation,
      wp16Light(full?r.light:'yellow'),r.complete?'COMPLETE':'—',
      (r.retired?'RETIRED · ':'')+String(r.dimensions?.work?.state||'unknown'),
      String(mon.state||'unknown')+' · last '+String(mon.last_evaluation||'not recorded')+
        ' · next '+String(mon.next_due||'unknown'),
      String(auth.state||'unknown')+' · '+String(auth.reason||'unknown'),
      el('span','wp16-observation',timerState),
      timerTimes,el('span','wp16-observation',browserCheck),
      (r.conflicts||[]).join('; ')||'none'
    ],r.key);
  }
  const selector=$('wp16-mode'),ot=$('wp16-ot'),tc=$('wp16-tc');
  const toggle=()=>{ot.hidden=selector.value!=='ot';tc.hidden=selector.value!=='tc';};
  selector.addEventListener('change',toggle);toggle();
}

// ── URL helpers ────────────────────────────────────────────
