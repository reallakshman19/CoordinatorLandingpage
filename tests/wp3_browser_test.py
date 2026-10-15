#!/usr/bin/env python3
"""WP3: browser readback polling; no external API or real 60-second wait."""
import json
from pathlib import Path
import shutil
import sys
import tempfile

from browser_smoke_test import find_free_port, start_server

def main():
    if len(sys.argv)!=2:
        raise SystemExit("usage: python tests/wp3_browser_test.py <browser-artifact>")
    original=Path(sys.argv[1]).resolve()
    from playwright.sync_api import sync_playwright
    passes,failures,errors=[],[],[]
    def check(name,what):
        try:
            ok=bool(what())
        except Exception as exc:
            ok=False
            errors.append(name+"="+type(exc).__name__)
        if ok:
            passes.append(name)
            print("PASS "+name)
        else:
            failures.append(name)
            print("FAIL "+name)

    with tempfile.TemporaryDirectory() as td:
        root=Path(td)/"artifact"
        shutil.copytree(original,root)
        projects_path=root/"data"/"projects.json"
        projects=json.loads(projects_path.read_text())
        assert isinstance(projects,list) and len(projects)>=2
        for p in projects:
            p["freshness_status"]="STALE"
            p["control"]=dict(p.get("control") or {},hold=None)
        projects_path.write_text(json.dumps(projects))
        stamp=root/"build-info.json"
        base={"schema_version":"wp4.1","source_commit":"a"*40,
              "source_capture_at":"2026-10-15T10:00:00+00:00",
              "built_at":"2026-10-15T10:00:00+00:00",
              "run_id":"1001","live_file_sha256":{"projects.json":"a"*64}}
        stamp.write_text(json.dumps(base))
        port=find_free_port()
        server=start_server(str(root),port)
        try:
            with sync_playwright() as playwright:
                browser=playwright.chromium.launch(headless=True)
                page=browser.new_page(viewport={"width":1100,"height":900})
                # Record real application scheduler calls without waiting 60s.
                page.add_init_script("""
                    window.__pollIntervals=[];
                    const original=window.setInterval;
                    window.setInterval=function(f,delay,...args){
                      window.__pollIntervals.push(delay);
                      return original.call(window,f,delay,...args);
                    };
                """)
                project_requests=[]
                page.on("request",lambda r: project_requests.append(r.url)
                        if "projects.json" in r.url and "benchmarks" not in r.url else None)
                url=f"http://127.0.0.1:{port}/index.html#home"
                page.goto(url,wait_until="networkidle",timeout=15000)
                page.wait_for_timeout(250)
                check("WP3_UI_01_60s_interval",
                      lambda: page.evaluate("window.__pollIntervals.includes(60000)"))
                check("WP3_UI_02_initial_buildinfo_time",
                      lambda: "data built 14:00" in page.locator("#data-built-at").inner_text())
                before=len(project_requests)
                # The optional function check avoids a ReferenceError on the
                # baseline page. It must still FAIL behaviourally on BASE.
                has_poll=page.evaluate("typeof pollBuildInfo === 'function'")
                if has_poll:
                    page.evaluate("pollBuildInfo()")
                page.wait_for_timeout(150)
                check("WP3_UI_03_unchanged_build_no_refetch",
                      lambda: has_poll and len(project_requests)==before)

                updated=dict(base,built_at="2026-10-15T10:01:00+00:00",
                             run_id="1002",
                             live_file_sha256={"projects.json":"b"*64})
                stamp.write_text(json.dumps(updated))
                for p in projects:
                    p["freshness_status"]="HOLD"
                    p["control"]=dict(p["control"],hold={"reason":"synthetic"})
                projects_path.write_text(json.dumps(projects))
                if has_poll:
                    page.evaluate("pollBuildInfo()")
                page.wait_for_timeout(200)
                check("WP3_UI_04_changed_build_triggers_refresh",
                      lambda: has_poll and
                      len(project_requests)>before and
                      "data built 14:01" in page.locator("#data-built-at").inner_text() and
                      "HOLD" in page.locator("#projects-tbody").inner_text())
                browser.close()
        finally:
            server.shutdown()
    print(f"WP3_BROWSER_COUNTS pass={len(passes)} fail={len(failures)} error={len(errors)}")
    print("WP3_BROWSER_FAILED_NAMES "+",".join(failures))
    print("WP3_BROWSER_ERROR_NAMES "+",".join(errors))
    if failures or errors:
        sys.exit(1)


if __name__=="__main__":
    main()
