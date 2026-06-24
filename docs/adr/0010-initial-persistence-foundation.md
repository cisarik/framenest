# ADR-0010: Initial SQLite Persistence and Migration Strategy

## Status

`Accepted`

## Decision Date

`2026-06-24`

## Decision Authority

The Cooperator delegated the final persistence-stack choice to the Orchestrator. The Orchestrator selected **synchronous SQLAlchemy 2.x Core with Alembic** after primary-source comparison of a standard-library-only runner, SQLAlchemy Core, SQLAlchemy ORM, and SQLModel bundles. The decision was recorded through bounded task `FRAMENEST-CYCLE-035-ADR-0010-PERSISTENCE-FOUNDATION`. Transient decision-support evidence was consumed without creating a committed research artifact.

## Context

FrameNest is local-first. Each desktop will eventually own a complete local catalog. SQLite is an index or cache and must not become the sole durable metadata representation. Future portable sidecar metadata remains the intended durable metadata layer. Live SQLite database files must not be synchronized between devices as the durable metadata protocol.

Verified repository state at decision time:

- No database module, schema, repository, migration environment, or database dependency exists.
- `pyproject.toml` contains no SQLAlchemy, Alembic, SQLModel, or `aiosqlite` dependency.
- Phase 4 still requires the initial SQLite catalog boundary and migration mechanism ([ROADMAP.md](../../ROADMAP.md)).
- Domain identities, media schema, library scanning, and sidecar contracts are not yet implemented.
- Initial development runs on Apple Silicon macOS with CPython 3.13 ([ADR-0001](0001-supported-python-version.md)).
- Later server deployment targets Fedora Linux on an Intel NUC.
- Domain and application layers must remain independent of FastAPI ([ADR-0003](0003-initial-server-api-framework.md)).
- Configuration, logging, and runtime boundaries already require infrastructure adapters and secret redaction ([ADR-0005](0005-configuration-strategy.md), [ADR-0009](0009-structured-logging-approach.md)).

Primary-source comparison retrieval date: **2026-06-24**.

Related documents:

- [ADR-0001](0001-supported-python-version.md)
- [ADR-0003](0003-initial-server-api-framework.md)
- [ADR-0004](0004-repository-layout.md)
- [ADR-0005](0005-configuration-strategy.md)
- [ADR-0008](0008-asgi-runtime.md)
- [ADR-0009](0009-structured-logging-approach.md)
- [SPEC.md](../../SPEC.md)
- [SECURITY.md](../../SECURITY.md)
- [ROADMAP.md](../../ROADMAP.md)

## Decision

### Accepted access and query strategy

1. FrameNest **MUST** use **synchronous SQLAlchemy 2.x Core** for its initial SQLite persistence layer.
2. SQLAlchemy **MUST** use the standard-library SQLite driver through the **`sqlite+pysqlite`** dialect.
3. The initial implementation **MUST NOT** use:
   - SQLAlchemy ORM mapped entities;
   - SQLModel;
   - `aiosqlite`;
   - SQLAlchemy async engines or sessions.
4. FastAPI does not require asynchronous database access.
5. SQLite's single-writer model means async access is **not** accepted merely for stylistic consistency.
6. Persistence details **MUST** remain inside infrastructure adapters.
7. Domain and application layers **MUST NOT** import:
   - SQLAlchemy;
   - Alembic;
   - SQLite driver types;
   - SQL expression objects;
   - persistence row models.
8. Application code **MUST** depend on FrameNest-owned repository or transaction interfaces.
9. SQLAlchemy Core expressions **MUST NOT** escape repository or infrastructure boundaries.
10. Database rows **MUST NOT** become the canonical durable metadata contract.
11. Parameterized statements are mandatory.
12. Raw SQL string interpolation with untrusted values is prohibited.

### Connection and transaction invariants

1. Every new SQLite connection **MUST** explicitly enable foreign-key enforcement.
2. Foreign-key enforcement **MUST** be verified by tests.
3. Transaction ownership **MUST** be explicit and FrameNest-controlled.
4. Connection and transaction lifetimes **MUST** be deterministic.
5. A bounded busy timeout **MUST** be configured.
6. Infinite retries or unbounded lock waiting are prohibited.
7. Database paths and raw driver errors **MUST NOT** leak through ordinary API responses or unsafe logs.
8. Tests **MUST** use isolated temporary databases outside the repository.
9. Connection cleanup **MUST** be deterministic.
10. Abrupt shutdown and failed transaction behavior **MUST** be covered by tests.

This ADR does **not** accept a concrete pool class, exact timeout duration, or final connection-factory module name.

### Migration strategy

1. FrameNest **MUST** use **Alembic** for initial schema migration management.
2. Migration revisions **MUST** be:
   - ordered through Alembic's revision graph;
   - committed;
   - reviewable;
   - deterministic;
   - immutable after release or shared use.
