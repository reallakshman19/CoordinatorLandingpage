#!/usr/bin/env python3
"""WP12 real registries + synthetic bounded v3.6/PR HEAD projections."""
import copy
import json
from datetime import datetime, timezone
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build_data
import fetch_live_data

CII = "cii-method-c"
XML = "xml229-output"
REPO = "reallakshman19/XML_Compare_Utilities"
OTHER = "reallakshman19/3D_Converters"
HUB = "reallakshman19/CoordinatorLandingpage"
NOW = datetime(2026, 10, 16, 14, tzinfo=timezone.utc)
O1 = f"https://github.com/{REPO}/issues/201"
O2 = f"https://github.com/{REPO}/issues/202"
PR = f"https://github.com/{REPO}/pull/106"
OLD = "a" * 40
NEW = "b" * 40


def registry(name=CII):
    return json.loads((ROOT / "logs" / name / "registry.json")
                      .read_text(encoding="utf-8"))


def projected(reg, child_observations=None, pr_observation=None):
    return build_data.build_project_data(
        ROOT, reg["project"], reg, {}, [], None,
        source_meta={"status": "ok", "errors": []},
        status_thread={}, now=NOW, registry_blob_sha="f" * 40,
        child_observations=child_observations, pr_observation=pr_observation)[0]


