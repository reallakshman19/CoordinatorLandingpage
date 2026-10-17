#!/usr/bin/env python3
"""WP-L1(b): RED-first timeline seam and pre-refactor frozen-fixture parity."""
from datetime import datetime, timezone
import hashlib
import importlib
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build_data

# Frozen fixture: #69 (7f5a6797) added project observation keys; WP-CI1
# compared 18 Windows/Linux files (run 39060897918): only CRLF differed.
# Generated JSON is now always LF; this is the cross-platform byte oracle.
PRE_REFACTOR_SHA256 = (
    "3eb5bddf175f2d44e50b7d2da9fecc30ac95742fcb17d3a3b62bc61eb8bcf311")


class FixedDatetime(datetime):
    @classmethod
    def now(cls, tz=None):
        fixed = datetime(2026, 10, 17, 15, 0, tzinfo=timezone.utc)
        return fixed if tz is None else fixed.astimezone(tz)


class TimelineExtractTests(unittest.TestCase):
    def _timeline(self):
        try:
            return importlib.import_module("landing_build.timeline")
        except ModuleNotFoundError:
            self.fail("RED: landing_build.timeline does not exist yet")

    def test_01_reexport_is_exact_same_function(self):
        timeline = self._timeline()
        for name in ("build_timeline_from_events",
                     "build_timeline_from_threads"):
            with self.subTest(name=name):
                self.assertIs(getattr(build_data, name),
                              getattr(timeline, name))
                self.assertEqual(getattr(timeline, name).__module__,
                                 "landing_build.timeline")
        for name in ("COORD_EVIDENCE_RE", "NEEDS_YOU_RE",
                     "TIME_CORRECTED_RE", "FOR_TC_RE"):
            with self.subTest(name=name):
                self.assertIs(getattr(build_data, name),
                              getattr(timeline, name))

    def test_02_shared_parsers_bound_to_build_data_objects(self):
        timeline = self._timeline()
        for name in ("scrub_chat_url", "parse_task_evidence",
                     "parse_verdict", "OUTSIDE_WRITE_RE"):
            with self.subTest(name=name):
                self.assertIs(getattr(timeline, name),
                              getattr(build_data, name))

    def test_03_threads_reconstruction_kinds(self):
        self._timeline()
        inbox = [{"id": 1, "created_at": "2026-10-17T15:00:00Z",
                  "body": "FOR TeamCoordinator · demo · ask · x1"}]
        threads = [{"number": 5, "comments": [
            {"id": 2, "created_at": "2026-10-17T14:00:00Z",
             "body": "outside write detected"}]}]
        events = build_data.build_timeline_from_threads(
            threads, inbox, "demo")
        self.assertEqual([e["type"] for e in events],
                         ["OUTSIDE_WRITE", "FOR_TC"])

    def test_04_frozen_fixture_bytes_match_pre_refactor(self):
        self._timeline()
        fixtures = [ROOT / "benchmarks" / name for name in (
            "grade9-pilot-2026-10-15", "imo-ab-test-2026-10-15")]
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "a"
            with mock.patch.object(build_data, "datetime", FixedDatetime):
                build_data.build_all(ROOT, out, benchmark_dirs=fixtures)
            digest = hashlib.sha256()
            files = sorted(out.glob("*.json"))
            self.assertTrue(files)
            for path in files:
                digest.update(path.name.encode("utf-8") + b"\0")
                digest.update(path.read_bytes())
            print("FROZEN_FIXTURE_SHA256=" + digest.hexdigest())
            self.assertEqual(digest.hexdigest(), PRE_REFACTOR_SHA256)


if __name__ == "__main__":
    unittest.main(verbosity=2)
