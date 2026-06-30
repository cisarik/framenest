# Next Worker Handoff

## 1. Authority and lifecycle

This file is the current canonical repository-native Worker handoff.
It supersedes every earlier version of `NEXT_WORKER.md` in Git history.

It is a non-authoritative context-restoration document. It grants no task authority.
A fresh Worker instance still requires a new authoritative ORCHESTRATOR prompt before performing any repository work.

The current concrete Kimi K2.7 Code/Cline Worker session is permanently closed after this handoff commit.
No active Worker instance remains.

Model, client, and provider do not redefine the persistent `WORKER` role.
Old Cline checkpoints, pending commands, and temporary task state must not be resumed.

## 2. Repository state

- Repository: `https://github.com/cisarik/framenest.git`
- Normal local path: `/Users/agile/framenest`
- Branch: `main`
- Implementation boundary before this handoff commit: `f73f5abb18054720f3de00f0837c8496f3664bde`
- Implementation subject: `feat: play local media in details`
- Implementation parent: `358241c56c012d331613aade2eb853abc98ab9cd`
- Current migration head: `0007`
- Current highest accepted ADR: `ADR-0030`
- Expected final repository state: clean worktree, clean index
- Public verification: a fresh Worker must independently verify HEAD, `origin/main`, and `refs/heads/main` before starting work. The enclosing handoff commit SHA, public main, and its parent must be discovered and verified, not taken from this file.

## 3. Implemented product horizon

### Existing foundation

- Loopback-first FastAPI application factory and Uvicorn runtime.
- Packaged vanilla HTML/CSS/JavaScript web application served same-origin at `GET /`.
- SQLite, SQLAlchemy Core, and Alembic migrations through `0007`.
- Registered device and library registry via `framenest-catalog` CLI.
- Explicit read-only library scan preview.
- Explicit idempotent scan-candidate import into the persistent media catalog.
- Searchable deterministic media catalog with display-title search, canonical-tag AND filters, and bounded offset pagination.
- Persistent display title, optional plain-text description, and ordered canonical tags up to 32 per medium.
- Automatic built-in `Processed` workflow collection derived from durable tag saves.
- Packaged Gallery with logical-media cards, representative-frame previews, Details dialog, and metadata workspace.
- Explicit AI boundaries with no automatic cloud calls; suggestion review requires `--confirm-cloud-upload` and a configured provider key.

### Secure content backend

Identity-only endpoint:

`GET /api/media/{media_id}/locations/{location_id}/content`

Implemented in commits:

- `14d01d9543c82c9812c7f59f1a89ceaa2f3721c5` — `feat: add secure media content endpoint`
- `9067139e6bbaf9fe6d9c0cf236e81ad86aefc920` — `fix: harden media content streaming`
- `358241c56c012d331613aade2eb853abc98ab9cd` — `fix: sanitize media descriptor cleanup`

Properties:

- Media, location, and library relationship authorization.
- Location availability must be `available`.
- Exact kind/extension allowlist: `video` + `.mp4` → `video/mp4`, `animated_image` + `.gif` → `image/gif`.
- Registered-root containment and symlink escape prevention.
- Complete streaming and single byte-range request support.
- Stable single opened file descriptor; descriptor size from `fstat`.
- Idempotent cleanup and sanitized failures.
- No arbitrary path-serving API and no absolute-path disclosure in responses, headers, or errors.

### Details frontend integration

Commit `f73f5abb18054720f3de00f0837c8496f3664bde` — `feat: play local media in details` — implements:

- First deterministic `available` location selection.
- Content URLs built only from `media_id` and `location_id` via `mediaContentUrl()`.
- Real native `<video>` for MP4 with `controls`, `preload="metadata"`, `playsinline`, no autoplay, and no automatic loop.
- Real `<img>` for animated GIF with `alt` text based on the displayed title.
- Loading and unavailable states.
- Explicit `cleanupDetailsMedia()` on Details replacement and close.
- `detailsMediaToken` stale-event checking so old handlers do not affect the current dialog.
- Preservation of card representative-frame preview behavior.
- Removal of Details representative-PNG playback simulation.

Worker-observed validation evidence (not public CI proof):

- Focused changed tests: `155 passed`.
- Full `poetry run pytest`: `1119 passed, 3 skipped` (expected real-tool / NVIDIA skips).
- Changed-test Ruff checks: passed.
- Rendered browser acceptance was explicitly not performed in this slice.

