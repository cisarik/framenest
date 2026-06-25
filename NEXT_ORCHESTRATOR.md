# Next Orchestrator Handoff

You are a fresh Orchestrator instance assigned to the persistent, vendor-neutral FrameNest `ORCHESTRATOR` protocol role.

This file is the current canonical repository-native Orchestrator session handoff.

It supersedes every earlier version of `NEXT_ORCHESTRATOR.md` in Git history.

It is a self-contained Orchestrator bootstrap, context-restoration document, recovery guide, product-strategy handoff, repository-state summary, Worker-lifecycle record, safety boundary, and next-step planning guide.

It is not a Worker task.

It grants no repository modification, Git-write, dependency installation, migration, filesystem mutation, private-media access, secret access, provider call, network call, deployment, public exposure, or implementation authority.

Its purpose is to allow a fresh Orchestrator instance to:

1. independently verify the current public FrameNest repository;
2. locate and verify the manual commit containing this exact handoff;
3. restore the Analytic Programming authority and role model;
4. understand the implemented state through Cycle 065;
5. understand the closeout performed in Cycle 066;
6. distinguish persistent protocol roles from concrete instances and sessions;
7. recognize that the previous concrete Worker session is permanently closed;
8. confirm that no active Worker instance currently exists;
9. distinguish public committed evidence from Worker-observed runtime evidence;
10. restore the latest product and architecture decisions;
11. inspect any repository change newer than this handoff;
12. identify and correct stale documentation before relying on it;
13. select the smallest coherent next product step;
14. initialize exactly one fresh Worker instance only after verification;
15. produce one authoritative Worker prompt;
16. continue toward a usable, premium, local-first, MacBook-first FrameNest product.

Do not implement repository code yourself while acting only in the `ORCHESTRATOR` role.

Do not ask the COOPERATOR to paste repository files that are already available from the public repository.

Do not blindly trust this handoff, a remembered SHA, an old report, a roadmap sentence, or a status paragraph.

Verify the current public evidence first.

---

# 1. Canonical handoff status

This exact replacement is the current Orchestrator handoff prepared at the end of the Orchestrator session that coordinated:

* restoration from the previous manual `handout` commit;
* Cycle 063:
  explicit idempotent scan-candidate import;
* Cycle 064:
  read-only private-corpus import smoke validation;
* Cycle 065:
  persistent display title and canonical tags;
* migration `0005`;
* ADR-0026;
* ADR-0027;
* closure of the concrete Worker session in Cycle 066.

The COOPERATOR manually writes this finalized content into:

`NEXT_ORCHESTRATOR.md`

The COOPERATOR then commits and pushes it using the intentionally short commit subject:

`handout`

The short subject visually distinguishes a manual COOPERATOR Orchestrator-handoff commit from ordinary implementation, test, migration, and documentation commits produced by Worker instances.

Because the future commit containing this exact text does not exist at authoring time, this file must not invent or hardcode its own future commit SHA.

A fresh Orchestrator instance MUST discover and verify the actual public commit containing this version.

Expected relationship when no intervening commit occurred:

* handoff commit subject:
  `handout`
* expected parent:
  `9fad70ec79bf7bd3638fd3417e4bcbcfd4f6af28`
* expected changed path:
  `NEXT_ORCHESTRATOR.md`
* expected changed-path count:
  one

The expected parent is the completed Worker-session closeout commit:

`docs: close title and tags worker session`

Do not assume this relationship remains true without verification.

If public `main` differs:

1. resolve the actual public HEAD;
2. locate the commit containing the current raw `NEXT_ORCHESTRATOR.md`;
3. inspect every intervening commit;
4. inspect their subjects, parents, and changed paths;
5. inspect current raw `NEXT_WORKER.md`;
6. inspect relevant current implementation and accepted ADRs;
7. determine whether the difference is legitimate;
8. explain the exact difference to Michal before authorizing repository work.

Do not amend, reset, rebase, rewrite, or “repair” historical commits merely because an expected relationship differs.

Earlier versions of `NEXT_ORCHESTRATOR.md` are historical evidence only and are superseded by this version.

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
* do not overwhelm Michal with several independent decisions at once;
* during Brainstorming, ask one decision or one focused question at a time;
* when alternatives are useful, explain them briefly and recommend one;
* do not ask Michal to manually transport public repository files;
* clearly separate:

  * public verified fact;
  * Worker-observed runtime evidence;
  * inference;
  * recommendation;
  * unresolved decision;
* prefer meaningful vertical product progress over endless speculative defect hunting;
* after explicit acceptance criteria pass, do not repeatedly extend a completed task with increasingly hypothetical edge cases.

Michal owns:

* strategic product intent;
* product priorities;
* UX preferences;
* acceptance of meaningful alternatives;
* protocol-topology decisions;
* account-level and credential actions;
* physical-device actions;
* real private-media authorization;
* irreversible-action approval;
* security-sensitive approval;
* final decisions where several legitimate product directions remain.

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

Current product priority:

* MacBook-first implementation and validation;
* local-first behavior;
* cross-platform architecture;
* premium browser-based development UI evolving toward a native desktop shell;
* later optional Intel NUC aggregation;
* no dependency on NUC, Tailscale, or cloud AI for ordinary local use.

The normal local path is contextual information, not proof.

Every Worker must verify the actual Git root, remote, branch, and public state.

## 2.3 Date-sensitive facts

Current handoff context:

June 2026.

The following are time-sensitive and must be rechecked through current official primary sources when relevant:

* provider model catalogs;
* model availability;
* free or trial access;
* pricing;
* provider API contracts;
* model capabilities;
* NVIDIA endpoint behavior;
* Vercel AI Gateway behavior;
* LM Studio capabilities;
* framework versions;
* Tauri behavior;
* macOS packaging and signing requirements;
* Fedora behavior;
* browser/WebView behavior;
* external media-tool distribution.

Do not convert a temporary free model, provider count, price, trial state, endpoint quirk, or current model name into permanent architecture.

---

# 3. Analytic Programming role and instance model

FrameNest uses the Analytic Programming / Coordinator Protocol.

Persistent uppercase protocol roles:

* `COOPERATOR`
* `ORCHESTRATOR`
* `WORKER`

These are abstract, persistent, vendor-neutral roles.

They are not:

* chats;
* browser tabs;
* IDE windows;
* execution clients;
* agent products;
* models;
* providers;
* local processes;
* individual context windows;
* sessions.

## 3.1 ORCHESTRATOR

`ORCHESTRATOR` is the persistent coordination, coherence, task-shaping, evidence-evaluation, and risk-control role.

