# ADR-0076: Companion History Hosted Click, Administrator Analyzed Inbox, and Ordinary Own-History

## Status

`Accepted`

## Decision Date

`2026-08-26`

## Context

ADR-0073 accepted a mixed administrator inbox of pending and analyzed rows, a
pending overlay click path, and ordinary-identity 403 as the way to hide
companion history. ADR-0067 accepted mark-opened as administrator-only together
with administrator-only inbox list, detail, and apply.

Rendered companion use showed three defects in that contract:

1. History clicks for pending rows opened the unused review overlay instead of
   hosted FrameNest Details.
2. Administrator history mixed pending Saves into the global analyzed review
   pool.
3. Ordinary requesters had no private view of their own cataloged X Saves, and
   the 403 hide path cleared the toolbar badge.

Per-actor open-state already exists in migration `0031` as table
`companion_review_open_states` with primary key `(actor_login_key, media_id)`.
Schema head remains `0033`. A new `0034` table would duplicate that isolation
mechanism.

## Decision

1. **R1 hosted click.** Every companion history row posts hosted `open_details`
   into the surviving iframe (`v: "framenest.companion.web.v1"`, target origin
   `storedOrigin`, never `*`). Clicking never removes the row and never gates
   the iframe on the opened HTTP result. Analyzed rows also POST the existing
   opened mutation with that row’s `analysis_run_id`, then refresh list and
   badge. Pending rows never POST opened. `ui/review.html` remains in tree and
   is unused for this click path. Hosted Details hide **Analyze by AI** and
   **Load AI suggestion** when `companionWebHosted()` is true. Standalone
   Details/Edit and the Gallery card brain action stay unchanged. Edit remains
   capability-gated (`metadata.canonical.write`).

2. **R2 administrator analyzed-only inbox.** `GET /api/companion/review-inbox`
   remains administrator-only (`media.workflow.read`). Rows are the global
   analyzed pool (website Analyze-by-AI successes still join). Pending X Saves
   are absent. Item `unopened` and page `unopened_count` remain joins on
   `companion_review_open_states` for this actor. Compact chrome is the newest
   five analyzed rows; **All** is the remainder analyzed. Class `--unopened`
   applies when `analyzed && unopened`.

3. **R3′ ordinary own-history.** Ordinary identities receive
   `GET /api/companion/own-history` (`x.request`, not `companion_mutation`).
   Rows are actor-owned cataloged X Saves in every analysis state, movies
   excluded. Item JSON matches inbox. Pending `unopened` is always false and
   never increments the badge. Analyzed own rows carry per-actor unopened
   accent and badge. `unopened_count` is own-analyzed only. Compact chrome is
   the newest five own Saves of any state (analyzed `completed_at_ms`, pending
   `created_at_ms`). Alice’s list is never Bob’s. Ordinary remains HTTP 403
   `CAPABILITY_DENIED` on inbox list, detail, and apply.

4. **Same opened route, ownership gate.** `POST /api/companion/review-inbox/{media_id}/opened`
   remains one of the four `companion_mutation` routes. Allowlist, Origin, and
   `X-FrameNest-Request: 1` are unchanged. Ingress capability is `x.request`
   (both roles already have it). Administrators (`media.workflow.read`) still
   mark any eligible non-movie run. Ordinary callers may mark opened only for
   cataloged X media they own; otherwise the API returns uniform 404
   `MEDIA_NOT_FOUND`. Movie remains 409. Apply never publishes. Administrator
   PUT remains the sole publication writer, including unpublish.

5. **No 0034.** Opened state remains `companion_review_open_states`. Missing
   ordinary rows mean unopened. Existing administrator rows stay. There is no
   ordinary backfill. Schema head remains `0033`.

6. **Extension routing.** After `GET /api/identity/me`, `media.workflow.read`
   uses inbox; else `x.request` uses own-history; else chrome hides. Badge
   refresh uses inbox `limit=1` for administrators and own-history `limit=1`
   for ordinary callers. Both expose `unopened_count`.

## Superseded statements

ADR-0073 remains accepted. Only its mixed-inbox listing, pending-overlay click
path, and ordinary-403-hides-history statements are succeeded by this hosted
click, analyzed-only administrator inbox, and requester-private own-history
contract.

ADR-0067 remains accepted. Only the statement that mark-opened is
administrator-only is succeeded for own-item opened. Inbox list, detail, and
apply stay administrator-only. Ordinary identities still must not gain
`analysis.run`, `metadata.canonical.write`, or `media.content.publish`.

Matching present-tense mixed-inbox, pending-overlay, and ordinary-403-hides
wording in [docs/X_COMPANION.md](../X_COMPANION.md), [SPEC.md](../../SPEC.md),
[PRODUCT.md](../../PRODUCT.md), and [README.md](../../README.md) is likewise
succeeded.

Do not edit the bodies of accepted ADR-0073 or ADR-0067.

## Consequences

Administrators review a global analyzed pool with per-actor unopened accent and
badge. Ordinary requesters see only their cataloged X Saves, with unopened
accent and badge after analysis. Every history click opens hosted Details.
Widening opened callers is a trust-boundary edit: tests must keep Apply,
inbox list/detail, and other-actor opened fail-closed, and must keep own-history
`unopened_count` from reusing the global analyzed subquery.

Exactly four `companion_mutation` routes remain. GET own-history is not a
mutation. Empty allowlist still fails closed for mutations and remains readable
for GET inbox and GET own-history.

## References

- [ADR-0063](0063-companion-side-panel-web-host.md)
- [ADR-0067](0067-administrator-companion-review-inbox-and-mutation-trust.md)
- [ADR-0070](0070-companion-exclusion-of-movie-workflows.md)
- [ADR-0073](0073-companion-merged-history-chrome-pending-visibility-x-seed-tag-and-preserving-apply.md)
- [docs/X_COMPANION.md](../X_COMPANION.md)
