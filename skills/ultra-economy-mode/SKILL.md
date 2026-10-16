# UltraEconomyMode v1 — agent execution skill

Read the governing project registry, Team Protocol v2.3, NEXT_MOVE v1, the
assigned workplan issue and current source state BEFORE using this skill.
This skill is **opt-in** and does not supersede any approval, custody, HOLD,
review, BuddyRunner, merge or release boundary.

## Trigger / parameters

Enable only when the registered project's `ultra_economy.enabled` is true
and integer `max_cycles` is in 1..5. Resolve current project, assigned task X,
active agent id8/role, evidence issue, workplan issue, grant and exact PR HEAD
from GitHub. Do not guess missing data. The configured cycle ceiling applies to
this task X; stopping early is always permitted.

## At START of workplan task X

1. Decide the next bounded unit from Owner aim and your grant. Describe in
   plain words: `Planned outcome`, `Expected next` and `Known blocker`.
2. **Timer is NOT_ARMED by default.** Do not create a ChatGPT timer/scheduled
   task in this WP17 work or suggest that the GitHub page armed one. Timer
   creation requires a separate explicit Owner authorization and a real
   authenticated host receipt. Even a text field saying ARMED is only an
   unverified agent claim and never changes the read-only NOT_ARMED state.
   This procedure never schedules a wake or resets a timer on restart.
3. Post a new comment in the registered evidence thread:

```text
TASK START v1 · <project> · <role> · chat <id8> · task <X> · cycle <n>/<limit>
Planned outcome: <observable result of this one unit>
Expected next: <expected next task/review>
Known blocker: NONE | <specific known blocker>
Workplan: https://github.com/<owner>/<repo>/issues/<number>
Fallback: NOT_ARMED no authorized host receipt
```

4. Re-read the actual START comment and its owning issue. Before any
   `WORKING_CLAIM`, a coordinator-reviewed registry source pin must match
   **START URL + comment id + updated_at + SHA-256 digest of entire body**;
   any missing/edited/duplicate record invalidates the claim. Recheck project
   HOLD, retired/unqualified successor, exclusive writer-lease conflicts, and
   an unexpired verified execution grant scoped to this id8/project.
   Monitoring grant is separate; it never authorizes execution. Do not treat
   composing a comment or self-reported chat text as published authority.

## At END of the task

1. Publish unchanged TASK EVIDENCE v2 with actual work, tests, proof and
   `Not done / HOLD`. Use `Task: <X> ...` (same first token as START)
   and one extra metadata line `UEM cycle: <n>/<limit>`.
2. Read back the new GitHub END comment and exact current PR HEAD.
3. Read Next Move from authoritative GitHub records **now**, even if the
   hourly fallback has not fired. Match recipient id8, X, n, END comment ID
   and evidence issue. Reject no-match, duplicates, stale basis, wrong HEAD,
   HOLD and undelivered/uncertain actions. An instruction published only
   on an issue is NOT automatically a message delivered to this chat.
4. If a matching Next Move has already passed the existing authorization and
   delivery gates, recheck **current** HOLD, source binding, writer lease, grant,
   exact head, and persisted per-task UEM cycle ledger before any further
   work. The next cycle is permitted only for n < limit and recorded
   completed_cycles=n (so a restart/handover cannot reset to cycle one).
   Next Move task counter and Owner delegation cycle never refill UEM credit.
   Otherwise record `WAITING_NEXT_MOVE` and stop your reply.
   Never loop by assuming the draft is approval.
5. On terminal COMPLETE/HOLD/STOP or limit exhaustion, mark the task stopped
   and report fallback as NOT_ARMED. No timer cancellation or creation is
   performed without a separately verified real host receipt and authority.

## Future hourly wake (not enabled by WP17)

No timer is armed. If a later Owner-approved, host-confirmed task exists,
any wake must only read a scoped GitHub delta and cannot grant a send,
execution, custody change, merge, release or automatic continuation.

## Economy and safety

One START and one END per cycle. Maximum five cycles per task. No duplicate
GitHub comments, no repeated transcript reads, no polling inside an agent
reply, no invented timer receipt, no competing Next Move ledger.

This is an **agent instruction skill**, not an installed scheduler or a
guaranteed native background resume mechanism. It becomes operational only
when the agent is explicitly instructed to use it and the required GitHub /
scheduled-task tools are available and authorized.
