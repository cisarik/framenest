# ADR-0016: Provider-Neutral Media Suggestions and NVIDIA NIM Prototype

## Status

`Accepted`

## Decision Date

`2026-06-24`

## Decision Authority

The Orchestrator authorized this bounded prototype through task `FRAMENEST-CYCLE-050-NVIDIA-NIM-MEDIA-SUGGESTION-VERTICAL-SLICE`.

## Context

FrameNest has a deterministic read-only local media preparation boundary per [ADR-0015](0015-deterministic-local-media-analysis-preparation.md). The next step is a complete but non-persistent AI-assisted suggestion preview that reuses local preparation and sends only bounded PNG frames and metadata to a cloud provider after explicit operator confirmation.

## Decision

### Provider-neutral application boundary

The application layer owns immutable request and suggestion values, a `MediaSuggestionProvider` port, a service composing local preparation and suggestion generation, and FrameNest-owned sanitized errors.

The application layer does not depend on NVIDIA request/response structures, HTTP, API keys, environment variables, base64 encoding, provider SDKs, filesystem paths, SQLAlchemy, or CLI classes.

The first infrastructure adapter is NVIDIA NIM. Future LM Studio and Vercel adapters must be able to implement the same port without a plugin framework in this slice.

### Temporary development credential boundary

For this prototype only:

- read `NVIDIA_API_KEY` at the CLI/infrastructure composition boundary;
- never place it in `FrameNestSettings`;
- never reuse `FRAMENEST_API_KEY`;
- never store it in SQLite or `.env` automatically;
- never log it or include it in exceptions, reports, snapshots, or command arguments;
- credential-bearing objects exclude their value from `repr`.

This is temporary developer behavior, not the final Settings GUI or secret-store architecture.

### NVIDIA prototype constants

- provider ID: `nvidia-nim`
- model ID: `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning`
- endpoint: `https://integrate.api.nvidia.com/v1/chat/completions`

This is a trial/free prototype facility whose availability, quotas, and terms may change. It is not described as permanently free or production-unlimited. No CLI base-URL override exists in this slice.

### Data sent to the provider

Send only basename, candidate kind, bounded technical metadata, one to three prepared PNG frames, and prompt/schema version.

Do not send absolute library roots, database paths, device or library display names, environment values, FFmpeg paths, raw subprocess output, complete videos, audio, unrelated files, or application logs.

The prototype sends PNG frames as base64 data URLs inside the provider request body.

### Explicit cloud confirmation

No provider call may occur without `--confirm-cloud-upload`. Missing confirmation or missing `NVIDIA_API_KEY` fails before local preparation and before any network request.

### No mutation or persistence

The operation must not rename, move, delete, tag, create collections, update sidecars, update the catalog, run migrations, or persist suggestions. Output is an untrusted preview requiring future human review.

### Prompt contract

Prompt version `framenest-media-suggestion-v1` requires one JSON object with title, description, collection, tags, suggested_filename, confidence, evidence, and uncertainties. The prompt instructs evidence-only English output, anti-injection behavior, extension preservation, and no Markdown commentary.

Provider output is not trusted for provider ID, model ID, or prompt version. FrameNest attaches those values after validation.

## Alternatives Considered

### NVIDIA NIM first prototype

**Selected.** Enables a real usable AI prototype behind a provider-neutral port while reusing local preparation.

### Vercel or LM Studio first

Deferred. Same port should accept future adapters without changing the application contract.

### Persistent suggestion storage

Rejected for this slice. Preview only.

## Consequences

### Positive

- End-to-end non-persistent suggestion preview through the catalog CLI.
- Provider-neutral application contract.
- Explicit cloud confirmation and bounded outbound payload policy.

### Negative / limitations

- NVIDIA trial availability may change.
- No model discovery.
- Temporary environment credential only.
- No GUI secret store.
- Model output quality and exact JSON reliability require real-corpus evaluation.
- Default tests use synthetic fixtures only.

## Security Boundaries

- HTTPS only with default TLS verification.
- Redirects rejected.
- Bounded request and response bodies.
- Sanitized transport and provider errors.
- No API key, Authorization header, absolute path, raw provider response, PNG/base64 payload, or raw prompt in CLI success output.

## Rejected Scope

Vercel, LM Studio, GUI Settings, model discovery, permanent secret storage, suggestion persistence, automatic tagging, renaming, file movement, sidecars, gallery, and API server endpoints remain out of scope.

## Conditions Requiring a Future ADR

Revisit when authorizing suggestion persistence, confirmed rename/tag application, additional providers in production, GUI secret storage, model discovery, or server/API exposure.
