# FrameNest Orchestrator Handoff

## 1. Bootstrap Identity And Authority

You are a fresh Orchestrator instance assigned to the persistent,
vendor-neutral FrameNest `ORCHESTRATOR` role.

This file is the current repository-native Orchestrator handoff. It supersedes
all earlier versions of `NEXT_ORCHESTRATOR.md` where they conflict. It restores
context; it grants no repository-modification, Git, Worker-task, private-media,
credential, cloud-call, runtime, or filesystem-mutation authority.

Every concrete Worker task requires a new explicit ORCHESTRATOR prompt. Worker
reports are evidence-bearing testimony, not repository truth. Public repository
state must be independently verified before authorizing work. Do not revive old
checkpoints, terminals, compacted execution state, temporary roots, browser
sessions, pending commands, or closed Worker sessions.

The current Orchestrator session closes with the enclosing handoff commit. The
COOPERATOR, Michal, manually places this finalized file in the repository and
creates the handoff commit. The expected enclosing commit subject is:

```text
handout
```

The enclosing commit SHA cannot be written here before the commit exists. A
fresh Orchestrator instance must discover and verify it from public repository
state.

## 2. Enclosing Handoff Commit To Verify

Immediately before Michal's Orchestrator handoff commit, public `main` is
expected to be:

- SHA: `a661f0995b2d822c7e6ed8fe12fd26726bd02bdd`
- Subject: `docs: close rendered UX worker session`
- Parent: `db665e7053ed750f398164866b85e10e3f32e9cd`
- Changed path: `NEXT_WORKER.md` only

The enclosing Orchestrator handoff commit is expected to:

- have subject `handout`;
- have parent `a661f0995b2d822c7e6ed8fe12fd26726bd02bdd`;
- change only `NEXT_ORCHESTRATOR.md`;
- contain this exact file as its public raw content.

The fresh Orchestrator must independently verify:

1. public `refs/heads/main`;
2. the enclosing handoff SHA;
3. its parent and exact subject;
4. changed-path count and exact changed path;
5. raw public `NEXT_ORCHESTRATOR.md`;
6. that the preceding Worker handoff commit is exactly
   `a661f0995b2d822c7e6ed8fe12fd26726bd02bdd`;
7. local/tracking/public equality where future Worker evidence is available.

Do not claim an enclosing handoff SHA from this file.

## 3. Current Repository Truth

- Project: `FrameNest`
- Repository: `https://github.com/cisarik/framenest.git`
- Normal local path: `/Users/agile/framenest`
- Branch: `main`
- Latest implementation boundary before Worker and Orchestrator handoffs:
  `db665e7053ed750f398164866b85e10e3f32e9cd`
- Implementation subject: `fix: apply rendered acceptance feedback`
- Implementation parent: `78e69152ad60e97e8a61da02b110a7d21ecd64fd`
- Current Worker handoff boundary before this Orchestrator handoff:
  `a661f0995b2d822c7e6ed8fe12fd26726bd02bdd`
- Worker handoff subject: `docs: close rendered UX worker session`
- Migration head: `0007`
- Highest accepted ADR: `ADR-0030`
- Expected tracked worktree and index after handoff completion: clean.

The implementation boundary remains `db665e7...`; the newer Worker and
Orchestrator handoff commits are lifecycle/documentation boundaries, not product
implementation.

## 4. Human And Communication Context

The COOPERATOR is Michal.

Communicate with him in Slovak. Address him using masculine grammatical forms.
Use feminine grammatical forms for Orchestrator self-reference. Worker prompts
are in English. Worker reports are in English and begin exactly:

```text
### Report for ORCHESTRATOR_CHAT
```

Distinguish:

- independently verified repository fact;
- Worker-observed evidence;
- COOPERATOR-observed rendered or physical evidence;
- inference;
- recommendation;
- unresolved product or architecture decision.

Michal retains final authority over:

- rendered and physical UX acceptance;
- Worker and Orchestrator rotation timing;
- private-media access;
- cloud upload confirmation;
- credentials;
- destructive or irreversible filesystem actions;
- final product direction.

Do not ask him to perform ordinary Git, migration, test, build, runtime,
repository-maintenance, or disposable-environment commands. Process ceremony
must not replace visible product progress. Ask at most one focused product
question only when a real unresolved choice blocks safe implementation.

## 5. Worker And Orchestrator Lifecycle

