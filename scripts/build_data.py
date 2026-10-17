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
import hashlib
import json
import os
import re
import sys
import owner_json
from next_move import load_project_moves
from ultra_economy import project as project_ultra_economy
from status_bar import build_status_bar
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


STATUS_RE = re.compile(
    r'STATUS v2\s*·\s*(?P<role>[^·]+?)\s*·\s*chat\s+(?:(?P<chat>[0-9a-f]{8})|n/a(?:\s+\([^)\n]*\))?)\s*·\s*working on\s+(?P<task>[^·]+?)\s*·\s*next\s+(?P<next>[^·]+?)\s*·\s*blocker\s+(?P<blocker>[^\n·]+)',
    re.MULTILINE
)

SUPERSEDED_RE = re.compile(
    r'supersedes\s+(?P<ref>[^\s;(]+)',
    re.IGNORECASE
)


from landing_build.evidence_parse import (
    id8, scrub_chat_url, EVIDENCE_RE, VERDICT_RE, OUTSIDE_WRITE_RE,
    parse_task_evidence, parse_verdict,
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


from landing_build.timeline import (
    build_timeline_from_events, build_timeline_from_threads,
    COORD_EVIDENCE_RE, NEEDS_YOU_RE, TIME_CORRECTED_RE, FOR_TC_RE,
)


from landing_build.freshness import (
    _utc_time, last_completed_cycle, derive_freshness,
    LIVENESS_OBSERVATION_LIMIT,
    _CYCLE_LINE, _COORD_RECEIPT_HEADER, _COORD_EVIDENCE_HEADER,
    _EPOCH_FIELD, _ISO_HEADER_TIME,
)


def git_blob_sha(path: Path):
    if not path.exists():
        return None
    data = path.read_bytes()
    return hashlib.sha1(f'blob {len(data)}\0'.encode('ascii') + data).hexdigest()


def _issue_number(url):
    match = re.search(r'/issues/(\d+)', url or '')
    return int(match.group(1)) if match else None



# WP10: registry projections report scoped claims, never confer authority.
_SAFE_GH_LINK = re.compile(
    r'^https://github\.com/([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)/(issues|pull)/(\d+)(?:#issuecomment-\d+)?$'
)


def _wp10_link(url, allowed):
    match = _SAFE_GH_LINK.fullmatch(url) if isinstance(url, str) else None
    return url if match and match.group(1) in allowed else None


def _wp10_external_links(registry):
    product = registry.get('repository')
    if not isinstance(product, str) or product == owner_json.REPO:
        return []
    result, seen = [], set()
    groups = [
        ('Issue', [registry.get('parent_issue'), registry.get('status_issue')]),
        ('Issue', registry.get('owning_issues', [])),
        ('PR', registry.get('pull_requests', [])),
        ('PR', registry.get('owning_prs', [])),
    ]
    for kind, entries in groups:
        for value in (entries if isinstance(entries, list) else []):
            url = _wp10_link(value.get('url') if isinstance(value, dict) else value,
                             {product})
            expected = '/issues/' if kind == 'Issue' else '/pull/'
            if url and expected in url and url not in seen:
                seen.add(url)
                result.append({'kind': kind, 'url': url, 'read_only': True})
    return result


def _wp10_auto_response(registry, now):
    """Project each recorded scope; retain the legacy single-dict projection."""
    source = registry.get('auto_response')

    def project_scope(data):
        allowed = data.get('allowed')
        until = data.get('until')
        forever = isinstance(until, str) and until.strip().lower() == 'forever'
        deadline = (_owner_time(until) if isinstance(until, str) and not forever
                    else None)
        state = ('UNKNOWN' if allowed not in ('yes', 'no', 'critical') or
                 (not forever and deadline is None)
                 else 'EXPIRED' if deadline is not None and deadline <= now
                 else 'NOT_ALLOWED' if allowed == 'no' else 'IN_SCOPE')
        words = data.get('owner_words')
        words = words if isinstance(words, str) else ''
        scope = data.get('scope')
        return {
            'scope': scope if isinstance(scope, str) else '',
            'allowed': allowed if allowed in ('yes', 'no', 'critical') else 'unknown',
            'until': 'forever' if forever else until if deadline else None,
            'state': state,
            'owner_words': words,
            'critical_rules': ('Critical requests require an Owner decision; '
                               'a delegated response is not Owner approval. ' + words),
        }

    if isinstance(source, list):
        return [project_scope(entry) for entry in source if isinstance(entry, dict)]
    if isinstance(source, dict):
        return project_scope(source)
    return None


def _wp10_decision_label(item):
    text = item.get('text', '') if isinstance(item, dict) else item
    text = text if isinstance(text, str) else ''
    words = item.get('owner_words') if isinstance(item, dict) else None
    if '(delegated)' in text.lower():
        return 'delegated (OwnerTeammember)'
    if (isinstance(words, str) and words.strip()) or re.search(
            r'''Owner(?:'s)? words:\s*["“]''', text, re.I):
        return 'Owner'
    return 'unverified'


def _wp10_agent_status(value):
    text = str(value or '').lower()
    for status in ('retired', 'standby', 'active', 'hold'):
        if text.startswith(status):
            return status
    return text or 'unknown'


def _wp10_meter(value):
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)) and 0 <= value <= 100:
        return value
    if isinstance(value, str):
        match = re.fullmatch(r'\s*(\d+(?:\.\d+)?)%?\s*', value)
        if match and 0 <= float(match.group(1)) <= 100:
            return float(match.group(1))
    return None



