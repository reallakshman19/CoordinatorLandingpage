#!/usr/bin/env python3
"""Validate Progress JSON against strict stdlib schemas and cross-file invariants."""
import argparse
import json
import re
import sys
from pathlib import Path

from progress_schema import UnsupportedKeyword, check_schema, validate

ROOT = Path(__file__).resolve().parents[1] / "site" / "progress-data"
SECTIONS = ("repository", "issues", "pullRequests", "roadmap", "highRoi",
            "future", "intent", "inputs", "knownIssues", "pending")
TOPIC_FILES = ("meta", "stages", "actions", "fixtures")
KEY = re.compile(r"^[a-z0-9][a-z0-9-]*$")
ID8 = re.compile(r"^[0-9a-f]{8}$")
BLOCKED = [(re.compile(r"drive\.google\.com|docs\.google\.com"), "Google Drive link"),
           (re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+"), "email address")]
CHATGPT = re.compile(r"chatgpt\.com/c/|chat\.openai\.com")


def check_tree(root=ROOT, private=False):
    errors = []

    def err(where, message):
        errors.append(f"{where}: {message}")

    def load(path):
        where = str(path.relative_to(root))
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            err(where, f"cannot read JSON ({exc})")
            return None
        return value

    def schema_check(name, value, where):
        path = root / "schema" / f"{name}.schema.json"
        try:
            schema = json.loads(path.read_text(encoding="utf-8"))
            check_schema(schema)
            for message in validate(value, schema):
                err(where, f"schema {name}: {message}")
        except (OSError, ValueError, TypeError) as exc:
            err(where, f"invalid or unsupported schema {name}: {exc}")

    def scan(path, is_private):
        where = str(path.relative_to(root))
        try:
            raw = path.read_text(encoding="utf-8")
        except OSError as exc:
            err(where, f"cannot scan ({exc})")
            return
        for rx, what in BLOCKED:
            if rx.search(raw):
                err(where, f"contains a {what}")
        if not is_private and CHATGPT.search(raw):
            err(where, "contains a ChatGPT chat link (public repo: id8 only)")

    def links(value, where):
        if isinstance(value, dict):
            for k, v in value.items():
                if k in ("u", "url", "ref") and isinstance(v, str) and v and not v.startswith("https://"):
                    err(where, f"link must start with https:// ({v[:50]})")
                links(v, where)
        elif isinstance(value, list):
            for v in value:
                links(v, where)

    projects = load(root / "projects.json")
    if not isinstance(projects, dict):
        return errors or ["projects.json: expected object"]
    schema_check("projects", projects, "projects.json")
    scan(root / "projects.json", private)
    links(projects, "projects.json")
    seen_projects = set()
    for p in projects.get("projects", []):
        if not isinstance(p, dict):
            err("projects.json", "project entry must be an object")
            continue
        key = p.get("key", "")
        if not isinstance(key, str) or not KEY.fullmatch(key) or key in seen_projects:
            err("projects.json", f"invalid or duplicate project key {key!r}")
            continue
        seen_projects.add(key)
        if p.get("mode", "coordinator") not in ("coordinator", "standalone-oracle"):
            err("projects.json", f"{key}: unknown workflow mode")
        own_private = private or p.get("visibility", "public") == "private"
        base = root / key
        index = load(base / "index.json")
        if not isinstance(index, dict):
            continue
        schema_check("index", index, f"{key}/index.json")
        scan(base / "index.json", own_private)
        links(index, f"{key}/index.json")
        chats = index.get("chats", {})
        if not isinstance(chats, dict):
            continue
        for ck, chat in chats.items():
            if not isinstance(chat, dict):
                continue
            if not ID8.fullmatch(str(chat.get("id8", ""))):
                err(f"{key}/index.json", f"chat {ck}: id8 must be 8 hex characters")
            url = chat.get("url")
            if url and isinstance(url, str) and not own_private and not url.startswith("https://github.com/"):
                err(f"{key}/index.json", f"chat {ck}: only github.com links are allowed")
        if p.get("mode") == "standalone-oracle":
            from standalone_oracle_relay import validate_audit
            for problem in validate_audit(base):
                err(f"{key}/audit.json", problem)
        seen = set()
        for t in index.get("topics", []):
            if not isinstance(t, dict):
                continue
            tk = t.get("key", "")
            if not isinstance(tk, str) or not KEY.fullmatch(tk) or tk in seen:
                err(f"{key}/index.json", f"invalid or duplicate topic key {tk!r}")
                continue
            seen.add(tk)
            if t.get("planned"):
                continue
            data = {}
            for name in TOPIC_FILES:
                path = base / tk / f"{name}.json"
                value = load(path)
                if value is None:
                    break
                schema_check(name, value, f"{key}/{tk}/{name}.json")
                scan(path, own_private)
                links(value, f"{key}/{tk}/{name}.json")
                data[name] = value
            if len(data) != 4 or any(not isinstance(v, dict) for v in data.values()):
                continue
            prefix = f"{key}/{tk}"
            for sid, s in data["stages"].items():
                if not isinstance(s, dict):
                    continue
                if s.get("milestone") not in data["meta"].get("milestones", {}):
                    err(f"{prefix}/stages.json", f"{sid}: unknown milestone {s.get('milestone')!r}")
                if s.get("lane") not in data["meta"].get("lanes", {}):
                    err(f"{prefix}/stages.json", f"{sid}: unknown lane {s.get('lane')!r}")
                for c in s.get("chats", []):
                    if c not in chats:
                        err(f"{prefix}/stages.json", f"{sid}: chat key {c!r} not in index.json")
            for cid, a in data["actions"].items():
                if not isinstance(a, dict):
                    continue
                for sid in a.get("stages", []):
                    if sid not in data["stages"]:
                        err(f"{prefix}/actions.json", f"{cid}: unknown stage {sid!r}")
                if a.get("status") == "open" and sum(bool(o.get("suggested")) for o in a.get("options", []) if isinstance(o, dict)) != 1:
                    err(f"{prefix}/actions.json", f"{cid}: open card needs exactly one suggested option")
                if a.get("status") == "done":
                    ans = a.get("answer")
                    for field in ("text", "at", "ref"):
                        if not isinstance(ans, dict) or not isinstance(ans.get(field), str) or not ans[field]:
                            err(f"{prefix}/actions.json", f"{cid}: done card needs answer.{field}")
            for sec, entries in data["fixtures"].items():
                if sec not in SECTIONS:
                    err(f"{prefix}/fixtures.json", f"unknown fixture section {sec!r}")
                elif isinstance(entries, list):
                    for e in entries:
                        if isinstance(e, dict) and not e.get("t"):
                            err(f"{prefix}/fixtures.json", f"{sec}: entry has no text")
    return errors


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=ROOT)
    parser.add_argument("--private", action="store_true")
    args = parser.parse_args(argv)
    problems = check_tree(args.data.resolve(), args.private)
    for problem in problems:
        print("ERROR", problem)
    print("progress-data OK" if not problems else f"{len(problems)} problem(s)")
    return int(bool(problems))


if __name__ == "__main__":
    sys.exit(main())