An Orchestrator instance is one concrete initialized execution entity temporarily assigned to the `ORCHESTRATOR` role for one bounded Orchestrator session.

An Orchestrator session is the lifecycle and conversational context of that concrete instance.

The following belong to the instance/session, not to the role:

* execution client;
* model;
* provider;
* tools;
* context window;
* context pressure;
* rate limits;
* session duration;
* automatic compaction;
* rotation requirements.

Correct terminology:

* `a fresh Orchestrator instance assigned to the ORCHESTRATOR role`;
* `the current Orchestrator instance is under context pressure`;
* `the ORCHESTRATOR role continues after instance rotation`.

## 3.2 WORKER

`WORKER` is the persistent bounded repository-execution role.

A Worker instance is one concrete initialized execution entity temporarily assigned to the `WORKER` role for one bounded Worker session.

A Worker implementation may use any compatible execution client, agent implementation, model, or provider.

Those implementation details are not protocol roles.

Correct terminology:

* `a fresh Worker instance assigned to the WORKER role`;
* `the previous Worker session is closed`;
* `the WORKER role remains available for a future instance`.

Do not conflate:

1. persistent role;
2. role implementation;
3. concrete instance;
4. instance session;
5. execution client;
6. model;
7. provider.

## 3.3 FrameNest topology

FrameNest currently uses the established single-Worker AP v1 workflow.

Current topology:

* one Worker instance at a time;
* no parallel Worker topology;
* no active APv2 migration;
* no `WORKERS.md` manifest;
* no multi-Worker integration workflow;
* one Orchestrator instance coordinates one fresh Worker instance through bounded tasks.

A separate public methodology repository exists at:

`https://github.com/cisarik/ap`

It contains reusable AP v1 and experimental APv2 material.

It is separate from FrameNest and currently parked.

Do not:

* copy AP repository files into FrameNest automatically;
* modify `/Users/agile/ap` from a FrameNest task;
* migrate FrameNest to APv2 without a dedicated COOPERATOR decision;
* introduce multiple Workers merely because APv2 exists;
* treat methodology development as FrameNest product implementation.

FrameNest continues using its current repository-native AP documents until a dedicated migration decision is made.

---

# 4. Authority model

BOOT and NEXT files restore context.

They do not grant concrete task authority.

The following do not independently authorize repository work:

* this handoff;
* `NEXT_WORKER.md`;
* `BOOT_WORKER.md`;
* `BOOT_ORCHESTRATOR.md`;
* `AP.md`;
* `AP_WORKER.md`;
* `AP_ORCHESTRATOR.md`;
* an ADR;
* a roadmap item;
* a TODO;
* an old Worker report;
* an old Orchestrator recommendation;
* remembered conversation;
* the existence of private test media;
* a listed future feature.

One authoritative ORCHESTRATOR task prompt is the only concrete task authority for a Worker instance.

The `ORCHESTRATOR` role owns:

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

The `WORKER` role owns bounded execution only within the current authoritative prompt.

A Worker report is evidence-bearing testimony.

It is not repository truth.

When public repository evidence is available, independently verify:

1. public HEAD;
2. commit SHA;
3. parent SHA;
4. exact subject;
5. changed paths;
6. relevant raw files;
7. report-versus-diff consistency;
8. public committed state versus local-only runtime evidence;
9. whether claimed validation is public evidence or Worker-observed evidence.

Classify every Worker task result as:

* `PASS`
* `PARTIAL`
* `BLOCKED`

Do not accept alternative status words such as `COMPLETE` as protocol classifications.

Do not continue indefinitely searching for hypothetical defects after explicit acceptance criteria pass.

Prefer coherent product progress.

---

# 5. Current public commit chain before this handoff

A fresh Orchestrator instance must verify this chain.

## 5.1 Manual metadata and Cover Studio architecture

Commit:

`c8bda2139a2d931c57620f0564bff17976d6cfd6`

Subject:

`docs: define manual media and cover workspaces`

This commit established accepted architecture for:

* manual-first metadata editing;
* a primary manual `Current` state;
* separate AI drafts;
* capability-aware future model selection;
* premium tag editing;
* manual Cover Studio;
* candidate-based covers;
* optional AI-generated cover candidates;
* separation of:

  * display title;
  * physical filename;
  * suggested filename;
  * catalog save;
  * future filesystem rename.

## 5.2 Minimum persistent catalog

Commit:

`32794797d2d5c2dcd2c3d4982cd5a23ad0fc9d5e`

Subject:

`feat: add persistent media catalog foundation`

This introduced:

* ADR-0025;
* persistent logical media;
* persistent physical locations;
* media identity types;
* `MediaRepository`;
* SQLAlchemy Core persistence;
* migration `0004`;
* domain, repository, and migration tests.

## 5.3 Previous Worker closeout

Commit:

`e2983920c2c5aeac101dc9e51efcacc801de106a`

Subject:

`docs: close persistent catalog worker session`

This closed the Worker session that implemented the catalog foundation.

## 5.4 Previous manual Orchestrator handoff

Commit:

`cd4071cd391ca3c33238679813e1dd39c785ef83`

Parent:

`e2983920c2c5aeac101dc9e51efcacc801de106a`

Subject:

`handout`

Changed path:

`NEXT_ORCHESTRATOR.md`

Changed-path count:

one

This was the canonical Orchestrator handoff that initialized the session now being closed.

## 5.5 Cycle 063 — explicit scan-candidate import

Commit:

`cfd4a01524045bce0a05059bafc230c36182ea0e`

Parent:

`cd4071cd391ca3c33238679813e1dd39c785ef83`

Subject:

`feat: add explicit scan candidate import`

Changed-path count:

20

This commit introduced:

* ADR-0026;
* application import use case;
* atomic logical-media plus location persistence;
* idempotency by `(library_id, relative_path)`;
* fresh-scan revalidation;
* same-origin import API;
* explicit browser Import action;
* deterministic unit, contract, and integration tests;
* bounded documentation updates.

## 5.6 Cycle 064 — private-corpus smoke

Cycle 064 created no repository commit.

It was a read-only private runtime validation.

It used:

* `dicaprio_bravo.gif`;
* one deterministic top-level MP4 candidate;
* a disposable catalog;
* the real FastAPI import path.

Its sanitized result is recorded later in this handoff.

## 5.7 Cycle 065 — persistent title and canonical tags

Commit:

`a13134551cfefee330afa14dcbbece3bcb1c46f5`

Parent:

`cfd4a01524045bce0a05059bafc230c36182ea0e`

Subject:

`feat: add persistent title and canonical tags`

Changed-path count:

28

This commit introduced:

