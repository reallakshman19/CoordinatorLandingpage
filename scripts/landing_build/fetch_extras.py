"""Read-only bounded extras/lineage and owner index, from fetch_live_data."""
import json
from pathlib import Path
import re
import shutil

from landing_build.fetch_github import (
    _API_ERRORS, gh_api as default_gh_api, save_json as default_save_json,
)
from landing_build.lineage import plan_lineage, finish_lineage

WP12_CHILD_LIMIT = 12


def capture_project_extras(root, cache, projects, errors, control_repo=None, *, api=None, save=None):
    token = _API_ERRORS.set(errors)
    try:
        return _capture_project_extras(root, cache, projects, errors,
                                       control_repo, api, save)
    finally:
        _API_ERRORS.reset(token)


def _capture_project_extras(root, cache, projects, errors,
                            control_repo=None, api=None, save=None):
    gh_api = api or default_gh_api
    save_json = save or default_save_json
    """Bounded read-only child-title and PR-head observations per project."""
    extras = cache / "project-extras"
    if extras.exists():
        shutil.rmtree(extras)
    extras.mkdir(parents=True)
    for project, config in sorted(projects.items()):
        reg = json.loads((root / "logs" / project / "registry.json")
                         .read_text(encoding="utf-8"))
        repo = config['repository']
        dest = extras / project
        dest.mkdir()
        lineage = plan_lineage(reg, control_repo or repo)
        observations = {}
        for item in lineage:
            if item["status"] != "PENDING":
                continue
            key = (item["repository"], item["issue_number"])
            if key not in observations:
                endpoint = f"/repos/{key[0]}/issues/{key[1]}"
                earlier = len(errors)
                result = gh_api(endpoint)
                reason = next((x.rsplit(":", 1)[-1] for x in errors[earlier:]
                               if x.startswith(f"gh_api_failure:{endpoint}:")), None)
                observations[key] = (result, reason)
            result, reason = observations[key]
            finish_lineage(item, result)
            if item["status"] == "INACCESSIBLE" and reason:
                item["reason"] = reason
        if lineage:
            save_json(dest / "lineage.json", lineage)
        children = reg.get('children', [])
        if children:
            if not isinstance(children, list) or len(children) > 100:
                errors.append(f"children_limit_or_shape_invalid:{project}")
            else:
                results, seen = [], set()
                for entry in children:
                    url = entry.get('url') if isinstance(entry, dict) else entry
                    mt = re.fullmatch(
                        r'https://github\.com/([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)/issues/(\d+)',
                        str(url or ''))
                    if not mt or mt.group(1) != repo:
                        errors.append(f"child_reference_invalid:{project}")
                        continue
                    if url in seen:
                        continue  # duplicate registry pointer is one child
                    seen.add(url)
                    if len(seen) > WP12_CHILD_LIMIT:
                        errors.append(f"children_limit_or_shape_invalid:{project}")
                        break
                    num = int(mt.group(2))
                    # A single resource endpoint, not a paginated search.
                    value = gh_api(f"/repos/{repo}/issues/{num}")
                    if (not isinstance(value, dict)
                            or value.get('number') != num
                            or value.get('pull_request')
                            or value.get('html_url', url) != url):
                        errors.append(f"child_fetch_invalid:{project}:{num}")
                        continue
                    results.append({'url': url, 'repository': repo,
                                    'title': value.get('title', '')})
                save_json(dest / "children.json", results)
        # One declared schema, at root and/or agents[i].evidence.
        # At most 12 unique, own-repository PR HEAD GETs per project.
        declarations = [reg.get('evidence')]
        declarations.extend(a.get('evidence') for a in reg.get('agents', [])
                            if isinstance(a, dict))
        pr_urls = []
        for record in declarations:
            if record is None:
                continue
            if not isinstance(record, dict):
                errors.append(f"evidence_declaration_invalid:{project}")
                continue
            url, sha = record.get('pr_url'), record.get('head')
            mt = re.fullmatch(
                r'https://github\.com/([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)/pull/(\d+)',
                str(url or ''))
            if (not mt or mt.group(1) != repo or not isinstance(sha, str)
                    or not re.fullmatch(r'[0-9a-fA-F]{40}', sha)):
                errors.append(f"evidence_declaration_invalid:{project}")
                continue
            if url not in pr_urls:
                pr_urls.append(url)
        if len(pr_urls) > WP12_CHILD_LIMIT:
            errors.append(f"evidence_pr_limit:{project}")
            continue
        snapshots = []
        for url in pr_urls:
            number = int(url.rsplit('/', 1)[-1])
            value = gh_api(f"/repos/{repo}/pulls/{number}")
            current = value.get('head') if isinstance(value, dict) else None
            sha = current.get('sha') if isinstance(current, dict) else None
            if (not isinstance(sha, str) or
                    not re.fullmatch(r'[0-9a-fA-F]{40}', sha)
                    or value.get('number') != number):
                errors.append(f"evidence_pr_head_unavailable:{project}")
                continue
            snap = {'url': url, 'repository': repo, 'head': sha}
            if value.get('state') in ('open', 'closed'):
                snap['state'] = value['state']
            if 'merged_at' in value:
                snap['merged_at'] = value['merged_at']
            snapshots.append(snap)
        if pr_urls:
            save_json(dest / "pr-heads.json", snapshots)


OWNER_INDEX_PAGE_LIMIT = 5


def fetch_bounded_owner_index(repo, labelled, max_pages=OWNER_INDEX_PAGE_LIMIT, *, api=None):
    """Read up to 5 explicit pages without gh auto-pagination.

    Page five containing 100 items is ambiguous (page six could exist):
    return None and refuse green publication rather than truncate silently.
    """
    gh_api = api or default_gh_api
    if max_pages != OWNER_INDEX_PAGE_LIMIT:
        raise ValueError("Owner issue page bound cannot be changed")
    prefix = f"/repos/{repo}/issues?state=all&"
    if labelled:
        prefix += "labels=owner-input&"
    rows = []
    for page in range(1, max_pages + 1):
        chunk = gh_api(prefix + f"per_page=100&page={page}")
        if not isinstance(chunk, list) or len(chunk) > 100:
            return None
        rows.extend(chunk)
        if len(chunk) < 100:
            return rows
    # Even if there were exactly 500, we cannot prove no sixth page.
    return None


