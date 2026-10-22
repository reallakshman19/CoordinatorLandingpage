// No SPA, OTM, or GitHub Actions dependency: fetch the supplied data directory.
const PP_DEFAULT_PAGES = [
  { key: 'g9v35', label: 'G9v3.5 Pilot Progress', project: 'g9v35', data: 'progress-data/g9v35' },
];
async function ppPages(projectsUrl, base) {
  try {
    const r = await fetch(projectsUrl, { cache: 'no-cache' });
    if (!r.ok) throw new Error(String(r.status));
    const j = await r.json();
    const list = (j.projects || [])
      .filter(p => p && /^[a-z0-9][a-z0-9-]*$/.test(p.key || '') && p.label)
      .sort((a, b) => (a.order || 0) - (b.order || 0))
      .map(p => ({ key: p.key, label: p.label, project: p.project || p.key,
        mode: p.mode === 'standalone-oracle' ? 'standalone-oracle' : 'coordinator',
        data: `progress-data/${p.key}`, fetchData: `${base}/${p.key}`, replyTo: p.replyTo || {kind: 'none'}, visibility: p.visibility || 'public' }));
    if (list.length) return list;
  } catch { /* use the fallback below */ }
  return PP_DEFAULT_PAGES.map(p => ({...p, fetchData: `${base}/${p.key}`, replyTo: {
    kind: 'github-issue', repo: 'reallakshman19/CoordinatorLandingpage', template: 'owner-reply.yml',
    target: 'OwnerTeammember', site: 'https://reallakshman19.github.io/CoordinatorLandingpage/'}}));
}
function ppHash(text) {
  let h = 5381;
  for (let i = 0; i < text.length; i++) h = ((h << 5) + h + text.charCodeAt(i)) | 0;
  return (h >>> 0).toString(36);
}
async function ppJson(path) {
  const r = await fetch(path, { cache: 'no-cache' });
  if (!r.ok) throw new Error(`${path}: HTTP ${r.status}`);
  const text = await r.text();
  return { data: JSON.parse(text), text };
}
async function ppBundle(page) {
  const idx = await ppJson(`${page.fetchData}/index.json`);
  const topics = {}, errors = {};
  let sig = ppHash(idx.text);
  await Promise.all((idx.data.topics || []).filter(t => !t.planned).map(async t => {
    try {
      const parts = await Promise.all(['meta', 'stages', 'actions', 'fixtures'].map(n => ppJson(`${page.fetchData}/${t.key}/${n}.json`)));
      const [meta, stages, actions, fixtures] = parts.map(p => p.data);
      topics[t.key] = { topic: Object.assign({ key: t.key, updatedAt: t.updatedAt }, meta), stages, actions, fixtures };
      sig += parts.map(p => ppHash(p.text)).join('');
    } catch (e) { errors[t.key] = e.message; }
  }));
  return { index: idx.data, topics, errors, sig: sig + '|' + Object.keys(errors).join(',') };
}

export {ppPages, ppBundle};
