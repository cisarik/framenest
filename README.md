# FrameNest

FrameNest is a local-first, privacy-conscious, cross-platform library for video and animated media, designed around ownership, organization, and a premium visual gallery experience.

## Status

FrameNest is in an early foundation, pre-alpha stage.

A minimal Poetry package scaffold exists at the repository root with centralized settings, a FastAPI application factory, a typed `GET /health` endpoint, in-process contract tests, a loopback-first Uvicorn development server, a packaged pre-alpha local web shell at `GET /`, and pure-domain identity primitives. There is no completed media application, gallery, downloader, desktop shell, installer, deployment, or supported release yet.

The repository also contains the first persistence, registry, media catalog, local media-analysis, and AI suggestion-review foundation: a centralized SQLite database path setting, synchronous SQLAlchemy Core engine helpers, packaged Alembic resources, explicit database commands, local device and library registry tables, persistent logical-media and physical-location tables through migration `0004`, read-only library scan and media-analysis preview commands, a provider-neutral NVIDIA NIM suggestion prototype, and an explicit non-persistent editable browser review for validated AI suggestions. The media catalog foundation is not yet exposed through the browser or normal catalog CLI, and it does not provide persistent scan import, editable metadata, tags, covers, thumbnails, or gallery data yet.

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

Default application URL: `http://127.0.0.1:8000`. Health path: `/health`.

The default URL serves the packaged pre-alpha FrameNest web shell. It can confirm that the real local application server is running, load the same-origin health endpoint, list registered libraries from the local catalog, run an explicit read-only library scan preview, explicitly inspect one returned candidate locally for bounded technical metadata and representative PNG frames, and, when the server-side NVIDIA credential is configured, request one editable AI suggestion review after explicit cloud-upload confirmation. Library registration remains available through the catalog CLI in this slice. Browser exposure of persistent media catalog records, gallery persistence, downloads, Settings, playback, provider selection, GUI credential entry, and metadata editing remain future work.

Read-only browser API paths currently include:

```text
GET /api/libraries
POST /api/libraries/{library_id}/scan-preview
POST /api/libraries/{library_id}/media-analysis-preview
GET /api/ai/media-suggestion-capability
POST /api/libraries/{library_id}/media-suggestion-preview
```

These API paths do not run migrations automatically and do not expose library root paths or persistent media records. The media-analysis preview endpoint is explicit, same-origin, read-only, local-only, stateless, provider-free, and non-persistent. It returns inline base64 PNG frames only for the lifetime of the response/displayed browser preview and sets `Cache-Control: no-store`.

The AI capability endpoint is same-origin, sanitized, and does not contact the provider. During this pre-alpha development slice the server composition boundary may read `NVIDIA_API_KEY` from the process environment. The browser never receives that value, credential state, key prefix, Authorization header, raw provider response, prompt payload, image payloads, absolute media path, or database path. When configured, the AI suggestion preview endpoint requires `confirm_cloud_upload: true`, reuses local read-only media preparation, sends at most three derived JPEG frames plus bounded metadata to NVIDIA NIM through the server, returns one validated editable suggestion, and performs no filesystem, catalog, or database mutation. Accepting or rejecting the browser draft is session-only. Future GUI Settings and a secret-store adapter are expected to replace the temporary process-environment credential source.

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

Normal `poetry run framenest-server` startup does not apply migrations. Migration remains explicit through `framenest-db`. Revisions through `0004` add the initial `devices`, `libraries`, `logical_media`, and `physical_media_locations` tables. The media catalog foundation is not exposed through the browser or normal catalog CLI yet, and there is still no persistent scan import, user-editable metadata, tags, covers, thumbnails, gallery, sidecar, user, or authentication schema.

## Device Catalog CLI

The `framenest-catalog` command is a development/operator boundary for local device and library registry operations. It does not migrate automatically and is not the final desktop UX. Device and library registration commands exist today; library registration does not scan directory contents.

After migrating the database and registering a device:

```text
poetry run framenest-db migrate
poetry run framenest-catalog device register --display-name "My MacBook"
poetry run framenest-catalog device list
poetry run framenest-catalog device get --id "<device-id>"
poetry run framenest-catalog library register \
  --device-id "<device-id>" \
  --display-name "Videos" \
  --root "$HOME/Videos"
poetry run framenest-catalog library list
poetry run framenest-catalog library get --id "<library-id>"
poetry run framenest-catalog library scan-preview \
  --id "<library-id>"
```

