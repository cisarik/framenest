# ADR-0013: Initial Library Registry and Device-Local Root Locators

## Status

`Accepted`

## Decision Date

`2026-06-24`

## Decision Authority

The Orchestrator authorized this initial library-registry decision and test-first implementation through bounded task `FRAMENEST-CYCLE-042-LIBRARY-REGISTRY-CORE`.

## Context

FrameNest is local-first. A library is an independently registered collection root owned by one known device. Device registration exists through [ADR-0012](0012-initial-device-registry.md), but no library entity, root-locator model, or library persistence boundary existed.

Relevant existing decisions:

- [ADR-0010](0010-initial-persistence-foundation.md) accepts synchronous SQLAlchemy 2.x Core with Alembic for SQLite.
- [ADR-0011](0011-stable-domain-identities.md) accepts application-owned UUIDv4 `LibraryId` and `DeviceId` values.
- [ADR-0012](0012-initial-device-registry.md) implements the initial local device registry.

## Decision

### Library meaning

A library is an independently registered collection root owned by one known FrameNest device.

Library identity is independent of:

- its root path;
- its display name;
- database row position;
- a future storage-volume association;
- filesystem availability.

Changing a path later must not silently create a different library identity.

### Domain ownership

The domain owns:

- `Library`;
- `LibraryRoot`;
- `LibraryPathFlavor`;
- library display-name and root-locator invariants.

The application layer owns:

- `LibraryRepository`;
- repository behavior and sanitized repository errors.

Infrastructure owns:

- SQLAlchemy table definitions;
- canonical ID conversion;
- persistence statements;
- transaction execution;
- persistence-error translation.

Domain and application modules **MUST NOT** import SQLAlchemy, Alembic, FastAPI, Uvicorn, Pydantic, configuration, or infrastructure modules.

### Root-locator model

A library root is initially represented by:

- one explicit path flavor: `posix` or `windows`;
- one canonical absolute path string in that flavor.

The root locator is:

- device-local;
- paired with the owning `DeviceId`;
- not a globally stable identity;
- not portable durable sidecar metadata;
- not proof that the path currently exists;
- not a storage-volume identity.

The domain performs lexical validation only.

The domain **MUST NOT**:

- query the filesystem;
- resolve symlinks;
- test existence;
- test readability or writability;
- inspect mount points;
- infer a storage volume;
- normalize using the current host OS.

A later local registration adapter or CLI will convert and validate a real host path before constructing the domain value.

### Canonical lexical representation

For `posix`:

- use standard-library `PurePosixPath`;
- require an absolute path;
- reject `.` and `..` segments;
- require the input to equal its canonical `str(PurePosixPath(value))` representation.

For `windows`:

- use standard-library `PureWindowsPath`;
- require a fully absolute drive-rooted or UNC path;
- reject `.` and `..` segments;
- require the input to equal its canonical `str(PureWindowsPath(value))` representation.

For both:

- require an actual `str`;
- length must be 1 through 4096 Unicode code points;
- reject NUL, ASCII C0 control characters, and DEL;
- reject leading or trailing whitespace;
- do not lowercase, Unicode-normalize, case-fold, or resolve filesystem aliases;
- store the exact accepted canonical string.

Lexical equality is not a final cross-platform filesystem-equivalence algorithm.

### Database representation

Persist:

- `LibraryId` as canonical lowercase UUID text;
- owning `DeviceId` as canonical lowercase UUID text;
- path flavor as `posix` or `windows`;
- canonical root path as text;
- display name as text.

The combination `device_id + path_flavor + root_path` **MUST** be unique.

Display names are not unique.

### Repository boundary

The initial application repository port provides:

- add/register one library;
- retrieve by `LibraryId`;
- list all registered libraries.

Repository behavior:

- missing owning device raises `LibraryDeviceNotFoundError`;
- duplicate `LibraryId` raises `LibraryAlreadyExistsError`;
- duplicate root on the same device raises `LibraryRootAlreadyRegisteredError`;
- duplicate display names are allowed;
- `get()` returns `None` when absent;
- `list_all()` returns deterministic ordering by display name, owning device ID, path flavor, root path, and library ID.

Alembic revision `0003` creates the `libraries` table with foreign key `device_id -> devices.id` and `ON DELETE RESTRICT`.

## Deferred Scope

Explicitly deferred:

- filesystem existence and directory checks;
- permission checks;
- symlink resolution;
- removable-media detection;
- storage-volume association;
- mount discovery;
- online/offline and writable/read-only state;
- path updates or library moves;
- deletion;
- scanning;
- media records;
- sidecar placement;
- synchronization;
- API and CLI;
- platform-specific path-equivalence rules;
- case-sensitivity discovery;
- network-share credential handling.

## Implementation Boundary

The implementation authorized by this decision is limited to:

- pure-domain `Library`, `LibraryRoot`, and `LibraryPathFlavor`;
- application `LibraryRepository` port and repository errors;
- synchronous SQLAlchemy Core adapter;
- Alembic revision `0003`;
- focused tests and narrow documentation updates.

It does not create library CLI commands, HTTP routes, filesystem scanning, storage-volume records, or media schema.

## Artifact Lifecycle

Classification: durable normative architecture decision.

Consumers: future library CLI, scanner, catalog, and API tasks.

Discoverability: ADR index, [SPEC.md](../../SPEC.md), [ROADMAP.md](../../ROADMAP.md), and [AGENTS.md](../../AGENTS.md).

Retention: permanent until explicitly superseded by a later accepted ADR.

Cleanup owner: future explicitly authorized architecture task.

## Related Documents

- [ADR index](README.md)
- [ADR-0010](0010-initial-persistence-foundation.md)
- [ADR-0011](0011-stable-domain-identities.md)
- [ADR-0012](0012-initial-device-registry.md)
- [SPEC.md](../../SPEC.md)
- [ROADMAP.md](../../ROADMAP.md)
- [AGENTS.md](../../AGENTS.md)
