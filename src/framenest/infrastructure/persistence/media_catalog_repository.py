"""SQLAlchemy Core adapter for the searchable media catalog read model."""

from __future__ import annotations

from collections import defaultdict

from sqlalchemy import and_, distinct, exists, func, or_, select
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.exc import SQLAlchemyError

from framenest.application.ports.media_catalog_repository import (
    CatalogMediaItem,
    CatalogMediaLocation,
    CatalogMediaTag,
    FrameNestMediaCatalogRepositoryError,
    MediaCatalogPage,
    MediaCatalogQuery,
)
from framenest.application.ports.media_content import SUPPORTED_MEDIA_CONTENT
from framenest.domain.media import MediaKind, MediaLocationAvailability
from framenest.infrastructure.persistence.catalog_schema import (
    canonical_tags,
    logical_media,
    media_canonical_tags,
    media_content_publications,
    media_metadata,
    physical_media_locations,
    x_assets,
    x_post_claims,
)
from framenest.infrastructure.persistence.engine import run_in_transaction

_REPOSITORY_FAILURE_MESSAGE = "Media catalog query failed."
_LIKE_ESCAPE = "\\"


class SqliteMediaCatalogRepository:
    """Synchronous SQLite searchable catalog read adapter."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def list_media(self, query: MediaCatalogQuery) -> MediaCatalogPage:
        def operation(connection: Connection) -> MediaCatalogPage:
            tag_values = _distinct_tag_values(query)
            companion = query.companion_audience_login_key is not None
            filtered = _filtered_media_select(query, tag_values).subquery()
            total = connection.execute(
                select(func.count()).select_from(filtered)
            ).scalar_one()
            if companion or query.collection_key is None:
                order_columns = [
                    filtered.c.created_at_ms.desc(),
                    filtered.c.id.asc(),
                ]
            else:
                order_columns = [
                    filtered.c.processed_at_ms.asc(),
                    filtered.c.id.asc(),
                ]
            page_statement = select(
                filtered.c.id,
                filtered.c.media_kind,
                filtered.c.created_at_ms,
                filtered.c.updated_at_ms,
                filtered.c.display_title,
                filtered.c.description,
                filtered.c.collection_key,
                filtered.c.processed_at_ms,
                filtered.c.content_category,
                filtered.c.acquisition_source,
                filtered.c.creator_attribution_kind,
                filtered.c.creator_stable_id,
                filtered.c.creator_handle,
                filtered.c.creator_display_name,
            )
            if (
                companion
                and query.cursor_created_at_ms is not None
                and query.cursor_media_id is not None
            ):
                page_statement = page_statement.where(
                    or_(
                        filtered.c.created_at_ms < query.cursor_created_at_ms,
                        and_(
                            filtered.c.created_at_ms == query.cursor_created_at_ms,
                            filtered.c.id > query.cursor_media_id,
                        ),
                    )
                )
            fetch_limit = query.limit + 1 if companion else query.limit
            page_statement = page_statement.order_by(*order_columns).limit(fetch_limit)
            if not companion:
                page_statement = page_statement.offset(query.offset)
            page_rows = list(connection.execute(page_statement).mappings())
            next_cursor = None
            if companion and len(page_rows) > query.limit:
                page_rows = page_rows[: query.limit]
                last = page_rows[-1]
                next_cursor = f"{int(last['created_at_ms'])}:{last['id']}"
            media_ids = tuple(str(row["id"]) for row in page_rows)
            tags_by_media = _load_tags(connection, media_ids)
            locations_by_media = _load_locations(connection, media_ids)
            items = tuple(
                CatalogMediaItem(
                    media_id=str(row["id"]),
                    media_kind=str(row["media_kind"]),
                    created_at_ms=int(row["created_at_ms"]),
                    updated_at_ms=int(row["updated_at_ms"]),
                    display_title=None
                    if row["display_title"] is None
                    else str(row["display_title"]),
                    collection_key=None
                    if row["collection_key"] is None
                    else str(row["collection_key"]),
                    processed_at_ms=None
                    if row["processed_at_ms"] is None
                    else int(row["processed_at_ms"]),
                    tags=tuple(tags_by_media[str(row["id"])]),
                    locations=tuple(locations_by_media[str(row["id"])]),
                    content_category=(
                        "general"
                        if row["content_category"] is None
                        else str(row["content_category"])
                    ),
                    acquisition_source=(
                        "unknown"
                        if row["acquisition_source"] is None
                        else str(row["acquisition_source"])
                    ),
                    description=None
                    if row["description"] is None
                    else str(row["description"]),
                    creator_attribution_kind=None
                    if row["creator_attribution_kind"] is None
                    else str(row["creator_attribution_kind"]),
                    creator_stable_id=None
                    if row["creator_stable_id"] is None
                    else str(row["creator_stable_id"]),
                    creator_handle=None
                    if row["creator_handle"] is None
                    else str(row["creator_handle"]),
                    creator_display_name=None
                    if row["creator_display_name"] is None
                    else str(row["creator_display_name"]),
                )
                for row in page_rows
            )
            return MediaCatalogPage(
                items=items,
                total=int(total),
                limit=query.limit,
                offset=query.offset,
                q=query.q,
                tag_keys=query.tag_keys,
                content_category=query.content_category,
                acquisition_source=query.acquisition_source,
                creator_attribution_kind=query.creator_attribution_kind,
                creator_stable_id=query.creator_stable_id,
                creator_handle=query.creator_handle,
                next_cursor=next_cursor,
            )

        try:
            return run_in_transaction(self._engine, operation)
        except FrameNestMediaCatalogRepositoryError:
            raise
        except SQLAlchemyError as exc:
            raise FrameNestMediaCatalogRepositoryError(_REPOSITORY_FAILURE_MESSAGE) from exc

    def get_media_item(self, media_id: str) -> CatalogMediaItem | None:
        def operation(connection: Connection) -> CatalogMediaItem | None:
            row = connection.execute(
                select(
                    logical_media.c.id,
                    logical_media.c.media_kind,
                    logical_media.c.created_at_ms,
                    logical_media.c.updated_at_ms,
                    media_metadata.c.display_title,
                    media_metadata.c.description,
                    media_metadata.c.collection_key,
                    media_metadata.c.processed_at_ms,
                    media_metadata.c.content_category,
                    media_metadata.c.acquisition_source,
                    media_metadata.c.creator_attribution_kind,
                    media_metadata.c.creator_stable_id,
                    media_metadata.c.creator_handle,
                    media_metadata.c.creator_display_name,
                )
                .select_from(
                    logical_media.outerjoin(
                        media_metadata,
                        media_metadata.c.media_id == logical_media.c.id,
                    )
                )
                .where(logical_media.c.id == media_id)
            ).mappings().first()
            if row is None:
                return None
            media_ids = (str(row["id"]),)
            tags_by_media = _load_tags(connection, media_ids)
            locations_by_media = _load_locations(connection, media_ids)
            return CatalogMediaItem(
                media_id=str(row["id"]),
                media_kind=str(row["media_kind"]),
                created_at_ms=int(row["created_at_ms"]),
                updated_at_ms=int(row["updated_at_ms"]),
                display_title=None
                if row["display_title"] is None
                else str(row["display_title"]),
                collection_key=None
                if row["collection_key"] is None
                else str(row["collection_key"]),
                processed_at_ms=None
                if row["processed_at_ms"] is None
                else int(row["processed_at_ms"]),
                tags=tuple(tags_by_media[str(row["id"])]),
                locations=tuple(locations_by_media[str(row["id"])]),
                content_category=(
                    "general"
                    if row["content_category"] is None
                    else str(row["content_category"])
                ),
                acquisition_source=(
                    "unknown"
                    if row["acquisition_source"] is None
                    else str(row["acquisition_source"])
                ),
                description=None
                if row["description"] is None
                else str(row["description"]),
                creator_attribution_kind=None
                if row["creator_attribution_kind"] is None
                else str(row["creator_attribution_kind"]),
                creator_stable_id=None
                if row["creator_stable_id"] is None
                else str(row["creator_stable_id"]),
                creator_handle=None
                if row["creator_handle"] is None
                else str(row["creator_handle"]),
                creator_display_name=None
                if row["creator_display_name"] is None
                else str(row["creator_display_name"]),
            )

        try:
            return run_in_transaction(self._engine, operation)
        except FrameNestMediaCatalogRepositoryError:
            raise
        except SQLAlchemyError as exc:
            raise FrameNestMediaCatalogRepositoryError(_REPOSITORY_FAILURE_MESSAGE) from exc


def _filtered_media_select(query: MediaCatalogQuery, tag_values: tuple[str, ...]):
    joined = logical_media.outerjoin(
        media_metadata,
        media_metadata.c.media_id == logical_media.c.id,
    )
    if query.published_only and query.companion_audience_login_key is None:
        joined = joined.join(
            media_content_publications,
            media_content_publications.c.media_id == logical_media.c.id,
        )
    if tag_values:
        joined = joined.join(
            media_canonical_tags,
            media_canonical_tags.c.media_id == logical_media.c.id,
        )
    statement = select(
        logical_media.c.id,
        logical_media.c.media_kind,
        logical_media.c.created_at_ms,
        logical_media.c.updated_at_ms,
        media_metadata.c.display_title,
        media_metadata.c.description,
        media_metadata.c.collection_key,
        media_metadata.c.processed_at_ms,
        media_metadata.c.content_category,
        media_metadata.c.acquisition_source,
        media_metadata.c.creator_attribution_kind,
        media_metadata.c.creator_stable_id,
        media_metadata.c.creator_handle,
        media_metadata.c.creator_display_name,
    ).select_from(joined)
    if query.q is not None:
        statement = statement.where(
            media_metadata.c.display_title.collate("NOCASE").like(
                _like_pattern(query.q),
                escape=_LIKE_ESCAPE,
            )
        )
    if query.collection_key is not None:
        statement = statement.where(
            media_metadata.c.collection_key == query.collection_key.value
        )
    if query.content_category is not None:
        statement = statement.where(
            media_metadata.c.content_category == query.content_category
        )
    if query.acquisition_source is not None:
        statement = statement.where(
            media_metadata.c.acquisition_source == query.acquisition_source
        )
    if (
        query.creator_attribution_kind is not None
        and query.creator_stable_id is not None
    ):
        statement = statement.where(
            media_metadata.c.creator_attribution_kind
            == query.creator_attribution_kind,
            media_metadata.c.creator_stable_id == query.creator_stable_id,
        )
    elif (
        query.creator_attribution_kind is not None
        and query.creator_handle is not None
    ):
        statement = statement.where(
            media_metadata.c.creator_attribution_kind
            == query.creator_attribution_kind,
            media_metadata.c.creator_handle == query.creator_handle,
        )
    if query.companion_audience_login_key is not None:
        statement = statement.where(
            _companion_audience_predicate(query.companion_audience_login_key)
        )
        kinds = query.companion_kinds or (
            MediaKind.IMAGE.value,
            MediaKind.ANIMATED_IMAGE.value,
            MediaKind.VIDEO.value,
        )
        statement = statement.where(logical_media.c.media_kind.in_(kinds))
        statement = statement.where(_supported_companion_location_exists())
    if tag_values:
        statement = (
            statement.where(media_canonical_tags.c.tag_key.in_(tag_values))
            .group_by(
                logical_media.c.id,
                logical_media.c.media_kind,
                logical_media.c.created_at_ms,
                logical_media.c.updated_at_ms,
                media_metadata.c.display_title,
                media_metadata.c.description,
                media_metadata.c.collection_key,
                media_metadata.c.processed_at_ms,
                media_metadata.c.content_category,
                media_metadata.c.acquisition_source,
                media_metadata.c.creator_attribution_kind,
                media_metadata.c.creator_stable_id,
                media_metadata.c.creator_handle,
                media_metadata.c.creator_display_name,
            )
            .having(func.count(distinct(media_canonical_tags.c.tag_key)) == len(tag_values))
        )
    return statement


def _companion_audience_predicate(login_key: str):
    published = exists(
        select(1)
        .select_from(media_content_publications)
        .where(media_content_publications.c.media_id == logical_media.c.id)
    )
    own_x_success = exists(
        select(1)
        .select_from(
            x_assets.join(x_post_claims, x_assets.c.claim_id == x_post_claims.c.id)
        )
        .where(
            x_assets.c.media_id == logical_media.c.id,
            x_assets.c.state == "cataloged",
            x_post_claims.c.created_by_login_key == login_key,
        )
    )
    return or_(published, own_x_success)


def _supported_companion_location_exists():
    clauses = []
    for kind, extension in SUPPORTED_MEDIA_CONTENT:
        extension_length = len(extension)
        clauses.append(
            and_(
                logical_media.c.media_kind == kind.value,
                physical_media_locations.c.availability
                == MediaLocationAvailability.AVAILABLE.value,
                func.lower(
                    func.substr(
                        physical_media_locations.c.relative_path,
                        func.length(physical_media_locations.c.relative_path)
                        - extension_length
                        + 1,
                    )
                )
                == extension,
            )
        )
    return exists(
        select(1)
        .select_from(physical_media_locations)
        .where(
            physical_media_locations.c.media_id == logical_media.c.id,
            or_(*clauses),
        )
    )


def _load_tags(
    connection: Connection,
    media_ids: tuple[str, ...],
) -> dict[str, list[CatalogMediaTag]]:
    tags_by_media: dict[str, list[CatalogMediaTag]] = defaultdict(list)
    if not media_ids:
        return tags_by_media
    rows = connection.execute(
        select(
            media_canonical_tags.c.media_id,
            media_canonical_tags.c.tag_key,
            canonical_tags.c.display_name,
            media_canonical_tags.c.position,
        )
        .select_from(
            media_canonical_tags.join(
                canonical_tags,
                canonical_tags.c.key == media_canonical_tags.c.tag_key,
            )
        )
        .where(media_canonical_tags.c.media_id.in_(media_ids))
        .order_by(
            media_canonical_tags.c.media_id.asc(),
            media_canonical_tags.c.position.asc(),
            media_canonical_tags.c.tag_key.asc(),
        )
    ).mappings()
    for row in rows:
        tags_by_media[str(row["media_id"])].append(
            CatalogMediaTag(
                key=str(row["tag_key"]),
                display_name=str(row["display_name"]),
                position=int(row["position"]),
            )
        )
    return tags_by_media


def _load_locations(
    connection: Connection,
    media_ids: tuple[str, ...],
) -> dict[str, list[CatalogMediaLocation]]:
    locations_by_media: dict[str, list[CatalogMediaLocation]] = defaultdict(list)
    if not media_ids:
        return locations_by_media
    rows = connection.execute(
        select(
            physical_media_locations.c.media_id,
            physical_media_locations.c.id,
            physical_media_locations.c.library_id,
            physical_media_locations.c.relative_path,
            physical_media_locations.c.availability,
            physical_media_locations.c.observed_size_bytes,
            physical_media_locations.c.observed_mtime_ns,
        )
        .where(physical_media_locations.c.media_id.in_(media_ids))
        .order_by(
            physical_media_locations.c.media_id.asc(),
            physical_media_locations.c.library_id.asc(),
            physical_media_locations.c.relative_path.asc(),
            physical_media_locations.c.id.asc(),
        )
    ).mappings()
    for row in rows:
        locations_by_media[str(row["media_id"])].append(
            CatalogMediaLocation(
                location_id=str(row["id"]),
                library_id=str(row["library_id"]),
                relative_path=str(row["relative_path"]),
                availability=str(row["availability"]),
                observed_size_bytes=None
                if row["observed_size_bytes"] is None
                else int(row["observed_size_bytes"]),
                observed_mtime_ns=None
                if row["observed_mtime_ns"] is None
                else int(row["observed_mtime_ns"]),
            )
        )
    return locations_by_media


def _distinct_tag_values(query: MediaCatalogQuery) -> tuple[str, ...]:
    values: list[str] = []
    seen: set[str] = set()
    for key in query.tag_keys:
        if key.value not in seen:
            seen.add(key.value)
            values.append(key.value)
    return tuple(values)


def _like_pattern(value: str) -> str:
    return f"%{_escape_like(value)}%"


def _escape_like(value: str) -> str:
    return (
        value.replace(_LIKE_ESCAPE, _LIKE_ESCAPE + _LIKE_ESCAPE)
        .replace("%", _LIKE_ESCAPE + "%")
        .replace("_", _LIKE_ESCAPE + "_")
    )
