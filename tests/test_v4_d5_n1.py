"""WP-V4 N1 review follow-up — adversarial source-bound retirement test cases.

All comments, claims, and registry amendments are synthetic/local. Live
registry and historic frozen benchmark remain untouched.
"""
import copy
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import next_move
import next_move_claim
import status_bar
from landing_build.retirement_guard import (
    retired, eligibility_reason, return_recommendations)
from landing_build.project_data import build_project_data
from landing_build.project_evidence import build_agent_evidence
from tests.test_wp13 import FIRST, REGSHA, TO, record, register
from tests.test_wp14 import FakeTransport

REPO = "reallakshman19/CoordinatorLandingpage"
G1 = "6ad0adca"
G4 = "6ad36e4d"
CUTOFF = "2026-10-17T23:33:54Z"
NOW = datetime(2026, 10, 18, 5, tzinfo=timezone.utc)
CLAIM = ("TASK EVIDENCE v2 · landing-live · coder · "
         "chat 6AD36E4D · #7 · 18 Oct 08:59 +04\n"
         "Task: SYNTHETIC retirement return\nStatus: DONE")


def base(**changes):
    reg = register()
    reg["agents"].append({"chat_id8": G4, "status": "active", "role": "coder"})
    reg.update(changes)
    return reg


def signal(body, comment_id=990005001):
    return {64: {"number": 64, "repository": REPO, "comments": [
        {"id": comment_id, "created_at": "2026-10-18T04:59:00Z",
         "body": body}]}}


