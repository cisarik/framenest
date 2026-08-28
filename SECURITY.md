# Security Policy

## Current Support Status

FrameNest is in foundation-stage, pre-alpha development.

There is no stable or supported public release and no security response service
level yet. The Ubuntu NUC operates as the FrameNest development-and-testing
machine
([ADR-0075](docs/adr/0075-nuc-development-test-target-and-routine-release-refresh.md)):
it runs only FrameNest, its state is disposable and reinitializable, and it is
routinely refreshed toward public `main` through the immutable release-update
contract ([ADR-0060](docs/adr/0060-repeatable-immutable-nuc-release-update-contract.md)).
An older release (`aec2f0091c10aed2fc2033dac154a0d9651b2b6d`, schema `0028`)
was previously accepted as owner-authoritative production served over Tailscale
Serve only; that fact is dated history. Tailscale-only remote access remains in
force and Funnel is not publicly exposed. NUC security hardening remains open
before any future VPS deployment. Security-sensitive decisions are still being
documented as the repository foundation and architecture are established.

## Reporting Security Issues

Do not post exploitable security details, real secrets, private logs, tokens, cookies, or reproduction steps for active vulnerabilities in a public issue.

When GitHub private vulnerability reporting or another private maintainer-approved channel is available, use that mechanism. If no private channel is available, open a public issue with only minimal, non-exploitable information and wait for maintainer guidance before sharing technical details.

Do not include personal secrets, private network details, or confidential media samples in a report. Use placeholders such as `YOUR_API_KEY`, `example.invalid`, or `<redacted>` when an example is necessary.

## Secret Handling

Secrets must never be committed to the repository. This includes:

- API keys.
- Tokens.
- Passwords.
- Cookies.
- Private keys.
- Service-account files.
- Real `.env` files.
- Authentication headers.

Template files such as `.env.example` may be committed only when they contain placeholders and no real credentials.

## Accidental Secret Exposure

Removing a secret in a later commit is not sufficient. Git history, local clones, logs, caches, and remote mirrors may still contain the exposed value.

If a secret is accidentally exposed:

- Stop using the exposed secret immediately.
- Revoke or rotate the secret at the provider or authority that issued it.
- Assess what systems, accounts, data, or environments may have been exposed.
- Inform the Orchestrator or maintainer responsible for the repository.
- Clean repository history only through an explicitly planned recovery procedure.

Do not keep using an exposed credential while waiting for repository cleanup.

## Logs and Diagnostics

Logs, support bundles, crash reports, diagnostics, and screenshots must be reviewed and sanitized before they are shared.

FrameNest now implements a structured logging foundation with centralized redaction before JSON serialization for FrameNest-owned log records. The formatter does not automatically serialize settings objects, request objects, private paths, media filenames, URLs, headers, or arbitrary object representations. Secrets must still never be passed intentionally as ordinary log messages. Uvicorn HTTP access logging is initially disabled. JSON logs remain diagnostic output and require review before sharing. Logging redaction is defense in depth, not permission to log sensitive data.

Launcher, interpreter, shell, supervisor, and future service-manager diagnostics are separate output sources outside the FrameNest logging graph. Captured combined `stderr` from a wrapped command must not automatically be treated as entirely application-generated. External diagnostics must still be reviewed and sanitized before sharing.

The initial SQLite persistence foundation uses explicit operator commands for database migration. `framenest-db status` and `framenest-db migrate` produce deterministic machine-readable output that must not include the configured database path, database URL, SQL text, SQL parameters, environment values, or raw SQLAlchemy, SQLite, or Alembic exception messages. Normal `framenest-server` startup does not apply migrations.

The initial local media-analysis preparation boundary uses optional external `ffprobe` and `ffmpeg` executables through a shell-free subprocess boundary. Operator commands and sanitized errors must not include absolute private media paths, database paths, raw OS errors, raw subprocess stderr, environment values, or PNG frame payloads. Representative frames are runtime in-memory artifacts only and must not be printed, base64-encoded, or persisted by the catalog CLI.

