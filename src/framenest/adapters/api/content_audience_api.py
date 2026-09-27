"""Shared application-level audience gate for direct media API surfaces."""

from __future__ import annotations

from fastapi import Request

from framenest.application.content_publication import ContentAudiencePolicy
from framenest.application.ports.content_publication_repository import (
    FrameNestContentPublicationRepositoryError,
)
from framenest.domain.identities import MediaId
from framenest.domain.identity_access import IdentityContext
from framenest.domain.record_access import READ_DENY
from framenest.adapters.api.tailscale_ingress import SCOPE_IDENTITY


class ContentAudienceUnavailableError(RuntimeError):
    """Raised when the durable audience decision cannot be established."""


def content_audience_decision(
    *,
    request: Request,
    media_id: MediaId,
    policy: ContentAudiencePolicy | None,
) -> str:
    """Return deny, current, approved, or legacy. Missing policy or identity denies."""
    if policy is None:
        return READ_DENY
    identity = request.scope.get(SCOPE_IDENTITY)
    if not isinstance(identity, IdentityContext) or not identity.login_key:
        return READ_DENY
    try:
        decider = getattr(policy, "read_decision", None)
        if decider is None:
            return "current" if policy.may_read(media_id, identity) else READ_DENY
        decision = decider(media_id, identity)
    except FrameNestContentPublicationRepositoryError as exc:
        raise ContentAudienceUnavailableError() from exc
    except Exception as exc:
        raise ContentAudienceUnavailableError() from exc
    if decision not in {"deny", "current", "approved", "legacy"}:
        return READ_DENY
    return str(decision)


def content_audience_allows(
    *,
    request: Request,
    media_id: MediaId,
    policy: ContentAudiencePolicy | None,
) -> bool:
    """Return whether the caller may read the media item at all."""
    return (
        content_audience_decision(
            request=request,
            media_id=media_id,
            policy=policy,
        )
        != READ_DENY
    )
