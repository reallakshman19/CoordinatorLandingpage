#!/usr/bin/env python3
"""WP15 read-only evaluator and WP14 follow-up regression tests."""
import base64
from datetime import datetime, timedelta, timezone
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
from contextlib import redirect_stdout

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import build_data
import next_move as nm
import next_move_claim as claims
import next_move_evaluator as ev
from tests.test_wp14 import FakeTransport, register, record, event, claim, REGSHA, SHA, FIRST, TO

NOW=datetime(2026,10,16,16,0,tzinfo=timezone.utc)
ACTOR={"role":"TeamCoordinator","id8":"11111111"}
REPO="reallakshman19/CoordinatorLandingpage"


def five_comments():
    return [{"id":i+1,"created_at":f"2026-10-16T14:00:{i+1:02d}Z",
             "body":f"TASK EVIDENCE v2 · landing-live · implementer · chat 22222222 · #{i+1} · 16 Oct 18:00 +04\nTask: active work"}
            for i in range(5)]


def fixture(root, *, heartbeat=None, count=5):
    folder=root/"logs"/"landing-live";folder.mkdir(parents=True,exist_ok=True)
    reg=register()
    reg.pop("_registry_sha",None)
    reg["agents"]=[{"chat_id8":TO["id8"],"role":"implementer",
                    "evidence_thread":"https://github.com/"+REPO+"/issues/22"}]
    (folder/"registry.json").write_text(json.dumps(reg))
    (folder/"moves").mkdir(exist_ok=True)
    (folder/"moves"/(FIRST+".json")).write_text(json.dumps(record()))
    if heartbeat:
        (folder/"moves.jsonl").write_text(json.dumps({
            "state":"EVALUATED","at":heartbeat,"by":ACTOR})+"\n")
    threads={22:{"number":22,"repository":REPO,"comments":five_comments()[:count]}}
    agent={"chat_id8":TO["id8"],"evidence_thread_num":22}
    view=nm.load_project_moves(folder,reg,[agent],threads,now=NOW,registry_sha=REGSHA)
    return reg,view,[agent],threads


def proposal(reg,view,agents,threads,now=NOW,root=None):
    return ev.evaluate(reg,view,agents,threads,now,ACTOR,REGSHA,
                       published=view,root=root)


