# landing-live — current brief, history index and authority map

**Start here.** This is the navigation page for a new agent, reviewer or successor on the landing-live project. It is an **index over the authoritative sources**: it is not itself authority, approval or acceptance. If anything here disagrees with a linked source, the source wins, so report the disagreement.

- **Root issue:** [#21](https://github.com/reallakshman19/CoordinatorLandingpage/issues/21) (Owner intent). **Evidence thread:** [#22](https://github.com/reallakshman19/CoordinatorLandingpage/issues/22). **Owner decisions and control:** [#1](https://github.com/reallakshman19/CoordinatorLandingpage/issues/1).
- **How the code turns inputs into the page:** [docs/ROUTE_MAP.md](ROUTE_MAP.md).
- **Built from:** Codex's S1 source reading (17 Oct 2026, 05:56–06:03 Dubai, main `23843c96ee142ea21577312b504d4ba6cb3f8fc8`). Corrections and the current state come from OwnerTeammember (17 Oct, after the S2 cold-reader test on #21 judged PARTIAL).
- **Pins are history.** Re-check main, PR heads and the registry before acting on anything here.

## 1. Current state (17 Oct 2026)

- **Aim:** keep the existing landing page and make evidence-backed, two-way, multi-project coordination live. Owner words on #21: no Dash V2, no revamp, no core protocol change. The page is a view. It never sends to chats, approves or grants anything.
- **Code:** everything through WP18 + NM0 is merged. The last integration was [#50](https://github.com/reallakshman19/CoordinatorLandingpage/pull/50) → main `885d95b4c115b2eb5f0b47bdd80f8ae5d70bda12`, and no PR was open at the S1 read (this page itself arrives via PR #54). Later main commits change records only: registries, the reset, and these docs.
- **People and authority:**
  - The Claude session is TeamCoordinator + OwnerTeammember: one actor, and the only one who sends to chats.
  - Codex is planner + reviewer: GitHub outputs only, no chats, no browser.
  - landing-live has `criticality: normal`, with merges delegated after an independent exact-head check (revocable). This is **not** acceptance.
- **Agents:** **no active implementer.**
  - L1 g1 `6ad0adca` retired on 16 Oct (its chat failed to load).
  - L1 g2 `6ad1a045` retired on 17 Oct 03:39 (its chat reached ChatGPT's maximum length, and no standby existed). OwnerTeammember wrote its 1a as G1 ([#22 6226735852](https://github.com/reallakshman19/CoordinatorLandingpage/issues/22#issuecomment-6226735852), with a later correction comment on #22).
  - **No g3 has been selected**, and its writer lease is released (registry `leases[0].released`).
- **Parked:** UltraEconomyMode (Owner, 17 Oct: "UEM is later. Park it."). It is enabled in no registry, and agent timers are NOT_ARMED. GitHub-pull delivery is not approved. The Next Move pilot is enabled, but no real move or evaluator record exists yet: no GO has been recorded, and the task count is UNKNOWN.
- **Operational HOLD:** under the Owner's 17 Oct HOLD, no chat sends or cycles run. Read-only work and record fixes the Owner asked for are allowed.
- **Other projects:** grade9-pilot, imo-ab-test, cii-method-c and xml229-output are SUPERSEDED ([#1 reset](https://github.com/reallakshman19/CoordinatorLandingpage/issues/1#issuecomment-6227912673)). Their history is kept, and they are not reopened. **Future programme:** P1 landing-page revision, P2 Common#408 and P3 Common#409 start only "once our protocol is ready" ([#1 6228221349](https://github.com/reallakshman19/CoordinatorLandingpage/issues/1#issuecomment-6228221349)).
- **Next action:** nothing runs until the Owner names new landing work and lifts the HOLD. Then the native route: a successor from the corrected 1a, its own-words 1b, then a fresh writer-lease remap.



## 1b. Operations: who may do what (17 Oct 2026)

Each step has its own actor and proof. **A doer never verifies its own work, and nobody accepts their own work.**

| Step | Who | Authority source | Stops it | Proof that it happened |
|---|---|---|---|---|
| **Approve** a landing-live next step | Owner, or OwnerTeammember ("OTM-approved", logged in #1) | Owner 17 Oct 03:5x (only critical projects need the Owner): [#1](https://github.com/reallakshman19/CoordinatorLandingpage/issues/1); registry `criticality: normal` | an Owner HOLD (registry `control.hold`), Owner revocation | an #1 line naming the step and its basis |
| **Act / implement** | the current writer-lease holder only. **There is none now** (L1 g2 retired; `leases[0].released`) | a registry lease + a GO on #22 | HOLD, lease release, scope beyond the GO | TASK EVIDENCE v2 on #22 at an exact head |
| **Deliver** to an agent chat | TeamCoordinator/OwnerTeammember only (the single deliverer). Codex never delivers | #1 control (epoch 1) + Owner 17 Oct (Codex = planner/reviewer) | HOLD (no sends now) | Next Move states: SENT_TO_CHAT, then PICKED_UP. Publishing on GitHub is not delivery |
| **Independently verify** | a fresh checker that is not the doer (Sonnet checker per PR), or Codex as reviewer | [#1 6190309680](https://github.com/reallakshman19/CoordinatorLandingpage/issues/1#issuecomment-6190309680) (fresh checker) | — | a verdict comment at the exact head; CI at that head |
| **Merge** | OwnerTeammember, after an independent PASS at the exact head | [#1 6193950778](https://github.com/reallakshman19/CoordinatorLandingpage/issues/1#issuecomment-6193950778) ("merge approved further", landing-only, revocable) | HOLD on merges, revocation, a failed check | the merge SHA on main |
| **Accept** (product, academic, release, rights) | **Owner only**, or a delegate the Owner names for an exact scope | an explicit acceptance record (e.g. [#21 6208531667](https://github.com/reallakshman19/CoordinatorLandingpage/issues/21#issuecomment-6208531667), WP0–WP9 only) | — | the acceptance record and its scope. Later work does not inherit it |

**Done ≠ verified ≠ accepted.** An action that happened but whose check failed is **"done, not verified"**, not "didn't happen". Example: deploy run 39000177607 deployed successfully, then its readback check failed. The served state for that run is UNKNOWN; later runs succeeded. Report the effect and the failed verification separately.

## 2. History index — preserve causality, not just PR totals

### 2.1 Owner amendments and decisions

| Date/time in attributed record (Dubai) | Owner input / material decision | Why it matters / disposition / source |
|---|---|---|
| 15 Oct, #21 intake | Existing page, live two-way, multiple repos, high-value changes, no revamp/core-protocol change | Governing product outcome; rejects Dash V2/new backend. [#21](https://github.com/reallakshman19/CoordinatorLandingpage/issues/21) is the canonical navigation root, with older brief [#15](https://github.com/reallakshman19/CoordinatorLandingpage/issues/15) retained, not deleted. |
| 15 Oct 14:42 | Claude dual-role TC/OTM; launch L1 narrowly; WP0 then small WP1a | Epoch 1 and narrow initial grant, not unrestricted implementation. [control](https://github.com/reallakshman19/CoordinatorLandingpage/issues/1#issuecomment-6190161629), [plan amendment](https://github.com/reallakshman19/CoordinatorLandingpage/issues/21#issuecomment-6190162030), [L1 issue body](https://github.com/reallakshman19/CoordinatorLandingpage/issues/22). |
| 15 Oct 14:50 | “yes” to fresh Sonnet checker; “optimise use of token” | Checker distinct from implementer; cost discipline is part of delivery, not a reason to omit proof. [record](https://github.com/reallakshman19/CoordinatorLandingpage/issues/1#issuecomment-6190309680). |
| 15 Oct 18:02 | “go ahead. merge approved further.” | Revocable landing-only merge authority after independent exact-head PASS or verified FIX. [standing source](https://github.com/reallakshman19/CoordinatorLandingpage/issues/1#issuecomment-6193950778). Not acceptance or activation. |
| 15 Oct 19:42 | Integrated C15 NOT-READY; current site behind, no full loop | Earlier green slices did not establish integrated acceptance. [findings](https://github.com/reallakshman19/CoordinatorLandingpage/issues/22#issuecomment-6196079899). |
| 15 Oct 20:06 → 20:11 | Google Form idea, then “ignore, we will use json<->webpage” / “implement” | Google Form/CSV REJECTED in favour of existing page → GitHub new-file JSON → committed receipts. Preserve both hops and reason. [earlier](https://github.com/reallakshman19/CoordinatorLandingpage/issues/1#issuecomment-6196562764), [superseding decision](https://github.com/reallakshman19/CoordinatorLandingpage/issues/1#issuecomment-6196668704), [WP7 directive](https://github.com/reallakshman19/CoordinatorLandingpage/issues/22#issuecomment-6196643525). |
| 15 Oct 22:36 | Automatic approval for these two projects | Scoped routing/fixes, independent-pass runs/merges and reasoned expected-answer versioning; protected exclusions retained. [record](https://github.com/reallakshman19/CoordinatorLandingpage/issues/1#issuecomment-6199498426). Never project-global authority. |
| 15 Oct 22:36–22:39 | Page must perform the steps; JSON-only answers from decision cards | Owner's usability correction, not cosmetic preference. [directive](https://github.com/reallakshman19/CoordinatorLandingpage/issues/22#issuecomment-6199498887), [card correction](https://github.com/reallakshman19/CoordinatorLandingpage/issues/22#issuecomment-6199561365). |
| 16 Oct 07:55 | “you are authorized to answer this tab/task” | g1 failed to load; g2 starts with same scope and continued evidence numbering. [changeover](https://github.com/reallakshman19/CoordinatorLandingpage/issues/1#issuecomment-6207717760), [handover](https://github.com/reallakshman19/CoordinatorLandingpage/issues/22#issuecomment-6207718018). |
| 16 Oct 09:07 → 09:24 | Attributed delegated acceptance of earlier scope, then genuine F7c click test | Acceptance is a scoped record, not erased by later work; earlier API commit limitation later supplemented by a signed-in click result. [acceptance](https://github.com/reallakshman19/CoordinatorLandingpage/issues/21#issuecomment-6208531667), [later live test](https://github.com/reallakshman19/CoordinatorLandingpage/issues/22#issuecomment-6208734742). |
| 16 Oct 18:17–19:53 | Continue L1 only; WP11 real two-repo proof; WP12/12b; Next Move adopted | C10 formerly deferred, later real read-only external-repo proof added; no external work activation. [WP11 verdict](https://github.com/reallakshman19/CoordinatorLandingpage/issues/22#issuecomment-6218166799), [WP12](https://github.com/reallakshman19/CoordinatorLandingpage/issues/22#issuecomment-6218814541), [NM0](https://github.com/reallakshman19/CoordinatorLandingpage/issues/22#issuecomment-6218917601), [normal criticality and WP13 GO](https://github.com/reallakshman19/CoordinatorLandingpage/issues/22#issuecomment-6219299960). |
| 16 Oct ~19:3x | “review cycle is over … start planning and implement” | Next Move dispatch/notice approval model adopted only for registry opt-in pilot. Exact specification controls over general prose. [§20](https://github.com/reallakshman19/CoordinatorLandingpage/blob/23843c96ee142ea21577312b504d4ba6cb3f8fc8/protocol/TEAM_PROTOCOL.md), [NM spec](https://github.com/reallakshman19/CoordinatorLandingpage/blob/23843c96ee142ea21577312b504d4ba6cb3f8fc8/protocol/NEXT_MOVE_v1.md). |
| 16 Oct 22:42 | “ok implement your reconciled plan” | WP16 status bar → WP17 UEM guards → WP18 preparation, independent check/delegated merge per WP. Does **not** authorize live UEM, timers or GitHub-pull delivery. [GO](https://github.com/reallakshman19/CoordinatorLandingpage/issues/22#issuecomment-6222337902). |
| 17 Oct 03:39 → 03:57 | g2 chat ended; 1a prepared; #50 later merged | Preserve 1a provenance, correct its stale pending merge question. [1a](https://github.com/reallakshman19/CoordinatorLandingpage/issues/22#issuecomment-6226735852), [final check](https://github.com/reallakshman19/CoordinatorLandingpage/pull/50#issuecomment-6226955608). No inferred g3 adoption. |
| 17 Oct 04:03 | Split: Codex long reading/thinking; Claude fast repeated delivery | Queue/review outputs, no Codex chat sends/browser. [queue](https://github.com/reallakshman19/CoordinatorLandingpage/issues/1#issuecomment-6227041754). |
| 17 Oct 05:1x, record 05:23 | “Lets reset (consider superseded) all project expect LandingPage” | grade9-pilot, imo-ab-test, cii-method-c, xml229-output histories kept; Q1–Q3 withdrawn. Time was explicitly corrected from an estimate; `05:1x` is **not an exact minute**. [record](https://github.com/reallakshman19/CoordinatorLandingpage/issues/1#issuecomment-6227912673), commits `badf51d8be9389ec89471ffa3fe7563d065afc50` → `23843c96ee142ea21577312b504d4ba6cb3f8fc8`. |
| 17 Oct 05:32 | “lets start” S1; read-only/local output | Landing-only coherence brief and private S2 questions. [Q5](https://github.com/reallakshman19/CoordinatorLandingpage/issues/1#issuecomment-6227989942). No protocol rollout. |
| 17 Oct 05:58 | New P1/P2/P3, after protocol ready; review/comment #408/#409 now | OTM's authorisation interpretation is labelled interpretation, not additional Owner words. Operational HOLD remains; no inference that old four projects reopened. [record](https://github.com/reallakshman19/CoordinatorLandingpage/issues/1#issuecomment-6228221349). |
| 17 Oct 05:32–06:3x | "lets start" (S1), then "fixes: go" | S1 brief (Codex Q5). S2 cold-reader test from #21 only, judged **PARTIAL** ([#21 6229244105](https://github.com/reallakshman19/CoordinatorLandingpage/issues/21#issuecomment-6229244105)). This page, the route map and the record corrections are its fixes. |

### 2.2 Implementation crux — actual source-to-output path

This is a source-navigation map, not an independently executed behavioural proof.

1. **Read boundary:** current `logs/<project>/registry.json` selects repositories, agents, issue/comment sources and authority anchors. `scripts/fetch_live_data.py` discovers sources/project refs, fetches issue/evidence/inbox and bounded extras into `_live_cache`; it does not authorize work.
2. **Meaning boundary:** `scripts/build_data.py` parses native TASK EVIDENCE/STATUS/verdicts, fences generations/repositories, derives freshness, reads committed Owner input JSON and receipts, and builds project/evidence/timeline projections. `owner_json.py` handles validated committed inputs. A shared GitHub account does not prove human intent.
3. **Next-action boundary:** `next_move.py` validates source/transition/approver/claim states. The evaluator produces a proposal; an uncommitted EVALUATED suggestion is not a heartbeat. The opt-in claim helper is a separate explicit Contents create/CAS operation, not a scheduler or proven exactly-once chat transport.
4. **Economy/status boundary:** `status_bar.py` projects roster coverage, work, monitoring and execution authority separately. `ultra_economy.py` is default-off. A START is a claim, never approval; a delivery-state row is not an execution grant. Silent foreign-source suppression remains an open observability note.
5. **Publication boundary:** `.github/workflows/deploy.yml` is the single Pages writer. Exact-main checkout → read-only fetch → fail-closed capture check → build live JSON separately from frozen benchmark paths → stamp build-info → checks → artifact → Pages deploy → readback. Existing issue/comment/push/schedule triggers build projections, not agent wakes.
6. **Consumer/return path:** `site/app.js` reads `build-info.json` and `data/*.json`, renders existing routes plus additive Next Move/status views, and offers GitHub-authenticated new-file request prefills. Requests still need actual handler/approval/delivery/evidence/reviewer/RESULT records. The browser does not become the coordinator.

### 2.3 Agent contribution chain and succession

- **Original builder/#15:** established the static page and eight-view/frozen-benchmark baseline; predecessor source is retained. Exact original builder chat/generation provenance was not reconstructed here.
- **L1 g1 `6ad0adca`:** #22 blocks #1–#17; WP0, WP1a/1b, WP2/4/3, WP5a/b, WP6, WP7, WP8a/b, WP9. Added truthful source boundaries and JSON feedback; underwent HOLD→FIX→PASS loops. Retired when chat failed to load; do not skip its negative findings.
- **L1 g2 `6ad1a045`:** #22 blocks #18–#29, continuing the same evidence chain; WP8c, WP10, WP11, WP12/12b, WP13–WP18. Took over the pre-existing UEM branch within its scoped GO; feature merges are distinct from integration into main.
- **OTM/TC Claude:** Owner-attributed decisions, one writer grants, evidence checks, independent-check reports, delegated merges, NM0 specification, g1→g2 handover and reconstructed outgoing g2 1a.
- **Checker C1/C15:** fresh Sonnet reviews attributed in public records. These are substantive review sources, but shared-account GitHub identity does not independently authenticate the checker runtime.
- **Codex:** #21 source/planning reconciliation; initial UEM draft contribution; current Q4 source applicability audit and local S1/S2. No claim that Codex authored L1's later implementation.
- **Proposed g3:** NOT_SELECTED / NOT_QUALIFIED from inspected sources. The 1a has no successor id, qualified 1b or final phase 2. No new agent was launched for Q5.

### 2.4 WP1–WP18 and NM0 — exact history table

WP numbering is **not merge order**: WP4 preceded WP3; WP8c followed WP9; WP1/5/8/12 have subdivisions. WP0 is read-only [traceability](https://github.com/reallakshman19/CoordinatorLandingpage/issues/21#issuecomment-6190276704), [evidence](https://github.com/reallakshman19/CoordinatorLandingpage/issues/22#issuecomment-6190301045), no PR/merge. WP5 is an integrated qualification workpack: 5a/5b are not substitutes for its later F7/acceptance records.

| Workpack / contributor | PR / actual target | Frozen PR head | Full merge SHA | Evidence / disposition |
|---|---|---|---|---|
| WP1a — truthful inbox/liveness/generation/provenance · g1 | [#24](https://github.com/reallakshman19/CoordinatorLandingpage/pull/24) → `main` | `24f06dd716dda10ff461b941f4a0eceed43660f5` | `59f821ff2b729ddbda00204dda629df4eaef8252` | [evidence](https://github.com/reallakshman19/CoordinatorLandingpage/issues/22#issuecomment-6191049265) · [verdict/GO](https://github.com/reallakshman19/CoordinatorLandingpage/issues/22#issuecomment-6191081581) |
| WP1b — Owner-input receipt and authority fences · g1 | [#25](https://github.com/reallakshman19/CoordinatorLandingpage/pull/25) → `main` | `88a7ae52c24291458b2d27ade844f7789b6cdaaf` | `9909cc2b05a6e1d9f67406308770b8d266c9d70a` | [evidence](https://github.com/reallakshman19/CoordinatorLandingpage/issues/22#issuecomment-6191774321) · [verdict/GO](https://github.com/reallakshman19/CoordinatorLandingpage/issues/22#issuecomment-6191796897) |
| WP2 — visible receipt/freshness UI · g1 | [#26](https://github.com/reallakshman19/CoordinatorLandingpage/pull/26) → `main` | `6ceede14132886052bac3eb854741b3c0fc19139` | `5d8a586c18a3907edd3b9779b2af4a1e4a0c4ef0` | [evidence](https://github.com/reallakshman19/CoordinatorLandingpage/issues/22#issuecomment-6193317183) · [verdict/GO](https://github.com/reallakshman19/CoordinatorLandingpage/issues/22#issuecomment-6193352265) |
| WP4 — one fail-closed Pages publisher (before WP3) · g1 | [#27](https://github.com/reallakshman19/CoordinatorLandingpage/pull/27) → `main` | `cdd9705831d03ae2351358f48e3b3e772c5a1586` | `b4c005ebb0037767ae53ce4a121b124f7b7c03cf` | [evidence](https://github.com/reallakshman19/CoordinatorLandingpage/issues/22#issuecomment-6193882794) · [verdict/GO](https://github.com/reallakshman19/CoordinatorLandingpage/issues/22#issuecomment-6193900175) |
| WP3 — real receipts, build polling, F4 isolation · g1 | [#28](https://github.com/reallakshman19/CoordinatorLandingpage/pull/28) → `main` | `dc2fbfcf6952d639a5f20aefa297eb36ceb1120b` | `0b56c75153c546771ef9c334a228d88c4c73f58f` | [evidence](https://github.com/reallakshman19/CoordinatorLandingpage/issues/22#issuecomment-6194782458) · [verdict/GO](https://github.com/reallakshman19/CoordinatorLandingpage/issues/22#issuecomment-6194799836) |
| WP5a — genuine F7 input/form/registry repairs · g1 | [#32](https://github.com/reallakshman19/CoordinatorLandingpage/pull/32) → `main` | `7f2d2eb42dd2333076bd30b0fe8704e7834b4c27` | `30496eb1a734048aa4028af77f79a3272f5b0ed9` | [evidence](https://github.com/reallakshman19/CoordinatorLandingpage/issues/22#issuecomment-6195674725) · [verdict/GO](https://github.com/reallakshman19/CoordinatorLandingpage/issues/22#issuecomment-6195721260) |
| WP5b — outsider segregation and bounded pagination · g1 | [#33](https://github.com/reallakshman19/CoordinatorLandingpage/pull/33) → `main` | `20d274a317a04fc4522fccc5dfd3f81fc7433773` | `960c8ca2e39385f642f100842688156e30c94a1a` | [evidence](https://github.com/reallakshman19/CoordinatorLandingpage/issues/22#issuecomment-6196019871) · [verdict/GO](https://github.com/reallakshman19/CoordinatorLandingpage/issues/22#issuecomment-6196048532) |
| WP6 — request trace and understandable next action · g1 | [#34](https://github.com/reallakshman19/CoordinatorLandingpage/pull/34) → `main` | `ae8a420a325382b2486d8916c36bcb7f97d668af` | `4f5abb0863ac7b7a78214f8b5ef19c2d35cc9df3` | [evidence](https://github.com/reallakshman19/CoordinatorLandingpage/issues/22#issuecomment-6196743440) · [verdict/GO](https://github.com/reallakshman19/CoordinatorLandingpage/issues/22#issuecomment-6196795386) |
| WP7 — page ⇄ GitHub JSON and receipts · g1 | [#35](https://github.com/reallakshman19/CoordinatorLandingpage/pull/35) → `main` | `f988c92538e266966261128e26129bf8a042785b` | `15caea96faa6c7138d624bb4eebac9ddb489ecf2` | [evidence](https://github.com/reallakshman19/CoordinatorLandingpage/issues/22#issuecomment-6197285349) · [verdict/GO](https://github.com/reallakshman19/CoordinatorLandingpage/issues/22#issuecomment-6197370254) |
| WP8a — stale asset/cache correction · g1 | [#36](https://github.com/reallakshman19/CoordinatorLandingpage/pull/36) → `main` | `03311e54c2ba51cc83baebd22830f0f5e189e4b1` | `8d6b254d7fa180dfdf815e6ac16b02e1a04524ca` | [evidence](https://github.com/reallakshman19/CoordinatorLandingpage/issues/22#issuecomment-6198198687) · [verdict/GO](https://github.com/reallakshman19/CoordinatorLandingpage/issues/22#issuecomment-6198212753) |
| WP8b — timestamps, protocol and input shortcut · g1 | [#37](https://github.com/reallakshman19/CoordinatorLandingpage/pull/37) → `main` | `425416930966b032cde092afc7d7a0d244214f2a` | `83c9ccb82fdef36fd105af23669dfadeeac43cdf` | [evidence](https://github.com/reallakshman19/CoordinatorLandingpage/issues/22#issuecomment-6198500207) · [verdict/GO](https://github.com/reallakshman19/CoordinatorLandingpage/issues/22#issuecomment-6198567231) |
| WP9 — decision answers using JSON, not issue form · g1 | [#40](https://github.com/reallakshman19/CoordinatorLandingpage/pull/40) → `main` | `52b488833809d514a9463b6795fae7b778d90b33` | `501b4c1b46e63a9cd23fb5617ba115ee1b883b50` | [evidence](https://github.com/reallakshman19/CoordinatorLandingpage/issues/22#issuecomment-6199795845) · [verdict/GO](https://github.com/reallakshman19/CoordinatorLandingpage/issues/22#issuecomment-6199826468) |
| WP8c — security/schema/foreign-author hardening · g2 | [#41](https://github.com/reallakshman19/CoordinatorLandingpage/pull/41) → `main` | `87f8624e0da01415999ae48f4d5d09a50a5c99cf` | `fe673fc380339652c8c8afb642639a4962602c2b` | [evidence](https://github.com/reallakshman19/CoordinatorLandingpage/issues/22#issuecomment-6207914576) · [verdict/GO](https://github.com/reallakshman19/CoordinatorLandingpage/issues/22#issuecomment-6208379335) |
| WP10 — auto-response, lifecycle and provenance · g2 | [#42](https://github.com/reallakshman19/CoordinatorLandingpage/pull/42) → `main` | `0cd8e2e73bce28eb10cccfbc583b4afb4e415527` | `bcf4eeb9d6186a70e95e247a148bd1bb2939a319` | [evidence](https://github.com/reallakshman19/CoordinatorLandingpage/issues/22#issuecomment-6213880218) · [verdict/GO](https://github.com/reallakshman19/CoordinatorLandingpage/issues/22#issuecomment-6214059487) |
| WP11 — real distinct-product-repo read-only isolation · g2 | [#43](https://github.com/reallakshman19/CoordinatorLandingpage/pull/43) → `main` | `442c903c633fa6ff66b9ac005a2252d27923fb4d` | `667bee780b70f4c896a8d670ca92f886a947e8a4` | [evidence](https://github.com/reallakshman19/CoordinatorLandingpage/issues/22#issuecomment-6218042239) · [verdict/GO](https://github.com/reallakshman19/CoordinatorLandingpage/issues/22#issuecomment-6218166799) |
| WP12 — HOLD/reporting tree/child evidence · g2 | [#44](https://github.com/reallakshman19/CoordinatorLandingpage/pull/44) → `main` | `88c54d69f7be88012f39c3f7f7cf3cfab1f6ec84` | `27df6c347fb995a3956552af75da6e82a372c945` | [evidence](https://github.com/reallakshman19/CoordinatorLandingpage/issues/22#issuecomment-6218453041) · [verdict/GO](https://github.com/reallakshman19/CoordinatorLandingpage/issues/22#issuecomment-6218814541) |
| NM0 — adopted Next Move specification · OTM/TC | [#45](https://github.com/reallakshman19/CoordinatorLandingpage/pull/45) → `main` | `d452f7b763f5b7753f2d16550a3dd54302369b43` | `fb464f8edc31a623509cb43ff9d669845d55d70d` | [verdict/GO](https://github.com/reallakshman19/CoordinatorLandingpage/issues/22#issuecomment-6218917601) |
| WP12b — exact evidence contract and negative controls · g2 | [#46](https://github.com/reallakshman19/CoordinatorLandingpage/pull/46) → `main` | `c1c8154624be2c623c38ef6490957f1a9db4e761` | `df0ba0cb205d853bbe67eece1c851e6ba88f948b` | [evidence](https://github.com/reallakshman19/CoordinatorLandingpage/issues/22#issuecomment-6219144889) · [verdict/GO](https://github.com/reallakshman19/CoordinatorLandingpage/issues/22#issuecomment-6219299960) |
| WP13 — Next Move validator/board/task cycles · g2 | [#47](https://github.com/reallakshman19/CoordinatorLandingpage/pull/47) → `main` | `af0e49b35eaff64d1aedeb30181e063dd57639d7` | `836c383c10c9de5cc59c29635bdec0af73290289` | [evidence](https://github.com/reallakshman19/CoordinatorLandingpage/issues/22#issuecomment-6219791107) · [verdict/GO](https://github.com/reallakshman19/CoordinatorLandingpage/pull/47#issuecomment-6220165048) |
| WP14 — request composer and opt-in claim CAS · g2 | [#48](https://github.com/reallakshman19/CoordinatorLandingpage/pull/48) → `main` | `304e4cde1398870099909de32ac797ae0af6b58b` | `f22b170f23765810a880419271d0cf9a06d9c6d1` | [evidence](https://github.com/reallakshman19/CoordinatorLandingpage/issues/22#issuecomment-6220584374) · [verdict/GO](https://github.com/reallakshman19/CoordinatorLandingpage/pull/48#issuecomment-6220688201) |
| WP15 — read-only evaluator and heartbeat proposal · g2 | [#49](https://github.com/reallakshman19/CoordinatorLandingpage/pull/49) → `main` | `1b5b2ff6980cae2da860115b907161a0917c865d` | `2b304dfe9d0219d801f1bb5a4edc46077fa3578b` | [evidence](https://github.com/reallakshman19/CoordinatorLandingpage/issues/22#issuecomment-6220992841) · [verdict/GO](https://github.com/reallakshman19/CoordinatorLandingpage/pull/49#issuecomment-6221197068) |
| WP16 — roster/status bar and three dimensions · g2 | [#51](https://github.com/reallakshman19/CoordinatorLandingpage/pull/51) → `feat/ultra-economy-mode-v1` | `a7c7e3ce747894f4a8285f1373ecbd15481cc17b` | `aac682e129cb042b8e6fae4e06bb905cd7257aa1` | [evidence](https://github.com/reallakshman19/CoordinatorLandingpage/issues/22#issuecomment-6222610295) · [verdict/GO](https://github.com/reallakshman19/CoordinatorLandingpage/pull/51#issuecomment-6222780724) |
| WP17 — UEM source/grant/cycle/timer guards · g2 | [#52](https://github.com/reallakshman19/CoordinatorLandingpage/pull/52) → `feat/ultra-economy-mode-v1` | `178634dea27252f3515c8cf96e32df80189ece7d` | `09b5e7a89d5e0eef0e58cc674fcf050a9e24f1fd` | [evidence](https://github.com/reallakshman19/CoordinatorLandingpage/issues/22#issuecomment-6223105248) · [verdict/GO](https://github.com/reallakshman19/CoordinatorLandingpage/pull/52#issuecomment-6223256152) |
| WP18 — unapplied one-cycle pilot preparation · g2 | [#53](https://github.com/reallakshman19/CoordinatorLandingpage/pull/53) → `feat/ultra-economy-mode-v1` | `176da586f2c986f0ec6913221343031a289a622e` | `af4ecb205d1a51f49de2574c6f69a7413f95b45a` | [evidence](https://github.com/reallakshman19/CoordinatorLandingpage/issues/22#issuecomment-6223561628) · [verdict/GO](https://github.com/reallakshman19/CoordinatorLandingpage/pull/53#issuecomment-6223804279) |
| UEM integration — WP16–18 feature → main · initial Codex + g2 takeover | [#50](https://github.com/reallakshman19/CoordinatorLandingpage/pull/50) → `main` | `af4ecb205d1a51f49de2574c6f69a7413f95b45a` | `885d95b4c115b2eb5f0b47bdd80f8ae5d70bda12` | [verdict/GO](https://github.com/reallakshman19/CoordinatorLandingpage/pull/50#issuecomment-6226955608) |

The #47 merged tree differs from its reviewed tree **only** in inherited `logs/grade9-pilot/registry.json` by direct complete blob-map comparison; landing implementation blobs match. Recorded review qualification is not proof of every integration/production behaviour. Full merge SHAs above are history, not today's source pins.

### 2.5 Known failures, limits and pending actions

| Finding / source | What actually happened | Disposition / next owner |
|---|---|---|
| WP1a placeholder CI; proposed tests NOT_RUN; C1 HOLD | An echo-green job and missing-API errors were insufficient. Later real behavioural red controls and exact-head CI were required. [partial](https://github.com/reallakshman19/CoordinatorLandingpage/issues/22#issuecomment-6190705619), [HOLD](https://github.com/reallakshman19/CoordinatorLandingpage/issues/22#issuecomment-6190865625), [fix](https://github.com/reallakshman19/CoordinatorLandingpage/issues/22#issuecomment-6191049265) | Preserve as anti-false-green history; don't retest old candidates. |
| WP4 permissions and WP3 coordinator spoofing HOLDs | Source authority/permissions corrected before qualification. [WP4 HOLD](https://github.com/reallakshman19/CoordinatorLandingpage/issues/22#issuecomment-6193799979), [WP3 HOLD](https://github.com/reallakshman19/CoordinatorLandingpage/issues/22#issuecomment-6194464257) | Never assume receipt text authenticates its role. |
| F7 #31 project mismatch, stale UI, incomplete round trip | Integrated C15 NOT-READY; fail-closed mismatch was not “fixed” by editing Owner intent. [C15](https://github.com/reallakshman19/CoordinatorLandingpage/issues/22#issuecomment-6196079899) | Later new F7b/c inputs/receipts supplement it; preserve old failure. |
| Old deployed JS/CSS | Owner saw old UI despite merges. [report](https://github.com/reallakshman19/CoordinatorLandingpage/issues/22#issuecomment-6197975466) | WP8a/b cache and timestamp fixes; fresh HTTP today still not a full browser qualification. |
| g1 disappeared; g2 later full | Recovery needed evidence-based handover and source custody, not assuming “active.” [g1 changeover](https://github.com/reallakshman19/CoordinatorLandingpage/issues/1#issuecomment-6207717760), [g2 1a](https://github.com/reallakshman19/CoordinatorLandingpage/issues/22#issuecomment-6226735852) | OTM reconciles current registry/handover before future work. |
| WP16 broad regression | Feature-only check attributed identical WP3 allowlist failure at pinned #50 base; WP17 repaired it. [#51 verdict](https://github.com/reallakshman19/CoordinatorLandingpage/pull/51#issuecomment-6222780724), [#52](https://github.com/reallakshman19/CoordinatorLandingpage/pull/52#issuecomment-6223256152) | Do not report old red as current or old green as current proof. |
| Foreign-source omission | Rejected sources fail closed but lack visible reason. [#53](https://github.com/reallakshman19/CoordinatorLandingpage/pull/53#issuecomment-6223804279), [#50](https://github.com/reallakshman19/CoordinatorLandingpage/pull/50#issuecomment-6226955608) | OPEN; propose visible rejection reason, retain denial. |
| Abbreviated END / unavailable-timer control | #53 notes not explicitly closed in #50. | OTM disposes of both; native full evidence remains required. |
| Timer prose conflict — **RESOLVED 17 Oct, see 3a** | Agent skill/runbook say NOT_ARMED, explicit one-shot exception only; ULTRA_ECONOMY_MODE.md still retains an older hourly instruction/terminal cancellation paragraph. | Document drift, not live timer permission. Correct in a separately scoped documentation change; don't arm anything. |
| Counter terminology drift | NEXT_MOVE spec describes delegation allowance converted to clock time; latest direct Owner requires no Codex counters and registry authority. | Preserve source distinction; don't calculate/reset/transfer allowances privately. |
| Missing real NM/evaluator ledger | Tree has no landing `moves.jsonl` or move directory; deployed evaluator missing, task-cycle no GO. | UNKNOWN/NOT_RECORDED, not zero completed work or permission to seed records. |
| Status authority stale — **registry part RESOLVED 17 Oct, see 3a** | Live source fresh while last TC cycle 16 Oct19:53:37+04 and registry g2 “active” are old; lease holder projects UNVERIFIED_HOLDER. | Data freshness ≠ work freshness. OTM owns authorized source repair; Codex does not fabricate it. |

### 2.6 Improvement/decision register

| Rank / disposition | Item / author or source | Reason | Revisit trigger |
|---|---|---|---|
| Mandatory KEEP | Existing page, unchanged core authority, native evidence, F1/F2 original fixtures — Owner #21 | Preserves product baseline and causal proof | Material new Owner outcome, not a failed tile/status alone |
| High ROI ADOPTED | Truthful receipt trace, stale/unknown boundary, generation attribution, one publisher — g1 | Prevents false live/false handled and wrong-agent conclusions | Regression/source/head change |
| High ROI ADOPTED | JSON page feedback replaces Google Form/issue-first flow — Owner WP7/WP9 | Fewer relays; real committed source and receipts | Genuine failure of chosen route, not aesthetic redesign |
| High ROI ADOPTED (pilot scope) | Next Move approval/delivery states and evaluator — OTM/TC plus reviews | Auditable who/why/authority; no automatic send | Actual first authorized round trip |
| High ROI ADOPTED (code only) | Status bar/three dimensions and UEM guard code — Owner WP16–18 GO, g2 | Coverage/work/monitoring/authority kept separate | Source-backed active instance and reviewed grants |
| High ROI PROPOSED | Current registry/handover/history index coherence — Q4/Q5 | Prevents successor reconstructing stale state | OTM/Owner authorizes source publication/update |
| High ROI PROPOSED | Visible foreign-source rejection note — final independent review | Explain fail-closed missing agents rather than silently omit | Next specifically authorized maintenance unit |
| Medium ROI PROPOSED | Explicit disposition of abbreviated END/unavailable-timer note; retire contradictory hourly prose | Avoid wrong guide interpretation | Documentation scope approved |
| PARKED | Live UEM one-cycle pilot — WP18 runbook/Q5 | Code/test success never opts in a project | New explicit Owner registry words, exact unit/agent/grants, source pins, independent check |
| PARKED | GitHub-pull task delivery | Owner reserved decision until after pilot | Actual pilot evidence and Owner decision |
| PARKED | Agent timer | One watcher selected; no native agent task proof | Exact Owner exception + creation, one fire and cancellation proof |
| PARKED | Protocol freeze/v3+rollout and broad future P1–P3 implementation | Current TEAM_PROTOCOL remains v2.3 final candidate; latest programme starts after protocol ready | Owner's readiness/activation words |
| REJECTED | Dash V2/new backend/database/replacement UI — Owner #21 | Duplicates architecture and changes the requested product | Only explicit material Owner reversal |
| REJECTED | Google Form/CSV first idea — superseded Owner WP7 | Chosen json⇄webpage route instead | Only new evidence/Owner reversal |

“Proposed” is not ADOPTED or work authority. No private project-wide score is introduced.

## 3. Authority map

| Fact type | Authoritative record / resolution order | Responsible owner | Scope / lifetime / crucial limit |
|---|---|---|---|
| Original intent and amendments | #21 + source-linked later Owner words in #1/#22; exact attributable quote, not role prefix | Owner; OTM records exact-word relay | Latest scoped words supersede earlier conflicting instructions; source history retained |
| Current control / actor | Registry control epoch + #1 control record + later direct role change | Owner; active Claude TC/OTM | One deliverer. Codex current planner/reviewer only, no chats/browser |
| Delegated merges | Registry MERGE-STANDING + #1 6193950778 / 6199498426; exact reviewed head | Owner grants; OTM applies within scope | Landing-only, independent PASS/verified FIX, revocable; not acceptance/release/activation |
| Criticality | Registry `criticality` + `criticality_owner_words` | Owner only | Normal is not auto-response; unset treated critical |
| Task evidence and checker verdict | Native #22 append-only block, exact candidate/source and role-tagged proof; independently attributed checker receipt | Implementer authors; checker/OTM reviews | Claim ≠ proof ≠ acceptance; correction appends, does not erase old failure |
| Code truth | Actual repository main/PR full SHA and changed files | Authorized exclusive writer; GitHub provides observed commit facts | Old accepted or tested SHA cannot qualify a changed current candidate |
| Deploy truth | Hosted root build-info + payload source hashes/run + actual HTTP source observation; workflow deploy/readback | Authorized existing publisher | Repo merge ≠ observed deployment; today's HTTP != live browser interaction/acceptance |
| Next Move state | Actual move/claim/transition records, source-bound approvals, current basis and delivery proof | Proper approver; Claude sole deliverer; non-doer verifies | Page/evaluator proposals execute nothing; publication≠chat delivery; expiry doesn't clear uncertain sends |
| Writer lease / succession | Registry exact holder/branch/path + actual stop/no pending send/qualified 1b/phase2 as applicable | Owner/scoped authorized OTM; TC remaps valid grants | g2 lease not silently inherited by hypothetical g3; scope expansion needs authority |
| HOLD / supersession | Latest Owner words + scoped registry/control; #1 reset and withdrawal | Owner; OTM records/delivers within its role | Historical project records survive; no revival from old queue or empty control.hold |
| Acceptance | Explicit source decision and exact accepted scope, e.g. #21 6208531667 | Owner or exact scoped delegate | Prior accepted WP0–9 scope != acceptance of later WP10–18/current UEM |
| Monitoring / work permission | Distinct current registry grants and actual watcher/host evidence | Owner grants; named watcher acts | Watch permission is not work permission; no agent timers by default |
| Future programme P1–P3 | #1 6228221349 attributed Owner quote; later OTM reading separately labelled | Owner; OTM named for three projects | Reviews of #408/#409 now; implementation after protocol ready; no general self-granted scope |

## 3a. Dispositions made with this page (17 Oct 2026, OwnerTeammember)

| Finding | Disposition |
|---|---|
| Registry said L1 g2 "active" | Corrected: g2 `retired` with the reason; lease marked `released`; workflow `current` updated, with the old text kept as `previous` |
| 1a still asked for the #50 merge | Corrected in a new #22 comment that replies to 1a (1a itself is unchanged, kept as history) |
| UEM hourly prose vs NOT_ARMED; a timer read as an activation prerequisite | ULTRA_ECONOMY_MODE.md: hourly text struck through but kept; "activation vs monitoring" note added. The runbook says a timer is optional |
| Abbreviated END / unavailable-timer notes | Dispositioned in ULTRA_ECONOMY_MODE.md "Review-note dispositions" |
| Foreign-source rejection not visible | OPEN; scheduled into the P1 landing-page revision (owner: OwnerTeammember) |

## 4. Source identities and explicit gaps (4.1, the snapshot read log, is omitted here)

### 4.2 File source identities

All links below pin the same current main. Full text was read for operating docs; code modules were used only for the stated source-map scope.

| File | Git blob SHA | Read scope |
|---|---|---|
| [`protocol/TEAM_PROTOCOL.md`](https://github.com/reallakshman19/CoordinatorLandingpage/blob/23843c96ee142ea21577312b504d4ba6cb3f8fc8/protocol/TEAM_PROTOCOL.md) | `61329d2e780b0af4df9e83a17c5c6ddefb946a29` | text/manifest read |
| [`protocol/NEXT_MOVE_v1.md`](https://github.com/reallakshman19/CoordinatorLandingpage/blob/23843c96ee142ea21577312b504d4ba6cb3f8fc8/protocol/NEXT_MOVE_v1.md) | `93dbe569fb9cdb0fee0fbc00da84ceb946a3fb30` | text/manifest read |
| [`ULTRA_ECONOMY_MODE.md`](https://github.com/reallakshman19/CoordinatorLandingpage/blob/23843c96ee142ea21577312b504d4ba6cb3f8fc8/ULTRA_ECONOMY_MODE.md) | `4c28cbb85efb69f0cf904c407d705a1ced335ffc` | text/manifest read |
| [`protocol/LANDING_PAGE_BRIEF.md`](https://github.com/reallakshman19/CoordinatorLandingpage/blob/23843c96ee142ea21577312b504d4ba6cb3f8fc8/protocol/LANDING_PAGE_BRIEF.md) | `fe1fa755f203b79336737d7be70db9271a4d8c6b` | text/manifest read |
| [`pilot/WP18_LANDING_LIVE_RUNBOOK.md`](https://github.com/reallakshman19/CoordinatorLandingpage/blob/23843c96ee142ea21577312b504d4ba6cb3f8fc8/pilot/WP18_LANDING_LIVE_RUNBOOK.md) | `b7c26d58ba239da99681b134ca9366e3d828f6d2` | text/manifest read |
| [`skills/ultra-economy-mode/SKILL.md`](https://github.com/reallakshman19/CoordinatorLandingpage/blob/23843c96ee142ea21577312b504d4ba6cb3f8fc8/skills/ultra-economy-mode/SKILL.md) | `e173edb5cc98b30b120fc01915ebe22dd9afdd38` | text/manifest read |
| [`scripts/fetch_live_data.py`](https://github.com/reallakshman19/CoordinatorLandingpage/blob/23843c96ee142ea21577312b504d4ba6cb3f8fc8/scripts/fetch_live_data.py) | `2c3be2530e1e146eee311c81e3d685e3594ec572` | function/entrypoint map only, not full correctness review |
| [`scripts/build_data.py`](https://github.com/reallakshman19/CoordinatorLandingpage/blob/23843c96ee142ea21577312b504d4ba6cb3f8fc8/scripts/build_data.py) | `1bb4dd3cb7e10f036d65c633ecc8c567af3b0401` | function/entrypoint map only, not full correctness review |
| [`site/app.js`](https://github.com/reallakshman19/CoordinatorLandingpage/blob/23843c96ee142ea21577312b504d4ba6cb3f8fc8/site/app.js) | `435512f84eeb4ac094ffbee97269a49821137d6f` | function/entrypoint map only, not full correctness review |
| [`.github/workflows/deploy.yml`](https://github.com/reallakshman19/CoordinatorLandingpage/blob/23843c96ee142ea21577312b504d4ba6cb3f8fc8/.github/workflows/deploy.yml) | `1d4f2fa1405308fc228c0dcc3af472d0a2192238` | text/manifest read |
| [`scripts/NEXT_MOVE_EVALUATOR.md`](https://github.com/reallakshman19/CoordinatorLandingpage/blob/23843c96ee142ea21577312b504d4ba6cb3f8fc8/scripts/NEXT_MOVE_EVALUATOR.md) | `fd314112ab0776cd87d0fb38f880d591d95ffaba` | text/manifest read |
| [`logs/landing-live/receipts.jsonl`](https://github.com/reallakshman19/CoordinatorLandingpage/blob/23843c96ee142ea21577312b504d4ba6cb3f8fc8/logs/landing-live/receipts.jsonl) | `d2a7166badda0d43baa770b3a1b6512b6b04cd5b` | text/manifest read |
| [`logs/landing-live/2026-10-15-s1/events.jsonl`](https://github.com/reallakshman19/CoordinatorLandingpage/blob/23843c96ee142ea21577312b504d4ba6cb3f8fc8/logs/landing-live/2026-10-15-s1/events.jsonl) | `978ab14a43d490590570467845bb13d4b5199734` | text/manifest read |
| [`benchmarks/grade9-pilot-2026-10-15/MANIFEST.json`](https://github.com/reallakshman19/CoordinatorLandingpage/blob/23843c96ee142ea21577312b504d4ba6cb3f8fc8/benchmarks/grade9-pilot-2026-10-15/MANIFEST.json) | `06baec0edbc5dafafd8c679b0ca83f427adaa5a0` | text/manifest read |
| [`benchmarks/imo-ab-test-2026-10-15/MANIFEST.json`](https://github.com/reallakshman19/CoordinatorLandingpage/blob/23843c96ee142ea21577312b504d4ba6cb3f8fc8/benchmarks/imo-ab-test-2026-10-15/MANIFEST.json) | `3cff580437e611bfc618b7865ce7a9a53f3dc597` | text/manifest read |

F1/F2 manifests list original frozen source files; their entire referenced payload bytes were **not** refetched/hash-audited or executed in this review. F2 explicitly lacks events.jsonl and needs reconstructed provenance. Both old product projects use Grade9v3.5; **they do not prove two distinct product repositories**. Later WP11's real XML/3D read-only proof is a different source.

### 4.3 Key comment identities

The amendment table and WP table are the linked comment manifest. Additional index anchors:
- #21 WP0 source map6190276704; authority/dependency notice6196679304; scoped acceptance6208531667.
- #22 original evidence #1–#29, including superseded partial/fix heads; primary own-work evidence IDs are listed in §2.4, not flattened into “all passed.”
- #1 Owner/control6190161629, checker6190309680, merge6193950778, JSON supersession6196668704, delegation6199498426, g2changeover6207717760, reset6227912673, Q5request6227989942, futureprogramme6228221349.
- Exact-head pre-merge review comment IDs6220165048/6220688201/6221197068/6222780724/6223256152/6223804279/6226955608. Attribution, time and SHA applicability reviewed; independent runtime authentication NOT_VERIFIED.
- Q4 result on #22:6228255925. Treat as Codex source-applicability audit, not a new checker or acceptance receipt.

### 4.4 Explicit gaps / UNKNOWNs


1. Actual g2 live browser state, exact chat-end observation, full conversation provenance and any selected g3/1b/2 beyond the source record were **NOT_OBSERVED**. No chat sends or browser were used.
2. Fresh distinct checker runtime identities are **not authenticated** by shared GitHub authorship. Test totals remain attributed reported evidence, not reruns by Codex.
3. Complete original fixture payload/golden byte identity, all historical CI logs and current main independent full regression/Owner acceptance are **not established** by this read. Don't turn manifest accounting into proof.
4. Actual Next Move live round trip and committed evaluator EVALUATED heartbeat not found; phase/P4 readiness should not be declared complete from fixture tests.
5. **(Registry part RESOLVED 17 Oct, see 3a.)** Registry workflow, g2 liveness, human lease-holder string and latest handover contain stale/ambiguous fields. Their authorized correction is not performed by this document.
6. Earlier delegated acceptance on #21 is source-backed but limited to its named scope; later added UEM/status/counter features do not inherit it.
7. Current deployed HTTP payload is attributable to main, but full visual, interactive, authentication, redaction and updated foreign-source presentation were not retested.
8. Q5 says UEM PARKED; actual source registry independently establishes disabled. No later Owner activation evidence was found.
9. Original LANDING_PAGE_BRIEF.md still says v2.1 and issue-prefilled input; current protocol/Owner JSON amendments supersede those details. Do not discard its original views/fixtures.
10. Full conversation transcripts are not captured; only 8-character chat ids are public. Provenance beyond that is UNKNOWN.
11. No rendered-browser test of the current deployed page has been run since the F7c click test (16 Oct).
