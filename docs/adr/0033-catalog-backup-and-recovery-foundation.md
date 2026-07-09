# ADR-0033: Catalog Backup and Recovery Foundation

## Status

`Accepted`

## Decision Date

`2026-07-08`

## Context

FrameNest is preparing for the first real Ubuntu NUC deployment. The production
catalog database at `/var/lib/framenest/catalog.sqlite3` will become
authoritative application state before broader sidecar rebuild behavior exists.
The repository previously required a backup before migration or service switch
but did not provide tested backup tooling.

The current production state classes are:

- authoritative catalog database: `/var/lib/framenest/catalog.sqlite3`;
- non-secret AI configuration: `/var/lib/framenest/ai/config.json`;
- rebuildable Gallery preview cache: `/var/cache/framenest/gallery-previews`;
- original media: `/srv/media`;
- future provider and service secrets outside Git.

This decision establishes only the minimum repository-native catalog backup and
recovery foundation. It does not claim that a real NUC backup exists, that
media has a second copy, that secrets are recoverable, that retention is
automated, or that a restore has been tested on the real server.

## Decision

FrameNest accepts a directory backup bundle created and verified by a dedicated
operator command:

```text
framenest-backup create --source <catalog.sqlite3> --output <new-bundle-dir>
framenest-backup verify --bundle <bundle-dir>
framenest-backup restore --bundle <bundle-dir> --destination <absent-catalog.sqlite3>
```

The root development launcher may route the same boundary as:

```text
./framenest backup create ...
./framenest backup verify ...
./framenest backup restore ...
```

The initial bundle contains:

```text
manifest.json
catalog.sqlite3
```

No other entries are valid in a version `1` bundle. Verification must reject
unexpected files, directories, symlinks, secret-shaped artifacts, and temporary
state rather than treating them as harmless extras.

The manifest schema is versioned. Version `1` records only safe verification
metadata: UTC creation time, application name/version when available, digest and
integrity algorithm identifiers, catalog logical artifact name, byte size,
SHA-256 digest, Alembic revision, included state, and explicitly excluded
state. It must not record source or destination paths, hostnames, usernames, IP
addresses, environment variables, SQLite URLs, SQL text, media paths, media
filenames, exception text, credentials, tokens, or operator comments.
Manifest validation is intentionally strict for version `1`: timestamps must
be canonical UTC seconds, algorithms must match the implemented algorithms,
catalog size must be positive and bounded, SHA-256 values must be lowercase
hex, Alembic revisions must match the current four-digit revision scheme, and
unknown nested fields are rejected.

The catalog snapshot must be created with the SQLite online backup mechanism as
exposed by Python `sqlite3.Connection.backup()`. A naive byte copy of a live
SQLite database is not accepted for backup creation. The completed snapshot must
pass `PRAGMA integrity_check`, `PRAGMA foreign_key_check`, Alembic revision
inspection, size recording, and SHA-256 calculation before the bundle is
published.

`verify` is read-only. It must reject malformed manifests, unsupported manifest
versions, missing artifacts, unexpected bundle entries, symlink substitution,
incomplete temporary state, size mismatch, checksum mismatch, SQLite integrity
failure, foreign-key failure, and recorded-versus-observed Alembic revision
mismatch.

`restore` restores only to a new destination path. It verifies the whole bundle
first, refuses an existing or symlink destination, copies the verified catalog
through temporary state in the target directory, rechecks checksum, SQLite
integrity, and Alembic revision, then publishes the new file with no-overwrite
semantics. It does not migrate, replace production state, stop or start
services, delete previous databases, or infer application readiness.

In-place production overwrite is not provided by the initial CLI because it is
service-affecting and potentially destructive. Production replacement remains a
future explicitly authorized operator step:

```text
stop/switch boundary
-> preserve previous database
-> restore to new path
-> verify
-> controlled replacement
-> explicit migration when needed
-> readiness
-> controlled service start
-> health and log verification
```

Migration after restore is explicit. A restored database may be behind the
deployed release; operators must run the normal migration command only after
restore verification and only within an authorized recovery or deployment
workflow.

The non-secret AI configuration is not included automatically in version `1`.
The repository confirms that the existing AI configuration has a known
schema-validated non-secret provider/model selection and excludes provider
credentials, but bundling it safely also needs a documented restore and merge
policy. Until that policy exists, recovery is manual: recreate or copy the
validated non-secret selection separately after reviewing that it contains no
paths, environment values, credentials, prompts, provider responses, cookies,
tokens, or authorization headers.

The Gallery preview cache is excluded. Loss causes regeneration cost, not
authoritative-data loss.

Original media under `/srv/media` is excluded. The 2 TB media SSD is not a
backup. Irreplaceable media requires a separate off-device second-copy strategy
with verification by file identity, size, and optionally checksums. FrameNest
must not claim media protection while only one copy exists, and no automatic
deletion may follow a copy until the destination is verified.

Secrets are excluded. Secret recovery means secure re-entry or rotation through
a future approved production secret mechanism. No secret value, prefix, hash, or
encrypted secret blob belongs in this repository or in ordinary backup
manifests.

Backup output and failures must be sanitized deterministic JSON. Command output
must not disclose paths, SQL, SQLite URLs, environment values, tracebacks, raw
exception strings, host details, media names, or secrets.

