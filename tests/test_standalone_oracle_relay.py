"""Standalone Oracle relay falsifiers: state/history, coordinator isolation, onboarding."""
from __future__ import annotations
import importlib.util
import json
from pathlib import Path
import tempfile
import types
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "standalone_oracle_relay.py"
spec = importlib.util.spec_from_file_location("standalone_oracle_relay_tested", SCRIPT)
mod = importlib.util.module_from_spec(spec)
assert spec is not None and spec.loader is not None
spec.loader.exec_module(mod)

def put(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


class StandaloneOracleRelayTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "progress-data"
        self.home = self.root / "ciifr"
        put(self.home / "index.json", {"topics": [{"key": "normal"}]})
        put(self.home / "normal" / "stages.json", {"N1": {"state": "NOT_STARTED"}})
        self.baseline = {"schema": "standalone-oracle-relay-audit/v1",
                         "project": "ciifr", "events": [{
                             "seq": 1, "id": "CIIFR-R-0001", "previous_id": None,
                             "at": "2026-10-21T17:38:11Z", "kind": "BASELINE",
                             "topic": "normal", "stage": "N1", "before": None,
                             "after": "NOT_STARTED", "actor": "Oracle",
                             "source": "https://github.com/example/contract",
                             "summary": "Declared historic dashboard snapshot only."}]}
        put(self.home / "audit.json", self.baseline)
        self.orig_root = mod.ROOT
        mod.ROOT = self.root
        self.addCleanup(lambda: setattr(mod, "ROOT", self.orig_root))

    def test_initial_baseline_is_a_snapshot_and_consistent(self):
        self.assertEqual(mod.validate_audit(self.home), [])

    def test_unlogged_stage_transition_is_falsified(self):
        put(self.home / "normal" / "stages.json", {"N1": {"state": "VERIFIED"}})
        self.assertTrue(any("differs" in x for x in mod.validate_audit(self.home)))

    def test_append_requires_existing_real_change_and_then_reconciles(self):
        put(self.home / "normal" / "stages.json", {"N1": {"state": "SUBMITTED"}})
        args = types.SimpleNamespace(project="ciifr", topic="normal", kind="STAGE_TRANSITION",
                                     actor="Oracle", source="https://github.com/example/proof",
                                     summary="Candidate returned; not yet independently reviewed.",
                                     stage="N1", before="NOT_STARTED", after="SUBMITTED")
        self.assertEqual(mod.append_event(args), "CIIFR-R-0002")
        self.assertEqual(mod.validate_audit(self.home), [])
        records = json.loads((self.home / "audit.json").read_text())["events"]
        self.assertEqual(records[-1]["previous_id"], "CIIFR-R-0001")
        self.assertEqual(records[-1]["after"], "SUBMITTED")

    def test_append_refuses_fabricated_before_state(self):
        put(self.home / "normal" / "stages.json", {"N1": {"state": "SUBMITTED"}})
        args = types.SimpleNamespace(project="ciifr", topic="normal", kind="STAGE_TRANSITION",
                                     actor="Oracle", source="https://github.com/example/proof",
                                     summary="Wrong prestate", stage="N1",
                                     before="VERIFIED", after="SUBMITTED")
        with self.assertRaises(ValueError):
            mod.append_event(args)

    def test_invalid_chain_falsified(self):
        corrupt = json.loads(json.dumps(self.baseline))
        corrupt["events"][0]["previous_id"] = "SPOOF"
        put(self.home / "audit.json", corrupt)
        self.assertTrue(any("broken append-only" in x for x in mod.validate_audit(self.home)))

    def test_public_custody_source_rule(self):
        corrupt = json.loads(json.dumps(self.baseline))
        corrupt["events"][0]["source"] = "https://drive.google.com/secret"
        put(self.home / "audit.json", corrupt)
        self.assertTrue(any("public GitHub source" in x for x in mod.validate_audit(self.home)))

    def test_real_ciifr_baseline_reconciles(self):
        home = ROOT / "site" / "progress-data" / "ciifr"
        self.assertEqual(mod.validate_audit(home), [])

    def test_ui_uses_opt_in_oracle_and_keeps_otm_fallback(self):
        data = json.loads((ROOT / "site" / "progress-data" / "projects.json").read_text())
        modes = {p["key"]: p.get("mode", "coordinator") for p in data["projects"]}
        self.assertEqual(modes["ciifr"], "standalone-oracle")
        self.assertEqual(modes["g9v35"], "coordinator")
        js = (ROOT / "site" / "js" / "progress_page.js").read_text()
        self.assertIn("ppOwnerRecipient(ctx)", js)
        self.assertIn("? 'Oracle' : 'OwnerTeammember'", js)
        self.assertIn("'fixtures' : 'actions'", js)

    def test_all_ciifr_topics_have_read_first_grounding(self):
        index = json.loads((ROOT / "site" / "progress-data" / "ciifr" / "index.json").read_text())
        for topic in index["topics"]:
            with self.subTest(topic=topic["key"]):
                f = json.loads((ROOT / "site" / "progress-data" / "ciifr" /
                                topic["key"] / "fixtures.json").read_text())
                self.assertTrue(any("REQUIRED FIRST" in z["t"] for z in f["inputs"]))
                self.assertTrue(any("Engineering relay audit" in z["t"] for z in f["inputs"]))


if __name__ == "__main__":
    unittest.main()
