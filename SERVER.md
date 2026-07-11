# FrameNest Server and Client Architecture

## Status

This is a living permanent product architecture reference. It records accepted
future server/client direction; it does not claim that NUC deployment,
streaming, synchronization, upload, per-user visibility state, authentication,
or transfer is currently implemented.

Classification: living permanent product architecture/UX reference.

Consumers: Orchestrator, Worker, designers, implementers, maintainers, and
security reviewers.

Retention: remains while the server product subsystem exists.

Inbound links: [README.md](README.md), [PRODUCT.md](PRODUCT.md),
[SPEC.md](SPEC.md), [ROADMAP.md](ROADMAP.md),
[ADR-0022](docs/adr/0022-selective-media-placement-and-server-aggregation.md),
[ADR-0035](docs/adr/0035-authoritative-server-and-client-state-model.md),
and [ADR-0021](docs/adr/0021-tauri-desktop-shell.md).

Cleanup/update owner: future explicitly authorized Worker under an Orchestrator
task. Git history remains the archive.

## Server Authority

ADR-0035 records the current server/client authority model. A FrameNest server
process is authoritative for:

- catalog records;
- server media originals;
- canonical title, description, and tags;
- future category and language metadata;
- per-user visibility state;
- upload and ingest state;
- server preview cache;
- authentication and capability decisions.

Browser, desktop, local NUC browser, and future remote interfaces are clients
of that server API. The server process may run locally on the same device as a
desktop client or later on the Ubuntu NUC. Local-first operation means FrameNest
can be owned and run locally without public cloud dependence; it does not mean
each client interface owns an independent authoritative catalog.

Ordinary clients may request catalog state and may explicitly stream, open, or
download authorized media. They must not mutate arbitrary server files and must
not infer administrator authority from loopback, source IP, hostname, Tailscale
membership, cookies, or same-machine execution.

## NUC Role

The Intel NUC is the current concrete personal production server preparation
target for a future authoritative FrameNest server and archive-node role. It is
not required for local ownership and must not make FrameNest a public-cloud or
SaaS dependency.

The NUC may later provide:

- authoritative catalog serving;
- archive or preferred storage for selected media bytes;
- remote streaming and download;
- transfer coordination;
- explicit archive/copy/move destinations;
- centralized provider access for AI workflows;
- future backup participation.

Ubuntu Server 24.04 on the Intel NUC6i5SYH supersedes Fedora as the active
deployment target. A repository-native systemd service foundation and Ubuntu
NUC deployment-readiness runbook now exist, but real host installation,
activation, NUC acceptance, Tailscale Serve, AppArmor/UFW policy,
production database replacement, media backup, secret recovery, and
authentication remain unimplemented. The minimum catalog backup and
restore-to-new-destination foundation is documented in
[docs/BACKUP_AND_RECOVERY.md](docs/BACKUP_AND_RECOVERY.md).
Sanitized command-observed NUC hardening and media-storage baseline facts are
preserved in [docs/NUC_HOST_BASELINE.md](docs/NUC_HOST_BASELINE.md); that
baseline is not host mutation authority or FrameNest deployment acceptance.

## Same Core, Different Deployment Capabilities

Desktop and server roles should reuse the same FrameNest domain and application
core. They are not separate products. Deployment role decides which adapters,
native capabilities, supervision, storage, and networking are available.

The desktop owns native interactive capabilities such as system WebView
presentation, file pickers, notifications, file-manager reveal, clipboard
integration, and future playback handoff. The server owns catalog and
server-state authority.

## Local Operation And Server State

Local desktop operation should remain useful when the required local server
process, local catalog/cache records, and local media are available. The Intel
NUC is optional for local ownership, because a desktop installation may run its
own local FrameNest server process.

Offline client caching and synchronization rules remain unresolved. A client
must distinguish stale cached records, unavailable server state, and unavailable
media bytes rather than pretending it still has authoritative live state.

## Metadata And Cover Aggregation

Remote-only media cards should be visible without full media-byte replication.
The server may provide:

- logical media metadata;
- titles and descriptions;
- canonical tags;
- collection labels;
- availability and location summaries;
- cover identity and provenance;
- derived JPEG thumbnails sized for gallery use.

Original covers and reproducible derived thumbnails remain separate concepts.
The full video must not be downloaded merely to render a gallery card.

## Location And Availability Tracking

FrameNest models one logical media item with zero or more physical locations.
Locations may be local, remote, archived, offline, missing, or unverified.

Users must be able to inspect where a media item is known to exist. Remote-only
cards should clearly show that playback or copy requires a remote operation.

## Selective Media Placement

FrameNest must not automatically mirror all media bytes to every device.
Metadata, tags, covers, availability state, and lightweight thumbnails may
synchronize independently of full media bytes. Full media transfer must be
explicit or governed by a later accepted automation rule.

Future actions may include:

- `Archive on server`;
- `Copy to server`;
- `Move to server`;
- `Download to this device`;
- `Stream from server`;
- `Show locations`.

## Remote Streaming Direction

Remote streaming may later allow a desktop to play server-hosted media without
first storing a permanent local copy. Streaming must use authorized local or
remote URLs through the playback abstraction. External VLC remains the first
intended full-playback backend.

