# FrameNest

FrameNest is a local-first, privacy-conscious, cross-platform library for video and animated media, designed around ownership, organization, and a premium visual gallery experience.

## Status

FrameNest is in an early foundation, pre-alpha stage.

A minimal Poetry package scaffold exists at the repository root with centralized settings, a FastAPI application factory, a typed `GET /health` endpoint, in-process contract tests, a loopback-first Uvicorn development server, a packaged pre-alpha local web shell at `GET /`, pure-domain identity primitives, and a repository-native systemd service foundation now targeted at Ubuntu Server 24.04 on the Intel NUC6i5SYH personal production server. A bounded operator-only YouTube manual-ingestion path exists, but there is no completed media application, generalized downloader UI, desktop shell, installer, real host deployment, or supported release yet.

The repository also contains the first persistence, registry, media catalog, local media-analysis, AI suggestion-review, and quarantine upload-transport foundations: a centralized SQLite database path setting, synchronous SQLAlchemy Core engine helpers, packaged Alembic resources, explicit database commands, local device and library registry tables, durable upload-session, canonical byte-identity, duplicate-disposition, and publication-provenance and upload-to-catalog linkage tables through migration `0014`, persistent logical-media and physical-location tables, persistent display-title, plain-text description, and canonical-tag tables through migration `0006`, and an automatic built-in `Processed` workflow collection derived from durable tag saves added in migration `0007`, read-only library scan and media-analysis preview commands, explicit idempotent scan-candidate import, an imported-media catalog browser with display-title search, canonical-tag AND filters, a virtual `All media` Catalog scope, and an optional `Processed` Catalog scope, a manual browser `Edit media` dialog for persistent title, optional plain-text description, ordered tag assignment, and explicit server-provider AI assistance through NVIDIA NIM or Vercel AI Gateway. The media catalog foundation is now exposed for explicit scan-candidate import, same-origin title/description/tag API operations, same-origin catalog retrieval, browser editing of the currently persisted title, description, and tag state, and identity-only imported-media AI suggestion preview. The upload path receives untrusted bytes only into configured server quarantine, performs bounded server-side validation, and derives canonical identity from validated byte size and SHA-256 digest. The first qualifying exact identity reaches `publish_pending`; later exact copies wait in `duplicate_pending` for an explicit keep-or-discard decision. When an operator explicitly selects a safe registered publication library, lifecycle-owned recovery publishes each eligible upload to its own verified server-owned target without replacement and then cleans up quarantine. `published` remains absent from Gallery until specialized cataloging reaches `cataloged`. The current foundation does not provide arbitrary user-created collections, a general collection manager, persisted suggested filenames, covers, thumbnails, AI Draft persistence, or premium gallery data yet.

Supported runtime: CPython `>=3.13,<3.14`. Local development uses a uv-managed CPython 3.13.14 interpreter with Poetry as the dependency, environment, and lockfile manager. The initial `poetry.lock` was generated with Poetry 2.1.4. The local virtual environment lives in `.venv/` and is not committed.

## Development Setup

Preferred clone:

```text
git clone --recurse-submodules <repository>
```

If the repository was cloned without submodules:

```text
git submodule update --init --recursive
./.ap/ap doctor
```

From the repository root on Apple Silicon macOS:

```text
./framenest setup
poetry run pytest
```

`./framenest setup` idempotently uses `uv` to locate or install CPython
`3.13.14`, configures Poetry for the in-project `.venv/`, and installs the
committed dependencies. Re-run it after dependency or lockfile changes.

## Local Server

Start the browser-development application from the repository root:

```text
./framenest start
```

Default application URL: `http://127.0.0.1:8000`. Health path: `/health`.

Common launcher commands:

```text
./framenest start
./framenest start --no-open
./framenest status
./framenest open
./framenest logs
./framenest logs --follow
./framenest restart
./framenest stop
```

