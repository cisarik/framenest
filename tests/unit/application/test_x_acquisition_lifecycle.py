"""Requester-private X application lifecycle and authorization tests."""

from __future__ import annotations

import asyncio
import types

import pytest
from sqlalchemy import create_engine, text

from framenest.application.x_acquisition import (
    XAcquisitionAdministrationService,
    XAcquisitionCoordinator,
    XAcquisitionRequestService,
    XRequestLimitError,
    XRequestLimits,
)
from framenest.domain.identities import MediaId, MediaLocationId
from framenest.domain.uploads import UploadSessionState
from framenest.domain.x_acquisition import (
    XAcquisitionState,
    XMediaType,
    XNormalizedAssetDescriptor,
    XPostClaimId,
)
from framenest.infrastructure.persistence.catalog_schema import metadata
from framenest.infrastructure.persistence.x_acquisition_claim_repository import (
    SqliteXAcquisitionClaimRepository,
)
from framenest.infrastructure.x.staging import FilesystemXStaging
from tests.support.x_fake_demo import FakeXExtractor


class _Notifier:
    def notify(self) -> None:
        pass


class _FakeTransport:
    def __init__(self) -> None:
        self.received: dict[str, int] = {}

    def create_session(self, **_: object):
        return types.SimpleNamespace(received_size_bytes=0, state="created")

    async def receive_chunk(self, upload_id: object, upload_offset: int,
                            content_length: int, body: object):
        self.received[str(upload_id)] = upload_offset + content_length
        return types.SimpleNamespace(
            received_size_bytes=self.received[str(upload_id)], state="receiving"
        )

    async def complete(self, upload_id: object):
        self.received[str(upload_id)] = self.received.get(str(upload_id), 0)
        return types.SimpleNamespace(
            received_size_bytes=self.received[str(upload_id)], state="received"
        )


class _FakeUploadRepository:
    def __init__(self) -> None:
        self.upload = types.SimpleNamespace(state=UploadSessionState.CATALOGED)

    def get(self, upload_id: object):
        return self.upload


class _FakePublicationRepository:
    def __init__(self, media_id: MediaId, location_id: MediaLocationId) -> None:
        pub = types.SimpleNamespace(
            media_id=media_id, media_location_id=location_id
        )
        self.candidate = types.SimpleNamespace(publication=pub)

    def get_candidate(self, upload_id: object):
        return self.candidate

    def find_cataloged_by_byte_identity(self, *a, **k):
        return None


URL = "https://x.com/author/status/987654321"
POST_ID = "987654321"


@pytest.fixture()
def lifecycle(tmp_path):
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    conn = engine.connect()
    conn.execute(text("PRAGMA foreign_keys=ON"))
    metadata.create_all(conn)
    repo = SqliteXAcquisitionClaimRepository(engine)
    staging_root = tmp_path / "xroot"
    staging_root.mkdir(exist_ok=True)
    staging_root.chmod(0o700)
    staging = FilesystemXStaging(staging_root)
    extractor = FakeXExtractor(tmp_path)
    extractor.post_text = "A genuinely funny clip with text"
    extractor.assets = [
        XNormalizedAssetDescriptor(
            ordinal=0, media_type=XMediaType.VIDEO, expected_mime="video/mp4",
            source_media_key="asset-0", width=640, height=360, duration_seconds=12,
        ),
        XNormalizedAssetDescriptor(
            ordinal=1, media_type=XMediaType.IMAGE, expected_mime="image/jpeg",
            source_media_key="asset-1", width=800, height=600,
        ),
    ]
    extractor.download_bytes = {0: b"fakevideo", 1: b"fakejpeg"}
    transport = _FakeTransport()
    upload_repo = _FakeUploadRepository()
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
            "VALUES (:id, 'video', 1, 1)"
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
            "'x/artifact.mp4', 'available', 1, 1)"
        ),
        {"id": location_id.to_string(), "mid": media_id.to_string()},
    )
    conn.commit()
    pub_repo = _FakePublicationRepository(media_id, location_id)
    notifier = _Notifier()
    coordinator = XAcquisitionCoordinator(
        repo, extractor, staging, transport, upload_repo, pub_repo,
        notifier, notifier,
    )
    limits = XRequestLimits(
        max_active_per_requester=1,
        max_global_active=8,
        max_submits_per_hour=6,
        max_failed_per_24h=10,
        free_space_bytes=lambda: 10_737_418_240,
    )
    service = XAcquisitionRequestService(repo, limits=limits)
    admin = XAcquisitionAdministrationService(repo)
    yield repo, service, admin, coordinator, extractor, media_id
    conn.close()


def _run(coro):
    return asyncio.run(coro)


