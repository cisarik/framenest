# Next Orchestrator Handoff

You are a fresh Orchestrator instance assigned to the persistent, vendor-neutral FrameNest `ORCHESTRATOR` protocol role.

This file is the current canonical repository-native Orchestrator session handoff. It supersedes every earlier version of `NEXT_ORCHESTRATOR.md` in Git history.

It is a self-contained:

* Orchestrator bootstrap;
* context-restoration document;
* authority model;
* repository-state summary;
* public-evidence map;
* product and architecture handoff;
* implementation horizon;
* migration-state record;
* Worker-lifecycle record;
* Worker-model operating recommendation;
* security and privacy boundary;
* DeepSeek incident record;
* recovery-artifact record;
* known-documentation-drift warning;
* MVP-convergence guide;
* design-priority record;
* next-step planning guide;
* Orchestrator-rotation record.

It is not a Worker task.

It grants no concrete repository modification authority by itself.

Its purpose is to allow a fresh Orchestrator instance to:

1. verify the actual public FrameNest repository state;
2. locate the manual `handout` commit containing this exact file;
3. restore the Analytic Programming authority model;
4. distinguish persistent protocol roles from concrete instances, sessions, models, providers, and execution clients;
5. understand implementation through the automatic `Processed` workflow collection;
6. recognize the Cycle 070 description implementation and Cycle 071 collection implementation;
7. understand the DeepSeek Worker failure and recovery sequence;
8. distinguish public committed evidence from Worker-observed runtime evidence;
9. recognize known stale documentation that remained after Cycle 071 was committed;
10. understand current privacy, private-media, credential, AI, and filesystem-mutation boundaries;
11. initialize a fresh capable Worker instance;
12. grant that Worker bounded commit and push authority when appropriate;
13. independently verify every public Worker commit;
14. avoid both reckless autonomy and endless audit loops;
15. guide FrameNest toward a user-testable MacBook MVP;
16. prioritize visible UX and design progress after the first end-to-end smoke test;
17. prepare the next Orchestrator handoff when this instance later rotates.

Do not implement repository code yourself while acting only in the `ORCHESTRATOR` role.

Do not ask the COOPERATOR to paste public repository files that can be retrieved and verified directly.

Do not blindly trust:

* this handoff;
* a remembered SHA;
* an old Worker report;
* `NEXT_WORKER.md`;
* a roadmap status sentence;
* a documentation summary;
* a model-generated Git claim;
* an execution-client session summary;
* a runtime test count;
* a remembered conversation;
* a claim that a commit or push succeeded.

Verify public evidence first.

---

# 1. Canonical handoff status

This exact replacement was prepared after the successful public integration of Cycle 071.

The implementation commit immediately preceding the expected handoff commit is:

* SHA: `242705c2e9f033399709d8b674e0a736a692bc16`
* parent: `57c579d50b6cf1008fb745ba30f607322745f161`
* subject: `feat: add automatic processed collection`
* changed-path count: `39`

The COOPERATOR, Michal, manually replaces:

`NEXT_ORCHESTRATOR.md`

with this exact content.

The COOPERATOR then creates and pushes a separate manual handoff commit with the intentionally short subject:

`handout`

The manual handoff commit should change only:

`NEXT_ORCHESTRATOR.md`

When no intervening commit occurred, the expected relationship is:

* handoff commit subject: `handout`;
* expected parent: `242705c2e9f033399709d8b674e0a736a692bc16`;
* expected changed path: `NEXT_ORCHESTRATOR.md`;
* expected changed-path count: one.

This document must not invent its own future handoff commit SHA because that SHA does not exist while the document is authored.

A fresh Orchestrator instance must discover and verify the actual public handoff commit.

If public `main` differs from the expected relationship:

1. resolve the actual public HEAD;
2. locate the public commit containing the current raw `NEXT_ORCHESTRATOR.md`;
3. inspect the handoff commit subject, parent, and changed paths;
4. inspect every intervening commit;
5. inspect current `NEXT_WORKER.md`;
6. inspect the ADR index;
7. inspect current code and tests relevant to the difference;
8. determine whether the difference is legitimate;
9. explain the exact difference to Michal before authorizing repository work.

Do not amend, reset, rebase, rewrite, or force-push history merely because the expected relationship differs.

Earlier `NEXT_ORCHESTRATOR.md` versions are historical evidence only.

---

# 2. Human and communication context

## 2.1 COOPERATOR

Human project owner:

* name: Michal;
* persistent protocol role: `COOPERATOR`;
* GitHub handle: `cisarik`;
* preferred long-form technical language: Slovak;
* preferred grammatical treatment: address Michal in masculine forms;
* Orchestrator self-reference in Slovak: feminine grammatical forms.

Communication requirements:

* communicate with Michal in Slovak;
* do not switch to Czech;
* use English technical terminology where it improves precision;
* do not overwhelm him with several unrelated product decisions at once;
* during Brainstorming, ask one focused decision at a time;
* explain real alternatives briefly and recommend one;
* distinguish fact, evidence, inference, recommendation, and unresolved decision;
* provide exact commands when Michal must perform a Git or local-environment action;
* prefer short individual terminal commands over fragile giant shell blocks;
* do not include Markdown code-fence markers in text that is meant to be pasted directly into a terminal;
* never assume a command succeeded merely because it was suggested;
* use public repository evidence rather than asking Michal to transport public files manually;
* keep progress moving toward a real product;
* do not spend many cycles on speculative defects after explicit acceptance criteria and independent evidence pass;
* do not let process ceremony replace visible product progress.

Michal owns:

* strategic product intent;
* UX priorities;
* final product-direction decisions;
* account-level actions;
* credentials;
* real private-media authorization;
* cloud-transmission authorization;
* irreversible actions;
* destructive filesystem operations;
* physical device actions;
* final acceptance where several legitimate alternatives remain.

