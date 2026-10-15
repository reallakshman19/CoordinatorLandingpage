#!/usr/bin/env python3
"""Fetch public GitHub projection sources for Team Protocol projects.

Issue #1 is the protocol inbox, independently of every project's status issue.
Only the explicitly named control repository is fetched. This script sends no
instructions, modifies no GitHub content and never treats a fetch failure as
successful observation.
"""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from urllib.parse import urlparse


def gh_api(path: str):
    """Return a decoded GitHub API resource, or None on transport/JSON failure."""
    try:
        proc = subprocess.run(
            ["gh", "api", "--paginate", path],
            capture_output=True, text=True, check=True
        )
        raw = proc.stdout.strip()
        if not raw:
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
        # Do not print API response bodies or credentials.
        print(f"  fetch failed for {path}: {type(exc).__name__}", file=sys.stderr)
        return None


def fetch_issue(repo: str, number: int):
    """Return issue and complete comments; never mistake missing comments for []."""
    issue = gh_api(f"/repos/{repo}/issues/{number}")
    if isinstance(issue, list):
        issue = issue[0] if len(issue) == 1 else None
    if not isinstance(issue, dict):
        return None
    comments = gh_api(f"/repos/{repo}/issues/{number}/comments")
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
        "comments": [
            {"id": c.get("id"), "created_at": c.get("created_at", ""),
             "updated_at": c.get("updated_at", ""),
             "body": c.get("body", ""),
             "author_association": c.get("author_association", "")}
            for c in comments if isinstance(c, dict)
        ],
    }


def extract_issue_number(url: str, repo: str | None = None):
    """Accept only a real issues URL, optionally fenced to the control repo."""
    if not isinstance(url, str):
        return None
    m = re.fullmatch(
        r"https://github\.com/([^/]+/[^/]+)/issues/(\d+)(?:#.*)?",
        url.strip(), flags=re.IGNORECASE
    )
    if not m or (repo and m.group(1).lower() != repo.lower()):
        return None
    return int(m.group(2))


def save_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8")


def discover_sources(root: Path, repo: str):
    """Registry-controlled source IDs. Inbox #1 is deliberately NOT inferred."""
    issue_numbers = {1}
    statuses = {}
    errors = []
    logs_root = root / "logs"
    for registry_path in sorted(logs_root.glob("*/registry.json")):
        project = registry_path.parent.name
        try:
            registry = json.loads(registry_path.read_text(encoding="utf-8"))
            if not isinstance(registry, dict):
                raise ValueError("registry is not an object")
        except (OSError, ValueError) as exc:
            errors.append(f"registry_invalid:{project}:{type(exc).__name__}")
            continue
        if registry.get("project") and registry["project"] != project:
            errors.append(f"registry_project_mismatch:{project}")
            continue
        status_url = registry.get("status_comment") or registry.get("status_issue") or ""
        if status_url:
            status_no = extract_issue_number(status_url, repo)
            if status_no is None:
                errors.append(f"status_reference_invalid:{project}")
            else:
                statuses[project] = status_no
                issue_numbers.add(status_no)
        for agent in registry.get("agents", []):
            if not isinstance(agent, dict):
                errors.append(f"agent_reference_invalid:{project}")
                continue
            ref = agent.get("evidence_thread", "")
            if ref:
                number = extract_issue_number(ref, repo)
                if number is None:
                    errors.append(f"evidence_reference_invalid:{project}")
                else:
                    issue_numbers.add(number)
    return issue_numbers, statuses, errors



def issue_ref(url: str, product_repo: str, control_repo: str):
    """Explicit URL repository wins; never resolve only the issue number.

    A project's registry can point at its PRODUCT repo or the control hub.
    Other repositories are not authorized data sources.
    """
    m = re.fullmatch(
        r"https://github\.com/([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)/issues/(\d+)"
        r"(?:#issuecomment-\d+)?",
        str(url or "").strip(), flags=re.IGNORECASE,
    )
    if not m:
        return None
    chosen = m.group(1)
    if chosen.lower() not in {product_repo.lower(), control_repo.lower()}:
        return None
    return chosen, int(m.group(2))