class WP15EvaluatorTests(unittest.TestCase):
    def test_01_due_5_10_15_ground_and_19_reconcile(self):
        for count,kind in [(5,"ground"),(10,"ground"),(15,"ground"),
                           (19,"reconcile"),(25,"ground"),(39,"reconcile")]:
            with tempfile.TemporaryDirectory() as tmp:
                reg,view,agents,threads=fixture(Path(tmp),count=5)
                # Extend comments with unique actual evidence ids and timestamps.
                threads[22]["comments"]=[
                    {"id":i+1,"created_at":f"2026-10-16T14:{i//60:02d}:{i%60:02d}Z",
                     "body":f"TASK EVIDENCE v2 · landing-live · implementer · chat 22222222 · #{i+1} · 16 Oct 18:00 +04\nTask: active work"}
                    for i in range(count)]
                view=nm.load_project_moves(Path(tmp)/"logs"/"landing-live",reg,
                       agents,threads,now=NOW,registry_sha=REGSHA)
                row=proposal(reg,view,agents,threads)
                self.assertEqual(view["task_cycle"]["due"],kind)
                self.assertEqual(row["trigger_notices"][0]["kind"],kind)
                self.assertEqual(row["trigger_notices"][0]["status"],"detected, not acted on")
                self.assertEqual(row["heartbeat_proposal"]["state"],"EVALUATED")
                self.assertFalse(row["heartbeat_committed"])

    def test_02_not_due_or_no_go_no_imagined_task(self):
        with tempfile.TemporaryDirectory() as tmp:
            reg,view,agents,threads=fixture(Path(tmp),count=4)
            view=nm.load_project_moves(Path(tmp)/"logs"/"landing-live",reg,
                                       agents,threads,now=NOW,registry_sha=REGSHA)
            self.assertFalse(proposal(reg,view,agents,threads)["trigger_notices"])
            (Path(tmp)/"logs"/"landing-live"/"moves"/(FIRST+".json")).unlink()
            no_go=nm.load_project_moves(Path(tmp)/"logs"/"landing-live",reg,
                                         agents,threads,now=NOW,registry_sha=REGSHA)
            self.assertEqual(no_go["task_cycle"]["status"],"no_go")
            self.assertFalse(proposal(reg,no_go,agents,threads)["trigger_notices"])

    def test_03_chat_end_confirmed_not_raw_text(self):
        with tempfile.TemporaryDirectory() as tmp:
            reg,view,agents,threads=fixture(Path(tmp),count=4)
            reg["chat_end_seen"]={"confirmed":True,"at":"2026-10-16T14:15:00Z",
                                  "chat_id8":TO["id8"]}
            out=proposal(reg,view,agents,threads)
            self.assertEqual([x["signal"] for x in out["trigger_notices"]],
                             ["chat_end_seen"])
            reg["chat_end_seen"]["confirmed"]=False
            self.assertEqual(proposal(reg,view,agents,threads)["trigger_notices"],[])

    def test_04_meter_self_reported_or_unknown(self):
        with tempfile.TemporaryDirectory() as tmp:
            reg,view,agents,threads=fixture(Path(tmp),count=4)
            reg["agents"][0]["handover_meter"]={
                "self_reported":False,"value":94,"warning_level":90,
                "at":"2026-10-16T15:00:00Z"}
            self.assertFalse(proposal(reg,view,agents,threads)["trigger_notices"])
            reg["agents"][0]["handover_meter"]["self_reported"]=True
            self.assertEqual(proposal(reg,view,agents,threads)[
                "trigger_notices"][0]["signal"],"handover_meter")
            reg["agents"][0]["handover_meter"]["value"]=89
            self.assertFalse(proposal(reg,view,agents,threads)["trigger_notices"])

    def test_05_registered_no_ack_requires_explicit_false(self):
        with tempfile.TemporaryDirectory() as tmp:
            reg,view,agents,threads=fixture(Path(tmp),count=4)
            reg["agents"][0].update(registered_at="2026-10-16T15:00:00Z",
                                    own_words_ack=False)
            self.assertEqual(proposal(reg,view,agents,threads)[
                "trigger_notices"][0]["kind"],"status_check")
            reg["agents"][0]["own_words_ack"]=True
            self.assertFalse(proposal(reg,view,agents,threads)["trigger_notices"])

    def test_06_evidence_head_moved_project_scoped(self):
        with tempfile.TemporaryDirectory() as tmp:
            reg,view,agents,threads=fixture(Path(tmp),count=4)
            agents[0]["evidence_head_status"]={
                "status":"superseded","pr_url":"https://github.com/"+REPO+"/pull/47",
                "current_head":"a"*40}
            self.assertEqual(proposal(reg,view,agents,threads)[
                "trigger_notices"][0]["signal"],"evidence_head_moved")
            agents[0]["evidence_head_status"]["status"]="unknown"
            self.assertFalse(proposal(reg,view,agents,threads)["trigger_notices"])

    def test_07_owner_words_and_decision_age(self):
        with tempfile.TemporaryDirectory() as tmp:
            reg,view,agents,threads=fixture(Path(tmp),count=4)
            reg["handover_owner_words"]={"text":"please hand over","at":"2026-10-16T15:00:00Z"}
            reg["open_owner_decisions"]=[{"id":"OD-1","status":"open",
                                          "created_at":"2026-10-16T14:00:00Z"}]
            notices=proposal(reg,view,agents,threads)["trigger_notices"]
            self.assertEqual([n["signal"] for n in notices],
                             ["owner_handover","owner_decision_age"])
            self.assertIsNone(notices[1]["kind"])
            self.assertEqual(notices[1]["status"],"observed_only")

    def test_08_label_missing_only_for_pinned_real_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);reg,view,agents,threads=fixture(root,count=4)
            reg["engineering_pr_delivery"]="v3.6";reg["engineering_work"]="LIVE"
            x=proposal(reg,view,agents,threads,root=root)
            self.assertEqual(x["trigger_notices"][0]["signal"],"label_missing")
            path=root/"relay"/"AIM"/"LIVE.yaml";path.parent.mkdir(parents=True)
            path.write_text("label: only fixture")
            self.assertFalse(proposal(reg,view,agents,threads,root=root)["trigger_notices"])

    def test_09_explicit_analysis_drift_not_inferred_from_prose(self):
        with tempfile.TemporaryDirectory() as tmp:
            reg,view,agents,threads=fixture(Path(tmp),count=4)
            threads[22]["comments"]=[
                {"created_at":f"2026-10-16T15:00:0{i}Z","kind":"analysis_only"}
                for i in range(3)]
            self.assertEqual(proposal(reg,view,agents,threads)[
                "trigger_notices"][0]["signal"],"analysis_drift")
            threads[22]["comments"][2]["kind"]="task_evidence"
            self.assertFalse(proposal(reg,view,agents,threads)["trigger_notices"])

    def test_10_page_mismatch_exact_source_and_stale_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            reg,view,agents,threads=fixture(Path(tmp),count=4)
            report=proposal(reg,view,agents,threads)
            self.assertEqual(ev.cross_check(view,report,REGSHA,NOW)["status"],"match")
            report["snapshot"]["flags"]=["deliberate mismatch"]
            cross=ev.cross_check(view,report,REGSHA,NOW)
            self.assertEqual(cross["status"],"mismatch")
            self.assertIn("flags",cross["mismatches"])
            self.assertEqual(ev.cross_check(view,report,"c"*40,NOW)["status"],
                             "untrusted_or_stale_source")
            self.assertEqual(ev.cross_check(view,report,REGSHA,
                 NOW+timedelta(minutes=31))["status"],"stale_output")
            self.assertEqual(ev.cross_check(view,None,REGSHA,NOW)["status"],
                             "not_recorded")

    def test_11_heartbeat_row_proposal_does_not_write_ledger(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);reg,view,agents,threads=fixture(root,count=4)
            path=root/"logs"/"landing-live"/"moves.jsonl"
            self.assertFalse(path.exists())
            report=proposal(reg,view,agents,threads)
            self.assertEqual(report["heartbeat_proposal"]["by"],ACTOR)
            self.assertFalse(path.exists())
            self.assertTrue(report["read_only"])
            self.assertFalse(report["may_send"])

    def test_12_owner_normalization_same_for_validator_and_input(self):
        reg=register()
        candidate=dict(record(),state="PUBLISHED")
        proposal_row={"project":"landing-live","type":"NEXT_MOVE_APPROVAL",
                      "text":json.dumps({"move":FIRST,
                            "by":{"role":" O_w n e r ","id8":"33333333"}})}
        result=nm.validate_input_request(reg,proposal_row,[candidate],
                {"author_association":"COLLABORATOR","flags":[]})
        self.assertEqual(result["reason"],"owner_identity_not_verified")
        result=nm.validate_input_request(reg,proposal_row,[candidate],
                {"author_association":"OWNER","flags":[]})
        self.assertTrue(result["valid"]);self.assertFalse(result["effective"])

    def test_13_conflict_409_and_422_mapped_to_claim_refused(self):
        api=claims.GHTransport()
        for status in (409,422):
            with mock.patch.object(subprocess,"run",side_effect=subprocess.CalledProcessError(
                    1,"gh",stderr=f"HTTP {status}: conflict")):
                with self.assertRaisesRegex(claims.ClaimRefused,"conflict"):
                    api.put("/repos/"+REPO+"/contents/a",{"content":"abc"})

    def test_14_expiry_cas_takeover_same_recipient_no_send_intent(self):
        previous=claim()
        previous["by"]={"role":"previous holder","id8":TO["id8"]}
        api=FakeTransport(existing=previous,rows=[
            event("APPROVED","14:01"),event("CLAIMED","14:02",by=TO)])
        at=datetime(2026,10,16,14,22,tzinfo=timezone.utc)
        claims.make_claim(api,"main",FIRST,REGSHA,TO,"renew",now=at)
        self.assertEqual(api.sent[0][1]["sha"],"c"*40)
        new=json.loads(base64.b64decode(api.sent[0][1]["content"]))
        self.assertEqual(new["by"],TO)
        self.assertLessEqual(nm.stamp(new["expires_at"])-at,timedelta(minutes=15))
        # Still forbidden if the move has an unresolved send intent.
        api=FakeTransport(existing=previous,rows=[
            event("APPROVED","14:01"),event("CLAIMED","14:02",by=TO),
            event("SEND_INTENT","14:03",by=TO,proof="draft open")])
        with self.assertRaises(claims.ClaimRefused):
            claims.make_claim(api,"main",FIRST,REGSHA,TO,"renew",now=at)
        self.assertFalse(api.sent)

    def test_15_real_project_pilot_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            reg,view,agents,threads=fixture(Path(tmp),count=4)
            reg["project"]="cii-method-c"
            with self.assertRaisesRegex(ValueError,"restricted"):
                proposal(reg,view,agents,threads)

    def test_16_cli_stdout_and_opt_in_file_outside_logs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);reg,view,agents,threads=fixture(root,count=4)
            sha=build_data.git_blob_sha(root/"logs"/"landing-live"/"registry.json")
            projected={"project":"landing-live","agents":agents,
                       "registry_blob_sha":sha,"next_move":view}
            src=root/"project-landing-live.json"
            src.write_text(json.dumps(projected))
            cache=root/"cache"/"project-threads"/"landing-live"
            cache.mkdir(parents=True)
            (cache/"issue-22.json").write_text(json.dumps(threads[22]))
            resultfile=root/"output"/"evaluator-proposal.json"
            with redirect_stdout(io.StringIO()) as stdout:
                row=ev.main(["--root",str(root),"--cache-dir","cache",
                    "--projection",str(src),"--actor-role","TeamCoordinator",
                    "--actor-id8","11111111","--at","2026-10-16T16:00:00Z",
                    "--output",str(resultfile)])
            self.assertEqual(row["heartbeat_proposal"]["state"],"EVALUATED")
            self.assertTrue(resultfile.exists())
            self.assertEqual(json.loads(stdout.getvalue())["schema"],ev.SCHEMA)
            self.assertFalse((root/"logs"/"landing-live"/"moves.jsonl").exists())
            with self.assertRaises(SystemExit):
                ev.main(["--root",str(root),"--projection",str(src),
                         "--actor-role","TeamCoordinator","--actor-id8","11111111",
                         "--at","2026-10-16T16:00:00Z",
                         "--output",str(root/"logs"/"landing-live"/"moves.jsonl")])

    def test_16_no_committed_evaluation_is_explicit_not_recorded(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);reg,view,agents,threads=fixture(root,count=4)
            out=root/"out"
            build_data.build_all(root,out,cache_dir=root/"cache")
            data=json.loads((out/"project-landing-live.json").read_text())
            self.assertEqual(data["next_move"]["evaluator_cross_check"]["status"],
                             "not_recorded")
            self.assertFalse((root/"logs"/"landing-live"/"next-move-evaluation.json").exists())


