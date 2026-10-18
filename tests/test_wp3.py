#!/usr/bin/env python3
"""WP3 synthetic F4 multi-product-repo and observed-coordinator regressions."""
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from unittest import mock

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import build_data
import fetch_live_data

F4=json.loads((ROOT/"tests/fixtures/f4_two_repos.json").read_text())
HUB=F4["control_repository"]
NOW=datetime.fromisoformat(F4["now"])


def synthetic_project(name, *, status=None, inbox=None, now=NOW):
    registry=json.loads(json.dumps(F4[name]["registry"]))
    return build_data.build_project_data(
        ROOT,name,registry,{}, F4["inbox"]["comments"] if inbox is None else inbox,
        None,source_meta={"status":"ok","errors":[]},
        status_thread={} if status is None else status,now=now,
        registry_blob_sha="f"*40
    )[0]


def synthetic_build():
    with tempfile.TemporaryDirectory() as tmp:
        root=Path(tmp)
        for name in ("alpha","beta"):
            p=root/"logs"/name/"registry.json"
            p.parent.mkdir(parents=True)
            p.write_text(json.dumps(F4[name]["registry"]))
        cache=root/"cache"
        repos={
            (HUB,1):F4["inbox"],
            (F4["alpha"]["registry"]["repository"],12):F4["alpha"]["status"],
            (F4["alpha"]["registry"]["repository"],13):F4["alpha"]["evidence"],
            (F4["beta"]["registry"]["repository"],12):F4["beta"]["status"],
            (F4["beta"]["registry"]["repository"],13):F4["beta"]["evidence"],
        }
        observed=[]
        def fake_issue(repo,n):
            observed.append((repo,n))
            return json.loads(json.dumps(repos[(repo,n)])) if (repo,n) in repos else None
        with mock.patch.object(fetch_live_data,"fetch_issue",side_effect=fake_issue), \
             mock.patch.object(fetch_live_data,"gh_api",side_effect=lambda path: {"name":"owner-input"} if path.endswith("/labels/owner-input") else []), \
             mock.patch.dict(os.environ,{"GITHUB_SHA":"a"*40}), \
             mock.patch.object(sys,"argv",[
                 "fetch_live_data.py","--root",str(root),"--repo",HUB,
                 "--cache-dir",str(cache),
             ]):
            fetch_live_data.main()
        build_data.build_all(root,root/"out",cache_dir=cache)
        projects=json.loads((root/"out/projects.json").read_text())
        evidence={}
        for name in ("alpha","beta"):
            path=root/"out"/f"evidence-{name}-aabbccdd.json"
            evidence[name]=json.loads(path.read_text())
        alias=json.loads((root/"out/evidence-aabbccdd.json").read_text())
        capture=json.loads((cache/"capture-info.json").read_text())
        inbox=json.loads((cache/"inbox-1.json").read_text())
        return observed,projects,evidence,alias,capture,inbox


