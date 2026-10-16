#!/usr/bin/env python3
"""WP9: actual Chromium decision answer controls, GitHub commit URL and readback.

The same browser checks run against old page JS/HTML for behavioural RED.
No API write, issue, GitHub token, deployment or actual Owner decision.
"""
import json
from pathlib import Path
import shutil
import sys
import tempfile
from urllib.parse import urlparse,parse_qs

from browser_smoke_test import find_free_port,start_server

REPO="reallakshman19/CoordinatorLandingpage"
ID="G9-DIFF-13"
OI="OI-20261015-183000-abcd"
SHA="a"*40


def saved_answer(association="MEMBER",status="OPEN",receipt=None):
    return {
      "id":OI,"number":None,"source_kind":"json_file","project":"grade9-pilot",
      "type":"DECISION","target":"TeamCoordinator",
      "text":ID+': Accept\nQuestion: "approve the 13 difficulty corrections confirmed by both g1 agents"',
      "status":status,"state":status.lower(),
      "ts":"2026-10-15T18:30:00Z","updated_at":"2026-10-15T18:30:00Z",
      "author_association":association,"is_outsider":association=="UNKNOWN",
      "source_commit":SHA,"flags":[],"authority":"UNVERIFIED","effective":False,
      "issue_url":f"https://github.com/{REPO}/blob/{SHA}/logs/grade9-pilot/inputs/{OI}.json",
      "receipt":receipt
    }


