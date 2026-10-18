#!/usr/bin/env python3
"""WP-L4 browser qualification: six filled and six UNKNOWN project views."""
import json
from pathlib import Path
import shutil
import sys
import tempfile

from browser_smoke_test import start_server, find_free_port

CONTROL = "reallakshman19/CoordinatorLandingpage"
PRODUCT = "reallakshman19/Common"
LINK = f"https://github.com/{PRODUCT}/issues/62"
ROUTES = ("understanding", "people", "engineering-history",
          "sources", "improvements", "changeover")


def record(project, filled):
    base = {
        "project": project, "repository": PRODUCT, "agents": [],
        "source_refs": {"status_issue": LINK,
                        "inbox": f"https://github.com/{CONTROL}/issues/1"},
        "registry": {"workflow": {}, "control": {}, "standing_owner_decisions": []},
    }
    if filled:
        base.update({
            "lineage": [{"kind": "parent_issue", "status": "AVAILABLE",
                         "title": "Design the coordination relay", "url": LINK}],
            "intent": {"status": "AVAILABLE", "text": "Root Owner purpose <unsafe>.",
                       "source": LINK, "truncated": True},
            "amendments": {"status": "AVAILABLE", "source": f"https://github.com/{CONTROL}/issues/1",
                           "total_matching": 2, "truncated": False, "records": [
                {"comment_id": 75, "text": "Owner correction for probe <img>",
                 "source": f"https://github.com/{CONTROL}/issues/1#issuecomment-75",
                 "superseded": False, "attribution": "ASSOCIATED_NOT_OWNER_PROOF"},
                {"comment_id": 76, "text": "Superseded Owner amendment",
                 "source": f"https://github.com/{CONTROL}/issues/1#issuecomment-76",
                 "superseded": True, "attribution": "ASSOCIATED_NOT_OWNER_PROOF"}]},
            "registry": {"workflow": {"owner_words": "Preserve exact intent"},
                         "control": {"current_coordinator": {
                             "holder": "TeamCoordinator Agent", "verified": True,
                             "control_ref": LINK}},
                         "standing_owner_decisions": [{
                             "text": "Earlier plan superseded by correction",
                             "source": LINK, "supersedes": "previous"},
                             {"text": "Owner amendment adopted", "source": LINK}]},
            "originals": [{"name": "Missing master", "path": "masters/a.xml",
                           "class": "MISSING", "custody": "Owner"},
                          {"name": "Original input", "path": "input/b.xml",
                           "class": "ORIGINAL"}],
            "improvements": [{"id": "IMP1", "title": "Evidence intake", "author": "G2",
                               "disposition": "ADOPTED", "reason": "Coverage",
                               "implemented_in": LINK, "observed_result": "PASS",
                               "retain": True}],
            "succession": {"outgoing": "G1", "incoming": "G2",
                           "method": "BuddyRunner", "phase": "2",
                           "links": {"1a": LINK, "1b": LINK, "2": LINK},
                           "pending_sends": ["Task X"], "custody": "issue"},
            "agents": [{"role": "coder", "generation": 1, "chat_id8": "deadbeef",
                        "alias": "Coder G1", "evidence_thread_url": LINK},
                       {"role": "coder", "generation": 2, "chat_id8": "cafebabe",
                        "alias": "Coder G2", "evidence_thread_url": LINK}],
        })
    return base


