"""Lifecycle service tests for durable automatic media analysis."""

from __future__ import annotations

from dataclasses import replace
import threading

import pytest

from framenest.application.media_analysis_lifecycle import (
    AutomaticAnalysisPublicView,
    CatalogedAnalysisTarget,
    ExecuteAutomaticMediaAnalysisRun,
    ScheduleAutomaticMediaAnalysis,
    public_view_from_run,
    serialize_suggestion_result,
)
from framenest.application.media_suggestion import (
    MediaSuggestion,
    MediaSuggestionProviderAuthError,
    MediaSuggestionProviderRateLimitedError,
    MediaSuggestionProviderUnavailableError,
    PROMPT_VERSION,
)
from framenest.domain.identities import MediaId, MediaLocationId
from framenest.domain.media_analysis_runs import (
    AUTOMATIC_POST_CATALOG_ANALYSIS_DEFINITION,
    MediaAnalysisRun,
    MediaAnalysisRunId,
    MediaAnalysisRunState,
)


MEDIA_ID = MediaId.from_string("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")
LOCATION_ID = MediaLocationId.from_string("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb")


def _suggestion() -> MediaSuggestion:
    return MediaSuggestion(
        title="Title",
        description="Description text for suggestion.",
        collection="Collection",
        tags=("tag-one",),
        suggested_filename="title.mp4",
        confidence=0.8,
        evidence=("frame evidence",),
        uncertainties=(),
        provider_id="nvidia-nim",
        model_id="test-model",
        prompt_version=PROMPT_VERSION,
    )


class _FakeRepository:
    def __init__(self) -> None:
        self.run: MediaAnalysisRun | None = None
        self.transactions: list[str] = []
        self._lock = threading.Lock()

    def get_by_media_definition(self, media_id, analysis_definition):
        del media_id, analysis_definition
        return self.run

    def create_pending(self, *, media_id, media_location_id, analysis_definition, created_at_ms):
        with self._lock:
            self.transactions.append("create_pending")
            if self.run is not None:
                return self.run
            self.run = MediaAnalysisRun(
                id=MediaAnalysisRunId("11111111-1111-4111-8111-111111111111"),
                media_id=media_id,
                media_location_id=media_location_id,
                analysis_definition=analysis_definition,
                state=MediaAnalysisRunState.PENDING,
                attempt_count=0,
                provider_id=None,
                model_id=None,
                prompt_version=None,
                result_schema_version=None,
                result_json=None,
                error_code=None,
                error_message=None,
                created_at_ms=created_at_ms,
                started_at_ms=None,
                completed_at_ms=None,
                version=1,
            )
            return self.run

    def claim_pending(self, *, run_id, expected_version, started_at_ms, max_attempts):
        del run_id, max_attempts
        with self._lock:
            self.transactions.append("claim_pending")
            assert self.run is not None
            assert self.run.version == expected_version
            self.run = replace(
                self.run,
                state=MediaAnalysisRunState.ANALYZING,
                attempt_count=self.run.attempt_count + 1,
                started_at_ms=started_at_ms,
                version=self.run.version + 1,
            )
            return self.run

    def requeue_for_retry(
        self,
        *,
        run_id,
        expected_version,
        error_code,
        error_message,
        updated_at_ms,
    ):
        del run_id, error_code, error_message, updated_at_ms
        with self._lock:
            self.transactions.append("requeue_for_retry")
            assert self.run is not None
            assert self.run.version == expected_version
            self.run = replace(
                self.run,
                state=MediaAnalysisRunState.PENDING,
                started_at_ms=None,
                version=self.run.version + 1,
            )
            return self.run

    def record_analyzed(
        self,
        *,
        run_id,
        expected_version,
        provider_id,
        model_id,
        prompt_version,
        result_schema_version,
        result_json,
        completed_at_ms,
    ):
        del run_id
        with self._lock:
            self.transactions.append("record_analyzed")
            assert self.run is not None
            assert self.run.version == expected_version
            self.run = replace(
                self.run,
                state=MediaAnalysisRunState.ANALYZED,
                provider_id=provider_id,
                model_id=model_id,
                prompt_version=prompt_version,
                result_schema_version=result_schema_version,
                result_json=result_json,
                completed_at_ms=completed_at_ms,
                version=self.run.version + 1,
            )
            return self.run

    def record_failed(
        self,
        *,
        run_id,
        expected_version,
        error_code,
        error_message,
        provider_id,
        model_id,
        prompt_version,
        completed_at_ms,
    ):
        del run_id
        with self._lock:
            self.transactions.append("record_failed")
            assert self.run is not None
            assert self.run.version == expected_version
            self.run = replace(
                self.run,
                state=MediaAnalysisRunState.FAILED,
                error_code=error_code,
                error_message=error_message,
                provider_id=provider_id,
                model_id=model_id,
                prompt_version=prompt_version,
                completed_at_ms=completed_at_ms,
                version=self.run.version + 1,
            )
            return self.run

    def reset_interrupted_analyzing(
        self,
        *,
        run_id,
        expected_version,
        max_attempts,
        updated_at_ms,
    ):
        del run_id, max_attempts
        with self._lock:
            self.transactions.append("reset_interrupted_analyzing")
            assert self.run is not None
            assert self.run.version == expected_version
            # Mirror production: stale analyzing is ambiguous and fail-closed.
            self.run = replace(
                self.run,
                state=MediaAnalysisRunState.FAILED,
                error_code="ANALYSIS_OUTCOME_UNKNOWN",
                error_message=(
                    "Automatic analysis was interrupted and the provider "
                    "outcome cannot be determined safely."
                ),
                completed_at_ms=updated_at_ms,
                version=self.run.version + 1,
            )
            return self.run

    def list_unfinished(self, *, limit, after_created_at_ms=None, after_id=None):
        del limit, after_created_at_ms, after_id
        if self.run is None or self.run.state in {
            MediaAnalysisRunState.ANALYZED,
            MediaAnalysisRunState.FAILED,
        }:
            return ()
        return (self.run,)


