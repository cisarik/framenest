# Next Worker Handoff

## Authority

This file is a non-authoritative Worker-session handoff. It restores current
context only. It is not a concrete task and grants no modification, command,
Git, migration, dependency, secret, network, provider, private-data,
filesystem, deployment, or implementation authority.

Only a future authoritative ORCHESTRATOR prompt may grant a concrete task.

`WORKER` is the persistent protocol role. A Worker instance/session is one
temporary concrete execution lifecycle assigned to that role. Do not describe a
fresh Worker instance as a new persistent role.

## Repository Identity

Repository: `https://github.com/cisarik/framenest.git`

Normal working directory: `/Users/agile/framenest`

Branch: `main`

A future Worker must verify the repository, working directory, and branch from
current Git state rather than trusting this handoff blindly.

## Fresh Worker Startup Reading Order

A fresh Worker instance must read at minimum:

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
12. task-relevant accepted ADRs
13. the future authoritative ORCHESTRATOR task prompt

Repository code, tests, accepted ADRs, public Git evidence, and the future
authoritative task override stale handoff claims.

## Current Implemented State Through Cycle 062

FrameNest is a foundation-stage, pre-alpha, local-first library for video and
animated media.

Implemented foundations include:

- CPython 3.13 and Poetry package foundation;
- centralized typed settings;
- loopback-first FastAPI application factory and Uvicorn runtime through
  `framenest-server`;
- typed unchanged `GET /health`;
- packaged vanilla HTML/CSS/JavaScript local web shell;
- FrameNest-owned structured JSON logging and redaction boundary;
- synchronous SQLAlchemy Core SQLite persistence with explicit Alembic
  migrations through revision `0004`;
- explicit `framenest-db status` and `framenest-db migrate`;
- no automatic server migration;
- stable pure-domain identity primitives;
- local device and library registries with application repository ports and
  SQLAlchemy Core adapters;
- deterministic read-only library scan preview;
- deterministic read-only local media-analysis preview;
- provider-neutral AI suggestion boundary;
- NVIDIA NIM prototype with JPEG VLM image input;
- sanitized AI capability API;
- explicit cloud confirmation for AI suggestion preview;
- editable non-persistent AI suggestion review in the browser;
- minimum persistent media catalog foundation.

The minimum persistent media catalog foundation includes:

- persistent logical media;
- persistent physical locations;
- stable logical media identities;
- stable physical media-location identities;
- media kinds `video` and `animated_image`;
- availability states `available`, `offline`, `missing`, `unverified`, and
  `archived`;
- normalized slash-separated library-relative paths;
- physical filename derived from the final path component;
- no duplicated filename column;
- no duplicated `device_id` on physical media-location records;
- one logical media item with zero or more physical locations;
- uniqueness for each exact `(library_id, relative_path)` location;
- restrictive foreign keys to logical media and libraries;
- no destructive cascading deletion;
- application `MediaRepository` port;
- SQLAlchemy Core adapter;
- Alembic migration `0004`.

## Explicitly Unimplemented State

The following remain unimplemented:

- explicit persistent import from scan candidates;
- user-editable persistent title, description, collection, and suggested
  filename;
- canonical tags;
- title/tag search;
- manual metadata detail;
- persistent AI drafts;
- covers and thumbnails;
- persistent premium gallery;
- catalog API exposure for persistent media records;
- normal catalog CLI media commands;
- automatic duplicate detection;
- content hashes and perceptual hashes;
- file mutation workflows;
- Tauri desktop shell;
- NUC deployment;
- server aggregation;
- streaming;
- transfer;
- GUI Settings and final secret-store integration.

## Relevant Accepted Architecture

ADR-0021 accepts Tauri v2 as the future desktop shell. It is not implemented and
is not the immediate next task.

ADR-0022 accepts selective media placement, one logical medium with several
locations, desktop-owned local catalogs, and later optional server aggregation.
NUC deployment, streaming, synchronization, and transfer remain future work.

ADR-0023 accepts a manual-first metadata workspace and separate AI drafts.
Opening detail must not call AI, save catalog metadata, or mutate files.
Manual metadata, AI drafts, catalog save, and filesystem rename are distinct
future boundaries.

