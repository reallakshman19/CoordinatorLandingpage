"""WP-V4 D5 RED guards: synthetic returning agent, no real posts or writes."""
import copy
from datetime import datetime, timezone
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import next_move
import next_move_claim
import next_move_evaluator
import status_bar
from landing_build.project_evidence import build_agent_evidence
from tests.test_wp13 import register, record, FIRST, TO, REGSHA, event
from tests.test_wp14 import FakeTransport

NOW = datetime(2026, 10, 18, 5, 0, tzinfo=timezone.utc)
REPO = "reallakshman19/CoordinatorLandingpage"
RETIRED = "6ad36e4d"
SRC = f"https://github.com/{REPO}/issues/64#issuecomment-990004005"
EVIDENCE = ("TASK EVIDENCE v2 · landing-live · coder · "
            f"chat {RETIRED} · #4 · 18 Oct 08:59 +04\n"
            "Task: unapproved work\nStatus: DONE")
THREAD = {"number": 64, "repository": REPO, "comments": [
    {"id": 990004005, "created_at": "2026-10-18T04:59:00Z", "body": EVIDENCE}]}


def synthetic_registry(status="RETIRED 2026-10-18; predecessor", released=True):
    registry = register()
    registry["agents"] = [
        {"chat_id8": "11111111", "role": "coder", "status": "active"},
        {"chat_id8": RETIRED, "role": "coder", "status": status,
         "evidence_thread": f"https://github.com/{REPO}/issues/64",
         "retired_at": "2026-10-18T03:30:00Z"}]
    registry["leases"] = ([{"holder": "Coder " + RETIRED,
                            "branches": "codex/old",
                            "released": "2026-10-18T03:30:00Z"}] if released else [])
    return registry


def claimed_record():
    move = record()
    move["to"] = {"role": "coder", "id8": RETIRED}
    return move


