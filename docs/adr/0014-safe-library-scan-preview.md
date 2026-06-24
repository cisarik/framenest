# ADR-0014: Safe Read-Only Library Scan Preview

## Status

`Accepted`

## Decision Date

`2026-06-24`

## Decision Authority

The Orchestrator authorized this initial scan-preview decision and test-first implementation through bounded task `FRAMENEST-CYCLE-045-SAFE-LIBRARY-SCAN-PREVIEW`.

## Context

FrameNest is local-first. Library registration exists through [ADR-0013](0013-initial-library-registry.md), but no filesystem scanning boundary existed. The first scanning step must prove safe traversal and candidate identification without persisting media records or mutating the library.

Relevant existing decisions:

- [ADR-0010](0010-initial-persistence-foundation.md) accepts synchronous SQLAlchemy 2.x Core with Alembic for SQLite.
- [ADR-0011](0011-stable-domain-identities.md) accepts application-owned UUIDv4 `LibraryId`.
- [ADR-0013](0013-initial-library-registry.md) implements the initial local library registry with device-local root locators.

## Decision

### Purpose

The first scanning boundary is a bounded, deterministic, read-only preview of one already registered local library.

The preview exists to:

- prove safe filesystem traversal;
- identify likely supported media candidates;
- produce deterministic operator-visible evidence;
- prepare future persistent media-catalog work.

It is not a persistent scan run and not media import.

### Architectural ownership

The application layer owns:

- scan limits;
- scan result and candidate value types;
- scanner port;
- preview orchestration;
- application-level sanitized errors.

The infrastructure filesystem adapter owns:

- local directory traversal;
- native-path compatibility;
- file-type inspection;
- candidate extension classification;
- filesystem-error translation.

The CLI adapter owns:

- command parsing;
- database-readiness checks;
- repository and scanner construction;
- JSON output;
- exit-code translation.

The domain layer remains unchanged.

The scanner must not depend on FastAPI, Starlette, Uvicorn, Pydantic, SQLAlchemy, Alembic, configuration, the catalog CLI, or global mutable state.

### Read-only boundary

The preview must not create, modify, rename, move, delete, open for content reading, hash, or write any scanned file; create sidecars; create thumbnails; persist candidates; update the library; update the database; execute a migration; invoke external tools; or enumerate beyond the configured bounded limit.

Directory metadata traversal and file metadata inspection required for type and size are allowed. No media file content may be opened or read.

### Library selection and locality

The preview operates on one existing registered `Library`, selected by strict `LibraryId`. The catalog database must already be at migration head. The library root flavor must match the current native platform (`posix` on non-Windows, `windows` on Windows). A mismatched path flavor is not locally scannable. The root must currently exist and behave as a directory. The scanner uses the stored canonical lexical root and does not rewrite or persist a new root.

### Symlink policy

The registered root itself may be a symlink path because ADR-0013 permits preserving that lexical root. Opening the registered root directory is allowed. Inside the scanned tree: symbolic-link directories must not be followed; symbolic-link files must not be classified as candidates; every nested symbolic-link entry is skipped and counted; no symlink target is resolved or exposed.

### Hidden-entry policy

An entry whose filename begins with `.` is initially treated as hidden. Hidden files are skipped. Hidden directories are skipped without traversing descendants. The root itself is not skipped merely because its own registered name begins with `.`. Platform-specific hidden attributes are deferred. A skipped hidden directory counts as one skipped entry; its unvisited descendants are not counted.

### Candidate policy

Candidate classification is extension-based only. Extension matching is case-insensitive. It is a scan hint, not proof that the file is valid media.

Initial video candidate extensions: `.3gp`, `.avi`, `.flv`, `.m2ts`, `.m4v`, `.mkv`, `.mov`, `.mp4`, `.mpeg`, `.mpg`, `.mts`, `.ogv`, `.ts`, `.vob`, `.webm`, `.wmv`.

Initial GIF candidate extension: `.gif`.

Candidate kinds are exactly `video` and `gif`. Unknown extensions are ordinary non-candidate files. Do not perform MIME detection, magic-byte detection, codec detection, container validation, duration extraction, or FFmpeg/ffprobe execution.

### Deterministic traversal

Traversal must be deterministic and independent of native filesystem enumeration order. For every directory, read entries once through a bounded standard-library directory enumeration boundary and order entries by `name.casefold()` then original `name`. Use deterministic depth-first traversal. Candidate output order must equal deterministic traversal order. Relative output paths must be relative to the registered library root, use `/` as the output separator on every platform, never include the absolute root, never begin with `/`, and never contain `.` or `..` components.

### Bounded work

Default limits: `max_entries = 100000`, `max_candidates = 1000`. Accepted ranges: `max_entries` 1 through 1000000; `max_candidates` 1 through 10000. An entry is one discovered child filesystem entry below the root. When another entry would exceed `max_entries`, stop traversal, set `truncated = true`, and return the deterministic partial preview collected so far. The scanner counts all candidate files encountered within the processed-entry limit, retains only the first `max_candidates` candidates in deterministic order, and sets `candidates_truncated = true` when the total encountered candidate count exceeds the returned candidate count. Limits are operation inputs, not global configuration.

### Filesystem error policy

If the registered root itself does not exist, is not a directory, cannot be opened, or has incompatible path flavor, the whole preview fails with a sanitized unavailable error. For an error encountered below an already opened root, do not expose the private path or raw OS error; increment `inaccessible_entries`; skip that entry or subtree; continue when safe. Unexpected scanner implementation failures must produce a sanitized generic scan failure.

### Result privacy

Successful preview output intentionally includes candidate paths relative to the registered library root. It must not include the absolute library root, configured database path, environment values, SQL, bound parameters, raw OS errors, stack traces, or symlink targets. Structured logs must not receive candidate paths or the library root from this task. The command emits one JSON object and no additional ordinary output.

### Deferred scope

Persistent scan records, scan history, scan resume, background execution, cancellation, progress streaming, media entities, physical media locations, media catalog tables, storage-volume association, availability updates, hashing, duplicate detection, metadata extraction, MIME inspection, FFmpeg and ffprobe, cover or thumbnail generation, sidecars, ignore files or user-configurable patterns, platform-specific hidden attributes, configurable extension sets, nested symlink following, API routes, desktop UI, and scheduled scanning are explicitly deferred.

## Consequences

### Positive

- Safe operator-visible evidence for one registered library without schema expansion.
- Reusable application and scanner boundaries for future desktop, API, and background execution.
- Deterministic tests for traversal, limits, privacy, and read-only safety.

### Negative

- Extension-only classification may include non-media files.
- Hidden-entry policy ignores platform-specific hidden attributes initially.
- Preview output is not durable catalog truth.

## Revisit triggers

Revisit when persistent scan runs, media catalog tables, MIME or codec validation, platform hidden attributes, configurable extension sets, or API exposure are authorized.

## Related documents

- [SPEC.md](../../SPEC.md)
- [ROADMAP.md](../../ROADMAP.md)
- [ADR-0013](0013-initial-library-registry.md)
