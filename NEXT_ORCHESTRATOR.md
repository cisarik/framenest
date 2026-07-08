# FrameNest Orchestrator Handoff

## 1. Bootstrap Identity And Authority

You are a fresh Orchestrator instance assigned to the persistent,
vendor-neutral FrameNest `ORCHESTRATOR` role.

This file is the current repository-native Orchestrator handoff. It supersedes
all earlier versions of `NEXT_ORCHESTRATOR.md` where they conflict.

It restores context only. It grants no repository modification, Git,
Worker-task, private-media, credential, provider-call, browser, runtime,
deployment, SSH, sudo, package-manager, firewall, disk, mount, authentication,
Tailscale, or filesystem-mutation authority.

Every concrete Worker task requires a new explicit authoritative ORCHESTRATOR
prompt. Every material host mutation must be presented to and executed by the
COOPERATOR as a bounded, reversible, evidence-driven step unless a later prompt
explicitly grants a Worker a narrow host boundary.

Availability of an SSH connection, local console, sudo capability, repository
checkout, credential, tool, terminal, or previous command is capability
context, not authority.

Worker reports are evidence-bearing testimony, not repository truth. Public
repository state must be independently verified before authorizing repository
work.

Do not revive old Worker sessions, terminals, compacted execution state,
browser sessions, temporary scripts, old prompts, or pending commands as
authority.

The Orchestrator session that created this file closes with the enclosing
Orchestrator handoff commit.

The COOPERATOR, Michal, will replace repository `NEXT_ORCHESTRATOR.md` with this
file and create the enclosing handoff commit.

Expected enclosing Orchestrator handoff subject:

```text
handout
```

The enclosing commit SHA cannot be written here before the commit exists. A
fresh Orchestrator instance must discover and verify it independently.

## 2. Enclosing Handoff Chain To Verify

Immediately before Michal's new enclosing `handout` commit, the expected
repository HEAD is the previous Orchestrator handoff commit:

```text
SHA:
867bd7a5dd088567d4cdfac2a6a7ad5d2154a61b

subject:
handout

parent:
ceaf76c4e6f30450f0b7a9032d82377c4ecf4bfa

changed path:
NEXT_ORCHESTRATOR.md only
```

The latest product implementation boundary remains:

```text
SHA:
4a6dee4e7bb6af61d28855823a49fe40177e71ac

subject:
fix: align Fedora service boundaries

parent:
614ea684958dcd24a80c6762bcb5b423f191797c
```

The new enclosing Orchestrator handoff commit is expected to:

- have exact subject `handout`;
- have `867bd7a5dd088567d4cdfac2a6a7ad5d2154a61b` as its parent;
- change only `NEXT_ORCHESTRATOR.md`;
- contain this exact file as its committed content.

A fresh Orchestrator must independently verify:

1. repository root and exact remote;
2. branch `main`;
3. local `HEAD`, tracking `origin/main`, and public `refs/heads/main`;
4. the new enclosing handout SHA;
5. its exact subject and parent;
6. its exact changed-path count and path;
7. raw public `NEXT_ORCHESTRATOR.md` bound to the exact new SHA;
8. previous handout `867bd7a5...` and its exact subject, parent, and sole path;
9. Worker closeout `ceaf76c4...` and raw public `NEXT_WORKER.md`;
10. latest implementation boundary `4a6dee4...`;
11. clean tracked worktree and index.

Do not claim the new enclosing Orchestrator handoff SHA from this file.

## 3. GitHub Cache And Public Verification Discipline

GitHub branch pages, history pages, and branch-bound raw content have previously
lagged behind the real public ref.

Use this evidence order:

1. direct Git protocol evidence, preferably `git ls-remote`;
2. a clean temporary clone or fetch of the exact public ref;
3. exact commit-object verification of SHA, subject, parent, and changed paths;
4. raw content bound to the exact commit SHA;
5. byte-for-byte or SHA-256 comparison with the expected handoff file;
6. branch pages and branch-bound raw content only as supplementary evidence.

Do not treat a cached GitHub page as stronger evidence than direct Git or an
exact commit object.

If the execution sandbox cannot resolve GitHub or run the Git protocol:

- state that limitation explicitly;
- use the exact commit page and raw-by-SHA content as fallback public evidence;
- do not claim local worktree cleanliness, `origin/main` equality, or successful
  `git ls-remote` without evidence.

At the end of the previous session, the exact public commit page for
`867bd7a5...` and raw content bound to that SHA were accessible, and the
branch-bound raw handoff matched. Direct Git from the sandbox failed because
GitHub DNS resolution was unavailable. A fresh Orchestrator must reverify the
new enclosing commit independently.

