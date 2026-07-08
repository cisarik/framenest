# FrameNest Ubuntu NUC Deployment Runbook

## Status

This is the current repository-native operator runbook for preparing and
performing a future FrameNest deployment to the Intel NUC6i5SYH running Ubuntu
Server 24.04 LTS as a personal production server.

It is not a transcript, installer, host acceptance record, or claim that the
real NUC has been deployed. It must be executed only by an authorized operator
on the real host in a later bounded session.

Classification: deployment operator runbook.

Consumers: Cooperator, Orchestrator, Worker, Ubuntu operators, and security
reviewers.

Retention: remains while Ubuntu NUC deployment is the current server workflow.

Inbound links: [ADR-0032](adr/0032-ubuntu-nuc-deployment-foundation.md),
[SERVER.md](../SERVER.md), [SECURITY.md](../SECURITY.md), and
[ROADMAP.md](../ROADMAP.md).

Cleanup/update owner: future explicitly authorized Worker under an Orchestrator
task. Git history remains the archive.

## Current Target

```text
Intel NUC6i5SYH
Ubuntu Server 24.04 LTS
x86_64
personal production server
```

The future Ubuntu VPS target is portability scope only. It is not the immediate
deployment target.

## Repository Artifacts

```text
deploy/systemd/framenest.service
deploy/systemd/framenest.env.example
deploy/ubuntu/README.md
docs/adr/0032-ubuntu-nuc-deployment-foundation.md
docs/adr/0033-catalog-backup-and-recovery-foundation.md
docs/BACKUP_AND_RECOVERY.md
```

The service artifacts are source material. Committing them does not install,
enable, start, stop, reload, or inspect a real service.

## Stable Service Contract

```text
service user: framenest
service group: framenest
release root: /opt/framenest/current
production executable: /opt/framenest/current/.venv/bin/framenest-production
operator environment: /etc/framenest/framenest.env
database: /var/lib/framenest/catalog.sqlite3
non-secret AI configuration: /var/lib/framenest/ai/config.json
Gallery preview cache: /var/cache/framenest/gallery-previews
runtime root: /run/framenest
original media root: /srv/media
```

Production operations:

```text
framenest-production check-database-ready
framenest-production serve
```

The service must remain loopback-first, foreground under systemd, journal
captured, explicit-migration only, and protected by the read-only database
readiness gate.

## 0. Preconditions And Authority

Read-only checks:

- Verify the operator has a specific authorized deployment task.
- Verify the exact repository commit or release SHA to deploy.
- Verify the catalog backup and restore-to-new-destination foundation in
  [BACKUP_AND_RECOVERY.md](BACKUP_AND_RECOVERY.md) has been exercised for the
  catalog database before important production state is created.
- Verify the service user, release root, environment path, state path, cache
  path, runtime path, and media root are still the accepted paths.
- Verify the NUC is not the only important copy of any media or catalog data.

Stop conditions:

- No exact commit or release is named.
- Backup and restore are not understood.
- The operator is asked to expose FrameNest publicly.
- The operator is asked to edit live code on the NUC.
- The operator is asked to place credentials in committed files or command
  arguments.
- The operator discovers host-specific facts that conflict with ADR-0032.

Evidence:

- Exact commit or release identifier.
- Confirmation that repository `main`, tag, or release evidence is public and
  verifiable.
- Catalog backup bundle verification evidence and restore-drill evidence.

## 1. Check

Read-only checks:

- Confirm the host reports Ubuntu Server 24.04 LTS and `x86_64`.
- Confirm AppArmor status when there is a concrete reason to inspect it.
- Confirm UFW remains enabled when host hardening prerequisites claim it is
  enabled.
- Confirm no public FrameNest listener exists.
- Confirm no router forwarding or public SSH exposure is part of the plan.
- Confirm `/srv/media`, `/srv/media/memes`, `/srv/media/youtube`, and
  `/srv/media/movies` are treated as source-media locations and are not
  service-writable by default.
- Confirm the repository service artifact still binds to `127.0.0.1`.

Security control: loopback binding.

- Threat: accidental LAN or public exposure of a pre-authentication service.
- Benefit: local-only listener until a later Tailscale and authentication slice.
- Limitation: loopback does not provide remote access by itself.
- Rollback: restore `FRAMENEST_HOST=127.0.0.1` and restart only after
  readiness succeeds.
- Verification: environment file contains `FRAMENEST_HOST=127.0.0.1`; health
  checks use loopback.

Stop conditions:

