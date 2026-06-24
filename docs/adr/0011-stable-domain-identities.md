# ADR-0011: Stable Domain Identities

## Status

`Accepted`

## Decision Date

`2026-06-24`

## Decision Authority

The Orchestrator authorized this stable identity decision and test-first implementation through bounded task `FRAMENEST-CYCLE-037-STABLE-DOMAIN-IDENTITIES`. Transient primary-source evidence was consumed directly into this ADR without creating a committed research artifact.

## Context

FrameNest is local-first and must eventually represent media across multiple devices, libraries, storage volumes, and physical locations. A logical media item is not the same thing as one stored file path. A library, device, storage volume, series, logical media record, and physical media location each need stable identity before a safe media catalog schema, sidecar format, repository interface, or synchronization protocol can be designed.

The current persistence foundation deliberately contains no media catalog schema. Database rows, SQLite row order, filenames, filesystem paths, content hashes, source-platform identifiers, and device-local counters are each useful evidence or implementation detail in some contexts, but none is sufficient as the initial FrameNest entity identity mechanism.

Relevant existing decisions:

- [ADR-0001](0001-supported-python-version.md) fixes the runtime at CPython 3.13.
- [ADR-0003](0003-initial-server-api-framework.md) keeps domain behavior independent of FastAPI.
- [ADR-0004](0004-repository-layout.md) establishes the staged `src/framenest/` layout.
- [ADR-0010](0010-initial-persistence-foundation.md) accepts SQLAlchemy Core and Alembic for the SQLite persistence foundation, while deferring stable identity format and catalog schema.

## Decision

FrameNest **MUST** use application-owned RFC 9562 UUID version 4 identifiers as the initial stable identity format for:

- logical media identity;
- physical media-location identity;
- device identity;
- library identity;
- storage-volume identity;
- series identity.

Identity generation **MUST** use the Python 3.13 standard-library `uuid.uuid4()` function.

Stable identities **MUST** be:

- independent of database row IDs and SQLite row order;
- independent of filesystem paths and filenames;
- independent of content hashes;
- independent of source-platform IDs;
- independent of device-local counters;
- opaque to domain consumers;
- represented externally by canonical lowercase hyphenated UUID text;
- separated by entity category at the Python type level.

The initial public domain API uses explicit category-specific value objects:

```python
media_id = MediaId.new()
serialized = media_id.to_string()
restored = MediaId.from_string(serialized)
```

`str(identity)` returns the same canonical serialized representation. Parsing accepts only canonical lowercase hyphenated UUIDv4 text and rejects non-canonical forms rather than silently normalizing them.

## Rationale

Local-first and future multi-device operation require identifiers that can be minted without a central service, survive local database rebuilds, and remain meaningful when a media record is observed on another device or in a future sidecar manifest. RFC 9562 defines UUIDs as 128-bit identifiers that can be generated without central registration and discusses their practical use for distributed systems and database keys. UUIDv4 gives FrameNest a simple globally practical identity mechanism before synchronization, sidecars, and catalog schema exist.

Filesystem paths are mutable location evidence. Files can be renamed, moved between libraries, copied to another storage volume, or temporarily unavailable while the logical media item remains the same. A physical location itself needs identity distinct from its path because future verification, availability, and migration state may outlive a specific path string.

Database row IDs are local persistence implementation details. They are useful inside one SQLite database, but they must not become cross-device, sidecar, or durable domain identity. Treating row order or autoincrement values as stable identity would make rebuilds, imports, and future synchronization brittle.

Content hashes describe content evidence and may later support verification, duplicate detection, or fingerprinting. They do not identify every domain entity. A library, device, storage volume, series, and physical location are not content blobs, and even media identity may need to distinguish provenance, edits, metadata decisions, or intentional duplicates.

Source-platform IDs are provider-scoped metadata. A YouTube identifier, downloader archive key, local filename, or future source adapter ID can support provenance and reconciliation, but it is not FrameNest-owned identity and may be absent, reused in another namespace, corrected, or unavailable for local imports.

UUIDv4 is selected because it is simple, opaque, dependency-free under Python 3.13, and does not require filesystem, database, platform, clock, or provider input. Python 3.13 documents `uuid.uuid4()` as random UUID generation and `str(uuid)` as the standard hyphenated text form. Python's `UUID.hex` is lowercase, and the canonical `str()` output is stable for roundtrip.

Different entity categories require distinct Python types so accidental interchange is caught at runtime and can be caught by future static checks. A `MediaId` and `LibraryId` wrapping the same UUID text are not the same domain value.

## Rejected Alternatives

### Filesystem paths or filenames

Rejected because paths are mutable evidence of location, not stable entity identity. They change during renames, moves, storage migration, library reorganization, or user correction.

