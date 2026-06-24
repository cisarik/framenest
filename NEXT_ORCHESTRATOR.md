# Next Orchestrator Handoff

## 1. Role restoration

Michal is the COOPERATOR and strategic owner. The fresh ChatGPT chat is the ORCHESTRATOR. Repository execution agents fulfill the persistent WORKER protocol role through concrete Worker instances.

The ORCHESTRATOR communicates with Michal in Slovak and uses feminine grammatical gender. Worker prompts and reports are English. Worker reports must begin exactly with:

`### Report for ORCHESTRATOR_CHAT`

The ORCHESTRATOR independently verifies public commits and raw file content. Issue one bounded task at a time. Analytic Programming is provider- and model-neutral. The repository, accepted ADRs, tests, and Git history are the source of truth.

This file restores orchestration state only. It is not an executable task and grants no implementation, provider, filesystem, network, secret, or Git authority.

**Current outgoing ORCHESTRATOR session: CLOSED.**

## 2. Repository restoration

- Repository: `https://github.com/cisarik/framenest.git`
- Local path used by the closing Worker instance: `/Users/agile/framenest`
- Branch: `main`
- Provider-protocol commit: `b4f432497106c19f20dc3107ef618dd779067a7e`
- Provider-protocol subject: `fix: support NVIDIA non-thinking pending responses`
- Provider-protocol parent: `ce5801c2ba1ea6fd9cde1c281943ea8d8f714765`
- Handoff commit: the commit containing this file; resolve it from public `main`

The fresh Orchestrator must independently resolve final local `HEAD`, local `origin/main`, remote `main`, final commit subjects, parents, tree, diffs, and raw handoff contents.

Required reading before authorizing work:

1. [BOOT_ORCHESTRATOR.md](BOOT_ORCHESTRATOR.md)
2. [AP.md](AP.md)
3. [AP_ORCHESTRATOR.md](AP_ORCHESTRATOR.md)
4. [NEXT_ORCHESTRATOR.md](NEXT_ORCHESTRATOR.md)
5. [AGENTS.md](AGENTS.md)
6. [BOOT_WORKER.md](BOOT_WORKER.md)
7. [AP_WORKER.md](AP_WORKER.md)
8. [NEXT_WORKER.md](NEXT_WORKER.md)
9. [PRODUCT.md](PRODUCT.md), [SPEC.md](SPEC.md), [ROADMAP.md](ROADMAP.md), [SECURITY.md](SECURITY.md), [README.md](README.md)
10. [docs/adr/README.md](docs/adr/README.md) and ADR-0001 through ADR-0016
11. task-relevant source and tests
12. recent public Git history through the final handoff commit

## 3. Verified project state

The repository implements the foundation-stage FrameNest backend, persistence, registry, scan-preview, media-analysis preparation, and provider-neutral suggestion preview described in accepted ADRs through ADR-0016.

Not implemented: media catalog persistence, storage volumes, sidecars, persistent suggestions, review/apply workflow, GUI, gallery, playback backend, LM Studio adapter, Vercel adapter, production secret store, deployment, or Tailscale integration.

The ordinary default-suite expectation after the recent real-tool test additions is:

- `597` tests collected
- `594 passed`
- `3 skipped`

The three default skips are one opt-in NVIDIA live test and two opt-in real-media-tool parameter cases.

The fresh Orchestrator and Worker must reverify from the final public commit.

## 4. NVIDIA provider state

Public commit `b4f432497106c19f20dc3107ef618dd779067a7e` contains independently useful provider-protocol corrections:

- exact `/no_think` system message first;
- multimodal user message second;
- removed `chat_template_kwargs.enable_thinking`;
- no `response_format`, retries, tool calls, generic JSON extraction, or reasoning stripping;
- bounded authenticated HTTPS `GET` transport support;
- documented NVIDIA `202` pending-response handling through validated `requestId` and fixed status URL polling;
- bounded pending deadline and interval;
- no frame or media payload resend during polling;
- sanitized errors that do not expose request IDs, provider bodies, credentials, Authorization headers, frame data, or paths.

Deterministic evidence observed before that commit:

- NVIDIA unit tests: `21 passed`
- targeted application/AI/catalog tests: `91 passed`
- `poetry check --lock`: passed
- `compileall`: passed
- `git diff --check`: passed

## 5. Sanitized live response diagnosis

The closing Worker made exactly one additional synthetic NVIDIA diagnostic call using the modified local implementation/request contract. It did not print or persist raw assistant content, raw reasoning text, raw provider response, request body, image/base64 data, Authorization header, credential, absolute path, generated natural-language output, or private media data.

Observed structural metadata:

- diagnostic stage: `MediaSuggestionProviderInvalidResponseError`
- HTTP status code: `200`
- top-level response keys: `choices`, `created`, `id`, `kv_transfer_params`, `model`, `object`, `prompt_logprobs`, `prompt_token_ids`, `service_tier`, `system_fingerprint`, `usage`
- `choices` type: `list`
- choice count: `1`
- first-choice keys: `finish_reason`, `index`, `logprobs`, `message`, `stop_reason`, `token_ids`
- `finish_reason`: `stop`
- `stop_reason`: present, `null`
- assistant-message keys: `annotations`, `audio`, `content`, `function_call`, `reasoning`, `reasoning_content`, `refusal`, `role`, `tool_calls`
- `content`: `null`
- `reasoning_content`: string, length `4`, not whitespace-only
- `refusal`: present, null
- tool-call count: `0`
- usage prompt tokens: `568`
- usage completion tokens: `3`
- usage total tokens: `571`
- returned model ID: `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning`
- structured error object: absent

