# FrameNest Worker Handoff

## 1. Bootstrap Identity And Authority

You are a future fresh Worker instance assigned to the persistent,
vendor-neutral FrameNest `WORKER` role.

This file is the current repository-native Worker handoff. It restores context
only. It grants no repository modification, Git, private-media, credential,
provider-call, runtime, browser, deployment, network, host, SSH, sudo, database
migration, Tailscale, authentication, or filesystem-mutation authority.

Every concrete Worker task requires a new explicit ORCHESTRATOR prompt. Tool
availability, local files, browser adapters, host services, old commands, old
terminals, checkpoints, compactions, local unstaged state, private files,
secrets, and prior prompts are not authority.

The Worker session that creates the enclosing closeout commit closes
permanently with that commit. After verified closeout there is no active
Worker. The Orchestrator session remains active.

Automatic context compaction occurred during the Fedora correction task. It was
not a fresh-session reset. The Worker restored protocol and repository state,
re-ran the repository gate, completed only the authorized correction task, and
stopped before receiving this documentation-only closeout task.

Worker reports must be written in English and begin exactly:

```markdown
### Report for ORCHESTRATOR_CHAT
```

Repository documentation and code remain English unless a future task
explicitly says otherwise.

## 2. Enclosing Closeout Commit To Verify

This file is expected to be committed by the closing Worker with subject:

```text
docs: prepare Fedora host readiness handoff
```

The enclosing closeout SHA cannot be written here before the commit exists. A
future Worker must independently discover and verify it from public
`refs/heads/main`.

Expected enclosing closeout commit properties:

- subject: `docs: prepare Fedora host readiness handoff`;
- parent: `4a6dee4e7bb6af61d28855823a49fe40177e71ac`;
- changed path count: exactly one;
- changed path: `NEXT_WORKER.md`;
- raw public `NEXT_WORKER.md`: this handoff content.

The future Worker must verify, before any task work:

1. repository root and remote;
2. public `refs/heads/main`;
3. enclosing closeout SHA and exact subject;
4. enclosing closeout parent;
5. changed-path count and exact changed path;
6. raw public `NEXT_WORKER.md`;
7. local `HEAD`, `origin/main`, and public `refs/heads/main` equality;
8. clean tracked worktree and index;
9. the latest product implementation boundary below;
10. the future ORCHESTRATOR prompt as the only concrete task authority.

The enclosing closeout commit is a Worker lifecycle and documentation boundary,
not a new product implementation boundary.

## 3. Current Repository Truth

```text
project: FrameNest
repository: https://github.com/cisarik/framenest.git
normal local path: /Users/agile/framenest
branch: main
latest product implementation boundary: 4a6dee4e7bb6af61d28855823a49fe40177e71ac
latest implementation subject: fix: align Fedora service boundaries
latest implementation parent: 614ea684958dcd24a80c6762bcb5b423f191797c
migration head: 0007
highest accepted ADR: ADR-0031
cover semantics authority: ADR-0024
expected tracked worktree and index after closeout: clean
expected local/tracking/public equality after closeout: verified closeout SHA
active Worker after verified closeout: none
```

Do not claim that a real Fedora service is installed, enabled, started, or
accepted. Do not claim knowledge of any runtime outside repository evidence.

`NEXT_ORCHESTRATOR.md` currently contains older lifecycle context. Handoff files
restore session state only; durable product truth comes from public repository
state, tests, ADRs, product documents, and each future task prompt.

## 4. Recent Public Commit Sequence

Important recent public commits:

```text
ba942f219932782b8f323768dbc9ed4667f6400f
feat: add server library workflow

7289d8b509f851f8c87009c239012e658746662c
feat: add persistent gallery previews

68ca36fbf2224f6536cc9901a3f19df577c1b778
fix: finalize compact gallery UX

c02c4e9c712aa0ae6b6a9d58850bfcc04d9f72f2
fix: position analyze action correctly

0d8de5b4b310a8b68455f11f5759b1a250451b93
docs: prepare Fedora deployment worker handoff

614ea684958dcd24a80c6762bcb5b423f191797c
feat: add Fedora systemd service foundation

4a6dee4e7bb6af61d28855823a49fe40177e71ac
fix: align Fedora service boundaries
```

Other recent implemented boundaries include live AI workflow, secure original
content delivery, and identity-only attachment-download behavior. Do not
reproduce the full Git log in future prompts unless a task needs it.

## 5. Implemented Product Horizon

FrameNest currently has:

- a loopback-first FastAPI backend;
- a packaged same-origin vanilla HTML, CSS, and JavaScript frontend;
- SQLite persistence through SQLAlchemy Core;
- Alembic migrations through `0007`;
- a root `./framenest` local development and operator launcher;
- explicit database commands: `framenest-db status` and `framenest-db migrate`;
- device and server-library registration;
- read-only scan, import, and refresh workflows;
- persistent logical media and physical locations;
- editable title, optional description, and ordered canonical tags;
- catalog search, repeated-tag AND filters, Processed semantics, and bounded
  pagination;
- server-owned Gallery preview cache;
- original GIF and MP4 delivery;
- MP4 single-range delivery and seeking;
- direct inline Gallery playback from the media surface;
- Details playback for original GIF and MP4 media;
- identity-only attachment-download backend;
- card-level Open original behavior against the identity-only content endpoint;
- server-side AI execution;
- NVIDIA NIM and Vercel AI Gateway adapters;
- server-operator AI CLI and provider-neutral non-secret configuration;
- sanitized browser AI status;
- explicit unsaved AI suggestion review and explicit Save flow;
- repository-native Fedora systemd service foundation.

Do not claim the complete remote server/client MVP, production deployment,
desktop shell, authentication layer, Tailscale integration, trusted local
availability, arbitrary collection manager, covers, persistent AI Drafts, AI
provenance model, physical rename workflow, or full MVP is finished.

## 6. Frozen Gallery And Details UX

Current Gallery card truth:

- card content is the media surface plus title;
- no tag chips beneath the title;
- no `+N` hidden-tag counter;
- no empty metadata row;
- no visible Processed status or timestamp;
- no permanent play glyph;
- direct unused-surface playback;
- title opens Details;
- Edit is bottom-left;
- Open original is bottom-right;
- Analyze is top-right only when applicable;
- idle Analyze uses `🧠`;
- busy Analyze stays fixed-size with the accepted animation;
- overlay activation does not start inline playback.

COOPERATOR-observed evidence:

- the final Analyze position was confirmed correct;
- Open original works and preserves the Gallery tab;
- compact overlays are accepted;
- Gallery visual presentation is frozen for MVP absent a concrete defect.

Current Details truth:

- Details prioritizes original media playback;
- persisted canonical tags render as clickable green tag buttons;
- clicking a tag activates the Gallery filter and closes Details;
- no prominent generic media-kind label belongs in the main surface;
- description appears once in the compact green panel;
- no prominent Processed panel belongs in the main surface;
- Edit remains available;
- the metadata editor retains Analyze by AI.

Do not reopen visual redesign in the recommended next task.

## 7. Corrected Fedora Service Foundation

The repository-native Fedora foundation is accepted in
[ADR-0031](docs/adr/0031-fedora-systemd-service-foundation.md) and documented
in [docs/FEDORA_SERVICE.md](docs/FEDORA_SERVICE.md). It is service source
material, not proof of a real host deployment.

### Identity

```text
user: framenest
group: framenest
```

This is a dedicated non-root service identity. The repository does not create
that identity on the current host.

### Installed Release Boundary

```text
/opt/framenest/current
/opt/framenest/current/.venv/bin/framenest-production
```

The service does not execute the Fish development launcher, Poetry as a runtime
supervisor, a shell wrapper, a browser-opening command, or reload mode.

### Stable Paths

```text
operator configuration: /etc/framenest/framenest.env
database: /var/lib/framenest/catalog.sqlite3
non-secret AI configuration: /var/lib/framenest/ai/config.json
Gallery preview cache: /var/cache/framenest/gallery-previews
runtime root: /run/framenest
```

`/etc/framenest` is operator managed. It is not a general service-writable
directory. systemd manages state, cache, and runtime directories. Source-media
roots remain external and read-only by default.

### Production Runtime Commands

```text
framenest-production check-database-ready
framenest-production serve
```

Both production operations explicitly disable repository `.env` loading.

The readiness command creates nothing, runs no migration, succeeds only at the
packaged Alembic head, safely rejects missing, empty, behind, unknown/ahead,
relative-path, and inspection-failure states, and provides sanitized
diagnostics.

`serve` uses resolved production settings, delegates to the existing foreground
server runtime, opens no browser, runs no migration, uses no reload, and starts
no additional workers.

### Systemd Contract

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

Security properties include loopback-only default binding, `ProtectSystem=strict`,
`ProtectHome=read-only`, `PrivateTmp=true`, `NoNewPrivileges=true`,
kernel/control-group protections, SUID/SGID restriction, personality locking,
empty capability bounding set, empty ambient capabilities, and no broad
writable source-media path.

`ProtectHome=read-only` remains because a narrowly authorized read-only media
root may be beneath a protected home hierarchy.

