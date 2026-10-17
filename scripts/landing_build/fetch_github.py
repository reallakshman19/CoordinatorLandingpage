"""GitHub read-only fetch and LF-serialized cache writing, from fetch_live_data."""
from contextvars import ContextVar
import json
from pathlib import Path
import re
import subprocess
import sys

_API_ERRORS = ContextVar("gh_api_errors", default=None)


def gh_api(path: str, errors=None):
    """Return decoded resource or None; report safe HTTP/transport reason."""
    def report(reason):
        sink = errors if errors is not None else _API_ERRORS.get()
        if sink is not None:
            sink.append(f"gh_api_failure:{path}:{reason}")
    try:
        # Owner indexes are fetched with explicit page numbers, max five.
        # Never let gh --paginate silently ignore that strict upper bound.
        bounded = bool(re.search(
            r"/issues\?state=all&.*per_page=100&page=[1-5]$", path))
        command = ["gh", "api"] + ([] if bounded else ["--paginate"]) + [path]
        proc = subprocess.run(
            command,
            capture_output=True, text=True, check=True
        )
        raw = proc.stdout.strip()
        if not raw:
            report("EMPTY_RESPONSE")
            return None
        decoder = json.JSONDecoder()
        pos = 0
        pages = []
        while pos < len(raw):
            while pos < len(raw) and raw[pos].isspace():
                pos += 1
            if pos >= len(raw):
                break
            value, pos = decoder.raw_decode(raw, pos)
            pages.append(value)
        if len(pages) == 1:
            return pages[0]
        values = []
        for page in pages:
            if isinstance(page, list):
                values.extend(page)
            else:
                values.append(page)
        return values
    except (subprocess.CalledProcessError, OSError, ValueError, TypeError) as exc:
        # Never echo stderr: it might contain credentials or response bodies.
        stderr = exc.stderr if isinstance(exc, subprocess.CalledProcessError) else ""
        match = re.search(r"(?i)\bHTTP(?:\s+error)?[\s:=-]*([45]\d{2})\b",
                          stderr if isinstance(stderr, str) else "")
        reason = ("HTTP_" + match.group(1) if match else
                  "TRANSPORT_ERROR" if isinstance(exc, OSError) else
                  "INVALID_RESPONSE" if isinstance(exc, (ValueError, TypeError))
                  else "API_FAILURE")
        report(reason)
        print(f"  fetch failed for {path}: {reason}", file=sys.stderr)
        return None


def fetch_issue(repo: str, number: int, *, api=None):
    """Return issue and complete comments; never mistake missing comments for []."""
    api = api or gh_api
    issue = api(f"/repos/{repo}/issues/{number}")
    if isinstance(issue, list):
        issue = issue[0] if len(issue) == 1 else None
    if not isinstance(issue, dict):
        return None
    comments = api(f"/repos/{repo}/issues/{number}/comments")
    if not isinstance(comments, list):
        return None
    return {
        "number": number,
        "repository": repo,
        "id": issue.get("id"),
        "title": issue.get("title", ""),
        "body": issue.get("body", ""),
        "state": issue.get("state", ""),
        "created_at": issue.get("created_at", ""),
        "updated_at": issue.get("updated_at", ""),
        "html_url": issue.get("html_url", ""),
        "author_association": issue.get("author_association", ""),
        "comments": [
            {"id": c.get("id"), "created_at": c.get("created_at", ""),
             "updated_at": c.get("updated_at", ""),
             "body": c.get("body", ""),
             "author_association": c.get("author_association", "")}
            for c in comments if isinstance(c, dict)
        ],
    }


def save_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8", newline="\n")


