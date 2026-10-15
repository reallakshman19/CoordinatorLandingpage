#!/usr/bin/env python3
"""F5 WP1b: stable behavioural projection assertions and detailed state gates.

Base red uses ONLY the pre-WP1b build_all API; failures are AssertionError
on observable missing/incorrect output, never absent signatures.
"""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build_data
import fetch_live_data

F5 = json.loads((ROOT / "tests/fixtures/f5_owner_input_history.json").read_text())
F3 = json.loads((ROOT / "tests/fixtures/f3_successor_collision.json").read_text())


def fixture_build(root, fixture=None):
    fixture = fixture or F5
    registry = root / "logs/imo-ab-test/registry.json"
    registry.parent.mkdir(parents=True)
    original = json.dumps(F3["registry"], sort_keys=True).encode()
    registry.write_bytes(original)
    cache = root / "cache"
    cache.mkdir()
    (cache / "capture-info.json").write_text(json.dumps(fixture["capture"]))
    (cache / "owner-inputs-source.json").write_text(
        json.dumps(fixture["issues"]))
    build_data.build_all(root, root / "output", cache_dir=cache)
    output = root / "output/owner-inputs.json"
    # This is a behavioural expectation of build_all's generated projection,
    # not a new helper/argument missing from the base.
    assert output.is_file(), "F5: build_all did not emit owner-inputs.json"
    assert registry.read_bytes() == original, "F5 build rewrote registry"
    return json.loads(output.read_text())


