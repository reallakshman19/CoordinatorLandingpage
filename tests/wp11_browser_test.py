#!/usr/bin/env python3
"""WP11: actual registered C10 external-project UI from offline live registry build."""
import json
from pathlib import Path
import shutil
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build_data
from browser_smoke_test import start_server, find_free_port

CII = "cii-method-c"
XML = "xml229-output"
CII_REPO = "reallakshman19/XML_Compare_Utilities"
XML_REPO = "reallakshman19/3D_Converters"


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: python tests/wp11_browser_test.py <artifact>")
    from playwright.sync_api import sync_playwright
    passed, failed, errors = [], [], []

    def check(name, fn):
        try:
            ok = bool(fn())
        except Exception as error:
            ok = False
            errors.append(f"{name}={type(error).__name__}:{error}")
        (passed if ok else failed).append(name)
        print(("PASS " if ok else "FAIL ") + name)

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        site = tmp / "site"
        shutil.copytree(Path(sys.argv[1]).resolve(), site)
        source = tmp / "read-only-registries"
        for project in (CII, XML):
            dest = source / "logs" / project / "registry.json"
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / "logs" / project / "registry.json", dest)
        build_data.build_all(source, site / "data", cache_dir=source / "cache")
        projects = json.loads((site / "data" / "projects.json").read_text())
        assert {p["project"] for p in projects} == {CII, XML}
        # A tampered published dataset must never make another repo clickable.
        for p in projects:
            if p["project"] == CII:
                p["external_links"].append({
                    "kind": "PR", "url":
                    f"https://github.com/{XML_REPO}/pull/106", "read_only": True,
                })
        (site / "data" / "projects.json").write_text(json.dumps(projects))
        server = start_server(str(site), find_free_port())
        try:
            with sync_playwright() as pw:
                browser = pw.chromium.launch(headless=True)
                page = browser.new_page(viewport={"width": 1180, "height": 900})
                base = f"http://127.0.0.1:{server.server_address[1]}/index.html"

                def visit(hash_value, ready):
                    page.goto(base + hash_value, wait_until="networkidle")
                    page.locator(ready).first.wait_for(state="attached", timeout=9000)

                visit("#home", "#auto-response-home tbody tr")
                check("WP11_UI_01_two_registered_projects_only",
                      lambda: set(page.locator("#projects-tbody tr td:first-child")
                                  .all_inner_texts()) == {CII, XML})
                check("WP11_UI_02_both_critical_owner_words_and_hold",
                      lambda: page.locator("#auto-response-home .auto-response-allowed")
                        .all_inner_texts() == ["critical", "critical"]
                      and page.locator("#auto-response-home tbody tr").count() == 2
                      and page.locator("#auto-response-home").inner_text().count(
                          "Not authorised for auto response") == 2
                      and all("HOLD" in x for x in
                          page.locator(".coordinator-by-project").all_inner_texts())
                      and len(page.locator(".coordinator-by-project").all_inner_texts()) == 2)
                visit("#project/cii-method-c", ".external-project-repo")
                check("WP11_UI_03_cii_own_repo_issue_and_hold_generations",
                      lambda: page.locator(".external-project-repo").get_attribute("href") ==
                          f"https://github.com/{CII_REPO}"
                      and page.locator(".external-project-link").get_attribute("href") ==
                          f"https://github.com/{CII_REPO}/issues/108"
                      and len(page.locator("#agents-tbody .agent-state").all_inner_texts()) == 2
                      and all("hold" in s.lower() for s in
                          page.locator("#agents-tbody .agent-state").all_inner_texts())
                      and page.locator("#agents-tbody td:nth-child(2)").all_inner_texts() ==
                          ["g2", "g1"]
                      and page.locator("#auto-response-project .auto-response-allowed")
                          .inner_text() == "critical")
                check("WP11_UI_04_cii_issue_numbers_are_not_hub_urls",
                      lambda: set(page.locator(".agent-evidence-thread").evaluate_all(
                          "(a)=>a.map(x=>x.href)")) ==
                          {f"https://github.com/{CII_REPO}/issues/106",
                           f"https://github.com/{CII_REPO}/issues/108"}
                      and page.locator(".external-project-link").count() == 1
                      and not page.locator("#post-btn").is_visible())
                visit("#agent/cii-method-c/6ad1ce42", "#agent-action-buttons")
                check("WP11_UI_05_external_agent_has_no_hub_write_controls",
                      lambda: not page.locator("#agent-action-buttons").is_visible()
                      and "hold" in page.locator("#agent-badges").inner_text().lower())
                visit("#project/xml229-output", ".external-project-repo")
                check("WP11_UI_06_xml_own_repo_links_issue_274_hold",
                      lambda: page.locator(".external-project-repo").get_attribute("href") ==
                          f"https://github.com/{XML_REPO}"
                      and page.locator(".external-project-link").get_attribute("href") ==
                          f"https://github.com/{XML_REPO}/issues/274"
                      and page.locator(".agent-evidence-thread").get_attribute("href") ==
                          f"https://github.com/{XML_REPO}/issues/274"
                      and len(page.locator("#agents-tbody .agent-state").all_inner_texts()) == 1
                      and "hold" in page.locator("#agents-tbody .agent-state").inner_text().lower()
                      and page.locator("#auto-response-project .auto-response-allowed")
                          .inner_text() == "critical")
                check("WP11_UI_07_repositories_do_not_bleed_in_links",
                      lambda: (lambda urls: bool(urls) and
                          all(u.startswith(f"https://github.com/{XML_REPO}")
                              for u in urls))(page.locator(
                          ".external-project-links a, .agent-evidence-thread"
                          ).evaluate_all("(a)=>a.map(x=>x.href)"))
                      and page.locator("#agents-tbody tr").count() == 1
                      and not page.locator("#post-btn").is_visible())
                visit("#owner-inputs", "#oi-json-project")
                check("WP11_UI_08_no_external_project_input_options",
                      lambda: CII not in page.locator("#oi-json-project").inner_text()
                      and XML not in page.locator("#oi-json-project").inner_text())
                browser.close()
        finally:
            server.shutdown()
    print(f"WP11_BROWSER_COUNTS pass={len(passed)} fail={len(failed)} error={len(errors)}")
    if failed:
        print("WP11_BROWSER_FAILED_NAMES " + ",".join(failed))
    if errors:
        print("WP11_BROWSER_ERROR_NAMES " + ",".join(errors))
    if failed or errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
