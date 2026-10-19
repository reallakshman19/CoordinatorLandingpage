# NextNudge distinct workspaces — implementation record

Owner request (2026-10-20 Dubai): each tab needs unique UI, fields to save and link, and real functionality. Fix the code directly.
Base: `99db602e9ed7d6f63a110e13ca0450f552c4d355`; branch: `fix/nextnudge-distinct-workspaces`.
This continues #110 after merged #112 and #116; #105's legacy-v2 work remains separate.

## Bounded acceptance
- W1: Ground, Task, Correction and Reconcile have distinct field sets, own save actions and tab links.
- W2: Task/Correction can select an immutable saved Ground version; Correction/Reconcile select actual recorded exchanges. Source URLs are usable links.
- W3: Fields and editable packet drafts survive tab navigation/reload independently per thread and workspace.
- W4: Typing creates no history; each meaningful save adds one append-only snapshot; unchanged saves add none; storage failures preserve recoverable work.
- W5: Packet content comes from the selected fields/references; stale fields, HOLD, private chat URLs and invalid closure cannot bypass existing protections.
- W6: Preserve existing data, sent bytes, ACK linkage, native Owner acceptance and GitHub save/transport; report real evidence and browser limits.

## Architecture
One shared canonical thread, with workspace snapshots carried as versioned amendment notes. Each mode owns its fields and save history. Local drafts are separately keyed by thread/mode.
Ground captures source links, orientation and existing Grounding Fixtures; Task links an exact saved Ground ID and specifies task/deliverable/check; Correction links a recorded exchange and specifies observed/expected/redo/preserve; Reconcile links a response and saves criteria/verdicts/decision independently.
The shared packet renderer and transport remain below those distinct forms.
This is standard software implementation in Owner-selected standalone mode, not a new coordinator/qualification exercise.

## Current checkpoint
Core model, views, per-mode draft storage and behavioral harness are prepared; app routing is not wired yet.
Baseline full suite: 99/99 pass.
Before wiring: `node --test tests/nextnudge-*.mjs`: 109 tests, 104 pass, five UI-routing behavior failures, no errors/skips.
The five failures distinguish the old generic composer flow from the requested workspaces. Core model tests already pass.
This RED checkpoint contains prepared modules as well as tests; it is not described as a test-only commit.

Next: wire app actions/rendering, source links and form submissions; style the distinct forms, rerun all tests, inspect the exact remote candidate and CI.
Visual/browser interaction verification is currently NOT_RUN: the cloud browser cannot reach the local preview (connection refused), and Opera exposes no click/type surface.
Local production-handler tests do not substitute for screenshots or visual QA.
No canonical thread, workflow, native acceptance rule or legacy-v2 mutation is authorized in this patch.
No merge/deployment has been performed.