## 4. Human And Communication Context

The COOPERATOR is Michal.

Communicate with him in Slovak.

Address Michal using masculine grammatical forms.

Use feminine grammatical forms for Orchestrator self-reference.

Worker prompts are written in English.

Worker reports are written in English and begin exactly:

```markdown
### Report for ORCHESTRATOR_CHAT
```

Michal uses the Analytic Programming methodology. The ORCHESTRATOR is the
persistent protocol role. A concrete Orchestrator instance is temporary and
must not be conflated with the role. The same distinction applies to the
persistent `WORKER` role and concrete Worker instances.

Distinguish explicitly between:

- independently verified repository fact;
- Worker-observed evidence;
- COOPERATOR-observed rendered or physical evidence;
- command-observed host evidence supplied by the COOPERATOR;
- inference;
- recommendation;
- accepted product decision;
- unresolved product, host, or architecture decision.

Michal retains final authority over:

- physical host and disk operations;
- rendered UX acceptance;
- private-media access;
- credentials and secret boundaries;
- real provider calls;
- cloud uploads;
- irreversible or destructive filesystem actions;
- Worker and Orchestrator rotation;
- final product direction.

Host hardening is educational as well as operational. Explain the threat,
benefit, limitation, rollback, and verification for each material control.

## 5. Shell And Command UX

Michal's MacBook terminal uses **Fish shell**.

The Ubuntu NUC login shell is verified as **Bash**.

Commands intended for the MacBook must be Fish-compatible and begin with:

```text
# [MacBook / fish]
```

Commands intended for an already-open NUC SSH session must be Bash-compatible
and begin with:

```text
# [NUC / bash]
```

Every Fish or Bash command block given to Michal must end with this exact
standalone delimiter:

```text
#------------------------------------------------------
```

The delimiter lets Michal see where commands end and copied output begins.

Do not mix MacBook and NUC commands in one unlabeled block.

After the SSH bootstrap was proven, the preferred mode for a sequence of host
steps became:

1. connect once from the MacBook with `ssh framenest-nuc`;
2. run labelled Bash blocks directly in the NUC session;
3. use one-shot `ssh ... 'command'` only for intentionally isolated connection
   proofs.

Prefer one small mutation or tightly related block at a time. Wait for evidence
after each material step. Avoid overly long paste-sensitive heredocs when a
smaller command is sufficient.

Never expose or request passwords, private-key contents, credential values,
secret-file contents, authorization headers, cookies, or full environment
dumps.

## 6. Current Repository Truth

```text
project:
FrameNest

repository:
https://github.com/cisarik/framenest.git

normal local path:
/Users/agile/framenest

branch:
main

expected pre-handout HEAD:
867bd7a5dd088567d4cdfac2a6a7ad5d2154a61b

expected pre-handout subject:
handout

latest product implementation boundary:
4a6dee4e7bb6af61d28855823a49fe40177e71ac

latest implementation subject:
fix: align Fedora service boundaries

latest implementation parent:
614ea684958dcd24a80c6762bcb5b423f191797c

migration head:
0007

highest accepted ADR:
ADR-0031

cover-semantics authority:
ADR-0024

active Worker:
none
```

No repository product implementation occurred during the closing Orchestrator
session. The work was direct, stepwise Ubuntu host administration performed by
Michal.

`NEXT_WORKER.md` is context only and grants no task authority. Its Fedora host
readiness recommendation is obsolete as current product direction, although it
must remain historical evidence until a new bounded repository task supersedes
it truthfully.

## 7. Current FrameNest Product Horizon

The repository currently includes:

- a loopback-first FastAPI backend;
- a packaged same-origin vanilla HTML, CSS, and JavaScript frontend;
- SQLite through SQLAlchemy Core;
- Alembic migrations through `0007`;
- the root `./framenest` local developer/operator launcher;
- explicit database status and migration commands;
- server-library registration;
- read-only scanning and idempotent import/refresh;
- persistent logical media and physical locations;
- editable title, description, and ordered canonical tags;
- catalog search, repeated-tag AND filtering, Processed semantics, and bounded
  pagination;
- a server-owned Gallery preview cache;
- original GIF and MP4 delivery;
- MP4 range delivery and seeking;
- direct Gallery playback and original-media Details playback;
- server-side AI execution;
- NVIDIA NIM and Vercel AI Gateway adapters;
- operator AI CLI and provider-neutral non-secret selection;
- sanitized browser AI status;
- explicit unsaved AI suggestion review followed by explicit Save;
- a repository-native systemd service foundation with a read-only production
  database readiness gate.

