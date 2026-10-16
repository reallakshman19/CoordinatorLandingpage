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
2. If a ChatGPT scheduled-task capability is available, **invoke it once** to
   create an hourly fallback source check. Use a recurring hourly cadence
   (one check per hour, not every 15 minutes). Bind the actual project, task X,
   agent id8, evidence issue and coordinator inbox; ask it to notify only when
   the task needs action and to avoid inventing send/approval. Save the real
   task identifier/receipt. Do not claim ARMED before host confirmation.
   If unavailable, state `NOT_ARMED:<reason>`. Do not create another timer
   for each UEM cycle.
3. Post a new comment in the registered evidence thread:

```text
TASK START v1 · <project> · <role> · chat <id8> · task <X> · cycle <n>/<limit>
Planned outcome: <observable result of this one unit>
Expected next: <expected next task/review>
Known blocker: NONE | <specific known blocker>
Workplan: https://github.com/<owner>/<repo>/issues/<number>
Fallback: ARMED <actual host task reference> | NOT_ARMED <reason>
```

4. Re-read your own comment URL and confirm it exists before making material
   changes; do not treat composing a comment as publishing it.

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
   delivery gates, recheck your own grant and start the next cycle only when
   n < limit. Otherwise record `WAITING_NEXT_MOVE` and stop your reply.
   Never loop by assuming the draft is approval.
5. On terminal COMPLETE/HOLD/STOP or limit exhaustion, mark the task stopped
   and disable/cancel the hourly fallback if the host supports it; otherwise
   report the outstanding timer clearly.

## On hourly wake

Read only the scoped GitHub delta and the current task. Check whether the
coordinator has replied or a linked Next Move changed; report an unresolved
status, verified response or stale/missing source. Do not autonomously send
to an old ChatGPT chat, create a new agent, edit authority, approve, merge,
release, or claim acceptance. A scheduled wake does not grant execution power.

## Economy and safety

One START and one END per cycle. Maximum five cycles per task. No duplicate
GitHub comments, no repeated transcript reads, no polling inside an agent
reply, no invented timer receipt, no competing Next Move ledger.

This is an **agent instruction skill**, not an installed scheduler or a
guaranteed native background resume mechanism. It becomes operational only
when the agent is explicitly instructed to use it and the required GitHub /
scheduled-task tools are available and authorized.
