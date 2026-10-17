"""WP-L2(d): source-linked G8 disagreement and non-destructive fetch errors."""
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build_data
import fetch_live_data
from landing_build import disagreement

REPO = "reallakshman19/CoordinatorLandingpage"
PRODUCT = "reallakshman19/Common"
PR = f"https://github.com/{PRODUCT}/pull/91"
STATUS_URL = f"https://github.com/{PRODUCT}/issues/80"
NOW = datetime(2026, 10, 18, tzinfo=timezone.utc)


def status_issue(word, previous="STATE: IN PROGRESS"):
    return {"number": 80, "repository": PRODUCT, "body": previous,
            "comments": [{"id": 12, "created_at": "2026-10-17T10:00:00Z",
                          "body": f"STATE: {word}"}]}


def pr_snapshot(state="open", merged=None, url=PR):
    return [{"url": url, "repository": PRODUCT, "head": "a" * 40,
             "state": state, "merged_at": merged}]


def project(word, prs):
    registry = {"project": "case", "repository": PRODUCT, "agents": [],
                "status_issue": STATUS_URL,
                "status_comment": STATUS_URL + "#issuecomment-12",
                "control": {"epoch": 1},
                "workflow": {}, "open_owner_decisions": []}
    status = status_issue(word)
    return build_data.build_project_data(
        ROOT, "case", registry, {80: status}, [], None,
        source_meta={"status": "ok", "errors": []},
        status_thread=status, now=NOW, pr_observation=prs)[0]