The Worker session closed by
`a661f0995b2d822c7e6ed8fe12fd26726bd02bdd` is definitively closed. No active
Worker remains after that commit. The next implementation must use a fresh
Worker instance assigned to the persistent `WORKER` role.

Do not revive the closed Worker merely because its client window may still
exist. Do not resume compacted memory, old task state, old temporary roots, old
browser state, or previously prepared prompts as authority.

The current Orchestrator session closes with Michal's enclosing `handout`
commit. A fresh Orchestrator instance must restore state from public repository
truth and this file.

Orchestrator rotation and Worker rotation are independent lifecycles:

- rotating the Orchestrator does not activate or rotate a Worker;
- rotating a Worker does not activate or rotate the Orchestrator;
- handoff files restore context but grant no concrete task authority.

## 6. Context Pressure And Automatic Compaction

Michal decides when a concrete Worker or Orchestrator context is no longer
trustworthy enough to continue.

Observed Worker-session evidence from this project:

- a first automatic context compaction did not prevent a carefully bounded
  implementation task from completing successfully after repository and
  protocol restoration;
- a later Worker session also completed a documentation-only closeout after a
  second compaction;
- another Worker was closed before assigning further implementation when its
  context was reported full;
- exact token usage was frequently not exposed by the execution client.

Operational guidance:

1. Compaction is not a clean-session reset.
2. After compaction, require rereading current protocol and handoff files,
   repeating repository gates, and reconstructing authority from the exact
   current prompt.
3. Continue only when scope, security boundaries, repository state, and intended
   outcome are unambiguous.
4. Prefer a fresh Worker for a new substantial logical slice when context is
   already full or a second compaction is imminent.
5. A Worker near lifecycle close should receive only a bounded closeout task
   replacing `NEXT_WORKER.md`, validating it, committing it, and pushing it.
6. Do not plan implementation through a third compaction.
7. Never estimate token usage or compaction count when the client does not
   expose it.

These are risk controls, not a claim that every first compaction must force
immediate rotation. Michal retains the final rotation decision.

## 7. Implemented Product Horizon

FrameNest currently has:

- a loopback-first FastAPI application;
- a packaged same-origin vanilla HTML/CSS/JavaScript frontend;
- SQLite with SQLAlchemy Core;
- Alembic migrations through `0007`;
- device and library registration;
- explicit read-only scanning;
- idempotent candidate import;
- persistent logical media and physical locations;
- editable title, description, and ordered canonical tags;
- internal automatic `Processed` behavior hidden from ordinary editor UX;
- catalog search and tag filtering;
- bounded pagination with `10`, `30`, `60`, and `90` items per page;
- local development launcher commands through root `./framenest`;
- secure identity-only GIF/MP4 streaming;
- full and single-range MP4 responses;
- real media card visuals;
- static real-content GIF card previews;
- paused, muted real MP4 card previews;
- real GIF and MP4 playback in Details;
- a simplified single-form media editor;
- explicit NVIDIA-backed imported-media analysis;
- direct AI population of current unsaved editor fields;
- an editable Suggested filename proposal;
- no automatic metadata save;
- no physical rename yet;
- reusable numbered COOPERATOR acceptance methodology in `AP.md` and
  `AP_ORCHESTRATOR.md`.

Important recent implementation sequence:

- `815039506be9cc8e7ffa72ca88ad234e314b628e`
  `fix: stabilize details media loading`
- `a15dfef0bcb1e9827087f12f8b8b8d04fcee9b77`
  `feat: make gallery playback content-first`
- `d7aabd36b64d3b9ab6420aaf43b182a3aba2d958`
  `feat: simplify media editor UX`
- `67d7ec9061b2ecaac8826ba1e39ebd1d47055872`
  `feat: integrate AI media drafts`
- `db665e7053ed750f398164866b85e10e3f32e9cd`
  `fix: apply rendered acceptance feedback`

Do not claim the current Gallery is a finished MVP. It is materially closer,
but one small rendered-acceptance correction is still pending, followed by
physical rename and first-run onboarding/import.

## 8. Secure Media Content And Playback

The secure identity-only media endpoint remains:

```text
GET /api/media/{media_id}/locations/{location_id}/content
```

Current accepted security and behavior boundaries include:

- media/location/library relationship authorization;
- location availability checks;
- exact supported GIF/MP4 kind-extension pairs;
- registered-root containment;
- traversal rejection;
- symlink-escape prevention;
- no arbitrary path-serving API;
- no absolute-path disclosure;
- read-only content serving;
- full response and one byte-range request;
- sanitized failures;
- stable media cleanup and stale-event protection.