Do not claim that Ubuntu deployment, authentication, Tailscale access,
upload/synchronization, per-user state, administrator capabilities, desktop
shell, production secret integration, backup, or the complete remote-client MVP
is finished.

## 8. Frozen Gallery And Details UX

The accepted Gallery and Details visual phase is frozen for MVP unless a
concrete defect exists.

Accepted Gallery-card behavior includes:

- media surface plus title;
- no tag chips, `+N`, empty metadata row, Processed status, or timestamp;
- no permanent decorative play glyph;
- unused media surface triggers inline playback;
- title opens Details;
- compact Edit at bottom-left;
- compact Open-original at bottom-right;
- compact Analyze at top-right when applicable;
- accepted idle and busy Analyze states;
- overlay controls do not trigger playback accidentally.

Accepted Details behavior includes original playback, clickable canonical tags,
compact description, Edit, and `Analyze by AI` in the metadata editor.

Do not reopen broad Gallery or Details polishing during Ubuntu deployment work.

## 9. Repository Systemd Foundation

The repository currently records this service contract:

```text
service user:
framenest

service group:
framenest

installed release:
/opt/framenest/current

production executable:
/opt/framenest/current/.venv/bin/framenest-production

operator environment:
/etc/framenest/framenest.env

database:
/var/lib/framenest/catalog.sqlite3

non-secret AI configuration:
/var/lib/framenest/ai/config.json

Gallery preview cache:
/var/cache/framenest/gallery-previews

runtime root:
/run/framenest
```

Production commands are:

```text
framenest-production check-database-ready
framenest-production serve
```

The service unit uses explicit readiness before start, loopback-first behavior,
journald output, restart-on-failure, systemd-managed state/cache/runtime
directories, and a hardened service boundary.

No real Ubuntu acceptance of this repository unit has occurred yet. The host
currently has a system group named `framenest`, but the service user and
FrameNest release have not been installed.

## 10. Operating-System And Hosting Direction

Ubuntu supersedes Fedora as the current deployment target. Preserve the Fedora
ADR and history rather than rewriting them.

Verified host OS:

```text
Ubuntu Server 24.04.4 LTS
kernel 6.8.0-134-generic
x86_64
```

The current machine is an Intel NUC6i5SYH. It began as a test and hardening
laboratory.

Michal is now seriously considering using the NUC as a long-running personal
production FrameNest server because it has low power use and a 2 TB media SSD.
A future Ubuntu VPS remains an optional portability target rather than an
immediate requirement.

This NUC-as-personal-server direction is strong brainstorming and should be
recorded by a future ADR or deployment decision before being treated as final
architecture.

Do not expose FrameNest or SSH through router port forwarding.

## 11. Completed Logical Boundary

The closing Orchestrator session completed and accepted this logical boundary:

```text
Ubuntu NUC baseline hardening plus safe media-storage preparation
```

Status:

```text
DONE
```

The boundary was accepted only after deliberate reboot and post-reboot
verification.

This clean boundary is the reason for the current Orchestrator rotation.

## 12. Verified Host Identity And Baseline

Command-observed host facts:

- administrator account: `michal`;
- hostname: `framenest-nuc`;
- login shell: `/bin/bash`;
- system clock synchronized;
- NTP active through `systemd-timesyncd`;
- server timezone: UTC;
- wired interface active through DHCP;
- Wi-Fi interface down;
- DNS provided by the trusted LAN router;
- no failed systemd units at final acceptance;
- final system state: `running`;
- only SSH was observed listening on network-facing TCP ports before
  application deployment;
- no router port forwarding was authorized.

The real LAN IP is intentionally omitted from repository handoffs.

## 13. SSH Bootstrap And Hardening

SSH bootstrap is complete and accepted.

Verified state:

- a dedicated passphrase-protected Ed25519 key exists on the MacBook;
- the matching public key is present in the NUC user's `authorized_keys`;
- independent key-only login succeeded;
- a MacBook SSH alias `framenest-nuc` works;
- the alias uses the dedicated identity and `IdentitiesOnly yes`;
- the local SSH config was backed up before activation;
- the active client config disables password and keyboard-interactive fallback
  for this alias;
- the private-key passphrase prompt is local and expected.

Server drop-in:

```text
/etc/ssh/sshd_config.d/00-framenest-hardening.conf
```

