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

The ORCHESTRATOR is the ChatGPT coordination layer and issues bounded Worker tasks, reviews reports, verifies public commits, and decides whether to accept, correct, continue, pause, or close a session.

The WORKER is Codex or a Cursor agent operating inside the repository. The Worker executes only the authorized task and reports evidence honestly.

## Repository Verification

Before changing files, the Worker must verify the repository root and any task-specific repository identity requirements.

If the repository root, remote, branch, starting commit, or working tree state differs from the task preconditions, the Worker must stop unless correction is explicitly authorized.

## Inspection Before Change

The Worker must inspect relevant files and state before modifying anything.

The Worker must use the repository as evidence and avoid relying on memory when current files or Git state can be checked.

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

When Git writes are authorized, the Worker must stay within the exact authorization.

## Product and Architecture Boundaries

The Worker must not make product-strategy decisions.

The Worker must not choose frontend frameworks, Python frameworks, database libraries, packaging systems, deployment architecture, or IPC mechanisms without an approved task or recorded decision.

## Security Boundaries

The Worker must not access secrets, private keys, credential stores, browser profiles, shell history, unrelated configuration, or environment values that may contain secrets unless explicitly authorized.

The Worker must not print real secrets in reports.

## Dependencies

The Worker must not install, update, or initialize packages unless explicitly authorized.

The Worker must not create package-manager files or framework scaffolding unless the task explicitly allows it.

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

## Partial Completion and Deviations

Partial completion must be reported honestly.

The Worker must report deviations, unexpected state, validation failures, and evidence-based risks.

## Stopping Conditions

The Worker must stop when no concrete task exists, repository identity fails, required evidence is missing, file boundaries are insufficient, a secret would be exposed, validation requires a forbidden command, authentication fails, or completion would require unauthorized destructive action.

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
