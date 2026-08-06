"""Application service and lifecycle coordinator for requester-private X.

X acquisition is a bounded requester-private candidate. It reuses the proven
YouTube requester-ownership, admission-limit, recovery, staging and
catalog-handoff discipline without generalizing the YouTube implementation.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Callable
from dataclasses import dataclass
import hashlib
import time

from framenest.application.ports.upload_publications import (
    UploadPublicationCandidate,
    UploadPublicationRepository,
)
from framenest.application.ports.upload_sessions import UploadSessionRepository
from framenest.application.ports.x_acquisition import (
    FrameNestXClaimRepositoryError,
    XAcquisitionClaimRepository,
    XClaimConcurrencyConflictError,
    XClaimNotFoundError,
    XClaimSourceIdentityConflictError,
)
from framenest.application.ports.x_extractor import (
    XExtractionError,
    XExtractor,
    XExtractorConfigurationError,
)
from framenest.application.upload_catalog import CatalogUploadClassification
from framenest.application.upload_transport import (
    UploadTransportError,
    UploadTransportService,
)
from framenest.domain.identities import MediaId, MediaLocationId, XPostClaimId
from framenest.domain.media_classification import (
    AcquisitionSource,
    ContentCategory,
    CreatorAttributionKind,
)
from framenest.domain.media_metadata import (
    MAX_DISPLAY_TITLE_CODE_POINTS,
    FrameNestMediaMetadataError,
    MediaDisplayTitle,
)
from framenest.domain.uploads import (
    UploadDuplicateResolutionMode,
    UploadSessionId,
    UploadSessionState,
    UploadStorageKey,
)
from framenest.domain.x_acquisition import (
    ACTIVE_X_ACQUISITION_STATES,
    LIVE_CATALOG_X_ACQUISITION_STATES,
    KNOWN_X_FAILURE_CODES,
    MAX_ASSETS_PER_POST,
    MAX_CLAIM_BYTES,
    MAX_CLAIM_STAGING_FOOTPRINT_BYTES,
    REQUESTER_PHASE_COMPLETED,
    SUCCESS_X_ACQUISITION_STATES,
    TERMINAL_X_ACQUISITION_STATES,
    FrameNestXAcquisitionError,
    XAcquisitionState,
    XAsset,
    XAssetState,
    XFailureStage,
    XMediaType,
    XPostClaim,
    XStagingCleanupState,
    accept_x_post_url,
    default_x_category,
    derive_x_requester_phase,
    ensure_x_asset_transition_allowed,
    ensure_x_transition_allowed,
    is_retryable_x_failure,
    normalize_x_creator,
    x_title_from_post_post,
)

DEFAULT_ACQUISITION_POLL_INTERVAL_SECONDS = 0.25
DEFAULT_ACQUISITION_BATCH_SIZE = 32
MS_PER_HOUR = 3_600_000
MS_PER_DAY = 86_400_000


class XAcquisitionError(RuntimeError):
    """Sanitized base application failure."""


class XAcquisitionNotFoundError(XAcquisitionError):
    """Requested durable claim or asset does not exist."""


class XAcquisitionStateConflictError(XAcquisitionError):
    """Requested operation is incompatible with current durable state."""


class XAcquisitionInfrastructureError(XAcquisitionError):
    """Required durable or filesystem infrastructure is unavailable."""


class XAcquisitionInvalidRequestError(XAcquisitionError):
    """Submitted URL is outside the accepted X post policy."""


class XRequestLimitError(XAcquisitionError):
    """Ordinary requester admission limit was reached."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


class XRequestInsufficientStorageError(XAcquisitionError):
    """Ordinary requester admission failed the free-space gate."""


@dataclass(frozen=True, slots=True)
class XAssetSnapshot:
    """Sanitized requester/admin asset projection."""

    asset_id: str
    ordinal: int
    media_type: str
    state: str
    acquired_bytes: int | None
    media_id: str | None
    failure_stage: str | None
    failure_code: str | None
    created_at_ms: int
    updated_at_ms: int


@dataclass(frozen=True, slots=True)
class XClaimSnapshot:
    """Sanitized durable projection shared by requester and administration."""

    claim_id: str
    state: str
    phase: str
    x_post_id: str
    submitted_url: str
    canonical_url: str
    title: str | None
    source_author_handle: str | None
    source_author_display_name: str | None
    discovered_asset_count: int
    success_count: int
    failure_count: int
    failure_stage: str | None
    failure_code: str | None
    retry_of_claim_id: str | None
    created_at_ms: int
    updated_at_ms: int
    completed_at_ms: int | None
    assets: tuple[XAssetSnapshot, ...] = ()


@dataclass(frozen=True, slots=True)
class XRequestSubmission:
    """Sanitized requester submit-result projection."""

    request_id: str
    submission_result: str
    phase: str
    x_post_id: str
    submitted_url: str


