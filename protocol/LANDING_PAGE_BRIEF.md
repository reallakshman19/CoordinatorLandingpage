# Design and build brief — Team Protocol landing page (GitHub Pages)

Paste this whole brief into the designer/builder agent's chat. It is self-contained.

## 1. Purpose
One page where the Owner sees every project run under Team protocol v2.1 (`protocol/TEAM_PROTOCOL.md` in reallakshman19/CoordinatorLandingpage), every action and every raw message between the team members, and **posts their own inputs** (for example "ground Agent A", "suggest an action for Agent B", "no source data available"). The coordinator and OwnerTeammember pick those inputs up and handle them per the protocol.

## 2. Users and roles
- **Owner:** reads everything; writes Owner inputs and decisions.
- **TeamCoordinator / OwnerTeammember:** read the page like the Owner; their actions stay on GitHub (#1, status issues, evidence threads, `logs/`), and the page only shows them.
- Agents never use the page.

## 3. Hosting and constraints
- **GitHub Pages** from reallakshman19/CoordinatorLandingpage (public). Static site: HTML, CSS and JS in `site/`; no server and no database.
- **No tokens or secrets in the page.** The repository is public, so show only what is already public there. Chat links appear only as 8-character ids.
- **Data comes from a pre-built snapshot**, not live API calls from the browser (unauthenticated GitHub API calls are rate-limited). A GitHub Actions workflow `site-data` builds `site/data/*.json` from the registries (`logs/<project>/registry.json`), status issues, evidence threads, inbox #1, `logs/<project>/<session>/events.jsonl` and `raw/`. It runs on `issue_comment` and `issues` events and every 10 minutes, and publishes with Pages.
- It must work at phone width and in light and dark themes.

## 4. Writing: Owner inputs (no backend)
- Every "post" button opens GitHub's **new-issue page, prefilled** (`/issues/new?template=owner-input.yml&title=…&labels=owner-input`) with an Issue Form `owner-input.yml`. Fields:
  - project
  - target (whole team / coordinator / OwnerTeammember / agent id8)
  - type: `GROUND` · `SUGGEST` · `INFO` · `DECISION` · `HOLD` · `RESUME` · `QUESTION`
  - text
  - optional link to evidence
- The Owner submits it while signed in to GitHub, so authentication is GitHub's own. The page never writes by itself.
- **Protocol handling (to add to v2.1 §2/§6b on freeze):**
  - An open issue labelled `owner-input` is an Owner instruction, quoted and time-stamped by GitHub.
  - The coordinator handles it in its next cycle. A DECISION or protected item goes through OwnerTeammember's check first.
  - The handler answers on that issue with a receipt (`HANDLED: <what was done, links>` or `NEEDS CLARIFICATION: <one line>`) and closes it when done.
  - The page shows each input's state: open, acknowledged, handled.

## 5. Views (ASCII reference in the Owner's chat; keep this information and order)
1. **Home:**
   - the Needs-you list first (open decision cards and unanswered Owner inputs);
   - a projects table: coordinator and epoch, agents, health, last cycle;
   - a liveness strip: TeamCoordinator, OwnerTeammember, watchdog, GitHub.
2. **Project:**
   - the workflow card (the Owner's words) with the loop drawn as steps;
   - an agents table: state, doing → outcome, last block, verdict;
   - open loops (commit → checker → PASS/FAIL/HOLD);
   - writer leases, with outside writes flagged;
   - Owner decisions (open, decided, parked);
   - a **"Post to team"** button with the type preset.
3. **Agent:**
   - the evidence chain: one row per TASK EVIDENCE v2 block (time, task, status, commit, proof grade, OwnerTeammember verdict, checker verdict);
   - each row expands to the full block plus links (raw block, thread, commit, CI run);
   - buttons "Ground this agent" and "Suggest action" (prefilled Owner input, target = this agent).
4. **Timeline / data flow:**
   - every event across actors (Owner, OwnerTeammember, TeamCoordinator, agents, outside commits), filterable by project, actor, type and time;
   - a **flow strip** drawing who sent what to whom: Owner → OwnerTeammember → (FOR TeamCoordinator) → TeamCoordinator → agent → evidence thread → verdict → …;
   - a raw-text panel with the exact message or reply and its hash.
5. **Decision card:** the ask, what was shown (links), who checked, what is still open, the recommendation, and Answer buttons (prefilled Owner input, type DECISION).
6. **Owner inputs:** the list of the Owner's inputs with state and the handler's receipt.
7. **Protocol:** the protocol rendered from `protocol/TEAM_PROTOCOL.md`, with a table of contents.
8. **Benchmarks:** switch the whole page to a frozen benchmark snapshot (section 6), read-only, with posting disabled.

## 6. Benchmark data (test fixtures)
Frozen copies of the two real projects, from 15 Oct 2026, in `benchmarks/`:
- `benchmarks/grade9-pilot-2026-10-15/`: registry, events log with raw replies and handovers, status #6, evidence #8–#11, the related inbox comments.
- `benchmarks/imo-ab-test-2026-10-15/`: registry, status #12, evidence #13–#14, the related inbox comments. **It has no events log.** The page must rebuild that project's timeline from the threads and inbox, and mark it "reconstructed".

The page must render both correctly, including these hard cases:
1. Two coordinators over time: grade9-pilot epoch 1 (Codex) on hold, then epoch 2 (OwnerTeammember stand-in).
2. Retired agents (g1) and their successors (g2) with linked threads.
3. A FAIL → fix → re-check → PASS chain (imo-ab-test, Agent A #2–#6 against Agent B #3, #6, #9).
4. An outside write (commit 5a117f69 on PR #240) flagged against an active lease.
5. A role conflict and its resolution (OwnerTeammember recognition, early imo-ab-test).
6. Superseded Owner words ("need to work with this", then the PDF supplied).
7. Parked decisions (AB-Q003-RUN) and a project under Owner HOLD (grade9-pilot).
8. Time-corrected records (coordinator receipts that replace estimated times).

## 7. Deliverables
1. `site/`, the static page.
2. `.github/workflows/site-data.yml`, the data build plus Pages deploy.
3. `.github/ISSUE_TEMPLATE/owner-input.yml`.
4. A tiny test script that builds `data.json` from the two benchmarks and checks the eight hard cases appear.
5. A short README.

Work on a branch with a draft PR. Do not merge it; the Owner decides.

## 8. Acceptance
- Both benchmarks load, and every hard case in section 6 is visible.
- The data build runs in under 2 minutes, and its output uses chat id8s only.
- **Round trip:** an Owner input posted from the page appears as a labelled issue; on the benchmark copy, a simulated receipt shows as "handled".
- No secrets in the repository or the page. It works at 390 px width and in both themes.
- The page never claims acceptance. It shows agent claims, verdicts and Owner decisions, labelled as such.

## 9. First reply
In your own words:
1. the views and the data sources for each;
2. how an Owner input travels and who answers it;
3. how you will test with the two benchmarks.

Then a file plan, then build.
