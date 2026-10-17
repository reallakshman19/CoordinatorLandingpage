"""STATUS v2 and per-agent recorded evidence helpers."""
import re
STATUS_RE = re.compile(
    r'STATUS v2\s*·\s*(?P<role>[^·]+?)\s*·\s*chat\s+(?:(?P<chat>[0-9a-f]{8})|n/a(?:\s+\([^)\n]*\))?)\s*·\s*working on\s+(?P<task>[^·]+?)\s*·\s*next\s+(?P<next>[^·]+?)\s*·\s*blocker\s+(?P<blocker>[^\n·]+)',
    re.MULTILINE
)

SUPERSEDED_RE = re.compile(
    r'supersedes\s+(?P<ref>[^\s;(]+)',
    re.IGNORECASE
)

from landing_build.disagreement import project_disagreement
from landing_build.evidence_parse import (
    id8, scrub_chat_url, EVIDENCE_RE, VERDICT_RE, OUTSIDE_WRITE_RE,
    parse_task_evidence, parse_verdict, validated_issue_ref,
    registered_issue_numbers, collect_unparsed_evidence,
)

def build_agent_evidence(thread: dict, project: str | None = None,
                         chat_id8: str | None = None, shared: bool = False) -> list:
    """Build a list of evidence blocks (with interleaved verdicts) from a thread."""
    items = []
    for c in thread.get('comments', []):
        body = c.get('body', '')
        cid = c.get('id', 0)
        ts = c.get('created_at', '')

        ev = parse_task_evidence(body, cid, ts)
        if ev:
            if chat_id8 and ev['chat_id8'] != chat_id8:
                continue
            if project and ev['project'] != project:
                continue
            # Check for replaces marker
            rep = re.search(r'replaces #(\d+)', body, re.IGNORECASE)
            if rep:
                ev['replaces'] = int(rep.group(1))
            items.append({'type': 'evidence', **ev})
            continue

        verd = parse_verdict(body, cid, ts)
        if verd:
            # Shared thread verdicts are unbound unless they name this chat.
            if shared and (not chat_id8 or chat_id8 not in body):
                continue
            items.append({'type': 'verdict', **verd})
            continue

        # STATUS v2 line
        sm = STATUS_RE.search(body)
        if sm:
            if chat_id8 and sm.group('chat') != chat_id8:
                continue
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
        if 'RETIRED' in body and 'OwnerTeammember' in body and (
                not shared or (chat_id8 and chat_id8 in body)):
            items.append({
                'type': 'retired',
                'comment_id': cid,
                'ts': ts,
                'raw': scrub_chat_url(body),
            })

    return items

