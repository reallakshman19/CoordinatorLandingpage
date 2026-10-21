# PR137 — operational Dashboard: current recovery state

HANDOVER_READINESS: READY (recoverable and reviewable; not acceptance)
PR_RECOVERY_STATE: HEALTHY
TAKEOVER_AUTHORITY: WRITE_ALLOWED for bounded current Owner assignment
WORK_INTENT: IMPLEMENT
CRITICALITY: STANDARD
REPOSITORY: reallakshman19/CoordinatorLandingpage
PR_OR_WIP: PR137
BRANCH: codex/otm-dashboard-20261021
PR_HEAD_OBSERVED: ccb08f525d0a84f24ad314061fa3b93c0bd46feb (browser capability preflight; no successful application load)
REPORT_BASIS_HEAD: ccb08f525d0a84f24ad314061fa3b93c0bd46feb (unchanged implementation and prior Oracle evidence; this update is recovery metadata only)
MAIN_HEAD_LAST_CHECKED: 4637f83b7cb4dcf48fafa9db98852a1332416ab9
MERGE_BASE: 4637f83b7cb4dcf48fafa9db98852a1332416ab9
REPORT_SYNC: CURRENT (recovery metadata only)
APPENDIX_A_STATUS: NOT_REQUIRED (new standard UI work, no engineering-critical takeover)
GROUNDING_EPOCH: GE-dashboard-20261021-BROWSER-PREFLIGHT
CURRENT_STAGE: BROWSER_PREFLIGHT_BLOCKED — application loading gate not passed
CURRENT_BLOCKER: Browser journeys NOT_RUN: local Chromium absent; official download policy-blocked (403); cloud Chrome localhost attempt ERR_CONNECTION_REFUSED. Independent review NOT_RUN.
EXACT_NEXT_ACTION: Use an environment that proves Chromium can load the exact app, with verified assets and qualified generated/controlled data. Run browser journeys only after that gate; then independent technical review. No next feature or acceptance.

## Handover in 60 seconds
PR https://github.com/reallakshman19/CoordinatorLandingpage/pull/137 is a DRAFT adding a separate Dashboard tab at #dashboard. It reuses the reviewed operational HTML, existing normalized roster/status data, source capture and build-info polling. Source-backed signal lights, ticking evidence/observation ages, known state durations, timer observations, due/late checks, project/state grouping, project rollups and evidence/next-step expansion are wired into the real app. Unknown source values remain unknown; no simulated production rows or dates.

The publisher adds a small latest_report envelope using already parsed, exactly scoped agent reports, with no new GitHub fetches. That envelope is LIVE ONLY: frozen benchmark output remains byte-identical. This live-only boundary fixes the CI-discovered regression in the initial implementation. Oracle checkpoint 1 now supersedes the CLI blocker: all four named suites executed against verified source files at 6db725bb, 93 PASS. Agent 1's own environment remains historically NOT_RUN. Full PR-app browser rendering and independent verification are NOT_RUN. Current actor implements the change and does not claim independent Oracle verification.

## Mission / authority / invariants
Owner directly authorized high/medium ROI coding for a new Dashboard using the provided HTML and data already available. No merge or deployment authorization. Existing Home, status rules, grants, canonical logs, scheduler, delivery, workflow configuration and frozen fixtures/oracles remain unchanged. Source reporting is not approval. Other project HOLDs are not resumed by this work.

Monitor freshness.next_due is a freshness threshold, NOT a scheduled agent check. Timer.next_due is separately labelled and qualified by its observed state/time. ON does not prove agent work or connectivity. Evidence-report age is not a direct activity observation and cannot promote green. Expired/stale/future/incomplete positive evidence is conservatively downgraded. Source-bound state-start absence never becomes a guessed duration. Reported completion freezes only a known claimed interval; acceptance remains separate. Benchmark clocks freeze.

## Implemented files / reconciled ledger
1. site/index.html — Dashboard tab and script loading.
2. site/js/core.js — Dashboard route and disposal hook only.
3. site/style.css — appended scoped responsive/theme rules; existing version stamping reused.
4. site/js/dashboard-model.js — pure projection and strict timezone/time/coverage handling.
5. site/js/dashboard.js — DOM view, clocks, grouping, project rollups, source links and cleanup; one existing status-bar fetch per render, no timer-driven heavy polling.
6. scripts/status_bar.py — additive live latest_report envelope; skips is_benchmark views; existing signal rules unchanged.
7. scripts/landing_build/dashboard_report.py — exact project/id8/generation report join; ignores ambiguous, invalid, foreign, future and verdict-only records; returns qualified source time/permalink and bounded task/next/blocker.
8. tests/dashboard.test.cjs — 13 focused model, DOM consumer, lifecycle, injection/outage, benchmark and route checks.
9. tests/test_dashboard_report.py — 6 claim-binding/publisher/benchmark-boundary checks.
10–12. agents/PR137_workreport.md; agents/claims/PR137.yaml; agents/status/PR137.yaml — own recovery metadata.

Actual GitHub changed-file list reconciled before the benchmark fix: exactly these nine implementation/test paths plus own three recovery records, no unexplained files. Fix changes only status_bar.py, test_dashboard_report.py and own report. WIP recovery records were migrated to PR137. Reconcile final diff again before review closure.