class BaseCompatibleWP3(unittest.TestCase):
    # These callable surfaces exist on both BASE and HEAD. The old product
    # fails by wrong STATE/output, never by an absent function or signature.
    def test_wp3_real_coordinator_receipt_is_observed(self):
        receipt=F4["alpha"]["status"]["comments"][0]
        project=synthetic_project("alpha",inbox=[receipt])
        self.assertEqual(project["freshness_status"],"RUNNING-observed")
        self.assertEqual(project["last_cycle_at"],"2026-10-15T15:50:00+00:00")

    def test_wp3_current_epoch_evidence_header_only(self):
        item={"comments":[{"id":1201,"author_association":"MEMBER",
            "body":"COORDINATOR EVIDENCE v1 · alpha · epoch 4 · 2026-10-15T15:50:00Z",
            "created_at":"2026-10-15T15:50:00Z",
            "updated_at":"2026-10-15T15:52:00Z"}]}
        project=synthetic_project("alpha",status=item)
        self.assertEqual(project["freshness_status"],"RUNNING-observed")

    def test_wp3_two_repositories_same_number_separate_evidence(self):
        observed,projects,evidence,alias,capture,inbox=synthetic_build()
        expected={(HUB,1),
                  ("example/product-alpha",12),("example/product-alpha",13),
                  ("example/product-beta",12),("example/product-beta",13)}
        self.assertEqual(set(observed),expected)
        self.assertEqual(capture["status"],"ok")
        self.assertEqual({p["repository"] for p in projects},
                         {"example/product-alpha","example/product-beta"})
        for name in ("alpha","beta"):
            raw=json.dumps(evidence[name])
            self.assertIn(name+"-ONLY",raw)
            self.assertNotIn(("beta" if name=="alpha" else "alpha")+"-ONLY",raw)
        self.assertEqual(alias.get("collision"),True)
        self.assertEqual(inbox,F4["inbox"]["comments"])

    def test_wp3_running_deploys_do_not_share_legacy_pages_group(self):
        workflow=(ROOT/".github/workflows/deploy.yml").read_text()
        # NextNudge may commit data, but it must never become a second Pages publisher.
        nextnudge=(ROOT/".github/workflows/nextnudge-save.yml").read_text()
        self.assertIn("contents: write",nextnudge)
        self.assertIn("issues: write",nextnudge)
        self.assertNotIn("pages: write",nextnudge)
        self.assertIn("cancel-in-progress: false",nextnudge)
        self.assertEqual(content_writers,["nextnudge-save.yml"])
        self.assertIn("group: landing-live-single-publisher-",workflow)
        self.assertIn("cancel-in-progress: false",workflow)
        self.assertNotIn("cancel-in-progress: true",workflow)


