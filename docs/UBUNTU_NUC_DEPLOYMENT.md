# FrameNest Ubuntu NUC Deployment Runbook

## Status

This is the current repository-native operator runbook for preparing and
operating FrameNest on the Intel NUC6i5SYH running Ubuntu Server 24.04 LTS as a
personal production server.

It is not a transcript of every historical host command and does not by itself
grant mutation authority. Public `main` and the production release may differ;
the authoritative mutable production readback is the authenticated runtime
command `framenest-release status` (see the Routine Immutable Release Update
section below), never a committed SHA snapshot. A production release was
previously accepted at public/canonical commit
`aec2f0091c10aed2fc2033dac154a0d9651b2b6d` (schema `0028`) served from
`/opt/framenest/releases/aec2f0091c10aed2fc2033dac154a0d9651b2b6d` with
Tailscale Serve only; that fact is dated history, not a current guarantee.
Execute host mutations only under an authorized operator task.

Classification: deployment operator runbook.

Consumers: Cooperator, Orchestrator, Worker, Ubuntu operators, and security
reviewers.

Retention: remains while Ubuntu NUC deployment is the current server workflow.

Inbound links: [ADR-0032](adr/0032-ubuntu-nuc-deployment-foundation.md),
[NUC_HOST_BASELINE.md](NUC_HOST_BASELINE.md), [SERVER.md](../SERVER.md),
[SECURITY.md](../SECURITY.md), [ROADMAP.md](../ROADMAP.md), and
[OPERATOR_NETWORK.md](OPERATOR_NETWORK.md).

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
deploy/systemd/framenest-ai-credential-nvidia-nim.conf
deploy/systemd/framenest-ai-credential-vercel-ai-gateway.conf
deploy/ubuntu/fn-production-env-deploy
deploy/ubuntu/framenest-release
deploy/ubuntu/framenest_release.py
deploy/ubuntu/README.md
docs/adr/0032-ubuntu-nuc-deployment-foundation.md
docs/adr/0060-repeatable-immutable-nuc-release-update-contract.md
docs/adr/0033-catalog-backup-and-recovery-foundation.md
docs/adr/0036-production-ai-credentials-via-systemd.md
docs/NUC_HOST_BASELINE.md
docs/BACKUP_AND_RECOVERY.md
```

The service artifacts are source material. Committing them does not install,
enable, start, stop, reload, or inspect a real service.

[NUC_HOST_BASELINE.md](NUC_HOST_BASELINE.md) records accepted sanitized
host hardening and media-storage baseline facts. It does not grant mutation
authority and is historical host evidence, not a substitute for current release
acceptance.

## Stable Service Contract

```text
service user: framenest
service group: framenest
release root: /opt/framenest/current
production executable: /opt/framenest/current/.venv/bin/framenest-production
operator environment: /etc/framenest/framenest.env
database: /var/lib/framenest/catalog.sqlite3
non-secret AI configuration: /var/lib/framenest/ai/config.json
durable cover storage: /var/lib/framenest/covers
cover thumbnails: /var/cache/framenest/cover-thumbnails
YouTube acquisition staging: /var/lib/framenest/youtube-acquisition
Gallery preview cache: /var/cache/framenest/gallery-previews
runtime root: /run/framenest
original media root: /srv/media
```

Production operations:

```text
framenest-production check-database-ready
framenest-production serve
```

Release-local operator console entry points:

```text
/opt/framenest/current/.venv/bin/framenest-db
/opt/framenest/current/.venv/bin/framenest-youtube
/opt/framenest/current/.venv/bin/framenest-ai
/opt/framenest/current/.venv/bin/framenest-backup
/opt/framenest/current/.venv/bin/framenest-previews
```

Automated catalog backup assets (ADR-0052):

```text
deploy/systemd/framenest-catalog-backup.service
deploy/systemd/framenest-catalog-backup.timer
```

Optional off-device catalog copy assets (ADR-0056):

```text
deploy/systemd/framenest-catalog-offdevice.service
deploy/systemd/framenest-catalog-offdevice.timer
```

These off-device units remain repository source material until a separately
authorized host task provisions `/mnt/framenest-catalog-offdevice`, sets the
non-secret destination ID, and accepts the physical failure domain. Installing
or enabling them is not part of ordinary repository implementation.

Operator-workstation pull assets (ADR-0057):

```text
deploy/ubuntu/framenest-catalog-export-v1
```

Console surfaces after the feature release is deployed:

```text
/opt/framenest/current/.venv/bin/framenest-backup export-latest
/opt/framenest/current/.venv/bin/framenest-recovery
```

The export launcher and exact no-argument sudoers bridge are later host
provisioning only. Current production may remain on an older SHA until an
authorized immutable deployment publishes this capability. Repository presence
alone does not enable real workstation pulls.

Install and enable the local backup timer only under an authorized deployment
task after the feature release is active:

```text
# [NUC / bash]
sudo install -m 0644 deploy/systemd/framenest-catalog-backup.service /etc/systemd/system/
sudo install -m 0644 deploy/systemd/framenest-catalog-backup.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now framenest-catalog-backup.timer
systemctl list-timers framenest-catalog-backup.timer
sudo -u framenest --chdir=/opt/framenest/current \
  env FRAMENEST_ENV_FILE=/etc/framenest/framenest.env \
  /opt/framenest/current/.venv/bin/framenest-backup status
