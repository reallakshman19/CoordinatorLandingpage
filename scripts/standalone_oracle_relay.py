#!/usr/bin/env python3
"""Standalone Oracle relay ledger: validate or explicitly append public-safe events.

No GitHub operations, agent dispatch, Owner authentication or stage-state updates.
The original Progress-stage file is the declared state; this log gives its
traceable baseline and all subsequent transitions, with Git commits as immutable history.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1] / "site" / "progress-data"
STATES = {"VERIFIED", "SUBMITTED", "IN_PROGRESS", "BLOCKED", "NOT_STARTED",
          "STALE", "UNKNOWN", "NOT_APPLICABLE"}
KINDS = {"BASELINE", "STAGE_TRANSITION", "GROUNDING_UPDATE", "AGENT_ONBOARDING",
         "TASK_HANDOFF", "AGENT_RETURN", "INDEPENDENT_REVIEW", "BENCHMARK_RECEIPT",
         "OWNER_INPUT_RECEIVED", "OWNER_DECISION", "IMPROVEMENT_PROPOSAL", "PUBLICATION"}
KEY = re.compile(r"^[a-z0-9][a-z0-9-]*$")


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def validate_audit(project_dir, audit_override=None):
    """Return all ledger/schema errors; never mutate anything."""
    project_dir = Path(project_dir)
    issues = []
    path = project_dir / "audit.json"
    try:
        audit = audit_override if audit_override is not None else load(path)
        index = load(project_dir / "index.json")
    except (OSError, ValueError) as exc:
        return [f"cannot read audit/index JSON: {exc}"]
    project = project_dir.name
    if audit.get("schema") != "standalone-oracle-relay-audit/v1" or audit.get("project") != project:
        issues.append("wrong audit schema/project")
    events = audit.get("events")
    if not isinstance(events, list) or not events:
        return issues + ["audit.events must be nonempty list"]
    topics = {t["key"] for t in index.get("topics", []) if not t.get("planned")}
    records = {}
    for topic in topics:
        try:
            records[topic] = load(project_dir / topic / "stages.json")
        except (OSError, ValueError) as exc:
            issues.append(f"{topic}: cannot read stages: {exc}")
    last = None
    current = {}
    for i, e in enumerate(events, 1):
        if not isinstance(e, dict):
            issues.append(f"record {i}: not object")
            continue
        rid = f"{project.upper()}-R-{i:04d}"
        if e.get("seq") != i or e.get("id") != rid or e.get("previous_id") != last:
            issues.append(f"record {i}: broken append-only sequence/previous_id")
        last = rid
        topic = e.get("topic")
        kind = e.get("kind")
        stage = e.get("stage")
        if topic not in topics:
            issues.append(f"record {i}: unknown topic {topic!r}")
        if kind not in KINDS:
            issues.append(f"record {i}: unknown kind {kind!r}")
        if not isinstance(e.get("at"), str) or not re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d+)?Z", e["at"]):
            issues.append(f"record {i}: expected real UTC timestamp")
        if not isinstance(e.get("actor"), str) or not e["actor"].strip() or not isinstance(e.get("summary"), str) or not e["summary"].strip():
            issues.append(f"record {i}: actor/summary missing")
        if not (isinstance(e.get("source"), str) and (e["source"].startswith("https://github.com/") or e["source"].startswith("OWNER_PRIVATE_REF:"))):
            issues.append(f"record {i}: public GitHub source or OWNER_PRIVATE_REF required")
        if kind in ("BASELINE", "STAGE_TRANSITION"):
            if topic not in records or stage not in records[topic]:
                issues.append(f"record {i}: invalid stage {topic}/{stage}")
                continue
            key = (topic, stage)
            if e.get("after") not in STATES:
                issues.append(f"record {i}: invalid after state")
                continue
            if kind == "BASELINE":
                if key in current or e.get("before") is not None:
                    issues.append(f"record {i}: duplicate/invalid baseline")
                else:
                    current[key] = e["after"]
            elif key not in current or e.get("before") != current.get(key):
                issues.append(f"record {i}: transition prestate mismatch (expected {current.get(key)!r})")
            else:
                current[key] = e["after"]
        elif "before" in e or "after" in e:
            issues.append(f"record {i}: only state transitions may set before/after")
    for topic, stages in records.items():
        for sid, s in stages.items():
            expected = current.get((topic, sid))
            if expected is None:
                issues.append(f"{topic}/{sid}: missing baseline")
            elif expected != s.get("state"):
                issues.append(f"{topic}/{sid}: audit last state {expected} differs from stages.json {s.get('state')}")
    return issues


def append_event(args):
    if not KEY.fullmatch(args.project) or not KEY.fullmatch(args.topic):
        raise ValueError("project/topic must be safe keys")
    home = ROOT / args.project
    audit_path = home / "audit.json"
    audit = load(audit_path)
    problems = validate_audit(home)
    # A newly edited stages.json may be one transition ahead of the ledger;
    # enforce current state on that stage separately, but reject other drift.
    if problems:
        allowed = f"{args.topic}/{args.stage}: audit last state "
        if args.kind != "STAGE_TRANSITION" or len(problems) != 1 or not problems[0].startswith(allowed):
            raise ValueError("invalid existing ledger: " + "; ".join(problems))
    if args.topic not in {t["key"] for t in load(home / "index.json").get("topics", [])}:
        raise ValueError("topic absent from project")
    if args.kind not in KINDS - {"BASELINE"}:
        raise ValueError("invalid append kind")
    if not (args.source.startswith("https://github.com/") or args.source.startswith("OWNER_PRIVATE_REF:")):
        raise ValueError("source must be public GitHub reference or private Owner reference marker")
    if args.kind == "STAGE_TRANSITION":
        stage_state = load(home / args.topic / "stages.json")[args.stage]["state"]
        if args.after not in STATES or stage_state != args.after or args.before not in STATES:
            raise ValueError("stage after-state must match already edited stages.json")
        last_state = None
        for e in audit["events"]:
            if e.get("topic") == args.topic and e.get("stage") == args.stage and e["kind"] in ("BASELINE", "STAGE_TRANSITION"):
                last_state = e["after"]
        if last_state != args.before or last_state == args.after:
            raise ValueError(f"transition prestate mismatch or no actual change: {last_state!r}")
    elif args.stage or args.before or args.after:
        raise ValueError("non-transition must not specify stage/before/after")
    seq = len(audit["events"]) + 1
    ev = {"seq": seq, "id": f"{args.project.upper()}-R-{seq:04d}",
          "previous_id": audit["events"][-1]["id"],
          "at": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
          "kind": args.kind, "topic": args.topic, "actor": args.actor, "source": args.source,
          "summary": args.summary}
    if args.kind == "STAGE_TRANSITION":
        ev.update(stage=args.stage, before=args.before, after=args.after)
    audit["events"].append(ev)
    proposed_errors = validate_audit(home, audit)
    if proposed_errors:
        # The in-memory record is not persisted, and nothing should be auto-fixed.
        raise ValueError("proposed event does not reconcile: " + "; ".join(proposed_errors))
    audit_path.write_text(json.dumps(audit, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return ev["id"]


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)
    check = sub.add_parser("check", help="read-only validate the existing public record")
    check.add_argument("--project", required=True)
    put = sub.add_parser("append", help="append one explicit source-backed event; does not edit stages")
    put.add_argument("--project", required=True)
    put.add_argument("--topic", required=True)
    put.add_argument("--kind", required=True)
    put.add_argument("--actor", required=True)
    put.add_argument("--source", required=True, help="GitHub permalink or OWNER_PRIVATE_REF:<record-id>")
    put.add_argument("--summary", required=True)
    put.add_argument("--stage", default="")
    put.add_argument("--before", default="")
    put.add_argument("--after", default="")
    args = p.parse_args(argv)
    try:
        if args.command == "append":
            ident = append_event(args)
            print("APPENDED", ident)
        else:
            errors = validate_audit(ROOT / args.project)
            for error in errors:
                print("ERROR", error)
            print("audit OK" if not errors else f"{len(errors)} audit problem(s)")
            return 1 if errors else 0
    except (ValueError, OSError, KeyError) as exc:
        print("ERROR", str(exc))
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())
