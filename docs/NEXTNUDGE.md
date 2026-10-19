# NextNudge — current thread workbench

Owner-operated steering: **Thread → Grounding Fixtures → bounded nudge → actual return → Reconcile**.
The Owner accepts and controls merge. The app does not infer approval from an ACK.

## Ground once, update when meaning changes
The current v3 thread has a Grounding Fixtures tab. It reuses the original headings:
inputs and issues/PRs, roadmap and Owner intent, task understanding, specification,
goldens, benchmarks, test criteria, midcycle/exit reconciliation and successor lessons.
All fields are optional; blank means UNKNOWN.

Type notes and source links, then **Save grounding** once. One meaningful save adds
one snapshot; typing and unchanged saves add no history entries. Earlier snapshots
and exact sent packets remain in append-only history. Copy grounding includes the
visible draft. Browser drafts survive navigation; Save to GitHub makes the thread
durable. Private chat links stay device-only; shared thread text is public.

The older v2 ladder remains available as an archive. Its log engine, timers and
per-field records are not reintroduced.

## Send and fetch through GitHub
A composer offers a named agent and target issue number. **Send via GitHub…**
prepares an Owner request using the existing `nextnudge-save` issue workflow.
The Owner reviews/submits that issue. The action posts the exact packet with
`TO: agent`, records its comment URL, and appends the sent move. Preparing the
request is not proof that delivery occurred. Compare with GitHub after the receipt.

**Fetch GitHub return…** finds an actual comment whose first nonempty line has
the expected primary `ACK move-id` and whose `FROM: agent` matches the target.
It retains the full reply and comment URL. That identity line is a recorded agent
claim, not independent authentication or engineering acceptance.

The existing workflow token supports this repository's issues only. Unsupported
repositories are refused; no broad cross-repository token is added. No new
workflow, polling service, automatic acceptance or coordinator registry is installed.

Saves use the expected blob SHA. If posting succeeds but recording fails, the
receipt says DELIVERED_NOT_RECORDED. Retry the same packet ID; an exact delivery
marker recovers the posted comment without sending twice. Changed retry content
is refused. Queued thread actions are excluded from legacy snapshot sweeps.

## Authenticated-host CLI
`node scripts/nextnudge_agent_bridge.mjs CONFIG.json` uses the same transport
functions. It emits NEXTNUDGE_RPC JSON for listComments/postComment. An authorized
host executes those operations with its GitHub connector, then supplies one JSON
response with the matching id, ok and value. No token enters the CLI.

CONFIG names the operation, source threadFile, observed Git blob baseSha, output,
and either move + target or moveId. A successful result writes the updated thread
and an existing-format Owner save request. Publish and read back that save before
claiming durable recording. The CLI can pilot a candidate without browser control;
this does not verify a deployed browser journey.

## Status and drafts
Waiting is derived from sent moves without a subsequent matching reply.
Late/unmatched replies do not answer a newer task. Done requires supported Owner
close checks and a return linked to that exact close move; older outstanding tasks
remain visible. Composer and grounding drafts are stored separately per thread.

A direct thread link uses `nextnudge/index.html?thread=NN-...`.
The current guidance link points to Common/skills/agent-work on main. The executing
agent records the actual revision read and follows the project's selected mode.

## Verification and continuation
Run `node --test tests/nextnudge-*.mjs`. Tests include the UI form handlers,
history/privacy checks, wrong/late ACKs, stale bases, unauthorized requests, failed
record/retry recovery and exact named-agent returns. Model/DOM-harness tests do
not establish real-browser or live-provider execution.

Current repair and source-bound setup: [#110](https://github.com/reallakshman19/CoordinatorLandingpage/issues/110).
The original prototype remains unchanged. Work report: [NEXTNUDGE_110_WORKREPORT.md](NEXTNUDGE_110_WORKREPORT.md).
