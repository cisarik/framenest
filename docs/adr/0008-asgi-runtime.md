# ADR-0008: Initial ASGI Runtime

## Status

`Accepted`

## Decision Date

`2026-06-24`

## Decision Authority

The Cooperator explicitly approved **Uvicorn** as FrameNest's initial ASGI runtime after reviewing a primary-source comparison of Uvicorn, Hypercorn, and Granian. The Orchestrator recorded and enforced the decision through bounded task `FRAMENEST-CYCLE-025-ADR-0008-UVICORN-DOCS-AND-WORKER-CLOSE`. This ADR records the decision and consumes the temporary ASGI runtime evidence package that preceded it. Git history remains the archive of that evidence.

## Context

FrameNest has an accepted FastAPI presentation adapter ([ADR-0003](0003-initial-server-api-framework.md)), centralized typed settings with safe default host `127.0.0.1` ([ADR-0005](0005-configuration-strategy.md), [ADR-0007](0007-settings-library.md)), and a hybrid staged repository layout ([ADR-0004](0004-repository-layout.md)).

Verified repository state at decision time:

- `create_app()` in `src/framenest/adapters/api/application.py` returns a `FastAPI` instance, accepts injected `FrameNestSettings`, and exposes typed `GET /health` returning `{"status": "ok"}`.
- Configuration loads through `load_settings()` in `src/framenest/configuration.py` with default host `127.0.0.1`.
- In-process contract tests exercise the health endpoint without starting a network listener.
- No ASGI runtime dependency, server entrypoint, listener, process manager, deployment artifact, or systemd unit exists yet.

Initial development is on Apple Silicon macOS with CPython 3.13 and Poetry ([ADR-0001](0001-supported-python-version.md), [ADR-0002](0002-python-environment-and-dependency-manager.md), [ADR-0006](0006-macos-python-interpreter-provider.md)). The later server target is Fedora KDE on an Intel NUC. Future remote exposure direction is Tailscale Serve with the application remaining loopback-bound ([SPEC.md](../../SPEC.md)).

ADR-0003 deferred the ASGI runtime command and process manager. Primary-source research compared Uvicorn 0.49.0, Hypercorn 0.18.0, and Granian 2.7.7 (retrieval date 2026-06-24).

Related documents:

- [ADR-0003](0003-initial-server-api-framework.md)
- [ADR-0004](0004-repository-layout.md)
- [ADR-0005](0005-configuration-strategy.md)
- [SPEC.md](../../SPEC.md)
- [ROADMAP.md](../../ROADMAP.md)

## Decision

FrameNest **MUST** use **Uvicorn** as its initial ASGI runtime.

Uvicorn **MUST** remain runtime and composition infrastructure. It **MUST NOT** enter the `domain` or `application` layers.

The existing FastAPI application factory **MUST** remain independently importable and testable without starting Uvicorn.

Importing FrameNest modules **MUST NOT** start a server or open a listener.

Default binding **MUST** use the centralized settings host, whose safe default is `127.0.0.1`.

A public bind address such as `0.0.0.0` **MUST** require an explicit configuration override.

Uvicorn **MUST NOT** imply public exposure.

Future Tailscale Serve integration **MUST** preserve loopback backend binding.

Forwarded or proxy headers **MUST NOT** be trusted broadly by default. Trusted proxy configuration requires a later bounded security or deployment task.

Secrets **MUST NOT** appear in runtime arguments, logs, diagnostics, exceptions, or process metadata.

Runtime startup and shutdown behavior **MUST** be testable without leaving listeners or child processes behind.

This ADR **MUST NOT** authorize installation, startup wiring, deployment, systemd units, or Tailscale provisioning.

### Explicitly deferred implementation details

The following remain unresolved until later bounded tasks:

- exact Uvicorn version pinning;
- plain `uvicorn` versus extras such as `uvicorn[standard]`;
- CLI versus programmatic startup API;
- exact module or entrypoint filename;
- reload policy;
- worker count;
- process manager choice;
- structured logging configuration;
- systemd unit;
- trusted proxy allowlist;
- Tailscale Serve commands;
- Fedora deployment configuration.

## Alternatives Considered

### Hypercorn

**Strongest alternative.** Hypercorn supports HTTP/1, HTTP/2, WebSockets, and optional HTTP/3 draft support. Its default bind is `127.0.0.1:8000`. Primary sources consulted on 2026-06-24 did not document server-level forwarded-header handling equivalent to Uvicorn's `proxy_headers` and `forwarded-allow-ips` options. Hypercorn would be reconsidered if native HTTP/2 at the application server becomes a hard requirement without an external proxy.

### Granian

**Credible native alternative.** Granian is a Rust HTTP server for Python with ASGI/3 support, HTTP/2, platform-specific wheels for macOS arm64 and Linux x86_64, and application-layer proxy wrappers in `granian.utils.proxies`. It introduces mandatory binary wheel dependencies and operational tuning guidance that differs from Uvicorn and Gunicorn. Granian would be reconsidered if measured reliability or throughput requirements, supported by primary-source operational evidence, outweigh the additional packaging and tuning complexity for a small localhost-first service.

