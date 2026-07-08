# ADR-0032: Ubuntu NUC Deployment Foundation

## Status

`Accepted`

## Decision Date

`2026-07-08`

## Supersedes

This ADR supersedes [ADR-0031](0031-fedora-systemd-service-foundation.md) for
the active deployment target and operator workflow.

ADR-0031 remains historical evidence of the first repository-native systemd
service foundation. The still-valid platform-neutral service boundaries from
ADR-0031 are carried forward here.

## Context

FrameNest is local-first and remains in foundation-stage pre-alpha. Development
continues on the MacBook. The repository already contains a loopback-first
FastAPI/Uvicorn runtime, explicit SQLite migrations, a production executable,
and generic systemd source material under `deploy/systemd/`.

The current concrete deployment target is:

```text
Intel NUC6i5SYH
Ubuntu Server 24.04 LTS
x86_64
personal production server
```

The repository must prepare for deployment without claiming that the real NUC
has been accessed, configured, accepted, or deployed.

Ubuntu Server 24.04 is now the active deployment target. A future Ubuntu VPS
remains a portability target, not the immediate deployment target.

FrameNest requires CPython `>=3.13,<3.14`. Official Ubuntu documentation for
Python availability lists Ubuntu 24.04 LTS with Python 3.12, and the Ubuntu
package index for `python3-minimal` in Noble shows `3.12.3-0ubuntu1`. Ubuntu's
system Python must not be replaced, repointed, shadowed, or modified for
FrameNest.

Official Python release evidence shows Python 3.13.14 was released on
2026-06-10, and PEP 719 records that Python 3.13 receives bugfix releases for
about 24 months and source-only security fixes until approximately October
2029.

Official `uv` documentation says `uv` can install and manage Python versions,
that Python itself does not publish official distributable binaries, and that
`uv` uses Astral `python-build-standalone` distributions for managed Python.
Official `uv` release pages publish platform artifacts, `sha256.sum`, and
GitHub Artifact Attestation verification instructions.

Official Poetry documentation records that Poetry can use a project-local
`.venv` and that install/sync operations use the lockfile-managed environment.
Poetry remains FrameNest's dependency manager and virtual-environment authority.

Official systemd documentation supports the carried-forward service model:
`ExecStartPre`, `ExecStart`, `EnvironmentFile`, `StateDirectory`,
`CacheDirectory`, `RuntimeDirectory`, journald stdout/stderr capture, and
hardening options such as `ProtectSystem`, `ProtectHome`, `NoNewPrivileges`,
and capability bounding.

Official Ubuntu Server documentation states AppArmor is installed and loaded by
default on Ubuntu and that UFW is Ubuntu's default firewall configuration tool,
initially disabled by default. This ADR does not create AppArmor or UFW policy.

## Decision

FrameNest accepts Ubuntu Server 24.04 LTS on the Intel NUC6i5SYH as the current
concrete personal production server target.

The NUC is not high availability, enterprise hosting, a backup replacement, or
the only acceptable deployment shape. Known limitations include:

- home power outages;
- home internet outages;
- upstream bandwidth;
- consumer hardware;
- physical theft;
- disk failure;
- absence of system-disk encryption;
- the need for tested backups;
- the system SSD must not contain the only important copy.

Development remains on the MacBook:

```text
edit -> test -> commit -> push an exact verified commit or release
```

Deployment on the NUC follows the controlled release boundary:

```text
fetch the exact verified commit or release
-> prepare an isolated runtime
-> back up existing state
-> run an explicit migration
-> run the database-readiness check
-> perform a controlled service switch or restart
-> verify health and logs
```

Live development, arbitrary editing, and unverified mutable checkouts on the
server are not the accepted deployment workflow.

## CPython 3.13 Strategy

FrameNest accepts a pinned, isolated, `uv`-provisioned CPython 3.13 strategy
for Ubuntu Server 24.04 deployment.

The accepted policy is:

- Source and trust boundary: install `uv` from official `astral-sh/uv` GitHub
  release artifacts, not from a shell pipeline, unreviewed PPA, or mutable
  third-party tutorial.
- Tool version policy: pin the `uv` release version in the operator plan. The
  initial documented target is `0.11.28`, the current official release observed
  during this ADR. Updating `uv` requires a bounded maintenance step with
  checksum, attestation, and FrameNest test evidence.
- Integrity verification: download the selected platform archive and
  `sha256.sum` from the same official release, verify the archive hash before
  extraction, and verify the artifact attestation with `gh attestation verify
  --repo astral-sh/uv` when GitHub CLI is available.
- Python version policy: install exact CPython `3.13.14` initially through
  `uv python install 3.13.14`. Advancing within the 3.13 series requires a
  bounded maintenance step with tests. Changing Python minor version requires a
  superseding ADR.
- Isolation from Ubuntu Python: do not replace `/usr/bin/python3`, do not
  install FrameNest packages globally, do not install `python-is-python3` for
  FrameNest, and do not modify Ubuntu's system Python packages.
