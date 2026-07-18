# FrameNest Specification

## 1. Document Status and Scope

FrameNest is in foundation-stage pre-alpha development. This document defines normative requirements for future implementation.

A minimal Poetry package foundation exists with centralized configuration, a FastAPI application factory, a typed health endpoint, a loopback-first Uvicorn runtime dependency and startup command, a minimal SQLAlchemy Core/Alembic SQLite migration foundation, pure domain identity primitives, local device and library registries, a minimum persistent logical-media and physical-location catalog foundation, persistent display-title and canonical-tag core, catalog retrieval with display-title search and canonical-tag AND filtering, a manual browser `Current` metadata workspace for display-title and ordered canonical-tag assignment, an automatic built-in `Processed` workflow collection derived from durable tag saves, read-only library scan preview, explicit idempotent scan-candidate import, local media-analysis preview, provider-neutral NVIDIA/Vercel suggestion preview, VLM JPEG derivative transport, a server-operated AI configuration and diagnostics CLI, a packaged local web shell, an explicit editable browser AI suggestion review, a trusted-loopback quarantine upload path with bounded validation, exact-duplicate disposition, and optional atomic publication to an explicitly selected server-owned library, and a repository-native systemd service foundation now targeted at Ubuntu Server 24.04 on the Intel NUC6i5SYH personal production server. There is no completed user application, upload-to-catalog linkage, arbitrary user-created collections, a general collection manager, suggested filenames, covers, thumbnails, persistent AI Drafts, real host deployment, trusted-proxy configuration, OS keychain support, systemd credentials, or Tailscale integration yet. Unresolved architecture choices remain subject to future architecture decision records.

This specification translates approved direction from [PRODUCT.md](PRODUCT.md), [README.md](README.md), [AGENTS.md](AGENTS.md), and [SECURITY.md](SECURITY.md) into requirements. It does not select frameworks, schemas, protocols, or packaging tools.

## 2. Normative Language

The terms MUST, MUST NOT, SHOULD, SHOULD NOT, and MAY are normative.

MUST means the requirement is mandatory.

MUST NOT means the behavior is prohibited.

SHOULD means the requirement is expected unless a documented reason justifies an alternative.

SHOULD NOT means the behavior is discouraged unless a documented reason justifies it.

MAY means the behavior is optional.

## 3. Product Invariants

FrameNest MUST remain local-first.

Local desktop gallery, metadata, search, and playback MUST remain usable without
a remote server where their required local server process, records, and media
are available.

The premium gallery and media-acquisition workflows MUST both remain flagship capabilities.

A remote server or public cloud service MUST NOT replace local ownership or
make local desktop operation unusable when the needed local server process,
local catalog/cache records, and local media are available.

Remote FrameNest communication direction MUST remain Tailscale-only unless explicitly superseded by an approved decision.

Backends MUST NOT be publicly exposed by default.

Provider secrets MUST NOT be distributed to ordinary clients.

Destructive operations MUST require safeguards.

The FrameNest catalog MUST remain authoritative over projected native OS tags.

## 4. Core Domain Concepts

A logical media item is the conceptual media record shown to users and connected to metadata, covers, tags, series relationships, and zero or more physical locations.

A physical media location is one known stored copy or representation of a logical media item on a device, library, storage volume, and path.

A device is a machine or storage-capable host that may contain libraries, provide playback, or participate in transfer and availability reporting.

A library is an independently registered collection root with stable identity and policy.

A storage volume is a mounted or otherwise addressable storage unit with capacity, availability, filesystem, and ownership context where available.

Standalone media is a logical item that is not modeled as an episode in a series.

A series groups related episodes and may carry inherited metadata.

An episode is media that belongs to a series relationship.

A canonical tag is an English stable identifier used by FrameNest for organization.

A source platform is structured metadata describing where media originated and is also projected as the final system tag in directory display names.

A cover is a user-visible representative image for standalone media, an episode, or a series.

A cover candidate is a proposed cover source or generated image that has not
yet replaced the accepted cover.

A derived thumbnail is a reproducible cache artifact derived from a durable source.

A sidecar manifest is portable durable metadata stored near media where feasible.

A FrameNest server process is the authoritative API and state boundary for the
catalog and server-owned state. It may run locally on the same device as a
desktop client or later on the Ubuntu NUC.

A client is a browser, desktop shell, local NUC browser, or remote interface
that requests state and actions from the FrameNest server API.

A local catalog/cache is local server or client-side state used for local
operation and offline visibility. Its exact authority, rebuild, and
synchronization semantics remain governed by ADR-0035 and future decisions.

A transfer is a copy, move, or related operation between locations.

An availability state describes whether a device, library, storage volume, or physical location is currently reachable and usable.

A desktop shell is the native application boundary that hosts the FrameNest UI, supervises the local backend, and provides narrowly scoped native capabilities.

## 5. Stable Identity Requirements

FrameNest MUST define stable identities for logical media, physical locations, devices, libraries, storage volumes, and series where applicable.

FrameNest entity identities MUST initially use application-owned RFC 9562 UUID version 4 values as accepted by [ADR-0011](docs/adr/0011-stable-domain-identities.md).

