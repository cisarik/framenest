# ADR-0040: Canonical Upload Byte Identity Foundation

## Status

`Accepted`

## Decision Date

2026-07-15

## Context

Durable upload validation already records server-derived checksum, size, media
kind, and media format evidence on `upload_sessions`. The next foundation slice
needs an internal exact-byte identity that can converge identical successful
uploads without changing Gallery visibility or deciding duplicate product
behavior.

## Decision

FrameNest stores canonical exact-byte identity in `media_byte_identities`.
The identity tuple is:

- `checksum_algorithm = sha256`;
- `size_bytes > 0`;
- lowercase 64-character hexadecimal `checksum_hex`.

The tuple is unique. The identity is separate from `LogicalMedia`, physical
media locations, paths, filenames, display titles, client MIME data, and
publication state.

Successful upload validation obtains or creates the canonical byte identity in
the same transaction that records upload checksum evidence, validation evidence,
the internal `upload_sessions.byte_identity_id` link, and the
`publish_pending` state. Identical byte tuples converge on one identity row.
Different sizes or digests do not converge.

Migration `0011` backfills only coherent validation-success-derived upload
states from existing database evidence. It does not read media files, hash
files, run media tools, scan libraries, or contact providers. Incoherent
successful legacy rows fail closed with a sanitized migration failure.

## Non-Visibility

This foundation remains internal. It creates:

- zero publication files;
- zero logical media;
- zero physical media locations;
- zero Gallery visibility;
- zero content-serving visibility;
- zero previews;
- zero AI analysis.

Upload HTTP responses do not expose `byte_identity_id` or byte-identity rows.

## Deferred Behavior

Duplicate semantics remain intentionally deferred. This decision does not add
duplicate review, duplicate APIs, duplicate UI, automatic reuse, publication,
catalog insertion, scan/import hashing, or content-addressable storage.

## Related Documents

- [ADR index](README.md)
- [ADR-0037](0037-durable-upload-session-and-safe-ingest-foundation.md)
- [ADR-0038](0038-bounded-upload-media-validation.md)
- [ADR-0039](0039-lifecycle-owned-upload-validation-orchestration.md)
