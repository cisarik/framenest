# FrameNest Worker Handoff

## 1. Identity And Authority

A future Worker must be a fresh Worker instance assigned to the persistent,
vendor-neutral FrameNest `WORKER` role.

The current Worker session closes with the enclosing closeout commit. After
that commit is verified and pushed, this concrete Worker instance must not be
reused and no active Worker remains.

This file restores context only. It grants no task, Git, repository mutation,
runtime, browser, private-media, credential, provider-call, network,
deployment, or filesystem-mutation authority. Every future concrete task
requires a new authoritative ORCHESTRATOR prompt.

Expected enclosing closeout commit:

```text
subject: docs: prepare real media acceptance handoff
parent: 0cc73ef4cc65e21ce1cac63eae52bdda43f98c61
changed path: NEXT_WORKER.md only
effect: closes this concrete Worker session
```

The enclosing commit SHA is intentionally not recorded here because the commit
does not exist until this file is committed.

## 2. Repository Truth

```text
repository: https://github.com/cisarik/framenest.git
normal local path: /Users/agile/framenest
branch: main
pre-closeout HEAD: 0cc73ef4cc65e21ce1cac63eae52bdda43f98c61
latest product implementation boundary: 0cc73ef4cc65e21ce1cac63eae52bdda43f98c61
implementation subject: feat: use persistent gallery previews
persistent preview backend boundary: 7289d8b509f851f8c87009c239012e658746662c
library workflow boundary: ba942f219932782b8f323768dbc9ed4667f6400f
migration head: 0007
highest accepted ADR: ADR-0030
cover semantics authority: ADR-0024
```

## 3. Worker Lifecycle

COOPERATOR-observed context usage was approximately 89% before closeout.
Automatic context compaction did not occur during the Gallery integration task.
Exact token usage was not exposed by the execution client.

If compaction occurs during closeout, it is reduced execution context only. It
does not create a fresh Worker session and does not authorize implementation or
new task intake.

This Worker must not be reused after the enclosing commit. The next task
requires a fresh Worker instance using Medium reasoning.

## 4. Implemented End-To-End Horizon

FrameNest now supports:

- server-operator library onboarding:
  - `./framenest library status`
  - `./framenest library add`
  - `./framenest library refresh`
- confirmed read-only scan before durable import;
- idempotent import and refresh;
- persistent gallery preview operator workflow:
  - `./framenest previews status`
  - `./framenest previews generate`
- server-owned preview cache outside registered source-media roots;
- deterministic source-identity and algorithm-version invalidation;
- atomic preview publication;
- identity-only preview delivery:
  - `GET /api/media/{media_id}/locations/{location_id}/gallery-preview`
- identity-only original delivery:
  - `GET /api/media/{media_id}/locations/{location_id}/content`
- full GIF and MP4 responses;
- MP4 range streaming;
- persistent-preview-first Gallery cards;
- lazy preview loading;
- stable no-original fallback;
- explicit same-card original GIF/MP4 playback;
- Details original playback;
- MP4 native controls and seeking;
- cleanup when playback, cards, filters, pagination, or Details are replaced;
- path-free browser APIs.

Do not claim browser download, client-local availability, offline
synchronization, Fedora deployment, Tailscale access, authentication, or a
completed MVP.

## 5. Preview Versus Cover Terminology

Accepted terminology:

- `gallery preview derivative` means an automatic reproducible server cache
  artifact;
- `accepted cover` means a future human-reviewed durable representative
  choice;
- automatic previews are not cover candidates and are not accepted covers;
- do not globally rename legitimate cover concepts;
- code currently uses the correct `gallery_preview` terminology;
- `COVER_PIPELINE.md` remains the umbrella document for previews, future
  accepted covers, candidates, and Cover Studio.

Known non-blocking documentation drift:

- `COVER_PIPELINE.md` still lists Gallery UI consumption as deferred;
- Gallery UI consumption was implemented at `0cc73ef...`;
- a later bounded documentation update should correct that statement;
- this does not block real-media acceptance.

## 6. Current Preview V1 Contract

```text
format: JPEG
media type: image/jpeg
algorithm version: gallery-preview-jpeg-v1
frame rule: first deterministic representative frame from the existing 10%, 50%, 90% preparation rule, currently approximately the 10% frame
maximum long edge: 512 pixels
aspect ratio: preserved
JPEG quality: 82
subsampling: 4:2:0
maximum encoded payload: 524288 bytes
generation: explicit operator action
browser delivery: ETag with private revalidation
```

Real-media acceptance must evaluate:

- Retina sharpness;
- representative-frame usefulness;
- black or title-card frames;
- vertical-media presentation;
- generation speed;
- derivative byte sizes;
- fallback behavior;
- explicit play and Details behavior.

Do not prescribe a resolution or frame-selection change before acceptance
evidence.

## 7. Current Client/Server Transfer Semantics

The browser does not yet maintain a FrameNest-managed synchronized preview
library. It requests visible previews lazily and may retain them through
ordinary private HTTP caching and ETag revalidation.

