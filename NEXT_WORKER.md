# Next Worker Handoff

## 1. Title and authority

This file is a non-authoritative repository-native Worker handoff. It restores
context for a future fresh Worker instance only.

It grants no modification, migration, dependency, secret, network, provider,
private-media, filesystem, deployment, Git-write, or implementation authority.
It does not authorize work merely because a direction or risk is recorded here.

Only one future authoritative ORCHESTRATOR prompt may grant a concrete task.
Boot files, AP methodology documents, ADRs, roadmap documents, and handoff files
do not independently authorize implementation.

## 2. Role and instance model

`WORKER` is the persistent protocol role in FrameNest's repository protocol.
A concrete Worker instance is one execution agent assigned to that role for a
bounded lifecycle. A Worker session is that instance's active continuity of
context and responsibility. The execution client, agent implementation, model,
and provider may vary between sessions and do not change the protocol role.

Context pressure and automatic compaction can make one concrete session less
reliable over time. This handoff closes the current concrete Worker session
after Cycle 065. After this closeout commit, this concrete Worker instance is
permanently closed and must never receive another task.

No active Worker instance exists after this closeout. A future Worker must be a
fresh instance newly assigned to the persistent `WORKER` role.

## 3. Repository identity

Repository URL: `https://github.com/cisarik/framenest.git`

Normal working directory: `/Users/agile/framenest`

Normal branch: `main`

Current public HEAD before this closeout commit:
`a13134551cfefee330afa14dcbbece3bcb1c46f5`

Subject before this closeout commit:
`feat: add persistent title and canonical tags`

A future Worker must verify the repository root, remote URL, branch, cleanliness,
local HEAD, tracking branch, and public remote state before acting. Do not trust
the recorded SHAs blindly, and do not invent this closeout commit SHA from this
document.

## 4. Fresh Worker startup reading order

A future fresh Worker must read at least:

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
11. `AI_WORKSPACE.md`
12. `GALLERY.md`
13. `COVER_PIPELINE.md`
14. `docs/adr/README.md`
15. task-relevant accepted ADRs
16. task-relevant implementation and tests
17. the future authoritative ORCHESTRATOR prompt

Repository implementation, tests, accepted ADRs, public Git evidence, and the
future authoritative prompt override stale handoff statements.

## 5. Current implemented state through Cycle 065

FrameNest is a foundation-stage, pre-alpha, local-first library for video and
animated media.

The public repository currently includes:

- CPython 3.13 and Poetry package foundation;
- centralized settings and package-mode source layout;
- FastAPI loopback-first local server and Uvicorn runtime through
  `framenest-server`;
- typed health endpoint;
- packaged vanilla same-origin local web shell;
- FrameNest-owned structured logging and redaction boundary;
- explicit SQLite/Alembic persistence through migration head `0005`;
- explicit `framenest-db status` and `framenest-db migrate`;
- no automatic server migration;
- stable domain identity primitives;
- local device registry;
- local library registry;
- deterministic read-only library scan preview;
- deterministic local media-analysis preview;
- provider-neutral AI suggestion boundary;
- NVIDIA NIM prototype with explicit cloud confirmation;
- minimum logical-media and physical-location catalog;
- explicit idempotent scan-candidate import;
- persistent display-title metadata;
- persistent canonical tags;
- ordered media-to-tag assignments;
- sparse media metadata rows;
- application ports, use cases, SQLAlchemy Core repositories, migrations, and
  same-origin API boundaries for the implemented catalog slices.

Do not describe import, display title, canonical tags, or migration `0005` as
unimplemented.

## 6. Cycle 063 implementation

Public commit:
`cfd4a01524045bce0a05059bafc230c36182ea0e`

Parent:
`cd4071cd391ca3c33238679813e1dd39c785ef83`

Subject:
`feat: add explicit scan candidate import`

Cycle 063 added ADR-0026 and an end-to-end explicit scan-candidate import
vertical slice.

Accepted public behavior:

- scan preview remains read-only;
- import is explicit and user-triggered;
- request uses one library-relative path;
- the server revalidates the selected path through a fresh bounded scan;
- client-provided kind and size are not trusted;
- scan `video` maps to persistent `video`;
- scan `gif` maps to persistent `animated_image`;
- one logical media row and one physical-location row are inserted atomically;
- exact `(library_id, relative_path)` is the idempotency key;
- repeated import returns the existing logical media and location identities;
- no filesystem mutation occurs;
- no migration beyond `0004` was required for import;
- exact API endpoint: `POST /api/libraries/{library_id}/media-imports`.

Cycle 063 changed 20 public paths, including ADR-0026, import application/API
code, browser import controls, media repository updates, and tests.

## 7. Cycle 064 private-corpus evidence

