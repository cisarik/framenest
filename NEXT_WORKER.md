# Next Worker Handoff

## 1. Purpose and authority

This file transfers current repository state to a fresh Worker session. It grants no task authority, modification authority, dependency authority, or Git authority. Every new Worker still requires a separate authoritative Orchestrator prompt.

**Current Worker session: CLOSED.**

## 2. Repository identity

- Repository: `https://github.com/cisarik/framenest.git`
- Local path: `/Users/agile/framenest`
- Branch: `main`
- Handoff base HEAD: `debfcff72d49ffcdd89aed970089d9c9130aa7c2`
- The fresh Worker MUST independently resolve local `HEAD`, `origin/main`, and remote `main`; do not assume this file contains the final post-handoff commit SHA.

## 3. Toolchain

- CPython 3.13.14 in `.venv/`
- Poetry 2.1.4
- `uv` 0.11.24 observed as the Apple Silicon macOS interpreter provider ([ADR-0006](docs/adr/0006-macos-python-interpreter-provider.md))
- Poetry remains dependency, environment, and lockfile authority

## 4. Current implemented foundation

- Root Poetry package using `src/framenest/`
- Centralized `pydantic-settings` configuration in `src/framenest/configuration.py`
- `FRAMENEST_HOST`, `FRAMENEST_PORT`, and safe loopback defaults
- FastAPI application factory in `src/framenest/adapters/api/application.py`
- Typed `GET /health` endpoint
- Plain Uvicorn runtime in `src/framenest/server.py`
- Runnable command: `poetry run framenest-server`
- Explicit single-worker, no-reload, no-proxy-trust runtime configuration
- FrameNest-owned structured logging boundary in `src/framenest/structured_logging.py`
- Deterministic JSON formatter, centralized redaction, and safe formatter fallback
- Explicit Uvicorn `log_config` integration
- Uvicorn access logging disabled (`access_log=False`)
- Unit, contract, live-loopback, import-boundary, redaction, and cleanup tests

## 5. Dependency state

Runtime (`pyproject.toml`, locked in `poetry.lock`):

- `pydantic-settings` `2.14.2`
- `fastapi` `0.138.0`
- `uvicorn` `0.49.0`

Development (`pyproject.toml`, locked in `poetry.lock`):

- `pytest` `9.1.1`
- `httpx2` `2.4.0`

No third-party structured-logging dependency is installed. No SQLite ORM or migration dependency is installed yet.

## 6. Verified tests

At handoff base HEAD:

- cache-free suite: **80 passed** with **zero warnings**
- warnings-as-errors suite: **80 passed**

The fresh Worker MUST rerun both during its bootstrap gate.

## 7. Accepted architectural decisions

Essential constraints only:

- [ADR-0005](docs/adr/0005-configuration-strategy.md): centralized layered settings, typed validation, secret redaction, deterministic isolated tests
- [ADR-0007](docs/adr/0007-settings-library.md): `pydantic-settings` as the concrete settings adapter; domain remains independent of Pydantic
- [ADR-0008](docs/adr/0008-asgi-runtime.md): Uvicorn as loopback-first ASGI runtime; runtime infrastructure only; no secret disclosure; testable startup/shutdown
- [ADR-0009](docs/adr/0009-structured-logging-approach.md): standard-library `logging` with a FrameNest-owned JSON formatter and centralized redaction boundary; no third-party logging framework in production code

## 8. Known unresolved logging-output issue

Verified report finding from the structured-logging implementation session (not a proven root cause):

- transient subprocess smoke using `poetry run framenest-server` produced **8** valid FrameNest JSON lines
- the combined captured `stderr` also contained **29** non-JSON lines
- reported sources included Poetry/macOS wrapper warnings and a `KeyboardInterrupt` traceback during SIGINT shutdown
- secrets, request path, URL, query data, and ANSI escapes were absent from the JSON records
- health, listener shutdown, and child-process cleanup succeeded
- the strict all-captured-stderr-is-JSON expectation was therefore **not** proven
- do not claim that the FrameNest formatter generated the foreign lines
- do not dismiss the issue without reproducing it

The next smallest task should isolate and correct or accurately specify the output contract by comparing at minimum:

- `poetry run framenest-server`
- direct `.venv/bin/framenest-server`
- graceful termination behavior
- application JSON logs versus wrapper/interpreter diagnostics

A future task may adjust code, tests, command behavior, or documentation only after reproduction. This handoff grants no authority to do so.

## 9. What still does not exist

- Functional media catalog
- SQLite database
- ORM/query implementation
- Migration mechanism
- Domain identity model
- Library scanning
- Sidecar format
- Downloader
- Gallery
- Desktop shell
- Deployment
- systemd
- Tailscale integration
- Authentication
- Correlation/request middleware
- Log retention or remote shipping

## 10. Database decision boundary

- [ROADMAP.md](ROADMAP.md) identifies SQLite catalog and migrations as the remaining Phase 4 foundation work
- [SPEC.md](SPEC.md) still explicitly defers ORM/query strategy
- a future Worker must not silently select SQLAlchemy, SQLModel, raw `sqlite3`, Alembic, or another migration mechanism
- after the logging-output correction, the next architecture step should be transient report-only primary-source evidence for the database/query/migration strategy
- no committed database research artifact is currently required

## 11. Required reading

1. [AGENTS.md](AGENTS.md)
2. [BOOT_WORKER.md](BOOT_WORKER.md)
3. [AP_WORKER.md](AP_WORKER.md)
4. [NEXT_WORKER.md](NEXT_WORKER.md)
5. [ROADMAP.md](ROADMAP.md)
6. [SPEC.md](SPEC.md)
7. [ADR-0005](docs/adr/0005-configuration-strategy.md)
8. [ADR-0007](docs/adr/0007-settings-library.md)
9. [ADR-0008](docs/adr/0008-asgi-runtime.md)
10. [ADR-0009](docs/adr/0009-structured-logging-approach.md)
11. `pyproject.toml`
12. current source and tests relevant to the next task
13. the separate authoritative Orchestrator prompt

## 12. Language and report protocol

- Worker prompts: English
- Worker reports: English
- reports begin exactly with: `### Report for ORCHESTRATOR_CHAT`
- reports use the compact evidence-dense format from [AP_WORKER.md](AP_WORKER.md)

## Authority

This handoff grants no modification or Git authority.
