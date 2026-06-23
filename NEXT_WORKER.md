# Next Worker Handoff

## 1. Handoff Purpose

The current Worker session is intentionally closed.

This file transfers repository state and context to a future Worker session. It does not grant modification authority.

A new Worker must still receive a separate authoritative task from the Orchestrator before changing files, running broad commands, or performing Git operations.

## 2. Required Reading Order for a Fresh Worker

A fresh Worker should read repository context in this order:

1. [AGENTS.md](AGENTS.md)
2. [BOOT_WORKER.md](BOOT_WORKER.md)
3. [AP_WORKER.md](AP_WORKER.md)
4. [NEXT_WORKER.md](NEXT_WORKER.md)
5. Task-specific files named by the Orchestrator
6. The separate authoritative Worker task

The Worker may consult [AP.md](AP.md) for the full protocol and [AP_ORCHESTRATOR.md](AP_ORCHESTRATOR.md) for role-boundary context when useful.

## 3. Repository Identity

- Repository: `https://github.com/cisarik/framenest.git`
- Verified local path used in the closing session: `/Users/agile/framenest`
- Branch: `main`
- Visibility: public repository
- Stage A substantive commit SHA: `fcf348c6c662a62ae8b9c137d961177362b7268c`
- Handoff commit: follows the Stage A commit and should be resolved from current `HEAD` by the next Worker rather than guessed from this file.

## 4. Completed Work

The committed foundation now includes:

- Repository safety files.
- Security policy.
- Analytic Programming protocol.
- Orchestrator and Worker handbooks.
- Worker bootstrap.
- Product foundation.
- Normative specification.
- Staged roadmap.

Known commit chain:

- `1ee4f46ef9100cee77c1398163510ec12ef5d5bd`
- `98327592482275b368d1946b3dcfa8d8d0a4aadd`
- `7c85208ab538a6dab6f0aaed84148bafaac2de8f`
- `fcf348c6c662a62ae8b9c137d961177362b7268c`

This file intentionally does not name a future Stage B commit SHA.

## 5. Current Implementation State

No application source code exists.

No server exists.

No frontend exists.

No package or environment configuration exists.

No tests exist.

No architecture ADR exists.

No framework has been selected.

The repository is documentation-only.

## 6. Approved Product Invariants

- FrameNest remains local-first.
- Premium gallery and acquisition are flagship capabilities.
- The server aggregator is optional for desktop operation.
- Server-first implementation priority begins on macOS.
- Fedora NUC deployment comes after the server foundation works locally.
- Remote access direction is Tailscale-only unless superseded by an approved decision.
- External VLC comes first for full playback.
- One logical media item may have multiple physical locations.
- Portable sidecars plus local indexes are the approved metadata direction.
- Canonical tags are English.
- Source platform is the final directory tag.
- Provider secrets must not be distributed to ordinary clients.

## 7. Environment Evidence

The initial audit observed an Apple Silicon / arm64 macOS development host.

Observed tools included:

- fish available at `/opt/homebrew/bin/fish`, version `4.2.1`.
- Git available at `/opt/homebrew/bin/git`, version `2.41.0`.
- Python 3 available at `/opt/homebrew/bin/python3`, version `3.14.6`.
- uv available, version `0.8.23`.
- Poetry available, version `2.1.4`.
- pyenv available, version `2.6.7`.
- Node.js available, version `v25.1.0`.
- npm available, version `11.6.2`.
- pnpm not available through PATH.
- Bun not available through PATH.
- Rust available through `/Users/agile/.cargo/bin`, with `rustc 1.65.0` and `cargo 1.65.0`.
- FFmpeg and ffprobe available, version `8.1.2`.
- yt-dlp available, version `2026.06.09`.
- VLC available at `/Applications/VLC.app/Contents/MacOS/VLC`; `vlc` was not available through PATH.

These are environment observations only. They are not approved project versions.

## 8. Open Decisions

The following architecture decisions remain deferred and must not be silently selected:

- Frontend framework.
- Python version and tooling.
- API framework.
- ORM or query strategy.
- Manifest format.
- Schema.
- IPC.
- Authentication above Tailscale.
- Synchronization protocol.
- FFmpeg distribution.
- yt-dlp packaging and update strategy.
- Player invocation.
- Thumbnail formats and sizes.
- Full-text search.
- Packaging, signing, and update mechanisms.
- Telemetry.
- License.

## 9. Exact Recommended Next Worker Task

The next bounded task should be an architecture-decision evidence package, not application scaffolding.

It should inspect current documentation and prepare comparison material for the Orchestrator covering only this first decision group:

- Supported Python version.
- Python environment and dependency manager.
- Initial server API framework.
- Repository layout boundary.
- Local development configuration strategy.

The next Worker must not decide these options by itself. The Orchestrator will provide the authoritative task separately.

## 10. Safety State

Expected closeout state:

- Clean working tree after closeout.
- No secrets introduced.
- No package installation performed.
- No generated or runtime files created.
- All current work pushed to `origin/main`.
- Public commit verification expected from the Orchestrator.

## 11. Known Risks

- Documentation can still contain inconsistencies requiring future review.
- Architecture remains intentionally unresolved.
- Product breadth must not produce an oversized first implementation.
- Server-first priority must not violate local-first behavior.
- A new Worker must verify current `HEAD` rather than trusting stale handoff assumptions.

## 12. Worker Session Closure

The current Worker performed no further work after this handoff task.

A new Worker must bootstrap from repository state.

This file may be replaced at the next intentional Worker-session close.

It must not accumulate an endless chronological log.
