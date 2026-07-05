# FrameNest Worker Handoff

## 1. Bootstrap Identity And Authority

You are a future fresh Worker instance assigned to the persistent,
vendor-neutral FrameNest `WORKER` role.

This file is the current repository-native Worker handoff. It supersedes
earlier versions of `NEXT_WORKER.md` where they conflict.

It restores context only. It grants no repository modification, Git,
private-media, credential, provider-call, runtime, browser, deployment, network,
or filesystem-mutation authority.

Every concrete Worker task requires a new explicit ORCHESTRATOR prompt.
Availability of a tool, local file, secret file, browser adapter, host service,
or previous terminal session is not authority.

Do not revive old Worker sessions, checkpoints, terminals, compacted execution
state, browser sessions, disposable databases, temporary files, prior prompts,
or previously prepared commands as authority.

The Worker session that creates the enclosing closeout commit closes
permanently with that commit. After verified closeout there is no active Worker.

Worker reports must be written in English and begin exactly:

```markdown
### Report for ORCHESTRATOR_CHAT
```

Repository documentation and code remain English unless a future task
explicitly says otherwise.

## 2. Enclosing Closeout Commit To Verify

This file is expected to be committed by the closing Worker with subject:

```text
docs: prepare Fedora deployment worker handoff
```

The enclosing closeout SHA cannot be written here before the commit exists. A
future Worker must independently discover and verify it from public
`refs/heads/main`.

Expected enclosing closeout commit properties:

- subject: `docs: prepare Fedora deployment worker handoff`;
- parent: `c02c4e9c712aa0ae6b6a9d58850bfcc04d9f72f2`;
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
7. implementation boundary `c02c4e9c712aa0ae6b6a9d58850bfcc04d9f72f2`;
8. implementation boundary subject, parent, and changed paths;
9. local `HEAD`, `origin/main`, and public `refs/heads/main` equality;
10. clean tracked worktree and index.

Do not claim the enclosing closeout SHA from this file.

## 3. Repository Gate Verified During Closeout

The closing Worker independently verified these public facts before editing this
file and again after automatic context compaction:

```text
repository root: /Users/agile/framenest
remote: https://github.com/cisarik/framenest.git
branch: main
pre-closeout HEAD: c02c4e9c712aa0ae6b6a9d58850bfcc04d9f72f2
pre-closeout subject: fix: position analyze action correctly
pre-closeout parent: 68ca36fbf2224f6536cc9901a3f19df577c1b778
pre-closeout changed paths:
  src/framenest/adapters/api/web/styles.css
  tests/contract/test_local_web_application.py
local/origin/public equality: verified at c02c4e9c712aa0ae6b6a9d58850bfcc04d9f72f2
tracked worktree and index before handoff edit: clean
```

Automatic context compaction occurred during closeout read-only inspection. It
was not treated as a fresh session. The repository and protocol gate were
restored, the same narrow closeout task was continued, and no additional scope
was adopted.

## 4. Current Repository Truth

```text
project: FrameNest
repository: https://github.com/cisarik/framenest.git
normal local path: /Users/agile/framenest
branch: main
latest product implementation boundary: c02c4e9c712aa0ae6b6a9d58850bfcc04d9f72f2
latest implementation subject: fix: position analyze action correctly
latest implementation parent: 68ca36fbf2224f6536cc9901a3f19df577c1b778
migration head: 0007
highest accepted ADR: ADR-0030
cover semantics authority: ADR-0024
expected tracked worktree and index after closeout: clean
expected active disposable runtime after closeout: none
active Worker after verified closeout: none
```

`NEXT_ORCHESTRATOR.md` was intentionally not modified by this closeout. Its
older lifecycle context must not override later public commits or this
`NEXT_WORKER.md` handoff. Handoff files restore session state; durable product
truth still comes from public repository state, tests, ADRs, product documents,
and fresh task evidence.

## 5. Recent Public Commit Sequence

Important recent public commits:

```text
ba942f219932782b8f323768dbc9ed4667f6400f
feat: add server library workflow

7289d8b509f851f8c87009c239012e658746662c
feat: add persistent gallery previews

0cc73ef4cc65e21ce1cac63eae52bdda43f98c61
feat: use persistent gallery previews

ffa8545608eda826a1a5fed311614b168f117e34
fix: refine gallery analysis workflow

7e783889f6f4fb237ef279a5bdd389efec1c06cc
docs: prepare live gallery AI acceptance handoff

2a0e73e
handout

9255ceb
feat: add secure media downloads

c5782dd
fix: compact gallery media actions

68ca36fbf2224f6536cc9901a3f19df577c1b778
fix: finalize compact gallery UX

c02c4e9c712aa0ae6b6a9d58850bfcc04d9f72f2
fix: position analyze action correctly
```

Short SHAs above are references only. Future Workers must verify exact public
SHAs when a task depends on them.

## 6. Implemented Product Horizon

FrameNest currently has:

- a loopback-first FastAPI application;
- a packaged same-origin vanilla HTML, CSS, and JavaScript frontend;
- SQLite persistence through SQLAlchemy Core;
- Alembic migrations through `0007`;
- a root `./framenest` development/operator launcher;
- local development runtime commands:
  `setup`, `start`, `start --no-open`, `stop`, `restart`, `status`, `open`,
  and `logs`;
- lower-level Poetry script entry points:
  `framenest-server`, `framenest-db`, `framenest-catalog`,
  `framenest-library`, `framenest-dev`, and `framenest-ai`;
- device and server-library registration;
- explicit read-only library scan and idempotent candidate import;
- persistent logical media and physical locations;
- editable title, description, and ordered canonical tags;
- built-in internal `Processed` workflow collection derived from durable tag
  saves;
- catalog search and canonical-tag AND filtering;
- bounded pagination;
- explicit server-library commands:
  `./framenest library status`, `./framenest library add`,
  and `./framenest library refresh`;
- server-owned persistent Gallery preview derivatives;
- explicit preview commands:
  `./framenest previews status` and `./framenest previews generate`;
- identity-only preview delivery;
- identity-only original GIF and MP4 delivery;
- full GIF and MP4 responses;
- MP4 single-range delivery and seeking;
- persistent-preview-first Gallery cards;
- lazy static preview loading;
- explicit same-card original GIF and MP4 playback;
- real Details GIF and MP4 playback;
- native MP4 controls and seeking;
- playback cleanup when cards or Details are replaced;
- a single metadata editor;
- card-level AI analysis shortcut for media needing metadata;
- modal `Analyze by AI` re-analysis flow;
- server-side provider execution;
- NVIDIA NIM and Vercel AI Gateway adapters;
- provider-neutral non-secret server AI configuration;
- server-operator AI CLI;
- provider-neutral local-development secret loading;
- sanitized read-only browser AI diagnostics;
- secure identity-only original media content endpoint;
- secure identity-only browser download endpoint.

Do not claim a completed end-user desktop application, production deployment,
systemd service, authentication layer, Tailscale integration, trusted
client-local availability, Tauri shell, general collection manager, accepted
covers, Cover Studio, persistent AI Drafts, AI provenance schema, physical
rename workflow, upload/sync system, or completed full MVP.

## 7. Current Gallery And Details UX

Current Gallery behavior:

- Gallery cards are compact visual tiles centered on media preview and title.
- Initial Gallery rendering uses persistent static JPEG previews and must not
  request original GIF or MP4 bytes.
- The media surface is the pointer and keyboard control for explicit same-card
  original playback.
- Static cards have no permanent central play glyph, corner badge, playback
  overlay, tag chips, hidden tag counters, empty tag rows, or visible Processed
  state.
- The card title opens Details.
- Card overlay controls are compact and media-overlaid:
  `Analyze by AI` at top right when metadata is needed, `Edit` at bottom left,
  and `Open original` at bottom right.
- `Open original` opens the identity-only original content endpoint in a new
  tab or window. It is not the attachment download endpoint.
- Untagged supported GIF and MP4 cards may show the card-level Analyze
  shortcut.
- Tagged cards show no card-level Analyze shortcut.
- Card-level Analyze is a needs-metadata shortcut, not proof of AI provenance.

Current Details behavior:

- Details prioritizes original playback and the persisted title.
- MP4 playback uses native browser video controls.
- GIF playback uses the original GIF.
- Persisted canonical tags are visible and clickable; clicking a tag activates
  the existing Gallery tag filter while preserving the current text query and
  other active tags where applicable.
