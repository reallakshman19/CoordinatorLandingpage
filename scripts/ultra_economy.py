"""UltraEconomyMode v1: read-only TASK START / TASK EVIDENCE / Next Move link.

No GitHub writes, agent launches, timer creation or authority transitions.
The project registry opts in with ultra_economy: {enabled: true, max_cycles: 1..5}.
"""
from datetime import datetime, timedelta, timezone
import re

ID8 = re.compile(r"^[0-9a-f]{8}$")
TASK_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,79}$")
START = re.compile(
    r"^TASK START v1\s*·\s*(?P<project>[^·\n]+)\s*·\s*"
    r"(?P<role>[^·\n]+)\s*·\s*chat\s+(?P<id8>[0-9a-f]{8})\s*·\s*"
    r"task\s+(?P<task>[A-Za-z0-9_.-]+)\s*·\s*"
    r"cycle\s+(?P<cycle>\d+)/(?P<limit>\d+)\s*$", re.MULTILINE)
END = re.compile(
    r"^TASK EVIDENCE v2\s*·\s*(?P<project>[^·\n]+)\s*·\s*"
    r"(?P<role>[^·\n]+)\s*·\s*chat\s+(?P<id8>[0-9a-f]{8})\s*·",
    re.MULTILINE)


def when(value):
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed.astimezone(timezone.utc) if parsed.tzinfo else None
    except ValueError:
        return None


def field(body, name):
    match = re.search(r"^" + re.escape(name) + r":\s*(.+)$",
                      body, re.MULTILINE | re.IGNORECASE)
    return match.group(1).strip() if match else ""


def status(body):
    """Normalize claims, never convert a claim into independently VERIFIED."""
    value = field(body, "Status")
    if not value:
        match = re.search(r"^Task:[^\n]*?\bStatus:\s*(.*)$", body, re.I | re.M)
        value = match.group(1).strip() if match else ""
    # Compound statuses such as 'DONE engineering / review pending' are claims.
    for category in ("FAILED", "BLOCKED", "PARTIAL", "DONE"):
        if re.search(r"\b" + category + r"\b", value, re.I):
            return category
    return "UNKNOWN"


def config(registry):
    cfg = registry.get("ultra_economy")
    if not isinstance(cfg, dict) or cfg.get("enabled") is not True:
        return {"enabled": False, "max_cycles": None, "error": None}
    limit = cfg.get("max_cycles")
    if type(limit) is not int or not 1 <= limit <= 5:
        return {"enabled": False, "max_cycles": None, "error": "invalid_max_cycles"}
    return {"enabled": True, "max_cycles": limit, "error": None}


def _comments(threads, issue):
    thread = threads.get(issue)
    if not isinstance(thread, dict):
        return None
    rows = thread.get("comments")
    return rows if isinstance(rows, list) else None


def _agent_source(agent):
    url = agent.get("evidence_thread_url") or agent.get("evidence_thread") or ""
    m = re.fullmatch(r"https://github\.com/([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)/issues/(\d+)", url)
    return (m.group(1), int(m.group(2)), url) if m else None


def _start_records(rows, project, id8, role, max_cycles):
    starts, warnings, used = [], [], set()
    for comment in sorted(rows, key=lambda c: (c.get("created_at", ""), c.get("id", 0))):
        if not isinstance(comment, dict):
            continue
        body = comment.get("body") or ""
        match = START.search(body)
        if not match or match.group("project").strip() != project or match.group("id8") != id8 or match.group("role").strip() != role:
            continue
        task = match.group("task")
        cycle, declared = int(match.group("cycle")), int(match.group("limit"))
        timestamp = when(comment.get("created_at"))
        planned = field(body, "Planned outcome")
        expected = field(body, "Expected next")
        blockers = field(body, "Known blocker")
        workplan = field(body, "Workplan")
        fallback = field(body, "Fallback")
        fallback_claim = ("AGENT_REPORTED_ARMED_UNVERIFIED" if re.match(
            r"^ARMED\s+\S+", fallback, re.I) else "AGENT_MUST_ARM")
        key = (task, cycle)
        if (not TASK_ID.fullmatch(task) or declared != max_cycles or
                not 1 <= cycle <= max_cycles or not timestamp or
                not all((planned, expected, blockers, workplan)) or
                not re.fullmatch(r"https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/issues/\d+", workplan)):
            warnings.append("invalid_task_start")
            continue
        if key in used:
            warnings.append("duplicate_task_start")
            continue
        used.add(key)
        starts.append({
            "task": task, "cycle": cycle, "max_cycles": max_cycles,
            "start_comment_id": comment.get("id"), "started_at": timestamp.isoformat(),
            "planned_outcome": planned[:500], "expected_next": expected[:500],
            "known_blocker": blockers[:500], "workplan": workplan,
            "fallback": fallback_claim, "fallback_due_at": (
                timestamp + timedelta(hours=1)).isoformat()})
    return starts, warnings