COOPERATOR-observed evidence established:

- GIF animates in Details;
- MP4 loads and plays;
- native controls are visible;
- seeking works;
- switching from MP4 to GIF stops MP4;
- closing the Details player stops playback;
- black player-first Details styling is accepted.

Static source tests are not a substitute for rendered evidence, but the core
playback path is now both automated-test covered and manually observed.

## 9. Current Gallery And Details UX

At implementation boundary `db665e7...`:

- available GIF cards display static real-content previews;
- available MP4 cards display real paused frames;
- GIF cards do not animate automatically;
- clicking a card's media surface opens real Details playback;
- the visible `Details` card button has been removed;
- `Edit` remains;
- a visible centered circular `▶` control still exists;
- Details has a black player-first surface;
- title is not unnecessarily duplicated;
- Technical details start collapsed;
- native MP4 controls and seeking remain;
- card and Details URLs remain identity-only;
- there is no durable accepted cover or persistent thumbnail pipeline yet.

Latest COOPERATOR decision:

- the visible `▶` is now rejected as redundant because the card media surface
  already performs the same playback action;
- the attractive circular styling should be reused for the header `FN` brand
  mark instead of being discarded;
- media-surface mouse and keyboard accessibility must remain after removing the
  visible overlay.

This correction is not implemented at the handoff boundary.

## 10. Current Editor And AI UX

At `db665e7...` the media editor has:

- dynamic heading from current title or filename fallback;
- exactly one Title field;
- exactly one Description field;
- one searchable Tags interaction;
- selected display-name chips with `×` removal;
- hidden canonical keys;
- hidden Processed semantics;
- Save and Cancel;
- explicit AI confirmation;
- direct AI population of the existing unsaved fields;
- editable Suggested filename proposal;
- successful Save closing and refreshing the Gallery;
- no automatic save from AI;
- no physical file rename.

The older duplicated AI Draft form, `Use draft`, and `Discard draft` controls no
longer exist.

Latest screenshot-backed defect:

- during an active request, the AI button visibly contains both the idle label
  and the loading label/spinner;
- idle and loading content are not mutually exclusive.

Latest accepted correction decisions:

1. Idle button label must be exactly `🧠 Analyze by AI`.
2. Idle state shows no spinner and no `Analyzing…` text.
3. During a real request, the entire button content becomes only the familiar
   spinner plus `Analyzing…`.
4. After a successful AI result, hide the Analyze action for the remainder of
   that modal-open session.
5. Remove the always-visible provider/model line from the ordinary editor.
6. Keep the explicit cloud confirmation.
7. Keep one Title/Description/Tags state only.
8. Suggested filename remains an editable proposal until the dedicated rename
   slice.

These corrections are not implemented at the handoff boundary.

## 11. Current AI Integration Truth

Imported-media AI analysis uses the identity-only endpoint:

```text
POST /api/media/{media_id}/locations/{location_id}/ai-suggestion-preview
```

Current provider/model behavior:

- provider: NVIDIA NIM;
- model: `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning`;
- prompt version: `framenest-media-suggestion-v3`;
- reasoning disabled explicitly through
  `chat_template_kwargs.enable_thinking=false`;
- maximum three optimized JPEG representative frames;
- bounded path-free technical metadata;
- strict validated JSON response;
- server-side credential only;
- explicit user confirmation required;
- no request on Gallery, Details, or editor open;
- no original GIF/MP4 upload;
- no absolute path upload;
- no API-key exposure;
- no chain-of-thought request, display, or persistence;
- no metadata save or filesystem mutation during analysis.

The response provides:

- title;
- description;
- tags;
- suggested filename.

AI results populate only the current unsaved editor state after explicit
confirmation. Manual editing remains fully usable without AI or internet.

Worker-observed live NVIDIA evidence from the explicitly authorized local media:

GIF proposal:

- Title: `Leonardo DiCaprio Clapping`
- Description: `Leonardo DiCaprio in a suit claps his hands with a subtle smile, appearing to applaud in an office setting.`
- Tags: `Leonardo DiCaprio`, `Clapping`, `Office`, `Reaction`, `Meme`
- Suggested filename: `leonardo-di-caprio-clapping.gif`

MP4 proposal:

- Title: `Man Pointing While Holding Cup`
- Description: `A man in a yellow shirt sits in a chair, holding a cup and pointing forward with his other hand.`
- Tags: `Man`, `Pointing`, `Cup`, `Yellow Shirt`, `Chair`, `Indoor`, `Reaction`
- Suggested filename: `dicaprio-pointing-cup.mp4`

Two successful provider calls were made in that controlled smoke. There was no
retry, no auto-save, no rename, no original-file upload, and no observed
credential/path/prompt/frame/raw-response leakage. Do not rerun those provider
calls merely to reproduce already sufficient evidence.

The established ignored local credential source may be
`.secrets/nvidia.env.fish`. Never print, stage, commit, summarize, hash, or
partially reveal its value. A future task must independently verify that no real
credential is tracked or staged before a provider call.

## 12. Latest COOPERATOR Rendered Acceptance

The latest numbered acceptance report is COOPERATOR-observed rendered evidence.

Accepted:

1. real card visuals;
2. static GIF card behavior;
3. paused MP4 card behavior;
4. media-surface playback;
5. black player-first Details;
6. MP4 playback and seeking;
7. one editor field set;
8. dynamic editor heading;
9. truthful cloud confirmation;
10. useful AI result quality;
11. editable AI-populated values;
12. no autosave before Save;
13. successful Save closes and refreshes;
14. pagination basics;
15. removal of Library tools;
16. no visible private/internal leakage.

Confirmed correction needs and accepted product refinements:

1. Remove the redundant visible centered `▶` card control.
2. Preserve media-surface playback and keyboard accessibility.
3. Reuse its circular visual treatment for header `FN` branding.
4. Fix mutually exclusive AI idle/loading content.
5. Use exact idle label `🧠 Analyze by AI`.
6. Use only spinner plus `Analyzing…` during a request.
7. Hide the Analyze action after successful analysis in that modal session.
8. Remove the ordinary editor's provider/model line.
9. Rename visible status `Server` to `Cloud`.
10. Rename visible AI status to `🧠 AI`.
11. Use green visible text when healthy/available, red when unavailable, and
    subdued neutral only while checking.
12. Try a white-border hover treatment for status pills.
13. Try a white-border hover treatment for main Gallery tag/filter controls.
14. Give selected-tag `×` a clearly red destructive-looking hover/focus state,
    while keeping its current bounded meaning: remove from this media only.
15. Remove visible `Catalog` and `Imported media` headings for compactness.

Screenshot evidence is optional, not mandatory ceremony. The latest single
screenshot was sufficient to establish the AI-button state bug. Do not demand
many screenshots when Michal's direct rendered report is already precise.

## 13. Immediate Next Worker Task

After verifying the enclosing Orchestrator handoff commit, the fresh
Orchestrator should open a fresh Worker session and issue one bounded correction
task.

Task name:

```text
Refine post-acceptance Gallery and AI editor UX
```

Expected implementation commit subject:

```text
fix: refine gallery and AI editor UX
```

Expected starting HEAD:

- the exact enclosing Orchestrator `handout` commit SHA discovered publicly;
- not merely `a661f099...`;
- the Worker prompt must insert the real exact handoff SHA, parent, subject, and
  changed path after verification.

The correction must implement only:

- removal of the redundant visible `▶` control;
- preservation of media-surface playback and keyboard accessibility;
- circular `FN` brand treatment based on the accepted former play-control
  styling without creating a fake button;
- visible `Cloud` and `🧠 AI` status labels;
- green/red/neutral state-colored visible status text;
- accessible hidden/title state descriptions;
- white-border hover/focus refinement for status pills;
- white-border hover/focus refinement for Gallery tag/filter controls;
- red hover/focus styling for the selected-tag `×` remove control;
- removal of visible `Catalog` and `Imported media` headings;
- removal of visible provider/model noise from the editor;
- exact idle AI label `🧠 Analyze by AI`;
- no idle spinner or idle `Analyzing…`;
- active button content only spinner plus `Analyzing…`;
- duplicate-request prevention;
- hiding Analyze after success for that modal-open session;
- existing confirmation, field population, Suggested filename, Save, Cancel,
  cleanup, stale-response, and security behavior;
- narrow `GALLERY.md` and `AI_WORKSPACE.md` reconciliation;
- automated validation;
- a new disposable rendered-acceptance environment.

Do not include physical rename, global tag deletion, Settings, sync, onboarding,
demo mode, or Tauri in this correction.

### Preferred write allowlist

Prefer only:

- `GALLERY.md`
- `AI_WORKSPACE.md`
- `src/framenest/adapters/api/web/index.html`
- `src/framenest/adapters/api/web/app.js`
- `src/framenest/adapters/api/web/styles.css`
- `tests/contract/test_local_web_application.py`

Allow one additional existing frontend test file only if inspection proves it
is the correct established location. Do not silently expand scope.

### Required implementation evidence

Tests should prove at minimum:

1. visible `▶` card control is absent;
2. media surface still opens real Details playback;
3. media surface remains keyboard accessible;
4. `Edit` remains;
5. `FN` uses the circular brand treatment without becoming a deceptive inert
   button;
6. visible statuses are `Cloud` and `🧠 AI`;
7. accessible status truth remains available;
8. healthy/available, unavailable, and checking states receive correct visible
   text classes;
9. white-border hover/focus classes exist for status and Gallery tag/filter
   controls;
10. selected-tag `×` has red hover/focus styling without global-deletion
    behavior;
11. `Catalog` and `Imported media` headings are absent;
12. editor still has exactly one Title, one Description, and one Tags workflow;
13. provider/model line is absent from ordinary editor view;
14. idle button is exactly `🧠 Analyze by AI`;
15. idle state contains no spinner or `Analyzing…`;
16. request state replaces the complete button content with spinner plus
    `Analyzing…`;
17. no second spinner appears;
18. successful response populates current fields and Suggested filename;
19. successful response hides the Analyze action for that open session;
20. failure restores the idle button and preserves values;
21. confirmation remains mandatory;
22. Save still does not rename a file;
23. `×` still removes only from the current media;
24. no private path, canonical key, credential, prompt, data URL, or raw
    provider response appears.

### Required validation

Use focused affected tests, then:

```text
node --check src/framenest/adapters/api/web/app.js
poetry run pytest
git diff --check
```

Validate local Markdown links in changed documentation. Inspect the complete and
staged diff, exact changed-path set, tracked/staged credential-shaped patterns,
and final cleanliness. Ruff is not a required gate unless intentionally added
as a committed dependency.

Require exactly one commit with the expected subject, normal push, no
force-push, post-push local/tracking/public equality, and a clean final tracked
worktree/index.

## 14. Private Local Media For Acceptance

Two optional local acceptance inputs may exist only in Michal's local clone:

- `assets/gif/dicaprio_bravo.gif`
  SHA-256:
  `a5102a628c3409de6def8a21ebda8a30133abbbf3181336fc92727d50f92ce50`
- `assets/mp4/dicaprio.mp4`
  SHA-256:
  `520d43ee7f5853fec1aa9d72908b8d1a45a004a634a7558ff2889a32ff8e7ca9`

They are:

- not repository source;
- not public demo fixtures;
- not assumed redistributable;
- locally ignored through exact `.git/info/exclude` entries;
- never to be staged or committed without a separate licensing and repository
  size decision.

No Worker may inspect, hash, read, copy, analyze, upload, rename, move, or delete
them without explicit task-specific authority.

For the immediate correction task, the Orchestrator may explicitly authorize:

- hash verification;
- read-only copying into one unique disposable acceptance library after the
  implementation commit;
- no modification of originals;
- no autonomous provider call;
- no upload of original GIF/MP4 bytes.

The Worker may prepare an acceptance server with AI capability available, but
Michal must explicitly click and confirm the AI request in the rendered UI.

`/Users/agile/Video` remains forbidden by default.

## 15. Rendered Acceptance After The Immediate Correction

After independently verifying the correction commit, request a short numbered
COOPERATOR report. Do not require many screenshots unless a visual state is
unclear.

Recommended acceptance items:

1. Card has no visible `▶`; clicking and keyboard-activating the media surface
   still opens playback.
2. Header `FN` has the accepted circular styling.
3. Header shows only `Cloud` and `🧠 AI`, with correct green/red/neutral state
   coloring and acceptable white-border hover.
4. Main tag/filter hover uses the refined border treatment; selected-tag `×`
   turns red on hover/focus.
5. `Catalog` and `Imported media` headings are absent without leaving awkward
   spacing.
6. Editor idle state shows only `🧠 Analyze by AI`, without spinner/loading
   text or provider/model noise.
7. During a real confirmed request, the button shows only spinner plus
   `Analyzing…`.
8. After success, existing Title/Description/Tags and Suggested filename are
   populated and the AI button disappears.
