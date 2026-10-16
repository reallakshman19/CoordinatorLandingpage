#!/usr/bin/env python3
"""WP18 pinned WP17 two behavioral RED assertions, not runner/import failures."""
from pathlib import Path
import re
import sys
if len(sys.argv)!=3:raise SystemExit("usage: wp18_red_verify.py <log> <exit_code>")
content=Path(sys.argv[1]).read_text(encoding="utf-8")
expected={"test_wp18_pinned_missing_roster_must_block",
          "test_wp18_pinned_uncertain_send_not_hidden_by_cycle_limit"}
results=re.findall(r"^(test_wp18_pinned_\w+)\s+\([^\n]+\)\s+\.\.\.\s+(FAIL|ERROR)$",
                   content,re.M)
fails={name for name,status in results if status=="FAIL"}
errors={name for name,status in results if status=="ERROR"}
ok=(sys.argv[2]!="0" and fails==expected and not errors and
    "Ran 2 tests in " in content and "FAILED (failures=2)" in content and
    "errors=" not in content)
print(f"WP18 PINNED WP17 RED: {'PASS' if ok else 'INVALID'} "
      f"expected={len(fails)} failures errors={len(errors)}")
if not ok:
    print("actual",sorted(fails),"expected",sorted(expected))
    raise SystemExit(1)
