#!/usr/bin/env python3
"""WP17 immutable UEM source binding, fail-closed pre-claim authority and WP16 notes."""
from datetime import datetime,timezone,timedelta
from pathlib import Path
import hashlib
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import ultra_economy as uem
import status_bar as sb
from tests.test_ultra_economy import fixture,NOW,REPO,URL,START,END

ID="11111111"


def examine(reg,agents,threads,view):
    return uem.project(reg,agents,threads,view,now=NOW)["agents"][ID]


class WP17Guards(unittest.TestCase):
    def test_01_bound_start_has_url_id_time_digest(self):
        reg,agents,threads,view=fixture(end=False)
        item=examine(reg,agents,threads,view)
        self.assertEqual(item["state"],"WORKING_CLAIM")
        anchor=item["start_binding"]
        self.assertEqual(anchor["url"],URL+"#issuecomment-101")
        self.assertEqual(anchor["comment_id"],101)
        self.assertEqual(anchor["updated_at"],"2026-10-16T14:00:00Z")
        self.assertEqual(anchor["body_sha256"],
                         hashlib.sha256(START.encode()).hexdigest())

    def test_02_missing_binding_never_working(self):
        reg,agents,threads,view=fixture(end=False)
        reg["ultra_economy"]["source_bindings"].clear()
        item=examine(reg,agents,threads,view)
        self.assertEqual(item["state"],"SOURCE_BINDING_INVALID")
        self.assertFalse(item["may_proceed"])

    def test_03_edited_start_body_invalidates_digest(self):
        reg,agents,threads,view=fixture(end=False)
        threads[22]["comments"][0]["body"]+="\nchanged"
        item=examine(reg,agents,threads,view)
        self.assertEqual(item["state"],"SOURCE_BINDING_INVALID")
        self.assertIn("source_binding_invalid_or_missing",item["warnings"])

    def test_04_updated_at_change_invalidates_start(self):
        reg,agents,threads,view=fixture(end=False)
        threads[22]["comments"][0]["updated_at"]="2026-10-16T14:01:00Z"
        self.assertEqual(examine(reg,agents,threads,view)["state"],"SOURCE_BINDING_INVALID")

    def test_05_missing_end_binding_inhibits_delivery(self):
        reg,agents,threads,view=fixture()
        del reg["ultra_economy"]["source_bindings"]["102"]
        item=examine(reg,agents,threads,view)
        self.assertEqual(item["state"],"SOURCE_BINDING_INVALID")
        self.assertFalse(item["may_proceed"])

    def test_06_edited_end_invalidates_commit_source(self):
        reg,agents,threads,view=fixture()
        threads[22]["comments"][1]["body"]+="\nappend untrusted edit"
        self.assertEqual(examine(reg,agents,threads,view)["state"],"SOURCE_BINDING_INVALID")

    def test_07_duplicate_end_inhibits_delivery(self):
        reg,agents,threads,view=fixture()
        dup=dict(threads[22]["comments"][1],id=103)
        threads[22]["comments"].append(dup)
        self.assertEqual(examine(reg,agents,threads,view)["state"],"AMBIGUOUS_END")

    def test_08_duplicate_start_inhibits_work_claim(self):
        reg,agents,threads,view=fixture(end=False)
        dup=dict(threads[22]["comments"][0],id=103)
        threads[22]["comments"].append(dup)
        self.assertEqual(examine(reg,agents,threads,view)["state"],"AMBIGUOUS_START")

    def test_09_project_hold_before_work_claim(self):
        reg,agents,threads,view=fixture(end=False)
        reg["control"]["hold"]="Owner HOLD"
        self.assertEqual(examine(reg,agents,threads,view)["state"],"HOLD")

    def test_10_retirement_after_start_invalidates(self):
        reg,agents,threads,view=fixture(end=False)
        agents[0]["status"]="retired 16 Oct"
        reg["agents"][0]["status"]=agents[0]["status"]
        self.assertEqual(examine(reg,agents,threads,view)["state"],"RETIRED_OR_STOPPED")

    def test_11_unqualified_successor_is_not_exec_holder(self):
        reg,agents,threads,view=fixture(end=False)
        agents[0]["adoption"]="PENDING"
        reg["agents"][0]["adoption"]="PENDING"
        self.assertEqual(examine(reg,agents,threads,view)["state"],"UNQUALIFIED_SUCCESSOR")

    def test_12_other_writer_conflict_blocks_claim(self):
        reg,agents,threads,view=fixture(end=False)
        reg["writer_leases"]=[{"holder_id8":"22222222","exclusive":True,
                               "active":True,"paths":["scripts/*"]}]
        self.assertEqual(examine(reg,agents,threads,view)["state"],"WRITER_LEASE_CONFLICT")

    def test_13_expired_execution_grant_blocks(self):
        reg,agents,threads,view=fixture(end=False)
        reg["ultra_economy"]["execution_grants"][ID]["expires_at"]="2026-10-16T14:39:00Z"
        self.assertEqual(examine(reg,agents,threads,view)["state"],"EXPIRED_EXECUTION")

    def test_14_monitoring_grant_cannot_authorize_execution(self):
        reg,agents,threads,view=fixture(end=False)
        reg["ultra_economy"]["execution_grants"].clear()
        self.assertEqual(examine(reg,agents,threads,view)["state"],"UNVERIFIED_EXECUTION")
        reg,agents,threads,view=fixture(move=False)
        reg["ultra_economy"]["monitoring_grants"].clear()
        row=examine(reg,agents,threads,view)
        self.assertEqual(row["state"],"NO_MATCHING_MOVE")
        self.assertEqual(row["monitoring_grant"],"UNVERIFIED_MONITORING")
        self.assertEqual(row["followup"]["state"],"MONITORING_UNGRANTED")

    def test_15_persisted_cycle_ledger_not_reset_on_restart(self):
        reg,agents,threads,view=fixture(end=False)
        reg["ultra_economy"]["cycle_ledger"]["https://github.com/reallakshman19/CoordinatorLandingpage/issues/21|WP16"]["completed_cycles"]=1
        self.assertEqual(examine(reg,agents,threads,view)["state"],"UEM_CYCLE_RESTART_OR_GAP")

    def test_16_separate_cycle_counters(self):
        reg,agents,threads,view=fixture(end=False)
        view["task_cycle"]={"count":19}
        reg["delegation_cycle"]=999
        row=examine(reg,agents,threads,view)
        self.assertEqual(row["cycle_balance"]["uem_completed"],0)
        self.assertEqual(row["cycle_balance"]["next_move_task_count"],19)
        self.assertEqual(row["cycle_balance"]["owner_delegation_cycle"],"SEPARATE_UNVERIFIED")
        self.assertEqual(row["cycle_balance"]["uem_remaining"],3)

    def test_17_claimed_armed_timer_always_not_armed_without_host(self):
        reg,agents,threads,view=fixture(end=False)
        body=threads[22]["comments"][0]["body"].replace(
            "Fallback: agent to arm hourly ChatGPT task","Fallback: ARMED dummy-receipt")
        threads[22]["comments"][0]["body"]=body
        reg["ultra_economy"]["source_bindings"]["101"]["body_sha256"]=hashlib.sha256(body.encode()).hexdigest()
        row=examine(reg,agents,threads,view)
        self.assertEqual(row["state"],"WORKING_CLAIM")
        self.assertEqual(row["timer"],"NOT_ARMED")
        self.assertEqual(row["fallback"],"NOT_ARMED")
        self.assertIn("ARMED",row["timer_claim"])
        self.assertIsNone(row["fallback_due_at"])

    def test_18_wrong_thread_repository_denies_provenance(self):
        reg,agents,threads,view=fixture(end=False)
        threads[22]["repository"]="acme/other"
        self.assertEqual(uem.project(reg,agents,threads,view,now=NOW)["agents"],{})

    def test_19_source_pin_wrong_comment_url(self):
        reg,agents,threads,view=fixture(end=False)
        reg["ultra_economy"]["source_bindings"]["101"]["url"]=URL+"#issuecomment-999"
        self.assertEqual(examine(reg,agents,threads,view)["state"],"SOURCE_BINDING_INVALID")

    def test_20_uncertain_delivery_no_proceed(self):
        for state in ("SEND_INTENT","DELIVERY_UNCERTAIN"):
            reg,agents,threads,view=fixture(state=state)
            row=examine(reg,agents,threads,view)
            self.assertEqual(row["state"],"DELIVERY_UNCERTAIN")
            self.assertFalse(row["may_proceed"])

    def test_21_stale_head_after_end_no_proceed(self):
        reg,agents,threads,view=fixture()
        agents[0]["evidence_head_status"]={"current_head":"a"*40}
        view["moves"][0]["basis"]["head"]="b"*40
        row=examine(reg,agents,threads,view)
        self.assertEqual(row["state"],"STALE_MOVE")
        self.assertFalse(row["may_proceed"])

    def test_22_wp16_parent_red_dependency_propagates(self):
        parent={"project":"parent","control":{"hold":None},
                "agents":[{"chat_id8":"aaaa0001","role":"worker","status":"active",
                          "observation":{"state":"WORKING","reachable":True,
                                         "observed_at":"2026-10-16T14:39:00Z"},
                          "grant":{"verified":True,"expires_at":"2026-10-16T16:00:00Z"}}],
                "dependencies":["upstream"]}
        upstream={"project":"upstream","control":{"hold":"Owner HOLD"},
                  "agents":[{"chat_id8":"bbbb0002","role":"worker","status":"hold"}]}
        out=sb.build_status_bar({"parent":parent,"upstream":upstream},
              {"parent":{"next_move":{"evaluator_at":"2026-10-16T14:35:00Z"}}},NOW)
        by={p["project"]:p for p in out["projects"]}
        self.assertEqual(by["upstream"]["light"],"grey")
        self.assertEqual(by["parent"]["light"],"red")

    def test_23_wp16_parent_yellow_dependency_propagates(self):
        regs={p:{"project":p,"agents":[{"chat_id8":key,"role":"worker",
            "status":"active","observation":{"state":"WORKING","reachable":True,
                "observed_at":"2026-10-16T14:35:00Z"},
            "grant":{"verified":True,"expires_at":"2026-10-16T16:00:00Z"}}],
            "control":{"hold":None}} for p,key in
            [("parent","aaaa0001"),("upstream","bbbb0002")]}
        regs["parent"]["dependencies"]=["upstream"]
        data=sb.build_status_bar(regs,{"parent":{"next_move":{"evaluator_at":"2026-10-16T14:35:00Z"}},
                                        "upstream":{"next_move":{}}},NOW)
        lights={p["project"]:p["light"] for p in data["projects"]}
        self.assertEqual(lights,{"parent":"yellow","upstream":"yellow"})

    def test_24_wp16_explicit_completion_only(self):
        for raw,expected in (("INCOMPLETE",False),("UNCOMPLETED",False),
                             ("FROZEN_AWAITING_REVIEW",False),("CODE_HOLD_COMPLETE_PENDING",False),
                             ("DONE engineering",True),("COMPLETE",True),
                             ("BOUNDED_UNIT_COMPLETE_FACTUAL_RESULT_ONLY",True)):
            reg={"project":"demo","agents":[{"chat_id8":"aabbccdd",
                "status":raw}],"control":{"hold":None}}
            self.assertEqual(sb.normalize_roster(reg)[0]["complete"],expected,raw)

    def test_25_wp16_root_vs_workstream_main_key_distinct(self):
        reg={"project":"demo","agents":[{"chat_id8":"aabbccdd"}],
             "workstreams":{"main":{"agents":[{"chat_id8":"ddeeff00"}]}}}
        rows=sb.normalize_roster(reg)
        self.assertEqual(len({r["key"] for r in rows}),2)
        self.assertTrue(any("workstream:@root" in r["key"] for r in rows))
        self.assertTrue(any("workstream:@ws:main" in r["key"] for r in rows))

    def test_26_successor_cannot_reset_the_same_workplan_task(self):
        reg,agents,threads,view=fixture(end=False)
        key="https://github.com/reallakshman19/CoordinatorLandingpage/issues/21|WP16"
        reg["ultra_economy"]["cycle_ledger"][key]["completed_cycles"]=1
        new_id="22222222"
        grant=dict(reg["ultra_economy"]["execution_grants"][ID],holder_id8=new_id)
        reg["ultra_economy"]["execution_grants"]={new_id:grant}
        reg["ultra_economy"]["monitoring_grants"]={new_id:dict(grant)}
        agents[0]["chat_id8"]=new_id
        reg["agents"][0]["chat_id8"]=new_id
        body=threads[22]["comments"][0]["body"].replace(
            "chat 11111111","chat 22222222").replace("cycle 1/3","cycle 2/3")
        threads[22]["comments"][0]["body"]=body
        reg["ultra_economy"]["source_bindings"]["101"]["body_sha256"]=hashlib.sha256(body.encode()).hexdigest()
        out=uem.project(reg,agents,threads,view,now=NOW)["agents"][new_id]
        self.assertEqual(out["state"],"WORKING_CLAIM")
        # A successor attempting cycle 1 on the same workplan cannot refill it.
        body=body.replace("cycle 2/3","cycle 1/3")
        threads[22]["comments"][0]["body"]=body
        reg["ultra_economy"]["source_bindings"]["101"]["body_sha256"]=hashlib.sha256(body.encode()).hexdigest()
        out=uem.project(reg,agents,threads,view,now=NOW)["agents"][new_id]
        self.assertEqual(out["state"],"UEM_CYCLE_RESTART_OR_GAP")

    def test_26_wp3_workflow_allowlist_keeps_exclusivity_gate(self):
        text=(ROOT/"tests"/"test_wp3.py").read_text()
        self.assertIn('"ultra-economy-tests.yml"',text)
        self.assertIn('self.assertNotIn("uses: actions/deploy-pages@"',text)


