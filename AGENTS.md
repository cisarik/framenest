# FrameNest Agent Instructions

## Project Identity

FrameNest is a local-first, privacy-conscious, cross-platform library for video and animated media. It is currently in a foundation-stage, pre-alpha state. There is no functional application or server yet.

## Roles

The COOPERATOR is the human project owner. The Cooperator owns strategic intent, approves important alternatives, performs physical-device and account-level actions, executes explicitly assigned human steps, and approves irreversible or security-sensitive operations.

The ORCHESTRATOR is the ChatGPT orchestration layer. The Orchestrator preserves project coherence, inspects evidence, shapes bounded Worker tasks, reviews Worker reports, verifies public commits, and decides whether to accept, correct, continue, pause, or close a session.

The WORKER is Codex or a Cursor agent operating inside the repository. The Worker inspects before modification, executes only the authorized task, maintains task boundaries, verifies results, and reports evidence honestly.

## Language Rules

Repository documentation must be written in professional English unless a task explicitly says otherwise.

Worker reports to the Orchestrator must be written in Slovak and begin with:

`### Report for ORCHESTRATOR_CHAT`

Do not use Czech in repository documents or Worker reports.

## Operating Rules

- Inspect before changing.
- Do not expand scope silently.
- Do not access or print secrets.
- Do not perform destructive actions without explicit authorization.
- Do not perform Git write operations without task-specific permission.
- Do not install dependencies unless explicitly authorized.
- Do not choose frameworks, databases, or architecture details without an approved task or recorded decision.

## Public Commit Verification

A Worker report is a structured claim. Public committed state is independently inspectable evidence.

When commits are pushed, the Orchestrator should compare the public commit SHA, file tree, diff, and raw file content with the Worker report. Local uncommitted state and public committed state must not be conflated.

## Source-of-Truth Conflict Handling

Repository files describe documented and implemented state. Tests describe verified behavior. Git history describes committed changes. ADRs and product specifications will be added later when authorized.

Handoff files describe session state but do not independently redefine permanent strategy.

When sources conflict, identify the exact conflict, determine whether a source is stale, incomplete, misunderstood, or intentionally superseded, and escalate strategic conflicts to the Cooperator through the Orchestrator.

## Product Invariants

- FrameNest remains local-first.
- A premium gallery is a flagship product invariant.
- Server functionality must not replace local desktop functionality.
- Backend services must not be publicly exposed by default.
- Remote access direction is Tailscale-only unless explicitly superseded by an approved decision.
- Provider secrets must not be distributed to ordinary client installations.

## Handoff Model

FrameNest uses exactly these four lifecycle files:

- `BOOT_ORCHESTRATOR.md`: one-time bootstrap for a new Orchestrator chat.
- `BOOT_WORKER.md`: stable Worker bootstrap protocol.
- `NEXT_ORCHESTRATOR.md`: session-close handoff for a future Orchestrator.
- `NEXT_WORKER.md`: concise repository-local Worker handoff.

`BOOT_ORCHESTRATOR.md` is the one-time founding Orchestrator bootstrap. `BOOT_WORKER.md` is stable Worker bootstrap protocol. `NEXT_WORKER.md` carries the latest Worker-session handoff when a Worker session is intentionally closed. `NEXT_ORCHESTRATOR.md` is created only when an Orchestrator session is intentionally closed. Do not create `NEXT_AGENT.md`.

## Protocol Documents

- [AP.md](AP.md): general Analytic Programming protocol.
- [AP_ORCHESTRATOR.md](AP_ORCHESTRATOR.md): operational handbook for Orchestrators.
- [AP_WORKER.md](AP_WORKER.md): operational handbook for Workers.
- [BOOT_WORKER.md](BOOT_WORKER.md): FrameNest-specific Worker bootstrap.

Product specifications and ADRs will be added later through bounded tasks.
