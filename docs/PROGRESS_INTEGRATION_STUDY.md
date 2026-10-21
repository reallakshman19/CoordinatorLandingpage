# Study: integrating the Progress page with the Timeline, Status bar and Home

Status: **proposal, nothing implemented.** Written by OTM (the Owner's teammate session), 21 Oct 2026, after the Owner asked:
"make a detailed study how to integrate them, however keeping progress page as optional stand alone, i.e. any outside
stand alone agent can also work". Measurements below were taken from the live site on 21 Oct 2026 (about 20:10 Dubai).

## 1. Summary

- The site already has **five separate data pipelines**. The Progress page is a sixth, written by hand. They answer
  different questions, so they should not be merged into one file, but they do overlap and they already disagree.
- Recommended design: **a portable core plus optional bridges.**
  1. *Core*: `site/progress-data/` + JSON Schemas + a stdlib-only tool + one self-contained viewer. It needs nothing
     from the landing page, GitHub or OTM. An outside agent can host it anywhere.
  2. *Bridges (optional, read-only)*: when the landing page's own data is present (`data/timeline-<project>.json`,
     `data/owner-inputs.json`, `data/status-bar.json`), the viewer adds evidence checks and links. When it is absent
     nothing breaks. Bridges **annotate; they never change a state**.
  3. *Projections (landing page only)*: Home "Needs you" and a "Progress" column in the Status bar read the Progress
     data, so the Owner sees one list of what waits on them.
- Biggest value for the least risk: **P0 to P3** in section 9. About two to three small PRs.
- Four decisions are needed from the Owner (section 11).

## 2. What exists today (facts)