The initial media suggestion preview uses an explicit cloud-upload confirmation gate and sends provider requests only through the FrameNest server. Server AI administration is performed by `./framenest ai status`, `./framenest ai configure`, and `./framenest ai test`. `status` is network-free. `configure` writes only non-secret provider/model selection outside the repository and must not write API keys, Authorization headers, cookies, provider responses, prompts, frame data, media paths, or database paths. `test` is an explicit minimal text-only provider request and persists only a safe category and timestamp. NVIDIA NIM uses `NVIDIA_API_KEY`; Vercel AI Gateway uses `AI_GATEWAY_API_KEY`. Operator commands, browser diagnostics, and sanitized errors must not include API keys, Authorization headers, absolute paths, raw provider responses, raw prompts, PNG/base64 payloads, or reasoning/chain-of-thought content. Suggestion output is untrusted preview data and must not be persisted automatically.

The ignored local-development file `.secrets/ai.env.fish` may export
`NVIDIA_API_KEY` and/or `AI_GATEWAY_API_KEY` for the root launcher. The launcher
must reject symlinks, non-private files, wrong ownership, and invalid Fish
syntax before sourcing it, and must not print file contents or credential
values. Production AI credentials are repository-supported through optional
systemd credential drop-ins and exact-name `CREDENTIALS_DIRECTORY` resolution.
The base service remains credential-optional, `/etc/framenest/framenest.env`
remains non-secret, and real host installation remains a separately authorized
deployment task.

The catalog backup foundation uses `framenest-backup` for the SQLite catalog
only. Backup manifests and command output must not contain source paths,
destination paths, usernames, hostnames, IP addresses, environment values, SQL,
media paths, media filenames, raw exception text, credentials, tokens, cookies,
authorization headers, private keys, or secret prefixes. Ordinary off-device
status output must also omit destination root, marker destination ID, filesystem
device numbers, and mount identity. Workstation snapshot envelopes and recovery
CLI output must omit SSH host/user/IP/alias, local source/destination paths,
store/marker IDs, device numbers, filesystem UUIDs, credentials, and production
release paths. The initial bundle
excludes Gallery preview cache, scan-imported originals, published upload
originals, non-secret AI configuration, and secrets. A valid catalog backup bundle contains only the declared manifest
and catalog artifact; unexpected files, directories, symlinks, and temporary
state are rejected. Backup and restore publication must not overwrite a path
that appears after an initial absence check. Restore writes only to a new
absent destination and does not replace production, run migrations, start
services, or prove readiness. Off-device and workstation snapshot publication
use no-replace semantics and must not overwrite a conflicting final destination
bundle. Workstation pull uses system OpenSSH with a fixed remote export
launcher and a narrow `framenest` sudo bridge; it must not grant arbitrary
sudo, caller-controlled launcher arguments, or NUC write access to workstation
storage.

