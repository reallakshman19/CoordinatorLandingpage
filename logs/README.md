# Coordination logs

Raw record of every coordination action and every agent reply, for the Owner's dashboard (to be programmed later). Written by OwnerTeammember (and TeamCoordinator) under [Team protocol v1](https://github.com/reallakshman19/CoordinatorLandingpage/issues/7). **This repository is public:** no credentials, tokens, private drafts or personal data are written here.

## Layout: project → session

```
logs/
  <project>/                      e.g. grade9-pilot
    <YYYY-MM-DD>_epoch<N>/        one session = one day under one coordinator control epoch
      events.jsonl                one JSON object per line, append only, in time order
      raw/<chat id8>/turn-<n>.md  full text of one agent reply (and the message it answered), saved once
```

A new session folder starts on a new day or when the control epoch changes (see `CONTROL epoch N` notices in inbox #1).

## events.jsonl fields

| field | meaning |
|---|---|
| `t` | time, ISO 8601, Dubai (+04:00) |
| `project`, `epoch` | project id and control epoch |
| `actor` | who acted: `OwnerTeammember`, `TeamCoordinator`, `coder 6ad02128`, `validator 6ad02130`, `Owner` |
| `action` | `CONTROL` · `SEND` · `CLEAR_DRAFT` · `OBSERVE` · `REPLY` · `EVIDENCE` · `VERDICT` · `STATUS_POST` / `STATUS_EDIT` · `ISSUE_CREATE` · `RELAY` · `ALERT` |
| `target` | the chat, thread or comment acted on |
| `text` | exact text sent (SEND) |
| `result` | outcome: `DELIVERED`, `TYPED_NOT_SENT`, `UNCERTAIN`, verdict (`ALIGNED` / `CORRECTED` / `ESCALATE`), … |
| `links` | GitHub links (evidence block, verdict, status, CI run) |
| `raw` | path of the raw reply file, relative to the session folder |
| `time_estimated` | `true` when the time was reconstructed afterwards (only the first hour of 15 Oct) |

## WP-L3 optional registry additions (backward-readable)

These three keys are optional at the top level of each `logs/<project>/registry.json`.
Absent keys mean **not recorded**, not a recorded empty list or an assertion
that nothing happened. The build projects only present keys into both
`project-<name>.json` and the `projects.json` project summary. No existing
registry has to be changed and unknown future keys are accepted.

### `originals[]` — source/original custody

Each array entry is an object with `name` and `path` (nonblank strings),
`class` (`ORIGINAL`, `SYNTHETIC`, `PARTIAL`, `MISSING`), optional `sha`
(7–64 hex digits or null), `sha256` (exactly 64 hex digits or null), and
`custody` (nonblank text or an object). A missing source does not need
an invented hash. Extra record keys are preserved verbatim.

### `improvements[]` — proposals and disposition

Each array entry has `id`, `title`, `author` (nonblank strings),
`disposition` (`KEEP`, `PROPOSED`, `ADOPTED`, `REJECTED`, `PARKED`),
and optional `reason`, `revisit_if`, `implemented_in`, `observed_result`
(nonblank strings or null) and `retain` (boolean). Unknown keys pass
through unchanged. Reported disposition **is not Owner approval**.

### `succession` — handover and custody state

A single object with optional `outgoing`, `incoming`, `method`, `phase`
(nonblank strings); `links` (object with optional `1a`, `1b`, `2` text/null
values); `pending_sends` (array); `custody` (nonblank text or object);
and `unrecorded_interval` (object with optional `from_checkpoint` and
`to_departure` text/null values). Unknown nested keys are preserved.
A null link does not assert a completed or verified handover stage.

### `history_refs[]` — existing WP-L2(c) fetch path

History references remain handled by the existing allow-listed G3 lineage
fetch, with its existing rejected, inaccessible and malformed states.
WP-L3 does not add fetching, revalidate these URLs or change the allow-list.

### Malformed values, schema visibility and forward compatibility

Wrongly typed top-level optional keys become visible `ERROR` objects.
Malformed array entries become `ERROR` objects **in their original position**;
valid siblings remain unchanged. Errors include `status: ERROR`,
`reason: INVALID_REGISTRY_VALUE`, `path`, `errors[]` listing offending
JSON field paths, and `raw` containing the unmodified source JSON value.
Malformed succession objects retain the original object in `raw`.
Optional fields that are absent produce no output keys, retaining legacy
frozen-fixture bytes. Projection is reporting, not source verification,
custody authentication, approval, or authorization.