ADR-0024 accepts a manual Cover Studio and optional AI-generated cover
candidates. Cover candidates do not become active without explicit human
acceptance. Cover persistence and derived thumbnails remain future work.

ADR-0025 accepts the minimum persistent logical-media and physical-location
catalog foundation in migration `0004`.

Tauri and NUC work are not the immediate next task.

## Cycle 062 Commit Evidence

Cycle 062 commit: `32794797d2d5c2dcd2c3d4982cd5a23ad0fc9d5e`

Parent: `c8bda2139a2d931c57620f0564bff17976d6cfd6`

Subject: `feat: add persistent media catalog foundation`

The commit introduced ADR-0025, the logical media and physical-location domain
model, the `MediaRepository` port, the SQLAlchemy Core adapter, migration
`0004`, migration tests, repository contract tests, domain tests, and bounded
documentation updates.

This handoff does not hardcode its own future closeout commit SHA. A future
Worker must discover and verify the commit containing this handoff.

## Worker-Observed Validation Evidence

Initial untouched baseline before Cycle 062 edits:

- `723 tests collected`;
- `720 passed`;
- `3 skipped`;
- warning-as-error run: `720 passed`, `3 skipped`.

Final Cycle 062 validation:

- migration-focused subset: `36 passed`;
- targeted domain/repository subset: `176 passed`;
- `790 tests collected`;
- full suite: `787 passed`, `3 skipped`;
- warning-as-error run: `787 passed`, `3 skipped`;
- Poetry lock check passed;
- compileall passed;
- package build passed;
- wheel inspection passed;
- empty database to `0004` passed;
- populated `0003` to `0004` passed with device/library rows preserved;
- `0004` to `0003` passed with only media-catalog objects removed;
- Markdown links passed;
- final worktree was clean;
- no live provider call;
- no private-media access;
- no user-database migration.

A future Worker must rerun whatever validation its own authoritative task
requires.

## Sanitized Live NVIDIA Evidence

Preserved sanitized Cycle 059 evidence only:

- one explicit authorized NVIDIA call;
- HTTP `200`;
- no polling;
- final content non-empty;
- reasoning content absent;
- strict parsing succeeded;
- `1316` prompt tokens;
- `400` completion tokens;
- `1716` total tokens;
- no mutation.

Do not include raw provider content in prompts, reports, docs, or logs. One
successful call does not guarantee future provider behavior. No provider call
occurred in Cycle 062.

## Strongest Next Implementation Recommendation

The strongest next bounded implementation candidate is explicit idempotent
import from selected scan candidates.

This is a recommendation, not task authority. A future Orchestrator must inspect
and resolve at least:

- scan candidate identity and current fields;
- explicit user selection boundary;
- mapping from scan candidate to logical media and physical location;
- whether one import operation creates both records atomically;
- idempotency key;
- duplicate `(library_id, relative_path)` handling;
- behavior when a location already exists;
- behavior when a logical media item already exists;
- transaction boundaries;
- partial failure behavior;
- no automatic import during scan;
- no filesystem mutation;
- no title/tag/cover scope unless separately authorized;
- API/CLI/UI exposure boundary;
- tests and migration implications;
- whether a new ADR is required before implementation.

This handoff does not pre-authorize the solution. Do not propose Tauri or NUC as
the next task.

## Session State

Current concrete Worker session: `CLOSED`.

The Worker that produced Cycle 062 must not receive another task. A future task
requires a fresh Worker instance assigned to the `WORKER` role. FrameNest
remains on its current single-Worker workflow. No future task is granted by
this handoff.

## Artifact Lifecycle

Classification: replaceable Worker-session handoff.

Consumers: future ORCHESTRATOR and future Worker instance.

Authority: contextual and non-authoritative.

Retention: until replaced by a future explicitly authorized Worker closeout.

Update owner: a Worker acting under explicit ORCHESTRATOR closeout authority.

Cleanup: replacement rather than accumulation; Git history remains the archive.
