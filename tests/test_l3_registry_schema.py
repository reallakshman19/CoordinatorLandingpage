#!/usr/bin/env python3
"""WP-L3 RED-first optional registry schema; source survives malformed input."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build_data
from landing_build import registry_schema


def registry(**extra):
    return {"project": "case", "repository": "reallakshman19/CoordinatorLandingpage",
            "agents": [], "control": {"epoch": 1}, "workflow": {},
            "open_owner_decisions": [], **extra}


class RegistrySchemaTests(unittest.TestCase):
    def valid(self):
        return {
            "originals": [{
                "name": "Reference A", "path": "records/reference-a.xml",
                "sha": "0123456789abcdef0123456789abcdef01234567",
                "sha256": "a" * 64, "class": "ORIGINAL",
                "custody": "Owner source", "unexpected": {"retain": True},
            }],
            "improvements": [{
                "id": "IMP-001", "title": "Better intake", "author": "agent",
                "disposition": "PROPOSED", "reason": "Needs review",
                "revisit_if": "after acceptance", "implemented_in": None,
                "observed_result": "not yet measured", "retain": True,
                "custom_detail": [1, 2],
            }],
            "succession": {
                "outgoing": "coder g1", "incoming": "coder g2",
                "method": "BuddyRunner v1.7", "phase": "1b",
                "links": {"1a": "https://github.com/example/a",
                          "1b": "https://github.com/example/b",
                          "2": "https://github.com/example/c"},
                "pending_sends": [], "custody": "handover issue",
                "unrecorded_interval": {
                    "from_checkpoint": "2026-10-17T09:00:00Z",
                    "to_departure": "2026-10-17T10:00:00Z"},
                "future_field": {"allowed": True},
            },
        }

    def test_01_valid_fields_preserved_exactly_in_project(self):
        source = self.valid()
        project, _ = build_data.build_project_data(
            ROOT, "case", registry(**source), {}, [], None)
        for key, value in source.items():
            self.assertEqual(project[key], value)
            self.assertEqual(registry_schema.project_additions(source)[key], value)

    def test_02_missing_all_optional_keys_is_byte_compatible(self):
        additions = registry_schema.project_additions(registry())
        self.assertEqual(additions, {})
        project, _ = build_data.build_project_data(
            ROOT, "case", registry(), {}, [], None)
        for key in ("originals", "improvements", "succession"):
            self.assertNotIn(key, project)

    def test_03_all_supported_enums_and_new_unknown_fields_allowed(self):
        for kind in ("ORIGINAL", "SYNTHETIC", "PARTIAL", "MISSING"):
            source = {"originals": [{"name": "x", "path": "x", "class": kind,
                                     "custody": {"owner": "human"}, "future": 12}]}
            self.assertEqual(registry_schema.project_additions(source)["originals"],
                             source["originals"])
        for decision in ("KEEP", "PROPOSED", "ADOPTED", "REJECTED", "PARKED"):
            source = {"improvements": [{"id": "I", "title": "T",
                                       "author": "A", "disposition": decision,
                                       "retain": False, "new_field": "preserve"}]}
            self.assertEqual(registry_schema.project_additions(source)["improvements"],
                             source["improvements"])

    def test_04_malformed_records_are_visible_with_original_content(self):
        source = registry(originals=[
            {"name": "good", "path": "good", "class": "ORIGINAL"},
            {"name": "bad", "path": "bad", "class": "OTHER", "future": 9},
            "wrong item"],
            improvements=[
                {"id": "I", "disposition": "UNREVIEWED", "retain": "yes"},
                {"id": "I2", "title": "safe", "author": "g2",
                 "disposition": "PARKED", "retain": False}])
        result = registry_schema.project_additions(source)
        self.assertEqual(result["originals"][0], source["originals"][0])
        self.assertEqual(result["originals"][1]["status"], "ERROR")
        self.assertEqual(result["originals"][1]["raw"], source["originals"][1])
        self.assertEqual(result["originals"][2]["raw"], "wrong item")
        self.assertEqual(result["improvements"][0]["status"], "ERROR")
        self.assertEqual(result["improvements"][0]["raw"], source["improvements"][0])
        self.assertEqual(result["improvements"][1], source["improvements"][1])
        self.assertEqual(result["originals"][1]["path"], "originals[1]")

    def test_05_malformed_top_level_values_not_dropped(self):
        source = {"originals": "not a list", "improvements": None,
                  "succession": ["not a succession object"]}
        result = registry_schema.project_additions(source)
        for key in source:
            self.assertEqual(result[key]["status"], "ERROR")
            self.assertEqual(result[key]["raw"], source[key])
            self.assertEqual(result[key]["path"], key)

    def test_06_succession_nested_malformed_field_visible(self):
        source = {"succession": {
            "outgoing": "g1", "incoming": "g2", "method": "BuddyRunner",
            "links": {"1a": 404, "1b": "https://github.com/x/y", "2": None},
            "pending_sends": "not an array", "custody": ["unexpected"],
            "unrecorded_interval": {"from_checkpoint": 123,
                                    "to_departure": "2026-10-17T10:00:00Z"}}}
        row = registry_schema.project_additions(source)["succession"]
        self.assertEqual(row["status"], "ERROR")
        self.assertEqual(row["raw"], source["succession"])
        self.assertTrue(row["errors"])
        self.assertIn("succession.links.1a", row["errors"])
        self.assertIn("succession.pending_sends", row["errors"])
        self.assertIn("succession.unrecorded_interval.from_checkpoint",
                      row["errors"])

    def test_07_project_summary_and_detail_show_same_validations(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            p = root / "logs" / "case" / "registry.json"
            p.parent.mkdir(parents=True)
            source = registry(originals=[
                {"name": "entry", "path": "x", "class": "PARTIAL"},
                {"name": "invalid", "class": "NOT_A_CLASS"}],
                improvements=[{"id": "I", "title": "T", "author": "A",
                               "disposition": "KEEP", "retain": True}],
                succession={"outgoing": "g1", "incoming": "g2",
                            "method": "documented", "phase": "2",
                            "links": {"1a": "url", "1b": "url", "2": "url"},
                            "pending_sends": []})
            p.write_text(json.dumps(source), encoding="utf-8")
            build_data.build_all(root, root / "out", cache_dir=root / "cache")
            detail = json.loads((root / "out" / "project-case.json").read_text())
            summary = json.loads((root / "out" / "projects.json").read_text())[0]
            for key in ("originals", "improvements", "succession"):
                self.assertEqual(summary[key], detail[key])
            self.assertEqual(detail["originals"][1]["status"], "ERROR")

    def test_08_existing_history_refs_remains_a_separate_fetch_path(self):
        from landing_build.lineage import plan_lineage
        source = registry(history_refs=[
            "https://github.com/reallakshman19/CoordinatorLandingpage/issues/62"])
        self.assertEqual(len(plan_lineage(source,
            "reallakshman19/CoordinatorLandingpage")), 1)
        self.assertEqual(registry_schema.project_additions(source), {})


if __name__ == "__main__":
    unittest.main(verbosity=2)
