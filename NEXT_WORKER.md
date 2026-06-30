# Next Worker Handoff

## 1. Authority And Lifecycle

This file is the current repository-native Worker handoff. It supersedes every
earlier version of `NEXT_WORKER.md` where they conflict.

This file restores context for a future Worker instance. It grants no task
authority, no modification authority, no Git authority, and no permission to
resume old execution-client state. A fresh Worker instance still requires a new
explicit ORCHESTRATOR task prompt before performing repository work.

The currently active Worker session is being intentionally closed by the
handoff commit that writes this file. After that commit is pushed and verified,
no active Worker instance remains. The next Worker must be a fresh Worker
instance assigned to the persistent, vendor-neutral FrameNest `WORKER` role.

The enclosing handoff commit SHA cannot be written into this file before the
commit exists. A fresh Worker must discover and verify it from Git/public remote
state. The expected handoff commit subject is:

```text
handout
```

Do not revive old Cline checkpoints, pending commands, terminal sessions,
temporary directories, or stale task state. Model, client, provider, and IDE do
not redefine the persistent `WORKER` role.

## 2. Repository State To Verify

- Repository: `https://github.com/cisarik/framenest.git`
- Normal local path: `/Users/agile/framenest`
- Branch: `main`
- Latest repository boundary before this Worker handoff commit:
  `1b3e1c7a8f312b64655eb6b9031ea2a37cc38a08`
- Boundary subject: `docs: hand off gallery MVP orchestration`
- Boundary parent: `caccd032a5e802e7c6188260db2d936290c4f549`
- Latest product implementation boundary:
  `caccd032a5e802e7c6188260db2d936290c4f549`
- Product implementation subject: `feat: add local development launcher`
- Product implementation parent:
  `24a2f66eca330a7cad1acd4c09d0b8875b61e792`
- Current migration head: `0007`
- Current highest accepted ADR: `ADR-0030`
- Expected final state after this handoff commit: clean worktree, clean index.

A fresh Worker must independently verify:

1. Git root is `/Users/agile/framenest`;
2. origin is `https://github.com/cisarik/framenest.git`;
3. branch is `main`;
4. public `main`, `origin/main`, and local `HEAD` match before work begins;
5. the enclosing Worker handoff commit subject is `handout`;
6. that commit changes only `NEXT_WORKER.md`;
7. the previous commit is `1b3e1c7a8f312b64655eb6b9031ea2a37cc38a08`;
8. raw `NEXT_WORKER.md` and `NEXT_ORCHESTRATOR.md` content match the public
   committed state;
9. the worktree and index are clean.

If any identity or cleanliness check fails, stop with `BLOCKED` unless the
new authoritative Orchestrator task explicitly authorizes a correction.

## 3. Session And Role Handoff

The previous Worker handoff at
`24a2f66eca330a7cad1acd4c09d0b8875b61e792` correctly closed an earlier Worker
session after Details playback source integration. A new Worker session was
then opened and completed:

- `caccd032a5e802e7c6188260db2d936290c4f549` —
  `feat: add local development launcher`
- `1b3e1c7a8f312b64655eb6b9031ea2a37cc38a08` —
  `docs: hand off gallery MVP orchestration`

This handoff closes that current Worker session as well. After this commit,
the correct lifecycle is:

1. the current Orchestrator session has already been handed off by
   `NEXT_ORCHESTRATOR.md`;
2. this current Worker session is closed by the enclosing `handout` commit;
3. Michal should start a fresh Orchestrator instance first;
4. that fresh Orchestrator should verify public state and then issue a new
   explicit Worker prompt to a fresh Worker instance.

Do not treat this file as the next task. It is context only.

## 4. Human And Communication Context

The COOPERATOR is Michal. Orchestrator communication with Michal is Slovak,
using masculine grammatical forms for Michal and feminine grammatical forms for
Orchestrator self-reference. Worker prompts are English. Worker reports are
English and begin exactly with:

```text
### Report for ORCHESTRATOR_CHAT
```

Worker reports must distinguish verified repository facts, Worker-observed
evidence, Cooperator-observed evidence, inference, recommendation, unresolved
decision, and blockers. Do not ask Michal to perform ordinary Git, test,
migration, build, or repository-maintenance commands. Michal owns final product
and UX acceptance, private-media authority, credential authority, and
irreversible decisions.

