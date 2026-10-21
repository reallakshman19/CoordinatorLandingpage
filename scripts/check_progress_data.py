#!/usr/bin/env python3
"""Validate site/progress-data/ (the JSON behind the landing page tab "Progress page").

Run from the repository root:  python scripts/check_progress_data.py
Exit code 1 and one line per problem when something is wrong. See docs/PROGRESS_PAGE.md.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "site" / "progress-data"
STATES = {"VERIFIED", "SUBMITTED", "IN_PROGRESS", "BLOCKED", "NOT_STARTED", "STALE", "UNKNOWN", "NOT_APPLICABLE"}
ACTORS = {"-", "YOU", "OTM", "ORACLE", "IR", "CODER", "PQRT", "PCHK"}
SECTIONS = ("repository", "issues", "pullRequests", "roadmap", "highRoi", "future", "intent", "inputs", "knownIssues", "pending")
TOPIC_FILES = ("meta", "stages", "actions", "fixtures")
KEY = re.compile(r"^[a-z0-9][a-z0-9-]*$")
FORBIDDEN = [(re.compile(r"chatgpt\.com/c/|chat\.openai\.com"), "ChatGPT chat link (public repo: id8 only)"),
             (re.compile(r"drive\.google\.com|docs\.google\.com"), "Google Drive link"),
             (re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+"), "email address")]
errors = []


def err(where, msg):
    errors.append(f"{where}: {msg}")


def load(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        err(path.relative_to(ROOT), f"cannot read JSON ({e})")
        return None


def scan(path):
    text = path.read_text(encoding="utf-8")
    for rx, what in FORBIDDEN:
        if rx.search(text):
            err(path.relative_to(ROOT), f"contains a {what}")


def check_urls(where, obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in ("u", "url", "ref") and isinstance(v, str) and v and not v.startswith("https://"):
                err(where, f"link must start with https:// ({v[:50]})")
            check_urls(where, v)
    elif isinstance(obj, list):
        for v in obj:
            check_urls(where, v)


def main():
    projects = load(ROOT / "projects.json")
    for p in (projects or {}).get("projects", []):
        key = p.get("key", "")
        if not KEY.match(key) or not p.get("label"):
            err("projects.json", f"bad project entry {p}")
            continue
        base = ROOT / key
        index = load(base / "index.json")
        if index is None:
            continue
        scan(base / "index.json")
        for c, chat in (index.get("chats") or {}).items():
            if not re.fullmatch(r"[0-9a-f]{8}", str(chat.get("id8", ""))):
                err(f"{key}/index.json", f"chat {c}: id8 must be 8 hex characters")
            if chat.get("url") and not str(chat["url"]).startswith("https://github.com/"):
                err(f"{key}/index.json", f"chat {c}: only github.com links are allowed")
        proj = index.get("project", {})
        for f in ("title", "updatedAt", "updatedBy", "staleAfterMin"):
            if f not in proj:
                err(f"{key}/index.json", f"project.{f} missing")
        seen = set()
        for t in index.get("topics", []):
            tk = t.get("key", "")
            if not KEY.match(tk) or tk in seen or not t.get("label"):
                err(f"{key}/index.json", f"bad or duplicate topic entry {t}")
                continue
            seen.add(tk)
            if t.get("planned"):
                continue
            tdir = base / tk
            data = {}
            for n in TOPIC_FILES:
                d = load(tdir / f"{n}.json")
                if d is None:
                    break
                scan(tdir / f"{n}.json")
                check_urls(f"{key}/{tk}/{n}.json", d)
                data[n] = d
            if len(data) < 4:
                continue
            where = f"{key}/{tk}"
            miles, lanes = data["meta"].get("milestones", {}), data["meta"].get("lanes", {})
            for sid, s in data["stages"].items():
                if s.get("state") not in STATES:
                    err(f"{where}/stages.json", f"{sid}: state {s.get('state')!r} not in the vocabulary")
                if s.get("actor", "-") not in ACTORS:
                    err(f"{where}/stages.json", f"{sid}: actor {s.get('actor')!r} unknown")
                if s.get("milestone") not in miles:
                    err(f"{where}/stages.json", f"{sid}: milestone {s.get('milestone')!r} not in meta.json")
                if s.get("lane") not in lanes:
                    err(f"{where}/stages.json", f"{sid}: lane {s.get('lane')!r} not in meta.json")
                for c in s.get("chats", []):
                    if c not in (index.get("chats") or {}):
                        err(f"{where}/stages.json", f"{sid}: chat {c!r} not in index.json chats")
            for cid, a in data["actions"].items():
                if a.get("status") not in ("open", "done"):
                    err(f"{where}/actions.json", f"{cid}: status must be open or done")
                for s in a.get("stages", []):
                    if s not in data["stages"]:
                        err(f"{where}/actions.json", f"{cid}: stage {s!r} not in stages.json")
                if a.get("status") == "open" and not any(o.get("suggested") for o in a.get("options", [])):
                    err(f"{where}/actions.json", f"{cid}: an open card needs one suggested option")
            for sec in data["fixtures"]:
                if sec not in SECTIONS:
                    err(f"{where}/fixtures.json", f"unknown section {sec!r}")
                for e in data["fixtures"][sec]:
                    if not e.get("t"):
                        err(f"{where}/fixtures.json", f"{sec}: an entry has no text (t)")
    for e in errors:
        print("ERROR", e)
    print("progress-data OK" if not errors else f"{len(errors)} problem(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
