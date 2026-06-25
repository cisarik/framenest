# FrameNest Product Foundation

## 1. Product Identity

FrameNest is a local-first, privacy-conscious, cross-platform library for video and animated media. It is intended to help people acquire, organize, browse, preserve, and play media while keeping local ownership central.

FrameNest is not merely:

- A yt-dlp frontend.
- A file renamer.
- A basic gallery.
- A basic media player.
- A cloud-only media service.

Downloading, cataloging, gallery presentation, metadata, storage awareness, transfer, playback, and optional server aggregation are parts of one product direction.

## 2. Current Product Status

FrameNest is currently in foundation-stage, pre-alpha development.

A minimal Poetry package, runnable loopback FastAPI server, packaged local web shell, explicit SQLite migration foundation, local device and library registries, read-only library scan preview, explicit idempotent scan-candidate import into the minimum persistent media catalog, local media-analysis preview, provider-neutral NVIDIA suggestion prototype, bounded JPEG VLM transport, and explicit editable browser AI suggestion review now exist. The browser review is pre-alpha, opt-in, non-persistent, and does not apply catalog or filesystem changes.

There is still no completed media application, premium gallery, downloader, desktop shell, GUI Settings, automatic AI workflow, media mutation workflow, server aggregator, installer, deployment, or supported release. The persistent media catalog remains minimal: it can store logical media and physical locations from explicit scan-candidate import, but it does not yet include user-editable metadata, canonical tags, covers, thumbnails, title/tag search, or gallery data. Tauri v2 is accepted as the future desktop shell, but no Tauri scaffold exists yet. Development remains MacBook-first; later Intel NUC/Fedora work is still an optional aggregation and server phase, not a replacement for local desktop operation. This document defines approved product direction; it does not claim full product implementation.

## 3. Product Vision

The long-term goal is to provide a personal media library that can acquire media, organize it, present it through a premium gallery, preserve local ownership, and support multiple devices and storage locations.

FrameNest should allow users to keep useful media under their own control, understand where each copy exists, and access the collection through local desktop catalogs. An optional server aggregator may later coordinate global views, remote access, transfers, and centralized provider integrations.

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

### Optional Server Aggregation

FrameNest may use an optional server to aggregate catalogs, coordinate transfers, provide remote streaming, run remote downloads, centralize AI provider access, and support future backup functionality.

The optional server may support global gallery visibility for remote-only media through metadata, covers, availability summaries, and derived thumbnails without requiring automatic full media-byte replication.

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
- Future downloader adapters.
- Existing local video files.
- GIF files.
- Very short videos.
- Reaction media.
- Meme collections.
- Covers and generated thumbnails.

This scope describes product direction. It does not claim that all sources, formats, or workflows are currently supported.

## 8. Local-First Invariants

Desktop installations must remain useful without internet access.

Local gallery and local playback must not require the server.

Local metadata must remain available when the server is offline.

The Intel NUC server is optional for desktop operation.

Local clients must not become unusable thin clients.

Durable metadata should remain portable where feasible.

The normal desktop experience must not require Chrome, Brave, Firefox, Safari, or another external browser.

## 9. Server Role

The optional Intel NUC server is an aggregator, not a replacement for local desktop catalogs.

The server may later support:

- Global catalog views.
- Device and location awareness.
- Remote streaming.
- Remote download.
- Transfer coordination.
- Centralized AI provider access.
- Future backup functionality.

Server functionality must not make local desktop use dependent on server availability.

A priority future scenario is a NUC-hosted `Meme` archive where a desktop can browse and search remote-only GIF and short MP4 media through synchronized metadata and covers, then explicitly stream or download selected media.

## 10. Logical Media and Physical Locations

FrameNest should distinguish logical media from physical locations.

One logical media item may have zero or more series relationships and may exist in multiple physical locations. Those locations may be on different devices, libraries, or storage volumes.

One gallery item should normally represent the logical media item rather than displaying every duplicate independently. The user should still be able to inspect where each physical copy exists.

FrameNest should use selective media placement. It must not automatically replicate all media bytes to every device.

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

For GIF and short MP4 social-response workflows, FrameNest should later support `Download + Copy to Clipboard` through native desktop capabilities with clear fallback behavior when direct paste is unsupported.

## 17. Privacy and AI Assistance

AI features are optional.

Cloud operations are opt-in, and users should understand what is sent before it is sent.

Provider keys should remain on the server where possible. Ordinary clients should not receive provider secrets.

Suspicious filenames may be manually analyzed, but AI suggestions require confirmation. Current pre-alpha AI suggestion review is editable, session-only, and not catalog truth.

FrameNest must not automatically rename media or upload frames without user intent and confirmation.

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

Agent and protocol behavior are defined in [AGENTS.md](AGENTS.md) and [AP.md](AP.md).

[SPEC.md](SPEC.md) defines normative product and system requirements.

[ROADMAP.md](ROADMAP.md) defines the staged, evidence-based development plan.

This document defines product direction. `SPEC.md` defines normative requirements. `ROADMAP.md` defines staged development. Architecture ADRs record accepted architecture decisions.

Permanent architecture and UX references:

- [DESKTOP.md](DESKTOP.md) records accepted desktop shell direction.
- [SERVER.md](SERVER.md) records accepted optional server and NUC aggregation direction.
- [GALLERY.md](GALLERY.md) records accepted gallery product and UX direction.
- [AI_WORKSPACE.md](AI_WORKSPACE.md) records accepted manual-first metadata and multi-model AI workspace direction.
- [COVER_PIPELINE.md](COVER_PIPELINE.md) records accepted Cover Studio and cover candidate direction.
- [ADR-0021](docs/adr/0021-tauri-desktop-shell.md) records the accepted Tauri desktop shell decision.
- [ADR-0022](docs/adr/0022-selective-media-placement-and-server-aggregation.md) records selective placement and server aggregation decisions.
- [ADR-0023](docs/adr/0023-manual-first-metadata-and-multi-model-ai-drafts.md) records manual-first metadata and multi-model AI draft decisions.
- [ADR-0024](docs/adr/0024-cover-studio-and-ai-cover-candidates.md) records Cover Studio and AI cover candidate decisions.
