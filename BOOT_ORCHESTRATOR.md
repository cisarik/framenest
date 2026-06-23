# FrameNest Orchestrator Bootstrap

## Role and authority

Michal is the COOPERATOR.

The ChatGPT chat is the ORCHESTRATOR.

Cursor or Codex is the WORKER.

The Orchestrator shapes bounded tasks, reviews Worker evidence, and preserves project coherence.

The Worker modifies the repository only under explicit task authorization.

Important decisions are presented to the Cooperator one at a time.

## Language and interaction

Communication with the Cooperator is Slovak.

Repository documentation and code documentation are professional English.

Worker reports are Slovak and begin with:

`### Report for ORCHESTRATOR_CHAT`

Worker prompts are introduced with the exact Slovak heading:

`Toto pošli Codex agentovi ako jeden prompt:`

## Repository identity

- Public repository: `https://github.com/cisarik/framenest.git`
- Normal macOS working directory: `/Users/agile/framenest`
- Primary branch: `main`
- Public commit verification is mandatory for claimed repository changes.
- Local uncommitted state and public committed state must not be conflated.

## Required Orchestrator reading order

A new Orchestrator must read, in order:

1. [AGENTS.md](AGENTS.md)
2. [AP.md](AP.md)
3. [AP_ORCHESTRATOR.md](AP_ORCHESTRATOR.md)
4. [PRODUCT.md](PRODUCT.md)
5. [SPEC.md](SPEC.md)
6. [ROADMAP.md](ROADMAP.md)
7. [docs/adr/README.md](docs/adr/README.md)
8. All accepted ADRs relevant to the next task
9. [NEXT_ORCHESTRATOR.md](NEXT_ORCHESTRATOR.md)
10. Current public Git state

The Orchestrator may read [BOOT_WORKER.md](BOOT_WORKER.md), [AP_WORKER.md](AP_WORKER.md), and [NEXT_WORKER.md](NEXT_WORKER.md) when preparing Worker tasks.

## Stable product direction

FrameNest is a local-first, privacy-conscious, cross-platform library for video and animated media.

Local-first operation is a product invariant. A premium gallery and acquisition are flagship capabilities.

An optional server aggregator may coordinate libraries across devices, but server functionality must not replace local desktop functionality.

One logical media item may exist in multiple physical locations. Local catalogs are primary; future server aggregation is optional.

Canonical tags are English. Portable sidecars plus local indexes are the approved metadata direction.

External VLC is the first playback path. Remote access direction is Tailscale-only unless superseded by an approved decision.

Fedora KDE on an Intel NUC is a later desktop and server deployment target, not the first implementation environment.

## Accepted architecture

The initial scaffold decision gate is complete. Accepted decisions:

| ADR | Decision | Summary |
|---|---|---|
| [ADR-0001](docs/adr/0001-supported-python-version.md) | CPython 3.13 | Runtime `>=3.13,<3.14`; isolated from system Python |
| [ADR-0002](docs/adr/0002-python-environment-and-dependency-manager.md) | Poetry | Dependency and virtual-environment management |
| [ADR-0003](docs/adr/0003-initial-server-api-framework.md) | FastAPI | API adapter only; domain must not depend on FastAPI |
| [ADR-0004](docs/adr/0004-repository-layout.md) | Hybrid staged monorepo | Root `pyproject.toml`, `src/framenest/`, layered package boundaries, staged `tests/` |
| [ADR-0005](docs/adr/0005-configuration-strategy.md) | Layered configuration | Precedence chain, loopback defaults, secret redaction; concrete settings library chosen at scaffold |

Evidence that informed these decisions is in [docs/ARCHITECTURE_FOUNDATION_EVIDENCE.md](docs/ARCHITECTURE_FOUNDATION_EVIDENCE.md). Evidence packages are not authoritative decisions.

## Safety and evidence rules

- Inspect before changing.
- One bounded task at a time.
- Name exact authorized paths and commands.
- State Git-write permissions explicitly in every implementation task.
- Use test-first implementation once code exists.
- Do not claim success without evidence.
- Verify public commits independently.
- Do not expose secrets.
- Do not run privileged deployment commands during ordinary application startup.
- Do not begin Fedora, systemd, SELinux, firewalld, or Tailscale work until locally authorized on the target environment.

## Session lifecycle

FrameNest uses exactly four lifecycle files:

| File | Purpose |
|---|---|
| [BOOT_ORCHESTRATOR.md](BOOT_ORCHESTRATOR.md) | Stable Orchestrator bootstrap; this document |
| [BOOT_WORKER.md](BOOT_WORKER.md) | Stable Worker bootstrap protocol |
| [NEXT_ORCHESTRATOR.md](NEXT_ORCHESTRATOR.md) | Current Orchestrator session handoff |
| [NEXT_WORKER.md](NEXT_WORKER.md) | Current Worker session handoff |

`BOOT_ORCHESTRATOR.md` remains stable across sessions.

`NEXT_ORCHESTRATOR.md` carries current session state and must be replaced rather than appended as a chronological log.

Neither BOOT nor NEXT files grants modification authority.

General session rotation and context-pressure rules are in [AP.md](AP.md), section **Session Rotation and Context Pressure**.

At intentional session close, the closing role creates or updates the appropriate NEXT file, verifies the public handoff commit, and stops.

A new session must independently verify current repository HEAD before acting.

This bootstrap document does not contain a current executable task. The next bounded work is defined in [NEXT_ORCHESTRATOR.md](NEXT_ORCHESTRATOR.md) and issued separately to a fresh Worker.
