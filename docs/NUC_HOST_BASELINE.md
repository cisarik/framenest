# FrameNest NUC Host Baseline

## Status

This document preserves sanitized, command-observed host baseline facts accepted
for the Intel NUC6i5SYH after the Ubuntu hardening and media-storage
preparation boundary. It is a durable project record, not a deployment runbook,
session handoff, installer, host mutation task, or proof that FrameNest has been
deployed.

Observation source: command output supplied by Michal during the accepted NUC
hardening/storage session.

Acceptance record: the repository handoff committed on 2026-07-08 recorded the
logical boundary as complete after reboot and post-reboot verification. Exact
host command timestamps are not retained here.

This document intentionally omits real LAN addresses, disk serial numbers,
filesystem UUIDs, SSH fingerprints, private paths, credentials, environment
contents, and private media filenames.

Related durable documents:

- [ADR-0032](adr/0032-ubuntu-nuc-deployment-foundation.md) records the accepted
  Ubuntu NUC deployment foundation.
- [Ubuntu NUC deployment runbook](UBUNTU_NUC_DEPLOYMENT.md) records the future
  deployment workflow.
- [Backup and recovery runbook](BACKUP_AND_RECOVERY.md) records the catalog
  backup and restore-to-new-destination foundation.

## Decision Context

Ubuntu Server 24.04 on the Intel NUC6i5SYH is the current concrete personal
production server direction for the optional FrameNest server. This supersedes
Fedora for the active deployment target while preserving the historical Fedora
ADR and service source material.

The completed host boundary was:

```text
Ubuntu NUC baseline hardening plus safe media-storage preparation
```

The boundary does not grant future host mutation authority. Any future SSH,
sudo, package, firewall, storage, service, Tailscale, deployment, backup,
secret, or authentication work requires a new bounded task and fresh evidence.

## Command-Observed Host Facts

The accepted host baseline is:

- host operating system: Ubuntu Server 24.04 LTS on x86_64;
- hardware direction: Intel NUC6i5SYH personal production server;
- shell for an already-open NUC session: Bash;
- time synchronization active through systemd-timesyncd;
- final accepted system state: running, with no failed systemd units;
- SSH was the only observed network-facing TCP listener before application
  deployment;
- no router port forwarding was authorized.

## SSH Baseline

SSH bootstrap and hardening were completed and accepted:

- key-only login succeeded with a dedicated passphrase-protected Ed25519 key;
- the MacBook alias `framenest-nuc` uses the dedicated identity and
  `IdentitiesOnly yes`;
- password and keyboard-interactive fallback are disabled for that alias;
- server root login is disabled;
- server password and keyboard-interactive authentication are disabled;
- X11 forwarding, agent forwarding, remote TCP forwarding, stream-local
  forwarding, gateway ports, and tunnels are disabled or restricted;
- local TCP forwarding remains allowed intentionally for a future loopback-only
  FrameNest tunnel;
- an explicit password-only login test failed with public-key-only behavior.

Do not loosen SSH policy merely because Tailscale may be added later.

## Firewall, Updates, Logging, And Accounts

The accepted host hardening baseline is:

- UFW is enabled and active;
- default incoming traffic is denied;
- outgoing traffic is allowed;
- routed traffic is denied or disabled;
- SSH is allowed only on the wired trusted LAN boundary;
- no FrameNest application or Tailscale firewall rule exists yet;
- official Ubuntu updates were applied and the host was deliberately rebooted;
- unattended upgrades are installed, enabled, and active;
- automatic reboot for unattended upgrades remains off;
- AppArmor is active and loaded;
- persistent journald storage exists and logs across multiple boots were
  verified;
- root is the only UID 0 account and root password login is locked;
- Michal is the only human account and only sudo-group member;
- sudoers validation passed;
- Fail2Ban was intentionally not added for the current key-only, LAN-restricted
  SSH exposure model.

When Tailscale is introduced, preserve UFW and design explicit Tailscale
interface rules. Tailnet membership must not become application administrator
authority.

## Secure Boot, Firmware, And fwupd

The accepted platform state is:

- UEFI boot mode;
- Secure Boot disabled and deliberately deferred;
- no TPM device detected by Linux;
- kernel lockdown disabled;
- BIOS firmware was reported as older firmware.

Secure Boot is not required for the current personal-server deployment path and
must not be enabled casually. Revisit only with exact firmware documentation,
local console access, boot recovery media, rollback planning, and explicit
authority.