- The target is not Ubuntu Server 24.04 LTS on x86_64.
- The service would bind to `0.0.0.0`.
- `/srv/media` would be made broadly writable to the service.

Evidence:

- Sanitized OS and architecture output.
- Sanitized UFW/AppArmor status when checked.
- Sanitized service environment diff.

## 2. Plan

Planned mutations:

- Select exact FrameNest commit or release.
- Select exact `uv` release version and platform artifact.
- Select exact CPython 3.13 patch version, initially `3.13.14`.
- Select exact Poetry version policy already present on the host or prepared by
  the operator.
- Decide whether activation is a first install, restart, or rollback.

Security control: pinned runtime acquisition.

- Threat: supply-chain substitution, unreviewed installer code, or mutable
  runtime drift.
- Benefit: reproducible tool and Python version with checksum and attestation
  evidence.
- Limitation: Astral `python-build-standalone` is the managed Python
  distribution source because Python does not publish official Linux
  distributable binaries.
- Rollback: keep the previous release tree and previous verified runtime until
  the new release passes readiness and health checks.
- Verification: recorded `uv --version`, `python --version`, archive checksum,
  and attestation result when available.

Stop conditions:

- The plan includes `curl | sh`, `wget | sh`, an unreviewed PPA, system Python
  replacement, or global FrameNest package installation.
- The `uv` artifact hash or attestation cannot be verified.

Evidence:

- Planned commit or release SHA.
- Planned `uv` version and artifact name.
- Planned CPython patch version.
- Planned rollback target.

## 3. Prepare Release

Planned reversible mutations:

- Fetch the exact verified commit or release into a new release tree under the
  release root policy.
- Install verified `uv` outside Ubuntu system package ownership.
- Use `uv` to provide CPython 3.13.14 without replacing Ubuntu Python.
- Point Poetry to that interpreter.
- Install the committed lock into the release-local `.venv`.
- Copy the non-secret environment template to `/etc/framenest/framenest.env`
  only if the operator environment does not already exist or the planned change
  explicitly updates it.

Security control: release-local `.venv`.

- Threat: dependency drift, global package contamination, or conflict with
  Ubuntu-managed Python packages.
- Benefit: the active service executes a release-local environment tied to the
  verified commit.
- Limitation: the operator must still maintain `uv`, Poetry, and dependencies.
- Rollback: restore `/opt/framenest/current` to the previous release and use
  its previous `.venv`.
- Verification: `/opt/framenest/current/.venv/bin/framenest-production` exists
  and reports the expected package command behavior.

Stop conditions:

- Poetry wants to update `poetry.lock`.
- `pyproject.toml` and `poetry.lock` are inconsistent.
- The release-local interpreter is not CPython 3.13.
- Any provider key is requested for `framenest.env`.

Evidence:

- Exact release tree path.
- `uv` version.
- Python version from the release-local environment.
- Poetry install result from the committed lock.

## 4. Apply One Bounded Change

Service-affecting mutations must be one bounded change at a time. Examples:

- Install or update the service unit.
- Update the non-secret environment file.
- Switch `/opt/framenest/current` to a prepared release.
- Restart the service after readiness succeeds.

Do not combine unrelated firewall, SSH, storage, Tailscale, authentication,
provider-secret, or backup implementation work with a FrameNest service switch.

Security control: least privilege service identity.

- Threat: application compromise gaining root or broad filesystem authority.
- Benefit: `framenest` service user and group limit routine service authority.
- Limitation: Unix permissions do not replace backups, AppArmor policy, or
  application authentication.
- Rollback: restore previous unit/environment/release and restart after
  readiness succeeds.
- Verification: unit contains `User=framenest` and `Group=framenest`.

Stop conditions:

- A change requires weakening SSH, UFW, AppArmor, or source-media permissions.
- A change requires entering a secret on the command line.
- A change would format, repartition, or remount storage.

Evidence:

- Sanitized before/after diff for the exact changed host artifact.
- Confirmation that no unrelated host control changed.

## 5. Migrate

Service-affecting mutation:

- Run explicit migration against the configured production database before
  service activation.

Security control: explicit migration.

- Threat: surprise schema mutation during service startup or partial startup.
- Benefit: the operator controls backup, timing, and rollback around schema
  changes.
- Limitation: migration success does not prove application health.
- Rollback: restore the pre-migration database backup and previous release if
  migration or readiness fails.
- Verification: migration command reports packaged head; readiness command
  reports ready.

Stop conditions:

