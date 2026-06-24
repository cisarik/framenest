# Next Orchestrator Handoff

## 1. Bootstrap identity

Michal is the COOPERATOR and strategic owner. Communication with Michal is Slovak. Self-reference in Slovak uses feminine grammatical gender.

Worker prompts and Worker reports are professional English. Every Worker report begins exactly:

`### Report for ORCHESTRATOR_CHAT`

When introducing a Worker prompt to Michal, use exactly:

`Toto pošli WORKEROVI ako jeden prompt:`

Shape one bounded task at a time.

This file restores orchestration context only. It is not an executable task and grants no implementation, filesystem, network, provider, secret, migration, dependency, or Git authority. A new authoritative Orchestrator task prompt is the only concrete task authority for a Worker instance.

## 2. Role and instance model

The persistent protocol roles are COOPERATOR, ORCHESTRATOR, and WORKER. These roles persist across instance rotation.

ORCHESTRATOR is the persistent coordination role. An Orchestrator implementation is the concrete system fulfilling that role. An Orchestrator instance is one initialized execution entity temporarily assigned to the ORCHESTRATOR role. An Orchestrator session is that instance's bounded lifecycle and context.

WORKER is the persistent repository execution role. A Worker implementation is the concrete execution system fulfilling that role. A Worker instance is one initialized execution agent temporarily assigned to the WORKER role. A Worker session is that instance's bounded lifecycle and context.

Execution client, agent implementation, model, and provider are separate identity layers. Do not describe a fresh Orchestrator instance or fresh Worker instance as a new persistent role.

## 3. Public verification state

Cycle 054 public verification: PASS.

- SHA: `46da061d0443176a1067d18e30bf5aaff2259b3d`
- Parent: `d94b65bc761e754cfba9034d8ea21edb15406952`
- Subject: `feat: add local web application shell`
- Result: packaged local web application foundation and ADR-0017.

Cycle 055 public verification: PASS.

- SHA: `3e6008886ad7925ca14e171839ad479eafa443a0`
- Parent: `46da061d0443176a1067d18e30bf5aaff2259b3d`
- Subject: `feat: add read-only library browser`
- Publicly verified changed paths count: nine.
- Result: real registered-library listing and explicit read-only scan-preview API/UI.

The closeout commit containing this handoff is newer and must be independently verified by the fresh Orchestrator instance. Worker reports are evidence-bearing testimony, not repository truth. Runtime tests and local provider behavior remain Worker-observed evidence until independently rerun.

## 4. Current product state

FrameNest now has a real runnable local FastAPI server. The server serves a packaged local web application from the installed Python package.

The browser can:

- load `GET /`;
- read same-origin `GET /health`;
- list real registered libraries through `GET /api/libraries`;
- let the user explicitly run bounded read-only scan preview through `POST /api/libraries/{library_id}/scan-preview`.

Returned scan candidates remain ephemeral preview data. They are not persistent media records and are not catalog truth.

FrameNest still has no persistent media catalog and no completed flagship gallery. Library registration remains CLI-only. Server startup does not run migrations automatically. Local functionality works without AI and without internet. Provider credentials remain server-side and are not exposed to browser code.

## 5. Product strategy

Preferred progression for the fresh Orchestrator to reassess:

1. Verify the closeout commit and raw handoffs.
2. Initialize a fresh Worker instance only with one new authoritative prompt.
3. Strongly consider user-triggered local media-analysis preview as the next visible vertical slice.
4. Connect scan candidate selection to existing deterministic analysis.
5. Show real technical metadata and representative frames.
6. Only afterward decide whether media catalog persistence, cover workflow, or on-demand AI review is the best next slice.
7. Do not let NVIDIA debugging block local product progress.

This sequence is strategic guidance, not pre-authorized work.

## 6. Candidate next task analysis

Local analysis preview is likely stronger than immediately introducing media migration `0004` because it reuses implemented and tested behavior, creates visible product value, moves toward premium gallery cards and later Analyze UX, remains read-only and reversible, and avoids prematurely freezing the logical-media/location persistence model.

