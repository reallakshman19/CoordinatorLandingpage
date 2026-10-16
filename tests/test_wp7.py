#!/usr/bin/env python3
"""WP7: page -> saved JSON -> receipt -> trace, without issue writes."""
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import build_data
import owner_json

REPO="reallakshman19/CoordinatorLandingpage"
SHA="a"*40
OLDER="OI-20261015-163000-abcd"
NEWER="OI-20261015-163100-1234"

def record(identifier=OLDER,project="landing-live",**overrides):
    value={"id":identifier,"project":project,"target":"TeamCoordinator",
           "type":"QUESTION","text":"Please confirm the next step.",
           "replaces":None,"created_at":"2026-10-15T16:30:00Z" if identifier==OLDER
           else "2026-10-15T16:31:00Z"}
    value.update(overrides)
    return value

def make_repo(root,old=True,new=False,raw=None,receipts=None):
    folder=Path(root)/"logs"/"landing-live"
    folder.mkdir(parents=True)
    (folder/"registry.json").write_text(json.dumps({
        "project":"landing-live","repository":REPO}),encoding="utf-8")
    inputs=folder/"inputs"
    inputs.mkdir()
    if old:
        (inputs/(OLDER+".json")).write_text(
            json.dumps(record()) if raw is None else raw,encoding="utf-8")
    if new:
        (inputs/(NEWER+".json")).write_text(
            json.dumps(record(NEWER,replaces=OLDER)),encoding="utf-8")
    if receipts is not None:
        (folder/"receipts.jsonl").write_text(
            "\n".join(json.dumps(x) for x in receipts)+"\n",encoding="utf-8")

def resolver(repo,path):
    return {"sha":SHA,"author":"verified-user","association":"MEMBER"}

def untrusted(repo,path):
    return {"sha":SHA,"author":"foreign-user","association":"UNKNOWN"}

def receipt(state="HANDLED",links=None):
    return {"input":OLDER,"state":state,"at":"2026-10-15T16:32:00Z",
            "by":"TeamCoordinator","note":"Reviewed","links":(
            ["https://github.com/"+REPO+"/issues/22#issuecomment-123"] if links is None else links)}

def projected(root,resolve=resolver):
    return owner_json.read_committed_inputs(root,resolver=resolve)

def built(root):
    cache=Path(root)/"cache"
    cache.mkdir()
    (cache/"capture-info.json").write_text(
        json.dumps({"status":"ok","issues_fetched":[1],
                    "owner_inputs_complete":True}))
    (cache/"owner-inputs-source.json").write_text("[]")
    out=Path(root)/"out"
    build_data.build_all(Path(root),out,cache_dir=cache)
    return json.loads((out/"owner-inputs.json").read_text())

class BaseCompatibleWP7(unittest.TestCase):
    def test_wp7_committed_json_appears_in_built_owner_inputs(self):
        with tempfile.TemporaryDirectory() as td:
            make_repo(td)
            with mock.patch.object(owner_json,"github_provenance",side_effect=resolver):
                rows=built(td)
        self.assertIn(OLDER,[x.get("id") for x in rows])

    def test_wp7_json_authority_remains_unverified(self):
        with tempfile.TemporaryDirectory() as td:
            make_repo(td)
            with mock.patch.object(owner_json,"github_provenance",side_effect=resolver):
                rows=built(td)
        self.assertTrue(any(x.get("id")==OLDER and x.get("authority")=="UNVERIFIED"
                            and x.get("effective") is False for x in rows))

    def test_wp7_bad_json_schema_fails_to_clarification(self):
        with tempfile.TemporaryDirectory() as td:
            make_repo(td,raw=json.dumps({**record(),"unrecognized":"x"}))
            with mock.patch.object(owner_json,"github_provenance",side_effect=resolver):
                rows=built(td)
        self.assertTrue(any(x.get("id")==OLDER and x.get("status")=="NEEDS_CLARIFICATION"
                            and x.get("reason")=="schema_keys" for x in rows))

    def test_wp7_json_replacement_marks_previous_superseded(self):
        with tempfile.TemporaryDirectory() as td:
            make_repo(td,new=True)
            with mock.patch.object(owner_json,"github_provenance",side_effect=resolver):
                rows=built(td)
        self.assertTrue(any(x.get("id")==OLDER and x.get("status")=="SUPERSEDED"
                            and x.get("superseded_by")==NEWER for x in rows))

    def test_wp7_untrusted_committer_does_not_enter_needs_you(self):
        with tempfile.TemporaryDirectory() as td:
            make_repo(td)
            with mock.patch.object(owner_json,"github_provenance",side_effect=untrusted):
                rows=built(td)
        self.assertTrue(any(x.get("id")==OLDER and x.get("is_outsider") is True
                            and x.get("needs_you") is False for x in rows))

    def test_wp7_issue_foreign_author_ack_does_not_change_state(self):
        issue={"number":777,"title":"[Owner input] INFO (landing-live)",
               "body":"Project: landing-live","labels":[{"name":"owner-input"}],
               "author_association":"MEMBER","events_complete":True,
               "created_at":"2026-10-15T16:00:00Z","comments":[{
                 "id":77701,"body":"ACK: owner-input #777",
                 "author_association":"CONTRIBUTOR","created_at":"2026-10-15T16:01:00Z"}]}
        capture={"status":"ok","issues_fetched":[1],"owner_inputs_complete":True}
        row=build_data.build_owner_inputs([issue],capture)[0]
        self.assertEqual(row["status"],"OPEN")

    def test_wp7_issue_foreign_repo_trace_link_is_not_evidence(self):
        issue={"number":778,"title":"[Owner input] INFO (landing-live)",
               "body":"Project: landing-live","labels":[{"name":"owner-input"}],
               "author_association":"MEMBER","events_complete":True,
               "created_at":"2026-10-15T16:00:00Z","comments":[{
                "id":77801,"body":"Sent to agent: https://github.com/other/elsewhere/issues/99",
                "author_association":"MEMBER","created_at":"2026-10-15T16:01:00Z"}]}
        capture={"status":"ok","issues_fetched":[1],"owner_inputs_complete":True}
        row=build_data.build_owner_inputs([issue],capture)[0]
        self.assertIsNone((row.get("trace",{}).get("steps",{}) or {}).get("sent"))


