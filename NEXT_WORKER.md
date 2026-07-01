# FrameNest Worker Handoff

## 1. Bootstrap Identity And Authority

A future Worker must be a fresh Worker instance assigned to the persistent,
vendor-neutral FrameNest `WORKER` role.

The current concrete Worker session closes with the enclosing handoff commit.
After that commit is verified and pushed, no active Worker remains. Do not
resume old checkpoints, terminals, compacted memory, temporary task state, or
execution-client state.

This file restores context only. It grants no concrete task authority,
repository modification authority, Git authority, media authority, credential
authority, cloud-call authority, filesystem mutation authority, or disposable
runtime authority. Every future task requires a new explicit ORCHESTRATOR
prompt.

Expected enclosing handoff commit subject:

```text
docs: close rendered UX worker session
```

The enclosing handoff commit SHA cannot be recorded before the commit exists. A
future Worker must discover and verify it from public repository state.

## 2. Repository Truth To Verify

- Repository: `https://github.com/cisarik/framenest.git`
- Normal local path: `/Users/agile/framenest`
- Branch: `main`
- Latest implementation boundary:
  `db665e7053ed750f398164866b85e10e3f32e9cd`
- Implementation subject: `fix: apply rendered acceptance feedback`
- Implementation parent:
  `78e69152ad60e97e8a61da02b110a7d21ecd64fd`
- Migration head: `0007`
- Highest accepted ADR: `ADR-0030`
- Expected enclosing handoff commit:
  - changes only `NEXT_WORKER.md`;
  - has subject `docs: close rendered UX worker session`;
  - has parent `db665e7053ed750f398164866b85e10e3f32e9cd`.

A future Worker must independently verify the handoff SHA, parent, subject,
changed-path count and exact changed path, raw public `NEXT_WORKER.md`,
local/tracking/public equality, and clean tracked worktree and index.

Do not place a guessed enclosing SHA in this file.

## 3. Human And Communication Context

The COOPERATOR is Michal. The Orchestrator communicates with him in Slovak,
uses masculine grammatical forms for Michal, and uses feminine grammatical
self-reference. Worker prompts and Worker reports are in English. Worker
reports begin exactly:

```text
### Report for ORCHESTRATOR_CHAT
```

Michal owns final rendered UX acceptance, private-media authority, credential
authority, cloud-upload approval, destructive filesystem decisions, and
irreversible product decisions. Do not ask him to perform ordinary Git,
migration, test, build, or repository-maintenance commands.

## 4. Worker Lifecycle And Context State

The current Worker instance implemented the rendered-acceptance correction
ending at `db665e7053ed750f398164866b85e10e3f32e9cd`.

COOPERATOR-observed context state: the current Worker context was reported as
full before this closeout task. This is lifecycle evidence, not repository
truth.

Worker-observed state: this mandatory closeout task stopped the completed
disposable rendered-acceptance runtime, replaced this handoff, validated it,
committed it, pushed it, and closes the Worker session. No automatic compaction
was exposed during closeout. Exact token usage was not exposed by the client.

Any compaction during closeout does not authorize further implementation. This
concrete Worker instance must receive no further task. The next implementation
requires a fresh Worker instance.

## 5. Implemented Product Horizon

FrameNest currently has:

- loopback-first FastAPI application;
- packaged same-origin vanilla HTML/CSS/JavaScript frontend;
- SQLite, SQLAlchemy Core, and Alembic through `0007`;
- device and library registry;
- read-only scanning;
- explicit idempotent import;
- persistent logical media and physical locations;
- editable title, description, and ordered tags;
- hidden automatic `Processed` behavior;
- catalog search and tag filtering;
- local development launcher;
- secure identity-only GIF/MP4 streaming;
- byte-range MP4 support;
- static real-content GIF card previews;
- paused real MP4 card previews;
- real Details playback;
- simplified single-form media editor;
- explicit NVIDIA AI analysis;
- direct AI population of current unsaved editor fields;
- editable Suggested filename proposal;
- no automatic metadata save;
- no physical rename yet;
- numbered COOPERATOR acceptance methodology in `AP.md` and
  `AP_ORCHESTRATOR.md`.

