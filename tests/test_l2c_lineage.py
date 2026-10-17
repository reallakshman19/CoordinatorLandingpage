#!/usr/bin/env python3
"""WP-L2(c): allow-listed G3 lineage intake and read-only projection."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build_data
import fetch_live_data

CONTROL = "reallakshman19/CoordinatorLandingpage"
PRODUCT = "reallakshman19/Common"
FOREIGN = "foreign/repository"


def url(repo, n):
    return f"https://github.com/{repo}/issues/{n}"


class LineageTests(unittest.TestCase):
    def run_capture(self, reg, responder=None):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        name = reg.get("project", "case")
        file = root / "logs" / name / "registry.json"
        file.parent.mkdir(parents=True)
        file.write_text(json.dumps(reg), encoding="utf-8")
        calls, errors = [], []

        def api(endpoint):
            calls.append(endpoint)
            if responder is not None:
                return responder(endpoint)
            n = int(endpoint.rsplit("/", 1)[-1])
            repo = endpoint.split("/")[2] + "/" + endpoint.split("/")[3]
            return {"number": n, "repository": repo, "title": f"Issue {n}",
                    "state": "open", "html_url": url(repo, n)}
        with mock.patch.object(fetch_live_data, "gh_api", side_effect=api):
            fetch_live_data.capture_project_extras(
                root, root / "cache", {name: {"repository": PRODUCT}},
                errors, control_repo=CONTROL)
        snapshot = root / "cache" / "project-extras" / name / "lineage.json"
        return root, (json.loads(snapshot.read_text()) if snapshot.exists()
                      else None), calls, errors

    def reg(self, **kwargs):
        return {"project": "case", "repository": PRODUCT,
                "agents": [], "control": {"epoch": 1},
                "open_owner_decisions": [], "workflow": {}, **kwargs}

    def test_01_parent_and_history_refs_are_allowlisted_get_only(self):
        reg = self.reg(parent_issue=url(PRODUCT, 408),
                       history_refs=[url(CONTROL, 21), {"url": url(PRODUCT, 409)}])
        _, rows, calls, errors = self.run_capture(reg)
        self.assertEqual(errors, [])
        self.assertEqual([x["kind"] for x in rows],
                         ["parent_issue", "history_ref", "history_ref"])
        self.assertEqual([x["status"] for x in rows], ["AVAILABLE"] * 3)
        self.assertEqual([x["repository"] for x in rows],
                         [PRODUCT, CONTROL, PRODUCT])
        self.assertEqual(calls, [f"/repos/{PRODUCT}/issues/408",
                                 f"/repos/{CONTROL}/issues/21",
                                 f"/repos/{PRODUCT}/issues/409"])
        self.assertTrue(all(row["title"] and row["url"] for row in rows))

    def test_02_foreign_repo_is_rejected_and_visible_without_request(self):
        reg = self.reg(parent_issue=url(FOREIGN, 408),
                       history_refs=[url(PRODUCT, 409)])
        _, rows, calls, errors = self.run_capture(reg)
        self.assertEqual(errors, [])
        self.assertEqual([r["status"] for r in rows], ["REJECTED", "AVAILABLE"])
        self.assertEqual(rows[0]["reference"], url(FOREIGN, 408))
        self.assertEqual(rows[0]["kind"], "parent_issue")
        self.assertNotIn("url", rows[0])
        self.assertEqual(calls, [f"/repos/{PRODUCT}/issues/409"])

    def test_03_404_and_inaccessible_not_deleted(self):
        reg = self.reg(parent_issue=url(PRODUCT, 405),
                       history_refs=[url(PRODUCT, 406)])
        def api(endpoint):
            return None if endpoint.endswith("/405") else {"number": 99}
        _, rows, calls, _ = self.run_capture(reg, responder=api)
        self.assertEqual([r["status"] for r in rows],
                         ["INACCESSIBLE", "INACCESSIBLE"])
        self.assertTrue(all(r["status"] != "DELETED" for r in rows))
        self.assertEqual(len(calls), 2)
        self.assertTrue(all("reference" in r for r in rows))

    def test_04_malformed_ref_visible_not_silently_dropped(self):
        reg = self.reg(parent_issue="not-a-github-issue",
                       history_refs=["https://example.org/issues/2", None, 42])
        _, rows, calls, errors = self.run_capture(reg)
        self.assertEqual(errors, [])
        self.assertEqual([r["status"] for r in rows], ["ERROR"] * 4)
        self.assertEqual([r["kind"] for r in rows],
                         ["parent_issue", "history_ref", "history_ref", "history_ref"])
        self.assertEqual(rows[0]["reference"], "not-a-github-issue")
        self.assertEqual(calls, [])

    def test_05_absent_history_key_is_backward_compatible(self):
        reg = self.reg()
        _, rows, calls, errors = self.run_capture(reg)
        self.assertIsNone(rows)
        self.assertEqual(calls, [])
        self.assertEqual(errors, [])

    def test_06_projection_in_summary_and_detail_without_agent(self):
        reg = self.reg(parent_issue=url(PRODUCT, 408),
                       history_refs=[url(CONTROL, 21)])
        root, expected, _, errors = self.run_capture(reg)
        self.assertEqual(errors, [])
        cache = root / "cache"
        built, _ = build_data.build_all(root, root / "output", cache_dir=cache)
        self.assertEqual(len(built), 1)
        self.assertEqual(built[0]["agents"], [])
        self.assertEqual(built[0]["lineage"], expected)
        project = json.loads((root / "output" / "project-case.json").read_text())
        summary = json.loads((root / "output" / "projects.json").read_text())
        self.assertEqual(project["lineage"], expected)
        self.assertEqual(summary[0]["lineage"], expected)

    def test_07_missing_lineage_keys_dont_add_project_output(self):
        reg = self.reg()
        root, rows, _, _ = self.run_capture(reg)
        built, _ = build_data.build_all(root, root / "output", cache_dir=root / "cache")
        self.assertIsNone(rows)
        self.assertNotIn("lineage", built[0])
        project = json.loads((root / "output" / "project-case.json").read_text())
        summary = json.loads((root / "output" / "projects.json").read_text())
        self.assertNotIn("lineage", project)
        self.assertNotIn("lineage", summary[0])

    def test_08_invalid_history_refs_shape_retained_as_error(self):
        reg = self.reg(history_refs={"unexpected": url(PRODUCT, 408)})
        _, rows, calls, errors = self.run_capture(reg)
        self.assertEqual(calls, [])
        self.assertEqual(errors, [])
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["status"], "ERROR")
        self.assertEqual(rows[0]["kind"], "history_ref")


if __name__ == "__main__":
    unittest.main(verbosity=2)
