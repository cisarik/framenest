# Next Worker Handoff

## 1. Purpose and authority

This file transfers current repository state to a fresh Worker session. It is not a task. It grants no modification authority, dependency authority, command authority, or Git authority. Every new Worker still requires one separate authoritative Orchestrator prompt.

The fresh Worker reads this file directly from the repository. The Cooperator normally does not paste its contents manually.

**Current WORKER session: CLOSED.**

## 2. Repository identity

- Repository: `https://github.com/cisarik/framenest.git`
- Local path: `/Users/agile/framenest`
- Branch: `main`
- Handoff base HEAD: `e43001eba2daafed27db6a3d304279cd61c04db4`
- The fresh Worker MUST independently resolve local `HEAD`, `origin/main`, and remote `main`; do not assume this file contains the final post-handoff commit SHA.

## 3. Toolchain and dependency state

- CPython 3.13.14 in `.venv/`
- Poetry 2.1.4
- `uv` 0.11.24 observed as the Apple Silicon macOS interpreter provider ([ADR-0006](docs/adr/0006-macos-python-interpreter-provider.md))
- Poetry remains dependency, environment, and lockfile authority

Runtime dependencies (`pyproject.toml`, locked in `poetry.lock`):

- `pydantic-settings` `2.14.2`
- `fastapi` `0.138.0`
- `uvicorn` `0.49.0`

Development dependencies (`pyproject.toml`, locked in `poetry.lock`):

- `pytest` `9.1.1`
- `httpx2` `2.4.0`

SQLAlchemy and Alembic are accepted through [ADR-0010](docs/adr/0010-initial-persistence-foundation.md) but are not installed. No ORM, SQLModel, or async SQLite dependency exists.

## 4. Current implemented foundation

- Root Poetry package using `src/framenest/`
- Centralized `pydantic-settings` configuration in `src/framenest/configuration.py`
- `FRAMENEST_HOST`, `FRAMENEST_PORT`, and safe loopback defaults
- FastAPI application factory in `src/framenest/adapters/api/application.py`
- Typed `GET /health` endpoint
- Plain Uvicorn runtime in `src/framenest/server.py`
- Runnable console entrypoint: `framenest-server`
- Explicit single-worker, no-reload, no-proxy-trust runtime configuration
- FrameNest-owned structured logging boundary in `src/framenest/structured_logging.py`
- Deterministic JSON formatter, centralized redaction, and safe formatter fallback
- Explicit Uvicorn `log_config` integration
- Uvicorn access logging disabled (`access_log=False`)
- Strict direct-process JSON output contract in `tests/contract/test_server_process_output.py`
- Clean direct-process SIGINT and SIGTERM shutdown without application traceback
- Documented application-versus-launcher output boundary in [README.md](README.md) and [SECURITY.md](SECURITY.md)
- Unit, contract, live-loopback, import-boundary, redaction, process-output, and cleanup tests

## 5. Current tests

At handoff base HEAD:

- cache-free suite: **94 passed** with **zero warnings**
- warnings-as-errors suite: **94 passed**

The fresh Worker MUST rerun the baseline during its bootstrap gate.

## 6. Accepted architecture

Essential accepted ADRs:

- [ADR-0001](docs/adr/0001-supported-python-version.md): CPython 3.13
- [ADR-0002](docs/adr/0002-python-environment-and-dependency-manager.md): Poetry
- [ADR-0003](docs/adr/0003-initial-server-api-framework.md): FastAPI as API adapter; domain independent
- [ADR-0004](docs/adr/0004-repository-layout.md): hybrid staged src-layout monorepo
- [ADR-0005](docs/adr/0005-configuration-strategy.md): layered configuration and secret redaction
- [ADR-0006](docs/adr/0006-macos-python-interpreter-provider.md): `uv` as macOS CPython provider
- [ADR-0007](docs/adr/0007-settings-library.md): `pydantic-settings` as concrete settings adapter
- [ADR-0008](docs/adr/0008-asgi-runtime.md): Uvicorn as loopback-first ASGI runtime
- [ADR-0009](docs/adr/0009-structured-logging-approach.md): stdlib logging with FrameNest JSON formatter and redaction boundary
- [ADR-0010](docs/adr/0010-initial-persistence-foundation.md): synchronous SQLAlchemy 2.x Core + Alembic for SQLite; FrameNest-owned repository boundaries; no ORM, SQLModel, or async SQLite initially

## 7. Resolved logging-output finding

Verified current state:

- direct console-script and module execution produce only FrameNest JSON application records on `stderr`
- ordinary SIGINT no longer emits an application traceback
- SIGTERM remains a normal signal exit
- Poetry may emit its own launcher diagnostics outside the FrameNest logging graph
- launcher output is not part of the FrameNest structured-log contract
- the issue is resolved and covered by process-level contract tests

## 8. Persistence decision and current absence

- [ADR-0010](docs/adr/0010-initial-persistence-foundation.md) accepts synchronous SQLAlchemy 2.x Core + Alembic
- the standard-library `sqlite3` driver remains the underlying SQLite access path through `sqlite+pysqlite`
- repositories and transactions must remain FrameNest-owned
- SQLAlchemy ORM mapped entities, SQLModel, async SQLite, and silent startup migrations are not accepted initially
- migrations are explicit and initially upgrade-only
- WAL remains deferred pending macOS and Fedora evidence
- no persistence package, engine, database path setting, Alembic environment, revision, CLI, database file, or migration dependency exists yet

## 9. Next implementation boundary

Non-authoritative context only:

- the next bounded implementation should create only the minimal persistence foundation defined by ADR-0010
- it must not create the media catalog
- no media, library, device, series, tag, location, cover, or sidecar tables
- a separate authoritative Orchestrator prompt is mandatory

## 10. What still does not exist

- Media-domain identity model
- Media catalog schema
- Durable sidecar schema
- Library scanning
- Acquisition or downloader
- Gallery
- Desktop shell
- Catalog synchronization
- Server aggregation
- Authentication
- Deployment
- systemd
- Tailscale integration
- Fedora validation
- Database backup, restore, corruption recovery, and rebuild commands

## 11. Fresh Worker reading order

1. [AGENTS.md](AGENTS.md)
2. [BOOT_WORKER.md](BOOT_WORKER.md)
3. [AP_WORKER.md](AP_WORKER.md)
4. [NEXT_WORKER.md](NEXT_WORKER.md)
5. [ROADMAP.md](ROADMAP.md)
6. [SPEC.md](SPEC.md)
7. [ADR-0010](docs/adr/0010-initial-persistence-foundation.md)
8. Other ADRs relevant to the task
9. Current source and tests relevant to the task
10. The separate authoritative Orchestrator prompt

## 12. Language and report protocol

- Worker prompts: English
- Worker reports: English
- reports begin exactly with: `### Report for ORCHESTRATOR_CHAT`
- reports use the compact evidence-dense format from [AP_WORKER.md](AP_WORKER.md)

## Authority

This handoff grants no modification or Git authority.