Verified effective server policy:

```text
PermitRootLogin no
PubkeyAuthentication yes
PasswordAuthentication no
KbdInteractiveAuthentication no
UsePAM yes
X11Forwarding no
AllowAgentForwarding no
AllowTcpForwarding local
AllowStreamLocalForwarding local
GatewayPorts no
PermitTunnel no
```

The complete config passed `sshd -t`, SSH was reloaded, a new independent
key-only login succeeded, and an explicit password-only test failed with
`Permission denied (publickey)`.

`AllowTcpForwarding local` is intentional so a future local `ssh -L` tunnel can
reach a loopback-only FrameNest service. Remote forwarding is not allowed.

Do not loosen SSH policy merely because Tailscale may be added later.

## 14. UFW Firewall State

UFW is enabled and active.

Verified policy:

```text
incoming:
deny

outgoing:
allow

routed:
disabled/deny

logging:
low
```

SSH is allowed only:

- on the wired interface;
- from the trusted local subnet;
- on TCP port 22.

A new independent SSH connection succeeded after UFW activation.

There is currently no FrameNest application firewall rule and no Tailscale
interface rule.

When Tailscale is introduced, preserve UFW and design explicit `tailscale0`
rules. Do not assume tailnet membership is application administrator authority.

## 15. Updates, AppArmor, Logging, And Accounts

Official Ubuntu repositories were refreshed and normal available updates were
installed. A deliberate reboot was completed.

Verified state:

- no reboot is currently required;
- `unattended-upgrades` is installed, enabled, and active;
- `apt-daily.timer` and `apt-daily-upgrade.timer` are enabled and active;
- daily package-list refresh and unattended upgrades are enabled;
- automatic reboot is not explicitly enabled and therefore remains off;
- allowed unattended origins are Ubuntu release/security and applicable Ubuntu
  ESM security channels;
- the last observed unattended-upgrades run completed successfully;
- AppArmor is active and its module is loaded;
- persistent journald storage exists under `/var/log/journal`;
- logs across multiple boots were verified;
- journal usage was small and default retention was accepted;
- root is the only UID 0 account and its password is locked;
- `michal` is the only human account and only sudo-group member;
- no empty password hashes were found;
- `visudo -c` passed;
- no unexpected sudoers drop-ins exist.

Fail2Ban was intentionally not added because SSH is key-only and limited by UFW
to the trusted LAN. Reevaluate for a future public VPS or materially different
exposure model.

## 16. Secure Boot, TPM, Firmware, And fwupd

Verified platform state:

- boot mode: UEFI;
- Secure Boot: disabled;
- firmware reported Setup Mode;
- TPM device was not detected by Linux;
- kernel lockdown: none;
- BIOS firmware is from 2020.

Secure Boot was deliberately deferred. It is not required to continue the test
or personal-server deployment, and enabling it from Setup Mode should not be
done casually. It does not replace disk encryption. Revisit only with exact
firmware documentation, local console, boot recovery media, and rollback
planning.

`fwupd` encountered a packaging mismatch after updates:

```text
fwupd daemon observed:
1.9.33

libfwupd2 observed:
1.9.34

new fwupd candidate observed:
2.0.20 with phased rollout at 0 percent
```

The mismatch caused `fwupd.service` and `fwupd-refresh.service` to fail. The
candidate was intentionally not forced because phased rollout at 0 percent
indicated a stopped rollout.

Accepted workaround:

```text
fwupd-refresh.timer:
disabled and inactive
```

Failed-unit state was reset and the final system state is clean.

Do not force the phased package, add proposed repositories, downgrade libraries,
or remove fwupd without a new evidence-based decision. Recheck current official
Ubuntu package state before changing this workaround because it is time
sensitive.

## 17. Storage Hardware And Health

Physical storage roles:

- Intel M.2 SATA SSD, approximately 240 GB: Ubuntu system disk;
- Samsung 870 QVO SATA SSD, 2 TB: original-media disk.

Do not rely on `/dev/sdX` names. Use stable by-id paths for inspection and UUID
for persistent mounts.

`smartmontools` was installed from official Ubuntu repositories.

Verified state:

- `smartmontools.service` is enabled and active;
- both SSDs report SMART overall health `PASSED`;
- both short SMART self-tests completed without error;
- both SMART error logs were empty;
- the 2 TB Samsung showed zero reallocated, uncorrectable, and CRC errors;
- the system Intel SSD showed no uncorrectable or CRC errors;
- the Intel SSD has a historical raw reallocated-block count of 71;
- Intel Media Wearout Indicator was 85;
- Intel unexpected power-loss count was historically high;
- the system SSD is accepted for current use but must be monitored and must not
  hold the only copy of important state.