#------------------------------------------------------
```

Manual oneshot trigger:

```text
# [NUC / bash]
sudo systemctl start framenest-catalog-backup.service
sudo systemctl status framenest-catalog-backup.service --no-pager
#------------------------------------------------------
```

Rollback to a release that lacks `run-scheduled` must disable and stop the timer
before switching `current`, then remove or leave the units disabled:

```text
# [NUC / bash]
sudo systemctl disable --now framenest-catalog-backup.timer
sudo systemctl disable --now framenest-catalog-backup.service
sudo systemctl daemon-reload
#------------------------------------------------------
```

The daily local pipeline creates an `auto-` catalog bundle, verifies it,
restores it to a disposable destination, records restore-readiness, and expires
only eligible automatic bundles. It does not back up original media bytes.
Defaults and operator commands are documented in
[BACKUP_AND_RECOVERY.md](BACKUP_AND_RECOVERY.md). The optional ADR-0056
off-device timer copies that verified recovery point to a distinct mount and
restore-verifies it; repository presence alone is not proof of host-loss
survival. The preferred current off-host layer is ADR-0057 operator-workstation
pull, which remains repository capability until later E3 launcher/sudoers/store
provisioning and the first accepted real pull/verify.

The service must remain loopback-first, foreground under systemd, journal
captured, explicit-migration only, and protected by the read-only database
readiness gate.

## Operator Command Execution Contract

Every FrameNest service-account operator command on the NUC must run under an
explicit identity transition that also establishes the immutable release root
as the working directory:

```text
sudo -u framenest --chdir=/opt/framenest/current \
  env FRAMENEST_ENV_FILE=/etc/framenest/framenest.env \
  /opt/framenest/current/.venv/bin/<entry-point> <arguments>
```

- Ubuntu Server 24.04 provides `sudo` with `--chdir` support. The
  service-account process always starts inside the immutable release root,
  which that account can traverse. It never inherits the caller's working
  directory.
- Configuration authority is explicit. FrameNest administrative and
  production commands never read a `.env` file from any working directory.
  An environment file is applied only when explicitly requested through
  `FRAMENEST_ENV_FILE`; a missing or unreadable explicit file fails closed
  with a sanitized error, and process environment variables keep the highest
  precedence.
- Never run service-account commands from a user home directory. Never solve
  a working-directory or permission failure by broadening access to a user
  home or any other unrelated directory, changing its ownership, or adding
  the service account to a personal group.
- The repository-root `./framenest` launcher is CachyOS Fish development
  tooling. It is not installed on the NUC and must not be used there. The
  release-local console entry points above are the only NUC operator
  interface; Fish is not a production prerequisite.
- `framenest-production` is an exception by design: it reads only the
  process environment (supplied by the systemd unit's `EnvironmentFile`)
  and runs readiness and serving through the unit's own
  `WorkingDirectory=/opt/framenest/current`.

### YouTube Operator Ingestion

YouTube manual ingestion uses the release-local `framenest-youtube` console
entry point under the same contract, never the development launcher:

```text
sudo -u framenest --chdir=/opt/framenest/current \
  env FRAMENEST_ENV_FILE=/etc/framenest/framenest.env \
  /opt/framenest/current/.venv/bin/framenest-youtube ingest URL --yes
sudo -u framenest --chdir=/opt/framenest/current \
  env FRAMENEST_ENV_FILE=/etc/framenest/framenest.env \
  /opt/framenest/current/.venv/bin/framenest-youtube status CLAIM_ID
sudo -u framenest --chdir=/opt/framenest/current \
  env FRAMENEST_ENV_FILE=/etc/framenest/framenest.env \
  /opt/framenest/current/.venv/bin/framenest-youtube retry CLAIM_ID --yes
