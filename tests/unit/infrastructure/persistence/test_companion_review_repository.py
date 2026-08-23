"""Repository evidence for companion review inbox and history reads."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from sqlalchemy import text

from framenest.application.companion_review import MappedTagStatus
from framenest.application.ports.companion_review_repository import (
    CompanionReviewMovieExcludedError,
    CompanionReviewRunNotEligibleError,
    CompanionReviewStaleMappingError,
    CompanionReviewStoredResultError,
    FrameNestCompanionReviewRepositoryError,
)
from framenest.configuration import FrameNestSettings
from framenest.domain.content_publication import ContentPublicationOrigin
from framenest.domain.identities import MediaId
from framenest.infrastructure.persistence.companion_review_repository import (
    SqliteCompanionReviewRepository,
)
from framenest.infrastructure.persistence.engine import create_sqlite_engine, dispose_engine
from framenest.infrastructure.persistence.migrations import upgrade_database_to_head

DEVICE_ID = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
LIBRARY_ID = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"
ADMIN_KEY = "admin@example.com"
OTHER_KEY = "other@example.com"

GENERIC = "aaaaaaaa-aaaa-4aaa-8aaa-000000000001"
GENERIC_LOC = "aaaaaaaa-aaaa-4aaa-8aaa-000000000011"
GENERIC_RUN = "aaaaaaaa-aaaa-4aaa-8aaa-000000000021"
GENERIC_FAIL = "aaaaaaaa-aaaa-4aaa-8aaa-000000000031"
GENERIC_NEWER = "aaaaaaaa-aaaa-4aaa-8aaa-000000000041"

MOVIE = "bbbbbbbb-bbbb-4bbb-8bbb-000000000002"
MOVIE_LOC = "bbbbbbbb-bbbb-4bbb-8bbb-000000000012"
MOVIE_RUN = "bbbbbbbb-bbbb-4bbb-8bbb-000000000022"

MOVIE_ID_MEDIA = "cccccccc-cccc-4ccc-8ccc-000000000003"
MOVIE_ID_LOC = "cccccccc-cccc-4ccc-8ccc-000000000013"
MOVIE_ID_RUN = "cccccccc-cccc-4ccc-8ccc-000000000023"

WEBSITE = "dddddddd-dddd-4ddd-8ddd-000000000004"
WEBSITE_LOC = "dddddddd-dddd-4ddd-8ddd-000000000014"
WEBSITE_RUN = "dddddddd-dddd-4ddd-8ddd-000000000024"

HISTORICAL = "eeeeeeee-eeee-4eee-8eee-000000000005"
HISTORICAL_LOC = "eeeeeeee-eeee-4eee-8eee-000000000015"
HISTORICAL_RUN = "eeeeeeee-eeee-4eee-8eee-000000000025"

NULL_PROFILE = "ffffffff-ffff-4fff-8fff-000000000006"
NULL_PROFILE_LOC = "ffffffff-ffff-4fff-8fff-000000000016"
NULL_PROFILE_RUN = "ffffffff-ffff-4fff-8fff-000000000026"


def _result_json(*, title: str, tags: list[str]) -> str:
    return json.dumps(
        {
            "collection": "memes",
            "confidence": 0.9,
            "description": "A description.",
            "evidence": ["visible subject"],
            "suggested_filename": "clip.gif",
            "tags": tags,
            "title": title,
            "uncertainties": [],
        },
        separators=(",", ":"),
        sort_keys=True,
    )


def _repository(tmp_path: Path) -> tuple[SqliteCompanionReviewRepository, object]:
    settings = FrameNestSettings(
        database_path=tmp_path / "catalog.sqlite3", _env_file=None
    )
    upgrade_database_to_head(settings)
    engine = create_sqlite_engine(settings.database_path)
    _seed_catalog(engine)
    return SqliteCompanionReviewRepository(engine), engine


def _seed_catalog(engine) -> None:
    with engine.begin() as connection:
        connection.execute(
            text("INSERT INTO devices (id, display_name) VALUES (:id, 'Dev')"),
            {"id": DEVICE_ID},
        )
        connection.execute(
            text(
                "INSERT INTO libraries "
                "(id, device_id, display_name, path_flavor, root_path) "
                "VALUES (:id, :device, 'Lib', 'posix', '/tmp/synthetic')"
            ),
            {"id": LIBRARY_ID, "device": DEVICE_ID},
        )
        connection.execute(
            text(
                "INSERT INTO canonical_tags "
                "(key, display_name, created_at_ms, updated_at_ms) VALUES "
                "('cats', 'Cats', 1, 1), "
                "('dogs', 'Dogs', 1, 1), "
                "('birds', 'Birds', 1, 1), "
                "('fish', 'Fish', 1, 1), "
                "('cars', 'Cars', 1, 1), "
                "('trees', 'Trees', 1, 1), "
                "('cat-a', 'Feline', 1, 1), "
                "('cat-b', 'Feline', 1, 1)"
            )
        )
        _insert_media(connection, GENERIC, GENERIC_LOC, "general", "Canonical generic")
        _insert_media(connection, MOVIE, MOVIE_LOC, "movie", "A movie")
        _insert_media(connection, MOVIE_ID_MEDIA, MOVIE_ID_LOC, "general", "Has movie run")
        _insert_media(connection, WEBSITE, WEBSITE_LOC, "meme", None)
        _insert_media(connection, HISTORICAL, HISTORICAL_LOC, "general", None)
        _insert_media(connection, NULL_PROFILE, NULL_PROFILE_LOC, "general", "Null profile")
        _insert_analyzed_run(
            connection,
            GENERIC_RUN,
            GENERIC,
            GENERIC_LOC,
            completed_at_ms=100,
            title="Older success",
            tags=["Cats"],
            prompt_version="framenest-media-suggestion-v4",
        )
        _insert_failed_run(
            connection,
            GENERIC_FAIL,
            GENERIC,
            GENERIC_LOC,
            completed_at_ms=200,
        )
        _insert_analyzed_run(
            connection,
            MOVIE_RUN,
            MOVIE,
            MOVIE_LOC,
            completed_at_ms=150,
            title="Movie suggestion",
            tags=["Cats"],
        )
        _insert_analyzed_run(
            connection,
            MOVIE_ID_RUN,
            MOVIE_ID_MEDIA,
            MOVIE_ID_LOC,
            completed_at_ms=160,
            title="Movie identification",
            tags=["Cats"],
            analysis_definition="movie_identification",
            analysis_profile="movie_identification",
            prompt_version="framenest-movie-identification-prompt-v2",
        )
        _insert_analyzed_run(
            connection,
            WEBSITE_RUN,
            WEBSITE,
            WEBSITE_LOC,
            completed_at_ms=180,
            title="Website Analyze-by-AI",
            tags=["Dogs"],
        )
        historical_tags = [
            "Cats",
            "Dogs",
            "Birds",
            "Fish",
            "Cars",
            "Trees",
            "unknown-tag",
            "Feline",
        ]
        _insert_analyzed_run(
            connection,
            HISTORICAL_RUN,
            HISTORICAL,
            HISTORICAL_LOC,
            completed_at_ms=90,
            title="Historical v3",
            tags=historical_tags,
            prompt_version="framenest-media-suggestion-v3",
        )
        _insert_analyzed_run(
            connection,
            NULL_PROFILE_RUN,
            NULL_PROFILE,
            NULL_PROFILE_LOC,
            completed_at_ms=170,
            title="Null profile success",
            tags=["Cats"],
            analysis_profile=None,
        )


def _insert_media(connection, media_id: str, location_id: str, category: str, title: str | None) -> None:
    connection.execute(
        text(
            "INSERT INTO logical_media (id, media_kind, created_at_ms, updated_at_ms) "
            "VALUES (:id, 'video', 10, 10)"
        ),
        {"id": media_id},
    )
    connection.execute(
        text(
            "INSERT INTO physical_media_locations ("
            "id, media_id, library_id, relative_path, availability, "
            "observed_size_bytes, observed_mtime_ns, created_at_ms, updated_at_ms"
            ") VALUES (:id, :media, :library, :path, 'available', 8, NULL, 10, 10)"
        ),
        {"id": location_id, "media": media_id, "library": LIBRARY_ID, "path": f"{media_id}.mp4"},
    )
    connection.execute(
        text(
            "INSERT INTO media_metadata ("
            "media_id, display_title, description, created_at_ms, updated_at_ms, "
            "content_category, acquisition_source"
            ") VALUES (:id, :title, 'Desc', 10, 10, :category, 'manual_upload')"
        ),
        {"id": media_id, "title": title, "category": category},
    )


def _insert_analyzed_run(
    connection,
    run_id: str,
    media_id: str,
    location_id: str,
    *,
    completed_at_ms: int,
    title: str,
    tags: list[str],
    analysis_definition: str = "automatic_post_catalog",
    analysis_profile: str | None = "generic_media",
    prompt_version: str = "framenest-media-suggestion-v4",
) -> None:
    connection.execute(
        text(
            "INSERT INTO media_analysis_runs ("
            "id, media_id, media_location_id, analysis_definition, state, attempt_count, "
            "provider_id, model_id, prompt_version, result_schema_version, result_json, "
            "error_code, error_message, analysis_profile, created_at_ms, started_at_ms, "
            "completed_at_ms, version"
            ") VALUES ("
            ":id, :media, :location, :definition, 'analyzed', 1, "
            "'nvidia-nim', 'test-model', :prompt, "
            "'framenest-media-suggestion-result-v1', :result, "
            "NULL, NULL, :profile, :completed, :completed, :completed, 2)"
        ),
        {
            "id": run_id,
            "media": media_id,
            "location": location_id,
            "definition": analysis_definition,
            "prompt": prompt_version,
            "result": _result_json(title=title, tags=tags),
            "profile": analysis_profile,
            "completed": completed_at_ms,
        },
    )


def _insert_failed_run(
    connection, run_id: str, media_id: str, location_id: str, *, completed_at_ms: int
) -> None:
    connection.execute(
        text(
            "INSERT INTO media_analysis_runs ("
            "id, media_id, media_location_id, analysis_definition, state, attempt_count, "
            "provider_id, model_id, prompt_version, result_schema_version, result_json, "
            "error_code, error_message, analysis_profile, created_at_ms, started_at_ms, "
            "completed_at_ms, version"
            ") VALUES ("
            ":id, :media, :location, 'automatic_post_catalog', 'failed', 1, "
            "NULL, NULL, 'framenest-media-suggestion-v4', NULL, NULL, "
            "'PROVIDER_UNAVAILABLE', 'unavailable', 'generic_media', "
            ":completed, :completed, :completed, 2)"
        ),
        {
            "id": run_id,
            "media": media_id,
            "location": location_id,
            "completed": completed_at_ms,
        },
    )


def test_latest_successful_generic_exclusions_and_unopened_empty_table(
    tmp_path: Path,
) -> None:
    repository, engine = _repository(tmp_path)
    try:
        page = repository.list_inbox(actor_login_key=ADMIN_KEY, limit=25, cursor=None)
        ids = [item.media_id for item in page.items]
        assert WEBSITE in ids
        assert GENERIC in ids
        assert NULL_PROFILE in ids
        assert HISTORICAL in ids
        assert MOVIE not in ids
        assert MOVIE_ID_MEDIA not in ids
        generic = next(item for item in page.items if item.media_id == GENERIC)
        assert generic.analysis_run_id == GENERIC_RUN
        assert generic.title == "Canonical generic"
        assert generic.unopened is True
        assert page.unopened_count == len(page.items)
        assert all(item.unopened for item in page.items)
        website = next(item for item in page.items if item.media_id == WEBSITE)
        assert website.title == "Website Analyze-by-AI"
    finally:
        dispose_engine(engine)


def test_actor_opened_rows_are_isolated(tmp_path: Path) -> None:
    repository, engine = _repository(tmp_path)
    try:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO companion_review_open_states "
                    "(actor_login_key, media_id, opened_run_id, opened_at_ms) "
                    "VALUES (:actor, :media, :run, 300)"
                ),
                {"actor": ADMIN_KEY, "media": GENERIC, "run": GENERIC_RUN},
            )
        admin_page = repository.list_inbox(
            actor_login_key=ADMIN_KEY, limit=25, cursor=None
        )
        other_page = repository.list_inbox(
            actor_login_key=OTHER_KEY, limit=25, cursor=None
        )
        admin_generic = next(
            item for item in admin_page.items if item.media_id == GENERIC
        )
        other_generic = next(
            item for item in other_page.items if item.media_id == GENERIC
        )
        assert admin_generic.unopened is False
        assert other_generic.unopened is True
        assert admin_page.unopened_count == other_page.unopened_count - 1
    finally:
        dispose_engine(engine)


def test_keyset_pagination_is_stable(tmp_path: Path) -> None:
    repository, engine = _repository(tmp_path)
    try:
        with engine.begin() as connection:
            for index in range(30):
                media_id = f"{index + 10:08x}-0000-4000-8000-{index + 10:012x}"
                location_id = f"{index + 110:08x}-0000-4000-8000-{index + 110:012x}"
                run_id = f"{index + 210:08x}-0000-4000-8000-{index + 210:012x}"
                _insert_media(
                    connection, media_id, location_id, "general", f"Page {index}"
                )
                _insert_analyzed_run(
                    connection,
                    run_id,
                    media_id,
                    location_id,
                    completed_at_ms=1000 + index,
                    title=f"Page {index}",
                    tags=["Cats"],
                )
        first = repository.list_inbox(actor_login_key=ADMIN_KEY, limit=25, cursor=None)
        assert len(first.items) == 25
        assert first.next_cursor is not None
        second = repository.list_inbox(
            actor_login_key=ADMIN_KEY, limit=25, cursor=_decode_cursor_tuple(first.next_cursor)
        )
        first_ids = {item.media_id for item in first.items}
        second_ids = {item.media_id for item in second.items}
        assert first_ids.isdisjoint(second_ids)
        assert first.unopened_count == second.unopened_count
        assert first.unopened_count > 25
    finally:
        dispose_engine(engine)


def test_history_maps_historical_tags_and_movie_detail_is_excluded(
    tmp_path: Path,
) -> None:
    repository, engine = _repository(tmp_path)
    try:
        detail = repository.get_detail(
            media_id=MediaId.from_string(HISTORICAL),
            actor_login_key=ADMIN_KEY,
            limit=25,
            cursor=None,
        )
        assert detail.suggestions
        tags = detail.suggestions[0].tags
        statuses = [item.status for item in tags]
        assert MappedTagStatus.MAPPED in statuses
        assert MappedTagStatus.LEGACY_LIMIT in statuses
        assert MappedTagStatus.UNKNOWN in statuses
        assert MappedTagStatus.AMBIGUOUS in statuses
        assert all(detail.field_sources[name] is None for name in detail.field_sources)
        with pytest.raises(CompanionReviewMovieExcludedError):
            repository.get_detail(
                media_id=MediaId.from_string(MOVIE),
                actor_login_key=ADMIN_KEY,
                limit=25,
                cursor=None,
            )
    finally:
        dispose_engine(engine)


def test_corrupt_result_json_is_not_silent(tmp_path: Path) -> None:
    repository, engine = _repository(tmp_path)
    try:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "UPDATE media_analysis_runs SET result_json = '{not-json' "
                    "WHERE id = :id"
                ),
                {"id": WEBSITE_RUN},
            )
        with pytest.raises(CompanionReviewStoredResultError):
            repository.list_inbox(actor_login_key=ADMIN_KEY, limit=25, cursor=None)
    finally:
        dispose_engine(engine)


def _decode_cursor_tuple(cursor: str) -> tuple[int, str]:
    from framenest.application.companion_review import decode_companion_review_cursor

    parsed = decode_companion_review_cursor(cursor)
    assert parsed is not None
    return parsed


def test_mark_opened_is_actor_scoped_monotonic_and_idempotent(tmp_path: Path) -> None:
    repository, engine = _repository(tmp_path)
    try:
        with engine.begin() as connection:
            _insert_analyzed_run(
                connection,
                GENERIC_NEWER,
                GENERIC,
                GENERIC_LOC,
                completed_at_ms=300,
                title="Newer success",
                tags=["Cats"],
            )
        first = repository.mark_opened(
            media_id=MediaId.from_string(GENERIC),
            actor_login_key=ADMIN_KEY,
            analysis_run_id=MediaId.from_string(GENERIC_NEWER),
            now_ms=400,
        )
        assert first.opened_run_id == GENERIC_NEWER
        assert first.unopened is False
        second = repository.mark_opened(
            media_id=MediaId.from_string(GENERIC),
            actor_login_key=ADMIN_KEY,
            analysis_run_id=MediaId.from_string(GENERIC_RUN),
            now_ms=500,
        )
        assert second.opened_run_id == GENERIC_NEWER
        assert second.opened_at_ms == 400
        assert second.unopened is False
        refreshed = repository.mark_opened(
            media_id=MediaId.from_string(GENERIC),
            actor_login_key=ADMIN_KEY,
            analysis_run_id=MediaId.from_string(GENERIC_NEWER),
            now_ms=600,
        )
        assert refreshed.opened_run_id == GENERIC_NEWER
        assert refreshed.opened_at_ms == 600
        other = repository.list_inbox(actor_login_key=OTHER_KEY, limit=25, cursor=None)
        other_generic = next(item for item in other.items if item.media_id == GENERIC)
        assert other_generic.unopened is True
        admin = repository.list_inbox(actor_login_key=ADMIN_KEY, limit=25, cursor=None)
        admin_generic = next(item for item in admin.items if item.media_id == GENERIC)
        assert admin_generic.unopened is False
        older_only = repository.mark_opened(
            media_id=MediaId.from_string(HISTORICAL),
            actor_login_key=ADMIN_KEY,
            analysis_run_id=MediaId.from_string(HISTORICAL_RUN),
            now_ms=700,
        )
        assert older_only.unopened is False
        with pytest.raises(CompanionReviewRunNotEligibleError):
            repository.mark_opened(
                media_id=MediaId.from_string(GENERIC),
                actor_login_key=ADMIN_KEY,
                analysis_run_id=MediaId.from_string(GENERIC_FAIL),
                now_ms=800,
            )
        with pytest.raises(CompanionReviewMovieExcludedError):
            repository.mark_opened(
                media_id=MediaId.from_string(MOVIE),
                actor_login_key=ADMIN_KEY,
                analysis_run_id=MediaId.from_string(MOVIE_RUN),
                now_ms=800,
            )
    finally:
        dispose_engine(engine)


def test_apply_review_preserves_unselected_fields_and_replaces_tags(
    tmp_path: Path,
) -> None:
    repository, engine = _repository(tmp_path)
    try:
        title_only = repository.apply_review(
            media_id=MediaId.from_string(WEBSITE),
            actor_login_key=ADMIN_KEY,
            analysis_run_id=MediaId.from_string(WEBSITE_RUN),
            fields=("display_title",),
            tag_keys=(),
            now_ms=400,
        )
        assert title_only.metadata_status == "updated"
        assert title_only.canonical.display_title == "Website Analyze-by-AI"
        assert title_only.canonical.description == "Desc"
        assert title_only.canonical.tags == ()
        assert title_only.publication.status == "not_ready"
        inbox = repository.list_inbox(actor_login_key=ADMIN_KEY, limit=25, cursor=None)
        website = next(item for item in inbox.items if item.media_id == WEBSITE)
        assert website.unopened is True
        with engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO media_canonical_tags (media_id, tag_key, position) "
                    "VALUES (:media, 'dogs', 0)"
                ),
                {"media": GENERIC},
            )
        replaced = repository.apply_review(
            media_id=MediaId.from_string(GENERIC),
            actor_login_key=ADMIN_KEY,
            analysis_run_id=MediaId.from_string(GENERIC_RUN),
            fields=("tags",),
            tag_keys=("cats",),
            now_ms=401,
        )
        assert [tag.key for tag in replaced.canonical.tags] == ["cats"]
        assert replaced.canonical.display_title == "Canonical generic"
        assert replaced.canonical.description == "Desc"
        assert replaced.publication.status == "published"
        assert replaced.publication.origin == ContentPublicationOrigin.COMPANION_REVIEW.value
        with engine.connect() as connection:
            category = connection.execute(
                text(
                    "SELECT content_category, acquisition_source FROM media_metadata "
                    "WHERE media_id = :media"
                ),
                {"media": GENERIC},
            ).first()
            tag_count = connection.execute(text("SELECT COUNT(*) FROM canonical_tags")).scalar_one()
        assert category is not None
        assert category[0] == "general"
        assert category[1] == "manual_upload"
        assert int(tag_count) == 8
        assert replaced.canonical.field_sources["tags"] is not None
        assert replaced.canonical.field_sources["display_title"] is None
        repeat = repository.apply_review(
            media_id=MediaId.from_string(GENERIC),
            actor_login_key=ADMIN_KEY,
            analysis_run_id=MediaId.from_string(GENERIC_RUN),
            fields=("tags",),
            tag_keys=("cats",),
            now_ms=402,
        )
        assert repeat.publication.status == "already_published"
        assert repeat.publication.origin == ContentPublicationOrigin.COMPANION_REVIEW.value
        assert repeat.publication.published_at_ms == 401
    finally:
        dispose_engine(engine)


def test_apply_review_rejects_stale_mapping_zero_union_and_movie_race(
    tmp_path: Path,
) -> None:
    repository, engine = _repository(tmp_path)
    try:
        with pytest.raises(CompanionReviewStaleMappingError):
            repository.apply_review(
                media_id=MediaId.from_string(HISTORICAL),
                actor_login_key=ADMIN_KEY,
                analysis_run_id=MediaId.from_string(HISTORICAL_RUN),
                fields=("tags",),
                tag_keys=("dogs", "cats"),
                now_ms=10,
            )
        with pytest.raises(CompanionReviewStaleMappingError):
            repository.apply_review(
                media_id=MediaId.from_string(HISTORICAL),
                actor_login_key=ADMIN_KEY,
                analysis_run_id=MediaId.from_string(HISTORICAL_RUN),
                fields=("tags",),
                tag_keys=("trees",),
                now_ms=10,
            )
        accepted = repository.apply_review(
            media_id=MediaId.from_string(HISTORICAL),
            actor_login_key=ADMIN_KEY,
            analysis_run_id=MediaId.from_string(HISTORICAL_RUN),
            fields=("tags",),
            tag_keys=("cats", "birds"),
            now_ms=11,
        )
        assert [tag.key for tag in accepted.canonical.tags] == ["cats", "birds"]
        with engine.begin() as connection:
            connection.execute(
                text(
                    "UPDATE media_metadata SET content_category = 'movie' "
                    "WHERE media_id = :media"
                ),
                {"media": WEBSITE},
            )
        with pytest.raises(CompanionReviewMovieExcludedError):
            repository.apply_review(
                media_id=MediaId.from_string(WEBSITE),
                actor_login_key=ADMIN_KEY,
                analysis_run_id=MediaId.from_string(WEBSITE_RUN),
                fields=("display_title",),
                tag_keys=(),
                now_ms=12,
            )
        with engine.connect() as connection:
            title = connection.execute(
                text("SELECT display_title FROM media_metadata WHERE media_id = :media"),
                {"media": WEBSITE},
            ).scalar_one()
            receipts = connection.execute(
                text(
                    "SELECT COUNT(*) FROM companion_review_field_sources "
                    "WHERE media_id = :media"
                ),
                {"media": WEBSITE},
            ).scalar_one()
            publications = connection.execute(
                text(
                    "SELECT COUNT(*) FROM media_content_publications "
                    "WHERE media_id = :media"
                ),
                {"media": WEBSITE},
            ).scalar_one()
        assert title is None
        assert int(receipts) == 0
        assert int(publications) == 0
    finally:
        dispose_engine(engine)


def test_apply_review_same_value_newer_receipt_and_atomic_rollback(
    tmp_path: Path,
) -> None:
    repository, engine = _repository(tmp_path)
    try:
        first = repository.apply_review(
            media_id=MediaId.from_string(GENERIC),
            actor_login_key=ADMIN_KEY,
            analysis_run_id=MediaId.from_string(GENERIC_RUN),
            fields=("display_title",),
            tag_keys=(),
            now_ms=20,
        )
        assert first.canonical.field_sources["display_title"] is not None
        assert first.canonical.field_sources["display_title"].analysis_run_id == GENERIC_RUN
        with engine.begin() as connection:
            _insert_analyzed_run(
                connection,
                GENERIC_NEWER,
                GENERIC,
                GENERIC_LOC,
                completed_at_ms=350,
                title="Older success",
                tags=["Cats"],
            )
        second = repository.apply_review(
            media_id=MediaId.from_string(GENERIC),
            actor_login_key=ADMIN_KEY,
            analysis_run_id=MediaId.from_string(GENERIC_NEWER),
            fields=("display_title",),
            tag_keys=(),
            now_ms=21,
        )
        receipt = second.canonical.field_sources["display_title"]
        assert receipt is not None
        assert receipt.analysis_run_id == GENERIC_NEWER
        assert receipt.applied_at_ms == 21
        assert second.canonical.display_title == "Older success"
        from unittest.mock import patch

        from sqlalchemy.exc import SQLAlchemyError

        def _boom(*args, **kwargs):
            raise SQLAlchemyError("forced failure")

        with patch(
            "framenest.infrastructure.persistence.companion_review_repository._upsert_field_source",
            side_effect=_boom,
        ):
            with pytest.raises(FrameNestCompanionReviewRepositoryError):
                repository.apply_review(
                    media_id=MediaId.from_string(WEBSITE),
                    actor_login_key=ADMIN_KEY,
                    analysis_run_id=MediaId.from_string(WEBSITE_RUN),
                    fields=("display_title", "description", "tags"),
                    tag_keys=("dogs",),
                    now_ms=22,
                )
        with engine.connect() as connection:
            title = connection.execute(
                text("SELECT display_title FROM media_metadata WHERE media_id = :media"),
                {"media": WEBSITE},
            ).scalar_one()
            receipts = connection.execute(
                text(
                    "SELECT COUNT(*) FROM companion_review_field_sources "
                    "WHERE media_id = :media"
                ),
                {"media": WEBSITE},
            ).scalar_one()
            publications = connection.execute(
                text(
                    "SELECT COUNT(*) FROM media_content_publications "
                    "WHERE media_id = :media"
                ),
                {"media": WEBSITE},
            ).scalar_one()
        assert title is None
        assert int(receipts) == 0
        assert int(publications) == 0
    finally:
        dispose_engine(engine)
