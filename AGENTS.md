# FrameNest Agent Instructions

## Project Identity

FrameNest is a local-first, privacy-conscious, cross-platform library for video and animated media. It is currently in a foundation-stage, pre-alpha state. A minimal Poetry package scaffold exists with centralized configuration, a FastAPI application factory, a Uvicorn loopback-first runtime wired through `framenest.server`, a typed health endpoint tested in-process and through a real local listener, a runnable development server command (`poetry run framenest-server`), a minimal SQLAlchemy Core/Alembic SQLite persistence foundation with explicit database commands (`poetry run framenest-db status` and `poetry run framenest-db migrate`), a development operator catalog command (`poetry run framenest-catalog`) for local device, library, scan-preview, analysis-preview, and suggestion-preview operations, a packaged same-origin local web shell with library listing, scan preview, local analysis preview, explicit scan-candidate import, imported-media catalog browsing with display-title search and canonical-tag AND filters, a manual `Current` metadata workspace for persistent display-title, optional plain-text description, and ordered canonical-tag assignment, an automatic built-in `Processed` workflow collection derived from durable metadata saves containing at least one canonical tag with a virtual `All media` Catalog scope and an optional `Processed` Catalog scope, and non-persistent AI suggestion review, a minimal pure-domain identity package, pure-domain `Device`, `Library`, `LogicalMedia`, `MediaLocation`, display-title, and canonical-tag entities, application repository ports, an application scan-preview boundary with a standard-library filesystem scanner per [ADR-0014](docs/adr/0014-safe-library-scan-preview.md), an explicit idempotent scan import boundary per [ADR-0026](docs/adr/0026-explicit-idempotent-scan-candidate-import.md), a persistent display-title and canonical-tag core per [ADR-0027](docs/adr/0027-persistent-display-title-and-canonical-tags.md), a deterministic catalog read model and search semantics per [ADR-0028](docs/adr/0028-catalog-read-model-and-search-semantics.md), synchronous SQLAlchemy Core registry and media adapters, and Alembic migration revisions through `0007` for the current catalog schema, where revision `0007` adds the nullable `collection_key` and `processed_at_ms` columns for the automatic built-in `Processed` workflow collection. There is no completed end-user desktop application, storage-volume registration, arbitrary user-created collections, a general collection manager, suggested filenames, covers, thumbnails, persistent AI Drafts, persistent premium gallery, deployment, systemd unit, or Tailscale integration yet.

## Roles

The COOPERATOR is the human project owner. The Cooperator owns strategic intent, approves important alternatives, performs physical-device and account-level actions, executes explicitly assigned human steps, and approves irreversible or security-sensitive operations.

The ORCHESTRATOR is the ChatGPT orchestration layer. The Orchestrator preserves project coherence, inspects evidence, shapes bounded Worker tasks, reviews Worker reports, verifies public commits, and decides whether to accept, correct, continue, pause, or close a session.

The WORKER is the repository execution role. Any compatible Worker implementation may fulfill it, including an IDE-integrated agent, a command-line agent, a local or remote execution agent, or a multi-agent system exposed through one accountable Worker endpoint. The authoritative task and repository protocol remain unchanged regardless of implementation. Availability of tools does not grant permission. The Worker inspects before modification, executes only the authorized task, maintains task boundaries, verifies results, and reports evidence honestly.

## Language Rules

Repository documentation and code must be written in professional English unless a task explicitly says otherwise.

Worker prompts are English.

Worker reports are English and must begin with:

`### Report for ORCHESTRATOR_CHAT`

Orchestrator communication with the Cooperator is Slovak.

Do not use Czech in repository documents, Worker prompts, or Worker reports.

## Operating Rules

- Inspect before changing.
- Do not expand scope silently.
- Do not access or print secrets.
- Do not perform destructive actions without explicit authorization.
- Do not perform Git write operations without task-specific permission.
- Do not install dependencies unless explicitly authorized.
- Do not choose frameworks, databases, or architecture details without an approved task or recorded decision.

## Public Commit Verification

A Worker report is a structured claim. Public committed state is independently inspectable evidence.

When commits are pushed, the Orchestrator should compare the public commit SHA, file tree, diff, and raw file content with the Worker report. Local uncommitted state and public committed state must not be conflated.

## Source-of-Truth Conflict Handling