The launcher is browser-development tooling. It is not `FrameNest.app`, not a
Tauri shell, and not a production service. It binds the managed server to
loopback, explicitly migrates the persistent development database as part of
user-invoked `start`, waits for the real `/health` response, opens the external
default browser by default, and controls only a process proven to have been
started by the launcher.

Lower-level developer/operator commands remain available:

```text
poetry run framenest-server
poetry run framenest-db status
poetry run framenest-db migrate
poetry run framenest-catalog --help
poetry run framenest-backup --help
./framenest ai status
./framenest ai configure
./framenest ai test
./framenest backup create --help
./framenest backup verify --help
./framenest backup restore --help
./framenest youtube --help
```

The raw `poetry run framenest-server` process keeps its existing behavior: it
does not migrate automatically and runs in the foreground until stopped.

The default URL serves the packaged pre-alpha FrameNest web shell. It can confirm that the real local application server is running, load the same-origin health endpoint, list registered libraries from the local catalog, browse imported catalog media with persisted display-title search and repeated canonical-tag AND filters, open one imported medium in `Edit media`, edit or clear its persisted title, edit or clear its optional plain-text description, select up to 32 tags, explicitly create tag definitions through the hidden-key tag control, save or cancel title/description/tag changes, use compact Gallery overlay actions to edit metadata or open an available imported GIF or MP4 as the direct original media resource in a new browser context, and, when a server-side AI provider is configured, explicitly analyze the imported GIF or MP4 to produce editable current-form values. AI analysis requires user confirmation, sends up to three optimized JPEG preview frames plus bounded non-secret metadata through the FrameNest server, never uploads the original file or local path, and never saves metadata or renames a file automatically. Same-origin APIs can create/list canonical tags, get/save media display-title/description/tag metadata, retrieve a deterministic read-only media catalog page, stream identity-only media content, initiate identity-only attachment downloads, and request identity-only imported-media AI suggestions. Library registration remains available through the catalog CLI in this slice. Gallery cards display only the media surface and title; they do not display canonical tag chips, hidden-tag counters, empty tag rows, or internal Processed state. The compact card Analyze control uses the brain symbol in the top-right corner when metadata is needed. Details prioritizes playback, clickable canonical tags that activate the existing Gallery filter, and the persisted description rather than generic media-kind text or a prominent Processed panel. The media content endpoint `GET /api/media/{media_id}/locations/{location_id}/content` is same-origin, read-only, identity-only (the URL contains catalog identities, never a filesystem path), and streams registered local GIF and MP4 content with single byte-range support. The download endpoint `GET /api/media/{media_id}/locations/{location_id}/download` uses the same identity-only catalog resolution and returns `Content-Disposition: attachment` with a sanitized deterministic filename; it initiates ordinary browser download behavior only, does not know the final destination, does not prove completion or retention, and does not register trusted client-local availability. Both endpoints verify the catalog relationship between the logical media, physical location, and registered library, require location availability `available`, allow only the exact supported kind/extension pairs (`video` + `.mp4` → `video/mp4`, `animated_image` + `.gif` → `image/gif`), enforce registered-root containment with symlink escape prevention, and return sanitized errors without path disclosure. Gallery Details renders the real local GIF or MP4 content from the identity-only endpoint when an `available` location exists. Premium gallery exposure with covers, full native/VLC playback, arbitrary user-created collections, deletion/removal actions, physical rename, trusted local-copy removal, and AI Draft persistence remain future work.

Browser API paths currently include:

```text
GET /api/libraries
POST /api/libraries/{library_id}/scan-preview
POST /api/libraries/{library_id}/media-imports
GET /api/media
POST /api/canonical-tags
GET /api/canonical-tags
GET /api/media/{media_id}/metadata
PUT /api/media/{media_id}/metadata
POST /api/libraries/{library_id}/media-analysis-preview
GET /api/ai/media-suggestion-capability
GET /api/status/cloud
POST /api/libraries/{library_id}/media-suggestion-preview
POST /api/media/{media_id}/locations/{location_id}/ai-suggestion-preview
GET /api/media/{media_id}/locations/{location_id}/content
POST /api/uploads
GET /api/uploads/{upload_id}
PATCH /api/uploads/{upload_id}
POST /api/uploads/{upload_id}/complete
POST /api/uploads/{upload_id}/duplicate-resolution
DELETE /api/uploads/{upload_id}
```

