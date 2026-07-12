# FrameNest Ubuntu Deployment Support

This directory makes the Ubuntu deployment workflow discoverable without adding
untested host-mutating automation.

The current authoritative runbook is
[docs/UBUNTU_NUC_DEPLOYMENT.md](../../docs/UBUNTU_NUC_DEPLOYMENT.md). The
architecture decision is
[ADR-0032](../../docs/adr/0032-ubuntu-nuc-deployment-foundation.md). The
catalog backup and recovery prerequisite is documented in
[docs/BACKUP_AND_RECOVERY.md](../../docs/BACKUP_AND_RECOVERY.md) and
[ADR-0033](../../docs/adr/0033-catalog-backup-and-recovery-foundation.md).

## Phase Map

| Phase | Repository support | Mutation class |
|---|---|---|
| check | Runbook sections `0`, `1`, and `6` | read-only |
| plan | Runbook section `2` | no host mutation |
| apply | Runbook sections `3`, `4`, `5`, and `7` | planned, reversible, or service-affecting |
| verify | Runbook sections `6`, `8`, and `10` | read-only after mutation |
| rollback | Runbook section `9` | planned recovery mutation |
| catalog backup | Backup runbook sections `create`, `verify`, and `restore drill` | new bundle or disposable restored catalog |

## Boundaries

`fn-production-env-deploy` is the repository-owned Fish entry point for the
first production AI credential/configuration helper. It has a non-mutating check
mode and is source material until a later bounded deployment task grants exact
host authority.

The helper manages only production AI provider configuration and the selected
provider credential. It must not be used as a general environment-file copier
or as authorization to run real NUC commands outside an explicit host task.
It atomically acquires `/run/framenest-ai-credential-deploy`; existing recovery
material causes a fail-closed stop before credential transmission or production
mutation. After a complete remote backup marker exists, failed deployment
mutations roll back the selected credential, systemd drop-in, and non-secret AI
configuration, then daemon-reload, restart, and wait up to 30 seconds for
readiness on the restored service. Deployment and rollback distinguish terminal
service failure from readiness timeout. If rollback or cleanup fails, the helper
reports the sanitized phase and leaves recovery material under
`/run/framenest-ai-credential-deploy` for operator recovery.

This directory must not contain secrets, host UUIDs, disk serials, LAN IP
addresses, SSH fingerprints, private media filenames, or generated deployment
logs.