FrameNest MUST represent identity categories with category-specific domain types rather than interchangeable raw UUID aliases.

The canonical external identity representation MUST be lowercase hyphenated UUID text.

FrameNest identity strings MUST be treated as opaque values. They MUST NOT be used to infer entity type, creation time, filesystem location, database row position, source platform, content hash, or semantic ordering.

Filesystem paths alone MUST NOT serve as globally stable media identity.

Database row IDs, SQLite row order, filesystem paths, filenames, source-platform IDs, content hashes, and device-local counters MUST NOT serve as FrameNest entity identity.

The final database encoding, catalog schema, sidecar schema, synchronization representation, hashing, deduplication, and identity reconciliation rules remain unresolved.

## 6. Logical Media and Physical Locations

One logical media item MAY have zero or more physical locations.

The initial persistent logical media foundation MUST represent one conceptual
media item with a stable `MediaId` and one supported media kind. Persistent
display-title and canonical-tag metadata are stored separately from physical
locations.

Initial supported persisted media kinds are `video` and `animated_image`.

The initial persistent physical media-location foundation MUST represent one
known file location inside one registered library with a stable
`MediaLocationId`, the owning `MediaId`, the owning `LibraryId`, one normalized
library-relative path, an availability state, optional observed file size in
bytes, optional observed modification time in integer nanoseconds, and
non-negative row timestamps.

Initial supported physical-location availability states are `available`,
`offline`, `missing`, `unverified`, and `archived`.

Persisted physical-location paths MUST be library-relative, slash-separated,
non-empty, free of NUL characters, free of empty path segments, and free of `.`
or `..` traversal segments. Domain and repository logic MUST NOT resolve,
traverse, or inspect the filesystem to validate these persisted paths.

The physical filename MUST be derived from the final component of the relative
path and MUST NOT be duplicated in a separate persisted filename column.

The owning device MUST be determined through the registered library. Physical
media-location records MUST NOT duplicate `device_id`.

The exact `(library_id, relative_path)` pair MUST be unique. Two different
logical media items MUST NOT claim the same registered library-relative
location.

Foreign keys from physical locations to logical media and libraries MUST use
restrictive or no-action semantics. Destructive cascading deletion is not part
of the initial catalog foundation.

The gallery SHOULD normally present one logical item rather than every duplicate independently.

Users MUST be able to inspect all known copies.

Future physical-location extensions SHOULD record storage volume and richer
verification state where available.

Offline locations MUST remain known and MUST be visibly unavailable.

Duplicate handling MUST distinguish identical media from unrelated files with similar names.

No final known valid copy MAY be deleted without explicit policy and confirmation.

## 7. Libraries and Storage

FrameNest MUST support multiple independent libraries.

Each library MUST have stable identity, a root directory, and an owning device.

Libraries and storage volumes SHOULD report online/offline state and writable/read-only state where available.

FrameNest SHOULD report capacity, free space, filesystem, and mount information where available.

The interface SHOULD provide `All libraries` filtering.

Transfers SHOULD provide storage-impact previews before execution.

FrameNest MUST NOT destructively initialize storage without explicit approval.

## 8. Standalone and Series Model

Standalone media MAY use a dedicated directory.

Series MAY share a directory.

Episodes SHOULD inherit series-level content tags where appropriate.

Users MUST be able to correct series detection.

Merge and split migrations MUST update paths, metadata, covers, OS tags, catalog records, and physical locations safely.

Migrations MUST be previewable and verifiable.

## 9. Canonical Tagging

Canonical tags MUST use stable English identifiers.

Persistent canonical tag keys are lowercase English ASCII slugs. The key is the
stable catalog identity. A canonical tag display name is separate presentation
text. A UUID tag identity MUST NOT be introduced for this slice.

Persistent display title is user-editable catalog metadata. It MUST remain
separate from physical filename and library-relative path, and saving or
clearing it MUST NOT mutate media files.

Initial display values SHOULD be English.

Content tags MUST be distinct from system and source metadata.

The source platform MUST be structured metadata and MUST be the final system tag in directory display names.

Native OS tags are synchronized projections and MUST NOT become the authoritative source.

Tag drift MUST be detectable and repairable.

Unsupported filesystems MUST degrade clearly rather than silently.

The automatic built-in `Processed` workflow collection is derived from durable
metadata saves, not from AI, VLM submission, suggestion generation, physical
rename, import, or filesystem time. The first successful durable metadata save
whose complete ordered tag list contains at least one canonical tag enters a
medium into `Processed` and records `processed_at_ms` as the current transition
time. Non-empty tag edits, title edits, and description edits MUST preserve an
existing `processed_at_ms` exactly. Removing all tags MUST clear `Processed`
membership and set `processed_at_ms` to null. Later re-tagging MUST assign a new
`processed_at_ms`. One medium MUST hold zero or one collection membership, the
only supported persisted collection key is `processed`, and no arbitrary
collection creation, rename, deletion, or manual assignment API exists. VLM
submission, AI suggestion generation, and physical rename MUST NOT change the
processing timestamp. Catalog metadata saves MUST NOT mutate media files.

