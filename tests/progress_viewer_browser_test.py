#!/usr/bin/env python3
"""Stage 2 T2: frozen baseline/main render parity and isolated standalone browser."""
from __future__ import annotations
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from urllib.parse import urlsplit
from playwright.sync_api import sync_playwright
from browser_smoke_test import find_free_port, start_server

ROOT = Path(__file__).resolve().parents[1]
BASE = sys.argv[1] if len(sys.argv)>1 else "fc1acdb1bd861fabdf046ce6dce03eac74586c28"
CLOCK = 1790000000000

def base_file(path):
    return subprocess.check_output(["git", "show", BASE+":"+path], cwd=ROOT).decode()

def snap(page, address, failures):
    page.goto(address,wait_until="domcontentloaded",timeout=30000)
    page.wait_for_function("""() => {
      let root=document.querySelector('#view-progress-page');
      return root && root.querySelector('.pp-panel') && !root.querySelector('.loading');
    }""",timeout=30000)
    if page.locator("#view-progress-page .pp-banner.pp-bad").count():
        failures.append("data load error: "+address)
    root=page.locator("#view-progress-page")
    return (root.inner_text(), root.locator("a").evaluate_all(
        "(els) => els.map(a=>[a.innerText,a.getAttribute('href')])"))

def main():
    failures=[]
    with tempfile.TemporaryDirectory() as tmp:
        folder=Path(tmp)
        before=folder/"base"
        after=folder/"head"
        solo=folder/"solo"
        shutil.copytree(ROOT/"site",before)
        shutil.copytree(ROOT/"site",after)
        (before/"js/progress_page.js").write_text(
            base_file("site/js/progress_page.js"), encoding="utf-8",newline="\n")
        (before/"style.css").write_text(
            base_file("site/style.css"),encoding="utf-8",newline="\n")
        (solo/"progress").mkdir(parents=True)
        shutil.copytree(ROOT/"site/progress",solo/"progress",dirs_exist_ok=True)
        shutil.copytree(ROOT/"site/progress-data",solo/"progress-data")
        port=find_free_port()
        server=start_server(str(folder),port)
        try:
            with sync_playwright() as pw:
                browser=pw.chromium.launch(headless=True)
                snapshots={}
                pages=[(x["key"],x) for x in json.loads(
                    (after/"progress-data/projects.json").read_text())["projects"]]
                for key,project in pages:
                    idx=json.loads((after/"progress-data"/key/"index.json").read_text())
                    routes=[key+"/overview"]
                    for item in idx.get("topics",[]):
                        if not item.get("planned"):
                            routes.extend(key+"/"+item["key"]+"/"+view
                                for view in ["actions","progress","fixtures"])
                    for route in routes:
                        results=[]
                        for prefix in ("base","head"):
                            page=browser.new_page()
                            page.add_init_script("Date.now = () => "+str(CLOCK))
                            errs=[]
                            page.on("pageerror",lambda e:errs.append(str(e)))
                            try:
                                results.append(snap(page,
                                    "http://127.0.0.1:"+str(port)+"/"+prefix+
                                    "/index.html#progress-page/"+route, failures))
                            except Exception as e:
                                failures.append(prefix+" "+route+" "+type(e).__name__+": "+str(e)[:140])
                            if errs: failures.append(prefix+" "+route+" errors "+repr(errs))
                            page.close()
                        if len(results)!=2 or results[0]!=results[1]:
                            failures.append("parity mismatch: "+route)
                        else:
                            snapshots[route]=results[1]
                            print("PASS frozen text/links "+route,flush=True)
                solo_page=browser.new_page()
                solo_page.add_init_script("Date.now = () => "+str(CLOCK))
                outgoing=[]
                errors=[]
                prefix="/solo/"
                def check_req(request):
                    path=urlsplit(request.url).path
                    if not (path.startswith(prefix+"progress/") or
                            path.startswith(prefix+"progress-data/")):
                        outgoing.append(request.url)
                solo_page.on("request",check_req)
                solo_page.on("pageerror", lambda error: errors.append(str(error)))
                solo_page.on("console", lambda msg: errors.append(msg.text) if msg.type=="error" else None)
                for route,expected in snapshots.items():
                    try:
                        actual=snap(solo_page, "http://127.0.0.1:"+str(port)+
                          "/solo/progress/index.html?data=../progress-data#progress-page/"+route, failures)
                        if actual!=expected: failures.append("standalone route parity "+route)
                        else: print("PASS standalone route "+route,flush=True)
                    except Exception as e:
                        failures.append("standalone "+route+" "+type(e).__name__+": "+str(e)[:140])
                # Now explicitly switch to Copy-only on a fresh isolated page.
                solo_page.close()
                solo_page=browser.new_page()
                solo_page.add_init_script("Date.now = () => "+str(CLOCK))
                solo_page.on("request",check_req)
                solo_page.on("pageerror", lambda error: errors.append(str(error)))
                solo_page.on("console", lambda msg: errors.append(msg.text) if msg.type=="error" else None)
                source=json.loads((solo/"progress-data/projects.json").read_text())
                for p in source["projects"]: p["replyTo"]={"kind":"none"}
                (solo/"progress-data/projects.json").write_text(json.dumps(source))
                snap(solo_page,"http://127.0.0.1:"+str(port)+
                    "/solo/progress/index.html?data=../progress-data#progress-page/g9v35/nlm/actions",
                    failures)
                if solo_page.locator(".pp-replybox button").count()<1:
                    failures.append("no copy control; route="+solo_page.url+" snapshot="+solo_page.locator("#view-progress-page").inner_text()[:160])
                if solo_page.locator(".pp-sendrow a, .pp-pm").count():
                    failures.append("Send control exists with replyTo none")
                if outgoing: failures.append("standalone requested outside two folders: "+repr(outgoing))
                if errors: failures.append("standalone console/page errors: "+repr(errors))
                solo_page.close()
                browser.close()
        finally:
            server.shutdown()
    if failures:
        for f in failures: print("FAIL",f,flush=True)
        raise SystemExit(1)
    print("PASS Stage 2 frozen parity and isolated copy-only standalone",flush=True)

if __name__=="__main__":
    main()