### Migration Policy

Production startup performs only read-only readiness. The operator must run the
existing explicit migration command before service startup when needed. The
root local-development launcher retains its existing development migration
behavior.

### Secret Policy

No production provider-secret integration is implemented. systemd loads no
provider-secret `EnvironmentFile`. The committed environment example contains
no credentials. The repository-local development AI environment helper remains
development-only. Production provider calls remain unavailable until a later
authorized service-secret integration exists. systemd credentials or another
approved adapter remain future scope. The service remains useful without AI
credentials.

Never include credential values, prefixes, private secret paths, or environment
contents in prompts, reports, or handoffs.

## 8. Fedora Foundation Limitations

The repository implementation does not prove:

- Fedora package availability;
- actual user/group creation;
- filesystem ownership and permissions;
- systemd unit installation;
- daemon reload;
- successful service activation;
- journald behavior on the target;
- SELinux compatibility;
- firewalld behavior;
- FFmpeg availability;
- database filesystem behavior on the target;
- reboot/restart recovery;
- actual health endpoint operation under systemd;
- private-media permissions;
- backup or restore;
- production secret integration;
- Tailscale;
- authentication.

No real Fedora host acceptance has occurred.

## 9. AI And Private-Media Boundaries

Provider execution is authoritative-server-only. Ordinary clients never receive
credentials. Browser AI Status is sanitized and read-only. Card Analyze opens
unsaved suggestions. Save remains explicit. No physical rename occurs. Modal
re-analysis remains available. No AI provenance model exists.

Safe non-secret selected configuration previously observed:

```text
provider: nvidia-nim
model: nvidia/nemotron-3-nano-omni-30b-a3b-reasoning
```

Use placeholders for private boundaries:

```text
<SERVER_AI_CONFIG_PATH>
<PRIVATE_MEMES_ROOT>
<SERVICE_SECRET_BOUNDARY>
```

No handoff authority permits access to those boundaries. Do not include actual
private paths, filenames, hashes, screenshots, credentials, prompts, payloads,
data URLs, host identifiers, SSH details, cookies, tokens, or provider request
content.

## 10. Download, Local Availability, Delete, And Admin Truth

Card Open original opens identity-only original content. The secure
attachment-download backend remains implemented. Neither browser action proves
final destination, completion, continued local existence, or trusted local
availability. Browser download does not register a client-local physical
location. Ordinary browser JavaScript cannot truthfully delete an arbitrary
downloaded local file later.

Future distinctions remain:

- Remove from this device;
- Hide from my library;
- Request server deletion;
- Global Retire/Purge.

Admin authority must not be inferred merely from loopback, source IP,
same-machine execution, or Tailscale membership.

Removing a tag assignment from an item changes shared server metadata after
Save. It does not delete the global canonical tag definition.

None of these future deletion or admin features is implemented.

## 11. Evidence Classification

### Independently Verified Repository Facts

- latest implementation SHA:
  `4a6dee4e7bb6af61d28855823a49fe40177e71ac`;
- latest implementation subject: `fix: align Fedora service boundaries`;
- latest implementation parent:
  `614ea684958dcd24a80c6762bcb5b423f191797c`;
- latest implementation changed paths:
  `README.md`, `SECURITY.md`, `SERVER.md`,
  `deploy/systemd/framenest.env.example`,
  `deploy/systemd/framenest.service`, `docs/FEDORA_SERVICE.md`,
  `docs/adr/0031-fedora-systemd-service-foundation.md`,
  `src/framenest/infrastructure/runtime/production.py`,
  `tests/contract/test_fedora_systemd_service.py`, and
  `tests/unit/infrastructure/runtime/test_production_runtime.py`;
- current unit and environment contracts match the corrected Fedora foundation;
- current production commands are `check-database-ready` and `serve`;
- ADR-0031 and Fedora operator documentation record the accepted service
  foundation;
- the implementation tasks did not modify handoff files.

### Worker-Observed Evidence

The Fedora correction task reported:

- focused Fedora tests: `31 passed`;
- relevant persistence/migration tests: `65 passed`;
- full suite: `1332 passed, 3 skipped`;
- `poetry check`: passed;
- JavaScript syntax check: passed;
- Fish syntax check: passed;
- Python compilation: passed;
- diff checks: passed;
- local/tracking/public equality verified;
- final worktree and index clean;
- no real host, private media, credentials, provider, frontend, or runtime
  access;
- automatic compaction occurred and restoration was performed.

This closeout handoff does not claim those application tests were rerun.

### COOPERATOR-Observed Evidence