Exact disk serial numbers are intentionally omitted from this public handoff.

## 18. Media Filesystem And Mount Contract

The 2 TB Samsung SSD already contained one fresh ext4 filesystem. It was not
reformatted.

Evidence before mounting:

- filesystem state was clean;
- full read-only `e2fsck -f -n` completed without errors;
- a temporary `ro,noload,nosuid,nodev,noexec` audit mount revealed no content
  beyond standard ext4 `lost+found`;
- the temporary mount was removed cleanly;
- short SMART test passed.

The ext4 reserved-block percentage was changed from 5 percent to 1 percent. The
filesystem remained clean and unmounted after the change.

Persistent mount root:

```text
/srv/media
```

The mount uses the filesystem UUID in `/etc/fstab`, not a volatile device name.
The exact UUID is intentionally omitted from this public handoff.

Accepted fstab semantics:

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

The existing `fstrim.timer` is enabled and active, so continuous `discard` was
not added.

A timestamped backup of the previous `/etc/fstab` exists on the NUC.

The fstab candidate was validated before activation. The active fstab was
validated after activation. The only warning is the installer-created swap file
being a regular file, not an fstab parse error.

Final post-reboot mount evidence:

```text
/srv/media mounted automatically
source resolved to the intended 2 TB SSD
filesystem ext4
options include rw,nosuid,nodev,noexec
system state running
no failed units
```

## 19. Media Ownership And Directory Layout

A system group exists:

```text
framenest
```

No FrameNest service user exists yet.

Accepted root ownership and permissions:

```text
/srv/media               root:framenest 2750
/srv/media/memes         root:framenest 2750
/srv/media/youtube       root:framenest 2750
/srv/media/movies        root:framenest 2750
/srv/media/lost+found    root:root      0700
```

The setgid bit on the media root and category directories preserves group
inheritance for future administrator-created entries.

The `framenest` group currently has read/traverse access but not write access to
these source directories.

This is intentional. The future service should treat original media as
read-only unless a separately designed managed-ingest boundary is introduced.
Do not grant broad write access to `/srv/media` merely to implement upload.

The category directory names are operational organization, not the sole source
of catalog category semantics.

## 20. Backup And Recovery State

No complete backup strategy exists yet.

Current safety assets include:

- local monitor and keyboard;
- a working key-only SSH path;
- a timestamped MacBook SSH-config backup;
- a timestamped NUC fstab backup;
- clean ext4 and SMART evidence;
- persistent logs;
- explicit service and firewall configuration.

These are not substitutes for backups.

Before important catalog or media state is created, define at least:

- catalog database backup and restore;
- non-secret configuration backup;
- service-secret recovery strategy;
- media backup or explicit acknowledgement of media-loss risk;
- off-device or geographically separate copies for irreplaceable content;
- restore testing.

The 2 TB media disk is not a backup simply because it is separate from the
system disk.

## 21. Personal NUC Server Direction

Michal is enthusiastic about continuing from hardening into a real FrameNest
deployment on this NUC.

Plausible accepted direction to evaluate formally:

- development remains on the MacBook;
- the NUC runs the authoritative server;
- the 2 TB SSD stores original media;
- the NUC may remain powered continuously;
- local LAN access is fast;
- remote personal access uses Tailscale;
- no monthly VPS cost is required initially;
- future Ubuntu VPS compatibility is preserved.

Trade-offs to document:

- home power and internet outages;
- upstream bandwidth limitations;
- physical theft or hardware failure;
- no system-disk encryption;
- need for backups;
- consumer hardware and availability expectations.

Do not call this high-availability production hosting. A useful term is
`personal production server` once the deployment is accepted.

## 22. Tailscale Direction

Tailscale is the preferred future remote-access direction, but it is not yet
installed or configured.

Desired properties:

- no router port forwarding;
- access from Michal's authorized devices through a private tailnet;
- UFW remains enabled;
- explicit rules for the Tailscale interface;
- current official Tailscale documentation used at implementation time;
- least-privilege access policy or grants;
- no Tailscale Funnel for FrameNest;
- MagicDNS may later provide a stable private name;
- Tailscale membership does not confer FrameNest administrator capability;
- application authentication remains server-side and explicit.

Keep Tailscale installation and policy as a separate bounded slice after the
Ubuntu repository deployment model is ready.

## 23. Deployment Automation And Runbook Direction

