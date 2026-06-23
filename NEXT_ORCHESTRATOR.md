# Next Orchestrator Handoff

## Handoff purpose

The current Orchestrator session is intentionally closing at a clean architecture checkpoint before implementation.

This file transfers session state to a fresh Orchestrator chat. It does not grant modification authority and does not replace permanent repository documents.

## Repository state

- Repository: `https://github.com/cisarik/framenest.git`
- Local path: `/Users/agile/framenest`
- Branch: `main`
- Verified pre-handoff public SHA: `116a6f691953c325625ff2b89277444cd670f770`

The final handoff commit for this session is the future current `HEAD`. Resolve it from public Git state rather than guessing inside this file.

## Completed work

The repository foundation now includes:

- Repository safety perimeter and security policy.
- Analytic Programming protocol and role handbooks.
- Product foundation ([PRODUCT.md](PRODUCT.md)), normative specification ([SPEC.md](SPEC.md)), and staged roadmap ([ROADMAP.md](ROADMAP.md)).
- Architecture foundation evidence package ([docs/ARCHITECTURE_FOUNDATION_EVIDENCE.md](docs/ARCHITECTURE_FOUNDATION_EVIDENCE.md)).
- Accepted ADRs:
  - [ADR-0001](docs/adr/0001-supported-python-version.md) — CPython 3.13
  - [ADR-0002](docs/adr/0002-python-environment-and-dependency-manager.md) — Poetry
  - [ADR-0003](docs/adr/0003-initial-server-api-framework.md) — FastAPI as API adapter only
  - [ADR-0004](docs/adr/0004-repository-layout.md) — hybrid staged monorepo layout
  - [ADR-0005](docs/adr/0005-configuration-strategy.md) — layered configuration strategy
- Initial scaffold decision gate complete.
- Session rotation handoff documents ([BOOT_ORCHESTRATOR.md](BOOT_ORCHESTRATOR.md), this file, updated [NEXT_WORKER.md](NEXT_WORKER.md)).

## Current implementation state

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

## Verified development environment

Known observations from earlier audits (must be reverified before installation work):

- Apple Silicon macOS development host
- fish shell
- Global `python3` is Python 3.14.6
- Global `python` command is unavailable
- FrameNest requires isolated CPython 3.13 per ADR-0001
- Poetry was observed as version 2.1.4
- Global Python must not be modified

These are observations, not approved project versions.

## Exact next strategy

The new Orchestrator should:

1. Verify the final public handoff commit SHA.
2. Start a completely fresh Worker session.
3. Require that Worker to read [AGENTS.md](AGENTS.md), [BOOT_WORKER.md](BOOT_WORKER.md), [AP_WORKER.md](AP_WORKER.md), and [NEXT_WORKER.md](NEXT_WORKER.md).
4. Issue a bootstrap and inspection-only task first.
5. Issue a separate bounded first scaffold task after bootstrap verification succeeds.

The first scaffold direction must be test-first and MacBook-first.

Expected scaffold goals, subject to fresh verification:

- Acquire or select CPython 3.13 without modifying global Python.
- Use Poetry per ADR-0002 and record the exact Poetry version.
- Decide `.venv` location explicitly for Cursor usability.
- Create root `pyproject.toml` and committed `poetry.lock`.
- Create `src/framenest/` package boundaries per ADR-0004.
- Create `tests/unit`, `tests/integration`, and `tests/contract`.
- Add FastAPI only as an API adapter per ADR-0003.
- Choose a concrete settings library only through explicit, evidence-backed authorization.
- Implement safe `127.0.0.1` defaults per ADR-0005.
- Implement configuration precedence and secret redaction tests.
- Implement an application factory and minimal health endpoint.
- Prove domain modules do not import FastAPI.
- Run all tests locally on Apple Silicon under Python 3.13.

The first scaffold should probably be divided into more than one bounded commit if environment provisioning and code creation are both substantial.

## Deferred work

The following remain later work, not the immediate next step:

- Database and query architecture
- Sidecar schema
- Media tools integration
- Authentication
- Streaming
- Premium gallery implementation
- Fedora deployment
- systemd hardening
- SELinux
- firewalld
- Tailscale
- Server hardening beyond loopback defaults

## Risks

- Accidentally using global Python 3.14 instead of isolated CPython 3.13.
- Oversized initial scaffold combining too many concerns in one task.
- Selecting unresolved libraries silently without Orchestrator authorization.
- Coupling domain code to FastAPI or a concrete settings library.
- Leaking secrets into Git or reports.
- Binding services publicly instead of loopback defaults.
- Beginning Fedora or Tailscale work before macOS scaffold evidence exists.

## Closure

The old Orchestrator must stop after this handoff is verified against the public commit.

A new Orchestrator must bootstrap from [BOOT_ORCHESTRATOR.md](BOOT_ORCHESTRATOR.md), read this file, verify current `HEAD`, and issue fresh bounded Worker tasks.
