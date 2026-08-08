# ADR-0056: Off-Device Catalog Backup Copy and Restore Verification

## Status

`Accepted`

## Decision Date

`2026-08-08`

## Context

ADR-0033 established catalog backup create/verify/restore primitives. ADR-0052
automated same-host scheduled backup, disposable restore verification, retention,
and operator readiness. Those recovery points still share the live catalog host
filesystem failure domain.

FrameNest needs a repository-native, provider-neutral path that copies a verified
scheduled catalog recovery point onto a distinct mounted filesystem destination
and proves that the published destination bundle can be restored and verified,
without claiming media recovery, secret recovery, full-host disaster recovery, or
that any particular physical destination survives host loss until separately
authorized host acceptance proves the failure domain.

## Decision

FrameNest adds a separate off-device copy and verification path that leaves the
local ADR-0052 pipeline unchanged.

Scheduled destination root is fixed:

```text
/mnt/framenest-catalog-offdevice
```

Destination trust requires:

- the exact directory exists as a real mount point;
- the destination filesystem device differs from the local backup root device;
- a root-owned non-symlink marker `.framenest-catalog-offdevice.json` with
  schema v1, purpose `framenest-catalog-offdevice`, and a 32-lowercase-hex
  `destination_id`;
- optional non-secret pin `FRAMENEST_CATALOG_OFFDEVICE_DESTINATION_ID` matching
  the marker when configured;
- a pre-created non-symlink `bundles/` directory with safe ownership/mode.

Operator command:

```text
framenest-backup run-offdevice
```

Under the existing shared backup operations lock, the command:

1. refuses to run when the destination ID is unset (`disabled`);
2. selects only the ledgered automatic recovery point recorded by
   `last_successful_scheduled_backup_and_restore`;
3. re-verifies that source bundle before copy;
4. copies through an operation-owned hidden staging directory under `bundles/`;
5. fsyncs copied files and the stage directory;
6. publishes with Linux `renameat2(RENAME_NOREPLACE)` semantics and fails closed
   when no-replace atomic publication is unavailable;
7. treats an exact already-published matching final bundle as idempotent success;
8. never overwrites, repairs, quarantines, or deletes a conflicting final bundle;
9. verify-restores the published destination bundle into the existing disposable
   local restore-verification root;
10. records success only after destination validation, durable publication,
    bundle verification, and disposable restore verification succeed.

Optional repository systemd assets:

```text
deploy/systemd/framenest-catalog-offdevice.service
deploy/systemd/framenest-catalog-offdevice.timer
```

Timer schedule: `04:17 UTC`, `Persistent=yes`, `RandomizedDelaySec=900`,
`AccuracySec=1min`. These units are repository source material only; this
decision does not install or enable them on a real host.

`framenest-backup status` gains an additive sanitized `off_device` section.
Ordinary status output must not expose destination root, marker ID, device
numbers, mount identity, or other host-specific identifiers.

V1 has no published off-device retention and no operator command to delete final
off-device bundles. Local retention remains local-only and must never scan the
destination as a retention candidate. Off-device code may delete only its own
exact validated staging state.

No Alembic migration, no manifest schema migration, no new Python dependency,
no cloud/provider API, no credentials, and no direct FrameNest outbound network
requirement are introduced by this whole.

## Consequences

### Positive

- Deterministic evidence that a verified local recovery point was copied onto a
  distinct mounted filesystem and restore-verified from that published bundle.
- Fail-closed destination, atomicity, conflict, and sanitization boundaries.
- Separation from the local ADR-0052 timer and retention model.

### Costs and limitations

- Repository implementation proves the filesystem contract only.
- Real destination provisioning, mount ownership, and physical/off-host failure
  domain evidence remain separate host-acceptance work.
- Catalog-only scope is preserved: original media, cover artifacts, secrets, AI
  configuration, host configuration, and full NUC recovery remain excluded.
- Capacity exhaustion fails closed; it never triggers destination deletion.

## Alternatives Considered

### Cloud/provider object storage upload

Rejected for v1. Provider APIs, credentials, and network dependence are outside
this local-first mounted-filesystem whole.

### Reusing `/srv/media` or widening the main application unit

Rejected. Original media remains read-only to the service by default, and
off-device catalog copy must not broaden media write authority.

### Editing ADR-0052 in place to absorb off-device copy

Rejected. Off-device copy is a distinct decision with distinct destination trust,
atomicity, and acceptance boundaries.

## References

- [ADR-0033](0033-catalog-backup-and-recovery-foundation.md)
- [ADR-0052](0052-automated-catalog-backup-retention-and-restore-verification.md)
- [BACKUP_AND_RECOVERY.md](../BACKUP_AND_RECOVERY.md)
- [UBUNTU_NUC_DEPLOYMENT.md](../UBUNTU_NUC_DEPLOYMENT.md)
