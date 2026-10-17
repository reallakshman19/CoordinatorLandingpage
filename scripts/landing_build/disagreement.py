"""G8: report source-linked disagreements; never choose a winning source."""
import re

from landing_build.evidence_parse import validated_issue_ref

_STATUS = re.compile(r"^[ \t]*STATE:[ \t]*([^\r\n]+)", re.I | re.M)
_PR = re.compile(r"https://github\.com/([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)/pull/([1-9]\d*)", re.I)
_WORDS = {"HOLD": "HOLD", "BLOCKED": "BLOCKED", "IN PROGRESS": "IN PROGRESS",
          "IN_PROGRESS": "IN PROGRESS", "DONE": "DONE"}


def latest_issue_status(registry, issue, control_repo):
    """Use registered source first; never let an unrelated quote override it."""
    if not isinstance(issue, dict):
        return None
    source = registry.get("status_comment") or registry.get("status_issue")
    ref = validated_issue_ref(source, registry, control_repo) if source else None
    if source and not ref:
        return None
    if ref is None:
        # Fallback only when no status source was registered; retain the
        # provider-verified repository/issue identity, not a number alone.
        repo = issue.get("repository")
        if not isinstance(repo, str):
            return None
        ref = validated_issue_ref(issue.get("html_url"),
                                  {"repository": registry.get("repository")},
                                  control_repo)
        if not ref:
            return None
    repo, number = ref
    if (issue.get("repository") and
            str(issue["repository"]).lower() != repo.lower()):
        return None
    if issue.get("number") not in (None, number):
        return None
    url = f"https://github.com/{repo}/issues/{number}"

    def from_text(body, permalink):
        if not isinstance(body, str):
            return None
        matches = list(_STATUS.finditer(body))
        if not matches:
            return None
        raw = matches[-1].group(1).strip()  # Last STATE in this source wins.
        return {"word": _WORDS.get(" ".join(raw.upper().split())),
                "raw": raw, "url": permalink}

    pinned = re.search(r"#issuecomment-(\d+)$", str(source or ""))
    if pinned:
        for entry in issue.get("comments", []):
            if isinstance(entry, dict) and str(entry.get("id")) == pinned.group(1):
                return from_text(entry.get("body"),
                                 url + "#issuecomment-" + pinned.group(1))
        return None  # Missing registered comment is not replaced by a quote.

    # The registered status-issue body is authoritative when it exists.
    body = issue.get("body")
    if source and isinstance(body, str) and body.strip():
        return from_text(body, url)

    # No registered status text: newest STATE observation is a fallback only.
    candidates = []
    if isinstance(body, str):
        result = from_text(body, url)
        if result:
            candidates.append(("", 0, result))
    for entry in issue.get("comments", []):
        if not isinstance(entry, dict):
            continue
        cid = entry.get("id")
        link = url + (f"#issuecomment-{cid}" if isinstance(cid, int) else "")
        result = from_text(entry.get("body"), link)
        if result:
            candidates.append((entry.get("created_at") or "",
                               cid if isinstance(cid, int) else 0, result))
    return max(candidates, key=lambda x: (x[0], x[1]))[2] if candidates else None

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
