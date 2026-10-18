#!/usr/bin/env python3
"""WP15 coordinator-cycle evaluator: read-only source check and proposed output.

No scheduler, gh mutation, chat send, or record append. A proposed EVALUATED
row is NOT an actual heartbeat until a human commits it to moves.jsonl.
"""
import argparse
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import sys

import build_data
import next_move
from landing_build.continuity import assess_amendment_checkpoint
from landing_build.project_intent import _amendments
from landing_build.retirement_guard import return_recommendations

SCHEMA = "next_move_evaluator.v1"
PROJECT = "landing-live"
REPO = "reallakshman19/CoordinatorLandingpage"
ALERT_FLAGS = {"evaluator stale", "detected, not acted on", "held",
               "delivery uncertain", "claim expired", "stale basis"}


def snapshot(view):
    """Stable comparison fields; volatile display text is not a contract."""
    moves = view.get("moves") or []
    return {
        "criticality": view.get("criticality"),
        "evaluator_at": view.get("evaluator_at"),
        "task_cycle": {k: (view.get("task_cycle") or {}).get(k)
                       for k in ("status", "count", "next", "due")},
        "active": sorted([m["id"] + ":" + m["state"]
                          for m in view.get("active", [])]),
        "queue": sorted([m["id"] + ":" + m["state"]
                         for m in view.get("queue", [])]),
        "flags": sorted(set(view.get("flags", [])) & ALERT_FLAGS),
        "rejected_count": len(view.get("rejected") or []),
    }


def differences(expected, observed):
    if not isinstance(expected, dict) or not isinstance(observed, dict):
        return ["snapshot_invalid"]
    keys = ("criticality", "evaluator_at", "task_cycle", "active", "queue",
            "flags", "rejected_count")
    return [k for k in keys if expected.get(k) != observed.get(k)]


def cross_check(view, recorded, registry_sha, now):
    """Only an explicitly committed evaluator report can be shown on page."""
    if recorded is None:
        return {"status": "not_recorded", "mismatches": [],
                "observed_at": None}
    if (not isinstance(recorded, dict) or recorded.get("schema") != SCHEMA
            or recorded.get("project") != PROJECT
            or recorded.get("registry_sha") != registry_sha
            or not isinstance(recorded.get("snapshot"), dict)):
        return {"status": "untrusted_or_stale_source",
                "mismatches": [], "observed_at": None}
    at = next_move.stamp(recorded.get("at"))
    if not at or at > now + timedelta(minutes=1):
        return {"status": "untrusted_or_stale_source",
                "mismatches": [], "observed_at": None}
    mismatch = differences(recorded["snapshot"], snapshot(view))
    freshness = "stale_output" if now - at > timedelta(minutes=30) else (
        "mismatch" if mismatch else "match")
    # The EVALUATED row in this file is only a proposal, never actual ledger state.
    return {"status": freshness,
            "mismatches": mismatch, "observed_at": at.isoformat(),
            "note": "proposal only; not a recorded EVALUATED heartbeat"}


