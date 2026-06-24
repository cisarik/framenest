# FrameNest

FrameNest is a local-first, privacy-conscious, cross-platform library for video and animated media, designed around ownership, organization, and a premium visual gallery experience.

## Status

FrameNest is in an early foundation, pre-alpha stage.

A minimal Poetry package scaffold exists at the repository root with centralized settings, a FastAPI application factory, a typed `GET /health` endpoint, in-process contract tests, a loopback-first Uvicorn development server, and pure-domain identity primitives. There is no functional user application, media catalog schema, gallery, downloader, desktop shell, installer, deployment, or supported release yet.

The repository also contains the first persistence foundation: a centralized SQLite database path setting, synchronous SQLAlchemy Core engine helpers, packaged Alembic resources, and explicit database commands. This is not a media catalog schema and does not provide library scanning or gallery data yet.

Supported runtime: CPython `>=3.13,<3.14`. Local development uses a uv-managed CPython 3.13.14 interpreter with Poetry as the dependency, environment, and lockfile manager. The initial `poetry.lock` was generated with Poetry 2.1.4. The local virtual environment lives in `.venv/` and is not committed.

## Development Setup

From the repository root on Apple Silicon macOS:

```fish
set UV_MANAGED_PYTHON (uv python find --managed-python --no-config --no-project 3.13.14)
env POETRY_VIRTUALENVS_IN_PROJECT=true poetry env use "$UV_MANAGED_PYTHON"
env POETRY_VIRTUALENVS_IN_PROJECT=true poetry install
env POETRY_VIRTUALENVS_IN_PROJECT=true poetry run pytest
```

## Local Server

Start the loopback-first development server:

```text
poetry run framenest-server
```

Default URL: `http://127.0.0.1:8000`. Health path: `/health`.

FrameNest-owned runtime logs are compact JSON lines written to `stderr` by the direct application process. The installed console entrypoint `.venv/bin/framenest-server` is the strict application-process boundary used by machine-readable output contract tests. Ordinary interactive termination with Ctrl+C or SIGTERM through that direct entrypoint must not emit an unstructured traceback.

`poetry run framenest-server` remains the normal development command, but Poetry or other launchers may additionally emit their own diagnostics outside the FrameNest logging graph. Those launcher-owned lines are not FrameNest structured log records and are not covered by the application JSON contract.

Override bind address with `FRAMENEST_HOST` and `FRAMENEST_PORT`. Default binding is loopback-only (`127.0.0.1`). Setting `FRAMENEST_HOST=0.0.0.0` is an explicit exposure override and is not the recommended default.

Reload, deployment, systemd, and Tailscale behavior are not provided yet.

## Local Database Foundation

FrameNest reads `FRAMENEST_DATABASE_PATH` through the centralized settings boundary.

The current default is temporary development behavior:

```text
Path(tempfile.gettempdir()) / "framenest-development" / "catalog.sqlite3"
```

This fallback is intentionally outside the repository and is not the final production storage policy. Persistent deployments are expected to set an explicit absolute `FRAMENEST_DATABASE_PATH`. `~` is expanded before validation. Relative paths are rejected with sanitized errors.

Inspect migration status without creating a missing database:

```text
poetry run framenest-db status
```

Explicitly upgrade the configured database to the packaged Alembic head:

```text
poetry run framenest-db migrate
```

Normal `poetry run framenest-server` startup does not apply migrations. The initial packaged revision is `0001` and creates no media catalog, library, device, location, gallery, sidecar, user, or authentication schema.

## Structured Logging

The direct FrameNest server process emits one compact JSON object per application-owned log line to `stderr`.

Logging uses a FrameNest-owned JSON formatter and centralized redaction boundary. Uvicorn access logging is initially disabled for privacy. There are no log files, rotation, retention enforcement, remote shipping, or correlation middleware yet.

Launcher, interpreter, shell, supervisor, and future service-manager diagnostics remain separate output sources. Captured combined `stderr` from a wrapped command must not automatically be treated as entirely application-generated.

## Product Vision

FrameNest is intended to help people acquire, organize, browse, and maintain personal video and animated-media libraries while keeping local ownership central.

The current approved product direction includes:

- A visually premium gallery as a flagship experience.
- Media acquisition through replaceable source adapters.
- Local-first catalog ownership, with portable sidecar metadata and local indexes.
- Privacy-aware AI assistance later, after core library behavior and safety boundaries are established.
- Multiple libraries, multiple devices, and one logical media item that may exist in multiple physical locations.
- An optional Intel NUC server aggregator for cross-device library coordination.

## Architectural Direction

The current conceptual direction is:

- A shared web-first UI that can later be hosted by a desktop shell.
- A Tauri desktop shell for local desktop operation.
- Python for domain, filesystem, downloader, metadata, server, and media-processing capabilities.
- PWA or browser access where appropriate.
- Local desktop catalogs plus an optional server aggregator.
- External VLC first for playback, with embedded libVLC considered later.
- Remote access through Tailscale-only networking rather than public internet exposure.

Accepted implementation foundations so far:

- CPython 3.13 ([ADR-0001](docs/adr/0001-supported-python-version.md))
- Poetry ([ADR-0002](docs/adr/0002-python-environment-and-dependency-manager.md))
- `pydantic-settings` ([ADR-0007](docs/adr/0007-settings-library.md))
- FastAPI ([ADR-0003](docs/adr/0003-initial-server-api-framework.md))
- Uvicorn as the initial ASGI runtime ([ADR-0008](docs/adr/0008-asgi-runtime.md)), installed and wired for loopback-first local development
- SQLAlchemy Core and Alembic for the initial SQLite migration foundation ([ADR-0010](docs/adr/0010-initial-persistence-foundation.md)), installed and wired behind explicit database commands
- Application-owned UUIDv4 stable domain identities with category-specific pure-domain types ([ADR-0011](docs/adr/0011-stable-domain-identities.md))

