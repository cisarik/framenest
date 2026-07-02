# FrameNest Worker Handoff

## 1. Identity And Authority

A future Worker must be a fresh Worker instance assigned to the persistent,
vendor-neutral FrameNest `WORKER` role.

The current Worker session closes with the enclosing handoff commit. After that
commit is verified and pushed, this concrete Worker instance must not be reused
and no active Worker remains.

This file restores context only. It grants no task, Git, repository mutation,
runtime, browser, private-media, credential, provider-call, deployment, or
filesystem-mutation authority.

Every future concrete task requires a new authoritative ORCHESTRATOR prompt.

Expected enclosing handoff commit:

```text
subject: docs: prepare gallery previews worker handoff
parent: 0f60f0313edb5970fc649f12ce25f8cdf6caa4dd
changed path: NEXT_WORKER.md only
effect: closes this concrete Worker session
```

The enclosing handoff commit SHA cannot be recorded before the commit exists. A
future Worker must discover and verify it from public repository state.

## 2. Repository Truth

```text
repository: https://github.com/cisarik/framenest.git
normal local path: /Users/agile/framenest
branch: main
current pre-closeout HEAD: 0f60f0313edb5970fc649f12ce25f8cdf6caa4dd
latest product implementation boundary: ba942f219932782b8f323768dbc9ed4667f6400f
implementation subject: feat: add server library workflow
migration head: 0007
highest accepted ADR: ADR-0030
relevant accepted cover architecture: ADR-0024
```

`0f60f0313edb5970fc649f12ce25f8cdf6caa4dd` is the latest documentation and
protocol boundary. The latest product implementation boundary remains
`ba942f219932782b8f323768dbc9ed4667f6400f`.

## 3. Worker Lifecycle

COOPERATOR-observed context usage was approximately 87% before closeout. Exact
token usage was not exposed by the execution client.

This Worker session must not be reused after closeout. No active Worker remains
after the verified push. The next implementation requires a fresh Worker
instance using Medium reasoning.

## 4. Recent Completed Work

Server-operator library onboarding and refresh was implemented at
`ba942f219932782b8f323768dbc9ed4667f6400f`.

Root commands now exist:

```text
./framenest library status
./framenest library add
./framenest library refresh
```

Implementation acceptance used synthetic GIF/MP4 media and real Safari browser
evidence. Gallery display, GIF playback, MP4 playback, native controls, seeking,
replacement cleanup, source immutability, and path-free browser responses were
Worker-observed. AI success UI was tested only through explicitly labelled
synthetic browser response interception. No real provider request occurred in
that acceptance. The disposable runtime was stopped.

Browser-automation protocol was added to canonical AP commit
`159adcf910abe56cb67ef0ddb47d946b3e030a0f`. FrameNest synchronized that
capability and documented the macOS Safari Apple Events adapter at
`0f60f0313edb5970fc649f12ce25f8cdf6caa4dd`.

Test counts, browser observations, runtime cleanup, and local/public equality in
this section are Worker-observed evidence from reports unless independently
rerun.

## 5. Current Server Library And Streaming Truth

FrameNest currently supports:

- absolute server-local library onboarding;
- confirmed read-only scan followed by durable idempotent import;
- deterministic device and library resolution;
- refresh importing only new exact candidates;
- Gallery display of imported GIF and MP4 media;
- identity-only media delivery:
  `GET /api/media/{media_id}/locations/{location_id}/content`;
- full GIF/MP4 responses;
- MP4 byte-range requests;
- GIF and MP4 Details playback;
- native MP4 controls and seeking;
- registered-root containment and path-free browser APIs.

Do not claim Fedora deployment, Tailscale access, authentication, download,
client-local availability, or full server/client MVP completion.

## 6. Gallery Preview Gap

Real-content Gallery previews currently work.

No durable persistent server-generated gallery preview or cover cache exists.
Current previews are not a server-prewarmed derivative library suitable for
efficient remote clients. No stable cache ownership, derivative invalidation,
identity-only preview endpoint, or operator prewarm workflow exists.

The next implementation must not call an automatically selected frame a
user-accepted cover.

ADR-0024 semantics remain:

