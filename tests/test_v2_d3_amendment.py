"""WP-V2 D3: owner scope change AFTER an already-completed checkpoint.

Tests/fixtures ONLY; do not use live network, mutate real registry or silently
accept an unrelated 30-minute freshness timeout as detecting the Owner change.
"""
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "wp_v2_d3"
sys.path.insert(0, str(ROOT / "scripts"))
from build_data import build_all
from landing_build.continuity import derive_continuity

CHECKPOINT = datetime(2026, 10, 17, 21, 0, tzinfo=timezone.utc)
AMENDMENT = datetime(2026, 10, 17, 21, 15, tzinfo=timezone.utc)
AMENDMENT_ID = 990000001
SOURCE = ("https://github.com/reallakshman19/CoordinatorLandingpage/"
          "issues/1#issuecomment-990000001")
CHANGED_INTENT = "scope changed after the 21:00Z checkpoint"
PROJECT = "landing-live"


def prepared_snapshot(temp):
    """Isolated byte-for-byte registry copy plus the pinned synthetic cache."""
    work = Path(temp)
    root, cache, output = work / "source", work / "cache", work / "output"
    shutil.copytree(FIXTURE / "logs", root / "logs")
    shutil.copytree(FIXTURE / "cache", cache)
    return root, cache, output


def build_snapshot(temp):
    root, cache, output = prepared_snapshot(temp)
    # No new GitHub reads: unknown provenance is retained, not presumed Owner.
    with mock.patch(
        "owner_json.github_provenance",
        return_value={"sha": None, "author": None, "association": "UNKNOWN"}
    ), mock.patch("owner_json.subprocess.run",
                  side_effect=AssertionError("D3 fixture attempted a gh API read")):
        build_all(root, output, cache_dir=cache)
    project = json.loads((output / ("project-" + PROJECT + ".json")).read_text())
    summary = {p["project"]: p for p in
               json.loads((output / "projects.json").read_text())}
    status = {p["project"]: p for p in
              json.loads((output / "status-bar.json").read_text())["projects"]}
    registry = json.loads((root / "logs" / PROJECT / "registry.json").read_text())
    return registry, project, summary[PROJECT], status[PROJECT], output


def source_linked_stale(project, status):
    """Alternative D3 acceptance: task explicitly stale due to this amendment."""
    # A stale clock or unrelated red continuity input is NOT sufficient.
    next_move = project.get("next_move") or {}
    if not isinstance(next_move, dict):
        return False
    text = json.dumps(next_move)
    return ("post_checkpoint_owner_amendment" in text and
            str(AMENDMENT_ID) in text and "STALE" in text.upper())


class D3OwnerChangeAfterCheckpoint(unittest.TestCase):
    def test_01_registry_is_a_copy_and_cached_sources_are_temporally_ordered(self):
        source = (ROOT / "logs" / PROJECT / "registry.json").read_bytes()
        self.assertEqual((FIXTURE / "logs" / PROJECT / "registry.json").read_bytes(),
                         source, "D3 must not amend the real registry")
        inbox = json.loads((FIXTURE / "cache" / "inbox-1.json").read_text())
        self.assertEqual(len(inbox), 1)
        self.assertEqual(inbox[0]["id"], AMENDMENT_ID)
        self.assertEqual(inbox[0]["author_association"], "OWNER")
        self.assertGreater(AMENDMENT, CHECKPOINT)
        self.assertEqual(datetime.fromisoformat(
            inbox[0]["created_at"].replace("Z", "+00:00")), AMENDMENT)
        self.assertIn(CHANGED_INTENT, inbox[0]["body"])
        self.assertTrue((FIXTURE / "cache" / "project-threads" / PROJECT /
                         "issue-30.json").is_file())

    def test_02_builder_carries_source_and_change_into_project_understanding(self):
        with tempfile.TemporaryDirectory() as tmp:
            _, project, summary, _, _ = build_snapshot(tmp)
        self.assertEqual(project["amendments"]["status"], "AVAILABLE")
        self.assertEqual(project["intent"]["status"], "AVAILABLE")
        self.assertEqual(project["amendments"], summary["amendments"])
        self.assertEqual(project["amendments"]["total_matching"], 1)
        record, = project["amendments"]["records"]
        self.assertEqual(record["source"], SOURCE)
        self.assertIn(CHANGED_INTENT, record["text"])
        self.assertEqual(record["created_at"], AMENDMENT.isoformat().replace(
            "+00:00", "Z"))

    def test_03_post_checkpoint_owner_change_requires_reconciliation(self):
        with tempfile.TemporaryDirectory() as tmp:
            _, project, _, status, _ = build_snapshot(tmp)
        self.assertEqual(project["last_cycle_at"],
                         CHECKPOINT.isoformat(),
                         "D3 must compare with the true recorded checkpoint")
        record, = project["amendments"]["records"]
        self.assertGreater(
            datetime.fromisoformat(record["created_at"].replace("Z", "+00:00")),
            datetime.fromisoformat(project["last_cycle_at"]))
        owner = status["continuity"]["inputs"]["owner_input_captured"]
        owner_blocked = (owner["state"] == "PROBLEM" and
                         owner.get("source") == SOURCE)
        self.assertTrue(
            owner_blocked or source_linked_stale(project, status),
            "D3 GAP: captured post-checkpoint #1 Owner scope amendment "
            "remains only visible text; neither owner_input_captured=PROBLEM "
            "with comment source nor task STALE due to this amendment. "
            "A successful cache read is not a reconciled checkpoint.")

    def test_04_post_checkpoint_change_cannot_leave_healthy_continuity_green(self):
        with tempfile.TemporaryDirectory() as tmp:
            registry, project, _, _, _ = build_snapshot(tmp)
        # Remove unrelated stale-clock effects: D3 must block on the amendment
        # itself, not pass merely because this fixture is >30 minutes old.
        healthy = {**project, "freshness_status": "RUNNING-observed",
                   "source_health": {"status": "ok", "errors": []}}
        healthy.pop("unparsed_evidence", None)
        healthy.pop("succession", None)
        baseline = {**healthy, "amendments": {"status": "NONE_FOUND", "records": []}}
        pre = derive_continuity(registry, baseline)
        self.assertEqual(pre["light"], "green",
                         "Only the Owner amendment may break this green baseline")
        post = derive_continuity(registry, healthy)
        self.assertNotEqual(
            post["light"], "green",
            "D3 GAP: continuity can still render GREEN despite a captured "
            "post-checkpoint Owner scope change needing reconciliation.")


if __name__ == "__main__":
    unittest.main(verbosity=2)
