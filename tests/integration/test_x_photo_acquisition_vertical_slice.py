"""Zero-network X photo acquisition vertical slice: fixture → staging → validator."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

from PIL import Image
from sqlalchemy import create_engine, text

from framenest.application.x_acquisition import (
    XAcquisitionCoordinator,
    XAcquisitionRequestService,
    XRequestLimits,
    x_classification_for_upload,
)
from framenest.domain.identities import MediaId, MediaLocationId
from framenest.domain.media_classification import ContentCategory
from framenest.domain.uploads import UploadSessionId, UploadValidatedFormat, UploadValidatedMediaKind
from framenest.domain.x_acquisition import XAcquisitionState, XAssetState, XPostClaimId
from framenest.infrastructure.media_validation.ffprobe import BoundedUploadMediaValidator
from framenest.infrastructure.persistence.catalog_schema import metadata
from framenest.infrastructure.persistence.media_metadata_repository import (
    SqliteMediaMetadataRepository,
)
from framenest.infrastructure.persistence.x_acquisition_claim_repository import (
    SqliteXAcquisitionClaimRepository,
)
from framenest.infrastructure.x.downloader import YtDlpXExtractor
from framenest.infrastructure.x.staging import ARTIFACT_FILENAME, FilesystemXStaging
from framenest.infrastructure.x.status_bridge import PhotoHttpResult
from tests.support.x_fake_demo import FakeXExtractor
from tests.unit.application.test_x_acquisition_lifecycle import (
    URL,
    _FakePublicationRepository,
    _FakeTransport,
    _FakeUploadRepository,
    _Notifier,
    _drain_until_terminal,
    _run,
)


POST_ID = "123456789"
SUBMITTED = f"https://x.com/author/status/{POST_ID}"


class _Reader:
    def __init__(self, payload: bytes) -> None:
        self._payload = payload
        self._offset = 0

    @property
    def size_bytes(self) -> int:
        return len(self._payload)

    @property
    def file_descriptor(self) -> int:
        return 123

    def read(self, size: int) -> bytes:
        chunk = self._payload[self._offset : self._offset + size]
        self._offset += len(chunk)
        return chunk

    def seek_start(self) -> None:
        self._offset = 0

    def verify_still_consistent(self) -> None:
        return None

    def close(self) -> None:
        return None


def _still_bytes(fmt: str) -> bytes:
    buffer = BytesIO()
    Image.new("RGB", (8, 8), (9, 10, 11)).save(buffer, format=fmt)
    return buffer.getvalue()


def _photo_status(media_id: str, fmt: str) -> dict:
    return {
        "id_str": POST_ID,
        "full_text": "A public photo",
        "timestamp": 1700000000,
        "user": {
            "id_str": "2222222222222222222",
            "screen_name": "author",
            "name": "Author Name",
        },
        "extended_entities": {
            "media": [
                {
                    "id_str": media_id,
                    "type": "photo",
                    "media_url_https": (
                        f"https://pbs.twimg.com/media/{media_id}?format={fmt}&name=small"
                    ),
                    "original_info": {"width": 8, "height": 8},
                }
            ]
        },
    }


def test_photo_fixture_stages_validates_and_classifies(tmp_path: Path) -> None:
    jpeg = _still_bytes("JPEG")
    png = _still_bytes("PNG")
    staging_root = tmp_path / "xroot"
    staging_root.mkdir(mode=0o700)
    staging = FilesystemXStaging(staging_root)
    payloads = {"photo-jpeg": jpeg, "photo-png": png}

    def _transport(_ip: str, _host: str, target: str, _timeout: float) -> PhotoHttpResult:
        media_id = "photo-png" if "photo-png" in target else "photo-jpeg"
        payload = payloads[media_id]
        content_type = "image/png" if media_id == "photo-png" else "image/jpeg"
        return PhotoHttpResult(
            status=200,
            headers={"content-type": content_type, "content-length": str(len(payload))},
            body=payload,
        )

    jpeg_extractor = YtDlpXExtractor(
        extract_status=lambda _post_id: _photo_status("photo-jpeg", "jpg"),
        photo_transport=_transport,
        photo_resolver=lambda _host, _port: [("8.8.8.8", 443)],
    )
    png_extractor = YtDlpXExtractor(
        extract_status=lambda _post_id: _photo_status("photo-png", "png"),
        photo_transport=_transport,
        photo_resolver=lambda _host, _port: [("8.8.8.8", 443)],
    )
    jpeg_extractor.download(
        post_id=POST_ID,
        ordinal=0,
        media_type="image",
        expected_mime="image/jpeg",
        source_media_key="photo-jpeg",
        selected_variant="x-photo-orig-jpeg-v1",
        stage_key="a" * 32,
        submitted_url=SUBMITTED,
        staging=staging,
    )
    png_extractor.download(
        post_id=POST_ID,
        ordinal=0,
        media_type="image",
        expected_mime="image/png",
        source_media_key="photo-png",
        selected_variant="x-photo-orig-png-v1",
        stage_key="b" * 32,
        submitted_url=SUBMITTED,
        staging=staging,
    )
    jpeg_bytes = (staging_root / ("a" * 32) / ARTIFACT_FILENAME).read_bytes()
    png_bytes = (staging_root / ("b" * 32) / ARTIFACT_FILENAME).read_bytes()
    assert jpeg_bytes == jpeg
    assert png_bytes == png
    validator = BoundedUploadMediaValidator()
    jpeg_evidence = validator.validate(_Reader(jpeg_bytes))
    png_evidence = validator.validate(_Reader(png_bytes))
    assert jpeg_evidence.media_kind is UploadValidatedMediaKind.IMAGE
    assert jpeg_evidence.media_format is UploadValidatedFormat.JPEG
    assert png_evidence.media_format is UploadValidatedFormat.PNG

    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    conn = engine.connect()
    conn.execute(text("PRAGMA foreign_keys=ON"))
    metadata.create_all(conn)
    repo = SqliteXAcquisitionClaimRepository(engine)
    fake = FakeXExtractor(tmp_path)
    fake.download_bytes = {0: jpeg}
    fake.assets = jpeg_extractor.inspect(post_id=POST_ID, submitted_url=SUBMITTED).assets
    media_id = MediaId.new()
    location_id = MediaLocationId.new()
    conn.execute(
        text(
            "INSERT INTO devices (id, display_name) VALUES "
            "('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa', 'Dev')"
        )
    )
    conn.execute(
        text(
            "INSERT INTO logical_media (id, media_kind, created_at_ms, updated_at_ms) "
            "VALUES (:id, 'image', 1, 1)"
        ),
        {"id": media_id.to_string()},
    )
    conn.execute(
        text(
            "INSERT INTO libraries (id, device_id, display_name, path_flavor, root_path) "
            "VALUES ('bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb', "
            "'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa', 'Lib', 'posix', :root)"
        ),
        {"root": str(staging_root)},
    )
    conn.execute(
        text(
            "INSERT INTO physical_media_locations "
            "(id, media_id, library_id, relative_path, availability, "
            " created_at_ms, updated_at_ms) "
            "VALUES (:id, :mid, 'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb', "
            "'x/artifact.bin', 'available', 1, 1)"
        ),
        {"id": location_id.to_string(), "mid": media_id.to_string()},
    )
    conn.commit()
    notifier = _Notifier()
    coordinator = XAcquisitionCoordinator(
        repo,
        fake,
        staging,
        _FakeTransport(),
        _FakeUploadRepository(),
        _FakePublicationRepository(media_id, location_id),
        notifier,
        notifier,
    )
    service = XAcquisitionRequestService(
        repo,
        limits=XRequestLimits(
            max_active_per_requester=2,
            max_global_active=8,
            max_submits_per_hour=6,
            max_failed_per_24h=10,
            free_space_bytes=lambda: 10_737_418_240,
        ),
        metadata_repository=SqliteMediaMetadataRepository(engine),
    )
    submitted = service.submit(
        SUBMITTED, login_key="alice", content_category=ContentCategory.MOVIE
    )
    claim = _run(_drain_until_terminal(coordinator, repo, submitted.request_id))
    assert claim.state is XAcquisitionState.COMPLETED
    assets = repo.list_assets_for_post(claim.id)
    assert assets[0].state is XAssetState.CATALOGED
    classification = x_classification_for_upload(
        repo, UploadSessionId.from_string(assets[0].id.to_string())
    )
    assert classification is not None
    assert classification.content_category is ContentCategory.MOVIE
    conn.close()


def test_photo_claim_retry_after_retryable_timeout(tmp_path: Path) -> None:
    from framenest.application.ports.x_extractor import XExtractionError

    jpeg = _still_bytes("JPEG")
    staging_root = tmp_path / "xroot"
    staging_root.mkdir(mode=0o700)
    staging = FilesystemXStaging(staging_root)
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    conn = engine.connect()
    conn.execute(text("PRAGMA foreign_keys=ON"))
    metadata.create_all(conn)
    repo = SqliteXAcquisitionClaimRepository(engine)
    fake = FakeXExtractor(tmp_path)
    fake.download_bytes = {0: jpeg}
    attempts = {"count": 0}
    original = fake.download

    def flaky_download(**kwargs):
        attempts["count"] += 1
        if attempts["count"] == 1:
            raise XExtractionError("X_DOWNLOAD_TIMEOUT", "timeout")
        return original(**kwargs)

    fake.download = flaky_download
    media_id = MediaId.new()
    location_id = MediaLocationId.new()
    conn.execute(
        text(
            "INSERT INTO devices (id, display_name) VALUES "
            "('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa', 'Dev')"
        )
    )
    conn.execute(
        text(
            "INSERT INTO logical_media (id, media_kind, created_at_ms, updated_at_ms) "
            "VALUES (:id, 'image', 1, 1)"
        ),
        {"id": media_id.to_string()},
    )
    conn.execute(
        text(
            "INSERT INTO libraries (id, device_id, display_name, path_flavor, root_path) "
            "VALUES ('bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb', "
            "'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa', 'Lib', 'posix', :root)"
        ),
        {"root": str(staging_root)},
    )
    conn.execute(
        text(
            "INSERT INTO physical_media_locations "
            "(id, media_id, library_id, relative_path, availability, "
            " created_at_ms, updated_at_ms) VALUES (:id, :mid, "
            "'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb', 'x/artifact.bin', 'available', 1, 1)"
        ),
        {"id": location_id.to_string(), "mid": media_id.to_string()},
    )
    conn.commit()
    notifier = _Notifier()
    coordinator = XAcquisitionCoordinator(
        repo,
        fake,
        staging,
        _FakeTransport(),
        _FakeUploadRepository(),
        _FakePublicationRepository(media_id, location_id),
        notifier,
        notifier,
    )
    service = XAcquisitionRequestService(
        repo,
        limits=XRequestLimits(
            max_active_per_requester=2,
            max_global_active=8,
            max_submits_per_hour=6,
            max_failed_per_24h=10,
            free_space_bytes=lambda: 10_737_418_240,
        ),
        metadata_repository=SqliteMediaMetadataRepository(engine),
    )
    submitted = service.submit(URL, login_key="alice")
    claim = _run(_drain_until_terminal(coordinator, repo, submitted.request_id))
    assert claim.state is XAcquisitionState.FAILED
    retried = service.retry(
        XPostClaimId.from_string(submitted.request_id), login_key="alice"
    )
    claim = _run(_drain_until_terminal(coordinator, repo, retried.claim_id))
    assert claim.state is XAcquisitionState.COMPLETED
    conn.close()
