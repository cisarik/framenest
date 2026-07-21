"""Lifecycle-owned bounded coordinator for durable automatic media analysis."""

from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
from enum import Enum, auto

from framenest.application.media_analysis_lifecycle import (
    CatalogedAnalysisTarget,
    ExecuteAutomaticMediaAnalysisRun,
    MediaAnalysisLifecycleError,
    RequestManualMediaAnalysis,
    ScheduleAutomaticMediaAnalysis,
)
from framenest.application.ports.media_analysis_runs import (
    FrameNestMediaAnalysisRunRepositoryError,
    MediaAnalysisRunRepository,
)
from framenest.domain.identities import MediaId, MediaLocationId
from framenest.domain.media_analysis_runs import (
    MediaAnalysisRun,
    MediaAnalysisRunState,
)
from framenest.structured_logging import get_logger

LOGGER = get_logger("media_analysis_coordinator")

DEFAULT_MEDIA_ANALYSIS_BATCH_SIZE = 32
DEFAULT_ANALYSIS_RETRY_INITIAL_DELAY_SECONDS = 0.25
DEFAULT_ANALYSIS_RETRY_MAX_DELAY_SECONDS = 5.0


class _DrainOutcome(Enum):
    IDLE = auto()
    RETRY = auto()
    SHUTDOWN = auto()


class _CandidateOutcome(Enum):
    PROGRESS = auto()
    RETRY = auto()
    STALE = auto()
    SHUTDOWN = auto()


