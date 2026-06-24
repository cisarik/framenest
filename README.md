# FrameNest

FrameNest is a local-first, privacy-conscious, cross-platform library for video and animated media, designed around ownership, organization, and a premium visual gallery experience.

## Status

FrameNest is in an early foundation, pre-alpha stage.

A minimal Poetry package scaffold exists at the repository root with centralized settings, a FastAPI application factory, a typed `GET /health` endpoint, in-process contract tests, and a loopback-first Uvicorn development server. There is no functional user application, database, gallery, catalog, downloader, desktop shell, installer, deployment, or supported release yet.

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

Override bind address with `FRAMENEST_HOST` and `FRAMENEST_PORT`. Default binding is loopback-only (`127.0.0.1`). Setting `FRAMENEST_HOST=0.0.0.0` is an explicit exposure override and is not the recommended default.

Reload, deployment, systemd, and Tailscale behavior are not provided yet.

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

Exact frontend framework, packaging choices, IPC design, data schema, deployment model, production update mechanisms, and many server operational details remain subject to later documented decisions.

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

## Non-Goals for the Current Stage

The current stage does not provide:

- A complete mobile application.
- Cloud backup.
- A transcoding cluster.
- Embedded libVLC.
- AI-generated covers.
- Public internet exposure.
- A functional gallery, catalog, database, or downloader.
- Production deployment.

## License

A license has not yet been selected.

Although this repository may be publicly readable, it is not currently offered under an open-source license unless and until a license file is added.

## Contributing

Contribution guidelines are not finalized while the architecture and repository foundation are being established. Public issues and proposals should avoid sensitive information and should stay within the currently documented project scope.
