# FrameNest Architecture Decision Records

## Purpose

Architecture Decision Records (ADRs) document **accepted** architecture decisions for FrameNest. Each ADR explains the context, the decision, rationale, consequences, and how the decision may be revisited.

ADRs are normative for the decisions they record. They do not replace [SPEC.md](../../SPEC.md) product requirements, but they resolve architecture choices that implementation must follow.

## Relationship to evidence packages

Evidence packages such as [ARCHITECTURE_FOUNDATION_EVIDENCE.md](../ARCHITECTURE_FOUNDATION_EVIDENCE.md) collect primary-source research and provisional recommendations. Evidence packages are **not** accepted decisions. Only an ADR with status **Accepted** records project authority for an architecture choice.

## Permitted statuses

| Status | Meaning |
|---|---|
| **Proposed** | Drafted for review; not yet authoritative |
| **Accepted** | Explicitly approved and binding until superseded |
| **Superseded** | Replaced by a later ADR; retained for history |
| **Rejected** | Considered and not adopted; retained for history |

An accepted ADR may only be changed by a later ADR that supersedes it. Editing an accepted ADR in place without a superseding ADR is not permitted.

## Index

| ADR | Title | Status | Decision date | Link |
|---|---|---|---|---|
| 0001 | Supported Python Version | Accepted | 2026-06-23 | [0001-supported-python-version.md](0001-supported-python-version.md) |
| 0002 | Python Environment and Dependency Manager | Accepted | 2026-06-23 | [0002-python-environment-and-dependency-manager.md](0002-python-environment-and-dependency-manager.md) |
| 0003 | Initial Server API Framework | Accepted | 2026-06-23 | [0003-initial-server-api-framework.md](0003-initial-server-api-framework.md) |
| 0004 | Repository Layout | Accepted | 2026-06-23 | [0004-repository-layout.md](0004-repository-layout.md) |
| 0005 | Configuration Strategy | Accepted | 2026-06-23 | [0005-configuration-strategy.md](0005-configuration-strategy.md) |
| 0006 | macOS Python Interpreter Provider | Accepted | 2026-06-23 | [0006-macos-python-interpreter-provider.md](0006-macos-python-interpreter-provider.md) |
| 0007 | Python Settings Library | Accepted | 2026-06-24 | [0007-settings-library.md](0007-settings-library.md) |
| 0008 | Initial ASGI Runtime | Accepted | 2026-06-24 | [0008-asgi-runtime.md](0008-asgi-runtime.md) |
| 0009 | Initial Structured Logging Approach | Accepted | 2026-06-24 | [0009-structured-logging-approach.md](0009-structured-logging-approach.md) |
| 0010 | Initial SQLite Persistence and Migration Strategy | Accepted | 2026-06-24 | [0010-initial-persistence-foundation.md](0010-initial-persistence-foundation.md) |
| 0011 | Stable Domain Identities | Accepted | 2026-06-24 | [0011-stable-domain-identities.md](0011-stable-domain-identities.md) |
| 0012 | Initial Device Registry and Repository Boundary | Accepted | 2026-06-24 | [0012-initial-device-registry.md](0012-initial-device-registry.md) |
| 0013 | Initial Library Registry and Device-Local Root Locators | Accepted | 2026-06-24 | [0013-initial-library-registry.md](0013-initial-library-registry.md) |
| 0014 | Safe Read-Only Library Scan Preview | Accepted | 2026-06-24 | [0014-safe-library-scan-preview.md](0014-safe-library-scan-preview.md) |
| 0015 | Deterministic Local Media Analysis Preparation | Accepted | 2026-06-24 | [0015-deterministic-local-media-analysis-preparation.md](0015-deterministic-local-media-analysis-preparation.md) |
| 0016 | Provider-Neutral Media Suggestions and NVIDIA NIM Prototype | Accepted | 2026-06-24 | [0016-provider-neutral-media-suggestions-and-nvidia-nim-prototype.md](0016-provider-neutral-media-suggestions-and-nvidia-nim-prototype.md) |
| 0017 | Initial Local Web Application Delivery | Accepted | 2026-06-24 | [0017-initial-local-web-application-delivery.md](0017-initial-local-web-application-delivery.md) |
| 0018 | Local Media Analysis Preview API | Accepted | 2026-06-24 | [0018-local-media-analysis-preview-api.md](0018-local-media-analysis-preview-api.md) |
| 0019 | VLM Image Derivatives and NVIDIA Instruct Mode | Accepted | 2026-06-24 | [0019-vlm-image-derivatives-and-nvidia-instruct-mode.md](0019-vlm-image-derivatives-and-nvidia-instruct-mode.md) |
| 0020 | On-Demand AI Suggestion Review | Accepted | 2026-06-25 | [0020-on-demand-ai-suggestion-review.md](0020-on-demand-ai-suggestion-review.md) |
| 0021 | Tauri Desktop Shell | Accepted | 2026-06-25 | [0021-tauri-desktop-shell.md](0021-tauri-desktop-shell.md) |
| 0022 | Selective Media Placement and Server Aggregation | Accepted | 2026-06-25 | [0022-selective-media-placement-and-server-aggregation.md](0022-selective-media-placement-and-server-aggregation.md) |
| 0023 | Manual-First Metadata and Multi-Model AI Drafts | Accepted | 2026-06-25 | [0023-manual-first-metadata-and-multi-model-ai-drafts.md](0023-manual-first-metadata-and-multi-model-ai-drafts.md) |
| 0024 | Cover Studio and AI Cover Candidates | Accepted | 2026-06-25 | [0024-cover-studio-and-ai-cover-candidates.md](0024-cover-studio-and-ai-cover-candidates.md) |
| 0025 | Minimum Persistent Media Catalog Foundation | Accepted | 2026-06-25 | [0025-minimum-persistent-media-catalog-foundation.md](0025-minimum-persistent-media-catalog-foundation.md) |
| 0026 | Explicit Idempotent Scan Candidate Import | Accepted | 2026-06-25 | [0026-explicit-idempotent-scan-candidate-import.md](0026-explicit-idempotent-scan-candidate-import.md) |
| 0027 | Persistent Display Title and Canonical Tags | Accepted | 2026-06-25 | [0027-persistent-display-title-and-canonical-tags.md](0027-persistent-display-title-and-canonical-tags.md) |
| 0028 | Catalog Read Model and Search Semantics | Accepted | 2026-06-26 | [0028-catalog-read-model-and-search-semantics.md](0028-catalog-read-model-and-search-semantics.md) |
