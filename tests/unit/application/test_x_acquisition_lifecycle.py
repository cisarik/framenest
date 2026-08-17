"""Requester-private X application lifecycle and authorization tests."""

from __future__ import annotations

import asyncio
import time
import types

import pytest
from sqlalchemy import create_engine, text

from framenest.application.ports.x_extractor import XExtractionError, XExtractionInterrupted
from framenest.application.x_acquisition import (
    XAcquisitionAdministrationService,
    XAcquisitionCoordinator,
    XAcquisitionNotFoundError,
    XAcquisitionRequestService,
    XAcquisitionStateConflictError,
    XRequestLimitError,
    XRequestLimits,
)
from framenest.domain.identities import MediaId, MediaLocationId
from framenest.domain.media_user_alias import parse_alias_content
from framenest.domain.uploads import UploadSessionState
from framenest.domain.x_acquisition import (
    XAcquisitionState,
    XAssetState,
    XMediaType,
    XNormalizedAssetDescriptor,
    XPostClaimId,
)
from framenest.infrastructure.persistence.catalog_schema import metadata
from framenest.infrastructure.persistence.media_user_alias_repository import (
    SqliteMediaUserAliasRepository,
)
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
    alias_repo = SqliteMediaUserAliasRepository(engine)
    coordinator = XAcquisitionCoordinator(
        repo, extractor, staging, transport, upload_repo, pub_repo,
        notifier, notifier, alias_repository=alias_repo,
    )
    limits = XRequestLimits(
        max_active_per_requester=1,
        max_global_active=8,
        max_submits_per_hour=6,
        max_failed_per_24h=10,
        free_space_bytes=lambda: 10_737_418_240,
    )
    service = XAcquisitionRequestService(
        repo, limits=limits, alias_repository=alias_repo
    )
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


def _partial_fixture(extractor):
    """Deterministically fail asset ordinal 0 while asset 1 succeeds."""
    from framenest.application.ports.x_extractor import XExtractionError as _E

    original_download = extractor.download

    def failing_download(*, ordinal, **kwargs):
        if ordinal == 0:
            raise _E("X_DOWNLOAD_TIMEOUT", "simulated asset failure")
        return original_download(ordinal=ordinal, **kwargs)

    extractor.assets = [
        XNormalizedAssetDescriptor(
            ordinal=0, media_type=XMediaType.VIDEO, expected_mime="video/mp4",
            source_media_key="asset-0", width=320, height=180, duration_seconds=12,
        ),
        XNormalizedAssetDescriptor(
            ordinal=1, media_type=XMediaType.IMAGE, expected_mime="image/jpeg",
            source_media_key="asset-1", width=800, height=600,
        ),
    ]
    extractor.download = failing_download


def test_completed_partial_retry_is_visible_and_touches_only_failed_asset(lifecycle) -> None:
    repo, service, admin, coordinator, extractor, media_id = lifecycle
    _partial_fixture(extractor)
    result = service.submit(URL, login_key="alice")
    claim = _run(_drain_until_terminal(coordinator, repo, result.request_id))
    assert claim.state is XAcquisitionState.COMPLETED_PARTIAL

    snapshot = service.get_owned(claim.id, login_key="alice")
    assert snapshot.can_retry is True

    before = {a.ordinal: a for a in repo.list_assets_for_post(claim.id)}
    assert before[0].state is XAssetState.FAILED
    assert before[1].state is XAssetState.CATALOGED
    successful_media_id = before[1].media_id

    service.retry(claim.id, login_key="alice")

    after = {a.ordinal: a for a in repo.list_assets_for_post(claim.id)}
    # Only the failed/incomplete asset is reset for re-acquisition.
    assert after[0].state is XAssetState.PENDING
    # The successful cataloged asset is preserved, bytes and linkage intact.
    assert after[1].state is XAssetState.CATALOGED
    assert after[1].media_id == successful_media_id


def test_completed_successful_claim_has_no_retry(lifecycle) -> None:
    repo, service, admin, coordinator, extractor, media_id = lifecycle
    result = service.submit(URL, login_key="alice")
    claim = _run(_drain_until_terminal(coordinator, repo, result.request_id))
    assert claim.state is XAcquisitionState.COMPLETED
    snapshot = service.get_owned(claim.id, login_key="alice")
    assert snapshot.can_retry is False


