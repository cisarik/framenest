# FrameNest Gallery Product Reference

## Status

This is a living permanent product and UX reference. It records accepted gallery
direction; it does not claim that a persistent gallery is currently implemented.

Classification: living permanent product architecture/UX reference.

Consumers: Orchestrator, Worker, designers, implementers, maintainers, and
security reviewers.

Retention: remains while the gallery product subsystem exists.

Inbound links: [README.md](README.md), [PRODUCT.md](PRODUCT.md),
[SPEC.md](SPEC.md), [ROADMAP.md](ROADMAP.md), [ADR-0022](docs/adr/0022-selective-media-placement-and-server-aggregation.md),
[ADR-0021](docs/adr/0021-tauri-desktop-shell.md),
[AI_WORKSPACE.md](AI_WORKSPACE.md), [COVER_PIPELINE.md](COVER_PIPELINE.md),
[ADR-0023](docs/adr/0023-manual-first-metadata-and-multi-model-ai-drafts.md),
and [ADR-0024](docs/adr/0024-cover-studio-and-ai-cover-candidates.md).

Cleanup/update owner: future explicitly authorized Worker under an Orchestrator
task. Git history remains the archive.

## Flagship Role

The gallery is a flagship FrameNest capability. It should be premium, dark,
cover-first, fast, and useful for large personal collections. The current
repository implements a minimum persistent media catalog and a read-only
imported-media catalog browser with display-title search and canonical-tag AND
filters. It does not yet implement the cover pipeline, derived thumbnails, or
real premium gallery.

The gallery should feel like a media product, not a generic administrative
dashboard.

## Media Detail And Metadata Workspace

The media detail direction is manual-first. The current packaged Catalog
browser includes a bounded manual media editor for one selected imported
medium. Opening the editor loads existing title, description, and tag metadata;
it must not trigger an AI call, save catalog metadata, or mutate the filesystem.
When no durable title exists, the browser may show a fallback label derived from the first
deterministic relative location, but the display title, physical filename,
library-relative path, suggested filename, catalog save, and future physical
rename operation remain separate concepts.

The current editor exposes ordinary `Title`, `Description`, `Tags`, `Save`, and
`Cancel` controls. Tag creation happens from the same search/add control and
uses hidden stable tag keys; those internal keys, collection assignment, and
`Processed` workflow state are not ordinary editor controls. The `Processed`
membership remains derived automatically from durable tag saves, not chosen
manually. The editor can explicitly run NVIDIA-backed analysis for an imported
available GIF or MP4 after confirmation. That request sends up to three
optimized preview frames plus bounded metadata, disables model reasoning for the
validated JSON request, and can replace the current unsaved `Title`,
`Description`, and `Tags` fields directly only after explicit confirmation. The
confirmation must state that current unsaved fields will be replaced, that the
result is not saved automatically, and that no physical rename occurs. A
successful analysis may reveal one compact editable `Suggested filename` field
inside the same editor; that field is not included in metadata Save and does
not rename the file. Save remains explicit and closes the editor on success.
Persistent drafts, model comparison, provider Settings, and explicit physical
rename remain future work.

The Details dialog now plays real local GIF and MP4 content through the
identity-only `GET /api/media/{media_id}/locations/{location_id}/content`
endpoint when the first catalog location is `available`. It selects only by
`media_id` and `location_id`; it never constructs playback URLs from relative
paths, absolute paths, or library roots. Video uses a native `<video>` element
with controls, metadata preload, and `playsinline`; animated images use a real
`<img>`. Available local Gallery cards show immediate real media visuals. GIF
cards use a static real-content preview so the grid does not animate
automatically; GIF animation occurs in Details after explicit user interaction.
MP4 cards use a real paused decoded-frame visual from the identity-only content
endpoint with no autoplay, loop, card controls, or automatic audio. A centered
real `▶` affordance and the media surface open actual Details playback, while
the only visible card action is `Edit`. These immediate card visuals are not
durable accepted covers, persistent thumbnails, or the future cover pipeline;
generic available-media placeholders are rejected. Details uses a black
player-first surface. Native/VLC playback, downloadable files, and a broader
media player are future work.

The Gallery header and pagination should stay compact: the temporary `FN` mark
is sufficient branding in the current shell, status labels should be short and
accessible, and pagination should offer bounded page-size choices without
verbose navigation labels.

Developer-oriented Library tools do not belong in the flagship Gallery
surface. Future library selection belongs in `Settings > General`. Upload,
central-server synchronization, server media storage, and download-on-demand
remain unresolved separate product and architecture scope.
Tag editing should support suggestions, keyboard and mouse navigation,
rounded removable chips, an explicit `×` control, visible
hover/focus/selected/AI-suggested/invalid states, case-insensitive duplicate
prevention, and immediate local filtering without progress UI for trivial local
search.

## Visual And Interaction Direction

The primary gallery surface should emphasize media covers, readable titles,
availability, collection context, and quick filtering. Interaction should feel
polished and responsive, with restrained motion and truthful state changes.

"Wow-quality" in FrameNest means deliberate detail, strong cover presentation,
clear state, careful animation, and reduced friction. It does not mean fake
progress, excessive decoration, or obscuring metadata.

## Logical Item Cards