The non-browser operator API additionally exposes:

```text
POST /api/operator/youtube/claims
GET /api/operator/youtube/claims/{claim_id}
POST /api/operator/youtube/claims/{claim_id}/retry
```

These API paths do not run migrations automatically and do not expose library root paths. The scan-candidate import endpoint is explicit, same-origin, idempotent by exact `(library_id, relative_path)`, and creates only minimum logical-media and physical-location records. `GET /api/media` is read-only, returns one deterministic logical-media page with total count, searches only persisted display titles using escaped SQLite `LIKE` with `NOCASE`, treats repeated canonical tag filters as AND constraints, accepts an optional `collection=processed` query parameter that restricts the page to members of the built-in `Processed` workflow collection, and returns only catalog-safe library-relative location data. Canonical tag keys are stable English identifiers. Display titles are user-editable catalog metadata and remain separate from physical filenames and paths. Metadata saves derive collection membership automatically from the saved tag list, do not accept client-supplied collection state, and do not rename, move, delete, retag, or otherwise mutate media files. Gallery cards do not display the internal `Processed` workflow label or timestamp; the built-in Processed scope and persistence semantics remain internal catalog behavior. The media-analysis preview endpoint is explicit, same-origin, read-only, local-only, stateless, provider-free, and non-persistent. It returns inline base64 PNG frames only for the lifetime of the response/displayed browser preview and sets `Cache-Control: no-store`. Upload endpoints are disabled until `FRAMENEST_UPLOAD_QUARANTINE_ROOT` names an existing absolute non-symlink quarantine directory outside registered media roots and the preview cache. They use a FrameNest-owned offset protocol with `PATCH application/offset+octet-stream`, explicit completion, fixed session expiry, configured total/chunk/free-space limits, and same-origin browser mutation checks. Default upload limits are 1 GiB per session, 8 MiB per PATCH, 24 hours fixed session TTL, and 64 MiB minimum free-space reserve. Exact duplicates are compared only after authoritative validation, and the resolution endpoint accepts only explicit keep or discard decisions for the selected opaque session. Optional automatic publication additionally requires `FRAMENEST_UPLOAD_PUBLICATION_LIBRARY_ID` to select an existing safe registered POSIX library. Without it, eligible uploads remain `publish_pending`; invalid explicit destination configuration fails closed. Publication uses opaque server-owned targets, verifies exact bytes, never overwrites an existing object, and creates no catalog or Gallery records. Upload responses remain sanitized and never expose storage keys, publication identities, destination paths, checksums, cleanup state, or server paths; duplicate-resolution responses additionally omit the matching session, byte identity, checksum, and filename.