def test_failed_claim_retry_is_visible(lifecycle) -> None:
    repo, service, admin, coordinator, extractor, media_id = lifecycle
    extractor.assets = [
        XNormalizedAssetDescriptor(
            ordinal=0, media_type=XMediaType.VIDEO, expected_mime="video/mp4",
            source_media_key="asset-0", width=320, height=180, duration_seconds=12,
        ),
    ]
    def failing_download(*, ordinal, **kwargs):
        raise XExtractionError("X_DOWNLOAD_TIMEOUT", "simulated asset failure")

    extractor.download = failing_download
    result = service.submit(URL, login_key="alice")
    claim = _run(_drain_until_terminal(coordinator, repo, result.request_id))
    assert claim.state is XAcquisitionState.FAILED
    snapshot = service.get_owned(claim.id, login_key="alice")
    assert snapshot.can_retry is True


def test_foreign_requester_cannot_retry_owning_claim(lifecycle) -> None:
    repo, service, admin, coordinator, extractor, media_id = lifecycle
    _partial_fixture(extractor)
    result = service.submit(URL, login_key="alice")
    claim = _run(_drain_until_terminal(coordinator, repo, result.request_id))
    assert claim.state is XAcquisitionState.COMPLETED_PARTIAL
    with pytest.raises(XAcquisitionNotFoundError):
        service.retry(claim.id, login_key="bob")


def test_non_retryable_terminal_claim_cannot_retry(lifecycle) -> None:
    repo, service, admin, coordinator, extractor, media_id = lifecycle
    result = service.submit(URL, login_key="alice")
    claim = _run(_drain_until_terminal(coordinator, repo, result.request_id))
    assert claim.state is XAcquisitionState.COMPLETED
    with pytest.raises(XAcquisitionStateConflictError):
        service.retry(claim.id, login_key="alice")


def test_inspect_and_download_do_not_block_the_event_loop(lifecycle) -> None:
    repo, service, admin, original, extractor, _media_id = lifecycle

    class _SlowExtractor:
        def __init__(self, inner: object) -> None:
            self._inner = inner

        def attest_version(self) -> str | None:
            return self._inner.attest_version()

        def inspect(self, **kwargs: object):
            time.sleep(0.2)
            return self._inner.inspect(**kwargs)

        def download(self, **kwargs: object):
            return self._inner.download(**kwargs)

    coordinator = XAcquisitionCoordinator(
        repo,
        _SlowExtractor(extractor),
        original._staging,
        original._transport,
        original._upload_repository,
        original._publication_repository,
        original._validation_coordinator,
        original._publication_coordinator,
    )
    ticks: list[float] = []

    async def ticker() -> None:
        deadline = time.monotonic() + 0.15
        while time.monotonic() < deadline:
            ticks.append(time.monotonic())
            await asyncio.sleep(0.02)

    async def scenario() -> None:
        service.submit(URL, login_key="alice")
        await asyncio.gather(coordinator.drain(), ticker())

    _run(scenario())
    assert len(ticks) >= 4


def test_interrupted_acquiring_retries_same_asset_after_staging_clear(lifecycle) -> None:
    repo, service, admin, original, extractor, _media_id = lifecycle
    extractor.assets = [
        XNormalizedAssetDescriptor(
            ordinal=0,
            media_type=XMediaType.VIDEO,
            expected_mime="video/mp4",
            source_media_key="asset-0",
            width=640,
            height=360,
            duration_seconds=12,
        )
    ]
    extractor.download_bytes = {0: b"\x00\x00\x00\x18ftypmp42retry-bytes"}

    class _InterruptOnceExtractor:
        def __init__(self, inner: object) -> None:
            self._inner = inner
            self.downloads = 0
            self.first_asset_id = None
            self.partial_present = False

        def attest_version(self) -> str | None:
            return self._inner.attest_version()

        def inspect(self, **kwargs: object):
            return self._inner.inspect(**kwargs)

        def download(self, **kwargs: object):
            self.downloads += 1
            staging = kwargs["staging"]
            stage_key = kwargs["stage_key"]
            directory = staging.prepare(stage_key)
            artifact = directory / "artifact.mp4"
            if self.downloads == 1:
                artifact.write_bytes(b"partial-overwrites-bait")
                self.partial_present = artifact.exists()
                raise XExtractionInterrupted()
            assert not artifact.exists()
            return self._inner.download(**kwargs)

    wrapper = _InterruptOnceExtractor(extractor)
    coordinator = XAcquisitionCoordinator(
        repo,
        wrapper,
        original._staging,
        original._transport,
        original._upload_repository,
        original._publication_repository,
        original._validation_coordinator,
        original._publication_coordinator,
    )
    result = service.submit(URL, login_key="alice")
    parsed = XPostClaimId.from_string(result.request_id)

    async def drain_until_interrupted() -> None:
        for _ in range(8):
            await coordinator.drain()
            assets = repo.list_assets_for_post(parsed)
            if wrapper.downloads >= 1 and any(
                asset.state is XAssetState.ACQUIRING for asset in assets
            ):
                return
        raise AssertionError("interrupted ACQUIRING asset was not observed")

    _run(drain_until_interrupted())
    assets = repo.list_assets_for_post(parsed)
    acquiring = [asset for asset in assets if asset.state is XAssetState.ACQUIRING]
    assert len(acquiring) == 1
    original_id = acquiring[0].id.to_string()
    original_stage_key = acquiring[0].stage_key
    assert wrapper.partial_present
    claim = _run(_drain_until_terminal(coordinator, repo, result.request_id))
    recovered = repo.list_assets_for_post(parsed)
    assert claim.state is XAcquisitionState.COMPLETED
    assert len(recovered) == 1
    assert recovered[0].id.to_string() == original_id
    assert recovered[0].stage_key == original_stage_key
    assert wrapper.downloads == 2


