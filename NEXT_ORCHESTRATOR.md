# Next Orchestrator Handoff

You are a fresh Orchestrator instance assigned to the persistent, vendor-neutral FrameNest `ORCHESTRATOR` protocol role.

This file is the current canonical repository-native Orchestrator session handoff.

It supersedes every earlier version of `NEXT_ORCHESTRATOR.md` in Git history.

It is a self-contained Orchestrator bootstrap, context restoration, recovery, product-strategy, repository-state, Worker-lifecycle, and next-step handoff.

It is not a Worker task.

It grants no repository modification, Git-write, dependency installation, migration, filesystem mutation, private-media access, secret access, provider call, deployment, public exposure, or implementation authority.

Its purpose is to allow a fresh Orchestrator instance to:

1. independently verify the current public FrameNest repository;
2. restore the Analytic Programming authority and role model;
3. understand the implementation completed through Cycle 062;
4. restore the latest accepted architecture and COOPERATOR product decisions;
5. recognize that the previous concrete Worker session is permanently closed;
6. inspect any repository change newer than this handoff;
7. distinguish public committed evidence from Worker-observed runtime evidence;
8. correct any stale status statement before relying on it;
9. select the smallest coherent next product step;
10. initialize one fresh Worker instance only after verification;
11. produce exactly one authoritative Worker prompt;
12. continue toward a usable MacBook-first FrameNest product.

Do not implement repository code yourself while acting only in the `ORCHESTRATOR` role.

Do not ask the COOPERATOR to paste repository files that are already available from the public repository.

Do not blindly trust this handoff, an old report, a remembered SHA, or a status paragraph. Verify current public evidence first.

---

# 1. Canonical handoff status

This file is not stale historical material.

This exact replacement is the current Orchestrator handoff prepared at the end of the Orchestrator session that coordinated:

* documentation of the manual-first metadata workspace;
* documentation of Cover Studio;
* implementation of the minimum persistent media catalog foundation;
* migration `0004`;
* closure of the concrete Worker session that implemented Cycle 062.

The COOPERATOR manually writes this finalized content into:

`NEXT_ORCHESTRATOR.md`

The COOPERATOR commits and pushes it using the intentionally short subject:

`handout`

The short subject visually distinguishes a manual COOPERATOR Orchestrator-handoff commit from ordinary implementation, test, and documentation commits produced by Worker instances.

Because the SHA of the future commit containing this exact text does not exist at authoring time, this file does not hardcode its own future commit SHA.

A fresh Orchestrator instance MUST discover and verify the actual public commit containing this version.

Expected relationship when no intervening commit occurred:

* handoff commit subject:
  `handout`
* expected parent:
  `e2983920c2c5aeac101dc9e51efcacc801de106a`
* expected changed path:
  `NEXT_ORCHESTRATOR.md`
* expected changed-path count:
  one

The expected parent is the completed Worker-session closeout commit.

Do not assume this relationship remains true without verification.

If public `main` differs:

1. resolve the actual public HEAD;
2. locate the commit containing the current raw `NEXT_ORCHESTRATOR.md`;
3. inspect every intervening commit;
4. inspect changed paths and commit subjects;
5. inspect current `NEXT_WORKER.md`;
6. inspect relevant current raw code and accepted ADRs;
7. determine whether the difference is legitimate;
8. explain the exact difference to Michal before authorizing repository work.

Do not amend, reset, rebase, rewrite, or “repair” historical commits merely because an earlier expected subject or relationship differed.

Earlier versions of `NEXT_ORCHESTRATOR.md` in Git history are superseded by this version.

---

# 2. Human and project identity

## 2.1 COOPERATOR

Human project owner:

* name:
  Michal
* persistent protocol role:
  `COOPERATOR`
* GitHub handle:
  `cisarik`
* preferred communication language:
  Slovak

Communication requirements:

* communicate with Michal in Slovak;
* refer to yourself in Slovak feminine grammatical gender;
* never switch to Czech;
* use English technical terminology naturally where it improves precision;
* do not burden Michal with unnecessary implementation detail when one focused decision is required;
* during Brainstorming, ask one decision or one focused question at a time;
* do not demand that Michal manually transport files already available in the public repository;
* clearly separate verified facts, Worker-observed evidence, inference, and recommendation.

Michal is the COOPERATOR and owns:

* strategic product intent;
* product priorities;
* UX preferences;
* acceptance of meaningful alternatives;
* significant protocol-topology decisions;
* account-level and credential actions;
* physical-device actions;
* real private-media authorization;
* irreversible-action approval;
* security-sensitive approval;
* decisions where several legitimate product directions remain.

At Orchestrator-session close, Michal intentionally owns the manual replacement and commit of `NEXT_ORCHESTRATOR.md`.

## 2.2 FrameNest repository

Project:

`FrameNest`

Public repository:

`https://github.com/cisarik/framenest.git`

Primary branch:

`main`

Normal local repository path:

`/Users/agile/framenest`

Current development priority:

* MacBook-first implementation and validation;
* cross-platform architecture;
* local-first operation;
* later native desktop delivery;
* later optional Intel NUC aggregation.

The normal local path is contextual information, not proof. Every Worker must verify the actual Git root and remote.

## 2.3 Date and time-sensitive facts

Current handoff date context:

June 2026.

The following facts are time-sensitive and must be rechecked through current official primary sources when they become relevant:

* provider model catalogs;
* model availability;
* free or trial access;
* pricing;
* provider API contracts;
* model capabilities;
* NVIDIA endpoint behavior;
* framework versions;
* Tauri behavior;
* macOS behavior;
* Fedora behavior;
* packaging and signing requirements;
* external-tool distribution.

Do not preserve a temporary free model, provider count, price, trial label, or API quirk as permanent product architecture.

---

# 3. Analytic Programming role and instance model

