# FrameNest Specification

## 1. Document Status and Scope

FrameNest is in foundation-stage pre-alpha development. This document defines normative requirements for future implementation.

A minimal Poetry package foundation exists with centralized configuration, a FastAPI application factory, a typed health endpoint, a loopback-first Uvicorn runtime dependency and startup command, a minimal SQLAlchemy Core/Alembic SQLite migration foundation, pure domain identity primitives, and tests. There is no functional user application, media catalog schema, gallery, deployment, systemd integration, trusted-proxy configuration, or Tailscale integration yet. Unresolved architecture choices remain subject to future architecture decision records.

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

Local desktop gallery, metadata, search, and playback MUST remain usable without the server where their required files are locally available.

The premium gallery and media-acquisition workflows MUST both remain flagship capabilities.

A server MUST NOT replace complete local desktop operation.

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

A derived thumbnail is a reproducible cache artifact derived from a durable source.

A sidecar manifest is portable durable metadata stored near media where feasible.

A local catalog is a desktop-owned index/cache used for local operation.

A server aggregate catalog is an optional cross-device aggregation of logical media and known locations.

A transfer is a copy, move, or related operation between locations.

An availability state describes whether a device, library, storage volume, or physical location is currently reachable and usable.

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

One logical item MAY have multiple physical locations.

The gallery SHOULD normally present one logical item rather than every duplicate independently.

Users MUST be able to inspect all known copies.

Each physical location MUST record device, library, storage volume, path, size where available, availability, and verification state.

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

Initial display values SHOULD be English.

Content tags MUST be distinct from system and source metadata.

The source platform MUST be structured metadata and MUST be the final system tag in directory display names.

Native OS tags are synchronized projections and MUST NOT become the authoritative source.

Tag drift MUST be detectable and repairable.

Unsupported filesystems MUST degrade clearly rather than silently.

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

Final image formats and thumbnail sizes remain unresolved.

## 14. Gallery Requirements

The gallery MUST provide a premium dark and cover-driven experience.

The gallery SHOULD scale to large libraries through rendering strategies such as lazy loading and virtualization.

Search and filtering MUST be supported.

Filters SHOULD include libraries, devices, platforms, canonical tags, media type, series, and availability.

Card and series views SHOULD be supported.

Remote availability, transfer state, and download state SHOULD be visible.

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

This document does not define implementation syntax.

## 18. Local Catalog and Server Aggregator

Each desktop MUST own a complete catalog for its local operation.

The server MAY aggregate logical media and known locations.

The server MAY support streaming, download, transfers, device state, centralized AI calls, and future backup.

The desktop MUST remain useful when the server is offline.

Server aggregate state and local authoritative state need explicit conflict rules later.

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

Operations SHOULD provide previews, progress, cancellation, transaction or audit state, final-copy protection, and clear partial-failure recovery.

This document does not choose a checksum algorithm.

## 21. Search and Filtering

Search and filtering SHOULD include canonical tags, platform, library, device, availability, duration, size, archive-added date, source date, media type, series, MEME classification, and local/remote state.

The search engine remains unresolved.

## 22. AI and Privacy

AI features MUST use replaceable provider adapters when implemented.

AI assistance MUST be optional.

Cloud operations MUST be explicit opt-in.

Users SHOULD understand what payload is sent.

Provider secrets SHOULD remain server-held where possible.

Provider secrets MUST NOT be returned to ordinary clients.

Suspicious filename analysis MUST occur only on user action.

Representative-frame selection MAY be used later.

Title and tag suggestions MUST require confirmation.

FrameNest MUST NOT automatically rename media.

FrameNest MUST NOT perform unsolicited cloud frame upload.

Prompts MUST NOT include unrelated paths, cookies, keys, or logs.

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

Fedora KDE on an Intel NUC is the later server deployment target.

Broader macOS, Linux, and Windows portability remains required.

Browser/PWA access remains conceptual direction.

Platform adapters MUST isolate OS-specific behavior.

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

Local tests, continuous integration, and Fedora deployment MUST install from the committed lock-based Poetry environment.

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