@dataclass(frozen=True, slots=True)
class XRequestPage:
    """Bounded requester claim listing."""

    items: tuple[XClaimSnapshot, ...]
    next_cursor: str | None


@dataclass(frozen=True, slots=True)
class XRequestLimits:
    """Bounded admission defaults for the X requester candidate."""

    max_assets_per_post: int = MAX_ASSETS_PER_POST
    max_video_duration_seconds: int = 300
    max_asset_bytes: int = 1_073_741_824
    max_claim_bytes: int = MAX_CLAIM_BYTES
    max_claim_staging_footprint_bytes: int = MAX_CLAIM_STAGING_FOOTPRINT_BYTES
    max_active_per_requester: int = 1
    max_global_active: int = 8
    max_submits_per_hour: int = 6
    max_failed_per_24h: int = 10
    min_free_space_reserve_bytes: int = 67_108_864
    free_space_bytes: Callable[[], int] | None = None


def default_now_ms() -> int:
    return int(time.time() * 1000)


class XAcquisitionAdministrationService:
    """Administrator review of requester-private X claims and resulting media."""

    def __init__(
        self,
        repository: XAcquisitionClaimRepository,
        *,
        now_ms: Callable[[], int] = default_now_ms,
    ) -> None:
        self._repository = repository
        self._now_ms = now_ms

    def get(self, claim_id: XPostClaimId) -> XClaimSnapshot:
        claim = self._repository.get_post(claim_id)
        if claim is None:
            raise XAcquisitionNotFoundError("X claim not found")
        assets = self._repository.list_assets_for_post(claim.id)
        return _administration_snapshot(claim, assets)

    def list(self) -> tuple[XClaimSnapshot, ...]:
        raise XAcquisitionInfrastructureError(
            "X administration listing is not enabled in this candidate."
        )