The exact streaming transport, authorization, buffering, range behavior, and
failure states remain deferred.

## Transfer Safety

Transfers must be explicit and safe. Move operations must not delete the source
until the destination copy is verified, readable, and registered. Transfer UI
should eventually show real determinate progress where available: bytes,
percentage, speed, ETA, and verification/finalization state.

Partial failures must be recoverable and must not silently remove the last known
valid copy.

## Service Unavailability Behavior

When a remote server is unavailable, remote-only items may become unavailable
for stream/download, but their known metadata and cover summaries should remain
visible if previously synchronized or cached.

The UI must distinguish offline server state from stale cached records, missing
local catalog/cache data, and unavailable media bytes.

## Upload, Synchronization, Cache, And Trash Direction

Future work must keep these operations separate:

- catalog synchronization;
- authenticated server-managed media ingest or upload;
- explicit client cache or download;
- per-user visibility state such as Hide or Trash;
- global retirement or physical purge of originals.

Future upload must require quarantine, content validation, limits, safe
filenames, duplicate detection, atomic publication, cleanup after failure, and
server-selected placement. Clients must not choose arbitrary server filesystem
paths.

Per-user Trash is server-persisted visibility state and must not delete the
server original. Separate future operations may include `Remove from this
managed client`, `Hide or Trash for this user`, `Request server deletion`,
`Retire globally`, and `Purge physical originals`.

## Category, Language, And Playback Direction

Future first-class categories include `memes`, `youtube`, and `movies`.
Categories are a dedicated catalog facet, not merely canonical tags or
operational directory names.

Movies may carry explicit language metadata such as English, Slovak, or Czech.
Prefer container or audio metadata and user editing before expensive AI
analysis. Do not automatically upload audio to a cloud provider.

Future playback should support fullscreen and truthful audio-track selection
where technically supported. Use capability detection and fallback instead of
fake controls. Subtitle support is not currently required. Do not silently
transcode originals.

## Network And Deployment Direction

Future remote access remains Tailscale-only unless superseded by a later
accepted decision. FrameNest must not require router port forwarding or public
internet exposure. Tailscale networking is not sufficient authorization by
itself; application-level authorization remains required.

The historical Fedora service foundation is recorded in
[ADR-0031](docs/adr/0031-fedora-systemd-service-foundation.md). It is
superseded for the active deployment target by
[ADR-0032](docs/adr/0032-ubuntu-nuc-deployment-foundation.md) and the current
[Ubuntu NUC deployment runbook](docs/UBUNTU_NUC_DEPLOYMENT.md). Do not describe
a real NUC deployment as completed until a later host-acceptance task verifies
it.

## Server-Side AI Provider Boundary

FrameNest now has an initial server-operated AI provider boundary for the local
development server. Ordinary browser and desktop clients do not configure
providers, select models, enter API keys, receive provider credentials, or call
NVIDIA, Vercel, Google, or another provider directly. Browser clients may view
sanitized read-only server AI status and may explicitly request AI analysis
through the FrameNest server when a provider is configured.

Server operators use the root CLI:

```text
./framenest ai status
./framenest ai configure
./framenest ai test
```

`status` is network-free and writes only a safe status snapshot beside the
non-secret AI configuration state. `configure` writes only schema-versioned
non-secret provider/model selection outside the repository, using the platform
application configuration location or an explicit configuration-path override.
`test` is an explicit minimal text-only provider request and persists only safe
historical test category/timestamp state. NVIDIA NIM remains supported. Vercel
AI Gateway is supported with preferred model `google/gemini-3.1-flash-lite`.

The browser Status modal is read-only. Its AI tab shows the configured provider
and model plus safe historical status rows when such state exists. Its Cloud tab
uses the sanitized server status contract and reports the local development
server as connected over loopback; it does not implement Tailscale detection or
authorization.

In development, provider credentials remain in the server process environment:
`NVIDIA_API_KEY` for NVIDIA NIM and `AI_GATEWAY_API_KEY` for Vercel AI Gateway.
Production provider-secret integration is not implemented by the Ubuntu service
foundation. Persistent secret storage, OS keychain integration, systemd
credential files, browser provider Settings, service-secret adapters, and
application-level remote administrator authorization remain future bounded work.

## Security And Authorization Deferred Decisions

Deferred security decisions include:

- server authentication and authorization;
- Tailscale Serve configuration;
- device trust and enrollment;
- provider-secret storage;
- transfer authorization;
- stream URL lifetime;
- audit logging;
- backup access;
- administrator operations;
- multi-user behavior, if any.

## Current MacBook MVP Non-Goals

The current MacBook MVP does not include:

- NUC deployment;
- real systemd service installation or activation;
- authoritative server deployment;
- remote streaming;
- transfer protocol;
- automatic synchronization;
- authenticated server-managed media ingest or upload;
- per-user visibility state such as Trash;
- backup orchestration;
- centralized provider Settings;
- multi-device conflict resolution;
- server-side media import.

The local Gallery and Details phase is frozen for MVP absent a concrete defect.
Further NUC work should stay bounded to deployment readiness, acceptance, or
server-authority tasks rather than reopening Gallery or Details UX.