Repository files describe documented and implemented state. Tests describe verified behavior. Git history describes committed changes. Product foundation documents (`PRODUCT.md`, `SPEC.md`, and `ROADMAP.md`) are committed. The accepted architecture package includes [ADR-0001](docs/adr/0001-supported-python-version.md) (CPython 3.13), [ADR-0002](docs/adr/0002-python-environment-and-dependency-manager.md) (Poetry), [ADR-0003](docs/adr/0003-initial-server-api-framework.md) (FastAPI), [ADR-0004](docs/adr/0004-repository-layout.md) (hybrid staged repository layout), [ADR-0005](docs/adr/0005-configuration-strategy.md) (layered configuration strategy), [ADR-0006](docs/adr/0006-macos-python-interpreter-provider.md) (`uv` as the Apple Silicon macOS CPython 3.13.14 interpreter provider while Poetry remains dependency and virtual-environment authority), [ADR-0007](docs/adr/0007-settings-library.md) (`pydantic-settings` as the concrete settings adapter with domain independence from Pydantic), [ADR-0008](docs/adr/0008-asgi-runtime.md) (Uvicorn as the initial ASGI runtime, installed and wired as the loopback-first development server), [ADR-0009](docs/adr/0009-structured-logging-approach.md) (standard-library logging with a FrameNest-owned structured JSON formatter and centralized redaction boundary, implemented in `src/framenest/structured_logging.py`; Uvicorn uses explicit FrameNest `log_config`; access logs are initially disabled; no file logging, retention, correlation middleware, deployment, or systemd integration yet), [ADR-0010](docs/adr/0010-initial-persistence-foundation.md) (synchronous SQLAlchemy 2.x Core with Alembic for SQLite migrations and FrameNest-owned repository boundaries; no ORM, SQLModel, or async SQLite access for the initial foundation; a minimal explicit SQLite migration foundation exists), [ADR-0011](docs/adr/0011-stable-domain-identities.md) (application-owned UUIDv4 stable identities with category-specific pure-domain types for logical media, physical locations, devices, libraries, storage volumes, and series), [ADR-0012](docs/adr/0012-initial-device-registry.md) (minimal pure-domain `Device` entity, application `DeviceRepository` port, synchronous SQLAlchemy Core adapter, and Alembic revision `0002` for the initial local device registry), [ADR-0013](docs/adr/0013-initial-library-registry.md) (minimal pure-domain `Library` and `LibraryRoot` entities, application `LibraryRepository` port, synchronous SQLAlchemy Core adapter, and Alembic revision `0003` for the initial local library registry), [ADR-0014](docs/adr/0014-safe-library-scan-preview.md) (bounded deterministic read-only library scan preview), [ADR-0017](docs/adr/0017-initial-local-web-application-delivery.md) (packaged same-origin vanilla web shell), [ADR-0025](docs/adr/0025-minimum-persistent-media-catalog-foundation.md) (minimum logical-media and physical-location catalog foundation in revision `0004`), [ADR-0026](docs/adr/0026-explicit-idempotent-scan-candidate-import.md) (explicit idempotent import from selected scan candidates), [ADR-0027](docs/adr/0027-persistent-display-title-and-canonical-tags.md) (persistent display-title and canonical-tag core in revision `0005`), and [ADR-0028](docs/adr/0028-catalog-read-model-and-search-semantics.md) (dedicated read-only catalog read model with display-title search, canonical-tag AND filters, deterministic ordering, and bounded offset pagination), and [ADR-0030](docs/adr/0030-automatic-processed-collection.md) (automatic built-in `Processed` workflow collection derived from durable tag saves with migration `0007`, accepted and implemented for the bounded built-in Processed workflow, with one zero-or-one collection membership per medium and no arbitrary collection CRUD or general collection manager). Future accepted decisions require bounded tasks and ADRs recorded in [docs/adr/](docs/adr/README.md).

Handoff files describe session state but do not independently redefine permanent strategy.

When sources conflict, identify the exact conflict, determine whether a source is stale, incomplete, misunderstood, or intentionally superseded, and escalate strategic conflicts to the Cooperator through the Orchestrator.

## Product Invariants

- FrameNest remains local-first.
- A premium gallery is a flagship product invariant.
- Server functionality must not replace local desktop functionality.
- Backend services must not be publicly exposed by default.
- Remote access direction is Tailscale-only unless explicitly superseded by an approved decision.
- Provider secrets must not be distributed to ordinary client installations.

## Handoff Model

FrameNest uses exactly these four lifecycle files:

- `BOOT_ORCHESTRATOR.md`: one-time bootstrap for a new Orchestrator chat.
- `BOOT_WORKER.md`: stable Worker bootstrap protocol.
- `NEXT_ORCHESTRATOR.md`: session-close handoff for a future Orchestrator.
- `NEXT_WORKER.md`: concise repository-local Worker handoff.

`BOOT_ORCHESTRATOR.md` is the stable Orchestrator bootstrap. `BOOT_WORKER.md` is stable Worker bootstrap protocol. `NEXT_ORCHESTRATOR.md` carries the latest Orchestrator-session handoff when an Orchestrator session is intentionally closed. `NEXT_WORKER.md` carries the latest Worker-session handoff when a Worker session is intentionally closed. Do not create `NEXT_AGENT.md`.

General session rotation and context-pressure rules are in [AP.md](AP.md), section **Session Rotation and Context Pressure**.

## Protocol Documents

- [AP.md](AP.md): general Analytic Programming protocol.
- [AP_ORCHESTRATOR.md](AP_ORCHESTRATOR.md): operational handbook for Orchestrators.
- [AP_WORKER.md](AP_WORKER.md): operational handbook for Workers.
- [BOOT_ORCHESTRATOR.md](BOOT_ORCHESTRATOR.md): stable Orchestrator bootstrap.
- [BOOT_WORKER.md](BOOT_WORKER.md): FrameNest-specific Worker bootstrap.
- [NEXT_ORCHESTRATOR.md](NEXT_ORCHESTRATOR.md): current Orchestrator session handoff.
- [PRODUCT.md](PRODUCT.md): approved product direction and experience principles.
- [SPEC.md](SPEC.md): normative product and system requirements.
- [ROADMAP.md](ROADMAP.md): staged, evidence-based development plan.

The accepted architecture package is summarized under **Source-of-Truth Conflict Handling** above.
