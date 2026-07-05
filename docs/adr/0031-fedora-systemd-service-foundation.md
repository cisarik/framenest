# ADR-0031: Fedora systemd Service Foundation

## Status

`Accepted`

## Decision Date

`2026-07-06`

## Decision Authority

The Orchestrator authorized this repository-native deployment-infrastructure
slice as the first Fedora systemd service foundation. The task explicitly
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
- production deployment not depending on developer `.env` files or the local
  `.secrets/ai.env.fish` helper;
- Tailscale-only remote-access direction unless superseded later.

Before this decision, the repository had no systemd unit, production service
environment template, or production startup gate.

## Decision

FrameNest accepts a repository-native Fedora systemd service foundation.

The committed service bundle is documentation and deployment source material.
It is not an installer and must not activate a real host by itself.

The production service runs the existing installed application process:

```text
/opt/framenest/.venv/bin/framenest-server
```

The production service must preserve the existing macOS/local development
launcher. The root `./framenest` launcher remains browser-development tooling
and is not the production supervisor boundary.

The production service uses an explicit database-readiness gate before server
startup:

```text
/opt/framenest/.venv/bin/framenest-production check-database-ready
```

The gate is read-only. It inspects the configured Alembic revision through the
existing migration-status boundary, must not create a missing database, must not
run migrations, must not bind a listener, and must not print database paths,
SQL, environment values, or raw exceptions.

Production startup refuses operation unless the configured database is already
at packaged migration head. Operators must run the explicit migration command
before starting or restarting the service when the database is uninitialized or
behind:

```text
framenest-db migrate
```

The Fedora service-owned boundaries are:

- state: `/var/lib/framenest`;
- cache: `/var/cache/framenest`;
- configuration: `/etc/framenest`;
- runtime: `/run/framenest`.

The initial production catalog path is:

```text
/var/lib/framenest/catalog.sqlite3
```

The initial production gallery-preview cache path is:

```text
/var/cache/framenest/gallery-previews
```

The initial non-secret server AI configuration path is:

```text
/etc/framenest/ai/config.json
```

The production non-secret environment file is:

```text
/etc/framenest/framenest.env
```

The committed template is:

```text
deploy/systemd/framenest.env.example
```

Provider credentials remain out of the non-secret template. A host-local secret
environment file may be supplied at:

```text
/etc/framenest/framenest-secrets.env
```

That file is intentionally not committed. It is a service-secret boundary for
current provider environment variables such as `NVIDIA_API_KEY` and
`AI_GATEWAY_API_KEY` until a later secret-store or systemd-credentials decision
supersedes it.

The service remains loopback-bound by default with `FRAMENEST_HOST=127.0.0.1`.
Public bind addresses are not the default. Future Tailscale Serve integration
must preserve loopback backend binding unless a later accepted security decision
supersedes this.

The unit captures application logs through systemd/journald from process
stdout/stderr. FrameNest still does not implement application-owned log files,
rotation, retention, or remote log shipping.

## Security And Operational Boundaries

The unit uses a dedicated service account named `framenest`.

The unit declares systemd-owned state, cache, configuration, and runtime
directories through `StateDirectory`, `CacheDirectory`,
`ConfigurationDirectory`, and `RuntimeDirectory`.

The unit applies baseline hardening including `NoNewPrivileges=true`,
`PrivateTmp=true`, `ProtectSystem=strict`, `ProtectHome=read-only`, kernel and
control-group protection, SUID/SGID restriction, personality locking, and a
private umask.

Registered media libraries remain explicit operator choices. The service must
not mutate media roots merely by starting. Operators must grant the service
account read access to intended media roots. Broader SELinux, firewalld,
backup/restore, Tailscale Serve, authentication, and remote authorization
policies remain separate later decisions.

## Consequences

### Positive

- Fedora service shape is now reviewable in Git.
- Production startup has a read-only database readiness gate.
- Service-owned state, cache, configuration, and runtime locations are stable.
- The macOS development launcher stays separate from production supervision.
- Provider secrets stay out of committed templates.

### Negative / Limitations

- The repository still does not install, enable, or verify a real Fedora host
  service.
- SELinux, firewalld, backup/restore, Tailscale Serve, authentication, and
  real NUC acceptance remain unimplemented.
- The secret boundary is an optional host-local environment file, not final
  systemd credentials or OS keychain integration.

## Rejected Scope

This decision does not authorize real host provisioning, `sudo`, `systemctl`,
package installation, SSH access, Tailscale configuration, firewall changes,
SELinux policy changes, public exposure, automatic migrations during service
startup, database backup/restore, or provider calls.

## Verification Expectations

Implementation must demonstrate:

- the service unit references only repository-approved executable boundaries;
- the service unit declares stable state, cache, configuration, and runtime
  directories;
- the service unit remains loopback-first through the environment template;
- the environment template contains no provider credential variables or
  placeholder secret values;
- the production readiness gate succeeds only when the configured database is
  already at migration head;
- the readiness gate reports uninitialized and behind databases as not ready
  without creating or migrating them;
- outputs are sanitized and do not disclose database paths;
- imports have no execution side effects.

## Revisit Triggers

Revisit this decision when implementing real Fedora host acceptance, SELinux
policy, firewalld policy, Tailscale Serve, application-level authentication,
backup and restore, systemd credentials, a different installation prefix, or a
non-Poetry deployment artifact.

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