```

The CLI reaches only the loopback server. Without `--yes` it asks for
interactive confirmation on stdin, which requires an interactive operator
session.

### Gallery Preview Operator Generation

Persistent Gallery preview derivatives for GIF and video cards are generated
explicitly through the release-local `framenest-previews` console entry point
under the same contract, never the development launcher and never on demand
from the Gallery preview HTTP endpoint:

```text
sudo -u framenest --chdir=/opt/framenest/current \
  env FRAMENEST_ENV_FILE=/etc/framenest/framenest.env \
  /opt/framenest/current/.venv/bin/framenest-previews status
sudo -u framenest --chdir=/opt/framenest/current \
  env FRAMENEST_ENV_FILE=/etc/framenest/framenest.env \
  /opt/framenest/current/.venv/bin/framenest-previews generate --all --yes
```

`status` is read-only. `generate` prints a plan and requires `--yes` or an
interactive confirmation before writing JPEG derivatives under
`/var/cache/framenest/gallery-previews`.

## Routine Immutable Release Update

The canonical, discoverable, tested routine immutable release-update entry
point is:

```text
deploy/ubuntu/framenest-release
```

It invokes `deploy/ubuntu/framenest_release.py` (standard library only; Ubuntu
system Python 3.12 compatible for its private transferred remote mode). The
architecture decision is [ADR-0060](adr/0060-repeatable-immutable-nuc-release-update-contract.md).

Public commands:

```text
framenest-release status [transport arguments]
framenest-release check --release <40-hex-SHA> [transport arguments]
framenest-release deploy --release <40-hex-SHA> --yes [transport arguments]
framenest-release rollback --release <40-hex-SHA> --yes [transport arguments]
```

Transport arguments are `--target`, `--user`, and `--identity`, with public-safe
fallbacks `FRAMENEST_NUC_SSH_TARGET`, `FRAMENEST_NUC_SSH_USER`, and
`FRAMENEST_NUC_SSH_IDENTITY`.

### Initial bootstrap versus routine update

Initial host bootstrap provisions the pinned standalone CPython through `uv`,
installs Poetry tooling, creates the service identity, and performs the first
release installation. Those are separate, explicitly authorized maintenance
tasks.

Routine immutable release updates reuse the already accepted tooling exactly:

```text
Poetry:  /opt/framenest/tooling/poetry/2.4.1/.venv/bin/poetry
CPython: /opt/framenest/tooling/python/cpython-3.13.14-linux-x86_64-gnu/bin/python3.13
```

A routine update never invokes `uv`, never requires `uv` on `PATH`, never
installs or downloads tooling automatically, and fails closed with a sanitized
result when the exact tooling is missing or mismatched.

### Modes

- `status` and `check` are read-only with respect to the repository, database,
  service, and host state. They use only fixed, tested commands and create no
  remote state. They must not transfer a helper, refresh sudo, or transition
  into deployment automatically.
- `deploy` re-runs every check gate, then builds and hashes two exact archives
  (superproject and pinned AP), transfers exact bytes, verifies hashes
  remotely, prepares a release-local `.venv` from the committed `poetry.lock`,
  atomically publishes the release, runs a fresh verified catalog checkpoint,
  and performs the atomic cutover and single restart. Pre-cutover
  `framenest-production` readiness uses a oneshot `systemd-run` with the unit
  `EnvironmentFile` because that binary reads only the process environment.
  After restart, deploy and automatic rollback wait up to 30 seconds
  (one-second polling) for active state, database readiness, and health;
  transient `activating` / socket-not-ready / health-not-ready states retry,
  terminal systemd states fail immediately, and deadline expiry is
  `EXIT_READINESS_TIMEOUT`. `--yes` prevents accidental execution but is not
  AP or Cooperator authority.
- `rollback` switches to an already complete release under
  `/opt/framenest/releases/<SHA>`. It never references a
  `/opt/framenest/rollback` path.

### Same-schema boundary and privilege release

This first implementation supports same-schema routine updates only. The
production database revision must equal the packaged target head; any schema
difference stops before cutover with a sanitized `migration-required` result.
The helper never runs `framenest-db migrate` and never hides migration
authority.

Privileged remote phases use `sudo -n` only after the Cooperator has
established the sudo timestamp outside the helper. At terminal handling the
Cooperator invalidates the sudo timestamp through the exact supported route
when the session remains available; if the session is lost first, privilege
release is reported unknown rather than fabricated.

Interrupted, ambiguous, or failed state retains bounded recovery evidence under
`/run/framenest-release-deploy` and provides an exact operator recovery
instruction. A partial target is never deployable; final release publication is
atomic; no wildcard deletion occurs.

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
- If YouTube ingestion is configured, confirm its pre-existing `0700` staging
  root is under `/var/lib/framenest`, is not a symlink, and is disjoint from
  the database, quarantine, preview cache, and every registered media root.
- Confirm any production AI credential plan uses optional systemd
  `LoadCredential=` drop-ins and root-controlled files under
  `/etc/framenest/credentials`, not `framenest.env` or command-line arguments.

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
- YouTube acquisition would require write access to `/srv/media` or any
  source-media library.

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

### Production AI Credential Helper

`deploy/ubuntu/fn-production-env-deploy` is repository-owned source
material for a later explicitly authorized production AI credential task. Its
documented entry point is:

```text
fn-production-env-deploy
```

The helper manages only one selected AI provider credential plus non-secret
provider/model selection. It supports a non-mutating `--check` mode, accepts an
explicit SSH target or non-secret operator environment default, transfers the
credential over SSH stdin rather than argv, uses only `sudo -n` remotely,
atomically acquires `/run/framenest-ai-credential-deploy` before production
mutation, installs deployment-controlled files atomically, and waits up to 30
seconds for bounded readiness. Existing recovery material causes a fail-closed
stop before credential transmission, configuration, restart, health polling, or
rollback. Check mode validates the selected private credential source and the
selected tracked provider-specific drop-in template locally before any SSH
activity.

The systemd credential drop-in source is always the exact tracked template
under `deploy/systemd/` for the selected provider. The helper validates the
template's strict two-line `LoadCredential=` contract locally, transfers the
template bytes as a non-secret stdin payload separate from the credential
payload, installs them to a `.next` path, proves byte equivalence before and
after atomic rename, and never reconstructs line breaks with shell escaping.
After non-secret provider/model configuration is written, the helper verifies
systemd acceptance before restart: `systemd-analyze verify`, daemon reload,
enabled state, loaded drop-in path, exact on-disk drop-in
`LoadCredential=IDENTITY:PATH` mapping via trusted drop-in bytes and
`systemctl cat` (not redacted `systemctl show LoadCredential`), and unchanged
base service unit. Only after those gates pass may it restart
`framenest.service`. After readiness succeeds, it calls only the loopback
`/api/ai/media-suggestion-capability` endpoint and requires the selected
provider/model to be configured, available, and credential-available. A
historical connection-test record must not fail deployment and is not proof
that the newly installed credential is valid; live proof remains an explicit
later `framenest-ai test`.

The helper starts rollback only after a complete backup marker has been written.
That backup records present/absent state for the selected credential, the
systemd credential drop-in, and `/var/lib/framenest/ai/config.json`. Rollback
restores those states, removes pending `.next` artifacts, daemon-reloads,
restarts, and uses the same bounded readiness contract for `framenest.service`.
Deployment terminal service failure and readiness timeout both trigger rollback.
Rollback terminal service failure and rollback readiness timeout are reported as
distinct sanitized outcomes, and recovery material remains under
`/run/framenest-ai-credential-deploy` for operator recovery.

The later operator may create a Fish wrapper or function that invokes the
repository script, but this repository task does not install anything into
`~/.config/fish`.

## 5. Migrate

Service-affecting mutation:

- Run explicit migration against the configured production database before
  service activation, using the operator command execution contract:

```text
sudo -u framenest --chdir=/opt/framenest/current \
  env FRAMENEST_ENV_FILE=/etc/framenest/framenest.env \
  /opt/framenest/current/.venv/bin/framenest-db migrate
