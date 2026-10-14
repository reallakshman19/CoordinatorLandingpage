# GitHub approvals — decision cards and prefilled forms

Status: **DESIGN PROPOSAL / NOT INSTALLED**. Prepared15October2026, Dubai. This document adds approval UX to the existing control protocol and reuse plan. It creates no active decision card, approval, form, workflow, agent, credential or authority grant.

## 1. Office interaction

The coordinator posts a **Decision required** card in the relevant request thread and links it from a proposed Approvals index. The Owner opens GitHub, reviews the exact action, clicks Approve/Reject/Modify/Defer, completes the prefilled Issue Form and submits. Coordinator acknowledges the actual response, validates it, performs the eligible approved action through existing guards, and posts its result/receipt linked to the card.

Native GitHub Issue Forms open a page; they are not a custom popup over arbitrary GitHub pages. The intended experience is a concise card with prominent links and one confirmation form. A custom modal would require a separate authenticated web UI/backend; defer it. GitHub notifications may surface the decision according to the Owner's subscriptions/settings; no guaranteed desktop popup or immediate local Codex wake is claimed.

## 2. Decision card contents

Every card shows:

- Project, affected agent/task, card ID and exact revision, request permalink and current state.
- Plain-language action and reason approval is required; direct approval-rule/authority reference.
- Exact allowed effects, write paths or recipient binding/generation, candidate and artifact identities where applicable.
- Excluded effects, only when needed to define the approval boundary: for example no product-write/merge authority in a reviewer handover.
- Evidence/handovers and precise dependency prerequisites; approvals do not manufacture missing readiness.
- Proposed batch/attempt count, time/resource scope, expiry policy and the next observable receipt.
- Approve, Reject, Modify and Defer links. No preselected response is itself consent.

Example layout, **illustrative only — not an active card**:

```text
DECISION REQUIRED — EXAMPLE
Project: Dash V2 | Agent: M3 G3
Card: <card-id> / revision 1
Action: Ground the Owner-opened independent reviewer using the specified handover.
Optional attachment sub-action: exact prepared public ZIP + unchanged test.
Why: the attachment needs specific file/destination approval.
Target: registered M3 generation3; live mode/adoption checks still apply.
Scope: one grounding instruction; only the explicitly selected attachments.
Evidence: handover + exact file sizes/hashes + current mapping record.
Boundary: independent review only; no product-write, merge or deployment grant.
After approval: verify route/readiness, execute permitted action once, publish receipt.

[Approve]  [Reject]  [Modify]  [Defer]
```

The real M3G3 was opened by the Owner already. A future card must not ask to create another G3. Grounding, uploading, mode verification, adoption and writer release remain distinct facts. If the Owner already supplied the files/instructions, reconcile them first rather than sending again.

## 3. Prefilled response form

Proposed form fields (not installed YAML):

| Field | Source / validation |
|---|---|
| Project | Prefilled registered ID; exact match to card |
| Card ID, revision, digest | Prefilled from coordinator card; validate against durable exact version |
| Original request / card link | Prefilled permalink; exact observed body version retained |
| Decision | Approve / Reject / Modify / Defer; explicit submitted choice |
| Limits / requested changes | Required for Modify; otherwise cannot silently expand approved action |
| Confirmation | Required acknowledgement of exact card action/version and listed effects |

Prefill fields through supported GitHub new-issue form query parameters after templates are installed on the default branch. URL fields and form text can be edited: they are **not signed, hidden, immutable or trusted**. The processor reloads the canonical saved card and rejects mismatched project, ID, revision, digest or target. Do not reconstruct authority from an edited link or arbitrary form text.

Do not put tokens/private payloads in URLs. Public cards include only sanitized action metadata and public evidence; sensitive exact details require an appropriately selected restricted channel. The current repo is public, and no private channel or bot separation is installed by this design.

## 4. Responses and change management

Approval flow: `OPEN -> RESPONSE_OBSERVED -> VALIDATED -> APPROVED_PENDING_PREREQUISITES -> EXECUTION_STARTED -> CONSUMED_WITH_RESULT`.

Alternatives: `REJECTED`, `DEFERRED`, `NEEDS_CLARIFICATION`, `EXPIRED`, `SUPERSEDED`, `EXECUTION_UNCERTAIN`. Approval validates authorization, not completion or readiness. A consumed card is not reusable authorization for an additional launch/send/upload.

Approve means only the canonical listed action/limits. Reject holds that action and records the reason. Defer leaves it parked. Modify requests a new card revision with an explicit change summary; it does not approve the old card or permit unreviewed changed effects.

Target generation, files, recipient, candidate, scope or authority changes supersede the affected card before execution. Minor display changes cannot change the underlying action. A new approval is unnecessary when the existing exact scoped grant still applies; approval validity is checked rather than asking again mechanically.

