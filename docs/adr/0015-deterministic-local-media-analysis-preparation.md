# ADR-0015: Deterministic Local Media Analysis Preparation

## Status

`Accepted`

## Decision Date

`2026-06-24`

## Decision Authority

The Orchestrator authorized this initial local media-analysis preparation decision and test-first implementation through bounded task `FRAMENEST-CYCLE-047-DETERMINISTIC-LOCAL-MEDIA-ANALYSIS-PREPARATION`.

## Context

FrameNest has a bounded read-only library scan preview per [ADR-0014](0014-safe-library-scan-preview.md). The next step must inspect one explicitly selected MP4 or GIF candidate from a registered library, return bounded technical metadata, and prepare a small number of deterministic representative PNG frames in memory without persistence, provider calls, or media mutation.

Relevant existing decisions:

- [ADR-0013](0013-initial-library-registry.md) provides registered library roots.
- [ADR-0014](0014-safe-library-scan-preview.md) provides extension-hint candidate classification and symlink policy for scan preview.

## Decision

### Purpose

The first local media-analysis preparation boundary is a bounded, deterministic, read-only operation on one explicit scan candidate within one registered library.

It exists to:

- prove safe single-file inspection inside a registered root;
- extract bounded technical metadata through optional external tools;
- prepare at most three exact-distinct representative PNG frames in memory;
- prepare future provider-neutral AI workflows without coupling this slice to any provider.

It is not media import, catalog persistence, thumbnail storage, scene detection, or AI analysis.

### External tool boundary

`ffprobe` and `ffmpeg` are optional external runtime tools. They are not Python package dependencies. FrameNest never installs them automatically.

Tool discovery uses the standard library and resolves an absolute executable path. Invocation never uses a shell. Input paths are passed as argv elements, never interpolated into a command string. The adapter validates that the resolved executable identifies itself as the expected tool.

This slice does not invent a semantic minimum FFmpeg version. Compatibility is initially behavioral: the required command contract must pass the opt-in real-tool integration test. Observed local versions are evidence only and are not hardcoded into product behavior.

### Architectural layering

The domain layer remains unaware of FFmpeg, subprocesses, paths, providers, HTTP, Pydantic, SQLAlchemy, and CLI concerns.

The application layer owns provider-neutral immutable values, sanitized errors, the preparation port, target-timestamp policy, and the preparation service.

The infrastructure layer owns executable discovery, subprocess execution, ffprobe JSON parsing, ffmpeg extraction, and local filesystem safety.

The CLI remains a development/operator adapter, not final desktop UX. No provider-specific type or concept enters the domain or application boundary.

### Read-only behavior

The operation may:

- look up an already registered library;
- validate one explicit relative candidate path;
- read local file metadata;
- allow ffprobe and ffmpeg to decode that selected file;
- hold bounded PNG bytes in memory;
- return a preview result.

The operation must not:

- modify the media file or its directory;
- write a sidecar or thumbnail;
- leave a temporary frame on disk;
- update or migrate SQLite;
- hash the complete media file;
- scan the entire library;
- invoke a provider;
- use the network.

### Representative-frame policy

The initial deterministic preview policy is:

- requested frame count: exactly `3`;
- target positions: `10%`, `50%`, and `90%` of known duration using deterministic integer millisecond arithmetic;
- clamp every target to a valid non-negative position below the known duration;
- remove duplicate target timestamps while preserving order;
- if duration is unknown or non-positive, attempt only timestamp `0`;
- extract one image for each target independently;
- preserve successful target order;
- exact-deduplicate produced frames by SHA-256 of the final PNG payload;
- never duplicate a frame to pretend that three frames exist;
- return fewer than three frames honestly;
- if an individual target cannot be decoded, record a sanitized warning and continue;
- if no frame can be decoded, fail with a sanitized FrameNest-owned error.

This is an initial exact-duplicate preview policy, not perceptual scene detection and not final catalog truth.

### Output bounds

Initial safety limits are explicit code constants:

| Limit | Value |
|---|---|
| ffprobe timeout | 15 seconds |
| each ffmpeg frame timeout | 30 seconds |
| ffprobe stdout maximum | 1 MiB |
| retained subprocess stderr maximum | 64 KiB |
| each PNG payload maximum | 5 MiB |
| aggregate PNG payload maximum | 15 MiB |
| maximum output dimensions | fit within 1024 × 1024 while preserving aspect ratio |
| maximum representative frames | 3 |

Oversized output is rejected with a sanitized FrameNest-owned error. FrameNest does not silently truncate JSON or image payloads and then treat them as valid.

### Filesystem and symlink policy

The adapter operates only inside the registered library root. Nested symlink path components and final symlink candidates are rejected. The registered root itself may remain a symlink, matching [ADR-0014](0014-safe-library-scan-preview.md). Dot-prefixed path segments are rejected to remain aligned with scan-preview hidden-entry policy.

A residual local time-of-check/time-of-use window remains: another process may change filesystem state after validation and before tool execution. This slice documents that limitation and does not attempt a large platform-specific file-descriptor redesign.

### Artifact lifecycle

Representative images in this slice are runtime ephemeral in-memory artifacts produced by the local FFmpeg adapter, consumed by the application result and CLI summary, forbidden from persistence, and retained only for the lifetime of the operation/result object. Cleanup is owned by the caller and normal Python object lifecycle.

The CLI must not print, base64-encode, or persist frame payloads.

ADR-0015 itself is durable normative architecture for future Workers and Orchestrators until explicitly superseded.

### Development CLI

`framenest-catalog library analyze-preview --id <library-id> --path <relative-path>` performs one read-only preparation on one explicit candidate. It requires the database at migration head, performs no automatic migration, performs no database write, and emits one compact deterministic JSON object on success.

### Testing strategy

- application unit tests for values, target policy, and service delegation;
- infrastructure unit tests with injected fake process runners;
- filesystem safety tests using pytest temporary directories only;
- CLI contract tests;
- opt-in real-tool integration tests gated by `FRAMENEST_RUN_REAL_MEDIA_TOOLS=1` using synthetic fixtures generated locally by ffmpeg.

## Alternatives Considered

### FFmpeg/ffprobe external executables

**Selected for this slice.** Mature cross-platform media support, no provider coupling, no large Python binary dependency, a testable argv boundary, and replaceability behind an application port.

### Python media bindings

Rejected for this slice because they add heavyweight native/binary coupling, complicate portability and testing, and are unnecessary for a bounded read-only prototype.

### Direct full-video provider upload

Rejected for the initial prototype because it couples inspection to network availability, provider policy, cost, and privacy risk before local safety boundaries are proven.

### Browser/desktop media decoding later

Deferred. Useful for future desktop UX, but not required to prove the local operator boundary and not equivalent to catalog-grade ingestion truth.

## Consequences

### Positive

- Provider-neutral application boundary for later AI workflows.
- Deterministic representative-frame policy with honest fewer-than-three results.
- Shell-free, timed, output-bounded subprocess execution.
- Read-only operator evidence without catalog persistence.

### Negative / limitations

- Exact PNG digest deduplication is not perceptual deduplication.
- Observed FFmpeg versions do not establish a complete compatibility matrix.
- Codec and container behavior remain dependent on the installed FFmpeg build.
- Residual TOCTOU risk remains between validation and tool execution.

## Security Boundaries

- No shell execution.
- No network or provider calls in this slice.
- No absolute media path, database path, raw OS error, or raw subprocess stderr in CLI output or sanitized application errors.
- No PNG payload in CLI output, logs, exceptions, or reports.
- No complete-media hashing.
- No implicit migration or database mutation.

## Rejected Scope

AI providers, model discovery, API key handling, GUI Settings, media catalog persistence, renaming, tagging, thumbnail persistence, gallery behavior, migration `0004`, persistent scan records, scene detection, perceptual hashing, and server endpoints remain out of scope for this slice.

## Conditions Requiring a Future ADR

Revisit when any of the following are authorized:

- persistent thumbnails or catalog media records;
- provider-backed analysis workflows;
- perceptual or scene-based frame selection;
- async/background analysis jobs;
- API exposure of analysis results;
- semantic minimum FFmpeg version policy;
- platform-specific decoder integration in desktop UX.