* ADR-0027;
* pure-domain display-title and canonical-tag types;
* sparse media metadata;
* ordered media-to-tag assignments;
* application use cases;
* repository port;
* SQLAlchemy Core adapter;
* same-origin metadata APIs;
* migration `0005`;
* migration, domain, application, repository, API, and integration tests;
* bounded documentation updates.

## 5.8 Cycle 066 — Worker-session closeout

Commit:

`9fad70ec79bf7bd3638fd3417e4bcbcfd4f6af28`

Parent:

`a13134551cfefee330afa14dcbbece3bcb1c46f5`

Subject:

`docs: close title and tags worker session`

Changed path:

`NEXT_WORKER.md`

Changed-path count:

one

This commit:

* replaced the stale Worker handoff;
* recorded implementation through Cycle 065;
* recorded migration head `0005`;
* recorded Cycle 064 as Worker-observed private runtime evidence;
* listed remaining unimplemented scope;
* declared the concrete Worker session permanently closed;
* granted no future task.

The future manual `handout` commit containing this file is expected to have `9fad70ec...` as its parent when no intervening commit exists.

---

# 6. Current lifecycle state

## 6.1 Worker state

Persistent protocol role:

`WORKER`

Active concrete Worker instance:

none

Active Worker session:

none

Previous concrete Worker session:

permanently `CLOSED`

Current `NEXT_WORKER.md`:

complete and current through Cycle 065

Future Worker requirement:

a fresh Worker instance

Future Worker task authority:

none until one authoritative ORCHESTRATOR prompt is issued

Do not:

* send another prompt to the closed Worker session;
* revive the closed execution-client conversation;
* modify `NEXT_WORKER.md` merely to initialize a new Worker;
* treat the recommendation inside `NEXT_WORKER.md` as authority.

A future fresh Worker receives one new authoritative launch-and-task prompt and reads the current repository-native handoff.

`NEXT_WORKER.md` should be replaced again only at a future explicitly authorized Worker closeout.

## 6.2 Orchestrator state

The Orchestrator instance that produced this file closes after the COOPERATOR commits and pushes this handoff.

Persistent protocol role:

`ORCHESTRATOR`

Active Orchestrator instance after session close:

none until a fresh instance is initialized

Future Orchestrator instance:

must verify the manual `handout` commit before acting

The `ORCHESTRATOR` role persists through instance rotation.

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
8. current raw `NEXT_WORKER.md`;
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
22. current logical-media and physical-location domain implementation;
23. `src/framenest/domain/media_metadata.py`;
24. scan-candidate domain and application contracts;
25. scan preview implementation;
26. library registry;
27. media repository port and adapter;
28. media-import application and API;
29. media-metadata repository port and adapter;
30. media-metadata application and API;
31. current catalog schema;
32. migration `0005`;
33. task-relevant migration, contract, integration, and unit tests;
34. current FastAPI composition;
35. current packaged HTML/CSS/JavaScript UI;
36. recent public Git history through current `main`.

Authority order:

1. current committed implementation and tests;
2. accepted ADRs;
3. current normative documentation;
4. this handoff for decisions not fully represented elsewhere;
5. current `NEXT_WORKER.md`;
6. historical reports;
7. memory and assumptions.

When a status sentence conflicts with implementation and accepted ADRs, classify it as stale.

Do not let a stale handoff or roadmap sentence override current code.

---

# 8. Current implemented product foundation

FrameNest is still foundation-stage and pre-alpha.

It is not an empty scaffold.

It has substantial executable foundations.

## 8.1 Python and repository foundation

Expected current foundation:

* CPython `>=3.13,<3.14`;
* Poetry dependency and virtual-environment management;
* committed lockfile;
* staged source layout under `src/framenest/`;
* professional English repository documentation;
* deterministic tests;
* explicit migration tooling;
* MacBook-first validation.

## 8.2 Local FastAPI server

Implemented:

* FastAPI application factory;
* typed `GET /health`;
* Uvicorn runtime;
* `framenest-server` entrypoint;
* loopback-first binding;
* structured JSON logging;
* centralized redaction;
* deterministic engine cleanup;
* no automatic migration on server startup.

Do not describe FrameNest as having no server.

## 8.3 Persistence foundation

Implemented:

* synchronous SQLAlchemy Core;
* SQLite;
* Alembic;
* explicit migration commands;
* migration head `0005`;
* stable domain identities;
* device registry;
* library registry;
* logical media;
* physical locations;
* canonical tags;
* sparse media metadata;
* ordered media-to-tag assignments.

Server startup does not automatically migrate a database.

No real user catalog may be migrated without explicit task authority.

## 8.4 Read-only scan preview

Implemented:

* registered libraries;
* deterministic bounded read-only scan preview;
* library-relative candidates;
* supported video and GIF classification;
* secure traversal boundaries;
* safe symlink behavior;
* no automatic persistence from scan;
* no file mutation;
* no automatic scan on page load.

## 8.5 Explicit persistent import

Implemented:

* explicit user-triggered import;
* one selected relative path per request;
* fresh-scan revalidation;
* no trust in client-provided kind or size;
* video to `video`;
* GIF to `animated_image`;
* atomic logical-media plus physical-location creation;
* exact-path idempotency;
* existing IDs returned on repeated import;
* no filesystem mutation;
* browser Import action.

Exact API:

`POST /api/libraries/{library_id}/media-imports`

## 8.6 Persistent display title and tags

Implemented:

* optional display title;
* stable canonical English tag keys;
* separate tag display names;
* ordered tag assignments;
* zero to 32 tags per medium;
* sparse metadata rows;
* atomic complete metadata replacement;
* create/update/unchanged statuses;
* exact no-op saves preserve `updated_at_ms`.

Exact APIs:

* `POST /api/canonical-tags`
* `GET /api/canonical-tags`
* `GET /api/media/{media_id}/metadata`
* `PUT /api/media/{media_id}/metadata`

These APIs exist even though the browser does not yet expose a persistent metadata editor.

## 8.7 Local media analysis

Implemented:

* explicit local analysis;
* technical metadata;
* up to three exact-distinct representative PNG frames;
* no persistent frame artifact;
* no automatic provider call;
* no automatic catalog mutation.

## 8.8 Local web application

Implemented browser development UI includes:

* packaged vanilla HTML;
* packaged CSS;
* packaged JavaScript;
* same-origin API communication;
* health state;
* library listing;
* explicit scan;
* scan candidates;
* explicit Import action;
* local inspection;
* representative frames;
* AI capability state;
* explicit cloud confirmation;
* editable non-persistent AI suggestion review.

The browser UI does not yet include:

* catalog media listing;
* persistent metadata workspace;
* title search;
* tag filtering;
* premium gallery;
* Cover Studio.

The current browser is a development/pre-alpha shell, not the final flagship gallery.

No frontend framework has been accepted.

Do not introduce React, Vue, Svelte, Vite, or another framework without a dedicated ADR and demonstrated need.

## 8.9 AI/VLM foundation

Implemented prototype foundation includes:

* provider-neutral application boundary;
* NVIDIA NIM prototype;
* strict structured response validation;
* prompt version:
  `framenest-media-suggestion-v2`;
* internal PNG frames;
* bounded JPEG VLM derivatives;
* Pillow confined to infrastructure;
* no temporary JPEG files;
* documented non-thinking/instruct request behavior;
* explicit user-triggered analysis;
* explicit cloud confirmation;
* server-side credential boundary;
* browser receives no credential;
* editable ephemeral review;
* no automatic save, rename, tagging, collection assignment, or cover activation.

AI remains optional.

---

# 9. Cycle 063 details — explicit idempotent import

ADR-0026 is accepted and implemented.

Core invariants:

* scan remains read-only;
* import is explicit;
* import is not triggered by page load;
* import is not triggered by scan completion;
* request identifies one library-relative path;
* server revalidates the selected candidate through a fresh bounded scan;
* client-provided kind, extension, and size are not trusted;
* unavailable or stale candidates fail safely;
* supported video candidates become `video`;
* GIF candidates become `animated_image`;
* one new import creates:

  * one logical medium;
  * one physical location;
* both are created in one transaction;
* exact `(library_id, relative_path)` is the idempotency key;
* repeat import returns existing identities;
* repeat import performs no update;
* failure cannot leave an orphan logical medium;
* no tags, title, cover, AI, sidecar, rename, move, or deletion occurs;
* no schema change beyond `0004` was needed.

The browser provides truthful states such as:

* pending;
* imported;
* already imported;
* retryable failure.

The existing local Inspect action remains separate.

---

# 10. Cycle 065 details — persistent display title and canonical tags

ADR-0027 is accepted and implemented.

## 10.1 Display title

A logical medium may have zero or one persisted display title.

Rules:

* absence is valid;
* empty string is invalid;
* title is separate from filename;
* title is separate from relative path;
* title is separate from suggested filename;
* leading or trailing whitespace is rejected;
* maximum length is 240 Unicode code points;
* NUL and Unicode control characters are forbidden;
* saving or clearing title does not:

  * rename a file;
  * move a file;
  * change media bytes;
  * change filesystem timestamps.

Fallback presentation from filename remains UI behavior and is not persisted as title truth.

## 10.2 Canonical tag identity

Canonical tags are content and organization tags.

Source platform remains a separate future structured field.

Canonical tag identity:

* stable English lowercase ASCII slug;
* no UUID tag identity;
* immutable in the current slice;
* examples:

  * `mathematics`
  * `compression`
  * `meme`
  * `reaction-video`

Key rules:

* begins with `a-z`;
* contains only `a-z`, `0-9`, and single hyphen separators;
* no leading hyphen;
* no trailing hyphen;
* no consecutive hyphens;
* maximum length 64.

Display name:

* separate presentation text;
* English;
* 1–80 Unicode code points;
* trimmed;
* no NUL or Unicode control characters.

No initial tag catalog is hardcoded or seeded.

Tag deletion and rename are not implemented.

## 10.3 Canonical tag creation

Tag creation is explicit.

Same key and same display name:

`already_exists`

Same key and different display name:

definition conflict

A metadata save cannot implicitly create or rename a canonical tag.

## 10.4 Media metadata

One logical medium may have:

* optional display title;
* zero to 32 ordered canonical tags.

Ordering:

* persisted;
* zero-based;
* deterministic.

Saving metadata:

* replaces the complete ordered tag assignment set;
* empty list removes assignments;
* all keys must already exist;
* duplicate keys are invalid;
* first save returns `created`;
* changed save returns `updated`;
* semantically identical save returns `unchanged`;
* unchanged save performs no write;
* unchanged save preserves `updated_at_ms`;
* title and tag replacement are atomic;
* rollback preserves complete prior state.

## 10.5 Sparse metadata

Importing media does not automatically create a metadata row.

An existing medium with no metadata row is represented as:

* `persisted: false`;
* `display_title: null`;
* `tags: []`;
* metadata timestamps absent.

First explicit save creates the row.

This preserves a clean distinction between:

* imported catalog identity;
* explicit user metadata.

## 10.6 Migration `0005`

Migration head:

`0005`

New tables:

* `canonical_tags`
* `media_metadata`
* `media_canonical_tags`

Upgrade behavior:

* existing device rows survive;
* existing library rows survive;
* existing logical media survive;
* existing physical locations survive;
* no metadata rows are automatically backfilled.

Downgrade behavior:

* assignment table removed;
* metadata table removed;
* canonical-tag table removed;
* previous device/library/media/location state remains.

Do not claim that migration head is `0004`.

---

# 11. Accepted architecture horizon

The ADR index extends through ADR-0027.

A fresh Orchestrator must verify the current highest ADR.

## ADR-0021 — Tauri desktop shell

Accepted future direction:

* Tauri v2;
* native WebView;
* Python/FastAPI sidecar;
* single-instance lifecycle;
* tray/menu-bar integration;
* browser mode retained for development and diagnostics;
* least-privilege native capabilities.

Not implemented.

Not the immediate next task.

## ADR-0022 — selective placement and server aggregation

Accepted future direction:

* one logical medium;
* multiple physical locations;
* local desktop catalogs;
* optional future server aggregator;
* selective placement;
* no automatic full replication to all devices.

NUC aggregation, streaming, transfer, and remote download are not implemented.

## ADR-0023 — manual-first metadata workspace and AI drafts

Accepted direction:

* media detail is primarily manual;
* `Current` is the primary working state;
* AI drafts are separate proposals;
* AI does not silently overwrite `Current`;
* `Use this draft` is not durable persistence by itself;
* catalog save is distinct from filesystem rename;
* manual editing must work without AI or internet;
* future model selection is capability-aware.

Persistent title/tag APIs now exist.

The user-facing manual metadata workspace is still not implemented.

## ADR-0024 — Cover Studio and AI cover candidates

Accepted future direction:

* manual timeline selection first;
* exact cover timestamp;
* cover timestamp independent from playback start;
* normal playback begins at `00:00`;
* cover candidates require explicit activation;
* AI-generated cover is a separate future workflow;
* no automatic replacement of accepted cover.

Not implemented.

## ADR-0025 — minimum persistent catalog

Implemented:

* logical media;
* physical locations;
* media kinds;
* availability states;
* safe relative paths;
* repository boundary;
* migration `0004`.

## ADR-0026 — explicit idempotent import

Implemented:

* fresh-scan-revalidated selected import;
* atomic persistence;
* exact-path idempotency;
* browser Import action;
* API endpoint.

## ADR-0027 — persistent display title and canonical tags

Implemented:

* optional display title;
* stable English canonical keys;
* tag definitions;
* ordered assignments;
* sparse metadata;
* atomic save;
* migration `0005`;
* API endpoints.

Accepted future architecture is not automatically implemented functionality.

---

# 12. Explicitly unimplemented state

Unless newer verified commits prove otherwise, the following remain unimplemented:

* catalog media-list/read-model endpoint suitable for normal gallery use;
* title search;
* canonical-tag filtering;
* multi-tag AND filtering;
* deterministic user-facing catalog pagination;
* browser persistent metadata workspace;
* premium tag-chip editor;
* persistent description;
* persistent collection;
* persistent suggested filename;
* structured source-platform field;
* source-platform tag presentation;
* persistent AI drafts;
* multi-model draft strip;
* inline model picker;
* manual Cover Studio;
* exact cover-timestamp persistence;
* cover candidate persistence;
* thumbnail generation;
* thumbnail cache;
* premium persistent gallery;
* series domain beyond current planning;
* storage-volume entities beyond identity foundation;
* sidecar manifest;
* sidecar roundtrip;
* filesystem rename;
* filesystem move;
* file deletion;
* native OS tag synchronization;
* content hashing;
* perceptual hashing;
* automatic duplicate detection;
* automatic logical-media merge;
* Tauri scaffold;
* native system tray/menu bar;
* native file picker;
* native clipboard;
* native download/export;
* reveal in Finder/file manager;
* VLC launch capability;
* NUC deployment;
* global catalog aggregation;
* streaming;
* remote download;
* transfer workflows;
* GUI Settings;
* final OS secret-store integration;
* production authentication;
* installer;
* signing;
* supported release;
* systemd deployment;
* production Tailscale integration;
* finished downloader workflow.

Do not claim:

* that no catalog exists;
* that import is absent;
* that display title is absent;
* that canonical tags are absent;
* that migration head remains `0004`.

Do not claim future documented features are already implemented.

---

# 13. Manual-first product invariants

Preserve these invariants.

## 13.1 AI remains optional

AI must:

* be explicitly requested;
* remain optional;
* never own metadata truth;
* never be required for normal metadata editing;
* never run merely because a detail page opens;
* never silently overwrite manual work;
* never automatically save;
* never automatically rename;
* never automatically move;
* never automatically tag;
* never automatically assign a collection;
* never automatically activate a cover.

## 13.2 Metadata state separation

Keep distinct:

* physical filename;
* library-relative path;
* display title;
* description;
* collection;
* source platform;
* suggested filename;
* persisted catalog state;
* unsaved manual `Current`;
* AI draft;
* promoted draft values;
* durable catalog save;
* future filesystem rename.

Changing a display title must not rename a file.

Saving metadata must not mutate media bytes or physical placement.

## 13.3 Canonical tag UX

Future user-facing tag editing should provide:

* stable English canonical identities;
* human-readable display names;
* searchable local suggestions;
* rapid keyboard interaction;
* mouse interaction;
* rounded removable chips;
* explicit `×` removal;
* duplicate prevention;
* selected, suggested, invalid, hover, and focus states;
* no fake progress indicator for trivial local filtering.

## 13.4 Premium UX

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

# 14. Desktop and server direction

## 14.1 MacBook-first

Current implementation priority:

* local server;
* local browser development UI;
* durable catalog;
* import;
* metadata;
* retrieval/search;
* manual metadata workspace;
* covers;
* gallery;
* AI drafts;
* tested first on MacBook.

Do not divert the immediate path to Fedora NUC deployment.

## 14.2 Future native desktop shell

The finished normal user experience should not require Chrome, Brave, Firefox, or another external browser.

Accepted future direction:

* Tauri v2;
* WebView shell;
* Python/FastAPI sidecar;
* single instance;
* system tray or macOS menu bar;
* initial menu:

  * `Gallery`
  * `Settings`
  * `Quit`
* future native:

  * file picker;
  * directory picker;
  * clipboard;
  * download destination;
  * export;
  * reveal;
  * VLC launch;
  * lifecycle control.

Do not scaffold Tauri before catalog retrieval, metadata UX, covers, and gallery foundations are mature enough to justify it.

## 14.3 Future Intel NUC

The future Intel NUC is intended as:

* Fedora KDE desktop;
* optional FrameNest server;
* archive/storage node;
* aggregate catalog node;
* streaming source;
* transfer target;
* later centralized provider boundary.

It must not become a mandatory dependency for local desktop operation.

Tailscale is intended only for remote functions.

Local gallery, local playback, local catalog, local metadata, and local search must work without Tailscale or internet.

---

# 15. Private local test-media corpus

The COOPERATOR has a private local test corpus at:

`/Users/agile/Video`

It contains multiple MP4 meme clips.

It includes:

`dicaprio_bravo.gif`

The existence of this path grants no access authority.

A future Worker MUST NOT access the corpus unless one authoritative ORCHESTRATOR prompt explicitly defines the minimum necessary authority.

Any private-corpus task must define:

* exact authorized path;
* read-only or write authority;
* exact file patterns;
* named sample versus all files;
* permitted stat/header reads;
* permitted content hashing;
* permitted frame extraction;
* permitted temporary derivatives;
* cleanup requirements;
* disposable versus user catalog;
* provider/network authority;
* reporting privacy rules.

Default boundaries:

* no access without explicit authority;
* no rename;
* no move;
* no delete;
* no tag mutation;
* no sidecar;
* no thumbnail;
* no derivative beside media;
* no timestamp modification;
* no cloud upload;
* no provider transmission;
* no raw frame transmission;
* no automatic import;
* no automatic analysis;
* no automatic AI.

Cloud transmission requires separate explicit confirmation even when local read access has already been granted.

---

# 16. Cycle 064 private runtime evidence

Classification:

`Worker-observed private runtime evidence`

It is not a public repository commit.

Observed sanitized result:

* `dicaprio_bravo.gif` was visible in the real scan;
* one MP4 was selected deterministically;
* first MP4 import returned:

  * `created`
  * kind `video`;
* first GIF import returned:

  * `created`
  * kind `animated_image`;
* repeated MP4 import returned:
  `already_imported`;
* repeated GIF import returned:
  `already_imported`;
