# ADR-0050: Durable Manual Cover Foundation

## Status

`Accepted`

## Decision Date

2026-08-02

## Context

FrameNest's Gallery and Details cortex describe durable covers as separate from
regenerable Gallery previews ([COVER_PIPELINE.md](../../COVER_PIPELINE.md),
[GALLERY.md](../../GALLERY.md), [ADR-0024](0024-cover-studio-and-ai-cover-candidates.md),
[PRODUCT.md](../../PRODUCT.md), [SPEC.md](../../SPEC.md)). Before this decision
there was no persistent cover schema, no durable server-owned cover artifact, no
manual source-frame workflow, no cover thumbnail, and no cover API. The only
persisted image derivatives were regenerable `gallery-preview-jpeg-v1` cache
artifacts.

This ADR records the bounded durable foundation for the first manually selected
cover: at most one accepted cover per logical medium, selected from an available
GIF or MP4 source at an exact integer-millisecond timestamp, stored with
sanitized provenance, and served to the Gallery through a validated cover
thumbnail. It deliberately does not implement Cover Studio, imported/AI/series
covers, cover candidates, bulk operations, or a background job system.

## Decision

### Persistence

Migration `0022` adds a sparse `media_covers` table keyed by `media_id`
(`ON DELETE CASCADE` to `logical_media`). Absence means "no accepted cover".
The row stores immutable logical `media_id`, a nullable live
`source_location_id` (`ON DELETE SET NULL`), an opaque immutable
`source_reference` (`location:<uuid>`), normalized `source_kind` (`gif`/`mp4`),
`source_timestamp_ms`, observed source size and mtime, optional source
duration, a versioned `source_observation_digest`, the artifact profile/media
type/sha256 digest/width/height/byte size, a `revision` counter starting at 1,
and `accepted_at_ms`.

The accepted cover belongs to logical media. Physical source information is
provenance, not ownership. Deleting a physical location sets the live FK to
`NULL` and keeps the cover row and its durable artifact usable. Deleting the
logical medium cascades the cover row according to the existing lifecycle
conventions.

### Source-version fencing

A deterministic opaque `source_version` (SHA-256 of a versioned JSON
observation over `media_id`, `location_id`, normalized kind, observed size,
observed mtime, and server-authoritative duration) is returned by the timeline
endpoint, required by frame preview and acceptance, re-verified after
extraction, and persisted with the row. Any mismatch rejects the request with a
sanitized `COVER_SOURCE_CHANGED` and leaves the previous accepted cover
unchanged. The browser never uploads pixels.

### Durable artifact and thumbnail roots

- `FRAMENEST_COVER_STORAGE_ROOT` (development default under the temporary
  development state; production-oriented `/var/lib/framenest/covers`) holds
  immutable content-addressed durable JPEG artifacts.
- `FRAMENEST_COVER_THUMBNAIL_CACHE_PATH` (development default under the
  temporary development state; production-oriented
  `/var/cache/framenest/cover-thumbnails`) holds regenerable
  `cover-thumbnail-jpeg-v1` derivatives.

Both roots are absolute, disjoint from the database, registered media roots,
Gallery preview cache, upload quarantine, YouTube acquisition storage, and one
another. Artifacts are published no-clobber (`os.link`-style) with temporary
file creation, fsync, re-validation, and directory fsync; an existing
immutable identity is never replaced. Old and orphaned content-addressed
artifacts are retained in this slice; no broad cleanup/eviction is added.

### Authoring boundaries and API

The authoring workflow is administrator-only through the existing
`metadata.canonical.write` capability. The accepted-cover mutation uses the
security-audit action `media.cover_set` recorded before mutation, consistent
with the Tailscale ingress architecture (ADR-0048) and migration `0020`.

Routes (all identity-only, no path-bearing fields):

- `GET /api/media/{media_id}/locations/{location_id}/cover-timeline`
- `GET /api/media/{media_id}/locations/{location_id}/cover-frame?timestamp_ms=&source_version=`
- `PUT /api/media/{media_id}/locations/{location_id}/cover`
- `GET /api/admin/media/{media_id}/cover`
- `GET /api/media/{media_id}/cover-thumbnail`

The cover-thumbnail read requires `gallery.read` and enforces the shared
content-publication visibility policy: ordinary users receive no cover bytes
for unpublished media. The Gallery catalog response exposes `cover_ready` only
when a validated cover thumbnail is actually present (bounded read-only
aggregation; no generation on read). Gallery cards prefer the cover thumbnail
and fall back to the existing `gallery-preview`/fallback path, never
reclassifying the preview as the accepted cover.

### Thumbnail ETag

The cover-thumbnail ETag binds the `cover-thumbnail-jpeg-v1` algorithm identity
to the accepted artifact digest, so a later algorithm change cannot return a
stale `304` for the previous representation.

### Migration downgrade

