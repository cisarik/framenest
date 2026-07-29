# ADR-0049: Durable Content Publication Boundary

## Status

`Accepted`

## Decision Date

2026-07-29

## Context

Catalog membership proves that FrameNest knows a logical medium and its
locations. It does not prove that the medium has complete presentation metadata
or that an administrator intended to expose it to the ordinary Gallery
audience. Treating every catalog row as Gallery-visible conflates ingest,
metadata preparation, AI-analysis state, and content publication.

The upload lifecycle also uses the word `published` for verified server-owned
storage bytes. That storage boundary is intentionally distinct from
user-visible content publication and must retain its existing meaning.

FrameNest therefore needs durable content-publication truth, a responsive
administrator workflow for explicit single-item publication, and one audience
policy shared by public catalog and direct-media routes.

## Decision

FrameNest separates catalog membership from content publication.

Migration `0021` adds `media_content_publications`. A row means that one logical
medium is published to the ordinary content audience; absence means
unpublished. The table contains:

- `media_id`, the primary key and a foreign key to `logical_media` with
  `ON DELETE CASCADE`;
- non-negative `published_at_ms`;
- `publication_origin`, constrained to `legacy_backfill` or
  `admin_explicit`;
- an index on `(published_at_ms, media_id)`.

The migration backfills every pre-existing logical medium exactly once with its
`created_at_ms` and `legacy_backfill`. Media created after migration begins
unpublished. Downgrade is allowed only when every logical medium is published,
because otherwise removing the table would silently widen Gallery visibility.

Content is ready for publication only when persisted canonical metadata has a
trimmed non-empty display title, a trimmed non-empty description, and at least
one canonical tag. Missing fields are reported deterministically as
`display_title`, `description`, then `tags`. `Processed` membership and
automatic-analysis state are independent facts and are not publication
prerequisites.

The single-item publication operation is atomic, conditional, idempotent, and
safe under concurrent attempts. A ready unpublished item receives one
`admin_explicit` row. A repeated request returns the existing publication. An
incomplete item remains unpublished. Once published, later metadata regression
does not revoke publication.

## Audience and Authorization

`GET /api/media` returns published media only for every caller. It offers no
parameter that can widen the public audience.

All direct media routes use the same content-audience policy. An unpublished
item is available only to a verified identity with `media.workflow.read`;
ordinary, missing, unmapped, and identity-absent loopback callers receive the
same sanitized not-found result as for an unknown media identity. This applies
to metadata, preview, original content, range, download, and analysis routes.

The administrator list at `GET /api/admin/media` requires
`media.workflow.read`. The mutation at
`PUT /api/admin/media/{media_id}/content-publication` requires
`media.content.publish`, same-origin mutation proof, and an audit record
established before the action. Required audit establishment fails closed.

Neither loopback location nor Tailscale membership grants administrator
authority.

## Administrator Workflow

The packaged web shell has a sibling administrator surface. `Manage media` is
hidden until verified identity resolution explicitly reports
`media.workflow.read`; the permissive legacy loopback capability fallback is
not used for this reveal.

The administrator surface owns independent search, publication, readiness, and
analysis filters, deterministic pagination, list request ownership, per-item
publication request ownership, and transient action status. It defaults to
unpublished items. Stale responses cannot overwrite newer state.

The surface distinguishes readiness, analysis, `Processed`, and publication
with literal text and icons. It reuses the existing Details dialog through a
path-redacted adapter and provides only a single-item Publish action. The
action does not claim success before the server response, prevents duplicate
activation, announces outcomes, and offers explicit retry only for transient
network or server failure.

The layout uses stacked cards at widths through 720 CSS pixels, compact
wrapping rows from 721 through 1023 pixels, and full grid rows from 1024 pixels.
Native controls, at least 44 by 44 CSS-pixel touch targets, visible focus,
non-color state labels, and reduced-motion behavior are required.

## Supersession

This ADR narrowly supersedes the statement in
[ADR-0043](0043-upload-to-catalog-transaction.md) that successful transition to
`cataloged` alone begins Gallery eligibility. `cataloged` still means that the
upload-to-catalog transaction committed and remains required before a content
publication can refer to the logical medium. Ordinary Gallery eligibility now
also requires a durable content-publication row.

ADR-0043's storage publication, upload lifecycle, catalog transaction,
recovery, and provenance decisions remain accepted and unchanged.

## Rejected Alternatives

- Deriving publication continuously from metadata completeness: later metadata
  edits would silently unpublish content and erase administrator intent.
- Storing `is_published` on `logical_media`: a separate sparse relation records
  timestamp and origin while making unpublished absence explicit.
- Allowing public callers to request unpublished rows: this would bypass the
  audience boundary and create object-existence leaks.
- Treating cataloging or `Processed` as publication: both are independent
  workflow facts.
- Adding multi-select, batch jobs, scheduling, unpublish, or approval groups:
  these require separate product and operational decisions.

## Consequences

- Existing catalogs remain visible after migration through explicit legacy
  backfill.
- Newly cataloged media remains outside the ordinary Gallery until ready and
  explicitly published.
- Administrator inspection and ordinary audience access have separate,
  capability-enforced paths.
- Content publication and upload storage publication remain distinct durable
  concepts.
- The catalog backup foundation captures publication rows because they live in
  the authoritative SQLite catalog; complete media-byte backup remains outside
  that foundation.

## Deferred Work

- Multi-select.
- Bulk publish.
- Bulk first analysis.
- Batch progress and reconstruction.
- Retry-failed batch workflows.
- Durable batch jobs.
- Unpublish, scheduling, approval groups, and per-user visibility.