The resumable upload transport is capability-gated trusted-path functionality,
not a public upload service. Upload endpoints are disabled until
`FRAMENEST_UPLOAD_QUARANTINE_ROOT` points to a pre-existing absolute
non-symlink quarantine directory. That directory must not overlap registered
media library roots or the Gallery preview cache. Upload requests use
server-generated session and storage identities and stream bytes directly to
quarantine. Direct-upload routes require `upload.submit`. Mapped ordinary
Tailscale users may submit; `upload.manage` remains administrator-only for
explicit duplicate resolution and ownership override. Durable upload-session
ownership (`created_by_login_key`) and creation-time
`duplicate_resolution_mode` are persisted by migration `0025`. Foreign ordinary
callers receive sanitized `404 UPLOAD_SESSION_NOT_FOUND`. Bounded validation
derives size and SHA-256 evidence on the server; administrator `explicit`
sessions retain `duplicate_pending` until keep/discard, while ordinary
`silent_keep_separate` sessions atomically keep-separate without disclosing a
match. Discard durably cancels that selected session before removing only
its quarantine object. Optional publication requires the server-controlled
`FRAMENEST_UPLOAD_PUBLICATION_LIBRARY_ID` to resolve one existing writable
registered POSIX library whose native non-symlink root is disjoint from
quarantine, cache, database state, and other registered POSIX roots. Publication
uses an opaque per-upload target, verifies exact size and SHA-256 evidence, and
atomically creates the final name without replacing an existing object. Only
after durable publication provenance and `published` commit together may the
exact quarantine object be removed; failed cleanup remains retryable. Upload
responses expose no storage key, publication identity, destination, target,
path, cleanup state, byte identity, or checksum; duplicate-resolution responses
additionally expose no matching session or filename. An optional opaque
`media_id` may appear only after successful `cataloged`. Merely `published`
uploads remain uncataloged, unserved, absent from Gallery, and never sent to AI
providers by this workflow. Ordinary cataloged submissions remain
content-unpublished until administrator publication. Catalog persistence failure
leaves the durable published file untouched under the trusted-loopback
single-tenant boundary; Tailscale multi-user ownership follows ADR-0053.
Browser mutation requests with an `Origin` header must match the effective same
origin; this is a bounded loopback protection and not authentication or
authorization. In Tailscale UDS mode, five `companion_mutation` routes may also accept an
exact allowlisted `chrome-extension://` origin after
`FRAMENEST_COMPANION_EXTENSION_ORIGINS` is set: `POST /api/x/requests`,
`POST /api/x/requests/{claim_id}/retry`,
`POST /api/companion/review-inbox/{media_id}/opened`,
`POST /api/companion/review-inbox/{media_id}/apply`, and
`PUT /api/admin/settings/automatic-analysis`. That allowlist defaults to
empty, still requires `X-FrameNest-Request: 1`, and adds no CORS headers. GET
inbox and own-history routes do not require the allowlist the same way;
mutations that carry the extension Origin fail closed when the allowlist is
empty with sanitized `403 MUTATION_ORIGIN_FORBIDDEN`, so with
`FRAMENEST_COMPANION_EXTENSION_ORIGINS` unset authenticated GET routes still
work while every extension-Origin mutation is rejected. Rollback is removing
the key or setting it to `[]` and restarting. See
[ADR-0061](docs/adr/0061-x-meme-browser-companion.md),
[ADR-0064](docs/adr/0064-x-save-category-and-public-photo-acquisition.md),
[ADR-0067](docs/adr/0067-administrator-companion-review-inbox-and-mutation-trust.md),
and
[docs/X_COMPANION.md](docs/X_COMPANION.md). The fifth mutation is
[ADR-0079](docs/adr/0079-administrator-automatic-analysis-runtime-setting.md).
Public JPEG/PNG X photographs are
acquired through an isolated status bridge and a strict `pbs.twimg.com`
transport; WebP is rejected; content scripts never fetch FrameNest or the CDN.
The companion still adds no CORS headers.

Three companion/workspace positions are accepted residuals documented here,
not new rules. Workspace embeddability: workspace HTML responses set no
`frame-ancestors` or `X-Frame-Options` header
(`src/framenest/adapters/api/application.py`), deliberately, because the
companion side panel hosts the workspace origin
([ADR-0063](docs/adr/0063-companion-side-panel-web-host.md)). The residual is
bounded by design: every unsafe mutation still requires the exact external
`Origin` plus the non-simple `X-FrameNest-Request: 1` header, and workspace
identity is injected per request from trusted UDS provenance with no cookies,
so a hostile embedder cannot ride an ambient session. Companion packaging:
the companion ships as an unpacked Manifest V3 extension with a pinned
development public key and no auto-update path
([docs/X_COMPANION.md](docs/X_COMPANION.md)); rotating that key changes the
derived extension ID and requires an allowlist update, and if the extension is
ever packed, store signing, a controlled update channel, and extension-ID
continuity would have to be re-established — no packing work is promised.
Companion storage: per-user connection state (the stored origin plus bounded
inflight-claim and awaiting-analysis traces, with no secrets) lives in
`chrome.storage.local` (`extension/background/service_worker.js`) and is
readable by anything executing in the same browser profile on a shared
machine; there is no cross-profile exposure. The accepted position is the
single-operator workstation assumption with bounded, non-secret contents.

YouTube manual ingestion is a separate operator-only loopback boundary. It is
disabled unless its private staging root and the existing upload/publication
prerequisites are configured, and it is disabled for non-loopback server
binds. Operator requests with any `Origin` header are rejected. The server
accepts only bounded exact JSON, revalidates supported single-video HTTPS
YouTube forms, and never accepts client-supplied canonical identities,
filenames, extractor evidence, or provenance. The pinned downloader runs
shell-free with an explicit environment allowlist, ignores user configuration,
uses no cookies or browser profiles, captures bounded output, and persists only
fixed failure codes. Claim staging is private, opaque, non-overlapping, and
cleaned by exact ownership. No downloader output, remote error, source title,
filesystem path, cookie, header, or inherited credential may reach operator
output or logs. YouTube-created catalog results are explicitly barred from
automatic AI analysis in this slice.

