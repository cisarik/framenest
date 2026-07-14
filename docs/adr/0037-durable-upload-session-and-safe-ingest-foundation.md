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

The first small transfer may be a single request, but it must behave as one
offset-checked session write. Later streamed and resumable transports will use
the same durable session identity, offset, state, and concurrency guards.

`tus` is a useful design reference and possible future compatibility target.
FrameNest will not add a tus server, sidecar, tus dependency, or external upload
service as the first implementation dependency.

Upload, ingest publication, cataloging, and AI analysis are separate stages:

- upload session state records byte receipt and ingest readiness;
- publication moves a verified server-owned object across the durable storage
  boundary;
- cataloging creates Gallery-visible catalog records;
- AI analysis remains an explicit later request after successful publication.

Clients do not provide server filesystem paths. The server generates opaque
storage keys and selects any eventual storage location. Display filenames are
metadata only and are never interpreted as storage paths.

Future quarantine storage must be outside served roots and outside authoritative
media roots. A quarantined object is not Gallery-visible and is not available
to provider-backed analysis.

The initial duplicate identity is SHA-256 plus exact byte size. This identity
is sufficient for first duplicate review but does not decide publication,
deduplication UI, or catalog merge policy by itself.

Filesystem mutation and SQLite mutation are not one atomic transaction.
`published` is therefore a durable reconciliation boundary before `cataloged`.
Once publication succeeds, a later cataloging failure must not be collapsed into
a pre-publication failed upload. No Gallery visibility exists before cataloging.

Provider access is forbidden before successful publication and an explicit
analysis request.

## Staged Implementation Sequence

1. Add the durable upload-session schema, domain state machine, and SQLite
   repository.
2. Add streamed small-file transport that writes through the same offset guard.
3. Add quarantine filesystem storage and checksum calculation.
4. Add duplicate review and publication staging.
5. Add catalog creation from published objects.
6. Add reconciliation for `published` records not yet `cataloged`.
7. Add resumable transport compatibility and optional tus alignment if needed.

## Consequences

### Positive

- Future resumable upload can reuse the initial schema and state model.
- Upload and AI analysis remain separate authority boundaries.
- Clients never gain arbitrary server path selection.
- Publication and catalog reconciliation have an explicit durable boundary.
- Loopback MVP behavior is not confused with completed authentication.

### Costs And Limitations

- The first slice stores upload-session state before any transport exists.
- Filesystem cleanup and reconciliation are deferred.
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

- HTTP upload routes;
- multipart parsing;
- streaming or chunk transport;
- quarantine directory layout;
- filesystem writes;
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
