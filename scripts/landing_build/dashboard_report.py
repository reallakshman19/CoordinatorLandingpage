"""Small read-only envelope over already parsed, instance-scoped evidence."""
from datetime import datetime
import re


def latest_report(row, project_view, now):
    unknown = {"status": "UNKNOWN", "reason": "no_unambiguous_instance_report"}
    ident, generation = row.get("instance_id8"), row.get("generation")
    if (not ident or type(generation) is not int or generation < 1 or row.get("conflicts")
            or project_view.get("project", row.get("project")) != row.get("project")):
        return unknown
    agents = [a for a in project_view.get("agents", [])
              if isinstance(a, dict) and a.get("chat_id8") == ident
              and type(a.get("generation")) is int
              and a.get("generation") == generation]
    if len(agents) != 1:
        return unknown
    agent = agents[0]
    thread = agent.get("evidence_thread_url", "")
    if not isinstance(thread, str) or not re.fullmatch(
            r"https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/issues/[1-9][0-9]*(?:#issuecomment-[1-9][0-9]*)?", thread):
        return unknown
    candidates = []
    for entry in agent.get("evidence", []):
        if not isinstance(entry, dict) or entry.get("type") not in ("evidence", "status"):
            continue
        if entry.get("chat_id8") != ident or entry.get("project", row.get("project")) != row.get("project"):
            continue
        cid, stamp = entry.get("comment_id"), entry.get("ts")
        if type(cid) is not int or cid <= 0 or not isinstance(stamp, str):
            continue
        try:
            at = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
        except ValueError:
            continue
        if at.tzinfo is None or at > now:
            continue
        candidates.append((at, cid, entry))
    if not candidates:
        return unknown
    _, cid, entry = max(candidates, key=lambda item: (item[0], item[1]))
    result = {"status": "REPORTED", "at": entry["ts"], "kind": entry["type"],
              "source_ref": thread.split("#")[0] + "#issuecomment-" + str(cid),
              "qualification": "agent_claim_not_activity_or_acceptance"}
    for field in ("task", "next", "blocker"):
        if isinstance(entry.get(field), str):
            result[field] = entry[field][:500]
    return result