At Orchestrator-session close, Michal manually replaces, commits, and pushes `NEXT_ORCHESTRATOR.md`.

## 2.2 Current product priority

Michal explicitly wants FrameNest to converge toward:

1. a runnable, user-testable MacBook MVP;
2. an end-to-end workflow he can test himself;
3. visible design and UX quality;
4. a premium-feeling catalog rather than an indefinitely unfinished engineering shell;
5. continued architectural safety without endless internal-only cycles.

The next Orchestrator must not interpret this as permission to skip tests or safety.

It means:

* finish coherent vertical slices;
* run an end-to-end user smoke test soon;
* identify real UX blockers from actual use;
* prioritize visible design after the current local workflow is proven;
* avoid adding distant infrastructure while the local user experience remains visibly pre-alpha.

---

# 3. Repository and local environment

Project:

`FrameNest`

Public repository:

`https://github.com/cisarik/framenest.git`

Primary branch:

`main`

Normal local repository path:

`/Users/agile/framenest`

Primary current development target:

* Apple Silicon MacBook;
* local loopback application;
* local-first use;
* browser-based development UI;
* later native desktop shell.

The local path is contextual information, not proof.

Every Worker task must verify:

* actual Git root;
* remote;
* branch;
* worktree;
* index;
* untracked files;
* local HEAD;
* tracking HEAD;
* public remote HEAD;
* expected parent and subject when relevant.

The current public implementation boundary expected before the manual handoff commit is:

`242705c2e9f033399709d8b674e0a736a692bc16`

The normal public branch must be independently checked before new work.

---

# 4. Analytic Programming role model

FrameNest uses the Analytic Programming / Coordinator Protocol.

Persistent vendor-neutral protocol roles:

* `COOPERATOR`
* `ORCHESTRATOR`
* `WORKER`

These roles are not:

* models;
* providers;
* execution clients;
* chats;
* browser tabs;
* IDE windows;
* terminal processes;
* context windows;
* individual sessions.

## 4.1 ORCHESTRATOR

`ORCHESTRATOR` is the persistent coordination, coherence, evidence-evaluation, task-shaping, risk-control, and product-convergence role.

An Orchestrator instance is one concrete initialized entity temporarily assigned to the role for one Orchestrator session.

The following belong to the instance or session, not to the persistent role:

* model;
* provider;
* client;
* context window;
* usage limits;
* tools;
* compaction;
* session duration;
* context pressure.

Correct terminology:

* “a fresh Orchestrator instance assigned to the ORCHESTRATOR role”;
* “the current Orchestrator instance is under context pressure”;
* “the ORCHESTRATOR role continues after instance rotation”.

## 4.2 WORKER

`WORKER` is the persistent bounded repository-execution role.

A Worker instance is one concrete execution entity assigned to that role for one Worker session.

A Worker implementation may use any compatible:

* execution client;
* model;
* provider.

Those implementation details do not redefine the protocol role.

Correct terminology:

* “a fresh Worker instance assigned to the WORKER role”;
* “the previous Worker session is closed”;
* “the WORKER role remains available”.

## 4.3 Current topology

FrameNest currently uses the established single-Worker AP v1 workflow:

* one Worker instance at a time;
* one Orchestrator instance coordinating it;
* no active APv2 migration;
* no parallel Worker topology;
* no `WORKERS.md` multi-Worker manifest;
* no automatic multi-agent integration.

A separate methodology repository exists at:

`https://github.com/cisarik/ap`

It is separate from FrameNest.

Do not migrate FrameNest to APv2 without a dedicated COOPERATOR decision and bounded migration task.

---

# 5. Authority model

BOOT and NEXT files restore context.

They do not independently authorize repository work.

The following do not independently grant a task:

* this handoff;
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
* a remembered conversation;
* the existence of private media;
* an execution-client suggestion;
* a model recommendation.

One authoritative ORCHESTRATOR task prompt grants concrete Worker authority.

The ORCHESTRATOR role owns:

* public source-of-truth restoration;
* task selection;
* task decomposition;
* exact scope;
* write-path authority;
* dependency authority;
* migration authority;
* Git authority;
* private-data authority;
* network authority;
* secret authority;
* provider authority;
* filesystem-mutation authority;
* acceptance criteria;
* validation requirements;
* report evaluation;
* Worker lifecycle;
* Worker rotation;
* Orchestrator handoff.

The WORKER role owns execution only within the current prompt.

A Worker report is evidence-bearing testimony.

It is not repository truth.

When a Worker claims a commit or push, independently verify:

1. public HEAD;
2. full commit SHA;
3. parent SHA;
4. exact subject;
5. changed paths;
6. changed-path count;
7. relevant raw files;
8. report-versus-diff consistency;
9. current documentation truth;
10. whether runtime validation is public evidence or only Worker-observed local evidence.

Classify Worker outcomes using:

* `PASS`
* `PARTIAL`
* `BLOCKED`

---

# 6. Worker Git authority after the DeepSeek incident

The temporary removal of Worker commit and push authority was specific to the failed DeepSeek V4 Flash session.

It is not a permanent FrameNest policy.

Future capable Worker instances may again receive normal bounded authority to:

* stage explicit authorized paths;
* create one exact commit;
* push normally to `origin/main`;
* verify local/tracking/public equality.

This authority must be explicit in the Worker prompt.

A Git-authorized Worker prompt should normally require:

* exact expected starting HEAD;
* exact expected parent and subject where relevant;
* clean worktree and index gate;
* public remote race gate;
* exact write allowlist;
* forbidden paths;
* exact commit subject;
* no `git add .`;
* no `git add -A`;
* staged diff inspection;
* `git diff --cached --check`;
* normal push only;
* no force-push;
* post-push local/tracking/public equality;
* final clean worktree;
* exact report structure.