class D5RetirementSafety(unittest.TestCase):
    def test_01_evaluator_source_linked_block_from_retired_claim_on_64(self):
        reg = synthetic_registry()
        view = {"moves": [], "task_cycle": {}, "flags": []}
        report = next_move_evaluator.evaluate(
            reg, view, [], {64: THREAD}, NOW,
            {"role": "TeamCoordinator", "id8": "11111111"}, REGSHA)
        recs = report.get("recommendations", [])
        block = [x for x in recs if x.get("kind") == "RETIREMENT_RETURN_BLOCK"]
        self.assertEqual(len(block), 1)
        self.assertEqual(block[0]["chat_id8"], RETIRED)
        self.assertEqual(block[0]["source"], SRC)
        self.assertEqual(block[0]["status"], "HOLD_RECOMMENDED")
        self.assertTrue(report["read_only"])
        self.assertFalse(report["may_send"])

    def test_02_evaluator_detects_status_v2_on_62_without_fake_go(self):
        reg = synthetic_registry()
        status = f"STATUS v2 · coder · chat {RETIRED} · working on old work · next write · blocker none"
        thread = {"number": 62, "repository": REPO, "comments": [
            {"id": 990004006, "created_at": "2026-10-18T04:59:00Z",
             "body": status}]}
        report = next_move_evaluator.evaluate(
            reg, {"moves": [], "task_cycle": {}, "flags": []}, [], {62: thread},
            NOW, {"role": "TeamCoordinator", "id8": "11111111"}, REGSHA)
        self.assertEqual(report["recommendations"][0]["source"],
                         f"https://github.com/{REPO}/issues/62#issuecomment-990004006")
        self.assertFalse(report["may_send"])

    def test_03_postretirement_evidence_visible_but_not_eligible(self):
        actual = build_agent_evidence(
            THREAD, "landing-live", RETIRED, retired=True,
            retired_at="2026-10-18T03:30:00Z")
        self.assertEqual(len(actual), 1)
        self.assertEqual(actual[0]["type"], "evidence")
        self.assertEqual(actual[0]["eligibility"], "INELIGIBLE")
        self.assertEqual(actual[0]["eligibility_reason"],
                         "retired_actor_post")
        self.assertFalse(actual[0]["counts_for_go"])

    def test_04_pre_retirement_history_remains_visible(self):
        earlier = copy.deepcopy(THREAD)
        earlier["comments"][0]["created_at"] = "2026-10-18T02:59:00Z"
        rows = build_agent_evidence(earlier, "landing-live", RETIRED,
                                    retired=True, retired_at="2026-10-18T03:30:00Z")
        self.assertEqual(len(rows), 1)
        self.assertNotEqual(rows[0].get("eligibility"), "INELIGIBLE")

    def test_05_invalid_retirement_clock_fails_closed(self):
        rows = build_agent_evidence(THREAD, "landing-live", RETIRED,
                                    retired=True, retired_at=None)
        self.assertEqual(rows[0]["eligibility"], "INELIGIBLE")
        self.assertFalse(rows[0]["counts_for_go"])

    def test_06_next_move_rejects_retired_recipient(self):
        reg = synthetic_registry(released=False)
        good, bad, _ = next_move.validate_records(
            reg, {FIRST+".json": claimed_record()}, [], {}, NOW)
        self.assertEqual(good, [])
        self.assertTrue(any("recipient_retired" in x["reasons"] for x in bad))

    def test_07_next_move_rejects_released_lease_even_if_active(self):
        reg = synthetic_registry(status="active")
        good, bad, _ = next_move.validate_records(
            reg, {FIRST+".json": claimed_record()}, [], {}, NOW)
        self.assertEqual(good, [])
        self.assertTrue(any("recipient_lease_released" in x["reasons"] for x in bad))

    def test_08_next_move_rejects_retired_approval_actor(self):
        reg = synthetic_registry()
        move = record()
        reg["agents"].append({"chat_id8": "22222222", "role": "coder", "status": "active"})
        transition = event("APPROVED", "14:01",
                           by={"role": "OwnerTeammember", "id8": RETIRED})
        good, bad, _ = next_move.validate_records(
            reg, {FIRST+".json": move}, [transition], {}, NOW)
        self.assertEqual(good, [])
        self.assertTrue(any("transition_actor_retired" in x["reasons"] for x in bad))

    def test_09_next_move_claim_refuses_retired_before_put(self):
        reg = register()
        reg["agents"][1]["status"] = "RETIRED"
        api = FakeTransport(registry=reg)
        with self.assertRaisesRegex(next_move_claim.ClaimRefused, "recipient_retired"):
            next_move_claim.make_claim(
                api, "main", FIRST, REGSHA, TO, now=NOW)
        self.assertEqual(api.sent, [])

    def test_10_next_move_claim_refuses_released_lease_before_put(self):
        reg = register()
        reg["leases"] = [{"holder": "Coder 22222222",
                          "released": "2026-10-16T13:00:00Z"}]
        api = FakeTransport(registry=reg)
        with self.assertRaisesRegex(next_move_claim.ClaimRefused, "recipient_lease_released"):
            next_move_claim.make_claim(
                api, "main", FIRST, REGSHA, TO, now=NOW)
        self.assertEqual(api.sent, [])

    def test_11_status_bar_blocks_released_lease_when_actor_active(self):
        reg = {"project": "case", "repository": REPO, "agents": [
            {"chat_id8": RETIRED, "role": "coder", "status": "active",
             "observation": {"state": "WORKING", "reachable": True,
                             "observed_at": "2026-10-18T04:58:00Z"}}],
               "leases": [{"holder": "Coder " + RETIRED,
                           "released": "2026-10-18T03:30:00Z",
                           "verified": True}]}
        view = {"next_move": {"evaluator_at": "2026-10-18T04:58:00Z"}}
        item = status_bar.derive_status(status_bar.normalize_roster(reg)[0],
                                        reg, view, NOW)
        self.assertEqual(item["dimensions"]["execution_authority"]["state"], "blocked")
        self.assertEqual(item["dimensions"]["execution_authority"]["reason"],
                         "writer_lease_released")
        self.assertEqual(item["light"], "red")

    def test_12_cannot_promote_retired_report_to_go_counter(self):
        agents = [{"chat_id8": RETIRED, "status": "retired",
                   "retired_at": "2026-10-18T03:30:00Z", "evidence_thread_num": 64}]
        go = claimed_record()
        go["created_at"] = "2026-10-18T02:00:00Z"
        go["state"] = "APPROVED"
        result = next_move.task_cycle(agents, {64: THREAD}, [go], "landing-live", NOW)
        self.assertEqual(result["count"], 0)

    def test_13_no_false_block_on_active_actor_without_released_lease(self):
        reg = register()
        valid, rejected, _ = next_move.validate_records(
            reg, {FIRST+".json": record()}, [], {}, NOW)
        self.assertEqual(rejected, [])
        self.assertEqual(len(valid), 1)

if __name__ == "__main__":
    unittest.main(verbosity=2)
