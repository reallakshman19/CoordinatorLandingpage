#!/usr/bin/env python3
"""WP-L2(b): project-wide evidence intake and strictly additive fixture gate."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build_data

CONTROL = "reallakshman19/CoordinatorLandingpage"
OLD_SHA = "3eb5bddf175f2d44e50b7d2da9fecc30ac95742fcb17d3a3b62bc61eb8bcf311"
FIVE = [6184238891, 6184418496, 6185406544, 6185867584, 6186385831]


class FixedDatetime(datetime):
    @classmethod
    def now(cls, tz=None):
        fixed = datetime(2026, 10, 17, 15, tzinfo=timezone.utc)
        return fixed if tz is None else fixed.astimezone(tz)


def comment(n, body):
    return {"id": n, "created_at": "2026-10-15T12:00:00Z", "body": body}


def header(role="coder", chat="deadbeef", seq=1):
    return ("TASK EVIDENCE v2 · demo · " + role + " · chat " + chat +
            " · #" + str(seq) + " · 2026-10-15T12:00:00Z\n"
            "Task: source-backed work\nStatus: DONE")


def fixture(agents=None, status=None, others=None):
    registry = {"project": "demo", "repository": CONTROL, "agents": agents or [],
                "status_issue": status or f"https://github.com/{CONTROL}/issues/42",
                "control": {"epoch": 1}, "workflow": {},
                "open_owner_decisions": []}
    threads = {42: {"number": 42, "comments": [comment(101, header())]}}
    threads.update(others or {})
    return build_data.build_project_data(
        ROOT, "demo", registry, threads, [], None,
        source_meta={"status": "ok"}, now=FixedDatetime.now(timezone.utc),
        status_thread=threads.get(42, {"comments": []}))


class IntakeTests(unittest.TestCase):
    def test_01_agentless_project_keeps_status_issue_history_and_role(self):
        project, timeline = fixture()
        evidence = [e for e in timeline if e.get("type") == "TASK_EVIDENCE"]
        self.assertEqual(len(project["agents"]), 0)
        self.assertEqual(len(evidence), 1)
        self.assertEqual(evidence[0]["comment_id"], 101)
        self.assertEqual(evidence[0]["actor"], "coder · agent:deadbeef")

    def test_02_unparsed_keeps_provenance_role_and_unknown_identity(self):
        agents = [{"role": "coder", "chat_id8": "deadbeef",
                   "evidence_thread": f"https://github.com/{CONTROL}/issues/43"}]
        threads = {43: {"number": 43, "comments": [
            comment(201, header("validator-g2", "UNKNOWN", 1)),
            comment(202, header("", "n/a", 2))]}}
        project, timeline = fixture(agents=agents, others=threads)
        unparsed = project["unparsed_evidence"]
        self.assertEqual([e["comment_id"] for e in unparsed], [201, 202])
        self.assertEqual([e["actor"] for e in unparsed],
                         ["validator-g2", "UNATTRIBUTED"])
        for row in unparsed:
            self.assertEqual(row["type"], "UNPARSED")
            self.assertIsNone(row["chat_id8"])
            self.assertEqual(row["issue_number"], 43)
            self.assertEqual(row["comment_url"],
                             f"https://github.com/{CONTROL}/issues/43#issuecomment-{row['comment_id']}")
        self.assertEqual(unparsed[0]["header_role"], "validator-g2")
        self.assertIsNone(unparsed[1]["header_role"])
        self.assertEqual([e for e in timeline if e.get("comment_id") == 202], [])

    def test_03_foreign_repository_pointer_rejected_before_issue_number(self):
        agents = [{"role": "coder", "chat_id8": "deadbeef",
                   "evidence_thread": "https://github.com/foreign/repo/issues/43"}]
        threads = {43: {"number": 43, "comments": [comment(
            301, header("validator-g2", "UNKNOWN"))]}}
        project, timeline = fixture(agents=agents, others=threads)
        self.assertFalse(project.get("unparsed_evidence"))
        self.assertEqual(project["agents"][0]["evidence"], [])
        self.assertFalse([e for e in timeline if e.get("comment_id") == 301])

    def test_04_five_historical_records_only_exact_frozen_json_delta(self):
        fixtures = [ROOT / "benchmarks" / n for n in (
            "grade9-pilot-2026-10-15", "imo-ab-test-2026-10-15")]
        def digest(folder):
            sha = hashlib.sha256()
            for path in sorted(folder.glob("*.json")):
                sha.update(path.name.encode("utf-8") + b"\0")
                sha.update(path.read_bytes())
            return sha.hexdigest()
        with tempfile.TemporaryDirectory() as temp:
            before, after = Path(temp) / "before", Path(temp) / "after"
            with mock.patch.object(build_data, "datetime", FixedDatetime):
                with mock.patch.object(build_data, "collect_unparsed_evidence",
                                       return_value=[]):
                    build_data.build_all(ROOT, before, benchmark_dirs=fixtures)
                build_data.build_all(ROOT, after, benchmark_dirs=fixtures)
            self.assertEqual(digest(before), OLD_SHA,
                             "Compatibility shim must reproduce exact current main")
            print("WP_L2B_NEW_FROZEN_SHA256=" + digest(after), flush=True)
            names_before = {p.name for p in before.glob("*.json")}
            names_after = {p.name for p in after.glob("*.json")}
            self.assertEqual(names_before, names_after)
            differences = []
            for name in sorted(names_before):
                previous = (before / name).read_bytes()
                current = (after / name).read_bytes()
                if previous == current:
                    continue
                old = json.loads(previous)
                new = json.loads(current)
                if name == "project-grade9-pilot.json":
                    self.assertEqual(set(new) - set(old), {"unparsed_evidence"})
                    records = new.pop("unparsed_evidence")
                    self.assertEqual(new, old)
                elif name == "projects.json":
                    old_row = next(p for p in old if p["project"] == "grade9-pilot")
                    new_row = next(p for p in new if p["project"] == "grade9-pilot")
                    self.assertEqual(set(new_row) - set(old_row), {"unparsed_evidence"})
                    records = new_row.pop("unparsed_evidence")
                    self.assertEqual(new, old)
                else:
                    self.fail("Unexpected frozen-fixture file changed: " + name)
                self.assertEqual([v["comment_id"] for v in records], FIVE)
                self.assertEqual([v["header_role"] for v in records],
                                 ["validator-g2", "coder-g2", "coder-g2", "coder-g2", "coder-g2"])
                self.assertTrue(all(v["type"] == "UNPARSED" and
                                    v["chat_id8"] is None and
                                    v["comment_url"].endswith(str(v["comment_id"]))
                                    for v in records))
                differences.append({"file": name, "added_key": "unparsed_evidence",
                                    "records": records})
            self.assertEqual([v["file"] for v in differences],
                             ["project-grade9-pilot.json", "projects.json"])
            print("WP_L2B_EXACT_JSON_DIFF=" +
                  json.dumps(differences, ensure_ascii=False, sort_keys=True), flush=True)


if __name__ == "__main__":
    unittest.main(verbosity=2)
