# ADR-0006: macOS Python Interpreter Provider

## Status

`Accepted`

## Decision Date

`2026-06-23`

## Decision Authority

The new Orchestrator session successfully completed repository bootstrap against public `main` at `c9c51584695bb5e5bcb27ee6e80485f64a4293d8`. The fresh Worker completed a read-only bootstrap with PASS in bounded task `FRAMENEST-CYCLE-013`. The Cooperator explicitly approved `uv` as the CPython 3.13.14 interpreter acquisition and discovery provider on the Apple Silicon macOS development host. The Cooperator explicitly retained Poetry as the FrameNest project dependency manager, virtual-environment manager, dependency resolver, and lockfile authority. This bounded task `FRAMENEST-CYCLE-014` records the decision in the repository without provisioning, installation, or implementation. After this ADR is committed, the repository record is the durable source of truth for this decision.

## Context

[ADR-0001](0001-supported-python-version.md) fixed the FrameNest runtime at CPython 3.13 with a supported range equivalent to `>=3.13,<3.14`. [ADR-0002](0002-python-environment-and-dependency-manager.md) accepted Poetry as the sole project dependency manager, virtual-environment manager, and `poetry.lock` authority. ADR-0002 noted that interpreter acquisition remains platform-specific and that pyenv **MAY** provide a local CPython 3.13 interpreter without becoming the project dependency manager.

The Apple Silicon macOS development host has a global `python3` installation at Python 3.14.6. That global interpreter must not define the FrameNest runtime. FrameNest still requires an explicit, isolated CPython 3.13 interpreter for Poetry-managed development once provisioning is authorized.

The architecture foundation evidence compared `uv`, Poetry, and pyenv-based workflows. Poetry was accepted for dependency management. The Cooperator now approves `uv` only for macOS interpreter acquisition and discovery, not as a replacement for Poetry.

Related documents:

- [ADR-0001](0001-supported-python-version.md)
- [ADR-0002](0002-python-environment-and-dependency-manager.md)
- [ARCHITECTURE_FOUNDATION_EVIDENCE.md](../ARCHITECTURE_FOUNDATION_EVIDENCE.md)
- [SPEC.md](../../SPEC.md)
- [ROADMAP.md](../../ROADMAP.md)

## Decision

On the Apple Silicon macOS development host, FrameNest **MUST** use exact CPython **3.13.14** as the initial development interpreter patch version.

`uv` is approved **only** as the local interpreter acquisition and discovery provider on Apple Silicon macOS.

Poetry remains the only authoritative FrameNest:

- Python project dependency manager;
- virtual-environment manager;
- dependency resolver;
- `pyproject.toml` workflow authority;
- `poetry.lock` authority.

FrameNest **MUST NOT** create or commit `uv.lock`.

FrameNest **MUST NOT** use `uv add`, `uv sync`, `uv lock`, `uv venv`, or the uv project-management workflow for application dependencies.

A later authorized provisioning task **MAY** use commands equivalent to:

```text
uv python install 3.13.14
uv python find 3.13.14
```

This ADR task itself **MUST NOT** run those commands.

Poetry **MUST** later be pointed explicitly at the resolved uv-managed CPython 3.13.14 interpreter.

Poetry, not `uv`, **MUST** create and manage the FrameNest project virtual environment.

The existing global Python 3.14.6 installation **MUST NOT** be removed, replaced, aliased, or modified.

The unversioned global `python` and `python3` commands **MUST NOT** define the FrameNest runtime.

The FrameNest runtime range remains `>=3.13,<3.14` as established by ADR-0001.

Exact patch `3.13.14` is the approved initial development patch version. The supported project boundary remains the Python 3.13 minor series.

Moving to another Python 3.13 patch version requires a separate bounded maintenance task with lockfile and test evidence once the scaffold exists.

Moving to another Python minor version requires a superseding architecture decision.

Fedora deployment is **NOT** required to use `uv` merely because macOS development uses it.

Fedora **MAY** later use a verified Fedora-provided CPython 3.13 interpreter or another separately authorized CPython 3.13 provider.

macOS and Fedora **MUST** eventually use:

- CPython 3.13;
- the committed Poetry metadata;
- the committed `poetry.lock`;
- equivalent test contracts.

Identical interpreter installation mechanisms are **NOT** required across operating systems.

This decision **MUST NOT** begin Fedora provisioning, systemd work, SELinux work, firewalld work, Tailscale work, deployment, or server hardening.

This ADR supplements ADR-0001 and ADR-0002. It does **NOT** supersede ADR-0002 and does **NOT** replace Poetry.

Whether `.python-version` will later be committed remains a separate scaffold or provisioning decision. This ADR does not decide it.

The exact `uv` tool version is **NOT** established as a mandatory project-wide version by this ADR. The actual local `uv` version **MUST** be recorded during the later provisioning task.

## Rationale

Separating interpreter acquisition from dependency management preserves the Cooperator's accepted Poetry workflow while using `uv`'s integrated Python installation and discovery capabilities on macOS. This avoids modifying the host's global Python 3.14.6 installation and provides an explicit path to exact CPython 3.13.14 before Poetry creates the project environment.

Restricting `uv` to interpreter provider duties prevents dual lockfile authority, avoids `uv.lock` in the repository, and keeps `poetry.lock` as the single dependency-resolution record across macOS development, CI, and Fedora deployment.

Platform-specific interpreter providers are acceptable when both environments converge on CPython 3.13, committed Poetry metadata, and the same test contracts.

## Consequences

### Positive

- Clear split between macOS interpreter acquisition (`uv`) and project dependency management (Poetry).
- Explicit initial patch target (`3.13.14`) within the accepted 3.13 minor series.
- No modification of global Python 3.14.6 on the development host.
- No `uv.lock` or uv project-management workflow in the repository.
- Fedora may choose its own CPython 3.13 provider without mirroring macOS `uv` usage.
- Poetry remains the familiar, unchanged authority for environments and lockfiles.