## 5. Implemented Product Horizon

### Core Platform

FrameNest is a local-first, privacy-conscious, cross-platform library for video
and animated media. Current implementation includes:

- loopback-first FastAPI application factory and Uvicorn runtime;
- packaged same-origin vanilla HTML/CSS/JavaScript web app at `GET /`;
- SQLite, SQLAlchemy Core, and Alembic migrations through `0007`;
- local device and library registry;
- explicit read-only library scan preview;
- explicit idempotent scan-candidate import;
- persistent logical media and physical locations;
- persistent display title, optional plain-text description, and ordered
  canonical tags;
- automatic built-in `Processed` workflow collection derived from durable tag
  saves;
- deterministic catalog read model with display-title search, canonical-tag
  AND filters, bounded pagination, virtual `All media`, and optional
  `Processed` scope;
- Details dialog and manual metadata workspace;
- explicit AI suggestion boundaries with no automatic cloud calls.

There is still no completed native end-user desktop app, arbitrary user-created
collection manager, suggested filenames, covers, thumbnails, persistent AI
Drafts, production deployment, systemd unit, Tailscale integration, or packaged
Tauri app.

### Gallery Direction

Gallery is the flagship product surface. The current browser application uses
the accepted terminal-glass visual direction: near-black background, restrained
terminal-green accents, compact glass surfaces, Gallery cards, search and tag
filters, Details dialog, metadata editing, representative card previews, and
actual Details media elements. This direction was accepted by Michal after
manual launcher use, but the Gallery is not yet an accepted MVP.

The product direction is a premium dense GIF/video/emoji-picker feeling, not an
administration dashboard. The UI should show many useful media items at once,
prefer real visual content over explanatory prose, keep cards compact and
content-first, and avoid fake controls.

## 6. Secure Media Content Backend

Identity-only endpoint:

```text
GET /api/media/{media_id}/locations/{location_id}/content
```

Implemented in:

- `14d01d9543c82c9812c7f59f1a89ceaa2f3721c5` —
  `feat: add secure media content endpoint`
- `9067139e6bbaf9fe6d9c0cf236e81ad86aefc920` —
  `fix: harden media content streaming`
- `358241c56c012d331613aade2eb853abc98ab9cd` —
  `fix: sanitize media descriptor cleanup`

Current properties:

- media, location, and library relationship authorization;
- location availability must be `available`;
- exact supported kind/extension allowlist:
  `video` + `.mp4` -> `video/mp4`,
  `animated_image` + `.gif` -> `image/gif`;
- registered-root containment;
- traversal rejection;
- symlink escape prevention;
- stable single opened descriptor;
- descriptor size from `fstat`;
- full response and one byte-range request support;
- read-only behavior;
- sanitized failures;
- no arbitrary path-serving API;
- no absolute path disclosure in responses, headers, or errors.

## 7. Details Playback Frontend

Commit `f73f5abb18054720f3de00f0837c8496f3664bde` —
`feat: play local media in details` — implemented:

- first deterministic available physical-location selection;
- identity-only content URLs built from media/location IDs;
- native `<video>` for MP4;
- real `<img>` for animated GIF;
- video controls;
- `preload="metadata"`;
- `playsinline`;
- no autoplay;
- no automatic loop;
- loading and unavailable states;
- cleanup on replacement and close;
- stale-event token protection;
- card representative-frame previews kept separate;
- removal of Details representative-PNG playback simulation.

Worker-observed evidence for that slice, not public CI proof:

- focused changed tests: `155 passed`;
- full `poetry run pytest`: `1119 passed, 3 skipped`;
- changed-test Ruff invocation passed;
- rendered browser acceptance was not performed.

Open source risk: current `renderDetailsMedia()` assigns `video.src` or
`img.src` and inserts the element before all load/error handlers are assigned.
A sufficiently fast cached load could happen before handlers exist and leave
the media hidden in a loading state. This is evidence-based source risk, not a
proven user-visible failure.

Confirmed documentation defect: `GALLERY.md` still contains a canonical-tag
editing sentence fragment beginning with text equivalent to:

```text
suggestions, keyboard and mouse navigation...
```

## 8. Local Development Launcher