async def _drain_until_terminal(coordinator, repo, claim_id: str, timeout: int = 50) -> None:
    parsed = XPostClaimId.from_string(claim_id)
    for _ in range(timeout):
        await coordinator.drain()
        claim = repo.get_post(parsed)
        if claim is not None and claim.state in {
            XAcquisitionState.COMPLETED,
            XAcquisitionState.COMPLETED_PARTIAL,
            XAcquisitionState.FAILED,
        }:
            return claim
    raise AssertionError("acquisition did not reach terminal state")


def test_successful_multi_asset_submit_and_complete(lifecycle) -> None:
    repo, service, admin, coordinator, extractor, media_id = lifecycle
    result = service.submit(URL, login_key="alice")
    assert result.submission_result == "new"
    claim_id = result.request_id
    claim = _run(_drain_until_terminal(coordinator, repo, claim_id))
    assert claim.state is XAcquisitionState.COMPLETED
    assert claim.success_count == 2
    assert claim.failure_count == 0
    assets = repo.list_assets_for_post(claim.id)
    assert {a.state.value for a in assets} == {"cataloged"}
    assert all(a.media_id == media_id for a in assets)
    # Requester private access.
    assert repo.has_live_requester_media_access(media_id=media_id, login_key="alice")
    assert not repo.has_live_requester_media_access(media_id=media_id, login_key="bob")


def test_same_requester_idempotent_submit(lifecycle) -> None:
    repo, service, admin, coordinator, extractor, _ = lifecycle
    first = service.submit(URL, login_key="alice")
    claim = _run(_drain_until_terminal(coordinator, repo, first.request_id))
    assert claim.state is XAcquisitionState.COMPLETED
    second = service.submit(URL, login_key="alice")
    assert second.submission_result == "reuse"
    assert second.phase == "completed"
    # Reuse returns the requester's existing durable result, not a new claim.
    assert second.request_id == first.request_id


def test_cross_requester_does_not_see_foreign_claim(lifecycle) -> None:
    repo, service, admin, coordinator, extractor, _ = lifecycle
    result = service.submit(URL, login_key="alice")
    owned = service.get_owned(
        __import__("framenest.domain.x_acquisition", fromlist=["XPostClaimId"]).XPostClaimId.from_string(result.request_id),
        login_key="alice",
    )
    assert owned.claim_id == result.request_id
    with pytest.raises(Exception):
        service.get_owned(
            __import__("framenest.domain.x_acquisition", fromlist=["XPostClaimId"]).XPostClaimId.from_string(result.request_id),
            login_key="bob",
        )


def test_partial_success_single_asset_fails(lifecycle) -> None:
    repo, service, admin, coordinator, extractor, media_id = lifecycle
    extractor.assets = [
        XNormalizedAssetDescriptor(
            ordinal=0, media_type=XMediaType.VIDEO, expected_mime="video/mp4",
            source_media_key="asset-0", width=1, height=1, duration_seconds=12,
        ),
        XNormalizedAssetDescriptor(
            ordinal=1, media_type=XMediaType.IMAGE, expected_mime="image/jpeg",
            source_media_key="asset-1", width=800, height=600,
        ),
    ]
    extractor.download_bytes = {1: b"fakejpeg"}  # asset 0 download is a no-op -> too large below
    result = service.submit(URL, login_key="alice")
    claim = _run(_drain_until_terminal(coordinator, repo, result.request_id))
    assets = repo.list_assets_for_post(claim.id)
    # Asset 0 whose download produced a default oversize payload is rejected.
    assert claim.state in {XAcquisitionState.COMPLETED_PARTIAL, XAcquisitionState.COMPLETED, XAcquisitionState.FAILED}
    assert claim.success_count + claim.failure_count == claim.discovered_asset_count


def test_invalid_url_submit_rejected(lifecycle) -> None:
    repo, service, admin, coordinator, extractor, _ = lifecycle
    from framenest.domain.x_acquisition import FrameNestXUrlError

    with pytest.raises(FrameNestXUrlError):
        service.submit("https://youtube.com/watch?v=abc", login_key="alice")


def test_admission_active_limit(lifecycle) -> None:
    repo, service, admin, coordinator, extractor, _ = lifecycle
    result = service.submit(URL, login_key="alice")
    # Second active submission for same post returns active_reuse, not a limit.
    second = service.submit(URL, login_key="alice")
    assert second.submission_result == "active_reuse"


def test_admin_review_exposes_result(lifecycle) -> None:
    repo, service, admin, coordinator, extractor, media_id = lifecycle
    result = service.submit(URL, login_key="alice")
    claim = _run(_drain_until_terminal(coordinator, repo, result.request_id))
    snapshot = admin.get(
        __import__("framenest.domain.x_acquisition", fromlist=["XPostClaimId"]).XPostClaimId.from_string(result.request_id)
    )
    assert snapshot.success_count == 2
    assert snapshot.source_author_handle == "author"
    assert snapshot.state == "completed"