class WP17PinnedBase(unittest.TestCase):
    """Pinned WP16: same fixture/observations demonstrate unguarded behavior."""
    def test_wp17_pinned_edited_start_cannot_work(self):
        reg,agents,threads,view=fixture(end=False)
        threads[22]["comments"][0]["body"]+="\nnew edit"
        self.assertEqual(examine(reg,agents,threads,view)["state"],"SOURCE_BINDING_INVALID")

    def test_wp17_pinned_expired_grant_cannot_work(self):
        reg,agents,threads,view=fixture(end=False)
        reg["ultra_economy"]["execution_grants"][ID]["expires_at"]="2026-10-16T14:39:00Z"
        self.assertEqual(examine(reg,agents,threads,view)["state"],"EXPIRED_EXECUTION")

    def test_wp17_pinned_duplicate_end_cannot_deliver(self):
        reg,agents,threads,view=fixture()
        threads[22]["comments"].append(dict(threads[22]["comments"][1],id=103))
        self.assertEqual(examine(reg,agents,threads,view)["state"],"AMBIGUOUS_END")

    def test_wp17_pinned_timer_claim_not_armed(self):
        reg,agents,threads,view=fixture(end=False)
        row=examine(reg,agents,threads,view)
        self.assertEqual(row["fallback"],"NOT_ARMED")


if __name__=="__main__":unittest.main(verbosity=2)