Expiry must be explicit and action-specific. A queued planning request need not expire like an execution permit. Capture freshness is separate: even a valid approval requires a fresh route/draft/generation/scope check before actual Send. Do not demand a new Owner approval merely because a new live observation was required.

Duplicate responses are idempotently recorded by exact response source/version and card identity. Conflicting responses, edits and revocations are reconciled before affected side effects. Preserve old decisions and effects; no promise to undo an already executed action. If a response arrives during execution, inspect the actual attempt before further effects.

## 5. How different approval types look

| Type | Required review details | Example scope |
|---|---|---|
| Resource approval | Previous rolling-five-minute B, next-five-minute P, same declared metric/window, forecast basis/uncertainty and planned work | One bounded planning/coordination batch, or an explicitly named recurring routine |
| New agent | Project, role, scope, independent reviewer/writer ownership, creation count, handover and mode | Create one regular ChatGPT High conversation; never Work |
| Existing successor | Actual supplied route, predecessor stop/handover, generation and retained scope | Register/ground existing G3; do not create another |
| File upload | Exact file names/sizes/hashes, specific destination and purpose | Attach only the approved public ZIP/test to that exact bound chat |
| Material writer release | Source/interface qualification, approved plan/paths, current writer stop and independent verifier | One named engineering slice; no blanket release |
| Merge/deployment | Exact PR/head/environment, original criteria/review/CI and concrete authority | Separate protected release, not implied by a green report |

For resource cards, reported input including cache + output is not billing. Estimates are not a guaranteed model-spend cap. B=0/P>0 still triggers the saved rule; offer a clearly bounded recurring routine when appropriate, not a hidden baseline floor. The already approved recurring checks remain available without new identical cards.

Group genuinely related effects into one reviewable card with explicit sub-actions when authority permits. Do not bundle unrelated projects or use a generic “approve everything.” Confirmation requirements at the actual browser action still apply where the tool policy requires them; a GitHub form cannot waive those rules.

## 6. Owner identity and evidence

A valid form response must be read through authenticated GitHub metadata and satisfy the enrolled Owner identity policy. Use stable account IDs and a distinct coordinator App-installation/bot identity. Neither a checkbox, prefix, reaction, edited comment nor a shared-account name establishes human approval by itself. Known coordinator/agent publications are never approval inputs.

Current shared-account operation can collect requests and make proposals within existing authority. Until identity separation/independent Owner confirmation is established, it cannot silently promote unrecognized approval comments into protected grants. This is the specific migration task needed for office-only protected approvals; it does not reintroduce a blanket private-destination blocker for ordinary panel/coordinator work.

Response author/source ID/body hash, card version/action digest, original request and actual execution receipt are linked. New/edited/deleted source versions remain in event history. The card's action and human response are separate records.

## 7. Reuse Dash V2, avoid another approval engine

Use existing command action `DECISION_RESOLVE`, decision payload `card_id/outcome`, TargetIdentity, payload digest/idempotency/journal and registration generation. Add a narrow form-to-decision adapter with explicit version/digest validation; do not weaken the pinned CASP schema to accommodate browser fields. Preserve the distinction between command admission ACCEPTED and product acceptance.

Coordinator's actual native delivery guard remains the side-effect owner until a separately qualified mapping changes it. ACK/publication/approval/Send/adoption/result are separate facts. Unsupported LA/native adapters cannot claim actual execution because a form was submitted. Keep uncertain delivery/publication reconciliation and single-flight controls.

## 8. Qualification tests and rollout

Required negative tests: edited prefills; wrong project/card revision/digest; retired generation; shared-account agent “approval”; stale/revoked/superseded card; duplicate/conflicting responses; change after approval/before dispatch; crash after effect/before receipt; response with broader scope; private-field leakage; no reply/reaction is not approval; unchanged valid approval survives ordinary reobservation; resource recurring scope does not authorize larger batches.

Rollout: (1) keep current plain-comment bridge, displaying exact cards and required reply wording, without pretending forms are installed; (2) qualify identity and canonical decision lookup; (3) separately authorize engineering to add native forms + admission adapter and publication links; (4) independently verify an office-submitted harmless decision and protected negative cases; (5) then use forms for eligible real approvals. No new worker, website, timer or GitHub Actions workflow is needed merely to display these cards.

First future implementation handover must include this design, the reuse plan, exact pinned source, original role/privacy/authority boundaries and discriminating tests. No actual approval request or engineering release has been generated by writing this document.

## Primary references

- [GitHub creating an issue and URL query parameters](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/creating-an-issue).
- [GitHub Issue Forms syntax](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/syntax-for-issue-forms).