Approved directory example:

```text
Reinventing Entropy - Compression is Intelligence [Math] [Compression] [YouTube]
```

## 10. Portable Naming

The title MUST remain the primary sort prefix.

Tags MUST remain at the end of display directory names.

The source platform MUST remain last.

Unsafe or non-portable characters MUST be normalized.

Collisions MUST be detected.

Renames MUST be planned before execution.

Cross-platform compatibility MUST include macOS, Linux, Windows, and common shared filesystems.

The exact normalization algorithm remains an ADR or design decision.

## 11. Metadata Durability

Portable sidecar manifests are durable metadata.

SQLite or another approved local database is an index/cache.

The local index SHOULD be rebuildable from durable metadata where feasible.

Live SQLite databases MUST NOT be synchronized between devices as the sole durable metadata mechanism.

Sidecar writes MUST eventually use versioning, validation, and atomic replacement.

The exact manifest format and schema remain unresolved.

## 12. Dates and Provenance

FrameNest MUST distinguish source publication or creation date, archive-added date, downloaded date, imported date, first-seen date, filesystem creation time, and filesystem modification time.

These concepts MUST NOT be silently conflated.

Metadata provenance SHOULD be retained where practical.

## 13. Cover Requirements

FrameNest MUST support cover concepts for standalone media, episodes, and series.

Cover selection SHOULD support timeline frame selection and image import.

The original approved cover SHOULD be durable.

A selected timestamp MUST be stored in a stable time unit when a cover comes from media.

Derived thumbnails MUST be reproducible cache artifacts.

Frame number alone MUST NOT be the only durable reference.

AI-generated covers are future scope.

An existing approved cover MUST NOT be overwritten without confirmation.

Cover provenance SHOULD be retained.

The manual cover workflow MUST require explicit acceptance such as `Set as
cover`.

A created or generated cover candidate MUST NOT become active automatically.

Only explicit human acceptance MAY activate a cover candidate and replace the
previous accepted cover.

Cover timestamp MUST NOT change normal playback start.

Ordinary Play MUST start at `00:00`; seeking to a cover timestamp is a separate
explicit action if offered later.

Final image formats and thumbnail sizes remain unresolved.

## 14. Gallery Requirements

The gallery MUST provide a premium dark and cover-driven experience.

The gallery SHOULD scale to large libraries through rendering strategies such as lazy loading and virtualization.

Search and filtering MUST be supported.

Filters SHOULD include libraries, devices, platforms, canonical tags, media type, series, and availability.

Multiple selected canonical tags MUST default to AND/intersection semantics. OR behavior MAY be added later only as an explicit advanced mode.

Card and series views SHOULD be supported.

Remote availability, transfer state, and download state SHOULD be visible.

Remote-only logical media SHOULD remain visible through metadata, covers, derived thumbnails, and availability summaries when those lightweight records are available without full media bytes.

Inline preview for short media SHOULD be supported separately from full playback.

Keyboard, mouse, and touch interaction SHOULD be supported.

Accessibility, reduced motion, reduced transparency, and lower-resource modes MUST be considered.

This document does not select a frontend framework.

## 15. GIF, Short Media, and MEME Requirements

FrameNest SHOULD support GIF files and short videos as first-class media.

MEME collections SHOULD be first-class collections rather than secondary gallery content.

Inline looping preview SHOULD be supported.

Copy to Clipboard MAY be supported where platform capabilities permit.

Download and Download + Copy actions MAY be supported for remote media.

`Download + Copy to Clipboard` MUST verify any downloaded representation before placing it on the native clipboard and MUST provide fallback behavior when the platform or target application does not support direct paste.

Heuristic classification MAY be used, but users MUST be able to override it.

FrameNest MUST NOT automatically upload short media or frames to an LLM provider.

Full playback MUST remain separate from inline preview.

## 16. Media Acquisition

Media acquisition MUST use an adapter-based source architecture.

yt-dlp is the intended first adapter.

Domain logic MUST NOT depend directly on yt-dlp.

Acquisition SHOULD support metadata inspection, progress, cancellation, temporary or incomplete state, collision-safe filenames, safe final rename, structured errors, finalization verification, and source identity/archive tracking.

FrameNest SHOULD NOT perform unnecessary transcoding by default.

The exact format policy remains unresolved.

## 17. Playback

FrameNest MUST define a `MediaPlayerBackend` conceptual boundary.

External VLC is the first intended full-playback backend.

Playback SHOULD support local paths and authorized remote URLs.

VLC availability SHOULD be checked and failures SHOULD be reported clearly.

Embedded libVLC is future scope.

An `InlinePreviewBackend` MUST remain separate from full playback.

Domain logic MUST NOT hardcode VLC command construction.

Future playback SHOULD support fullscreen and truthful audio-track selection
where technically supported. Playback UI MUST use capability detection and
fallback rather than fake controls. Subtitle support is not currently required.
FrameNest MUST NOT silently transcode originals.

This document does not define implementation syntax.

## 18. Authoritative Server and Client State

The FrameNest server process MUST be authoritative for catalog records and
server-owned state.

