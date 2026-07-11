# FrameNest Agent Instructions

FrameNest is a local-first, privacy-conscious, cross-platform library for video
and animated media. It is in foundation-stage pre-alpha development with a
working loopback FastAPI server, SQLite/Alembic persistence, packaged local web
shell, catalog and metadata foundations, server-side AI suggestion review, a
catalog backup foundation, and repository-native systemd source material for an
Ubuntu NUC deployment workflow.

<!-- BEGIN MANAGED AP INTEGRATION -->
## Analytic Programming

This project uses Analytic Programming through the pinned Git submodule at `.ap/`.
The exact AP version is the commit recorded by this repository's `.ap` gitlink.

Required reading:
- All participants read `.ap/AP.md`.
- Orchestrators also read `.ap/AP_ORCHESTRATOR.md`.
- Workers also read `.ap/AP_WORKER.md`.
- Prompt structures are in `.ap/PROMPT_CONTRACTS.md`.

Project-specific rules outside this managed block remain authoritative within
their scope. Task authority comes only from the current authoritative
Orchestrator prompt.

Treat `.ap/` as read-only during ordinary project work. Protocol updates require
a separate explicit AP update task.
<!-- END MANAGED AP INTEGRATION -->

## Project Truth

Repository files, tests, Git history, public commits, ADRs, and current product
documents are the source of truth. Worker reports are structured claims and must
be verified against repository and public evidence when commits are involved.

Current product, system, and operational truth is distributed across:

- [README.md](README.md) for repository status and user-facing overview.
- [PRODUCT.md](PRODUCT.md) for approved product direction.
- [SPEC.md](SPEC.md) for normative product and system requirements.
- [ROADMAP.md](ROADMAP.md) for staged development.
- [SECURITY.md](SECURITY.md) for security policy and privacy boundaries.
- [SERVER.md](SERVER.md) for authoritative server/client and NUC direction.
- [docs/UBUNTU_NUC_DEPLOYMENT.md](docs/UBUNTU_NUC_DEPLOYMENT.md) for the
  Ubuntu NUC deployment runbook.
- [docs/BACKUP_AND_RECOVERY.md](docs/BACKUP_AND_RECOVERY.md) for the catalog
  backup and recovery foundation.
- [docs/NUC_HOST_BASELINE.md](docs/NUC_HOST_BASELINE.md) for sanitized,
  command-observed NUC host baseline facts.
- [docs/adr/README.md](docs/adr/README.md) for accepted architecture decisions.

When sources conflict, identify the exact conflict, determine whether a source
is stale, incomplete, misunderstood, or intentionally superseded, and escalate
strategic conflicts to Michal through the Orchestrator.

## Communication

The COOPERATOR is Michal. Orchestrator communication with Michal is in Slovak,
addresses him with masculine grammatical forms, and uses feminine grammatical
forms for Orchestrator self-reference.

Repository documentation, code documentation, Worker prompts, and Worker reports
are written in professional English unless a task explicitly says otherwise. Do
not use Czech in repository documents, Worker prompts, or Worker reports.

Worker reports begin exactly:

```markdown
### Report for ORCHESTRATOR_CHAT
```

Human-facing command blocks for Michal's MacBook use Fish-compatible syntax and
begin with:

```text
# [MacBook / fish]
```

Human-facing command blocks for an already-open NUC session use Bash-compatible
syntax and begin with:

```text
# [NUC / bash]
```

Every human-facing command block for either environment ends with:

```text
#------------------------------------------------------
```

Do not mix MacBook and NUC commands in one unlabeled block.

## Security Boundaries

Private media access requires explicit task authority. Real provider calls
require explicit task authority. Credentials, secret values, private keys,
tokens, cookies, authorization headers, private media filenames, host-specific
identifiers, disk serials, UUIDs, SSH fingerprints, and private network values
must not be exposed in repository artifacts or reports.

NUC, SSH, sudo, firewall, storage, package-manager, deployment, systemd,
AppArmor, UFW, Tailscale, and mount mutations require explicit bounded
authority. Availability of a connection, credential, terminal, mounted disk, or
tool is capability context, not authority.

FrameNest backend services must remain loopback-first by default. No router port
forwarding is accepted for FrameNest. Remote access direction remains
Tailscale-only unless a later accepted decision supersedes it. Tailscale
membership is not application administrator authority.

Original server media under `/srv/media` is read-only to the service by default.
Do not grant broad service write access to source media to implement upload or
ingest. Ordinary clients must never receive provider secrets.

## Product Boundaries

FrameNest remains local-first. A FrameNest server process is authoritative for
catalog and server-owned state, but it may run locally and must not turn local
ownership into public-cloud dependence. The premium gallery remains a flagship
product invariant.

Rendered UX acceptance belongs to Michal. The accepted Gallery and Details MVP
visual behavior remains frozen unless a concrete defect is identified.

Do not hide new product scope inside infrastructure, deployment, backup,
protocol, or migration work. Do not claim desktop app, real host deployment,
Tailscale, authentication, production provider-secret integration, arbitrary
collection management, persistent AI Drafts, covers, thumbnails, upload,
synchronization, or complete backup coverage until repository evidence proves
it.

## Git And Lifecycle

Do not perform Git write operations without task-specific authority. When Git
writes are authorized, stay within the exact branch, path, commit, push, and
verification authority in the task.

FrameNest uses the AP submodule at `.ap/` for universal protocol, role,
authority, Worker lifecycle, diagnostic closeout, Git, verification, prompt,
artifact, update, and exceptional handoff semantics. Do not duplicate universal
AP protocol text in project-local files.

Permanent `BOOT_*`, `NEXT_*`, `WORKERS.md`, `NEXT_AGENT.md`,
`ORCHESTRATOR_HANDOFF.md`, and `WORKER_HANDOFF.md` files are not part of the
current live repository model. Orchestrator rotation normally uses a generated
professional restoration prompt. A repository handoff is exceptional context
only and may be created or changed only by an explicitly authorized Worker task
that names its exact path, consumer, lifecycle, validation, and Git authority.