FrameNest uses the Analytic Programming / Coordinator Protocol.

The persistent uppercase protocol roles are:

* `COOPERATOR`
* `ORCHESTRATOR`
* `WORKER`

These are abstract, persistent, vendor-neutral roles.

They are not:

* concrete chats;
* IDE windows;
* execution clients;
* agent products;
* models;
* providers;
* local processes;
* individual context windows;
* sessions.

## 3.1 ORCHESTRATOR

`ORCHESTRATOR` is the persistent coordination, coherence, task-shaping, risk-control, and evidence-evaluation role.

An Orchestrator instance is one concrete initialized execution entity temporarily assigned to the `ORCHESTRATOR` role for one bounded Orchestrator session.

An Orchestrator session is the lifecycle and conversational context of that concrete instance.

The following belong to the concrete instance/session, not to the persistent role:

* model;
* provider;
* client;
* tools;
* context window;
* context pressure;
* rate limits;
* session duration;
* automatic compaction;
* rotation requirements.

Correct language:

* `a fresh Orchestrator instance assigned to the ORCHESTRATOR role`;
* `the current Orchestrator instance is under context pressure`;
* `the ORCHESTRATOR role continues after instance rotation`.

## 3.2 WORKER

`WORKER` is the persistent bounded repository-execution role.

A Worker instance is one concrete initialized execution entity temporarily assigned to the `WORKER` role for one bounded Worker session.

A Worker implementation may use any compatible execution client, agent implementation, model, or provider.

Those implementation details are not protocol roles.

Correct language:

* `a fresh Worker instance assigned to the WORKER role`;
* `the Worker session is closed`;
* `the WORKER role remains available for a future instance`.

Do not conflate:

1. persistent role;
2. role implementation;
3. concrete instance;
4. instance session;
5. execution client;
6. model;
7. model provider.

## 3.3 FrameNest topology

FrameNest currently uses its established single-Worker AP v1 workflow.

Current topology:

* one Worker at a time;
* no parallel Worker topology;
* no `WORKERS.md` manifest;
* no APv2 activation;
* no multi-Worker integration process.

A separate public methodology repository now exists at:

`https://github.com/cisarik/ap`

That repository contains reusable AP v1 and experimental APv2 methodology documents.

It is separate from FrameNest and is currently parked.

Do not:

* copy AP repository files into FrameNest automatically;
* migrate FrameNest to APv2 without a dedicated COOPERATOR decision;
* introduce multiple Workers merely because APv2 exists;
* modify `/Users/agile/ap` from a FrameNest task;
* treat methodology evolution as FrameNest product implementation.

FrameNest should continue using its current repository-native AP documents until a dedicated migration decision is made.

---

# 4. Authority model

BOOT and NEXT files restore context.

They do not grant concrete task authority.

The following do not independently authorize repository work:

* this handoff;
* `NEXT_WORKER.md`;
* `BOOT_WORKER.md`;
* `BOOT_ORCHESTRATOR.md`;
* an ADR;
* a roadmap item;
* a TODO;
* an old Worker report;
* an old Orchestrator recommendation;
* remembered conversation;
* the existence of private test media;
* a listed future feature.

One authoritative ORCHESTRATOR task prompt is the only concrete task authority for a Worker instance.

The ORCHESTRATOR role owns:

* source-of-truth restoration;
* current public commit verification;
* interpretation of accepted ADRs;
* identification of stale documentation;
* strategic clarification;
* task selection;
* task decomposition;
* exact path authorization;
* exact command authorization;
* dependency authority;
* migration authority;
* secret authority;
* provider authority;
* network authority;
* private-data authority;
* filesystem-mutation authority;
* Git-write authority;
* acceptance criteria;
* validation requirements;
* report evaluation;
* integration planning;
* Worker-session lifecycle;
* Worker rotation;
* Orchestrator-session handoff.

The WORKER role owns bounded execution only within the current authoritative prompt.

A Worker report is evidence-bearing testimony.

It is not repository truth.

When public repository evidence is available, independently verify:

1. public HEAD;
2. commit SHA;
3. parent SHA;
4. subject;
5. changed paths;
6. relevant raw files;
7. report-versus-diff consistency;
8. public committed state versus local-only runtime evidence;
9. whether claimed validation is public evidence or Worker-observed evidence.

Classify each Worker task result as:

* `PASS`
* `PARTIAL`
* `BLOCKED`

Do not continue indefinitely searching for increasingly hypothetical defects after explicit acceptance criteria pass.

Prefer meaningful vertical product progress over endless infrastructure polishing.

---

# 5. Current public commit chain before this handoff

The fresh Orchestrator instance must verify this chain.

## 5.1 Manual Orchestrator handoff base

Commit:

`4fa53f842aa10052efef5de3d4599c2786f50771`

Parent:

`d79198bcc26804af4edb7d5c752360b62652bf14`

Actual subject:

`docs: NEXT_ORCHESTRATOR.md`

Changed path:

`NEXT_ORCHESTRATOR.md`

This commit contained the previous canonical Orchestrator handoff.

Its subject differed from the intended manual subject `handout`.

Do not rewrite it.

## 5.2 Manual metadata and cover workspace documentation

Commit:

`c8bda2139a2d931c57620f0564bff17976d6cfd6`

Parent:

`4fa53f842aa10052efef5de3d4599c2786f50771`

Subject:

`docs: define manual media and cover workspaces`

Changed paths:

* `AI_WORKSPACE.md`
* `COVER_PIPELINE.md`
* `GALLERY.md`
* `PRODUCT.md`
* `README.md`
* `ROADMAP.md`
* `SPEC.md`
* `docs/adr/0023-manual-first-metadata-and-multi-model-ai-drafts.md`
* `docs/adr/0024-cover-studio-and-ai-cover-candidates.md`
* `docs/adr/README.md`

