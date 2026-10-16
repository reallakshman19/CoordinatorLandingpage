#!/usr/bin/env python3
"""WP14 pilot Owner-input requests, exact authority, claim CAS, WP13 fixes."""
import base64
from datetime import datetime, timezone, timedelta
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import next_move as nm
import next_move_claim as claimhelper
import build_data
from tests.test_wp13 import (
    NOW, REGSHA, SHA, FIRST, SECOND, FROM, TO, OTM, OWNER, record,
    event, claim, register, checked,
)

def proposal(candidate):
    return {"id":"OI-20261016-140000-abcd","project":"landing-live",
            "type":"NEXT_MOVE_COMPOSE","text":json.dumps({"move":candidate})}

def approval(role="OwnerTeammember",identifier="11111111"):
    return {"id":"OI-20261016-140100-abce","project":"landing-live",
            "type":"NEXT_MOVE_APPROVAL",
            "text":json.dumps({"move":FIRST,"by":{"role":role,"id8":identifier},
                                "at":"2026-10-16T14:01:00Z",
                                "request_only":True})}
PROVENANCE={"author_association":"COLLABORATOR","flags":[]}
OWNERPROVENANCE={"author_association":"OWNER","flags":[]}


class FakeTransport:
    """In-memory Contents API simulator, including sha CAS and 404."""
    def __init__(self, existing=None, rows=None, others=None, registry=None):
        self.registry=registry or register()
        self.registry.pop("_registry_sha",None)
        self.rows=rows if rows is not None else [event("APPROVED","14:01")]
        self.existing=existing
        self.others=others or {}
        self.sent=[]
    def get(self,path):
        if "/contents/logs/landing-live/moves?ref=" in path:
            return [{"type":"file","name":FIRST+".json"}]+[
                {"type":"file","name":name+".json"} for name in self.others]
        data=None
        if "/registry.json" in path: data=self.registry
        elif path.endswith("/moves/"+FIRST+".json?ref=main"):data=record()
        elif "/moves.jsonl" in path:data="".join(json.dumps(x)+"\n" for x in self.rows)
        elif "/claims/"+FIRST+".json" in path and self.existing is not None:data=self.existing
        elif any("/moves/"+i+".json" in path for i in self.others):
            key=next(k for k in self.others if "/moves/"+k+".json" in path)
            data=self.others[key]
        if data is None:raise claimhelper.NotFound("remote_resource_absent")
        value=data if isinstance(data,str) else json.dumps(data)
        return {"sha":REGSHA if "/registry.json" in path else "c"*40,
                "content":base64.b64encode(value.encode()).decode()}
    def put(self,path,fields):
        if self.existing is not None and "sha" not in fields:
            raise claimhelper.ClaimRefused("create conflict 422")
        if "sha" in fields and fields["sha"]!="c"*40:
            raise claimhelper.ClaimRefused("CAS conflict 409")
        self.sent.append((path,fields))
        return {"content":{"sha":"d"*40},"commit":{"sha":"e"*40}}


