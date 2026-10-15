# Coordinator landing page

Your GitHub interface to the home coordinator across registered projects and agents.

## Start here

**[Send an instruction / read replies](https://github.com/reallakshman19/CoordinatorLandingpage/issues/1)**

### Native request forms

| Action | Open form |
|---|---|
| Ask for status/work or change an instruction | [Request or change](https://github.com/reallakshman19/CoordinatorLandingpage/issues/new?template=request.yml) |
| Register a successor, request an agent or retire an assignment | [Agent or successor change](https://github.com/reallakshman19/CoordinatorLandingpage/issues/new?template=agent-change.yml) |
| Respond to an existing approval card | [Decision response](https://github.com/reallakshman19/CoordinatorLandingpage/issues/new?template=decision.yml) |

**Availability:** GitHub serves these forms after their templates reach the default branch. A draft PR or branch preview does not make them live. Until release, use inbox #1 below.

**First-slice boundary:** forms capture requests and decision responses as issues. Automated form processing, protected approval authentication, status publication and agent dispatch are not installed by these templates. The existing coordinator must read and reconcile actual sources under the current protocol before action. A submitted form or checkbox is not execution or proof of human approval.

Comment in the inbox:

```text
FOR COORDINATOR:
Project: dash-v2
Request: Show current agent status and advance the next eligible task.
```

Use `Project: aa3` for AA3. AA3 currently remains HOLD / observation-only proposal; a message does not silently resume its engineering. For a successor, supply project, old agent, existing ChatGPT URL, handover, what you already typed/uploaded and requested action. An existing opened chat must not be duplicated.

## Projects and status

| Project | Status / registration | Product source |
|---|---|---|
| Dash V2 | [Status and page-information summaries](https://github.com/reallakshman19/CoordinatorLandingpage/issues/2) | [Common#360](https://github.com/reallakshman19/Common/issues/360) |
| AA3 | [HOLD / observation-only proposal](https://github.com/reallakshman19/CoordinatorLandingpage/issues/3) | [AA3 repository](https://github.com/reallakshman19/AA3) |

## Interaction

Owner request -> coordinator ACK -> eligible mapped-agent dispatch -> actual report and independent review -> coordinator RESULT. Publication, delivery, execution and acceptance are separate facts. Requests and status comments carry exact source/evidence links and capture times; no live status is inferred from GitHub silence.

The existing15minute generic reminder handles intake while the home computer/Codex session is available. No immediate GitHub-triggered wake, new timer or workflow is installed. Shared-account posts do not prove human approval for protected authority. The coordinator's role follows the latest Owner selection; a named Coder exception does not release unrelated work or waive independent review.

This repository is **public**. Only sanitized coordination summaries/public evidence are posted. Full private page information and approval identity segregation require the selected privacy/identity setup; no credentials, private drafts or transcripts here.

## Protocol and current readiness

[Implementation plan with ASCII UI](IMPLEMENTATION_PLAN.md) defines the bounded coding slices and their acceptance gates.

[Full protocol proposal](PROTOCOL_PROPOSAL.md), [Dash reuse plan](DASH_V2_REUSE_PLAN.md) and [approval design](APPROVAL_CARDS_AND_FORMS_DESIGN.md) cover two-project routing, successor/new-agent change control, traceable page snapshots and restart/uncertainty. The complete system remains proposed. Native forms are the request-capture slice; distinct bot identity, automated processing and snapshot tooling require their own implementation and qualification. Ordinary inbox comments remain the fallback interface.

[Previous Common#390 inbox and history](https://github.com/reallakshman19/Common/issues/390) is superseded for new instructions; old receipts/history remain there. Late comments there must be reconciled, not lost or replayed blindly.
