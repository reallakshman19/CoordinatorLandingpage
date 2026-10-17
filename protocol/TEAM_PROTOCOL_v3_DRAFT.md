# Team protocol v3.0 — DRAFT r2 (not in force)

**Status:** DRAFT r2 (17 Oct 2026). `protocol/TEAM_PROTOCOL.md` **v2.3 stays in force** until the Owner records an adoption decision. r1 was written by OwnerTeammember. r2 adopts Codex's Q9 review ([PR #59 comment 6229963293](https://github.com/reallakshman19/CoordinatorLandingpage/pull/59#issuecomment-6229963293)): its exact R1–R10 wording, its section-by-section crosswalk and its Part C migration guard, plus three OwnerTeammember differences (D1–D3), each tied to a recorded Owner source. Proposed text below is **not** operating instruction; permission still comes only from recorded Owner decisions.

Superseded v2.3 text will be **struck through in place and kept** on adoption (Owner: "Scrap all the old modes, do not delete, mark like comment"). Known issues: [`docs/KNOWN_ISSUES.md`](../docs/KNOWN_ISSUES.md).

---

## Part A — Rules (proposed v3 text)

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


## Part C — Adoption and migration guard (Codex Q9 §6, adopted)


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
