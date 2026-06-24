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
- Do not disable SELinux, firewall protections, or platform security controls as a shortcut.
- Keep local backend services bound to localhost where applicable.
- Use Tailscale as the remote network boundary for cross-device features.
- Treat Tailscale networking as necessary but not sufficient; application-level authorization is still required.
- Require explicit confirmation for destructive actions.
- Do not distribute provider secrets to ordinary client installations.

## Dependencies and Updates

Dependencies, update mechanisms, packaging flows, and production deployment procedures must be pinned where appropriate, reviewed, tested, and documented before production use.

The project does not currently promise automated updates, dependency freshness guarantees, or production security support.
