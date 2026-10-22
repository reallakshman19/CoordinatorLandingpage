const {el, ppOpenActions, ppAllCard, ppList, ppMilestones, PP_CLS, PP_SYM} = await import('./helpers.mjs' + new URL(import.meta.url).search);
function ppDrawOverview(root, page, B) {
  const topics = (B.index.topics || []).slice().sort((a, b) => (a.order || 0) - (b.order || 0));
  const open = [];
  topics.forEach(t => { const P = B.topics[t.key]; if (P) ppOpenActions(P).forEach(a => open.push({ t, a })); });

  const need = el('div', 'pp-sec');
  need.appendChild(el('h2', '', 'Needs you, across topics'));
  if (!open.length) {
    need.appendChild(el('div', 'pp-empty', 'Nothing waits on you in any topic.'));
  } else {
    const ul = el('ul', 'pp-plain');
    open.forEach(({ t, a }) => {
      const li = el('li');
      const head = el('div', 'pp-pt');
      head.appendChild(el('span', 'pp-topicchip', t.label));
      head.appendChild(document.createTextNode(' ' + (a.title || a.id)));
      li.appendChild(head);
      const go = el('a', 'btn btn-small', 'Open the card');
      go.href = `#progress-page/${page.key}/${t.key}/actions`;
      li.appendChild(go);
      ul.appendChild(li);
    });
    need.appendChild(ul);
    const all = ppAllCard(open.map(x => x.a), { project: page.project, page: page.key, topic: '', view: 'actions', mode: page.mode, replyTo: page.replyTo });
    if (all) need.appendChild(all);
  }
  root.appendChild(need);

  const sec = el('div', 'pp-sec');
  sec.appendChild(el('h2', '', 'Topics'));
  const ids = [];
  topics.forEach(t => { const P = B.topics[t.key]; if (P) ppMilestones(P).forEach(m => { if (!ids.includes(m.id)) ids.push(m.id); }); });
  ids.sort();
  const wrap = el('div', 'table-wrap pp-tw');
  const tb = el('table', 'pp-table pp-matrix');
  const hr = el('tr');
  ['Topic', ...ids, 'Verified', 'Blocked', 'Next on you'].forEach(c => hr.appendChild(el('th', '', c)));
  tb.appendChild(el('thead')).appendChild(hr);
  const body = el('tbody');
  topics.forEach(t => {
    const P = B.topics[t.key];
    const row = el('tr');
    const first = el('td');
    const a = el('a', 'pp-toplink', (P && P.topic && P.topic.title) || t.title || t.label);
    a.href = `#progress-page/${page.key}/${t.key}/progress`;
    first.appendChild(a);
    row.appendChild(first);
    if (!P) {
      const td = el('td', 'pp-planned', B.errors[t.key] ? 'Could not load: ' + B.errors[t.key] : t.planned ? 'Planned: no data yet' : 'Loading');
      td.colSpan = ids.length + 3;
      row.appendChild(td);
    } else {
      const ms = ppMilestones(P);
      ids.forEach(id => {
        const m = ms.find(x => x.id === id);
        const td = el('td', 'pp-mcell');
        if (m) {
          const c = el('span', 'pp-mini ' + PP_CLS[m.state], PP_SYM[m.state]);
          c.title = `${m.id} ${m.name}: ${m.state}, ${m.ok} of ${m.total} verified`;
          td.appendChild(c);
        } else td.textContent = '–';
        row.appendChild(td);
      });
      const stages = ppList(P.stages);
      row.appendChild(el('td', '', `${stages.filter(s => s.state === 'VERIFIED').length} of ${stages.length}`));
      row.appendChild(el('td', '', String(stages.filter(s => s.state === 'BLOCKED').length)));
      const o = ppOpenActions(P)[0];
      row.appendChild(el('td', '', o ? o.title : '–'));
    }
    body.appendChild(row);
  });
  tb.appendChild(body);
  wrap.appendChild(tb);
  sec.appendChild(wrap);
  sec.appendChild(el('p', 'note', 'Each topic is a child of the pilot and has its own My actions, Progress and Grounding fixtures. Shared tooling holds what every topic depends on. A new topic, for example Motion in 1D, appears here as soon as OTM creates it.'));
  root.appendChild(sec);
}

export {ppDrawOverview};
