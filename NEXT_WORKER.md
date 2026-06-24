# Next Worker Handoff

## 1. Purpose and authority

This file is a non-authoritative Worker-session handoff. It is state-restoration evidence only. It is not a task and grants no modification, dependency, command, architecture, migration, or Git authority.

A fresh Worker requires one separate authoritative Orchestrator prompt before doing any work. The Cooperator normally does not paste this file manually. A fresh Worker reads it directly from the repository during bootstrap.

Repository state and the new authoritative task override stale handoff claims.

Current WORKER session: CLOSED.

## 2. Repository identity

- Repository: `https://github.com/cisarik/framenest.git`
- Local path used by the closing Worker: `/Users/agile/framenest`
- Branch: `main`
- Pre-handoff public HEAD: `b90b680b382dded53d53c046b816c0b77e85eb2d`
- Pre-handoff subject: `feat: add library catalog CLI`
- Pre-handoff parent: `8d800e83c59d975aaf6a466c9359121af583afcf`

A fresh Worker must independently resolve final post-handoff local `HEAD`, local `origin/main`, remote `main`, and the final handoff commit subject and parent. Do not infer the post-handoff SHA from this file.

## 3. Toolchain and dependency state

- Runtime constraint: CPython `>=3.13,<3.14`
- Observed project interpreter: CPython `3.13.14` in `.venv/`
- Observed Poetry version: `2.1.4`
- Poetry remains the dependency, environment, and lockfile authority
- `uv` remains the accepted Apple Silicon macOS CPython interpreter provider through [ADR-0006](docs/adr/0006-macos-python-interpreter-provider.md)

Direct runtime dependency constraints in `pyproject.toml`:

- `pydantic-settings (>=2.14.2,<3.0.0)`
- `fastapi (>=0.138.0,<0.139.0)`
- `uvicorn (>=0.49.0,<0.50.0)`
- `sqlalchemy (>=2.0.51,<2.1.0)`
- `alembic (>=1.18.4,<1.19.0)`

Direct development dependency constraints:

- `pytest = ^9.1.1`
- `httpx2 = ^2.4.0`

Relevant locked versions observed at closeout:

- `alembic 1.18.4`
- `fastapi 0.138.0`
- `greenlet 3.5.2`
- `httpx2 2.4.0`
- `mako 1.3.12`
- `pydantic 2.13.4`
- `pydantic-settings 2.14.2`
- `pytest 9.1.1`
- `sqlalchemy 2.0.51`
- `starlette 1.3.1`
- `uvicorn 0.49.0`

Console entrypoints:

- `framenest-server = "framenest.server:main"`
- `framenest-db = "framenest.infrastructure.persistence.cli:main"`
- `framenest-catalog = "framenest.adapters.cli.catalog:main"`

SQLAlchemy and Alembic are installed and active. SQLAlchemy ORM mapped entities, SQLModel, `aiosqlite`, and SQLAlchemy async engines or sessions are not accepted or implemented. No dependency change occurred in cycles 040 through 043.

## 4. Current implemented foundation

The repository currently implements:

- a root Poetry package with `src/framenest/`
- centralized `pydantic-settings` configuration in `src/framenest/configuration.py`
- loopback-safe defaults through `FRAMENEST_HOST` and `FRAMENEST_PORT`
- a temporary development database path setting through `FRAMENEST_DATABASE_PATH`
- a FastAPI application factory in `src/framenest/adapters/api/application.py`
- typed `GET /health`
- a loopback-first Uvicorn runtime in `src/framenest/server.py`
- console script `poetry run framenest-server`
- single-worker, no-reload, no-proxy-trust runtime defaults
- FrameNest-owned structured JSON logging and redaction in `src/framenest/structured_logging.py`
- explicit Uvicorn `log_config` integration
- Uvicorn access logging disabled
- process-output and shutdown contracts for the direct FrameNest server process
- a synchronous SQLAlchemy Core SQLite persistence boundary in `src/framenest/infrastructure/persistence/`
- `sqlite+pysqlite` engine creation with explicit foreign-key enablement
- bounded busy handling and explicit transaction helper behavior
- deterministic engine disposal boundary
- sanitized FrameNest-owned persistence and migration error types
- packaged Alembic migration resources
- explicit database commands `poetry run framenest-db status` and `poetry run framenest-db migrate`
- deterministic machine-readable database command output
- no automatic migration during normal server startup
- packaged migrations through revision `0003`

## 5. Migration and schema state

### Revision `0001`

- persistence foundation only
- no product table

### Revision `0002`

- creates `devices`
- canonical UUID-text primary key
- non-null display name
- accepted Device Registry boundary per [ADR-0012](docs/adr/0012-initial-device-registry.md)

### Revision `0003`

- creates `libraries`
- foreign key to `devices` with non-cascading delete restriction
- canonical UUID-text `LibraryId` and `DeviceId`
- display name
- explicit path flavor (`posix` or `windows`)
- canonical root path text
- unique `(device_id, path_flavor, root_path)` boundary per [ADR-0013](docs/adr/0013-initial-library-registry.md)