* repeated media and location IDs matched the first results;
* disposable database contained:

  * 2 logical-media rows;
  * 2 physical-location rows;
* duplicate count:
  0;
* selected source SHA-256 values were unchanged;
* selected source sizes were unchanged;
* selected source mtimes were unchanged;
* top-level directory-entry count and digest were unchanged;
* no sidecar or derivative was created;
* no database was created beside media;
* no provider was called;
* no AI was called;
* no ffmpeg or ffprobe was used;
* no real user catalog was accessed;
* temporary state was cleaned;
* repository state remained unchanged.

Do not expose:

* selected MP4 filename;
* private hashes;
* private directory listing;
* database UUIDs;
* raw media;
* raw frames;
* other filenames.

A future task must not present these private observations as independently public evidence.

---

# 17. Worker-observed validation evidence

These command results were reported by the now-closed Worker session.

A future Orchestrator or Worker must not claim to have run them.

## 17.1 Cycle 063

Reported:

* focused suite:
  `114 passed`;
* collection:
  `812 tests collected`;
* full suite:
  `809 passed`, `3 skipped`;
* warning-as-error:
  `809 passed`, `3 skipped`;
* Poetry lock check passed;
* compileall passed;
* build passed;
* wheel assets confirmed;
* Markdown links passed;
* `dist/` removed;
* worktree clean.

## 17.2 Cycle 064

Reported:

* focused integration test:
  `1 passed`;
* disposable migration to `0004`;
* real MP4/GIF import smoke passed;
* idempotency passed;
* source immutability passed;
* cleanup passed;
* no repository changes.

## 17.3 Cycle 065 baseline

Reported before implementation:

* `812 tests collected`;
* `809 passed`;
* `3 skipped`.

## 17.4 Cycle 065 final

Reported:

* `870 tests collected`;
* full suite:
  `867 passed`, `3 skipped`;
* warning-as-error:
  `867 passed`, `3 skipped`;
* Poetry lock check passed;
* compileall passed;
* package build passed;
* wheel inspection passed;
* migration `0005` packaged;
* HTML/CSS/JavaScript assets remained packaged;
* Markdown local links:
  `681` checked;
* `dist/` removed;
* no private-media access;
* no provider call;
* no secret access;
* no user-catalog access;
* final worktree clean.

## 17.5 Cycle 066 closeout

Reported:

* Markdown local links:
  `681` checked across `56` Markdown files;
* exactly `NEXT_WORKER.md` changed;
* secret/private-data audit passed;
* `dist/` absent;
* final public/local/tracking equality at:
  `9fad70ec79bf7bd3638fd3417e4bcbcfd4f6af28`;
* final worktree clean.

A future Worker must rerun validation required by its own task.

Do not preserve old counts as expected fixed counts after adding tests.

---

# 18. Sanitized historical NVIDIA evidence

Historical Worker-observed evidence from a prior explicitly authorized live test:

* one authorized NVIDIA request;
* HTTP status:
  `200`;
* no pending polling;
* non-empty final content;
* no `reasoning_content`;
* strict structured parsing succeeded;
* model reported at that time:
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

Do not assume:

* endpoint availability;
* model availability;
* free access;
* pricing;
* token behavior;
* capability;
* response shape;

remain unchanged.

Do not claim JPEG transport reduced token use without a controlled comparative experiment.

No provider call occurred in Cycles 063–066.

---

# 19. Known current risks and cautions

## 19.1 No user-facing persistent metadata workspace

Persistent metadata APIs exist.

The browser does not yet expose:

* persistent title editing;
* canonical tag creation;
* canonical tag selection;
* persistent Save;
* saved/unsaved state;
* conflict handling.

Do not confuse API implementation with completed metadata UX.

## 19.2 No catalog retrieval/search layer

The current system can import and persist media, title, and tags.

It does not yet provide a normal catalog read model suitable for:

* media listing;
* title search;
* tag filtering;
* multi-tag AND filtering;
* pagination;
* gallery consumption.

This is the key missing bridge between persistence and a usable manual workspace/gallery.

## 19.3 Current browser is a development shell

The current web UI is pre-alpha.

It is not the target premium gallery.

Do not polish isolated admin-like screens indefinitely without advancing durable user workflows.

## 19.4 Provider facts are unstable

Provider/model catalogs, trial access, and model capabilities are time-sensitive.

Always verify current official sources before provider-related task shaping.

## 19.5 Real database migration remains sensitive

Migration `0005` is implemented and tested against disposable databases.

Do not migrate an existing real user catalog without explicit future authority.

## 19.6 Private corpus remains sensitive

Cycle 064 access was task-specific and expired after completion.

No future Worker inherits that authority.

---

# 20. Strongest next product direction

The strongest current direction is a bounded catalog retrieval and search vertical slice that enables the accepted manual metadata workspace.

This is a recommendation.

It is not task authority.

## 20.1 Roadmap interpretation

The current roadmap places:

`manual metadata detail`

after persistent title/tag metadata.

The current Worker handoff recommends:

* catalog media-list/read-model API;
* title search;
* canonical-tag filtering;
* multi-tag AND semantics;
* deterministic pagination and order.

These should not be treated as conflicting directions.

A likely coherent interpretation is:

* the read/search layer is the enabling backend and application slice for the manual metadata detail and premium gallery;
* it should be shaped as a product-facing vertical step, not as isolated infrastructure;
* it should not become a long detour that postpones the manual workspace indefinitely.

## 20.2 Why retrieval/search is likely next

FrameNest now persists:

* logical media;
* physical locations;
* display title;
* canonical tags;
* ordered assignments.

The next convergence point is retrieving these records in a deterministic, privacy-safe, UI-consumable form.

Without a catalog read model:

* the browser cannot select a persisted medium normally;
* the manual metadata workspace has no catalog navigation foundation;
* title search cannot exist;
* tag filtering cannot exist;
* gallery cards cannot consume durable catalog data.

## 20.3 Likely bounded scope

A future Orchestrator should inspect current repository contracts and consider a vertical slice containing:

* accepted ADR if a real architecture decision is needed;
* deterministic media-list/read model;
* title query;
* canonical-tag filters;
* multi-tag AND semantics;
* stable ordering;
* bounded pagination;
* safe treatment of media with no metadata;
* safe treatment of media with multiple locations;
* API endpoint;
* existing vanilla browser integration sufficient to make the workflow reachable;
* deterministic tests;
* documentation alignment.

Potentially deferred from that first slice:

* full metadata editing;
* premium tag chips;
* cover cards;
* descriptions;
* collections;
* AI drafts;
* Tauri;
* NUC.

## 20.4 Questions the fresh Orchestrator must resolve from code

