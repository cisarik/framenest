"""Integration proof for explicit local web AI suggestion review."""

from __future__ import annotations

import os
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import inspect, text

from framenest.adapters.api.application import create_app
from framenest.adapters.api.media_suggestion_api import MediaSuggestionApiDependencies
from framenest.application.library_scan import LibraryScanCandidateKind
from framenest.application.media_analysis import (
    MediaRelativePath,
    PreparedAnalysisResult,
    REQUESTED_FRAME_COUNT,
    TechnicalMetadata,
    build_representative_frame,
    PNG_SIGNATURE,
)
from framenest.application.media_suggestion import (
    MediaSuggestion,
    MediaSuggestionRequest,
    PreviewMediaSuggestion,
    PROMPT_VERSION,
)
from framenest.configuration import FrameNestSettings
from framenest.domain import Device, DeviceId, Library, LibraryId, LibraryPathFlavor, LibraryRoot
from framenest.infrastructure.persistence.device_repository import SqliteDeviceRepository
from framenest.infrastructure.persistence.engine import create_sqlite_engine, dispose_engine
from framenest.infrastructure.persistence.library_repository import SqliteLibraryRepository
from framenest.infrastructure.persistence.migrations import upgrade_database_to_head


class _DeterministicPreparer:
    def __init__(self, expected_relative_path: str) -> None:
        self.expected_relative_path = expected_relative_path
        self.calls: list[tuple[LibraryRoot, MediaRelativePath]] = []

    def prepare(
        self,
        root: LibraryRoot,
        relative_path: MediaRelativePath,
    ) -> PreparedAnalysisResult:
        self.calls.append((root, relative_path))
        if relative_path.value != self.expected_relative_path:
            raise AssertionError("unexpected relative path")
        return PreparedAnalysisResult(
            relative_path=relative_path,
            candidate_kind=LibraryScanCandidateKind.VIDEO,
            technical_metadata=TechnicalMetadata(
                duration_ms=1000,
                width=64,
                height=48,
                video_codec="h264",
                container_formats=("mp4",),
                has_audio=False,
            ),
            representative_frames=(
                build_representative_frame(timestamp_ms=100, payload=PNG_SIGNATURE + b"frame"),
            ),
            requested_frame_count=REQUESTED_FRAME_COUNT,
            warnings=(),
            ffprobe_version="ffprobe version hidden",
            ffmpeg_version="ffmpeg version hidden",
        )


class _DeterministicProvider:
    def __init__(self) -> None:
        self.calls: list[MediaSuggestionRequest] = []

    def suggest(self, request: MediaSuggestionRequest) -> MediaSuggestion:
        self.calls.append(request)
        return MediaSuggestion(
            title="Editable title",
            description="Editable description",
            collection="Meme",
            tags=("Meme", "Animation"),
            suggested_filename="editable-name.mp4",
            confidence=0.85,
            evidence=("Visible evidence",),
            uncertainties=("Unclear context",),
            provider_id="nvidia-nim",
            model_id="nvidia/nemotron-3-nano-omni-30b-a3b-reasoning",
            prompt_version=PROMPT_VERSION,
        )


def _native_flavor() -> LibraryPathFlavor:
    if os.name == "nt":
        return LibraryPathFlavor.WINDOWS
    return LibraryPathFlavor.POSIX


def _snapshot_files(root: Path) -> dict[str, tuple[int, int]]:
    snapshot: dict[str, tuple[int, int]] = {}
    for path in sorted(root.rglob("*")):
        if path.is_file():
            stat = path.stat()
            snapshot[path.relative_to(root).as_posix()] = (stat.st_size, stat.st_mtime_ns)
    return snapshot


def _row_counts(database_path: Path) -> dict[str, int]:
    engine = create_sqlite_engine(database_path)
    try:
        table_names = sorted(inspect(engine).get_table_names())
        with engine.connect() as connection:
            return {
                table_name: connection.execute(text(f"select count(*) from {table_name}")).scalar_one()
                for table_name in table_names
            }
    finally:
        dispose_engine(engine)


def test_local_web_media_suggestion_review_is_confirmed_validated_and_readonly(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "catalog.sqlite3"
    library_root = tmp_path / "registered-library"
    library_root.mkdir()
    source = library_root / "clip.mp4"
    original_source = b"not-real-media-but-explicit-candidate"
    source.write_bytes(original_source)
    before_files = _snapshot_files(library_root)

    settings = FrameNestSettings(database_path=database_path, _env_file=None)
    upgrade_database_to_head(settings)
    engine = create_sqlite_engine(database_path)
    library_id = LibraryId.new()
    try:
        device = Device(id=DeviceId.new(), display_name="Test Device")
        SqliteDeviceRepository(engine).add(device)
        library = Library(
            id=library_id,
            device_id=device.id,
            display_name="Temporary Videos",
            root=LibraryRoot(flavor=_native_flavor(), path=os.path.normpath(str(library_root))),
        )
        SqliteLibraryRepository(engine).add(library)
    finally:
        dispose_engine(engine)
    before_rows = _row_counts(database_path)

    engine = create_sqlite_engine(database_path)
    repository = SqliteLibraryRepository(engine)
    preparer = _DeterministicPreparer("clip.mp4")
    provider = _DeterministicProvider()
    try:
        with TestClient(
            create_app(
                settings=settings,
                media_suggestion_api_dependencies=MediaSuggestionApiDependencies(
                    preview_suggestion=PreviewMediaSuggestion(repository, preparer, provider),
                    provider_configured=True,
                ),
            )
        ) as client:
            missing_confirmation = client.post(
                f"/api/libraries/{library_id}/media-suggestion-preview",
                json={"relative_path": "clip.mp4", "confirm_cloud_upload": False},
            )
            assert missing_confirmation.status_code == 409
            assert preparer.calls == []
            assert provider.calls == []

            response = client.post(
                f"/api/libraries/{library_id}/media-suggestion-preview",
                json={"relative_path": "clip.mp4", "confirm_cloud_upload": True},
            )
            assert response.status_code == 200
            payload = response.json()
            assert payload["suggestion"]["title"] == "Editable title"
            assert payload["suggestion"]["tags"] == ["Meme", "Animation"]
            assert payload["sent_frame_count"] == 1
            assert "raw provider" not in response.text
            assert "payload_base64" not in response.text
            assert "image/jpeg" not in response.text
            assert str(library_root) not in response.text
            assert str(database_path) not in response.text

            missing_library = client.post(
                f"/api/libraries/{LibraryId.new()}/media-suggestion-preview",
                json={"relative_path": "clip.mp4", "confirm_cloud_upload": True},
            )
            assert missing_library.status_code == 404
            assert missing_library.json()["error"]["code"] == "LIBRARY_NOT_FOUND"
    finally:
        dispose_engine(engine)

    assert len(preparer.calls) == 1
    assert len(provider.calls) == 1
    assert source.read_bytes() == original_source
    assert _snapshot_files(library_root) == before_files
    assert not any(path.suffix in {".png", ".jpg", ".jpeg"} for path in library_root.rglob("*"))
    assert _row_counts(database_path) == before_rows
