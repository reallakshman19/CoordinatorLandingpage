"""WP-L6: a source-backed fourth, project-scoped continuity light."""
from datetime import datetime, timezone
import unittest
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import status_bar
from landing_build.continuity import derive_continuity

REPO = "reallakshman19/Common"
ISSUE = f"https://github.com/{REPO}/issues/62"
NOW = datetime(2026, 10, 18, 6, 0, tzinfo=timezone.utc)
EXPECTED = ("intent_linked", "originals_declared", "owner_input_captured",
            "lineage_verified", "head_fresh")


def data():
    registry = {"project": "case", "repository": REPO,
                "parent_issue": ISSUE, "agents": []}
    view = {"lineage": [{"kind": "parent_issue", "status": "AVAILABLE",
                         "url": ISSUE, "issue_number": 62}],
            "originals": [{"name": "original", "path": "x", "class": "ORIGINAL"}],
            "source_health": {"status": "ok", "errors": []},
            "source_refs": {"inbox":
                "https://github.com/reallakshman19/CoordinatorLandingpage/issues/1"},
            "freshness_status": "RUNNING-observed"}
    return registry, view


class ContinuityTests(unittest.TestCase):
    def test_01_all_unknown_cannot_turn_green(self):
        result = derive_continuity({"project": "case"}, {})
        self.assertEqual(result["light"], "grey")
        self.assertEqual(set(result["inputs"]), set(EXPECTED))
        self.assertTrue(all(v["state"] == "UNKNOWN" for v in result["inputs"].values()))
        self.assertTrue(all("source" in v for v in result["inputs"].values()))

    def test_02_all_five_sources_ok_light_green(self):
        reg, view = data()
        result = derive_continuity(reg, view)
        self.assertEqual(result["light"], "green")
        self.assertTrue(all(row["state"] == "OK" for row in result["inputs"].values()))
        self.assertEqual(result["inputs"]["intent_linked"]["source"], ISSUE)

    def test_03_one_problem_makes_light_red(self):
        reg, view = data()
        view["freshness_status"] = "STALE"
        result = derive_continuity(reg, view)
        self.assertEqual(result["light"], "red")
        self.assertEqual(result["inputs"]["head_fresh"]["state"], "PROBLEM")

    def test_04_parent_declared_but_unfetched_unknown(self):
        reg, view = data()
        del view["lineage"]
        state = derive_continuity(reg, view)["inputs"]["intent_linked"]
        self.assertEqual(state["state"], "UNKNOWN")

    def test_05_unavailable_parent_is_problem(self):
        reg, view = data()
        view["lineage"][0]["status"] = "INACCESSIBLE"
        result = derive_continuity(reg, view)
        self.assertEqual(result["light"], "red")
        self.assertEqual(result["inputs"]["intent_linked"]["state"], "PROBLEM")

    def test_06_origins_valid_and_missing_marked_problem(self):
        reg, view = data()
        view["originals"].append({"name": "missing", "path": "y", "class": "MISSING"})
        result = derive_continuity(reg, view)
        self.assertEqual(result["inputs"]["originals_declared"]["state"], "PROBLEM")
        self.assertEqual(result["inputs"]["originals_declared"]["missing"], ["missing"])
        self.assertEqual(result["light"], "red")

    def test_07_originals_error_and_absence_stay_fail_closed(self):
        reg, view = data()
        view["originals"] = [{"status": "ERROR", "raw": {"class": "bad"}}]
        self.assertEqual(derive_continuity(reg, view)["inputs"]["originals_declared"]["state"], "PROBLEM")
        del view["originals"]
        self.assertEqual(derive_continuity(reg, view)["inputs"]["originals_declared"]["state"], "UNKNOWN")

    def test_08_uncaptured_owner_interval_is_problem(self):
        reg, view = data()
        view["succession"] = {"unrecorded_interval": {
            "from_checkpoint": "2026-10-17T10:00Z", "to_departure": "2026-10-17T11:00Z"}}
        self.assertEqual(derive_continuity(reg, view)["inputs"]["owner_input_captured"]["state"], "PROBLEM")
        self.assertEqual(derive_continuity(reg, view)["light"], "red")

    def test_09_owner_capture_missing_and_errors(self):
        reg, view = data()
        view["source_health"] = {"status": "unknown", "errors": []}
        self.assertEqual(derive_continuity(reg, view)["inputs"]["owner_input_captured"]["state"], "UNKNOWN")
        view["source_health"] = {"status": "degraded", "errors": ["owner_inbox_missing"]}
        self.assertEqual(derive_continuity(reg, view)["inputs"]["owner_input_captured"]["state"], "PROBLEM")

    def test_10_lineage_foreign_and_inaccessible_not_green(self):
        reg, view = data()
        for status in ("REJECTED", "FOREIGN", "FOREIGN_REPOSITORY",
                       "ERROR", "INACCESSIBLE"):
            with self.subTest(status=status):
                view["lineage"] = [{"kind": "history_ref", "status": status,
                                    "reference": ISSUE}]
                result = derive_continuity(reg, view)
                self.assertEqual(result["inputs"]["lineage_verified"]["state"], "PROBLEM")
                self.assertEqual(result["light"], "red")

    def test_11_freshness_unknown_hold_stale_and_observed(self):
        reg, view = data()
        for raw, expected in (("UNKNOWN", "UNKNOWN"), ("BENCHMARK", "UNKNOWN"),
                              ("HOLD", "PROBLEM"), ("STALE", "PROBLEM"),
                              ("RUNNING-observed", "OK")):
            with self.subTest(raw=raw):
                view["freshness_status"] = raw
                self.assertEqual(derive_continuity(reg, view)["inputs"]["head_fresh"]["state"], expected)

    def test_12_existing_three_dimensions_and_legacy_lights_unchanged(self):
        reg, view = data()
        instance = {"key": "case/workstream:@root/instance:agent:0",
                    "project": "case", "instance_id8": "a1b2c3d4",
                    "work_state": "active", "retired": False, "standby": False,
                    "complete": False, "conflicts": [],
                    "observation": None, "last_evaluation": None,
                    "monitoring": None, "grant": None,
                    "material_release": None, "timer_observation": None,
                    "browser_observation": None}
        status = status_bar.derive_status(instance, reg, view, NOW)
        self.assertEqual(set(status["dimensions"]),
                         {"work", "monitoring", "execution_authority"})
        snapshot = status_bar.build_status_bar({"case": reg}, {"case": view}, NOW)
        self.assertIn("continuity", snapshot["projects"][0])
        self.assertEqual(snapshot["projects"][0]["continuity"]["light"], "green")
        self.assertEqual(snapshot["projects"][0]["light"], "yellow")
        frozen = status_bar.build_status_bar(
            {"case": reg}, {"case": view}, NOW, include_continuity=False)
        self.assertNotIn("continuity", frozen["projects"][0])


if __name__ == "__main__":
    unittest.main(verbosity=2)
