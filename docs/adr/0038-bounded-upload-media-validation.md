# ADR-0038: Bounded Upload Media Validation

## Status

`Accepted`

## Decision Date

2026-07-14

## Context

ADR-0037 established durable upload sessions and server-owned quarantine
storage. The transport can durably receive bytes and stop at `received`, but it
does not yet prove that a quarantined object is acceptable media, compute byte
identity evidence, or prepare the session for later publication.

Upload validation parses untrusted media and therefore needs bounded parser
execution, stable filesystem identity, sanitized failure classification, and
atomic persistence. It must not make a quarantined object visible, publish it,
insert catalog rows, decide duplicates, or trigger AI analysis.

## Decision

FrameNest validates completed uploads through an internal application use case
only. No public validation endpoint is added, and `/complete` does not invoke
validation automatically.

The initial accepted upload media policy is content-derived and limited to:

- GIF, persisted as `validated_media_kind = animated_image` and
  `validated_format = gif`;
- MP4, persisted as `validated_media_kind = video` and
  `validated_format = mp4`.

Filename, extension, client MIME, browser metadata, and upload request
`Content-Type` are not trusted for media identity.

Validation uses two mutually reinforcing checks:

- a bounded prefix/container precheck for GIF signatures or an MP4 `ftyp` box;
- bounded structured `ffprobe` JSON output from the same stable quarantine
  object.

The signature result and probe result must agree. Contradictory or ambiguous
evidence is rejected.

## Stable Quarantine Object

The validator resolves the quarantine object only from the server-generated
storage key under the configured quarantine root. The filesystem adapter opens
the object relative to a validated root descriptor, uses no-follow protections
where supported, rejects missing, symlink, and non-regular objects, and keeps a
stable open descriptor for hashing and probing.

Validation verifies that the physical size equals both durable
`received_size_bytes` and `declared_size_bytes`. SHA-256 is computed in chunks
over the stable descriptor. The object is verified before probing, after
probing, and after a second digest pass before success is committed. Path
replacement cannot make hashing and probing inspect different objects.

The bounded process runner may inherit an explicit stable file descriptor and
address it through `/dev/fd/{fd}` on supported POSIX targets. It still uses a
shell-free argument vector, bounded stdout and stderr, a wall-clock timeout, and
deterministic termination.

## Validation Limits

The upload-validation probe uses these centralized limits:

- probe timeout: 10 seconds;
- ffprobe stdout: 262,144 bytes;
- ffprobe stderr: 32,768 bytes;
- prefix precheck: 4,096 bytes;
- maximum streams: 16;
- maximum width or height: 8,192 pixels;
- maximum total pixels: 33,177,600;
- maximum duration: 21,600,000 ms.

MP4 accepts one primary non-attached visual stream with an explicit accepted
codec name from the initial bounded set: `h264`, `hevc`, `mpeg4`, `vp9`, or
`av1`. This accepts a bounded visual stream for ingest staging only; it does not
claim browser playback compatibility.

## Durable Evidence

Migration `0010` adds nullable normalized upload-session fields:

- `validated_media_kind`;
- `validated_format`.

Allowed durable pairs are exactly:

- `animated_image` + `gif`;
- `video` + `mp4`.

The states `duplicate_pending`, `publish_pending`, `published`, and `cataloged`
must have complete received bytes, `checksum_algorithm = sha256`, a lowercase
64-character checksum, and a coherent validation evidence pair. Earlier states
may keep validation evidence null. A rejected session may have null checksum and
null validation evidence.

The migration fails closed if pre-existing rows are already in those advanced
states without evidence. It does not invent validation evidence for legacy rows.

## Atomic Completion

Validation starts with a guarded `received -> validating` transition. A retry
that observes `validating` reruns validation from the complete quarantine object.

Successful validation atomically persists SHA-256, normalized media evidence,
and `validating -> publish_pending` in one SQLite transaction. The state
transition is not committed separately from the evidence.

Permanent content or policy failures atomically persist one sanitized failure
code and transition `validating -> rejected`.

Infrastructure and quarantine-consistency failures are not labeled as user media
policy failures. When the current state permits, they are recorded through the
existing `failed` state with a sanitized infrastructure code.

## Non-Visibility

`publish_pending` remains quarantined and non-visible. This decision creates:

- zero catalog rows;
- zero physical media locations;
- zero logical media;
- zero publication files;
- zero Gallery visibility;
- zero content-serving reachability.

## Deferred Work

This ADR does not implement or decide:

- validation trigger integration from the upload workflow;
- duplicate identity review or duplicate UI;
- publication root or atomic publication mechanics;
- catalog insertion or reconciliation;
- browser upload UI;
- AI analysis;
- deployment or NUC behavior;
- cleanup scheduling.

## Security Consequences

No private media paths, storage keys, parser stderr, command lines, SQL, raw
exceptions, provider credentials, or host-specific values are exposed in public
responses or durable validation metadata.

The implementation remains inside the current loopback-first, single-process,
single-worker development boundary. In-process same-session locking is not
claimed as multi-process safety.

## Related Documents

- [ADR index](README.md)
- [ADR-0037](0037-durable-upload-session-and-safe-ingest-foundation.md)
- [SECURITY.md](../../SECURITY.md)
- [SPEC.md](../../SPEC.md)