class G8DisagreementTests(unittest.TestCase):
    def test_01_latest_done_vs_open_pr_flags_both_sources(self):
        out = project("DONE", pr_snapshot("open"))
        item = out["status_merge_disagreement"]
        self.assertEqual(item["status"], "DISAGREEMENT")
        self.assertTrue(item["flag"])
        self.assertEqual(item["issue_status"], "DONE")
        self.assertEqual(item["issue_url"], STATUS_URL + "#issuecomment-12")
        self.assertEqual(item["prs"][0]["pr_status"], "OPEN")
        self.assertEqual(item["prs"][0]["url"], PR)
        self.assertEqual(item["prs"][0]["comparison"], "CONTRADICTION")

    def test_02_hold_and_in_progress_contradict_merged(self):
        for word in ("HOLD", "BLOCKED", "IN PROGRESS"):
            with self.subTest(word=word):
                out = project(word, pr_snapshot("closed", "2026-10-17T11:00:00Z"))
                result = out["status_merge_disagreement"]
                self.assertEqual(result["status"], "DISAGREEMENT")
                self.assertEqual(result["prs"][0]["pr_status"], "MERGED")

    def test_03_no_linked_pr_means_no_flag_not_agreement(self):
        out = project("DONE", [])
        self.assertNotIn("status_merge_disagreement", out)

    def test_04_unknown_status_means_unknown_not_a_disagreement(self):
        out = project("WAITING REVIEW", pr_snapshot("open"))
        result = out["status_merge_disagreement"]
        self.assertEqual(result["status"], "UNKNOWN")
        self.assertFalse(result["flag"])
        self.assertIsNone(result["issue_status"])

    def test_05_closed_unmerged_is_not_merged(self):
        result = project("DONE", pr_snapshot("closed", None))["status_merge_disagreement"]
        self.assertEqual(result["status"], "DISAGREEMENT")
        self.assertEqual(result["prs"][0]["pr_status"], "CLOSED_UNMERGED")
        self.assertNotEqual(result["prs"][0]["pr_status"], "MERGED")

    def test_06_foreign_repo_pr_is_ignored(self):
        foreign = pr_snapshot("open", url="https://github.com/other/repo/pull/91")
        out = project("DONE", foreign)
        self.assertNotIn("status_merge_disagreement", out)

    def test_07_done_and_merged_not_falsely_flagged(self):
        result = project("DONE", pr_snapshot("closed", "2026-10-17T11:00:00Z"))
        self.assertEqual(result["status_merge_disagreement"]["status"], "NO_DISAGREEMENT")
        self.assertFalse(result["status_merge_disagreement"]["flag"])

    def test_08_fetched_pr_snapshot_keeps_state_without_extra_get(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            registry = {"project": "case", "repository": PRODUCT, "agents": [],
                        "status_issue": STATUS_URL,
                        "evidence": {"pr_url": PR, "head": "a" * 40}}
            p = root / "logs" / "case" / "registry.json"
            p.parent.mkdir(parents=True)
            p.write_text(json.dumps(registry))
            requests = []
            def api(endpoint):
                requests.append(endpoint)
                if endpoint.endswith("/pulls/91"):
                    return {"number": 91, "state": "closed",
                            "merged_at": "2026-10-17T11:00:00Z",
                            "head": {"sha": "a" * 40}}
                return None
            with mock.patch.object(fetch_live_data, "gh_api", side_effect=api):
                fetch_live_data.capture_project_extras(
                    root, root / "cache", {"case": {"repository": PRODUCT}},
                    [], control_repo=REPO)
            self.assertEqual(requests.count(f"/repos/{PRODUCT}/pulls/91"), 1)
            records = json.loads((root / "cache" / "project-extras" /
                                  "case" / "pr-heads.json").read_text())
            self.assertEqual(records[0]["state"], "closed")
            self.assertEqual(records[0]["merged_at"], "2026-10-17T11:00:00Z")

    def test_09_http_404_403_and_transport_failures_report_reasons(self):
        for stderr, expected in (("HTTP 404: Not Found", "HTTP_404"),
                                 ("HTTP 403: forbidden", "HTTP_403")):
            with self.subTest(expected=expected):
                errors = []
                exception = subprocess.CalledProcessError(
                    1, ["gh", "api"], stderr=stderr)
                with mock.patch.object(fetch_live_data.subprocess, "run",
                                       side_effect=exception):
                    self.assertIsNone(fetch_live_data.gh_api(
                        f"/repos/{PRODUCT}/issues/999", errors=errors))
                self.assertTrue(any(expected in err for err in errors), errors)
        errors = []
        with mock.patch.object(fetch_live_data.subprocess, "run",
                               side_effect=OSError("network unavailable")):
            self.assertIsNone(fetch_live_data.gh_api(
                f"/repos/{PRODUCT}/issues/999", errors=errors))
        self.assertTrue(any("TRANSPORT_ERROR" in err for err in errors), errors)

    def test_10_lineage_inaccessible_has_http_reason(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            p = root / "logs" / "case" / "registry.json"
            p.parent.mkdir(parents=True)
            p.write_text(json.dumps({"project": "case", "repository": PRODUCT,
                                      "parent_issue": STATUS_URL}))
            error = subprocess.CalledProcessError(
                1, ["gh", "api"], stderr="HTTP 403: denied")
            with mock.patch.object(fetch_live_data.subprocess, "run",
                                   side_effect=error):
                errors = []
                fetch_live_data.capture_project_extras(
                    root, root / "cache", {"case": {"repository": PRODUCT}},
                    errors, control_repo=REPO)
            data = json.loads((root / "cache" / "project-extras" /
                               "case" / "lineage.json").read_text())
            self.assertEqual(data[0]["status"], "INACCESSIBLE")
            self.assertEqual(data[0]["reason"], "HTTP_403")
            self.assertTrue(any("HTTP_403" in err for err in errors))


    def test_11_registered_status_comment_beats_newer_unrelated_quote(self):
        registry = {"repository": PRODUCT, "status_issue": STATUS_URL,
                    "status_comment": STATUS_URL + "#issuecomment-12"}
        issue = {"number": 80, "repository": PRODUCT,
                 "body": "STATE: IN PROGRESS",
                 "comments": [
                     {"id": 12, "created_at": "2026-10-17T09:00:00Z",
                      "body": "STATE: HOLD"},
                     {"id": 13, "created_at": "2026-10-17T11:00:00Z",
                      "body": "Quotation from another actor:\nSTATE: DONE"}]}
        result = disagreement.latest_issue_status(registry, issue, REPO)
        self.assertEqual(result["word"], "HOLD")
        self.assertEqual(result["url"], STATUS_URL + "#issuecomment-12")

    def test_12_last_state_line_wins_within_registered_comment(self):
        registry = {"repository": PRODUCT,
                    "status_comment": STATUS_URL + "#issuecomment-12"}
        issue = {"number": 80, "repository": PRODUCT,
                 "comments": [{"id": 12, "created_at": "2026-10-17T09:00:00Z",
                               "body": "Earlier:\nSTATE: HOLD\nReconciled:\nSTATE: DONE"}]}
        result = disagreement.latest_issue_status(registry, issue, REPO)
        self.assertEqual(result["word"], "DONE")
        self.assertEqual(result["url"], STATUS_URL + "#issuecomment-12")

    def test_13_registered_issue_body_beats_unrelated_comment(self):
        registry = {"repository": PRODUCT, "status_issue": STATUS_URL}
        issue = {"number": 80, "repository": PRODUCT,
                 "body": "Recorded source:\nSTATE: BLOCKED",
                 "comments": [{"id": 13, "created_at": "2026-10-17T11:00:00Z",
                               "body": "Quoted old text:\nSTATE: DONE"}]}
        result = disagreement.latest_issue_status(registry, issue, REPO)
        self.assertEqual(result["word"], "BLOCKED")
        self.assertEqual(result["url"], STATUS_URL)

    def test_14_fallback_newest_only_when_no_registered_source(self):
        registry = {"repository": PRODUCT}
        issue = {"number": 80, "repository": PRODUCT, "html_url": STATUS_URL,
                 "body": "No status here",
                 "comments": [
                     {"id": 12, "created_at": "2026-10-17T09:00:00Z",
                      "body": "STATE: DONE"},
                     {"id": 13, "created_at": "2026-10-17T11:00:00Z",
                      "body": "STATE: HOLD\nSTATE: IN PROGRESS"}]}
        result = disagreement.latest_issue_status(registry, issue, REPO)
        self.assertEqual(result["word"], "IN PROGRESS")
        self.assertEqual(result["url"], STATUS_URL + "#issuecomment-13")

    def test_15_missing_registered_comment_not_replaced_by_quote(self):
        registry = {"repository": PRODUCT,
                    "status_comment": STATUS_URL + "#issuecomment-999"}
        issue = {"number": 80, "repository": PRODUCT,
                 "body": "STATE: HOLD",
                 "comments": [{"id": 13, "created_at": "2026-10-17T11:00:00Z",
                               "body": "STATE: DONE"}]}
        self.assertIsNone(disagreement.latest_issue_status(registry, issue, REPO))


if __name__ == "__main__":
    unittest.main(verbosity=2)