- Persisted description appears when present.
- Generic media-kind text and a prominent Processed panel are not part of the
  main Details surface.
- Technical details may still expose technical/internal facts appropriate to
  the current debug/operator surface.

The compact Gallery and Details presentation is currently frozen for MVP except
for concrete usability, accessibility, misleading-state, or broken-interaction
defects.

## 8. Secure Original Content And Download Semantics

Implemented endpoint:

```text
GET /api/media/{media_id}/locations/{location_id}/content
```

Current content semantics:

- identity-only media/location resolution;
- read-only source access;
- path-free browser API;
- original GIF and MP4 delivery;
- MP4 range support for seeking;
- no catalog mutation;
- no source mutation;
- no claim of local client availability.

Implemented endpoint:

```text
GET /api/media/{media_id}/locations/{location_id}/download
```

Current download semantics:

- explicit identity-only browser download;
- attachment response;
- sanitized deterministic suggested filename;
- no server path disclosure;
- no browser destination-path knowledge;
- no claim that download completed merely because it was initiated;
- no catalog mutation claiming local availability.

A browser download alone does not prove final destination path, successful
completion, continued file existence, or a trustworthy client-local physical
location. A later native or trusted local-client boundary is required for that.

## 9. Persistent Gallery Preview Truth

Implemented command:

```text
./framenest previews status
./framenest previews generate
```

Implemented endpoint:

```text
GET /api/media/{media_id}/locations/{location_id}/gallery-preview
```

Preview semantics:

- a Gallery preview derivative is an automatic, reproducible server cache
  artifact;
- it is not an accepted cover;
- it is not a cover candidate;
- it is not catalog metadata;
- it may be deleted and regenerated;
- an accepted cover remains future human-reviewed durable representative media
  under ADR-0024.

Current preview profile remains:

```text
format: JPEG
media type: image/jpeg
algorithm version: gallery-preview-jpeg-v1
frame rule: first deterministic representative frame from the existing
            10 percent, 50 percent, 90 percent preparation rule
maximum long edge: 512 pixels
aspect ratio: preserved
JPEG quality: 82
subsampling: 4:2:0
maximum encoded payload: 524288 bytes
generation: explicit operator action
browser delivery: ETag with private revalidation
```

Do not change preview resolution, frame selection, or cover semantics without a
new explicit task and evidence.

## 10. AI Architecture And Operator Boundaries

AI provider execution occurs only on the authoritative FrameNest server.

Ordinary browser clients:

- never receive provider credentials;
- never configure credentials;
- never activate providers;
- never select models;
- never call NVIDIA, Vercel, Google, or another provider directly;
- request analysis only from the FrameNest server;
- receive only sanitized capability and result data.

Supported provider adapters:

```text
nvidia-nim
vercel-ai-gateway
```

Implemented operator commands:

```text
./framenest ai status
./framenest ai configure
./framenest ai test
```

`ai status` is network-free. `ai configure` writes only non-secret provider and
model selection. `ai test` is the explicit text-only live provider check and
uploads no media.

The root `./framenest` launcher may load `.secrets/ai.env.fish` for local
development commands that need AI environment variables. That file is ignored,
must remain private, and is not the production Fedora secret boundary.

No handoff grants authority to read, print, hash, summarize, validate by
content, or report any secret file or credential. Secret-bearing file names that
appear in IDE tabs are not authority to inspect them.

The selected NVIDIA NIM model and earlier real provider success are
COOPERATOR-observed and prior Worker-observed evidence unless a future task
independently verifies them. Do not silently switch provider or model in a
future task.

## 11. Current AI Media Analysis Semantics

Implemented identity-only endpoint:

```text
POST /api/media/{media_id}/locations/{location_id}/ai-suggestion-preview
```

Accepted boundaries:

- explicit user action;
- explicit cloud-upload confirmation;
- maximum three optimized derived JPEG frames;
- bounded path-free technical metadata;
- strict validated structured result;
- no original GIF or MP4 upload;
- no absolute source path upload;
- no API-key exposure;
- no browser-side provider call;
- no chain-of-thought request, display, or persistence;
- no automatic request on Gallery, Details, editor, or Status open;
- no automatic metadata save;
- no physical rename.

