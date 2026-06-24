# ADR-0019: VLM Image Derivatives and NVIDIA Instruct Mode

## Status

`Accepted`

## Decision Date

`2026-06-24`

## Decision Authority

The Orchestrator authorized this bounded VLM transport update through task
`FRAMENEST-CYCLE-058-VLM-JPEG-INPUT-AND-NVIDIA-INSTRUCT-MODE`.

## Context

FrameNest already prepares bounded lossless PNG representative frames locally
per [ADR-0015](0015-deterministic-local-media-analysis-preparation.md), exposes
those PNG frames to the local browser technical preview per
[ADR-0018](0018-local-media-analysis-preview-api.md), and has a provider-neutral
NVIDIA NIM suggestion prototype per
[ADR-0016](0016-provider-neutral-media-suggestions-and-nvidia-nim-prototype.md).

The initial NVIDIA prototype sent PNG data URLs and used a synthetic
`/no_think` system message. This decision updates only the provider-image and
NVIDIA request-mode portions of ADR-0016. All mutation, persistence, cloud
confirmation, and provider-secret boundaries remain unchanged.

## Decision

### Separate Image Representations

Internal deterministic local-analysis frames remain bounded lossless PNG. The
browser local technical preview remains unchanged and continues to return PNG
frames.

VLM transport uses derived JPEG images. Future gallery and cover thumbnails may
also use derived JPEG profiles, but gallery persistence is not implemented by
this decision.

One canonical source may have multiple reproducible derivatives for different
consumers. VLM transport images are ephemeral and must not be persisted.

### VLM JPEG Profile

The initial VLM JPEG profile is:

- input: a validated FrameNest-generated PNG representative frame;
- output MIME type: `image/jpeg`;
- maximum long edge: `768` pixels;
- preserve aspect ratio;
- output color mode: RGB;
- JPEG quality: `82`;
- chroma subsampling: `4:2:0`;
- progressive encoding: disabled;
- optimization pass: disabled unless deterministic tests prove identical output;
- EXIF, XMP, ICC, comments, and unrelated source metadata are not copied;
- maximum encoded size: `1_572_864` bytes per frame;
- maximum aggregate JPEG payload: `4_718_592` bytes;
- maximum frame count remains three;
- conversion is deterministic for identical input bytes and library version;
- no disk file is created.

The profile is an initial quality and size compromise, not a universal optimum.

Pillow is accepted as the concrete implementation dependency because it provides
in-memory PNG decode, resize, RGB conversion, and JPEG encode without shell
execution or temporary files. It is a cross-platform Python package and can be
reused behind the derived-image boundary later. Pillow does not replace FFmpeg
for media decoding or representative-frame extraction, and it must not become a
domain-layer dependency.

### Token-Accounting Honesty

JPEG generally reduces request bytes compared with PNG photographic frames.
Base64 still adds transport overhead. Smaller encoded byte size does not by
itself prove fewer visual input tokens.

Visual token accounting may depend primarily on provider preprocessing,
dimensions, tiling, and model implementation. FrameNest must report request
bytes separately from provider token usage. FrameNest may claim token savings
only when comparable provider usage evidence demonstrates them.

Dimension reduction and frame-count reduction are the controlled mechanisms
intended to reduce visual workload.

### NVIDIA Instruct Mode

NVIDIA requests use the documented non-thinking request form:

- no `"/no_think"` system message;
- no synthetic system message solely for mode selection;
- `chat_template_kwargs.enable_thinking = false`;
- `temperature = 0.2`;
- `top_k = 1`;
- `max_tokens = 1024`;
- `stream = false`.

This decision does not add undocumented `response_format` behavior. The
endpoint and model ID remain unchanged.

### Human-Review Output Policy

Suggestion output is always an untrusted editable draft for a human reviewer.
Insufficient context is not by itself a reason for the model to refuse.
Uncertainties must be represented explicitly.

FrameNest must never automatically apply title, description, collection, tags,
or filename. Reasoning output must never be surfaced as the suggestion.

Strict validated JSON remains the primary contract in this cycle. A future
review UI may support a bounded non-empty final-content fallback when strict JSON
fails, but that raw-draft fallback is deferred and must not consume
`reasoning_content`.

## Consequences

### Positive

- VLM transport payloads are smaller for photographic frames in byte terms.
- Local and browser PNG semantics remain stable.
- The provider request follows the documented NVIDIA non-thinking mode.
- Derived-image behavior is testable without provider calls.

### Negative / limitations

- Pillow is a new runtime dependency.
- JPEG is lossy and not appropriate as the canonical local analysis frame.
- Byte reduction is not proof of token reduction.
- Provider response behavior may still vary externally.

## Revisit Triggers

Revisit when authorizing gallery thumbnails, persistent covers, provider/model
selection, additional providers, raw final-content review fallback, prompt
version changes, measured provider-token comparisons, or alternate derivative
profiles.

## Rejected Scope

This decision does not implement gallery persistence, cover storage, media
catalog tables, browser AI review, Settings, secret storage, provider selection,
model discovery, another provider, retries, jobs, migrations, or automatic
suggestion application.

## Security Boundaries

- No provider call occurs without explicit cloud confirmation.
- No provider secret is exposed to browser code or repository files.
- No image payload, base64 payload, Authorization header, raw provider response,
  prompt body, or reasoning content may enter logs, reports, exceptions, or
  committed artifacts.
- VLM JPEG derivatives are in-memory runtime artifacts only.
- No temporary frame file or image cache directory is created.

## Relationship to ADR-0016

This ADR partially supersedes ADR-0016 only for provider image representation and
NVIDIA request mode. ADR-0016 remains authoritative for the provider-neutral
application boundary, temporary credential boundary, model/endpoint selection,
explicit cloud confirmation, no mutation, no persistence, and strict suggestion
validation unless later superseded.

## Related Documents

- [ADR index](README.md)
- [ADR-0015](0015-deterministic-local-media-analysis-preparation.md)
- [ADR-0016](0016-provider-neutral-media-suggestions-and-nvidia-nim-prototype.md)
- [ADR-0018](0018-local-media-analysis-preview-api.md)
- [SPEC.md](../../SPEC.md)
- [ROADMAP.md](../../ROADMAP.md)
