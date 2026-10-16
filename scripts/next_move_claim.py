#!/usr/bin/env python3
"""WP14 opt-in GitHub Contents claim create/CAS helper (landing-live only).

No background send, chat delivery, token storage, or transition writing.
Use --execute only when an authorized coordinator deliberately claims a move.
GitHub 409/422 contention is failure, never retried as an unconditional PUT.
"""
import argparse
import base64
from datetime import datetime, timedelta, timezone
import json
import re
import subprocess
from urllib.parse import quote

import next_move

REPOSITORY = "reallakshman19/CoordinatorLandingpage"
PROJECT = "landing-live"


class ClaimRefused(ValueError):
    pass


class NotFound(ClaimRefused):
    pass


class GHTransport:
    def get(self, path):
        try:
            result = subprocess.run(["gh", "api", path], text=True,
                                    capture_output=True, check=True)
        except subprocess.CalledProcessError as exc:
            if re.search(r"(HTTP 404|404 Not Found)", exc.stderr or ""):
                raise NotFound("remote_resource_absent") from exc
            raise ClaimRefused("remote_api_read_failed") from exc
        return json.loads(result.stdout)

    def put(self, path, fields):
        cmd = ["gh", "api", "-X", "PUT", path]
        for key, value in fields.items():
            cmd.extend(["-f", key + "=" + str(value)])
        try:
            result = subprocess.run(cmd, text=True, capture_output=True, check=True)
        except subprocess.CalledProcessError as exc:
            message = exc.stderr or ""
            if re.search(r"(HTTP\s+409|409\s+Conflict|HTTP\s+422|422\s+Unprocessable)", message, re.I):
                raise ClaimRefused("claim_contents_conflict_409_or_422") from exc
            raise ClaimRefused("remote_api_write_failed") from exc
        try:
            return json.loads(result.stdout)
        except ValueError as exc:
            raise ClaimRefused("remote_api_write_response_invalid") from exc


def _contents(api, path, branch):
    result = api.get("/repos/" + REPOSITORY + "/contents/" + path +
                     "?ref=" + quote(branch, safe=""))
    if not isinstance(result, dict) or not isinstance(result.get("sha"), str):
        raise ClaimRefused("source_sha_unavailable")
    if not re.fullmatch(r"[0-9a-f]{40}", result["sha"]):
        raise ClaimRefused("source_sha_invalid")
    try:
        decoded = base64.b64decode(result["content"], validate=False).decode("utf-8")
    except (ValueError, KeyError, UnicodeDecodeError, TypeError) as exc:
        raise ClaimRefused("source_content_unavailable") from exc
    return result["sha"], decoded


def _optional_contents(api, path, branch):
    try:
        return _contents(api, path, branch)
    except NotFound:
        return None


def _load_json(text):
    try:
        return json.loads(text)
    except ValueError as exc:
        raise ClaimRefused("remote_json_invalid") from exc


def checked_context(api, branch, move_id, registry_sha, now):
    if not isinstance(branch, str) or not re.fullmatch(r"[A-Za-z0-9._/-]{1,100}", branch):
        raise ClaimRefused("branch_invalid")
    if not isinstance(move_id, str) or not next_move.ID.fullmatch(move_id):
        raise ClaimRefused("move_id_invalid")
    reg_sha, reg_text = _contents(api, "logs/landing-live/registry.json", branch)
    if reg_sha != registry_sha:
        raise ClaimRefused("registry_basis_moved")
    registry = _load_json(reg_text)
    if registry.get("project") != PROJECT or registry.get("repository") != REPOSITORY:
        raise ClaimRefused("wrong_project")
    if not (registry.get("next_move") or {}).get("pilot") or (
            registry.get("control") or {}).get("hold"):
        raise ClaimRefused("pilot_off_or_hold")
    _, move_text = _contents(api, "logs/landing-live/moves/" + move_id + ".json", branch)
    move = _load_json(move_text)
    if move.get("project") != PROJECT or move.get("id") != move_id:
        raise ClaimRefused("move_source_invalid")
    if move.get("basis", {}).get("registry_sha") != reg_sha:
        raise ClaimRefused("move_basis_stale")
    try:
        ledger = _optional_contents(api, "logs/landing-live/moves.jsonl", branch)
    except ClaimRefused:
        raise
    rows = []
    if ledger:
        for line in ledger[1].splitlines():
            if line.strip():
                rows.append(_load_json(line))
    # Prove there is no other active move addressed to this recipient.
    # Bounded list of the same project only; fail closed if the listing or an
    # item cannot be read. A supersedes declaration does not erase an active
    # predecessor without its own SUPERSEDED transition.
    listing = api.get("/repos/" + REPOSITORY +
                      "/contents/logs/landing-live/moves?ref=" +
                      quote(branch, safe=""))
    if not isinstance(listing, list) or len(listing) > next_move.MAX_FILES + 1:
        raise ClaimRefused("move_listing_unavailable_or_over_limit")
    other = {}
    for entry in listing:
        if not isinstance(entry, dict):
            raise ClaimRefused("move_listing_invalid")
        name = entry.get("name")
        if entry.get("type") == "dir" and name == "claims":
            continue
        if entry.get("type") != "file" or not isinstance(name, str) or (
                not next_move.ID.fullmatch(name[:-5]) or
                not name.endswith(".json")):
            raise ClaimRefused("move_listing_invalid")
        if name == move_id + ".json":
            continue
        _, value = _contents(api, "logs/landing-live/moves/" + name, branch)
        record = _load_json(value)
        if not isinstance(record, dict) or next_move.schema(
                record, PROJECT, name):
            raise ClaimRefused("other_move_invalid")
        other[record["id"]] = record
    # Even malformed/unfinished transitions on an *other* addressed move
    # block new claims if an ACTIVE state is recorded; reconcile first.
    for other_id, item in other.items():
        if item.get("class") != "Dispatch" or item["to"]["id8"] != move["to"]["id8"]:
            continue
        states = [row.get("state") for row in rows if isinstance(row, dict)
                  and row.get("move") == other_id]
        if states and states[-1] in next_move.ACTIVE:
            raise ClaimRefused("recipient_has_active_dispatch")
    # Publication/approval are authoritative only in the move lifecycle,
    # not in a draft Owner-input file.
    claim_path = "logs/landing-live/moves/claims/" + move_id + ".json"
    existing = _optional_contents(api, claim_path, branch)
    claims = {move_id: _load_json(existing[1])} if existing else {}
    valid, rejected, _ = next_move.validate_records(
        dict(registry, _registry_sha=reg_sha),
        {move_id + ".json": move}, rows, claims, now)
    if rejected or len(valid) != 1:
        raise ClaimRefused("move_not_valid:" + ",".join(
            str(x.get("reasons")) for x in rejected))
    return valid[0], claim_path, existing


