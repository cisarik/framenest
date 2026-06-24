# Next Orchestrator Handoff

## 1. Role restoration

Michal is the COOPERATOR and strategic owner. The fresh ChatGPT chat is the ORCHESTRATOR. Repository execution agents are WORKER.

The ORCHESTRATOR communicates with Michal in Slovak and uses feminine grammatical gender. Worker prompts and reports are English. Worker reports must begin exactly with:

`### Report for ORCHESTRATOR_CHAT`

The ORCHESTRATOR independently verifies public commits and raw file content. Issue one bounded task at a time. Analytic Programming is provider- and model-neutral. The repository, accepted ADRs, tests, and Git history are the source of truth.

This file restores orchestration state only. It is not an executable task and grants no implementation or Git authority.

**Current outgoing ORCHESTRATOR session: CLOSED.**

## 2. Repository restoration

- Repository: `https://github.com/cisarik/framenest.git`
- Local path used by the closing Worker: `/Users/agile/framenest`
- Branch: `main`
- Pre-handoff public HEAD: `c4a80b40f89f67e0aadc66d02536cbd6626acef3`
- Pre-handoff subject: `feat: add library scan preview`
- Pre-handoff parent: `0c5795baedfcacaf1334e6bb5e4e62f682888ab4`

The fresh Orchestrator must resolve the final handoff commit from public `main` after the closeout push. Do not assume this file contains the post-handoff SHA.

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
10. [docs/adr/README.md](docs/adr/README.md) and ADR-0001 through ADR-0014
11. task-relevant source and tests
12. recent public Git history from the persistence foundation through the final handoff commit

## 3. Verified project state

### Directly committed public facts

The repository implements:

- centralized typed settings with loopback-safe defaults
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
- application scan values, `LibraryScanner` port, `PreviewLibraryScan`, and `LocalLibraryScanner`
- `framenest-catalog library scan-preview` with deterministic JSON output and sanitized errors

There is no migration `0004`, no media table, no storage-volume table, no FFmpeg/ffprobe integration, no AI provider, and no media persistence from scanning.

### Closing-Worker-observed runtime evidence

At pre-handoff HEAD `c4a80b40f89f67e0aadc66d02536cbd6626acef3`:

- CPython `3.13.14` in project `.venv/`
- Poetry `2.1.4`
- `poetry check --lock`: passed
- `poetry run pytest --collect-only -q`: **487 tests collected**
- `poetry run pytest -q`: **487 passed**
- `poetry run pytest -q -W error`: **487 passed**
- zero observed pytest warnings

The fresh Orchestrator and Worker must reverify these values from the final public commit.

### Recent public commit sequence

Meaningful sequence through scan preview:

- `4a2a167` — SQLite persistence foundation
- `bf82ad4` / `dcb9f68` — stable domain identities
- `07dbd94` — device registry core
- `a872265` — device catalog CLI
- `8d800e8` — library registry core
- `b90b680` — library catalog CLI
- `c4a80b4` — library scan preview and ADR-0014

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
- API keys for remotely consumed AI features must eventually remain server-side, not in ordinary client installations

See [PRODUCT.md](PRODUCT.md) and [SPEC.md](SPEC.md) for normative detail.

## 5. Newly clarified COOPERATOR AI intent

**Strategic intent only — not accepted architecture and not implemented.**

### Test corpus

The Cooperator states that the current local test corpus lives at:

`/Users/agile/Video`

The corpus consists of MP4 and GIF meme media. Representative filenames include:

- `HAaXdF3XMAAeahd.mp4`
- `G_MCaLEXcAE7EHb.mp4`
- `decart-realtime-1763826467496.mp4`
- readable names such as `haha.mp4`, `moonufo.mp4`, and `screaming.mp4`

### Desired future behavior

When eventually authorized:

- detect suspicious or non-informative filenames
- extract approximately three representative visual frames from videos and GIFs
- include technical metadata in the analysis payload
- send only an explicitly approved analysis payload to an optional cloud VLM
- obtain structured suggestions for:
  - concise title
  - description
  - English canonical tags
  - collection or category
  - safe suggested filename preserving extension
  - confidence
  - observed evidence
  - uncertainties
- classify this test corpus as appropriate for a canonical `Meme` tag or collection when supported by evidence
- never invent people, places, dates, or events
- never automatically rename, move, categorize, or tag without explicit user confirmation
- preserve the original file until an authorized confirmed operation exists
- support MP4 and GIF first without assuming every source has three distinct decodable frames
- prefer uploading representative frames and metadata rather than complete private videos for the first cloud prototype

None of this is implemented. No provider, frame extractor, suggestion schema, or confirmation workflow exists in the repository.

## 6. Current provider research to reverify

**Time-sensitive non-authoritative research dated 2026-06-24.**

The next Orchestrator must reverify official primary sources before authorizing integration. No provider is accepted yet. No free quota is guaranteed permanently.

### NVIDIA NIM

Candidate model:

`nvidia/nemotron-3-nano-omni-30b-a3b-reasoning`

Current official pages indicate:

- image, video, audio, and text understanding
- a hosted free endpoint
- free NVIDIA Developer Program access for prototyping
- OpenAI-compatible hosted base URL: `https://integrate.api.nvidia.com/v1`
- trial or development terms rather than a guaranteed unrestricted production service

Official references:

- `https://build.nvidia.com/nvidia/nemotron-3-nano-omni-30b-a3b-reasoning`
- `https://docs.api.nvidia.com/nim/docs/product`
- `https://docs.api.nvidia.com/nim/docs/api-quickstart`

Also consider, without accepting:

`nvidia/nemotron-nano-12b-v2-vl`