def _eligible_signal(registry, agents, threads, view, now, root=None):
    """Explicit source signals; no invented self-report or G2 activation."""
    triggers = []
    registry_agents = registry.get("agents") or []
    if isinstance(registry.get("chat_end_seen"), dict):
        seen = registry["chat_end_seen"]
        if (seen.get("confirmed") is True and
                next_move.stamp(seen.get("at")) and seen.get("chat_id8") in {
                    x.get("chat_id8") for x in registry_agents
                    if isinstance(x, dict)}):
            triggers.append(("chat_end_seen", "handover_trigger",
                             seen["at"], str(seen["chat_id8"])))
    # A numeric threshold without the agent's self-report is not evidence.
    for a in registry_agents:
        if not isinstance(a, dict):
            continue
        meter = a.get("handover_meter")
        if (isinstance(meter, dict) and meter.get("self_reported") is True
                and isinstance(meter.get("value"), (int, float))
                and not isinstance(meter.get("value"), bool)
                and isinstance(meter.get("warning_level"), (int, float))
                and meter["value"] >= meter["warning_level"]
                and next_move.stamp(meter.get("at"))):
            triggers.append(("handover_meter", "handover_trigger",
                             meter["at"], str(a.get("chat_id8", ""))))
        regat = next_move.stamp(a.get("registered_at"))
        if (regat and now - regat > timedelta(minutes=15)
                and a.get("own_words_ack") is False):
            triggers.append(("agent_registered_no_ack", "status_check",
                             a["registered_at"], str(a.get("chat_id8", ""))))
    # Only verified, owner-repository PR HEAD observations from the publisher.
    for a in agents:
        if not isinstance(a, dict): continue
        status = a.get("evidence_head_status") or {}
        if (status.get("status") == "superseded"
                and status.get("pr_url") and status.get("current_head")):
            triggers.append(("evidence_head_moved", "reconcile",
                             now.isoformat(), str(a.get("chat_id8", ""))))
    if isinstance(registry.get("handover_owner_words"), dict):
        words = registry["handover_owner_words"]
        if words.get("text") and next_move.stamp(words.get("at")):
            triggers.append(("owner_handover", "handover_trigger",
                             words["at"], "Owner words"))
    # Red flag only: not an authorized dispatch.
    open_decisions = registry.get("open_owner_decisions") or []
    for row in open_decisions if isinstance(open_decisions, list) else []:
        if not isinstance(row, dict):
            continue
        at = next_move.stamp(row.get("created_at"))
        if at and now - at > timedelta(minutes=30) and row.get("status") in (None, "open"):
            triggers.append(("owner_decision_age", None, row["created_at"],
                             str(row.get("id", "unknown"))))
    # No inferred analysis-only streak from prose. Explicit marker is required.
    recent = []
    for thread in threads.values():
        if not isinstance(thread, dict): continue
        for c in thread.get("comments", []):
            if isinstance(c, dict) and c.get("kind") == "analysis_only" and next_move.stamp(c.get("created_at")):
                recent.append((c["created_at"], True))
            elif isinstance(c, dict) and c.get("kind") in ("task_evidence", "implementation"):
                recent.append((c.get("created_at", ""), False))
    recent.sort(key=lambda x: x[0])
    if len(recent) >= 3 and all(x[1] for x in recent[-3:]):
        triggers.append(("analysis_drift", "ground", recent[-1][0], "3 explicitly tagged blocks"))
    # An actual, bounded on-disk read is needed to assert a label is missing.
    work = registry.get("engineering_work")
    if (registry.get("engineering_pr_delivery") == "v3.6"
            and isinstance(work, str) and work.replace("-", "").isalnum()
            and len(work) <= 64 and root is not None
            and not (root / "relay" / "AIM" / (work + ".yaml")).is_file()):
        triggers.append(("label_missing", "label_request", now.isoformat(), "missing "+work+".yaml"))
    return triggers