The suggestion result contains editable title, description, tags, and suggested
filename. Suggested filename is not persisted or applied by Save.

Card-level Analyze:

- is visible only when persisted canonical tags are empty and media is
  supported for analysis;
- changes to an actual in-flight busy state during the request;
- blocks duplicate requests;
- opens the existing metadata editor with unsaved suggestions on success;
- performs no metadata save before explicit Save;
- shows sanitized compact failure information on failure.

The editor-level `Analyze by AI` action remains available even after tags are
saved, because an operator may intentionally request a fresh draft from the
current configured model.

No persistent `AI analyzed` badge or provenance model exists yet.

## 12. Server Library Workflow Truth

Implemented commands:

```text
./framenest library status
./framenest library add
./framenest library refresh
```

Accepted workflow boundaries:

- absolute existing server-local directory only;
- read-only scan summary before durable confirmation;
- deterministic device and library resolution;
- stable FrameNest server device creation only inside confirmed durable work;
- existing canonical root reuse;
- idempotent import;
- refresh imports only new exact candidates;
- no source copy, move, rename, delete, transcode, upload, AI request, or
  background watch;
- no missing-file deletion or availability mutation;
- browser APIs remain path-free.

Real private-library acceptance from earlier work remains Worker-observed
evidence unless a future task independently reruns it.

## 13. Fedora Deployment Direction

Fedora deployment is the recommended next product slice after the recent
Gallery/download refinements, but this handoff does not authorize deployment
work.

Current repository truth:

- deployment, systemd, and Tailscale behavior are not provided yet;
- Fedora KDE on an Intel NUC is the later server deployment target;
- local tests, continuous integration, and Fedora deployment must run under
  Python 3.13;
- deployment must install from the committed lock-based Poetry environment;
- production deployment must not depend on developer `.env` files or the local
  `.secrets/ai.env.fish` helper;
- explicit `FRAMENEST_DATABASE_PATH` is expected for persistent deployments;
- public bind addresses must not be the default;
- remote access direction remains Tailscale-only unless explicitly superseded;
- FrameNest must not use Tailscale Funnel in the approved direction;
- normal application startup must not invoke privileged Tailscale provisioning;
- no destructive disk commands belong in roadmap deployment tasks.

Roadmap Phase 11 says Intel NUC Fedora Deployment should deliver Fedora KDE
installation notes, updates, hardware/storage inspection, hardening,
SELinux/firewalld policy, service user, systemd hardening, and backup/recovery
documentation, with documented deployment checks and verified service behavior
on the NUC.

Open deployment decisions likely requiring explicit ORCHESTRATOR shaping:

- whether the next slice is documentation-only, local service scaffolding, or
  real Fedora host acceptance;
- service user name and ownership model;
- production database path, preview cache path, runtime directory, and log
  destination;
- media-root registration and read-only source policy on the NUC;
- systemd unit shape, environment file location, restart policy, and hardening
  directives;
- SELinux and firewalld policy boundaries;
- backup and restore procedure for database, preview cache, configuration, and
  non-secret operational metadata;
- secret boundary for provider credentials in Fedora/systemd;
- whether real hardware inspection is authorized, and if so the exact host and
  command boundary;
- how to keep loopback-first behavior compatible with later Tailscale Serve;
- what constitutes deployment acceptance before Tailscale, authentication, or
  remote access exist.

A future Worker must not infer real host, SSH, sudo, systemd, package-manager,
firewall, SELinux, disk, secret, provider, Tailscale, or deployment authority
from this handoff.

## 14. Recommended Next Worker Task Shape

The next concrete Worker task should be prepared by the Orchestrator after the
enclosing closeout commit is verified publicly.

Recommended first Fedora-deployment slice:

```text
Task:
Prepare the smallest repository implementation or documentation slice needed
for Fedora deployment planning, without touching real Fedora host state unless
the ORCHESTRATOR prompt explicitly grants that authority.
```

Recommended default boundaries:

- use a fresh Worker instance;
- verify the enclosing closeout commit as the expected start SHA;
- read current protocol, product, roadmap, spec, ADR, README, launcher, runtime,
  and persistence configuration files;
