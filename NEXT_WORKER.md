# Next Worker Handoff

## Purpose

This file transfers current repository state to a future Worker session. It does not grant modification authority, Git-write permission, or an executable task.

## Repository

- Repository: `https://github.com/cisarik/framenest.git`
- Local path: `/Users/agile/framenest`
- Branch: `main`
- Pre-closeout public SHA: `09909b64924a0ef35f19be78f1fff871bfe0d00e`
- Final public HEAD: resolve from current `main` after push; do not guess from this file.

## Current scaffold

A minimal Poetry package scaffold exists:

- `pyproject.toml`
- `poetry.lock`
- `src/framenest/`
- `tests/unit/`

Current test suite: one passing import and src-layout test.

Local `.venv` uses uv-managed CPython 3.13.14 at `/Users/agile/framenest/.venv`.

Observed toolchain:

- `uv` 0.11.24 (Homebrew)
- Poetry 2.1.4

## Accepted decisions relevant to next work

- [ADR-0005](docs/adr/0005-configuration-strategy.md) — layered configuration strategy
- [ADR-0006](docs/adr/0006-macos-python-interpreter-provider.md) — uv-managed CPython 3.13.14 on macOS
- [ADR-0007](docs/adr/0007-settings-library.md) — `pydantic-settings` approved; not yet installed or implemented

## What does not exist yet

- No configuration module
- No `pydantic-settings` dependency in `pyproject.toml`
- No FastAPI application
- No API endpoint
- No database
- No server process
- No deployment configuration

## Required reading for the next Worker

1. [AGENTS.md](AGENTS.md)
2. [BOOT_WORKER.md](BOOT_WORKER.md)
3. [AP_WORKER.md](AP_WORKER.md)
4. [NEXT_WORKER.md](NEXT_WORKER.md)
5. [ADR-0005](docs/adr/0005-configuration-strategy.md)
6. [ADR-0007](docs/adr/0007-settings-library.md)
7. `pyproject.toml`
8. Current tests
9. The separate authoritative task from the Orchestrator

The next Worker may perform a compact bootstrap gate inside the first implementation task instead of a separate bootstrap-only task.

## Language and reporting

- Worker prompts: English
- Worker reports: English, beginning with `### Report for ORCHESTRATOR_CHAT`
- Use the compact report format defined in [AP_WORKER.md](AP_WORKER.md)

## Authority

This handoff grants no modification or Git authority.
