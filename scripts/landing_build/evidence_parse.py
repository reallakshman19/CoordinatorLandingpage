"""Evidence parsing helpers moved verbatim from the landing data builder."""

import re


def id8(raw: str) -> str:
    """Return at most 8 chars — already the convention in the data."""
    if not raw:
        return raw
    return str(raw)[:8]


def scrub_chat_url(text: str) -> str:
    """Replace any full chat URL with an 8-char id placeholder."""
    # Pattern: long hex runs (>8 chars) that look like UUIDs or chat IDs
    # We do NOT scrub GitHub URLs — those are public.
    text = re.sub(
        r'https?://(?:chat\.openai\.com|chatgpt\.com)/c/([0-9a-f-]{9,})',
        lambda m: f'chat:{id8(m.group(1).replace("-",""))}',
        text
    )
    return text


EVIDENCE_RE = re.compile(
    r'TASK EVIDENCE v2\s*·\s*(?P<project>[^·]+?)\s*·\s*(?P<role>[^·]+?)\s*·\s*chat\s+(?:(?P<chat>[0-9a-f]{8})|n/a(?:\s+\([^)\n]*\))?)\s*·\s*#(?P<seq>\d+)\s*·\s*(?P<ts>[^\n]+)',
    re.MULTILINE
)


VERDICT_RE = re.compile(
    r'OwnerTeammember.*?(?:grounding verdict|RETIRED)[^\n]*(✅ ALIGNED|✏ CORRECTED|⚑ ESCALATE|RETIRED)',
    re.MULTILINE | re.DOTALL
)

OUTSIDE_WRITE_RE = re.compile(
    r'(?:outside write|second writer outside|pushed outside)',
    re.IGNORECASE
)


def parse_task_evidence(comment_body: str, comment_id: int, comment_ts: str) -> dict | None:
    """Parse a TASK EVIDENCE v2 block from a comment body."""
    m = EVIDENCE_RE.search(comment_body)
    if not m:
        return None

    body = comment_body[m.start():]

    def field(name: str) -> str:
        pattern = re.compile(rf'^{name}:\s*(.+)', re.MULTILINE | re.IGNORECASE)
        fm = pattern.search(body)
        return fm.group(1).strip() if fm else ""

    status_m = re.search(r'Status:\s*(\w+)', body, re.IGNORECASE)

    proof_lines = []
    in_proof = False
    for line in body.splitlines():
        if line.startswith('Proof:'):
            in_proof = True
            continue
        if in_proof:
            if line.startswith('  -') or line.startswith('- '):
                proof_lines.append(line.strip())
            elif line.strip() and not line.startswith(' '):
                in_proof = False

    grade_map = {'CI': 'CI', 'READBACK': 'READBACK', 'LOCAL': 'LOCAL', 'CLAIM-ONLY': 'CLAIM-ONLY', 'OWNER': 'OWNER'}
    proofs = []
    for pl in proof_lines:
        grade = 'CLAIM-ONLY'
        for g in grade_map:
            if f'[{g}]' in pl:
                grade = g
                break
        proofs.append({'line': pl, 'grade': grade})

    return {
        'comment_id': comment_id,
        'ts': comment_ts,
        'project': m.group('project').strip(),
        'role': m.group('role').strip(),
        'chat_id8': m.group('chat'),
        'seq': int(m.group('seq')),
        'header_ts': m.group('ts').strip(),
        'task': field('Task'),
        'status': status_m.group(1) if status_m else '',
        'aim': field('Aim'),
        'did': field('Did'),
        'where': field('Where'),
        'proofs': proofs,
        'tests': field('Tests'),
        'would_be_wrong': field('Would be wrong if'),
        'not_done': field('Not done / HOLD'),
        'needs_owner': field('Needs Owner'),
        'next': field('Next'),
        'meter': field('Meter'),
        'raw': scrub_chat_url(comment_body),
        'replaces': None,
    }


def parse_verdict(comment_body: str, comment_id: int, comment_ts: str) -> dict | None:
    """Parse an OwnerTeammember grounding verdict from a comment."""
    m = VERDICT_RE.search(comment_body)
    if not m:
        return None
    return {
        'comment_id': comment_id,
        'ts': comment_ts,
        'verdict': m.group(1),
        'raw': scrub_chat_url(comment_body),
    }
