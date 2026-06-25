# ADR-0027: Persistent Display Title and Canonical Tags

## Status

`Accepted`

## Decision Date

`2026-06-25`

## Decision Authority

The Orchestrator authorized this bounded architecture decision and vertical
slice through task `FRAMENEST-CYCLE-065-PERSISTENT-TITLE-AND-CANONICAL-TAGS`.

## Context

FrameNest has a minimum persistent logical-media and physical-location catalog
foundation through [ADR-0025](0025-minimum-persistent-media-catalog-foundation.md)
and explicit idempotent scan-candidate import through
[ADR-0026](0026-explicit-idempotent-scan-candidate-import.md). Imported media
records still need user-editable catalog metadata without confusing catalog
state with physical filenames, library-relative paths, media bytes, AI drafts,
or future file-organization workflows.

This decision implements only persistent display title and canonical
content-tag core. It does not implement browser metadata editing, search,
filtering, descriptions, collections, suggested filenames, covers, gallery
data, sidecars, or filesystem rename behavior.

## Decision

### Display title

A logical medium may have zero or one persisted user-editable display title.
Absence is represented as `None` and SQL `NULL`. An empty string is not a
title.

A title must be valid before construction. Inputs with leading or trailing
whitespace are rejected rather than silently changed. A title may contain at
most 240 Unicode code points. NUL and Unicode control characters are forbidden.

Changing or clearing a display title never changes the physical filename,
library-relative path, media bytes, or filesystem timestamps. An untitled
logical medium remains valid. Presentation fallback to a physical filename is
future application or UI behavior and is not persisted as the display title.

### Canonical tag identity

Canonical tags in this slice are content and organization tags. Source platform
remains a separate future structured field and must not be conflated with
content tags.

The canonical tag key is the stable internal identity. No UUID tag identity is
introduced. Keys are English lowercase ASCII slugs. Valid examples include:

- `mathematics`
- `compression`
- `meme`
- `reaction-video`

Key grammar:

- starts with `a-z`;
- contains only `a-z`, `0-9`, and single `-` separators;
- has no leading or trailing hyphen;
- has no consecutive hyphens;
- has a maximum length of 64 characters.

The key is immutable in this slice.

The display name is separate presentation text, for example key `mathematics`
and display name `Math`. Display names are English, are trimmed, contain 1 to
80 Unicode code points, and forbid NUL and Unicode control characters.

No hardcoded initial tag catalog is seeded. Canonical tag deletion and rename
are not implemented.

### Tag creation

Tag creation is explicit through a dedicated application and same-origin API
boundary. Creating a new key stores one canonical definition. Repeating creation
with the same key and exactly the same display name is idempotent. Repeating
creation with the same key and a different display name is a conflict.

A metadata save cannot implicitly create or rename canonical tags.

### Media-tag assignment

One logical medium may have zero to 32 canonical tags. Tag assignment is
ordered. Order is persisted using a zero-based integer position.

A media item cannot contain the same tag key twice. Saving metadata replaces
the complete ordered tag assignment set atomically. All referenced tag keys must
already exist. Saving an empty tag list removes all assignments. Assignment
never changes global canonical-tag definitions.

### Metadata persistence

Metadata is stored separately from physical locations. The database uses a
sparse one-to-one metadata row:

- no metadata row is required merely because media was imported;
- a media item without a row is read as title `null`, tags `[]`, and
  `persisted: false`;
- the first explicit save creates the row;
- later saves update it.

Metadata timestamps are application-owned non-negative integer milliseconds.

A semantically identical save is a no-op: no row update, no assignment rewrite,
the existing `updated_at_ms` remains unchanged, and the result status is
`unchanged`. First save returns `created`. A changed existing save returns
`updated`.

First save or replacement of tags and title is one transaction. A failure must
preserve the complete previous state.

Media-file mutation, AI calls, sidecars, covers, descriptions, collections,
suggested filenames, search, and gallery behavior are out of scope.

### Migration

Migration head becomes `0005`.

Revision `0005` creates:

- `canonical_tags`
- `media_metadata`
- `media_canonical_tags`

Existing `0004` device, library, logical-media, and location rows survive
unchanged. Upgrade does not create metadata rows automatically. Downgrade
removes only the metadata and tag schema introduced by `0005`. No media,
location, library, or device row may be deleted by downgrade.

## Consequences

FrameNest now has the persistent local catalog core needed to store a
user-edited display title and ordered canonical content tags for imported
logical media. The same-origin API can create canonical tags, list canonical
tags, read media metadata, and save a complete metadata replacement.

This unlocks later browser metadata editor, title search, multi-tag AND
filtering, manual metadata workspace, covers, and gallery tasks without
silently coupling those future features to scan import or filesystem mutation.

## Artifact Lifecycle

Classification: durable normative architecture decision.

Consumers: domain, migration, repositories, API, future metadata UI, future
search/filtering, ORCHESTRATOR and WORKER instances.

Inbound references: ADR index plus bounded product/specification documents.

Retention: until explicitly superseded.

Cleanup owner: only a future explicitly authorized task.

No temporary research Markdown artifact was created.

## Related Documents

- [ADR index](README.md)
- [ADR-0023](0023-manual-first-metadata-and-multi-model-ai-drafts.md)
- [ADR-0025](0025-minimum-persistent-media-catalog-foundation.md)
- [ADR-0026](0026-explicit-idempotent-scan-candidate-import.md)
- [SPEC.md](../../SPEC.md)
- [ROADMAP.md](../../ROADMAP.md)
