# FrameNest AI Workspace

## Status

This is living subsystem documentation for the future manual-first Metadata
workspace and optional multi-model AI draft workflow.

Classification: living subsystem documentation.

Intended consumers: COOPERATOR, ORCHESTRATOR, WORKER, and product/UX
implementation tasks.

Retention trigger: retain while the AI workspace subsystem exists.

Inbound discoverability: [README.md](README.md), [PRODUCT.md](PRODUCT.md),
[GALLERY.md](GALLERY.md), [SPEC.md](SPEC.md), [ROADMAP.md](ROADMAP.md),
[ADR-0020](docs/adr/0020-on-demand-ai-suggestion-review.md), and
[ADR-0023](docs/adr/0023-manual-first-metadata-and-multi-model-ai-drafts.md).

Update owner: only a future explicitly authorized WORKER task under
ORCHESTRATOR authority.

## Current Implementation Boundary

FrameNest currently implements an explicit, same-origin, non-persistent browser
AI suggestion review per
[ADR-0020](docs/adr/0020-on-demand-ai-suggestion-review.md). It is pre-alpha,
session-only, provider-confirmed for cloud execution, and does not save catalog
metadata or mutate files.

The packaged browser now implements a bounded manual `Current` metadata
workspace for one selected imported medium. It can load sparse or persisted
metadata, edit or clear the display title, search existing canonical tags
locally, assign up to 32 ordered canonical tags, explicitly create a canonical
tag definition, save through the existing metadata API, discard unsaved
changes, and refresh the active Catalog view after a successful save. This
current slice covers display title and canonical tags only.

The full multi-model AI draft comparison, inline model picker, persistent draft
storage, descriptions, collections, suggested filename editing, and premium
media detail workspace remain future architecture accepted by
[ADR-0023](docs/adr/0023-manual-first-metadata-and-multi-model-ai-drafts.md).

## Workspace Purpose

The Metadata workspace exists to let the user edit media metadata manually first
and use AI only as optional assistance. It must remain usable without internet,
without provider credentials, and after every AI draft is rejected.

The workspace edits catalog metadata concepts. It must not silently rename,
move, delete, tag, reorganize, or otherwise mutate media files.

## State Model

The workspace distinguishes:

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

Opening a detail page performs no AI call, no catalog save, and no filesystem
mutation. If no durable display title exists, FrameNest may derive an initial
display title from the real on-disk filename, but that display value is not the
physical filename.

Changing display title does not rename a file. Editing suggested filename does
not rename a file. Saving catalog metadata does not implicitly rename, move,
delete, tag, or reorganize files. A future physical rename operation must be an
explicit separate workflow.

## `Current`

`Current` is the primary editable manual working copy. In the current browser
slice, `Current` covers display title and ordered canonical tags for one
selected imported medium. In later detail slices it should expand to additional
manual metadata fields. It is available before any AI run, remains editable
after AI, and is not closable like an AI draft.

`Current` must never be silently overwritten. Values enter `Current` through
manual editing or explicit promotion from an AI draft. `Current` remains
unsaved until the user performs an explicit durable save.

Unsaved `Current` work may be abandoned. A detail page must not save merely
because it opened or because an AI draft exists.

## AI Drafts

Every explicit AI invocation creates a separate AI draft representing one
provider, one model, one run, one prompt version, and one proposal.

A draft may contain title, description, collection, canonical tags, suggested
filename, confidence, evidence, uncertainties, provider/model provenance,
local/cloud classification, creation time, and edited/accepted/rejected state.

Draft values may be prefilled inside the draft. They do not overwrite
`Current`. `Use this draft` copies selected proposal values into `Current`; it
does not save the catalog and does not mutate the filesystem.

A draft may be edited, rejected, discarded, or compared. Closing an edited draft
requires an explicit discard decision. No draft is automatically promoted,
saved, tagged, renamed, or assigned to a collection.

## Promotion And Save Flow

Promotion and persistence are separate.

`Use this draft` copies chosen draft values into `Current`. The user may then
continue editing manually, compare another draft, abandon the work, or save.

Durable save writes accepted current-page metadata to the future catalog
boundary. It still must not implicitly rename, move, delete, tag operating
system metadata, reorganize directories, or run a physical migration.

## Discard Flow

Discarding an unedited draft may be immediate when the UI clearly shows the
result. Discarding an edited draft requires an explicit decision because the
user may have created manual work inside that draft.

Discarding a draft does not alter `Current`, persisted catalog values, physical
filename, library-relative path, or media bytes.

Abandoning unsaved `Current` work returns to persisted catalog values or the
derived display value used when no durable title exists.

## Inline Model Picker

