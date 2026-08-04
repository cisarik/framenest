# FrameNest Backup and Recovery Runbook

## Status

This is the repository-native operator runbook for the minimum FrameNest catalog
backup and recovery foundation.

It is not a real NUC backup record, media backup plan, secret backup plan,
service-replacement procedure, or deployment acceptance record.

Authoritative decision: [ADR-0033](adr/0033-catalog-backup-and-recovery-foundation.md).
Automated scheduling, retention, and restore-readiness:
[ADR-0052](adr/0052-automated-catalog-backup-retention-and-restore-verification.md).

The accepted sanitized NUC host baseline is recorded in
[NUC_HOST_BASELINE.md](NUC_HOST_BASELINE.md). That baseline confirms the current
media-storage preparation state but does not replace catalog backup, media
second-copy planning, secret recovery, restore drills, or deployment
acceptance.

## Automated Daily Pipeline

Threat: unverified or unscheduled catalog backups leave no proven recovery point
after destructive administrator operations or failed migrations.

Benefit: one systemd timer runs a full create → verify → disposable restore →
semantic readback → retention pipeline every day.

Limitation: this protects the catalog database only. It does not back up
`/srv/media`, published originals, cover bytes, caches, secrets, or AI
configuration. Successful catalog restore does not restore lost original media.
Backups currently share the system SSD with the live catalog; off-host copies
remain deferred.

Default roots:

```text
/var/lib/framenest/catalog-backups
/var/lib/framenest/catalog-restore-verify
/var/lib/framenest/catalog-backup-ops
```

Schedule:

```text
framenest-catalog-backup.timer
OnCalendar=*-*-* 03:17:00 UTC
Persistent=yes
RandomizedDelaySec=900
```

There is exactly one timer. Restore-readiness is proven by the daily pipeline.
Status becomes stale when no complete scheduled success has occurred for more
than 48 hours. Scheduled attempt ordering uses a durable monotonic
`attempt_seq` in operator state so a later failure remains `failed` even when
wall-clock timestamps collide in the same UTC second. Manual `verify-restore`
never supersedes scheduled attempt order.

Shared exclusive non-blocking `fcntl.flock` on
`/var/lib/framenest/catalog-backup-ops/catalog-backup.lock` protects:

- `create`
- `verify`
- `restore`
- `run-scheduled`
- `verify-restore`
- `expire`

Competing protected commands return sanitized `BACKUP_OPS_BUSY` with zero
mutation. Read-only `status`, `list`, and `retain-plan` do not take the lock.
Production manual pre-deployment `create` therefore shares the lock with the
scheduled service when both use the configured operator-state root.

Successful restore publication removes the private temporary sibling. A fully
successful scheduled or manual restore-verification leaves the disposable
restore-verification root without that operation's database or temporary
sibling; unrelated files in the restore root are never removed.
`pending_cleanup=false` only when every disposable artifact created by that
operation was removed.

Retention:

- `FRAMENEST_CATALOG_BACKUP_KEEP_AUTO=30` by default;
- minimum accepted value is `3`; invalid values fail closed;
- only verified ledger-recorded `auto-` bundles expire;
- all non-`auto-` bundles remain pinned;
- failed pipelines perform no deletion;
- `expire` defaults to dry-run; `--apply` is required to delete.

Operator commands:

```text
framenest-backup run-scheduled
framenest-backup status
framenest-backup list
framenest-backup retain-plan
framenest-backup expire --dry-run
framenest-backup expire --apply
framenest-backup verify-restore --bundle <bundle>
```

## State Classes

| State | Path | Backup treatment |
|---|---|---|
| Catalog database | `/var/lib/framenest/catalog.sqlite3` | Included in catalog backup bundle |
| Durable accepted cover facts (migration `0022`) | catalog database | Included in catalog backup bundle |
| Durable cover artifacts | `/var/lib/framenest/covers` | Excluded; regenerable while source is available |
| Cover thumbnails | `/var/cache/framenest/cover-thumbnails` | Excluded; regenerate |
| Non-secret AI configuration | `/var/lib/framenest/ai/config.json` | Manual recovery for now |
| Gallery preview cache | `/var/cache/framenest/gallery-previews` | Excluded; regenerate |
| Original media | `/srv/media` | Excluded; needs separate second copy |
| Published upload originals | configured registered publication library | Excluded; needs separate media second copy |
| YouTube acquisition claims and provenance | catalog database | Included in catalog backup bundle |
| YouTube acquisition staging | `/var/lib/framenest/youtube-acquisition` | Excluded; lifecycle-owned transient state |
| Secrets | outside Git | Excluded; re-enter or rotate later |