class _FakeExecutor:
    def __init__(self, *, error: Exception | None = None, calls: list | None = None) -> None:
        self.error = error
        self.calls = calls if calls is not None else []
        self.in_transaction_probe = lambda: False

    def execute(self, media_id, location_id):
        assert not self.in_transaction_probe()
        self.calls.append((media_id, location_id))
        if self.error is not None:
            raise self.error
        return _suggestion()


def test_schedule_disabled_creates_no_run() -> None:
    repository = _FakeRepository()
    scheduler = ScheduleAutomaticMediaAnalysis(repository, enabled=False)
    assert (
        scheduler.execute(
            CatalogedAnalysisTarget(media_id=MEDIA_ID, media_location_id=LOCATION_ID)
        )
        is None
    )
    assert repository.run is None


def test_schedule_enabled_is_idempotent() -> None:
    repository = _FakeRepository()
    scheduler = ScheduleAutomaticMediaAnalysis(repository, enabled=True, now_ms=lambda: 10)
    first = scheduler.execute(
        CatalogedAnalysisTarget(media_id=MEDIA_ID, media_location_id=LOCATION_ID)
    )
    second = scheduler.execute(
        CatalogedAnalysisTarget(media_id=MEDIA_ID, media_location_id=LOCATION_ID)
    )
    assert first is not None and second is not None
    assert first.id.to_string() == second.id.to_string()
    assert repository.transactions.count("create_pending") == 2


def test_execute_success_records_analyzed_outside_transaction() -> None:
    repository = _FakeRepository()
    scheduler = ScheduleAutomaticMediaAnalysis(repository, enabled=True, now_ms=lambda: 10)
    run = scheduler.execute(
        CatalogedAnalysisTarget(media_id=MEDIA_ID, media_location_id=LOCATION_ID)
    )
    assert run is not None
    open_transactions = {"open": False}
    executor = _FakeExecutor()
    executor.in_transaction_probe = lambda: open_transactions["open"]
    service = ExecuteAutomaticMediaAnalysisRun(
        repository,
        executor,
        now_ms=lambda: 20,
        in_transaction=lambda: open_transactions["open"],
    )
    # Simulate that DB claim closes before provider work.
    original_claim = repository.claim_pending

    def claim_and_close(**kwargs):
        open_transactions["open"] = True
        claimed = original_claim(**kwargs)
        open_transactions["open"] = False
        return claimed

    repository.claim_pending = claim_and_close  # type: ignore[method-assign]
    result = service.execute(run)
    assert result.state is MediaAnalysisRunState.ANALYZED
    assert result.result_json is not None
    assert "nvidia-nim" not in (result.error_message or "")
    assert len(executor.calls) == 1
    view = public_view_from_run(result)
    assert view.state == "analyzed"
    assert view.result is not None
    assert view.error_code is None