def main():
    if len(sys.argv)!=2:raise SystemExit("usage: python tests/wp9_browser_test.py <artifact>")
    from playwright.sync_api import sync_playwright
    passed,failed,errors=[],[],[]
    def check(key,fn):
        try:
            good=bool(fn())
        except Exception as exc:
            good=False
            errors.append(key+"="+type(exc).__name__)
        (passed if good else failed).append(key)
        print(("PASS " if good else "FAIL ")+key)

    with tempfile.TemporaryDirectory() as temp:
        root=Path(temp)/"site"
        shutil.copytree(Path(sys.argv[1]).resolve(),root)
        inputs=root/"data"/"owner-inputs.json"
        inputs.write_text("[]",encoding="utf-8")
        server=start_server(str(root),find_free_port())
        try:
            with sync_playwright() as pw:
                browser=pw.chromium.launch(headless=True)
                base=f"http://127.0.0.1:{server.server_address[1]}/index.html"
                page=browser.new_page(viewport={"width":1100,"height":940})
                page.goto(base+"#project/grade9-pilot",wait_until="networkidle")
                card=page.locator("#open-decisions-list .decision-card").filter(
                    has=page.locator(".decision-card-id",has_text=ID)).first
                buttons=card.locator(".decision-answer-btn")
                present=(buttons.count()==3)
                check("WP9_UI_01_three_project_decision_answer_buttons",
                      lambda: present and
                        set(buttons.evaluate_all("(els)=>els.map(x=>x.dataset.choice)"))==
                        {"Accept","Hold","Other"})
                check("WP9_UI_02_commit_twice_hint_visible_on_card",
                      lambda: present and
                        "GitHub opens — click Commit changes twice" in
                        card.locator(".decision-commit-hint").inner_text())
                check("WP9_UI_03_draft_is_not_recorded_or_approved",
                      lambda: present and
                        card.locator(".decision-answer-state").count()==0 and
                        "approved" not in card.inner_text().lower())
                if present:
                    page.evaluate("window.open = (url)=>{window.__lastDecisionURL=url;return null}")
                    card.locator('button[data-choice="Accept"]').click()
                def prepared():
                    url=page.evaluate("window.__lastDecisionURL || ''")
                    query=parse_qs(urlparse(url).query)
                    obj=json.loads(query.get("value",["{}"])[0])
                    return url,query,obj
                check("WP9_UI_04_accept_opens_new_file_json_one_click",
                      lambda: present and
                        (lambda u,q,r:
                          u.startswith(f"https://github.com/{REPO}/new/main?") and
                          q.get("filename",[""])[0]==
                          f"logs/grade9-pilot/inputs/{r['id']}.json" and
                          r.get("project")=="grade9-pilot" and
                          r.get("target")=="TeamCoordinator" and
                          r.get("type")=="DECISION" and
                          r.get("text","").startswith(ID+": Accept\nQuestion: \"") and
                          "approve the 13 difficulty corrections" in r.get("text","") and
                          "token=" not in u and "issues/new" not in u
                        )(*prepared()))
                check("WP9_UI_05_input_form_prefilled_from_one_click_accept",
                      lambda: present and page.url.endswith("#owner-inputs") and
                        page.locator("#oi-json-project").input_value()=="grade9-pilot" and
                        page.locator("#oi-json-target").input_value()=="TeamCoordinator" and
                        page.locator("#oi-json-type").input_value()=="DECISION" and
                        page.locator("#oi-json-text").input_value().startswith(ID+": Accept\n") and
                        "Nothing is posted" not in page.locator("#oi-json-result").inner_text() and
                        "Commit changes twice" in page.locator("#oi-json-result").inner_text())
                page.goto(base+"#home",wait_until="networkidle")
                home=page.locator(f"#needs-you-list li.needs-pending").filter(
                    has=page.locator("strong",has_text=ID)).first
                home_hold=home.locator('button[data-choice="Hold"]')
                has_home_hold=home_hold.count()==1
                if has_home_hold:
                    page.evaluate("window.open = (url)=>{window.__lastDecisionURL=url;return null}")
                    home_hold.click()
                check("WP9_UI_06_home_hold_button_prefills_opens_github",
                      lambda: has_home_hold and
                        prepared()[2].get("text","").startswith(ID+": Hold\nQuestion: \"") and
                        page.url.endswith("#owner-inputs") and
                        page.locator("#oi-json-text").input_value().startswith(ID+": Hold\n"))
                page.goto(base+"#decision/grade9-pilot/"+ID,wait_until="networkidle")
                other=page.locator('#view-decision button[data-choice="Other"]')
                has_other=other.count()==1
                if has_other:
                    page.evaluate("""() => {
                      window.prompt = () => 'Please attach checker evidence';
                      window.open = (url)=>{window.__lastDecisionURL=url;return null};
                    }""")
                    other.click()
                check("WP9_UI_07_other_answer_requires_custom_text_and_opens_github",
                      lambda: has_other and
                        prepared()[2].get("text","").startswith(
                          ID+": Other: Please attach checker evidence\nQuestion: \"") and
                        page.locator("#oi-json-type").input_value()=="DECISION")
                page.goto(base+"#project/grade9-pilot",wait_until="networkidle")
                # Async project rendering can lag page.goto(networkidle).
                # The original >=3 button and no-answered-state assertions
                # remain intact; absence stays FAIL, never a runner ERROR.
                def decisions_rendered():
                    try:
                        page.locator(
                            '#open-decisions-list .decision-card .decision-answer-btn'
                        ).first.wait_for(state="attached", timeout=5000)
                        return True
                    except Exception:
                        return False
                check("WP9_UI_08_prepared_but_uncommitted_draft_never_marks_answered",
                      lambda: decisions_rendered() and page.locator(
                          f'#open-decisions-list .decision-card .decision-answer-btn'
                        ).count()>=3 and
                        "answered, waiting for receipt" not in
                        page.locator("#open-decisions-list").inner_text())

                # Simulate only a *saved, read-back* file. The browser itself
                # never writes Github or changes the input file.
                inputs.write_text(json.dumps([saved_answer()]),encoding="utf-8")
                committed=browser.new_page()
                committed.goto(base+"#project/grade9-pilot",wait_until="networkidle")
                accepted=committed.locator("#open-decisions-list .decision-card").filter(
                    has=committed.locator(".decision-card-id",has_text=ID)).first
                check("WP9_UI_09_only_recorded_associated_file_marks_waiting_for_receipt",
                      lambda: accepted.locator(".decision-answer-state").count()==1 and
                        "answered, waiting for receipt" in
                        accepted.locator(".decision-answer-state").inner_text())
                committed.goto(base+"#home",wait_until="networkidle")
                check("WP9_UI_10_home_decision_status_comes_from_committed_file",
                      lambda: "answered, waiting for receipt" in
                        committed.locator("#needs-you-list").inner_text())
                committed.goto(base+"#decision/grade9-pilot/"+ID,wait_until="networkidle")
                check("WP9_UI_11_decision_detail_uses_same_recorded_answer_state",
                      lambda: "answered, waiting for receipt" in
                        committed.locator("#view-decision .decision-answer-state").inner_text()
                        if committed.locator("#view-decision .decision-answer-state").count() else False)
                committed.close()

                inputs.write_text(json.dumps([saved_answer(association="UNKNOWN")]),encoding="utf-8")
                outsider=browser.new_page()
                outsider.goto(base+"#project/grade9-pilot",wait_until="networkidle")
                check("WP9_UI_12_foreign_author_cannot_spoof_answered_state",
                      lambda: outsider.locator(
                        "#open-decisions-list .decision-answer-btn").count()>=3 and
                        outsider.locator(
                        "#open-decisions-list .decision-answer-state").count()==0)
                outsider.close()

                receipt=f"https://github.com/{REPO}/blob/{SHA}/logs/grade9-pilot/receipts.jsonl#L1"
                inputs.write_text(json.dumps([saved_answer(status="HANDLED",receipt=receipt)]),encoding="utf-8")
                handler=browser.new_page()
                handler.goto(base+"#decision/grade9-pilot/"+ID,wait_until="networkidle")
                check("WP9_UI_13_trusted_receipt_is_not_owner_approval",
                      lambda: handler.locator(".decision-answer-state").count()==1 and
                        "linked handler receipt recorded" in
                          handler.locator(".decision-answer-state").inner_text() and
                        "not Owner approval" in
                          handler.locator(".decision-answer-state").inner_text() and
                        "answered, waiting for receipt" not in
                          handler.locator(".decision-answer-state").inner_text())
                handler.close()
                browser.close()
        finally:
            server.shutdown()
    print(f"WP9_BROWSER_COUNTS pass={len(passed)} fail={len(failed)} error={len(errors)}")
    if failed:print("WP9_BROWSER_FAILED_NAMES "+",".join(failed))
    if errors:print("WP9_BROWSER_ERROR_NAMES "+",".join(errors))
    if failed or errors:sys.exit(1)

if __name__=="__main__":main()
