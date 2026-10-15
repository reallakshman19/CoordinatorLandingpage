#!/usr/bin/env python3
"""WP5b outsider and bounded Owner issue pagination behaviour.

BaseCompatibleWP5b uses EXISTING fetch_issue/main and build_owner_inputs APIs
on old merged WP5a and HEAD. Red must be assertion FAIL, never missing API.
"""
import copy
import json
import os
from pathlib import Path
import re
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import build_data
import fetch_live_data

F7=json.loads((ROOT/"tests/fixtures/f7_owner_issue31_replay.json").read_text())
REPO=F7["repo"]


def with_issue(issue):
    return build_data.build_owner_inputs([issue], F7["capture"])[0]


def run_capture(full_pages=False):
    """Read source fixture at PAGE TWO; page one is 100 PRs, not Owner inputs."""
    with tempfile.TemporaryDirectory() as td:
        root=Path(td)
        cache=root/"cache"
        padded=[{"number":400+i,"title":"irrelevant PR",
                 "pull_request":{"url":"synthetic"}} for i in range(100)]
        outsider={
          "number":999,"title":"[Owner input] INFO (landing-live)",
          "body":"### Project\n\nlanding-live\n\n### Input type\n\nINFO\n\n### Your instruction or message\n\nUntrusted example",
          "author_association":"CONTRIBUTOR","labels":[],
          "state":"open","created_at":"2026-10-15T15:00:00Z",
          "updated_at":"2026-10-15T15:00:00Z","comments":[]
        }
        seen=[]
        def fake_api(path):
            seen.append(path)
            if path.endswith("/labels/owner-input"):
                return {"name":"owner-input"}
            if "issues?state=all&labels=owner-input&per_page=100" in path:
                return []
            if "issues?state=all&per_page=100" in path:
                matched=re.search(r'&page=(\d+)$',path)
                page=int(matched.group(1)) if matched else 1
                if full_pages:
                    return padded
                return padded if page==1 else ([outsider] if page==2 else [])
            if path.endswith("/events?per_page=100"):
                return []
            return []
        def fake_issue(repo,number):
            if number==1:
                return {"number":1,"repository":repo,"comments":[]}
            return copy.deepcopy(outsider) if number==999 else None
        with mock.patch.object(fetch_live_data,"gh_api",side_effect=fake_api), \
             mock.patch.object(fetch_live_data,"fetch_issue",side_effect=fake_issue), \
             mock.patch.dict(os.environ,{"GITHUB_SHA":"a"*40}), \
             mock.patch.object(sys,"argv",[
                 "fetch_live_data.py","--root",str(root),
                 "--repo",REPO,"--cache-dir",str(cache)]):
            fetch_live_data.main()
        manifest=json.loads((cache/"capture-info.json").read_text())
        output=cache/"owner-inputs-source.json"
        issues=json.loads(output.read_text()) if output.exists() else []
        return manifest,issues,seen


