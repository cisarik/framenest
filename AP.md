# Analytic Programming Protocol

## 1. Purpose and Scope

Analytic Programming is a Coordinator Protocol for software work in which intent, evidence, bounded tasks, verification, and explicit handoff matter more than conversational momentum.

The protocol is reusable across software projects. A specific repository MAY layer local rules on top through files such as `AGENTS.md`, bootstrap documents, specifications, or architecture decision records.

## 2. Roles and Authority

Analytic Programming uses three primary roles.

The COOPERATOR is the human project owner. The Cooperator owns strategic intent, approves important alternatives, performs physical-device and account-level actions, executes explicitly assigned human steps, returns complete outputs, and approves irreversible or security-sensitive operations.

The ORCHESTRATOR is the coordination layer. The Orchestrator preserves project coherence, understands Cooperator intent, inspects source-of-truth evidence, shapes the smallest safe Worker task, defines boundaries and acceptance criteria, reviews Worker reports, verifies public commits when available, detects scope expansion, and decides whether to accept, correct, continue, pause, or close a session. The Orchestrator is not merely a prompt relay.

The WORKER is the protocol role that executes one bounded authoritative task, validates the result, and returns evidence. The Worker inspects before modifying, maintains task boundaries, runs permitted checks, reports evidence honestly, stops when required evidence is missing, and MUST NOT decide product strategy independently. WORKER is not a product, model, provider, IDE, CLI, or hosted service.

## 3. Worker Role Portability and Capability Model

WORKER is a protocol role, not a product or provider.

A **Worker implementation** is the concrete system currently fulfilling the WORKER role. It may be an IDE-integrated execution agent, a command-line agent, a local or remote coding agent, a general execution agent, a multi-agent system exposed through one accountable Worker endpoint, or, where a project permits it, a human executor following the same task contract.

A **Worker instance** is one concrete initialized execution-agent instance temporarily assigned to the WORKER role. A **Worker session** is the lifecycle and conversational context of one Worker instance from bootstrap or continuation through intentional closeout.

An **execution client** is the host tool or environment running the agent. An **agent implementation** is the concrete agent system fulfilling capabilities. A **model** is the language model used for generation. A **model provider** is the organization or service hosting that model. Cursor Agent, Codex agent, Hermes, OpenClaw, or another coding agent may be an execution client or agent implementation; they are not the WORKER role itself.

Use `WORKER` in normative rules for the persistent protocol role. Use `Worker instance` or `Worker session` when referring to one concrete agent lifecycle. Use `Worker implementation` only when discussing environment-specific capabilities. Use `a fresh Worker instance assigned to the WORKER role` when opening a new concrete agent. Do not use `a fresh WORKER` for that meaning.

Context-pressure heuristics apply to the current Worker instance and Worker session, not to the persistent WORKER protocol role.

A **Worker capability profile** describes what the active Worker implementation can do in the current session. Capabilities may include repository and filesystem access, shell or command execution, Git access, network or web access, package-manager access, test execution, multimodal inspection, visible context telemetry, context capacity, and internal sub-agent delegation.

### Protocol neutrality

The protocol does not depend on:

- a particular IDE, CLI, hosted platform, or model family;
- a particular context-window size or agent framework;
- a single-agent or multi-agent internal implementation.

A Worker implementation may change between sessions without changing protocol roles.

Every Worker remains bound by the authoritative task, repository rules, file and command boundaries, Git authority, security constraints, validation, and report requirements.

### Capability requirements

Required capabilities MUST be stated functionally in the task, not by naming a vendor.

A Worker MUST stop and report before modification when a required capability is unavailable.

Missing required capabilities MUST NOT be compensated by broader filesystem, network, secret, or Git actions.

Tool availability does not grant permission.

### Multi-agent accountability

A multi-agent Worker implementation is still one accountable WORKER at the protocol boundary.

Internal delegation:

- MUST NOT expand task scope;
- MUST NOT grant additional filesystem, network, secret, or Git authority;
- MUST NOT hide commands, changes, failures, or evidence;
- remains the responsibility of the reporting WORKER.

The Worker MUST return one consolidated accountable report and MUST distinguish directly observed evidence from sub-agent claims.

### Context capacity

A larger context window does not replace repository source of truth, verification, durable decisions, artifact lifecycle, or intentional handoffs.