def make_claim(api, branch, move_id, registry_sha, claimant,
               action="create", now=None, ttl_minutes=15):
    """Execute a single create (without sha) or CAS (with latest sha).

    A separate approved transition is required for CLAIMED. This helper
    never appends moves.jsonl or sends a message.
    """
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None or not 0 < ttl_minutes <= 15 or not next_move.actor(claimant):
        raise ClaimRefused("ttl_or_claimant_invalid")
    record, path, existing = checked_context(api, branch, move_id, registry_sha, now)
    if claimant["id8"] != record["to"]["id8"]:
        raise ClaimRefused("claimant_not_recipient")
    if record["state"] in ("SEND_INTENT", "DELIVERY_UNCERTAIN", "NOT_SENT"):
        raise ClaimRefused("delivery_requires_reconciliation")
    if record["state"] not in ("APPROVED", "CLAIMED"):
        raise ClaimRefused("move_not_approved_or_claimed")
    if action == "create":
        if existing is not None or record["state"] != "APPROVED":
            raise ClaimRefused("claim_already_exists_or_not_approved")
    elif action == "renew":
        if existing is None or record["state"] != "CLAIMED":
            raise ClaimRefused("cas_claim_missing_or_not_claimed")
        old = _load_json(existing[1])
        prior = next_move.stamp(old.get("expires_at"))
        if not prior:
            raise ClaimRefused("prior_claim_invalid")
        if prior > now and old.get("by") != claimant:
            raise ClaimRefused("unexpired_claim_owned_by_other_actor")
        # An expired CLAIMED record is explicitly flagged and must be
        # rechecked against the remote ledger and current registered basis.
    else:
        raise ClaimRefused("action_invalid")
    expires = now + timedelta(minutes=ttl_minutes)
    body = {"by": claimant, "claimed_at": now.isoformat(),
            "expires_at": expires.isoformat()}
    fields = {"message": f"Next Move {action} claim {move_id}",
              "content": base64.b64encode(json.dumps(
                  body, sort_keys=True).encode("utf-8")).decode("ascii"),
              "branch": branch}
    if action == "renew":
        # A real GitHub Contents CAS. Never supply sha for create.
        fields["sha"] = existing[0]
    return api.put("/repos/" + REPOSITORY + "/contents/" + path, fields)


def main():
    parser = argparse.ArgumentParser(description="Explicit Next Move claim action")
    parser.add_argument("--execute", action="store_true",
                        help="required: no implicit remote write")
    parser.add_argument("--action", choices=("create", "renew"), required=True)
    parser.add_argument("--move", required=True)
    parser.add_argument("--branch", required=True)
    parser.add_argument("--registry-sha", required=True)
    parser.add_argument("--role", required=True)
    parser.add_argument("--id8", required=True)
    parser.add_argument("--ttl", type=int, default=15)
    args = parser.parse_args()
    if not args.execute:
        parser.error("refusing remote write: --execute required")
    result = make_claim(GHTransport(), args.branch, args.move, args.registry_sha,
                        {"role": args.role, "id8": args.id8},
                        args.action, ttl_minutes=args.ttl)
    print(json.dumps({"commit_sha": (result.get("commit") or {}).get("sha"),
                      "file_sha": (result.get("content") or {}).get("sha"),
                      "claim": args.move, "action": args.action}))


if __name__ == "__main__":
    main()
