"""WP-L5: immutable, synthetic-only v3.6 scoreboard projection.

Never derives an E pass, source attestation or Owner acceptance from a title,
author self-check, fixture or the constant-zero snapshot field.
"""
import hashlib
import json
from pathlib import Path
from landing_build.project_view import V36_TITLE

ARTIFACT = "benchmarks/v36-scoreboard/scoreboard.json"
SHA256 = "a3d3a50ab830ebf261004936cc916f9ca9659d93be23e9fc41edf6bc2e1d34d3"
SELECTED = "v36-continuity"  # Explicit fixture display only; no ECO-08 live pilot.
EVAL = "NOT_EVALUATED"


def _base(registry, state, reason):
    return {
        "status": state, "reason": reason,
        "source_class": "synthetic fixture",
        "source_path": ARTIFACT, "source_sha256": SHA256,
        "registry_parent": registry.get("parent_issue"),
        "E": {"status": state},
        "A": {"label": "category coverage", "status": state},
        "V": {"status": state},
        "acceptance": {"status": state},
        "tasks": [],
    }


def _title_fallback(view):
    progress = view.get("child_progress") if isinstance(view, dict) else {}
    if not isinstance(progress, dict) or progress.get("status") != "known":
        return None
    items = progress.get("items")
    if not isinstance(items, list):
        return None
    matched = [V36_TITLE.match(t.get("title", ""))
               for t in items if isinstance(t, dict)
               and isinstance(t.get("title"), str)]
    matches = [m for m in matched if m]
    return {"label": "derived from title", "count": len(matches),
            "done": sum(m.group(2) == "DONE" for m in matches),
            "note": "Title projection only; not E, verification or acceptance"} if matches else None


def _fail(registry, status, reason, view):
    result = _base(registry, status, reason)
    if status == "UNKNOWN":
        fallback = _title_fallback(view)
        if fallback:
            result["title_fallback"] = fallback
    return result


def _valid(board):
    if not isinstance(board, dict) or board.get("schema") != "v36.scoreboard/v1":
        return "schema_mismatch: expected v36.scoreboard/v1"
    rows, totals = board.get("rows"), board.get("totals")
    if not isinstance(rows, list) or not isinstance(totals, dict):
        return "schema_mismatch: rows/totals"
    tasks = totals.get("tasks")
    if (not isinstance(tasks, int) or isinstance(tasks, bool) or tasks < 0
            or len(rows) != tasks):
        return "schema_mismatch: selected task denominator"
    if (board.get("parent") != "reallakshman19/Common#341"
            or board.get("plan") != "V36-341-PLAN-02"):
        return "source_identity_mismatch: pinned Common example"
    if board.get("read_complete") is not True:
        return "source_incomplete: cannot certify the fixture's denominator"
    if any(not isinstance(board.get(k), str)
           or not board[k].startswith(EVAL) for k in ("A", "V", "acceptance")):
        return "schema_mismatch: A/V/acceptance must remain NOT_EVALUATED"
    for k in ("A_detail", "V_detail"):
        if not isinstance(board.get(k), dict) or board[k].get("status") != EVAL:
            return "schema_mismatch: " + k
    for t in rows:
        if (not isinstance(t, dict) or not isinstance(t.get("task_id"), str)
                or not isinstance(t.get("E"), str)
                or any(not isinstance(t.get(k), str)
                       or not t[k].startswith(EVAL)
                       for k in ("A", "V", "acceptance"))):
            return "schema_mismatch: task evidence and unverified categories"
    return None


def scoreboard_project(root, project_name, registry, project_view):
    """Project a pinned local artifact; missing UNKNOWN, corrupt/mismatch ERROR."""
    if project_name != SELECTED:
        return None
    registry = registry if isinstance(registry, dict) else {}
    path = Path(root) / ARTIFACT
    if not path.is_file():
        return _fail(registry, "UNKNOWN", "artifact_missing", project_view)
    try:
        raw = path.read_bytes()
        board = json.loads(raw)
    except (OSError, UnicodeError, ValueError):
        return _fail(registry, "ERROR", "artifact_unreadable_or_invalid_json", project_view)
    problem = _valid(board)   # Report schema errors even when bytes also drift.
    if problem:
        return _fail(registry, "ERROR", problem, project_view)
    if hashlib.sha256(raw).hexdigest() != SHA256:
        # Windows Actions checkout may materialize committed LF as CRLF.
        # Accept only if byte-for-byte canonical LF hashes to the same pin.
        canonical = raw.replace(b"\r\n", b"\n")
        if hashlib.sha256(canonical).hexdigest() != SHA256:
            return _fail(registry, "ERROR", "artifact_sha256_mismatch", project_view)
    total = board["totals"]
    if (not isinstance(total.get("E_current"), int)
            or isinstance(total["E_current"], bool)
            or total["E_current"] < 0 or total["E_current"] > total["tasks"]):
        return _fail(registry, "ERROR", "schema_mismatch: E numerator", project_view)
    result = _base(registry, "SYNTHETIC_FIXTURE",
                   "test_fixture_not_live_ECO_08_NOT_RUN")
    result.update({
        "source_parent": board["parent"],
        "plan": board["plan"],
        "observed_at": board.get("observed_at"),
        "E": {"status": "SYNTHETIC_FIXTURE",
              "current": total["E_current"], "tasks": total["tasks"],
              "note": "Native fixture evidence, NOT a passing test"},
        "A": {"label": "category coverage", "status": EVAL,
              "required_categories": len(board["A_detail"].get("required_categories") or [])},
        "V": {"status": EVAL},
        "acceptance": {"status": EVAL},
        "tasks": [{
            "task_id": t["task_id"], "E": t["E"],
            "A": EVAL, "V": EVAL, "acceptance": EVAL,
        } for t in board["rows"]],
    })
    return result