Context-pressure heuristics apply relative to the active Worker implementation's actual telemetry and behavior, not to a hard-coded absolute token budget.

When no context meter exists, participants SHOULD use behavioral indicators and natural checkpoints.

Task sizing SHOULD consider the active capability profile while preserving the same authority and safety model.

### Vendor references

Project-specific prompts MAY mention an actual execution environment only when operationally necessary.

Vendor, model, and client names MUST NOT appear as normative requirements in reusable protocol documents.

This section integrates with roles in section 2, transport neutrality in section 18, Worker session handoff in section 29, session rotation in section 30, stopping conditions in section 31, and anti-patterns in section 32.

## 4. Core Terminology

An artifact is a bounded piece of evidence or work product, such as an individual file, diff, Git status, test output, command output, schema, log, screenshot, snapshot, or structured report.

A task is one authoritative instruction set issued to the Worker.

A boundary is an explicit limit on files, commands, scope, Git operations, environment access, or expected outcomes.

A claim is a statement that something is true. Evidence is the output or repository state used to verify a claim.

## 5. Source-of-Truth Model

Repository files describe documented and implemented state.

Tests describe verified behavioral expectations.

Git history describes committed changes.

Architecture decision records SHOULD record architectural decisions when a project uses ADRs.

Normative specifications SHOULD define product and system requirements when they exist.

Handoff files describe session state but do not independently redefine permanent strategy.

Founding orchestration decisions remain authoritative until explicitly superseded through an approved decision and recorded in the proper repository document.

## 6. Evidence Hierarchy

Current repository content is stronger evidence than memory.

Passing tests are stronger evidence than implementation claims.

Public committed state is stronger shared evidence than local uncommitted state.

Worker reports are structured claims, not proof by themselves.

When evidence conflicts, participants MUST identify the conflict rather than silently choosing a convenient source.

## 7. Intent Analysis

The Orchestrator SHOULD restate the Cooperator intent in operational terms before implementation.

Ambiguous intent SHOULD be narrowed to the smallest useful question or change.

If a decision is strategic, irreversible, or security-sensitive, the Orchestrator MUST seek Cooperator approval before authorizing action.

## 8. Artifact Selection

The Orchestrator SHOULD request the lightest artifact that can answer the current question.

Suitable artifacts include individual files, diffs, Git status, test output, command output, schemas, logs, screenshots, snapshots, and structured reports.

The Orchestrator SHOULD avoid requesting broad scans when a targeted inspection is sufficient.

Committed documentation and evidence artifacts MUST follow the classification, consumer, retention, and cleanup rules in section **Artifact Lifecycle and Repository Hygiene**.

## 9. Task Shaping

A Worker task SHOULD be small enough to verify and large enough to produce a coherent result.

Each task SHOULD include a task ID, task type, working directory, current verified state, context, exact goal, hard rules, files to inspect, files allowed to change, allowed commands, forbidden actions, Git restrictions, validation commands, acceptance criteria, stopping conditions, and required report structure.

## 10. Worker Task Contract

The Worker MUST treat the authoritative task as the boundary of work.

The Worker MUST inspect preconditions before modifying files.

The Worker MUST stop when a required precondition fails unless the task explicitly authorizes correction.

The Worker MUST report deviations, unexpected state, partial completion, and validation failures.

## 11. Allowed and Forbidden Actions

Allowed actions MUST be stated explicitly when they could affect files, Git state, credentials, network state, installed software, or external systems.

Forbidden actions MUST be stated explicitly for high-risk areas.

An omitted permission is not implied permission.

## 12. Git Safety

Git write operations MUST NOT be performed without explicit task-specific authorization.

Git write operations include staging, committing, pushing, pulling, fetching, merging, rebasing, resetting, restoring, checking out, switching branches, cleaning, stashing, tagging, branch creation or deletion, remote modification, and Git configuration writes.

When Git writes are authorized, the task SHOULD name the exact commands or the exact allowed operation class.

## 13. Testing and Verification

Verification MUST be proportional to risk.

Documentation changes may require formatting, link, content, and Git status checks.

Code changes SHOULD require tests or direct behavioral evidence.

The Worker MUST NOT claim success without evidence.

## 14. Structured Worker Reports

Worker reports SHOULD present evidence in a predictable structure.

