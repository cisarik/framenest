# FrameNest Optional Server Architecture

## Status

This is a living permanent product architecture reference. It records accepted
future server direction; it does not claim that NUC deployment, aggregation,
streaming, synchronization, or transfer is currently implemented.

Classification: living permanent product architecture/UX reference.

Consumers: Orchestrator, Worker, designers, implementers, maintainers, and
security reviewers.

Retention: remains while the server product subsystem exists.

Inbound links: [README.md](README.md), [PRODUCT.md](PRODUCT.md),
[SPEC.md](SPEC.md), [ROADMAP.md](ROADMAP.md), [ADR-0022](docs/adr/0022-selective-media-placement-and-server-aggregation.md),
and [ADR-0021](docs/adr/0021-tauri-desktop-shell.md).

Cleanup/update owner: future explicitly authorized Worker under an Orchestrator
task. Git history remains the archive.

## Optional NUC Role

The Intel NUC is the current concrete personal production server preparation
target for the optional aggregator and archive-node role. It is not required
for local desktop operation and must not make desktop clients unusable thin
clients.

The NUC may later provide:

- global catalog aggregation;
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

The desktop owns local interactive operation. The server may aggregate and serve
remote-capable state when available.

## Local Catalog Versus Server Aggregate Catalog

Each desktop installation owns a complete local catalog sufficient for local
operation. The server aggregate catalog may later combine known logical media,
locations, availability state, cover metadata, and transfer state across
devices.

The server aggregate is optional. Desktop local catalog behavior must remain
useful when the server is offline, unreachable, unconfigured, or disabled.

## Metadata And Cover Aggregation

Remote-only media cards should be visible without full media-byte replication.
The server may aggregate or provide:

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

When the server is unavailable, desktop local operation continues. Remote-only
items may become unavailable for stream/download, but their known metadata and
cover summaries should remain visible if previously synchronized or cached.

The UI must distinguish offline server state from missing local catalog data and
from unavailable media bytes.

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
development server. Ordinary browser clients do not configure providers, select
models, enter API keys, receive provider credentials, or call NVIDIA, Vercel,
Google, or another provider directly. Browser clients may view sanitized
read-only server AI status and may explicitly request AI analysis through the
FrameNest server when a provider is configured.

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
- server aggregate catalog;
- remote streaming;
- transfer protocol;
- automatic synchronization;
- backup orchestration;
- centralized provider Settings;
- multi-device conflict resolution;
- server-side media import.

The local Gallery and Details phase is frozen for MVP absent a concrete defect.
Further NUC work should stay bounded to deployment readiness, acceptance, or
server aggregation tasks rather than reopening Gallery or Details UX.
