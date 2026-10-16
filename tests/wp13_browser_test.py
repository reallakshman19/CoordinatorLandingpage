#!/usr/bin/env python3
"""WP13 Next Move publisher and page: exact own-repo projected fixtures.

Identical seven checks are required to fail behaviorally, not crash, on the
pinned pre-WP13 builder and app. Never tests a real create/approve/send action.
"""
import json
from pathlib import Path
import shutil
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import build_data
from browser_smoke_test import start_server,find_free_port

P="landing-live"
M1="NM-20261016-140000-abcd"
M2="NM-20261016-140100-abce"
BAD="NM-20261016-140200-abcf"
REPO="reallakshman19/CoordinatorLandingpage"
OWNER={"role":"TeamCoordinator","id8":"11111111"}
RECIP={"role":"implementer","id8":"6ad1a045"}
OTM={"role":"OwnerTeammember","id8":"11111111"}


def move(ident,kind="next_step"):
    return {"id":ident,"project":P,"class":"Dispatch","kind":kind,
            "from":OWNER,"to":RECIP,"text":"read-only validation <img onerror=alert(1)>",
            "basis":{"evidence":f"https://github.com/{REPO}/issues/22",
                     "head":"a"*40,"registry_sha":"b"*40},
            "trigger":"GO" if ident==M1 else "additional task",
            "supersedes":None,"evidence_format":"TASK EVIDENCE v2",
            "created_at":"2026-10-16T14:00:00Z"}


def main():
    if len(sys.argv)!=2:
        raise SystemExit("usage: python tests/wp13_browser_test.py <artifact>")
    from playwright.sync_api import sync_playwright
    passed,failed,errors=[],[],[]
    def check(name,fn):
        try:
            good=bool(fn())
        except Exception as exc:
            good=False
            errors.append(name+":"+type(exc).__name__)
        (passed if good else failed).append(name)
        print(("PASS " if good else "FAIL ")+name)
    with tempfile.TemporaryDirectory() as temp:
        root=Path(temp)
        site=root/"site"
        shutil.copytree(Path(sys.argv[1]).resolve(),site)
        for proj in (P,"cii-method-c"):
            p=root/"logs"/proj/"registry.json"
            p.parent.mkdir(parents=True,exist_ok=True)
            reg=json.loads((ROOT/"logs"/proj/"registry.json").read_text())
            p.write_text(json.dumps(reg))
        folder=root/"logs"/P/"moves"
        folder.mkdir()
        for ident in (M1,M2,BAD):
            entry=move(ident,kind="invalid" if ident==BAD else "next_step")
            (folder/(ident+".json")).write_text(json.dumps(entry))
        (folder/"claims").mkdir()
        (folder/"claims"/(M1+".json")).write_text(json.dumps({
            "by":RECIP,"claimed_at":"2026-10-16T14:02:00Z",
            "expires_at":"2026-10-16T14:17:00Z"
        }))
        transitions=[
            {"move":M1,"state":"APPROVED","by":OTM,"at":"2026-10-16T14:01:00Z"},
            {"move":M1,"state":"CLAIMED","by":RECIP,"at":"2026-10-16T14:02:00Z"},
            {"state":"EVALUATED","by":OTM,"at":"2026-10-16T09:00:00Z"},
        ]
        (root/"logs"/P/"moves.jsonl").write_text(
            "".join(json.dumps(t)+"\n" for t in transitions))
        thread=root/"cache"/"project-threads"/P/"issue-22.json"
        thread.parent.mkdir(parents=True)
        comments=[]
        for i in range(19):
            chat="6ad0adca" if i<8 else "6ad1a045"
            comments.append({"id":i+1,
                "created_at":f"2026-10-16T14:00:{i+1:02d}Z",
                "body":f"TASK EVIDENCE v2 · landing-live · implementer · chat {chat} · #{i+1} · 16 Oct 18:00 +04:00\nTask: work item"})
        thread.write_text(json.dumps({"number":22,"repository":REPO,
                                       "comments":comments}))
        build_data.build_all(root,site/"data",cache_dir=root/"cache")
        server=start_server(str(site),find_free_port())
        try:
            with sync_playwright() as pw:
                browser=pw.chromium.launch(headless=True)
                page=browser.new_page(viewport={"width":1180,"height":900})
                base=f"http://127.0.0.1:{server.server_address[1]}/index.html"
                def visit(route):
                    page.goto(base+route,wait_until="networkidle")

                visit("#next-moves")
                check("WP13_UI_01_board_readonly_navigation",
                      lambda: page.locator("#view-next-moves").count()==1
                        and page.locator("#wp13-board").count()==1
                        and page.locator("#view-next-moves button").count()==0)
                check("WP13_UI_02_board_states_and_criticality",
                      lambda: page.locator("#wp13-board").count()==1
                        and "Criticality: normal" in page.locator(
                          "#wp13-board").inner_text()
                          and "Criticality: critical" in page.locator(
                              "#wp13-board").inner_text()
                          and M1 in page.locator("#wp13-board").inner_text()
                          and M2 in page.locator("#wp13-board").inner_text())
                visit("#project/landing-live")
                print("WP13_DIAG_PROJECT", repr(page.locator("#wp13-project-moves").all_inner_texts()))
                check("WP13_UI_03_active_queue_and_approver",
                      lambda: page.locator("#wp13-project-moves").count()==1
                        and M1 in page.locator("#wp13-project-moves").inner_text()
                        and M2 in page.locator("#wp13-project-moves").inner_text()
                        and "Owner / OwnerTeammember" in page.locator(
                            "#wp13-project-moves").inner_text())
                check("WP13_UI_04_flags_and_rejected_reason",
                      lambda: page.locator("#wp13-project-moves").count()==1
                        and "evaluator stale" in page.locator(
                          "#wp13-project-moves").inner_text()
                          and "self-approved" in page.locator(
                              "#wp13-project-moves").inner_text()
                          and "kind_invalid" in page.locator(
                              "#wp13-project-moves").inner_text()
                          and BAD in page.locator("#wp13-project-moves").inner_text())
                check("WP13_UI_05_mod20_counter_from_go",
                      lambda: page.locator("#wp13-project-moves").count()==1
                        and "task 19 · next ground at 25" in page.locator(
                          "#wp13-project-moves").inner_text())
                visit("#agent/landing-live/6ad1a045")
                check("WP13_UI_06_agent_own_dispatch_queue",
                      lambda: page.locator("#wp13-agent-moves").count()==1
                        and M1 in page.locator("#wp13-agent-moves").inner_text()
                        and M2 in page.locator("#wp13-agent-moves").inner_text())
                check("WP13_UI_07_no_next_move_actions",
                      lambda: page.locator("#wp13-agent-moves").count()==1
                        and page.locator("#wp13-agent-moves button").count()==0
                        and page.locator("#wp13-agent-moves textarea").count()==0
                        and page.locator("#wp13-agent-moves form").count()==0
                        and "task 19" in page.locator(
                            "#wp13-agent-moves").inner_text())
                browser.close()
        finally:
            server.shutdown()
    print(f"WP13_BROWSER_COUNTS pass={len(passed)} fail={len(failed)} error={len(errors)}")
    if failed:print("WP13_BROWSER_FAILED_NAMES "+",".join(failed))
    if errors:print("WP13_BROWSER_ERROR_NAMES "+",".join(errors))
    if failed or errors:raise SystemExit(1)


if __name__=="__main__":
    main()
