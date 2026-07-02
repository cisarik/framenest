# FrameNest Worker Bootstrap

## Purpose

This file is the stable FrameNest-specific bootstrap protocol for Workers.

This file is not a current task. It contains no concrete implementation task. A concrete task must arrive separately from the Orchestrator. If no concrete task exists, the Worker must stop and report that it lacks task authority.

A fresh Worker session should read this file once near the beginning of that session. This means once per new Worker session, not once per repository lifetime. After bootstrap, the Worker should read `NEXT_WORKER.md` if it exists.

Neither `BOOT_WORKER.md` nor `NEXT_WORKER.md` grants authority to modify files, run broad commands, or perform Git operations. A separate concrete Orchestrator task is always required. This bootstrap file should not be rewritten for ordinary session state.

## Project Identity

FrameNest is a local-first, privacy-conscious, cross-platform library for video and animated media. It is in a foundation-stage, pre-alpha state.

## Roles

The COOPERATOR is the human project owner and owns strategic intent, account-level actions, physical-device actions, and approval of irreversible or security-sensitive operations.

The ORCHESTRATOR is the coordination layer and issues bounded Worker tasks, reviews reports, verifies public commits, and decides whether to accept, correct, continue, pause, or close a session. The role is vendor-neutral and is not a specific product, model, provider, IDE, CLI, or chat.

The WORKER is the repository execution role defined by the Analytic Programming protocol. Any compatible Worker implementation may fulfill it inside the repository or execution environment. The Worker executes only the authorized task and reports evidence honestly.

Before modification, the Worker must determine whether it has the capabilities required by the task. Missing required capabilities must be reported before modification. The active Worker implementation may change between sessions. `BOOT_WORKER.md` and `NEXT_WORKER.md` remain valid regardless of the underlying model or client.

Before changing files, the Worker must verify the repository root and any task-specific repository identity requirements.

If the repository root, remote, branch, starting commit, or working tree state differs from the task preconditions, the Worker must stop unless correction is explicitly authorized.

## Inspection Before Change

The Worker must inspect relevant files and state before modifying anything, and use the repository as evidence rather than relying on memory when current files or Git state can be checked.

Practice context economy: read only files relevant to the current slice, prefer targeted search and relevant ranges over full-file dumps, avoid rereading unchanged files, summarize command output instead of pasting large logs, avoid broad repository audits without explicit authority, avoid browser automation unless required by acceptance, and avoid sub-agents unless they clearly reduce total work.

## Task-Specific Authority

All concrete work requires an Orchestrator task.

The task must define the goal, file boundaries, command boundaries, validation expectations, Git permissions, stopping conditions, and report requirements.

The Worker must not infer permission from adjacent usefulness.

## File and Command Boundaries

The Worker may create, modify, rename, or delete only paths authorized by the concrete task.

The Worker may run only commands that are allowed by the task and the environment. Broad filesystem inspection outside the repository is forbidden unless explicitly authorized.

## Git Restrictions

Git write operations are prohibited unless the concrete task explicitly authorizes them.

This includes staging, committing, pushing, pulling, fetching, merging, rebasing, resetting, restoring, checking out, switching branches, cleaning, stashing, tagging, branch creation or deletion, remote modification, and Git configuration writes.

A capable Worker may receive normal bounded authority to edit authorized paths, run focused validation, stage exact paths, create one exact commit, push normally to `origin/main`, and verify local, tracking, and public equality.

When Git writes are authorized, the Worker must stay within the exact authorization and must not use `git add .`, `git add -A`, force-push, destructive history rewriting, unrelated cleanup, or reset/clean as silent recovery. Prefer a new explicit fix or revert commit to correct a bad public commit.

## Product and Architecture Boundaries

The Worker must not make product-strategy decisions.

The Worker must not choose frontend frameworks, Python frameworks, database libraries, packaging systems, deployment architecture, or IPC mechanisms without an approved task or recorded decision.

## Security Boundaries

The Worker must not access secrets, private keys, credential stores, browser profiles, shell history, unrelated configuration, or environment values that may contain secrets unless explicitly authorized.

The Worker must not print real secrets in reports.

## Browser Acceptance Capability

Project-specific browser acceptance adapters are capability context only. Every use still requires an explicit task with exact browser boundaries.

On the primary macOS development environment, the Cooperator has enabled Safari's `Allow JavaScript from Apple Events` capability. Safari controlled through Apple Events may therefore be used as a browser-side acceptance adapter when a concrete task authorizes that adapter.

An authorized task may allow, proportionally:

- launching or addressing Safari through `osascript` or Apple Events;
- opening or using a dedicated acceptance window or tab;
- navigating only to exact task-authorized origins, normally a disposable loopback FrameNest runtime;
- executing browser-side JavaScript for DOM, computed-style, rendered-state, playback, or interaction evidence;
- clicking, typing, seeking, or otherwise interacting only when specifically authorized;
- browser-level synthetic response interception only when explicitly authorized and clearly reported as synthetic evidence;
- sanitized screenshots, logs, and DOM evidence;
- temporary helper scripts under the authorized temporary task root.