Before creating a Worker prompt, inspect and resolve:

1. What application read model best serves both manual metadata detail and future gallery?
2. Should one logical medium return all locations or only summarized availability?
3. What should be the deterministic default ordering?
4. How should untitled media be ordered?
5. Should search use only persisted display title in the first slice?
6. Should physical filename fallback be presentation-only?
7. What exact normalization and matching semantics should title search use?
8. Should tag filters accept canonical keys only?
9. Must multiple selected tags use AND by default?
10. How should zero selected tags behave?
11. What pagination contract is stable and testable?
12. Should offset pagination be sufficient initially?
13. How should unavailable/offline locations affect listing?
14. Is a new repository port needed or should a dedicated read repository exist?
15. Does the existing media metadata schema need an index migration?
16. Is migration `0006` required?
17. Can title search and tag filtering remain efficient without premature indexing?
18. What is the smallest browser workflow that creates visible product value?
19. Does the first browser slice list imported media and open a metadata workspace placeholder?
20. Which exact paths and tests must be authorized?

Do not invent answers before inspecting current code.

## 20.5 Preferred task shape

Prefer one meaningful vertical slice.

Avoid several backend-only cycles with no reachable user workflow.

A strong first slice may include:

* read repository;
* application query;
* API;
* simple persisted-media browser list;
* title search;
* tag filter controls;
* multi-tag AND;
* deterministic tests.

Then the immediate next slice can implement:

* manual persistent metadata detail;
* premium tag editing;
* save state;
* title editing.

The fresh Orchestrator may choose a different bounded shape if current code evidence shows a safer or more coherent path.

---

# 21. Product sequence after current state

Current intended near-term sequence:

1. persistent catalog foundation — complete;
2. logical media and physical locations — complete;
3. explicit idempotent selected import — complete;
4. persistent display title and canonical tags — complete;
5. catalog read model, title search, and tag filtering — likely next enabling slice;
6. manual persistent metadata detail;
7. premium tag-chip editing;
8. Cover Studio and derivatives;
9. persistent premium gallery;
10. multi-model AI draft workspace;
11. optional AI cover experiments;
12. Tauri desktop shell;
13. later NUC aggregation, streaming, transfer, and remote workflows.

Do not jump directly to:

* Tauri;
* NUC;
* Cover Studio;
* AI draft persistence;

before the normal catalog retrieval and metadata UX foundation is usable.

Do not postpone visible product progress indefinitely for infrastructure refinement.

---

# 22. Public commit verification loop

After every Worker report:

1. resolve current public `main`;
2. inspect the reported commit;
3. verify parent;
4. verify exact subject;
5. verify changed paths;
6. inspect relevant raw files;
7. compare report claims to public diff;
8. distinguish public implementation evidence from runtime evidence;
9. distinguish committed state from local-only claims;
10. classify:

    * `PASS`
    * `PARTIAL`
    * `BLOCKED`.

When public push fails or a commit is unavailable:

* state what is publicly verifiable;
* state what comes only from the Worker report;
* do not claim public verification.

Do not accept a report merely because tests are listed.

Check:

* scope;
* allowlist;
* forbidden paths;
* migration history;
* handoff files;
* secrets;
* private data;
* commit structure.

---

# 23. Worker prompt requirements

When the next task is ready, introduce the prompt to Michal exactly:

`Toto pošli WORKEROVI ako jeden prompt:`

The prompt must be one coherent, copy-pasteable English block.

It must include:

* fresh Worker instance identity;
* persistent `WORKER` role;
* repository URL;
* exact working directory;
* branch;
* exact verified public HEAD;
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
* stop conditions;
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
* claim unrun tests;
* claim public verification from local-only state;
* silently expand scope.

---

# 24. Brainstorming protocol

Strategic ambiguity belongs primarily between the COOPERATOR and ORCHESTRATOR.

When a real decision blocks safe task shaping:

1. explicitly state:
   `Brainstorming`;
2. explain one decision;
3. provide concise alternatives when useful;
4. recommend one;
5. ask Michal exactly one focused question;
6. wait for the answer;
7. incorporate it;
8. only then create a Worker prompt.

Do not ask a questionnaire.

Do not force every question into A/B options when Michal should explain the intent.

A Worker may stop and report:

* missing path authority;
* contradictory repository evidence;
* required out-of-scope file;
* migration ambiguity;
* unsafe prerequisite;
* multiple legitimate architecture alternatives.

When that happens:

* do not punish the stop;
* inspect the evidence;
* provide a narrow continuation when appropriate;
* do not repeat the entire task unnecessarily;
* preserve the current clean state.

Cycles 062 and 065 demonstrated the correct missing-allowlist behavior:

* Worker stopped before editing;
* Orchestrator verified the required path;
* Orchestrator granted one explicit path continuation;
* Worker then completed the logical task.

---

# 25. Error-prevention method

Do not rely mainly on vague instructions such as:

`be careful`

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
* code and ADR inspection;
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
* changed-path audit;
* staged-path audit;
* pre-commit remote gate;
* exact commit subject;
* normal push only;
* post-push public verification;
* final clean worktree;
* structured report.

A Worker must stop rather than guess.

---

# 26. Artifact lifecycle rules

Every new documentation or evidence artifact should have:

* classification;
* concrete consumer;
* inbound reference;
* retention or cleanup trigger;
* cleanup owner.

Durable ADRs:

* remain until explicitly superseded;
* must be indexed;
* must describe accepted decisions;
* must not become temporary task logs.

Temporary research or decision evidence:

* should be removed after accepted conclusions and relevant sources are transferred;
* must not accumulate as orphaned Markdown files;
* requires explicit deletion authority.

Worker must not delete artifacts automatically without task-specific authority.

Git history remains the archive.

The active working tree should not accumulate consumed evidence files.

---

# 27. Context pressure and rotation

Context pressure belongs to concrete instances and sessions.

It does not belong to persistent roles.

Rotate a Worker instance when:

* a substantial coherent task is complete;
* automatic compaction occurs repeatedly;
* context telemetry becomes constrained;
* rate limits disrupt work;
* repeated summarization risks losing constraints;
* a major subsystem change is next;
* quality degrades;
* a clean committed boundary exists.

The Worker session closed in Cycle 066 because:

* Cycle 065 completed a major coherent slice;
* context was automatically compacted more than once;
* a clean public boundary existed;
* continuing would increase risk.

Rotate an Orchestrator instance when:

* strategic context becomes large;
* many product decisions accumulate;
* a clean repository-native handoff exists;
* source-of-truth recovery would benefit from a fresh instance.

No fixed token percentage is universally required.

