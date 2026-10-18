"""WP-V2 D3 browser proof: cached post-checkpoint amendment is source visible.

The continuity acceptance condition lives in test_v2_d3_amendment.py and must
not be satisfied by the unrelated 30-minute freshness timeout.
"""
from pathlib import Path
import shutil
import sys
import tempfile

from browser_smoke_test import start_server, find_free_port
from test_v2_d3_amendment import build_snapshot, SOURCE, CHANGED_INTENT, PROJECT


def run(artifact):
    from playwright.sync_api import sync_playwright
    passed, failed = [], []
    def check(name, valid):
        (passed if valid else failed).append(name)
        print(("PASS " if valid else "FAIL ") + name, flush=True)

    with tempfile.TemporaryDirectory() as temp:
        base = Path(temp)
        _, project, summary, _, output = build_snapshot(base / "case")
        site = base / "site"
        shutil.copytree(Path(artifact).resolve(), site)
        data = site / "data"
        data.mkdir(parents=True, exist_ok=True)
        # Preserve all other published data but point at this isolated drill.
        (data / "projects.json").write_text(__import__("json").dumps([summary]))
        shutil.copy2(output / ("project-" + PROJECT + ".json"),
                     data / ("project-" + PROJECT + ".json"))
        server = start_server(str(site), find_free_port())
        try:
            with sync_playwright() as pw:
                browser = pw.chromium.launch(headless=True)
                page = browser.new_page()
                errors = []
                page.on("pageerror", lambda e: errors.append(str(e)))
                page.goto(f"http://127.0.0.1:{server.server_address[1]}/"
                          f"index.html#understanding/{PROJECT}", wait_until="networkidle")
                view = page.locator("#l4-understanding")
                view.wait_for(timeout=10000)
                content = view.inner_text()
                check("D3_PROJECT_UNDERSTANDING_SHOULD_SHOW_OWNER_CHANGE",
                      CHANGED_INTENT in content)
                check("D3_SOURCE_LINK_ON_AMENDMENT",
                      SOURCE in view.locator("a[href]").evaluate_all(
                          "(nodes)=>nodes.map(n=>n.href).join(' ')" ))
                check("D3_NOT_ERASED_BY_OLD_INTENT", "synthetic root intent" not in content.lower()
                      or CHANGED_INTENT in content)
                check("D3_NO_BROWSER_ERRORS", not errors)
                browser.close()
        finally:
            server.shutdown()
    print(f"WP_V2_D3_BROWSER={len(passed)}/{len(passed)+len(failed)}", flush=True)
    if failed:
        raise SystemExit("WP-V2 D3 browser failed: " + ", ".join(failed))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: wp_v2_d3_browser_test.py <site_artifact>")
    run(sys.argv[1])
