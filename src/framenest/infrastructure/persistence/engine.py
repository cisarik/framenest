"""Synchronous SQLAlchemy Core engine and transaction helpers."""

from __future__ import annotations

import math
from collections.abc import Callable
from pathlib import Path
from typing import TypeVar

from sqlalchemy import event
from sqlalchemy.engine import Connection, Engine, URL, create_engine

from framenest.infrastructure.persistence.errors import FrameNestPersistenceError

DEFAULT_BUSY_TIMEOUT_SECONDS = 5.0
MAX_BUSY_TIMEOUT_SECONDS = 60.0

T = TypeVar("T")


def create_sqlite_engine(
    database_path: Path | str,
    *,
    busy_timeout_seconds: float = DEFAULT_BUSY_TIMEOUT_SECONDS,
) -> Engine:
    """Create a synchronous file-backed SQLite engine without opening it."""
    normalized_timeout = _validate_busy_timeout(busy_timeout_seconds)
    normalized_path = _validate_database_path(database_path)
    url = URL.create("sqlite+pysqlite", database=str(normalized_path))
    engine = create_engine(
        url,
        connect_args={"timeout": normalized_timeout},
        echo=False,
        hide_parameters=True,
    )
    busy_timeout_milliseconds = max(1, int(normalized_timeout * 1000))

    @event.listens_for(engine, "connect")
    def _configure_sqlite_connection(dbapi_connection: object, _: object) -> None:
        cursor = dbapi_connection.cursor()
        try:
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.execute(f"PRAGMA busy_timeout={busy_timeout_milliseconds}")
        finally:
            cursor.close()

    return engine


def run_in_transaction(
    engine: Engine,
    operation: Callable[[Connection], T],
) -> T:
    """Run an operation in an explicit transaction and close the connection."""
    with engine.connect() as connection:
        transaction = connection.begin()
        try:
            result = operation(connection)
        except BaseException:
            transaction.rollback()
            raise
        transaction.commit()
        return result


def run_in_immediate_transaction(
    engine: Engine,
    operation: Callable[[Connection], T],
) -> T:
    """Run one SQLite write decision after acquiring the writer lock first."""
    with engine.connect() as connection:
        connection.exec_driver_sql("BEGIN IMMEDIATE")
        try:
            result = operation(connection)
        except BaseException:
            connection.rollback()
            raise
        connection.commit()
        return result


def dispose_engine(engine: Engine) -> None:
    """Dispose an engine at an explicit cleanup boundary."""
    engine.dispose()


def _validate_database_path(database_path: Path | str) -> Path:
    try:
        path = Path(database_path).expanduser()
    except (RuntimeError, TypeError, ValueError) as exc:
        raise FrameNestPersistenceError(
            "Database path must be absolute.",
            error_code="INVALID_DATABASE_PATH",
            retryable=False,
            cause=exc,
        ) from exc
    if not path.is_absolute():
        raise FrameNestPersistenceError(
            "Database path must be absolute.",
            error_code="INVALID_DATABASE_PATH",
            retryable=False,
        )
    return path.resolve(strict=False)


def _validate_busy_timeout(value: float) -> float:
    if (
        not isinstance(value, int | float)
        or isinstance(value, bool)
        or not math.isfinite(value)
        or value <= 0
        or value > MAX_BUSY_TIMEOUT_SECONDS
    ):
        raise FrameNestPersistenceError(
            "Database busy timeout must be a positive bounded value.",
            error_code="INVALID_BUSY_TIMEOUT",
            retryable=False,
        )
    return float(value)
