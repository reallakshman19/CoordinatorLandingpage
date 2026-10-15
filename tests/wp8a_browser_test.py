#!/usr/bin/env python3
"""WP8a: real Chromium sees newer site, offers a deliberate cache-busted reload.

Run the SAME four behavioural checks against old app/index on red control;
absence of a banner is a FAIL, never a timeout or API error.
"""
import json
from pathlib import Path
import shutil
import sys
import tempfile

from browser_smoke_test import find_free_port, start_server

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import publish_site

def main():
    if len(sys.argv)!=2:
        raise SystemExit("usage: python tests/wp8a_browser_test.py <artifact>")
    from playwright.sync_api import sync_playwright
    ok,failed,errors=[],[],[]
    def check(name,fn):
        try:
            outcome=bool(fn())
        except Exception as ex:
            outcome=False
            errors.append(name+"="+type(ex).__name__)
        (ok if outcome else failed).append(name)
        print(("PASS " if outcome else "FAIL ")+name)

    with tempfile.TemporaryDirectory() as td:
        root=Path(td)/"artifact"
        shutil.copytree(Path(sys.argv[1]).resolve(),root)
        version="a"*8
        publish_site.stamp_asset_urls(root,"a"*40)
        build=root/"build-info.json"
        old={"source_commit":"a"*40,"site_version":version,
             "source_capture_at":"2026-10-15T10:00:00+00:00",
             "built_at":"2026-10-15T10:00:00+00:00","run_id":"101",
             "live_file_sha256":{"projects.json":"a"*64}}
        build.write_text(json.dumps(old))
        server=start_server(str(root),find_free_port())
        try:
            with sync_playwright() as pw:
                browser=pw.chromium.launch(headless=True)
                page=browser.new_page(viewport={"width":1000,"height":800})
                address="http://127.0.0.1:"+str(server.server_address[1])+"/index.html#owner-inputs"
                page.goto(address,wait_until="networkidle",timeout=20000)
                check("WP8A_UI_01_initial_loaded_version_and_hidden_banner",
                      lambda: page.locator('meta[name="site-version"][content="'+version+'"]').count()==1
                      and page.locator("#site-update-banner").count()==1
                      and page.locator("#site-update-banner").is_hidden())
                textfield=page.locator("#oi-json-text")
                if textfield.count():
                    textfield.fill("This draft must survive until I click reload.")
                original=page.url
                new=dict(old,site_version="b"*8,
                         source_commit="b"*40,run_id="102",
                         built_at="2026-10-15T10:01:00+00:00")
                build.write_text(json.dumps(new))
                if page.evaluate("typeof pollBuildInfo === 'function'"):
                    page.evaluate("pollBuildInfo()")
                check("WP8A_UI_02_changed_version_shows_reloader",
                      lambda: page.locator("#site-update-banner").count()==1
                      and page.locator("#site-update-banner").is_visible()
                      and "New version available" in page.locator("#site-update-banner").inner_text())
                def target():
                    if page.locator("#site-update-reload").count()==0:
                        return None
                    from urllib.parse import urlparse,parse_qs
                    url=page.locator("#site-update-reload").get_attribute("href")
                    parsed=urlparse(url)
                    return parsed,parse_qs(parsed.query)
                check("WP8A_UI_03_reloader_fresh_index_url_preserves_route",
                      lambda: (lambda x:
                              x is not None and
                              x[0].path.endswith("/index.html") and
                              x[0].fragment=="owner-inputs" and
                              x[1].get("v")==["b"*8] and
                              "Reload now" in page.locator("#site-update-reload").inner_text())(target()))
                check("WP8A_UI_04_no_surprise_navigation_or_draft_loss",
                      lambda: page.url==original and textfield.count()==1
                      and textfield.input_value()=="This draft must survive until I click reload.")
                browser.close()
        finally:
            server.shutdown()
    print(f"WP8A_BROWSER_COUNTS pass={len(ok)} fail={len(failed)} error={len(errors)}")
    print("WP8A_BROWSER_FAILED_NAMES "+",".join(failed))
    print("WP8A_BROWSER_ERROR_NAMES "+",".join(errors))
    if failed or errors:sys.exit(1)

if __name__=="__main__":
    main()
