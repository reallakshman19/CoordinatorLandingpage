#!/usr/bin/env python3
"""
build_data.py — Team Protocol landing page data builder.

Usage:
  # Normal build (from repo root):
  python scripts/build_data.py --root . --out site/data

  # Benchmark build (for testing or the Benchmarks view):
  python scripts/build_data.py --root . --out site/data \
      --benchmark benchmarks/grade9-pilot-2026-10-15 \
      --benchmark benchmarks/imo-ab-test-2026-10-15

The script never writes tokens, secrets, or full chat URLs.
Chat IDs appear only as 8-character id8s (already stored that way in the data).
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_json(path: Path):
    if not path.exists():
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  wrote {path}")


def id8(raw: str) -> str:
    """Return at most 8 chars — already the convention in the data."""
    if not raw:
        return raw
    return str(raw)[:8]


def scrub_chat_url(text: str) -> str:
    """Replace any full chat URL with an 8-char id placeholder."""
    # Pattern: long hex runs (>8 chars) that look like UUIDs or chat IDs
    # We do NOT scrub GitHub URLs — those are public.
    text = re.sub(
        r'https?://(?:chat\.openai\.com|chatgpt\.com)/c/([0-9a-f-]{9,})',
        lambda m: f'chat:{id8(m.group(1).replace("-",""))}',
        text
    )
    return text


EVIDENCE_RE = re.compile(
    r'TASK EVIDENCE v2\s*·\s*(?P<project>[^·]+?)\s*·\s*(?P<role>[^·]+?)\s*·\s*chat\s+(?P<chat>[0-9a-f]{8})\s*·\s*#(?P<seq>\d+)\s*·\s*(?P<ts>[^\n]+)',
    re.MULTILINE
)

STATUS_RE = re.compile(
    r'STATUS v2\s*·\s*(?P<role>[^·]+?)\s*·\s*chat\s+(?P<chat>[0-9a-f]{8})\s*·\s*working on\s+(?P<task>[^·]+?)\s*·\s*next\s+(?P<next>[^·]+?)\s*·\s*blocker\s+(?P<blocker>[^\n·]+)',
    re.MULTILINE
)

VERDICT_RE = re.compile(
    r'OwnerTeammember.*?(?:grounding verdict|RETIRED)[^\n]*(✅ ALIGNED|✏ CORRECTED|⚑ ESCALATE|RETIRED)',
    re.MULTILINE | re.DOTALL
)

COORD_EVIDENCE_RE = re.compile(
    r'COORDINATOR EVIDENCE v1\s*·\s*(?P<project>[^·]+?)\s*·\s*(?:cycle\s+(?P<cycle>\d+)\s*·\s*)?(?:epoch\s+(?P<epoch>\d+)\s*·\s*)?(?P<rest>[^\n]*)',
    re.MULTILINE
)

NEEDS_YOU_RE = re.compile(
    r'NEEDS YOU\s*\((\d+)\)(.*?)(?=\n```|\Z)',
    re.DOTALL
)

OUTSIDE_WRITE_RE = re.compile(
    r'(?:outside write|second writer outside|pushed outside)',
    re.IGNORECASE
)

SUPERSEDED_RE = re.compile(
    r'supersedes\s+(?P<ref>[^\s;(]+)',
    re.IGNORECASE
)

TIME_CORRECTED_RE = re.compile(
    r'(?:replaces|time-corrected|correction.*?replaces)',
    re.IGNORECASE
)

FOR_TC_RE = re.compile(
    r'FOR TeamCoordinator\s*·\s*(?P<project>[^·]+?)\s*·\s*(?P<type>\w+)\s*·\s*(?P<id>[^\n]+)',
    re.MULTILINE
)


def parse_task_evidence(comment_body: str, comment_id: int, comment_ts: str) -> dict | None:
    """Parse a TASK EVIDENCE v2 block from a comment body."""
    m = EVIDENCE_RE.search(comment_body)
    if not m:
        return None

    body = comment_body[m.start():]

    def field(name: str) -> str:
        pattern = re.compile(rf'^{name}:\s*(.+)', re.MULTILINE | re.IGNORECASE)
        fm = pattern.search(body)
        return fm.group(1).strip() if fm else ""

    status_m = re.search(r'Status:\s*(\w+)', body, re.IGNORECASE)

    proof_lines = []
    in_proof = False
    for line in body.splitlines():
        if line.startswith('Proof:'):
            in_proof = True
            continue
        if in_proof:
            if line.startswith('  -') or line.startswith('- '):
                proof_lines.append(line.strip())
            elif line.strip() and not line.startswith(' '):
                in_proof = False

    grade_map = {'CI': 'CI', 'READBACK': 'READBACK', 'LOCAL': 'LOCAL', 'CLAIM-ONLY': 'CLAIM-ONLY', 'OWNER': 'OWNER'}
    proofs = []
    for pl in proof_lines:
        grade = 'CLAIM-ONLY'
        for g in grade_map:
            if f'[{g}]' in pl:
                grade = g
                break
        proofs.append({'line': pl, 'grade': grade})

    return {
        'comment_id': comment_id,
        'ts': comment_ts,
        'project': m.group('project').strip(),
        'role': m.group('role').strip(),
        'chat_id8': m.group('chat'),
        'seq': int(m.group('seq')),
        'header_ts': m.group('ts').strip(),
        'task': field('Task'),
        'status': status_m.group(1) if status_m else '',
        'aim': field('Aim'),
        'did': field('Did'),
        'where': field('Where'),
        'proofs': proofs,
        'tests': field('Tests'),
        'would_be_wrong': field('Would be wrong if'),
        'not_done': field('Not done / HOLD'),
        'needs_owner': field('Needs Owner'),
        'next': field('Next'),
        'meter': field('Meter'),
        'raw': scrub_chat_url(comment_body),
        'replaces': None,
    }


def parse_verdict(comment_body: str, comment_id: int, comment_ts: str) -> dict | None:
    """Parse an OwnerTeammember grounding verdict from a comment."""
    m = VERDICT_RE.search(comment_body)
    if not m:
        return None
    return {
        'comment_id': comment_id,
        'ts': comment_ts,
        'verdict': m.group(1),
        'raw': scrub_chat_url(comment_body),
    }


def build_agent_evidence(thread: dict) -> list:
    """Build a list of evidence blocks (with interleaved verdicts) from a thread."""
    items = []
    for c in thread.get('comments', []):
        body = c.get('body', '')
        cid = c.get('id', 0)
        ts = c.get('created_at', '')

        ev = parse_task_evidence(body, cid, ts)
        if ev:
            # Check for replaces marker
            rep = re.search(r'replaces #(\d+)', body, re.IGNORECASE)
            if rep:
                ev['replaces'] = int(rep.group(1))
            items.append({'type': 'evidence', **ev})
            continue

        verd = parse_verdict(body, cid, ts)
        if verd:
            items.append({'type': 'verdict', **verd})
            continue

        # STATUS v2 line
        sm = STATUS_RE.search(body)
        if sm:
            items.append({
                'type': 'status',
                'comment_id': cid,
                'ts': ts,
                'role': sm.group('role').strip(),
                'chat_id8': sm.group('chat'),
                'task': sm.group('task').strip(),
                'next': sm.group('next').strip(),
                'blocker': sm.group('blocker').strip(),
                'raw': scrub_chat_url(body),
            })
            continue

        # Retirement notice
        if 'RETIRED' in body and 'OwnerTeammember' in body:
            items.append({
                'type': 'retired',
                'comment_id': cid,
                'ts': ts,
                'raw': scrub_chat_url(body),
            })

    return items


def build_timeline_from_events(events_path: Path, project: str) -> list:
    """Build timeline from events.jsonl (grade9-pilot)."""
    events = []
    if not events_path.exists():
        return events
    with open(events_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                ev = json.loads(line)
                ev['_source'] = 'events_jsonl'
                ev['project'] = project
                # Scrub any chat URLs
                for k, v in ev.items():
                    if isinstance(v, str):
                        ev[k] = scrub_chat_url(v)
                events.append(ev)
            except json.JSONDecodeError:
                pass
    return events


def build_timeline_from_threads(threads: list, inbox: list, project: str) -> list:
    """
    Reconstruct a timeline from thread comments + inbox (imo-ab-test has no events.jsonl).
    Marks the result as reconstructed=True.
    """
    events = []

    # Inbox events
    for c in inbox:
        body = c.get('body', '')
        ts = c.get('created_at', '')

        # FOR TeamCoordinator
        ftc = FOR_TC_RE.search(body)
        if ftc and project in ftc.group('project').strip():
            events.append({
                'type': 'FOR_TC',
                'ts': ts,
                'actor': 'OwnerTeammember',
                'target': 'TeamCoordinator',
                'text': scrub_chat_url(body),
                'reconstructed': True,
                'project': project,
                '_source': 'inbox',
                'comment_id': c.get('id'),
            })
            continue

        # CONTROL epoch
        if 'CONTROL epoch' in body and project in body:
            events.append({
                'type': 'CONTROL_EPOCH',
                'ts': ts,
                'actor': 'OwnerTeammember',
                'text': scrub_chat_url(body[:200]),
                'reconstructed': True,
                'project': project,
                '_source': 'inbox',
                'comment_id': c.get('id'),
            })
            continue

        # COORDINATOR EVIDENCE receipts in inbox? No — they go in status.
        # Owner decisions in inbox
        if 'Owner decision' in body or 'relaying Owner decision' in body:
            events.append({
                'type': 'OWNER_DECISION',
                'ts': ts,
                'actor': 'OwnerTeammember',
                'text': scrub_chat_url(body),
                'reconstructed': True,
                'project': project,
                '_source': 'inbox',
                'comment_id': c.get('id'),
            })

    # Thread events (coordinator evidence + agent evidence)
    for t in threads:
        for c in t.get('comments', []):
            body = c.get('body', '')
            ts = c.get('created_at', '')
            cid = c.get('id', 0)
            issue_num = t.get('number', 0)

            # COORDINATOR EVIDENCE
            cm = COORD_EVIDENCE_RE.search(body)
            if cm:
                ny = NEEDS_YOU_RE.search(body)
                is_time_corrected = bool(TIME_CORRECTED_RE.search(body))
                events.append({
                    'type': 'COORDINATOR_EVIDENCE',
                    'ts': ts,
                    'actor': 'TeamCoordinator',
                    'project': cm.group('project').strip(),
                    'cycle': cm.group('cycle'),
                    'epoch': cm.group('epoch'),
                    'needs_you': ny.group(2).strip() if ny else None,
                    'needs_you_count': int(ny.group(1)) if ny else 0,
                    'time_corrected': is_time_corrected,
                    'text': scrub_chat_url(body),
                    'reconstructed': True,
                    'project_filter': project,
                    '_source': f'thread_{issue_num}',
                    'comment_id': cid,
                })
                continue

            # TASK EVIDENCE
            ev = parse_task_evidence(body, cid, ts)
            if ev:
                events.append({
                    'type': 'TASK_EVIDENCE',
                    'ts': ts,
                    'actor': f"agent:{ev['chat_id8']}",
                    'project': project,
                    'chat_id8': ev['chat_id8'],
                    'seq': ev['seq'],
                    'task': ev['task'],
                    'status': ev['status'],
                    'reconstructed': True,
                    '_source': f'thread_{issue_num}',
                    'comment_id': cid,
                })
                continue

            # Verdict
            verd = parse_verdict(body, cid, ts)
            if verd:
                events.append({
                    'type': 'VERDICT',
                    'ts': ts,
                    'actor': 'OwnerTeammember',
                    'verdict': verd['verdict'],
                    'project': project,
                    'reconstructed': True,
                    '_source': f'thread_{issue_num}',
                    'comment_id': cid,
                })
                continue

            # Outside write detection
            if OUTSIDE_WRITE_RE.search(body):
                events.append({
                    'type': 'OUTSIDE_WRITE',
                    'ts': ts,
                    'actor': 'external',
                    'project': project,
                    'text': scrub_chat_url(body[:300]),
                    'reconstructed': True,
                    '_source': f'thread_{issue_num}',
                    'comment_id': cid,
                })
                continue

    events.sort(key=lambda e: e.get('ts', ''))
    return events


def build_project_data(root: Path, project_name: str, registry: dict,
                        threads: dict, inbox: list, events_path: Path | None) -> dict:
    """Assemble the project data payload."""

    # Agents
    agents = []
    for a in registry.get('agents', []):
        chat = a.get('chat_id8', '')
        thread_url = a.get('evidence_thread', '')
        # Extract thread number
        thread_num = None
        m = re.search(r'/issues/(\d+)', thread_url)
        if m:
            thread_num = int(m.group(1))

        thread_data = threads.get(thread_num, {}) if thread_num else {}
        evidence = build_agent_evidence(thread_data)

        agents.append({
            'role': a.get('role', ''),
            'alias': a.get('alias', ''),
            'generation': a.get('generation', 1),
            'chat_id8': chat,
            'status': a.get('status', ''),
            'retired': a.get('retired'),
            'evidence_thread_num': thread_num,
            'branch': a.get('branch', ''),
            'started': a.get('started'),
            'evidence': evidence,
        })

    # Leases
    leases = registry.get('leases', [])
    # Also parse leases from standing_owner_decisions
    sod = registry.get('standing_owner_decisions', [])
    lease_pattern = re.compile(r'AB-LEASE granted.*?(?:Agent\s+\w+\s+[0-9a-f]{8})', re.IGNORECASE | re.DOTALL)
    for sd in sod:
        sd_str = sd if isinstance(sd, str) else json.dumps(sd)
        if 'lease' in sd_str.lower() and not leases:
            leases.append({'description': sd})

    # Facts / outside writes
    facts = registry.get('facts', [])
    outside_writes = [f for f in facts if OUTSIDE_WRITE_RE.search(f if isinstance(f, str) else json.dumps(f))]

    # Status comment
    status_issue_url = registry.get('status_comment') or registry.get('status_issue', '')

    # Timeline
    if events_path and events_path.exists():
        timeline = build_timeline_from_events(events_path, project_name)
        timeline_source = 'events_jsonl'
    else:
        # Reconstruct from threads + inbox
        thread_list = list(threads.values())
        timeline = build_timeline_from_threads(thread_list, inbox, project_name)
        timeline_source = 'reconstructed'

    return {
        'project': project_name,
        'registry': {
            'protocol': registry.get('protocol', ''),
            'repository': registry.get('repository', ''),
            'updated': registry.get('updated', ''),
            'control': registry.get('control', {}),
            'workflow': registry.get('workflow', {}),
            'source': registry.get('source', {}),
            'standing_owner_decisions': sod,
            'open_owner_decisions': registry.get('open_owner_decisions', []),
            'status_issue': status_issue_url,
            'log_folder': registry.get('log_folder', ''),
            'facts': facts,
        },
        'agents': agents,
        'leases': leases,
        'outside_writes': outside_writes,
        'timeline_source': timeline_source,
        'timeline_event_count': len(timeline),
        'built_at': datetime.now(timezone.utc).isoformat(),
    }, timeline


def load_benchmark(bm_dir: Path) -> tuple:
    """Load data from a benchmark directory."""
    manifest = load_json(bm_dir / 'MANIFEST.json') or {}
    project_name = manifest.get('project', bm_dir.name)

    registry = load_json(bm_dir / 'logs' / 'registry.json') or {}
    inbox_data = load_json(bm_dir / 'inbox-1.json') or []

    # Load threads
    threads = {}
    threads_dir = bm_dir / 'threads'
    if threads_dir.exists():
        for tf in threads_dir.glob('issue-*.json'):
            t = load_json(tf)
            if t:
                threads[t['number']] = t

    # Events log (grade9-pilot has one, imo-ab-test does not)
    logs_dir = bm_dir / 'logs'
    events_path = None
    for child in logs_dir.iterdir() if logs_dir.exists() else []:
        if child.is_dir():
            ep = child / 'events.jsonl'
            if ep.exists():
                events_path = ep
                break

    return project_name, registry, threads, inbox_data, events_path


def load_live_threads(cache_dir: Path) -> tuple[dict, list]:
    """Load threads and inbox from _live_cache/ (written by fetch_live_data.py)."""
    threads: dict = {}
    threads_dir = cache_dir / 'threads'
    if threads_dir.exists():
        for tf in threads_dir.glob('issue-*.json'):
            t = load_json(tf)
            if t:
                threads[t['number']] = t

    inbox_path = cache_dir / 'inbox-1.json'
    inbox = load_json(inbox_path) or []
    return threads, inbox


def build_all(root: Path, out_dir: Path, benchmark_dirs: list[Path] | None = None,
              cache_dir: Path | None = None):
    """Main build entry point."""
    print(f"Building site data → {out_dir}")
    out_dir.mkdir(parents=True, exist_ok=True)

    # Determine sources
    if benchmark_dirs:
        sources = []
        for bmd in benchmark_dirs:
            sources.append(('benchmark', bmd))
    else:
        # Normal build from repo structure
        sources = []
        logs_root = root / 'logs'
        if logs_root.exists():
            for proj_dir in logs_root.iterdir():
                if proj_dir.is_dir() and proj_dir.name != 'README.md':
                    sources.append(('live', proj_dir))

    all_projects = []
    all_timelines = {}

    for source_type, source_path in sources:
        if source_type == 'benchmark':
            project_name, registry, threads, inbox, events_path = load_benchmark(source_path)
            is_benchmark = True
        else:
            project_name = source_path.name
            registry = load_json(source_path / 'registry.json') or {}
            # Load threads + inbox from _live_cache/ (populated by fetch_live_data.py)
            _cache = cache_dir if cache_dir else root / '_live_cache'
            threads, inbox = load_live_threads(_cache)
            events_path = None
            for session_dir in source_path.iterdir():
                if session_dir.is_dir():
                    ep = session_dir / 'events.jsonl'
                    if ep.exists():
                        events_path = ep
                        break
            is_benchmark = False

        project_data, timeline = build_project_data(
            root, project_name, registry, threads, inbox, events_path
        )
        project_data['is_benchmark'] = is_benchmark
        project_data['benchmark_snapshot'] = (
            load_json(source_path / 'MANIFEST.json') or {}
        ).get('snapshot') if is_benchmark else None

        all_projects.append(project_data)
        all_timelines[project_name] = timeline

        # Save per-agent evidence
        for agent in project_data['agents']:
            aid = agent['chat_id8']
            if aid:
                save_json(
                    out_dir / f'evidence-{aid}.json',
                    {
                        'project': project_name,
                        'agent': agent,
                        'built_at': project_data['built_at'],
                    }
                )

        # Save timeline
        save_json(
            out_dir / f'timeline-{project_name}.json',
            {
                'project': project_name,
                'source': project_data['timeline_source'],
                'events': timeline,
                'built_at': project_data['built_at'],
            }
        )

    # Save projects summary
    summary = []
    for pd in all_projects:
        summary.append({
            'project': pd['project'],
            'repository': pd['registry']['repository'],
            'control': pd['registry']['control'],
            'workflow': pd['registry']['workflow'],
            'agents': [
                {
                    'role': a['role'],
                    'alias': a.get('alias', ''),
                    'generation': a['generation'],
                    'chat_id8': a['chat_id8'],
                    'status': a['status'],
                    'evidence_thread_num': a['evidence_thread_num'],
                }
                for a in pd['agents']
            ],
            'open_owner_decisions': pd['registry']['open_owner_decisions'],
            'outside_writes': pd['outside_writes'],
            'timeline_source': pd['timeline_source'],
            'is_benchmark': pd['is_benchmark'],
            'benchmark_snapshot': pd['benchmark_snapshot'],
            'built_at': pd['built_at'],
        })

    save_json(out_dir / 'projects.json', summary)

    # Save full project detail files
    for pd in all_projects:
        pname = pd['project']
        # Remove bulky evidence from the project file (use per-agent files instead)
        pd_slim = {k: v for k, v in pd.items() if k != 'agents'}
        pd_slim['agents'] = [
            {k: v for k, v in a.items() if k != 'evidence'}
            for a in pd['agents']
        ]
        save_json(out_dir / f'project-{pname}.json', pd_slim)

    print(f"Done. Built {len(all_projects)} project(s).")
    return all_projects, all_timelines


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Build site data JSON files")
    parser.add_argument('--root', default='.', help='Repository root')
    parser.add_argument('--out', default='site/data', help='Output directory')
    parser.add_argument('--benchmark', action='append', dest='benchmarks',
                        help='Benchmark directory (may be specified multiple times)')
    parser.add_argument('--cache-dir', default=None,
                        help='Directory written by fetch_live_data.py (live mode only)')
    args = parser.parse_args()

    root = Path(args.root).resolve()
    out = Path(args.out)
    if not out.is_absolute():
        out = root / out

    bm_dirs = None
    if args.benchmarks:
        bm_dirs = [Path(b) if Path(b).is_absolute() else root / b for b in args.benchmarks]

    cache = Path(args.cache_dir) if args.cache_dir else None
    if cache and not cache.is_absolute():
        cache = root / cache

    build_all(root, out, bm_dirs, cache_dir=cache)
