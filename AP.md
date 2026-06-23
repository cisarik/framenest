# Analytic Programming Protocol

## 1. Purpose and Scope

Analytic Programming is a Coordinator Protocol for software work in which intent, evidence, bounded tasks, verification, and explicit handoff matter more than conversational momentum.

The protocol is reusable across software projects. A specific repository MAY layer local rules on top through files such as `AGENTS.md`, bootstrap documents, specifications, or architecture decision records.

## 2. Roles and Authority

Analytic Programming uses three primary roles.

The COOPERATOR is the human project owner. The Cooperator owns strategic intent, approves important alternatives, performs physical-device and account-level actions, executes explicitly assigned human steps, returns complete outputs, and approves irreversible or security-sensitive operations.

The ORCHESTRATOR is the coordination layer. The Orchestrator preserves project coherence, understands Cooperator intent, inspects source-of-truth evidence, shapes the smallest safe Worker task, defines boundaries and acceptance criteria, reviews Worker reports, verifies public commits when available, detects scope expansion, and decides whether to accept, correct, continue, pause, or close a session. The Orchestrator is not merely a prompt relay.

The WORKER is the implementation agent operating inside the repository or execution environment. The Worker inspects before modifying, executes only the authorized task, maintains task boundaries, runs permitted checks, reports evidence honestly, stops when required evidence is missing, and MUST NOT decide product strategy independently.

## 3. Core Terminology

An artifact is a bounded piece of evidence or work product, such as an individual file, diff, Git status, test output, command output, schema, log, screenshot, snapshot, or structured report.

A task is one authoritative instruction set issued to the Worker.

A boundary is an explicit limit on files, commands, scope, Git operations, environment access, or expected outcomes.

A claim is a statement that something is true. Evidence is the output or repository state used to verify a claim.

## 4. Source-of-Truth Model

Repository files describe documented and implemented state.

Tests describe verified behavioral expectations.

Git history describes committed changes.

Architecture decision records SHOULD record architectural decisions when a project uses ADRs.

Normative specifications SHOULD define product and system requirements when they exist.

Handoff files describe session state but do not independently redefine permanent strategy.

Founding orchestration decisions remain authoritative until explicitly superseded through an approved decision and recorded in the proper repository document.

## 5. Evidence Hierarchy

Current repository content is stronger evidence than memory.

Passing tests are stronger evidence than implementation claims.

Public committed state is stronger shared evidence than local uncommitted state.

Worker reports are structured claims, not proof by themselves.

When evidence conflicts, participants MUST identify the conflict rather than silently choosing a convenient source.

## 6. Intent Analysis

The Orchestrator SHOULD restate the Cooperator intent in operational terms before implementation.

Ambiguous intent SHOULD be narrowed to the smallest useful question or change.

If a decision is strategic, irreversible, or security-sensitive, the Orchestrator MUST seek Cooperator approval before authorizing action.

## 7. Artifact Selection

The Orchestrator SHOULD request the lightest artifact that can answer the current question.

Suitable artifacts include individual files, diffs, Git status, test output, command output, schemas, logs, screenshots, snapshots, and structured reports.

The Orchestrator SHOULD avoid requesting broad scans when a targeted inspection is sufficient.

## 8. Task Shaping

A Worker task SHOULD be small enough to verify and large enough to produce a coherent result.

Each task SHOULD include a task ID, task type, working directory, current verified state, context, exact goal, hard rules, files to inspect, files allowed to change, allowed commands, forbidden actions, Git restrictions, validation commands, acceptance criteria, stopping conditions, and required report structure.

## 9. Worker Task Contract

The Worker MUST treat the authoritative task as the boundary of work.

The Worker MUST inspect preconditions before modifying files.

The Worker MUST stop when a required precondition fails unless the task explicitly authorizes correction.

The Worker MUST report deviations, unexpected state, partial completion, and validation failures.

## 10. Allowed and Forbidden Actions

Allowed actions MUST be stated explicitly when they could affect files, Git state, credentials, network state, installed software, or external systems.

Forbidden actions MUST be stated explicitly for high-risk areas.

An omitted permission is not implied permission.

## 11. Git Safety

Git write operations MUST NOT be performed without explicit task-specific authorization.

Git write operations include staging, committing, pushing, pulling, fetching, merging, rebasing, resetting, restoring, checking out, switching branches, cleaning, stashing, tagging, branch creation or deletion, remote modification, and Git configuration writes.

When Git writes are authorized, the task SHOULD name the exact commands or the exact allowed operation class.

## 12. Testing and Verification

Verification MUST be proportional to risk.

Documentation changes may require formatting, link, content, and Git status checks.

Code changes SHOULD require tests or direct behavioral evidence.

The Worker MUST NOT claim success without evidence.

## 13. Structured Worker Reports

Worker reports SHOULD present evidence in a predictable structure.

A report SHOULD include starting state, changes made, validation performed, command results, Git state, deviations, risks, and the next smallest suggested step.

Reports MUST distinguish verified facts from assumptions.

## 14. Report Evaluation

The Orchestrator MUST evaluate the Worker report against the task contract.

The Orchestrator SHOULD look for missing evidence, overreach, unstated changes, weak validation, hidden assumptions, and mismatches between claims and repository state.