There is no revision `0004`. There is no media table, storage-volume table, physical-media-location table, tag table, series table, or sidecar table. Migrations remain explicit and upgrade-only. Normal server startup and catalog commands do not migrate automatically.

## 6. Stable identities and domain model

[ADR-0011](docs/adr/0011-stable-domain-identities.md) is Accepted and implemented.

Identity types:

- `MediaId`
- `MediaLocationId`
- `DeviceId`
- `LibraryId`
- `StorageVolumeId`
- `SeriesId`

Identity behavior:

- application-owned RFC 9562 UUID version 4 values
- generation through Python standard-library `uuid.uuid4()`
- canonical external text as lowercase hyphenated UUID strings
- strict parsing that rejects non-canonical forms
- immutable frozen and slotted value objects
- runtime category separation between identity classes
- runtime type, UUID variant, and UUIDv4 enforcement on normal constructor paths
- FrameNest-owned sanitized validation errors
- no FastAPI, Pydantic, SQLAlchemy, Alembic, Uvicorn, settings, filesystem, persistence, or network imports in the domain identity module

### Device

Implemented in `src/framenest/domain/devices.py`:

- `Device` with `DeviceId` and display name
- immutable entity
- display-name invariants enforced in domain
- no hostname detection, availability, authentication, update, rename, or deletion

### Library

Implemented in `src/framenest/domain/libraries.py`:

- `Library` with `LibraryId`, owning `DeviceId`, display name, and `LibraryRoot`
- `LibraryPathFlavor.POSIX` and `LibraryPathFlavor.WINDOWS`
- canonical lexical absolute path in the declared flavor
- device-local root locator, not a storage-volume identity
- no filesystem I/O in domain
- no scan state or storage-volume association

## 7. Application and persistence boundaries

### Device repository

- application port: `src/framenest/application/ports/device_repository.py`
- operations: add, get, list_all
- deterministic ordering by display name and `DeviceId`
- duplicate `DeviceId` handling
- synchronous SQLAlchemy Core adapter: `src/framenest/infrastructure/persistence/device_repository.py`
- sanitized repository errors

### Library repository

- application port: `src/framenest/application/ports/library_repository.py`
- operations: add, get, list_all
- owner-device validation before insert
- duplicate `LibraryId` and duplicate same-device root handling
- deterministic ordering by display name, owning device, path flavor, root path, and `LibraryId`
- synchronous SQLAlchemy Core adapter: `src/framenest/infrastructure/persistence/library_repository.py`
- sanitized repository errors

Boundaries:

- application ports expose no SQLAlchemy objects
- domain and application do not import infrastructure
- no generic repository framework
- no Unit of Work abstraction
- no ORM

## 8. Current operator CLI

### Database

```text
poetry run framenest-db status
poetry run framenest-db migrate
```

### Devices

```text
poetry run framenest-catalog device register --display-name NAME
poetry run framenest-catalog device get --id DEVICE_ID
poetry run framenest-catalog device list
```

### Libraries

```text
poetry run framenest-catalog library register \
  --device-id DEVICE_ID \
  --display-name NAME \
  --root PATH

poetry run framenest-catalog library get --id LIBRARY_ID
poetry run framenest-catalog library list
```

Catalog CLI behavior:

- one compact JSON object per non-help invocation
- success on stdout, errors on stderr
- stable exit and error contracts
- strict identity parsing
- catalog database must already be at packaged migration head
- catalog CLI never migrates
- library registration requires an existing owning device
- local root is expanded and converted to a native canonical absolute lexical path in `src/framenest/adapters/cli/library_root.py`
- root must exist and be a directory
- relative paths and `~` are accepted by the CLI adapter
- symlink target resolution is intentionally not performed
- directory contents are not enumerated
- registration does not scan files
- these commands are development/operator boundaries, not final desktop UX

## 9. Current test evidence

Observed by the closing Worker before replacing this handoff:

- `poetry run pytest --collect-only -q`: `401 tests collected`
- `poetry run pytest -q`: `401 passed`
- `poetry run pytest -q -W error`: `401 passed`
- zero observed pytest warnings
- `poetry check --lock`: passed

These are Worker-observed dynamic results. Every future Worker must rerun its own baseline from the final public commit it receives.

Test tree structure:

- `tests/contract/`: health API, server process output, Uvicorn runtime/logging, persistence CLI, persistence package resources, catalog CLI
- `tests/integration/`: persistence migrations; persistence device/library repository and migration tests
- `tests/unit/`: configuration, import boundaries, API boundaries, persistence engine/boundaries, server runtime, structured logging, package import; domain identity/device/library tests; application repository-port tests; catalog library-root helper tests

## 10. Accepted ADR package

