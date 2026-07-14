"""Integration tests for upload-session migrations."""

from __future__ import annotations

import importlib.resources
import sqlite3
from pathlib import Path

import pytest

from framenest.configuration import FrameNestSettings
from framenest.infrastructure.persistence.catalog_schema import upload_sessions

PRODUCTION_VERSIONS_PACKAGE = (
    "framenest.infrastructure.persistence.alembic_environment.versions"
)
CURRENT_HEAD_REVISION = "0010"
TARGET_VALIDATION_REVISION = "0010"
TARGET_COMPLETENESS_REVISION = "0009"
TARGET_UPLOAD_SESSION_REVISION = "0008"
TARGET_PREVIOUS_REVISION = "0007"
COMPLETE_UPLOAD_SESSION_STATES = (
    "received",
    "validating",
    "duplicate_pending",
    "publish_pending",
    "published",
    "cataloged",
    "rejected",
)


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


def test_packaged_migration_resources_include_upload_session_revisions() -> None:
    versions = importlib.resources.files(PRODUCTION_VERSIONS_PACKAGE)
    assert versions.joinpath("0008_upload_sessions.py").is_file()
    assert versions.joinpath("0009_upload_session_completeness.py").is_file()
    assert versions.joinpath("0010_upload_validation_evidence.py").is_file()

    from framenest.infrastructure.persistence.migrations import load_script_directory

    script = load_script_directory()
    upload_revision = script.get_revision(TARGET_UPLOAD_SESSION_REVISION)
    assert upload_revision is not None
    assert upload_revision.down_revision == TARGET_PREVIOUS_REVISION
    completeness_revision = script.get_revision(TARGET_COMPLETENESS_REVISION)
    assert completeness_revision is not None
    assert completeness_revision.down_revision == TARGET_UPLOAD_SESSION_REVISION
    validation_revision = script.get_revision(TARGET_VALIDATION_REVISION)
    assert validation_revision is not None
    assert validation_revision.down_revision == TARGET_COMPLETENESS_REVISION
    assert script.get_heads() == [CURRENT_HEAD_REVISION]