The gallery normally displays one logical media card rather than one duplicate
card per physical file. A card may summarize multiple known physical locations.
Users must be able to inspect the location list when needed.

Remote-only media cards should remain visible when metadata and covers are
available, even if the full media bytes are not stored locally.

## Location And Availability Badges

Cards should distinguish states such as:

- local and available;
- remote and available;
- known but offline;
- archived on server;
- missing;
- unverified;
- transferring;
- download available;
- stream available.

Badges must be clear without overwhelming the cover. The user should understand
whether an action will open local media, stream remote media, or require a
download.

## Covers And Thumbnails

Covers are durable user-visible representative images. Derived thumbnails are
cache artifacts derived from durable sources. Original approved covers and
reproducible derived thumbnails remain separate concepts.

Remote-only cards may use synchronized cover identity/provenance and derived
JPEG thumbnails. The full video must not be downloaded merely to render a card.

Normal `Play` is conceptually separate from cover timestamp selection. A cover
timestamp may represent a useful image; playback should still start at the
normal beginning unless the user chooses another playback action.

The future Cover Studio is manual-first: the user scrubs a timeline, sees the
exact current timestamp, previews the selected source frame, and explicitly
uses `Set as cover`. Cover candidates may later include a selected source frame,
the currently accepted cover, an imported image, or an AI-generated image. A
candidate is not active merely because it was created or generated; explicit
human acceptance is required. These rules are recorded in
[COVER_PIPELINE.md](COVER_PIPELINE.md) and
[ADR-0024](docs/adr/0024-cover-studio-and-ai-cover-candidates.md).

## MEME Collection Experience

GIF and short MP4 meme collections are first-class. The semantic canonical tag
or collection is `Meme`; the UI may style the collection label as `MEME`.

A future NUC-hosted MEME archive may allow a desktop to show the full MEME
collection through synchronized metadata and covers while storing few or none of
the media bytes locally. Remote-only meme cards should clearly identify remote
availability and offer explicit stream or download actions.

## Search And Filtering

The gallery must eventually support title/name search and canonical tag
filtering. The current packaged browser has a catalog slice that searches
persisted display titles, filters repeated canonical tags with
AND/intersection semantics, and lets the user manually edit the current
display title and ordered canonical-tag assignment for one selected imported
medium. Multiple selected tags default to AND/intersection semantics. For
example, selected tags `Meme`, `Reaction`, and `Money` normally return items
containing all three tags.

The UI should use filter chips and removable active filters. Filters should
include:

- canonical tags;
- local/remote availability;
- device;
- library;
- media kind;
- collection;
- platform/source where available.

The current packaged browser implements a virtual `All media` Catalog scope and
an optional built-in `Processed` Catalog scope that restricts the page to media
whose durable tag saves entered `Processed`. Arbitrary user-created collection
filters remain future work. A future advanced OR mode may exist, but AND is the
default.

## Preview And Playback

GIF and short-video inline preview should be supported separately from full
playback. Inline preview should be lightweight, respectful of reduced motion,
and should not replace the full playback backend.

External VLC remains the first intended full-playback direction for long videos.
Embedded libVLC remains deferred.

## Future Actions

Future card or detail actions may include:

- `Download`;
- `Stream`;
- `Download + Copy to Clipboard`;
- `Show locations`;
- `Reveal in Finder` or equivalent file manager;
- `Open in VLC`;
- `Edit metadata`;
- `Select cover`.

`Download + Copy to Clipboard` is a future native desktop capability for GIF and
short MP4 workflows. It must verify the downloaded representation before placing
it on the native clipboard and must provide fallbacks when direct paste is not
supported by the platform or target application.

## States

The gallery should define honest states for:

- initial loading;
- empty catalog;
- empty filter result;
- offline server;
- remote-only media;
- local unavailable media;
- transfer pending;
- transfer active;
- verification/finalization;
- transfer failed;
- media missing;
- cover missing;
- analysis pending;
- recoverable error.

State text should be actionable without exposing private paths, raw provider
responses, tokens, or raw diagnostics.

## Progress And Animation Rules

Determinate work should show real values when available: transferred bytes,
total bytes, percentage, speed, ETA, and verification/finalization state.

Indeterminate work may use restrained shimmer, masked text, pulse, or fade
animation. It must not show fabricated percentages, invented queue stages, or
false cancellation.

Reduced-motion users should receive static or simplified state changes.

## Accessibility

Gallery cards must support keyboard navigation, visible focus, meaningful
labels, screen-reader semantics, and non-color-only state distinctions. Tag
chips and active filters should be removable through keyboard and assistive
technology.

Inline previews must not autoplay in a way that violates reduced-motion
preferences. Motion should pause or simplify when requested.

## Performance Direction

The gallery should eventually support large libraries through lazy loading,
virtualization, cached derived thumbnails, incremental loading, and careful
state management. This document makes no unsupported numeric performance
promise.

## Boundary Model

Gallery metadata, media bytes, covers, and cache artifacts are separate:

- metadata describes logical media;
- physical locations describe where media bytes may exist;
- covers are durable selected representative images;
- derived thumbnails are reproducible cache artifacts;
- full media bytes are transferred, streamed, or opened only through explicit
  user actions or later approved automation.

This separation lets remote-only media remain visible without automatic full
byte replication.
