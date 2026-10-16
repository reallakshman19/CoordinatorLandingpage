# UltraEconomyMode v1 — agent-led bounded workplan loop

**Status:** Draft implementation, opt-in only. Preserves `protocol/TEAM_PROTOCOL.md`,
`protocol/NEXT_MOVE_v1.md`, Owner approval, BuddyRunner and existing Pages publisher.
**Parent:** [CoordinatorLandingpage #21](https://github.com/reallakshman19/CoordinatorLandingpage/issues/21).

## Purpose

Reduce repeated coordinator/agent turns. At the beginning of one workplan task X,
the agent declares its planned outcome, expected next step and known blocker in its
**registered GitHub evidence issue**. It executes X, publishes the existing
TASK EVIDENCE v2, then reads the latest authoritative Next Move. The cycle repeats
only while an applicable, fresh, properly delivered instruction is available.
The limit is configured 1–5, defaulting to **disabled** until explicitly enabled.

No new process map, backend, automation platform, task ledger or authorization
mechanism is introduced. A TASK START is an **agent claim**, not Owner approval.

## Opt in

Add this field only to a project registry under an authorized change:

```json
"ultra_economy": {"enabled": true, "max_cycles": 3}
```

Valid max_cycles: integer 1 through 5. Missing config, invalid values (including
boolean or string) or disabled config result in no UEM task execution projection.
Existing projects remain unaffected.

## Agent operating contract

1. Read project/Owner aim, assigned work item, permissions and HOLD before starting.
2. Arm **one** recurring hourly ChatGPT scheduled task (when that capability is
   available in the agent runtime), scoped to the current project, agent id8,
   evidence issue and workplan task X. If task creation is unavailable, state
   **NOT_ARMED** in the evidence rather than claiming success. Do not create a
   new hourly task on every cycle.
3. Publish an append-only TASK START v1 comment to the registered evidence issue
   **before engineering begins**, with all required fields:

```text
TASK START v1 · landing-live · implementer · chat 11111111 · task WP16 · cycle 1/3
Planned outcome: Implement the next scoped unit with source evidence
Expected next: Independent exact-HEAD review after tests
Known blocker: NONE
Workplan: https://github.com/reallakshman19/CoordinatorLandingpage/issues/21
Fallback: ARMED <host task receipt> | NOT_ARMED <reason>
```

4. Perform only the currently authorized work. End with the unchanged
   TASK EVIDENCE v2 body and the additional non-authoritative correlation line
   `UEM cycle: 1/3`. The first token after `Task:` must be `WP16`.
   The existing `Did`, `Not done / HOLD`, `Needs Owner`, `Next`
   and `Proof` fields still apply.
5. **Immediately after publishing the END record**, read GitHub's newest
   validated Next Move, the actual registry, HOLD and current PR HEAD. A matching
   move uses the existing fields and a strictly correlated trigger:

```json
{
  "class": "Dispatch",
  "kind": "next_step",
  "to": {"role": "implementer", "id8": "11111111"},
  "trigger": {
    "type": "uem_end", "task": "WP16",
    "cycle": 1, "end_comment_id": 102
  },
  "basis": {
    "evidence": "https://github.com/reallakshman19/CoordinatorLandingpage/issues/22",
    "head": "<actual 40-hex PR HEAD>",
    "registry_sha": "<actual 40-hex registry blob SHA>"
  }
}
```

   The example is a **partial specification**. Full Next Move schema, transitions,
   actor checks and approvals remain governed by NEXT_MOVE v1. UEM never creates,
   approves, claims or sends the move.
6. Only a validated, recipient-matched, source-fresh **SENT_TO_CHAT** (or
   subsequently PICKED_UP/ACKED) move can be surfaced as
   `NEXT_MOVE_RECORDED_DELIVERED`. A proposed move, approval request, APPROVED
   transition, GitHub issue publication or PUBLISHED_TO_THREAD does **not**
   establish chat delivery. Even on delivered status, the agent rechecks
   custody, grant and HOLD before starting the next scoped cycle.
7. Stop on HOLD, unsupported/missing evidence, uncertain delivery, explicit
   terminal decision, role retirement or reaching the configured maximum.
   Do not start cycle 6 of 5. A fresh authorized task Y may start its own
   independently configured cycle 1.
8. Stop/cancel the recurring ChatGPT task on terminal completion. If the
   scheduler does not support programmatic cancellation from the agent,
   ask for explicit user action and mark it as still active/unknown.

## Hourly fallback instruction (agent uses native ChatGPT scheduling)

```text
Every hour, check the registered GitHub evidence issue for TASK START v1 and
TASK EVIDENCE v2 on workplan task WP16, chat 11111111, and the corresponding
CoordinatorLandingpage Next Move. Only report a missing/changed answer,
stale source, HOLD, delivery uncertainty, or an actionable and independently
authorized transition. Do not create/approve moves, send to chats, change agents,
merge, deploy or advance the workplan by yourself. Stop this recurring task
after verified terminal completion or cancellation; otherwise retain it.
```

The host ChatGPT agent must actually invoke its native scheduled-task capability;
this repository cannot create ChatGPT Tasks from a static GitHub Pages site.
A line saying ARMED without a host receipt remains agent-reported only.
An hourly scheduled task is a **fallback source checker**, not a guaranteed
automatic resumption of the original conversation.

## Coordinator and follow-ups

Existing Coordinator/OwnerTeammember uses TASK START context alongside its own
Owner context to prepare an evidence-bound Next Move. Upon END, the agent reads
the current result once. If none is delivered, it stops rather than guessing.

The read-only publisher computes follow-up due times at END+15/+20/+30.
This **does not schedule** GitHub reads itself. A separately authorized watcher
may consume those due times, taking care not to conflate coordinator ACK,
PUBLISHED_TO_THREAD and SENT_TO_CHAT. The project evaluator and landing page
remain read-only sources of observations, not senders.

## Source paths

- `skills/ultra-economy-mode/SKILL.md` — an opt-in agent operating contract for publishing START/END, invoking one native hourly fallback and performing immediate GitHub readback; it is not a scheduler.

- `scripts/ultra_economy.py` — derive task lifecycle, cycle cap, exact-match move,
  source status and follow-up due times.
- `scripts/build_data.py` — attach UEM to existing `next_move` projection
  only for opt-in projects.
- `site/app.js` — render UEM facts in existing Next Move views, with no button
  to auto-approve or send.
- `tests/test_ultra_economy.py` — positive and negative source/authority fixtures.

## Qualification boundaries

A positive UEM demo should prove START → END → delivered matching Next Move →
eligible next cycle with independent source links. Negative controls must reject
wrong task/comment/cycle, stale HEAD, missing/unknown evidence, paused/retired
recipient, unpublished/undelivered moves, duplicate matching moves, project HOLD,
invalid cycle count and cycle limit exhaustion.

**Not provided by this draft:** a live ChatGPT task receipt, any automatic native
ChatGPT conversation wake-up, public-site deployment, protected approval,
coordinator-generated actual moves or a verified two-repository acceptance.
