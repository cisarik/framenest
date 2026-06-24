# Next Orchestrator Handoff

## 1. Purpose and authority

This file restores orchestration state for a fresh Orchestrator session. It is not an executable task. Permanent documentation, current code, tests, Git history, and accepted ADRs remain authoritative.

The fresh Orchestrator must independently verify public `main` and must not treat this file as task authority.

**Current ORCHESTRATOR session: CLOSED.**

## 2. Repository identity and expected state

- Repository: `https://github.com/cisarik/framenest.git`
- Local path used by Worker: `/Users/agile/framenest`
- Branch: `main`
- Pre-handoff public HEAD: `e43001eba2daafed27db6a3d304279cd61c04db4`
- Latest verified test baseline: **94 passed**, zero warnings
- Resolve the final handoff commit from public `main` after push; do not assume this file contains the post-handoff SHA.

## 3. Role and communication rules

- Michal is the COOPERATOR
- The ChatGPT orchestration chat is the ORCHESTRATOR
- The repository execution role is WORKER
- Analytic Programming is provider- and model-neutral
- Orchestrator ↔ Cooperator communication is Slovak
- Worker prompts and reports are English
- Worker reports begin with: `### Report for ORCHESTRATOR_CHAT`
- Issue one bounded authoritative task at a time
- User-facing Worker prompts use: `Toto pošli WORKEROVI ako jeden prompt:`

## 4. Current product direction

Essential FrameNest invariants:

- local-first
- privacy-conscious
- cross-platform
- premium gallery and acquisition are flagship capabilities
- one logical media item may have multiple physical locations
- portable sidecars plus local indexes
- optional server aggregation must not replace desktop autonomy
- external VLC is the initial full-player path
- Tailscale is the remote-access direction
- Fedora KDE on an Intel NUC is a later deployment target

See [PRODUCT.md](PRODUCT.md) and [SPEC.md](SPEC.md) for normative detail.

## 5. Implemented technical foundation

Current verified implementation:

- centralized typed configuration with loopback-safe defaults
- FastAPI application factory and typed `GET /health`
- Uvicorn runtime with explicit safety settings and console entrypoint `framenest-server`
- FrameNest-owned structured JSON logging with centralized redaction
- disabled Uvicorn access logging
- strict direct-process JSON output contract
- clean direct-process SIGINT and SIGTERM shutdown without application traceback
- documented application-versus-launcher output boundary
- import-boundary, configuration, API, runtime, logging, process-output, and cleanup tests

Current test count at handoff base HEAD: **94 passed**, zero warnings.

## 6. Accepted decisions

| ADR | Decision | Implementation state |
|---|---|---|
| [0001](docs/adr/0001-supported-python-version.md) | CPython 3.13 | active |
| [0002](docs/adr/0002-python-environment-and-dependency-manager.md) | Poetry | active |
| [0003](docs/adr/0003-initial-server-api-framework.md) | FastAPI adapter | active |
| [0004](docs/adr/0004-repository-layout.md) | hybrid staged src-layout | active |
| [0005](docs/adr/0005-configuration-strategy.md) | layered configuration | active |
| [0006](docs/adr/0006-macos-python-interpreter-provider.md) | `uv` on macOS | active |
| [0007](docs/adr/0007-settings-library.md) | `pydantic-settings` | active |
| [0008](docs/adr/0008-asgi-runtime.md) | Uvicorn | active |
| [0009](docs/adr/0009-structured-logging-approach.md) | stdlib structured logging | implemented |
| [0010](docs/adr/0010-initial-persistence-foundation.md) | SQLAlchemy Core + Alembic | accepted, not implemented |

No database dependency exists in `pyproject.toml` or `poetry.lock`.

## 7. Latest completed work

Recent meaningful sequence:

- structured logging foundation per ADR-0009
- server shutdown and output correction with direct-process contract tests
- universal AP Worker handoff transport clarification
- provider-neutral WORKER role in AP and bootstrap documents
- transient database-stack research with no committed evidence artifact
- ADR-0010 acceptance for the initial persistence foundation

## 8. Persistence strategy

Accepted constraints from [ADR-0010](docs/adr/0010-initial-persistence-foundation.md):

- synchronous SQLAlchemy 2.x Core
- Alembic for schema migrations
- `sqlite+pysqlite` as the SQLite dialect
- FrameNest-owned repository and transaction boundaries
- no SQLAlchemy ORM mapped entities
- no SQLModel
- no async SQLite access initially
- no silent migration during normal server startup
- explicit upgrade-only migrations initially
- server should eventually detect incompatible schema and refuse safely
- WAL is deferred pending macOS and Fedora evidence
- the database is a rebuildable local index or cache, not the durable synchronization protocol

## 9. Exact next orchestration strategy

The fresh Orchestrator should:

1. verify the final public `main` and both handoff files
2. inspect ADR-0010, the current settings boundary, package layout, tests, and dependencies
3. issue one bounded test-first implementation task for the minimal persistence foundation
4. keep media-domain tables completely out of that task
5. require dependency addition through Poetry
6. require exact import boundaries and no ORM or async leakage
7. require an explicit migration command and schema-status boundary
8. require temporary-directory database tests
9. require no automatic migration during normal server startup
10. independently verify the resulting public commit

Shape the final implementation prompt from current repository truth rather than treating this handoff as task authority.

## 10. First implementation acceptance boundary

The next implementation may prove only:

- database path configuration
- SQLAlchemy engine or connection creation
- foreign keys on each connection
- bounded busy handling
- explicit transaction commit and rollback
- Alembic environment and revision `0001`
- empty-to-head migration
- current and head schema inspection
- deterministic reopen
- migration failure behavior
- explicit migrate and status command or equivalent boundary
- installed-package migration resource discovery
- no HTTP dependency
- no media schema

## 11. Known risks and deferred decisions

- `greenlet` or other native-wheel portability must be checked on supported platforms
- Fedora validation remains future work
- WAL mode and checkpoint policy remain undecided
- default database path and exact busy timeout remain implementation decisions
- backup, restore, and corruption recovery are deferred
- sidecar schema and durable identity model are unresolved
- Alembic autogenerate is non-authoritative
- SQLAlchemy Core expressions must not leak out of infrastructure
- a database row must not become canonical durable metadata

## 12. AP lifecycle state

- the outgoing Worker session is closed
- the outgoing Orchestrator session is closed
- the next Worker should be a completely fresh session
- a fresh Orchestrator must read [BOOT_ORCHESTRATOR.md](BOOT_ORCHESTRATOR.md), [AP_ORCHESTRATOR.md](AP_ORCHESTRATOR.md), and this file
- repository handoffs are read directly from the repository and normally not pasted manually
- neither NEXT file grants task or Git authority
