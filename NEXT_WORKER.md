# FrameNest Worker Handoff

## 1. Bootstrap Identity And Authority

A future Worker must be a fresh Worker instance assigned to the persistent,
vendor-neutral FrameNest `WORKER` role.

This current Worker session is closed by the enclosing handoff commit. After
that commit is verified and pushed, no active Worker remains. Do not revive old
checkpoints, terminals, temporary task state, client memory, or closed session
context.

This file restores context only. It grants no concrete task, repository
modification, Git, media, credential, cloud, runtime, cleanup, or implementation
authority. Every future task requires a new explicit ORCHESTRATOR prompt.

Expected enclosing handoff commit subject:

```text
docs: close AI draft worker session
```

The enclosing handoff commit SHA cannot be recorded here before the commit
exists. A future Worker must discover and verify it from public repository
state.

## 2. Repository Truth To Verify

- Repository: `https://github.com/cisarik/framenest.git`
- Normal local path: `/Users/agile/framenest`
- Branch: `main`
- Latest implementation boundary before this handoff:
  `67d7ec9061b2ecaac8826ba1e39ebd1d47055872`
- Implementation subject: `feat: integrate AI media drafts`
- Implementation parent: `d7aabd36b64d3b9ab6420aaf43b182a3aba2d958`
- Migration head: `0007`
- Highest accepted ADR: `ADR-0030`
- Expected handoff commit changed path: only `NEXT_WORKER.md`

A future Worker must independently verify local `HEAD`, tracking `origin/main`,
and public `refs/heads/main`; the enclosing handoff commit SHA, parent, subject,
changed path count, raw `NEXT_WORKER.md` content, and repository cleanliness.
Do not infer repository truth from this file alone.

## 3. Human And Communication Context

The COOPERATOR is Michal. The Orchestrator communicates with him in Slovak,
uses masculine grammatical forms for Michal, and uses feminine grammatical
self-reference. Worker prompts and Worker reports are in English. Worker
reports begin exactly:

```text
### Report for ORCHESTRATOR_CHAT
```

Michal owns final UX acceptance, private-media authority, credential authority,
and irreversible filesystem decisions. Do not ask him to perform ordinary Git,
migration, test, build, or repository-maintenance commands.

## 4. Session And Compaction Lifecycle

- COOPERATOR-observed evidence: one automatic context compaction occurred
  earlier in this Worker session.
- Worker-observed evidence: a second automatic context compaction occurred
  during this closeout task after the handoff replacement was drafted. The
  Worker reread the final task, protocol, handoff, product, and relevant ADR
  files; repeated the repository gate; and continued only because the remaining
  closeout validation was unambiguous.
- Client limitation: exact token usage was not exposed.
- This closeout is the final task for the current Worker session regardless of
  whether a second compaction occurs.
- No further task may be assigned to this concrete Worker instance.
- Any future task requires a fresh Worker instance.

## 5. Implemented Horizon

FrameNest currently has a loopback FastAPI application, packaged same-origin
vanilla frontend, SQLite persistence with SQLAlchemy Core and Alembic through
`0007`, device and library registration, read-only scanning, idempotent
candidate import, persistent logical media and physical locations, user-editable
title and description, ordered tags, automatic internal `Processed` behavior,
catalog search and filtering, local development launcher, secure identity-only
GIF/MP4 content streaming, content-first Gallery cards, real Details playback,
a simplified user-facing `Edit media` dialog, and explicit NVIDIA-backed AI
Draft workflow.

Important recent implementation sequence:

- `815039506be9cc8e7ffa72ca88ad234e314b628e`
  `fix: stabilize details media loading`
- `a15dfef0bcb1e9827087f12f8b8b8d04fcee9b77`
  `feat: make gallery playback content-first`
- `d7aabd36b64d3b9ab6420aaf43b182a3aba2d958`
  `feat: simplify media editor UX`
- `67d7ec9061b2ecaac8826ba1e39ebd1d47055872`
  `feat: integrate AI media drafts`

## 6. Accepted Gallery And Editor UX

Accepted direction:

- available Gallery cards show real visual media, not generic steady-state
  placeholders;
- animated GIFs may animate and MP4 cards use a real paused frame;
- the centered Unicode `▶` is functional;
- card actions are labelled `Details` and `Edit`;
- Details is player-first;
- ordinary editor terminology is `Edit media`, `Title`, `Description`, `Tags`,
  `Save`, and `Cancel`;
- tags are searched and added through one control;
- selected tags are removable display-name chips with `×`;
- canonical keys and automatic `Processed` semantics are hidden from ordinary
  editor controls;
- compact terminal-glass styling remains the accepted visual language;
- components and loading language should be reused consistently;
- Gallery is the flagship dense GIF/video picker experience.

Do not claim final rendered UX acceptance for the newest content-first cards,
simplified editor, or AI Draft changes.

## 7. Current AI Draft Truth

