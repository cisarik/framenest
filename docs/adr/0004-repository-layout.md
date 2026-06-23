# ADR-0004: Repository Layout

## Status

`Accepted`

## Decision Date

`2026-06-23`

## Decision Authority

The Cooperator explicitly selected the hybrid staged monorepo option after reviewing the three compared layout strategies in the architecture foundation evidence. The Orchestrator recorded and enforced the decision through bounded task `FRAMENEST-CYCLE-010-ADR-0004-REPOSITORY-LAYOUT`.

## Context

FrameNest begins with a real Python server and domain implementation. CPython 3.13, Poetry, and FastAPI are already accepted through [ADR-0001](0001-supported-python-version.md), [ADR-0002](0002-python-environment-and-dependency-manager.md), and [ADR-0003](0003-initial-server-api-framework.md).

Future product direction includes a shared web UI and a Tauri desktop shell. Creating a complete empty multi-application monorepo now would add premature complexity. Using a root Python project without explicit future boundaries could cause a disruptive migration when web and desktop work begins.

The hybrid staged layout supports real Python work now and reserves conceptual boundaries for later expansion without relocating the initial server package.

Related documents:

- [ADR-0001](0001-supported-python-version.md)
- [ADR-0002](0002-python-environment-and-dependency-manager.md)
- [ADR-0003](0003-initial-server-api-framework.md)
- [ARCHITECTURE_FOUNDATION_EVIDENCE.md](../ARCHITECTURE_FOUNDATION_EVIDENCE.md)
- [SPEC.md](../../SPEC.md)
- [ROADMAP.md](../../ROADMAP.md)

## Decision

The initial Python project **MUST** live at repository root.

Project metadata **MUST** use root `pyproject.toml`.

Dependency locking **MUST** use root `poetry.lock`.

Importable source **MUST** live under `src/framenest/`.

Tests **MUST** live under root `tests/`.

Documentation **MUST** remain under `docs/`.

Architecture decision records **MUST** remain under `docs/adr/`.

Repository governance documents **MUST** remain at repository root.

Poetry package mode **MUST** be used.

The import package name **MUST** be `framenest`.

Package imports **MUST** be resolved through the installed project environment rather than ad-hoc `sys.path` modification.

Future web and desktop components **MUST NOT** be scaffolded before they contain real implementation work.

Future web and desktop components **SHOULD** use top-level `web/` and `desktop/` boundaries unless later evidence justifies another ADR.

The Python server is **NOT** placed under `apps/server/` initially.

A disruptive future move of the Python project into another top-level directory **SHOULD** be avoided unless justified by a later ADR.

Runtime-generated files, databases, caches, downloaded media, secrets, and virtual environments **MUST NOT** become tracked source layout.

### Conceptual initial layout

```text
pyproject.toml
poetry.lock
src/framenest/
tests/
docs/
```

This ADR does not create these paths. The authorized scaffold task creates only justified files and directories.

### Conceptual internal package boundaries

```text
src/framenest/
├── domain/
├── application/
├── adapters/
│   └── api/
└── infrastructure/
```

### Conceptual test boundaries

```text
tests/
├── unit/
├── integration/
└── contract/
```

These names define architectural boundaries. The directories are not created by this ADR task.

### Intended dependency direction

```text
adapters/api
    ↓
application
    ↓
domain
    ↑
infrastructure adapters implementing domain/application ports
```

## Python Package Boundaries

### `domain`

**Responsibilities:**

- entities,
- value objects,
- domain rules,
- domain services where needed,
- ports or protocols representing required capabilities,
- domain-specific errors.

**Forbidden dependencies:**

- FastAPI,
- Starlette,
- HTTP concepts,
- database implementations,
- filesystem implementation details,
- subprocess invocation,
- platform-specific code.

`domain` **MUST NOT** import infrastructure adapters. It **MUST** remain usable without HTTP, ASGI, database, filesystem, yt-dlp, FFmpeg, VLC, or Tailscale integrations.

### `application`

**Responsibilities:**

- use cases,
- orchestration,
- transaction boundaries where later applicable,
- calls to domain ports,
- application-level result and error handling.

`application` **MAY** depend on `domain`. It **MUST NOT** depend directly on FastAPI route objects.

### `adapters/api`

**Responsibilities:**

- FastAPI application and routers,
- request and response transport models,
- HTTP status mapping,
- dependency wiring,
- structured and sanitized API errors.

`adapters/api` **MAY** depend on FastAPI and application interfaces.

### `infrastructure`

**Responsibilities:**

- SQLite implementations,
- filesystem adapters,
- media probing,
- downloader integrations,
- VLC integration,
- OS metadata and tag adapters,
- external service adapters.

Most infrastructure modules will be implemented only in later phases. Infrastructure implementations **MUST NOT** become domain policy.

Transport schemas and domain entities **MAY** be separate.

## Test Layout

### `tests/unit`

- pure domain and application tests,
- no network,
- no real user filesystem,
- no external media executables.

### `tests/integration`

- controlled combinations of infrastructure and application components,
- temporary directories and temporary databases,
- no destructive access to real user libraries.

