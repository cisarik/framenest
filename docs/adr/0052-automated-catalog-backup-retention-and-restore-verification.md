# ADR-0052: Automated Catalog Backup, Retention and Restore Verification

## Status

`Accepted`

## Decision Date

`2026-08-04`

## Context

ADR-0033 established repository-native catalog backup create, verify, and
restore-to-new-destination primitives. Production already stores operator and
pre-deployment bundles under `/var/lib/framenest/catalog-backups`, but scheduling,
retention, disposable restore readiness, and operator status remained manual.

After administrator catalog removal, FrameNest needs an automated, fail-closed
catalog recovery point that verifies restore readiness without overwriting the
live catalog and without claiming original-media recovery.

## Decision

FrameNest automates catalog backup through one systemd oneshot service and one
daily timer:

```text
framenest-catalog-backup.service
framenest-catalog-backup.timer
```

The timer runs at `03:17 UTC` with `Persistent=yes`, `RandomizedDelaySec=900`,
and `AccuracySec=1min`. There is no second timer and no weekly restore job.

`framenest-backup run-scheduled` performs, under an exclusive non-blocking
`fcntl.flock` shared with manual `create`, `verify`, `restore`,
`verify-restore`, and `expire`:

1. configuration validation;
2. create a uniquely named `auto-<UTC>-<8hex>` bundle using ADR-0033 create;
3. verify the completed bundle;
4. restore to a new disposable database under
   `/var/lib/framenest/catalog-restore-verify`;
5. integrity and foreign-key checks on the restored database;
6. bounded semantic catalog readback;
7. durable success recording with a monotonic scheduled `attempt_seq`;
8. deterministic retention planning;
9. expiration of only eligible verified `auto-` bundles;
10. disposable cleanup and final status/events.

A scheduled run succeeds only when create, verify, disposable restore, restored
integrity/foreign-key checks, semantic readback, and durable success recording
all pass. File existence alone is not success. If any pre-retention step fails,
the unit exits non-zero and performs no retention deletion. Successful restore
publication removes private temporary siblings; `pending_cleanup` remains false
only when every disposable artifact from that operation was removed.

Restore-readiness states are deterministic: `busy`, `never_verified`, `failed`,
`stale`, and `ready`. Readiness becomes `stale` when the last complete scheduled
backup-and-restore success is older than 48 hours. Attempt ordering prefers
durable monotonic `attempt_seq` over wall-clock timestamps so a later failure
in the same UTC second still yields `failed`. Manual
`framenest-backup verify-restore` may record selected-bundle evidence but must
not masquerade as scheduled backup creation or supersede scheduled attempt
order.

Retention uses `FRAMENEST_CATALOG_BACKUP_KEEP_AUTO` default `30`, minimum `3`.
Invalid values fail closed with no silent clamping. Only ledger-recorded,
verified `auto-` bundles are eligible. All non-`auto-` bundles, including all
existing pre-deployment and manual production bundles, remain pinned against
automatic expiry. The newest verified automatic recovery point is never deleted
and verified automatic recovery points never fall below three.

Durable operator state lives outside the catalog at:

```text
/var/lib/framenest/catalog-backup-ops/status.json
/var/lib/framenest/catalog-backup-ops/events.jsonl
/var/lib/framenest/catalog-backup-ops/catalog-backup.lock
```

Manifest schema v1 is preserved. No Alembic migration is added. The backup
bundle remains catalog-only and does not include original media, secrets,
caches, cover bytes, or AI configuration.

Accepted backup root is `/var/lib/framenest/catalog-backups`. `/mnt/umbrel-data`
and `/srv/media` are rejected for this whole. Same-system-SSD placement protects
against operator and schema mistakes; off-host second copies remain deferred.

## Consequences

### Positive

- Daily verified restore-readiness without production overwrite.
- Fail-closed retention that cannot delete pinned historical recovery points.
- Operator-visible status through the existing `framenest-backup` CLI.
- Immutable-release compatible systemd activation using `/opt/framenest/current`.

### Costs and limitations

- Catalog backups share the system SSD failure domain with the live catalog.
- Original media bytes remain unprotected by this whole.
- Off-host copy, monitoring, and in-place production restore remain deferred.
- Cleanup failure after a proven restore is visible as pending cleanup and
  non-zero exit while preserving restore-readiness success evidence.

## Rejected Alternatives

### Weekly restore-verification timer

Rejected because the daily pipeline already performs disposable restore
verification; a second timer adds concurrency and operational ambiguity.

### `/mnt/umbrel-data` destination

Rejected because that path is absent on the production NUC.

### `/srv/media` backup root

Rejected because the media mount is not a catalog backup destination and would
blur the original-media boundary.

### Catalog-table backup history / Alembic migration

Rejected because storing the only recovery history inside the backed-up catalog
creates a circular recovery dependency.

## Related Documents

- [ADR-0033](0033-catalog-backup-and-recovery-foundation.md)
- [Backup and recovery runbook](../BACKUP_AND_RECOVERY.md)
- [Ubuntu NUC deployment runbook](../UBUNTU_NUC_DEPLOYMENT.md)
