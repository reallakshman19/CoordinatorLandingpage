"""WP-L6b real-build contract: read live registries, never benchmark fixtures."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_data import build_all

INPUTS = ("intent_linked", "originals_declared", "owner_input_captured",
          "lineage_verified", "head_fresh")
STATES = {"OK", "PROBLEM", "UNKNOWN"}


class LiveContinuityContract(unittest.TestCase):
    def test_live_registry_build_emits_five_inputs_and_landing_custody(self):
        registries = {
            folder.name: json.loads((folder / "registry.json").read_text())
            for folder in (ROOT / "logs").iterdir()
            if folder.is_dir() and (folder / "registry.json").is_file()
        }
        self.assertIn("landing-live", registries)
        landing = registries["landing-live"]
        parent_url = landing["parent_issue"]
        self.assertEqual(parent_url,
                         "https://github.com/reallakshman19/CoordinatorLandingpage/issues/21")
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "output"
            cache = Path(temp) / "cache"
            extra = cache / "project-extras" / "landing-live"
            extra.mkdir(parents=True)
            (extra / "lineage.json").write_text(json.dumps([{
                "kind": "parent_issue", "reference": parent_url,
                "status": "AVAILABLE", "url": parent_url, "issue_number": 21,
            }]), encoding="utf-8")
            build_all(ROOT, output, cache_dir=cache)  # LIVE: benchmark_dirs omitted.
            result = json.loads((output / "status-bar.json").read_text())
            projects = {p["project"]: p for p in result["projects"]}
            self.assertEqual(set(projects), set(registries))
            for name, row in projects.items():
                with self.subTest(project=name):
                    continuity = row["continuity"]
                    self.assertEqual(set(continuity["inputs"]), set(INPUTS))
                    for key in INPUTS:
                        item = continuity["inputs"][key]
                        self.assertIn(item["state"], STATES)
                        self.assertIn("source", item)
                    states = {item["state"] for item in continuity["inputs"].values()}
                    self.assertEqual(continuity["light"], "red" if "PROBLEM" in states
                                     else "green" if states == {"OK"} else "grey")
            live = projects["landing-live"]["continuity"]["inputs"]
            self.assertEqual(live["originals_declared"]["state"], "OK")
            self.assertEqual(
                {item["class"] for item in landing["originals"]},
                {"ORIGINAL", "PARTIAL"})
            self.assertEqual(live["intent_linked"]["state"], "OK")
            self.assertEqual(live["intent_linked"]["source"], parent_url)
            self.assertNotEqual(
                projects["landing-live"]["continuity"]["light"], "green",
                "Unobserved other inputs must never become green")


if __name__ == "__main__":
    unittest.main(verbosity=2)