3. Alembic's version tracking is the migration authority.
4. FrameNest **MUST NOT** introduce a redundant `schema_migrations` table solely to duplicate Alembic revision tracking.
5. Alembic batch migrations **MUST** be available for SQLite table-rebuild operations.
6. Autogenerate **MAY** produce candidate changes but **MUST NOT** be treated as complete or automatically authoritative.
7. Every generated revision **MUST** be manually reviewed.
8. Destructive or lossy migration operations require explicit review and task authority.
9. Migration execution **MUST** be separately testable from HTTP startup.
10. Migration failures **MUST NOT** leave the application claiming a successful current schema.
11. Migration commands and errors **MUST** use sanitized output.
12. Migration resources **MUST** remain available in an installed package or deployment layout.

### Startup migration policy

1. Normal server startup **MUST NOT** silently apply pending migrations.
2. Migrations **MUST** initially require an explicit user or operator command.
3. Server startup **SHOULD** inspect the current schema revision.
4. If the schema is behind, unknown, or incompatible, the server **SHOULD** refuse normal operation with a sanitized actionable error.
5. Exact command names and CLI layout remain implementation details.
6. Future guarded automatic migration would require a superseding or amending ADR.

### Upgrade and downgrade policy

1. Initial migrations are upgrade-only.
2. Downgrade implementations are not required initially.
3. Empty or unsupported downgrade functions **MUST** be explicit rather than pretending reversibility.
4. Recovery from a failed or unwanted migration **MUST** rely on tested backup, restore, or rebuild procedures developed later.
5. An irreversible migration **MUST** be clearly identified before execution.

### WAL policy

1. WAL is **not** accepted as an unconditional architecture invariant yet.
2. WAL is a likely implementation-time default for supported local filesystems after tests.
3. WAL **MUST NOT** be assumed safe for network filesystems.
4. WAL behavior **MUST** be validated on:
   - Apple Silicon macOS local storage;
   - Fedora Linux local storage.
5. Journal-mode selection, checkpoint policy, and busy-timeout values remain bounded implementation decisions.
6. The application **MUST NOT** silently place databases on unsupported remote or network storage.

### Integrity, backup, and rebuildability

1. SQLite integrity checks and foreign-key checks **MUST** remain available to later operational tooling.
2. SQLite backup functionality is separate from schema migration.
3. Backup, restore, corruption repair, and catalog rebuild commands are deferred.
4. The selected stack **MUST NOT** prevent rebuilding the catalog from future durable metadata.
5. Database deletion or reset remains a destructive operation requiring explicit safeguards.

### First implementation boundary

The first implementation after ADR acceptance **MUST** remain a persistence foundation, not a media catalog.

It **MAY** include only enough behavior to prove:

- database path configuration;
- SQLAlchemy engine or connection creation;
- foreign-key enforcement;
- bounded busy handling;
- explicit transactions;
- Alembic configuration;
- migration from an empty database to revision `0001`;
- current and head revision inspection;
- deterministic reopen;
- failed-transaction rollback;
- failed-migration behavior;
- explicit migrate and status commands or equivalent programmatic boundaries;
- no HTTP dependency;
- no ORM models;
- no media, library, device, series, tag, location, cover, or sidecar tables.

A minimal neutral foundation table **MAY** be introduced only if required to prove migration behavior. Alembic's own version table alone **MAY** be sufficient if implementation tests can prove the required boundary.

### Explicitly deferred decisions

This ADR does **not** silently decide:

- exact SQLAlchemy or Alembic versions;
- exact package or module names;
- engine pool class;
- exact busy timeout;
- concrete database default path;
- WAL default;
- checkpoint policy;
- migration command name;
- final repository interfaces;
- unit-of-work API;
- media catalog schema;
- stable identity format;
- sidecar schema;
- full-text search schema;
- JSON column usage;
- backup and restore commands;
- corruption recovery;
- database encryption;
- multi-process write coordination beyond the initial bounded migration guard;
- remote or server aggregate database design.

This ADR does **NOT** authorize dependency installation, database code, migration directories, CLI commands, or tests for unimplemented behavior.

## Alternatives Considered

### Standard-library `sqlite3` with a FrameNest-owned migration runner

**Strongest alternative.** Zero new database dependency and maximal direct control. FrameNest would need to own revision ordering, checksums, locking, resource packaging, partial-failure recovery, and SQLite table-rebuild migration behavior because SQLite provides almost no `ALTER` support for many schema changes. Reconsider if dependency minimization or binary-wheel portability becomes unacceptable.

### SQLAlchemy ORM + Alembic

Mature option with mapped persistence entities and session complexity before the domain exists. Risks persistence models becoming domain or durable metadata models. Not selected initially.

### SQLModel + Alembic

