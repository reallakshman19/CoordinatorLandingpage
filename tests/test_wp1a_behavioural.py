#!/usr/bin/env python3
"""F3/F6 behavioural controls: old and new scripts share the called API surface.

Assertions intentionally target wrong output or stale side effects on base.
No new-only function calls or keyword arguments appear in this module.
"""
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

FIXTURE = ROOT / "tests" / "fixtures" / "f3_successor_collision.json"
CONTROL_REPO = "reallakshman19/CoordinatorLandingpage"


class BaseCompatibleBehaviouralControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.f3 = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def project(self):
        reg = json.loads(json.dumps(self.f3["registry"]))
        threads = {int(n): data for n, data in self.f3["threads"].items()}
        # EXACT five-positional-argument base-compatible API.
        return build_data.build_project_data(
            ROOT, "imo-ab-test", reg, threads, self.f3["inbox"], None
        )

    def fetch_with(self, cache, root, fake_issue):
        with mock.patch.object(fetch_live_data, "fetch_issue", side_effect=fake_issue), \
             mock.patch.object(sys, "argv", [
                 "fetch_live_data.py", "--root", str(root),
                 "--repo", CONTROL_REPO, "--cache-dir", str(cache)
             ]):
            fetch_live_data.main()

    def registry_root(self, root):
        rpath = root / "logs" / "imo-ab-test" / "registry.json"
        rpath.parent.mkdir(parents=True)
        rpath.write_text(json.dumps(self.f3["registry"]), encoding="utf-8")

    def test_f3_old_proof_never_attaches_to_successor(self):
        project, _ = self.project()
        agents = {a["chat_id8"]: a for a in project["agents"]}
        g1 = [e["chat_id8"] for e in agents["a1111111"]["evidence"]
              if e["type"] == "evidence"]
        g2 = [e["chat_id8"] for e in agents["b2222222"]["evidence"]
              if e["type"] == "evidence"]
        self.assertEqual(g1, ["a1111111"])
        self.assertEqual(g2, ["b2222222"])

    def test_f3_retired_holder_leases_are_not_green(self):
        project, _ = self.project()
        self.assertEqual(project.get("stale_lease_count"), 5)
        self.assertEqual([lease.get("warning") for lease in project["leases"]],
                         ["RETIRED_HOLDER"] * 5)
        self.assertEqual([lease.get("valid_for_active_agent")
                          for lease in project["leases"]], [False] * 5)

    def test_f3_foreign_issue_and_project_never_appear_in_timeline(self):
        _, timeline = self.project()
        task_names = [e["task"] for e in timeline
                      if e.get("type") == "TASK_EVIDENCE"]
        self.assertEqual(task_names,
                         ["SYNTH-OLD historical report",
                          "SYNTH-NEW successor report"])
        self.assertEqual([e["project"] for e in timeline],
                         ["imo-ab-test"] * len(timeline))

    def test_f3_inbox_is_exact_issue_one_not_issue_twelve(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.registry_root(root)
            cache = root / "cache"
            def fake_issue(repo, number):
                self.assertEqual(repo, CONTROL_REPO)
                return {"number": number, "comments": [
                    {"id": number, "body": f"issue-{number}-synthetic"}
                ]}
            self.fetch_with(cache, root, fake_issue)
            inbox = json.loads((cache / "inbox-1.json").read_text())
            self.assertEqual(inbox, [{"id": 1, "body": "issue-1-synthetic"}])

    def test_f6_failed_inbox_fetch_removes_old_cache(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.registry_root(root)
            cache = root / "cache"
            (cache / "threads").mkdir(parents=True)
            (cache / "inbox-1.json").write_text('[{"body":"stale-success"}]')
            (cache / "threads" / "issue-1.json").write_text('{"number":1}')
            def fake_issue(repo, number):
                if number == 1:
                    return None
                return {"number": number, "comments": []}
            self.fetch_with(cache, root, fake_issue)
            self.assertFalse((cache / "inbox-1.json").exists(),
                             "failed #1 fetch cannot appear as successful inbox")
            self.assertFalse((cache / "threads" / "issue-1.json").exists(),
                             "old successful #1 thread must be purged")

    def test_f6_missing_capture_must_be_explicitly_unknown(self):
        project, _ = self.project()
        self.assertEqual(project.get("freshness_status"), "UNKNOWN",
                         "missing observation must not imply running")
        self.assertEqual(project.get("source_health"), {
            "status": "unknown", "errors": ["capture_manifest_missing"],
        })

    def test_f6_publication_is_not_inferred_from_local_build(self):
        project, _ = self.project()
        self.assertIsNone(project.get("published_at", "ABSENT"),
                          "publisher timestamp must be explicit null, not absent")
        self.assertEqual(project.get("schema_version"), "wp1a.1")


if __name__ == "__main__":
    unittest.main(verbosity=2)