A report SHOULD include starting state, changes made, validation performed, command results, Git state, deviations, risks, and the next smallest suggested step.

Reports MUST distinguish verified facts from assumptions.

## 15. Report Evaluation

The Orchestrator MUST evaluate the Worker report against the task contract.

The Orchestrator SHOULD look for missing evidence, overreach, unstated changes, weak validation, hidden assumptions, and mismatches between claims and repository state.

The Orchestrator MAY request correction, accept the result, pause, continue, or close the session.

## 16. Public Commit Verification

A public commit SHA, file tree, diff, and raw file content SHOULD be compared with the Worker report when a public remote is available.

Public committed state and local uncommitted state MUST NOT be conflated.

Mismatches MUST be reported explicitly.

A polished Worker report is not proof by itself.

## 17. Local Uncommitted State

Local uncommitted state can normally be verified by the Orchestrator only through Worker-supplied evidence.

The Worker SHOULD provide enough status, diff, and validation output for the Orchestrator to evaluate local-only work.

If local state must become shared evidence, the Orchestrator MAY authorize a commit and push.

## 18. File-Mediated or RPC-Style Requests

Some workflows use files, tickets, messages, or RPC-style requests to pass tasks and reports.

The protocol does not depend on the transport mechanism or on a particular Worker implementation.

Regardless of transport, the task MUST remain authoritative, bounded, and verifiable.

## 19. Snapshots and State Capture

Snapshots MAY capture repository state, environment state, screenshots, logs, or external observations.

Snapshots SHOULD be scoped to the task and SHOULD avoid secrets.

Snapshots are evidence, not permission to broaden scope.

## 20. Risk Classification

Tasks SHOULD be classified by risk when useful.

Low-risk tasks are usually inspection-only or documentation-only.

Medium-risk tasks may change shared code, tests, or user-visible behavior.

High-risk tasks include destructive operations, credential handling, production changes, security-sensitive changes, data migration, and irreversible external actions.

## 21. Destructive Operations

Destructive operations MUST require explicit authorization.

Examples include deleting files, dropping data, overwriting history, rotating credentials, removing remote resources, changing production configuration, or deleting committed evidence artifacts.

The Worker MUST stop if destructive scope is ambiguous.

Deleting temporary or retained evidence is destructive even when a retention trigger has been reached. A retention trigger identifies when cleanup may be appropriate; it does not grant deletion permission by itself.

## 22. Security-Sensitive Operations

Security-sensitive operations MUST be bounded and approved.

The Worker MUST NOT inspect secrets, credential stores, private keys, browser profiles, shell history, or unrelated configuration unless explicitly authorized and necessary.

Secrets MUST NOT be printed in reports.

## 23. Failure Handling

Failures MUST be reported with sanitized output.

The Worker SHOULD explain whether a failure was expected, whether it affected the task, and what evidence remains available.

The Worker MUST NOT silently repair out-of-scope issues.

## 24. Partial Completion

Partial completion is acceptable when honestly reported.

The Worker MUST state what was completed, what was not completed, why, and what state the repository was left in.

The Orchestrator decides whether to accept, correct, continue, or pause.

## 25. Scope-Change Handling

Scope changes MUST be explicit.

The Worker MUST NOT expand a task because an adjacent improvement appears useful.

The Orchestrator MAY issue a new task when scope changes are justified.

## 26. Conflict Resolution

When sources conflict, participants MUST identify the exact conflict.

They SHOULD determine whether one source is stale, incomplete, misunderstood, or intentionally superseded.

Strategic conflicts MUST be escalated to the Cooperator through the Orchestrator.

Approved resolutions SHOULD be recorded in the proper repository document.

## 27. Session Lifecycle

A session begins with context restoration and current-state inspection.

It continues through bounded tasks, reports, review, and verification.

It ends when the Orchestrator explicitly closes, pauses, or hands off the session.

## 28. Handoff Lifecycle

Projects MAY define lifecycle files for bootstrapping and next-session handoff.

Bootstrap files SHOULD be stable and should not contain current tasks.

Next-session handoff files SHOULD describe session state but MUST NOT redefine permanent strategy.

The set of handoff files is project-specific and SHOULD be documented in repository rules.

## 29. Worker Session Handoff Transport and Authority

Worker rotation relies on three distinct session inputs. Each has a different authority, lifecycle, and transport rule. They MUST NOT be conflated.

