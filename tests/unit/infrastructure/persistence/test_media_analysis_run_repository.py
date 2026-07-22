"""Persistence tests for durable automatic media analysis runs."""

from __future__ import annotations

from pathlib import Path

import pytest
from alembic import command

from framenest.application.ports.media_analysis_runs import MediaAnalysisRunConflictError
from framenest.configuration import FrameNestSettings
from framenest.domain.identities import MediaId, MediaLocationId
from framenest.domain.media_analysis_runs import (
    AUTOMATIC_POST_CATALOG_ANALYSIS_DEFINITION,
    MediaAnalysisRunState,
)
from framenest.infrastructure.persistence.engine import (
    create_sqlite_engine,
    dispose_engine,
)
from framenest.infrastructure.persistence.media_analysis_run_repository import (
    SqliteMediaAnalysisRunRepository,
)
from framenest.infrastructure.persistence.migrations import _alembic_config


MEDIA_ID = MediaId.from_string("eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee")
LOCATION_ID = MediaLocationId.from_string("ffffffff-ffff-4fff-8fff-ffffffffffff")


def _migrate(database_path: Path) -> None:
    engine = create_sqlite_engine(database_path)
    try:
        with engine.connect() as connection:
            with _alembic_config(
                "framenest.infrastructure.persistence.alembic_environment"
            ) as config:
                config.attributes["connection"] = connection
                command.upgrade(config, "head")
        with engine.begin() as connection:
            connection.exec_driver_sql(
                "INSERT INTO devices (id, display_name) VALUES (?, 'Synthetic')"
                ,
                ("dddddddd-dddd-4ddd-8ddd-dddddddddddd",),
            )
            connection.exec_driver_sql(
                """
                INSERT INTO libraries (id, device_id, display_name, path_flavor, root_path)
                VALUES (?, ?, 'Library', 'posix', '/synthetic')
                """,
                (
                    "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb",
                    "dddddddd-dddd-4ddd-8ddd-dddddddddddd",
                ),
            )
            connection.exec_driver_sql(
                """
                INSERT INTO logical_media (id, media_kind, created_at_ms, updated_at_ms)
                VALUES (?, 'video', 1, 1)
                """,
                (MEDIA_ID.to_string(),),
            )
            connection.exec_driver_sql(
                """
                INSERT INTO physical_media_locations (
                    id, media_id, library_id, relative_path, availability,
                    observed_size_bytes, observed_mtime_ns, created_at_ms, updated_at_ms
                ) VALUES (?, ?, ?, 'clip.mp4', 'available', 8, NULL, 1, 1)
                """,
                (
                    LOCATION_ID.to_string(),
                    MEDIA_ID.to_string(),
                    "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb",
                ),
            )
    finally:
        dispose_engine(engine)


@pytest.fixture
def repository(tmp_path: Path) -> SqliteMediaAnalysisRunRepository:
    database_path = tmp_path / "catalog.sqlite3"
    _migrate(database_path)
    engine = create_sqlite_engine(database_path)
    repo = SqliteMediaAnalysisRunRepository(engine)
    yield repo
    dispose_engine(engine)


def test_create_pending_is_idempotent(repository: SqliteMediaAnalysisRunRepository) -> None:
    first = repository.create_pending(
        media_id=MEDIA_ID,
        media_location_id=LOCATION_ID,
        analysis_definition=AUTOMATIC_POST_CATALOG_ANALYSIS_DEFINITION,
        created_at_ms=10,
    )
    second = repository.create_pending(
        media_id=MEDIA_ID,
        media_location_id=LOCATION_ID,
        analysis_definition=AUTOMATIC_POST_CATALOG_ANALYSIS_DEFINITION,
        created_at_ms=20,
    )
    assert first.id.to_string() == second.id.to_string()
    assert first.state is MediaAnalysisRunState.PENDING
    assert second.created_at_ms == 10


def test_claim_and_record_analyzed_outside_contradictory_states(
    repository: SqliteMediaAnalysisRunRepository,
) -> None:
    pending = repository.create_pending(
        media_id=MEDIA_ID,
        media_location_id=LOCATION_ID,
        analysis_definition=AUTOMATIC_POST_CATALOG_ANALYSIS_DEFINITION,
        created_at_ms=10,
    )
    claimed = repository.claim_pending(
        run_id=pending.id.to_string(),
        expected_version=pending.version,
        started_at_ms=11,
        max_attempts=3,
    )
    assert claimed.state is MediaAnalysisRunState.ANALYZING
    assert claimed.attempt_count == 1
    analyzed = repository.record_analyzed(
        run_id=claimed.id.to_string(),
        expected_version=claimed.version,
        provider_id="nvidia-nim",
        model_id="model",
        prompt_version="framenest-media-suggestion-v3",
        result_schema_version="framenest-media-suggestion-result-v1",
        result_json='{"title":"T","description":"D","collection":"C","tags":["a"],'
        '"suggested_filename":"t.mp4","confidence":0.5,"evidence":["e"],'
        '"uncertainties":[]}',
        completed_at_ms=12,
    )
    assert analyzed.state is MediaAnalysisRunState.ANALYZED
    assert analyzed.result_json is not None
    with pytest.raises(MediaAnalysisRunConflictError):
        repository.claim_pending(
            run_id=analyzed.id.to_string(),
            expected_version=analyzed.version,
            started_at_ms=13,
            max_attempts=3,
        )


