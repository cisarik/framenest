# ADR-0059: Portable Media Sidecar Round-Trip Foundation

## Status

`Accepted`

## Decision Date

`2026-08-14`

## Context

[ADR-0010](0010-initial-persistence-foundation.md) accepted SQLite as the local
catalog index and stated that live SQLite files must not become the sole
durable portable metadata representation. [SPEC.md](../../SPEC.md) already
requires portable sidecar manifests as durable metadata, versioned and
validated writes, and rebuildability of the local index where feasible.
[ADR-0035](0035-authoritative-server-and-client-state-model.md) keeps a
FrameNest server process authoritative for catalog records during normal
operation. [ADR-0033](0033-catalog-backup-and-recovery-foundation.md) backs up
that catalog database; it does not make SQLite portable near-media metadata.

The catalog now stores logical media, one or more physical locations, display
title, description, canonical tags, processed-collection state, content
classification, acquisition source, movie genres, and creator attribution
([ADR-0011](0011-stable-domain-identities.md),
[ADR-0013](0013-initial-library-registry.md),
[ADR-0025](0025-minimum-persistent-media-catalog-foundation.md),
[ADR-0027](0027-persistent-display-title-and-canonical-tags.md),
[ADR-0029](0029-persistent-plain-text-media-description.md),
[ADR-0030](0030-automatic-processed-collection.md),
[ADR-0045](0045-content-classification-and-movie-identification.md),
[ADR-0055](0055-youtube-creator-taxonomy-and-immutable-provenance.md)). Those
records are not yet projectable into a closed, deterministic near-file
document. Without that contract, later filesystem export, validation, compare,
and rebuild slices would invent incompatible encodings.

This decision records the durable v1 sidecar schema and codec. It does not
implement filesystem I/O, application projection, CLI operations, catalog
import, or synchronization.

## Decision

### Authority

During normal operation the FrameNest server catalog remains authoritative for
catalog records and server-owned state. Sidecar v1 is an explicit portable
projection of selected catalog metadata beside one media file. A sidecar is
not live catalog authority, not a second catalog, and not a substitute for
catalog backup.

### Closed v1 object

The codec owns one closed JSON object. Every v1 key is always emitted.
Optional values use JSON `null`. Collections use arrays. Fields are never
omitted.

Root fields are exactly:

```text
format
schema_version
media_id
media_kind
display_title
description
tag_keys
tag_definitions
content_category
acquisition_source
genre_keys
creator_attribution_kind
creator_stable_id
creator_handle
creator_display_name
processed
created_at_ms
updated_at_ms
location
```

Fixed identity:

```text
format = "framenest-media-sidecar"
schema_version = 1
```

Nested contracts:

```text
tag_definitions[] = {
  "key": <canonical tag key>,
  "display_name": <canonical display name>
}

processed = null
or
processed = {
  "collection_key": "processed",
  "processed_at_ms": <non-negative integer>
}

location = {
  "location_id": <canonical UUIDv4>,
  "library_id": <canonical UUIDv4>,
  "relative_path": <portable slash-separated relative path>
}
```

`created_at_ms` and `updated_at_ms` are nullable `MediaMetadataSnapshot`
timestamps, not logical-media or location timestamps. They are either both
`null` or both non-negative integers with `updated_at_ms >= created_at_ms`.

v1 contains no `sidecar_written_at_ms`. Write-time is not durable document
identity. Compare uses document content; content equality is stronger than
timestamp equality. A later operator compare may report `stale` when catalog
metadata timestamps advanced and projected content otherwise matches.

v1 also contains no absolute library root, host path, device identity,
publication state, cover state, checksum, observed size or mtime, availability,
database path or revision, application version, analysis/provider/request
state, requester-private acquisition state, credential, token, cookie,
environment value, secret field, or extension/unknown field.

Identities are canonical RFC 4122 UUIDv4 text. Tag keys are unique.
`tag_definitions` has exactly one definition for every `tag_keys` entry, in the
same order, with no extra definition. Genre keys are unique, bounded, and legal
only for `movie`. Creator fields preserve existing FrameNest attribution
combination rules. Relative paths use existing `MediaRelativePath` rules.
Processed state is absent or exactly the built-in `processed` collection with a
non-negative timestamp.

### Deterministic codec

Canonical bytes are:

- UTF-8 without BOM;
- one JSON object;
- `sort_keys=True`;
- compact separators `(",", ":")`;
- `ensure_ascii=False`;
- `allow_nan=False`;
- exactly one trailing LF byte;
- array order preserved;
- no wall-clock or random value;
- at most 256 KiB.

Encoding the same document twice produces identical bytes. Decoding accepts
`bytes` only, enforces the size bound before parsing, rejects empty input,
UTF-8 BOM, invalid UTF-8, trailing second values, non-object top-level JSON,
duplicate keys at every nesting level, `NaN`/`Infinity`/`-Infinity`, missing
and unknown fields at every closed-object level, and booleans where integers
are required. A present but unsupported `format` or `schema_version` is
`SIDECAR_UNSUPPORTED`. All other schema, type, identity, range, and invariant
failures are `SIDECAR_MALFORMED`. Errors are sanitized: they do not include
raw payload bytes, user strings, paths, exception text, or secret-shaped
values.

The domain API is `SIDECAR_FORMAT`, `SIDECAR_SCHEMA_VERSION`,
`MAX_SIDECAR_BYTES`, `FrameNestMediaSidecarError`, `SidecarTagDefinition`,
`SidecarProcessedState`, `SidecarLocation`, `SidecarDocument`,
`encode_media_sidecar`, and `decode_media_sidecar`. No new dependency and no
Alembic revision are introduced.

### Future operator contract, not this slice

The intended sidecar filename is `{media_filename}.framenest.json` beside the
selected media file. A logical medium may have multiple locations; export
selects exactly one explicit location.

Later slices of this still-open logical whole may add operator operations
`export`, `validate`, and `compare`.

Export outcomes:

- `created`
- `replaced`
- `unchanged`

Compare results are completed observations with exit zero:

- `match`
- `stale`
- `mismatch`
- `missing`

Malformed, unsupported, unsafe, or foreign-identity targets are errors, not
compare results. Future same-directory writes use validated atomic replacement.
Byte-equal output is a no-op (`unchanged`). Malformed, unsupported,
special-file, symlink, and foreign-identity targets are never destroyed.

Filesystem store, application projection, CLI, round-trip integration, and
compare/export execution remain later slices. Catalog import/rebuild, metadata
Save coupling, multi-copy fan-out, synchronization, conflict resolution, UI,
HTTP, migration, deployment, and production behavior are excluded here.

The current implementation boundary is only this ADR, the domain codec, and
unit tests.

## Rationale

SQLite remains the operational catalog and the subject of catalog backup. It is
a live index bound to one server process and one database file. Portable
near-media metadata must survive copying a file to another disk, inspecting
metadata without opening the catalog, and later rebuild work. A closed
deterministic v1 document gives later slices one byte contract instead of
ad-hoc JSON.

Omitting `sidecar_written_at_ms` keeps document identity aligned with projected
catalog content. A write stamp would make byte-equal no-op and content-vs-stale
compare ambiguous. Catalog timestamps already record metadata durability.

Explicit one-location selection avoids silently projecting the wrong copy when
one logical medium has several physical locations.

## Consequences

- Sidecar v1 can be encoded and decoded without filesystem or application
  services.
- Later filesystem and CLI slices must use this codec rather than inventing a
  parallel schema.
- Rebuild, import, Save hooks, and multi-device synchronization remain
  separately authorized.
- Known Windows replace and case-folding evidence remains incomplete; later
  filesystem slices must not assume POSIX `os.replace` semantics on Windows
  without new evidence.

## Related

- [ADR-0010](0010-initial-persistence-foundation.md)
- [ADR-0011](0011-stable-domain-identities.md)
- [ADR-0013](0013-initial-library-registry.md)
- [ADR-0025](0025-minimum-persistent-media-catalog-foundation.md)
- [ADR-0027](0027-persistent-display-title-and-canonical-tags.md)
- [ADR-0029](0029-persistent-plain-text-media-description.md)
- [ADR-0030](0030-automatic-processed-collection.md)
- [ADR-0033](0033-catalog-backup-and-recovery-foundation.md)
- [ADR-0035](0035-authoritative-server-and-client-state-model.md)
- [ADR-0045](0045-content-classification-and-movie-identification.md)
- [ADR-0055](0055-youtube-creator-taxonomy-and-immutable-provenance.md)
- [SPEC.md](../../SPEC.md)
- [SECURITY.md](../../SECURITY.md)
- [ROADMAP.md](../../ROADMAP.md)