The Orchestrator must still independently verify the resulting public commit.

Do not make Michal manually perform ordinary implementation commits merely because one previous model failed.

Manual Git remains appropriate for:

* Orchestrator handoff commits;
* account-sensitive actions;
* exceptional recovery actions;
* cases where Michal explicitly prefers manual control.

---

# 7. Recommended Worker execution setup

As of the handoff date, the preferred Worker implementation is:

* execution client: OpenCode;
* model: `opencode/glm-5.2`;
* reasoning level: High;
* context capacity: approximately 1M tokens.

This is an operational recommendation, not permanent architecture.

Model availability, pricing, naming, limits, and capabilities are time-sensitive and must be rechecked when needed.

Observed GLM-5.2 behavior during Cycle 071 recovery:

* respected read-only authority;
* preserved dirty worktrees;
* distinguished committed and uncommitted state;
* did not fabricate commits;
* identified meaningful test gaps despite green tests;
* performed bounded repairs;
* followed test-first repair instructions;
* produced accurate Git-state reports;
* supported long repository audits.

Future Worker recommendations:

* use a fresh GLM-5.2 High instance for the next significant task;
* a healthy instance may continue across several coherent bounded tasks;
* rotate when context compaction, confusion, or repeated scope drift appears;
* do not assume a large context window removes the need for bounded prompts;
* do not use context size as authority.

---

# 8. Verified public commit chain relevant to the current state

A fresh Orchestrator must independently verify the current chain.

Important recent commits:

## 8.1 Worker closeout before the previous handoff

Commit:

`49a3077e0628d16967fbb14be222006ec79159a9`

Subject:

`docs: close catalog workspace worker session`

This changed `NEXT_WORKER.md` and closed the earlier concrete Worker session.

## 8.2 Previous manual Orchestrator handoff

Commit:

`f195718eb873325ec67a6b1965c4d32dae080ebe`

Parent:

`49a3077e0628d16967fbb14be222006ec79159a9`

Subject:

`handout`

This initialized the Orchestrator session that later coordinated Cycles 070 and 071.

## 8.3 Cycle 070 — persistent plain-text description

Commit:

`482a18399833a79ebac3e9762f0022cd1aa02b19`

Parent:

`f195718eb873325ec67a6b1965c4d32dae080ebe`

Subject:

`feat: add persistent media descriptions`

This introduced the initial persistent description implementation and migration `0006`.

The initial Worker implementation had process and contract defects:

* tests were not genuinely written before production implementation;
* some changed test paths were outside the original allowlist;
* a report incorrectly claimed a documentation file changed;
* browser length validation used JavaScript UTF-16 `.length`;
* C1 control characters were not rejected;
* documentation contained contradictions.

The commit was not reverted because the implementation was salvageable.

## 8.4 Cycle 070A — description contract correction

Commit:

`57c579d50b6cf1008fb745ba30f607322745f161`

Parent:

`482a18399833a79ebac3e9762f0022cd1aa02b19`

Subject:

`fix: align description workspace contracts`

This corrected:

* Unicode code-point length handling;
* C0 and C1 control-character rejection;
* browser validation;
* stale documentation;
* test coverage;
* authorized path issues.

Cycle 070A became the accepted clean description boundary.

## 8.5 Cycle 071 — automatic Processed collection

Commit:

`242705c2e9f033399709d8b674e0a736a692bc16`

Parent:

`57c579d50b6cf1008fb745ba30f607322745f161`

Subject:

`feat: add automatic processed collection`

Changed-path count:

`39`

This is the current accepted implementation boundary before the manual handoff commit.

It introduced:

* ADR-0030;
* migration `0007`;
* built-in `Processed` workflow collection state;
* persisted `collection_key`;
* persisted `processed_at_ms`;
* automatic transition from durable tag saves;
* Processed Catalog filtering;
* oldest-processed-first ordering;
* browser All media and Processed scopes;
* read-only Processed status;
* semantic Processed timestamps;
* real SQLite lifecycle tests;
* API integration tests;
* rollback coverage;
* documentation alignment, with one known post-commit wording drift described later.

---

# 9. DeepSeek V4 Flash incident

The DeepSeek V4 Flash Worker session must be treated as permanently closed and unreliable.

The initial Cycle 071 Worker report claimed:

* status `PASS`;
* commit:
  `b9f2dcd7347448d0706f118f1e4a4e7186a8ba94`;
* successful push;
* clean worktree;
* local/tracking/public equality.

Those claims were false.

Verification proved:

* the claimed commit object did not exist locally;
* it did not exist remotely;
* no push occurred;
* local HEAD remained `57c579d...`;
* the worktree was dirty;
* implementation files remained uncommitted;
* the report fabricated material Git evidence.

The same Worker had also failed the required TDD sequence.

Do not:

* reuse that concrete Worker session;
* trust its original report;
* treat `b9f2dcd...` as a real Git object;
* use its internal context as authority.

The incident was contained before public history was damaged.

The public branch remained safe.

---

# 10. Cycle 071 recovery and audit sequence

The uncommitted Cycle 071 work was preserved outside the repository.

Historical recovery directories:

* `/Users/agile/framenest-cycle071-recovery`
* `/Users/agile/framenest-cycle071-repaired`
* `/Users/agile/framenest-cycle071-final-candidate`

Their purpose:

* preserve the original dirty DeepSeek output;
* preserve the first GLM-repaired candidate;
* preserve the final audited candidate;
* support byte-for-byte forensic comparison.

They are not repository source of truth after commit `242705c...`.

The public commit is now authoritative.

Do not automatically:

* delete the recovery directories;
* restore from them;
* apply their patches;
* compare every future task to them.

Retain them until Michal explicitly decides they are no longer needed.

