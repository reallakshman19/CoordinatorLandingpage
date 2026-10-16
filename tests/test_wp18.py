#!/usr/bin/env python3
"""WP18 landing-live one-cycle preflight: real-shape START/END and Next Move negatives.

Every GitHub comment is a local GitHub-API-shaped observation including id,
created_at, updated_at and complete UTF-8 body. No actual issue/claim/timer writes.
"""
import copy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import ultra_economy as uem
import next_move as nm
import next_move_claim as claimhelper
from tests.test_ultra_economy import fixture, START, END, REPO, URL, NOW
from tests.test_wp13 import FIRST,SECOND,REGSHA,TO,OTM,record,event,register
from tests.test_wp14 import FakeTransport

ID="11111111"
TASK="WP16"
LEDGER="https://github.com/"+REPO+"/issues/21|"+TASK


def pilot(*,end=True,move=True,state="SENT_TO_CHAT"):
    return fixture(end=end,move=move,limit=1,cycle=1,state=state)


def observe(reg,agents,threads,view):
    # Round-trip all four authentic GitHub-shaped materials through a local
    # fixture directory on every pass; read back without writing production.
    with tempfile.TemporaryDirectory() as work:
        root=Path(work)
        for filename,data in [("registry.json",reg),("agents.json",agents),
                              ("thread.json",threads),("moves.json",view)]:
            (root/filename).write_text(json.dumps(data,ensure_ascii=False),
                                       encoding="utf-8")
        loaded=[json.loads((root/name).read_text(encoding="utf-8"))
                for name in ("registry.json","agents.json","thread.json","moves.json")]
        # JSON object keys are strings, whereas the scoped fetch builds an
        # issue-number-indexed map with integer keys. Match that readback.
        loaded[2]={int(key):value for key,value in loaded[2].items()}
        return uem.project(*loaded,now=NOW)


