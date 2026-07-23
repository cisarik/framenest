# FrameNest Product Foundation

## 1. Product Identity

FrameNest is a local-first, privacy-conscious, cross-platform library for video and animated media. It is intended to help people acquire, organize, browse, preserve, and play media while keeping local ownership central.

FrameNest is not merely:

- A yt-dlp frontend.
- A file renamer.
- A basic gallery.
- A basic media player.
- A cloud-only media service.

Downloading, cataloging, gallery presentation, metadata, storage awareness,
transfer, playback, and server/client coordination are parts of one product
direction.

## 2. Current Product Status

FrameNest is currently in foundation-stage, pre-alpha development.

A minimal Poetry package, runnable loopback FastAPI server, packaged local web shell, explicit SQLite migration foundation, local device and library registries, read-only library scan preview, explicit idempotent scan-candidate import into the minimum persistent media catalog, persistent display-title and canonical-tag core, local media-analysis preview, provider-neutral NVIDIA suggestion prototype, bounded JPEG VLM transport, explicit editable browser AI suggestion review, and owner-operated cookie-free YouTube manual ingestion now exist. YouTube ingestion is CLI-only, durable, loopback-only, and reuses the existing quarantine, validation, byte-identity, publication, and catalog lifecycle.

There is still no completed media application, premium gallery, generalized downloader UI,
desktop shell, GUI Settings, broad automatic AI workflow beyond optional
server-enabled post-catalog analysis, media mutation workflow,
deployed server, installer, or supported release. The persistent media catalog
remains minimal: it can store logical media and physical locations from
explicit scan-candidate import plus a user-editable display title and ordered
canonical content tags. Canonical tag keys are stable English identifiers, and
display titles remain separate from physical filenames. Display-title search
and canonical-tag AND filtering exist in the catalog browser. A manual browser
metadata workspace exists for display title, optional plain-text description,
and ordered canonical tags. An automatic built-in `Processed` workflow
collection is derived from durable metadata saves containing at least one
canonical tag: the first such save records a `processed_at_ms` tagging
timestamp, non-empty tag edits and title/description edits preserve it, and
removing all tags clears Processed membership and the timestamp. The catalog
does not yet include arbitrary user-created collections, a general collection
manager, suggested filenames, covers, thumbnails, gallery data, or filesystem
rename workflows. Tauri v2 is accepted as the future desktop shell, but no
Tauri scaffold exists yet. Development remains MacBook-first; Ubuntu Server
24.04 on the Intel NUC6i5SYH is now the current personal production server
preparation target for a future authoritative FrameNest server. This document
defines approved product direction; it does not claim full product
implementation.

## 3. Product Vision

The long-term goal is to provide a personal media library that can acquire media, organize it, present it through a premium gallery, preserve local ownership, and support multiple devices and storage locations.

FrameNest should allow users to keep useful media under their own control,
understand where each copy exists, and access the collection through clients of
an authoritative FrameNest server process. That server process may run locally
on the same device as the desktop client or later on the Ubuntu NUC. This is
not a public cloud or SaaS requirement.

The normal user experience should be a native desktop application rather than a manually opened external browser. Browser mode remains useful for development and diagnostics.

Privacy-aware AI assistance may be added later for tasks such as metadata suggestions, suspicious filename analysis, tagging support, and cover generation, but such features must remain optional and user-controlled.

## 4. Product Pillars

### Media Acquisition

FrameNest should support safe acquisition of media from external sources and local imports. Downloading is a flagship product capability, not an auxiliary utility.

### Intelligent Organization and Tagging

FrameNest should help users organize media with canonical metadata, tags, series relationships, source information, and durable local records.

### Premium Visual Gallery

FrameNest should provide a visually premium gallery as a flagship capability. The gallery should make large personal media libraries fast, attractive, searchable, and understandable.

The gallery should support title search, removable filter chips, and multiple selected canonical tags with default AND/intersection semantics.

### Local-First Ownership

FrameNest should keep local desktop operation useful without requiring a server, cloud account, or public backend.

### Multi-Device Cataloging

FrameNest should represent media across multiple devices, libraries, disks, and storage volumes while keeping one logical media item distinct from its physical copies.

### Safe Transfer and Remote Playback

FrameNest should support careful movement, copying, and remote playback of media with clear status, verified destinations, and explicit confirmation before destructive actions.

