# ADR-0003: Initial Server API Framework

## Status

`Accepted`

## Decision Date

`2026-06-23`

## Decision Authority

The Cooperator explicitly selected FastAPI after reviewing the architecture foundation evidence and the compared alternatives. The Orchestrator recorded and enforced the decision through bounded task `FRAMENEST-CYCLE-009-ADR-0003-FASTAPI`.

## Context

FrameNest begins server and domain development on Apple Silicon macOS. The later server target is Fedora KDE on an Intel NUC. The server must remain compatible with local-first desktop operation and must not make desktop functionality depend on server availability.

The API layer needs typed contracts, testability, OpenAPI documentation, and ASGI support for a localhost-first service that may later run under systemd and Tailscale Serve.

FastAPI, Litestar, and Django REST Framework were compared in [ARCHITECTURE_FOUNDATION_EVIDENCE.md](../ARCHITECTURE_FOUNDATION_EVIDENCE.md). Starlette was evaluated as the lower-level ASGI foundation beneath FastAPI. FastAPI was selected as the initial HTTP API adapter.

Related documents:

- [ADR-0001](0001-supported-python-version.md)
- [ADR-0002](0002-python-environment-and-dependency-manager.md)
- [ARCHITECTURE_FOUNDATION_EVIDENCE.md](../ARCHITECTURE_FOUNDATION_EVIDENCE.md)
- [SPEC.md](../../SPEC.md)
- [ROADMAP.md](../../ROADMAP.md)

## Decision

FrameNest **MUST** use FastAPI for the initial server HTTP API.

FastAPI **MUST** remain in the presentation or adapter layer.

Domain and application modules **MUST NOT** import FastAPI.

Core behavior **MUST** be testable without starting an HTTP server.

Route handlers **MUST** remain thin.

Route handlers **MUST NOT** directly contain complex filesystem operations, media processing, database orchestration, downloader execution, or destructive-operation logic.

Route handlers **SHOULD** call explicit application services or use cases.

API request and response contracts **MUST** be typed.

HTTP and validation errors **MUST** be translated into structured, sanitized responses.

Internal exceptions **MUST NOT** leak secrets, absolute private paths, or raw stack traces to ordinary clients.

The API **MUST** support dependency replacement or injection for tests.

The initial server **MUST** be configurable for loopback-only binding.

Production and remote deployment **MUST NOT** expose the application publicly by default.

OpenAPI output **MAY** be enabled for development and controlled deployment environments.

Exact API versioning, authentication, authorization, and public documentation exposure remain deferred.

Exact FastAPI, Starlette, Pydantic, ASGI server, and supporting dependency versions **MUST** be pinned by the authorized scaffold task through Poetry.

Long-running downloads, media processing, scans, and transfers **MUST NOT** be designed as unbounded synchronous work inside route handlers.

The initial background-work mechanism remains unresolved.

Starlette is accepted only as an underlying FastAPI dependency, not as the separately selected primary application framework.

This ADR creates no implementation files.

## Architectural Boundary

Intended dependency direction:

```text
HTTP / FastAPI adapters
        ↓
Application use cases
        ↓
Domain model and ports
        ↑
Infrastructure adapters
```

- The domain does not know FastAPI.
- Infrastructure does not become domain policy.
- API schemas and domain entities need not be the same objects.
- Conversion between transport and domain types must remain explicit where separation is useful.
- Avoid unnecessary architecture ceremony for trivial values.

## Initial API Expectations

The first authorized server skeleton is expected to include, without prescribing exact module filenames before the repository-layout ADR:

- an application factory,
- a health endpoint,
- structured configuration,
- structured logging,
- deterministic tests,
- API-level integration tests,
- no public binding by default,
- clean startup and shutdown lifecycle,
- clear dependency boundaries.

## Testing Expectations

Future implementation must include:

- domain unit tests without FastAPI,
- application-service tests,
- API contract tests,
- a health endpoint test,
- dependency override or replacement tests,
- structured error-response tests,
- tests that sensitive values are not returned,
- startup and shutdown lifecycle tests where applicable,
- configuration tests proving loopback is the safe default,
- macOS execution under CPython 3.13 through Poetry,
- later Fedora execution of the same contract suite.