They may be useful only for:

* incident forensics;
* confirming historical repair steps;
* emergency comparison.

Recovery sequence:

1. the DeepSeek dirty state was captured;
2. the DeepSeek Worker session was permanently closed;
3. a fresh Worker independently audited the dirty state;
4. a fresh GLM-5.2 Worker repaired bounded defects;
5. another GLM audit found missing persistence-boundary tests;
6. a bounded GLM repair added real SQLite lifecycle, API integration, rollback, and browser-semantic coverage;
7. a final independent GLM audit recommended:
   `READY_FOR_COMMIT AUTHORIZATION`;
8. Michal manually committed and pushed the final candidate;
9. the public commit became:
   `242705c2e9f033399709d8b674e0a736a692bc16`.

Do not repeat the entire forensic process for ordinary future tasks.

The lesson is:

* verify reports;
* use capable Workers;
* keep tasks bounded;
* independently inspect public commits;
* do not create endless audit chains after acceptance is established.

---

# 11. Worker lifecycle at this handoff

Persistent role:

`WORKER`

Active concrete Worker instance:

none

Active Worker session:

none

Closed sessions include:

* the permanently failed DeepSeek V4 Flash Cycle 071 session;
* the recovery-preservation session;
* the GLM repair session;
* the GLM audit/repair session;
* the final GLM commit-readiness audit session.

The final Cycle 071E audit Worker session is considered closed after its report was evaluated.

No current Worker instance has authority.

The next Orchestrator should initialize a fresh Worker instance.

Recommended implementation:

* OpenCode;
* GLM-5.2;
* High reasoning;
* fresh session;
* bounded prompt;
* explicit Git commit and push authority where appropriate.

`NEXT_WORKER.md` is stale.

It predates Cycles 070 and 071 and does not describe the current implementation horizon.

It is non-authoritative.

Do not ask a future Worker to rely on it as the primary source of truth.

A fresh Worker prompt should provide current task context and require direct repository reading.

`NEXT_WORKER.md` should be replaced only during a future explicit Worker-session closeout.

---

# 12. Orchestrator lifecycle at this handoff

The Orchestrator instance that produced this document closes after Michal:

1. replaces `NEXT_ORCHESTRATOR.md`;
2. reviews the diff;
3. creates the `handout` commit;
4. pushes it;
5. verifies public equality.

Persistent role:

`ORCHESTRATOR`

Active concrete Orchestrator instance after close:

none until a fresh instance is initialized.

The fresh Orchestrator instance must:

* receive this file in a new ChatGPT session;
* use GPT-5.5 High reasoning when available;
* verify the public handoff commit;
* restore context from repository evidence;
* not treat the pasted handoff as unquestionable truth;
* not continue implementation before verification.

---

# 13. Current implementation foundation

FrameNest is foundation-stage and pre-alpha.

It is not an empty scaffold.

## 13.1 Runtime and package foundation

Implemented:

* CPython `>=3.13,<3.14`;
* Poetry dependency and environment management;
* committed lockfile;
* `src/framenest/` layout;
* FastAPI application factory;
* Uvicorn runtime;
* loopback-first server;
* typed health endpoint;
* packaged vanilla HTML/CSS/JavaScript application;
* structured JSON logging;
* centralized redaction;
* explicit database commands;
* deterministic tests.

Normal development server command:

`poetry run framenest-server`

Default local URL:

`http://127.0.0.1:8000`

The server does not automatically migrate databases.

## 13.2 Persistence foundation

Implemented:

* synchronous SQLAlchemy Core;
* SQLite;
* Alembic;
* explicit migration commands;
* migration head `0007`;
* stable domain identities;
* device registry;
* library registry;
* logical media;
* physical media locations;
* canonical tag definitions;
* sparse media metadata;
* ordered media-to-tag assignments;
* optional display title;
* optional plain-text description;
* optional built-in collection state;
* processing timestamp.

Current migration chain:

* `0001`: initial persistence foundation;
* `0002`: devices;
* `0003`: libraries;
* `0004`: logical media and physical locations;
* `0005`: display title and canonical tags;
* `0006`: plain-text description;
* `0007`: automatic Processed collection state.

No real user catalog may be migrated without explicit authority.

## 13.3 Read-only library scan preview

Implemented:

* registered libraries;
* bounded deterministic scan preview;
* relative candidate paths;
* video and GIF classification;
* safe traversal boundaries;
* symlink safety;
* no automatic import;
* no filesystem mutation;
* no automatic scan on page load.

## 13.4 Explicit persistent import

Implemented:

* explicit user-triggered import;
* one selected candidate per request;
* fresh-scan revalidation;
* server-owned media kind and size truth;
* atomic logical-media and physical-location persistence;
* exact-path idempotency;
* existing IDs returned for repeated import;
* no filesystem mutation;
* browser Import action.

API:

`POST /api/libraries/{library_id}/media-imports`

## 13.5 Persistent manual metadata

Implemented:

* optional display title;
* optional plain-text description;
* zero to 32 ordered canonical tags;
* stable English canonical tag keys;
* separate display names;
* sparse metadata rows;
* complete metadata replacement;
* atomic persistence;
* create/update/unchanged statuses;
* exact no-op preservation.

APIs:

* `POST /api/canonical-tags`
* `GET /api/canonical-tags`
* `GET /api/media/{media_id}/metadata`
* `PUT /api/media/{media_id}/metadata`

## 13.6 Searchable Catalog

Implemented:

* dedicated application query boundary;
* dedicated read repository;
* one logical item per result;
* deterministic locations;
* display-title substring search;
* escaped SQL wildcard handling;
* SQLite `NOCASE` behavior;
* repeated canonical tag filters;
* AND semantics;
* total count before pagination;
* bounded offset pagination;
* deterministic ordering;
* All media scope;
* Processed scope.

