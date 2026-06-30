# FrameNest Orchestrator Handoff

## 1. Bootstrap Identity And Authority

You are a fresh Orchestrator instance assigned to the persistent,
vendor-neutral FrameNest `ORCHESTRATOR` role.

This file is the current repository-native Orchestrator handoff. It supersedes
all earlier versions of `NEXT_ORCHESTRATOR.md` where they conflict. It restores
context; it grants no repository-modification authority. Every concrete Worker
task still requires a new explicit ORCHESTRATOR prompt.

Public repository state must be independently verified before authorizing work.
Worker reports are evidence-bearing testimony, not repository truth. Do not
revive old Cline checkpoints, pending commands, temporary roots, or closed
sessions.

This handoff commit's own SHA cannot be written here before the commit exists.
Discover and verify the enclosing commit, its parent, subject, changed path
count, and raw file content from public repository state.

## 2. Current Repository Truth

- Project: `FrameNest`
- Repository: `https://github.com/cisarik/framenest.git`
- Normal local path: `/Users/agile/framenest`
- Branch: `main`
- Latest implementation boundary before this handoff commit:
  `caccd032a5e802e7c6188260db2d936290c4f549`
- Implementation subject: `feat: add local development launcher`
- Implementation parent: `24a2f66eca330a7cad1acd4c09d0b8875b61e792`
- Migration head: `0007`
- Highest accepted ADR: `ADR-0030`
- Expected worktree and index at handoff completion: clean.

The fresh Orchestrator must verify public `main`, the enclosing handoff commit
SHA, handoff commit parent, exact subject, changed path count, raw
`NEXT_ORCHESTRATOR.md`, and local/tracking/public equality where Worker
evidence is available. Do not claim a future handoff commit SHA from this file.

## 3. Human And Communication Context

The COOPERATOR is Michal. Communicate with him in Slovak, address him using
masculine grammatical forms, and use feminine grammatical forms for
Orchestrator self-reference. Worker prompts are in English. Worker reports are
in English and begin with `### Report for ORCHESTRATOR_CHAT`.

Distinguish verified fact, Worker-observed evidence, Cooperator-observed
evidence, inference, recommendation, and unresolved decision. Do not ask Michal
to perform ordinary Git, test, migration, build, or repository-maintenance
commands. Michal retains final product and UX acceptance. Ask at most one
focused product question when a real choice is necessary. Process ceremony must
never substitute for visible product progress.

## 4. Active Worker Lifecycle

The Worker session closed by commit
`24a2f66eca330a7cad1acd4c09d0b8875b61e792` remains historically closed. A new
Worker session was subsequently opened. The currently active concrete Worker
instance implemented the local development launcher ending at
`caccd032a5e802e7c6188260db2d936290c4f549`, and remains active after this
Orchestrator handoff task.

Do not rotate the Worker merely because the Orchestrator is rotating. The
COOPERATOR estimates approximately half of this Worker session's context
remains; this is a COOPERATOR estimate, not measured repository fact. The exact
usage must be supplied with every subsequent Worker report. Size tasks according
to remaining context.

Do not rely on the older `NEXT_WORKER.md` statement that no Worker is active as
current lifecycle truth. That statement was correct at its closeout commit and
predates the currently active Worker session. Do not update `NEXT_WORKER.md`
until this current Worker session is intentionally being closed. When context
pressure becomes material, the final task of that Worker session must replace,
validate, commit, and push `NEXT_WORKER.md`. Do not wait for complete context
exhaustion or uncontrolled auto-compaction before scheduling closeout.

The current concrete client/model may be Kimi K2.7 Code High through Cline, but
`WORKER` remains vendor-neutral.

## 5. Current Implemented Product Horizon

### Core Platform

FrameNest currently has a loopback-first FastAPI application, a packaged
same-origin vanilla HTML/CSS/JavaScript application, SQLite with SQLAlchemy
Core, Alembic migrations through `0007`, a device and library registry,
explicit read-only scanning, idempotent candidate import, persistent logical
media and physical locations, user-editable title, description, ordered
canonical tags, automatic virtual `Processed` behavior, catalog search and tag
filtering, metadata Details/workspace flows, and explicit AI boundaries with no
automatic cloud calls.

