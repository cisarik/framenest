"""Contract evidence for the loopback-only YouTube operator API."""

from __future__ import annotations

from dataclasses import replace

from fastapi import FastAPI
from fastapi.testclient import TestClient

from framenest.adapters.api.youtube_operator_api import (
    YouTubeOperatorApiDependencies,
    create_youtube_operator_api_router,
)
from framenest.application.youtube_acquisition import (
    YouTubeAcquisitionInfrastructureError,
    YouTubeAcquisitionInvalidRequestError,
    YouTubeClaimSnapshot,
    YouTubeClaimSubmission,
)
from framenest.domain.youtube_acquisition import (
    FrameNestYouTubeUrlError,
    canonicalize_youtube_url,
)

CLAIM_ID = "11111111-1111-4111-8111-111111111111"
VIDEO_ID = "AbCdEf123_-"


def _snapshot(**changes: object) -> YouTubeClaimSnapshot:
    snapshot = YouTubeClaimSnapshot(
        id=CLAIM_ID,
        state="claimed",
        acquisition_source="youtube_manual_claim",
        youtube_video_id=VIDEO_ID,
        upload_id=None,
        upload_state=None,
        media_id=None,
        media_location_id=None,
        result=None,
        downloaded_size_bytes=None,
        failure_stage=None,
        failure_code=None,
        cleanup_state="pending",
        retry_of_claim_id=None,
        resolved_claim_id=None,
        created_at_ms=10,
        updated_at_ms=10,
        completed_at_ms=None,
        version=0,
    )
    return replace(snapshot, **changes)


class _Service:
    def __init__(self) -> None:
        self.submissions: list[tuple[str, str]] = []
        self.retries: list[tuple[str, str]] = []
        self.failure: Exception | None = None

    def submit(self, *, submitted_url, confirmation_method):
        if self.failure is not None:
            raise self.failure
        try:
            identity = canonicalize_youtube_url(submitted_url)
        except FrameNestYouTubeUrlError as exc:
            raise YouTubeAcquisitionInvalidRequestError(
                "raw submitted target must remain private"
            ) from exc
        assert identity.video_id == VIDEO_ID
        self.submissions.append((submitted_url, confirmation_method.value))
        return YouTubeClaimSubmission(_snapshot(), created=True)

    def get(self, claim_id):
        if self.failure is not None:
            raise self.failure
        assert claim_id.to_string() == CLAIM_ID
        return _snapshot()

    def retry(self, claim_id, *, confirmation_method):
        if self.failure is not None:
            raise self.failure
        self.retries.append((claim_id.to_string(), confirmation_method.value))
        return YouTubeClaimSubmission(
            _snapshot(retry_of_claim_id=CLAIM_ID),
            created=True,
        )


def _client(
    service: object | None,
    *,
    enabled: bool = True,
    peer: str = "127.0.0.1",
) -> TestClient:
    app = FastAPI()
    app.include_router(
        create_youtube_operator_api_router(
            YouTubeOperatorApiDependencies(
                service=service,
                enabled=enabled,
            )
        )
    )
    return TestClient(app, client=(peer, 50_000))


def test_loopback_create_get_and_retry_use_bounded_server_service() -> None:
    service = _Service()
    with _client(service) as client:
        created = client.post(
            "/api/operator/youtube/claims",
            content=(
                '{"url":"https://youtu.be/AbCdEf123_-",'
                '"confirmation_method":"yes_flag"}'
            ),
            headers={"Content-Type": "application/json"},
        )
        status = client.get(
            f"/api/operator/youtube/claims/{CLAIM_ID}"
        )
        retried = client.post(
            f"/api/operator/youtube/claims/{CLAIM_ID}/retry",
            content='{"confirmation_method":"interactive"}',
            headers={"Content-Type": "application/json"},
        )

    assert created.status_code == 201
    assert created.json()["id"] == CLAIM_ID
    assert created.json()["state"] == "claimed"
    assert status.status_code == 200
    assert retried.status_code == 201
    assert service.submissions == [
        ("https://youtu.be/AbCdEf123_-", "yes_flag")
    ]
    assert service.retries == [(CLAIM_ID, "interactive")]


def test_non_loopback_origin_and_non_loopback_bind_are_rejected() -> None:
    service = _Service()
    with _client(service, peer="192.0.2.10") as client:
        peer_response = client.get(
            f"/api/operator/youtube/claims/{CLAIM_ID}"
        )
    with _client(service) as client:
        origin_response = client.get(
            f"/api/operator/youtube/claims/{CLAIM_ID}",
            headers={"Origin": "http://127.0.0.1:8000"},
        )
    with _client(service, enabled=False) as client:
        disabled_response = client.get(
            f"/api/operator/youtube/claims/{CLAIM_ID}"
        )

    assert peer_response.status_code == 403
    assert (
        peer_response.json()["error"]["code"]
        == "YOUTUBE_OPERATOR_LOOPBACK_REQUIRED"
    )
    assert origin_response.status_code == 403
    assert (
        origin_response.json()["error"]["code"]
        == "YOUTUBE_OPERATOR_ORIGIN_FORBIDDEN"
    )
    assert disabled_response.status_code == 503
    assert (
        disabled_response.json()["error"]["code"]
        == "YOUTUBE_OPERATOR_NOT_CONFIGURED"
    )
    assert service.submissions == []


def test_exact_json_media_type_unknown_fields_and_client_provenance_are_rejected() -> None:
    service = _Service()
    with _client(service) as client:
        charset = client.post(
            "/api/operator/youtube/claims",
            content='{"url":"x","confirmation_method":"yes_flag"}',
            headers={"Content-Type": "application/json; charset=utf-8"},
        )
        unknown = client.post(
            "/api/operator/youtube/claims",
            content=(
                '{"url":"https://youtu.be/AbCdEf123_-",'
                '"confirmation_method":"yes_flag","canonical_url":"forged"}'
            ),
            headers={"Content-Type": "application/json"},
        )
        malformed = client.post(
            "/api/operator/youtube/claims",
            content="{",
            headers={"Content-Type": "application/json"},
        )
        oversized = client.post(
            "/api/operator/youtube/claims",
            content='{"url":"' + ("x" * 5_000) + '"}',
            headers={"Content-Type": "application/json"},
        )

    assert charset.status_code == 415
    assert unknown.status_code == 400
    assert malformed.status_code == 400
    assert oversized.status_code == 413
    assert service.submissions == []


def test_invalid_url_and_internal_failure_are_sanitized() -> None:
    service = _Service()
    with _client(service) as client:
        invalid = client.post(
            "/api/operator/youtube/claims",
            content=(
                '{"url":"https://evil.example/private",'
                '"confirmation_method":"yes_flag"}'
            ),
            headers={"Content-Type": "application/json"},
        )
        service.failure = YouTubeAcquisitionInfrastructureError(
            "raw /private/path secret upstream error"
        )
        failed = client.get(
            f"/api/operator/youtube/claims/{CLAIM_ID}"
        )

    assert invalid.status_code == 400
    assert (
        invalid.json()["error"]["code"]
        == "YOUTUBE_OPERATOR_INVALID_URL"
    )
    assert "evil.example" not in invalid.text
    assert failed.status_code == 503
    assert "/private/path" not in failed.text
    assert "secret" not in failed.text
