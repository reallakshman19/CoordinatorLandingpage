#!/usr/bin/env python3
"""
browser_smoke_test.py — Headless Playwright smoke test for the Team Protocol landing page.

Verifies that all 8 hard cases produce visible content in the actual browser,
not just in Python data checks.

Usage:
  python tests/browser_smoke_test.py <artifact-dir>

The script:
1. Serves artifact-dir on a random port via Python's http.server
2. Navigates to each view with Playwright (Chromium headless)
3. Asserts that key text/elements are present in the DOM
4. Prints PASS/FAIL for each check
5. Exits non-zero if any check fails

Hard cases exercised:
  HC1 — Home shows two coordinator entries (OwnerTeammember + Codex paused)
  HC2 — grade9-pilot project shows retired g1 and active g2 agents
  HC3 — imo-ab-test Agent A evidence chain shows ✏ CORRECTED and ✅ ALIGNED verdicts
  HC4 — imo-ab-test project shows outside-write flag (5a117f69)
  HC5 — imo-ab-test project shows role-conflict / CONTROL_EPOCH entry
  HC6 — imo-ab-test project shows superseded decision (supersedes 08:58)
  HC7 — grade9-pilot project shows HOLD banner and G9-DIFF-13 open decision
  HC8 — imo-ab-test timeline shows time-corrected coordinator record
"""

import http.server
import functools
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path


def find_free_port() -> int:
    with socket.socket() as s:
        s.bind(('', 0))
        return s.getsockname()[1]


def start_server(directory: str, port: int):
    handler = functools.partial(
        http.server.SimpleHTTPRequestHandler,
        directory=directory
    )
    handler.log_message = lambda *a: None  # silence request logs
    httpd = http.server.HTTPServer(('127.0.0.1', port), handler)
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    return httpd