Exact frontend framework, packaging choices, IPC design, data schema, identity database encoding, deployment model, production update mechanisms, and many server operational details remain subject to later documented decisions.

## Security and Privacy Principles

FrameNest must keep secrets out of Git. Real environment files, API keys, tokens, cookies, private keys, and service credentials must not be committed.

Local desktop operation must not require a server. Remote features are expected to use Tailscale as the network boundary, and backend services must not be exposed publicly by default.

Security decisions should favor least privilege, explicit confirmation for destructive actions, and clear separation between local user data, generated runtime state, and version-controlled source files.

## Development Methodology

FrameNest development follows Analytic Programming and the Coordinator Protocol:

- Inspect before changing.
- Use the repository as the source of truth.
- Keep Worker tasks bounded and evidence-based.
- Make the smallest change that satisfies the authorized task.
- Verify behavior with tests or direct evidence before claiming success.
- Use public commit verification once commits are authorized.

## Development Targets

Initial development and testing targets Apple Silicon macOS.

Later server deployment targets a Fedora KDE environment on an Intel NUC. Broader cross-platform support remains an architectural requirement, but platform details will be refined through documented decisions.

## Documentation Map

The full documentation set will be added in later bounded cycles. Expected future documents include architecture decision records, development workflow guidance, security notes, local runtime layout, testing strategy, and deployment notes.

Current foundation files:

- [`.gitignore`](.gitignore) defines the first repository safety perimeter.
- [`.gitattributes`](.gitattributes) defines cross-platform text and binary handling.
- [`.editorconfig`](.editorconfig) defines baseline editor formatting.
- [`SECURITY.md`](SECURITY.md) defines the initial pre-alpha security policy.
- [`PRODUCT.md`](PRODUCT.md) defines the approved product vision, users, outcomes, experience principles, capabilities, and non-goals.
- [`SPEC.md`](SPEC.md) defines the initial normative product and system requirements.
- [`ROADMAP.md`](ROADMAP.md) defines the staged evidence-based development roadmap.
- [`AGENTS.md`](AGENTS.md) defines FrameNest-specific agent operating rules.
- [`AP.md`](AP.md) defines the general Analytic Programming protocol.
- [`AP_ORCHESTRATOR.md`](AP_ORCHESTRATOR.md) defines the Orchestrator operating handbook.
- [`AP_WORKER.md`](AP_WORKER.md) defines the Worker operating handbook.
- [`BOOT_ORCHESTRATOR.md`](BOOT_ORCHESTRATOR.md) defines the stable FrameNest Orchestrator bootstrap.
- [`BOOT_WORKER.md`](BOOT_WORKER.md) defines the stable FrameNest Worker bootstrap.
- [`NEXT_ORCHESTRATOR.md`](NEXT_ORCHESTRATOR.md) carries the current Orchestrator session handoff.
- [`NEXT_WORKER.md`](NEXT_WORKER.md) carries the current Worker session handoff.
- [`docs/ARCHITECTURE_FOUNDATION_EVIDENCE.md`](docs/ARCHITECTURE_FOUNDATION_EVIDENCE.md) collects primary-source evidence for the first architecture decisions. It is not an ADR and does not approve any option.
- [`docs/adr/README.md`](docs/adr/README.md) indexes accepted architecture decision records.
- [`docs/adr/0001-supported-python-version.md`](docs/adr/0001-supported-python-version.md) records the accepted CPython 3.13 runtime decision.
- [`docs/adr/0002-python-environment-and-dependency-manager.md`](docs/adr/0002-python-environment-and-dependency-manager.md) records the accepted Poetry dependency and environment management decision.
- [`docs/adr/0003-initial-server-api-framework.md`](docs/adr/0003-initial-server-api-framework.md) records the accepted FastAPI initial server API framework decision.
- [`docs/adr/0004-repository-layout.md`](docs/adr/0004-repository-layout.md) records the accepted hybrid staged monorepo repository layout decision.
- [`docs/adr/0005-configuration-strategy.md`](docs/adr/0005-configuration-strategy.md) records the accepted layered configuration strategy decision.
- [`docs/adr/0006-macos-python-interpreter-provider.md`](docs/adr/0006-macos-python-interpreter-provider.md) records the accepted macOS interpreter provider decision.
- [`docs/adr/0007-settings-library.md`](docs/adr/0007-settings-library.md) records the accepted `pydantic-settings` decision.
- [`docs/adr/0008-asgi-runtime.md`](docs/adr/0008-asgi-runtime.md) records the accepted Uvicorn ASGI runtime decision.
- [`docs/adr/0009-structured-logging-approach.md`](docs/adr/0009-structured-logging-approach.md) records the accepted structured logging decision.
- [`docs/adr/0010-initial-persistence-foundation.md`](docs/adr/0010-initial-persistence-foundation.md) records the accepted SQLAlchemy Core and Alembic SQLite persistence foundation decision.
- [`docs/adr/0011-stable-domain-identities.md`](docs/adr/0011-stable-domain-identities.md) records the accepted stable domain identity decision.

## Non-Goals for the Current Stage

The current stage does not provide:

- A complete mobile application.
- Cloud backup.
- A transcoding cluster.
- Embedded libVLC.
- AI-generated covers.
- Public internet exposure.
- A functional gallery, media catalog schema, library scanner, or downloader.
- Production deployment.

## License

A license has not yet been selected.

Although this repository may be publicly readable, it is not currently offered under an open-source license unless and until a license file is added.

## Contributing

Contribution guidelines are not finalized while the architecture and repository foundation are being established. Public issues and proposals should avoid sensitive information and should stay within the currently documented project scope.
