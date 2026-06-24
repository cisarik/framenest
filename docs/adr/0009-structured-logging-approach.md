# ADR-0009: Initial Structured Logging Approach

## Status

`Accepted`

## Decision Date

`2026-06-24`

## Decision Authority

The Cooperator delegated the final structured-logging choice to the Orchestrator. The Orchestrator selected **Python standard-library `logging` with a FrameNest-owned structured JSON formatter and centralized redaction boundary** after primary-source comparison of stdlib logging, `structlog`, and `python-json-logger`. The decision was recorded through bounded task `FRAMENEST-CYCLE-028-ADR-0009-STRUCTURED-LOGGING`. Transient decision-support evidence was consumed without creating a committed research artifact.

## Context

FrameNest now has centralized typed settings ([ADR-0005](0005-configuration-strategy.md), [ADR-0007](0007-settings-library.md)), a FastAPI presentation adapter ([ADR-0003](0003-initial-server-api-framework.md)), a loopback-first Uvicorn runtime ([ADR-0008](0008-asgi-runtime.md)), a runnable development server command, and health contracts verified by tests.

Verified repository state at decision time:

- `load_settings()` in `src/framenest/configuration.py` provides typed settings with `SecretStr` redaction in representations.
- `create_app()` in `src/framenest/adapters/api/application.py` exposes typed `GET /health`.
- `src/framenest/server.py` wires Uvicorn without passing a FrameNest `log_config`.
- Uvicorn's default text logging configuration remains active.
- No FrameNest logging module, formatter, filter, or structured event schema exists yet.

Structured logging remains a missing Phase 4 foundation capability ([ROADMAP.md](../../ROADMAP.md)). Logging affects security ([SPEC.md](../../SPEC.md), [SECURITY.md](../../SECURITY.md)), diagnostics, support-bundle review, systemd or container stdout/stderr capture on Fedora, Uvicorn error and access log integration, and future request or correlation identifiers.

Disclosure risks include secrets, private paths, sensitive media filenames, authorization headers, cookies, credentials, complete settings objects, raw request objects, arbitrary object representations, query strings, URLs, and unsanitized exception traces returned to ordinary API clients.

Domain and application business logic must not depend on a third-party logging framework ([ADR-0003](0003-initial-server-api-framework.md)).

Primary-source comparison retrieval date: **2026-06-24**.

Related documents:

- [ADR-0003](0003-initial-server-api-framework.md)
- [ADR-0005](0005-configuration-strategy.md)
- [ADR-0008](0008-asgi-runtime.md)
- [SPEC.md](../../SPEC.md)
- [SECURITY.md](../../SECURITY.md)
- [ROADMAP.md](../../ROADMAP.md)

## Decision

FrameNest **MUST** initially use **Python standard-library `logging`**.

Structured serialization **MUST** use a small **FrameNest-owned JSON formatter**.

Redaction and sanitization **MUST** be owned by FrameNest and applied centrally through FrameNest-owned filters and formatter logic.

Production code **MUST** use a FrameNest-owned logging boundary. Domain and application layers **MUST NOT** import a third-party logging framework.

This ADR **MUST NOT** authorize a new runtime logging dependency.

Uvicorn error and access logging **MUST** be integrated through an explicit FrameNest-owned `log_config` passed to Uvicorn configuration.

Logging infrastructure **MUST** remain outside domain and application business logic.

The implementation **MUST** support these stable structured keys:

- `event`
- `component`
- `operation`
- `error_code`
- `retryable`
- `level`
- `timestamp`
- `exception`, only when safely applicable

Optional context **MAY** later include:

- request ID;
- correlation ID;
- safe platform or tool context.

User-facing error messages **MUST** remain separate from internal diagnostic log data.

Secrets **MUST NOT** be logged, including:

- `SecretStr` contents;
- API keys and tokens;
- authorization headers;
- cookies;
- credentials;
- complete settings objects.

Raw request objects, arbitrary object representations, private paths, media filenames, query strings, and URLs **MUST NOT** be serialized by default.

