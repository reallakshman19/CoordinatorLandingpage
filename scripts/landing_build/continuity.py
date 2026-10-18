"""WP-L6 fourth dimension: conservative source-linked project continuity.

Does not modify legacy work, monitoring or execution-authority lights.
A capture observation is not proof that every off-platform Owner input exists.
"""
from collections.abc import Mapping
from landing_build.freshness import _utc_time

ORDER = ("intent_linked", "originals_declared", "owner_input_captured",
         "lineage_verified", "head_fresh")
BAD_LINEAGE = {"INACCESSIBLE", "REJECTED", "FOREIGN", "FOREIGN_REPOSITORY", "ERROR"}
VALID_ORIGINAL = {"ORIGINAL", "SYNTHETIC", "PARTIAL", "MISSING"}


def _item(state="UNKNOWN", source=None, reason=None, **additional):
    return {"state": state, "source": source,
            "reason": reason or "not_recorded", **additional}



AMENDMENT_NOTICE = "amendment after checkpoint: reconcile before continuing"


def assess_amendment_checkpoint(amendments, checkpoint):
    """Compare bounded captured #1 records with a source-attested cycle.

    A capture is not a checkpoint. Equal times do not prove a later cycle.
    Never infer a newer checkpoint from wall-clock time or the build date.
    """
    if not isinstance(amendments, Mapping):
        return {"status": "NOT_RECORDED", "markers": []}
    source = amendments.get("source")
    state, rows = amendments.get("status"), amendments.get("records")
    if state == "NONE_FOUND" and rows == []:
        return {"status": "NONE_FOUND", "markers": []}
    if state != "AVAILABLE" or not isinstance(rows, list) or not rows:
        return {"status": "UNKNOWN", "reason": "amendment_capture_unknown",
                "source": source, "markers": []}
    when = _utc_time(checkpoint)
    pending, uncertain = [], []
    for row in rows:
        item = row if isinstance(row, Mapping) else {}
        ts = _utc_time(item.get("created_at"))
        if not ts or not when:
            uncertain.append(item.get("source") or source)
        elif ts >= when:  # A checkpoint must be strictly AFTER the change.
            pending.append({"text": AMENDMENT_NOTICE,
                            "source": item.get("source") or source,
                            "created_at": item["created_at"],
                            "checkpoint_at": checkpoint})
    if pending:
        pending.sort(key=lambda x: _utc_time(x["created_at"]))
        return {"status": "UNRECONCILED", "checkpoint_at": checkpoint,
                "source": pending[-1]["source"], "markers": pending}
    if uncertain or amendments.get("truncated"):
        return {"status": "UNKNOWN",
                "reason": "amendment_or_checkpoint_time_unknown"
                          if uncertain else "amendment_list_truncated",
                "source": next((s for s in uncertain if s), source),
                "checkpoint_at": checkpoint, "markers": []}
    return {"status": "RECONCILED", "checkpoint_at": checkpoint,
            "source": source, "markers": []}


