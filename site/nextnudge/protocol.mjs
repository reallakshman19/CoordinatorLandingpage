import {esc} from './util.mjs';
export const SECTIONS=[
  ['purpose','Purpose and boundary',[
    'NextNudge is the Owner’s standalone workbench for instructing a coding agent. NextMove belongs to the Coordinator protocol. This page does not create claims, approvals, dispatch authority or automatic sends.',
    'The main ladder is predetermined; feedback creates child branches. You may use a nudge for implementation, midcycle reconciliation, recovery or any other task. Labels and step counts are editable.'
  ]],
  ['grounding','Grounding and continuity',[
    'Use Grounding Fixtures for On boarding, Midcycle 1, Midcycle 2, Exit and successor improvements. Each heading accepts items and source links. Missing originals, goldens, benchmarks and tests must be marked UNKNOWN.',
    'Pulling a heading copies an earlier run’s rows, source IDs, source revision and pull time. Copies start NEEDS_REVIEW. They do not silently track later edits. Owner discussions and future improvements append; roadmap replacements require a recorded Owner-approved update basis.',
    'Archived runs remain available for transfer. Delete removes a run or unused step from the working list while retaining its tombstone and history in the snapshot.'
  ]],
  ['delivery','Copy, send and reply',[
    'Copy for chat includes project, run and step IDs and asks for ACK of the step ID. Copying does not send anything. Mark sent is your record that you delivered the exact copied instruction to the recorded chat id8; it is not independent proof.',
    'Mark sent freezes the instruction. Revisions after delivery use a correction child. Duplicate Mark sent is refused. Replies are pasted exactly and labelled Agent, manually relayed by Owner. Recorded time and actual reply time are separate; unknown reply time remains UNKNOWN.',
    'A mismatched ACK is rejected. An absent ACK is retained as unknown, rather than invented. Chat URLs stay on the device; public snapshots carry chat id8 only.'
  ]],
  ['review','Review, correction and gaps',[
    'Instructor guide lives in Prepare the Ladder. Import configurable JSON profiles and combine Quantitative, Conceptual, Implementation, Coding or your own profiles.',
    'A correction blocks acceptance of its parent. Resolving all children returns the parent for re-review; it does not automatically accept the parent. Accepted here is the Owner’s local workbench judgment, not VERIFIED or protocol acceptance.',
    'Evidence is optional. Unreviewed checklist items, Proceed with gap and missing evidence links require a review note. Needs correction must be resolved before acceptance.'
  ]],
  ['locks','No future-step locks — current behaviour',[
    'Every nudge is visible and available from the start. There is no automatic sequential unlock. Choose the step you need; you may reorder work by selecting another step.',
    'Separate safeguards remain: sent/answered instruction text is frozen, paused or archived runs are not editable, and unresolved correction children block parent acceptance. These are integrity safeguards, not future-nudge locks.',
    'Future proposal only: an optional guided mode could release steps after predecessor review. It should show the reason and a deliberate override with a note. It is not implemented or enabled.'
  ]],
  ['storage','GitHub snapshots and browser drafts',[
    'Canonical shared data belongs to site/nextnudge-data/workbench.json in CoordinatorLandingpage. Browser storage holds unsaved drafts. Export after a session until the GitHub readback confirms your snapshot.',
    'Prepare GitHub update checks the source blob SHA, copies the complete JSON and provides the GitHub edit page. You paste, review and commit using GitHub. NextNudge stores no token and performs no automatic write. Verify GitHub save compares the committed content with your prepared snapshot.',
    'A changed GitHub base or another browser tab triggers a conflict warning. Export the draft and reconcile before replacing data. Archive/delete and edits append events; they do not erase earlier event rows. Import validates identifiers, relationships, profile shapes and safe URLs. Imported content remains a claim, not verified proof.',
    'All event times are UTC; export format is version 2. The event shape includes step, state, by, at, proof and note. It is deliberately not a valid NextMove ledger or a grant to convert local acceptance into VERIFIED.'
  ]]
];
export function protocol() {
  return `<section class="panel protocol-page"><aside><h3>NUDGE PROTOCOL</h3>${SECTIONS.map(([id,title])=>`<a href="#nn-${id}">${esc(title)}</a>`).join('')}</aside>
    <article><span class="eyebrow">STANDALONE · VERSION 2</span><h1>Nudge Protocol</h1><p>Owner-operated instructions, grounding and continuity.</p>${SECTIONS.map(([id,title,paras])=>`<section id="nn-${id}"><h2>${esc(title)}</h2>${paras.map(p=>`<p>${esc(p)}</p>`).join('')}</section>`).join('')}</article></section>`;
}
