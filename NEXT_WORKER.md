# Next Worker Handoff

## 1. Purpose and authority

This file is a non-authoritative Worker-session handoff. It is state-restoration evidence only. It is not a task and grants no modification, architecture, dependency, migration, command, filesystem, network, AI-provider, or Git authority.

A fresh Worker instance assigned to the WORKER role requires one separate authoritative Orchestrator task prompt before doing any work. The Cooperator normally does not paste this file manually. The fresh Worker instance reads it directly from the repository during bootstrap.

Repository state, accepted ADRs, tests, and the new authoritative task override stale handoff claims.

Current Worker instance session: **CLOSED**. The persistent WORKER protocol role continues.

## 2. Repository identity

- Repository: `https://github.com/cisarik/framenest.git`
- Local path used by the closing Worker instance: `/Users/agile/framenest`
- Branch: `main`
- Pre-handoff public HEAD: `a488e0672382d75bf4939db09e9999b365ebab1a`
- Pre-handoff subject: `feat: add NVIDIA NIM suggestion prototype`
- Pre-handoff parent: `8c923a816cfeb5f5ab49f0b043072c09a6d53797`

A fresh Worker instance must independently resolve final post-handoff local `HEAD`, local `origin/main`, remote `main`, and the final handoff commit subject and parent. Do not infer the post-handoff SHA from this file.

## 3. Toolchain and dependency state

- Runtime constraint: CPython `>=3.13,<3.14`
- Observed project interpreter: CPython `3.13.14` in `.venv/`
- Observed Poetry version: `2.1.4`
- Poetry remains the dependency, environment, and lockfile authority
- `uv` remains the accepted Apple Silicon macOS CPython interpreter provider through [ADR-0006](docs/adr/0006-macos-python-interpreter-provider.md)

Direct runtime dependency constraints in `pyproject.toml`:

- `pydantic-settings (>=2.14.2,<3.0.0)`
- `fastapi (>=0.138.0,<0.139.0)`
- `uvicorn (>=0.49.0,<0.50.0)`
- `sqlalchemy (>=2.0.51,<2.1.0)`
- `alembic (>=1.18.4,<1.19.0)`

Direct development dependency constraints:

- `pytest = ^9.1.1`
- `httpx2 = ^2.4.0`

Console entrypoints:

- `framenest-server = "framenest.server:main"`
- `framenest-db = "framenest.infrastructure.persistence.cli:main"`
- `framenest-catalog = "framenest.adapters.cli.catalog:main"`

No dependency change occurred in cycle 051. SQLAlchemy ORM mapped entities, SQLModel, `aiosqlite`, and async SQLAlchemy are not accepted or implemented.

## 4. Implemented architecture

The repository currently implements:

- centralized typed settings in `src/framenest/configuration.py` with `FRAMENEST_DATABASE_PATH` for database location
- FastAPI application factory and typed `GET /health`
- loopback-first Uvicorn runtime through `poetry run framenest-server`
- FrameNest-owned structured JSON logging and redaction in `src/framenest/structured_logging.py`
- synchronous SQLAlchemy 2.x Core SQLite persistence in `src/framenest/infrastructure/persistence/`
- explicit database commands `poetry run framenest-db status` and `poetry run framenest-db migrate`
- packaged Alembic migrations through revision `0003`
- stable UUIDv4 domain identities per [ADR-0011](docs/adr/0011-stable-domain-identities.md)
- pure-domain `Device` and `Library` entities with device-local `LibraryRoot` locators
- application `DeviceRepository` and `LibraryRepository` ports with synchronous SQLAlchemy Core adapters
- development catalog CLI `poetry run framenest-catalog` for device and library registry operations
- ADR-0014 scan-preview boundary, application service, scanner port, and `library scan-preview`
- ADR-0015 deterministic local media analysis preparation with optional `ffprobe`/`ffmpeg` and `library analyze-preview`
- ADR-0016 provider-neutral media suggestion boundary with first NVIDIA NIM adapter and `library suggest-preview`
- bounded subprocess output handling and completion-race hardening in media-analysis infrastructure

## 5. Media suggestion contract

Per [ADR-0016](docs/adr/0016-provider-neutral-media-suggestions-and-nvidia-nim-prototype.md):