class DetailedWP7(unittest.TestCase):

    def test_wp7_checked_in_receipts_fixture_replays_ack_then_handled(self):
        fixture=ROOT/"tests/fixtures/wp7_receipts.jsonl"
        source=[json.loads(line) for line in fixture.read_text().splitlines()]
        self.assertEqual([x["state"] for x in source],["ACK","HANDLED"])
        with tempfile.TemporaryDirectory() as td:
            make_repo(td,receipts=source)
            row=projected(td)[0]
        self.assertEqual(row["status"],"HANDLED")
        self.assertTrue(row["receipt"].endswith("receipts.jsonl#L2"))
        self.assertTrue(row["trace"]["steps"]["result"]["accepted"])

    def test_wp7_timestamp_or_filename_mismatch_stays_clarification(self):
        with tempfile.TemporaryDirectory() as td:
            make_repo(td,raw=json.dumps(record(created_at="2026-10-15T16:31:00Z")))
            row=projected(td)[0]
        self.assertEqual(row["status"],"NEEDS_CLARIFICATION")
        self.assertEqual(row["reason"],"created_at")

    def test_wp7_receipt_handled_requires_actual_link(self):
        with tempfile.TemporaryDirectory() as td:
            make_repo(td,receipts=[receipt(links=[])])
            self.assertNotEqual(projected(td)[0]["status"],"HANDLED")
            (Path(td)/"logs/landing-live/receipts.jsonl").write_text(
                json.dumps(receipt())+"\n")
            row=projected(td)[0]
            self.assertEqual(row["status"],"HANDLED")
            self.assertTrue(row["receipt"].endswith("receipts.jsonl#L1"))
            self.assertTrue(row["trace"]["steps"]["result"]["url"])

    def test_wp7_latest_invalid_receipt_cannot_inherit_old_handled(self):
        with tempfile.TemporaryDirectory() as td:
            make_repo(td,receipts=[receipt(),receipt(links=[])])
            row=projected(td)[0]
        self.assertNotEqual(row["status"],"HANDLED")

    def test_wp7_validates_wrong_project_path_and_id_timestamp(self):
        with tempfile.TemporaryDirectory() as td:
            make_repo(td,raw=json.dumps(record(project="grade9-pilot")))
            row=projected(td)[0]
        self.assertEqual(row["status"],"NEEDS_CLARIFICATION")
        self.assertIn("project_or_path_mismatch",row["flags"])

    def test_wp7_associated_committer_only_no_by_spoof(self):
        with tempfile.TemporaryDirectory() as td:
            make_repo(td,receipts=[receipt()])
            row=projected(td,untrusted)[0]
        self.assertNotEqual(row["status"],"HANDLED")
        self.assertTrue(row["is_outsider"])
        self.assertFalse(row["needs_you"])

    def test_wp7_external_link_blocked_and_registered_product_allowed(self):
        with tempfile.TemporaryDirectory() as td:
            make_repo(td,receipts=[receipt(links=["https://github.com/evil/elsewhere/issues/10"])])
            self.assertNotEqual(projected(td)[0]["status"],"HANDLED")
        self.assertTrue(owner_json.linked_repo("https://github.com/product/project/issues/1",
                                               {REPO,"product/project"}))
        self.assertFalse(owner_json.linked_repo("https://github.com/evil/elsewhere/issues/1",
                                                {REPO,"product/project"}))

    def test_wp7_receipt_ack_has_associated_commit_permalink(self):
        with tempfile.TemporaryDirectory() as td:
            make_repo(td,receipts=[receipt("ACK",[])])
            row=projected(td)[0]
        self.assertEqual(row["status"],"ACKNOWLEDGED")
        self.assertIn("/blob/"+SHA+"/logs/",row["trace"]["steps"]["ack"]["url"])