| Pipeline | Source of truth | Written by | Cadence | Answers |
|---|---|---|---|---|
| **Registry** `logs/<project>/registry.json` | a file in the repo | OTM, by PR | by hand | who the project is: control epoch, hold history, agents, open Owner decisions |
| **Timeline** `data/timeline-<project>.json` | GitHub issue comments (#1 inbox, evidence threads) | the site build (`scripts/landing_build/timeline.py`) | every issue event and every 10 min | what was posted, when, by whom |
| **Status bar** `data/status-bar.json` | registries + fetched evidence | the site build (`scripts/status_bar.py`) | same | one light per project and agent, continuity checks |
| **Home "Needs you"** | registry `open_owner_decisions` + Owner inputs with `needs_you` | the site build | same | what waits on the Owner |
| **Owner inputs** `data/owner-inputs.json` | issues labelled `owner-input` | the site build, with HANDLED receipts | same | what the Owner sent and whether it was handled |
| **Progress page** `site/progress-data/` | files in the repo | OTM, with `prog.py`, by PR | at each event | stage states, the Owner's decision cards, grounding fixtures |

All five landing pipelines are built by `.github/workflows/deploy.yml` from GitHub records. The Progress page is not: it is
curated judgment, committed as files. That difference is the reason to keep it separate.

Sizes on the live site: `projects.json` 345 KB, `timeline-g9v35.json` 81 KB (64 events), `status-bar.json` 79 KB,
`owner-inputs.json` 6 KB, Progress data about 100 KB for two topics.

### Gaps observed for project `g9v35`

1. **The registry roster is out of date.** It lists three agents (`6ad7678e`, `6ad77d6a`, `6ad77d97`); the Progress data's
   chat list has the current Oracle and agents. Result: the Status bar reports 3 instances, and `coordinator.mode = UNKNOWN`.
2. **Home shows nothing for the Owner**, because the registry's `open_owner_decisions` is empty, while the Progress page
   lists four open decisions.
3. **Timeline misclassifies bookkeeping.** All 51 `OWNER_DECISION` events (of 64) come from comments on #1, including
   OTM's own `SEND_INTENT` and `SENT_TO_CHAT` records, labelled `decision_label: unverified`. Real Owner decisions cannot
   be told apart from OTM records.
4. **Status bar continuity is red** for `g9v35`: `owner_input_captured = PROBLEM (unrecorded_or_unparsed_evidence)`,
   `head_fresh = UNKNOWN`, `originals_declared = UNKNOWN`. The Owner's real words arrive in chat and are recorded as OTM
   comments, which the parser does not count as Owner input.
5. **No link between a Progress stage and the Timeline.** A stage cites a comment URL, but nothing checks that the comment
   exists, who wrote it, or whether newer activity has made the stage stale.
6. **Two chat registries** (registry agents, Progress `chats`) with no cross-check.

None of this is a defect of the Progress page; they are reasons the Owner currently has to look in several places.

## 3. Goals and hard constraints

| # | Requirement |
|---|---|
| G1 | **One owner per fact.** Every field has one source of truth; others read it. |
| G2 | **The Progress page stays optional and standalone.** Removing the landing page, the Timeline, the registry and GitHub Actions must leave a working Progress view. |
| G3 | **Any outside agent can use it**: write the files, validate, get a page. No OTM, no `gh`, no Python packages. |
| G4 | **Derived data never upgrades a state or grants acceptance.** Evidence can raise a flag, never turn `SUBMITTED` into `VERIFIED`. |
| G5 | **Public-repo safety**: id8 only, no private links or text. Configurable for a private deployment. |
| G6 | **Additive changes only** to existing pipelines; no change to WP16 status-bar light logic. |
| G7 | **Cheap and robust**: static files, conditional fetches, no new secrets, no new server. |
| G8 | **Reversible**: each phase can be switched off by removing one file or one line. |

## 4. Proposed design

```
                 ┌───────────────────────── landing page (optional host) ───────────────────────┐
  CORE           │  PROJECTIONS (landing only)        BRIDGES (optional enrichers, read-only)    │
 (portable)      │  Home "Needs you"  ◄────────────┐   timeline  owner-inputs  status-bar  registry│
 progress-data/  │  Status bar "Progress" column ◄─┤        │          │            │          │   │
  schema/        │  Timeline PROGRESS_CHANGE   ◄───┘        ▼          ▼            ▼          ▼   │
  <project>/ ... │                                   evidence checks · decision receipts · drift │
 viewer module ──┼──► mounted in the SPA tab ◄─────────── annotate only, never edit the data ────┘
 progress.html   │
 progress_tool.py└─ also works alone: any static host, any agent
```

### 4.1 Core (portable, no dependencies)

Everything an outside agent needs, in one folder that can be copied or extracted into its own repository later:

```
site/progress-data/
  projects.json                     sub-tabs
  schema/                           JSON Schemas for every file below (new)
  <project>/index.json              project, chats, topics
  <project>/<topic>/{meta,stages,actions,fixtures}.json
site/progress/
  viewer.mjs                        the viewer as an ES module (extracted from progress_page.js)
  index.html                        standalone page: ?data=<base url>
scripts/progress_tool.py            stdlib-only CLI: validate | set | answer | fix | topic add | project add
```

- **Viewer** `mountProgress(root, {base, projectsUrl, replyTo, enrichers})`. It draws with `textContent` only. The landing page's
  tab becomes a thin adapter that calls it. `site/progress/index.html` calls it with `?data=` (default `./progress-data`),
  so any static host works, including a raw GitHub URL or a local `python -m http.server`.
- **Config** moves out of code into `projects.json`, per project: `replyTo` (`{kind: "github-issue", repo, template}` or
  `none`), `visibility` (`public` | `private`), `staleAfterMin`. With `replyTo: none` the Send buttons disappear and only
  Copy remains. Today the repo name and form template are hard-coded in `progress_page.js`; that is the main thing that ties
  it to this repository.
- **Tool** `progress_tool.py` is the portable half of OTM's `prog.py` (edit, validate, add topic/project) with no GitHub,
  no board hooks and no issue creation. OTM's `prog.py` becomes a wrapper: master files, export, commit.
- **Validator** already exists (`scripts/check_progress_data.py`); it gains the JSON Schemas and a `--private` switch that
  allows chat links.

### 4.2 Bridges (optional, read-only enrichers)

An enricher is a function the host passes to the viewer. It receives the loaded data and may return **annotations**
(`{stageId, kind, text, link}`); the viewer draws them as small chips and a "Checks" list. If a bridge's source file is
missing, the enricher returns nothing and the page looks exactly as today.

| Bridge | Reads | Adds | Never does |
|---|---|---|---|
| **Evidence** | `data/timeline-<project>.json` | for each stage ref that is a comment URL: found / not found, time, tag of the poster; "newer activity since this stage was updated" | change `state` |
| **Decision receipt** | `data/owner-inputs.json`, timeline `OWNER_DECISION` events | on an answered card: "recorded on #1 at <time>" or "HANDLED receipt #N"; on an open card: "Owner reply received, not yet recorded" | mark a card answered |
| **Roster drift** | registry (via `data/projects.json` agents) | a warning when a Progress chat id is not in the registry, or the reverse | edit either list |
| **Status** | `data/status-bar.json` | the project light and continuity result shown beside the Progress header, labelled as a different measure | blend it with Progress states |

Why browser-side, not a build step: no workflow change, no CI coupling, works the day it merges, and the files are small
enough (about 170 KB for the three it needs). A build-time bridge stays available as option C if size or latency ever
becomes a problem.

### 4.3 Projections (landing page only)

These make the **existing** views show Progress facts. They are separate from the core, switchable off, and each reads the
Progress files directly.

1. **Home "Needs you"**: add one row per open Progress card (`#progress-page/<project>/<topic>/actions`). Today this list is
   empty for `g9v35`. This is the highest-value change.
2. **Status bar**: an extra **Progress** column per project: open Owner cards, blocked stages, age of the last write. It is
   a separate measure: `UNKNOWN` when there is no Progress data; it never turns the project light green.
3. **Timeline**: a new event type `PROGRESS_CHANGE`. Source: a short `hist` list kept inside each `stages.json` entry
   (`{ts, from, to, ref}`, last 20, written by the tool on every state change). Reading `hist` needs no git history, so it
   also works for an outside agent. (Reading `git log` was rejected: the deploy checkout is shallow.)

## 5. Data model changes (additive; `schema: 2` stays valid)

| Where | Field | Purpose |
|---|---|---|
| `projects.json` entries | `replyTo`, `visibility`, `staleAfterMin` | remove hard-coded repo and policy from the viewer |
| `index.json` project | `registryProject` (optional) | tells bridges which registry/timeline project this maps to |
| `stages.json` entries | `updatedAt` | enables "newer activity since" |
| | `hist` `[{ts, from, to, ref}]` | Timeline events and an audit trail |
| | `refs[].c` (optional comment id) | exact match to a timeline event instead of parsing URLs |
| `actions.json` cards | `answer.ref` becomes **required** when `status = done` | a decision with no record is shown as "unrecorded" |
| `fixtures.json` entries | `at`, `by` (optional) | who added an entry, and when |

JSON Schemas live in `site/progress-data/schema/` and are the contract for outside agents. The validator uses them.

## 6. Precedence rules (declared against derived)

| Fact | Truth | Others |
|---|---|---|
| A stage's `state` | the Progress file (declared, with refs) | bridges flag disagreement only |
| An Owner decision | the GitHub record (#1 comment or HANDLED receipt) | the card mirrors it and must cite it (`answer.ref`) |
| Who the agents are | the registry for landing-hosted projects; the Progress `chats` list for a standalone project | drift warning when both exist |
| Control, hold, epoch | the registry | Progress shows it as a read-only note, never edits it |
| Light colour of the project | the Status bar (WP16) | Progress adds its own column |

A flag has three levels: **info** ("evidence found"), **warn** ("newer activity since this was updated", "ref not found"),
**conflict** ("stage is VERIFIED but the referenced comment is a FAILED/BLOCKED evidence block"). Only the Owner or OTM
resolves a conflict, by editing the Progress data.

## 7. Staying standalone: what an outside agent gets

**Minimum use, five steps, no landing page:**
1. Copy `site/progress-data/` and `site/progress/` into any folder served as static files (or use the repo's Pages).
2. Create `projects.json` and `<project>/index.json` (copy `g9v35`, delete the topics).
3. `python scripts/progress_tool.py topic add <key> --title ...` then `set`, `answer`, `fix` as work proceeds.
4. `python scripts/progress_tool.py validate` before every commit.
5. Open `site/progress/index.html?data=./progress-data`.

**What is lost without the landing page:** the Home, Status bar and Timeline projections, and the bridge chips. The core
views, the Overview, the fixtures and the copy-ready replies all remain. Reply buttons fall back to Copy unless the project
sets `replyTo`.

**Private deployments:** `visibility: private` lets chat links through the validator and the viewer. Everything else is
identical.

**Extraction later:** the core folder has no import from the rest of the site, so it can move to its own repository with a
copy and a changed base URL. No decision is needed now.

## 8. Options considered

| Option | Idea | For | Against | Verdict |
|---|---|---|---|---|
| **A** Links only | Keep separate; add hyperlinks between views | trivial | the gaps in section 2 stay; no checks | too little |
| **B** Browser enrichers + projections | core + optional bridges (this document) | no build change; standalone preserved; reversible; fast | each viewer fetches three more small files | **recommended** |
| **C** Build-time bridge | a deploy step joins the files into `progress-bridge-<project>.json` | one fetch; can use more history | touches `deploy.yml`; couples to CI; breaks if a landing script changes; harder for outside agents | keep as fallback |
| **D** Merge into the registry | put stages and cards into `registry.json` | one file | breaks standalone; the registry is a protocol document, not a work log; bigger schema risk (WP-L3) | reject |
| **E** Derive Progress from the Timeline | compute stages from comments | no hand writing | needs a rule per stage; a comment is not proof; loses the Owner cards and fixtures | reject |

## 9. Phased plan

| Phase | What | Files | Effort | Risk | Rollback |
|---|---|---|---|---|---|
| **P0** Hygiene | JSON Schemas; make reply config per project; update the g9v35 registry roster; classify OTM records so the Timeline can tell them from Owner decisions | `site/progress-data/schema/*`, `projects.json`, `site/js/progress_page.js`, `logs/g9v35/registry.json`, `scripts/landing_build/timeline.py` (label only) | S | low | revert |
| **P1** Extract the viewer | `viewer.mjs` + standalone `site/progress/index.html`; landing tab becomes an adapter; `progress_tool.py` | `site/progress/*`, `site/js/progress_page.js`, `scripts/progress_tool.py` | M | medium (a rewrite of loading code; tests needed) | keep old file until tests pass |
| **P2** Bridges | evidence, decision-receipt, roster-drift, status enrichers | `site/progress/bridges/*.mjs` | M | low | remove the enrichers array |
| **P3** Projections | Home "Needs you" rows; Status bar Progress column | `site/js/home.js`, `site/js/statusbar.js` | S to M | medium: existing pages and their tests | feature flag in `projects.json` |
| **P4** History | `hist` written by the tool; Timeline `PROGRESS_CHANGE` | `progress_tool.py`, `timeline.py` | M | low | drop the event type |
| **P5** Optional | build-time bridge (option C) only if P2 proves heavy | `deploy.yml`, one script | M | higher | remove the step |

Each phase ends with a PR that passes the existing landing tests plus new node tests for the viewer and the bridges. P0 to
P3 are the proposal; P4 and P5 are held until there is a need.

## 10. Risks and mitigations

| Risk | Mitigation |
|---|---|
| **Authority leak**: a bridge or projection makes something look accepted | G4 as code: enrichers cannot write state; the viewer ignores any annotation field named `state`; tests assert it |
| **Drift** between registry and Progress | roster-drift flag; one CI check script comparing both |
| **Landing tests pin many strings** | projections behind a flag; add tests first, run the full landing suite in the PR |
| **Latency**: data commits redeploy the site (a few minutes) | acceptable; a later option is serving the files from a raw URL for fresher reads |
| **Size/rate**: several JSON fetches per refresh | conditional requests (`no-cache`), no GitHub API calls, all files are static |
| **Privacy**: a bridge shows more than intended | bridges only copy fields already on the public site; validator blocks chat/Drive/email text |
| **Single writer**: OTM edits while an outside agent edits | one writer per topic (already a rule); PRs show conflicts; `hist` keeps the trail |
| **Over-engineering** | P0 to P3 only; each phase must justify itself with a visible Owner benefit |

## 11. Decisions needed from the Owner

1. **Approve P0 to P3** as the integration path (option B). Recommended.
2. **Home "Needs you" may include Progress cards** (changes the main page). Recommended: yes.
3. **Standalone package stays inside this repository for now** (self-contained folder, extractable later), not a new repository. Recommended: yes.
4. **Data-only commits to `main` under `site/progress-data/`** by OTM (still open from earlier): without it every update waits for a PR merge.

## 12. Acceptance tests (how we will know it works)

- Delete `data/` from a local copy of the site: the Progress page loads and shows every view; no console errors.
- Serve only `site/progress/` and `site/progress-data/` with `python -m http.server`: `progress/index.html` works and shows all topics.
- Add a project and a topic with `progress_tool.py` only; the validator passes; the sub-tab and topic appear with no code change.
- A stage citing a comment that exists shows "found, <time>, <tag>"; citing a missing id shows "not found" and the state is unchanged.
- An answered card without `answer.ref` shows "unrecorded"; with a `ref` that matches a timeline event it shows the record.
- Home "Needs you" lists the open Progress cards for `g9v35`; the Status bar shows a Progress column and the project light is unchanged.
- A test that feeds a bridge an annotation with `state: VERIFIED` and checks the displayed state did not change.
- The existing landing test suite passes unchanged.

## Appendix: evidence and file pointers

- Pipelines: `scripts/build_data.py` (writes `status-bar.json`, `timeline-*.json`, `projects.json`, `owner-inputs.json`),
  `scripts/status_bar.py`, `scripts/landing_build/timeline.py`, `scripts/landing_build/owner_inputs.py`, `.github/workflows/deploy.yml`.
- Views: `site/js/home.js` (Needs you), `site/js/statusbar.js`, `site/js/timeline.js`, `site/js/owner_inputs.js`,
  `site/js/progress_page.js`.
- Progress contract: `docs/PROGRESS_PAGE.md`, `scripts/check_progress_data.py`.
- Live measurements (21 Oct 2026): `g9v35` status light yellow (`work_or_coverage_not_proven`), continuity red; 3 registry
  instances; timeline 64 events (51 `OWNER_DECISION`, 11 `TASK_EVIDENCE`, 2 `CONTROL_EPOCH`); `open_owner_decisions` empty.
