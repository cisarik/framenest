"""Repository evidence for readiness, filtering, and atomic publication."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import sqlalchemy as sa
from sqlalchemy import event, text

from framenest.application.ports.content_publication_repository import (
    AdminMediaQuery,
)
from framenest.configuration import FrameNestSettings
from framenest.domain.identities import MediaId

MEDIA_READY = "11111111-1111-4111-8111-111111111111"
MEDIA_INCOMPLETE = "22222222-2222-4222-8222-222222222222"


def _repository(tmp_path: Path):
    from framenest.infrastructure.persistence.content_publication_repository import (
        SqliteContentPublicationRepository,
    )
    from framenest.infrastructure.persistence.engine import create_sqlite_engine
    from framenest.infrastructure.persistence.migrations import upgrade_database_to_head

    database_path = tmp_path / "publication.sqlite3"
    upgrade_database_to_head(
        FrameNestSettings(database_path=database_path, _env_file=None)
    )
    engine = create_sqlite_engine(database_path)
    return SqliteContentPublicationRepository(engine), engine


def _seed(engine: sa.Engine) -> None:
    with engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO logical_media "
                "(id, media_kind, created_at_ms, updated_at_ms) VALUES "
                "(:ready, 'video', 20, 20), "
                "(:incomplete, 'image', 20, 20)"
            ),
            {"ready": MEDIA_READY, "incomplete": MEDIA_INCOMPLETE},
        )
        connection.execute(
            text(
                "INSERT INTO canonical_tags "
                "(key, display_name, created_at_ms, updated_at_ms) "
                "VALUES ('manual', 'Manual', 1, 1)"
            )
        )
        connection.execute(
            text(
                "INSERT INTO media_metadata "
                "(media_id, display_title, description, collection_key, "
                "processed_at_ms, created_at_ms, updated_at_ms) VALUES "
                "(:ready, 'Manual title', 'Manual description', NULL, NULL, 2, 2), "
                "(:incomplete, NULL, ' ', 'processed', 3, 2, 3)"
            ),
            {"ready": MEDIA_READY, "incomplete": MEDIA_INCOMPLETE},
        )
        connection.execute(
            text(
                "INSERT INTO media_canonical_tags "
                "(media_id, tag_key, position) VALUES "
                "(:ready, 'manual', 0), "
                "(:incomplete, 'manual', 0)"
            ),
            {"ready": MEDIA_READY, "incomplete": MEDIA_INCOMPLETE},
        )


def _query(**overrides: object) -> AdminMediaQuery:
    values: dict[str, object] = {
        "q": None,
        "tag_keys": (),
        "publication": "unpublished",
        "readiness": "all",
        "analysis": "all",
        "limit": 24,
        "offset": 0,
    }
    values.update(overrides)
    return AdminMediaQuery(**values)  # type: ignore[arg-type]


def test_admin_list_orders_filters_and_keeps_processed_readiness_independent(
    tmp_path: Path,
) -> None:
    repository, engine = _repository(tmp_path)
    _seed(engine)
    try:
        page = repository.list_admin_media(_query())
        ready = repository.list_admin_media(_query(readiness="ready"))
        incomplete = repository.list_admin_media(_query(readiness="incomplete"))
        tagged = repository.list_admin_media(_query(tag_keys=("manual",)))
    finally:
        engine.dispose()

    assert [item.media_id for item in page.items] == [
        MEDIA_READY,
        MEDIA_INCOMPLETE,
    ]
    assert [item.media_id for item in ready.items] == [MEDIA_READY]
    assert [item.media_id for item in incomplete.items] == [MEDIA_INCOMPLETE]
    assert tagged.total == 2
    incomplete_item = incomplete.items[0]
    assert incomplete_item.collection_key == "processed"
    assert incomplete_item.analysis_state == "not_requested"
    assert incomplete_item.readiness.missing_fields == (
        "display_title",
        "description",
    )


def test_admin_page_loads_latest_analysis_in_one_bounded_batched_query(
    tmp_path: Path,
) -> None:
    repository, engine = _repository(tmp_path)
    _seed(engine)
    statements: list[str] = []

    def capture_statement(
        _connection,
        _cursor,
        statement,
        _parameters,
        _context,
        _executemany,
    ) -> None:
        if "media_analysis_runs" in statement:
            statements.append(statement)

    event.listen(engine, "before_cursor_execute", capture_statement)
    try:
        repository.list_admin_media(_query())
    finally:
        event.remove(engine, "before_cursor_execute", capture_statement)
        engine.dispose()

    assert len(statements) == 1
    assert "row_number()" in statements[0].lower()


def test_publication_is_conditional_repeated_and_survives_metadata_regression(
    tmp_path: Path,
) -> None:
    repository, engine = _repository(tmp_path)
    _seed(engine)
    try:
        incomplete = repository.publish(
            MediaId.from_string(MEDIA_INCOMPLETE),
            100,
        )
        first = repository.publish(MediaId.from_string(MEDIA_READY), 101)
        repeated = repository.publish(MediaId.from_string(MEDIA_READY), 999)
        with engine.begin() as connection:
            connection.execute(
                text(
                    "UPDATE media_metadata SET description = NULL "
                    "WHERE media_id = :media_id"
                ),
                {"media_id": MEDIA_READY},
            )
        after_regression = repository.publish(
            MediaId.from_string(MEDIA_READY),
            1000,
        )
        remains_published = repository.is_published(
            MediaId.from_string(MEDIA_READY)
        )
    finally:
        engine.dispose()

    assert incomplete.status == "not_ready"
    assert incomplete.readiness.missing_fields == ("display_title", "description")
    assert first.status == "published"
    assert first.publication is not None
    assert first.publication.published_at_ms == 101
    assert repeated.status == "already_published"
    assert repeated.publication == first.publication
    assert after_regression.status == "already_published"
    assert after_regression.readiness.ready is False
    assert remains_published is True


def test_concurrent_publication_has_one_creator_and_safe_winner_observation(
    tmp_path: Path,
) -> None:
    repository, engine = _repository(tmp_path)
    _seed(engine)
    media_id = MediaId.from_string(MEDIA_READY)
    try:
        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(
                executor.map(
                    lambda timestamp: repository.publish(media_id, timestamp),
                    (200, 201),
                )
            )
    finally:
        engine.dispose()

    assert sorted(result.status for result in results) == [
        "already_published",
        "published",
    ]
    assert len(
        {
            result.publication.published_at_ms
            for result in results
            if result.publication is not None
        }
    ) == 1
