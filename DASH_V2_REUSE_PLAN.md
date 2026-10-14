# Dash V2 reuse plan for CoordinatorLandingpage

Status: **PROPOSED — source-mapped, not implementation or acceptance**. Prepared15October2026, Dubai. Basis inspected locally: Common PR377 head `f31d8d35f8f6d2fa3d212e6d0801207d278eea84`; no tracked differences in the inspected master_panel and command modules. No product edits, tests, browser delivery, workflow activation or new agents in this planning unit.

## 1. Decision

Use CoordinatorLandingpage as a **GitHub-native interface and projection** of the existing Dash/control-tower logic. Keep one canonical backend for registered identity, evidence and command state. Do not create a second dashboard, request engine or copy of the database model.

Owner requests/comments/forms become one additional input adapter. Sanitized GitHub comments/status threads become one output adapter. Dash V2 continues as the visual consumer of the same qualified read model. Existing coordinator runtime remains responsible for actual supported guarded browser delivery; importing command code does not activate a provider worker.

This changes the original implementation strategy from building a generic new control platform to reusing pinned components and filling explicitly identified seams. Reuse is an engineering proposal, not evidence that those components are fully integrated or independently accepted.

## 2. Inspected sources and evidence limits

- `coordination/master_panel/CONTRACT.md` and `HANDOFF.md` describe source identity, versioning, health, public projections and local read routes.
- `github_source.py`, `storage.py`, `report_parser.py`, `casp_validation.py`, `casp_store.py`, `registration.py`, `pr_checks.py`, `models.py`, `read_api.py` expose candidate components listed below.
- `coordination/command_contracts.py`, `command_engine.py`, `command_db.py`, `command_service.py` provide existing command-plane contracts, journaling and transport boundaries. Their availability does not prove the new GitHub-control path works.
- Existing registration/CASP/Owner-command tests contain useful counterexamples; test-name inspection is not execution or independent PASS.
- Retained F07-B decomposition describes B2 scanner/recorder atomicity, B3 coherent read/cursor and B4 integration gaps. Its historical “Codex implements corrections” and missing-private-destination wording is superseded by later Owner role/override controls.
- Standalone B1 full pinned-dependency independent verification remains NOT_RUN. Accepted Dash product outcomes remain0. Preserve all historical failures and shim-only execution limits.

## 3. Reuse matrix

| Requirement | Available logic at the inspected pin | Proposed treatment | Qualification boundary |
|---|---|---|---|
| Fetch GitHub issues/comments, pagination, bounded reads, source health | `master_panel/github_source.py` — PublicGitHubReader, GitHubSourceScanner | Reuse read/pagination/error semantics; add an explicitly registered control-mailbox source adapter | Current allowlist covers Common/AA3 only; no permissive arbitrary-repo ingestion |
| Exact object identity, edit history, replay and absence | `models.py` SourceIdentity + `storage.py` SourceStore | Reuse object/version model and durable revision history | Preserve A→B→A edits, conflict and complete-scan-only absence semantics |
| Structured agent ACK/PLAN/RESULT validation | `casp_validation.py` and pinned CASP schemas | Reuse unchanged envelope/correlation checks | Plain Owner text is a separate ingress format; do not silently relax CASP |
| Correlated raw report recording | `casp_store.py` CaspStore | Reuse recording/history; finish B2 integration | Scanner currently drops context before recorder; transaction/restart seam must qualify |
| Existing successor/new conversation generations | `registration.py` RegistrationStore.record_snapshot/select_current | Reuse snapshots, pointer history and expected_previous checks | Record supplied URL as provisional; actual proof/grounding/adoption still required |
| Command identity, idempotency and receipts | `command_contracts.py`, `command_db.py`, `command_engine.py` | Reuse typed targets/actions, journal and single-flight/uncertainty semantics | Review exact authority and native-runtime mapping; never create two independent send owners |
| Source/work/evidence rows and public redaction | `models.py` build_row and existing projection/schema contracts | Reuse typed allowlisted projections | New status fields must be explicitly admitted; no private command DB/raw body exposure |
| Source freshness and bounded project queries | `read_api.py` MasterReadService | Reuse qualified read model for Dash and GitHub summaries | Complete B3 coherent snapshot/generation-cursor integration; GET stays read-only |
| PR/head/check evidence | `pr_checks.py` PullCheckIntake | Reuse head-bound CI and applicability | No per-cycle reruns; skipped/old-head proof is not current acceptance |
| Actual tab status, Worked labels, turns/pages, guarded sends and aims | Installed coordinator-protocol runtime plus existing durable observations | Reuse actual probes, metrics and delivery/aims receipts | GitHub cannot observe private page liveness; unsupported adapter stays unsupported |
| GitHub inbox/form UX | Existing dedicated inbox1 and README | Keep current comment route; later add native Issue Forms as metadata | Forms require separately released engineering/default-branch deployment |
| GitHub ACK/RESULT/status publication | Current manual publication/readback receipts | Small restart-safe output adapter over qualified projection/ledger | Intent/readback/reconciliation needed; no duplicate POST after uncertainty |

