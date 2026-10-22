#!/usr/bin/env python3
"""Validate the portable Progress data contract with no external packages."""
import argparse
import json
import re
import sys
from pathlib import Path

from progress_schema import (check_schema, validate, scan_forbidden,
                             check_links, check_topic)

ROOT = Path(__file__).resolve().parents[1] / "site" / "progress-data"
FILES = ("meta", "stages", "actions", "fixtures")
KEY = re.compile(r"^[a-z0-9][a-z0-9-]*$")


def check_tree(root=ROOT, private=False):
    errors = []

    def err(where, why):
        errors.append(f"{where}: {why}")

    def read(path):
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            err(str(path.relative_to(root)), f"cannot read JSON ({exc})")
            return None

    def verify(name, path, value, private_mode):
        where = str(path.relative_to(root))
        schema = root / "schema" / f"{name}.schema.json"
        try:
            contract = json.loads(schema.read_text(encoding="utf-8"))
            check_schema(contract)
            for message in validate(value, contract):
                err(where, f"schema {name}: {message}")
        except (OSError, ValueError, TypeError) as exc:
            err(where, f"invalid or unsupported schema {name}: {exc}")
        try:
            for message in scan_forbidden(path.read_text(encoding="utf-8"), private_mode):
                err(where, message)
        except OSError as exc:
            err(where, f"cannot scan ({exc})")
        for message in check_links(value):
            err(where, message)

    projects_path = root / "projects.json"
    projects = read(projects_path)
    if not isinstance(projects, dict):
        return errors or ["projects.json: expected object"]
    verify("projects", projects_path, projects, private)
    seen_projects = set()
    for page in projects.get("projects", []):
        if not isinstance(page, dict):
            err("projects.json", "project entry must be an object")
            continue
        key = page.get("key", "")
        if not isinstance(key, str) or not KEY.fullmatch(key) or key in seen_projects:
            err("projects.json", f"invalid or duplicate project key {key!r}")
            continue
        seen_projects.add(key)
        mode = page.get("mode", "coordinator")
        if mode not in ("coordinator", "standalone-oracle"):
            err("projects.json", f"{key}: unknown workflow mode {mode!r}")
        private_mode = private or page.get("visibility", "public") == "private"
        base = root / key
        index_path = base / "index.json"
        index = read(index_path)
        if not isinstance(index, dict):
            continue
        verify("index", index_path, index, private_mode)
        chats = index.get("chats", {})
        if not isinstance(chats, dict):
            continue
        for ck, chat in chats.items():
            if not isinstance(chat, dict):
                continue
            if not re.fullmatch(r"[0-9a-f]{8}", str(chat.get("id8", ""))):
                err(f"{key}/index.json", f"chat {ck}: id8 must be 8 hex characters")
            url = chat.get("url")
            if isinstance(url, str) and url and not private_mode and not url.startswith("https://github.com/"):
                err(f"{key}/index.json", f"chat {ck}: only github.com links are allowed")
        if mode == "standalone-oracle":
            from standalone_oracle_relay import validate_audit
            for message in validate_audit(base):
                err(f"{key}/audit.json", message)
        seen_topics = set()
        for topic in index.get("topics", []):
            if not isinstance(topic, dict):
                continue
            tk = topic.get("key", "")
            if not isinstance(tk, str) or not KEY.fullmatch(tk) or tk in seen_topics:
                err(f"{key}/index.json", f"invalid or duplicate topic key {tk!r}")
                continue
            seen_topics.add(tk)
            if topic.get("planned"):
                continue
            data = {}
            for name in FILES:
                path = base / tk / f"{name}.json"
                value = read(path)
                if value is None:
                    break
                verify(name, path, value, private_mode)
                data[name] = value
            if len(data) != 4 or any(not isinstance(v, dict) for v in data.values()):
                continue
            for filename, message in check_topic(data, chats):
                err(f"{key}/{tk}/{filename}.json", message)
    return errors


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=ROOT)
    parser.add_argument("--private", action="store_true")
    args = parser.parse_args(argv)
    errors = check_tree(args.data.resolve(), args.private)
    for message in errors:
        print("ERROR", message)
    print("progress-data OK" if not errors else f"{len(errors)} problem(s)")
    return int(bool(errors))


if __name__ == "__main__":
    sys.exit(main())
