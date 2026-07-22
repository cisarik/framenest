"""Application port for the searchable media catalog read model."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from framenest.domain.media_metadata import CanonicalTagKey, MediaCollectionKey


class FrameNestMediaCatalogRepositoryError(RuntimeError):
    """Sanitized error raised when media catalog reads fail."""


@dataclass(frozen=True, slots=True)
class MediaCatalogQuery:
    """Normalized catalog query parameters."""

    q: str | None
    tag_keys: tuple[CanonicalTagKey, ...]
    limit: int
    offset: int
    collection_key: MediaCollectionKey | None
    content_category: str | None = None
    acquisition_source: str | None = None


@dataclass(frozen=True, slots=True)
class CatalogMediaTag:
    """Ordered canonical tag attached to one catalog media item."""

    key: str
    display_name: str
    position: int


@dataclass(frozen=True, slots=True)
class CatalogMediaLocation:
    """Catalog-safe physical location read model."""

    location_id: str
    library_id: str
    relative_path: str
    availability: str
    observed_size_bytes: int | None
    observed_mtime_ns: int | None


@dataclass(frozen=True, slots=True)
class CatalogMediaItem:
    """One logical media item for catalog browsing."""

    media_id: str
    media_kind: str
    created_at_ms: int
    updated_at_ms: int
    display_title: str | None
    collection_key: str | None
    processed_at_ms: int | None
    tags: tuple[CatalogMediaTag, ...]
    locations: tuple[CatalogMediaLocation, ...]
    content_category: str = "general"
    acquisition_source: str = "unknown"


@dataclass(frozen=True, slots=True)
class MediaCatalogPage:
    """Bounded catalog page with total filtered count."""

    items: tuple[CatalogMediaItem, ...]
    total: int
    limit: int
    offset: int
    q: str | None
    tag_keys: tuple[CanonicalTagKey, ...]
    content_category: str | None = None
    acquisition_source: str | None = None


class MediaCatalogRepository(Protocol):
    """Persistence-independent searchable catalog read contract."""

    def list_media(self, query: MediaCatalogQuery) -> MediaCatalogPage:
        """Return one deterministic page of catalog media."""
