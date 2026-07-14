"""Programmatic Alembic migration operations for FrameNest."""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from importlib import resources
from pathlib import Path
from typing import Iterator, Literal

from alembic import command
from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory

from framenest.configuration import FrameNestSettings
from framenest.infrastructure.persistence.engine import (
    DEFAULT_BUSY_TIMEOUT_SECONDS,
    create_sqlite_engine,
    dispose_engine,
)
from framenest.infrastructure.persistence.errors import FrameNestMigrationError

DEFAULT_MIGRATION_PACKAGE = "framenest.infrastructure.persistence.alembic_environment"
MigrationState = Literal["uninitialized", "at_head", "behind", "unknown"]


@dataclass(frozen=True)
class MigrationStatus:
    """Current migration state without exposing database location."""

    state: MigrationState
    current_revision: str | None
    head_revision: str


def inspect_database_migration_status(
    settings: FrameNestSettings,
    *,
    migration_package: str = DEFAULT_MIGRATION_PACKAGE,
    busy_timeout_seconds: float = DEFAULT_BUSY_TIMEOUT_SECONDS,
) -> MigrationStatus:
    """Inspect current and head revisions without creating a missing database."""
    try:
        head_revision = _head_revision(migration_package)
        database_path = settings.database_path
        if not database_path.exists():
            return MigrationStatus(
                state="uninitialized",
                current_revision=None,
                head_revision=head_revision,
            )

        engine = create_sqlite_engine(
            database_path,
            busy_timeout_seconds=busy_timeout_seconds,
        )
        try:
            with engine.connect() as connection:
                context = MigrationContext.configure(connection)
                current_revision = context.get_current_revision()
        finally:
            dispose_engine(engine)
        return _status_from_revisions(current_revision, head_revision)
    except FrameNestMigrationError:
        raise
    except Exception as exc:
        raise FrameNestMigrationError(
            "Database migration status inspection failed.",
            error_code="MIGRATION_STATUS_FAILED",
            retryable=False,
            cause=exc,
        ) from exc


def upgrade_database_to_head(
    settings: FrameNestSettings,
    *,
    migration_package: str = DEFAULT_MIGRATION_PACKAGE,
    busy_timeout_seconds: float = DEFAULT_BUSY_TIMEOUT_SECONDS,
) -> MigrationStatus:
    """Create the explicit database boundary and upgrade it to the package head."""
    try:
        settings.database_path.parent.mkdir(parents=True, exist_ok=True)
        engine = create_sqlite_engine(
            settings.database_path,
            busy_timeout_seconds=busy_timeout_seconds,
        )
        try:
            with engine.connect() as connection:
                with _alembic_config(migration_package) as config:
                    config.attributes["connection"] = connection
                    command.upgrade(config, "head")
        finally:
            dispose_engine(engine)
        return inspect_database_migration_status(
            settings,
            migration_package=migration_package,
            busy_timeout_seconds=busy_timeout_seconds,
        )
    except FrameNestMigrationError:
        raise
    except Exception as exc:
        raise FrameNestMigrationError(
            "Database migration failed.",
            error_code="MIGRATION_FAILED",
            retryable=False,
            cause=exc,
        ) from exc


def load_script_directory(
    migration_package: str = DEFAULT_MIGRATION_PACKAGE,
) -> ScriptDirectory:
    """Load the packaged Alembic script directory for review and tests."""
    with _alembic_config(migration_package) as config:
        return ScriptDirectory.from_config(config)


def _status_from_revisions(
    current_revision: str | None,
    head_revision: str,
) -> MigrationStatus:
    if current_revision is None:
        state: MigrationState = "uninitialized"
    elif current_revision == head_revision:
        state = "at_head"
    else:
        state = "behind"
    return MigrationStatus(
        state=state,
        current_revision=current_revision,
        head_revision=head_revision,
    )


def _head_revision(migration_package: str) -> str:
    script = load_script_directory(migration_package)
    head_revision = script.get_current_head()
    if not head_revision:
        raise FrameNestMigrationError(
            "Database migration head is unavailable.",
            error_code="MIGRATION_HEAD_UNAVAILABLE",
            retryable=False,
        )
    return head_revision


@contextmanager
def _alembic_config(migration_package: str) -> Iterator[Config]:
    manager = None
    try:
        traversable = resources.files(migration_package)
        manager = resources.as_file(traversable)
        migration_root = manager.__enter__()
        config = _build_alembic_config(migration_root)
    except FrameNestMigrationError:
        raise
    except Exception as exc:
        raise FrameNestMigrationError(
            "Database migration resources are unavailable.",
            error_code="MIGRATION_RESOURCES_UNAVAILABLE",
            retryable=False,
            cause=exc,
        ) from exc
    try:
        yield config
    finally:
        if manager is not None:
            manager.__exit__(None, None, None)


def _build_alembic_config(migration_root: Path) -> Config:
    config = Config()
    config.set_main_option("script_location", str(migration_root))
    config.set_main_option("file_template", "%%(rev)s_%%(slug)s")
    return config
