"""Application boundary for secure read-only local media content resolution."""

from __future__ import annotations

from collections.abc import Callable, Iterator
from dataclasses import dataclass

from framenest.application.ports.library_repository import (
    LibraryRepository,
)
from framenest.application.ports.media_content import (
    MediaContentReader,
    SUPPORTED_MEDIA_CONTENT,
)
from framenest.application.ports.media_repository import (
    MediaRepository,
)
from framenest.domain import MediaId, MediaLocationId
from framenest.domain.media import MediaKind, MediaLocationAvailability, MediaRelativePath

MEDIA_NOT_FOUND_MESSAGE = "Media content was not found."
MEDIA_CONTENT_UNAVAILABLE_MESSAGE = "Media content is not available."
MEDIA_CONTENT_FAILED_MESSAGE = "Media content delivery failed."


class MediaContentNotFoundError(RuntimeError):
    """Sanitized error raised when the requested media or location is absent or mismatched."""


class MediaContentUnavailableError(RuntimeError):
    """Sanitized error raised when content cannot be safely served."""


class MediaContentFailedError(RuntimeError):
    """Sanitized error raised when an unexpected content delivery failure occurs."""


@dataclass(frozen=True, slots=True)
class ResolvedMediaContent:
    """Resolved media content ready for bounded byte streaming from a stable handle."""

    media_type: str
    byte_size: int
    stream: Callable[[int, int | None], Iterator[bytes]]
    close: Callable[[], None]


def supported_media_type(kind: MediaKind, extension: str) -> str | None:
    """Return the MIME type for a supported kind/extension pair, or None."""
    return SUPPORTED_MEDIA_CONTENT.get((kind, extension))


def _extension_for_relative_path(relative_path: MediaRelativePath) -> str:
    filename = relative_path.filename
    if "." not in filename:
        return ""
    return "." + filename.rsplit(".", 1)[-1].lower()


class ResolveMediaContent:
    """Resolve one catalog media location for secure read-only content delivery."""

    def __init__(
        self,
        media_repository: MediaRepository,
        library_repository: LibraryRepository,
        content_reader: MediaContentReader,
    ) -> None:
        self._media_repository = media_repository
        self._library_repository = library_repository
        self._content_reader = content_reader

    def execute(
        self,
        media_id: MediaId,
        location_id: MediaLocationId,
    ) -> ResolvedMediaContent:
        media = self._media_repository.get_media(media_id)
        if media is None:
            raise MediaContentNotFoundError(MEDIA_NOT_FOUND_MESSAGE)
        location = self._media_repository.get_location(location_id)
        if location is None:
            raise MediaContentNotFoundError(MEDIA_NOT_FOUND_MESSAGE)
        if location.media_id != media_id:
            raise MediaContentNotFoundError(MEDIA_NOT_FOUND_MESSAGE)
        if location.availability != MediaLocationAvailability.AVAILABLE:
            raise MediaContentUnavailableError(MEDIA_CONTENT_UNAVAILABLE_MESSAGE)
        library = self._library_repository.get(location.library_id)
        if library is None:
            raise MediaContentUnavailableError(MEDIA_CONTENT_UNAVAILABLE_MESSAGE)
        extension = _extension_for_relative_path(location.relative_path)
        media_type = supported_media_type(media.kind, extension)
        if media_type is None:
            raise MediaContentUnavailableError(MEDIA_CONTENT_UNAVAILABLE_MESSAGE)
        try:
            opened = self._content_reader.open(
                library.root,
                location.relative_path,
                media.kind,
            )
        except MediaContentUnavailableError:
            raise
        except MediaContentFailedError:
            raise
        except Exception:
            raise MediaContentFailedError(MEDIA_CONTENT_FAILED_MESSAGE) from None
        return ResolvedMediaContent(
            media_type=opened.media_type,
            byte_size=opened.byte_size,
            stream=opened.stream,
            close=opened.close,
        )


__all__ = [
    "MEDIA_CONTENT_FAILED_MESSAGE",
    "MEDIA_CONTENT_UNAVAILABLE_MESSAGE",
    "MEDIA_NOT_FOUND_MESSAGE",
    "MediaContentFailedError",
    "MediaContentNotFoundError",
    "MediaContentUnavailableError",
    "ResolveMediaContent",
    "ResolvedMediaContent",
    "supported_media_type",
]