def _pre_send_recheck(view, amendment_checkpoint):
    """D8: read-only, source-bound check of pending dispatches before send.

    Project capture being read-only is not a recheck. The caller supplies the
    already projected D3 checkpoint; neither this check nor evaluate() fetches.
    """
    moves = [m for m in view.get("moves", []) if isinstance(m, dict)
             and m.get("class") == "Dispatch"
             and m.get("state") in ("CLAIMED", "APPROVED")]
    if not moves:
        return {"status": "NOT_APPLICABLE", "reason": "no_pre_send_move"}, []
    check = amendment_checkpoint if isinstance(amendment_checkpoint, dict) else {}
    state = check.get("status")
    checks = []
    for move in moves:
        move_id = move.get("id")
        entry = {"move_id": move_id, "move": move_id,
                 "status": "UNKNOWN", "reason": "amendment_context_unknown",
                 "source": check.get("source"), "amendment_at": None}
        transitions = [row for row in move.get("history", [])
                       if isinstance(row, dict) and
                       row.get("state") == move.get("state")]
        claim_at = next_move.stamp(transitions[-1].get("at")) if transitions else None
        if claim_at is None:
            entry["reason"] = "approval_or_claim_time_unknown"
        elif state in ("NONE_FOUND", "RECONCILED"):
            entry.update(status="CLEAR", reason="no_new_unreconciled_amendment")
        elif state == "UNRECONCILED":
            records = check.get("markers")
            if not isinstance(records, list) or not records:
                entry["reason"] = "unreconciled_records_unknown"
            else:
                later, unknown = [], []
                for row in records:
                    if not isinstance(row, dict):
                        unknown.append({"source": check.get("source")})
                        continue
                    created = next_move.stamp(row.get("created_at"))
                    if created is None:
                        unknown.append(row)
                    elif created > claim_at:
                        later.append((created, row))
                if later:
                    created, latest = max(later, key=lambda pair: pair[0])
                    entry.update(status="BLOCKED",
                                 reason="unreconciled_owner_amendment",
                                 source=latest.get("source") or check.get("source"),
                                 amendment_at=latest.get("created_at"))
                elif unknown:
                    entry.update(reason="amendment_time_unknown",
                                 source=unknown[0].get("source") or check.get("source"))
                else:
                    entry.update(status="CLEAR", reason="no_amendment_newer_than_move")
        elif state == "UNKNOWN":
            entry["reason"] = check.get("reason") or "amendment_time_unknown"
        checks.append(entry)
    # A proven block outranks unknown, which outranks a clear. All candidates
    # remain available for independent inspection, not just the first move.
    rank = {"BLOCKED": 0, "UNKNOWN": 1, "CLEAR": 2}
    return min(checks, key=lambda row: rank[row["status"]]), checks


def evaluate(registry, view, agents, threads, now, actor, registry_sha,
             published=None, root=None, amendment_checkpoint=None):
    if (registry.get("project") != PROJECT or registry.get("repository") != REPO
            or not (registry.get("next_move") or {}).get("pilot")):
        raise ValueError("WP15 is restricted to the registered landing-live pilot")
    if not next_move.actor(actor) or not next_move.stamp(now.isoformat()):
        raise ValueError("An explicit coordinator role+id8 and timestamp are required")
    triggers = []
    cycle = view.get("task_cycle") or {}
    if cycle.get("due") in ("ground", "reconcile") and isinstance(cycle.get("count"), int):
        triggers.append(("task_cycle", cycle["due"], cycle.get("due_at"),
                         str(cycle["count"])))
    triggers.extend(_eligible_signal(registry, agents, threads, view, now, root=root))
    moves = view.get("moves") or []
    notices = []
    for signal, kind, source_at, detail in triggers:
        if not kind:  # Owner decision aging only warns; no dispatch
            notices.append({"signal": signal, "kind": None, "warning": "red owner decision",
                            "source_at": source_at, "detail": detail,
                            "status": "observed_only"})
            continue
        if not next_move.stamp(source_at):
            continue
        active = any(m.get("kind") == kind and m.get("state") not in
                     next_move.TERMINAL for m in moves)
        if active:
            status = "already_recorded"
        elif now - next_move.stamp(source_at) > timedelta(minutes=20):
            status = "detected, not acted on"
        else:
            status = "due"
        notices.append({"signal": signal, "kind": kind, "source_at": source_at,
                        "detail": detail, "status": status})
    observed = snapshot(view)
    recheck, checks = _pre_send_recheck(view, amendment_checkpoint)
    return {"schema": SCHEMA, "project": PROJECT, "repository": REPO,
            "at": now.isoformat(), "registry_sha": registry_sha,
            "read_only": True, "may_send": False,
            "recommendations": return_recommendations(registry, threads),
            "pre_send_recheck": recheck, "pre_send_rechecks": checks,
            "heartbeat_proposal": {"state": "EVALUATED", "at": now.isoformat(),
                                   "by": actor},
            "heartbeat_committed": False,
            "trigger_notices": notices,
            "snapshot": observed,
            "page_compare": differences(snapshot(published), observed)
                if published is not None else [],
            "summary": {"last_recorded_evaluated": view.get("evaluator_at"),
                        "evaluator_stale": "evaluator stale" in view.get("flags", []),
                        "detected_not_acted_on": (
                            "detected, not acted on" in view.get("flags", [])
                            or any(x["status"] == "detected, not acted on"
                                   for x in notices))}}


