# Coordinator control implementation plan — ASCII UI and bounded workpacks

Status: **IMPLEMENTATION STARTED — CODEX EXPLICITLY DESIGNATED CODER FOR CoordinatorLandingpage implementation**. Prepared15October2026, Dubai. Owner requested a detailed plan and coding. The Owner subsequently revoked Economy Coordinator and explicitly selected Coder for CoordinatorLandingpage implementation. This named scope authorizes the first implementation slice here; it grants no new engineering conversation, protected release or unrelated project authority.

Repository: `reallakshman19/CoordinatorLandingpage` (PUBLIC). Last inspected head before this document: `97c9cc9b55bc9d630535945ae3b89c550235df00`, containing documentation only. Existing inbox1, Dash status2, AA3 HOLD registration3. No forms, workflow, browser worker or approval processor is installed.

## 1. Product boundary and ownership

One Owner, one active Economy Coordinator, multiple isolated project assignments. GitHub is the office interface; the running home coordinator performs authorized coordination; engineering agents implement and independently verify. Dash V2 and GitHub should consume the same qualified records, not competing engines/databases.

Proposed control-project Main Aim `MA-GCCP-r1`: manage registered project/agent work from office GitHub with traceable requests, decisions, observations and execution receipts. Proposed first coder task `TA-GCCP-C1-r1`, workpack `GCCP-C1-S1`. These labels are proposed planning identities, not fabricated ledger adoption or selected v3.6 work-label approvals. Dash `MA-D2-MASTER-r2` and original project criteria remain unchanged.

Roles: Owner approves priorities/protected authority; this Codex session is the explicitly assigned Coder for the first slice. A coordinator outside that named Coder scope grounds/routes/reviews applicability; independent verifier and post-handoff repair owner require distinct applicable assignments before release. Stopped coders are not sent repairs. M3G3 is Owner-opened but not yet live-verified/adopted. Existing M2/M4 scope is not borrowed automatically.

## 2. Office UI — GitHub native first

These ASCII screens are specifications, not rendered/installed screens. Initial links/forms use GitHub's native UI; a custom web app is unnecessary for first delivery.

### A. Landing page / README

```text
+---------------------------------------------------------------------+
| COORDINATOR CONTROL                         Last check: <time/age>    |
| Home coordinator: <observed state or UNKNOWN>  Mode: Economy          |
+---------------------------------------------------------------------+
| [Request work/status] [Agent change] [Respond to decision]            |
| [Inbox & activity]    [Pending approvals] [Protocol / help]           |
+---------------------------------------------------------------------+
| PROJECT     STATUS             AGENTS      OWNER ACTION              |
| Dash V2     <latest qualified>  <counts>    <decision links or none>   |
| AA3         HOLD               <known>     No engineering resumed     |
+---------------------------------------------------------------------+
| ACTIVE REQUESTS                                                     |
| Request | Project | State | Responsible actor | Next | Updated        |
| <link>  | <id>    | ...   | ...               | ...  | <time>         |
+---------------------------------------------------------------------+
| Public summaries only. Capture time != publication time.             |
| Submission != delivery != execution != independent acceptance.       |
+---------------------------------------------------------------------+
```

### B. Request / change form

```text
+---------------------- REQUEST / CHANGE -----------------------------+
| Project*       [dash-v2 / aa3]                                       |
| Request type*  [status / next / question / change / hold / resume]     |
| Agent/task     [optional stable alias/task ID]                        |
| Instruction*   [                                                     |
|                ]                                                    |
| Supersedes     [prior request/card permalink, when applicable]        |
| Evidence       [public links; no secrets/private drafts]              |
|                                                                     |
| [Submit new issue]                                                  |
| Submission stores a request. It does not execute an agent action.    |
+---------------------------------------------------------------------+
```

### C. Agent / successor change form

```text
+-------------------------- AGENT CHANGE -----------------------------+
| Project*       [dash-v2 / aa3]                                       |
| Operation*     [register successor / register existing /              |
|                 request new agent / retire]                          |
| Existing agent [assignment + previous generation]                    |
| Proposed role  [coder / reviewer / preparation + scope]               |
| Existing URL   [only if already opened; never duplicate creation]     |
| Handover       [exact artifact/link]                                 |
| Already done   [instructions/files Owner supplied in that chat]       |
| Requested      [registration / grounding / creation / other]          |
| [Submit new issue]                                                  |
| Provisional -> inspect -> grounded adoption -> activated binding.     |
+---------------------------------------------------------------------+
```

The repository is public. Do not require publication of private chat routes/drafts; allow a restricted reference or a request to reconcile an already privately supplied URL. A missing required execution identity blocks that dependent dispatch, not unrelated status work.

### D. Approval card and response