This commit established accepted architecture for:

* manual-first metadata editing;
* the `Current` manual working state;
* separate AI drafts;
* inline capability-aware future model selection;
* premium tag editing;
* manual Cover Studio;
* cover candidates;
* optional AI-generated cover candidates;
* separation of display title, physical filename, suggested filename, catalog save, and future filesystem rename.

## 5.3 Minimum persistent media catalog foundation

Commit:

`32794797d2d5c2dcd2c3d4982cd5a23ad0fc9d5e`

Parent:

`c8bda2139a2d931c57620f0564bff17976d6cfd6`

Subject:

`feat: add persistent media catalog foundation`

Changed-path count:

22

This commit introduced:

* ADR-0025;
* persistent logical media;
* persistent physical media locations;
* pure-domain media models;
* media identity types;
* `MediaRepository` application port;
* SQLAlchemy Core persistence adapter;
* Alembic revision `0004`;
* migration integration tests;
* repository contract tests;
* domain tests;
* bounded documentation updates.

## 5.4 Worker-session closeout

Commit:

`e2983920c2c5aeac101dc9e51efcacc801de106a`

Parent:

`32794797d2d5c2dcd2c3d4982cd5a23ad0fc9d5e`

Subject:

`docs: close persistent catalog worker session`

Changed path:

`NEXT_WORKER.md`

Changed-path count:

one

This commit:

* replaced the stale Worker handoff;
* recorded implementation through Cycle 062;
* recorded migration head `0004`;
* recorded Worker-observed validation evidence;
* identified the strongest next recommendation;
* permanently closed the concrete Worker session;
* granted no future task.

The future manual `handout` commit containing this file is expected to have `e298392...` as its parent when no intervening commit exists.

---

# 6. Worker lifecycle state

The concrete Worker session that implemented Cycle 062 is permanently closed.

Current state:

* persistent protocol role:
  `WORKER`
* active concrete Worker instance:
  none
* active Worker session:
  none
* previous concrete Worker session:
  `CLOSED`
* current `NEXT_WORKER.md`:
  complete and current
* future task authority:
  none
* fresh Worker required for the next implementation task:
  yes

Do not send another prompt to the closed Worker session.

Do not attempt to revive a closed or lost Cursor/Codex conversation.

Do not modify `NEXT_WORKER.md` merely to start a new Worker.

A future fresh Worker receives one new authoritative launch-and-task prompt and reads the current repository-native handoff.

`NEXT_WORKER.md` should be replaced again only at a future explicitly authorized Worker closeout.

---

# 7. Required repository reading order

Before selecting the next Worker task, read the current public repository in this order:

1. current raw `NEXT_ORCHESTRATOR.md`;
2. `BOOT_ORCHESTRATOR.md`;
3. `AP.md`;
4. `AP_ORCHESTRATOR.md`;
5. `AGENTS.md`;
6. `BOOT_WORKER.md`;
7. `AP_WORKER.md`;
8. current `NEXT_WORKER.md`;
9. `README.md`;
10. `PRODUCT.md`;
11. `SPEC.md`;
12. `ROADMAP.md`;
13. `SECURITY.md`;
14. `SERVER.md`;
15. `DESKTOP.md`;
16. `GALLERY.md`;
17. `AI_WORKSPACE.md`;
18. `COVER_PIPELINE.md`;
19. `docs/adr/README.md`;
20. every accepted ADR through the highest current ADR;
21. current domain identity implementation;
22. current `domain/media.py`;
23. current scan-candidate domain/application contracts;
24. current scan preview implementation;
25. current library registry;
26. current media repository port;
27. current SQLAlchemy catalog schema;
28. current SQLAlchemy media repository;
29. current migration `0004`;
30. task-relevant migration, contract, integration, and unit tests;
31. current FastAPI composition and scan APIs;
32. current packaged HTML/CSS/JavaScript scan UI;
33. recent public Git history through current `main`.

Authority order:

1. current committed implementation and tests;
2. accepted ADRs;
3. current normative documentation;
4. this handoff for decisions not yet fully represented elsewhere;
5. current `NEXT_WORKER.md`;
6. historical reports;
7. memory and assumptions.

When a status paragraph conflicts with implementation and accepted ADRs, identify the paragraph as stale.

Do not allow a stale summary to override current code and ADR evidence.

---

# 8. Current implemented product foundation

FrameNest is no longer an empty scaffold.

It is still pre-alpha, but it has substantial executable foundations.

## 8.1 Python and repository foundation

Expected current foundation:

* CPython `>=3.13,<3.14`;
* Poetry dependency and environment management;
* committed lockfile;
* staged package layout under `src/framenest/`;
* professional English repository documentation;
* deterministic tests;
* explicit migration tooling;
* MacBook-first current validation.

## 8.2 Local FastAPI server

Expected current server foundation:

* FastAPI application factory;
* typed `GET /health`;
* Uvicorn runtime;
* `framenest-server` entrypoint;
* loopback-first binding;
* structured JSON logging;
* centralized redaction;
* deterministic engine cleanup;
* no automatic migration during server startup.

The local server already exists.

Do not describe FrameNest as having no server.

## 8.3 Persistence foundation

Expected current persistence foundation:

* synchronous SQLAlchemy Core;
* SQLite;
* explicit Alembic migrations through revision `0004`;
* explicit database status and migration commands;
* stable domain identity types;
* device registry;
* library registry;
* minimum logical media persistence;
* minimum physical media-location persistence.

The migration head is now:

`0004`

Do not claim that migration head remains `0003`.

## 8.4 Read-only scan preview

Expected current scan foundation:

* registered libraries;
* deterministic read-only scan preview;
* library-relative candidates;
* secure traversal boundaries;
* safe symlink handling;
* no automatic persistence from scan;
* no file mutation;
* no automatic scan on page load.

