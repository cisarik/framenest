"""Application services for durable analysis proposals.

These use-cases never call a provider, enqueue analysis, or read the automatic
analysis flag. Duplicate proposals for the same medium are allowed: each POST
creates its own row.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import uuid

from framenest.application.ports.analysis_proposal import (
    ANALYSIS_PROPOSAL_STATUS_OPEN,
    AdminAnalysisProposalPage,
    AnalysisProposal,
    AnalysisProposalMediaNotFoundError,
    AnalysisProposalRepository,
    FrameNestAnalysisProposalRepositoryError,
)
from framenest.application.upload_transport import default_now_ms
from framenest.domain.identities import MediaId
from framenest.domain import FrameNestIdentityError

DEFAULT_ANALYSIS_PROPOSAL_LIMIT = 24
MAX_ANALYSIS_PROPOSAL_LIMIT = 100


class AnalysisProposalValidationError(ValueError):
    """Raised for invalid proposal list input."""


def _new_proposal_id() -> str:
    return str(uuid.uuid4())


@dataclass(frozen=True, slots=True)
class ProposeAnalysis:
    """Create one durable administrator-visible analysis proposal."""

    repository: AnalysisProposalRepository
    now_ms: Callable[[], int] = default_now_ms
    new_id: Callable[[], str] = _new_proposal_id

    def execute(self, *, media_id: str, login_key: str) -> AnalysisProposal:
        if not isinstance(login_key, str) or not login_key.strip():
            raise AnalysisProposalValidationError()
        try:
            parsed_media_id = MediaId.from_string(media_id)
        except FrameNestIdentityError as exc:
            raise AnalysisProposalMediaNotFoundError() from exc
        return self.repository.create_proposal(
            proposal_id=self.new_id(),
            media_id=parsed_media_id,
            login_key=login_key,
            created_at_ms=self.now_ms(),
            status=ANALYSIS_PROPOSAL_STATUS_OPEN,
        )


@dataclass(frozen=True, slots=True)
class ListAnalysisProposals:
    """Normalize and execute the administrator open-proposal query."""

    repository: AnalysisProposalRepository

    def execute(
        self,
        *,
        limit: int = DEFAULT_ANALYSIS_PROPOSAL_LIMIT,
        offset: int = 0,
    ) -> AdminAnalysisProposalPage:
        bounded_limit = _bounded_int(
            limit,
            minimum=1,
            maximum=MAX_ANALYSIS_PROPOSAL_LIMIT,
        )
        bounded_offset = _bounded_int(offset, minimum=0, maximum=None)
        try:
            return self.repository.list_open_proposals(
                limit=bounded_limit,
                offset=bounded_offset,
            )
        except FrameNestAnalysisProposalRepositoryError:
            raise


def _bounded_int(value: int, *, minimum: int, maximum: int | None) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise AnalysisProposalValidationError()
    if maximum is not None and value > maximum:
        raise AnalysisProposalValidationError()
    return value
