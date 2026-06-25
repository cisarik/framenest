"""Application port for persistent media metadata and canonical tags."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Protocol

from framenest.domain import MediaId
from framenest.domain.media_metadata import (
    CanonicalTag,
    CanonicalTagDisplayName,
    CanonicalTagKey,
    MediaDisplayTitle,
)


class CanonicalTagDefinitionConflictError(RuntimeError):
    """Raised when an existing tag key has a different display name."""


class CanonicalTagNotFoundError(RuntimeError):
    """Raised when metadata references an absent canonical tag."""


class MediaMetadataMediaNotFoundError(RuntimeError):
    """Raised when a logical media item is absent."""


class FrameNestMediaMetadataRepositoryError(RuntimeError):
    """Sanitized error raised when media metadata persistence fails."""


@dataclass(frozen=True, slots=True)
class CanonicalTagCreateResult:
    """Result from creating a canonical tag definition."""

    status: Literal["created", "already_exists"]
    tag: CanonicalTag


@dataclass(frozen=True, slots=True)
class MediaMetadataSnapshot:
    """Application-facing metadata state for one media item."""

    media_id: MediaId
    persisted: bool
    display_title: MediaDisplayTitle | None
    tag_keys: tuple[CanonicalTagKey, ...]
    created_at_ms: int | None
    updated_at_ms: int | None


@dataclass(frozen=True, slots=True)
class MediaMetadataSaveResult:
    """Result from saving metadata for one media item."""

    status: Literal["created", "updated", "unchanged"]
    metadata: MediaMetadataSnapshot


class MediaMetadataRepository(Protocol):
    """Persistence-independent media metadata contract."""

    def create_canonical_tag(
        self,
        key: CanonicalTagKey,
        display_name: CanonicalTagDisplayName,
        now_ms: int,
    ) -> CanonicalTagCreateResult:
        """Create one tag definition idempotently."""

    def list_canonical_tags(self) -> tuple[CanonicalTag, ...]:
        """Return canonical tags in deterministic order."""

    def get_canonical_tag(self, key: CanonicalTagKey) -> CanonicalTag | None:
        """Return one canonical tag definition, or None."""

    def get_media_metadata(self, media_id: MediaId) -> MediaMetadataSnapshot:
        """Return persisted or empty metadata for an existing media item."""

    def save_media_metadata(
        self,
        media_id: MediaId,
        display_title: MediaDisplayTitle | None,
        tag_keys: tuple[CanonicalTagKey, ...],
        now_ms: int,
    ) -> MediaMetadataSaveResult:
        """Persist a complete metadata replacement atomically."""
