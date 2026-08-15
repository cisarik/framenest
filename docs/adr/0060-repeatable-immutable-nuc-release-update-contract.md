# ADR-0060: Repeatable Immutable NUC Release-Update Contract

## Status

`Accepted`

## Decision Date

`2026-08-15`

## Context

ADR-0032 accepted the Ubuntu NUC as the personal production server target and
described an exact-commit deployment procedure: fetch an exact verified commit,
prepare an isolated runtime, back up state, migrate explicitly, verify
readiness, switch, and verify health. The runbook that followed remained a set
of phase descriptions plus historical host commands. Each later deployment
risked reconstructing the actual command sequence from chat, probing generic
`uv`/Poetry locations, and conflating the initial host bootstrap (which
provisions a pinned standalone CPython via `uv`) with the routine release
update (which must reuse the already accepted Poetry and CPython tooling).

The production host now holds an immutable release tree with a release-local
`.venv`, a `.framenest-release-sha` marker, and a deployment-local `poetry.toml`
declaring in-project virtualenvs. The routine update must be repeatable and
discoverable, must not invoke `uv`, must not guess PATH values, must preserve
the exact previous release as rollback, and must never run migrations or
replace production secrets.

## Decision

FrameNest adopts one repository-native routine immutable release-update
contract under `deploy/ubuntu/`:

- `deploy/ubuntu/framenest-release` is the single Fish-compatible operator
  entry point. It resolves the repository root and invokes the repository
  `.venv/bin/python` to run the engine.
- `deploy/ubuntu/framenest_release.py` is the standard-library engine with
  four public commands and a private transferred remote mode.

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

The engine uses only the Python standard library and stays compatible with
Ubuntu system Python 3.12 for its private transferred remote mode.

### Exact tooling and immutability

Routine updates reuse exactly:

```text
Poetry:  /opt/framenest/tooling/poetry/2.4.1/.venv/bin/poetry
CPython: /opt/framenest/tooling/python/cpython-3.13.14-linux-x86_64-gnu/bin/python3.13
```

`uv` was used only to provision the pinned standalone CPython during the
initial host bootstrap and for later explicit tooling maintenance. Routine
release updates never invoke `uv` and never require `uv` on `PATH`.

Releases live at `/opt/framenest/releases/<40-hex-SHA>`, the active reference
is `/opt/framenest/current`, and the environment file is
`/etc/framenest/framenest.env`. Deployed releases intentionally contain no
`.git` metadata. Provenance is recorded in `.framenest-release-sha` and
`.framenest-release-manifest.json`, which is how `status` and future probes
read release identity rather than `git -C /opt/framenest/current`. A
pre-manifest production tree is observed via `.framenest-release-sha` only;
synthesizing a manifest on an old immutable tree is forbidden.

### Source and public gates

Deployment requires a full lowercase 40-hex commit SHA whose local `HEAD`
matches, whose superproject and `.ap` worktrees are clean, whose
`refs/heads/main` public ref equals it, and whose local `.ap` `HEAD` is
identical to the release gitlink. Abbreviated, dirty, unpublished, moving, or
ambiguous source is rejected. The canonical owner checkout is never modified.

### Release artifact

Two exact archives are built: one superproject archive from the selected commit
and one separate AP archive from the gitlink pinned by that commit. AP `main` is
never followed. Both byte streams are hashed locally and re-verified remotely
before extraction. Every archive member is validated before extraction,
rejecting absolute paths, `..`, path escape, devices, unsafe links, or any
member outside its designated root. Pinned AP content is materialized under
`<release>/.ap/`.

### Preparation, cutover, rollback

Preparation writes a deployment-local `poetry.toml` (`[virtualenvs]
in-project = true`), runs `poetry check --lock`, `poetry env use <tooling
CPython>`, and `poetry install --only main --no-interaction --no-ansi`, and
verifies the committed `poetry.lock` is not changed. Staging-prefix paths
inside the in-project venv (console-script shebangs and editable install
metadata such as `.pth` and `direct_url.json`) are rewritten to the final
release prefix before the tree is made non-writable. The completed source and
`.venv` are root-controlled and non-writable by the service account. Staging is
renamed to the final release only after every gate passes.

Cutover requires target readiness under the accepted service-account contract,
then atomically replaces `/opt/framenest/current`, restarts
`framenest.service` exactly once, and verifies active release identity, service
state, database readiness, health (including Tailscale UDS ingress), working
directory, and sanitized logs. Automatic rollback restores the captured
previous release after a post-switch failure.

### Backup and schema boundary

`check` requires `restore_readiness=ready` from the sanitized backup status.
`deploy` runs one fresh scheduled create/verify/disposable-restore checkpoint
before cutover and requires successful terminal evidence. The first
implementation supports same-schema routine updates only: the production
database revision must equal the packaged target head, otherwise the helper
stops with a sanitized `migration-required` result before cutover. The helper
never runs `framenest-db migrate` and never hides migration authority.

### Privilege and transport

Transport mirrors the strict SSH settings of the existing Worker gate, reuses
the GPG SSH-agent socket safely, never handles passwords, and uses `sudo -n`
only for privileged remote phases after the Cooperator has established the sudo
timestamp outside the helper. For deploy/rollback the exact Python engine is
transferred to an exact temporary remote path, SHA-256 verified, and executed
only in its private fixed remote mode with validated scalar arguments. The
read-only `status` and `check` paths use only fixed, tested commands and create
no remote state.

## Consequences

### Positive

- One discoverable, tested routine update path replaces reconstructed chat
  commands and PATH guessing.
- Immutable release identity is explicit and independent of Git metadata.
- Exact rollback and negative-path behavior are exercised by contract tests.
- Bootstrap versus routine-update responsibilities are separated.

### Costs and limitations

- The first implementation is same-schema only; migration stays a separately
  authorized task and must not be smuggled into the helper.
- Real deployment remains unproven until a later E3 host task with fresh
  preflight, Cooperator approval, and independent acceptance.
- The engine is security-sensitive and must be independently audited before
  publication or live use.

## Related Documents

- [ADR-0032](0032-ubuntu-nuc-deployment-foundation.md)
- [ADR-0052](0052-automated-catalog-backup-retention-and-restore-verification.md)
- [Ubuntu NUC deployment runbook](../UBUNTU_NUC_DEPLOYMENT.md)
- [Backup and recovery runbook](../BACKUP_AND_RECOVERY.md)
- [NUC host baseline](../NUC_HOST_BASELINE.md)
- [Deployment support map](../../deploy/ubuntu/README.md)