FrameNest MUST use synchronous SQLAlchemy 2.x Core with Alembic for the initial local SQLite persistence and migration foundation per [ADR-0010](docs/adr/0010-initial-persistence-foundation.md). SQLAlchemy ORM mapped entities, SQLModel, and async SQLite access are not accepted for the initial foundation. A minimal migration foundation and explicit database command boundary exist. A minimal device domain entity and local device registry exist per [ADR-0012](docs/adr/0012-initial-device-registry.md). A minimal library domain entity, device-local root-locator model, and local library registry exist per [ADR-0013](docs/adr/0013-initial-library-registry.md), with canonical UUID text storage for catalog tables and lexical device-local root paths represented by explicit `posix` or `windows` flavor plus canonical absolute path text. A bounded, deterministic, read-only, non-persistent library scan preview exists per [ADR-0014](docs/adr/0014-safe-library-scan-preview.md); candidate classification is extension-hint based only and writes no media records. A bounded, deterministic, read-only, provider-neutral local media-analysis preparation boundary exists per [ADR-0015](docs/adr/0015-deterministic-local-media-analysis-preparation.md); it inspects one explicit MP4 or GIF candidate through optional external `ffprobe` and `ffmpeg` executables, returns bounded technical metadata, prepares at most three exact-distinct representative PNG frames in memory only, and writes no media records. The broader media catalog schema, repository API beyond device and library registries, durable sidecars, availability tracking, storage volumes, media locations, synchronization, and persistent scanning remain unimplemented.

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

SELinux and firewall protections MUST NOT be disabled as shortcuts.

FrameNest SHOULD use path validation, input validation, explicit authorization, localhost service direction, secret redaction, safe updates, and later service hardening.

## 29. First Functional Vertical Slice

The first functional vertical slice SHOULD register one local library, import or download one media item, create durable metadata, index it locally, apply canonical tags, create the expected portable directory name, select or import a cover, generate derived thumbnail data, display it in a real gallery, open it through the playback abstraction, and prove roundtrip and filesystem behavior with tests.

The vertical slice is not implemented.

## 30. Verification Requirements

Implementation work SHOULD include unit tests, integration tests where boundaries require them, filesystem safety tests, path portability tests, manifest roundtrip tests, migration tests, failure-case tests, and deterministic fixtures.

Success MUST NOT be claimed without evidence.

## 31. Explicitly Deferred Decisions

Deferred decisions include frontend framework, frontend workspace tooling, committed configuration file format, exact configuration schema, operating-system secret-store implementation, manifest format, schema, IPC, authentication above Tailscale, synchronization protocol, FFmpeg distribution, yt-dlp packaging/update strategy, player invocation, thumbnail formats and sizes, full-text search, packaging/signing/update mechanisms, telemetry, and license.

The supported Python minor version is recorded in [ADR-0001](docs/adr/0001-supported-python-version.md). Poetry dependency and environment management is recorded in [ADR-0002](docs/adr/0002-python-environment-and-dependency-manager.md). The initial server API framework is recorded in [ADR-0003](docs/adr/0003-initial-server-api-framework.md). Repository layout and Poetry package mode are recorded in [ADR-0004](docs/adr/0004-repository-layout.md). Configuration strategy is recorded in [ADR-0005](docs/adr/0005-configuration-strategy.md). The concrete settings library is recorded in [ADR-0007](docs/adr/0007-settings-library.md). The initial ASGI runtime is recorded in [ADR-0008](docs/adr/0008-asgi-runtime.md). The initial SQLite persistence and migration foundation is recorded in [ADR-0010](docs/adr/0010-initial-persistence-foundation.md). The stable entity identity format is recorded in [ADR-0011](docs/adr/0011-stable-domain-identities.md). Media catalog schema, identity database encoding, sidecar manifest format, full-text search design, final production database path policy, WAL and checkpoint details, backup and restore, and remote aggregate database design remain unresolved. Exact dependency versions, 3.13 patch pinning, Poetry virtual-environment location, Uvicorn version and extras, startup interface, process model, worker count, reload policy, trusted proxy configuration, structured logging, systemd integration, background jobs, authentication, and API versioning remain implementation concerns governed by those ADRs and later authorized tasks.

None of these may be silently selected during implementation.

## 32. Relationship to Other Documents

This specification is grounded in [README.md](README.md), [PRODUCT.md](PRODUCT.md), [SECURITY.md](SECURITY.md), [AGENTS.md](AGENTS.md), [AP.md](AP.md), [AP_ORCHESTRATOR.md](AP_ORCHESTRATOR.md), and [AP_WORKER.md](AP_WORKER.md).

Future ADRs should record architecture decisions. This document does not create ADRs.