## 4. Confirmed open work and risks

### Rendered acceptance is still required

A future Browser-capable task must validate using only disposable synthetic media and a disposable catalog under a unique `/tmp/framenest-*` root:

- Real GIF appears in Details.
- Real MP4 metadata loads and native controls appear.
- Playback starts and `currentTime` advances.
- Seeking works and exercises byte-range requests.
- Closing or replacing Details stops playback and old network activity.
- Actual title, metadata, and Edit action remain functional.
- No absolute path appears in UI, response body, or headers.
- The server binds to loopback only.
- The temporary server and task root are cleaned up.

The private path `/Users/agile/Video` remains forbidden without new task-specific authority.

### Potential media-event ordering race

Evidence-based risk requiring inspection, not a proven runtime failure:

- Current `renderDetailsMedia()` in `src/framenest/adapters/api/web/app.js` sets `src` and inserts the element before assigning all load/error handlers.
- A very fast or cached load might complete before the handler assignment.
- The fresh Orchestrator should authorize a targeted fix if inspection confirms it.
- The likely correction is to attach handlers before setting `src` and before exposure to loading, while preserving `detailsMediaToken` and `cleanupDetailsMedia()` behavior.
- Rendered acceptance must verify the final behavior.

### Confirmed `GALLERY.md` prose defect

The playback insertion left a sentence fragment. The text currently begins:

`suggestions, keyboard and mouse navigation, rounded removable chips, an explicit × control, ...`

The missing opening should restore the intended canonical-tag statement, approximately:

`Canonical tag editing should feel like a premium local interaction: searchable suggestions, keyboard and mouse navigation, ...`

This is a documentation correction, not evidence that playback code failed.

### Environment note

A stale `framenest-server` process had been observed in earlier work but was outside this task authority and was not touched. A future task must independently inspect port/process state and must not kill an unrelated process without explicit authority.

## 5. Recommended next sequence toward MVP

These are recommendations only and grant no task authority.

Recommended immediate next slice: **Stabilize and render-validate Details playback**.

Prefer one Browser-capable Worker task that:

1. Inspects and, if confirmed, fixes the media handler ordering risk.
2. Fixes the small `GALLERY.md` sentence fragment.
3. Creates only synthetic GIF/MP4 media and a disposable migrated catalog under `/tmp`.
4. Performs focused rendered acceptance of GIF, MP4, seek/range behavior, and cleanup.
5. Runs focused and full automated validation.
6. Creates one exact commit.

If the chosen execution client has no real browser/DOM capability, do not pretend static source checks are rendered acceptance. Separate the small source/document correction from a later Browser-capable acceptance task.

After playback is visibly accepted, the Orchestrator should choose the smallest next Gallery MVP slice based on observed UX. Likely priorities include:

- Content-first visual Gallery cards.
- Automatic bounded representative visuals rather than placeholder-heavy cards.
- Natural media-surface interaction leading to Details/playback.
- Dense, useful Gallery presentation.

Do not jump yet to:

- Tauri packaging.
- VLC integration.
- AI Settings.
- Automatic AI analysis.
- Downloader or clipboard workflows.
- Synchronization.
- Broad cover-pipeline work.
- Unrelated documentation audits.

## 6. Product and security direction

Preserve succinctly:

- Gallery is the flagship product surface.
- It should resemble a premium dense visual GIF/video picker, not an administration dashboard.
- Real visuals and truthful controls matter; decorative controls that do nothing are forbidden.
- Representative frames are previews, not playback.
- Metadata editing remains manual-first and independent of AI.
- Cloud calls require explicit action and confirmation.
- Private media, catalogs, credentials, and providers require explicit task authority.
- Tauri v2 remains a future native-shell direction, not the immediate next task.
- `/Users/agile/Video` is private and inaccessible by default.

## 7. Fresh Worker bootstrap

A fresh Worker must:

1. Read `AP.md`, `AGENTS.md`, `BOOT_WORKER.md`, and this `NEXT_WORKER.md`.
2. Verify public and local repository state before work.
3. Follow only the new explicit ORCHESTRATOR task.
4. Use Poetry for project Python commands.
5. Respect exact write allowlists and Git gates.
6. Stop early on genuine blockers.
7. Keep reports compact and in English, beginning with `### Report for ORCHESTRATOR_CHAT`.
