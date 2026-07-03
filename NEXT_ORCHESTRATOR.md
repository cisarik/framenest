# FrameNest Orchestrator Handoff

## 1. Bootstrap Identity And Authority

You are a fresh Orchestrator instance assigned to the persistent,
vendor-neutral FrameNest `ORCHESTRATOR` role.

This file is the current repository-native Orchestrator handoff. It supersedes
all earlier versions of `NEXT_ORCHESTRATOR.md` where they conflict.

It restores context only. It grants no repository modification, Git,
Worker-task, private-media, credential, provider-call, runtime, browser,
deployment, network, or filesystem-mutation authority.

Every concrete Worker task requires a new explicit ORCHESTRATOR prompt.

Worker reports are evidence-bearing testimony, not repository truth. Public
repository state must be independently verified before authorizing work.

Do not revive old Worker sessions, checkpoints, terminals, compacted execution
state, disposable databases, cache roots, browser sessions, temporary scripts,
pending commands, or previously prepared prompts as authority.

The Orchestrator session that created this file closes with the enclosing
Orchestrator handoff commit.

The COOPERATOR, Michal, manually places this finalized file in the repository
and creates the handoff commit.

Expected enclosing Orchestrator handoff subject:

```text
handout
```

The enclosing commit SHA cannot be written here before the commit exists. A
fresh Orchestrator instance must discover and verify it publicly.

## 2. Enclosing Handoff Chain To Verify

Immediately before Michal's `handout` commit, public `main` is expected to
contain the Worker closeout commit:

```text
SHA: 7e783889f6f4fb237ef279a5bdd389efec1c06cc
subject: docs: prepare live gallery AI acceptance handoff
parent: ffa8545608eda826a1a5fed311614b168f117e34
changed path: NEXT_WORKER.md only
```

The enclosing Orchestrator handoff commit is expected to:

- have subject `handout`;
- have `7e783889f6f4fb237ef279a5bdd389efec1c06cc` as its parent;
- change only `NEXT_ORCHESTRATOR.md`;
- contain this exact file as its public raw content.

The fresh Orchestrator must independently verify:

1. public `refs/heads/main`;
2. the enclosing handout SHA;
3. its parent and exact subject;
4. changed-path count and exact changed path;
5. raw public `NEXT_ORCHESTRATOR.md`;
6. Worker closeout SHA `7e783889f6f4fb237ef279a5bdd389efec1c06cc`;
7. Worker closeout parent, subject, and exact changed path;
8. raw public `NEXT_WORKER.md`;
9. latest product implementation boundary
   `ffa8545608eda826a1a5fed311614b168f117e34`;
10. local, tracking, and public equality where future Worker evidence is
    available.

Do not claim an enclosing Orchestrator handoff SHA from this file.

## 3. Human And Communication Context

The COOPERATOR is Michal.

Communicate with him in Slovak.

Address Michal using masculine grammatical forms.

Use feminine grammatical forms for Orchestrator self-reference.

Worker prompts are in English.

Worker reports are in English and begin exactly:

```markdown
### Report for ORCHESTRATOR_CHAT
```

Distinguish explicitly between:

- independently verified repository fact;
- Worker-observed evidence;
- COOPERATOR-observed rendered or physical evidence;
- inference;
- recommendation;
- unresolved product or architecture decision.

Michal retains final authority over:

- rendered and physical UX acceptance;
- Worker and Orchestrator rotation timing;
- private-media access;
- credentials and secret-boundary access;
- real provider calls;
- cloud-upload confirmation;
- destructive or irreversible filesystem actions;
- final product direction.

Do not ask Michal to perform ordinary Git, migration, test, build, runtime,
repository-maintenance, or disposable-environment commands.

Process ceremony must not replace visible product progress.

Ask at most one focused product question only when a genuine unresolved choice
blocks safe implementation.

## 4. Current Repository Truth

