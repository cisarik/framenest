# ADR-0044: Durable Automatic Post-Catalog AI Analysis

## Status

`Accepted`

## Decision Date

2026-07-19

## Context

FrameNest already has deterministic local preparation and provider-neutral
on-demand suggestion preview. After an upload reaches durable `cataloged`,
operators may want the same suggestion pipeline to run automatically without
opening Gallery and clicking Analyze.

The previous planning recommendation preferred persistence without execution.
Owner clarification for this MVP requires real server-side execution during
work in progress, with a truthful durable lifecycle that survives restart.

Automatic cloud frame upload remains forbidden unless an explicit server-owned
enablement boundary is set. Interactive preview continues to require
`confirm_cloud_upload: true`.

## Decision

FrameNest accepts an optional durable automatic analysis lifecycle for newly
cataloged uploads:

1. Configuration flag `FRAMENEST_AUTOMATIC_MEDIA_ANALYSIS_ENABLED` defaults to
   `false`. When false, cataloging never schedules analysis.
2. After a successful `published -> cataloged` transition, the catalog
   coordinator may notify a single-process analysis coordinator.
3. Migration `0015` adds `media_analysis_runs` with one row per
   `(media_id, analysis_definition)`, lifecycle states
   `pending | analyzing | analyzed | failed`, normalized suggestion JSON on
   success, and sanitized error fields on failure. No historical backfill.
4. Short SQLite transactions create, claim, complete, or fail runs. Provider
   and ffmpeg/ffprobe work run outside write transactions.
5. Startup reconciles only unfinished requested runs. Historical catalog rows
   without a run are not treated as paid jobs.
6. API exposes capability and per-media status without credentials, paths, or
   raw provider payloads. Gallery visibility does not depend on analysis state.
7. Existing on-demand preview routes remain unchanged.

## Authorization Boundary

Server-owned enablement of automatic analysis is the consent boundary for
non-interactive cloud frame upload. Credentials remain server-only. The
current product remains trusted-loopback and single-tenant.

## Rejected Alternatives

- Persistence without execution: rejected by Owner MVP clarification.
- Bulk analysis of the existing catalog at migration or startup: would invent
  paid work and expand scope.
- Redis/Celery/distributed queues: unnecessary for the current single-process
  topology.
- A second suggestion schema: reuse the existing normalized suggestion fields.

## Consequences

- Automatic analysis is opt-in and off by default.
- Catalog success is independent of provider availability.
- SPEC and PRODUCT statements that forbade all automatic cloud upload are
  narrowed to require explicit server enablement for this path.
- Manual re-analysis history, editable drafts, and provider-management UI
  remain deferred.

## Related

- [ADR-0016](0016-provider-neutral-media-suggestions-and-nvidia-nim-prototype.md)
- [ADR-0020](0020-on-demand-ai-suggestion-review.md)
- [ADR-0043](0043-upload-to-catalog-transaction.md)