## 4. Thin adapter architecture

```text
Owner GitHub issue/comment/form
  -> OwnerInboxAdapter: exact source/version, actor evidence, project, parsed request
  -> existing qualified registration + command admission/journal
  -> current coordinator planning/native delivery guard
  -> actual mapped ChatGPT/LA conversation

Agent GitHub report
  -> existing source scanner -> qualified CASP recorder -> applicability/review

Actual browser observation
  -> existing coordinator probe/aim/delivery records -> allowlisted observation view

Qualified rows + receipts + observations
  -> SnapshotPublisher -> CoordinatorLandingpage status/ACK/RESULT comments
  -> Dash V2 UI through the same released read contract
```

Logical new pieces, proposed names rather than installed modules:

1. **OwnerInboxAdapter:** normalize plain comments/form bodies into request records, preserving original GitHub actor/object/body version. Resolve project/assignment only through registry. Match decision cards; do not equate a claimed sender with Owner authority.
2. **SnapshotPublisher:** turn qualified existing rows/receipts/probes into sanitized Markdown. Record publication intent, logical ID/body version, actual comment ID, readback and uncertain/restart disposition. One formatter should feed both agent/project summaries and the landing page.
3. **GitHub control surface/config:** forms, repository/issue routing, enrolled actor identities and current control project mappings. Store configuration separately from product source and protected authority.

Successor/add-agent forms should call the existing qualified registration path, not build a second registry. Provider interaction should use the existing actual supported guard, not a new automatic worker. Identity separation still requires actual Owner-controlled setup; no code reuse can infer a human author from shared credentials.

## 5. Explicit compatibility gaps

### Repository and project identity

Current source allowlist is `common`/Common repo1412133785 and `aa3`/AA3 repo1363905693. The dedicated control repository is CoordinatorLandingpage repo1419959095. Product alias `dash-v2` and source project key `common` are not interchangeable.

Define and test explicit routing: control-mailbox repository -> selected product project -> registered assignment -> actual conversation binding. Do not rewrite old persisted IDs or treat the control repository as a product evidence source for every project. Adding its mailbox source needs a bounded reviewed adapter/registration change, not disabling the allowlist.

### Atomic recording and coherent reads

B1 registration storage is standalone. Existing source and CASP stores own separate connections; naive hooks can expose a source row without its qualified recorder context. Finish B2 with a tested atomic boundary or explicit nonqualified reconciliation state. Finish B3 so one read snapshot/cursor includes source, registration, CASP and invalidation generations coherently. Preserve last-good evidence on partial scan/failure.

### Two command implementations are not two dispatchers

Existing command_engine is product/control-tower logic; cycle.py is the running coordinator's guarded interaction runtime. Engineering must select one authoritative side-effect owner and document a state/receipt mapping. Reuse command semantics and evidence through an adapter while actual browser effects remain guarded. Do not wire both engines to send independently, infer live delivery from NoOpTransportAdapter, or bypass native unresolved-send/Owner-intervention checks.

### Distinct command acceptance and product acceptance

An internal command state named ACCEPTED means admitted to a command workflow, not accepted Dash product outcomes. Render these as separate labels. Agent ACK/adoption, coordinator review, test PASS and product criteria have separate evidence and counters.

### Browser observations and public status

Existing probe/metric logic is reusable. The publisher must preserve real capture time, observed IDs, lower bounds and UNKNOWN values. Public output should omit private chat routes, raw prompts/drafts and command DB contents. Full page information requires the separately selected privacy channel; this repository is currently public. An old snapshot must never authorize a new send.

## 6. Phases and engineering ownership

