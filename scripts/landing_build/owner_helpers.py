"""Immutable owner-input parsing state, form validation and trace."""
import re
import owner_json
from datetime import datetime, timezone
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