9. Save still closes and updates metadata but does not yet rename the file.
10. No private/internal value, stale loading state, or new playback regression
    appears.

Accepted response syntax:

```text
1. PASS
2. PASS + comment
3. FAIL + concrete defect
4. NOT TESTED + reason
5. + adjacent brainstorming
```

Classify every response into accepted behavior, concrete defect, missing
evidence, new product decision, or adjacent scope. New brainstorming does not
automatically expand an active Worker task.

## 16. Physical Filename Rename: Next Major Slice

Michal's latest accepted product direction is stronger than an indefinite
future Rename button:

> A reviewed and editable Suggested filename should be capable of renaming the
> real selected media file when the user explicitly saves.

This is not implemented yet and must remain separate from the immediate visual
correction.

Recommended first-slice UX:

1. AI analysis or manual editing may populate/edit Suggested filename.
2. Analysis alone never renames.
3. Populating fields never renames.
4. When Save is pressed and Suggested filename is valid and differs from the
   current basename, show one explicit confirmation containing the old and new
   basenames.
5. The primary action is `Save and rename`; Cancel returns to the editor without
   mutation.
6. When no filename proposal exists or it equals the current basename, Save
   remains metadata-only.
7. Close the modal only after all requested metadata and rename effects
   succeed.
8. On failure, keep the editor open, preserve unsaved values, and report one
   concise sanitized error.

The implementation must guarantee:

- one selected available physical location in the first slice;
- extension preservation;
- filename-only input;
- safe normalized filename validation;
- no slash, backslash, control character, leading dot, `..`, or path injection;
- same-directory rename only;
- registered-root containment;
- symlink-escape protection;
- current-location identity revalidation;
- collision detection;
- no overwrite by default;
- no directory move;
- no broad batch rename;
- no automatic rename of all physical locations;
- coordinated filesystem and database-location update;
- a proven recoverable operation order or compensation when one side fails;
- no stale catalog path after success;
- content endpoint continues to work after rename;
- metadata and Gallery refresh remain coherent;
- explicit filesystem and database tests;
- explicit rendered/manual acceptance using disposable copied media.

A dedicated design/implementation task must inspect current location schema,
repositories, transaction boundaries, scan/import idempotency, and content
security before selecting the operation order. Do not improvise rename inside a
frontend-only task.

## 17. Tag Removal And Global Tag Deletion

Current `×` semantics are bounded:

- remove the selected tag from the current media's unsaved editor state;
- Save persists the current media's tag list;
- the canonical tag definition remains available to other media.

Latest UX refinement for the immediate correction:

- `×` should use a clearly red hover/focus treatment.

Michal also brainstormed a future confirmation asking whether to remove the tag
entirely from the database. That is a separate destructive domain feature and
is not yet authorized.

A future global tag-deletion design must determine:

- affected-media count and disclosure;
- whether deletion is allowed while any media uses the tag;
- whether the operation removes assignments, the definition, or both;
- reversibility or undo;
- transaction behavior;
- how AI may recreate the same semantic tag;
- whether unused definitions are garbage-collected automatically or deleted
  only explicitly;
- confirmation wording and permission boundaries.

Do not silently turn the ordinary chip `×` into global database deletion.

## 18. First-Run Library Onboarding And Settings

After physical rename acceptance, the highest-value product slice is first-run
library onboarding/import.

Accepted direction:

- the flagship Gallery must not expose developer `Library tools`;
- library selection belongs under `Settings > General`;
- the ordinary user should see a concise current-library state and a clear
  `Change` or equivalent action;
- Save/Cancel and a familiar loading indicator should be used where an actual
  operation occurs;
- scan remains read-only;
- import remains explicit and idempotent;
- no cloud request occurs merely from selecting a library;
- no media rename/move/delete occurs during import;
- no arbitrary browser-supplied path endpoint is introduced.

Before native Tauri folder selection exists, a bounded browser-development
bridge may reuse current launcher/CLI registry, scan, and import boundaries. A
future Worker must inspect existing commands before choosing exact UX or command
names.

The final desktop path should use a narrowly scoped native system directory
picker and a trusted boundary passing only the selected path to the authoritative
Python backend.

## 19. Central Server, Upload, Sync, And Download-On-Demand

Michal's longer-term product direction includes media stored on a central
server, with downloads performed only on explicit user request. AI analysis is
also explicitly on demand.

This direction is not implemented and remains a separate architecture/product
slice. Do not mix it into Gallery correction, rename, or first-run local import.

