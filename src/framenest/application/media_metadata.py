"""Application use cases for persistent media metadata and canonical tags."""

from __future__ import annotations

from dataclasses import dataclass
import time
from typing import Literal, Protocol

from framenest.application.ports.media_metadata_repository import (
    CanonicalTagCreateResult,
    CanonicalTagNotFoundError,
    MediaMetadataRepository,
    MediaMetadataSaveResult,
    MediaMetadataSnapshot,
)
from framenest.domain import MediaId
from framenest.domain.media_metadata import (
    CanonicalTag,
    CanonicalTagDisplayName,
    CanonicalTagKey,
    MediaDescription,
    MediaDisplayTitle,
)

MEDIA_METADATA_OPERATION_FAILED_MESSAGE = "Media metadata operation failed."


class ClockMs(Protocol):
    """Callable source of non-negative millisecond timestamps."""

    def __call__(self) -> int:
        """Return current timestamp in milliseconds."""


@dataclass(frozen=True, slots=True)
class CanonicalTagListResult:
    """Deterministic canonical tag list."""

    tags: tuple[CanonicalTag, ...]


@dataclass(frozen=True, slots=True)
class MediaMetadataView:
    """Application-facing complete metadata view."""

    persisted: bool
    display_title: str | None
    description: str | None
    tags: tuple[CanonicalTag, ...]
    created_at_ms: int | None
    updated_at_ms: int | None


@dataclass(frozen=True, slots=True)
class SaveMediaMetadataResult:
    """Application save result with complete metadata view."""

    status: Literal["created", "updated", "unchanged"]
    metadata: MediaMetadataView


class CreateCanonicalTag:
    """Create one canonical tag definition idempotently."""

    def __init__(
        self,
        repository: MediaMetadataRepository,
        *,
        clock_ms: ClockMs | None = None,
    ) -> None:
        self._repository = repository
        self._clock_ms = clock_ms if clock_ms is not None else _utc_now_ms

    def execute(self, key: str, display_name: str) -> CanonicalTagCreateResult:
        return self._repository.create_canonical_tag(
            CanonicalTagKey(key),
            CanonicalTagDisplayName(display_name),
            _call_clock_ms(self._clock_ms),
        )


class ListCanonicalTags:
    """List all canonical tag definitions deterministically."""

    def __init__(self, repository: MediaMetadataRepository) -> None:
        self._repository = repository

    def execute(self) -> CanonicalTagListResult:
        return CanonicalTagListResult(tags=self._repository.list_canonical_tags())


class GetMediaMetadata:
    """Load complete metadata view for one logical media item."""

    def __init__(self, repository: MediaMetadataRepository) -> None:
        self._repository = repository

    def execute(self, media_id: str) -> MediaMetadataView:
        snapshot = self._repository.get_media_metadata(MediaId.from_string(media_id))
        return _view_from_snapshot(self._repository, snapshot)


class SaveMediaMetadata:
    """Persist one complete metadata replacement."""

    def __init__(
        self,
        repository: MediaMetadataRepository,
        *,
        clock_ms: ClockMs | None = None,
    ) -> None:
        self._repository = repository
        self._clock_ms = clock_ms if clock_ms is not None else _utc_now_ms

    def execute(
        self,
        media_id: str,
        display_title: str | None,
        description: str | None,
        tag_keys: list[str],
    ) -> SaveMediaMetadataResult:
        parsed_keys = tuple(CanonicalTagKey(key) for key in tag_keys)
        if len(parsed_keys) != len(set(parsed_keys)):
            raise ValueError(MEDIA_METADATA_OPERATION_FAILED_MESSAGE)
        parsed_title = None if display_title is None else MediaDisplayTitle(display_title)
        parsed_description = _normalize_description(description)
        result = self._repository.save_media_metadata(
            MediaId.from_string(media_id),
            parsed_title,
            parsed_description,
            parsed_keys,
            _call_clock_ms(self._clock_ms),
        )
        return SaveMediaMetadataResult(
            status=result.status,
            metadata=_view_from_snapshot(self._repository, result.metadata),
        )


def _normalize_description(value: str | None) -> MediaDescription | None:
    if value is None:
        return None
    stripped = value.strip()
    if not stripped:
        return None
    return MediaDescription(value)


def _view_from_snapshot(
    repository: MediaMetadataRepository,
    snapshot: MediaMetadataSnapshot,
) -> MediaMetadataView:
    tags: list[CanonicalTag] = []
    for key in snapshot.tag_keys:
        tag = repository.get_canonical_tag(key)
        if tag is None:
            raise CanonicalTagNotFoundError()
        tags.append(tag)
    return MediaMetadataView(
        persisted=snapshot.persisted,
        display_title=None if snapshot.display_title is None else snapshot.display_title.value,
        description=None if snapshot.description is None else snapshot.description.value,
        tags=tuple(tags),
        created_at_ms=snapshot.created_at_ms,
        updated_at_ms=snapshot.updated_at_ms,
    )


def _utc_now_ms() -> int:
    return time.time_ns() // 1_000_000


def _call_clock_ms(clock_ms: ClockMs) -> int:
    value = clock_ms()
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(MEDIA_METADATA_OPERATION_FAILED_MESSAGE)
    return value
