"""Read-only cycle provenance and freshness; extracted unchanged from build_data."""

from datetime import datetime, timezone
import re


# Derived read-only cycle observation and capture provenance.
_CYCLE_LINE = re.compile(
    r'^(?:Coordinator last completed cycle|Cycle completed):[ \t]*(.+)$',
    re.MULTILINE | re.IGNORECASE,
)


def _utc_time(value):
    if not isinstance(value, str):
        return None
    value = value.strip().strip('*')
    try:
        dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
        if dt.tzinfo:
            return dt.astimezone(timezone.utc)
    except ValueError:
        pass
    for fmt in ('%d %b %Y %H:%M:%S %z', '%d%b%Y %H:%M:%S %z',
                '%d %B %Y %H:%M:%S %z', '%d %b %Y %H:%M %z'):
        try:
            return datetime.strptime(value, fmt).astimezone(timezone.utc)
        except ValueError:
            pass
    return None


_COORD_RECEIPT_HEADER = re.compile(
    r"^COORDINATOR RECEIPT\s*·\s*(?P<project>[^·\n]+?)\s*·\s*"
    r"(?:(?:epoch\s*(?P<epoch>\d+)\s*·\s*))?"
    r"(?P<when>[^\n]+)$", re.MULTILINE | re.IGNORECASE,
)
_COORD_EVIDENCE_HEADER = re.compile(
    r"^COORDINATOR EVIDENCE v1\s*·\s*(?P<project>[^·\n]+?)\s*·\s*"
    r"(?P<rest>[^\n]+)$", re.MULTILINE | re.IGNORECASE,
)
_EPOCH_FIELD = re.compile(r"(?:^|·)\s*epoch\s*(\d+)\s*(?:·|$)", re.IGNORECASE)
_ISO_HEADER_TIME = re.compile(r"20\d{2}-\d{2}-\d{2}T[0-9:.]+(?:Z|[+-]\d{2}:\d{2})")


# GitHub's issue author association fences public outsiders, but cannot prove
# which TEAM role posted: TeamCoordinator and OwnerTeammember share an account.
LIVENESS_OBSERVATION_LIMIT = (
    "GitHub OWNER/MEMBER/COLLABORATOR association excludes outsiders; "
    "team roles share one GitHub account, so the posting role cannot be "
    "distinguished. RUNNING-observed is scoped activity, not identity proof."
)


def last_completed_cycle(status_thread: dict, project: str, now: datetime,
                         epoch: int | None = None, inbox=None,
                         pinned_comment_id=None, epoch_since=None):
    """Observed coordinator activity from scoped status and hub receipts.

    A header must match project and current epoch (if present); receipts
    without an epoch must be newer than the registry's current-epoch start.
    A status-comment update is evidence only when pinned and parseable; a
    raw GitHub updated_at or foreign/malformed post is NOT a coordinator cycle.
    """
    times = []
    since = _utc_time(epoch_since)
    def accept(ts, explicit_epoch):
        if not ts or ts > now:
            return
        if epoch is not None and explicit_epoch is not None and str(explicit_epoch) != str(epoch):
            return
        if epoch is not None and explicit_epoch is None and (not since or ts < since):
            return
        if since and ts < since:
            return
        times.append(ts)

    def examine(comment, is_status=False):
        # Strictly require GitHub's source-provided author association. A
        # public issue comment from an outsider, or an absent association,
        # can NEVER promote observed liveness (including pinned edit-time).
        if comment.get("author_association") not in (
                "OWNER", "MEMBER", "COLLABORATOR"):
            return
        body = comment.get("body") or ""
        headers = list(_COORD_EVIDENCE_HEADER.finditer(body))
        receipts = list(_COORD_RECEIPT_HEADER.finditer(body))
        valid_header = False
        for m in headers:
            if m.group("project").strip() != project:
                continue
            e = _EPOCH_FIELD.search("· " + m.group("rest"))
            e = e.group(1) if e else None
            if epoch is not None and e is not None and str(e) != str(epoch):
                continue
            valid_header = True
            # Explicit completion line is authoritative over a header time.
            found_line = False
            for line in _CYCLE_LINE.finditer(body):
                stamp = _utc_time(line.group(1))
                if stamp:
                    accept(stamp, e)
                    found_line = True
            if not found_line:
                iso = _ISO_HEADER_TIME.search(m.group("rest"))
                if iso:
                    accept(_utc_time(iso.group(0)), e)
        for m in receipts:
            if m.group("project").strip() != project:
                continue
            valid_header = True
            accept(_utc_time(m.group("when")), m.group("epoch"))

        # Only the exact registry-linked coordinator status comment can
        # contribute its edit time. The comment still needs a scoped marker.
        if (is_status and pinned_comment_id is not None
                and str(comment.get("id")) == str(pinned_comment_id)
                and valid_header):
            accept(_utc_time(comment.get("updated_at")), None)

    for comment in (status_thread or {}).get("comments", []):
        if isinstance(comment, dict):
            examine(comment, is_status=True)
    for comment in inbox or []:
        if isinstance(comment, dict):
            examine(comment, is_status=False)
    return max(times).isoformat() if times else None

def derive_freshness(last_cycle, capture, hold, now):
    if hold:
        return 'HOLD'
    if not isinstance(capture, dict) or capture.get('status') != 'ok':
        return 'STALE' if last_cycle else 'UNKNOWN'
    cycle = _utc_time(last_cycle)
    if not cycle:
        return 'UNKNOWN'
    elapsed = (now - cycle).total_seconds()
    if elapsed < 0:
        return 'UNKNOWN'
    return 'STALE' if elapsed > 30 * 60 else 'RUNNING-observed'