- provider ID `nvidia-nim`; default model `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning`
- endpoint `https://integrate.api.nvidia.com/v1/chat/completions`
- prompt version `framenest-media-suggestion-v1`
- requires `--confirm-cloud-upload` and `NVIDIA_API_KEY` before local preparation or network I/O
- sends one to three bounded PNG frames plus basename, candidate kind, and bounded technical metadata only
- no persistence, mutation, absolute-path transmission, whole-video upload, or audio
- temporary prototype credential read at CLI/infrastructure boundary only; not in `FrameNestSettings`

## 6. Current CLI

### Database

```text
poetry run framenest-db status
poetry run framenest-db migrate
```

### Devices

```text
poetry run framenest-catalog device register --display-name NAME
poetry run framenest-catalog device get --id DEVICE_ID
poetry run framenest-catalog device list
```

### Libraries

```text
poetry run framenest-catalog library register \
  --device-id DEVICE_ID \
  --display-name NAME \
  --root PATH
poetry run framenest-catalog library get --id LIBRARY_ID
poetry run framenest-catalog library list
```

### Scan, analyze, and suggest preview

```text
poetry run framenest-catalog library scan-preview --id LIBRARY_ID
poetry run framenest-catalog library analyze-preview --id LIBRARY_ID --path RELATIVE_PATH
poetry run framenest-catalog library suggest-preview \
  --id LIBRARY_ID \
  --path RELATIVE_PATH \
  --provider nvidia-nim \
  --model nvidia/nemotron-3-nano-omni-30b-a3b-reasoning \
  --confirm-cloud-upload
```

Catalog commands require the database at packaged migration head, emit one compact JSON object per non-help invocation, never migrate automatically, and remain development/operator boundaries rather than final desktop UX.

## 7. Test evidence

### Worker-observed default-suite baseline at Cycle 050 public commit `a488e06`

Observed by the closing Worker instance before Cycle 051 live validation; not re-run during Cycle 051 documentation closeout:

- `poetry run pytest --collect-only -q`: **597 tests collected**
- `poetry run pytest -q`: **596 passed, 1 skipped**
- `poetry run pytest -q -W error`: **596 passed, 1 skipped**
- skipped test: opt-in NVIDIA live smoke in `tests/integration/test_nvidia_nim_live.py`
- `poetry check --lock`: passed at Cycle 050 closeout

Every future Worker instance must independently rerun the baseline from the final public commit it receives.

### Cycle 051 live NVIDIA validation evidence

Worker-observed during operational live validation; distinct from public commit evidence:

- **LIVE NVIDIA SYNTHETIC SMOKE: FAIL**
- **REAL MP4 NVIDIA PREVIEW: NOT RUN** (skipped because synthetic smoke failed)
- credential loaded only through `source .secrets/nvidia.env.fish`; `test -n "$NVIDIA_API_KEY"` succeeded; no credential material printed, copied, committed, or reported
- real NVIDIA endpoint was called from the opt-in live test; HTTP transport and authentication succeeded
- failure category: **provider response validation** — `MediaSuggestionProviderInvalidResponseError` because assistant `content` was not parseable as the required JSON object (content did not match the fenced-or-raw JSON object contract)
- no raw provider response envelope, Authorization header, base64 frame payload, or API key included in this handoff

Test tree structure:

- `tests/contract/`: health API, server process output, Uvicorn runtime/logging, persistence CLI, persistence package resources, catalog CLI
- `tests/integration/`: persistence migrations; device/library repository tests; filesystem read-only scan safety; bounded subprocess real-tool tests; opt-in NVIDIA live smoke
- `tests/unit/`: configuration, import boundaries, API boundaries, persistence engine/boundaries, server runtime, structured logging, package import; domain identity/device/library tests; application repository-port, library-scan, media-analysis, and media-suggestion tests; filesystem scanner tests; media-analysis process and adapter tests; AI credential/transport/prompt tests; catalog helper tests

## 8. Accepted ADRs

- [ADR-0001](docs/adr/0001-supported-python-version.md) through [ADR-0014](docs/adr/0014-safe-library-scan-preview.md): Accepted, implemented
- [ADR-0015](docs/adr/0015-deterministic-local-media-analysis-preparation.md): Accepted, implemented
- [ADR-0016](docs/adr/0016-provider-neutral-media-suggestions-and-nvidia-nim-prototype.md): Accepted, implemented

