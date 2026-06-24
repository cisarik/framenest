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

Committed documentation and evidence artifacts MUST follow the classification, consumer, retention, and cleanup rules in section **Artifact Lifecycle and Repository Hygiene**.

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

Examples include deleting files, dropping data, overwriting history, rotating credentials, removing remote resources, changing production configuration, or deleting committed evidence artifacts.

The Worker MUST stop if destructive scope is ambiguous.

Deleting temporary or retained evidence is destructive even when a retention trigger has been reached. A retention trigger identifies when cleanup may be appropriate; it does not grant deletion permission by itself.

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

## 28. Session Rotation and Context Pressure

Conversational context is temporary. It MUST NOT be treated as the sole project memory.

Repository files, tests, commits, ADRs, and handoff documents are the durable source of truth.

Automatic context compaction or summarization MAY help continuity, but it MUST NOT replace an explicit handoff when a session is ending or when durable state has changed.

Visible context percentages are heuristics. Different tools measure and display context differently, so percentage thresholds are guidance rather than universal guarantees.

At approximately 80% context usage, a role SHOULD avoid starting a large new task and SHOULD plan a checkpoint instead.

At approximately 85% or more, a role SHOULD normally finish only the current bounded task, create or update the appropriate handoff, and stop.

Earlier rotation is required when a role repeats questions, forgets constraints, confuses commits, expands scope, or shows inconsistent reasoning.

A natural architectural or implementation checkpoint is preferable to waiting for complete context exhaustion.

BOOT files describe stable role or project initialization.

NEXT files describe current session state.

Neither BOOT nor NEXT files grants modification authority.

Every Worker still requires a separate authoritative task from the Orchestrator.

Handoff files SHOULD be replaced with current state rather than grow into endless chronological logs.

Handoffs MAY reference temporary committed evidence while a decision remains open. After that evidence is consumed by a durable artifact, handoffs MUST reference the accepted durable artifact instead.

The closing session MUST stop after the handoff report.

A new session MUST independently verify the current repository HEAD and public committed state.

## 29. Stopping Conditions

The Worker MUST stop when required identity checks fail, authorized files differ from expectations, secrets would be exposed, required evidence is missing, authentication fails in an unsafe way, or completion would require out-of-scope changes.

The Orchestrator MUST stop or reframe when the next step requires Cooperator approval.

## 30. Anti-Patterns

Anti-patterns include silent scope expansion, implementation before inspection, treating reports as proof, conflating public commits with local changes, inventing decisions, hiding failures, broad filesystem inspection, unnecessary package installation, Git writes without permission, orphaned committed evidence, unnecessary research-file creation, stale evidence references, and retaining consumed temporary evidence without explicit continuing-value justification.

## 31. Minimal Orchestrator Loop

1. Understand Cooperator intent.
2. Inspect source-of-truth evidence.
3. Choose the smallest coherent next step.
4. Decide whether a Worker report is sufficient or a committed artifact is genuinely needed.
5. Issue one bounded Worker task with artifact lifecycle metadata when documentation is required.
6. Review the Worker report.
7. Verify public commits when available.
8. Decide to accept, correct, continue, pause, or close.

## 32. Minimal Worker Loop

1. Read the complete task.
2. Verify working directory, repository identity, and preconditions.
3. Verify artifact lifecycle authority before creating, consuming, or deleting documentation.
4. Inspect before changing.
5. Modify only authorized paths.
6. Run permitted validation.
7. Perform authorized Git operations only when explicitly allowed.
8. Report evidence, artifact lifecycle state, deviations, risks, and final state.

## 33. Example Task Lifecycle

The Cooperator asks for a capability.

The Orchestrator inspects the repository and determines that a design decision is missing.

The Orchestrator asks the Worker for a bounded inspection report rather than implementation.

The Worker reports current evidence and limitations.

The Orchestrator evaluates the report, asks the Cooperator to approve a direction, then issues a narrow implementation task.

The Worker implements only the authorized change, validates it, reports the result, and commits only if Git writes are authorized.

The Orchestrator verifies the public commit before authorizing the next step.

## 34. Compact Communication Mode

Repositories MAY use a compact communication mode to reduce prompt and report verbosity without weakening authority, safety, or evidence requirements.