def test_transient_failure_requeues_until_success_or_exhaustion() -> None:
    repository = _FakeRepository()
    scheduler = ScheduleAutomaticMediaAnalysis(repository, enabled=True, now_ms=lambda: 1)
    run = scheduler.execute(
        CatalogedAnalysisTarget(media_id=MEDIA_ID, media_location_id=LOCATION_ID)
    )
    assert run is not None
    executor = _FakeExecutor(error=MediaSuggestionProviderUnavailableError("down"))
    service = ExecuteAutomaticMediaAnalysisRun(
        repository,
        executor,
        max_attempts=2,
        now_ms=lambda: 2,
    )
    requeued = service.execute(run)
    assert requeued.state is MediaAnalysisRunState.PENDING
    failed = service.execute(requeued)
    assert failed.state is MediaAnalysisRunState.FAILED
    assert failed.error_code == "PROVIDER_UNAVAILABLE"
    assert len(executor.calls) == 2


def test_rate_limited_is_retryable_then_terminal_on_exhaustion() -> None:
    repository = _FakeRepository()
    scheduler = ScheduleAutomaticMediaAnalysis(repository, enabled=True, now_ms=lambda: 1)
    run = scheduler.execute(
        CatalogedAnalysisTarget(media_id=MEDIA_ID, media_location_id=LOCATION_ID)
    )
    assert run is not None
    executor = _FakeExecutor(error=MediaSuggestionProviderRateLimitedError("slow"))
    service = ExecuteAutomaticMediaAnalysisRun(
        repository,
        executor,
        max_attempts=1,
        now_ms=lambda: 2,
    )
    failed = service.execute(run)
    assert failed.state is MediaAnalysisRunState.FAILED
    assert failed.error_code == "PROVIDER_RATE_LIMITED"
    assert len(executor.calls) == 1
    assert "requeue_for_retry" not in repository.transactions


def test_terminal_provider_auth_refusal_is_not_retried() -> None:
    repository = _FakeRepository()
    scheduler = ScheduleAutomaticMediaAnalysis(repository, enabled=True, now_ms=lambda: 1)
    run = scheduler.execute(
        CatalogedAnalysisTarget(media_id=MEDIA_ID, media_location_id=LOCATION_ID)
    )
    assert run is not None
    executor = _FakeExecutor(error=MediaSuggestionProviderAuthError("denied"))
    service = ExecuteAutomaticMediaAnalysisRun(
        repository,
        executor,
        max_attempts=3,
        now_ms=lambda: 2,
    )
    failed = service.execute(run)
    assert failed.state is MediaAnalysisRunState.FAILED
    assert failed.error_code == "PROVIDER_AUTH"
    assert len(executor.calls) == 1
    again = service.execute(failed)
    assert again.state is MediaAnalysisRunState.FAILED
    assert len(executor.calls) == 1


def test_pending_surviving_restart_executes_normally() -> None:
    repository = _FakeRepository()
    scheduler = ScheduleAutomaticMediaAnalysis(repository, enabled=True, now_ms=lambda: 1)
    pending = scheduler.execute(
        CatalogedAnalysisTarget(media_id=MEDIA_ID, media_location_id=LOCATION_ID)
    )
    assert pending is not None
    assert pending.state is MediaAnalysisRunState.PENDING
    executor = _FakeExecutor()
    service = ExecuteAutomaticMediaAnalysisRun(repository, executor, now_ms=lambda: 2)
    result = service.execute(pending)
    assert result.state is MediaAnalysisRunState.ANALYZED
    assert len(executor.calls) == 1


