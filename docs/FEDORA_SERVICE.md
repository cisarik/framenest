# FrameNest Fedora systemd Service

## Status

This is a superseded repository-native Fedora operator workflow for the initial
FrameNest systemd service foundation. It is not the current deployment workflow,
not an installer, and not proof that a real Intel NUC deployment has been
completed.

Current deployment guidance is [docs/UBUNTU_NUC_DEPLOYMENT.md](UBUNTU_NUC_DEPLOYMENT.md).
[ADR-0032](adr/0032-ubuntu-nuc-deployment-foundation.md) supersedes
[ADR-0031](adr/0031-fedora-systemd-service-foundation.md) for the active
deployment target and operator workflow.

Classification: deployment operator guide.

Consumers: Cooperator, Orchestrator, Worker, maintainers, security reviewers,
and anyone auditing the historical Fedora service foundation.

Retention: retained as historical evidence for ADR-0031.

Inbound links: [README.md](../README.md), [SERVER.md](../SERVER.md),
[SECURITY.md](../SECURITY.md), [ROADMAP.md](../ROADMAP.md), and
[ADR-0031](adr/0031-fedora-systemd-service-foundation.md).

Cleanup/update owner: future explicitly authorized Worker under an Orchestrator
task. Git history remains the archive.

## Historical Repository Artifacts

```text
deploy/systemd/framenest.service
deploy/systemd/framenest.env.example
```

The service file began as source material for a Fedora host and remains generic
systemd source material. Committing it does not install, enable, start, stop,
reload, or inspect a real service.

## Historical Service Model

The historical Fedora service model ran through the production executable:

```text
/opt/framenest/current/.venv/bin/framenest-production
```

The root `./framenest` launcher remains macOS/local browser-development
tooling. It is not used by the systemd service.

Before startup, systemd runs a read-only readiness gate:

```text
/opt/framenest/current/.venv/bin/framenest-production check-database-ready
```

The service foreground process is:

```text
/opt/framenest/current/.venv/bin/framenest-production serve
```

Both production operations disable repository `.env` loading and use only the
process environment supplied by systemd plus normal safe defaults.

The readiness gate requires the configured SQLite database to already be at
packaged Alembic head. It does not create the database and does not run
migrations.

## Stable Paths

```text
/opt/framenest/current                      active repository checkout or release tree
/opt/framenest/current/.venv                Poetry-managed virtual environment
/etc/framenest/framenest.env                non-secret service environment
/var/lib/framenest/catalog.sqlite3          production catalog database
/var/lib/framenest/ai/config.json           non-secret AI provider/model config
/var/cache/framenest/gallery-previews       server-owned preview cache
/run/framenest                              service runtime directory
```

The service account is `framenest`. systemd manages only the mutable service
state, cache, and runtime directories. `/etc/framenest` and `framenest.env` are
host-operator managed; the service reads them and does not need ordinary write
permission there.

## Non-Secret Environment

Copy the committed template to the host-local configuration path:

```text
deploy/systemd/framenest.env.example -> /etc/framenest/framenest.env
```

The template contains only non-secret settings:

```text
FRAMENEST_HOST=127.0.0.1
FRAMENEST_PORT=8000
FRAMENEST_DATABASE_PATH=/var/lib/framenest/catalog.sqlite3
FRAMENEST_GALLERY_PREVIEW_CACHE_PATH=/var/cache/framenest/gallery-previews
FRAMENEST_AI_CONFIG_PATH=/var/lib/framenest/ai/config.json
```

Do not put provider keys, passwords, tokens, cookies, private keys, or
authorization headers in `framenest.env`.

## Secret Boundary

Production provider-secret integration is not implemented in this slice. Do
not create a service secret EnvironmentFile and do not place API keys in the
non-secret environment template.

AI provider calls remain unavailable in production until a later authorized
service-secret integration exists, likely systemd credentials or another
approved service-secret adapter. Without credentials, configured providers
preserve the existing sanitized `credential_unavailable` behavior.

## Superseded Safe Operator Workflow

This section is retained for historical context only. Use
[docs/UBUNTU_NUC_DEPLOYMENT.md](UBUNTU_NUC_DEPLOYMENT.md) for current Ubuntu
NUC preparation and deployment workflow.

1. Install a CPython 3.13 environment and Poetry according to the host policy.
2. Place the active repository or release tree at `/opt/framenest/current`.
3. Install from the committed lock-based Poetry environment in
   `/opt/framenest/current`.
4. Create the `framenest` service account and grant it only the required access.
5. Install `framenest.service` as the host systemd unit source.
6. Copy and edit `framenest.env.example` as `/etc/framenest/framenest.env`.
7. Prepare service-owned state, cache, and runtime directories with restrictive
   permissions.
8. Run the explicit migration command as an operator step:

```text
FRAMENEST_DATABASE_PATH=/var/lib/framenest/catalog.sqlite3 \
/opt/framenest/current/.venv/bin/framenest-db migrate
```

9. Check readiness without starting the server:

```text
FRAMENEST_DATABASE_PATH=/var/lib/framenest/catalog.sqlite3 \
/opt/framenest/current/.venv/bin/framenest-production check-database-ready
```

10. Only after the readiness gate reports `ready`, enable or start the unit
    through ordinary host systemd procedures.

This historical repository slice did not perform any of those host actions.

## Media Roots

Registered library roots must be explicit, absolute, existing server-local
directories. Grant the `framenest` service account read access only to intended
media roots.

The service unit uses `ProtectSystem=strict` and `ProtectHome=read-only`.
`ProtectHome=read-only` is retained rather than changed to a full home denial
because an explicitly registered media root may be operator-authorized under a
protected home hierarchy, but remains read-only to the service.

If a media root needs additional read access under a protected location, use a
host-local systemd drop-in with the narrowest suitable `ReadOnlyPaths=` entry.
Do not give the service broad write access to media libraries merely to make
imports or previews work.

## Networking

The template binds to `127.0.0.1` by default. Do not change it to `0.0.0.0` for
ordinary deployment.

Remote access remains a future Tailscale-only direction. This service
foundation does not configure Tailscale Serve, authentication, firewall rules,
Fedora SELinux policy, public ports, reverse proxies, or trusted proxy headers.

## Logging And Lifecycle

FrameNest application logs are JSON lines written to stderr by the server
process and captured by systemd/journald. The unit explicitly routes stdout and
stderr to `journal`. FrameNest does not create service log files, rotate logs,
enforce retention, or ship logs remotely in this slice.

The unit sends `SIGTERM` for ordinary shutdown, bounds stop waiting to 30
seconds, restarts on unexpected failure, and does not restart after an
intentional clean stop.

Review and sanitize logs before sharing them. Do not share provider keys,
private paths, private media filenames, raw provider responses, or private
network details.

## Hardening

The unit removes Linux capabilities with empty `CapabilityBoundingSet=` and
`AmbientCapabilities=` directives. It also retains compatible hardening such as
`NoNewPrivileges=true`, `PrivateTmp=true`, `ProtectSystem=strict`,
`ProtectHome=read-only`, kernel/control-group protections, SUID/SGID
restriction, personality locking, and a private umask.

The unit does not grant a writable media-root path.

## Not Implemented Yet

This superseded service foundation does not include:

- real host acceptance;
- Ubuntu host acceptance;
- AppArmor policy;
- UFW policy;
- Tailscale Serve;
- application authentication or authorization;
- backup and restore;
- automated updates;
- provider-secret integration;
- systemd credentials;
- public exposure;
- desktop replacement behavior.
