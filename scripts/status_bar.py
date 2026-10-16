"""WP16: normalized registered roster and three-dimensional STATUS BAR.

Read-only. Never turns activity, a timer hint or a role label into authority.
Top-level agents, workstream agents/runners and standbys all remain individual
records, including retirement history and conflicting identity declarations.
"""
from datetime import datetime, timedelta, timezone
import re

PROJECT_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,79}$")
ID8 = re.compile(r"^[0-9a-f]{8}$")
ORDER = {"green": 0, "yellow": 1, "grey": 2, "red": 3}


def _stamp(raw):
    if not isinstance(raw, str):
        return None
    try:
        value = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        return value.astimezone(timezone.utc) if value.tzinfo else None
    except ValueError:
        return None


def _sources(registry):
    """Enumerate before projection; never silently skip an invalid row."""
    for index, row in enumerate(registry.get("agents") or []):
        yield ("main", "agent", index, row, f"agents[{index}]")
    for stream, data in sorted((registry.get("workstreams") or {}).items()):
        if not isinstance(data, dict):
            yield (str(stream), "workstream_invalid", 0, data,
                   f"workstreams.{stream}")
            continue
        for index, row in enumerate(data.get("agents") or []):
            yield (str(stream), "agent", index, row,
                   f"workstreams.{stream}.agents[{index}]")
        if "execution_runner" in data:
            yield (str(stream), "execution_runner", 0,
                   data["execution_runner"], f"workstreams.{stream}.execution_runner")
        if "standby" in data:
            yield (str(stream), "standby", 0, data["standby"],
                   f"workstreams.{stream}.standby")
        standby = data.get("standbys") or []
        if isinstance(standby, dict):
            standby = [standby]
        for index, row in enumerate(standby):
            yield (str(stream), "standby", index + 1, row,
                   f"workstreams.{stream}.standbys[{index}]")
    standby = registry.get("standbys") or []
    if isinstance(standby, dict):
        standby = [standby]
    for index, row in enumerate(standby):
        yield ("main", "standby", index, row, f"standbys[{index}]")


def normalize_roster(registry):
    """One deterministic key per *declaration*, never per deduped id8."""
    project = registry.get("project")
    if not isinstance(project, str) or not PROJECT_ID.fullmatch(project):
        raise ValueError("registry_project_invalid")
    out = []
    for stream, kind, index, raw, source in _sources(registry):
        entry = raw if isinstance(raw, dict) else {}
        ident = entry.get("chat_id8")
        valid = isinstance(ident, str) and bool(ID8.fullmatch(ident))
        generation = entry.get("generation")
        if type(generation) is not int or generation < 1:
            generation = None
        # Position is a stable source locator, not a claim about chat identity.
        # Include workstream+kind and index so colliding id8 declarations survive.
        key = f"{project}/workstream:{stream}/instance:{kind}:{index}"
        role = str(entry.get("role") or "unknown")
        state = str(entry.get("status") or entry.get("state") or "unknown")
        retired = bool(entry.get("retired")) or state.lower().startswith("retired")
        standby = kind == "standby" or "standby" in state.lower()
        record = {
            "key": key, "project": project, "workstream": stream,
            "kind": kind, "source_path": source, "source_index": index,
            "instance_id8": ident if valid else None,
            "generation": generation, "role": role,
            "alias": str(entry.get("alias") or role),
            "work_state": state, "retired": retired, "standby": standby,
            "complete": ("COMPLETE" in state.upper() or
                         "DONE" in state.upper() or
                         "FROZEN" in state.upper()),
            "chat_link": None, "conflicts": [],
            "observation": entry.get("observation"),
            "monitoring": entry.get("monitoring"),
            "last_evaluation": entry.get("last_evaluation"),
            "grant": entry.get("grant") or entry.get("execution_grant"),
            "material_release": entry.get("material_release"),
            "adoption": entry.get("adoption"),
            "work": entry.get("work") or entry.get("current_task"),
        }
        if valid:
            record["chat_link"] = "https://chatgpt.com/c/" + ident
        else:
            record["conflicts"].append("missing_or_invalid_id8")
        if not isinstance(raw, dict):
            record["conflicts"].append("invalid_roster_declaration")
        out.append(record)
    seen = {}
    for row in out:
        key = row["instance_id8"]
        if not key:
            continue
        seen.setdefault(key, []).append(row)
    for ident, peers in seen.items():
        if len(peers) > 1:
            for row in peers:
                row["conflicts"].append("duplicate_id8_declared:" + ident)
    return out


