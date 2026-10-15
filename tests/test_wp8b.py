#!/usr/bin/env python3
"""WP8b clock provenance — posted and updated must come from source records.

BaseCompatibleWP8b asserts fields available on the older builder API;
all four assertions should fail on WP8a BASE, with zero API/runtime errors.
"""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import build_data
import owner_json
from tests.test_wp7 import make_repo, resolver, receipt, OLDER, NEWER


class BaseCompatibleWP8b(unittest.TestCase):
    def fixture(self):
        data=json.loads((ROOT/"tests/fixtures/f7_owner_issue31_replay.json").read_text())
        return data["issues"],data["capture"]

    def test_wp8b_issue_last_comment_timestamp_is_not_missing(self):
        issues,capture=self.fixture()
        issues[0]["updated_at"] = ""
        row=next(x for x in build_data.build_owner_inputs(issues,capture)
                 if x["number"]==31)
        expected=max(c["created_at"] for c in issues[0]["comments"])
        self.assertEqual(row.get("updated_at"),expected.replace("Z","+00:00"))

    def test_wp8b_github_issue_updated_at_can_be_later_than_comments(self):
        issues,capture=self.fixture()
        issues[0]["updated_at"]="2026-10-15T18:45:00Z"
        row=next(x for x in build_data.build_owner_inputs(issues,capture)
                 if x["number"]==31)
        self.assertEqual(row.get("updated_at"),"2026-10-15T18:45:00+00:00")

    def test_wp8b_committed_json_receipt_time_becomes_last_update(self):
        with tempfile.TemporaryDirectory() as td:
            make_repo(td,receipts=[receipt("ACK",[])])
            row=owner_json.read_committed_inputs(td,resolver=resolver)[0]
        self.assertEqual(row.get("updated_at"),"2026-10-15T16:32:00Z")
        self.assertEqual(row["ts"],"2026-10-15T16:30:00Z")

    def test_wp8b_replacing_json_updates_superseded_record_clock(self):
        with tempfile.TemporaryDirectory() as td:
            make_repo(td,new=True)
            entries=owner_json.read_committed_inputs(td,resolver=resolver)
        rows={r["id"]:r for r in entries}
        self.assertEqual(rows[OLDER].get("updated_at"),rows[NEWER]["ts"])
        self.assertEqual(rows[OLDER]["status"],"SUPERSEDED")


class ExtraWP8b(unittest.TestCase):
    def test_wp8b_missing_unverified_time_not_invented(self):
        issues,capture=BaseCompatibleWP8b().fixture()
        issues[0]["updated_at"]="not-a-date"
        issues[0]["comments"]=[]
        row=next(x for x in build_data.build_owner_inputs(issues,capture)
                 if x["number"]==31)
        self.assertEqual(row["updated_at"],"2026-10-15T15:03:23+00:00")


if __name__=="__main__":
    unittest.main(verbosity=2)
