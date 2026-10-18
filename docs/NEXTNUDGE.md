# NextNudge — #97, implementation revision NN-R2

Owner-operated standalone workbench. NextMove remains separate. The UI does
not grant protocol authority, approve merges, claim agents or automatically
send messages. Governing task: https://github.com/reallakshman19/CoordinatorLandingpage/issues/97

## Structure

- `site/js/core.js`: navigation, hash-route mount and polling preservation.
- `site/nextnudge/host.mjs`: same-origin iframe isolation; benchmark entry blocked.
- `site/nextnudge/model.mjs`: actions, correction gates and append-only events.
- `fixtures.mjs`: headings, edits, append-only fields and provenance transfers.
- `schema.mjs`: import validation, including strict IDs, URLs and acyclic trees.
- `repository.mjs` / `storage.mjs`: GitHub readback and explicit save preparation;
  local drafts are never labelled committed merely because they were copied.
- `workspace.mjs`, `prepare.mjs`, `fixture-view.mjs`, `protocol.mjs`: independent views.
- `site/nextnudge-data/workbench.json`: canonical shared project/run snapshot.

No runtime packages, external fonts, new workflow or second publisher.
The existing Pages publisher copies the self-hosted assets and snapshot.

## Data and delivery

Project/run/step IDs are stable. All future steps are available. Sent or answered
instructions are frozen; corrections retain their parent relationship. Resolving
children requires a separate parent review. Evidence remains optional; gaps need
a note. Checklist profiles are versioned configurable JSON.

Copy does not send. Mark sent is an Owner-recorded claim with exact message text,
destination id8 and timestamp; it is not independent proof. Relayed Agent replies
retain exact text, recorded UTC time, and a separate actual reply time or null.
A matching ACK is recorded, never manufactured. Chat URLs are device-only because
this repository is public; they are excluded from shared snapshots.

GitHub edit flow: prepare snapshot (checks base blob SHA), copy JSON, open GitHub
editor, review/paste/commit manually, then verify content readback. A changed base
refuses save preparation. Browser tabs warn on concurrent draft changes. GitHub
credentials are not stored in the app and no automatic API writes occur.

Delete is a tombstone: working-list entries disappear; source/history remains.
Copies from earlier headings retain project/run/row/revision/time provenance and
start NEEDS_REVIEW. Roadmap edits need an Owner-approved update basis; Owner intent
and future-improvement headings append rather than overwrite.

## Real pilot and limits

The pilot is this issue #97, using inspected public repository facts and actual
local rule-test results. The second run demonstrates predecessor fixture pulls;
it is explicitly an unassigned handover rehearsal, not a launched successor.
No actual chat delivery, independent review, acceptance or production deployment
is claimed. Original golden export and performance benchmark are UNKNOWN.

Base: c83e1b3a4ca297c321d446f888625295a3c1a3cc. No active lease or open PR at review.
Current branch: codex/nextnudge-tab-97. Shared changes: core.js only; other source
changes are isolated under site/nextnudge. No registry or NextMove engine changes.

## Verification

Run `node --test tests/nextnudge-*.mjs`.
Browser QA is NOT_RUN: installed Playwright has no Chromium executable in this
workspace. Independent review, CI and deployed Pages readback remain separate.

## Published checkpoint and continuation

PR: https://github.com/reallakshman19/CoordinatorLandingpage/pull/100 (draft).
Code basis: 52043a3d6871f7eb55698762cae228d3746b4732. The following metadata
checkpoint appends the real PR and validation facts to the pilot; no source
behaviour changes are included in that checkpoint.

17 Node checks PASS; baseline navigation/poll assertions produce 2 expected
assertion failures on c83e1b3a and PASS on the code basis. GitHub CI was initially
queued/running; no pending run is counted as PASS. Source files remain <=300
physical lines; core 288 to 298. Event dispatch/render functions are cohesive
handlers, with template markup included in spans; independent cohesion review
is still pending, not inferred from the line limit.

Pilot project: PRJ-20261018-085012-1225.
Implementation run: NN-20261018-085012-215a.
Successor-transfer rehearsal: NN-20261018-085013-3e7b.

The browser GitHub save can be fully exercised only after the snapshot exists
on main. Until then, the candidate's deployed-file fallback can show the pilot,
but it explicitly reports that the GitHub base is unavailable. The initial
private Sites prototype has not been silently replaced; this task delivers the
repository integration.
