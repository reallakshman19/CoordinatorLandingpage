"""Registry-owned product/control issue discovery, from fetch_live_data."""
import json
from pathlib import Path
import re

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




