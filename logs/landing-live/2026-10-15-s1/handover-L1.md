# landing-live · Agent L1 (implementer) · evidence thread

**Project:** `landing-live` · **Repo:** reallakshman19/CoordinatorLandingpage · **Parent:** #21 (read it fully) · **Protocol:** `protocol/TEAM_PROTOCOL.md` v2.3 FINAL CANDIDATE (#7), unchanged.
**Control:** epoch 1, TeamCoordinator = OwnerTeammember = the Claude session (Owner 15 Oct 14:3x: "you will be teamcoodinator and ownerteammember"). Registry: `logs/landing-live/registry.json`.

## Handover (BuddyRunner v1.7 style)

**Owner's aim (controlling, quoted in #21):** "no dash v2, we have to use existing landingpage and make it live, no revamp but high valve [high-value] change, no core protocol change."

**Your role:** implementer, Agent L1 gen 1. You post every finished step here as TASK EVIDENCE v2 (protocol §3). You never merge, deploy, change protocol, create/retire agents, or claim acceptance.

**Baseline:** `main` moved since #21 was written (2a7da2ba → 83e9eef9 at 14:40 +04). Re-pin at the start of each slice and say which SHA you used.

**Order of work (smaller than #21, one draft PR at a time):**
1. **WP0 — read-only.** Post in #21: traceability table G01–G15 → current source line(s) → test that will falsify → expected state. Include the exact blob SHAs you read and what changed vs #21's intake snapshot. No code. **Stop and wait** for my verdict here.
2. **WP1 slice A** (after my GO): `scripts/fetch_live_data.py`, `scripts/build_data.py`, `tests/` only. Targets G01, G03, G04, G10 first (liveness/UNKNOWN-STALE, #1 fetched separately, g1/g2 fence + retired-lease warning, source provenance). New negative fixtures F3, F6 under `tests/fixtures/` (generated, sanitized). Draft PR from a new branch `l1/wp1a-<id8>`.
3. Next slices only after a PASS on the previous one: WP1b (G02/G05/G06 + F5), then WP2.

**Writer grant (narrow, §19):** branches `l1/*` only; paths `scripts/fetch_live_data.py`, `scripts/build_data.py`, `tests/**`. Everything else read-only, especially `protocol/`, `benchmarks/` (frozen F1/F2), `logs/`, `.github/workflows/`, `site/` (until WP2/3 GO). Need another path → ask here first.

**Rules that bite:** F1/F2 fixtures never change. Every new check ships with a red negative control shown failing first. Baseline-red needs a red run on the base. No substring-"PASS" oracles. No private/chat content in fixtures; chat ids as id8 only. Clock times, not estimates. Claims say "local run" vs "CI run <id>"; never "accepted".

**Evidence block end of every reply (also posted here):** `TASK EVIDENCE v2` with task id, status, base SHA, head SHA, files, commands run + result, negative control result, open questions, Next.

**Who checks:** I check each block against GitHub (source-first). Final integrated acceptance (C15) needs a separate independent checker the Owner names later; you never certify your own work.