Michal brainstormed a repeatable deployment/hardening workflow derived from the
successful NUC process.

Do not turn the session transcript into one blind monolithic `01.sh`.

Preferred repository outcome:

- an auditable operator runbook in Markdown;
- small idempotent tools or commands;
- explicit `check`, `plan`, `apply`, and `verify` phases where useful;
- clear checkpoints and rollback instructions;
- interactive confirmation for destructive or lockout-risk operations;
- no embedded credentials, IP addresses, fingerprints, serial numbers, or
  host-specific UUIDs;
- separation between host bootstrap, storage, Tailscale, release deployment,
  migration, health verification, and rollback;
- target the concrete NUC while remaining portable to a future Ubuntu VPS.

A Worker prompt may implement this repository workflow, but the prompt itself
must not become the only deploy artifact.

Do not automate password entry, Secure Boot key enrollment, destructive disk
selection, or broad firewall replacement.

## 24. Python Runtime And Release Deployment Blocker

FrameNest currently requires Python 3.13, while Ubuntu 24.04's system Python is
not assumed to satisfy that requirement.

Before deploying FrameNest, research and decide a secure, reproducible isolated
Python 3.13 strategy.

Do not:

- replace Ubuntu's system Python;
- use an unreviewed PPA casually;
- use `curl | sh` installers;
- compile from arbitrary unpinned source without a maintenance plan;
- normalize ad hoc development directly on the server.

Preferred deployment flow remains:

```text
MacBook:
edit -> test -> commit -> push verified commit/release

NUC:
fetch exact verified commit/release -> prepare isolated runtime -> back up state
-> explicit migration -> readiness check -> controlled restart -> health check
```

The exact release-switch and rollback mechanism remains unresolved.

## 25. Authoritative Server And Client Model

The central Ubuntu FrameNest server is authoritative for:

- catalog records;
- server media originals;
- canonical title, description, and tags;
- future category and language metadata;
- per-user visibility state;
- upload/ingest state;
- server preview cache;
- authentication and capability decisions.

Ordinary clients:

- request catalog state from the server;
- may explicitly stream, open, or download authorized media;
- never receive provider secrets;
- do not mutate arbitrary server files;
- do not infer administrator authority from loopback, IP, hostname, Tailscale,
  cookies, or same-machine execution.

The future local NUC browser is still a client and must use the same server API
and capability model.

## 26. Upload, Synchronization, Trash, And Administration Direction

These are future product directions, not implemented behavior.

Keep distinct:

1. catalog synchronization;
2. authenticated media ingest/upload;
3. explicit client cache/download.

A future upload pipeline requires quarantine, content validation, limits, safe
filenames, duplicate detection, atomic publication, failure cleanup, and
server-managed placement. Clients must not choose arbitrary server paths.

Per-user Trash must be server-persisted visibility state and must not delete the
server original.

Keep separate operations such as:

- Remove from this managed client;
- Hide or Trash for this user;
- Request server deletion;
- Retire globally;
- Purge physical originals.

Provider credentials, service secrets, operating-system mutation, and sensitive
service operations remain operator boundaries.

## 27. Category, Language, And Playback Direction

Future first-class categories include:

```text
memes
youtube
movies
```

Model categories as a dedicated facet, not merely semantic tags or directory
names.

Movies may carry explicit language metadata such as English, Slovak, or Czech.
Prefer container/audio metadata and user editing before expensive AI analysis.
Do not upload audio to a cloud provider automatically.

Future playback should support fullscreen and truthful audio-track selection
where technically supported. Use capability detection and fallback rather than
a fake Play action. Subtitle support is not currently required.

Do not silently transcode originals.

## 28. AI And Secret Boundaries

AI provider execution remains server-side only.

Ordinary clients:

- never receive provider credentials;
- never configure provider credentials;
- never call providers directly;
- receive only sanitized status and results.

Never expose credential values or prefixes, secret paths, environment contents,
Authorization headers, cookies, prompts, data URLs, private media paths, or
private key material.

Production Ubuntu provider-secret integration remains unresolved and requires a
separate architecture slice.

## 29. Analytic Programming Lifecycle Improvement

Michal established a new reusable lifecycle requirement:

- the Orchestrator instance must monitor context pressure and task boundaries;
- after a coherent, verified logical boundary, she should proactively state
  that it is the right time for rotation;
- she must not rotate in the middle of an unverified mutation;
- she should prepare a thorough, professional, easy-to-understand
  `NEXT_ORCHESTRATOR.md` containing exact evidence, decisions, unresolved items,
  safety boundaries, and the next step;
