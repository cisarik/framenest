# ADR-0085: Kronika Sole Identity

## Status

`Accepted`

Accepted by the Cooperator on 2026-10-02. This decision records the accepted
product identity and its single remaining spelling. It does not rename any
package, command, header, unit, or host path by itself, does not implement,
deploy, or contact the NUC, and does not claim the code has already moved.

## Decision Date

2026-10-02

## Context

[ADR-0082](0082-kronika-one-product-and-private-records.md) accepted one Kronika
in this repository and, for that stage, deliberately kept the `framenest`
internal package, migration history, compatible HTTP headers, and deployment
identifiers, and excluded a mass `framenest` rename. That was a staged hold, not
the terminal product identity.

The Cooperator has now decided that the `framenest` product identity does not
remain. The product is Kronika, including its package, commands, settings
prefix, HTTP mutation header, and the NUC layout. This ADR fixes the single
target identity and the exact points at which each spelling changes, so that the
rename is an ordered, reversible-at-each-step sequence rather than a mass
replacement.

Applied migration history, on-disk backup artifacts, and the accepted tooling
paths are engineering constraints that outlast this rename. They are named here
as frozen residues so they are not later mistaken for unfinished rename work.

## Decision

### Sole product identity

The product identity is Kronika.

- Import package: `kronika`, at `src/kronika`.
- Distribution name: `kronika`.
- `provenanceModule` in `ap.project.conf`: `kronika`.
- Console scripts: `kronika-*`, mapped in the accepted identity cut sequence.
- Root launcher: `./kronika`.

There is exactly one spelling for each of these after the sequence completes.
Compatibility spellings that exist during the sequence are temporary readers and
aliases, not a second identity.

### Settings, header, and command error codes

- Settings environment prefix: `KRONIKA_`.
- HTTP mutation header: `X-Kronika-Request: 1`.
- Command error-code strings: `KRONIKA_` prefix after the removal cut.

Numeric command exit statuses are unchanged.

### Web host layout on the NUC

- Release tree: `/opt/kronika/releases`, `/opt/kronika/current`.
- Environment file: `/etc/kronika/kronika.env`.
- State: `/var/lib/kronika`. Cache: `/var/cache/kronika`.
- Unix socket: `/run/kronika/kronika.sock`.
- Unix account and group: `kronika`.
- Units: `kronika.service`, `kronika-catalog-backup.service`,
  `kronika-catalog-backup.timer`, `kronika-catalog-offdevice.service`,
  `kronika-catalog-offdevice.timer`.

The web release entry point becomes `deploy/ubuntu/kronika-release`. It is the
same release engine, not a second deployment system. The existing release helper
remains the only deployment system throughout.

### Applied migration bytes and the loader alias

Applied Alembic bytes through revision `0035` remain byte-identical and are
never edited. A later cut moves the Alembic directory with the package; a path
may change, those bytes may not.

The only mechanism that loads
`from framenest.infrastructure.persistence.sqlite_batch_fk import ...` is a
process-local `sys.modules` alias installed by the migration loader at the start
of script-directory load. After the package cut there is no `src/framenest`
package and no `framenest` distribution; the alias is the sole bridge for that
one applied revision.

### Named frozen residues

These keep the former spelling on purpose. They are not pending rename work.

- The accepted tooling paths:
  `/opt/framenest/tooling/poetry/2.4.1/.venv/bin/poetry` and
  `/opt/framenest/tooling/python/cpython-3.13.14-linux-x86_64-gnu/bin/python3.13`.
- Protocol magic `FNCBE01`.
- The capture state-directory name `framenest-chatgpt-page`.
- The off-device mount path `/mnt/framenest-catalog-offdevice`.
- Historical ADR bodies, including this ADR's citations.
- [docs/FEDORA_SERVICE.md](../FEDORA_SERVICE.md) and
  [docs/NUC_HOST_BASELINE.md](../NUC_HOST_BASELINE.md).
- Existing backup archives and sidecars, which readers keep accepting.

### Ordered implementation, not mass replacement

The compatibility windows and their removal gates are the ordered cuts of the
accepted identity cut sequence (ADR to cut C0 through C9). A mass
search-and-replace is not an implementation of this ADR. Each cut is a separate
bounded grant; each one keeps the running NUC serving.

## Consequences

- There is one product identity, Kronika, with a single spelling per surface.
- Applied migration history stays verifiable and byte-stable across the rename.
- Backups and sidecars written under either accepted spelling stay readable.
- The rename is auditable cut by cut; a premature or missed rename fails loudly
  at the cut that owns it rather than at the end.
- Temporary compatibility spellings exist only inside the ordered sequence and
  are removed by their stated gates.

## Supersession

This ADR partially supersedes
[ADR-0082](0082-kronika-one-product-and-private-records.md), **by citation, not
by patch**. ADR-0082 is not edited; its original wording stays as historical
decision text, and its historical reasoning stays in that file. ADR-0085
supersedes exactly three passages of ADR-0082:

- ADR-0082 lines 87-89: the internal `framenest` package, migration history,
  compatible HTTP headers, and deployment identifiers remaining during that
  stage, and the exclusion of a mass `framenest` rename.
- ADR-0082 lines 208-209: the `framenest` package, provenance module, migration
  history, HTTP headers, and deployment identifiers staying.
- ADR-0082 line 196, "Local paths need not be renamed," superseded only for the
  product commands, the settings prefix, the mutation header, the systemd unit
  names, and the host paths named in this ADR. It is **not** superseded for Git
  history, for the historical MacBook path in old artifacts, or for the accepted
  tooling paths named above.

Every other ADR-0082 decision, and the ADR-0083 and
[ADR-0084](0084-administrator-managed-research-settings-and-versioned-pricing.md)
decisions, are unaffected and remain accepted.

## Boundaries restated as still accepted

This whole inherits, and this ADR does not change:

- One repository, `cisarik/kronika`. No Git history rewrite and no force push.
- The former capture repository `cisarik/cli_chatgpt`, at commit
  `66c40d43c577276b0ad304a494fbbb1ffb6fc933`, stays active.
- The parked capture module and its constraints: one persistent browser,
  loopback-only token authentication, bounded attachment staging, and explicit
  `needs_admin` recovery without automatic resend. It uses the page as
  configured, with no model or reasoning inspection and no fallback to an
  external API.
- Gallery remains a separate, frozen working view.
- The administrator-curated Timeline, with owner-private records, administrator
  read of product records, and household publication only by administrator
  approval.
- Internet publication stays disabled; the public composition stays off.
- Search and Research use the ADR-0083 and ADR-0084 provider boundary, with
  research disabled by default and no automatic fallback.
- Loopback-first service; Tailscale-only remote ingress; no router port
  forwarding.
- A single release helper as the only deployment system.

## Revisit criteria

A different product name, a different import or distribution name, a change to
the frozen tooling or off-device paths, or a new applied migration revision
requires a later accepted decision. Changing this identity does not require
revisiting the identity itself.

## Non-grants

This ADR grants no implementation, no deploy, no host migration, and no change
to applied migration bytes. Each identity cut requires its own bounded grant.