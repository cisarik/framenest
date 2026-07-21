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
mode that validates the selected private credential source and the selected
provider-specific tracked systemd drop-in template before any remote activity.
The helper is source material until a later bounded deployment task grants
exact host authority.

The helper manages only production AI provider configuration and the selected
provider credential. It must not be used as a general environment-file copier
or as authorization to run real NUC commands outside an explicit host task.
It atomically acquires `/run/framenest-ai-credential-deploy`; existing recovery
material causes a fail-closed stop before credential transmission or production
mutation. After a complete remote backup marker exists, failed deployment
mutations roll back the selected credential, systemd drop-in, and non-secret AI
configuration. The drop-in installed remotely is the exact tracked template
bytes transferred as a non-secret stdin payload, verified by deterministic byte
equivalence before and after atomic rename. Before restart, the helper verifies
systemd syntax, daemon-reloads, confirms `framenest.service` is still enabled,
and checks that systemd loaded the intended drop-in and credential identity.
Before restart, loaded-credential acceptance verifies the exact trusted drop-in
bytes, `DropInPaths`, and `systemctl cat` mapping without relying on redacted
`systemctl show LoadCredential` output. After readiness, it checks only the
same loopback capability endpoint used by the web status modal and requires the
selected provider/model to be configured, available, and credential-available.
A historical connection-test record does not fail deployment and is not treated
as proof that the newly installed credential is valid. Rollback daemon-reloads,
restarts, and waits up to 30 seconds for readiness on the restored service. Deployment and rollback
distinguish terminal service failure from readiness timeout. If rollback or
cleanup fails, the helper reports the sanitized phase and leaves recovery
material under `/run/framenest-ai-credential-deploy` for operator recovery.

This directory must not contain secrets, host UUIDs, disk serials, LAN IP
addresses, SSH fingerprints, private media filenames, or generated deployment
logs.