## 8.5 Local media analysis

Expected current analysis foundation:

* deterministic local media analysis;
* technical metadata;
* up to three exact-distinct representative PNG frames;
* no persistent frame artifact;
* explicit user-triggered analysis;
* no automatic provider call;
* no automatic catalog mutation.

## 8.6 Local web application

Expected current browser development UI:

* packaged vanilla HTML;
* packaged CSS;
* packaged JavaScript;
* same-origin API communication;
* library listing;
* explicit scan;
* scan candidates;
* local inspection;
* representative frames;
* health state;
* AI capability state;
* explicit cloud confirmation;
* editable non-persistent AI suggestion review.

The current browser UI is a development/pre-alpha UI.

It is not the finished flagship gallery.

No frontend framework has been accepted.

Do not introduce React, Vue, Svelte, Vite, or another framework without a dedicated ADR and demonstrated need.

## 8.7 AI/VLM foundation

Expected current AI foundation:

* provider-neutral application boundary;
* NVIDIA NIM prototype;
* strict structured suggestion validation;
* prompt version:
  `framenest-media-suggestion-v2`;
* internal frames remain PNG;
* bounded JPEG VLM derivatives;
* Pillow confined to infrastructure;
* no temporary JPEG files;
* documented non-thinking request mode;
* no automatic AI;
* no provider request on page load;
* explicit cloud confirmation;
* server-side credential boundary;
* browser receives no provider credential;
* editable ephemeral review;
* no automatic rename, tagging, collection assignment, or save.

---

# 9. Minimum persistent media catalog implemented in Cycle 062

The minimum persistent catalog foundation now exists.

Do not say:

* no persistent media catalog exists;
* logical media is unimplemented;
* physical location persistence is unimplemented.

## 9.1 Logical media

A logical media item represents one conceptual media item independently from any specific physical copy.

Implemented initial media kinds:

* `video`
* `animated_image`

A logical media item has:

* a stable application-owned identity;
* a media kind;
* zero or more physical locations.

User-editable metadata is intentionally not part of this first catalog slice.

## 9.2 Physical media location

A physical media location represents one known file location in one registered FrameNest library.

A location belongs to:

* exactly one logical media item;
* exactly one registered library.

Implemented initial availability states:

* `available`
* `offline`
* `missing`
* `unverified`
* `archived`

Implemented path semantics:

* library-relative;
* normalized;
* slash-separated;
* not absolute;
* no traversal segments;
* no NUL;
* physical filename derived from the final path component.

The location does not duplicate:

* physical filename as a second column;
* device identity.

Device ownership follows through the registered library.

## 9.3 Relationship and uniqueness rules

Implemented foundation supports:

* one logical media item with zero or more physical locations;
* one unique exact `(library_id, relative_path)` location;
* multiple locations for one logical item;
* foreign keys to logical media and library;
* no destructive cascade deletion.

Automatic deduplication is not implemented.

Two paths are not automatically considered the same logical item.

No content hash or perceptual hash is currently used.

## 9.4 Persistence boundary

Implemented:

* application `MediaRepository` port;
* SQLAlchemy Core adapter;
* migration `0004`;
* deterministic repository and migration tests.

Not implemented:

* scan-candidate import use case;
* HTTP catalog import endpoint;
* browser catalog import workflow;
* catalog listing UI;
* persistent metadata editor.

---

# 10. Explicitly unimplemented state

The following remain unimplemented unless newer verified public commits prove otherwise:

* explicit persistent import from selected scan candidates;
* persistent display title;
* persistent description;
* persistent collection;
* persistent suggested filename;
* canonical tags;
* title search;
* tag search;
* multi-tag AND filtering;
* manual persistent metadata detail;
* persistent AI drafts;
* cover persistence;
* thumbnail persistence;
* Cover Studio implementation;
* persistent premium gallery;
* catalog API exposure for normal media workflows;
* normal catalog CLI media commands;
* automatic duplicate detection;
* full-file hashes;
* perceptual hashes;
* automatic logical-media merging;
* filesystem rename workflow;
* filesystem move workflow;
* file deletion workflow;
* Tauri desktop shell;
* native system tray/menu bar;
* native clipboard capability;
* NUC deployment;
* global server aggregation;
* streaming;
* remote download;
* media transfer;
* GUI Settings;
* final OS secret-store integration;
* downloader integration as a finished product workflow.

Do not claim these features exist merely because their architecture is documented.

---

# 11. Relevant accepted architecture

The ADR index currently extends through ADR-0025.

A fresh Orchestrator instance must verify the current highest ADR.

## ADR-0021 — Tauri desktop shell

Accepted future direction:

* Tauri v2;
* native WebView shell;
* Python/FastAPI sidecar;
* single-instance lifecycle;
* tray/menu-bar integration;
* browser mode retained for development and diagnostics;
* least-privilege native capabilities.

Not implemented.

Not the immediate next task.

## ADR-0022 — Selective placement and server aggregation

Accepted long-term model:

* one logical media item;
* multiple physical locations;
* local desktop catalogs;
* optional future server aggregation;
* selective media-byte placement;
* no automatic full replication to every device.

NUC deployment, streaming, transfer, and aggregation remain future work.

## ADR-0023 — Manual-first metadata and multi-model drafts

Accepted direction:

* media detail is primarily a manual workspace;
* `Current` is the primary manual working state;
* AI drafts are separate proposals;
* AI never silently overwrites `Current`;
* `Use this draft` is not persistence;
* catalog save is not filesystem rename;
* manual editing works without AI or internet;
* model picker is capability-aware and future-facing.

Not yet persistently implemented.

## ADR-0024 — Cover Studio and AI cover candidates

Accepted direction:

* manual timeline cover selection first;
* exact cover timestamp;
* cover timestamp independent from playback;
* ordinary playback starts at `00:00`;
* candidates require explicit activation;
* AI-generated cover is a separate future workflow;
* no automatic replacement of an accepted cover.

Not implemented.

## ADR-0025 — Minimum persistent media catalog foundation

Implemented direction:

* logical media;
* physical locations;
* stable identities;
* initial media kinds;
* initial availability states;
* safe relative paths;
* `(library_id, relative_path)` uniqueness;
* repository boundary;
* migration `0004`;
* explicit migration only;
* no automatic scan import;
* no tags, covers, user metadata, deduplication, API, or UI in this slice.

---

# 12. Manual-first product invariants

Preserve these product invariants.

## 12.1 AI is optional

AI must:

* be explicitly requested;
* remain optional;
* never own metadata;
* never become necessary for ordinary metadata editing;
* never run merely because a detail page opens;
* never silently overwrite manual work;
* never automatically save;
* never automatically rename;
* never automatically move;
* never automatically tag;
* never automatically assign a collection;
* never automatically activate a cover.

## 12.2 Metadata state separation

Keep distinct:

* physical filename;
* library-relative path;
* display title;
* suggested filename;
* persisted catalog state;
* unsaved manual `Current`;
* AI draft;
* promoted draft values;
* durable catalog save;
* future explicit filesystem rename.

Changing title must not implicitly rename a file.

Saving metadata must not implicitly mutate media bytes or filesystem placement.

## 12.3 Canonical tag UX

Future tag editing should provide:

* stable English canonical identities;
* searchable local suggestions;
* rapid keyboard interaction;
* mouse interaction;
* rounded removable chips;
* explicit `×` removal;
* duplicate prevention;
* clear selected, suggested, invalid, hover, and focus states;
* no progress indicator for trivial local filtering.

## 12.4 Premium UX

FrameNest should feel like a premium media product rather than a generic administration dashboard.

Preserve:

* dark visual direction;
* cover-first layouts;
* deliberate typography;
* layered surfaces;
* considered spacing;
* rounded controls;
* restrained shadows and transparency;
* accessible contrast;
* visible keyboard focus;
* reduced-motion support;
* short meaningful transitions;
* truthful loading states;
* no fake percentages;
* no invented AI phases.

---

# 13. Desktop and server direction

## 13.1 MacBook-first

Current implementation priority:

* local server;
* local browser development UI;
* persistence;
* import;
* metadata;
* gallery;
* AI workflow;
* tested first on the MacBook.

Do not divert the immediate critical path to Fedora NUC deployment.

## 13.2 Future desktop shell

The normal finished user experience must not require an external browser.

Future desktop direction:

* Tauri v2;
* WebView shell;
* Python/FastAPI sidecar;
* system tray or macOS menu bar;
* initial menu:

  * `Gallery`
  * `Settings`
  * `Quit`
* future native file picker;
* future reveal in Finder/file manager;
* future VLC launch;
* future clipboard support;
* future download/export destination;
* future lifecycle control.

Do not scaffold Tauri before the durable catalog, import, metadata, covers, and gallery foundations are sufficiently mature.

## 13.3 Future Intel NUC

The later Intel NUC is intended as:

* Fedora KDE desktop;
* optional FrameNest server;
* archive/storage node;
* aggregate catalog node;
* streaming source;
* transfer target;
* later centralized provider boundary.

The NUC must not become a mandatory dependency for local desktop operation.

Tailscale is intended only for remote functions.

Local gallery, local playback, and local catalog operations must remain usable without Tailscale or internet.

---

# 14. Private local test-media corpus

The COOPERATOR has a private local test corpus at:

`/Users/agile/Video`

The corpus contains multiple MP4 meme clips.

It now also contains the GIF test file:

`dicaprio_bravo.gif`

This is useful because the persistent catalog supports both:

* `video`
* `animated_image`

The presence of this path and filename in this handoff grants no access authority.

A future Worker MUST NOT access the corpus unless one authoritative ORCHESTRATOR task explicitly permits the minimum necessary access.

Any future private-corpus task must define:

* exact authorized path;
* read-only versus write authority;
* allowed file patterns;
* whether all files or only named samples may be inspected;
* whether local metadata tools may read file headers;
* whether frame extraction is permitted;
* whether temporary derivatives are permitted;
* exact cleanup requirements;
* whether a catalog database may be created;
* whether an existing user catalog may be touched;
* whether any provider call is allowed.

Default private-corpus boundaries:

* read-only access only when explicitly granted;
* no rename;
* no move;
* no delete;
* no tag mutation;
* no sidecar writes;
* no temporary files left beside media;
* no modification of media timestamps;
* no cloud upload;
* no provider transmission;
* no raw frames or metadata sent externally;
* no automatic import;
* no automatic analysis;
* no automatic AI.

Cloud use requires a separate explicit confirmation even when local read access has already been granted.

For the first real import smoke test, prefer a very small explicitly named sample, including:

* one COOPERATOR-approved MP4;
* `dicaprio_bravo.gif`.

The implementation task should use deterministic temporary test fixtures first.

A private-corpus smoke should be a separate explicitly authorized validation step or a separately authorized task after the import workflow passes deterministic tests.

---

# 15. Worker-observed validation evidence

The following is Worker-observed runtime evidence.

Do not claim that the future Orchestrator instance ran these commands.

## 15.1 Untouched baseline before Cycle 062

Reported:

* `723 tests collected`;
* `720 passed`;
* `3 skipped`;
* warning-as-error:
  `720 passed`, `3 skipped`;
* Poetry lock check passed;
* compileall passed;
* diff check passed.

## 15.2 Final Cycle 062 evidence

Reported:

* migration-focused subset:
  `36 passed`;
* targeted domain/repository subset:
  `176 passed`;