def run(artifact):
    from playwright.sync_api import sync_playwright
    passed, failures = [], []
    def check(name, yes):
        (passed if yes else failures).append(name)
        print(("PASS " if yes else "FAIL ") + name, flush=True)
    with tempfile.TemporaryDirectory() as temp:
        site = Path(temp) / "site"
        shutil.copytree(Path(artifact).resolve(), site)
        data = site / "data"
        data.mkdir(exist_ok=True)
        originals = [record("probe", True), record("blank", False)]
        (data / "projects.json").write_text(json.dumps(originals), encoding="utf-8")
        for item in originals:
            (data / f"project-{item['project']}.json").write_text(
                json.dumps(item), encoding="utf-8")
        (data / "timeline-probe.json").write_text(json.dumps({"events": [
            {"type": "TASK_EVIDENCE", "actor": "OwnerTeammember",
             "ts": "2026-10-17T10:00:00Z", "text": "Evidence reviewed",
             "comment_url": LINK},
            {"type": "COORDINATOR", "actor": "TeamCoordinator",
             "ts": "2026-10-17T11:00:00Z", "text": "Coordinator observed",
             "comment_url": LINK}]}), encoding="utf-8")
        (data / "timeline-blank.json").write_text(
            json.dumps({"events": []}), encoding="utf-8")
        server = start_server(str(site), find_free_port())
        try:
            with sync_playwright() as pw:
                browser = pw.chromium.launch(headless=True)
                page = browser.new_page()
                page_errors = []
                page.on("pageerror", lambda exc: page_errors.append(str(exc)))
                expected_filled = {
                    "understanding": "Design the coordination relay",
                    "people": "TeamCoordinator Agent",
                    "engineering-history": "OwnerTeammember",
                    "sources": "Missing master",
                    "improvements": "Evidence intake",
                    "changeover": "BuddyRunner",
                }
                for view in ROUTES:
                    for name, filled in (("probe", True), ("blank", False)):
                        page.goto(f"http://127.0.0.1:{server.server_address[1]}/"
                                  f"index.html#{view}/{name}", wait_until="networkidle")
                        page.wait_for_selector(f'#l4-{view}', timeout=10000)
                        page.wait_for_timeout(100)
                        card = page.locator(f'#l4-{view}')
                        text = card.inner_text() if card.count() else ""
                        check(f"{view.upper()}_{'FILLED' if filled else 'UNKNOWN'}",
                              bool(card.count()) and
                              ((expected_filled[view] in text)
                               if filled else "UNKNOWN" in text))
                        check(f"{view.upper()}_NO_UNSAFE_LINK_{name}", all(
                            h.startswith("https://github.com/" + PRODUCT + "/")
                            or h.startswith("https://github.com/" + CONTROL + "/")
                            or h.startswith("#")
                            for h in card.locator("a[href]").evaluate_all(
                                "(nodes)=>nodes.map(a=>a.getAttribute('href'))")
                        ) if card.count() else False)
                page.goto(f"http://127.0.0.1:{server.server_address[1]}/"
                          "index.html#sources/probe", wait_until="networkidle")
                page.wait_for_selector("#l4-sources .badge-red", timeout=10000)
                check("MISSING_VISIBLE_RED", bool(page.locator(
                      "#l4-sources .badge-red").filter(has_text="MISSING").count()))
                page.goto(f"http://127.0.0.1:{server.server_address[1]}/"
                          "index.html#understanding/probe", wait_until="networkidle")
                page.wait_for_selector("#l4-understanding s a[href]", timeout=10000)
                check("SUPERSEDED_STRUCK_WITH_SOURCE", bool(
                    page.locator("#l4-understanding s a[href]").count()))
                text = page.locator("#l4-understanding").inner_text()
                check("ROOT_INTENT_TEXT_WITH_TRUNCATION",
                      "Root Owner purpose <unsafe>" in text and
                      "truncated" in text.lower())
                check("INBOX_AMENDMENT_TEXT_AND_SOURCE",
                      "Owner correction for probe <img>" in text and
                      bool(page.locator("#l4-understanding a[href*='issuecomment-75']").count()))
                check("AMENDMENT_SUPERSEDED_STRUCK",
                      bool(page.locator("#l4-understanding s a[href*='issuecomment-76']").count()))
                check("INERT_INTENT_AND_AMENDMENT",
                      not page.locator("#l4-understanding img").count())
                page.goto(f"http://127.0.0.1:{server.server_address[1]}/"
                          "index.html#understanding/blank", wait_until="networkidle")
                check("MISSING_INBOX_REASON_VISIBLE",
                      "UNKNOWN" in page.locator("#l4-understanding").inner_text()
                      and "not fetched" in page.locator("#l4-understanding").inner_text().lower())
                page.goto(f"http://127.0.0.1:{server.server_address[1]}/"
                          "index.html#people/probe", wait_until="networkidle")
                check("OTM_AND_TC_TWO_ROLES",
                      "OwnerTeammember" in page.locator("#l4-people").inner_text()
                      and "TeamCoordinator" in page.locator("#l4-people").inner_text())
                check("ORACLE_ADVISES_ONLY",
                      "advises only" in page.locator("#l4-people").inner_text())
                page.goto(f"http://127.0.0.1:{server.server_address[1]}/"
                          "index.html#changeover/probe", wait_until="networkidle")
                page.evaluate("""() => {
                  window.__copiedBrief = null;
                  Object.defineProperty(navigator, 'clipboard', {configurable:true,
                    value:{writeText: async text=>{window.__copiedBrief=text;}}});
                }""")
                page.locator("#l4-copy-brief").click()
                copied = page.evaluate("window.__copiedBrief")
                check("COPY_SUCCESSOR_MARKDOWN", bool(copied and
                      "G1" in copied and "G2" in copied and
                      "##" in copied and LINK in copied))
                check("NO_PAGE_ERRORS", not page_errors)
                browser.close()
        finally:
            server.shutdown()
    print(f"WP_L4_BROWSER={len(passed)}/{len(passed)+len(failures)}", flush=True)
    if failures:
        raise SystemExit("WP-L4 failed: " + ", ".join(failures))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: wp_l4_browser_test.py <site_artifact>")
    run(sys.argv[1])
