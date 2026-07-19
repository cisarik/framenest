# ADR-0043: Published-to-Cataloged Upload Transaction

## Status

`Accepted`

## Decision Date

2026-07-19

## Context

Atomic publication ([ADR-0042](0042-atomic-upload-publication.md)) can leave an
upload in durable `published` with verified server-owned bytes and completed
quarantine cleanup. That state must not imply Gallery visibility. Gallery lists
logical media and physical locations only. Until a specialized catalog
transaction exists, published uploads remain invisible to clients that browse
`GET /api/media`.

Synchronous catalog creation inside the original upload HTTP request is not
viable: publication already runs through a lifecycle-owned coordinator outside
that request. Introducing a new asynchronous job queue, Redis, Celery, or
multiprocess fencing would add infrastructure that FrameNest does not require
for the current single-process trusted-loopback topology.

## Decision

FrameNest accepts a persisted intermediate `published` state followed by a
lifecycle-owned, retryable, idempotent `published -> cataloged` transition.

Migration `0014` adds nullable `media_id` and `media_location_id` on
`upload_publications`, constrained so both are null or both are non-null,
unique when non-null, and restrictively referenced to catalog tables. Existing
rows remain valid with null links. No historical ownership is invented.

A specialized repository transaction
(`commit_cataloged_publication`) alone may:

1. require `published`, verified publication, complete cleanup, and absent links;
2. create exactly one logical media item and one physical location;
3. store both catalog identities on the publication row;
4. transition the upload session to `cataloged`;
5. commit those database changes atomically.

Generic upload state transitions still cannot move `published -> cataloged`.

Application service `CatalogPublishedUpload` and coordinator
`UploadCatalogCoordinator` discover eligible published uploads, wake after
successful publication cleanup, reconcile at startup, prevent duplicate
in-process work through the shared per-upload lock, treat a completed matching
transition as idempotent success, leave failures truthfully `published` for
retry, and shut down cleanly with the application.

On catalog persistence failure, every database write from the catalog
transaction rolls back. The durable published file remains untouched. No false
`cataloged` success is exposed.

Gallery eligibility begins only after successful `cataloged`. Upload API
responses may include an opaque public `media_id` only in that state and must
not expose storage paths, publication identities, destinations, checksums, or
cleanup internals.

## Authorization Boundary

The current product remains a trusted-loopback single-tenant service without
per-user ownership columns. This decision does not invent `owner_id`, users,
sessions, or ACLs. Catalog visibility for cataloged uploads matches existing
scan-imported media under the same loopback boundary. Multi-user authorization
is deferred.

## Rejected Alternatives

- Synchronous cataloging inside the upload HTTP request: publication is not on
  that path and would couple byte receipt to catalog durability incorrectly.
- A new async job queue or external worker system: overkill for the current
  single-process coordinator model and out of MVP scope.
- Deleting a successfully published file when catalog persistence fails: would
  destroy durable publication truth and violate the publication/catalog
  boundary.

## Consequences

- `published` remains a truthful intermediate state.
- Catalog creation is lifecycle-owned and retryable without a queue.
- Gallery and content routes continue to use identity-only catalog records.
- AI analysis, tags beyond existing catalog invariants, thumbnails,
  transcoding, backup of media bytes, multiprocess fencing, deployment, and
  multi-user ownership remain out of scope for this decision.

## Deferred Work

- Multi-user ownership and authorization.
- AI analysis or re-analysis of newly cataloged uploads.
- Thumbnails, previews beyond existing on-demand mechanisms, and transcoding.
- Media-byte backup and remote replication.
- Multiprocess leases or fencing if multiple writers are later accepted.
