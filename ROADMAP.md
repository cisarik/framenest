# FrameNest Roadmap

## Roadmap Principles

This roadmap is staged and evidence-based. It does not promise release dates.

Each phase should begin only when its entry conditions are satisfied and should close only with the listed exit evidence.

The roadmap distinguishes completed foundation, immediate next work, planned phases, long-term scope, and explicitly deferred work.

## Near-Term MacBook MVP Convergence

The minimum logical-media and physical-location persistence foundation and
explicit idempotent import from selected scan candidates now exist on MacBook.
The persistent display-title and canonical-tag core now exists, and imported
media can now be reached through a catalog browser with display-title search,
canonical-tag AND filters, and a manual `Current` metadata workspace for title,
optional plain-text description, and ordered tag assignment. An automatic
built-in `Processed` workflow collection derived from durable tag saves is
implemented through [ADR-0030](docs/adr/0030-automatic-processed-collection.md)
and migration `0007`; arbitrary
user-created collections and suggested filename remain future decisions not yet
authorized by a subsequent slice.

The near-term convergence sequence is:

1. persistent local media catalog foundation;
2. logical media and physical locations;
3. explicit idempotent import from selected scan candidates;
4. canonical tags and title/tag metadata;
5. searchable catalog browser;
6. manual title/tag metadata detail;
7. Cover Studio and derivatives;
8. persistent premium gallery;
9. multi-model AI workspace;
10. optional AI cover experiments;
11. later Tauri and NUC work.

This sequence preserves broader cross-platform goals while keeping the immediate
critical path focused on a polished and functional macOS MVP.

## Phase 0 — Repository and Protocol Foundation

Status: completed before this task.

Goal: establish a safe public repository and working protocol.

Key deliverables: public repository, safety perimeter, security policy, Analytic Programming protocol, Orchestrator and Worker handbooks, Worker bootstrap, and product foundation.

Entry conditions: empty verified repository.

Exit evidence: committed foundation files through `PRODUCT.md`.

Boundaries: no application code, package scaffolding, or framework selection.

## Phase 1 — Normative Product Foundation

Status: completed by Stage A of this task.

Goal: convert approved product direction into normative requirements and a staged plan.

Key deliverables: [PRODUCT.md](PRODUCT.md), [SPEC.md](SPEC.md), and [ROADMAP.md](ROADMAP.md).

Entry conditions: product foundation committed.

Exit evidence: specification and roadmap committed.

Boundaries: unresolved architecture decisions remain unresolved.

## Phase 2 — Architecture Decision Package

Status: in progress.

Goal: prepare individual ADR evidence before scaffolding and record accepted architecture decisions one at a time.

Accepted so far:

- Supported Python version: CPython 3.13 through [ADR-0001](docs/adr/0001-supported-python-version.md).
- Python environment and dependency manager: Poetry through [ADR-0002](docs/adr/0002-python-environment-and-dependency-manager.md).
- Initial server API framework: FastAPI through [ADR-0003](docs/adr/0003-initial-server-api-framework.md).
- Hybrid staged repository layout through [ADR-0004](docs/adr/0004-repository-layout.md).
- Configuration strategy: layered configuration with explicit precedence through [ADR-0005](docs/adr/0005-configuration-strategy.md).
- macOS Python interpreter provider: `uv` for CPython 3.13.14 on Apple Silicon macOS through [ADR-0006](docs/adr/0006-macos-python-interpreter-provider.md).
- Python settings library: `pydantic-settings` through [ADR-0007](docs/adr/0007-settings-library.md).
- Initial ASGI runtime: Uvicorn through [ADR-0008](docs/adr/0008-asgi-runtime.md).
- Initial structured logging approach: standard-library `logging` with a FrameNest-owned JSON formatter and redaction boundary through [ADR-0009](docs/adr/0009-structured-logging-approach.md); implementation complete.
- Initial SQLite persistence and migration foundation: synchronous SQLAlchemy Core with Alembic through [ADR-0010](docs/adr/0010-initial-persistence-foundation.md); minimal explicit migration implementation complete.
- Stable domain identities: application-owned UUIDv4 values with category-specific pure-domain types through [ADR-0011](docs/adr/0011-stable-domain-identities.md); minimal identity primitives implemented.
- Local web application delivery through packaged vanilla HTML/CSS/JavaScript assets through [ADR-0017](docs/adr/0017-initial-local-web-application-delivery.md); implementation complete.
- Local media-analysis preview API through [ADR-0018](docs/adr/0018-local-media-analysis-preview-api.md); implementation complete.
- VLM JPEG derivatives and NVIDIA instruct mode through [ADR-0019](docs/adr/0019-vlm-image-derivatives-and-nvidia-instruct-mode.md); implementation complete for the prototype boundary.
- On-demand editable AI suggestion review through [ADR-0020](docs/adr/0020-on-demand-ai-suggestion-review.md); implementation complete as a non-persistent pre-alpha review.
- Tauri desktop shell direction through [ADR-0021](docs/adr/0021-tauri-desktop-shell.md); not implemented.
- Selective media placement and optional server aggregation direction through [ADR-0022](docs/adr/0022-selective-media-placement-and-server-aggregation.md); not implemented.
- Manual-first metadata and multi-model AI draft direction through [ADR-0023](docs/adr/0023-manual-first-metadata-and-multi-model-ai-drafts.md); partially implemented for manual `Current` display title, plain-text description, and ordered canonical tags. Collection, suggested filename, persistent AI drafts, multi-model draft comparison, inline model picker, and draft promotion workflows remain unimplemented.
- Cover Studio and AI cover candidate direction through [ADR-0024](docs/adr/0024-cover-studio-and-ai-cover-candidates.md); not implemented.
- Minimum persistent media catalog foundation through [ADR-0025](docs/adr/0025-minimum-persistent-media-catalog-foundation.md); implementation complete for logical media and physical locations only.
- Explicit idempotent scan-candidate import through [ADR-0026](docs/adr/0026-explicit-idempotent-scan-candidate-import.md); implementation complete for one selected scan candidate at a time.
- Persistent display-title and canonical-tag core through [ADR-0027](docs/adr/0027-persistent-display-title-and-canonical-tags.md); implementation complete for API-level title/tag persistence.
- Catalog read model and search semantics through [ADR-0028](docs/adr/0028-catalog-read-model-and-search-semantics.md); implementation complete for read-only imported-media listing, display-title search, canonical-tag AND filters, deterministic ordering, and bounded offset pagination.
- Automatic built-in `Processed` workflow collection from durable tag saves through [ADR-0030](docs/adr/0030-automatic-processed-collection.md); accepted and implemented through migration `0007`, with one zero-or-one collection membership per medium, and no arbitrary collection CRUD or general collection manager.

The initial scaffold decision gate is complete. A Poetry package scaffold, centralized configuration boundary, FastAPI application factory, typed health endpoint, contract tests, Uvicorn runtime dependency, startup wiring, and a runnable loopback-only server command now exist.

Broader architecture decisions still open include sidecar manifest format and versioning, metadata/tag/search schema, cover and thumbnail cache implementation details, desktop sidecar IPC, initial authentication boundary, media-tool distribution strategy, and Fedora deployment details.

Persistence strategy is accepted through [ADR-0010](docs/adr/0010-initial-persistence-foundation.md). The minimal SQLAlchemy/Alembic migration foundation is implemented. The current local catalog schema is implemented through revision `0007`, where revision `0007` adds the automatic built-in `Processed` collection columns for [ADR-0030](docs/adr/0030-automatic-processed-collection.md).

Stable identity strategy is accepted through [ADR-0011](docs/adr/0011-stable-domain-identities.md). Pure domain identity primitives exist, and minimal logical media, physical location, device, and library entities exist. Storage volume and series entities remain future work beyond identity values.

Key deliverables: remaining broader architecture ADRs and evidence as needed before later implementation phases.

Entry conditions: [SPEC.md](SPEC.md) and this roadmap are accepted.

Exit evidence: broader architecture package completed without silently selecting unresolved options beyond accepted ADRs.

Boundaries: Phase 2 remains `in progress` until the broader architecture package is completed. Application code is not implemented by this decision gate alone.

## Phase 3 — Domain and Metadata Core

Status: planned.

Goal: define and test the core domain model and durable metadata behavior.

Implemented so far:

- Stable identity format accepted through [ADR-0011](docs/adr/0011-stable-domain-identities.md)
- Immutable pure-domain identity primitives for logical media, physical locations, devices, libraries, storage volumes, and series
- Minimal pure-domain `Device` entity and local device registry core accepted through [ADR-0012](docs/adr/0012-initial-device-registry.md)
- Minimal pure-domain `Library`, `LibraryRoot`, and device-local root-locator model with local library registry core accepted through [ADR-0013](docs/adr/0013-initial-library-registry.md)
- Minimal pure-domain `LogicalMedia`, `MediaLocation`, relative-path, media-kind, and availability-state model accepted through [ADR-0025](docs/adr/0025-minimum-persistent-media-catalog-foundation.md)

Still required for phase exit:

- Storage volume and series entities beyond identity values
- Manual metadata detail beyond display title and ordered canonical tags
- Durable metadata roundtrip behavior beyond the current SQLite/API/browser title-tag slice
- Sidecar contracts
- Exact roundtrip tests for durable metadata behavior

Entry conditions: relevant ADRs accepted.

Exit evidence: tests proving domain rules, identity behavior, sidecar roundtrip, and no implementation claims without passing evidence.

Boundaries: no gallery, downloader, playback, or server aggregation beyond what domain tests require.

## Phase 4 — Server-First Development Skeleton on macOS

Status: partially started.

Goal: create the first local development server skeleton on macOS.

Implemented so far:

- Poetry package scaffold
- Centralized `pydantic-settings` configuration boundary with loopback-safe default host
- FastAPI application factory with typed `GET /health`
- In-process API contract tests and import-boundary tests
- Uvicorn runtime dependency and startup wiring
- Runnable loopback-only server process verified by tests and command output
- Runtime health smoke verification
- Packaged local web shell at `GET /` with same-origin assets
- Read-only registered-library listing API
- Same-origin scan-preview API
- Same-origin local media-analysis preview API
- Same-origin explicit AI capability and media-suggestion preview API
- Structured logging foundation per [ADR-0009](docs/adr/0009-structured-logging-approach.md)
- Persistence strategy accepted through [ADR-0010](docs/adr/0010-initial-persistence-foundation.md)
- Minimal SQLAlchemy Core/Alembic persistence foundation with `FRAMENEST_DATABASE_PATH`, packaged revisions `0001` through `0007`, explicit `framenest-db status`, and explicit `framenest-db migrate`
- Initial local device registry core with pure-domain `Device`, application repository port, SQLAlchemy Core adapter, and `devices` table through revision `0002`
- Initial local library registry core with pure-domain `Library`, `LibraryRoot`, application repository port, SQLAlchemy Core adapter, and `libraries` table through revision `0003`
- Minimum persistent media catalog foundation with pure-domain logical media and physical locations, application repository port, SQLAlchemy Core adapter, and `logical_media` plus `physical_media_locations` tables through revision `0004`
- Persistent display-title and canonical-tag core with pure-domain metadata values, application repository port, SQLAlchemy Core adapter, and `canonical_tags`, `media_metadata`, plus `media_canonical_tags` tables through revision `0005`
- Automatic built-in `Processed` workflow collection derived from durable tag saves with nullable `collection_key` and `processed_at_ms` columns added in revision `0007`
- Read-only imported-media catalog browser with display-title search, repeated canonical-tag AND filters, deterministic ordering, and bounded offset pagination
- Development operator catalog CLI (`framenest-catalog`) for device register, get, and list operations
- Library catalog CLI commands for local library register, get, and list with lexical root-path preparation
- Explicit idempotent scan-candidate import through same-origin API and packaged browser action

Still required for phase exit:

- Manual metadata detail beyond persistent title/tag data and the current catalog browser

The next bounded implementation step should build on imported media records without adding gallery, cover, or filesystem mutation scope prematurely.

Key deliverables: loopback-only local development server skeleton, health endpoint, configuration boundary, structured logging, SQLite development catalog, migration mechanism, and tests.

Entry conditions: server/API/database/repository-layout ADRs accepted.

Exit evidence: local tests and command output showing loopback-only behavior and basic health/config/database boundaries.

Boundaries: server-first implementation priority MUST NOT make the desktop product server-dependent.

## Phase 5 — Local Catalog and Library Scanning

Status: in progress.

Goal: register and scan local libraries safely.

Implemented within this phase:

- library registration through the development catalog CLI;
- safe read-only library scan preview through `framenest-catalog library scan-preview` per [ADR-0014](docs/adr/0014-safe-library-scan-preview.md);
- deterministic read-only local media-analysis preparation through `framenest-catalog library analyze-preview` per [ADR-0015](docs/adr/0015-deterministic-local-media-analysis-preparation.md);
- explicit opt-in NVIDIA NIM media suggestion preview through `framenest-catalog library suggest-preview` per [ADR-0016](docs/adr/0016-provider-neutral-media-suggestions-and-nvidia-nim-prototype.md);
- packaged browser library listing, scan preview, explicit scan-candidate import, local media-analysis preview, capability discovery, and editable non-persistent AI suggestion review.
- minimum logical-media and physical-location persistence through revision `0004`.
- explicit idempotent import from selected scan candidates through [ADR-0026](docs/adr/0026-explicit-idempotent-scan-candidate-import.md).
- persistent display-title and canonical content tags through [ADR-0027](docs/adr/0027-persistent-display-title-and-canonical-tags.md).
- read-only catalog retrieval, display-title search, canonical-tag AND filters, deterministic ordering, and bounded offset pagination through [ADR-0028](docs/adr/0028-catalog-read-model-and-search-semantics.md).
- browser manual `Current` metadata workspace for one selected imported medium, including persistent display-title edit/clear, canonical-tag search, selected-tag removal and reordering, explicit canonical-tag creation, dirty/discard protection, and catalog refresh after successful save.
- automatic built-in `Processed` workflow collection entered by the first durable tag save, cleared when all tags are removed, with a virtual `All media` Catalog scope and an optional `Processed` Catalog scope in the packaged browser.

Still unimplemented within this phase:

- arbitrary user-created collections and a general collection manager;
- suggested filename editing and physical rename;
- browser metadata fields beyond display title, plain-text description, and ordered canonical tags;
- availability tracking;
- storage capacity reporting;
- rebuildable local index persistence;
- sidecars and rebuild behavior.

Key deliverables: library registration, safe scanning, persistent metadata collection, logical media and physical locations, canonical tags, title/tag search, availability tracking, storage capacity reporting, rebuildable local index, and tests.

Entry conditions: domain and local database foundations exist.

Exit evidence: deterministic fixtures and filesystem tests showing non-destructive scanning and rebuildable index behavior.

Boundaries: no destructive organization by default; no file mutation is required for the minimum persistent catalog.

## Phase 6 — Naming, Tagging, and Portable Metadata

Status: planned.

Goal: implement canonical organization rules and durable metadata.

Key deliverables: canonical tags, directory naming, sidecars, native tag adapters, dry runs, migrations, drift detection, and repair workflows.

Entry conditions: metadata contracts and path portability rules are accepted.

Exit evidence: tests for naming, tag projection, sidecar durability, dry-run previews, and safe migrations.

Boundaries: no silent rename or migration execution.

## Phase 7 — Media Acquisition

Status: planned.

Goal: implement the first adapter-based acquisition workflow.

Key deliverables: yt-dlp adapter, source inspection, metadata preview, progress, cancellation, temporary state, finalization, archive identity, structured errors, and tests.

Entry conditions: media acquisition boundaries and packaging/update strategy are decided.

Exit evidence: deterministic tests or controlled fixtures proving adapter isolation and safe finalization.

Boundaries: domain logic must not depend directly on yt-dlp and no unnecessary transcoding by default.

## Phase 8 — Covers and Thumbnail Pipeline

Status: planned.

Goal: support durable covers and reproducible derived thumbnails.

Key deliverables: timeline selection, cover import, durable original cover storage, derived cache, reproducibility checks, series covers, and tests.

Entry conditions: media metadata and storage layout are stable enough for cover references.

Exit evidence: roundtrip tests for selected timestamps, imported covers, derived thumbnails, and cover provenance.

Boundaries: AI-generated covers remain later scope.

## Phase 9 — Premium Local Gallery

Status: planned.

Goal: build the first real scalable local gallery.

Key deliverables: cover-driven gallery, logical-item cards, local and remote-only card states, title search, multi-tag AND filtering, removable active filters, series views, storage/device state, short-media preview, accessibility support, reduced motion, reduced transparency, and lower-resource modes.

Entry conditions: domain, metadata, covers, and local catalog are testable.

Exit evidence: working local gallery backed by testable local data and verified accessibility/performance behavior without unsupported numeric promises.

Boundaries: do not select a frontend framework outside approved ADRs.

## Phase 10 — Playback

Status: planned.

Goal: open local and later remote media through a playback abstraction.

Key deliverables: external VLC backend, VLC availability checks, failure reporting, authorized remote URL support later, and separate inline-preview backend.

