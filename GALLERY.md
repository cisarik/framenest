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
and [ADR-0021](docs/adr/0021-tauri-desktop-shell.md).

Cleanup/update owner: future explicitly authorized Worker under an Orchestrator
task. Git history remains the archive.

## Flagship Role

The gallery is a flagship FrameNest capability. It should be premium, dark,
cover-first, fast, and useful for large personal collections. The current
repository does not yet implement the persistent media catalog, cover pipeline,
derived thumbnails, search, or real gallery.

The gallery should feel like a media product, not a generic administrative
dashboard.

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

## MEME Collection Experience

GIF and short MP4 meme collections are first-class. The semantic canonical tag
or collection is `Meme`; the UI may style the collection label as `MEME`.

A future NUC-hosted MEME archive may allow a desktop to show the full MEME
collection through synchronized metadata and covers while storing few or none of
the media bytes locally. Remote-only meme cards should clearly identify remote
availability and offer explicit stream or download actions.

## Search And Filtering

The gallery must eventually support title/name search and canonical tag
filtering. Multiple selected tags default to AND/intersection semantics. For
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

A future advanced OR mode may exist, but AND is the default.

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