Server-owned state includes server media originals, canonical display title,
description, canonical tags, future category and language metadata, per-user
visibility state, upload and ingest state, server preview cache,
authentication, and capability decisions.

Browser, desktop, local NUC browser, and future remote interfaces MUST be
clients of the server API. Clients MUST NOT infer administrator authority from
loopback, source IP, hostname, Tailscale membership, cookies, or same-machine
execution.

The server MAY run locally on the same device as a desktop client or remotely
on the Ubuntu NUC after deployment acceptance. Local-first operation MUST NOT
require public cloud dependence.

Local desktop operation SHOULD remain useful when the needed local server
process, local catalog/cache records, and local media are available.

Metadata, covers, availability state, and lightweight derived thumbnails MAY synchronize independently of full media bytes.

FrameNest MUST NOT automatically replicate all media bytes to every device.

Explicit streaming, opening, or download of authorized media MAY be supported
without registering trusted permanent client-local availability.

Authenticated server-managed ingest/upload, catalog synchronization, explicit
client cache/download, per-user visibility state, server deletion requests,
global retirement, and physical purge of originals MUST remain distinct
operations.

The trusted-loopback upload foundation MUST use server-selected placement and
MUST include quarantine, validation, limits, safe server-owned names, duplicate
detection, atomic no-replace publication, and cleanup recovery. Clients MUST
NOT select arbitrary server filesystem paths. Publication MUST require an
explicit server-configured registered destination; absent configuration MUST
leave eligible work safely at `publish_pending`. `published` MUST prove verified
server-owned bytes and durable provenance but MUST NOT imply catalog or Gallery
visibility.

Per-user Trash MUST be server-persisted visibility state and MUST NOT delete
the server original.

The synchronization protocol remains unresolved.

## 19. Network Boundary

Local-only functions need no Tailscale.

Remote and cross-device functions MUST use Tailscale in the approved direction unless explicitly superseded by an approved decision.

An application backend SHOULD bind to loopback when exposed through Tailscale Serve.

FrameNest MUST NOT require router port forwarding.

FrameNest MUST NOT use Tailscale Funnel in the approved direction.

The normal application process MUST NOT invoke privileged Tailscale provisioning on every startup.

Network identity alone is insufficient authorization.

Application capabilities must later be defined.

This document does not place current Tailscale command syntax in the specification.

## 20. Transfers and Duplicate Removal

FrameNest SHOULD support Copy, Move, and Move while retaining lightweight local metadata.

Transfers MUST verify destination size, integrity, and readability where feasible before source deletion.

Source deletion MUST occur only after successful validation.

Full media transfer MUST be explicit or governed by a later accepted automation rule.

Operations SHOULD provide previews, progress, cancellation, transaction or audit state, final-copy protection, and clear partial-failure recovery.

This document does not choose a checksum algorithm.

## 21. Search and Filtering

Search and filtering SHOULD include canonical tags, platform, library, device, availability, duration, size, archive-added date, source date, media type, series, MEME classification, and local/remote state.

The search engine remains unresolved.

Title/name search SHOULD be supported by the first persistent gallery-capable catalog. The initial local SQLite catalog browser supports persisted display-title substring search and repeated canonical-tag filters with AND semantics as a bounded read-only slice. Multiple selected tags MUST use AND semantics by default. `All media` is a virtual Catalog scope and is not stored as a collection. An optional `collection=processed` query parameter restricts a catalog page to members of the built-in `Processed` workflow collection; All-media requests MUST omit it.

Future first-class categories SHOULD include `memes`, `youtube`, and `movies`.
Categories MUST be modeled as a dedicated facet rather than only canonical tags
or directory names once category persistence is implemented.

Movies MAY carry explicit language metadata such as English, Slovak, or Czech.
Language metadata SHOULD prefer container or audio metadata and user editing
before expensive AI analysis. FrameNest MUST NOT automatically upload audio to
a cloud provider.

## 22. AI and Privacy

AI features MUST use replaceable provider adapters when implemented.

AI assistance MUST be optional.

Cloud operations MUST be explicit opt-in.

Users SHOULD understand what payload is sent.

Provider secrets SHOULD remain server-held where possible.

Provider secrets MUST NOT be returned to ordinary clients.

Ordinary browser clients MUST NOT configure AI providers, activate models, enter
provider API keys, receive provider API keys, or call external AI providers
directly.

Server AI provider administration MUST use an operator boundary. The initial
operator boundary is `./framenest ai configure`, `./framenest ai status`, and
`./framenest ai test`.

Server AI configuration files MUST contain only schema-versioned non-secret
provider/model selection and safe timestamps. They MUST NOT contain API keys,
Authorization headers, cookies, provider responses, prompts, frame data, media
paths, or database paths.

AI configuration precedence MUST preserve deployment overrides: explicit
FrameNest provider/model environment overrides first, then persisted non-secret
server AI configuration, then legacy NVIDIA compatibility when `NVIDIA_API_KEY`
is present and no explicit provider configuration exists, then unconfigured.

`./framenest ai status` MUST be network-free. `./framenest ai test` MUST be an
explicit text-only provider request, upload no media data, and persist only a
safe last-test category and timestamp.

