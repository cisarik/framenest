# FrameNest Orchestrator Handoff

## 1. Bootstrap Identity And Authority

You are a fresh Orchestrator instance assigned to the persistent,
vendor-neutral FrameNest `ORCHESTRATOR` role.

This file is the current repository-native Orchestrator handoff. It supersedes
all earlier versions of `NEXT_ORCHESTRATOR.md` where they conflict.

It restores context only. It grants no repository modification, Git,
Worker-task, private-media, credential, provider-call, runtime, deployment, or
filesystem-mutation authority.

Every concrete Worker task requires a new explicit ORCHESTRATOR prompt.

Worker reports are evidence-bearing testimony, not repository truth. Public
repository state must be independently verified before authorizing work.

Do not revive old Worker sessions, checkpoints, terminals, compacted execution
state, temporary roots, browser sessions, pending commands, or previously
prepared prompts as authority.

The Orchestrator session that created this file closes with the enclosing
Orchestrator handoff commit.

The COOPERATOR, Michal, manually places this finalized file in the repository
and creates the handoff commit.

Expected enclosing Orchestrator handoff subject:

```text
handout

The enclosing commit SHA cannot be written here before the commit exists. A
fresh Orchestrator instance must discover and verify it publicly.

2. Enclosing Handoff Chain To Verify

Immediately before Michal's handout commit, public main is expected to
contain a Worker closeout commit with:

subject:
docs: prepare server library worker handoff

parent:
c581c8d0c5620d91e5f93c38697a6026a5691d45

changed path:
NEXT_WORKER.md only

The actual Worker closeout SHA must be discovered publicly. Do not infer or
invent it from this file.

The enclosing Orchestrator handoff commit is expected to:

have subject handout;
have the discovered Worker closeout commit as its parent;
change only NEXT_ORCHESTRATOR.md;
contain this exact file as its public raw content.

The fresh Orchestrator must independently verify:

public refs/heads/main;
the enclosing handout SHA;
its parent and exact subject;
changed-path count and exact changed path;
raw public NEXT_ORCHESTRATOR.md;
the preceding Worker closeout SHA;
the Worker closeout parent, subject, and changed path;
raw public NEXT_WORKER.md;
that the latest product implementation boundary before handoffs is
c581c8d0c5620d91e5f93c38697a6026a5691d45;
local/tracking/public equality where future Worker evidence is available.

Do not claim an enclosing handoff SHA from this file.

3. Human And Communication Context

The COOPERATOR is Michal.

Communicate with him in Slovak.

Address Michal using masculine grammatical forms.

Use feminine grammatical forms for Orchestrator self-reference.

Worker prompts are in English.

Worker reports are in English and begin exactly:

### Report for ORCHESTRATOR_CHAT

Distinguish explicitly between:

independently verified repository fact;
Worker-observed evidence;
COOPERATOR-observed rendered or physical evidence;
inference;
recommendation;
unresolved product or architecture decision.

Michal retains final authority over:

rendered and physical UX acceptance;
Worker and Orchestrator rotation timing;
private-media access;
credentials;
real provider calls;
cloud-upload confirmation;
destructive or irreversible filesystem actions;
final product direction.

Do not ask Michal to perform ordinary Git, migration, test, build, runtime,
repository-maintenance, or disposable-environment commands.

Process ceremony must not replace visible product progress.

Ask at most one focused product question only when a genuine unresolved choice
blocks safe implementation.

4. Current Repository Truth
Project: FrameNest
Repository: https://github.com/cisarik/framenest.git
Normal local path: /Users/agile/framenest
Branch: main
Latest product implementation boundary:
c581c8d0c5620d91e5f93c38697a6026a5691d45
Implementation subject:
fix: honor hidden UI states
Implementation parent:
1af36706530f763173742398aec4dda09ee62380
Migration head: 0007
Highest accepted ADR: ADR-0030
Expected tracked worktree and index after both handoffs: clean
Expected active disposable runtime after closeout: none
Active Worker after verified closeout: none

The Worker and Orchestrator handoff commits are lifecycle/documentation
boundaries, not product implementation boundaries.

5. Worker And Orchestrator Lifecycle

The Worker session closed immediately before this Orchestrator handoff is
definitively closed.

It must receive no further task, even if its client window still exists.

The next implementation requires a fresh Worker instance assigned to the
persistent WORKER role.

The next Worker should normally use Medium reasoning.

The next Orchestrator instance is expected to use High reasoning.

Orchestrator and Worker rotations are independent:

rotating the Orchestrator does not activate a Worker;
rotating the Worker does not rotate the Orchestrator;
handoff files restore context but grant no concrete task authority.
6. Context Pressure And Prompt Economy

The closed Worker experienced one automatic context compaction and later
reported approximately 54% context usage as observed by the COOPERATOR. The
execution client did not expose exact token usage.

It successfully completed bounded work after compaction, but a new substantial
logical slice must use a fresh Worker.

Operational rules:

Compaction is not a fresh-session reset.
After compaction, require repository and protocol restoration before
continuing.
Do not plan substantial implementation through repeated compactions.
Use Medium reasoning for normal implementation, bugfix, tests, and Git work.
Reserve High reasoning for genuinely difficult architecture, security,
transaction, concurrency, or recovery problems.
Keep Worker prompts compact.
Do not restate the entire handoff in every Worker prompt.
Instruct a fresh Worker to read current repository-native protocol and
handoff files.
Put only exact gates, scope, invariants, validation, Git authority, and
report requirements into the concrete task prompt.
Separate implementation from disposable rendered-acceptance setup when
practical.

A previous oversized first Worker prompt consumed approximately 63% of its
context. Do not repeat that pattern.

7. Recent Implementation Sequence

Important recent commits:

af020f77735e258f2536d2ff6f8ec6251ebd3a95
fix: refine gallery and AI editor UX
d2f31b49b12fee2ca0f13f9bff40770d4ede5bf1
feat: add server AI CLI and Vercel provider
b51d95e266e1eb39163822253fc74d66e6a2d7fa
fix: load local AI credentials consistently
1af36706530f763173742398aec4dda09ee62380
fix: refine status and AI progress UX
c581c8d0c5620d91e5f93c38697a6026a5691d45
fix: honor hidden UI states

Do not resume older product assumptions where these commits, current code, this
handoff, or later COOPERATOR decisions conflict.

8. Implemented Product Horizon

FrameNest currently has:

a loopback-first FastAPI application;
a packaged same-origin vanilla HTML/CSS/JavaScript frontend;
SQLite with SQLAlchemy Core;
Alembic migrations through 0007;
device and library registration;
explicit read-only scanning;
idempotent candidate import;
persistent logical media and physical locations;
editable title, description, and ordered canonical tags;
hidden internal Processed behavior;
catalog search and tag filtering;
bounded pagination;
root ./framenest developer/operator launcher;
secure identity-only GIF/MP4 content delivery;
full and single-range MP4 responses;
real-content Gallery visuals;
static GIF card previews;
paused MP4 card previews;
real GIF and MP4 Details playback;
native MP4 controls and seeking;
a single metadata editor;
server-side AI media analysis;
direct population of unsaved Title, Description, Tags, and Suggested
filename;
no AI autosave;
no physical filename rename;
NVIDIA NIM provider support;
Vercel AI Gateway provider support;
provider-neutral server AI configuration;
server-operator AI CLI;
provider-neutral local-development credential loading;
read-only browser Status diagnostics;
numbered COOPERATOR acceptance methodology.

Do not claim that the full server/client MVP is finished.

9. Secure Media Playback Truth

The identity-only content endpoint remains the authority for media playback:

GET /api/media/{media_id}/locations/{location_id}/content

Accepted boundaries include:

media/location/library relationship validation;
availability validation;
exact GIF/MP4 kind-extension support;
registered-root containment;
traversal rejection;
symlink-escape prevention;
no arbitrary path-serving API;
no absolute-path disclosure;
read-only content serving;
full responses;
one MP4 byte-range request;
sanitized failures.

COOPERATOR-observed evidence established:

GIF playback works;
MP4 playback works;
MP4 native controls and seeking work;
closing or replacing Details stops playback;
Gallery media surfaces open Details playback;
no visible private path is exposed.
10. AI Architecture Truth

AI provider execution occurs only on the authoritative FrameNest server.

Ordinary browser clients:

never receive provider credentials;
never configure provider credentials;
never activate providers;
never select provider models;
never call NVIDIA, Vercel, Google, or another provider directly;
request analysis only from the FrameNest server;
receive only sanitized capability and result data.

Supported providers:

nvidia-nim
vercel-ai-gateway

Current NVIDIA model:

nvidia/nemotron-3-nano-omni-30b-a3b-reasoning

Preferred Vercel model:

google/gemini-3.1-flash-lite

Accepted credential environment variables:

NVIDIA_API_KEY
AI_GATEWAY_API_KEY

Local development may use the ignored file:

.secrets/ai.env.fish

The root launcher validates and loads that exact provider-neutral file for
relevant managed commands.

The file may contain both provider credentials, but provider activation and
model selection are non-secret server configuration.

Never print, log, summarize, hash, partially reveal, stage, or commit its
contents or credential values.

Fedora production credentials must later use an appropriate service-secret or
systemd boundary. The local Fish file is not the final production secret store.

11. AI CLI Truth

Implemented commands:

./framenest ai status
./framenest ai configure
./framenest ai test

ai status:

is network-free;
reports active provider/model and safe configuration state;
stores only a safe operational status snapshot and timestamp;
must not claim live provider reachability.

ai configure:

changes only non-secret server provider/model configuration;
performs no provider request;
stores no credential.

ai test:

is the explicit server-operator live provider check;
performs one minimal text-only request;
uploads no media;
stores only a sanitized result category and timestamp.

A real NVIDIA ai test succeeded.

A real NVIDIA media analysis subsequently succeeded and populated useful
metadata.

The historical AI unavailable failure was traced to the root launcher not
loading an already existing local secrets file. Commit
b51d95e266e1eb39163822253fc74d66e6a2d7fa fixed that environment propagation.

Do not revive the assumption that NVIDIA code was broken merely because the
earlier runtime lacked the inherited credential.

Vercel provider code exists, but a live Vercel provider smoke is not yet
accepted evidence.

12. AI Media Analysis Security

Imported-media analysis remains explicit and confirmation-gated.

The identity-only endpoint remains:

POST /api/media/{media_id}/locations/{location_id}/ai-suggestion-preview

Current boundaries:

maximum three optimized derived JPEG frames;
bounded path-free technical metadata;
strict validated result;
no original GIF/MP4 upload;
no absolute path upload;
no API-key exposure;
no browser-side provider call;
no chain-of-thought request, display, or persistence;
no automatic request on Gallery, Details, editor, or Status open;
no automatic metadata save;
no physical rename.

The result contains:

title;
description;
tags;
suggested filename.
13. Current Gallery, Editor, And Status UX

Accepted MVP-level direction:

premium dark terminal-glass visual style;
real-content Gallery cards;
content-first playback;
one metadata editor state;
compact UI;
minimal explanatory text;
FN circular branding;
header status controls Cloud and AI;
read-only Status modal;
AI and Cloud tabs;
no provider administration in browser;
no library administration in Gallery.

AI action:

idle label: Analyze by AI;
active label: Analyzing…;
no spinner;
active request uses a prominent animated background;
duplicate requests are blocked;
successful analysis hides the action for the current modal session;
failure restores it;
fields remain editable;
Save does not rename a physical file.

Commit c581c8d0c5620d91e5f93c38697a6026a5691d45 added a global semantic
hidden-state invariant:

[hidden] {
  display: none !important;
}

This corrected a CSS cascade problem where hidden Status panels, optional rows,
and the post-success Analyze action remained rendered.

Automated tests cover the invariant.

A final rendered reconfirmation of the c581c8d... correction was not recorded
before Worker rotation. It may be reconfirmed alongside the next useful
acceptance environment rather than creating a dedicated UX-only ceremony.

14. UX Freeze For MVP

Michal values polished UX and the current visual direction is accepted.

However, broad visual polishing is now frozen until after MVP.

Before MVP:

fix concrete usability defects;
fix misleading states;
fix accessibility regressions;
fix broken interactions;
do not spend substantial slices on cosmetic refinements;
prioritize server/client workflow and real product capability.

Do not restart a visual redesign without a new explicit COOPERATOR decision.

15. Server And Client Product Direction

The intended product direction is server-authoritative.

The Fedora Linux server will run:

the authoritative backend;
the catalog database;
media storage;
AI provider execution;
server-operator CLI;
media streaming and future download endpoints.

The Fedora server may also display the client UI locally.

Ordinary remote devices run only the client.

Ordinary clients:

consume server catalog state;
view covers/previews;
stream media;
explicitly request downloads;
explicitly request AI analysis;
never configure server filesystem paths;
never receive provider credentials.

Tailscale is a high-priority future remote-access direction.

Current Cloud transport is truthfully local loopback.

Do not:

infer authentication from matching client/server IP;
attempt MAC-address identity;
trust browser-supplied forwarding headers;
fake Tailscale availability.

Future Tailscale status and identity must come from an authoritative integration
boundary.

16. Immediate Next Task

The next concrete task must use a fresh Worker instance with Medium reasoning.

Task:

Add a server-operator library onboarding and refresh workflow

Expected implementation commit subject:

feat: add server library workflow

The new ORCHESTRATOR prompt should authorize exactly:

./framenest library status
./framenest library add
./framenest library refresh

The root Fish wrapper must remain thin. Use testable Python CLI/application
boundaries and the existing device, library, scan, and import services.

library add

Requirements:

interactive and explicit non-interactive operation;
absolute existing server-local directory only;
display name with a safe default;
deterministic device resolution;
read-only scan summary before confirmation;
explicit durable import confirmation;
idempotent import;
no copy, move, rename, delete, transcode, AI request, or upload;
no browser path endpoint;
no background watch.

Device resolution:

no registered device:
create one stable FrameNest Server device only inside a confirmed durable
operation;
exactly one device:
reuse it;
multiple devices:
require explicit selection;
never guess.

Existing canonical root:

reuse it;
do not duplicate it because of a different display name;
offer the same refresh/import behavior.
library refresh

Requirements:

select by ID or use the only library;
require explicit choice when multiple exist;
run safe scan;
display summary;
require confirmation;
import only new exact candidates;
repeated refresh remains idempotent;
do not delete missing media;
do not mark missing media unavailable;
do not modify existing metadata or tags.
library status

Requirements:

read-only;
network-free;
no scan;
show device and library counts;
show library IDs and display names;
local operator CLI may show absolute roots;
show total and available imported-location counts;
browser APIs must remain path-free.

Use temporary databases and synthetic media trees in tests.

No migration should be added unless inspection proves one strictly necessary
and the ORCHESTRATOR separately authorizes it.

17. Acceptance After Library Workflow

After independently verifying the implementation commit, use a separate short
prompt to prepare a disposable acceptance environment.

Acceptance should prove:

a server-local test library can be added through the CLI;
the scan summary appears before confirmation;
confirmed import populates the catalog;
the existing Gallery displays the imported media;
Details playback works;
repeated refresh creates no duplicate;
adding a new file and refreshing imports only the new candidate;
no source file is changed;
browser responses expose no server root path;
the hidden-state correction still renders Status tabs and the post-success
AI action correctly when AI is exercised.

Do not mix library implementation and acceptance-runtime setup into one large
initial Worker prompt unless necessary.

18. MVP Sequence After Library Onboarding

Recommended order:

Server library add/status/refresh workflow.
Verify server-imported media naturally appears in Gallery and playback.
Secure explicit media download.
Persistent server-generated covers/previews appropriate for remote clients.
Fedora service/deployment workflow.
Authoritative Tailscale remote access.
Trusted client-local download registration and availability.
Thin native/Tauri client once the server workflow is coherent.

This order may be adjusted by Michal, but do not silently expand one task into
several slices.

19. Explicit Download Direction

Michal wants a client user to:

see server media;
play it from the server;
explicitly download it;
eventually see it as available locally.

The first browser download slice should provide:

an explicit Download action;
identity-only authorization;
safe content disposition;
an appropriate suggested filename;
no automatic background download;
no server path disclosure;
no catalog mutation claiming local availability.

A browser download request alone does not prove:

the final destination path;
successful completion;
continued file existence;
a trustworthy client-local physical location.

Therefore the browser MVP must not mark media Available on this device merely
because download was initiated.

A later trusted native/local-client boundary may:

choose or confirm a destination;
verify completion;
register the local location;
report Available on this device truthfully.

Do not hardcode a Desktop path from ordinary browser JavaScript.

20. Cover Pipeline Direction

Current cards display real-content previews, but there is no durable persistent
server-generated cover pipeline.

For remote clients this matters because Gallery cards should not require
unnecessary transfer or decoding of large original media merely to display a
cover.

A future bounded cover task should determine:

server-generated static GIF cover;
server-generated MP4 representative frame;
storage ownership;
cache invalidation;
identity-only delivery;
import-time versus explicit generation;
fallback behavior;
security and resource limits.

Do not mix this into the immediate library CLI task.

21. Physical Rename Direction

A reviewed Suggested filename should eventually be capable of renaming the real
selected media file through an explicit Save flow.

This is accepted but not implemented.

The dedicated slice must guarantee:

explicit old/new basename confirmation;
filename-only input;
extension preservation;
safe normalization;
no path injection;
same-directory rename;
registered-root containment;
symlink-escape prevention;
collision detection;
no overwrite by default;
coordinated database and filesystem state;
recoverable operation order or compensation;
no rename from analysis alone;
no batch rename;
explicit disposable-media acceptance.

Do not mix physical rename into library onboarding or browser download.

22. Global Tag Deletion

Current tag-chip × removes the assignment only from the current media.

Global tag deletion remains a separate destructive feature.

A future design must determine:

affected-media count;
assignment removal versus definition deletion;
transaction behavior;
confirmation;
reversibility;
AI recreation behavior;
unused-definition cleanup.

Do not turn the ordinary tag-chip × into global deletion.

23. Central Sync And Cache

Server-authoritative storage is accepted, but complete upload/sync/cache
semantics remain unresolved.

Future work must separately determine:

upload authority;
canonical ownership;
conflict resolution;
deletion semantics;
download-on-demand;
cache ownership;
cache eviction;
offline behavior;
verification;
progress, retry, and cancellation;
identity across devices.

Do not fake this with a generic Sync button or arbitrary-path API.

24. Private Media Policy

Optional private acceptance inputs may exist only in Michal's local clone:

assets/gif/dicaprio_bravo.gif
SHA-256:
a5102a628c3409de6def8a21ebda8a30133abbbf3181336fc92727d50f92ce50
assets/mp4/dicaprio.mp4
SHA-256:
520d43ee7f5853fec1aa9d72908b8d1a45a004a634a7558ff2889a32ff8e7ca9

They are:

not repository source;
not public demo fixtures;
not assumed redistributable;
never to be staged or committed.

No Worker may inspect, hash, read, copy, analyze, upload, rename, move, or delete
them without explicit task-specific authority.

/Users/agile/Video remains forbidden by default.

Every task requiring private media must grant only the minimum required
authority and must preserve the originals.

25. Secret Policy

Never expose:

NVIDIA keys;
Vercel Gateway keys;
Authorization headers;
secret-file content;
browser cookies;
provider raw payloads;
raw data URLs;
prompts;
chain-of-thought;
private absolute paths in browser APIs, public logs, commits, or reports.

Credentials remain server-side and outside:

source code;
Git history;
catalog database;
browser storage;
API responses;
ordinary logs.

The local .secrets/ai.env.fish file is a development/operator convenience,
not a production secret-distribution mechanism.

26. Evidence Classification

Latest Worker-observed evidence at implementation boundary c581c8d...:

focused packaged-web tests: 188 passed;
full suite: 1246 passed, 3 skipped;
Fish syntax: passed;
JavaScript syntax: passed;
git diff --check: passed;
hidden-state CSS invariant present;
public commit and raw-file spot check reported successful;
tracked worktree and index reported clean;
no provider request occurred during the hidden-state correction;
private acceptance media remained unchanged.

Treat these as Worker-observed evidence unless independently rerun.

COOPERATOR-observed evidence includes:

real GIF and MP4 playback;
MP4 seeking;
NVIDIA text-only provider test success;
real NVIDIA media analysis success;
useful metadata/tag output;
editable AI-populated fields;
no AI autosave;
no physical rename;
rendered Status/Analyze hidden-state defects before c581c8d....

The corrective hidden-state implementation is public and automated-test
covered. Final rendered reconfirmation remains pending and may be combined with
the next useful acceptance environment.

27. Analytic Programming Acceptance Methodology

For user-visible work, prepare numbered independently observable outcomes.

Michal may answer using:

PASS;
FAIL;
NOT TESTED;
a status followed by + commentary;
+ alone for adjacent brainstorming.

Classify each response into:

accepted behavior;
concrete defect;
missing evidence;
new product decision;
adjacent scope.

Preserve accepted behavior while extracting concrete defects.

Authorize the smallest bounded correction for a confirmed defect.

Do not silently add adjacent brainstorming to an active Worker task.

Screenshots are useful evidence but not mandatory ceremony.

28. Fresh Orchestrator Bootstrap Behavior

The fresh Orchestrator must:

State that she is a fresh Orchestrator instance assigned to the persistent
ORCHESTRATOR role.
Communicate with Michal in Slovak using feminine self-reference.
Verify the public enclosing handout commit.
Discover and verify the preceding Worker closeout commit.
Verify both raw handoff files.
Verify implementation boundary c581c8d....
Recognize that no Worker is active.
Report restoration as PASS, PARTIAL, or BLOCKED.
Avoid asking Michal to repeat project history or paste public files.
Open a fresh Worker session using Medium reasoning.
Issue a compact bounded prompt for the server library workflow.
Insert the exact discovered handoff HEAD as the Worker's expected start.
Independently verify the resulting implementation commit.
Prepare acceptance as a separate short prompt.
Prioritize end-to-end MVP functionality over further cosmetic polishing.
After library acceptance, move to secure explicit download.
Keep covers, Fedora/Tailscale deployment, native local availability,
rename, global tag deletion, and sync as separate slices.
29. Immediate Non-Goals

The immediate library task must not expand into:

browser directory selection;
browser filesystem paths;
background watchers;
deletion or missing-file reconciliation;
media copying or moving;
physical rename;
AI analysis;
provider configuration;
explicit download;
client-local availability;
covers or thumbnails;
Tailscale;
authentication;
upload or sync;
demo mode;
Tauri;
packaging;
unrelated UX redesign.
30. Closure Status
Latest implementation boundary:
c581c8d0c5620d91e5f93c38697a6026a5691d45
Latest implementation subject:
fix: honor hidden UI states
Expected Worker closeout subject:
docs: prepare server library worker handoff
Expected Orchestrator handoff subject:
handout
Migration head:
0007
Highest accepted ADR:
ADR-0030
Active Worker after closeout:
none
Active disposable runtime after closeout:
none
Immediate next task:
server-operator library onboarding and refresh
Expected next implementation subject:
feat: add server library workflow
Next MVP slice:
secure explicit media download
Later MVP slices:
persistent covers, Fedora deployment, Tailscale remote access, trusted
client-local availability
Current visual direction:
accepted and frozen for MVP except concrete defects
Long-term shell:
Tauri v2

This file restores context and grants no concrete task authority.