Avoid exposing:

- Home-directory paths when they are not necessary.
- Cookies.
- URLs containing tokens or signed access parameters.
- Authentication headers.
- API requests containing secrets.
- Private network details when they are not necessary.
- Personal media metadata or filenames when they are sensitive.

## Security Architecture Principles

FrameNest security work should follow these principles:

- Use least privilege for filesystem, process, network, and service access.
- Do not require routine root or administrator execution.
- Do not disable AppArmor, firewall protections, or platform security controls as a shortcut.
- Keep local backend services bound to localhost where applicable.
- Use Tailscale as the workspace remote network boundary for cross-device
  features. A local-only public published-reader composition is implemented
  per
  [ADR-0074](docs/adr/0074-dual-audience-public-published-and-tailscale-workspace-boundary.md)
  and is not exposed externally.
- Treat Tailscale networking as necessary but not sufficient; application-level authorization is still required.
- Keep public-internet egress distinct from Tailscale Serve ingress; operator Mullvad controls are documented in [docs/OPERATOR_NETWORK.md](docs/OPERATOR_NETWORK.md) and [ADR-0058](docs/adr/0058-independent-mullvad-egress-and-operator-network-recovery.md) and must not create inbound exposure.
- Require explicit confirmation for destructive actions.
- Do not distribute provider secrets to ordinary client installations.

### Dual-audience public trust boundary (accepted direction)

[ADR-0074](docs/adr/0074-dual-audience-public-published-and-tailscale-workspace-boundary.md)
records the dual-audience boundary. The local-only
`public_published_uds` published-reader composition is implemented and is not
exposed. It does not add a public bind, TLS listener, Funnel, or NUC
enablement.

For the local-only public composition:

- Public callers are identity-absent and receive only published reads.
- Unknown and unpublished items, and every unlisted route or method, return
  the same sanitized `404`.
- `Tailscale-*` headers MUST NOT be trusted outside `tailscale_uds`.
- No CORS.
- No shared caching initially, so an unpublished item is not retained by a
  reverse-proxy cache.
- The application process remains loopback-first. Workspace remote access
  remains Tailscale Serve to `/run/framenest/framenest.sock`. Funnel to that
  workspace socket stays forbidden. Router port-forwarding is not accepted.

The sanitized NUC baseline in [docs/NUC_HOST_BASELINE.md](docs/NUC_HOST_BASELINE.md)
is evidence of accepted host preparation, not authority for future host
mutation. The pinned AP integration in [AGENTS.md](AGENTS.md) and
[ADR-0034](docs/adr/0034-canonical-analytic-programming-integration.md) defines
task-authority boundaries; tool or credential availability is never permission
by itself.

### UDS socket provenance tightening and fail-closed startup verification

In `tailscale_uds` and `public_published_uds` ingress modes, header trust is
bound to the provenance of a single Unix domain socket. At startup, immediately
after uvicorn binds that socket and before the server accepts or serves any
request, the application tightens the bound socket to owner-only `0600` in both
UDS ingress modes. It then asserts that the path is a socket, that its mode has
no group or other permission bits, and that it is owned by the effective user
ID. Any tightening or assertion failure emits a sanitized CRITICAL structured
record (event `uds_socket_provenance_failure`, error code
`UDS_SOCKET_PROVENANCE_FAILURE`, with a machine reason token and no socket
paths or environment values), closes the listening sockets, and exits
fail-closed before any request is served.

Recorded residuals, stated honestly: between the kernel bind and the
owner-only tightening there is a microsecond-scale window spanning one
event-loop iteration (uvicorn's UDS bind path yields once before its own
post-bind chmod), during which a connection may be accepted at the transport
level; no request data is read or processed before the tightening and
provenance checks complete. The previously documented posture left the bound
socket at `0666` permanently, so the tightened state is strictly stronger.
Directory-level protection remains the systemd `RuntimeDirectory`/`UMask`
contract: an attacker with write access inside that runtime directory is
outside this invariant.

## Secure Media Content Endpoint

The `GET /api/media/{media_id}/locations/{location_id}/content` endpoint serves registered local media content securely:

- **Identity-only URLs**: The URL contains only catalog identities (`media_id`, `location_id`), never a filesystem path. Absolute paths, database paths, and filesystem details are never exposed in response bodies, headers, or error messages.
- **Registered-root containment**: The filesystem adapter treats the registered library root as the only authority. The catalog relative path is resolved without permitting absolute paths or traversal, and the resolved target must remain inside the resolved registered root.
- **Symlink escape prevention**: Symlinks are resolved and any target outside the registered root is rejected. A symlink is permitted only when its final resolved target remains inside that root.
- **Catalog relationship checks**: Each request verifies that the logical media exists, the physical location exists, the location belongs to the requested logical media, the location availability is `available`, and the referenced library is registered.
- **Exact kind/extension allowlist**: Only `video` + `.mp4` → `video/mp4` and `animated_image` + `.gif` → `image/gif` are served. No arbitrary MIME types are inferred and unsupported extensions are rejected.
- **Sanitized failures**: Errors are mapped to stable sanitized codes and messages (`503` catalog unavailable, `404` identity not found or mismatched, `409` unavailable/unsafe/unsupported content, `416` unsatisfiable range, `500` unexpected failure). All error responses use `Cache-Control: no-store`. Underlying exception text, SQL, and filesystem paths are never disclosed.
- **No arbitrary path-serving API**: The endpoint does not accept or serve arbitrary filesystem paths. It serves only catalog-referenced content beneath a registered library root.
- **Read-only behavior**: The endpoint performs no database or filesystem mutation. Repository calls are read-only.
- **Streaming safety**: Successful responses send `X-Content-Type-Options: nosniff`, `Cache-Control: private, no-store`, and `Accept-Ranges: bytes`. File handles are closed reliably including interrupted streaming.

### Durable Cover Endpoints

The first durable manual cover workflow ([ADR-0050](docs/adr/0050-durable-manual-cover-foundation.md))
adds identity-only authoring and delivery endpoints:

- Timeline, ephemeral frame preview, and the accepted-cover mutation require the
  `metadata.canonical.write` capability and expose no filesystem paths.
- The accepted-cover mutation requires origin/mutation-header proof and an
  audit record (`media.cover_set`) established before mutation, per the current
  ingress architecture.
- The cover thumbnail endpoint is identity-only (`/api/media/{media_id}/cover-thumbnail`),
  requires `gallery.read`, enforces the shared content-publication audience
  policy (unpublished media returns the same sanitized not-found as unknown
  media), performs no generation or mutation on read, and never discloses
  absolute paths, storage roots, filenames, or raw ffmpeg output.
- Durable cover artifacts are stored under a server-owned root disjoint from
  the database, registered media roots, Gallery preview cache, upload
  quarantine, and YouTube acquisition storage.

## Portable Media Sidecar

The portable media sidecar v1 projection ([ADR-0059](docs/adr/0059-portable-media-sidecar-roundtrip-foundation.md))
is a closed JSON document beside one explicit media copy:

- The schema is closed. Unknown fields are rejected. Secrets, absolute library
  roots, host paths, device identities, requester-private acquisition state,
  credentials, tokens, cookies, and catalog/database paths are not projected.
- Reads are bounded to 256 KiB before parse.
- Sidecar targets are classified before open. Symlinks and other non-regular
  files are refused without following or replacing them. Source-media symlinks
  and symlink parents are refused. The store does not reuse content-reader
  behavior that permits an in-root media symlink.
- Create and replace use a same-directory uniquely owned temp, fsync, codec
  validation, installed mode `0644`, `os.replace`, and directory fsync. Exact
  intended bytes are a no-op. Foreign `media_id` or `location_id` is refused.
  Malformed and unsupported documents are refused. The previous valid target is
  preserved when temp creation, write, validation, or replacement preparation
  fails. The catalog is not mutated.
- Known Windows `os.replace` and case-folding evidence remains incomplete;
  non-native library roots are rejected on the current host.
- The `framenest-sidecar` command emits sanitized JSON only. It does not print
  sidecar contents, absolute paths, or tracebacks. Validate does not require
  the catalog. Export and compare do not write catalog rows.

## Dependencies and Updates

Dependencies, update mechanisms, packaging flows, and production deployment procedures must be pinned where appropriate, reviewed, tested, and documented before production use.

The project does not currently promise automated updates, dependency freshness guarantees, or production security support.