def read_threads(cache, project=PROJECT):
    folder = cache / "project-threads" / project
    rows = {}
    for path in folder.glob("issue-*.json") if folder.is_dir() else []:
        obj = next_move.load(path)
        if isinstance(obj, dict) and isinstance(obj.get("number"), int):
            rows[obj["number"]] = obj
    return rows


def main(argv=None):
    parser = argparse.ArgumentParser(description="Emit read-only coordinator-cycle evaluation JSON")
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--cache-dir", type=Path, default=Path("_live_cache"))
    parser.add_argument("--projection", type=Path, required=True,
                        help="published site/data/project-landing-live.json")
    parser.add_argument("--actor-role", required=True)
    parser.add_argument("--actor-id8", required=True)
    parser.add_argument("--at", required=True,
                        help="explicit offset-aware ISO timestamp, no automatic scheduler")
    parser.add_argument("--output", type=Path,
                        help="optional local proposal file, never under logs/")
    opts = parser.parse_args(argv)
    root = opts.root.resolve()
    at = next_move.stamp(opts.at)
    if at is None:
        parser.error("--at must be an explicit timestamp with timezone")
    if opts.output and (opts.output.resolve() == root / "logs" or
                        root / "logs" in opts.output.resolve().parents):
        parser.error("--output may not write the authoritative logs/ ledger")
    raw = next_move.load(root / "logs" / PROJECT / "registry.json")
    projection = next_move.load(opts.projection)
    if not isinstance(raw, dict) or not isinstance(projection, dict) or projection.get("project") != PROJECT:
        parser.error("missing/foreign registry or published projection")
    sha = build_data.git_blob_sha(root / "logs" / PROJECT / "registry.json")
    if projection.get("registry_blob_sha") != sha:
        parser.error("registry head does not match projection; recapture first")
    cache = (opts.cache_dir if opts.cache_dir.is_absolute() else root / opts.cache_dir)
    agents = projection.get("agents") or []
    threads = read_threads(cache)
    own_heads = {a["chat_id8"]: a["evidence_head_status"]["current_head"]
                 for a in agents if isinstance(a, dict) and
                 a.get("chat_id8") and isinstance(a.get("evidence_head_status"), dict)
                 and a["evidence_head_status"].get("current_head")}
    latest = next_move.load_project_moves(root / "logs" / PROJECT, raw, agents, threads,
            now=at, registry_sha=sha, evidence_heads=own_heads)
    if "amendment_checkpoint" in projection:
        # A present projection is the authoritative captured D3 snapshot.
        amendment_checkpoint = projection["amendment_checkpoint"]
    else:
        # Older project projections have no D3 field. Reuse only locally
        # captured #1 comments; absence/error stays UNKNOWN, never CLEAR.
        inbox = next_move.load(cache / "inbox-1.json")
        amended = _amendments(PROJECT, inbox, isinstance(inbox, list), REPO)
        amendment_checkpoint = assess_amendment_checkpoint(
            amended, projection.get("last_cycle_at"))
    report = evaluate(raw, latest, agents, threads, at,
                      {"role":opts.actor_role, "id8":opts.actor_id8}, sha,
                      projection.get("next_move"), root=root,
                      amendment_checkpoint=amendment_checkpoint)
    encoded = json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True)
    if opts.output:
        opts.output.parent.mkdir(parents=True, exist_ok=True)
        opts.output.write_text(encoded + "\n", encoding="utf-8", newline="\n")
    print(encoded)
    return report


if __name__ == "__main__":
    main()
