#!/usr/bin/env python3
"""WP5a F7: sanitized #31 replay, resilient issue discovery and form-schema guard.

BaseCompatibleF7 runs unchanged on pinned merged WP3 and this WP5a head.
The six red tests rely on existing build_all / fetch_live_data.main entrypoints;
a failure at base is a wrong STATE or missing content, never a missing API.
"""
import copy
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import build_data
import fetch_live_data
import sync_owner_input_form

F7=json.loads((ROOT/"tests/fixtures/f7_owner_issue31_replay.json").read_text())
REPO=F7["repo"]


def f7_rows():
    return {row["number"]:row for row in
            build_data.build_owner_inputs(F7["issues"], F7["capture"])}


def capture_f7(label_exists=True):
    with tempfile.TemporaryDirectory() as tmp:
        root=Path(tmp)
        cache=root/"cache"
        by_number={row["number"]:row for row in F7["issues"]}
        labelled=[dict(row) for row in F7["issues"] if row["labels"]]
        full=[dict(row) for row in F7["issues"]]
        def fake_api(path):
            if "issues?state=all&labels=owner-input&per_page=100" in path:
                return labelled
            if "issues?state=all&per_page=100" in path:
                return full
            if path.endswith("/labels/owner-input"):
                return {"name":"owner-input"} if label_exists else None
            if path.endswith("/events?per_page=100"):
                return []
            return []
        def fake_issue(repo,number):
            if number==1:
                return {"number":1,"comments":[],"repository":repo}
            return copy.deepcopy(by_number.get(number))
        with mock.patch.object(fetch_live_data,"gh_api",side_effect=fake_api), \
             mock.patch.object(fetch_live_data,"fetch_issue",side_effect=fake_issue), \
             mock.patch.dict(os.environ,{"GITHUB_SHA":"a"*40}), \
             mock.patch.object(sys,"argv",["fetch_live_data.py","--root",str(root),
                "--repo",REPO,"--cache-dir",str(cache)]):
            fetch_live_data.main()
        capture=json.loads((cache/"capture-info.json").read_text())
        source_path=cache/"owner-inputs-source.json"
        source=json.loads(source_path.read_text()) if source_path.exists() else []
        return capture,source


class BaseCompatibleF7(unittest.TestCase):
    def test_f7_issue_form_project_target_type_text(self):
        row=f7_rows()[32]
        self.assertEqual(
            (row["project"],row.get("target"),row["type"],row["text"]),
            ("landing-live","OwnerTeammember","QUESTION","Please review progress."))

    def test_f7_title_body_project_mismatch_fails_closed(self):
        row=f7_rows()[31]
        self.assertEqual(row["status"],"NEEDS_CLARIFICATION")
        self.assertEqual(row.get("reason"),"project_mismatch")
        self.assertEqual(row["project"],"")
        self.assertIsNone(row["receipt"])
        self.assertTrue(row["needs_you"])
        self.assertEqual(row.get("project_claims"),
                         {"title":"landing-live","form":"grade9-pilot"})

    def test_f7_unlabelled_issue_is_flagged_and_pending(self):
        row=f7_rows()[33]
        self.assertEqual(row["status"],"NEEDS_CLARIFICATION")
        self.assertEqual(row.get("reason"),"label_missing")
        self.assertTrue(row.get("label_missing"))
        self.assertIn("label_missing",row.get("flags",[]))
        self.assertTrue(row["needs_you"])

    def test_f7_registered_projects_are_in_issue_form(self):
        template=ROOT/".github/ISSUE_TEMPLATE/owner-input.yml"
        self.assertEqual(sync_owner_input_form.generated_content(ROOT,template),
                         template.read_text(),
                         "a registered project was omitted from the form options")
        self.assertIn("landing-live",sync_owner_input_form.registry_projects(ROOT))

    def test_f7_fetches_unlabelled_title_in_addition_to_labelled_issues(self):
        capture,source=capture_f7()
        self.assertEqual(capture["status"],"ok")
        self.assertEqual({x["number"] for x in source},{31,32,33})
        self.assertEqual(next(x for x in source if x["number"]==33)["labels"],[])

    def test_f7_missing_repo_label_fails_the_publisher_capture_guard(self):
        capture,source=capture_f7(label_exists=False)
        self.assertEqual(capture["status"],"degraded")
        self.assertIn("owner_input_label_missing",capture["errors"])
        self.assertTrue(capture["owner_inputs_complete"])
        self.assertIn(33,{x["number"] for x in source})


class DetailedF7(unittest.TestCase):
    def test_f7_matching_project_preserves_exact_handled_receipt(self):
        issue=copy.deepcopy(F7["issues"][1])
        issue["comments"]=[{
            "id":32001,"created_at":"2026-10-15T15:12:00Z",
            "author_association":"MEMBER",
            "body":"HANDLED: owner-input #32 receipt: "
                   "https://github.com/"+REPO+"/issues/32#issuecomment-32001"
        }]
        row=build_data.build_owner_inputs([issue],F7["capture"])[0]
        self.assertEqual(row["status"],"HANDLED")
        self.assertEqual(row["project"],"landing-live")
        self.assertEqual(row["text"],"Please review progress.")
        self.assertEqual(row["receipt"],
                         "https://github.com/"+REPO+"/issues/32#issuecomment-32001")
        self.assertFalse(row["effective"])
        self.assertEqual(row["authority"],"UNVERIFIED")

    def test_f7_missing_label_not_dropped_in_build_all(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            reg=root/"logs"/"landing-live"/"registry.json"
            reg.parent.mkdir(parents=True)
            live_registry=json.loads(
                (ROOT/"logs"/"landing-live"/"registry.json").read_text())
            reg.write_text(json.dumps(live_registry))
            cache=root/"cache"
            cache.mkdir()
            (cache/"capture-info.json").write_text(json.dumps(F7["capture"]))
            (cache/"owner-inputs-source.json").write_text(
                json.dumps(F7["issues"]))
            build_data.build_all(root,root/"output",cache_dir=cache)
            rows=json.loads((root/"output/owner-inputs.json").read_text())
        self.assertIn(33,{r["number"] for r in rows})
        row=next(r for r in rows if r["number"]==33)
        self.assertEqual(row["reason"],"label_missing")
        self.assertTrue(row["needs_you"])

    def test_f7_new_registry_requires_updated_project_dropdown(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            (root/"logs"/"grade9-pilot").mkdir(parents=True)
            (root/"logs"/"new-project").mkdir()
            for name in ("grade9-pilot","new-project"):
                (root/"logs"/name/"registry.json").write_text(
                    json.dumps({"project":name}))
            f=root/".github/ISSUE_TEMPLATE/owner-input.yml"
            f.parent.mkdir(parents=True)
            f.write_text((ROOT/".github/ISSUE_TEMPLATE/owner-input.yml").read_text())
            expected=sync_owner_input_form.generated_content(root,f)
            self.assertNotEqual(f.read_text(),expected)
            f.write_text(expected)
            self.assertEqual(sync_owner_input_form.generated_content(root,f),
                             f.read_text())
            self.assertIn("        - new-project\n",expected)


if __name__=="__main__":
    unittest.main(verbosity=2)