Classification: Worker-observed private runtime evidence.

Cycle 064 produced no repository commit and did not change the repository. It
was a read-only private-corpus smoke validation using `dicaprio_bravo.gif`, one
deterministic MP4 candidate, a disposable catalog, and the real FastAPI
application/import boundary.

Sanitized observed result:

- first MP4 import returned `created`, kind `video`;
- first GIF import returned `created`, kind `animated_image`;
- repeated imports returned `already_imported`;
- media and location identities were stable across repeat imports;
- the disposable catalog contained exactly two logical media rows;
- the disposable catalog contained exactly two physical-location rows;
- zero duplicate rows were observed;
- selected source-file SHA-256, size, and mtime were unchanged;
- the top-level directory-entry snapshot was unchanged;
- no sidecars or derivatives were created;
- no provider, AI, ffmpeg, ffprobe, secret, or user-catalog access occurred;
- temporary resources were cleaned up completely;
- repository state was unchanged.

Do not expose the selected MP4 filename, private hashes, directory listings,
database identifiers, other private filenames, raw frames, private metadata, or
media contents. The existence of `/Users/agile/Video` grants no future access.
Any future private-media access requires exact task-specific authority. Any
cloud or provider transmission requires separate explicit authorization.

## 8. Cycle 065 implementation

Public commit:
`a13134551cfefee330afa14dcbbece3bcb1c46f5`

Parent:
`cfd4a01524045bce0a05059bafc230c36182ea0e`

Subject:
`feat: add persistent title and canonical tags`

Cycle 065 added ADR-0027 and the persistent display-title and canonical-tag
core through migration `0005`. The public diff changed 28 paths.

### Display title

- display title is optional persisted catalog metadata;
- display title is separate from filename and library-relative path;
- saving or clearing a title does not imply rename or filesystem mutation;
- title absence is valid;
- metadata is stored as a sparse row, so imported media need not have metadata.

### Canonical tags

- canonical tag identity is a stable English lowercase slug key;
- display name is separate presentation text;
- no UUID tag identity is introduced;
- tag creation is explicit;
- same key with the same display name is idempotent;
- same key with a different display name is a conflict;
- metadata save cannot implicitly create tags;
- tag deletion and rename are not implemented yet.

### Media metadata

- one logical medium may have zero to 32 ordered canonical tags;
- order is persisted as zero-based positions;
- saving metadata atomically replaces the full ordered assignment set;
- an empty tag list removes assignments;
- an exact semantically identical save returns `unchanged`;
- unchanged saves preserve `updated_at_ms`;
- save statuses are `created`, `updated`, and `unchanged`;
- first save and replacement save are atomic;
- rollback preserves the previous complete state.

### API

Exact endpoints:

- `POST /api/canonical-tags`
- `GET /api/canonical-tags`
- `GET /api/media/{media_id}/metadata`
- `PUT /api/media/{media_id}/metadata`

### Migration

Migration head is `0005`.

Revision `0005` adds:

- `canonical_tags`;
- `media_metadata`;
- `media_canonical_tags`.

Existing device, library, logical-media, and physical-location data survives
upgrade. No metadata rows are automatically backfilled. Downgrade removes only
the metadata/tag schema introduced by `0005`.

## 9. Accepted ADR state

The ADR index extends through ADR-0027.

Selected accepted decisions near the current horizon:

- ADR-0021: Tauri v2 is accepted as the future desktop shell. It is not
  implemented.
- ADR-0022: selective media placement and later optional server aggregation are
  accepted future architecture. NUC aggregation is not implemented.
- ADR-0023: manual-first metadata workspace and separate AI drafts are accepted.
  Manual `Current` metadata and AI drafts must remain distinct.
- ADR-0024: Cover Studio and candidate-based cover workflow are accepted future
  architecture. Cover persistence and thumbnail generation are not implemented.
- ADR-0025: minimum persistent logical-media and physical-location catalog.
- ADR-0026: explicit idempotent import from selected scan candidates.
- ADR-0027: persistent display title and canonical tags.

Accepted future architecture is not the same as implemented functionality.

## 10. Explicitly unimplemented state

Major remaining work includes:

- title search;
- canonical-tag filtering;
- multi-tag AND filtering;
- catalog media-list/read-model endpoint suitable for gallery;
- browser metadata workspace;
- premium tag-chip editor;
- description;
- collection;
- suggested filename;
- source-platform structured field;
- browser persistence of metadata;
- persistent AI drafts;
- manual Cover Studio implementation;
- exact cover timestamp persistence;
- thumbnail generation and persistence;
- premium persistent gallery;
- filesystem rename, move, and delete workflows;
- native OS tag synchronization;
- duplicate, content-hash, and perceptual-hash workflows;
- Tauri desktop shell;
- native tray/menu-bar;
- native clipboard, download, export, and VLC capabilities;
- NUC aggregation;
- remote streaming and transfer;
- GUI Settings and final secret-store integration;
- supported release, installer, deployment, and systemd/Tailscale production
  setup.