class BaseCompatibleF5(unittest.TestCase):
    def rows(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            # The original API call succeeds at base and head; the new
            # projection is the only differentiated observable behaviour.
            rows = fixture_build(root)
        return {row["number"]: row for row in rows}

    def test_f5_open_and_ack_are_different(self):
        r = self.rows()
        self.assertEqual((r[201]["status"], r[202]["status"]),
                         ("OPEN", "ACKNOWLEDGED"))

    def test_f5_clarification_and_exact_handled_receipt(self):
        r = self.rows()
        self.assertEqual(r[203]["status"], "NEEDS_CLARIFICATION")
        self.assertEqual(r[204]["status"], "HANDLED")
        self.assertEqual(r[204]["receipt"],
                         "https://github.com/reallakshman19/CoordinatorLandingpage/"
                         "issues/204#issuecomment-20401")

    def test_f5_closed_without_receipt_stays_unresolved(self):
        r = self.rows()
        self.assertEqual((r[205]["status"], r[205]["needs_you"],
                          r[205]["closed_without_receipt"]),
                         ("OPEN", True, True))
        self.assertEqual(r[214]["status"], "ACKNOWLEDGED")

    def test_f5_edit_and_reopen_never_reactivate_old_receipt(self):
        r = self.rows()
        self.assertEqual(r[206]["status"], "NEEDS_CLARIFICATION")
        self.assertIsNone(r[206]["receipt"])
        self.assertTrue(r[206]["fresh_receipt_required"])
        self.assertTrue(r[206]["needs_you"])

    def test_f5_duplicates_out_of_order_are_deterministic(self):
        r = self.rows()
        self.assertEqual(r[207]["status"], "HANDLED")
        self.assertEqual(r[207]["receipt"],
                         "https://github.com/reallakshman19/CoordinatorLandingpage/"
                         "issues/207#issuecomment-20702")

    def test_f5_checkbox_and_role_prefix_cannot_approve_protected_action(self):
        r = self.rows()
        self.assertTrue(r[208]["protected_action"])
        self.assertEqual(r[208]["authority"], "UNVERIFIED")
        self.assertFalse(r[208]["effective"])

    def test_f5_supersedes_marks_old_not_new(self):
        r = self.rows()
        self.assertEqual(r[209]["status"], "SUPERSEDED")
        self.assertEqual(r[209]["superseded_by"], 210)
        self.assertEqual(r[210]["status"], "ACKNOWLEDGED")
        self.assertEqual(r[210]["authority"], "UNVERIFIED")
        self.assertFalse(r[210]["effective"])

    def test_f5_sha_and_role_must_match_exactly(self):
        r = self.rows()
        self.assertEqual((r[210]["review"]["state"], r[210]["review"]["reason"]),
                         ("UNVERIFIED", "sha_mismatch"))
        self.assertEqual((r[211]["review"]["state"], r[211]["review"]["reason"]),
                         ("UNVERIFIED", "role_mismatch"))
        self.assertEqual(r[212]["review"]["state"], "MATCHED")
        self.assertEqual(r[212]["authority"], "UNVERIFIED")


class DetailedF5(unittest.TestCase):
    def test_f5_wrong_link_never_marks_handled(self):
        r = {x["number"]: x for x in
             build_data.build_owner_inputs(F5["issues"], F5["capture"])}
        self.assertEqual(r[213]["status"], "OPEN")
        self.assertIsNone(r[213]["receipt"])
        self.assertTrue(r[213]["closed_without_receipt"])

    def test_f5_inbox_one_missing_fails_closed(self):
        capture = copy.deepcopy(F5["capture"])
        capture["status"] = "degraded"
        capture["issues_fetched"].remove(1)
        capture["errors"] = ["issue_fetch_failed:1"]
        r = {x["number"]: x for x in
             build_data.build_owner_inputs(F5["issues"], capture)}
        self.assertEqual(r[204]["status"], "NEEDS_CLARIFICATION")
        self.assertEqual(r[207]["status"], "NEEDS_CLARIFICATION")
        self.assertIsNone(r[204]["receipt"])
        self.assertTrue(r[204]["needs_you"])
        self.assertEqual(r[204]["source_health"], "UNVERIFIED")

    def test_f5_future_receipt_cannot_survive_reopened_state(self):
        issue = copy.deepcopy(next(i for i in F5["issues"] if i["number"] == 206))
        issue["comments"].append({
            "id": 20603, "created_at": "2026-10-15T10:12:00Z",
            "body": "ACK: owner-input #206",
        })
        result = build_data.build_owner_inputs([issue], F5["capture"])
        self.assertEqual(result[0]["status"], "NEEDS_CLARIFICATION")
        self.assertTrue(result[0]["fresh_receipt_required"])

    def test_f5_duplicate_page_preserves_one_row(self):
        issues = F5["issues"] + [copy.deepcopy(F5["issues"][7])]
        rows = build_data.build_owner_inputs(issues, F5["capture"])
        self.assertEqual(len(rows), 15)
        self.assertEqual(len(set(r["number"] for r in rows)), len(rows))
        self.assertEqual([r["status"] for r in rows],
                         [F5["expected"][str(r["number"])] for r in rows])

    def test_f5_review_role_claim_is_not_owner_approval(self):
        rows = {r["number"]: r for r in
                build_data.build_owner_inputs(F5["issues"], F5["capture"])}
        self.assertEqual(rows[212]["review"]["state"], "MATCHED")
        self.assertEqual(rows[212]["authority"], "UNVERIFIED")
        self.assertFalse(rows[212]["effective"])

    def test_f5_fetch_missing_owner_index_is_visible_and_cache_purged(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            reg = root / "logs/imo-ab-test/registry.json"
            reg.parent.mkdir(parents=True)
            reg.write_text(json.dumps(F3["registry"]))
            cache = root / "cache"
            cache.mkdir()
            (cache / "owner-inputs-source.json").write_text('[{"number":999}]')
            def fake_api(path):
                if path.endswith("issues?state=all&labels=owner-input&per_page=100"):
                    return None
                return []
            def fake_issue(repo, number):
                return {"number": number, "comments": []}
            with mock.patch.object(fetch_live_data, "gh_api", side_effect=fake_api), \
                 mock.patch.object(fetch_live_data, "fetch_issue", side_effect=fake_issue), \
                 mock.patch.object(sys, "argv", [
                     "fetch_live_data.py", "--root", str(root),
                     "--repo", "reallakshman19/CoordinatorLandingpage",
                     "--cache-dir", str(cache)
                 ]):
                fetch_live_data.main()
            self.assertFalse((cache / "owner-inputs-source.json").exists())
            manifest = json.loads((cache / "capture-info.json").read_text())
            self.assertEqual(manifest["status"], "degraded")
            self.assertFalse(manifest["owner_inputs_complete"])
            self.assertIn("owner_input_index_failed", manifest["errors"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
