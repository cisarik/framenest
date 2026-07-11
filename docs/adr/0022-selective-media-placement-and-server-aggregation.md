# ADR-0022: Selective Media Placement and Server Aggregation

## Status

`Accepted`

Server-authority portions are superseded by
[ADR-0035](0035-authoritative-server-and-client-state-model.md). This ADR
remains accepted for selective media placement, remote-only visibility, explicit
transfer/open/download semantics, final-copy safeguards, and application
authorization above Tailscale.

## Decision Date

`2026-06-25`

## Decision Authority

The Cooperator accepted the distributed media direction through task
`FRAMENEST-CYCLE-061-DESKTOP-DISTRIBUTED-MEDIA-ARCHITECTURE-AND-WORKER-CLOSEOUT`.

## Context

FrameNest is local-first and cross-platform. The product direction includes a
premium gallery, desktop operation, multiple devices, multiple libraries, and an
optional Intel NUC server role. The repository currently implements only the
foundation through local device and library registries, read-only scan preview,
local media-analysis preview, and non-persistent editable AI suggestion review.
It does not yet implement a persistent media catalog, logical media records,
physical media-location records, cover persistence, thumbnail cache, transfer
protocol, streaming, synchronization, or server deployment.

The Cooperator has accepted a future scenario where the NUC can hold archive or
preferred media bytes for GIF and short MP4 meme collections while another
desktop still shows a useful global gallery through synchronized metadata and
covers. This requires selective placement rather than automatic all-device media
replication.

## Decision

Each desktop installation was originally described here as owning a complete
local catalog sufficient for local operation. ADR-0035 supersedes that
authority model: a FrameNest server process is authoritative for catalog and
server-owned state, and browser, desktop, and remote interfaces are clients of
that server API. The server process may run locally on the same device as the
desktop client, so local-first operation and local ownership remain intact.

The future Intel NUC remains optional for local ownership and may host the
authoritative FrameNest server once deployment is accepted. It may act as:

- an aggregator;
- an archive or storage node;
- a global catalog aggregation point;
- a remote streaming and download source;
- a receiver for explicit copy, move, or archive operations;
- a later centralized AI-provider boundary;
- a future backup participant.

The NUC is not mandatory public-cloud infrastructure and must not turn local
FrameNest ownership into SaaS dependence. Server functionality must not make
local desktop operation unusable when the needed local server process, cached
records, and local media are available.

FrameNest models one logical media item with zero or more known physical media
locations. The gallery normally displays one logical media card, not one
duplicate card per physical copy. A physical location may be local and
available, remote and available, known but offline, archived on the NUC, missing,
or unverified.

Global gallery visibility may synchronize or cache metadata and cover data
without replicating full media bytes. Remote-only cards should remain visually
useful through title, description, collection, canonical tags, availability and
location summaries, cover identity and provenance, and appropriately sized
derived JPEG thumbnails. The full video must not be downloaded merely to render
its gallery card.

FrameNest must not automatically replicate all media bytes to every device.
Full media transfer must be explicit or governed by a later explicitly accepted
automation rule.

Future user actions may include:

- `Copy to server`;
- `Move to server`;
- `Archive on server`;
- `Download to this device`;
- `Stream from server`;
- `Show locations`.

A move operation must not delete the source until the destination copy is
verified, readable, and registered. Transport, resumability, chunking, hashing,
authorization, conflict handling, and synchronization protocols remain deferred.

The gallery must eventually support title/name search, canonical tag filtering,
selection of multiple tags simultaneously, local/remote availability filtering,
device and library filtering, and media-kind filtering. Multiple selected tags
default to AND/intersection semantics. For example, selecting `Meme`, `Reaction`,
and `Money` should normally return items containing all three tags. A future
advanced OR mode may be added, but AND is the default approved behavior.

The priority MEME scenario is:

- the NUC contains authoritative or preferred archive copies of the user's GIF
  and short MP4 meme collection;