Important recent commit sequence:

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

## 6. Current Gallery And Details Truth

Available GIF cards show a static real-content preview. Available MP4 cards
show a real paused frame. Card media surfaces open real playback. The visible
`Details` card action is removed.

A visible centered `▶` overlay still exists at the implementation boundary and
is now rejected as redundant by the latest COOPERATOR rendered acceptance.
`Edit` remains.

Details is player-first with black surfaces. GIF animates in Details only. MP4
native controls and seeking work. Playback stops on close or replacement. Card
and Details URLs remain identity-only. No durable persistent cover pipeline is
implemented.

## 7. Current Editor And AI Truth

The media editor modal heading derives from current title or filename fallback.
Exactly one Title, Description, and Tags workflow exists.

AI analysis requires explicit confirmation. The idle button is intended to be
an explicit AI action. Active loading occurs in the AI button. AI success
directly populates the existing unsaved editor state. Suggested filename is
shown as an editable proposal. Metadata Save is separate. Successful Save
closes the modal. No physical file rename occurs.

No automatic provider call occurs on Gallery, Details, or editor open. No
second AI Draft form, `Use draft`, or `Discard draft` remains.

Identity-only AI endpoint:

```text
POST /api/media/{media_id}/locations/{location_id}/ai-suggestion-preview
```

- Model: `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning`
- Prompt: `framenest-media-suggestion-v3`
- Reasoning: `chat_template_kwargs.enable_thinking=false`
- Transport: maximum three optimized JPEG preview frames plus bounded
  path-free metadata.

Original media, absolute path, and API key are not uploaded.

## 8. Latest COOPERATOR Rendered Acceptance

Latest rendered acceptance is COOPERATOR-observed evidence.

Accepted:

1. real card visuals;
2. static GIF card behavior;
3. paused MP4 card behavior;
4. media-surface playback;
5. black player-first Details;
6. MP4 playback and seeking;
7. one editor field set;
8. dynamic editor heading;
9. cloud confirmation;
10. AI result quality;
11. editability;
12. no autosave before Save;
13. Save closes and refreshes;
14. pagination basics;
15. removal of Library tools;
16. no visible private/internal leakage.

Screenshot-backed bug:

- during an active AI request, the AI button visibly contains both the idle
  label and loading content simultaneously;
- the idle and loading states are therefore not mutually exclusive.

Latest accepted correction decisions:

1. remove the visible centered `▶` card control because clicking the card media
   already performs playback;
2. preserve media-surface keyboard accessibility;
3. reuse the appealing circular visual language for the header `FN` mark;
4. idle AI label becomes `🧠 Analyze by AI`;
5. active AI button content becomes only spinner plus `Analyzing…`;
6. after successful AI analysis, hide the AI button for that modal-open
   session;
7. remove always-visible provider/model text from the editor;
8. rename visible `Server` status to `Cloud`;
9. visible AI status becomes `🧠 AI`;
10. healthy/available text is green, unavailable text red, checking neutral;
11. status-pill hover should try a white border;
12. main Gallery tag/filter hover should try a white border;
13. remove visible `Catalog` and `Imported media` headings.

These corrections are not yet implemented at the handoff boundary.

## 9. Immediate Next Recommended Task

Next bounded task name:

```text
Refine post-acceptance Gallery and AI editor UX
```

Expected implementation commit subject:

```text
fix: refine gallery and AI editor UX
```

The task should implement only:

- removal of the redundant visible `▶`;
- preservation of media-surface playback and accessibility;
- circular `FN` branding treatment;
- `Cloud` and `🧠 AI` visible status labels;
- green/red state-colored visible text;
- white-border hover experiments for status pills and Gallery tag/filter
  controls;