Imported-media identity-only endpoint:

```text
POST /api/media/{media_id}/locations/{location_id}/ai-suggestion-preview
```

Current AI contract:

- model: `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning`;
- prompt version: `framenest-media-suggestion-v3`;
- request explicitly sets `chat_template_kwargs.enable_thinking=false`;
- at most three optimized JPEG preview frames are sent;
- the original media file and absolute path are not uploaded;
- credentials remain server-side only;
- explicit cloud confirmation is required;
- no provider call occurs on Gallery, Details, or editor open;
- one separate editable AI Draft is returned with title, description, tags, and
  suggested filename;
- `Use draft` changes only unsaved manual editor state;
- `Discard draft` preserves manual work;
- metadata Save remains separate;
- no physical rename occurs;
- AI remains optional and manual editing works offline.

Worker-observed controlled live smoke evidence:

GIF draft:

- title: `Leonardo DiCaprio Clapping`
- description: `Leonardo DiCaprio in a suit claps his hands with a subtle smile, appearing to applaud in an office setting.`
- tags: `Leonardo DiCaprio`, `Clapping`, `Office`, `Reaction`, `Meme`
- suggested filename: `leonardo-di-caprio-clapping.gif`

MP4 draft:

- title: `Man Pointing While Holding Cup`
- description: `A man in a yellow shirt sits in a chair, holding a cup and pointing forward with his other hand.`
- tags: `Man`, `Pointing`, `Cup`, `Yellow Shirt`, `Chair`, `Indoor`,
  `Reaction`
- suggested filename: `dicaprio-pointing-cup.mp4`

Worker-observed live smoke details: two successful provider calls, no retry, no
metadata auto-save, no physical rename, no original upload, and no checked
response or log leakage of credentials, private paths, or provider internals.
The outer smoke wrapper later exited nonzero only because of a shell variable
naming mistake after successful Python evidence. Do not rerun those calls merely
to remove that reporting caveat.

## 8. Automated Evidence

Worker-observed evidence for the AI Draft slice:

- JavaScript syntax check passed.
- Focused tests: `248 passed`.
- Full suite: `1188 passed, 3 skipped`.
- `git diff --check` passed.
- Staged credential-shaped check passed.

This is Worker-observed evidence, not public CI proof and not independently
rerun by the Orchestrator.

## 9. Rendered Acceptance State

Earlier COOPERATOR-observed playback evidence:

- GIF animated.
- MP4 loaded and played.
- Switching MP4 to GIF stopped MP4.
- Seeking and close cleanup were not fully established in that earlier report.
- The original placeholder-heavy Gallery and admin-like editor UX were rejected
  and subsequently replaced by later commits.

Current state:

- Rendered acceptance of the newest content-first cards, simplified editor, and
  AI Draft integration remains pending.
- Disposable acceptance URL: `http://127.0.0.1:8765/`
- Only copied disposable media is involved.
- Original repository-local media inputs remained untouched.
- Static tests and HTTP smoke do not count as rendered acceptance.

Worker-observed disposable launcher state:

- Ephemeral root:
  `/var/folders/93/7fg3d5j17wxdkyh6nlyz239m0000gn/T/framenest-ai-mvp-w0oup8st`
- Database path:
  `/var/folders/93/7fg3d5j17wxdkyh6nlyz239m0000gn/T/framenest-ai-mvp-w0oup8st/catalog.sqlite3`
- Disposable library root:
  `/var/folders/93/7fg3d5j17wxdkyh6nlyz239m0000gn/T/framenest-ai-mvp-w0oup8st/library`
- Runtime directory:
  `$HOME/Library/Application Support/FrameNest/development/runtime`
- State file:
  `$HOME/Library/Application Support/FrameNest/development/runtime/server-state.json`
- Log path:
  `$HOME/Library/Logs/FrameNest/development/server.log`
- Port: `8765`
- PID observed at closeout: `47870`
- Process start identity observed in launcher state:
  `Tue Jun 30 22:48:43 2026`
- Launcher module: `framenest.server`
- Host: `127.0.0.1`
- Later normal cleanup should use the exact launcher-owned boundary with:
  `FRAMENEST_DATABASE_PATH` set to the disposable database path and
  `FRAMENEST_PORT=8765`. Do not use `pkill`, `killall`, port-based killing,
  process adoption, or automatic `SIGKILL`.

Classify the runtime as ephemeral Worker-observed state, not repository truth.
A future Worker must not revive it for implementation. It may interact with it
only under a new explicit ORCHESTRATOR cleanup or acceptance task.

Required COOPERATOR rendered checks:

1. real GIF and MP4 card visuals;
2. functional `▶`;
3. Details player size and controls;
4. `Edit media` terminology and tag UX;
5. `Analyze by AI`;
6. truthful cloud confirmation;
7. familiar loading animation;
8. editable AI Draft;
9. editing draft values;
10. `Use draft` changes manual fields without saving;
11. explicit Save;
12. no stale response, unexpected playback, exposed path, or confusing internal
    terminology.

