#!/usr/bin/env python3
"""WP16 selected registry roster, light safety and 100% coverage controls."""
from datetime import datetime,timedelta,timezone
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import status_bar as sb
import build_data

NOW=datetime(2026,10,16,18,0,tzinfo=timezone.utc)
PROJECTS=("cii-method-c","grade9-pilot","imo-ab-test","landing-live","xml229-output")


def registry():
    return {"project":"demo","repository":"acme/demo",
            "control":{"hold":None},
            "agents":[{"role":"writer","chat_id8":"aabbccdd",
                       "generation":2,"status":"active",
                       "observation":{"state":"WORKING","reachable":True,
                         "observed_at":"2026-10-16T17:55:00Z"},
                       "grant":{"verified":True,"expires_at":"2026-10-16T19:00:00Z"}}]}


def view(at="2026-10-16T17:55:00Z"):
    return {"next_move":{"evaluator_at":at,"ultra_economy":{"enabled":False}}}


class WP16StatusBar(unittest.TestCase):
    def test_01_actual_all_five_registered_project_rosters(self):
        regs={p:json.loads((ROOT/"logs"/p/"registry.json").read_text()) for p in PROJECTS}
        data=sb.build_status_bar(regs,{},NOW)
        self.assertEqual(set(p["project"] for p in data["projects"]),set(PROJECTS))
        self.assertEqual(len(data["projects"]),5)
        expected_from_registry=sum(len(sb.normalize_roster(reg)) for reg in regs.values())
        self.assertEqual(data["coverage"]["expected"],expected_from_registry)
        self.assertEqual(data["coverage"]["projected"],expected_from_registry)
        self.assertEqual(data["coverage"]["expected"],expected_from_registry)
        self.assertEqual(data["coverage"]["projected"],expected_from_registry)
        self.assertEqual(data["coverage"]["percent"],100)
        self.assertTrue(data["coverage"]["complete"])

    def test_02_workstream_v_m_runner_standby_all_preserved(self):
        reg=json.loads((ROOT/"logs"/"grade9-pilot"/"registry.json").read_text())
        rows=sb.normalize_roster(reg)
        self.assertEqual(len(rows),12)
        self.assertEqual(len([r for r in rows if r["workstream"]=="QRT-VM"]),4)
        self.assertEqual({r["kind"] for r in rows if r["workstream"]=="QRT-VM"},
                         {"agent","execution_runner","standby"})
        self.assertEqual(len({r["key"] for r in rows}),12)

    def test_03_retired_not_lost_or_counted_active(self):
        reg=json.loads((ROOT/"logs"/"grade9-pilot"/"registry.json").read_text())
        rows=sb.normalize_roster(reg)
        self.assertGreaterEqual(sum(x["retired"] for x in rows),6)
        data=sb.build_status_bar({"grade9-pilot":reg},{},NOW)
        self.assertEqual(data["projects"][0]["historical_retired_count"],
                         sum(x["retired"] for x in rows))

    def test_04_duplicate_id8_flagged_not_deduplicated(self):
        reg=registry()
        reg["workstreams"]={"W":{"agents":[{"chat_id8":"aabbccdd","role":"reviewer"}]}}
        rows=sb.normalize_roster(reg)
        self.assertEqual(len(rows),2)
        self.assertTrue(all("duplicate_id8_declared:aabbccdd" in x["conflicts"]
                            for x in rows))
        self.assertNotEqual(rows[0]["key"],rows[1]["key"])
        result=sb.build_status_bar({"demo":reg},{"demo":view()},NOW)
        self.assertEqual(result["coverage"]["expected"],2)
        self.assertEqual(result["projects"][0]["light"],"red")

    def test_05_invalid_missing_id8_row_not_hidden(self):
        reg=registry()
        reg["standbys"]=[{"role":"standby missing identifier"}]
        rows=sb.normalize_roster(reg)
        self.assertEqual(len(rows),2)
        self.assertIsNone(rows[1]["chat_link"])
        self.assertIn("missing_or_invalid_id8",rows[1]["conflicts"])
        data=sb.build_status_bar({"demo":reg},{"demo":view()},NOW)
        self.assertTrue(data["coverage"]["complete"])
        self.assertEqual(len(data["instances"]),2)

    def test_06_three_dimensions_green_only_with_real_fresh_sources(self):
        reg=registry()
        status=sb.derive_status(sb.normalize_roster(reg)[0],reg,view(),NOW)
        self.assertEqual(status["light"],"green")
        self.assertEqual(status["dimensions"]["work"]["state"],"running")
        self.assertEqual(status["dimensions"]["monitoring"]["state"],"fresh")
        self.assertEqual(status["dimensions"]["execution_authority"]["state"],"allowed")

    def test_07_unknown_or_stale_monitoring_yellow(self):
        reg=registry()
        row=sb.normalize_roster(reg)[0]
        self.assertEqual(sb.derive_status(row,reg,{"next_move":{}},NOW)["light"],"yellow")
        self.assertEqual(sb.derive_status(row,reg,view("2026-10-16T16:00:00Z"),NOW)["light"],"yellow")
        reg["agents"][0].pop("observation")
        self.assertEqual(sb.derive_status(sb.normalize_roster(reg)[0],reg,view(),NOW)["light"],"yellow")

    def test_08_execution_authority_unverified_cannot_green(self):
        reg=registry()
        reg["agents"][0].pop("grant")
        status=sb.derive_status(sb.normalize_roster(reg)[0],reg,view(),NOW)
        self.assertEqual(status["light"],"yellow")
        self.assertEqual(status["dimensions"]["execution_authority"]["state"],"unknown")
        reg["agents"][0]["grant"]={"verified":True,"expires_at":"2026-10-16T17:00:00Z"}
        self.assertEqual(sb.derive_status(sb.normalize_roster(reg)[0],reg,view(),NOW)["light"],"red")

    def test_09_hard_block_red_and_project_hold_grey(self):
        reg=registry()
        reg["agents"][0]["status"]="blocked"
        self.assertEqual(sb.derive_status(sb.normalize_roster(reg)[0],reg,view(),NOW)["light"],"red")
        reg["control"]["hold"]="Owner HOLD"
        self.assertEqual(sb.derive_status(sb.normalize_roster(reg)[0],reg,view(),NOW)["light"],"grey")
        self.assertEqual(sb.build_status_bar({"demo":reg},{"demo":view()},NOW)["projects"][0]["light"],"grey")

    def test_10_COMPLETE_separate_never_implies_green(self):
        reg=registry()
        reg["agents"][0]["status"]="DONE"
        row=sb.derive_status(sb.normalize_roster(reg)[0],reg,view(),NOW)
        self.assertTrue(row["complete"])
        self.assertNotEqual(row["light"],"green")

    def test_11_project_requires_every_active_dependency(self):
        reg=registry()
        reg["agents"].append({"chat_id8":"eeff0011","role":"checker","status":"waiting"})
        p=sb.build_status_bar({"demo":reg},{"demo":view()},NOW)["projects"][0]
        self.assertEqual(p["light"],"yellow")
        reg["workstreams"]={"gated":{"state":"CODE_HOLD","material_release":False}}
        p=sb.build_status_bar({"demo":reg},{"demo":view()},NOW)["projects"][0]
        self.assertEqual(p["light"],"red")
        self.assertEqual(p["dependencies"]["blocked"],["gated"])

    def test_12_no_active_agents_does_not_go_green(self):
        reg=registry()
        reg["agents"][0]["status"]="retired"
        p=sb.build_status_bar({"demo":reg},{"demo":view()},NOW)["projects"][0]
        self.assertEqual(p["light"],"yellow")
        self.assertEqual(p["active_count"],0)

    def test_13_workstream_standby_cannot_confer_execution_authority(self):
        reg=registry()
        reg["workstreams"]={"W":{"standby":{"chat_id8":"00112233",
                                               "state":"OWNER_SELECTED_NOT_QUALIFIED"}}}
        data=sb.build_status_bar({"demo":reg},{"demo":view()},NOW)
        s=next(x for x in data["instances"] if x["kind"]=="standby")
        self.assertEqual(s["dimensions"]["execution_authority"]["state"],"waiting")
        self.assertNotEqual(s["light"],"green")

    def test_14_cycle_balance_separate_from_nm_counter(self):
        reg=registry()
        um={"enabled":True,"max_cycles":1,"agents":{"aabbccdd":{"cycle":1}}}
        projection={"next_move":{"evaluator_at":"2026-10-16T17:55:00Z",
                                "ultra_economy":um,
                                "task_cycle":{"count":19}}}
        out=sb.derive_status(sb.normalize_roster(reg)[0],reg,projection,NOW)
        self.assertEqual(out["light"],"yellow")
        self.assertEqual(out["dimensions"]["execution_authority"]["reason"],
                         "uem_cycle_limit_reached")

    def test_15_selected_registry_name_mismatch_fails_closed(self):
        with self.assertRaisesRegex(ValueError,"name_mismatch"):
            sb.build_status_bar({"other":registry()}, {},NOW)

    def test_16_builder_publishes_single_same_projection_and_full_coverage(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            for project in PROJECTS:
                target=root/"logs"/project
                target.mkdir(parents=True)
                (target/"registry.json").write_text(
                    (ROOT/"logs"/project/"registry.json").read_text())
            build_data.build_all(root,root/"out",cache_dir=root/"cache")
            doc=json.loads((root/"out"/"status-bar.json").read_text())
            projects=json.loads((root/"out"/"projects.json").read_text())
            expected_from_registry=sum(
                len(sb.normalize_roster(json.loads((ROOT/"logs"/p/"registry.json").read_text())))
                for p in PROJECTS)
            self.assertEqual(len(doc["instances"]),expected_from_registry)
            self.assertEqual(doc["coverage"]["percent"],100)
            self.assertEqual(len(doc["instances"]),expected_from_registry)
            self.assertEqual(len(projects),len(doc["projects"]))
            self.assertEqual({p["project"]:p["status_bar"] for p in projects},
                             {p["project"]:p for p in doc["projects"]})


    def test_17_control_record_normal_and_acting(self):
        reg=registry(); reg["control"]["epoch"]=4
        ref="https://github.com/acme/demo/issues/1#issuecomment-123"
        for mode,holder in (("NORMAL","Codex"),("ACTING","OwnerTeammember")):
            with self.subTest(mode=mode):
                reg["control"]["current_coordinator"]={
                    "holder":holder,"mode":mode,"epoch":4,"control_ref":ref,
                    "effective_at":"2026-10-16T17:30:00Z","verified":True}
                out=sb.build_status_bar({"demo":reg},{},NOW)
                self.assertEqual(out["projects"][0]["coordinator"]["holder"],holder)
                self.assertEqual(out["projects"][0]["coordinator"]["mode"],mode)
                self.assertEqual(out["projects"][0]["coordinator"]["control_ref"],ref)

    def test_18_missing_invalid_or_unverified_coordinator_is_unknown(self):
        reg=registry(); reg["control"]["epoch"]=4
        self.assertEqual(sb.build_status_bar({"demo":reg},{},NOW)
                         ["projects"][0]["coordinator"]["mode"],"UNKNOWN")
        record={"holder":"OwnerTeammember","mode":"ACTING","epoch":4,
                "control_ref":"https://github.com/acme/demo/issues/1#issuecomment-123",
                "effective_at":"2026-10-16T17:30:00Z","verified":True}
        for patch in ({"verified":False},{"epoch":3},
                      {"control_ref":"not a CONTROL link"},
                      {"effective_at":"2026-10-17T12:00:00Z"}):
            with self.subTest(patch=patch):
                reg["control"]["current_coordinator"]={**record,**patch}
                self.assertEqual(sb.build_status_bar({"demo":reg},{},NOW)
                                 ["projects"][0]["coordinator"]["mode"],"UNKNOWN")

    def test_19_verified_timer_browser_additive_without_light_changes(self):
        reg=registry(); agent=reg["agents"][0]
        base=sb.build_status_bar({"demo":reg},{"demo":view()},NOW)
        ref="https://github.com/acme/demo/issues/1#issuecomment-123"
        agent["timer_observation"]={"state":"ACTIVE","last_tick":"2026-10-16T17:50:00Z",
            "next_due":"2026-10-16T18:20:00Z","checked_at":"2026-10-16T17:55:00Z",
            "source_ref":ref,"verified":True}
        agent["browser_observation"]={"result":"UP","checked_at":"2026-10-16T17:56:00Z",
                                     "source_ref":ref,"verified":True}
        out=sb.build_status_bar({"demo":reg},{"demo":view()},NOW)
        self.assertEqual(out["instances"][0]["timer"]["state"],"ACTIVE")
        self.assertEqual(out["instances"][0]["timer"]["next_due"],"2026-10-16T18:20:00+00:00")
        self.assertEqual(out["instances"][0]["browser"]["result"],"UP")
        self.assertEqual(out["instances"][0]["browser"]["checked_at"],"2026-10-16T17:56:00+00:00")
        self.assertEqual(out["instances"][0]["light"],base["instances"][0]["light"])
        self.assertEqual(out["coverage"],base["coverage"])

    def test_20_missing_stale_unverified_never_claims_active_or_up(self):
        reg=registry(); agent=reg["agents"][0]
        ref="https://github.com/acme/demo/issues/1#issuecomment-123"
        def instance():
            return sb.build_status_bar({"demo":reg},{},NOW)["instances"][0]
        self.assertEqual(instance()["timer"]["state"],"UNKNOWN")
        self.assertEqual(instance()["browser"]["result"],"UNKNOWN")
        for checked,verified,source in (
            ("2026-10-16T16:50:00Z",True,ref),
            ("2026-10-16T17:55:00Z",False,ref),
            ("2026-10-16T17:55:00Z",True,"untrusted")):
            agent["timer_observation"]={"state":"ACTIVE","checked_at":checked,
                "verified":verified,"source_ref":source}
            agent["browser_observation"]={"result":"UP","checked_at":checked,
                "verified":verified,"source_ref":source}
            self.assertEqual(instance()["timer"]["state"],"UNKNOWN")
            self.assertEqual(instance()["browser"]["result"],"UNKNOWN")
        agent["timer_observation"]["state"]="PAUSED"
        agent["timer_observation"].update(checked_at="2026-10-16T17:55:00Z",
                                           verified=True,source_ref=ref)
        self.assertEqual(instance()["timer"]["state"],"PAUSED")

    def test_21_builder_passes_registry_control_and_observations(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            for project in PROJECTS:
                target=root/"logs"/project; target.mkdir(parents=True)
                reg=json.loads((ROOT/"logs"/project/"registry.json").read_text())
                if project=="landing-live":
                    reg["control"]["current_coordinator"]={
                        "holder":"OwnerTeammember","mode":"ACTING",
                        "epoch":reg["control"]["epoch"],
                        "control_ref":"https://github.com/acme/demo/issues/1#issuecomment-123",
                        "effective_at":"2026-10-16T17:00:00Z","verified":True}
                (target/"registry.json").write_text(json.dumps(reg))
            build_data.build_all(root,root/"out",cache_dir=root/"cache")
            projected=json.loads((root/"out"/"status-bar.json").read_text())
            target=next(p for p in projected["projects"] if p["project"]=="landing-live")
            self.assertEqual(target["coordinator"]["mode"],"ACTING")


    def test_22_malformed_control_never_crashes_or_confers_coordinator(self):
        for value in ("not-a-control", ["not", "a", "dict"], 7):
            with self.subTest(control=value):
                reg=registry();reg["control"]=value
                out=sb.build_status_bar({"demo":reg},{"demo":view()},NOW)
                self.assertEqual(out["projects"][0]["coordinator"]["mode"],"UNKNOWN")
                self.assertEqual(out["coverage"]["projected"],1)
                self.assertEqual(out["instances"][0]["light"],"green")

    def test_23_control_requires_explicit_verified_true(self):
        reg=registry();reg["control"]["epoch"]=4
        record={"holder":"Acting TC","mode":"ACTING","epoch":4,
                "control_ref":"https://github.com/acme/demo/issues/1#issuecomment-123",
                "effective_at":"2026-10-16T17:30:00Z"}
        for extra in ({},{"verified":False},{"verified":None},{"verified":"true"}):
            with self.subTest(extra=extra):
                reg["control"]["current_coordinator"]={**record,**extra}
                out=sb.build_status_bar({"demo":reg},{},NOW)
                self.assertEqual(out["projects"][0]["coordinator"]["mode"],"UNKNOWN")
        reg["control"]["current_coordinator"]={**record,"verified":True}
        self.assertEqual(sb.build_status_bar({"demo":reg},{},NOW)
                         ["projects"][0]["coordinator"]["mode"],"ACTING")

    def test_24_overdue_or_missing_next_due_never_active(self):
        reg=registry()
        baseline=sb.build_status_bar({"demo":reg},{},NOW)["instances"][0]["light"]
        ref="https://github.com/acme/demo/issues/1#issuecomment-123"
        timer={"state":"ACTIVE","checked_at":"2026-10-16T17:55:00Z",
               "last_tick":"2026-10-16T17:50:00Z",
               "source_ref":ref,"verified":True}
        for due in ("2026-10-16T17:59:00Z","2026-10-16T18:00:00Z",None):
            with self.subTest(next_due=due):
                reg["agents"][0]["timer_observation"]={**timer,"next_due":due}
                out=sb.build_status_bar({"demo":reg},{},NOW)
                self.assertEqual(out["instances"][0]["timer"]["state"],"UNKNOWN")
                self.assertEqual(out["instances"][0]["light"],baseline)
        reg["agents"][0]["timer_observation"]={**timer,
                                                "next_due":"2026-10-16T18:20:00Z"}
        self.assertEqual(sb.build_status_bar({"demo":reg},{},NOW)
                         ["instances"][0]["timer"]["state"],"ACTIVE")

class WP16PinnedBase(unittest.TestCase):
    """Old PR #50 publisher fails these exact two assertions (0 ERROR)."""
    def test_wp16_pinned_registry_projection_absent(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);p=root/"logs"/"landing-live";p.mkdir(parents=True)
            (p/"registry.json").write_text(
                (ROOT/"logs"/"landing-live"/"registry.json").read_text())
            build_data.build_all(root,root/"out",cache_dir=root/"cache")
            path=root/"out"/"status-bar.json"
            self.assertTrue(path.is_file(),"missing published roster projection")

    def test_wp16_pinned_project_row_lacks_shared_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);p=root/"logs"/"landing-live";p.mkdir(parents=True)
            (p/"registry.json").write_text(
                (ROOT/"logs"/"landing-live"/"registry.json").read_text())
            build_data.build_all(root,root/"out",cache_dir=root/"cache")
            projects=json.loads((root/"out"/"projects.json").read_text())
            self.assertEqual(projects[0].get("status_bar",{}).get("selected_roster_coverage",{}).get("complete"),
                             True,"missing shared project coverage report")

if __name__=="__main__":
    unittest.main(verbosity=2)
