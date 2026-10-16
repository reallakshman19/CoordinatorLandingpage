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
2. **Fallback is NOT_ARMED** under WP17: no timer, scheduler, auto-wake or
   background send may be created. A written claim of ARMED is unverified.
   A future explicit Owner authorization and actual host task receipt are
   required before any separate timer change.
3. Publish an append-only TASK START v1 comment to the registered evidence issue
   **before engineering begins**, with all required fields:

```text
TASK START v1 · landing-live · implementer · chat 11111111 · task WP16 · cycle 1/3
Planned outcome: Implement the next scoped unit with source evidence
Expected next: Independent exact-HEAD review after tests
Known blocker: NONE
Workplan: https://github.com/reallakshman19/CoordinatorLandingpage/issues/21
Fallback: NOT_ARMED no authorized host timer
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

- `skills/ultra-economy-mode/SKILL.md` — an opt-in agent operating contract for publishing START/END, recording NOT_ARMED until separately Owner-authorized one-shot creation proof and performing immediate GitHub readback; it is not a scheduler.

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


## WP17 source and authority gate (before any working claim)

The registry must explicitly opt in, then pin START **and** END GitHub comments
using a reviewer-sourced, immutable \`ultra_economy.source_bindings\` keyed by
decimal comment ID. Each entry is
\`{url, comment_id, updated_at, body_sha256}\`, with URL
\`https://github.com/<owning-repo>/issues/<n>#issuecomment-<id>\`.
The SHA-256 is of the full UTF-8 body. A refetched edit (body or updated_at),
missing anchor, unexpected owning repository, or duplicate START/END is
**not** an authorized working claim or delivered Next Move. These values
cannot be supplied just by the author of the comment.

The registry also has distinct \`monitoring_grants\` and \`execution_grants\`
per public id8, each with verified=true, holder_id8, project and finite
expires_at. **Monitoring never grants write/execution.** Before any working
claim the publisher checks an unexpired execution grant, live project HOLD,
retired/STOP status, unqualified successor/adoption, and competing exclusive
writer lease. A result is a read-only assertion, not a GitHub write grant.
Missing or invalid fields remain blocked.

The separately persisted \`cycle_ledger\` maps \`<workplan issue URL>|<task>\` to
\`{completed_cycles:n}\`. START cycle must equal n+1; no chat restart,
handover, registry reload or changed Next Move task counter resets it.
A delivered move is never permission unless *all* source and authority
checks pass. This ledger must be updated only through separately authorized
recording of a completed cycle; WP17 does not write it. Owner delegation
cycles and Next Move task-evidence counters are distinct and do not refill
the UEM task budget.

**Timer remains NOT_ARMED.** No timer/scheduler, auto-send, new chat,
GitHub-pull delivery or other project's pilot is activated by this branch.


## WP18 single-cycle prepared pilot: do not apply

The landing-live single-cycle diff is staged **only** at `pilot/landing-live-uem-v1.proposed.patch`; it has **NOT** been applied to any registry. The procedure and source-custody roles are in `pilot/WP18_LANDING_LIVE_RUNBOOK.md`. `ultra_economy.enabled=true` with `max_cycles=1` requires new explicit Owner approval before a separate registry PR. The TeamCoordinator (acting as OwnerTeammember) is the named custodian who proposes reviewed START/END URL/comment_id/updated_at/body_sha256 bindings and the persisted workplan-task `cycle_ledger` and separate grants. The implementer cannot self-certify those entries.

A future host timer, if ever approved, requires **Owner words** specific to that timer and scope, independently verified **creation proof** with real host task ID, **one fire** only, and verified **cancellation** or completion. Default and WP18 state remain **NOT_ARMED**; no timer or task is created here. Timer monitoring gives no write, execution or send authority. Reviewer must check the claim and delivery ledger independently (START -> END -> APPROVED -> CLAIMED -> SEND_INTENT -> SENT_TO_CHAT -> PICKED_UP), recognizing that a finished single cycle cannot be restarted even after successful pickup. Replay adds no duplicate comments, moves, sends or timers.
