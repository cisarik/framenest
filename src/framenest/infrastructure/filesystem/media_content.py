"""Local filesystem adapter for secure read-only media content delivery."""

from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path, PurePosixPath

from framenest.application.media_content import (
    MEDIA_CONTENT_FAILED_MESSAGE,
    MEDIA_CONTENT_UNAVAILABLE_MESSAGE,
    MediaContentFailedError,
    MediaContentUnavailableError,
    supported_media_type,
)
from framenest.application.ports.media_content import OpenedMediaContent
from framenest.domain import LibraryPathFlavor, LibraryRoot
from framenest.domain.media import MediaKind, MediaRelativePath

_CHUNK_SIZE = 65_536


def _native_path_flavor() -> LibraryPathFlavor:
    if os.name == "nt":
        return LibraryPathFlavor.WINDOWS
    return LibraryPathFlavor.POSIX


def _resolve_safe_target(
    root: LibraryRoot,
    relative_path: MediaRelativePath,
) -> Path:
    """Resolve one safe regular-file target beneath a registered library root."""
    if root.flavor != _native_path_flavor():
        raise MediaContentUnavailableError(MEDIA_CONTENT_UNAVAILABLE_MESSAGE)

    host_root = Path(root.path)
    try:
        if not host_root.exists() or not host_root.is_dir():
            raise MediaContentUnavailableError(MEDIA_CONTENT_UNAVAILABLE_MESSAGE)
    except OSError:
        raise MediaContentUnavailableError(MEDIA_CONTENT_UNAVAILABLE_MESSAGE) from None

    parsed = PurePosixPath(relative_path.value)
    if parsed.is_absolute() or any(
        part in (".", "..") or not part for part in parsed.parts
    ):
        raise MediaContentUnavailableError(MEDIA_CONTENT_UNAVAILABLE_MESSAGE)

    candidate = host_root.joinpath(*parsed.parts)

    try:
        resolved_root = host_root.resolve(strict=True)
        resolved_target = candidate.resolve(strict=True)
    except (OSError, ValueError):
        raise MediaContentUnavailableError(MEDIA_CONTENT_UNAVAILABLE_MESSAGE) from None

    try:
        resolved_target.relative_to(resolved_root)
    except ValueError:
        raise MediaContentUnavailableError(MEDIA_CONTENT_UNAVAILABLE_MESSAGE) from None

    try:
        if not resolved_target.is_file():
            raise MediaContentUnavailableError(MEDIA_CONTENT_UNAVAILABLE_MESSAGE)
    except OSError:
        raise MediaContentUnavailableError(MEDIA_CONTENT_UNAVAILABLE_MESSAGE) from None

    return resolved_target


class LocalMediaContentReader:
    """Read-only filesystem content reader for registered library media."""

    def open(
        self,
        root: LibraryRoot,
        relative_path: MediaRelativePath,
        kind: MediaKind,
    ) -> OpenedMediaContent:
        try:
            target = _resolve_safe_target(root, relative_path)
            extension = target.suffix.lower()
            media_type = supported_media_type(kind, extension)
            if media_type is None:
                raise MediaContentUnavailableError(MEDIA_CONTENT_UNAVAILABLE_MESSAGE)
            try:
                stat_result = target.stat()
            except OSError:
                raise MediaContentUnavailableError(
                    MEDIA_CONTENT_UNAVAILABLE_MESSAGE,
                ) from None
            byte_size = stat_result.st_size
            try:
                with open(target, "rb") as handle:
                    handle.read(0)
            except OSError:
                raise MediaContentUnavailableError(
                    MEDIA_CONTENT_UNAVAILABLE_MESSAGE,
                ) from None
        except MediaContentUnavailableError:
            raise
        except MediaContentFailedError:
            raise
        except Exception:
            raise MediaContentFailedError(MEDIA_CONTENT_FAILED_MESSAGE) from None

        resolved_target = target

        def stream(start: int, length: int | None) -> Iterator[bytes]:
            remaining = length
            handle = open(resolved_target, "rb")
            try:
                if start > 0:
                    handle.seek(start)
                while True:
                    if remaining is not None and remaining <= 0:
                        break
                    chunk = handle.read(_CHUNK_SIZE)
                    if not chunk:
                        break
                    if remaining is not None:
                        chunk = chunk[:remaining]
                    yield chunk
                    if remaining is not None:
                        remaining -= len(chunk)
            finally:
                handle.close()

        return OpenedMediaContent(
            media_type=media_type,
            byte_size=byte_size,
            stream=stream,
        )
