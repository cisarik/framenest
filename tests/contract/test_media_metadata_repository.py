"""Contract tests for the SQLite media metadata repository adapter."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
import sqlalchemy as sa
from sqlalchemy import text

from framenest.application.ports.media_metadata_repository import (
    CanonicalTagDefinitionConflictError,
    CanonicalTagNotFoundError,
    FrameNestMediaMetadataRepositoryError,
    MediaMetadataMediaNotFoundError,
)
from framenest.domain.media import LogicalMedia, MediaKind
from framenest.domain.media_metadata import (
    CanonicalTagDisplayName,
    CanonicalTagKey,
    MediaDisplayTitle,
)
from framenest.domain.identities import MediaId

CANONICAL_MEDIA_ID = "12345678-1234-4234-9234-123456789abc"
SECOND_MEDIA_ID = "abcdefab-cdef-4abc-8def-abcdefabcdef"


def _migrated_engine(tmp_path: Path) -> sa.Engine:
    from framenest.configuration import FrameNestSettings
    from framenest.infrastructure.persistence.engine import create_sqlite_engine
    from framenest.infrastructure.persistence.migrations import upgrade_database_to_head

    database_path = tmp_path / "media-metadata-repository.sqlite3"
    upgrade_database_to_head(FrameNestSettings(database_path=database_path, _env_file=None))
    return create_sqlite_engine(database_path)


def _repository(tmp_path: Path):
    from framenest.infrastructure.persistence.media_metadata_repository import (
        SqliteMediaMetadataRepository,
    )

    engine = _migrated_engine(tmp_path)
    return SqliteMediaMetadataRepository(engine), engine


def _insert_media(engine: sa.Engine, media_id: str = CANONICAL_MEDIA_ID) -> MediaId:
    parsed = MediaId.from_string(media_id)
    with engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO logical_media (id, media_kind, created_at_ms, updated_at_ms) "
                "VALUES (:id, 'video', 1, 1)"
            ),
            {"id": parsed.to_string()},
        )
    return parsed


def test_create_canonical_tag_and_idempotent_repeat(tmp_path: Path) -> None:
    repository, engine = _repository(tmp_path)
    try:
        created = repository.create_canonical_tag(
            CanonicalTagKey("mathematics"),
            CanonicalTagDisplayName("Math"),
            now_ms=10,
        )
        repeated = repository.create_canonical_tag(
            CanonicalTagKey("mathematics"),
            CanonicalTagDisplayName("Math"),
            now_ms=99,
        )

        assert created.status == "created"
        assert repeated.status == "already_exists"
        assert repeated.tag == created.tag
    finally:
        engine.dispose()


def test_same_key_different_display_name_conflicts(tmp_path: Path) -> None:
    repository, engine = _repository(tmp_path)
    try:
        repository.create_canonical_tag(
            CanonicalTagKey("mathematics"),
            CanonicalTagDisplayName("Math"),
            now_ms=10,
        )
        with pytest.raises(CanonicalTagDefinitionConflictError):
            repository.create_canonical_tag(
                CanonicalTagKey("mathematics"),
                CanonicalTagDisplayName("Mathematics"),
                now_ms=11,
            )
    finally:
        engine.dispose()


def test_tag_listing_is_deterministic(tmp_path: Path) -> None:
    repository, engine = _repository(tmp_path)
    try:
        repository.create_canonical_tag(CanonicalTagKey("meme"), CanonicalTagDisplayName("Meme"), 1)
        repository.create_canonical_tag(CanonicalTagKey("compression"), CanonicalTagDisplayName("Compression"), 1)
        repository.create_canonical_tag(CanonicalTagKey("math"), CanonicalTagDisplayName("Compression"), 1)

        assert [(tag.display_name.value, tag.key.value) for tag in repository.list_canonical_tags()] == [
            ("Compression", "compression"),
            ("Compression", "math"),
            ("Meme", "meme"),
        ]
    finally:
        engine.dispose()


def test_missing_and_unsaved_media_are_distinguished(tmp_path: Path) -> None:
    repository, engine = _repository(tmp_path)
    media_id = _insert_media(engine)
    try:
        unsaved = repository.get_media_metadata(media_id)
        assert unsaved.persisted is False
        assert unsaved.display_title is None
        assert unsaved.tag_keys == ()
        assert unsaved.created_at_ms is None
        with pytest.raises(MediaMetadataMediaNotFoundError):
            repository.get_media_metadata(MediaId.new())
    finally:
        engine.dispose()


def test_metadata_save_create_update_clear_empty_and_unchanged(tmp_path: Path) -> None:
    repository, engine = _repository(tmp_path)
    media_id = _insert_media(engine)
    try:
        repository.create_canonical_tag(CanonicalTagKey("mathematics"), CanonicalTagDisplayName("Math"), 1)
        repository.create_canonical_tag(CanonicalTagKey("compression"), CanonicalTagDisplayName("Compression"), 1)

        created = repository.save_media_metadata(
            media_id,
            MediaDisplayTitle("Reinventing Entropy"),
            (CanonicalTagKey("mathematics"), CanonicalTagKey("compression")),
            now_ms=20,
        )
        updated = repository.save_media_metadata(
            media_id,
            MediaDisplayTitle("Entropy"),
            (CanonicalTagKey("compression"), CanonicalTagKey("mathematics")),
            now_ms=30,
        )
        unchanged = repository.save_media_metadata(
            media_id,
            MediaDisplayTitle("Entropy"),
            (CanonicalTagKey("compression"), CanonicalTagKey("mathematics")),
            now_ms=40,
        )
        cleared = repository.save_media_metadata(media_id, None, (), now_ms=50)

        assert created.status == "created"
        assert updated.status == "updated"
        assert updated.metadata.tag_keys == (
            CanonicalTagKey("compression"),
            CanonicalTagKey("mathematics"),
        )
        assert unchanged.status == "unchanged"
        assert unchanged.metadata.updated_at_ms == updated.metadata.updated_at_ms
        assert cleared.status == "updated"
        assert cleared.metadata.display_title is None
        assert cleared.metadata.tag_keys == ()
    finally:
        engine.dispose()


def test_missing_tag_duplicate_keys_and_too_many_tags_fail_safely(tmp_path: Path) -> None:
    repository, engine = _repository(tmp_path)
    media_id = _insert_media(engine)
    try:
        repository.create_canonical_tag(CanonicalTagKey("mathematics"), CanonicalTagDisplayName("Math"), 1)
        with pytest.raises(CanonicalTagNotFoundError):
            repository.save_media_metadata(media_id, None, (CanonicalTagKey("missing"),), now_ms=2)
        with pytest.raises(ValueError):
            repository.save_media_metadata(
                media_id,
                None,
                (CanonicalTagKey("mathematics"), CanonicalTagKey("mathematics")),
                now_ms=2,
            )
        with pytest.raises(ValueError):
            repository.save_media_metadata(
                media_id,
                None,
                tuple(CanonicalTagKey(f"tag-{index}") for index in range(33)),
                now_ms=2,
            )
    finally:
        engine.dispose()


def test_assignment_replacement_failure_rolls_back_previous_state(tmp_path: Path) -> None:
    repository, engine = _repository(tmp_path)
    media_id = _insert_media(engine)
    try:
        repository.create_canonical_tag(CanonicalTagKey("mathematics"), CanonicalTagDisplayName("Math"), 1)
        repository.create_canonical_tag(CanonicalTagKey("compression"), CanonicalTagDisplayName("Compression"), 1)
        repository.save_media_metadata(
            media_id,
            MediaDisplayTitle("Original"),
            (CanonicalTagKey("mathematics"),),
            now_ms=10,
        )
        with patch(
            "framenest.infrastructure.persistence.media_metadata_repository._insert_assignments",
            side_effect=FrameNestMediaMetadataRepositoryError("Media metadata operation failed."),
        ):
            with pytest.raises(FrameNestMediaMetadataRepositoryError):
                repository.save_media_metadata(
                    media_id,
                    MediaDisplayTitle("Changed"),
                    (CanonicalTagKey("compression"),),
                    now_ms=20,
                )

        preserved = repository.get_media_metadata(media_id)
        assert preserved.display_title == MediaDisplayTitle("Original")
        assert preserved.tag_keys == (CanonicalTagKey("mathematics"),)
        assert preserved.updated_at_ms == 10
    finally:
        engine.dispose()


def test_malformed_persisted_rows_raise_sanitized_error(tmp_path: Path) -> None:
    repository, engine = _repository(tmp_path)
    media_id = _insert_media(engine)
    try:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO media_metadata (media_id, display_title, created_at_ms, updated_at_ms) "
                    "VALUES (:media_id, :display_title, 1, 1)"
                ),
                {"media_id": media_id.to_string(), "display_title": "Bad\nTitle"},
            )
        with pytest.raises(FrameNestMediaMetadataRepositoryError) as exc_info:
            repository.get_media_metadata(media_id)
        rendered = str(exc_info.value)
        assert rendered == "Media metadata operation failed."
        assert "Bad" not in rendered
        assert "SELECT" not in rendered
        assert "sqlite" not in rendered.lower()
    finally:
        engine.dispose()


def test_importing_media_does_not_create_metadata_rows(tmp_path: Path) -> None:
    from framenest.infrastructure.persistence.media_repository import SqliteMediaRepository

    repository, engine = _repository(tmp_path)
    media_repository = SqliteMediaRepository(engine)
    try:
        media = LogicalMedia(
            id=MediaId.from_string(CANONICAL_MEDIA_ID),
            kind=MediaKind.VIDEO,
            created_at_ms=1,
            updated_at_ms=1,
        )
        media_repository.add_media(media)
        assert repository.get_media_metadata(media.id).persisted is False
        with engine.connect() as connection:
            assert connection.execute(text("SELECT COUNT(*) FROM media_metadata")).scalar_one() == 0
            assert connection.execute(text("SELECT COUNT(*) FROM canonical_tags")).scalar_one() == 0
    finally:
        engine.dispose()