def test_stale_analyzing_fails_closed_without_provider_call() -> None:
    repository = _FakeRepository()
    scheduler = ScheduleAutomaticMediaAnalysis(repository, enabled=True, now_ms=lambda: 1)
    pending = scheduler.execute(
        CatalogedAnalysisTarget(media_id=MEDIA_ID, media_location_id=LOCATION_ID)
    )
    assert pending is not None
    claimed = repository.claim_pending(
        run_id=pending.id.to_string(),
        expected_version=pending.version,
        started_at_ms=2,
        max_attempts=3,
    )
    assert claimed.state is MediaAnalysisRunState.ANALYZING
    executor = _FakeExecutor()
    service = ExecuteAutomaticMediaAnalysisRun(repository, executor, now_ms=lambda: 3)
    failed = service.execute(claimed)
    assert failed.state is MediaAnalysisRunState.FAILED
    assert failed.error_code == "ANALYSIS_OUTCOME_UNKNOWN"
    assert failed.result_json is None
    assert len(executor.calls) == 0
    view = public_view_from_run(failed)
    assert view.state == "failed"
    assert view.error_code == "ANALYSIS_OUTCOME_UNKNOWN"
    assert view.result is None
    again = service.execute(failed)
    assert again.state is MediaAnalysisRunState.FAILED
    assert len(executor.calls) == 0


def test_analyzed_run_is_never_re_executed() -> None:
    repository = _FakeRepository()
    scheduler = ScheduleAutomaticMediaAnalysis(repository, enabled=True, now_ms=lambda: 1)
    pending = scheduler.execute(
        CatalogedAnalysisTarget(media_id=MEDIA_ID, media_location_id=LOCATION_ID)
    )
    assert pending is not None
    executor = _FakeExecutor()
    service = ExecuteAutomaticMediaAnalysisRun(repository, executor, now_ms=lambda: 2)
    analyzed = service.execute(pending)
    assert analyzed.state is MediaAnalysisRunState.ANALYZED
    assert len(executor.calls) == 1
    again = service.execute(analyzed)
    assert again.state is MediaAnalysisRunState.ANALYZED
    assert len(executor.calls) == 1


def test_public_view_states_are_truthful() -> None:
    assert public_view_from_run(None).state == "not_requested"
    pending = MediaAnalysisRun(
        id=MediaAnalysisRunId("11111111-1111-4111-8111-111111111111"),
        media_id=MEDIA_ID,
        media_location_id=LOCATION_ID,
        analysis_definition=AUTOMATIC_POST_CATALOG_ANALYSIS_DEFINITION,
        state=MediaAnalysisRunState.PENDING,
        attempt_count=0,
        provider_id=None,
        model_id=None,
        prompt_version=None,
        result_schema_version=None,
        result_json=None,
        error_code=None,
        error_message=None,
        created_at_ms=1,
        started_at_ms=None,
        completed_at_ms=None,
        version=1,
    )
    pending_view = public_view_from_run(pending)
    assert pending_view.state == "pending"
    assert pending_view.result is None
    analyzing = replace(
        pending,
        state=MediaAnalysisRunState.ANALYZING,
        attempt_count=1,
        started_at_ms=2,
        version=2,
    )
    analyzing_view = public_view_from_run(analyzing)
    assert analyzing_view.state == "analyzing"
    assert analyzing_view.result is None
    suggestion = _suggestion()
    analyzed = replace(
        analyzing,
        state=MediaAnalysisRunState.ANALYZED,
        provider_id=suggestion.provider_id,
        model_id=suggestion.model_id,
        prompt_version=PROMPT_VERSION,
        result_schema_version="framenest-media-suggestion-result-v1",
        result_json=serialize_suggestion_result(suggestion),
        completed_at_ms=3,
        version=3,
    )
    analyzed_view = public_view_from_run(analyzed)
    assert isinstance(analyzed_view, AutomaticAnalysisPublicView)
    assert analyzed_view.result is not None
    assert analyzed_view.error_code is None
    failed = replace(
        analyzing,
        state=MediaAnalysisRunState.FAILED,
        error_code="ANALYSIS_OUTCOME_UNKNOWN",
        error_message=(
            "Automatic analysis was interrupted and the provider "
            "outcome cannot be determined safely."
        ),
        completed_at_ms=4,
        version=3,
    )
    failed_view = public_view_from_run(failed)
    assert failed_view.error_code == "ANALYSIS_OUTCOME_UNKNOWN"
    assert failed_view.result is None