def discover_project_refs(root: Path, control_repo: str):
    """Scope each project by its registry product repo, and each link by URL."""
    projects, refs, errors = {}, {(control_repo, 1)}, []
    for path in sorted((root / "logs").glob("*/registry.json")):
        project = path.parent.name
        try:
            registry = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(registry, dict) or (registry.get("project") and
                                                  registry["project"] != project):
                raise ValueError("registry/project mismatch")
            product = registry.get("repository")
            if not isinstance(product, str) or not re.fullmatch(
                    r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", product):
                raise ValueError("product repository invalid")
        except (OSError, ValueError) as exc:
            errors.append(f"registry_invalid:{project}:{type(exc).__name__}")
            continue
        status_url = registry.get("status_comment") or registry.get("status_issue") or ""
        status = issue_ref(status_url, product, control_repo) if status_url else None
        if status_url and status is None:
            errors.append(f"status_reference_invalid:{project}")
        named = set()
        if status:
            named.add(status)
        for agent in registry.get("agents", []):
            if not isinstance(agent, dict):
                errors.append(f"agent_reference_invalid:{project}")
                continue
            url = agent.get("evidence_thread", "")
            if not url:
                continue
            pointer = issue_ref(url, product, control_repo)
            if pointer is None:
                errors.append(f"evidence_reference_invalid:{project}")
            else:
                named.add(pointer)
        refs.update(named)
        projects[project] = {"repository": product,
                             "status": status, "threads": sorted(named)}
    return projects, refs, errors


def main():
    parser = argparse.ArgumentParser(description="Fetch read-only issue projections")
    parser.add_argument("--root", default=".")
    parser.add_argument("--repo", required=True)
    parser.add_argument("--cache-dir", default="_live_cache")
    args = parser.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", args.repo):
        parser.error("--repo must be owner/repo")

    root = Path(args.root).resolve()
    cache = Path(args.cache_dir)
    cache = (cache if cache.is_absolute() else root / cache).resolve()
    if cache == root or cache == root / "logs":
        parser.error("--cache-dir must not be repository root/logs")
    cache.mkdir(parents=True, exist_ok=True)
    threads_dir = cache / "threads"
    threads_dir.mkdir(parents=True, exist_ok=True)
    scoped_dir = cache / "project-threads"
    if scoped_dir.exists():
        shutil.rmtree(scoped_dir)
    scoped_dir.mkdir(parents=True)
    # Never replay an earlier successful cache object as a fresh capture.
    for path in threads_dir.glob("issue-*.json"):
        path.unlink()
    for path in list(cache.glob("status-*.json")) + [
        cache / "inbox-1.json", cache / "capture-info.json",
        cache / "owner-inputs-source.json"
    ]:
        if path.exists():
            path.unlink()

    project_refs, all_refs, errors = discover_project_refs(root, args.repo)
    captured_at = datetime.now(timezone.utc).isoformat()
    fetched = {}
    # A (repo, number) pair is the immutable identity. 12@product-A is not
    # 12@product-B and neither may be substituted for 12@control-hub.
    for chosen_repo, number in sorted(all_refs):
        item = fetch_issue(chosen_repo, number)
        if item is None:
            message = (f"issue_fetch_failed:{number}" if chosen_repo == args.repo
                       else f"issue_fetch_failed:{chosen_repo}:{number}")
            errors.append(message)
            continue
        # Never trust a response bearing a different repository or issue id.
        if item.get("number") != number or (
                item.get("repository") and
                item["repository"].lower() != chosen_repo.lower()):
            errors.append(f"issue_identity_mismatch:{chosen_repo}:{number}")
            continue
        item["repository"] = chosen_repo
        fetched[(chosen_repo, number)] = item
        if chosen_repo == args.repo:
            save_json(threads_dir / f"issue-{number}.json", item)

    # Hub inbox #1 must remain hub #1, independent of every product status.
    inbox = fetched.get((args.repo, 1))
    if inbox:
        save_json(cache / "inbox-1.json", inbox["comments"])
    statuses = {}
    for project, config in project_refs.items():
        project_dir = scoped_dir / project
        project_dir.mkdir(parents=True, exist_ok=True)
        for key in config["threads"]:
            if key in fetched:
                save_json(project_dir / f"issue-{key[1]}.json", fetched[key])
        status = config["status"]
        if status:
            statuses[project] = status[1]
            if status in fetched:
                save_json(cache / f"status-{project}.json", fetched[status])
    # NOTE: product-repo tuples may share issue number within a project if
    # its status is in the hub; explicit project refs with same number are
    # rejected rather than silently clobbered by a different repository.
    for project, config in project_refs.items():
        identities = {}
        for key in config["threads"]:
            if key[1] in identities and identities[key[1]] != key[0]:
                errors.append(f"project_issue_number_collision:{project}:{key[1]}")
            identities[key[1]] = key[0]


    # G02/G05: read all issue states via GitHub, not a pseudo-Owner form claim.
    # Fetch failures are explicit degraded capture, never empty successful data.
    owner_index = gh_api(
        f"/repos/{args.repo}/issues?state=all&labels=owner-input&per_page=100"
    )
    all_issues = gh_api(f"/repos/{args.repo}/issues?state=all&per_page=100")
    # This is a build-time guard, not a mutating label creation.
    # The existing publisher refuses a degraded capture BEFORE Pages upload.
    label_check = gh_api(f"/repos/{args.repo}/labels/owner-input")
    if not (isinstance(label_check, dict) and
            label_check.get("name") == "owner-input"):
        errors.append("owner_input_label_missing")
    owner_complete = isinstance(owner_index, list) and isinstance(all_issues, list)
    owner_issues = []
    if not owner_complete:
        errors.append("owner_input_index_failed")
    else:
        selected = {}
        for candidate in all_issues:
            if (isinstance(candidate, dict) and not candidate.get("pull_request")
                    and re.match(r'^\[Owner input\](?:\s|$)',
                                 candidate.get("title") or "", re.I)):
                selected[candidate.get("number")] = candidate
        # The labelled index is still authoritative for non-standard titles.
        for candidate in owner_index:
            if isinstance(candidate, dict) and not candidate.get("pull_request"):
                row = dict(candidate)
                row_labels = row.get("labels") or []
                if not any((x.get("name") if isinstance(x, dict) else x)
                           == "owner-input" for x in row_labels):
                    row_labels = list(row_labels) + [{"name": "owner-input"}]
                row["labels"] = row_labels
                selected[row.get("number")] = row
        for num, candidate in sorted(selected.items(),
                                     key=lambda pair: str(pair[0])):
            if not isinstance(num, int):
                errors.append("owner_input_number_invalid")
                owner_complete = False
                continue
            detail = fetch_issue(args.repo, num)
            events = gh_api(f"/repos/{args.repo}/issues/{num}/events?per_page=100")
            if not isinstance(detail, dict) or not isinstance(events, list):
                errors.append(f"owner_input_fetch_failed:{num}")
                owner_complete = False
                continue
            owner_issues.append({
                "number": num, "title": candidate.get("title", ""),
                "body": detail.get("body", ""),
                "type": "OWNER_INPUT", "project": "",
                "labels": detail.get("labels", candidate.get("labels", [])),
                "state": candidate.get("state"),
                "created_at": candidate.get("created_at"),
                "updated_at": candidate.get("updated_at"),
                "closed_at": candidate.get("closed_at"),
                "comments": detail.get("comments", []),
                "events": [
                    {"id": e.get("id"), "event": e.get("event"),
                     "created_at": e.get("created_at")}
                    for e in events if isinstance(e, dict)
                ],
                "events_complete": True,
            })
    if owner_complete:
        save_json(cache / "owner-inputs-source.json", owner_issues)

    sha = os.environ.get("GITHUB_SHA", "")
    manifest = {
        "schema_version": "wp1a.1",
        "repository": args.repo,
        "source_commit": sha if re.fullmatch(r"[0-9a-fA-F]{40}", sha) else None,
        "source_capture_at": captured_at,
        "status": "ok" if not errors else "degraded",
        "issues_fetched": sorted(num for (r, num) in fetched if r == args.repo),
        "project_repositories": {k: v["repository"] for k, v in project_refs.items()},
        "fetched_sources": sorted(f"{r}#{n}" for r, n in fetched),
        "owner_inputs_complete": owner_complete,
        "statuses": statuses,
        "errors": errors,
    }
    save_json(cache / "capture-info.json", manifest)
    print(f"Capture {manifest['status']}: {len(fetched)}/{len(all_refs)} sources; "
          f"{len(errors)} issue/reference errors. Protocol inbox is #1.")
    # The builder reads the manifest and marks degraded projections UNKNOWN/STALE.
    # An API outage must not be relabelled as a successful fetch.


if __name__ == "__main__":
    main()
