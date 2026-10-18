"""WP-V1 cold-reader: project only already-captured root body and #1 records.

Neither function performs provider reads or treats a shared GitHub author as
proof of an Owner decision. Keep the source and truncation visible.
"""
import re
from landing_build.continuity import assess_amendment_checkpoint

MAX_AMENDMENTS = 25
MAX_COMMENT_CHARS = 900
CONTROL_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
ASSOCIATED = {"OWNER", "MEMBER", "COLLABORATOR"}


def _intent(registry, lineage):
    expected = registry.get("parent_issue")
    rows = lineage if isinstance(lineage, list) else []
    parent = next((r for r in rows if isinstance(r, dict)
                   and r.get("kind") == "parent_issue"
                   and r.get("status") == "AVAILABLE"
                   and r.get("url") == expected), None)
    if parent is None:
        return {"status": "UNKNOWN", "reason": "parent_issue_not_fetched",
                "source": expected if isinstance(expected, str) else None}
    text = parent.get("body_excerpt")
    if not isinstance(text, str) or not text.strip():
        return {"status": "UNKNOWN", "reason": "parent_body_not_captured",
                "source": expected}
    return {"status": "AVAILABLE", "text": text,
            "truncated": parent.get("body_truncated") is True,
            "limit_chars": 1600, "source": expected}


def _amendments(project, inbox, fetched, control_repo):
    prefix = ("https://github.com/" + control_repo + "/issues/1"
              if isinstance(control_repo, str)
              and CONTROL_PATTERN.fullmatch(control_repo) else None)
    if not fetched or not isinstance(inbox, list) or not prefix:
        return {"status": "UNKNOWN", "reason": "inbox_1_not_fetched",
                "records": [], "source": prefix}
    # Match an exact project label; 'landing-live-other' is a distinct project.
    marker = re.compile(r"(?<![A-Za-z0-9_.-])" + re.escape(project) +
                        r"(?![A-Za-z0-9_.-])", re.I)
    matching, records = 0, []
    for item in inbox:
        if not isinstance(item, dict):
            continue
        body, ident = item.get("body"), item.get("id")
        if not isinstance(body, str) or not marker.search(body):
            continue
        matching += 1
        if not isinstance(ident, int) or isinstance(ident, bool) or ident <= 0:
            continue
        # GitHub returns comments oldest-first; a cold reader needs the
        # latest corrections, while we disclose the omitted earlier count.
        if len(records) >= MAX_AMENDMENTS:
            records.pop(0)
        assoc = item.get("author_association")
        records.append({
            "comment_id": ident,
            "source": prefix + "#issuecomment-" + str(ident),
            "text": body[:MAX_COMMENT_CHARS],
            "truncated": len(body) > MAX_COMMENT_CHARS,
            "created_at": item.get("created_at"),
            "superseded": bool(re.search(r"\bsupersed", body, re.I)),
            "attribution": ("ASSOCIATED_NOT_OWNER_PROOF" if assoc in ASSOCIATED
                            else "UNVERIFIED_AUTHOR"),
            "source_kind": "project_referenced_inbox_record",
        })
    state = ("UNKNOWN" if matching > 0 and not records else
             "AVAILABLE" if records else "NONE_FOUND")
    return {
        "status": state, "source": prefix,
        "reason": ("matching_records_lack_usable_comment_ids"
                   if state == "UNKNOWN" else None),
        "total_matching": matching, "truncated": matching > len(records),
        "records": records,
        "note": "Project-referenced #1 records, not proof of an Owner amendment or approval",
    }


def project_intake(project, registry, lineage, inbox, inbox_fetched, control_repo,
                   last_cycle_at=None):
    """No fetches; bind the project amendment marker to its real checkpoint."""
    amendments = _amendments(project, inbox, inbox_fetched, control_repo)
    return {
        "intent": _intent(registry if isinstance(registry, dict) else {}, lineage),
        "amendments": amendments,
        "amendment_checkpoint": assess_amendment_checkpoint(amendments, last_cycle_at),
    }
