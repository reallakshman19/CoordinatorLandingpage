# Deployment selection amendment

Owner selected https://github.com/reallakshman19/CoordinatorLandingpage on15October2026. Repository observed PUBLIC; visibility not changed. This is the dedicated public coordination landing/inbox, restricted to sanitized content. The private-control and separate-identity recommendations below remain proposed, not installed; protected approvals retain their original checks. Canonical inbox: https://github.com/reallakshman19/CoordinatorLandingpage/issues/1.

# GitHub Coordinator Control Protocol — v1 proposal

Status: **PROPOSED / NOT ACTIVATED**. Prepared 15 October 2026, Dubai. Owner approved specification and review publication only. No repository, form, workflow, worker, agent, credential or permission is created by this proposal.

## 1. Outcome and operating conditions

The Owner works from an office laptop with GitHub and ordinary ChatGPT access, without access to this local Codex conversation. The Owner sends instructions and decisions through GitHub; a running home coordinator reads them, communicates with registered ChatGPT/Antigravity agents, and posts traceable responses back to GitHub.

The Owner need not paste routine instructions into agent conversations. Ad hoc direct ChatGPT instructions remain possible and must be reconciled before coordinator sends. This protocol does not provide remote desktop access or copy local browser sign-ins to the office.

Treat GitHub Pages access as optional: the whole initial system must work through normal github.com issues/forms regardless of whether a Pages site is available. An offline home coordinator cannot execute browser work; queued requests must remain visible without false ACK/execution claims.

## 2. Recommended architecture

Use one **private control repository** (proposed name `Coordinator-Control`, not created) as the Owner interface. Keep product code, agent work issues, PRs and test evidence in their own project repositories. The existing public Common#390 inbox is the transitional route, not proof that the private design is installed.

Four layers:

1. **Owner interface:** repository README landing page, Issue Forms, request threads and one cross-project status issue.
2. **Durable control:** project/agent registry, versioned plans, request/change/decision events, receipts and last published snapshots. GitHub is the durable source; a local indexed ledger/cache aids inexpensive intake and crash recovery.
3. **Coordinator execution:** one active coordinator epoch with project-scoped lanes, existing cadence, cost gates and writer/reviewer rules. It chooses eligible actions and communicates with existing mapped conversations through supported guarded transport.
4. **Engineering/evidence:** agents execute their assigned work, publish CASP-correlated reports and PR evidence, and stop at handoff. Independent review qualifies exact candidates. Project outcomes remain distinct from communication/testing counts.

One control repository avoids making the Owner visit every agent issue. One project record and one agent record per identity prevent authority crossing between projects. Issue Forms are the initial writable UI; GitHub Pages is an optional derived display, not the command database.

## 3. Two-project routing example

| Stable project ID | Product source | Control dashboard | Isolation |
|---|---|---|---|
| `dash-v2` | Common#360 and its registered agent issues/PRs | One project-status thread | Dash scope, aims, candidate, releases and writer/reviewer ownership |
| `aa3` | AA3 programme/issues and retained handover | Separate project-status thread | AA3 authority, original criteria, candidate/fixture/preparation identities and holds |

AA3 is an **example second registration, initially HOLD / observation-only**. Registering it does not revive its retired scheduler, writer, Antigravity assignment or old tests. Existing explicit prohibitions remain.

A form selects one project. A cross-project request creates separately tracked child requests; one project's failure does not imply the other is blocked or authorized. No all-project broadcast or agent sharing is inferred. Agent aliases such as M3 are always interpreted under a project ID, never globally.

## 4. Office-facing forms

The README provides links to these proposed forms:

| Form | Required Owner fields | Effect after validation |
|---|---|---|
| Ask / next task | Project, request text, optional agent/task | Read/report or coordinate eligible existing-scope work |
| Change instructions | Project, affected task/agent, requested change, superseded request if any | Versioned change assessment; affected action reconciled |
| Register existing successor | Project, old assignment/generation, existing chat URL, handover link, intended role, what Owner already typed/uploaded, requested permissions | Provisional successor; inspect/ground/adopt before activation; never create a duplicate chat |
| Add agent | Project, role, existing URL or explicit creation request, scope, issue/handover, intended writer/reviewer, allowed actions | Proposed registration or separately authorized launch, not automatic material release |
| Decision / approval | Decision-card ID/version, approve/reject/modify/defer, exact scope/limits/expiry, allowed attachments where applicable | Resolve only the referenced current card after verified Owner identity |
| Hold / resume / retire | Project and exact scope, action, reason | Precise control event; holds affect future permitted actions, not an imaginary rollback |
| Refresh page information | Project/agent and requested fields | Fresh authorized observation or honest unavailable result |

Forms create issues. Follow-ups can be comments in that request thread, or a new change form linked to it. Plain `FOR COORDINATOR:` comments remain a fallback; normal text is enough. No handwritten CASP/UUID required. Dropdown choices must be checked against the current registry, even if a form contains an old option.

New agent registration requests must distinguish **register an already-opened conversation**, **open an existing saved conversation view**, and **create a new conversation**. These are not the same permission.

## 5. Identity and authority — required before protected office approvals

Current tooling may publish as the same GitHub account as the Owner. That is insufficient to identify human approval from an unrecognized comment. The robust target separates identities:

- Owner signs in to GitHub as the Owner; allowlist the stable numeric account ID, not only the editable login string.
- Coordinator publishes using a dedicated GitHub App **installation identity**, or a separate restricted bot account. Do not use an App user token that makes posts appear as the Owner.
- ChatGPT/LA agents use separate agent identities or have their actual reports mechanically relayed with explicit attribution. They do not receive Owner credentials or control-repository administrative access.
- Protect identity/authority registry changes through Owner review. A comment, form checkbox or agent report cannot grant itself additional permissions.

Before protected commands can be approved exclusively from the office, establish the separate publisher identity and ensure human credentials are not shared with the agents/coordinator. Thereafter Owner-authored decisions in the control repository can be verified through authenticated GitHub actor metadata under the enrolled policy. This proposal does not itself install an App or grant access.

During transition, ordinary requests can guide work within existing authority. A shared-account message cannot silently authorize a new launch, upload, writer transfer, acceptance waiver, merge, deployment, security change or increased resource scope. Such decisions retain independently confirmed Owner authority. The earlier Owner override that private command destination is not a blocker remains respected; identity evidence and actual execution authority are separate questions.

## 6. Records and traceability

These are logical records, not yet implemented schemas. Reuse existing CASP fields rather than replacing its envelope incompatibly.

| Record | Essential fields |
|---|---|
| Project | Stable ID, repo numeric ID/name, parent issue, scope/aim revisions, control issue, active/HOLD state, source versions, budget/release policy |
| Agent assignment | Project/work/lane/assignment IDs, role, provider, agent issue, allowed paths/actions, plan, writer/reviewer ownership |
| Conversation binding | Binding ID, generation, exact URL/provider instance, observed mode, lifecycle, handover/adoption refs, coordinator epoch |
| Request | Repo/issue/comment ID, source body hash/version, authenticated actor ID, project/target, operation, text, authority refs, expiry, parent/supersedes |
| Change event | Old/new versions, requester, affected tasks/evidence, disposition, approval/adoption and activation refs |
| Decision card | ID/version, exact action, candidate/body/file hashes, limits, recipients, expiry, approving request, consumption result |
| Observation | Snapshot ID, binding/generation, capture time, capture method, status, fields and coverage, source versions, evidence refs |
| Delivery | Logical request, reservation, exact target, whole-message hash, actual user ID, end verification, state and attempts |
| Review | Exact report version, candidate/profile/fixture, original criteria, applicability, gaps and verdict |

