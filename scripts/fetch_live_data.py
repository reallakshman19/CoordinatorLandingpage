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
import subprocess  # Compatibility: existing callers patch subprocess.run here.
import sys
from urllib.parse import urlparse

from landing_build.fetch_github import _API_ERRORS, gh_api, save_json
from landing_build.fetch_github import fetch_issue as _fetch_issue
from landing_build.fetch_discovery import (
    discover_sources, extract_issue_number, issue_ref, discover_project_refs,
)
from landing_build.fetch_extras import WP12_CHILD_LIMIT, OWNER_INDEX_PAGE_LIMIT
from landing_build import fetch_extras as _fetch_extras
from landing_build.lineage import plan_lineage, finish_lineage


def fetch_issue(repo: str, number: int):
    """Public compatibility API; preserve patched fetch_live_data.gh_api."""
    return _fetch_issue(repo, number, api=gh_api)


def capture_project_extras(root, cache, projects, errors, control_repo=None):
    """Public compatibility API; preserve caller-patched provider/writer."""
    return _fetch_extras.capture_project_extras(
        root, cache, projects, errors, control_repo, api=gh_api, save=save_json)


def _capture_project_extras(root, cache, projects, errors, control_repo=None):
    """Compatibility alias for existing non-CLI callers."""
    return _fetch_extras._capture_project_extras(
        root, cache, projects, errors, control_repo, api=gh_api, save=save_json)


def fetch_bounded_owner_index(repo, labelled, max_pages=OWNER_INDEX_PAGE_LIMIT):
    """Public compatibility API; preserve caller-patched gh_api."""
    return _fetch_extras.fetch_bounded_owner_index(
        repo, labelled, max_pages, api=gh_api)


def main():
    try:
        return _main()
    finally:
        _API_ERRORS.set(None)


def _main():
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
    _API_ERRORS.set(errors)
    captured_at = datetime.now(timezone.utc).isoformat()
    capture_project_extras(root, cache, project_refs, errors, control_repo=args.repo)
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
    owner_index = fetch_bounded_owner_index(args.repo, labelled=True)
    all_issues = fetch_bounded_owner_index(args.repo, labelled=False)
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
                # Trust only GitHub's source association, never body text.
                "author_association": detail.get("author_association",
                                                  candidate.get("author_association", "")),
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