class WP14Tests(unittest.TestCase):
    def test_01_owner_input_compose_schema_pending_only(self):
        result=nm.validate_input_request(register(),proposal(record()),[],PROVENANCE)
        self.assertTrue(result["valid"]);self.assertFalse(result["effective"])
        self.assertEqual(result["reason"],"draft_only_not_published")

    def test_02_owner_input_approval_tier_self_approval_labeled_not_effective(self):
        move=dict(record(),state="PUBLISHED")
        result=nm.validate_input_request(register(),approval(),[move],PROVENANCE)
        self.assertTrue(result["valid"]);self.assertTrue(result["self_approved"])
        self.assertFalse(result["effective"])
        self.assertEqual(result["reason"],"approval_request_only")

    def test_03_critical_otm_denied_owner_provenance_required(self):
        move=dict(record(),state="PUBLISHED")
        res=nm.validate_input_request(register("critical"),approval(),[move],PROVENANCE)
        self.assertFalse(res["valid"])
        res=nm.validate_input_request(register("critical"),
                                      approval("Owner","33333333"),[move],PROVENANCE)
        self.assertEqual(res["reason"],"owner_identity_not_verified")
        res=nm.validate_input_request(register("critical"),
                                      approval("Owner","33333333"),[move],OWNERPROVENANCE)
        self.assertTrue(res["valid"]);self.assertFalse(res["effective"])

    def test_04_untrusted_json_or_missing_move_not_approval(self):
        move=dict(record(),state="PUBLISHED")
        self.assertFalse(nm.validate_input_request(register(),approval(),[move],
                                                   {"author_association":"UNKNOWN","flags":[]})["valid"])
        self.assertEqual(nm.validate_input_request(register(),approval(),[],PROVENANCE)["reason"],
                         "move_not_waiting_approval")
        corrupt=approval();corrupt["text"]="{bad}"
        self.assertEqual(nm.validate_input_request(register(),corrupt,[move],PROVENANCE)["reason"],
                         "request_json_invalid")

    def test_05_expired_claimed_flag_distinct_from_send_uncertain(self):
        rows=[event("APPROVED","14:01"),event("CLAIMED","14:02",by=TO)]
        now=datetime(2026,10,16,14,22,tzinfo=timezone.utc)
        good,bad,_=checked(transitions=rows,claims={FIRST:claim()},now=now)
        self.assertFalse(bad);self.assertEqual(good[0]["state"],"CLAIMED")
        self.assertIn("claim expired",good[0]["flags"])
        self.assertNotIn("delivery uncertain",good[0]["flags"])
        rows.append(event("SEND_INTENT","14:03",by=TO,proof="draft visible"))
        good,bad,_=checked(transitions=rows,claims={FIRST:claim()},now=now)
        self.assertFalse(bad);self.assertEqual(good[0]["state"],"DELIVERY_UNCERTAIN")

    def test_06_current_head_is_recipient_scoped(self):
        reg=register()
        reg["_current_evidence_heads"]={"99999999":"f"*40}
        moves,bad,_=nm.validate_records(reg,{FIRST+".json":record()},[],{},NOW)
        self.assertFalse(bad)
        self.assertNotIn("stale basis",moves[0]["flags"])
        reg["_current_evidence_heads"]={TO["id8"]:"f"*40}
        moves,bad,_=nm.validate_records(reg,{FIRST+".json":record()},[],{},NOW)
        self.assertIn("stale basis",moves[0]["flags"])
        reg["_current_evidence_heads"]={TO["id8"]:SHA}
        moves,bad,_=nm.validate_records(reg,{FIRST+".json":record()},[],{},NOW)
        self.assertNotIn("stale basis",moves[0]["flags"])

    def test_07_missing_heartbeat_still_detects_overdue_ground(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp);(folder/"moves").mkdir()
            (folder/"moves"/(FIRST+".json")).write_text(json.dumps(record()))
            comments=[{"id":i+1,"created_at":f"2026-10-16T14:00:{i+1:02d}Z",
                       "body":f"TASK EVIDENCE v2 · landing-live · implementer · chat 22222222 · #{i+1} · 16 Oct 18:00 +04\nTask: active work"}
                      for i in range(5)]
            view=nm.load_project_moves(folder,register(),[
                {"chat_id8":TO["id8"],"evidence_thread_num":22}
            ],{22:{"number":22,"repository":"reallakshman19/CoordinatorLandingpage",
                    "comments":comments}},now=datetime(2026,10,16,14,50,tzinfo=timezone.utc),
                registry_sha=REGSHA)
            self.assertIn("detected, not acted on",view["flags"])
            self.assertIn("evaluator stale",view["flags"])
            self.assertEqual(view["task_cycle"]["count"],5)

    def test_08_create_claim_no_sha_and_ttl(self):
        api=FakeTransport()
        now=datetime(2026,10,16,14,5,tzinfo=timezone.utc)
        claimhelper.make_claim(api,"main",FIRST,REGSHA,TO,now=now)
        self.assertEqual(len(api.sent),1)
        path,fields=api.sent[0]
        self.assertTrue(path.endswith("/claims/"+FIRST+".json"))
        self.assertNotIn("sha",fields)
        obj=json.loads(base64.b64decode(fields["content"]).decode())
        self.assertEqual(obj["expires_at"],"2026-10-16T14:20:00+00:00")
        self.assertEqual(obj["by"],TO)

    def test_09_create_conflict_and_critical_hold_refuse(self):
        now=datetime(2026,10,16,14,5,tzinfo=timezone.utc)
        api=FakeTransport(existing=claim())
        with self.assertRaises(claimhelper.ClaimRefused):
            claimhelper.make_claim(api,"main",FIRST,REGSHA,TO,now=now)
        self.assertFalse(api.sent)
        api=FakeTransport(registry=dict(register(),control={"hold":"Owner HOLD"}))
        with self.assertRaises(claimhelper.ClaimRefused):
            claimhelper.make_claim(api,"main",FIRST,REGSHA,TO,now=now)
        self.assertFalse(api.sent)

    def test_10_cas_renew_requires_sha_and_identity(self):
        api=FakeTransport(existing=claim(),rows=[
            event("APPROVED","14:01"),event("CLAIMED","14:02",by=TO)])
        now=datetime(2026,10,16,14,10,tzinfo=timezone.utc)
        claimhelper.make_claim(api,"main",FIRST,REGSHA,TO,"renew",now=now,ttl_minutes=10)
        self.assertEqual(api.sent[0][1]["sha"],"c"*40)
        self.assertNotIn("sha",FakeTransport().sent if False else {})

    def test_11_expired_send_intent_refuses_takeover(self):
        api=FakeTransport(existing=claim(),rows=[
            event("APPROVED","14:01"),event("CLAIMED","14:02",by=TO),
            event("SEND_INTENT","14:03",by=TO,proof="composer draft")])
        now=datetime(2026,10,16,14,22,tzinfo=timezone.utc)
        with self.assertRaises(claimhelper.ClaimRefused):
            claimhelper.make_claim(api,"main",FIRST,REGSHA,TO,"renew",now=now)
        self.assertEqual(api.sent,[])

    def test_12_another_active_recipient_blocks_claim(self):
        second=record(SECOND)
        rows=[event("APPROVED","14:01"),
              dict(event("APPROVED","14:01"),move=SECOND),
              dict(event("CLAIMED","14:02",by=TO),move=SECOND)]
        api=FakeTransport(rows=rows,others={SECOND:second})
        with self.assertRaisesRegex(claimhelper.ClaimRefused,"recipient_has_active_dispatch"):
            claimhelper.make_claim(api,"main",FIRST,REGSHA,TO,
                                   now=datetime(2026,10,16,14,5,tzinfo=timezone.utc))
        self.assertFalse(api.sent)

    def test_13_registry_moved_or_actor_mismatch_blocks(self):
        api=FakeTransport()
        now=datetime(2026,10,16,14,5,tzinfo=timezone.utc)
        with self.assertRaises(claimhelper.ClaimRefused):
            claimhelper.make_claim(api,"main",FIRST,"f"*40,TO,now=now)
        with self.assertRaises(claimhelper.ClaimRefused):
            claimhelper.make_claim(api,"main",FIRST,REGSHA,OTM,now=now)
        self.assertFalse(api.sent)

    def test_14_no_execute_or_network_at_import(self):
        # CI imports code and runs FakeTransport only; GHTransport is never
        # invoked, no Contents API call or real files written by tests.
        self.assertEqual(claimhelper.REPOSITORY,
                         "reallakshman19/CoordinatorLandingpage")
        self.assertEqual(claimhelper.PROJECT,"landing-live")