class WP12Source(unittest.TestCase):
    def test_wp12_real_hold_and_reports_to_isolation(self):
        src = registry()
        data = projected(src)
        self.assertEqual(data["freshness_status"], "HOLD")
        self.assertTrue(data.get("hold_report", {}).get("active"))
        self.assertEqual(data["hold_report"]["recorded"], "Owner HOLD 16 Oct 18:0x")
        self.assertEqual(data["hold_report"]["since"], "")  # no invented exact time
        self.assertEqual([a["status"] for a in data["agents"]], ["hold", "hold"])
        tree = data.get("reporting_tree") or []
        self.assertEqual(len(tree), 2)
        self.assertEqual(tree[1]["reports_to"], "6ad1ce42")
        self.assertIsNone(tree[0]["reports_to"])
        self.assertEqual(projected(registry(XML))["freshness_status"], "HOLD")

    def test_wp12_precise_owner_hold_since_and_dangling_edge(self):
        src = registry()
        src["control"]["hold"] = {
            "since": "2026-10-16T18:03:00+04:00",
            "owner_words": "Pause all work pending Owner review."
        }
        src["agents"][1]["reports_to"] = "0badc0de"
        data = projected(src)
        self.assertEqual(data.get("hold_report", {}).get("since"),
                         "2026-10-16T18:03:00+04:00")
        self.assertEqual(data["hold_report"]["owner_words"],
                         "Pause all work pending Owner review.")
        self.assertIsNone(data["reporting_tree"][1]["reports_to"])

    def test_wp12_v36_child_titles_count_and_strict_repo_fence(self):
        src = registry()
        src["children"] = [O1, {"url": O2}]
        observed = [
            {"url": O1, "repository": REPO,
             "title": "[V3.6][O1][DONE] Method C check"},
            {"url": O2, "repository": REPO,
             "title": "[V3.6][O2][IN_PROGRESS] Review"},
        ]
        data = projected(src, observed)
        progress = data.get("child_progress") or {}
        self.assertEqual((progress.get("status"),progress.get("done"),
                          progress.get("total")), ("known",1,2))
        self.assertEqual([x["state"] for x in progress["items"]],
                         ["DONE","IN_PROGRESS"])
        self.assertTrue(all(x["url"].startswith(f"https://github.com/{REPO}/")
                            for x in progress["items"]))
        self.assertEqual(projected(src, observed[:1])["child_progress"]["status"],
                         "unknown")
        src["children"].append(f"https://github.com/{OTHER}/issues/201")
        self.assertEqual(projected(src, observed)["child_progress"]["status"],
                         "unknown")

    def test_wp12_v36_over_limit_and_invalid_title_fail_closed(self):
        src = registry()
        src["children"] = [f"https://github.com/{REPO}/issues/{i}"
                           for i in range(201, 214)]
        self.assertEqual(projected(src)["child_progress"]["status"], "unknown")
        src["children"] = [O1]
        data = projected(src, [{"url": O1, "repository": REPO,
                                "title": "[V3.6][O1][COMPLETE] Wrong marker"}])
        self.assertEqual(data["child_progress"]["status"], "unknown")

    def test_wp12_evidence_head_moved_current_and_unknown(self):
        src = registry()
        src["evidence_head"] = OLD
        src["evidence_pr"] = PR
        stale = projected(src, pr_observation={
            "url": PR, "repository": REPO, "head": NEW})
        self.assertEqual(stale.get("evidence_head_status", {}).get("status"),
                         "superseded")
        self.assertEqual(stale["evidence_head_status"]["current_head"], NEW)
        self.assertEqual(projected(src, pr_observation={
            "url": PR, "repository": REPO, "head": OLD
        })["evidence_head_status"]["status"], "current")
        self.assertEqual(projected(src)["evidence_head_status"]["status"], "unknown")
        src["evidence_pr"] = f"https://github.com/{OTHER}/pull/106"
        self.assertEqual(projected(src, {"unused":True})["evidence_head_status"]["status"],
                         "unknown")

    def test_wp12_bounded_read_only_fetch_and_registry_cache(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            src = registry()
            src["children"] = [O1, O2]
            src["evidence_head"] = OLD
            src["evidence_pr"] = PR
            path = root / "logs" / CII / "registry.json"
            path.parent.mkdir(parents=True)
            path.write_text(json.dumps(src), encoding="utf-8")
            calls = []
            def api(endpoint):
                calls.append(endpoint)
                if endpoint.endswith("/issues/201"):
                    return {"number": 201, "html_url": O1,
                            "title": "[V3.6][O1][DONE] Work"}
                if endpoint.endswith("/issues/202"):
                    return {"number": 202, "html_url": O2,
                            "title": "[V3.6][O2][PLANNED] Work"}
                if endpoint.endswith("/pulls/106"):
                    return {"number": 106, "head": {"sha": NEW}}
                return None
            errors = []
            with mock.patch.object(fetch_live_data, "gh_api", side_effect=api):
                fetch_live_data.capture_project_extras(
                    root, root / "cache", {CII: {"repository": REPO}}, errors)
            self.assertEqual(errors, [])
            self.assertEqual(len(calls), 3)
            self.assertEqual(set(calls), {
                f"/repos/{REPO}/issues/201", f"/repos/{REPO}/issues/202",
                f"/repos/{REPO}/pulls/106",
            })
            build_data.build_all(root, root / "out", cache_dir=root / "cache")
            data = json.loads((root / "out" / f"project-{CII}.json").read_text())
            self.assertEqual((data["child_progress"]["done"],
                              data["child_progress"]["total"]), (1,2))
            self.assertEqual(data["evidence_head_status"]["status"], "superseded")



class WP12BaseCompatible(unittest.TestCase):
    """Runs unchanged HEAD assertions with only the pinned-base call contract."""

    def basic(self, reg):
        return build_data.build_project_data(
            ROOT, reg["project"], reg, {}, [], None,
            source_meta={"status": "ok", "errors": []},
            status_thread={}, now=NOW, registry_blob_sha="f" * 40)[0]

    def test_wp12_hold_report_was_missing_on_main(self):
        result = self.basic(registry())
        self.assertTrue((result.get("hold_report") or {}).get("active"))

    def test_wp12_reporting_lines_were_missing_on_main(self):
        result = self.basic(registry())
        rows = result.get("reporting_tree") or []
        self.assertEqual(len(rows), 2)

    def test_wp12_children_unknown_without_observation_on_main(self):
        reg = registry()
        reg["children"] = [O1]
        result = self.basic(reg)
        self.assertEqual((result.get("child_progress") or {}).get("status"),
                         "unknown")

    def test_wp12_evidence_head_unknown_without_pr_observation_on_main(self):
        reg = registry()
        reg["evidence_head"] = OLD
        reg["evidence_pr"] = PR
        result = self.basic(reg)
        self.assertEqual((result.get("evidence_head_status") or {}).get("status"),
                         "unknown")


if __name__ == "__main__":
    unittest.main(verbosity=2)