class XAcquisitionRequestService:
    """Ordinary requester admission and own-claim access."""

    def __init__(
        self,
        repository: XAcquisitionClaimRepository,
        *,
        limits: XRequestLimits,
        now_ms: Callable[[], int] = default_now_ms,
    ) -> None:
        self._repository = repository
        self._limits = limits
        self._now_ms = now_ms

    def submit(self, url: str, *, login_key: str) -> XRequestSubmission:
        identity = accept_x_post_url(url)
        requester = _normalize_requester(login_key)

        owned_successful = self._repository.find_owned_successful_by_post_id(
            post_id_key=identity.post_id,
            created_by_login_key=requester,
        )
        if owned_successful is not None:
            return _submission(
                owned_successful, submission_result="reuse", requester=requester
            )

        active = self._repository.find_active_by_post_id(
            post_id_key=identity.post_id,
            created_by_login_key=requester,
        )
        if active is not None:
            return _submission(active, submission_result="active_reuse", requester=requester)

        self._enforce_admission_limits(requester)

        claim = XPostClaim.new(
            submitted_url=url,
            now_ms=self._now_ms(),
            created_by_login_key=requester,
        )
        claim, created = self._repository.create_or_get_active(claim)
        if not created:
            _submission_result = "active_reuse"
        else:
            _submission_result = "new"
        return XRequestSubmission(
            request_id=claim.id.to_string(),
            submission_result=_submission_result,
            phase=derive_x_requester_phase(claim),
            x_post_id=claim.x_post_id,
            submitted_url=claim.submitted_url,
        )

    def list_owned(
        self,
        *,
        login_key: str,
        limit: int = 20,
        cursor: str | None = None,
    ) -> XRequestPage:
        requester = _normalize_requester(login_key)
        after_created_at_ms: int | None = None
        after_id: str | None = None
        if cursor:
            try:
                encoded, raw = cursor.split(":", 1)
                after_created_at_ms = int(encoded)
                after_id = raw
            except (ValueError, AttributeError):
                raise XAcquisitionInvalidRequestError(
                    "Invalid X request cursor."
                ) from None
        claims = self._repository.list_owned(
            created_by_login_key=requester,
            limit=limit + 1,
            after_created_at_ms=after_created_at_ms,
            after_id=after_id,
        )
        has_more = len(claims) > limit
        page = claims[:limit]
        next_cursor = None
        if has_more and page:
            last = page[-1]
            next_cursor = f"{last.created_at_ms}:{last.id.to_string()}"
        items = tuple(
            _requester_snapshot(claim, self._repository)
            for claim in page
        )
        return XRequestPage(items=items, next_cursor=next_cursor)

    def get_owned(self, claim_id: XPostClaimId, *, login_key: str) -> XClaimSnapshot:
        requester = _normalize_requester(login_key)
        claim = self._repository.get_owned_post(claim_id, created_by_login_key=requester)
        if claim is None:
            raise XAcquisitionNotFoundError("X claim not found")
        return _requester_snapshot(claim, self._repository)

    def retry(self, claim_id: XPostClaimId, *, login_key: str) -> XClaimSnapshot:
        requester = _normalize_requester(login_key)
        claim = self._repository.get_owned_post(claim_id, created_by_login_key=requester)
        if claim is None:
            raise XAcquisitionNotFoundError("X claim not found")
        if claim.state is not XAcquisitionState.FAILED and not (
            claim.state is XAcquisitionState.COMPLETED_PARTIAL
            and claim.failure_count > 0
        ):
            raise XAcquisitionStateConflictError(
                "X claim is not retryable in its current state."
            )
        assets = self._repository.list_assets_for_post(claim.id)
        retryable = [a for a in assets if _asset_retryable(a)]
        if not retryable:
            if claim.state is XAcquisitionState.FAILED:
                queued = claim.advance(
                    XAcquisitionState.QUEUED, updated_at_ms=self._now_ms()
                )
                self._save_claim(claim, queued)
                return _requester_snapshot(queued, self._repository)
            raise XAcquisitionStateConflictError(
                "X claim has no retryable assets."
            )
        # Reset retryable assets to pending for re-acquisition.
        for asset in retryable:
            reset = asset.advance(
                XAssetState.PENDING, updated_at_ms=self._now_ms(),
                failure_stage=None, failure_code=None,
            )
            self._save_asset(asset, reset)
        queued = claim.advance(XAcquisitionState.QUEUED, updated_at_ms=self._now_ms())
        updated = self._save_claim(claim, queued)
        return _requester_snapshot(updated, self._repository)

    def _enforce_admission_limits(self, requester: str) -> None:
        if self._limits.max_active_per_requester >= 0:
            active = self._repository.count_active_for_requester(
                created_by_login_key=requester
            )
            if active >= self._limits.max_active_per_requester:
                raise XRequestLimitError(
                    "X_REQUEST_ACTIVE_LIMIT",
                    "You already have an active X request.",
                )
        global_active = self._repository.count_global_active_ordinary()
        if global_active >= self._limits.max_global_active:
            raise XRequestLimitError(
                "X_REQUEST_GLOBAL_QUEUE_FULL", "X request queue is full."
            )
        since = self._now_ms() - MS_PER_HOUR
        submits = self._repository.count_submits_since(
            created_by_login_key=requester, since_ms=since
        )
        if submits >= self._limits.max_submits_per_hour:
            raise XRequestLimitError(
                "X_REQUEST_RATE_LIMIT", "Too many X requests this hour."
            )
        failed_since = self._now_ms() - MS_PER_DAY
        failed_count = self._repository.count_failed_transitions_since(
            created_by_login_key=requester, since_ms=failed_since
        )
        if failed_count >= self._limits.max_failed_per_24h:
            raise XRequestLimitError(
                "X_REQUEST_FAILED_24H_LIMIT", "Too many failed X requests."
            )
        if self._limits.free_space_bytes is not None:
            available = self._limits.free_space_bytes()
            if available <= self._limits.min_free_space_reserve_bytes:
                raise XRequestInsufficientStorageError(
                    "X staging has insufficient free space."
                )

    def _save_claim(
        self, previous: XPostClaim, updated: XPostClaim
    ) -> XPostClaim:
        return self._repository.save_post(
            updated,
            expected_state=previous.state,
            expected_version=previous.version,
        )

    def _save_asset(self, previous: XAsset, updated: XAsset) -> XAsset:
        return self._repository.save_asset(
            updated,
            expected_state=previous.state,
            expected_version=previous.version,
        )


