"""Shared application-level audience gate for direct media API surfaces."""

from __future__ import annotations

from fastapi import Request

from framenest.application.content_publication import ContentAudiencePolicy
from framenest.application.ports.content_publication_repository import (
    FrameNestContentPublicationRepositoryError,
)
from framenest.domain.identities import MediaId
from framenest.adapters.api.tailscale_ingress import SCOPE_IDENTITY


class ContentAudienceUnavailableError(RuntimeError):
    """Raised when the durable audience decision cannot be established."""


def content_audience_allows(
    *,
    request: Request,
    media_id: MediaId,
    policy: ContentAudiencePolicy | None,
) -> bool:
    """Return the shared audience decision, preserving legacy injected test seams."""
    if policy is None:
        return True
    try:
        return policy.may_read(media_id, request.scope.get(SCOPE_IDENTITY))
    except FrameNestContentPublicationRepositoryError as exc:
        raise ContentAudienceUnavailableError() from exc
    except Exception as exc:
        raise ContentAudienceUnavailableError() from exc
