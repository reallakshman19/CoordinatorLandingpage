#!/usr/bin/env python3
"""WP7 visible form and JSON roundtrip (no issue or token)."""
import json
from pathlib import Path
import shutil
import sys
import tempfile
from browser_smoke_test import find_free_port,start_server

REPO="reallakshman19/CoordinatorLandingpage"
OI="OI-20261015-163000-abcd"

def main():
    if len(sys.argv)!=2:
        raise SystemExit("usage: python tests/wp7_browser_test.py <artifact>")
    from playwright.sync_api import sync_playwright
    passed,failed,errors=[],[],[]
    def check(label,fn):
        try:
            good=bool(fn())
        except Exception as error:
            good=False
            errors.append(label+":"+type(error).__name__)
        (passed if good else failed).append(label)
        print(("PASS " if good else "FAIL ")+label)
    with tempfile.TemporaryDirectory() as td:
        folder=Path(td)/"site"
        shutil.copytree(Path(sys.argv[1]).resolve(),folder)
        file_url=f"https://github.com/{REPO}/blob/"+("a"*40)+f"/logs/grade9-pilot/inputs/{OI}.json"
        receipt=f"https://github.com/{REPO}/blob/"+("b"*40)+"/logs/grade9-pilot/receipts.jsonl#L1"
        row={
           "id":OI,"number":None,"source_kind":"json_file","project":"grade9-pilot",
           "text":"Please review the next session.","target":"TeamCoordinator","type":"QUESTION",
           "status":"ACKNOWLEDGED","state":"acknowledged","ts":"2026-10-15T16:30:00Z",
           "author_association":"MEMBER","is_outsider":False,"needs_you":True,
           "authority":"UNVERIFIED","effective":False,"issue_url":file_url,
           "receipt":None,"trace":{"why":"The team acknowledged the request.",
             "waiting_for":"TeamCoordinator","steps":{
               "posted":{"url":file_url,"at":"2026-10-15T16:30:00Z"},
               "ack":{"url":receipt,"at":"2026-10-15T16:31:00Z"},
               "sent":None,"evidence":None,"check":None,"result":None}}
        }
        (folder/"data"/"owner-inputs.json").write_text(json.dumps([row]))
        port=find_free_port()
        server=start_server(str(folder),port)
        try:
            with sync_playwright() as pw:
                browser=pw.chromium.launch(headless=True)
                page=browser.new_page(viewport={"width":1100,"height":900})
                base=f"http://127.0.0.1:{port}/index.html"
                page.goto(base+"#owner-inputs",wait_until="networkidle")
                check("WP7_UI_01_form_has_registry_project_and_no_issue_post",
                    lambda: page.locator("#oi-json-form").count()==1
                       and page.locator("#oi-json-project option").count()==2
                       and "Commit changes" in page.locator(".owner-json-card").inner_text())
                page.evaluate("window.open = url => { window.__lastPost = url; };")
                page.locator("#oi-json-project").select_option("grade9-pilot")
                page.locator("#oi-json-target").fill("TeamCoordinator")
                page.locator("#oi-json-text").fill("Please review the next session.")
                page.locator("#oi-json-post").click()
                def record():
                    url=page.evaluate("window.__lastPost || ''")
                    from urllib.parse import urlparse,parse_qs
                    qs=parse_qs(urlparse(url).query)
                    return url,qs,json.loads(qs["value"][0]) if "value" in qs else {}
                check("WP7_UI_02_new_file_url_contains_confined_valid_json_and_no_token",
                    lambda: (lambda u,q,r:
                        u.startswith(f"https://github.com/{REPO}/new/main?") and
                        len(u)<7000 and
                        q["filename"][0]==f"logs/grade9-pilot/inputs/{r['id']}.json" and
                        r["id"].startswith("OI-") and r["project"]=="grade9-pilot" and
                        r["target"]=="TeamCoordinator" and r["replaces"] is None and
                        set(r)=={"id","project","target","type","text","replaces","created_at"} and
                        all(s not in u for s in ("token=","issues/new","access_token"))
                    )(*record()))
                check("WP7_UI_03_page_requires_actual_github_commit",
                    lambda: "Nothing is posted until then" in page.locator("#oi-json-result").inner_text())
                check("WP7_UI_04_invalid_replacement_is_blocked",
                    lambda: page.evaluate("""() => {
                      try { ownerJSONCommitURL({
                        project:'grade9-pilot',target:'TeamCoordinator',
                        type:'INFO',text:'Some words',replaces:'../../other'
                      }); return false; } catch (e) { return true; }
                    }"""))
                check("WP7_UI_05_foreign_repo_trace_link_rejected",
                    lambda: page.evaluate("""() =>
                      traceSafeGitHubURL('https://github.com/unrelated/other/issues/1') === null"""))
                page.goto(base+"#home",wait_until="networkidle")
                check("WP7_UI_06_json_input_is_in_needs_you_with_trace",
                    lambda: OI in page.locator("#needs-you-list").inner_text()
                       and page.locator(f'#needs-you-list a[href="#trace/{OI}"]').count()==1)
                page.goto(base+"#trace/"+OI,wait_until="networkidle")
                check("WP7_UI_07_json_trace_and_ack_have_commit_permalinks",
                    lambda: page.locator(".trace-step[data-step='posted'] a").count()==1
                       and page.locator(".trace-step[data-step='ack'] a").count()==1
                       and page.locator(".trace-step[data-step='ack'] a").get_attribute("href")==receipt
                       and "ACKNOWLEDGED" in page.locator("#trace-status").inner_text())
                check("WP7_UI_08_percent_encoding_round_trips_unicode_and_symbols",
                    lambda: page.evaluate("""() => {
                      const made=ownerJSONCommitURL({
                        project:'grade9-pilot',target:'TeamCoordinator',type:'INFO',
                        text:'Grade 9 & algebra — مراجعة?',replaces:''
                      });
                      const parsed=new URL(made.url);
                      const record=JSON.parse(parsed.searchParams.get('value'));
                      return parsed.pathname.endsWith('/new/main') &&
                        record.text==='Grade 9 & algebra — مراجعة?' &&
                        parsed.searchParams.get('filename')===
                          'logs/grade9-pilot/inputs/'+record.id+'.json';
                    }"""))
                check("WP7_UI_09_reject_overlong_encoded_url",
                    lambda: page.evaluate("""() => {
                      try {
                        ownerJSONCommitURL({
                          project:'grade9-pilot',target:'TeamCoordinator',
                          type:'INFO',text:'é'.repeat(1400),replaces:''
                        });
                        return false;
                      } catch (e) { return String(e.message).includes('too long'); }
                    }"""))
                browser.close()
        finally:
            server.shutdown()
    print(f"WP7_BROWSER_COUNTS pass={len(passed)} fail={len(failed)} error={len(errors)}")
    if failed:print("WP7_BROWSER_FAILED_NAMES "+",".join(failed))
    if errors:print("WP7_BROWSER_ERROR_NAMES "+",".join(errors))
    if failed or errors:sys.exit(1)

if __name__=="__main__":
    main()
