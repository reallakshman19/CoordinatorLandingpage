"""WP-L5 pinned SYNTHETIC v3.6 scoreboard contract; no Common network."""
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from landing_build.v36_scoreboard import scoreboard_project, SHA256, ARTIFACT
from build_data import build_all

NAME = "v36-continuity"
PARENT = "https://github.com/reallakshman19/Common/issues/409"


def project(root, titles=()):
    return scoreboard_project(root, NAME, {"parent_issue": PARENT}, {
        "child_progress": {"status": "known", "items": [
            {"title": title, "state": "DONE"} for title in titles]}})


class PinnedV36ScoreboardTests(unittest.TestCase):
    def test_pinned_fixture_provenance_not_live(self):
        result = project(ROOT)
        self.assertEqual(SHA256, "a3d3a50ab830ebf261004936cc916f9ca9659d93be23e9fc41edf6bc2e1d34d3")
        self.assertEqual(ARTIFACT, "benchmarks/v36-scoreboard/scoreboard.json")
        self.assertEqual(result["status"], "SYNTHETIC_FIXTURE", result)
        self.assertEqual(result["source_class"], "synthetic fixture")
        self.assertEqual(result["source_parent"], "reallakshman19/Common#341")
        self.assertEqual(result["registry_parent"], PARENT)
        self.assertNotEqual(result["source_parent"], result["registry_parent"])
        self.assertEqual((result["E"]["current"], result["E"]["tasks"]), (1, 7))
        self.assertEqual(result["A"]["label"], "category coverage")
        for key in ("A", "V", "acceptance"):
            self.assertEqual(result[key]["status"], "NOT_EVALUATED")
        self.assertEqual(len(result["tasks"]), 7)
        self.assertTrue(all(t["A"] == "NOT_EVALUATED"
                            and t["V"] == "NOT_EVALUATED"
                            and t["acceptance"] == "NOT_EVALUATED"
                            for t in result["tasks"]))
        self.assertNotIn("PASS", json.dumps(result))

    def test_missing_file_unknown_not_pass(self):
        with tempfile.TemporaryDirectory() as temp:
            result = project(Path(temp))
        self.assertEqual(result["status"], "UNKNOWN")
        self.assertEqual(result["E"]["status"], "UNKNOWN")
        self.assertEqual(result["acceptance"]["status"], "UNKNOWN")

    def test_wrong_schema_visible_error(self):
        with tempfile.TemporaryDirectory() as temp:
            artifact = Path(temp) / ARTIFACT
            artifact.parent.mkdir(parents=True)
            artifact.write_text('{"schema":"v36.scoreboard/v2","rows":[]}')
            result = project(Path(temp))
        self.assertEqual(result["status"], "ERROR")
        self.assertIn("schema", result["reason"].lower())
        self.assertEqual(result["E"]["status"], "ERROR")

    def test_corrupt_json_and_valid_schema_wrong_digest_error(self):
        with tempfile.TemporaryDirectory() as temp:
            artifact = Path(temp) / ARTIFACT
            artifact.parent.mkdir(parents=True)
            artifact.write_text("{invalid")
            self.assertEqual(project(Path(temp))["status"], "ERROR")
            artifact.write_text('{"schema":"v36.scoreboard/v1","rows":[]}')
            self.assertEqual(project(Path(temp))["status"], "ERROR")

    def test_title_only_fallback_is_not_evidence(self):
        with tempfile.TemporaryDirectory() as temp:
            result = project(Path(temp), ("[V3.6][O2][DONE] sample",))
        self.assertEqual(result["status"], "UNKNOWN")
        self.assertEqual(result["title_fallback"]["label"], "derived from title")
        self.assertEqual(result["title_fallback"]["count"], 1)
        self.assertEqual(result["E"]["status"], "UNKNOWN")

    def test_irrelevant_project_has_no_v36_overlay(self):
        self.assertIsNone(scoreboard_project(
            ROOT, "landing-live", {"parent_issue": PARENT}, {}))

    def test_live_build_projects_and_no_github_api(self):
        with tempfile.TemporaryDirectory() as temp, mock.patch(
            "owner_json.github_provenance",
            return_value={"sha": None, "author": None, "association": "UNKNOWN"}
        ), mock.patch("owner_json.subprocess.run",
                      side_effect=AssertionError("test attempted gh api")):
            output = Path(temp) / "data"
            build_all(ROOT, output, cache_dir=Path(temp) / "empty-cache")
            projects = {p["project"]: p for p in
                        json.loads((output / "projects.json").read_text())}
            self.assertEqual(projects[NAME]["v36_scoreboard"]["source_class"],
                             "synthetic fixture")
            self.assertNotIn("v36_scoreboard", projects["landing-live"])
            detail = json.loads((output / f"project-{NAME}.json").read_text())
            self.assertEqual(detail["v36_scoreboard"]["status"], "SYNTHETIC_FIXTURE")


if __name__ == "__main__":
    unittest.main(verbosity=2)
