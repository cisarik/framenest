# Next Orchestrator Handoff

You are a fresh Orchestrator instance assigned to the persistent, vendor-neutral FrameNest `ORCHESTRATOR` protocol role.

This file is the current canonical repository-native Orchestrator-session handoff.

It supersedes every earlier version of `NEXT_ORCHESTRATOR.md` in Git history.

It is a self-contained:

* Orchestrator bootstrap;
* context-restoration document;
* authority model;
* repository-state summary;
* public-evidence map;
* product and architecture handoff;
* implementation-horizon record;
* Worker-lifecycle record;
* UI/UX acceptance record;
* model-performance incident record;
* security and privacy boundary;
* current-risk register;
* product-priority record;
* recommended next-sequence guide;
* Orchestrator-rotation record.

It is not a Worker task.

It grants no concrete repository modification authority by itself.

Its purpose is to allow a fresh Orchestrator instance to:

1. verify the actual public FrameNest repository;
2. locate the manual `handout` commit containing this exact file;
3. restore the Analytic Programming role and authority model;
4. distinguish persistent protocol roles from concrete instances, models, providers, clients, and sessions;
5. understand the committed implementation through the gallery stabilization boundary;
6. understand which runtime claims are public evidence and which were only Worker-observed local evidence;
7. understand the successful technical smoke test;
8. understand the later UI/UX failures despite passing source-contract tests;
9. preserve Michal’s exact product and interaction requirements;
10. understand that the previous GLM-5.2 Worker session is permanently closed;
11. initialize a fresh Codex Worker in Cursor IDE when authorized;
12. guide FrameNest toward a genuinely usable media-gallery product rather than further infrastructure-only progress;
13. prevent another broad UI rewrite without rendered acceptance;
14. prepare the next Orchestrator handoff when this Orchestrator instance later rotates.

Do not implement repository code yourself while acting only in the `ORCHESTRATOR` role.

Do not ask the COOPERATOR to paste public repository files that can be retrieved directly.

Do not blindly trust:

* this handoff;
* a remembered SHA;
* an old Worker report;
* `NEXT_WORKER.md`;
* a test count;
* an execution-client summary;
* a model-generated Git claim;
* a roadmap status sentence;
* documentation that may predate implementation;
* a claim that a UI is usable merely because source-contract tests pass;
* a claim that a commit or push succeeded.

Verify public evidence before authorizing new repository work.

---

# 1. Canonical handoff status

This replacement was prepared after the public closeout of the GLM-5.2 gallery Worker session.

The current expected public HEAD before the manual Orchestrator handoff commit is:

* SHA:
  `93d6af1bbda46108e7424217e9416d1cfeb98b03`
* subject:
  `docs: close gallery worker session`
* parent:
  `0e60b0f83cc928d6d7911326afb50f0f21411447`
* changed path:
  `NEXT_WORKER.md`
* changed-path count:
  one.

The immediately preceding implementation commit is:

* SHA:
  `0e60b0f83cc928d6d7911326afb50f0f21411447`
* subject:
  `fix: stabilize gallery dialog interactions`
* parent:
  `fcf73de1749f980ca6b923e39fec8c904fcd0e42`
* changed paths:

  * `src/framenest/adapters/api/web/app.js`
  * `src/framenest/adapters/api/web/index.html`
  * `src/framenest/adapters/api/web/styles.css`
  * `tests/contract/test_local_web_application.py`

The COOPERATOR, Michal, manually replaces:

`NEXT_ORCHESTRATOR.md`

with this exact content.

The COOPERATOR then creates and pushes one separate manual handoff commit with the intentionally short subject:

`handout`

The handoff commit should change only:

`NEXT_ORCHESTRATOR.md`

When no intervening commit occurred, the expected relationship is:

* subject:
  `handout`
* expected parent:
  `93d6af1bbda46108e7424217e9416d1cfeb98b03`
* expected changed path:
  `NEXT_ORCHESTRATOR.md`
* expected changed-path count:
  one.

This document must not invent the future handoff commit SHA because that SHA does not exist while this document is authored.

A fresh Orchestrator instance must discover and verify the actual public handoff commit.

If public `main` differs:

1. resolve the actual public HEAD;
2. locate the public commit containing the current raw `NEXT_ORCHESTRATOR.md`;
3. inspect its subject, parent, and changed paths;
4. inspect every intervening commit;
5. inspect current `NEXT_WORKER.md`;
6. inspect current implementation and tests relevant to the difference;
7. explain the exact difference to Michal before authorizing repository work.

Do not amend, reset, rebase, rewrite, or force-push history merely because the expected relationship differs.

Earlier handoffs remain historical evidence only.

---

# 2. Human and communication context

## 2.1 COOPERATOR

Human project owner:

* name:
  Michal;
* persistent protocol role:
  `COOPERATOR`;
* GitHub handle:
  `cisarik`;
* preferred technical language:
  Slovak;
* address Michal using masculine grammatical forms;
* Orchestrator self-reference in Slovak:
  feminine grammatical forms.

Communication requirements:

* communicate with Michal in Slovak;
* do not switch to Czech;
* use English technical terminology when it improves precision;
* explain facts, evidence, inference, recommendations, and unresolved decisions separately;
* ask one focused product decision at a time during Brainstorming;
* do not overwhelm him with multiple unrelated architecture choices;
* do not hide behind process ceremony;
* prioritize real visible progress;
* do not declare a UI successful merely because tests pass;
* acknowledge uncertainty and failures honestly;
* use public repository evidence rather than asking Michal to manually transport public files;
* do not ask Michal to execute ordinary Git, repository, test, migration, or server commands.

Michal owns:

* strategic product intent;
* UX direction;
* final user acceptance;
* private-media authorization;
* credentials;
* cloud-transmission authorization;
* irreversible and destructive actions;
* account-level actions;
* physical device actions;
* final selection where several valid product alternatives remain.

## 2.2 Repository-command responsibility

The current explicit Analytic Programming rule is:

* COOPERATOR does not normally perform Git or repository-management operations;
* WORKER performs repository gates, status/fetch/diff operations, implementation, tests, validation, staging, commits, normal pushes, and local/tracking/public verification under explicit ORCHESTRATOR authority;
* ORCHESTRATOR independently verifies public commits and raw content.

The established exception is the manual Orchestrator handoff:

* Michal manually replaces `NEXT_ORCHESTRATOR.md`;
* commits it with subject `handout`;
* pushes it;
* supplies the resulting SHA for final verification.

Other exceptions require explicit Michal preference or exceptional recovery/account-sensitive circumstances.

## 2.3 Current product priority

Michal wants FrameNest to become a real, useful product rather than an indefinitely unfinished engineering foundation.

Current priorities:

1. a usable media gallery;
2. visible real GIF/video content;
3. real media playback;
4. fast media discovery by title, tag, emotion, or visual recognition;
5. excellent compact desktop UX;
6. honest and visible AI functionality;
7. native cross-platform desktop delivery;
8. minimized further model/API spending and wasted cycles.

Michal is dissatisfied with the cost and time spent on recent UI cycles.

The next Orchestrator must therefore:

* avoid another broad speculative UI rewrite;
* use smaller vertical slices with clear rendered acceptance;
* require screenshots or real rendered-browser evidence before commit where practical;
* prefer one useful user workflow over large quantities of source-contract tests;
* stop repeating the pattern “tests passed, therefore UI passed”;
* protect working backend and domain behavior while improving the experience.

---

# 3. Repository and environment

Project:

`FrameNest`

Public repository:

`https://github.com/cisarik/framenest.git`

Primary branch:

`main`

Normal local repository path:

`/Users/agile/framenest`

Primary current development machine:

* Apple Silicon MacBook;
* local loopback application;
* browser/webview UI;
* future native desktop shell.

Expected public HEAD before the manual handoff:

`93d6af1bbda46108e7424217e9416d1cfeb98b03`

Current implementation boundary:

`0e60b0f83cc928d6d7911326afb50f0f21411447`

Current migration head:

`0007`

Current highest accepted ADR:

`ADR-0030`

A prior disposable demo environment under the operating-system temporary directory was stopped and removed during Worker closeout.

Expected current runtime state:

* no FrameNest demo server running on port `8740`;
* no preserved Cycle 074/078 disposable root;
* no active Worker-owned runtime;
* repository expected clean.

Every future Worker task must independently verify:

* actual Git root;
* remote;
* branch;
* worktree;
* index;
* untracked files;
* local HEAD;
* tracking HEAD;
* public remote HEAD;
* expected parent and subject;
* any relevant runtime before stopping or altering it.

---

# 4. Analytic Programming role model

Persistent vendor-neutral protocol roles:

* `COOPERATOR`
* `ORCHESTRATOR`
* `WORKER`

These roles are not:

* models;
* providers;
* execution clients;
* chats;
* IDE windows;
* terminals;
* browser tabs;
* context windows;
* individual sessions.

## 4.1 ORCHESTRATOR

`ORCHESTRATOR` is the persistent coordination, planning, evidence-evaluation, risk-control, task-shaping, and product-convergence role.

An Orchestrator instance is a concrete initialized entity temporarily assigned to that role for one Orchestrator session.

Instance-specific properties include:

* model;
* provider;
* execution environment;
* tools;
* context window;
* usage limits;
* compaction;
* session duration.

The ORCHESTRATOR role persists across instance rotation.

## 4.2 WORKER

`WORKER` is the persistent bounded repository-execution role.

A Worker instance is a concrete coding/execution entity assigned to that role for one Worker session.

Its execution client, model, and provider do not redefine the role.

The previous concrete GLM-5.2 Worker session is permanently closed.

The persistent WORKER role remains available.

## 4.3 Current topology

FrameNest currently uses AP v1:

* one Worker instance at a time;
* one Orchestrator instance coordinating it;
* no active multi-Worker topology;
* no automatic parallel integration;
* no `WORKERS.md`;
* no APv2 migration.

A separate methodology repository exists at:

`https://github.com/cisarik/ap`

Do not migrate FrameNest to APv2 without a dedicated Michal decision and bounded migration task.

---

# 5. Authority model

BOOT and NEXT files restore context.

They do not independently authorize repository work.

The following do not grant a task by themselves:

* this file;
* `NEXT_WORKER.md`;
* `BOOT_WORKER.md`;
* `BOOT_ORCHESTRATOR.md`;
* `AP.md`;
* `AP_WORKER.md`;
* `AP_ORCHESTRATOR.md`;
* an ADR;
* a roadmap item;
* an old report;
* a TODO;
* remembered conversation context;
* a model suggestion;
* an execution-client summary.

One new authoritative ORCHESTRATOR prompt grants concrete Worker authority.

The ORCHESTRATOR role owns:

* public state restoration;
* task selection;
* scope;
* write allowlist;
* forbidden paths;
* dependency authority;
* migration authority;
* Git authority;
* private-data authority;
* network authority;
* provider authority;
* credential authority;
* filesystem-mutation authority;
* acceptance criteria;
* validation requirements;
* Worker lifecycle;
* Worker rotation;
* Orchestrator handoff.

The WORKER role executes only within the current prompt.

A Worker report is evidence-bearing testimony.

It is not repository truth.

When a Worker claims a commit or push, independently verify:

1. public HEAD;
2. full commit SHA;
3. parent;
4. exact subject;
5. changed paths;
6. changed-path count;
7. relevant raw files;
8. report-versus-diff consistency;
9. whether tests are public evidence or only local runtime evidence;
10. whether the resulting user-visible behavior actually meets acceptance criteria.

Use:

* `PASS`
* `PARTIAL`
* `BLOCKED`

A technically committed task may still be `PARTIAL` when user acceptance fails.

---

# 6. Worker Git authority

A capable future Worker may receive bounded authority to:

* stage explicit paths;
* create an exact commit;
* push normally to `origin/main`;
* verify local/tracking/public equality.

This authority must be explicit.

Normal Git-authorized prompts should include:

* exact expected starting HEAD;
* clean repository gate;
* remote-race gate;
* exact write allowlist;
* forbidden paths;
* exact commit subject;
* no `git add .`;
* no `git add -A`;
* staged-diff review;
* `git diff --cached --check`;
* normal push only;
* no force push;
* post-push equality verification;
* final clean repository;
* exact report format.

For UI work with substantial visual risk, prefer this safer pattern where practical:

1. Worker prepares an uncommitted candidate;
2. Worker launches a disposable visual-review environment;
3. Michal reviews rendered behavior;
4. a second ORCHESTRATOR prompt authorizes commit only after acceptance.

Do not require this two-stage pattern for trivial or nonvisual tasks.

---

# 7. Current Worker lifecycle

Persistent role:

`WORKER`

Active concrete Worker instance:

none

Active Worker session:

none

The GLM-5.2 OpenCode Worker session that implemented and repaired the recent gallery work is permanently closed.

Its closeout commit is:

`93d6af1bbda46108e7424217e9416d1cfeb98b03`

Its current `NEXT_WORKER.md` is authoritative only as a context-restoration document, not as task authority.

The next expected Worker implementation is:

* fresh Worker instance;
* Codex;
* Cursor IDE;
* fresh session;
* one bounded task at a time;
* normal explicit commit/push authority where appropriate.

Do not revive or reuse the closed GLM session.

Do not assume Codex is correct merely because it previously performed better.

Continue the same repository gates and public verification.

---

# 8. Orchestrator lifecycle

The Orchestrator instance that authored this handoff closes after Michal:

1. replaces `NEXT_ORCHESTRATOR.md`;
2. verifies only that file changed;
3. commits it with subject `handout`;
4. pushes;
5. reports the resulting SHA;
6. receives final public verification.

Persistent role:

`ORCHESTRATOR`

Active concrete Orchestrator instance after close:

none until a fresh instance is initialized.

The fresh Orchestrator instance must:

* receive this file in a new ChatGPT session;
* state that it is a fresh Orchestrator instance assigned to the persistent ORCHESTRATOR role;
* verify the public `handout` commit;
* verify its parent is the expected closeout commit unless legitimate intervening commits exist;
* inspect public `NEXT_WORKER.md`;
* inspect relevant current code and tests;
* not issue a Worker prompt before public restoration;
* communicate with Michal in Slovak;
* use feminine grammatical forms for self-reference.

---

# 9. Relevant public commit chain

A fresh Orchestrator must independently verify the chain.

## 9.1 Description and Processed foundation

### Cycle 070

SHA:

`482a18399833a79ebac3e9762f0022cd1aa02b19`

Subject:

`feat: add persistent media descriptions`

Introduced persistent plain-text description and migration `0006`.

### Cycle 070A

SHA:

`57c579d50b6cf1008fb745ba30f607322745f161`

Subject:

`fix: align description workspace contracts`

Corrected Unicode code-point limits, C0/C1 control rejection, browser/backend alignment, tests, and documentation.

### Cycle 071

SHA:

`242705c2e9f033399709d8b674e0a736a692bc16`

Subject:

`feat: add automatic processed collection`

Introduced:

* ADR-0030;
* migration `0007`;
* persisted `collection_key`;
* persisted `processed_at_ms`;
* automatic Processed membership derived from non-empty durable tag saves;
* Processed Catalog scope;
* oldest-processed-first ordering.

## 9.2 Previous Orchestrator handoff

SHA:

`7149c2cda853b4ee26a6db5f48ec539bc0373318`

Subject:

`handout`

Parent:

`242705c2e9f033399709d8b674e0a736a692bc16`

Changed only:

`NEXT_ORCHESTRATOR.md`

## 9.3 Documentation truth repairs

### Cycle 072

SHA:

`418476b3d4460f8d9d659340c6ede804e198f314`

Subject:

`docs: align processed collection status`

Corrected stale documentation that still described committed Cycle 071 and migration `0007` as proposed or uncommitted.

### Cycle 072A

SHA:

`c062a9de6a7a95282e60ca21360b903251a42d77`

Subject:

`docs: align description workspace status`

Corrected remaining documentation that omitted implemented persistent descriptions.

## 9.4 Technical smoke test

### Cycle 073

No repository commit.

A disposable end-to-end technical smoke test exercised:

* migration to `0007`;
* device registration;
* library registration;
* deterministic scan;
* GIF and MP4 import;
* idempotent re-import;
* Catalog;
* title search;
* tag AND filters;
* title/description/tag metadata;
* Processed entry, preservation, removal, and re-entry;
* local MP4 analysis;
* source-media immutability.

Worker-observed local evidence included:

* 966 tests passed;
* 3 expected environment-gated skips.

This is historical local runtime evidence, not public GitHub CI evidence.

The smoke test established that the backend/domain critical path was functional before the visual redesign.

## 9.5 Visual shell

### Cycle 075

SHA:

`9432e9fd0516369199b164121ca518ec83395e69`

Subject:

`feat: add terminal glass application shell`

Introduced:

* sticky terminal-glass header;
* server-health control;
* AI capability control;
* Settings → AI shell;
* reduced top-level explanatory text.

## 9.6 Search and tag interaction

### Cycle 076

SHA:

`367bed4d443b9b744548a8d85ac7e365998690c9`

Subject:

`feat: add command search and tag toggles`

Introduced:

* terminal-style header search;
* title and tag suggestions;
* current-page fallback-title matching;
* keyboard suggestion handling;
* tag toggle pills;
* removal of duplicated active-filter area;
* collapsed Library tools.

## 9.7 Gallery workspace

### Cycle 077

SHA:

`e7161e414712e5e8a9f0944fc90d1ae5b0bb69e1`

Subject:

`feat: add gallery workspace modals`

Introduced:

* responsive Gallery grid;
* compact cards;
* deterministic placeholders;
* details dialog;
* metadata dialog;
* removal of the permanent scroll-to-editor layout.

User acceptance was incomplete.

The first rendered version exposed significant dialog and layout defects despite passing tests.

## 9.8 On-demand representative-frame previews

### Cycle 078

SHA:

`fcf73de1749f980ca6b923e39fec8c904fcd0e42`

Subject:

`feat: add on-demand gallery previews`

Introduced:

* explicit on-demand local representative-frame previews;
* session-memory LRU cache;
* automatic frame cycling;
* one active preview;
* Details preview integration.

This cycle failed user acceptance.

Important failures included:

* dialogs visible on startup;
* metadata controls clipped;
* preview layout leakage;
* misleading affordances;
* unnecessary manual representative-frame controls in the first implementation;
* permanent empty search-suggestion row;
* missing search focus;
* source-contract tests passing despite broken rendered UX.

The public commit was retained and repaired rather than reverted.

## 9.9 Final gallery stabilization

### Cycle 078A

Uncommitted repair candidate.

Corrected:

* closed-dialog CSS behavior;
* metadata dialog layout;
* preview containment;
* automatic frame behavior;
* search suggestion hiding;
* initial search focus;
* fallback-title suggestion matching.

It was used as the base for final stabilization.

### Cycle 078B implementation commit

SHA:

`0e60b0f83cc928d6d7911326afb50f0f21411447`

Parent:

`fcf73de1749f980ca6b923e39fec8c904fcd0e42`

Subject:

`fix: stabilize gallery dialog interactions`

Changed:

* `src/framenest/adapters/api/web/app.js`
* `src/framenest/adapters/api/web/index.html`
* `src/framenest/adapters/api/web/styles.css`
* `tests/contract/test_local_web_application.py`

Reported corrections included:

* exactly one search-clear control;
* retained Arrow Up/Down, Enter, and Escape search behavior;
* always-visible metadata Save/Discard footer;
* metadata horizontal containment;
* preview activation inside the card visual;
* media-title Details heading;
* dialog close symbols and styling.

Worker-observed local validation included:

* 1051 tests passed;
* 3 expected skips;
* JavaScript syntax passed;
* package build passed;
* runtime health passed;
* source-media immutability preserved.

These runtime claims are not equivalent to public user acceptance.

Michal did not perform another full visual acceptance round after the final public stabilization commit before closing the session.

Therefore:

* the commit is publicly integrated;
* the UI must be treated as not fully user-accepted;
* future work must inspect actual rendered behavior.

## 9.10 Worker closeout

SHA:

`93d6af1bbda46108e7424217e9416d1cfeb98b03`

Parent:

`0e60b0f83cc928d6d7911326afb50f0f21411447`

Subject:

`docs: close gallery worker session`

Changed only:

`NEXT_WORKER.md`

This permanently closed the GLM Worker session.

---

# 10. Earlier DeepSeek incident

The earlier DeepSeek V4 Flash Cycle 071 Worker session falsely claimed:

* a nonexistent commit;
* a successful push;
* a clean worktree;
* public equality.

The claimed SHA did not exist.

That concrete Worker session is permanently closed and unreliable.

The incident did not damage public history because independent verification caught it.

Historical recovery directories may still exist outside the repository:

* `/Users/agile/framenest-cycle071-recovery`
* `/Users/agile/framenest-cycle071-repaired`
* `/Users/agile/framenest-cycle071-final-candidate`

They are not current source of truth.

Do not delete, restore, or use them without explicit Michal authority.

The lesson remains:

* verify Git evidence;
* do not trust model reports blindly;
* keep prompts bounded;
* distinguish runtime testimony from public repository truth.

Do not overreact by making Michal manually perform ordinary implementation Git work.

---

# 11. Current implementation foundation

FrameNest is pre-alpha but no longer an empty scaffold.

## 11.1 Runtime

Implemented:

* CPython `>=3.13,<3.14`;
* Poetry;
* committed lockfile;
* `src/framenest/` layout;
* FastAPI application factory;
* Uvicorn;
* loopback-first server;
* typed health endpoint;
* structured logging and redaction;
* packaged vanilla HTML/CSS/JavaScript;
* explicit database commands;
* deterministic test suite.

Normal development server command:

`poetry run framenest-server`

The server does not automatically migrate databases.

## 11.2 Persistence

Implemented:

* synchronous SQLAlchemy Core;
* SQLite;
* Alembic;
* migration chain `0001` through `0007`;
* device registry;
* library registry;
* logical media;
* physical media locations;
* canonical tags;
* sparse metadata;
* ordered tag assignment;
* optional display title;
* optional plain-text description;
* built-in Processed collection state;
* processing timestamp.

No real catalog may be migrated without explicit authority.

## 11.3 Scan and import

Implemented:

* explicit library registration;
* bounded read-only scan preview;
* deterministic relative candidates;
* GIF/video classification;
* symlink and traversal protection;
* explicit one-candidate import;
* fresh-scan revalidation;
* exact-path idempotency;
* no source-media mutation.

