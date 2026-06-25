# ADR-0026: Explicit Idempotent Scan Candidate Import

## Status

`Accepted`

## Decision Date

`2026-06-25`

## Decision Authority

The Orchestrator authorized this bounded architecture decision and vertical
slice through task `FRAMENEST-CYCLE-063-EXPLICIT-IDEMPOTENT-SCAN-IMPORT`.

## Context

ADR-0014 established bounded read-only library scan preview. ADR-0025
established the minimum persistent logical-media and physical-location catalog
foundation, but deliberately deferred scan import because extension hints must
not become catalog truth automatically.

FrameNest now needs the smallest explicit local workflow that lets a user take
one scan candidate and create durable catalog records without adding metadata,
tags, covers, gallery persistence, background scanning, or filesystem mutation.

## Decision

FrameNest adds explicit import of one selected scan candidate from one
registered library.

The application import use case takes:

- a strict `LibraryId`;
- one library-relative media path;
- bounded scan limits.

The use case reloads the registered library, runs the existing deterministic
filesystem scan through the scanner port, and imports only when the requested
relative path is present in the current scan candidate set. A raw path alone is
not sufficient to create catalog records.

The import maps scan candidate kinds as follows:

- scan `video` becomes persistent media kind `video`;
- scan `gif` becomes persistent media kind `animated_image`.

When no physical location already exists for the exact
`(library_id, relative_path)` pair, the repository creates one `LogicalMedia`
and one `MediaLocation` atomically. The new location is marked `available`,
stores the candidate size as `observed_size_bytes`, stores no modification time
yet, and uses the current domain path normalization rules. Import does not
read media file contents, hash files, inspect codecs, create sidecars, create
thumbnails, infer metadata, or mutate the filesystem.

When a location already exists for the exact `(library_id, relative_path)` pair,
the import returns the existing logical media and physical location without
creating another logical media item, another physical location, or updating
stored values. This makes repeated imports idempotent.

The persistent creation boundary is owned by the `MediaRepository` port and
the SQLite adapter. It must create the logical-media and physical-location rows
inside one transaction so a failed location insert does not leave an orphan
logical-media row.

Migrations remain explicit through `framenest-db migrate`; server startup,
scan preview, and import do not apply migrations automatically. This decision
requires no new database migration beyond revision `0004`.

The first exposure is deliberately small:

- same-origin `POST /api/libraries/{library_id}/media-imports`;
- a packaged browser Import action next to scan-preview candidates.

The API and browser may expose catalog identities and selected library-relative
paths, but must not expose library root paths, database paths, environment
values, raw SQL, stack traces, or provider credentials.

## Deferred Decisions

Deferred scope includes:

- importing multiple candidates in one request;
- durable scan runs or scan history;
- background import jobs, progress streaming, cancellation, or resume;
- updating existing locations from later scan observations;
- duplicate detection across paths or libraries;
- content hashes or perceptual hashes;
- media validation beyond extension-hint scan candidates;
- user-editable title, description, collection, suggested filename, or tags;
- cover and thumbnail persistence;
- gallery presentation of imported records;
- sidecar writes;
- file rename, move, delete, or organization workflows;
- storage-volume linkage;
- server aggregation and synchronization.

## Consequences

FrameNest now has an end-to-end local vertical slice from registered-library
scan preview to explicit persistent catalog import. The imported records are
minimum catalog facts only: one logical media item and one known physical
location. They are not yet gallery items with user metadata, tags, covers, or
thumbnails.

Because import reruns a bounded scan and requires candidate presence, a file
removed after preview is not imported from stale browser state. Because the
workflow is idempotent by `(library_id, relative_path)`, repeated user actions
do not create duplicates.

## Related Documents

- [ADR index](README.md)
- [ADR-0014](0014-safe-library-scan-preview.md)
- [ADR-0025](0025-minimum-persistent-media-catalog-foundation.md)
- [SPEC.md](../../SPEC.md)
- [ROADMAP.md](../../ROADMAP.md)
