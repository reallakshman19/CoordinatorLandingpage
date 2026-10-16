# Landing app registry evidence fields (WP12b)

This document describes the **read-only projection contract** for an evidence PR. It does **not** amend `TEAM_PROTOCOL.md`, grant merge authority, or permit actions in external repositories.

## One declaration key

Use **`evidence`**, an object with exactly `pr_url` and `head`, at either or both scopes:

```json
{
  "project": "cii-method-c",
  "repository": "reallakshman19/XML_Compare_Utilities",
  "evidence": {
    "pr_url": "https://github.com/reallakshman19/XML_Compare_Utilities/pull/106",
    "head": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
  },
  "agents": [
    {
      "chat_id8": "6ad1ce42",
      "evidence": {
        "pr_url": "https://github.com/reallakshman19/XML_Compare_Utilities/pull/107",
        "head": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
      }
    }
  ]
}
```

Values above are **illustrative, not declarations in a live registry**. The owning repository comes from `repository`. `pr_url` must point to a PR in that **same repository**, and `head` must be a 40-character hexadecimal commit SHA. At build time, the read-only fetcher requests the current head of each distinct declared PR (at most **12 unique PRs per project**), then compares it to the recorded `head`. A mismatch is **evidence superseded (head moved)**; an equal head is **current**; a malformed, inaccessible, missing, or foreign PR remains **UNKNOWN**, never presumed current. One project's project-level comparison never substitutes for an individual agent's comparison. Both use the same `evidence` shape.

The previous guessed root-level aliases `evidence_head`, `evidence_pr`, `evidence_pr_url`, `pr_url`, and `pr` are **not read as declarations**. Existing parsed TASK EVIDENCE v2 blocks in the published agent-detail JSON still use an unrelated array named `evidence`; the declared PR is projected separately as `evidence_head_status` and does not replace the evidence timeline.

## Other read-only boundaries

`children` is a list of exact owning-repository GitHub issue URLs or `{"url":"..."}` entries. Duplicate URLs count only once; the fetch limit is **12 unique children per project**. Only exact upper-case `[V3.6]` prefixes followed by `[O#][PLANNED|IN_PROGRESS|DONE]` in fetched child titles qualify for progress. Missing or wrong-repository observations yield UNKNOWN.

`agents[].reports_to` points to a same-project `chat_id8`. Circular chains appear with a **reporting cycle** warning, and every recorded agent remains visible. A proof label is **hosted CI link claimed** only if its recorded URL points to `/actions/runs/<number>` in that project's registered repository. All other proof blocks are **local only**; neither label independently verifies CI or confers acceptance.
