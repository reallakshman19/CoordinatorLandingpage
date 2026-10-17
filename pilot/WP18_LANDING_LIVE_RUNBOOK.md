# WP18 — landing-live UltraEconomyMode v1 single-cycle pilot runbook

**Status: PREPARED ONLY — NOT ENABLED.** This is a test/review playbook, not an authorization, agent instruction, timer, or applied registry change. Owner's 16 Oct 22:42 "ok implement your reconciled plan" authorizes preparation of WP16–18, **not** immediate UEM activation. The separate [proposed patch](landing-live-uem-v1.proposed.patch) is NOT APPLIED to `logs/landing-live/registry.json`. The actual source registry has no `ultra_economy` key.

## Who can authorize and write

**Owner** must supply new, explicit Owner words allowing landing-live UEM activation with `max_cycles: 1`, the exact bounded work item, named current implementer, permitted writer scope and duration, and whether any timer is authorized (a timer is **optional and not required** for activation; the default pilot runs with no timer, see the timer authority boundary below). Do not infer enablement from the general 22:42 GO, a pasted example, a task comment, or a separate Next Move grant. Reviewer must independently confirm the live Owner words, current main/feature-head and recorded HOLD.

**TeamCoordinator, acting also as OwnerTeammember**, is the sole designated pilot registry/source custodian under an Owner-authorized scoped PR after C1 review. This actor must (1) commit the Owner-approved registry opt-in and source-scoped **execution grant**, separate **monitoring grant**, and an initial `cycle_ledger` for the workplan/task; (2) after seeing the live START comment on GitHub, re-read its canonical URL, numeric comment ID, `updated_at`, and SHA-256 of the entire UTF-8 body, then propose a new audited registry `source_bindings` entry by checked PR; (3) after END, do the same for END's source binding and update `completed_cycles` to 1 **only after the work unit and independent evidence are reconciled**. Each registry/ledger/source binding update needs the appropriate scoped authority and independent checkout/CI, not an implementer's self-approval. The implementer must not write its own proof anchors or reset the ledger.

The **independent C1 checker** verifies Owner scope, immutable comment source and exact PR HEAD, live HOLD/retirement/successor qualification and competing lease, grants' finite expiry, and UEM cycle ledger before an agent is permitted material action. Check actual source rows, not the page's summary or a typed author role. Unknown/missing/edited/duplicate START or END, changed source HEAD, or missing roster row means **HOLD**, not "proceed." The TeamCoordinator remains responsible for recorded approval and supervised chat delivery, never automated sends.

## Prepared opt-in (no registry write)

The prepared single-line diff is:

```json
"ultra_economy": {"enabled": true, "max_cycles": 1}
```

It must not be applied without the separate Owner activation words and a checked, independently reviewed registry PR. Enabling alone is **insufficient**: the UEM parser also requires the authoritative top-level active roster identity, matched owning evidence issue, per-comment `source_bindings`, finite verified `execution_grants[id8]`, independent `monitoring_grants[id8]`, and a persistent `cycle_ledger[workplan URL + "|" + task]`. Work is stopped while a START is being independently pinned; posting START does not confer permission. Use the actual 40-hex PR HEAD in the Next Move basis; do not copy an old head across a handover. Never enable any other project under this plan.

## Exact proposed TASK START comment (do not post from this runbook)

Only the specifically authorized implementer (currently landing-live L1 g2 id8 `6ad1a045`, subject to fresh registry/readback) may post **one** START in registered GitHub issue #22 for the Owner-approved task X. Replace `<OWNER_APPROVED_TASK>`, `<...>` values with verified, real facts; the workplan issue URL must be genuine and in the owning repository. For the prepared landing-live example use the real workplan issue #21, provided Owner approval actually covers the chosen task.

```text
TASK START v1 · landing-live · implementer · chat 6ad1a045 · task <OWNER_APPROVED_TASK> · cycle 1/1
Planned outcome: <one objectively checkable bounded result>
Expected next: <independent exact-head check, then an authorized decision>
Known blocker: NONE | <specific verified blocker>
Workplan: https://github.com/reallakshman19/CoordinatorLandingpage/issues/21
Fallback: NOT_ARMED no Owner-authorized host timer
```

The START is **not source-bound** until the TeamCoordinator has fetched the committed GitHub comment and separately pinned `https://github.com/reallakshman19/CoordinatorLandingpage/issues/22#issuecomment-<actual numeric ID>`, `comment_id`, `updated_at`, and `body_sha256` in the checked registry. Re-fetch the source immediately before any claim; changed text or duplicate IDs/STARTs invalidate that claim. The agent may describe a plan but must not start material work until this and the current grant/HOLD/lease checks pass.

## Exact proposed TASK END/EVIDENCE comment (do not post from this runbook)