def _end_for_start(rows, start, project, id8, role):
    started = when(start["started_at"])
    candidates = []
    for comment in rows:
        if not isinstance(comment, dict):
            continue
        body = comment.get("body") or ""
        marker = END.search(body)
        stamp = when(comment.get("created_at"))
        if not marker or not stamp or stamp < started or (
                marker.group("project").strip(), marker.group("id8"), marker.group("role").strip()) != (project, id8, role):
            continue
        task = field(body, "Task").split(maxsplit=1)[0] if field(body, "Task") else ""
        if task != start["task"]:
            continue
        # END should explicitly tie to the START cycle. No guessing across cycles.
        cycle = field(body, "UEM cycle")
        if cycle != str(start["cycle"]) + "/" + str(start["max_cycles"]):
            continue
        candidates.append((stamp, comment, body))
    if not candidates:
        return None
    stamp, row, body = sorted(candidates, key=lambda item: (item[0], item[1].get("id", 0)))[-1]
    return {"end_comment_id": row.get("id"), "ended_at": stamp.isoformat(),
            "claim_status": status(body), "not_done": field(body, "Not done / HOLD")[:500],
            "next_claim": field(body, "Next")[:500]}


def _find_move(moves, evidence_url, current, id8):
    """Exact task/cycle/end-comment correlation; delivery is independently gated."""
    matches = []
    for move in moves or []:
        if not isinstance(move, dict) or move.get("class") != "Dispatch":
            continue
        to = move.get("to") or {}
        trigger = move.get("trigger") or {}
        basis = move.get("basis") or {}
        if (to.get("id8") != id8 or not isinstance(trigger, dict) or
                trigger.get("type") != "uem_end" or trigger.get("task") != current["task"] or
                trigger.get("cycle") != current["cycle"] or
                trigger.get("end_comment_id") != current["end_comment_id"] or
                basis.get("evidence") != evidence_url):
            continue
        matches.append(move)
    if len(matches) != 1:
        return None, "AMBIGUOUS_MOVE" if matches else "NO_MATCHING_MOVE"
    move = matches[0]
    if "stale basis" in (move.get("flags") or []):
        return move, "STALE_MOVE"
    if move.get("state") in ("SENT_TO_CHAT", "PICKED_UP", "ACKED"):
        return move, "DELIVERED_MOVE"
    if move.get("state") in ("HELD", "REJECTED", "CANCELLED", "SUPERSEDED", "EXPIRED"):
        return move, "MOVE_HELD_OR_CLOSED"
    return move, "AWAITING_DELIVERY"


def _followup(end_at, now):
    age = (now - when(end_at)).total_seconds()
    if age < 0:
        return {"state": "UNKNOWN", "next_due_at": None}
    for n in (15, 20, 30):
        due = when(end_at) + timedelta(minutes=n)
        if now < due:
            return {"state": "WAITING", "next_due_at": due.isoformat()}
    return {"state": "OVERDUE_30", "next_due_at": None}


def project(registry, agents, threads, next_view, now=None):
    """Read-only projection. No default activation and no move construction."""
    opts = config(registry)
    result = {"enabled": opts["enabled"], "max_cycles": opts["max_cycles"],
              "error": opts["error"], "agents": {}}
    if not opts["enabled"]:
        return result
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError("now must be timezone aware")
    for agent in agents:
        id8 = agent.get("chat_id8")
        if not isinstance(id8, str) or not ID8.fullmatch(id8):
            continue
        if not str(agent.get("status") or "").lower().startswith("active"):
            result["agents"][id8] = {"state": "NOT_ACTIVE", "may_proceed": False}
            continue
        source = _agent_source(agent)
        if not source or source[0] != registry.get("repository"):
            continue
        rows = _comments(threads, source[1])
        if rows is None:
            result["agents"][id8] = {"state": "UNKNOWN_SOURCE", "may_proceed": False}
            continue
        starts, warnings = _start_records(rows, registry.get("project"), id8,
                                           agent.get("role"), opts["max_cycles"])
        if not starts:
            result["agents"][id8] = {"state": "NO_TASK_START", "may_proceed": False,
                                      "warnings": warnings}
            continue
        current = starts[-1]
        end = _end_for_start(rows, current, registry.get("project"), id8,
                             agent.get("role"))
        item = {**current, "warnings": warnings, "may_proceed": False}
        if end is None:
            item["state"] = "WORKING_CLAIM"
            item["fallback"] = current["fallback"]
        else:
            item.update(end)
            item["fallback"] = "AGENT_MUST_CANCEL_OR_REFRESH"
            move, condition = _find_move(next_view.get("moves"), source[2], item, id8)
            item["move_state"] = condition
            item["move_id"] = move.get("id") if move else None
            item["followup"] = _followup(end["ended_at"], now)
            held = bool((registry.get("control") or {}).get("hold"))
            exhausted = current["cycle"] >= opts["max_cycles"]
            if held:
                item["state"] = "HOLD"
            elif exhausted:
                item["state"] = "MAX_CYCLES_REACHED"
            elif condition == "DELIVERED_MOVE" and end["claim_status"] != "UNKNOWN":
                item["state"] = "NEXT_MOVE_RECORDED_DELIVERED"
                item["may_proceed"] = True  # still requires agent-side custody checks
            else:
                item["state"] = condition
            if (held or exhausted or condition in (
                    "DELIVERED_MOVE", "MOVE_HELD_OR_CLOSED")):
                item["followup"] = {"state": "STOPPED", "next_due_at": None}
        result["agents"][id8] = item
    return result