The AI capability endpoint is same-origin, read-only, sanitized, and does not contact the provider. The browser Status modal exposes a read-only AI `Model` tab and a Cloud tab that reports the current development server as connected over local loopback. AI provider administration is a server-operator CLI boundary: `./framenest ai configure` writes only non-secret provider/model selection outside the repository, `./framenest ai status` is network-free and records a safe local status snapshot, `./framenest ai status --no-write` performs the same sanitized resolution without writing a snapshot for deployment preflight, and `./framenest ai test` is the only explicit text-only provider connection test in this slice. Configuration precedence is explicit `FRAMENEST_AI_PROVIDER_ID`/`FRAMENEST_AI_MODEL_ID` environment override, persisted non-secret server AI configuration, legacy NVIDIA compatibility when `NVIDIA_API_KEY` is present and no provider config exists, then unconfigured. An unconfigured server reports `not_configured` without fabricating a fallback provider/model. A selected provider/model with no matching credential reports `credential_unavailable` while preserving only safe provider/model diagnostics. Other sanitized states include `configured_unverified`, `available`, `authentication_failed`, `rate_limited_or_quota_exhausted`, `model_unavailable`, `provider_unreachable`, and `provider_error`. Credentials are resolved from the existing process environment first (`AI_GATEWAY_API_KEY` for Vercel AI Gateway and `NVIDIA_API_KEY` for NVIDIA NIM), then from systemd's `CREDENTIALS_DIRECTORY` using only the exact selected provider credential name. The preferred Vercel model is `google/gemini-3.1-flash-lite`; NVIDIA keeps the existing default model. The browser never configures providers, selects models, enters API keys, or receives credential values, credential prefixes, Authorization headers, raw provider responses, prompt payloads, image payloads, absolute media paths, or database paths. When configured, the imported-media AI suggestion preview endpoint requires `confirm_cloud_upload: true`, resolves only `media_id` and `location_id`, reuses local read-only media preparation, sends at most three derived JPEG frames plus bounded metadata to the active server provider, returns one validated editable suggestion with title, description, tags, and suggested filename, and performs no filesystem, catalog, or database mutation. Untagged supported Gallery cards may expose a direct `Analyze` shortcut that uses the same identity-only suggestion flow and opens the existing metadata editor with unsaved editable suggestions; tagged cards omit that shortcut. Metadata Save remains explicit, and the suggested filename is not persisted or applied. OS keychain support and explicit physical rename are separate work.

For local development, the root `./framenest` launcher optionally loads `.secrets/ai.env.fish` before `ai status`, `ai configure`, `ai test`, `start`, and `restart`. This ignored file is resolved only inside the repository root, must be a private regular file owned by the current user, and may export `NVIDIA_API_KEY` and/or `AI_GATEWAY_API_KEY`. Missing file means no local secret bootstrap, and existing exported environment values remain supported. Production AI credential support is repository source material only until a later authorized host task runs `deploy/ubuntu/fn-production-env-deploy`; the helper does not install itself into `~/.config/fish` and does not perform a provider test by default.

FrameNest-owned runtime logs are compact JSON lines written to `stderr` by the direct application process. The installed console entrypoint `.venv/bin/framenest-server` is the strict application-process boundary used by machine-readable output contract tests. Ordinary interactive termination with Ctrl+C or SIGTERM through that direct entrypoint must not emit an unstructured traceback. The browser-development launcher redirects its managed child process output to the user development log shown by `./framenest logs`.

`poetry run framenest-server` remains the normal development command, but Poetry or other launchers may additionally emit their own diagnostics outside the FrameNest logging graph. Those launcher-owned lines are not FrameNest structured log records and are not covered by the application JSON contract.

Override bind address with `FRAMENEST_HOST` and `FRAMENEST_PORT` for the raw server command. Default binding is loopback-only (`127.0.0.1`). Setting `FRAMENEST_HOST=0.0.0.0` is an explicit exposure override and is not the recommended default. The browser-development launcher enforces loopback and accepts only `FRAMENEST_PORT` for port selection.

Reload, real host deployment, Tailscale behavior, authentication, and AppArmor/UFW policy are not provided yet. A minimum catalog backup and restore-to-new-destination foundation exists through `framenest-backup` and is documented in [docs/BACKUP_AND_RECOVERY.md](docs/BACKUP_AND_RECOVERY.md); it does not copy original media, include secrets, automate retention, replace production databases, or prove a real NUC restore. A repository-native generic systemd service bundle exists under `deploy/systemd/`, the superseded Fedora guide remains in [docs/FEDORA_SERVICE.md](docs/FEDORA_SERVICE.md), and the current Ubuntu NUC deployment-readiness workflow is documented in [docs/UBUNTU_NUC_DEPLOYMENT.md](docs/UBUNTU_NUC_DEPLOYMENT.md).