- removal of `Catalog` and `Imported media` headings;
- removal of visible provider/model noise in the editor;
- exact idle label `🧠 Analyze by AI`;
- mutually exclusive idle/loading content;
- active content only spinner plus `Analyzing…`;
- hiding the Analyze action after success for the current modal session;
- narrow `GALLERY.md` and `AI_WORKSPACE.md` reconciliation;
- focused and full automated validation;
- a fresh disposable rendered-acceptance environment.

A future ORCHESTRATOR prompt must independently provide the exact handoff SHA,
write allowlist, tests, Git authority, media authority, runtime authority, and
commit subject. This handoff does not authorize that task.

## 10. Explicit Deferrals

### Global Tag Deletion

Latest brainstorming introduced global tag deletion as a separate product idea.
Current `×` behavior removes a tag from the selected media only.

A future global deletion design must separately decide:

- whether the definition should be deleted;
- what happens to every other media item using it;
- whether confirmation identifies affected item count;
- whether the action is reversible;
- how AI may recreate the same semantic tag;
- whether unused tags are cleaned automatically or only explicitly.

Do not treat `×` as global database deletion until a dedicated domain task
authorizes it.

### Physical Rename On Save

Michal wants a reviewed AI-suggested filename to be capable of renaming real
hash-like media files. This is accepted product direction but is not
implemented.

The dedicated rename slice must decide whether rename happens:

- as part of Save;
- through a separate explicit confirmation triggered from Save;
- or through a dedicated Rename action.

It must guarantee explicit old/new basename review, one selected available
physical location, extension preservation, safe filename validation,
registered-root containment, symlink-escape protection, collision detection, no
overwrite by default, no directory move, no broad batch rename, coordinated
filesystem and database-location update, recoverable ordering or compensation
on partial failure, no rename from analysis alone, no rename merely from
populating fields, focused filesystem tests, and explicit rendered/manual
acceptance.

The fresh Orchestrator should prioritize this immediately after the small UX
correction passes rendered acceptance.

## 11. Header, Pagination, And Gallery State

Current implementation:

- visible `FN` branding;
- visible `Server` and `AI` status pills;
- status semantics remain accessible;
- page-size choices `10`, `30`, `60`, and `90`;
- default page size `30`;
- localStorage validation;
- `<` and `>` pagination controls;
- Library tools removed from Gallery.

Pending correction:

- `Server` to `Cloud`;
- `AI` to `🧠 AI`;
- state-colored visible text;
- white-border hover;
- circular `FN`;
- remove `Catalog` and `Imported media`.

## 12. Settings, Library, And Central-Server Direction

Future product direction, not implemented authority:

- library selection should move to `Settings > General`;
- ordinary Gallery must not expose developer Library tools;
- exact library path, folder picker, registration, scan, and import UX still
  require a bounded design;
- no arbitrary-path browser endpoint;
- future product direction includes central-server media storage;
- upload/sync semantics remain unresolved;
- downloads should be explicit and on demand;
- AI analysis remains explicit and on demand;
- local/server ownership, cache, conflict, availability, and deletion semantics
  require a separate architecture decision.

Do not claim Settings, upload, sync, central storage, or download-on-demand are
implemented.

## 13. Demo Strategy

Accepted future direction:

```text
./framenest demo start
./framenest demo status
./framenest demo reset
```

Optional alias:

```text
./framenest demo
```

Demo mode should use isolated database/runtime/logs, run migrations
deterministically, import only generated, original, or clearly redistributable
fixtures, never commit a generated SQLite database, never depend on private
local media inputs, never mix with the persistent development catalog, provide
an immediately populated Gallery, and remove only positively identified
demo-owned state.

Demo mode is not yet implemented.

## 14. Local Media Policy

Optional local acceptance inputs:

- `assets/gif/dicaprio_bravo.gif`
  `a5102a628c3409de6def8a21ebda8a30133abbbf3181336fc92727d50f92ce50`
