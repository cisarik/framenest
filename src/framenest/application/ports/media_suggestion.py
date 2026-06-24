"""Application port for provider-neutral media suggestion generation."""

from __future__ import annotations

from typing import Protocol

from framenest.application.media_suggestion import MediaSuggestion, MediaSuggestionRequest


class MediaSuggestionProvider(Protocol):
    """Infrastructure-independent suggestion contract."""

    def suggest(self, request: MediaSuggestionRequest) -> MediaSuggestion:
        """Return one validated suggestion preview for a prepared request."""
