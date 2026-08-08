# ADR-0057: Operator-Workstation Pull-Based Catalog Snapshot and Recovery

## Status

`Accepted`

## Decision Date

`2026-08-08`

## Context

ADR-0052 established same-host scheduled catalog backup with disposable restore
verification and retention. ADR-0056 added an optional mounted-filesystem
off-device copy that remains a legitimate capability: the NUC service may copy a
verified recovery point onto a distinct mounted destination with fail-closed
trust checks and no-replace publication.

Mounted copy still requires the NUC to know and write a destination. The
preferred current recovery layer for surviving NUC host loss is a
workstation-initiated pull: the operator workstation uses existing OpenSSH to
fetch exactly one ledgered successful scheduled recovery point, verifies it
locally, and publishes it into a private local snapshot store. The NUC must
never learn the workstation destination, gain workstation credentials, or gain
write/delete authority over workstation snapshots. No NUC outbound backup
connection is introduced.

This decision does not redefine `off_device` status or replace ADR-0056.

## Decision

FrameNest adds an additional repository capability for operator-workstation
pull-based catalog snapshots.

### Trust model

An existing SSH operator account may invoke exactly one root-owned, fixed,
argument-free export launcher through one passwordless sudo rule. The run-as
identity is exactly `framenest`, not `root`. The intended sudoers semantic
contract is:

```text
<FRAME_NEST_OPERATOR> ALL=(framenest) NOPASSWD:NOSETENV: /usr/local/libexec/framenest-catalog-export-v1 ""
```

The explicit final `""` argument matcher is security-significant. Wildcard
FrameNest CLI rules, root run-as targets, caller environment override, and
arbitrary launcher arguments are rejected.

Repository source for the launcher:

```text
deploy/ubuntu/framenest-catalog-export-v1
```

Host installation, sudoers activation, and real workstation-store provisioning
are later authorized host work. This ADR does not install them.

### Export

`framenest-backup export-latest` accepts no arguments. Under the existing shared
backup operation lock it:

1. selects only `last_successful_scheduled_backup_and_restore`;
2. requires a valid automatic bundle ID present in the automatic ledger;
3. verifies the real non-symlink bundle and recorded evidence;
4. streams protocol-v1 bytes to stdout only;
5. writes sanitized diagnostics to stderr only;
6. re-verifies source identity before successful exit;
7. does not mutate scheduled success status, retention, or backup roots.

### Protocol v1

Fixed magic `FNCBE01\0`, unsigned network-order 32-bit JSON header length,
canonical UTF-8 JSON header (maximum 8192 bytes), exact `manifest.json` bytes,
exact `catalog.sqlite3` bytes, then EOF. Unknown v1 fields and unsupported
protocol versions are rejected. No tar, compression, or encryption above SSH.

### Workstation store

Generic CLI accepts snapshot store root, expected mount root, expected store ID,
SSH target, and safe timeouts. Concrete workstation paths remain local operator
configuration. The store fails closed when the mount is missing, symlinked,
same-device as its parent, ownership/mode is unsafe, marker/store ID mismatches,
or the store leaves the mount filesystem. Store ID is a non-secret 32-lowercase
hex value generated at first init and immutable thereafter.

Layout:

```text
<store>/
  .framenest-workstation-snapshot-store.json
  snapshots/
    <bundle-id>/
      snapshot.json
      bundle/
        manifest.json
        catalog.sqlite3
```

Final publication uses Linux `renameat2(RENAME_NOREPLACE)` with no overwrite
fallback. V1 has no workstation retention or final-snapshot deletion authority.

### Recovery CLI

`framenest-recovery` exposes only:

- `init-store`
- `pull`
- `list`
- `verify`

Level 1 (implemented): offline `list` and `verify`.
Level 2 (documented): operator-assisted transfer of the nested original bundle
into bounded NUC recovery staging with no-replace install and reverify.
Level 3 (documented): existing FrameNest verify/restore into a new absent
disposable database with integrity/FK/revision/semantic checks and no migration.
Level 4 (excluded): production stop/replace/migrate/cutover.

### Recovery layers

1. same-host scheduled verified backup (ADR-0052);
2. optional mounted off-device copy (ADR-0056);
3. preferred current NUC operator-workstation pull (this ADR).

## Consequences

- Repository capability may exist before real-host E3 acceptance.
- Current public repository SHA and current production SHA may differ until an
  authorized immutable deployment publishes the export command.
- Catalog-only scope is unchanged: media, covers, secrets, AI config, and full
  host state remain out of scope.
- Mounted ADR-0056 behavior remains available and must not be silently redefined
  as workstation snapshots.

## Alternatives considered

- NUC-pushed backup to workstation storage: rejected; grants NUC write authority
  and destination knowledge.
- Broad sudo/`framenest-backup *` rules: rejected; excess privilege.
- Reusing `off_device` status for workstation snapshots: rejected; distinct trust
  and transport boundaries.

## References

- [ADR-0033](0033-catalog-backup-and-recovery-foundation.md)
- [ADR-0052](0052-automated-catalog-backup-retention-and-restore-verification.md)
- [ADR-0056](0056-off-device-catalog-backup-copy-and-restore-verification.md)
- [BACKUP_AND_RECOVERY.md](../BACKUP_AND_RECOVERY.md)
- [UBUNTU_NUC_DEPLOYMENT.md](../UBUNTU_NUC_DEPLOYMENT.md)
