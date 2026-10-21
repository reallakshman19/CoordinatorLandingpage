# Progress page: data architecture and how agents use it

The landing page tab **Progress page** shows, for each project, what the Owner must do and how the work stands.
It is drawn entirely from JSON files in `site/progress-data/`. There is no database and no build step: change a file,
and the page shows it after the next Pages build (the page re-fetches every two minutes).

## 1. What the Owner sees

```
Progress page                              top-level tab
 └─ <project sub-tab>                      one per entry in projects.json, e.g. "G9v3.5 Pilot Progress"
     ├─ topic bar: Overview | <topic> | <topic> | ...     topics are the children of the project
     ├─ Overview: needs-you list across topics, joined reply, topic x milestone grid
     └─ a topic has three views:
          My actions            the Owner's open decisions, each with files, options and a copy-ready reply
          Progress              milestone strip, then lane cards with one row per stage
          Grounding fixtures    what a new agent or Oracle should read first (sources and starting context)
```

Routes: `#progress-page/<project>/overview` and `#progress-page/<project>/<topic>/<view>`
with view = `actions` | `progress` | `fixtures`.

## 2. Folder tree

```
site/progress-data/
  projects.json                      the sub-tabs: [{key, label, project?, order}]
  <project>/                         key from projects.json, e.g. g9v35
    index.json                       project title, last write, chat ids, topic list
    <topic>/                         key from index.json, e.g. nlm, shared, m1d
      meta.json                      title, subtitle, milestones, lanes
      stages.json                    one object per stage
      actions.json                   one object per decision card
      fixtures.json                  grounding fixtures: ten lists
scripts/check_progress_data.py       validator: run it before every commit
```

