"""Optional local browser check. Requires Python Playwright and its Chromium.

Run: python scripts/verify_nextnudge_workspaces.py --output /path/to/evidence
Uses an isolated browser profile and local HTTP server. Imports the existing
public pilot thread as a fixture; no GitHub request is submitted or posted.
"""
import argparse
import functools
import http.server
import json
from pathlib import Path
import re
import threading
from playwright.sync_api import sync_playwright, expect


def run(output):
    root = Path(__file__).resolve().parents[1]
    fixture = root / 'site/nextnudge-data/threads/NN-20261019-165622-6810.md'
    moves = [json.loads(x) for x in re.findall(r'<!-- nn3:move\n([^\n]+)\n-->', fixture.read_text(encoding='utf-8'))]
    reply = next(x for x in reversed(moves) if x['kind'] == 'reply')
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(root / 'site'))
    server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    output.mkdir(parents=True, exist_ok=True)
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            context = browser.new_context(viewport={'width': 1280, 'height': 900})
            page = context.new_page()
            page.route('https://api.github.com/**', lambda route: route.abort())
            page.goto(f'http://127.0.0.1:{server.server_port}/nextnudge/index.html')
            page.locator('#import-file').set_input_files(str(fixture))
            page.locator('[data-action="workspace-ground"]').click()
            page.locator('[name="brief"]').fill('Browser fixture context; no external delivery')
            page.locator('[name="issue"]').fill('https://github.com/reallakshman19/CoordinatorLandingpage/issues/110')
            page.get_by_role('button', name='Save Ground context', exact=True).click()
            expect(page.locator('#workspace-status')).to_contain_text('Saved ground locally')
            expect(page.locator('.source-links a').first).to_be_visible()
            page.screenshot(path=str(output / '01-ground.png'), full_page=True)

            page.locator('[data-action="workspace-task"]').click()
            version = page.locator('[name="groundId"] option').nth(1).get_attribute('value')
            page.locator('[name="groundId"]').select_option(version)
            page.locator('[name="task"]').fill('Inspect only this preview fixture')
            page.locator('[name="deliverable"]').fill('A fixture-only result')
            page.locator('[name="success"]').fill('Original source and result are identified')
            page.get_by_role('button', name='Save Task', exact=True).click()
            page.locator('[data-action="workspace-build"]').click()
            expect(page.locator('#packet')).to_contain_text(version)
            page.locator('#packet').fill(page.locator('#packet').input_value() + '\nManual preview note')
            page.locator('[data-action="workspace-ground"]').click()
            expect(page.locator('[name="brief"]')).to_have_value('Browser fixture context; no external delivery')
            page.locator('[data-action="workspace-task"]').click()
            expect(page.locator('#packet')).to_contain_text('Manual preview note')
            page.reload()
            expect(page.locator('[name="task"]')).to_have_value('Inspect only this preview fixture')
            expect(page.locator('#packet')).to_contain_text('Manual preview note')
            page.screenshot(path=str(output / '02-task.png'), full_page=True)

            page.locator('[data-action="workspace-correction"]').click()
            page.locator('[name="target"]').select_option(reply['id'])
            for key, value in {'claim': 'Preview issue', 'expected': 'Original sources retained', 'redo': 'Fixture comparison only'}.items():
                page.locator(f'[name="{key}"]').fill(value)
            page.get_by_role('button', name='Save Correction', exact=True).click()
            page.locator('[data-action="workspace-build"]').click()
            expect(page.locator('#packet')).to_contain_text(reply['id'])
            page.screenshot(path=str(output / '03-correction.png'), full_page=True)

            page.locator('[data-action="workspace-reconcile"]').click()
            page.locator('[name="target"]').select_option(reply['id'])
            page.locator('[name="check0"]').select_option('met')
            page.locator('[name="nextTask"]').fill('Return evidence for remaining checks')
            page.locator('[name="gap"]').fill('Remaining checks are not yet verified in this fixture')
            page.get_by_role('button', name='Save Review', exact=True).click()
            page.reload()
            expect(page.locator('[name="check0"]')).to_have_value('met')
            page.locator('[name="decision"]').select_option('close')
            page.locator('[data-action="workspace-build"]').click()
            expect(page.locator('#notice')).to_contain_text('cannot close')
            page.locator('[name="decision"]').select_option('request evidence')
            page.screenshot(path=str(output / '04-reconcile.png'), full_page=True)
            page.set_viewport_size({'width': 390, 'height': 844})
            assert page.locator('body').evaluate('(el) => el.scrollWidth <= innerWidth'), 'Horizontal overflow'
            page.screenshot(path=str(output / '05-mobile-review.png'), full_page=True)
            browser.close()
            print('PASS: four distinct workspaces, saves, exact source links, packet recovery and guarded closure')
    finally:
        server.shutdown()
        server.server_close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    run(parser.parse_args().output)