### Why Uvicorn

Uvicorn is proportionate for the current small, localhost-first FastAPI service because:

- FastAPI documents Uvicorn as the default ASGI server.
- Uvicorn's default host `127.0.0.1` aligns with accepted FrameNest configuration policy.
- Uvicorn provides built-in configurable trusted proxy-header handling relevant to a future Tailscale Serve topology.
- The base package is a pure-Python wheel with optional native extras, minimizing initial platform risk on macOS and Fedora.

## Primary Sources

Research retrieval date: **2026-06-24**.

| Topic | Source |
|---|---|
| Uvicorn release metadata | https://pypi.org/project/uvicorn/ |
| Uvicorn settings and proxy headers | https://www.uvicorn.dev/settings/ |
| Uvicorn README and extras | https://raw.githubusercontent.com/encode/uvicorn/master/README.md |
| Uvicorn deployment and workers | https://raw.githubusercontent.com/encode/uvicorn/master/docs/deployment/index.md |
| Uvicorn source defaults | https://raw.githubusercontent.com/encode/uvicorn/master/uvicorn/config.py |
| Hypercorn release metadata | https://pypi.org/project/hypercorn/ |
| Hypercorn README | https://raw.githubusercontent.com/pgjones/hypercorn/main/README.rst |
| Hypercorn configuration | https://raw.githubusercontent.com/pgjones/hypercorn/main/docs/how_to_guides/configuring.rst |
| Granian release metadata | https://pypi.org/project/granian/ |
| Granian README | https://raw.githubusercontent.com/emmett-framework/granian/master/README.md |
| FastAPI ASGI server guidance | https://fastapi.tiangolo.com/deployment/manually/#asgi-servers |

## Rationale

Uvicorn provides the smallest conventional path from the existing FastAPI factory to a loopback-first ASGI process while preserving domain and application independence. Its documented defaults and proxy-header controls align with FrameNest security direction without requiring immediate deployment complexity.

Keeping Uvicorn outside domain and application code preserves the adapter boundary established by ADR-0003 and ADR-0004.

## Consequences

### Positive

- Concrete ASGI runtime choice unblocks test-first startup wiring.
- Alignment with FastAPI documentation and ecosystem examples.
- Loopback-default compatibility with centralized settings.
- Built-in proxy-header controls for a future Tailscale Serve path, subject to explicit later configuration.

### Costs and risks

- Application or infrastructure code will depend on Uvicorn for process serving.
- Optional native extras may introduce platform-specific wheel considerations.
- HTTP/2 is not a native Uvicorn protocol; an external proxy or runtime change would be needed for native HTTP/2 termination at the app server.
- Proxy-header defaults require explicit security review before production remote exposure.
- Worker and shutdown semantics must be tested to avoid orphaned listeners or child processes.

### Mitigations

- Keep Uvicorn confined to runtime/infrastructure boundaries.
- Map bind host explicitly from `FrameNestSettings`.
- Defer trusted proxy allowlists, reload policy, and worker count to later bounded tasks.
- Test startup and shutdown without leaving listeners behind.

## Implementation Constraints

This ADR does **NOT**:

- install Uvicorn;
- modify `pyproject.toml` or `poetry.lock`;
- create startup modules, CLI commands, or deployment files;
- authorize systemd, Tailscale, or Fedora provisioning.

Future implementation **MUST** be test-first and **MUST** preserve in-process FastAPI contract tests without requiring a live listener for ordinary unit and contract suites.

## Verification Expectations

Future implementation must demonstrate:

- Uvicorn installed and locked through Poetry;
- startup wiring uses `FrameNestSettings.host` with safe loopback default;
- `create_app()` remains importable and testable without Uvicorn;
- no secret disclosure in runtime arguments, logs, or diagnostics;
- startup and shutdown tests leave no orphaned listeners or child processes;
- macOS execution under CPython 3.13 through Poetry;
- the same contracts later pass on Fedora.

## Revisit Triggers

Revisit this decision when any of the following occur:

- a hard requirement for native HTTP/2 termination at the application server without an external proxy;
- Uvicorn maintenance or security concerns that cannot be mitigated;
- FastAPI incompatibility with the selected Uvicorn version or startup model;
- unacceptable shutdown, worker, or proxy-header behavior in verified tests;
- Fedora packaging or wheel problems that block reliable deployment;
- measured reliability or operational evidence favoring Hypercorn or Granian for the actual FrameNest workload.

## Related Documents

- [ADR index](README.md)
- [ADR-0003](0003-initial-server-api-framework.md)
- [ADR-0004](0004-repository-layout.md)
- [ADR-0005](0005-configuration-strategy.md)
- [ADR-0007](0007-settings-library.md)
- [SPEC.md](../../SPEC.md)
- [ROADMAP.md](../../ROADMAP.md)
- [AGENTS.md](../../AGENTS.md)