class WP8cInputSafety(unittest.TestCase):
    """WP8c negative controls. Keep these independent of older WP7 assertions."""

    def test_wp8c_self_replacement_is_invalid_not_open(self):
        with tempfile.TemporaryDirectory() as td:
            make_repo(td, raw=json.dumps(record(replaces=OLDER)))
            row = projected(td)[0]
        self.assertEqual(row["status"], "NEEDS_CLARIFICATION")
        self.assertIn("replaces", row["flags"])
        self.assertIsNone(row["superseded_by"])

    def test_wp8c_unknown_replacement_is_invalid_not_open(self):
        with tempfile.TemporaryDirectory() as td:
            make_repo(td, raw=json.dumps(record(replaces=NEWER)))
            row = projected(td)[0]
        self.assertEqual(row["status"], "NEEDS_CLARIFICATION")
        self.assertIn("replaces", row["flags"])

    def test_wp8c_id_path_timestamp_and_length_limits_exact(self):
        valid = record(target="t" * 160, type="T" * 64, text="x" * 1500)
        self.assertEqual(owner_json.schema_errors(valid, OLDER, "landing-live",
                          {"landing-live": REPO}), [])
        cases = [
            ("target_empty", record(target=""), "target"),
            ("target_161", record(target="t" * 161), "target"),
            ("type_empty", record(type=""), "type"),
            ("type_65", record(type="T" * 65), "type"),
            ("text_empty", record(text=""), "text"),
            ("text_1501", record(text="x" * 1501), "text"),
            ("bad_replaces", record(replaces="../"), "replaces"),
            ("id_wrong_path", record(NEWER), "id_or_path_mismatch"),
            ("time_wrong_id", record(created_at="2026-10-15T16:31:00Z"), "created_at"),
            ("project_wrong_path", record(project="grade9-pilot"), "project_or_path_mismatch"),
        ]
        for name, obj, expected in cases:
            with self.subTest(name=name):
                self.assertIn(expected, owner_json.schema_errors(
                    obj, OLDER, "landing-live", {"landing-live": REPO}))

    def test_wp8c_non_json_and_non_object_fail_closed(self):
        for raw in ("{", "[]", "null", '"not an object"'):
            with self.subTest(raw=raw), tempfile.TemporaryDirectory() as td:
                make_repo(td, raw=raw)
                row = projected(td)[0]
                self.assertEqual(row["status"], "NEEDS_CLARIFICATION")
                self.assertIn("schema_keys", row["flags"])
                self.assertFalse(row["trace"]["steps"]["result"])

    def test_wp8c_foreign_handled_and_clarification_comments_cannot_count(self):
        number = 813
        base_issue = {
            "number": number, "title": "[Owner input] INFO (landing-live)",
            "body": "Project: landing-live", "labels": [{"name": "owner-input"}],
            "author_association": "MEMBER", "events_complete": True,
            "created_at": "2026-10-15T16:00:00Z", "comments": [],
        }
        capture = {"status": "ok", "issues_fetched": [1],
                   "owner_inputs_complete": True}
        receipt_url = (f"https://github.com/{REPO}/issues/{number}"
                       "#issuecomment-81303")
        comments = [
            {"id": 81301, "body": f"ACK: owner-input #{number}",
             "author_association": "MEMBER", "created_at": "2026-10-15T16:01:00Z"},
            {"id": 81302, "body": f"NEEDS CLARIFICATION: owner-input #{number} more info",
             "author_association": "CONTRIBUTOR", "created_at": "2026-10-15T16:02:00Z"},
            {"id": 81303, "body": f"HANDLED: owner-input #{number} receipt: {receipt_url}",
             "author_association": "NONE", "created_at": "2026-10-15T16:03:00Z"},
        ]
        issue = dict(base_issue, comments=comments)
        row = build_data.build_owner_inputs([issue], capture)[0]
        self.assertEqual(row["status"], "ACKNOWLEDGED")
        self.assertIsNone(row["receipt"])
        self.assertIsNone(row["trace"]["steps"]["result"])
        for i in (1, 2):
            alternative = [dict(c) for c in comments]
            alternative[i]["author_association"] = "MEMBER"
            issue = dict(base_issue, comments=alternative)
            row = build_data.build_owner_inputs([issue], capture)[0]
            self.assertEqual(row["status"],
                             "HANDLED" if i == 2 else "ACKNOWLEDGED")

if __name__=="__main__":
    unittest.main(verbosity=2)
