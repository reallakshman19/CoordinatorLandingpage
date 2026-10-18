# v3.6 scoreboard artifact: SYNTHETIC

- **Class: SYNTHETIC.** It was built from Common's own test fixtures, not from a live governed v3.6 project. No live v3.6 project exists yet, because the ECO-08 pilot is NOT_RUN. Never present this file as live project status.
- **Generator:** `reallakshman19/Common` at `d3584066e` (the ECO-07 merge), using `skills/engineering-pr-delivery-v3.6/scripts/scoreboard_v36.py` (`sb.board`).
- **Input:** `tests/test_readmodel_v36.py` helpers. The read model is
  `run([comment(SC_ID, self_check()), comment(9002, evidence())])[0]`.
- **Command:** run from `skills/engineering-pr-delivery-v3.6/tests` with
  `py -c "import sys,json;sys.path[:0]=['.','../scripts'];from test_readmodel_v36 import SC_ID,comment,evidence,run,self_check;import scoreboard_v36 as sb;print(json.dumps(sb.board(run([comment(SC_ID,self_check()),comment(9002,evidence())])[0]),indent=2,ensure_ascii=False,sort_keys=True))"`.
  The output was written with LF line endings and a trailing newline.
- **sha256:** `a3d3a50ab830ebf261004936cc916f9ca9659d93be23e9fc41edf6bc2e1d34d3`
- **Schema:** `v36.scoreboard/v1`
- **Added by:** OwnerTeammember (acting TeamCoordinator) for WP-L5, per decision #1 6243304714.
