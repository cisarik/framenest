"""Unit evidence for ContentAudiencePolicy requester-private extension."""

from __future__ import annotations

from framenest.application.content_publication import ContentAudiencePolicy
from framenest.domain.identities import MediaId
from framenest.domain.identity_access import (
    CAPABILITIES_BY_ROLE,
    IdentityContext,
    ROLE_ADMIN,
    ROLE_USER,
)


MEDIA_ID = MediaId.from_string("11111111-1111-4111-8111-111111111111")


class _PublicationRepo:
    def __init__(self, *, exists: bool = True, published: bool = False) -> None:
        self.exists = exists
        self.published = published
        self.media_exists_calls = 0
        self.is_published_calls = 0

    def media_exists(self, media_id: MediaId) -> bool:
        self.media_exists_calls += 1
        return self.exists

    def is_published(self, media_id: MediaId) -> bool:
        self.is_published_calls += 1
        return self.published


class _RequesterAccess:
    def __init__(self, allowed: set[tuple[str, str]]) -> None:
        self.allowed = allowed
        self.calls: list[tuple[str, str]] = []

    def has_live_requester_media_access(self, *, media_id: MediaId, login_key: str) -> bool:
        key = (media_id.to_string(), login_key)
        self.calls.append(key)
        return key in self.allowed


def _identity(role: str, login_key: str) -> IdentityContext:
    return IdentityContext(
        login=login_key,
        login_key=login_key,
        display_name=login_key,
        role=role,
        capabilities=CAPABILITIES_BY_ROLE[role],
        provenance="tailscale-serve",
    )


def test_decision_order_workflow_published_then_requester() -> None:
    repo = _PublicationRepo(exists=True, published=False)
    access = _RequesterAccess({(MEDIA_ID.to_string(), "owner@example.com")})
    policy = ContentAudiencePolicy(repo, youtube_requester_private_access=access)

    assert policy.may_read(MEDIA_ID, _identity(ROLE_ADMIN, "admin@example.com")) is True
    assert repo.media_exists_calls == 1
    assert access.calls == []

    repo = _PublicationRepo(exists=True, published=True)
    access = _RequesterAccess(set())
    policy = ContentAudiencePolicy(repo, youtube_requester_private_access=access)
    assert policy.may_read(MEDIA_ID, _identity(ROLE_USER, "other@example.com")) is True
    assert access.calls == []

    repo = _PublicationRepo(exists=True, published=False)
    access = _RequesterAccess({(MEDIA_ID.to_string(), "owner@example.com")})
    policy = ContentAudiencePolicy(repo, youtube_requester_private_access=access)
    assert policy.may_read(MEDIA_ID, _identity(ROLE_USER, "owner@example.com")) is True
    assert policy.may_read(MEDIA_ID, _identity(ROLE_USER, "foreign@example.com")) is False