def _lease(registry, row):
    ident = row["instance_id8"]
    if not ident:
        return None
    possible = registry.get("writer_leases") or registry.get("leases") or []
    for lease in possible if isinstance(possible, list) else []:
        if not isinstance(lease, dict):
            continue
        actor = str(lease.get("actor") or lease.get("holder") or "")
        if ident == actor or re.search(r"(?<![0-9a-f])" + ident + r"(?![0-9a-f])", actor):
            return lease
    return row.get("grant") if isinstance(row.get("grant"), dict) else None


def _authority(registry, row, now, uem):
    if row["retired"]:
        return {"state": "blocked", "reason": "retired"}
    if row["standby"]:
        return {"state": "waiting", "reason": "standby_not_execution_authority"}
    if row.get("material_release") is False:
        return {"state": "blocked", "reason": "material_release_not_granted"}
    lease = _lease(registry, row)
    if not isinstance(lease, dict):
        return {"state": "unknown", "reason": "execution_grant_not_verified"}
    recorded = lease.get("state", "")
    if any(token in str(recorded).upper() for token in ("RETIRED", "FROZEN", "STOP", "HOLD")):
        return {"state": "blocked", "reason": "writer_lease_not_active"}
    expires = _stamp(lease.get("expires_at") or lease.get("until"))
    if expires is not None and expires <= now:
        return {"state": "blocked", "reason": "execution_grant_expired"}
    if lease.get("verified") is not True and lease.get("branch_base_qualified") is not True:
        return {"state": "unknown", "reason": "execution_grant_not_verified"}
    budget = {"state": "unknown", "reason": "uem_not_enabled"}
    if isinstance(uem, dict) and uem.get("enabled") is True:
        limit = uem.get("max_cycles")
        agent = (uem.get("agents") or {}).get(row["instance_id8"]) or {}
        consumed = agent.get("cycle", 0)
        if type(limit) is int and 1 <= limit <= 5 and type(consumed) is int:
            if consumed >= limit:
                budget = {"state": "waiting", "reason": "uem_cycle_limit_reached"}
            else:
                budget = {"state": "available", "reason": "uem_cycle_remaining"}
    if budget["state"] == "waiting":
        return {"state": "waiting", "reason": budget["reason"], "uem_budget": budget}
    return {"state": "allowed", "reason": "source_verified_grant",
            "uem_budget": budget}


def derive_status(row, registry, project_view, now=None):
    """Three separate dimensions and a fail-closed light; no guessed green."""
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError("now_must_be_timezone_aware")
    next_view = project_view.get("next_move") or {}
    uem = next_view.get("ultra_economy") or {}
    observation = row.get("observation")
    work = str(row.get("work_state") or "").lower()
    if row["retired"]:
        work_state = {"state": "blocked", "reason": "retired"}
    elif any(token in work for token in ("blocked", "cancelled", "failed", "stop")):
        work_state = {"state": "blocked", "reason": "work_blocked"}
    elif row["complete"]:
        work_state = {"state": "complete", "reason": "complete_separate_from_light"}
    elif row["standby"] or "wait" in work or "pending" in work:
        work_state = {"state": "waiting", "reason": "waiting"}
    elif isinstance(observation, dict) and str(observation.get("state")).upper() == "WORKING" and observation.get("reachable") is True:
        seen = _stamp(observation.get("observed_at"))
        work_state = ({"state": "running", "reason": "fresh_observed_work"}
                      if seen and timedelta(0) <= now - seen <= timedelta(minutes=30)
                      else {"state": "unknown", "reason": "activity_observation_stale"})
    else:
        work_state = {"state": "unknown", "reason": "status_claim_not_fresh_activity"}
    evaluated = (_stamp(row.get("last_evaluation")) or
                 _stamp((row.get("monitoring") or {}).get("last_evaluation")
                        if isinstance(row.get("monitoring"), dict) else None) or
                 _stamp(next_view.get("evaluator_at")))
    if evaluated is None:
        monitor = {"state": "unknown", "last_evaluation": None,
                   "next_due": None, "reason": "no_recorded_evaluation"}
    else:
        due = evaluated + timedelta(minutes=30)
        monitor = {"state": "fresh" if timedelta(0) <= now-evaluated <= timedelta(minutes=30) else "stale",
                   "last_evaluation": evaluated.isoformat(),
                   "next_due": due.isoformat(),
                   "reason": "recorded_evaluator_cycle"}
    authority = _authority(registry, row, now, uem)
    control = registry.get("control") or {}
    if control.get("hold"):
        light, reason = "grey", "project_HOLD"
    elif row["conflicts"]:
        light, reason = "red", "roster_conflict"
    elif work_state["state"] == "blocked" or authority["state"] == "blocked":
        light, reason = "red", "work_or_authority_blocked"
    elif work_state["state"] == "running" and monitor["state"] == "fresh" and authority["state"] == "allowed":
        light, reason = "green", "all_three_dimensions_verified"
    else:
        light, reason = "yellow", "waiting_stale_or_unknown"
    return {**row, "light": light, "light_reason": reason,
            "dimensions": {"work": work_state, "monitoring": monitor,
                           "execution_authority": authority}}


