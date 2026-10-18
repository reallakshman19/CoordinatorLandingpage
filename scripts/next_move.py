"""Next Move v1 P1: strictly read-only validator and publisher projection.

This module never writes moves, claims or transitions. An invalid record is
quarantined with specific reasons; a claim is not authority to send.
"""
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
import re

from landing_build.retirement_guard import eligibility_reason, countable_evidence

ID = re.compile(r"^NM-\d{8}-\d{6}-[0-9a-f]{4}$")
ID8 = re.compile(r"^[0-9a-f]{8}$")
HEX = re.compile(r"^[0-9a-fA-F]{40}$")
DISPATCH = {"next_step", "course_correction", "new_requirement", "ground",
            "reconcile", "handover_trigger", "buddy_1a", "buddy_1b", "buddy_2",
            "label_request", "skill_alignment", "status_check"}
NOTICE = {"agent_added", "agent_retired"}
TERMINAL = {"REJECTED", "CANCELLED", "EXPIRED", "SUPERSEDED", "VERIFIED"}
SIDES = {"REJECTED", "HELD", "SUPERSEDED", "CANCELLED", "EXPIRED"}
FLOW = {
    "PUBLISHED": {"APPROVED", "REJECTED", "HELD", "SUPERSEDED", "CANCELLED", "EXPIRED"},
    "APPROVED": {"CLAIMED", "HELD", "SUPERSEDED", "CANCELLED", "EXPIRED"},
    "CLAIMED": {"SEND_INTENT", "HELD", "SUPERSEDED", "CANCELLED", "EXPIRED"},
    "SEND_INTENT": {"SENT_TO_CHAT", "PUBLISHED_TO_THREAD", "DELIVERY_UNCERTAIN",
                    "NOT_SENT"},
    "DELIVERY_UNCERTAIN": {"SENT_TO_CHAT", "NOT_SENT"},
    "NOT_SENT": {"CLAIMED", "HELD", "CANCELLED", "EXPIRED"},
    "SENT_TO_CHAT": {"PICKED_UP", "HELD", "SUPERSEDED"},
    "PUBLISHED_TO_THREAD": {"PICKED_UP", "HELD", "SUPERSEDED"},
    "PICKED_UP": {"ACKED", "HELD", "SUPERSEDED"},
    "ACKED": {"DONE_CLAIMED", "HELD", "SUPERSEDED"},
    "DONE_CLAIMED": {"VERIFIED", "HELD", "SUPERSEDED"},
    "HELD": {"PUBLISHED"},  # no stale grant may resume directly
}
ACTIVE = {"CLAIMED", "SEND_INTENT", "DELIVERY_UNCERTAIN", "NOT_SENT",
          "SENT_TO_CHAT", "PUBLISHED_TO_THREAD", "PICKED_UP", "ACKED",
          "DONE_CLAIMED"}
BOARD = {
    "Waiting approval": {"PUBLISHED", "HELD", "REJECTED"},
    "Approved": {"APPROVED"},
    "Claimed": {"CLAIMED", "SEND_INTENT"},
    "Sent/Published/Uncertain": {"SENT_TO_CHAT", "PUBLISHED_TO_THREAD",
                                  "DELIVERY_UNCERTAIN", "NOT_SENT"},
    "Picked up/Acked": {"PICKED_UP", "ACKED"},
    "Done claimed": {"DONE_CLAIMED"},
    "Verified": {"VERIFIED"},
}
TASK_TRIGGERS = {5: "ground", 10: "ground", 15: "ground", 19: "reconcile"}
MAX_FILES = 100
MAX_ROWS = 1000


def stamp(value):
    if not isinstance(value, str):
        return None
    try:
        d = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return d.astimezone(timezone.utc) if d.tzinfo else None
    except ValueError:
        return None


