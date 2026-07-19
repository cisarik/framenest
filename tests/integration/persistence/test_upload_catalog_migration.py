"""Migration evidence for upload publication catalog linkage."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from framenest.configuration import FrameNestSettings


def _settings(database_path: Path) -> FrameNestSettings:
    return FrameNestSettings(database_path=database_path, _env_file=None)


def _migrate(database_path: Path, revision: str, *, downgrade: bool = False) -> None:
    from alembic import command
    from framenest.infrastructure.persistence.migrations import _alembic_config
    from framenest.infrastructure.persistence.engine import create_sqlite_engine, dispose_engine

    database_path.parent.mkdir(parents=True, exist_ok=True)
    engine = create_sqlite_engine(database_path)
    try:
        with engine.connect() as connection:
            with _alembic_config(
                "framenest.infrastructure.persistence.alembic_environment"
            ) as config:
                config.attributes["connection"] = connection
                if downgrade:
                    command.downgrade(config, revision)
                else:
                    command.upgrade(config, revision)
    finally:
        dispose_engine(engine)


def _connect(database_path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(database_path)
    connection.execute("PRAGMA foreign_keys=ON")
    return connection


def _seed_0013_publication(database_path: Path) -> None:
    connection = _connect(database_path)
    try:
        connection.execute(
            "INSERT INTO devices (id, display_name) VALUES (?, 'Synthetic device')",
            ("dddddddd-dddd-4ddd-8ddd-dddddddddddd",),
        )
        connection.execute(
            """
            INSERT INTO libraries (id, device_id, display_name, path_flavor, root_path)
            VALUES (?, ?, 'Synthetic published originals', 'posix', '/synthetic/published')
            """,
            (
                "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb",
                "dddddddd-dddd-4ddd-8ddd-dddddddddddd",
            ),
        )
        connection.execute(
            """
            INSERT INTO media_byte_identities (
                id, checksum_algorithm, size_bytes, checksum_hex, created_at_ms
            ) VALUES (?, 'sha256', 8, ?, 10)
            """,
            ("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa", "a" * 64),
        )
        connection.execute(
            """
            INSERT INTO upload_sessions (
                id, state, storage_key, display_filename,
                declared_size_bytes, received_size_bytes,
                checksum_algorithm, checksum_hex,
                validated_media_kind, validated_format, byte_identity_id,
                duplicate_disposition,
                created_at_ms, updated_at_ms, expires_at_ms,
                failure_code, version
            ) VALUES (?, 'published', 'synthetic-upload-0001', 'synthetic.mp4',
                      8, 8, 'sha256', ?, 'video', 'mp4', ?, NULL,
                      10, 30, 100, NULL, 5)
            """,
            (
                "11111111-1111-4111-8111-111111111111",
                "a" * 64,
                "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
            ),
        )
        publication_id = "cccccccc-cccc-4ccc-8ccc-cccccccccccc"
        connection.execute(
            """
            INSERT INTO upload_publications (
                upload_id, publication_id, destination_id, relative_target,
                byte_identity_id, expected_size_bytes, checksum_algorithm, checksum_hex,
                validated_media_kind, validated_format, state, cleanup_state,
                created_at_ms, updated_at_ms, verified_at_ms,
                cleanup_completed_at_ms, version
            ) VALUES (?, ?, ?, ?, ?, 8, 'sha256', ?, 'video', 'mp4',
                      'verified', 'complete', 20, 31, 30, 31, 2)
            """,
            (
                "11111111-1111-4111-8111-111111111111",
                publication_id,
                "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb",
                f"{publication_id.replace('-', '')}.mp4",
                "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
                "a" * 64,
            ),
        )
        connection.commit()
    finally:
        connection.close()


def test_upgrade_from_0013_preserves_publications_with_null_catalog_links(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "catalog.sqlite3"
    _migrate(database_path, "0013")
    _seed_0013_publication(database_path)

    _migrate(database_path, "0014")

    connection = _connect(database_path)
    try:
        row = connection.execute(
            """
            SELECT upload_id, state, cleanup_state, media_id, media_location_id, version
            FROM upload_publications
            """
        ).fetchone()
        assert row == (
            "11111111-1111-4111-8111-111111111111",
            "verified",
            "complete",
            None,
            None,
            2,
        )
        assert connection.execute("SELECT COUNT(*) FROM logical_media").fetchone() == (0,)
    finally:
        connection.close()


def test_0014_linkage_constraints_and_restrictive_references(tmp_path: Path) -> None:
    database_path = tmp_path / "constraints" / "catalog.sqlite3"
    _migrate(database_path, "0014")
    _seed_0013_publication(database_path)
    connection = _connect(database_path)
    try:
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """
                UPDATE upload_publications
                SET media_id = ?
                WHERE upload_id = ?
                """,
                (
                    "eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee",
                    "11111111-1111-4111-8111-111111111111",
                ),
            )
        connection.rollback()
        connection.execute(
            """
            INSERT INTO logical_media (id, media_kind, created_at_ms, updated_at_ms)
            VALUES (?, 'video', 40, 40)
            """,
            ("eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee",),
        )
        connection.execute(
            """
            INSERT INTO physical_media_locations (
                id, media_id, library_id, relative_path, availability,
                observed_size_bytes, observed_mtime_ns, created_at_ms, updated_at_ms
            ) VALUES (?, ?, ?, 'cccccccccccc4ccc8cccccccccccccccc.mp4', 'available',
                      8, NULL, 40, 40)
            """,
            (
                "ffffffff-ffff-4fff-8fff-ffffffffffff",
                "eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee",
                "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb",
            ),
        )
        connection.execute(
            """
            UPDATE upload_publications
            SET media_id = ?, media_location_id = ?
            WHERE upload_id = ?
            """,
            (
                "eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee",
                "ffffffff-ffff-4fff-8fff-ffffffffffff",
                "11111111-1111-4111-8111-111111111111",
            ),
        )
        connection.commit()
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                "DELETE FROM logical_media WHERE id = ?",
                ("eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee",),
            )
        connection.rollback()
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                "DELETE FROM physical_media_locations WHERE id = ?",
                ("ffffffff-ffff-4fff-8fff-ffffffffffff",),
            )
        connection.rollback()
    finally:
        connection.close()


def test_0014_downgrade_removes_linkage_and_preserves_publication_rows(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "roundtrip" / "catalog.sqlite3"
    _migrate(database_path, "0013")
    _seed_0013_publication(database_path)
    _migrate(database_path, "0014")
    _migrate(database_path, "0013", downgrade=True)

    connection = _connect(database_path)
    try:
        columns = {
            row[1]
            for row in connection.execute("PRAGMA table_info(upload_publications)")
        }
        assert "media_id" not in columns
        assert "media_location_id" not in columns
        assert connection.execute(
            "SELECT upload_id, state, cleanup_state FROM upload_publications"
        ).fetchone() == (
            "11111111-1111-4111-8111-111111111111",
            "verified",
            "complete",
        )
    finally:
        connection.close()
