# Next Worker Handoff

## 1. Title And Authority

This file is a non-authoritative repository-native Worker handoff. It restores
context for a future fresh Worker instance only.

It grants no modification, migration, dependency, secret, network, provider,
private-media, filesystem, deployment, Git-write, or implementation authority.
It does not authorize work merely because a direction or risk is recorded here.

Only one future authoritative ORCHESTRATOR prompt may grant a concrete task.
Boot files, AP methodology documents, ADRs, roadmap documents, and handoff files
do not independently authorize implementation.

## 2. Role And Lifecycle Model

`WORKER` is the persistent protocol role in FrameNest's repository protocol. A
concrete Worker instance is one execution agent assigned to that role for a
bounded lifecycle. A Worker session is that instance's active continuity of
context and responsibility. The execution client, agent implementation, model,
and provider may vary between sessions and do not change the protocol role.

Context pressure and automatic compaction can make one concrete session less
reliable over time. This handoff closes the currently active concrete Worker
session after Cycle 069. After the Cycle 069 closeout commit and push, this
concrete Worker instance is permanently closed and must never receive another
task.

No active Worker instance exists after this closeout. A future Worker must be a
fresh instance newly assigned to the persistent `WORKER` role.

## 3. Repository Identity

Repository URL: `https://github.com/cisarik/framenest.git`

Normal working directory: `/Users/agile/framenest`

Normal branch: `main`

Public implementation HEAD before the Cycle 069 closeout commit:
`74fc43b24eae976d47dfeab5685f50d6aa1c0ef6`

Subject before the Cycle 069 closeout commit:
`feat: add manual metadata workspace`

Parent of that implementation HEAD:
`b55dc3e400afae30ba73f00f255f953cf022fb10`

A future Worker must verify the repository root, remote URL, branch,
cleanliness, local HEAD, tracking branch, and public remote state before
acting. Do not trust recorded SHAs blindly, and do not invent the Cycle 069
closeout commit SHA from this document. Discover it from Git.

## 4. Future Fresh Worker Startup

A future fresh Worker must read at least:

1. [AGENTS.md](AGENTS.md)
2. [BOOT_WORKER.md](BOOT_WORKER.md)
3. [AP_WORKER.md](AP_WORKER.md)
4. [NEXT_WORKER.md](NEXT_WORKER.md)
5. [AP.md](AP.md)
6. [AP_ORCHESTRATOR.md](AP_ORCHESTRATOR.md)
7. [PRODUCT.md](PRODUCT.md)
8. [SPEC.md](SPEC.md)
9. [ROADMAP.md](ROADMAP.md)
10. [README.md](README.md)
11. [AI_WORKSPACE.md](AI_WORKSPACE.md)
12. [GALLERY.md](GALLERY.md)
13. [COVER_PIPELINE.md](COVER_PIPELINE.md)
14. [SECURITY.md](SECURITY.md)
15. [docs/adr/README.md](docs/adr/README.md)
16. task-relevant accepted ADRs
17. task-relevant implementation and tests
18. the future authoritative ORCHESTRATOR prompt

Repository implementation, tests, accepted ADRs, public Git evidence, and the
future authoritative prompt override stale handoff statements.

## 5. Implemented Foundation Through Cycle 068

FrameNest is a foundation-stage, pre-alpha, local-first library for video and
animated media.

The public repository currently includes:

- CPython 3.13 and Poetry package foundation;
- centralized settings and package-mode source layout;
- FastAPI loopback-first local server and Uvicorn runtime through
  `framenest-server`;
- typed health endpoint;
- packaged vanilla same-origin local web shell;
- FrameNest-owned structured logging and redaction boundary;
- explicit SQLite/Alembic persistence through migration head `0005`;
- explicit `framenest-db status` and `framenest-db migrate`;
- no automatic server migration;
- stable domain identity primitives;
- local device registry;
- local library registry;
- deterministic read-only library scan preview;
- deterministic local media-analysis preview;
- provider-neutral AI suggestion boundary;
- NVIDIA NIM prototype with explicit cloud confirmation;
- minimum logical-media and physical-location catalog;
- explicit idempotent scan-candidate import;
- persistent display-title metadata;
- persistent canonical tags and ordered media-to-tag assignments;
- sparse media metadata rows;
- searchable catalog read/query boundary;
- packaged catalog browser UI;
- manual metadata workspace for display-title and canonical-tag review/editing;
- application ports, use cases, SQLAlchemy Core repositories, migrations, and
  same-origin API boundaries for the implemented catalog slices.