### Costs and Limitations

- Developers on macOS need both `uv` (for interpreter acquisition) and Poetry (for project work) once provisioning is authorized.
- Poetry must be explicitly configured to use the uv-managed interpreter; automatic detection may be ambiguous.
- Patch upgrades within 3.13 require deliberate maintenance tasks with evidence.
- The exact `uv` version is deferred to the provisioning task.
- Whether `.python-version` is committed remains unresolved.

## Rejected or Deferred Alternatives

### pyenv as macOS interpreter provider

ADR-0002 already permitted pyenv as a local interpreter provider. `uv` is now the approved macOS provider for exact CPython 3.13.14. pyenv is not forbidden for unrelated host use but is not the approved FrameNest macOS acquisition path.

### uv as project dependency manager

Rejected for FrameNest. Poetry remains authoritative per ADR-0002. `uv` must not manage application dependencies, virtual environments, or lockfiles for this project.

### Global Python 3.14.6 as development runtime

Rejected. Global `python3` at 3.14.6 must not define the FrameNest runtime. The project uses isolated CPython 3.13 within the Poetry-managed environment.

### Fedora uv requirement

Rejected. Fedora may use Fedora-provided CPython 3.13 or another authorized provider without adopting `uv`.

### Committing `.python-version` now

Deferred to a later scaffold or provisioning decision.

## Relationship to Poetry

Poetry remains the sole FrameNest authority for:

- declaring dependencies in `pyproject.toml`;
- resolving and locking dependencies in `poetry.lock`;
- creating and managing the project virtual environment;
- running project commands through `poetry run` or the Poetry-managed environment.

`uv` supplies only the macOS CPython 3.13.14 interpreter path that Poetry will use. Poetry installs project dependencies into the Poetry-managed environment. `uv` does not install FrameNest application dependencies and does not replace `poetry install`, `poetry add`, or lockfile generation.

## macOS Development Policy

On Apple Silicon macOS:

1. Acquire CPython 3.13.14 through `uv` in a later provisioning task.
2. Discover the interpreter path through `uv python find 3.13.14` or equivalent authorized discovery.
3. Point Poetry explicitly at that interpreter.
4. Let Poetry create and manage `.venv` or the chosen virtual-environment location.
5. Install dependencies only through Poetry from committed metadata.
6. Do not modify global Python 3.14.6.
7. Do not use global `python` or `python3` as the FrameNest runtime.

## Fedora and Deployment Boundary

Fedora deployment is not required to use `uv`. Fedora **MAY** use a verified Fedora-provided CPython 3.13 interpreter or another separately authorized CPython 3.13 provider.

macOS and Fedora must converge on:

- CPython 3.13;
- committed `pyproject.toml`;
- committed `poetry.lock`;
- equivalent test contracts.

They need not use identical interpreter installation commands or tools.

This ADR does not authorize Fedora provisioning, systemd, SELinux, firewalld, Tailscale, deployment, or server hardening.

## Version and Upgrade Policy

- Supported runtime range: `>=3.13,<3.14` per ADR-0001.
- Approved initial macOS development patch: `3.13.14`.
- Another Python 3.13 patch: separate bounded maintenance task with lockfile and test evidence after scaffold exists.
- Another Python minor version: superseding ADR required.
- `uv` tool version: recorded during provisioning, not fixed by this ADR.

## Implementation Constraints

This ADR does **NOT** authorize:

- installing Python;
- changing shell configuration;
- creating `.python-version`;
- creating `.venv`;
- creating `pyproject.toml`;
- creating `poetry.lock`;
- creating `uv.lock`;
- creating `src/`;
- creating `tests/`;
- installing dependencies;
- implementing application code;
- Fedora provisioning;
- systemd, SELinux, firewalld, or Tailscale work;
- deployment or server hardening.

This ADR creates no files beyond the ADR record itself.

## Verification Expectations

Future provisioning and scaffold tasks must demonstrate:

- `uv` acquired or located CPython 3.13.14 on Apple Silicon macOS;
- the actual local `uv` version was recorded;
- Poetry was pointed explicitly at the uv-managed 3.13.14 interpreter;
- Poetry created and manages the project virtual environment;
- the Poetry environment reports CPython 3.13.14 (or the then-approved 3.13 patch);
- global Python 3.14.6 was not modified;
- no `uv.lock` exists in the repository;
- `poetry.lock` remains the dependency authority;
- dependencies install only through Poetry;
- tests run under the Poetry-managed CPython 3.13 environment;
- Fedora later reproduces equivalent behavior from committed Poetry metadata without requiring `uv`.

## Revisit Triggers

Revisit this decision when any of the following occur:

- `uv` Python management becomes unreliable or unsupported on required macOS versions;
- Poetry cannot reliably use uv-managed interpreters;
- Fedora deployment evidence requires a different interpreter acquisition model;
- CPython 3.13.14 becomes unavailable or unsuitable and a controlled patch change is needed;
- evidence shows another macOS interpreter provider materially improves reliability;
- a proposal would make `uv` the dependency manager or introduce `uv.lock`;
- a controlled Python minor-version upgrade is planned.

## Related Documents

- [ADR index](README.md)
- [ADR-0001](0001-supported-python-version.md)
- [ADR-0002](0002-python-environment-and-dependency-manager.md)
- [ARCHITECTURE_FOUNDATION_EVIDENCE.md](../ARCHITECTURE_FOUNDATION_EVIDENCE.md)
- [SPEC.md](../../SPEC.md)
- [ROADMAP.md](../../ROADMAP.md)
- [AGENTS.md](../../AGENTS.md)
