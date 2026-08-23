"""Persistence port for administrator companion review inbox reads."""

from __future__ import annotations

from typing import Protocol

from framenest.application.companion_review import (
    CompanionReviewDetail,
    CompanionReviewInboxPage,
)
from framenest.domain.identities import MediaId


class FrameNestCompanionReviewRepositoryError(RuntimeError):
    """Sanitized companion-review persistence failure."""


class CompanionReviewMediaNotFoundError(FrameNestCompanionReviewRepositoryError):
    """Raised when the target logical medium is absent."""


class CompanionReviewMovieExcludedError(FrameNestCompanionReviewRepositoryError):
    """Raised when the target medium is in the movie category."""


class CompanionReviewStoredResultError(FrameNestCompanionReviewRepositoryError):
    """Raised when a stored suggestion payload cannot be decoded."""


class CompanionReviewRepository(Protocol):
    """Read-only persistence contract for companion review inbox and history."""

    def list_inbox(
        self,
        *,
        actor_login_key: str,
        limit: int,
        cursor: tuple[int, str] | None,
    ) -> CompanionReviewInboxPage:
        """Return one keyset page of latest successful generic runs."""

    def get_detail(
        self,
        *,
        media_id: MediaId,
        actor_login_key: str,
        limit: int,
        cursor: tuple[int, str] | None,
    ) -> CompanionReviewDetail:
        """Return canonical state and one history page for one medium."""