NVIDIA NIM and Vercel AI Gateway are supported server providers in this slice.
Vercel AI Gateway uses `AI_GATEWAY_API_KEY` and preferred model
`google/gemini-3.1-flash-lite`. NVIDIA NIM keeps the existing `NVIDIA_API_KEY`
credential boundary and default model.

Suspicious filename analysis MUST occur only on user action.

Representative-frame selection MAY be used later.

Title and tag suggestions MUST require confirmation.

FrameNest MUST NOT automatically rename media.

FrameNest MUST NOT perform unsolicited cloud frame upload.

Prompts MUST NOT include unrelated paths, cookies, keys, or logs.

Opening a media detail view MUST NOT trigger an AI call, catalog save, or
filesystem mutation.

FrameNest MUST distinguish persisted catalog values, unsaved `Current` manual
working state, physical filename, library-relative path, AI draft, promoted
draft values, accepted current-page values, durable catalog save, suggested
filename, and future explicit physical rename operation.

Changing display title MUST NOT rename a file. Editing suggested filename MUST
NOT rename a file. Catalog save MUST NOT implicitly rename, move, delete, tag,
or reorganize media files.

`Use this draft` or an equivalent promotion action MUST copy selected AI draft
values into `Current`; it MUST NOT save to the catalog or mutate the filesystem.

AI drafts MUST NOT be automatically promoted, saved, tagged, renamed, or
assigned to a collection.

Canonical-tag editing SHOULD provide searchable local suggestions, keyboard and
mouse navigation, rounded removable chips, an explicit `×` control, visible
hover/focus/selected/AI-suggested/invalid states, case-insensitive duplicate
prevention, optional controlled new-tag creation, and immediate local filtering
without progress UI for trivial local filtering.

Capability-aware model filtering SHOULD use provider-neutral concepts such as
`vision_input`, `video_input`, `structured_text_output`, `image_generation`,
`image_editing`, `reference_image`, `local_execution`, and `cloud_execution`.
Browsing or highlighting models MUST NOT invoke a provider.

## 23. Secrets

Secrets MUST NOT be committed to Git.

Secrets MUST NOT be stored in plaintext sidecars.

Secrets MUST NOT be stored in ordinary SQLite fields.

Secrets MUST NOT be logged.

Secrets MUST NOT be stored in browser local storage.

Native or server secret storage requires a dedicated decision.

Replacement and removal workflows MUST NOT reveal the full stored secret.

## 24. Structured Errors and Logging

FrameNest SHOULD use a structured component, operation, and error-code model.

Messages MUST be sanitized.

Tool and platform context SHOULD be included where safe.

Errors SHOULD describe retryability where possible.

Secrets MUST NOT be logged.

Log retention SHOULD be bounded.

Support bundles MUST be reviewed before sharing.

Cloud AI diagnostics require sanitization and user awareness.

## 25. Destructive Operations

Destructive operations include delete, move, deduplication, database clearing, library removal, global tag deletion, cover overwrite, final-copy deletion, and storage formatting.

Destructive operations MUST require previews, confirmations, verification, and rollback or recovery information where feasible.

## 26. Cross-Platform Requirements

Apple Silicon macOS is the first development and test environment.

Ubuntu Server 24.04 on the Intel NUC6i5SYH is the current personal production server preparation target.

Broader macOS, Linux, and Windows portability remains required.

Browser/PWA access remains conceptual direction.

Platform adapters MUST isolate OS-specific behavior.

### Desktop Shell Requirements

FrameNest MUST become a desktop application for normal end-user use. Browser mode MAY remain for development, diagnostics, and controlled operator workflows, but it MUST NOT be the required normal end-user experience.

Tauri v2 is the accepted future desktop shell per [ADR-0021](docs/adr/0021-tauri-desktop-shell.md).

The desktop shell MUST display the FrameNest UI in a native system WebView and MUST supervise the Python/FastAPI backend as a sidecar rather than duplicating domain or catalog logic.

The sidecar backend MUST bind only to loopback by default.

The desktop shell MUST enforce a single-instance lifecycle.

The desktop shell SHOULD provide a tray or macOS menu-bar presence with initial `Gallery`, `Settings`, and `Quit` actions.

Closing the main window SHOULD hide the window rather than terminate the application. `Quit` MUST stop the supervised backend cleanly.

Native capabilities MUST be least-privilege and allowlisted. The WebView MUST NOT receive unrestricted filesystem, shell, process, or arbitrary-command access.

Native file selection, directory selection, save/export destinations, file-manager reveal, VLC opening, notifications, and clipboard operations MAY be exposed only through explicit scoped capabilities.

MacBook-first implementation is accepted, but platform-specific behavior MUST remain isolated so later Windows and Linux validation remains possible.

### Distributed Media Requirements

Selective media placement direction is recorded in
[ADR-0022](docs/adr/0022-selective-media-placement-and-server-aggregation.md).
The authoritative server/client state model is recorded in
[ADR-0035](docs/adr/0035-authoritative-server-and-client-state-model.md).

The Intel NUC server MAY act as an authoritative FrameNest server, archive
node, remote streaming/download source, transfer receiver, centralized
AI-provider boundary, and future backup participant after deployment
acceptance.