### Database row IDs

Rejected because row IDs are scoped to one database and one migration history. FrameNest identities must remain stable across rebuilds, sidecars, future imports, and multi-device workflows.

### Content-hash-only identity

Rejected as the general identity mechanism because hashes describe content evidence, not all domain identity. Content fingerprinting and duplicate detection remain future features.

### Source-platform IDs

Rejected because they are provider-scoped metadata and may not exist for local media or future imports. They are useful provenance, not FrameNest-owned identity.

### Device-local counters

Rejected because they require additional device identity, conflict handling, and synchronization rules before they can be safely interpreted outside one local process or database.

### UUIDv1

Rejected because it embeds time and node characteristics. Python 3.13 also warns that `uuid1()` may compromise privacy by including the computer network address.

### UUIDv3 and UUIDv5

Rejected as the general mechanism because normal FrameNest entity creation is not name-derived. RFC 9562 defines these as namespace/name hash-based layouts, which are appropriate only when the name and namespace are the identity source.

### UUIDv6 and UUIDv7

Deferred rather than implemented manually or through a new dependency. RFC 9562 defines time-ordered UUID versions with database-index locality advantages, but Python 3.13's standard `uuid` API does not provide UUIDv6 or UUIDv7 generation. Ordered database representation remains a separate persistence decision.

### Public generic identity alias

Rejected because a public generic identity type or `typing.NewType` alone would weaken runtime entity-category separation. FrameNest needs concrete runtime types for each identity category.

## Consequences

### Positive

- Domain entities can receive stable application-owned identifiers before catalog schema design.
- Identity generation remains dependency-free under CPython 3.13.
- Domain code stays independent from FastAPI, Pydantic, SQLAlchemy, Alembic, Uvicorn, settings, persistence, filesystem, and network boundaries.
- Canonical external text works for future APIs, sidecars, logs after redaction review, and manual inspection.
- Category-specific types prevent accidental equality between unrelated entity identities.

### Costs and risks

- UUIDv4 values are not semantically ordered and must not be used for creation-time ordering.
- Random UUIDv4 values have weaker database-index locality than time-ordered UUID versions.
- Storage representation remains undecided, so future persistence schema work must choose text or 16-byte storage deliberately.
- Collision handling policy is not yet designed, although UUIDv4 collision probability is acceptable for this initial non-safety-critical local library foundation.

### Mitigations

- Treat identity strings as opaque.
- Add tests for strict parsing, UUID version, variant, category separation, immutability, collection behavior, and import boundaries.
- Defer database storage, indexing, synchronization, and conflict handling to bounded future decisions.

## Deferred Decisions

This ADR does **NOT** decide:

- final SQLite column representation;
- text versus 16-byte database storage;
- database indexes;
- catalog schema;
- repository interfaces;
- sidecar representation and versioning;
- synchronization wire format;
- duplicate detection;
- content fingerprinting;
- import identity reconciliation;
- identity conflict handling;
- aggregate-server behavior;
- migration from a future superseding identity-generation strategy.

## Implementation Boundary

The implementation authorized by this decision is limited to immutable, dependency-free domain identity value objects and focused tests. It does not create media catalog tables, migration revision `0002`, repositories, services, HTTP endpoints, sidecars, scanners, hashing, synchronization, or catalog entities beyond the six identity types.

## Artifact Lifecycle

Classification: durable normative architecture decision.

Consumers: ORCHESTRATOR, future WORKER sessions, domain implementation, persistence schema design, sidecar design, and synchronization design.

Discoverability: ADR index, [SPEC.md](../../SPEC.md) stable identity requirements, [ROADMAP.md](../../ROADMAP.md), and [AGENTS.md](../../AGENTS.md) current-state summary.

Retention: permanent until explicitly superseded by a later accepted ADR.

Cleanup owner: a future explicitly authorized architecture-decision task.

## Primary Sources

Research retrieval date: **2026-06-24**.

| Topic | Source |
|---|---|
| RFC 9562 UUID specification | https://www.rfc-editor.org/rfc/rfc9562.html |
| RFC 9562 UUIDv4 layout and UUID best practices | https://www.rfc-editor.org/rfc/rfc9562.html#section-5.4 |
| Python 3.13 `uuid` module | https://docs.python.org/3.13/library/uuid.html |

## Related Documents

- [ADR index](README.md)
- [ADR-0001](0001-supported-python-version.md)
- [ADR-0003](0003-initial-server-api-framework.md)
- [ADR-0004](0004-repository-layout.md)
- [ADR-0010](0010-initial-persistence-foundation.md)
- [SPEC.md](../../SPEC.md)
- [ROADMAP.md](../../ROADMAP.md)
- [AGENTS.md](../../AGENTS.md)