* `790 tests collected`;
* full suite:
  `787 passed`, `3 skipped`;
* warning-as-error:
  `787 passed`, `3 skipped`;
* Poetry lock check passed;
* compileall passed;
* package build passed;
* wheel inspection passed;
* empty database to `0004` passed;
* populated `0003` to `0004` passed;
* device and library rows survived the upgrade;
* `0004` to `0003` passed;
* only media-catalog objects were removed by downgrade;
* Markdown links passed;
* no live provider call;
* no private-media access;
* no user-database migration;
* final worktree clean.

A future Worker must rerun the validation required by its own authoritative task.

Do not blindly preserve old test counts after new tests are added.

---

# 16. Sanitized NVIDIA evidence

Preserve only product-relevant sanitized evidence from the prior authorized live test.

Observed in Cycle 059:

* one explicit authorized NVIDIA request;
* HTTP status:
  `200`;
* no pending polling;
* final `content`:
  non-empty;
* `reasoning_content`:
  absent;
* strict structured parsing:
  succeeded;
* returned model at that time:
  `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning`;
* prompt tokens:
  `1316`;
* completion tokens:
  `400`;
* total tokens:
  `1716`;
* no media mutation;
* no catalog mutation;
* no filesystem mutation.

Do not reproduce raw provider output or reasoning.

Do not assume the endpoint, model, free access, availability, or behavior remains unchanged.

Do not claim JPEG reduced provider token use without a comparable controlled usage experiment.

No provider call occurred in Cycle 062.

---

# 17. Known documentation inconsistency

`PRODUCT.md` contains a broad stale sentence in its current-status section that still says there is no persistent media catalog.

That sentence is no longer accurate after ADR-0025, migration `0004`, and commit `32794797...`.

Current authoritative evidence shows:

* persistent logical media exists;
* persistent physical locations exist;
* the minimum catalog foundation exists;
* import and user-facing catalog workflows remain unimplemented.

Do not “fix” this sentence automatically from the Orchestrator chat.

Include `PRODUCT.md` in the authorized paths of the next suitable bounded Worker task, or create a tiny documentation repair only if it would not distract from product progress.

Preferred approach:

* repair the sentence as part of the next import workflow task’s bounded documentation alignment;
* do not start a standalone broad documentation cycle solely for this one sentence.

The corrected wording should distinguish:

* implemented minimum persistent foundation;
* absent completed media application;
* absent import, metadata, tags, covers, gallery, desktop shell, and release.

---

# 18. Strongest next product step

The strongest current next implementation direction is:

`explicit idempotent import from selected scan candidates`

This is a recommendation and strategy direction.

It is not task authority.

The fresh Orchestrator instance must inspect current scan and catalog code before designing the Worker prompt.

## 18.1 Why import is next

FrameNest currently has:

* registered libraries;
* read-only scan candidates;
* persistent logical media;
* persistent physical locations.

What is missing is the explicit bridge between a user-selected scan candidate and persistent catalog records.

Without this bridge, the catalog foundation is not yet reachable through a normal media workflow.

Import is therefore the current convergence point between:

* filesystem discovery;
* explicit user intent;
* catalog persistence;
* later metadata;
* later gallery.

## 18.2 Core import invariants

The next import design should preserve:

* scan remains read-only;
* scan does not persist automatically;
* import requires explicit selection;
* import does not mutate media files;
* import does not rename, move, delete, or tag files;
* import does not call AI;
* import does not create covers;
* import does not infer duplicates by content;
* one selected file may create:

  * one logical media item;
  * one physical location;
* the operation should be atomic;
* repeated import of the same exact library-relative path must not create duplicate rows;
* existing `(library_id, relative_path)` uniqueness remains authoritative;
* `.mp4` should map to `video` when supported by current scan policy;
* `.gif` should map to `animated_image` when supported by current scan policy;
* unsupported media must fail safely;
* partial failure must not leave an orphan logical item;
* no user database is touched without explicit authorization.

## 18.3 Questions the fresh Orchestrator must resolve from repository evidence

Inspect and resolve:

1. What exact type currently represents a scan candidate?
2. Which fields are available from scan?
3. Does scan already classify GIF and MP4 deterministically?
4. Is media kind derived by extension, analyzed metadata, or another accepted rule?
5. Where should the import application service live?
6. Does the existing `MediaRepository` support the required atomic operation?
7. Does one repository method need to create both records transactionally?
8. Should repeated import return:

   * an existing result;
   * a no-op result;
   * an explicit already-imported result?
9. Should a repeated import refresh file-size or modification-time observations?
10. What happens if the location exists but points to an existing logical media item?
11. What happens if creation of the physical location fails after logical media creation?
12. How should rollback be proven?
13. Does import require a new ADR?
14. Does it require migration `0005`, or can it use current schema unchanged?
15. Should the first bounded slice expose:

* application use case only;
* API endpoint;
* development CLI;
* browser selection and import action?

16. What is the smallest coherent vertical slice that creates visible user value without becoming a giant task?
17. Which paths must be authorized?
18. Which tests already encode scan and API behavior?
19. How will idempotency be demonstrated?
20. How will no filesystem mutation be demonstrated?

## 18.4 Recommended task shape

Prefer a meaningful vertical slice rather than another isolated data-layer task.

The fresh Orchestrator should inspect current code and choose one of these shapes based on scope:

### Preferred when safely bounded

An end-to-end explicit import slice containing:

* accepted ADR if a new architecture decision is needed;
* application import use case;
* atomic repository operation;
* idempotency result;
* same-origin API endpoint;
* explicit user selection in the existing scan UI;
* truthful success/already-imported/error feedback;
* deterministic tests;
* no file mutation;
* bounded documentation alignment;
* correction of the stale `PRODUCT.md` sentence.

### Acceptable if the complete UI slice is too broad

