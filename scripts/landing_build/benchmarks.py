"""Benchmark fixture and live GitHub scope readers; unchanged loader bodies."""
from pathlib import Path
from landing_build.file_io import load_json
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


