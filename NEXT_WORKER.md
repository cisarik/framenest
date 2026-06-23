# Next Worker Handoff

## 1. Handoff Purpose

The current Worker session is intentionally closing after the session-rotation handoff task.

This file transfers repository state to a future Worker session. It does not grant modification authority, Git-write permission, or an executable task.

A new Worker must receive a separate authoritative task from the Orchestrator before changing files, running broad commands, or performing Git operations.

## 2. Required Reading Order for a Fresh Worker

A fresh Worker should read repository context in this order:

1. [AGENTS.md](AGENTS.md)
2. [BOOT_WORKER.md](BOOT_WORKER.md)
3. [AP_WORKER.md](AP_WORKER.md)
4. [NEXT_WORKER.md](NEXT_WORKER.md)
5. Task-specific files named by the Orchestrator
6. The separate authoritative Worker task

The Worker may consult [AP.md](AP.md) for the full protocol, including session rotation rules, and [AP_ORCHESTRATOR.md](AP_ORCHESTRATOR.md) for role-boundary context when useful.

## 3. Repository Identity

- Repository: `https://github.com/cisarik/framenest.git`
- Verified local path used in the closing session: `/Users/agile/framenest`
- Branch: `main`
- Verified pre-handoff public SHA: `116a6f691953c325625ff2b89277444cd670f770`
- Final handoff commit: resolve from current public `HEAD` rather than guessing from this file.

## 4. Completed Work

The committed foundation now includes:

- Repository safety files and security policy.
- Analytic Programming protocol and role handbooks.
- Worker and Orchestrator bootstrap and handoff documents.
- Product foundation, normative specification, and staged roadmap.
- Architecture foundation evidence package.
- Accepted ADRs:
  - [ADR-0001](docs/adr/0001-supported-python-version.md) — CPython 3.13 (`>=3.13,<3.14`)
  - [ADR-0002](docs/adr/0002-python-environment-and-dependency-manager.md) — Poetry
  - [ADR-0003](docs/adr/0003-initial-server-api-framework.md) — FastAPI as API adapter only
  - [ADR-0004](docs/adr/0004-repository-layout.md) — hybrid staged monorepo layout
  - [ADR-0005](docs/adr/0005-configuration-strategy.md) — layered configuration strategy
- Initial scaffold decision gate complete.

## 5. Current Implementation State

No application implementation exists yet:

- No `pyproject.toml`
- No `poetry.lock`
- No `src/`
- No `tests/`
- No FastAPI application
- No server process
- No database
- No Fedora deployment
- No Tailscale configuration

The repository remains documentation-only until the first bounded scaffold task is authorized and completed.

## 6. Approved Product Invariants

- FrameNest remains local-first.
- Premium gallery and acquisition are flagship capabilities.
- The server aggregator is optional for desktop operation.
- Server-first implementation priority begins on macOS.
- Fedora NUC deployment comes after the server foundation works locally.
- Remote access direction is Tailscale-only unless superseded by an approved decision.
- External VLC comes first for full playback.
- One logical media item may have multiple physical locations.
- Portable sidecars plus local indexes are the approved metadata direction.
- Canonical tags are English.
- Provider secrets must not be distributed to ordinary clients.

## 7. Environment Evidence

Known observations from earlier audits (must be reverified before installation work):

- Apple Silicon / arm64 macOS development host
- fish shell
- Global `python3` is Python 3.14.6 at `/opt/homebrew/bin/python3`
- Global `python` command is unavailable
- FrameNest requires isolated CPython 3.13 per ADR-0001
- Poetry was observed as version 2.1.4
- pyenv was observed as available
- Global Python must not be modified

These are environment observations only. They are not approved project versions.

## 8. Remaining Unresolved Implementation Details

The following require explicit authorization during scaffold, not silent Worker choice:

- Concrete settings library selection (ADR-0005 defers the library; strategy is accepted)
- Exact `.venv` location for Cursor usability
- Exact CPython 3.13 acquisition path on the development host
- Database and query architecture
- Sidecar schema
- Media tools integration
- Authentication, streaming, and gallery implementation
- Fedora deployment, systemd, SELinux, firewalld, and Tailscale

## 9. Next Worker Expectations

The next Worker must first perform bootstrap and read-only verification in a separate authorized task.

After successful bootstrap verification, the Orchestrator will issue a separate bounded first scaffold task.

Expected next implementation direction is a test-first Python and FastAPI scaffold on macOS under isolated CPython 3.13 and Poetry.

Fedora and Tailscale work are not next.

No task is granted by this file.

No Git writes are granted by this file.

## 10. Safety State

Expected closeout state:

- Clean working tree after closeout.
- No secrets introduced.
- No package installation performed in this closeout task.
- No generated or runtime files created in this closeout task.
- Public commit verification expected from the Orchestrator.

## 11. Known Risks

- Accidentally using global Python 3.14 instead of isolated CPython 3.13.
- Oversized initial scaffold in a single task.
- Selecting unresolved libraries without Orchestrator authorization.
- Coupling domain code to FastAPI or concrete settings implementations.
- Beginning Fedora or Tailscale work before macOS scaffold evidence exists.
- A new Worker must verify current `HEAD` rather than trusting stale handoff assumptions.

## 12. Worker Session Closure

The current Worker stops after this closeout report.

No scaffold or further implementation was started in this session.

A new Worker must bootstrap from repository state and receive a fresh authoritative task.

This file may be replaced at the next intentional Worker-session close.

It must not accumulate an endless chronological log.