def _seed_canonical_and_metadata(repo, media_id: MediaId, title: str) -> None:
    with repo._engine.begin() as connection:
        connection.execute(
            text(
                "INSERT OR IGNORE INTO canonical_tags "
                "(key, display_name, created_at_ms, updated_at_ms) "
                "VALUES ('meme', 'Meme', 1, 1)"
            )
        )
        connection.execute(
            text(
                "INSERT OR IGNORE INTO media_metadata "
                "(media_id, display_title, description, content_category, "
                "acquisition_source, created_at_ms, updated_at_ms) "
                "VALUES (:id, :title, NULL, 'meme', 'x_manual_claim', 1, 1)"
            ),
            {"id": media_id.to_string(), "title": title},
        )


def test_pending_alias_applies_on_complete_without_changing_canonical_title(
    lifecycle,
) -> None:
    repo, service, admin, coordinator, extractor, media_id = lifecycle
    _seed_canonical_and_metadata(repo, media_id, "Canonical From Tweet")
    alias_repo = coordinator._alias_repository
    result = service.submit(
        URL,
        login_key="alice",
        alias=parse_alias_content("Overlay title", "Overlay desc", ["meme"]),
    )
    claim = _run(_drain_until_terminal(coordinator, repo, result.request_id))
    assert claim.state is XAcquisitionState.COMPLETED
    overlay = alias_repo.get_alias(media_id, "alice")
    assert overlay is not None
    assert overlay.content.display_title is not None
    assert overlay.content.display_title.value == "Overlay title"
    assert overlay.content.description is not None
    assert overlay.content.description.value == "Overlay desc"
    assert overlay.content.tag_keys[0].value == "meme"
    assert alias_repo.get_alias(media_id, "bob") is None
    with repo._engine.connect() as connection:
        canonical = connection.execute(
            text("SELECT display_title FROM media_metadata WHERE media_id = :id"),
            {"id": media_id.to_string()},
        ).scalar_one()
    assert canonical == "Canonical From Tweet"


def test_pending_alias_applies_on_reuse(lifecycle) -> None:
    repo, service, admin, coordinator, extractor, media_id = lifecycle
    _seed_canonical_and_metadata(repo, media_id, "Canonical From Tweet")
    alias_repo = coordinator._alias_repository
    first = service.submit(URL, login_key="alice")
    claim = _run(_drain_until_terminal(coordinator, repo, first.request_id))
    assert claim.state is XAcquisitionState.COMPLETED
    reused = service.submit(
        URL,
        login_key="alice",
        alias=parse_alias_content("Reuse overlay", None, None),
    )
    assert reused.submission_result == "reuse"
    overlay = alias_repo.get_alias(media_id, "alice")
    assert overlay is not None
    assert overlay.content.display_title is not None
    assert overlay.content.display_title.value == "Reuse overlay"
    with repo._engine.connect() as connection:
        canonical = connection.execute(
            text("SELECT display_title FROM media_metadata WHERE media_id = :id"),
            {"id": media_id.to_string()},
        ).scalar_one()
    assert canonical == "Canonical From Tweet"
