# NEXT MOVE v1: specification

**Status: ADOPTED v1.0 for PILOT on `landing-live` only.**
- Owner, 16 Oct 2026 ~19:3x: "review cycle is over. start planning and implement. any difference, now you dictate (if genuine else adopt)".
- Reviewed by Codex twice (plan rev 1 and spec draft); every genuine point is adopted (see §11).
- Written by OwnerTeammember + TeamCoordinator.
- Other projects join only on the Owner's words.

Dubai time (+04:00). Public repo: 8-character chat ids only; no secrets or credentials.

---

## 1. Purpose
A **Next Move** is an auditable record of **who should do what next, why, on what basis, and with whose approval**. It executes nothing: an accountable actor still does the work and proves it. Uses:
- the next step from known status;
- a new requirement;
- a course correction;
- grounding and reconciling a working agent (task cycles 5/10/15/19);
- handover;
- a label request;
- coordinator alignment (e.g. a Codex skill vs this protocol);
- agent added or retired.

## 2. Words used precisely
| Term | Meaning |
|---|---|
| **task cycle** | one evidence block posted by the working agent for the current work item, counted on GitHub (§6.1) |
| **coordinator cycle** | one run of the coordinator's timer (15 min) |
| **delegation allowance** | the Owner's "N cycles" for auto-response, converted to a clock time when given |
| **criticality** | registry `criticality: critical \| normal`, **set only by the Owner's words**. It is separate from `auto_response`. A project with no value is treated as **critical**. |

## 3. Classes
| Class | Effect | Approval in the pilot |
|---|---|---|
| **Dispatch** | asks someone to act | **required** (§5) |
| **Notice** | records a fact (agent_added, agent_retired, EVALUATED heartbeat) | none; **authorises nothing** |

## 4. Files and states
- `logs/<project>/moves/NM-YYYYMMDD-HHMMSS-xxxx.json`: one immutable file per move. Fields: `id, project, class, kind, from{role,id8}, to{role,id8}, text, basis{evidence, head, registry_sha}, trigger, supersedes, evidence_format, created_at`.
- `logs/<project>/moves.jsonl`: append-only transitions `{move, state, by, at, proof, note}`.
- `logs/<project>/moves/claims/<move-id>.json`: the claim file (§4.2).
- Existing files are **unchanged**: OI inputs, receipts, registries, evidence threads, protocol pins.

### 4.1 Lifecycle
```
PUBLISHED → APPROVED → CLAIMED → SENT_TO_CHAT(proof) | PUBLISHED_TO_THREAD(link) | DELIVERY_UNCERTAIN | NOT_SENT
          → PICKED_UP (a real recipient response) → ACKED (own words, link) → DONE_CLAIMED(link) → VERIFIED(by a non-doer)
side states: REJECTED · HELD · SUPERSEDED(by id) · CANCELLED · EXPIRED
```
- **SENT_TO_CHAT** needs chat-visible proof: the text shows as a user message, and the composer is empty or Stop is showing.
- **PUBLISHED_TO_THREAD** proves publication only. It is **not** delivery into a chat.
- **PICKED_UP** needs a real response from the recipient.
- **NOT_SENT** = a known unsent draft (for example, text left in the composer).
- **DELIVERY_UNCERTAIN** can't be cleared by a claim expiring. It must be **reconciled** first: someone checks the chat and records SENT_TO_CHAT or NOT_SENT before any sender proceeds.
- **VERIFIED means the phase or step happened as specified. It is not correctness or acceptance.** Acceptance stays with its owner.
- **HELD:** when a HOLD lifts, the move goes back to **PUBLISHED** and needs a fresh approval, with basis, grant and HOLD re-checked. It never returns straight to APPROVED.

### 4.2 Claims (conflict-safe)
- **Create** the claim file `moves/claims/<id>.json` through the GitHub Contents API with no `sha`. If the file already exists, the create fails, so only one claimer can win.
- **Renewing or taking over an expired claim** is an update with the current `sha`, a compare-and-swap. It is allowed only if the move is not DELIVERY_UNCERTAIN.
- **Immediately before sending**, the claimer re-checks authority, basis (has the head or registry moved?) and HOLD. Any change → release the claim and record why.
- Only one dispatch per recipient may be between CLAIMED and VERIFIED. Others wait in the queue, and replacing one needs an explicit `supersedes`.

## 5. Approval and grants
- In the pilot, **every dispatch needs APPROVED before CLAIMED.** Approval can become optional per project, only on the Owner's words. After that a valid `grant_ref` is needed: an Owner decision record with exact words, an in-date `auto_response` row, or a CRITICAL standing rule. The publisher checks it.
- **Approvers** (Owner, 16 Oct ~19:1x):
  - `criticality: normal` → the **Owner or OwnerTeammember**;
  - `critical` → the **Owner only**, except for the handover grant below.
- **Combined roles are one actor.** When one actor holds both TC and OTM, approving its own dispatch is **self-approval**. The page shows "self-approved".
  - Allowed only for `normal` projects (the Owner named OTM as an approver).
  - Never for `critical` projects.
  - Independence is supplied at VERIFIED, which is always done by a non-doer.