def build_status_bar(registries, project_views, now=None):
    """One projection feeds OT and TC. 100% selected-roster coverage is checked."""
    now = now or datetime.now(timezone.utc)
    if len(registries) != len(set(registries)):
        raise ValueError("selected_registry_duplicate")
    instances, projects = [], []
    expected = []
    for project in sorted(registries):
        registry = registries[project]
        if registry.get("project") != project:
            raise ValueError("registered_project_name_mismatch:" + project)
        roster = normalize_roster(registry)
        expected += [row["key"] for row in roster]
        view = project_views.get(project) or {}
        scoped = [derive_status(row, registry, view, now) for row in roster]
        instances.extend(scoped)
        active = [row for row in scoped if not row["retired"] and not row["standby"]]
        streams = registry.get("workstreams") or {}
        dependency_blocks = [
            name for name, ws in (streams.items() if isinstance(streams, dict) else [])
            if isinstance(ws, dict) and (
                "HOLD" in str(ws.get("state", "")).upper()
                or ws.get("material_release") is False)]
        explicit_deps = registry.get("dependencies") or []
        unknown_deps = ([str(dep) for dep in explicit_deps if dep not in project_views]
                        if isinstance(explicit_deps, list) else ["invalid_dependency_shape"])
        selected_complete = len(roster) == len(scoped) and len({x["key"] for x in scoped}) == len(scoped)
        if (registry.get("control") or {}).get("hold"):
            light, reason = "grey", "project_HOLD"
        elif dependency_blocks or any(a["light"] == "red" for a in active):
            light, reason = "red", "blocked_dependency_or_active_instance"
        elif (active and not unknown_deps and not dependency_blocks and
              all(a["light"] == "green" for a in active) and selected_complete):
            light, reason = "green", "all_active_instances_and_dependencies_green"
        else:
            light, reason = "yellow", "dependency_or_coverage_not_proven"
        projects.append({"project": project, "light": light, "reason": reason,
                         "complete": bool(active) and all(a["complete"] for a in active),
                         "dependencies": {"blocked": dependency_blocks,
                                          "unknown": unknown_deps},
                         "instance_count": len(scoped),
                         "active_count": len(active),
                         "historical_retired_count": sum(a["retired"] for a in scoped),
                         "selected_roster_coverage": {"expected": len(roster),
                                                      "projected": len(scoped),
                                                      "complete": selected_complete}})
    actual = [r["key"] for r in instances]
    missing = sorted(set(expected) - set(actual))
    extra = sorted(set(actual) - set(expected))
    coverage = {"expected": len(expected), "projected": len(actual),
                "complete": not missing and not extra and len(expected) == len(actual)
                            and len(actual) == len(set(actual)),
                "percent": (100 if not expected else round(100 * (len(expected) - len(missing)) / len(expected), 2)),
                "missing": missing, "extra": extra}
    if not coverage["complete"]:
        # Preserve all rows for diagnosis but never show a green project light.
        for p in projects:
            if p["light"] == "green":
                p.update(light="yellow", reason="selected_roster_incomplete")
    return {"schema": "status_bar.v1", "source": "all_registered_logs_registry_json",
            "as_of": now.isoformat(), "coverage": coverage,
            "projects": projects, "instances": instances}