## Rationale

FastAPI provides typed Python API contracts, OpenAPI generation, and an async-capable ASGI foundation with straightforward in-process test support through standard HTTP test clients.

For a local service with a ports-and-adapters architecture, FastAPI offers a smaller initial framework surface than Django plus Django REST Framework and a lower initial conceptual burden than the broader Litestar feature set.

Keeping FastAPI at the boundary preserves domain and application testability while still supporting the typed HTTP contracts FrameNest needs for future gallery, catalog, and media workflows.

## Consequences

### Positive

- Clear initial API framework choice.
- Typed request and response contracts.
- Generated API documentation for development and controlled deployment.
- Testable HTTP adapter layer.
- Suitable basis for localhost server development on macOS before Fedora deployment.

### Costs and risks

- Accidental coupling of domain logic to FastAPI or Pydantic transport models.
- Route handlers becoming oversized if business logic is not delegated.
- Misuse of async for blocking filesystem or media operations.
- Framework validation models leaking into the domain.
- Background task misuse before a dedicated background-work ADR exists.
- Later authorization complexity above the network boundary.

### Mitigations

- Enforce import boundaries in reviews and tests.
- Keep route handlers thin and delegate to application services.
- Run blocking work outside request handlers or behind explicit async boundaries once a background mechanism is chosen.
- Convert explicitly between API schemas and domain types where they differ.
- Defer authentication, authorization, streaming, and background jobs to later ADRs.

## Rejected Alternatives

### Litestar

Litestar is credible and capable, with a broader built-in feature set. It was not selected initially because FrameNest benefits from a narrower and more familiar initial API surface for a small project.

### Django with Django REST Framework

Django with DRF is strong for ORM-centric and admin-heavy applications. FrameNest does not yet need the full Django application framework, and selecting it now would increase the risk of premature ORM and server-centric coupling.

### Starlette directly

Starlette is a capable lower-level ASGI framework and FastAPI foundation. It was not selected as the primary application framework because FrameNest wants higher-level typed API contracts and OpenAPI integration without assembling those concerns manually.

## Explicit Non-Decisions

The following remain unresolved:

- repository layout,
- configuration library and precedence implementation,
- ORM or query layer,
- SQLite schema,
- migrations,
- ASGI runtime command and process manager,
- authentication and authorization,
- API versioning,
- background job model,
- streaming implementation,
- WebSockets or server-sent events,
- frontend framework,
- Tauri IPC,
- packaging and deployment.

## Implementation Constraints

- No FastAPI dependency is added by this ADR task.
- No `pyproject.toml` or `poetry.lock` is created or modified.
- No source or test file is created.
- First implementation must be test-first.
- First skeleton runs on macOS.
- Fedora deployment follows after local verification.
- Localhost-only behavior must be explicit and tested.
- The first scaffold must preserve the domain and API dependency boundary.

## Verification Expectations

Future implementation must demonstrate:

- FastAPI is installed through Poetry,
- exact versions are locked,
- the application factory can be imported in tests,
- the health endpoint works through an in-process test client,
- domain tests do not import FastAPI,
- error responses are sanitized,
- server configuration defaults to loopback,
- tests run under CPython 3.13,
- clean installation from `poetry.lock`,
- the same contracts later pass on Fedora.

## Revisit Triggers

Revisit this decision when any of the following occur:

- framework security or maintenance concerns,
- major incompatibility with required streaming behavior,
- unacceptable testing or lifecycle limitations,
- repeated domain coupling to FastAPI,
- future multi-user requirements not served by the current adapter model,
- evidence that another framework materially improves reliability,
- a major architectural change that invalidates the API adapter boundary.

## Related Documents

- [ADR index](README.md)
- [ADR-0001](0001-supported-python-version.md)
- [ADR-0002](0002-python-environment-and-dependency-manager.md)
- [ARCHITECTURE_FOUNDATION_EVIDENCE.md](../ARCHITECTURE_FOUNDATION_EVIDENCE.md)
- [SPEC.md](../../SPEC.md)
- [ROADMAP.md](../../ROADMAP.md)
- [AGENTS.md](../../AGENTS.md)