| Phase | Bounded task | Reuse target | Release/verification |
|---|---|---|---|
| R0 — qualify reuse contract | Produce exact module/contract/source index and adapter interfaces; reconcile current Owner/agent controls | Existing F07-B decomposition, source contract and this plan | Read-only engineering preparation; no writer release implied |
| R1 — finish existing backend seam | Independent B1 challenge, then B2 recording/B3 read/B4 integration | M4's existing backend continuation, not a parallel replacement backend | M4 after actual adoption/scoped writer release; independent M3 exact-head qualification |
| R2 — Owner GitHub ingress | Explicit control-repo registration, plain/form parser, actor/admission/decision mapping | Source identity, registration and command receipts | Separate approved scope; negative identity/cross-project/edit/replay cases |
| R3 — GitHub status/output | Sanitized snapshots, ACK/RESULT publication and permalink chain | Existing projections, CI, probes and journal | Read-only publication first; crash/duplicate/privacy qualification |
| R4 — office forms and successor workflow | Native forms and generation-change UX, not new engine | Existing registry/pointer/plan rules | Owner-opened successor test; no duplicate launch/writer; protected approval checks |
| R5 — shared visual panel | M2 consumes the same backend contract | Existing Dash view/read API; GitHub remains office interface | Only after complete seam qualification and sole UI writer release |

M4 is the proposed engineering owner for eligible backend preparation/continuation, subject to actual adoption and scope. A new control-repository adapter assignment is not silently added to its material write scope. M3 G3 is Owner-opened but not yet verified/adopted as active; do not invent its readiness or create another successor. M2 remains UI preparation/dependency-held. Economy Coordinator only grounds/routes/reviews applicability and does not implement or independently certify these phases.

If an adapter needs a different engineering owner, prepare a durable handover and obtain actual assignment/launch authority. Never send corrections back to stopped M1 merely to save setup effort.

## 7. Validation strategy — reuse oracles, add seam tests

Reuse applicable existing tests for source-version replay, registration conflicts, cross-project identity, idempotency and privacy. Do not rewrite them to mirror a new implementation or reduce criteria. Existing independent seven-case evidence remains shim-limited until full pinned dependencies execute independently.

Add focused integration cases where interfaces change:

- Control-repo comment selects Dash versus AA3 correctly; AA3 HOLD is retained.
- Plain Owner request is not parsed as an authenticated CASP agent report; same-account agent approval cannot release protected work.
- Numeric repo/object identity and alias mapping prevent source/assignment collisions.
- Edit/supersede/delete/restart preserves body versions and invalidates stale decisions/actions.
- Partial scanner/recorder failure cannot expose qualified correlation or refresh old proof.
- Registry/CASP/source change invalidates the correct read cursor/snapshot.
- Command/native delivery adapter has one side-effect owner; uncertain send/publication is reconciled without duplicate effect.
- Owner-opened M3 G3 is registered/adopted once, old generation receives no work, historical evidence is not promoted.
- Sanitized GitHub snapshot has capture time/head/coverage/proof links and excludes private fields.
- Exact-head independent review and existing project outcomes remain distinct from support/adapter test counts.

No tests were executed for this plan. Qualification must use the exact implemented candidate and applicable profiles, not a remembered passing count.

## 8. Effort reduction and what remains new

Expected savings come from avoiding a second database model, CASP implementation, source scanner, registry, command lifecycle, CI interpreter and dashboard frontend. The likely new write surface is adapters, configuration/forms and seam tests. Integration/identity/recovery work is real and cannot be removed by calling existing modules reusable.

Do not present a percentage or date as measured savings. The engineering owner should report per-phase existing/reused/new interfaces, changed-line estimate, test effort and unresolved dependencies after R0. Use the retained bounded-unit decomposition rules; split a unit if its applicable size/time limits are exceeded before release.

## 9. Immediate next eligible work

Under a separately delivered scoped request, the engineering owner prepares **R0 / B2-P0 reuse interface assessment** against the exact pinned head. Outputs: module/interface index; repo/project alias mapping; scanner/recorder atomicity decision; command/native-runtime state mapping; minimum ingress/publisher changes; tests and ownership. This is a reviewable preparation deliverable, not implementation release.

In parallel, resolve actual M3 G3 grounding/adoption and independent B1 capability using its existing handover. Do not re-run historical tests simply to refresh a cycle. The coordinator can maintain the current GitHub inbox/status documentation while dependent product integration remains gated.

Current dedicated repository/inbox remains operational as registered; this plan does not enable any worker, automatic provider adapter, real command SEND, new agent, merge/deploy, workflow or product acceptance.
