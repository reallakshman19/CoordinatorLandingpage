#!/usr/bin/env python3
"""WP-L1(a): RED-first seam, behavior and frozen-fixture parity checks."""
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


class FixedDatetime(datetime):
    @classmethod
    def now(cls, tz=None):
        fixed = datetime(2026, 10, 17, 15, 0, tzinfo=timezone.utc)
        return fixed if tz is None else fixed.astimezone(tz)


class FreshnessExtractTests(unittest.TestCase):
    def test_01_new_module_reexport_is_exact_same_function(self):
        try:
            freshness = importlib.import_module("landing_build.freshness")
        except ModuleNotFoundError:
            self.fail("RED: landing_build.freshness does not exist yet")
        for name in ("_utc_time", "last_completed_cycle", "derive_freshness"):
            with self.subTest(name=name):
                self.assertIs(getattr(build_data, name), getattr(freshness, name))
                self.assertEqual(getattr(freshness, name).__module__,
                                 "landing_build.freshness")
        self.assertEqual(build_data.LIVENESS_OBSERVATION_LIMIT,
                         freshness.LIVENESS_OBSERVATION_LIMIT)

    def test_02_utc_parse_retains_original_boundaries(self):
        parse = build_data._utc_time
        self.assertIsNone(parse(None))
        self.assertIsNone(parse("2026-10-17T15:00:00"))
        self.assertIsNone(parse("not a time"))
        expected = datetime(2026, 10, 17, 15, 0, tzinfo=timezone.utc)
        for value in ("2026-10-17T15:00:00Z",
                      "2026-10-17T19:00:00+04:00",
                      "17 Oct 2026 19:00 +0400",
                      "**2026-10-17T15:00:00Z**"):
            with self.subTest(value=value):
                self.assertEqual(parse(value), expected)

    def test_03_cycle_custody_and_epoch_restrictions(self):
        now = datetime(2026, 10, 17, 16, 0, tzinfo=timezone.utc)
        def receipt(project, epoch, stamp, association):
            return {
                "body": (f"COORDINATOR RECEIPT · {project} · epoch {epoch}"
                         f" · {stamp}"),
                "author_association": association,
                "created_at": stamp,
            }
        entries = [
            receipt("landing-live", 2, "2026-10-17T15:00:00Z", "OWNER"),
            receipt("landing-live", 2, "2026-10-17T15:30:00Z", "CONTRIBUTOR"),
            receipt("landing-live", 1, "2026-10-17T15:45:00Z", "OWNER"),
            receipt("another-project", 2, "2026-10-17T15:50:00Z", "OWNER"),
            receipt("landing-live", 2, "2026-10-17T16:30:00Z", "OWNER"),
        ]
        observed = build_data.last_completed_cycle(
            {"comments": entries}, "landing-live", now, epoch=2,
            epoch_since="2026-10-17T14:00:00Z")
        self.assertEqual(observed, "2026-10-17T15:00:00+00:00")

    def test_04_freshness_maintains_hold_and_age(self):
        now = datetime(2026, 10, 17, 16, 0, tzinfo=timezone.utc)
        classify = build_data.derive_freshness
        self.assertEqual(classify(None, None, None, now), "UNKNOWN")
        self.assertEqual(classify("bogus", {"status": "ok"}, None, now),
                         "UNKNOWN")
        self.assertEqual(classify(None, {"status": "ok"}, "HOLD", now),
                         "HOLD")
        self.assertEqual(classify("2026-10-17T15:29:00Z",
                                  {"status": "degraded"}, None, now), "STALE")
        self.assertEqual(classify("2026-10-17T15:31:00Z",
                                  {"status": "ok"}, None, now),
                         "RUNNING-observed")
        self.assertEqual(classify("2026-10-17T15:29:00Z",
                                  {"status": "ok"}, None, now), "STALE")
        self.assertEqual(classify("2026-10-17T16:01:00Z",
                                  {"status": "ok"}, None, now), "UNKNOWN")

    def test_05_frozen_fixture_bytes_reproducible_and_reported(self):
        fixtures = [ROOT / "benchmarks" / name for name in (
            "grade9-pilot-2026-10-15", "imo-ab-test-2026-10-15")]
        for source in fixtures:
            self.assertTrue((source / "MANIFEST.json").is_file())
        def fingerprint(out):
            digest = hashlib.sha256()
            files = sorted(out.glob("*.json"))
            self.assertTrue(files)
            for path in files:
                digest.update(path.name.encode("utf-8") + b"\\0")
                digest.update(path.read_bytes())
            return digest.hexdigest()
        with tempfile.TemporaryDirectory() as tmp:
            left = Path(tmp) / "a"
            right = Path(tmp) / "b"
            with mock.patch.object(build_data, "datetime", FixedDatetime):
                build_data.build_all(ROOT, left, benchmark_dirs=fixtures)
                build_data.build_all(ROOT, right, benchmark_dirs=fixtures)
            first = fingerprint(left)
            second = fingerprint(right)
            print("FROZEN_FIXTURE_SHA256=" + first)
            self.assertEqual(first, second)
            self.assertEqual(
                {p.name: p.read_bytes() for p in left.glob("*.json")},
                {p.name: p.read_bytes() for p in right.glob("*.json")})


if __name__ == "__main__":
    unittest.main(verbosity=2)
