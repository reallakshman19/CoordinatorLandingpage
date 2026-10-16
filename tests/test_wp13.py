#!/usr/bin/env python3
"""WP13 Next Move P1 truth boundary, approval, transitions and task-cycle tests."""
import copy
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import next_move as nm
import build_data

NOW=datetime(2026,10,16,16,0,tzinfo=timezone.utc)
SHA="a"*40
REGSHA="b"*40
FIRST="NM-20261016-140000-abcd"
SECOND="NM-20261016-140100-abce"
FROM={"role":"TeamCoordinator","id8":"11111111"}
TO={"role":"implementer","id8":"22222222"}
OTM={"role":"OwnerTeammember","id8":"11111111"}
OWNER={"role":"Owner","id8":"33333333"}
OTHER={"role":"checker","id8":"44444444"}
AGENTS=[{"chat_id8":"11111111","status":"active"},
        {"chat_id8":"22222222","status":"active"}]


def register(crit="normal"):
    result={"project":"landing-live","repository":"reallakshman19/CoordinatorLandingpage",
            "agents":copy.deepcopy(AGENTS),"control": {"hold":None},
            "_registry_sha":REGSHA,"next_move":{"pilot":True,"approval_required":True}}
    if crit=="normal":
        result.update(criticality="normal",criticality_owner_words="landing normal, proceed implementation")
    return result


def record(mid=FIRST, kind="next_step", cls="Dispatch"):
    return {"id":mid,"project":"landing-live","class":cls,"kind":kind,
            "from":copy.deepcopy(FROM),"to":copy.deepcopy(TO),
            "text":"Carry out specified task and report proof",
            "basis":{"evidence":"https://github.com/reallakshman19/CoordinatorLandingpage/issues/22",
                     "head":SHA,"registry_sha":REGSHA},
            "trigger":"GO","supersedes":None,"evidence_format":"TASK EVIDENCE v2",
            "created_at":"2026-10-16T14:00:00Z"}


def event(state, at, by=OTM, proof=None, note=None, **kw):
    d={"move":FIRST,"state":state,"by":copy.deepcopy(by),
       "at":f"2026-10-16T{at}:00Z"}
    if proof is not None: d["proof"]=proof
    if note is not None: d["note"]=note
    d.update(kw)
    return d


def claim():
    return {"by":copy.deepcopy(TO),"claimed_at":"2026-10-16T14:02:00Z",
            "expires_at":"2026-10-16T14:17:00Z"}


def checked(reg=None, rec=None, transitions=None, claims=None, now=NOW):
    rec=rec or record()
    return nm.validate_records(reg or register(),{rec["id"]+".json":rec},
                               transitions or [],claims or {},now)