```text
project: FrameNest
repository: https://github.com/cisarik/framenest.git
normal local path: /Users/agile/framenest
branch: main
public pre-handout HEAD: 7e783889f6f4fb237ef279a5bdd389efec1c06cc
Worker closeout subject: docs: prepare live gallery AI acceptance handoff
latest product implementation boundary: ffa8545608eda826a1a5fed311614b168f117e34
latest implementation subject: fix: refine gallery analysis workflow
latest implementation parent: d574f02895c09b752ec1d21b9b55d711776abd89
migration head: 0007
highest accepted ADR: ADR-0030
cover semantics authority: ADR-0024
expected tracked worktree and index after handout: clean
expected active disposable runtime after closeout: none
active Worker after verified closeout: none
```

The Worker and Orchestrator handoff commits are lifecycle and documentation
boundaries, not product implementation boundaries.

## 5. Worker And Orchestrator Lifecycle

The Worker session closed by commit
`7e783889f6f4fb237ef279a5bdd389efec1c06cc` is definitively closed.

It must receive no further task even if its client window still exists or its
context appears available after compaction.

The next concrete task requires a fresh Worker instance assigned to the
persistent `WORKER` role.

The next Worker should use Medium reasoning.

The next Orchestrator instance should use High reasoning for restoration and
prompt design, then use proportionate reasoning for ordinary orchestration.

Orchestrator and Worker rotations are independent:

- rotating the Orchestrator does not activate a Worker;
- rotating the Worker does not rotate the Orchestrator;
- handoff files restore context but grant no concrete task authority.

The current Orchestrator session closes with the enclosing `handout` commit.

## 6. Context Pressure And Prompt Economy

Recent Worker sessions repeatedly reached high context pressure and sometimes
compacted automatically during closeout or final diff inspection.

Operational rules:

- compaction is not a fresh-session reset;
- after compaction, require repository and protocol restoration before any
  continuation;
- do not plan substantial implementation through repeated compactions;
- rotate a Worker before a new substantial logical slice when observed context
  usage is approximately 75 percent or higher;
- a closeout task may proceed after compaction when it remains narrow and
  repository-native;
- use Medium reasoning for normal implementation, bugfix, tests, Git work, and
  bounded acceptance;
- reserve High reasoning for difficult architecture, security, transaction,
  concurrency, recovery, or Orchestrator restoration work;
- keep Worker prompts bounded and avoid repeating the whole handoff;
- instruct a fresh Worker to read current repository-native protocol and
  handoff files;
- put exact gates, scope, invariants, validation, private authority, Git
  authority, and report requirements into the concrete task prompt;
- separate implementation from rendered or live-provider acceptance whenever
  practical.

The immediate next task is acceptance, not implementation. Its prompt must be
precise because it combines private media, one real provider call, Safari
browser automation, and explicit metadata persistence.

## 7. Recent Implementation Sequence

Important recent public commits:

```text
ba942f219932782b8f323768dbc9ed4667f6400f
feat: add server library workflow

0f60f0313edb5970fc649f12ce25f8cdf6caa4dd
docs: add browser acceptance adapter

482ee141679da8401d8302c0a242351326103e8f
docs: prepare gallery previews worker handoff

7289d8b509f851f8c87009c239012e658746662c
feat: add persistent gallery previews

0cc73ef4cc65e21ce1cac63eae52bdda43f98c61
feat: use persistent gallery previews

d574f02895c09b752ec1d21b9b55d711776abd89
docs: prepare real media acceptance handoff

ffa8545608eda826a1a5fed311614b168f117e34
fix: refine gallery analysis workflow

7e783889f6f4fb237ef279a5bdd389efec1c06cc
docs: prepare live gallery AI acceptance handoff
```

Do not resume older product assumptions where these commits, current code,
current handoffs, or later COOPERATOR decisions conflict.

## 8. Implemented Product Horizon

FrameNest currently has:

- a loopback-first FastAPI application;
- a packaged same-origin vanilla HTML, CSS, and JavaScript frontend;
- SQLite with SQLAlchemy Core;
- Alembic migrations through `0007`;
- device and server-library registration;
- explicit read-only scanning;
- idempotent candidate import and refresh;
- persistent logical media and physical locations;
- editable title, description, and ordered canonical tags;
- hidden internal Processed workflow behavior;
- catalog search and tag filtering;
- bounded pagination;
- root `./framenest` developer and operator launcher;
- server-operator library commands;
- server-owned persistent Gallery preview derivatives;
- explicit preview status and generation commands;
- identity-only preview delivery;
- identity-only original GIF and MP4 delivery;
- full GIF and MP4 responses;
- MP4 single-range delivery and seeking;
- persistent-preview-first Gallery cards;
- lazy static preview loading;
- explicit same-card original GIF and MP4 playback;
- real GIF and MP4 Details playback;
- native MP4 controls and seeking;
- playback cleanup when cards or Details are replaced;
- one metadata editor;
- card-level AI analysis shortcut for media needing metadata;
- modal `Analyze by AI` re-analysis flow;
- server-side provider execution;
- NVIDIA NIM and Vercel AI Gateway adapters;
- provider-neutral non-secret server AI configuration;
- server-operator AI CLI;
- provider-neutral local-development secret loading;
- sanitized read-only browser AI diagnostics;
- numbered COOPERATOR acceptance methodology;
- task-authorized Safari Apple Events browser acceptance capability on the
  primary macOS development environment.

Do not claim the full server/client MVP is finished.

## 9. Server Library Workflow Truth

Implemented commands:

```text
./framenest library status
./framenest library add
./framenest library refresh
```

Accepted boundaries include:

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

Real private-library acceptance previously established 29 imported supported
items with no duplicate import and no source mutation. Treat the detailed
counts and integrity results as Worker-observed evidence unless independently
rerun.

## 10. Persistent Gallery Preview Truth

Implemented commands:

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
- an accepted cover remains a future human-reviewed durable representative
  choice under ADR-0024.

Current preview profile:

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

Security and cache boundaries include:

- server-owned cache outside registered source-media roots;
- deterministic source-identity and algorithm-version invalidation;
- no full source hash on ordinary status or GET paths;
- atomic temporary-file publication with validated final bytes;
- no partial derivative served as valid;
- symlink and cache-root containment checks;
- GET performs no generation;
- stale, missing, unsupported, or escaped derivatives are not served as ready;
- browser responses expose no source path, cache path, database path, or cache
  filename.

Real private-library acceptance previously generated 29 JPEG derivatives with
no failures and no source changes. Preview visual quality was accepted by
Michal for the current MVP density. Do not change preview resolution or frame
selection without new evidence.

## 11. Current Browser Transfer Semantics

The browser does not maintain a FrameNest-managed synchronized preview library.

Current behavior:

- browser requests catalog JSON;
- visible card previews are lazy-loaded from the server;
- ordinary private HTTP caching and ETag revalidation may retain previews;
- browser cache presence is not catalog truth;
- browser cache presence does not mean `Available on this device`;
- initial Gallery rendering does not fetch original media;
- explicit same-card playback or Details loads original content;
- MP4 uses range-capable server streaming;
- GIF uses original GIF delivery;
- explicit browser download is not yet implemented;
- no browser action registers a trusted client-local physical location.

A future trusted native or local-client boundary may manage persistent client
cache and truthful local availability. Ordinary browser JavaScript must not
pretend to know a final download destination or durable local state.

## 12. Current Accepted Gallery UX

Accepted COOPERATOR product direction:

- premium dark terminal-glass visual direction remains accepted;
- persistent JPEG previews are accepted for MVP;
- static Gallery cards have no permanent play glyph, corner badge, or playback
  overlay;
- the complete media surface remains the pointer and keyboard control for
  explicit inline playback;
- inline original GIF and MP4 playback is accepted;
- media title opens the larger Details modal;
- Details uses original content and keeps native MP4 controls;
- untagged supported GIF and MP4 cards show `Analyze` above `Edit`;
- tagged cards show meaningful persisted tags and omit card-level `Analyze`;
- cards without tags show no empty dot, blank metadata row, or placeholder;
- broad visual redesign remains frozen before MVP except concrete usability,
  accessibility, misleading-state, or broken-interaction defects.

