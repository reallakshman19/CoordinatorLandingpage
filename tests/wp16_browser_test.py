#!/usr/bin/env python3
"""WP16 real five-registry status bar Chromium and pinned-PR50 negative tests."""
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
import shutil
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import build_data
import status_bar as sb
from browser_smoke_test import start_server,find_free_port
PROJECTS=("cii-method-c","grade9-pilot","imo-ab-test","landing-live","xml229-output")


def main():
    if len(sys.argv)!=2: raise SystemExit("usage: wp16_browser_test.py <site_artifact>")
    from playwright.sync_api import sync_playwright
    passed, failed, errors=[],[],[]
    def check(name,fn):
        try: ok=bool(fn())
        except Exception as exc:
            ok=False; errors.append(name+":"+type(exc).__name__)
        (passed if ok else failed).append(name)
        print(("PASS " if ok else "FAIL ")+name)
    with tempfile.TemporaryDirectory() as tmp:
        root=Path(tmp);site=root/"site"
        expected_from_registry=0
        expected_link_count=0
        checked=datetime.now(timezone.utc)
        due=checked+timedelta(minutes=20)
        control_url="https://github.com/reallakshman19/CoordinatorLandingpage/issues/1#issuecomment-6237149165"
        shutil.copytree(Path(sys.argv[1]).resolve(),site)
        for name in PROJECTS:
            folder=root/"logs"/name
            folder.mkdir(parents=True)
            source=json.loads((ROOT/"logs"/name/"registry.json").read_text())
            if name=="grade9-pilot":
                # Conflicting identities MUST both appear and be marked.
                source["agents"][1]["chat_id8"]=source["agents"][0]["chat_id8"]
            if name=="landing-live":
                source["control"]["current_coordinator"]={
                    "holder":"OwnerTeammember","mode":"ACTING",
                    "epoch":source["control"]["epoch"],"control_ref":control_url,
                    "effective_at":(checked-timedelta(minutes=5)).isoformat(),
                    "verified":True}
                source["agents"][0]["timer_observation"]={
                    "state":"ACTIVE","last_tick":(checked-timedelta(minutes=2)).isoformat(),
                    "next_due":due.isoformat(),"checked_at":checked.isoformat(),
                    "source_ref":control_url,"verified":True}
                source["agents"][0]["browser_observation"]={
                    "result":"UP","checked_at":checked.isoformat(),
                    "source_ref":control_url,"verified":True}
            (folder/"registry.json").write_text(json.dumps(source))
            declared_rows=sb.normalize_roster(source)
            expected_from_registry+=len(declared_rows)
            expected_link_count+=sum(row["instance_id8"] is not None for row in declared_rows)
        build_data.build_all(root,site/"data",cache_dir=root/"cache")
        projection=json.loads((site/"data"/"status-bar.json").read_text())
        assert len(projection["instances"])==expected_from_registry
        server=start_server(str(site),find_free_port())
        try:
            with sync_playwright() as pw:
                browser=pw.chromium.launch(headless=True)
                page=browser.new_page(viewport={"width":1300,"height":850})
                url=f"http://127.0.0.1:{server.server_address[1]}/index.html#status-bar"
                page.goto(url,wait_until="networkidle")
                if page.locator("#wp16-mode").count():
                    page.wait_for_function("""()=>
                      document.getElementById('wp16-coverage')?.textContent.includes('%')
                    """,timeout=9000)
                check("WP16_UI_01_coverage_exact_complete",
                      lambda: page.locator("#view-status-bar").count()==1
                      and f"{expected_from_registry}/{expected_from_registry}" in page.locator("#wp16-coverage").inner_text()
                      and "100%" in page.locator("#wp16-coverage").inner_text())
                check("WP16_UI_02_ot_exact_five_project_rows",
                      lambda: page.locator("#wp16-ot-rows tr").count()==5
                      and set(page.locator("#wp16-ot-rows tr td:first-child").all_inner_texts())==set(PROJECTS))
                check("WP16_UI_03_project_hold_grey_not_green",
                      lambda: page.locator("#wp16-ot-rows tr").count()==5
                      and all("GREY" in row.inner_text() for row in
                          page.locator("#wp16-ot-rows tr").all()
                          if row.locator("td:first-child").inner_text() in
                             ("cii-method-c","xml229-output")))
                check("WP16_UI_04_grade9_dependency_prevents_any_child_green",
                      lambda: page.locator("#wp16-ot-rows tr").count()==5
                      and any("RED" in row.inner_text() and "QRT-VM" in row.inner_text()
                          for row in page.locator("#wp16-ot-rows tr").all()
                          if row.locator("td:first-child").inner_text()=="grade9-pilot"))
                if page.locator("#wp16-mode").count():
                    page.locator("#wp16-mode").select_option("tc")
                check("WP16_UI_05_tc_exact_21_instances_plus_workstream",
                      lambda: page.locator("#wp16-tc-rows tr").count()==expected_from_registry
                      and page.locator("#wp16-tc").is_visible()
                      and sum("QRT-VM" in s for s in
                          page.locator("#wp16-tc-rows tr td:nth-child(2)").all_inner_texts())==4)
                check("WP16_UI_06_duplicates_flagged_retired_preserved",
                      lambda: page.locator("#wp16-tc-rows tr").count()==expected_from_registry
                      and sum("duplicate_id8_declared" in s for s in
                          page.locator("#wp16-tc-rows tr td:last-child").all_inner_texts())>=2
                      and sum("RETIRED" in s for s in
                          page.locator("#wp16-tc-rows tr td:nth-child(8)").all_inner_texts())>=6
                      and len({x.get_attribute("data-instance-key") for x in
                          page.locator("#wp16-tc-rows tr").all()})==expected_from_registry)
                check("WP16_UI_07_links_id8_only_three_dimensions",
                      lambda: page.locator("#wp16-tc-rows tr").count()==expected_from_registry
                      and page.locator("#wp16-tc-rows .wp16-chat-id8").count()==expected_link_count
                      and all(len(x.inner_text())==8 and
                          x.get_attribute("href")=="https://chatgpt.com/c/"+x.inner_text()
                          for x in page.locator(".wp16-chat-id8").all())
                      and all("last " in x and "next " in x for x in
                          page.locator("#wp16-tc-rows tr td:nth-child(9)").all_inner_texts())
                      and all(" · " in x for x in
                          page.locator("#wp16-tc-rows tr td:nth-child(10)").all_inner_texts()))
                if page.locator("#wp16-mode").count():
                    check("WP_L7_UI_08_coordinator_acting_link_and_unknown",
                          lambda: "OwnerTeammember" in page.locator(
                              "#wp16-ot-rows tr").filter(has_text="landing-live").first.inner_text()
                          and "ACTING" in page.locator(
                              "#wp16-ot-rows tr").filter(has_text="landing-live").first.inner_text()
                          and page.locator("#wp16-ot-rows tr").filter(
                              has_text="landing-live").first.locator(
                              "a.wp16-control-ref").get_attribute("href")==control_url
                          and "UNKNOWN" in page.locator(
                              "#wp16-ot-rows tr").filter(has_text="imo-ab-test").first.inner_text())
                    check("WP_L7_UI_09_agent_timer_browser_observed",
                          lambda: "ACTIVE" in page.locator(
                              "#wp16-tc-rows tr").filter(has_text="landing-live").first.inner_text()
                          and "UP" in page.locator(
                              "#wp16-tc-rows tr").filter(has_text="landing-live").first.inner_text()
                          and "last tick" in page.locator(
                              "#wp16-tc-rows tr").filter(has_text="landing-live").first.inner_text()
                          and "next due" in page.locator(
                              "#wp16-tc-rows tr").filter(has_text="landing-live").first.inner_text()
                          and "checked" in page.locator(
                              "#wp16-tc-rows tr").filter(has_text="landing-live").first.inner_text())
                    check("WP_L7_UI_10_missing_observations_fail_unknown",
                          lambda: "UNKNOWN" in page.locator(
                              "#wp16-tc-rows tr").filter(has_text="imo-ab-test").first.inner_text()
                          and page.locator("#wp16-tc-rows tr").filter(
                              has_text="imo-ab-test").first.locator(
                              ".wp16-observation.wp16-green").count()==0)
                browser.close()
        finally: server.shutdown()
    print(f"WP16_BROWSER_COUNTS pass={len(passed)} fail={len(failed)} error={len(errors)}")
    if failed: print("WP16_BROWSER_FAILED_NAMES "+",".join(failed))
    if errors: print("WP16_BROWSER_ERROR_NAMES "+",".join(errors))
    if failed or errors: raise SystemExit(1)


if __name__=="__main__":
    main()