Accepted ADRs are normative until superseded. This handoff does not edit or reinterpret accepted ADR text.

## 9. Maintainability debt observed at closeout

Record only; no broad refactor was authorized in cycle 051:

- `tests/contract/test_catalog_cli.py` has become oversized
- CLI command-family tests should likely be split by command family
- provider-specific composition and error mapping in the shared catalog CLI deserve a bounded review
- repetitive fixtures and assertions may be extractable without losing readable behavior-focused test names
- long test names alone are not proof of bad code
- no broad architecture rewrite is authorized merely because files are large

## 10. Explicitly unimplemented scope

Not implemented:

- persistent scan records or scan history
- logical media entities and physical media-location entities
- media catalog tables
- migration `0004`
- persistent suggestion storage
- automatic or confirmed file renaming from suggestions
- persistent tag system and MEME collection persistence
- storage-volume entity, table, or discovery
- hashing and duplicate detection
- sidecars
- thumbnails or covers
- HTTP catalog API beyond health
- desktop UI, premium gallery, playback, sync, server aggregation, deployment
- GUI Settings for provider/model selection
- secure secret-store boundary replacing prototype `NVIDIA_API_KEY` handling
- LM Studio and Vercel AI Gateway adapters
- review/accept/reject suggestion UX
- authentication, backup, restore, rebuild, or corruption recovery
- Fedora deployment, systemd services, and Tailscale integration

GUI Settings and the premium gallery remain strategic product goals per [PRODUCT.md](PRODUCT.md) and [ROADMAP.md](ROADMAP.md); they are not abandoned deferred ideas.

## 11. Non-authoritative next direction

Planning context only — not task authority. For the next Worker instance:

1. verify this closeout commit on public `main`
2. inspect Cycle 051 live-test evidence in this handoff and the closing Worker report
3. when live validation failed: implement one narrow evidence-driven correction with a regression test (likely provider response parsing or reasoning-model output handling for NVIDIA NIM)
4. when live validation passes: perform a bounded maintainability refactor without changing behavior
5. preserve the NVIDIA path and provider-neutral application boundary
6. continue toward provider/model Settings architecture and a secure secret-store boundary
7. then add LM Studio and Vercel adapters behind the same port
8. continue toward review/accept/reject UX, persistent media catalog, premium gallery, and playback according to existing product documentation

No Worker instance may implement any of this from the handoff alone. A separate authoritative Orchestrator task is required.

## 12. Fresh Worker instance reading order

1. [AGENTS.md](AGENTS.md)
2. [BOOT_WORKER.md](BOOT_WORKER.md)
3. [AP_WORKER.md](AP_WORKER.md)
4. [NEXT_WORKER.md](NEXT_WORKER.md)
5. [PRODUCT.md](PRODUCT.md), [SPEC.md](SPEC.md), [ROADMAP.md](ROADMAP.md), [SECURITY.md](SECURITY.md), [README.md](README.md)
6. [ADR-0010](docs/adr/0010-initial-persistence-foundation.md) through [ADR-0016](docs/adr/0016-provider-neutral-media-suggestions-and-nvidia-nim-prototype.md)
7. task-relevant source and tests
8. the separate authoritative Orchestrator task prompt

The task prompt, not this handoff, defines actual scope and Git authority.

## 13. Protocol and lifecycle

- Orchestrator communication with the Cooperator is Slovak
- Worker prompts and reports are English
- Worker reports must begin exactly with `### Report for ORCHESTRATOR_CHAT`
- the persistent protocol role is `WORKER`, independent of execution client, agent implementation, model, or model provider
- one Worker instance is a concrete agent temporarily assigned to the WORKER role; context pressure belongs to that instance and its Worker session

Artifact lifecycle:

- classification: non-authoritative Worker-session handoff
- intended consumer: future fresh Worker instances during bootstrap
- discoverability: repository root and Worker bootstrap reading order
- retention: replace only at a future explicitly authorized Worker-session closeout
- supersession and cleanup owner: future closing Worker instance acting under explicit Orchestrator authority
- Git history is the archive; the active tree must contain only the latest handoff

Current Worker instance session: **CLOSED**. The persistent WORKER protocol role continues.
