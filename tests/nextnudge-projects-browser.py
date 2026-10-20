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
    assert page.locator("#project-grounding-form textarea").count() == 17
    assert page.get_by_text("Master Log", exact=True).count() >= 1
    assert "Midcycle 1" not in page.locator("#project-grounding-form").inner_text()
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
    inline = page.locator("#new-thread-error")
    assert inline.is_visible(), "Duplicate agent feedback must be beside Create, not only at the page top"
    assert "already has a project thread" in inline.inner_text()
    assert page.evaluate("document.activeElement?.id") == "new-thread-error"
    assert page.locator('#new-thread input[name="title"]').input_value() == "Collision"
    assert page.locator('button[data-open]').count() == 2
    # F2: the device-only member has not been saved to GitHub; publication must be blocked.
    page.locator('[data-action="project-save"]').click()
    page.get_by_text("Save thread Agent One", exact=False).first.wait_for()
    assert page.locator('button[data-open]').count() == 2
    # F1: manual confirmation cannot label a G1 thread's exact task packet as G2.
    page.locator('button[data-open]').filter(has_text="Agent One").first.click()
    page.locator('nav.workspace-tabs button[data-action="workspace-task"]').click()
    page.locator('#workspace-form textarea[name="task"]').fill("One bounded source task for G1")
    page.locator('#workspace-form textarea[name="deliverable"]').fill("A recorded source-backed result")
    page.locator('#workspace-form textarea[name="success"]').fill("Verify one observable result")
    page.locator('[data-action="workspace-build"]').click()
    page.locator('#composer [data-action="record-sent"]').wait_for()
    page.locator('#composer button[data-action="record-sent"]').click()
    page.locator('#sent-confirm input[name="agent"]').fill("Agent Two")
    page.locator('#sent-confirm input[name="approved"]').check()
    page.locator('#sent-confirm button[type="submit"]').click()
    assert "Project agent mismatch" in page.locator("#notice").inner_text()
    # F1: the original GitHub delivery controls must also reject a G2 target.
    page.locator('#delivery-issue').fill("118")
    page.locator('#delivery-agent').fill("Agent Two")
    page.locator('[data-action="send-github"]').click()
    page.get_by_text("Project agent mismatch", exact=False).first.wait_for()
    page.screenshot(path=str(OUT / "review-f1-f2-rejected.png"), full_page=True)
    # Preserve the successfully built G1 Task using its correct bound agent.
    page.locator('#sent-confirm input[name="agent"]').fill("Agent One")
    page.locator('#sent-confirm button[type="submit"]').click()
    page.locator("#composer").wait_for(state="attached")
    # Project Master Log reads original records; it creates no second Task record.
    page.locator('[data-action="project"]').first.click()
    page.locator('[data-action="master-log"]').click()
    page.get_by_role("heading", name="Master Log · Project A", exact=True).wait_for()
    page.get_by_text("Agent One · Task", exact=False).first.wait_for()
    assert page.locator(".master-log-item").count() >= 1
    page.locator(".master-log-item a").first.click()
    page.get_by_role("heading", name="Agent One delivery", exact=True).wait_for()
    assert page.locator('.move-summary[id^="move-"]').count() >= 1
    assert "move=" in page.url
    # BETA has no G1 Task from ALPHA; the project feed must not leak across projects.
    page.locator('[data-action="project"]').first.click()
    page.locator('[data-action="projects"]').first.click()
    page.get_by_role("button", name="Project B", exact=False).click()
    page.locator('[data-action="master-log"]').click()
    page.get_by_role("heading", name="Master Log · Project B", exact=True).wait_for()
    assert page.locator(".master-log-item").count() == 0
    page.locator('[data-action="projects"]').first.click()
    page.get_by_role("button", name="Project A", exact=False).click()
    page.locator('button[data-open]').filter(has_text="Agent One").first.click()
    # F3: inject a corrupt sibling record; real reload must keep the healthy project and thread usable.
    page.evaluate("""() => {
      const key='nextnudge.projects.v1', all=JSON.parse(localStorage.getItem(key));
      all['MALFORMED']={version:999,unexpected:'keep this raw entry'};
      localStorage.setItem(key,JSON.stringify(all));
    }""")
    page.reload(wait_until="domcontentloaded")
    page.get_by_role("heading", name="Agent One delivery", exact=True).wait_for()
    assert "invalid local project record" in page.locator("#notice").inner_text()
    assert page.evaluate("""() => JSON.parse(localStorage.getItem('nextnudge.projects.v1')).MALFORMED.unexpected""") == "keep this raw entry"
    page.screenshot(path=str(OUT / "review-f3-corrupt-recovered.png"), full_page=True)
    # G2-F01: one authentic legacy thread may appear in two project memberships.
    # Preserve the thread's original packets and open it without selecting either fixture store.
    legacy_id = "NN-20261018-171656-66d2"
    import hashlib
    import json
    def sent_packets():
        raw = page.evaluate("""id => JSON.parse(localStorage.getItem('nextnudge.threads.v3'))[id]""", legacy_id)
        return [hashlib.sha256(m["packet"].encode("utf-8")).hexdigest()
                for m in raw["moves"] if m.get("delivery") == "sent"]
    original_hashes = sent_packets()
    assert original_hashes, "Historical NLM thread must contain genuine sent packets"
    page.evaluate("""id => {
      const key='nextnudge.projects.v1', rows=JSON.parse(localStorage.getItem(key));
      for (const p of Object.values(rows)) {
        if (p.name==='Project A' || p.name==='Project B')
          p.threads.push({id,agent:'Google Antigravity',legacy:true});
      }
      localStorage.setItem(key,JSON.stringify(rows));
    }""", legacy_id)
    page.goto("/nextnudge/", wait_until="domcontentloaded")
    page.get_by_role("button", name="Project A", exact=False).click()
    page.locator('button[data-open="'+legacy_id+'"]').click()
    page.get_by_role("heading", name="NLM validator · PR #299 review", exact=True).wait_for()
    assert "Ambiguous project association" in page.locator("#notice").inner_text()
    assert page.locator("summary").filter(has_text="Earlier moves").count() == 1
    assert sent_packets() == original_hashes, "Project navigation altered exact legacy packets"
    page.screenshot(path=str(OUT / "review-legacy-ambiguous-open.png"), full_page=True)
    # Cold direct link and explicit Markdown import use the same conservative association choice.
    page.goto("/nextnudge/?thread="+legacy_id, wait_until="domcontentloaded")
    page.get_by_role("heading", name="NLM validator · PR #299 review", exact=True).wait_for()
    assert "Ambiguous project association" in page.locator("#notice").inner_text()
    assert sent_packets() == original_hashes
    source = SITE / "nextnudge-data" / "threads" / (legacy_id + ".md")
    page.locator("#import-file").set_input_files(str(source))
    page.get_by_role("heading", name="NLM validator · PR #299 review", exact=True).wait_for()
    assert "Ambiguous project association" in page.locator("#notice").inner_text()
    assert sent_packets() == original_hashes, "Import altered historical packet bytes"
    print("NN118_CHROMIUM: PASS navigation, sharing, isolation, F1-F3 and G2-F01 ambiguous legacy open/URL/import with authentic sent-packet SHA")


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
