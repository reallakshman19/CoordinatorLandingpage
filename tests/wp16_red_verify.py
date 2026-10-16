#!/usr/bin/env python3
"""WP16 genuine base RED verifier: precise assertion failures, zero ERROR."""
import re
import sys
from pathlib import Path

if len(sys.argv)!=4 or sys.argv[1] not in ("source","browser"):
    raise SystemExit("usage: wp16_red_verify.py source|browser <log> <exit_code>")
mode,path,rc=sys.argv[1:]
log=Path(path).read_text()
expected={
    "source":{
        "test_wp16_pinned_registry_projection_absent",
        "test_wp16_pinned_project_row_lacks_shared_status",
    },
    "browser":{
        "WP16_UI_01_coverage_exact_complete",
        "WP16_UI_02_ot_exact_five_project_rows",
        "WP16_UI_03_project_hold_grey_not_green",
        "WP16_UI_04_grade9_dependency_prevents_any_child_green",
        "WP16_UI_05_tc_exact_21_instances_plus_workstream",
        "WP16_UI_06_duplicates_flagged_retired_preserved",
        "WP16_UI_07_links_id8_only_three_dimensions",
    },
}
if mode=="source":
    matches=re.findall(
        r"^(test_wp16_pinned_\w+)\s+\([^\n]+\)\s+\.\.\.\s+(FAIL|ERROR)$",
        log,re.M)
    failed={name for name,result in matches if result=="FAIL"}
    errors={name for name,result in matches if result=="ERROR"}
    valid_count=("Ran 2 tests in " in log and "FAILED (failures=2)" in log)
else:
    failed=set(re.findall(r"^FAIL (WP16_UI_0[1-7]_\w+)$",log,re.M))
    counts=re.search(r"^WP16_BROWSER_COUNTS pass=(\d+) fail=(\d+) error=(\d+)$",log,re.M)
    errors=set() if counts and counts.group(3)=="0" else {"browser_error"}
    valid_count=counts and counts.groups()==("0","7","0")
    if "Traceback (most recent call last)" in log:
        errors.add("unhandled_exception")
ok=rc!="0" and failed==expected[mode] and not errors and bool(valid_count)
print(f"WP16 {mode} pinned PR50 RED: {len(failed)} expected FAIL / {len(errors)} ERROR — "
      +("PASS" if ok else "INVALID"))
if not ok:
    print("actual FAIL:",sorted(failed),"expected:",sorted(expected[mode]))
    raise SystemExit(1)