```text
+------------------------ DECISION REQUIRED --------------------------+
| Card: <id> / revision <n>     Project: <id>     State: OPEN            |
| ACTION: <exact effect, target generation, files/head when relevant>   |
| WHY: <concrete approval rule and source>                             |
| SCOPE/LIMITS: <one action/batch, allowed paths, time/cost scope>        |
| EVIDENCE: <handover / source / original request links>                |
| VALIDITY: <scope/version/expiry, prerequisites still outstanding>     |
| [Approve] [Reject] [Modify] [Defer]                                  |
+---------------------------------------------------------------------+
                           opens native form
+-------------------------- DECISION FORM ----------------------------+
| Project / Card ID / Revision / Digest: [prefilled; validated later]    |
| Decision* [Approve / Reject / Modify / Defer]                         |
| Limits / requested modification: [                                 ]|
| [ ] I confirm the exact referenced card action/version.              |
| [Submit response]                                                   |
+---------------------------------------------------------------------+
```

Links/form prefills are editable, not authority. Exact canonical card/version/digest and enrolled Owner actor must qualify. Modify creates a revised proposal. Neither checkboxes nor same-account agent replies establish human approval. Native forms open pages; no custom popup or guaranteed notification is installed.

### E. Agent status and trace

```text
+----------------------- PROJECT / AGENT STATUS ----------------------+
| Agent [chat/private ref] | Generation | Captured at | Age | Status    |
| Aim / task / plan        | Claimed / reviewed     | Current head      |
| Minutes/pages/turns      | lower-bound/UNKNOWN    | CI refs + checked  |
| Coordinator action: <planned / attempted / verified + receipt>        |
| Owner action: <none / exact decision link>                            |
| Trace: Request -> ACK -> Delivery -> Agent result -> Review -> RESULT |
+---------------------------------------------------------------------+
```

Public projection omits private routes, raw bodies, drafts, credentials and unrestricted screenshots. Full snapshots require the selected privacy channel. GitHub source freshness and browser liveness remain separate.

## 3. Repository structure and reuse

Proposed new surface:

```text
CoordinatorLandingpage/
  README.md                              # Office entry/index
  .github/ISSUE_TEMPLATE/
    request.yml                          # Native request/change form
    agent-change.yml                     # Existing/new/successor request
    decision.yml                         # Exact decision response
    config.yml                           # Keep plain issue fallback
  docs/                                  # Protocol and interface contracts
  adapters/                              # Later: thin intake/publication only
    owner_inbox.*
    status_publisher.*
  tests/                                 # Later: discriminating seam tests
```

Language/layout for later adapters must be selected by the engineering owner against the existing Python interfaces; do not create placeholder execution code now. Reuse pinned Common `f31d8d35f8f6d2fa3d212e6d0801207d278eea84`: source scanner/storage, CASP validation/recording, registration, typed command receipts, read model and PR checks. Coordinator runtime supplies actual guarded delivery/observations/aim review. Preserve one side-effect owner; do not activate two dispatch engines.

Current allowlist does not include control repo1419959095. Explicitly map control mailbox -> product project (`dash-v2` versus source key `common`) -> assignment -> binding. Finish applicable B1/B2/B3/B4 qualification; importing a module does not certify integration.

## 4. Phases and independently reviewable units

| Unit | Implementation deliverable | Depends on | Acceptance / stop boundary |
|---|---|---|---|
| S1 | Three native forms, chooser config, README links | Assigned/adopted C1 scope and actual coding-protocol selected inputs | Valid YAML/documented form shape; no backend, workflows or command execution. UI availability verified only after separately authorized default-branch release |
| S2 | Canonical project/agent/decision contracts and separate actor enrollment | Engineering interface review, Owner identity setup | Wrong actor/project/version rejected; no agent-authored protected approval |
| S3 | OwnerInboxAdapter + durable version/dedupe mapping | Qualified source/registration/command seams | New/edit/supersede/restart/cross-project cases; AA3 HOLD preserved; no real browser send |
| S4 | Sanitized status/ACK/RESULT publisher | Qualified read model and actual observation contract | Exact permalinks/capture age/privacy; uncertain POST cannot cause duplicate publication |
| S5 | Successor/add-agent activation workflow | Actor/adoption/registry and pending-effect reconciliation | Existing opened successor registered once; old generation fenced; no overlapping writer |
| S6 | Actual coordinator dispatch bridge | Independent exact-head checks, native guard, explicit effect authority | One harmless office request end-to-end with actual receipt/result; no invented delivery |
| S7 | Shared Dash/GitHub view and optional Projects/Pages | Complete released read seam, M2 scope/release | Two views of same qualified data; no second backend or frontend token |

S1 is the smallest coding start and can be independently scoped without pretending the backend is qualified. Later phases stay gated. GitHub Actions wakeups/automatic workers and custom authenticated web UI remain deferred. Existing reminder stays generic and15minutes.

Use bounded units: target <=700 changed lines /15 minutes; hard retained limits <=1500 /20; split before release if an applicable limit would be exceeded. These are planning bounds, not a promised overall delivery date. Engineering estimates new/reused surfaces and validation per unit after adoption.

## 5. First coding workpack — GCCP-C1-S1

**Purpose:** Owner can select Request, Agent change or Decision in native GitHub issue creation, with clear data/authority boundaries.

