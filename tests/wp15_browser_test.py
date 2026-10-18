#!/usr/bin/env python3
"""WP15 browser: committed evaluator comparison vs actual moves.jsonl heartbeat."""
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
import shutil
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import build_data
from synthetic_historical_roster import historical_active_roster
from browser_smoke_test import start_server,find_free_port

REPO="reallakshman19/CoordinatorLandingpage"
GO="NM-20261016-140000-abcd"


def main():
    if len(sys.argv)!=2:
        raise SystemExit("usage: python tests/wp15_browser_test.py <artifact>")
    from playwright.sync_api import sync_playwright
    passed,failed,errors=[],[],[]
    def check(name,fn):
        try:
            ok=bool(fn())
        except Exception as exc:
            ok=False;errors.append(name+":"+type(exc).__name__)
        (passed if ok else failed).append(name)
        print(("PASS " if ok else "FAIL ")+name)
    with tempfile.TemporaryDirectory() as temp:
        root=Path(temp)
        site=root/"site";shutil.copytree(Path(sys.argv[1]).resolve(),site)
        project=root/"logs"/"landing-live";project.mkdir(parents=True)
        other=root/"logs"/"cii-method-c";other.mkdir(parents=True)
        for name,folder in [("landing-live",project),("cii-method-c",other)]:
            (folder/"registry.json").write_text(
                (ROOT/"logs"/name/"registry.json").read_text())
        details=json.loads((project/"registry.json").read_text())
        agent=details["agents"][1]["chat_id8"]
        # The synthetic GO is dated 16 Oct, before this historical
        # participant's subsequent retirement; do not model a revived chat.
        details=historical_active_roster(details, agent)
        (project/"registry.json").write_text(json.dumps(details))
        (project/"moves").mkdir()
        candidate={
          "id":GO,"project":"landing-live","class":"Dispatch","kind":"next_step",
          "from":{"role":"TeamCoordinator","id8":"11111111"},
          "to":{"role":"implementer","id8":agent},
          "text":"Read-only proof","basis":{
            "evidence":"https://github.com/"+REPO+"/issues/22",
            "head":"a"*40,"registry_sha":build_data.git_blob_sha(project/"registry.json")},
          "trigger":"GO","supersedes":None,
          "evidence_format":"TASK EVIDENCE v2",
          "created_at":"2026-10-16T14:00:00Z"}
        (project/"moves"/(GO+".json")).write_text(json.dumps(candidate))
        hb=(datetime.now(timezone.utc)-timedelta(minutes=5)).isoformat()
        (project/"moves.jsonl").write_text(json.dumps(
            {"state":"EVALUATED","at":hb,
             "by":{"role":"TeamCoordinator","id8":"11111111"}})+"\n")
        cache=root/"cache"/"project-threads"/"landing-live"
        cache.mkdir(parents=True)
        comments=[{"id":i+1,"created_at":f"2026-10-16T14:00:{i+1:02d}Z",
                   "body":f"TASK EVIDENCE v2 · landing-live · implementer · chat {agent} · #{i+1} · 16 Oct 18:00 +04\nTask: work"}
                  for i in range(5)]
        (cache/"issue-22.json").write_text(json.dumps({
            "number":22,"repository":REPO,"comments":comments}))
        # Authored report is deliberately mismatched; no proposed heartbeat is
        # written to moves.jsonl or substituted for the recorded one.
        (project/"next-move-evaluation.json").write_text(json.dumps({
            "schema":"next_move_evaluator.v1","project":"landing-live",
            "registry_sha":build_data.git_blob_sha(project/"registry.json"),
            "at":datetime.now(timezone.utc).isoformat(),
            "snapshot":{"criticality":"critical"},
            "heartbeat_proposal":{"state":"EVALUATED",
                "at":datetime.now(timezone.utc).isoformat(),
                "by":{"role":"TeamCoordinator","id8":"11111111"}}}))
        build_data.build_all(root,site/"data",cache_dir=root/"cache")
        server=start_server(str(site),find_free_port())
        try:
            with sync_playwright() as pw:
                browser=pw.chromium.launch(headless=True)
                page=browser.new_page(viewport={"width":1180,"height":850})
                base=f"http://127.0.0.1:{server.server_address[1]}/index.html"
                def visit(route):
                    page.goto(base+route,wait_until="networkidle")
                    if route == "#next-moves":
                        page.locator("#wp13-board .wp13-board-project").first.wait_for(
                            state="attached", timeout=8000)
                    if route.startswith("#project/") or route.startswith("#agent/"):
                        element="#wp13-project-moves" if route.startswith("#project/") else "#wp13-agent-moves"
                        page.locator(element).wait_for(state="attached",timeout=8000)
                        page.wait_for_function("""selector=>{
                            let e=document.querySelector(selector);
                            return !e || e.querySelector('.wp13-criticality');
                        }""",arg=element,timeout=8000)
                visit("#next-moves")
                check("WP15_UI_01_board_evaluator_panel",
                    lambda: page.locator("#wp13-board .wp15-evaluator-panel").count()==1)
                check("WP15_UI_02_last_committed_evaluated_time",
                    lambda: page.locator("#wp13-board .wp15-last-evaluated").count()==1
                    and hb in page.locator("#wp13-board .wp15-last-evaluated").inner_text())
                check("WP15_UI_03_recent_evaluated_not_stale",
                    lambda: page.locator("#wp13-board .wp15-evaluator-stale").count()==1
                    and "Evaluator stale: no" in page.locator(
                        "#wp13-board .wp15-evaluator-stale").inner_text())
                check("WP15_UI_04_overdue_task_not_acted_on",
                    lambda: page.locator("#wp13-board .wp15-not-acted").count()==1
                    and "Detected, not acted on: yes" in page.locator(
                        "#wp13-board .wp15-not-acted").inner_text())
                check("WP15_UI_05_mismatched_report_is_explicit",
                    lambda: page.locator("#wp13-board .wp15-cross-check").count()==1
                    and "Evaluator output: mismatch" in page.locator(
                        "#wp13-board .wp15-cross-check").inner_text()
                    and "criticality" in page.locator(
                        "#wp13-board .wp15-cross-check").inner_text())
                visit("#agent/landing-live/"+agent)
                check("WP15_UI_06_agent_evaluator_cross_check",
                    lambda: page.locator("#wp13-agent-moves .wp15-cross-check").count()==1
                    and "mismatch" in page.locator(
                        "#wp13-agent-moves .wp15-cross-check").inner_text())
                check("WP15_UI_07_proposal_not_heartbeat_or_sender",
                    lambda: page.locator("#wp13-agent-moves .wp15-evaluator-panel").count()==1
                    and "only a committed moves.jsonl row counts" in page.locator(
                        "#wp13-agent-moves .wp15-evaluator-panel").inner_text()
                    and page.locator("#wp15-evaluator-send").count()==0
                    and page.locator("#wp15-evaluator-schedule").count()==0)
                browser.close()
        finally:
            server.shutdown()
    print(f"WP15_BROWSER_COUNTS pass={len(passed)} fail={len(failed)} error={len(errors)}")
    if failed: print("WP15_BROWSER_FAILED_NAMES "+",".join(failed))
    if errors: print("WP15_BROWSER_ERROR_NAMES "+",".join(errors))
    if failed or errors: raise SystemExit(1)


if __name__=="__main__":
    main()