Every ACK/RESULT/status/change points to the initiating request and exact observed versions. Comment IDs alone identify objects; hashes identify the body versions actually reviewed. Hashes establish content identity, not human authorship or product correctness.

Maintain an append-only **event history** in durable storage. GitHub comments themselves remain editable/deletable; retain original observed versions and record edits/deletions rather than calling the platform immutable. Public projections are allowlisted/redacted views of private control records, never the source of approval authority.

## 7. Request and delivery state machines

Request states: `OBSERVED → VALIDATED → ACKNOWLEDGED → ELIGIBLE/QUEUED → IN_PROGRESS → RESULT_REPORTED → REVIEWED → FULFILLED`.

Alternative states: `NEEDS_CLARIFICATION`, `BLOCKED`, `REJECTED`, `CANCELLED`, `EXPIRED`. A blocked action names prerequisite, responsible actor, allowed unblock and return condition. ACK means the coordinator read/reconciled the request, not that a browser message was delivered. A GitHub Actions intake receipt must be labeled intake-only, never a coordinator ACK.

Delivery is tracked separately: `PREPARED → RESERVED → SEND_ATTEMPTED → VERIFIED_DELIVERED / UNCERTAIN / NOT_SENT`. Evidence and acceptance have separate review states. Agent RESULT uses the pinned CASP `REPORTED/BLOCKED/FAILED` values; success-looking prose or workflow green does not bypass independent review.

Do not promise exactly-once network effects. Design for one actual effect per resolved attempt and conservative uncertainty: after a crash or timeout, inspect actual target IDs/body before any retry. Persist intent before a send/publication, verify afterward, and recover from both halves. A successful GitHub POST followed by a failed GET is publication-uncertain, not permission to publish again. Resume by finding the intended correlation marker/version and reconciling the actual object.

## 8. Coordinator cycle and token economy

Keep one existing 15-minute generic reminder; it chooses when to wake, not which historical task to repeat.

1. Restore current Owner controls, protocol version, active coordinator epoch and selected session role. Acquire the shared cycle lease.
2. Read compact control-inbox/project-source deltas. Use supported conditional/cursor reads where available; periodically perform complete reconciliation for edits/deletions. Process only new/changed bodies.
3. Take the Owner-required compact live STATUS/PAGE INFO batch for mapped lanes. GitHub silence never implies browser idle. Respect observation holds and redaction policy.
4. Reconcile human interventions, stale bindings, expiring decisions, unresolved deliveries and actual new reports. Review report alignment/proof through the aims ledger.
5. Build a fair project-scoped action queue: safety/stop/recovery first, then oldest eligible work. One project must not consume every cycle. Perform coordinator-owned unblocks, delegate engineering and preserve one-writer/independent-review gates.
6. Execute only actions with current authority, resource permission and fresh delivery guards. Current recurring approval covers bounded checks, not unlimited dispatch or engineering.
7. Publish changed status/ACK/RESULT; release lease in finally. Stable full tables can be linked rather than repeated in comments.

Local caches/indexes are accelerators; durable request identities/receipts are needed for successor recovery. Reuse candidate-specific CI/tests; do not rerun per cycle. Future model-step targets are estimates, not hard spending guarantees. Token-spike approval cards must be answerable in the authenticated office control channel once that identity policy is installed.

## 9. Change management

| Change | Required handling |
|---|---|
| Priority or next task within current role | Record change, reconcile current instructions, update queue; no invented role/writer transfer |
| Task scope, acceptance, fixture or authority | Identify affected original criteria and protected gates; obtain concrete authority before dependent action |
| New product commit | Refresh applicability; old proof remains historical; independent challenge applies to exact changed head/profile |
| Owner directly typed in agent chat | Capture changed actual user ID/body; reconcile before competing send; preserve generation and drafts |
| Successor URL supplied | Provisional binding only; verify actual route/mode/instructions, handover and adoption before activation |
| Extra agent | Explicit scope/launch or existing-chat registration; new assignment ID; declared writer/reviewer; no duplicate writer |
| Pause/cancel while running | Block pending affected actions, reconcile any in-flight side effect; do not claim execution stopped without proof |
| Roll back a binding/plan | New recorded change and current adoption; do not reuse an old generation or silently revive retired authority |

