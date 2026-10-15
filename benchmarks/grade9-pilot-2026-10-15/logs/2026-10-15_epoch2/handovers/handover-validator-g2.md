# Handover — Grade 9 QRT tile validator, generation 2

You are the **validator agent** for the Grade 9 IMO research suite, generation 2. The Owner stopped the previous validator chat (6ad02130, thread [#9](https://github.com/reallakshman19/CoordinatorLandingpage/issues/9)) on 15 Oct 2026; its work is your **input, not your authority** — re-verify what you rely on.

- **Coordinator:** OwnerTeammember (stand-in TeamCoordinator, control epoch 2), under [Team protocol v1.1](https://github.com/reallakshman19/CoordinatorLandingpage/issues/7).
- **Your evidence thread:** this issue (#10). **The HTML fixer (coder g2):** [#11](https://github.com/reallakshman19/CoordinatorLandingpage/issues/11).

## The Owner's workflow (Owner's words)
> "QRT tile by tile: idea is to design a validator (by one agent), fix existing standalone html based on validator outcome (another agent), check and fix the validator if required"

## Your loop, one QRT tile at a time
1. **Define the tile's checks from the repository's own blueprint logic:** the QRT cell (demand × band) per `Shared/tools/question_review_matrix.py`; the five-factor rubric `Shared/vocabularies/learner-question-metadata.v1.json` with the canonical `Shared/tools/question_difficulty.py`; learner protection in the standalone HTML (no answer shown or highlighted before a committed attempt, progressive hints, solution only after commit, keyboard access); Core relationships; math rendering. Implement them in your validator.
2. **Run them on the current standalone HTML and source at the exact commit** (now: PR #240 head `90c85970`; later: the coder's frozen fix commit).
3. **Post the tile findings** as TASK EVIDENCE v2 here — one line per question: `PASS` / `FAIL` · rule · location (file + element or question ID). The coder fixes from this list only.
4. **When the coder posts a frozen fix commit for the tile, re-run on that exact commit.** If a FAIL was your validator's own mistake, fix the validator, say so in the block, and re-run.

A tile is **done** at 0 FAIL with no validator fix pending; then the next tile. **Start with `QRT-RETRIEVE-D1`** unless another order is clearly better (say why in your first reply).

## Repository state (checked 15 Oct 08:0x Dubai)
- `reallakshman19/Grade9v3.5`. Source PR #240 (draft, base `main`), branch `feat/imo-grade9-68-questions-master-suite` @ `90c85970`. Generator `Mathematics/research/build_full_master_suite.py`. Four outputs, identical bytes: `standalone/mathematics-imo-grade9-master-suite.html`, `public/standalone/mathematics-imo-grade9-master-suite.html`, `public/test/imo-grade9/core2.html`, `docs/test/imo-grade9/core2.html`.
- Previous validator code: draft PR #250, branch `agent/issue249-qrt-validator-v1` @ `a6b42cd9` — `Shared/tools/imo_qrt_validator.py`, `imo_qrt_core_relationships.py`, `imo_qrt_hots_review.py`, their tests, workflow `.github/workflows/qrt249-pinned-source-factor.yml` (detached source + validator overlay; 55 tests green in run 38675500699). **Reuse it. Work on a new branch from `a6b42cd9`** (e.g. `agent/qrt-tile-validator-g2`) with its own draft PR into the feature branch; PR #250 stays frozen.
- Known findings (validator g1, Issue #249): 27 score mismatches, 6 band mismatches, 1 invalid factor, 50 missing HOTS factor sets, 177 topic-only Core links, HOTS Q024/Q035 on HOLD. 13 difficulty corrections confirmed against the blueprint wait for the Owner ([#249 comment 6184002829](https://github.com/reallakshman19/Grade9v3.5/issues/249#issuecomment-6184002829)); 15 are parked.
- CI already red on `90c85970` (baseline-red, not yours): guardrails, learner-platform-code-tests.

## Boundaries
You check; you never edit source content, the generator or the HTML. No merge, release, QRT/academic or source-rights acceptance. Difficulty scores are findings only; they change only for question IDs the Owner approves. Owner option B: v3.6 managed lifecycle stays off.

## Reporting
Every reply that finishes a task ends with **TASK EVIDENCE v2** ([#7](https://github.com/reallakshman19/CoordinatorLandingpage/issues/7) section 3), and the same block is posted as a comment here. A reply that finishes no task ends with the **STATUS v2** line.

## First reply
Short own-words answers: who you are and who owned this before; which inputs are authoritative (and which are only candidates); the checks you will run for tile 1 and why that tile first. Then start tile 1, post its findings here as TASK EVIDENCE v2 #1.
