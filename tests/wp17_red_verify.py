#!/usr/bin/env python3
"""Exact pinned WP16 UEM guard behavioral RED, no imports or runner errors."""
from pathlib import Path
import re
import sys
if len(sys.argv)!=3:raise SystemExit("usage: wp17_red_verify.py <log> <exitcode>")
log=Path(sys.argv[1]).read_text()
names={
"test_wp17_pinned_edited_start_cannot_work",
"test_wp17_pinned_expired_grant_cannot_work",
"test_wp17_pinned_duplicate_end_cannot_deliver",
"test_wp17_pinned_timer_claim_not_armed",
}
matches=re.findall(r"^(test_wp17_pinned_\w+)\s+\([^\n]+\)\s+\.\.\.\s+(FAIL|ERROR)$",log,re.M)
fails={n for n,tag in matches if tag=="FAIL"}
errors={n for n,tag in matches if tag=="ERROR"}
# Assertion failures legitimately contain tracebacks; prohibit unittest ERROR entries.
ok=(sys.argv[2]!="0" and fails==names and not errors
    and "Ran 4 tests in " in log and "FAILED (failures=4)" in log
    and "errors=" not in log)
print("WP17_PINNED_WP16_RED: "+("PASS" if ok else "INVALID")+
      f" expected_fail={len(fails)} error={len(errors)}")
if not ok:print("actual",sorted(fails),"expected",sorted(names));raise SystemExit(1)
