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

- `Keep as separate item` atomically moves only that session to
  `publish_pending` and records the internal `keep_separate` disposition while
  retaining its quarantine object.
- `Discard duplicate` atomically moves only that session to `cancelled` and
  records the internal `discard` disposition, then removes only its quarantine
  object. If removal fails, the durable state and disposition remain
  non-publishable and a sanitized failure is reported.

The nullable disposition is authorization provenance, not public state. `NULL`
means that no duplicate resolution has been proven. In particular, an original
canonical upload at `publish_pending + NULL` is distinct from a kept duplicate
at `publish_pending + keep_separate`; only the latter permits an idempotent Keep
receipt. Likewise, only `cancelled + discard` permits idempotent Discard cleanup,
while ordinary `cancelled + NULL` does not.

Migration `0012` leaves every existing row at `NULL`. It does not infer history
from state or backfill existing `publish_pending` rows, so pre-migration rows are
handled conservatively. Future valid state changes retain recorded provenance.
Repeated identical resolutions are idempotent only when that provenance agrees.
A later conflicting resolution fails without changing state, disposition, or
storage. State version ownership makes concurrent Keep and Discard operations
produce exactly one durable state-plus-disposition winner.

## Identity and Privacy Boundaries

Duplicate identity uses only server-derived validated byte size and SHA-256
digest. Filename, title, client metadata, path, timestamps, and media format do
not affect the comparison. Existing scan-imported catalog media is not hashed or
compared.

The resolution API uses only the opaque upload-session identity and exposes a
sanitized state snapshot. It does not reveal the matching session, byte identity,
checksum, storage key, path, original filename, library location, or canonical
target details. The internal duplicate disposition is also excluded from upload
status, duplicate-resolution, capability, and frontend response models.

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
