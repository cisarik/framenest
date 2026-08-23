"""SQLite adapter for administrator companion review inbox reads."""

from __future__ import annotations

from sqlalchemy import and_, func, or_, select
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.sql import Select

from framenest.application.companion_review import (
    CanonicalTagView,
    CompanionReviewCanonicalTag,
    CompanionReviewCodecError,
    CompanionReviewDetail,
    CompanionReviewFieldSource,
    CompanionReviewInboxItem,
    CompanionReviewInboxPage,
    CompanionReviewSuggestion,
    canonical_field_digest,
    decode_stored_suggestion_result,
    derive_review_readiness,
    encode_companion_review_cursor,
    inbox_title,
    map_suggested_tags,
)
from framenest.application.ports.companion_review_repository import (
    CompanionReviewMediaNotFoundError,
    CompanionReviewMovieExcludedError,
    CompanionReviewStoredResultError,
    FrameNestCompanionReviewRepositoryError,
)
from framenest.domain.content_publication import ContentPublication, ContentPublicationOrigin
from framenest.domain.identities import MediaId
from framenest.domain.media_analysis_runs import (
    AUTOMATIC_POST_CATALOG_ANALYSIS_DEFINITION,
    RESULT_SCHEMA_VERSION,
)
from framenest.domain.media_classification import (
    AnalysisProfile,
    ContentCategory,
    DEFAULT_CONTENT_CATEGORY,
    MOVIE_IDENTIFICATION_ANALYSIS_DEFINITION,
)
from framenest.infrastructure.persistence.catalog_schema import (
    canonical_tags,
    companion_review_field_sources,
    companion_review_open_states,
    logical_media,
    media_analysis_runs,
    media_canonical_tags,
    media_content_publications,
    media_metadata,
)
from framenest.infrastructure.persistence.engine import run_in_transaction

_REPOSITORY_FAILURE_MESSAGE = "Companion review query failed."
_MEDIA_NOT_FOUND_MESSAGE = "The requested media item was not found."
_MOVIE_EXCLUDED_MESSAGE = "Movie workflows are excluded from companion review."
_STORED_RESULT_MESSAGE = "Stored analysis result is invalid."
_REVIEW_FIELDS = ("display_title", "tags", "description")


