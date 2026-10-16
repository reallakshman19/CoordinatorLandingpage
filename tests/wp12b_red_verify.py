#!/usr/bin/env python3
"""Fail-closed verifier for WP12b pinned-source/UI RED jobs. Never masks ERROR."""
import re
import sys
from pathlib import Path

if len(sys.argv) != 4:
    raise SystemExit("usage: wp12b_red_verify.py ui|app|source <log> <test_rc>")
mode, log_path, rc = sys.argv[1:]
log = Path(log_path).read_text(encoding="utf-8")
expected = {
    "ui": {
        "WP12_UI_01_hold_words_and_exact_since",
        "WP12_UI_02_reporting_lines_small_tree",
        "WP12_UI_03_child_progress_one_of_one_own_repo",
        "WP12_UI_04_moved_pr_head_superseded",
        "WP12_UI_05_real_hold_no_invented_since",
        "WP12_UI_06_agent_hold_banner",
        "WP12_UI_07_local_vs_hosted_ci_link",
    },
    "app": {
        "WP12B_UI_01_cycle_warning_shows_all_agents",
        "WP12B_UI_02_agent_evidence_head_moved",
        "WP12B_UI_03_foreign_ci_run_local_only",
    },
    "source": {
        "test_wp12b_project_evidence_single_key_vs_guessed_aliases",
        "test_wp12b_duplicate_children_count_once",
    },
}
if mode not in expected:
    raise SystemExit("unknown RED mode")
if mode == "source":
    matches = re.findall(
        r"^(test_wp12b_\w+)\s+\([^\n]+\)\s+\.\.\.\s+(FAIL|ERROR)$",
        log, re.M)
    fails = {name for name, outcome in matches if outcome == "FAIL"}
    errors = {name for name, outcome in matches if outcome == "ERROR"}
    counts_valid = (re.search(r"^Ran 2 tests in ", log, re.M)
                    and "FAILED (failures=2)" in log)
else:
    tag = "WP12_UI_BASE" if mode == "ui" else "WP12B_ONLY"
    fails = set(re.findall(r"^FAIL (" + (
        r"WP12_UI_0[1-7]_\w+" if mode == "ui"
        else r"WP12B_UI_0[1-3]_\w+") + r")$", log, re.M))
    count = re.search(
        rf"^{tag}_COUNTS pass=(\d+) fail=(\d+) error=(\d+)$", log, re.M)
    errors = set() if count and count.group(3) == "0" else {"runner error"}
    counts_valid = (count and count.groups() ==
                    ("0", str(len(expected[mode])), "0"))
# unittest prints a Traceback for expected AssertionError FAIL. Reject
# execution ERROR from parsed outcomes; browser runners must have no Traceback.
ok = (rc != "0" and fails == expected[mode] and not errors and counts_valid
      and (mode == "source" or "Traceback (most recent call last)" not in log))
print(f"WP12b {mode} RED: {len(fails)} expected FAIL, {len(errors)} ERROR — " +
      ("PASS" if ok else "INVALID"))
if not ok:
    print("observed:", sorted(fails), "expected:", sorted(expected[mode]))
    raise SystemExit(1)