```

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

Read-only checks:

The readiness gate itself runs inside the service unit through
`ExecStartPre` with the unit's own `WorkingDirectory` and `EnvironmentFile`:

```text
/opt/framenest/current/.venv/bin/framenest-production check-database-ready
```

Manual operator verification of the same migration contract uses the
read-only status form under the operator command execution contract:

```text
sudo -u framenest --chdir=/opt/framenest/current \
  env FRAMENEST_ENV_FILE=/etc/framenest/framenest.env \
  /opt/framenest/current/.venv/bin/framenest-db status
```

AI status preflight uses the network-free read-only form with the explicit
non-secret AI configuration path:

```text
sudo -u framenest --chdir=/opt/framenest/current \
  env FRAMENEST_ENV_FILE=/etc/framenest/framenest.env \
  /opt/framenest/current/.venv/bin/framenest-ai \
  --config-path /var/lib/framenest/ai/config.json status --no-write
```

The ordinary `framenest-ai status` command may record a safe local status
snapshot. Use `--no-write` when deployment preflight must avoid creating or
modifying AI status files.

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

- Query `GET /health` through `127.0.0.1`, or run the release-local
  `framenest-production check-health` command, which uses the Unix socket
  automatically when the Tailscale ingress mode from section 11 is active.
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

## 11. Tailscale Remote Access Ingress

This phase is a separately authorized slice. It is not part of the base
activation above and requires its own bounded task authority.

Architecture:

```text
authenticated tailnet browser
  -> Tailscale HTTPS Serve (root-owned tailscaled)
  -> /run/framenest/framenest.sock (service-account Unix socket)
  -> FrameNest tailscale_uds ingress mode