class XAcquisitionCoordinator:
    """Single-worker async state machine for requester-private X claims."""

    def __init__(
        self,
        repository: XAcquisitionClaimRepository,
        extractor: XExtractor,
        staging: object,
        transport: UploadTransportService,
        upload_repository: UploadSessionRepository,
        publication_repository: UploadPublicationRepository,
        validation_coordinator: object,
        publication_coordinator: object,
        *,
        chunk_size_bytes: int = 1_048_576,
        poll_interval_seconds: float = DEFAULT_ACQUISITION_POLL_INTERVAL_SECONDS,
        batch_size: int = DEFAULT_ACQUISITION_BATCH_SIZE,
        now_ms: Callable[[], int] = default_now_ms,
    ) -> None:
        self._repository = repository
        self._extractor = extractor
        self._staging = staging
        self._transport = transport
        self._upload_repository = upload_repository
        self._publication_repository = publication_repository
        self._validation_coordinator = validation_coordinator
        self._publication_coordinator = publication_coordinator
        self._chunk_size_bytes = chunk_size_bytes
        self._poll_interval_seconds = poll_interval_seconds
        self._batch_size = batch_size
        self._now_ms = now_ms
        self._wake = asyncio.Event()
        self._runner_task: asyncio.Task | None = None
        self._shutdown_requested = False
        self._draining = False

    async def start(self) -> None:
        if self._runner_task is None:
            self._runner_task = asyncio.create_task(self._run())

    def notify(self) -> None:
        self._wake.set()

    async def drain(self) -> None:
        await self._drain_once()

    async def shutdown(self) -> None:
        self._shutdown_requested = True
        self._wake.set()
        if self._runner_task is not None:
            await self._runner_task
            self._runner_task = None

    @property
    def runner_done(self) -> bool:
        task = self._runner_task
        if task is None:
            return True
        return task.done()

    async def _run(self) -> None:
        while not self._shutdown_requested:
            progress = await self._drain_once()
            if progress:
                await asyncio.sleep(0)
            else:
                self._wake.clear()
                try:
                    await asyncio.wait_for(self._wake.wait(), self._poll_interval_seconds)
                except asyncio.TimeoutError:
                    pass

    async def _drain_once(self) -> bool:
        self._draining = True
        try:
            cleanup = self._repository.list_cleanup_candidates(limit=self._batch_size)
            for claim in cleanup:
                await self._reconcile_cleanup(claim)
            candidates = self._repository.list_recovery_candidates(limit=self._batch_size)
            if not candidates:
                return False
            for claim in candidates:
                await self._process(claim)
            return True
        finally:
            self._draining = False

    async def _process(self, claim: XPostClaim) -> None:
        try:
            if claim.state is XAcquisitionState.SUBMITTED:
                await self._queue(claim)
            elif claim.state is XAcquisitionState.QUEUED:
                await self._extract(claim)
            elif claim.state is XAcquisitionState.EXTRACTING:
                await self._extract(claim)
            elif claim.state is XAcquisitionState.ACQUIRING:
                await self._acquire(claim)
            elif claim.state is XAcquisitionState.HANDING_OFF:
                await self._handoff(claim)
        except Exception as exc:
            await self._fail(claim, stage=XFailureStage.INTERNAL, code=_code_from_exception(exc))

    async def _queue(self, claim: XPostClaim) -> None:
        queued = claim.advance(XAcquisitionState.QUEUED, updated_at_ms=self._now_ms())
        self._save(claim, queued)

    async def _extract(self, claim: XPostClaim) -> None:
        current = self._repository.get_post(claim.id)
        if current is None or current.state in TERMINAL_X_ACQUISITION_STATES:
            return
        if current.state is XAcquisitionState.QUEUED:
            current = self._save(
                current,
                current.advance(
                    XAcquisitionState.EXTRACTING, updated_at_ms=self._now_ms()
                ),
            )
        try:
            inspection = self._extractor.inspect(
                post_id=current.x_post_id, submitted_url=current.submitted_url
            )
        except XExtractionError as exc:
            stage = _stage_for_extractor_code(exc.code)
            await self._fail_with_assets(
                current, stage=stage, code=exc.code
            )
            return
        if inspection.failure_code is not None:
            await self._fail_with_assets(
                current, stage=XFailureStage.EXTRACTION, code=inspection.failure_code
            )
            return
        if not inspection.assets or len(inspection.assets) > MAX_ASSETS_PER_POST:
            code = (
                "X_TOO_MANY_ASSETS"
                if len(inspection.assets) > MAX_ASSETS_PER_POST
                else "X_NO_SUPPORTED_MEDIA"
            )
            await self._fail_with_assets(
                current, stage=XFailureStage.EXTRACTION, code=code
            )
            return
        canonical_url = current.canonical_url
        if inspection.canonical_url is not None:
            try:
                validated = accept_x_post_url(inspection.canonical_url)
                canonical_url = validated.canonical_url
            except FrameNestXAcquisitionError:
                canonical_url = current.canonical_url
        stable_id, handle, display = normalize_x_creator(
            stable_id=inspection.author_stable_id,
            handle=inspection.author_handle,
            display_name=inspection.author_display_name,
        )
        post_text = _bound_post_text(inspection.post_text)
        title = current.title
        creator_handle = handle or current.source_author_handle
        media_type_label = _media_type_label(inspection.assets[0].media_type)
        derived_title = x_title_from_post_post(
            post_text,
            creator_handle=creator_handle,
            media_type_label=media_type_label,
            post_id=current.x_post_id,
            ordinal=0,
        )
        ev = current.advance(
            XAcquisitionState.ACQUIRING,
            updated_at_ms=self._now_ms(),
            canonical_url=canonical_url,
            source_author_stable_id=stable_id,
            source_author_handle=handle,
            source_author_display_name=display,
            source_post_text=post_text,
            source_posted_at_ms=inspection.posted_at_ms,
            extractor_version=inspection.extractor_version,
            discovered_asset_count=len(inspection.assets),
            title=derived_title,
        )
        ev = self._save(current, ev)
        assets = tuple(
            XAsset.new(
                claim_id=ev.id,
                ordinal=desc.ordinal,
                media_type=desc.media_type,
                expected_mime=desc.expected_mime,
                now_ms=self._now_ms(),
                source_media_key=desc.source_media_key,
                width=desc.width,
                height=desc.height,
                duration_seconds=desc.duration_seconds,
                selected_variant=desc.selected_variant,
            )
            for desc in inspection.assets
        )
        self._repository.create_assets(assets)

    async def _acquire(self, claim: XPostClaim) -> None:
        assets = self._repository.list_assets_for_post(claim.id)
        pending = [a for a in assets if a.state in (XAssetState.PENDING, XAssetState.EXTRACTED)]
        if not pending:
            await self._advance_to_handoff(claim, assets)
            return
        asset = pending[0]
        if asset.state is XAssetState.PENDING:
            asset = self._save_asset(
                asset,
                asset.advance(XAssetState.EXTRACTED, updated_at_ms=self._now_ms()),
            )
        acquiring = asset.advance(XAssetState.ACQUIRING, updated_at_ms=self._now_ms())
        acquiring = self._save_asset(asset, acquiring)
        try:
            result = await self._acquire_one(claim, acquiring)
        except Exception as exc:
            await self._fail_asset(
                claim, acquiring, stage=XFailureStage.ACQUISITION,
                code=_code_from_exception(exc),
            )
            return
        staged = acquiring.advance(
            XAssetState.STAGED,
            updated_at_ms=self._now_ms(),
            acquired_bytes=result.size_bytes,
            acquired_sha256=result.sha256,
        )
        self._save_asset(acquiring, staged)
        await self._advance_to_handoff(claim, self._repository.list_assets_for_post(claim.id))

    async def _advance_to_handoff(self, claim: XPostClaim, assets: tuple[XAsset, ...]) -> None:
        if any(a.state in _AWAITING_ACQUISITION_ASSET_STATES for a in assets):
            return
        current = self._repository.get_post(claim.id)
        if current is None or current.state not in ACTIVE_X_ACQUISITION_STATES:
            return
        handoff_target = current.advance(
            XAcquisitionState.HANDING_OFF, updated_at_ms=self._now_ms()
        )
        self._save(current, handoff_target)

    async def _acquire_one(self, claim: XPostClaim, asset: XAsset) -> _Acquired:
        result = self._extractor.download(
            post_id=claim.x_post_id,
            ordinal=asset.ordinal,
            media_type=asset.media_type.value,
            expected_mime=asset.expected_mime,
            source_media_key=asset.source_media_key,
            stage_key=asset.stage_key,
            staging=self._staging,
        )
        if (
            not isinstance(result.size_bytes, int)
            or result.size_bytes <= 0
            or not isinstance(result.sha256, str)
            or len(result.sha256) != 64
        ):
            raise XAcquisitionInfrastructureError("X acquisition produced no bytes.")
        if result.size_bytes > 1_073_741_824:
            raise _AssetTooLarge()
        return _Acquired(size_bytes=result.size_bytes, sha256=result.sha256)

    async def _handoff(self, claim: XPostClaim) -> None:
        assets = self._repository.list_assets_for_post(claim.id)
        for asset in assets:
            if asset.state is XAssetState.STAGED:
                await self._handoff_asset(claim, asset)
                return
        for asset in assets:
            if asset.state is XAssetState.HANDING_OFF:
                await self._project_asset(claim, asset)
                return
        failed = [a for a in assets if a.state is XAssetState.FAILED]
        success = [a for a in assets if a.state is XAssetState.CATALOGED]
        current = self._repository.get_post(claim.id)
        if current is None or current.state not in ACTIVE_X_ACQUISITION_STATES:
            return
        updated = current.evolve(
            updated_at_ms=self._now_ms(),
            failure_count=len(failed),
            success_count=len(success),
        )
        if failed and not success:
            updated = updated.advance(
                XAcquisitionState.FAILED,
                updated_at_ms=self._now_ms(),
                failure_stage=XFailureStage.ACQUISITION,
                failure_code="X_PARTIAL_MULTI_ASSET" if len(assets) > 1 else "X_NO_SUPPORTED_MEDIA",
                completed_at_ms=self._now_ms(),
            )
        elif failed and success:
            updated = updated.advance(
                XAcquisitionState.COMPLETED_PARTIAL,
                updated_at_ms=self._now_ms(),
                completed_at_ms=self._now_ms(),
            )
        else:
            updated = updated.advance(
                XAcquisitionState.COMPLETED,
                updated_at_ms=self._now_ms(),
                completed_at_ms=self._now_ms(),
            )
        self._save(current, updated)
        await self._cleanup_claim(updated)

    async def _handoff_asset(self, claim: XPostClaim, asset: XAsset) -> None:
        if asset.acquired_bytes is None:
            raise XAcquisitionInfrastructureError("X staged asset has no bytes.")
        upload_id = UploadSessionId.from_string(asset.id.to_string())
        upload_storage_key = UploadStorageKey(asset.stage_key)
        requester = claim.created_by_login_key
        duplicate_mode = (
            UploadDuplicateResolutionMode.SILENT_KEEP_SEPARATE
            if requester is not None
            else UploadDuplicateResolutionMode.EXPLICIT
        )
        snapshot = self._transport.create_session(
            display_filename=f"x-{claim.x_post_id}-{asset.ordinal}.{_extension(asset.media_type)}",
            declared_size_bytes=asset.acquired_bytes,
            session_id=upload_id,
            storage_key=upload_storage_key,
            created_by_login_key=requester,
            duplicate_resolution_mode=duplicate_mode,
        )
        current = asset
        if current.upload_asset_key is None:
            linked = current.advance(
                XAssetState.HANDING_OFF,
                updated_at_ms=self._now_ms(),
                upload_asset_key=upload_id.to_string(),
            )
            current = self._save_asset(asset, linked)
        reader = self._staging.open_artifact(
            asset.stage_key, expected_size_bytes=asset.acquired_bytes
        )
        try:
            while snapshot.received_size_bytes < asset.acquired_bytes:
                reader.verify_still_consistent()
                reader.seek(snapshot.received_size_bytes)
                chunk = reader.read(
                    min(
                        self._chunk_size_bytes,
                        asset.acquired_bytes - snapshot.received_size_bytes,
                    )
                )
                if not chunk:
                    raise UploadTransportError("X upload handoff failed")
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
            snapshot.received_size_bytes != asset.acquired_bytes
            or snapshot.state
            not in {state.value for state in UploadSessionState}
            - {UploadSessionState.CREATED.value, UploadSessionState.RECEIVING.value}
        ):
            raise UploadTransportError("X upload handoff failed")
        _notify(self._validation_coordinator)

    async def _project_asset(self, claim: XPostClaim, asset: XAsset) -> None:
        if asset.upload_asset_key is None:
            raise XAcquisitionInfrastructureError("X asset has no upload linkage.")
        if asset.cleanup_state is XStagingCleanupState.PENDING:
            asset = self._clean_asset_staging(asset)
        upload_id = UploadSessionId.from_string(asset.upload_asset_key)
        upload = self._upload_repository.get(upload_id)
        if upload is None:
            raise XAcquisitionInfrastructureError("X upload handoff failed")
        if upload.state in {UploadSessionState.RECEIVED, UploadSessionState.VALIDATING}:
            _notify(self._validation_coordinator)
            return
        if upload.state in {
            UploadSessionState.PUBLISH_PENDING,
            UploadSessionState.PUBLISHED,
        }:
            _notify(self._publication_coordinator)
            return
        if upload.state is UploadSessionState.CATALOGED:
            candidate = self._publication_repository.get_candidate(upload_id)
            self._complete_asset(claim, asset, candidate)
            return
        if (
            upload.state is UploadSessionState.CANCELLED
            or upload.state is UploadSessionState.DUPLICATE_PENDING
        ):
            await self._fail_asset(
                claim, asset, stage=XFailureStage.DOWNSTREAM,
                code="X_CATALOG_HANDOFF_FAILED",
            )
            return
        await self._fail_asset(
            claim, asset, stage=XFailureStage.DOWNSTREAM,
            code="X_CATALOG_HANDOFF_FAILED",
        )

    def _complete_asset(
        self,
        claim: XPostClaim,
        asset: XAsset,
        candidate: UploadPublicationCandidate | None,
    ) -> None:
        if (
            candidate is None
            or candidate.publication is None
            or candidate.publication.media_id is None
            or candidate.publication.media_location_id is None
        ):
            raise XAcquisitionInfrastructureError("X catalog handoff failed.")
        completed = asset.advance(
            XAssetState.CATALOGED,
            updated_at_ms=self._now_ms(),
            media_id=candidate.publication.media_id,
            media_location_id=candidate.publication.media_location_id,
            completed_at_ms=self._now_ms(),
        )
        self._save_asset(asset, completed)

    async def _reconcile_cleanup(self, claim: XPostClaim) -> None:
        assets = self._repository.list_assets_for_post(claim.id)
        for asset in assets:
            if asset.cleanup_state is XStagingCleanupState.PENDING and asset.state in (
                XAssetState.CATALOGED, XAssetState.FAILED,
            ):
                self._clean_asset_staging(asset)
        updated_assets = self._repository.list_assets_for_post(claim.id)
        if all(
            a.cleanup_state is XStagingCleanupState.COMPLETE
            or a.state in ACTIVE_X_ASSET_STATES
            for a in updated_assets
        ):
            if claim.cleanup_state is XStagingCleanupState.PENDING:
                cleaned = claim.evolve(
                    updated_at_ms=self._now_ms(),
                    cleanup_state=XStagingCleanupState.COMPLETE,
                    cleanup_completed_at_ms=self._now_ms(),
                )
                self._save(claim, cleaned)

    def _clean_asset_staging(self, asset: XAsset) -> XAsset:
        try:
            self._staging.clear(asset.stage_key)
        except Exception:
            return asset
        cleaned = asset.evolve(
            updated_at_ms=self._now_ms(),
            cleanup_state=XStagingCleanupState.COMPLETE,
            cleanup_completed_at_ms=self._now_ms(),
        )
        return self._save_asset(asset, cleaned)

    async def _cleanup_claim(self, claim: XPostClaim) -> None:
        for asset in self._repository.list_assets_for_post(claim.id):
            if (
                asset.state in (XAssetState.CATALOGED, XAssetState.FAILED)
                and asset.cleanup_state is XStagingCleanupState.PENDING
            ):
                self._clean_asset_staging(asset)
        assets = self._repository.list_assets_for_post(claim.id)
        if all(
            a.cleanup_state is XStagingCleanupState.COMPLETE or a.state in ACTIVE_X_ASSET_STATES
            for a in assets
        ) and claim.cleanup_state is XStagingCleanupState.PENDING:
            cleaned = claim.evolve(
                updated_at_ms=self._now_ms(),
                cleanup_state=XStagingCleanupState.COMPLETE,
                cleanup_completed_at_ms=self._now_ms(),
            )
            self._save(claim, cleaned)

    async def _fail(
        self, claim: XPostClaim, *, stage: XFailureStage, code: str
    ) -> None:
        try:
            current = self._repository.get_post(claim.id)
            if current is None or current.state in TERMINAL_X_ACQUISITION_STATES:
                return
            failed = current.advance(
                XAcquisitionState.FAILED,
                updated_at_ms=self._now_ms(),
                failure_stage=stage,
                failure_code=code,
                completed_at_ms=self._now_ms(),
            )
            self._save(current, failed)
            await self._cleanup_claim(failed)
        except (FrameNestXClaimRepositoryError, FrameNestXAcquisitionError):
            return

    async def _fail_with_assets(
        self, claim: XPostClaim, *, stage: XFailureStage, code: str
    ) -> None:
        await self._fail(claim, stage=stage, code=code)

    async def _fail_asset(
        self,
        claim: XPostClaim,
        asset: XAsset,
        *,
        stage: XFailureStage,
        code: str,
    ) -> None:
        failed = asset.advance(
            XAssetState.FAILED,
            updated_at_ms=self._now_ms(),
            failure_stage=stage,
            failure_code=code,
        )
        self._save_asset(asset, failed)
        if is_retryable_x_failure(code):
            await self._advance_to_handoff(claim, self._repository.list_assets_for_post(claim.id))
        else:
            await self._fail(claim, stage=stage, code=code)

    def _save(self, previous: XPostClaim, updated: XPostClaim) -> XPostClaim:
        return self._repository.save_post(
            updated,
            expected_state=previous.state,
            expected_version=previous.version,
        )

    def _save_asset(self, previous: XAsset, updated: XAsset) -> XAsset:
        return self._repository.save_asset(
            updated,
            expected_state=previous.state,
            expected_version=previous.version,
        )