class WP13Validator(unittest.TestCase):
    def test_01_registry_normal_owner_words_and_default_critical(self):
        self.assertEqual(nm.criticality(register()),"normal")
        self.assertEqual(nm.criticality(register("critical")),"critical")
        no_words=register();no_words["criticality_owner_words"]=""
        self.assertEqual(nm.criticality(no_words),"critical")

    def test_02_schema_and_dispatch_notice_kinds(self):
        moves,bad,_=checked()
        self.assertEqual(len(moves),1)
        self.assertEqual(bad,[])
        r=record(kind="agent_added",cls="Notice")
        good,bad,_=checked(rec=r)
        self.assertEqual(len(good),1)
        self.assertEqual(bad,[])
        r["kind"]="status_check"
        _,bad,_=checked(rec=r)
        self.assertIn("kind_invalid",bad[0]["reasons"])
        r=record();r["id"]="bad"
        _,bad,_=checked(rec=r)
        self.assertIn("id_or_filename_invalid",bad[0]["reasons"])

    def test_03_normal_otm_self_approval_visible(self):
        records,bad,_=checked(transitions=[event("APPROVED","14:01")])
        self.assertFalse(bad)
        self.assertTrue(records[0]["self_approved"])
        self.assertIn("self-approved",records[0]["flags"])

    def test_04_critical_self_approval_denied_and_owner_accepted(self):
        _,bad,_=checked(reg=register("critical"),
                        transitions=[event("APPROVED","14:01")])
        self.assertIn("critical_self_approval_forbidden",bad[0]["reasons"])
        good,bad,_=checked(reg=register("critical"),
                           transitions=[event("APPROVED","14:01",by=OWNER)])
        self.assertEqual(len(good),1)
        self.assertFalse(bad)

    def test_05_critical_buddy_exception_narrow_and_grant_bounded(self):
        r=record(kind="buddy_1a");r["trigger"]="chat_end_seen"
        r["from"]["id8"]="55555555"
        yes=event("APPROVED","14:01",grant_ref="approve takeover via buddy v1.7")
        good,bad,_=checked(reg=register("critical"),rec=r,transitions=[yes])
        self.assertEqual(len(good),1);self.assertFalse(bad)
        yes["grant_ref"]="not this grant"
        _,bad,_=checked(reg=register("critical"),rec=r,transitions=[yes])
        self.assertIn("critical_handover_grant_ineligible",bad[0]["reasons"])
        r["kind"]="status_check";yes["grant_ref"]="approve takeover via buddy v1.7"
        _,bad,_=checked(reg=register("critical"),rec=r,transitions=[yes])
        self.assertIn("approver_tier_invalid",bad[0]["reasons"])

    def test_06_notice_does_not_authorize_claim(self):
        r=record(kind="agent_added",cls="Notice")
        _,bad,_=checked(rec=r,transitions=[event("APPROVED","14:01")])
        self.assertIn("notice_cannot_be_approved",bad[0]["reasons"])

    def test_07_held_can_only_return_published_then_approve(self):
        badrow=[event("HELD","14:01"),event("APPROVED","14:02")]
        _,bad,_=checked(transitions=badrow)
        self.assertIn("transition_forbidden",bad[0]["reasons"])
        goodrow=[event("HELD","14:01"),
                 event("PUBLISHED","14:02",proof="new basis and grant checked",note="HOLD lifted"),
                 event("APPROVED","14:03")]
        good,bad,_=checked(transitions=goodrow)
        self.assertEqual(good[0]["state"],"APPROVED")
        self.assertFalse(bad)

    def test_08_delivery_uncertain_not_reclaimed_by_expiry(self):
        rows=[event("APPROVED","14:01"),
              event("CLAIMED","14:02",by=TO),
              event("SEND_INTENT","14:03",by=TO,proof="draft poised")]
        good,bad,_=checked(transitions=rows,claims={FIRST:claim()})
        self.assertFalse(bad)
        self.assertEqual(good[0]["state"],"DELIVERY_UNCERTAIN")
        self.assertIn("delivery uncertain",good[0]["flags"])
        rows += [event("CLAIMED","14:04",by=TO)]
        _,bad,_=checked(transitions=rows,claims={FIRST:claim()})
        self.assertIn("transition_forbidden",bad[0]["reasons"])
        rows[-1]=event("NOT_SENT","14:04",by=TO,proof="composer still full")
        good,bad,_=checked(transitions=rows,claims={FIRST:claim()})
        self.assertFalse(bad)
        self.assertEqual(good[0]["state"],"NOT_SENT")

    def test_09_claim_ttl_fail_closed(self):
        rows=[event("APPROVED","14:01"),event("CLAIMED","14:02",by=TO)]
        bad_claim=claim();bad_claim["expires_at"]="2026-10-16T14:25:00Z"
        _,bad,_=checked(transitions=rows,claims={FIRST:bad_claim})
        self.assertIn("claim_ttl_invalid",bad[0]["reasons"])
        _,bad,_=checked(transitions=rows)
        self.assertIn("claim_file_missing",bad[0]["reasons"])

    def test_10_supersedes_target_and_concurrent_dispatch(self):
        a=record();b=record(SECOND)
        b["supersedes"]="NM-20261016-000000-0000"
        _,bad,_=nm.validate_records(register(),{FIRST+".json":a,SECOND+".json":b},[],{},NOW)
        self.assertTrue(any("supersedes_target_missing" in x["reasons"] for x in bad))
        b["supersedes"]=FIRST
        moves,bad,_=nm.validate_records(register(),{FIRST+".json":a,SECOND+".json":b},[],{},NOW)
        self.assertEqual(len(moves),2);self.assertFalse(bad)
        bs=[event("APPROVED","14:01"),event("CLAIMED","14:02",by=TO)]
        bs += [dict(event("APPROVED","14:01"),move=SECOND),
               dict(event("CLAIMED","14:02",by=TO),move=SECOND)]
        moves,bad,_=nm.validate_records(register(),{FIRST+".json":a,SECOND+".json":b},
                                         bs,{FIRST:claim(),SECOND:claim()},NOW)
        self.assertFalse(moves)
        self.assertEqual(sum("concurrent_dispatch" in x["reasons"] for x in bad),2)

    def test_11_verified_is_non_doer_and_never_acceptance(self):
        rec=record()
        rows=[event("APPROVED","14:01"),event("CLAIMED","14:02",by=TO),
              event("SEND_INTENT","14:03",by=TO,proof="intent"),
              event("SENT_TO_CHAT","14:04",by=TO,proof="chat visible"),
              event("PICKED_UP","14:05",by=TO,proof="recipient reply"),
              event("ACKED","14:06",by=TO,proof="own words"),
              event("DONE_CLAIMED","14:07",by=TO,proof="evidence link"),
              event("VERIFIED","14:08",by=FROM,proof="checked")]
        _,bad,_=checked(transitions=rows,claims={FIRST:claim()})
        self.assertIn("verification_requires_non_doer",bad[0]["reasons"])
        rows[-1]=event("VERIFIED","14:08",by=OTHER,proof="independent checker")
        good,bad,_=checked(transitions=rows,claims={FIRST:claim()})
        self.assertEqual(good[0]["state"],"VERIFIED")
        self.assertFalse(bad)

    def test_12_evaluator_stale_heartbeat_and_invalid_logs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);root.mkdir(exist_ok=True)
            reg=register()
            result=nm.load_project_moves(root,reg,AGENTS,{},NOW,registry_sha=REGSHA)
            self.assertIn("evaluator stale",result["flags"])
            log={"state":"EVALUATED","at":"2026-10-16T15:45:00Z","by":OTM}
            (root/"moves.jsonl").write_text(json.dumps(log)+"\n")
            result=nm.load_project_moves(root,reg,AGENTS,{},NOW,registry_sha=REGSHA)
            self.assertNotIn("evaluator stale",result["flags"])
            (root/"moves.jsonl").write_text("{bad json")
            result=nm.load_project_moves(root,reg,AGENTS,{},NOW,registry_sha=REGSHA)
            self.assertTrue(result["rejected"])

    def test_13_cycle_mod_20_same_work_across_generations(self):
        # Real TASK EVIDENCE v2 headers; include a duplicate numerical # sequence
        # across chat changeover, but dedupe by issue COMMENT id.
        source=record()
        moves=[dict(source,state="PUBLISHED")]
        agents=[{"chat_id8":"11111111","evidence_thread_num":22},
                {"chat_id8":"22222222","evidence_thread_num":22}]
        def comments(n):
            return [{"id":i+1,"created_at":f"2026-10-16T14:{i//60:02d}:{i%60:02d}Z",
                     "body":f"TASK EVIDENCE v2 · landing-live · implementer · chat {'11111111' if i<11 else '22222222'} · #{i%11+1} · 16 Oct 18:00 +04\nTask: GO work"}
                    for i in range(n)]
        for n,expected in [(0,5),(4,5),(5,10),(10,15),(15,19),(19,25),(25,30),(39,45)]:
            cycle=nm.task_cycle(agents,{22:{"number":22,"repository":"reallakshman19/CoordinatorLandingpage",
                                          "comments":comments(n)}},moves,"landing-live",NOW)
            self.assertEqual(cycle["count"],n)
            self.assertEqual(cycle["next"],expected)
        self.assertEqual(nm.task_cycle(agents,{},[],"landing-live")["status"],"no_go")

    def test_14_live_real_registry_criticality_owner_words(self):
        reg=json.loads((ROOT/"logs"/"landing-live"/"registry.json").read_text())
        self.assertEqual(nm.criticality(reg),"normal")
        self.assertTrue((reg.get("next_move") or {}).get("pilot"))
        for other in ["cii-method-c","xml229-output"]:
            ext=json.loads((ROOT/"logs"/other/"registry.json").read_text())
            self.assertEqual(nm.criticality(ext),"critical")

    def test_15_no_automatic_move_creation_or_publisher_writes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/"logs"/"landing-live").mkdir(parents=True)
            src=json.loads((ROOT/"logs"/"landing-live"/"registry.json").read_text())
            (root/"logs"/"landing-live"/"registry.json").write_text(json.dumps(src))
            cache=root/"cache";cache.mkdir()
            build_data.build_all(root,root/"out",cache_dir=cache)
            detail=json.loads((root/"out"/"project-landing-live.json").read_text())
            summ=json.loads((root/"out"/"projects.json").read_text())
            self.assertIn("next_move",detail)
            self.assertEqual(detail["next_move"]["criticality"],"normal")
            self.assertEqual(detail["next_move"]["moves"],[])
            self.assertEqual(summ[0]["next_move"]["board"]["Verified"],[])
            self.assertFalse((root/"logs"/"landing-live"/"moves").exists())
            self.assertFalse((root/"logs"/"landing-live"/"moves.jsonl").exists())


