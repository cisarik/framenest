"""Integration tests for upload-session migration revision 0008."""

from __future__ import annotations

import importlib.resources
import sqlite3
from pathlib import Path

from framenest.configuration import FrameNestSettings

PRODUCTION_VERSIONS_PACKAGE = (
    "framenest.infrastructure.persistence.alembic_environment.versions"
)
CURRENT_HEAD_REVISION = "0008"
TARGET_UPLOAD_SESSION_REVISION = "0008"
TARGET_PREVIOUS_REVISION = "0007"


def _settings_for(database_path: Path) -> FrameNestSettings:
    return FrameNestSettings(database_path=database_path, _env_file=None)


def _upgrade_to_revision(database_path: Path, revision: str) -> None:
    from alembic import command
    from framenest.infrastructure.persistence.engine import create_sqlite_engine, dispose_engine
    from framenest.infrastructure.persistence.migrations import _alembic_config

    settings = _settings_for(database_path)
    settings.database_path.parent.mkdir(parents=True, exist_ok=True)
    engine = create_sqlite_engine(settings.database_path)
    try:
        with engine.connect() as connection:
            with _alembic_config(
                "framenest.infrastructure.persistence.alembic_environment"
            ) as config:
                config.attributes["connection"] = connection
                command.upgrade(config, revision)
    finally:
        dispose_engine(engine)


def _downgrade_to_revision(database_path: Path, revision: str) -> None:
    from alembic import command
    from framenest.infrastructure.persistence.engine import create_sqlite_engine, dispose_engine
    from framenest.infrastructure.persistence.migrations import _alembic_config

    engine = create_sqlite_engine(database_path)
    try:
        with engine.connect() as connection:
            with _alembic_config(
                "framenest.infrastructure.persistence.alembic_environment"
            ) as config:
                config.attributes["connection"] = connection
                command.downgrade(config, revision)
    finally:
        dispose_engine(engine)


def _connect(database_path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(database_path)
    connection.execute("PRAGMA foreign_keys=ON")
    return connection


def _table_names(database_path: Path) -> set[str]:
    connection = _connect(database_path)
    try:
        rows = connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name"
        ).fetchall()
        return {str(row[0]) for row in rows}
    finally:
        connection.close()


def _columns(database_path: Path, table_name: str) -> dict[str, tuple[object, ...]]:
    connection = _connect(database_path)
    try:
        rows = connection.execute(f"PRAGMA table_info({table_name})").fetchall()
        return {str(row[1]): row for row in rows}
    finally:
        connection.close()


def _indexes(database_path: Path, table_name: str) -> dict[str, tuple[object, ...]]:
    connection = _connect(database_path)
    try:
        rows = connection.execute(f"PRAGMA index_list({table_name})").fetchall()
        return {str(row[1]): row for row in rows}
    finally:
        connection.close()


def _table_sql(database_path: Path, table_name: str) -> str:
    connection = _connect(database_path)
    try:
        row = connection.execute(
            "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = ?",
            (table_name,),
        ).fetchone()
        assert row is not None
        return str(row[0])
    finally:
        connection.close()


def test_packaged_migration_resources_include_0008() -> None:
    versions = importlib.resources.files(PRODUCTION_VERSIONS_PACKAGE)
    assert versions.joinpath("0008_upload_sessions.py").is_file()

    from framenest.infrastructure.persistence.migrations import load_script_directory

    revision = load_script_directory().get_revision(TARGET_UPLOAD_SESSION_REVISION)
    assert revision is not None
    assert revision.down_revision == TARGET_PREVIOUS_REVISION


def test_empty_database_upgrades_to_current_head_revision_0008(tmp_path: Path) -> None:
    from framenest.infrastructure.persistence.migrations import (
        inspect_database_migration_status,
        upgrade_database_to_head,
    )

    settings = _settings_for(tmp_path / "head-0008.sqlite3")
    status = upgrade_database_to_head(settings)

    assert status.state == "at_head"
    assert status.current_revision == CURRENT_HEAD_REVISION
    assert status.head_revision == CURRENT_HEAD_REVISION
    assert inspect_database_migration_status(settings) == status
    assert "upload_sessions" in _table_names(settings.database_path)


def test_upload_sessions_table_has_required_columns_constraints_and_indexes(
    tmp_path: Path,
) -> None:
    from framenest.infrastructure.persistence.migrations import upgrade_database_to_head

    settings = _settings_for(tmp_path / "schema.sqlite3")
    upgrade_database_to_head(settings)

    assert set(_columns(settings.database_path, "upload_sessions")) == {
        "id",
        "state",
        "storage_key",
        "display_filename",
        "declared_size_bytes",
        "received_size_bytes",
        "checksum_algorithm",
        "checksum_hex",
        "created_at_ms",
        "updated_at_ms",
        "expires_at_ms",
        "failure_code",
        "version",
    }
    table_sql = _table_sql(settings.database_path, "upload_sessions")
    for name in (
        "ck_upload_sessions_state",
        "ck_upload_sessions_declared_size_positive",
        "ck_upload_sessions_received_size_non_negative",
        "ck_upload_sessions_received_size_not_over_declared",
        "ck_upload_sessions_checksum_pair",
        "ck_upload_sessions_checksum_hex",
        "ck_upload_sessions_expires_after_created",
        "ck_upload_sessions_failure_code_sanitized",
        "ck_upload_sessions_version_non_negative",
        "uq_upload_sessions_storage_key",
    ):
        assert name in table_sql
    indexes = _indexes(settings.database_path, "upload_sessions")
    assert "ix_upload_sessions_state" in indexes
    assert "ix_upload_sessions_expires_at_ms" in indexes
    assert "ix_upload_sessions_state_expires_at_ms" in indexes