@dataclass(frozen=True, slots=True)
class _Acquired:
    size_bytes: int
    sha256: str


class _AssetTooLarge(XAcquisitionError):
    pass


def x_classification_for_upload(
    repository: XAcquisitionClaimRepository,
    upload_id: UploadSessionId,
) -> CatalogUploadClassification | None:
    """Return sparse catalog defaults for one source X asset upload."""
    asset = repository.find_asset_by_upload_id(upload_id)
    if asset is None:
        return None
    claim = repository.get_post(asset.claim_id)
    if claim is None:
        return None
    creator_kind = None
    creator_stable_id = None
    creator_handle = None
    creator_display_name = None
    if claim.source_author_stable_id is not None or claim.source_author_handle is not None:
        creator_kind = CreatorAttributionKind.X_AUTHOR
        creator_stable_id = claim.source_author_stable_id
        creator_handle = claim.source_author_handle
        creator_display_name = claim.source_author_display_name
    return CatalogUploadClassification(
        content_category=default_x_category(asset.media_type),
        acquisition_source=AcquisitionSource.X_MANUAL_CLAIM,
        display_title=_imported_display_title(claim.title),
        creator_attribution_kind=creator_kind,
        creator_stable_id=creator_stable_id,
        creator_handle=creator_handle,
        creator_display_name=creator_display_name,
    )


