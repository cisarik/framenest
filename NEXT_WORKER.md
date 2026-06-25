# Next Worker Handoff

## Authority And Startup

This file is a non-authoritative Worker-session handoff. It restores current
context only. It is not a task and grants no implementation, command,
filesystem, network, provider, secret, migration, dependency, or Git authority.

The persistent protocol role is WORKER. A Worker instance/session is one
temporary execution-agent lifecycle assigned to that persistent role. Do not
describe a fresh Worker instance as a new persistent role.

Repository: `https://github.com/cisarik/framenest.git`

Working directory: `/Users/agile/framenest`

Branch: `main`

A fresh Worker instance must verify the public closeout commit that replaced
this file, then follow only the future authoritative Orchestrator task.

Mandatory early reading for a fresh Worker instance:

1. `AGENTS.md`
2. `BOOT_WORKER.md`
3. `AP_WORKER.md`
4. `NEXT_WORKER.md`
5. `AP.md`
6. `AP_ORCHESTRATOR.md`
7. `PRODUCT.md`
8. `SPEC.md`
9. `ROADMAP.md`
10. `README.md`
11. `docs/adr/README.md`
12. the future authoritative Orchestrator task prompt

Repository code, tests, accepted ADRs, Git history, and the future authoritative
task override stale handoff claims.

## Current Implemented State Through Cycle 060

FrameNest is a foundation-stage, pre-alpha, local-first library for video and
animated media.

Implemented foundations include:

- CPython 3.13 and Poetry package foundation;
- centralized typed settings with loopback-safe server defaults;
- FastAPI application factory and typed unchanged `GET /health`;
- loopback-first Uvicorn runtime through `framenest-server`;
- FrameNest-owned structured JSON logging and redaction boundary;
- synchronous SQLAlchemy Core SQLite persistence with Alembic revisions through
  `0003`;
- explicit `framenest-db status` and `framenest-db migrate`;
- pure-domain identity primitives;
- pure-domain `Device`, `Library`, and device-local `LibraryRoot`;
- application repository ports and SQLAlchemy Core adapters for device and
  library registries;
- development catalog CLI for device/library registration and preview commands;
- deterministic read-only library scan preview;
- deterministic read-only local media-analysis preview;
- provider-neutral AI suggestion boundary;
- NVIDIA NIM prototype with JPEG VLM image input;
- one successful documented non-thinking live provider validation from Cycle
  059;
- packaged vanilla HTML/CSS/JavaScript local web shell;
- same-origin registered-library listing, scan-preview, and media-analysis
  preview APIs;
- sanitized AI capability API;
- explicit cloud confirmation for AI suggestion preview;
- editable non-persistent AI suggestion review in the browser.

Not implemented:

- no persistent media catalog;
- no gallery persistence;
- no logical media or physical-location persistence;
- no storage-volume registry;
- no durable cover or thumbnail pipeline;
- no desktop shell;
- no Tauri scaffold;
- no NUC deployment;
- no server aggregation;
- no streaming or transfer implementation;
- no GUI Settings or secret-store adapter.

## Latest Worker-Observed Validation

The following is Worker-observed evidence from Cycle 060. A fresh Worker must
rerun whatever validation its future authoritative task requires.

- Final collection: `723` tests collected.
- Full result: `720 passed`, `3 skipped`.
- Full `-W error`: `720 passed`, `3 skipped`.
- Targeted Cycle 060 suite: `55 passed`.
- `poetry check --lock`: passed.
- `poetry run python -m compileall -q src tests`: passed.
- `poetry build`: passed.
- Wheel inspection: passed for new API module, updated app composition, updated
  web assets, and credential loader.
- Fake-dependency smoke: passed for capability, confirmation gate, success,
  sanitized body, and unconfigured provider.
- No live provider call occurred in Cycle 060.
- No browser visual inspection occurred in Cycle 060.

## Sanitized Live NVIDIA Evidence

Preserved sanitized Cycle 059 evidence only:

- one explicit NVIDIA call;
- HTTP `200`;
- no polling;
- final content was non-empty;
- reasoning content was absent;
- strict parsing succeeded;
- usage was `1316` prompt tokens, `400` completion tokens, and `1716` total
  tokens;
- no mutation occurred.

Do not include raw provider content in prompts, reports, docs, or logs.

## Accepted Architecture Direction

ADR-0021 accepts Tauri v2 as the future desktop shell. The shell will display
the existing HTML/CSS/JavaScript UI in a native WebView, supervise a packaged
Python/FastAPI sidecar, use a single-instance lifecycle, provide tray or macOS
menu-bar behavior, and initially expose `Gallery`, `Settings`, and `Quit`.

Implementation remains MacBook-first, while cross-platform architecture
boundaries remain required. Browser mode remains development and diagnostic
mode, not the normal end-user desktop UX.

ADR-0022 accepts selective media placement and optional server aggregation. Each
desktop owns a complete local catalog for local operation. The NUC comes later
as an optional archive/aggregator, remote streaming/download source, transfer
receiver, later centralized AI-provider boundary, and future backup participant.

FrameNest models one logical media item with zero or more physical locations.
The gallery should show logical media cards rather than duplicate physical-file
cards. Remote-only cards should remain visible through metadata, covers,
availability summaries, and derived thumbnails without downloading full media.

Search direction includes title search and multi-tag filtering. Multiple
selected tags default to AND/intersection semantics.

The priority MEME scenario is a NUC-hosted `Meme` archive where another desktop
can browse, search, stream, or explicitly download GIF and short MP4 media
without storing all bytes locally.

`Download + Copy to Clipboard` is accepted as a future native desktop capability
for GIF and short MP4 workflows, with verified download and fallback behavior.

## Non-Authoritative Next Recommendation

The strongest next implementation candidate is the minimum persistent local
media catalog on MacBook.

A fresh Orchestrator must inspect current domain, identity, persistence,
migration, tag, cover, and scan boundaries before authorizing it.

Likely required concepts include:

- logical media;
- physical media locations;
- canonical tags;
- catalog persistence;
- idempotent import from explicit scan results;
- search-ready title/tag data;
- no file mutation;
- migration `0004` only after a dedicated accepted decision.

This handoff does not pre-authorize schema details.

Tauri scaffolding and NUC implementation are not the immediate next
implementation task.

## Session State

Current Worker instance session: CLOSED.
