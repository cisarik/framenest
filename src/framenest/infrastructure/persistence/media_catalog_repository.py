"""SQLAlchemy Core adapter for the searchable media catalog read model."""

from __future__ import annotations

from collections import defaultdict

from sqlalchemy import distinct, func, select
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
from framenest.infrastructure.persistence.catalog_schema import (
    canonical_tags,
    logical_media,
    media_canonical_tags,
    media_metadata,
    physical_media_locations,
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
            filtered = _filtered_media_select(query, tag_values).subquery()
            total = connection.execute(
                select(func.count()).select_from(filtered)
            ).scalar_one()
            if query.collection_key is not None:
                order_columns = [
                    filtered.c.processed_at_ms.asc(),
                    filtered.c.id.asc(),
                ]
            else:
                order_columns = [
                    filtered.c.created_at_ms.desc(),
                    filtered.c.id.asc(),
                ]
            page_rows = list(
                connection.execute(
                    select(
                        filtered.c.id,
                        filtered.c.media_kind,
                        filtered.c.created_at_ms,
                        filtered.c.updated_at_ms,
                        filtered.c.display_title,
                        filtered.c.collection_key,
                        filtered.c.processed_at_ms,
                        filtered.c.content_category,
                        filtered.c.acquisition_source,
                    )
                    .order_by(*order_columns)
                    .limit(query.limit)
                    .offset(query.offset)
                ).mappings()
            )
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
        media_metadata.c.collection_key,
        media_metadata.c.processed_at_ms,
        media_metadata.c.content_category,
        media_metadata.c.acquisition_source,
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
    if tag_values:
        statement = (
            statement.where(media_canonical_tags.c.tag_key.in_(tag_values))
            .group_by(
                logical_media.c.id,
                logical_media.c.media_kind,
                logical_media.c.created_at_ms,
                logical_media.c.updated_at_ms,
                media_metadata.c.display_title,
                media_metadata.c.collection_key,
                media_metadata.c.processed_at_ms,
                media_metadata.c.content_category,
                media_metadata.c.acquisition_source,
            )
            .having(func.count(distinct(media_canonical_tags.c.tag_key)) == len(tag_values))
        )
    return statement


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