### Worker prompts

A compact prompt MAY reference stable protocol documents such as `AGENTS.md`, `BOOT_WORKER.md`, and `AP_WORKER.md` instead of repeating them verbatim.

A compact prompt MUST still explicitly contain:

- task ID and goal;
- working directory;
- expected repository state or HEAD;
- task-specific allowed paths;
- task-specific scope prohibitions;
- Git write authority;
- required validation;
- acceptance and stopping conditions;
- required report format.

Stable restrictions already defined in repository protocol documents need not be copied into every prompt.

### Worker reports

Worker reports MUST be evidence-dense and MUST NOT restate the task.

Unless a task explicitly requires more detail, a report SHOULD contain:

1. status;
2. start and end HEAD;
3. changed files and short purpose;
4. tests and validation results;
5. commit and push result;
6. deviations or risks;
7. one proposed next step.

Summarize command execution instead of listing every command.

Include full command output only when:

- a command failed;
- unexpected state occurred;
- evidence cannot be summarized safely;
- the Orchestrator explicitly requested the full output.

Target a concise report, normally no more than approximately 800–1,000 words.

Safety-relevant evidence MUST NOT be omitted merely to satisfy brevity.

### Fresh Worker startup

A separate bootstrap-only task is optional, not universally mandatory.

For a normal low- or medium-risk continuation, the first implementation prompt MAY contain a short mandatory read-only bootstrap gate before modifications.

A separate bootstrap-only task SHOULD still be used when:

- repository identity is uncertain;
- the working tree may be dirty;
- environment state is uncertain;
- security-sensitive work is next;
- the Orchestrator explicitly requires it.

The Worker MUST stop before modification if the integrated bootstrap gate fails.

## 35. Artifact Lifecycle and Repository Hygiene

Repository hygiene requires every committed documentation or evidence artifact to have a defined lifecycle. Artifact lifecycle rules apply proportionally and MUST NOT create bureaucracy heavier than the artifact itself.

### Classification model

1. **Transient evidence**
   - Command output, reports, chat findings, or observations that normally remain uncommitted.
   - Preferred when one-use evidence is sufficient.

2. **Temporary committed evidence**
   - Research or decision-support material committed only when multi-session review, independent inspection, or durable pre-decision evidence is genuinely needed.
   - Non-authoritative.
   - MUST have an explicit future consumer and cleanup trigger.

3. **Retained evidence**
   - Durable audits, reproducible benchmarks, incident evidence, compatibility records, or other material with continuing independent value.
   - MUST have an explicit retention rationale and discoverable index or reference.

4. **Normative durable artifacts**
   - Accepted ADRs, specifications, policies, schemas, or equivalent authoritative project records.
   - Remain until explicitly superseded or retired.

5. **Operational lifecycle artifacts**
   - Bootstrap, session handoff, checkpoint, or similar working-state documents.
   - Follow replacement or session-specific lifecycle rules and MUST NOT become endless historical logs.

### Required metadata for newly committed documentation or evidence

Every task that authorizes a new committed documentation or evidence artifact MUST define:

- artifact classification;
- authoritative or non-authoritative status;
- intended consumer;
- discoverability or inbound reference;
- retention or cleanup trigger;
- cleanup owner or responsible role.

### Normative principles

- Use the lightest sufficient artifact.
- Prefer an evidence-dense Worker report over a committed research file when the report is sufficient.
- Do not create an artifact without a concrete consumer.
- No committed documentation artifact may remain unintentionally orphaned.
- Git history is the historical archive; the active working tree represents current usable project knowledge.
- When temporary evidence is consumed by an Accepted ADR, specification, test suite, or other durable artifact:
  - transfer the material conclusions, constraints, and necessary source references;
  - remove the temporary evidence;
  - remove or replace its inbound links;
  - perform these actions in the same bounded task and preferably the same commit.
- Retaining consumed evidence is an exception requiring an explicit continuing-value rationale.
- Handoffs may reference temporary evidence while a decision is open, but must reference the durable decision after consumption.
- A retention trigger does not itself authorize deletion. Deletion still requires explicit task-specific authority.
- Do not introduce a mandatory global artifact registry; use existing indexes, ADR indexes, README sections, or handoffs when sufficient.
