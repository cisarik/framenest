# ADR-0072: Native Side-Panel Unread Inbox and Title-Bar History Chrome

## Status

`Accepted`

## Decision Date

`2026-08-23`

## Context

ADR-0071 accepted native review chrome above the surviving hosted FrameNest
iframe. Live Cooperator review rejected the visible `Connected` success line,
the `Review inbox` heading, empty-state copy, and a collapsible inbox as the
primary attention surface. The accepted replacement separates unread attention
from all-item analysis history without changing the server-owned opened state or
the hosted iframe contract.

## Decision

1. The side panel shows successful generic analyses whose latest run is
   unopened as a heading-free unread list immediately above the hosted iframe.
   Empty unread state renders no copy and consumes no height.
2. The FrameNest title bar is the native Analysis history control. Its hit
   target is the whole green bar except the existing Settings and
   Connect/Disconnect buttons. It uses native button keyboard behavior and
   starts collapsed on every panel load; collapse state is not persisted.
3. Expanded history appears directly below the title bar, pushes the surviving
   hosted iframe down, and lists every page of latest successful generic results
   in server order. Unread and history may contain the same title.
4. Rows in both lists open the same extension-local review overlay. Clicking a
   row marks its selected run opened through the existing durable actor-scoped
   route. Review Save ensures that mark-opened succeeded before Apply and does
   not restore opened attention.
5. Successful connection renders no `Connected` status line. Configuration and
   framing failures, Connect guidance, `Cleared`, and `Attached` remain visible
   in the existing status region.
6. Ordinary identities receive no review titles: a forbidden response hides
   both lists, collapses and disables history, and clears the toolbar badge.
   The badge remains the server `unopened_count` formatted as `1` through `99`
   or `99+`.

## Preserved contracts

- ADR-0063's hosted FrameNest iframe remains mounted and unchanged while review
  lists render or history expands and collapses; hosted Gallery Attach remains
  available.
- The badge has no second counter, no title content, no OS notification, and no
  `notifications` permission.
- The review overlay remains a sibling extension surface, not content inside
  the hosted iframe. The ingest Save overlay remains frozen.
- Exactly four `companion_mutation` routes remain: X submit, X retry, review
  opened, and review apply.
- ADR-0068 G2 readiness-triggered publication, ADR-0069's generic v4 one-to-five
  tag contract, and ADR-0070's movie exclusion remain unchanged.

## Superseded statements

ADR-0071 remains accepted. Only its collapsible-inbox chrome decision, and the
associated implementation statements that exposed a `Review inbox` heading and
empty-state copy, are succeeded by this unread-list and title-bar-history
design. ADR-0071's iframe-survival, badge, no-notifications, overlay separation,
and ingest-Save statements remain in force.

The matching collapsible-inbox, heading, and empty-copy descriptions in
[docs/X_COMPANION.md](../X_COMPANION.md) are likewise succeeded. No other
companion trust, mutation, or hosting statement is superseded.

## Consequences

The service worker aggregates sequential 100-row inbox pages and follows the
server cursor without client re-sorting. A repeated cursor or any later-page
failure fails the complete list and clears the badge rather than exposing a
partial history. Both history and unread lists have bounded scroll height; an
empty list occupies no chrome. Full-history refresh cost grows with the number
of eligible media, and a concurrent analysis may appear on the next poll.

No HTTP route, JSON field, database schema, manifest permission, or companion
message type changes. The existing `REVIEW_INBOX` response shape is retained,
with `items` fully aggregated by the service worker.

## References

- [ADR-0063](0063-companion-side-panel-web-host.md)
- [ADR-0067](0067-administrator-companion-review-inbox-and-mutation-trust.md)
- [ADR-0068](0068-companion-review-save-and-readiness-triggered-publication.md)
- [ADR-0069](0069-five-tag-generic-media-suggestion-contract.md)
- [ADR-0070](0070-companion-exclusion-of-movie-workflows.md)
- [ADR-0071](0071-native-side-panel-review-inbox-chrome.md)
- [docs/X_COMPANION.md](../X_COMPANION.md)
