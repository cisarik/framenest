"""Lifecycle-owned orchestration for durable upload validation."""

from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Protocol

from framenest.application.ports.upload_sessions import (
    FrameNestUploadSessionRepositoryError,
    UploadSessionRepository,
)
from framenest.application.upload_transport import UploadSessionLockRegistry
from framenest.application.upload_validation import (
    UploadValidationConcurrencyError,
    UploadValidationError,
    UploadValidationNotFoundError,
    UploadValidationResult,
    UploadValidationStateConflictError,
    ValidateReceivedUpload,
)
from framenest.domain.uploads import UploadSession, UploadSessionId, UploadSessionState
from framenest.structured_logging import get_logger

LOGGER = get_logger("upload_validation_coordinator")

DEFAULT_UPLOAD_VALIDATION_BATCH_SIZE = 32


class _UploadValidator(Protocol):
    def validate_owned_blocking(
        self,
        session_id: UploadSessionId,
    ) -> UploadValidationResult:
        """Validate a received upload while the caller owns the process-local lock."""

    def recover_abandoned_validating_owned_blocking(
        self,
        session_id: UploadSessionId,
    ) -> UploadValidationResult:
        """Validate a startup-abandoned validating upload without reclaiming it."""


class UploadValidationCoordinator:
    """Run durable upload validation through one application-owned consumer.

    The coordinator is intentionally scoped to one FrameNest process, one Uvicorn
    worker, and one validation consumer. Durable recovery handles forced process
    loss, but this class does not provide a lease, heartbeat, or multi-process lock.
    """

    def __init__(
        self,
        repository: UploadSessionRepository,
        validator: _UploadValidator | ValidateReceivedUpload,
        locks: UploadSessionLockRegistry,
        *,
        batch_size: int = DEFAULT_UPLOAD_VALIDATION_BATCH_SIZE,
        executor: ThreadPoolExecutor | None = None,
    ) -> None:
        if isinstance(batch_size, bool) or batch_size <= 0:
            raise ValueError("upload validation batch size must be positive")
        self._repository = repository
        self._validator = validator
        self._locks = locks
        self._batch_size = batch_size
        self._executor = executor
        self._owns_executor = executor is None
        self._runner: asyncio.Task[None] | None = None
        self._wake: asyncio.Event | None = None
        self._stopping = False
        self._active_upload_ids: set[str] = set()

    async def start(self) -> None:
        """Start the lifecycle-owned runner and schedule startup reconciliation."""
        if self._runner is not None:
            return
        self._stopping = False
        self._ensure_executor()
        self._wake = asyncio.Event()
        self._runner = asyncio.create_task(
            self._run(),
            name="framenest-upload-validation-coordinator",
        )
        self.notify()

    def notify(self) -> None:
        """Wake the runner to reconcile durable validation candidates."""
        wake = self._wake
        if wake is not None and not self._stopping:
            wake.set()

    async def drain(self) -> None:
        """Deterministically process currently discoverable validation work."""
        self._ensure_executor()
        await self._drain_until_idle()

    async def shutdown(self) -> None:
        """Stop claiming new uploads and retain ownership until the runner exits."""
        self._stopping = True
        wake = self._wake
        if wake is not None:
            wake.set()
        runner = self._runner
        if runner is not None:
            await runner
        self._runner = None
        self._wake = None
        if self._executor is not None and self._owns_executor:
            self._executor.shutdown(wait=True, cancel_futures=False)
            self._executor = None

    @property
    def runner_done(self) -> bool:
        """Return whether the lifecycle runner has no pending asyncio task."""
        return self._runner is None or self._runner.done()

    @property
    def active_count(self) -> int:
        """Return active upload validations for deterministic tests."""
        return len(self._active_upload_ids)

    @property
    def executor_running(self) -> bool:
        """Return whether the owned execution boundary still has an executor."""
        return self._executor is not None

    async def _run(self) -> None:
        assert self._wake is not None
        while True:
            await self._wake.wait()
            self._wake.clear()
            if self._stopping:
                break
            await self._drain_until_idle()

    async def _drain_until_idle(self) -> None:
        while not self._stopping:
            candidates = await self._discover_candidates()
            if not candidates:
                return
            processed_any = False
            for candidate in candidates:
                if self._stopping:
                    return
                processed = await self._process_candidate(candidate)
                processed_any = processed_any or processed
            if not processed_any:
                return

    async def _discover_candidates(self) -> tuple[UploadSession, ...]:
        try:
            return await self._run_blocking(
                self._repository.list_validation_candidates,
                limit=self._batch_size,
            )
        except FrameNestUploadSessionRepositoryError:
            LOGGER.emit(
                level="WARNING",
                event="upload_validation_candidate_discovery_failed",
                operation="upload_validation_discovery",
                error_code="UPLOAD_VALIDATION_DISCOVERY_FAILED",
                retryable=True,
            )
            return ()

    async def _process_candidate(self, candidate: UploadSession) -> bool:
        upload_id = candidate.id.to_string()
        if upload_id in self._active_upload_ids:
            return False
        if candidate.state not in {
            UploadSessionState.RECEIVED,
            UploadSessionState.VALIDATING,
        }:
            return False
        self._active_upload_ids.add(upload_id)
        try:
            async with self._locks.lease(candidate.id):
                if candidate.state is UploadSessionState.VALIDATING:
                    await self._run_blocking(
                        self._validator.recover_abandoned_validating_owned_blocking,
                        candidate.id,
                    )
                else:
                    await self._run_blocking(
                        self._validator.validate_owned_blocking,
                        candidate.id,
                    )
            return True
        except (
            UploadValidationConcurrencyError,
            UploadValidationNotFoundError,
            UploadValidationStateConflictError,
        ):
            return True
        except UploadValidationError:
            return True
        finally:
            self._active_upload_ids.discard(upload_id)

    async def _run_blocking(self, func, /, *args, **kwargs):
        loop = asyncio.get_running_loop()
        executor = self._ensure_executor()
        return await loop.run_in_executor(
            executor,
            lambda: func(*args, **kwargs),
        )

    def _ensure_executor(self) -> ThreadPoolExecutor:
        if self._executor is None:
            self._executor = ThreadPoolExecutor(
                max_workers=1,
                thread_name_prefix="framenest-upload-validation",
            )
        return self._executor