# WP12 projections are reports of recorded claims, never new Owner authority.
V36_TITLE = re.compile(
    r'^\[V3\.6\]\[O(\d+)\]\[(PLANNED|IN_PROGRESS|DONE)\]')


def _wp12_hold(control, agents):
    control = control if isinstance(control, dict) else {}
    raw = control.get('hold')
    if not raw and not any(a.get('status') == 'hold' for a in agents):
        return None
    # A plain string like "Owner HOLD 16 Oct 18:0x" is not a timestamp.
    # Expose it as the source claim without inventing precise Owner words/time.
    detail = raw if isinstance(raw, dict) else {}
    words = (detail.get('owner_words') or control.get('hold_owner_words')
             or control.get('owner_words') or '')
    since = detail.get('since') or control.get('hold_since') or control.get('since')
    if not isinstance(words, str):
        words = ''
    if not isinstance(since, str):
        since = ''
    return {'active': True,
            'recorded': raw if isinstance(raw, str) else '',
            'owner_words': words,
            'since': since}


def _wp12_tree(agents):
    ids = {a.get('chat_id8') for a in agents}
    return [
        {'chat_id8': a.get('chat_id8'),
         'alias': a.get('alias') or a.get('role') or 'agent',
         'status': a.get('status'),
         # Only same-project ID8 edges; never infer from a shared issue number.
         'reports_to': a.get('reports_to') if a.get('reports_to') in ids
                       and a.get('reports_to') != a.get('chat_id8') else None}
        for a in agents
    ]


def _wp12_children(registry, observations):
    """A fraction is known only if every registered title was captured."""
    product = registry.get('repository')
    requested = registry.get('children', [])
    if not isinstance(requested, list) or not requested:
        return {'status': 'not_recorded', 'done': 0, 'total': 0, 'items': []}
    if len(requested) > 100:  # bound parse work even for repeated URLs
        return {'status': 'unknown', 'done': 0, 'total': len(requested),
                'items': []}
    valid, seen = [], set()
    for entry in requested:
        url = entry.get('url') if isinstance(entry, dict) else entry
        match = re.fullmatch(
            r'https://github\.com/([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)/issues/(\d+)',
            str(url or ''))
        if not match or match.group(1) != product:
            return {'status': 'unknown', 'done': 0, 'total': len(requested),
                    'items': []}
        if url not in seen:
            seen.add(url)
            valid.append(url)
    if len(valid) > 12:
        return {'status': 'unknown', 'done': 0, 'total': len(valid), 'items': []}
    entries = observations if isinstance(observations, list) else []
    keyed = {x.get('url'): x for x in entries if isinstance(x, dict)}
    items = []
    for url in valid:
        record = keyed.get(url, {})
        title = record.get('title')
        if record.get('repository') != product or not isinstance(title, str):
            return {'status': 'unknown', 'done': 0, 'total': len(valid),
                    'items': []}
        mt = V36_TITLE.match(title)
        if not mt:
            return {'status': 'unknown', 'done': 0, 'total': len(valid),
                    'items': []}
        items.append({'url': url, 'title': title, 'order': int(mt.group(1)),
                      'state': mt.group(2).upper(), 'read_only': True})
    return {'status': 'known', 'done': sum(x['state'] == 'DONE' for x in items),
            'total': len(items), 'items': items}


def _wp12_evidence_head(declaration, observations, repository):
    """Exactly one evidence schema at project or agent scope: evidence{pr_url,head}."""
    if declaration is None:
        return {'status': 'not_recorded'}
    if not isinstance(declaration, dict):
        return {'status': 'unknown'}
    expected, url = declaration.get('head'), declaration.get('pr_url')
    if not isinstance(expected, str) or not re.fullmatch(r'[0-9a-fA-F]{40}', expected):
        return {'status': 'unknown'}
    mt = re.fullmatch(
        r'https://github\.com/([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)/pull/(\d+)',
        str(url or ''))
    if not mt or mt.group(1) != repository:
        return {'status': 'unknown', 'evidence_head': expected}
    entries = observations if isinstance(observations, list) else (
        [observations] if isinstance(observations, dict) else [])
    found = [x for x in entries if isinstance(x, dict) and
             x.get('url') == url and x.get('repository') == repository]
    if len(found) != 1 or not re.fullmatch(
            r'[0-9a-fA-F]{40}', str(found[0].get('head') or '')):
        return {'status': 'unknown', 'evidence_head': expected}
    current = found[0]['head']
    return {'status': 'superseded' if current.lower() != expected.lower()
            else 'current', 'evidence_head': expected, 'current_head': current,
            'pr_url': url}


