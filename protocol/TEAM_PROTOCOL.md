# Team protocol v2.2 (final candidate) — CoordinatorLandingpage

Status: **v2.2 FINAL CANDIDATE** (15 Oct 2026; v2.1 + §19.13–19.19 and the Owner-input channel, from the afternoon run of imo-ab-test, the landing-page build and Codex onboarding). v2.0 plus §19, the rules proven necessary by the imo-ab-test stress test (two agents, a separate Claude coordinator, OwnerTeammember). Becomes **FROZEN** on the Owner's word "freeze"; after that, changes need the Owner's words, a change note and a version bump. Dubai time (+04:00) everywhere.

**Machine copy:** `protocol/TEAM_PROTOCOL.md` in this repository (read the raw file). **Start here as a new agent:** §2 places → your project's `registry.json` → your role's rows in §1 → §3 or §4 → §13–§17.

**Purpose.** The Owner sets the aim and decides. ChatGPT agents do the engineering and report their own evidence here. TeamCoordinator keeps the chats moving. OwnerTeammember checks the evidence against GitHub and the Owner's intent. **Success = every relay improves the agent's work** (grounding check + Owner/parent intent reconciliation), at the lowest token cost, with nobody silently stuck.

---

## 1. Roles

| Role | Who | Does | Never |
|---|---|---|---|
| **Owner** | the human | aims, priorities, protected approvals | — |
| **OwnerTeammember** | Claude (posts on the Owner's GitHub account) | checks evidence vs GitHub and intent, grounding questions, relays Owner decisions, watches TeamCoordinator, writes a new TeamCoordinator's handover on Owner approval | approve protected actions without the Owner's quoted words |
| **TeamCoordinator** | Codex / ChatGPT Work (or OwnerTeammember as a stand-in when the Owner says so) | sends to agents, recovers them, replaces an unresponsive agent, publishes coordinator evidence | engineering, accepting, merging |
| **Agent** (coder, validator …) | one ChatGPT chat per role | works in its own lane, posts TASK EVIDENCE v2 | approve, accept, merge, release, edit another lane |
| **Watchdog** | GitHub Actions job (planned, needs Owner approval) | flags a stale status to the Owner | anything else |

**One TeamCoordinator at a time.** Control is held under a numbered **epoch** posted in inbox #1 (`CONTROL epoch N: <who> for <project>`). Before every send, a coordinator checks #1: a higher epoch than its own → it stops sending at once.

## 2. Places

- **Project registry** `logs/<project>/registry.json` — the single source of truth: control epoch and coordinator, the workflow card, active and retired agents (role, generation, chat id8, evidence thread, branch), standing Owner decisions, open Owner decisions, log folder. Every coordinator reads it first and updates it on every change; prompts never carry state that belongs here.
- **Owner inputs** — an open issue labelled `owner-input` (Issue Form `owner-input.yml`, posted by the Owner) is an Owner instruction, quoted and time-stamped by GitHub. The coordinator handles it next cycle (protected items via OwnerTeammember first), answers on the issue `HANDLED: …` or `NEEDS CLARIFICATION: …`, and closes it when handled.
- **OwnerTeammember ↔ TeamCoordinator** talk only through `FOR TeamCoordinator` posts in #1 and the coordinator's receipts (Owner, 15 Oct: "further you deal via post"); the Owner is not asked to paste between them.
- **Inbox #1** — instructions, Owner decisions (relayed), control/epoch notices, alerts.
- **Project status issue** (Grade 9: #6) — ONE status comment, edited in place (COORDINATOR EVIDENCE, §4).
- **Evidence thread per agent** — one issue per agent chat, `[Evidence] <project> · <role> · <chat id8>`. Agents append TASK EVIDENCE v2 blocks; OwnerTeammember replies there with the grounding verdict.
- **The chat** — the same block appears at the end of the agent's reply, plus the link to its GitHub copy.
- **Action log** (Owner, 15 Oct: "same ... CoordinatorLandingpage ... project wise > session wise"): `logs/<project>/<YYYY-MM-DD>_epoch<N>/events.jsonl` (one JSON line per action: time, actor, action, target, exact text sent, result, links) and `raw/<chat id8>/turn-<n>.md` (full text of each agent reply, saved once). Layout and fields: `logs/README.md`. Source for the Owner's dashboard (to be programmed later). Pushed as one commit per cycle.
- Public repository: facts and links only. Full chat URLs, drafts, tokens and transcripts stay out.

## 3. Agent evidence — TASK EVIDENCE v2

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

## 4. Coordinator evidence — COORDINATOR EVIDENCE v1

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

## 5. Cycles

**TeamCoordinator — smart cadence:** 10 min while an agent is working or was just sent something · 15 min while agents wait on another agent or CI · 30 min while everything waits on the Owner.
**Routine cycle = 3 steps:**
1. ONE batched read: new evidence comments, #1, PR/CI changes since the last cycle (IDs and hashes first; each new body read once).
2. ONE look at the tabs: working / idle / error / full (state only, not text).
3. Act and record together: for an idle agent with no gate, nudge with **its own `Next:`** ("proceed with G9C-T4 …"); route a finished coder block to the validator; ONE status edit.
**Quiet cycle = 1 step, no write.** Runner changes are tested and versioned outside the live loop, never patched mid-cycle.

**OwnerTeammember — event-driven:** a local waiter polls GitHub each minute (no model tokens) and wakes on a new evidence block, a new #1 comment, or a change in a status row's State/Needs-you; plus a **silence guard**: TeamCoordinator's last completed cycle older than 15 min → wake and check. Per new evidence block: 1–2 steps.

## 6. Grounding from the evidence

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

## 6b. FOR TeamCoordinator — when OwnerTeammember instructs the coordinator (Owner, 15 Oct: "lets start using")

Only by exception, as ONE comment in inbox #1, in this form:
```text
FOR TeamCoordinator · <project> · <TYPE> · <id>
Do: send to <agent id8> word for word: "<text>"   |   <action for the coordinator>
Why: <one line> · Evidence: <links>
```
TYPE: **RELAY** (an Owner decision, quoted with time; always) · **CORRECTION** (a verdict that must reach the agent's chat) · **ROUTE** (a finished step not routed within one coordinator cycle) · **STATUS** (status wrong vs GitHub, a missing Needs-you item, or no completed cycle for 30 min) · **BREACH** (send to a retired chat, hold ignored, wrong epoch, claim treated as accepted) · **GATE** (a milestone claim: freeze both agents' commits for the final check before the Owner's acceptance card).
The coordinator acts on it in its next cycle and posts a receipt that names the id (`FOR-TC <id> → DELIVERED | NOT_SENT <why>`). Never used for routine nudges, task choice, engineering, or anything that still needs the Owner's approval.

## 7. Authority

Protected: merge, release/publish, new chat, upload, change of writer or role, acceptance (academic, QRT, source rights). Only the Owner decides. OwnerTeammember relays a decision only as: `OwnerTeammember — relaying Owner decision. Source: Owner chat, <time>. Owner's words: "<quote>". Action / Target / Limits: …`. A prefix alone is never approval.
**Standing approvals in force for the Grade 9 pilot:** pilot cycles up to 10× tokens for 24 h (15 Oct); option B (v3.6 managed lifecycle off); BuddyRunner v1.7 for new handovers; 10-min cadence. **Owner, 15 Oct ~07:25:** *no* standing approval for replacing an agent ("no approval follow protocol in your skill"): a new chat for a dead agent only on the Owner's word. Timeouts in §8: approved ("ok"). OwnerTeammember as stand-in TeamCoordinator during a TeamCoordinator outage: approved ("ok").

## 8. Guards, fallback, takeover

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

## 9. Handover and new agents

New handovers use **BuddyRunner v1.7** (`skills/buddy-runner-v1-7` at 8405c9d9). One-step handover: the outgoing agent writes the complete handover file (final direction, first workpack, the twelve sections of v1.7 `2_RECONCILE.md`, anchors to re-verify, open decisions) and stops. The successor's first reply answers the v1.7 own-words questions (role and predecessor, authoritative inputs and approval scope, original-issue gap, up to three highest-value steps with a falsifier), then posts TASK EVIDENCE v2 #1 in its new thread.

## 10. Onboarding a chat to this protocol (one message)

> Team protocol v1 applies from now: <link to this issue>. Your evidence thread is <link>. From your next reply: end every reply that finishes a task with TASK EVIDENCE v2 (section 3, exact layout) and post the same text as a new comment in your thread; replies that finish no task end with the STATUS v2 line. First: post TASK EVIDENCE v2 #1 for the work you just finished (<what>) in your thread — this is also the access test; if you cannot comment there, say NOT_POSTED and why. <one grounding note from §6>. Then continue with <its own Next>.

## 11. Economy

Targets: quiet cycle 1 step and no write; routine TeamCoordinator cycle ≤ 3 steps; OwnerTeammember 1–2 steps per new evidence block; every status shows `steps · ~tokens`. Measured after one pilot day: tokens per finished task, minutes from block to next nudge, grounding corrections.

## 13. Workflow card (per project)

The Owner's loop for the project, in the Owner's words, with the current step. It lives in the registry (`workflow`) and in the status header. Only the Owner changes it; a change is relayed in #1 with the quote and time, and every active agent gets one message with the new card. Example (Grade 9): *"QRT tile by tile: idea is to design a validator (by one agent), fix existing standalone html based on validator outcome (another agent), check and fix the validator if required"* → validator checks a tile → fixer fixes via source + builder → validator re-runs and fixes itself where wrong → 0 FAIL → next tile.

## 14. Changeover (Owner-ordered replacement, or takeover)

1. **Freeze** the outgoing chat: if it is working, press Stop; read back its branch/PR heads; wait one cycle and confirm no new commit or evidence arrives.
2. **Retire**: one line in its evidence thread and a notice in #1 (Owner's words + time); registry → `retired`.
3. **Handover issue** = the new agent's evidence thread, body = handover: role and loop (workflow card), repository state with exact commits, reusable prior work, known findings, open Owner decisions, boundaries, reporting, first reply. Written by the **coordinator** when the Owner orders the change or the workflow changes; by the **outgoing agent** (BuddyRunner v1.7 one-step) when it is alive and the workflow is unchanged. Built from the evidence threads and GitHub, never from memory.
4. **New chat** (only on the Owner's word): one-paragraph start prompt pointing to the handover issue and this protocol. Count and roles must be clear (§16).
5. **First reply** = v1.7 own-words answers (role and predecessor, authoritative vs candidate inputs, what it may not change, first step). OwnerTeammember checks them (§6) before the agent's first material change.
6. **New branch** from the last confirmed commit; old branch frozen. Registry, status and log updated; a coordinator never sends to a retired chat.

## 15. Drift rule

A block that does not advance the current workflow step → one grounding question back to the step. Three analysis-only blocks in a row from an implementing agent → "What can you fix now?". Reports for the Owner are produced only when the Owner or the workflow asks for them.

## 16. Ambiguity rule

An Owner instruction that would trigger a protected action (new chat, merge, release, upload, writer/role change, acceptance) and is unclear in count, roles or scope → one-line confirmation first, unless an earlier Owner instruction settles it; then name that instruction in the relay.

## 17. Bringing in another coordinator (bootstrap)

A new TeamCoordinator (any capable agent with GitHub comment access and control of the agent chats) starts **observe-only**: it reads this protocol and the registry, answers in its own words (roles, its 3-step cycle, what it must never do, what it would do in its first cycle), and posts one COORDINATOR EVIDENCE block with **no sends**. OwnerTeammember checks the answers and the block against the registry and the chats. Control passes only on the Owner's word: `CONTROL epoch N+1: <who>` in #1, registry updated, the previous coordinator stops sending.

## 19. Rules added from the stress test (v2.1)

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

## 18. Open Owner decisions

Decided 15 Oct ~07:25: no standing approval for agent replacement (Owner decides each case); timeouts approved; stand-in during an outage approved.
Open: **freeze v2.1** (one word: "freeze"). **Watchdog workflow** (§1): a scheduled GitHub Actions job, every 15 min, reads the status comment's "Cycle completed" time and, if older than 45 min, opens/updates an alert issue mentioning the Owner. It runs on GitHub, not on the home computer, so it still alerts when the computer or both sessions are down. Free on a public repository, no AI; blind during a GitHub outage.