A populated `0022 -> 0021` downgrade fails closed with a clear operator-facing
error instead of silently discarding accepted cover state. An empty
`media_covers` downgrade may drop the schema. Application code running ahead of
the migration ignores `media_covers` and reproduces the pre-cover Gallery
behavior.

## Backup and recovery limitation

The catalog backup bundle remains catalog-only and unchanged. Accepted cover
rows travel inside the SQLite catalog artifact. Durable cover artifacts and
cover thumbnails are excluded from the bundle: thumbnails are regenerable cache
state, and durable artifacts are regenerable from the recorded source location
and source version only while those remain available. After a restore, an
artifact may be regenerated when the recorded source is available; otherwise
manual re-selection is required. FrameNest does not claim complete disaster
durability for cover artifacts in this slice.

## Consequences

### Positive

- One accepted manual cover per logical medium is durable and displayable
  without rereading the original video.
- Server-authoritative extraction and source-version fencing prevent stale or
  fabricated cover pixels.
- The Gallery gains cover priority with an unmodified fallback, and the
  preview/cover conceptual separation is preserved.
- Stale/replaced browser tabs cannot silently overwrite a newer accepted cover.

### Costs and limitations

- Media-derived covers require an available GIF/MP4 source at authoring time.
- Thumbnails regenerate only on acceptance or via the explicit operator CLI
  (`framenest-covers`); a missing thumbnail falls back until regenerated.
- Durable artifacts are not included in the catalog backup bundle.
- Still-image manual cover authoring, imported/AI/series covers, candidate
  history, bulk operations, and background generation remain out of scope.

## Rejected Alternatives

- Unconditional populated downgrade: rejected because it would silently discard
  accepted cover state.
- `ON DELETE RESTRICT` on `source_location_id`: rejected because the cover must
  survive physical-location loss (the accepted decision uses `SET NULL` plus
  opaque provenance).
- Read-through thumbnail generation: rejected because Gallery reads must remain
  mutation-free.
- Unconditional `os.replace` artifact publication: rejected because immutable
  content-addressed identities must never be overwritten.
- `gallery-preview-jpeg-v1` promotion into a cover: rejected; the preview and
  cover concepts remain distinct.

## Revisit Triggers

Revisit when authorizing Cover Studio, imported/AI/series covers, cover
candidates, bulk cover operations, artifact eviction/cleanup, cover inclusion
in the backup bundle, still-image cover authoring, background generation, or
thumbnail lifecycle automation.

## Addendum (2026-08-02): Still-Image Manual Cover Authoring

A bounded follow-on slice extends this accepted foundation to still-image
(JPEG/PNG) cover sources without changing the durability, fencing, replacement,
audit, storage, or audience contracts recorded above. This addendum supersedes
the "still-image manual cover authoring" out-of-scope statements in
[Costs and limitations](#costs-and-limitations) and
[Revisit Triggers](#revisit-triggers) for exactly this slice.

- Migration `0023` widens the `media_covers.source_kind` check constraint to
  `('gif', 'mp4', 'image')`; existing GIF and MP4 cover rows are preserved and
  no other column or table changes.
- A still-image source is timeless: it carries no fabricated duration, exposes
  no selectable timeline, and reuses the existing non-null integer
  `source_timestamp_ms` with the explicit canonical value `0`. The value and
  the API/UI never present it as a selected temporal frame.
- Still-image sources are observed for size, mtime, kind, reference, and
  availability and fenced by the same deterministic source-version digest; the
  existing optimistic-concurrency and source-change protection applies
  unchanged.
- The accepted artifact remains the normalized `durable-cover-jpeg-v1` JPEG and
  its `cover-thumbnail-jpeg-v1` derivative; the original still-image bytes and
  location are never modified.
- Still-image decoding reuses the existing bounded Pillow still-image
  preparation boundary (no ffprobe/ffmpeg invocation), consistent with the
  accepted still-image media foundations from migration `0016`.
- The browser upload cockpit truthfully accepts `.jpg`/`.jpeg`/`.png` and
  `image/jpeg`/`image/png`; server-authoritative validation remains unchanged.
- Authoring stays administrator-only through `metadata.canonical.write` with
  the existing `media.cover_set` security-audit action; ordinary users retain
  read/download visibility and no mutation action.

## Related Documents

- [ADR index](README.md)
- [ADR-0024](0024-cover-studio-and-ai-cover-candidates.md)
- [ADR-0033](0033-catalog-backup-and-recovery-foundation.md)
- [ADR-0035](0035-authoritative-server-and-client-state-model.md)
- [ADR-0048](0048-tailscale-remote-access-and-identity-foundation.md)
- [ADR-0049](0049-durable-content-publication-boundary.md)
- [COVER_PIPELINE.md](../../COVER_PIPELINE.md)
- [GALLERY.md](../../GALLERY.md)
- [PRODUCT.md](../../PRODUCT.md)
- [SPEC.md](../../SPEC.md)
- [ROADMAP.md](../../ROADMAP.md)
