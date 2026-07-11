# ADR-0035: Authoritative Server and Client State Model

## Status

`Accepted`

## Decision Date

`2026-07-11`

## Context

ADR-0022 accepted selective media placement and an optional Intel NUC server
aggregation direction. It also described each desktop as owning a complete
local authoritative catalog for local operation and the NUC as an optional
aggregator.

Later accepted FrameNest direction refined the authority model. The central
FrameNest server process is authoritative for catalog records and server-owned
state. That server may run locally on the same device as the desktop client, or
on the Ubuntu NUC personal production server once deployment is accepted.
Browser, desktop, and remote interfaces are clients of the server API.

This ADR records that newer authority model without undoing the still-valid
selective-placement decisions from ADR-0022.

## Decision

A FrameNest server process is authoritative for:

- catalog records;
- server media originals;
- canonical display title, description, and tags;
- future category and language metadata;
- per-user visibility state;
- upload and ingest state;
- server preview cache;
- authentication and capability decisions.

FrameNest interfaces are clients of that server API. This includes the current
browser development UI, the future Tauri desktop shell, a browser running on
the NUC itself, and future remote interfaces.

The server process may be local to a desktop installation. Local-first
operation means Michal remains able to own and run FrameNest locally without a
public cloud service, public internet exposure, or mandatory remote NUC. It
does not require every client interface to maintain an independent
authoritative catalog.

Original media is not automatically replicated to every client. Clients may
explicitly stream, open, or download authorized media. Explicit client cache or
download state is distinct from catalog synchronization and from managed server
ingest.

Provider secrets, service secrets, authentication decisions, administrator
capabilities, and privileged operator actions remain server-side or operator
boundaries. Ordinary clients never receive provider secrets and never infer
administrator authority from loopback, source IP, hostname, same-machine
execution, cookies, or Tailscale membership.

## ADR-0022 Partial Supersession

This ADR supersedes only the server-authority portions of ADR-0022 that state
or imply:

- each desktop owns a complete independent authoritative catalog;
- the NUC is only an optional aggregator;
- server state is not the authoritative catalog and capability boundary.

ADR-0022 remains accepted for these decisions:

- selective media placement;
- no automatic full-byte replication to every device;
- one logical medium with multiple physical locations;
- remote-only media visibility through metadata, covers, previews, and
  availability state;
- explicit streaming, opening, download, copy, archive, and move operations;
- source removal only after destination verification;
- Tailscale-only remote-access direction unless superseded;
- application authorization above Tailscale.

## Upload, Synchronization, Cache, And Trash

Future work must keep these operations distinct:

- catalog synchronization;
- authenticated server-managed media ingest or upload;
- explicit client cache or download;
- per-user visibility state such as Hide or Trash;
- global retirement or physical purge of originals.

Future upload must be server-managed and must require quarantine, validation,
limits, safe filenames, duplicate detection, atomic publication, cleanup after
failure, and server-selected placement. Clients must not select arbitrary
server filesystem paths.

Per-user Trash is server-persisted visibility state. Moving an item to Trash
for a user must not delete the server original. Separate operations may later
include:

- remove from this managed client;
- hide or Trash for this user;
- request server deletion;
- retire globally;
- purge physical originals.

None of these workflows is implemented by this ADR.

## Category, Language, And Playback Direction

Future first-class categories include `memes`, `youtube`, and `movies`.
Categories are a dedicated catalog facet, not merely tags or operational
directory names.

Movies may carry explicit language metadata, such as English, Slovak, or
Czech. Prefer container or audio metadata and user editing before expensive AI
analysis. FrameNest must not automatically upload audio to a cloud provider.

Future playback should support fullscreen and truthful audio-track selection
where technically supported. Use capability detection and clear fallback rather
than fake controls. Subtitle support is not currently required. FrameNest must
not silently transcode originals.

## Consequences

### Positive

- Server authority, client behavior, and privileged capability boundaries are
  explicit.
- The local-first invariant remains compatible with a local server process and
  with future NUC deployment.
- Selective media placement remains intact.
- Future upload, cache, Trash, category, language, playback, and AI work have a
  clearer decision boundary.

### Costs And Limitations

- Offline client caching remains unresolved.
- Multi-device synchronization and conflict rules remain unresolved.
- Server authentication and capability implementation remain unresolved.
- Existing documents that used older optional-aggregator wording must point to
  this ADR.

## Security Consequences

Ordinary clients do not receive provider secrets, service secrets, arbitrary
filesystem write authority, or administrator capabilities. Tailscale membership
and same-machine execution are not authorization. The server-side AI boundary,
sanitized browser status, secret redaction, and operator-only provider
administration remain required.

## Rejected Alternatives

### Independent Authoritative Desktop Catalogs Everywhere

Rejected for the current direction because it makes server-owned state,
per-user visibility, upload ingest, capability decisions, and remote access
harder to reason about.

### Public Cloud Authority

Rejected. The authoritative server process may be local or NUC-hosted and does
not require a public cloud service.

### Automatic Full Replication

Rejected by ADR-0022 and retained here. Full media bytes are not automatically
replicated to every client.

### Client-Selected Server Paths

Rejected. Future ingest is server-managed, and clients do not choose arbitrary
server filesystem destinations.

## Deferred Decisions

This ADR does not decide:

- synchronization protocol;
- offline client cache format or eviction rules;
- conflict resolution;
- server authentication implementation;
- per-user data model;
- upload API and quarantine storage design;
- language metadata schema;
- category schema;
- audio-track capability detection;
- production provider-secret storage.

## Related Documents

- [ADR index](README.md)
- [ADR-0022](0022-selective-media-placement-and-server-aggregation.md)
- [ADR-0032](0032-ubuntu-nuc-deployment-foundation.md)
- [SERVER.md](../../SERVER.md)
- [PRODUCT.md](../../PRODUCT.md)
- [SPEC.md](../../SPEC.md)
- [ROADMAP.md](../../ROADMAP.md)
- [SECURITY.md](../../SECURITY.md)
