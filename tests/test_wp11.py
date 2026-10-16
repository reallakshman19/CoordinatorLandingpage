#!/usr/bin/env python3
"""WP11 C10: real registered external projects, exact repository scoping, collisions."""
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build_data
import fetch_live_data

CII = "cii-method-c"
XML = "xml229-output"
CII_REPO = "reallakshman19/XML_Compare_Utilities"
XML_REPO = "reallakshman19/3D_Converters"
HUB = "reallakshman19/CoordinatorLandingpage"
NOW = datetime(2026, 10, 16, 14, 0, tzinfo=timezone.utc)


def actual_registry(project):
    # Read actual registered source files, not a synthetic stand-in.
    return json.loads((ROOT / "logs" / project / "registry.json")
                      .read_text(encoding="utf-8"))


def projection(project, registry):
    return build_data.build_project_data(
        ROOT, project, registry, {}, [], None,
        source_meta={"status": "ok", "errors": []},
        status_thread={}, now=NOW, registry_blob_sha="f" * 40)[0]


class WP11ActualRegistry(unittest.TestCase):
    def test_wp11_cii_real_registry_has_own_evidence_links(self):
        reg = actual_registry(CII)
        self.assertEqual(reg["repository"], CII_REPO)
        self.assertEqual(len(reg["agents"]), 2)
        data = projection(CII, reg)
        self.assertEqual(data["freshness_status"], "HOLD")
        self.assertEqual([a["status"] for a in data["agents"]], ["hold", "hold"])
        self.assertEqual(data["auto_response"][0]["allowed"], "critical")
        self.assertEqual(data["auto_response"][0]["until"], "forever")
        self.assertEqual(data["auto_response"][0]["state"], "IN_SCOPE")
        self.assertIn("Not authorised for auto response",
                      data["auto_response"][0]["owner_words"])
        self.assertEqual([x["url"] for x in data["external_links"]],
                         [f"https://github.com/{CII_REPO}/issues/108"])
        self.assertEqual([a.get("evidence_thread_url") for a in data["agents"]],
                         [f"https://github.com/{CII_REPO}/issues/106",
                          f"https://github.com/{CII_REPO}/issues/108"])

    def test_wp11_xml_real_registry_has_own_evidence_links(self):
        reg = actual_registry(XML)
        self.assertEqual(reg["repository"], XML_REPO)
        self.assertEqual(len(reg["agents"]), 1)
        data = projection(XML, reg)
        self.assertEqual(data["freshness_status"], "HOLD")
        self.assertEqual(data["agents"][0]["status"], "hold")
        self.assertEqual(data["agents"][0]["generation"], 2)
        self.assertEqual(data["auto_response"][0]["allowed"], "critical")
        self.assertEqual(data["auto_response"][0]["until"], "forever")
        self.assertIn("Not authorised for auto response",
                      data["auto_response"][0]["owner_words"])
        self.assertEqual([x["url"] for x in data["external_links"]],
                         [f"https://github.com/{XML_REPO}/issues/274"])
        self.assertEqual(data["agents"][0].get("evidence_thread_url"),
                         f"https://github.com/{XML_REPO}/issues/274")

    def test_wp11_cross_repository_source_cannot_become_agent_link(self):
        reg = actual_registry(CII)
        reg["agents"][0]["evidence_thread"] = (
            f"https://github.com/{XML_REPO}/issues/106")
        data = projection(CII, reg)
        self.assertIsNone(data["agents"][0].get("evidence_thread_url"))
        self.assertTrue(all(x["url"].startswith(f"https://github.com/{CII_REPO}/")
                            for x in data["external_links"]))

    def test_wp11_live_data_same_issue_number_is_scoped_by_repository(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for project in (CII, XML):
                p = root / "logs" / project / "registry.json"
                p.parent.mkdir(parents=True)
                p.write_text(json.dumps(actual_registry(project)), encoding="utf-8")
            # Collision ONLY in a transient test registry: #106 in 3D_Converters
            # must never be #106 in XML_Compare_Utilities, or hub #106.
            xml_path = root / "logs" / XML / "registry.json"
            xml_reg = json.loads(xml_path.read_text(encoding="utf-8"))
            xml_reg["agents"].append({
                "alias": "Collision sentinel", "role": "checker",
                "chat_id8": "0badc0de", "generation": 1, "status": "hold",
                "evidence_thread": f"https://github.com/{XML_REPO}/issues/106",
            })
            xml_path.write_text(json.dumps(xml_reg), encoding="utf-8")

            seen = []
            def fake_issue(product, number):
                seen.append((product, number))
                chat = ({(CII_REPO, 106): "6ad1ce42",
                         (CII_REPO, 108): "6ad1fa79",
                         (XML_REPO, 274): "6ad1cc04",
                         (XML_REPO, 106): "0badc0de"}).get((product, number))
                project = CII if product == CII_REPO else XML
                token = product.split("/")[-1] + "-ONLY"
                body = (f"TASK EVIDENCE v2 · {project} · implementer · "
                        f"chat {chat} · #1 · 16 Oct 17:00 +04:00\n"
                        f"Task: {token}\nStatus: DONE") if chat else ""
                return {"number": number, "repository": product,
                        "comments": [{"id": number, "created_at":
                                      "2026-10-16T13:00:00Z", "body": body,
                                      "author_association": "MEMBER"}]}

            cache = root / "cache"
            with mock.patch.object(fetch_live_data, "fetch_issue",
                                   side_effect=fake_issue), \
                 mock.patch.object(fetch_live_data, "fetch_bounded_owner_index",
                                   return_value=[]), \
                 mock.patch.object(fetch_live_data, "gh_api",
                                   side_effect=lambda path:
                                   {"name": "owner-input"} if
                                   path.endswith("/labels/owner-input") else []), \
                 mock.patch.object(sys, "argv", [
                     "fetch_live_data.py", "--root", str(root),
                     "--repo", HUB, "--cache-dir", str(cache)]), \
                 mock.patch.dict(os.environ, {"GITHUB_SHA": "a" * 40}):
                fetch_live_data.main()

            self.assertEqual(set(seen), {(HUB, 1), (CII_REPO, 106),
                                         (CII_REPO, 108), (XML_REPO, 274),
                                         (XML_REPO, 106)})
            manifest = json.loads((cache / "capture-info.json").read_text())
            self.assertEqual(manifest["status"], "ok")
            self.assertIn(f"{CII_REPO}#106", manifest["fetched_sources"])
            self.assertIn(f"{XML_REPO}#106", manifest["fetched_sources"])
            scoped_cii = json.loads((cache / "project-threads" / CII /
                                     "issue-106.json").read_text())
            scoped_xml = json.loads((cache / "project-threads" / XML /
                                     "issue-106.json").read_text())
            self.assertEqual(scoped_cii["repository"], CII_REPO)
            self.assertEqual(scoped_xml["repository"], XML_REPO)
            self.assertNotEqual(scoped_cii["comments"][0]["body"],
                                scoped_xml["comments"][0]["body"])
            build_data.build_all(root, root / "site-data", cache_dir=cache)
            for project, chat, other_repo in [
                (CII, "6ad1ce42", XML_REPO),
                (XML, "0badc0de", CII_REPO),
            ]:
                data = json.loads((root / "site-data" /
                                   f"evidence-{project}-{chat}.json").read_text())
                raw = json.dumps(data["agent"]["evidence"])
                self.assertIn(("XML_Compare_Utilities" if project == CII
                               else "3D_Converters") + "-ONLY", raw)
                self.assertNotIn(other_repo.split("/")[-1] + "-ONLY", raw)
            summary = json.loads((root / "site-data" / "projects.json").read_text())
            self.assertEqual({p["project"] for p in summary}, {CII, XML})
            for project in summary:
                own = CII_REPO if project["project"] == CII else XML_REPO
                # Baseline scoping must stand on its own; HEAD adds source URLs.
                if "evidence_thread_url" in project["agents"][0]:
                    self.assertTrue(all(a["evidence_thread_url"].startswith(
                        f"https://github.com/{own}/") for a in project["agents"]))


if __name__ == "__main__":
    unittest.main(verbosity=2)
