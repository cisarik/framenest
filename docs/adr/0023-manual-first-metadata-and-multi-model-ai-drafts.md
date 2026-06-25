# ADR-0023: Manual-First Metadata and Multi-Model AI Drafts

## Status

`Accepted`

## Decision Date

`2026-06-25`

## Decision Authority

The Cooperator accepted the manual-first metadata workspace and multi-model AI
draft direction through bounded task
`FRAMENEST-CYCLE-061-DOCUMENT-MANUAL-AI-AND-COVER-WORKSPACES`.

## Context

FrameNest is local-first and privacy-conscious. The current repository includes
a non-persistent, editable, explicit browser AI suggestion review accepted by
[ADR-0020](0020-on-demand-ai-suggestion-review.md). It does not yet include a
persistent media catalog, durable metadata editing, persistent AI drafts, a
model picker, provider discovery, or the premium media detail workspace.

Before the persistent media catalog and any later migration are designed,
FrameNest must separate manual metadata, physical file state, catalog
persistence, and optional AI suggestions. AI must assist the user; it must not
own metadata or mutate files.

Related documents:

- [ADR-0020](0020-on-demand-ai-suggestion-review.md)
- [ADR-0010](0010-initial-persistence-foundation.md)
- [ADR-0014](0014-safe-library-scan-preview.md)
- [SPEC.md](../../SPEC.md)
- [GALLERY.md](../../GALLERY.md)
- [AI_WORKSPACE.md](../../AI_WORKSPACE.md)

## Decision

### Manual-first detail behavior

Opening a media detail view must perform no AI call, no catalog save, and no
filesystem mutation.

When no durable display title exists, FrameNest may derive an initial display
title from the real on-disk filename. That derived display value is not the
physical filename and must not be conflated with it.

The user must be able to manually edit:

- display title;
- description;
- collection;
- canonical tags;
- suggested filename.

Manual editing must work before AI, after AI, without AI, without internet, and
after the user rejects every AI draft.

### State separation

FrameNest must distinguish:

- persisted catalog values;
- unsaved `Current` manual working state;
- physical filename;
- library-relative path;
- AI draft;
- edited AI draft;
- promoted draft values;
- accepted current-page values;
- durable catalog save;
- suggested filename;
- future explicit physical rename operation.

Changing display title does not rename a file. Editing suggested filename does
not rename a file. `Use this draft` does not save to the catalog and does not
mutate the filesystem. A catalog save does not implicitly rename, move, delete,
tag, or reorganize media files. Unsaved work may be abandoned. No save occurs
merely because a detail page is opened.

### `Current` workspace

`Current` is the primary editable manual working copy. It is available before
any AI run, is never silently overwritten, is not closable like an AI draft, and
remains separate from durable persistence until an explicit save.

### AI draft semantics

Every explicit AI invocation creates a separate draft representing one provider,
one model, one run, one prompt version, and one proposal.

A draft may include:

- title;
- description;
- collection;
- canonical tags;
- suggested filename;
- confidence;
- evidence;
- uncertainties;
- provider/model provenance;
- local/cloud classification;
- creation time;
- edited, accepted, or rejected state.

AI draft values may be prefilled inside the draft. Drafts do not overwrite
`Current`. Promotion requires an explicit action such as `Use this draft`.
Promotion copies selected proposal values into `Current`; it is not
persistence. Drafts may be edited, rejected, discarded, or compared. Closing an
edited draft requires an explicit discard decision.

No AI draft is automatically promoted, saved, tagged, renamed, or assigned to a
collection.

### Inline model picker

A future `+` control may open a searchable model picker from the media detail
workspace without navigating to Settings.

The picker may display, when available:

- display name;
- provider;
- model ID;
- local/cloud classification;
- configured or unconfigured state;
- current availability;
- capability badges;
- provider-reported free or trial information.

Browsing, filtering, selecting, or highlighting a model must not invoke a
provider. Only a separate explicit final action such as `Analyze with this
model` may invoke analysis.

Settings remains responsible for credentials, provider configuration, provider
enablement, defaults, and discovery refresh. The media detail picker selects
only from configured, currently compatible choices.

Provider-reported free or trial information is informational when available. It
must not be documented as permanent, universal, or guaranteed.

### Capability-aware selection

FrameNest accepts provider-neutral capability concepts for future filtering and
compatibility decisions, including:

- `vision_input`;
- `video_input`;
- `structured_text_output`;
- `image_generation`;
- `image_editing`;
- `reference_image`;
- `local_execution`;
- `cloud_execution`.

