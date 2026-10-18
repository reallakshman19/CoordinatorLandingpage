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

from landing_build.file_io import load_json, save_json, git_blob_sha
from landing_build.project_evidence import STATUS_RE, SUPERSEDED_RE, build_agent_evidence
from landing_build.project_view import (
    _issue_number, _SAFE_GH_LINK, _wp10_link, _wp10_external_links,
    _wp10_auto_response, _wp10_decision_label, _wp10_agent_status,
    _wp10_meter, _wp12_hold, _wp12_tree, _wp12_children,
    _wp12_evidence_head, V36_TITLE,
)
from landing_build.owner_helpers import (
    _owner_time, _owner_trace, owner_form_fields, owner_issue_is_labelled,
    _OWNER_RECEIPT, _OWNER_ACK, _OWNER_CLARIFY, _OWNER_SUPERSEDES,
    _OWNER_FROZEN, _OWNER_REVIEW_SHA, _OWNER_REVIEW_ROLE,
    _OWNER_REVIEW_TARGET, _OWNER_REVIEW_RESULT, _OWNER_PROTECTED,
    _FORM_SECTION, _OWNER_TITLE_PROJECT, _OWNER_TITLE, _FORM_MAP,
    _ISSUE_ASSOCIATIONS, _TRACE_LINK, _TRACE_HEADINGS,
)
from landing_build.owner_inputs import build_owner_inputs
from landing_build.benchmarks import load_benchmark, load_live_threads
from landing_build.project_intent import project_intake
from landing_build.v36_scoreboard import scoreboard_project
from landing_build import project_data as _project_data
from landing_build.disagreement import project_disagreement
from landing_build.evidence_parse import (
    id8, scrub_chat_url, EVIDENCE_RE, VERDICT_RE, OUTSIDE_WRITE_RE,
    parse_task_evidence, parse_verdict, validated_issue_ref,
    registered_issue_numbers, collect_unparsed_evidence,
)
from landing_build.timeline import (
    build_timeline_from_events, build_timeline_from_threads,
    COORD_EVIDENCE_RE, NEEDS_YOU_RE, TIME_CORRECTED_RE, FOR_TC_RE,
)
from landing_build.freshness import (
    _utc_time, last_completed_cycle, derive_freshness,
    LIVENESS_OBSERVATION_LIMIT, _CYCLE_LINE, _COORD_RECEIPT_HEADER,
    _COORD_EVIDENCE_HEADER, _EPOCH_FIELD, _ISO_HEADER_TIME,
)


def build_project_data(*args, **kwargs):
    """Preserve original public import and frozen-oracle monkeypatch points."""
    _project_data.datetime = datetime
    _project_data.collect_unparsed_evidence = collect_unparsed_evidence
    return _project_data.build_project_data(*args, **kwargs)


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
        lineage_snapshot = (load_json(extra / 'lineage.json') if not is_benchmark
                            else None)
        status_ref = validated_issue_ref(
            registry.get('status_comment') or registry.get('status_issue'),
            registry, owner_json.REPO)
        status_num = status_ref[1] if status_ref else None
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
        if isinstance(lineage_snapshot, list) and lineage_snapshot:
            project_data['lineage'] = lineage_snapshot
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
        if not is_benchmark:
            project_data.update(project_intake(project_name, registry, lineage_snapshot, inbox, (_cache / 'inbox-1.json').is_file(), owner_json.REPO))
            v36 = scoreboard_project(root, project_name, registry, project_data)
            if v36 is not None:
                project_data['v36_scoreboard'] = v36
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
        now=datetime.now(timezone.utc),
        include_continuity=not bool(benchmark_dirs))
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
            **({'lineage': pd['lineage']} if pd.get('lineage') else {}),
            **{key: pd[key] for key in ('originals', 'improvements', 'succession')
               if key in pd},
            **({'status_merge_disagreement': pd['status_merge_disagreement']}
               if pd.get('status_merge_disagreement') is not None else {}),
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
            **({'v36_scoreboard': pd['v36_scoreboard']}
               if 'v36_scoreboard' in pd else {}),
            **({k: pd[k] for k in ('intent', 'amendments')} if not pd['is_benchmark'] else {}),
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
            **({'unparsed_evidence': pd['unparsed_evidence']}
               if pd.get('unparsed_evidence') else {}),
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