Commit `caccd032a5e802e7c6188260db2d936290c4f549` —
`feat: add local development launcher` — added the accepted browser-development
launcher.

Commands:

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

Properties:

- root `framenest` entrypoint is executable fish;
- fish wrapper is thin bootstrap only;
- Python `framenest-dev` owns runtime behavior;
- setup uses uv-managed CPython `3.13.14`;
- Poetry remains dependency/environment authority;
- no dependency changes or `poetry.lock` changes were made;
- launcher `start` explicitly migrates the selected development database;
- managed server binds to `127.0.0.1`;
- launcher waits for verified `/health`;
- database, runtime state, and log paths live outside the Git worktree;
- process identity is validated before stop;
- unrelated processes are not killed;
- no `pkill`, `killall`, broad process search, or automatic `SIGKILL`;
- browser opens by default, but the browser tab/process is external and is not
  owned or terminated by FrameNest;
- direct foreground commands remain available.

Worker-observed validation:

- focused tests: `58 passed`;
- full suite: `1154 passed, 3 skipped`;
- disposable root-wrapper smoke passed with `start/status/logs/restart/stop`;
- health and packaged `/` responded;
- restart changed the managed PID;
- final worktree was clean.

Cooperator-observed evidence:

- Michal ran `./framenest start`;
- the launcher worked as intended;
- the application opened successfully;
- the visual design was perceived as cool and accepted as the current
  direction;
- the visible catalog was empty and showed messages equivalent to:
  `No tags.`, `No media matched this catalog query.`, and
  `No catalog results.`

The empty Gallery is not launcher failure. It means the persistent development
catalog has no imported media/tag content and first-run onboarding/import is
missing.

## 9. Current Orchestrator Handoff

Commit `1b3e1c7a8f312b64655eb6b9031ea2a37cc38a08` —
`docs: hand off gallery MVP orchestration` — replaced `NEXT_ORCHESTRATOR.md`.

It records:

- current repository truth through the launcher boundary;
- active Worker lifecycle before this Worker handoff;
- Cooperator launcher evidence;
- immediate `Stabilize Details media loading` task;
- separate rendered playback acceptance plan;
- empty-catalog onboarding/import gap;
- Gallery MVP direction;
- staged Tauri/macOS/Linux/Windows strategy;
- private data rules;
- Orchestrator bootstrap behavior.

After this Worker handoff commit, its statement that the Worker remains active
will be historically superseded by this file: the current Worker session is now
closed too. A fresh Orchestrator must verify both handoff files and current Git
truth rather than relying on any single stale lifecycle sentence.

## 10. Immediate Next Worker Task

The next implementation task should come from a fresh Orchestrator after public
verification and after Michal starts a fresh Worker instance.

Task name:

```text
Stabilize Details media loading
```

Expected commit subject:

```text
fix: stabilize details media loading
```

Expected start: the enclosing Worker handoff commit with subject `handout`.
Because that SHA cannot be known while this file is written, the fresh
Orchestrator must discover it publicly and insert it into the actual Worker
prompt.

Preferred write scope:

- `src/framenest/adapters/api/web/app.js`
- `tests/integration/test_local_web_media_playback.py`
- `tests/contract/test_local_web_application.py`
- `GALLERY.md`

Allow another existing web test file only if the current test structure proves
it is the correct location. Do not silently expand scope.

Do not modify backend media content code, launcher, migrations, dependencies,
lockfiles, AI code, Settings, Tauri files, handoff files, or unrelated Gallery
styling.

Required behavior:

- inspect `renderDetailsMedia()` and cleanup lifecycle;
- attach all token-guarded media event handlers before assigning `src`;
- ensure handlers exist before an image/video can begin loading;
- handle immediate success, immediate error, stale success/error, close during
  loading, and item replacement;
- preserve controls, metadata preload, `playsinline`, no autoplay, no loop,
  title-derived accessibility, identity-only URLs, first available location
  selection, card-preview behavior, video source cleanup, and stale-token
  protection;
- avoid duplicate cleanup and stale handlers mutating the new Details state;
- fix the `GALLERY.md` canonical-tag sentence fragment only.

Required tests:

- handlers assigned before `src`;
- media cannot start loading before handlers exist;
- video and GIF success reveal media and clear loading;
- immediate error produces unavailable state;
- stale success/error do not mutate current Details;
- close during loading performs cleanup;
- replacing item invalidates old events;
- video cleanup pauses, removes sources, and calls `load()`;
- card preview behavior remains present;
- playback URLs use only media/location IDs;
- `GALLERY.md` no longer contains the fragment.

Validation:

- focused affected tests;
- Python compile/import checks only where relevant;
- full `poetry run pytest`;
- `git diff --check`;
- exact allowlist review;
- no Ruff requirement unless Ruff becomes a committed project dependency;
- no rendered-browser claim from static tests.

If the fresh Worker/client lacks real browser/DOM capability, do not pretend
rendered acceptance happened. Mark it explicitly not performed.

## 11. Rendered Playback Acceptance After Stabilization

After the stabilization commit is publicly verified, arrange a separate
rendered acceptance step. Prefer a Worker/client with real browser or DOM
automation. If none is available, Michal may perform a focused manual
acceptance because visual product acceptance belongs to the COOPERATOR.

Use only:

- unique `/tmp/framenest-playback-*` root;
- disposable database;
- disposable registered library;
- small valid synthetic GIF;
- small valid synthetic MP4;
- non-conflicting loopback port;
- launcher environment overrides;
- `./framenest start --no-open`.

Do not use `/Users/agile/Video`. Do not inspect or alter Michal's real
persistent catalog.

Acceptance must verify migrated disposable catalog, disposable device/library,
synthetic imports, health, packaged root, populated cards, GIF animation, MP4
controls, playback start, advancing `currentTime`, seeking/range behavior,
replacement stopping old playback, close cleanup, metadata/Edit behavior, no
absolute path disclosure, launcher stop, and disposable cleanup.

Do not perform a broad screenshot-baseline mission. If rendered acceptance
finds a concrete defect, authorize one small fix task.

## 12. MVP Path After Playback Acceptance

Priority A: first-run library onboarding/import.

Goal:

> A user who starts FrameNest with an empty catalog can understand what to do
> and populate the Gallery without knowing internal registry/scan/import
> commands.

Investigate existing device/library registry and scan/import CLI before
designing new behavior. A likely temporary browser-development bridge may be a
launcher namespace or one idempotent command, but do not commit exact command
names before inspecting current CLI contracts.

Requirements:

- explicit user invocation;
- clear read-only scan semantics;
- no cloud access;
- no media rename, move, or delete;
- no hidden recursive mutation;
- no raw SQL;
- idempotent registration/import;
- sanitized output;
- clear counts and errors;
- persistent development catalog compatibility;
- private paths never in public logs or API responses;
- Workers must not access `/Users/agile/Video`;
- Michal may later invoke the command himself with a directory he chooses.

Gallery empty state should become compact and actionable: no alarming error
language, explain no media is imported, one primary action or instruction,
minimal prose, browser mode points to the supported import workflow, future
Tauri mode opens native directory picker.

Priority B: populated, content-first Gallery refinement.

Likely slices: automatic representative visuals, less placeholder-heavy
presentation, dense card layout, responsive card sizing, natural media-surface
interaction, compact title/tag presentation, bounded loading, useful
empty/error states, smooth Details opening, no fake play affordances, and no
manual representative-frame transport controls.

Priority C: responsive desktop-window behavior.

Validate narrow desktop widths, shorter window heights, dialog max sizes,
responsive card count, header/search wrapping, Details/media sizing, metadata
dialog usability, keyboard behavior, and focus behavior.

Priority D: thin Tauri shell.

Begin only after media can be added/imported, populated Gallery is useful,
Details playback is accepted, and browser-mode UX is stable enough to wrap.
The first Tauri slice should be a thin shell spike, not production packaging.

## 13. Cross-Platform Desktop Direction

End-user target artifacts:

- macOS: `FrameNest.app`, later DMG/signing/notarization;
- Linux: AppImage first, later AUR/package integration suitable for
  CachyOS/Arch, optional RPM/deb as maturity grows;
- Windows: NSIS setup executable or MSI.

End users should not be required to install fish, Poetry, uv, Python, Node, or
Rust.

Do not plan current top-level commands:

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

Future target flags should use `macos`, `linux`, and `windows`; do not use
`osx` as canonical. Treat CachyOS as Linux/Arch packaging, not a separate app
platform.