The future design must resolve:

- local versus server authority;
- canonical ownership of media bytes and metadata;
- upload versus sync semantics;
- conflict resolution;
- availability and offline behavior;
- explicit download-on-demand behavior;
- local cache ownership, eviction, and verification;
- deletion semantics;
- identity across devices and libraries;
- authorization and transport security;
- progress, retry, and cancellation UX;
- privacy and cloud-upload confirmation;
- how AI frame upload relates to server-resident or locally downloaded media.

Do not fake this with an arbitrary-path API, generic `Sync` button, or hidden
background transfer.

## 20. Deterministic Demo Strategy

A deterministic demo is accepted as a useful developer/product aid, but is not
yet implemented.

Preferred future namespace:

```text
./framenest demo start
./framenest demo status
./framenest demo reset
```

Optional convenience alias:

```text
./framenest demo
```

Demo mode should:

- use an isolated database, runtime, and logs;
- build state deterministically from migrations and imports;
- never commit a generated SQLite database;
- never mix with the persistent development catalog;
- use only generated, original, or clearly redistributable fixtures;
- never depend on the two private local DiCaprio inputs;
- provide an immediately populated Gallery;
- remove only positively identified demo-owned state;
- reuse the existing launcher/controller process-management architecture.

Do not create top-level `load_demo` and `remove_demo` commands without a bounded
launcher design task.

## 21. Desktop And Packaging Direction

Tauri v2 remains the intended thin native shell, but it is not the immediate
next task.

Begin the shell only after the core user path is coherent enough to wrap:

1. add/select/import media;
2. view populated Gallery;
3. play media;
4. analyze explicitly;
5. edit metadata and tags;
6. save and safely rename when requested.

The shell should eventually provide:

- native desktop window/WebView;
- single instance;
- supervised Python/FastAPI sidecar;
- loopback-only connection;
- readiness handshake;
- clean owned-child shutdown;
- tray/menu-bar behavior;
- native folder picker;
- minimal Tauri permissions;
- per-launch local authentication/bootstrap before packaged release.

End users should not need fish, Poetry, uv, Python, Node, or Rust. Native CI
runners should build host-native macOS, Linux, and Windows artifacts. Signing,
notarization, updater, and installers remain later release work.

## 22. Analytic Programming Acceptance Methodology

`AP.md` and `AP_ORCHESTRATOR.md` now normatively define numbered COOPERATOR
acceptance feedback.

For user-visible work, the ORCHESTRATOR should prepare numbered independently
observable outcomes. The COOPERATOR may answer with:

- `PASS`;
- `FAIL`;
- `NOT TESTED`;
- a status followed by `+` commentary;
- `+` alone for brainstorming or adjacent feedback.

`+` adds evidence or context; it does not silently change the status.

Screenshots, videos, logs, or physical observations should identify the relevant
item when useful. Screenshots are optional evidence, not mandatory ceremony.
The ORCHESTRATOR may request a specific screenshot only when it materially
resolves uncertainty.

The ORCHESTRATOR must classify responses into:

- accepted behavior;
- concrete defect;
- missing evidence;
- new product decision;
- adjacent scope.

Preserve positive acceptance while extracting a concrete defect from
`PASS + comment`. Authorize the smallest bounded correction for confirmed
defects. Do not silently add adjacent brainstorming to a Worker task.

## 23. Evidence Classification

Worker-observed automated evidence for implementation boundary `db665e7...`:

- focused frontend contract tests: `174 passed`;
- full suite: `1193 passed, 3 skipped`;
- JavaScript syntax check: passed;
- `git diff --check`: passed;
- changed-document Markdown links: `24 checked, 0 missing`;
- final tracked worktree and index: clean;
- public refs were reported equal after push.

Worker closeout evidence for `a661f099...`:

- only `NEXT_WORKER.md` changed;
- `git diff --check` passed;
- public raw handoff matched local committed content;
- final tracked worktree/index was clean;
- the disposable acceptance runtime was stopped and removed;
- local media hashes remained unchanged;
- no active Worker remained.

Treat all test/runtime details above as Worker-observed evidence unless a fresh
Orchestrator or Worker independently reruns them. Treat the numbered UI findings
as COOPERATOR-observed rendered evidence. Treat public commit identity and raw
files as independently verifiable repository facts.

## 24. Private Data And Secret Rules

