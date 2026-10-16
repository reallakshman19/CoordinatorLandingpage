#!/usr/bin/env python3
"""UltraEconomyMode read-only and negative authority controls."""
from datetime import datetime, timezone
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import ultra_economy as uem

REPO = "reallakshman19/CoordinatorLandingpage"
URL = "https://github.com/" + REPO + "/issues/22"
NOW = datetime(2026, 10, 16, 14, 40, tzinfo=timezone.utc)
START = """TASK START v1 · landing-live · implementer · chat 11111111 · task WP16 · cycle 1/3
Planned outcome: Deliver opt-in source-based next moves
Expected next: Route independent review after tests
Known blocker: NONE
Workplan: https://github.com/reallakshman19/CoordinatorLandingpage/issues/21
Fallback: agent to arm hourly ChatGPT task
"""
END = """TASK EVIDENCE v2 · landing-live · implementer · chat 11111111 · #28 · 16 Oct 18:20 +04
Task: WP16 opt-in source-based next moves
Status: ENGINEERING DONE / independent review pending
Did: Added read-only projection
Not done / HOLD: independent review pending
Next: reviewer check
UEM cycle: 1/3
"""


def fixture(*, end=True, limit=3, cycle=1, state="SENT_TO_CHAT", hold=None,
            marker=None, move=True):
    start = START.replace("cycle 1/3", f"cycle {cycle}/{limit}")
    end_body = (END.replace("UEM cycle: 1/3", f"UEM cycle: {cycle}/{limit}")
                if marker is None else marker)
    rows = [{"id": 101, "created_at": "2026-10-16T14:00:00Z", "body": start}]
    if end:
        rows.append({"id": 102, "created_at": "2026-10-16T14:20:00Z", "body": end_body})
    reg = {"project": "landing-live", "repository": REPO,
           "ultra_economy": {"enabled": True, "max_cycles": limit},
           "control": {"hold": hold}}
    agents = [{"chat_id8": "11111111", "role": "implementer", "status": "active",
               "evidence_thread_url": URL}]
    moves = []
    if move:
        moves.append({
            "id": "NM-20261016-142100-abcd", "class": "Dispatch", "state": state,
            "to": {"role": "implementer", "id8": "11111111"},
            "trigger": {"type": "uem_end", "task": "WP16", "cycle": cycle,
                        "end_comment_id": 102},
            "basis": {"evidence": URL}, "flags": []})
    return reg, agents, {22: {"number": 22, "comments": rows}}, {"moves": moves}


def current(*args, **kwargs):
    reg, agents, threads, view = fixture(*args, **kwargs)
    return uem.project(reg, agents, threads, view, now=NOW)["agents"]["11111111"]


