'use strict';

async function renderBenchmarks(app) {
  const frag = cloneTemplate('tpl-benchmarks');
  app.innerHTML = '';
  app.appendChild(frag);

  const list = $('benchmarks-list');

  const benchmarks = [
    {
      project: 'grade9-pilot',
      snapshot: '2026-10-15',
      note: 'Grade 9 pilot — with events.jsonl, two coordinator epochs, two agent generations.',
    },
    {
      project: 'imo-ab-test',
      snapshot: '2026-10-15',
      note: 'IMO AB test — no events.jsonl (timeline reconstructed from threads + inbox). Includes FAIL→fix→PASS chain, outside write, role conflict, superseded Owner words.',
    },
  ];

  benchmarks.forEach(bm => {
    const row = el('div');
    row.style.cssText = 'padding:14px 16px;border-bottom:1px solid var(--border)';
    row.innerHTML = `
      <div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap">
        <strong>${escapeHtml(bm.project)}</strong>
        <span class="badge badge-yellow">snapshot ${escapeHtml(bm.snapshot)}</span>
      </div>
      <p style="font-size:0.85rem;color:var(--text-2);margin:6px 0">${escapeHtml(bm.note)}</p>
      <button class="btn btn-small bm-load-btn" data-project="${bm.project}">
        Load this benchmark
      </button>
    `;
    list.appendChild(row);
  });

  list.querySelectorAll('.bm-load-btn').forEach(btn => {
    btn.addEventListener('click', async () => {
      const project = btn.dataset.project;
      state.benchmarkMode = true;
      state.benchmarkProject = project;
      state.projects = [];
      state.timelines = {};
      state.evidenceCache = {};
    state.statusBar = null;
      state.ownerInputs = null;
      state.ownerInputsLoaded = false;

      // Update banner
      const banner = $('benchmark-banner');
      banner.classList.add('visible');
      banner.querySelector('#exit-benchmark') || 0;

      await loadProjects();
      navigate('#home');
    });
  });
}

// ── Init ───────────────────────────────────────────────────
