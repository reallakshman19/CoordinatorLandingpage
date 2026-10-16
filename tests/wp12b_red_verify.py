#!/usr/bin/env python3
"""Fail-closed shared verifier for WP12b–WP15 RED controls."""
import re
import sys
from pathlib import Path

if len(sys.argv) != 4:
    raise SystemExit("usage: wp12b_red_verify.py ui|app|source|wp13_ui|wp13_source|wp14_ui|wp14_source|wp15_ui|wp15_source <log> <test_rc>")
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
    "wp13_source": {
        "test_wp13_pinned_rejects_invalid_move",
        "test_wp13_pinned_exposes_real_task_counter",
    },
    "wp13_ui": {
        "WP13_UI_01_board_readonly_navigation",
        "WP13_UI_02_board_states_and_criticality",
        "WP13_UI_03_active_queue_and_approver",
        "WP13_UI_04_flags_and_rejected_reason",
        "WP13_UI_05_mod20_counter_from_go",
        "WP13_UI_06_agent_own_dispatch_queue",
        "WP13_UI_07_no_next_move_actions",
    },
    "wp14_source": {
        "test_wp14_expired_claimed_flag_was_missing",
        "test_wp14_missing_heartbeat_must_detect_due_ground",
    },
    "wp14_ui": {
        "WP14_UI_01_pilot_compose_controls_on_board",
        "WP14_UI_02_project_compose_and_published_approval",
        "WP14_UI_03_compose_prefills_one_exact_owner_input_json",
        "WP14_UI_04_invalid_draft_does_not_open_github",
        "WP14_UI_05_approval_is_request_not_approved",
        "WP14_UI_06_external_critical_nonpilot_no_controls",
        "WP14_UI_07_no_agent_auto_claim_or_send",
    },
    "wp15_source": {
        "test_wp15_pinned_evaluator_report_missing_is_explicit",
        "test_wp15_pinned_evaluator_mismatch_is_visible",
    },
    "wp15_ui": {
        "WP15_UI_01_board_evaluator_panel",
        "WP15_UI_02_last_committed_evaluated_time",
        "WP15_UI_03_recent_evaluated_not_stale",
        "WP15_UI_04_overdue_task_not_acted_on",
        "WP15_UI_05_mismatched_report_is_explicit",
        "WP15_UI_06_agent_evaluator_cross_check",
        "WP15_UI_07_proposal_not_heartbeat_or_sender",
    },
}
if mode not in expected:
    raise SystemExit("unknown RED mode")
if mode in ("source", "wp13_source", "wp14_source", "wp15_source"):
    prefix = {"source":"test_wp12b_", "wp13_source":"test_wp13_",
              "wp14_source":"test_wp14_", "wp15_source":"test_wp15_"}[mode]
    matches = re.findall(
        r"^(" + prefix + r"\w+)\s+\([^\n]+\)\s+\.\.\.\s+(FAIL|ERROR)$",
        log, re.M)
    fails = {name for name, outcome in matches if outcome == "FAIL"}
    errors = {name for name, outcome in matches if outcome == "ERROR"}
    counts_valid = (re.search(r"^Ran 2 tests in ", log, re.M)
                    and "FAILED (failures=2)" in log)
else:
    tag = {"ui":"WP12_UI_BASE", "app":"WP12B_ONLY",
           "wp13_ui":"WP13_BROWSER", "wp14_ui":"WP14_BROWSER",
           "wp15_ui":"WP15_BROWSER"}[mode]
    pattern = {"ui":r"WP12_UI_0[1-7]_\w+",
               "app":r"WP12B_UI_0[1-3]_\w+",
               "wp13_ui":r"WP13_UI_0[1-7]_\w+",
               "wp14_ui":r"WP14_UI_0[1-7]_\w+",
               "wp15_ui":r"WP15_UI_0[1-7]_\w+"}[mode]
    fails = set(re.findall(r"^FAIL (" + pattern + r")$", log, re.M))
    count = re.search(
        rf"^{tag}_COUNTS pass=(\d+) fail=(\d+) error=(\d+)$", log, re.M)
    errors = set() if count and count.group(3) == "0" else {"runner error"}
    counts_valid = (count and count.groups() ==
                    ("0", str(len(expected[mode])), "0"))
# unittest prints a Traceback for expected AssertionError FAIL. Reject
# execution ERROR from parsed outcomes; browser runners must have no Traceback.
ok = (rc != "0" and fails == expected[mode] and not errors and counts_valid
      and (mode in ("source", "wp13_source", "wp14_source", "wp15_source") or "Traceback (most recent call last)" not in log))
print(f"WP12b {mode} RED: {len(fails)} expected FAIL, {len(errors)} ERROR — " +
      ("PASS" if ok else "INVALID"))
if not ok:
    print("observed:", sorted(fails), "expected:", sorted(expected[mode]))
    raise SystemExit(1)
