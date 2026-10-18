"""WP-V4 D5 real Chromium view: retired actor is evidence-visible, not actionable."""
import json
from pathlib import Path
import shutil
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build_data
from browser_smoke_test import start_server, find_free_port

PROJECT = "landing-live"
RETIRED = "6ad36e4d"
SYNTHETIC_ID = 990004005


def run(artifact):
    from playwright.sync_api import sync_playwright
    passed, failed = [], []

    def check(name, good):
        (passed if good else failed).append(name)
        print(("PASS " if good else "FAIL ") + name, flush=True)

    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        site = root / "site"
        shutil.copytree(Path(artifact).resolve(), site)
        reg_path = root / "logs" / PROJECT / "registry.json"
        reg_path.parent.mkdir(parents=True)
        # The live registry is READ; only this isolated copy is changed.
        reg = json.loads((ROOT / "logs" / PROJECT / "registry.json").read_text())
        for agent in reg["agents"]:
            if agent.get("chat_id8") == RETIRED:
                agent["status"] = "RETIRED; SYNTHETIC D5 (not a real event)"
                agent["retired_at"] = "2026-10-18T03:30:00Z"
                agent["evidence_thread"] = (
                    "https://github.com/reallakshman19/CoordinatorLandingpage/issues/64")
        reg_path.write_text(json.dumps(reg))
        cache = root / "cache"
        (cache / "project-threads" / PROJECT).mkdir(parents=True)
        (cache / "capture-info.json").write_text(
            json.dumps({"status": "ok", "errors": []}))
        issue = {"number": 64, "repository": "reallakshman19/CoordinatorLandingpage",
                 "comments": [{"id": SYNTHETIC_ID,
                               "created_at": "2026-10-18T04:59:00Z",
                               "body": ("TASK EVIDENCE v2 · landing-live · coder · "
                                        f"chat {RETIRED} · #4 · 18 Oct 08:59 +04\n"
                                        "Task: SYNTHETIC unapproved old work\nStatus: DONE")}]}
        (cache / "project-threads" / PROJECT / "issue-64.json").write_text(
            json.dumps(issue))
        build_data.build_all(root, site / "data", cache_dir=cache)
        data = json.loads((site / "data" /
                           f"evidence-{RETIRED}.json").read_text())
        recs = [e for e in data["agent"]["evidence"] if e["type"] == "evidence"]
        check("D5_SYNTHETIC_PROJECTION_INELIGIBLE",
              len(recs) == 1 and recs[0].get("eligibility") == "INELIGIBLE")
        server = start_server(str(site), find_free_port())
        try:
            with sync_playwright() as pw:
                browser = pw.chromium.launch(headless=True)
                page = browser.new_page()
                errors = []
                page.on("pageerror", lambda exc: errors.append(str(exc)))
                base = f"http://127.0.0.1:{server.server_address[1]}/index.html"
                page.goto(base + f"#agent/{PROJECT}/{RETIRED}",
                          wait_until="networkidle")
                page.locator("#agent-title").wait_for(timeout=10000)
                page.locator(".wp-v4-retired").first.wait_for(timeout=10000)
                check("D5_RETIRED_LABEL", "Ground/Suggest unavailable" in
                      page.locator(".wp-v4-retired").inner_text())
                check("D5_ACTION_BUTTONS_HIDDEN", not page.locator(
                    "#agent-action-buttons").is_visible())
                check("D5_INELIGIBLE_REPORT_STILL_VISIBLE",
                      page.locator(".wp-v4-ineligible").count() == 1 and
                      "no GO/acceptance" in page.locator(
                          ".wp-v4-ineligible").inner_text())
                check("D5_PAGE_NO_ERRORS", not errors)
                browser.close()
        finally:
            server.shutdown()
    print(f"WP_V4_D5_BROWSER={len(passed)}/{len(passed)+len(failed)}", flush=True)
    if failed:
        raise SystemExit("WP-V4 D5 Chromium failed: " + ", ".join(failed))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: wp_v4_d5_browser_test.py <site_artifact>")
    run(sys.argv[1])
