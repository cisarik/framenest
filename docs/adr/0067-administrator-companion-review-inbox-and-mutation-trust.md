# ADR-0067: Administrator Companion Review Inbox and Mutation Trust

## Status

`Accepted`

## Decision Date

`2026-08-23`

## Context

ADR-0061 and ADR-0064 freeze `companion_mutation` at two X POST routes. The
administrator review inbox needs list, history, opened, and field-apply HTTP
that ordinary `x.request` callers must not receive. Alias PUT is not a
canonical-write channel.

## Decision

1. Successor companion routes for inbox list, per-media suggestion history,
   mark-opened, and review apply are administrator-only. Ordinary identities
   receive empty or fail-closed results and must not gain `analysis.run`,
   `metadata.canonical.write`, or `media.content.publish`.
2. New mutations expand `companion_mutation` (or a named successor Origin-gated
   policy that remains service-worker-only). They do not reuse alias PUT, CORS,
   `all_urls`, or content-script FrameNest fetch.
3. Until those routes exist, code continues to flag only the two existing X
   POST mutations. This ADR records the successor contract; implementation is a
   later slice.
4. Opened state is server-durable per administrator identity and media,
   referencing the displayed analysis run. `chrome.storage` is not inbox truth.
5. Website Analyze by AI successes on in-scope (non-movie) media join the same
   inbox. There is no second suggestion store.

## Superseded statements

ADR-0061 remains accepted. Only the statement that companion mutations are
exactly the two X POST routes is superseded for the later review routes named
here.

## Consequences

Inbox and apply become a distinct administrator trust surface. Origin checks
are CSRF-equivalent controls, not authorization. Dual apply capabilities and
fail-closed ordinary access are mandatory when the routes land.

## Deferred

Route implementation, Alembic 0031, overlay, badge, and independent INFOSEC R3.

## References

- [ADR-0061](0061-x-meme-browser-companion.md)
- [ADR-0064](0064-x-save-category-and-public-photo-acquisition.md)
- [ADR-0068](0068-companion-review-save-and-readiness-triggered-publication.md)