The NUC MUST NOT make FrameNest a public-cloud dependency or make local clients
unusable when the needed local server process, local catalog/cache records, and
local media are available.

Remote-only media cards SHOULD be visible from metadata and covers without requiring full media download.

Future remote access MUST follow the Tailscale-only direction unless explicitly superseded.

### Progress Requirements

Determinate operations SHOULD show real transferred bytes, total bytes, percentage, speed, ETA, and verification/finalization state when available.

Indeterminate operations MAY use restrained animation, shimmer, masked text, pulse, or fade effects, but MUST NOT show fabricated percentages, invented backend stages, or false cancellation.

### Supported Python Runtime

FrameNest MUST target CPython 3.13 as the initial supported runtime.

Future project metadata MUST constrain supported Python to an equivalent of `>=3.13,<3.14` unless a later ADR supersedes [ADR-0001](docs/adr/0001-supported-python-version.md).

Local tests, continuous integration, and server deployment verification MUST run under Python 3.13.

Project commands MUST use an isolated project environment independent of a developer's global Python installation once project tooling exists.

The exact 3.13 patch release is pinned by accepted project tooling and ADR-0001; it MAY advance within the 3.13 series after tests pass.

### Python Dependency and Environment Management

FrameNest MUST use Poetry as the Python dependency and virtual-environment manager per [ADR-0002](docs/adr/0002-python-environment-and-dependency-manager.md).

Future Python project metadata MUST be stored in `pyproject.toml`.

The FrameNest application MUST commit `poetry.lock` for reproducible development, test, continuous integration, and deployment dependency resolution.

Python dependencies MUST NOT be installed globally for FrameNest.

Project commands MUST execute through the Poetry-managed isolated CPython 3.13 environment.

Lockfile updates MUST occur only in explicit bounded tasks and MUST be accompanied by test evidence and verification that `pyproject.toml` and `poetry.lock` remain synchronized.

Local tests, continuous integration, and Ubuntu deployment MUST install from the committed lock-based Poetry environment.

Poetry virtual-environment location remains unresolved until the authorized scaffold task.

### Repository Layout

FrameNest MUST use the hybrid staged monorepo layout per [ADR-0004](docs/adr/0004-repository-layout.md).

The initial Python project MUST live at repository root with root `pyproject.toml`, root `poetry.lock`, `src/framenest/`, root `tests/`, and `docs/`.

Poetry package mode MUST be used. The importable package name MUST be `framenest`.

The initial internal boundaries MUST be `domain`, `application`, `adapters/api`, and `infrastructure` under `src/framenest/`.

`domain` MUST NOT import FastAPI or infrastructure adapters. `application` MUST NOT depend on FastAPI route objects. `adapters/api` MAY depend on FastAPI and application interfaces.

Tests MUST be organized under `tests/unit/`, `tests/integration/`, and `tests/contract/` and MUST reflect these boundaries.

Package imports MUST be resolved through the Poetry-managed installed project environment. Reliance on `sys.path` manipulation MUST NOT be the standard import mechanism.

Empty future web or desktop scaffolds MUST NOT be created. Future `web/` and `desktop/` top-level boundaries MAY be added only when real implementation work begins.

### Configuration Strategy

FrameNest MUST use a layered configuration model with explicit precedence per [ADR-0005](docs/adr/0005-configuration-strategy.md).

Precedence from lowest to highest authority MUST be: safe program defaults; optional committed non-secret configuration; ignored local `.env` values; process environment variables; future approved secret-store values.

The default server host MUST be `127.0.0.1`. Public bind addresses MUST NOT be the default.

Configuration MUST be loaded through a centralized boundary. Application and domain logic MUST NOT read environment variables directly throughout the codebase. The domain layer MUST remain independent of the concrete configuration library.

Configuration values MUST be typed and validated. Invalid configuration MUST fail clearly with sanitized errors.

Secrets MUST NOT be committed or stored in normal version-controlled configuration. Secret values MUST be redacted from representations, logs, errors, and ordinary API responses.

Local `.env` files MUST remain Git-ignored. Process environment variables MUST override `.env` and lower-precedence values. Production deployment MUST NOT depend on a developer `.env` file.

Tests MUST use deterministic, isolated configuration state and MUST NOT rely on the developer's real shell environment.

### Initial Server API Framework

FrameNest MUST use FastAPI for the initial server HTTP API adapter per [ADR-0003](docs/adr/0003-initial-server-api-framework.md).