Do not describe import, display title, canonical tags, catalog search, manual
title editing, manual tag editing, or migration `0005` as unimplemented.

## 6. Cycle 067: Searchable Catalog Browser

Public commit:
`b55dc3e400afae30ba73f00f255f953cf022fb10`

Parent:
`0ff83f8e16cd95de89a8e32dab0240b09cd2092b`

Subject:
`feat: add searchable media catalog`

Public changed-path count: 20.

Cycle 067 added [ADR-0028](docs/adr/0028-catalog-read-model-and-search-semantics.md)
and a dedicated catalog query/read vertical slice.

Accepted public behavior:

- dedicated application catalog query/read boundary;
- `GET /api/media` same-origin API endpoint;
- literal display-title search;
- SQLite `NOCASE` limitation is accepted for the initial implementation;
- repeated canonical-tag filters use AND semantics;
- deterministic newest-first ordering with stable media-ID tie-breaker;
- total count is computed before pagination;
- deterministic tag and location order;
- one logical result is returned even when media has multiple locations;
- packaged catalog UI lists imported media;
- catalog refresh occurs after successful explicit import;
- no migration or dependency change was required.

Worker-observed runtime evidence from Cycle 067, not rerun during Cycle 069:

- baseline full suite: `867 passed, 3 skipped`;
- focused final tests: `61 passed`;
- full final suite: `898 passed, 3 skipped`;
- warning-as-error suite: `898 passed, 3 skipped`;
- build, compile, lock, wheel, and diff checks passed.

## 7. Cycle 068: Manual Metadata Workspace

Public commit:
`74fc43b24eae976d47dfeab5685f50d6aa1c0ef6`

Parent:
`b55dc3e400afae30ba73f00f255f953cf022fb10`

Subject:
`feat: add manual metadata workspace`

Public changed-path count: 11.

Cycle 068 changed documentation, packaged web assets, contract tests, and one
integration test only. It made no backend, schema, API, migration, or dependency
change.

Accepted public behavior:

- explicit `Edit metadata` action;
- one selected medium is addressed by media ID;
- manual `Current` metadata state is shown;
- sparse metadata is accepted;
- title can be edited or cleared;
- fallback display title is not persisted implicitly;
- canonical tag search is available;
- a maximum of 32 assigned tags is enforced;
- duplicate tag assignment is prevented;
- ordered removable tag chips are shown;
- earlier/later controls reorder assigned tags;
- explicit tag creation is available;
- creation statuses include `created`, `already_exists`, and `conflict`;
- workspace distinguishes clean and dirty state;
- discard confirmation protects unsaved changes;
- `beforeunload` protection is dirty-only;
- save statuses include `created`, `updated`, and `unchanged`;
- missing-tag, missing-medium, catalog-unavailable, validation, and generic
  errors are surfaced;
- unsaved edits are preserved where safe;
- active catalog refreshes after successful save;
- no AI invocation occurs;
- no filesystem mutation occurs.

Worker-observed runtime evidence from Cycle 068, not rerun during Cycle 069:

- baseline full suite: `898 passed, 3 skipped`;
- test-first expected failure: `6 failed, 35 passed`;
- focused final tests: `41 passed`;
- full final suite: `905 passed, 3 skipped`;
- warning-as-error suite: `905 passed, 3 skipped`;
- Node syntax check passed;
- build, compile, lock, wheel, and diff checks passed;
- `dist/` was removed.

## 8. ADR And Migration Horizon

Highest accepted ADR before the Cycle 069 closeout commit:
[ADR-0028](docs/adr/0028-catalog-read-model-and-search-semantics.md).

Current migration head before the Cycle 069 closeout commit: `0005`.

Accepted architecture through Cycle 068 includes:

- [ADR-0023](docs/adr/0023-manual-first-metadata-and-multi-model-ai-drafts.md)
  for AI suggestion confidence and action semantics;
- [ADR-0024](docs/adr/0024-cover-studio-and-ai-cover-candidates.md)
  for the provider-neutral AI suggestion workspace;
- [ADR-0025](docs/adr/0025-minimum-persistent-media-catalog-foundation.md)
  for the minimum persistent catalog foundation;
- [ADR-0026](docs/adr/0026-explicit-idempotent-scan-candidate-import.md)
  for explicit idempotent scan-candidate import;
- [ADR-0027](docs/adr/0027-persistent-display-title-and-canonical-tags.md)
  for persistent display-title and canonical-tag metadata;
- [ADR-0028](docs/adr/0028-catalog-read-model-and-search-semantics.md)
  for the searchable media catalog browser.

