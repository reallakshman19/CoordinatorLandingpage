"""WP-L5 Chromium: fixture is visibly synthetic, never a live PASS."""
import json
from pathlib import Path
import shutil
import sys
import tempfile
from browser_smoke_test import start_server, find_free_port

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from landing_build.v36_scoreboard import scoreboard_project

def main(artifact):
    from playwright.sync_api import sync_playwright
    errors, results = [], []
    def check(name, ok):
        results.append((name, bool(ok)))
        print(("PASS " if ok else "FAIL ") + name, flush=True)
    with tempfile.TemporaryDirectory() as temp:
        site = Path(temp) / "site"
        shutil.copytree(Path(artifact).resolve(), site)
        data = site / "data"
        rows = json.loads((data / "projects.json").read_text())
        synthetic = scoreboard_project(
            ROOT, "v36-continuity",
            {"parent_issue": "https://github.com/reallakshman19/Common/issues/409"}, {})
        row = {"project": "v36-continuity",
               "repository": "reallakshman19/Common", "agents": [],
               "control": {}, "workflow": {}, "v36_scoreboard": synthetic}
        rows.append(row)
        (data / "projects.json").write_text(json.dumps(rows))
        (data / "project-v36-continuity.json").write_text(json.dumps(row))
        srv = start_server(str(site), find_free_port())
        try:
            with sync_playwright() as pw:
                browser = pw.chromium.launch(headless=True)
                page = browser.new_page()
                page.on("pageerror", lambda err: errors.append(str(err)))
                base = f"http://127.0.0.1:{srv.server_address[1]}/index.html"
                page.goto(base + "#project/v36-continuity", wait_until="networkidle")
                page.wait_for_selector("#v36-scoreboard")
                card = page.locator("#v36-scoreboard")
                text = card.inner_text()
                check("SYNTHETIC_LABEL_ALWAYS_VISIBLE", "synthetic fixture" in text.lower())
                check("CATEGORY_COVERAGE", "category coverage" in text)
                check("V36_E_FROM_PINNED", "1 / 7" in text)
                check("A_V_ACCEPTANCE_NOT_EVALUATED", text.count("NOT_EVALUATED") >= 3)
                check("NO_FALSE_LIVE_OR_PASS", "live scoreboard" not in text.lower()
                      and not card.locator(".badge-green").count())
                check("SOURCE_PARENT_DISTINCT", "Common#341" in text
                      and "Common/issues/409" in text)
                # Directly exercise corrupted and absent overlays as rendered.
                missing = {"status":"UNKNOWN", "source_class":"synthetic fixture",
                           "reason":"artifact_missing"}
                invalid = {"status":"ERROR", "source_class":"synthetic fixture",
                           "reason":"schema_mismatch"}
                check("UNKNOWN_VISIBLE", page.evaluate(
                    "(v) => { const target=document.createElement('div');"
                    "renderV36Scoreboard(target,v);return target.textContent.includes('UNKNOWN');}",
                    missing))
                check("ERROR_VISIBLE", page.evaluate(
                    "(v) => { const target=document.createElement('div');"
                    "renderV36Scoreboard(target,v);return target.textContent.includes('ERROR');}",
                    invalid))
                xss = {**synthetic, "tasks": [
                    {"task_id":"<img src=x onerror=alert(1)>", "E":"MISSING_CHILD",
                     "A":"NOT_EVALUATED","V":"NOT_EVALUATED",
                     "acceptance":"NOT_EVALUATED"}]}
                check("TEXT_ONLY_NO_INJECTED_IMAGE", page.evaluate(
                    "(v) => {const t=document.createElement('div');"
                    "renderV36Scoreboard(t,v);return t.querySelectorAll('img').length===0"
                    " && t.textContent.includes('<img src=x');}", xss))
                check("NO_PAGE_ERRORS", not errors)
                browser.close()
        finally:
            srv.shutdown()
    if not all(ok for _,ok in results):
        raise SystemExit("WP-L5 browser failure")
    print(f"WP_L5_BROWSER={len(results)}/{len(results)}", flush=True)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: wp_l5_browser_test.py <site_artifact>")
    main(sys.argv[1])
