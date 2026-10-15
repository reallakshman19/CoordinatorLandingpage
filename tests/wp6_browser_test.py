#!/usr/bin/env python3
"""WP6: browser proof of trace permalink, real records and plain language."""
import json
from pathlib import Path
import shutil
import sys
import tempfile

from browser_smoke_test import find_free_port,start_server

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import build_data


def main():
    if len(sys.argv)!=2:
        raise SystemExit("Usage: python tests/wp6_browser_test.py <artifact>")
    from playwright.sync_api import sync_playwright
    passes,failures,errors=[],[],[]

    def check(name,fn):
        try:
            good=bool(fn())
        except Exception as exc:
            good=False
            errors.append(name+":"+type(exc).__name__)
        if good:
            passes.append(name)
            print("PASS "+name)
        else:
            failures.append(name)
            print("FAIL "+name)

    with tempfile.TemporaryDirectory() as tmp:
        root=Path(tmp)/"site"
        shutil.copytree(Path(sys.argv[1]).resolve(),root)
        fixture=json.loads((ROOT/"tests/fixtures/f7_owner_issue31_replay.json").read_text())
        rows=build_data.build_owner_inputs(fixture["issues"],fixture["capture"])
        path=root/"data"/"owner-inputs.json"
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(json.dumps(rows))
        port=find_free_port()
        server=start_server(str(root),port)
        try:
            with sync_playwright() as playwright:
                browser=playwright.chromium.launch(headless=True)
                page=browser.new_page(viewport={"width":1100,"height":860})
                base=f"http://127.0.0.1:{port}/index.html"
                page.goto(base+"#home",wait_until="networkidle",timeout=20000)
                check("WP6_UI_01_needs_you_plain_request_and_trace",
                    lambda: "#31" in page.locator("#needs-you-list").inner_text()
                       and "What: F7 test: please acknowledge." in page.locator("#needs-you-list").inner_text()
                       and page.locator("#needs-you-list a[href='#trace/31']").count()==1)
                check("WP6_UI_02_decision_rows_say_owner_must_answer",
                    lambda: "Waiting for: Owner to answer" in
                       page.locator("#needs-you-list").inner_text())
                check("WP6_UI_03_per_project_coordinator_not_global",
                    lambda: page.locator("#live-coordinators .coordinator-by-project").count()>=2
                       and page.locator("#live-tc-time").count()==0
                       and "grade9-pilot" in page.locator("#live-coordinators").inner_text()
                       and "imo-ab-test" in page.locator("#live-coordinators").inner_text())
                page.goto(base+"#trace/31",wait_until="networkidle",timeout=20000)
                page.wait_for_timeout(120)
                def steps():
                    return page.locator("#trace-steps .trace-step")
                check("WP6_UI_04_six_named_trace_steps",
                    lambda: steps().count()==6 and
                       [s.inner_text().split("\n")[0] for s in steps().all()]==
                       ["Posted","ACK","Sent to agent","Agent evidence","Check","Result"])
                check("WP6_UI_05_posted_and_ack_are_real_links_with_times",
                    lambda: page.locator(".trace-step[data-step='posted'] a[href='https://github.com/reallakshman19/CoordinatorLandingpage/issues/31']").count()==1
                       and page.locator(".trace-step[data-step='ack'] a[href$='#issuecomment-31001']").count()==1
                       and page.locator(".trace-step[data-step='ack'] .trace-step-time").count()==1)
                check("WP6_UI_06_missing_three_steps_wait_for_responsible_person",
                    lambda: page.locator("#trace-steps .trace-step").count()==6 and
                           "waiting for TeamCoordinator" in
                           page.locator(".trace-step[data-step='sent']").inner_text()
                       and "waiting for agent" in
                           page.locator(".trace-step[data-step='evidence']").inner_text()
                       and "waiting for checker" in
                           page.locator(".trace-step[data-step='check']").inner_text())
                check("WP6_UI_07_why_mismatch_both_claims_visible",
                    lambda: page.locator("#trace-explanation").count()==1 and
                           "Why this status: Form says grade9-pilot, title says landing-live" in
                           page.locator("#trace-explanation").inner_text())
                check("WP6_UI_08_result_recorded_but_not_accepted",
                    lambda: page.locator("#trace-steps .trace-step").count()==6 and
                           "Recorded note (not accepted)" in
                           page.locator(".trace-step[data-step='result']").inner_text()
                       and page.locator(".trace-step[data-step='result'] a[href$='#issuecomment-31002']").count()==1
                       and "NEEDS_CLARIFICATION" in page.locator("#trace-status").inner_text())
                browser.close()
        finally:
            server.shutdown()
    print(f"WP6_BROWSER_COUNTS pass={len(passes)} fail={len(failures)} error={len(errors)}")
    print("WP6_BROWSER_FAILED_NAMES "+",".join(failures))
    print("WP6_BROWSER_ERROR_NAMES "+",".join(errors))
    if failures or errors:
        sys.exit(1)


if __name__=="__main__":
    main()
