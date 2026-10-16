#!/usr/bin/env python3
"""WP14 Next Move UI: draft Owner-input GitHub URLs, no live writes.

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
        raise SystemExit("usage: python tests/wp14_browser_test.py <artifact>")
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
                # Stub popup only; no GitHub writes or external network.
                page.add_init_script("""window.__wp14URLs=[];
                   window.open=(url)=>{window.__wp14URLs.push(url);return null;};""")
                base=f"http://127.0.0.1:{server.server_address[1]}/index.html"
                def visit(route):
                    page.goto(base+route,wait_until="networkidle")
                    # Routes fetch data asynchronously. Wait for the view before
                    # asserting either feature presence or pinned-base absence.
                    if route.startswith("#project/"):
                        page.locator("#view-project").wait_for(
                            state="attached", timeout=9000)
                        page.wait_for_function("""() => {
                          const box=document.querySelector('#wp13-project-moves');
                          return !box || !!box.querySelector('.wp13-criticality');
                        }""", timeout=9000)
                    elif route.startswith("#agent/"):
                        page.locator("#view-agent").wait_for(
                            state="attached", timeout=9000)
                        page.wait_for_function("""() => {
                          const box=document.querySelector('#wp13-agent-moves');
                          return !box || !!box.querySelector('.wp13-criticality');
                        }""", timeout=9000)

                visit("#next-moves")
                check("WP14_UI_01_pilot_compose_controls_on_board",
                      lambda: page.locator(".wp14-board-controls .wp14-compose-submit").count()==1)
                visit("#project/landing-live")
                check("WP14_UI_02_project_compose_and_published_approval",
                      lambda: page.locator("#wp14-project-controls .wp14-compose-submit").count()==1
                      and page.locator("#wp14-project-controls .wp14-approval-submit").count()==1)
                form=page.locator("#wp14-project-controls .wp14-compose-form")
                if form.count():
                    form.locator(".wp14-from").fill("11111111")
                    form.locator(".wp14-to").fill("6ad1a045")
                    form.locator(".wp14-head").fill("a"*40)
                    form.locator(".wp14-trigger").fill("GO")
                    form.locator(".wp14-text").fill("Draft a bounded next-step; no send")
                    form.locator(".wp14-compose-submit").click()
                def request_payload():
                    urls=page.evaluate("window.__wp14URLs")
                    if not urls:return None
                    from urllib.parse import urlparse,parse_qs
                    params=parse_qs(urlparse(urls[-1]).query)
                    return (urls[-1],params,
                            json.loads(params["value"][0]),
                            json.loads(json.loads(params["value"][0])["text"]))
                check("WP14_UI_03_compose_prefills_one_exact_owner_input_json",
                      lambda: bool((data:=request_payload())
                                   and data[0].startswith("https://github.com/"+REPO+"/new/main?")
                                   and data[2]["type"]=="NEXT_MOVE_COMPOSE"
                                   and data[1]["filename"][0].startswith("logs/landing-live/inputs/OI-")
                                   and data[3]["move"]["class"]=="Dispatch"
                                   and data[3]["move"]["basis"]["head"]=="a"*40
                                   and data[3]["move"]["basis"]["registry_sha"]
                                       == next(p["registry_blob_sha"] for p in
                                         json.loads((site/"data"/"projects.json").read_text())
                                         if p["project"]=="landing-live")))
                n_before=page.evaluate("window.__wp14URLs.length")
                if form.count():
                    form.locator(".wp14-head").fill("invalid")
                    form.locator(".wp14-compose-submit").click()
                check("WP14_UI_04_invalid_draft_does_not_open_github",
                      lambda: form.count()==1
                      and page.evaluate("window.__wp14URLs.length")==n_before
                      and "Supply valid id8s" in page.locator(".wp14-compose-result").inner_text())
                approve=page.locator("#wp14-project-controls .wp14-approval-row").first
                if approve.count():
                    approve.locator(".wp14-approver-role").select_option("OwnerTeammember")
                    approve.locator(".wp14-approver-id8").fill("11111111")
                    approve.locator(".wp14-approval-submit").click()
                check("WP14_UI_05_approval_is_request_not_approved",
                      lambda: bool((data:=request_payload())
                                  and data[2]["type"]=="NEXT_MOVE_APPROVAL"
                                  and data[3]["move"]==M2
                                  and data[3]["request_only"] is True
                                  and data[3]["by"]=={"role":"OwnerTeammember","id8":"11111111"}
                                  and approve.count()==1
                                  and "not approved" in approve.locator(
                                     ".wp14-approval-result").inner_text().lower()))
                recorded_requests=page.evaluate("window.__wp14URLs.slice()")
                visit("#project/cii-method-c")
                check("WP14_UI_06_external_critical_nonpilot_no_controls",
                      lambda: len(recorded_requests)>=2
                      and page.locator("#wp14-project-controls .wp14-compose-submit").count()==0
                      and page.locator("#wp14-project-controls .wp14-approval-submit").count()==0)
                visit("#agent/landing-live/6ad1a045")
                check("WP14_UI_07_no_agent_auto_claim_or_send",
                      lambda: page.locator("#wp14-agent-request-note").count()==1
                      and page.locator("#wp13-agent-moves button").count()==0
                      and page.locator("#wp13-agent-moves form").count()==0
                      and page.locator("#wp13-agent-moves textarea").count()==0)
                browser.close()
        finally:
            server.shutdown()
    print(f"WP14_BROWSER_COUNTS pass={len(passed)} fail={len(failed)} error={len(errors)}")
    if failed:print("WP14_BROWSER_FAILED_NAMES "+",".join(failed))
    if errors:print("WP14_BROWSER_ERROR_NAMES "+",".join(errors))
    if failed or errors:raise SystemExit(1)


if __name__=="__main__":
    main()
