# Standalone Oracle Engineering Relay Protocol v1.0

**Mode:** `standalone-oracle`, explicitly selected **per project**. **Principle:** **Engineering relay with improvements and a complete audit trail**. This applies to Owner ↔ designated Oracle ↔ engineers ↔ independent reviewers, **without Team Coordinator or OTM**. It does not override `protocol/TEAM_PROTOCOL.md` for other projects, authorize agents, release a HOLD, authenticate a shared GitHub user, or merge/release software.

## Step 0: Mandatory grounding for EVERY agent — before any execution

The first instruction in every new or resumed standalone assignment is: **Open Progress page → assigned project → assigned topic → Grounding fixtures. Read all relevant Project sources and Starting context, including this protocol, the governing issue, current Owner amendments, active candidate HEAD, known safety failures, custody and HOLD constraints.** Do not treat a previously copied packet as fresher than live project sources.

Before starting the task, the **actual agent** posts this concise receipt to the owning GitHub task; Oracle cannot fabricate it:

```text
[STANDALONE_ORACLE_RELAY_ONBOARD/v1]
project/topic and assignment:
actual actor/session role and independence disclosure:
Grounding fixtures read: URL, source commit SHA, UTC time
source contract, Owner amendments, issue and exact candidate HEAD:
input access / benchmark custody and prohibited materials:
authority to read, test, edit or dispatch: grant / gaps / HOLD:
own source and expectation lineage; first surviving-error challenge:
material discrepancies, missing files and limitations:
onboarding status: GROUNDED_READY | HOLD | UNKNOWN
[/STANDALONE_ORACLE_RELAY_ONBOARD]
```

A receipt is self-reported **reading**, not independent comprehension, actual execution, Owner authorization, or verified bench custody. An unguided agent with no actual receipt remains **NOT_STARTED** for the pre-start gate. Re-ground on resumed sessions and significant source/fixture/head amendments. When urgent safety observation is separately authorized, report that scope distinctly; do not pretend the normal gate passed.

## Roles and authority

- **Owner:** sets intent, authorizes bounded assignments and private materials, decides controversial policy, approves merges/releases. A prefilled `Owner Reply` form under a shared GitHub login is input requiring interpretation and, for protected decisions, separate Owner confirmation.
- **Oracle:** re-grounds, designs tasks and contrasts, maintains Progress records under an assigned writer lease, reconciles actual return artifacts, exposes uncertainty and proposes improvements. An Oracle contributor may not independently accept its own code.
- **Engineer:** after grounding and explicit task-specific authorization, executes bounded work, retains source/backup/patch/test proofs and negative cases, reports actual HEAD and a checkable return.
- **Independent reviewer:** separately challenges material claims and likely wrong implementations, with honest independence, method, fixture lineage and exact-head qualifications.
- **Page:** renders published JSON, opens the *prefilled* Owner inlet and re-reads evidence; it neither sends issues nor starts agents.

## Relay flow and improvement loop

```text
Owner intent / current governing sources
    ↓
Oracle builds contract-native parallel task/dependency map
    ↓
ASSIGNED AGENT READS GROUNDING FIXTURE FIRST → posts onboarding receipt
    ↓
Owner task authorization and private-custody/HOLD checks
    ↓
Bounded engineer work → versioned candidate + proof + untested/failed cases
    ↓
Distinct adversarial reviewer → PASS/FAIL/HOLD/NOT_RUN claim judgments
    ↓
Oracle reconciles source, candidate, reviewer and dependent consumers
    ├─ Falsified → bounded repair and another independent check
    ├─ Improvement → separately logged alternative/benefit/risk/falsifier
    └─ Qualified → authorized integration and fresh joint challenge
    ↓
Owner-only acceptance / merge / production release
```

A packet created ≠ sent. Sent ≠ picked up. Acknowledged ≠ executed. Author tests ≠ independent review. Subsystem PASS ≠ integrated acceptance. The NEXT OBSERVABLE names the responsible actor, required evidence and actual prerequisite, not a substitute for dispatch or proof. Preserve independent parallel workstreams. Improvements must retain the original purpose, competing explanation, cost/benefit, falsifier, scope owner and conditions for adoption; no silent "helpful" scope expansion.

## Mapping the landing-page data contract (no new tab required)

| Data file | Oracle maintenance obligation | What it cannot prove |
| --- | --- | --- |
| `<project>/<topic>/fixtures.json` | Mandatory pre-start anchor; current project/issue/PR links, intent, inputs, public-safe benchmark custody, known failures, next dependency, safe improvement references | That an agent read it or holds protected files |
| `<project>/index.json` | Confirmed `id8` agent/Oracle aliases and optional public GitHub task links; project and topic last-write stamps | Principal independence, active execution |
| `<topic>/meta.json`, `stages.json` | Actual milestones/parallel lanes, stage ID, next `actor`, `detail.do`, `detail.waits`, `detail.done`, exact PR/commit/test `refs` and truthful normalized `state` | That a prepared task is a completed milestone |
| `<topic>/actions.json` | Real unresolved **Owner decisions only**, options, one suggested response, affected stage IDs, and `done.answer` with verified words, time and durable source | That the form checkbox or shared account authenticated Owner consent |
| `<project>/audit.json` | Append-only evidence ledger from declared baseline; every material fixture/roster/task/decision update and **every stage transition** with actual source, actor, reason, previous event and before/after states | Pre-baseline private history or independent truth merely from a row |

