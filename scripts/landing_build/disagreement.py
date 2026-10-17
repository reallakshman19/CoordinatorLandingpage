"""G8: report source-linked disagreements; never choose a winning source."""
import re

from landing_build.evidence_parse import validated_issue_ref

_STATUS = re.compile(r"^[ \t]*STATE:[ \t]*([^\r\n]+)", re.I | re.M)
_PR = re.compile(r"https://github\.com/([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)/pull/([1-9]\d*)", re.I)
_WORDS = {"HOLD": "HOLD", "BLOCKED": "BLOCKED", "IN PROGRESS": "IN PROGRESS",
          "IN_PROGRESS": "IN PROGRESS", "DONE": "DONE"}


def latest_issue_status(registry, issue, control_repo):
    ref = validated_issue_ref(registry.get("status_comment") or
                              registry.get("status_issue"), registry, control_repo)
    if not ref or not isinstance(issue, dict):
        return None
    if (issue.get("repository") and
            issue["repository"].lower() != ref[0].lower()):
        return None
    url = f"https://github.com/{ref[0]}/issues/{ref[1]}"
    candidates = []
    body = issue.get("body")
    if isinstance(body, str):
        for match in _STATUS.finditer(body):
            candidates.append(("", 0, match.group(1).strip(), url))
    for entry in issue.get("comments", []):
        if not isinstance(entry, dict) or not isinstance(entry.get("body"), str):
            continue
        stamp = entry.get("created_at") or ""
        cid = entry.get("id")
        for match in _STATUS.finditer(entry["body"]):
            candidates.append((stamp, cid if isinstance(cid, int) else 0,
                               match.group(1).strip(),
                               url + (f"#issuecomment-{cid}" if isinstance(cid, int) else "")))
    if not candidates:
        return None
    _, _, raw, link = max(candidates, key=lambda row: (row[0], row[1]))
    return {"word": _WORDS.get(" ".join(raw.upper().split())), "raw": raw,
            "url": link}


def project_disagreement(registry, status_issue, pr_snapshots, control_repo):
    """Compare only verified registered PR snapshots against explicit issue text."""
    if not isinstance(pr_snapshots, list) or not pr_snapshots:
        return None  # No PR does not imply agreement.
    own_repo = str(registry.get("repository") or "").lower()
    linked = []
    for record in pr_snapshots:
        if not isinstance(record, dict):
            continue
        match = _PR.fullmatch(str(record.get("url") or ""))
        if not match or match.group(1).lower() != own_repo:
            continue
        if str(record.get("repository") or "").lower() != own_repo:
            continue
        state = str(record.get("state") or "").lower()
        if record.get("merged_at"):
            pr_state = "MERGED"
        elif state == "open":
            pr_state = "OPEN"
        elif state == "closed":
            pr_state = "CLOSED_UNMERGED"
        else:
            pr_state = "UNKNOWN"
        linked.append({"url": match.group(0), "pr_status": pr_state})
    if not linked:
        return None
    found = latest_issue_status(registry, status_issue, control_repo)
    word = found["word"] if found else None
    conflicting = False
    for record in linked:
        state = record["pr_status"]
        contradicts = bool(
            (word == "DONE" and state in ("OPEN", "CLOSED_UNMERGED")) or
            (word in ("HOLD", "BLOCKED", "IN PROGRESS") and state == "MERGED"))
        record["comparison"] = ("CONTRADICTION" if contradicts else
                                "UNDETERMINED" if not word or state == "UNKNOWN"
                                else "NOT_CONTRADICTORY")
        conflicting |= contradicts
    return {"status": ("DISAGREEMENT" if conflicting else
                       "UNKNOWN" if not word or all(x["pr_status"] == "UNKNOWN"
                                                     for x in linked)
                       else "NO_DISAGREEMENT"),
            "flag": conflicting, "issue_status": word,
            "issue_status_raw": found["raw"] if found else None,
            "issue_url": found["url"] if found else None,
            "prs": linked}
