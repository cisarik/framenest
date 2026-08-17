"""Application port for per-user media alias overlay persistence."""

from __future__ import annotations

from typing import Protocol

from framenest.domain.identities import MediaId
from framenest.domain.media_metadata import CanonicalTagKey
from framenest.domain.media_user_alias import MediaUserAlias, MediaUserAliasContent
from framenest.domain.x_acquisition import XPostClaimId


class FrameNestMediaUserAliasRepositoryError(RuntimeError):
    """Sanitized error raised when alias overlay persistence fails."""


class MediaUserAliasMediaNotFoundError(RuntimeError):
    """Raised when a logical media item is absent."""


class AliasTagNotFoundError(RuntimeError):
    """Raised when an alias references an absent canonical tag."""


class MediaUserAliasRepository(Protocol):
    """Persistence-independent caller-private overlay contract."""

    def get_alias(self, media_id: MediaId, login_key: str) -> MediaUserAlias | None:
        """Return the caller's overlay row, or None when absent."""

    def upsert_alias(
        self,
        media_id: MediaId,
        login_key: str,
        content: MediaUserAliasContent,
        now_ms: int,
    ) -> MediaUserAlias | None:
        """Replace the caller overlay. Empty content deletes the row and returns None."""

    def delete_alias(self, media_id: MediaId, login_key: str) -> None:
        """Delete the caller overlay and its tags if present."""

    def canonical_tag_keys_exist(self, tag_keys: tuple[CanonicalTagKey, ...]) -> bool:
        """Return True when every tag key exists in the canonical tag catalog."""
