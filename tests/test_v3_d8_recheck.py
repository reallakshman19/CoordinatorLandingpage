"""WP-V3 D8: evaluator must stop a CLAIMED move after a newer Owner correction.

Tests only. All data, claims and GitHub references here are synthetic.
The evaluator's unconditional read_only/may_send=False is NOT a D8 pass.
"""
from contextlib import redirect_stdout
from datetime import datetime, timezone
import io
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build_data
import next_move
import next_move_evaluator as evaluator

D3 = ROOT / "tests" / "fixtures" / "wp_v2_d3"
D8 = ROOT / "tests" / "fixtures" / "wp_v3_d8"
PROJECT = "landing-live"
MID = "NM-20261017-210000-a11a"
CLAIMED_AT = "2026-10-17T21:02:00Z"
CORRECTED_AT = "2026-10-17T21:15:00Z"
AT = datetime(2026, 10, 17, 21, 16, tzinfo=timezone.utc)
SOURCE = ("https://github.com/reallakshman19/CoordinatorLandingpage/"
          "issues/1#issuecomment-990000001")
COORDINATOR = {"role": "TeamCoordinator", "id8": "11111111"}


def scenario(temp, *, remove_amendment=False):
    """Copy frozen input material into a fully isolated test root."""
    root = Path(temp) / "root"
    cache = Path(temp) / "cache"
    out = Path(temp) / "out"
    shutil.copytree(D3 / "logs", root / "logs")
    shutil.copytree(D3 / "cache", cache)
    project_dir = root / "logs" / PROJECT
    shutil.copytree(D8 / "moves", project_dir / "moves")
    shutil.copyfile(D8 / "moves.jsonl", project_dir / "moves.jsonl")
    manifest = cache / "capture-info.json"
    cap = json.loads(manifest.read_text())
    cap["source_capture_at"] = "2026-10-17T21:16:00Z"
    manifest.write_text(json.dumps(cap))
    if remove_amendment:
        (cache / "inbox-1.json").write_text("[]\n")
    with mock.patch(
        "owner_json.github_provenance",
        return_value={"sha": None, "author": None, "association": "UNKNOWN"}
    ), mock.patch("subprocess.run",
                  side_effect=AssertionError("D8 cannot access network/chat transport")):
        build_data.build_all(root, out, cache_dir=cache)
    projection = json.loads((out / f"project-{PROJECT}.json").read_text())
    registry = json.loads((project_dir / "registry.json").read_text())
    sha = build_data.git_blob_sha(project_dir / "registry.json")
    threads = evaluator.read_threads(cache)
    agents = projection["agents"]
    view = next_move.load_project_moves(project_dir, registry, agents, threads,
                                        now=AT, registry_sha=sha)
    return root, cache, out, registry, sha, projection, view, agents, threads


def evaluate_scenario(root, registry, sha, projection, view, agents, threads):
    """Directly execute the existing evaluator's read-only pre-send simulation."""
    with mock.patch("subprocess.run",
                    side_effect=AssertionError("evaluator attempted network/chat send")):
        return evaluator.evaluate(registry, view, agents, threads, AT, COORDINATOR,
                                  sha, published=projection["next_move"], root=root)


