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
prompt.

Host-administration guidance given directly to the COOPERATOR must also remain
bounded, reversible, evidence-driven, and stepwise. Availability of an SSH
connection, local console, sudo capability, repository checkout, credential,
tool, terminal, or previous command is capability context, not authority.

Worker reports are evidence-bearing testimony, not repository truth. Public
repository state must be independently verified before authorizing repository
work.

Do not revive old Worker sessions, checkpoints, terminals, compacted execution
state, browser sessions, temporary scripts, disposable databases, old prompts,
or pending commands as authority.

The Orchestrator session that created this file closes with the enclosing
Orchestrator handoff commit.

The COOPERATOR, Michal, will place this finalized handoff in the repository and
create the enclosing handoff commit.

Expected enclosing Orchestrator handoff subject:

```text
handout
```

The enclosing commit SHA cannot be written here before the commit exists. A
fresh Orchestrator instance must discover and verify it independently.

## 2. Enclosing Handoff Chain To Verify

Immediately before Michal's enclosing `handout` commit, the expected repository
HEAD is the Worker closeout commit:

```text
SHA:
ceaf76c4e6f30450f0b7a9032d82377c4ecf4bfa

subject:
docs: prepare Fedora host readiness handoff

parent:
4a6dee4e7bb6af61d28855823a49fe40177e71ac

changed path:
NEXT_WORKER.md only
```

The latest product implementation boundary before this Orchestrator handoff is:

```text
SHA:
4a6dee4e7bb6af61d28855823a49fe40177e71ac

subject:
fix: align Fedora service boundaries

parent:
614ea684958dcd24a80c6762bcb5b423f191797c
```

The enclosing Orchestrator handoff commit is expected to:

- have exact subject `handout`;
- have `ceaf76c4e6f30450f0b7a9032d82377c4ecf4bfa` as its parent;
- change only `NEXT_ORCHESTRATOR.md`;
- contain this exact file as its committed content.

A fresh Orchestrator must independently verify:

1. repository root and exact remote;
2. branch `main`;
3. local `HEAD`, tracking `origin/main`, and public `refs/heads/main`;
4. the enclosing handout SHA;
5. its exact subject and parent;
6. its exact changed-path count and path;
7. raw public `NEXT_ORCHESTRATOR.md`;
8. Worker closeout `ceaf76c4e6f30450f0b7a9032d82377c4ecf4bfa`;
9. Worker closeout subject, parent, and sole changed path;
10. raw public `NEXT_WORKER.md`;
11. latest implementation boundary
    `4a6dee4e7bb6af61d28855823a49fe40177e71ac`;
12. clean tracked worktree and index.

Use direct Git evidence such as `git ls-remote` for public branch truth. Web
branch pages and raw-content caches have previously lagged behind exact public
commit pages. Do not treat a cached branch page as stronger evidence than
direct Git or exact commit-object verification.

Do not claim the enclosing Orchestrator handoff SHA from this file.

## 3. Human And Communication Context

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

Do not ask Michal to perform routine repository tests, migrations, builds,
commits, pushes, or disposable-environment maintenance when a properly
authorized Worker can perform them.

Host installation and hardening are different: Michal is physically operating
the NUC and wants to learn professional security practice. Guide him one safe,
well-explained step at a time and wait for evidence after each material step.

## 4. Shell And Command UX

Michal's MacBook terminal uses **Fish shell**.

The fresh Orchestrator must not forget this.

Commands intended for the MacBook must be Fish-compatible and labelled
clearly, for example:

```text
[MacBook / fish]
```

Commands intended for the Ubuntu NUC must be labelled separately, for example:

```text
[NUC / remote shell]
```

The Ubuntu account currently appears to use the normal Ubuntu shell, but this
must be verified before relying on shell-specific syntax.

Do not mix local Mac commands and remote NUC commands in one unlabeled block.

Do not give a long block requiring manual typing at the physical console when
SSH copy-and-paste is not yet safely established.

Prefer:

- one small command or tightly related block at a time;
- no ambiguous multiline continuations;
- no hidden stdin redirection during password bootstrap;
- no complex command substitution before the connection state is understood;
- explicit expected output;
- an explanation of why the command is safe;
- a stop condition when output differs.

Never expose or request:

- passwords;
- private-key contents;
- credential values;
- secret-file contents;
- full environment dumps.

Public-key fingerprints may be compared privately with Michal but should not be
committed to the repository.

