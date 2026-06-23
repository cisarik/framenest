# ADR-0002: Python Environment and Dependency Manager

## Status

`Accepted`

## Decision Date

`2026-06-23`

## Decision Authority

The Cooperator explicitly selected Poetry after prior experience using it and after review of the architecture foundation evidence. The Orchestrator recorded and enforced the decision through bounded task `FRAMENEST-CYCLE-008-ADR-0002-POETRY`.

## Context

[ADR-0001](0001-supported-python-version.md) fixed the FrameNest runtime at CPython 3.13. A development Mac may still have a different global Python version installed. FrameNest requires isolated, reproducible environments so local macOS development, continuous integration, and future Fedora deployment resolve the same dependency set.

`uv`, Poetry, and a split pyenv/venv/pip workflow were compared in [ARCHITECTURE_FOUNDATION_EVIDENCE.md](../ARCHITECTURE_FOUNDATION_EVIDENCE.md). The evidence package provisionally favored `uv` and identified Poetry as the strongest alternative. The Cooperator selected Poetry based on familiarity and acceptable project fit.

Developer familiarity is a legitimate maintainability input for a small project, but it does not override validation requirements. Lockfile consistency, interpreter identity, and test evidence remain mandatory.

Related documents:

- [ADR-0001](0001-supported-python-version.md)
- [ARCHITECTURE_FOUNDATION_EVIDENCE.md](../ARCHITECTURE_FOUNDATION_EVIDENCE.md)
- [SPEC.md](../../SPEC.md)
- [ROADMAP.md](../../ROADMAP.md)

## Decision

FrameNest **MUST** use Poetry as the Python dependency manager.

FrameNest **MUST** use Poetry-managed isolated virtual environments.

FrameNest **MUST** declare Python project metadata and dependency constraints in `pyproject.toml` once project scaffolding is authorized.

FrameNest application development **MUST** commit `poetry.lock`.

Development, tests, continuous integration, and server deployment **MUST** install from the committed lockfile unless an explicitly authorized dependency-update task regenerates it.

FrameNest **MUST** use a CPython 3.13 interpreter compatible with [ADR-0001](0001-supported-python-version.md).

Poetry **MUST** be pointed at the intended interpreter explicitly when automatic detection is ambiguous.

Python packages **MUST NOT** be installed globally for FrameNest.

Project commands **SHOULD** use `poetry run ...` or execute from the Poetry-managed environment.

Shell aliases **MUST NOT** disguise an unsupported global Python version as the project runtime.

pyenv **MAY** provide a local CPython 3.13 interpreter, but it **MUST NOT** be required as the project dependency manager.

Fedora deployment **MAY** use a verified Fedora-provided CPython 3.13 interpreter or another explicitly provisioned 3.13 interpreter.

The exact Poetry 2.x tool version used for initial lock generation **MUST** be recorded by the authorized scaffold task.

Package mode and virtual-environment location remain implementation decisions until the repository-layout scaffold is accepted.

This ADR creates no configuration files.

## Rationale

Poetry reduces cognitive and operational overhead for a small project by combining dependency resolution, virtual-environment management, and lockfile generation in one workflow the Cooperator already knows.

The decision preserves the CPython 3.13 runtime boundary from ADR-0001 while adding reproducible dependency resolution through a committed `poetry.lock`. Explicit interpreter selection prevents accidental use of an unsupported global Python such as 3.14.

Poetry is compatible with local macOS development and future Fedora deployment when both environments install from the same committed lockfile and verify CPython 3.13 inside the Poetry environment.

`uv` may offer faster workflows and more integrated Python version acquisition, but speed alone does not outweigh familiarity and maintainability for the current project stage. Poetry remains an acceptable fit for a test-first server foundation with bounded complexity.

## Consequences

### Positive