FrameNest MUST use synchronous SQLAlchemy 2.x Core with Alembic for the initial local SQLite persistence and migration foundation per [ADR-0010](docs/adr/0010-initial-persistence-foundation.md). SQLAlchemy ORM mapped entities, SQLModel, and async SQLite access are not accepted for the initial foundation. A minimal migration foundation and explicit database command boundary exist. A minimal device domain entity and local device registry exist per [ADR-0012](docs/adr/0012-initial-device-registry.md). A minimal library domain entity, device-local root-locator model, and local library registry exist per [ADR-0013](docs/adr/0013-initial-library-registry.md), with canonical UUID text storage for catalog tables and lexical device-local root paths represented by explicit `posix` or `windows` flavor plus canonical absolute path text. A minimum persistent logical-media and physical-location foundation exists per [ADR-0025](docs/adr/0025-minimum-persistent-media-catalog-foundation.md), with canonical UUID text storage, explicit repository boundaries, migration `0004`, and no automatic migration. Persistent display title and canonical content tags exist per [ADR-0027](docs/adr/0027-persistent-display-title-and-canonical-tags.md), with migration `0005`, sparse metadata rows, ordered tag assignments, stable English tag keys, and no file mutation. A nullable plain-text description column is added in migration `0006`. An automatic built-in `Processed` workflow collection is added per [ADR-0030](docs/adr/0030-automatic-processed-collection.md), with nullable `collection_key` and `processed_at_ms` columns added in migration `0007`, one medium holding zero or one collection membership, the built-in `processed` key as the only supported collection key, and no arbitrary collection CRUD or general collection manager. A dedicated catalog read model exists per [ADR-0028](docs/adr/0028-catalog-read-model-and-search-semantics.md), with display-title substring search, repeated canonical-tag AND filters, deterministic ordering, bounded offset pagination, and catalog-safe location data. The packaged browser includes a manual `Current` metadata workspace that loads one imported medium by media ID, keeps persisted baseline values distinct from unsaved form state and filename fallback labels, edits or clears display title, edits or clears an optional plain-text description, locally searches existing canonical tags, selects, removes, and explicitly reorders up to 32 ordered tag assignments, explicitly creates canonical tag definitions, saves through the existing metadata API, refreshes the active catalog query after successful save, and does not rename, move, delete, analyze, upload, or mutate media files. A bounded, deterministic, read-only, non-persistent library scan preview exists per [ADR-0014](docs/adr/0014-safe-library-scan-preview.md); candidate classification is extension-hint based only. Explicit idempotent scan-candidate import exists per [ADR-0026](docs/adr/0026-explicit-idempotent-scan-candidate-import.md); it requires an explicit selected candidate, reruns the bounded scan, creates one logical media item plus one physical location atomically when absent, returns an existing location for repeated imports, and performs no filesystem mutation. A bounded, deterministic, read-only, provider-neutral local media-analysis preparation boundary exists per [ADR-0015](docs/adr/0015-deterministic-local-media-analysis-preparation.md); it inspects one explicit MP4 or GIF candidate through optional external `ffprobe` and `ffmpeg` executables, returns bounded technical metadata, prepares at most three exact-distinct representative PNG frames in memory only, and writes no media records. A bounded, explicit opt-in, non-persistent media suggestion preview exists per [ADR-0016](docs/adr/0016-provider-neutral-media-suggestions-and-nvidia-nim-prototype.md); it reuses local preparation, requires explicit cloud confirmation, derives bounded JPEG VLM images for NVIDIA NIM transport per [ADR-0019](docs/adr/0019-vlm-image-derivatives-and-nvidia-instruct-mode.md), validates one untrusted suggestion preview, and performs no catalog or filesystem mutation. An explicit same-origin browser AI suggestion review exists per [ADR-0020](docs/adr/0020-on-demand-ai-suggestion-review.md); capability discovery is sanitized and provider-free, suggestion requests require explicit confirmation, the browser receives no credential, raw prompt, raw provider response, frame payload, absolute media path, or database path, and accept/reject actions are session-only with no mutation endpoint. Durable sidecars, storage volumes, arbitrary user-created collections, a general collection manager, collection CRUD, manual collection assignment, suggested filenames, covers, thumbnails, persistent AI Drafts, gallery persistence, synchronization, upload-to-catalog linkage, per-user visibility state, and multi-device server workflows remain unimplemented. The trusted-loopback upload foundation through migration `0013` provides durable quarantine sessions, bounded validation, canonical byte identity, exact-duplicate disposition, lifecycle-owned single-process publication recovery, and verified server-owned originals without creating logical media or physical locations.

Domain and application logic MUST remain independent of FastAPI and MUST be testable without starting an HTTP server.

API route handlers MUST remain thin and SHOULD delegate to application services or use cases rather than contain filesystem, media-processing, database, downloader, or destructive-operation logic directly.

API request and response contracts MUST be typed.

HTTP and validation errors MUST be translated into structured, sanitized responses that do not leak secrets, absolute private paths, or raw stack traces to ordinary clients.

The API MUST support dependency replacement or injection for tests.

The initial server MUST be configurable for loopback-only binding and MUST NOT be publicly exposed by default.

Long-running downloads, media processing, scans, and transfers MUST NOT be implemented as unbounded synchronous work inside route handlers.

Future implementation MUST include API contract tests and domain tests that do not import FastAPI.

## 27. Accessibility and Performance

FrameNest SHOULD support reduced motion, reduced transparency, keyboard access, focus visibility, touch targets, useful errors, responsive interaction, bounded background work, large-library scalability, and weaker-device degradation modes.

This specification makes no numeric performance promises.

## 28. Security Baseline

FrameNest SHOULD use least privilege.

FrameNest MUST NOT require routine root execution.