class UltraEconomyTests(unittest.TestCase):
    def test_01_disabled_by_default(self):
        reg, agents, threads, view = fixture()
        del reg["ultra_economy"]
        self.assertFalse(uem.project(reg, agents, threads, view, now=NOW)["enabled"])

    def test_02_config_must_be_1_to_5_not_bool(self):
        for bad in (0, 6, True, "3", None, -1):
            reg, agents, threads, view = fixture()
            reg["ultra_economy"]["max_cycles"] = bad
            out = uem.project(reg, agents, threads, view, now=NOW)
            self.assertFalse(out["enabled"])
            self.assertEqual(out["error"], "invalid_max_cycles")

    def test_03_start_provides_plan_and_hourly_fallback_requirement(self):
        task = current(end=False)
        self.assertEqual(task["state"], "WORKING_CLAIM")
        self.assertEqual(task["planned_outcome"], "Deliver opt-in source-based next moves")
        self.assertEqual(task["known_blocker"], "NONE")
        self.assertEqual(task["fallback"], "AGENT_MUST_ARM")
        self.assertEqual(task["fallback_due_at"], "2026-10-16T15:00:00+00:00")
        self.assertFalse(task["may_proceed"])

    def test_04_end_exact_cycle_and_status_claim(self):
        task = current(move=False)
        self.assertEqual(task["claim_status"], "DONE")
        self.assertEqual(task["end_comment_id"], 102)
        self.assertEqual(task["state"], "NO_MATCHING_MOVE")
        self.assertFalse(task["may_proceed"])

    def test_05_published_approved_and_thread_publication_do_not_deliver(self):
        for state in ("PUBLISHED", "APPROVED", "CLAIMED", "SEND_INTENT",
                      "PUBLISHED_TO_THREAD", "DELIVERY_UNCERTAIN"):
            task = current(state=state)
            self.assertEqual(task["state"], "AWAITING_DELIVERY", state)
            self.assertFalse(task["may_proceed"])

    def test_06_matching_proven_chat_delivery_enables_readback(self):
        task = current()
        self.assertEqual(task["state"], "NEXT_MOVE_RECORDED_DELIVERED")
        self.assertTrue(task["may_proceed"])
        self.assertEqual(task["move_id"], "NM-20261016-142100-abcd")

    def test_07_wrong_comment_id_must_not_match(self):
        reg, agents, threads, view = fixture()
        view["moves"][0]["trigger"]["end_comment_id"] = 999
        item = uem.project(reg, agents, threads, view, now=NOW)["agents"]["11111111"]
        self.assertEqual(item["state"], "NO_MATCHING_MOVE")

    def test_08_stale_basis_blocks_even_sent_move(self):
        reg, agents, threads, view = fixture()
        view["moves"][0]["flags"] = ["stale basis"]
        item = uem.project(reg, agents, threads, view, now=NOW)["agents"]["11111111"]
        self.assertEqual(item["state"], "STALE_MOVE")
        self.assertFalse(item["may_proceed"])

    def test_09_max_cycles_cannot_start_sixth(self):
        task = current(limit=1, cycle=1)
        self.assertEqual(task["state"], "MAX_CYCLES_REACHED")
        self.assertFalse(task["may_proceed"])

    def test_10_project_hold_overrides_valid_delivery(self):
        task = current(hold="Owner HOLD")
        self.assertEqual(task["state"], "HOLD")
        self.assertFalse(task["may_proceed"])

    def test_11_missing_or_mismatched_end_cycle_is_not_done(self):
        task = current(marker=END.replace("UEM cycle: 1/3", "UEM cycle: 2/3"))
        self.assertEqual(task["state"], "WORKING_CLAIM")
        self.assertNotIn("claim_status", task)

    def test_12_inactive_agent_no_execution(self):
        reg, agents, threads, view = fixture()
        agents[0]["status"] = "retired"
        item = uem.project(reg, agents, threads, view, now=NOW)["agents"]["11111111"]
        self.assertEqual(item["state"], "NOT_ACTIVE")
        self.assertFalse(item["may_proceed"])

    def test_13_unknown_source_not_falsely_working(self):
        reg, agents, threads, view = fixture()
        out = uem.project(reg, agents, {}, view, now=NOW)
        self.assertEqual(out["agents"]["11111111"]["state"], "UNKNOWN_SOURCE")

    def test_14_duplicate_start_warns_no_override(self):
        reg, agents, threads, view = fixture()
        duplicate = {"id": 103, "created_at": "2026-10-16T14:05:00Z",
                     "body": START.replace("Known blocker: NONE", "Known blocker: owner")}
        threads[22]["comments"].append(duplicate)
        item = uem.project(reg, agents, threads, view, now=NOW)["agents"]["11111111"]
        self.assertEqual(item["known_blocker"], "NONE")
        self.assertIn("duplicate_task_start", item["warnings"])

    def test_15_future_due_window(self):
        task = current(move=False)
        self.assertEqual(task["followup"]["state"], "WAITING")
        self.assertEqual(task["followup"]["next_due_at"], "2026-10-16T14:50:00+00:00")
        self.assertEqual(uem._followup("2026-10-16T14:20:00Z",
                         datetime(2026,10,16,14,51,tzinfo=timezone.utc))["state"],
                         "OVERDUE_30")
        self.assertEqual(uem._followup("2026-10-16T14:20:00Z",
                                     datetime(2026,10,16,14,22,tzinfo=timezone.utc)),
                         {"state": "WAITING", "next_due_at": "2026-10-16T14:35:00+00:00"})

    def test_16_no_double_move_claim(self):
        reg, agents, threads, view = fixture()
        view["moves"].append(dict(view["moves"][0], id="NM-20261016-142101-eeee"))
        item = uem.project(reg, agents, threads, view, now=NOW)["agents"]["11111111"]
        self.assertEqual(item["state"], "AMBIGUOUS_MOVE")
        self.assertFalse(item["may_proceed"])

    def test_17_cross_project_source_fenced(self):
        reg, agents, threads, view = fixture()
        reg["repository"] = "reallakshman19/Other"
        self.assertEqual(uem.project(reg, agents, threads, view, now=NOW)["agents"], {})

    def test_19_recorded_delivery_stops_followup_reminders(self):
        item = current()
        self.assertEqual(item["followup"], {"state": "STOPPED", "next_due_at": None})

    def test_20_spoofed_role_does_not_match_registered_agent(self):
        reg, agents, threads, view = fixture()
        threads[22]["comments"][0]["body"] = START.replace(
            "· implementer ·", "· validator ·")
        item = uem.project(reg, agents, threads, view, now=NOW)["agents"]["11111111"]
        self.assertEqual(item["state"], "NO_TASK_START")
        self.assertFalse(item["may_proceed"])

    def test_21_timer_claim_is_not_host_verified(self):
        reg, agents, threads, view = fixture(end=False)
        threads[22]["comments"][0]["body"] = START.replace(
            "Fallback: agent to arm hourly ChatGPT task",
            "Fallback: ARMED task-receipt-example")
        item = uem.project(reg, agents, threads, view, now=NOW)["agents"]["11111111"]
        self.assertEqual(item["fallback"], "AGENT_REPORTED_ARMED_UNVERIFIED")

    def test_18_invalid_start_has_no_action(self):
        reg, agents, threads, view = fixture()
        threads[22]["comments"][0]["body"] = START.replace(
            "Workplan: https://github.com/reallakshman19/CoordinatorLandingpage/issues/21",
            "Workplan: https://example.com/unknown")
        item = uem.project(reg, agents, threads, view, now=NOW)["agents"]["11111111"]
        self.assertEqual(item["state"], "NO_TASK_START")
        self.assertFalse(item["may_proceed"])


if __name__ == "__main__":
    unittest.main()