### Gallery

The Gallery is integrated and visually follows the accepted premium
terminal-glass direction: near-black background, restrained terminal-green
accents, compact glass surfaces, Gallery cards, search and tag filters, Details
dialog, metadata editing, representative card-preview behavior, and actual
Details media elements. Do not claim the Gallery is an accepted MVP yet.

### Secure Media Content Backend

Identity-only endpoint:

```text
GET /api/media/{media_id}/locations/{location_id}/content
```

Implemented in:

- `14d01d9543c82c9812c7f59f1a89ceaa2f3721c5`
- `9067139e6bbaf9fe6d9c0cf236e81ad86aefc920`
- `358241c56c012d331613aade2eb853abc98ab9cd`

The backend authorizes the media/location/library relationship, enforces
location availability, allows only exact GIF/MP4 kind-extension pairs, enforces
registered-root containment, rejects traversal, prevents symlink escape, uses a
stable single opened descriptor with size from `fstat`, supports full response
and one byte-range request, returns sanitized errors, remains read-only, exposes
no arbitrary path-serving API, and discloses no absolute paths.

### Details Playback Frontend

Commit `f73f5abb18054720f3de00f0837c8496f3664bde` implemented first
deterministic available physical-location selection, identity-only content URLs,
native `<video>` for MP4, real `<img>` for animated GIF, video controls,
metadata preload, `playsinline`, no autoplay, loading and unavailable states,
cleanup on replacement and close, stale-event token protection, separate card
representative-frame previews, and removal of the old Details representative-PNG
simulation.

Worker-observed evidence for that slice: focused frontend tests `155 passed`,
full suite `1119 passed, 3 skipped`, changed-test Ruff invocation passed, and
rendered browser acceptance was not performed. Treat this as Worker-observed
evidence, not public CI proof.

### Local Development Launcher

Commit `caccd032a5e802e7c6188260db2d936290c4f549` accepted:

```text
./framenest setup
./framenest start
./framenest start --no-open
./framenest stop
./framenest restart
./framenest restart --no-open
./framenest status
./framenest open
./framenest logs
./framenest logs --follow
```

The root entrypoint is executable fish and is a thin bootstrap wrapper. Python
`framenest-dev` owns runtime behavior. The environment uses uv-managed CPython
`3.13.14`; Poetry remains authoritative. Launcher `start` explicitly migrates
the development database, binds the server to `127.0.0.1`, waits for `/health`,
and keeps background state, database, and logs outside Git. Process identity is
verified before stop. Unrelated processes are not killed. There is no `pkill`,
`killall`, or automatic `SIGKILL`. The browser opens by default; it is external
and is not owned or terminated by FrameNest. Direct foreground entrypoints remain
available.

Worker-observed validation for the launcher: focused tests `58 passed`, full
suite `1154 passed, 3 skipped`, disposable start/status/logs/restart/stop smoke
passed, restart changed the managed PID, health and packaged `/` responded, and
the final worktree was clean.

Cooperator-observed evidence: Michal ran `./framenest start`; the launcher
worked as intended; the application opened successfully; the visual design was
perceived as cool and accepted as the current direction; the visible catalog was
empty and showed messages equivalent to `No tags.`, `No media matched this
catalog query.`, and `No catalog results.`

The empty Gallery is not evidence that the launcher failed. It reveals that the
persistent development catalog has no imported media/tag content and that
first-run onboarding/import remains missing.

## 6. Accepted Product Direction

### Gallery Role

Gallery is the flagship experience. It should feel like a premium dense
GIF/video/emoji picker, not an administration dashboard. Many useful media items
should be visible simultaneously. Real visual content matters more than
explanatory prose. Cards should be compact, content-first, and responsive.
Technical details belong in Details or metadata dialogs. Empty space and
marketing-like explanatory copy should be minimized. The current terminal-glass
visual language is broadly accepted; future work should refine rather than
restart the visual identity.

### Card Interaction

