#!/usr/bin/env python3
"""WP1a F3/F6 red controls for G01/G03/G04/G10 only.

Generated fixtures are synthetic, sanitized and have no agent-chat data.
The fixture assertions are deliberately exact, not substring PASS oracles.
"""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock
from datetime import datetime, timezone, timedelta

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build_data
import fetch_live_data

FIXTURES = Path(__file__).parent / "fixtures"
CONTROL_REPO = "reallakshman19/CoordinatorLandingpage"


class WP1aNegativeControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.f3 = json.loads((FIXTURES / "f3_successor_collision.json").read_text())
        cls.f6 = json.loads((FIXTURES / "f6_freshness_failure.json").read_text())
        cls.now = datetime.fromisoformat(cls.f6["now"])

    def fixture_project(self, *, status=None, meta=None, registry=None):
        f = self.f3
        reg = registry or f["registry"]
        threads = {int(n): value for n, value in f["threads"].items()}
        return build_data.build_project_data(
            ROOT, "imo-ab-test", reg, threads, f["inbox"], None,
            source_meta=f["capture"] if meta is None else meta,
            status_thread=threads[12] if status is None else status,
            now=self.now, registry_blob_sha="b" * 40,
        )

    def test_f3_successor_cannot_inherit_g1_proof_or_unbound_verdict(self):
        project, events = self.fixture_project()
        agents = {a["chat_id8"]: a for a in project["agents"]}
        self.assertEqual(set(agents), {"a1111111", "b2222222"})
        self.assertEqual(agents["a1111111"]["status"], "retired")
        self.assertEqual(agents["b2222222"]["status"], "active")
        old_evidence = agents["a1111111"]["evidence"]
        new_evidence = agents["b2222222"]["evidence"]
        self.assertEqual([e["chat_id8"] for e in old_evidence if e["type"] == "evidence"],
                         ["a1111111"])
        self.assertEqual([e["chat_id8"] for e in new_evidence if e["type"] == "evidence"],
                         ["b2222222"])
        self.assertEqual([e for e in new_evidence if e["type"] == "verdict"], [])
        self.assertEqual(project["stale_lease_count"], 5)
        self.assertEqual([l["warning"] for l in project["leases"]],
                         ["RETIRED_HOLDER"] * 5)
        self.assertEqual([l["valid_for_active_agent"] for l in project["leases"]],
                         [False] * 5)
        self.assertEqual(project["registry"]["open_owner_decisions"], [])
        self.assertNotIn("AB-DISPATCH", json.dumps(project["registry"]["open_owner_decisions"]))
        self.assertEqual([e["chat_id8"] for e in events if e["type"] == "TASK_EVIDENCE"],
                         ["a1111111", "b2222222"])

    def test_f3_other_project_or_thread_does_not_bleed(self):
        _, timeline = self.fixture_project()
        self.assertEqual(
            [e["task"] for e in timeline if e.get("type") == "TASK_EVIDENCE"],
            ["SYNTH-OLD historical report", "SYNTH-NEW successor report"],
        )
        self.assertEqual([e["project"] for e in timeline], ["imo-ab-test"] * len(timeline))
        self.assertEqual(
            [e for e in timeline if e.get("_source") == "thread_99"], []
        )

    def test_f3_inbox_one_is_not_last_status(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            rpath = root / "logs" / "imo-ab-test" / "registry.json"
            rpath.parent.mkdir(parents=True)
            rpath.write_text(json.dumps(self.f3["registry"]), encoding="utf-8")
            numbers, statuses, errors = fetch_live_data.discover_sources(root, CONTROL_REPO)
            self.assertEqual(errors, [])
            self.assertEqual(numbers, {1, 12, 13})
            self.assertEqual(statuses, {"imo-ab-test": 12})
            cache = root / "cache"
            def fake_issue(repo, number):
                self.assertEqual(repo, CONTROL_REPO)
                return {"number": number, "repository": repo,
                        "comments": [{"id": number, "body": f"comment from #{number}"}]}
            with mock.patch.object(fetch_live_data, "fetch_issue", side_effect=fake_issue), \
             mock.patch.object(fetch_live_data, "gh_api", return_value=[]), \
                 mock.patch.object(sys, "argv", ["fetch_live_data.py",
                     "--root", str(root), "--repo", CONTROL_REPO,
                     "--cache-dir", str(cache)]):
                fetch_live_data.main()
            self.assertEqual(json.loads((cache / "inbox-1.json").read_text()),
                             [{"id": 1, "body": "comment from #1"}])
            self.assertEqual(json.loads((cache / "status-imo-ab-test.json").read_text())["number"], 12)
            self.assertEqual(json.loads((cache / "capture-info.json").read_text())["status"], "ok")

    def test_f3_rejects_wrong_repository_issue_pointer(self):
        self.assertIsNone(fetch_live_data.extract_issue_number(
            "https://github.com/foreign/repo/issues/13", CONTROL_REPO))
        self.assertEqual(fetch_live_data.extract_issue_number(
            "https://github.com/reallakshman19/CoordinatorLandingpage/issues/1",
            CONTROL_REPO), 1)

    def test_f6_exact_cycle_freshness_states(self):
        project, _ = self.fixture_project()
        self.assertEqual(project["freshness_status"], self.f6["expected"]["fresh_observed"])
        self.assertEqual(project["last_cycle_at"], "2026-10-15T10:45:00+00:00")
        self.assertIsNone(project["published_at"])
        def status(cycle, epoch=1):
            return {"comments": [{"author_association": "MEMBER", "body": (
                f"COORDINATOR EVIDENCE v1 · imo-ab-test · cycle 2 · epoch {epoch} · test\n"
                f"Coordinator last completed cycle: {cycle}"
            )}]}
        for cycle, expectation in (
            (self.f6["stale_cycle_at"], self.f6["expected"]["stale_31_min"]),
            (self.f6["fresh_cycle_at"], self.f6["expected"]["fresh_observed"]),
        ):
            with self.subTest(cycle=cycle):
                project, _ = self.fixture_project(status=status(cycle))
                self.assertEqual(project["freshness_status"], expectation)
        missing, _ = self.fixture_project(status={"comments": []})
        self.assertEqual(missing["freshness_status"], self.f6["expected"]["missing_cycle"])
        wrong, _ = self.fixture_project(
            status=status(self.f6["fresh_cycle_at"], self.f6["wrong_epoch"]))
        self.assertEqual(wrong["freshness_status"], self.f6["expected"]["wrong_epoch"])

    def test_f6_exact_30_minute_boundary(self):
        # Exactly 30:00 is current; one second later it is stale.
        def status(observed):
            return {"comments": [{"author_association": "MEMBER", "body": (
                "COORDINATOR EVIDENCE v1 · imo-ab-test · cycle 2 · epoch 1 · synthetic\n"
                "Coordinator last completed cycle: " + observed.isoformat()
            )}]}
        for age_seconds, expected in (
            (1799, "RUNNING-observed"),
            (1800, "RUNNING-observed"),
            (1801, "STALE"),
        ):
            observed = self.now - timedelta(seconds=age_seconds)
            with self.subTest(age_seconds=age_seconds):
                project, _ = self.fixture_project(status=status(observed))
                self.assertEqual(project["freshness_status"], expected)
                self.assertEqual(
                    datetime.fromisoformat(project["last_cycle_at"]),
                    observed.astimezone(timezone.utc),
                )

    def test_f6_failed_source_and_hold_are_not_green(self):
        degraded = {**self.f3["capture"], "status": "degraded",
                    "errors": ["issue_fetch_failed:1"]}
        p, _ = self.fixture_project(meta=degraded)
        self.assertEqual(p["freshness_status"], "STALE")
        self.assertEqual(p["source_health"]["status"], "degraded")
        registry = json.loads(json.dumps(self.f3["registry"]))
        registry["control"]["hold"] = {"owner_words": "synthetic HOLD"}
        held, _ = self.fixture_project(registry=registry)
        self.assertEqual(held["freshness_status"], "HOLD")
        unknown, _ = self.fixture_project(meta={"status": "degraded", "errors": ["source_down"]},
                                           status={"comments": []})
        self.assertEqual(unknown["freshness_status"], "UNKNOWN")

    def test_f6_failed_inbox_fetch_clears_older_successful_cache(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            rpath = root / "logs" / "imo-ab-test" / "registry.json"
            rpath.parent.mkdir(parents=True)
            rpath.write_text(json.dumps(self.f3["registry"]), encoding="utf-8")
            cache = root / "cache"
            (cache / "threads").mkdir(parents=True)
            (cache / "inbox-1.json").write_text('[{"body":"old-success"}]')
            (cache / "threads" / "issue-1.json").write_text('{"number":1}')
            def fake_issue(repo, number):
                if number == 1:
                    return None
                return {"number": number, "comments": []}
            with mock.patch.object(fetch_live_data, "fetch_issue", side_effect=fake_issue), \
             mock.patch.object(fetch_live_data, "gh_api", return_value=[]), \
                 mock.patch.object(sys, "argv", ["fetch_live_data.py",
                     "--root", str(root), "--repo", CONTROL_REPO,
                     "--cache-dir", str(cache)]):
                fetch_live_data.main()
            self.assertFalse((cache / "inbox-1.json").exists())
            self.assertFalse((cache / "threads" / "issue-1.json").exists())
            manifest = json.loads((cache / "capture-info.json").read_text())
            self.assertEqual(manifest["status"], "degraded")
            self.assertEqual(manifest["errors"], ["issue_fetch_failed:1"])

    def test_f6_registry_exact_git_blob_and_separate_clocks(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "registry.json"
            blob = b'{"project":"synthetic"}\n'
            path.write_bytes(blob)
            expected = hashlib.sha1(b"blob " + str(len(blob)).encode() + b"\x00" + blob).hexdigest()
            self.assertEqual(build_data.git_blob_sha(path), expected)
        p, _ = self.fixture_project()
        self.assertEqual(p["registry_blob_sha"], "b" * 40)
        self.assertEqual(p["source_commit"], "a" * 40)
        self.assertEqual(p["source_capture_at"], "2026-10-15T10:50:00+00:00")
        self.assertEqual(p["built_at"], "2026-10-15T10:50:00+00:00")
        self.assertIsNone(p["published_at"])

    def test_f6_multi_session_merge_with_duplicate_dedup(self):
        with tempfile.TemporaryDirectory() as temp:
            first = Path(temp) / "s1" / "events.jsonl"
            second = Path(temp) / "s2" / "events.jsonl"
            first.parent.mkdir()
            second.parent.mkdir()
            a = {"id": "e1", "t": "2026-10-15T10:00:00Z",
                 "actor": "coordinator", "type": "CONTROL_EPOCH"}
            b = {"id": "e2", "t": "2026-10-15T11:00:00Z",
                 "actor": "agent:b2222222", "type": "TASK_EVIDENCE"}
            first.write_text(json.dumps(a) + "\n")
            second.write_text(json.dumps(a) + "\n" + json.dumps(b) + "\n")
            events = build_data.build_timeline_from_events([first, second], "imo-ab-test")
            self.assertEqual([e["id"] for e in events], ["e1", "e2"])
            self.assertEqual([e["project"] for e in events], ["imo-ab-test"] * 2)
            self.assertEqual([e["_source"] for e in events], ["events_jsonl"] * 2)

    def test_f3_registry_bytes_unchanged_by_full_live_build(self):
        # G04: projections must not rewrite the source registry, even indirectly.
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            registry = root / "logs" / "imo-ab-test" / "registry.json"
            registry.parent.mkdir(parents=True)
            original = json.dumps(self.f3["registry"], indent=2).encode("utf-8")
            registry.write_bytes(original)
            before_digest = hashlib.sha256(registry.read_bytes()).hexdigest()
            cache = root / "cache"
            threads = cache / "threads"
            threads.mkdir(parents=True)
            for number, payload in self.f3["threads"].items():
                (threads / f"issue-{number}.json").write_text(
                    json.dumps(payload), encoding="utf-8"
                )
            (cache / "inbox-1.json").write_text(
                json.dumps(self.f3["inbox"]), encoding="utf-8"
            )
            (cache / "capture-info.json").write_text(
                json.dumps(self.f3["capture"]), encoding="utf-8"
            )
            projects, _ = build_data.build_all(root, root / "generated", cache_dir=cache)
            after = registry.read_bytes()
            self.assertEqual(after, original, "builder must not rewrite registry bytes")
            self.assertEqual(hashlib.sha256(after).hexdigest(), before_digest)
            self.assertEqual(len(projects), 1)
            projected = projects[0]
            self.assertEqual(projected["stale_lease_count"], 5)
            self.assertEqual([l.get("warning") for l in projected["leases"]],
                             ["RETIRED_HOLDER"] * 5)
            self.assertEqual(projected["registry_blob_sha"], build_data.git_blob_sha(registry))
            self.assertEqual(
                json.loads((root / "generated" / "projects.json").read_text())[0][
                    "registry_blob_sha"
                ], build_data.git_blob_sha(registry),
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