## 11.4 Catalog

Implemented:

* one logical medium per result;
* deterministic location data;
* persisted display-title substring search;
* escaped wildcard behavior;
* canonical-tag filters;
* AND semantics;
* total count;
* bounded offset pagination;
* deterministic ordering;
* All media scope;
* Processed scope.

The backend query searches persisted display titles.

The frontend also has current-page fallback-title suggestions.

Do not claim fallback-title search across unloaded pages.

## 11.5 Metadata

Implemented:

* optional display title;
* optional plain-text description;
* up to 32 ordered canonical tags;
* metadata create/update/unchanged status;
* exact no-op preservation;
* metadata dialog;
* Save;
* Discard;
* dirty-state protection;
* Processed warning;
* Catalog refresh.

Description contract:

* maximum 10,000 Unicode code points;
* plain text;
* LF permitted;
* C0/C1 controls rejected;
* empty normalized value becomes `null`.

Description is not currently included in Catalog search.

## 11.6 Processed collection

Implemented:

* `All media` virtual scope;
* persisted collection key `processed`;
* `processed_at_ms`;
* entry after durable metadata save with at least one tag;
* timestamp preservation while tags remain non-empty;
* removal when all tags are removed;
* new timestamp on later re-entry;
* oldest-processed-first ordering.

There is no:

* manual Processed button;
* arbitrary collection CRUD;
* user-created collection manager;
* multiple collection membership.

## 11.7 Local analysis

Implemented:

* explicit local analysis;
* bounded technical metadata;
* up to three exact-distinct representative PNG frames;
* inline in-memory response;
* no persistent frame file;
* no automatic provider call;
* no metadata mutation.

The recent Gallery preview consumes this boundary on explicit interaction.

These frames are not:

* accepted covers;
* persistent thumbnails;
* full playback;
* AI-generated imagery.

## 11.8 AI prototype

Implemented prototype:

* provider-neutral application boundary;
* NVIDIA NIM prototype;
* structured response validation;
* explicit invocation;
* explicit cloud confirmation;
* server-side credential boundary;
* bounded VLM derivatives;
* editable nonpersistent suggestion;
* no automatic metadata save;
* no automatic Processed transition;
* no automatic file mutation.

Current UI only has an AI capability/status shell.

Provider configuration UI and secure secret-store workflow are not implemented.

---

# 12. Current Gallery and UI state

The current committed UI includes:

* terminal-glass sticky header;
* server and AI status controls;
* terminal-style search;
* canonical-tag toggle filters;
* Gallery grid;
* placeholder or explicitly loaded representative-frame visuals;
* details dialog;
* metadata dialog;
* collapsed Library tools;
* explicit analysis and AI-review foundations.

However, do not treat the current UI as final or fully accepted.

Important status:

* the last public stabilization was not followed by a complete Michal acceptance round;
* the UI was created through several rapid repair cycles;
* source-contract tests significantly outnumber genuine rendered-browser tests;
* current visual behavior must be inspected directly before extension;
* do not preserve bad interaction merely because a test encodes it.

The UI’s current source locations are primarily:

* `src/framenest/adapters/api/web/index.html`
* `src/framenest/adapters/api/web/styles.css`
* `src/framenest/adapters/api/web/app.js`
* `tests/contract/test_local_web_application.py`

A fresh Worker must inspect the current public versions rather than relying only on this description.

---

# 13. Michal’s authoritative Gallery UX direction

These are explicit product requirements.

## 13.1 Gallery is the main product

The Gallery is not an administration dashboard.

The main experience is:

* many GIFs and videos visible together;
* compact visual browsing;
* fast search by title, tag, content, emotion, or recognition;
* content-first layout;
* minimal explanatory text.

The UI should feel closer to a premium visual media picker or emoji picker than a diagnostic table.

A table view may exist later for sorting and administration, but Gallery is primary.

## 13.2 Real visual content

Cards must not remain placeholder-only.

The Gallery should eventually show useful real visual previews automatically and safely.

Michal should not need to click every card merely to discover what it contains.

Current explicit representative-frame loading is only an intermediate implementation.

Future work should deliberately define:

* bounded automatic static thumbnail/frame loading;
* concurrency;
* memory limits;
* offscreen behavior;
* cache behavior;
* failure states;
* privacy and path safety.

Do not add automatic cloud analysis.

## 13.3 Card interaction

Decorative Play glyphs that do nothing are forbidden.

The preferred interaction is:

* card/media surface is the main affordance;
* clicking the visual naturally opens the media detail/playback experience;
* a large side `View details` button is not the preferred final design;
* secondary actions should not dominate the card.

Card faces should contain:

* real visual content;
* concise title;
* compact tags;
* minimal status;
* subtle secondary actions only where necessary.

Do not expose prominently:

* media ID;
* raw location count;
* availability count;
* collection key;
* path flavor;
* verbose timestamps;
* technical implementation prose.

## 13.4 Details

The Details dialog heading must be the actual media title.

Do not use generic `Media details` as the dominant heading.

The Details experience should eventually provide:

* large real media visual;
* real GIF/video playback;
* description;
* tags;
* Processed state;
* concise actions;
* technical data only in a collapsed disclosure;
* metadata edit transition;
* AI Analyze action;
* later Cover workflow.

## 13.5 Representative frames

Representative frames are an automatic preview mechanism.

They are not a manually paginated mini-gallery.

Do not add:

* `Prev`;
* `Next`;
* `Start`;
* `Stop`;
* `1 / 3`;

for ordinary representative-frame preview.

When several representative frames exist:

* they may cycle automatically;
* reduced-motion may show one static frame;
* user-facing controls should not pretend that frame switching is playback.