- No fresh verified catalog backup exists.
- The database path is not `/var/lib/framenest/catalog.sqlite3` or another
  explicitly accepted absolute production path.
- Migration reports failure or an unexpected revision.

Evidence:

- Catalog backup verification evidence.
- Migration command result.
- Database readiness result.

## 6. Readiness Verification

Read-only check:

```text
/opt/framenest/current/.venv/bin/framenest-production check-database-ready
```

Security control: read-only readiness gate.

- Threat: starting against a missing, empty, behind, ahead, or unreadable
  database.
- Benefit: startup fails before binding the service when the database is not at
  packaged Alembic head.
- Limitation: readiness does not test networking, media availability, or remote
  client behavior.
- Rollback: restore previous release/database state and re-run readiness.
- Verification: command exits success and emits sanitized ready output.

Stop conditions:

- Readiness fails.
- Readiness creates or mutates the database.
- Output discloses private paths, SQL, tracebacks, or environment values.

Evidence:

- Sanitized readiness output.
- Confirmation that no migration ran during readiness.

## 7. Controlled Activation

Service-affecting mutation:

- Start or restart only the FrameNest service after readiness passes.
- Do not enable public listeners.
- Do not configure Tailscale in this phase.

Security control: systemd foreground supervision.

- Threat: orphaned daemons, unmanaged logs, or development launcher behavior in
  production.
- Benefit: systemd supervises one foreground `framenest-production serve`
  process and captures stdout/stderr in journald.
- Limitation: systemd supervision is not application authentication or backup.
- Rollback: stop the service, restore previous release reference, run
  readiness, and start the previous service.
- Verification: unit uses `ExecStartPre` readiness and `ExecStart` serve from
  `/opt/framenest/current/.venv/bin/framenest-production`.

Stop conditions:

- The service would use `./framenest`, Poetry as supervisor, reload mode,
  shell wrappers, or browser-opening behavior.
- The service would write to `/srv/media`.

Evidence:

- Sanitized `systemctl` status for the FrameNest unit.
- Sanitized unit content or verification output.

## 8. Health And Log Verification

Read-only checks:

- Query `GET /health` through `127.0.0.1`.
- Inspect recent journald entries for the FrameNest unit.
- Verify logs contain no credentials, private media filenames, raw provider
  responses, database paths, or tracebacks.
- Verify the service did not call a provider during startup.

Security control: sanitized journald capture.

- Threat: leaking secrets or private paths through operator logs.
- Benefit: application-owned logs use structured sanitized stderr captured by
  journald.
- Limitation: journald retention and host log access remain host policy.
- Rollback: stop the service if logs reveal sensitive data and perform a
  security incident review before continuing.
- Verification: sanitized log sample and health response.

Stop conditions:

- Health fails.
- Logs show tracebacks, raw paths, provider keys, authorization headers, or
  private media names.
- The service binds outside loopback.

Evidence:

- Sanitized health response.
- Sanitized recent log sample.
- Listener verification showing loopback binding only.

## 9. Rollback

Rollback commands and mutations must be planned before activation.

Rollback sequence:

1. Stop only the FrameNest service if the new release is running.
2. Restore the previous `/opt/framenest/current` reference.
3. Restore a verified database backup to a new path and perform the separately
   authorized controlled replacement when migration compatibility requires it.
4. Run `check-database-ready` from the restored release.
5. Start the service.
6. Verify health and logs.

Stop conditions:

- The previous release or database backup is missing.
- The previous release readiness fails.
- Rollback requires destructive storage actions not already authorized.

Evidence:

- Previous release SHA.
- Restored database backup identifier.
- Readiness result.
- Health and log verification.

## 10. Evidence Capture

Capture only sanitized evidence:

- Exact deployed commit or release SHA.
- `uv` version and artifact verification result.
- CPython version.
- Poetry install result.
- Database backup identifier.
- Migration result.
- Readiness result.
- Service activation result.
- Loopback health result.
- Sanitized logs.
- Final rollback target retained.

Do not capture or share:

- passwords;
- API keys;
- authorization headers;
- cookies;
- private keys;
- full environment dumps;
- private network values;
- disk UUIDs or serial numbers;
- SSH fingerprints;
- private media filenames;
- paths below the approved generic roots.

## Not Implemented By This Runbook

- Real deployment acceptance.
- Backup/restore tooling.
- Production provider-secret integration.
- Tailscale.
- Application authentication or authorization.
- AppArmor profile.
- UFW policy changes.
- SSH changes.
- Upload or synchronization.
- Managed ingest area.
- System-disk encryption.
- High availability.