The media visual is the primary card control. Representative visual content
should communicate what the file contains. Representative frames are previews,
not playback. Bounded automatic representative cycling is preferred. Manual
Prev/Next/Start/Stop representative-frame controls are rejected. Decorative play
controls that do nothing are forbidden. Clicking the meaningful media surface
should lead naturally to real Details playback. Unavailable content should be
represented truthfully and compactly.

### Details And Metadata

Actual media title must be shown. GIF and MP4 playback must be real. Title,
description, canonical tags, and suggested filename remain manually editable
independently of AI. AI must create explicit reviewable drafts, must never
silently overwrite manual work, and must never make automatic cloud calls.
Credentials and providers remain outside the catalog database and source code.

### Responsive Direction

A large visual redesign is not currently requested. Responsive behavior should
be refined for future desktop window resizing, compact macOS window sizes,
ordinary laptop screens, and later Linux and Windows WebViews. The Gallery must
remain useful at narrower widths. Cards should reflow without becoming a verbose
one-column dashboard. Dialogs must remain usable within constrained desktop
windows.

## 7. Confirmed Open Defects And Acceptance Gaps

### Details Rendered Acceptance

Source and automated tests do not establish rendered usability. Rendered
acceptance must still prove that GIF visibly renders and animates; MP4 metadata
loads; native controls are visible; playback begins; `currentTime` advances;
seeking works; byte-range requests return and playback continues; replacing the
selected item stops old playback; closing Details stops playback and old network
activity; title, metadata, and Edit action remain correct; focus restoration
works; no absolute path appears in UI, responses, or headers; card previews
remain independent; and cleanup leaves no background playback.

### Media Event Ordering Risk

This is an evidence-based source risk, not a proven user-visible failure.
Current Details code assigns `video.src` or `img.src` and inserts the element
before all load/error handlers are assigned. A sufficiently fast cached load
could occur before those handlers are attached, leaving the UI hidden in the
loading state. The likely correction is to attach token-guarded handlers before
setting `src` and before exposing the element to loading. Cleanup and
stale-token semantics must remain intact. A future Worker must inspect the
current source and prove the correction with focused tests.

### `GALLERY.md` Defect

A confirmed sentence fragment remains around canonical-tag editing. The
fragment begins with text equivalent to `suggestions, keyboard and mouse
navigation...`. The intended opening should restore the canonical-tag editing
statement. This is a documentation defect, not evidence that playback code
failed.

### Empty-Catalog Onboarding Gap

This is a critical MVP gap. A new user can now start FrameNest easily, but the
application can still open with no media and no tags. The user currently lacks a
polished first-run path in the Gallery to select/register a media directory and
import it. An empty-state message alone is not sufficient MVP onboarding. This
gap blocks the feeling of a real end-user product.

## 8. Immediate Next Worker Task

The fresh Orchestrator must first verify the handoff commit publicly and inspect
current Worker usage. Then issue this bounded task to the currently active
Worker.

### Task Name

**Stabilize Details media loading**

Expected commit subject:

```text
fix: stabilize details media loading
```

### Expected Start

Use the enclosing Orchestrator-handoff commit as expected starting HEAD. Because
that SHA does not exist while this file is written, discover it publicly and
insert the exact SHA into the actual Worker prompt.

### Required Bootstrap

The Worker prompt must require current active Worker identity; reading
`AGENTS.md`, `AP.md`, `BOOT_WORKER.md`, current `NEXT_WORKER.md`, and current
`NEXT_ORCHESTRATOR.md`; repository root/origin/branch checks; clean worktree and
index; local/tracking/public equality; exact expected handoff parent and
subject; and current token usage included in the final report.

### Write Scope

Prefer only:

- `src/framenest/adapters/api/web/app.js`
- `tests/integration/test_local_web_media_playback.py`
- `tests/contract/test_local_web_application.py`
- `GALLERY.md`

Allow another existing web test file only if the current test structure proves
it is the correct existing contract location. Do not silently expand scope.

Do not modify backend media-content endpoint, launcher, migrations,
dependencies, lockfiles, AI code, Settings, Tauri files, handoff files, or
unrelated Gallery styling.

### Required Implementation

