"""Application service and lifecycle coordinator for YouTube manual ingestion."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Callable
from dataclasses import dataclass
import time

from framenest.application.ports.upload_publications import (
    UploadPublicationCandidate,
    UploadPublicationRepository,
)
from framenest.application.ports.upload_sessions import UploadSessionRepository
from framenest.application.ports.youtube_acquisition_claims import (
    FrameNestYouTubeClaimRepositoryError,
    YouTubeAcquisitionClaimRepository,
)
from framenest.application.ports.youtube_downloader import (
    YouTubeDownloadError,
    YouTubeDownloader,
    YouTubeDownloaderConfigurationError,
    YouTubeDownloadPlan,
    YouTubeInspection,
    YouTubeInspectionError,
)
from framenest.application.ports.youtube_staging import (
    YouTubeStagingError,
    YouTubeStagingStorage,
)
from framenest.application.upload_transport import (
    UploadDuplicateResolution,
    UploadTransportError,
    UploadTransportService,
)
from framenest.domain.identities import (
    MediaId,
    MediaLocationId,
    YouTubeAcquisitionClaimId,
)
from framenest.domain.media_classification import AcquisitionSource, ContentCategory
from framenest.domain.uploads import (
    UploadSession,
    UploadSessionId,
    UploadSessionState,
    UploadStorageKey,
)
from framenest.domain.youtube_acquisition import (
    ACTIVE_YOUTUBE_ACQUISITION_STATES,
    TERMINAL_YOUTUBE_ACQUISITION_STATES,
    FrameNestYouTubeAcquisitionError,
    YouTubeAcquisitionClaim,
    YouTubeAcquisitionState,
    YouTubeConfirmationMethod,
    YouTubeFailureStage,
    YouTubeStagingCleanupState,
    canonicalize_youtube_url,
)

DEFAULT_ACQUISITION_POLL_INTERVAL_SECONDS = 0.25
DEFAULT_ACQUISITION_BATCH_SIZE = 32


class YouTubeAcquisitionError(RuntimeError):
    """Sanitized base application failure."""


class YouTubeAcquisitionNotFoundError(YouTubeAcquisitionError):
    """Requested durable claim does not exist."""


class YouTubeAcquisitionStateConflictError(YouTubeAcquisitionError):
    """Requested operation is incompatible with current claim state."""


class YouTubeAcquisitionInfrastructureError(YouTubeAcquisitionError):
    """Required durable or filesystem infrastructure is unavailable."""


class YouTubeAcquisitionInvalidRequestError(YouTubeAcquisitionError):
    """Submitted URL or confirmation data is outside the accepted policy."""


@dataclass(frozen=True, slots=True)
class YouTubeClaimSnapshot:
    """Operator-safe durable claim projection."""

    id: str
    state: str
    acquisition_source: str
    youtube_video_id: str
    upload_id: str | None
    upload_state: str | None
    media_id: str | None
    media_location_id: str | None
    result: str | None
    downloaded_size_bytes: int | None
    failure_stage: str | None
    failure_code: str | None
    cleanup_state: str
    retry_of_claim_id: str | None
    resolved_claim_id: str | None
    created_at_ms: int
    updated_at_ms: int
    completed_at_ms: int | None
    version: int


@dataclass(frozen=True, slots=True)
class YouTubeClaimSubmission:
    """Submission result distinguishing a newly persisted claim from reuse."""

    snapshot: YouTubeClaimSnapshot
    created: bool


def default_now_ms() -> int:
    return int(time.time() * 1_000)


class YouTubeAcquisitionService:
    """Create, read, and explicitly retry durable owner-confirmed claims."""

    def __init__(
        self,
        repository: YouTubeAcquisitionClaimRepository,
        upload_repository: UploadSessionRepository,
        staging: YouTubeStagingStorage,
        *,
        now_ms: Callable[[], int] = default_now_ms,
        notifier: object | None = None,
    ) -> None:
        self._repository = repository
        self._upload_repository = upload_repository
        self._staging = staging
        self._now_ms = now_ms
        self._notifier = notifier

    def submit(
        self,
        *,
        submitted_url: str,
        confirmation_method: YouTubeConfirmationMethod,
    ) -> YouTubeClaimSubmission:
        now_ms = self._now_ms()
        try:
            claim = YouTubeAcquisitionClaim.new(
                submitted_url=submitted_url,
                confirmation_method=confirmation_method,
                now_ms=now_ms,
            )
        except FrameNestYouTubeAcquisitionError as exc:
            raise YouTubeAcquisitionInvalidRequestError(
                "Invalid public YouTube video URL."
            ) from exc
        try:
            existing = self._repository.find_latest_cataloged_by_source_identity(
                extractor_key=claim.extractor_key,
                youtube_video_id=claim.youtube_video_id,
            )
            if (
                existing is not None
                and existing.media_id is not None
                and existing.media_location_id is not None
            ):
                reused = claim.advance(
                    YouTubeAcquisitionState.DUPLICATE_RESOLVED,
                    updated_at_ms=now_ms,
                    resolved_claim_id=existing.id,
                    media_id=existing.media_id,
                    media_location_id=existing.media_location_id,
                    completed_at_ms=now_ms,
                    cleanup_state=YouTubeStagingCleanupState.COMPLETE,
                    cleanup_completed_at_ms=now_ms,
                )
                self._repository.create(reused)
                return YouTubeClaimSubmission(
                    snapshot=self._snapshot(reused),
                    created=True,
                )
            selected, created = self._repository.create_or_get_active(claim)
        except (
            FrameNestYouTubeClaimRepositoryError,
        ) as exc:
            raise YouTubeAcquisitionInfrastructureError(
                "YouTube acquisition is unavailable."
            ) from exc
        if created:
            _notify(self._notifier)
        return YouTubeClaimSubmission(
            snapshot=self._snapshot(selected),
            created=created,
        )

    def get(
        self,
        claim_id: YouTubeAcquisitionClaimId,
    ) -> YouTubeClaimSnapshot:
        try:
            claim = self._repository.get(claim_id)
        except FrameNestYouTubeClaimRepositoryError as exc:
            raise YouTubeAcquisitionInfrastructureError(
                "YouTube acquisition is unavailable."
            ) from exc
        if claim is None:
            raise YouTubeAcquisitionNotFoundError(
                "YouTube acquisition claim not found."
            )
        return self._snapshot(claim)

    def retry(
        self,
        claim_id: YouTubeAcquisitionClaimId,
        *,
        confirmation_method: YouTubeConfirmationMethod,
    ) -> YouTubeClaimSubmission:
        try:
            original = self._repository.get(claim_id)
            if original is None:
                raise YouTubeAcquisitionNotFoundError(
                    "YouTube acquisition claim not found."
                )
            if original.state is not YouTubeAcquisitionState.FAILED:
                raise YouTubeAcquisitionStateConflictError(
                    "YouTube acquisition claim cannot be retried."
                )
            if original.cleanup_state is YouTubeStagingCleanupState.PENDING:
                self._staging.cleanup(original.staging_key)
                now_ms = self._now_ms()
                cleaned = original.evolve(
                    updated_at_ms=now_ms,
                    cleanup_state=YouTubeStagingCleanupState.COMPLETE,
                    cleanup_completed_at_ms=now_ms,
                )
                original = self._repository.save(
                    cleaned,
                    expected_state=original.state,
                    expected_version=original.version,
                )
            now_ms = self._now_ms()
            retry = YouTubeAcquisitionClaim.new(
                submitted_url=original.submitted_url,
                confirmation_method=confirmation_method,
                now_ms=now_ms,
                retry_of_claim_id=original.id,
            )
            selected, created = self._repository.create_or_get_active(retry)
        except (
            YouTubeAcquisitionNotFoundError,
            YouTubeAcquisitionStateConflictError,
        ):
            raise
        except (
            FrameNestYouTubeClaimRepositoryError,
            YouTubeStagingError,
        ) as exc:
            raise YouTubeAcquisitionInfrastructureError(
                "YouTube acquisition is unavailable."
            ) from exc
        if created:
            _notify(self._notifier)
        return YouTubeClaimSubmission(
            snapshot=self._snapshot(selected),
            created=created,
        )

    def _snapshot(
        self,
        claim: YouTubeAcquisitionClaim,
    ) -> YouTubeClaimSnapshot:
        upload_state = None
        if claim.upload_id is not None:
            try:
                upload = self._upload_repository.get(claim.upload_id)
            except Exception as exc:
                raise YouTubeAcquisitionInfrastructureError(
                    "YouTube acquisition is unavailable."
                ) from exc
            upload_state = None if upload is None else upload.state.value
        result = None
        if claim.state is YouTubeAcquisitionState.CATALOGED:
            result = "new"
        elif claim.state is YouTubeAcquisitionState.DUPLICATE_RESOLVED:
            result = "reused"
        return YouTubeClaimSnapshot(
            id=claim.id.to_string(),
            state=claim.state.value,
            acquisition_source=claim.acquisition_source.value,
            youtube_video_id=claim.youtube_video_id,
            upload_id=_identity_text(claim.upload_id),
            upload_state=upload_state,
            media_id=_identity_text(claim.media_id),
            media_location_id=_identity_text(claim.media_location_id),
            result=result,
            downloaded_size_bytes=claim.downloaded_size_bytes,
            failure_stage=None
            if claim.failure_stage is None
            else claim.failure_stage.value,
            failure_code=claim.failure_code,
            cleanup_state=claim.cleanup_state.value,
            retry_of_claim_id=_identity_text(claim.retry_of_claim_id),
            resolved_claim_id=_identity_text(claim.resolved_claim_id),
            created_at_ms=claim.created_at_ms,
            updated_at_ms=claim.updated_at_ms,
            completed_at_ms=claim.completed_at_ms,
            version=claim.version,
        )


class YouTubeAcquisitionCoordinator:
    """Sequential durable acquisition owner for the single-worker server."""

    def __init__(
        self,
        repository: YouTubeAcquisitionClaimRepository,
        downloader: YouTubeDownloader,
        staging: YouTubeStagingStorage,
        transport: UploadTransportService,
        upload_repository: UploadSessionRepository,
        publication_repository: UploadPublicationRepository,
        *,
        validation_coordinator: object | None,
        publication_coordinator: object | None,
        chunk_size_bytes: int,
        now_ms: Callable[[], int] = default_now_ms,
        poll_interval_seconds: float = DEFAULT_ACQUISITION_POLL_INTERVAL_SECONDS,
        batch_size: int = DEFAULT_ACQUISITION_BATCH_SIZE,
    ) -> None:
        if (
            isinstance(chunk_size_bytes, bool)
            or not isinstance(chunk_size_bytes, int)
            or chunk_size_bytes <= 0
        ):
            raise ValueError("YouTube handoff chunk size must be positive")
        if (
            isinstance(poll_interval_seconds, bool)
            or poll_interval_seconds < 0
        ):
            raise ValueError("YouTube acquisition poll interval is invalid")
        if isinstance(batch_size, bool) or batch_size <= 0:
            raise ValueError("YouTube acquisition batch size must be positive")
        self._repository = repository
        self._downloader = downloader
        self._staging = staging
        self._transport = transport
        self._upload_repository = upload_repository
        self._publication_repository = publication_repository
        self._validation_coordinator = validation_coordinator
        self._publication_coordinator = publication_coordinator
        self._chunk_size_bytes = chunk_size_bytes
        self._now_ms = now_ms
        self._poll_interval_seconds = float(poll_interval_seconds)
        self._batch_size = batch_size
        self._runner: asyncio.Task[None] | None = None
        self._wake: asyncio.Event | None = None
        self._stopping = False
        self._startup_reconciled = False

    async def start(self) -> None:
        if self._runner is not None:
            if self._runner.done() and not self._stopping:
                raise RuntimeError("YouTube acquisition runner is not active")
            return
        self._stopping = False
        self._wake = asyncio.Event()
        await self._reconcile_startup()
        self._runner = asyncio.create_task(
            self._run(),
            name="framenest-youtube-acquisition-coordinator",
        )
        self.notify()

    def notify(self) -> None:
        if self._runner is not None and self._runner.done() and not self._stopping:
            raise RuntimeError("YouTube acquisition runner is not active")
        if self._wake is not None and not self._stopping:
            self._wake.set()

    async def drain(self) -> None:
        if not self._startup_reconciled:
            await self._reconcile_startup()
        await self._drain_once()

    async def shutdown(self) -> None:
        self._stopping = True
        if self._wake is not None:
            self._wake.set()
        runner = self._runner
        if runner is not None and not runner.done():
            runner.cancel()
        try:
            if runner is not None:
                await runner
        except asyncio.CancelledError:
            pass
        finally:
            self._runner = None
            self._wake = None

    @property
    def runner_done(self) -> bool:
        return self._runner is None or self._runner.done()

    async def _run(self) -> None:
        assert self._wake is not None
        while not self._stopping:
            try:
                progressed = await self._drain_once()
            except asyncio.CancelledError:
                raise
            except Exception:
                progressed = False
            if self._stopping:
                return
            if progressed:
                # Durable steps may complete synchronously with a fake adapter or
                # local filesystem I/O. Yield so API requests and downstream
                # lifecycle coordinators cannot be starved by the recovery loop.
                await asyncio.sleep(0)
                continue
            try:
                await asyncio.wait_for(
                    self._wake.wait(),
                    timeout=self._poll_interval_seconds,
                )
            except TimeoutError:
                pass
            finally:
                self._wake.clear()

    async def _reconcile_startup(self) -> None:
        if self._startup_reconciled:
            return
        candidates: list[YouTubeAcquisitionClaim] = []
        after_updated_at_ms: int | None = None
        after_id: str | None = None
        while True:
            page = self._repository.list_recovery_candidates(
                limit=self._batch_size,
                after_updated_at_ms=after_updated_at_ms,
                after_id=after_id,
            )
            if not page:
                break
            candidates.extend(page)
            last = page[-1]
            after_updated_at_ms = last.updated_at_ms
            after_id = last.id.to_string()
        current_version: str | None = None
        for claim in candidates:
            if claim.state is YouTubeAcquisitionState.INSPECTING:
                recovered = claim.advance(
                    YouTubeAcquisitionState.CLAIMED,
                    updated_at_ms=self._now_ms(),
                )
                self._save(claim, recovered)
                continue
            if claim.state in {
                YouTubeAcquisitionState.DOWNLOAD_PENDING,
                YouTubeAcquisitionState.DOWNLOADING,
            }:
                if current_version is None:
                    try:
                        current_version = await self._downloader.attest_version()
                    except YouTubeDownloaderConfigurationError as exc:
                        await self._fail(
                            claim,
                            stage=YouTubeFailureStage.CONFIGURATION,
                            code=exc.code,
                        )
                        continue
                if claim.downloader_version != current_version:
                    try:
                        self._staging.cleanup(claim.staging_key)
                    except YouTubeStagingError:
                        await self._fail(
                            claim,
                            stage=YouTubeFailureStage.CLEANUP,
                            code="STAGING_CLEANUP_FAILED",
                        )
                        continue
                    restarted = claim.advance(
                        YouTubeAcquisitionState.CLAIMED,
                        updated_at_ms=self._now_ms(),
                        upstream_title=None,
                        upstream_channel=None,
                        upstream_channel_id=None,
                        upstream_source_date=None,
                        downloader_name=None,
                        downloader_version=None,
                        extractor_version=None,
                        selected_video_format_id=None,
                        selected_audio_format_id=None,
                        remote_filename=None,
                    )
                    self._save(claim, restarted)
                elif claim.state is YouTubeAcquisitionState.DOWNLOADING:
                    resumed = claim.advance(
                        YouTubeAcquisitionState.DOWNLOAD_PENDING,
                        updated_at_ms=self._now_ms(),
                    )
                    self._save(claim, resumed)
        self._startup_reconciled = True

    async def _drain_once(self) -> bool:
        cleanup_candidates = self._repository.list_cleanup_candidates(
            limit=self._batch_size
        )
        if cleanup_candidates:
            for claim in cleanup_candidates:
                self._cleanup(claim)
            return True
        candidates = self._repository.list_recovery_candidates(
            limit=self._batch_size
        )
        if not candidates:
            return False
        await self._process(candidates[0])
        return True

    async def _process(self, claim: YouTubeAcquisitionClaim) -> None:
        try:
            if claim.state is YouTubeAcquisitionState.CLAIMED:
                await self._inspect(claim)
            elif claim.state is YouTubeAcquisitionState.DOWNLOAD_PENDING:
                await self._download(claim)
            elif claim.state is YouTubeAcquisitionState.DOWNLOADED:
                handoff = claim.advance(
                    YouTubeAcquisitionState.HANDOFF,
                    updated_at_ms=self._now_ms(),
                )
                self._save(claim, handoff)
            elif claim.state is YouTubeAcquisitionState.HANDOFF:
                await self._handoff(claim)
            elif claim.state is YouTubeAcquisitionState.HANDED_OFF:
                await self._project_upload(claim)
            elif claim.state is YouTubeAcquisitionState.DOWNLOADING:
                resumed = claim.advance(
                    YouTubeAcquisitionState.DOWNLOAD_PENDING,
                    updated_at_ms=self._now_ms(),
                )
                self._save(claim, resumed)
            elif claim.state is YouTubeAcquisitionState.INSPECTING:
                recovered = claim.advance(
                    YouTubeAcquisitionState.CLAIMED,
                    updated_at_ms=self._now_ms(),
                )
                self._save(claim, recovered)
        except YouTubeDownloaderConfigurationError as exc:
            await self._fail(
                claim,
                stage=YouTubeFailureStage.CONFIGURATION,
                code=exc.code,
            )
        except YouTubeInspectionError as exc:
            await self._fail(
                claim,
                stage=YouTubeFailureStage.INSPECTION,
                code=exc.code,
            )
        except YouTubeDownloadError as exc:
            await self._fail(
                claim,
                stage=YouTubeFailureStage.DOWNLOAD,
                code=exc.code,
            )
        except UploadTransportError:
            await self._fail(
                claim,
                stage=YouTubeFailureStage.HANDOFF,
                code="UPLOAD_HANDOFF_FAILED",
            )
        except (
            FrameNestYouTubeClaimRepositoryError,
            YouTubeStagingError,
        ):
            return
        except Exception:
            await self._fail(
                claim,
                stage=YouTubeFailureStage.INTERNAL,
                code="INTERNAL_ERROR",
            )

    async def _inspect(self, claim: YouTubeAcquisitionClaim) -> None:
        inspecting = claim.advance(
            YouTubeAcquisitionState.INSPECTING,
            updated_at_ms=self._now_ms(),
        )
        inspecting = self._save(claim, inspecting)
        identity = canonicalize_youtube_url(inspecting.canonical_url)
        inspection = await self._downloader.inspect(identity)
        pending = inspecting.advance(
            YouTubeAcquisitionState.DOWNLOAD_PENDING,
            updated_at_ms=self._now_ms(),
            upstream_title=inspection.title,
            upstream_channel=inspection.channel,
            upstream_channel_id=inspection.channel_id,
            upstream_source_date=inspection.source_date,
            downloader_name="yt-dlp",
            downloader_version=inspection.downloader_version,
            extractor_version=inspection.extractor_version,
            selected_video_format_id=inspection.plan.video_format_id,
            selected_audio_format_id=inspection.plan.audio_format_id,
            remote_filename=inspection.remote_filename,
        )
        self._save(inspecting, pending)

    async def _download(self, claim: YouTubeAcquisitionClaim) -> None:
        identity = canonicalize_youtube_url(claim.canonical_url)
        if (
            claim.downloader_version is None
            or claim.extractor_version is None
            or claim.selected_video_format_id is None
        ):
            raise YouTubeDownloadError("INSPECTION_EVIDENCE_MISSING")
        inspection = YouTubeInspection(
            video_id=claim.youtube_video_id,
            extractor_key=claim.extractor_key,
            title=claim.upstream_title,
            channel=claim.upstream_channel,
            channel_id=claim.upstream_channel_id,
            source_date=claim.upstream_source_date,
            remote_filename=claim.remote_filename,
            duration_seconds=1.0,
            downloader_version=claim.downloader_version,
            extractor_version=claim.extractor_version,
            plan=YouTubeDownloadPlan(
                video_format_id=claim.selected_video_format_id,
                audio_format_id=claim.selected_audio_format_id,
                expected_size_bytes=None,
                has_source_audio=claim.selected_audio_format_id is not None,
                split_streams=claim.selected_audio_format_id is not None,
            ),
        )
        downloading = claim.advance(
            YouTubeAcquisitionState.DOWNLOADING,
            updated_at_ms=self._now_ms(),
        )
        downloading = self._save(claim, downloading)
        result = await self._downloader.download(
            identity,
            inspection,
            staging_key=downloading.staging_key,
        )
        downloaded = downloading.advance(
            YouTubeAcquisitionState.DOWNLOADED,
            updated_at_ms=self._now_ms(),
            downloaded_size_bytes=result.size_bytes,
            downloaded_at_ms=self._now_ms(),
        )
        self._save(downloading, downloaded)

    async def _handoff(self, claim: YouTubeAcquisitionClaim) -> None:
        if claim.downloaded_size_bytes is None:
            raise UploadTransportError("upload handoff failed")
        upload_id = UploadSessionId.from_string(claim.id.to_string())
        upload_storage_key = UploadStorageKey(claim.staging_key)
        snapshot = self._transport.create_session(
            display_filename=claim.generated_filename,
            declared_size_bytes=claim.downloaded_size_bytes,
            session_id=upload_id,
            storage_key=upload_storage_key,
        )
        current = claim
        if current.upload_id is None:
            linked = current.evolve(
                updated_at_ms=self._now_ms(),
                upload_id=upload_id,
            )
            current = self._save(current, linked)
        reader = self._staging.open_artifact(
            claim.staging_key,
            expected_size_bytes=claim.downloaded_size_bytes,
        )
        try:
            while snapshot.received_size_bytes < claim.downloaded_size_bytes:
                reader.verify_still_consistent()
                reader.seek(snapshot.received_size_bytes)
                chunk = reader.read(
                    min(
                        self._chunk_size_bytes,
                        claim.downloaded_size_bytes
                        - snapshot.received_size_bytes,
                    )
                )
                if not chunk:
                    raise UploadTransportError("upload handoff failed")
                snapshot = await self._transport.receive_chunk(
                    upload_id,
                    upload_offset=snapshot.received_size_bytes,
                    content_length=len(chunk),
                    body=_one_chunk(chunk),
                )
            reader.verify_still_consistent()
        finally:
            reader.close()
        if snapshot.state in {
            UploadSessionState.CREATED.value,
            UploadSessionState.RECEIVING.value,
        }:
            snapshot = await self._transport.complete(upload_id)
        if (
            snapshot.received_size_bytes != claim.downloaded_size_bytes
            or snapshot.state
            not in {state.value for state in UploadSessionState}
            - {
                UploadSessionState.CREATED.value,
                UploadSessionState.RECEIVING.value,
            }
        ):
            raise UploadTransportError("upload handoff failed")
        _notify(self._validation_coordinator)
        handed_off = current.advance(
            YouTubeAcquisitionState.HANDED_OFF,
            updated_at_ms=self._now_ms(),
        )
        handed_off = self._save(current, handed_off)
        self._cleanup(handed_off)

    async def _project_upload(self, claim: YouTubeAcquisitionClaim) -> None:
        if claim.cleanup_state is YouTubeStagingCleanupState.PENDING:
            claim = self._cleanup(claim)
        if claim.upload_id is None:
            raise UploadTransportError("upload handoff failed")
        upload = self._upload_repository.get(claim.upload_id)
        if upload is None:
            raise UploadTransportError("upload handoff failed")
        if upload.state in {
            UploadSessionState.RECEIVED,
            UploadSessionState.VALIDATING,
        }:
            _notify(self._validation_coordinator)
            return
        if upload.state in {
            UploadSessionState.PUBLISH_PENDING,
            UploadSessionState.PUBLISHED,
        }:
            _notify(self._publication_coordinator)
            return
        if upload.state is UploadSessionState.CATALOGED:
            candidate = self._publication_repository.get_candidate(upload.id)
            self._complete_cataloged(claim, candidate)
            return
        if upload.state in {
            UploadSessionState.DUPLICATE_PENDING,
            UploadSessionState.CANCELLED,
        }:
            if await self._resolve_byte_duplicate(claim, upload):
                return
            if upload.state is UploadSessionState.DUPLICATE_PENDING:
                return
        failure_code = {
            UploadSessionState.REJECTED: "UPLOAD_REJECTED",
            UploadSessionState.FAILED: "UPLOAD_FAILED",
            UploadSessionState.EXPIRED: "UPLOAD_EXPIRED",
            UploadSessionState.CANCELLED: "UPLOAD_CANCELLED",
        }.get(upload.state, "UPLOAD_STATE_INCONSISTENT")
        await self._fail(
            claim,
            stage=YouTubeFailureStage.DOWNSTREAM,
            code=failure_code,
        )

    async def _resolve_byte_duplicate(
        self,
        claim: YouTubeAcquisitionClaim,
        upload: UploadSession,
    ) -> bool:
        if upload.byte_identity_id is None:
            return False
        canonical = (
            self._publication_repository.find_cataloged_by_byte_identity(
                upload.byte_identity_id,
                exclude_upload_id=upload.id,
            )
        )
        if (
            canonical is None
            or canonical.publication is None
            or canonical.publication.media_id is None
            or canonical.publication.media_location_id is None
        ):
            return False
        if upload.state is UploadSessionState.DUPLICATE_PENDING:
            await self._transport.resolve_duplicate(
                upload.id,
                UploadDuplicateResolution.DISCARD,
            )
        resolved_claim = self._repository.find_by_upload_id(
            canonical.upload.id
        )
        completed = claim.advance(
            YouTubeAcquisitionState.DUPLICATE_RESOLVED,
            updated_at_ms=self._now_ms(),
            resolved_claim_id=None
            if resolved_claim is None
            else resolved_claim.id,
            media_id=canonical.publication.media_id,
            media_location_id=canonical.publication.media_location_id,
            completed_at_ms=self._now_ms(),
        )
        self._save(claim, completed)
        return True

    def _complete_cataloged(
        self,
        claim: YouTubeAcquisitionClaim,
        candidate: UploadPublicationCandidate | None,
    ) -> None:
        if (
            candidate is None
            or candidate.publication is None
            or candidate.publication.media_id is None
            or candidate.publication.media_location_id is None
        ):
            raise YouTubeAcquisitionInfrastructureError(
                "YouTube acquisition is unavailable."
            )
        completed = claim.advance(
            YouTubeAcquisitionState.CATALOGED,
            updated_at_ms=self._now_ms(),
            media_id=candidate.publication.media_id,
            media_location_id=candidate.publication.media_location_id,
            completed_at_ms=self._now_ms(),
        )
        self._save(claim, completed)

    async def _fail(
        self,
        observed: YouTubeAcquisitionClaim,
        *,
        stage: YouTubeFailureStage,
        code: str,
    ) -> None:
        try:
            current = self._repository.get(observed.id)
            if current is None or current.state in TERMINAL_YOUTUBE_ACQUISITION_STATES:
                return
            failed = current.advance(
                YouTubeAcquisitionState.FAILED,
                updated_at_ms=self._now_ms(),
                failure_stage=stage,
                failure_code=code,
                completed_at_ms=self._now_ms(),
            )
            failed = self._save(current, failed)
            try:
                self._cleanup(failed)
            except (
                FrameNestYouTubeClaimRepositoryError,
                YouTubeStagingError,
            ):
                return
        except (
            FrameNestYouTubeClaimRepositoryError,
            FrameNestYouTubeAcquisitionError,
        ):
            return

    def _cleanup(
        self,
        claim: YouTubeAcquisitionClaim,
    ) -> YouTubeAcquisitionClaim:
        if claim.cleanup_state is YouTubeStagingCleanupState.COMPLETE:
            return claim
        self._staging.cleanup(claim.staging_key)
        cleaned = claim.evolve(
            updated_at_ms=self._now_ms(),
            cleanup_state=YouTubeStagingCleanupState.COMPLETE,
            cleanup_completed_at_ms=self._now_ms(),
        )
        return self._save(claim, cleaned)

    def _save(
        self,
        previous: YouTubeAcquisitionClaim,
        updated: YouTubeAcquisitionClaim,
    ) -> YouTubeAcquisitionClaim:
        return self._repository.save(
            updated,
            expected_state=previous.state,
            expected_version=previous.version,
        )


def youtube_classification_for_upload(
    repository: YouTubeAcquisitionClaimRepository,
    upload_id: UploadSessionId,
) -> tuple[ContentCategory, AcquisitionSource] | None:
    """Return sparse catalog defaults only for a linked YouTube claim."""
    claim = repository.find_by_upload_id(upload_id)
    if claim is None:
        return None
    return ContentCategory.GENERAL, AcquisitionSource.YOUTUBE_MANUAL_CLAIM


def automatic_analysis_allowed_for_upload(
    repository: YouTubeAcquisitionClaimRepository,
    upload_id: UploadSessionId,
) -> bool:
    """Fail closed for linked YouTube acquisitions, even when globally enabled."""
    return repository.find_by_upload_id(upload_id) is None


async def _one_chunk(chunk: bytes) -> AsyncIterator[bytes]:
    yield chunk


def _identity_text(value: object) -> str | None:
    if value is None:
        return None
    to_string = getattr(value, "to_string", None)
    if not callable(to_string):
        raise YouTubeAcquisitionInfrastructureError(
            "YouTube acquisition is unavailable."
        )
    return str(to_string())


def _notify(coordinator: object | None) -> None:
    if coordinator is None:
        return
    try:
        notify = getattr(coordinator, "notify")
        notify()
    except Exception:
        return