Determinate operations such as downloads and transfers should eventually show real bytes, percentages, speed, ETA, and verification/finalization state when available. Indeterminate operations may use restrained premium animation but must not invent percentages or backend stages.

### Authoritative Server and Clients

FrameNest uses a server/client architecture. The FrameNest server process is
authoritative for catalog records and server-owned state. Browser, desktop, and
remote interfaces are clients of that server API.

The server may run locally for a desktop installation or later on the Intel NUC
personal production server. It may coordinate catalog state, transfers, remote
streaming, remote downloads, centralized AI provider access, and future backup
functionality.

The server may support global gallery visibility for remote-only media through
metadata, covers, availability summaries, and derived thumbnails without
requiring automatic full media-byte replication.

### Privacy-Aware AI Assistance

FrameNest may later provide AI-assisted metadata, cover, and organization workflows. These workflows must be optional, understandable, and confirmation-based.

AI assistance does not own metadata. Manual display-title, description,
collection, canonical-tag, and suggested-filename editing must remain complete
without AI, without internet, and after the user rejects all AI drafts. Future
multi-model AI drafts are comparison aids that may be promoted into the manual
`Current` working state only by explicit action; promotion is not a catalog save
and does not mutate files.

## 5. Target Users and Use Cases

Target users include:

- People maintaining personal educational video archives.
- Users downloading and organizing long-form videos.
- Users managing GIF, reaction, and meme collections.
- Users with media distributed across several computers and disks.
- Users who want local ownership with optional remote access.

This document does not claim validated market demand, market size, or customer statistics.

## 6. Core User Outcomes

FrameNest should help users:

- Find media quickly.
- Understand where every physical copy exists.
- Download and organize new media safely.
- View media through a visually premium gallery.
- Select and maintain covers.
- Move or copy media between devices.
- Play local or remote media.
- Recover useful metadata when a device is offline.
- Avoid dependence on one cloud vendor.

## 7. Media Scope

The intended media scope includes:

- Standalone videos.
- Series and episodes.
- YouTube media.
- Movies with explicit language metadata where useful.
- Future downloader adapters.
- Existing local video files.
- GIF files.
- Very short videos.
- Reaction media.
- Meme collections.
- Covers and generated thumbnails.

This scope describes product direction. It does not claim that all sources, formats, or workflows are currently supported.

Future first-class categories include `memes`, `youtube`, and `movies`.
Categories are a dedicated catalog facet rather than only tags or directory
names. Movie language metadata should prefer container or audio metadata and
user editing before expensive AI analysis, and FrameNest must not automatically
upload audio to a cloud provider.

## 8. Local-First Invariants

Desktop installations must remain useful without internet access.

Local gallery and local playback must remain useful when the needed local
server process, local catalog/cache state, and local media are available.

The Intel NUC server is optional for local ownership. A desktop client may use
a local FrameNest server process rather than a remote NUC.

Local clients must not become unusable public-cloud thin clients.

Durable metadata should remain portable where feasible.

The normal desktop experience must not require Chrome, Brave, Firefox, Safari, or another external browser.

## 9. Server Role

The FrameNest server process is authoritative for catalog records, server media
originals, canonical title, description, and tags, future category and language
metadata, per-user visibility state, upload and ingest state, server preview
cache, authentication, and capability decisions.

Browser, desktop, and remote interfaces are clients. They must not infer
administrator authority from loopback, source IP, hostname, Tailscale
membership, cookies, or same-machine execution.

The Intel NUC may later host the authoritative server, but it is not required
for local ownership and is not yet deployed.

The server may later support:

- Global catalog views.
- Device and location awareness.
- Remote streaming.
- Remote download.
- Transfer coordination.
- Centralized AI provider access.
- Future backup functionality.

Server functionality must not make local ownership dependent on public cloud
availability. Offline client caching and synchronization remain future design
work.

A priority future scenario is a NUC-hosted `Meme` archive where a desktop can browse and search remote-only GIF and short MP4 media through synchronized metadata and covers, then explicitly stream or download selected media.

## 10. Logical Media and Physical Locations

FrameNest should distinguish logical media from physical locations.

One logical media item may have zero or more series relationships and may exist in multiple physical locations. Those locations may be on different devices, libraries, or storage volumes.

One gallery item should normally represent the logical media item rather than displaying every duplicate independently. The user should still be able to inspect where each physical copy exists.

FrameNest should use selective media placement. It must not automatically replicate all media bytes to every device.