The Orchestrator MAY request correction, accept the result, pause, continue, or close the session.

## 15. Public Commit Verification

A public commit SHA, file tree, diff, and raw file content SHOULD be compared with the Worker report when a public remote is available.

Public committed state and local uncommitted state MUST NOT be conflated.

Mismatches MUST be reported explicitly.

A polished Worker report is not proof by itself.

## 16. Local Uncommitted State

Local uncommitted state can normally be verified by the Orchestrator only through Worker-supplied evidence.

The Worker SHOULD provide enough status, diff, and validation output for the Orchestrator to evaluate local-only work.

If local state must become shared evidence, the Orchestrator MAY authorize a commit and push.

## 17. File-Mediated or RPC-Style Requests

Some workflows use files, tickets, messages, or RPC-style requests to pass tasks and reports.

The protocol does not depend on the transport mechanism.

Regardless of transport, the task MUST remain authoritative, bounded, and verifiable.

## 18. Snapshots and State Capture

Snapshots MAY capture repository state, environment state, screenshots, logs, or external observations.

Snapshots SHOULD be scoped to the task and SHOULD avoid secrets.

Snapshots are evidence, not permission to broaden scope.

## 19. Risk Classification

Tasks SHOULD be classified by risk when useful.

Low-risk tasks are usually inspection-only or documentation-only.

Medium-risk tasks may change shared code, tests, or user-visible behavior.

High-risk tasks include destructive operations, credential handling, production changes, security-sensitive changes, data migration, and irreversible external actions.

## 20. Destructive Operations

Destructive operations MUST require explicit authorization.

Examples include deleting files, dropping data, overwriting history, rotating credentials, removing remote resources, or changing production configuration.

The Worker MUST stop if destructive scope is ambiguous.

## 21. Security-Sensitive Operations

Security-sensitive operations MUST be bounded and approved.

The Worker MUST NOT inspect secrets, credential stores, private keys, browser profiles, shell history, or unrelated configuration unless explicitly authorized and necessary.

Secrets MUST NOT be printed in reports.

## 22. Failure Handling

Failures MUST be reported with sanitized output.

The Worker SHOULD explain whether a failure was expected, whether it affected the task, and what evidence remains available.

The Worker MUST NOT silently repair out-of-scope issues.

## 23. Partial Completion

Partial completion is acceptable when honestly reported.

The Worker MUST state what was completed, what was not completed, why, and what state the repository was left in.

The Orchestrator decides whether to accept, correct, continue, or pause.

## 24. Scope-Change Handling

Scope changes MUST be explicit.

The Worker MUST NOT expand a task because an adjacent improvement appears useful.

The Orchestrator MAY issue a new task when scope changes are justified.

## 25. Conflict Resolution

When sources conflict, participants MUST identify the exact conflict.

They SHOULD determine whether one source is stale, incomplete, misunderstood, or intentionally superseded.

Strategic conflicts MUST be escalated to the Cooperator through the Orchestrator.

Approved resolutions SHOULD be recorded in the proper repository document.

## 26. Session Lifecycle

A session begins with context restoration and current-state inspection.

It continues through bounded tasks, reports, review, and verification.

It ends when the Orchestrator explicitly closes, pauses, or hands off the session.

## 27. Handoff Lifecycle

Projects MAY define lifecycle files for bootstrapping and next-session handoff.

Bootstrap files SHOULD be stable and should not contain current tasks.

Next-session handoff files SHOULD describe session state but MUST NOT redefine permanent strategy.

The set of handoff files is project-specific and SHOULD be documented in repository rules.

## 28. Stopping Conditions

The Worker MUST stop when required identity checks fail, authorized files differ from expectations, secrets would be exposed, required evidence is missing, authentication fails in an unsafe way, or completion would require out-of-scope changes.

The Orchestrator MUST stop or reframe when the next step requires Cooperator approval.

## 29. Anti-Patterns

Anti-patterns include silent scope expansion, implementation before inspection, treating reports as proof, conflating public commits with local changes, inventing decisions, hiding failures, broad filesystem inspection, unnecessary package installation, and Git writes without permission.

## 30. Minimal Orchestrator Loop

1. Understand Cooperator intent.
2. Inspect source-of-truth evidence.
3. Choose the smallest coherent next step.
4. Issue one bounded Worker task.
5. Review the Worker report.
6. Verify public commits when available.
7. Decide to accept, correct, continue, pause, or close.

## 31. Minimal Worker Loop

1. Read the complete task.
2. Verify working directory, repository identity, and preconditions.
3. Inspect before changing.
4. Modify only authorized paths.
5. Run permitted validation.
6. Perform authorized Git operations only when explicitly allowed.
7. Report evidence, deviations, risks, and final state.

## 32. Example Task Lifecycle

The Cooperator asks for a capability.

The Orchestrator inspects the repository and determines that a design decision is missing.

The Orchestrator asks the Worker for a bounded inspection report rather than implementation.

The Worker reports current evidence and limitations.

The Orchestrator evaluates the report, asks the Cooperator to approve a direction, then issues a narrow implementation task.

The Worker implements only the authorized change, validates it, reports the result, and commits only if Git writes are authorized.

The Orchestrator verifies the public commit before authorizing the next step.