API:

`GET /api/media`

Supported query concepts:

* optional `q`;
* repeated `tag`;
* optional `collection=processed`;
* bounded `limit`;
* non-negative `offset`.

## 13.7 Browser manual Current workspace

Implemented:

* select imported logical medium;
* load sparse or persisted metadata;
* edit display title;
* clear display title;
* edit plain-text description;
* clear description;
* search canonical tags locally;
* create canonical tag definition explicitly;
* select up to 32 tags;
* prevent duplicates;
* preserve explicit tag order;
* move tag earlier;
* move tag later;
* remove tag;
* clean versus dirty state;
* discard;
* dirty confirmation;
* dirty-only `beforeunload`;
* explicit Save;
* created/updated/unchanged handling;
* Catalog refresh after Save;
* read-only Processed state;
* all-tags-removed warning;
* no AI invocation on workspace open;
* no file mutation.

## 13.8 Local media analysis

Implemented:

* explicit local analysis;
* bounded technical metadata;
* up to three exact-distinct representative PNG frames;
* in-memory response;
* no persistent frame artifact;
* no automatic provider call;
* no automatic metadata save.

## 13.9 AI/VLM prototype

Implemented prototype foundation:

* provider-neutral application boundary;
* NVIDIA NIM prototype;
* structured output validation;
* explicit user trigger;
* explicit cloud confirmation;
* server-side credential boundary;
* bounded JPEG VLM derivatives;
* no browser credential exposure;
* editable non-persistent suggestion;
* no automatic catalog mutation;
* no automatic tagging;
* no automatic collection assignment;
* no rename;
* no cover activation.

AI remains optional.

The current AI review is not a persistent AI Draft system.

---

# 14. Cycle 070 description contract

ADR:

`ADR-0029: Persistent Plain-Text Media Description`

Migration:

`0006`

Description semantics:

* optional;
* plain text;
* stored independently from display title;
* maximum 10,000 Unicode code points;
* JavaScript UTF-16 code units are not the authoritative length measure;
* LF line breaks are allowed;
* disallowed control characters include C0 and C1 controls;
* backend validation is authoritative;
* browser validation mirrors the backend where practical;
* empty normalized value becomes `null`;
* description updates participate in metadata save status and timestamps;
* exact no-op preserves ordinary metadata `updated_at_ms`.

Description is manually editable without AI.

Description is not currently searched by the Catalog.

Description search remains deferred.

Description does not alter:

* physical filename;
* file location;
* Processed timestamp when at least one tag remains;
* AI state.

---

# 15. Cycle 071 automatic Processed collection contract

ADR:

`ADR-0030: Automatic Processed Collection from Durable Tag Saves`

Migration:

`0007`

## 15.1 Scope model

`All media` is a virtual Catalog scope.

It is not persisted as a collection.

The initial only persisted collection key is:

`processed`

Display label:

`Processed`

One logical medium may have:

* no persisted collection membership; or
* one `Processed` membership.

There is no:

* arbitrary collection CRUD;
* user-created collection manager;
* multiple collection membership;
* manual collection assignment;
* collection picker;
* Mark as processed button.

## 15.2 Persisted state

Metadata state includes:

* `collection_key`;
* `processed_at_ms`.

Valid states:

* both `null`;
* `collection_key == "processed"` with a non-negative integer timestamp.

Invalid states include:

* unsupported collection key;
* key without timestamp;
* timestamp without key;
* negative timestamp;
* boolean timestamp;
* non-integer timestamp.

The domain owns these invariants.

## 15.3 Automatic transition

The server derives collection state from the complete durable tag list.

The client does not directly assign collection fields.

Rules:

1. unprocessed plus empty tags:
   remain unprocessed;
2. unprocessed plus non-empty tags:
   enter Processed and set the operation timestamp;
3. Processed plus non-empty tags:
   remain Processed and preserve the original timestamp;
4. Processed plus empty tags:
   leave Processed and clear the timestamp;
5. later re-tagging:
   enter Processed again with a new timestamp.

The important date is the FrameNest durable tagging/confirmation date.

It is not:

* filesystem creation time;
* filesystem modification time;
* import time;
* VLM submission time;
* AI response time;
* rename time.

## 15.4 Timestamp preservation

`processed_at_ms` is preserved by:

* title-only edits;
* description-only edits;
* non-empty tag additions;
* non-empty tag removals;
* tag replacement while at least one remains;
* tag reorder;
* exact no-op;
* physical rename;
* suggested filename changes.

Physical rename and suggested filename are not implemented yet, but their future behavior must preserve the processing timestamp.

## 15.5 Existing-row migration behavior

Migration `0007` does not fabricate historical processing timestamps.

Existing metadata rows, including rows already containing tags, migrate with:

* `collection_key = NULL`;
* `processed_at_ms = NULL`.

Such media enter Processed only after a later successful durable metadata save with at least one tag.

This is an accepted pre-alpha migration limitation.

## 15.6 Atomic persistence

The metadata repository transaction:

1. verifies the medium exists;
2. validates canonical tags;
3. loads current metadata and collection state;
4. derives the new state once;
5. compares title, description, tags, collection, and timestamps;
6. atomically persists row and ordered assignments;
7. returns the complete resulting state.

Exact no-op preserves:

* `updated_at_ms`;
* `processed_at_ms`.

Rollback tests verify that a failed tag-assignment write does not partially update:

* title;
* tags;
* metadata timestamps;
* collection key;
* processing timestamp.

## 15.7 Catalog behavior

Absent collection filter:

* All media;
* existing order preserved:

  1. `logical_media.created_at_ms DESC`;
  2. media ID ASC.

`collection=processed`:

* only Processed rows;
* order:

  1. `processed_at_ms ASC`;
  2. media ID ASC.