Optional bounded limits:

```text
--max-entries
--max-candidates
```

Library registration requires an already registered owning device and a database migrated to the packaged head. It checks that the supplied local root path exists and is a directory. It does not enumerate files, resolve symlinks to their targets, or scan the library contents.

`library scan-preview` requires the same migrated database and an already registered library. The preview is read-only, writes no media records, skips nested symlinks and dot-prefixed entries, classifies candidates by extension only, and may return relative candidate paths. This remains a development/operator boundary, not the final desktop UX.

`library analyze-preview` requires the same migrated database, an already registered library, and one explicit relative MP4 or GIF candidate path. The command is read-only, uses optional local `ffprobe` and `ffmpeg` executables when present, returns bounded technical metadata plus at most three exact-distinct representative PNG frames in memory only, writes no media records, leaves no extracted frame files on disk, and performs no provider or network calls. This remains a development/operator boundary, not the final desktop UX.

`library suggest-preview` requires the same migrated database, an already registered library, one explicit relative MP4 or GIF candidate path, `--confirm-cloud-upload`, and `NVIDIA_API_KEY` in the process environment. The command reuses local read-only preparation, derives bounded in-memory JPEG images from the local PNG representative frames for NVIDIA NIM transport when explicitly confirmed, returns one validated non-persistent suggestion preview, performs no catalog or filesystem mutation, and does not persist suggestions. This remains a development/operator boundary, not the final desktop UX.

```text
poetry run framenest-catalog library analyze-preview \
  --id "<library-id>" \
  --path "relative/path.mp4"
```

```text
poetry run framenest-catalog library suggest-preview \
  --id "<library-id>" \
  --path "relative/path.mp4" \
  --provider nvidia-nim \
  --model nvidia/nemotron-3-nano-omni-30b-a3b-reasoning \
  --confirm-cloud-upload
```

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

- A shared HTML/CSS/JavaScript UI that can run in browser development mode and later in a native system WebView.
- Tauri v2 as the accepted future desktop shell for normal local desktop operation.
- Python for domain, filesystem, downloader, metadata, server, and media-processing capabilities.
- PWA or browser access where appropriate.
- Local desktop catalogs plus an optional server aggregator.
- External VLC first for playback, with embedded libVLC considered later.
- Remote access through Tailscale-only networking rather than public internet exposure.

The accepted desktop and distributed-media direction is documentation only at this stage. No Tauri scaffold, installer, NUC deployment, persistent gallery, transfer implementation, or server aggregation exists yet.

Accepted implementation foundations so far:

- CPython 3.13 ([ADR-0001](docs/adr/0001-supported-python-version.md))
- Poetry ([ADR-0002](docs/adr/0002-python-environment-and-dependency-manager.md))
- `pydantic-settings` ([ADR-0007](docs/adr/0007-settings-library.md))
- FastAPI ([ADR-0003](docs/adr/0003-initial-server-api-framework.md))
- Uvicorn as the initial ASGI runtime ([ADR-0008](docs/adr/0008-asgi-runtime.md)), installed and wired for loopback-first local development
- SQLAlchemy Core and Alembic for the initial SQLite migration foundation ([ADR-0010](docs/adr/0010-initial-persistence-foundation.md)), installed and wired behind explicit database commands
- Application-owned UUIDv4 stable domain identities with category-specific pure-domain types ([ADR-0011](docs/adr/0011-stable-domain-identities.md))
- Packaged vanilla local web application delivery through the existing FastAPI process ([ADR-0017](docs/adr/0017-initial-local-web-application-delivery.md))
- Same-origin local media-analysis preview API with inline bounded base64 PNG frames ([ADR-0018](docs/adr/0018-local-media-analysis-preview-api.md))
- VLM transport JPEG derivatives and NVIDIA documented instruct mode for the suggestion prototype ([ADR-0019](docs/adr/0019-vlm-image-derivatives-and-nvidia-instruct-mode.md))
- Explicit on-demand editable AI suggestion review ([ADR-0020](docs/adr/0020-on-demand-ai-suggestion-review.md))
- Tauri v2 desktop shell direction ([ADR-0021](docs/adr/0021-tauri-desktop-shell.md))
- Selective media placement and optional server aggregation direction ([ADR-0022](docs/adr/0022-selective-media-placement-and-server-aggregation.md))
- Manual-first metadata and multi-model AI draft workspace direction ([ADR-0023](docs/adr/0023-manual-first-metadata-and-multi-model-ai-drafts.md), [AI_WORKSPACE.md](AI_WORKSPACE.md))
- Manual Cover Studio and AI cover candidate direction ([ADR-0024](docs/adr/0024-cover-studio-and-ai-cover-candidates.md), [COVER_PIPELINE.md](COVER_PIPELINE.md))
- Minimum persistent media catalog foundation ([ADR-0025](docs/adr/0025-minimum-persistent-media-catalog-foundation.md))

