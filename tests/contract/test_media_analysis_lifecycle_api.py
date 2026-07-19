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