- Ownership and location: keep `uv` and managed Python under service-owned
  deployment tooling state, outside `/usr/bin` and outside Ubuntu package
  ownership. The active release uses `/opt/framenest/current/.venv`.
- Poetry install: point Poetry at the verified CPython 3.13.14 interpreter and
  install the committed lock into `/opt/framenest/current/.venv`.
- Active release reference: the systemd unit continues to execute
  `/opt/framenest/current/.venv/bin/framenest-production`.
- Update procedure: prepare a new exact commit or release on the MacBook, verify
  tests, fetch it on the server, create a new release-local environment, install
  from the committed lock, run explicit migration and readiness checks, then
  switch or restart the service.
- Rollback procedure: retain the previous release tree and database backup,
  stop the service if needed, restore the previous `/opt/framenest/current`
  reference and compatible database state, run readiness, then restart and
  verify logs.
- Maintenance responsibility: the operator owns pinned tool updates, Python
  patch updates, dependency-lock deployment, backups, rollback evidence, and
  security review.
- Portability: the same Ubuntu Server 24.04, x86_64, pinned `uv`, CPython
  3.13.14, Poetry lock, and systemd boundaries are portable to a future Ubuntu
  VPS. VPS-specific firewall, storage, provider-secret, backup, and remote
  access policies still require bounded decisions.

This strategy does not use:

```text
curl ... | sh
wget ... | sh
an unreviewed PPA
replacement of /usr/bin/python3
replacement of Ubuntu system Python packages
an arbitrary unpinned source build
an unverified binary download
a mutable unversioned runtime
```

## Service Boundaries

The systemd source artifacts remain under `deploy/systemd/` because the current
unit and environment template are platform-neutral for Ubuntu systemd.

The service identity remains:

```text
user: framenest
group: framenest
```

The release root remains:

```text
/opt/framenest/current
```

The production executable remains:

```text
/opt/framenest/current/.venv/bin/framenest-production
```

The operator environment remains:

```text
/etc/framenest/framenest.env
```

The database remains:

```text
/var/lib/framenest/catalog.sqlite3
```

The non-secret AI configuration remains:

```text
/var/lib/framenest/ai/config.json
```

The Gallery preview cache remains:

```text
/var/cache/framenest/gallery-previews
```

The runtime root remains:

```text
/run/framenest
```

The production operations remain:

```text
framenest-production check-database-ready
framenest-production serve
/opt/framenest/current/.venv/bin/framenest-production check-database-ready
/opt/framenest/current/.venv/bin/framenest-production serve
```

Production startup must remain loopback-first, require an explicitly migrated
database, use the read-only readiness gate, never run migrations implicitly,
never open a browser, never daemonize itself, never enable reload, never load a
repository `.env`, never depend on the development launcher, keep stdout and
stderr under journald capture, preserve sanitized failures, and keep provider
secrets out of committed files.

## Media Boundary

The expected server original-media root is:

```text
/srv/media
```

Expected operational category directories currently include:

```text
/srv/media/memes
/srv/media/youtube
/srv/media/movies
```

Those directory names are operational organization, not the only authority for
future catalog category semantics.

Original media must be read-only to the FrameNest service by default. The
repository must not grant, recommend, or imply broad service write access to
`/srv/media`. Future managed upload or ingest areas require a separate
server-owned boundary.

## Networking And Security Context

FrameNest remains loopback-first. The repository does not authorize router port
forwarding, a public FrameNest listener, public SSH exposure, Tailscale Funnel,
or treating tailnet membership as application authorization.

UFW should remain enabled on the host once host prerequisites are accepted, but
this ADR does not mutate firewall policy. Tailscale remains a later separate
bounded slice. Application authentication remains future work and distinct from
tailnet membership.

Ubuntu AppArmor remains part of the host security context. FrameNest does not
ship an AppArmor profile in this slice. Any future profile must be designed,
tested, and rolled back as a separate bounded task.

Provider secrets remain outside Git. Production provider-secret integration
remains unresolved; no provider key belongs in the committed environment
template. systemd credentials or another approved service-secret adapter remain
future bounded work.

Catalog backup and restore-to-new-destination tooling is accepted separately in
[ADR-0033](0033-catalog-backup-and-recovery-foundation.md). A verified catalog
backup before migration or service switch remains mandatory operator workflow;
media second-copy strategy, retention automation, production database
replacement, and real NUC restore acceptance remain outside this ADR.

## Rejected Scope

This decision does not authorize real NUC access, SSH, `sudo`, host package
installation, service-user creation, systemd installation or activation, real
database migration, private-media inspection, provider calls, credential file
creation, Tailscale configuration, UFW changes, AppArmor changes, SSH changes,
storage or mount changes, authentication, upload/ingest implementation, backup
tooling, schema changes, application source changes, or a real deployment.

## Consequences

### Positive