**Benchmarks:** the viewer supports only `repository, issues, pullRequests, roadmap, highRoi, future, intent, inputs, knownIssues, pending` fixture sections. Public-safe benchmark identifiers, version, custodian *role*, access rules and scope-limited test receipts belong in `inputs`/stage refs. **Do not add a `benchmarks` JSON section**; do not post private ORIGINALS, sealed BM/BM3 goldens, Drive URLs or withheld expected outputs in this public repository. Hash identity alone is not technical acceptance.

## Status, freshness and evidence requirements

`NOT_STARTED` = no verified execution; `IN_PROGRESS` = actual work evidenced; `SUBMITTED` = candidate returned, not yet independently qualified; `VERIFIED` = every contract-specific check satisfied at assessed revision; `BLOCKED` = known failure/hold/missing prerequisite; `STALE` = superseded evidence; `UNKNOWN` = contradictory/inaccessible; `NOT_APPLICABLE` = governed exclusion. Pass/fail/NOT_RUN remain claim-level judgments, not percentages.

Freeze independent expectations before reading the candidate when possible. Preserve comparison method and exact byte/test receipts. Distinguish native checkout, source-exact reconstructed Node, browser DOM harness, true served HTTP, authorized originals and sealed benchmark reviews. On new HEAD, only requalify affected claims. Owner HOLD and protected decisions remain externally authoritative. A LIVE badge means updated JSON; it is **not** live agent observation or acceptance.

## Audit: complete dashboard history from declared baseline, no invented past

The initial ledger `audit.json` contains one `BASELINE` event for each currently displayed stage at the pinned old Progress commit. These records are **snapshots of previously declared states**, not proof those old events actually occurred, passed tests or were independently accepted. Event IDs and `previous_id` form an ordered chain; Git commit history/PR diff is the tamper-evident publication boundary.

For **every future standalone Progress update**, append source-backed events:
`GROUNDING_UPDATE`, `AGENT_ONBOARDING`, `TASK_HANDOFF`, `AGENT_RETURN`, `INDEPENDENT_REVIEW`, `BENCHMARK_RECEIPT`, `OWNER_INPUT_RECEIVED`, `OWNER_DECISION`, `IMPROVEMENT_PROPOSAL`, `STAGE_TRANSITION`, `PUBLICATION` as applicable. Do **not** log an onboarding or dispatch without an actual receipt. For a `STAGE_TRANSITION`, give exact `stage`, `before`, `after` and public GitHub source; the validator requires the final state in the chain to match `stages.json`. A protected private source uses `OWNER_PRIVATE_REF:<redacted-record-id>` and is reconciled privately by Owner. The ledger covers recorded dashboard mutations after its baseline, **not activity invisibly occurring outside GitHub**.

Helper usage on an authorized *local checkout* (it never sends GitHub actions):

```sh
python scripts/check_progress_data.py
python scripts/standalone_oracle_relay.py check --project ciifr
python scripts/standalone_oracle_relay.py append --project ciifr --topic normal \
  --kind AGENT_ONBOARDING --actor 'Agent A1' \
  --source 'https://github.com/owner/repo/issues/123#issuecomment-456' \
  --summary 'Read required fixtures; source and authority checked, receipt on owning task.'
# Stage transition example: first update stages.json on the same branch;
# then append with --kind STAGE_TRANSITION --stage N3 --before BLOCKED --after SUBMITTED.
```

An Oracle who changes only a source fixture must still record `GROUNDING_UPDATE`. Before a PR, compare every Progress data diff against the ledger; the built-in validator checks chronology and stage-state agreement, but cannot authenticate roles, file-read receipts or that a non-state change was logged. Those are explicit reviewer duties.

## Owner inlet — no coordinator

For projects marked `"mode": "standalone-oracle"`, **My actions → Send to Oracle** and **Grounding fixtures + / −** create a prefilled *GitHub Owner Reply draft* with `target=Oracle`. The Owner examines and submits it. Oracle logs received input separately from an accepted, scoped Owner decision; `actions.json` stays OPEN until Owner meaning/authority and corresponding durable reference are confirmed. This does not create an agent dispatch, task start, change to source or automatic acceptance. Projects without the mode retain OTM routing.

## One-topic writer, review and adoption

1. Read latest main, fixture revision, target issues/PR heads, current HOLD and any competing data PRs. Only one writer per topic, with a distinct branch and tracked preimages.
2. Reconcile source facts, receipt, stage impact, private custody and next actor; update only public-safe `site/progress-data/` plus protocol/tool tests when required.
3. Update project/topic timestamps and roster only with actual evidence. Append audit events for changes and stages; preserve negative knowledge and old evidence refs.
4. Validate all data and source; publish a small draft PR. **Oracle-created PR ≠ Owner-approved merge**. Owner or designated independent checker examines diff, ledger continuity, preserved Coordinator routing and the exact source basis.
5. On Owner-authorized merge, read back the public page. On new Oracle/agent session, re-open this fixture before relying on any prior NEXT or task packet.

**EXACT_NEXT_ACTION for all new standalone agents:** Open the assigned topic's Grounding fixtures, read the governing sources and this protocol, post the real onboarding receipt, establish task-specific authority, then execute only the authorized work.