def automatic_analysis_allowed_for_upload(
    repository: XAcquisitionClaimRepository,
    upload_id: UploadSessionId,
) -> bool:
    """Fail closed for linked X acquisitions, even when globally enabled."""
    return repository.find_asset_by_upload_id(upload_id) is None


def _imported_display_title(title: str | None) -> MediaDisplayTitle | None:
    if title is None:
        return None
    candidate = title[:MAX_DISPLAY_TITLE_CODE_POINTS].rstrip()
    if not candidate:
        return None
    try:
        return MediaDisplayTitle(candidate)
    except FrameNestMediaMetadataError:
        return None


def _administration_snapshot(
    claim: XPostClaim, assets: tuple[XAsset, ...]
) -> XClaimSnapshot:
    return XClaimSnapshot(
        claim_id=claim.id.to_string(),
        state=claim.state.value,
        phase=derive_x_requester_phase(claim),
        x_post_id=claim.x_post_id,
        submitted_url=claim.submitted_url,
        canonical_url=claim.canonical_url,
        title=claim.title,
        source_author_handle=claim.source_author_handle,
        source_author_display_name=claim.source_author_display_name,
        discovered_asset_count=claim.discovered_asset_count,
        success_count=claim.success_count,
        failure_count=claim.failure_count,
        failure_stage=None if claim.failure_stage is None else claim.failure_stage.value,
        failure_code=claim.failure_code,
        retry_of_claim_id=None if claim.retry_of_claim_id is None else claim.retry_of_claim_id.to_string(),
        created_at_ms=claim.created_at_ms,
        updated_at_ms=claim.updated_at_ms,
        completed_at_ms=claim.completed_at_ms,
        assets=tuple(_asset_snapshot(a) for a in assets),
    )