A future `+` control opens a compact searchable model picker inside the media
detail workspace. It does not navigate to Settings.

The picker may show display name, provider, model ID, local/cloud
classification, configured/unconfigured state, current availability, capability
badges, and provider-reported free or trial information when available.

Browsing, filtering, selecting, or highlighting a model must not invoke a
provider. Only an explicit final action such as `Analyze with this model` may
invoke analysis.

Settings remains responsible for credentials, provider configuration, provider
enablement, defaults, discovery refresh, and unavailable-provider remediation.
The workspace picker selects from configured, currently compatible choices.

Free or trial information must be treated as provider-reported and temporary,
not as permanent product truth.

## Capability Labels

Future filtering should use provider-neutral capability concepts such as
`vision_input`, `video_input`, `structured_text_output`, `image_generation`,
`image_editing`, `reference_image`, `local_execution`, and `cloud_execution`.

Exact implementation names, discovery contracts, compatibility registries,
refresh cadence, and provider-specific fallbacks are deferred.

The workspace must not assume every provider supports dynamic discovery, every
model supports every workflow, one fixed model count exists, or one provider
architecture is permanent.

## Loading And Error States

Capability loading must be truthful. A capability list may be loading,
unavailable because no provider is configured, unavailable because credentials
are missing, unavailable because the provider cannot be reached, or unavailable
because no compatible model exists.

Provider analysis is indeterminate unless real progress data exists. The UI may
show pending state, but it must not show fabricated percentages, invented model
stages, false cancellation, raw provider responses, raw prompts, image payloads,
absolute media paths, database paths, credentials, or reasoning content.

Errors should explain the next useful user action without exposing secrets,
private paths, raw diagnostics, or provider internals.

## Local And Cloud Labelling

Every model choice and AI draft should clearly indicate whether execution is
local or cloud. Cloud execution requires explicit confirmation before each
request. Local execution must not be mislabeled as cloud, and cloud execution
must not be hidden behind generic wording.

Provider credentials remain server-side. Browser code must not receive API
keys, Authorization headers, credential state that reveals a value, raw prompt
payloads, raw provider responses, frame payloads, absolute media paths, or
database paths.

## Draft Navigation

For a small number of drafts, the workspace may use browser-style tabs:

```text
[ Current ] [ Provider A ] [ Provider B ] [ + ]
```

`Current` remains fixed and not closable. Draft tabs may be closable when their
discard rules are satisfied.

For a larger number of drafts, the UI should use a horizontal strip with stable
minimum widths, horizontal scrolling, and an overflow menu. Labels must not
compress into unreadable text. Keyboard focus order must remain predictable.

## Canonical Tag Editing

Canonical tags use stable English storage identifiers. The future editor should
provide searchable local suggestions, keyboard and mouse navigation, rounded
removable chips, an explicit `×` removal control, visible hover, focus,
selected, AI-suggested, and invalid states, case-insensitive duplicate
prevention, optional controlled new-tag creation, and responsive behavior with a
larger local tag catalog.

Filtering local tag suggestions should feel immediate and should not display a
progress indicator for trivial local work.

This document does not choose a frontend framework or component library.

## Accessibility And Focus

The workspace must support keyboard navigation, visible focus, meaningful
labels, non-color-only state distinctions, and screen-reader semantics for
tabs, draft close controls, model-picker controls, tag chips, invalid states,
and cloud-confirmation dialogs.

Focus should move predictably after creating a draft, promoting draft values,
discarding a draft, opening the model picker, closing the picker, and removing a
tag chip.

Reduced-motion users should receive static or simplified state transitions.

## Provenance

AI drafts should retain provider, model, prompt version, local/cloud
classification, creation time, and any supported confidence, evidence, and
uncertainty fields. Provenance belongs to the draft and future accepted catalog
metadata may later record selected provenance where an explicit persistence
design accepts it.

Provider output is untrusted. FrameNest attaches trusted provider/model/prompt
metadata from its own invocation boundary rather than trusting model text.

## Ephemeral And Future Persistent Boundaries

Current implemented AI suggestion review is ephemeral page-session state.
Accepting or rejecting that review does not call a mutation endpoint.

Future persistent drafts, audit history, catalog save behavior, draft retention,
and provenance persistence require separate implementation tasks and likely
schema decisions. This document records the accepted conceptual boundaries but
does not design a database migration.

## Security Invariants

- AI is optional.
- AI is explicitly requested.
- Cloud execution requires explicit confirmation.
- Provider credentials remain server-side.
- No provider call occurs on page load.
- No AI draft is automatically promoted.
- No AI value is automatically saved.
- No file is automatically renamed, moved, deleted, tagged, or assigned to a
  collection.
- No browser credential exposure is allowed.
