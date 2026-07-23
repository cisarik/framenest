"""Application port for durable YouTube manual-acquisition claims."""

from __future__ import annotations

from typing import Protocol

from framenest.domain.identities import YouTubeAcquisitionClaimId
from framenest.domain.youtube_acquisition import (
    YouTubeAcquisitionClaim,
    YouTubeAcquisitionState,
)
from framenest.domain.uploads import UploadSessionId


class FrameNestYouTubeClaimRepositoryError(RuntimeError):
    """Sanitized base error for durable claim persistence."""


class YouTubeClaimAlreadyExistsError(FrameNestYouTubeClaimRepositoryError):
    """Raised when a claim UUID already exists."""


class YouTubeClaimNotFoundError(FrameNestYouTubeClaimRepositoryError):
    """Raised when a claim does not exist."""


class YouTubeClaimConcurrencyConflictError(FrameNestYouTubeClaimRepositoryError):
    """Raised when an optimistic state/version guard is stale."""


class YouTubeClaimSourceIdentityConflictError(FrameNestYouTubeClaimRepositoryError):
    """Raised when another active claim owns the source identity."""


class YouTubeAcquisitionClaimRepository(Protocol):
    """Persistence-independent durable YouTube claim contract."""

    def create_or_get_active(
        self,
        claim: YouTubeAcquisitionClaim,
    ) -> tuple[YouTubeAcquisitionClaim, bool]:
        """Create a claim or return the transactionally selected active winner."""

    def create(self, claim: YouTubeAcquisitionClaim) -> None:
        """Persist one new claim, rejecting identity conflicts."""

    def get(
        self,
        claim_id: YouTubeAcquisitionClaimId,
    ) -> YouTubeAcquisitionClaim | None:
        """Return one claim by identity, or None."""

    def find_active_by_source_identity(
        self,
        *,
        extractor_key: str,
        youtube_video_id: str,
    ) -> YouTubeAcquisitionClaim | None:
        """Return the single active source-identity owner, if present."""

    def find_latest_cataloged_by_source_identity(
        self,
        *,
        extractor_key: str,
        youtube_video_id: str,
    ) -> YouTubeAcquisitionClaim | None:
        """Return the newest successful source claim available for reuse."""

    def find_by_upload_id(
        self,
        upload_id: UploadSessionId,
    ) -> YouTubeAcquisitionClaim | None:
        """Return the unique claim linked to an upload session, if present."""

    def list_recovery_candidates(
        self,
        *,
        limit: int,
        after_updated_at_ms: int | None = None,
        after_id: str | None = None,
    ) -> tuple[YouTubeAcquisitionClaim, ...]:
        """Return active claims in deterministic recovery order."""

    def list_cleanup_candidates(
        self,
        *,
        limit: int,
    ) -> tuple[YouTubeAcquisitionClaim, ...]:
        """Return terminal claims whose exact staging cleanup remains pending."""

    def save(
        self,
        claim: YouTubeAcquisitionClaim,
        *,
        expected_state: YouTubeAcquisitionState,
        expected_version: int,
    ) -> YouTubeAcquisitionClaim:
        """Persist one already-domain-validated optimistic snapshot idempotently."""