## 5. Current Repository Truth

```text
project:
FrameNest

repository:
https://github.com/cisarik/framenest.git

normal local path:
/Users/agile/framenest

branch:
main

expected pre-handout Worker closeout:
ceaf76c4e6f30450f0b7a9032d82377c4ecf4bfa

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

expected tracked worktree and index after handout:
clean

active Worker:
none
```

`NEXT_WORKER.md` is a context handoff only. Its recommendation for a Fedora
host readiness audit was correct when written but is now superseded as product
direction by Michal's later decision to use Ubuntu. It grants no task authority.

The current repository contains a corrected repository-native systemd
foundation originally framed around Fedora. Much of the service implementation
is distro-neutral, but the target operating-system decision has changed.

Do not rewrite history to pretend Fedora was never selected. A future bounded
repository task should record the Ubuntu decision as a new superseding ADR and
adapt current documentation truthfully.

## 6. Recent Repository Sequence

Important recent public boundaries include:

```text
c02c4e9c712aa0ae6b6a9d58850bfcc04d9f72f2
fix: position analyze action correctly

0d8de5b4b310a8b68455f11f5759b1a250451b93
docs: prepare Fedora deployment worker handoff

614ea684958dcd24a80c6762bcb5b423f191797c
feat: add Fedora systemd service foundation

4a6dee4e7bb6af61d28855823a49fe40177e71ac
fix: align Fedora service boundaries

ceaf76c4e6f30450f0b7a9032d82377c4ecf4bfa
docs: prepare Fedora host readiness handoff
```

The last commit above is a Worker lifecycle/documentation boundary, not a new
product implementation boundary.

No Worker is active after `ceaf76c4...`.

## 7. Current FrameNest Product Horizon

FrameNest currently has, at repository level:

- a loopback-first FastAPI backend;
- a packaged same-origin vanilla HTML, CSS, and JavaScript frontend;
- SQLite through SQLAlchemy Core;
- Alembic migrations through `0007`;
- a root `./framenest` local development and operator launcher;
- explicit database status and migration commands;
- server-library registration;
- read-only scanning and idempotent import/refresh;
- persistent logical media and physical locations;
- editable title, description, and ordered canonical tags;
- catalog search, repeated-tag AND filtering, Processed semantics, and bounded
  pagination;
- server-owned persistent Gallery preview cache;
- original GIF and MP4 delivery;
- MP4 range delivery and seeking;
- direct inline Gallery playback;
- original-media Details playback;
- identity-only attachment-download backend;
- card-level Open-original behavior;
- server-side AI execution;
- NVIDIA NIM and Vercel AI Gateway adapters;
- operator AI CLI;
- provider-neutral non-secret AI configuration;
- sanitized browser AI status;
- explicit unsaved AI suggestion review followed by explicit Save;
- a repository-native systemd service foundation with a read-only production
  database readiness gate.

Do not claim that the complete remote server/client MVP, Ubuntu deployment,
authentication, upload/synchronization, trusted client-local availability,
admin capability model, desktop shell, Tailscale access, or full production
hardening is finished.

## 8. Frozen Gallery And Details UX

Current Gallery-card UX is accepted and frozen for MVP absent a concrete
usability, accessibility, misleading-state, broken-interaction, privacy, or
security defect.

Accepted card behavior:

- media surface plus title;
- no tag chips under the title;
- no `+N`;
- no empty metadata row;
- no visible Processed status or timestamp;
- no permanent play glyph;
- unused media surface triggers direct inline playback;
- title opens Details;
- compact Edit control at bottom-left;
- compact Open-original control at bottom-right;
- compact Analyze control at top-right when applicable;
- idle Analyze uses `🧠`;
- busy Analyze remains fixed-size and uses the accepted animation;
- overlay activation does not accidentally trigger inline playback.

COOPERATOR-observed evidence includes:

- the final Analyze position was confirmed correct;
- Open original works and preserves the Gallery tab;
- compact overlay controls are accepted;
- the visual phase is closed for MVP.

Current Details behavior includes:

- original media playback;
- clickable green canonical-tag buttons;
- tag activation closes Details and activates the Gallery filter;
- no prominent generic media-kind label;
- description appears once in the compact green panel;
- no prominent Processed panel;
- Edit remains available;
- the metadata editor retains `Analyze by AI`.

Do not reopen broad Gallery or Details polishing during the Ubuntu hardening or
deployment work.

