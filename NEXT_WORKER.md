# Next Worker Handoff

## Purpose

This file transfers current repository state to a future Worker session. It does not grant modification authority, Git-write permission, or an executable task.

**Current Worker session: CLOSED.**

## Repository

- Repository: `https://github.com/cisarik/framenest.git`
- Local path: `/Users/agile/framenest`
- Branch: `main`
- Handoff base HEAD: `45daea5e72e3f26daf3422fe1cf4e672249dfb58`
- Final public HEAD: the next Worker MUST resolve current local, tracking, and remote `main` itself; do not assume this file contains the post-push SHA.

## Toolchain

- CPython 3.13.14 in `.venv/`
- Poetry 2.1.4
- `uv` 0.11.24 observed as the Apple Silicon macOS interpreter provider ([ADR-0006](docs/adr/0006-macos-python-interpreter-provider.md))

## Current implemented state

- Poetry package at repository root with `src/framenest/`
- Centralized `pydantic-settings` configuration in `src/framenest/configuration.py`
- FastAPI application factory in `src/framenest/adapters/api/application.py`
- Typed `GET /health` endpoint
- In-process API contract tests in `tests/contract/`
- Import-boundary tests in `tests/unit/`
- Configuration precedence and secret-redaction tests

## Current dependencies

Runtime (`pyproject.toml`):

- `pydantic-settings`
- `fastapi`

Development:

- `pytest`
- `httpx2`

Uvicorn is **not** installed. See [ADR-0008](docs/adr/0008-asgi-runtime.md).

## Verified tests

At handoff base HEAD, the cache-free suite reported **18 passed** with **zero warnings**. The next Worker MUST re-verify.

## Accepted ADR-0008 constraints

[ADR-0008](docs/adr/0008-asgi-runtime.md) accepts **Uvicorn** as the initial ASGI runtime. Essential constraints:

- Uvicorn remains runtime/infrastructure only; not in domain or application layers
- `create_app()` must stay independently testable without starting Uvicorn
- default bind uses centralized settings host (`127.0.0.1`)
- public bind requires explicit override
- forwarded/proxy headers must not be trusted broadly by default
- secrets must not appear in runtime arguments, logs, diagnostics, or process metadata
- startup/shutdown must be testable without orphaned listeners or child processes

## What does not exist yet

- Uvicorn dependency in `pyproject.toml` or `poetry.lock`
- Startup entrypoint or runtime command
- Real network listener or runnable server process
- Database or SQLite catalog
- Structured logging implementation
- Deployment configuration
- systemd unit
- Tailscale integration

## Next smallest proposed task

A fresh Worker session should receive a bounded, test-first task to install and wire Uvicorn runtime/startup using `FrameNestSettings.host`, still without deployment, systemd, or public binding. This handoff is descriptive only and grants no authority.

## Required reading for the next Worker

1. [AGENTS.md](AGENTS.md)
2. [BOOT_WORKER.md](BOOT_WORKER.md)
3. [AP_WORKER.md](AP_WORKER.md)
4. [NEXT_WORKER.md](NEXT_WORKER.md)
5. [ADR-0008](docs/adr/0008-asgi-runtime.md)
6. [ADR-0005](docs/adr/0005-configuration-strategy.md)
7. [ADR-0007](docs/adr/0007-settings-library.md)
8. `pyproject.toml`
9. `src/framenest/configuration.py`
10. `src/framenest/adapters/api/application.py`
11. Current tests
12. The separate authoritative task from the Orchestrator

The next Worker may perform a compact bootstrap gate inside the first implementation task.

## Language and reporting

- Worker prompts: English
- Worker reports: English, beginning with `### Report for ORCHESTRATOR_CHAT`
- Use the compact report format defined in [AP_WORKER.md](AP_WORKER.md)

## Authority

This handoff grants no modification or Git authority.