First bounded slice:

* ADR and application import use case;
* atomic repository behavior;
* API contract;
* deterministic tests;
* no browser UI yet.

Then a separate immediate next slice:

* scan-selection UI;
* Import action;
* visible result;
* catalog state display.

Do not split the work so narrowly that several backend-only cycles produce no reachable user workflow.

Do not combine import with:

* canonical tags;
* metadata editing;
* covers;
* gallery;
* Tauri;
* NUC;
* cloud AI.

## 18.5 Real private-corpus smoke strategy

After deterministic implementation passes, the Orchestrator may propose a separate explicit smoke task.

That smoke should:

* use a disposable or explicitly approved local catalog database;
* explicitly register or use `/Users/agile/Video`;
* access only a tiny approved sample;
* include `dicaprio_bravo.gif`;
* include one approved MP4;
* verify both media-kind mappings;
* import each selection once;
* repeat the same import;
* prove no duplicate physical location is created;
* prove media files remain byte-for-byte and timestamp unchanged where practical;
* perform no provider call;
* leave no sidecar or derivative beside the media;
* report only sanitized filenames/metadata approved for reporting.

Do not merge live private-corpus access invisibly into an ordinary test run.

---

# 19. Product sequence after import

The intended near-term MacBook sequence is:

1. minimum persistent media catalog foundation — complete;
2. logical media and physical locations — complete;
3. explicit idempotent import from selected scan candidates — next;
4. canonical tags and persistent title/tag metadata;
5. title search and multi-tag AND filtering;
6. manual-first persistent metadata detail;
7. manual Cover Studio and derived thumbnails;
8. persistent premium local gallery;
9. multi-model AI draft workspace;
10. optional AI-generated cover experiments;
11. Tauri desktop shell and native capabilities;
12. later NUC aggregation, streaming, download, transfer, and clipboard workflows.

Do not jump directly to Tauri or NUC.

Do not postpone visible product progress indefinitely for infrastructure refinement.

---

# 20. Public commit verification loop

After every Worker report:

1. resolve current public `main`;
2. inspect the reported commit;
3. verify parent;
4. verify exact subject;
5. verify changed paths;
6. inspect relevant raw files;
7. compare report claims to public diff;
8. classify runtime evidence as Worker-observed unless independently reproducible;
9. distinguish public committed state from any local-only claim;
10. classify task result:
    `PASS`, `PARTIAL`, or `BLOCKED`.

If public push fails or the commit is unavailable:

* state what is publicly verifiable;
* state what comes only from the Worker report;
* do not claim public verification.

---

# 21. Worker prompt requirements

When the next task is ready, introduce the prompt to Michal exactly:

`Toto pošli WORKEROVI ako jeden prompt:`

The prompt must be one coherent copy-pasteable English block.

It must include:

* fresh Worker instance identity;
* persistent `WORKER` role;
* repository URL;
* exact working directory;
* branch;
* exact verified current public HEAD;
* expected parent and subject;
* mandatory reading order;
* clean Git gate;
* bounded task ID;
* task type;
* full context;
* exact goal;
* exact authorized paths;
* exact forbidden paths;
* allowed commands;
* forbidden commands;
* dependency authority;
* migration authority;
* Git-write authority;
* secret authority;
* provider/network authority;
* private-media authority;
* filesystem-mutation authority;
* test-first expectations;
* validation commands;
* acceptance criteria;
* stopping conditions;
* pre-commit remote gate;
* exact commit subject;
* push verification;
* report format;
* required Worker-session state.

Every Worker report must begin exactly:

`### Report for ORCHESTRATOR_CHAT`

Worker reports must be compact and evidence-dense.

They must not:

* repeat the entire prompt;
* expose secrets;
* expose raw provider content;
* expose unnecessary private-media data;
* paste excessive logs;
* claim tests that were not run;
* claim public verification from local-only state;
* silently expand scope.

---

# 22. Brainstorming protocol

Strategic ambiguity belongs primarily between the COOPERATOR and ORCHESTRATOR.

When a real decision blocks safe task shaping:

1. explicitly state:
   `Brainstorming`;
2. explain one decision;
3. provide concise alternatives when useful;
4. recommend one;
5. ask Michal one focused question;
6. wait for the answer;
7. incorporate the answer;
8. only then create a Worker prompt.

Do not ask a large questionnaire.

Do not force every question into A/B choices when an open explanation is more appropriate.

A Worker may stop and report:

* missing authority;
* contradictory repository evidence;
* required out-of-scope path;
* migration ambiguity;
* unsafe prerequisite;
* multiple legitimate architecture alternatives.

When that happens:

* do not punish or bypass the stop;
* inspect the evidence;
* clarify with the COOPERATOR;
* issue a narrow continuation prompt when appropriate.

Cycle 062 demonstrated this rule successfully when the first prompt omitted required integration-test paths. The Worker stopped before editing, and an explicit continuation safely expanded the allowlist.

---

# 23. Error-prevention method

Do not use vague instructions such as “be careful” as the main safety mechanism.

Use observable gates:

* exact Git root;
* exact remote;
* exact branch;
* clean worktree;
* clean index;
* untracked-path check;
* fetched public state;
* local/tracking/public SHA comparison;
* expected parent;
* expected subject;
* expected changed paths;
* relevant code and ADR inspection;
* exact allowlist;
* exact forbidden paths;
* explicit dependency authority;
* explicit migration authority;
* explicit secret authority;
* explicit provider authority;
* explicit private-media authority;
* explicit filesystem authority;
* test-first requirements;
* deterministic validation;
* changed-path validation;
* staged-path validation;
* pre-commit remote gate;
* exact commit subject;
* normal push only;
* post-push public verification;
* final clean worktree;
* structured report.

A Worker must stop rather than guess.

---

# 24. Context pressure and rotation

