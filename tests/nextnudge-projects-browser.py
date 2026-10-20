"""NN118: actual Chromium pointer-level navigation on locally served NextNudge assets."""
from __future__ import annotations
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
OUT = ROOT / "artifacts" / "nextnudge-projects-browser"


def test_navigation(page):
    page.goto("/nextnudge/", wait_until="domcontentloaded")
    page.get_by_role("heading", name="Projects", exact=True).wait_for()
    # Owner creates project A and Agent One's v3 thread.
    page.locator('#new-project input[name="name"]').fill("Project A")
    page.locator('#new-project button[type="submit"]').click()
    page.get_by_role("heading", name="Project A", exact=True).wait_for()
    def create_agent(name):
        form = page.locator("#new-thread")
        form.locator('input[name="agent"]').fill(name)
        form.locator('input[name="title"]').fill(name + " delivery")
        form.locator('textarea[name="goal"]').fill("Preserve Owner intent")
        form.locator('button[type="submit"]').click()
        page.get_by_role("heading", name=name + " delivery", exact=True).wait_for()
    create_agent("Agent One")
    for label in ("Overview", "Ground", "Task", "Correction", "Reconcile"):
        page.get_by_role("button", name=label, exact=False).first.wait_for()
    page.locator('nav.workspace-tabs button[data-action="grounding"]').click()
    page.locator("#project-grounding-form").wait_for()
    assert page.locator("#project-grounding-form textarea").count() == 25
    page.locator('#project-grounding-form textarea[name="ground-1f"]').fill("Shared Project A truth")
    page.locator('#project-grounding-form button[type="submit"]').first.click()
    page.locator('[data-action="project"]').first.click()
    # Agent Two gets another thread under the SAME project.
    create_agent("Agent Two")
    page.locator('nav.workspace-tabs button[data-action="grounding"]').click()
    value=page.locator('#project-grounding-form textarea[name="ground-1f"]').input_value()
    assert value == "Shared Project A truth", value
    OUT.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(OUT / "project-a-shared.png"), full_page=True)
    # A second project must not inherit those 25-heading values.
    page.locator('[data-action="project"]').first.click()
    page.locator('[data-action="projects"]').first.click()
    page.locator('#new-project input[name="name"]').fill("Project B")
    page.locator('#new-project button[type="submit"]').click()
    page.get_by_role("heading", name="Project B", exact=True).wait_for()
    page.locator('[data-action="project-grounding"]').click()
    assert page.locator('#project-grounding-form textarea[name="ground-1f"]').input_value() == ""
    page.screenshot(path=str(OUT / "project-b-isolation.png"), full_page=True)
    # Project B's active browser URL is repeatably navigable after reload.
    page.reload(wait_until="domcontentloaded")
    page.get_by_role("heading", name="Grounding Fixtures", exact=True).wait_for()
    assert page.locator('#project-grounding-form textarea[name="ground-1f"]').input_value() == ""
    # Return to A and verify duplicate active agent thread is rejected, not merged.
    page.locator('[data-action="project"]').first.click()
    page.locator('[data-action="projects"]').first.click()
    page.get_by_role("button", name="Project A", exact=False).click()
    page.locator('#new-thread input[name="agent"]').fill("Agent One")
    page.locator('#new-thread input[name="title"]').fill("Collision")
    page.locator('#new-thread textarea[name="goal"]').fill("Must be rejected")
    page.locator('#new-thread button[type="submit"]').click()
    assert "already has a project thread" in page.locator("#notice").inner_text()
    assert page.locator('button[data-open]').count() == 2
    print("NN118_CHROMIUM: PASS navigation, 25 headings, shared same-project, isolated second project, reload and duplicate block")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    server = ThreadingHTTPServer(("127.0.0.1", 0),
        partial(SimpleHTTPRequestHandler, directory=str(SITE)))
    worker = Thread(target=server.serve_forever, daemon=True)
    worker.start()
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(base_url=f"http://127.0.0.1:{server.server_port}")
            page = context.new_page()
            # No live main-data reads/writes are needed for this local pointer test.
            page.route("https://api.github.com/**", lambda route: route.fulfill(status=404, body="{}"))
            try:
                test_navigation(page)
            except Exception:
                page.screenshot(path=str(OUT / "failure.png"), full_page=True)
                raise
            finally:
                context.close()
                browser.close()
    finally:
        server.shutdown()


if __name__ == "__main__":
    main()
