# Dashboard implementation — recovery checkpoint
HANDOVER_READINESS: READY
PR_RECOVERY_STATE: HEALTHY
TAKEOVER_AUTHORITY: WRITE_ALLOWED (current Owner instruction)
WORK_INTENT: IMPLEMENT
CRITICALITY: STANDARD
REPOSITORY: reallakshman19/CoordinatorLandingpage
PR_OR_WIP: WIP-dashboard-20261021
BRANCH: codex/otm-dashboard-20261021
REPORT_BASIS_HEAD: 4637f83b7cb4dcf48fafa9db98852a1332416ab9
MAIN_HEAD_LAST_CHECKED: 4637f83b7cb4dcf48fafa9db98852a1332416ab9
MERGE_BASE: 4637f83b7cb4dcf48fafa9db98852a1332416ab9
REPORT_SYNC: CURRENT (only recovery metadata after basis)
GROUNDING_EPOCH: GE-dashboard-20261021-01
CURRENT_STAGE: IMPLEMENT
APPENDIX_A_STATUS: NOT_REQUIRED (new standard UI work; no engineering-critical takeover)
EXACT_NEXT_ACTION: implement read-only #dashboard model/view against status_bar.v1.

## Mission and scope
Owner requests a new Dashboard page reusing the provided operational HTML and existing data; continue high/medium ROI coding. Working UI must show source-backed traffic lights, evidence/observation age, known state duration, timer observation, scheduled check countdown and overdue state, with project/state grouping and expanded evidence. No synthetic production agents or dates. Reuse existing publisher, grants, monitoring, and routing; do not add schedulers or dispatches. No merge authority.

## Live grounding and coordination
Main is the basis above. No AGENTS.md, agents master index, or active repo-local claims exist at that tree. Existing registry writer leases inspected: released. Open PRs #123, #120, #105 inspected using actual changed-file lists. None overlaps the planned paths. #120 has substantially more changed files than its test-only description; do not trust description as file truth. Its actual paths remain outside this scope. Coordination: SAFE for this bounded read-only view. Other workstreams and HOLDs are not resumed by this assignment.

## File claim
site/index.html; site/js/core.js; new site/js/dashboard-model.js; new site/js/dashboard.js; new site/dashboard.css; new tests/dashboard.test.cjs; own agents recovery records. Shared files get navigation/script/route wiring only. No workflow, canonical logs, backend or existing status-rule edits.

## Data boundary and diagnosis
status-bar.json supplies normalized registered declarations, work/monitoring/authority dimensions, timer state/checked_at/last_tick/next_due, browser observation and as_of. projects.json and build-info supply project context/capture. monitoring.next_due is a freshness threshold, not a scheduled check; label separately. State-start timestamps are often absent: display UNKNOWN rather than derive from capture. Preserve project-qualified identity and evidence links. Recheck positive observations as the local clock advances. Benchmark clocks must remain frozen.

## Current implementation / validation
Bootstrap only; implementation and tests NOT_RUN. Browser engine unavailable in this workspace (earlier preview finding); assess available runtime again if needed. Local source files are selected exact-head materializations, not a complete git clone. No independent verification claimed.

## Risks / continuation
RISK-001: confusing timer schedule with monitoring freshness; regression required.
RISK-002: stale green as time passes; regression required.
RISK-003: late async response or interval surviving navigation; integration regression required.
RISK-004: unavailable state start or evidence timestamp; never invent one.
Next: build pure projection functions and real DOM consumer, test known fixtures/negative cases, commit checkpoints, open draft PR and record exact head/check state. Independent review remains required.
