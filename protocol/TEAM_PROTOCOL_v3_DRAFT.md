# Team protocol v3.0 — DRAFT (not in force)

**Status:** DRAFT, written by OwnerTeammember on 17 Oct 2026 (Owner: "S4: go (protocol draft)"). **`protocol/TEAM_PROTOCOL.md` v2.3 stays in force** until the Owner adopts this draft in words. Review route: Codex reviews (queue item in #1), OwnerTeammember reconciles, Owner decides.

**What this draft does:** it states the rules we actually operate by after 16–17 Oct, and maps **every v2.3 section** to KEEP / REVISED / SUPERSEDED (Part B), so nothing is lost. On adoption, superseded v2.3 text is **struck through in place and kept** (Owner: "Scrap all the old modes, do not delete, mark like comment").

**Built from** (sources, not authority):
- the ecosystem v4 proposal + Codex review (M01–M12) + OwnerTeammember reconciliation;
- the S1 brief and the S2 cold-reader tests (#55);
- the operations table in [`docs/LANDING_LIVE_BRIEF.md`](../docs/LANDING_LIVE_BRIEF.md);
- [`docs/KNOWN_ISSUES.md`](../docs/KNOWN_ISSUES.md).

---

## Part A — Rules (v3)

### A1. Roles
| Role | Who | Does | Never |
|---|---|---|---|
| **Owner** | the human owner | intent, criticality, critical approvals, **acceptance**, release, rights, new agents outside the standby rule, scope | — |
| **OwnerTeammember + TeamCoordinator (OTM/TC)** | one Claude session (one actor) | approves non-critical next steps (labelled), **sole deliverer** to agent chats, nudge/recover/succession, merges where delegated, records, status | verifies or accepts its own work; long reading in its own context |
| **Codex** | planner + reviewer ([#1 6229612086](https://github.com/reallakshman19/CoordinatorLandingpage/issues/1#issuecomment-6229612086)) | reviews, decision papers, WP drafts, briefs/indexes, audits of OTM approvals, cold-test judging, all on GitHub | chat sends, browser delivery, unilateral authority changes (it still honours real HOLDs, grants, counters) |
| **Checker** | a fresh independent model run per PR | exact-head check, with a verdict | merging; reuse across PRs |
| **Agent** | ChatGPT/Antigravity chats doing the work | the work, native evidence, reporting Owner words it receives | approving itself |
| **Scripts** | watcher, publisher, validators | observation and projection | judgement or authority |

All posts come from the Owner's one GitHub account, so role labels are **claims, not authentication** (known issue K12).

### A2. Authority — every power cites a recorded Owner decision
1. **Authority map per project:** power → Owner record (link) → scope → lifetime → what stops it. Example: the operations table in the landing-live brief. A classification (e.g. `criticality: normal`), a checker PASS, a START, a filled field or a timer is **never** a permission by itself.
2. **Non-critical projects:** OTM may approve next steps inside the Owner-approved plan, labelled "OTM-approved"/"self-approved" with one #1 line giving the basis. **Critical projects** (or unset criticality): Owner only, apart from OTM's three standing duties (nudge with the agent's own Next; takeover via the selected native handover; clarify non-critical questions that need no assumption).
3. **Always the Owner's, on every project:**
   - acceptance (product, academic, QRT);
   - release;
   - rights or publication;
   - merges outside a delegated grant;
   - new agents or chats outside the standby rule;
   - widening scope;
   - lifting an Owner HOLD;
   - purchases.
4. **Done ≠ verified ≠ accepted.** The doer never verifies its own work; nobody accepts their own work. An action whose check failed is "done, not verified", not "didn't happen" (example: deploy run 39000177607).

### A3. Owner words
- **One Owner word = one #1 record** (keeps v2.3 §19.2). Words given in any chat (to OTM, to Codex, inside an agent's chat) are posted in #1 as a **record copy** with the exact quote, source and time (or a marked range such as `05:1x`). The latest word wins; a later record names the one it supersedes.
- **An authoritative channel for Owner technical input:** the Owner's own commit via the landing page Owner-inputs form, or an Owner comment. An agent's transcription is a claim until linked to one of these.

### A4. HOLD — one meaning
- HOLD stops **work and sends** in its scope (all / project / agent).
- It is recorded in #1 and in registry `control.hold` as an object: `since, owner_words, scope, lifts_on, source, previous`.
- **Watching continues only on an explicit Owner "watch only".** Read-only analysis and record fixes the Owner asks for are allowed.
- A HOLD on a working agent must **reach its chat** (post HOLD; Stop if mid-turn).
- It lifts only on Owner words. Held moves need fresh approval afterwards.

### A5. The coordination loop (event-driven)
0. **Sense:**
   - one authorised watcher script polls GitHub (new comments, PR heads, registry/inputs) and emits a line only on a change;
   - plus **due events** (an Owner-ask age or deadline, an expected agent return) and **watcher health**;
   - quiet = no model work.
1. **Read (first pass):** a fresh read-only helper returns a short card per agent (state, last instruction, status/meter or UNKNOWN, new evidence, head match, uncaptured Owner words, suggested action).
2. **Decide (second pass, OTM/TC):** one bounded useful step after checking Owner amendments, grant lifetime, HOLD, source/head, custody and prerequisites.
   - **Outcomes:** GO · nudge · deliver · recover · succession · FOR Codex · ask Owner · KEEP/NO_CHANGE · BLOCKED (precise).
   - A complete END is **not** a GO.
3. **Act:** delivery uses the Next Move states (SEND_INTENT → SENT_TO_CHAT / NOT_SENT / DELIVERY_UNCERTAIN → PICKED_UP).
   - One sender per chat.
   - An uncertain send is reconciled before any resend.
   - Publication is not delivery; pickup is not acceptance.
4. **Record:** the **next actor, next action and expected return** for every open item; registry + status comment updated together (K11); a #1 line per approval/delivery/Owner word.
5. **Report:** the Owner sees one status line plus traffic-light rows. An ask escalates by deadline or impact, once. Identical repeated reports are not sent.
- **Agent timers are NOT_ARMED by default.** An exception needs Owner words + creation proof + one fire + cancellation proof.
- **COORDINATOR EVIDENCE** is posted **only when something changed**.

### A6. Evidence
- **Native format per project:**
  - team projects (e.g. landing-live): **TASK EVIDENCE v2** / STATUS v2;
  - Engineering v3.6 repos: native TASK_EVIDENCE + **mandatory terminal LOG**.
  - A richer continuity format may be added later **by reference** as a sidecar. It never competes as a completion receipt (Codex M03).
- **Three axes, kept apart:**
  - input provenance (ORIGINAL / SYNTHETIC / PARTIAL / NONE);
  - verification scope (STRUCTURAL / BEHAVIOURAL);
  - acceptance (a human record).
  Keep both the falsifier ("would be wrong if") and "not proven".
- **Three outcomes, kept apart:** readable record / sufficient for a stated claim / eligible for an action. UNKNOWN never satisfies a permission, custody, source or acceptance condition.
- **Exact head:** hosted CI at the exact current head; a moved head = "superseded". Keep §19.13–19.22.

### A7. Continuity (long-running projects)
- **Root issue + brief/index per project:** one root issue (Owner intent) with a "START HERE" pointer to a brief + history index + authority map + route map, each an **index over sources**, never authority (model: landing-live `docs/`).
- **Struck-through grammar for anything superseded** (issues, agents, modes, decisions): `#123 → ~~#125~~ (reason, link) → #126`. A 404 is shown as "availability unverified", never as deleted.
- **Accounting ≠ proof.** UNKNOWN is shown openly and never shown green.
- **Invalidate on material change:** a changed Owner decision, source SHA, fixture or grant invalidates the dependent conclusions at once. History stays.
- **Corrections append, never edit.** E.g. a correction comment under a stale handover.
- **Continuity test:** a fresh cold reader given only the root issue answers the Owner's 10 questions, judged on reasoning by a non-author. Test material lives in a separate log issue (e.g. #55), never on the root issue (K13).

### A8. Succession
- **Handover Master selects the native method** (BuddyRunner 1.6 / 1.7 per the governing pin; see K20).
- **Early warning:** at a measured meter ≥80%, or a real sign (a long chat, slowness, "Could not load" once, "maximum length"), open **one standby** while the outgoing agent still works. It onboards with own-words answers and a published 1b, then holds.
- **No standby at chat end:** OTM acts as G1 and writes the 1a from GitHub, marking G1 claims as hypotheses.
- **Lease on a retirement:** mark the agent `retired` with the reason and the lease `released`; a successor needs a fresh lease remap (§19.20) and work permission.

### A9. Records hygiene
- **Times from the clock only;** an unknown minute is written as a range (`04:1x`), never invented (§19.10, K16).
- **Registry and doc edits from the repo bytes,** line endings preserved, minimal diff confirmed before push (K17).
- **Thread reads via the REST comments API with pagination** (K15).
- **Known issues** live in `docs/KNOWN_ISSUES.md` with source, status and owner.

### A10. Codex desk
- **The queue:** OTM posts `FOR Codex — Qn` items in #1. The Owner pastes one fixed line to Codex. Codex's outputs start with `VERDICT / NEXT / DELIVER TO`.
- **Codex's answers:**
  - "FOR TeamCoordinator: deliver <URL> to <id8>" → OTM delivers and answers DELIVERED / NOT_DELIVERED in #1;
  - "DONE Qn" → OTM summarises.
- **Audits:** every Codex run audits OTM's approvals since the last run.
- **No timer for Codex** while the queue is light; the queue age shows on the status bar.

---

## Part B — Crosswalk: every v2.3 section

| v2.3 section | v3 disposition |
|---|---|
| §1 Roles | **REVISED → A1.** ~~Codex/ChatGPT Work as TeamCoordinator~~, ~~observe-only candidate TC~~, ~~stand-in TC~~: one combined OTM/TC actor; Codex is planner/reviewer. The Watchdog stays an open option (see §18). |
| §2 Places | **KEEP**, plus: `docs/` brief/route map/known issues; a separate test-log issue (#55). |
| §3 TASK EVIDENCE v2 | **KEEP** as the native team format; A6 adds the three-axis wording. |
| §4 COORDINATOR EVIDENCE v1 | **REVISED → A5:** posted only on change. |
| §5 Cycles | **SUPERSEDED → A5.** ~~Cadence 10/15/30 min; routine vs quiet cycle~~: event-driven watcher + due events. |
| §6 Grounding | **KEEP** (gap-specific, from evidence; no CI rule). Plus grounding at assignment and on material change (A7). |
| §6b FOR TeamCoordinator | **REVISED → A10:** now also the Codex "deliver" line; OTM answers DELIVERED/NOT_DELIVERED. |
| §7 Authority | **REVISED → A2** (authority map; operations; done ≠ verified ≠ accepted). |
| §8 Guards, fallback, takeover | **REVISED → A5/A8.** ~~TC-silence guard between two coordinators~~: one actor; an outage goes to the Owner. |
| §9 Handover and new agents | **REVISED → A8** (Handover Master selects; early warning; coordinator-as-G1). |
| §10 Onboarding | **KEEP.** |
| §11 Economy | **REVISED → A5:** event-driven, a reading helper, and a context-size rule for the coordinator session (not a timer). |
| §13 Workflow card | **KEEP:** registry `workflow.current`, with old text kept as `previous`. |
| §14 Changeover | **KEEP**, plus A8 (retired + released + remap). |
| §15 Drift · §16 Ambiguity · §17 Bootstrap | **KEEP.** |
| §18 Open Owner decisions | **REVISED:** ~~"freeze v2.3"~~ is replaced by "adopt v3.0". The Watchdog workflow stays OPEN. |
| §19.1–19.22 stress-test rules | **KEEP all.** 19.2 → A3; 19.10 → A9; 19.12 liveness → A5; 19.18 full chat → A8 early warning; 19.20 → A8 lease. |
| §20 Next Move v1 | **KEEP** (pilot, `next_move.pilot: true`); delivery states are reused in A5. |
| UltraEconomyMode (`ULTRA_ECONOMY_MODE.md`) | **PARKED** (Owner 17 Oct). Not part of v3. Activation needs Owner words; timers are not a prerequisite. |

## Part C — Adoption steps (each needs its own go)
1. **Codex review** of this draft (queue item in #1). OTM reconciles; genuine points are adopted.
2. **The Owner adopts in words** (e.g. "adopt v3.0"), recorded in #1.
3. **One PR:**
   - `TEAM_PROTOCOL.md` → v3.0, with Part A added;
   - superseded v2.3 text **struck in place inside `<details>`** (kept);
   - the Protocol tab shows v3.0.
4. **Then the three projects may start:** P1 landing revision (OTM author), P2 Common#408, P3 Common#409 (Owner, [#1 6228221349](https://github.com/reallakshman19/CoordinatorLandingpage/issues/1#issuecomment-6228221349)).

## Part D — Known issues
See [`docs/KNOWN_ISSUES.md`](../docs/KNOWN_ISSUES.md) (K01–K21). The protocol-relevant ones are:
- K11 (registry/status lag);
- K12 (shared account);
- K13 (blind-test limit);
- K16 (estimated times);
- K17 (line endings);
- K18 (no meter);
- K20/K21 (cross-repo).