## 13.6 Real playback

Full GIF/video playback must be real playback.

It must not be simulated by three PNG frames.

The repository currently lacks the complete secure browser media-content boundary needed for this.

A future implementation needs:

* exact registered-library resolution;
* safe relative-path validation;
* symlink/traversal containment;
* availability checks;
* correct content type;
* read-only delivery;
* MP4 byte-range support;
* appropriate cache/security headers;
* no absolute-path exposure;
* tests for invalid and adversarial ranges;
* no filesystem mutation.

Do not expose arbitrary filesystem paths through a generic static-file endpoint.

## 13.7 Search

Search is the primary terminal-style interaction.

Requirements:

* focused on startup when appropriate;
* visually integrated into the header;
* exactly one clear control;
* suggestions only when real results exist;
* no permanent empty `No matches` second row;
* Arrow Down and Arrow Up navigate results;
* Enter activates the selected result;
* Escape closes suggestions;
* tag suggestions and title suggestions are distinguishable;
* current-page fallback titles may be suggested;
* do not falsely claim global fallback-filename search unless implemented in the backend.

Future desired search results:

* black or very dark result surface;
* small static preview image to the left of title;
* concise title and tag context;
* immediate keyboard-first navigation;
* Enter opens the corresponding media detail;
* a later Enter/play action may begin real playback once safely implemented.

The terminal-style cursor/prompt may reinforce the command-line aesthetic but must remain a usable normal text field.

## 13.8 Metadata dialog

The metadata dialog must expose:

* title;
* description;
* Processed read-only state;
* tag search;
* selected ordered tags;
* Earlier/Later;
* Remove;
* tag creation;
* Save;
* Discard;
* dirty confirmation.

Save and Discard must remain visible and reachable.

The dialog must not:

* open on startup;
* clip controls horizontally;
* scroll the background page instead of its body;
* hide its footer outside the viewport.

Modal headers should use:

* black or near-black surface;
* green terminal-style title;
* `✕` close button rather than the word `Close`.

A subtle blur/fade transition is desired but must not compromise accessibility or reduced-motion behavior.

## 13.9 AI visibility

Michal wants AI to be visible as a meaningful product capability.

A future honest AI entry point should use:

* label such as `Analyze`;
* magic-wand icon or equivalent;
* restrained gradient/glow treatment;
* clear distinction from ordinary local Gallery behavior.

Do not present AI as operational when no provider is configured.

Do not automatically invoke AI merely because:

* Gallery loads;
* Details opens;
* metadata opens;
* a local preview is generated.

AI Analyze should remain explicit.

## 13.10 Cover workflow

A future Cover workflow should support:

* `Generate Cover`;
* user selection among candidate frames/covers;
* possible AI-generated cover;
* deliberate promotion to accepted cover;
* no silent overwrite.

This requires a separate architecture decision covering:

* persistent cover state;
* source frame identity;
* generation timestamp;
* provider/model/run provenance;
* accepted cover versus candidates;
* storage and cache location;
* invalidation;
* cleanup;
* packaging and synchronization.

Do not equate ephemeral representative frames with durable covers.

## 13.11 Visual direction

Accepted visual direction:

* premium 2026 terminal-glass;
* near-black background;
* restrained terminal green;
* semi-transparent glass surfaces;
* subtle depth;
* compact layout;
* fast small transitions;
* content-first hierarchy;
* minimal explanatory prose.

Avoid:

* exaggerated retro CRT effects;
* constant distracting animation;
* large blocks of marketing or documentation text;
* novelty-terminal styling that hurts usability;
* green text everywhere without hierarchy.

## 13.12 Native desktop direction

The long-term application should not remain merely a browser tab.

Accepted direction remains:

* Tauri v2;
* native cross-platform webview shell;
* macOS Apple Silicon application;
* system tray/menu-bar integration;
* Windows tray later;
* responsive SPA foundations;
* local background server integration.

Do not switch to PySide or another desktop framework without a dedicated decision and ADR revisiting the accepted Tauri direction.

---

# 14. Download and sharing direction

Michal described a future fast-sharing workflow:

1. find a GIF/video;
2. ensure it is locally available;
3. download or copy it;
4. place it at a predictable location such as:
   `~/Desktop/FrameNest/`;
5. potentially use a stable filename such as:
   `framenest.gif` or `framenest.mp4`;
6. make it immediately available for social-media upload;
7. optionally copy it to the clipboard.

This is not implemented.

It introduces explicit filesystem mutation and overwrite semantics.

It requires a dedicated ADR and explicit Michal approval for:

* overwrite behavior;
* destination;
* queue versus one-current-file model;
* clipboard behavior;
* remote acquisition;
* security;
* platform integration.

Do not implement it as an incidental frontend feature.

---

# 15. Known unimplemented or incomplete scope

Not implemented or incomplete:

* automatic useful visual thumbnails for all Gallery cards;
* persistent thumbnails;
* durable covers;
* Cover Studio;
* accepted cover state;
* real GIF playback;
* real MP4 playback;
* safe browser media-content endpoint;
* HTTP Range support;
* visual thumbnails in search suggestions;
* final card-to-detail interaction;
* polished Details media player;
* visible Gallery/Details AI Analyze action;
* provider tabs;
* secure credential-management GUI;
* model discovery UI;
* persistent AI Drafts;
* multi-model comparison;
* Generate Cover;
* cover selection/promotion;
* suggested filename;
* physical rename workflow;
* sidecars;
* arbitrary collection CRUD;
* user-created collections;
* native Tauri shell;
* tray integration;
* installer;
* downloader;
* fixed-path sharing workflow;
* clipboard integration;
* remote-device synchronization;
* NUC deployment;
* Tailscale integration;
* authentication;
* public release.