class D5RetirementN1Hardening(unittest.TestCase):
    def test_01_whitespace_casefold_retired_state(self):
        self.assertTrue(retired({"chat_id8": G4, "status": "  \tReTiReD due to capacity  "}))
        self.assertEqual(eligibility_reason(base(agents=[
            {"chat_id8": G4, "status": " \tRETIRED 18 Oct"}]), G4), "retired")

    def test_02_uppercase_task_evidence_id_detected_and_normalized(self):
        reg = base(agents=[{"chat_id8": G4, "status": "RETIRED",
                            "retired_at": CUTOFF}])
        recs = return_recommendations(reg, signal(CLAIM))
        self.assertEqual(len(recs), 1)
        self.assertEqual(recs[0]["kind"], "RETIREMENT_RETURN_BLOCK")
        self.assertEqual(recs[0]["chat_id8"], G4)
        self.assertEqual(recs[0]["source"],
                         f"https://github.com/{REPO}/issues/64#issuecomment-990005001")

    def test_03_uppercase_status_id_detected_and_normalized(self):
        reg = base(agents=[{"chat_id8": G4, "status": "retired",
                            "retired_at": CUTOFF}])
        body = ("STATUS v2 · coder · chat 6AD36E4D · "
                "working on old work · next write · blocker none")
        rows = return_recommendations(reg, signal(body))
        self.assertEqual([r["chat_id8"] for r in rows], [G4])
        self.assertEqual(rows[0]["source_kind"], "STATUS_v2")

    def test_04_released_at_in_writer_leases_denies_even_when_leases_active(self):
        reg = base(writer_leases=[{"holder": f"Coder {G4}",
                                   "released_at": CUTOFF}],
                   leases=[{"holder": f"Coder {G4}", "verified": True}])
        self.assertEqual(eligibility_reason(reg, G4), "lease_released")
        move = record()
        move["to"]["id8"] = G4
        ok, bad, _ = next_move.validate_records(reg, {FIRST + ".json": move}, [], {}, NOW)
        self.assertEqual(ok, [])
        self.assertTrue(any("recipient_lease_released" in r["reasons"] for r in bad))

    def test_05_released_state_in_leases_denies_despite_unreleased_writer_lease(self):
        reg = base(writer_leases=[{"holder": f"Coder {G4}", "verified": True}],
                   leases=[{"holder": f"Coder {G4}", "state": " RELEASED "}])
        self.assertEqual(eligibility_reason(reg, G4), "lease_released")

    def test_06_status_bar_fails_closed_on_released_at_even_with_two_lists(self):
        reg = base(
            agents=[{"chat_id8": G4, "status": "active", "role": "coder",
                     "observation": {"state": "WORKING", "reachable": True,
                                     "observed_at": "2026-10-18T04:59:00Z"}}],
            writer_leases=[{"holder": f"Coder {G4}", "verified": True}],
            leases=[{"holder": f"Coder {G4}", "released_at": CUTOFF}])
        instance = status_bar.normalize_roster(reg)[0]
        outcome = status_bar.derive_status(instance, reg, {"next_move": {
            "evaluator_at": "2026-10-18T04:59:00Z"}}, NOW)
        self.assertEqual(outcome["dimensions"]["execution_authority"]["reason"],
                         "writer_lease_released")
        self.assertEqual(outcome["light"], "red")

    def test_07_claim_denies_released_at_in_writer_leases_before_mutation(self):
        reg = register()
        reg["writer_leases"] = [{"holder": f"Coder {TO['id8']}",
                                 "released_at": "2026-10-16T13:00:00Z"}]
        reg["leases"] = [{"holder": f"Coder {TO['id8']}", "verified": True}]
        api = FakeTransport(registry=reg)
        with self.assertRaisesRegex(next_move_claim.ClaimRefused,
                                    "recipient_lease_released"):
            next_move_claim.make_claim(api, "main", FIRST, REGSHA, TO, now=NOW)
        self.assertEqual(api.sent, [])

    def test_08_retired_boolean_alone_blocks_and_marks_report(self):
        reg = base(agents=[{"chat_id8": G4, "status": "active",
                            "retired": True, "retired_at": CUTOFF,
                            "evidence_thread": f"https://github.com/{REPO}/issues/64"}])
        self.assertEqual(eligibility_reason(reg, G4), "retired")
        with tempfile.TemporaryDirectory() as temp:
            projection, _ = build_project_data(
                Path(temp), "landing-live", reg, signal(CLAIM),
                [], None, source_meta={"status": "ok", "errors": []}, now=NOW)
        agent = next(x for x in projection["agents"] if x["chat_id8"] == G4)
        rows = [x for x in agent["evidence"] if x["type"] == "evidence"]
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["eligibility"], "INELIGIBLE")

    def test_09_real_format_registry_historical_evidence_remains_eligible(self):
        reg = json.loads((ROOT / "logs" / "landing-live" / "registry.json").read_text())
        # Copy a real registered g1 entry (retired=true is absent, status is text).
        g1 = next(x for x in reg["agents"] if x["chat_id8"] == G1)
        self.assertTrue(str(g1["status"]).strip().casefold().startswith("retired"))
        # N1: main may already include the reviewed #98 field; test *behavior*
        # with an explicit copy-only cutoff, never absence in the live registry.
        g1["retired_at"] = "2026-10-16T03:55:25Z"  # #1/6207717760
        before = ("TASK EVIDENCE v2 · landing-live · implementer · "
                  f"chat {G1} · #1 · 15 Oct 14:47 +04\n"
                  "Task: legitimate historical WP0\nStatus: DONE")
        after = ("TASK EVIDENCE v2 · landing-live · implementer · "
                 f"chat {G1} · #99 · 16 Oct 09:00 +04\n"
                 "Task: synthetic unauthorized return\nStatus: DONE")
        threads = {22: {"number": 22, "repository": REPO, "comments": [
            {"id": 990005003, "created_at": "2026-10-15T10:47:00Z", "body": before},
            {"id": 990005004, "created_at": "2026-10-16T05:00:00Z", "body": after}]}}
        with tempfile.TemporaryDirectory() as temp:
            projection, _ = build_project_data(
                Path(temp), "landing-live", reg, threads,
                [], None, source_meta={"status": "ok", "errors": []}, now=NOW)
        agent = next(a for a in projection["agents"] if a["chat_id8"] == G1)
        rows = [e for e in agent["evidence"] if e["type"] == "evidence"]
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["eligibility"], "ELIGIBLE")
        self.assertTrue(rows[0]["counts_for_go"])
        self.assertEqual(rows[1]["eligibility"], "INELIGIBLE")
        self.assertFalse(rows[1]["counts_for_go"])
        recs = return_recommendations(reg, threads)
        self.assertEqual([r["source"] for r in recs],
                         [f"https://github.com/{REPO}/issues/22#issuecomment-990005004"])


    def test_10_status_bar_checks_released_legacy_lease_when_writer_list_unrelated(self):
        reg = base(
            agents=[{"chat_id8": G4, "status": "active", "role": "coder"}],
            writer_leases=[{"holder": "Coder 11111111", "verified": True}],
            leases=[{"holder": f"Coder {G4}", "state": "ReLeAsEd"}])
        outcome = status_bar.derive_status(
            status_bar.normalize_roster(reg)[0], reg,
            {"next_move": {"evaluator_at": "2026-10-18T04:59:00Z"}}, NOW)
        self.assertEqual(outcome["dimensions"]["execution_authority"]["state"],
                         "blocked")
        self.assertEqual(outcome["dimensions"]["execution_authority"]["reason"],
                         "writer_lease_released")


    def test_11_all_three_real_format_entries_keep_precutoff_evidence_eligible(self):
        # #98 registry source declarations: exact GitHub publication times,
        # not independently proven private chat-exhaustion instants.
        # The registry input is read only, and EVERY cutoff is overridden on
        # an in-memory copy, so this test runs before AND after PR #98 merges.
        cutoffs = {
            G1: ("2026-10-16T03:55:25Z", 22, "2026-10-15T10:47:00Z",
                 "https://github.com/reallakshman19/CoordinatorLandingpage/"
                 "issues/1#issuecomment-6207717760"),
            "6ad1a045": ("2026-10-16T23:39:52Z", 22, "2026-10-16T10:32:00Z",
                         "https://github.com/reallakshman19/CoordinatorLandingpage/"
                         "issues/22#issuecomment-6226735852"),
            G4: ("2026-10-17T23:33:54Z", 64, "2026-10-17T23:20:00Z",
                 "https://github.com/reallakshman19/CoordinatorLandingpage/"
                 "issues/1#issuecomment-6243133548"),
        }
        live = ROOT / "logs" / "landing-live" / "registry.json"
        before = live.read_bytes()
        reg = json.loads(before)
        threads = {22: {"number": 22, "repository": REPO, "comments": []},
                   64: {"number": 64, "repository": REPO, "comments": []}}
        for ordinal, (chat, (cutoff, issue, evidence_at, source)) in enumerate(
                cutoffs.items(), start=1):
            agent = next(a for a in reg["agents"] if a["chat_id8"] == chat)
            self.assertTrue(str(agent["status"]).strip().casefold().startswith("retired"))
            # If #98 has already landed, its actual fields must match the
            # independently pinned source values. If not, tests still run
            # against an exact copy of the planned #98 cutoff.
            if agent.get("retired_at") is not None:
                self.assertEqual(agent["retired_at"], cutoff)
                self.assertEqual(agent["retired_at_source"], source)
                self.assertIn("declaration comment created_at",
                              agent["retired_at_basis"])
            agent["retired_at"] = cutoff
            agent["retired_at_source"] = source
            body = ("TASK EVIDENCE v2 · landing-live · implementer · "
                    f"chat {chat} · #{ordinal} · historical\n"
                    "Task: synthetic legitimate pre-retirement record\n"
                    "Status: DONE")
            threads[issue]["comments"].append({
                "id": 990005100 + ordinal, "created_at": evidence_at,
                "body": body,
            })
        with tempfile.TemporaryDirectory() as tmp:
            projection, _ = build_project_data(
                Path(tmp), "landing-live", reg, threads, [], None,
                source_meta={"status": "ok", "errors": []}, now=NOW)
        for chat in cutoffs:
            agent = next(a for a in projection["agents"] if a["chat_id8"] == chat)
            reports = [x for x in agent["evidence"] if x["type"] == "evidence"]
            self.assertEqual(len(reports), 1, chat)
            self.assertEqual(reports[0]["eligibility"], "ELIGIBLE", chat)
            self.assertTrue(reports[0]["counts_for_go"], chat)
        self.assertEqual(return_recommendations(reg, threads), [],
                         "Historical comments must not trigger return blocks")
        self.assertEqual(live.read_bytes(), before,
                         "PR #98's live registry must never be mutated")


if __name__ == "__main__":
    unittest.main(verbosity=2)