class SqliteCompanionReviewRepository:
    """Synchronous SQLite adapter for companion review reads."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def list_inbox(
        self,
        *,
        actor_login_key: str,
        limit: int,
        cursor: tuple[int, str] | None,
    ) -> CompanionReviewInboxPage:
        def operation(connection: Connection) -> CompanionReviewInboxPage:
            latest = _latest_successful_generic().subquery("latest_generic")
            opened = companion_review_open_states
            unopened_count = connection.execute(
                _unopened_count_statement(latest, actor_login_key)
            ).scalar_one()
            statement = (
                select(
                    latest.c.id,
                    latest.c.media_id,
                    latest.c.completed_at_ms,
                    latest.c.result_json,
                    latest.c.display_title,
                    opened.c.opened_run_id,
                )
                .select_from(
                    latest.outerjoin(
                        opened,
                        and_(
                            opened.c.actor_login_key == actor_login_key,
                            opened.c.media_id == latest.c.media_id,
                        ),
                    )
                )
            )
            statement = _apply_keyset(statement, latest, cursor)
            statement = statement.order_by(
                latest.c.completed_at_ms.desc(),
                latest.c.id.desc(),
            ).limit(limit + 1)
            rows = connection.execute(statement).mappings().all()
            has_more = len(rows) > limit
            page_rows = rows[:limit]
            items = tuple(_inbox_item_from_row(row) for row in page_rows)
            next_cursor = None
            if has_more and items:
                last = items[-1]
                next_cursor = encode_companion_review_cursor(
                    completed_at_ms=last.completed_at_ms,
                    analysis_run_id=last.analysis_run_id,
                )
            return CompanionReviewInboxPage(
                items=items,
                unopened_count=int(unopened_count),
                next_cursor=next_cursor,
            )

        try:
            return run_in_transaction(self._engine, operation)
        except FrameNestCompanionReviewRepositoryError:
            raise
        except SQLAlchemyError as exc:
            raise FrameNestCompanionReviewRepositoryError(
                _REPOSITORY_FAILURE_MESSAGE
            ) from exc

    def get_detail(
        self,
        *,
        media_id: MediaId,
        actor_login_key: str,
        limit: int,
        cursor: tuple[int, str] | None,
    ) -> CompanionReviewDetail:
        del actor_login_key

        def operation(connection: Connection) -> CompanionReviewDetail:
            media_id_text = media_id.to_string()
            exists = connection.execute(
                select(logical_media.c.id).where(logical_media.c.id == media_id_text)
            ).first()
            if exists is None:
                raise CompanionReviewMediaNotFoundError(_MEDIA_NOT_FOUND_MESSAGE)
            metadata_row = connection.execute(
                select(
                    media_metadata.c.display_title,
                    media_metadata.c.description,
                    media_metadata.c.content_category,
                ).where(media_metadata.c.media_id == media_id_text)
            ).mappings().first()
            content_category = DEFAULT_CONTENT_CATEGORY.value
            display_title = None
            description = None
            if metadata_row is not None:
                content_category = str(
                    metadata_row["content_category"] or DEFAULT_CONTENT_CATEGORY.value
                )
                display_title = metadata_row["display_title"]
                description = metadata_row["description"]
                if isinstance(display_title, str) and not display_title.strip():
                    display_title = None
                if isinstance(description, str) and not description.strip():
                    description = None
            if content_category == ContentCategory.MOVIE.value:
                raise CompanionReviewMovieExcludedError(_MOVIE_EXCLUDED_MESSAGE)

            tag_rows = connection.execute(
                select(
                    canonical_tags.c.key,
                    canonical_tags.c.display_name,
                    media_canonical_tags.c.position,
                )
                .select_from(
                    media_canonical_tags.join(
                        canonical_tags,
                        canonical_tags.c.key == media_canonical_tags.c.tag_key,
                    )
                )
                .where(media_canonical_tags.c.media_id == media_id_text)
                .order_by(media_canonical_tags.c.position, canonical_tags.c.key)
            ).mappings().all()
            tags = tuple(
                CompanionReviewCanonicalTag(
                    key=str(row["key"]),
                    display_name=str(row["display_name"]),
                    position=int(row["position"]),
                )
                for row in tag_rows
            )
            publication = _load_publication(connection, media_id_text)
            field_sources = _load_field_sources(
                connection,
                media_id=media_id_text,
                display_title=display_title if isinstance(display_title, str) else None,
                description=description if isinstance(description, str) else None,
                tag_keys=tuple(tag.key for tag in tags),
            )
            definition_catalog = _load_canonical_catalog(connection)
            runs = _load_history_page(
                connection,
                media_id=media_id_text,
                limit=limit,
                cursor=cursor,
            )
            has_more = len(runs) > limit
            page_runs = runs[:limit]
            suggestions = tuple(
                _suggestion_from_run(run, definition_catalog) for run in page_runs
            )
            next_cursor = None
            if has_more and suggestions:
                last = suggestions[-1]
                next_cursor = encode_companion_review_cursor(
                    completed_at_ms=last.completed_at_ms,
                    analysis_run_id=last.analysis_run_id,
                )
            return CompanionReviewDetail(
                media_id=media_id_text,
                display_title=display_title if isinstance(display_title, str) else None,
                description=description if isinstance(description, str) else None,
                tags=tags,
                field_sources=field_sources,
                publication=publication,
                readiness=derive_review_readiness(
                    display_title=display_title if isinstance(display_title, str) else None,
                    description=description if isinstance(description, str) else None,
                    tag_count=len(tags),
                ),
                suggestions=suggestions,
                next_cursor=next_cursor,
            )

        try:
            return run_in_transaction(self._engine, operation)
        except FrameNestCompanionReviewRepositoryError:
            raise
        except CompanionReviewCodecError as exc:
            raise CompanionReviewStoredResultError(_STORED_RESULT_MESSAGE) from exc
        except SQLAlchemyError as exc:
            raise FrameNestCompanionReviewRepositoryError(
                _REPOSITORY_FAILURE_MESSAGE
            ) from exc


def _latest_successful_generic():
    ranked = (
        select(
            media_analysis_runs.c.id,
            media_analysis_runs.c.media_id,
            media_analysis_runs.c.completed_at_ms,
            media_analysis_runs.c.result_json,
            media_metadata.c.display_title,
            func.row_number()
            .over(
                partition_by=media_analysis_runs.c.media_id,
                order_by=(
                    media_analysis_runs.c.completed_at_ms.desc(),
                    media_analysis_runs.c.id.desc(),
                ),
            )
            .label("rn"),
        )
        .select_from(
            media_analysis_runs.outerjoin(
                media_metadata,
                media_metadata.c.media_id == media_analysis_runs.c.media_id,
            )
        )
        .where(*_successful_generic_predicates())
    ).subquery("ranked_generic")
    return select(ranked).where(ranked.c.rn == 1)


def _successful_generic_predicates() -> tuple[object, ...]:
    return (
        media_analysis_runs.c.state == "analyzed",
        media_analysis_runs.c.analysis_definition
        == AUTOMATIC_POST_CATALOG_ANALYSIS_DEFINITION,
        media_analysis_runs.c.analysis_definition
        != MOVIE_IDENTIFICATION_ANALYSIS_DEFINITION,
        media_analysis_runs.c.result_schema_version == RESULT_SCHEMA_VERSION,
        or_(
            media_analysis_runs.c.analysis_profile
            == AnalysisProfile.GENERIC_MEDIA.value,
            media_analysis_runs.c.analysis_profile.is_(None),
        ),
        media_analysis_runs.c.completed_at_ms.is_not(None),
        func.coalesce(
            media_metadata.c.content_category, DEFAULT_CONTENT_CATEGORY.value
        )
        != ContentCategory.MOVIE.value,
    )


def _unopened_count_statement(latest, actor_login_key: str) -> Select:
    opened = companion_review_open_states
    joined = latest.outerjoin(
        opened,
        and_(
            opened.c.actor_login_key == actor_login_key,
            opened.c.media_id == latest.c.media_id,
        ),
    )
    return (
        select(func.count())
        .select_from(joined)
        .where(
            or_(
                opened.c.opened_run_id.is_(None),
                opened.c.opened_run_id != latest.c.id,
            )
        )
    )


def _apply_keyset(
    statement: Select,
    latest,
    cursor: tuple[int, str] | None,
) -> Select:
    if cursor is None:
        return statement
    completed_at_ms, analysis_run_id = cursor
    return statement.where(
        or_(
            latest.c.completed_at_ms < completed_at_ms,
            and_(
                latest.c.completed_at_ms == completed_at_ms,
                latest.c.id < analysis_run_id,
            ),
        )
    )


def _inbox_item_from_row(row: object) -> CompanionReviewInboxItem:
    mapping = dict(row)  # type: ignore[arg-type]
    try:
        stored = decode_stored_suggestion_result(str(mapping["result_json"]))
    except CompanionReviewCodecError as exc:
        raise CompanionReviewStoredResultError(_STORED_RESULT_MESSAGE) from exc
    canonical_title = mapping.get("display_title")
    title = inbox_title(
        canonical_display_title=(
            str(canonical_title) if isinstance(canonical_title, str) else None
        ),
        stored=stored,
    )
    analysis_run_id = str(mapping["id"])
    opened_run_id = mapping.get("opened_run_id")
    unopened = opened_run_id is None or str(opened_run_id) != analysis_run_id
    return CompanionReviewInboxItem(
        media_id=str(mapping["media_id"]),
        title=title,
        analysis_run_id=analysis_run_id,
        completed_at_ms=int(mapping["completed_at_ms"]),
        unopened=unopened,
    )


def _load_publication(
    connection: Connection, media_id: str
) -> ContentPublication | None:
    row = connection.execute(
        select(media_content_publications).where(
            media_content_publications.c.media_id == media_id
        )
    ).mappings().first()
    if row is None:
        return None
    return ContentPublication(
        media_id=str(row["media_id"]),
        published_at_ms=int(row["published_at_ms"]),
        publication_origin=ContentPublicationOrigin(str(row["publication_origin"])),
    )


def _load_canonical_catalog(connection: Connection) -> tuple[CanonicalTagView, ...]:
    rows = connection.execute(
        select(canonical_tags.c.key, canonical_tags.c.display_name).order_by(
            canonical_tags.c.display_name, canonical_tags.c.key
        )
    ).mappings().all()
    return tuple(
        CanonicalTagView(key=str(row["key"]), display_name=str(row["display_name"]))
        for row in rows
    )


def _load_field_sources(
    connection: Connection,
    *,
    media_id: str,
    display_title: str | None,
    description: str | None,
    tag_keys: tuple[str, ...],
) -> dict[str, CompanionReviewFieldSource | None]:
    receipts: dict[str, CompanionReviewFieldSource | None] = {
        field: None for field in _REVIEW_FIELDS
    }
    current_digests = {
        "display_title": (
            None
            if display_title is None
            else canonical_field_digest("display_title", display_title)
        ),
        "description": (
            None
            if description is None
            else canonical_field_digest("description", description)
        ),
        "tags": canonical_field_digest("tags", tag_keys),
    }
    rows = connection.execute(
        select(
            companion_review_field_sources.c.field_name,
            companion_review_field_sources.c.analysis_run_id,
            companion_review_field_sources.c.applied_at_ms,
            companion_review_field_sources.c.value_digest,
            media_analysis_runs.c.completed_at_ms,
            media_analysis_runs.c.provider_id,
            media_analysis_runs.c.model_id,
        )
        .select_from(
            companion_review_field_sources.join(
                media_analysis_runs,
                media_analysis_runs.c.id
                == companion_review_field_sources.c.analysis_run_id,
            )
        )
        .where(companion_review_field_sources.c.media_id == media_id)
    ).mappings().all()
    for row in rows:
        field_name = str(row["field_name"])
        expected = current_digests.get(field_name)
        if expected is None or str(row["value_digest"]) != expected:
            continue
        receipts[field_name] = CompanionReviewFieldSource(
            analysis_run_id=str(row["analysis_run_id"]),
            completed_at_ms=int(row["completed_at_ms"]),
            provider_id=str(row["provider_id"]),
            model_id=str(row["model_id"]),
            applied_at_ms=int(row["applied_at_ms"]),
        )
    return receipts


def _load_history_page(
    connection: Connection,
    *,
    media_id: str,
    limit: int,
    cursor: tuple[int, str] | None,
) -> list[object]:
    statement = (
        select(
            media_analysis_runs.c.id,
            media_analysis_runs.c.completed_at_ms,
            media_analysis_runs.c.provider_id,
            media_analysis_runs.c.model_id,
            media_analysis_runs.c.prompt_version,
            media_analysis_runs.c.result_json,
        )
        .select_from(
            media_analysis_runs.outerjoin(
                media_metadata,
                media_metadata.c.media_id == media_analysis_runs.c.media_id,
            )
        )
        .where(
            media_analysis_runs.c.media_id == media_id,
            *_successful_generic_predicates(),
        )
    )
    if cursor is not None:
        completed_at_ms, analysis_run_id = cursor
        statement = statement.where(
            or_(
                media_analysis_runs.c.completed_at_ms < completed_at_ms,
                and_(
                    media_analysis_runs.c.completed_at_ms == completed_at_ms,
                    media_analysis_runs.c.id < analysis_run_id,
                ),
            )
        )
    statement = statement.order_by(
        media_analysis_runs.c.completed_at_ms.desc(),
        media_analysis_runs.c.id.desc(),
    ).limit(limit + 1)
    return list(connection.execute(statement).mappings().all())


def _suggestion_from_run(
    row: object, catalog: tuple[CanonicalTagView, ...]
) -> CompanionReviewSuggestion:
    mapping = dict(row)  # type: ignore[arg-type]
    try:
        stored = decode_stored_suggestion_result(str(mapping["result_json"]))
    except CompanionReviewCodecError as exc:
        raise CompanionReviewStoredResultError(_STORED_RESULT_MESSAGE) from exc
    return CompanionReviewSuggestion(
        analysis_run_id=str(mapping["id"]),
        completed_at_ms=int(mapping["completed_at_ms"]),
        provider_id=str(mapping["provider_id"]),
        model_id=str(mapping["model_id"]),
        prompt_version=str(mapping["prompt_version"]),
        title=stored.title,
        description=stored.description,
        tags=map_suggested_tags(stored.tags, catalog),
    )