Activate a binding change under a transaction/fenced coordinator epoch; invalidate actions issued for the old binding. Reobserve before delivery. A race after final observation remains possible and is handled through actual receipt verification, not a claim of instantaneous control.

## 10. Actual M3 G2 → G3 case

The Owner has already supplied an existing M3 G3 URL. The current record is **OWNER_OPENED / PROPOSED_NOT_LIVE_VERIFIED_OR_ADOPTED**; do not create another G3. Keep M3 issue375 and its original independent-verifier aim/criteria; generation3 identifies the new conversation, not a new product acceptance.

Sequence: reconcile any instructions/files the Owner already supplied → verify regular ChatGPT High (never Work) → provide exact outgoing handover and available public source/test pointers under applicable authority → inspect actual G3 plan/adoption → activate generation3 → release its precise eligible independent verification unit. G2 remains stopped and receives no work. Reset only the new conversation's observed meters; retain G2 meters and evidence history. Do not claim zero usage where no observation exists.

An attachment approval must identify exact files and destination. Prefer already available, accessible source links; if the independent execution environment still cannot access actual file bytes, report that precise gap. A new chat alone does not solve the old runtime capability problem.

## 11. Agent interaction and LA support

Issue instruction → guarded actual conversation delivery → agent ACK/plan → execution → source/result → independent review → coordinator reply.

CASP correlation retains request/message IDs, full target and generation, expected revision/label hash, reply_to and request_digest, exact candidate/source/fixture/profile, authority and evidence references. Unsupported native message IDs stay null. A provider or GitHub connector being unavailable is not proof of delivery.

ChatGPT High can fill architect/coder/reviewer roles according to assignment. Antigravity LA is optional for bounded work with frozen inputs/oracles and distinct writer scope; no automatic LA launch in Dash. Support is provider-capability-specific: validated manual transport can be supervised, while unsupported automatic adapters stay disabled. If an agent cannot publish to GitHub, relay its actual report with attribution and actual limitations. Never synthesize an agent RESULT.

An engineering handoff stops its original coder. A separately authorized engineering successor owns repairs; Economy Coordinator does not take over. Independent reviewer remains separate. Merging/deployment require their own applicable authority.

## 12. Page information through GitHub

Yes: publish a **sanitized snapshot comment** in each private agent-status thread, and a compact aggregate in the project/cross-project status thread. Each snapshot has a stable ID and exact comment permalink. An example below describes the format only, not a live observation:

```text
COORDINATOR SNAPSHOT — EXAMPLE, NOT LIVE
Snapshot: <project>-<binding>-g<generation>-<UTC capture time>
Project / agent: dash-v2 / M3
Conversation: <registered URL; private control issue only>
Binding generation: 3
Captured at: <UTC> | <Dubai time>
Status: Processing / Waiting for input / Held / Completed / Error / Unknown
Reason: <observed reason; separate from task dependency>
Latest user/final: <actual IDs or UNKNOWN>
Body version: <complete-body SHA256 or UNKNOWN>
Draft: empty / present / UNKNOWN; never publish draft contents by default
Worked minutes / pages / completed turns: <values with lower-bound coverage>
Aim / plan: <exact IDs and revisions>
Candidate / CI: <exact head, applicable workflow links, conclusion and checked_at>
Claimed / reviewed: <separate counters and retained gaps>
Coordinator action: <planned versus actually executed; receipt link>
Owner action: <none or exact decision-card link>
Evidence: <request → delivery → result → review permalinks>
Freshness: <last capture and expected interval; age is recomputed when read>
```

