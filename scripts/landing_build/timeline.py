"""Timeline builders; extracted unchanged from build_data."""

import json
from pathlib import Path
import re


# Shared parsers stay in build_data (also used outside the timeline).
# build_data binds them here right after importing this module, which
# avoids a circular import; the function bodies below are unchanged.
scrub_chat_url = parse_task_evidence = parse_verdict = None
OUTSIDE_WRITE_RE = None


COORD_EVIDENCE_RE = re.compile(
    r'COORDINATOR EVIDENCE v1\s*·\s*(?P<project>[^·]+?)\s*·\s*(?:cycle\s+(?P<cycle>\d+)\s*·\s*)?(?:epoch\s+(?P<epoch>\d+)\s*·\s*)?(?P<rest>[^\n]*)',
    re.MULTILINE
)

NEEDS_YOU_RE = re.compile(
    r'NEEDS YOU\s*\((\d+)\)(.*?)(?=\n```|\Z)',
    re.DOTALL
)

TIME_CORRECTED_RE = re.compile(
    r'(?:replaces|time-corrected|correction.*?replaces)',
    re.IGNORECASE
)

FOR_TC_RE = re.compile(
    r'FOR TeamCoordinator\s*·\s*(?P<project>[^·]+?)\s*·\s*(?P<type>\w+)\s*·\s*(?P<id>[^\n]+)',
    re.MULTILINE
)


def build_timeline_from_events(events_path: Path | list[Path], project: str) -> list:
    """Build timeline from events.jsonl (grade9-pilot)."""
    events = []
    paths = events_path if isinstance(events_path, list) else [events_path]
    seen = set()
    for path in sorted(paths, key=str):
        if not path.exists():
            continue
        with open(path, encoding="utf-8") as f:
            for line_number, line in enumerate(f, 1):
                if not line.strip():
                    continue
                try:
                    ev = json.loads(line)
                except (ValueError, TypeError):
                    continue
                if not isinstance(ev, dict):
                    continue
                key = (ev.get('id') or ev.get('event_id') or
                       json.dumps(ev, sort_keys=True, ensure_ascii=False))
                if key in seen:
                    continue
                seen.add(key)
                ev['_source'] = 'events_jsonl'
                ev['_source_path'] = path.name
                ev['_source_line'] = line_number
                ev['project'] = project
                for k, v in list(ev.items()):
                    if isinstance(v, str):
                        ev[k] = scrub_chat_url(v)
                events.append(ev)
    events.sort(key=lambda e: (e.get('ts') or e.get('t') or '',
                                e.get('_source_path', ''), e.get('_source_line', 0)))
    return events


def build_timeline_from_threads(threads: list, inbox: list, project: str,
                                allowed_chats: set[str] | None = None,
                                shared_threads: set[int] | None = None) -> list:
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
            if cm and cm.group('project').strip() == project:
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
            if ev and ev['project'] == project and (
                    allowed_chats is None or ev['chat_id8'] in allowed_chats):
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
                # A shared issue's unbound verdict is not proof of either
                # chat generation. Keep single-agent frozen benchmark oracles.
                if (shared_threads and issue_num in shared_threads and
                        not any(chat in body for chat in (allowed_chats or set()))):
                    continue
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
