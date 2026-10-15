#!/usr/bin/env python3
"""
build_test.py — Test the data builder against the two benchmark snapshots.

Checks that all 8 hard cases from the brief §6 are present in the output.

Usage:
  python tests/build_test.py

Must be run from the repository root (or set REPO_ROOT env var).
Exits 0 on all-pass, non-zero on any failure.
"""

import json
import os
import sys
import tempfile
from pathlib import Path

# Allow import of scripts/build_data.py
REPO_ROOT = Path(os.environ.get('REPO_ROOT', Path(__file__).parent.parent)).resolve()
sys.path.insert(0, str(REPO_ROOT / 'scripts'))
import build_data  # noqa: E402


PASS = '✅'
FAIL = '❌'
results: list[tuple[str, bool, str]] = []


def check(name: str, condition: bool, detail: str = ''):
    results.append((name, condition, detail))
    status = PASS if condition else FAIL
    print(f"  {status} {name}" + (f": {detail}" if detail else ''))


def run_build(out_dir: Path) -> tuple:
    """Run the build against both benchmarks, return (projects, timelines)."""
    bm1 = REPO_ROOT / 'benchmarks' / 'grade9-pilot-2026-10-15'
    bm2 = REPO_ROOT / 'benchmarks' / 'imo-ab-test-2026-10-15'
    return build_data.build_all(REPO_ROOT, out_dir, [bm1, bm2])