- [ADR-0001](docs/adr/0001-supported-python-version.md): CPython 3.13 — Accepted, implemented
- [ADR-0002](docs/adr/0002-python-environment-and-dependency-manager.md): Poetry — Accepted, implemented
- [ADR-0003](docs/adr/0003-initial-server-api-framework.md): FastAPI as API adapter — Accepted, implemented
- [ADR-0004](docs/adr/0004-repository-layout.md): hybrid staged `src/` layout — Accepted, implemented
- [ADR-0005](docs/adr/0005-configuration-strategy.md): layered configuration strategy — Accepted, implemented
- [ADR-0006](docs/adr/0006-macos-python-interpreter-provider.md): `uv` as macOS CPython provider — Accepted, implemented
- [ADR-0007](docs/adr/0007-settings-library.md): `pydantic-settings` adapter — Accepted, implemented
- [ADR-0008](docs/adr/0008-asgi-runtime.md): Uvicorn loopback-first runtime — Accepted, implemented
- [ADR-0009](docs/adr/0009-structured-logging-approach.md): standard-library structured JSON logging — Accepted, implemented
- [ADR-0010](docs/adr/0010-initial-persistence-foundation.md): synchronous SQLAlchemy Core with Alembic — Accepted, implemented
- [ADR-0011](docs/adr/0011-stable-domain-identities.md): stable UUIDv4 domain identities — Accepted, implemented
- [ADR-0012](docs/adr/0012-initial-device-registry.md): initial device registry boundary — Accepted, implemented
- [ADR-0013](docs/adr/0013-initial-library-registry.md): initial library registry and root locators — Accepted, implemented

Accepted ADRs are normative until superseded. This handoff does not edit or reinterpret accepted ADR text.

## 11. Explicitly unimplemented scope

Not implemented:

- filesystem scan preview
- persistent scan runs
- recursive media discovery
- media-file candidate classification
- logical media entities
- physical media-location entities
- media catalog tables
- migration `0004`
- storage-volume entity or table
- storage discovery or mount detection
- capacity or free-space monitoring
- availability or last-seen state
- hashing or duplicate detection
- file metadata extraction
- FFmpeg or ffprobe integration
- thumbnails or cover generation
- sidecar format
- tags and series behavior beyond identity values
- acquisition or downloader workflow inside FrameNest
- HTTP catalog API
- desktop UI
- gallery
- playback
- synchronization
- server aggregation
- authentication
- backup, restore, rebuild, or corruption recovery
- final WAL policy
- final production database-location policy
- Fedora deployment
- systemd services
- Tailscale integration

## 12. Non-authoritative next direction

The next Orchestrator must independently choose and authorize the next bounded task.

The strongest current product pressure is a safe, read-only scan-preview boundary for one registered local library. A likely first preview would traverse without writing media records and produce deterministic summary or candidate evidence. The exact traversal policy, supported extensions, symlink policy, hidden-file policy, error policy, ordering, limits, output contract, and privacy boundary remain undecided.

No Worker may implement scanning from this handoff alone. The next task requires a separate authoritative Orchestrator prompt and possibly an ADR if durable architectural choices are introduced. Storage-volume work also remains deferred and must not be inferred automatically.

## 13. Fresh Worker reading order

1. [AGENTS.md](AGENTS.md)
2. [BOOT_WORKER.md](BOOT_WORKER.md)
3. [AP_WORKER.md](AP_WORKER.md)
4. [NEXT_WORKER.md](NEXT_WORKER.md)
5. [PRODUCT.md](PRODUCT.md)
6. [SPEC.md](SPEC.md)
7. [ROADMAP.md](ROADMAP.md)
8. [SECURITY.md](SECURITY.md)
9. [README.md](README.md)
10. [ADR-0010](docs/adr/0010-initial-persistence-foundation.md)
11. [ADR-0011](docs/adr/0011-stable-domain-identities.md)
12. [ADR-0012](docs/adr/0012-initial-device-registry.md)
13. [ADR-0013](docs/adr/0013-initial-library-registry.md)
14. task-relevant source and tests
15. the separate authoritative Orchestrator prompt

The task prompt, not this handoff, defines actual scope and Git authority.

## 14. Language and report protocol

- Orchestrator communication with the Cooperator is Slovak
- Worker prompts are English
- Worker reports are English
- Worker reports must begin exactly with `### Report for ORCHESTRATOR_CHAT`
- Worker reports must distinguish observed evidence from inference
- Worker reports remain compact and evidence-dense
- protocol role is `WORKER`, independent of Cursor, Codex, Auto routing, model, or provider

## 15. Artifact lifecycle

- Classification: non-authoritative Worker-session handoff
- Intended consumer: future fresh Worker sessions during bootstrap
- Discoverability: repository root and Worker bootstrap reading order
- Retention: replace only at a future explicitly authorized Worker-session closeout
- Supersession and cleanup owner: future closing Worker acting under explicit Orchestrator authority
- Git history is the archive; the active tree must contain only the latest handoff

Current WORKER session: CLOSED.