Status vocabulary must be explicit: Processing, Waiting for input, Dependency-held, Owner-held, Handover ready, Stopped, Tab not open, Access/login required, Chat-length error, Provider/rate-limit error, Delivery uncertain, Unknown. Nonresponsive requires observed lack of progress under the bounded recovery protocol; it is not a synonym for idle/missing tab.

Loaded-page estimates and completed Worked labels are lower bounds, not actual model context/tokens. Record which final turns were counted; never count streaming parts twice. Keep capture time separate from publication time. Old snapshots visibly remain old; they cannot authorize a Send. Historical snapshots need append-only references; a convenience latest-status comment may be updated, but must link its underlying immutable-by-policy event version.

Do not post complete private transcripts, system prompts, raw drafts, credentials or unredacted screenshots to a public repo. Default public summary: alias, project, status, capture time, next actor, public evidence. Full allowlisted IDs/URLs/hashes belong in the private control channel. Screenshots are optional, purpose-specific and separately approved where required; the protocol does not grant blanket upload authority.

## 13. Trace a request end to end

Owner request issue/comment → coordinator ACK and parsed version → project/agent assignment → CASP request permalink → actual delivery receipt → agent ACK/plan/RESULT → exact commit/CI/test evidence → independent review → coordinator RESULT linked back to Owner request.

One click from the status row should open the request; another opens the evidence/review. Report a missing link as a gap. GitHub history is not a replacement for actual browser receipt proof.

## 14. Offline, restart and rate-limit behavior

- Publish last coordinator check and last **successful live observation** separately. A stale timestamp is evidence of staleness, not proof of the cause. No automatic “home computer offline” claim from silence.
- While the coordinator is unavailable, GitHub stores requests; no agent delivery or coordinator ACK is fabricated.
- On resume, acquire a new fenced epoch/lease, reconcile supersedes/expiry/holds, inspect pending actual side effects, then process eligible backlog. Never replay every old command indiscriminately.
- Keep future request expiry configurable; a default expiry is policy to select, not silently imposed on current pending commands. Expired approvals do not release work.
- Respect server retry/rate-limit indications with bounded restart-safe pacing. Preserve cursors and attempt receipts. No loops that repeatedly create comments or spam unchanged snapshots.
- All asleep/offline recovery must preserve the Owner's most recent stop. Two coordinators cannot own the same project lane concurrently; a local lease alone is insufficient if two machines operate independently. Before multi-host support, add one shared authoritative coordinator election/fencing mechanism.

## 15. GitHub-native UI versus a custom website

Recommended first: **README landing page + native Issue Forms + issue threads**, optionally a GitHub Projects board. GitHub hosts the editable form, authentication and discussion; no separate web application or office installation is required. Forms/templates must reach the repository's default branch before users can use them normally.

GitHub Pages is static hosting. It can later show a redacted status view and link to native forms, but it does not itself provide an authenticated command-processing backend. Never place a personal access token in page JavaScript. A custom writable dashboard would require an independently designed authenticated service and is outside this proposal's first release. Dash V2 can ultimately consume the same normalized snapshots; avoid building a competing product before the control protocol is qualified.

## 16. Optional Actions and wakeups

Phase1 retains polling, with a target of one cadence interval when the coordinator is available; not a guaranteed response SLA. GitHub Actions may later validate form structure, label/route requests and produce intake-only receipts from issues/issue_comment/workflow_dispatch events.

Actions cannot be claimed to wake this Codex conversation until an actual supported wake adapter is installed and demonstrated. A green workflow or repository_dispatch event is not itself a Codex wake. Actions must not evaluate comment text as shell, run untrusted request code, possess Owner browser credentials, automatically merge/deploy, or generate product acceptance. Existing workflows and old draft PR362/364 remain untouched.

## 17. Phased implementation plan