def load(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return None


def actor(value):
    return (isinstance(value, dict) and isinstance(value.get("role"), str)
            and bool(value["role"].strip())
            and isinstance(value.get("id8"), str)
            and bool(ID8.fullmatch(value["id8"])))


def criticality(registry):
    if (registry.get("criticality") == "normal" and
            isinstance(registry.get("criticality_owner_words"), str) and
            registry["criticality_owner_words"].strip()):
        return "normal"
    return "critical"  # unset or an unsubstantiated downgrade is critical


def schema(item, project, filename):
    faults = []
    if not isinstance(item, dict):
        return ["invalid_json_object"]
    ident = item.get("id")
    if not isinstance(ident, str) or not ID.fullmatch(ident) or filename != ident + ".json":
        faults.append("id_or_filename_invalid")
    if item.get("project") != project:
        faults.append("project_mismatch")
    cls, kind = item.get("class"), item.get("kind")
    if cls != "Dispatch" and cls != "Notice":
        faults.append("class_invalid")
    elif kind not in (DISPATCH if cls == "Dispatch" else NOTICE):
        faults.append("kind_invalid")
    for key in ("from", "to"):
        if not actor(item.get(key)):
            faults.append(key + "_actor_invalid")
    if not isinstance(item.get("text"), str) or not item["text"].strip():
        faults.append("text_missing")
    if not isinstance(item.get("trigger"), (str, dict)) or not item["trigger"]:
        faults.append("trigger_invalid")
    if not isinstance(item.get("evidence_format"), str) or not item["evidence_format"].strip():
        faults.append("evidence_format_missing")
    basis = item.get("basis")
    if not isinstance(basis, dict):
        faults.append("basis_invalid")
    else:
        if not isinstance(basis.get("evidence"), str) or not basis["evidence"].strip():
            faults.append("basis_evidence_missing")
        for key in ("head", "registry_sha"):
            val = basis.get(key)
            if not isinstance(val, str) or not HEX.fullmatch(val):
                faults.append("basis_" + key + "_invalid")
    if stamp(item.get("created_at")) is None:
        faults.append("created_at_invalid")
    parent = item.get("supersedes")
    if parent is not None and (not isinstance(parent, str) or
                               not ID.fullmatch(parent) or parent == ident):
        faults.append("supersedes_invalid")
    return faults


def normal_role(value):
    """Shared conservative normalization for identity-role labels only."""
    return (str(value or "").lower().replace(" ", "").replace("_", ""))


def _approval(record, row, crit, registry):
    who, sender, role = row.get("by"), record.get("from"), None
    if not actor(who):
        return "approval_actor_invalid", False
    role = normal_role(who["role"])
    self_approved = who["id8"] == sender.get("id8") if isinstance(sender, dict) else False
    if role == "owner":
        return None, self_approved
    is_otm = "ownerteammember" in role
    if crit == "normal" and is_otm:
        return None, self_approved
    if crit == "critical" and is_otm and record["kind"] in {
            "buddy_1a", "buddy_1b", "buddy_2"}:
        # H1–H3, not an umbrella grant. A real signal, no HOLD and a named
        # successor are necessary. Activation remains an Owner decision.
        grant = row.get("grant_ref") or record.get("grant_ref")
        signal = (record.get("trigger") in ("chat_end_seen", "handover_meter",
                                            "owner_handover") or
                  isinstance(record.get("trigger"), dict) and
                  record["trigger"].get("type") in (
                      "chat_end_seen", "handover_meter", "owner_handover"))
        agents = registry.get("agents") or []
        successor = (record.get("to") or {}).get("id8")
        eligible = any(a.get("chat_id8") == successor for a in agents if isinstance(a, dict))
        if (grant == "approve takeover via buddy v1.7" and signal
                and not (registry.get("control") or {}).get("hold")
                and eligible and not self_approved):
            return None, False
        return "critical_handover_grant_ineligible", self_approved
    return ("critical_self_approval_forbidden" if self_approved and crit == "critical"
            else "approver_tier_invalid"), self_approved


def _claim(record, claim, at):
    if not isinstance(claim, dict):
        return "claim_file_missing"
    claimed = stamp(claim.get("claimed_at"))
    until = stamp(claim.get("expires_at"))
    claimant = claim.get("by")
    if not actor(claimant) or not claimed or not until:
        return "claim_schema_invalid"
    if (until <= claimed or until - claimed > timedelta(minutes=15)):
        return "claim_ttl_invalid"
    if at and at < claimed:
        return "claim_before_creation"
    if claimant["id8"] != record["to"]["id8"]:
        return "claimer_is_not_recipient"
    return None


def validate_records(registry, raw_moves, rows, claims, now=None):
    now = now or datetime.now(timezone.utc)
    crit = criticality(registry)
    project = registry.get("project")
    valid, rejected, by_id = {}, [], {}
    if len(raw_moves) > MAX_FILES or len(rows) > MAX_ROWS:
        return [], [{"id": "source", "reasons": ["source_limit_exceeded"]}], {
            "criticality": crit, "heartbeats": []}
    for filename, value in sorted(raw_moves.items()):
        faults = schema(value, project, filename)
        if isinstance(value, dict):
            for side, label in (("from", "sender"), ("to", "recipient")):
                who = value.get(side)
                reason = eligibility_reason(registry, who.get("id8") if isinstance(who, dict) else None)
                if reason:
                    faults.append(label + "_" + reason)
        if isinstance(value, dict):
            mid = value.get("id")
            if mid in by_id:
                faults.append("duplicate_move_id")
            elif isinstance(mid, str):
                by_id[mid] = value
        if faults:
            rejected.append({"id": filename, "reasons": faults})
        else:
            valid[value["id"]] = dict(value, state="PUBLISHED", self_approved=False,
                                      history=[], flags=[])
    for mid, item in list(valid.items()):
        parent = item.get("supersedes")
        if parent and (parent not in by_id or parent == mid or
                       by_id[parent].get("project") != project):
            rejected.append({"id": mid, "reasons": ["supersedes_target_missing"]})
            del valid[mid]
    # Supersede chains must terminate, never cycle.
    for mid in list(valid):
        seen, target = set(), mid
        while target and target in valid:
            if target in seen:
                rejected.append({"id": mid, "reasons": ["supersedes_cycle"]})
                valid.pop(mid, None)
                break
            seen.add(target)
            target = valid[target].get("supersedes")
    heartbeats = []
    grouped = {mid: [] for mid in valid}
    for row in rows:
        if not isinstance(row, dict):
            rejected.append({"id": "row", "reasons": ["transition_not_object"]})
            continue
        if row.get("state") == "EVALUATED" and row.get("move") is None:
            if stamp(row.get("at")) and actor(row.get("by")):
                heartbeats.append(row["at"])
            else:
                rejected.append({"id": "EVALUATED", "reasons": ["heartbeat_invalid"]})
            continue
        mid = row.get("move")
        if mid not in grouped:
            rejected.append({"id": str(mid), "reasons": ["transition_unknown_move"]})
            continue
        grouped[mid].append(row)
    for mid, item in list(valid.items()):
        problem = None
        claim = claims.get(mid)
        last_ts = stamp(item["created_at"])
        for row in grouped[mid]:
            state, at = row.get("state"), stamp(row.get("at"))
            if not at or (last_ts and at < last_ts) or not actor(row.get("by")):
                problem = "transition_actor_or_timestamp_invalid"; break
            if (reason := eligibility_reason(registry, row["by"]["id8"])):
                problem = "transition_actor_" + reason; break
            if state not in FLOW.get(item["state"], set()):
                problem = "transition_forbidden"; break
            if item["class"] == "Notice" and state == "APPROVED":
                problem = "notice_cannot_be_approved"; break
            if state == "APPROVED":
                problem, own = _approval(item, row, crit, registry)
                if problem: break
                item["self_approved"] = own
            if state == "CLAIMED":
                problem = _claim(item, claim, at)
                if problem: break
            if state in ("SEND_INTENT", "SENT_TO_CHAT", "PUBLISHED_TO_THREAD",
                         "NOT_SENT", "PICKED_UP", "ACKED", "DONE_CLAIMED",
                         "VERIFIED") and not row.get("proof"):
                problem = "transition_proof_missing"; break
            if state == "PUBLISHED" and item["state"] == "HELD":
                if not row.get("note") or not row.get("proof"):
                    problem = "hold_release_revalidation_missing"; break
                item["self_approved"] = False
            if state == "VERIFIED":
                who = row["by"]["id8"]
                if who in {item["from"]["id8"], item["to"]["id8"]}:
                    problem = "verification_requires_non_doer"; break
            if state in ("REJECTED", "CANCELLED", "EXPIRED") and not row.get("note"):
                problem = "terminal_reason_missing"; break
            if state == "SUPERSEDED":
                replacement = row.get("by_move") or row.get("proof")
                if replacement not in by_id or by_id[replacement].get("supersedes") != mid:
                    problem = "supersession_not_linked"; break
            item["state"] = state
            item["history"].append({"state": state, "at": row["at"]})
            last_ts = at
        if problem:
            rejected.append({"id": mid, "reasons": [problem]})
            del valid[mid]
            continue
        expires = stamp(claim.get("expires_at")) if isinstance(claim, dict) else None
        if item["state"] == "SEND_INTENT" and expires and expires <= now:
            item["state"] = "DELIVERY_UNCERTAIN"
            item["flags"].append("delivery uncertain")
        # Expiry before SEND_INTENT is not a delivery claim. Flag/queue it for
        # reconciliation, never silently mark a send or authorize a renewal.
        if item["state"] == "CLAIMED" and expires and expires <= now:
            item["flags"].append("claim expired")
        if item["state"] == "DELIVERY_UNCERTAIN":
            item["flags"].append("delivery uncertain")
        if item["state"] == "NOT_SENT": item["flags"].append("not sent")
        if item["state"] == "HELD": item["flags"].append("held")
        if item["state"] == "PUBLISHED" and item["class"] == "Dispatch":
            item["flags"].append("waiting approval")
        if item["self_approved"]: item["flags"].append("self-approved")
        if item["basis"].get("registry_sha") != registry.get("_registry_sha"):
            item["flags"].append("stale basis")
        # A moved PR head is not excused by a matching registry checksum.
        # Compare a move only with a verified head for its own recipient.
        # Never copy another agent's PR head into the project-wide basis.
        current = (registry.get("_current_evidence_heads") or {}).get(
            item["to"]["id8"])
        if current and item["basis"]["head"].lower() != current.lower():
            if "stale basis" not in item["flags"]: item["flags"].append("stale basis")
    # Only one effective active claim per recipient, and queued dispatches cannot
    # start with a second simultaneous CLAiMED record. Reject every contender.
    slots = {}
    for item in valid.values():
        if item["class"] == "Dispatch" and item["state"] in ACTIVE:
            key = item["to"]["id8"]
            slots.setdefault(key, []).append(item["id"])
    for mids in slots.values():
        if len(mids) > 1:
            for mid in mids:
                rejected.append({"id": mid, "reasons": ["concurrent_dispatch"]})
                valid.pop(mid, None)
    return list(valid.values()), rejected, {"criticality": crit,
                                           "heartbeats": heartbeats}


def task_cycle(agents, threads, moves, project, now=None):
    """Count distinct evidence COMMENT IDs since the last recorded work GO.

    Count across chat generations; no GO boundary -> no invented cycle count.
    """
    starts = [m for m in moves if m["class"] == "Dispatch"
              and m["state"] not in ("REJECTED", "CANCELLED", "EXPIRED")
              and (m.get("trigger") == "GO"
                   or isinstance(m.get("trigger"), dict)
                   and m["trigger"].get("type") == "GO")]
    if not starts:
        return {"status": "no_go", "count": None, "next": None,
                "label": "task cycle unknown — no GO recorded"}
    go = max(starts, key=lambda m: m["created_at"])
    since = stamp(go["created_at"])
    ids = {a.get("chat_id8") for a in agents}
    by_agent = {a.get("chat_id8"): a for a in agents}
    issue_nums = {a.get("evidence_thread_num") for a in agents}
    # Import once per count, never inside the per-comment loop.
    from build_data import parse_task_evidence
    seen = {}
    for number in issue_nums:
        thread = threads.get(number) or {}
        for row in thread.get("comments", []):
            try:
                block = parse_task_evidence(row.get("body", ""),
                                            row.get("id", 0),
                                            row.get("created_at", ""))
            except (TypeError, ValueError, AttributeError):
                block = None
            if (block and block["project"] == project and block["chat_id8"] in ids
                    and stamp(row.get("created_at")) and
                    stamp(row["created_at"]) >= since
                    and countable_evidence(by_agent.get(block["chat_id8"], {}),
                                           row["created_at"])):
                seen[(thread.get("repository"), number, row.get("id"))] = stamp(
                    row["created_at"])
    n = len(seen)
    next_trigger = next(n + distance for distance in range(1, 21)
                        if (n + distance) % 20 in TASK_TRIGGERS)
    trigger = TASK_TRIGGERS.get(n % 20) if n else None
    return {"status": "known", "count": n, "next": next_trigger,
            "due": trigger,
            "due_at": max(seen.values()).isoformat() if trigger and seen else None,
            "label": f"task {n} · next {TASK_TRIGGERS[next_trigger % 20]} at {next_trigger}"}


def load_project_moves(folder, registry, agents, threads, now=None, registry_sha=None,
                       evidence_heads=None, owner_inputs=None):
    now = now or datetime.now(timezone.utc)
    path = Path(folder)
    moves_dir = path / "moves"
    raw = {}
    if moves_dir.is_dir():
        for file in sorted(moves_dir.iterdir()):
            if file.is_file() and file.suffix == ".json":
                raw[file.name] = load(file)
    rows = []
    lines = path / "moves.jsonl"
    if lines.is_file():
        try:
            with lines.open(encoding="utf-8") as fh:
                for i, line in enumerate(fh):
                    if i >= MAX_ROWS:
                        rows.append({"overflow": True})
                        break
                    if line.strip():
                        try: rows.append(json.loads(line))
                        except ValueError: rows.append(None)
        except OSError:
            rows.append(None)
    claims = {file.stem: load(file) for file in
              sorted((moves_dir / "claims").glob("*.json"))} if (
                  moves_dir / "claims").is_dir() else {}
    reg = dict(registry, _registry_sha=registry_sha,
               _current_evidence_heads=evidence_heads or {})
    valid, rejected, meta = validate_records(reg, raw, rows, claims, now)
    heartbeat = max((stamp(x) for x in meta["heartbeats"]), default=None)
    flags = []
    if heartbeat is None or now - heartbeat > timedelta(minutes=30):
        flags.append("evaluator stale")
    if (registry.get("control") or {}).get("hold"):
        flags.append("held")
    by_recipient = {}
    for item in valid:
        item["approver_tier"] = ("Owner / OwnerTeammember" if meta["criticality"] == "normal"
                                 else "Owner only (H1–H3 exception)")
        by_recipient.setdefault(item["to"]["id8"], []).append(item)
    for recipient, items in by_recipient.items():
        items.sort(key=lambda m: m["created_at"])
        active = any(m["state"] in ACTIVE for m in items)
        for m in items:
            if m["class"] == "Dispatch" and m["state"] == "PUBLISHED" and active:
                m["flags"].append("queued behind active dispatch")
    active_moves = [m for m in valid if m["class"] == "Dispatch"
                    and m["state"] in ACTIVE]
    queue = [m for m in valid if m["class"] == "Dispatch"
             and m["state"] in {"PUBLISHED", "APPROVED", "HELD"}]
    board = {name: [m["id"] for m in valid if m["state"] in states]
             for name, states in BOARD.items()}
    counters = task_cycle(agents, threads, valid, registry.get("project"), now)
    if counters.get("due") and not any(
            m["kind"] == counters["due"] and m["state"] not in TERMINAL
            for m in valid):
        # Do not turn an unverified time-of-threshold into a made-up alert.
        # The observed checkpoint time is the real evidence comment timestamp,
        # not the evaluator's optional heartbeat (which may be missing).
        due = stamp(counters.get("due_at"))
        if due and now - due > timedelta(minutes=20):
            flags.append("detected, not acted on")
    for item in valid:
        flags.extend(item["flags"])
    input_requests = []
    for source in owner_inputs or []:
        if source.get("project") == registry.get("project") and source.get(
                "type") in ("NEXT_MOVE_COMPOSE", "NEXT_MOVE_APPROVAL"):
            input_requests.append({"id": source.get("id"),
                                   "type": source.get("type"),
                                   **validate_input_request(
                                       registry, source, valid, source)})
    return {"pilot": (registry.get("next_move") or {}).get("pilot") is True,
            "criticality": meta["criticality"],
            "approval_required": (registry.get("next_move") or {}).get(
                "approval_required", True),
            "approver_tier": ("Owner / OwnerTeammember" if meta["criticality"] == "normal"
                              else "Owner only (H1–H3 exception)"),
            "moves": valid, "rejected": rejected, "input_requests": input_requests,
            "board": board,
            "active": active_moves, "queue": queue,
            "flags": sorted(set(flags)), "evaluator_at": (
                heartbeat.isoformat() if heartbeat else None),
            "task_cycle": counters,
            "agents": {a["chat_id8"]: {
                "active": [m for m in active_moves if m["to"]["id8"] == a["chat_id8"]],
                "queue": [m for m in queue if m["to"]["id8"] == a["chat_id8"]],
                "task_cycle": counters}
                for a in agents if a.get("chat_id8")}}


# WP14 Owner-input proposals: never convert a self-asserted role or committed
# request into an APPROVED transition. A transition must still pass _approval.
def validate_input_request(registry, record, moves, provenance):
    """Return a read-only evaluation of a committed OI request.

    GitHub author association is not an OwnerTeammember identity proof.
    Role claims in text never override the actual transition ledger.
    """
    if record.get("project") != "landing-live" or not (
            registry.get("next_move") or {}).get("pilot"):
        return {"valid": False, "reason": "pilot_not_enabled"}
    kind = record.get("type")
    if kind not in ("NEXT_MOVE_COMPOSE", "NEXT_MOVE_APPROVAL"):
        return {"valid": False, "reason": "not_next_move_input"}
    try:
        payload = json.loads(record.get("text") or "")
    except (ValueError, TypeError):
        return {"valid": False, "reason": "request_json_invalid"}
    if not isinstance(payload, dict):
        return {"valid": False, "reason": "request_payload_invalid"}
    if not provenance or provenance.get("author_association") not in (
            "OWNER", "MEMBER", "COLLABORATOR") or provenance.get("flags"):
        return {"valid": False, "reason": "unverified_commit_author"}
    if kind == "NEXT_MOVE_COMPOSE":
        candidate = payload.get("move")
        faults = schema(candidate, registry["project"],
                        str(candidate.get("id", "")) + ".json"
                        if isinstance(candidate, dict) else "")
        return {"valid": not faults, "reason": ",".join(faults) if faults
                else "draft_only_not_published", "effective": False}
    move_id, by = payload.get("move"), payload.get("by")
    found = next((m for m in moves if m.get("id") == move_id), None)
    if not found or found.get("state") != "PUBLISHED":
        return {"valid": False, "reason": "move_not_waiting_approval"}
    if isinstance(by, dict) and (reason := eligibility_reason(registry, by.get("id8"))):
        return {"valid": False, "reason": "approval_actor_" + reason}
    row = {"by": by, "grant_ref": payload.get("grant_ref")}
    problem, self_approved = _approval(found, row, criticality(registry), registry)
    if problem:
        return {"valid": False, "reason": problem}
    # Owner tier is independently anchored by the GitHub author association.
    # No public registry maps OTM to a specific GitHub login, so even a
    # collaborator's valid tier claim remains a REQUEST pending ledger proof.
    if normal_role(by["role"]) == "owner" and (
            provenance.get("author_association") != "OWNER"):
        return {"valid": False, "reason": "owner_identity_not_verified"}
    return {"valid": True, "reason": "approval_request_only",
            "self_approved": self_approved, "effective": False}