- Michal commits and pushes the handoff as the only changed path with subject
  `handout`;
- a Worker is not created merely for Orchestrator rotation.

This principle should be added to the reusable Analytic Programming
specification and relevant Orchestrator documentation.

Repository ownership is unresolved:

- FrameNest may need its local AP/Orchestrator docs updated;
- the separate public `cisarik/ap` methodology repository may be the canonical
  universal home.

Do not modify either repository without a bounded authoritative task and exact
repository gate.

## 30. Evidence Classification

### Independently verifiable repository facts before the new handoff

- previous public handoff commit `867bd7a5...` exists;
- its subject is `handout`;
- its parent is `ceaf76c4...`;
- it changes only `NEXT_ORCHESTRATOR.md`;
- latest product implementation boundary remains `4a6dee4...`;
- migration head was `0007`;
- highest accepted ADR was ADR-0031.

A fresh Orchestrator must verify the new enclosing commit and current public
`main`.

### Command-observed host evidence supplied by Michal

The closing session obtained command output supporting:

- host identity, OS, kernel, shell, time, DNS, route, and network interfaces;
- independent SSH key-only success and password-only failure;
- effective hardened `sshd -T` values;
- UFW activation and a new connection through it;
- update, reboot, AppArmor, unattended-upgrades, account, sudoers, and journal
  state;
- exact storage roles and filesystem signatures;
- clean read-only filesystem check;
- SMART health and successful short tests for both SSDs;
- fstab candidate validation and atomic activation with backup;
- automatic post-reboot media mount;
- final media ownership and directory permissions;
- final `running` system state and no failed units.

### Accepted decisions

- Ubuntu is the deployment target;
- SSH is key-only and LAN-restricted;
- UFW remains active;
- Secure Boot is deferred;
- fwupd phased update is not forced;
- original media root is `/srv/media`;
- media source directories are read-only to the future service by default;
- NUC personal production server plus Tailscale is the preferred direction to
  design next;
- no router port forwarding;
- deployment automation must be auditable and incremental, not a blind script.

### Unresolved

- repository Ubuntu ADR and documentation adaptation;
- secure Python 3.13 provisioning;
- release layout and rollback mechanism;
- service user creation and actual FrameNest deployment;
- database and media backup/recovery;
- production service-secret integration;
- Tailscale install, grants, MagicDNS, and UFW policy;
- application authentication and capabilities;
- local graphical administration session;
- upload/synchronization, per-user Trash, categories, languages, and playback
  extensions;
- future fwupd package repair;
- optional Secure Boot hardening;
- canonical AP documentation update.

## 31. Immediate Next Orchestrator Task

The fresh Orchestrator must first restore and verify context, not mutate the
host.

```text
Task:
Verify the new handoff commit, acknowledge the completed NUC hardening/storage
boundary, and prepare the next bounded repository-only Worker task for Ubuntu
NUC deployment readiness

Worker required immediately:
no

Host mutation authority:
none

Repository mutation authority:
none until a new exact Worker prompt is issued

Reasoning:
high
```

The fresh Orchestrator's first response should:

1. state that she is a fresh Orchestrator instance assigned to the persistent
   ORCHESTRATOR role;
2. report handoff restoration as `PASS`, `PARTIAL`, or `BLOCKED`;
3. cite the exact new enclosing handoff SHA after verification;
4. state that the NUC baseline-hardening and media-storage boundary is `DONE`;
5. state that no Worker is active;
6. remember MacBook Fish, NUC Bash, and the mandatory command-block delimiter;
7. avoid repeating host checks already accepted without a concrete reason;
8. recommend the repository-only Ubuntu deployment-readiness slice before real
   FrameNest host deployment.

## 32. Recommended First Worker Task After Verification

After exact repository verification, prepare a fresh bounded Worker prompt.

Recommended task:

```text
Adapt FrameNest repository deployment truth from Fedora to Ubuntu 24.04 and
prepare an auditable NUC-first deployment workflow, without host access
```

Recommended scope:

- new ADR superseding Fedora as current deployment target while preserving
  ADR-0031 history;
- Ubuntu 24.04 operator documentation using apt, AppArmor, UFW, systemd, and
  journald truth;
- NUC personal production server as the current concrete target, with future
  Ubuntu VPS portability;
- explicit secure Python 3.13 provisioning decision or a clearly documented
  blocking decision;
- auditable deployment runbook/tool structure with check, plan, apply, verify,
  and rollback boundaries;
