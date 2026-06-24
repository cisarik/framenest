# Next Worker Handoff

## 1. Purpose and authority

This file is a non-authoritative Worker-session handoff. It is not a task, does not grant modification authority, and does not grant dependency, command, architecture, or Git authority.

A fresh Worker must receive a separate authoritative Orchestrator prompt before doing any work. The fresh Worker reads this file directly from the repository during bootstrap; the Cooperator normally does not paste it manually.

Current WORKER session: CLOSED.

## 2. Repository identity

- Repository: `https://github.com/cisarik/framenest.git`
- Local path used by the closing Worker: `/Users/agile/framenest`
- Branch: `main`
- Pre-handoff public HEAD: `dcb9f68b155e3b96cb715c3cf6eef0ae7e0f7f5d`
- Pre-handoff subject: `fix: enforce identity construction invariants`
- Pre-handoff parent: `bf82ad445dc29a437779f5b8c75859176a32d6f6`

A fresh Worker must independently resolve final post-handoff local `HEAD`, local `origin/main`, and remote `main`. Do not infer the final post-handoff SHA from this file.

## 3. Toolchain and dependency state

- Runtime target: CPython `>=3.13,<3.14`
- Observed project environment: CPython `3.13.14` in `.venv/`
- Observed Poetry version: `2.1.4`
- Poetry remains the dependency, environment, and lockfile authority.
- `uv` remains the accepted Apple Silicon macOS CPython interpreter provider through [ADR-0006](docs/adr/0006-macos-python-interpreter-provider.md), while Poetry remains authoritative for the project environment.

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

SQLAlchemy and Alembic are installed and active for the persistence foundation. SQLAlchemy ORM mapped entities, SQLModel, `aiosqlite`, async SQLAlchemy engines, and async SQLAlchemy sessions are not accepted or implemented for the initial foundation.

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
- initial Alembic revision `0001` with no product schema
- explicit database commands `poetry run framenest-db status` and `poetry run framenest-db migrate`
- deterministic machine-readable database command output
- no automatic migration during normal server startup
- pure-domain identity primitives in `src/framenest/domain/identities.py`

The initial persistence foundation creates only Alembic version tracking. It does not create a media catalog, gallery data, library registration, device table, location table, sidecar table, user table, authentication table, or any product schema.

## 5. Stable identity foundation

[ADR-0011](docs/adr/0011-stable-domain-identities.md) is Accepted and implemented only within its stated boundary.

Implemented identity types:

- `MediaId`
- `MediaLocationId`
- `DeviceId`
- `LibraryId`
- `StorageVolumeId`
- `SeriesId`

Current identity behavior:

- application-owned RFC 9562 UUID version 4 values
- generation through Python standard-library `uuid.uuid4()`
- canonical external text as lowercase hyphenated UUID strings
- strict parsing that rejects non-canonical forms instead of normalizing them
- immutable frozen and slotted value objects
- runtime category separation between identity classes
- runtime type, UUID variant, and UUIDv4 enforcement on every normal constructor path
- FrameNest-owned sanitized validation errors
- no FastAPI, Pydantic, SQLAlchemy, Alembic, Uvicorn, settings, filesystem, persistence, or network imports in the domain identity module

Identity strings are opaque. They must not be used to infer entity type, creation time, filesystem location, database row position, source platform, content hash, or semantic ordering.

## 6. Test evidence at closeout

Observed by the closing Worker before replacing this handoff:

- `poetry run pytest --collect-only -q`: `249 tests collected`
- `poetry run pytest -q`: `249 passed`
- `poetry run pytest -q -W error`: `249 passed`

The closeout validation after replacing this file also passed the full suite and warnings-as-errors suite. A fresh Worker must still rerun its own bootstrap baseline from the final public commit it receives.

## 7. Accepted architecture package

Accepted ADRs currently recorded:

- [ADR-0001](docs/adr/0001-supported-python-version.md): CPython 3.13
- [ADR-0002](docs/adr/0002-python-environment-and-dependency-manager.md): Poetry
- [ADR-0003](docs/adr/0003-initial-server-api-framework.md): FastAPI as an API adapter; domain independent
- [ADR-0004](docs/adr/0004-repository-layout.md): hybrid staged `src/` layout
- [ADR-0005](docs/adr/0005-configuration-strategy.md): layered configuration strategy
- [ADR-0006](docs/adr/0006-macos-python-interpreter-provider.md): `uv` as macOS CPython interpreter provider
- [ADR-0007](docs/adr/0007-settings-library.md): `pydantic-settings` as settings adapter
- [ADR-0008](docs/adr/0008-asgi-runtime.md): Uvicorn as initial loopback-first ASGI runtime
- [ADR-0009](docs/adr/0009-structured-logging-approach.md): standard-library logging with FrameNest JSON formatter and centralized redaction boundary
- [ADR-0010](docs/adr/0010-initial-persistence-foundation.md): synchronous SQLAlchemy 2.x Core with Alembic for SQLite migrations; no ORM, SQLModel, or async SQLite access initially
- [ADR-0011](docs/adr/0011-stable-domain-identities.md): application-owned UUIDv4 stable domain identities with category-specific pure-domain types

Accepted ADRs are normative until superseded by later accepted ADRs. Evidence packages and handoff files do not supersede ADRs.

## 8. Boundaries and unimplemented areas

Still not implemented:

- actual media catalog schema
- migration revision `0002`
- media catalog repository API
- domain entities beyond the six identity value types
- logical media, physical location, device, library, storage volume, or series behavior beyond identities
- canonical tags
- sidecar manifest format
- scanner
- downloader or acquisition adapter
- cover pipeline
- gallery
- desktop shell
- playback implementation
- sync
- server aggregation
- authentication or authorization
- Fedora deployment
- systemd integration
- Tailscale integration
- backup, restore, corruption recovery, and rebuild commands
- final WAL policy
- final production database path

Do not treat the empty `0001` Alembic revision as a media catalog.

## 9. Non-authoritative next direction

The next Orchestrator must independently choose the next bounded task. Likely project pressure is toward an initial local catalog schema and a FrameNest-owned repository boundary, but this handoff does not authorize that work.

No Worker may implement catalog schema, migration `0002`, repository interfaces, entities, or scanning from this file alone. A separate authoritative Orchestrator prompt is mandatory, and any unresolved strategic or architectural choice must be handled through the approved protocol.

## 10. Fresh Worker reading order

1. [AGENTS.md](AGENTS.md)
2. [BOOT_WORKER.md](BOOT_WORKER.md)
3. [AP_WORKER.md](AP_WORKER.md)
4. [NEXT_WORKER.md](NEXT_WORKER.md)
5. [PRODUCT.md](PRODUCT.md)
6. [SPEC.md](SPEC.md)
7. [ROADMAP.md](ROADMAP.md)
8. [ADR-0010](docs/adr/0010-initial-persistence-foundation.md)
9. [ADR-0011](docs/adr/0011-stable-domain-identities.md)
10. Other task-relevant ADRs
11. Task-relevant source and tests
12. The separate authoritative Orchestrator prompt

## 11. Language and report protocol

- Orchestrator communication with the Cooperator is Slovak.
- Worker prompts are English.
- Worker reports are English.
- Worker reports must begin exactly with `### Report for ORCHESTRATOR_CHAT`.
- Worker reports should be compact, evidence-dense, and honest about deviations and residual risk.
- Repository documentation and code remain professional English unless a task explicitly says otherwise.

## 12. Artifact lifecycle

- Classification: non-authoritative Worker-session handoff
- Consumer: future Worker sessions during bootstrap
- Discoverability: repository root and Worker bootstrap reading order
- Retention: replace only at a future explicitly authorized Worker-session closeout
- Supersession: the next committed `NEXT_WORKER.md` replacement supersedes this file as session state, while Git history remains the archive

Current WORKER session: CLOSED.