def test_max_attempts_one_permits_single_provider_call_without_requeue() -> None:
    repository = _FakeRepository()
    scheduler = ScheduleAutomaticMediaAnalysis(repository, enabled=True, now_ms=lambda: 1)
    run = scheduler.execute(
        CatalogedAnalysisTarget(media_id=MEDIA_ID, media_location_id=LOCATION_ID)
    )
    assert run is not None
    executor = _FakeExecutor(error=MediaSuggestionProviderUnavailableError("down"))
    service = ExecuteAutomaticMediaAnalysisRun(
        repository,
        executor,
        max_attempts=1,
        now_ms=lambda: 2,
    )
    failed = service.execute(run)
    assert failed.state is MediaAnalysisRunState.FAILED
    assert failed.error_code == "PROVIDER_UNAVAILABLE"
    assert failed.attempt_count == 1
    assert "requeue_for_retry" not in repository.transactions
    assert len(executor.calls) == 1
    again = service.execute(failed)
    assert again.state is MediaAnalysisRunState.FAILED
    assert len(executor.calls) == 1


def test_higher_max_attempts_retains_bounded_retry_then_terminal() -> None:
    repository = _FakeRepository()
    scheduler = ScheduleAutomaticMediaAnalysis(repository, enabled=True, now_ms=lambda: 1)
    run = scheduler.execute(
        CatalogedAnalysisTarget(media_id=MEDIA_ID, media_location_id=LOCATION_ID)
    )
    assert run is not None
    executor = _FakeExecutor(error=MediaSuggestionProviderUnavailableError("down"))
    service = ExecuteAutomaticMediaAnalysisRun(
        repository,
        executor,
        max_attempts=3,
        now_ms=lambda: 2,
    )
    first = service.execute(run)
    assert first.state is MediaAnalysisRunState.PENDING
    assert first.attempt_count == 1
    second = service.execute(first)
    assert second.state is MediaAnalysisRunState.PENDING
    assert second.attempt_count == 2
    third = service.execute(second)
    assert third.state is MediaAnalysisRunState.FAILED
    assert third.error_code == "PROVIDER_UNAVAILABLE"
    assert third.attempt_count == 3
    assert repository.transactions.count("requeue_for_retry") == 2
    assert len(executor.calls) == 3


def test_startup_reconciliation_does_not_bypass_configured_max_attempts() -> None:
    repository = _FakeRepository()
    scheduler = ScheduleAutomaticMediaAnalysis(repository, enabled=True, now_ms=lambda: 1)
    pending = scheduler.execute(
        CatalogedAnalysisTarget(media_id=MEDIA_ID, media_location_id=LOCATION_ID)
    )
    assert pending is not None
    claimed = repository.claim_pending(
        run_id=pending.id.to_string(),
        expected_version=pending.version,
        started_at_ms=2,
        max_attempts=1,
    )
    assert claimed.attempt_count == 1
    executor = _FakeExecutor()
    service = ExecuteAutomaticMediaAnalysisRun(
        repository,
        executor,
        max_attempts=1,
        now_ms=lambda: 3,
    )
    failed = service.execute(claimed)
    assert failed.state is MediaAnalysisRunState.FAILED
    assert failed.error_code == "ANALYSIS_OUTCOME_UNKNOWN"
    assert failed.attempt_count == 1
    assert len(executor.calls) == 0
    assert "requeue_for_retry" not in repository.transactions
    assert repository.transactions.count("reset_interrupted_analyzing") == 1


def test_max_attempts_rejects_zero_and_above_configured_bound() -> None:
    repository = _FakeRepository()
    executor = _FakeExecutor()
    with pytest.raises(ValueError):
        ExecuteAutomaticMediaAnalysisRun(repository, executor, max_attempts=0)
    with pytest.raises(ValueError):
        ExecuteAutomaticMediaAnalysisRun(repository, executor, max_attempts=-1)
    with pytest.raises(ValueError):
        ExecuteAutomaticMediaAnalysisRun(repository, executor, max_attempts=11)


def test_no_fallback_provider_is_selected_on_retryable_exhaustion() -> None:
    repository = _FakeRepository()
    scheduler = ScheduleAutomaticMediaAnalysis(repository, enabled=True, now_ms=lambda: 1)
    run = scheduler.execute(
        CatalogedAnalysisTarget(media_id=MEDIA_ID, media_location_id=LOCATION_ID)
    )
    assert run is not None
    executor = _FakeExecutor(error=MediaSuggestionProviderRateLimitedError("slow"))
    service = ExecuteAutomaticMediaAnalysisRun(
        repository,
        executor,
        max_attempts=1,
        now_ms=lambda: 2,
    )
    failed = service.execute(run)
    assert failed.state is MediaAnalysisRunState.FAILED
    assert failed.provider_id is None
    assert failed.model_id is None
    assert len(executor.calls) == 1
