#!/usr/bin/env python3
"""WP-L2(a): native chat n/a intake regression (Common #408/6230274796).

This is a RED-first behavioral test. No production code is changed by this file.
"""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build_data


# Exact authentic header from Common #408, comment 6230274796.
REAL_HEADER = (
    "TASK EVIDENCE v2 · handover-master · implementer (OwnerTeammember) "
    "· chat n/a (Claude session) · #1 · 17 Oct 09:38 +04:00"
)
BODY = REAL_HEADER + "\nTask: HM-01/HM-03/HM-04\nStatus: DONE\n"
STAMP = "2026-10-17T05:38:00Z"


def task_with_chat(value):
    return BODY.replace("chat n/a (Claude session)", "chat " + value, 1)


def status_with_chat(value):
    return (
        "STATUS v2 · implementer · chat " + value
        + " · working on HM-01 · next HM-02 · blocker none"
    )


def parse_status(value):
    thread = {"comments": [{
        "id": 408, "created_at": STAMP, "body": status_with_chat(value),
    }]}
    return build_data.build_agent_evidence(thread)


class ChatNAIntakeTests(unittest.TestCase):
    def test_authentic_task_evidence_na_has_unknown_identity(self):
        event = build_data.parse_task_evidence(BODY, 408, STAMP)
        self.assertIsNotNone(event)
        self.assertEqual(event["project"], "handover-master")
        self.assertEqual(event["role"], "implementer (OwnerTeammember)")
        self.assertEqual(event["chat_id8"], None)  # UNKNOWN, never a fake id8
        self.assertEqual(event["seq"], 1)
        self.assertEqual(event["status"], "DONE")

    def test_task_na_without_optional_parenthesis(self):
        event = build_data.parse_task_evidence(task_with_chat("n/a"), 408, STAMP)
        self.assertIsNotNone(event)
        self.assertIsNone(event["chat_id8"])

    def test_status_na_with_and_without_optional_parenthesis(self):
        for value in ("n/a (Claude session)", "n/a"):
            with self.subTest(chat=value):
                entries = parse_status(value)
                self.assertEqual(len(entries), 1)
                self.assertEqual(entries[0]["type"], "status")
                self.assertIsNone(entries[0]["chat_id8"])
                self.assertEqual(entries[0]["task"], "HM-01")
                self.assertEqual(entries[0]["next"], "HM-02")

    def test_existing_eight_hex_id_unchanged(self):
        ident = "6ad36e4d"
        event = build_data.parse_task_evidence(task_with_chat(ident), 408, STAMP)
        self.assertIsNotNone(event)
        self.assertEqual(event["chat_id8"], ident)
        entries = parse_status(ident)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["chat_id8"], ident)

    def test_malformed_chat_ids_rejected_by_both_headers(self):
        for ident in ("1234567", "123456789", "g1234567",
                      "n/a (unclosed", "n/a (Claude session) extra"):
            with self.subTest(chat=ident):
                self.assertIsNone(
                    build_data.parse_task_evidence(task_with_chat(ident), 408, STAMP))
                self.assertEqual(parse_status(ident), [])


if __name__ == "__main__":
    unittest.main()
