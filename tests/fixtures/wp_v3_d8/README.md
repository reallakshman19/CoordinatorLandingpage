# WP-V3 / D8 — post-CLAIMED Owner correction (synthetic evaluator simulation)

**No actual send, approval, receipt or Owner instruction is present.** All move
and #1 comment identifiers are test-only. This test reuses the WP-V2 D3
read-only registry/cached source fixture at
`tests/fixtures/wp_v2_d3/**`, whose registry file is a byte-for-byte copy
of the real `landing-live` registry. The repo HEAD when WP-V3 started:
`01b0645d765e455640a71fdb6a5e10ded5b2779d`. No real `logs/**` is edited.

Timeline (all in UTC, synthetic):

1. **21:00** — coordinator checkpoint, previously captured and verified in the
   D3 synthetic status issue #30 cache. Move
   `NM-20261017-210000-a11a` is PUBLISHED.
2. **21:01** — Owner APPROVED via fake `moves.jsonl` transition (not a
   GitHub or real Owner approval).
3. **21:02** — named recipient `6ad405cc` CLAIMED; bounded fake claim expires
   **21:17**.
4. **21:15** — synthetic #1 project-matching Owner correction, comment
   `990000001`, changes project scope, already in
   `tests/fixtures/wp_v2_d3/cache/inbox-1.json`.
5. **21:16** — coordinator's evaluator pre-send simulation. Registry and
   move basis SHA are unchanged; claim still valid; no HOLD; no SEND_INTENT
   or SENT_TO_CHAT ever existed. The *only* invalidating condition is the
   previously unseen, after-checkpoint scope correction.

D3 source guard already projects `amendment_checkpoint.status=UNRECONCILED`,
source `https://github.com/reallakshman19/CoordinatorLandingpage/issues/1#issuecomment-990000001`.
The D8 evaluator must fail closed **for the specific claimed move** and
surface this source. The global evaluator `read_only: true` / `may_send: false`
are independent of D8 and cannot alone constitute a successful pre-send check.

The evaluator can propose a transition but may not append one, mutate GitHub,
send to ChatGPT, or turn `SENT_TO_CHAT` into a claimed delivery. These tests
check that the previously claimed move is no longer considered ready-to-send.

Frozen benchmark SHA-256 must remain:
`0a7ebd12ca385963c97adadfeb033a8f88777a4ec6ad9d1bcddf0e785e4095a8`.