def _requester_snapshot(
    claim: XPostClaim, repository: XAcquisitionClaimRepository
) -> XClaimSnapshot:
    assets = repository.list_assets_for_post(claim.id)
    return _administration_snapshot(claim, assets)


def _asset_snapshot(asset: XAsset) -> XAssetSnapshot:
    return XAssetSnapshot(
        asset_id=asset.id.to_string(),
        ordinal=asset.ordinal,
        media_type=asset.media_type.value,
        state=asset.state.value,
        acquired_bytes=asset.acquired_bytes,
        media_id=None if asset.media_id is None else asset.media_id.to_string(),
        failure_stage=None if asset.failure_stage is None else asset.failure_stage.value,
        failure_code=asset.failure_code,
        created_at_ms=asset.created_at_ms,
        updated_at_ms=asset.updated_at_ms,
    )


def _submission(
    claim: XPostClaim, *, submission_result: str, requester: str
) -> XRequestSubmission:
    return XRequestSubmission(
        request_id=claim.id.to_string(),
        submission_result=submission_result,
        phase=derive_x_requester_phase(claim),
        x_post_id=claim.x_post_id,
        submitted_url=claim.submitted_url,
    )


def _normalize_requester(login_key: str) -> str:
    from framenest.domain.identity_access import normalize_login

    try:
        return normalize_login(login_key)
    except Exception as exc:
        raise XAcquisitionInvalidRequestError("Invalid requester identity.") from exc