The existing full TASK EVIDENCE v2 is unchanged. Post **one** END comment using the same role, chat id8, first task token X and exactly `UEM cycle: 1/1`. Record actual tests, exact head, source links and HOLD with no fabricated Owner acceptance. This abbreviated example shows the required operational lines; the actual completed comment must contain all mandated TASK EVIDENCE v2 evidence fields.

```text
TASK EVIDENCE v2 · landing-live · implementer · chat 6ad1a045 · #<actual sequence> · <actual timestamp>
Task: <OWNER_APPROVED_TASK> — bounded unit and immutable source result
Status: ENGINEERING DONE / independent checker pending
Did: <actual changes, or explicit no-change finding>
Where: <real PR URL and exact 40-hex head>
Proof: <actual hosted CI run/job or explicit local-only>
Not done / HOLD: <remaining risks and unapproved decisions>
Needs TeamCoordinator: independent exact-HEAD review, handover decision
Next: STOP pending an authorized Next Move
UEM cycle: 1/1
```

TeamCoordinator alone prepares the independent END source binding, separately verifies that the END matches the same task/cycle/recipient and observes the immutable GitHub `updated_at` and body digest. **No END is a send, and no proposed heartbeat is a recorded Next Move approval.**

## Independent observer's five-stage control

1. **START:** Owner's specific enablement words and authorized scope checked; live project not HOLD; registered non-retired qualified agent; no competing exclusive writer; valid execution grant independent of monitoring grant; exact owning START source pin; `completed_cycles = 0` for `<workplan URL>|<task>`. If any guard unknown, fail closed. No work from an agent's unverified START claim.
2. **END:** One full TASK EVIDENCE v2 with `UEM cycle: 1/1`. Source-bound immutable ID/updated_at/digest and exact PR HEAD verified independently; duplicates, edited text or wrong source block. Once done, the TeamCoordinator updates the source ledger under a separate reviewed change. The single-cycle budget is exhausted; a restart or replacement chat cannot refill it.
3. **Approved Next Move:** A distinct validated `Dispatch` references the same owning evidence URL, END comment ID, task X, cycle 1 and exact current PR HEAD, with a human-authenticated `APPROVED` transition at the proper tier (landing-live normal: Owner or OwnerTeammember; self-approval **labelled**, not excused). A prefilled Owner-input JSON **request** is not effective approval. Check `PUBLISHED → APPROVED → CLAIMED` in the actual ledger.
4. **Delivery:** A recipient-matched claim file with a ≤15-minute lease, unique active dispatch, `SEND_INTENT` then real, witnessed `SENT_TO_CHAT` proof. Merely posting a GitHub comment or approval does not establish chat delivery. If send is uncertain, keep `DELIVERY_UNCERTAIN` pending explicit reconciliation, and do not retry automatically.
5. **Pickup/stop:** Independent observer confirms the actual recipient's `PICKED_UP` (and any ACK if available) from source evidence. This is **not** Owner acceptance. As `max_cycles = 1`, even a properly delivered/picked-up Next Move cannot start a second UEM cycle. Record the final non-action, remaining HOLD and any separate human-governed work decision. No scheduler, new chat, second START/END, move, claim, or send is produced on replay.

## Timer authority boundary

Fallback timer state is **NOT_ARMED** now and throughout this WP18 prep. To consider arming a future task, TeamCoordinator must obtain **explicit Owner words** authorizing that particular timer and its scope and then collect **creation proof** (host-confirmed task ID/receipt). The default future timer design is **one fire**, not a recurring hourly loop; after the one fire, verify **cancellation**/completion with host evidence and record that fact. A second fire, recurring task, missing cancellation receipt or pasted `ARMED` text is not authorization. No automation tool has been called and no task created. Even a later authorized single fire is **read-only monitoring**, never an execution or send grant.

## WP18 negative evidence matrix

The checked-in `tests/test_wp18.py` replays JSON-serialized, GitHub-API-shaped comments (`id`, `created_at`, `updated_at`, full `body`) and exact pinned body SHA-256 against the production UEM projector and existing Next Move validator/claim helper. It checks: HOLD before END, retirement after START, stale PR head, expired execution grant, edited START/END, duplicate START/END, unresolved SEND_INTENT, missing/duplicate authoritative roster rows, unavailable/self-claimed ARMED timer, same-unit restart and final cycle ceiling, two competing active claims to one recipient (both rejected), actual claim-create refusal before any Contents PUT, and no duplicate START/END/move/send/timer or source mutation on a second read-only replay. All input registries/claims/moves are **temporary synthetic test copies**; no production registry, comment, chat, task or PR HEAD is altered.

The pilot is **prepared, not executed or accepted**. Independent WP18 review and later explicit Owner activation precede any real opt-in.
