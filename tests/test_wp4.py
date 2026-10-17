#!/usr/bin/env python3
"""WP4 publisher negative control and fail-closed publication checks.

BaseCompatiblePublisherTests run on both merged WP2 BASE and proposed WP4 HEAD.
They use the same workflow/file interfaces on either ref. Failures on BASE
demonstrate actual overwritten live bytes and multiple Pages writers, not
missing Python functions or changed signatures.
"""
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import publish_site


class BaseCompatiblePublisherTests(unittest.TestCase):
    def workflows(self):
        return sorted((ROOT / ".github" / "workflows").glob("*.yml"))

    def test_wp4_only_one_pages_publisher(self):
        writers = []
        for path in self.workflows():
            body = path.read_text(encoding="utf-8")
            if ("actions/deploy-pages@" in body or
                    "actions/jekyll-build-pages@" in body):
                writers.append(path.name)
        self.assertEqual(writers, ["deploy.yml"],
                         "more than one Pages writer can replace a live deployment")

    def test_wp4_old_benchmark_snapshot_cannot_overwrite_live_projects(self):
        workflow = (ROOT / ".github/workflows/deploy.yml").read_text()
        # Model exactly the OLD/NEW shell ordering with fixture-only bytes:
        # OLD builds _artifact/data/projects.json then copies site/. including
        # the committed 07:23 site/data benchmark snapshot, overwriting LIVE.
        # NEW copies site first, deletes its copied data, then builds LIVE.
        build_pos = workflow.find("name: Build live site data")
        if build_pos < 0:
            build_pos = workflow.find("name: Build LIVE root")
        copy_pos = workflow.find("cp -r site/. _artifact/")
        self.assertGreaterEqual(build_pos, 0)
        self.assertGreaterEqual(copy_pos, 0)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            snapshot = root / "site/data/projects.json"
            snapshot.parent.mkdir(parents=True)
            snapshot.write_text('{"source":"benchmark-07:23"}')
            out = root / "_artifact/data/projects.json"
            out.parent.mkdir(parents=True)
            live = '{"source":"live-current-registry"}'
            if build_pos < copy_pos:
                out.write_text(live)
                shutil.copytree(root / "site", root / "_artifact",
                                dirs_exist_ok=True)
            else:
                shutil.copytree(root / "site", root / "_artifact",
                                dirs_exist_ok=True)
                shutil.rmtree(root / "_artifact/data")
                out.parent.mkdir(parents=True)
                out.write_text(live)
            # The benchmark generation also writes a distinct path.
            benchmark = root / "_artifact/data/benchmarks/projects.json"
            benchmark.parent.mkdir(parents=True)
            benchmark.write_text('{"source":"frozen-benchmark"}')
            self.assertEqual(out.read_text(), live,
                             "base publisher replaced LIVE with benchmark snapshot")
            self.assertNotEqual(out.read_bytes(), benchmark.read_bytes())

    def test_wp4_failed_fetch_cannot_be_masked_as_green(self):
        workflow = (ROOT / ".github/workflows/deploy.yml").read_text()
        self.assertNotIn("continue-on-error: true", workflow)
        self.assertIn("python scripts/publish_site.py capture", workflow)
        self.assertIn("python scripts/publish_site.py stamp", workflow)


class PublisherGateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.cache = self.root / "cache"
        self.cache.mkdir()
        self.repo = "reallakshman19/CoordinatorLandingpage"
        self.sha = "d" * 40
        self.capture = {
            "status": "ok", "repository": self.repo,
            "source_commit": self.sha,
            "source_capture_at": datetime.now(timezone.utc).isoformat(),
            "issues_fetched": [1, 12], "owner_inputs_complete": True,
            "statuses": {"imo-ab-test": 12}, "errors": []
        }
        self.write_capture()
        (self.cache / "inbox-1.json").write_text("[]")
        (self.cache / "owner-inputs-source.json").write_text("[]")

    def write_capture(self):
        (self.cache / "capture-info.json").write_text(
            json.dumps(self.capture))

    def test_wp4_degraded_manifest_blocks_publish(self):
        for mutation in (
            {"status": "degraded"},
            {"errors": ["issue_fetch_failed:12"]},
            {"owner_inputs_complete": False},
            {"issues_fetched": [12]},
            {"source_commit": "f" * 40},
        ):
            with self.subTest(mutation=mutation):
                self.write_capture()
                data = json.loads((self.cache/"capture-info.json").read_text())
                data.update(mutation)
                (self.cache/"capture-info.json").write_text(json.dumps(data))
                with self.assertRaises(ValueError):
                    publish_site.check_capture(self.cache, self.repo, self.sha)

    def test_wp4_stale_manifest_and_missing_inbox_block_publish(self):
        self.capture["source_capture_at"] = "2026-01-01T00:00:00+00:00"
        self.write_capture()
        with self.assertRaisesRegex(ValueError, "stale"):
            publish_site.check_capture(self.cache, self.repo, self.sha)
        self.capture["source_capture_at"] = datetime.now(timezone.utc).isoformat()
        self.write_capture()
        (self.cache / "inbox-1.json").unlink()
        with self.assertRaisesRegex(ValueError, "inbox"):
            publish_site.check_capture(self.cache, self.repo, self.sha)

    def make_artifact(self):
        logs = self.root / "logs/imo-ab-test"
        logs.mkdir(parents=True)
        registry = logs / "registry.json"
        registry.write_text('{"project":"imo-ab-test"}')
        b = registry.read_bytes()
        blob = hashlib.sha1(
            b"blob " + str(len(b)).encode() + b"\0" + b
        ).hexdigest()
        data = self.root / "artifact/data"
        data.mkdir(parents=True)
        summary = [{
            "project": "imo-ab-test", "is_benchmark": False,
            "registry_blob_sha": blob, "source_commit": self.sha,
            "source_capture_at": self.capture["source_capture_at"],
            "source_health": {"status": "ok", "errors": []},
            "published_at": None, "built_at": datetime.now(timezone.utc).isoformat()
        }]
        (data / "projects.json").write_text(json.dumps(summary))
        (data / "owner-inputs.json").write_text("[]")
        (data / "project-imo-ab-test.json").write_text("{}")
        (data / "benchmarks").mkdir()
        (data / "benchmarks/projects.json").write_text(
            json.dumps([{"is_benchmark": True, "project": "frozen"}]))
        (self.root / "artifact/index.html").write_text(
            '<!doctype html><html><head><link rel="stylesheet" href="style.css">'
            '</head><body><script src="js/core.js"></script></body></html>')
        (self.root / "artifact/js").mkdir()
        (self.root / "artifact/js/core.js").write_text("// test fixture\n")
        p = self.root / "artifact/protocol"
        p.mkdir()
        (p / "TEAM_PROTOCOL.md").write_text("# Test source")
        return self.root / "artifact", registry

    def test_wp4_live_and_benchmark_paths_isolated(self):
        artifact, _ = self.make_artifact()
        original = (artifact / "data/projects.json").read_bytes()
        got = publish_site.check_artifact(
            artifact, self.root/"logs", self.capture)
        self.assertEqual(len(got), 1)
        self.assertEqual((artifact / "data/projects.json").read_bytes(), original)
        wrong = json.loads(original)
        wrong[0]["is_benchmark"] = True
        (artifact/"data/projects.json").write_text(json.dumps(wrong))
        with self.assertRaisesRegex(ValueError, "stale/mismatched"):
            publish_site.check_artifact(artifact, self.root/"logs",
                                        self.capture)

    def test_wp4_stamp_and_deployed_readback_hash(self):
        artifact, registry = self.make_artifact()
        old_registry = registry.read_bytes()
        info = publish_site.stamp(
            artifact, self.root/"logs", self.cache, self.repo,
            self.sha, "487123")
        path = artifact / "build-info.json"
        self.assertEqual(info["source_commit"], self.sha)
        self.assertEqual(info["published_at"], None)
        self.assertEqual(info["source_capture_at"],
                         self.capture["source_capture_at"])
        self.assertEqual(info["live_file_sha256"]["projects.json"],
                         publish_site.sha256(artifact/"data/projects.json"))
        self.assertEqual(registry.read_bytes(), old_registry)
        contents = path.read_bytes()
        self.assertEqual(
            publish_site.verify_readback_bytes(path, contents, self.sha),
            hashlib.sha256(contents).hexdigest())
        with self.assertRaisesRegex(ValueError, "mismatch"):
            publish_site.verify_readback_bytes(
                path, contents.replace(b"487123", b"487122"), self.sha)
        with self.assertRaisesRegex(ValueError, "source SHA mismatch"):
            publish_site.verify_readback_bytes(path, contents, "f" * 40)


if __name__ == "__main__":
    unittest.main(verbosity=2)
