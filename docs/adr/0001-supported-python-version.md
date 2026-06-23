# ADR-0001: Supported Python Version

## Status

`Accepted`

## Decision Date

`2026-06-23`

## Decision Authority

The Cooperator explicitly accepted this decision after review of the architecture foundation evidence. The Orchestrator recorded and enforced the decision through bounded task `FRAMENEST-CYCLE-007-ADR-0001-PYTHON-313`.

## Context

FrameNest begins server and domain development on Apple Silicon macOS. Fedora KDE on an Intel NUC is the later server deployment target. The project requires reproducible behavior across local development, automated tests, continuous integration, and deployment.

A development host may have a global Python installation that differs from the project runtime. That global interpreter must not define FrameNest's supported runtime. The project will use an isolated project environment once tooling is accepted.

Python 3.12, 3.13, and 3.14 were compared in [ARCHITECTURE_FOUNDATION_EVIDENCE.md](../ARCHITECTURE_FOUNDATION_EVIDENCE.md). The evidence package provisionally recommended Python 3.13. The Cooperator accepted CPython 3.13 as the initial supported runtime.

Related documents:

- [ARCHITECTURE_FOUNDATION_EVIDENCE.md](../ARCHITECTURE_FOUNDATION_EVIDENCE.md)
- [SPEC.md](../../SPEC.md)
- [ROADMAP.md](../../ROADMAP.md)

## Decision

FrameNest **MUST** target **CPython 3.13**.

Future project metadata **MUST** constrain supported Python to an equivalent of `requires-python = ">=3.13,<3.14"` unless a later ADR explicitly supersedes this decision.

Tests **MUST** execute under Python 3.13.

Continuous integration and Fedora deployment verification **MUST** use Python 3.13 explicitly.

Project commands **MUST** run through the isolated project environment once project tooling exists. They must not depend on whichever Python version happens to be global on a developer machine.

Global Python installations on a host **MUST NOT** be altered merely to satisfy this repository.

Documentation **MUST NOT** instruct users to alias a different global Python version to pretend it is Python 3.13.

The exact 3.13 patch release **MAY** advance within the 3.13 series after tests pass. Exact patch pinning is an implementation concern for accepted project tooling.

Supporting another Python minor version requires a deliberate later decision and compatibility evidence recorded in a superseding ADR.

Python 3.12 and Python 3.14 are not initially supported project runtime targets.

This ADR does not select uv, Poetry, pyenv, venv workflow, or any other environment or dependency manager.

## Rationale

Python 3.13 offers a practical balance between upstream support runway and ecosystem maturity for a test-first server foundation.

Compared with Python 3.14, 3.13 presents lower immediate compatibility risk while the project has no implementation yet to validate wheels and native dependencies on the newest runtime.

Compared with Python 3.12, 3.13 remains in active bugfix support and aligns with the Fedora 42 default `python3` evidence collected in the foundation evidence package.

The decision creates a stable runtime boundary for forthcoming dependency-manager, API-framework, and repository-layout decisions without requiring changes to a developer's global Python installation. A host with Python 3.14 installed globally remains compatible because FrameNest will use an isolated project interpreter.

## Consequences

### Positive

- Stable target for dependency and framework evaluation.
- Reproducible test and runtime boundary across macOS development and Fedora deployment.
- No dependence on whichever Python version is global on a machine.
- Clear Fedora deployment requirement: verify CPython 3.13 explicitly.

### Costs

- The project environment must install or locate CPython 3.13 when tooling is implemented.
- Developers whose global Python is not 3.13 must use the isolated project interpreter.
- A future upgrade ADR will be required before changing the supported minor version.
- Dependencies must be checked against Python 3.13 compatibility.

## Rejected Alternatives

### Python 3.12

Not selected initially because it is already in upstream security-only support with a shorter remaining support runway than 3.13. It remains a credible choice when maximum ecosystem conservatism outweighs runway, but it is not the accepted initial target.

### Python 3.14

Not selected initially because it is the newest runtime and carries higher ecosystem lag risk for a project that has not yet implemented media, database, and packaging dependencies. It remains viable for a later deliberate upgrade once compatibility evidence exists.

## Implementation Constraints

No implementation tooling has yet been accepted.

The next architecture decision concerns Python environment and dependency management.

This ADR task does not create `.python-version`, `pyproject.toml`, a lockfile, or `.venv`.

Future scaffolding **MUST** include local macOS tests under Python 3.13.

Future Fedora deployment **MUST** run the same verified test contracts under Python 3.13.

## Verification Expectations

Future implementation must demonstrate:

- the project environment interpreter reports Python 3.13,
- tests fail clearly when run with an unsupported minor version where feasible,
- unit and integration tests run on Apple Silicon macOS under Python 3.13,
- CI uses Python 3.13,
- Fedora deployment verification uses Python 3.13,
- no test depends on a developer's global Python 3.14 installation.

## Revisit Triggers

Revisit this decision when any of the following occur:

- Python 3.13 nears end of upstream support.
- A mandatory dependency drops Python 3.13 support.
- Security or platform constraints make 3.13 impractical.
- Fedora deployment evidence shows Python 3.13 incompatibility for required packages.
- Evidence shows another version materially improves reliability without violating project constraints.
- The project prepares for a controlled Python minor-version upgrade.

## Related Documents

- [ADR index](README.md)
- [ARCHITECTURE_FOUNDATION_EVIDENCE.md](../ARCHITECTURE_FOUNDATION_EVIDENCE.md)
- [SPEC.md](../../SPEC.md)
- [ROADMAP.md](../../ROADMAP.md)
- [AGENTS.md](../../AGENTS.md)