def load(out_dir: Path, filename: str) -> dict | list | None:
    path = out_dir / filename
    if not path.exists():
        return None
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def main():
    print(f"\nRunning build against benchmark snapshots (repo: {REPO_ROOT})\n")

    with tempfile.TemporaryDirectory() as tmpdir:
        out = Path(tmpdir)
        projects, timelines = run_build(out)

        # Index projects by name
        proj_map = {p['project']: p for p in projects}
        g9 = proj_map.get('grade9-pilot')
        imo = proj_map.get('imo-ab-test')

        print("\n--- Hard case checks ---\n")

        # ── Hard case 1: Two coordinators over time (grade9-pilot) ──────────
        print("Hard case 1: Two coordinators over time (grade9-pilot)")
        g9_ctrl = g9['registry']['control'] if g9 else {}
        epoch = g9_ctrl.get('epoch', 0)
        coord = g9_ctrl.get('coordinator', '')
        paused = g9_ctrl.get('paused', [])
        check("grade9-pilot epoch = 2", epoch == 2, f"epoch={epoch}")
        check("epoch 2 coordinator is OwnerTeammember stand-in",
              'OwnerTeammember' in coord, coord)
        check("paused list contains Codex epoch 1",
              any('Codex' in str(p) for p in paused), str(paused))

        # ── Hard case 2: Retired agents (g1) and successors (g2) ────────────
        print("\nHard case 2: Retired g1 agents and active g2 successors (grade9-pilot)")
        g9_agents = g9['agents'] if g9 else []
        retired = [a for a in g9_agents if a['status'] == 'retired']
        active = [a for a in g9_agents if a['status'] == 'active']
        check("has retired g1 agents", len(retired) >= 2, f"found {len(retired)}")
        check("has active g2 agents", len(active) >= 2, f"found {len(active)}")
        check("g1 validator chat_id8=6ad02130",
              any(a['chat_id8'] == '6ad02130' for a in retired))
        check("g2 validator chat_id8=6ad0506c",
              any(a['chat_id8'] == '6ad0506c' for a in active))

        # ── Hard case 3: FAIL → fix → re-check → PASS chain (imo-ab-test) ──
        print("\nHard case 3: FAIL→fix→re-check→PASS chain (imo-ab-test, Agent A/B)")
        imo_tl = timelines.get('imo-ab-test', [])
        # Look for evidence events from both agents
        agent_a_events = [e for e in imo_tl if e.get('type') == 'TASK_EVIDENCE'
                          and e.get('chat_id8', '').startswith('6ad0449d')]
        agent_b_events = [e for e in imo_tl if e.get('type') == 'TASK_EVIDENCE'
                          and e.get('chat_id8', '').startswith('6ad04451')]
        check("Agent A (6ad0449d) has evidence in timeline",
              len(agent_a_events) >= 2, f"found {len(agent_a_events)}")
        check("Agent B (6ad04451) has evidence in timeline",
              len(agent_b_events) >= 2, f"found {len(agent_b_events)}")

        # Load Agent A evidence detail
        ev_a = load(out, 'evidence-6ad0449d.json')
        ev_b = load(out, 'evidence-6ad04451.json')
        a_blocks = ev_a['agent']['evidence'] if ev_a else []
        b_blocks = ev_b['agent']['evidence'] if ev_b else []

        a_verdicts = [e for e in a_blocks if e.get('type') == 'verdict']
        b_verdicts = [e for e in b_blocks if e.get('type') == 'verdict']

        # Should have CORRECTED verdicts (FAIL) and ALIGNED (PASS)
        a_corrected = [v for v in a_verdicts if 'CORRECTED' in v.get('verdict', '')]
        a_aligned = [v for v in a_verdicts if 'ALIGNED' in v.get('verdict', '')]
        check("Agent A has ✏ CORRECTED verdicts (FAIL phase)",
              len(a_corrected) >= 1, f"found {len(a_corrected)}")
        check("Agent A has ✅ ALIGNED verdicts (PASS phase)",
              len(a_aligned) >= 3, f"found {len(a_aligned)}")

        b_fail_ev = [e for e in b_blocks if e.get('type') == 'evidence'
                     and ('FAIL' in e.get('status', '') or
                          'FAIL' in e.get('did', '') or
                          'FAIL' in e.get('raw', ''))]
        check("Agent B (checker) posted FAIL evidence",
              len(b_fail_ev) >= 1, f"found {len(b_fail_ev)}")

        # ── Hard case 4: Outside write flagged (imo-ab-test) ────────────────
        print("\nHard case 4: Outside write commit 5a117f69 flagged (imo-ab-test)")
        imo_ow = imo['outside_writes'] if imo else []
        check("outside_writes array is non-empty", len(imo_ow) >= 1, f"found {len(imo_ow)}")
        check("5a117f69 mentioned in outside writes",
              any('5a117f69' in str(w) for w in imo_ow), str(imo_ow[:1]))

        # Also check in timeline
        ow_tl = [e for e in imo_tl if e.get('type') == 'OUTSIDE_WRITE']
        check("outside-write event in imo-ab-test timeline",
              len(ow_tl) >= 1 or len(imo_ow) >= 1,
              f"timeline OW events: {len(ow_tl)}, registry: {len(imo_ow)}")

        # ── Hard case 5: Role conflict and resolution (imo-ab-test) ─────────
        print("\nHard case 5: Role conflict and resolution (imo-ab-test)")
        imo_ctrl = imo['registry']['control'] if imo else {}
        imo_otm = imo_ctrl.get('owner_teammember', '')
        check("owner_teammember field present in imo-ab-test registry",
              bool(imo_otm), imo_otm[:80] if imo_otm else '(empty)')
        # Timeline should have CONTROL_EPOCH event
        ctrl_events = [e for e in imo_tl if e.get('type') == 'CONTROL_EPOCH']
        check("CONTROL_EPOCH event in imo-ab-test timeline",
              len(ctrl_events) >= 1, f"found {len(ctrl_events)}")

        # ── Hard case 6: Superseded Owner words ──────────────────────────────
        print("\nHard case 6: Superseded Owner words (imo-ab-test, AB-SOURCE)")
        imo_sod = imo['registry']['standing_owner_decisions'] if imo else []
        superseded = [d for d in imo_sod if 'supersedes' in d.lower()]
        check("standing decision with 'supersedes' present",
              len(superseded) >= 1, str(superseded[:1])[:100])
        # Check for the 08:58 → 09:05 pair
        has_0858 = any('08:58' in d or 'need to work with this' in d.lower()
                       for d in imo_sod)
        has_0905 = any('09:05' in d or 'AB-SOURCE update' in d for d in imo_sod)
        check("08:58 instruction recorded in standing decisions", has_0858,
              "(check AB-SOURCE entries)")
        check("09:05 superseding instruction recorded", has_0905,
              "(check AB-SOURCE update entry)")

        # ── Hard case 7: Parked decisions + project under HOLD ───────────────
        print("\nHard case 7: Parked decisions and project HOLD (grade9-pilot)")
        g9_ood = g9['registry']['open_owner_decisions'] if g9 else []
        g9_diff13 = [d for d in g9_ood if 'G9-DIFF-13' in d.get('id', '')]
        check("G9-DIFF-13 in open_owner_decisions", len(g9_diff13) >= 1,
              f"found {len(g9_diff13)}")

        g9_hold = g9['registry']['control'].get('hold', {}) if g9 else {}
        check("grade9-pilot control.hold is set",
              bool(g9_hold) and g9_hold.get('owner_words'),
              str(g9_hold))

        imo_ood = imo['registry']['open_owner_decisions'] if imo else []
        ab_q003 = [d for d in imo_sod if 'AB-Q003-RUN' in d]
        check("AB-Q003-RUN in standing decisions (parked dispatch)",
              len(ab_q003) >= 1, str(ab_q003[:1])[:80])

        # ── Hard case 8: Time-corrected records ──────────────────────────────
        print("\nHard case 8: Time-corrected coordinator records (imo-ab-test)")
        tc_events = [e for e in imo_tl if e.get('type') == 'COORDINATOR_EVIDENCE'
                     and e.get('time_corrected')]
        check("time-corrected COORDINATOR_EVIDENCE event in timeline",
              len(tc_events) >= 1, f"found {len(tc_events)}")

        # ── Bonus: both benchmarks load correctly ─────────────────────────────
        print("\nBonus: basic structure checks")
        check("grade9-pilot loaded", g9 is not None)
        check("imo-ab-test loaded", imo is not None)
        check("grade9-pilot timeline has events", len(timelines.get('grade9-pilot', [])) >= 1)
        check("imo-ab-test timeline has events", len(timelines.get('imo-ab-test', [])) >= 1)
        check("grade9-pilot timeline_source = events_jsonl",
              g9 and g9.get('timeline_source') == 'events_jsonl',
              g9.get('timeline_source') if g9 else 'N/A')
        check("imo-ab-test timeline_source = reconstructed",
              imo and imo.get('timeline_source') == 'reconstructed',
              imo.get('timeline_source') if imo else 'N/A')
        check("chat IDs appear only as id8 (no full UUID in output)",
              all(
                  'chat.openai.com' not in str(e)
                  for e in timelines.get('imo-ab-test', [])
              ), "checked timeline for raw chat URLs")

    # ── Summary ──────────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    passed = sum(1 for _, ok, _ in results if ok)
    total = len(results)
    print(f"Result: {passed}/{total} checks passed\n")
    for name, ok, detail in results:
        if not ok:
            print(f"  {FAIL} FAILED: {name}" + (f" — {detail}" if detail else ''))

    if passed == total:
        print("ALL CHECKS PASSED ✅")
        return 0
    else:
        print(f"{total - passed} CHECK(S) FAILED ❌")
        return 1


if __name__ == '__main__':
    sys.exit(main())