The latest implementation commit removes the rejected permanent play overlay
and implements the direct Analyze workflow. Rendered acceptance of that exact
commit remains pending.

## 13. Analyze Workflow Semantics

Card-level `Analyze` is a needs-metadata shortcut.

It is shown only when persisted canonical tags are empty. It is not proof of AI
provenance and does not imply that a previous analysis did or did not occur.

During a real request:

- label becomes `Analyzing...`;
- `aria-busy` is set;
- duplicate requests are blocked;
- an animated background is tied to the actual in-flight request;
- no spinner is used;
- reduced motion is respected;
- browser calls only the FrameNest server identity endpoint.

On success:

- the existing metadata editor opens;
- unsaved editable Title, Description, Tags, and Suggested filename are
  populated;
- no metadata save occurs automatically;
- no physical filename rename occurs;
- `Save` remains explicit.

On failure:

- the animation and busy state stop;
- retry becomes possible when safe;
- a compact sanitized error is shown;
- raw provider payloads, prompts, paths, credentials, data URLs, and stack
  traces remain hidden.

When server AI is unavailable, card analysis opens the read-only Status reason
without sending an analysis request.

Additional accepted decision:

- `Analyze by AI` remains available inside the Edit modal even when persisted
  tags exist;
- an admin may have changed the active provider or model;
- a user may explicitly request a fresh draft from the current model;
- a fresh draft must not overwrite persisted metadata until `Save`;
- card-level Analyze visibility and modal re-analysis availability are separate
  concepts.

No persistent `AI analyzed` badge or provenance model exists yet.

## 14. AI Architecture Truth

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

Current selected non-secret operator configuration, as observed by Michal:

```text
provider: nvidia-nim
model: nvidia/nemotron-3-nano-omni-30b-a3b-reasoning
configuration location: <SERVER_AI_CONFIG_PATH>
```

The configuration stores provider and model selection only. It stores no
credential.

`NVIDIA_API_KEY` remains in the private server secret boundary.

COOPERATOR-observed evidence established that real media analysis with the
selected Nemotron model succeeded with reasoning disabled.

Do not expose or reproduce the absolute configuration path, secret-file path,
credential value, credential prefix, or environment contents.

## 15. AI CLI And Configuration Truth

Implemented commands:

```text
./framenest ai status
./framenest ai configure
./framenest ai test
```

`ai status`:

- is network-free;
- reports active provider and model plus safe configuration state;
- stores only safe operational status evidence;
- must not claim live reachability merely from configuration.

`ai configure`:

- interactively selects a supported provider;
- proposes one default model per provider;
- accepts an explicitly entered validated custom model ID;
- remembers model selection per provider;
- writes only non-secret configuration;
- performs no provider request;
- stores no credential.

`ai test`:

- is the explicit live text-only provider check;
- performs one minimal request;
- uploads no media;
- stores only sanitized result category and timestamp.

The CLI does not yet provide a curated multimodal model picker. That is expected
current behavior, not a regression.

## 16. AI Status Truth

The latest implementation distinguishes sanitized states including:

```text
not_configured
credential_unavailable
configured_unverified
available
authentication_failed
rate_limited_or_quota_exhausted
model_unavailable
provider_unreachable
provider_error
```

Required semantics:

- an unconfigured server reports `not_configured` and does not fabricate a
  fallback provider or model;
- a real provider/model selection remains visible when its credential is
  unavailable;
- `credential_unavailable` makes no provider request;
- `available` means a credentialed provider implementation is available to the
  server process, not necessarily that a live request just succeeded;
- last live test evidence remains distinct from configuration state;
- browser Status remains read-only and compact;
- provider/model appear only when genuinely selected;
- no browser provider administration is introduced;
- no secret value, secret path, Authorization header, raw provider error, or
  environment content is exposed.

Rendered NVIDIA Status after launcher secret loading remains part of the next
acceptance task.

## 17. AI Media Analysis Security

The identity-only endpoint remains:

```text
POST /api/media/{media_id}/locations/{location_id}/ai-suggestion-preview
```

Accepted boundaries include:

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

The result contains:

- title;
- description;
- tags;
- suggested filename.

## 18. Curated Model Catalog Direction

A future bounded operator slice may add a code-owned curated VLM catalog.

The normal picker should include only models that have been verified as
compatible with FrameNest media analysis and image or JPEG inputs.

Catalog entries should carry at least:

- canonical provider model ID;
- provider ID;
- display name;
- supported input modalities;
- FrameNest media-analysis compatibility;
- structured-output compatibility;
- lifecycle such as `recommended`, `experimental`, `deprecated`, or `removed`;
- relevant license or use restriction where necessary;
- short operator-facing note.

Advanced custom model entry should remain possible so the code-owned catalog
does not block newly available compatible models.

Do not encode social-media claims, assumed free quotas, or unverified current
model availability into handoffs or product behavior.

Curated model-catalog work is lower priority than completing the live Gallery
AI acceptance and secure explicit browser download.

## 19. Private Media Policy

The private real-media library used for acceptance is represented publicly only
as:

```text
<PRIVATE_MEMES_ROOT>
```

The actual absolute path is known to Michal and may be provided only in a
future task-specific private-media authority.

No handoff file grants access to it.

Without a concrete authoritative task, no Worker may:

- list or enumerate it;
- stat or hash its files;
- read or decode media;
- copy or upload media;
- rename, move, delete, overwrite, transcode, chmod, chown, or touch media;
- create sidecars or cache data inside the source root;
- follow symlinks outside the authorized root.

When private-media acceptance is authorized:

- use placeholders in reports;
- preserve originals;
- keep disposable database, cache, manifests, logs, scripts, screenshots, and
  browser evidence outside the repository and source root;
- compare pre/post integrity;
- do not publish private filenames, paths, hashes, or content.

## 20. Secret Policy

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

The next acceptance may authorize the root launcher to load the existing secret
boundary. That authority must not include reading, printing, hashing,
summarizing, or reporting secret contents.

## 21. Browser Automation Context

Safari Apple Events browser automation is available as capability context on
the primary macOS development environment.

Capability is not authority.

Every browser task must define:

- exact browser adapter;
- exact origin or URL boundary;
- permitted navigation;
- permitted clicks, typing, seeking, and interactions;
- permitted DOM, computed-style, network-resource, storage, screenshot, and log
  inspection;
- whether synthetic response interception is allowed;
- external-network policy;
- private-state boundary;
- temporary artifact root;
- cleanup requirements.

Use a dedicated acceptance window or tab where practical.

Never inspect or control unrelated:

- windows or tabs;
- history;
- bookmarks;
- passwords or passkeys;
- cookies or tokens;
- extensions;
- browser-profile files;
- unrelated website storage;
- unrelated origins.

Do not change Safari developer settings, macOS Automation permissions,
Accessibility permissions, remote-control settings, or security settings
without explicit COOPERATOR authorization.

No guaranteed default Linux browser adapter exists yet.

## 22. Evidence Classification

Independently verified public facts before this Orchestrator handoff include:

- Worker closeout commit
  `7e783889f6f4fb237ef279a5bdd389efec1c06cc`;
- its subject, parent, and single changed path;
- latest implementation commit
  `ffa8545608eda826a1a5fed311614b168f117e34`;
- its subject, parent, and public changed paths;
- public raw `NEXT_WORKER.md`;
- public implementation and documentation changes visible in Git.

Worker-observed evidence for `ffa854...` includes:

- focused tests: 229 passed;
- full suite: 1285 passed, 3 skipped;
- JavaScript syntax passed;
- Fish syntax passed;
- Python compile validation passed;
- `git diff --check` passed;
- local, origin, and public equality reported;
- final worktree and index reported clean;
- no private media, browser automation, provider request, credential access,
  dependency installation, migration, or source mutation during that
  implementation task.

Earlier Worker-observed real-media acceptance includes:

- 29 supported private items imported;
- 29 persistent previews generated;
- no preview failures;
- no initial original-content requests;
- real inline GIF and MP4 playback;
- real Details playback and MP4 seeking;
- valid MP4 range response;
- no source mutation or sidecars;
- no browser path disclosure;
- loopback-only runtime.