### `tests/contract`

- FastAPI and API behavior,
- health endpoint,
- structured errors,
- configuration safety,
- adapter contracts,
- later cross-platform behavior.

Tests **MAY** use fixtures and support modules without turning the test layout into a copy of production structure.

## Import and Dependency Rules

- `domain` must remain framework-independent.
- Adapters depend inward; circular dependencies are forbidden.
- Infrastructure implementations satisfy inward-facing contracts.
- Application services must remain callable without HTTP.
- API schemas should not automatically become domain models.
- Absolute imports from the `framenest` package should be preferred.
- Runtime path manipulation must not be the standard import mechanism.

## Future Web and Desktop Expansion

- `web/` may later contain the shared web or PWA frontend.
- `desktop/` may later contain Tauri-specific desktop integration.
- These directories are not created until authorized implementation work begins.
- JavaScript package manager and workspace tooling remain undecided.
- Python domain and server code remains independently testable.
- Future frontend clients communicate through explicit contracts rather than importing Python modules.

## Package Mode Resolution

This decision resolves the package-mode question deferred by ADR-0002:

- FrameNest will initially use Poetry package mode.
- The importable Python package will be `framenest`.
- Source code will live under `src/framenest/`.
- Tests will import the installed package through the Poetry-managed environment.

Poetry virtual-environment location remains unresolved until the authorized scaffold task.

## Rationale

The hybrid staged monorepo is the smallest useful repository layout today. It avoids empty monorepo ceremony while recording how future web and desktop components will be added without relocating the initial Python package.

The `src` layout, Poetry package mode, and explicit `domain` / `application` / `adapters` / `infrastructure` boundaries support clear dependency direction, predictable imports, test organization, and domain independence from FastAPI and infrastructure. This remains maintainable for a small project when boundaries are enforced in reviews and tests.

## Consequences

### Positive

- Direct path to the first server scaffold.
- Conventional Python package structure.
- Predictable imports through the installed package.
- Clear test categories.
- Future web and desktop boundaries reserved conceptually.
- Reduced premature multi-ecosystem tooling.

### Costs and risks

- Repository root will later contain multiple ecosystems.
- Future root tooling may become more complex.
- Boundaries can decay without enforcement.
- The initial Python project remains visually dominant at root.
- Future web tooling may require additional workspace decisions.
- Adapter and infrastructure separation may be overused for trivial code.

### Mitigations

- Do not create empty `web/` or `desktop/` directories.
- Enforce import boundaries in tests and review.
- Keep application services HTTP-free and test them directly.
- Revisit layout only through a superseding ADR with evidence.

## Rejected Alternatives

### Python-first root without explicit staged-monorepo rules

Simple and fast to start, but insufficiently records how future web and desktop components will be added without disruptive migration.

### Full application-oriented monorepo immediately

Provides explicit multi-application organization under paths such as `apps/server/`, but would create premature directories, tooling, and maintenance before those applications exist.

Neither alternative is universally wrong; they were not selected for the current project stage.

## Explicit Non-Decisions

The following remain unresolved:

- local configuration strategy,
- settings library,
- `.venv` location,
- concrete module filenames,
- ORM or query layer,
- database schema,
- migration framework,
- ASGI server command and process manager,
- background jobs,
- frontend framework,
- JavaScript package manager,
- Tauri workspace structure,
- CI provider,
- deployment packaging.

## Implementation Constraints

- This ADR creates no scaffold.
- The configuration ADR must be accepted before scaffold.
- The scaffold task must create only justified directories and files.
- Empty `web/` and `desktop/` directories must not be created.
- Initial scaffold must be test-first.
- MacBook verification precedes Fedora deployment.
- Repository-root paths must remain portable.
- Generated and runtime artifacts must remain ignored.

## Verification Expectations

Future scaffold must demonstrate:

- root `pyproject.toml`,
- committed `poetry.lock`,
- package import from `src/framenest/`,
- tests running through Poetry,
- no manual `sys.path` injection required,
- `domain` imports no FastAPI,
- application behavior can be tested without HTTP,
- FastAPI adapter can be tested in-process,
- temporary filesystem use for integration tests,
- no future app directories created without real implementation.

## Revisit Triggers

Revisit this decision when any of the following occur:

- multiple independently released Python applications are required,
- web and desktop tooling require a different workspace boundary,
- repository-root tooling becomes unmanageable,
- package publishing requirements change,
- significant CI isolation needs emerge,
- evidence shows that moving the server under `apps/server/` materially improves maintainability,
- domain boundaries prove too fragmented or too weak.

## Related Documents

- [ADR index](README.md)
- [ADR-0001](0001-supported-python-version.md)
- [ADR-0002](0002-python-environment-and-dependency-manager.md)
- [ADR-0003](0003-initial-server-api-framework.md)
- [ARCHITECTURE_FOUNDATION_EVIDENCE.md](../ARCHITECTURE_FOUNDATION_EVIDENCE.md)
- [SPEC.md](../../SPEC.md)
- [ROADMAP.md](../../ROADMAP.md)
- [AGENTS.md](../../AGENTS.md)
