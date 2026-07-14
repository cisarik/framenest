# ADR-0037: Durable Upload Session and Safe Ingest Foundation

## Status

`Accepted`

## Decision Date

2026-07-14

## Context

FrameNest is moving toward server-managed media upload and ingest while
remaining local-first and loopback-first by default. ADR-0035 established that
the FrameNest server process is authoritative for upload and ingest state, but
it did not define the durable state model needed before transport, quarantine,
publication, cataloging, or AI analysis work.

Large media cannot rely on raw multipart upload alone as the durable model. A
single request can fail late, be retried ambiguously, and lacks a stable
server-owned offset and reconciliation boundary for later resumable transport.
Future chunks need the same state model as a first small-file transfer.

The current trusted loopback development boundary may be sufficient for an MVP
upload endpoint, but it is not completed authentication or authorization.

## Decision

FrameNest will use FrameNest-owned durable upload sessions as the architecture
for future media upload and safe ingest.

The first transport uses a FrameNest-owned offset protocol:

```text
POST /api/uploads
PATCH /api/uploads/{upload_id}
GET /api/uploads/{upload_id}
POST /api/uploads/{upload_id}/complete
DELETE /api/uploads/{upload_id}
```

`PATCH` requests use `application/offset+octet-stream`, `Upload-Offset`, and
`Content-Length`. Request bytes are streamed into quarantine incrementally and
the durable offset is advanced only after the intended bytes are flushed and
fsynced. The client never selects session identity, storage identity, or a
server path.

`tus` is a useful design reference and possible future compatibility target.
FrameNest will not add a tus server, sidecar, tus dependency, or external upload
service as the first implementation dependency.

Upload, ingest publication, cataloging, and AI analysis are separate stages:

- upload session state records byte receipt and ingest readiness;
- publication moves a verified server-owned object across the durable storage
  boundary;
- cataloging creates Gallery-visible catalog records;
- AI analysis remains an explicit later request after successful publication.

Upload-session byte progress is state-specific. A `created` session has zero
received bytes. `received` and every validation, duplicate-review,
publication, published, cataloged, and rejected state require
`received_size_bytes` to equal `declared_size_bytes`. Partial uploads may remain
in receiving, cancelled, expired, or failed states, but they cannot advance into
validation, publication, or catalog-ready states. FrameNest enforces this
invariant in the pure domain model, atomic repository state-transition guards,
and the SQLite schema.

Clients do not provide server filesystem paths. The server generates opaque
storage keys and selects any eventual storage location. Display filenames are
metadata only and are never interpreted as storage paths.

Quarantine storage is optional configuration. When it is absent or unsafe, the
upload API fails closed. When configured, quarantine storage must be a
pre-existing absolute non-symlink directory outside served roots, outside
registered library roots, and outside the preview cache root. A quarantined
object is not Gallery-visible and is not available to provider-backed analysis.

The planned duplicate identity is SHA-256 plus exact byte size. That later
identity is sufficient for first duplicate review but does not decide
publication, deduplication UI, or catalog merge policy by itself.

Filesystem mutation and SQLite mutation are not one atomic transaction.
`published` is therefore a durable reconciliation boundary before `cataloged`.
Once publication succeeds, a later cataloging failure must not be collapsed into
a pre-publication failed upload. No Gallery visibility exists before cataloging.

The quarantine transport uses an explicit file/database recovery policy. If a
staged file is ahead of the persisted offset after a crash, unacknowledged bytes
are truncated before accepting more data. If the file is behind the persisted
offset, FrameNest fails closed and marks the session failed when the existing
transition graph allows it. Disconnects, write failures, and repository
conflicts roll the staged file back to the authoritative offset before returning
a sanitized error.

Current production configuration uses one Uvicorn worker. This slice serializes
same-session upload writers with an in-process per-session lock while leaving
unrelated sessions independent. Multi-process concurrent upload writers are not
enabled by this decision and require a later interprocess locking decision.

Browser-origin protection is bounded to current non-proxied loopback behavior:
mutation requests with no `Origin` header are accepted for trusted local clients,
and browser requests with an `Origin` header must match the effective same
origin. This is not authentication or authorization.

Provider access is forbidden before successful publication and an explicit
analysis request.

## Staged Implementation Sequence

1. Add the durable upload-session schema, domain state machine, and SQLite
   repository.
2. Add resumable streamed transport into quarantine through the same offset
   guard.
3. Add checksum calculation and duplicate review.
4. Add duplicate review UX and publication staging.
5. Add catalog creation from published objects.
6. Add reconciliation for `published` records not yet `cataloged`.
7. Add optional tus alignment if needed.

## Consequences

### Positive

- Future resumable upload can reuse the initial schema and state model.
- Upload and AI analysis remain separate authority boundaries.
- Clients never gain arbitrary server path selection.
- Publication and catalog reconciliation have an explicit durable boundary.
- Loopback MVP behavior is not confused with completed authentication.

### Costs And Limitations

- The upload transport stops at the durable `received` boundary.
- Scheduled abandoned-upload cleanup is deferred.
- Duplicate review needs later product and UI decisions.
- Authentication and authorization remain unresolved.

## Rejected Alternatives

### Raw Multipart As The Durable Model

Rejected because it does not provide durable offset, retry, concurrency, or
resumability semantics for large media.

### Client-Provided Server Paths

Rejected because clients must not choose arbitrary server filesystem
destinations or encode placement policy.

### tus As The First Dependency

Rejected for the first slice. tus remains a reference and possible future
compatibility target, but FrameNest needs its own durable domain boundary first.

### Immediate Catalog Visibility

Rejected. Gallery visibility begins only after successful cataloging.

## Deferred Work

This ADR does not implement or decide:

- browser upload UI;
- multipart parsing;
- checksum calculation from files;
- duplicate review UX;
- publication mechanics;
- catalog insertion;
- reconciliation execution;
- cleanup policy;
- authentication or authorization;
- tus compatibility;
- AI analysis workflows.

## Security Consequences

The trusted loopback MVP boundary is only an initial deployment assumption, not
completed authentication or authorization. No router port forwarding is implied.
Remote access remains Tailscale-only unless superseded by a later accepted
decision, and Tailscale membership is not application administrator authority.

No provider receives upload bytes or derived media before successful
publication and an explicit analysis request. No credentials, private media
paths, production addresses, storage roots, or host-specific secret material are
recorded by this ADR.

## Related Documents

- [ADR index](README.md)
- [ADR-0035](0035-authoritative-server-and-client-state-model.md)
- [SERVER.md](../../SERVER.md)
- [SECURITY.md](../../SECURITY.md)
- [SPEC.md](../../SPEC.md)
