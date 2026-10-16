#!/usr/bin/env python3
"""WP10 browser controls: synthetic published fixtures only; no GitHub writes."""
import json
from pathlib import Path
import shutil
import sys
import tempfile
from urllib.parse import parse_qs, urlparse

from browser_smoke_test import find_free_port, start_server

REPO = "reallakshman19/CoordinatorLandingpage"
PRODUCT = "example/3D_Converters"
ISSUE = f"https://github.com/{PRODUCT}/issues/12"
PR = f"https://github.com/{PRODUCT}/pull/13"


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: python tests/wp10_browser_test.py <artifact>")
    from playwright.sync_api import sync_playwright
    passed, failed, errors = [], [], []

    def check(name, evaluate):
        try:
            result = bool(evaluate())
        except Exception as exc:
            result = False
            errors.append(name + "=" + type(exc).__name__)
        (passed if result else failed).append(name)
        print(("PASS " if result else "FAIL ") + name)

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "site"
        shutil.copytree(Path(sys.argv[1]).resolve(), root)
        data = root / "data"
        projects_file = data / "projects.json"
        projects = json.loads(projects_file.read_text(encoding="utf-8"))
        sample = next(p for p in projects if p["project"] == "grade9-pilot")
        sample["auto_response"] = {
            "allowed": "yes", "scope": "Old authority", "until": "2020-01-01T00:00:00Z",
            "state": "EXPIRED", "critical_rules": "Critical requests need Owner approval."}
        product = dict(sample)
        product.update({
            "project": "3d-test", "repository": PRODUCT,
            "auto_response": {
                "allowed": "critical", "scope": "TeamCoordinator: routine FAQs",
                "until": "2099-01-01T00:00:00Z", "state": "IN_SCOPE",
                "critical_rules": "Critical decisions: Owner only. Do not delegate protected actions."
            },
            "external_links": [
                {"kind": "Issue", "url": ISSUE, "read_only": True},
                {"kind": "PR", "url": PR, "read_only": True},
                {"kind": "PR", "url": "javascript:alert(1)", "read_only": True},
            ],
            "agents": [
                {"role": "implementer", "chat_id8": "abcdef01", "generation": 2,
                 "status": "standby", "chat_end_risk": True, "handover_meter": 82,
                 "handover": ISSUE, "evidence_thread_num": 12},
                {"role": "checker", "chat_id8": "abcdef02", "generation": 1,
                 "status": "hold", "chat_end_seen": True, "chat_end_risk": True,
                 "handover": None, "evidence_thread_num": 12},
            ],
            "open_owner_decisions": [{
                "id": "TEST-ANSWER", "ask": "Shall we publish the converter?",
                "asked_at": "2026-10-15T08:00:00Z"
            }],
        })
        projects.append(product)
        projects_file.write_text(json.dumps(projects), encoding="utf-8")
        detail_file = data / "project-3d-test.json"
        detail = json.loads((data / "project-grade9-pilot.json").read_text())
        detail["project"] = "3d-test"
        detail["repository"] = PRODUCT
        detail["registry"]["standing_owner_decisions"] = [
            {'text': 'Owner\'s words: "Finish this"', "owner_words": "Finish this"},
            "(delegated) TeamCoordinator may answer questions.",
            "OwnerTeammember summary without a quoted Owner decision."
        ]
        detail_file.write_text(json.dumps(detail), encoding="utf-8")
        (data / "timeline-3d-test.json").write_text(json.dumps({
            "project": "3d-test", "events": [
                {"type": "OWNER_DECISION", "ts": "2026-10-16T08:00:00Z",
                 "text": 'Owner\'s words: "Finish this"'},
                {"type": "OWNER_DECISION", "ts": "2026-10-16T08:01:00Z",
                 "text": "(delegated) Routine inquiry answered."},
                {"type": "OWNER_DECISION", "ts": "2026-10-16T08:02:00Z",
                 "text": "Unsigned decision note."},
            ]}), encoding="utf-8")
        server = start_server(str(root), find_free_port())
        try:
            with sync_playwright() as pw:
                browser = pw.chromium.launch(headless=True)
                page = browser.new_page(viewport={"width": 1100, "height": 950})
                base = f"http://127.0.0.1:{server.server_address[1]}/index.html"
                page.goto(base + "#home", wait_until="networkidle")
                check("WP10_UI_01_expired_auto_response_is_not_valid",
                      lambda: page.locator("#auto-response-home").count() == 1
                      and "EXPIRED — no current delegation" in
                      page.locator("#auto-response-home").inner_text()
                      and "Critical requests need Owner approval." in
                      page.locator("#auto-response-home").inner_text())
                page.goto(base + "#project/3d-test", wait_until="networkidle")
                check("WP10_UI_02_critical_scope_and_expiry_visible",
                      lambda: page.locator("#auto-response-project").count() == 1
                      and "routine only; critical to Owner" in
                      page.locator("#auto-response-project").inner_text()
                      and "2099-01-01" in page.locator("#auto-response-project").inner_text())
                check("WP10_UI_03_generations_standby_hold_chat_end_risk",
                      lambda: page.locator("#agents-tbody .chat-end-risk").count() == 2
                      and "standby" in page.locator("#agents-tbody").inner_text()
                      and "hold" in page.locator("#agents-tbody").inner_text()
                      and "g2" in page.locator("#agents-tbody").inner_text())
                check("WP10_UI_04_takeover_is_safe_read_only_link",
                      lambda: page.locator(".agent-takeover-link").count() == 1
                      and page.locator(".agent-takeover-link").get_attribute("href") == ISSUE
                      and page.locator(".agent-takeover-link").get_attribute("rel") ==
                      "noopener noreferrer")
                check("WP10_UI_05_open_decision_card_uses_plain_words",
                      lambda: "No answer recorded yet. Owner action needed." in
                      page.locator("#open-decisions-list").inner_text()
                      and "Accept this decision" in page.locator("#open-decisions-list").inner_text())
                check("WP10_UI_06_standing_history_marks_owner_vs_delegated",
                      lambda: (lambda labels: labels == [
                          "Owner", "delegated (OwnerTeammember)", "unverified"])(
                          page.locator("#standing-decisions-section .decision-provenance")
                              .all_inner_texts()))
                check("WP10_UI_07_external_links_restricted_to_owning_repo",
                      lambda: set(page.locator(".external-project-link").evaluate_all(
                          "(a)=>a.map(x=>x.href)")) == {ISSUE, PR}
                      and page.locator(".external-project-link").count() == 2)
                page.goto(base + "#timeline/3d-test", wait_until="networkidle")
                # Hash navigation renders timelines asynchronously after several fetches.
                # Missing badges stay a behavioural FAIL (not a browser exception).
                def timeline_ready():
                    try:
                        page.locator("#timeline-events .decision-provenance").first.wait_for(
                            state="attached", timeout=8000)
                        return True
                    except Exception:
                        return False
                check("WP10_UI_08_timeline_owner_vs_delegated_labels",
                      lambda: timeline_ready() and (lambda texts: "Owner" in texts and
                          "delegated (OwnerTeammember)" in texts and "unverified" in texts)(
                          page.locator("#timeline-events .decision-provenance").all_inner_texts()))
                page.goto(base + "#owner-inputs", wait_until="networkidle")
                page.locator("#oi-json-form").wait_for(state="attached")
                page.evaluate("""() => {
                  window.__wp10URL = null;
                  window.open = u => { window.__wp10URL = u; return null; };
                  document.querySelector('#oi-json-project').value = '3d-test';
                  document.querySelector('#oi-json-target').value = 'TeamCoordinator';
                  document.querySelector('#oi-json-text').value = 'Routine project question';
                }""")
                page.locator("#oi-json-post").click()
                def fixed_commit():
                    url = page.evaluate("window.__wp10URL")
                    q = parse_qs(urlparse(url).query) if url else {}
                    value = json.loads(q["value"][0])
                    return (q.get("message") == [
                        "Owner input " + value["id"] + " via landing page"] and
                        q.get("filename") == [
                        f"logs/3d-test/inputs/{value['id']}.json"] and
                        url.startswith(f"https://github.com/{REPO}/new/main?"))
                check("WP10_UI_09_fixed_commit_message_prefilled", fixed_commit)
                browser.close()
        finally:
            server.shutdown()

    print(f"WP10_BROWSER_COUNTS pass={len(passed)} fail={len(failed)} error={len(errors)}")
    if failed: print("WP10_BROWSER_FAILED_NAMES " + ",".join(failed))
    if errors: print("WP10_BROWSER_ERROR_NAMES " + ",".join(errors))
    if failed or errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
