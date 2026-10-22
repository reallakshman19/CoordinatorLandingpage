"""Stage 1 portable Progress data contract tests (all invented fixtures)."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CHECKER = os.environ.get("PROGRESS_CHECKER", str(REPO / "scripts/check_progress_data.py"))
SECTIONS = ("repository", "issues", "pullRequests", "roadmap", "highRoi",
            "future", "intent", "inputs", "knownIssues", "pending")


class ProgressDataTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name) / "progress-data"
        shutil.copytree(REPO / "site/progress-data/schema", self.root / "schema")
        self.files = {
            "projects": self.root / "projects.json",
            "index": self.root / "demo/index.json",
            "meta": self.root / "demo/one/meta.json",
            "stages": self.root / "demo/one/stages.json",
            "actions": self.root / "demo/one/actions.json",
            "fixtures": self.root / "demo/one/fixtures.json",
        }
        self.data = {
            "projects": {"schema": 2, "projects": [
                {"key": "demo", "label": "Demo", "visibility": "public",
                 "replyTo": {"kind": "none"}}]},
            "index": {"schema": 2, "project": {
                "key": "demo", "title": "Demo", "updatedAt": "2026-10-21T10:00:00Z",
                "updatedBy": "Agent", "staleAfterMin": 120},
                "chats": {"p": {"label": "Coder", "id8": "1234abcd"}},
                "topics": [{"key": "one", "label": "One"}]},
            "meta": {"title": "One", "milestones": {
                "M0": {"order": 0, "name": "Start", "full": "Start"}},
                "lanes": {"L": {"order": 0, "title": "Build"}}},
            "stages": {"S1": {"order": 0, "lane": "L", "milestone": "M0",
                              "name": "Start", "state": "NOT_STARTED", "actor": "-",
                              "chats": ["p"]}},
            "actions": {"D1": {"order": 1, "status": "open", "title": "Choose",
                               "stages": ["S1"], "options": [
                                   {"key": "A", "label": "A", "suggested": True,
                                    "body": "Take A", "reply": "A", "short": "A"}]}},
            "fixtures": {name: [] for name in SECTIONS},
        }
        self.write()

    def write(self):
        for name, path in self.files.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(self.data[name], indent=2) + "\n", encoding="utf-8")

    def run_check(self, *args):
        return subprocess.run(
            [sys.executable, CHECKER, "--data", str(self.root), *args],
            cwd=REPO, capture_output=True, text=True, check=False)

    def assert_rejected(self, hint):
        self.write()
        result = self.run_check()
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn(hint, result.stdout + result.stderr)

    def test_clean_synthetic_tree_passes(self):
        r = self.run_check()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("progress-data OK", r.stdout)

    def test_live_tree_passes(self):
        r = subprocess.run([sys.executable, CHECKER], cwd=REPO,
                           capture_output=True, text=True, check=False)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("progress-data OK", r.stdout)

    def test_bad_state(self):
        self.data["stages"]["S1"]["state"] = "UNPROVEN"
        self.assert_rejected("schema stages:")

    def test_bad_actor(self):
        self.data["stages"]["S1"]["actor"] = "WIZARD"
        self.assert_rejected("schema stages:")

    def test_unknown_milestone(self):
        self.data["stages"]["S1"]["milestone"] = "M404"
        self.assert_rejected("unknown milestone")

    def test_unknown_lane(self):
        self.data["stages"]["S1"]["lane"] = "missing"
        self.assert_rejected("unknown lane")

    def test_chat_not_in_index(self):
        self.data["stages"]["S1"]["chats"] = ["absent"]
        self.assert_rejected("chat key 'absent' not in index")

    def test_open_card_without_suggested(self):
        self.data["actions"]["D1"]["options"][0]["suggested"] = False
        self.assert_rejected("open card needs exactly one suggested option")

    def test_http_link(self):
        self.data["stages"]["S1"]["refs"] = [{"l": "bad", "u": "http://example.test/"}]
        self.assert_rejected("link must start with https://")

    def test_public_chatgpt_link(self):
        self.data["index"]["chats"]["p"]["url"] = "https://chatgpt.com/c/not-real"
        self.assert_rejected("ChatGPT chat link")

    def test_drive_link(self):
        self.data["fixtures"]["repository"] = [
            {"t": "forbidden", "u": "https://drive.google.com/file/not-real"}]
        self.assert_rejected("Google Drive link")

    def test_bad_id8(self):
        self.data["index"]["chats"]["p"]["id8"] = "bad"
        self.assert_rejected("id8 must be 8 hex characters")

    def test_wrong_schema_type(self):
        self.data["index"]["topics"] = "not an array"
        self.assert_rejected("schema index: $.topics: expected array")

    def test_unsupported_schema_keyword(self):
        self.write()
        file = self.root / "schema/stages.schema.json"
        schema = json.loads(file.read_text(encoding="utf-8"))
        schema["mysteryKeyword"] = True
        file.write_text(json.dumps(schema, indent=2) + "\n", encoding="utf-8")
        r = self.run_check()
        self.assertNotEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("unsupported schema keyword 'mysteryKeyword'", r.stdout)

    def test_duplicate_topic_key(self):
        self.data["index"]["topics"].append({"key": "one", "label": "Duplicate"})
        self.assert_rejected("duplicate topic key")

    def test_done_card_without_answer_ref(self):
        card = self.data["actions"]["D1"]
        card["status"] = "done"
        card["answer"] = {"text": "A", "at": "2026-10-21T12:00:00Z"}
        self.assert_rejected("done card needs answer.ref")

    def test_private_chat_allowed(self):
        self.data["index"]["chats"]["p"]["url"] = "https://chatgpt.com/c/synthetic"
        self.write()
        result = self.run_check("--private")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.data["projects"]["projects"][0]["visibility"] = "private"
        self.write()
        result = self.run_check()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_private_drive_still_rejected(self):
        self.data["fixtures"]["issues"] = [
            {"t": "no", "u": "https://drive.google.com/fake"}]
        self.write()
        r = self.run_check("--private")
        self.assertNotEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("Google Drive link", r.stdout)


if __name__ == "__main__":
    unittest.main()
