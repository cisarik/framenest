"""Route-policy and requester-private audience tests for the X candidate."""

from __future__ import annotations

import pytest

from framenest.adapters.api.tailscale_ingress import find_route_policy
from framenest.application.content_publication import ContentAudiencePolicy
from framenest.domain.identity_access import (
    CAPABILITY_X_ACQUIRE,
    CAPABILITY_X_REQUEST,
    IdentityContext,
    ROLE_ADMIN,
    ROLE_USER,
    CAPABILITIES_BY_ROLE,
)


def _identity(login: str, role: str) -> IdentityContext:
    return IdentityContext(
        login=login,
        login_key=login,
        display_name=login,
        role=role,
        capabilities=CAPABILITIES_BY_ROLE[role],
        provenance="tailscale-serve",
    )


def test_x_request_routes_require_x_request_capability() -> None:
    for method, path in [
        ("POST", "/api/x/requests"),
        ("GET", "/api/x/requests"),
        ("GET", "/api/x/requests/00000000-0000-4000-8000-000000000000"),
        ("POST", "/api/x/requests/00000000-0000-4000-8000-000000000000/retry"),
        ("GET", "/api/x/companion/media"),
    ]:
        policy, match = find_route_policy(method, path)
        assert match is not None
        assert policy.capability == CAPABILITY_X_REQUEST


def test_only_x_request_mutations_are_companion_flagged() -> None:
    submit, submit_match = find_route_policy("POST", "/api/x/requests")
    retry, retry_match = find_route_policy(
        "POST", "/api/x/requests/00000000-0000-4000-8000-000000000000/retry"
    )
    picker, picker_match = find_route_policy("GET", "/api/x/companion/media")
    tags, tags_match = find_route_policy("POST", "/api/canonical-tags")
    assert submit_match is not None and submit.companion_mutation is True
    assert retry_match is not None and retry.companion_mutation is True
    assert picker_match is not None and picker.companion_mutation is False
    assert tags_match is not None and tags.companion_mutation is False


def test_x_admin_route_requires_x_acquire_capability() -> None:
    policy, _match = find_route_policy(
        "GET", "/api/admin/x/requests/00000000-0000-4000-8000-000000000000"
    )
    assert policy is not None
    assert policy.capability == CAPABILITY_X_ACQUIRE


def test_roles_carry_x_capabilities() -> None:
    assert CAPABILITY_X_REQUEST in _identity("user", ROLE_USER).capabilities
    assert CAPABILITY_X_REQUEST in _identity("admin", ROLE_ADMIN).capabilities
    assert CAPABILITY_X_ACQUIRE not in _identity("user", ROLE_USER).capabilities
    assert CAPABILITY_X_ACQUIRE in _identity("admin", ROLE_ADMIN).capabilities


class _Repo:
    def __init__(self, outcome: bool = False) -> None:
        self._outcome = outcome

    def media_exists(self, media_id: object) -> bool:
        return False

    def is_published(self, media_id: object) -> bool:
        return False

    def has_live_requester_media_access(
        self, *, media_id: object, login_key: str
    ) -> bool:
        return self._outcome


def test_requester_can_read_own_private_media() -> None:
    from framenest.domain.identities import MediaId

    policy = ContentAudiencePolicy(
        _Repo(outcome=True), x_requester_private_access=_Repo(outcome=True)
    )
    identity = _identity("alice", ROLE_USER)
    assert policy.may_read(MediaId.new(), identity)


def test_foreign_requester_cannot_read_private_media() -> None:
    from framenest.domain.identities import MediaId

    policy = ContentAudiencePolicy(
        _Repo(outcome=False), x_requester_private_access=_Repo(outcome=False)
    )
    assert not policy.may_read(MediaId.new(), _identity("alice", ROLE_USER))
