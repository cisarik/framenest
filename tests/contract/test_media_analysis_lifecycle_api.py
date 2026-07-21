"""Contract tests for durable automatic media analysis status API."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from framenest.adapters.api.application import create_app
from framenest.adapters.api.library_api import LibraryApiDependencies
from framenest.adapters.api.media_analysis_api import MediaAnalysisApiDependencies
from framenest.adapters.api.media_analysis_lifecycle_api import (
    MediaAnalysisLifecycleApiDependencies,
)
from framenest.adapters.api.media_suggestion_api import MediaSuggestionApiDependencies
from framenest.application.media_analysis_lifecycle import (
    AutomaticAnalysisPublicView,
    ReadAutomaticMediaAnalysis,
)
from framenest.configuration import FrameNestSettings
from framenest.domain.identities import MediaId

CANONICAL_MEDIA_ID = "aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee"
PRIVATE_PATH = "/Users/example/private/videos/secret.mp4"
SECRET = "sk-test-secret-value"


class _FakeReadAnalysis:
    def __init__(self, view: AutomaticAnalysisPublicView) -> None:
        self.view = view
        self.calls: list[MediaId] = []

    def execute(self, media_id: MediaId) -> AutomaticAnalysisPublicView:
        self.calls.append(media_id)
        return self.view


def _client(view: AutomaticAnalysisPublicView, *, enabled: bool = True) -> TestClient:
    reader = _FakeReadAnalysis(view)
    settings = FrameNestSettings(
        host="127.0.0.1",
        database_path=Path("/tmp/framenest-analysis-lifecycle-api.sqlite3"),
        automatic_media_analysis_enabled=enabled,
        _env_file=None,
    )
    app = create_app(
        settings=settings,
        library_api_dependencies=LibraryApiDependencies(
            repository=object(),  # type: ignore[arg-type]
            scan_preview=object(),
            catalog_available=lambda: True,
        ),
        media_analysis_api_dependencies=MediaAnalysisApiDependencies(
            prepare_preview=object(),
            catalog_available=lambda: True,
        ),
        media_suggestion_api_dependencies=MediaSuggestionApiDependencies(
            preview_suggestion=None,
            provider_configured=False,
        ),
        media_analysis_lifecycle_api_dependencies=MediaAnalysisLifecycleApiDependencies(
            read_analysis=reader,  # type: ignore[arg-type]
            automatic_analysis_enabled=enabled,
            provider_configured=True,
            provider_id="nvidia-nim",
            model_id="test-model",
        ),
    )
    return TestClient(app)


def test_capability_and_not_requested_status() -> None:
    client = _client(
        AutomaticAnalysisPublicView(
            state="not_requested",
            analysis_definition=None,
            provider_id=None,
            model_id=None,
            prompt_version=None,
            result=None,
            error_code=None,
            error_message=None,
            attempt_count=None,
            created_at_ms=None,
            started_at_ms=None,
            completed_at_ms=None,
        ),
        enabled=False,
    )
    capability = client.get("/api/ai/automatic-analysis-capability")
    assert capability.status_code == 200
    assert capability.json() == {
        "automatic_analysis_enabled": False,
        "analysis_definition": "automatic_post_catalog",
        "result_schema_version": "framenest-media-suggestion-result-v1",
        "provider_configured": True,
        "provider_id": "nvidia-nim",
        "model_id": "test-model",
    }
    status = client.get(f"/api/media/{CANONICAL_MEDIA_ID}/automatic-analysis")
    assert status.status_code == 200
    payload = status.json()
    assert payload["state"] == "not_requested"
    assert payload["result"] is None
    assert payload["error_code"] is None
    assert SECRET not in status.text
    assert PRIVATE_PATH not in status.text


def test_pending_and_analyzing_omit_result() -> None:
    for state in ("pending", "analyzing"):
        client = _client(
            AutomaticAnalysisPublicView(
                state=state,
                analysis_definition="automatic_post_catalog",
                provider_id=None,
                model_id=None,
                prompt_version=None,
                result=None,
                error_code=None,
                error_message=None,
                attempt_count=1 if state == "analyzing" else 0,
                created_at_ms=10,
                started_at_ms=11 if state == "analyzing" else None,
                completed_at_ms=None,
            )
        )
        payload = client.get(f"/api/media/{CANONICAL_MEDIA_ID}/automatic-analysis").json()
        assert payload["state"] == state
        assert payload["result"] is None
        assert payload["error_code"] is None


def test_analyzed_returns_normalized_result_only() -> None:
    client = _client(
        AutomaticAnalysisPublicView(
            state="analyzed",
            analysis_definition="automatic_post_catalog",
            provider_id="nvidia-nim",
            model_id="test-model",
            prompt_version="framenest-media-suggestion-v3",
            result={
                "title": "Title",
                "description": "Description",
                "collection": "Collection",
                "tags": ["one"],
                "suggested_filename": "title.mp4",
                "confidence": 0.5,
                "evidence": ["frame"],
                "uncertainties": [],
            },
            error_code=None,
            error_message=None,
            attempt_count=1,
            created_at_ms=10,
            started_at_ms=11,
            completed_at_ms=12,
        )
    )
    payload = client.get(f"/api/media/{CANONICAL_MEDIA_ID}/automatic-analysis").json()
    assert payload["state"] == "analyzed"
    assert payload["result"]["title"] == "Title"
    assert payload["error_code"] is None
    assert PRIVATE_PATH not in str(payload)
    assert SECRET not in str(payload)


def test_failed_returns_sanitized_error_without_result() -> None:
    client = _client(
        AutomaticAnalysisPublicView(
            state="failed",
            analysis_definition="automatic_post_catalog",
            provider_id=None,
            model_id=None,
            prompt_version="framenest-media-suggestion-v3",
            result=None,
            error_code="PROVIDER_UNAVAILABLE",
            error_message="AI provider is temporarily unavailable.",
            attempt_count=3,
            created_at_ms=10,
            started_at_ms=11,
            completed_at_ms=12,
        )
    )
    payload = client.get(f"/api/media/{CANONICAL_MEDIA_ID}/automatic-analysis").json()
    assert payload["state"] == "failed"
    assert payload["result"] is None
    assert payload["error_code"] == "PROVIDER_UNAVAILABLE"
    assert SECRET not in payload["error_message"]
    assert PRIVATE_PATH not in payload["error_message"]


def test_ambiguous_outcome_failure_exposes_sanitized_classification_only() -> None:
    client = _client(
        AutomaticAnalysisPublicView(
            state="failed",
            analysis_definition="automatic_post_catalog",
            provider_id=None,
            model_id=None,
            prompt_version="framenest-media-suggestion-v3",
            result=None,
            error_code="ANALYSIS_OUTCOME_UNKNOWN",
            error_message=(
                "Automatic analysis was interrupted and the provider "
                "outcome cannot be determined safely."
            ),
            attempt_count=1,
            created_at_ms=10,
            started_at_ms=11,
            completed_at_ms=12,
        )
    )
    response = client.get(f"/api/media/{CANONICAL_MEDIA_ID}/automatic-analysis")
    assert response.status_code == 200
    payload = response.json()
    assert payload["state"] == "failed"
    assert payload["result"] is None
    assert payload["error_code"] == "ANALYSIS_OUTCOME_UNKNOWN"
    assert SECRET not in response.text
    assert PRIVATE_PATH not in response.text
    assert "/tmp/" not in response.text


def test_analyzed_read_is_side_effect_free_and_does_not_schedule_provider_work() -> None:
    reader = _FakeReadAnalysis(
        AutomaticAnalysisPublicView(
            state="analyzed",
            analysis_definition="automatic_post_catalog",
            provider_id="nvidia-nim",
            model_id="test-model",
            prompt_version="framenest-media-suggestion-v3",
            result={
                "title": "Title",
                "description": "Description",
                "collection": "Collection",
                "tags": ["one"],
                "suggested_filename": "title.mp4",
                "confidence": 0.5,
                "evidence": ["frame"],
                "uncertainties": [],
            },
            error_code=None,
            error_message=None,
            attempt_count=1,
            created_at_ms=10,
            started_at_ms=11,
            completed_at_ms=12,
        )
    )
    settings = FrameNestSettings(
        host="127.0.0.1",
        database_path=Path("/tmp/framenest-analysis-lifecycle-api-side-effect.sqlite3"),
        automatic_media_analysis_enabled=True,
        _env_file=None,
    )
    app = create_app(
        settings=settings,
        library_api_dependencies=LibraryApiDependencies(
            repository=object(),  # type: ignore[arg-type]
            scan_preview=object(),
            catalog_available=lambda: True,
        ),
        media_analysis_api_dependencies=MediaAnalysisApiDependencies(
            prepare_preview=object(),
            catalog_available=lambda: True,
        ),
        media_suggestion_api_dependencies=MediaSuggestionApiDependencies(
            preview_suggestion=None,
            provider_configured=False,
        ),
        media_analysis_lifecycle_api_dependencies=MediaAnalysisLifecycleApiDependencies(
            read_analysis=reader,  # type: ignore[arg-type]
            automatic_analysis_enabled=True,
            provider_configured=True,
            provider_id="nvidia-nim",
            model_id="test-model",
        ),
    )
    client = TestClient(app)
    first = client.get(f"/api/media/{CANONICAL_MEDIA_ID}/automatic-analysis")
    second = client.get(f"/api/media/{CANONICAL_MEDIA_ID}/automatic-analysis")
    assert first.status_code == 200
    assert second.status_code == 200
    assert len(reader.calls) == 2
    assert first.json()["result"]["title"] == "Title"
    assert first.json() == second.json()
    assert SECRET not in first.text
    assert PRIVATE_PATH not in first.text


def test_manual_durable_analysis_request_requires_confirmation_and_schedules() -> None:
    calls: list[tuple[MediaId, object]] = []

    def _request(media_id: MediaId, location_id: object) -> object:
        from framenest.domain.media_analysis_runs import (
            AUTOMATIC_POST_CATALOG_ANALYSIS_DEFINITION,
            MediaAnalysisRun,
            MediaAnalysisRunId,
            MediaAnalysisRunState,
        )
        from framenest.domain.identities import MediaLocationId

        assert isinstance(location_id, MediaLocationId)
        calls.append((media_id, location_id))
        return MediaAnalysisRun(
            id=MediaAnalysisRunId("11111111-1111-4111-8111-111111111111"),
            media_id=media_id,
            media_location_id=location_id,
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
            created_at_ms=10,
            started_at_ms=None,
            completed_at_ms=None,
            version=1,
        )

    location_id = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"
    settings = FrameNestSettings(
        host="127.0.0.1",
        database_path=Path("/tmp/framenest-analysis-lifecycle-api-manual.sqlite3"),
        automatic_media_analysis_enabled=False,
        _env_file=None,
    )
    app = create_app(
        settings=settings,
        library_api_dependencies=LibraryApiDependencies(
            repository=object(),  # type: ignore[arg-type]
            scan_preview=object(),
            catalog_available=lambda: True,
        ),
        media_analysis_api_dependencies=MediaAnalysisApiDependencies(
            prepare_preview=object(),
            catalog_available=lambda: True,
        ),
        media_suggestion_api_dependencies=MediaSuggestionApiDependencies(
            preview_suggestion=None,
            provider_configured=False,
        ),
        media_analysis_lifecycle_api_dependencies=MediaAnalysisLifecycleApiDependencies(
            read_analysis=_FakeReadAnalysis(
                AutomaticAnalysisPublicView(
                    state="not_requested",
                    analysis_definition=None,
                    provider_id=None,
                    model_id=None,
                    prompt_version=None,
                    result=None,
                    error_code=None,
                    error_message=None,
                    attempt_count=None,
                    created_at_ms=None,
                    started_at_ms=None,
                    completed_at_ms=None,
                )
            ),  # type: ignore[arg-type]
            automatic_analysis_enabled=False,
            provider_configured=True,
            provider_id="nvidia-nim",
            model_id="test-model",
            request_manual_analysis=_request,  # type: ignore[arg-type]
        ),
    )
    client = TestClient(app)
    denied = client.post(
        f"/api/media/{CANONICAL_MEDIA_ID}/locations/{location_id}/durable-analysis",
        json={"confirm_cloud_upload": False},
    )
    assert denied.status_code == 409
    assert denied.json()["error"]["code"] == "CLOUD_CONFIRMATION_REQUIRED"
    assert calls == []
    accepted = client.post(
        f"/api/media/{CANONICAL_MEDIA_ID}/locations/{location_id}/durable-analysis",
        json={"confirm_cloud_upload": True},
    )
    assert accepted.status_code == 200
    payload = accepted.json()
    assert payload["state"] == "pending"
    assert payload["automatic_analysis_enabled"] is False
    assert payload["result"] is None
    assert len(calls) == 1
    assert SECRET not in accepted.text
    assert PRIVATE_PATH not in accepted.text
