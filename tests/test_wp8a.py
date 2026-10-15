#!/usr/bin/env python3
"""WP8a: the published HTML and build-info must identify the same code version.

Four BaseCompatible checks run against the prior publisher without new APIs.
All four must FAIL assertions on BASE, then PASS on this branch.
"""
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import publish_site
from tests.test_wp4 import PublisherGateTests


class BaseCompatibleWP8a(unittest.TestCase):
    def setUp(self):
        helper = PublisherGateTests("test_wp4_stamp_and_deployed_readback_hash")
        helper.setUp()
        self.addCleanup(helper.doCleanups)
        self.helper = helper
        self.artifact, _ = helper.make_artifact()
        self.source = helper.sha
        self.info = publish_site.stamp(
            self.artifact, helper.root / "logs", helper.cache,
            helper.repo, self.source, "874321")
        self.document = (self.artifact / "index.html").read_text()

    def test_wp8a_stamped_javascript_and_stylesheet_urls(self):
        sha8 = self.source[:8]
        self.assertIn('src="app.js?v=' + sha8 + '"', self.document)
        self.assertIn('href="style.css?v=' + sha8 + '"', self.document)
        self.assertNotIn('src="app.js"', self.document)
        self.assertNotIn('href="style.css"', self.document)

    def test_wp8a_build_info_has_matching_site_version(self):
        stored = json.loads((self.artifact / "build-info.json").read_text())
        self.assertEqual(self.info.get("site_version"), self.source[:8])
        self.assertEqual(stored.get("site_version"), self.source[:8])

    def test_wp8a_html_exposes_loaded_version_to_running_page(self):
        self.assertIn(
            '<meta name="site-version" content="' + self.source[:8] + '">',
            self.document)
        self.assertEqual(self.document.count('name="site-version"'), 1)

    def test_wp8a_readback_rejects_invalid_version(self):
        path = self.artifact / "build-info.json"
        record = json.loads(path.read_text())
        record["site_version"] = "ffffffff"
        path.write_text(json.dumps(record))
        with self.assertRaisesRegex(ValueError, "site version mismatch"):
            publish_site.verify_readback_bytes(
                path, path.read_bytes(), self.source)


class ExtraWP8a(unittest.TestCase):
    def test_wp8a_source_template_unversioned_until_publisher_runs(self):
        template = (ROOT / "site/index.html").read_text()
        self.assertIn('src="app.js"', template)
        self.assertIn('href="style.css"', template)
        self.assertIn('id="site-update-banner"', template)
        self.assertNotIn('src="app.js?v=', template)


if __name__ == "__main__":
    unittest.main(verbosity=2)
