#!/usr/bin/env python3
"""WP6: trace links are grounded in immutable issue/comment records."""
import copy
import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import build_data

F7=json.loads((ROOT/"tests/fixtures/f7_owner_issue31_replay.json").read_text())
REPO=F7["repo"]

def rows(issues=None):
    return {r["number"]:r for r in
            build_data.build_owner_inputs(issues or F7["issues"],F7["capture"])}

class BaseCompatibleWP6(unittest.TestCase):
    def test_wp6_f7_posted_and_ack_have_real_links_and_dates(self):
        r=rows()[31]
        steps=r.get("trace",{}).get("steps",{})
        self.assertEqual(steps.get("posted",{}).get("url"),
                         "https://github.com/"+REPO+"/issues/31")
        self.assertEqual(steps.get("ack",{}).get("url"),
                         "https://github.com/"+REPO+"/issues/31#issuecomment-31001")
        self.assertEqual(steps.get("ack",{}).get("at"),"2026-10-15T15:04:00Z")

    def test_wp6_f7_real_handled_comment_does_not_clear_project_mismatch(self):
        r=rows()[31]
        result=r.get("trace",{}).get("steps",{}).get("result") or {}
        self.assertEqual(result.get("url"),
                         "https://github.com/"+REPO+"/issues/31#issuecomment-31002")
        self.assertIs(result.get("accepted"),False)
        self.assertEqual(r["status"],"NEEDS_CLARIFICATION")
        self.assertIsNone(r["receipt"])

    def test_wp6_f7_why_line_explains_both_conflicting_projects(self):
        r=rows()[31]
        why=r.get("trace",{}).get("why","")
        self.assertIn("Form says grade9-pilot",why)
        self.assertIn("title says landing-live",why)
        self.assertEqual(r.get("trace",{}).get("waiting_for"),"Owner")

    def test_wp6_unrecorded_handoff_agent_and_check_are_missing_not_guessed(self):
        r=rows()[31]
        steps=r.get("trace",{}).get("steps",{})
        self.assertEqual(set(steps), {"posted","ack","sent","evidence","check","result"})
        self.assertIsNone(steps.get("sent"))
        self.assertIsNone(steps.get("evidence"))
        self.assertIsNone(steps.get("check"))

class AdditionalWP6(unittest.TestCase):
    def test_wp6_six_links_only_when_real_explicit_comments_exist(self):
        issue=copy.deepcopy(F7["issues"][1])
        issue["comments"]=[]
        marker=[
          ("ACK: owner-input #32",32001),
          ("Sent to agent: FTC-123 https://github.com/"+REPO+"/issues/66#issuecomment-32002",32002),
          ("Agent evidence: TASK EVIDENCE https://github.com/"+REPO+"/issues/66#issuecomment-32003",32003),
          ("Check: C1 verdict https://github.com/"+REPO+"/issues/66#issuecomment-32004",32004),
          ("HANDLED: owner-input #32 receipt: https://github.com/"+REPO+"/issues/32#issuecomment-32005",32005),
        ]
        for k,(body,cid) in enumerate(marker):
            issue["comments"].append({
                "id":cid,"body":body,"author_association":"MEMBER",
                "created_at":f"2026-10-15T15:{12+k:02d}:00Z"
            })
        r=rows([issue])[32]
        steps=r["trace"]["steps"]
        self.assertEqual(list(steps),["posted","ack","sent","evidence","check","result"])
        for name,datum in steps.items():
            with self.subTest(name=name):
                self.assertIsInstance(datum,dict)
                self.assertTrue(datum["url"].startswith("https://github.com/"+REPO))
                self.assertTrue(datum["at"])
        self.assertTrue(steps["result"]["accepted"])
        self.assertEqual(r["status"],"HANDLED")

    def test_wp6_spoofed_foreign_or_non_git_handoff_cannot_create_link(self):
        issue=copy.deepcopy(F7["issues"][1])
        issue["comments"]=[
           {"id":32001,"author_association":"CONTRIBUTOR",
            "body":"Sent to agent: FTC123 https://github.com/"+REPO+"/issues/8#issuecomment-2",
            "created_at":"2026-10-15T15:11:00Z"},
           {"id":32002,"author_association":"MEMBER",
            "body":"Sent to agent: javascript:alert(1)",
            "created_at":"2026-10-15T15:12:00Z"},
           {"id":32003,"author_association":"MEMBER",
            "body":"Our TASK EVIDENCE is not linked anywhere yet",
            "created_at":"2026-10-15T15:13:00Z"},
        ]
        steps=rows([issue])[32]["trace"]["steps"]
        self.assertIsNone(steps["sent"])
        self.assertIsNone(steps["evidence"])
        self.assertIsNone(steps["check"])
        self.assertIsNone(steps["result"])

    def test_wp6_no_false_assurances_when_source_is_unknown(self):
        issue=copy.deepcopy(F7["issues"][2])
        result=rows([issue])[33]
        self.assertIn("label",result["trace"]["why"])
        self.assertEqual(result["trace"]["waiting_for"],"TeamCoordinator")

if __name__=="__main__":
    unittest.main(verbosity=2)
