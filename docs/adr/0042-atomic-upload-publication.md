# ADR-0042: Atomic Upload Publication

## Status

`Accepted`

## Decision Date

2026-07-18

## Context

Validated uploads can reach `publish_pending`, and an exact duplicate explicitly
kept by the user can reach the same state. Until now that state had no durable
path to server-owned original storage. A state-only transition could also claim
`published` without proving that verified bytes existed outside quarantine.

Publication crosses SQLite and filesystem durability boundaries. It must remain
recoverable after interruption without overwriting an unexpected object,
inventing ownership for historical rows, deleting the only recoverable source,
or making an uncataloged upload visible in Gallery.

## Decision

FrameNest adds a dedicated published-original storage port and POSIX filesystem
adapter. Publication is automatic and lifecycle-owned; there is no public
Publish endpoint or manual Publish control.

Publication is enabled only when `FRAMENEST_UPLOAD_PUBLICATION_LIBRARY_ID`
selects one registered, server-controlled, writable POSIX library by opaque
UUIDv4 identity. The root must already exist, must be a native non-symlink
directory, and must not overlap quarantine, the Gallery preview cache, the
database parent, or another registered POSIX library. Missing configuration
leaves uploads safely at `publish_pending` and performs no publication write.
Invalid explicit configuration fails startup with sanitized diagnostics.

Each upload owns exactly one durable publication reservation. Its independent
opaque UUIDv4 publication identity determines a server-owned `.mp4` or `.gif`
target name. Client filenames, paths, and byte digests do not select the target.
Byte identity verifies content but is not the idempotency key. Consequently, an
exact duplicate kept as a separate item receives a distinct physical target;
this decision introduces no physical deduplication.

## Persistence and State Ownership

Migration `0013` adds one `upload_publications` row per upload, with restrictive
foreign keys, unique publication identity, unique destination-plus-target,
expected byte-identity and validation evidence, reservation/verification state,
cleanup progress, timestamps, and optimistic versioning.

The migration creates the table empty. It preserves existing upload, byte
identity, and duplicate-disposition data but does not infer a target, verified
ownership, or cleanup completion. Legacy `published` and `cataloged` rows that
lack publication provenance remain identifiable and are not adopted.

Generic upload state transitions cannot commit either
`publish_pending -> published` or `published -> cataloged`. A specialized
repository transaction alone may mark the reserved publication verified and
move its upload to `published`. No specialized upload-to-catalog transaction
exists yet, so `cataloged` remains unavailable.

## Filesystem and Transaction Ordering

The publisher follows this durability order:

1. Reserve exactly one destination and target in a short SQLite transaction.
2. Open the exact quarantine object without following symlinks.
3. Exclusively create a restrictive publication-owned temporary file under the
   validated root.
4. Stream bytes while computing SHA-256 and checking exact size and stable
   regular-file source identity.
5. Flush and `fsync` the temporary file.
6. Atomically publish without replacement by linking the owned temporary inode
   to the absent final name through directory file descriptors.
7. `fsync` the containing directory, then remove the temporary name and
   `fsync` the directory again.
8. Atomically persist verified publication provenance and `published`, leaving
   quarantine cleanup pending.
9. Remove only the upload's exact quarantine object and persist cleanup
   completion idempotently.

An expected final target found during retry is adopted only after complete size
and SHA-256 verification. Unexpected bytes, symlinks, directories, or target
collisions are never overwritten or adopted. Failure before verified ownership
preserves quarantine. Failure after the database publication commit leaves
`published + cleanup_pending`; it never demotes the upload or deletes the
published target.

## Recovery and Lifecycle

A single lifecycle-owned coordinator performs bounded filesystem work off the
event loop. It reconciles eligible durable work at startup, is notified after
validation or Duplicate Keep reaches `publish_pending`, isolates failures by
upload, retries with bounded backoff, and shuts down deterministically.

Per-upload in-process ownership, SQLite serialization, uniqueness constraints,
and optimistic state/version checks define the accepted single-process safety
boundary. Multiprocess or distributed publication requires leases or fencing
and remains deferred.

## API, Catalog, and Privacy Boundaries

Public upload responses continue to expose only the high-level upload state.
They do not expose publication identity, destination, target, library root,
quarantine key, checksum, byte identity, duplicate disposition, cleanup state,
or internal storage errors.

`published` means verified server-owned bytes and durable publication
provenance exist. It does not mean cataloged or Gallery-visible. Publication
creates no logical media, physical location, metadata, tag, collection,
preview, cover, or upload-to-catalog link. The browser reports published uploads
as awaiting cataloging and not yet available in Gallery.

Published originals are media bytes and remain outside the catalog-only backup
bundle accepted by ADR-0033. Media backup, replication, retention, deployment
storage policy, and production host mutation are not introduced here.

## Consequences

- Publication can resume from a durable reservation, owned temporary target,
  verified final target, or pending quarantine cleanup without allocating a
  second target.
- Existing installations remain non-publishing until an operator explicitly
  selects a safe registered destination.
- Publication is intentionally POSIX-specific under the current adapter because
  the implementation requires a proven atomic no-replace primitive.
- Catalog creation and Gallery visibility require a later specialized decision
  and transaction.

## Related Documents

- [ADR index](README.md)
- [ADR-0033](0033-catalog-backup-and-recovery-foundation.md)
- [ADR-0037](0037-durable-upload-session-and-safe-ingest-foundation.md)
- [ADR-0038](0038-bounded-upload-media-validation.md)
- [ADR-0039](0039-lifecycle-owned-upload-validation-orchestration.md)
- [ADR-0040](0040-canonical-upload-byte-identity-foundation.md)
- [ADR-0041](0041-exact-byte-upload-duplicate-disposition.md)