`fwupd` encountered a version mismatch during the accepted hardening session.
The candidate package was in a phased rollout at zero percent, so it was not
forced. The accepted temporary workaround was disabling the `fwupd` refresh
timer, resetting failed-unit state, and leaving the system clean.

This workaround is time-sensitive. Recheck current official Ubuntu package
state before changing it. Do not force the paused phased package, add proposed
repositories, downgrade libraries, or remove `fwupd` without a new
evidence-based decision.

## Storage Health And Roles

The accepted storage roles are:

- Intel approximately 240 GB system SSD for Ubuntu;
- Samsung 870 QVO 2 TB SSD for original media.

Use stable by-id paths for inspection and filesystem UUIDs for persistent
mounts. Do not rely on volatile `/dev/sdX` names.

Accepted health evidence:

- `smartmontools` was installed from official Ubuntu repositories;
- SMART service is enabled and active;
- both SSDs reported SMART overall health `PASSED`;
- short SMART self-tests completed without error on both SSDs;
- both SMART error logs were empty;
- the 2 TB media SSD showed zero reallocated, uncorrectable, and CRC errors;
- the system SSD showed no uncorrectable or CRC errors;
- the system SSD has a historical raw reallocated-block count and must be
  monitored;
- the system SSD is accepted for current use but must not hold the only copy of
  important state.

## Media Filesystem And Mount

The 2 TB media SSD already contained one fresh ext4 filesystem and was not
reformatted. Before persistent activation, the accepted evidence included a
clean read-only filesystem check, a temporary read-only audit mount, and a clean
short SMART test.

The persistent media mount is:

```text
/srv/media
```

Accepted mount semantics:

```text
ext4
defaults
nofail
nodev
nosuid
noexec
x-systemd.device-timeout=10s
dump 0
fsck pass 2
```

The mount uses the filesystem UUID in `/etc/fstab`; the UUID is intentionally
not recorded here. The existing `fstrim.timer` remains enabled and continuous
`discard` was not added.

Post-reboot verification showed `/srv/media` mounted automatically from the
intended 2 TB SSD as ext4 with `rw,nosuid,nodev,noexec`, system state running,
and no failed units.

## Media Ownership Model

A system group named `framenest` exists on the host. No FrameNest service user
exists yet.

Accepted ownership and permissions:

```text
/srv/media               root:framenest 2750
/srv/media/memes         root:framenest 2750
/srv/media/youtube       root:framenest 2750
/srv/media/movies        root:framenest 2750
/srv/media/lost+found    root:root      0700
```

The setgid bit preserves group inheritance for administrator-created entries.
The `framenest` group currently has read/traverse access but not write access to
source directories.

This is intentional. The future FrameNest service treats original media as
read-only by default. A future upload or managed-ingest feature must use a
separate server-owned boundary rather than broad write access to `/srv/media`.

The directory names `memes`, `youtube`, and `movies` are operational
organization, not the only source of catalog category semantics.

## Not Completed

Repository capability now exists for synthetic catalog backup creation,
verification, and restore-to-new-destination through
[ADR-0033](adr/0033-catalog-backup-and-recovery-foundation.md) and
[Backup and recovery runbook](BACKUP_AND_RECOVERY.md). That capability does
not prove production recovery on the NUC.

The accepted baseline does not include:

- FrameNest service user creation;
- FrameNest release installation;
- systemd service installation, enablement, or activation;
- production database replacement;
- production provider-secret integration;
- Tailscale installation or policy;
- application authentication or administrator capability model;
- complete media backup acceptance;
- complete database production backup acceptance;
- a real NUC catalog backup bundle;
- an off-device backup copy;
- a retention policy;
- production database replacement;
- a production restore drill;
- router port forwarding;
- host-level proof of FrameNest application health.

The 2 TB media SSD is not a backup merely because it is separate from the system
SSD. Before important production catalog or media state is created, FrameNest
still needs real-host catalog backup acceptance, non-secret configuration
recovery, service-secret recovery, media second-copy strategy or explicit
loss-risk acceptance, retention decisions, off-device copies, and restore
testing.

## Future Work Boundaries

Future NUC work should remain incremental and evidence-driven:

- exact-release deployment workflow;
- secure isolated CPython 3.13 provisioning;
- service user and release directory preparation;
- explicit migration and readiness;
- loopback health and journald verification;
- catalog and media backup/recovery;
- Tailscale-only remote access;
- application authentication and capabilities.

Do not combine those into a blind monolithic script or a single broad host
mutation task.