### Three distinct Worker-session inputs

**Stable bootstrap**

A stable bootstrap document:

- defines role, repository, safety, language, and protocol rules;
- is read once near the beginning of a fresh Worker session;
- is not rewritten for ordinary progress;
- contains no current concrete task;
- grants no modification or Git authority.

**Repository-local next-session handoff**

A Worker handoff document:

- is an operational lifecycle artifact stored in the repository;
- describes the current implemented state, evidence, unresolved risks, and likely next boundary;
- is written or replaced by the closing Worker only under an explicit Orchestrator task;
- is designed and scoped by the Orchestrator;
- grants no task, modification, dependency, or Git authority;
- may describe a proposed next step only as non-authoritative context;
- is read directly from the repository by the fresh Worker;
- normally does not need to be manually copied by the Cooperator;
- MUST be independently verified by the fresh Worker against the current repository and refs;
- is replaced at the next intentional Worker close rather than growing as a chronological log.

**Authoritative Worker task**

A concrete Orchestrator task:

- is the only source of current task authority;
- may reference stable bootstrap and handoff documents instead of repeating them;
- MUST still define task-specific goal, working directory, expected state, boundaries, Git authority, validation, acceptance criteria, stopping conditions, and report format;
- may include an integrated read-only bootstrap gate;
- is the prompt the Cooperator sends to the fresh Worker session.

Wording such as "You are a fresh Worker session" describes the conversational context and restoration requirement. It does not replace the handoff and does not itself grant unlisted permissions.

### End-to-end Worker rotation flow

**Closing sequence**

1. The Orchestrator decides that rotation is required.
2. The Orchestrator issues one bounded handoff-authoring task.
3. The closing Worker writes or replaces the repository handoff.
4. The closing Worker validates it and performs only authorized Git writes.
5. The closing Worker reports a compact summary, exact changed path, validation, commit SHA, push state, and final repository status.
6. The Orchestrator independently verifies the committed handoff when possible.
7. The closing Worker session stops.

**Opening sequence**

1. The Cooperator opens a new Worker conversation in the same repository or workspace.
2. The Orchestrator provides one new authoritative concrete task prompt.
3. The fresh Worker reads repository rules, stable bootstrap, role handbook, and current handoff directly from the repository.
4. The fresh Worker independently resolves repository identity, current refs, cleanliness, and task preconditions.
5. The fresh Worker stops if the integrated bootstrap gate fails.
6. The fresh Worker executes only the concrete authoritative task.

The Cooperator normally transfers only the new Orchestrator task prompt, not copies of repository files. The Cooperator reports when the Worker cannot access the repository or referenced files.

### Report-content rule for handoff closeout

When the handoff is publicly committed and independently inspectable, the closing Worker report SHOULD normally summarize it rather than reproduce the entire file.

The Orchestrator SHOULD inspect the exact committed file and diff.

Full handoff content or full diff is appropriate only when:

- state is local-only;
- push failed;
- the remote is unavailable or private to the Orchestrator;
- independent inspection is impossible;
- the task explicitly requests full content.

A report MUST clearly distinguish committed handoff state from local-only handoff state.

Duplicating a committed handoff in the report without need is context waste and risks inconsistent parallel copies.

### Role responsibilities in Worker rotation

**Cooperator**

- opens the fresh Worker session;
- sends the new authoritative prompt supplied by the Orchestrator;
- does not normally reconstruct or manually copy repository handoff files;
- reports when the Worker cannot access the repository or referenced files.

**Orchestrator**

- owns handoff task design and required content;
- authorizes the closing Worker to materialize the handoff;
- verifies the committed handoff;
- creates the next authoritative task prompt;
- decides whether an exceptional manual handoff transfer is necessary;
- MUST NOT treat the handoff as current task authority.

**Closing Worker**

- writes only the explicitly authorized handoff path;
- does not invent the next task;
- reports and stops.

**Fresh Worker instance**

- is a new concrete execution agent assigned to the WORKER role;
- reads the handoff itself;
- treats it as state evidence only;
- verifies it against current repository truth;
- follows only the new Orchestrator task.

This section integrates with the source-of-truth model in section 5, handoff lifecycle in section 28, session rotation in section 30, compact communication in section 36, operational lifecycle artifacts in section 37, and the minimal loops in sections 33 and 34.

