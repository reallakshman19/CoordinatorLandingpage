# WP-V2 / D3: post-checkpoint Owner amendment (synthetic, tests only)

This frozen isolated fixture copies the exact `logs/landing-live/registry.json`
bytes from `main@a8cccc62a4eb10631a4d87ac664f37eaa0e7f137` into
`logs/landing-live/registry.json`. No real registry fields or leases were edited.

`cache/` is a **synthetic snapshot of the WP-L2(c) cache *shape***, not
an assertion that the associated GitHub comments exist:

- `project-threads/landing-live/issue-30.json`: synthetic verified epoch-2
  coordinator checkpoint at **2026-10-17T21:00:00Z**.
- `project-extras/landing-live/lineage.json`: source-scoped synthetic
  copy of the root issue #21 body excerpt, retaining intent at checkpoint.
- `inbox-1.json`: **one** synthetic Owner amendment, comment
  **#990000001**, at **2026-10-17T21:15:00Z**. It explicitly changes
  the project scope, requires pausing the planned release, and references
  `landing-live`.
- `capture-info.json`: source capture reports `ok` with no errors at
  21:20Z; deliberately tests that “capture succeeded” does **not** mean
  the 21:00Z checkpoint incorporated the 21:15Z change.

The test builds from this isolated registry/cache with a mocked GitHub
provenance resolver. It expects the amendment text/source to be rendered
by WP-V1 and **a D3-specific reconciliation barrier**: either
`owner_input_captured=PROBLEM` or an explicit source-linked stale task.
An unrelated 30-minute freshness timeout cannot satisfy D3.

No fixture under `benchmarks/` is written. No real Owner decision or
acceptance is claimed by these synthetic identifiers.