The task must require the Worker to inspect current `renderDetailsMedia()` and
cleanup lifecycle; attach all token-guarded media event handlers before
assigning `src`; ensure handlers exist before an image/video can begin loading;
handle immediate success, immediate error, cleanup during stale events, Details
close during loading, and replacement by another item; preserve controls,
`preload="metadata"`, `playsinline`, no autoplay, no automatic loop,
title-derived accessibility text, identity-only content URL, first
deterministic available location selection, card-preview behavior, video source
cleanup, and stale-token protection; avoid duplicate cleanup or stale handlers
mutating new Details state; and fix the `GALLERY.md` canonical-tag sentence
fragment without unrelated documentation rewriting.

### Required Tests

Tests must prove handlers are assigned before `src`; media cannot start loading
before handlers exist; video and GIF success reveal the element and clear
loading; immediate error produces unavailable state; stale success and stale
error do not mutate the current Details item; close during loading performs
cleanup; replacing an item invalidates old events; video cleanup pauses, removes
sources, and calls `load()`; card preview behavior remains present; playback
URLs use only media/location IDs; and `GALLERY.md` no longer contains the
fragment. Do not add a JavaScript framework or new dependency.

### Validation

Use focused affected tests, Python compile/import checks only where relevant,
full `poetry run pytest`, `git diff --check`, exact allowlist review, no Ruff
requirement unless Ruff has become a committed project dependency, and no
browser claim from static tests.

### Browser Capability Rule

The currently active Cline CLI Worker previously lacked a real browser/DOM
tool. If the execution client still lacks browser capability, source
stabilization and automated tests may pass, but rendered acceptance remains
explicitly deferred and must not be reported as rendered PASS. If a real
browser/DOM tool is available, the Orchestrator may separately authorize
rendered acceptance, but capability must be demonstrated before it becomes a
hard gate.

### Git And Report

Require one exact commit, `fix: stabilize details media loading`, exact staging,
normal push, no force-push, post-push verification, and clean final state.

Require a compact English report with status, start/end SHA, changed paths,
event-ordering correction, cleanup/stale-event behavior, focused/full tests,
docs correction, push verification, final worktree, current session token usage
supplied by the COOPERATOR, and rendered acceptance explicitly marked performed
or not performed.

## 9. Rendered Playback Acceptance Task

After the source stabilization commit is publicly verified, require a separate
acceptance step. Prefer a Worker/client with real browser or DOM automation. If
none is available, request one focused manual acceptance session from Michal,
because visual product acceptance belongs to the COOPERATOR. Do not misrepresent
static source inspection as rendered validation.

Use only a unique `/tmp/framenest-playback-*` root, disposable database,
disposable registered library, small valid synthetic GIF, small valid synthetic
MP4, non-conflicting loopback port, launcher environment overrides, and
`./framenest start --no-open`.

Do not use `/Users/agile/Video`. Do not inspect or alter Michal's real
persistent catalog.

Acceptance must verify disposable migration; disposable device/library
registration; synthetic media import; real launcher start; `/health`; Gallery
cards; GIF Details animation; MP4 Details controls; playback start; advancing
time; seeking; range behavior; Details item replacement stopping old playback;
close stopping playback/network activity; metadata and Edit; no absolute path
disclosure; launcher stop; and disposable cleanup. Do not perform a broad
screenshot-baseline mission. If a concrete defect appears, authorize one small
fix task rather than a general Gallery redesign.

## 10. MVP Roadmap After Playback Acceptance

### Priority A: First-Run Library Onboarding And Import

Highest-value product slice after playback is accepted:

> A user who starts FrameNest with an empty catalog can understand what to do
> and populate the Gallery without knowing internal registry/scan/import
> commands.

Before native Tauri folder selection exists, provide a coherent user-invoked
browser-development bridge that reuses current application boundaries. Inspect
the existing device/library registry and scan/import CLI before designing new
behavior. A likely temporary developer UX is a launcher namespace such as:

```text
./framenest library add <absolute-directory>
./framenest library scan <library>
./framenest library import <library>
```

or one carefully designed idempotent command that combines explicit
registration and import. Do not commit those exact command names without
inspecting existing CLI contracts.