class WP3Additional(unittest.TestCase):
    def test_wp3_wrong_project_epoch_and_unparseable_unknown(self):
        status={"comments":[
            {"id":1201,"author_association":"MEMBER","body":"COORDINATOR RECEIPT · beta · epoch4 · 2026-10-15T15:55:00Z"},
            {"id":1202,"author_association":"MEMBER","body":"COORDINATOR RECEIPT · alpha · epoch3 · 2026-10-15T15:55:00Z"},
            {"id":1203,"author_association":"MEMBER","body":"COORDINATOR RECEIPT · alpha · epoch4 · NOT-A-TIMESTAMP"},
        ]}
        p=synthetic_project("alpha",status=status,inbox=[])
        self.assertEqual(p["freshness_status"],"UNKNOWN")

    def test_wp3_30min_boundary_from_receipt(self):
        for age,expected in [(1800,"RUNNING-observed"),(1801,"STALE")]:
            with self.subTest(age_seconds=age):
                when=(NOW-timedelta(seconds=age)).isoformat()
                comment={"author_association":"MEMBER","body":f"COORDINATOR RECEIPT · alpha · epoch4 · {when}"}
                p=synthetic_project("alpha",inbox=[comment])
                self.assertEqual(p["freshness_status"],expected)

    def test_wp3_status_edit_time_must_be_pinned_and_parseable(self):
        original=F4["alpha"]["status"]["comments"][0]
        comment={"id":1201,"author_association":"MEMBER","body":"COORDINATOR EVIDENCE v1 · alpha · epoch 4 · no clock",
                 "updated_at":"2026-10-15T15:52:00Z"}
        good=build_data.last_completed_cycle(
            {"comments":[comment]},"alpha",NOW,4,inbox=[],
            pinned_comment_id=1201,epoch_since="2026-10-15T15:00:00Z")
        bad=build_data.last_completed_cycle(
            {"comments":[comment]},"alpha",NOW,4,inbox=[],
            pinned_comment_id=999,epoch_since="2026-10-15T15:00:00Z")
        self.assertEqual(good,"2026-10-15T15:52:00+00:00")
        self.assertIsNone(bad)
        self.assertIsNone(build_data.last_completed_cycle(
            {"comments":[{"id":1201,"author_association":"MEMBER","body":"random changed status",
                          "updated_at":"2026-10-15T15:52:00Z"}]},
            "alpha",NOW,4,inbox=[],pinned_comment_id=1201,
            epoch_since="2026-10-15T15:00:00Z"))


    def test_wp3_foreign_author_receipt_cannot_spoof_observed(self):
        # Negative control: the earlier WP3 implementation accepted ANY
        # public commenter whose body imitated a coordinator receipt.
        receipt=F4["alpha"]["status"]["comments"][0]
        self.assertEqual(receipt["author_association"],"MEMBER")
        foreign=dict(receipt,author_association="CONTRIBUTOR")
        injected=synthetic_project("alpha",inbox=[foreign])
        self.assertEqual(injected["freshness_status"],"UNKNOWN")
        self.assertIsNone(injected["last_cycle_at"])
        verified=synthetic_project("alpha",inbox=[receipt])
        self.assertEqual(verified["freshness_status"],"RUNNING-observed")
        self.assertEqual(verified["last_cycle_at"],"2026-10-15T15:50:00+00:00")
        # Even the exact registry-pinned status comment's edit clock
        # cannot turn a foreign-author post green.
        pinned=dict(foreign,id=1201,updated_at="2026-10-15T15:52:00Z")
        self.assertIsNone(build_data.last_completed_cycle(
            {"comments":[pinned]},"alpha",NOW,4,inbox=[],
            pinned_comment_id=1201,epoch_since="2026-10-15T15:00:00Z"))

    def test_wp3_exact_author_association_allowlist(self):
        receipt=F4["alpha"]["status"]["comments"][0]
        for association in ("OWNER","MEMBER","COLLABORATOR"):
            with self.subTest(association=association):
                row=synthetic_project(
                    "alpha",inbox=[dict(receipt,author_association=association)])
                self.assertEqual(row["freshness_status"],"RUNNING-observed")
        for association in ("CONTRIBUTOR","FIRST_TIME_CONTRIBUTOR",
                            "FIRST_TIMER","NONE",None,"member"):
            with self.subTest(association=association):
                row=synthetic_project(
                    "alpha",inbox=[dict(receipt,author_association=association)])
                self.assertEqual(row["freshness_status"],"UNKNOWN")

    def test_wp3_liveness_limit_declared_in_project_data_and_visible_page(self):
        row=synthetic_project("alpha")
        note=row["liveness_observation_limit"]
        self.assertIn("team roles share one GitHub account",note)
        self.assertIn("not identity proof",note)
        page=(ROOT/"site/js/home.js").read_text()
        self.assertIn("Team roles share one GitHub account",page)
        self.assertIn("actual role cannot be distinguished",page)

    def test_wp3_no_other_workflow_uses_legacy_pages_group_or_deploys(self):
        import re
        workflows=sorted((ROOT/".github/workflows").glob("*.yml"))
        self.assertEqual({p.name for p in workflows},
                         {"blank.yml","deploy.yml","landing-tests.yml","ultra-economy-tests.yml",
                          "nextnudge-save.yml"})
        content_writers=[]
        for path in workflows:
            content=path.read_text()
            if re.search(r'^\s*contents:\s*write\s*
            self.assertIsNone(
                re.search(r'^\s*group:\s*["\x27]?pages["\x27]?\s*$',
                          content,re.MULTILINE),path.name)
            if path.name!="deploy.yml":
                self.assertNotIn("uses: actions/deploy-pages@",content)
                self.assertNotIn("uses: actions/upload-pages-artifact@",content)
        self.assertIn("group: landing-live-single-publisher-",
                      (ROOT/".github/workflows/deploy.yml").read_text())


if __name__=="__main__":
    unittest.main(verbosity=2)
,content,re.MULTILINE):
                content_writers.append(path.name)
            self.assertIsNone(
                re.search(r'^\s*group:\s*["\x27]?pages["\x27]?\s*$',
                          content,re.MULTILINE),path.name)
            if path.name!="deploy.yml":
                self.assertNotIn("uses: actions/deploy-pages@",content)
                self.assertNotIn("uses: actions/upload-pages-artifact@",content)
        self.assertIn("group: landing-live-single-publisher-",
                      (ROOT/".github/workflows/deploy.yml").read_text())


if __name__=="__main__":
    unittest.main(verbosity=2)
