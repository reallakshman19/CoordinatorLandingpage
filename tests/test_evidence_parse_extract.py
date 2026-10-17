#!/usr/bin/env python3
"""WP-L1(c): evidence parser seam, direct timeline import, and frozen byte oracle."""
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

# Historical baseline from test_timeline_extract.py test_04; never recompute it here.
PRE_REFACTOR_SHA256 = "ffc6efd54d895d76bc7eb0baa6c55cdfb3b16798eb0bca82fe2e3f1dd6cc1057"


class FixedDatetime(datetime):
    @classmethod
    def now(cls, tz=None):
        fixed = datetime(2026, 10, 17, 15, 0, tzinfo=timezone.utc)
        return fixed if tz is None else fixed.astimezone(tz)


class EvidenceParseExtractTests(unittest.TestCase):
    def test_01_functions_and_regexes_are_exact_reexports(self):
        try:
            parser = importlib.import_module("landing_build.evidence_parse")
        except ModuleNotFoundError:
            self.fail("RED: landing_build.evidence_parse not yet created")
        for name in ("id8", "scrub_chat_url", "parse_task_evidence",
                     "parse_verdict", "EVIDENCE_RE", "VERDICT_RE",
                     "OUTSIDE_WRITE_RE"):
            with self.subTest(name=name):
                self.assertIs(getattr(build_data, name), getattr(parser, name))
        for name in ("id8", "scrub_chat_url", "parse_task_evidence", "parse_verdict"):
            self.assertEqual(getattr(parser, name).__module__,
                             "landing_build.evidence_parse")

    def test_02_timeline_imports_shared_parser_directly(self):
        parser = importlib.import_module("landing_build.evidence_parse")
        timeline = importlib.import_module("landing_build.timeline")
        for name in ("scrub_chat_url", "parse_task_evidence",
                     "parse_verdict", "OUTSIDE_WRITE_RE"):
            with self.subTest(name=name):
                self.assertIs(getattr(timeline, name), getattr(parser, name))
        source = (ROOT / "scripts" / "landing_build" / "timeline.py").read_text()
        self.assertIn("from landing_build.evidence_parse import", source)
        builder = (ROOT / "scripts" / "build_data.py").read_text()
        for name in ("scrub_chat_url", "parse_task_evidence", "parse_verdict",
                     "OUTSIDE_WRITE_RE"):
            self.assertNotIn("_timeline." + name + " =", builder)

    def test_03_chat_na_hex_verdict_and_outside_write_unchanged(self):
        prefix = "TASK EVIDENCE v2 · landing-live · coder · chat "
        suffix = " · #2 · 2026-10-17T09:38:00+04:00\\nTask: check\\nStatus: DONE"
        na = build_data.parse_task_evidence(prefix + "n/a (Claude session)" + suffix,
                                             42, "2026-10-17T09:38:00Z")
        self.assertEqual(na["chat_id8"], None)
        self.assertEqual(na["task"], "check")
        ident = build_data.parse_task_evidence(prefix + "6ad36e4d" + suffix, 43,
                                                "2026-10-17T09:38:00Z")
        self.assertEqual(ident["chat_id8"], "6ad36e4d")
        self.assertIsNone(build_data.parse_task_evidence(
            prefix + "6ad36e4x" + suffix, 44, "2026-10-17T09:38:00Z"))
        verdict = build_data.parse_verdict(
            "OwnerTeammember grounding verdict: ✅ ALIGNED", 10, "2026-10-17T09:38:00Z")
        self.assertEqual(verdict["verdict"], "✅ ALIGNED")
        self.assertTrue(build_data.OUTSIDE_WRITE_RE.search("outside write detected"))
        self.assertFalse(build_data.OUTSIDE_WRITE_RE.search("writer within the lease"))
        raw = "https://chatgpt.com/c/01234567-89abcdef-01234567-89abcdef"
        self.assertEqual(build_data.scrub_chat_url(raw), "chat:01234567")

    def test_04_frozen_fixture_bytes_match_existing_pre_refactor_oracle(self):
        fixtures = [ROOT / "benchmarks" / name for name in (
            "grade9-pilot-2026-10-15", "imo-ab-test-2026-10-15")]
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "a"
            with mock.patch.object(build_data, "datetime", FixedDatetime):
                build_data.build_all(ROOT, out, benchmark_dirs=fixtures)
            sha = hashlib.sha256()
            files = sorted(out.glob("*.json"))
            self.assertTrue(files)
            for path in files:
                sha.update(path.name.encode("utf-8") + b"\\0")
                sha.update(path.read_bytes())
            print("FROZEN_FIXTURE_SHA256=" + sha.hexdigest())
            self.assertEqual(sha.hexdigest(), PRE_REFACTOR_SHA256)


if __name__ == "__main__":
    unittest.main(verbosity=2)