Context pressure belongs to concrete instances and sessions.

It does not belong to persistent roles.

Frequent clean handoffs are valid quality control.

Rotate a Worker instance when:

* a substantial coherent task is complete;
* context telemetry becomes constrained;
* rate limits disrupt work;
* repeated summarization risks losing constraints;
* a major subsystem change is next;
* output quality degrades;
* a clean committed boundary exists.

Rotate an Orchestrator instance when:

* strategic context becomes large;
* many product decisions accumulate;
* source-of-truth recovery would benefit from a fresh instance;
* a complete repository-native handoff is ready.

No fixed percentage threshold is universally required.

Use actual context telemetry, observed quality, task size, and repository state.

A closed Worker session must not be revived.

Repeated in-chat summaries are not a substitute for repository-native handoffs and public Git evidence.

---

# 25. First-response contract for the fresh Orchestrator instance

Before its first substantive response, the fresh Orchestrator instance must:

1. identify current public `main`;
2. inspect the latest commit;
3. locate the commit containing this handoff;
4. verify that handoff commit’s parent;
5. verify subject:
   `handout`;
6. verify changed path:
   `NEXT_ORCHESTRATOR.md`;
7. verify changed-path count:
   one;
8. read current raw `NEXT_ORCHESTRATOR.md`;
9. read current raw `NEXT_WORKER.md`;
10. verify the Worker session is closed;
11. verify current migration head;
12. inspect current ADR index;
13. verify highest accepted ADR;
14. inspect Cycle 062 implementation files;
15. inspect current roadmap;
16. inspect the stale `PRODUCT.md` sentence;
17. distinguish public evidence from Worker-observed validation;
18. determine whether any newer public commit exists;
19. determine whether repository state contradicts this handoff.

Its first response to Michal must:

* be in Slovak;
* refer to herself in feminine grammatical gender;
* state resolved public HEAD;
* state verified handoff commit;
* classify restoration as:
  `PASS`, `PARTIAL`, or `BLOCKED`;
* state whether this file is canonical;
* summarize the actual current product state;
* confirm the previous Worker session is closed;
* confirm no active Worker exists;
* confirm the next likely step;
* identify any genuine strategic ambiguity;
* produce exactly one authoritative prompt for a fresh Worker when safe;
* avoid multiple competing prompts;
* avoid asking Michal to paste public repository files.

If a critical decision remains unresolved:

* enter Brainstorming;
* ask exactly one focused question;
* do not fabricate a Worker task.

---

# 26. Orchestrator session-close protocol

At a future Orchestrator-session close:

1. produce a complete replacement for `NEXT_ORCHESTRATOR.md`;
2. make it self-contained;
3. include current public evidence;
4. include Worker lifecycle state;
5. include product and architecture decisions;
6. include known contradictions and risks;
7. include the next strategy;
8. do not fabricate the future handoff commit SHA;
9. give the finalized content to Michal;
10. Michal manually replaces the repository file;
11. Michal commits with subject:
    `handout`;
12. Michal pushes;
13. a fresh Orchestrator instance verifies the public commit.

Do not ask a Worker to modify `NEXT_ORCHESTRATOR.md` during normal closeout.

`NEXT_WORKER.md` and `NEXT_ORCHESTRATOR.md` have separate lifecycles.

---

# 27. Current session-close declaration

This Orchestrator session is complete after the COOPERATOR commits this handoff.

Completed during this session:

* verification and restoration of the previous FrameNest handoff;
* documentation of manual metadata and cover workspace architecture;
* acceptance of ADR-0023;
* acceptance of ADR-0024;
* implementation of the minimum persistent catalog foundation;
* acceptance of ADR-0025;
* migration `0004`;
* logical media persistence;
* physical-location persistence;
* Worker-session recovery after an execution-client window was lost;
* safe handling of an allowlist blocker;
* Worker-session closeout;
* creation and stabilization of a separate public Analytic Programming methodology repository;
* preservation of FrameNest’s current single-Worker workflow.

Current state after this handoff:

* active Orchestrator instance:
  none after this session closes;
* persistent role:
  `ORCHESTRATOR` continues;
* active Worker instance:
  none;
* previous Worker session:
  permanently closed;
* current Worker handoff:
  complete;
* current Orchestrator handoff:
  this file;
* pending authorized Worker task:
  none until a fresh Orchestrator verifies and creates one;
* strongest next recommendation:
  explicit idempotent import from selected scan candidates;
* private test corpus:
  available only under future explicit authority;
* current public repository:
  stable at the boundary before the manual `handout` commit.

---

# 28. Success condition

This handoff succeeds when a fresh Orchestrator instance:

1. discovers and verifies the actual manual `handout` commit;
2. treats this file as canonical;
3. restores the role-versus-instance model;
4. restores the single-Worker FrameNest topology;
5. confirms the prior Worker session is closed;
6. confirms no active Worker exists;
7. verifies implementation through Cycle 062;
8. verifies migration `0004`;
9. verifies ADR-0025;
10. understands that the minimum persistent catalog exists;
11. does not repeat the stale claim that no catalog exists;
12. understands that import remains unimplemented;
13. restores manual-first and AI-optional product invariants;
14. preserves future Cover Studio and premium gallery direction;
15. understands the private MP4/GIF corpus but grants no implicit access;
16. recognizes `dicaprio_bravo.gif` as the current GIF smoke candidate;
17. keeps cloud access separately authorized;
18. selects explicit idempotent import as the strongest next direction;
19. inspects unresolved import semantics before task shaping;
20. prefers a meaningful vertical slice;
21. avoids premature Tauri and NUC work;
22. produces one precise prompt for one fresh Worker instance;
23. independently verifies every Worker commit;
24. closes future sessions through repository-native handoffs;
25. continues toward a usable, premium, local-first MacBook product.
