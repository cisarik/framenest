"""Contract tests for the secure media content API."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from fastapi.testclient import TestClient

from framenest.adapters.api.application import create_app
from framenest.adapters.api.media_content_api import MediaContentApiDependencies
from framenest.application.media_content import (
    MediaContentFailedError,
    MediaContentNotFoundError,
    MediaContentUnavailableError,
    ResolvedMediaContent,
)
from framenest.application.ports.media_repository import FrameNestMediaRepositoryError
from framenest.application.ports.library_repository import FrameNestLibraryRepositoryError
from framenest.configuration import FrameNestSettings

MEDIA_ID = "12345678-1234-4234-9234-123456789abc"
LOCATION_ID = "abcdefab-cdef-4abc-8def-abcdefabcdef"
PRIVATE_TEXT = "secret-private-db-path-leak"
MP4_BYTES = bytes(range(256)) * 4
GIF_BYTES = b"GIF89a" + b"\x00" * 100
CONTENT_PATH = f"/api/media/{MEDIA_ID}/locations/{LOCATION_ID}/content"


@dataclass
class _FakeResolveContent:
    result: ResolvedMediaContent | None = None
    error: Exception | None = None

    def execute(self, media_id, location_id):
        if self.error is not None:
            raise self.error
        return self.result


def _resolved(media_type, payload):
    return ResolvedMediaContent(
        media_type=media_type,
        byte_size=len(payload),
        stream=lambda start, length: _slice(payload, start, length),
    )


def _slice(payload, start, length):
    if length is None:
        yield payload[start:]
    else:
        yield payload[start : start + length]


def _client(
    resolve=None,
    catalog_available=True,
    database_path=None,
):
    deps = MediaContentApiDependencies(
        resolve_content=resolve or _FakeResolveContent(),
        catalog_available=lambda: catalog_available,
    )
    settings = FrameNestSettings(
        database_path=database_path or Path("/tmp/framenest-media-content-api.sqlite3"),
        _env_file=None,
    )
    return TestClient(create_app(settings=settings, media_content_api_dependencies=deps))


def test_full_gif_200():
    resolved = _resolved("image/gif", GIF_BYTES)
    response = _client(resolve=_FakeResolveContent(result=resolved)).get(CONTENT_PATH)
    assert response.status_code == 200
    assert response.content == GIF_BYTES
    assert response.headers["content-type"] == "image/gif"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["cache-control"] == "private, no-store"
    assert response.headers["accept-ranges"] == "bytes"
    assert response.headers["content-length"] == str(len(GIF_BYTES))


def test_full_mp4_200():
    resolved = _resolved("video/mp4", MP4_BYTES)
    response = _client(resolve=_FakeResolveContent(result=resolved)).get(CONTENT_PATH)
    assert response.status_code == 200
    assert response.content == MP4_BYTES
    assert response.headers["content-type"] == "video/mp4"
    assert response.headers["content-length"] == str(len(MP4_BYTES))


def test_closed_range_206():
    resolved = _resolved("video/mp4", MP4_BYTES)
    response = _client(resolve=_FakeResolveContent(result=resolved)).get(
        CONTENT_PATH, headers={"Range": "bytes=0-9"}
    )
    assert response.status_code == 206
    assert response.content == MP4_BYTES[0:10]
    assert response.headers["content-length"] == "10"
    assert response.headers["content-range"] == f"bytes 0-9/{len(MP4_BYTES)}"


def test_open_ended_range_206():
    resolved = _resolved("video/mp4", MP4_BYTES)
    response = _client(resolve=_FakeResolveContent(result=resolved)).get(
        CONTENT_PATH, headers={"Range": "bytes=500-"}
    )
    assert response.status_code == 206
    assert response.content == MP4_BYTES[500:]
    assert response.headers["content-length"] == str(len(MP4_BYTES) - 500)


def test_suffix_range_206():
    resolved = _resolved("video/mp4", MP4_BYTES)
    response = _client(resolve=_FakeResolveContent(result=resolved)).get(
        CONTENT_PATH, headers={"Range": "bytes=-10"}
    )
    assert response.status_code == 206
    assert response.content == MP4_BYTES[-10:]
    assert response.headers["content-length"] == "10"


def test_malformed_range_416():
    resolved = _resolved("video/mp4", MP4_BYTES)
    for bad in ["bytes=abc", "0-10", "bytes=", "bytes=1-2,3-4", "bytes=-0", "bytes=5-3"]:
        response = _client(resolve=_FakeResolveContent(result=resolved)).get(
            CONTENT_PATH, headers={"Range": bad}
        )
        assert response.status_code == 416, f"failed for {bad}"
        assert response.headers["content-range"] == f"bytes */{len(MP4_BYTES)}"
        assert response.headers["cache-control"] == "no-store"


def test_unsatisfiable_range_416():
    resolved = _resolved("video/mp4", MP4_BYTES)
    response = _client(resolve=_FakeResolveContent(result=resolved)).get(
        CONTENT_PATH, headers={"Range": f"bytes={len(MP4_BYTES)}-"}
    )
    assert response.status_code == 416
    assert response.headers["content-range"] == f"bytes */{len(MP4_BYTES)}"


def test_zero_byte_file_full_200():
    resolved = _resolved("video/mp4", b"")
    response = _client(resolve=_FakeResolveContent(result=resolved)).get(CONTENT_PATH)
    assert response.status_code == 200
    assert response.content == b""
    assert response.headers["content-length"] == "0"


def test_invalid_uuid_returns_422():
    response = _client().get("/api/media/not-a-uuid/locations/not-a-uuid/content")
    assert response.status_code == 422


def test_catalog_unavailable_503():
    response = _client(catalog_available=False).get(CONTENT_PATH)
    assert response.status_code == 503
    assert response.headers["cache-control"] == "no-store"


def test_not_found_404():
    response = _client(
        resolve=_FakeResolveContent(error=MediaContentNotFoundError("x"))
    ).get(CONTENT_PATH)
    assert response.status_code == 404
    assert PRIVATE_TEXT not in response.text


def test_unavailable_409():
    response = _client(
        resolve=_FakeResolveContent(error=MediaContentUnavailableError("x"))
    ).get(CONTENT_PATH)
    assert response.status_code == 409
    assert response.headers["cache-control"] == "no-store"


def test_unexpected_failure_500():
    response = _client(
        resolve=_FakeResolveContent(error=FrameNestMediaRepositoryError(PRIVATE_TEXT))
    ).get(CONTENT_PATH)
    assert response.status_code == 500
    assert PRIVATE_TEXT not in response.text


def test_no_absolute_path_or_exception_disclosure():
    for error in [
        MediaContentNotFoundError("private-path-leak"),
        MediaContentUnavailableError("private-path-leak"),
        MediaContentFailedError("private-path-leak"),
        FrameNestLibraryRepositoryError(PRIVATE_TEXT),
    ]:
        response = _client(resolve=_FakeResolveContent(error=error)).get(CONTENT_PATH)
        assert "private-path-leak" not in response.text
        assert PRIVATE_TEXT not in response.text