Do not claim that no catalog, no import, no title, or no tags exist.

## 11. Manual-first product invariants

- AI is optional and explicit.
- Manual metadata is primary.
- AI drafts must remain separate from `Current`.
- AI never silently overwrites catalog truth.
- Catalog save is distinct from filesystem rename.
- Cover timestamp never changes normal playback start.
- Canonical tags use stable English identities.
- No provider call is automatic.
- No catalog or filesystem mutation is automatic.

## 12. Security and privacy boundaries

FrameNest remains loopback-first and local-first. Server startup does not run
migrations automatically.

Security and privacy boundaries:

- no credential exposure to the browser;
- no credentials in the catalog database;
- no implicit private-media authority;
- no cloud upload without explicit confirmation;
- no filename, path, SQL, database path, secret, or provider leakage through
  errors;
- deterministic temporary fixtures should be preferred before private smoke;
- task-specific authority is required for secrets, provider calls, real catalog
  migration, private-media access, or media mutation.

## 13. Validation evidence

### Publicly committed evidence

Relevant public commits:

- `e2983920c2c5aeac101dc9e51efcacc801de106a`:
  `docs: close persistent catalog worker session`; previous concrete Worker
  session closeout.
- `cd4071cd391ca3c33238679813e1dd39c785ef83`: `handout`; canonical
  Orchestrator handoff that initialized the current coordination phase.
- `cfd4a01524045bce0a05059bafc230c36182ea0e`:
  `feat: add explicit scan candidate import`; Cycle 063.
- `a13134551cfefee330afa14dcbbece3bcb1c46f5`:
  `feat: add persistent title and canonical tags`; Cycle 065.

Public repository evidence includes ADR-0026, ADR-0027, migrations through
`0005`, media import implementation and tests, media metadata implementation and
tests, API composition, and documentation updates. A future Worker or
Orchestrator must verify public state independently.

### Worker-observed runtime evidence

Cycle 065 baseline before implementation:

- `812 tests collected`;
- `809 passed`, `3 skipped`.

Cycle 065 final validation:

- `870 tests collected`;
- full suite: `867 passed`, `3 skipped`;
- warning-as-error suite: `867 passed`, `3 skipped`;
- Poetry lock check passed;
- compileall passed;
- package build passed;
- wheel inspection passed;
- Markdown local links: `681` checked;
- `dist/` removed;
- no private-media, provider, secret, or user-catalog access.

These are Worker-observed command results from the closed concrete session, not
independent future verification.

## 14. Known risks and cautions

- The current browser UI does not expose persistent metadata editing yet.
- Persistent metadata APIs exist but are not integrated into a user-facing
  metadata workspace.
- Search and filtering are absent.
- The current gallery remains a pre-alpha development shell rather than the
  target premium gallery.
- Provider/model availability is time-sensitive.
- Private corpus access remains separately authorized.
- Migration `0005` must never be applied to a real user database without
  explicit future authority.
- No future Worker should treat this handoff as task authorization.

## 15. Strongest next product direction

Non-authoritative recommendation only: the strongest next direction is a bounded
read/search vertical slice built on the new metadata foundation, most likely:

- catalog media-list/read-model API;
- title search;
- canonical-tag filtering;
- multi-tag AND semantics;
- deterministic pagination and order;
- tests and an ADR when needed.

Reasoning: import, title, and tags now persist. The next convergence point is
retrieving and filtering persistent media, which creates the foundation for the
manual metadata workspace and premium gallery. This should likely precede
Tauri, NUC, Cover Studio, or AI draft persistence.

This is not a task. The future ORCHESTRATOR must independently inspect current
code and product strategy before issuing any concrete task.

## 16. Worker lifecycle declaration

Persistent role: `WORKER`

Concrete Worker instance that wrote this handoff: permanently closed after this
closeout commit.

Worker session: `CLOSED`

Active Worker after this commit: none.

Future Worker: must be a fresh instance.

Future task authority: none from this handoff.

Current handoff: context only.

`NEXT_ORCHESTRATOR.md`: not modified by this task.

## 17. Fresh Worker first-response obligations

A future fresh Worker must:

- verify repository root, remote, branch, cleanliness, and public HEAD;
- read the required documents;
- identify the current authoritative ORCHESTRATOR prompt;
- compare prompt scope against repository state;
- stop on missing authority or contradictions;
- never start from the recommendation alone;
- never revive this closed concrete Worker session.