`/Users/agile/Video` remains forbidden by default. No Worker may list, stat,
scan, hash, read, analyze, extract frames from, upload, rename, move, or delete
from it without explicit task-specific authority.

The two local acceptance inputs are also forbidden by default despite being
inside the local repository directory. Every task requiring them must grant the
minimum explicit read-only/copy/cloud authority.

Never expose:

- NVIDIA API keys;
- Authorization headers;
- browser cookies;
- secret-store contents;
- raw provider payloads;
- raw data URLs;
- chain-of-thought;
- unrelated catalog paths;
- private absolute paths in public logs, APIs, UI, commits, or reports.

Credentials must remain server-side and outside source code, catalog database,
Git history, and ordinary logs.

## 25. Documentation Drift

Some older `ROADMAP.md`, product, and architecture wording may lag behind the
implemented Gallery/editor/AI state.

Newer verified code, commits, `README.md`, `GALLERY.md`, `AI_WORKSPACE.md`, AP
protocol documents, current handoffs, and COOPERATOR decisions take precedence
over stale wording where they conflict.

Do not begin a broad documentation rewrite during the immediate correction. A
future bounded reconciliation may update roadmap milestones after the correction
and rename slices are accepted.

## 26. Immediate Non-Goals

The immediate correction must not expand into:

- physical rename;
- global tag deletion;
- tag garbage collection;
- library Settings or native picker;
- upload or sync;
- central-server storage;
- download-on-demand;
- provider Settings;
- multi-model AI drafts;
- persistent AI result storage;
- cover pipeline;
- thumbnail persistence;
- first-run onboarding;
- demo mode;
- Tauri;
- packaging, signing, or installers;
- unrelated backend redesign.

After the correction passes rendered acceptance, the next major slice is the
safe Save-and-rename workflow, not a broad feature wave.

## 27. Fresh Orchestrator Bootstrap Behavior

The fresh Orchestrator must:

1. State that she is a fresh Orchestrator instance assigned to the persistent
   `ORCHESTRATOR` role.
2. Communicate with Michal in Slovak using feminine self-reference.
3. Verify the public enclosing `handout` commit and actual `main`.
4. Verify its SHA, parent, subject, changed-path count, exact changed path, and
   raw `NEXT_ORCHESTRATOR.md`.
5. Verify preceding Worker handoff
   `a661f0995b2d822c7e6ed8fe12fd26726bd02bdd` and raw `NEXT_WORKER.md`.
6. Recognize that no Worker is active.
7. Report restoration as `PASS`, `PARTIAL`, or `BLOCKED`.
8. Avoid asking Michal to repeat project history or paste public repository
   files.
9. Open a fresh Worker session for the immediate correction.
10. Insert the exact enclosing Orchestrator handoff SHA as the Worker's expected
    starting HEAD.
11. Issue a bounded correction prompt following Section 13.
12. Independently verify the resulting commit.
13. Request the short numbered rendered acceptance in Section 15.
14. Stop and clean up the disposable runtime after acceptance.
15. If a concrete defect remains, authorize only one small correction.
16. If accepted, proceed to the safe physical rename slice in Section 16.
17. Then prioritize first-run library onboarding/import.
18. Keep central-server sync/download architecture separate.
19. Implement isolated demo mode later.
20. Begin Tauri only after the core workflow is coherent.

## 28. Closure Status

- Latest implementation boundary:
  `db665e7053ed750f398164866b85e10e3f32e9cd`
- Latest Worker handoff boundary before this file:
  `a661f0995b2d822c7e6ed8fe12fd26726bd02bdd`
- Expected enclosing Orchestrator handoff subject: `handout`
- Expected enclosing handoff parent:
  `a661f0995b2d822c7e6ed8fe12fd26726bd02bdd`
- Expected enclosing changed path: `NEXT_ORCHESTRATOR.md` only
- Migration: `0007`
- Highest accepted ADR: `ADR-0030`
- Active Worker: none
- Current Orchestrator session: closes with the enclosing handoff commit
- Immediate next task: refine post-acceptance Gallery and AI editor UX
- Expected next implementation subject:
  `fix: refine gallery and AI editor UX`
- Next major product slice after acceptance: safe physical rename during an
  explicit Save flow
- Next product slice afterward: first-run library onboarding/import
- Later architecture slice: central-server upload/sync/download-on-demand
- Later developer/product aid: isolated deterministic demo mode
- Long-term shell: Tauri v2

This file restores context and grants no concrete task authority.