The catalog bundle contains only:

```text
manifest.json
catalog.sqlite3
```

Revision `0013` publication provenance is catalog data and is included in the
SQLite artifact, but the published media bytes it describes are not. Restoring
the catalog bundle alone therefore does not restore a published upload original
or prove that its destination object is available.

Revision `0019` YouTube claims, retry/reuse lineage, downloader evidence, and
final media/location links are likewise catalog data included in the SQLite
artifact. Claim staging bytes, partial downloads, quarantine bytes, and
published originals are excluded. A restore therefore preserves durable
provenance but does not resume or recreate missing media bytes by itself.

Revision `0022` durable accepted-cover rows are also catalog data and travel
inside the SQLite artifact. Durable cover artifacts and cover thumbnails are
not included in the bundle. A restore therefore preserves accepted-cover facts
but not the cover artifact bytes; an artifact may be regenerated only while the
recorded source location and source version remain available, otherwise manual
re-selection is required. FrameNest does not claim complete disaster durability
for cover artifacts in this slice (see
[ADR-0050](adr/0050-durable-manual-cover-foundation.md)).

## Check

Threat: backing up the wrong state, treating rebuildable cache as durable state,
or relying on an untested command during deployment.

Benefit: confirms the operator is acting on the catalog database boundary only.

Limitation: check does not create a backup and does not inspect real media.

Preconditions:

- An authorized operator task exists.
- The source catalog path is known.
- The source is expected to be an existing SQLite catalog database.
- No service stop, restart, migration, or production replacement is part of
  this repository-only check.

Mutation class: read-only.

Stop conditions:

- The source path is not the expected catalog database.
- The operator wants to include `/srv/media`, cache files, `.env` files, or
  credentials in the catalog bundle.
- A command would expose private paths, secrets, or media filenames in shared
  evidence.

Rollback or cleanup: none for read-only checks.

Verification evidence:

- Exact FrameNest commit or release.
- The planned source is the catalog database, not a media or cache path.
- Backup tooling help is available:

```text
framenest-backup --help
framenest-backup create --help
framenest-backup verify --help
framenest-backup restore --help
```

## Plan

Threat: creating a local-only backup that is later mistaken for disaster
recovery, or deleting older backups before a new backup is verified.

Benefit: defines destination, retention, and evidence before mutation.

Limitation: the repository does not choose the physical off-device product,
destination, schedule, or retention period.

Preconditions:

- Select a new local bundle directory that does not exist.
- Select an off-device copy destination controlled by the operator.
- Decide how many verified bundles to retain.
- Decide where restore-drill evidence will be recorded.

Mutation class: planning only.

Stop conditions:

- The plan has only one copy on the NUC.
- The plan treats the media SSD as a backup.
- The plan stores secrets in the bundle or manifest.
- The plan includes automatic deletion without verified replacement.

Rollback or cleanup: revise the plan before creating state.

Verification evidence:

- Planned bundle identifier.
- Planned off-device destination class.
- Retention rule.
- Restore-drill target path class.

## Create

Threat: a naive copy of a live SQLite database can miss WAL state or capture an
inconsistent image.

Benefit: `framenest-backup create` uses SQLite online backup, verifies the
snapshot, records manifest metadata, and publishes a complete bundle only after
validation.

Limitation: create does not migrate, stop services, copy cache, copy media,
include AI configuration, include secrets, or copy off-device. It prioritizes
no-overwrite publication; an interrupted final publication may leave a bundle
directory that fails verification and must be treated as unusable.

Preconditions:

- Source catalog database exists.
- Output bundle path is new and absent.
- Output parent exists and is trusted by the operator.

Mutation class: creates a new backup bundle directory.

Command shape:

```text
framenest-backup create \
  --source /var/lib/framenest/catalog.sqlite3 \
  --output /path/to/new/catalog-backup
```

Development launcher route:

```text
./framenest backup create \
  --source /path/to/catalog.sqlite3 \
  --output /path/to/new/catalog-backup
```

