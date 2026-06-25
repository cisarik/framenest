# ADR-0020: On-Demand AI Suggestion Review

## Status

`Accepted`

## Decision Date

`2026-06-25`

## Decision Authority

The Orchestrator authorized this bounded product slice through task
`FRAMENEST-CYCLE-060-EDITABLE-AI-SUGGESTION-REVIEW`.

## Context

FrameNest already has deterministic read-only local media-analysis preparation
per [ADR-0015](0015-deterministic-local-media-analysis-preparation.md),
a provider-neutral NVIDIA NIM suggestion prototype per
[ADR-0016](0016-provider-neutral-media-suggestions-and-nvidia-nim-prototype.md),
a same-origin local media-analysis preview API per
[ADR-0018](0018-local-media-analysis-preview-api.md), and VLM-only bounded JPEG
derivatives plus NVIDIA documented instruct mode per
[ADR-0019](0019-vlm-image-derivatives-and-nvidia-instruct-mode.md).

Cycle 059 provided Worker-observed evidence that one explicit live NVIDIA
request using the current JPEG VLM transport and prompt version
`framenest-media-suggestion-v2` returned non-empty final content and passed
strict FrameNest suggestion validation. That evidence supports exposing the
existing provider-neutral workflow through the loopback server for an editable,
non-persistent browser review.

## Decision

### Explicit on-demand cloud analysis

AI suggestion generation is never automatic. It is not triggered by page load,
library scan, or local media inspection. It requires one explicit user action
and explicit cloud-upload confirmation for every request.

The server reuses the existing provider-neutral `PreviewMediaSuggestion`
application boundary. The request performs no automatic retry. Provider
credentials remain exclusively server-side.

### Capability discovery

The browser may load a sanitized same-origin capability response that reports:

- whether the prototype provider is currently configured;
- provider ID;
- model ID;
- prompt version;
- local/cloud classification;
- whether explicit confirmation is required.

Capability discovery performs no provider network call and exposes no
credential, environment value, Authorization header, key prefix, key length, or
credential object state. The local application remains usable when no provider
credential exists.

### Temporary credential source

Until GUI Settings and an operating-system secret-store adapter exist, the
server composition boundary may read `NVIDIA_API_KEY`.

The key remains server-side. It must not enter browser responses, settings API
responses, logs, exceptions, `repr` output, Worker reports, persisted catalog
data, SQLite, or browser storage. Missing credentials must not prevent the local
FrameNest application from starting; they disable only the cloud suggestion
capability.

This environment-based source is temporary and will be superseded by GUI
Settings and a secret-store adapter. It must not be renamed into a browser-facing
or `FRAMENEST_` client setting.

### Editable preview semantics

The suggestion is untrusted, editable, ephemeral, and not catalog truth. It is
never automatically applied.

The user may edit title, description, collection, tags, and suggested filename.
The user may inspect confidence, evidence, uncertainties, provider, model, and
prompt version.

`Accept draft for this session` validates the current browser form, marks the
ephemeral review as accepted in current page memory, and shows that no file or
catalog change occurred. `Reject draft` discards the current browser review
draft and shows that no change was applied.

Neither action calls a mutation endpoint. This decision does not introduce a
write API.

### Cancellation boundary

The browser may show a pending state, but it must not present an action that
claims to terminate an already-running synchronous FFmpeg or provider operation.
True cancellation remains deferred to a future job architecture.

## Consequences

### Positive

- The local browser can review a validated AI suggestion without catalog or file
  mutation.
- Provider, model, prompt, and cloud status are visible before the user
  confirms the request.
- The existing provider-neutral application boundary remains the central
  contract.
- Missing credentials degrade to an unavailable cloud capability instead of
  blocking local library and media-analysis workflows.

### Negative / limitations

- The synchronous route cannot provide true cancellation.
- Suggestions are not durable and disappear with the page session.
- Provider/model selection and GUI credential entry remain absent.
- The browser review form is a pre-alpha vanilla implementation rather than the
  final gallery review UX.

## Rejected Scope

Persistent media catalog updates, applying accepted suggestions, mutation
endpoints, rename/move/tag behavior, sidecars, cover selection, gallery
thumbnail cache, playback, downloads, GUI Settings, secret-store integration,
provider selection, model discovery, LM Studio, Vercel AI Gateway, retries,
background jobs, WebSockets, SSE, polling, true cancellation, authentication,
CORS, Tailscale, NUC deployment, and multi-device aggregation are out of scope.

## Security Boundaries

- Default binding remains loopback-first.
- No CORS middleware is introduced.
- No browser credential is exposed.
- No direct browser-to-provider request is introduced.
- No provider call occurs on startup, page load, capability discovery, scan, or
  local media inspection.
- No provider call occurs without explicit confirmation.
- No full video, PNG frame, raw JPEG frame, base64 frame payload, raw provider
  response, raw prompt, reasoning content, tool calls, absolute media path, or
  database path is returned by the suggestion API.
- No media or catalog mutation is introduced.
- No migration is introduced.
- No browser persistence is introduced.

## Revisit Triggers

Revisit when authorizing persistent media records, applying accepted
suggestions, editable review persistence, gallery thumbnail cache, GUI Settings,
secret-store implementation, provider/model selection, additional providers,
background jobs, real cancellation, authentication, or remote/multi-device AI
workflows.

## Related Documents

- [ADR index](README.md)
- [ADR-0015](0015-deterministic-local-media-analysis-preparation.md)
- [ADR-0016](0016-provider-neutral-media-suggestions-and-nvidia-nim-prototype.md)
- [ADR-0018](0018-local-media-analysis-preview-api.md)
- [ADR-0019](0019-vlm-image-derivatives-and-nvidia-instruct-mode.md)
- [SPEC.md](../../SPEC.md)
- [ROADMAP.md](../../ROADMAP.md)