## 30. Session Rotation and Context Pressure

Conversational context is temporary. It MUST NOT be treated as the sole project memory.

Repository files, tests, commits, ADRs, and handoff documents are the durable source of truth.

Automatic context compaction or summarization MAY help continuity, but it MUST NOT replace an explicit handoff when a session is ending or when durable state has changed.

Visible context percentages are heuristics relative to the active Worker instance and its Worker implementation. Different implementations measure and display context differently, so percentage thresholds are guidance rather than universal guarantees or fixed token budgets. Context pressure belongs to the current Worker instance and Worker session, not to the persistent WORKER protocol role.

At approximately 80% of the active implementation's reported context usage, a role SHOULD avoid starting a large new task and SHOULD plan a checkpoint instead.

At approximately 85% or more of the active implementation's reported context usage, a role SHOULD normally finish only the current bounded task, create or update the appropriate handoff, and stop.

When no context meter exists, use behavioral indicators such as repeated questions, forgotten constraints, confused commits, scope expansion, inconsistent reasoning, or a natural project checkpoint.

A natural architectural or implementation checkpoint is preferable to waiting for complete context exhaustion.

BOOT files describe stable role or project initialization.

NEXT files describe current session state.

Neither BOOT nor NEXT files grants modification authority.

Every Worker still requires a separate authoritative task from the Orchestrator.

Handoff files SHOULD be replaced with current state rather than grow into endless chronological logs.

Handoffs MAY reference temporary committed evidence while a decision remains open. After that evidence is consumed by a durable artifact, handoffs MUST reference the accepted durable artifact instead.

The closing session MUST stop after the handoff report.

A new session MUST independently verify the current repository HEAD and public committed state.

## 31. Stopping Conditions

The Worker MUST stop when required identity checks fail, authorized files differ from expectations, secrets would be exposed, required evidence is missing, authentication fails in an unsafe way, or completion would require out-of-scope changes.

The Orchestrator MUST stop or reframe when the next step requires Cooperator approval.

## 32. Anti-Patterns

Anti-patterns include silent scope expansion, implementation before inspection, treating reports as proof, conflating public commits with local changes, inventing decisions, hiding failures, broad filesystem inspection, unnecessary package installation, Git writes without permission, orphaned committed evidence, unnecessary research-file creation, stale evidence references, retaining consumed temporary evidence without explicit continuing-value justification, treating a next-session handoff file as a task, asking the Cooperator to manually copy committed handoff files without need, embedding the complete committed handoff into every report, starting a fresh Worker without repository-state verification, allowing the closing Worker to invent the next task, defining WORKER as one named product, assuming a particular tool exists without declaring it as a task capability, using a large context window as justification to skip handoffs or source-of-truth updates, allowing hidden sub-agent delegation to expand authority, and changing protocol semantics when only the Worker implementation changes.

## 33. Minimal Orchestrator Loop

1. Understand Cooperator intent.
2. Inspect source-of-truth evidence.
3. Choose the smallest coherent next step.
4. Decide whether a Worker report is sufficient or a committed artifact is genuinely needed.
5. Issue one bounded Worker task with artifact lifecycle metadata when documentation is required.
6. Review the Worker report.
7. Verify public commits when available.
8. Decide to accept, correct, continue, pause, or close.

## 34. Minimal Worker Loop

1. Read the complete task.
2. Verify working directory, repository identity, and preconditions.
3. Verify artifact lifecycle authority before creating, consuming, or deleting documentation.
4. Inspect before changing.
5. Modify only authorized paths.
6. Run permitted validation.
7. Perform authorized Git operations only when explicitly allowed.
8. Report evidence, artifact lifecycle state, deviations, risks, and final state.

## 35. Example Task Lifecycle

The Cooperator asks for a capability.

The Orchestrator inspects the repository and determines that a design decision is missing.

The Orchestrator asks the Worker for a bounded inspection report rather than implementation.

The Worker reports current evidence and limitations.

The Orchestrator evaluates the report, asks the Cooperator to approve a direction, then issues a narrow implementation task.

The Worker implements only the authorized change, validates it, reports the result, and commits only if Git writes are authorized.

The Orchestrator verifies the public commit before authorizing the next step.

## 36. Compact Communication Mode

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

## 37. Artifact Lifecycle and Repository Hygiene

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
