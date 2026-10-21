"""Report join must not blend projects/generations or promote claims."""
import copy
from datetime import datetime, timezone
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from landing_build.dashboard_report import latest_report

NOW = datetime(2026, 10, 21, 6, tzinfo=timezone.utc)


class DashboardReport(unittest.TestCase):
    def setUp(self):
        self.row = {"instance_id8": "12345678", "generation": 2, "project": "p"}
        self.agent = {"chat_id8": "12345678", "generation": 2,
                      "evidence_thread_url": "https://github.com/owner/product/issues/7",
                      "evidence": [{"type": "status", "chat_id8": "12345678",
                                    "ts": "2026-10-21T05:59:00Z", "comment_id": 4,
                                    "task": "Review PR", "next": "Publish verdict", "blocker": "none"}]}

    def result(self, agents=None):
        return latest_report(self.row, {"agents": agents or [self.agent]}, NOW)

    def test_report_is_qualified_and_linked_without_mutating_source(self):
        before = copy.deepcopy(self.agent)
        r = self.result()
        self.assertEqual(r["status"], "REPORTED")
        self.assertEqual(r["next"], "Publish verdict")
        self.assertEqual(r["source_ref"], "https://github.com/owner/product/issues/7#issuecomment-4")
        self.assertEqual(r["qualification"], "agent_claim_not_activity_or_acceptance")
        self.assertEqual(self.agent, before)

    def test_duplicate_or_wrong_generation_cannot_supply_report(self):
        self.assertEqual(self.result([self.agent, self.agent])["status"], "UNKNOWN")
        self.agent["generation"] = 1
        self.assertEqual(self.result()["status"], "UNKNOWN")
        self.agent["generation"] = True
        self.assertEqual(self.result()["status"], "UNKNOWN")

    def test_foreign_future_unzoned_and_verdict_records_do_not_become_agent_evidence(self):
        original = self.agent["evidence"][0]
        for patch in ({"project": "q"}, {"chat_id8": "87654321"},
                      {"ts": "2026-10-21T07:00:00Z"}, {"ts": "2026-10-21T05:59:00"},
                      {"type": "verdict"}, {"comment_id": True}):
            self.agent["evidence"] = [{**original, **patch}]
            self.assertEqual(self.result()["status"], "UNKNOWN", patch)

    def test_latest_valid_agent_record_wins_not_latest_verdict(self):
        old = {**self.agent["evidence"][0], "ts": "2026-10-21T05:50:00Z", "comment_id": 3}
        verdict = {**self.agent["evidence"][0], "type": "verdict", "comment_id": 5}
        self.agent["evidence"].extend([old, verdict])
        self.assertTrue(self.result()["source_ref"].endswith("-4"))

    def test_actual_status_bar_publisher_includes_envelope_without_upgrading_light(self):
        from status_bar import build_status_bar
        registry = {"project": "p", "repository": "owner/product", "agents": [
            {"chat_id8": "12345678", "generation": 2, "status": "active", "role": "worker"}]}
        view = {"project": "p", "agents": [self.agent]}
        data = build_status_bar({"p": registry}, {"p": view}, NOW)
        self.assertEqual(data["instances"][0]["latest_report"]["next"], "Publish verdict")
        self.assertEqual(data["instances"][0]["light"], "yellow")
        self.assertEqual(data["coverage"]["expected"], data["coverage"]["projected"])

    def test_frozen_benchmark_rows_remain_byte_compatible_without_new_envelope(self):
        from status_bar import build_status_bar
        registry = {"project": "p", "repository": "owner/product", "agents": [
            {"chat_id8": "12345678", "generation": 2, "status": "active", "role": "worker"}]}
        view = {"project": "p", "agents": [self.agent], "is_benchmark": True}
        data = build_status_bar({"p": registry}, {"p": view}, NOW, include_continuity=False)
        self.assertNotIn("latest_report", data["instances"][0])


if __name__ == "__main__":
    unittest.main()
