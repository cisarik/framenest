# Next Orchestrator Handoff

## Purpose

This file transfers session state to a fresh Orchestrator chat after scaffold-session closeout. It does not grant modification authority and does not replace permanent repository documents.

## Repository state

- Repository: `https://github.com/cisarik/framenest.git`
- Local path: `/Users/agile/framenest`
- Branch: `main`
- Scaffold commit before this closeout: `09909b64924a0ef35f19be78f1fff871bfe0d00e`
- Final handoff commit: resolve from public `main` after push

## Completed work

- Minimal Poetry package scaffold with `pyproject.toml`, `poetry.lock`, `src/framenest/`, and `tests/unit/`
- One passing import and src-layout test
- uv-managed CPython 3.13.14 provisioning on Apple Silicon macOS
- Homebrew `uv` upgraded to 0.11.24
- Poetry 2.1.4 in-project `.venv` at `/Users/agile/framenest/.venv`
- [ADR-0007](docs/adr/0007-settings-library.md) accepted: `pydantic-settings` as concrete settings adapter
- Compact communication protocol and English Worker report rules recorded

## Toolchain evidence

- uv: 0.11.24 (Homebrew)
- uv-managed interpreter: CPython 3.13.14 (`cpython-3.13.14-macos-aarch64-none`)
- Poetry: 2.1.4
- pytest: 9.1.1 (dev dependency only)
- Runtime dependencies: none

## Current tests

- `tests/unit/test_package_import.py` — 1 passing test

## What does not exist yet

- No configuration implementation
- No `pydantic-settings` installed
- No FastAPI application or health endpoint
- No server process
- No database
- No deployment

## Language and communication rules

- Orchestrator ↔ Cooperator: Slovak
- Worker prompts: English
- Worker reports: English, compact evidence-dense format
- Czech must not be used

## Exact next strategy

The new Orchestrator must:

1. Independently verify public `main` HEAD.
2. Start a fresh Worker session.
3. Issue one bounded test-first configuration task using `pydantic-settings`.

That task should remain separate from FastAPI and should include:

- adding and locking `pydantic-settings` through Poetry;
- centralized settings boundary outside the domain layer;
- safe `127.0.0.1` default host;
- environment-variable override;
- local ignored `.env` behavior;
- deterministic ADR-0005 precedence;
- `SecretStr` or equivalent secret-aware types;
- sanitized validation errors, including `hide_input_in_errors=True` where applicable;
- tests proving precedence and secret non-disclosure;
- no FastAPI, server startup, database, deployment, or secret-store integration.

A compact bootstrap gate inside the implementation task is sufficient unless repository or environment uncertainty requires a separate bootstrap-only task.

## Deferred work

- FastAPI application factory and health endpoint
- Database and query architecture
- Fedora deployment, systemd, SELinux, firewalld, Tailscale
- Committed non-secret configuration file format
- OS secret stores

## Closure

The old Orchestrator session stops after this handoff is verified against the public commit.

A new Orchestrator must bootstrap from [BOOT_ORCHESTRATOR.md](BOOT_ORCHESTRATOR.md), read this file, verify current `HEAD`, and issue the bounded configuration task.