## 9. Corrected Repository Systemd Foundation

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

Production commands:

```text
framenest-production check-database-ready
framenest-production serve
```

Both production operations explicitly disable repository `.env` loading.

Systemd contract includes:

```text
WorkingDirectory=/opt/framenest/current
EnvironmentFile=/etc/framenest/framenest.env
ExecStartPre=/opt/framenest/current/.venv/bin/framenest-production check-database-ready
ExecStart=/opt/framenest/current/.venv/bin/framenest-production serve
KillSignal=SIGTERM
TimeoutStopSec=30s
Restart=on-failure
RestartSec=5s
StandardOutput=journal
StandardError=journal
StateDirectory=framenest
CacheDirectory=framenest
RuntimeDirectory=framenest
```

Repository hardening includes a strict system boundary, private temporary
storage, no-new-privileges, kernel/control-group protections, SUID/SGID
restrictions, personality locking, and empty capability sets.

Production provider-secret integration remains unimplemented.

No real Fedora or Ubuntu host acceptance of this unit has occurred.

## 10. Operating-System Pivot

Michal decided to use Ubuntu rather than install Fedora.

Reasons:

- the real test host is now an Ubuntu NUC;
- the future production VPS is expected to run Ubuntu;
- learning Ubuntu security hardening is directly transferable to that future
  production environment;
- the existing systemd service core can largely remain distro-neutral.

The installed test OS is:

```text
Ubuntu Server 24.04.4 LTS
architecture: amd64
```

This is COOPERATOR-observed physical state and still requires command evidence
from the host.

Future repository adaptation should:

- preserve the useful distro-neutral systemd implementation;
- add a new ADR superseding Fedora as the deployment target;
- preserve ADR-0031 as history rather than silently rewriting the decision;
- add or rename operator documentation for Ubuntu;
- replace Fedora-specific package, SELinux, and firewalld assumptions with
  Ubuntu-specific apt, AppArmor, and UFW/nftables guidance;
- retain loopback-first service behavior;
- retain explicit migrations and the read-only startup gate;
- retain server-only secrets;
- remain compatible with a future Ubuntu VPS.

Python runtime provisioning is an important unresolved decision. FrameNest
currently requires Python 3.13 while Ubuntu 24.04's system Python is not assumed
to satisfy that requirement. Do not casually modify the system Python or choose
an unreviewed third-party package source. Research and explicitly decide a
secure, reproducible isolated Python 3.13 installation strategy before
deployment.

## 11. Physical Ubuntu NUC State

COOPERATOR-observed current host state:

```text
hardware:
Intel NUC6i5SYH

purpose:
test FrameNest server and professional Ubuntu hardening laboratory

hostname:
framenest-nuc

administrator account:
michal

operating system:
Ubuntu Server 24.04.4 LTS

installation:
completed successfully and rebooted

system disk:
approximately 256 GB M.2

installer storage choice:
use entire M.2 disk
LVM disabled
LUKS encryption disabled

secondary disk:
approximately 2 TB SATA

local monitor:
attached and intended to remain useful

OpenSSH server:
installed

first password-based SSH connection from MacBook:
successful

reported remote verification:
whoami -> michal
hostname -> framenest-nuc
```

The 2 TB disk's actual partition, filesystem, mount, and data state have not yet
been verified by trusted command output. Do not assume it is empty merely
because that is the intended use.

The NUC is a test server, but Michal wants production-quality security habits.
The later production server is expected to be an Ubuntu VPS.

The system disk is not encrypted. This was accepted for the test NUC to permit
unattended reboot and simplify recovery. Record the physical-theft trade-off;
do not pretend that software hardening substitutes for encryption at rest.

## 12. Current SSH Bootstrap State

Confirmed:

- password-based SSH from the MacBook to the NUC worked;
- the connection reached the expected account and hostname;
- the NUC is currently on a trusted local network;
- no internet router port-forwarding was authorized.

Not confirmed:

- whether the dedicated Ed25519 key files were successfully created;
- whether the public key was appended to the NUC's
  `~/.ssh/authorized_keys`;
- whether the attempted key-install command completed partially;
- whether the original working SSH session is still open;
- whether a second independent key-only SSH login works;
- whether an SSH alias exists;
- whether password authentication has been changed.

A command resembling the following was attempted from the MacBook and appeared
to hang:

```text
ssh michal@<NUC_LAN_IP> '<remote key-install command>' < <local-public-key>
```

