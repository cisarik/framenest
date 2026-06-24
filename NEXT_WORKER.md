# Next Worker Handoff

## 1. Purpose and authority

This file is a non-authoritative Worker-session handoff. It restores current context only. It is not a task and grants no implementation, command, filesystem, network, provider, secret, migration, dependency, or Git authority.

A fresh Worker instance assigned to the persistent WORKER protocol role requires one separate authoritative Orchestrator task prompt before doing any work. The future authoritative prompt is the only concrete task authority and overrides stale recommendations in this file.

The persistent protocol roles are COOPERATOR, ORCHESTRATOR, and WORKER. Concrete Orchestrator and Worker instances are temporary execution instances assigned to those persistent roles. Execution client, agent implementation, model, provider, instance, and session are separate identity layers. Do not describe a fresh Worker instance as a new persistent role.

Current Worker instance session: **CLOSED**. The persistent WORKER role continues.

## 2. Startup identity

- Repository: `https://github.com/cisarik/framenest.git`
- Normal working directory: `/Users/agile/framenest`
- Branch: `main`
- Expected handoff parent state before this closeout: `3e6008886ad7925ca14e171839ad479eafa443a0`
- Closeout commit: the commit containing this file; a fresh Worker instance must verify the actual current public `main` HEAD because this closeout commit is newer than the parent state above.

Mandatory early reading for a fresh Worker instance:

1. `AGENTS.md`
2. `BOOT_WORKER.md`
3. `AP_WORKER.md`
4. `NEXT_WORKER.md`
5. the future authoritative Orchestrator task prompt

Repository code, accepted ADRs, tests, Git history, and the future authoritative task override stale handoff claims.

## 3. Verified implementation state

FrameNest is a foundation-stage, pre-alpha, local-first, privacy-conscious library for video and animated media.

Implemented foundations include:

- CPython 3.13 and Poetry package foundation;
- centralized typed settings with loopback-safe server defaults and `FRAMENEST_DATABASE_PATH`;
- FastAPI application factory, typed unchanged `GET /health`, and loopback-first Uvicorn runtime through `framenest-server`;
- FrameNest-owned structured JSON logging and centralized redaction boundary;
- synchronous SQLAlchemy Core SQLite persistence with Alembic revisions through `0003`;
- explicit database commands: `framenest-db status` and `framenest-db migrate`;
- pure-domain identity primitives, `Device`, `Library`, and device-local `LibraryRoot`;
- application repository ports and SQLAlchemy Core adapters for device and library registries;
- development catalog CLI registration boundaries for devices and libraries;
- deterministic read-only library scan preview through the application scanner port and standard-library filesystem adapter;
- deterministic read-only local media analysis through the application preparation boundary and optional local `ffprobe`/`ffmpeg` infrastructure;
- provider-neutral AI suggestion boundary;
- NVIDIA NIM prototype with unresolved sanitized live response evidence;
- packaged vanilla HTML/CSS/JavaScript local application shell;
- ADR-0017 local web application delivery;
- `GET /` for the packaged web document;
- `/assets/{asset_name}` for packaged CSS and JavaScript;
- `GET /api/libraries` for read-only registered-library listing;
- explicit `POST /api/libraries/{library_id}/scan-preview` for bounded read-only scan preview;
- browser states for library loading, empty catalog, unavailable catalog, generic error, scan success, scanning, summary, truncation, and candidate rendering;
- same-origin and loopback security boundaries.

Current non-implemented boundaries include:

- no persistent media catalog;
- no storage-volume registry;
- no automatic migration on server startup;
- no automatic scan;
- no browser-visible library roots;
- no browser-visible secrets;
- no automatic AI;
- no persistent media records from scan candidates.

## 4. Latest Worker-observed runtime evidence

The following is Worker-observed evidence from the preceding cycles. A fresh Worker instance must rerun the baseline required by its future authoritative task.

Untouched Cycle 055 baseline before web/library browser work:

- `627` tests collected;
- `624 passed`;
- `3 skipped`.

Final Cycle 055 state:

- `644` tests collected;
- `641 passed`;
- `3 skipped`.

Additional final Cycle 055 evidence:

