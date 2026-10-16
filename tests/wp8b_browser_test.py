#!/usr/bin/env python3
"""WP8b: timestamp traceability and Home shortcut in actual Chromium."""
import json
from pathlib import Path
import shutil
import sys
import tempfile

from browser_smoke_test import find_free_port, start_server

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import build_data

def main():
    if len(sys.argv)!=2: raise SystemExit("usage: python tests/wp8b_browser_test.py <artifact>")
    from playwright.sync_api import sync_playwright
    ok,failed,errors=[],[],[]
    def check(key,fn):
        try: good=bool(fn())
        except Exception as exc:
            good=False
            errors.append(key+"="+type(exc).__name__)
        (ok if good else failed).append(key)
        print(("PASS " if good else "FAIL ")+key)

    with tempfile.TemporaryDirectory() as td:
        folder=Path(td)/"site"
        shutil.copytree(Path(sys.argv[1]).resolve(),folder)
        fixture=json.loads((ROOT/"tests/fixtures/f7_owner_issue31_replay.json").read_text())
        records=build_data.build_owner_inputs(fixture["issues"],fixture["capture"])
        (folder/"data"/"owner-inputs.json").write_text(json.dumps(records))
        projects_path=folder/"data"/"projects.json"
        projects=json.loads(projects_path.read_text())
        for project in projects:
            if project.get("project")=="grade9-pilot":
                for decision in project.get("open_owner_decisions",[]):
                    if decision.get("id")=="G9-DIFF-13":
                        decision["asked_at"]="2026-10-15T15:10:00Z"
        projects_path.write_text(json.dumps(projects))
        port=find_free_port()
        server=start_server(str(folder),port)
        try:
            with sync_playwright() as pw:
                browser=pw.chromium.launch(headless=True)
                page=browser.new_page(viewport={"width":1100,"height":900})
                base=f"http://127.0.0.1:{port}/index.html"
                page.goto(base+"#home",wait_until="networkidle",timeout=20000)
                check("WP8B_UI_01_home_new_input_top_right_visible",
                      lambda: page.locator("#home-new-input").count()==1
                      and page.locator("#home-new-input").is_visible()
                      and page.locator("#home-new-input").get_attribute("href")=="#owner-inputs")
                check("WP8B_UI_02_home_owner_row_posted_and_updated_plus04",
                      lambda: (lambda text: "posted 19:03 +04" in text
                          and "updated 19:07 +04" in text)(
                          page.locator("#needs-you-list li.needs-input").first.inner_text())
                          if page.locator("#needs-you-list li.needs-input").count() else False)
                check("WP8B_UI_03_home_decision_clocks_and_asked_context",
                      lambda: page.locator("#needs-you-list").count()==1
                      and "posted 19:10 +04 · updated 19:10 +04" in
                      page.locator("#needs-you-list").inner_text()
                      and "Asked at" not in page.locator("#needs-you-list").inner_text()
                      and "Decision needed: Review freeze of current Team protocol v2.3" in
                      page.locator("#needs-you-list").inner_text())
                if page.locator("#home-new-input").count():
                    page.locator("#home-new-input").click()
                # Hash navigation schedules asynchronous rendering. Wait for
                # the actual form, without relaxing the original assertions;
                # a missing form still produces a behavioural FAIL, not ERROR.
                def json_form_rendered():
                    try:
                        page.locator("#oi-json-form").wait_for(state="attached", timeout=5000)
                        return True
                    except Exception:
                        return False
                check("WP8B_UI_04_home_shortcut_opens_json_form",
                      lambda: json_form_rendered()
                      and page.url.endswith("#owner-inputs")
                      and page.locator("#oi-json-form").count()==1
                      and page.locator("#oi-json-post").count()==1)
                check("WP8B_UI_05_owner_input_list_posted_updated_local",
                      lambda: page.locator(".oi-row[data-issue='31'] .oi-ts.owner-clock").count()==1
                      and "posted 19:03 +04 · updated 19:07 +04" in
                      page.locator(".oi-row[data-issue='31'] .oi-ts").inner_text())
                page.goto(base+"#trace/31",wait_until="networkidle")
                check("WP8B_UI_06_each_trace_step_has_time_or_missing_notice",
                      lambda: page.locator("#trace-steps .trace-step").count()==6
                      and page.locator("#trace-steps .trace-step-time").count()==6
                      and page.locator(".trace-step[data-step='ack'] .trace-step-time").inner_text().endswith("+04")
                      and "time not recorded" in page.locator(".trace-step[data-step='sent']").inner_text())
                page.goto(base+"#project/grade9-pilot",wait_until="networkidle")
                check("WP8B_UI_07_protocol_freeze_from_source_not_stale_registry",
                      lambda: "Review freeze of current Team protocol v2.3" in
                      page.locator("#open-decisions-list").inner_text()
                      and "freeze Team protocol v2.0" not in
                      page.locator("#open-decisions-list").inner_text())
                check("WP8B_UI_08_project_decision_cards_show_source_asked_at",
                      lambda: page.locator("#open-decisions-list .decision-asked").count()>=2
                      and "Asked at 19:10 +04" in
                      page.locator("#open-decisions-list").inner_text()
                      and "Asked at: not recorded in source" in
                      page.locator("#open-decisions-list").inner_text())
                page.goto(base+"#decision/grade9-pilot/G9-DIFF-13",wait_until="networkidle")
                check("WP8B_UI_09_decision_detail_shows_source_asked_at",
                      lambda: page.locator("#dc-ask .decision-asked").count()==1
                      and "Asked at 19:10 +04" in page.locator("#dc-ask").inner_text())
                browser.close()
        finally:
            server.shutdown()
    print(f"WP8B_BROWSER_COUNTS pass={len(ok)} fail={len(failed)} error={len(errors)}")
    print("WP8B_BROWSER_FAILED_NAMES "+",".join(failed))
    print("WP8B_BROWSER_ERROR_NAMES "+",".join(errors))
    if failed or errors:sys.exit(1)

if __name__=="__main__":main()