Convenient FastAPI and Pydantic integration. Risks conflating API validation, persistence, and domain models. Conflicts with FrameNest's boundary-first architecture. Not selected.

## Primary Sources

Research retrieval date: **2026-06-24**.

| Topic | Source |
|---|---|
| Python 3.13 `sqlite3` module | https://docs.python.org/3.13/library/sqlite3.html |
| SQLite foreign keys | https://www.sqlite.org/foreignkeys.html |
| SQLite transactions | https://www.sqlite.org/lang_transaction.html |
| SQLite WAL mode | https://www.sqlite.org/wal.html |
| SQLite `busy_timeout` pragma | https://www.sqlite.org/pragma.html#pragma_busy_timeout |
| SQLite backup API (via Python) | https://docs.python.org/3.13/library/sqlite3.html#sqlite3.Connection.backup |
| SQLAlchemy 2.x Core | https://docs.sqlalchemy.org/en/20/core/ |
| SQLAlchemy SQLite dialect | https://docs.sqlalchemy.org/en/20/dialects/sqlite.html |
| Alembic tutorial | https://alembic.sqlalchemy.org/en/latest/tutorial.html |
| Alembic programmatic API | https://alembic.sqlalchemy.org/en/latest/api/commands.html |
| Alembic batch migrations for SQLite | https://alembic.sqlalchemy.org/en/latest/batch.html |
| Alembic autogenerate | https://alembic.sqlalchemy.org/en/latest/autogenerate.html |
| SQLAlchemy PyPI metadata | https://pypi.org/project/SQLAlchemy/ |
| Alembic PyPI metadata | https://pypi.org/project/alembic/ |

## Rationale

SQLAlchemy Core with Alembic is proportionate for Phase 4 because SQLite migration requires table-rebuild workflows that Alembic documents and implements for SQLite batch operations, while Core preserves explicit SQL and repository boundaries without introducing ORM mapped entities before the domain exists. Synchronous access matches the current loopback-first Uvicorn runtime and SQLite's single-writer concurrency model. Explicit migration commands align with FrameNest security and destructive-operation safeguards.

Keeping persistence inside infrastructure adapters preserves domain independence required by ADR-0003, ADR-0004, and ADR-0005.

## Consequences

### Positive

- Mature SQLite migration support through Alembic batch operations.
- Explicit query construction without ORM domain coupling.
- Reusable Alembic revision tooling and review workflow.
- Clear repository boundary behind FrameNest-owned ports.
- Future replacement remains possible behind repository interfaces.

### Costs and risks

- New runtime dependencies including SQLAlchemy, Alembic, and transitive packages such as `greenlet` on supported platforms.
- SQLAlchemy and Alembic learning and configuration complexity.
- Temptation to leak Core expressions outside infrastructure.
- Alembic autogenerate can produce incomplete candidate migrations.
- Packaging and migration-environment correctness require dedicated tests.

### Mitigations

- Confine SQLAlchemy and Alembic imports to infrastructure modules.
- Enforce repository ports in domain and application layers.
- Require manual review of every migration revision.
- Test migration discovery from installed package layout.
- Defer WAL, backup, and catalog rebuild tooling to later bounded tasks.

## Verification Expectations

Future implementation must demonstrate at minimum:

- dependency and import boundaries;
- Python 3.13 on macOS;
- later Fedora installation;
- foreign keys on every connection;
- parameter binding;
- transaction commit and rollback;
- bounded busy behavior;
- migration from empty database;
- current and head revision reporting;
- repeated migration idempotence at head;
- migration failure rollback or explicit failure state;
- concurrent migration attempt behavior;
- installed-package migration-resource discovery;
- no HTTP dependency;
- no persistence implementation leakage into domain or application layers;
- no sensitive path or SQL leakage in ordinary logs or errors.

## Revisit Triggers

Revisit this decision when any of the following occur:

- SQLAlchemy or Alembic no longer supports the project runtime;
- `greenlet` or packaging failures appear on supported macOS or Fedora systems;
- Core expressions repeatedly leak across repository boundaries;
- the migration environment becomes disproportionately complex;
- the catalog's rebuildable-cache nature makes a smaller stdlib runner clearly safer;
- async access becomes necessary due to demonstrated workload evidence;
- another migration tool materially reduces complexity without weakening safety;
- future database-server requirements invalidate SQLite-specific assumptions.

## Related Documents

- [ADR index](README.md)
- [ADR-0003](0003-initial-server-api-framework.md)
- [ADR-0004](0004-repository-layout.md)
- [ADR-0005](0005-configuration-strategy.md)
- [ADR-0008](0008-asgi-runtime.md)
- [ADR-0009](0009-structured-logging-approach.md)
- [SPEC.md](../../SPEC.md)
- [SECURITY.md](../../SECURITY.md)
- [ROADMAP.md](../../ROADMAP.md)
- [AGENTS.md](../../AGENTS.md)