Entry conditions: player invocation and playback boundary decisions accepted.

Exit evidence: tests or controlled verification showing backend separation and clear failure handling.

Boundaries: embedded libVLC remains deferred.

## Phase 11 — Intel NUC Fedora Deployment

Status: planned after the MacBook MVP has a persistent local catalog, premium local gallery, and desktop shell direction ready for deployment packaging.

Goal: deploy and harden the server foundation on Fedora KDE Intel NUC.

Key deliverables: Fedora KDE installation notes, updates, hardware/storage inspection, hardening, SELinux/firewalld policy, service user, systemd hardening, and backup/recovery documentation.

Entry conditions: macOS local catalog, gallery, and desktop foundations are working and tested; server aggregation decisions are ready.

Exit evidence: documented deployment checks and verified service behavior on the NUC.

Boundaries: no destructive disk commands in roadmap tasks.

## Phase 12 — Tailscale-Only Remote Access

Status: planned.

Goal: enable private remote access without public exposure.

Key deliverables: Tailscale provisioning as deployment infrastructure, Serve boundary, loopback backend exposure, authorization design, no Funnel, and no public ports.

Entry conditions: server deployment boundary and authorization decisions accepted.

Exit evidence: verification that remote access is private, authorized, and not publicly exposed.

Boundaries: no router port forwarding and no Tailscale Funnel in the approved direction.

## Phase 13 — Aggregated Multi-Device Catalog

Status: planned.

Goal: aggregate media and locations across devices.

Key deliverables: device synchronization, global logical media visibility, remote-only cards backed by metadata/covers, global locations, offline state, conflict handling, and Android/PWA global view direction.

Entry conditions: local catalogs, server aggregator, and synchronization decisions are ready.

Exit evidence: tests proving known locations, offline state, and conflict behavior.

Boundaries: automatic full-media replication is not the default; automatic global synchronization remains deferred until explicitly designed.

## Phase 14 — Streaming, Download, and Transfer

Status: planned.

Goal: support safe remote media operations.

Key deliverables: direct play first, explicit stream/download/archive actions, copy/move operations, verification, deduplication safeguards, remote download, `Download + Copy to Clipboard` through native desktop capability, truthful progress, cancellation, and partial-failure recovery.

Entry conditions: remote access, authorization, and transfer model are accepted.

Exit evidence: tests and controlled transfer evidence showing destination verification and final-copy protection.

Boundaries: no source deletion before verified destination success.

## Phase 15 — AI-Assisted Workflows

Status: long-term planned.

Goal: add optional user-controlled AI assistance.

Key deliverables: manual-first metadata workspace, multi-model AI draft comparison, naming/tagging assistance, suspicious filename analysis, representative-frame selection, provider adapters, privacy modes, and confirmation workflows.

Entry conditions: persistent catalog and manual metadata detail exist; provider-adapter decisions, secret storage decisions, and privacy UX are accepted.

Exit evidence: tests and reviews showing no unsolicited cloud upload and no provider secrets in ordinary clients.

Boundaries: suggestions require confirmation, draft promotion is not persistence, and AI remains optional.

## Phase 16 — AI-Generated Covers

Status: long-term planned.

Goal: add optional generated cover workflows.

Key deliverables: generated cover candidates, provenance, confirmation, replacement safeguards, and rollback information.

Entry conditions: manual Cover Studio, cover candidates, and AI provider boundaries are mature.

Exit evidence: user-confirmed cover generation flow with provenance and no automatic replacement.

Boundaries: no generated cover candidate replaces an approved cover without explicit human acceptance.

## Phase 17 — Backup and Encrypted Cloud Restore

Status: long-term scope only.

Goal: provide future backup and restore without losing local-first ownership.

Key deliverables: metadata-first restore, integrity checks, multiple providers, encryption, recovery workflows, and documentation.

Entry conditions: stable metadata, identity, server, and security foundations.

Exit evidence: restore tests proving metadata and integrity behavior.

Boundaries: not part of early implementation and not a cloud-only direction.

## Deferred Early Non-Goals

Deferred early non-goals include mobile-native completeness, public hosting, transcoding cluster, embedded libVLC, automatic global synchronization, every source adapter, multi-user SaaS, automatic self-updates, and VeraCrypt UI.

These items MUST NOT be pulled into early implementation without explicit Orchestrator and Cooperator approval.