## Validation ledger (implementation basis above)
PASS | LOCAL_EXECUTION | IMPLEMENTATION_COUPLED regression:
- node --test tests/dashboard.test.cjs: 12 tests.
- python3 tests/test_dashboard_report.py: 6 tests, including actual build_status_bar integration.
PASS | LOCAL_EXECUTION | unchanged regression oracles:
- python3 tests/test_wp16.py: all 26 unchanged registered-roster/status/builder checks.
- python3 -m unittest discover -s tests -p 'test_*extract.py' -q: 48 existing extraction/schema/lineage/intake checks.
- python3 -m unittest discover -s tests -p 'test_l2b_intake.py' -q: 4 checks also included in the 48 above; not double-counted.
Total distinct executed checks: 92.
PASS: JavaScript syntax checks and git diff --check.

Original frozen generated-output SHA256 restored EXACTLY:
0a7ebd12ca385963c97adadfeb033a8f88777a4ec6ad9d1bcddf0e785e4095a8
No expected hash, frozen fixture, existing test or tolerance changed. Exact-base fixture bytes were materialized for execution.

NOT_RUN | NOT_OBSERVED: genuine browser/mobile visual inspection, hosted new Dashboard readback and independent review. Browser executable unavailable locally. Minimal DOM harness is behavioral evidence, not browser-layout evidence. The two new test files are not automatically enumerated by current workflows; run their explicit commands during review. No workflow edits performed.

## CI regression / resolution history
Initial implementation 2602fe3d98bcc481efa16cce9f3f41349e0c48c5 and recovery head 90a6c2451fccca083aed31300f61581c7c6d6832 passed the first 43 local checks. Hosted Windows job 119062569259 failed four frozen-output checks because the additive field changed benchmark JSON. Failure origin: INTRODUCED_BY_PR. Fix 73a7914e1276df2421aea6cf27300d60f7f38a57 gates the field to live views and adds the explicit exclusion regression. The exact original frozen hash and 92 local checks pass after the fix. Earlier fingerprints/check counts are historical, not current validation.
The predecessor PR head f639a74b264c9f0cca374eb7ab068757adf9fe92 has 39/39 GitHub hosted checks SUCCESS (checked by Agent 1 on 21 Oct). These are not CLI execution of the new Dashboard suites. Implementation/test commit 8248342b0c631e3f811cf847b53524f90eda57da was observed at 38 SUCCESS and 1 pending; subsequent metadata commits require exact-head CI reconciliation. Earlier head had no submitted reviews, mergeable=true and running/failed checks. No independent approval recorded.

## Grounding / coordination / risks
No AGENTS.md, MASTER_INDEX, or active repo-local claims existed at base. Released landing registry leases inspected. Actual changed-file lists of open #123/#120/#105 and their heads were inspected twice: no scope overlap. #120's description understated its real diff, so actual files governed the check. Classification SAFE for this bounded work. Main last recheck matched base, no drift. Check again before further implementation.

RISK-001 OPEN: browser layout, narrow screen fit, actual keyboard interaction and source-refresh visual behavior not inspected.
RISK-002 OPEN: some canonical sources have no usable timer/start/activity anchors; UNKNOWN is intended. Do not replace missing source values with guessed clock starts.
RISK-003 OPEN: source role labels/shared GitHub account do not independently establish actor identity or acceptance.
ISS-001 RESOLVED_BY_PR: frozen-output regression; live-only envelope fix and exact original byte oracle now pass locally. Hosted latest-head confirmation remains pending.

## Exact continuation
Fetch live PR137 HEAD and main; inspect this report and final changed files/checks. Run the two new suites plus existing WP16/extraction checks explicitly. In a real browser, open #dashboard at desktop, 390px and 320px; inspect due->late, timer vs monitor-limit labels, state/project regrouping and expansion, source outage, benchmark freeze, source refresh, and navigation away/back. Inspect latest_report binding and source-link fences. Review narrow-width layout before approval. Preserve existing authorizations, status semantics, scheduler and delivery.

Local scratch git is a selected-source materialization, not the true repository commit graph. Unchanged producer dependencies, test inputs and exact-base registries/fixtures were materialized solely for local checks and are NOT PR changes. GitHub base/head/diff are authoritative. Remote implementation and metadata commits preserve recoverable history. No agent was spawned; no external chat message or dispatch sent. No merge/deploy performed.

## Agent 1 bounded continuation — 21 October 2026