Future upload, catalog synchronization, explicit client cache/download,
per-user Trash, server deletion requests, global retirement, and physical purge
of originals are separate operations. Server-managed upload must quarantine,
validate, limit, safely name, de-duplicate, atomically publish, clean up
failures, and choose server placement; clients must not select arbitrary server
filesystem paths. Per-user Trash is server-persisted visibility state and must
not delete the server original.

## 11. Library and Storage Experience

FrameNest should support multiple independent libraries with stable library identities.

The user experience should make storage and device availability visible. It should support free-space reporting, capacity visualization, filtering by library and device, `All libraries` views, and global views across available catalogs.

The product should help users understand not only what media they have, but also where it is and whether the relevant storage is currently available.

## 12. Premium Gallery Experience

The gallery should be visually premium, dark, responsive, cover-driven, fast, and scalable to large libraries. It should be usable by keyboard, mouse, and touch, and it should support accessibility needs.

The gallery should be able to reduce motion and visual effects on weaker devices.

Remote-only media cards should remain visually useful through metadata, cover identity/provenance, derived thumbnails, and visible location/availability badges. Rendering a card should not require downloading the full video.

Important gallery concepts include:

- Media cards.
- Series cards.
- Cover editing.
- Device and availability indicators.
- Remote-only cards.
- Inline short-media previews.
- Title search.
- Multi-tag AND filtering.
- Lazy loading and virtualization.

This document does not select a frontend framework.

## 13. Downloading and Acquisition Experience

Downloading and acquisition should provide source inspection, metadata preview, format selection policies, progress, cancellation, safe temporary state, finalization verification, structured errors, collision-safe names, and reusable downloader adapters.

yt-dlp is the intended first adapter, but it must not be coupled directly to domain logic. The product direction is adapter-based acquisition so future sources can be added without making one downloader tool the domain model.

## 14. Naming and Tagging

Canonical tags are English.

Tags appear at the end of directory names.

The source platform is the final system tag.

FrameNest should support standalone and series directory models.

Series-level content tags may be inherited by episodes where appropriate.

Operating-system tags are synchronized projections.

The FrameNest catalog remains authoritative.

Approved example:

```text
Reinventing Entropy - Compression is Intelligence [Math] [Compression] [YouTube]
```

## 15. Cover Experience

FrameNest should support timeline frame selection, importing a cover from disk, series and episode covers, durable original covers, and reproducible derived thumbnails.

Manual cover selection comes before AI cover generation. Future Cover Studio
should let the user select a source frame and explicitly set it as cover while
retaining an exact cover timestamp. Future AI-generated covers are roadmap
scope, must create reviewable cover candidates, and must require explicit human
acceptance before replacing covers.

The product should preserve enough information to regenerate derived thumbnails while retaining user-approved original cover choices.

## 16. Playback Experience

FrameNest should support external VLC first for full playback.

Playback direction includes local file playback, remote stream playback, inline looping previews for GIFs and short clips, and a clear separation between full playback and inline preview.

Embedded libVLC is future roadmap scope, not an early-stage implemented capability.

Future playback should support fullscreen and truthful audio-track selection
where technically supported. FrameNest should use capability detection and
fallback rather than fake controls. Subtitle support is not currently required,
and FrameNest must not silently transcode originals.

For GIF and short MP4 social-response workflows, FrameNest should later support `Download + Copy to Clipboard` through native desktop capabilities with clear fallback behavior when direct paste is unsupported.

## 17. Privacy and AI Assistance

AI features are optional.

Cloud operations are opt-in, and users should understand what is sent before it is sent.

Provider keys should remain on the server where possible. Ordinary clients should not receive provider secrets.

Ordinary clients should not configure provider credentials or call providers
directly. Browser status and results must be sanitized. Production
provider-secret integration remains unresolved.

Suspicious filenames may be manually analyzed, but AI suggestions require confirmation. Current pre-alpha AI suggestion review is editable, session-only, and not catalog truth.

FrameNest must not automatically rename media.

FrameNest must not automatically upload media or prepared frames to a cloud
provider merely because media was cataloged: automatic cloud analysis stays
off by default and is permitted only after the explicit server-owner or
administrator opt-in `FRAMENEST_AUTOMATIC_MEDIA_ANALYSIS_ENABLED=true`, which
represents standing consent only for eligible automatic post-catalog analysis
on that server. That enablement does not authorize historical bulk analysis,
arbitrary external URL retrieval, user-provided provider keys, hidden provider
fallback, analysis before cataloging, or uploading unrelated personal files.
Interactive on-demand suggestion preview continues to require explicit
per-request confirmation such as `confirm_cloud_upload: true`. Ordinary users
do not supply provider credentials; credentials remain server-side.