Do not infer success or failure from the apparent hang.

Do not repeat a complex stdin-redirection command.

The immediate operational goal is to recover and verify state without making
another blind mutation.

The fresh Orchestrator should begin by:

1. telling Michal not to close any still-working SSH session;
2. stopping only the visibly hung local command with `Ctrl+C` if it is still
   active;
3. confirming which terminal is local MacBook Fish and which is remote NUC;
4. checking whether the local private and public key files exist without
   displaying private-key content;
5. obtaining the local public-key fingerprint;
6. inspecting only the existence, permissions, and fingerprints of remote
   `authorized_keys`, without printing unrelated key material;
7. determining whether the intended key is already present;
8. installing the public key only if proven absent;
9. testing a new independent key-only connection;
10. preserving the original password session as a recovery channel;
11. disabling password SSH only in a later separate step after successful
    key-only proof and configuration validation.

Do not proceed directly to firewall or SSH lock-down until this gate passes.

Use placeholder:

```text
<NUC_LAN_IP>
```

Do not persist the real LAN address in repository handoffs.

## 13. Security-Hardening Objective

Michal wants a deep, educational, professional infosec hardening process, not a
copy-pasted "hardening script."

The Orchestrator must teach:

- the threat each control addresses;
- what the control does not protect;
- the rollback path;
- the exact verification step;
- how the test NUC differs from the future Ubuntu VPS;
- why a control is selected rather than cargo-culted.

Operational method:

- one material mutation at a time;
- inspect before changing;
- preserve a recovery path;
- validate syntax before reload;
- test a second independent connection before closing the first;
- never combine disk, SSH, firewall, and package changes into one unreviewable
  block;
- do not use `curl | sh`;
- do not run unaudited community hardening scripts;
- do not apply broad sysctl lists without a concrete threat model;
- do not remove packages or services before proving they are unnecessary;
- do not expose SSH or FrameNest through router port forwarding;
- search current official Ubuntu/OpenSSH/systemd documentation for unstable or
  security-sensitive details.

The local monitor and keyboard are a recovery asset, but not a reason to be
careless.

## 14. Recommended Host-Hardening Sequence

Recommended order, subject to evidence:

1. recover and verify SSH public-key state;
2. prove independent key-only login;
3. create a clear MacBook SSH host alias after key proof;
4. capture read-only baseline inventory;
5. verify system time, DNS, network route, listening services, failed units,
   Secure Boot state, firmware state, storage identity, and current update
   state;
6. apply official Ubuntu updates;
7. reboot deliberately when required and prove recovery;
8. harden SSH through a dedicated drop-in:
   - prohibit root login;
   - disable password authentication only after key proof;
   - disable unnecessary forwarding only when it will not break planned use;
   - validate with `sshd -t`;
   - reload rather than blindly restart;
   - test a new session before closing recovery sessions;
9. configure UFW with SSH allowed before enabling it;
10. initially restrict exposure to the trusted LAN where practical;
11. verify unattended security updates;
12. audit and minimize listening services;
13. verify AppArmor status and profiles;
14. configure sensible persistent journald retention and log review;
15. evaluate brute-force protection based on the actual exposure model;
16. verify sudo policy and account hygiene;
17. review BIOS/UEFI, Secure Boot, firmware, and hardware health;
18. prepare the 2 TB media disk safely;
19. establish backup and recovery before important media/catalog state;
20. adapt repository deployment guidance to Ubuntu;
21. deploy FrameNest loopback-only;
22. prove systemd service, migration, readiness, restart, logs, and health;
23. add a minimal graphical administration session only after baseline
    hardening;
24. design production secret integration;
25. add Tailscale in a separate bounded slice;
26. add application authentication and capabilities before multi-user admin
    features.

Do not treat this list as permission to execute all stages at once.

## 15. NUC Storage Direction

Accepted direction:

- the M.2 disk holds Ubuntu, FrameNest application releases, database, preview
  cache, logs/state, and system data;
- the 2 TB SATA disk holds all original media, including GIF and MP4;
- the 2 TB disk should not be mounted under `/home`;
- intended mount root:

```text
/srv/media
```

Candidate media directories:

```text
/srv/media/memes
/srv/media/youtube
/srv/media/movies
```

These directory names are operational organization, not the sole source of
catalog semantics.

Before any destructive storage command:

1. capture `lsblk`, filesystem, mount, model, and size evidence;
2. distinguish the M.2 and SATA devices beyond ambiguous `/dev/sdX` naming;
3. verify whether the 2 TB disk contains data;
4. inspect SMART health when tooling is available;
5. obtain explicit COOPERATOR confirmation of the exact target disk;
6. decide filesystem and encryption policy;
7. create a partition/filesystem only in a separate authorized step;
8. mount by UUID, not volatile device name;
9. validate `/etc/fstab` with a non-destructive mount test before reboot;
10. define root ownership and a least-privilege FrameNest group;
11. preserve read-only source semantics for the FrameNest service unless an
    explicit managed-ingest directory is later designed.

Do not combine partitioning, formatting, fstab editing, permission changes, and
reboot into one command block.

The intended test-server media disk is currently not treated as a backup.
Backup and recovery remain required.

## 16. Local Graphical Administration

Michal does not want the NUC to remain permanently headless.

The NUC has a monitor and should later provide a local browser client for an
administrator.

This does not mean:

- installing a full desktop before baseline hardening;
- making the browser the service supervisor;
- treating loopback as automatic admin authority;
- bypassing authentication for the local browser;
- granting local browser JavaScript filesystem authority.

A later explicit decision must choose between:

- Ubuntu Desktop Minimal;
- a smaller graphical session;
- a kiosk-like browser session;
- another reviewed local-admin approach.

Evaluate:

- attack-surface increase;
- idle resource usage;
- display-manager behavior;
- update burden;
- local session locking;
- browser profile isolation;
- automatic login risk.

The local NUC browser must eventually use the same authenticated FrameNest
server API and capability system as remote clients. Being on the same machine
must not silently confer administrator rights.

## 17. Authoritative Server And Client Model

The central Ubuntu FrameNest server is the authoritative owner of:

- catalog records;
- server media originals;
- canonical title, description, and tags;
- category and language metadata once implemented;
- per-user visibility state;
- upload/ingest state;
- server preview cache;
- authentication and capability decisions.

Ordinary clients:

- request catalog state from the server;
- may explicitly open, stream, or download authorized media;
- must not receive provider secrets;
- must not directly mutate arbitrary server files;
- must not claim trusted local availability without a managed client boundary;
- must not infer admin rights from IP, loopback, hostname, or Tailscale.

The local NUC browser is still a client.

## 18. Upload And Synchronization Product Direction

Michal wants every appropriately authorized client to be able to upload GIF or
MP4 media to the authoritative server.

This is future product direction, not implemented behavior.

Do not model "synchronization" as one vague operation. Separate:

1. **Catalog synchronization**
   - titles;
   - descriptions;
   - canonical tags;
   - categories;
   - language metadata;
   - per-user state.

2. **Media ingest/upload**
   - controlled client-to-server transfer;
   - validation;
   - quarantine;
   - duplicate detection;
   - server-managed final placement;
   - catalog registration.

3. **Client cache/download**
   - explicit local copies;
   - cache ownership;
   - eviction;
   - truthful availability;
   - no automatic server deletion.

A future upload pipeline should include:

- authenticated upload capability;
- size and media-type limits;
- safe filenames;
- temporary quarantine outside the final media root;
- content validation independent of extension;
- duplicate detection;
- atomic publication;
- no path traversal;
- no client-chosen absolute server path;
- clear failure cleanup;
- optional admin review where policy requires it;
- audit evidence without secret or path leakage.

Do not implement upload before authentication/capability architecture is
defined.

## 19. Per-User Trash And Cache Direction

A user's Trash must not be cookie-only authoritative state.

Cookies may identify a session, but the server must persist per-user media
visibility state.

Conceptual future state:

```text
user_id
media_id
state: visible | trashed
trashed_at
```

Expected semantics:

- `Trash` hides media for that user;
- it does not delete the server original;
- it synchronizes across that user's clients;
- it supports Restore;
- it must not be conflated with global delete;
- `Empty Trash` requires explicit product semantics and still must not silently
  destroy server media.

Client cache clearing belongs in:

```text
Settings > General
```

A client may clear only FrameNest-managed cache for that client.

Server preview-cache management is an administrator/operator concern.

Server originals are not cache.

Ordinary browser JavaScript cannot truthfully delete arbitrary files previously
downloaded outside FrameNest-managed storage.

## 20. Administrator Capability Direction

Michal wants administrator operations available in the web UI where
appropriate, especially content administration and synchronization workflows.