The Cooperator accepted the compact Gallery overlays, confirmed the Analyze
position, confirmed Open original works while preserving the Gallery tab, and
froze the current Gallery and Details visual direction for MVP absent a
concrete defect.

### Unproven Or Unresolved

Real Fedora host properties and operational behavior remain unproven. This
includes packages, service identity, filesystem ownership, systemd
installation, activation, journald behavior, SELinux, firewalld, FFmpeg,
database filesystem behavior, health under systemd, private-media permissions,
backup/restore, production secrets, Tailscale, and authentication.

## 12. Recommended Immediate Next Task

Recommendation only, not authority:

```text
Task: Run a read-only Fedora target readiness audit
Task type: Real-host deployment readiness and risk assessment without host mutation
Worker: fresh Worker instance
Reasoning: High
Expected start: the enclosing Worker closeout commit, discovered after it exists
```

The first real-host task should inspect only after a new ORCHESTRATOR prompt
provides explicit task-specific authority.

It should determine, without mutation:

- exact Fedora release;
- architecture;
- Python 3.13 availability;
- Poetry/runtime-install strategy;
- systemd version and relevant supported directives;
- SELinux mode;
- firewalld state;
- filesystem layout and free space;
- intended release root;
- whether a `framenest` account already exists;
- whether `/etc/framenest`, `/var/lib/framenest`, `/var/cache/framenest`, and
  `/run/framenest` already exist;
- current ownership and permissions;
- FFmpeg/ffprobe availability and versions;
- whether an existing FrameNest service, database, configuration, media root,
  or deployment already exists;
- health of any existing service without exposing credentials or private paths;
- required sudo boundary;
- backup/recovery prerequisites before later mutation.

The audit must not install packages, create users, create or change
directories, copy repository files, migrate a database, start or stop services,
invoke mutating system service operations, change SELinux, change firewalld,
configure Tailscale, inspect credentials, enumerate private media, bind a port,
or deploy FrameNest.

Host identity, hostname, address, SSH identity, sudo authority, and whether the
target is disposable or production remain unresolved and must be supplied or
approved by the COOPERATOR in the future task prompt using placeholders such as
`<FEDORA_TARGET>` and `<FEDORA_SSH_IDENTITY>` as needed.

The read-only audit should produce the exact bounded deployment plan for a
later separate mutation task.

## 13. Recommended Sequence After Readiness Audit

Recommended order, subject to COOPERATOR reprioritization:

1. read-only Fedora target readiness audit;
2. bounded real-host installation and loopback service acceptance;
3. backup and recovery proof;
4. production service-secret integration;
5. Tailscale remote-access slice;
6. authentication and administrator capability boundary;
7. trusted client-local availability;
8. local-copy removal and deletion-request workflow;
9. thin native/Tauri client.

Do not combine these automatically.

## 14. Immediate Non-Goals

This handoff does not authorize real-host mutation, deployment,
provider-secret implementation, Tailscale, authentication, deletion,
synchronization, private-media access, provider requests, browser automation,
further Gallery visual polishing, covers, AI provenance, packaging or RPM work,
or Tauri work.

## 15. Fresh Worker Behavior

A future Worker must:

- identify itself as a fresh Worker instance assigned to the persistent
  `WORKER` role;
- discover and verify the enclosing closeout SHA;
- verify its parent, subject, and sole changed path;
- verify raw public `NEXT_WORKER.md`;
- verify local `HEAD`, `origin/main`, public `main`, and clean state;
- read protocol and handoff files;
- recognize that this handoff grants no task authority;
- use only authority in the future ORCHESTRATOR prompt;
- preserve secret and private-media placeholders;
- report context usage when exposed;
- rotate before a new substantial slice when context pressure approaches
  approximately 75 percent;
- never revive the closed Worker session.

## 16. Closure Summary

```text
latest product implementation boundary: 4a6dee4e7bb6af61d28855823a49fe40177e71ac
latest implementation subject: fix: align Fedora service boundaries
expected closeout subject: docs: prepare Fedora host readiness handoff
expected closeout parent: 4a6dee4e7bb6af61d28855823a49fe40177e71ac
expected changed path: NEXT_WORKER.md
migration head: 0007
highest accepted ADR: ADR-0031
active Worker after closeout: none
current Worker closes with enclosing commit: yes
Orchestrator session remains active: yes
private-media authority: no
credential authority: no
provider-call authority: no
runtime authority: no
real-host authority: no
immediate recommended next task: read-only Fedora target readiness audit
Gallery and Details visual direction: frozen for MVP absent a concrete defect
long-term native shell: Tauri v2
```
