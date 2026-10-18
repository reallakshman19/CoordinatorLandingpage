"""D5 source-only retirement and released-lease guards.

Registry id8 is an attribution hint, not authenticated agent identity.
No method sends a chat message, accepts a workpack or mutates GitHub.
"""
import re
from collections.abc import Mapping
from datetime import datetime, timezone

from landing_build.evidence_parse import EVIDENCE_RE

CONTROL_REPO = "reallakshman19/CoordinatorLandingpage"
STATUS_ID = re.compile(
    r"STATUS v2\s*·\s*[^·\n]+\s*·\s*chat\s+([0-9a-f]{8})\b", re.IGNORECASE)


def stamp(value):
    if not isinstance(value, str):
        return None
    try:
        time = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return time.astimezone(timezone.utc) if time.tzinfo else None
    except ValueError:
        return None


def retired(agent):
    if not isinstance(agent, Mapping):
        return False
    return (agent.get("retired") is True or
            str(agent.get("status") or "").strip().casefold().startswith("retired"))


def lease_released(lease):
    """Recognise legacy released, recorded released_at and RELEASED state."""
    return (bool(lease.get("released")) or bool(lease.get("released_at")) or
            str(lease.get("state") or "").strip().casefold() == "released")


def eligibility_reason(registry, ident):
    """Only *positively matched* retired/released id8s are denied.

    Actors not declared in agents (e.g. the Owner/TC control actor) still
    require their own separate authority/approval; this is not such a grant.
    """
    if not isinstance(ident, str) or not re.fullmatch(r"[0-9a-fA-F]{8}", ident):
        return None
    ident = ident.casefold()
    for entry in registry.get("agents", []):
        if (isinstance(entry, Mapping) and
                str(entry.get("chat_id8") or "").casefold() == ident and
                retired(entry)):
            return "retired"
    # Both lease collections are authoritative evidence. A live-looking
    # writer_leases entry cannot erase a released legacy lease (or vice versa).
    for field in ("writer_leases", "leases"):
        for lease in registry.get(field) or []:
            if not isinstance(lease, Mapping) or not lease_released(lease):
                continue
            holder = str(lease.get("actor") or lease.get("holder") or "")
            if re.search(r"(?<![0-9a-f])" + ident + r"(?![0-9a-f])",
                         holder, re.I):
                return "lease_released"
    return None


def countable_evidence(agent, comment_at):
    """Historical evidence before a verified retirement is retained.

    If the actual retirement instant cannot be proven, don't promote an
    alleged returning agent's evidence toward GO. Never invent the clock.
    """
    if not retired(agent):
        return True
    retired_at = stamp(agent.get("retired_at"))
    created_at = stamp(comment_at)
    return bool(retired_at and created_at and created_at < retired_at)


def return_recommendations(registry, threads):
    """Source-link new-looking claims by retired agents in cached threads.

    No authenticated full chat identifier is available. This reports a
    *claimed* id8 and proposes HOLD; it never delivers one.
    """
    agents = {str(a.get("chat_id8") or "").casefold(): a
              for a in registry.get("agents", [])
              if isinstance(a, Mapping) and retired(a)}
    if not agents:
        return []
    found = []
    for key, thread in (threads.items() if isinstance(threads, Mapping) else []):
        if not isinstance(thread, Mapping):
            continue
        repo = thread.get("repository") or CONTROL_REPO
        number = thread.get("number", key)
        if repo != CONTROL_REPO or not isinstance(number, int) or number <= 0:
            continue
        for row in thread.get("comments", []):
            if not isinstance(row, Mapping) or not isinstance(row.get("body"), str):
                continue
            ident, kind = None, None
            match = EVIDENCE_RE.search(row["body"])
            if match and match.group("project").strip() == registry.get("project"):
                ident, kind = match.group("chat"), "TASK_EVIDENCE_v2"
            if not ident:
                status = STATUS_ID.search(row["body"])
                if status:
                    ident, kind = status.group(1), "STATUS_v2"
            ident = ident.casefold() if isinstance(ident, str) else None
            comment = row.get("id")
            if ident not in agents or not isinstance(comment, int) or comment <= 0:
                continue
            if countable_evidence(agents[ident], row.get("created_at")):
                continue
            found.append({
                "kind": "RETIREMENT_RETURN_BLOCK",
                "status": "HOLD_RECOMMENDED", "chat_id8": ident,
                "source": f"https://github.com/{CONTROL_REPO}/issues/{number}"
                          f"#issuecomment-{comment}",
                "comment_at": row.get("created_at"),
                "source_kind": kind, "reason": "retired_actor_claim_unverified",
                "read_only": True})
    return found
