#!/usr/bin/env python3
"""WP2 visible page behavioural qualification, preserving original 19 checks.

Usage: python tests/wp2_browser_test.py <benchmark-artifact-dir>
The test copies the already-built benchmark artifact to a temporary HTTP
directory and overlays a synthetic F5 projection and liveness states.
No live GitHub API, protected action, publication or production data mutation.
"""
import json
import shutil
import sys
import tempfile
from pathlib import Path

from browser_smoke_test import find_free_port, start_server

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build_data


def prepare(artifact, destination):
    shutil.copytree(artifact, destination, dirs_exist_ok=True)
    data = destination / "data"
    data.mkdir(exist_ok=True)
    projects = json.loads((data / "projects.json").read_text())
    assert len(projects) >= 2, "benchmark artifact needs two real project entries"
    for p in projects:
        p["control"] = dict(p.get("control") or {}, hold=None)
        p["freshness_status"] = "STALE"
        p["last_cycle_at"] = "2026-10-15T10:00:00+00:00"
        p["source_health"] = {"status": "ok", "errors": []}
        # Preserve real benchmark decision links for the Answer route test.
        p["is_benchmark"] = False
    (data / "projects.json").write_text(json.dumps(projects))
    fixture = json.loads((ROOT / "tests/fixtures/f5_owner_input_history.json").read_text())
    projection = build_data.build_owner_inputs(fixture["issues"], fixture["capture"])
    assert len(projection) == 15
    (data / "owner-inputs.json").write_text(json.dumps(projection))
    return projects


def _proto_version(artifact):
    """Protocol version from the served source header (fail-closed: None)."""
    import re as _re
    from pathlib import Path as _P
    try:
        md = (_P(artifact) / "protocol" / "TEAM_PROTOCOL.md").read_text(encoding="utf-8")
    except OSError:
        return None
    m = _re.search(r"^#\s+Team protocol\s+(v\d+(?:\.\d+)+)", md, _re.M | _re.I)
    return m.group(1) if m else None