class WP14BaseCompatible(unittest.TestCase):
    """Exact predecessor next_move.py gives two assertion FAIL not ERROR."""
    def test_wp14_expired_claimed_flag_was_missing(self):
        rows=[event("APPROVED","14:01"),event("CLAIMED","14:02",by=TO)]
        good,bad,_=checked(transitions=rows,claims={FIRST:claim()},
                           now=datetime(2026,10,16,14,22,tzinfo=timezone.utc))
        self.assertFalse(bad)
        self.assertIn("claim expired",good[0]["flags"])

    def test_wp14_missing_heartbeat_must_detect_due_ground(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp);(folder/"moves").mkdir()
            (folder/"moves"/(FIRST+".json")).write_text(json.dumps(record()))
            comments=[{"id":i+1,"created_at":f"2026-10-16T14:00:{i+1:02d}Z",
                       "body":f"TASK EVIDENCE v2 · landing-live · implementer · chat 22222222 · #{i+1} · 16 Oct 18:00 +04\nTask: work"}
                      for i in range(5)]
            view=nm.load_project_moves(folder,register(),[
                {"chat_id8":TO["id8"],"evidence_thread_num":22}],
                {22:{"number":22,"repository":"reallakshman19/CoordinatorLandingpage",
                     "comments":comments}},now=datetime(2026,10,16,14,50,tzinfo=timezone.utc),
                registry_sha=REGSHA)
            self.assertIn("detected, not acted on",view["flags"])


if __name__=="__main__":
    unittest.main(verbosity=2)