Stop conditions:

- Source is missing, a directory, or a symlink.
- Output already exists.
- Output parent is missing, invalid, or unsafe.
- Permission restriction fails on a POSIX platform where restrictive file modes
  are supported.
- The command returns non-zero.

Rollback or cleanup:

- The command removes only owned temporary state on failure.
- Do not manually delete older verified backups merely because creation of a
  new backup started.

Verification evidence:

- Exit code `0`.
- Single JSON success line with `state` equal to `created`.
- Bundle contains exactly `manifest.json` and `catalog.sqlite3`.
- Output does not disclose source or output paths.

## Verify

Threat: a bundle may be incomplete, tampered with, corrupted, or internally
inconsistent even when files exist.

Benefit: verify checks manifest structure, supported schema version, required
files, absence of unexpected bundle entries, symlink safety, byte size,
SHA-256 digest, SQLite integrity, foreign-key check, and Alembic revision.

Limitation: verify does not prove media recovery, secret recovery, service
readiness, or off-device copy success.

Preconditions:

- Bundle directory exists.
- Bundle is not being modified.

Mutation class: read-only.

Command:

```text
framenest-backup verify --bundle /path/to/catalog-backup
```

Stop conditions:

- Verification returns non-zero.
- Manifest is malformed or unsupported.
- The catalog checksum, integrity, or revision check fails.
- The bundle contains files, directories, symlinks, or secret-shaped artifacts
  other than the two declared bundle artifacts.
- The bundle contains temporary/incomplete state.

Rollback or cleanup:

- Keep failed bundles quarantined for diagnosis or delete them only under a
  separate operator cleanup decision.

Verification evidence:

- Exit code `0`.
- Single JSON success line with `state` equal to `verified`.
- Recorded catalog size, SHA-256 digest, and Alembic revision.

## Copy Off-Device

Threat: a backup stored only on the NUC can be lost with the NUC, disk, power
event, theft, or operator error.

Benefit: an off-device copy protects the catalog bundle against local loss.

Limitation: FrameNest does not implement upload, sync, cloud storage, media
copy, or retention automation in this slice.

Preconditions:

- Local bundle verification passed.
- Destination is chosen by the operator.
- Destination copy method is outside this repository task.

Mutation class: operator-controlled file copy outside FrameNest tooling.

Stop conditions:

- Destination cannot be verified.
- Copy process would expose private paths, media filenames, or secrets in shared
  logs.
- The operator intends to delete the only verified local bundle before proving
  the off-device copy.

Rollback or cleanup:

- Keep the verified local bundle until the off-device copy is verified.
- Remove incomplete destination copies according to the destination's own safe
  cleanup procedure.

Verification evidence:

- Off-device copy identity.
- Bundle `manifest.json` and `catalog.sqlite3` present at destination.
- Verification run against the copied bundle when practical.
- Matching SHA-256 digest for the catalog artifact.

## Restore Drill

Threat: a backup that has never been restored may fail during a real recovery.

Benefit: restore drill proves that a verified bundle can produce a usable
catalog file at a new destination.

Limitation: restore drill does not replace production, run migrations, start the
service, verify health, recover media, or recover secrets.

Preconditions:

- Use a disposable absent destination path.
- The destination parent is safe for test output.
- The source bundle verified successfully.

Mutation class: creates a new restored database file at an absent destination.

Command:

```text
framenest-backup restore \
  --bundle /path/to/catalog-backup \
  --destination /path/to/disposable/restored-catalog.sqlite3
```

Stop conditions:

- Destination exists or is a symlink.
- Restore returns non-zero.
- Permission restriction fails on a POSIX platform where restrictive file modes
  are supported.
- Post-restore checksum, integrity, or revision verification fails.

Rollback or cleanup:

- Delete the disposable restored database only after recording evidence.
- Do not delete or mutate the source bundle.

Verification evidence:

- Exit code `0`.
- Single JSON success line with `state` equal to `restored`.
- Restored catalog digest and Alembic revision match the bundle.

## Production Recovery

Threat: overwriting production state incorrectly can destroy the last usable
catalog or start FrameNest against an incompatible schema.

Benefit: separating restore-to-new-path from production replacement keeps the
initial CLI non-destructive.

Limitation: production replacement is not automated in this repository task.

Preconditions:

- A future explicit recovery task authorizes service-affecting steps.
- Current production database is preserved first.
- Bundle verifies.
- Restore to a new path succeeds.
- Migration need is understood.

Mutation class: future service-affecting recovery mutation, not implemented by
`framenest-backup`.

Required future sequence:

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

Stop conditions:

- No separate preservation of the current production database exists.
- The restore target would overwrite `/var/lib/framenest/catalog.sqlite3`
  directly.
- Migration status is unknown.
- Readiness fails.
- Logs disclose secrets, private paths, SQL, or tracebacks.

Rollback or cleanup:

- Restore the preserved previous database and previous release when recovery
  fails before acceptance.
- Keep failed restored files for diagnosis or remove them only under explicit
  cleanup authority.

Verification evidence:

- Preserved previous database identifier.
- Verified restored database identifier.
- Migration result when migration is authorized.
- Readiness output.
- Health and sanitized log evidence.

## Retention

Threat: too few backups, unverified backups, or automatic deletion can remove
the only recoverable catalog.

Benefit: automated retention keeps the newest verified `auto-` recovery points
while pinning all non-`auto-` historical bundles.

Limitation: automatic expiry never claims off-device durability and never deletes
pinned pre-deployment or manual bundles.

Preconditions:

- Only completed verified ledger-recorded `auto-` bundles are eligible.
- `FRAMENEST_CATALOG_BACKUP_KEEP_AUTO` is valid (`>= 3`, default `30`).
- A newer verified automatic recovery point exists according to the policy.

Mutation class: deletes only whole eligible automatic bundle directories after
dry-run or scheduled success.

Stop conditions:

- A current scheduled create/verify/restore pipeline failed.
- Deletion would remove a non-`auto-` bundle.
- Deletion would remove the newest verified automatic bundle.
- Deletion would reduce verified automatic recovery points below three.
- The path is a symlink or escapes the configured backup root.

Rollback or cleanup:

- Retain older verified bundles until replacement evidence exists.
- Use `framenest-backup expire --dry-run` before `--apply`.

Verification evidence:

- List of retained bundle identifiers.
- Verification evidence for retained current bundles.
- Operator status and events for applied expiry.

## Failure Handling

Threat: partial temporary state or unsafe manual cleanup can remove the wrong
files.

Benefit: FrameNest-owned operations clean only their own temporary artifacts.

Limitation: external copy tools and operator storage destinations have their
own cleanup rules.

Preconditions:

- Identify which operation failed.
- Preserve stderr/stdout JSON output.

Mutation class: cleanup only when the failed artifact is positively identified
as temporary or disposable.

Stop conditions:

- The path is a symlink.
- The path is not a FrameNest-created temporary artifact or disposable restore
  target.
- Cleanup would touch media, secrets, environment files, or production
  database state.

Rollback or cleanup:

- Remove only owned temporary bundle directories beginning with the documented
  temporary prefix when they are inside the selected output parent and are not
  symlinks.
- Remove disposable restore-drill output only after evidence capture.

Verification evidence:

- Failed command output.
- Confirmation that source database and bundle were not mutated unexpectedly.
- Confirmation that no media/cache/secrets were touched.

## Evidence Capture

Capture:

- Exact FrameNest commit or release.
- Command executed.
- Exit code.
- Sanitized JSON output.
- Bundle manifest.
- Catalog SHA-256 digest.
- Alembic revision.
- Off-device copy verification.
- Restore-drill result.

Do not capture:

- Real passwords, tokens, cookies, private keys, provider credentials, or
  authorization headers.
- Real `.env` files or `/etc/framenest/framenest.env` content when it may
  contain operational details.
- Private media filenames.
- Private home paths unless the operator has explicitly chosen to record them in
  private notes outside the repository.
- Real IP addresses, disk UUIDs, or serial numbers in repository artifacts.

## What This Runbook Does Not Prove

Creating a catalog backup is not the same as verifying it.

Verifying a backup bundle is not the same as restoring it.

Restoring into a new destination is not the same as replacing production.

Replacing production during a future recovery is not the same as migrating a
restored database.

Migrating a restored database is not the same as proving application readiness.

Application readiness is not the same as recovering original media.

Recovering original media is not the same as recovering secrets.

The NUC is not deployment-ready merely because repository tests pass.