**Role / takeover:** Continuing the existing open PR137 under the stated bounded Agent 1 assignment; no separate native actor ID, lease, grant or takeover receipt asserted. Main remained `4637f83b7cb4dcf48fafa9db98852a1332416ab9` at PR inspection, and the pre-continuation PR head was `f639a74b264c9f0cca374eb7ab068757adf9fe92`. Four open PRs (#137, #123, #120 and #105) were inspected: the three other PR changed-file sets do not overlap Dashboard/report/status recovery files; no submitted #137 review or PR discussion comment observed. Recheck live state before further mutations.

**Reproduction and smallest patch:** with a valid status_bar.v1 document containing one project and state.projects = [] (controlled missing `projects.json` response), the existing Dashboard strip visibly displayed `0 projects`. The app projects catalog is auxiliary to this strip's status-bar projection. Change only `site/js/dashboard.js` to count `source.projects` and use singular/plural text; add focused regression `tests/dashboard.test.cjs`. Controlled V8 consumer replay changed `0 projects` to `1 project`, without touching source meanings, model thresholds, joins, timers or publisher. Test head `8248342b0c631e3f811cf847b53524f90eda57da`; UI commit `2f019605b80efe94b4316f51bdbaaa8e812c6b5b`. Implementation/test changed paths exactly these two; recovery synchronization modifies `agents/PR137_workreport.md` and `agents/status/PR137.yaml`. No other implementation paths touched in Agent 1 continuation.

**Verification ledger — scope and provenance are essential:**
- PASS | CONTROLLED_JS_EXECUTION | Exact fetched pre-patch Dashboard model and consumer, 13 separately asserted cases including strict dates, source downgrade, freeze, due-to-late, expansion, qualified evidence, timer cleanup, injection/outage, late fetch and no tick refetch, all 13/13; source under old PR head f639a74b2… .
- PASS | CONTROLLED_JS_EXECUTION | Original `tests/dashboard.test.cjs` 13 test callback functions (including new project count regression) executed 13/13 using a V8 compatibility shim for Node's test/assert/fs/vm on the exact fetched implementation/test source at `8248342b0c631e3f811cf847b53524f90eda57da`. This is NOT `node --test` and NOT full Node runtime qualification.
- PASS | CONTROLLED_BROWSER_FIXTURE | Headless Chromium (Playwright `page.set_content`) at 1280, 390 and 320 CSS pixels, representative static Dashboard markup and the excerpt of actual scoped CSS rules, measured document scroll width equal to viewport width, native details opened with Enter, focused summary outline solid. All source strings/sample dates in this witness are explicitly **test fixtures**; this is NOT a checkout/served actual PR application or a source-refresh/route QA proof. Screenshots existed in the executing ChatGPT container at `/mnt/data/pr137_fixture_qa/fixture_{1280,390,320}.png`; these are conversation-local, not durable GitHub attachments.
- PASS | HOSTED_HISTORICAL | At former PR head f639a74b2…, GitHub check-runs API returned 39 completed/successful out of 39, with no submitted reviews. At implementation/test head 8248342b0…, 38/39 completed/successful at last observation; recheck final metadata-head CI.
- NOT_RUN | LOCAL_CLI_ENVIRONMENT | Requested `node --test tests/dashboard.test.cjs`, `python3 tests/test_dashboard_report.py`, `python3 tests/test_wp16.py`, and `python3 -m unittest discover -s tests -p 'test_*extract.py' -q`. Checkout/materialization of the complete repository unavailable from this runtime: `git ls-remote` returned `Could not resolve host: github.com`; direct URL network and IP-pinned curl also failed. Files could be inspected via authenticated GitHub connector but not cloned into the CLI runtime. The previous 92 PASS suite count is historic and must not be reported as rerun.
- NOT_RUN | ACTUAL_PR_BROWSER | No browser visit of a locally served or hosted **PR137** application; full navigation Home → Dashboard → Project/evidence, real desktop/mobile fit, source refresh, benchmark UI, and source-error/visibility journeys remain unproved. Chrome `file://` and localhost navigation to a controlled fixture were `ERR_BLOCKED_BY_ADMINISTRATOR`; only in-memory `set_content` fixture rendering succeeded. The available public Pages URL is not the draft PR source.
- NOT_RUN | INDEPENDENT_REVIEW / MERGE / DEPLOY / CHAT_DISPATCH | No approval asserted or permission enlarged.

**Risk / allocation:** This bounded presentational mismatch was directly reproduced on the actual fetched consumer with a controlled missing-catalog fixture; a one-line change and one regression are Medium effort/high practical value relative to confusing false source counts, with no quantified savings claim. Rejected: creating fake project catalog entries, changing publisher roster coverage, widening status rules, and implying that fixture QA equals genuine hosted/mobile QA. Browser and CLI limits are explicit and do not erase predecessor negative findings.

**Oracle handoff:** Recheck final head, 39 CI checks and overlap; inspect the one-line correction and 13 callback-function fixture results. Obtain actual PR-app browser/mobile/keyboard/source-refresh/lifecycle evidence and execute four exact CLI commands in a checkout-capable environment. On a discrepancy, identify the first faulty source → projection → DOM boundary before creating status/time/authority rules. Preserve UNKNOWN and qualified evidence semantics. No Agent 2, merge, deploy or Owner acceptance initiated.

## Same Agent 1 — verification continuation and capability gate (21 October 2026)

**Boundary:** Continued the same PR137 and preserved implementation/test basis `8248342b0c631e3f811cf847b53524f90eda57da`. This continuation was **verification and recovery metadata only**. Immediately prior to the present report update, live `main` remained `4637f83b7cb4dcf48fafa9db98852a1332416ab9` and PR137 remained OPEN/DRAFT, mergeable and at `a32f3308a4863e307b03ce5d60b6fd116b285b86`; no submitted reviews or discussion comments. The actual PR changed-file set remained nine implementation/test paths and three own recovery paths. All 39 of 39 check-runs on **that precise pre-handoff head** were completed with conclusion SUCCESS (GitHub Checks API `/repos/reallakshman19/CoordinatorLandingpage/commits/a32f3308a4863e307b03ce5d60b6fd116b285b86/check-runs?per_page=100`, latest observed completion 2026-10-21T06:54:05Z). The two new Dashboard suites are not enumerated by those workflows, so this is a bounded hosted-check claim, **not** Dashboard CLI or browser qualification. Once this documentation commit advances HEAD, independently recheck CI on the NEW exact head. Historic earlier 92 local checks remain predecessor evidence, not this continuation's execution.

**Capability check — new runtime available, missing essential source checkout:** Container `/mnt/data` has no `CoordinatorLandingpage/.git` and contains only the previous static CSS/markup fixture directory; no complete PR application, dependency set or frozen input fixtures. `node --version` = `v22.16.0`; `python3 --version` = `Python 3.13.5`; `chromium --version` = `Chromium 144.0.7559.96` (Debian). A single standard repository transport capability probe, `timeout 12s git ls-remote https://github.com/reallakshman19/CoordinatorLandingpage.git refs/heads/codex/otm-dashboard-20261021`, exited **128**, `Could not resolve host: github.com`. No DNS/IP bypass attempted or repeated. Authenticated GitHub connector reads **can** verify exact source blobs and CI metadata but cannot materialize a complete working tree in this CLI/browser container through the available interface. The prior browser restriction (`ERR_BLOCKED_BY_ADMINISTRATOR` for `file://` and localhost fixture routes; `page.set_content` CSS-only witness) was already documented. Presence of a Chromium binary does not establish a running **actual PR** app. No browser-route retries against a substitute, public-main deployment or CSS fixture were relabelled as PR QA.

**Requested exact commands (all NOT_RUN, not FAIL):**
```
node --test tests/dashboard.test.cjs
python3 tests/test_dashboard_report.py
python3 tests/test_wp16.py
python3 -m unittest discover -s tests -p 'test_*extract.py' -q
```
Reason: no verified local input tree and dependencies at the exact PR head. Consequently there are no new command outputs, exit codes or executed test counts to report. Historical V8 compatibility-harness results (13/13 callbacks) and predecessor CLI results (92) retain their original, narrower provenance. **No local candidate re-run** and **no actual PR browser QA** occurred in this continuation.

**Exact candidate/source identification for a capable verifier:** pre-handoff PR HEAD `a32f3308a4863e307b03ce5d60b6fd116b285b86`, repair/test commit `8248342b0c631e3f811cf847b53524f90eda57da`, original implementation `73a7914e1276df2421aea6cf27300d60f7f38a57`. Retrieved Git blob object IDs (not SHA256): `site/js/dashboard.js` `a076f19293165105a6ff1e5f87a8140082aa9405`; `site/js/dashboard-model.js` `ec6769dfe696bdfbf64018e81552300671adf09f`; `tests/dashboard.test.cjs` `68af5a3d17ff4da4d3a2d7483fd9efac80265172`; `tests/test_dashboard_report.py` `af9b09aa071adb31e20e6e875809d64ca624c172`; `tests/test_wp16.py` `d7085c06be84d8dc217eef85260ddab621551841`; `scripts/status_bar.py` `ea6f27cd07a27ca4d6948d87197380920887673a`. The predecessor's restored frozen-output SHA256 `0a7ebd12ca385963c97adadfeb033a8f88777a4ec6ad9d1bcddf0e785e4095a8` is *historical*, not freshly verified.

**Previously created CSS-only fixture manifest (NOT an app or release artifact):** `/mnt/data/pr137_fixture_qa/fixture.html` SHA256 `90b66dd1fb81979dbc8ab9abacf985e0c14e5fbb7e015d3a5bb27c00c9a97744`. PNG SHA256: `fixture_1280.png` `0046d0e6e4769a90a96c61807ee4663f1a08310cb713ae881472870a571c5339`; `fixture_390.png` `deed93507bec103253020238d3fc6e4d7eae8dfc4748f57a7dc85dd479c21a91`; `fixture_320.png` `d6c69286c2b79ca795edc0e503d83d681d000719921e2ae4551cffc664330341`. Those files are **not portable across agent environments**. The durable reproduction for the count claim is the committed test case in `tests/dashboard.test.cjs` and the Git diff for `site/js/dashboard.js`; this report is the portable index, not the screenshot link.

**Claim-versus-surviving-error challenge:**
1. **Bounded Agent 1 count claim, previously exercised:** Governing expectation is that the Dashboard's displayed source count reflects the `status_bar.v1.projects` projection even if the optional `state.projects` catalog fails. Competing behavior uses the catalog count. Discriminator (controlled existing DOM-harness fixture in `tests/dashboard.test.cjs`): one status-bar project, missing/empty catalog. Predicted text: source-based implementation `1 project`, catalog-based implementation `0 projects`. Previous Agent 1 execution observed original `0 projects`, patched `1 project`, and regression pass on `8248342b0…`; author-produced fixture and expectation have **not** been independently reviewed. A plausible surviving error is that `status_bar.projects` itself can be incomplete or inconsistent with declaration coverage; counting it correctly does **not** establish complete roster or project integrity, so no completeness verdict is promoted.
2. **Ticking clock versus fresh agent activity — NOT_RUN in actual app:** Requirement: recorded `observation.observed_at` and direct activity age are independent of `build-info.source_capture_at` and page clock ticks; capture freshness must not reset an agent-activity timestamp. Competing interpretation treats each build refresh as agent activity. Discriminator: fixed agent `observed_at`, advance browser time and refresh only build capture, compare Direct activity observed field before/after. Correct outcome: original observed timestamp remains and age increases; competing outcome: activity timestamp refreshes or age resets. Source-code inspection and a model harness cannot establish full deployed rendering/refresh. A changed-build, same-observation PR-app witness is **NOT_RUN**, claim-level HOLD.
3. **Real navigation/lifecycle/viewport/refresh — NOT_RUN:** Wrong route wiring, stale promises reviving detached views, mobile clipping, inaccessible focus, or extra network fetches could escape all 39 hosted checks and CSS-only witness. Discriminator is a served exact-head PR application at 1280/390/320, including direct `#dashboard`, Home return, grouping and expanded same agent, keyboard, repeated navigation/visibility, delayed fetch, invalid/unavailable source, due-now→late, frozen benchmark, and changed build signature. Require explicit capture versus agent-observation ages and source/fixture labelling. No actual-app pass inferred.
4. **Source/authority semantics — UNKNOWN until corroborated:** `monitoring.next_due` is a freshness boundary, not an agent check or permission; `timer.next_due` is separately conditional. Do not reinterpret `UNKNOWN` based on new capture or post-hoc expected values. Oracle should adjudicate any genuinely contradictory source projections, without converting a hypothesis into an automatic repair.

**Minimal reproducible next action for a genuinely capable verifier:** acquire and verify full exact PR commit source via an authorized repository checkout or complete connector-backed materialization; verify dependencies and the frozen fixture tree against the same commit; run the four commands above and record stdout/stderr, exit statuses and exact hashes; use the existing `.github/workflows/deploy.yml` publication path and documented local serving path to build/serve a read-only PR candidate; execute the listed browser interactions and preserve URL, viewport, source vs disposable fixture, screenshots/console/network witnesses and version/build signatures. Preserve original oracles and existing Home/publisher; do not deploy as an alternative to QA. Only then pass scoped results to Oracle for challenge and separate independent review. The present restricted environment is not an adequate substitute for that verifier.

**Continuation disposition:** no new product code, schema, thresholds, schedules, grants, workflows, external messages, merge or deployment; only this report plus its matching recovery-status record. Agent 1 stops at Oracle handoff, not self-approval or Agent 2 assignment.


## Oracle checkpoint 1 — actual execution and bounded challenge (21 Oct 2026)

**Current verdict: HOLD for full-application acceptance. CLI gap CLOSED; browser and independent review remain OPEN.** This Oracle authored the original Dashboard implementation. Its checks of that implementation are contributor self-review, not independent acceptance. Agent 1 authored the count repair. No production, schema, workflow, expected fixture or shipped test was changed in this checkpoint.

### Grounding and scope
Source head: `6db725bb71149ff1d4335c2ec302168e1c5baec6`; main/base: `4637f83b7cb4dcf48fafa9db98852a1332416ab9`; OPEN/DRAFT. At that source head, 39/39 hosted checks SUCCESS and zero submitted reviews. These CI observations do not certify the later evidence/recovery commits; refresh their exact-head checks before review closure.

Live diff before this checkpoint: the nine documented production/test paths and three recovery paths. Open PR123/120/105 changed NextNudge paths; no exact-path overlap with these evidence/recovery additions. Coordination classification: SAFE for this bounded evidence/report update; no inference of authority for other domains. No AGENTS.md or agents/MASTER_INDEX.md was present in the inspected source tree.

Two additional paths are now part of the reconciled ledger:
- `agents/evidence/PR137/oracle-checkpoint-1.cjs`: rerunnable diagnostic, wrapping the existing test harness without changing shipped tests.
- `agents/evidence/PR137/oracle-checkpoint-1.json`: source manifest with Git blob IDs and SHA256 for 75 existing files, actual CLI logs, diagnostic logs, failed-mutant witness, environment and limitations.

The local tree is a selected-source materialization, not a full remote Git checkout. All 75 existing remote-listed files in that materialization matched exact-head Git blob hashes before execution evidence was assembled; mismatches were synced from that exact revision. The four suites executed with their actual dependencies and frozen inputs. This establishes those suite executions, not completeness of an application checkout or browser readiness.

### Actual CLI ledger
All four returned exit code 0, LOCAL_EXECUTION:

| Command | Actual result | Expectation qualification |
| --- | --- | --- |
| `node --test tests/dashboard.test.cjs` | 13 PASS | Author/contributor-coupled model and DOM assertions; not browser layout |
| `python3 tests/test_dashboard_report.py` | 6 PASS | Contributor-authored report/publisher regression |
| `python3 tests/test_wp16.py` | 26 PASS | Existing source-derived roster/status/builder suite |
| `python3 -m unittest discover -s tests -p 'test_*extract.py' -q` | 48 PASS | Existing extraction/schema/lineage/intake suite |

Total: **93 distinct suite tests**, not predecessor 92 and not 93+17. Diagnostic reruns the 13 Dashboard tests and adds four assertions. Frozen-output witness remains exactly `0a7ebd12ca385963c97adadfeb033a8f88777a4ec6ad9d1bcddf0e785e4095a8`. Node v24.19.0; Python 3.12.14. Full command outputs and input hashes are in the JSON evidence.

### Claim, competing interpretation and falsifier
**Bounded claim:** the monitor strip counts the entries of the same `status_bar.v1.projects` array consumed by the Dashboard, independently of auxiliary `projects.json`, with singular/plural wording. This follows the Owner's reuse/condensation requirement and the displayed source model. It does not establish unique real-world projects, completeness of the roster, source truth or all Dashboard correctness.

**Surviving error:** hardcoding `1 project` passes all 13 submitted Dashboard tests, including Agent 1's new missing-catalog regression. Thus that regression alone cannot justify the broader count claim.

**Discriminator actually executed:** zero source projects with two auxiliary entries; two source projects with no auxiliary entries; two source projects with one conflicting auxiliary entry. Each predicts the source-array count, not an auxiliary count or constant. Actual patch: all three PASS. Injected hardcoded-one mutant: all 13 submitted tests PASS, all three count challenges FAIL, process exit 1. This is a demonstrated test-coverage weakness, not a defect demonstrated in the repaired production code.

**Separate timing challenge:** fresh source capture with a 40-minute-old direct observation must retain 40-minute activity age, show YELLOW, and advance to 42 minutes after two minutes without another fetch. Actual model/DOM execution PASS. It does not substitute for browser visibility, refresh, navigation or layout journeys.

Diagnostic command: `node agents/evidence/PR137/oracle-checkpoint-1.cjs` → 17 PASS, exit 0. Mutant command: `ORACLE_MUTANT=hardcoded-one node agents/evidence/PR137/oracle-checkpoint-1.cjs` → expected exit 1 (14 PASS, three count failures). The diagnostic uses the existing author harness and Oracle-authored assertions; keep expectations and independence qualification explicit.

### Remaining verifier assignment — capability gate, then actual app
Do not start another feature or repeat the completed CLI work without a relevant source change. Use the same agent if it obtains the required environment; otherwise assign a verifier in an environment that actually has both the exact PR application and a working browser. A new chat in the same restricted environment is not remediation.

1. Establish fresh PR/main SHA and exact source materialization. Prove the real application can be served and opened by the browser before accepting this assignment as executable. Preserve the head used, loaded asset/input hashes, commands and actual outputs. Authoritative API materialization is acceptable if all load-bearing assets/dependencies are verified; do not claim a clone or full app from four fetched files.
2. Open the actual `site/index.html` application at `#dashboard` with its real routing, CSS and scripts, using controlled source responses where necessary. Label controlled fixtures separately from live data. Capture desktop 1280px, 390px and 320px; inspect overflow, readable timing, grouping, expansion, project/evidence navigation and source-error presentation. A standalone CSS fixture does not satisfy this.
3. Exercise due → late, PAUSED/UNKNOWN, stale activity with fresh capture, benchmark freeze, Dashboard exit/re-entry, hidden/visible return, delayed source response after navigation, and existing build-info-triggered refresh. Check correct data replacement and interval/listener cleanup; a ticking device clock must never imply renewed agent activity.
4. Apply the same hypothesis/competing interpretation/discriminating-fixture discipline. For every claimed PASS, ask which significant wrong behavior could still pass. Record any contradiction as FAIL/HOLD/UNKNOWN and keep it separate from environment limitations. Make no speculative repair. If a defect is reproduced, return the minimal evidence and affected boundary to Oracle for the next bounded task.
5. Return evidence for the exact tested head and a qualified verdict. A reviewer who authored the affected change retains self-review qualification. Separately required independent technical review must examine the original Oracle contribution and its expectations before Owner acceptance. No merge, deployment, dispatch or Owner acceptance is authorized by this assignment.

Local browser evidence: Playwright package exists, but launch with a writable TMPDIR fails because its Chromium headless-shell executable is missing. Actual PR-app browser journeys remain NOT_RUN; this environment failure is not a product failure. No independent reviewer has accepted this PR.

### Continuation decision
Preserve Agent 1's repair. Current high-value next stage is **actual-application browser verification**, followed by independent review of consequential claims and Oracle-authored contributions. It is not the next feature. Oracle checkpoint 1 remains partial until that evidence arrives; then choose repair, falsification or feature work from the observed result.


## Authorized browser verification attempt — 21 Oct 2026

**Disposition: environment-blocked before loading gate; browser QA remains NOT_RUN and acceptance remains HOLD.** This supersedes no established test result. It adds no UI PASS, product FAIL, review approval or acceptance. The 93 CLI tests and earlier counterexample evidence retain their recorded scope; this session did not rerun or broaden them.

### Exact basis and preparation
- Live source/checkpoint head: `ccb08f525d0a84f24ad314061fa3b93c0bd46feb`; main/base `4637f83b7cb4dcf48fafa9db98852a1332416ab9`; PR OPEN/DRAFT; 39/39 hosted checks SUCCESS; zero submitted reviews, rechecked before this recovery update.
- Materialized and verified 34 committed app-shell/data files against that head: index, stylesheet, every classic script loaded by index, and tracked site/data JSON. Every byte sequence matched its Git blob ID. The manifest below records separate SHA256 input hashes.
- This is selected-source preparation, not a full Git checkout or proof of a runnable application. Generated `data/status-bar.json` and `build-info.json` are not tracked in that commit; qualified generated or controlled responses still need to be supplied by the actual-app runner and labelled by origin. No newly generated data was claimed live or accepted.

### Executable preflight and actual observations
Local inventory found no Chromium/Chrome executable on PATH. Playwright is installed at `/opt/codex/runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright`.

Attempted official browser acquisition:

```sh
TMPDIR=/workspace/scratch/43db3e4ed079/landing-plan-runtime \
PLAYWRIGHT_BROWSERS_PATH=/workspace/scratch/43db3e4ed079/browser-runtime \
node /opt/codex/runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright/cli.js install chromium --only-shell
```

Observed: download for Chrome Headless Shell 151.0.7922.34 / Playwright v1234 from the official Playwright CDN returned HTTP 403 with `Forbidden. Calls to this URL are not allowed.` The installer retried automatically; it was interrupted (exit 130). No alternate download host, proxy, policy change or bypass was attempted. This is an environment policy block, not a product defect or bot-detection claim.

Attempted server process:

```sh
python3 -m http.server 8765 --bind 0.0.0.0 --directory /workspace/scratch/43db3e4ed079/dashboard-work/site
curl -I --max-time 3 http://127.0.0.1:8765/
```

Observed: the server invocation remained running without a successful readback; curl returned exit 7, connection refused. The server was interrupted after the preflight (exit 130). Do not infer that a working server was established.

Cloud Chrome inventory supplied a CDP browser. Through its documented browser API, attempted:

```js
await cua.createBrowserTab(browser.browserId, 'http://127.0.0.1:8765/#dashboard');
```

Observed: `Browser Use cannot open http://127.0.0.1:8765 in tab 1. Browser reported: net::ERR_CONNECTION_REFUSED`. There was no successful document/application observation. Browser-side telemetry also logged unrelated forbidden requests; those are not application failures. No other local hostname, tunnel, public hosting/deployment or security change was attempted to bypass the limitation.

### Bounded verdict and allocation
- Loading real PR137 app in Chromium: **NOT_RUN / NOT_OBSERVED**, capability preflight blocked.
- Desktop 1280px, 390px, 320px journeys: **NOT_RUN**, dependent loading gate not passed.
- Navigation/expansion, timing boundaries, fresh capture with stale observation, source/build refresh, error handling, visibility and timer/listener cleanup: **NOT_RUN in an actual browser**.
- Independent technical review: **NOT_RUN**; original Oracle authorship/self-review qualification retained.
- Runtime failure origin: environment; no new product failure demonstrated. No production/test code, expectations, fixture or workflow was changed.

Next actor must have actual app-serving and Chromium capability in the same usable environment. Before accepting the verification task as executable, show the exact app loaded at the tested head and verify loaded assets/data provenance. Then execute the existing browser assignment above, retain runnable scripts, input hashes, actual outputs and screenshots, and return bounded results. Do not repeat the completed CLI stage merely to replace the missing browser evidence. If source changes, reconcile the applicability of prior evidence. Independent technical review remains a later gate before Owner acceptance.

This recovery update changes only this work report and own status record. It preserves all prior implementation and evidence artifacts. The new metadata commit's CI must be checked separately; 39/39 above refers to the observed source/checkpoint head.

### Verified input manifest (preparation only)

| Path | Git blob | SHA256 |
| --- | --- | --- |
| `site/data/evidence-6ad02128.json` | `57d7d67bd71f664a34fe2d1dbe7bdaade5d3302d` | `1850226a5b8e2004ad3c6878e9e44747be4c9a42b316c4b350d37dd38df72817` |
| `site/data/evidence-6ad02130.json` | `af9645e344f83a99179ec3d4a9078bb2d60ae7f4` | `cd2b75a209ea25011a2a5bfa21e623c331948fc0fda2ab400ffedc30c236f366` |
| `site/data/evidence-6ad04451.json` | `10257aaca0f3f4a25ab734262b0ec3e67c04df2a` | `eb5890a2b3b2a33d3d8fa8f732c2a4aed4a4c9eb251d91083c133892b53b4683` |
| `site/data/evidence-6ad0449d.json` | `c05fdfd49ddfb16207b0a7ac153ef70e46de7723` | `049c6e58ccf82ae5fe4370f9a88ee78274a91a0d4bd95d33c1994c6bc2c0c1d1` |
| `site/data/evidence-6ad0506c.json` | `a8dfa72d3c5d3e1104b19b926da9e8be56a5dad7` | `0d266353d338556f5b07ec5e6548de2595f7f282ec21d56c20839152bdc7fe5b` |
| `site/data/evidence-6ad0508a.json` | `b6de91fc097ec8f0ca1e3ebfb826997cd6c71d83` | `29169e43da6b286d6c373abc431226bbe7714786c868f1a2b4c27e997357c87e` |
| `site/data/project-grade9-pilot.json` | `0aeb9ca49e5df7f798cc553e362df89405d8be68` | `d97c06d368c919122b416486e8ae050f8ab523e23d89de81486b600b099bb6ba` |
| `site/data/project-imo-ab-test.json` | `877ab8cac1d0b3a57ab556a1dc3e981368581297` | `2a551282f80fa7da164a492589b25e78233e21d7814921cebabb646f0b660ab2` |
| `site/data/projects.json` | `57a4443ab053e7c7bed9c5a36b510f3a582e0191` | `ae0aec1ea9fa2c294b55ea6da110ae34b805f5723f8c91c799e7284cff2dfd75` |
| `site/data/timeline-grade9-pilot.json` | `5d7069789cf8d7f643d37f3a47e3ead135ad1026` | `6a36a58c456abfc4f700997cb3e5a3026df5f6c7ace45d5164851818c9090c03` |
| `site/data/timeline-imo-ab-test.json` | `b8afa96bb7c68346f0481df87b48733a15080396` | `7f264c7d14bf528c3cb5d4c62b9d3ce2c93a75cac38a7201e947b95b7a238f6d` |
| `site/index.html` | `f5ffe380d4934582bafea35974896bbf90a677b0` | `468bb27e7ede43b24f807e115a86dba6708be820b6c0e7eea7daaecd1e8f9a37` |
| `site/js/agent.js` | `a4cf82e98cbd0d90e3317411ffad0575567cee4d` | `d7f2d05a1af4ce3f99b080ce9c1f32e5b54e6a2a4491c8fd7865968a8d7e54f6` |
| `site/js/benchmarks.js` | `f126ce9a530785c2f0c2cdeab00cd33d07e549b5` | `0e4d5a070d89b9174b410be6b19591e3b53a1ce6659c9ecf8946875d1686b4ec` |
| `site/js/core.js` | `c58e488aed7973eb3b11d5b431d0d5352578adf0` | `0df0492a5d9a26a2769873e4812acf8e06df4da844f07dfdd25f7f2368a09cdb` |
| `site/js/dashboard-model.js` | `ec6769dfe696bdfbf64018e81552300671adf09f` | `b814d95d7c05b40076912908b1fac4fae009f7a2f3e36796bd0325988a8ec792` |
| `site/js/dashboard.js` | `a076f19293165105a6ff1e5f87a8140082aa9405` | `13b4e5af3d895b2b965747aa0f215578ed5a28f98b75bc5b89cea1a9ab56c8d4` |
| `site/js/home.js` | `10552e5808c7571b87903704a89a6f4beca0af1c` | `30e300a9ac1289cef7fb068b2248a1f437f6851bf5eae91eb766c9938c084d4a` |
| `site/js/l4_changeover.js` | `c12a07b4e944108d4176fc99efbdb4032144046c` | `d0ee860087295f7cbffc41e58eb9386e61aa1ae217b3516d7d35435af8f065c1` |
| `site/js/l4_common.js` | `3b8dc5f2ab66fea526ac839555642a4136d9ea0d` | `f64aaff4fbd8a425788b55bd8581d2e621aeaf9ad5d1407a1e31d09a0061349b` |
| `site/js/l4_engineering_history.js` | `195410e480d3a6c944e2ba426b21b4e41a844dbf` | `ed13ab546811df5877085e0f51f3aeaa127d521fd1fec9da051139423b76b70e` |
| `site/js/l4_improvements.js` | `f371b216d4b68f6a8b746d73726beeb54fd8381f` | `13ae51658f8a2e84b1821a57c9adb77c77380992fd77f53ea51660021987fc7a` |
| `site/js/l4_people.js` | `d7d391e695279a7ec805c15b2a5c1ae2acd41789` | `35f7a8ca91c4c180118188f83c231a5248d74061932566a33c1b46796169da60` |
| `site/js/l4_sources.js` | `6f0880725ef2f5cd61df0d4aebf7931cf2ba07d0` | `0c4fbad9469a9173eb0ba13bfa9e7d4c3528c93698e6f0b624881919210642a7` |
| `site/js/l4_understanding.js` | `e3b352e56c55d6bda8ae70a15b87770c8e841249` | `b528816a2a1ce188daa584bcf02def917ee9cc7feb610b3f15898df5f373e758` |
| `site/js/nextmove.js` | `e060653ea52ef5749d9f432be330f0e882c8ce86` | `0f849fbec1854b6ed7cff9fedfe10f1236d856a650750812e7cf8779cb9c3404` |
| `site/js/owner_inputs.js` | `81a53d8f54ee1ad87558f2ab4bbab2ea7fb398b2` | `2e6b1b2d0a2656159bf25802e6ab8276d8f7a95a4f6f653e6e13c35d6969b174` |
| `site/js/project.js` | `063cb723dfd849ec2d0c823f1bf4dd64b16c7a53` | `4b992abf87370dc97c7f22a079107097a77d96da9095d95cf73b62c93cb09a64` |
| `site/js/protocol.js` | `876a1dba5f0322a781c1d03c1367cb13a75be839` | `c5c6280ebe0194fc08337d3e086af494cd1f0d876f57f3d3a7cf022249fef921` |
| `site/js/statusbar.js` | `6347d4e28e681f19cddbf07800daa968f08e1261` | `00929ba306265df50f061acd70e03cf0cab86c38a22ab0410936e06280a0337a` |
| `site/js/timeline.js` | `b840ea43c62c96bdf6655e279e89c3eb667b2373` | `0f9b904db889f10232384758c04d6a0c829f01bbd7dcc36c55bee6de42a237c6` |
| `site/js/trace.js` | `604aa0e06fae85ed7a4f2e071897029909e10efc` | `7c738579b7808fb9a8d50366c6543a834ad68560be934563a922ca18fcd45aee` |
| `site/js/v36_scoreboard.js` | `c0b0ea88f9ed10aec806e75bd147c28f8e9f2116` | `6aa05121b9d7ad8d8cd341518edfe0f6583017acf97d8172589e0eee2fc404a6` |
| `site/style.css` | `c8f1f4d4bd2713dbd81012842ec2acefc9ba621d` | `7fbd831685ded6b2ef4727b3f001688ccaa3da46fe634a0608b6d65f99039c81` |
