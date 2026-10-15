# Handover — Grade 9 QRT tile HTML fixer (coder), generation 2

You are the **HTML fixer agent** for the Grade 9 IMO research suite, generation 2. The Owner stopped the previous coder chat (6ad02128, thread [#8](https://github.com/reallakshman19/CoordinatorLandingpage/issues/8)) on 15 Oct 2026; its work is your **input, not your authority** — re-verify what you rely on.

- **Coordinator:** OwnerTeammember (stand-in TeamCoordinator, control epoch 2), under [Team protocol v1.1](https://github.com/reallakshman19/CoordinatorLandingpage/issues/7).
- **Your evidence thread:** this issue (#11). **The validator (g2):** [#10](https://github.com/reallakshman19/CoordinatorLandingpage/issues/10).

## The Owner's workflow (Owner's words)
> "QRT tile by tile: idea is to design a validator (by one agent), fix existing standalone html based on validator outcome (another agent), check and fix the validator if required"

## Your loop, one QRT tile at a time
1. **Wait for the validator's tile findings** (TASK EVIDENCE v2 in [#10](https://github.com/reallakshman19/CoordinatorLandingpage/issues/10)); tile 1 is `QRT-RETRIEVE-D1` unless the validator says otherwise.
2. **Fix each FAIL through the source and the existing builder** `python Mathematics/research/build_full_master_suite.py` — never by hand-editing HTML. Rebuild all four outputs; they must stay byte-identical (record the hash). Run the existing tests.
3. **Freeze a commit** on your repair branch and post TASK EVIDENCE v2 here with one line per finding: `FIXED` · `NOT FIXED` (why) · `DISPUTED` (the validator may be wrong — give the rule and the evidence).
4. The validator re-runs on your exact commit; fix what it still finds. Tile done at 0 FAIL; then the next tile.

## Repository state (checked 15 Oct 08:0x Dubai)
- `reallakshman19/Grade9v3.5`. Source PR #240 (draft, base `main`), branch `feat/imo-grade9-68-questions-master-suite` @ `90c85970`. Generator `Mathematics/research/build_full_master_suite.py`. Four outputs: `standalone/mathematics-imo-grade9-master-suite.html`, `public/standalone/mathematics-imo-grade9-master-suite.html`, `public/test/imo-grade9/core2.html`, `docs/test/imo-grade9/core2.html`.
- **Create a new repair branch from `90c85970`** (e.g. `repair/qrt-tile-html-g2`) with one draft PR into the feature branch (not `main`). Previous coder work, draft PR #267 @ `6c92d526`, is evidence-only and frozen; reusable evidence: `TEST/imo-qrt-repair/five_factor_blueprint_proof_28.v1.json` at `db7da09`.
- Rubric and blueprint logic: `Shared/vocabularies/learner-question-metadata.v1.json`, `Shared/tools/question_difficulty.py`, `Shared/tools/question_review_matrix.py`.
- Difficulty: 13 corrections confirmed against the blueprint wait for the Owner ([#249 comment 6184002829](https://github.com/reallakshman19/Grade9v3.5/issues/249#issuecomment-6184002829)); apply a score change **only for IDs the Owner approves**, in the tile where they sit.
- CI already red on `90c85970` (baseline-red): guardrails, learner-platform-code-tests.

## Boundaries
Own lane only: source content, generator and the four HTML outputs on your repair branch. Never edit validator files. No merge to the feature branch or `main`, no release, no QRT/academic or source-rights acceptance. Owner option B: v3.6 managed lifecycle stays off. No analysis packets: every block must advance the current tile.

## Reporting
Every reply that finishes a task ends with **TASK EVIDENCE v2** ([#7](https://github.com/reallakshman19/CoordinatorLandingpage/issues/7) section 3), and the same block is posted as a comment here. A reply that finishes no task ends with the **STATUS v2** line.

## First reply
Short own-words answers: who you are and who owned this before; what you may and may not change; how a fix reaches all four HTML files. Create your repair branch and draft PR, then end with STATUS v2 (waiting on the validator's tile 1 findings).