## 10. Local Media Policy

Optional local acceptance inputs:

- `assets/gif/dicaprio_bravo.gif`
  `a5102a628c3409de6def8a21ebda8a30133abbbf3181336fc92727d50f92ce50`
- `assets/mp4/dicaprio.mp4`
  `520d43ee7f5853fec1aa9d72908b8d1a45a004a634a7558ff2889a32ff8e7ca9`

These files are not repository source, not public demo fixtures, and may exist
only in Michal's current local clone. They are locally excluded by exact
`.git/info/exclude` entries:

```text
/assets/gif/dicaprio_bravo.gif
/assets/mp4/dicaprio.mp4
```

They must never be staged or committed without a separate licensing and
repository-size decision. No future Worker may read, hash, inspect, copy,
analyze, upload, rename, move, or delete them without explicit task-specific
authority. `/Users/agile/Video` remains forbidden by default.

## 11. Demo Strategy Decision

Accepted future product/development direction, not yet implemented and not
authorized by this handoff:

```text
./framenest demo start
./framenest demo status
./framenest demo reset
```

An optional future `./framenest demo` alias may mean `demo start`.

Future demo mode should use an isolated demo database, runtime, and logs; create
its database deterministically from migrations and imports; never commit a
generated SQLite database; never mix with the persistent development catalog;
use only small original, generated, or clearly redistributable fixtures; avoid
depending on the two local DiCaprio inputs; provide an immediately populated
Gallery; let `reset` remove only positively identified demo-owned state; and
reuse the existing launcher/controller architecture rather than duplicating
process management.

Do not treat exact internal command behavior as authorized until a future Worker
inspects current launcher contracts under a new task.

## 12. Recommended Continuation Decision Tree

A fresh Orchestrator should first collect Michal's rendered acceptance result.

Then:

A. Safely stop and remove the disposable acceptance environment through its
exact launcher-owned boundary.

B. If acceptance exposes a concrete defect, authorize one bounded correction
before adding new scope.

C. If acceptance passes, the next primary implementation slice should be:

```text
Explicit physical filename rename
```

The rename workflow must be separately user-invoked; never triggered merely by
AI analysis, `Use draft`, or metadata Save; based on a reviewed editable
suggested filename; explicit about old and new basename; limited to a selected
available physical location; extension-preserving for the first slice; safe-name
validated; registered-root contained; symlink-escape protected; collision
checked; no overwrite by default; no directory move; no broad batch rename; no
automatic rename of multiple physical locations; database location update
coordinated with filesystem mutation; failure-aware with compensation or a
clearly proven recoverable order; accompanied by focused filesystem and
repository tests; and followed by explicit rendered/manual acceptance.

D. After rename, prioritize first-run library onboarding and import so an empty
installation can become useful without internal CLI knowledge.

E. After onboarding, implement the deterministic isolated demo workflow.

F. Refine the populated Gallery from real use.

G. Begin the thin Tauri shell only after the core add/import/analyze/edit/rename
Gallery path is coherent.

## 13. First-Run Onboarding Direction

The empty Gallery must become actionable. The user chooses or explicitly
provides a library. Scan is read-only. Import is explicit and idempotent. There
is no cloud request and no media rename, move, or delete during import.

Browser-development may temporarily use a launcher/library command. Final
desktop UX should use a narrowly scoped native directory picker. Do not create
an arbitrary-path HTTP endpoint.

## 14. Documentation Drift

`ROADMAP.md` and some older product wording may lag behind actual implemented
AI Draft, Gallery, and editor state. A future documentation update should
reconcile current implementation truth without rewriting architecture or
claiming final MVP acceptance.

Stale roadmap wording must not override newer verified code, `README.md`,
`GALLERY.md`, `AI_WORKSPACE.md`, commits, or COOPERATOR decisions.

Do not modify those documents from this handoff.

## 15. Explicit Immediate Non-Goals

The next task must not automatically expand into multi-model drafts, provider
Settings, persistent AI Draft storage, arbitrary collections, bulk rename,
filesystem reorganization, sidecars, cover pipeline, broad visual redesign,
full Tauri packaging, signing/notarization, Windows installer, NUC deployment,
remote synchronization, downloader, VLC integration, or automatic AI calls.

## 16. Closure Status

- Implementation boundary:
  `67d7ec9061b2ecaac8826ba1e39ebd1d47055872`
- Migration: `0007`
- ADR: `ADR-0030`
- Current Worker session: closes with the enclosing handoff commit
- Active Worker after push: none
- Rendered AI acceptance: pending
- Recommended next implementation after acceptance: explicit physical filename
  rename
- Next product slice afterward: first-run library onboarding/import
- Later developer/product aid: isolated deterministic demo mode
- Long-term shell: Tauri v2

This handoff grants no task authority.