Temporary state must remain outside the final bundle name until the snapshot
and manifest pass verification. Final bundle publication must use a
no-overwrite destination claim so a path created after the initial absence
check is not replaced. Because no-overwrite safety is stronger than
directory-level all-at-once replacement for this foundation, the final bundle
directory may briefly exist before both hard-linked artifacts are present; such
incomplete bundles fail verification. Restore file publication must also use
no-overwrite semantics. Failure cleanup must remove only owned temporary or
newly-created output artifacts and must not follow caller-controlled symlinks.
Bundle directories and catalog/manifest files must use restrictive POSIX
permissions where supported; on supported POSIX platforms, inability to apply
those permissions is a backup or restore failure.

Retention is operator policy. The minimum guidance is to keep more than one
recent verified bundle, keep at least one off-device copy for important catalog
state, record verification evidence, and avoid deleting old backups until a
newer backup has been verified and copied off-device. Automated retention
deletion is not implemented.

Operators should perform restore drills into disposable new destinations before
real production recovery. A passing restore drill does not prove service
readiness, media recovery, secret recovery, or NUC deployment acceptance.

## Primary Sources

Research retrieval date: **2026-07-08**.

| Topic | Source |
|---|---|
| Python `sqlite3.Connection.backup()` | https://docs.python.org/3.13/library/sqlite3.html#sqlite3.Connection.backup |
| SQLite Online Backup API | https://www.sqlite.org/backup.html |
| SQLite `PRAGMA integrity_check` and `foreign_key_check` | https://www.sqlite.org/pragma.html#pragma_integrity_check |
| SQLite WAL behavior | https://www.sqlite.org/wal.html |
| SQLite URI filenames | https://www.sqlite.org/uri.html |
| Python `pathlib.Path.as_uri()` | https://docs.python.org/3.13/library/pathlib.html#pathlib.Path.as_uri |
| Python `os.rename()`, `os.replace()`, and `os.link()` behavior | https://docs.python.org/3.13/library/os.html |
| Linux `rename(2)` directory replacement behavior | https://man7.org/linux/man-pages/man2/rename.2.html |
| Python `hashlib.sha256()` | https://docs.python.org/3.13/library/hashlib.html |

Design facts used:

- Python exposes SQLite's backup API through `Connection.backup()` and documents
  that it works while the database is accessed by other clients.
- SQLite's online backup API produces a destination snapshot of the source
  database as it was when copying commenced.
- `PRAGMA integrity_check` returns `ok` only when the checked database passes
  the low-level consistency checks it covers; foreign keys require
  `PRAGMA foreign_key_check`.
- WAL allows concurrent readers and writers but has filesystem and operational
  constraints, so backup must use SQLite's backup API rather than copying only
  the main database file.
- SQLite URI filenames treat `?` as the query delimiter and `#` as the fragment
  delimiter, so FrameNest must generate a properly escaped file URI before
  appending `mode=ro`.
- `os.rename()` and `os.replace()` can overwrite existing files on POSIX, and a
  directory rename can replace an existing empty directory. FrameNest therefore
  cannot satisfy no-overwrite publication with a check-then-rename sequence.
- A hard link to a verified temporary file provides same-filesystem
  no-overwrite file publication because link creation fails if the destination
  already exists.
- SHA-256 is guaranteed by Python's `hashlib` constructors.

## Consequences

### Positive

- Catalog backups are created from consistent SQLite snapshots.
- Every bundle is self-describing and verifyable without private paths.
- Restore drills can be performed without touching production state.
- Deployment runbooks can require a concrete tested catalog-backup command.

### Costs and limitations

- The initial bundle protects only the catalog database.
- Non-secret AI configuration recovery remains manual.
- Original media still needs a separate second-copy plan.
- Secrets still need a future production secret recovery mechanism.
- No scheduler, cloud upload, retention deletion, or real NUC restore drill is
  implemented.
- Restore does not replace production and does not run migrations.

## Rejected Alternatives

### Byte-copy the live SQLite files

Rejected because WAL and concurrent access make a naive copy of only the main
database file unsafe as the accepted backup mechanism.

### Include `/var/cache/framenest/gallery-previews`

Rejected because the cache is rebuildable derived state and would enlarge the
bundle without protecting authoritative data.

### Include `/srv/media`

Rejected because media protection is a separate second-copy storage strategy,
not a catalog backup bundle.

### Include secrets or environment files

Rejected because provider credentials and service secrets remain outside Git
and should be recovered by re-entry or rotation through a future approved
secret mechanism.

### Restore directly over production

Rejected for the initial CLI because it is destructive, service-affecting, and
requires an explicit stop/switch/readiness workflow.

## Revisit Triggers

Revisit this decision when implementing production database replacement,
scheduled backups, retention automation, off-device copy automation, encrypted
backup storage, non-secret AI configuration bundling, media second-copy
workflows, production secret integration, sidecar rebuild behavior, or a real
NUC restore-drill acceptance task.

## Related Documents

- [ADR index](README.md)
- [ADR-0010](0010-initial-persistence-foundation.md)
- [ADR-0032](0032-ubuntu-nuc-deployment-foundation.md)
- [Backup and recovery runbook](../BACKUP_AND_RECOVERY.md)
- [Ubuntu NUC deployment runbook](../UBUNTU_NUC_DEPLOYMENT.md)
- [SECURITY.md](../../SECURITY.md)
