# ADR-0028: Catalog Read Model and Search Semantics

## Status

`Accepted`

## Decision Date

`2026-06-26`

## Decision Authority

The Orchestrator authorized this bounded architecture decision and vertical
slice through task
`FRAMENEST-CYCLE-067-SEARCHABLE-CATALOG-BROWSER`.

## Context

FrameNest has persistent logical media and physical locations through
[ADR-0025](0025-minimum-persistent-media-catalog-foundation.md), explicit
idempotent scan-candidate import through
[ADR-0026](0026-explicit-idempotent-scan-candidate-import.md), and persistent
display-title and canonical-tag metadata through
[ADR-0027](0027-persistent-display-title-and-canonical-tags.md). Imported media
records were not yet reachable through a normal catalog media-list API or a
browser catalog surface.

The next product work needs a deterministic read model that can list imported
media, search persisted display titles, and filter by canonical tags without
adding the manual metadata editor, premium gallery, cover pipeline, or schema
changes prematurely.

## Decision

FrameNest adds a dedicated read-only catalog query boundary:

- application query use case: `ListMediaCatalog`;
- read repository port: `MediaCatalogRepository`;
- SQLAlchemy Core SQLite read adapter: `SqliteMediaCatalogRepository`;
- same-origin API route: `GET /api/media`;
- packaged vanilla browser Catalog section.

This read model is separate from the write-oriented `MediaRepository` and
`MediaMetadataRepository`. Product-specific joined search behavior is not added
to those write ports. The application layer remains independent of FastAPI,
SQLAlchemy, and browser details.

### API contract

`GET /api/media` accepts:

- `q`: optional display-title query;
- repeated `tag`: optional canonical tag keys;
- `limit`: integer, default `24`, minimum `1`, maximum `100`;
- `offset`: integer, default `0`, minimum `0`.

The successful response contains `items`, `total`, `limit`, `offset`, normalized
`q` or `null`, and normalized canonical `tag_keys`.

Each item exposes only catalog-safe structured data:

- `media_id`;
- `media_kind`;
- `created_at_ms`;
- `updated_at_ms`;
- nullable `display_title`;
- ordered `tags`;
- deterministic `locations`.

Tags expose `key`, `display_name`, and `position`. Locations expose
`location_id`, `library_id`, `relative_path`, `availability`,
`observed_size_bytes`, and `observed_mtime_ns`.

The route does not expose absolute library roots, arbitrary host filesystem
paths, provider information, secrets, raw media, or frames.

### Title search semantics

Search uses only persisted `media_metadata.display_title`.

FrameNest does not search physical filenames, library-relative paths,
suggested filenames, descriptions, AI drafts, filesystem content, or provider
payloads in this slice.

The application trims leading and trailing whitespace. An absent or
whitespace-only `q` means no title filter. The normalized query may contain at
most 240 Unicode code points. NUL and Unicode control characters are rejected.

The SQLite adapter matches a literal substring, not a SQL wildcard expression.
The adapter escapes `%`, `_`, and the chosen escape character before applying
`LIKE`. Matching uses SQLite built-in `NOCASE` behavior. This is sufficient for
the bounded local MVP slice, but it does not guarantee full Unicode
case-folding. A derived normalized-title column and a general search engine are
deferred.

### Tag filtering semantics

Each `tag` value must validate as a `CanonicalTagKey`. Repeated identical keys
are normalized to one filter at the application boundary. Zero tag filters mean
no tag constraint.

Multiple distinct selected tag keys use AND semantics: a logical medium must
contain every requested canonical tag. A syntactically valid but nonexistent
key returns a valid empty result page. Tag order in each result follows the
persisted media assignment order.

Source platform remains separate future structured metadata. This read model
does not reinterpret source platform as a canonical content tag.

### Ordering and pagination

The default result order is:

1. `logical_media.created_at_ms` descending;
2. `logical_media.id` ascending as the stable tie-breaker.

The order does not depend on display title, tag order, SQL row accident, or
physical-location row order. The response returns the total filtered logical
media count before bounded offset pagination is applied. Cursors, full-text
search, and a general search engine are deferred.

### Result assembly

Media without a persisted metadata row remain visible in unfiltered listings
with `display_title: null` and `tags: []`.

Media with multiple physical locations appear exactly once as one logical
result item. Location order is deterministic:

1. `library_id` ascending;
2. `relative_path` ascending;
3. `location_id` ascending.

The SQLite adapter avoids an unbounded N+1 query pattern by loading the page of
logical media, ordered tags, and ordered locations in bounded batched queries.

### Browser workflow

The packaged vanilla browser shell now includes a Catalog section. It loads the
first catalog page automatically, loads canonical tag definitions from the
existing same-origin tag API, provides display-title search, selectable
canonical tag filters, active-filter removal, empty/loading/unavailable/error
states, and Previous/Next offset pagination.

After a scan candidate is successfully imported, the browser refreshes the
currently selected catalog query and filters. The browser derives a
presentation-only fallback label from the basename of the first deterministic
relative location when no display title exists. It never persists that fallback
as title truth.

The Catalog section is read-only. It does not scan, analyze, call AI, edit
metadata, save titles or tags, rename files, move files, delete files, show
fake covers, or claim to be the final premium gallery.

### Migration

This decision adds no schema migration. Migration head remains `0005`.

## Consequences

FrameNest now has a normal, deterministic, user-visible way to reach imported
persistent media through a same-origin API and packaged browser shell. This
unblocks the likely next manual metadata detail slice because users can find
and select imported logical media.

The implementation is intentionally limited. SQLite `NOCASE` does not provide
complete Unicode case-folding, offset pagination is the bounded MVP behavior,
and the browser surface is a catalog browser rather than the premium
cover-driven gallery.

## Deferred Decisions

This ADR does not decide or implement:

- persistent metadata editor;
- descriptions;
- collections;
- suggested filenames;
- persistent AI drafts;
- covers or thumbnails;
- premium gallery persistence;
- storage-volume registration;
- title normalization columns;
- full-text search;
- cursor pagination;
- OR tag filtering;
- source-platform filtering;
- filesystem rename, move, or delete workflows;
- Tauri, VLC, NUC deployment, Tailscale, streaming, authentication, or
  provider workflows.

## Artifact Lifecycle

Classification: durable normative architecture decision.

Consumers: application query boundary, catalog read adapter, same-origin API,
browser catalog UI, future metadata detail tasks, future gallery tasks,
ORCHESTRATOR and WORKER instances.

Inbound references: ADR index plus bounded product/specification documents.

Retention: until explicitly superseded.

Cleanup owner: only a future explicitly authorized task.

## Related Documents

- [ADR index](README.md)
- [ADR-0023](0023-manual-first-metadata-and-multi-model-ai-drafts.md)
- [ADR-0025](0025-minimum-persistent-media-catalog-foundation.md)
- [ADR-0026](0026-explicit-idempotent-scan-candidate-import.md)
- [ADR-0027](0027-persistent-display-title-and-canonical-tags.md)
- [SPEC.md](../../SPEC.md)
- [ROADMAP.md](../../ROADMAP.md)
