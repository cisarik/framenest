# ADR-0005: Configuration Strategy

## Status

`Accepted`

## Decision Date

`2026-06-23`

## Decision Authority

The Cooperator explicitly selected the layered configuration option after reviewing the compared strategies in the architecture foundation evidence. The Orchestrator recorded and enforced the decision through bounded task `FRAMENEST-CYCLE-011-ADR-0005-CONFIGURATION-STRATEGY`.

## Context

FrameNest begins as a local server on Apple Silicon macOS. Fedora KDE with systemd is the later server deployment target. The server must remain loopback-only by default and must not be publicly exposed without an explicit override.

Development configuration must be convenient without weakening production security. Secrets and non-secret settings require different handling. Tests require deterministic and isolated configuration that does not depend on a developer's real shell environment or personal `.env` file.

`.env` files are useful for local development but are not sufficient as the complete production model. Three configuration approaches were compared in [ARCHITECTURE_FOUNDATION_EVIDENCE.md](../ARCHITECTURE_FOUNDATION_EVIDENCE.md). The Cooperator accepted the layered strategy with explicit precedence.

Related documents:

- [ADR-0001](0001-supported-python-version.md)
- [ADR-0002](0002-python-environment-and-dependency-manager.md)
- [ADR-0003](0003-initial-server-api-framework.md)
- [ADR-0004](0004-repository-layout.md)
- [ARCHITECTURE_FOUNDATION_EVIDENCE.md](../ARCHITECTURE_FOUNDATION_EVIDENCE.md)
- [SPEC.md](../../SPEC.md)
- [ROADMAP.md](../../ROADMAP.md)

## Decision

Configuration precedence from lowest to highest authority is:

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

A higher-precedence layer **MUST** override a lower-precedence layer.

FrameNest **MUST** use explicit and deterministic configuration precedence.

Safe defaults **MUST** permit local testing without public exposure.

The default server host **MUST** be `127.0.0.1`.

A public bind address such as `0.0.0.0` **MUST NOT** be the default and **MUST** require an explicit override.

Application code **MUST NOT** scatter direct environment-variable reads throughout the codebase.

Configuration **MUST** be loaded through a centralized application or infrastructure boundary.

Configuration values **MUST** be typed and validated before use.

Invalid configuration **MUST** fail with a structured and sanitized error.

Secrets **MUST** use secret-aware types or equivalent redaction behavior.

Secret values **MUST NOT** appear in `repr`, logs, trace messages, API errors, generated diagnostics, or support bundles.

Tests **MUST** control and clean their own environment variables.

Tests **MUST NOT** rely on the developer's actual `.env` file.

`.env` files **MUST** remain local and Git-ignored.

Production deployment **MUST NOT** require a developer `.env` file.

Version-controlled configuration **MUST** contain only non-secret values.

Future server secret storage requires a separate security decision.

The domain layer **MUST** remain unaware of the concrete configuration library.

Tailscale and systemd provisioning **MUST** remain deployment concerns, not repeated privileged application-startup actions.

The exact Python configuration library, committed non-secret file format, operating-system secret store, and `.venv` location remain unresolved until the authorized scaffold task.

## Initial Scaffold Scope

The first authorized implementation may create:

- safe defaults,
- an ignored local `.env` convention,
- an example or template file containing no secrets,
- environment-variable overrides,
- typed settings validation,
- secret redaction,
- tests for precedence and safe defaults.

The first scaffold **MUST NOT** implement:

- macOS Keychain integration,
- Fedora system credentials,
- Vault or cloud secret stores,
- remote configuration services,
- dynamic runtime configuration reload,
- a settings UI,
- Tailscale provisioning.

This ADR task creates none of these files or behaviors.

## Configuration Categories

### Safe non-secret settings

Examples include host, port, log level, runtime mode, database path, temporary directory, and feature flags that contain no sensitive data. These examples are conceptual only and do not define the final schema.

### Secrets

Examples include provider API keys, authentication credentials, encryption keys, future database credentials, and external-service tokens. Secret presence and validity may be reported, but secret values must not be displayed.

### Deployment-controlled settings

Examples include service paths, systemd-provided values, storage roots, and network exposure policy. Deployment configuration must not silently weaken safe application defaults.

## Security and Redaction Rules

FrameNest **MUST NOT** place secret values in Git, normal logs, validation output returned to clients, metrics labels, or a future settings UI display.

Secret replacement and deletion **MUST NOT** reveal the current stored value.