- full `-W error`: `641 passed`, `3 skipped`;
- targeted tests: `31 passed`;
- `poetry check --lock`: passed;
- `poetry run python -m compileall -q src tests`: passed;
- build and wheel inspection: passed;
- in-process API smoke: passed;
- no visual browser inspection was performed.

## 5. Latest commits

### Cycle 054

- SHA: `46da061d0443176a1067d18e30bf5aaff2259b3d`
- Parent: `d94b65bc761e754cfba9034d8ea21edb15406952`
- Subject: `feat: add local web application shell`
- Result: packaged local web application foundation and ADR-0017.

### Cycle 055

- SHA: `3e6008886ad7925ca14e171839ad479eafa443a0`
- Parent: `46da061d0443176a1067d18e30bf5aaff2259b3d`
- Subject: `feat: add read-only library browser`
- Result: real registered-library listing and explicit read-only scan-preview API/UI.

## 6. Security and mutation boundaries

- Do not inspect secrets without task-specific authority.
- `.secrets/nvidia.env.fish` remains ignored and must not be read, printed, hashed, encoded, committed, or reported without explicit task authority.
- Do not make any provider call without explicit authority.
- Do not run a library scan automatically on page load.
- Do not run migrations automatically.
- Do not persist media records.
- Do not rename, move, delete, tag, write sidecars, choose covers, download media, or mutate catalog truth.
- Do not expose non-loopback service behavior.
- Do not add CORS without authority.
- Do not use browser credentials.
- Do not install dependencies without authority.

## 7. Recommended next technical boundary

This is non-authoritative planning context, not a task.

The strongest next candidate is **user-triggered local media-analysis preview through the existing local web application**. The future Orchestrator should reassess this from current source before authorizing anything.

Likely intended scope:

- select one candidate produced by explicit scan preview;
- explicitly request local read-only analysis;
- reuse the existing deterministic media-analysis application service;
- return bounded technical metadata;
- make up to three exact-distinct representative PNG frames available to the browser through a deliberately designed bounded delivery contract;
- show a truthful local analysis state;
- no automatic analysis;
- no AI provider call;
- no cloud transmission;
- no persistence;
- no temporary frame files left behind;
- no arbitrary file access;
- no path traversal;
- no raw absolute media path in browser output;
- no media streaming or full playback;
- no cover selection yet.

The future Orchestrator must inspect and decide:

- whether frames should use bounded inline encoding, a short-lived in-memory resource contract, or another testable same-origin mechanism;
- request and response size limits;
- cancellation and timeout behavior;
- content types and cache headers;
- safe resolution of library ID plus relative candidate path;
- API error sanitization;
- lifecycle and cleanup of any transient frame representation.

This handoff does not pre-accept any of those alternatives.

## 8. Additional future boundaries

- Persistent media catalog and migration `0004` remain undecided.
- Premium gallery cards, covers, playback, downloads, Settings, provider selection, model discovery, and editable AI review remain future tasks.
- AI remains on-demand.
- AI output remains editable suggestion only.
- Cover timestamp remains independent of playback start.
- Normal Play must begin at `00:00`.
- Unresolved NVIDIA `content=null` plus `reasoning_content` evidence remains preserved but must not block local UI progress.
- Reasoning content must not be surfaced as the user-facing suggestion.

## 9. Sanitized NVIDIA evidence

Preserved sanitized facts only:

- the last real synthetic provider call reached NVIDIA;
- HTTP `200`;
- one choice;
- `finish_reason=stop`;
- assistant `content=null`;
- assistant `reasoning_content` was a short string;
- no refusal;
- no tool calls;
- returned model: `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning`;
- strict parser remained closed;
- no successful real `printit.mp4` suggestion preview followed that diagnosis.

No raw reasoning content is included here.

## 10. Handoff lifecycle

- Classification: non-authoritative Worker-session handoff.
- Intended consumer: fresh Worker instances during bootstrap.
- Discoverability: repository root and Worker bootstrap reading order.
- Retention: replace only at a future explicitly authorized Worker-session closeout.
- Supersession and cleanup owner: a future closing Worker instance acting under explicit Orchestrator authority.
- Git history is the archive; the active tree should contain only the latest handoff.

Current Worker instance session: **CLOSED**. The persistent WORKER role continues.
