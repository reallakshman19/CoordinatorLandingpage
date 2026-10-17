# Team protocol v3.1 — CoordinatorLandingpage

Status: **v3.1 ADOPTED** (17 Oct 2026; v3.0 + the A13/A14 amendment: Owner "add A13 + A14 to P3 and team protocol", [#1 6230407705](https://github.com/reallakshman19/CoordinatorLandingpage/issues/1#issuecomment-6230407705); wording = Codex Q12 [Common #409 6230450337](https://github.com/reallakshman19/Common/issues/409#issuecomment-6230450337)).

> (v3.0) Status: **v3.0 ADOPTED** (17 Oct 2026; Owner "with D3 … go ahead", [#1 6230015272](https://github.com/reallakshman19/CoordinatorLandingpage/issues/1#issuecomment-6230015272); text = draft r2 of PR #59 incl. OTM differences D1–D3).

**What changed from v2.3:** Part A states the rules in force. Part B maps every v2.3 section (KEEP / REVISE). The v2.3 text is kept below as a historical appendix, struck through where superseded and **not deleted** (Owner: "Scrap all the old modes, do not delete, mark like comment"). Permission still comes only from recorded Owner decisions. Adopting this protocol starts no project, agent or work by itself (Part C).

**Start here as a new agent:** your project's root issue "START HERE" comment → its brief (e.g. `docs/LANDING_LIVE_BRIEF.md`) → your project's `logs/<project>/registry.json` → Part A here → your native evidence format (A6). Known issues: `docs/KNOWN_ISSUES.md`.

---

## Part A — Rules (v3.0, adopted)

### A1. Roles


The project's current Owner-recorded role assignment and CONTROL epoch govern. For landing-live, Claude is one combined OTM/TC actor and the sole chat deliverer; Codex is planner/reviewer, publishes on GitHub and does not send to chats or use browser delivery. Combining OTM and TC does not create a second approver or an independent verifier. A later expressly scoped Owner authoring assignment must be recorded; it does not enable self-review or self-acceptance.

Agents perform only their assigned authorized work under exclusive custody. A checker is a different qualified actor from the author for the assessed work, reviews one frozen target and records the exact proof and limits. Freshness/independence requirements follow the applicable Owner-approved review contract; an earlier PASS is not reused for changed material. A role label, a fresh model invocation or this table neither proves independence nor grants a new-agent/helper launch.

Scripts observe/project only; helpers advise only. Keep necessary source review bounded and cached, but do not prohibit reading the evidence needed for a decision. All shared-account role labels are attributed claims, not authentication.


### A2. Authority


For every action use the project's existing authority map: actual deciding actor and Owner record, target/project, permitted action and paths, conditions, lifetime/counter, and revocation/stop conditions. Classification, plan membership, auto_response alone, START, PASS, schema completion, clock tick or protocol installation cannot substitute for that grant.

On a normal project, OTM may approve only actions covered by the actual unexpired Owner delegation and accepted scope. Label combined TC/OTM approval/self-approval with its basis in #1 and obtain non-doer verification where required. Critical or unset projects require Owner approval, except a specifically recorded standing exception. The critical H1–H3 BuddyRunner v1.7 exception is eligibility-only: actual trigger, no HOLD, registered successor and unchanged scope; it grants no general critical approval or authority for a different handover method. Nudges and assumption-free clarifications must likewise stay inside their recorded scope.

Protected decisions require the applicable explicit Owner record: acceptance, release, rights/publication, private-input upload/custody, purchases, new chats outside an authorized standby scope, widened work, writer/role/control changes, and merge outside a scoped merge grant. Do not infer a new blanket delegation or erase a historical acceptance record's actual limited scope.

Done, verified and accepted are different. The doer may report execution and self-tests, but is not its own independent verifier or acceptance authority. A performed action with failed readback is done/not verified, with its effect UNKNOWN—not proved absent.

Permission to observe is separate from permission to work. HOLD/expiry blocks new work; only a still-valid separate observation grant permits watching. HOLD lift does not renew expiry or reset a count. Preserve three independent counters: UEM 1–5 per stable work unit (pilot 1), Next Move evidence-cycle checkpoints at n mod 20 in {5,10,15,19}, and Owner delegation allowances. Scheduler ticks, handover, restart and rename reset none.


### A3. Owner words


Record each material Owner instruction once in #1, in the same authorized activity, with exact words, attributable source, actual clock or explicitly unknown/ranged time, scope and supersession. Reconcile a later instruction against the earlier one; do not silently broaden an unrelated project's permission.

Keep private inputs, full private chat identifiers/URLs, credentials and private transcripts out of a public repository. Use public id8 references and an approved protected source/digest or sanitized quotation where necessary; retain the exact private source only in its authorized custody.

Distinguish direct Owner input, an attributed Owner-word record and an agent's unconfirmed interpretation. The Owner-input form or an Owner decision comment is a source channel, not an authentication guarantee under a shared account. Neither a role prefix nor a self-referential link proves who decided. Preserve already valid scoped records with their provenance limits; seek precise clarification for a material untraceable or contradictory approval, not a routine human re-post of every settled instruction. Tag an OTM transcription as OTM evidence, not as a human-authenticated [OWNER] post.


### A4. HOLD


HOLD immediately stops new work and dispatch in its actual scope. Record #1 and the structured registry hold with source, scope, lifetime/lift condition and prior value. Owner-requested read-only analysis/record fixes remain allowed; watching continues only under a separate explicit observation grant. Current stopped watchers do not restart because this document is adopted.

The sole authorized deliverer must convey an agent HOLD into that agent's own chat using the supported guarded route. Reconcile pending sends and Owner intervention first; preserve drafts and active generation. A Stop/interrupt control is used only where the actual authority and supported safety guard permit it, never as an automatic consequence of this sentence.

Record SENT_TO_CHAT with actual receipt when verified. If not sent or uncertain, preserve NOT_SENT/DELIVERY_UNCERTAIN and alert the Owner with the exact delivery gap; do not infer the agent stopped, blindly resend, or lift HOLD to make delivery easier. Only Owner words lift an Owner HOLD. A previously held move returns to its applicable published state and needs fresh approval; expired grants, custody and counters remain unchanged.


### A5. The coordination loop


First reconcile Owner amendments, the authoritative registry/control epoch, pending receipts and open Owner questions. Use one complete scoped GitHub metadata delta, then only new/edited relevant bodies, cached by provider ID, edit/body digest and candidate/source. Retain a source manifest, completeness/gap and last-success cursor. Source failure or incomplete pagination means UNKNOWN and does not advance successful freshness.

At assignment or material change, ground the actual actor in Project → AIM → task, current Owner amendments, source/input identity, benchmark/golden-fixture identity, done-when, role/custody and non-goals. Reuse an already qualified native investigation; do not add another handover round.

Use one authorized watcher. Event/due/health sensing is a proposed optimization until its actual event-to-coordinator wake path, silence/deadline behavior and failure reporting are qualified. It does not silently replace a selected cadence, resume a stopped watcher or establish “quiet means zero model cost.” No agent timers by default; an exception needs actual Owner words and created/fired-once/cancelled proof.

Helpers are optional and require applicable launch/capability authority. A capability request names the required operator, source, bounded operation, expected evidence, privacy boundary and stop/return condition; ownership stays with the assigned runner. A tool limitation is not permission for another agent, public upload or architecture rewrite. Respect existing agent/slot/resource limits.

Choose the smallest eligible useful step after checking grant, HOLD, exact current basis, dependency, custody and stage prerequisites. Prefer reuse/minimal adaptation or KEEP/NO_CHANGE. For an improvement state benefit, alternative, owner, effort/risk and falsifier; park medium/low-ROI ideas rather than silently adding them to the task.

For delivery, reuse the complete applicable native Next Move claim/approval/publication contract, not a shortened parallel ledger. Validate approval and current basis; claim with a conflict-safe identity/expiry and recipient fence before sending. Recheck control, HOLD, Owner intervention, draft/generation and pending uncertainty. Record SEND_INTENT and the actual NOT_SENT / SENT_TO_CHAT / DELIVERY_UNCERTAIN outcome, then actual attributed PICKED_UP where observed. Expiry, rename and retry do not clear uncertainty. Publication or END alone is not delivery, pickup, GO or acceptance.

For every open item retain next actor, concrete next action, expected return/due event and blocking prerequisite. Write an incremental checkpoint before a wait/exit, not just at task completion. Update maintained registry/status projections with minimal conflict-safe writes and readback; they are separate writes, so expose a partial failure instead of claiming atomic success. Append material authority/delivery/decision receipts once.

Keep Owner questions durably OPEN, ANSWERED, ACTION_PENDING, explicitly deferred or superseded with source/reason. An acknowledgement is not an answer. Every Owner decision request includes recommendation, reasoning, exact scope, risk/urgency and who is blocked. Escalate new impact or a due deadline without repeating unchanged alerts.

Unknown/silent/inaccessible is not idle, dead or stopped. Use finite supported liveness/recovery; settle pending deliveries first, preserve failed capability observations and name the next actor. Keep status rows distinct for work, authority, monitoring and evidence age. Post changed coordinator evidence only; no green from START, timers or bookkeeping.


**OTM reconciliation D3 (a measured threshold, a proposal):** the coordinator session's cost per step follows its context size (measured 17 Oct over 1,838 steps: ~30k effective tokens per step at ~230k context vs ~88k at ~830k). Proposed trigger: compact or restart from the recovery records above ~400k context, not on a timer.

### A6. Evidence


Preserve each project's native reporting contract and pinned version: Team TASK EVIDENCE v2 / STATUS v2; Engineering v3.6's canonical TASK_EVIDENCE block plus mandatory terminal LOG; the selected native handover phase records separately. A future continuity sidecar is linked outside the native block, never another completion receipt or extra handover phase.

DONE, PARTIAL, BLOCKED and FAILED report honestly. Use STATUS/checkpoints when no task has finished; NOT_RUN and NOT_POSTED are explicit, not fabricated passing tests or publication. Where required, publish the same source-bound block in the reply and the agent's own issue, or make an unchanged attributed relay with its actual publication limit.

Keep input provenance (ORIGINAL/SYNTHETIC/PARTIAL/NONE), verification scope (STRUCTURAL/BEHAVIOURAL), and acceptance source separate. Bind claims to actual candidate/source/fixtures, commands/environment, outcome, independent role where applicable, falsifier and not-proven limits. Preserve original-input custody and complete golden-fixture boundaries.

Assess separately: readable record, sufficient evidence for the stated claim, and eligibility for the proposed action. UNKNOWN never satisfies authority, custody, source or acceptance.

Proof requirements are stage-appropriate: a read-only review does not require future implementation CI. Applicable engineering/review/hosted-CI claims identify the exact assessed SHA and actual run; authorized local evidence states its route and limitations. A moved head invalidates affected claims of current qualification, while the prior run remains historical evidence. Do not call it baseline-red without same-check/base proof or treat a passing check as academic/product acceptance.


### A6.1 Coding practice (P3 A13, added in v3.1)

**A13 — coding practice within authorized scope.** New authored source/test files and materially changed source/test files must satisfy the 300-line file limit. An existing file already over 300 lines must not grow; when materially touched it is split along a coherent responsibility boundary as part of that authorized change. Unrelated oversized files are not a mandate for a big-bang rewrite. If the necessary split crosses allowed paths or changes an interface/scope beyond the grant, report that precise prerequisite; do not perform the wider refactor or claim compliance.

Use one documented, deterministic size basis: physical file lines, including blank/comment lines, at the exact comparison base and candidate; report each changed file's before/after count. Identify the authored source/test file set and any generated/vendor/data exclusions explicitly. An exclusion is a scope rule to justify, not a loophole for hiding authored logic. Do not compress statements, delete useful explanation or scatter coupled code merely to pass a number.

Functions should normally be approximately 50 lines or fewer, using a documented language-aware span measurement. A deviation is recorded with its reason and reviewed for cohesion; an approximate target does not silently become a hard universal parser gate.

Keep one coherent responsibility per module, reuse established modules, and avoid duplicate engines/parallel implementations of the same responsibility. The required independent reviewer assesses these properties and any claimed deviation; line counts alone do not establish them.

Changed behavior has applicable tests, including changed failure boundaries where relevant. Report the actual tested source, commands/environment, results, failures/skips and NOT_RUN reasons. Scope-preserving structural changes still need appropriate regression evidence. A read-only or blocked task uses its own stage-appropriate criteria, not invented future implementation tests.

Mechanical checks may verify size measurements and explicit ratchet violations; they do not judge understanding, architecture, benefit, correctness or acceptance. New workflow changes or widening shared paths require their own applicable authority.

### A6.2 Pre-claim self-check (P3 A14, added in v3.1)

**A14 — self-check and issue reconciliation before a task claim.** Before a new DONE, PARTIAL or BLOCKED claim, publish one source-bound SELF-CHECK v1 companion on the task's actual evidence issue. Use the real stable task ID, governing plan/criteria revision, issue and assessed candidate/source. Where the native task has no candidate or accessible source yet, state UNKNOWN/NOT_AVAILABLE and identify the resolver; never invent an identity.

Reconcile each applicable done-when item for the current authorized task/stage against actual proof, the planned/changed scope, A13 where applicable, actual tests, the issue checklist and every known unresolved task obligation. Mark MET only when the cited proof supports that criterion; otherwise use NOT_MET, NOT_RUN or UNKNOWN with its limit. NOT_APPLICABLE requires an explicit stage/scope basis and cannot waive an unmet criterion.

List pending items with their stable existing task/issue reference where one exists, responsible actor, smallest next action, dependency/unblock condition and whether they prevent this task's done-when. Unknown ownership is reported UNKNOWN and routed, not invented. This is reconciliation of existing work, not another task-number/counter scheme.

DONE is supportable only when all applicable task done-when criteria are MET, no unresolved obligation needed for that task remains, and the scope/required checks are satisfied. Separate future work may remain open if genuinely outside the approved unit; retain its source/owner and limits. Do not shrink criteria, rename the unit or move pending work merely to obtain DONE. PARTIAL/BLOCKED reports remain honest when evidence or capability is missing.

A self-check is the author's report, not independent verification, approval, release or Owner acceptance. The coordinator assesses its applicability/sufficiency against the real issue, plan, source and authority. Missing or stale self-check means the new completion claim is unqualified; it does not erase material work, prove a failure, or prohibit reporting a blocker.

Keep native evidence/LOG unchanged. The self-check is linked supporting context, earns no native evidence/progress/acceptance credit by itself, and creates no new lifecycle/phase. Corrections append with the replaced companion's reference; changed plan/candidate/proof invalidates affected current claims while preserving history.

The coordinator reconciles pending facts into the existing issue/control/status records, keeping actual ownership, next action and unresolved decisions visible. Use Next Move only where the project's real opt-in and authority permit it. A pending row or “next” instruction is neither dispatch nor permission to work. Do not tick issues, expand scope or approve work merely from the self-check.

**OTM extension (labelled, not Owner wording):** the same self-check also applies before a FAILED claim.

**Team-protocol integration (Codex Q12 §5):**

Where this Owner-adopted amendment applies, perform A13 and publish the A14 SELF-CHECK companion before a new DONE/PARTIAL/BLOCKED claim. Publish the companion on the existing registered evidence issue, then reference its actual permalink through an existing TASK EVIDENCE v2 Proof line, graded CLAIM-ONLY for the author's self-assessment. Actual test/readback proof keeps its own true grade. Preserve every existing field, task status, STATUS v2 rule, NOT_POSTED relay and evidence-publication requirement.

Do not add another mandatory terminal section, repeat the entire self-check inside the task block, or introduce a competing completion count. The same native block still appears in the agent reply and evidence issue. A linked companion establishes that an assessment was recorded, not that the task passed independent verification or was accepted.

If publication is unavailable, show the actual NOT_POSTED limit and follow the existing unchanged attributed-relay rule. Do not claim the self-check was published or the completion gate qualified without actual readback. Urgent blocker/unsafe-work/Owner-intervention reporting is never withheld pending a form or unavailable tool; stop affected work as required and report the missing assessment honestly.

Reconcile pending items in existing issue/control records; invoke Next Move only under its actual pilot/authority. Self-checks do not grant authority, clear HOLD, renew allowances, reset task-cycle counters or activate a watcher.

**Companion template** (plain text; not a completion receipt):

```text
SELF-CHECK v1 · <stable task ID> · <own evidence issue>
Basis: plan/criteria <source + revision>; candidate <repo@sha or UNKNOWN with reason>; source/fixtures <refs or limits>
Done-when: <criterion> → MET <proof> | NOT_MET <gap> | NOT_RUN <why> | UNKNOWN <missing source>
Scope: approved <paths/ref>; actual changed <paths>; extras <none or grant/gap>
A13: applicable <yes/no + basis>; files <before→after/count source>; legacy split <result/gap>
A13 review: function-span findings <refs>; cohesion/reuse/duplicates <author's assessment + limits>
Tests: <command/environment> @ <tested sha> → <actual result>; failures/skips/NOT_RUN <limits>
Issue reconciliation: <criterion/checklist ref> → <actual proof or mismatch>
Pending: <existing ref or descriptive item> · owner <actor/UNKNOWN> · next <action> · unblocks <event> · prevents task DONE <yes/no + basis>
Proposed claim: DONE | PARTIAL | BLOCKED · reason/limits <text>
Native report: <permalink when published, or PENDING/NOT_POSTED with reason>
```

### A7. Continuity


Maintain one root Owner-intent issue with START HERE links to the brief, causal history, authority map and route map. These are projections over cited sources, not another authority ledger. Preserve original intent, later amendments, what each predecessor contributed and why, known failures, unfinished actions, current source/benchmark, next actor and alternatives/rejected or parked ideas with reasons and revisit conditions.

Mark superseded items with the struck-through chain, reason and replacement link. A 404 is availability-unverified, not proof of deletion. A material Owner/source/fixture/grant change invalidates dependent current conclusions immediately; keep prior history and expose which dependencies are stale.

Correct published evidence, decisions and native phase claims by attributed append-only correction. Maintained registry/status/brief/index projections may be edited from current bytes with conflict detection, minimal diff, source/version history and readback. This is not permission to erase an inconvenient receipt.

Accounting is not proof. Show UNKNOWN and evidence age; START or a filled status row cannot turn work green. A continuity test asks a non-author cold reader the Owner's ten reasoning questions from the root entry point. Keep test material off that entry point, but record actual exposure through other reachable comments/API; a separate issue or minimized comment does not prove blindness.


### A8. Succession


Use the project's governing Handover Master selection and exact native BuddyRunner version/contract. A selector/native mismatch is an explicit gate or reported defect, not permission to bypass it or globally upgrade closed handovers.

Prepare one standby only under the actual scoped launch/standby grant. Use the recorded self-reported warning trigger or actual chat-end signal (maximum-length, or repeated supported “Could not load” observations under the applicable rule). Do not invent a meter or a new 80% threshold. Slowness, length or one failed/unsupported read prompts bounded triage and UNKNOWN, not automatic launch or retirement.

While G1 is alive, complete native H1/1a preparation and H2/1b investigation once, with no product coding. OTM qualifies the incoming instance's own-words/source-bound 1b against the selected contract before placing it on HOLD. A generated packet or mere publication is not qualified adoption. A supplied 1b is usable only where that native contract permits it and with actual provenance.

Preserve the native final phase: G1 supplies phase 2 final direction and the required twelve-section handover, then closes; G2 does not add a phase-2 acknowledgement or another round. If G1 cannot write 1a or 2, the authorized coordinator may act as G1 from cited GitHub records, marking inherited unverified claims as hypotheses. This is not independent technical verification. Closure requires the actual owning-issue publication, not renderer output; duplicate handover/intervention keys require receipt verification, not regeneration.

Activate only after actual outgoing cessation, settled/fenced pending sends, qualified incoming investigation/adoption, and exclusive custody plus valid work/control authority with no HOLD. Record retirement/activation and remap every affected lease/grant to the successor's actual branch/PR in the same eligible transition, from the confirmed frozen source. Do not renew scope/lifetime, reset any counter or infer an inaccessible chat is dead. No authority means prepare/route the precise missing decision, not launch another runner.


**OTM reconciliation D1 (Owner record, not an invented threshold):** the Owner's standby rule ([#1 6229973054](https://github.com/reallakshman19/CoordinatorLandingpage/issues/1#issuecomment-6229973054): "we should always have an agent based on our handover meter … facilitate continuity"; "HOLDED only after he is on board") is the scoped standby grant. **Meter warning = 80% of the recorded meter budget, where a meter is actually measured;** where no meter exists (K18), only a self-reported warning or a real chat-end sign triggers it. Slowness alone triggers triage, not a launch.

### A9. Records hygiene


Use real clock times; label an unavailable time as unknown or a range and never pass “04:1x” as a valid machine timestamp. Correct a wrong published time by an attributed replacement receipt.

Edit registry/docs from current repository bytes, preserve line endings, check the minimal diff and conflict basis before publishing, and verify actual readback.

Read complete paginated issue comments through the supported API rather than a stale/truncated issue view. On incomplete/error results retain UNKNOWN and the last successful cursor.

Keep known issues with source, owner, status and remaining proof. Distinguish a proposed mitigation, adopted rule, implemented fix and independently verified repair. None creates implementation authority.


### A10. Codex desk


Process the Owner-authorized FOR Codex queue oldest first against current registries and named sources. Post on the named issue with three plain lines: VERDICT, NEXT, DELIVER TO; then evidence, recommendation, reasoning and limits. Verify publication, then post the single FOR TeamCoordinator delivery pointer or DONE-for-Owner receipt in #1. Stop when the queue is empty.

Claude alone delivers chat-bound outputs under current permission and records actual delivery proof or NOT_SENT/DELIVERY_UNCERTAIN; pickup is a further fact, not inferred from posting. Do not collapse uncertainty into “not delivered” and resend. Codex makes no chat sends/browser delivery, creates no private work counters or HOLDs, and derives no new engineering, launch or acceptance authority from a queued item.

Audit approvals relevant to the current request and changed scoped authority evidence. A broader recurring audit requires its own explicit scope; a growing queue does not authorize Codex timers. Queue-age/status display is a proposed projection until implemented and source/readback verified, not a service already guaranteed by this rule.


**OTM reconciliation D2:** for **pilot/test** projects, each Codex desk run includes an audit of OTM approvals since the last audit (Owner, "For Pilot/Test , think of more cycle", [#1 6229973054](https://github.com/reallakshman19/CoordinatorLandingpage/issues/1#issuecomment-6229973054)). Other projects: audits only as requested.

---

## Part B — Reconciliation of every v2.3 section (Codex Q9, adopted)


“KEEP” must preserve the operative rule, not only its heading. State precedence explicitly: project Owner records and the gated native pilot may supersede a legacy clause only in their actual scope; a global v3 draft does not silently export landing's exceptions.

| Baseline section | Required disposition/correction |
|---|---|
| §1 Roles | REVISE current named roles; retain one active controller, CONTROL epoch and old-controller stop/fencing. Do not strike bootstrap mechanics merely because current TC/OTM is one actor. |
| §2 Places | REVISE, not unqualified KEEP: retain canonical registry, Owner-input/decision route, single current status and per-agent evidence issue; reconcile old “all raw transcripts” language with private-input/public-repo limits. A GitHub outage does not override the current no-chat/no-browser role or justify public private-data fallback. |
| §3 Evidence | KEEP native fields, all four task outcomes, STATUS when unfinished, same-block publication/NOT_POSTED and attributed correction; retain falsifier, proof roles and recommendation. R6 adds no competing schema. |
| §4 Coordinator evidence | KEEP with clearer material-change definition. “Only on change” already exists; retain the edited current status plus appended material sends/epoch/Owner-decision receipts. |
| §5 Cycles | Deliberate REVISE proposal, not an already-proved supersession. Preserve due/liveness/health obligations and separately scoped watch authority; qualify the wake path and obtain the actual cadence change. Do not revive the stopped watcher. |
| §6 Grounding | KEEP gap-specific intent/source/benchmark/claim review and meaningful ALIGNED/CORRECTED/ESCALATE judgment, not CI scoring. Put assignment/material-change grounding explicitly in R5; the current A7 reference alone does not supply it. |
| §6b FOR TeamCoordinator | REVISE to add the Codex route, but retain the existing instruction/receipt meanings (RELAY/CORRECTION/ROUTE/STATUS/BREACH/GATE), identity and protected-action limits. Preserve distinct uncertain delivery. |
| §7 Authority | REVISE to trace actual per-project grants, protected boundaries and expiry. Do not carry historical Grade9 grants into current landing authority or treat normal classification as permission. |
| §8 Guards/fallback/takeover | REVISE for a single current actor while preserving finite recovery, UNKNOWN, pending-send fencing, outage escalation and authorized controller replacement/epoch. Outage risk does not vanish when the roles combine. |
| §9 Handover/new agents | REVISE explicitly: the legacy “one-step” description must not conflict with selected 1a → 1b → 2 native phases and gated pilot policy. Preserve actual launch approval, qualification and no extra rounds. |
| §10 Onboarding | REVISE the obsolete literal “Team protocol v1” instruction to the actual governing pin. Retain per-instance own-words adoption and usable evidence/publication capability; do not fabricate a finished task block for a read-only setup check. |
| §11 Economy | REVISE with supported measurements, existing resource approvals and bounded necessary reading. The draft mentions a “context-size rule” but defines no threshold/source; do not invent one. Helpers are neither automatically authorized nor evidence of token savings. |
| §13 Workflow card | KEEP the full Owner-visible loop, source/authority, current and previous text, and guarded notice/readback—not just a mutable current string. There is no §12 in this baseline; do not invent a missing rule. |
| §14 Changeover | KEEP actual stop/frozen head, full native handover, successor branch, adoption/grounding and role/custody remap before writes. Restore both surrogate-G1 phases and unchanged work limits. |
| §15 Drift | KEEP: detect departures from the actual AIM/source/benchmark and analysis-only loops; choose a bounded correction or escalation. A drift finding does not authorize redesign or a scope expansion. |
| §16 Ambiguity | KEEP: resolve material count/role/scope ambiguity with a precise recommended decision; do not repeatedly re-ask a settled grant. |
| §17 Bootstrap | KEEP its observe-only start, Owner CONTROL epoch and prior-controller cessation. This directly conflicts with Part B §1 striking “observe-only candidate TC”; remove that contradiction, not the safety mechanism. |
| §18 Open Owner decisions | REVISE only with an explicit Owner disposition. A draft author cannot silently replace the pending v2.3-freeze decision with v3 adoption. Watchdog remains OPEN/not activated; proposed sensing must not be presented as that qualified workflow. |
| §19.1–§19.22 | Replace the blanket KEEP assertion with the individual preservation/revision table below. Several legacy empirical absolutes need explicit proposed correction rather than being both “KEEP” and contradicted. |
| §20 Next Move | KEEP its actual landing-only pilot gate, approval tiers, native claim/receipt states, uncertainty, qualified phases and task-cycle evaluator. Do not export the pilot by merely referencing its states elsewhere. |
| UEM | PARKED, no live activation. Preserve the one-watcher/no-agent-timer policy and three counters, but do not activate UEM START/END/cycle behavior where the registry lacks actual Owner opt-in. |

### Every stress-test rule, individually

| v2.3 rule | Disposition and invariant to preserve |
|---|---|
| §19.1 | KEEP explicit per-project OTM appointment/authority before a relay counts; cite the actual record even if a historical registry uses a different field layout. Normal criticality alone is insufficient. |
| §19.2 | KEEP exact Owner words/time/source and named supersession in the same authorized activity; add privacy/attribution limits from R3. Do not fabricate a precise minute. |
| §19.3 | KEEP exact exclusive path/branch/holder grants. Record outside writes; do not build on them or count them as approved until the required different checker review. A human account name is not an instance lease. |
| §19.4 | KEEP a different agent qualifying a changed validator/audit/harness at the exact commit before its generated result certifies anything. No self-certifying checker change. |
| §19.5 | REVISE the causal absolute explicitly: same-check/base evidence is required to claim baseline-red; without it responsibility remains with the assigned agent to investigate, but causation is UNATTRIBUTED—not proven to be its regression merely by absence of base evidence. |
| §19.6 | KEEP an exact Owner out-of-allowlist grant, specified paths/generator output, frozen target and checker PASS. R2 must not make plan membership substitute for this. |
| §19.7 | KEEP approved manual/gated run initiated by a different actor from the graded agent, once on the approved/checker-qualified exact SHA, with actual run receipt. No self-dispatch or arbitrary CI rerun from a protocol review. |
| §19.8 | KEEP privacy, authorized custody, actual hashes and truthful runtime limits. REVISE the historical blanket “sandboxes cannot clone / lose files” into observed route capability; do not prohibit a newly authorized capable runtime or claim one exists. Private upload/runtime changes still need their actual authority. |
| §19.9 | KEEP own-lane non-blocked Next nudges only when current permission, adoption, dependency and HOLD gates allow. “Waiting” does not authorize more work by itself. |
| §19.10 | KEEP real clocks and an explicit correction receipt naming the replaced time; ranged/unknown times remain honest, not machine-valid timestamps. |
| §19.11 | KEEP milestone freeze, real count verification and one scoped Owner acceptance card including open limits. No completion, checker or coordinator claim becomes acceptance. |
| §19.12 | KEEP liveness, due/silence/health guards and #1/registry notice when stepping back. REVISE timer implementation only under the authorized single-watcher policy and qualified wake path; do not erase outage protection or resume monitoring during the present operational HOLD. |
| §19.13 | KEEP draft-PR/exact-SHA CI and review for frozen engineering commits where that phase requires them. Clarify stage scope: a read-only decision paper or BLOCKED preflight is not refused because future implementation CI does not exist. |
| §19.14 | KEEP source/generator repair and regenerated mirrors; no hand-editing output to conceal the source defect. |
| §19.15 | KEEP fail-closed wrappers, the actual sanitized child error and a tested failure path. No swallowed failures reported as success. |
| §19.16 | KEEP no borrowed approval/review: role's own attributable post or explicit correction. Shared-account identity remains an acknowledged limit. |
| §19.17 | KEEP different-checker review plus a real failing negative control when a check is weakened. Passing output alone does not validate the new oracle. |
| §19.18 | REVISE only through the exact project/native standby grant: real chat-end trigger, qualified investigation/grounding, actual stop and custody before activation. Do not replace Owner launch authority with length/slowness/one failed load. |
| §19.19 | KEEP unreachable active chat as a reported liveness gap, not a silent skip or automatic retirement. Current sole deliverer and supported capability limits remain. |
| §19.20 | KEEP same-transition remap of every affected lease/grant to the actual successor branch/PR. Preserve scope, lifetime and all three counters; “follow the work” is not renewal. |
| §19.21 | KEEP one frozen review target per evidence block, with intermediate SHAs explicitly superseded. Preserve old proof as history and invalidate only affected current claims after change. |
| §19.22 | KEEP truthful proof-role tags, [OWNER] only for the actual Owner decision source, and correction of mislabelling. Role tags/shared GitHub account do not authenticate an actor. |


## Part C — Migration guard (adopted with v3.0)


Replace Part C.4 and add the migration guard:

Protocol readiness is one prerequisite for the Owner's recorded P1 landing revision, P2 Common#408 and P3 Common#409 sequence. Adoption does not itself lift any HOLD, renew a grant, authorize a new chat/helper, remap custody, start a watcher or work unit, activate UEM, merge/release, or confer acceptance. Before each project's next unit, use its actual registry and Owner record to establish actor, action/scope/lifetime, source, capability, custody and applicable independent verification. Route only the missing decision; do not ask again for a settled one.

The adoption record names the adopted version, projects and explicit supersessions. Preserve the old text struck in place, historical native records, source links, original fixture custody, pending/uncertain deliveries, counter identities/counts and grant expiries. Update the governing entry points/registry pins and their status projections in a scoped migration with actual readback and a rollback/reference path; expose any partial update. A Protocol-tab label, draft merge, passing tests or this review is not adoption or live activation. Unadopted projects and existing HOLDs stay unchanged.

Also reconcile Part B §1 versus §17 before adoption: remove an obsolete named role if appropriate, but retain observe-only bootstrap, single controller, epoch fencing and real stop/custody. Explicitly dispose of the pending v2.3-freeze question rather than having a document editor silently replace it.


## Part D — What known issues mean for this draft (Codex Q9 §7, adopted)


- **K01/K04:** foreign-source omission and incomplete qualification remain proof limits; a new protocol title does not make unseen work visible or manufacture a full run.
- **K02:** retain “action done, readback failed, served effect UNKNOWN”; do not infer no deployment. A proposed race explanation remains a hypothesis.
- **K03/K21:** do not repair a loose original oracle by editing frozen goldens, or add fields to the canonical v3.6 block to solve continuity. Future versioned repairs are separately authorized work.
- **K05/K11:** an unverified human-string lease holder and stale registry/status are unresolved data/custody limits; a proposed schema or “updated together” sentence is not implemented atomicity.
- **K06/K07/K08:** no real moves/EVALUATED during HOLD is not a reason to seed activity. Approximate time is not an ISO date; irregular scheduled deploys are not an agent wake guarantee.
- **K10/K14/K16:** keep append-only typo correction, post-retirement activity investigation and estimated-time disclosure as actual open items, not assumed breach or fix.
- **K12/K13:** shared-account attribution and API-exposed/minimized grading material remain limitations. Do not claim authenticated Owner identity or a pristine blind test from formatting.
- **K15/K17/K19:** a changed skill/delivery-role/line-ending policy is a mitigation; actual read completeness, byte preservation and chat delivery still need their own observable receipts.
- **K18/K20:** no invented meter; no selector mismatch bypass or silent global BuddyRunner upgrade.
- **K09:** a cancelled concurrency run is not a passing run; retain its actual disposition where relevant.

### Recommended next decision

OwnerTeammember should reconcile this one draft first, keeping the ten-rule layout and making the precise changes above. Then give the Owner a short adoption card naming the affected projects, remaining known limits, explicit policy changes and unchanged HOLDs. Reason: this preserves the useful simplification without accidentally expanding launch/approval authority or deleting the liveness, bootstrap, native evidence and handover protections the simplified document is meant to carry.

No product work, chat send, browser use, new agent, timer, own counter, new HOLD, protocol/registry edit, merge, release or acceptance was performed for Q9. The only requested output is this review and its #1 completion receipt.


## Part E — Reconciliation record (OwnerTeammember)

- **Adopted from Q9 as written:**
  - R1–R10;
  - the Part B table, including every §19 rule individually (it restores observe-only bootstrap, §17, which r1 wrongly struck);
  - §18: the pending "freeze v2.3" decision stays the Owner's (adopt v3.0 or freeze v2.3);
  - the Part C guard: protocol readiness does not lift the HOLD or create custody for P1–P3.
- **D1 (A8):** the standby trigger cites the Owner's recorded standby rule (#1 6229973054); 80% only where a meter is actually measured.
- **D2 (A10):** per-run audits for pilot/test projects cite the Owner's words (#1 6229973054).
- **D3 (A5):** a measured context-size trigger (~400k), proposed and not adopted.
- **Open for the Owner:** adopt v3.0 (with or without D1–D3) or freeze v2.3; the Watchdog workflow stays OPEN.

---

## Appendix — Team protocol v2.3 (15 Oct 2026), historical text

> Superseded by v3.0 on 17 Oct 2026 where Part B says REVISE. Kept word for word below (headings demoted one level, nothing deleted). Do not follow a v2.3 clause that Part A or Part B revises.

### ~~Team protocol v2.3 (final candidate) — CoordinatorLandingpage~~ (historical)

> (v2.3) Status: **v2.3 FINAL CANDIDATE** (15 Oct 2026; v2.2 + §19.20–19.22 from the R14 fix loop; v2.1 + §19.13–19.19 and the Owner-input channel, from the afternoon run of imo-ab-test, the landing-page build and Codex onboarding). v2.0 plus §19, the rules proven necessary by the imo-ab-test stress test (two agents, a separate Claude coordinator, OwnerTeammember). Becomes **FROZEN** on the Owner's word "freeze"; after that, changes need the Owner's words, a change note and a version bump. Dubai time (+04:00) everywhere.

**Machine copy:** `protocol/TEAM_PROTOCOL.md` in this repository (read the raw file). **Start here as a new agent:** §2 places → your project's `registry.json` → your role's rows in §1 → §3 or §4 → §13–§17.

**Purpose.** The Owner sets the aim and decides. ChatGPT agents do the engineering and report their own evidence here. TeamCoordinator keeps the chats moving. OwnerTeammember checks the evidence against GitHub and the Owner's intent. **Success = every relay improves the agent's work** (grounding check + Owner/parent intent reconciliation), at the lowest token cost, with nobody silently stuck.

---

### 1. Roles

| Role | Who | Does | Never |
|---|---|---|---|
| **Owner** | the human | aims, priorities, protected approvals | — |
| **OwnerTeammember** | Claude (posts on the Owner's GitHub account) | checks evidence vs GitHub and intent, grounding questions, relays Owner decisions, watches TeamCoordinator, writes a new TeamCoordinator's handover on Owner approval | approve protected actions without the Owner's quoted words |
| **TeamCoordinator** | Codex / ChatGPT Work (or OwnerTeammember as a stand-in when the Owner says so) | sends to agents, recovers them, replaces an unresponsive agent, publishes coordinator evidence | engineering, accepting, merging |
| **Agent** (coder, validator …) | one ChatGPT chat per role | works in its own lane, posts TASK EVIDENCE v2 | approve, accept, merge, release, edit another lane |
| **Watchdog** | GitHub Actions job (planned, needs Owner approval) | flags a stale status to the Owner | anything else |

**One TeamCoordinator at a time.** Control is held under a numbered **epoch** posted in inbox #1 (`CONTROL epoch N: <who> for <project>`). Before every send, a coordinator checks #1: a higher epoch than its own → it stops sending at once.

### 2. Places

- **Project registry** `logs/<project>/registry.json` — the single source of truth: control epoch and coordinator, the workflow card, active and retired agents (role, generation, chat id8, evidence thread, branch), standing Owner decisions, open Owner decisions, log folder. Every coordinator reads it first and updates it on every change; prompts never carry state that belongs here.
- **Owner inputs** — an open issue labelled `owner-input` (Issue Form `owner-input.yml`, posted by the Owner) is an Owner instruction, quoted and time-stamped by GitHub. The coordinator handles it next cycle (protected items via OwnerTeammember first), answers on the issue `HANDLED: …` or `NEEDS CLARIFICATION: …`, and closes it when handled.
- **OwnerTeammember ↔ TeamCoordinator** talk only through `FOR TeamCoordinator` posts in #1 and the coordinator's receipts (Owner, 15 Oct: "further you deal via post"); the Owner is not asked to paste between them.
- **Inbox #1** — instructions, Owner decisions (relayed), control/epoch notices, alerts.
- **Project status issue** (Grade 9: #6) — ONE status comment, edited in place (COORDINATOR EVIDENCE, §4).
- **Evidence thread per agent** — one issue per agent chat, `[Evidence] <project> · <role> · <chat id8>`. Agents append TASK EVIDENCE v2 blocks; OwnerTeammember replies there with the grounding verdict.
- **The chat** — the same block appears at the end of the agent's reply, plus the link to its GitHub copy.
- **Action log** (Owner, 15 Oct: "same ... CoordinatorLandingpage ... project wise > session wise"): `logs/<project>/<YYYY-MM-DD>_epoch<N>/events.jsonl` (one JSON line per action: time, actor, action, target, exact text sent, result, links) and `raw/<chat id8>/turn-<n>.md` (full text of each agent reply, saved once). Layout and fields: `logs/README.md`. Source for the Owner's dashboard (to be programmed later). Pushed as one commit per cycle.
- Public repository: facts and links only. Full chat URLs, drafts, tokens and transcripts stay out.

### 3. Agent evidence — TASK EVIDENCE v2

Every reply that **finishes a task** ends with this block (plain text code block), and the **same text** is posted as a new comment in the agent's evidence thread:

```text
TASK EVIDENCE v2 · <project> · <role> · chat <id8> · #<seq> · <dd Mon HH:MM +04:00>
Task: <ID> <title>                         Status: DONE | PARTIAL | BLOCKED | FAILED
Aim: <outcome> → user sees: <one line>   (or: enabling, none yet)
Did: <1–3 plain lines>
Where: <repo> @ <branch> · commit <7> · PR #<n> (<draft→target>) · files: <list>
Proof:
  - <claim> → <link>   [CI | READBACK | LOCAL | CLAIM-ONLY]
Tests: <command> → <p> pass / <f> fail / <n> not-run · CI <run link>: green | red | queued | not-run | baseline-red (<which, already red on base>)
Would be wrong if: <the test or observation that would overturn this>
Not done / HOLD: <item → evidence still missing>
Lane & authority: own lane only ✓ | <what crossed> · approvals used: none | <who, scope, link>
Needs Owner: none | "<exact question>" options A/B (recommended: X)
Next: <task IDs in order> (~<minutes>)
Meter: worked <m> this turn · <turns> turns · <min>/<limit> min · ok | near | due    Posted: <comment link> | NOT_POSTED:<reason>
```

A reply that finishes no task ends with one line: `STATUS v2 · <role> · chat <id8> · working on <task> · next <IDs> · blocker <NONE|OWNER|CI|PERSON|MACHINE|EXTERNAL: what> · <time>`.

Rules: post before ending the reply · **append only** (a correction is a new block `replaces #n`) · one claim per Proof line with its own grade · CI red that is already red on the base commit is `baseline-red`, not a new failure · no "approved/accepted/certified" without the decision link · if the agent cannot post, it writes `NOT_POSTED:<reason>` and TeamCoordinator copies the block unchanged, marked `relayed by TeamCoordinator`.

### 4. Coordinator evidence — COORDINATOR EVIDENCE v1

The project status comment, edited in place **only when something changed**:

```text
COORDINATOR EVIDENCE v1 · <project> · cycle <n> · epoch <e> · <start>–<end> +04:00 · steps <s> · ~<K> tokens
Health: TC ✓ <time> · OwnerTeammember ✓ <time> · watchdog ✓|— · agents <a> active, <w> waiting, <s> stopped
NEEDS YOU (<k>)
  1. <exact decision> Recommended: <option>. → <card link>
```
| Agent | State | Doing → outcome | Last evidence | Proof | Meter | Next (who) |
|---|---|---|---|---|---|---|
| [role id8](link) | 🟢 working · 🟡 waiting <age> · 🟠 handover · 🔴 error · ⚫ stopped | <task> → <outcome> | [#seq](link) <status> | <c> claims, <v> verified | <min>/<limit> · <t> t ⚠ | <TC / agent / OwnerTeammember / You>: <action> |

```text
Stopped: <agent> (since <time>; evidence thread kept)
Changed since last cycle: <bullets>
Sent this cycle: <agent> ← "<exact text>" → DELIVERED | UNCERTAIN | NOT_SENT <time>
```

A separate COORDINATOR EVIDENCE comment is **appended** (receipt) only for a send, a takeover, an epoch change or an Owner decision. In the TeamCoordinator's own chat: the first three lines only.

### 5. Cycles

**TeamCoordinator — smart cadence:** 10 min while an agent is working or was just sent something · 15 min while agents wait on another agent or CI · 30 min while everything waits on the Owner.
**Routine cycle = 3 steps:**
1. ONE batched read: new evidence comments, #1, PR/CI changes since the last cycle (IDs and hashes first; each new body read once).
2. ONE look at the tabs: working / idle / error / full (state only, not text).
3. Act and record together: for an idle agent with no gate, nudge with **its own `Next:`** ("proceed with G9C-T4 …"); route a finished coder block to the validator; ONE status edit.
**Quiet cycle = 1 step, no write.** Runner changes are tested and versioned outside the live loop, never patched mid-cycle.

**OwnerTeammember — event-driven:** a local waiter polls GitHub each minute (no model tokens) and wakes on a new evidence block, a new #1 comment, or a change in a status row's State/Needs-you; plus a **silence guard**: TeamCoordinator's last completed cycle older than 15 min → wake and check. Per new evidence block: 1–2 steps.

### 6. Grounding from the evidence

OwnerTeammember compares three things for each new block: **intent** (Owner handover, issue, parent, roadmap), **the block**, and **GitHub** (commit exists, PR head, CI, files).

| Signal | Question (sent through TeamCoordinator, word for word) |
|---|---|
| 3 blocks, no planned task closed / work outside the plan | "Your last blocks worked on X; the aim is Y. Which next task moves Y, and what proves it?" |
| claim ≠ GitHub | "You report <result> at <commit>; the PR head is <other>. Which commit does it belong to?" |
| approval words without a decision | "Who approved this, for what scope? Else mark it UNKNOWN." |
| lane crossed | "That file belongs to <lane>; your lane is <lane>." |
| new agent | only the BuddyRunner v1.7 own-words questions it has not answered |
| short turns (3 under 5 min) | "What is the smallest testable step that moves <outcome>?" |
| nothing specific | the standard Ground questions (fallback only) |

Verdict, replied in the agent's evidence thread: **✅ ALIGNED** · **✏ CORRECTED** (plan or next action changed, with the question) · **⚑ ESCALATE** (route conflicts with the Owner's intent → one line to the Owner).

### 6b. FOR TeamCoordinator — when OwnerTeammember instructs the coordinator (Owner, 15 Oct: "lets start using")

Only by exception, as ONE comment in inbox #1, in this form:
```text
FOR TeamCoordinator · <project> · <TYPE> · <id>
Do: send to <agent id8> word for word: "<text>"   |   <action for the coordinator>
Why: <one line> · Evidence: <links>
```
TYPE: **RELAY** (an Owner decision, quoted with time; always) · **CORRECTION** (a verdict that must reach the agent's chat) · **ROUTE** (a finished step not routed within one coordinator cycle) · **STATUS** (status wrong vs GitHub, a missing Needs-you item, or no completed cycle for 30 min) · **BREACH** (send to a retired chat, hold ignored, wrong epoch, claim treated as accepted) · **GATE** (a milestone claim: freeze both agents' commits for the final check before the Owner's acceptance card).
The coordinator acts on it in its next cycle and posts a receipt that names the id (`FOR-TC <id> → DELIVERED | NOT_SENT <why>`). Never used for routine nudges, task choice, engineering, or anything that still needs the Owner's approval.

### 7. Authority

Protected: merge, release/publish, new chat, upload, change of writer or role, acceptance (academic, QRT, source rights). Only the Owner decides. OwnerTeammember relays a decision only as: `OwnerTeammember — relaying Owner decision. Source: Owner chat, <time>. Owner's words: "<quote>". Action / Target / Limits: …`. A prefix alone is never approval.
**Standing approvals in force for the Grade 9 pilot:** pilot cycles up to 10× tokens for 24 h (15 Oct); option B (v3.6 managed lifecycle off); BuddyRunner v1.7 for new handovers; 10-min cadence. **Owner, 15 Oct ~07:25:** *no* standing approval for replacing an agent ("no approval follow protocol in your skill"): a new chat for a dead agent only on the Owner's word. Timeouts in §8: approved ("ok"). OwnerTeammember as stand-in TeamCoordinator during a TeamCoordinator outage: approved ("ok").

### 8. Guards, fallback, takeover

| Link | Alive signal | Unresponsive when | Watched by |
|---|---|---|---|
| Agent | tab state + new evidence | working with no new turn 60 min · idle and nudged twice, no reply · error survives recovery · chat full | TeamCoordinator |
| TeamCoordinator | `Cycle completed` + local heartbeat file | no completed cycle for 2× its cadence (max 30 min) · a #1 instruction not taken up in 2 cycles | OwnerTeammember (+ watchdog) |
| OwnerTeammember | evidence-thread replies + local heartbeat file | heartbeat older than 30 min, or evidence unanswered 30 min | TeamCoordinator → alert in #1 |
| GitHub | API reachable | down | everyone falls back to the chats |

**Agent ladder:** (1) Stop → wait 30 s → `continue` → check; (2) error rows (reload / retry / unusual-activity wait); (3) normal handover if it can still write (BuddyRunner v1.7 one-step); (4) **cannot write its own handover → report to the Owner** (one line, the agent's chat and evidence links) with a **draft handover** already written by TeamCoordinator from the agent's evidence thread + PR/CI + the Owner's handover. **Only on the Owner's word**: ONE new chat, same role and scope → the new agent answers the v1.7 questions first → works on a **new branch** from the last confirmed commit (old branch frozen; old chat retired, gets nothing) → its evidence thread links the old one. Settle any UNCERTAIN send first.
**TeamCoordinator down:** OwnerTeammember alerts the Owner at once (with a paste-ready resume line) → if not back in 15 min or the Owner says so, writes the handover for a new TeamCoordinator (roles, chats with state and next task, open decisions with quoted words, UNCERTAIN sends, timers, "observe first, then take control") → **on Owner approval** the Owner starts it → epoch +1 in #1 (the old one stops itself if it wakes). Agents keep working and posting evidence meanwhile; OwnerTeammember becomes stand-in TeamCoordinator (approved by the Owner, 15 Oct) once the old one is confirmed stopped: new epoch in #1, one line to the Owner.
**OwnerTeammember down:** TeamCoordinator continues with fallback grounding and alerts the Owner in #1; the Owner restarts it with "Resume OwnerTeammember for CoordinatorLandingpage"; it rebuilds from GitHub.
**GitHub down:** agents put the block in the chat (`NOT_POSTED:github`); coordinators read the chats; post the backlog when GitHub returns.
Checked by an executable model (`flowcheck.py`, 77 failure combinations): with epochs, branch fence, heartbeat files and watchdog, the only open cases are both watchers down at once plus the Owner away or GitHub down.

### 9. Handover and new agents

New handovers use **BuddyRunner v1.7** (`skills/buddy-runner-v1-7` at 8405c9d9). One-step handover: the outgoing agent writes the complete handover file (final direction, first workpack, the twelve sections of v1.7 `2_RECONCILE.md`, anchors to re-verify, open decisions) and stops. The successor's first reply answers the v1.7 own-words questions (role and predecessor, authoritative inputs and approval scope, original-issue gap, up to three highest-value steps with a falsifier), then posts TASK EVIDENCE v2 #1 in its new thread.

### 10. Onboarding a chat to this protocol (one message)

> Team protocol v1 applies from now: <link to this issue>. Your evidence thread is <link>. From your next reply: end every reply that finishes a task with TASK EVIDENCE v2 (section 3, exact layout) and post the same text as a new comment in your thread; replies that finish no task end with the STATUS v2 line. First: post TASK EVIDENCE v2 #1 for the work you just finished (<what>) in your thread — this is also the access test; if you cannot comment there, say NOT_POSTED and why. <one grounding note from §6>. Then continue with <its own Next>.

### 11. Economy

Targets: quiet cycle 1 step and no write; routine TeamCoordinator cycle ≤ 3 steps; OwnerTeammember 1–2 steps per new evidence block; every status shows `steps · ~tokens`. Measured after one pilot day: tokens per finished task, minutes from block to next nudge, grounding corrections.

### 13. Workflow card (per project)

The Owner's loop for the project, in the Owner's words, with the current step. It lives in the registry (`workflow`) and in the status header. Only the Owner changes it; a change is relayed in #1 with the quote and time, and every active agent gets one message with the new card. Example (Grade 9): *"QRT tile by tile: idea is to design a validator (by one agent), fix existing standalone html based on validator outcome (another agent), check and fix the validator if required"* → validator checks a tile → fixer fixes via source + builder → validator re-runs and fixes itself where wrong → 0 FAIL → next tile.

### 14. Changeover (Owner-ordered replacement, or takeover)

1. **Freeze** the outgoing chat: if it is working, press Stop; read back its branch/PR heads; wait one cycle and confirm no new commit or evidence arrives.
2. **Retire**: one line in its evidence thread and a notice in #1 (Owner's words + time); registry → `retired`.
3. **Handover issue** = the new agent's evidence thread, body = handover: role and loop (workflow card), repository state with exact commits, reusable prior work, known findings, open Owner decisions, boundaries, reporting, first reply. Written by the **coordinator** when the Owner orders the change or the workflow changes; by the **outgoing agent** (BuddyRunner v1.7 one-step) when it is alive and the workflow is unchanged. Built from the evidence threads and GitHub, never from memory.
4. **New chat** (only on the Owner's word): one-paragraph start prompt pointing to the handover issue and this protocol. Count and roles must be clear (§16).
5. **First reply** = v1.7 own-words answers (role and predecessor, authoritative vs candidate inputs, what it may not change, first step). OwnerTeammember checks them (§6) before the agent's first material change.
6. **New branch** from the last confirmed commit; old branch frozen. Registry, status and log updated; a coordinator never sends to a retired chat.

### 15. Drift rule

A block that does not advance the current workflow step → one grounding question back to the step. Three analysis-only blocks in a row from an implementing agent → "What can you fix now?". Reports for the Owner are produced only when the Owner or the workflow asks for them.

### 16. Ambiguity rule

An Owner instruction that would trigger a protected action (new chat, merge, release, upload, writer/role change, acceptance) and is unclear in count, roles or scope → one-line confirmation first, unless an earlier Owner instruction settles it; then name that instruction in the relay.

### 17. Bringing in another coordinator (bootstrap)

A new TeamCoordinator (any capable agent with GitHub comment access and control of the agent chats) starts **observe-only**: it reads this protocol and the registry, answers in its own words (roles, its 3-step cycle, what it must never do, what it would do in its first cycle), and posts one COORDINATOR EVIDENCE block with **no sends**. OwnerTeammember checks the answers and the block against the registry and the chats. Control passes only on the Owner's word: `CONTROL epoch N+1: <who>` in #1, registry updated, the previous coordinator stops sending.

### 19. Rules added from the stress test (v2.1)

1. **Delegation is per project and explicit.** A project's registry names its OwnerTeammember (`control.owner_teammember`) from the Owner's own words, before any relay counts. Until then the coordinator correctly ignores relays (observed: relays were refused while the Owner had told the coordinator "OwnerTeammember = Owner").
2. **One Owner word, one record.** Whoever receives an Owner instruction (coordinator or OwnerTeammember) posts it in #1 with the quote and time in the same cycle. The **latest** Owner word wins; a later relay names the record it supersedes (observed: "need to work with this" at 08:58, then a PDF supplied at 09:05).
3. **Writer leases live in the registry.** Every exclusive path grant (`leases`: agent, paths, branch, granted by and when) is listed. A commit to a project branch from anyone not holding the lease, including the Owner's local agents, is an **outside write**: the coordinator records it, it is not built on, and the checker reviews it before it counts (observed: commit 5a117f69 pushed onto PR #240 from outside, carrying a leased file).
4. **A checker change never certifies itself.** A change to a validator, audit or test harness counts only after a different agent has checked that exact commit, never in the same commit as the result it produces (observed: the QRT audit edited in the same commit that claimed "100% across 260"; AB-HARNESS required Agent B's check first).
5. **Proving baseline-red.** A failing check is baseline-red only with a link to the same check failing on the base commit before the agent's change. Otherwise it is the agent's regression and its own next task (observed: Core1B and learner-platform were proven caused by the renderer change, then fixed).
6. **Narrow scope grants.** Fixing outside the allowlist needs an Owner grant naming exact paths, generator output only (no hand edits), one frozen commit, and the checker's PASS on it (observed twice: three TEST hub pages, then their docs mirror).
7. **Manual or gated runs are started by someone other than the graded agent** (OwnerTeammember, on the Owner's word), once, on the commit the checker passed, with the run link posted in #1.
8. **Private inputs.** Never in the public repository. Agent sandboxes lose files between turns and cannot clone the repository: use private inputs in the same turn and report hashes only. A full native run happens on the Owner's computer (files downloaded by the Owner, hashes checked, commands shown to the Owner before running) or is parked until the final phase.
9. **An agent waiting on another agent but holding its own non-blocked Next is nudged**, not left idle (observed: corrected by FOR TeamCoordinator FTC-003).
10. **Times come from the clock**, never estimates; a wrong time is corrected by a receipt that names the record it replaces.
11. **Milestone gate.** A claim such as 21/21 or "plan done" → GATE instruction: freeze the commits, OwnerTeammember verifies the counts on GitHub, then ONE acceptance card to the Owner (what was shown, what is open, what is asked). Nothing is accepted from an agent's or a coordinator's word.
12. **Liveness mechanics.** One-shot timers are unreliable; the waiter (wake on change or on silence) plus a recurring check are the guards. A participant stepping back posts it in #1 and the registry (`paused since`).

13. **Every frozen commit is on a draft PR.** A new or successor branch gets its draft PR when its first commit is frozen, so CI runs on the exact SHA and the checker can cite a run (observed: successor branch with no PR, tests NOT_RUN).
14. **Fix at the source, regenerate the copy.** A generated file or mirror is never hand-edited to pass a check; the fix goes into the source or generator and the copy is regenerated (observed: 01f29334 gated only the docs copy while the public source still revealed the proof).
15. **Harnesses fail closed with the real error.** A wrapper must not swallow a child failure; it stops the run and reports the real assertion (sanitized), and its own failure path has a test (observed: the R14 wrapper hid the subprocess assertion; fixed in 8192d28d).
16. **No borrowed approvals.** An agent never states that another role reviewed, approved or confirmed something (in a block, a commit message or a PR) without a link to that role's own post. An unsupported claim is corrected in the thread (observed: a commit message said OwnerTeammember had confirmed a test change it had not).
17. **A loosened check is a weakened check.** A test changed so that it passes (for example by matching a substring such as "FAIL" that also appears in "FAIL 0") counts only after the checker reviews it and a negative control proves it can still fail.
18. **A full chat is a changeover.** When an agent's chat hits its length limit: Owner's word → new chat → §14 (successor branch, v1.7 first reply, OwnerTeammember grounding check before edits). The coordinator records the Owner's words in #1 before or with the start message.
19. **The coordinator must be able to reach every active chat.** A chat tab that is closed or unreachable is a liveness item for the Owner (one line), never a silent skip.

20. **Grants follow the work through a changeover.** When a successor branch or PR replaces the one a lease or grant names, the coordinator re-maps every affected registry entry to the new branch/PR in the same cycle and says so in its receipt. Any change of scope (other files, other repos) needs the Owner again (observed: AB-R14-REDISPATCH named PR #268, while the passed runner lived on successor PR #272).
21. **One review target at a time.** Each evidence block names exactly one frozen SHA for checking and lists the intermediate SHAs it supersedes. The checker checks only the latest named SHA (observed: c98cf322 and b0a0de94 superseded by 8192d28d, then 3691af85).
22. **Role tags on proof.** Besides the proof grade, a link to another role's post carries that role: `[OWNER]` only for the Owner's own decision, `[OWNERTEAMMEMBER]`, `[CHECKER]`, `[COORDINATOR]`. Mislabelling a role is a §19.16 correction (observed: OwnerTeammember's confirmation tagged "[B / OWNER]").

### 18. Open Owner decisions

Decided 15 Oct ~07:25: no standing approval for agent replacement (Owner decides each case); timeouts approved; stand-in during an outage approved.
Open: **freeze v2.3** (one word: "freeze"). **Watchdog workflow** (§1): a scheduled GitHub Actions job, every 15 min, reads the status comment's "Cycle completed" time and, if older than 45 min, opens/updates an alert issue mentioning the Owner. It runs on GitHub, not on the home computer, so it still alerts when the computer or both sessions are down. Free on a public repository, no AI; blind during a GitHub outage.

### 20. Next Move v1 (pilot, landing-live only)

Change note, 16 Oct 2026 ~19:3x. Owner: "review cycle is over. start planning and implement. any difference, now you dictate (if genuine else adopt)".
- **Next Move v1** is the auditable record of who should do what next, on what basis and with whose approval. It is specified in `protocol/NEXT_MOVE_v1.md` and reviewed by Codex.
- It applies **only** where a registry has `next_move.pilot: true`, currently `landing-live`. Everywhere else this protocol is unchanged.
- Registry `criticality` (`critical | normal`) is set only by the Owner's words. An unset value counts as critical.
