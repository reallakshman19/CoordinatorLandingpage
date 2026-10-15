#!/usr/bin/env python3
"""WP5b: actual browser isolates OUTSIDER from Owner Needs-you and inputs."""
import json
from pathlib import Path
import shutil
import sys
import tempfile

from browser_smoke_test import find_free_port,start_server


def main():
    if len(sys.argv)!=2:
        raise SystemExit("usage: python tests/wp5b_browser_test.py <artifact>")
    from playwright.sync_api import sync_playwright
    checks,failed,errors=[],[],[]
    def check(name,fn):
        try:
            result=bool(fn())
        except Exception as exc:
            errors.append(name+":"+type(exc).__name__)
            result=False
        if result:
            checks.append(name)
            print("PASS "+name)
        else:
            failed.append(name)
            print("FAIL "+name)

    with tempfile.TemporaryDirectory() as temp:
        root=Path(temp)/"artifact"
        shutil.copytree(Path(sys.argv[1]).resolve(),root)
        data=root/"data"
        data.mkdir(exist_ok=True)
        inputs=[
            {"number":801,"status":"OPEN","state":"open","needs_you":True,
             "type":"INFO","text":"Member-associated test message",
             "author_association":"MEMBER","is_outsider":False,
             "authority":"UNVERIFIED","effective":False},
            {"number":802,"status":"OPEN","state":"open","needs_you":False,
             "type":"INFO","text":"Untrusted outsider test message",
             "author_association":"CONTRIBUTOR","is_outsider":True,
             "authority":"UNVERIFIED","effective":False}
        ]
        (data/"owner-inputs.json").write_text(json.dumps(inputs))
        port=find_free_port()
        server=start_server(str(root),port)
        try:
            with sync_playwright() as playwright:
                browser=playwright.chromium.launch(headless=True)
                page=browser.new_page(viewport={"width":1100,"height":900})
                page.goto(f"http://127.0.0.1:{port}/index.html#home",
                          wait_until="networkidle",timeout=20000)
                check("WP5B_UI_01_owner_needs_you_excludes_outsider",
                      lambda: "Owner input #801" in
                          page.locator("#needs-you-list").inner_text() and
                          "Owner input #802" not in
                          page.locator("#needs-you-list").inner_text())
                page.goto(f"http://127.0.0.1:{port}/index.html#owner-inputs",
                          wait_until="networkidle",timeout=20000)
                check("WP5B_UI_02_outsider_badge_and_separate_list",
                      lambda: page.locator("#oi-count").inner_text()=="1" and
                          page.locator("#oi-outsider-count").inner_text()=="1" and
                          page.locator("#oi-list .oi-row[data-issue='801']").count()==1 and
                          page.locator("#oi-list .oi-row[data-issue='802']").count()==0 and
                          page.locator("#oi-outsider-list .oi-row[data-issue='802']").count()==1 and
                          page.locator("#oi-outsider-list .badge").filter(
                             has_text="OUTSIDER").count()==1)
                check("WP5B_UI_03_unverified_outsider_context",
                      lambda: "GitHub author_association: CONTRIBUTOR" in
                          page.locator("#oi-outsider-list").inner_text() and
                          "not an Owner instruction" in
                          page.locator("#oi-outsider-list").inner_text() and
                          page.locator("#oi-outsider-list .oi-receipt").count()==0)
                browser.close()
        finally:
            server.shutdown()
    print(f"WP5B_BROWSER_COUNTS pass={len(checks)} fail={len(failed)} error={len(errors)}")
    print("WP5B_BROWSER_FAILED_NAMES "+",".join(failed))
    print("WP5B_BROWSER_ERROR_NAMES "+",".join(errors))
    if failed or errors:
        sys.exit(1)


if __name__=="__main__":
    main()