- another desktop may not store those media bytes locally;
- opening FrameNest on that desktop still shows the complete MEME collection
  using synchronized catalog metadata and covers;
- remote-only media cards visibly identify their availability and location;
- the user can search and filter them;
- the user can explicitly stream or download a selected item.

The semantic canonical tag or collection is `Meme`. The UI may visually style
the collection label as `MEME`. This ADR does not decide final database casing
or identifier encoding.

For GIF and short MP4 media, `Download + Copy to Clipboard` is accepted as a
future native desktop capability. For remote media this means obtaining the
selected media through an explicit bounded download, verifying the local
downloaded representation is complete, placing a platform-appropriate file or
image representation on the native clipboard, and presenting a clear fallback
when the platform or target application does not support the payload. Fallbacks
may include keeping the downloaded file, revealing it in the file manager, or
allowing drag-and-drop/manual upload. Universal direct-paste compatibility is
not claimed.

Remote access direction remains Tailscale-only unless explicitly superseded by a
later accepted decision.

## Why Not Implement NUC Aggregation Now

NUC aggregation depends on a local media catalog model that does not exist yet.
FrameNest must first implement logical media, physical media locations,
canonical tags, covers, derived thumbnails, search-ready local data, and safe
local import from explicit scan results. Starting with NUC aggregation would
force premature schema, transfer, synchronization, cache, conflict, and security
decisions before the local catalog behavior is testable.

The strongest next implementation candidate remains the minimum persistent
local media catalog on MacBook. NUC deployment, aggregation, streaming, and
transfer should follow only after local catalog and gallery foundations exist.

## Security Consequences

Selective placement avoids unnecessary full-byte replication. Remote operations
must be explicit, authorized, and auditable. Server availability must not be
required for local use. Future remote access must use Tailscale in the approved
direction, but application-level authorization remains required.

Remote-only cards must not expose private absolute paths, provider secrets,
authorization tokens, or raw diagnostics. Transfer and stream endpoints require
later dedicated security decisions.

## Deferred Decisions

This ADR does not decide:

- persistent media catalog schema;
- physical-location table structure;
- storage-volume model;
- sidecar schema;
- synchronization protocol;
- transfer protocol;
- resumability and chunking;
- checksum or hashing algorithm;
- conflict rules;
- cache invalidation;
- cover synchronization protocol;
- thumbnail sizes and formats;
- server authorization model;
- Tailscale Serve configuration;
- Fedora deployment and systemd service layout;
- remote streaming transport;
- platform clipboard representations;
- temporary download cleanup lifecycle;
- target-application clipboard compatibility.

## Artifact Lifecycle

Classification: permanent normative architecture decision.

Consumers: future Orchestrator and Worker instances, maintainers, catalog
implementers, gallery implementers, server implementers, transfer implementers,
and security reviewers.

Retention: retained permanently; superseded only by a later accepted ADR.

Inbound links: ADR index, [SERVER.md](../../SERVER.md),
[GALLERY.md](../../GALLERY.md), [PRODUCT.md](../../PRODUCT.md),
[SPEC.md](../../SPEC.md), [ROADMAP.md](../../ROADMAP.md), and
[README.md](../../README.md).

Cleanup owner: future explicitly authorized Worker only through a superseding
ADR.

## Related Documents

- [ADR index](README.md)
- [ADR-0010](0010-initial-persistence-foundation.md)
- [ADR-0011](0011-stable-domain-identities.md)
- [ADR-0013](0013-initial-library-registry.md)
- [ADR-0021](0021-tauri-desktop-shell.md)
- [ADR-0035](0035-authoritative-server-and-client-state-model.md)
- [DESKTOP.md](../../DESKTOP.md)
- [SERVER.md](../../SERVER.md)
- [GALLERY.md](../../GALLERY.md)
- [PRODUCT.md](../../PRODUCT.md)
- [SPEC.md](../../SPEC.md)
- [ROADMAP.md](../../ROADMAP.md)