No real `printit.mp4` call has been run after this diagnosis. The next Worker must not run private-media preview until synthetic live validation passes.

## 6. Product invariants and UX direction

FrameNest AI analysis is strictly on-demand. Future gallery work should expose an explicit `Analyze` button, not automatic library-wide analysis or background cloud submission.

The analysis UI must indicate selected provider, selected model, local versus cloud execution, and whether representative frames leave the device. The user must be able to cancel an in-progress analysis.

Premium analysis animation may use masked shimmer or subtle fade transitions with truthful rotating messages such as:

- `Preparing representative frames...`
- `Analyzing visual content...`
- `Generating title and tags...`
- `Validating suggestions...`

The UI must not claim backend stage certainty that FrameNest cannot actually determine.

AI output is an editable suggestion, not catalog truth. Review must allow editing title, description, collection, tags, and suggested filename; adding and removing tags; accepting the edited proposal; or rejecting it without mutation.

No automatic rename, tagging, collection assignment, sidecar mutation, suggestion persistence, or catalog mutation is permitted without explicit future user confirmation and authorized implementation.

Cover and playback semantics:

- the user must later be able to scrub a video and select an exact frame as cover;
- the selected cover timestamp is stored independently from playback state;
- the selected cover frame becomes the displayed cover and can be regenerated deterministically from its timestamp;
- normal `Play` always starts at `00:00`;
- a separate future `Play from this position` action may start at the selected timestamp.

## 7. Maintainability debt

Record only; not authorization:

- `tests/contract/test_catalog_cli.py` is oversized;
- CLI command-family tests should likely be split;
- provider-specific composition and error mapping in the shared catalog CLI deserve bounded review;
- repetitive fixtures/assertions may be extractable carefully;
- long files alone do not justify broad architecture work.

## 8. Recommended orchestration sequence

Strategy for the fresh Orchestrator to reassess; not an executable task.

1. Verify both closeout commits publicly.
2. Reproduce the sanitized live response shape.
3. Implement one narrow correction based only on the observed shape.
4. Add one regression test.
5. Rerun synthetic live NVIDIA validation.
6. Run the real `printit.mp4` preview after synthetic success.
7. Assess suggestion quality.
8. Perform a bounded CLI/test maintainability refactor.
9. Begin the first on-demand gallery Analyze UX vertical slice.
10. Continue toward GUI Settings, secure secret store, LM Studio, Vercel, review/apply workflow, persistent media catalog, premium gallery, cover selection, and playback.

The fresh Orchestrator must choose the smallest safe next bounded step after public verification.

## 9. AI and privacy guardrails

- Cloud analysis is optional and explicitly user-triggered.
- Local scan and gallery must remain functional without AI or internet.
- Representative frames may contain private imagery.
- Absolute local paths must never be transmitted.
- Avoid whole-video upload initially.
- No biometric or person-identification claim.
- No automatic person naming.
- No secret in source, database, logs, reports, tests, or subprocess arguments.
- API responses are untrusted external data.
- Provider output is suggestion evidence, not catalog truth.
- User confirmation is mandatory before mutation.

## 10. Session and context strategy

- This Worker instance is intentionally closed after a context-heavy NVIDIA live/protocol/debug cycle.
- Exact context telemetry is not exposed in repository files, but the session accumulated enough live-debug and handoff state that a fresh Worker instance is safer for the next correction.
- Initialize one fresh Worker instance assigned to the WORKER role for the next coherent implementation session.
- Do not manually copy repository handoffs into new Worker sessions; the fresh Worker reads them from the repository.
- Verify every closing handoff commit publicly.

User-facing Worker prompts may use: `Toto pošli WORKEROVI ako jeden prompt:`

## 11. First response expected from fresh Orchestrator

The fresh Orchestrator must:

1. read and independently verify public repository state;
2. resolve the final handoff commit;
3. verify both NEXT files against public raw content;
4. summarize implemented state, deterministic evidence, and sanitized live response shape;
5. identify stale or contradictory handoff claims;
6. propose the smallest safe next task;
7. provide one authoritative prompt for a fresh Worker instance assigned to the WORKER role only after verification;
8. not implement code in ORCHESTRATOR chat;
9. not ask the Cooperator to paste repository files that already exist in the repository.

## 12. Handoff lifecycle

- classification: non-authoritative Orchestrator-session handoff
- intended consumer: one fresh future ORCHESTRATOR session
- discoverability: repository root and Orchestrator bootstrap reading order
- retention: replace only at a future explicitly authorized Orchestrator closeout
- supersession and cleanup owner: explicitly authorized closing Worker instance
- Git history is the archive; the active tree must contain only the latest handoff

**Current outgoing ORCHESTRATOR session: CLOSED.**
