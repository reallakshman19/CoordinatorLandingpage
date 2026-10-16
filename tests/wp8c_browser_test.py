#!/usr/bin/env python3
"""WP8c: browser security regressions. Synthetic public data, no write actions."""
import json
from pathlib import Path
import shutil
import sys
import tempfile
from urllib.parse import quote

from browser_smoke_test import find_free_port, start_server

REPO = "reallakshman19/CoordinatorLandingpage"
PAYLOAD = '<img src=x onerror="window.__wp8c_xss=1">'
INPUT = "OI-20261015-163000-abcd"


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: python tests/wp8c_browser_test.py <artifact>")
    from playwright.sync_api import sync_playwright
    passed, failed, errors = [], [], []

    def check(name, expression):
        try:
            ok = bool(expression())
        except Exception as exc:
            ok = False
            errors.append(name + "=" + type(exc).__name__)
        (passed if ok else failed).append(name)
        print(("PASS " if ok else "FAIL ") + name)

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "site"
        shutil.copytree(Path(sys.argv[1]).resolve(), root)
        projects_file = root / "data/projects.json"
        projects = json.loads(projects_file.read_text(encoding="utf-8"))
        sample = dict(projects[0])
        sample["project"] = PAYLOAD
        projects.insert(0, sample)
        projects_file.write_text(json.dumps(projects), encoding="utf-8")
        inputs_file = root / "data/owner-inputs.json"
        inputs_file.write_text(json.dumps([{
            "id": INPUT, "number": None, "source_kind": "json_file",
            "project": "grade9-pilot", "target": "TeamCoordinator",
            "type": "QUESTION", "text": PAYLOAD, "status": "OPEN",
            "author_association": "MEMBER", "is_outsider": False,
            "ts": "2026-10-15T16:30:00Z", "updated_at": "2026-10-15T16:30:00Z",
            "receipt": None, "flags": []
        }]), encoding="utf-8")
        server = start_server(str(root), find_free_port())
        try:
            with sync_playwright() as pw:
                browser = pw.chromium.launch(headless=True)
                page = browser.new_page(viewport={"width": 1100, "height": 940})
                page.goto(f"http://127.0.0.1:{server.server_address[1]}/index.html#home",
                          wait_until="networkidle")
                base = page.url.split("#")[0]
                check("WP8C_UI_01_project_xss_is_literal_text",
                      lambda: PAYLOAD in page.locator("#projects-tbody").inner_text()
                      and page.locator("#projects-tbody img").count() == 0
                      and page.evaluate("window.__wp8c_xss || 0") == 0)

                page.goto(base + "#owner-inputs", wait_until="networkidle")
                check("WP8C_UI_02_input_text_xss_is_literal_text",
                      lambda: PAYLOAD in page.locator("#oi-list .oi-text").inner_text()
                      and page.locator("#oi-list img").count() == 0
                      and page.evaluate("window.__wp8c_xss || 0") == 0)

                for index, project in enumerate(("unlisted-project", ".."), 3):
                    page.evaluate("""p => {
                      const s = document.querySelector('#oi-json-project');
                      s.add(new Option(p, p)); s.value = p;
                      document.querySelector('#oi-json-target').value = 'TeamCoordinator';
                      document.querySelector('#oi-json-text').value = 'Test';
                      window.open = u => { window.__wp8c_opened = u; return null; };
                      window.__wp8c_opened = null;
                    }""", project)
                    page.locator("#oi-json-form button[type=submit]").click()
                    check(f"WP8C_UI_0{index}_unlisted_project_rejected",
                          lambda: "Choose a listed project" in
                          page.locator("#oi-json-result").inner_text()
                          and page.evaluate("window.__wp8c_opened === null"))

                page.goto(base + "#decision/grade9-pilot/G9-DIFF-13",
                          wait_until="networkidle")
                check("WP8C_UI_05_github_issue_backup_secondary",
                      lambda: page.locator("#dc-answer-btn.btn-backup").count() == 1
                      and page.locator("#dc-answer-btn.btn-primary").count() == 0
                      and "backup" in page.locator("#dc-answer-btn").inner_text())

                requests = []
                page.on("request", lambda req: requests.append(req.url))
                page.goto(base + "#agent/grade9-pilot/" +
                          quote(PAYLOAD, safe=""), wait_until="networkidle")
                check("WP8C_UI_06_id8_xss_as_text_no_evidence_fetch",
                      lambda: PAYLOAD in page.locator("#app").inner_text()
                      and page.locator("#app img").count() == 0
                      and page.evaluate("window.__wp8c_xss || 0") == 0
                      and not any("/evidence-" in url for url in requests))
                requests.clear()
                page.goto(base + "#agent/grade9-pilot/..", wait_until="networkidle")
                check("WP8C_UI_07_id8_traversal_rejected_before_fetch",
                      lambda: "Invalid agent reference" in
                      page.locator("#app").inner_text()
                      and not any("/evidence-" in url for url in requests))

                page.goto(base + "#project/..", wait_until="networkidle")
                check("WP8C_UI_08_dotdot_project_rejected",
                      lambda: "not found" in page.locator("#app").inner_text().lower()
                      and not page.locator("#app script, #app img").count())
                browser.close()
        finally:
            server.shutdown()
    print(f"WP8C_BROWSER_COUNTS pass={len(passed)} fail={len(failed)} error={len(errors)}")
    if failed:
        print("WP8C_BROWSER_FAILED_NAMES " + ",".join(failed))
    if errors:
        print("WP8C_BROWSER_ERROR_NAMES " + ",".join(errors))
    if failed or errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