def main():
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python tests/wp2_browser_test.py <artifact-dir>")
    artifact = Path(sys.argv[1]).resolve()
    if not artifact.is_dir():
        raise SystemExit("Missing pre-built artifact directory")
    from playwright.sync_api import sync_playwright

    failures, errors, passed = [], [], []
    def check(name, condition):
        try:
            ok = bool(condition())
        except Exception as exc:
            errors.append((name, type(exc).__name__))
            ok = False
        if ok:
            passed.append(name)
            print("PASS", name)
        else:
            failures.append(name)
            print("FAIL", name)

    def txt(page, selector):
        match = page.locator(selector)
        return match.first.inner_text(timeout=1500) if match.count() else ""

    with tempfile.TemporaryDirectory() as temp:
        directory = Path(temp) / "artifact"
        prepare(artifact, directory)
        port = find_free_port()
        srv = start_server(str(directory), port)
        url = "http://127.0.0.1:" + str(port) + "/index.html"
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page(viewport={"width": 1100, "height": 900})

                def goto(route):
                    page.goto(url + "#" + route, wait_until="networkidle", timeout=15000)
                    page.wait_for_timeout(250)

                goto("home")
                home = txt(page, "#needs-you")
                table = txt(page, "#projects-tbody")
                strip = txt(page, "#liveness-strip")
                check("WP2_01_home_owner_input_closed_pending",
                      lambda: "Owner input #205" in home and "OPEN" in home)
                check("WP2_02_home_clarification_is_pending",
                      lambda: "Owner input #206" in home and "NEEDS_CLARIFICATION" in home)
                check("WP2_03_home_protected_unverified",
                      lambda: "Owner input #208" in home and "UNVERIFIED" in home)
                check("WP2_04_no_unconditional_running",
                      lambda: "STALE" in table and "▶ running" not in table)
                check("WP2_05_source_last_cycle_visible",
                      lambda: "15/10/2026" in table and "14:00" in table)
                check("WP2_06_liveness_strip_observed_state",
                      lambda: "STALE" in strip and
                      "UNKNOWN (no independent observation)" in strip)

                goto("owner-inputs")
                row206 = txt(page, '.oi-row[data-issue="206"]')
                row204 = page.locator('.oi-row[data-issue="204"] a.oi-receipt')
                row208 = txt(page, '.oi-row[data-issue="208"]')
                check("WP2_07_reopen_clarification_label",
                      lambda: "NEEDS_CLARIFICATION" in row206 and "pending" in row206)
                check("WP2_08_exact_receipt_clickthrough",
                      lambda: row204.count() == 1 and row204.get_attribute("href") ==
                      "https://github.com/reallakshman19/CoordinatorLandingpage/"
                      "issues/204#issuecomment-20401")
                check("WP2_09_protected_no_action",
                      lambda: "UNVERIFIED" in row208 and "no action authorized" in row208)
                check("WP2_10_closed_without_receipt_not_green",
                      lambda: "OPEN" in txt(page, '.oi-row[data-issue="205"]') and
                      page.locator('.oi-row[data-issue="205"] a.oi-receipt').count() == 0)
                check("WP2_11_new_issue_form_link",
                      lambda: page.locator("#new-input-btn").get_attribute("href").startswith(
                          "https://github.com/reallakshman19/CoordinatorLandingpage/"
                          "issues/new?template=owner-input.yml"))

                goto("protocol")
                check("WP2_12_protocol_source_label",
                      lambda: bool(_proto_version(sys.argv[1])) and _proto_version(sys.argv[1]) in txt(page, "#protocol-label") and
                      "v2.1" not in txt(page, "#protocol-label"))

                # Existing eight hash routes still point to their original templates.
                routes = [
                    ("home", "#needs-you"), ("project/imo-ab-test", "#view-project"),
                    ("agent/imo-ab-test/6ad0449d", "#view-agent"),
                    ("timeline/imo-ab-test", "#view-timeline"),
                    ("decision/grade9-pilot/G9-DIFF-13", "#view-decision"),
                    ("owner-inputs", "#view-owner-inputs"),
                    ("protocol", "#view-protocol"), ("benchmarks", "#view-benchmarks"),
                ]
                for route, selector in routes:
                    goto(route)
                    check("ROUTE_" + route.replace("/", "_"),
                          lambda selector=selector: page.locator(selector).count() == 1)

                goto("agent/imo-ab-test/6ad0449d")
                check("FORMS_ground_and_suggest",
                      lambda: all(
                          page.locator(sel).get_attribute("href").startswith(
                              "https://github.com/reallakshman19/CoordinatorLandingpage/issues/new?")
                          for sel in ("#btn-ground", "#btn-suggest")))
                goto("project/imo-ab-test")
                check("FORMS_post_to_team",
                      lambda: page.locator("#post-btn").get_attribute("href").startswith(
                          "https://github.com/reallakshman19/CoordinatorLandingpage/issues/new?"))
                goto("decision/grade9-pilot/G9-DIFF-13")
                check("FORMS_answer",
                      lambda: page.locator("#dc-answer-btn").get_attribute("href").startswith(
                          "https://github.com/reallakshman19/CoordinatorLandingpage/issues/new?"))

                for scheme in ("light", "dark"):
                    ctx = browser.new_context(viewport={"width": 390, "height": 844},
                                              color_scheme=scheme)
                    mobile = ctx.new_page()
                    mobile.goto(url + "#owner-inputs", wait_until="networkidle", timeout=15000)
                    mobile.wait_for_timeout(300)
                    check("MOBILE_" + scheme + "_rows_and_390px",
                          lambda: mobile.locator('.oi-row[data-issue="208"]').count() == 1 and
                          mobile.evaluate("document.documentElement.scrollWidth <= window.innerWidth + 2"))
                    mobile.goto(url + "#home", wait_until="networkidle", timeout=15000)
                    mobile.wait_for_timeout(300)
                    check("MOBILE_" + scheme + "_freshness",
                          lambda: "STALE" in txt(mobile, "#projects-tbody"))
                    ctx.close()
                browser.close()
        finally:
            srv.shutdown()
    print("WP2_BROWSER_COUNTS pass=" + str(len(passed)) +
          " fail=" + str(len(failures)) + " error=" + str(len(errors)))
    print("WP2_BROWSER_FAILED_NAMES " + ",".join(failures))
    print("WP2_BROWSER_ERROR_NAMES " + ",".join(n for n, _ in errors))
    if failures or errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