Possible future admin UI includes:

- upload/ingest review;
- library refresh;
- sync-job status;
- deletion requests;
- media Retire/Purge review;
- preview regeneration;
- catalog/category/language administration.

Provider credentials, service secrets, operating-system mutation, and sensitive
service operations remain operator boundaries unless a later secure design
explicitly changes that.

Administrator authority must be authenticated and enforced server-side.

Do not infer it from:

- loopback;
- same-machine execution;
- source IP;
- hostname;
- a client-set cookie;
- a visual button style;
- Tailscale membership alone.

Michal likes a distinct animated red-gradient visual language for destructive
or privileged admin controls. That may be used later as UX communication, but
visual styling is never authorization.

One ambiguous `Delete` control must not perform local removal for users and
global destruction for admins.

Keep distinct future operations:

- Remove from this managed client;
- Hide/Trash for this user;
- Request server deletion;
- Retire globally;
- Purge physical originals.

## 21. Category, Language, And Broader Media Direction

FrameNest is expanding beyond a meme-only catalog.

Future first-class categories include:

```text
memes
youtube
movies
```

These should be represented as a dedicated category/facet model, not merely
ordinary semantic tags and not solely inferred from directories.

Current ordinary tags remain semantic descriptors.

Movies may also carry language metadata such as:

```text
english
slovak
czech
```

Language should be modeled explicitly rather than mixed indiscriminately into
semantic tags.

Potential evidence sources, in order of cost and risk:

1. container/audio-track metadata;
2. user editing;
3. bounded audio-language analysis on explicit request;
4. more expensive transcription only when separately authorized.

Do not automatically upload audio to a cloud provider.

Future Gallery/filter UI may expose categories as a dedicated filter group
separate from ordinary tags.

This needs a bounded product/domain task, migration design, API contract,
documentation, and acceptance. It is not authorized by this handoff.

## 22. Playback Direction

Future media UX should support:

- fullscreen for browser-playable video;
- truthful audio-track selection when the browser/container stack supports it;
- explicit download/open-original fallback;
- capability detection rather than optimistic playback;
- no fake Play action when the codec is unsupported.

Subtitle support is not currently required.

Audio-track switching is not assumed trivial across browsers and containers.
A future task must inspect actual media/container/browser support and may need:

- a supported container profile;
- server remuxing;
- transcoding;
- a native player;
- or download-only fallback.

Do not silently transcode originals.

YouTube-related storage is a future product direction. Any downloader or ingest
workflow must be separately designed and should respect the user's rights and
the source platform's applicable rules. No downloader is currently authorized.

## 23. AI And Secret Boundaries

AI provider execution remains server-side only.

Ordinary clients:

- never receive provider credentials;
- never configure provider credentials;
- never call providers directly;
- receive only sanitized status and results.

Safe non-secret selection previously observed:

```text
provider:
nvidia-nim

model:
nvidia/nemotron-3-nano-omni-30b-a3b-reasoning
```

Use placeholders:

```text
<SERVER_AI_CONFIG_PATH>
<SERVICE_SECRET_BOUNDARY>
<PRIVATE_MEMES_ROOT>
```

Never expose:

- credential values or prefixes;
- private-key contents;
- secret-file paths;
- environment contents;
- Authorization headers;
- cookies or session tokens;
- raw provider payloads;
- prompts;
- data URLs;
- private media paths or filenames.

Production Ubuntu provider-secret integration is unresolved and requires a
separate architecture slice.

## 24. Evidence Classification

### Independently Verifiable Repository Facts

Before this Orchestrator handoff:

- Worker closeout commit
  `ceaf76c4e6f30450f0b7a9032d82377c4ecf4bfa` exists;
- its subject is `docs: prepare Fedora host readiness handoff`;
- its parent is `4a6dee4e7bb6af61d28855823a49fe40177e71ac`;
- it changes only `NEXT_WORKER.md`;
- latest product implementation boundary is
  `4a6dee4e7bb6af61d28855823a49fe40177e71ac`;
- current migration head is `0007`;
- highest accepted ADR is ADR-0031.

A fresh Orchestrator must still verify the enclosing `handout` commit and
current public `main`.

### Worker-Observed Evidence

The Fedora service-boundary correction reported:

- focused Fedora tests: `31 passed`;
- relevant persistence/migration tests: `65 passed`;
- full suite: `1332 passed, 3 skipped`;
- `poetry check`: passed;
- JavaScript syntax: passed;
- Fish syntax: passed;
- Python compilation: passed;
- diff checks: passed;
- local/tracking/public equality: reported;
- final worktree and index: reported clean;
- no real host, private media, credential, provider, or frontend access.

### COOPERATOR-Observed Physical Evidence

Michal reported:

- Ubuntu Server 24.04.4 installed successfully on the NUC;
- reboot and local login succeeded;
- hostname is `framenest-nuc`;
- administrator account is `michal`;
- password SSH from the MacBook succeeded;
- remote `whoami` and `hostname` returned expected values;
- a key-install attempt appeared to hang;
- the MacBook shell is Fish;
- the 2 TB SATA disk is intended for all original media;
- the NUC should later have a local graphical browser;
- the test NUC is a learning platform for future Ubuntu production hardening.

### Unresolved Or Unproven

Still unresolved:

- SSH key installation state;
- SSH key-only authentication;
- current open-session state;
- host update state;
- Secure Boot;
- BIOS and firmware;
- RAM and storage health;
- exact disk layout after installation;
- exact 2 TB disk state;
- UFW;
- AppArmor;
- unattended-upgrades;
- listening services;
- Ubuntu Python 3.13 deployment strategy;
- real systemd service installation and operation;
- graphical-session choice;
- production secret integration;
- Tailscale;
- authentication/capabilities;
- upload/synchronization;
- per-user Trash;
- categories/languages;
- fullscreen/audio-track support.

Do not convert unresolved items into confident claims.

## 25. Immediate Next Orchestrator Task

The immediate task belongs to the fresh Orchestrator instance, not a Worker.

```text
Task:
Safely restore and complete SSH public-key bootstrap on the Ubuntu NUC

Task type:
Stepwise host administration with the COOPERATOR

Worker required:
no

Reasoning:
High

Mutation authority:
only the exact small SSH-key step explicitly presented to and executed by
Michal after current state is inspected

Repository authority:
none
```

The fresh Orchestrator should not start with a long inventory block.

The first response should:

1. state restoration status;
2. acknowledge that the MacBook uses Fish;
3. state that no active Worker exists;
4. explain that the previous key-install command has unknown outcome;
5. preserve any existing working SSH session;
6. give one minimal Fish-compatible local check;
7. wait for its result before the next step.

Recommended first local check:

```text
[MacBook / fish]

test -f ~/.ssh/id_ed25519_framenest_nuc
and echo "PRIVATE KEY EXISTS"
or echo "PRIVATE KEY MISSING"

test -f ~/.ssh/id_ed25519_framenest_nuc.pub
and echo "PUBLIC KEY EXISTS"
or echo "PUBLIC KEY MISSING"
```

The fresh Orchestrator should adjust the exact command if current evidence
requires it.

Do not print the private key.

Only after local key existence is known should the Orchestrator inspect remote
authorized-key fingerprints and decide whether installation is needed.

## 26. When To Create A Fresh Worker

No Worker is active now.

Do not create a Worker merely to guide terminal commands on the NUC.

A fresh Worker becomes useful after one of these gates:

### Gate A: host baseline captured

Then a repository-only Worker may implement the Ubuntu documentation/ADR pivot
without touching the host.

### Gate B: Ubuntu repository adaptation completed

Then a separately authorized Worker may perform a read-only host readiness
audit through an exact SSH boundary.

### Gate C: deployment plan accepted

Then a fresh Worker may perform a bounded mutation task on the test NUC.

Recommended first repository Worker task after the host baseline:

```text
Task:
Adapt the repository-native service foundation from Fedora-specific target
documentation to Ubuntu 24.04 and a future Ubuntu VPS

Task type:
Repository implementation, ADR, documentation, and tests only

Reasoning:
High

Host access:
none
```

Expected content:

- new ADR superseding Fedora as current deployment target;
- preserved ADR-0031 history;
- distro-neutral systemd core retained;
- Ubuntu operator guide;
- apt/AppArmor/UFW truth;
- secure Python 3.13 strategy researched and explicitly decided or documented
  as a blocking decision;
- no real host mutation;
- no secrets;
- no Tailscale;
- no authentication;
- no frontend redesign.

A future authoritative prompt must use the exact then-current repository HEAD.

## 27. Recommended Development And Deployment Model

Development remains on the MacBook.

Preferred flow:

```text
MacBook:
edit -> test -> commit -> push verified commit

Ubuntu server:
fetch -> select exact verified commit/release -> prepare isolated environment
-> back up state -> explicit migration -> readiness check -> restart
-> health verification
```

Do not normalize ad hoc production editing on the server.

Do not treat unrestricted `git pull` as the final deployment mechanism.

The repository's `/opt/framenest/current` contract suggests versioned or
otherwise controlled releases with an explicit active release boundary. The
exact release-switch/rollback mechanism remains to be designed.

## 28. Orchestrator Rotation Plan

The Orchestrator instance reading this file is fresh.

The previous Orchestrator instance is closed by the enclosing `handout` commit.

A future Orchestrator rotation is recommended after a coherent operational
boundary, for example:

- SSH key hardening complete;
- baseline inventory captured;
- updates and first reboot accepted;
- UFW and SSH hardening accepted;
- 2 TB media disk safely mounted;
- repository Ubuntu pivot completed;
- before the first real FrameNest deployment mutation.

Do not rotate in the middle of an unverified SSH or disk mutation unless
context safety requires it.

When rotating, create a new repository-native `NEXT_ORCHESTRATOR.md`, commit it
as the sole changed path, and preserve exact host/repository evidence without
including secrets, real IP addresses, key fingerprints, or private media
paths.

## 29. Immediate Non-Goals

The immediate SSH/hardening continuation must not expand into:

- FrameNest deployment;
- formatting the 2 TB disk;
- desktop installation;
- Tailscale;
- router port forwarding;
- public SSH;
- authentication implementation;
- upload/sync implementation;
- per-user Trash;
- admin UI;
- categories/language migration;
- fullscreen/audio-track coding;
- AI provider calls;
- private-media enumeration;
- production secrets;
- broad Gallery changes.

These remain separate bounded decisions.

## 30. Fresh Orchestrator Bootstrap Behavior

The fresh Orchestrator must:

1. state that she is a fresh Orchestrator instance assigned to the persistent
   `ORCHESTRATOR` role;
2. communicate in Slovak using feminine self-reference;
3. verify the enclosing `handout` commit and its exact parent/path;
4. verify Worker closeout `ceaf76c4...`;
5. verify raw public handoff files;
6. verify latest product boundary `4a6dee4...`;
7. recognize that no Worker is active;
8. classify restoration as `PASS`, `PARTIAL`, or `BLOCKED`;
9. not ask Michal to repeat the entire project history;
10. remember that MacBook commands must be Fish-compatible;
11. not assume the SSH key-install command succeeded or failed;
12. start with the smallest read-only key-state check;
13. preserve existing SSH recovery sessions;
14. guide one host mutation at a time;
15. use current official sources for security-sensitive Ubuntu details;
16. delay Worker creation until a repository task actually exists;
17. preserve the Ubuntu pivot and new product directions;
18. avoid public IPs, private paths, fingerprints, secrets, or key contents in
    repository files;
19. never use loopback, IP, same-machine execution, cookies, or Tailscale as
    administrator authorization;
20. keep the visual Gallery/Details phase frozen.

## 31. Closure Summary

```text
project:
FrameNest

expected pre-handout Worker closeout:
ceaf76c4e6f30450f0b7a9032d82377c4ecf4bfa

latest product implementation boundary:
4a6dee4e7bb6af61d28855823a49fe40177e71ac

latest implementation subject:
fix: align Fedora service boundaries

expected Orchestrator handoff subject:
handout

expected Orchestrator handoff parent:
ceaf76c4e6f30450f0b7a9032d82377c4ecf4bfa

expected Orchestrator handoff changed path:
NEXT_ORCHESTRATOR.md only

migration head:
0007

highest accepted ADR:
ADR-0031

active Worker:
none

previous Orchestrator closes with enclosing handout:
yes

immediate operational task:
restore and complete SSH key bootstrap safely

MacBook shell:
Fish

test host:
Intel NUC6i5SYH

installed host OS:
Ubuntu Server 24.04.4 LTS

host name:
framenest-nuc

host role:
test server and security-hardening laboratory

2 TB media mount direction:
/srv/media

repository deployment target direction:
Ubuntu, superseding Fedora for current planning

future production platform:
Ubuntu VPS

Gallery and Details visual direction:
frozen for MVP absent a concrete defect

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

long-term native client direction:
Tauri v2
```

This file restores context and grants no concrete task authority.