Prefer native CI matrix builds by platform. Do not assume universal
cross-compilation. Signing, notarization, publishing, and auto-update are later
release concerns.

The current `./framenest` fish wrapper is the macOS/Linux development bridge,
not the Windows end-user entrypoint. Do not introduce platform wrappers before
the Tauri scaffold creates a concrete need.

## 14. Desktop-Shell Security Direction

Future desktop shell constraints:

- sidecar binds only to loopback;
- prefer ephemeral port for packaged desktop;
- do not expose backend externally;
- do not trust arbitrary local web pages;
- establish per-launch authentication/bootstrap before packaged release;
- keep Tauri permissions minimal;
- native filesystem selection is narrowly scoped;
- no arbitrary filesystem browsing from web content;
- sidecar termination targets only shell-owned child;
- Quit stops the sidecar;
- window close versus Quit must be intentionally defined;
- tray behavior must not leave an unmanageable hidden backend;
- secrets remain in an approved secret-store boundary;
- catalog database must not contain provider API keys.

Do not choose exact IPC/auth implementation without a dedicated design task.

## 15. Private Data And Security Rules

`/Users/agile/Video` is forbidden by default. No Worker may list, stat, scan,
hash, read, analyze, extract frames from, upload, rename, move, or delete from
it without explicit authority for that exact task.

Implementation tests must use synthetic media and temporary directories. A
future user-facing import command may be manually invoked by Michal against a
directory he selects; that does not grant Worker authority to inspect that
directory. Cloud providers require explicit authority and confirmation.
Credentials, browser cookies, private keys, unrelated catalogs, and shell
history remain forbidden.

## 16. Worker Bootstrap For The Next Session

A fresh Worker instance must:

1. Read `AGENTS.md`, `AP.md`, `AP_WORKER.md`, `BOOT_WORKER.md`, current
   `NEXT_ORCHESTRATOR.md`, and this `NEXT_WORKER.md`.
2. Treat both NEXT files as context only, never as task authority.
3. Verify repository root, origin, branch, clean worktree/index, public refs,
   expected start commit, subject, parent, and changed paths before modifying
   files.
4. Follow only the new explicit Orchestrator prompt.
5. Use Poetry for project Python commands.
6. Modify only paths authorized by the task.
7. Do not install dependencies unless explicitly authorized.
8. Do not access private media, credentials, browser profiles, shell history,
   or unrelated user files.
9. Report in English beginning with `### Report for ORCHESTRATOR_CHAT`.
10. Include current token/context usage when the Cooperator supplies it.

If the fresh Worker lacks a capability required by the task, it must stop
before modification and report `BLOCKED`.

## 17. Analytic Programming Discipline

Preserve:

- one coherent outcome per Worker task;
- focused reading;
- exact write allowlists;
- explicit Git authority;
- practical bounded validation;
- normally one exact commit;
- normal push;
- public verification;
- no adjacent self-authorization;
- at most one materially different retry after failure;
- early `BLOCKED` for genuine capability, safety, repository, or scope
  barriers;
- no broad audits without need;
- no giant rendered-baseline missions;
- no process ceremony replacing product progress.

Ruff is not currently a committed project dependency and must not be required as
a hard gate unless intentionally added later. Poetry remains authoritative for
project Python commands.

## 18. Closure Status

- Repository before this Worker handoff commit:
  `1b3e1c7a8f312b64655eb6b9031ea2a37cc38a08`
- Expected Worker handoff commit subject: `handout`
- Latest product implementation boundary:
  `caccd032a5e802e7c6188260db2d936290c4f549`
- Migration: `0007`
- ADR: `ADR-0030`
- Current Orchestrator session: already handed off by `NEXT_ORCHESTRATOR.md`
- Current Worker session: closes after this handoff commit
- Active Worker after commit: no
- Next Orchestrator action: fresh Orchestrator verifies public state
- Next Worker action: wait for a new explicit Orchestrator prompt
- Next implementation task: `Stabilize Details media loading`
- Next acceptance: synthetic rendered GIF/MP4 validation
- Next product slice: first-run library onboarding/import
- Product target: populated, responsive, premium Gallery MVP
- Later shell: Tauri v2, macOS-first, then Linux/CachyOS and Windows

This file restores context and grants no concrete task authority.