Exact future frontend framework or compiled toolchain, desktop/Tauri packaging choices, IPC design, sidecar bundling, data schema, identity database encoding, deployment model, production update mechanisms, and many server operational details remain subject to later documented decisions.

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
- [`DESKTOP.md`](DESKTOP.md) records accepted desktop shell architecture and UX direction.
- [`SERVER.md`](SERVER.md) records accepted optional server and NUC aggregation direction.
- [`GALLERY.md`](GALLERY.md) records accepted gallery product and UX direction.
- [`AI_WORKSPACE.md`](AI_WORKSPACE.md) records accepted manual-first metadata and multi-model AI workspace direction.
- [`COVER_PIPELINE.md`](COVER_PIPELINE.md) records accepted Cover Studio and cover candidate direction.
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
- [`docs/adr/0012-initial-device-registry.md`](docs/adr/0012-initial-device-registry.md) records the accepted initial device registry decision.
- [`docs/adr/0013-initial-library-registry.md`](docs/adr/0013-initial-library-registry.md) records the accepted initial library registry decision.
- [`docs/adr/0014-safe-library-scan-preview.md`](docs/adr/0014-safe-library-scan-preview.md) records the accepted read-only library scan preview decision.
- [`docs/adr/0015-deterministic-local-media-analysis-preparation.md`](docs/adr/0015-deterministic-local-media-analysis-preparation.md) records the accepted local media-analysis preparation decision.
- [`docs/adr/0016-provider-neutral-media-suggestions-and-nvidia-nim-prototype.md`](docs/adr/0016-provider-neutral-media-suggestions-and-nvidia-nim-prototype.md) records the accepted provider-neutral media suggestion preview decision.
- [`docs/adr/0017-initial-local-web-application-delivery.md`](docs/adr/0017-initial-local-web-application-delivery.md) records the accepted packaged local web shell delivery decision.
- [`docs/adr/0018-local-media-analysis-preview-api.md`](docs/adr/0018-local-media-analysis-preview-api.md) records the accepted same-origin local media-analysis preview API decision.
- [`docs/adr/0019-vlm-image-derivatives-and-nvidia-instruct-mode.md`](docs/adr/0019-vlm-image-derivatives-and-nvidia-instruct-mode.md) records the accepted VLM JPEG derivative and NVIDIA instruct-mode decision.
- [`docs/adr/0020-on-demand-ai-suggestion-review.md`](docs/adr/0020-on-demand-ai-suggestion-review.md) records the accepted on-demand editable AI suggestion review decision.
- [`docs/adr/0021-tauri-desktop-shell.md`](docs/adr/0021-tauri-desktop-shell.md) records the accepted Tauri v2 desktop shell direction.
- [`docs/adr/0022-selective-media-placement-and-server-aggregation.md`](docs/adr/0022-selective-media-placement-and-server-aggregation.md) records the accepted selective placement and optional server aggregation direction.
- [`docs/adr/0023-manual-first-metadata-and-multi-model-ai-drafts.md`](docs/adr/0023-manual-first-metadata-and-multi-model-ai-drafts.md) records the accepted manual-first metadata and multi-model AI draft decision.
- [`docs/adr/0024-cover-studio-and-ai-cover-candidates.md`](docs/adr/0024-cover-studio-and-ai-cover-candidates.md) records the accepted Cover Studio and AI cover candidate decision.

## Non-Goals for the Current Stage

The current stage does not provide:

- A complete mobile application.
- Cloud backup.
- A transcoding cluster.
- Embedded libVLC.
- AI-generated covers.
- Public internet exposure.
- A functional gallery, persistent scan import, metadata editor, tags, covers, thumbnails, persistent media scanner, or downloader.
- Production deployment.

## License

A license has not yet been selected.

Although this repository may be publicly readable, it is not currently offered under an open-source license unless and until a license file is added.

## Contributing

Contribution guidelines are not finalized while the architecture and repository foundation are being established. Public issues and proposals should avoid sensitive information and should stay within the currently documented project scope.