def test_requeue_and_terminal_failure(
    repository: SqliteMediaAnalysisRunRepository,
) -> None:
    pending = repository.create_pending(
        media_id=MEDIA_ID,
        media_location_id=LOCATION_ID,
        analysis_definition=AUTOMATIC_POST_CATALOG_ANALYSIS_DEFINITION,
        created_at_ms=10,
    )
    claimed = repository.claim_pending(
        run_id=pending.id.to_string(),
        expected_version=pending.version,
        started_at_ms=11,
        max_attempts=3,
    )
    requeued = repository.requeue_for_retry(
        run_id=claimed.id.to_string(),
        expected_version=claimed.version,
        error_code="PROVIDER_UNAVAILABLE",
        error_message="temporary",
        updated_at_ms=12,
    )
    assert requeued.state is MediaAnalysisRunState.PENDING
    assert requeued.started_at_ms is None
    claimed_again = repository.claim_pending(
        run_id=requeued.id.to_string(),
        expected_version=requeued.version,
        started_at_ms=13,
        max_attempts=3,
    )
    failed = repository.record_failed(
        run_id=claimed_again.id.to_string(),
        expected_version=claimed_again.version,
        error_code="PROVIDER_AUTH",
        error_message="AI provider authentication failed.",
        provider_id=None,
        model_id=None,
        prompt_version="framenest-media-suggestion-v3",
        completed_at_ms=14,
        provider_submission_occurred=True,
    )
    assert failed.state is MediaAnalysisRunState.FAILED
    assert failed.error_code == "PROVIDER_AUTH"
    assert failed.result_json is None
    assert failed.provider_submission_occurred is True


def test_reset_interrupted_analyzing_fails_closed_as_outcome_unknown(
    repository: SqliteMediaAnalysisRunRepository,
) -> None:
    pending = repository.create_pending(
        media_id=MEDIA_ID,
        media_location_id=LOCATION_ID,
        analysis_definition=AUTOMATIC_POST_CATALOG_ANALYSIS_DEFINITION,
        created_at_ms=10,
    )
    claimed = repository.claim_pending(
        run_id=pending.id.to_string(),
        expected_version=pending.version,
        started_at_ms=11,
        max_attempts=3,
    )
    assert claimed.state is MediaAnalysisRunState.ANALYZING
    assert claimed.attempt_count == 1
    failed = repository.reset_interrupted_analyzing(
        run_id=claimed.id.to_string(),
        expected_version=claimed.version,
        max_attempts=3,
        updated_at_ms=12,
    )
    assert failed.state is MediaAnalysisRunState.FAILED
    assert failed.error_code == "ANALYSIS_OUTCOME_UNKNOWN"
    assert failed.result_json is None
    assert "ANALYSIS_OUTCOME_UNKNOWN" == failed.error_code
    assert failed.error_message is not None
    assert "/home/" not in failed.error_message
    assert "sk-" not in failed.error_message
    # Must not return to pending under remaining attempts.
    assert failed.state is not MediaAnalysisRunState.PENDING
    listed = repository.list_unfinished(limit=8)
    assert listed == ()


def test_crash_window_provider_success_then_interrupt_does_not_replay_provider(
    repository: SqliteMediaAnalysisRunRepository,
) -> None:
    """Reproduce ambiguous crash: provider OK, analyzed row never written."""
    from framenest.application.media_analysis_lifecycle import (
        ExecuteAutomaticMediaAnalysisRun,
    )
    from framenest.application.media_suggestion import MediaSuggestion, PROMPT_VERSION

    pending = repository.create_pending(
        media_id=MEDIA_ID,
        media_location_id=LOCATION_ID,
        analysis_definition=AUTOMATIC_POST_CATALOG_ANALYSIS_DEFINITION,
        created_at_ms=10,
    )
    calls = {"n": 0}

    class _CountingProvider:
        def execute(self, media_id, location_id):
            del media_id, location_id
            calls["n"] += 1
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

    service = ExecuteAutomaticMediaAnalysisRun(
        repository,
        _CountingProvider(),
        max_attempts=3,
        now_ms=lambda: 20,
    )
    claimed = repository.claim_pending(
        run_id=pending.id.to_string(),
        expected_version=pending.version,
        started_at_ms=11,
        max_attempts=3,
    )
    # External provider succeeds once; process dies before record_analyzed.
    _ = service._executor.execute(claimed.media_id, claimed.media_location_id)
    assert calls["n"] == 1
    surviving = repository.get_by_media_definition(
        MEDIA_ID,
        AUTOMATIC_POST_CATALOG_ANALYSIS_DEFINITION,
    )
    assert surviving is not None
    assert surviving.state is MediaAnalysisRunState.ANALYZING

    recovered = service.execute(surviving)
    assert recovered.state is MediaAnalysisRunState.FAILED
    assert recovered.error_code == "ANALYSIS_OUTCOME_UNKNOWN"
    assert calls["n"] == 1

    second_restart = service.execute(recovered)
    assert second_restart.state is MediaAnalysisRunState.FAILED
    assert calls["n"] == 1
    assert repository.list_unfinished(limit=8) == ()

    # Repeated catalog-equivalent create must not invent another paid job.
    again = repository.create_pending(
        media_id=MEDIA_ID,
        media_location_id=LOCATION_ID,
        analysis_definition=AUTOMATIC_POST_CATALOG_ANALYSIS_DEFINITION,
        created_at_ms=30,
    )
    assert again.id.to_string() == recovered.id.to_string()
    assert again.state is MediaAnalysisRunState.FAILED
    assert calls["n"] == 1