## Local Database Foundation

FrameNest reads `FRAMENEST_DATABASE_PATH` through the centralized settings boundary.

Administrative and production CLI commands never read a `.env` file from the
caller's working directory. An environment file is applied only when
explicitly requested through `FRAMENEST_ENV_FILE` (or the explicit
`load_settings(env_file=...)` parameter); a missing or unreadable explicit
file fails closed with a sanitized error, and process environment variables
keep the highest precedence.

The browser-development launcher uses a persistent development database at:

```text
~/Library/Application Support/FrameNest/development/catalog.sqlite3
```

If an explicit absolute `FRAMENEST_DATABASE_PATH` is already set, the launcher
honors it. The launcher applies packaged Alembic migrations to the selected
development database during `./framenest start`.

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

Normal `poetry run framenest-server` startup does not apply migrations.
Migration remains explicit through `framenest-db`. Revisions through `0007` add
the initial catalog and metadata tables. Revisions `0008` through `0018` add
the durable upload, validation, byte-identity, duplicate, publication, catalog,
automatic-analysis, still-image, classification, movie-identification, and
analysis-history foundations. Revision `0019` adds the durable YouTube
manual-acquisition claim and provenance lifecycle without fabricating
historical claims. A resumable quarantine upload transport now exists but
remains disabled until `FRAMENEST_UPLOAD_QUARANTINE_ROOT` is configured. It
writes only to server quarantine, validates completed uploads, and gates later
exact copies in `duplicate_pending` until the user explicitly keeps or discards
that copy. With an explicitly configured safe publication library, the
application automatically reconciles and atomically publishes eligible
uploads, including cleanup retry after a durable publication. Multiprocess
publication or catalog leases/fencing and broader media-transfer product UX
remain future work. The media catalog foundation supports explicit idempotent
import from selected scan candidates, persistent display title and canonical
content tags, catalog retrieval with display-title search plus canonical-tag
AND filtering, an automatic built-in `Processed` collection entered by the
first durable tag save and cleared when all tags are removed, and browser
editing of the current title, description, and tag metadata. There is still no
arbitrary user-created collection schema, general collection manager,
suggested filenames, covers, thumbnails, gallery, sidecar, user, or
authentication schema.

## YouTube Operator Ingestion

Cookie-free public single-video ingestion is an owner-operated loopback
boundary. It is enabled only when upload quarantine, a safe publication
library, and a pre-existing private `FRAMENEST_YOUTUBE_ACQUISITION_ROOT` are
configured. The root must be absolute, non-symlinked, and disjoint from the
database, quarantine, preview cache, and every registered media root. The
server owns durable claims, one downloader subprocess at a time, restart
recovery, staging cleanup, and the handoff into the existing upload lifecycle.
The CLI never receives downloader output or filesystem paths.

```text
./framenest youtube ingest URL
./framenest youtube status CLAIM_ID
./framenest youtube retry CLAIM_ID
```

These are CachyOS development-launcher forms. On the NUC production host the
release-local `framenest-youtube` console entry point is the operator
interface under the protected production environment and explicit release
working directory; it does not require Fish. See the operator command
execution contract in
[docs/UBUNTU_NUC_DEPLOYMENT.md](docs/UBUNTU_NUC_DEPLOYMENT.md).

The server independently validates each URL. Only supported HTTPS YouTube
single-video forms are accepted; playlists, authenticated or live media,
cookies, browser profiles, sidecars, and transcoding are excluded. A successful
new item begins with `content_category=general` and
`acquisition_source=youtube_manual_claim`. Byte duplicates reuse the existing
logical medium and location without overwriting editable metadata, while the
claim retains immutable provenance. Automatic AI analysis is suppressed for
this source.

Run the deterministic no-network acceptance demonstration:

```fish
# [CachyOS / fish]
poetry run python tests/support/youtube_fake_demo.py
#------------------------------------------------------
```

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
- Local-first ownership through an authoritative FrameNest server process that
  may run locally or later on the Ubuntu NUC.
- Privacy-aware AI assistance later, after core library behavior and safety boundaries are established.
- Multiple libraries, multiple devices, and one logical media item that may exist in multiple physical locations.
- An Intel NUC personal production server direction for future authoritative
  server hosting, remote access, transfer, and archive workflows.

## Architectural Direction

The current conceptual direction is:

- A shared HTML/CSS/JavaScript UI that can run in browser development mode and later in a native system WebView.
- Tauri v2 as the accepted future desktop shell for normal local desktop operation.
- Python for domain, filesystem, downloader, metadata, server, and media-processing capabilities.
- PWA or browser access where appropriate.
- An authoritative FrameNest server process with browser, desktop, and remote
  clients.
- External VLC first for playback, with embedded libVLC considered later.
- Remote access through Tailscale-only networking rather than public internet exposure.

The accepted desktop and distributed-media direction is documentation only at this stage. No Tauri scaffold, installer, real NUC deployment, persistent gallery, transfer implementation, or deployed authoritative server exists yet.

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
- Selective media placement direction ([ADR-0022](docs/adr/0022-selective-media-placement-and-server-aggregation.md)); server-authority portions are superseded by the authoritative server/client state model ([ADR-0035](docs/adr/0035-authoritative-server-and-client-state-model.md))
- Manual-first metadata and multi-model AI draft workspace direction ([ADR-0023](docs/adr/0023-manual-first-metadata-and-multi-model-ai-drafts.md), [AI_WORKSPACE.md](AI_WORKSPACE.md))
- Manual Cover Studio and AI cover candidate direction ([ADR-0024](docs/adr/0024-cover-studio-and-ai-cover-candidates.md), [COVER_PIPELINE.md](COVER_PIPELINE.md))
- Minimum persistent media catalog foundation ([ADR-0025](docs/adr/0025-minimum-persistent-media-catalog-foundation.md))
- Explicit idempotent scan-candidate import ([ADR-0026](docs/adr/0026-explicit-idempotent-scan-candidate-import.md))
- Persistent display title and canonical tags ([ADR-0027](docs/adr/0027-persistent-display-title-and-canonical-tags.md))
- Catalog read model and search semantics ([ADR-0028](docs/adr/0028-catalog-read-model-and-search-semantics.md))
- Automatic built-in `Processed` workflow collection from durable tag saves ([ADR-0030](docs/adr/0030-automatic-processed-collection.md))
- Fedora systemd service foundation, superseded for the active deployment target by the Ubuntu NUC deployment foundation ([ADR-0031](docs/adr/0031-fedora-systemd-service-foundation.md), [ADR-0032](docs/adr/0032-ubuntu-nuc-deployment-foundation.md))
- Durable quarantine upload sessions, bounded validation, lifecycle orchestration, canonical byte identity, exact-duplicate disposition, atomic upload publication and cataloging, source-aware analysis suppression, content classification, and YouTube manual acquisition ([ADR-0037](docs/adr/0037-durable-upload-session-and-safe-ingest-foundation.md), [ADR-0038](docs/adr/0038-bounded-upload-media-validation.md), [ADR-0039](docs/adr/0039-lifecycle-owned-upload-validation-orchestration.md), [ADR-0040](docs/adr/0040-canonical-upload-byte-identity-foundation.md), [ADR-0041](docs/adr/0041-exact-byte-upload-duplicate-disposition.md), [ADR-0042](docs/adr/0042-atomic-upload-publication.md), [ADR-0043](docs/adr/0043-upload-to-catalog-transaction.md), [ADR-0044](docs/adr/0044-durable-automatic-post-catalog-analysis.md), [ADR-0045](docs/adr/0045-content-classification-and-movie-identification.md), [ADR-0046](docs/adr/0046-youtube-manual-ingestion-and-provenance.md))

