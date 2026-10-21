# Progress data

Full guide for agents (formats, rules, how to add a topic or a project): [docs/PROGRESS_PAGE.md](../../docs/PROGRESS_PAGE.md).
Validate before every commit: `python scripts/check_progress_data.py`.

JSON files behind the landing page tab **Progress page**. One folder per project, one sub-folder per topic
(a child of the project, for example `nlm` = "G9v3.5 Physics pilot-NLM", `m1d` = Motion in 1D).

```
site/progress-data/
  README.md
  projects.json              the sub-tabs of the Progress page (add a project here)
  <project>/                 e.g. g9v35
    index.json               project title, last write time, chat ids (id8 only), list of topics
    <topic>/                 e.g. nlm, shared, m1d
      meta.json              topic title, subtitle, milestones, lanes
      stages.json            stage id -> state, next actor, chats, evidence links, details
      actions.json           the Owner's decision cards (open or answered) with replies
      fixtures.json          grounding fixtures: sources and starting context, as entry lists
```

`fixtures.json` sections (each a list of entries `{t: text, u?: link, s?: status, n?: note}`):
`repository`, `issues`, `pullRequests`, `roadmap`, `highRoi`, `future` (Project sources) and
`intent`, `inputs`, `knownIssues`, `pending` (Starting context).

**Written by OTM** (the Owner's teammate session) at each event; do not edit by hand. The page fetches the files again
every two minutes. The repository is public: chat ids are id8 only, and no ChatGPT chat link, Drive link or private
file text belongs here. A new topic is a new folder with the four files plus an entry in `index.json`.