Nested configuration objects **MUST** be handled defensively for redaction.

Startup diagnostics **MUST** be sanitized.

Transmitting diagnostics externally **MUST** require explicit opt-in.

## Testing Expectations

Future implementation must include tests proving:

- default host is `127.0.0.1`,
- defaults load without a real `.env`,
- `.env` overrides defaults,
- process environment overrides `.env`,
- invalid typed values fail clearly,
- missing required secret values fail without exposing secret content,
- secret `repr` is redacted,
- logs do not contain secret values,
- API errors do not contain secret values,
- each test restores environment state,
- configuration tests work on Apple Silicon macOS,
- the same contract suite later works on Fedora,
- application services can receive explicit settings without reading the global environment themselves.

## Rationale

The layered model provides secure defaults, deterministic precedence, local developer convenience, and a clean transition from macOS development to Fedora systemd deployment.

Separating secrets from ordinary settings and centralizing configuration loading reduces the risk of accidental public binding, secret leakage, and untestable environment coupling. The model also preserves a future extension point for approved secret-store values without requiring that complexity in the first scaffold.

## Consequences

### Positive

- Explicit and testable configuration behavior.
- Safe loopback default.
- Local `.env` convenience for development.
- Production environment-variable compatibility.
- Future secret-store extension point.
- Easier diagnosis of configuration origin when diagnostics are well designed.

### Costs and risks

- More concepts than a single `.env` file.
- Precedence must be documented and maintained.
- Secret redaction requires dedicated tests.
- Multiple layers may confuse users if diagnostics are poor.
- A future settings UI must respect the same precedence.
- Platform-specific secret stores remain unresolved.

### Mitigations

- Document precedence in code comments, ADRs, and tests.
- Provide sanitized startup diagnostics that identify source layers without exposing secrets.
- Keep the first scaffold limited to defaults, `.env`, and environment overrides.
- Defer secret-store integration to a later security decision.

## Rejected Alternatives

### Environment variables and `.env` only

Simple and valid for small services, but insufficiently expressive for the expected future desktop and server configuration evolution and secret-store integration.

### Version-controlled configuration plus environment secrets

Readable and manageable for non-secret settings, but insufficiently records the complete local-development precedence model and future secret-store layer.

Neither alternative is universally wrong; they were not selected for the current project stage.

## Explicit Non-Decisions

The following remain unresolved:

- concrete Python settings library,
- committed configuration file format,
- exact configuration schema,
- `.venv` location,
- macOS Keychain integration,
- Fedora systemd credentials mechanism,
- authentication secrets,
- encryption-key storage,
- settings UI,
- runtime reload,
- database configuration model,
- ASGI runner,
- deployment packaging.

## Implementation Constraints

- This ADR creates no configuration code.
- This ADR creates no `.env` or `.env.example`.
- This ADR creates no committed configuration file.
- This ADR installs no settings library.
- The next scaffold task may evaluate and pin a suitable library under the accepted constraints.
- The scaffold must remain test-first.
- MacBook implementation and tests come before Fedora deployment.
- No test may access real user secrets.
- Temporary files and isolated environment state must be used in tests.
- Loopback-safe behavior must be verified before the server is manually run.

## Verification Expectations

Future scaffold must demonstrate:

- a typed settings object,
- deterministic precedence,
- safe loopback default,
- isolated test configuration,
- redacted secrets,
- no direct configuration-library dependency in the domain layer,
- clean Poetry installation,
- CPython 3.13 execution,
- FastAPI application receives configuration through explicit wiring,
- no public binding without an explicit override.

## Revisit Triggers

Revisit this decision when any of the following occur:

- introduction of a settings UI,
- introduction of multiple users,
- need for runtime configuration reload,
- addition of encrypted cloud backup,
- adoption of systemd credentials,
- addition of macOS native secret storage,
- repeated configuration-origin confusion,
- secret leakage or redaction failure,
- deployment model changing materially.

## Related Documents

- [ADR index](README.md)
- [ADR-0001](0001-supported-python-version.md)
- [ADR-0002](0002-python-environment-and-dependency-manager.md)
- [ADR-0003](0003-initial-server-api-framework.md)
- [ADR-0004](0004-repository-layout.md)
- [ARCHITECTURE_FOUNDATION_EVIDENCE.md](../ARCHITECTURE_FOUNDATION_EVIDENCE.md)
- [SPEC.md](../../SPEC.md)
- [ROADMAP.md](../../ROADMAP.md)
- [AGENTS.md](../../AGENTS.md)