Exact future frontend framework or compiled toolchain, desktop/Tauri packaging choices, IPC design, sidecar bundling, data schema, identity database encoding, deployment model, production update mechanisms, and many server operational details remain subject to later documented decisions.

## Security and Privacy Principles

FrameNest must keep secrets out of Git. Real environment files, API keys, tokens, cookies, private keys, and service credentials must not be committed.

Local desktop operation must not require a server. Remote features are expected to use Tailscale as the network boundary, and backend services must not be exposed publicly by default.

Security decisions should favor least privilege, explicit confirmation for destructive actions, and clear separation between local user data, generated runtime state, and version-controlled source files.

## Development Methodology

FrameNest development follows Analytic Programming through the pinned `.ap/`
Git submodule. The initial AP pin is:

```text
c4c69f52b9995c609248cee5d04223dbddd6da5f
```

Universal AP protocol files live under `.ap/`. FrameNest-specific operating
rules live in [AGENTS.md](AGENTS.md) outside the managed AP block. Verify AP
integration with:

```text
./.ap/ap doctor
```

AP updates are explicit, reviewed, and committed as `.ap` gitlink changes.
FrameNest does not consume AP `main` dynamically. Permanent `BOOT_*` and
`NEXT_*` files are not part of the current live repository model. Orchestrator
rotation normally uses a generated professional restoration prompt. A repository
handoff is exceptional context, not task authority, and Michal is not expected
to manually create `handout` commits by default.

Core working principles remain:

- Inspect before changing.
- Use the repository as the source of truth.
- Keep Worker tasks bounded and evidence-based.
- Make the smallest change that satisfies the authorized task.
- Verify behavior with tests or direct evidence before claiming success.
- Use public commit verification once commits are authorized.

## Development Targets

Initial development and testing targets Apple Silicon macOS.

