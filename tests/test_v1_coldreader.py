"""WP-V1 cold-reader RED: bounded captured parent intent and #1 amendments."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from landing_build.lineage import finish_lineage
from landing_build.project_intent import project_intake
from landing_build.project_data import build_project_data
from build_data import build_all

REPO = "reallakshman19/CoordinatorLandingpage"
PARENT = f"https://github.com/{REPO}/issues/21"
INBOX = f"https://github.com/{REPO}/issues/1"
REG = {"project": "landing-live", "repository": REPO, "parent_issue": PARENT,
       "agents": [], "control": {"epoch": 1}, "workflow": {},
       "open_owner_decisions": []}


def parent(body):
    row = {"kind": "parent_issue", "reference": PARENT,
           "repository": REPO, "issue_number": 21, "status": "PENDING"}
    return finish_lineage(row, {
        "number": 21, "html_url": PARENT, "repository": REPO,
        "title": "Owner root intent", "body": body, "state": "open"})


def item(comment_id, body, association="MEMBER"):
    return {"id": comment_id, "body": body, "author_association": association,
            "created_at": "2026-10-18T01:00:00Z"}


class ColdReaderV1(unittest.TestCase):
    def test_parent_body_captured_bounded_and_marked_truncated(self):
        row = parent("Purpose: preserve exact Owner words. " + "A" * 4000)
        self.assertEqual(row["status"], "AVAILABLE")
        self.assertTrue(row["body_truncated"])
        self.assertLessEqual(len(row["body_excerpt"]), 1600)
        self.assertIn("Purpose:", row["body_excerpt"])
        self.assertEqual(row["url"], PARENT)

    def test_intent_and_amendments_are_source_bound_not_new_owner_approval(self):
        lineage = [parent("Owner aim: keep a truthful project dashboard.")]
        comments = [item(120, "landing-live correction: preserve source first."),
                    item(121, "For landing-live: superseded draft direction."),
                    item(122, "landing-live-other correction must not be shown."),
                    item(123, "Unrelated system correction.")]
        data = project_intake("landing-live", REG, lineage, comments, True, REPO)
        self.assertEqual(data["intent"]["status"], "AVAILABLE")
        self.assertIn("Owner aim", data["intent"]["text"])
        self.assertEqual(data["intent"]["source"], PARENT)
        amendments = data["amendments"]
        self.assertEqual(amendments["status"], "AVAILABLE")
        self.assertEqual([x["comment_id"] for x in amendments["records"]], [120, 121])
        self.assertEqual(amendments["records"][0]["source"], INBOX + "#issuecomment-120")
        self.assertTrue(amendments["records"][1]["superseded"])
        self.assertEqual(amendments["records"][0]["attribution"], "ASSOCIATED_NOT_OWNER_PROOF")

    def test_missing_inbox_is_unknown_with_reason_not_empty(self):
        r = project_intake("landing-live", REG, [parent("real aim")], [], False, REPO)
        self.assertEqual(r["amendments"]["status"], "UNKNOWN")
        self.assertEqual(r["amendments"]["reason"], "inbox_1_not_fetched")
        self.assertEqual(r["amendments"]["records"], [])

    def test_missing_body_unknown_even_if_parent_link_is_available(self):
        old = {"kind": "parent_issue", "reference": PARENT,
               "url": PARENT, "status": "AVAILABLE", "title": "Title only"}
        data = project_intake("landing-live", REG, [old], [], True, REPO)
        self.assertEqual(data["intent"]["status"], "UNKNOWN")
        self.assertEqual(data["intent"]["reason"], "parent_body_not_captured")
        self.assertEqual(data["amendments"]["status"], "NONE_FOUND")

    def test_foreign_parent_row_is_never_used_as_intent(self):
        row = parent("Do not admit this mismatched source")
        row["url"] = "https://github.com/outsider/other/issues/21"
        result = project_intake("landing-live", REG, [row], [], False, REPO)
        self.assertEqual(result["intent"]["status"], "UNKNOWN")

    def test_amendment_cap_reports_truncation_not_silent_loss(self):
        rows = [item(i+100, "landing-live Owner correction " + str(i))
                for i in range(36)]
        result = project_intake("landing-live", REG, [parent("aim")], rows, True, REPO)
        a = result["amendments"]
        self.assertTrue(a["truncated"])
        self.assertEqual(a["total_matching"], 36)
        self.assertEqual(len(a["records"]), 25)
        self.assertEqual(a["records"][0]["comment_id"], 111)
        self.assertEqual(a["records"][-1]["comment_id"], 135)

    def test_retired_and_unverified_warning_both_counted(self):
        registry = {**REG, "agents": [{"role": "coder", "generation": 1,
            "chat_id8": "1234abcd", "status": "retired"}],
            "leases": [
              {"holder": "Coder 1234abcd"},
              {"holder": "unknown actor"},
              {"holder": "Coder 1234abcd"},
              {"holder": "Coder deadbeef"},
            ]}
        data, _ = build_project_data(
            ROOT, "landing-live", registry, {}, [], None,
            now=__import__("datetime").datetime(2026, 10, 18,
                tzinfo=__import__("datetime").timezone.utc))
        warnings = [x["warning"] for x in data["leases"] if x.get("warning")]
        self.assertEqual(warnings.count("RETIRED_HOLDER"), 2)
        self.assertEqual(warnings.count("UNVERIFIED_HOLDER"), 1)
        self.assertEqual(data["stale_lease_count"], 3)
        self.assertEqual(data["stale_lease_count"], len(warnings))

    def test_live_build_reuses_cache_and_preserves_benchmark_separation(self):
        with tempfile.TemporaryDirectory() as temp, mock.patch(
            "owner_json.github_provenance",
            return_value={"sha":None, "author":None, "association":"UNKNOWN"}
        ), mock.patch("owner_json.subprocess.run",
                      side_effect=AssertionError("network attempted")):
            root, cache, output = Path(temp), Path(temp)/"cache", Path(temp)/"out"
            reg = root / "logs" / "landing-live" / "registry.json"
            reg.parent.mkdir(parents=True)
            reg.write_text(json.dumps(REG))
            extra = cache / "project-extras" / "landing-live"
            extra.mkdir(parents=True)
            (extra/"lineage.json").write_text(json.dumps([parent("Aim from fetched #21.")]))
            (cache/"inbox-1.json").write_text(json.dumps([
                item(331, "landing-live Owner amendment: keep prior rationale.")]))
            build_all(root, output, cache_dir=cache)
            summary = json.loads((output/"projects.json").read_text())[0]
            detail = json.loads((output/"project-landing-live.json").read_text())
            self.assertEqual(summary["intent"], detail["intent"])
            self.assertEqual(summary["amendments"], detail["amendments"])
            self.assertIn("Aim from fetched", summary["intent"]["text"])
            self.assertEqual(summary["amendments"]["records"][0]["comment_id"], 331)
            # Absent #1 is not a confirmed empty amendment set.
            (cache/"inbox-1.json").unlink()
            build_all(root, output, cache_dir=cache)
            detail = json.loads((output/"project-landing-live.json").read_text())
            self.assertEqual(detail["amendments"]["status"], "UNKNOWN")


if __name__ == "__main__":
    unittest.main(verbosity=2)