Exception traces **MAY** be emitted only to internal logs after sanitization and **MUST NOT** be returned in ordinary API responses.

Formatter or serialization failure **MUST** degrade to a safe minimal fallback record and **MUST NOT** expose the rejected value.

Logging output **MUST** be deterministic enough for unit tests.

The initial application **MUST** emit logs through stdout and/or stderr for later systemd or container capture.

The application **MUST NOT** initially implement log files, rotation, retention enforcement, upload, or support-bundle generation.

Retention policy remains an operational or deployment concern, separate from event serialization.

Direct access-log duplication between Uvicorn and future application middleware **MUST** be avoided by an explicit policy decided in a later bounded task.

The logging boundary **MUST** remain replaceable without changing domain behavior.

This ADR **MUST NOT** authorize implementation, dependency installation, Uvicorn `log_config` wiring, middleware, file logging, systemd units, or remote log shipping.

### Initial stable event semantics

- `event`: stable machine-readable event name for the recorded occurrence.
- `component`: emitting subsystem, such as `configuration`, `runtime`, or `api`.
- `operation`: attempted action within the component.
- `error_code`: stable internal code when applicable; otherwise `null`.
- `retryable`: boolean when retry guidance is known; otherwise `null`.
- `level`: normalized level name derived from the logging level.
- `timestamp`: UTC timestamp in a documented machine-readable format.
- `exception`: sanitized exception metadata when present; not arbitrary exception object serialization.

This ADR does not define every future event name.

### Explicitly deferred implementation details

The following remain unresolved until later bounded tasks:

- exact module or package layout;
- exact formatter class names;
- exact filter class names;
- exact timestamp string format beyond UTC machine-readability;
- development pretty renderer;
- request or correlation middleware;
- concrete access-log suppression policy;
- per-route access-log filtering;
- exact logger names;
- exact stdout/stderr handler split;
- file logging;
- file rotation;
- retention duration;
- support-bundle generation;
- systemd configuration;
- journald field mapping;
- remote log shipping;
- OpenTelemetry;
- Sentry or another hosted service.

## Alternatives Considered

### `structlog` with standard-library integration

**Strongest alternative.** `structlog` provides a processor model, bound context, JSON rendering, and documented testing utilities while integrating with standard-library `logging` through `ProcessorFormatter` and related stdlib processors. It would still require FrameNest-owned schema enforcement and secret-redaction policy. It adds a runtime dependency and a second logging API surface that must be confined behind the FrameNest boundary. Reconsider if stdlib context propagation or Uvicorn log unification becomes disproportionately brittle in verified implementation.

### `python-json-logger`

**Thinner formatter alternative.** `python-json-logger` supplies `logging.Formatter` subclasses that encode `LogRecord` objects as JSON and supports `process_log_record()` customization. It integrates with standard-library `logging` and Uvicorn `log_config`. It does not provide the full processor or bound-context model. FrameNest would still need owned schema wrappers, redaction filters, tests, and Uvicorn integration design. Reconsider only if a maintained formatter dependency materially reduces custom code without weakening boundaries.

### Why standard-library logging

Standard-library `logging` is proportionate for the current small, localhost-first service because:

- FrameNest already depends on CPython 3.13 and accepted minimal-runtime dependency policy ([ADR-0001](0001-supported-python-version.md), [ADR-0008](0008-asgi-runtime.md)).
- Uvicorn documents `log_config` integration with `logging.config.dictConfig()` ([Uvicorn settings](https://www.uvicorn.dev/settings/#logging)).
- A FrameNest-owned formatter and filter preserve full control of schema, redaction, and replaceability without importing a third-party logging framework into production code.
- Secret redaction, API sanitization, and deterministic tests remain FrameNest responsibilities under any alternative; stdlib logging avoids adding dependency surface while those responsibilities are implemented once behind the owned boundary.

## Primary Sources

Research retrieval date: **2026-06-24**.

| Topic | Source |
|---|---|
| Python logging module | https://docs.python.org/3/library/logging.html |
| Python `Formatter` and `handleError()` behavior | https://docs.python.org/3/library/logging.html#formatter-objects |
| Uvicorn logging configuration | https://www.uvicorn.dev/settings/#logging |
| `structlog` standard-library integration | https://www.structlog.org/en/stable/standard-library.html |
| `structlog` processors | https://www.structlog.org/en/stable/processors.html |
| `structlog` testing utilities | https://www.structlog.org/en/stable/testing.html |
| `structlog` PyPI metadata | https://pypi.org/project/structlog/ |
| `python-json-logger` documentation | https://nhairs.github.io/python-json-logger/latest/ |
| `python-json-logger` PyPI metadata | https://pypi.org/project/python-json-logger/ |

## Rationale

A FrameNest-owned stdlib logging boundary aligns with accepted configuration and runtime patterns: centralized infrastructure, domain independence, minimal dependencies, and explicit security controls. JSON structured output to stdout/stderr supports later Fedora systemd or container capture without deciding retention or shipping in this decision.

Keeping logging outside domain and application code preserves the adapter and infrastructure boundaries established by ADR-0003, ADR-0004, and ADR-0008.

## Consequences

### Positive

- Zero additional logging runtime dependency.
- Full FrameNest ownership of event schema and redaction policy.
- Direct compatibility with Uvicorn `log_config` and standard-library test capture.
- Replaceable facade without changing domain behavior.

### Costs and risks

- FrameNest must implement and maintain formatter, filter, boundary API, and Uvicorn integration.
- Risk of accidentally building an oversized internal logging framework.
- Strict import and serialization boundaries are required to prevent secret or object leakage.
- Context propagation and access-log policy require careful later design.

### Mitigations

- Keep logging confined to infrastructure modules.
- Enforce allowlisted structured keys and denylisted sensitive keys centrally.
- Test redaction, formatter failure fallback, and Uvicorn integration without live listeners.
- Defer correlation middleware, file logging, retention, and remote shipping to later bounded tasks.

## Implementation Constraints

This ADR does **NOT**:

- add logging code;
- modify `pyproject.toml` or `poetry.lock`;
- wire Uvicorn `log_config` in `src/framenest/server.py`;
- create middleware, log files, or deployment artifacts;
- authorize systemd, journald mapping, or remote log services.

Future implementation **MUST** be test-first and **MUST** preserve existing health and runtime contracts without requiring a live network listener for ordinary unit tests.

## Verification Expectations

Future implementation must demonstrate:

- required structured keys in emitted JSON;
- normalized `level`;
- UTC `timestamp` shape;
- deterministic JSON suitable for unit tests;
- secret and denylisted-key redaction, including nested values and `SecretStr`;
- safe handling of arbitrary or malformed context;
- sanitized `exception` metadata without API disclosure;
- formatter failure fallback that does not expose rejected values;
- Uvicorn error and access logging integrated through FrameNest `log_config`;
- no unintended duplicate access events;
- log capture without starting a real network listener.

## Revisit Triggers

Revisit this decision when any of the following occur:

- stdlib context propagation becomes disproportionately complex;
- correlation-ID implementation becomes brittle;
- Uvicorn and application logs cannot be unified safely;
- redaction or sanitization logic becomes difficult to compose or test;
- the formatter grows into an internal general-purpose framework;
- a maintained alternative materially reduces complexity without weakening boundaries;
- operational requirements require OpenTelemetry or another structured telemetry pipeline.

## Related Documents

- [ADR index](README.md)
- [ADR-0003](0003-initial-server-api-framework.md)
- [ADR-0005](0005-configuration-strategy.md)
- [ADR-0007](0007-settings-library.md)
- [ADR-0008](0008-asgi-runtime.md)
- [SPEC.md](../../SPEC.md)
- [SECURITY.md](../../SECURITY.md)
- [ROADMAP.md](../../ROADMAP.md)
- [AGENTS.md](../../AGENTS.md)
