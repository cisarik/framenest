# ADR-0018: Local Media Analysis Preview API

## Status

`Accepted`

## Decision Date

`2026-06-24`

## Decision Authority

The Orchestrator authorized this bounded local web preview through task
`FRAMENEST-CYCLE-057-LOCAL-MEDIA-ANALYSIS-PREVIEW`.

## Context

FrameNest already has deterministic read-only local media-analysis preparation
per [ADR-0015](0015-deterministic-local-media-analysis-preparation.md), and a
packaged same-origin local web application per
[ADR-0017](0017-initial-local-web-application-delivery.md). ADR-0015 explicitly
required a future decision before exposing media-analysis results through the
server API.

The next useful product-visible slice is one explicit browser-triggered local
technical inspection of one candidate returned by scan preview. This remains
pre-alpha inspection, not the final AI Analyze workflow.

## Decision

### API Exposure

The existing deterministic media-analysis preparation may be exposed through
one same-origin loopback API endpoint:

```text
POST /api/libraries/{library_id}/media-analysis-preview
```

The browser submits only:

- a registered library ID in the path;
- a validated library-relative candidate path in the request body.

The browser must never submit or receive an absolute library root.

The server remains responsible for:

- repository lookup;
- path validation;
- containment and symlink checks;
- ffprobe and ffmpeg invocation;
- metadata preparation;
- frame extraction;
- response validation;
- sanitized error mapping.

The endpoint returns bounded technical metadata and up to three representative
PNG frames prepared by the existing application service. The response omits
absolute media paths, database paths, ffprobe and ffmpeg executable paths, raw
subprocess output, raw stderr, provider concepts, API credentials,
`ffprobe_version`, and `ffmpeg_version`.

### Initial Frame Delivery Strategy

For this first pre-alpha loopback-only slice, representative PNG frames are
returned inline in the successful JSON response as standard base64 strings.

This is accepted initially because:

- each request is explicit and user-triggered;
- at most three frames are returned;
- existing strict raw frame and aggregate bounds remain authoritative;
- no server-side token store is needed;
- no temporary image files are created;
- no frame persistence is introduced;
- no background cleanup scheduler is needed;
- no additional frame-fetch authorization model is introduced;
- the contract is simple, deterministic, and testable;
- operation is same-origin and loopback-first.

Every successful response must use `Cache-Control: no-store`. Task-owned error
responses also use `Cache-Control: no-store`.

Browser code must decode `payload_base64` locally into PNG `Blob` objects, create
object URLs for display, and revoke those object URLs when replacing the preview
and during page teardown.

Raw frame payloads must not enter logs, exceptions, Worker reports, or
persistent storage.

### Cancellation

Cooperative backend cancellation is not implemented in this synchronous preview
slice. The existing subprocess operations remain bounded by their current
timeouts.

The UI must not claim that it can terminate already-running ffprobe or ffmpeg
subprocesses. A future background or job architecture must revisit true
cancellation.

## Consequences

### Positive

- The browser can explicitly inspect one scan candidate without creating media
  records.
- The API reuses the existing deterministic application service and local
  adapter boundary.
- The implementation remains stateless, local-only, provider-free, and
  non-persistent.
- Testing can prove exact base64 round trip, metadata mapping, and sanitized
  errors without requiring real ffmpeg or ffprobe in the default suite.

### Negative / limitations

- Base64 increases response and browser-memory size.
- JSON serialization temporarily duplicates frame data in memory.
- This mechanism is unsuitable as an assumed final remote-server or
  large-gallery design.
- Inline frame delivery is not a thumbnail cache, streaming protocol, or
  gallery-wide prefetch mechanism.

## Revisit Triggers

Revisit this decision when any of the following are authorized or become
material:

- remote clients;
- background jobs;
- many concurrent analyses;
- larger frame policies;
- persistent thumbnails;
- gallery-wide prefetching;
- streaming or incremental delivery;
- authentication or multi-user server operation;
- true cancellation semantics.

## Rejected Scope

This decision does not introduce an ephemeral server token cache, temporary frame
directory, multipart protocol, WebSocket, polling job, persistent blob store,
media catalog tables, persistent thumbnails, playback, downloads, AI providers,
provider selection, or cloud analysis.

## Security Boundaries

- Default bind remains loopback-first.
- No CORS middleware is introduced.
- No authentication behavior is changed.
- No provider call or network media-analysis call is introduced.
- No database mutation, migration, automatic scan, or automatic analysis is
  introduced.
- No absolute root, arbitrary file path, traversal path, hidden path segment,
  symlink candidate, full-media stream, complete-media hash, temporary PNG file,
  or raw payload logging is permitted.

## Related Documents

- [ADR index](README.md)
- [ADR-0014](0014-safe-library-scan-preview.md)
- [ADR-0015](0015-deterministic-local-media-analysis-preparation.md)
- [ADR-0017](0017-initial-local-web-application-delivery.md)
- [SPEC.md](../../SPEC.md)
- [ROADMAP.md](../../ROADMAP.md)