AppArmor and firewall protections MUST NOT be disabled as shortcuts.

FrameNest SHOULD use path validation, input validation, explicit authorization, localhost service direction, secret redaction, safe updates, and later service hardening.

## 29. First Functional Vertical Slice

The first functional vertical slice SHOULD register one local library, import or download one media item, create durable metadata, index it locally, apply canonical tags, create the expected portable directory name, select or import a cover, generate derived thumbnail data, display it in a real gallery, open it through the playback abstraction, and prove roundtrip and filesystem behavior with tests.

The vertical slice is not implemented.

## 30. Verification Requirements

Implementation work SHOULD include unit tests, integration tests where boundaries require them, filesystem safety tests, path portability tests, manifest roundtrip tests, migration tests, failure-case tests, and deterministic fixtures.

Success MUST NOT be claimed without evidence.

## 31. Explicitly Deferred Decisions

Deferred decisions include frontend framework, frontend workspace tooling,
committed configuration file format, exact configuration schema,
operating-system secret-store implementation, manifest format, schema, IPC,
authentication above Tailscale, synchronization protocol, offline client cache
semantics, multiprocess publication leases or fencing, upload-to-catalog
transactions, per-user visibility state,
category schema, language metadata schema, audio-track capability detection,
FFmpeg distribution, yt-dlp packaging/update strategy, player invocation,
thumbnail formats and sizes, full-text search, packaging/signing/update
mechanisms, telemetry, and license.

The supported Python minor version is recorded in [ADR-0001](docs/adr/0001-supported-python-version.md). Poetry dependency and environment management is recorded in [ADR-0002](docs/adr/0002-python-environment-and-dependency-manager.md). The initial server API framework is recorded in [ADR-0003](docs/adr/0003-initial-server-api-framework.md). Repository layout and Poetry package mode are recorded in [ADR-0004](docs/adr/0004-repository-layout.md). Configuration strategy is recorded in [ADR-0005](docs/adr/0005-configuration-strategy.md). The concrete settings library is recorded in [ADR-0007](docs/adr/0007-settings-library.md). The initial ASGI runtime is recorded in [ADR-0008](docs/adr/0008-asgi-runtime.md). The initial SQLite persistence and migration foundation is recorded in [ADR-0010](docs/adr/0010-initial-persistence-foundation.md). The stable entity identity format is recorded in [ADR-0011](docs/adr/0011-stable-domain-identities.md). Selective media placement is recorded in [ADR-0022](docs/adr/0022-selective-media-placement-and-server-aggregation.md), with server-authority portions superseded by [ADR-0035](docs/adr/0035-authoritative-server-and-client-state-model.md). Manual-first metadata and multi-model AI drafts are recorded in [ADR-0023](docs/adr/0023-manual-first-metadata-and-multi-model-ai-drafts.md). Cover Studio and AI cover candidates are recorded in [ADR-0024](docs/adr/0024-cover-studio-and-ai-cover-candidates.md). The minimum persistent media catalog foundation is recorded in [ADR-0025](docs/adr/0025-minimum-persistent-media-catalog-foundation.md). Explicit idempotent scan-candidate import is recorded in [ADR-0026](docs/adr/0026-explicit-idempotent-scan-candidate-import.md). Persistent display title and canonical tags are recorded in [ADR-0027](docs/adr/0027-persistent-display-title-and-canonical-tags.md). Catalog read model and search semantics are recorded in [ADR-0028](docs/adr/0028-catalog-read-model-and-search-semantics.md). The automatic built-in `Processed` workflow collection is recorded in [ADR-0030](docs/adr/0030-automatic-processed-collection.md). The Fedora systemd service foundation is recorded in [ADR-0031](docs/adr/0031-fedora-systemd-service-foundation.md) and superseded for the active deployment target by the Ubuntu NUC deployment foundation in [ADR-0032](docs/adr/0032-ubuntu-nuc-deployment-foundation.md). Arbitrary user-created collections, a general collection manager, suggested filenames, covers, thumbnails, and persistent AI drafts remain unresolved and unimplemented. Identity database encoding beyond canonical UUID text, sidecar manifest format, full-text search design, WAL and checkpoint details, production backup and restore, remote server database design, real Ubuntu NUC host acceptance, AppArmor/UFW policy, Tailscale Serve, systemd credentials, and authentication remain unresolved. Exact dependency versions, 3.13 patch pinning, Poetry virtual-environment location, Uvicorn version and extras, startup interface, process model, worker count, reload policy, trusted proxy configuration, structured logging, background jobs, authentication, and API versioning remain implementation concerns governed by those ADRs and later authorized tasks.

None of these may be silently selected during implementation.

## 32. Relationship to Other Documents

This specification is grounded in [README.md](README.md), [PRODUCT.md](PRODUCT.md), [SECURITY.md](SECURITY.md), [AGENTS.md](AGENTS.md), and the pinned canonical AP protocol under [`.ap/`](.ap/). The FrameNest AP integration decision is recorded in [ADR-0034](docs/adr/0034-canonical-analytic-programming-integration.md).

Future ADRs should record architecture decisions. This document does not create ADRs.
