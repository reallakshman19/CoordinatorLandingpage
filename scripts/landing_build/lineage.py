"""Read-only G3 issue-lineage classification; networking stays in fetch_live_data."""
import json
import re
from landing_build.evidence_parse import validated_issue_ref

_ISSUE_SHAPE = re.compile(
    r"https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/issues/[1-9]\d*"
    r"(?:#issuecomment-\d+)?", re.I)


def plan_lineage(registry, control_repo):
    """Preserve each declared pointer, including rejected or malformed entries."""
    entries = []
    if "parent_issue" in registry:
        entries.append(("parent_issue", registry["parent_issue"]))
    if "history_refs" in registry:
        history = registry["history_refs"]
        if not isinstance(history, list):
            history = [history]  # A malformed collection must remain visible.
        entries.extend(("history_ref", item) for item in history)
    output = []
    for kind, value in entries:
        link = value.get("url") if isinstance(value, dict) and "url" in value else value
        ref = validated_issue_ref(link, registry, control_repo)
        display = (link if isinstance(link, str) else
                   json.dumps(link, ensure_ascii=False, sort_keys=True))
        row = {"kind": kind, "reference": display}
        if ref:
            row.update(status="PENDING", repository=ref[0],
                       issue_number=ref[1])
        elif isinstance(link, str) and _ISSUE_SHAPE.fullmatch(link.strip()):
            row.update(status="REJECTED", reason="FOREIGN_REPOSITORY")
        else:
            row.update(status="ERROR", reason="MALFORMED_REFERENCE")
        output.append(row)
    return output


def finish_lineage(row, issue):
    """A failed GET proves only INACCESSIBLE, never deletion."""
    repo, number = row["repository"], row["issue_number"]
    canonical = f"https://github.com/{repo}/issues/{number}"
    if (not isinstance(issue, dict) or issue.get("number") != number
            or issue.get("html_url") != canonical
            or issue.get("pull_request")
            or (issue.get("repository") and
                str(issue["repository"]).lower() != repo.lower())):
        row.update(status="INACCESSIBLE", reason="NOT_OBSERVABLE")
        return row
    row.update(status="AVAILABLE", url=canonical,
               title=issue.get("title") or "",
               issue_state=issue.get("state") or "UNKNOWN",
               updated_at=issue.get("updated_at"))
    if row.get("kind") == "parent_issue" and isinstance(issue.get("body"), str):
        # WP-L2(c) has already fetched this exact verified parent; never
        # issue a second GET just to populate the cold-reader view.
        body = issue["body"]
        row["body_excerpt"] = body[:1600]
        row["body_truncated"] = len(body) > 1600
    return row