- `assets/mp4/dicaprio.mp4`
  `520d43ee7f5853fec1aa9d72908b8d1a45a004a634a7558ff2889a32ff8e7ca9`

They are not repository source, not redistributable demo fixtures, and may
exist only in Michal's current clone. They are ignored locally through exact
`.git/info/exclude` entries:

```text
/assets/gif/dicaprio_bravo.gif
/assets/mp4/dicaprio.mp4
```

No future Worker may inspect, read, hash, copy, analyze, upload, rename, move,
or delete them without explicit task-specific authority. The private Video
directory remains forbidden by default.

## 15. Automated And Rendered Evidence Classification

Worker-observed evidence for the latest implementation slice:

- Focused tests: `174 passed`
- Full suite: `1193 passed, 3 skipped`
- JavaScript syntax: passed
- `git diff --check`: passed
- Markdown links: `24 checked, 0 missing`

These results are Worker-observed evidence, not independently rerun public CI
proof.

The latest COOPERATOR acceptance is rendered evidence and includes the concrete
AI-button visual defect and new product decisions listed above.

## 16. Analytic Programming Acceptance Methodology

`AP.md` and `AP_ORCHESTRATOR.md` now normatively support numbered COOPERATOR
acceptance reports.

Each item may receive:

- `PASS`
- `FAIL`
- `NOT TESTED`
- status plus `+` commentary
- `+` alone for new brainstorming

Screenshots are optional evidence, not mandatory ceremony.

The ORCHESTRATOR must classify results into accepted behavior, concrete
defect, missing evidence, new product decision, or adjacent scope. New ideas do
not automatically expand an active Worker task.

## 17. Recommended Continuation

A fresh Orchestrator should:

1. verify the enclosing Worker handoff commit publicly;
2. boot a fresh Worker instance;
3. issue the bounded `Refine post-acceptance Gallery and AI editor UX`
   correction;
4. independently verify its commit;
5. request one short numbered rendered acceptance report;
6. if the correction passes, stop and remove its disposable runtime;
7. then authorize the dedicated physical filename rename design and
   implementation slice;
8. after rename acceptance, prioritize first-run library onboarding/import;
9. design central-server upload/sync/download semantics separately;
10. implement isolated demo mode;
11. refine the populated Gallery;
12. begin thin Tauri v2 shell work only after the core
    add/import/analyze/edit/rename flow is coherent.

## 18. Immediate Non-Goals

The next correction task must not expand into global tag deletion, physical
rename, tag garbage collection, Settings library picker, upload,
synchronization, central-server storage, download-on-demand, provider Settings,
multi-model AI Drafts, persistent AI results, cover pipeline, thumbnail
storage, onboarding, demo mode, Tauri, signing, packaging, or unrelated backend
redesign.

## 19. Orchestrator Lifecycle Note

The current Orchestrator session remains active while this Worker session
closes. After the immediate correction logical slice is completed and rendered
acceptance is processed, Michal intends to rotate the Orchestrator. The current
Orchestrator will then prepare a complete `NEXT_ORCHESTRATOR.md`. Michal will
manually place it in the repository, commit it, and push it using his chosen
handoff commit subject.

No Worker should modify `NEXT_ORCHESTRATOR.md` without a future explicit task.

## 20. Closure Status

- Implementation boundary:
  `db665e7053ed750f398164866b85e10e3f32e9cd`
- Migration: `0007`
- Highest accepted ADR: `ADR-0030`
- Current Worker: closes with the enclosing handoff commit
- Active Worker after verified push: none
- Immediate next task: refine post-acceptance Gallery and AI editor UX
- Immediate expected implementation subject:
  `fix: refine gallery and AI editor UX`
- Next major product slice after correction: explicit safe physical filename
  rename
- Rendered acceptance: latest slice accepted with one concrete AI-button bug
  and listed UX corrections
- Orchestrator: remains active until the correction logical slice is completed

This handoff grants no task authority.
