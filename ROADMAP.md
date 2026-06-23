# FrameNest Roadmap

## Roadmap Principles

This roadmap is staged and evidence-based. It does not promise release dates.

Each phase should begin only when its entry conditions are satisfied and should close only with the listed exit evidence.

The roadmap distinguishes completed foundation, immediate next work, planned phases, long-term scope, and explicitly deferred work.

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

The initial scaffold decision gate is complete. The next bounded task may begin the first test-first Python server scaffold on macOS. Scaffolding is now eligible but not automatically authorized.

Broader architecture decisions still open include local database/query strategy, sidecar manifest format and versioning, server/domain boundaries, initial authentication boundary, media-tool distribution strategy, macOS development runtime details, and Fedora deployment details.

Key deliverables: remaining broader architecture ADRs and evidence as needed before later implementation phases.

Entry conditions: [SPEC.md](SPEC.md) and this roadmap are accepted.

Exit evidence: broader architecture package completed without silently selecting unresolved options beyond the initial scaffold gate.

Boundaries: Phase 2 remains `in progress` until the broader architecture package is completed. Application code is not implemented by this decision gate alone.

## Phase 3 — Domain and Metadata Core

Status: planned.

Goal: define and test the core domain model and durable metadata behavior.

Key deliverables: stable identities, logical media, physical locations, devices, libraries, storage volumes, series, canonical tags, sidecar contracts, and exact roundtrip tests.

Entry conditions: relevant ADRs accepted.

Exit evidence: tests proving domain rules, identity behavior, sidecar roundtrip, and no implementation claims without passing evidence.

Boundaries: no gallery, downloader, playback, or server aggregation beyond what domain tests require.

## Phase 4 — Server-First Development Skeleton on macOS

Status: planned.

Goal: create the first local development server skeleton on macOS.

Key deliverables: loopback-only local development server skeleton, health endpoint, configuration boundary, structured logging, SQLite development catalog, migration mechanism, and tests.

Entry conditions: server/API/database/repository-layout ADRs accepted.

Exit evidence: local tests and command output showing loopback-only behavior and basic health/config/database boundaries.

Boundaries: server-first implementation priority MUST NOT make the desktop product server-dependent.

## Phase 5 — Local Catalog and Library Scanning

Status: planned.

Goal: register and scan local libraries safely.

Key deliverables: library registration, safe scanning, metadata collection, availability tracking, storage capacity reporting, rebuildable local index, and tests.

Entry conditions: domain and local database foundations exist.

Exit evidence: deterministic fixtures and filesystem tests showing non-destructive scanning and rebuildable index behavior.

Boundaries: no destructive organization by default.

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

Key deliverables: cover-driven gallery, search, filtering, series views, storage/device state, short-media preview, accessibility support, reduced motion, reduced transparency, and lower-resource modes.

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

Status: planned after the server foundation works on macOS.

Goal: deploy and harden the server foundation on Fedora KDE Intel NUC.

Key deliverables: Fedora KDE installation notes, updates, hardware/storage inspection, hardening, SELinux/firewalld policy, service user, systemd hardening, and backup/recovery documentation.

Entry conditions: macOS server foundation is working and tested.

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

Key deliverables: device synchronization, global locations, offline state, conflict handling, and Android/PWA global view direction.

Entry conditions: local catalogs, server aggregator, and synchronization decisions are ready.

Exit evidence: tests proving known locations, offline state, and conflict behavior.

Boundaries: automatic global synchronization remains deferred until explicitly designed.

## Phase 14 — Streaming, Download, and Transfer

Status: planned.

Goal: support safe remote media operations.

Key deliverables: direct play first, copy/move operations, verification, deduplication safeguards, remote download, progress, cancellation, and partial-failure recovery.

Entry conditions: remote access, authorization, and transfer model are accepted.

Exit evidence: tests and controlled transfer evidence showing destination verification and final-copy protection.

Boundaries: no source deletion before verified destination success.

## Phase 15 — AI-Assisted Workflows

Status: long-term planned.

Goal: add optional user-controlled AI assistance.

Key deliverables: naming/tagging assistance, suspicious filename analysis, representative-frame selection, provider adapters, privacy modes, and confirmation workflows.

Entry conditions: provider-adapter decisions, secret storage decisions, and privacy UX are accepted.

Exit evidence: tests and reviews showing no unsolicited cloud upload and no provider secrets in ordinary clients.

Boundaries: suggestions require confirmation and AI remains optional.

## Phase 16 — AI-Generated Covers

Status: long-term planned.

Goal: add optional generated cover workflows.

Key deliverables: generated cover proposals, provenance, confirmation, replacement safeguards, and rollback information.

Entry conditions: cover pipeline and AI provider boundaries are mature.

Exit evidence: user-confirmed cover generation flow with provenance and no automatic replacement.

Boundaries: no generated cover replaces an approved cover without confirmation.

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
