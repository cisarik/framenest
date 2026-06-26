"""Application query boundary for searchable media catalog browsing."""

from __future__ import annotations

from dataclasses import dataclass
import unicodedata

from framenest.application.ports.media_catalog_repository import (
    MediaCatalogPage,
    MediaCatalogQuery,
    MediaCatalogRepository,
)
from framenest.domain.media_metadata import (
    CanonicalTagKey,
    FrameNestMediaMetadataError,
    MediaCollectionKey,
)

MEDIA_CATALOG_QUERY_INVALID_MESSAGE = "Invalid media catalog query."
MAX_MEDIA_CATALOG_QUERY_CODE_POINTS = 240
DEFAULT_MEDIA_CATALOG_LIMIT = 24
MAX_MEDIA_CATALOG_LIMIT = 100


class MediaCatalogValidationError(ValueError):
    """Raised when catalog query input is invalid."""


@dataclass(frozen=True, slots=True)
class ListMediaCatalog:
    """List persisted logical media through a normalized read query."""

    repository: MediaCatalogRepository

    def execute(
        self,
        *,
        q: str | None = None,
        tag_keys: list[str] | tuple[str, ...] | None = None,
        limit: int = DEFAULT_MEDIA_CATALOG_LIMIT,
        offset: int = 0,
        collection_key: MediaCollectionKey | None = None,
    ) -> MediaCatalogPage:
        query = MediaCatalogQuery(
            q=_normalize_title_query(q),
            tag_keys=_normalize_tag_keys(tag_keys or []),
            limit=_validate_limit(limit),
            offset=_validate_offset(offset),
            collection_key=collection_key,
        )
        return self.repository.list_media(query)


def _normalize_title_query(value: str | None) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise MediaCatalogValidationError(MEDIA_CATALOG_QUERY_INVALID_MESSAGE)
    normalized = value.strip()
    if not normalized:
        return None
    if len(normalized) > MAX_MEDIA_CATALOG_QUERY_CODE_POINTS or _has_control_character(normalized):
        raise MediaCatalogValidationError(MEDIA_CATALOG_QUERY_INVALID_MESSAGE)
    return normalized


def _normalize_tag_keys(values: list[str] | tuple[str, ...]) -> tuple[CanonicalTagKey, ...]:
    normalized: list[CanonicalTagKey] = []
    seen: set[CanonicalTagKey] = set()
    try:
        for value in values:
            key = CanonicalTagKey(value)
            if key not in seen:
                seen.add(key)
                normalized.append(key)
    except FrameNestMediaMetadataError as exc:
        raise MediaCatalogValidationError(MEDIA_CATALOG_QUERY_INVALID_MESSAGE) from exc
    return tuple(normalized)


def _validate_limit(value: int) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or value < 1
        or value > MAX_MEDIA_CATALOG_LIMIT
    ):
        raise MediaCatalogValidationError(MEDIA_CATALOG_QUERY_INVALID_MESSAGE)
    return value


def _validate_offset(value: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise MediaCatalogValidationError(MEDIA_CATALOG_QUERY_INVALID_MESSAGE)
    return value


def _has_control_character(value: str) -> bool:
    return any(unicodedata.category(character) == "Cc" for character in value)