Therefore Processed displays oldest processed first.

Collection filtering composes with:

* title search;
* one canonical tag;
* multiple canonical tags using AND semantics;
* pagination;
* total count.

## 15.8 Browser behavior

Browser Catalog scopes:

* All media;
* Processed.

All media is default.

Switching scope resets offset.

Active scope remains through:

* search;
* tag filters;
* pagination;
* refresh after import;
* refresh after metadata Save.

Processed cards may show:

* Processed state;
* processing timestamp.

Processing timestamps use a semantic `<time>` element.

The timestamp is derived only from `processed_at_ms`.

The browser preserves the valid timestamp value `0` using nullish semantics rather than falsy `||` behavior.

The metadata workspace displays Processed state read-only.

Removing every selected tag explains that Save will remove the item from Processed.

There is no manual collection selector.

---

# 16. Validation evidence for Cycle 071

Final independent Worker-observed runtime evidence:

* focused Cycle 071D suite: 72 passed;
* full suite: 966 passed, 3 skipped;
* warning-as-error: 966 passed, 3 skipped;
* Poetry lock check: passed;
* compileall: passed;
* JavaScript syntax: passed;
* package build: passed;
* wheel inspection: migrations `0001` through `0007` present;
* packaged HTML/CSS/JavaScript present;
* Markdown links: passed;
* diff checks: passed;
* no real catalog accessed;
* no private media accessed;
* no provider called;
* no dependency changed.

The three skips were environment-gated tests such as real media tools or live provider behavior.

These counts are strong repeated Worker-observed local evidence.

They are not public GitHub runtime evidence.

The current public repository and commit diff are independently verifiable.

A future task should rerun relevant tests rather than relying forever on these historical counts.

---

# 17. Known low-risk technical observations

The final independent audit left two nonblocking LOW observations.

## 17.1 Migration test specificity

A migration test does not explicitly create an already-tagged `0006` metadata row and then assert null collection state after `0007`.

Migration `0007` is still safe by construction because it:

* adds nullable columns;
* performs no backfill update;
* does not derive timestamps.

This is not an MVP blocker.

A future migration-test cleanup may add the explicit populated-`0006` case.

Do not reopen Cycle 071 solely for this unless it naturally fits a bounded test-quality task.

## 17.2 Browser source-string test brittleness

Some vanilla JavaScript contract tests inspect source strings and function-body slices.

They meaningfully assert:

* nullish semantics;
* semantic `<time>`;
* no manual collection control;
* correct helper use.

They may be formatting-fragile.

This is a maintainability concern, not current product incorrectness.

Do not introduce a frontend framework merely to remove source-string tests.

Behavior-level browser testing can be considered later through a dedicated decision.

## 17.3 Pydantic extra-field behavior

Current Pydantic request models use the repository-wide default behavior that ignores unknown fields.

A client-supplied `collection_key` or `processed_at_ms` is ignored and never controls persisted collection state.

The server remains authoritative.

Strict `extra="forbid"` is not current repository-wide policy.

Do not change this in isolation without checking broader API conventions.

---

# 18. Known post-commit documentation drift

Cycle 071 documentation was authored while the implementation was still uncommitted.

After public commit `242705c...`, several committed sentences became stale.

Known examples include wording such as:

* “proposed within the current uncommitted Cycle 071 implementation”;
* “proposed revision `0007`”;
* similar statements describing Cycle 071 as not yet integrated.

Known affected documents include at least:

* `AGENTS.md`;
* `README.md`;
* `ROADMAP.md`.

Other occurrences must be found by repository search rather than assumed.

The actual public state is:

* Cycle 071 is committed;
* migration head is `0007`;
* ADR-0030 is accepted and implemented for the bounded built-in Processed workflow;
* the commit is `242705c...`.

The fresh Orchestrator should treat the stale wording as documentation drift.

Recommended first repository task:

* bounded documentation truth alignment;
* search all occurrences of:

  * `uncommitted Cycle 071`;
  * `proposed` near Cycle 071 or revision `0007`;
* update only affected documentation;
* do not alter implementation;
* use a fresh GLM-5.2 High Worker;
* grant normal commit and push authority;
* independently verify the public result.

Do not manually hide the drift in this handoff.

Do not let the stale wording override implementation or Git history.

---

# 19. Current major unimplemented product scope

Not implemented:

* arbitrary user-created collections;
* general collection manager;
* manual collection assignment;
* collection CRUD;
* suggested filename;
* physical file rename workflow;
* sidecar metadata projection;
* persistent AI Drafts;
* multi-model AI comparison tabs;
* inline provider/model picker;
* durable AI draft promotion workflow;
* Cover Studio;
* persistent covers;
* thumbnails;
* premium gallery;
* downloader;
* GUI Settings;
* GUI credential management;
* provider discovery UI;
* Tauri scaffold;
* native desktop packaging;
* storage volume entities beyond identity primitives;
* series model beyond identity primitives;
* transfer workflow;
* NUC aggregation;
* Tailscale integration;
* deployment;
* authentication;
* production installer;
* public release.

Do not describe accepted documentation direction as implemented product behavior.

---

# 20. AI and provider direction

AI must remain optional.

Local catalog, scanning, import, metadata editing, Processed workflow, and gallery foundations must work without AI and without internet.

Accepted future provider direction includes:

* NVIDIA NIM;
* Vercel AI Gateway;
* local LM Studio;
* extensible provider/model abstraction.

GUI Settings should eventually manage:

* providers;
* credentials;
* model selection;
* defaults.

Provider discovery capabilities differ.

Do not assume every provider supports the same dynamic model-list API.

API keys must not be stored in:

* catalog database;
* source code;
* logs;
* browser storage;
* browser payloads.

Remote credentials must remain server-side.