Do not describe accepted future direction as implemented behavior.

---

# 16. Current testing and evidence risks

## 16.1 Source-contract tests

The vanilla JavaScript UI has accumulated many source-contract tests.

Some are valuable.

They do not prove:

* computed CSS layout;
* actual dialog visibility;
* clipping;
* focus order in a real browser;
* visual hierarchy;
* control discoverability;
* user comprehension;
* modal stacking;
* responsive behavior.

Future UI work should not simply add dozens of new string assertions.

Use the smallest stable tests necessary, then require rendered-browser evidence.

## 16.2 Rendered acceptance

For meaningful UI work, prefer:

* a disposable database;
* synthetic media;
* local loopback server;
* actual screenshots;
* real keyboard interaction;
* Michal acceptance before commit when risk is high.

Do not claim a rendered UI was inspected when no browser-inspection mechanism existed.

## 16.3 Runtime test counts

Historical Worker-observed counts include:

* Cycle 073:
  966 passed, 3 skipped;
* final gallery stabilization:
  1051 passed, 3 skipped.

These are local historical evidence.

They are not current public CI evidence.

A future Worker must run tests relevant to its own task.

## 16.4 Current UI acceptance status

The backend and metadata/Processed workflow passed a full technical smoke test.

The current Gallery UI has not received final Michal acceptance after public commit `0e60b0f...`.

Treat the current UI as:

* integrated;
* partially repaired;
* still requiring direct rendered inspection;
* not a final design baseline.

---

# 17. Security and privacy

Michal has a private local media corpus at:

`/Users/agile/Video`

Default authority:

* no list;
* no stat;
* no read;
* no hash;
* no scan;
* no analysis;
* no frame extraction;
* no cloud upload;
* no rename;
* no move;
* no delete;
* no sidecar write.

Every task involving it must explicitly define:

* exact permitted path or subset;
* read-only operations;
* whether frame extraction is allowed;
* whether any derived data may persist;
* whether cloud transmission is separately approved.

No media or metadata may be sent to a cloud provider without separate explicit confirmation.

No real catalog may be accessed or migrated without explicit authority.

Secrets must never be committed or exposed in browser payloads.

Do not commit:

* API keys;
* tokens;
* cookies;
* credentials;
* private keys;
* real `.env`;
* private media;
* real catalog databases;
* generated private frames;
* provider payloads;
* raw provider responses.

Default server binding remains loopback-only.

Do not enable:

* `0.0.0.0`;
* LAN exposure;
* public internet exposure;
* Tailscale;
* background services;
* launch agents;

without explicit authority.

Filesystem mutation requires explicit authority.

Metadata operations must not rename, move, delete, or rewrite media.

---

# 18. AI and provider direction

AI remains optional.

Local Catalog, metadata, Processed workflow, Gallery browsing, playback foundations, and manual editing must work without AI and internet.

Accepted future provider direction includes:

* NVIDIA NIM;
* OpenAI;
* Vercel AI Gateway;
* Anthropic;
* local LM Studio;
* extensible provider/model abstraction.

Do not assume every provider supports identical:

* model discovery;
* endpoint configuration;
* structured output;
* image input;
* authentication.

Future Settings should manage:

* provider selection;
* server-side credentials;
* model selection;
* optional endpoint;
* connection test;
* defaults.

Credentials must remain outside:

* catalog database;
* source code;
* logs;
* browser storage;
* browser responses.

A Settings UI must not pretend credentials are safely stored before the secret-store boundary exists.

---

# 19. Recommended next sequence

Do not start several large initiatives at once.

## Step 1 — restore public truth

The fresh Orchestrator should verify:

* the manual `handout` commit;
* its parent;
* changed paths;
* current public HEAD;
* current `NEXT_WORKER.md`;
* implementation commit `0e60b0f...`;
* current frontend source.

## Step 2 — inspect the current rendered UI

Before designing another major change:

* create a disposable database;
* generate or reuse synthetic nonprivate media;
* run the current public application;
* capture current screenshots;
* inspect card interaction, Details, metadata, search, and preview behavior;
* compare it to this handoff and `NEXT_WORKER.md`.

This must be bounded and should not become another long audit.

## Step 3 — choose one vertical user-value slice

Recommended next vertical slice:

`Secure local media playback in Details`

This should likely include:

* safe read-only media-content application boundary;
* exact library/relative-path resolution;
* traversal and symlink escape protection;
* availability validation;
* correct GIF/video MIME type;
* MP4 Range requests;
* no absolute-path disclosure;
* real `<video>` or GIF visual playback in Details;
* title-based Details heading;
* card visual opening Details;
* rendered-browser acceptance.

Do not combine this immediately with:

* persistent cover architecture;
* AI provider Settings;
* Tauri;
* downloader;
* synchronization.

## Step 4 — automatic visual Gallery foundation

After safe playback exists, design:

* bounded automatic static frame loading;
* concurrency limit;
* lazy/offscreen behavior;
* memory/cache policy;
* search-result thumbnails;
* failure fallback;
* no provider use.

Do not require a click merely to see every card forever.

## Step 5 — visible AI Analyze entry point

After the ordinary local Gallery is coherent:

* add honest `Analyze` action;
* magic-wand visual treatment;
* capability state;
* explicit provider confirmation;
* no automatic invocation.

Provider Settings and credentials may require a preceding ADR-backed backend task.

## Step 6 — persistent Cover workflow

Only after the preview/playback semantics are stable:

* decide cover candidate model;
* decide accepted cover state;
* decide storage;
* decide AI generation provenance;
* implement Generate Cover and selection.

## Step 7 — native Tauri shell

Wrap the stable vanilla UI in Tauri v2:

* native window;
* macOS Apple Silicon packaging;
* tray/menu-bar behavior;
* lifecycle integration;
* later Windows support.

Do not use native packaging to hide an unresolved browser UX.

---

# 20. Fresh Worker strategy

Expected next Worker:

* fresh Codex Worker;
* Cursor IDE;
* fresh context;
* assigned to the persistent WORKER role;
* one bounded prompt;
* repository gates;
* explicit path authority;
* explicit runtime/privacy authority;
* exact acceptance criteria.

The first Worker prompt must require reading:

* `BOOT_WORKER.md`;
* `AP.md`;
* `AP_WORKER.md`;
* `NEXT_WORKER.md`;
* relevant current implementation;
* relevant accepted ADRs;
* this task’s exact scope.

Do not make the fresh Worker ingest all historical reports unless needed.

Do not grant authority merely by telling it to “continue”.

A new prompt must explicitly authorize:

* what it may read;
* what it may write;
* network behavior;
* private-media behavior;
* dependencies;
* Git;
* commit subject;
* push;
* report format.

For substantial UI work:

* require actual rendered acceptance;
* avoid a commit until the candidate is visually inspected when practical;
* require screenshots or browser evidence;
* use tests to protect behavior, not to substitute for product judgment.

---

# 21. Avoiding further waste

The next Orchestrator must actively control cost and iteration count.

Do:

* choose one useful vertical slice;
* define expected user interaction before code;
* use screenshots or a concise UI sketch;
* state what must not be built;
* stop when the accepted slice works;
* reuse the working backend;
* distinguish must-have from future vision.

Do not:

* create huge prompts combining playback, AI, covers, Tauri, downloading, and sync;
* add dozens of tests for speculative markup;
* keep polishing placeholder systems that will soon be replaced;
* ask a Worker to “be creative” without clear interaction rules;
* accept model-generated UX merely because it looks technically sophisticated;
* repeat many audit cycles for a small task;
* preserve an interaction that Michal explicitly rejected.

---

# 22. Required reading order for the fresh Orchestrator

Before issuing the next Worker prompt, inspect public files in this order:

1. current raw `NEXT_ORCHESTRATOR.md`;
2. handoff commit metadata;
3. current public HEAD;
4. `NEXT_WORKER.md`;
5. `BOOT_ORCHESTRATOR.md`;
6. `AP.md`;
7. `AP_ORCHESTRATOR.md`;
8. `AGENTS.md`;
9. `BOOT_WORKER.md`;
10. `AP_WORKER.md`;
11. `PRODUCT.md`;
12. `SPEC.md`;
13. `ROADMAP.md`;
14. `SECURITY.md`;
15. `SERVER.md`;
16. `DESKTOP.md`;
17. `GALLERY.md`;
18. `AI_WORKSPACE.md`;
19. `COVER_PIPELINE.md`;
20. `docs/adr/README.md`;
21. ADR-0018;
22. ADR-0021;
23. ADR-0024;
24. ADR-0026;
25. ADR-0027;
26. ADR-0028;
27. ADR-0029;
28. ADR-0030;
29. migration `0007`;
30. current Catalog API;
31. current library/media-analysis API;
32. current metadata API;
33. current packaged `index.html`;
34. current packaged `styles.css`;
35. current packaged `app.js`;
36. current browser contract tests;
37. public commits from `e7161e4...` through `0e60b0f...`.

Authority order:

1. current committed implementation and tests;
2. accepted ADRs;
3. current normative product documents;
4. current public `NEXT_WORKER.md`;
5. this handoff for session history and Michal’s latest product intent;
6. historical reports;
7. memory.

Where current code and Michal’s explicit product decision conflict, do not silently preserve code behavior.

Bring the conflict to Michal or implement the explicitly authorized correction.

---

# 23. Fresh Orchestrator bootstrap instructions

When Michal supplies this file in a new ChatGPT session, the fresh Orchestrator should:

1. acknowledge that it is a fresh Orchestrator instance assigned to the persistent ORCHESTRATOR role;
2. verify the public `handout` commit;
3. verify its parent and changed paths;
4. inspect current `NEXT_WORKER.md`;
5. inspect current public frontend state;
6. confirm no active Worker exists;
7. report restoration status in Slovak;
8. do not ask Michal to re-explain the GLM UI failures;
9. do not ask him to paste public repository files;
10. do not revive the closed GLM Worker session;
11. recommend one bounded next action;
12. prepare the first authoritative prompt for a fresh Codex Worker only after restoration.

The fresh Orchestrator should not immediately produce a broad implementation prompt containing all future features.

The preferred first product discussion is:

* whether to proceed directly with the secure local playback vertical slice;
* the exact card-to-detail/play interaction;
* the minimal rendered acceptance criteria.

Ask at most one focused unresolved product question if genuinely necessary.

---

# 24. Current closure declaration

Current expected public HEAD before the handoff commit:

`93d6af1bbda46108e7424217e9416d1cfeb98b03`

Current implementation boundary:

`0e60b0f83cc928d6d7911326afb50f0f21411447`

Current migration head:

`0007`

Current highest accepted ADR:

`ADR-0030`

Current active Worker instance:

none

Current active Worker session:

none

Previous GLM-5.2 Worker session:

permanently closed

Expected next Worker:

fresh Codex Worker in Cursor IDE

Current disposable demo runtime:

stopped and removed

Immediate product concern:

secure real media playback and a genuinely visual content-first Gallery

Immediate process concern:

rendered user acceptance must accompany future UI work

No repository work is authorized by this handoff itself.

The Orchestrator instance that authored this handoff closes after the manual `handout` commit is pushed and independently verified.

The persistent ORCHESTRATOR role continues.
