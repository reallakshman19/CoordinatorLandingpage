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