- **Critical handover grant (ruled; Owner may revoke with one word):** the Owner's standing words of 16 Oct ~11:3x, "approve takeover via buddy v1.7", are recorded as **standing pre-approval for H1–H3 only** (§6.3).
  - OwnerTeammember checks eligibility; it gets no general approval authority on critical projects.
  - Eligibility: a real trigger (§6.3), no HOLD, and the successor named in the registry.
  - Everything else on a critical project needs the Owner.
- **During the pilot, the existing cycle is unchanged.** Routine nudges and the three CRITICAL standing actions keep running as today, outside Next Move.

## 6. Triggers
**The publisher is not a scheduler.** It validates and displays.
**The evaluator is the active coordinator cycle.** Each cycle it:
- checks the triggers below;
- publishes the due moves;
- appends `{state:"EVALUATED", at, by}` to `moves.jsonl` (the heartbeat).

The page computes the same conditions from data it already reads, and shows:
- **"detected, not acted on"** when a condition has been true for more than 1 coordinator cycle + 5 min with no move;
- **"evaluator stale"** when there has been no EVALUATED entry for more than 2 coordinator cycles.

### 6.1 Task cycles 5/10/15/19 (Owner: "Task cycle based, to ground the working agent and reconcile")
- **Count** evidence blocks by the working agent(s) for the work item on its evidence thread, from the work's GO. The count follows the work across a chat changeover.
- **Period: 20 blocks.** Triggers fire when `n mod 20 ∈ {5, 10, 15, 19}`, i.e. at 5, 10, 15, 19, 25, 30, 35, 39, …
- **5, 10, 15 → `ground`** (to the working agent): restate the main aim and done-when in your own words, and say which outcome the last 5 blocks served. OTM compares the answer with the label or issue. Aligned → VERIFIED; drift → a `course_correction` for approval.
- **19 → `reconcile`**, using BuddyRunner v1.7 **Xb → Y**. Block 19 is Xb. The designated buddy (OTM, or the MemberCoordinator for its workers) gives **one** Y:
  - a correction, or CONTINUE / NO_CHANGE;
  - it covers the claims against GitHub (heads, CI, leases, open Owner decisions) and standby readiness.
  - Y is keyed by its canonical evidence key: repo, issue, task id, assessed commit, evidence digest.

### 6.2 Other triggers (real signals only)
| Trigger | Condition | Move |
|---|---|---|
| evidence_head_moved | `agents[].evidence.head` ≠ the PR's current head | reconcile |
| chat_end_seen | registry `chat_end_seen` ("maximum length", or "Could not load" twice) | handover_trigger |
| handover_meter | **a self-reported** value with a time at or above the warning level; otherwise "meter unknown" | handover_trigger |
| agent_registered_no_ack | a registry agent with no own-words ACK after 1 coordinator cycle | status_check |
| label_missing | pinned to Engineering PR Delivery v3.6, but there is no `relay/AIM/<WORK>.yaml` | label_request (to the Owner) |
| owner_decision_age | an `open_owner_decisions` entry older than 30 min | shown red; no dispatch |
| analysis_drift (protocol §15) | 3 analysis-only blocks in a row | ground ("What can you fix now?") |

### 6.3 Handover with BuddyRunner v1.7 (Common @ b92b6096)
**BuddyRunner defines** the phases, packets, digests and receipts. **Next Move only tracks and serialises** them. It keeps no second ledger and makes no exactly-once claim. The following are **project policy (Owner, 16 Oct), layered over BuddyRunner, not BuddyRunner rules**:
- standby timing;
- the coordinator acting as G1;
- same-cycle activation.

| Move | To | VERIFIED when | Boundary |
|---|---|---|---|
| H1 `buddy_1a` | G1. If G1's chat has ended: the coordinator acts as G1 from GitHub records, marking G1's claims as hypotheses (project policy) | a durable reference to the 1a packet (target, UTF-8 digest, `agent_invoked=false`) on the owning issue | execution HOLD; no G2 launch or product work |
| H2 `buddy_1b` | G2 | a durable reference to 1b: **either** published on the owning issue, **or** exact supplied text with a provenance ref and digest recorded by the coordinator. BuddyRunner accepts NOT_PUBLISHED; a missing publication never blocks analysis or reconciliation | no product coding; await 2 |
| H3 `buddy_2` | G1, or the coordinator acting as G1 (project policy) | a durable reference to 2, with its `handover.id` and the receipt recorded on the owning issue | no further round; **no G2 acknowledgement of 2** |
| notices | — | `agent_retired` G1; `agent_added` G2; leases and grants remapped (protocol §19.20) | authorise nothing |

- **Duplicates:**
  - Response **2** is identified by `handover.id`, and Y by its canonical evidence key.
  - A receipt for 1a never makes a legitimate 1b or 2 a duplicate.
  - A real duplicate 2 or Y gives `BUDDY_V17_DUPLICATE_RESPONSE_CLAIM`: verify the existing response; don't regenerate.
