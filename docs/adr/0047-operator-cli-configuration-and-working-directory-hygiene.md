# ADR-0047: Operator CLI Configuration and Working-Directory Hygiene

## Status

`Accepted`

## Decision Date

2026-07-23

## Context

The first real NUC deployment of the accepted YouTube Manual Ingestion and
Provenance MVP ([ADR-0046](0046-youtube-manual-ingestion-and-provenance.md))
surfaced three concrete operator frictions that did not affect the deployed
service itself but made administrative operation fragile:

1. `load_settings()` defaulted to an implicit, caller-working-directory
   relative `.env` probe. Every administrative CLI sharing the loader
   (`framenest-db`, `framenest-youtube`, `framenest-catalog`,
   `framenest-library`, `framenest-previews`, `framenest-ai`,
   `framenest-server`) inherited that probe. An unreadable `.env` in the
   caller's working directory made commands fail with a sanitized error even
   when the complete required configuration was supplied explicitly, and an
   unsearchable working directory made behavior depend on incidental
   `pathlib` error swallowing.
2. Operator commands executed under a service-account identity transition
   (`sudo -u framenest ...`) inherited the caller's working directory, which
   the service account could not traverse when that directory was a user
   home.
3. Operator documentation presented only the repository-root `./framenest`
   Fish development launcher for YouTube ingestion, which cannot run on the
   NUC and is not a production prerequisite.

ADR-0005 and ADR-0007 accept an ignored local `.env` layer for development
convenience, and ADR-0031/ADR-0032 already require production service
operations to load settings with the explicit no-dotenv boundary. The gap was
that administrative CLIs kept the implicit development-oriented probe even in
production operation, and no tracked command established an explicit safe
working directory across the identity transition.

## Decision

Configuration loading uses explicit-only environment-file authority:

- `load_settings()` never probes the caller's working directory for an
  implicit `.env` file.
- An explicit `env_file` argument remains authoritative and must name a
  readable regular file.
- `env_file=None` disables environment-file loading entirely; the production
  runtime (`framenest-production`) keeps this boundary unchanged per
  ADR-0031.
- An omitted argument consults the `FRAMENEST_ENV_FILE` process environment
  variable; when set, it is an authoritative explicit file, and when unset
  or empty, no environment file is loaded.
- A missing, unreadable, or unloadable explicit file fails closed with a
  sanitized `FrameNestConfigurationError` that discloses neither the path
  nor the contents. Process environment variables keep the highest
  precedence, preserving the ADR-0005 layering.

Operator-facing CLIs map that failure to stable sanitized error codes
(`FRAMENEST_DB_CONFIGURATION_FAILED`, `YOUTUBE_CONFIGURATION_FAILED`, the
existing sanitized AI configuration channel, and a sanitized
`framenest-server` startup message) instead of raw exceptions or misleading
loopback errors.

Development convenience remains deterministic and repository-rooted: the
CachyOS Fish launcher exposes a regular non-symlink repository-root `.env`
as `FRAMENEST_ENV_FILE` for its CLI subcommands only when the operator has
not already set the variable. The managed development server and the
production runtime never read environment files.

Tracked deployment and operator commands that change execution identity must
establish a safe working directory as part of the transition. The NUC
runbook uses `sudo -u framenest --chdir=/opt/framenest/current` (supported
by the documented Ubuntu Server 24.04 platform) with the release-local
console entry points and the explicit `FRAMENEST_ENV_FILE` environment. The
production AI credential helper's service-account `configure` invocation
establishes the same explicit release working directory. No command may
solve a working-directory or permission failure by broadening access to a
user home directory.

## Consequences

### Positive

- Administrative and production CLI behavior is identical from any working
  directory.
- A random or unreadable `.env` in a caller working directory can neither
  break nor influence production configuration.
- Explicit configuration failure is deterministic, sanitized, and
  actionable.
- The NUC operator interface is documented with release-local, shell-neutral
  entry points; Fish is not a production prerequisite.
- Service-account processes always start from a traversable explicit
  directory.

### Costs and risks

- Direct development invocations that silently relied on a working-directory
  `.env` must now set `FRAMENEST_ENV_FILE` explicitly; the launcher preserves
  the repository-rooted convenience.
- The operator contract depends on `sudo --chdir`, which the documented
  Ubuntu Server 24.04 platform provides.

## Related Documents

- [ADR index](README.md)
- [ADR-0005](0005-configuration-strategy.md)
- [ADR-0007](0007-settings-library.md)
- [ADR-0031](0031-fedora-systemd-service-foundation.md)
- [ADR-0032](0032-ubuntu-nuc-deployment-foundation.md)
- [ADR-0046](0046-youtube-manual-ingestion-and-provenance.md)
- [Ubuntu NUC deployment runbook](../UBUNTU_NUC_DEPLOYMENT.md)
- [SPEC.md](../../SPEC.md)