| Phase | Deliverable | Acceptance gate |
|---|---|---|
| A — current bridge | Common390 + existing reminder + actual request/ACK/RESULT tracing | One harmless Owner request from office GitHub completes end-to-end; current protected identity limits explicit |
| B — private control and identity | Owner-selected private repo, distinct bot/App identity, project/agent registry and native forms | Owner and bot authors distinguishable; project routing and protected approvals tested; no new writer/agent implied |
| C — two-project coordinator intake | Durable request/change/decision ledger, project isolation, dedupe/restart and fair queue | Dash + AA3 test cases; AA3 remains HOLD until explicit activation; cross-project/old-generation rejection |
| D — page information and handovers | Allowlisted snapshot publisher, permalink trace, stale handling, successor/add-agent workflow | Actual mapped snapshots; truthful UNKNOWN; Owner-opened successor adopted once with no duplicate creation/send |
| E — optional wake/display | Demonstrated wake adapter and/or redacted Pages/Projects view | Wake measured end-to-end; no browser token exposure; optional component may remain absent |

Implementation belongs to an expressly authorized separate engineering agent. Coordinator grounds it with this specification, selected repo/identity, allowed paths and exact tests; it does not implement the tooling in Economy Coordinator mode. Handoff/repair/independent verification follow the existing Owner rules. Phase acceptance does not accept Dash or AA3 product outcomes.

## 18. Discriminating qualification matrix

Required before robust activation:

1. Owner request from office GitHub produces correlated ACK and actual RESULT.
2. Same alias in two projects routes to the right work/repo/conversation.
3. Duplicate polling and restart do not duplicate publication or agent Send.
4. Crash before/after publication and before/after Send recovers with honest uncertainty.
5. Edited/deleted/superseded requests preserve versions and block stale actions.
6. Unauthorized actor and agent-authored “Owner approval” cannot release protected work.
7. Genuine Owner decision matches exact current card/body/files/recipient and is consumed only for its scope.
8. Owner-opened successor registers once; old generation receives no task; independent criteria/history retained.
9. Added coder cannot overlap an existing material writer; verifier is independently owned.
10. Unknown tab/mode/history stays UNKNOWN; generation gets no ordinary nudge; Owner draft is protected.
11. Unavailable provider adapter cannot emit a fabricated native PASS.
12. Snapshot capture/publication age is explicit; repeated final labels do not inflate meters.
13. Raw private content never enters public projections; source hashes do not substitute for execution.
14. STOP racing with an in-flight request is reconciled, with no false undo/stop claim.
15. Offline backlog, expiry and rate limits preserve holds and bounded retry behavior.
16. Token approval and handover decisions can be submitted from the enrolled office identity without Codex IDE access.
17. Actions intake success is distinguishable from actual coordinator wake and agent execution.
18. Source CI is tied to actual head/profile; evidence reuse does not advance unrelated product acceptance.

These are proposed tests/oracles, not executed PASS results.

## 19. Owner choices before implementation

Select the private repository name/visibility and publisher identity; confirm the second project's permitted scope (AA3 can start observation-only); select routine snapshot cadence/visibility and any broader bounded coordinator-action budget. Then authorize one appropriately grounded engineering implementation task. Repo/App installation, security access, new agents, workflows and uploads remain separate concrete permissions where applicable.

Current planning approval only permits this document and its review publication. Existing15minute checks and Common390 remain operational as previously registered. M3G3 is recorded as Owner-opened, not activated by this proposal. No whole protocol is certified from a document review.

## Primary documentation

- [GitHub issue forms and templates](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/about-issue-and-pull-request-templates): native form fields and default-branch availability.
- [GitHub Pages](https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages): static hosting; the architecture's writable backend requirement is an engineering inference from that model.
- [Workflow trigger events](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows): issues/comments and dispatch event support, distinct from a demonstrated local Codex wake.
- [GitHub App authentication](https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/about-authentication-with-a-github-app): installation attribution versus acting on behalf of a user; the proposed identity separation uses installation identity.