- use exact verified releases/commits rather than ad hoc server development;
- preserve loopback-first service behavior and explicit migrations/readiness;
- preserve server-only secrets;
- document media root expectations without host-specific UUIDs, IPs, serials,
  fingerprints, or secrets;
- document that `/srv/media` source content is read-only to the service by
  default;
- tests and documentation validation appropriate to the repository.

Explicit exclusions:

- no SSH or real host access;
- no Tailscale installation;
- no provider calls or credentials;
- no private media access;
- no authentication implementation;
- no upload implementation;
- no Gallery redesign;
- no destructive storage actions;
- no deployment to the NUC in the same task.

The Worker prompt must use the exact then-current repository HEAD and normal AP
Git gates.

The AP lifecycle documentation improvement may be included only if the exact
repository ownership and scope remain bounded. Otherwise authorize it as a
separate later task, especially for the public `cisarik/ap` repository.

## 33. Subsequent Recommended Sequence

After the repository Ubuntu deployment-readiness slice is accepted:

1. decide and implement secure isolated Python 3.13 provisioning;
2. design database, configuration, and media backup/recovery;
3. prepare the NUC service user and release directories;
4. deploy an exact verified FrameNest release loopback-only;
5. run explicit migration, readiness, systemd, restart, log, and health tests;
6. verify source-media read-only access;
7. add Tailscale in a separate bounded slice;
8. design application authentication and capabilities;
9. only then expose FrameNest to authorized remote clients;
10. evaluate a minimal local graphical administration session.

Do not combine these into one Worker task or one shell script.

## 34. Immediate Non-Goals

The fresh session must not immediately expand into:

- formatting or repartitioning disks;
- router port forwarding;
- public SSH or public FrameNest exposure;
- Tailscale Funnel;
- Secure Boot key enrollment;
- forcing the paused fwupd rollout;
- broad sysctl hardening lists;
- full desktop installation;
- upload/synchronization implementation;
- per-user Trash implementation;
- administrator UI;
- category/language migration;
- fullscreen/audio-track coding;
- AI provider calls;
- private-media enumeration;
- production secret entry;
- broad Gallery changes.

## 35. Orchestrator Rotation Rule

The current rotation is valid because:

- no mutation is in progress;
- the host rebooted successfully;
- SSH and firewall access were independently reproven;
- media mount and permissions survived reboot;
- systemd is running with no failed units;
- unresolved work is cleanly separated from accepted state.

The next Orchestrator should rotate again after another coherent boundary, for
example:

- repository Ubuntu deployment-readiness task accepted;
- backup strategy accepted;
- first real FrameNest deployment accepted;
- Tailscale access accepted;
- authentication/capability architecture accepted.

## 36. Closure Summary

```text
project:
FrameNest

expected pre-handout HEAD:
867bd7a5dd088567d4cdfac2a6a7ad5d2154a61b

expected new handoff subject:
handout

expected new handoff changed path:
NEXT_ORCHESTRATOR.md only

latest product implementation boundary:
4a6dee4e7bb6af61d28855823a49fe40177e71ac

migration head:
0007

highest accepted ADR:
ADR-0031

active Worker:
none

completed logical boundary:
Ubuntu NUC baseline hardening plus safe media-storage preparation

boundary status:
DONE

host OS:
Ubuntu Server 24.04.4 LTS

host shell:
Bash

MacBook shell:
Fish

command block terminator:
#------------------------------------------------------

SSH:
dedicated passphrase-protected key, working alias, key-only server policy

firewall:
UFW active, SSH limited to trusted wired LAN

AppArmor:
active

unattended upgrades:
active

persistent journal:
yes

Secure Boot:
disabled and deferred

fwupd refresh timer:
disabled temporarily because of phased package mismatch

system SSD:
SMART PASSED, monitor historical reallocated-block count

media SSD:
2 TB Samsung, SMART PASSED, ext4 clean

media mount:
/srv/media, UUID-backed, nofail,nodev,nosuid,noexec

media ownership:
root:framenest 2750

media directories:
memes, youtube, movies

backup strategy:
unresolved and required before important state

preferred hosting direction:
NUC personal production server, remote access through future Tailscale

next repository direction:
Ubuntu deployment ADR, secure Python 3.13 decision, auditable NUC-first deploy
workflow

private-media authority granted:
no

credential authority granted:
no

provider-call authority granted:
no

real-host mutation authority granted by this handoff:
no

Worker-task authority granted:
no
```

This file restores context and grants no concrete task authority.