## 18. Security Principles

FrameNest must keep secrets out of Git.

Backend services must not be publicly exposed by default.

Remote functions follow a Tailscale-only direction unless explicitly superseded by an approved decision.

Application-level authorization remains necessary even when the network boundary is private.

FrameNest should use least privilege, explicit confirmation for destructive actions, and verified destination state before source deletion.

## 19. Experience Principles

FrameNest should feel premium but restrained.

Interactions should be fast, status should be clear, and complexity should appear through progressive disclosure rather than crowded screens.

The interface should support accessibility and reduced-motion preferences.

FrameNest should avoid outdated generic desktop-widget appearance and avoid visual effects that damage responsiveness.

The future desktop shell should provide single-instance behavior, a tray or macOS menu-bar presence, close-to-tray behavior, and initial `Gallery`, `Settings`, and `Quit` menu items.

## 20. Early Product Non-Goals

Early product non-goals include:

- Complete Android or iOS application.
- Public internet hosting.
- Cloud backup.
- Server-side transcoding infrastructure.
- Embedded libVLC.
- AI-generated covers.
- Automatic multi-device synchronization.
- Support for every downloader platform.
- Multi-user SaaS.

These may be reconsidered only through explicit future decisions.

## 21. Success Criteria for the First Functional Vertical Slice

A future first functional vertical slice should prove a coherent local workflow:

- Registering a local library.
- Importing or downloading one media item.
- Storing portable metadata.
- Indexing it locally.
- Displaying it in a real gallery.
- Applying canonical tags.
- Generating or selecting a cover.
- Opening it through the playback backend.
- Proving exact filesystem and metadata behavior with tests.

This vertical slice is future work. It is not currently implemented.

## 22. Open Product Questions

Open product questions include:

- What is the minimum useful first library setup experience?
- Which media fields must be user-editable in the first vertical slice?
- How should duplicate physical copies be summarized in the gallery without hiding important storage information?
- What is the safest user experience for move, copy, and delete workflows across devices?
- Which cover-editing features are essential before AI-generated covers are considered?
- What level of remote playback should be part of the first server-backed experience?
- How should meme, GIF, and very short video collections be grouped without making them feel secondary to long-form video?

## 23. Relationship to Other Documents

This document complements the repository overview in [README.md](README.md).

Agent and protocol behavior is defined by [AGENTS.md](AGENTS.md) and the
pinned canonical AP submodule beginning at [`.ap/AP.md`](.ap/AP.md).
FrameNest's AP integration decision is recorded in
[ADR-0034](docs/adr/0034-canonical-analytic-programming-integration.md).

[SPEC.md](SPEC.md) defines normative product and system requirements.

[ROADMAP.md](ROADMAP.md) defines the staged, evidence-based development plan.

This document defines product direction. `SPEC.md` defines normative requirements. `ROADMAP.md` defines staged development. Architecture ADRs record accepted architecture decisions.

Permanent architecture and UX references:

- [DESKTOP.md](DESKTOP.md) records accepted desktop shell direction.
- [SERVER.md](SERVER.md) records accepted authoritative server/client and NUC direction.
- [GALLERY.md](GALLERY.md) records accepted gallery product and UX direction.
- [AI_WORKSPACE.md](AI_WORKSPACE.md) records accepted manual-first metadata and multi-model AI workspace direction.
- [COVER_PIPELINE.md](COVER_PIPELINE.md) records accepted Cover Studio and cover candidate direction.
- [ADR-0021](docs/adr/0021-tauri-desktop-shell.md) records the accepted Tauri desktop shell decision.
- [ADR-0022](docs/adr/0022-selective-media-placement-and-server-aggregation.md) records selective placement decisions.
- [ADR-0035](docs/adr/0035-authoritative-server-and-client-state-model.md) records the authoritative server/client state model.
- [ADR-0023](docs/adr/0023-manual-first-metadata-and-multi-model-ai-drafts.md) records manual-first metadata and multi-model AI draft decisions.
- [ADR-0024](docs/adr/0024-cover-studio-and-ai-cover-candidates.md) records Cover Studio and AI cover candidate decisions.