Requirements: explicit user invocation, clear read-only scan semantics, no cloud
access, no media rename/move/delete, no hidden recursive mutation, no raw SQL,
idempotent registration/import, sanitized output, clear counts and errors,
compatibility with the persistent development catalog, private paths never in
public logs or API responses, no Worker access to `/Users/agile/Video` during
implementation/tests, and allowance for Michal to later invoke the command
himself with a directory he chooses.

The Gallery empty state should become compact and actionable: no alarming error
language, explain no media is imported, one primary action or instruction, no
verbose marketing copy, browser mode points to the supported local import
workflow, and future Tauri mode opens the native directory picker.

The polished native MVP path is native `Add library`, system folder picker,
explicit confirmation, read-only scan summary, import, and progressively
populated Gallery. The native shell should pass only the selected path through a
narrow trusted boundary. Do not create a general arbitrary-path HTTP endpoint.

### Priority B: Content-First Gallery

After import works, refine from real populated-state observation: automatically
available representative visuals, less placeholder-heavy presentation, dense
card layout, responsive card sizing, natural media-surface interaction, compact
title/tag presentation, bounded loading, useful empty/error states, smooth
Details opening, no fake play affordances, and no manual representative-frame
transport controls. Do not redesign the visual identity from scratch unless
Michal rejects it after seeing a populated Gallery.

### Priority C: Responsive Desktop-Window Behavior

Validate and refine narrow desktop widths, shorter window heights, dialog max
sizes, responsive card count, header/search wrapping, Details/media sizing,
metadata dialog usability, keyboard behavior, and focus behavior. The target is
a desktop WebView, not a mobile-first website.

### Priority D: Thin Tauri Shell

Begin only after media can be added/imported coherently, populated Gallery is
useful, Details playback is accepted, and browser-mode UX is stable enough to
wrap.

The first Tauri slice should be a thin shell spike proving existing vanilla
frontend in a Tauri WebView, single instance, supervised Python/FastAPI sidecar,
loopback-only connection, readiness handshake, clean backend shutdown,
window show/hide/focus, tray/menu-bar icon, minimal `Open FrameNest` /
`Hide/Show` / `Quit` menu, no duplicate domain logic, no AI/provider redesign,
and no updater or signing. Python backend remains authoritative. Do not assume
Poetry or a development `.venv` can ship inside the final app; sidecar packaging
needs a separate decision.

## 11. Cross-Platform Desktop Strategy

End users should receive native artifacts:

- macOS: `FrameNest.app`, later DMG/signing/notarization.
- Linux: AppImage first, later AUR/package integration suitable for
  CachyOS/Arch, optional RPM/deb as release maturity grows.
- Windows: NSIS setup executable or MSI, normal Start Menu/application launch.

End users should not be required to install fish, Poetry, uv, Python, Node, or
Rust.

Do not plan top-level commands:

```text
./framenest osx
./framenest cachyos
./framenest windows
```

Prefer a future namespace:

```text
./framenest desktop dev
./framenest desktop build
./framenest desktop package
```

Default behavior should target the current host. A future optional target flag
may use stable platform names:

```text
--target macos
--target linux
--target windows
```

Do not use `osx` as the canonical modern name. Do not make CachyOS a separate
application platform; treat it as Linux/Arch packaging.

Prefer a native CI matrix: macOS runner builds macOS artifacts, Linux runner
builds Linux artifacts, and Windows runner builds Windows artifacts.
Cross-compilation should not be assumed universally reliable. Signing,
notarization, installer publishing, and auto-update are later release concerns.

The current `./framenest` fish wrapper is the macOS/Linux development bridge. It
is not the future Windows end-user entrypoint. It may later delegate `desktop`
subcommands. Windows development may use the Python controller, Tauri tooling,
or a thin PowerShell wrapper if required. Do not introduce platform wrappers
before the Tauri scaffold creates a concrete need.

## 12. Desktop-Shell Security Requirements

Future desktop constraints: sidecar binds only to loopback; prefer an ephemeral
port for packaged desktop; do not expose backend externally; do not trust
arbitrary local web pages; establish a per-launch authentication/bootstrap
mechanism before packaged release; Tauri capability permissions stay minimal;
native filesystem selection is narrowly scoped; no arbitrary filesystem browsing
from web content; sidecar termination targets only the child owned by the shell;
Quit stops the sidecar; window close versus application Quit is intentionally
defined; tray behavior never leaves an unmanageable hidden backend; secrets
remain in an approved secret-store boundary; and the catalog database must not
contain provider API keys.