Exact implementation names, provider-discovery contracts, refresh behavior, and
compatibility registry details remain deferred.

FrameNest must not assume that every provider supports dynamic model discovery,
every model can perform every workflow, one fixed model count exists, free
access is permanent, or one NVIDIA architecture is permanent.

### Canonical tag editing

The premium canonical-tag interaction is accepted as future UX direction.
Canonical storage identities are stable English identifiers.

The future tag editor should provide searchable local suggestions, keyboard and
mouse navigation, rounded removable chips, an explicit `×` removal control,
visible hover, focus, selected, AI-suggested, and invalid states,
case-insensitive duplicate prevention, optional controlled creation of a new
tag, responsive behavior with a larger local tag catalog, and immediate local
filtering.

Trivial local tag filtering should not show a progress indicator. Progress
feedback is reserved for genuinely asynchronous or expensive work.

This ADR does not choose a concrete frontend framework or component library.

### Security and product invariants

AI remains optional and explicitly requested. Cloud execution requires explicit
cloud confirmation. Provider credentials remain server-side and must not be
exposed to browser code.

FrameNest must not perform automatic provider requests on page load. It must not
automatically rename, move, delete, tag, assign collection, promote a draft, or
save.

## Rationale

Manual-first metadata keeps FrameNest usable without internet, without provider
accounts, and after AI suggestions are rejected. Separating `Current`, AI
drafts, catalog saves, and filesystem mutation prevents accidental data loss and
prevents the future persistent catalog from inheriting ambiguous semantics.

One draft per provider/model/run preserves provenance and comparison. It also
avoids one model result silently overwriting another model's suggestion or the
user's manual work.

Capability-aware model selection keeps the UI truthful as provider catalogs,
model availability, local models, cloud models, and pricing or trial labels
change over time.

## Consequences

### Positive

- Persistent catalog work has clear naming and state boundaries before schema
  design.
- AI remains assistance rather than metadata authority.
- Manual editing remains complete without AI.
- Future model comparison can preserve provenance and user choice.
- Canonical-tag editing is recorded as a premium interaction without selecting
  a framework.

### Costs and limitations

- Future implementation must manage more states than a single suggestion form.
- Draft comparison, discard prompts, and overflow behavior require careful UX.
- Capability metadata needs future provider or registry contracts.
- Persistent draft storage is not decided by this ADR.

## Deferred Decisions

This ADR does not decide:

- persistent media catalog schema;
- migration numbering or table design;
- API endpoints;
- draft persistence schema;
- provider and model discovery contracts;
- prompt construction;
- model ranking or defaults;
- cost display semantics;
- exact capability metadata names;
- frontend framework or component library;
- Settings implementation;
- secret-store implementation;
- background jobs, cancellation, retries, or streaming updates;
- physical rename workflow.

## Current Implementation Boundary

The current implementation remains the ADR-0020 pre-alpha, session-only browser
AI suggestion review. The multi-model `Current` workspace, inline model picker,
durable catalog save, persistent drafts, and premium tag-chip editor are future
architecture and are not implemented by this ADR.

## Artifact Lifecycle

Classification: permanent normative architecture decision.

Consumers: future Orchestrator and Worker instances, product/UX implementation
tasks, catalog implementers, gallery implementers, AI-provider implementers,
and security reviewers.

Retention: retained permanently; superseded only by a later accepted ADR.

Inbound links: ADR index, [AI_WORKSPACE.md](../../AI_WORKSPACE.md),
[GALLERY.md](../../GALLERY.md), [PRODUCT.md](../../PRODUCT.md),
[SPEC.md](../../SPEC.md), [ROADMAP.md](../../ROADMAP.md), and
[README.md](../../README.md).

Cleanup owner: future explicitly authorized Worker only through a superseding
ADR.

## Revisit Triggers

Revisit when authorizing persistent media catalog schema, durable metadata save,
draft persistence, provider/model discovery, GUI Settings, secret-store
implementation, background analysis jobs, exact frontend framework selection, or
physical rename workflows.

## Related Documents

- [ADR index](README.md)
- [ADR-0020](0020-on-demand-ai-suggestion-review.md)
- [ADR-0024](0024-cover-studio-and-ai-cover-candidates.md)
- [AI_WORKSPACE.md](../../AI_WORKSPACE.md)
- [COVER_PIPELINE.md](../../COVER_PIPELINE.md)
- [GALLERY.md](../../GALLERY.md)
- [PRODUCT.md](../../PRODUCT.md)
- [SPEC.md](../../SPEC.md)
- [ROADMAP.md](../../ROADMAP.md)
