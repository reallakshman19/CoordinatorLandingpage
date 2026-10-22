const {el, ppList, ppRich, ppLink, ppFmtTime, ppOpenActions, ppActionCard, ppAllCard, ppPlainList} = await import('./helpers.mjs' + new URL(import.meta.url).search);
function ppDrawActions(root, page, topicKey, P) {
  const ctx = { project: page.project, page: page.key, topic: topicKey, view: 'actions', mode: page.mode, replyTo: page.replyTo };
  const open = ppOpenActions(P);
  const done = ppList(P.actions).filter(a => a.status === 'done');
  const sec = el('div', 'pp-sec');
  sec.appendChild(el('h2', '', 'Do now'));
  if (!open.length) {
    sec.appendChild(el('div', 'pp-empty', 'Nothing waits on you in this topic. When an agent or OTM needs a decision, it appears here with the files involved and a reply to copy.'));
  } else {
    sec.appendChild(el('p', 'pp-intro', `${open.length} open. Each card says what to reply. Paste your reply in the chat with OTM, or use Send to OTM, and OTM records it and moves the work on.`));
    open.forEach(a => sec.appendChild(ppActionCard(a, ctx)));
    const all = ppAllCard(open, ctx);
    if (all) sec.appendChild(all);
  }
  root.appendChild(sec);

  const covered = {};
  open.forEach(a => (a.stages || []).forEach(s => { covered[s] = true; }));
  const coming = ppList(P.stages).filter(s => s.actor === 'YOU' && s.state !== 'VERIFIED' && !covered[s.id]);
  if (coming.length) {
    const cs = el('div', 'pp-sec');
    cs.appendChild(el('h2', '', 'Coming up for you'));
    cs.appendChild(ppPlainList(coming.map(s => () => {
      const li = el('li');
      const t = el('div', 'pp-pt');
      t.appendChild(el('span', 'pp-sid', s.id + ' '));
      t.appendChild(document.createTextNode(s.name || s.id));
      li.appendChild(t);
      if (s.sub) li.appendChild(ppRich(el('div', 'pp-ps'), s.sub));
      const det = s.detail || {};
      if (det.do) li.appendChild(ppRich(el('div', 'pp-ps'), 'Do: ' + det.do));
      if (det.waits) li.appendChild(ppRich(el('div', 'pp-ps'), 'Waits for: ' + det.waits));
      return li;
    })));
    root.appendChild(cs);
  }
  if (done.length) {
    const ds = el('div', 'pp-sec');
    ds.appendChild(el('h2', '', 'Answered'));
    ds.appendChild(ppPlainList(done.map(a => () => {
      const li = el('li');
      li.appendChild(el('div', 'pp-pt', a.title || a.id));
      const ans = a.answer || {};
      if (ans.text) li.appendChild(ppRich(el('div', 'pp-ps'), 'Your answer: ' + ans.text));
      const meta = el('div', 'pp-ps');
      if (ans.at) meta.appendChild(document.createTextNode('Recorded ' + ppFmtTime(ans.at) + '. '));
      if (ans.ref) meta.appendChild(ppLink(ans.ref, 'Record on GitHub'));
      if (meta.childNodes.length) li.appendChild(meta);
      return li;
    })));
    root.appendChild(ds);
  }
}

export {ppDrawActions};