def test_upload_session_constraints_reject_invalid_rows(tmp_path: Path) -> None:
    from framenest.infrastructure.persistence.migrations import upgrade_database_to_head

    settings = _settings_for(tmp_path / "constraints.sqlite3")
    upgrade_database_to_head(settings)
    connection = _connect(settings.database_path)
    try:
        valid = {
            "id": "11111111-1111-4111-8111-111111111111",
            "state": "created",
            "storage_key": "upload-session-0001",
            "display_filename": "example.mp4",
            "declared_size_bytes": 100,
            "received_size_bytes": 0,
            "checksum_algorithm": None,
            "checksum_hex": None,
            "created_at_ms": 10,
            "updated_at_ms": 10,
            "expires_at_ms": 20,
            "failure_code": None,
            "version": 0,
        }
        _insert_upload_session(connection, valid)
        for overrides in (
            {"id": "22222222-2222-4222-8222-222222222222", "state": "unknown"},
            {"id": "22222222-2222-4222-8222-222222222222", "declared_size_bytes": 0},
            {"id": "22222222-2222-4222-8222-222222222222", "received_size_bytes": -1},
            {"id": "22222222-2222-4222-8222-222222222222", "received_size_bytes": 101},
            {
                "id": "22222222-2222-4222-8222-222222222222",
                "checksum_algorithm": "sha256",
                "checksum_hex": "A" * 64,
            },
            {
                "id": "22222222-2222-4222-8222-222222222222",
                "checksum_algorithm": "md5",
                "checksum_hex": "a" * 64,
            },
            {"id": "22222222-2222-4222-8222-222222222222", "expires_at_ms": 10},
            {"id": "22222222-2222-4222-8222-222222222222", "version": -1},
            {"id": "22222222-2222-4222-8222-222222222222", "storage_key": "/tmp/file"},
            {
                "id": "22222222-2222-4222-8222-222222222222",
                "display_filename": "nested/file.mp4",
            },
        ):
            row = valid | overrides | {"storage_key": f"upload-session-{len(str(overrides)):04d}"}
            if "storage_key" in overrides:
                row["storage_key"] = overrides["storage_key"]
            try:
                _insert_upload_session(connection, row)
            except sqlite3.IntegrityError:
                pass
            else:
                raise AssertionError(f"invalid row accepted: {overrides}")
    finally:
        connection.close()


def test_upgrade_from_0007_preserves_existing_catalog_rows_and_adds_empty_upload_sessions(
    tmp_path: Path,
) -> None:
    from framenest.infrastructure.persistence.migrations import upgrade_database_to_head

    settings = _settings_for(tmp_path / "preserve.sqlite3")
    _upgrade_to_revision(settings.database_path, TARGET_PREVIOUS_REVISION)
    before_tables = _table_names(settings.database_path)

    status = upgrade_database_to_head(settings)

    assert status.current_revision == CURRENT_HEAD_REVISION
    assert before_tables | {"upload_sessions"} == _table_names(settings.database_path)
    connection = _connect(settings.database_path)
    try:
        assert connection.execute("SELECT COUNT(*) FROM upload_sessions").fetchone()[0] == 0
    finally:
        connection.close()


def test_downgrade_from_0008_to_0007_removes_only_upload_sessions(tmp_path: Path) -> None:
    settings = _settings_for(tmp_path / "downgrade.sqlite3")
    _upgrade_to_revision(settings.database_path, TARGET_UPLOAD_SESSION_REVISION)
    assert "upload_sessions" in _table_names(settings.database_path)

    _downgrade_to_revision(settings.database_path, TARGET_PREVIOUS_REVISION)

    assert "upload_sessions" not in _table_names(settings.database_path)
    connection = _connect(settings.database_path)
    try:
        row = connection.execute("SELECT version_num FROM alembic_version").fetchone()
    finally:
        connection.close()
    assert row == (TARGET_PREVIOUS_REVISION,)


def _insert_upload_session(connection: sqlite3.Connection, values: dict[str, object]) -> None:
    connection.execute(
        """
        INSERT INTO upload_sessions (
            id,
            state,
            storage_key,
            display_filename,
            declared_size_bytes,
            received_size_bytes,
            checksum_algorithm,
            checksum_hex,
            created_at_ms,
            updated_at_ms,
            expires_at_ms,
            failure_code,
            version
        ) VALUES (
            :id,
            :state,
            :storage_key,
            :display_filename,
            :declared_size_bytes,
            :received_size_bytes,
            :checksum_algorithm,
            :checksum_hex,
            :created_at_ms,
            :updated_at_ms,
            :expires_at_ms,
            :failure_code,
            :version
        )
        """,
        values,
    )