- Ubuntu Server 24.04 is now the documented deployment target.
- The Intel NUC6i5SYH is the concrete personal production server target.
- Fedora history remains intact while current operator guidance moves to
  Ubuntu.
- The Python 3.13 deployment path is isolated from Ubuntu's system Python.
- Existing platform-neutral systemd artifacts stay reviewable and tested.
- Deployment becomes exact-commit and rollback oriented.

### Costs and limitations

- `uv` becomes an additional deployment tool to pin, verify, and maintain.
- Managed Python distributions come from Astral `python-build-standalone`,
  because Python does not publish official Linux distributable binaries.
- Real host acceptance is still absent.
- Media backups, retention automation, production database replacement,
  provider-secret integration, Tailscale, authentication, AppArmor policy, and
  UFW policy remain unresolved or future work.
- The NUC remains vulnerable to home power, connectivity, consumer-hardware,
  physical-theft, disk-failure, and no-system-disk-encryption risks.

## Verification Expectations

Repository verification must demonstrate:

- ADR-0031 is marked superseded in the ADR index but remains historically
  intact.
- Ubuntu runbook guidance is current and does not claim real-host acceptance.
- Systemd artifacts remain loopback-first and use the read-only readiness gate.
- Migrations remain explicit and are never run by service startup.
- `/srv/media` is documented as read-only to the service by default.
- Committed deployment templates contain no provider credential variables.
- No `curl | sh`, `wget | sh`, unreviewed PPA, system Python replacement, host
  UUID, disk serial, IP address, SSH fingerprint, credential, or private media
  filename is committed.
- Any added executable deployment helper is shell-syntax checked and tested or
  statically validated.

Real deployment acceptance requires a later host-specific task with evidence
from the NUC.

## Revisit Triggers

Revisit this decision when:

- Ubuntu 24.04 gains an official supported CPython 3.13 package suitable for
  FrameNest deployment;
- FrameNest changes Python minor version;
- `uv` managed Python or its artifact verification model becomes unsuitable;
- Poetry deployment behavior changes materially;
- the service moves away from `/opt/framenest/current` or systemd;
- AppArmor, UFW, Tailscale, authentication, provider-secret integration,
  media backup, production database replacement, retention automation, or VPS
  deployment is implemented;
- the real NUC deployment produces evidence that contradicts this runbook.

## Official Sources Consulted

- Ubuntu Python availability:
  <https://ubuntu.com/developers/docs/reference/availability/python/>
- Ubuntu Noble `python3-minimal` package:
  <https://packages.ubuntu.com/noble/python/python3-minimal>
- Python 3.13.14 release:
  <https://www.python.org/downloads/release/python-31314/>
- PEP 719, Python 3.13 release schedule:
  <https://peps.python.org/pep-0719/>
- `uv` installation documentation:
  <https://docs.astral.sh/uv/getting-started/installation/>
- `uv` Python installation documentation:
  <https://docs.astral.sh/uv/guides/install-python/>
- `uv` Python versions documentation:
  <https://docs.astral.sh/uv/concepts/python-versions/>
- `uv` official GitHub releases:
  <https://github.com/astral-sh/uv/releases>
- Astral open source security:
  <https://astral.sh/blog/open-source-security-at-astral>
- Poetry CLI documentation:
  <https://python-poetry.org/docs/cli/>
- Poetry configuration documentation:
  <https://python-poetry.org/docs/configuration/>
- systemd service documentation:
  <https://www.freedesktop.org/software/systemd/man/systemd.service.html>
- systemd execution environment documentation:
  <https://www.freedesktop.org/software/systemd/man/systemd.exec.html>
- Ubuntu Server AppArmor documentation:
  <https://ubuntu.com/server/docs/how-to/security/apparmor/>
- Ubuntu Server firewall documentation:
  <https://ubuntu.com/server/docs/how-to/security/firewalls/>

## Related Documents

- [ADR index](README.md)
- [ADR-0001](0001-supported-python-version.md)
- [ADR-0002](0002-python-environment-and-dependency-manager.md)
- [ADR-0006](0006-macos-python-interpreter-provider.md)
- [ADR-0008](0008-asgi-runtime.md)
- [ADR-0009](0009-structured-logging-approach.md)
- [ADR-0010](0010-initial-persistence-foundation.md)
- [ADR-0022](0022-selective-media-placement-and-server-aggregation.md)
- [ADR-0031](0031-fedora-systemd-service-foundation.md)
- [ADR-0033](0033-catalog-backup-and-recovery-foundation.md)
- [Ubuntu NUC deployment runbook](../UBUNTU_NUC_DEPLOYMENT.md)
- [Superseded Fedora service guide](../FEDORA_SERVICE.md)
- [systemd service artifact](../../deploy/systemd/framenest.service)
- [systemd environment template](../../deploy/systemd/framenest.env.example)
- [Ubuntu deployment support map](../../deploy/ubuntu/README.md)
