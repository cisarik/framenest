# ADR-0031: Fedora systemd Service Foundation

## Status

`Accepted`

## Decision Date

`2026-07-06`

## Decision Authority

The Orchestrator authorized this repository-native deployment-infrastructure
slice as the first Fedora systemd service foundation. A follow-up correction
kept the accepted foundation but aligned the release-root, secret,
configuration, lifecycle, and production-runtime boundaries. The task explicitly
forbids installing or activating anything on a real host.

## Context

FrameNest now has a loopback-first FastAPI/Uvicorn server, explicit SQLite
database migration commands, server-owned persistent gallery previews, and
provider-neutral server-side AI configuration. Fedora KDE on an Intel NUC is
the later optional server target, while local desktop operation remains a
separate product invariant.

Existing accepted decisions require:

- safe loopback defaults and centralized typed configuration;
- Uvicorn as runtime infrastructure;
- structured JSON logs to process stderr for supervisor capture;
- explicit migrations rather than automatic schema changes during server
  startup;
- production deployment not depending on developer `.env` files, repository
  `.env` files, or the local `.secrets/ai.env.fish` helper;
- Tailscale-only remote-access direction unless superseded later.

Before this decision, the repository had no systemd unit, production service
environment template, or production startup gate.

## Decision

FrameNest accepts a repository-native Fedora systemd service foundation.

The committed service bundle is documentation and deployment source material.
It is not an installer and must not activate a real host by itself.

The accepted release boundary is:

```text
/opt/framenest/current
```

The production service runs through the FrameNest production executable:

```text
/opt/framenest/current/.venv/bin/framenest-production
```

The production service must preserve the existing macOS/local development
launcher. The root `./framenest` launcher remains browser-development tooling
and is not the production supervisor boundary.

The production executable provides two service-facing operations:

```text
/opt/framenest/current/.venv/bin/framenest-production check-database-ready
/opt/framenest/current/.venv/bin/framenest-production serve
```

Both production operations must load settings with the explicit no-dotenv
boundary equivalent to `env_file=None`. Production must use only process
environment supplied by systemd plus normal safe settings defaults. It must not
implicitly load a repository or working-directory `.env` file.

`serve` runs the existing Uvicorn server composition in the foreground with
explicitly resolved settings. It must not duplicate server composition, run
migrations, open a browser, daemonize, enable reload, or use more than one
worker.

`check-database-ready` is read-only. It inspects the configured Alembic revision
through the existing migration-status boundary, must not create a missing
database, must not run migrations, must not bind a listener, and must not print
database paths, SQL, environment values, raw revisions on expected failure
paths, tracebacks, or raw exceptions.

Production startup refuses operation unless the configured database is already
at packaged migration head. Operators must run the explicit migration command
before starting or restarting the service when the database is uninitialized or
behind:

```text
framenest-db migrate
```

The Fedora service-owned mutable boundaries are:

- state: `/var/lib/framenest`;
- cache: `/var/cache/framenest`;
- runtime: `/run/framenest`.

`/etc/framenest` is an operator-owned configuration boundary. The service reads
the required non-secret environment file there, but the service must not be
given ordinary ownership or general write permission over `/etc/framenest`.

The initial production catalog path is:

```text
/var/lib/framenest/catalog.sqlite3
```

The initial production gallery-preview cache path is:

```text
/var/cache/framenest/gallery-previews
```

The initial mutable non-secret server AI configuration path is:

```text
/var/lib/framenest/ai/config.json
```

Mutable application state must not be placed under `/etc`.

The production non-secret environment file is:

```text
/etc/framenest/framenest.env
```

The committed template is:

```text
deploy/systemd/framenest.env.example
```

Provider-secret integration is not implemented by this service foundation. The
systemd unit must not load a provider-secret `EnvironmentFile`, and the
repository must not commit a production secret-file template. Production
provider-secret integration remains explicitly deferred to a later bounded
decision, likely systemd credentials or another approved service-secret
adapter. Without credentials, configured providers preserve the existing
sanitized `credential_unavailable` behavior.

The service remains loopback-bound by default with `FRAMENEST_HOST=127.0.0.1`.
Public bind addresses are not the default. Future Tailscale Serve integration
must preserve loopback backend binding unless a later accepted security decision
supersedes this.

The unit captures application stdout and stderr through systemd/journald.
FrameNest still does not implement application-owned log files, log rotation,
retention enforcement, or remote log shipping.