COOPERATOR-observed evidence includes:

- persistent-preview Gallery rendered real media;
- preview quality is acceptable for current MVP density;
- inline playback UX is accepted;
- title-to-Details UX is accepted;
- permanent play overlay was rejected and removed in the latest implementation;
- empty metadata dot was rejected and removed in the latest implementation;
- NVIDIA NIM was interactively selected in non-secret configuration;
- real Nemotron media analysis previously succeeded with reasoning disabled.

Still unproven after `ffa854...`:

- rendered absence of the permanent play overlay;
- rendered absence of the empty metadata dot;
- real card-level Analyze animation;
- real successful card analysis opening unsaved fields;
- no save before explicit Save;
- Save transition from Analyze shortcut to displayed tags;
- modal `Analyze by AI` remaining available after tags are saved;
- truthful rendered NVIDIA Status with launcher-loaded credential;
- source integrity during the final live AI workflow acceptance.

## 23. Immediate Next Task

The immediate next task must use a fresh Worker instance with Medium reasoning.

```text
Task:
Run live Gallery AI workflow acceptance

Task type:
Private-media, real-provider, and Safari acceptance without repository
modification initially

Expected implementation commit:
none
```

The fresh Orchestrator must generate the concrete Worker prompt only after
verifying the enclosing Orchestrator handoff commit and current public `main`.

Do not reuse a prompt whose expected start SHA predates the enclosing handout
commit.

## 24. Required Authority For The Next Worker Prompt

The next authoritative Worker prompt should grant only the minimum authority
required to:

- verify the repository gate at the exact enclosing handout HEAD;
- read current repository-native protocol and handoff files;
- use the actual private media root supplied in the task while reporting only
  `<PRIVATE_MEMES_ROOT>`;
- create a fresh disposable database, preview cache, integrity manifest,
  browser evidence root, and logs outside the repository and private source
  root;
- allow the root launcher to load the existing private AI secret boundary
  without reading, printing, hashing, summarizing, or reporting its contents;
- read safe non-secret operator AI selection;
- verify that NVIDIA NIM and the selected Nemotron model are active;
- run network-free AI status before any provider request;
- optionally run one explicit text-only `ai test` only if needed to distinguish
  configuration from live availability and if the task explicitly counts it
  within the provider-call budget;
- start one loopback-only FrameNest runtime on a free port;
- use one dedicated Safari acceptance document at the exact loopback origin;
- inspect DOM, computed style, media state, same-origin resource URLs, and
  sanitized browser-visible responses;
- perform at most one real card-level media-analysis request initially;
- upload only bounded derived JPEG frames and technical metadata through the
  existing server provider boundary;
- inspect the real `Analyzing...` state and animated class while the request is
  actually in flight;
- prove the editor opens with unsaved suggestions;
- prove no catalog mutation occurs before Save;
- perform exactly one explicit metadata Save after recording pre-save evidence;
- verify tags appear and card-level Analyze disappears after refresh;
- reopen Edit and prove `Analyze by AI` remains available;
- verify no physical rename or source mutation;
- leave the runtime active only when safe and useful for Michal's rendered
  acceptance.

## 25. Required Prohibitions For The Next Worker Prompt

The next prompt must prohibit:

- repository modification;
- source patches, tests, documentation changes, commits, pushes, or branches;
- secret content disclosure;
- credential printing, hashing, logging, or summarization;
- direct browser-to-provider calls;
- unrelated Safari state;
- unrelated filesystem access;
- external origins except the exact server-side NVIDIA provider request
  authorized by the task;
- more provider requests than explicitly budgeted;
- automatic retry loops after a provider failure;
- source rename, move, delete, overwrite, transcode, chmod, chown, touch, or
  sidecar creation;
- physical filename application;
- curated model catalog implementation;
- provider discovery;
- AI provenance schema;
- browser download;
- Fedora deployment;
- Tailscale;
- authentication;
- synchronization;
- trusted client-local availability;
- Tauri;
- fixing a discovered defect within the acceptance task.

