"""WP10 / WP12 project summary helpers, pure read-only reports."""
import re
import owner_json
from landing_build.owner_helpers import _owner_time
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
    text = str(value or '').strip().casefold()
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


