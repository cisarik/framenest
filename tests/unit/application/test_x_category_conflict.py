"""Focused create-race and mixed-catalog category conflict tests."""

from __future__ import annotations

import types

import pytest
from sqlalchemy import create_engine, text

from framenest.application.x_acquisition import (
    XAcquisitionCategoryConflictError,
    XAcquisitionRequestService,
    XRequestLimits,
)
from framenest.domain.identities import MediaId
from framenest.domain.media_classification import ContentCategory
from framenest.domain.x_acquisition import XAssetState, XPostClaim
from framenest.infrastructure.persistence.catalog_schema import metadata
from framenest.infrastructure.persistence.x_acquisition_claim_repository import (
    SqliteXAcquisitionClaimRepository,
)

URL = "https://x.com/author/status/987654321"


class _RaceRepository:
    def __init__(self, inner: SqliteXAcquisitionClaimRepository, winner: XPostClaim) -> None:
        self._inner = inner
        self._winner = winner

    def find_owned_successful_by_post_id(self, **kwargs):
        return None

    def find_active_by_post_id(self, **kwargs):
        return None

    def create_or_get_active(self, claim: XPostClaim):
        return self._winner, False

    def count_active_for_requester(self, **kwargs):
        return 0

    def count_global_active_ordinary(self):
        return 0

    def count_submits_since(self, **kwargs):
        return 0

    def count_failed_transitions_since(self, **kwargs):
        return 0

    def __getattr__(self, name: str):
        return getattr(self._inner, name)


class _SuccessfulMixedRepository:
    def __init__(self, claim: XPostClaim, categories: dict[str, ContentCategory]) -> None:
        self._claim = claim
        self._categories = categories

    def find_owned_successful_by_post_id(self, **kwargs):
        return self._claim

    def list_assets_for_post(self, claim_id):
        assets = []
        for index, media_id in enumerate(self._categories):
            assets.append(
                types.SimpleNamespace(
                    state=XAssetState.CATALOGED,
                    media_id=MediaId.from_string(media_id),
                    ordinal=index,
                )
            )
        return tuple(assets)


class _MixedMetadata:
    def __init__(self, mapping: dict[str, ContentCategory]) -> None:
        self._mapping = mapping

    def get_media_metadata(self, media_id: MediaId):
        category = self._mapping.get(media_id.to_string())
        if category is None:
            return types.SimpleNamespace(persisted=False, content_category=None)
        return types.SimpleNamespace(persisted=True, content_category=category)


def _limits() -> XRequestLimits:
    return XRequestLimits(
        max_active_per_requester=8,
        max_global_active=8,
        max_submits_per_hour=20,
        max_failed_per_24h=20,
        free_space_bytes=lambda: 10_737_418_240,
    )


def test_create_race_compares_winner_category_before_active_reuse() -> None:
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    connection = engine.connect()
    connection.execute(text("PRAGMA foreign_keys=ON"))
    metadata.create_all(connection)
    connection.commit()
    try:
        inner = SqliteXAcquisitionClaimRepository(engine)
        winner = XPostClaim.new(
            submitted_url=URL,
            now_ms=10,
            created_by_login_key="alice",
            requested_content_category=ContentCategory.MEME,
        )
        inner.create_post(winner)
        service = XAcquisitionRequestService(
            _RaceRepository(inner, winner),
            limits=_limits(),
        )
        with pytest.raises(XAcquisitionCategoryConflictError):
            service.submit(URL, login_key="alice", content_category=ContentCategory.MOVIE)
        same = service.submit(URL, login_key="alice", content_category=ContentCategory.MEME)
        assert same.submission_result == "active_reuse"
        assert same.request_id == winner.id.to_string()
    finally:
        connection.close()


def test_mixed_live_catalog_categories_conflict() -> None:
    first = MediaId.new().to_string()
    second = MediaId.new().to_string()
    claim = XPostClaim.new(
        submitted_url=URL,
        now_ms=10,
        created_by_login_key="alice",
        requested_content_category=ContentCategory.MEME,
    )
    mapping = {
        first: ContentCategory.MEME,
        second: ContentCategory.MOVIE,
    }
    service = XAcquisitionRequestService(
        _SuccessfulMixedRepository(claim, mapping),
        limits=_limits(),
        metadata_repository=_MixedMetadata(mapping),
    )
    with pytest.raises(XAcquisitionCategoryConflictError):
        service.submit(URL, login_key="alice", content_category=ContentCategory.MEME)
    with pytest.raises(XAcquisitionCategoryConflictError):
        service.submit(URL, login_key="alice", content_category=ContentCategory.MOVIE)