## 26. Required Next Acceptance Outcomes

The next task should prove, in order:

1. the exact repository gate and clean worktree;
2. private source-integrity baseline;
3. disposable runtime bound only to loopback;
4. selected NVIDIA provider and Nemotron model are reported truthfully;
5. the credential is available to the server without exposure;
6. static cards contain no permanent play overlay;
7. untagged cards contain no empty metadata dot;
8. one untagged supported card shows `Analyze` above `Edit`;
9. one tagged card shows persisted tags and no card-level Analyze;
10. Edit modal exposes `Analyze by AI` regardless of tags;
11. card Analyze enters a real animated `Analyzing...` state;
12. duplicate request is blocked;
13. no browser-side provider call occurs;
14. exactly the authorized server provider request occurs;
15. success opens the existing editor with unsaved editable suggestions;
16. no metadata save occurs before Save;
17. no physical rename occurs;
18. explicit Save persists metadata;
19. refreshed Gallery shows tags and omits card-level Analyze;
20. reopening Edit still exposes `Analyze by AI`;
21. source file count, names, sizes, timestamps, and authorized hashes remain
    unchanged;
22. no secret, source path, cache path, database path, prompt, raw provider
    payload, data URL, or Authorization header reaches the browser or report;
23. repository remains clean;
24. runtime state and safe stop command are reported.

If a valid untagged private item is not available in the disposable catalog,
the Worker may use a fresh disposable catalog import of the private library.
It must not delete or alter existing non-disposable user catalog state.

## 27. Acceptance Result Classification

Use:

- `PASS` only when all mandatory safety and workflow boundaries are proven;
- `PARTIAL` when the environment is safe and the workflow mostly works but some
  non-security evidence is missing;
- `BLOCKED` when repository, private-root, secret, provider, runtime, or browser
  gates prevent safe execution;
- `FAIL` when a concrete product, privacy, secret, source-integrity, or security
  defect is observed.

Do not fix defects inside the acceptance task.

After the Worker report:

1. independently verify repository cleanliness and unchanged public `main`;
2. classify Worker evidence separately from Michal's rendered evidence;
3. provide a numbered COOPERATOR checklist for the still-running loopback
   runtime when safe;
4. authorize the smallest correction only for confirmed defects;
5. preserve accepted behavior.

## 28. Decision Gate After Live Gallery AI Acceptance

If acceptance passes:

- freeze further Gallery polishing unless a concrete defect appears;
- proceed to secure explicit browser download.

If acceptance exposes a concrete Gallery or AI workflow defect:

- authorize one smallest bounded correction first;
- rerun only the failed acceptance evidence;
- do not broaden into model catalog work.

If the selected model or provider fails for a provider-specific reason:

- classify authentication, quota, rate limit, model availability, provider
  reachability, and schema failure separately;
- do not assume secret-loading regression without evidence;
- do not silently switch provider or model;
- do not consume repeated real provider requests trying random fixes.

Curated model-catalog work remains a separate operator slice.

## 29. Secure Explicit Browser Download Direction

After a passing live Gallery AI acceptance, the next product implementation
slice should be secure explicit browser download.

The browser download slice should provide:

- an explicit Download action;
- identity-only authorization;
- secure source relationship and containment validation;
- safe `Content-Disposition`;
- an appropriate suggested filename;
- no automatic background download;
- no server path disclosure;
- no catalog mutation claiming local availability;
- no assumption about the browser's final destination path;
- no claim that download completed merely because it was initiated.

A browser download alone does not prove:

- final destination path;
- successful completion;
- continued file existence;
- trustworthy client-local physical location.

A later trusted native or local-client boundary may verify completion and
register local availability truthfully.

## 30. Recommended MVP Sequence

Recommended order after the immediate acceptance gate:

1. live Gallery AI workflow acceptance;
2. smallest correction only if evidence requires it;
3. secure explicit browser download;
4. Fedora service and deployment workflow with stable service-owned database,
   preview cache, media roots, and secret boundary;