class WP15PinnedBase(unittest.TestCase):
    """Both fail on pinned WP14 builder with no cross-check projection."""
    def test_wp15_pinned_evaluator_report_missing_is_explicit(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);fixture(root,count=4);out=root/"out"
            build_data.build_all(root,out,cache_dir=root/"cache")
            view=json.loads((out/"project-landing-live.json").read_text())["next_move"]
            self.assertEqual(view.get("evaluator_cross_check",{}).get("status"),
                             "not_recorded")

    def test_wp15_pinned_evaluator_mismatch_is_visible(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);reg,view,agents,threads=fixture(root,count=4)
            registry_path=root/"logs"/"landing-live"/"registry.json"
            sha=build_data.git_blob_sha(registry_path)
            report=proposal(reg,view,agents,threads)
            report["registry_sha"]=sha
            report["at"]=datetime.now(timezone.utc).isoformat()
            report["snapshot"]["criticality"]="critical"
            (registry_path.parent/"next-move-evaluation.json").write_text(json.dumps(report))
            out=root/"out"
            build_data.build_all(root,out,cache_dir=root/"cache")
            data=json.loads((out/"project-landing-live.json").read_text())
            cross=data["next_move"].get("evaluator_cross_check",{})
            self.assertEqual(cross.get("status"),"mismatch")
            self.assertIn("criticality",cross.get("mismatches",[]))


if __name__=="__main__":
    unittest.main(verbosity=2)
