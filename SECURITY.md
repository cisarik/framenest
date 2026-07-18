# Security Policy

## Current Support Status

FrameNest is in foundation-stage, pre-alpha development.

There is no stable release, supported release, production deployment, or security response service level yet. Security-sensitive decisions are still being documented as the repository foundation and architecture are established.

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
authorization headers, private keys, or secret prefixes. The initial bundle
excludes Gallery preview cache, original media, non-secret AI configuration,
and secrets. A valid catalog backup bundle contains only the declared manifest
and catalog artifact; unexpected files, directories, symlinks, and temporary
state are rejected. Backup and restore publication must not overwrite a path
that appears after an initial absence check. Restore writes only to a new
absent destination and does not replace production, run migrations, start
services, or prove readiness.

The resumable upload transport is trusted-loopback MVP functionality, not a
public upload service. Upload endpoints are disabled until
`FRAMENEST_UPLOAD_QUARANTINE_ROOT` points to a pre-existing absolute
non-symlink quarantine directory. That directory must not overlap registered
media library roots or the Gallery preview cache. Upload requests use
server-generated session and storage identities and stream bytes directly to
quarantine. Bounded validation derives size and SHA-256 evidence on the server;
the first qualifying identity reaches `publish_pending`, while a later exact
copy remains quarantined in `duplicate_pending` until explicitly kept or
discarded. Discard durably cancels that selected session before removing only
its quarantine object. Upload responses expose no storage key or path;
duplicate-resolution responses additionally expose no matching session, byte
identity, checksum, or filename. Uploaded bytes remain untrusted and are not
published, cataloged, served, displayed, or sent to AI providers in this slice.
Browser mutation requests with an `Origin` header must match the effective same
origin; this is a bounded loopback protection and not authentication or
authorization.

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
- Use Tailscale as the remote network boundary for cross-device features.
- Treat Tailscale networking as necessary but not sufficient; application-level authorization is still required.
- Require explicit confirmation for destructive actions.
- Do not distribute provider secrets to ordinary client installations.

The sanitized NUC baseline in [docs/NUC_HOST_BASELINE.md](docs/NUC_HOST_BASELINE.md)
is evidence of accepted host preparation, not authority for future host
mutation. The pinned AP integration in [AGENTS.md](AGENTS.md) and
[ADR-0034](docs/adr/0034-canonical-analytic-programming-integration.md) defines
task-authority boundaries; tool or credential availability is never permission
by itself.

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

## Dependencies and Updates

Dependencies, update mechanisms, packaging flows, and production deployment procedures must be pinned where appropriate, reviewed, tested, and documented before production use.

The project does not currently promise automated updates, dependency freshness guarantees, or production security support.
