"""Source-first per-project projections; body moved unchanged from build_data."""
import json
import re
import owner_json
from pathlib import Path
from datetime import datetime, timezone
from landing_build.disagreement import project_disagreement
from landing_build.project_evidence import build_agent_evidence
from landing_build.project_view import (
    _issue_number, _SAFE_GH_LINK, _wp10_link, _wp10_external_links,
    _wp10_auto_response, _wp10_decision_label, _wp10_agent_status,
    _wp10_meter, _wp12_hold, _wp12_tree, _wp12_children,
    _wp12_evidence_head, V36_TITLE,
)
from landing_build.evidence_parse import (
    OUTSIDE_WRITE_RE, validated_issue_ref, registered_issue_numbers,
    collect_unparsed_evidence,
)
from landing_build.timeline import (
    build_timeline_from_events, build_timeline_from_threads,
)
from landing_build.freshness import (
    last_completed_cycle, derive_freshness, LIVENESS_OBSERVATION_LIMIT,
)
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
        ref = validated_issue_ref(item.get('evidence_thread'), registry, owner_json.REPO)
        if ref:
            n = ref[1]
            thread_owners[n] = thread_owners.get(n, 0) + 1

    # Agents
    agents = []
    for a in registry.get('agents', []):
        chat = a.get('chat_id8', '')
        thread_url = a.get('evidence_thread', '')
        # Extract thread number
        ref = validated_issue_ref(thread_url, registry, owner_json.REPO)
        thread_num = ref[1] if ref else None

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
        allowed = registered_issue_numbers(registry, owner_json.REPO)
        thread_list = [t for n, t in threads.items() if n in allowed]
        timeline = build_timeline_from_threads(
            thread_list, inbox, project_name, ({a['chat_id8'] for a in agents} or None),
            {n for n, count in thread_owners.items() if count > 1}
        )
        timeline_source = 'reconstructed'
    unparsed = collect_unparsed_evidence(registry, threads, project_name, owner_json.REPO)
    for event in timeline:
        if event.get('type') == 'OWNER_DECISION':
            event['decision_label'] = _wp10_decision_label(event)

    hold_report = _wp12_hold(registry.get('control'), agents)
    child_progress = _wp12_children(registry, child_observations)
    evidence_head_report = _wp12_evidence_head(
        registry.get('evidence'), pr_observation, registry.get('repository'))
    disagreement = project_disagreement(registry, status_thread or {},
                                        pr_observation, owner_json.REPO)
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
        **({'status_merge_disagreement': disagreement} if disagreement is not None else {}),
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
        **({'unparsed_evidence': unparsed} if unparsed else {}),
        'built_at': now.isoformat(),
    }, timeline


