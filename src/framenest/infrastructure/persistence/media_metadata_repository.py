"""SQLAlchemy Core adapter for persistent media metadata and canonical tags."""

from __future__ import annotations

from sqlalchemy import delete, insert, select, update
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from framenest.application.ports.media_metadata_repository import (
    CanonicalTagCreateResult,
    CanonicalTagDefinitionConflictError,
    CanonicalTagNotFoundError,
    FrameNestMediaMetadataRepositoryError,
    MediaMetadataMediaNotFoundError,
    MediaMetadataSaveResult,
    MediaMetadataSnapshot,
)
from framenest.domain import FrameNestIdentityError, MediaId
from framenest.domain.media_metadata import (
    CanonicalTag,
    CanonicalTagDisplayName,
    CanonicalTagKey,
    FrameNestMediaMetadataError,
    MediaDisplayTitle,
)
from framenest.infrastructure.persistence.catalog_schema import (
    canonical_tags,
    logical_media,
    media_canonical_tags,
    media_metadata,
)
from framenest.infrastructure.persistence.engine import run_in_transaction

_REPOSITORY_FAILURE_MESSAGE = "Media metadata operation failed."


class SqliteMediaMetadataRepository:
    """Synchronous SQLite metadata repository backed by SQLAlchemy Core."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def create_canonical_tag(
        self,
        key: CanonicalTagKey,
        display_name: CanonicalTagDisplayName,
        now_ms: int,
    ) -> CanonicalTagCreateResult:
        def operation(connection: Connection) -> CanonicalTagCreateResult:
            existing = _get_tag(connection, key)
            if existing is not None:
                if existing.display_name != display_name:
                    raise CanonicalTagDefinitionConflictError()
                return CanonicalTagCreateResult(status="already_exists", tag=existing)
            tag = CanonicalTag(
                key=key,
                display_name=display_name,
                created_at_ms=now_ms,
                updated_at_ms=now_ms,
            )
            connection.execute(
                insert(canonical_tags).values(
                    key=tag.key.value,
                    display_name=tag.display_name.value,
                    created_at_ms=tag.created_at_ms,
                    updated_at_ms=tag.updated_at_ms,
                )
            )
            return CanonicalTagCreateResult(status="created", tag=tag)

        try:
            return run_in_transaction(self._engine, operation)
        except CanonicalTagDefinitionConflictError:
            raise
        except IntegrityError as exc:
            raise FrameNestMediaMetadataRepositoryError(_REPOSITORY_FAILURE_MESSAGE) from exc
        except SQLAlchemyError as exc:
            raise FrameNestMediaMetadataRepositoryError(_REPOSITORY_FAILURE_MESSAGE) from exc

    def list_canonical_tags(self) -> tuple[CanonicalTag, ...]:
        def operation(connection: Connection) -> tuple[CanonicalTag, ...]:
            rows = connection.execute(
                select(
                    canonical_tags.c.key,
                    canonical_tags.c.display_name,
                    canonical_tags.c.created_at_ms,
                    canonical_tags.c.updated_at_ms,
                ).order_by(canonical_tags.c.display_name, canonical_tags.c.key)
            ).mappings()
            return tuple(_tag_from_row(row) for row in rows)

        try:
            return run_in_transaction(self._engine, operation)
        except FrameNestMediaMetadataRepositoryError:
            raise
        except SQLAlchemyError as exc:
            raise FrameNestMediaMetadataRepositoryError(_REPOSITORY_FAILURE_MESSAGE) from exc

    def get_canonical_tag(self, key: CanonicalTagKey) -> CanonicalTag | None:
        def operation(connection: Connection) -> CanonicalTag | None:
            return _get_tag(connection, key)

        try:
            return run_in_transaction(self._engine, operation)
        except FrameNestMediaMetadataRepositoryError:
            raise
        except SQLAlchemyError as exc:
            raise FrameNestMediaMetadataRepositoryError(_REPOSITORY_FAILURE_MESSAGE) from exc

    def get_media_metadata(self, media_id: MediaId) -> MediaMetadataSnapshot:
        def operation(connection: Connection) -> MediaMetadataSnapshot:
            if not _media_exists(connection, media_id):
                raise MediaMetadataMediaNotFoundError()
            return _load_metadata_snapshot(connection, media_id)

        try:
            return run_in_transaction(self._engine, operation)
        except MediaMetadataMediaNotFoundError:
            raise
        except FrameNestMediaMetadataRepositoryError:
            raise
        except SQLAlchemyError as exc:
            raise FrameNestMediaMetadataRepositoryError(_REPOSITORY_FAILURE_MESSAGE) from exc

    def save_media_metadata(
        self,
        media_id: MediaId,
        display_title: MediaDisplayTitle | None,
        tag_keys: tuple[CanonicalTagKey, ...],
        now_ms: int,
    ) -> MediaMetadataSaveResult:
        if len(tag_keys) > 32 or len(set(tag_keys)) != len(tag_keys):
            raise ValueError(_REPOSITORY_FAILURE_MESSAGE)

        def operation(connection: Connection) -> MediaMetadataSaveResult:
            if not _media_exists(connection, media_id):
                raise MediaMetadataMediaNotFoundError()
            for key in tag_keys:
                if _get_tag(connection, key) is None:
                    raise CanonicalTagNotFoundError()
            current = _load_metadata_snapshot(connection, media_id)
            if (
                current.persisted
                and current.display_title == display_title
                and current.tag_keys == tag_keys
            ):
                return MediaMetadataSaveResult(status="unchanged", metadata=current)

            if current.persisted:
                created_at_ms = current.created_at_ms
                assert created_at_ms is not None
                connection.execute(
                    update(media_metadata)
                    .where(media_metadata.c.media_id == media_id.to_string())
                    .values(
                        display_title=None if display_title is None else display_title.value,
                        updated_at_ms=now_ms,
                    )
                )
                status = "updated"
            else:
                created_at_ms = now_ms
                connection.execute(
                    insert(media_metadata).values(
                        media_id=media_id.to_string(),
                        display_title=None if display_title is None else display_title.value,
                        created_at_ms=now_ms,
                        updated_at_ms=now_ms,
                    )
                )
                status = "created"
            connection.execute(
                delete(media_canonical_tags).where(
                    media_canonical_tags.c.media_id == media_id.to_string()
                )
            )
            _insert_assignments(connection, media_id, tag_keys)
            snapshot = MediaMetadataSnapshot(
                media_id=media_id,
                persisted=True,
                display_title=display_title,
                tag_keys=tag_keys,
                created_at_ms=created_at_ms,
                updated_at_ms=now_ms,
            )
            return MediaMetadataSaveResult(status=status, metadata=snapshot)

        try:
            return run_in_transaction(self._engine, operation)
        except (
            CanonicalTagNotFoundError,
            MediaMetadataMediaNotFoundError,
            FrameNestMediaMetadataRepositoryError,
        ):
            raise
        except IntegrityError as exc:
            raise FrameNestMediaMetadataRepositoryError(_REPOSITORY_FAILURE_MESSAGE) from exc
        except SQLAlchemyError as exc:
            raise FrameNestMediaMetadataRepositoryError(_REPOSITORY_FAILURE_MESSAGE) from exc


def _media_exists(connection: Connection, media_id: MediaId) -> bool:
    return (
        connection.execute(
            select(logical_media.c.id).where(logical_media.c.id == media_id.to_string())
        ).first()
        is not None
    )


def _get_tag(connection: Connection, key: CanonicalTagKey) -> CanonicalTag | None:
    row = (
        connection.execute(
            select(
                canonical_tags.c.key,
                canonical_tags.c.display_name,
                canonical_tags.c.created_at_ms,
                canonical_tags.c.updated_at_ms,
            ).where(canonical_tags.c.key == key.value)
        )
        .mappings()
        .first()
    )
    if row is None:
        return None
    return _tag_from_row(row)


def _load_metadata_snapshot(connection: Connection, media_id: MediaId) -> MediaMetadataSnapshot:
    metadata_row = (
        connection.execute(
            select(
                media_metadata.c.media_id,
                media_metadata.c.display_title,
                media_metadata.c.created_at_ms,
                media_metadata.c.updated_at_ms,
            ).where(media_metadata.c.media_id == media_id.to_string())
        )
        .mappings()
        .first()
    )
    if metadata_row is None:
        return MediaMetadataSnapshot(
            media_id=media_id,
            persisted=False,
            display_title=None,
            tag_keys=(),
            created_at_ms=None,
            updated_at_ms=None,
        )
    assignment_rows = connection.execute(
        select(media_canonical_tags.c.tag_key)
        .where(media_canonical_tags.c.media_id == media_id.to_string())
        .order_by(media_canonical_tags.c.position)
    ).mappings()
    try:
        mapping = dict(metadata_row)
        title = mapping["display_title"]
        if title is not None and not isinstance(title, str):
            raise FrameNestMediaMetadataRepositoryError(_REPOSITORY_FAILURE_MESSAGE)
        return MediaMetadataSnapshot(
            media_id=MediaId.from_string(mapping["media_id"]),
            persisted=True,
            display_title=None if title is None else MediaDisplayTitle(title),
            tag_keys=tuple(CanonicalTagKey(dict(row)["tag_key"]) for row in assignment_rows),
            created_at_ms=mapping["created_at_ms"],
            updated_at_ms=mapping["updated_at_ms"],
        )
    except (
        FrameNestIdentityError,
        FrameNestMediaMetadataError,
        KeyError,
        TypeError,
        ValueError,
    ) as exc:
        raise FrameNestMediaMetadataRepositoryError(_REPOSITORY_FAILURE_MESSAGE) from exc


def _insert_assignments(
    connection: Connection,
    media_id: MediaId,
    tag_keys: tuple[CanonicalTagKey, ...],
) -> None:
    for position, key in enumerate(tag_keys):
        connection.execute(
            insert(media_canonical_tags).values(
                media_id=media_id.to_string(),
                tag_key=key.value,
                position=position,
            )
        )


def _tag_from_row(row: object) -> CanonicalTag:
    try:
        mapping = dict(row)  # type: ignore[arg-type]
        return CanonicalTag(
            key=CanonicalTagKey(mapping["key"]),
            display_name=CanonicalTagDisplayName(mapping["display_name"]),
            created_at_ms=mapping["created_at_ms"],
            updated_at_ms=mapping["updated_at_ms"],
        )
    except (
        FrameNestMediaMetadataError,
        KeyError,
        TypeError,
        ValueError,
    ) as exc:
        raise FrameNestMediaMetadataRepositoryError(_REPOSITORY_FAILURE_MESSAGE) from exc
