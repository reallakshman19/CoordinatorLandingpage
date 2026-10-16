# WP15 — Next Move evaluator, landing-live pilot

The evaluator is **manually invoked in a coordinator cycle**. It does not schedule itself, call GitHub write APIs, commit a heartbeat, send text to an agent, or start chats. It reads the checked-out project registry and immutable move/transition files, the scoped local read-only evidence cache, and a publisher projection captured at the same source head.

Example (after running the existing read-only fetch/build pipeline):

```bash
python scripts/next_move_evaluator.py \
  --root . --cache-dir _live_cache \
  --projection site/data/project-landing-live.json \
  --actor-role TeamCoordinator --actor-id8 11111111 \
  --at 2026-10-16T16:00:00Z \
  --output _artifacts/next-move-evaluator-proposal.json
```

Replace the id8 and timestamp with the **real coordinator and actual cycle instant**; example values above are illustrative, not recorded source evidence. With no `--output` the result is JSON on stdout only. `--output` is explicitly local and cannot target the authoritative `logs/` directory. The proposed JSON includes `heartbeat_proposal: {state:"EVALUATED",at,by}` and signal notices. **It is not a heartbeat yet.** The coordinator must separately inspect/validate sources and **manually** append that exact row to `logs/landing-live/moves.jsonl` under a permitted grant, with any required human decision. No move is automatically created, approved, claimed or sent.

To publish a page cross-check, the coordinator may separately review and commit a copy of the evaluator report at `logs/landing-live/next-move-evaluation.json`. The page compares the report snapshot to the current source projection and displays `match`, `mismatch` (with field names), `stale_output`, `untrusted_or_stale_source`, or `not_recorded`. Its **Last recorded EVALUATED** comes **only** from `moves.jsonl`; the proposed row in the report is never counted. The evaluator flags detected-but-not-acted on only when there is a dated source condition, not on guessed meter percentages, unconfirmed chat ends or undated GO boundaries.

## WP14 post-expiry claim CAS review note

After a 15-minute claim expires **before** SEND_INTENT, a different human coordinator session may deliberately inspect the existing file and attempt a CAS renewal under the exact same **recipient id8**. This is a *claim custody change*, not delegation to another recipient or a newly authorized send. Preconditions are an explicitly recorded APPROVED/CLAIMED move, current registry SHA and basis, no HOLD, no other active dispatch to the same recipient, and no outstanding SEND_INTENT or DELIVERY_UNCERTAIN. The helper includes the current file SHA in the PUT. A competing 409/422 response is a **ClaimRefused** conflict, never a retry that overwrites the winner. The coordinator must still record an authorized CLAIMED transition as applicable; the helper does not append it. Once SEND_INTENT has appeared without a proved outcome, expiry **cannot** clear uncertainty or authorize takeover: reconcile the actual chat first and record SENT_TO_CHAT or NOT_SENT.

**Evidence:** `tests.test_wp15` tests successful post-expiry CAS custody under the same recipient, expiry TTL, unresolved SEND_INTENT refusal and 409/422 mapping. All tests use an in-memory fake Contents transport; no live claim was created.