Do not prematurely choose exact IPC/auth implementation without a dedicated
design task.

## 13. Private Data And Media Rules

`/Users/agile/Video` is forbidden by default. No Worker may list, stat, scan,
hash, read, analyze, extract frames from, upload, rename, move, or delete from
it without explicit task-specific authority.

Implementation tests use synthetic media and temporary directories. A future
user-facing import command may be manually invoked by Michal against a directory
he selects; that does not grant a Worker authority to inspect the directory.
Cloud providers require explicit authority and confirmation. Credentials,
browser cookies, and unrelated catalogs remain forbidden.

## 14. Analytic Programming Discipline

Preserve one coherent outcome per Worker task; focused reading; exact write
allowlists; practical bounded authority; focused tests; normally one commit;
exact Git subject; normal push; public verification; stop after acceptance; no
adjacent self-authorization; at most one materially different retry after
failure; early `BLOCKED` for genuine capability, safety, or scope barriers; no
broad audits without explicit need; no giant rendered-baseline missions; and no
process ceremony replacing product progress.

Ruff is not currently a committed project dependency and must not be required as
a hard gate unless it is later added intentionally. Poetry remains authoritative
for project Python commands.

## 15. Orchestrator And Worker Context Management

Michal supplies current Worker token usage with reports. The Orchestrator must
track it. Task size must shrink as context pressure rises. Do not send a large
new implementation task when the Worker needs lifecycle closeout.

The closing Worker task must replace `NEXT_WORKER.md`, validate it, create one
exact commit, push, and report evidence. The current Worker is not yet being
closed. Orchestrator handoff and Worker handoff are independent lifecycles.
Rotating Orchestrator does not imply rotating Worker. Rotating Worker does not
imply rotating Orchestrator.

## 16. Fresh Orchestrator Bootstrap Behavior

The fresh Orchestrator must:

1. State that she is a fresh Orchestrator instance assigned to the persistent
   `ORCHESTRATOR` role.
2. Communicate with Michal in Slovak using feminine self-reference.
3. Verify the public handoff commit and actual `main`.
4. Verify SHA, parent, subject, only `NEXT_ORCHESTRATOR.md` changed, and raw
   file content.
5. Recognize that the current Worker session remains active.
6. Request or accept the latest token usage before sizing the next task.
7. Report restoration as `PASS`, `PARTIAL`, or `BLOCKED`.
8. Avoid asking Michal to repeat project history.
9. Avoid asking him to paste public repository files.
10. Issue the ready `Stabilize Details media loading` task to the current Worker
    after successful verification.
11. Verify that commit independently.
12. Arrange honest rendered playback acceptance.
13. Move directly to first-run library onboarding/import.
14. Then refine populated Gallery UX.
15. Begin Tauri only after the core Gallery path is functional enough to wrap.

## 17. Explicit Non-Goals For The Immediate Continuation

Do not jump immediately into full Tauri production packaging,
signing/notarization, Windows installers, auto-update, synchronization,
downloader, clipboard workflow, VLC integration, AI Settings, automatic AI
analysis, broad cover pipeline, arbitrary collections manager, broad
documentation audit, another architecture rewrite, or complete visual redesign.

The immediate objective remains:

> Make real playback trustworthy, make an empty installation easy to populate,
> and turn the accepted visual direction into a genuinely useful Gallery MVP.

## 18. Closure Status

- Implementation boundary:
  `caccd032a5e802e7c6188260db2d936290c4f549`
- Migration: `0007`
- ADR: `ADR-0030`
- Current active Worker: yes
- Current Orchestrator session: closes after the handoff commit
- Next Worker task: `Stabilize Details media loading`
- Next acceptance: synthetic rendered GIF/MP4 validation
- Next product slice: first-run library onboarding/import
- Product target: populated, responsive, premium Gallery MVP
- Later shell: Tauri v2, macOS-first, then Linux/CachyOS and Windows

This file restores context and grants no concrete task authority.
