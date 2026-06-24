# Next Worker Handoff

## 1. Purpose and authority

This file is a non-authoritative Worker-session handoff. It is state-restoration evidence only. It is not a task and grants no modification, architecture, dependency, migration, command, filesystem, network, AI-provider, or Git authority.

A fresh Worker requires one separate authoritative Orchestrator task prompt before doing any work. The Cooperator normally does not paste this file manually. A fresh Worker reads it directly from the repository during bootstrap.

Repository state, accepted ADRs, tests, and the new authoritative task override stale handoff claims.

Current WORKER session: **CLOSED**.

## 2. Repository identity

- Repository: `https://github.com/cisarik/framenest.git`
- Local path used by the closing Worker: `/Users/agile/framenest`
- Branch: `main`
- Pre-handoff public HEAD: `c4a80b40f89f67e0aadc66d02536cbd6626acef3`
- Pre-handoff subject: `feat: add library scan preview`
- Pre-handoff parent: `0c5795baedfcacaf1334e6bb5e4e62f682888ab4`

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

No dependency change occurred in cycle 045. SQLAlchemy ORM mapped entities, SQLModel, `aiosqlite`, and async SQLAlchemy are not accepted or implemented.

## 4. Implemented architecture

The repository currently implements:

- centralized typed settings in `src/framenest/configuration.py`
- FastAPI application factory and typed `GET /health`
- loopback-first Uvicorn runtime through `poetry run framenest-server`
- FrameNest-owned structured JSON logging and redaction in `src/framenest/structured_logging.py`
- synchronous SQLAlchemy 2.x Core SQLite persistence in `src/framenest/infrastructure/persistence/`
- explicit database commands `poetry run framenest-db status` and `poetry run framenest-db migrate`
- packaged Alembic migrations through revision `0003`
- stable UUIDv4 domain identities per [ADR-0011](docs/adr/0011-stable-domain-identities.md)
- pure-domain `Device` and `Library` entities with device-local `LibraryRoot` locators
- application `DeviceRepository` and `LibraryRepository` ports
- synchronous SQLAlchemy Core registry adapters
- development catalog CLI `poetry run framenest-catalog` for device and library registry operations
- ADR-0014 scan-preview application boundary in `src/framenest/application/library_scan.py`
- `LibraryScanner` port in `src/framenest/application/ports/library_scanner.py`
- standard-library `LocalLibraryScanner` in `src/framenest/infrastructure/filesystem/library_scanner.py`
- `PreviewLibraryScan` application service
- `poetry run framenest-catalog library scan-preview`

## 5. Scan-preview contract

Per [ADR-0014](docs/adr/0014-safe-library-scan-preview.md), the implemented preview is:

- bounded (`max_entries` default `100000`, range 1–1000000; `max_candidates` default `1000`, range 1–10000)
- deterministic depth-first traversal with per-directory ordering by `name.casefold()` then `name`
- extension-hint candidate classification only (17 video extensions plus `.gif`)
- candidate kinds `video` and `gif`
- relative `/` output paths only
- dot-prefixed entries skipped without traversing hidden directories
- nested symbolic links skipped and counted; registered root symlink path allowed
- metadata-only file inspection (`stat` size); no file-content reading
- no filesystem mutation, database write, migration, media persistence, hashing, or external tools
- no FFmpeg, ffprobe, MIME sniffing, or thumbnail generation
- sanitized CLI errors; no absolute library root, database path, raw OS error, or symlink-target leakage

## 6. Current CLI

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

### Scan preview

```text
poetry run framenest-catalog library scan-preview --id LIBRARY_ID
poetry run framenest-catalog library scan-preview \
  --id LIBRARY_ID \
  --max-entries N \
  --max-candidates N
```

Catalog commands require the database at packaged migration head, emit one compact JSON object per non-help invocation, never migrate automatically, and remain development/operator boundaries rather than final desktop UX.

## 7. Test evidence

Observed by the closing Worker before replacing this handoff:

