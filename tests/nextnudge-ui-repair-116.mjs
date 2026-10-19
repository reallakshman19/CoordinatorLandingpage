import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { newThread } from '../site/nextnudge/revamp/thread.mjs';
import { groundingPanel, readGrounding } from '../site/nextnudge/revamp/grounding.mjs';
import { renderGrounding, installFeatures } from '../site/nextnudge/revamp/features.mjs';

test('Repair 1 & 5: Clipboard fallback unhides parent label and shows truthful packet status', () => {
  const app = fs.readFileSync(new URL('../site/nextnudge/revamp/app.mjs', import.meta.url), 'utf8');
  // Fallback box and textarea are both unhidden in catch block
  assert.match(app, /const fb=\$\('#fallback'\),box=\$\('#fallback-box'\);if\(box\)box\.hidden=false;/);
  assert.match(app, /if\(fb\)\{fb\.hidden=false;fb\.value=text;fb\.focus\(\);fb\.select\(\);/);
  // Status feedback beside buttons
  assert.match(app, /id="packet-status" class="packet-status" role="status" aria-live="polite"/);
  assert.match(app, /Packet copied\. Copy does not send\./);
  assert.match(app, /Clipboard denied; use selected manual fallback below\./);
});

test('Repair 2: Grounding state feedback reflects draft, save snapshot, and clears restored notice', () => {
  const t = newThread({ id: 'NN-20261019-173100-aa11', title: 'Grounding state', goal: 'Verify feedback' });
  const store = new Map();
  const DRAFTS = 'nextnudge.grounding.drafts.v1';
  let noticeMsg = '';
  const statusTexts = [];
  const form = { id: 'grounding-form', fields: [['ground-1f', 'Updated task notes']] };

  const originals = {
    document: globalThis.document,
    FormData: globalThis.FormData,
    localStorage: globalThis.localStorage
  };

  globalThis.document = {
    addEventListener: (name, handler) => { handlers[name] = handler; },
    querySelector: () => form,
    querySelectorAll: (sel) => {
      if (sel === '.grounding-status') {
        return [{ set textContent(v) { statusTexts.push(v); } }, { set textContent(v) { statusTexts.push(v); } }];
      }
      return [];
    }
  };
  globalThis.FormData = class { constructor(f) { this.rows = f.fields; } [Symbol.iterator]() { return this.rows[Symbol.iterator](); } };
  globalThis.localStorage = { getItem: k => store.get(k) || null, setItem: (k, v) => store.set(k, v) };

  const handlers = {};
  let renderedHasDraft = null;

  try {
    installFeatures({
      state: {},
      t: () => t,
      append: m => {
        // When append runs, render() is called: draft in localStorage must already be deleted!
        const rows = JSON.parse(store.get(DRAFTS) || '{}');
        assert.equal(rows[t.id], undefined, 'Draft must be cleared from storage BEFORE append/render');
        renderedHasDraft = !!rows[t.id];
        t.moves.push(m);
      },
      render: () => {},
      notice: s => { noticeMsg = s; }
    });

    // 1. User types in grounding form
    handlers.input({ target: { id: 'ground-1f', closest: () => form } });
    assert.equal(statusTexts.at(-1), 'Unsaved device draft');
    const savedDraft = JSON.parse(store.get(DRAFTS))[t.id];
    assert.equal(savedDraft['1f'], 'Updated task notes');

    // 2. User submits form
    handlers.submit({ target: form, preventDefault: () => {} });
    assert.equal(t.moves.length, 1);
    assert.equal(renderedHasDraft, false, 'Unsaved device draft restored must NOT be rendered after save');
    assert.equal(statusTexts.at(-1), 'Grounding saved locally as one update. Save to GitHub for durable sharing.');
    assert.equal(store.get(DRAFTS), '{}');

    // 3. User makes another keystroke after saving: previous saved confirmation is replaced
    handlers.input({ target: { id: 'ground-1f', closest: () => form } });
    assert.equal(statusTexts.at(-1), 'Unsaved device draft');

    // 4. Test storage failure handling
    globalThis.localStorage.setItem = () => { throw new Error('QuotaExceededError'); };
    handlers.input({ target: { id: 'ground-1f', closest: () => form } });
    assert.match(statusTexts.at(-1), /Draft storage failed: QuotaExceededError/);
    assert.match(noticeMsg, /Browser draft storage failed: QuotaExceededError/);
  } finally {
    Object.assign(globalThis, originals);
  }
});

test('Repair 3: Sealed notes opens Utilities details and focuses target', () => {
  const app = fs.readFileSync(new URL('../site/nextnudge/revamp/app.mjs', import.meta.url), 'utf8');
  // Utilities details gets open attribute when state.editor === 'seal'
  assert.match(app, /class="thread-utilities"'\+\(state\.editor==='seal'\?' open':''\)/);
  // seal-host is populated with sealForm and focuses the form target
  assert.match(app, /host\.innerHTML=sealForm\(x,esc\)/);
  assert.match(app, /target\.focus\(\)/);
});

test('Repair 4: Dark appearance contrast for utility and reply summaries', () => {
  const css = fs.readFileSync(new URL('../site/nextnudge/revamp/style.css', import.meta.url), 'utf8');
  // Light mode summary
  assert.match(css, /\.fallback-reply summary,\.thread-utilities summary\{color:#183f45\}/);
  // Dark mode summary has high contrast #a5f3fc
  assert.match(css, /\.fallback-reply summary,\.thread-utilities summary\{color:#a5f3fc\}/);
  // Status colors in dark mode
  assert.match(css, /\.grounding-status,\.packet-status\{color:#86efac\}/);
});