Browser cache presence is not catalog truth and does not mean `Available on
this device`. Initial Gallery rendering does not fetch originals. Explicit
card playback or Details loads original content. MP4 supports range streaming.
GIF uses original GIF delivery.

Explicit browser download is not implemented. No browser action currently
registers a trusted client-local physical location.

## 8. Evidence Classification

Worker-observed evidence:

- persistent-preview backend focused tests: 21 passed;
- backend full suite: 1279 passed, 3 skipped;
- Gallery integration focused tests: 214 passed;
- latest full suite: 1280 passed, 3 skipped;
- JavaScript syntax passed;
- Fish syntax passed;
- `git diff --check` passed;
- local/origin/public equality was reported;
- final tracked worktree/index was reported clean;
- no private-media, browser, provider, credential, dependency-installation, or
  source-mutation access occurred in the two implementation tasks.

Not yet proven:

- real preview quality against the COOPERATOR's MEMEs corpus;
- full-library generation performance;
- real Safari rendering of the new persistent-preview Gallery;
- real GIF/MP4 playback regression after `0cc73ef...`;
- private source-file integrity during real-library acceptance.

## 9. Private Media Placeholder

The private MEMEs root must be represented publicly only as:

```text
<PRIVATE_MEMES_ROOT>
```

The actual private path is known to the COOPERATOR and ORCHESTRATOR. It will be
supplied only in the next task-specific private-media authority. This handoff
file grants no access to it.

Reports, public commits, browser responses, screenshots, and logs must use
`<PRIVATE_MEMES_ROOT>` rather than the absolute path. Do not repeat other
private absolute media paths in handoff files or public artifacts.

## 10. Immediate Next Task

```text
Task:
Run real server-library and Safari acceptance using <PRIVATE_MEMES_ROOT>

Task type:
Acceptance and evidence collection, initially without repository modification

Expected implementation commit:
none
```

The next task must use a fresh Worker instance.

The future authoritative prompt should grant only the minimum private-media
access required to:

- identify the root and enumerate candidate GIF/MP4 files;
- perform the existing read-only library scan;
- import through the confirmed library workflow;
- read/decode source media locally for preview generation and playback;
- create preview derivatives only in the configured server-owned cache outside
  the source root;
- collect a sanitized pre/post integrity manifest;
- run a loopback-only FrameNest acceptance runtime;
- use the authorized Safari Apple Events adapter only against the exact
  loopback origin;
- inspect Gallery DOM, rendered preview state, playback, network paths, and
  sanitized API responses;
- leave the runtime active only when explicitly requested for COOPERATOR
  acceptance.

The future prompt must prohibit:

- AI or provider calls;
- uploads;
- external application network access;
- source rename, move, delete, overwrite, transcode, metadata write, or
  sidecar creation;
- arbitrary filesystem access outside authorized repository, temporary, cache,
  database, and private-library roots;
- unrelated Safari tabs, windows, profiles, cookies, credentials, history,
  bookmarks, extensions, or storage;
- publishing private filenames or the absolute media root in reports or
  commits.

The acceptance should prove:

1. initial library status;
2. interactive add with scan summary before confirmation;
3. catalog import counts;
4. preview status before generation;
5. explicit preview generation in bounded batches until the planned corpus is
   ready or every failure is classified;
6. no duplicate import or derivative creation after repeat refresh/prewarm;
7. Gallery cards display server JPEG previews without initial original
   requests;
8. representative preview sharpness and usefulness;
9. explicit GIF and MP4 in-card playback;
10. Details playback, controls, seeking, and cleanup;
11. MP4 range requests;
12. no browser path disclosure;
13. no source mutation or sidecar creation;
14. sanitized preview byte-size and generation-time statistics;
15. a numbered COOPERATOR checklist for visual acceptance.

If the corpus is unexpectedly large, generation must remain bounded and
transparent. Do not invent progress or silently process an unbounded set.

## 11. Acceptance Decision Gate

If real acceptance passes, the next implementation slice is secure explicit
browser download.

If preview quality fails, authorize the smallest evidence-driven preview
correction first. Possible future corrections include resolution variants or
deterministic selection among existing representative frames. Do not implement
those corrections before evidence.

Accepted covers, Cover Studio, AI cover generation, sync, native local
availability, Fedora deployment, and Tailscale remain separate slices.

## 12. Browser Automation

Safari Apple Events is available as capability context on the primary macOS
development environment. Capability is not task authority.

Exact origin, navigation, JavaScript, interactions, interception, screenshots,
logs, external-network policy, private-state boundary, temporary artifacts, and
cleanup must be authorized. Unrelated browser state must never be inspected.

No guaranteed Linux browser adapter exists yet.

## 13. Closure Summary

```text
pre-closeout HEAD: 0cc73ef4cc65e21ce1cac63eae52bdda43f98c61
latest implementation boundary: 0cc73ef4cc65e21ce1cac63eae52bdda43f98c61
migration head: 0007
current Worker closes with enclosing commit: yes
active Worker afterward: none
active disposable runtime: none
immediate next task: real server-library and Safari acceptance
private media authority granted by this handoff: no
actual private root recorded publicly: no
Orchestrator session: remains active
```