- `poetry run pytest --collect-only -q`: **487 tests collected**
- `poetry run pytest -q`: **487 passed**
- `poetry run pytest -q -W error`: **487 passed**
- zero observed pytest warnings
- `poetry check --lock`: passed

These are closing-Worker-observed results. Every future Worker must independently rerun the baseline from the final public commit it receives.

Test tree structure:

- `tests/contract/`: health API, server process output, Uvicorn runtime/logging, persistence CLI, persistence package resources, catalog CLI
- `tests/integration/`: persistence migrations; device/library repository tests; filesystem read-only scan safety
- `tests/unit/`: configuration, import boundaries, API boundaries, persistence engine/boundaries, server runtime, structured logging, package import; domain identity/device/library tests; application repository-port and library-scan tests; filesystem scanner tests; catalog library-root helper tests

## 8. Accepted ADRs

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
- [ADR-0014](docs/adr/0014-safe-library-scan-preview.md): safe read-only library scan preview — Accepted, implemented

Accepted ADRs are normative until superseded. This handoff does not edit or reinterpret accepted ADR text.

## 9. Explicitly unimplemented scope

Not implemented:

- persistent scan records or scan history
- logical media entities and physical media-location entities
- media catalog tables
- migration `0004`
- FFmpeg or ffprobe integration
- representative-frame extraction
- AI or VLM analysis
- AI-provider adapters
- AI-generated title, tags, descriptions, or filename suggestions
- automatic or confirmed file renaming
- persistent tag system
- MEME collection implementation
- storage-volume entity, table, or discovery
- hashing and duplicate detection
- file metadata extraction beyond scan-preview size and extension hints
- sidecars
- thumbnails or covers
- HTTP catalog API beyond health
- desktop UI, gallery, playback, sync, server aggregation, deployment
- authentication, backup, restore, rebuild, or corruption recovery
- Fedora deployment, systemd services, and Tailscale integration

## 10. Non-authoritative next direction

Planning context only — not task authority:

- strongest current product pressure is preparation for safe AI-assisted media understanding
- likely next foundational slice is deterministic local metadata and representative-frame preparation
- it may use `ffprobe` and `ffmpeg`, but tool choice and dependency/installation policy require a separate authorized decision
- target is approximately three representative distinct frames per video or GIF; fewer distinct frames must be reported honestly when three do not exist
- cloud AI remains optional and opt-in
- no Worker may implement any of this from the handoff alone
- a separate authoritative prompt and likely one or more ADRs are required

## 11. Fresh Worker reading order

1. [AGENTS.md](AGENTS.md)
2. [BOOT_WORKER.md](BOOT_WORKER.md)
3. [AP_WORKER.md](AP_WORKER.md)
4. [NEXT_WORKER.md](NEXT_WORKER.md)
5. [PRODUCT.md](PRODUCT.md), [SPEC.md](SPEC.md), [ROADMAP.md](ROADMAP.md), [SECURITY.md](SECURITY.md), [README.md](README.md)
6. [ADR-0010](docs/adr/0010-initial-persistence-foundation.md) through [ADR-0014](docs/adr/0014-safe-library-scan-preview.md)
7. task-relevant source and tests
8. the separate authoritative Orchestrator task prompt

The task prompt, not this handoff, defines actual scope and Git authority.

## 12. Protocol and lifecycle

- Orchestrator communication with the Cooperator is Slovak
- Worker prompts and reports are English
- Worker reports must begin exactly with `### Report for ORCHESTRATOR_CHAT`
- protocol role is `WORKER`, independent of Cursor, Codex, Auto routing, model, or provider

Artifact lifecycle:

- classification: non-authoritative Worker-session handoff
- intended consumer: future fresh Worker sessions during bootstrap
- discoverability: repository root and Worker bootstrap reading order
- retention: replace only at a future explicitly authorized Worker-session closeout
- supersession and cleanup owner: future closing Worker acting under explicit Orchestrator authority
- Git history is the archive; the active tree must contain only the latest handoff

Current WORKER session: **CLOSED**.