```

Security properties:

- The application stops listening on TCP entirely; Tailscale Serve is the
  only remote application ingress.
- Serve strips and reinjects `Tailscale-User-*` identity headers; the
  application trusts them only in this ingress mode, bound to the protected
  Unix socket, and never trusts same-named headers from any other channel.
- `RuntimeDirectory=framenest` (mode `0750`, service account only) and
  `UMask=0077` keep the socket closed to normal login users; the root-owned
  `tailscaled` can always reach it.
- An explicit configuration identity map assigns roles; unknown verified
  identities are denied, privileged actions are capability-checked and
  recorded in the durable `security_audit_events` table.
- Browser mutations require the exact external `Origin` plus the
  `X-FrameNest-Request: 1` header; no CORS middleware is enabled.

Configuration (placeholders; see `deploy/systemd/framenest.env.example`):

```text
FRAMENEST_INGRESS_MODE=tailscale_uds
FRAMENEST_UDS_PATH=/run/framenest/framenest.sock
FRAMENEST_EXTERNAL_ORIGIN=https://<node>.<tailnet>.ts.net
FRAMENEST_IDENTITY_MAP={"<verified-login>":"<admin|user>"}
```

Rules:

- The exact verified Serve login must be observed through
  `GET /api/identity/me` from an authenticated tailnet client before the
  admin mapping is written.
- The database must be backed up before migration `0020` runs, and the
  backup readability must be verified.
- Health verification in this mode uses the release-local
  `framenest-production check-health` command, which speaks to the Unix
  socket; there is no separate TCP health listener.
- Funnel stays disabled. No LAN binding, no tailnet-wide ACL, DNS, user, or
  tag changes, and no stale node cleanup belong to this slice.

Serve activation (root, after the application is healthy on the socket):

```bash
tailscale serve --bg unix:/run/framenest/framenest.sock
tailscale serve status --json
tailscale funnel status
```

Verification:

- No FrameNest TCP listener remains (`ss -tlnp` shows no port 8000).
- `tailscale serve status --json` shows exactly one HTTPS handler to the
  Unix socket, and Funnel reports no configuration.
- `framenest-production check-health` reports ready.
- `GET /api/identity/me` through the tailnet HTTPS URL returns the expected
  login, role, and capability list.

Rollback:

1. Capture `tailscale serve status --json` before any change; remove only
   the FrameNest Serve handler (`tailscale serve reset` is acceptable only
   when the captured state was empty).
2. Remove the four ingress environment keys and restore the previous
   `/opt/framenest/current` reference.
3. Restore the pre-migration database backup when the previous release
   predates migration `0020`, per `docs/BACKUP_AND_RECOVERY.md`.
4. Restart the service and verify loopback health.

Stop conditions:

- Tailscale is below the accepted minimum version, Serve Unix-socket proxying
  is unsupported, or MagicDNS/HTTPS would require a tailnet-wide setting that
  is not already enabled.
- The observed Serve login differs from the intended admin identity.
- A normal login user can open the application socket.

## Not Implemented By This Runbook

- Real deployment acceptance of the automated catalog-backup timer on a host.
- Off-device copies, media-byte backup, and in-place production catalog overwrite.
- Live production provider-secret deployment or provider testing.
- Tailscale Funnel or any ingress beyond the authenticated tailnet.
- Live Mullvad exit-node assignment; see [OPERATOR_NETWORK.md](OPERATOR_NETWORK.md)
  and [ADR-0058](adr/0058-independent-mullvad-egress-and-operator-network-recovery.md).
- Multi-user administration UI, invitations, or per-user personal metadata.
- AppArmor profile.
- UFW policy changes.
- SSH changes.
- Upload or synchronization.
- Managed ingest area.
- System-disk encryption.
- High availability.