def test_empty_database_upgrades_to_current_head_revision_0010(tmp_path: Path) -> None:
    from framenest.infrastructure.persistence.migrations import (
        inspect_database_migration_status,
        upgrade_database_to_head,
    )

    settings = _settings_for(tmp_path / "head-0010.sqlite3")
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
        "validated_media_kind",
        "validated_format",
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
        "ck_upload_sessions_created_received_size_zero",
        "ck_upload_sessions_complete_states_received_size_exact",
        "ck_upload_sessions_checksum_pair",
        "ck_upload_sessions_checksum_hex",
        "ck_upload_sessions_validation_evidence_pair",
        "ck_upload_sessions_validated_states_have_evidence",
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
            {"id": "22222222-2222-4222-8222-222222222222", "received_size_bytes": 1},
            {
                "id": "22222222-2222-4222-8222-222222222222",
                "state": "received",
                "received_size_bytes": 99,
            },
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
        invalid_validation_pair = valid | {
            "id": "33333333-3333-4333-8333-333333333333",
            "storage_key": "upload-session-invalid-validation",
            "state": "received",
            "validated_media_kind": "video",
            "validated_format": "gif",
        }
        with pytest.raises(sqlite3.IntegrityError):
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
                    validated_media_kind,
                    validated_format,
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
                    :validated_media_kind,
                    :validated_format,
                    :created_at_ms,
                    :updated_at_ms,
                    :expires_at_ms,
                    :failure_code,
                    :version
                )
                """,
                invalid_validation_pair,
            )
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


def test_upgrade_from_0008_to_0009_preserves_valid_upload_session_rows(
    tmp_path: Path,
) -> None:
    settings = _settings_for(tmp_path / "valid-completeness.sqlite3")
    _upgrade_to_revision(settings.database_path, TARGET_UPLOAD_SESSION_REVISION)
    rows = [
        _valid_upload_session_values(
            "11111111-1111-4111-8111-111111111111",
            "upload-session-0001",
            state="created",
            received_size_bytes=0,
        ),
        _valid_upload_session_values(
            "22222222-2222-4222-8222-222222222222",
            "upload-session-0002",
            state="receiving",
            received_size_bytes=25,
        ),
        _valid_upload_session_values(
            "33333333-3333-4333-8333-333333333333",
            "upload-session-0003",
            state="cancelled",
            received_size_bytes=25,
        ),
        _valid_upload_session_values(
            "44444444-4444-4444-8444-444444444444",
            "upload-session-0004",
            state="failed",
            received_size_bytes=100,
        ),
        _valid_upload_session_values(
            "55555555-5555-4555-8555-555555555555",
            "upload-session-0005",
            state="received",
            received_size_bytes=100,
        ),
        _valid_upload_session_values(
            "66666666-6666-4666-8666-666666666666",
            "upload-session-0006",
            state="published",
            received_size_bytes=100,
        ),
    ]
    connection = _connect(settings.database_path)
    try:
        for row in rows:
            _insert_upload_session(connection, row)
        connection.commit()
    finally:
        connection.close()

    _upgrade_to_revision(settings.database_path, TARGET_COMPLETENESS_REVISION)

    assert _upload_session_rows(settings.database_path) == rows


def test_upgrade_from_0008_to_0009_fails_closed_for_invalid_created_row(
    tmp_path: Path,
) -> None:
    settings = _settings_for(tmp_path / "invalid-created.sqlite3")
    _upgrade_to_revision(settings.database_path, TARGET_UPLOAD_SESSION_REVISION)
    invalid = _valid_upload_session_values(
        "11111111-1111-4111-8111-111111111111",
        "private-storage-key-0001",
        state="created",
        received_size_bytes=1,
        display_filename="Private Clip.mp4",
    )
    connection = _connect(settings.database_path)
    try:
        _insert_upload_session(connection, invalid)
        connection.commit()
    finally:
        connection.close()

    with pytest.raises(Exception) as error:
        _upgrade_to_revision(settings.database_path, TARGET_COMPLETENESS_REVISION)

    message = str(error.value)
    assert "private-storage-key-0001" not in message
    assert "Private Clip.mp4" not in message


@pytest.mark.parametrize("state", COMPLETE_UPLOAD_SESSION_STATES)
def test_upgrade_from_0008_to_0009_fails_closed_for_incomplete_complete_state(
    tmp_path: Path,
    state: str,
) -> None:
    settings = _settings_for(tmp_path / f"invalid-{state}.sqlite3")
    _upgrade_to_revision(settings.database_path, TARGET_UPLOAD_SESSION_REVISION)
    invalid = _valid_upload_session_values(
        "11111111-1111-4111-8111-111111111111",
        "private-storage-key-0001",
        state=state,
        received_size_bytes=99,
        display_filename="Private Clip.mp4",
    )
    connection = _connect(settings.database_path)
    try:
        _insert_upload_session(connection, invalid)
        connection.commit()
    finally:
        connection.close()

    with pytest.raises(Exception) as error:
        _upgrade_to_revision(settings.database_path, TARGET_COMPLETENESS_REVISION)

    message = str(error.value)
    assert "private-storage-key-0001" not in message
    assert "Private Clip.mp4" not in message


def test_upgrade_from_0009_to_0010_preserves_rows_that_do_not_require_validation_evidence(
    tmp_path: Path,
) -> None:
    settings = _settings_for(tmp_path / "valid-validation-evidence.sqlite3")
    _upgrade_to_revision(settings.database_path, TARGET_COMPLETENESS_REVISION)
    rows = [
        _valid_upload_session_values(
            "11111111-1111-4111-8111-111111111111",
            "upload-session-0001",
            state="created",
            received_size_bytes=0,
        ),
        _valid_upload_session_values(
            "22222222-2222-4222-8222-222222222222",
            "upload-session-0002",
            state="received",
            received_size_bytes=100,
        ),
        _valid_upload_session_values(
            "33333333-3333-4333-8333-333333333333",
            "upload-session-0003",
            state="validating",
            received_size_bytes=100,
        ),
        _valid_upload_session_values(
            "44444444-4444-4444-8444-444444444444",
            "upload-session-0004",
            state="rejected",
            received_size_bytes=100,
        ),
    ]
    connection = _connect(settings.database_path)
    try:
        for row in rows:
            _insert_upload_session(connection, row)
        connection.commit()
    finally:
        connection.close()

    _upgrade_to_revision(settings.database_path, TARGET_VALIDATION_REVISION)

    assert _upload_session_rows(settings.database_path) == rows
    columns = _columns(settings.database_path, "upload_sessions")
    assert "validated_media_kind" in columns
    assert "validated_format" in columns


@pytest.mark.parametrize(
    "state",
    ("duplicate_pending", "publish_pending", "published", "cataloged"),
)
def test_upgrade_from_0009_to_0010_fails_closed_for_advanced_rows_without_evidence(
    tmp_path: Path,
    state: str,
) -> None:
    settings = _settings_for(tmp_path / f"invalid-validation-{state}.sqlite3")
    _upgrade_to_revision(settings.database_path, TARGET_COMPLETENESS_REVISION)
    invalid = _valid_upload_session_values(
        "11111111-1111-4111-8111-111111111111",
        "private-storage-key-0001",
        state=state,
        received_size_bytes=100,
        display_filename="Private Clip.mp4",
    )
    connection = _connect(settings.database_path)
    try:
        _insert_upload_session(connection, invalid)
        connection.commit()
    finally:
        connection.close()

    with pytest.raises(Exception) as error:
        _upgrade_to_revision(settings.database_path, TARGET_VALIDATION_REVISION)

    message = str(error.value)
    assert "private-storage-key-0001" not in message
    assert "Private Clip.mp4" not in message


def test_downgrade_from_0009_to_0008_preserves_rows_and_upgrade_can_run_again(
    tmp_path: Path,
) -> None:
    settings = _settings_for(tmp_path / "downgrade-completeness.sqlite3")
    _upgrade_to_revision(settings.database_path, TARGET_COMPLETENESS_REVISION)
    rows = [
        _valid_upload_session_values(
            "11111111-1111-4111-8111-111111111111",
            "upload-session-0001",
            state="created",
            received_size_bytes=0,
        ),
        _valid_upload_session_values(
            "22222222-2222-4222-8222-222222222222",
            "upload-session-0002",
            state="received",
            received_size_bytes=100,
        ),
    ]
    connection = _connect(settings.database_path)
    try:
        for row in rows:
            _insert_upload_session(connection, row)
        connection.commit()
    finally:
        connection.close()

    _downgrade_to_revision(settings.database_path, TARGET_UPLOAD_SESSION_REVISION)
    assert _upload_session_rows(settings.database_path) == rows
    assert _table_sql(
        settings.database_path,
        "upload_sessions",
    ).find("ck_upload_sessions_complete_states_received_size_exact") == -1

    _upgrade_to_revision(settings.database_path, TARGET_COMPLETENESS_REVISION)

    assert _upload_session_rows(settings.database_path) == rows
    connection = _connect(settings.database_path)
    try:
        row = connection.execute("SELECT version_num FROM alembic_version").fetchone()
    finally:
        connection.close()
    assert row == (TARGET_COMPLETENESS_REVISION,)


def test_shared_metadata_and_migrated_schema_have_equivalent_upload_constraints_and_indexes(
    tmp_path: Path,
) -> None:
    from framenest.infrastructure.persistence.migrations import upgrade_database_to_head

    settings = _settings_for(tmp_path / "metadata-equivalence.sqlite3")
    upgrade_database_to_head(settings)

    metadata_constraint_names = {
        constraint.name
        for constraint in upload_sessions.constraints
        if constraint.name is not None
    }
    table_sql = _table_sql(settings.database_path, "upload_sessions")
    for name in metadata_constraint_names:
        assert name in table_sql

    metadata_index_names = {index.name for index in upload_sessions.indexes}
    assert metadata_index_names <= set(_indexes(settings.database_path, "upload_sessions"))


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


def _valid_upload_session_values(
    session_id: str,
    storage_key: str,
    *,
    state: str,
    received_size_bytes: int,
    display_filename: str = "example.mp4",
) -> dict[str, object]:
    return {
        "id": session_id,
        "state": state,
        "storage_key": storage_key,
        "display_filename": display_filename,
        "declared_size_bytes": 100,
        "received_size_bytes": received_size_bytes,
        "checksum_algorithm": None,
        "checksum_hex": None,
        "created_at_ms": 10,
        "updated_at_ms": 10,
        "expires_at_ms": 20,
        "failure_code": None,
        "version": 0,
    }


def _upload_session_rows(database_path: Path) -> list[dict[str, object]]:
    connection = _connect(database_path)
    try:
        rows = connection.execute(
            """
            SELECT
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
            FROM upload_sessions
            ORDER BY id
            """
        ).fetchall()
        columns = [
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
        ]
        return [dict(zip(columns, row, strict=True)) for row in rows]
    finally:
        connection.close()


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