- preserve loopback-first behavior by default;
- preserve Python 3.13 and Poetry/lockfile requirements;
- keep secrets out of Git and logs;
- avoid real provider calls;
- avoid private media access;
- avoid browser automation unless specifically required;
- avoid package installation or dependency changes unless explicitly
  authorized;
- avoid destructive filesystem or disk operations;
- avoid sudo/systemctl/firewall/SELinux/Tailscale/SSH unless explicitly
  authorized;
- do not broaden into authentication, Tailscale, Tauri, synchronization, model
  catalog, cover workflows, or broad Gallery polishing.

If a future task is implementation rather than planning, it should specify exact
files or behavioral outcomes, tests, Git authority, and whether commits/pushes
are authorized.

## 15. Private Media Policy

The private real-media library used for acceptance is represented publicly only
as:

```text
<PRIVATE_MEMES_ROOT>
```

No handoff file grants access to it.

Without a concrete authoritative task, no Worker may:

- list or enumerate it;
- stat or hash its files;
- read or decode media;
- copy or upload media;
- rename, move, delete, overwrite, transcode, chmod, chown, or touch media;
- create sidecars or cache data inside the source root;
- follow symlinks outside an authorized root.

When private-media acceptance is explicitly authorized:

- use placeholders in reports;
- preserve originals;
- keep disposable database, cache, manifests, logs, scripts, screenshots, and
  browser evidence outside the repository and source root;
- compare pre/post integrity as authorized;
- do not publish private filenames, paths, hashes, or content.

## 16. Secret Policy

Never expose:

- NVIDIA or Vercel credential values;
- credential prefixes;
- secret-file paths;
- environment contents;
- Authorization headers;
- browser cookies or tokens;
- raw provider payloads;
- raw data URLs;
- prompts;
- chain-of-thought;
- private absolute paths in browser APIs, public logs, commits, screenshots, or
  reports.

Credentials remain server-side and outside:

- source code;
- Git history;
- catalog database;
- browser storage;
- API responses;
- ordinary logs.

Production Fedora secret handling remains future work and must be authorized
explicitly. The developer `.secrets/ai.env.fish` helper is not a production
secret design.

## 17. Browser Automation Context

Safari Apple Events browser automation is known capability context on the
primary macOS development environment. Capability is not authority.

Every browser task must define:

- exact browser adapter;
- exact origin or URL boundary;
- permitted navigation;
- permitted clicks, typing, seeking, and interactions;
- permitted DOM, computed-style, network-resource, storage, screenshot, and
  log inspection;
- whether synthetic response interception is allowed;
- external-network policy;
- private-state boundary;
- temporary artifact root;
- cleanup requirements.

No guaranteed default Linux browser adapter exists. A future Linux or Fedora
task must authorize and document a suitable adapter before requiring browser
evidence there.

## 18. Evidence Classification

Independently verified during this closeout:

- local repository root and origin URL;
- branch `main`;
- local `HEAD` at `c02c4e9c712aa0ae6b6a9d58850bfcc04d9f72f2`;
- `origin/main` and public `refs/heads/main` equality at the same SHA;
- latest implementation subject, parent, and changed paths;
- clean tracked worktree and index before handoff edit;
- migration revision `0007` exists as the current Alembic head in public files;
- highest accepted ADR listed in the repository is ADR-0030;
- Fedora deployment and Tailscale remain planned/deferred in public docs;
- root launcher commands and local AI secret-loading behavior in public code.

Worker-observed evidence from recent implementation reports:

- secure download implementation at `9255ceb`:
  focused tests `236 passed`, targeted processed tests `16 passed`, full suite
  `1297 passed, 3 skipped`, JavaScript syntax, Fish syntax, Python compile
  validation, and `git diff --check` passed;
- compact Gallery media actions implementation at `c5782dd`:
  focused tests `223 passed`, full suite `1298 passed, 3 skipped`, JavaScript
  syntax, Fish syntax, Python compile validation, and `git diff --check`
  passed;
- compact Gallery UX finalization at `68ca36f`:
  web contract tests `198 passed`, focused related suite `206 passed`, full
  suite `1301 passed, 3 skipped`, JavaScript syntax, Fish syntax, Python
  compile validation, and `git diff --check` passed;