- a future accepted cover remains a human-reviewed choice;
- exact accepted cover timestamp and Cover Studio remain later work;
- an automatically selected frame in the immediate slice is a persistent gallery
  preview derivative or fallback gallery cover;
- it must not silently become the accepted cover candidate.

## 7. New COOPERATOR Product Direction

Product decision: Michal wants to reach an MVP state where a server-local
directory of real GIF and MP4 MEMEs can be onboarded, preview derivatives can be
prepared, Gallery loads efficiently, and originals stream on explicit playback.

Prioritize persistent Gallery preview derivatives before browser download.
Streaming already exists and must be preserved. Broad cosmetic work remains
frozen except concrete usability defects.

Future private acceptance directory:

```text
/Users/agile/MEMEs
```

This is private local media and is forbidden by default. No Worker may inspect,
list, stat, hash, read, decode, copy, analyze, upload, rename, move, delete, or
write sidecars in that directory without future task-specific authority. The
current handoff grants no access to it.

## 8. Immediate Next Recommended Task

```text
Task:
Add persistent server gallery preview derivatives

Expected implementation subject:
feat: add persistent gallery previews
```

The future task should use a fresh Worker and should be limited to a backend
foundation.

Recommended boundaries for the future ORCHESTRATOR prompt:

- inspect existing media analysis/frame extraction, content delivery,
  configuration, persistence, and ADR-0024;
- create server-owned derivative storage outside registered source-media roots;
- generate one deterministic static preview derivative for an available GIF or
  MP4;
- use local processing only;
- no AI or provider call;
- never mutate source media;
- version the derivative algorithm or cache key;
- invalidate or regenerate when the observed source identity changes;
- make generation idempotent and atomic;
- prevent partial files from becoming valid cache entries;
- enforce resource limits and sanitized failures;
- expose derivative bytes through an identity-only path-free endpoint;
- support an explicit server-operator prewarm/generate workflow suitable for one
  library or all imported available media;
- use temporary databases and synthetic media in tests;
- keep Gallery integration and real private-media acceptance as a following
  separate task unless inspection proves a small integration is essential.

Do not prescribe a final database migration, media format, endpoint path, CLI
spelling, or cache layout in this handoff. Those must be chosen by a future
authoritative task after repository inspection.

## 9. Expected Following Slices

Recommended MVP order:

1. persistent server gallery preview backend;
2. Gallery consumption of persistent previews;
3. explicitly authorized acceptance using `/Users/agile/MEMEs`;
4. secure explicit browser download;
5. Fedora service/deployment;
6. authoritative Tailscale remote access;
7. trusted client-local download registration;
8. thin native/Tauri client after the server workflow is coherent.

Keep manual Cover Studio, AI cover generation, physical rename, sync, global tag
deletion, and arbitrary upload as separate slices.

## 10. Immediate Non-Goals

The next preview-foundation task must not silently expand into:

- manual Cover Studio;
- accepted cover selection;
- AI cover generation;
- metadata AI analysis;
- private `/Users/agile/MEMEs` access;
- Gallery redesign;
- physical rename;
- explicit media download;
- local-availability registration;
- upload or synchronization;
- background filesystem watching;
- Fedora deployment;
- Tailscale or authentication;
- Tauri;
- source-media mutation.

## 11. Browser Automation Context

Safari Apple Events browser automation is available as project capability
context on the primary macOS development environment. Availability grants no
task authority.

Every use requires exact origins, interactions, evidence, external-network,
private-state, temporary-artifact, and cleanup boundaries. Unrelated browser
state must never be inspected. Linux has no guaranteed default browser adapter
yet.

## 12. Closure Status

```text
pre-closeout HEAD: 0f60f0313edb5970fc649f12ce25f8cdf6caa4dd
latest implementation boundary: ba942f219932782b8f323768dbc9ed4667f6400f
migration head: 0007
current Worker closes with enclosing commit: yes
active Worker after verified push: none
active disposable runtime: none
immediate next recommended task: Add persistent server gallery preview derivatives
expected next implementation subject: feat: add persistent gallery previews
next private acceptance input: /Users/agile/MEMEs remains unauthorized
Orchestrator session: remains active and is not being handed off
```
