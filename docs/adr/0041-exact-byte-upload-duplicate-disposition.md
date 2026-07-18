# ADR-0041: Exact-Byte Upload Duplicate Disposition

## Status

`Accepted`

## Decision Date

2026-07-18

## Context

Successful upload validation already derives a canonical byte identity from the
validated size and SHA-256 digest. Identical uploads converge on one internal
identity, but every successful session previously continued directly to
`publish_pending`. FrameNest needs an explicit user decision for a later exact
copy without adding publication, catalog reuse, or Gallery visibility.

## Decision

The first transactionally committed upload with a canonical byte identity and a
qualifying state becomes the publication candidate and reaches
`publish_pending`. A later successfully validated upload with the same identity
reaches `duplicate_pending`.

Only `publish_pending`, `published`, and `cataloged` qualify as prior canonical
states. `duplicate_pending`, `rejected`, `cancelled`, `expired`, and `failed` do
not independently cause later sessions to be classified as duplicates. A
session is excluded from its own duplicate lookup, and repeated validation
completion preserves its committed result.

Canonical identity convergence, qualifying-state lookup, validation evidence,
final state, and session version update share one SQLite write transaction. The
write transaction is acquired before the qualifying-state lookup, so concurrent
validation through distinct connections has one commit-ordered winner.

A `duplicate_pending` session remains in quarantine until one explicit
resolution:

- `Keep as separate item` moves only that session to `publish_pending` and
  retains its quarantine object.
- `Discard duplicate` durably cancels only that session and then removes only
  its quarantine object. If removal fails, the session remains cancelled and a
  sanitized failure is reported.

Repeated identical resolutions are idempotent. A later conflicting resolution
fails without changing state or storage. State version ownership makes
concurrent keep and discard operations produce exactly one durable winner.

## Identity and Privacy Boundaries

Duplicate identity uses only server-derived validated byte size and SHA-256
digest. Filename, title, client metadata, path, timestamps, and media format do
not affect the comparison. Existing scan-imported catalog media is not hashed or
compared.

The resolution API uses only the opaque upload-session identity and exposes a
sanitized state snapshot. It does not reveal the matching session, byte identity,
checksum, storage key, path, original filename, library location, or canonical
target details.

## Non-Visibility

Both `publish_pending` and `duplicate_pending` remain outside publication and
the catalog. This decision creates no publication files, logical media, physical
locations, Gallery entries, content-serving visibility, previews, or AI work.

## Deferred Behavior

Publication, upload-to-catalog creation, automatic catalog reuse, logical-media
merge, physical-location merge, alternate-location deduplication, and hashing
existing libraries remain separate future decisions.

## Related Documents

- [ADR index](README.md)
- [ADR-0037](0037-durable-upload-session-and-safe-ingest-foundation.md)
- [ADR-0038](0038-bounded-upload-media-validation.md)
- [ADR-0039](0039-lifecycle-owned-upload-validation-orchestration.md)
- [ADR-0040](0040-canonical-upload-byte-identity-foundation.md)