- Analyze action positioning fix at `c02c4e9`:
  focused micro test `1 passed`, web contract tests `198 passed`, full suite
  `1301 passed, 3 skipped`, JavaScript syntax, Fish syntax, Python compile
  validation, and `git diff --check` passed;
- those recent tasks reported no private media access, provider call,
  credential inspection, browser runtime, or deployment mutation.

COOPERATOR-observed evidence:

- rendered Gallery feedback found the Analyze action incorrectly placed at the
  upper left after `68ca36f`;
- `c02c4e9` was prepared to correct that specific placement defect;
- persistent preview quality was previously accepted for current MVP density;
- inline playback UX was previously accepted;
- title-to-Details UX was previously accepted;
- NVIDIA NIM selection and real Nemotron media analysis had previously been
  observed with reasoning disabled;
- Worker context usage was observed around 73 percent at the start of this
  closeout.

Unproven after `c02c4e9` unless a future task verifies it:

- rendered top-right Analyze placement in the live browser;
- real Fedora service behavior;
- production database/cache/log/runtime path behavior;
- systemd hardening;
- SELinux/firewalld behavior;
- Tailscale Serve behavior;
- Fedora secret boundary behavior;
- backup and recovery procedure;
- real provider availability at the time of any future acceptance.

## 19. Validation Expectations For Future Tasks

Validation should fit the authorized task. Do not run broad or stateful checks
merely for ceremony when they would require unauthorized secrets, media, browser
state, provider calls, deployment state, package installation, or destructive
operations.

For repository implementation tasks, prefer focused tests first, then broaden
when the blast radius justifies it. Preserve existing accepted behavior and
report skipped or unavailable evidence honestly.

For deployment tasks, distinguish:

- repository-local validation;
- disposable local runtime validation;
- real Fedora host validation;
- COOPERATOR-observed rendered or physical evidence;
- Worker-observed command output;
- public committed state.

Do not conflate a successful local development launcher run with a production
Fedora service acceptance.

## 20. Operational Rules For The Next Worker

Before doing task work, the next Worker must:

1. read the explicit ORCHESTRATOR prompt;
2. read `AGENTS.md`, `AP.md`, `AP_WORKER.md`, `BOOT_WORKER.md`, and current
   `NEXT_WORKER.md`;
3. verify the exact expected start SHA from public `main`;
4. verify raw public handoff files when required;
5. verify local, tracking, and public equality;
6. verify tracked worktree and index cleanliness unless the prompt authorizes
   working with known dirt;
7. classify facts as independently verified, Worker-observed,
   COOPERATOR-observed, inference, recommendation, or unresolved decision;
8. stay inside the concrete task boundary.

The Worker must not:

- modify files outside the authorized scope;
- perform Git writes without explicit Git authority;
- create branches without explicit authority;
- pull, reset, clean, stash, switch branches, or repair history unless
  explicitly authorized;
- install dependencies without explicit authority;
- access private media or secrets without explicit authority;
- perform provider calls without explicit authority and call budget;
- run browser automation without explicit authority;
- perform deployment, package-manager, systemd, firewall, SELinux, Tailscale,
  SSH, sudo, disk, or network mutations without explicit authority;
- fix newly discovered defects inside an acceptance-only task.

If automatic context compaction occurs, do not treat it as a fresh task reset.
Restore repository and protocol context, rerun the relevant gate, continue only
if the current task remains narrow and safe, and record compaction in the final
report when relevant.

## 21. Closure Status

```text
latest product implementation boundary:
c02c4e9c712aa0ae6b6a9d58850bfcc04d9f72f2

latest implementation subject:
fix: position analyze action correctly

expected Worker closeout subject:
docs: prepare Fedora deployment worker handoff

migration head:
0007

highest accepted ADR:
ADR-0030

active Worker after verified closeout:
none

active disposable runtime:
none

private-media authority granted by this handoff:
no

credential or secret authority granted by this handoff:
no

provider-call authority granted by this handoff:
no

deployment authority granted by this handoff:
no

recommended next product slice:
Fedora deployment planning or the smallest explicitly authorized Fedora
deployment implementation step

current visual direction:
accepted and frozen for MVP except concrete defects

long-term desktop shell:
Tauri v2
```

This file restores context and grants no concrete task authority.