Allowed changes: `.github/ISSUE_TEMPLATE/request.yml`, `agent-change.yml`, `decision.yml`, `config.yml`, and only relevant README instructions/links. No product/backend code, credentials, permissions, Pages, workflows, registry activation or real command sending.

Form fields:

- Request: `project_id`, `request_type`, optional `target`, `instruction`, optional `supersedes`, `evidence`.
- Agent change: `project_id`, `operation`, `previous_assignment`, proposed `role_scope`, optional/restricted `existing_route_ref`, `handover`, `owner_already_supplied`, `requested_effect`.
- Decision: `project_id`, `card_id`, `card_revision`, `card_digest`, `decision`, `limits_or_changes`, explicit confirmation. Prefills do not authenticate responses.

Project choices initially dash-v2 and aa3, with conspicuous AA3 HOLD wording. Use GitHub-supported elements and unique field IDs; do not invent dynamic/conditional form behavior. Preserve plain-comment/blank-issue fallback. Do not add labels/Projects/assignees that do not actually exist or request ungranted repo access. Buttons are links to native forms, not claims of an installed backend.

Any future separately assigned engineering agent must read the exact public protocol, reuse and approval designs, repository rules and Engineering PR Delivery v3.6 pin `Common@2963ec3003980873804638860e5ebdd9022de1c8`. Its actual work-specific label/plan selection and lane adoption must be established, not copied or invented. For this initial slice, the Owner explicitly designated this Codex session Coder; that actual scope is recorded separately and no external-agent adoption is fabricated.

Deliver a bounded draft PR with base/head, file index, validation evidence and limitations. YAML parsing plus documented-shape/diff checks are appropriate here; do not build a new test framework to mirror four metadata files. GitHub-visible template submission checks remain NOT_RUN until the forms are actually released on default branch under applicable authority. Do not claim live UI PASS from local YAML syntax.

Acceptance criteria:

1. Exactly the three form purposes are available in the proposed chooser, with readable required fields and unique IDs.
2. Project/agent/change/decision references are unambiguous; no form implies execution, approval, new launch or writer release by submission.
3. No public form demands private transcript/token/draft content; restricted refs can be requested where needed.
4. Existing inbox/public sanitized status and AA3 HOLD remain explicit.
5. Draft PR contains only allowed files; no workflow/security/product mutation; honest qualification limits and exact handoff.

Coder stops after indexed handoff. Independent exact-head review and any separately assigned repair owner precede merge/release. No merge/deploy authority is provided by this coding workpack.

## 6. Engineering handover and change control

First instruction to the authorized C1 must contain: actual issue/workpack, exact scope and source head, selected coding protocol/label/plan, links to all three designs, original criteria, allowed files, protected boundaries, stop/handoff condition, reviewer and repair ownership readiness, and smallest unit S1. The agent must report actual plan/adoption before material work under applicable gates.

The Owner has explicitly designated this Codex conversation Coder for CoordinatorLandingpage implementation; no C1 ChatGPT launch is needed for this slice. Future separate coding conversations still require actual launch/registration authority. Do not reassign existing M2/M4 by assuming their old scope covers this new control project.

Subsequent source/head, target-generation, scope or form-contract changes have versioned impact/adoption records. Original request/decision/effect histories are preserved. Protected revisions require exact new authority; ordinary refreshed observation does not require redundant approval when an exact scoped grant remains valid.

## 7. Minimal end-to-end qualification

Office submits harmless status request -> correct project source recorded -> coordinator ACK -> scoped read/eligible agent task -> actual report/receipt -> independent evidence review -> GitHub RESULT and status trace.

Negative cases: same alias/different project; old binding generation; edited card/pre-fill; shared-account agent approval; replay/restart; crash after POST/Send; superseded STOP/decision; partial source scan; private marker leakage; old-head CI; missing mode/tab/Worked history. Unknown remains UNKNOWN; no reply/reaction is approval; registration and code counts are not outcomes.

No per-cycle reruns. Reuse applicable proof by exact body/head/profile; changed identity invalidates only relevant evidence. Backend's historical shim-only tests do not qualify full-runtime deployment.

## 8. Rollout and rollback

First release may expose forms as request capture only, clearly marked pending coordinator processing; no false automatic ACK. Retain ordinary inbox1 comments as fallback. Later adapters are dry-run/read-only first, then independently reviewed single-writer side-effect release. Preserve the existing15minute intake and root control pointer.

On unexpected effects, STOP the affected lane, reconcile attempts, preserve receipts and fall back to the known inbox. Rollback uses a new reviewed config/binding version; it does not resurrect an old generation or silently undo executed commands. Do not change repository visibility/permissions or install an App under this plan without the concrete Owner authority.

## 9. Current execution status

Implementation plan and first native forms/README slice prepared by the Owner-designated Codex Coder. Validation and draft-PR receipts are reported separately; live default-branch UI verification remains pending release. No new engineering agent launch or assignment is needed for this first slice. Current shared-account approval limitations and backend qualification remain separate later gates. No additional agent/timer/worker activated by this document.