Current server deployment preparation targets Ubuntu Server 24.04 on the Intel NUC6i5SYH personal production server. Broader cross-platform support remains an architectural requirement, and a future Ubuntu VPS remains a portability target.

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
- [`DEVELOPMENT.md`](DEVELOPMENT.md) describes the local browser-development launcher workflow.
- [`SERVER.md`](SERVER.md) records accepted optional server and NUC aggregation direction.
- [`GALLERY.md`](GALLERY.md) records accepted gallery product and UX direction.
- [`AI_WORKSPACE.md`](AI_WORKSPACE.md) records accepted manual-first metadata and multi-model AI workspace direction.
- [`COVER_PIPELINE.md`](COVER_PIPELINE.md) records accepted Cover Studio and cover candidate direction.
- [`AGENTS.md`](AGENTS.md) defines FrameNest-specific agent operating rules.
- [`.ap/README.md`](.ap/README.md), [`.ap/INTEGRATION.md`](.ap/INTEGRATION.md), and [`.ap/AP.md`](.ap/AP.md) define the pinned canonical Analytic Programming protocol integration.
- [`.ap/AP_ORCHESTRATOR.md`](.ap/AP_ORCHESTRATOR.md) defines the universal Orchestrator handbook.
- [`.ap/AP_WORKER.md`](.ap/AP_WORKER.md) defines the universal Worker handbook.
- [`docs/NUC_HOST_BASELINE.md`](docs/NUC_HOST_BASELINE.md) preserves sanitized command-observed NUC host baseline facts accepted before real FrameNest deployment.
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
- [`docs/adr/0022-selective-media-placement-and-server-aggregation.md`](docs/adr/0022-selective-media-placement-and-server-aggregation.md) records the accepted selective placement direction.
- [`docs/adr/0023-manual-first-metadata-and-multi-model-ai-drafts.md`](docs/adr/0023-manual-first-metadata-and-multi-model-ai-drafts.md) records the accepted manual-first metadata and multi-model AI draft decision.
- [`docs/adr/0024-cover-studio-and-ai-cover-candidates.md`](docs/adr/0024-cover-studio-and-ai-cover-candidates.md) records the accepted Cover Studio and AI cover candidate decision.
- [`docs/adr/0025-minimum-persistent-media-catalog-foundation.md`](docs/adr/0025-minimum-persistent-media-catalog-foundation.md) records the accepted minimum persistent media catalog foundation decision.
- [`docs/adr/0026-explicit-idempotent-scan-candidate-import.md`](docs/adr/0026-explicit-idempotent-scan-candidate-import.md) records the accepted explicit idempotent scan-candidate import decision.
- [`docs/adr/0027-persistent-display-title-and-canonical-tags.md`](docs/adr/0027-persistent-display-title-and-canonical-tags.md) records the accepted persistent display-title and canonical-tag decision.
- [`docs/adr/0028-catalog-read-model-and-search-semantics.md`](docs/adr/0028-catalog-read-model-and-search-semantics.md) records the accepted catalog read model and search semantics decision.
- [`docs/adr/0029-persistent-plain-text-media-description.md`](docs/adr/0029-persistent-plain-text-media-description.md) records the accepted persistent plain-text media description decision.
- [`docs/adr/0030-automatic-processed-collection.md`](docs/adr/0030-automatic-processed-collection.md) records the accepted automatic built-in `Processed` workflow collection decision.
- [`docs/adr/0031-fedora-systemd-service-foundation.md`](docs/adr/0031-fedora-systemd-service-foundation.md) records the historical Fedora systemd service foundation superseded by ADR-0032 for the active deployment target.
- [`docs/adr/0032-ubuntu-nuc-deployment-foundation.md`](docs/adr/0032-ubuntu-nuc-deployment-foundation.md) records the accepted Ubuntu NUC deployment foundation.
- [`docs/adr/0033-catalog-backup-and-recovery-foundation.md`](docs/adr/0033-catalog-backup-and-recovery-foundation.md) records the accepted catalog backup and recovery foundation.
- [`docs/adr/0034-canonical-analytic-programming-integration.md`](docs/adr/0034-canonical-analytic-programming-integration.md) records the accepted pinned canonical AP submodule integration.
- [`docs/adr/0035-authoritative-server-and-client-state-model.md`](docs/adr/0035-authoritative-server-and-client-state-model.md) records the accepted authoritative server/client state model.
- [`docs/adr/0042-atomic-upload-publication.md`](docs/adr/0042-atomic-upload-publication.md) records the accepted atomic upload publication decision.
- [`docs/adr/0043-upload-to-catalog-transaction.md`](docs/adr/0043-upload-to-catalog-transaction.md) records the accepted upload-to-catalog transaction.
- [`docs/adr/0044-durable-automatic-post-catalog-analysis.md`](docs/adr/0044-durable-automatic-post-catalog-analysis.md) records the accepted automatic-analysis lifecycle.
- [`docs/adr/0045-content-classification-and-movie-identification.md`](docs/adr/0045-content-classification-and-movie-identification.md) records the accepted content classification and movie-identification decision.
- [`docs/adr/0046-youtube-manual-ingestion-and-provenance.md`](docs/adr/0046-youtube-manual-ingestion-and-provenance.md) records the accepted YouTube manual-ingestion provenance lifecycle.

## Non-Goals for the Current Stage

The current stage does not provide:

- A complete mobile application.
- Cloud backup.
- A transcoding cluster.
- Embedded libVLC.
- AI-generated covers.
- Public internet exposure.
- A functional premium gallery, arbitrary user-created collections, suggested filenames, covers, thumbnails, persistent AI Drafts, persistent media scanner, or generalized downloader UI.
- Production deployment.

## License

A license has not yet been selected.

Although this repository may be publicly readable, it is not currently offered under an open-source license unless and until a license file is added.

## Contributing

Contribution guidelines are not finalized while the architecture and repository foundation are being established. Public issues and proposals should avoid sensitive information and should stay within the currently documented project scope.