- **Standby onboarding** (project policy):
  - At the warning level, open G2 and run H1 and H2 while G1 is alive.
  - G2 counts as **onboarded** only when OTM **qualifies** its 1b: identity, source and scope grounding checked, not merely published.
  - Then G2 goes on HOLD.
- **Activation** (project policy) needs **all four**:
  1. the outgoing chat has stopped (ended, or told to stop and confirmed);
  2. no pending send to it (no CLAIMED or DELIVERY_UNCERTAIN move);
  3. a qualified successor;
  4. valid custody (leases remapped, no outside writes).

  Reaching "chat end" alone is not enough.
- Closed v1.6 handovers stay closed and are not migrated.

## 7. Page (built in phases)
- **Per project and agent:**
  - criticality;
  - the active dispatch and its queue;
  - the task-cycle counter (`task 7 · next ground at 10`);
  - flags: waiting approval · self-approved · stale basis · delivery uncertain · not sent · held · detected not acted on · evaluator stale.
- **Board:** Waiting approval · Approved · Claimed · Sent/Published/Uncertain · Picked up/Acked · Done claimed · Verified.
- **Approver buttons** write JSON through the same GitHub new-file path as Owner inputs. The Owner signs in; coordinators never sign in for the Owner.

## 8. Preservation
Owner inputs, receipts, registries, evidence threads and protocol pins stay as they are. An optional later adapter shows each OI as a move from the Owner. Each project keeps its own evidence format.

## 9. Delivery plan
| WP | Phase | Scope | Pass |
|---|---|---|---|
| **NM0** | P0 | this spec committed as `protocol/NEXT_MOVE_v1.md`; registry `criticality` (landing-live normal; cii-method-c and xml229-output critical; others unset = critical); landing-live `next_move: {pilot: true, approval_required: true}` | merged, by OTM |
| **WP13** | P1 | validator: schema, transitions, approver tier, self-approval label, critical rules, claim rules, supersedes. Read-only view, board, flags, task-cycle counter (mod 20). Seed moves hand-written by OTM | red control (invalid moves accepted on base / rejected on head; counter absent on base); independent check |
| **WP14** | P2 | page approve/compose (JSON new-file); claim file create/CAS helper for coordinators (documented script; no secrets) | one real move PUBLISHED → VERIFIED on landing-live; a concurrent claim is refused |
| **WP15** | P3 | coordinator evaluator (skill) + EVALUATED heartbeat; page cross-check | each trigger condition caught on a fixture; a skipped cycle shows "not acted on" |
| **P4** | — | Codex skill v3.37 alignment (§10); Codex as second claimer | a Codex ↔ TC round trip on GitHub; no duplicate send |

## 10. Codex alignment items (from its review, to fix in its skill)
1. The dispatch/notice approval model and approver tiers; a combined role means self-approval.
2. The task-cycle evaluator (mod 20) and heartbeat, kept separate from scheduler cycles and delegation allowances.
3. Standby: H1 and H2 while G1 is alive → OTM qualifies 1b → HOLD.
4. Coordinator-as-G1 for both 1a and 2 (project policy), marking claims as hypotheses.
5. HOLD reaches the agent's own chat, recorded as SENT_TO_CHAT with proof.

## 11. Review record
| Codex point | Ruling |
|---|---|
| One active dispatch, explicit supersession | adopted (§4.2) |
| Publisher is not a scheduler | adopted (§6) |
| No invented meters; precise 5/10/15/19 | adopted (§6.1–6.2) |
| Authority must resolve to a real grant | adopted (§5) |
| Claim, uncertainty, separate states | adopted (§4.1–4.2) |
| Preserve records and pins | adopted (§8) |
| Project policy vs BuddyRunner rules | adopted (§6.3) |
| Supplied 1b / NOT_PUBLISHED accepted | adopted: a durable reference, either published or supplied with provenance (§6.3) |
| Narrow duplicate wording | adopted (§6.3) |
| Conflict-safe claim, re-check before send | adopted: Contents API create / CAS (§4.2) |
| Expiry never clears uncertain; NOT_SENT | adopted (§4.1) |
| Publication ≠ delivery; pickup needs a real response | adopted (§4.1) |
| HOLD lift needs revalidation | adopted: back to PUBLISHED, fresh approval (§4.1) |
| Verification ≠ acceptance; 1b must qualify | adopted (§4.1, §6.3) |
| Activation conditions | adopted (§6.3) |
| Separate criticality from auto-response | adopted: Owner-set field; unset = critical (§2) |
| Reset after 19 gives a 19-block period | adopted: mod 20 (§6.1) |
| Combined TC/OT is one actor | adopted: self-approval is labelled; normal projects only (§5) |
| Critical H1–H3 approval | **ruled:** the Owner's standing words "approve takeover via buddy v1.7" are the explicit standing pre-approval for H1–H3 only; OTM checks eligibility; revocable by the Owner with one word (§5) |