The unit uses bounded process-lifecycle behavior:

```text
KillSignal=SIGTERM
TimeoutStopSec=30s
Restart=on-failure
RestartSec=5s
```

This permits graceful ordinary SIGTERM shutdown, bounds shutdown waiting,
restarts after unexpected failure, and avoids restart after an intentional clean
stop.

## Security And Operational Boundaries

The unit uses a dedicated service account named `framenest`.

The unit declares systemd-owned mutable state, cache, and runtime directories
through `StateDirectory`, `CacheDirectory`, and `RuntimeDirectory`. It must not
declare `ConfigurationDirectory` or `LogsDirectory` for this slice.

The unit applies baseline hardening including `NoNewPrivileges=true`,
`PrivateTmp=true`, `ProtectSystem=strict`, `ProtectHome=read-only`, kernel and
control-group protection, SUID/SGID restriction, personality locking, empty
`CapabilityBoundingSet=`, empty `AmbientCapabilities=`, and a private umask.

`ProtectHome=read-only` is retained instead of a full home denial because an
operator may explicitly register a read-only media root under a protected home
hierarchy. This does not grant broad write access to home directories or media
roots.

Registered media libraries remain explicit operator choices. The service must
not mutate media roots merely by starting. Operators must grant the service
account read access only to intended media roots. Broader SELinux, firewalld,
backup/restore, Tailscale Serve, authentication, and remote authorization
policies remain separate later decisions.

## Consequences

### Positive

- Fedora service shape is now reviewable in Git.
- Production startup has a read-only database readiness gate.
- Service-owned mutable state, cache, and runtime locations are stable.
- Operator-owned non-secret configuration remains under `/etc/framenest`
  without making that directory service-writable.
- The macOS development launcher stays separate from production supervision.
- Provider secrets stay out of committed templates and out of the unit.
- Production service startup no longer depends on implicit dotenv loading.

### Negative / Limitations

- The repository still does not install, enable, or verify a real Fedora host
  service.
- SELinux, firewalld, backup/restore, Tailscale Serve, authentication, and
  real NUC acceptance remain unimplemented.
- Provider calls are unavailable in production until a later approved
  service-secret integration exists.
- The secret boundary is deferred; systemd credentials or another approved
  mechanism require a later decision.

## Rejected Scope

This decision does not authorize real host provisioning, `sudo`, `systemctl`,
package installation, SSH access, Tailscale configuration, firewall changes,
SELinux policy changes, public exposure, provider-secret EnvironmentFiles,
systemd credentials, automatic migrations during service startup, database
backup/restore, or provider calls.

## Verification Expectations

Implementation must demonstrate:

- the service unit references only repository-approved executable boundaries
  under `/opt/framenest/current/.venv/bin`;
- the service unit declares stable state, cache, and runtime directories;
- the service unit does not declare `ConfigurationDirectory` or `LogsDirectory`;
- the service unit remains loopback-first through the environment template;
- the service unit contains no provider-secret file or credential variables;
- the environment template contains no provider credential variables or
  placeholder secret values;
- mutable AI configuration is under `/var/lib/framenest`;
- the production readiness gate succeeds only when the configured database is
  already at migration head;
- the readiness gate reports uninitialized, empty, behind, unknown/ahead, and
  inspection-failure databases as not ready or failed without creating or
  migrating them;
- production operations disable dotenv loading;
- `serve` delegates to the existing server runtime with explicit settings and
  does not run migrations or open a browser;
- outputs are sanitized and do not disclose database paths or tracebacks;
- imports have no execution side effects.

## Revisit Triggers

Revisit this decision when implementing real Fedora host acceptance, SELinux
policy, firewalld policy, Tailscale Serve, application-level authentication,
backup and restore, systemd credentials, another service-secret adapter, a
different installation prefix, or a non-Poetry deployment artifact.

## Related Documents

- [ADR index](README.md)
- [ADR-0005](0005-configuration-strategy.md)
- [ADR-0008](0008-asgi-runtime.md)
- [ADR-0009](0009-structured-logging-approach.md)
- [ADR-0010](0010-initial-persistence-foundation.md)
- [ADR-0022](0022-selective-media-placement-and-server-aggregation.md)
- [SERVER.md](../../SERVER.md)
- [SECURITY.md](../../SECURITY.md)
- [ROADMAP.md](../../ROADMAP.md)