class D8OwnerCorrectionInvalidatesQueuedMove(unittest.TestCase):
    def test_01_approved_claimed_move_is_valid_and_no_send_was_recorded(self):
        with tempfile.TemporaryDirectory() as temp:
            root, cache, _, reg, sha, proj, view, agents, threads = scenario(temp)
            self.assertEqual(
                (D3 / "logs" / PROJECT / "registry.json").read_bytes(),
                (root / "logs" / PROJECT / "registry.json").read_bytes())
            self.assertEqual(proj["last_cycle_at"], "2026-10-17T21:00:00+00:00")
            self.assertFalse(reg.get("control", {}).get("hold"))
            self.assertEqual(len(view["moves"]), 1)
            self.assertEqual(view["rejected"], [])
            move, = view["moves"]
            self.assertEqual(move["id"], MID)
            self.assertEqual(move["state"], "CLAIMED")
            self.assertEqual([x["state"] for x in move["history"]],
                             ["APPROVED", "CLAIMED"])
            self.assertEqual(move["basis"]["registry_sha"], sha)
            self.assertNotIn("claim expired", move["flags"])
            self.assertNotIn("stale basis", move["flags"])
            self.assertFalse(any(x["state"] in (
                "SEND_INTENT", "SENT_TO_CHAT", "PUBLISHED_TO_THREAD")
                for x in move["history"]))

    def test_02_owner_amendment_is_later_and_d3_guard_is_unreconciled(self):
        with tempfile.TemporaryDirectory() as temp:
            _, cache, _, _, _, proj, _, _, _ = scenario(temp)
            row, = proj["amendments"]["records"]
            self.assertEqual(row["source"], SOURCE)
            self.assertGreater(next_move.stamp(row["created_at"]),
                               next_move.stamp(proj["last_cycle_at"]))
            marker = proj["amendment_checkpoint"]
            self.assertEqual(marker["status"], "UNRECONCILED")
            self.assertEqual(marker["markers"][0]["source"], SOURCE)
            self.assertEqual(len(json.loads((cache/"inbox-1.json").read_text())), 1)

    def test_03_evaluator_pre_send_blocks_the_specific_claimed_move(self):
        with tempfile.TemporaryDirectory() as temp:
            root, _, _, reg, sha, proj, view, agents, threads = scenario(temp)
            report = evaluate_scenario(root, reg, sha, proj, view, agents, threads)
            self.assertEqual(report["schema"], evaluator.SCHEMA)
            self.assertTrue(report["read_only"])
            self.assertFalse(report["may_send"])  # This is *not* the D8 proof.
            gate = report.get("pre_send_recheck") or {}
            self.assertEqual(
                gate.get("status"), "BLOCKED",
                "D8 GAP: evaluator ignores post-CLAIMED Owner scope correction; "
                "always-false may_send is NOT a pre-send recheck")
            self.assertEqual(gate.get("move"), MID)
            self.assertEqual(gate.get("source"), SOURCE)
            self.assertEqual(gate.get("reason"), "unreconciled_owner_amendment")

    def test_04_stale_move_not_ready_or_sent_after_source_correction(self):
        with tempfile.TemporaryDirectory() as temp:
            root, _, _, reg, sha, proj, view, agents, threads = scenario(temp)
            report = evaluate_scenario(root, reg, sha, proj, view, agents, threads)
            self.assertFalse(any(
                x.get("state") in ("SEND_INTENT", "SENT_TO_CHAT")
                for x in report.get("moves", [])))
            gate = report.get("pre_send_recheck") or {}
            self.assertNotEqual(
                gate.get("status"), "READY",
                "A post-checkpoint change must not pass the send gate")
            self.assertEqual(
                gate.get("source"), SOURCE,
                "D8 GAP: there is no amendment-specific, source-linked block "
                "for the CLAIMED move (even if the evaluator is generally read-only)")
            self.assertTrue(gate.get("move") == MID)

    def test_05_cli_does_not_send_or_append_transitions(self):
        with tempfile.TemporaryDirectory() as temp:
            root, cache, out, _, _, _, _, _, _ = scenario(temp)
            ledger = root / "logs" / PROJECT / "moves.jsonl"
            before = ledger.read_bytes()
            with mock.patch("subprocess.run",
                            side_effect=AssertionError("D8 has no external transport")):
                with redirect_stdout(io.StringIO()) as stream:
                    result = evaluator.main([
                        "--root", str(root), "--cache-dir", str(cache),
                        "--projection", str(out / f"project-{PROJECT}.json"),
                        "--actor-role", "TeamCoordinator", "--actor-id8", "11111111",
                        "--at", AT.isoformat()])
            self.assertFalse(result["may_send"])
            self.assertTrue(result["read_only"])
            self.assertEqual(before, ledger.read_bytes())
            self.assertFalse((root/"logs"/PROJECT/"next-move-evaluation.json").exists())
            self.assertEqual(json.loads(stream.getvalue())["schema"], evaluator.SCHEMA)
            self.assertNotIn("SENT_TO_CHAT", ledger.read_text())

    def test_06_control_without_new_amendment_is_not_d8_stale(self):
        with tempfile.TemporaryDirectory() as temp:
            root, _, _, reg, sha, proj, view, agents, threads = scenario(
                temp, remove_amendment=True)
            self.assertEqual(proj["amendment_checkpoint"]["status"], "NONE_FOUND")
            self.assertEqual(view["moves"][0]["state"], "CLAIMED")
            self.assertFalse(view["rejected"])
            report = evaluate_scenario(root, reg, sha, proj, view, agents, threads)
            gate = report.get("pre_send_recheck") or {}
            self.assertNotEqual(gate.get("reason"), "unreconciled_owner_amendment")


if __name__ == "__main__":
    unittest.main(verbosity=2)
