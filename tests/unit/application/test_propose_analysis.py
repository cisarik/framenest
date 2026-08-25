"""Unit evidence for analysis-proposal use-case bounds."""

from __future__ import annotations

import pytest

from framenest.application.analysis_proposal import (
    ListAnalysisProposals,
    ProposeAnalysis,
    AnalysisProposalValidationError,
)
from framenest.application.ports.analysis_proposal import (
    AdminAnalysisProposalPage,
    AnalysisProposal,
    AnalysisProposalMediaNotFoundError,
)
from framenest.domain.identities import MediaId

MEDIA_A = "11111111-1111-4111-8111-111111111111"


class _Repo:
    def __init__(self) -> None:
        self.created: list[dict[str, object]] = []

    def create_proposal(self, **kwargs: object) -> AnalysisProposal:
        self.created.append(kwargs)
        media_id = kwargs["media_id"]
        assert isinstance(media_id, MediaId)
        created_at_ms = kwargs["created_at_ms"]
        assert isinstance(created_at_ms, int)
        return AnalysisProposal(
            proposal_id=str(kwargs["proposal_id"]),
            media_id=media_id.to_string(),
            proposed_by_login_key=str(kwargs["login_key"]),
            created_at_ms=created_at_ms,
            status=str(kwargs["status"]),
        )

    def list_open_proposals(self, *, limit: int, offset: int) -> AdminAnalysisProposalPage:
        return AdminAnalysisProposalPage(items=(), total=0, limit=limit, offset=offset)


def test_propose_rejects_empty_login_and_unknown_identity_shape() -> None:
    repo = _Repo()
    service = ProposeAnalysis(repo, now_ms=lambda: 42, new_id=lambda: "id-1")
    with pytest.raises(AnalysisProposalValidationError):
        service.execute(media_id=MEDIA_A, login_key="")
    with pytest.raises(AnalysisProposalMediaNotFoundError):
        service.execute(media_id="not-a-uuid", login_key="alice@example.com")
    created = service.execute(media_id=MEDIA_A, login_key="alice@example.com")
    assert created.created_at_ms == 42
    assert created.proposal_id == "id-1"
    assert created.status == "open"
    assert len(repo.created) == 1


def test_list_rejects_invalid_bounds() -> None:
    service = ListAnalysisProposals(_Repo())
    with pytest.raises(AnalysisProposalValidationError):
        service.execute(limit=0)
    with pytest.raises(AnalysisProposalValidationError):
        service.execute(offset=-1)
    page = service.execute()
    assert page.limit == 24
    assert page.total == 0