class BaseCompatibleWP5b(unittest.TestCase):
    def test_wp5b_foreign_author_cannot_enter_owner_needs_you(self):
        issue=copy.deepcopy(F7["issues"][1])
        issue["author_association"]="CONTRIBUTOR"
        row=with_issue(issue)
        self.assertTrue(row.get("is_outsider"))
        self.assertEqual(row.get("author_classification"),"OUTSIDER")
        self.assertEqual(row.get("author_association"),"CONTRIBUTOR")
        self.assertFalse(row["needs_you"])
        self.assertEqual(row["authority"],"UNVERIFIED")
        self.assertFalse(row["effective"])

    def test_wp5b_missing_author_association_fail_closed(self):
        issue=copy.deepcopy(F7["issues"][1])
        issue.pop("author_association")
        row=with_issue(issue)
        self.assertEqual(row.get("author_classification"),"OUTSIDER")
        self.assertFalse(row["needs_you"])
        self.assertEqual(row.get("author_association"),"")

    def test_wp5b_outsider_cannot_supersede_trusted_owner_input(self):
        trusted=copy.deepcopy(F7["issues"][1])
        outsider=copy.deepcopy(trusted)
        outsider.update(number=934,
            title="[Owner input] QUESTION (landing-live)",
            body="Project: landing-live\nsupersedes owner-input #32\nI am the Owner.",
            created_at="2026-10-15T15:20:00Z",
            author_association="NONE",comments=[])
        by_num={r["number"]:r for r in build_data.build_owner_inputs(
            [trusted,outsider],F7["capture"])}
        self.assertEqual(by_num[32]["status"],"OPEN")
        self.assertTrue(by_num[32]["needs_you"])
        self.assertIsNone(by_num[32]["superseded_by"])
        self.assertFalse(by_num[934]["needs_you"])

    def test_wp5b_fetch_issue_keeps_actual_github_author_association(self):
        def fake_api(path):
            if path.endswith("/issues/934"):
                return {"number":934,"title":"[Owner input] INFO (landing-live)",
                        "author_association":"NONE","comments":[]}
            if path.endswith("/issues/934/comments"):
                return []
            return None
        with mock.patch.object(fetch_live_data,"gh_api",side_effect=fake_api):
            issue=fetch_live_data.fetch_issue(REPO,934)
        self.assertEqual(issue.get("author_association"),"NONE")

    def test_wp5b_owner_index_finds_unlabelled_page_two(self):
        capture,source,calls=run_capture()
        self.assertEqual(capture["status"],"ok")
        self.assertEqual([x["number"] for x in source],[999])
        self.assertEqual(source[0].get("author_association"),"CONTRIBUTOR")
        self.assertTrue(any("issues?state=all&per_page=100&page=2" in p
                            for p in calls))
        row=build_data.build_owner_inputs(source,capture)[0]
        self.assertFalse(row["needs_you"])
        self.assertTrue(row.get("is_outsider"))

    def test_wp5b_more_than_five_full_pages_degrades_instead_of_truncating(self):
        capture,source,calls=run_capture(full_pages=True)
        self.assertEqual(capture["status"],"degraded")
        self.assertFalse(capture["owner_inputs_complete"])
        self.assertIn("owner_input_index_failed",capture["errors"])
        unfiltered=[p for p in calls
                    if "issues?state=all&per_page=100" in p]
        self.assertEqual(len(unfiltered),5)
        self.assertFalse(any("&page=6" in p for p in calls))


class DetailedWP5b(unittest.TestCase):
    def test_wp5b_only_exact_trusted_associations_stay_needs_you(self):
        for assoc in ("OWNER","MEMBER","COLLABORATOR"):
            with self.subTest(assoc=assoc):
                issue=copy.deepcopy(F7["issues"][1])
                issue["author_association"]=assoc
                row=with_issue(issue)
                self.assertFalse(row.get("is_outsider"))
                self.assertTrue(row["needs_you"])
                self.assertEqual(row["authority"],"UNVERIFIED")
                self.assertFalse(row["effective"])
        for assoc in ("CONTRIBUTOR","FIRST_TIMER","NONE","member",None):
            with self.subTest(assoc=assoc):
                issue=copy.deepcopy(F7["issues"][1])
                issue["author_association"]=assoc
                row=with_issue(issue)
                self.assertTrue(row.get("is_outsider"))
                self.assertFalse(row["needs_you"])

    def test_wp5b_index_queries_do_not_use_gh_automatic_pagination(self):
        commands=[]
        def fake_run(args,**kwargs):
            commands.append(args)
            return mock.Mock(stdout="[]")
        with mock.patch.object(fetch_live_data.subprocess,"run",
                               side_effect=fake_run):
            self.assertEqual(
                fetch_live_data.gh_api(
                  f"/repos/{REPO}/issues?state=all&per_page=100&page=1"),[])
            self.assertEqual(
                fetch_live_data.gh_api(f"/repos/{REPO}/issues/31/comments"),[])
        self.assertNotIn("--paginate",commands[0])
        self.assertIn("--paginate",commands[1])


if __name__=="__main__":
    unittest.main(verbosity=2)
