# ADR-0030: Automatic Processed Collection from Durable Tag Saves

## Status

`Accepted`

## Decision Date

`2026-06-26`

## Decision Authority

The Cooperator explicitly decided each logical medium may belong to at most one
collection, the first persisted collection is the built-in system workflow
collection `Processed`, and entry occurs automatically after the first
successful durable metadata save whose complete ordered tag list contains at
least one canonical tag.

## Context

FrameNest supports persistent display title, plain-text description, and
ordered canonical tags through the manual `Current` metadata workspace. A
Catalog browser provides display-title search and canonical-tag AND filtering.

The product direction expects media management workflows to distinguish media
that the user has explicitly reviewed and tagged from media that has only been
imported. This distinction is a built-in workflow concept, not an arbitrary
user-created collection in the initial implementation.

VLM submission, AI suggestion generation, and AI draft promotion alone must not
mark media as processed. Only a durable user-authorized metadata save with at
least one canonical tag creates the workflow transition.

### Key constraints

- All media remains visible in the virtual unfiltered Catalog scope.
- A medium enters Processed automatically; no manual collection picker exists.
- The important date is the durable tagging date, not filesystem or import time.
- No provider call, AI action, or media-byte inspection triggers the transition.
- No filesystem mutation occurs.

## Decision

### All-media scope

`All media` is a virtual Catalog scope. It is not stored as a collection.
Every logical medium remains visible there subject to ordinary Catalog filters
and pagination.

### Initial collection model

One logical medium may have zero or one persisted collection membership.

The initial implementation supports only the built-in system collection key
`processed`. No collection creation, rename, deletion, or arbitrary assignment
API is introduced. No collection selector appears in the manual metadata
workspace.

### Automatic transition

The complete ordered tag list after a successful metadata save determines the
transition:

| Previous state     | New complete tag list | Result                                               |
| ------------------ | --------------------- | ---------------------------------------------------- |
| no collection      | empty                 | remain outside Processed                             |
| no collection      | non-empty             | enter Processed; set `processed_at_ms = now_ms`      |
| processed          | non-empty             | remain Processed; preserve `processed_at_ms` exactly |
| processed          | empty                 | leave Processed; set `processed_at_ms = null`         |
| previously removed | later non-empty       | re-enter with a new `processed_at_ms = now_ms`       |

### Timestamp semantics

`processed_at_ms` is the FrameNest tagging/confirmation timestamp:

- it is not filesystem creation time;
- it is not filesystem modification time;
- it is not import time;
- it is not VLM request time;
- it is not provider response time;
- it is not physical rename time;
- it is not updated by title changes;
- it is not updated by description changes;
- it is not updated by non-empty-to-non-empty tag changes;
- it is cleared when all tags are removed;
- it is newly assigned if tags are added again later.

### Migration

Migration head becomes `0007`. A nullable `collection_key` column and a
nullable `processed_at_ms` column are added to `media_metadata`. Existing rows
upgrade with null collection state. No historical tagging timestamps are
fabricated. A composite index on `(collection_key, processed_at_ms, media_id)`
supports Processed filtering and ordering; it is not a covering index for the
catalog read query, which also selects display-title and timestamp columns that
are not present in the index.

### Privacy and AI boundary

No provider call is required. No AI action triggers the transition directly.
No media bytes are inspected. No filesystem mutation occurs.

## Rationale

The automatic transition eliminates a manual `Mark as processed` action while
preserving the principle that only a durable user-authorized save with explicit
tagging creates the workflow state. The single-collection scalar model avoids
a separate collection-membership table and general collection-management API
before the use cases for arbitrary collections are demonstrated.

## Consequences

### Positive

- Imported-but-untagged media is immediately distinguishable from reviewed media.
- The Processed scope uses oldest-first ordering, matching the review workflow.
- No new API endpoint or manual action is required for the initial workflow.
- The atomic metadata-save transaction prevents race conditions between
  metadata and collection state.
- The existing Catalog query architecture extends naturally with an optional
  collection filter.

### Costs and limitations

- Only one built-in collection exists. Arbitrary named collections are absent.
- Existing tagged media after migration remain unprocessed until their next
  save.
- No manual collection assignment, removal, or override exists.
- The scalar column model limits future collection membership to a single
  collection per medium without a migration.

## Deferred Scope

- arbitrary user-created collections;
- collection creation, rename, and deletion;
- multiple simultaneous collections per medium;
- manual collection assignment in the workspace;
- collection icons or covers;
- collection-specific permissions;
- drag-and-drop organization;
- physical folder mapping;
- filesystem moves;
- sidecar projection;
- native OS tag projection.

## Artifact Lifecycle

Classification: permanent normative architecture decision.

Consumers: future Orchestrator and Worker instances, domain implementers,
migration implementers, API implementers, catalog implementers, browser
workspace implementers.

Inbound references: ADR index.

Retention: until explicitly superseded.

Cleanup owner: only a future explicitly authorized task.

## Related Documents

- [ADR index](README.md)
- [ADR-0023](0023-manual-first-metadata-and-multi-model-ai-drafts.md)
- [ADR-0027](0027-persistent-display-title-and-canonical-tags.md)
- [ADR-0028](0028-catalog-read-model-and-search-semantics.md)
- [ADR-0029](0029-persistent-plain-text-media-description.md)
- [SPEC.md](../../SPEC.md)
- [ROADMAP.md](../../ROADMAP.md)
