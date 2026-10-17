# landing-live route map: from source to page and back

An **index over the code** that shows how a fact gets from its authoritative source to the deployed page, and who acts on it next. It does not replace the code or specs; links are pinned to main `23843c96ee142ea21577312b504d4ba6cb3f8fc8` (re-check before relying on line numbers). The project brief is [LANDING_LIVE_BRIEF.md](LANDING_LIVE_BRIEF.md).

Pinned base: `https://github.com/reallakshman19/CoordinatorLandingpage/blob/23843c96ee142ea21577312b504d4ba6cb3f8fc8/` (abbreviated `@pin/` below).

## Stage 0: one publisher builds everything
[`.github/workflows/deploy.yml`](https://github.com/reallakshman19/CoordinatorLandingpage/blob/23843c96ee142ea21577312b504d4ba6cb3f8fc8/.github/workflows/deploy.yml) is the **only** Pages writer. The steps run in this order:
1. check out exact main;
2. `fetch_live_data.py` reads GitHub into `_live_cache/` (read-only);
3. `publish_site.py capture` checks the capture and fails closed;
4. `build_data.py` writes `_artifact/data/*.json` (live), plus a separate benchmark build from the frozen fixtures;
5. `publish_site.py stamp` writes `build-info.json` and versions the asset URLs;
6. tests;
7. Pages deploy;
8. HTTP readback (`deployed_readback`).

A trigger (push, issue/comment event, schedule) **rebuilds the view**. It never wakes or instructs an agent.

## Route A: an Owner input (page → GitHub → page → responsible actor)

| Step | Where | What happens | Boundary / authority |
|---|---|---|---|
| A1 Owner writes | `site/app.js` [`setupJSONInputForm`](https://github.com/reallakshman19/CoordinatorLandingpage/blob/23843c96ee142ea21577312b504d4ba6cb3f8fc8/site/app.js#L1087) and [`ownerJSONCommitURL`](https://github.com/reallakshman19/CoordinatorLandingpage/blob/23843c96ee142ea21577312b504d4ba6cb3f8fc8/site/app.js#L969) | The page builds a GitHub "new file" URL for `logs/<project>/inputs/OI-<date>-<time>-<hex>.json`. **The Owner commits it while signed in.** | The page holds no token and writes nothing; the Owner's commit is the record |
| A2 Read | [`owner_json.read_committed_inputs`](https://github.com/reallakshman19/CoordinatorLandingpage/blob/23843c96ee142ea21577312b504d4ba6cb3f8fc8/scripts/owner_json.py#L102) | Validates the schema and registered project, checks GitHub provenance (`github_provenance`), pairs each input with `receipts.jsonl` rows (ACK / NEEDS_CLARIFICATION / HANDLED; HANDLED needs links) | An untrusted or invalid receipt never makes an input "handled" |
| A3 Build | [`build_data.build_all`](https://github.com/reallakshman19/CoordinatorLandingpage/blob/23843c96ee142ea21577312b504d4ba6cb3f8fc8/scripts/build_data.py#L1345), around [L1377](https://github.com/reallakshman19/CoordinatorLandingpage/blob/23843c96ee142ea21577312b504d4ba6cb3f8fc8/scripts/build_data.py#L1377) and [L1573](https://github.com/reallakshman19/CoordinatorLandingpage/blob/23843c96ee142ea21577312b504d4ba6cb3f8fc8/scripts/build_data.py#L1573) | Merges older issue-form rows (`build_owner_inputs`) with the verified JSON inputs into `data/owner-inputs.json` | A typed role or unverified JSON never becomes an effective approval |
| A4 Show | [`loadOwnerInputs`](https://github.com/reallakshman19/CoordinatorLandingpage/blob/23843c96ee142ea21577312b504d4ba6cb3f8fc8/site/app.js#L100) → `renderOwnerInputs`, `renderHome`, `renderTrace`, decision views | State badge and receipt trace | The view only |
| A5 Act | **OwnerTeammember/TeamCoordinator** (human/agent step, not code) | Reads the input, acts within authority, and appends a receipt row (`ACK` → `HANDLED` with links) | The receipt is the claim; the linked evidence is the proof; acceptance stays separate |

## Route B: an agent's evidence (chat → GitHub → page → next action)

| Step | Where | What happens | Boundary / authority |
|---|---|---|---|
| B1 Agent publishes | Evidence thread (landing-live: [#22](https://github.com/reallakshman19/CoordinatorLandingpage/issues/22)) | The **TASK EVIDENCE v2** block (TEAM_PROTOCOL §3) is posted as a comment | An agent claim; no permission |
| B2 Discover + fetch | [`fetch_live_data.discover_sources`](https://github.com/reallakshman19/CoordinatorLandingpage/blob/23843c96ee142ea21577312b504d4ba6cb3f8fc8/scripts/fetch_live_data.py#L111), [`discover_project_refs`](https://github.com/reallakshman19/CoordinatorLandingpage/blob/23843c96ee142ea21577312b504d4ba6cb3f8fc8/scripts/fetch_live_data.py#L171), [`fetch_issue`](https://github.com/reallakshman19/CoordinatorLandingpage/blob/23843c96ee142ea21577312b504d4ba6cb3f8fc8/scripts/fetch_live_data.py#L61) | The registry (`logs/<project>/registry.json` → `agents[].evidence_thread`) decides which threads are read; they are cached in `_live_cache/` | Only registry-declared sources are read |
| B3 Parse | [`parse_task_evidence`](https://github.com/reallakshman19/CoordinatorLandingpage/blob/23843c96ee142ea21577312b504d4ba6cb3f8fc8/scripts/build_data.py#L114), [`parse_verdict`](https://github.com/reallakshman19/CoordinatorLandingpage/blob/23843c96ee142ea21577312b504d4ba6cb3f8fc8/scripts/build_data.py#L176), [`build_agent_evidence`](https://github.com/reallakshman19/CoordinatorLandingpage/blob/23843c96ee142ea21577312b504d4ba6cb3f8fc8/scripts/build_data.py#L189) | Turns blocks and verdicts into per-agent evidence, fenced by generation and repository | Parsing ≠ proof |
| B4 Project | [`build_project_data`](https://github.com/reallakshman19/CoordinatorLandingpage/blob/23843c96ee142ea21577312b504d4ba6cb3f8fc8/scripts/build_data.py#L790) | Freshness (`derive_freshness`), HOLD/tree/children (WP12), auto-response (WP10), Next Move view (WP13), UEM projection (default off) | A projection of records, never new authority |
| B5 **Write the payloads** | [build_data.py L1476–1491](https://github.com/reallakshman19/CoordinatorLandingpage/blob/23843c96ee142ea21577312b504d4ba6cb3f8fc8/scripts/build_data.py#L1476) | Two files are written: **`data/evidence-<project>-<id8>.json`** (project-qualified) and **`data/evidence-<id8>.json`** (a compatibility copy for the first project with that id8). If the same id8 appears in two projects, the compatibility file becomes `{"collision": true, "agent": null, "source_health": {"status": "ambiguous_agent_id8"}, "projects": [...]}` | Ambiguity is shown, never guessed |
| B6 **Consume** | [`loadEvidence(id8)`](https://github.com/reallakshman19/CoordinatorLandingpage/blob/23843c96ee142ea21577312b504d4ba6cb3f8fc8/site/app.js#L86) reads **`evidence-<id8>.json`** (the compatibility file) → [`renderAgent`](https://github.com/reallakshman19/CoordinatorLandingpage/blob/23843c96ee142ea21577312b504d4ba6cb3f8fc8/site/app.js#L1527) (Agent view) | The page reads the compatibility payload, not the project-qualified one | Known limit: a collision shows as ambiguous |
| B7 Status + next | [`scripts/status_bar.py`](https://github.com/reallakshman19/CoordinatorLandingpage/blob/23843c96ee142ea21577312b504d4ba6cb3f8fc8/scripts/status_bar.py) → `data/status-bar.json` → [`renderStatusBar`](https://github.com/reallakshman19/CoordinatorLandingpage/blob/23843c96ee142ea21577312b504d4ba6cb3f8fc8/site/app.js#L686); Next Move: [`next_move.py`](https://github.com/reallakshman19/CoordinatorLandingpage/blob/23843c96ee142ea21577312b504d4ba6cb3f8fc8/scripts/next_move.py) validator → [`renderNextMoves`](https://github.com/reallakshman19/CoordinatorLandingpage/blob/23843c96ee142ea21577312b504d4ba6cb3f8fc8/site/app.js#L449) | Lights from work / monitoring / authority; moves are shown with their states | Green needs sourced work + monitoring + authority. A START or a filled field is never enough |
| B8 Act | **OwnerTeammember/TeamCoordinator** (human/agent step) | Verifies the evidence against GitHub (exact head, hosted CI), posts the verdict on #22, then GO / FIX / HOLD. A send uses the Next Move states (SENT_TO_CHAT / DELIVERY_UNCERTAIN / NOT_SENT) | Delivery ≠ pickup ≠ acceptance |

## Originals and oracles (what a "complete expected result" is)
- **F1** `benchmarks/grade9-pilot-2026-10-15/` (MANIFEST blob `06baec0e…`) and **F2** `benchmarks/imo-ab-test-2026-10-15/` (MANIFEST blob `3cff5804…`) are the frozen original fixtures. They are built separately (`build_data.py --benchmark`) and never edited. F2 has no `events.jsonl`, so its provenance is reconstructed.
- **Acceptance oracles:** the eight hard cases in [`protocol/LANDING_PAGE_BRIEF.md`](https://github.com/reallakshman19/CoordinatorLandingpage/blob/23843c96ee142ea21577312b504d4ba6cb3f8fc8/protocol/LANDING_PAGE_BRIEF.md), plus the F1–F7, G01–G15 and C00–C16 layers on [#21](https://github.com/reallakshman19/CoordinatorLandingpage/issues/21). These are separate layers; do not merge them into one count.
- **Not proven by these:** that F1/F2 are two product repos (both point to Grade9v3.5; WP11 gives the separate real two-repo proof), and full byte-level golden verification. Synthetic negative tests do not replace original Owner inputs (the F7b/c traces).