Direct NVIDIA NIM is currently the preferred first no-cost prototype candidate.

### Vercel AI Gateway

Current official evidence indicates:

- OpenAI-compatible API
- image inputs
- model routing and usage tracking
- pay-as-you-go pricing
- some unpaid accounts currently receive recurring small gateway credits
- vision-capable NVIDIA model listing: `nvidia/nemotron-nano-12b-v2-vl`

Official references:

- `https://vercel.com/docs/ai-gateway`
- `https://vercel.com/docs/ai-gateway/openai-compat/chat-completions`
- `https://vercel.com/docs/ai-gateway/pricing`
- `https://vercel.com/ai-gateway/models/nemotron-nano-12b-v2-vl`

Vercel AI Gateway is a useful alternate adapter and may use the Cooperator's existing credits.

### Research guardrails

- provider and model selection must stay outside domain and application policy
- a fake deterministic provider is required for tests
- network tests must not be part of the default test suite
- no API key may be committed, logged, returned, or stored in the catalog database

## 7. Recommended orchestration sequence

Strategy for the fresh Orchestrator to reassess — not an executable task.

### Stage A — local analysis-preparation boundary

Potential ADR for:

- `ffprobe` metadata extraction
- `ffmpeg` deterministic frame extraction
- approximately three representative distinct frames
- MP4 and GIF handling
- temporary artifact lifecycle and cleanup
- no network
- no catalog mutation
- explicit external-tool detection and version evidence
- deterministic tests with tiny media fixtures

This is likely the first new Worker task after repository verification.

### Stage B — provider-neutral AI suggestion boundary

Define:

- application request and result types
- provider protocol
- structured suggestion schema
- title, description, English tags, category, safe filename, confidence, evidence, uncertainties
- fake provider for tests
- no network in default tests
- no automatic file action

### Stage C — NVIDIA NIM prototype adapter

Implement only with explicit opt-in:

- secret from environment or future secret store
- three-frame multimodal request
- strict structured response validation
- timeouts and bounded retry policy
- sanitized errors
- no secrets or private absolute paths in logs
- manually invoked smoke test excluded from normal tests

### Stage D — Vercel AI Gateway adapter or fallback

Only after provider-neutral behavior exists.

### Stage E — review and confirmation workflow

Only after suggestion quality is proven:

- show original name and preview evidence
- show proposed title, tags, and filename
- explicit accept, edit, or reject
- no automatic rename
- eventual audit-safe file operation boundary

### Stage F — persistent media and location catalog

Do not prematurely combine this with cloud-provider integration.

The fresh Orchestrator must choose the smallest safe next bounded step after public verification.

## 8. AI and privacy guardrails

Record for future tasks:

- cloud analysis is optional; local scan and gallery must remain functional without AI or internet
- representative frames may contain private imagery
- payloads require explicit user action
- absolute local paths must never be transmitted
- only relative identifiers and metadata required by the prompt should be sent
- avoid whole-video upload initially
- no biometric or person-identification claim
- no automatic person naming
- no secret in source, database, logs, reports, tests, or subprocess arguments where avoidable
- API responses must be validated as untrusted external data
- provider output is suggestion evidence, not catalog truth
- user confirmation is mandatory before mutation

## 9. Explicitly unresolved decisions

Do not treat these as decided:

- exact frame-position algorithm
- treatment of media with fewer than three distinct frames
- ffmpeg and ffprobe installation and version policy across macOS, Fedora, and Windows
- frame dimensions and image format
- temporary storage versus in-memory frames
- frame cleanup policy
- provider selection and model
- structured-output compatibility with chosen models
- free quota, rate limits, and retention terms
- retry and timeout policy
- prompt versioning
- tag vocabulary and synonym policy beyond canonical English and intended `Meme`
- filename normalization rules
- whether suggestions are persisted before confirmation
- cloud-data retention and provider privacy terms
- media and physical-location schema
- relationship between AI suggestions, sidecars, and durable catalog metadata

## 10. Session and context strategy

- one fresh Worker bootstrap per coherent Worker session
- subsequent tasks use short continuation prompts
- do not close solely because automatic compaction occurred
- close when context pressure, coherence loss, usage limits, milestone boundaries, or domain shifts make continuation unsafe
- update [NEXT_WORKER.md](NEXT_WORKER.md) only at Worker-session closeout
- update [NEXT_ORCHESTRATOR.md](NEXT_ORCHESTRATOR.md) only at Orchestrator-session closeout
- verify every closing handoff commit publicly
- do not manually copy repository handoffs into new Worker sessions; the fresh Worker reads handoffs from the repository

User-facing Worker prompts may use: `Toto pošli WORKEROVI ako jeden prompt:`

## 11. First response expected from fresh Orchestrator

The fresh Orchestrator must:

1. read and independently verify public repository state
2. resolve the final handoff commit
3. verify both NEXT files against public raw content
4. summarize implemented state and test evidence
5. reverify current official NVIDIA and Vercel facts from primary sources
6. identify any contradiction or stale claim
7. propose the smallest safe next task
8. provide one authoritative fresh-WORKER prompt only after verification
9. not implement code in ORCHESTRATOR chat
10. not ask the Cooperator to paste repository files that already exist in the repository

## 12. Handoff lifecycle

- classification: non-authoritative Orchestrator-session handoff
- intended consumer: one fresh future ORCHESTRATOR session
- discoverability: repository root and Orchestrator bootstrap reading order
- retention: replace only at a future explicitly authorized Orchestrator closeout
- supersession and cleanup owner: explicitly authorized closing Worker
- Git history is the archive; the active tree must contain only the latest handoff

**Current outgoing ORCHESTRATOR session: CLOSED.**