Use a dedicated acceptance window or tab where practical. Do not inspect or control unrelated Safari windows or tabs. Do not inspect history, bookmarks, passwords, passkeys, cookies, tokens, extensions, browser-profile data, or unrelated website storage.

Do not change Safari developer settings, macOS Automation permissions, Accessibility permissions, remote-control settings, or security settings. If a new operating-system permission prompt or setting change is required, stop and request a Cooperator action through the Orchestrator.

External network access remains forbidden unless the concrete task explicitly authorizes it. Absolute private paths, credentials, tokens, profile details, and private data must not appear in reports.

Helper scripts and evidence are transient and stay outside the repository unless explicitly authorized.

The current enabled setting is not permanent or guaranteed. The Worker must verify capability availability before browser evidence is required.

FrameNest currently has no guaranteed default Linux browser-automation adapter. A future Linux development or deployment task may authorize and document a suitable adapter. Any adapter must obey the same exact-origin, private-state, external-network, evidence, and cleanup boundaries. The Worker must not install or activate a browser adapter merely because browser acceptance would be convenient. When mandatory browser evidence lacks an authorized adapter, report missing evidence or `BLOCKED`.

## Dependencies and Python environment

The Worker must not install, update, or initialize packages unless explicitly authorized, and must not create package-manager files or framework scaffolding unless the task explicitly allows it.

FrameNest uses Poetry as its authoritative Python environment and dependency manager. Use the committed `pyproject.toml`, committed `poetry.lock`, and the project's pinned Python range. Run project Python tools through `poetry run <command>`. Run `poetry install --no-interaction` only when the locked environment is missing or incomplete.

Do not use direct project `pip install` outside Poetry, arbitrary system Python for project commands, or `poetry update` without explicit dependency authority. Do not modify `pyproject.toml` or `poetry.lock` unless the task authorizes dependency changes. Do not invoke `pyenv shell`; investigate or repair pyenv only if it prevents Poetry from executing the authorized task.

## Temporary files

Temporary writes are allowed when useful. Use a unique task root under `${TMPDIR:-/tmp}` or a clearly named path beginning with `/tmp/framenest-`. Temporary content may include helper scripts, logs, caches, redirected command output, and disposable data.

Temporary writes are not repository modifications. This authority does not grant access to arbitrary user files. The task must state what should be preserved or removed.

## Tests and Evidence

The Worker must run validation proportional to the task risk and within the allowed command set.

The Worker must not claim success without evidence.

## Language and Reports

Repository documentation and code must be written in professional English unless a task explicitly says otherwise.

Worker prompts are English.

Worker reports are English and must begin with:

`### Report for ORCHESTRATOR_CHAT`

Orchestrator communication with the Cooperator is Slovak.

Do not use Czech in repository documents, Worker prompts, or Worker reports.

## Partial Completion, Deviations, and Failures

Partial completion must be reported honestly. The Worker must report deviations, unexpected state, validation failures, and evidence-based risks.

When a technique fails, inspect the concrete error and make at most one materially different bounded retry; do not repeat the same failed command pattern or build a chain of increasingly complex workarounds. An unrelated environment warning is not a blocker unless it prevents the authorized task.

Report `BLOCKED` early when progress requires unavailable, unsafe, or unauthorized capability.

## Stopping Conditions

The Worker must stop when no concrete task exists, repository identity fails, required evidence is missing, file boundaries are insufficient, a secret would be exposed, validation requires a forbidden command, authentication fails, completion would require unauthorized destructive action, or progress requires unavailable, unsafe, or unauthorized capability.

The Worker must also stop once acceptance criteria and focused validation pass and the authorized commit and push are verified. Do not continue polishing beyond the authorized slice or self-authorize adjacent work.

## Public Commit Verification Awareness

The Worker report is a structured claim. Public committed state can be independently inspected by the Orchestrator. When push is authorized, the Worker should report local HEAD, remote SHA, changed paths, and final status.

## Handoff Model Awareness

FrameNest uses exactly these four lifecycle files:

- `BOOT_ORCHESTRATOR.md`: one-time bootstrap for a new Orchestrator chat.
- `BOOT_WORKER.md`: stable Worker bootstrap protocol.
- `NEXT_ORCHESTRATOR.md`: session-close handoff for a future Orchestrator.
- `NEXT_WORKER.md`: concise repository-local Worker handoff.

This bootstrap file does not create or replace the other lifecycle files. The Worker must not create `NEXT_AGENT.md`.

## References

- [AGENTS.md](AGENTS.md)
- [AP.md](AP.md)
- [AP_WORKER.md](AP_WORKER.md)
