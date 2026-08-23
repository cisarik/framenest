# ADR-0068: Companion Review Save and Readiness-Triggered Publication

## Status

`Accepted`

## Decision Date

`2026-08-23`

## Context

ADR-0049 requires explicit administrator publication and keeps ordinary Gallery
published-only. The accepted companion product is G2: after a successful review
Save of checkmarked fields, publish when canonical title, description, and at
least one tag are then present. NIM completion alone must not publish.

## Decision

1. Companion review Save writes only checkmarked fields (title, tags,
   description). Tags replace, they do not union. Zero-tag apply is forbidden.
2. After those writes, if publication readiness holds and the item is
   unpublished, the same transaction publishes with an honest companion-review
   origin. Already-published items stay published; origin and timestamp are
   preserved.
3. Not-ready is a successful metadata transaction without publication. Missing
   fields remain `display_title`, `description`, then `tags`.
4. Publication never occurs on analysis completion, X ingest Save, row opening,
   or dropdown selection.
5. Ordinary `GET /api/media` stays published-only. Website Publish remains.
6. This ADR is an accepted contract. This Worker does not implement apply or
   publication.

## Superseded statements

ADR-0049 remains accepted. Only the explicit-route-only publication rule is
narrowly superseded for companion review Save when readiness holds. Other
automatic publication stays forbidden.

## Consequences

An administrator can publish NIM-influenced metadata by checkmarking fields and
Saving. Structural readiness is not semantic quality. Residual product risk
belongs to the Cooperator.

## Deferred

Apply HTTP, receipts, atomic publication, and G2 tests.

## References

- [ADR-0049](0049-durable-content-publication-boundary.md)
- [ADR-0067](0067-administrator-companion-review-inbox-and-mutation-trust.md)