- Familiar workflow for the Cooperator.
- One authority for dependency constraints and lock resolution.
- Reproducible dependencies across local, CI, and deployment environments.
- Isolated environments that do not require modifying global Python installations.
- Explicit association with CPython 3.13 through Poetry environment configuration.
- Consistent local, CI, and server commands through Poetry.

### Costs and limitations

- Poetry itself must be installed separately on each machine that builds or runs the project.
- Poetry does not by itself guarantee that CPython 3.13 is installed; interpreter acquisition remains platform-specific.
- Lockfile changes require deliberate review and test evidence.
- Future web and Tauri tooling will use separate ecosystems alongside Poetry.
- Some contributors may prefer another Python tool.
- Exact Poetry version compatibility must be documented during scaffold and dependency-update tasks.

## Rejected Alternatives

### uv

`uv` remains a credible alternative with strong integrated tooling and workspace support. It was not selected because the Cooperator preferred a familiar Poetry workflow for the initial implementation. This is not a judgment that `uv` is inferior.

### pyenv + venv + pip

This approach can be transparent and standards-based, but it separates interpreter management, environment creation, dependency resolution, and locking across several tools or manual procedures. It was not selected as the authoritative project dependency manager.

pyenv may still be used only as a local interpreter provider for CPython 3.13. It must not become a mandatory project runtime dependency.

## Lockfile Policy

- `poetry.lock` is committed for the FrameNest application.
- Lockfile updates occur only in explicit bounded tasks.
- Dependency updates require test evidence before acceptance.
- Unexplained lockfile churn must be rejected.
- Continuous integration and Fedora deployment should install from the committed lock.
- The future project must document how to verify that `pyproject.toml` and `poetry.lock` are synchronized.

## Interpreter Policy

- Runtime range remains `>=3.13,<3.14` per ADR-0001.
- The Poetry environment must report CPython 3.13.
- A global Python 3.14 installation does not need modification.
- An interpreter may be selected through an explicit path or version when Poetry detection is ambiguous.
- Commands must not silently fall back to an unsupported interpreter.
- The authorized scaffold task must test interpreter identity before installing project dependencies.

## Implementation Constraints

- This ADR creates no `pyproject.toml`.
- This ADR creates no `poetry.lock`.
- This ADR creates no virtual environment.
- This ADR installs no Python interpreter.
- This ADR changes no shell configuration.
- Repository layout and package mode remain unresolved.
- The first scaffold task must be test-first and bounded.
- macOS verification must precede Fedora deployment.
- Fedora must later reproduce the same lock-based environment.

## Verification Expectations

Future implementation must demonstrate:

- Poetry is available and its exact version is reported.
- The selected interpreter is CPython 3.13.
- The environment is isolated from global Python.
- `poetry check` succeeds.
- Lockfile consistency succeeds.
- Test dependencies are separated from runtime dependencies.
- Unit and integration tests execute through Poetry.
- Fresh-environment installation succeeds from committed metadata.
- No global package installation is needed for FrameNest development.
- macOS and Fedora use equivalent dependency resolution from the committed lock.

## Revisit Triggers

Revisit this decision when any of the following occur:

- Poetry drops required platform or Python support needed by FrameNest.
- Repeated lockfile or resolver failures block reliable development or deployment.
- Security-maintenance concerns make Poetry unsuitable.
- Substantial CI or deployment friction attributable to Poetry cannot be mitigated.
- Migration to a repository layout poorly served by Poetry.
- Evidence shows another tool materially improves reliability or reproducibility.
- Controlled reevaluation during a future Python-minor upgrade.

## Related Documents

- [ADR index](README.md)
- [ADR-0001](0001-supported-python-version.md)
- [ARCHITECTURE_FOUNDATION_EVIDENCE.md](../ARCHITECTURE_FOUNDATION_EVIDENCE.md)
- [SPEC.md](../../SPEC.md)
- [ROADMAP.md](../../ROADMAP.md)
- [AGENTS.md](../../AGENTS.md)
