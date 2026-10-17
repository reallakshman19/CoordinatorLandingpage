"""Immutable linked owner-input receipts, with shared owner helper state."""
import re
import owner_json
from landing_build.evidence_parse import scrub_chat_url
from landing_build.owner_helpers import (
    _owner_time, _owner_trace, owner_form_fields, owner_issue_is_labelled,
    _OWNER_RECEIPT, _OWNER_ACK, _OWNER_CLARIFY, _OWNER_SUPERSEDES,
    _OWNER_FROZEN, _OWNER_REVIEW_SHA, _OWNER_REVIEW_ROLE,
    _OWNER_REVIEW_TARGET, _OWNER_REVIEW_RESULT, _OWNER_PROTECTED,
    _FORM_SECTION, _OWNER_TITLE_PROJECT, _OWNER_TITLE, _FORM_MAP,
    _ISSUE_ASSOCIATIONS, _TRACE_LINK, _TRACE_HEADINGS,
)
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


