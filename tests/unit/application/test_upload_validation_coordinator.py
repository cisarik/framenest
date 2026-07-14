"""Unit tests for lifecycle-owned upload-validation orchestration."""

from __future__ import annotations

import asyncio
import threading
from pathlib import Path

from framenest.application.upload_transport import UploadSessionLockRegistry
from framenest.application.upload_validation import UploadValidationResult
from framenest.application.upload_validation_coordinator import UploadValidationCoordinator
from framenest.domain.uploads import (
    UploadDisplayFilename,
    UploadSession,
    UploadSessionId,
    UploadSessionState,
    UploadStorageKey,
)


def _session(
    state: UploadSessionState = UploadSessionState.RECEIVED,
    *,
    storage_key: str = "validation-candidate-0001",
) -> UploadSession:
    return UploadSession(
        id=UploadSessionId.new(),
        state=state,
        storage_key=UploadStorageKey(storage_key),
        display_filename=UploadDisplayFilename("example.mp4"),
        declared_size_bytes=10,
        received_size_bytes=10,
        checksum_algorithm=None,
        checksum_hex=None,
        created_at_ms=10,
        updated_at_ms=10,
        expires_at_ms=1000,
        failure_code=None,
        version=0,
    )


class _Repository:
    def __init__(self, batches: list[tuple[UploadSession, ...]]) -> None:
        self._batches = batches
        self._guard = threading.Lock()
        self.limits: list[int] = []

    def list_validation_candidates(self, *, limit: int) -> tuple[UploadSession, ...]:
        with self._guard:
            self.limits.append(limit)
            if not self._batches:
                return ()
            return self._batches.pop(0)[:limit]


class _BlockingValidator:
    def __init__(self) -> None:
        self.started = threading.Event()
        self.release = threading.Event()
        self.calls: list[tuple[str, str]] = []
        self.active = 0
        self.max_active = 0
        self._guard = threading.Lock()

    def validate_owned_blocking(self, session_id: UploadSessionId) -> UploadValidationResult:
        return self._run("received", session_id)

    def recover_abandoned_validating_owned_blocking(
        self,
        session_id: UploadSessionId,
    ) -> UploadValidationResult:
        return self._run("validating", session_id)

    def _run(self, mode: str, session_id: UploadSessionId) -> UploadValidationResult:
        with self._guard:
            self.active += 1
            self.max_active = max(self.max_active, self.active)
            self.calls.append((mode, session_id.to_string()))
        self.started.set()
        try:
            assert self.release.wait(timeout=5)
            return UploadValidationResult(
                upload_id=session_id.to_string(),
                state="publish_pending",
                checksum_algorithm="sha256",
                checksum_hex="a" * 64,
                validated_media_kind="video",
                validated_format="mp4",
                failure_code=None,
            )
        finally:
            with self._guard:
                self.active -= 1


def test_drain_runs_blocking_validation_off_event_loop() -> None:
    async def scenario() -> None:
        session = _session()
        validator = _BlockingValidator()
        coordinator = UploadValidationCoordinator(
            _Repository([(session,), ()]),
            validator,
            UploadSessionLockRegistry(),
        )

        drain = asyncio.create_task(coordinator.drain())
        await asyncio.wait_for(asyncio.to_thread(validator.started.wait), timeout=1)

        marker_ran = False

        async def marker() -> None:
            nonlocal marker_ran
            marker_ran = True

        await asyncio.wait_for(marker(), timeout=1)
        assert marker_ran
        assert not drain.done()

        validator.release.set()
        await asyncio.wait_for(drain, timeout=1)
        await coordinator.shutdown()

    asyncio.run(scenario())


def test_duplicate_notifications_share_one_runner_and_do_not_validate_concurrently() -> None:
    async def scenario() -> None:
        session = _session()
        validator = _BlockingValidator()
        coordinator = UploadValidationCoordinator(
            _Repository([(session,), ()]),
            validator,
            UploadSessionLockRegistry(),
        )

        await coordinator.start()
        coordinator.notify()
        coordinator.notify()
        await asyncio.wait_for(asyncio.to_thread(validator.started.wait), timeout=1)
        assert validator.max_active == 1
        assert len(validator.calls) == 1

        validator.release.set()
        await asyncio.wait_for(coordinator.shutdown(), timeout=1)
        assert coordinator.runner_done

    asyncio.run(scenario())


def test_startup_reconciles_received_and_abandoned_validating_without_claiming_validating() -> None:
    async def scenario() -> None:
        received = _session(UploadSessionState.RECEIVED, storage_key="validation-candidate-0001")
        validating = _session(
            UploadSessionState.VALIDATING,
            storage_key="validation-candidate-0002",
        )
        validator = _BlockingValidator()
        validator.release.set()
        coordinator = UploadValidationCoordinator(
            _Repository([(received, validating), ()]),
            validator,
            UploadSessionLockRegistry(),
        )

        await coordinator.drain()
        await coordinator.shutdown()

        assert validator.calls == [
            ("received", received.id.to_string()),
            ("validating", validating.id.to_string()),
        ]

    asyncio.run(scenario())


def test_active_in_process_validating_work_is_not_recovered_concurrently() -> None:
    async def scenario() -> None:
        session = _session(UploadSessionState.VALIDATING)
        locks = UploadSessionLockRegistry()
        validator = _BlockingValidator()
        validator.release.set()
        coordinator = UploadValidationCoordinator(
            _Repository([(session,), ()]),
            validator,
            locks,
        )

        async with locks.lease(session.id):
            drain = asyncio.create_task(coordinator.drain())
            await asyncio.sleep(0)
            assert validator.calls == []
            assert not drain.done()

        await asyncio.wait_for(drain, timeout=1)
        await coordinator.shutdown()
        assert validator.calls == [("validating", session.id.to_string())]

    asyncio.run(scenario())


def test_shutdown_waits_for_owned_runner_without_orphaning_task_or_thread(tmp_path: Path) -> None:
    async def scenario() -> None:
        session = _session()
        validator = _BlockingValidator()
        coordinator = UploadValidationCoordinator(
            _Repository([(session,), ()]),
            validator,
            UploadSessionLockRegistry(),
        )

        await coordinator.start()
        await asyncio.wait_for(asyncio.to_thread(validator.started.wait), timeout=1)
        shutdown = asyncio.create_task(coordinator.shutdown())
        await asyncio.sleep(0)
        assert not shutdown.done()
        assert coordinator.active_count == 1

        validator.release.set()
        await asyncio.wait_for(shutdown, timeout=1)

        assert coordinator.runner_done
        assert not coordinator.executor_running
        assert not [
            thread
            for thread in threading.enumerate()
            if thread.name.startswith("framenest-upload-validation") and thread.is_alive()
        ]

    asyncio.run(scenario())