Risks that the fresh Orchestrator must inspect before shaping a task:

- secure library-relative path resolution;
- preventing arbitrary file access and path traversal;
- bounding PNG and frame payloads;
- no persistent or leaked temporary frame artifacts;
- request cancellation and timeout behavior;
- no accidental full-media streaming;
- browser memory use;
- no raw root path exposure;
- testability without real user media.

The fresh Orchestrator instance must inspect current analysis ports, adapters, tests, and accepted ADRs before authorizing implementation.

## 7. NVIDIA evidence

Preserved sanitized facts only:

- last real synthetic provider call reached NVIDIA;
- HTTP `200`;
- one choice;
- `finish_reason=stop`;
- assistant `content=null`;
- assistant `reasoning_content` was a short string;
- no refusal;
- no tool calls;
- returned model: `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning`;
- strict parser remained closed;
- no successful real `printit.mp4` suggestion preview followed that diagnosis.

Do not include, request, or invent raw reasoning content. Reasoning content must not be surfaced as the user-facing suggestion.

## 8. Product invariants

- FrameNest remains local-first.
- Backend behavior remains loopback-first and must not be publicly exposed by default.
- AI is only on explicit request.
- AI output is editable suggestion only and requires accept/reject review.
- No automatic rename, move, tagging, collection assignment, sidecar write, or catalog truth update.
- Representative frames may leave the device only after explicit cloud confirmation.
- Provider and model must be visible in future AI UI.
- Local/cloud status must be visible in future AI UI.
- Cover selection stores an exact timestamp.
- Cover timestamp does not alter standard playback start.
- Standard Play starts at `00:00`.
- Premium gallery and downloading remain flagship capabilities.
- Avoid endless infrastructure polishing.
- Stop once clear acceptance criteria pass.

## 9. Fresh-session procedure

The fresh Orchestrator instance should:

1. Independently verify public `main`.
2. Verify this closeout commit's SHA, parent, subject, and exact changed paths.
3. Read raw `NEXT_WORKER.md` and `NEXT_ORCHESTRATOR.md`.
4. Compare them with repository code and accepted ADRs.
5. Distinguish public evidence from Worker-observed runtime evidence.
6. Reassess the next task.
7. Produce exactly one authoritative prompt for a fresh Worker instance.
8. Never ask Michal to manually paste repository files that are publicly available.

## 10. Additional future boundaries

- Persistent media catalog and migration `0004` remain undecided.
- Storage volumes, media locations, sidecars, premium gallery cards, covers, playback, downloads, Settings, provider selection, model discovery, and editable AI review remain future tasks.
- AI remains on-demand.
- AI suggestions remain non-persistent until a future task explicitly authorizes review and persistence behavior.
- Unresolved NVIDIA `content=null` plus `reasoning_content` evidence is preserved but must not block local UI progress.

## 11. Latest Worker-observed evidence

The following runtime evidence is Worker-observed and must be rerun when a future task requires it:

- untouched Cycle 055 baseline: `627` collected, `624 passed`, `3 skipped`;
- final Cycle 055 state: `644` collected, `641 passed`, `3 skipped`;
- final full `-W error`: `641 passed`, `3 skipped`;
- targeted tests: `31 passed`;
- build and wheel inspection: passed;
- in-process API smoke: passed;
- no visual browser inspection was performed.

## 12. Handoff lifecycle

- Classification: non-authoritative Orchestrator-session handoff.
- Intended consumer: one fresh future Orchestrator instance assigned to the persistent ORCHESTRATOR role.
- Discoverability: repository root and Orchestrator bootstrap reading order.
- Retention: replace only at a future explicitly authorized Orchestrator closeout.
- Supersession and cleanup owner: explicitly authorized closing Worker instance.
- Git history is the archive; the active tree should contain only the latest handoff.

Current Orchestrator session context: **CLOSED AFTER CLOSEOUT VERIFICATION**. The persistent ORCHESTRATOR role continues.
