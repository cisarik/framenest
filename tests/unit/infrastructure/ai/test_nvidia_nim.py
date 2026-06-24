"""Unit tests for the NVIDIA NIM media suggestion adapter."""

from __future__ import annotations

import base64
import json

import pytest

from framenest.application.library_scan import LibraryScanCandidateKind
from framenest.application.media_analysis import (
    PNG_SIGNATURE,
    RepresentativeFrame,
    TechnicalMetadata,
    build_representative_frame,
)
from framenest.application.media_suggestion import (
    MediaSuggestionProviderAuthError,
    MediaSuggestionProviderFailedError,
    MediaSuggestionProviderInvalidResponseError,
    MediaSuggestionProviderRateLimitedError,
    MediaSuggestionProviderUnavailableError,
    MediaSuggestionRequest,
    PROMPT_VERSION,
    SUGGESTION_PROVIDER_AUTH_MESSAGE,
)
from framenest.infrastructure.ai.constants import DEFAULT_MODEL_ID, NVIDIA_CHAT_COMPLETIONS_URL
from framenest.infrastructure.ai.credentials import NvidiaApiCredential
from framenest.infrastructure.ai.nvidia_nim import (
    NvidiaNimMediaSuggestionProvider,
    build_nvidia_request_body,
    extract_message_content,
    parse_suggestion_content_text,
)
from framenest.infrastructure.ai.transport import (
    HttpsJsonResponse,
    HttpsTransportError,
    TRANSPORT_AUTH_REJECTED_MESSAGE,
    TRANSPORT_RATE_LIMITED_MESSAGE,
    TRANSPORT_UNAVAILABLE_MESSAGE,
)

_SECRET = "test-nvidia-secret-value"
_SENSITIVE_PATH = "/sensitive-example/private-media.mp4"
_VALID_PNG = PNG_SIGNATURE + b"png"


class _FakeTransport:
    def __init__(self, *, status_code: int = 200, body: bytes | None = None, error: Exception | None = None) -> None:
        self.status_code = status_code
        self.body = body
        self.error = error
        self.last_url: str | None = None
        self.last_headers: dict[str, str] | None = None
        self.last_body: bytes | None = None

    def post_json(
        self,
        url: str,
        *,
        headers: dict[str, str],
        body: bytes,
        max_request_bytes: int,
    ) -> HttpsJsonResponse:
        self.last_url = url
        self.last_headers = headers
        self.last_body = body
        if self.error is not None:
            raise self.error
        assert self.body is not None
        return HttpsJsonResponse(status_code=self.status_code, body=self.body)


def _sample_request() -> MediaSuggestionRequest:
    return MediaSuggestionRequest(
        basename="clip.mp4",
        candidate_kind=LibraryScanCandidateKind.VIDEO,
        technical_metadata=TechnicalMetadata(
            duration_ms=1000,
            width=64,
            height=48,
            video_codec="h264",
            container_formats=("mp4",),
            has_audio=False,
        ),
        representative_frames=(
            build_representative_frame(timestamp_ms=0, payload=_VALID_PNG),
        ),
        prompt_version=PROMPT_VERSION,
    )


def _provider_response_payload(content: str) -> bytes:
    return json.dumps(
        {"choices": [{"message": {"content": content}}]},
        separators=(",", ":"),
    ).encode("utf-8")


def _valid_suggestion_json() -> str:
    return json.dumps(
        {
            "title": "Evening clip",
            "description": "A short evening scene with warm light.",
            "collection": "Home",
            "tags": ["evening", "clip"],
            "suggested_filename": "evening-clip.mp4",
            "confidence": 0.72,
            "evidence": ["Warm light is visible in the frame."],
            "uncertainties": ["Exact location is unknown."],
        },
        separators=(",", ":"),
    )


def test_build_request_uses_exact_endpoint_and_data_urls() -> None:
    request = _sample_request()
    body = build_nvidia_request_body(request, model_id=DEFAULT_MODEL_ID)
    encoded = base64.b64encode(_VALID_PNG).decode("ascii")
    assert body["model"] == DEFAULT_MODEL_ID
    assert body["stream"] is False
    assert body["temperature"] == 0.2
    assert body["chat_template_kwargs"] == {"enable_thinking": False}
    content = body["messages"][0]["content"]
    assert content[0]["type"] == "text"
    assert _SENSITIVE_PATH not in json.dumps(body)
    image_parts = [part for part in content if part["type"] == "image_url"]
    assert len(image_parts) == 1
    assert image_parts[0]["image_url"]["url"] == f"data:image/png;base64,{encoded}"


def test_provider_sends_authorization_without_exposing_secret() -> None:
    transport = _FakeTransport(body=_provider_response_payload(_valid_suggestion_json()))
    provider = NvidiaNimMediaSuggestionProvider(
        NvidiaApiCredential(_SECRET),
        transport,
    )
    suggestion = provider.suggest(_sample_request())
    assert transport.last_url == NVIDIA_CHAT_COMPLETIONS_URL
    assert transport.last_headers is not None
    assert transport.last_headers["Authorization"] == f"Bearer {_SECRET}"
    assert suggestion.provider_id == "nvidia-nim"
    assert suggestion.model_id == DEFAULT_MODEL_ID
    assert _SECRET not in repr(provider)
    assert _SECRET not in suggestion.title


def test_provider_parses_exact_fenced_json() -> None:
    fenced = f"```json\n{_valid_suggestion_json()}\n```"
    transport = _FakeTransport(body=_provider_response_payload(fenced))
    provider = NvidiaNimMediaSuggestionProvider(NvidiaApiCredential(_SECRET), transport)
    suggestion = provider.suggest(_sample_request())
    assert suggestion.suggested_filename == "evening-clip.mp4"


def test_provider_rejects_unknown_fields_and_wrong_extension() -> None:
    bad_object = json.loads(_valid_suggestion_json())
    bad_object["extra"] = "value"
    with pytest.raises(MediaSuggestionProviderInvalidResponseError):
        parse_suggestion_content_text(json.dumps(bad_object))
    wrong_extension = json.loads(_valid_suggestion_json())
    wrong_extension["suggested_filename"] = "evening-clip.mov"
    transport = _FakeTransport(
        body=_provider_response_payload(json.dumps(wrong_extension, separators=(",", ":")))
    )
    provider = NvidiaNimMediaSuggestionProvider(NvidiaApiCredential(_SECRET), transport)
    with pytest.raises(MediaSuggestionProviderInvalidResponseError):
        provider.suggest(_sample_request())


@pytest.mark.parametrize(
    ("error", "expected"),
    [
        (HttpsTransportError(TRANSPORT_AUTH_REJECTED_MESSAGE), MediaSuggestionProviderAuthError),
        (HttpsTransportError(TRANSPORT_RATE_LIMITED_MESSAGE), MediaSuggestionProviderRateLimitedError),
        (HttpsTransportError(TRANSPORT_UNAVAILABLE_MESSAGE), MediaSuggestionProviderUnavailableError),
    ],
)
def test_provider_maps_transport_failures(error: Exception, expected: type[Exception]) -> None:
    transport = _FakeTransport(error=error)
    provider = NvidiaNimMediaSuggestionProvider(NvidiaApiCredential(_SECRET), transport)
    with pytest.raises(expected):
        provider.suggest(_sample_request())


def test_extract_message_content_rejects_missing_choice() -> None:
    with pytest.raises(MediaSuggestionProviderInvalidResponseError):
        extract_message_content({"choices": []})