Keys are lower case letters, digits and `-`. A topic is a child of a project: for example project `g9v35`
(G9v3.5 Physics pilot) has topics `nlm` (Newton's Laws of Motion), `shared` (tooling every topic needs) and later `m1d`
(Motion in 1D). Stage ids (`S1`, `P4`, `G5`...) and card ids (`D1`...) are unique inside a topic, not across topics.

## 3. File formats

**projects.json**: `{"schema":2,"projects":[{"key":"g9v35","label":"G9v3.5 Pilot Progress","project":"g9v35","order":1}]}`.
`project` is the value the "Send to OTM" form carries (defaults to `key`).

**index.json**: `project` {key, title, subtitle, updatedAt (UTC ISO), updatedBy, staleAfterMin}, `chats`
{chatKey: {label, id8, url? (github.com only), note?}}, `topics` [{key, label, order, title, updatedAt, planned?}].
`planned: true` shows a greyed topic with no files yet.

**meta.json**: `title`, `subtitle`, `milestones` {M0: {order, name, full}}, `lanes` {S: {order, title, sub, parallel?}}.

**stages.json**: `{ "P4": {order, lane, milestone, name, sub, state, actor, cond?, chats[], refs[{l,u}], detail{}} }`
- `state` is one of `VERIFIED` `SUBMITTED` `IN_PROGRESS` `BLOCKED` `NOT_STARTED` `STALE` `UNKNOWN` `NOT_APPLICABLE`.
  A state means evidence exists and still applies, never a label someone typed. `SUBMITTED` is not `VERIFIED`.
- `actor` is who acts next: `YOU` (the Owner), `OTM`, `ORACLE`, `IR`, `CODER`, `PQRT`, `PCHK` or `-`.
- `chats` are keys into `index.json` `chats`. `detail` keys shown: who, do, why, files, status, still, waits, result, done, next.
- A milestone's state is computed from its stages: BLOCKED if any is, else VERIFIED if all are, else the weakest.

**actions.json**: `{ "D1": {order, status: "open"|"done", stages[], title, lead, tables[], ask?, options[], links[], answer?} }`
- Each option: `{key, label, suggested, body, steps?, reply, short}`. Exactly one option per open card is `suggested`.
  `reply` is the text the Owner pastes or sends; `short` is its form inside the joined "answer all" reply.
- When the Owner answers: `status: "done"` and `answer: {text, at, ref}`.

**fixtures.json**: ten lists of entries `{t: text, u?: link, s?: status, n?: note}`. Left column "Project sources":
`repository`, `issues`, `pullRequests`, `roadmap`, `highRoi` (status `proposed` or `implemented`), `future`. Right column
"Starting context": `intent`, `inputs`, `knownIssues`, `pending`. In text, `code` between backticks renders as code.

## Standalone Oracle mode (opt-in per project)

A project in `site/progress-data/projects.json` with
`"mode": "standalone-oracle"` is maintained by the **designated Oracle
directly with the Owner**, without OTM or Team Coordinator. Existing
projects without this flag retain their original Coordinator-mode
routing and protocol. On standalone projects, a topic without an
explicit view opens **Grounding fixtures first**; every new/resumed
agent MUST read the applicable fixtures and protocol and return an
actual onboarding receipt **before task execution**.

The project's fixture +/- and Owner decision replies now open the
existing prefilled GitHub **Send to Oracle** form. Only the Owner
submits; shared-account provenance requires reconciliation. The
Oracle proposes small reviewable Progress PRs and adds complete
source-backed events since an explicit audit baseline to
`audit.json`. The validator reconciles recorded stage transitions
with current `stages.json`. A status does not grant authorization.

See [Standalone Oracle Engineering Relay Protocol](STANDALONE_ORACLE_PROGRESS_PROTOCOL.md)
for grounding, benchmark custody, agent/Owner inlet, relay, improvement
proposals, auditable status updates and Owner-gated adoption. This
mode does not amend `protocol/TEAM_PROTOCOL.md`.

## 4. Rules (the repository is public)

1. Only public-safe facts: states, names, GitHub links, hashes and findings. Never private files or their text, Drive
   links, emails, passwords or tokens.
2. ChatGPT chats appear as `id8` (the first 8 characters) only. A `url` is allowed only when it is a `github.com` link.
3. States come from evidence, not wishes. If a result is unknown, say `UNKNOWN`. A stage the plan names but nothing has
   started is `NOT_STARTED`, never `SUBMITTED`.
4. The Owner alone accepts, merges and releases: never mark acceptance or release `VERIFIED` without the Owner's recorded words.
5. Do not edit another agent's topic without telling OTM; one writer per topic at a time.

## 5. How an agent uses it

**Read**: open the topic's `fixtures.json` first (intent, known issues, pending items), then `stages.json` for the state
and `actions.json` for what waits on the Owner. Link to the card or stage by id (`nlm/P4`).

**Update the data** (normally OTM does this at each event with its `prog.py` tool; if you are told to do it by hand):
1. Edit the JSON file(s) of one topic. Keep the file formats above. Set `index.json` `project.updatedAt`, `updatedBy`
   and the topic's `updatedAt` to the current UTC time.
2. Run `python scripts/check_progress_data.py`. Fix every ERROR.
3. Commit only files under `site/progress-data/` in a small pull request (message: `Progress data: <topic>`).

**Add a topic** (a new child, e.g. Motion in 1D): create `site/progress-data/<project>/<topic>/` with `meta.json`,
`stages.json`, `actions.json` (`{}`), `fixtures.json` (ten empty lists); copy the shape of an existing topic and start
every stage at `NOT_STARTED`; add `{key, label, order, title, updatedAt}` to `index.json` `topics`. No code change.

**Add a project** (a new sub-tab): create `site/progress-data/<project>/index.json` (same shape as `g9v35/index.json`, with
its topics) and add `{key, label, order}` to `projects.json`. No code change.

**Propose a change as the Owner**: the page's `+` / `−` on a fixture and **Send to OTM** on a reply open GitHub's
"Owner Reply" issue form (`.github/ISSUE_TEMPLATE/owner-reply.yml`) with the text filled in. The Owner ticks "I am the
Owner" and submits; the issue is labelled `owner-input`. The GitHub account is shared with agents, so an issue proves
nothing about who wrote it: OTM compares the text with the reply offered on an open card and confirms with the Owner in
chat unless the Owner has given a standing rule. Nothing on the page writes to GitHub.

## 6. How the page reads (for whoever changes the code)

`site/js/progress_page.js` fetches `progress-data/projects.json`, then for the chosen project `index.json`, then the four
files of every topic, with `cache: 'no-cache'` (conditional requests), every two minutes while the tab is visible. It
draws everything with `textContent`, so data can never inject markup; only `https://` links are rendered as links. If
`projects.json` cannot be read it falls back to the built-in `g9v35` entry. The badge turns amber when `updatedAt` is
older than `staleAfterMin`.
