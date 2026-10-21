# Team Protocol — Owner Dashboard

Static landing page for the Owner of the Team Protocol v2.1 project.
Hosted via GitHub Pages from the `feat/landing-page` branch (draft PR; not yet merged).

## What it shows

| View | What you see |
|---|---|
| **Home** | Open decision cards and unanswered Owner inputs first; projects table (coordinator, epoch, agents, health); liveness strip |
| **Project** | Workflow card and loop; agents table (state, evidence, branch); writer leases and outside-write flags; open decisions; "Post to team" button |
| **Agent** | Evidence chain — one row per TASK EVIDENCE v2 block with OwnerTeammember verdict; expand for full block and proof grades |
| **Timeline** | Every event across actors, filterable; flow strip; raw-text panel for selected event |
| **Decision card** | The ask, evidence link, and a prefilled "Answer this decision" button |
| **Owner inputs** | All Owner inputs with state (open / acknowledged / handled) and handler receipts |
| **Progress page** | Sub-tab **G9v3.5 Pilot Progress**: an **Overview** of every child topic of the pilot (for example G9v3.5 Physics pilot-NLM, shared tooling) and, per topic, three views: *My actions* (what the Owner must do, with files and copy-ready replies), *Progress* (milestones and stages with chat ids) and *Grounding fixtures* (sources and starting context). Read live from GitHub issues that OTM rewrites at each event (one index issue and one issue per topic). **Send to OTM**, and the + / - on a fixture, open the Owner Reply issue form prefilled; the page itself posts nothing |
| **Protocol** | `protocol/TEAM_PROTOCOL.md` rendered with table of contents |
| **Benchmarks** | Switch to a frozen benchmark snapshot; posting disabled |

## How an Owner input travels

1. Owner clicks **Post to team** (or **Ground / Suggest / Answer**) on the page.
2. GitHub's new-issue page opens, prefilled with the `owner-input.yml` Issue Form.
3. Owner submits (authenticated as their GitHub account).
4. The `site-data` GHA workflow triggers on the `issues` event → rebuilds `site/data/` → redeploys Pages → page shows the input as **open**.
5. TeamCoordinator reads and handles it in its next cycle; posts a receipt (`HANDLED: …` or `NEEDS CLARIFICATION: …`) and closes the issue.
6. Next data build → page shows **handled**.

## Data build

```
python scripts/build_data.py --root . --out site/data
```

Against the two benchmark snapshots:

```
python scripts/build_data.py --root . --out site/data/benchmarks \
  --benchmark benchmarks/grade9-pilot-2026-10-15 \
  --benchmark benchmarks/imo-ab-test-2026-10-15
```

The build runs in GitHub Actions (`.github/workflows/site-data.yml`), triggered on `issue_comment`/`issues` events and every 10 minutes.

## Test suite

```
python tests/build_test.py
```

Checks all eight hard cases from `protocol/LANDING_PAGE_BRIEF.md §6`:
1. Two coordinators over time (grade9-pilot, epoch 1 Codex → epoch 2 OwnerTeammember)
2. Retired agents (g1) and successors (g2) with linked threads
3. FAIL → fix → re-check → PASS chain (imo-ab-test, Agent A #2–#6 vs Agent B #3, #6, #9)
4. Outside write (commit 5a117f69 on PR #240) flagged against Agent A's lease
5. Role conflict and resolution (OwnerTeammember recognition, imo-ab-test registry §19 rule 1)
6. Superseded Owner words ("need to work with this" at 08:58, then PDF supplied at 09:05)
7. Parked decisions (AB-Q003-RUN) and project under Owner HOLD (grade9-pilot)
8. Time-corrected records (coordinator receipts that replace estimated times)

## Files

```
site/
  index.html           ← SPA shell with all view templates
  style.css            ← light + dark, responsive from 390 px
  app.js               ← hash router and all view renderers
  data/                ← built by GHA workflow (committed)

.github/
  workflows/
    site-data.yml      ← data build + Pages deploy
  ISSUE_TEMPLATE/
    owner-input.yml    ← Issue Form for Owner inputs

scripts/
  build_data.py        ← data build script

tests/
  build_test.py        ← hard-case tests
```

## Rules

- Branch: `feat/landing-page`. Draft PR into `main`. **Not merged by the agent.**
- No tokens, secrets or full chat URLs anywhere.
- Chat links appear only as 8-character id8s.
- The page never claims acceptance. It shows agent claims, verdicts and Owner decisions, labelled as such.
- GitHub Pages not yet enabled — the Owner enables it when ready.
