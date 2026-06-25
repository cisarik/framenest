# ADR-0025: Minimum Persistent Media Catalog Foundation

## Status

`Accepted`

## Decision Date

`2026-06-25`

## Context

FrameNest needs persistent local catalog records before explicit scan import,
manual metadata editing, canonical tags, covers, thumbnails, gallery search, and
distributed location awareness can be implemented safely.

Existing foundations include stable UUIDv4 identity value objects, local device
and library registries, explicit SQLAlchemy Core/Alembic SQLite migrations, and
read-only scan and media-analysis preview boundaries. Those previews do not
persist media records.

## Decision

FrameNest now establishes the minimum persistent media catalog foundation in
Alembic revision `0004`.

One logical media item represents one conceptual media item independently of
where its bytes exist. It has a stable application-owned `MediaId`, a media
kind, and zero or more physical locations.

Initial media kinds are:

- `video`
- `animated_image`

One physical media location represents one known file location inside one
registered FrameNest library. It has a stable `MediaLocationId`, belongs to
exactly one logical media item, belongs to exactly one registered library, stores
one normalized library-relative path, stores an availability state, may store an
observed file size in bytes, may store an observed modification time in integer
nanoseconds, and stores non-negative integer row timestamps.

Initial availability states are:

- `available`
- `offline`
- `missing`
- `unverified`
- `archived`

The persisted path is library-relative, slash-separated, non-empty, and rejected
when it is absolute, contains NUL, contains empty segments, or contains `.` or
`..` traversal segments. Domain and repository code do not resolve or traverse
the filesystem.

The physical filename is derived from the final component of the relative path.
FrameNest does not persist a duplicated filename column.

The owning device is determined through the registered library. FrameNest does
not duplicate `device_id` on physical media-location records.

Revision `0004` creates:

- `logical_media`
- `physical_media_locations`

It enforces unique logical-media identity, unique physical-location identity,
and one unique physical location for each exact `(library_id, relative_path)`
pair. Different libraries may use the same relative path. The physical-location
table uses explicit restrictive foreign keys to logical media and libraries. It
does not use destructive cascading deletion.

The application layer owns the `MediaRepository` port and sanitized repository
errors. The infrastructure layer owns the SQLAlchemy Core adapter, row mapping,
transaction execution, and database error translation.

Migrations remain explicit through `framenest-db migrate`. Server startup does
not apply migrations automatically.

This decision introduces no scan import, HTTP route, browser UI, desktop UI, or
catalog CLI media command.

## Deferred Decisions

Deferred scope includes:

- explicit idempotent import from selected scan candidates;
- display title;
- description;
- collection;
- suggested filename;
- canonical tags;
- title and tag search;
- manual metadata editing;
- AI drafts;
- covers;
- thumbnails;
- persistent gallery data;
- storage-volume registration;
- content hashes;
- perceptual hashes;
- duplicate detection;
- automatic merge;
- cross-library duplicate discovery;
- replacement-file heuristics;
- deletion workflows;
- sidecar schema;
- synchronization and server aggregation protocols.

## Alternatives Considered

### One database row per physical file with no logical-media layer

Rejected. It would make gallery cards and future metadata duplicate per file
copy. FrameNest needs one logical media item that can have several locations.

### Duplicated device identity on every location

Rejected. The registered library already owns its device relationship. A second
`device_id` on locations would introduce drift and update complexity.

### Storing physical filename separately

Rejected. The current physical filename is the final component of the
library-relative path. A second filename column would duplicate mutable path
state before a rename workflow exists.

### Adding tags and covers into the first catalog migration

Deferred. Tags, covers, and thumbnails need their own domain and persistence
contracts. Including them in `0004` would blur the minimum catalog foundation.

### Automatic scan-to-catalog persistence

Deferred. Scan preview is intentionally read-only. Import requires an explicit,
idempotent, user-approved workflow so FrameNest does not silently create catalog
truth from extension hints.

## Consequences

FrameNest can now persist a logical media item and one or more known physical
locations in a local SQLite catalog after explicit migration to revision `0004`.
This unblocks later bounded tasks for scan import, metadata, tags, covers,
thumbnails, and gallery persistence.

The catalog remains incomplete. There is still no user-facing media catalog
workflow, no persistent scan import, no title or tag metadata, no covers, no
thumbnails, and no gallery backed by these records.

## Related Documents

- [ADR index](README.md)
- [ADR-0010](0010-initial-persistence-foundation.md)
- [ADR-0011](0011-stable-domain-identities.md)
- [ADR-0013](0013-initial-library-registry.md)
- [ADR-0014](0014-safe-library-scan-preview.md)
- [ADR-0022](0022-selective-media-placement-and-server-aggregation.md)
- [ADR-0023](0023-manual-first-metadata-and-multi-model-ai-drafts.md)
- [ADR-0024](0024-cover-studio-and-ai-cover-candidates.md)
- [SPEC.md](../../SPEC.md)
- [ROADMAP.md](../../ROADMAP.md)