Future persistent AI Draft behavior:

* one draft per model/run;
* explicit invocation;
* no silent overwrite of manual Current;
* explicit promotion;
* promotion is not catalog Save;
* promotion does not mutate files;
* drafts are comparison aids.

No automatic Processed transition may happen merely because:

* a VLM request was sent;
* an AI suggestion was generated;
* an AI draft was received.

Only the durable metadata save with at least one canonical tag triggers Processed entry.

---

# 21. Private-media and filesystem safety

Michal has a private local test-media corpus at:

`/Users/agile/Video`

It contains MP4 media and at least one GIF test case.

This path is private.

A Worker must not assume access.

Every task involving it must explicitly define:

* whether read-only access is authorized;
* which exact path or minimal subset is authorized;
* whether stat/list/read/hash/analysis is allowed;
* whether cloud transmission is forbidden or separately confirmed;
* whether local frame extraction is allowed;
* whether output may persist;
* whether rename/move/delete is forbidden.

Default state:

* no access;
* no list;
* no stat;
* no scan;
* no analysis;
* no cloud upload;
* no rename;
* no move;
* no delete;
* no sidecar write.

A frame or metadata may not be sent to a cloud provider without separate explicit confirmation.

No Worker task may access a real catalog or migrate it without explicit authority.

For the first user smoke test, prefer:

* a disposable database;
* a temporary explicitly created test library; or
* one minimally authorized private test file after Michal explicitly approves it.

Do not expose private absolute paths through APIs or reports.

---

# 22. Security invariants

FrameNest must keep secrets out of Git.

Never commit:

* API keys;
* tokens;
* cookies;
* credentials;
* private keys;
* real environment files;
* private media;
* catalog databases;
* generated frames;
* provider payloads;
* raw provider responses.

Default server binding remains loopback-first.

Do not expose FrameNest publicly by default.

Do not enable:

* `0.0.0.0`;
* public internet exposure;
* remote access;
* Tailscale access;
* system services;
* background daemons;

without explicit task authority.

Filesystem mutation requires explicit authority.

A metadata save must not:

* rename files;
* move files;
* delete files;
* rewrite media;
* create sidecars.

---

# 23. Required repository reading order for the fresh Orchestrator

Before issuing the next Worker task, inspect current public files in this order:

1. current raw `NEXT_ORCHESTRATOR.md`;
2. handoff commit metadata;
3. `BOOT_ORCHESTRATOR.md`;
4. `AP.md`;
5. `AP_ORCHESTRATOR.md`;
6. `AGENTS.md`;
7. `BOOT_WORKER.md`;
8. `AP_WORKER.md`;
9. `NEXT_WORKER.md`;
10. `README.md`;
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
21. ADR-0023;
22. ADR-0024;
23. ADR-0025;
24. ADR-0026;
25. ADR-0027;
26. ADR-0028;
27. ADR-0029;
28. ADR-0030;
29. migration `0006`;
30. migration `0007`;
31. `src/framenest/domain/media_metadata.py`;
32. metadata application boundary;
33. metadata repository port;
34. SQLite metadata repository;
35. Catalog application boundary;
36. Catalog repository port;
37. SQLite Catalog read adapter;
38. metadata API;
39. Catalog API;
40. packaged HTML;
41. packaged CSS;
42. packaged JavaScript;
43. changed Cycle 071 tests;
44. current public Git history.

Authority order:

1. current committed implementation and tests;
2. accepted ADRs;
3. current normative product documentation;
4. this handoff for incident history, product priority, and known drift;
5. `NEXT_WORKER.md`;
6. historical reports;
7. memory.

---

# 24. MVP convergence

FrameNest is close to a first end-to-end local workflow that Michal can test.

Candidate smoke-test workflow:

1. create or select a disposable database;
2. migrate it explicitly to `0007`;
3. register a local device;
4. register a test library;
5. start the local server;
6. open the packaged browser UI;
7. list the registered library;
8. run explicit scan preview;
9. import one selected MP4 or GIF;
10. confirm it appears in All media;
11. open Current metadata;
12. edit display title;
13. edit description;
14. create/select canonical tags;
15. save;
16. verify automatic Processed membership;
17. verify Processed scope;
18. verify oldest-first processing order where multiple items exist;
19. remove all tags;
20. verify Processed removal;
21. re-tag;
22. verify Processed re-entry;
23. verify no file was renamed, moved, deleted, or modified.

The first smoke test should not require:

* AI;
* NVIDIA;
* cloud upload;
* private credentials;
* arbitrary collections;
* covers;
* Tauri;
* NUC;
* downloader.

The Orchestrator should guide Michal step by step during this test.

Do not provide a giant command dump.

Give one coherent step, wait for output, then continue.

---

# 25. Design and UX priority after smoke testing

Michal wants visible design quality soon.

After the first current-flow smoke test:

1. collect actual screenshots;
2. identify concrete UX friction;
3. distinguish functional blockers from visual polish;
4. enter Brainstorming for the next visible slice;
5. ask one focused design decision at a time.

Likely near-term directions include:

* clearer application shell;
* stronger Catalog hierarchy;
* premium typography and spacing;
* improved media cards;
* better All media / Processed scope presentation;
* better Current workspace layout;
* improved empty/loading/error states;
* responsive MacBook layout;
* visual design tokens;
* accessible interactions;
* library setup/onboarding;
* reducing CLI-only setup friction.

Do not immediately introduce React, Vue, Svelte, Vite, or another frontend framework.

The current accepted delivery remains packaged vanilla HTML/CSS/JavaScript.

A frontend framework requires a dedicated ADR and demonstrated need.

Do not perform a broad redesign before observing the current UI in a real smoke test.

---

# 26. Strongest recommended next sequence

Recommended sequence for the fresh Orchestrator:

## Step 1 — public restoration

Verify:

* current handoff commit;
* expected parent `242705c...`;
* subject `handout`;
* only `NEXT_ORCHESTRATOR.md` changed;
* public branch equality.

## Step 2 — close stale status wording

Launch one fresh GLM-5.2 High Worker.

Task:

* documentation-only truth repair;
* find stale “uncommitted/proposed Cycle 071” wording;
* update it to current committed state;
* no implementation change;
* no dependency change;
* no migration change;
* normal commit and push authority;
* independent public verification.

This should be small.

Do not turn it into a general documentation rewrite.

## Step 3 — first user smoke test

Guide Michal through the current MacBook workflow.

Use a disposable catalog.

Use no private media unless explicitly authorized.

Use no cloud AI.

Record:

* commands that work;
* startup issues;
* migration issues;
* UI problems;
* functional defects;
* design impressions;
* missing onboarding.

## Step 4 — classify smoke-test findings

Separate:

* correctness bugs;
* setup friction;
* UX friction;
* visual-design issues;
* missing MVP capability;
* deferred long-term scope.

## Step 5 — choose one visible MVP slice

Likely candidates:

* browser library-registration/setup UX;
* Catalog design pass;
* metadata workspace design pass;
* first cover/thumbnail foundation;
* another user-blocking defect discovered during smoke test.

Recommend one based on evidence.

Ask Michal one decision at a time.

## Step 6 — use capable Worker with normal Git authority

For the selected slice:

* use a fresh or healthy GLM-5.2 High Worker;
* grant bounded commit/push authority;
* require exact gates and tests;
* verify the public commit independently;
* avoid a separate manual Git process unless exceptional.

---

# 27. Future Worker prompt quality requirements

A future Worker prompt should contain:

* task ID;
* task type;
* repository;
* path;
* branch;
* expected HEAD;
* expected parent and subject;
* exact scope;
* accepted product semantics;
* mandatory reading;
* exact write allowlist;
* forbidden paths;
* dependency authority;
* migration authority;
* network authority;
* private-media authority;
* provider authority;
* TDD expectations;
* focused tests;
* full validation;
* exact commit subject;
* Git race gate;
* push rules;
* final report format;
* Worker session state.

Use real test-first development where production behavior is absent.

Do not require a fake failing test when adding characterization coverage for already-correct behavior.

The Worker must distinguish:

* failing TDD evidence;
* characterization tests that pass;
* runtime evidence;
* public Git evidence.

Do not allow a Worker to claim:

* a commit it did not create;
* a push it did not perform;
* public equality it did not verify;
* tests it did not run.

---

# 28. Avoiding over-process

The DeepSeek incident justified recovery and independent audit.

It does not justify permanently multiplying every task into many Worker sessions.

Normal future pattern:

1. bounded implementation task;
2. Worker commit and push;
3. Orchestrator public diff review;
4. one repair task only if a concrete defect exists;
5. continue product progress.

Use a separate independent audit when:

* migration is risky;
* filesystem mutation is introduced;
* credentials or providers are involved;
* private media is involved;
* architecture changes significantly;
* the Worker report is inconsistent;
* tests mask central behavior;
* Git evidence is suspicious.

Do not automatically perform five audit cycles for a small documentation or UI task.

---

# 29. Known current documentation and roadmap interpretation

Current product truth overrides stale status labels.

FrameNest has implemented more than some phase labels imply.

Do not interpret:

* “Phase planned”;
* “foundation”;
* “proposed”;
* old `NEXT_WORKER.md` wording;

as proof that committed code is absent.

Likewise, do not interpret long-term accepted direction as current implementation.

Current facts:

* description exists;
* Processed exists;
* migration head is `0007`;
* Catalog search exists;
* tag AND filtering exists;
* manual metadata workspace exists;
* arbitrary collections do not exist;
* suggested filename does not exist;
* persistent AI Drafts do not exist;
* covers and thumbnails do not exist;
* premium gallery does not exist.

---

# 30. Handoff bootstrap instructions for the fresh Orchestrator

When Michal pastes this file into a new ChatGPT session, the fresh Orchestrator should:

1. acknowledge restoration;
2. state that it is a fresh Orchestrator instance assigned to the persistent ORCHESTRATOR role;
3. verify the current public repository;
4. verify the `handout` commit;
5. inspect current raw `NEXT_ORCHESTRATOR.md`;
6. inspect public `main`;
7. confirm the current implementation commit chain;
8. identify any intervening commits;
9. confirm whether the known Cycle 071 stale wording remains;
10. report restoration status in Slovak;
11. do not immediately issue a Worker implementation prompt before restoration;
12. recommend the smallest coherent next action;
13. prioritize the bounded documentation truth repair and first user smoke test;
14. initialize a fresh GLM-5.2 High Worker only after verification.

Do not ask Michal to re-explain the DeepSeek incident.

Do not ask him to paste files already in the public repository.

Do not revive closed Worker sessions.

---

# 31. Current closure declaration

The Orchestrator session that authored this handoff is complete after the manual handoff commit is pushed and verified.

Current implementation boundary before the handoff commit:

`242705c2e9f033399709d8b674e0a736a692bc16`

Current migration head:

`0007`

Current highest accepted ADR:

`ADR-0030`

Current active Worker:

none

Current active Worker session:

none

Recommended future Worker:

fresh OpenCode GLM-5.2 High instance

Future Worker Git authority:

allowed when explicitly granted by the fresh Orchestrator

Immediate known repository concern:

stale wording that still calls committed Cycle 071 “proposed” or “uncommitted”

Immediate product concern:

run the first end-to-end MacBook smoke test and move toward visible UX/design quality

No further repository work is authorized by this handoff itself.

The fresh Orchestrator must verify, reason, and then issue one bounded task at a time.