A future Worker must inspect [docs/adr/README.md](docs/adr/README.md) and the
task-relevant ADRs directly before making architectural claims.

## 9. Explicitly Unimplemented State

The repository still does not contain a completed end-user desktop application,
storage-volume registration, browser metadata editor beyond the current manual
title/tag workspace, multi-tag filtering beyond repeated canonical-tag AND
filtering, descriptions, collections, suggested filenames, covers, thumbnails,
persistent premium gallery, deployment, systemd unit, or Tailscale integration.

The server must remain loopback-first by default. Backend services must not
replace local desktop functionality. Remote access direction remains
Tailscale-only unless explicitly superseded by an accepted decision. Provider
secrets must not be distributed to ordinary client installations.

## 10. Product Invariants

FrameNest remains local-first, privacy-conscious, and cross-platform in product
direction. The premium gallery remains a flagship product invariant.

The current AI suggestion workspace is non-persistent. Provider-backed analysis
requires explicit confirmation and must respect the provider, secret, and
private-media boundaries recorded in product and architecture documents.

## 11. Private Corpus Boundary

Private corpus path: `/Users/agile/Video`.

The private corpus contains MP4 test material and `dicaprio_bravo.gif`. Its
existence grants no task authority.

Cycle 064 evidence remains Worker-observed private runtime evidence only. No
private corpus access occurred in Cycles 067, 068, or 069.

Future private-media access requires exact task-specific authorization. Any
cloud or provider transmission of private media requires separate explicit
authorization.

Do not expose private filenames other than the already authorized
`dicaprio_bravo.gif` name. Do not expose private hashes, database identifiers,
directory listings, raw frames, metadata extracts, or media contents.

## 12. Known Limitations And Risks

Recorded handoff statements may become stale. Public committed repository state,
tests, accepted ADRs, and future authoritative prompts are stronger evidence
than this file.

Catalog search currently accepts SQLite `NOCASE` behavior. It should not be
described as full Unicode case folding or locale-aware search.

Manual metadata editing currently covers display title and canonical tags. Tag
rename/delete, description editing, collections, covers, thumbnails, and
suggested filename persistence remain outside the implemented surface.

## 13. Non-Authoritative Next Direction

Likely future work should stay bounded to one approved vertical slice at a time
and should be authorized by a future ORCHESTRATOR prompt. Candidate directions
must be checked against [ROADMAP.md](ROADMAP.md), [SPEC.md](SPEC.md), accepted
ADRs, and current repository state before action.

This handoff does not choose the next task.

## 14. Validation Evidence Classification

Cycle 067 and Cycle 068 validation evidence in this file is historical
Worker-observed evidence from those cycles. It was not rerun during Cycle 069.

Cycle 069 is a documentation-only closeout. The authorized validation surface is
limited to handoff replacement checks, diff checks, link checks, secret-pattern
checks, Git state checks, and public push verification.

Do not infer from Cycle 069 that implementation tests, full pytest, build,
package, migration, browser, or runtime checks were rerun.

## 15. Cycle 069 Closeout

Cycle 069 replaces this handoff file after Cycles 067 and 068. It records the
current repository state, lifecycle closure, private corpus boundary, and future
fresh Worker startup requirements.

Cycle 069 is authorized to modify exactly [NEXT_WORKER.md](NEXT_WORKER.md), then
commit once with subject `docs: close catalog workspace worker session`, push to
`origin main`, and report.

Cycle 069 is not authorized to modify [NEXT_ORCHESTRATOR.md](NEXT_ORCHESTRATOR.md),
implementation files, tests, ADRs, product documents, migrations, dependencies,
or generated artifacts.

## 16. Final Lifecycle Declaration

Persistent role: `WORKER` continues.

Concrete Worker instance: permanently closed after the successful Cycle 069
closeout commit and push.

Worker session: `CLOSED`.

Active Worker instance: none.

Future Worker: fresh instance required.

Future task authority: none.

[NEXT_ORCHESTRATOR.md](NEXT_ORCHESTRATOR.md): unchanged by Cycle 069.

## 17. Future Worker First Response Checklist

A future Worker should begin by verifying:

- repository root and remote URL;
- current branch and cleanliness;
- local HEAD, `origin/main`, and public remote `main`;
- whether the Cycle 069 closeout commit is now the public head;
- migration head and accepted ADR index;
- task-specific authority from the future ORCHESTRATOR prompt;
- no reliance on private corpus state unless expressly authorized.

If the future prompt conflicts with repository sources, identify the exact
conflict and escalate through the Orchestrator rather than silently expanding
scope.
