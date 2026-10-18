# landing-live: known issues

Owner, 17 Oct 2026: "Note down identified bugs as known issues." This list collects defects and gaps found during the S1/S2 work, the independent checks and Codex reviews on 16–17 Oct 2026. Each row has a source and an owner. **Nothing here is fixed by being listed.** Status: OPEN / ACCEPTED (a known limit) / FIXED (with a link).

## Product (landing page code and data)

| ID | Issue | Found by / source | Status | Owner · next step |
|---|---|---|---|---|
| K01 | Agents from a foreign source (an evidence thread outside the registry repo) are dropped without a visible reason. Fail-closed is correct, but the operator sees only "no evidence yet" | final #50 check; #53 check | OPEN | OwnerTeammember · P1 landing revision: show a "foreign source rejected" reason |
| K02 | A deploy succeeded but its readback check failed (run 39000177607, 17 Oct 03:48Z). The served state for that run is UNKNOWN; later runs passed. The readback may race the Pages CDN | Codex Q7; checker on #56 | OPEN | OwnerTeammember · check the readback retry/backoff in `publish_site.deployed_readback` |
| K03 | Original hard-case oracle HC3 passes on a bare `FAIL` substring (too loose) | S2 run 3 reader | OPEN | P1 · tighten the oracle without editing the frozen goldens (a new versioned check) |
| K04 | `landing-tests.yml` runs only on pull requests (plus manual `workflow_dispatch`), so main-head behaviour has no test run of its own (deploy runs only `build_test` + WP1a/1b/3/4) | S2 run 1 reader | OPEN | P1 · decide whether main needs a scheduled or push test run |
| K05 | The status bar shows the landing lease holder as UNVERIFIED_HOLDER: `leases[].holder` is "Agent L1 g2", with no id8 | Codex S1 | OPEN | P1 · put the id8 in lease holders (schema v3) |
| K06 | The Next Move pilot has no real move, transition or EVALUATED records, so the page shows "evaluator stale" and task cycle `no_go` forever | Codex S1; evaluator run 16 Oct | ACCEPTED while the HOLD is on | OwnerTeammember · first real use in S3 |
| K07 | Registry `control.hold.since` holds "2026-10-17T04:1x+04:00", which is not a timestamp (the minute is unknown); the page shows it as text | checker on #56 | ACCEPTED | — (an honest range beats an invented minute) |
| K08 | The 10-minute deploy schedule fired far less often than scheduled (only 10 runs seen) | S2 run 2 reader | OPEN | P1 · check against GitHub's scheduled-workflow limits; the page must not imply 10-minute freshness |
| K09 | Push-triggered deploy runs are often `cancelled` by concurrency when an issue-comment run deploys the same SHA, which looks alarming in the run list | run list 17 Oct | ACCEPTED | — (expected; documented here) |

## Records and process

| ID | Issue | Found by / source | Status | Owner · next step |
|---|---|---|---|---|
| K10 | A #22 comment cites the F7c click-test commit as `1371bb8`; the repo commit is `1321bb8e` | S2 runs 1–3 | OPEN | OwnerTeammember · append a correction comment (never edit history) |
| K11 | The registry `updated` field and the #30 status comment lag behind real changes | S2 runs 2–3 | OPEN | OwnerTeammember · update both with every registry write (protocol v3 rule) |
| K12 | **Every actor posts from the Owner's one GitHub account**, so role prefixes, "independent" checkers and agent identities are claims, not authenticated | Codex reviews; all S2 runs | ACCEPTED (Owner decision needed to change) | Owner · bot accounts or a GitHub App would be a separate decision |
| K13 | Minimized GitHub comments are still returned by the API, so a "blind" cold-reader test from #21 is not perfectly blind | Codex Q8 | ACCEPTED | Keep test material in #55, never on #21 |
| K14 | The original Antigravity builder posted evidence and PRs after being marked retired | S2 run 2 reader | OPEN | OwnerTeammember · reconcile and annotate in the history index |
| K15 | `gh issue view --json comments` returned a stale last comment for about 3 h (reallakshman19/XML_Compare_Utilities#117 showed 19:58Z while a 23:32Z comment existed; observed by the coordinator, not independently re-verified) | coordinator 17 Oct | FIXED in the coordinator skill (REST `gh api …/comments`) | — |
| K16 | Coordinator status headers used **estimated** clock times (several times on 16–17 Oct) | Owner / self | OPEN (process) | OwnerTeammember · every time from the clock; v3 rule |
| K17 | Registry/doc commits flipped line endings (CRLF↔LF) three times, turning small edits into whole-file diffs | checkers on #54, #57; reset commit | FIXED going forward (edit the repo bytes, `autocrlf=false`, check the diff stat) | — |
| K18 | L1 g2 hit ChatGPT's maximum length with **no standby**; no meter was measured (the code reads `agents[].handover_meter`, but no registry sets it) | 17 Oct 03:39 | OPEN | v3 protocol: a real meter or an early-warning trigger |
| K19 | Codex directives for V/M sat undelivered for 4 h (nobody was assigned to deliver) | 17 Oct | FIXED by role (Codex = planner/reviewer; OwnerTeammember = sole deliverer, #1 6229612086) | — |
| K22 / G-D5-3 | Retired-instance identity cannot be cryptographically authenticated from shared GitHub posts, a claimed 8-character chat ID or role tag. WP-V4 warnings are **source-linked claimed-identity recommendations**, not proof the retired instance actually posted. | [D5 tabletop #55/6245399164](https://github.com/reallakshman19/CoordinatorLandingpage/issues/55#issuecomment-6245399164) | **KNOWN LIMIT / OUT OF WP-V4** | Owner: separate identity/credential-custody decision; do not silently infer real agent identity |
| K23 / G-D5-6 | The guarded chat HOLD delivery route, receipt and returned-agent START HERE reread have not been exercised. Detecting a return in evaluator or displaying a red status does not prove the retired instance received or followed HOLD. | [D5 tabletop #55/6245399164](https://github.com/reallakshman19/CoordinatorLandingpage/issues/55#issuecomment-6245399164) | **KNOWN LIMIT / LIVE D5 NOT_RUN** | Acting OTM/TeamCoordinator: separate authorized live delivery and readback drill; do not auto-send |

## Cross-repo (tracked elsewhere)

| ID | Issue | Where | Status |
|---|---|---|---|
| K20 | Handover Master router blocks every v3.6 request whose BuddyRunner version isn't 1.6, even with a recorded Owner amendment; this contradicts the skill's stated precedence | [Common #408](https://github.com/reallakshman19/Common/issues/408) | OPEN (planned P2) |
| K21 | Any change to the v3.6 PR/issue title grammar would break the landing parser's `[V3.6][O#][PLANNED|IN_PROGRESS|DONE]` regex | [Common #409](https://github.com/reallakshman19/Common/issues/409) | OPEN (planned P3; the landing page should consume scoreboard JSON instead) |
