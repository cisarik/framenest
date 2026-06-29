# Next Worker Handoff

## 1. Title And Authority

This file is the current canonical repository-native Worker handoff. It supersedes every earlier version of `NEXT_WORKER.md` in Git history.

It is a non-authoritative context-restoration document. It grants no task authority.

A fresh Worker instance still requires a new authoritative ORCHESTRATOR prompt before performing any repository work.

## 2. Repository State

- Repository: `https://github.com/cisarik/framenest.git`
- Normal local path: `/Users/agile/framenest`
- Branch: `main`
- Final implementation HEAD: `0e60b0f83cc928d6d7911326afb50f0f21411447`
- Subject: `fix: stabilize gallery dialog interactions`
- Parent: `fcf73de1749f980ca6b923e39fec8c904fcd0e42`
- Current migration head: `0007`
- Current highest accepted ADR: `ADR-0030`
- Expected state: clean worktree, clean index
- Public verification: a fresh Worker must independently verify HEAD, `origin/main`, and `refs/heads/main` before starting work.

## 3. Worker Lifecycle

The current GLM-5.2 Worker session is permanently closed. No active Worker instance remains.

The persistent `WORKER` protocol role continues and requires a fresh instance plus a new authoritative ORCHESTRATOR prompt for future work.

The next concrete Worker implementation is expected to be a fresh Codex Worker in Cursor IDE, subject to a new ORCHESTRATOR prompt.

Model, client, and provider do not redefine the `WORKER` role.

## 4. Implemented Product Horizon

The following are committed and implemented on `main`:

- Local server: FastAPI application factory, Uvicorn loopback-first runtime, typed health endpoint.
- Packaged vanilla HTML/CSS/JavaScript web application served same-origin at `GET /`.
- SQLite/Alembic persistence through migration `0007`.
- Device and library registration via `framenest-catalog` CLI.
- Explicit read-only library scan preview.
- Explicit idempotent scan-candidate import.
- Catalog with display-title search, canonical-tag AND filters, bounded offset pagination.
- Persistent display title, optional plain-text description, and ordered canonical tags.
- Automatic built-in `Processed` workflow collection derived from durable tag saves.
- Terminal-glass sticky application header with server-health and AI-status controls.
- Header command search with title and tag suggestions, current-page fallback-title matching.
- Canonical-tag toggle pills with `aria-pressed` semantics, no duplicate active-filter region.
- Gallery grid with compact media cards, deterministic visual placeholders.
- On-demand representative-frame preview using the existing local media-analysis API.
- Bounded in-memory session preview cache (LRU, max 12).
- Single active frame-cycling preview, automatic cycling, no manual frame controls.
- Media-details dialog with one unified visual surface, collapsed technical details.
- Metadata edit dialog with complete form, always-visible Save/Discard footer.
- Collapsible Library tools section.
- Settings → AI shell dialog (provider configuration not yet implemented).
- `prefers-reduced-motion` support throughout.
- `dialog:not([open]) { display: none }` ensures no dialog is visible on startup.

## 5. Critical COOPERATOR UX Direction

These are explicit product requirements from Michal:

1. Gallery is the main product experience.
2. Cards must ultimately show real visual media content, not remain placeholder-only.
3. Real local thumbnail/frame loading should feel automatic and content-first, while staying bounded and safe.
4. Decorative Play glyphs that do nothing are forbidden.
5. Clicking the media surface should lead naturally into the media detail/playback experience.
6. The Details heading should be the media title, not generic `Media details`.
7. Representative frames are an automatic preview, not a manually paginated mini-gallery.
8. Do not add `Prev`, `Next`, `Start`, or `Stop` for representative frames.
9. Full GIF/video playback must be real playback, not frame switching.
10. A future secure read-only media-content boundary must handle path safety and MP4 Range requests.
11. Search remains a terminal-style primary input.
12. Search must support Arrow Up/Down and Enter.
13. Suggestions should eventually show a small static visual preview on black beside the title.
14. Suggestions open only when actual results exist.
15. Exactly one clear control may be visible.
16. Metadata dialog must expose the complete form plus always-visible Save and Discard.
17. The main app must remain compact and free of verbose explanatory text.
18. `View details` as a prominent side button is not the preferred final interaction; content/card interaction should carry the flow.
19. AI must be visually recognizable in the product through a future honest `Analyze` action with a magic-wand treatment and restrained gradient/glow.
20. Do not present AI as configured when it is unavailable.
21. A future Cover workflow should offer `Generate Cover` and user cover selection, but it requires a deliberate persisted-cover architecture.
22. The accepted visual direction is premium 2026 terminal glass: near-black, restrained terminal green, glass surfaces, fast subtle effects, content-first layout.
23. The final desktop direction remains a native cross-platform webview/tray shell, with Tauri v2 already accepted unless a later dedicated ADR changes it.
24. The COOPERATOR is dissatisfied with repeated source-contract-only UI work; future UI tasks require actual rendered acceptance and screenshot-driven checks before commit where practical.
25. Modal headers should be black with green terminal-style title text.
26. Close buttons should use `✕` (Unicode), not the word `Close`.
27. Dialog animations should include blur+fade-in for a wow effect.

## 6. Known Unresolved Scope

The following are explicitly unimplemented or incomplete:

- Automatic real visual Gallery thumbnails (currently requires explicit click).
- Durable thumbnail/cover cache.
- Full GIF playback.
- Full MP4 playback.
- Safe media-content endpoint.
- HTTP Range requests for MP4 streaming.
- Search-result visual thumbnails.
- Final card-to-detail interaction model.
- AI Analyze entry point in Gallery/Details.
- Provider Settings and secure credentials.
- Generate Cover and cover selection.
- Tauri shell and tray integration.
- Download/copy workflow.
- Remote-device synchronization.
- Dialog blur+fade-in animations (CSS transitions not yet implemented for dialog open).

## 7. Known Current Risks

- Vanilla JS UI has accumulated source-contract tests that do not prove rendered UX.
- Actual browser/rendered acceptance must accompany future UI work.
- Current analysis frames are ephemeral and not durable covers.
- No real private-media task may assume access to `/Users/agile/Video`.
- Current public implementation may still require visual cleanup despite passing tests.
- Do not begin another broad UI rewrite without screenshots and explicit acceptance criteria.
- The preview click handler is attached during card rendering; after `loadCatalog()` rerenders cards, cached previews are shown but cycling is not automatically restarted.
- The metadata dialog `#metadata-workspace` `hidden` attribute is managed by `renderMetadataWorkspace()`; the footer (Save/Discard) is now outside the workspace div and always visible in the dialog.

## 8. Recommended Next Task

`Secure local media playback and visual Gallery foundation`

The fresh ORCHESTRATOR should first decide its exact scope, likely separating:

1. Safe read-only media-content endpoint and MP4 Range support.
2. Real GIF/video playback in Details.
3. Bounded automatic Gallery thumbnail/frame loading.
4. Visual search-result thumbnails.

Do not grant this task through `NEXT_WORKER.md`.

## 9. Security And Privacy

- `/Users/agile/Video` is private and inaccessible by default.
- No list, stat, read, hash, scan, or analysis without explicit authority.
- No cloud upload without separate confirmation.
- No credential exposure.
- No filesystem mutation without explicit authority.
- No public binding by default.
- No real-catalog migrations without authority.

## 10. Protocol Rules

- COOPERATOR does not normally execute Git/repository commands.
- WORKER handles repo gates, implementation, tests, commit, push, and local verification under explicit authority.
- ORCHESTRATOR independently verifies public commits.
- NEXT/BOOT files restore context but grant no task.
- Reports must distinguish public evidence from local runtime evidence.
- One Worker instance at a time under current AP v1 topology.

## 11. Restart Instructions

A fresh Worker must:

1. Receive a new ORCHESTRATOR prompt.
2. Verify repository truth (HEAD, `origin/main`, `refs/heads/main`).
3. Read `BOOT_WORKER.md`.
4. Read `AP.md`.
5. Read `AP_WORKER.md`.
6. Read this `NEXT_WORKER.md`.
7. Inspect the relevant current implementation.
8. Not revive this closed session's authority.