Use actual context pressure, observed quality, task size, and repository state.

A closed Worker session must never be revived.

Repeated in-chat summaries are not a substitute for repository-native handoffs and public Git evidence.

---

# 28. First-response contract for the fresh Orchestrator instance

Before the first substantive response, the fresh Orchestrator instance must:

1. identify current public `main`;
2. inspect the latest commit;
3. locate the commit containing this handoff;
4. verify that handoff commit’s parent;
5. verify its subject:
   `handout`;
6. verify changed path:
   `NEXT_ORCHESTRATOR.md`;
7. verify changed-path count:
   one;
8. read current raw `NEXT_ORCHESTRATOR.md`;
9. read current raw `NEXT_WORKER.md`;
10. confirm Worker session state:
    `CLOSED`;
11. confirm no active Worker exists;
12. verify commit `9fad70ec...`;
13. verify commit `a131345...`;
14. verify commit `cfd4a015...`;
15. verify migration head `0005`;
16. inspect ADR index;
17. verify highest accepted ADR;
18. inspect ADR-0026;
19. inspect ADR-0027;
20. inspect media import implementation;
21. inspect metadata domain and persistence;
22. inspect metadata API;
23. inspect migration `0005`;
24. inspect roadmap;
25. inspect current UI boundaries;
26. identify any stale status statement;
27. distinguish public evidence from Worker-observed evidence;
28. determine whether any newer public commit exists;
29. determine whether repository state contradicts this handoff;
30. decide whether the next task is safe to shape immediately.

Its first response to Michal must:

* be in Slovak;
* refer to herself in feminine grammatical gender;
* state resolved public HEAD;
* state verified handoff commit;
* classify restoration as:

  * `PASS`
  * `PARTIAL`
  * `BLOCKED`;
* state whether this file is canonical;
* summarize actual implemented state;
* confirm the previous Worker session is permanently closed;
* confirm no active Worker exists;
* confirm migration head `0005`;
* confirm ADR horizon through ADR-0027;
* explain the likely next product step;
* identify any genuine strategic ambiguity;
* produce exactly one authoritative prompt for one fresh Worker when safe;
* avoid multiple competing prompts;
* avoid asking Michal to paste public repository files.

If a critical decision remains unresolved:

* enter Brainstorming;
* ask exactly one focused question;
* do not fabricate a Worker task.

---

# 29. Recommended fresh Worker initialization

When a next task is selected:

* create one new authoritative Worker prompt;
* identify the new execution entity as:
  `a fresh Worker instance assigned to the WORKER role`;
* instruct it to read:

  * `AGENTS.md`;
  * `BOOT_WORKER.md`;
  * `AP_WORKER.md`;
  * `NEXT_WORKER.md`;
  * task-relevant ADRs and code;
* do not manually copy `NEXT_WORKER.md` into the Worker conversation;
* the Worker reads it from the repository;
* the authoritative prompt remains the only task authority.

Do not modify `NEXT_WORKER.md` merely to initialize the fresh Worker.

---

# 30. Orchestrator session-close protocol

At a future Orchestrator-session close:

1. produce a complete replacement for `NEXT_ORCHESTRATOR.md`;
2. make it self-contained;
3. include current public evidence;
4. include current Worker lifecycle state;
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

`NEXT_WORKER.md` is updated only when a Worker session requires closeout.

`NEXT_ORCHESTRATOR.md` is updated manually by the COOPERATOR at Orchestrator-session close.

---

# 31. Current session-close declaration

This Orchestrator session is complete after the COOPERATOR commits this handoff.

Completed during this session:

* restoration from the previous manual Orchestrator handoff;
* independent public verification of repository state;
* Cycle 063:
  explicit idempotent selected scan-candidate import;
* correction of initial Worker scope deviations before commit;
* public verification of the import commit;
* Cycle 064:
  explicitly authorized read-only private-corpus smoke;
* verification of GIF and MP4 import behavior;
* preservation of media bytes and timestamps;
* Cycle 065:
  persistent display title and canonical tags;
* correction of one missing allowlisted migration-test path;
* ADR-0027;
* migration `0005`;
* persistent sparse metadata;
* ordered tag assignments;
* canonical-tag APIs;
* metadata APIs;
* public verification of Cycle 065;
* recognition of repeated Worker context compaction;
* Cycle 066 Worker-session closeout;
* replacement of stale `NEXT_WORKER.md`;
* permanent closure of the concrete Worker session.

Current state after this handoff:

* persistent role:
  `ORCHESTRATOR` continues;
* active Orchestrator instance:
  none after this session closes;
* persistent role:
  `WORKER` continues;
* active Worker instance:
  none;
* previous Worker session:
  permanently closed;
* current Worker handoff:
  complete through Cycle 065;
* current Orchestrator handoff:
  this file;
* migration head:
  `0005`;
* highest accepted ADR:
  ADR-0027;
* pending authorized Worker task:
  none;
* strongest next recommendation:
  catalog read/search vertical slice enabling manual metadata detail;
* private test corpus:
  available only under future explicit task authority;
* current public repository before manual `handout`:
  `9fad70ec79bf7bd3638fd3417e4bcbcfd4f6af28`.

---

# 32. Success condition

This handoff succeeds when a fresh Orchestrator instance:

1. discovers and verifies the new manual `handout` commit;
2. confirms its parent is the Worker closeout commit when no intervening commit exists;
3. treats this file as canonical;
4. restores the role-versus-instance model;
5. restores the single-Worker AP v1 topology;
6. confirms the prior Worker session is permanently closed;
7. confirms no active Worker exists;
8. verifies implementation through Cycle 065;
9. verifies closeout Cycle 066;
10. verifies migration `0005`;
11. verifies ADR-0026;
12. verifies ADR-0027;
13. understands that import exists;
14. understands that display title exists;
15. understands that canonical tags exist;
16. understands that browser metadata editing does not yet exist;
17. understands that title search and tag filtering do not yet exist;
18. preserves manual-first product invariants;
19. preserves AI-optional behavior;
20. preserves Cover Studio direction;
21. preserves premium gallery direction;
22. understands private MP4/GIF evidence without inheriting private access;
23. keeps cloud access separately authorized;
24. recognizes catalog retrieval/search as the likely enabling next direction;
25. reconciles that enabling slice with the roadmap’s manual metadata detail goal;
26. inspects current code before shaping the task;
27. initializes one fresh Worker instance;
28. produces one precise authoritative Worker prompt;
29. independently verifies every future Worker commit;
30. rotates instances when context pressure threatens quality;
31. closes future sessions through repository-native handoffs;
32. continues toward a usable, premium, local-first MacBook product.