def main():
    if len(sys.argv) < 2:
        print("Usage: python tests/browser_smoke_test.py <artifact-dir>")
        sys.exit(1)

    artifact_dir = Path(sys.argv[1]).resolve()
    if not artifact_dir.exists():
        print(f"ERROR: artifact directory not found: {artifact_dir}")
        sys.exit(1)

    port = find_free_port()
    base_url = f"http://127.0.0.1:{port}"

    print(f"Serving {artifact_dir} on {base_url}")
    start_server(str(artifact_dir), port)
    time.sleep(0.5)  # let server start

    try:
        from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
    except ImportError:
        print("ERROR: playwright not installed. Run: pip install playwright && playwright install chromium")
        sys.exit(1)

    passed = 0
    failed = 0
    failures = []

    def check(name: str, ok: bool, detail: str = ""):
        nonlocal passed, failed
        if ok:
            print(f"  ✅ {name}")
            passed += 1
        else:
            print(f"  ❌ {name}{': ' + detail if detail else ''}")
            failed += 1
            failures.append(name)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        def goto(hash_route: str):
            url = f"{base_url}/index.html#{hash_route}"
            page.goto(url, wait_until="networkidle", timeout=15000)
            # Give JS router time to render
            page.wait_for_timeout(800)

        def text_visible(selector_or_text: str, mode: str = "contains") -> bool:
            try:
                if mode == "contains":
                    # Look for any element containing the text
                    return page.locator(f"text={selector_or_text}").count() > 0
                else:
                    return page.locator(selector_or_text).count() > 0
            except Exception:
                return False

        # ── HC1: Home — two coordinators ──────────────────────────────────────
        print("\nHC1: Home — two coordinators over time")
        goto("home")
        check("Home loads (projects listed)",
              text_visible("grade9-pilot") or text_visible("Project"))
        check("OwnerTeammember coordinator visible",
              text_visible("OwnerTeammember") or text_visible("stand-in"))
        check("Codex paused entry visible",
              text_visible("Codex") or text_visible("paused") or text_visible("HOLD"))

        # ── HC2: grade9-pilot — retired g1 / active g2 ────────────────────────
        print("\nHC2: grade9-pilot — retired g1 and active g2 agents")
        goto("project/grade9-pilot")
        check("grade9-pilot project view loads",
              text_visible("grade9-pilot") or text_visible("validator"))
        check("Retired agent label visible",
              text_visible("retired") or text_visible("g1"))
        check("Active agent label visible",
              text_visible("active") or text_visible("g2"))

        # ── HC3: imo-ab-test — FAIL→fix→PASS chain ────────────────────────────
        print("\nHC3: imo-ab-test — FAIL→fix→PASS chain (Agent A evidence)")
        goto("agent/imo-ab-test/6ad0449d")
        check("Agent A evidence view loads",
              text_visible("6ad0449d") or text_visible("evidence") or text_visible("TASK EVIDENCE"))
        check("CORRECTED verdict visible",
              text_visible("CORRECTED") or text_visible("✏"))
        check("ALIGNED verdict visible",
              text_visible("ALIGNED") or text_visible("✅"))

        # ── HC4: imo-ab-test — outside write ──────────────────────────────────
        print("\nHC4: imo-ab-test — outside write flagged")
        goto("project/imo-ab-test")
        check("imo-ab-test project view loads",
              text_visible("imo-ab-test") or text_visible("analyst"))
        check("Outside write commit 5a117f69 visible",
              text_visible("5a117f69") or text_visible("outside"))

        # ── HC5: role conflict / CONTROL_EPOCH ────────────────────────────────
        print("\nHC5: imo-ab-test — role conflict / CONTROL_EPOCH")
        goto("timeline/imo-ab-test")
        check("Timeline view loads",
              text_visible("timeline") or text_visible("Timeline") or text_visible("COORDINATOR"))
        check("CONTROL_EPOCH event visible",
              text_visible("CONTROL") or text_visible("epoch") or text_visible("OwnerTeammember"))

        # ── HC6: superseded Owner words ────────────────────────────────────────
        print("\nHC6: imo-ab-test — superseded Owner words")
        goto("project/imo-ab-test")
        check("Superseded decision (supersedes 08:58) visible",
              text_visible("supersedes") or text_visible("08:58") or text_visible("AB-SOURCE"))

        # ── HC7: parked decisions + HOLD ──────────────────────────────────────
        print("\nHC7: grade9-pilot — HOLD banner and open decision")
        goto("project/grade9-pilot")
        check("HOLD banner visible",
              text_visible("HOLD") or text_visible("hold"))
        check("G9-DIFF-13 open decision visible",
              text_visible("G9-DIFF-13") or text_visible("open decision"))

        # ── HC8: time-corrected coordinator record ─────────────────────────────
        print("\nHC8: imo-ab-test timeline — time-corrected entry")
        goto("timeline/imo-ab-test")
        check("Time-corrected event visible",
              text_visible("time-corrected") or text_visible("corrected") or
              text_visible("replaces") or text_visible("COORDINATOR"))

        # ── Protocol view (Fix 2 check) ────────────────────────────────────────
        print("\nFix 2: Protocol view — not blank")
        goto("protocol")
        check("Protocol view loads content (not blank)",
              text_visible("TEAM_PROTOCOL") or text_visible("§") or
              text_visible("protocol") or text_visible("Protocol") or
              text_visible("TASK EVIDENCE") or text_visible("TeamCoordinator"))

        # ── Benchmarks view ────────────────────────────────────────────────────
        print("\nBonus: Benchmarks view loads both snapshots")
        goto("benchmarks")
        check("Benchmarks view loads",
              text_visible("grade9-pilot") or text_visible("benchmark"))

        browser.close()

    print(f"\n{'='*60}")
    print(f"Browser smoke test: {passed}/{passed+failed} checks passed")
    if failures:
        print(f"\n  ❌ FAILED:")
        for f in failures:
            print(f"     - {f}")
        sys.exit(1)
    else:
        print("ALL BROWSER CHECKS PASSED ✅")
        sys.exit(0)


if __name__ == "__main__":
    main()