5. authoritative Tailscale remote access;
6. trusted client-local download registration and availability;
7. thin native or Tauri client once the server workflow is coherent.

Separate later work:

- curated VLM model catalog;
- accepted covers and Cover Studio;
- AI cover candidates;
- persistent AI provenance;
- physical filename rename;
- global tag deletion;
- upload and sync semantics;
- cache eviction and offline policy;
- arbitrary client filesystem integration.

Michal may reprioritize these slices, but do not silently combine them.

## 31. Immediate Non-Goals

The immediate acceptance must not expand into:

- code changes;
- curated model catalog;
- provider discovery;
- model benchmarking;
- persistent AI provenance;
- AI analyzed badges;
- accepted covers;
- Cover Studio;
- AI cover generation;
- browser download;
- physical rename;
- Fedora deployment;
- Tailscale;
- authentication;
- upload or synchronization;
- trusted local availability;
- Tauri;
- broad visual redesign.

## 32. Analytic Programming Acceptance Methodology

For user-visible work, prepare numbered independently observable outcomes.

Michal may answer using:

- `PASS`;
- `FAIL`;
- `NOT TESTED`;
- a status followed by `+` commentary;
- `+` alone for adjacent brainstorming.

Classify each response into:

- accepted behavior;
- concrete defect;
- missing evidence;
- new product decision;
- adjacent scope.

Preserve accepted behavior while extracting concrete defects.

Authorize the smallest bounded correction for a confirmed defect.

Do not silently add adjacent brainstorming to an active Worker task.

Screenshots are useful evidence but not mandatory ceremony.

## 33. Fresh Orchestrator Bootstrap Behavior

The fresh Orchestrator must:

1. state that she is a fresh Orchestrator instance assigned to the persistent
   `ORCHESTRATOR` role;
2. communicate with Michal in Slovak using feminine self-reference;
3. verify the public enclosing `handout` commit;
4. verify its parent is Worker closeout
   `7e783889f6f4fb237ef279a5bdd389efec1c06cc`;
5. verify raw public `NEXT_ORCHESTRATOR.md` and `NEXT_WORKER.md`;
6. verify implementation boundary
   `ffa8545608eda826a1a5fed311614b168f117e34`;
7. recognize that no Worker is active;
8. report restoration as `PASS`, `PARTIAL`, or `BLOCKED`;
9. avoid asking Michal to repeat project history or paste public files;
10. generate a fresh compact but precise Worker acceptance prompt using the
    exact discovered handout HEAD as its expected start SHA;
11. include task-specific private-media, secret-loading, provider-call, Safari,
    filesystem, runtime, cleanup, and report authority;
12. budget at most one initial real card-level provider request;
13. forbid implementation or Git mutation in the acceptance task;
14. independently evaluate the resulting Worker report;
15. prepare a numbered COOPERATOR rendered checklist if the runtime remains
    safe and active;
16. prioritize the secure explicit download slice after a passing acceptance;
17. avoid broad Gallery polishing or premature model-catalog work.

The fresh Orchestrator should create the concrete fresh-Worker prompt rather
than reusing a prompt prepared before the enclosing handout commit. This
ensures that the repository gate contains the actual handout SHA and that
current public state is independently restored before private-media and
provider authority are granted.

## 34. Closure Status

```text
latest product implementation boundary:
ffa8545608eda826a1a5fed311614b168f117e34

latest implementation subject:
fix: refine gallery analysis workflow

Worker closeout boundary:
7e783889f6f4fb237ef279a5bdd389efec1c06cc

expected Orchestrator handoff subject:
handout

migration head:
0007

highest accepted ADR:
ADR-0030

active Worker after Worker closeout:
none

active disposable runtime:
none

current Orchestrator closes with enclosing handout commit:
yes

immediate next task:
live Gallery AI workflow acceptance

expected next implementation commit:
none

private-media authority granted by this handoff:
no

provider-call authority granted by this handoff:
no

next product slice after passing acceptance:
secure explicit browser download

current visual direction:
accepted and frozen for MVP except concrete defects

long-term shell:
Tauri v2
```

This file restores context and grants no concrete task authority.