def derive_continuity(registry, project_view):
    """One independently attributable record per input, no inferred winner."""
    registry = registry if isinstance(registry, Mapping) else {}
    view = project_view if isinstance(project_view, Mapping) else {}
    lineage = view.get("lineage")
    entries = lineage if isinstance(lineage, list) else []
    declared_parent = registry.get("parent_issue")
    parent = next((v for v in entries
                   if isinstance(v, Mapping) and v.get("kind") == "parent_issue"), None)
    if parent and parent.get("status") == "AVAILABLE" and declared_parent:
        intent = _item("OK", parent.get("url") or declared_parent,
                       "registered_parent_fetched")
    elif parent and parent.get("status") in BAD_LINEAGE:
        intent = _item("PROBLEM", parent.get("reference") or declared_parent,
                       "parent_not_verified")
    else:
        intent = _item(source=declared_parent, reason="parent_not_observed")

    originals = view.get("originals")
    refs = view.get("source_refs")
    refs = refs if isinstance(refs, Mapping) else {}
    if not isinstance(originals, list) or not originals:
        invalid = isinstance(originals, Mapping) and originals.get("status") == "ERROR"
        origin = _item("PROBLEM" if invalid else "UNKNOWN", refs.get("status_issue"),
                       "source_inventory_invalid" if invalid else "source_inventory_unknown")
    else:
        issues = [v for v in originals if not isinstance(v, Mapping)
                  or v.get("status") == "ERROR"
                  or v.get("class") not in VALID_ORIGINAL]
        missing = [str(v.get("name") or "UNKNOWN") for v in originals
                   if isinstance(v, Mapping) and v.get("class") == "MISSING"]
        origin = _item("PROBLEM" if issues or missing else "OK", refs.get("status_issue"),
                       "missing_original" if missing else
                       "source_inventory_error" if issues else "declared_originals",
                       missing=missing)

    health = view.get("source_health")
    health = health if isinstance(health, Mapping) else {}
    errors = health.get("errors")
    succession = view.get("succession")
    succession = succession if isinstance(succession, Mapping) else {}
    interval = succession.get("unrecorded_interval")
    gaps = bool(isinstance(interval, Mapping) and
                any(interval.get(k) for k in ("from_checkpoint", "to_departure")))
    known_unparsed = bool(view.get("unparsed_evidence"))
    errored = health.get("status") in ("degraded", "error", "failed")
    if gaps or known_unparsed or errored or (isinstance(errors, list) and errors):
        owner = _item("PROBLEM", refs.get("inbox"),
                      "unrecorded_or_unparsed_evidence" if gaps or known_unparsed
                      else "incomplete_source_capture")
    elif health.get("status") == "ok" and errors == [] and refs.get("inbox"):
        owner = _item("OK", refs.get("inbox"), "no_capture_gap_observed")
    else:
        owner = _item(source=refs.get("inbox"), reason="owner_input_capture_unknown")

    # A fetched amendment after the last completed coordinator cycle is
    # not captured *by that checkpoint*. This overrides "source fetch OK".
    check = assess_amendment_checkpoint(view.get("amendments"),
                                        view.get("last_cycle_at"))
    if check["status"] == "UNRECONCILED":
        owner = _item("PROBLEM", check["source"], "post_checkpoint_owner_amendment",
                      created_at=check["markers"][-1]["created_at"],
                      checkpoint_at=check["checkpoint_at"],
                      unreconciled=check["markers"])
    elif check["status"] == "UNKNOWN" and owner["state"] != "PROBLEM":
        owner = _item(source=check.get("source") or refs.get("inbox"),
                      reason=check.get("reason") or "amendment_time_unknown")

    if not entries:
        ln = _item(reason="lineage_not_observed")
    elif any(isinstance(v, Mapping) and v.get("status") in BAD_LINEAGE
             for v in entries) or any(not isinstance(v, Mapping) for v in entries):
        bad = next((v for v in entries if not isinstance(v, Mapping)
                    or v.get("status") in BAD_LINEAGE), None)
        ln = _item("PROBLEM", bad.get("reference") if isinstance(bad, Mapping) else None,
                   "lineage_rejected_or_inaccessible")
    elif all(v.get("status") == "AVAILABLE" for v in entries):
        ln = _item("OK", entries[0].get("url"), "all_lineage_records_available")
    else:
        ln = _item(source=entries[0].get("reference"),
                   reason="lineage_pending_or_unverified")

    freshness = view.get("freshness_status")
    status_source = refs.get("status_issue")
    if freshness == "RUNNING-observed":
        fresh = _item("OK", status_source, "recorded_cycle_within_freshness_window")
    elif freshness in ("STALE", "HOLD"):
        fresh = _item("PROBLEM", status_source, "existing_freshness_" + freshness.lower())
    else:
        fresh = _item(source=status_source, reason="freshness_unknown")

    inputs = dict(zip(ORDER, (intent, origin, owner, ln, fresh)))
    states = [v["state"] for v in inputs.values()]
    light = "red" if "PROBLEM" in states else (
        "green" if all(v == "OK" for v in states) else "grey")
    return {"light": light, "inputs": inputs}