def _asset_retryable(asset: XAsset) -> bool:
    if asset.state is XAssetState.FAILED:
        return True
    if asset.state in ACTIVE_X_ASSET_STATES:
        return True
    return False


def _bound_post_text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    from framenest.domain.media_metadata import MAX_DISPLAY_TITLE_CODE_POINTS

    return value.strip()[:MAX_DISPLAY_TITLE_CODE_POINTS]


def _media_type_label(media_type: XMediaType) -> str:
    return {XMediaType.VIDEO: "video", XMediaType.ANIMATED_GIF: "video", XMediaType.IMAGE: "image"}[media_type]


def _stage_for_extractor_code(code: str) -> XFailureStage:
    if code in {"X_AUTHENTICATION_REQUIRED", "X_POST_UNAVAILABLE", "X_POST_DELETED", "X_POST_PROTECTED"}:
        return XFailureStage.EXTRACTION
    return XFailureStage.EXTRACTION


def _code_from_exception(exc: Exception) -> str:
    if isinstance(exc, _AssetTooLarge):
        return "X_MEDIA_TOO_LARGE"
    if isinstance(exc, XExtractionError):
        return exc.code
    if isinstance(exc, XExtractorConfigurationError):
        return "X_EXTRACTOR_UNAVAILABLE"
    if isinstance(exc, UploadTransportError):
        return "X_CATALOG_HANDOFF_FAILED"
    if isinstance(exc, FrameNestXClaimRepositoryError):
        return "X_STAGING_FAILED"
    return "X_EXTRACTOR_FAILED"


def _extension(media_type: XMediaType) -> str:
    return {
        XMediaType.VIDEO: "mp4",
        XMediaType.ANIMATED_GIF: "mp4",
        XMediaType.IMAGE: "jpg",
    }[media_type]


def _one_chunk(chunk: bytes) -> AsyncIterator[bytes]:
    async def _iterator() -> AsyncIterator[bytes]:
        yield chunk

    return _iterator()


def _notify(coordinator: object) -> None:
    notify = getattr(coordinator, "notify", None)
    if callable(notify):
        notify()


ACTIVE_X_ASSET_STATES = frozenset(
    {
        XAssetState.PENDING,
        XAssetState.EXTRACTED,
        XAssetState.ACQUIRING,
        XAssetState.STAGED,
        XAssetState.HANDING_OFF,
    }
)

_AWAITING_ACQUISITION_ASSET_STATES = frozenset(
    {
        XAssetState.PENDING,
        XAssetState.EXTRACTED,
        XAssetState.ACQUIRING,
    }
)