def build_project_data(root: Path, project_name: str, registry: dict,
                        threads: dict, inbox: list, events_path: Path | list[Path] | None,
                        source_meta: dict | None = None,
                        status_thread: dict | None = None,
                        now: datetime | None = None,
                        registry_blob_sha: str | None = None,
                        child_observations=None, pr_observation=None) -> dict:
    """Assemble the project data payload."""

    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError('now must be timezone-aware')
    now = now.astimezone(timezone.utc)
    thread_owners = {}
    for item in registry.get('agents', []):
        number = _issue_number(item.get('evidence_thread', ''))
        if number:
            thread_owners[number] = thread_owners.get(number, 0) + 1

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
        evidence = build_agent_evidence(
            thread_data, project_name, chat,
            shared=thread_owners.get(thread_num, 0) > 1
        )

        meter = _wp10_meter(a.get('handover_meter'))
        agents.append({
            'role': a.get('role', ''),
            'alias': a.get('alias', ''),
            'generation': a.get('generation', 1),
            'chat_id8': chat,
            'status': _wp10_agent_status(a.get('status')),
            'status_raw': a.get('status', ''),
            'retired': a.get('retired'),
            'handover_meter': meter,
            'chat_end_seen': a.get('chat_end_seen') is True,
            'chat_end_risk': ((meter is not None and meter >= 80)
                              or a.get('chat_end_seen') is True),
            'handover': _wp10_link(a.get('handover'), {
                owner_json.REPO, registry.get('repository')}),
            # A numeric issue id is not a repository identity. Only the
            # registry's own product repository can be linked as agent evidence.
            'evidence_thread_num': thread_num,
            'evidence_thread_url': _wp10_link(thread_url, {
                registry.get('repository')}),
            'reports_to': a.get('reports_to', ''),
            'evidence_head_status': _wp12_evidence_head(
                a.get('evidence'), pr_observation, registry.get('repository')),
            'branch': a.get('branch', ''),
            'started': a.get('started'),
            'evidence': evidence,
        })

    # Leases
    leases = [dict(item) for item in registry.get('leases', [])
              if isinstance(item, dict)]
    retired_chats = {a['chat_id8'] for a in agents if a['status'] == 'retired'}
    for lease in leases:
        holder = str(lease.get('holder') or lease.get('actor') or '')
        match = re.search(r'(?<![0-9a-f])[0-9a-f]{8}(?![0-9a-f])',
                          holder, re.IGNORECASE)
        holder_id8 = match.group(0) if match else None
        lease['holder_chat_id8'] = holder_id8
        lease['valid_for_active_agent'] = (
            None if holder_id8 is None else holder_id8 not in retired_chats
        )
        if holder_id8 in retired_chats:
            lease['warning'] = 'RETIRED_HOLDER'
        elif not holder_id8:
            lease['warning'] = 'UNVERIFIED_HOLDER'
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
    has_events = (any(p.exists() for p in events_path)
                  if isinstance(events_path, list) else
                  bool(events_path and events_path.exists()))
    if has_events:
        timeline = build_timeline_from_events(events_path, project_name)
        timeline_source = 'events_jsonl'
    else:
        # Reconstruct from threads + inbox
        allowed = {_issue_number(registry.get('status_comment') or
                                 registry.get('status_issue') or '')}
        allowed.update(_issue_number(a.get('evidence_thread'))
                       for a in registry.get('agents', []))
        thread_list = [t for n, t in threads.items() if n in allowed]
        timeline = build_timeline_from_threads(
            thread_list, inbox, project_name, {a['chat_id8'] for a in agents},
            {n for n, count in thread_owners.items() if count > 1}
        )
        timeline_source = 'reconstructed'
    for event in timeline:
        if event.get('type') == 'OWNER_DECISION':
            event['decision_label'] = _wp10_decision_label(event)

    hold_report = _wp12_hold(registry.get('control'), agents)
    child_progress = _wp12_children(registry, child_observations)
    evidence_head_report = _wp12_evidence_head(
        registry.get('evidence'), pr_observation, registry.get('repository'))
    capture = source_meta if isinstance(source_meta, dict) else None
    status_pointer = registry.get('status_comment') or registry.get('status_issue') or ''
    pinned = re.search(r'#issuecomment-(\d+)', status_pointer)
    last_cycle = last_completed_cycle(
        status_thread or {}, project_name, now,
        registry.get('control', {}).get('epoch'), inbox=inbox,
        pinned_comment_id=(pinned.group(1) if pinned else None),
        epoch_since=registry.get('control', {}).get('since'),
    )
    freshness = ('BENCHMARK' if capture and capture.get('status') == 'benchmark'
                 else derive_freshness(last_cycle, capture,
                                       registry.get('control', {}).get('hold'), now))
    health = {'status': capture.get('status', 'unknown') if capture else 'unknown',
              'errors': capture.get('errors', []) if capture else ['capture_manifest_missing']}
    source_commit = capture.get('source_commit') if capture else None
    source_capture_at = capture.get('source_capture_at') if capture else None

    return {
        'project': project_name,
        'schema_version': 'wp1a.1',
        'source_commit': source_commit,
        'registry_blob_sha': registry_blob_sha,
        'repository': registry.get('repository', ''),
        'auto_response': _wp10_auto_response(registry, now),
        'external_links': _wp10_external_links(registry),
        'hold_report': hold_report,
        'reporting_tree': _wp12_tree(agents),
        'child_progress': child_progress,
        'evidence_head_status': evidence_head_report,
        'source_capture_at': source_capture_at,
        'source_health': health,
        'source_refs': {
            'inbox': 'https://github.com/reallakshman19/CoordinatorLandingpage/issues/1',
            'status_issue': registry.get('status_comment') or registry.get('status_issue'),
            'registry_blob_sha': registry_blob_sha,
            'source_commit': source_commit,
        },
        'last_cycle_at': last_cycle,
        'freshness_status': freshness,
        'liveness_observation_limit': LIVENESS_OBSERVATION_LIMIT,
        'published_at': None,
        'stale_lease_count': sum(l.get('warning') == 'RETIRED_HOLDER' for l in leases),
        'registry': {
            'protocol': registry.get('protocol', ''),
            'repository': registry.get('repository', ''),
            'updated': registry.get('updated', ''),
            'control': registry.get('control', {}),
            'workflow': registry.get('workflow', {}),
            'source': registry.get('source', {}),
            'standing_owner_decisions': sod,
            'auto_response': registry.get('auto_response'),
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
        'built_at': now.isoformat(),
    }, timeline



# G02/G05/G06: projection is reporting, NOT authorization.
_OWNER_RECEIPT = re.compile(
    r'^HANDLED:\s*owner-input\s*#(?P<n>\d+)\s+receipt:\s*'
    r'(?P<url>https://github\.com/[\w.-]+/[\w.-]+/issues/\d+#issuecomment-\d+)\s*$',
    re.I | re.M)
_OWNER_ACK = re.compile(r'^ACK(?:NOWLEDGED)?:\s*(?:owner-input\s*)?#(\d+)\s*$',
                        re.I | re.M)
_OWNER_CLARIFY = re.compile(
    r'^NEEDS CLARIFICATION:\s*(?:owner-input\s*)?#(\d+)\b', re.I | re.M)
_OWNER_SUPERSEDES = re.compile(r'\bsupersedes\s+(?:owner-input\s*)?#(\d+)\b', re.I)
_OWNER_FROZEN = re.compile(r'^Frozen-SHA:\s*([0-9a-f]{40})\s*$', re.I | re.M)
_OWNER_REVIEW_SHA = re.compile(r'^Review-SHA:\s*([0-9a-f]{40})\s*$', re.I | re.M)
_OWNER_REVIEW_ROLE = re.compile(r'^Review-Role:\s*(\S+)\s*$', re.M)
_OWNER_REVIEW_TARGET = re.compile(r'^Review-Target:\s*#(\d+)\s*$', re.M)
_OWNER_REVIEW_RESULT = re.compile(r'^Review-Result:\s*(PASS|HOLD)\s*$', re.I | re.M)
_OWNER_PROTECTED = re.compile(
    r'\b(?:merge|release|publish|deploy|new[\s-]+chat|start[\s-]+agent|'
    r'writer[\s-]+grant|role[\s-]+change|acceptance|freeze|upload)\b', re.I)


def _owner_time(value):
    try:
        dt = datetime.fromisoformat((value or '').replace('Z', '+00:00'))
        return dt.astimezone(timezone.utc) if dt.tzinfo else None
    except (TypeError, ValueError, AttributeError):
        return None



_FORM_SECTION = re.compile(r'^###\s+(.+?)\s*$', re.M)
_OWNER_TITLE_PROJECT = re.compile(r'^\[Owner input\][^\n]*?\(([^()\n]+)\)\s*$', re.I)
_OWNER_TITLE = re.compile(r'^\[Owner input\](?:\s|$)', re.I)
_FORM_MAP = {
    'Project': 'project', 'Target': 'target', 'Input type': 'type',
    'Your instruction or message': 'text',
}


def owner_form_fields(body):
    """Read GitHub Issue Form markdown sections, NOT the raw form as text."""
    if not isinstance(body, str):
        return {}
    matches = list(_FORM_SECTION.finditer(body))
    sections = {}
    for i, marker in enumerate(matches):
        key = _FORM_MAP.get(marker.group(1).strip())
        if not key:
            continue
        end = matches[i + 1].start() if i + 1 < len(matches) else len(body)
        value = body[marker.end():end].strip()
        if value and value != '_No response_':
            sections[key] = value
    return sections


def owner_issue_is_labelled(issue):
    labels = issue.get('labels')
    if not isinstance(labels, list):
        return False
    return any((x.get('name') if isinstance(x, dict) else x) == 'owner-input'
               for x in labels)


_ISSUE_ASSOCIATIONS = frozenset(('OWNER', 'MEMBER', 'COLLABORATOR'))


# WP6: trace facts must be recorded links, not guessed status transitions.
_TRACE_LINK = re.compile(
    r'https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/'
    r'(?:issues|pull)/\d+(?:#issuecomment-\d+)?'
)
_TRACE_HEADINGS = (
    ('sent', re.compile(r'^(?:Sent to agent|FTC(?: relay)?):', re.I)),
    ('evidence', re.compile(r'^(?:Agent evidence|TASK EVIDENCE(?: v\d+)?):', re.I)),
    ('check', re.compile(r'^(?:Check|C1(?: verdict)?|B verdict):', re.I)),
)


def _owner_trace(issue, comments, number, repo, boundary, status, reason,
                 title_project, body_project, association, allowed_repos):
    """Report only links inside this issue's recorded, timestamped comments.

    Handoff/evidence/check links require explicit headings AND a real GitHub
    URL in an associated comment. Never infer them from a HANDLED claim.
    """
    issue_url = f'https://github.com/{repo}/issues/{number}'
    steps = {'posted': {'url': issue_url, 'at': issue.get('created_at')},
             'ack': None, 'sent': None, 'evidence': None, 'check': None,
             'result': None}
    for c in comments:
        stamp = _owner_time(c.get('created_at'))
        cid = c.get('id')
        if stamp is None or not isinstance(cid, int):
            continue
        if boundary and stamp <= boundary:
            continue
        if c.get('author_association') not in _ISSUE_ASSOCIATIONS:
            continue
        comment_url = issue_url + f'#issuecomment-{cid}'
        body = c.get('body') or ''
        ack = _OWNER_ACK.search(body)
        if ack and int(ack.group(1)) == number:
            steps['ack'] = {'url': comment_url, 'at': c['created_at']}
        handled = _OWNER_RECEIPT.search(body)
        if (handled and int(handled.group('n')) == number
                and handled.group('url').lower() == comment_url.lower()):
            steps['result'] = {
                'url': comment_url, 'at': c['created_at'],
                'accepted': status == 'HANDLED',
            }
        for line in body.splitlines():
            for key, pattern in _TRACE_HEADINGS:
                if not pattern.search(line):
                    continue
                link = _TRACE_LINK.search(line)
                if link and owner_json.linked_repo(link.group(0), allowed_repos):
                    steps[key] = {
                        'url': link.group(0), 'at': c['created_at'],
                        'source_url': comment_url,
                    }
    if reason == 'project_mismatch':
        why = (f'Form says {body_project or "not given"}, '
               f'title says {title_project or "not given"}. '
               'Waiting for Owner to clarify the project.')
        waiting = 'Owner'
    elif association not in _ISSUE_ASSOCIATIONS:
        why = ('The post has not been confirmed as coming from a '
               'repository-associated person; it is not an Owner instruction.')
        waiting = 'TeamCoordinator'
    elif reason == 'label_missing':
        why = ('This request is missing the owner-input label. '
               'Waiting for TeamCoordinator to check the label.')
        waiting = 'TeamCoordinator'
    elif status == 'HANDLED':
        why = ('A linked handler note is recorded. This is not '
               'proof of an agent review or Owner approval.')
        waiting = None
    elif status == 'ACKNOWLEDGED':
        why = ('The team acknowledged this request, but a confirmed '
               'result has not been recorded.')
        waiting = 'TeamCoordinator'
    elif status == 'NEEDS_CLARIFICATION':
        why = 'The team needs more information before this can be marked handled.'
        waiting = 'Owner'
    elif status == 'SUPERSEDED':
        why = 'A newer linked request replaces this one.'
        waiting = None
    else:
        why = 'No linked team acknowledgment or result has been recorded yet.'
        waiting = 'TeamCoordinator'
    return {'steps': steps, 'why': why, 'waiting_for': waiting}


def build_owner_inputs(issues, capture, repo='reallakshman19/CoordinatorLandingpage',
                       registered_repos=None):
    """Immutable, strictly linked versioned issue receipts; fail closed."""
    allowed_repos = {repo} | set(registered_repos or [])
    source_ok = (isinstance(capture, dict) and capture.get('status') == 'ok'
                 and 1 in capture.get('issues_fetched', [])
                 and capture.get('owner_inputs_complete') is True)
    by_num = {}
    for issue in sorted((i for i in (issues if isinstance(issues, list) else [])
                         if isinstance(i, dict) and isinstance(i.get('number'), int)),
                        key=lambda i: (i.get('updated_at') or '', i['number'])):
        by_num[issue['number']] = issue
    result = []
    for number, issue in sorted(by_num.items()):
        body = issue.get('body') or ''
        cm = {}
        for comment in issue.get('comments', []):
            if isinstance(comment, dict) and isinstance(comment.get('id'), int):
                cm[comment['id']] = comment
        comments = sorted(cm.values(),
                          key=lambda c: (c.get('created_at') or '', c['id']))
        events = {}
        for event in issue.get('events', []):
            if isinstance(event, dict) and isinstance(event.get('id'), int):
                events[event['id']] = event
        revisions = [_owner_time(e.get('created_at')) for e in events.values()
                     if e.get('event') in ('edited', 'reopened')]
        revisions = [v for v in revisions if v]
        created = _owner_time(issue.get('created_at'))
        # A row's "updated" clock is GitHub source activity, not an
        # invented ACK or Owner approval. A missing REST updated_at in test
        # fixtures can still be reconstructed from timestamped comments.
        activity = [created, _owner_time(issue.get('updated_at'))] + [
            _owner_time(c.get('updated_at') or c.get('created_at'))
            for c in comments
        ] + revisions
        activity = [v for v in activity if v is not None]
        last_updated = max(activity).isoformat() if activity else None
        boundary = max(revisions) if revisions else created
        state, receipt, previous_handled = 'OPEN', None, False
        for comment in comments:
            stamp = _owner_time(comment.get('created_at'))
            text = comment.get('body') or ''
            m = _OWNER_RECEIPT.search(text)
            expected_url = (f'https://github.com/{repo}/issues/{number}'
                            f'#issuecomment-{comment["id"]}')
            is_receipt = bool(m and int(m.group('n')) == number and
                              m.group('url').lower() == expected_url.lower())
            if stamp is None or (boundary and stamp <= boundary):
                previous_handled |= is_receipt and comment.get('author_association') in _ISSUE_ASSOCIATIONS
                continue
            if is_receipt and comment.get('author_association') in _ISSUE_ASSOCIATIONS:
                state, receipt = 'HANDLED', expected_url
            elif (m := _OWNER_CLARIFY.search(text)) and int(m.group(1)) == number and comment.get('author_association') in _ISSUE_ASSOCIATIONS:
                state, receipt = 'NEEDS_CLARIFICATION', None
            elif (m := _OWNER_ACK.search(text)) and int(m.group(1)) == number and comment.get('author_association') in _ISSUE_ASSOCIATIONS:
                if state != 'HANDLED':
                    state, receipt = 'ACKNOWLEDGED', None
        if previous_handled and revisions and state != 'HANDLED':
            state = 'NEEDS_CLARIFICATION'
        if state == 'HANDLED' and (not source_ok or
                                   issue.get('events_complete') is not True):
            state, receipt = 'NEEDS_CLARIFICATION', None
        form = owner_form_fields(body)
        title = issue.get('title') or ''
        title_match = _OWNER_TITLE_PROJECT.match(title.strip())
        title_project = title_match.group(1).strip() if title_match else ''
        body_project = (form.get('project') or '').strip()
        legacy_project = (issue.get('project') or '').strip()
        if not body_project:
            legacy = re.search(r'^Project:\s*(.+)$', body, re.M | re.I)
            body_project = legacy.group(1).strip() if legacy else ''
        mismatch = bool(title_project and body_project and
                        title_project.casefold() != body_project.casefold())
        # Conflicting Title/Form claims must NOT become a project assignment.
        project = '' if mismatch else (body_project or legacy_project or title_project)
        missing_label = bool(_OWNER_TITLE.match(title.strip())
                             and not owner_issue_is_labelled(issue))
        reason = None
        if mismatch:
            reason = 'project_mismatch'
        elif missing_label:
            reason = 'label_missing'
        if reason:
            state, receipt = 'NEEDS_CLARIFICATION', None
        fsha = _OWNER_FROZEN.search(body)
        frozen_sha = fsha.group(1).lower() if fsha else None
        review = {'state': 'UNVERIFIED', 'reason': 'review_missing_or_unbound',
                  'frozen_sha': frozen_sha, 'comment_id': None}
        for comment in comments:
            text = comment.get('body') or ''
            target = _OWNER_REVIEW_TARGET.search(text)
            sha = _OWNER_REVIEW_SHA.search(text)
            role = _OWNER_REVIEW_ROLE.search(text)
            verdict = _OWNER_REVIEW_RESULT.search(text)
            if not (target and sha and role and verdict):
                continue
            review['comment_id'] = comment['id']
            if int(target.group(1)) != number:
                review['reason'] = 'target_mismatch'
            elif not frozen_sha:
                review['reason'] = 'frozen_sha_missing'
            elif sha.group(1).lower() != frozen_sha:
                review['reason'] = 'sha_mismatch'
            elif role.group(1) != 'OwnerTeammember':
                review['reason'] = 'role_mismatch'
            elif verdict.group(1).upper() != 'PASS':
                review['reason'] = 'review_hold'
            else:
                review.update(state='MATCHED',
                              reason='sha_and_role_claim_match_not_owner_approval')
        association = issue.get('author_association') or ''
        outsider = association not in _ISSUE_ASSOCIATIONS
        if outsider:
            # Retain untrusted submissions for audit but never present them
            # as Owner instructions or allow claims in their bodies to act.
            review = {'state': 'UNVERIFIED', 'reason': 'outsider_author',
                      'frozen_sha': frozen_sha, 'comment_id': None}
        trace = _owner_trace(issue, comments, number, repo, boundary, state,
                             reason, title_project, body_project, association,
                             allowed_repos)
        sup = _OWNER_SUPERSEDES.search(body)
        result.append({
            'schema_version': 'wp1b.1', 'number': number,
            'issue_url': f'https://github.com/{repo}/issues/{number}',
            'type': form.get('type') or issue.get('type') or 'OWNER_INPUT',
            'target': form.get('target') or issue.get('target') or '',
            'text': scrub_chat_url((form.get('text') or body)[:300]),
            'project': project, 'ts': issue.get('created_at'),
            'updated_at': last_updated,
            'reason': reason,
            'flags': (['project_mismatch'] if mismatch else []) +
                     (['label_missing'] if missing_label else []),
            'label_missing': missing_label,
            'project_claims': {'title': title_project, 'form': body_project},
            'trace': trace,
            'author_association': association,
            'is_outsider': outsider,
            'author_classification': 'OUTSIDER' if outsider else 'ASSOCIATED_NOT_OWNER_PROOF',

            'issue_state': issue.get('state'), 'status': state,
            'state': state.lower(), 'needs_you': state != 'HANDLED' and not outsider,
            'receipt': receipt,
            'revision_time': boundary.isoformat() if boundary else None,
            'fresh_receipt_required': bool(previous_handled and revisions and
                                           state != 'HANDLED'),
            'closed_without_receipt': issue.get('state') == 'closed' and
                                      state != 'HANDLED',
            'supersedes': int(sup.group(1)) if sup else None,
            'superseded_by': None,
            'protected_action': bool(_OWNER_PROTECTED.search(
                (issue.get('title') or '') + '\n' + body)),
            'authority': 'UNVERIFIED', 'review': review, 'effective': False,
            'source_health': 'ok' if source_ok else 'UNVERIFIED',
        })
    index = {item['number']: item for item in result}
    for row in result:
        old = index.get(row['supersedes'])
        if (old and old is not row and old['project'] == row['project']
                and not row.get('is_outsider') and not old.get('is_outsider')):
            old.update(state='superseded', status='SUPERSEDED',
                       needs_you=False, superseded_by=row['number'],
                       effective=False, receipt=None)
            old['trace']['why'] = 'A newer linked request replaces this one.'
            old['trace']['waiting_for'] = None
    return result


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
    selected_registries = {}  # raw complete logs/*/registry.json, never UI summary
    all_timelines = {}
    evidence_names = {}
    owner_source, owner_capture = [], None
    if not benchmark_dirs:
        _owner_cache = cache_dir if cache_dir else root / '_live_cache'
        owner_source = load_json(_owner_cache / 'owner-inputs-source.json') or []
        owner_capture = load_json(_owner_cache / 'capture-info.json')

    # Reuse WP7's GitHub-provenance check; no typed role or unverified JSON
    # becomes an effective Next Move approval.
    verified_inputs = owner_json.read_committed_inputs(root) if not benchmark_dirs else []
    request_inputs = []
    for row in verified_inputs:
        if (row.get('source_kind') != 'json_file' or row.get('flags')
                or row.get('type') not in ('NEXT_MOVE_COMPOSE','NEXT_MOVE_APPROVAL')):
            continue
        candidate = root / 'logs' / row['project'] / 'inputs' / (row['id'] + '.json')
        raw = load_json(candidate)
        if isinstance(raw, dict):
            request_inputs.append({**row, 'text': raw.get('text')})
    for source_type, source_path in sources:
        if source_type == 'benchmark':
            project_name, registry, threads, inbox, events_path = load_benchmark(source_path)
            is_benchmark = True
            source_meta = {'status': 'benchmark', 'errors': []}
            registry_sha = git_blob_sha(source_path / 'logs' / 'registry.json')
        else:
            project_name = source_path.name
            registry_path = source_path / 'registry.json'
            registry = load_json(registry_path) or {}
            registry_sha = git_blob_sha(registry_path)
            _cache = cache_dir if cache_dir else root / '_live_cache'
            scoped = _cache / 'project-threads' / project_name
            if scoped.is_dir():
                threads, inbox = load_live_threads(_cache)
                # The sole source of this project's evidence/status is its
                # registry-keyed scope, not the global issue-number map.
                threads = {}
                for tf in scoped.glob('issue-*.json'):
                    item = load_json(tf)
                    if isinstance(item, dict) and isinstance(item.get('number'), int):
                        threads[item['number']] = item
            else:
                threads, inbox = load_live_threads(_cache)
            source_meta = load_json(_cache / 'capture-info.json')
            events_path = sorted(source_path.rglob('events.jsonl'))
            is_benchmark = False

        # Per-project external title/head observations are read-only GitHub
        # capture outputs. Missing observations never count as DONE/current.
        extra = ((cache_dir if cache_dir else root / '_live_cache') /
                 'project-extras' / project_name)
        children_snapshot = (load_json(extra / 'children.json') if not is_benchmark
                             else None)
        pr_snapshot = (load_json(extra / 'pr-heads.json') if not is_benchmark
                       else None)
        status_num = _issue_number(
            registry.get('status_comment') or registry.get('status_issue') or ''
        )
        status_thread = threads.get(status_num, {}) if status_num else {}
        current_meta = dict(source_meta) if isinstance(source_meta, dict) else None
        if not is_benchmark and current_meta and status_num and status_num not in threads:
            current_meta['status'] = 'degraded'
            current_meta['errors'] = list(current_meta.get('errors', [])) + [
                f'status_missing:{project_name}'
            ]
        project_data, timeline = build_project_data(
            root, project_name, registry, threads, inbox, events_path,
            source_meta=current_meta, status_thread=status_thread,
            registry_blob_sha=registry_sha,
            child_observations=children_snapshot,
            pr_observation=pr_snapshot
        )
        # WP13 publisher validates read-only Next Move source records. Nothing
        # is created or altered under logs/; invalid records are quarantined.
        agent_heads = {
            a['chat_id8']: a['evidence_head_status']['current_head']
            for a in project_data['agents']
            if (a.get('evidence_head_status') or {}).get('current_head')
        }
        next_view = load_project_moves(
            source_path if not is_benchmark else source_path / 'logs',
            registry, project_data['agents'], threads, now=datetime.now(timezone.utc),
            registry_sha=registry_sha, evidence_heads=agent_heads,
            owner_inputs=request_inputs if not is_benchmark else [])
        # Optional manually committed evaluator report: never substitute
        # its proposed heartbeat for a moves.jsonl EVALUATED row.
        if not is_benchmark and project_name == 'landing-live':
            from next_move_evaluator import cross_check
            published_eval = load_json(source_path / 'next-move-evaluation.json')
            next_view['evaluator_cross_check'] = cross_check(
                next_view, published_eval, registry_sha, datetime.now(timezone.utc))
        else:
            next_view['evaluator_cross_check'] = {
                'status': 'not_recorded', 'mismatches': [], 'observed_at': None}
        # UEM is an opt-in, read-only overlay. It never creates moves or timers.
        next_view['ultra_economy'] = project_ultra_economy(
            registry, project_data['agents'], threads, next_view,
            now=datetime.now(timezone.utc))
        project_data['next_move'] = next_view
        project_data['is_benchmark'] = is_benchmark
        project_data['benchmark_snapshot'] = (
            load_json(source_path / 'MANIFEST.json') or {}
        ).get('snapshot') if is_benchmark else None

        selected_registries[project_name] = registry
        all_projects.append(project_data)
        all_timelines[project_name] = timeline

        # Save per-agent evidence
        for agent in project_data['agents']:
            aid = agent['chat_id8']
            if aid:
                payload = {'project': project_name, 'agent': agent,
                           'built_at': project_data['built_at']}
                save_json(out_dir / f'evidence-{project_name}-{aid}.json', payload)
                if aid not in evidence_names:
                    evidence_names[aid] = project_name
                    save_json(out_dir / f'evidence-{aid}.json', payload)
                elif evidence_names[aid] != project_name:
                    save_json(out_dir / f'evidence-{aid}.json', {
                        'collision': True, 'agent': None,
                        'source_health': {'status': 'ambiguous_agent_id8'},
                        'projects': [evidence_names[aid], project_name],
                    })

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

    # WP16 covers the entire selected registry roster, not just the older
    # dashboard's top-level agent projection. Both OT/TC views use this one file.
    status_bar = build_status_bar(
        selected_registries,
        {pd['project']: pd for pd in all_projects},
        now=datetime.now(timezone.utc))
    if not status_bar['coverage']['complete']:
        raise ValueError('WP16 selected registry roster coverage incomplete')
    save_json(out_dir / 'status-bar.json', status_bar)
    status_by_project = {p['project']: p for p in status_bar['projects']}
    # Save projects summary
    summary = []
    for pd in all_projects:
        summary.append({
            'project': pd['project'],
            'repository': pd['registry']['repository'],
            'schema_version': pd['schema_version'],
            'source_commit': pd['source_commit'],
            'registry_blob_sha': pd['registry_blob_sha'],
            'source_capture_at': pd['source_capture_at'],
            'source_health': pd['source_health'],
            'source_refs': pd['source_refs'],
            'last_cycle_at': pd['last_cycle_at'],
            'freshness_status': pd['freshness_status'],
            'liveness_observation_limit': pd['liveness_observation_limit'],
            'published_at': pd['published_at'],
            'stale_lease_count': pd['stale_lease_count'],
            'auto_response': pd['auto_response'],
            'external_links': pd['external_links'],
            'hold_report': pd['hold_report'],
            'reporting_tree': pd['reporting_tree'],
            'child_progress': pd['child_progress'],
            'evidence_head_status': pd['evidence_head_status'],
            'next_move': pd['next_move'],
            'status_bar': status_by_project[pd['project']],
            'control': pd['registry']['control'],
            'workflow': pd['registry']['workflow'],
            'agents': [
                {
                    'role': a['role'],
                    'alias': a.get('alias', ''),
                    'generation': a['generation'],
                    'chat_id8': a['chat_id8'],
                    'status': a['status'],
                    'handover_meter': a['handover_meter'],
                    'chat_end_seen': a['chat_end_seen'],
                    'chat_end_risk': a['chat_end_risk'],
                    'handover': a['handover'],
                    'evidence_thread_num': a['evidence_thread_num'],
                    'evidence_thread_url': a['evidence_thread_url'],
                    'reports_to': a['reports_to'],
                    'evidence_head_status': a['evidence_head_status'],
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
    if not benchmark_dirs:
        registered = {pd['registry'].get('repository') for pd in all_projects
                      if isinstance(pd['registry'].get('repository'), str)}
        issue_rows = build_owner_inputs(owner_source, owner_capture,
                                        registered_repos=registered)
        save_json(out_dir / 'owner-inputs.json', issue_rows + verified_inputs)

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
