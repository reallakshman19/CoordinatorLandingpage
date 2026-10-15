#!/usr/bin/env python3
"""
fetch_live_data.py — Fetch live GitHub issue threads for Team Protocol projects.

Run this from the GHA workflow BEFORE build_data.py.
Writes fetched thread JSON files to --cache-dir (default: _live_cache/).
The GITHUB_TOKEN is consumed by `gh api` via environment; it is never
written to any file or printed.

Usage (workflow):
  python scripts/fetch_live_data.py \
      --root . \
      --repo reallakshman19/CoordinatorLandingpage \
      --cache-dir _live_cache

The script reads every registry.json under logs/*/registry.json, collects
evidence_thread URLs and status_issue / status_comment URLs, and fetches
the corresponding issues (with all comments, paginated) via `gh api`.

Output layout (inside cache-dir):
  threads/issue-<N>.json   — same shape as benchmark thread files
  inbox-1.json             — comments from the status/inbox issue
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO = ""  # Set from --repo arg


def gh_api(path: str) -> list | dict | None:
    """Call `gh api PATH --paginate` and return parsed JSON."""
    try:
        result = subprocess.run(
            ["gh", "api", "--paginate", path],
            capture_output=True, text=True, check=True
        )
        raw = result.stdout.strip()
        if not raw:
            return None
        # --paginate may emit multiple JSON arrays; join them
        # gh concatenates multiple pages as separate JSON arrays
        # We reassemble into one list
        items = []
        decoder = json.JSONDecoder()
        pos = 0
        while pos < len(raw):
            # Skip whitespace
            while pos < len(raw) and raw[pos] in ' \t\n\r':
                pos += 1
            if pos >= len(raw):
                break
            obj, end = decoder.raw_decode(raw, pos)
            if isinstance(obj, list):
                items.extend(obj)
            else:
                items.append(obj)
            pos = end
        return items if items else None
    except subprocess.CalledProcessError as e:
        print(f"  gh api error for {path}: {e.stderr.strip()[:200]}", file=sys.stderr)
        return None


def fetch_issue(repo: str, number: int) -> dict | None:
    """Fetch a single issue with all its comments."""
    issue = gh_api(f"/repos/{repo}/issues/{number}")
    if not issue:
        return None
    # issue is a list with one item (because --paginate on single resource)
    issue_obj = issue[0] if isinstance(issue, list) else issue

    comments = gh_api(f"/repos/{repo}/issues/{number}/comments") or []

    return {
        "number": number,
        "title": issue_obj.get("title", ""),
        "body": issue_obj.get("body", ""),
        "state": issue_obj.get("state", ""),
        "created_at": issue_obj.get("created_at", ""),
        "updated_at": issue_obj.get("updated_at", ""),
        "html_url": issue_obj.get("html_url", ""),
        "comments": [
            {
                "id": c.get("id"),
                "created_at": c.get("created_at", ""),
                "updated_at": c.get("updated_at", ""),
                "body": c.get("body", ""),
                "author_association": c.get("author_association", ""),
            }
            for c in comments
        ],
    }


def extract_issue_number(url: str) -> int | None:
    """Extract issue number from a GitHub issues URL."""
    import re
    m = re.search(r"/issues/(\d+)", url or "")
    return int(m.group(1)) if m else None


def save_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  wrote {path}")


def main():
    parser = argparse.ArgumentParser(description="Fetch live GitHub thread data")
    parser.add_argument("--root", default=".", help="Repository root")
    parser.add_argument("--repo", required=True, help="owner/repo slug")
    parser.add_argument("--cache-dir", default="_live_cache",
                        help="Output directory for fetched JSON")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    cache = Path(args.cache_dir)
    if not cache.is_absolute():
        cache = root / cache
    repo = args.repo

    logs_root = root / "logs"
    if not logs_root.exists():
        print(f"No logs/ dir found at {logs_root} — nothing to fetch.", file=sys.stderr)
        sys.exit(0)

    # Collect all issue numbers to fetch across all projects
    issue_numbers: set[int] = set()
    inbox_issue_number: int | None = None

    for registry_path in sorted(logs_root.rglob("registry.json")):
        registry = json.loads(registry_path.read_text(encoding="utf-8"))

        # Agent evidence threads
        for agent in registry.get("agents", []):
            n = extract_issue_number(agent.get("evidence_thread", ""))
            if n:
                issue_numbers.add(n)

        # Status / inbox issue (the coordinator posts COORDINATOR EVIDENCE here)
        status_url = registry.get("status_comment") or registry.get("status_issue", "")
        n = extract_issue_number(status_url)
        if n:
            inbox_issue_number = n
            issue_numbers.add(n)

    if not issue_numbers:
        print("No issue numbers found in registries — nothing to fetch.", file=sys.stderr)
        sys.exit(0)

    print(f"Fetching {len(issue_numbers)} issues from {repo}: {sorted(issue_numbers)}")

    threads_dir = cache / "threads"
    for num in sorted(issue_numbers):
        print(f"  Fetching issue #{num}...")
        data = fetch_issue(repo, num)
        if data:
            save_json(threads_dir / f"issue-{num}.json", data)
        else:
            print(f"  WARNING: could not fetch issue #{num}", file=sys.stderr)

    # Write inbox-1.json: comments from the status issue, if any
    if inbox_issue_number:
        inbox_path = threads_dir / f"issue-{inbox_issue_number}.json"
        if inbox_path.exists():
            inbox_data = json.loads(inbox_path.read_text(encoding="utf-8"))
            inbox_comments = inbox_data.get("comments", [])
            save_json(cache / "inbox-1.json", inbox_comments)
            print(f"  wrote inbox-1.json from issue #{inbox_issue_number} "
                  f"({len(inbox_comments)} comments)")

    print("Done.")


if __name__ == "__main__":
    main()
