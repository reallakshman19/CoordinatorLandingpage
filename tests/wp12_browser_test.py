#!/usr/bin/env python3
"""WP12 browser: offline registered products, synthetic source observations; N2 read-only RED."""
import json
from pathlib import Path
import shutil
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build_data
from browser_smoke_test import find_free_port, start_server

CII = "cii-method-c"
XML = "xml229-output"
PRODUCT = "reallakshman19/XML_Compare_Utilities"
CHILD = f"https://github.com/{PRODUCT}/issues/201"
PULL = f"https://github.com/{PRODUCT}/pull/106"


def main():
    from playwright.sync_api import sync_playwright
    if len(sys.argv) not in (2,3):
        raise SystemExit("usage: python tests/wp12_browser_test.py <artifact> [--readonly-only]")
    readonly_only = len(sys.argv) == 3 and sys.argv[2] == "--readonly-only"
    if len(sys.argv) == 3 and not readonly_only:
        raise SystemExit("unknown option")
    passes, failures, errors = [], [], []
    def check(name, fn):
        try:
            yes = bool(fn())
        except Exception as error:
            yes = False
            errors.append(name + ":" + type(error).__name__)
        (passes if yes else failures).append(name)
        print(("PASS " if yes else "FAIL ") + name)

    with tempfile.TemporaryDirectory() as temp:
        tmp = Path(temp)
        site = tmp / "site"
        source = tmp / "sources"
        shutil.copytree(Path(sys.argv[1]).resolve(), site)
        for project in (CII, XML):
            registry = ROOT / "logs" / project / "registry.json"
            dest = source / "logs" / project / "registry.json"
            dest.parent.mkdir(parents=True, exist_ok=True)
            src = json.loads(registry.read_text())
            if project == CII:
                src["control"]["hold"] = {
                    "since": "2026-10-16T18:03:00+04:00",
                    "owner_words": "Pause until Owner says continue."
                }
                src["children"] = [CHILD]
                src["evidence_head"] = "a" * 40
                src["evidence_pr"] = PULL
            dest.write_text(json.dumps(src))
        extra = source / "cache" / "project-extras" / CII
        extra.mkdir(parents=True)
        (extra / "children.json").write_text(json.dumps([{
            "url": CHILD, "repository": PRODUCT,
            "title": "[V3.6][O1][DONE] Verify Method C",
        }]))
        (extra / "pr-head.json").write_text(json.dumps({
            "url": PULL, "repository": PRODUCT, "head": "b" * 40
        }))
        build_data.build_all(source, site / "data", cache_dir=source / "cache")
        evidence = site / "data" / "evidence-cii-method-c-6ad1ce42.json"
        content = json.loads(evidence.read_text())
        content["agent"]["evidence"] = [
            {"type":"evidence","seq":1,"task":"Local test","status":"DONE",
             "ts":"2026-10-16T14:00:00Z",
             "proofs":[{"line":"[LOCAL] 6 checks passed","grade":"LOCAL"}]},
            {"type":"evidence","seq":2,"task":"Hosted claim","status":"DONE",
             "ts":"2026-10-16T14:01:00Z",
             "proofs":[{"line":"[CI] https://github.com/reallakshman19/CoordinatorLandingpage/actions/runs/123",
                        "grade":"CI"}]},
        ]
        evidence.write_text(json.dumps(content))
        # Existing agent route still reads the legacy unscoped evidence-id8 file;
        # verify both published forms carry the same project-checked fixture.
        (site / "data" / "evidence-6ad1ce42.json").write_text(json.dumps(content))
        server = start_server(str(site), find_free_port())
        try:
            with sync_playwright() as pw:
                browser = pw.chromium.launch(headless=True)
                page = browser.new_page(viewport={"width":1180,"height":950})
                url = f"http://127.0.0.1:{server.server_address[1]}/index.html"
                def visit(route, ready):
                    page.goto(url + route, wait_until="networkidle")
                    page.locator(ready).first.wait_for(state="attached",timeout=9000)

                visit("#project/cii-method-c", "#agents-tbody tr")
                check("WP12_N2_01_external_project_no_post_action",
                      lambda: not page.locator("#post-btn").is_visible())
                check("WP12_N2_02_agent_link_matches_product_not_hub",
                      lambda: page.locator(".agent-evidence-thread").count() == 2
                      and page.locator(".agent-evidence-thread").first.get_attribute(
                          "href") == f"https://github.com/{PRODUCT}/issues/106")
                visit("#agent/cii-method-c/6ad1ce42", "#agent-action-buttons")
                check("WP12_N2_03_external_agent_no_ground_suggest",
                      lambda: not page.locator("#agent-action-buttons").is_visible())
                visit("#owner-inputs", "#oi-json-project")
                check("WP12_N2_04_external_projects_not_writable",
                      lambda: CII not in page.locator("#oi-json-project").inner_text()
                      and XML not in page.locator("#oi-json-project").inner_text())
                if not readonly_only:
                    visit("#project/cii-method-c", "#agents-tbody tr")
                    check("WP12_UI_01_hold_words_and_exact_since",
                          lambda: "Pause until Owner says continue." in page.locator(
                              "#wp12-project-hold").inner_text()
                          and "2026-10-16T18:03:00+04:00" in page.locator(
                              "#wp12-project-hold").inner_text())
                    check("WP12_UI_02_reporting_lines_small_tree",
                          lambda: "MemberCoordinator" in page.locator(
                              "#wp12-reporting-tree").inner_text()
                          and "Method C worker" in page.locator(
                              "#wp12-reporting-tree ul ul").inner_text()
                          and page.locator("#wp12-reporting-tree ul ul").count() == 1)
                    check("WP12_UI_03_child_progress_one_of_one_own_repo",
                          lambda: "1/1 DONE" in page.locator(
                              "#wp12-child-progress").inner_text()
                          and page.locator(".wp12-child-link").first.get_attribute(
                              "href") == CHILD)
                    check("WP12_UI_04_moved_pr_head_superseded",
                          lambda: "evidence superseded (head moved)" in page.locator(
                              "#wp12-head-status").inner_text()
                          and page.locator(".wp12-head-pr-link").get_attribute(
                              "href") == PULL)
                    visit("#project/xml229-output", "#agents-tbody tr")
                    check("WP12_UI_05_real_hold_no_invented_since",
                          lambda: "HOLD" in page.locator(
                              "#wp12-project-hold").inner_text()
                          and "Since: not recorded" in page.locator(
                              "#wp12-project-hold").inner_text()
                          and "No v3.6 child issues registered." in page.locator(
                              "#wp12-child-progress").inner_text()
                          and page.locator(".wp12-head-pr-link").count() == 0)
                    visit("#agent/cii-method-c/6ad1ce42", ".evidence-row")
                    check("WP12_UI_06_agent_hold_banner",
                          lambda: "HOLD" in page.locator(
                              "#wp12-agent-hold").inner_text())
                    check("WP12_UI_07_local_vs_hosted_ci_link",
                          lambda: page.locator(".wp12-evidence-hosting").all_inner_texts()
                              == ["local only","hosted CI link claimed"])
                browser.close()
        finally:
            server.shutdown()
    tag = "WP12_READONLY" if readonly_only else "WP12_BROWSER"
    print(f"{tag}_COUNTS pass={len(passes)} fail={len(failures)} error={len(errors)}")
    if failures: print(f"{tag}_FAILED_NAMES " + ",".join(failures))
    if errors: print(f"{tag}_ERROR_NAMES " + ",".join(errors))
    if errors or failures: raise SystemExit(1)


if __name__ == "__main__":
    main()