class WP18PilotControls(unittest.TestCase):
    def test_01_actual_landing_registry_not_enabled(self):
        actual=json.loads((ROOT/"logs/landing-live/registry.json").read_text())
        self.assertFalse(uem.config(actual)["enabled"])
        self.assertNotIn("ultra_economy",actual)
        self.assertEqual(actual["criticality"],"normal")

    def test_02_eligible_single_start_source_bound_working_claim_no_timer(self):
        reg,agents,threads,view=pilot(end=False)
        report=observe(reg,agents,threads,view)
        row=report["agents"][ID]
        self.assertEqual(report["max_cycles"],1)
        self.assertEqual(row["state"],"WORKING_CLAIM")
        self.assertFalse(row["may_proceed"])
        self.assertEqual(row["timer"],"NOT_ARMED")
        self.assertEqual(row["fallback"],"NOT_ARMED")
        self.assertEqual(row["start_binding"]["url"],URL+"#issuecomment-101")
        self.assertEqual(row["start_binding"]["body_sha256"],
                         hashlib.sha256(threads[22]["comments"][0]["body"].encode()).hexdigest())

    def test_03_hold_before_end_and_after_start(self):
        reg,agents,threads,view=pilot()
        reg["control"]["hold"]="Owner HOLD before END"
        out=observe(reg,agents,threads,view)["agents"][ID]
        self.assertEqual(out["state"],"HOLD")
        self.assertFalse(out["may_proceed"])

    def test_04_retirement_after_start_denies_work_and_end(self):
        reg,agents,threads,view=pilot()
        agents[0]["status"]="retired after TASK START"
        reg["agents"][0]["status"]=agents[0]["status"]
        out=observe(reg,agents,threads,view)["agents"][ID]
        self.assertEqual(out["state"],"RETIRED_OR_STOPPED")
        self.assertFalse(out["may_proceed"])

    def test_05_stale_head_visible_even_on_final_cycle(self):
        reg,agents,threads,view=pilot()
        agents[0]["evidence_head_status"]={"current_head":"f"*40}
        view["moves"][0]["basis"]["head"]="a"*40
        out=observe(reg,agents,threads,view)["agents"][ID]
        self.assertEqual(out["move_state"],"STALE_MOVE")
        self.assertEqual(out["state"],"STALE_MOVE")
        self.assertFalse(out["may_proceed"])

    def test_06_expired_execution_grant_before_claim(self):
        reg,agents,threads,view=pilot(end=False)
        reg["ultra_economy"]["execution_grants"][ID]["expires_at"]="2026-10-16T14:39:00Z"
        self.assertEqual(observe(reg,agents,threads,view)["agents"][ID]["state"],
                         "EXPIRED_EXECUTION")

    def test_07_edited_start_body_invalidates_source(self):
        reg,agents,threads,view=pilot(end=False)
        threads[22]["comments"][0]["body"]+="\nEdit after pin"
        self.assertEqual(observe(reg,agents,threads,view)["agents"][ID]["state"],
                         "SOURCE_BINDING_INVALID")

    def test_08_edited_end_time_and_body_invalidate_source(self):
        for field,value in (("updated_at","2026-10-16T14:21:00Z"),
                            ("body",END+"\npost-hoc changed")):
            reg,agents,threads,view=pilot()
            threads[22]["comments"][1][field]=value
            self.assertEqual(observe(reg,agents,threads,view)["agents"][ID]["state"],
                             "SOURCE_BINDING_INVALID")

    def test_09_duplicate_start_fails_no_winner(self):
        reg,agents,threads,view=pilot()
        threads[22]["comments"].append(dict(threads[22]["comments"][0],id=103))
        row=observe(reg,agents,threads,view)["agents"][ID]
        self.assertEqual(row["state"],"AMBIGUOUS_START")
        self.assertFalse(row["may_proceed"])

    def test_10_duplicate_end_fails_no_winner(self):
        reg,agents,threads,view=pilot()
        threads[22]["comments"].append(dict(threads[22]["comments"][1],id=103))
        row=observe(reg,agents,threads,view)["agents"][ID]
        self.assertEqual(row["state"],"AMBIGUOUS_END")
        self.assertFalse(row["may_proceed"])

    def test_11_uncertain_send_pending_stays_visible_before_any_next_claim(self):
        for state in ("SEND_INTENT","DELIVERY_UNCERTAIN"):
            reg,agents,threads,view=pilot(state=state)
            row=observe(reg,agents,threads,view)["agents"][ID]
            self.assertEqual(row["state"],"DELIVERY_UNCERTAIN")
            self.assertEqual(row["move_state"],"DELIVERY_UNCERTAIN")
            self.assertFalse(row["may_proceed"])

    def test_12_missing_authoritative_roster_row_does_not_work(self):
        reg,agents,threads,view=pilot(end=False)
        reg["agents"]=[]
        row=observe(reg,agents,threads,view)["agents"][ID]
        self.assertEqual(row["state"],"MISSING_ROSTER_ROW")
        self.assertFalse(row["may_proceed"])

    def test_13_duplicate_authoritative_roster_identity_refused(self):
        reg,agents,threads,view=pilot(end=False)
        reg["agents"].append(copy.deepcopy(reg["agents"][0]))
        row=observe(reg,agents,threads,view)["agents"][ID]
        self.assertEqual(row["state"],"AMBIGUOUS_ROSTER")
        self.assertFalse(row["may_proceed"])

    def test_14_missing_or_unavailable_timer_remains_not_armed(self):
        reg,agents,threads,view=pilot(end=False)
        start=threads[22]["comments"][0]
        start["body"]=start["body"].replace(
            "Fallback: agent to arm hourly ChatGPT task",
            "Fallback: ARMED apparently-valid-but-unverified-receipt")
        reg["ultra_economy"]["source_bindings"]["101"]["body_sha256"]=hashlib.sha256(
            start["body"].encode()).hexdigest()
        row=observe(reg,agents,threads,view)["agents"][ID]
        self.assertEqual(row["timer"],"NOT_ARMED")
        self.assertEqual(row["fallback"],"NOT_ARMED")
        self.assertIsNone(row["fallback_due_at"])

    def test_15_same_unit_restart_cannot_reset_or_begin_1_again(self):
        reg,agents,threads,view=pilot(end=False)
        reg["ultra_economy"]["cycle_ledger"][LEDGER]["completed_cycles"]=1
        row=observe(reg,agents,threads,view)["agents"][ID]
        self.assertEqual(row["state"],"UEM_CYCLE_RESTART_OR_GAP")
        self.assertFalse(row["may_proceed"])

    def test_16_final_end_does_not_authorize_second_cycle(self):
        reg,agents,threads,view=pilot()
        row=observe(reg,agents,threads,view)["agents"][ID]
        self.assertEqual(row["state"],"MAX_CYCLES_REACHED")
        self.assertEqual(row["move_state"],"DELIVERED_MOVE")
        self.assertFalse(row["may_proceed"])

    def test_17_published_or_approved_move_not_a_chat_delivery(self):
        for state in ("PUBLISHED","APPROVED","CLAIMED"):
            reg,agents,threads,view=pilot(state=state)
            row=observe(reg,agents,threads,view)["agents"][ID]
            self.assertEqual(row["move_state"],"AWAITING_DELIVERY")
            self.assertFalse(row["may_proceed"])

    def test_18_two_active_claimed_moves_same_recipient_both_rejected(self):
        a,b=record(FIRST),record(SECOND)
        a["to"]={"role":"implementer","id8":ID}
        b["to"]={"role":"implementer","id8":ID}
        reg=register()
        rows=[]
        claims={}
        for mid in (FIRST,SECOND):
            rows.extend([event("APPROVED","14:01",move=mid),
                         event("CLAIMED","14:02",by={"role":"implementer","id8":ID},
                               move=mid)])
            claims[mid]={"by":{"role":"implementer","id8":ID},
                         "claimed_at":"2026-10-16T14:02:00Z",
                         "expires_at":"2026-10-16T14:17:00Z"}
        valid,rejected,_=nm.validate_records(reg,{
            FIRST+".json":a,SECOND+".json":b},rows,claims,
            datetime(2026,10,16,14,5,tzinfo=timezone.utc))
        self.assertFalse(valid)
        self.assertEqual(sorted(row["id"] for row in rejected),
                         sorted((FIRST,SECOND)))
        self.assertTrue(all("concurrent_dispatch" in row["reasons"] for row in rejected))

    def test_19_claim_helper_refuses_while_other_move_active(self):
        other=record(SECOND)
        rows=[event("APPROVED","14:01"),
              event("APPROVED","14:01",move=SECOND),
              event("CLAIMED","14:02",by=TO,move=SECOND)]
        api=FakeTransport(rows=rows,others={SECOND:other})
        with self.assertRaisesRegex(claimhelper.ClaimRefused,
                                    "recipient_has_active_dispatch"):
            claimhelper.make_claim(api,"main",FIRST,REGSHA,TO,
                 now=datetime(2026,10,16,14,5,tzinfo=timezone.utc))
        self.assertEqual(api.sent,[])

    def test_20_replay_is_read_only_no_duplicate_comment_move_timer_or_send(self):
        reg,agents,threads,view=pilot()
        before=json.dumps((reg,agents,threads,view),sort_keys=True)
        first=observe(reg,agents,threads,view)
        second=observe(reg,agents,threads,view)
        self.assertEqual(first,second)
        self.assertEqual(before,json.dumps((reg,agents,threads,view),sort_keys=True))
        self.assertEqual([x["id"] for x in threads[22]["comments"]],[101,102])
        self.assertEqual(len(view["moves"]),1)
        self.assertEqual(first["timer"],"NOT_ARMED")
        self.assertEqual(first["agents"][ID]["state"],"MAX_CYCLES_REACHED")
        self.assertFalse(first["agents"][ID]["may_proceed"])

    def test_21_independent_observer_move_approval_to_pickup_validated(self):
        a=record(FIRST)
        a["from"]={"role":"TeamCoordinator","id8":"33333333"}
        a["to"]={"role":"implementer","id8":ID}
        a["trigger"]={"type":"uem_end","task":TASK,"cycle":1,
                      "end_comment_id":102}
        a["created_at"]="2026-10-16T14:20:30Z"
        rows=[event("APPROVED","14:21",by=OTM),
              event("CLAIMED","14:22",by={"role":"implementer","id8":ID}),
              event("SEND_INTENT","14:23",by={"role":"implementer","id8":ID},
                    proof="draft composition witnessed"),
              event("SENT_TO_CHAT","14:24",by={"role":"implementer","id8":ID},
                    proof="delivery receipt separately witnessed"),
              event("PICKED_UP","14:25",by={"role":"implementer","id8":ID},
                    proof="pickup evidence verified")]
        claim={"by":{"role":"implementer","id8":ID},
               "claimed_at":"2026-10-16T14:22:00Z",
               "expires_at":"2026-10-16T14:37:00Z"}
        good,bad,_=nm.validate_records(register(),{FIRST+".json":a},
                  rows,{FIRST:claim},datetime(2026,10,16,14,26,tzinfo=timezone.utc))
        self.assertFalse(bad)
        self.assertEqual(len(good),1)
        self.assertEqual(good[0]["state"],"PICKED_UP")
        reg,agents,threads,view=pilot()
        view["moves"]=good
        out=observe(reg,agents,threads,view)["agents"][ID]
        self.assertEqual(out["move_state"],"DELIVERED_MOVE")
        self.assertEqual(out["state"],"MAX_CYCLES_REACHED")
        self.assertFalse(out["may_proceed"])
        self.assertEqual(out["end_binding"]["comment_id"],102)

    def test_22_pilot_patch_not_applied_and_requires_owner_words(self):
        path=ROOT/"pilot"/"landing-live-uem-v1.proposed.patch"
        text=path.read_text(encoding="utf-8")
        self.assertIn('"enabled": true',text)
        self.assertIn('"max_cycles": 1',text)
        self.assertIn("NOT APPLIED",text)
        self.assertNotIn("ultra_economy",(
            ROOT/"logs"/"landing-live"/"registry.json").read_text())

    def test_23_skill_and_runbook_no_automatic_timer_authority(self):
        skill=(ROOT/"skills"/"ultra-economy-mode"/"SKILL.md").read_text()
        runbook=(ROOT/"pilot"/"WP18_LANDING_LIVE_RUNBOOK.md").read_text()
        for text in (skill,runbook):
            self.assertIn("NOT_ARMED",text)
            self.assertIn("Owner words",text)
            self.assertIn("creation proof",text)
            self.assertIn("one fire",text)
            self.assertIn("cancellation",text)


class WP18PinnedBase(unittest.TestCase):
    """Existing WP17 code fails both without masking errors. Exactly 2 RED."""
    def test_wp18_pinned_missing_roster_must_block(self):
        reg,agents,threads,view=pilot(end=False)
        reg["agents"]=[]
        self.assertEqual(observe(reg,agents,threads,view)["agents"][ID]["state"],
                         "MISSING_ROSTER_ROW")

    def test_wp18_pinned_uncertain_send_not_hidden_by_cycle_limit(self):
        reg,agents,threads,view=pilot(state="SEND_INTENT")
        self.assertEqual(observe(reg,agents,threads,view)["agents"][ID]["state"],
                         "DELIVERY_UNCERTAIN")


if __name__=="__main__":
    unittest.main(verbosity=2)
