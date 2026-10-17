"""WP-L6 UI and WP-L4 follow-ups, real Chromium on the existing artifact."""
import json
from pathlib import Path
import shutil
import sys
import tempfile
from browser_smoke_test import start_server, find_free_port


def main(artifact):
    from playwright.sync_api import sync_playwright
    results = []
    def check(label, value):
        results.append((label, bool(value)))
        print(("PASS " if value else "FAIL ") + label, flush=True)
    with tempfile.TemporaryDirectory() as temp:
        site = Path(temp) / "site"
        shutil.copytree(Path(artifact).resolve(), site)
        data = site / "data"
        source = json.loads((data / "status-bar.json").read_text())
        row = source["projects"][0]
        row["continuity"] = {"light": "red", "inputs": {
            "intent_linked": {"state": "OK", "source":
                "https://github.com/reallakshman19/CoordinatorLandingpage/issues/21"},
            "originals_declared": {"state": "PROBLEM", "source": None,
                                   "missing": ["master"]},
            "owner_input_captured": {"state": "UNKNOWN", "source": None},
            "lineage_verified": {"state": "OK", "source": None},
            "head_fresh": {"state": "OK", "source": None},
        }}
        (data / "status-bar.json").write_text(json.dumps(source), encoding="utf-8")
        server = start_server(str(site), find_free_port())
        try:
            with sync_playwright() as browser:
                page = browser.chromium.launch(headless=True).new_page()
                errors = []
                page.on("pageerror", lambda exc: errors.append(str(exc)))
                root = f"http://127.0.0.1:{server.server_address[1]}/index.html"
                page.goto(root + "#status-bar", wait_until="networkidle")
                page.wait_for_selector(".wp16-continuity-light")
                check("CONTINUITY_RED_VISIBLE", "RED" in
                      page.locator(".wp16-continuity-light").first.inner_text())
                check("FIVE_INPUTS_VISIBLE",
                      page.locator(".wp16-continuity-input").count() >= 5)
                check("MISSING_ORIGINAL_VISIBLE",
                      "master" in page.locator("#wp16-ot-rows").inner_text())
                check("CONTINUITY_SOURCE_LINK_ALLOWLIST",
                      bool(page.locator(".wp16-continuity-input a[href*='/issues/21']").count()))
                check("EXISTING_THREE_DIMENSIONS_REMAIN",
                      page.locator("#wp16-tc-table th").count() == 14)
                page.goto(root + "#people/landing-live", wait_until="networkidle")
                page.wait_for_selector(".l4-oracle")
                check("ORACLE_NONE_AND_ADVISORY_ONLY",
                      "none" in page.locator(".l4-oracle").inner_text() and
                      "advises only" in page.locator(".l4-oracle").inner_text())
                check("L4_UNKNOWN_RULE", page.locator(".l4-unknown").evaluate_all(
                     "(nodes) => nodes.length===0 || nodes.every(x => getComputedStyle(x).color !== 'rgba(0, 0, 0, 0)')"))
                page.goto(root + "#changeover/landing-live", wait_until="networkidle")
                page.wait_for_selector("#l4-changeover")
                brief = page.evaluate("""() => l4SuccessorBrief(
                    {projectName:'test',repo:'reallakshman19/Common',
                     summary:{source_refs:{}}},
                    {outgoing:'**evil**\n# forged section',
                     incoming:'[role](https://invalid.invalid)',
                     pending_sends:['- [ ] unauthorized step']}
                  )""")
                check("SUCCESSOR_BRIEF_MARKDOWN_ESCAPED",
                      "\\*\\*evil\\*\\* # forged section" in brief
                      and "\\[role\\]\\(https://invalid\\.invalid\\)" in brief
                      and "\\- \\[ \\] unauthorized step" in brief)
                check("NO_PAGE_ERRORS", not errors)
        finally:
            server.shutdown()
    if not all(status for _, status in results):
        raise SystemExit("WP-L6 browser failure")
    print(f"WP_L6_BROWSER={len(results)}/{len(results)}", flush=True)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: wp_l6_browser_test.py <site_artifact>")
    main(sys.argv[1])
