#!/usr/bin/env python3
"""WP10: synthetic registry projection and authority/read-only regression controls."""
import json
from datetime import datetime, timezone
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build_data

NOW = datetime(2026, 10, 16, 10, 0, tzinfo=timezone.utc)
REPO = "reallakshman19/CoordinatorLandingpage"
PRODUCT = "example/3D_Converters"


def project(registry, events_path=None):
    return build_data.build_project_data(
        ROOT, "product-a", registry, {}, [], events_path,
        source_meta={"status": "ok", "errors": []},
        status_thread={}, now=NOW, registry_blob_sha="f" * 40
    )


class BaseCompatibleWP10(unittest.TestCase):
    """Four behaviour checks are expected to FAIL on the pinned old builder."""

    def test_wp10_expired_auto_response_and_critical_rules(self):
        registry = {"project": "product-a", "repository": PRODUCT,
                    "auto_response": {
                        "scope": "TeamCoordinator answers routine questions",
                        "allowed": "critical", "until": "2026-10-15T00:00:00Z",
                        "owner_words": "Critical questions require an explicit Owner decision.",
                    }}
        projected, _ = project(registry)
        response = projected.get("auto_response") or {}
        self.assertEqual(response.get("state"), "EXPIRED")
        self.assertEqual(response.get("allowed"), "critical")
        self.assertIn("Critical questions", response.get("critical_rules", ""))

    def test_wp10_agent_standby_hold_and_chat_end_risk(self):
        registry = {"project": "product-a", "repository": PRODUCT, "agents": [
            {"role": "implementer", "chat_id8": "abcdef01", "generation": 2,
             "status": "standby", "handover_meter": 80,
             "handover": "https://github.com/example/3D_Converters/issues/12#issuecomment-1212"},
            {"role": "checker", "chat_id8": "abcdef02", "generation": 1,
             "status": "hold", "chat_end_seen": True},
        ]}
        projected, _ = project(registry)
        self.assertEqual([a["status"] for a in projected["agents"]], ["standby", "hold"])
        self.assertTrue(all(a.get("chat_end_risk", False) for a in projected["agents"]))
        self.assertEqual(projected["agents"][0]["handover_meter"], 80)
        self.assertEqual(projected["agents"][0]["handover"],
                         "https://github.com/example/3D_Converters/issues/12#issuecomment-1212")

    def test_wp10_owner_vs_delegated_labels_in_timeline(self):
        registry = {"project": "product-a", "repository": PRODUCT}
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "events.jsonl"
            events = [
                {"id": 1, "type": "OWNER_DECISION", "ts": "2026-10-16T08:00:00Z",
                 "text": 'Owner\'s words: "Do it"'},
                {"id": 2, "type": "OWNER_DECISION", "ts": "2026-10-16T08:01:00Z",
                 "text": "(delegated) OwnerTeammember chose a routine reply."},
                {"id": 3, "type": "OWNER_DECISION", "ts": "2026-10-16T08:02:00Z",
                 "text": "OwnerTeammember made a decision without quoted words."},
            ]
            path.write_text("\n".join(json.dumps(e) for e in events))
            _, timeline = project(registry, path)
        self.assertEqual([x.get("decision_label") for x in timeline],
                         ["Owner", "delegated (OwnerTeammember)", "unverified"])

    def test_wp10_external_project_read_only_issue_pr_links(self):
        registry = {"project": "product-a", "repository": PRODUCT,
                    "parent_issue": "https://github.com/example/3D_Converters/issues/12#issuecomment-1212",
                    "pull_requests": [
                        "https://github.com/example/3D_Converters/pull/13",
                        "javascript:alert(1)",
                        "https://github.com/malicious/elsewhere/pull/14",
                    ]}
        projected, _ = project(registry)
        self.assertEqual(projected.get("repository"), PRODUCT)
        self.assertEqual([x["url"] for x in projected.get("external_links", [])], [
            "https://github.com/example/3D_Converters/issues/12#issuecomment-1212",
            "https://github.com/example/3D_Converters/pull/13",
        ])
        self.assertTrue(all(x["read_only"] is True
                            for x in projected["external_links"]))


if __name__ == "__main__":
    unittest.main(verbosity=2)
