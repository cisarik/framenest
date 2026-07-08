# FrameNest Ubuntu Deployment Support

This directory makes the Ubuntu deployment workflow discoverable without adding
untested host-mutating automation.

The current authoritative runbook is
[docs/UBUNTU_NUC_DEPLOYMENT.md](../../docs/UBUNTU_NUC_DEPLOYMENT.md). The
architecture decision is
[ADR-0032](../../docs/adr/0032-ubuntu-nuc-deployment-foundation.md).

## Phase Map

| Phase | Repository support | Mutation class |
|---|---|---|
| check | Runbook sections `0`, `1`, and `6` | read-only |
| plan | Runbook section `2` | no host mutation |
| apply | Runbook sections `3`, `4`, `5`, and `7` | planned, reversible, or service-affecting |
| verify | Runbook sections `6`, `8`, and `10` | read-only after mutation |
| rollback | Runbook section `9` | planned recovery mutation |

## Boundaries

No executable helper is committed in this slice. Real host commands belong in a
future bounded deployment task after the operator has exact host authority.

This directory must not contain secrets, host UUIDs, disk serials, LAN IP
addresses, SSH fingerprints, private media filenames, or generated deployment
logs.
