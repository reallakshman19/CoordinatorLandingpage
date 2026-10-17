#!/usr/bin/env python3
"""Guard/synchronize the Issue Form Project dropdown with live registries."""
import argparse
import json
from pathlib import Path
import re
import sys

SENTINEL = "all projects"
HUB_REPO = "reallakshman19/CoordinatorLandingpage"
# Historical benchmark projects remain selectable; newly registered product
# repositories are read-only C10 views and are not hub Owner-input targets.
LEGACY_BENCHMARK_FORM_PROJECTS = {"grade9-pilot", "imo-ab-test"}


def registry_projects(root):
    projects = []
    for path in sorted((Path(root) / "logs").glob("*/registry.json")):
        item = json.loads(path.read_text(encoding="utf-8"))
        name = path.parent.name
        if not isinstance(item, dict) or item.get("project") != name:
            raise ValueError("registry/project mismatch: " + name)
        if not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9._-]*", name):
            raise ValueError("invalid project name: " + name)
        product = item.get("repository")
        # Missing repository in older synthetic registries is retained; only
        # explicit external product links are excluded from writable hub form.
        if (product and product != HUB_REPO
                and name not in LEGACY_BENCHMARK_FORM_PROJECTS):
            continue
        projects.append(name)
    if not projects:
        raise ValueError("no registries found: refuse empty Project dropdown")
    return projects


def option_region(content):
    """Locate Project's exact options block, not Target/Input type options."""
    anchor = re.search(
        r'(?m)^  - type: dropdown\s*\n    id: project\s*\n'
        r'(?:(?!^  - type:)[\s\S])*?^      options:\s*\n', content)
    if not anchor:
        raise ValueError("Issue Form Project options section not found")
    rest = content[anchor.end():]
    tail = re.search(r'(?m)^(?:    validations:|  - type:)', rest)
    if not tail:
        raise ValueError("Issue Form Project options section has no terminator")
    return anchor.end(), anchor.end() + tail.start()


def generated_content(root, template):
    content = Path(template).read_text(encoding="utf-8")
    start, end = option_region(content)
    block = "".join("        - " + project + "\n" for project in
                    (registry_projects(root) + [SENTINEL]))
    return content[:start] + block + content[end:]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--template", default=".github/ISSUE_TEMPLATE/owner-input.yml")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--write", action="store_true")
    args = parser.parse_args()
    try:
        path = Path(args.root) / args.template
        expected = generated_content(args.root, path)
        original = path.read_text(encoding="utf-8")
        if args.check:
            if original != expected:
                print("ISSUE_FORM_PROJECT_OPTIONS_MISMATCH registry projects=" +
                      ",".join(registry_projects(args.root)), file=sys.stderr)
                return 1
            print("ISSUE_FORM_PROJECT_OPTIONS_OK " +
                  ",".join(registry_projects(args.root)))
            return 0
        if original != expected:
            path.write_text(expected, encoding="utf-8", newline="\n")
        print("ISSUE_FORM_PROJECT_OPTIONS_SYNCED " +
              ",".join(registry_projects(args.root)))
        return 0
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        print("ISSUE_FORM_PROJECT_OPTIONS_BLOCKED " + str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