class WP13PinnedBase(unittest.TestCase):
    """New tests remain exact; pinned main builder must fail by assertion."""

    def projection(self):
        temp=tempfile.TemporaryDirectory()
        root=Path(temp.name)
        project=root/"logs"/"landing-live"
        project.mkdir(parents=True)
        reg=json.loads((ROOT/"logs"/"landing-live"/"registry.json").read_text())
        (project/"registry.json").write_text(json.dumps(reg))
        move_dir=project/"moves"
        move_dir.mkdir()
        valid=record()
        (move_dir/(FIRST+".json")).write_text(json.dumps(valid))
        invalid=record(SECOND,kind="illegal_kind")
        (move_dir/(SECOND+".json")).write_text(json.dumps(invalid))
        thread=root/"cache"/"project-threads"/"landing-live"/"issue-22.json"
        thread.parent.mkdir(parents=True)
        comments=[
            {"id":i+1,"created_at":f"2026-10-16T14:00:0{i+1}Z",
             "body":f"TASK EVIDENCE v2 · landing-live · implementer · chat 6ad1a045 · #{i+1} · 16 Oct 18:00 +04\nTask: work"}
            for i in range(5)]
        thread.write_text(json.dumps({"number":22,"repository":HUB if False else
                                      "reallakshman19/CoordinatorLandingpage",
                                      "comments":comments}))
        build_data.build_all(root,root/"out",cache_dir=root/"cache")
        row=json.loads((root/"out"/"project-landing-live.json").read_text())
        return temp,row

    def test_wp13_pinned_rejects_invalid_move(self):
        tmp,row=self.projection()
        try:
            invalid=(row.get("next_move") or {}).get("rejected") or []
            self.assertIn(SECOND,[x.get("id","").removesuffix(".json") for x in invalid])
        finally:
            tmp.cleanup()

    def test_wp13_pinned_exposes_real_task_counter(self):
        tmp,row=self.projection()
        try:
            counter=(row.get("next_move") or {}).get("task_cycle") or {}
            self.assertEqual(counter.get("count"),5)
            self.assertEqual(counter.get("next"),10)
        finally:
            tmp.cleanup()



if __name__=="__main__":
    unittest.main(verbosity=2)