class MediaAnalysisCoordinator:
    """Run automatic analysis through one consumer in the current process."""

    def __init__(
        self,
        repository: MediaAnalysisRunRepository,
        scheduler: ScheduleAutomaticMediaAnalysis,
        executor_service: ExecuteAutomaticMediaAnalysisRun,
        *,
        manual_requester: RequestManualMediaAnalysis | None = None,
        batch_size: int = DEFAULT_MEDIA_ANALYSIS_BATCH_SIZE,
        executor: ThreadPoolExecutor | None = None,
        retry_initial_delay_seconds: float = (
            DEFAULT_ANALYSIS_RETRY_INITIAL_DELAY_SECONDS
        ),
        retry_max_delay_seconds: float = DEFAULT_ANALYSIS_RETRY_MAX_DELAY_SECONDS,
    ) -> None:
        if isinstance(batch_size, bool) or batch_size <= 0:
            raise ValueError("media analysis batch size must be positive")
        if (
            isinstance(retry_initial_delay_seconds, bool)
            or retry_initial_delay_seconds < 0
        ):
            raise ValueError("media analysis retry delay must be non-negative")
        if (
            isinstance(retry_max_delay_seconds, bool)
            or retry_max_delay_seconds < retry_initial_delay_seconds
        ):
            raise ValueError("media analysis retry max delay is invalid")
        self._repository = repository
        self._scheduler = scheduler
        self._executor_service = executor_service
        self._manual_requester = manual_requester or RequestManualMediaAnalysis(
            repository
        )
        self._batch_size = batch_size
        self._executor = executor
        self._owns_executor = executor is None
        self._retry_initial_delay_seconds = retry_initial_delay_seconds
        self._retry_max_delay_seconds = retry_max_delay_seconds
        self._current_retry_delay_seconds = retry_initial_delay_seconds
        self._runner: asyncio.Task[None] | None = None
        self._wake: asyncio.Event | None = None
        self._stopping = False
        self._active_run_ids: set[str] = set()

    async def start(self) -> None:
        """Start one runner and wake startup reconciliation of requested work."""
        if self._runner is not None:
            if self._runner.done() and not self._stopping:
                raise RuntimeError("media analysis coordinator runner is not active")
            return
        self._stopping = False
        self._current_retry_delay_seconds = self._retry_initial_delay_seconds
        self._ensure_executor()
        self._wake = asyncio.Event()
        self._runner = asyncio.create_task(
            self._run(),
            name="framenest-media-analysis-coordinator",
        )
        self.notify()

    def notify(self) -> None:
        """Wake the runner after durable analysis work becomes eligible."""
        runner = self._runner
        if runner is not None and runner.done() and not self._stopping:
            raise RuntimeError("media analysis coordinator runner is not active")
        if self._wake is not None and not self._stopping:
            self._wake.set()

    def notify_cataloged(
        self,
        media_id: MediaId,
        media_location_id: MediaLocationId,
    ) -> None:
        """Schedule automatic analysis after successful cataloging when enabled."""
        if self._stopping or not self._scheduler.enabled:
            return
        try:
            self._scheduler.execute(
                CatalogedAnalysisTarget(
                    media_id=media_id,
                    media_location_id=media_location_id,
                )
            )
        except MediaAnalysisLifecycleError:
            _safe_log(
                level="WARNING",
                event="media_analysis_schedule_failed",
                operation="media_analysis_schedule",
                error_code="MEDIA_ANALYSIS_SCHEDULE_FAILED",
                retryable=False,
            )
            return
        self.notify()

    def request_manual(
        self,
        media_id: MediaId,
        media_location_id: MediaLocationId,
    ) -> MediaAnalysisRun:
        """Request one durable analysis run without enabling automatic scheduling."""
        if self._stopping:
            raise MediaAnalysisLifecycleError("media analysis coordinator is stopping")
        run = self._manual_requester.execute(
            CatalogedAnalysisTarget(
                media_id=media_id,
                media_location_id=media_location_id,
            )
        )
        if run.state in {
            MediaAnalysisRunState.PENDING,
            MediaAnalysisRunState.ANALYZING,
        }:
            self.notify()
        return run

    async def drain(self) -> None:
        """Process currently discoverable unfinished work once for tests."""
        self._ensure_executor()
        await self._drain_once()

    async def shutdown(self) -> None:
        """Stop claiming work and wait for owned blocking work to settle."""
        self._stopping = True
        if self._wake is not None:
            self._wake.set()
        runner = self._runner
        cancellation: asyncio.CancelledError | None = None
        try:
            if runner is not None:
                try:
                    await runner
                except asyncio.CancelledError as exc:
                    cancellation = exc
                except Exception:
                    _safe_log(
                        level="WARNING",
                        event="media_analysis_runner_shutdown_fault",
                        operation="media_analysis_shutdown",
                        error_code="MEDIA_ANALYSIS_RUNNER_SHUTDOWN_FAULT",
                        retryable=False,
                    )
        finally:
            self._runner = None
            self._wake = None
            self._active_run_ids.clear()
            self._current_retry_delay_seconds = self._retry_initial_delay_seconds
            try:
                if self._executor is not None and self._owns_executor:
                    self._executor.shutdown(wait=True, cancel_futures=False)
            finally:
                if self._owns_executor:
                    self._executor = None
        if cancellation is not None:
            raise cancellation

    @property
    def runner_done(self) -> bool:
        return self._runner is None or self._runner.done()

    @property
    def active_count(self) -> int:
        return len(self._active_run_ids)

    async def _run(self) -> None:
        assert self._wake is not None
        while not self._stopping:
            await self._wake.wait()
            self._wake.clear()
            if self._stopping:
                return
            try:
                await self._reconcile_until_idle()
            except asyncio.CancelledError:
                raise
            except Exception:
                _safe_log(
                    level="ERROR",
                    event="media_analysis_runner_iteration_failed",
                    operation="media_analysis_run",
                    error_code="MEDIA_ANALYSIS_RUNNER_ITERATION_FAILED",
                    retryable=True,
                )

    async def _reconcile_until_idle(self) -> None:
        while not self._stopping:
            outcome = await self._drain_once()
            if outcome is _DrainOutcome.SHUTDOWN:
                return
            if outcome is _DrainOutcome.RETRY:
                await self._wait_before_retry()
                self._increase_retry_delay()
                continue
            self._reset_retry_delay()
            if self._wake is not None and self._wake.is_set():
                self._wake.clear()
                continue
            return

    async def _drain_once(self) -> _DrainOutcome:
        cursor: tuple[int, str] | None = None
        visited: set[str] = set()
        retry_needed = False
        while not self._stopping:
            runs = await self._discover(after=cursor)
            if runs is None:
                return _DrainOutcome.RETRY
            if not runs:
                return _DrainOutcome.RETRY if retry_needed else _DrainOutcome.IDLE
            for run in runs:
                cursor = (run.created_at_ms, run.id.to_string())
                if self._stopping:
                    return _DrainOutcome.SHUTDOWN
                run_id = run.id.to_string()
                if run_id in visited:
                    continue
                visited.add(run_id)
                outcome = await self._process_run(run)
                if outcome is _CandidateOutcome.SHUTDOWN:
                    return _DrainOutcome.SHUTDOWN
                if outcome is _CandidateOutcome.RETRY:
                    retry_needed = True
        return _DrainOutcome.SHUTDOWN

    async def _discover(
        self,
        *,
        after: tuple[int, str] | None,
    ) -> tuple[MediaAnalysisRun, ...] | None:
        try:
            return await self._run_blocking(
                self._repository.list_unfinished,
                limit=self._batch_size,
                after_created_at_ms=None if after is None else after[0],
                after_id=None if after is None else after[1],
            )
        except FrameNestMediaAnalysisRunRepositoryError as exc:
            if _missing_schema_error(exc):
                return ()
            _safe_log(
                level="WARNING",
                event="media_analysis_discovery_failed",
                operation="media_analysis_discovery",
                error_code="MEDIA_ANALYSIS_DISCOVERY_FAILED",
                retryable=True,
            )
            return None
        except Exception:
            _safe_log(
                level="WARNING",
                event="media_analysis_discovery_failed",
                operation="media_analysis_discovery",
                error_code="MEDIA_ANALYSIS_DISCOVERY_FAILED",
                retryable=True,
            )
            return None

    async def _process_run(self, run: MediaAnalysisRun) -> _CandidateOutcome:
        run_id = run.id.to_string()
        if run_id in self._active_run_ids:
            return _CandidateOutcome.STALE
        if run.state not in {
            MediaAnalysisRunState.PENDING,
            MediaAnalysisRunState.ANALYZING,
        }:
            return _CandidateOutcome.STALE
        self._active_run_ids.add(run_id)
        try:
            if self._stopping:
                return _CandidateOutcome.SHUTDOWN
            await self._run_blocking(self._executor_service.execute, run)
            return _CandidateOutcome.PROGRESS
        except MediaAnalysisLifecycleError:
            return _CandidateOutcome.RETRY
        except Exception:
            _safe_log(
                level="WARNING",
                event="media_analysis_candidate_processing_failed",
                operation="media_analysis_candidate",
                error_code="MEDIA_ANALYSIS_CANDIDATE_FAILED",
                retryable=True,
            )
            return _CandidateOutcome.RETRY
        finally:
            self._active_run_ids.discard(run_id)

    async def _wait_before_retry(self) -> None:
        delay = self._current_retry_delay_seconds
        if delay <= 0:
            await asyncio.sleep(0)
            return
        if self._wake is None:
            await asyncio.sleep(delay)
            return
        try:
            await asyncio.wait_for(self._wake.wait(), timeout=delay)
        except TimeoutError:
            return
        finally:
            if self._wake.is_set():
                self._wake.clear()

    def _increase_retry_delay(self) -> None:
        if self._current_retry_delay_seconds <= 0:
            return
        self._current_retry_delay_seconds = min(
            self._current_retry_delay_seconds * 2,
            self._retry_max_delay_seconds,
        )

    def _reset_retry_delay(self) -> None:
        self._current_retry_delay_seconds = self._retry_initial_delay_seconds

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
                thread_name_prefix="framenest-media-analysis",
            )
        return self._executor


def _missing_schema_error(exc: BaseException) -> bool:
    message = str(exc).lower()
    cause = getattr(exc, "__cause__", None)
    cause_message = "" if cause is None else str(cause).lower()
    haystack = f"{message} {cause_message}"
    return "media_analysis_runs" in haystack and (
        "no such table" in haystack or "does not exist" in haystack
    )


def _safe_log(**fields: object) -> None:
    try:
        LOGGER.emit(**fields)
    except Exception:
        return
