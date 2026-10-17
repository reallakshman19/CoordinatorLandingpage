#!/usr/bin/env python3
"""Fail-closed, read-only Pages publisher qualification and deployed readback.

No production write happens in this module; only the single deploy.yml job can
upload and deploy.  A failed GitHub source capture must STOP before upload.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys
import time
from urllib.parse import urljoin, urlsplit
from urllib.request import Request, urlopen


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def assert_sha(sha):
    if not isinstance(sha, str) or not re.fullmatch(r"[a-fA-F0-9]{40}", sha):
        raise ValueError("source commit must be exactly 40 hex characters")
    return sha.lower()


def check_capture(cache_dir, repo, source_commit):
    """Fail (never pretend fresh) on ANY degraded or incomplete source fetch."""
    source_commit = assert_sha(source_commit)
    manifest = read_json(Path(cache_dir) / "capture-info.json")
    errors = manifest.get("errors")
    if (manifest.get("repository") != repo or
            manifest.get("status") != "ok" or
            not isinstance(errors, list) or errors or
            manifest.get("owner_inputs_complete") is not True or
            1 not in manifest.get("issues_fetched", []) or
            manifest.get("source_commit", "").lower() != source_commit or
            not isinstance(manifest.get("statuses"), dict)):
        raise ValueError("degraded/incomplete capture — refuse publish")
    captured = manifest.get("source_capture_at")
    try:
        dt = datetime.fromisoformat(captured.replace("Z", "+00:00"))
    except (ValueError, AttributeError) as exc:
        raise ValueError("missing capture clock — refuse publish") from exc
    if dt.tzinfo is None or abs((datetime.now(timezone.utc)-dt).total_seconds()) > 1200:
        raise ValueError("capture clock is stale or invalid — refuse publish")
    if not (Path(cache_dir) / "inbox-1.json").is_file():
        raise ValueError("protocol inbox #1 missing — refuse publish")
    if not (Path(cache_dir) / "owner-inputs-source.json").is_file():
        raise ValueError("Owner-input source missing — refuse publish")
    return manifest


def check_artifact(artifact, logs_dir, manifest, expected_names=None):
    """Verify live output from real registries and independent benchmark path."""
    artifact = Path(artifact)
    live_dir = artifact / "data"
    summary = read_json(live_dir / "projects.json")
    owner_inputs = read_json(live_dir / "owner-inputs.json")
    if not isinstance(summary, list) or not summary:
        raise ValueError("no live projects; refusing benchmark-only publication")
    if not isinstance(owner_inputs, list):
        raise ValueError("Owner-inputs projection missing")
    registries = sorted(Path(logs_dir).glob("*/registry.json"))
    names = {r.parent.name for r in registries}
    if not names:
        raise ValueError("no current registries")
    if expected_names is not None and set(expected_names) != names:
        raise ValueError("expected project set disagrees with current registries")
    if {p.get("project") for p in summary} != names:
        raise ValueError("live projects do not exactly match current registries")
    sha_source = assert_sha(manifest["source_commit"])
    for p in summary:
        project = p["project"]
        path = Path(logs_dir) / project / "registry.json"
        blob = path.read_bytes()
        git_blob = hashlib.sha1(
            b"blob " + str(len(blob)).encode() + b"\0" + blob
        ).hexdigest()
        if (p.get("is_benchmark") is not False or
                p.get("registry_blob_sha") != git_blob or
                p.get("source_commit") != sha_source or
                p.get("source_capture_at") != manifest["source_capture_at"] or
                not isinstance(p.get("built_at"), str) or
                p.get("source_health", {}).get("status") != "ok" or
                p.get("published_at", "absent") is not None):
            raise ValueError("stale/mismatched live source: " + project)
        if not (live_dir / ("project-" + project + ".json")).is_file():
            raise ValueError("missing live detail for " + project)
    # Benchmarks MUST exist, live exclusively in data/benchmarks, with all
    # benchmarks flagged. Live files cannot be rewritten by this build.
    benchmarks = read_json(live_dir / "benchmarks" / "projects.json")
    if (not isinstance(benchmarks, list) or not benchmarks or
            any(p.get("is_benchmark") is not True for p in benchmarks)):
        raise ValueError("benchmark tree missing or misclassified")
    if (artifact / "data" / "benchmarks" / "owner-inputs.json").exists():
        raise ValueError("live Owner-inputs illegally copied to benchmark path")
    if not (artifact / "index.html").is_file() or not (artifact / "protocol" / "TEAM_PROTOCOL.md").is_file():
        raise ValueError("site/protocol missing")
    return summary


def stamp_asset_urls(artifact, source_commit):
    """Version the *published* HTML; each commit gives JS/CSS a fresh URL."""
    version = assert_sha(source_commit)[:8]
    path = Path(artifact) / "index.html"
    html = path.read_text(encoding="utf-8")
    assets = sorted((Path(artifact) / "js").glob("*.js"))
    if not assets:
        raise ValueError("cannot version published index.html: missing site/js assets")
    changes = [
        ('href="style.css"', f'href="style.css?v={version}"'),
        ('</head>', f'  <meta name="site-version" content="{version}">\n</head>'),
    ]
    changes.extend((f'src="js/{asset.name}"',
                    f'src="js/{asset.name}?v={version}"') for asset in assets)
    if 'src="app.js"' in html:
        raise ValueError("cannot version published index.html: legacy app.js")
    for original, replacement in changes:
        if html.count(original) != 1:
            raise ValueError("cannot version published index.html: " + original)
        html = html.replace(original, replacement, 1)
    path.write_text(html, encoding="utf-8", newline="\n")
    print("SITE_ASSETS_VERSIONED=" + version)
    return version


def stamp(artifact, logs, cache_dir, repo, source_commit, run_id):
    manifest = check_capture(cache_dir, repo, source_commit)
    projects = check_artifact(artifact, logs, manifest)
    artifact = Path(artifact)
    data = artifact / "data"
    site_version = stamp_asset_urls(artifact, source_commit)
    # Hash the files that determine the visible live page; build-info itself
    # is separately hashed (no self-referential hash). All SHA values are
    # source readbacks, not a claim that GitHub Pages is already published.
    files = ["projects.json", "owner-inputs.json"] + [
        "project-" + p["project"] + ".json" for p in projects
    ]
    info = {
        "schema_version": "wp4.1",
        "source_commit": assert_sha(source_commit),
        "site_version": site_version,
        "source_capture_at": manifest["source_capture_at"],
        "built_at": datetime.now(timezone.utc).isoformat(),
        "published_at": None,
        "run_id": str(run_id),
        "capture_status": "ok",
        "repository": repo,
        "registry_blob_shas": {p["project"]: p["registry_blob_sha"]
                               for p in projects},
        "live_file_sha256": {name: sha256(data / name) for name in files},
        "benchmark_projects_sha256": sha256(data / "benchmarks" / "projects.json"),
    }
    out = artifact / "build-info.json"
    out.write_text(json.dumps(info, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print("BUILD_INFO_SHA256=" + sha256(out))
    return info


def verify_readback_bytes(expected_path, response, expected_source):
    expected_sha = sha256(expected_path)
    observed_sha = hashlib.sha256(response).hexdigest()
    if observed_sha != expected_sha:
        raise ValueError("deployed build-info SHA256 mismatch")
    observed = json.loads(response)
    if observed.get("source_commit") != assert_sha(expected_source):
        raise ValueError("deployed source SHA mismatch")
    if observed.get("site_version") != assert_sha(expected_source)[:8]:
        raise ValueError("deployed site version mismatch")
    if observed.get("capture_status") != "ok":
        raise ValueError("deployed capture status is not ok")
    return observed_sha


def deployed_readback(pages_url, expected_path, expected_source,
                      attempts=9, delay_seconds=10):
    if urlsplit(pages_url).scheme != "https":
        raise ValueError("deployed Pages URL must be HTTPS")
    endpoint = urljoin(pages_url.rstrip("/") + "/", "build-info.json")
    expected_run = read_json(expected_path).get("run_id")
    last = "not attempted"
    for attempt in range(attempts):
        try:
            request = Request(endpoint + "?readback=" + str(expected_run) +
                              "-" + str(attempt),
                              headers={"Cache-Control": "no-cache"})
            with urlopen(request, timeout=15) as response:
                if response.status != 200:
                    raise ValueError("HTTP " + str(response.status))
                payload = response.read(1_000_000)
            digest = verify_readback_bytes(expected_path, payload, expected_source)
            print("DEPLOYED_READBACK_OK sha256=" + digest +
                  " source_commit=" + expected_source +
                  " url=" + endpoint)
            return digest
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            last = type(exc).__name__ + ": " + str(exc)
            print("Readback attempt " + str(attempt + 1) + " failed: " + last,
                  file=sys.stderr)
            if attempt + 1 < attempts:
                time.sleep(delay_seconds)
    raise ValueError("deployed readback never matched: " + last)


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="operation", required=True)
    for op in ("capture", "stamp"):
        p = sub.add_parser(op)
        p.add_argument("--cache", required=True)
        p.add_argument("--repo", required=True)
        p.add_argument("--source", required=True)
        if op == "stamp":
            p.add_argument("--artifact", required=True)
            p.add_argument("--logs", default="logs")
            p.add_argument("--run-id", required=True)
    r = sub.add_parser("readback")
    r.add_argument("--url", required=True)
    r.add_argument("--expected", required=True)
    r.add_argument("--source", required=True)
    args = parser.parse_args()
    try:
        if args.operation == "capture":
            check_capture(args.cache, args.repo, args.source)
        elif args.operation == "stamp":
            stamp(args.artifact, args.logs, args.cache, args.repo,
                  args.source, args.run_id)
        else:
            deployed_readback(args.url, args.expected, args.source)
    except (ValueError, KeyError, OSError, TypeError, json.JSONDecodeError) as exc:
        print("PUBLISH_BLOCKED " + type(exc).__name__ + ": " + str(exc),
              file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
