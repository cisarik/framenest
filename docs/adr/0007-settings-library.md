# ADR-0007: Python Settings Library

## Status

`Accepted`

## Decision Date

`2026-06-24`

## Decision Authority

The Cooperator explicitly approved `pydantic-settings` as FrameNest's concrete Python settings library and `pydantic.SecretStr` or equivalent Pydantic secret-aware types for secret values. The Orchestrator recorded and enforced the decision through bounded task `FRAMENEST-CYCLE-019`. This ADR records the decision without installing packages or implementing configuration code.

## Context

[ADR-0005](0005-configuration-strategy.md) accepted a layered configuration strategy with explicit precedence, typed validation, secret redaction, safe loopback defaults, and centralized configuration loading. ADR-0005 deferred the concrete Python settings library, committed non-secret file format, and operating-system secret stores.

FrameNest now has a minimal Poetry package scaffold with CPython 3.13.14, pytest, and a single import test. The next implementation step is a bounded configuration module, still without FastAPI, server startup, or deployment.

Related documents:

- [ADR-0005](0005-configuration-strategy.md)
- [ADR-0004](0004-repository-layout.md)
- [SPEC.md](../../SPEC.md)
- [ROADMAP.md](../../ROADMAP.md)

## Decision

FrameNest **MUST** use **`pydantic-settings`** as the concrete settings adapter.

The domain layer **MUST** remain independent of Pydantic and `pydantic-settings`.

Settings **MUST** be loaded through a centralized application or infrastructure boundary.

[ADR-0005](0005-configuration-strategy.md) precedence remains authoritative:

```text
safe program defaults
        ↓ overridden by
optional committed non-secret configuration
        ↓ overridden by
ignored local .env values
        ↓ overridden by
process environment variables
        ↓ overridden by
future approved secret-store values
```

The implementation **MUST** use typed validation.

Secrets **MUST** use `pydantic.SecretStr` or equivalent secret-aware Pydantic behavior.

Validation errors, `repr`, logs, API responses, diagnostics, and support bundles **MUST NOT** reveal secret values.

Pydantic configuration **SHOULD** enable sanitized validation errors, including `hide_input_in_errors=True` where applicable.

`.env` files **MUST** remain local and Git-ignored.

Tests **MUST** isolate environment state and **MUST NOT** depend on the developer's real `.env` file.

The default server host **MUST** remain `127.0.0.1`.

A public bind address such as `0.0.0.0` **MUST** require an explicit override.

The committed non-secret file format remains deferred.

Operating-system secret stores remain deferred.

This ADR **MUST NOT** authorize FastAPI, an API endpoint, server startup, deployment, Tailscale, systemd, SELinux, or firewalld.

Exact `pydantic-settings` and `pydantic` package versions **MUST** be selected and locked by Poetry in the later implementation task.

This ADR supplements [ADR-0005](0005-configuration-strategy.md) and does **NOT** supersede it.

## Rationale

`pydantic-settings` aligns with the accepted layered configuration model, provides typed validation, environment-variable and `.env` loading, and integrates naturally with Pydantic secret-aware types already expected by the FastAPI adapter boundary in a later phase.

Keeping Pydantic confined to application or infrastructure boundaries preserves domain independence required by ADR-0004 and ADR-0005.

## Consequences

### Positive

- Concrete library choice unblocks test-first configuration implementation.
- Typed settings with precedence and redaction can be implemented in one bounded task.
- Secret handling can use established Pydantic patterns.
- Domain code can remain framework-independent.

### Costs and limitations

- Application or infrastructure code will depend on Pydantic for settings loading.
- Exact versions remain to be locked during implementation.
- Committed configuration file format and secret stores remain deferred.

## Implementation Constraints

This ADR does **NOT**:

- install `pydantic-settings` or `pydantic`;
- modify `pyproject.toml` or `poetry.lock`;
- create configuration modules or tests;
- authorize FastAPI, server startup, or deployment.

## Verification Expectations

Future implementation must demonstrate:

- `pydantic-settings` installed and locked through Poetry;
- centralized settings loading outside the domain layer;
- ADR-0005 precedence behavior;
- default host `127.0.0.1`;
- `SecretStr` redaction in `repr`, logs, and validation output;
- `hide_input_in_errors=True` or equivalent sanitized validation errors where applicable;
- isolated test environment without developer `.env` dependence;
- domain modules do not import `pydantic` or `pydantic-settings`.

## Revisit Triggers

Revisit this decision when:

- Pydantic or `pydantic-settings` becomes unsuitable for required configuration behavior;
- secret redaction or validation-sanitization requirements cannot be met;
- a settings UI or runtime reload requires a different adapter model;
- evidence shows another library materially improves reliability without violating domain boundaries.

## Related Documents

- [ADR index](README.md)
- [ADR-0005](0005-configuration-strategy.md)
- [ADR-0004](0004-repository-layout.md)
- [SPEC.md](../../SPEC.md)
- [ROADMAP.md](../../ROADMAP.md)
- [AGENTS.md](../../AGENTS.md)
