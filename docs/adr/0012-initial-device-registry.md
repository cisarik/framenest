# ADR-0012: Initial Device Registry and Repository Boundary

## Status

`Accepted`

## Decision Date

`2026-06-24`

## Decision Authority

The Orchestrator authorized this initial device-registry decision and test-first implementation through bounded task `FRAMENEST-CYCLE-040-DEVICE-REGISTRY-CORE`.

## Context

FrameNest is local-first. A machine or storage-capable host known to FrameNest must be representable before libraries, storage volumes, physical media locations, or logical media can be registered safely.

Relevant existing decisions:

- [ADR-0010](0010-initial-persistence-foundation.md) accepts synchronous SQLAlchemy 2.x Core with Alembic for SQLite and defers product schema.
- [ADR-0011](0011-stable-domain-identities.md) accepts application-owned UUIDv4 `DeviceId` values with canonical lowercase hyphenated text representation.

The persistence foundation previously contained only Alembic version tracking through revision `0001`. No product catalog tables existed.

## Decision

### Purpose

The device registry is the first real local catalog slice.

A device represents a machine or storage-capable host known to FrameNest.

This decision creates only enough behavior to register, retrieve, and list device records locally.

### Domain ownership

The domain owns:

- `Device`;
- `DeviceId`;
- device display-name invariants.

The application layer owns:

- the `DeviceRepository` port;
- repository-level errors and behavior contracts.

The infrastructure layer owns:

- SQLAlchemy table definitions;
- canonical UUID text conversion;
- SQLite statements;
- transaction execution;
- SQLAlchemy-specific error translation.

Domain and application modules **MUST NOT** import SQLAlchemy, Alembic, FastAPI, Uvicorn, Pydantic, or persistence modules.

### Identity persistence

For the initial `devices` table:

- `DeviceId` is persisted as canonical lowercase hyphenated UUID text;
- the stored value is exactly `DeviceId.to_string()`;
- values read from the database are reconstructed using strict `DeviceId.from_string()`;
- SQLite row IDs or integer surrogate IDs **MUST NOT** become FrameNest device identity;
- this decision applies only to the initial `devices` table;
- broader UUID storage decisions for future tables may be revisited by a later ADR without invalidating stored canonical UUID strings.

### Repository boundary

The initial application repository port provides:

- add/register one device;
- retrieve by `DeviceId`;
- list all registered devices.

The repository **MUST NOT** expose:

- SQLAlchemy `Engine`;
- SQLAlchemy `Connection`;
- SQLAlchemy rows;
- SQL strings;
- database paths;
- raw SQLite exceptions.

Repository behavior:

- `add()` persists one valid `Device`;
- duplicate `DeviceId` raises `DeviceAlreadyExistsError`;
- duplicate display names are allowed;
- `get()` returns `None` when the ID is absent;
- `list_all()` returns all valid devices in deterministic order by:
  1. `display_name.casefold()`;
  2. original `display_name`;
  3. canonical `DeviceId` string as tie-breaker.

This ordering is an initial deterministic repository contract, not semantic ordering of identities and not a future full-text search decision.

### Database schema

Alembic revision `0002` creates exactly one product table: `devices`.

Required columns:

- `id`: SQLite text, primary key, non-null, canonical `DeviceId` representation;
- `display_name`: SQLite text, non-null.

Required constraints:

- primary key on `id`;
- check that `id` length is exactly 36;
- check that `display_name` length is between 1 and 120 inclusive.

`display_name` is not unique.

The migration remains upgrade-only per [ADR-0010](0010-initial-persistence-foundation.md).

Normal `framenest-server` startup remains migration-free.

## Consequences

### Positive

- Establishes the first genuine local catalog vertical slice.
- Preserves domain and application independence from persistence frameworks.
- Provides a tested repository boundary for future device CLI and API work.
- Accepts canonical UUID text storage for the initial device table without blocking later storage-format decisions for other tables.

### Negative

- Device records have no availability, hostname, operating-system, or audit metadata yet.
- No update, rename, or delete workflows exist yet.
- Repository ordering is repository-contract ordering, not user-facing search ordering.

## Deferred Scope

Explicitly deferred:

- automatic current-host detection;
- hostname or hardware fingerprinting;
- device authentication;
- network identity;
- device availability or last-seen tracking;
- device kind or operating-system enum;
- device update and rename workflows;
- device deletion;
- libraries;
- storage volumes;
- media locations;
- logical media;
- synchronization;
- server aggregation;
- HTTP API;
- CLI;
- timestamps and audit history;
- soft deletion;
- multi-user ownership.

## Implementation Boundary

The implementation authorized by this decision is limited to:

- pure-domain `Device` entity and display-name validation;
- application `DeviceRepository` port and repository errors;
- synchronous SQLAlchemy Core adapter;
- Alembic revision `0002`;
- focused tests and narrow documentation updates.

It does not create HTTP routes, CLI commands, library registration, scanning, media schema, or synchronization behavior.

## Artifact Lifecycle

Classification: durable normative architecture decision.

Consumers: future domain, catalog, library, scanner, and API tasks.

Discoverability: ADR index, [SPEC.md](../../SPEC.md), [ROADMAP.md](../../ROADMAP.md), and [AGENTS.md](../../AGENTS.md).

Retention: permanent until explicitly superseded by a later accepted ADR.

Cleanup owner: future explicitly authorized architecture task.

## Related Documents

- [ADR index](README.md)
- [ADR-0010](0010-initial-persistence-foundation.md)
- [ADR-0011](0011-stable-domain-identities.md)
- [SPEC.md](../../SPEC.md)
- [ROADMAP.md](../../ROADMAP.md)
- [AGENTS.md](../../AGENTS.md)
