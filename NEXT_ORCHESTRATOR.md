# Next Orchestrator Handoff

## 1. Role restoration

Michal is the COOPERATOR and strategic owner. The fresh ChatGPT chat is the ORCHESTRATOR. Repository execution agents fulfill the persistent WORKER protocol role through concrete Worker instances.

The ORCHESTRATOR communicates with Michal in Slovak and uses feminine grammatical gender. Worker prompts and reports are English. Worker reports must begin exactly with:

`### Report for ORCHESTRATOR_CHAT`

The ORCHESTRATOR independently verifies public commits and raw file content. Issue one bounded task at a time. Analytic Programming is provider- and model-neutral. The repository, accepted ADRs, tests, and Git history are the source of truth.

This file restores orchestration state only. It is not an executable task and grants no implementation or Git authority.

**Current outgoing ORCHESTRATOR session: CLOSED.**

## 2. Repository restoration

- Repository: `https://github.com/cisarik/framenest.git`
- Local path used by the closing Worker instance: `/Users/agile/framenest`
- Branch: `main`
- Pre-handoff public HEAD: `a488e0672382d75bf4939db09e9999b365ebab1a`
- Pre-handoff subject: `feat: add NVIDIA NIM suggestion prototype`
- Pre-handoff parent: `8c923a816cfeb5f5ab49f0b043072c09a6d53797`

The fresh Orchestrator must resolve the final handoff commit from public `main` after the Cycle 051 closeout push. Do not assume this file contains the post-handoff SHA.

Required reading before authorizing work:

1. [BOOT_ORCHESTRATOR.md](BOOT_ORCHESTRATOR.md)
2. [AP.md](AP.md)
3. [AP_ORCHESTRATOR.md](AP_ORCHESTRATOR.md)
4. [NEXT_ORCHESTRATOR.md](NEXT_ORCHESTRATOR.md)
5. [AGENTS.md](AGENTS.md)
6. [BOOT_WORKER.md](BOOT_WORKER.md)
7. [AP_WORKER.md](AP_WORKER.md)
8. [NEXT_WORKER.md](NEXT_WORKER.md)
9. [PRODUCT.md](PRODUCT.md), [SPEC.md](SPEC.md), [ROADMAP.md](ROADMAP.md), [SECURITY.md](SECURITY.md), [README.md](README.md)
10. [docs/adr/README.md](docs/adr/README.md) and ADR-0001 through ADR-0016
11. task-relevant source and tests
12. recent public Git history from the persistence foundation through the final handoff commit

## 3. Verified project state

### Directly committed public facts

The repository implements:

- centralized typed settings with loopback-safe defaults and `FRAMENEST_DATABASE_PATH`
- FastAPI application factory and typed `GET /health`
- Uvicorn loopback-first runtime through `framenest-server`
- FrameNest-owned structured JSON logging with centralized redaction
- synchronous SQLAlchemy 2.x Core SQLite persistence with Alembic
- explicit `framenest-db status` and `framenest-db migrate` commands
- packaged migrations `0001` (foundation), `0002` (`devices`), `0003` (`libraries`)
- stable UUIDv4 domain identities
- pure-domain `Device` and `Library` entities with `LibraryRoot` locators
- application `DeviceRepository` and `LibraryRepository` ports with SQLAlchemy Core adapters
- development catalog CLI for device and library registry
- ADR-0014 bounded read-only library scan preview
- ADR-0015 deterministic local media analysis preparation with optional external tools
- ADR-0016 provider-neutral media suggestion preview with first NVIDIA NIM adapter
- `framenest-catalog library scan-preview`, `analyze-preview`, and `suggest-preview`

There is no migration `0004`, no media table, no storage-volume table, no persistent suggestion storage, no LM Studio or Vercel adapter, and no review/accept/reject UX.

### Closing-Worker-instance-observed default-suite evidence

Worker-observed at Cycle 050 public commit `a488e06`; not re-run during Cycle 051 documentation closeout:

- CPython `3.13.14` in project `.venv/`
- Poetry `2.1.4`
- `poetry check --lock`: passed at Cycle 050 closeout
- `poetry run pytest --collect-only -q`: **597 tests collected**
- `poetry run pytest -q`: **596 passed, 1 skipped**
- `poetry run pytest -q -W error`: **596 passed, 1 skipped**
- skipped: opt-in NVIDIA live smoke

The fresh Orchestrator and Worker instance must reverify these values from the final public commit.

### Cycle 051 live NVIDIA validation evidence

Worker-observed operational evidence; distinct from public commit evidence:

- **LIVE NVIDIA SYNTHETIC SMOKE: FAIL**
- **REAL MP4 NVIDIA PREVIEW: NOT RUN**
- ignored local credential file was sourced successfully; no credential material was printed, copied, committed, or reported
- real NVIDIA endpoint was reached; authentication and transport succeeded
- failure category: provider response validation — assistant content was not parseable as required structured JSON for prompt version `framenest-media-suggestion-v1`
- likely next correction: narrow handling for reasoning-model output shape before or during JSON extraction; confirm with one regression test and re-run opt-in live smoke

Authorized real-media preview for a future live-validation task remains Cooperator-approved representative MP4/GIF meme corpus; do not record private absolute paths in committed repository artifacts.

### Recent public commit sequence

Meaningful sequence through NVIDIA suggestion prototype:

- `8cd4f3f` — deterministic local media analysis preparation (ADR-0015)
- `2f739c8` — subprocess output bounds hardening
- `82a2e0a` — subprocess completion race fixes
- `8c923a8` — subprocess completion race closeout
- `a488e06` — provider-neutral media suggestions and NVIDIA NIM prototype (ADR-0016)

Cycle 051 closeout commit subject: `docs: close live NVIDIA worker session`

## 4. Product invariants

Preserve the established FrameNest direction:

- local-first and privacy-conscious
- cross-platform
- multiple independently registered libraries with stable identities
- one logical medium may have multiple physical locations
- portable sidecars plus rebuildable local indexes
- premium gallery and acquisition are flagship capabilities
- optional server aggregation must not replace desktop autonomy
- external VLC is the initial full-player path; future `MediaPlayerBackend` remains a product direction
- MEME collection for GIFs and short videos is a product direction
- local inline looping previews for GIFs and short clips are a product direction
- Tailscale only for remote features unless explicitly superseded
- Fedora KDE on an Intel NUC is a later deployment target
- API keys for remotely consumed AI features must eventually remain server-side or behind a secure secret-store boundary, not in ordinary client installations
- GUI Settings for provider/model selection remains a strategic product goal

See [PRODUCT.md](PRODUCT.md) and [SPEC.md](SPEC.md) for normative detail.

## 5. Maintainability debt

Record for future bounded tasks; not authorization to refactor broadly:

- `tests/contract/test_catalog_cli.py` is oversized
- split CLI command-family tests where practical
- review provider-specific composition and error mapping in the shared catalog CLI
- extract repetitive fixtures/assertions cautiously while preserving behavior-focused test names
- large files alone do not justify architecture rewrites

## 6. Recommended orchestration sequence

Strategy for the fresh Orchestrator to reassess — not an executable task.

### Immediate next bounded step

After public verification of the Cycle 051 closeout commit:

1. inspect live-validation evidence
2. if synthetic live smoke still fails: authorize one narrow evidence-driven correction plus regression test, then re-run opt-in live smoke
3. if synthetic live smoke passes but real-media preview has not yet passed: authorize operational live validation on Cooperator-approved representative media
4. if live validation passes: authorize bounded maintainability refactor without behavior change

### Subsequent stages

- provider/model Settings architecture and secure secret-store boundary
- LM Studio adapter behind the existing `MediaSuggestionProvider` port
- Vercel AI Gateway adapter behind the same port
- review/accept/reject suggestion UX with no automatic rename
- persistent media and location catalog
- premium gallery and playback according to [PRODUCT.md](PRODUCT.md) and [ROADMAP.md](ROADMAP.md)

The fresh Orchestrator must choose the smallest safe next bounded step after public verification.

## 7. AI and privacy guardrails

Record for future tasks:

- cloud analysis is optional; local scan and gallery must remain functional without AI or internet
- representative frames may contain private imagery
- payloads require explicit user action (`--confirm-cloud-upload` today; future GUI equivalent)
- absolute local paths must never be transmitted
- only relative identifiers and metadata required by the prompt should be sent
- avoid whole-video upload initially
- no biometric or person-identification claim
- no automatic person naming
- no secret in source, database, logs, reports, tests, or subprocess arguments where avoidable
- API responses must be validated as untrusted external data
- provider output is suggestion evidence, not catalog truth
- user confirmation is mandatory before mutation

## 8. Session and context strategy

- initialize one fresh Worker instance assigned to the WORKER role per coherent Worker session
- subsequent tasks use short continuation prompts within the same Worker instance when safe
- do not close solely because automatic compaction occurred
- close when context pressure, coherence loss, usage limits, milestone boundaries, or domain shifts make continuation unsafe for the current Worker instance
- context pressure belongs to the Worker instance and Worker session, not to the persistent WORKER role
- update [NEXT_WORKER.md](NEXT_WORKER.md) only at Worker-session closeout
- update [NEXT_ORCHESTRATOR.md](NEXT_ORCHESTRATOR.md) only at Orchestrator-session closeout
- verify every closing handoff commit publicly
- do not manually copy repository handoffs into new Worker sessions; the fresh Worker instance reads handoffs from the repository

User-facing Worker prompts may use: `Toto pošli WORKEROVI ako jeden prompt:`

## 9. First response expected from fresh Orchestrator

The fresh Orchestrator must:

1. read and independently verify public repository state
2. resolve the final handoff commit after Cycle 051 closeout
3. verify both NEXT files against public raw content
4. summarize implemented state, Worker-observed test baseline, and live-validation evidence
5. identify any contradiction or stale claim
6. propose the smallest safe next task based on live-validation outcome
7. provide one authoritative prompt for a fresh Worker instance assigned to the WORKER role only after verification
8. not implement code in ORCHESTRATOR chat
9. not ask the Cooperator to paste repository files that already exist in the repository

## 10. Handoff lifecycle

- classification: non-authoritative Orchestrator-session handoff
- intended consumer: one fresh future ORCHESTRATOR session
- discoverability: repository root and Orchestrator bootstrap reading order
- retention: replace only at a future explicitly authorized Orchestrator closeout
- supersession and cleanup owner: explicitly authorized closing Worker instance
- Git history is the archive; the active tree must contain only the latest handoff

**Current outgoing ORCHESTRATOR session: CLOSED.**
