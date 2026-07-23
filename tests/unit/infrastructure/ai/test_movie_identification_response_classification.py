"""Focused fixtures for movie-identification request and response classification."""

from __future__ import annotations

import io
import json
from typing import Any

import pytest
from PIL import Image

from framenest.application.media_analysis import build_representative_frame
from framenest.application.media_suggestion import (
    MediaSuggestionProviderInvalidResponseError,
    MediaSuggestionProviderTruncatedResponseError,
)
from framenest.application.movie_identification import (
    LocalMovieHints,
    MovieIdentificationRequest,
)
from framenest.domain.media_classification import (
    MOVIE_IDENTIFICATION_MAX_TOKENS,
    MOVIE_IDENTIFICATION_REASONING_BUDGET,
    MOVIE_IDENTIFICATION_REASONING_GRACE_TOKENS,
)
from framenest.infrastructure.ai import nvidia_nim
from framenest.infrastructure.ai.credentials import NvidiaApiCredential
from framenest.infrastructure.ai.nvidia_nim import (
    MOVIE_STRUCTURED_OUTPUT_COMPATIBILITY_MODE,
    NvidiaNimMediaSuggestionProvider,
    build_nvidia_movie_identification_body,
    classify_chat_completion_choice,
)
from framenest.infrastructure.ai.transport import HttpsJsonResponse
from framenest.infrastructure.media_analysis.contact_sheet import compose_contact_sheet


VALID_UNKNOWN = {
    "identified_title": None,
    "release_year": None,
    "identification_status": "unknown",
    "confidence": "unknown",
    "candidate_titles": [],
    "genres": [],
    "description": "Unknown film.",
    "tags": [],
    "evidence_summary": "Insufficient evidence.",
}

_SECRET = "test-nvidia-secret-value"
_REASONING_SENTINEL = "private-reasoning-sentinel"
_CONTENT_SENTINEL = "private-content-sentinel"


def _png(color: tuple[int, int, int]) -> bytes:
    image = Image.new("RGB", (48, 32), color)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def _movie_request() -> MovieIdentificationRequest:
    frames = tuple(
        build_representative_frame(
            timestamp_ms=index * 100,
            payload=_png((30 + index * 40, 90, 120)),
        )
        for index in range(3)
    )
    sheet = compose_contact_sheet(frames)
    return MovieIdentificationRequest(
        basename="synthetic.mp4",
        contact_sheet=sheet,
        hints=LocalMovieHints(
            filename_stem="synthetic",
            container_title=None,
            duration_ms=3000,
            width=48,
            height=32,
        ),
    )


class _FakeTransport:
    def __init__(
        self,
        *,
        body: bytes,
        status_code: int = 200,
        content_type: str | None = "application/json",
    ) -> None:
        self.post_response = HttpsJsonResponse(
            status_code=status_code,
            body=body,
            content_type=content_type,
        )
        self.post_calls: list[tuple[str, dict[str, str], bytes]] = []
        self.get_calls: list[tuple[str, dict[str, str]]] = []

    def post_json(
        self,
        url: str,
        *,
        headers: dict[str, str],
        body: bytes,
        max_request_bytes: int,
    ) -> HttpsJsonResponse:
        del max_request_bytes
        self.post_calls.append((url, dict(headers), body))
        return self.post_response

    def get_json(self, url: str, *, headers: dict[str, str]) -> HttpsJsonResponse:
        self.get_calls.append((url, dict(headers)))
        raise AssertionError("movie identification must not poll in this fixture")


class _RecordingLogger:
    def __init__(self) -> None:
        self.events: list[dict[str, Any]] = []

    def emit(self, **fields: Any) -> None:
        self.events.append(fields)


def _response_payload(
    content: object,
    *,
    finish_reason: object = "stop",
    reasoning_field: str | None = None,
) -> dict[str, object]:
    message: dict[str, object] = {"content": content}
    if reasoning_field is not None:
        message["reasoning_content"] = reasoning_field
    return {
        "id": "chatcmpl-test",
        "choices": [
            {
                "finish_reason": finish_reason,
                "message": message,
            }
        ],
    }


def _json_body(payload: object) -> bytes:
    return json.dumps(payload, separators=(",", ":")).encode("utf-8")


def _identify(
    payload: object,
    monkeypatch: pytest.MonkeyPatch,
    *,
    status_code: int = 200,
) -> tuple[object, _FakeTransport, _RecordingLogger]:
    transport = _FakeTransport(body=_json_body(payload), status_code=status_code)
    logger = _RecordingLogger()
    monkeypatch.setattr(nvidia_nim, "LOGGER", logger)
    provider = NvidiaNimMediaSuggestionProvider(
        NvidiaApiCredential(_SECRET),
        transport,
    )
    suggestion = provider.identify_movie(_movie_request())
    return suggestion, transport, logger


def test_movie_request_contract_is_documented_and_bounded() -> None:
    request = _movie_request()
    body = build_nvidia_movie_identification_body(request, model_id="fake-model")

    assert body["reasoning_budget"] == MOVIE_IDENTIFICATION_REASONING_BUDGET == 2048
    assert body["max_tokens"] == MOVIE_IDENTIFICATION_MAX_TOKENS == 4096
    assert body["thinking_token_budget"] == (
        MOVIE_IDENTIFICATION_REASONING_BUDGET
        + MOVIE_IDENTIFICATION_REASONING_GRACE_TOKENS
    )
    assert body["chat_template_kwargs"] == {
        "enable_thinking": True,
        "reasoning_budget": 2048,
    }
    assert body["stream"] is False
    assert body["max_tokens"] > body["thinking_token_budget"]
    assert not ({"response_format", "guided_json", "tools"} & set(body))

    content = body["messages"][0]["content"]
    text_parts = [part for part in content if part.get("type") == "text"]
    image_parts = [part for part in content if part.get("type") == "image_url"]
    assert len(text_parts) == 1
    assert len(image_parts) == 1
    assert image_parts[0]["image_url"]["url"].startswith("data:image/jpeg;base64,")
    serialized = json.dumps(body)
    assert "data:video/" not in serialized
    assert "data:audio/" not in serialized
    assert request.basename not in serialized
    assert "/home/" not in serialized
    assert "/srv/" not in serialized


@pytest.mark.parametrize(
    ("content", "reasoning"),
    [
        (json.dumps(VALID_UNKNOWN), None),
        (json.dumps(VALID_UNKNOWN), _REASONING_SENTINEL),
        (
            f"<think>{_REASONING_SENTINEL}</think>{json.dumps(VALID_UNKNOWN)}",
            None,
        ),
        (f"```json\n{json.dumps(VALID_UNKNOWN)}\n```", None),
    ],
)
def test_movie_response_accepts_only_supported_final_answer_shapes(
    content: str,
    reasoning: str | None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    suggestion, transport, logger = _identify(
        _response_payload(content, reasoning_field=reasoning),
        monkeypatch,
    )

    assert suggestion.identification_status.value == "unknown"
    assert len(transport.post_calls) == 1
    assert transport.get_calls == []
    assert len(logger.events) == 1
    event = logger.events[0]
    assert event["level"] == "INFO"
    assert event["error_code"] is None
    context = event["context"]
    assert context["compatibility_mode"] == MOVIE_STRUCTURED_OUTPUT_COMPATIBILITY_MODE
    assert context["reasoning_enabled"] is True
    assert context["reasoning_budget"] == 2048
    assert context["initial_http_status_class"] == "2xx"
    assert context["http_status_class"] == "2xx"
    assert context["response_content_type"] == "application/json"
    assert context["response_lifecycle"] == "synchronous_200"
    assert context["parser_stage"] == "completed"
    assert context["json_decode_stage"] == "succeeded"
    assert context["decoded_top_level_type"] == "object"
    assert context["schema_validation_stage"] == "succeeded"
    assert context["terminal_domain_error"] is None

    diagnostic_text = json.dumps(logger.events, sort_keys=True)
    assert _REASONING_SENTINEL not in diagnostic_text
    assert "Unknown film." not in diagnostic_text
    assert "Insufficient evidence." not in diagnostic_text
    assert _SECRET not in diagnostic_text


@pytest.mark.parametrize(
    ("payload", "expected_error", "error_code"),
    [
        (
            _response_payload(
                [{"type": "text", "text": json.dumps(VALID_UNKNOWN)}]
            ),
            MediaSuggestionProviderInvalidResponseError,
            "PROVIDER_INVALID_RESPONSE",
        ),
        (
            _response_payload(f"{_CONTENT_SENTINEL} {json.dumps(VALID_UNKNOWN)}"),
            MediaSuggestionProviderInvalidResponseError,
            "PROVIDER_INVALID_RESPONSE",
        ),
        (
            _response_payload(f"{json.dumps(VALID_UNKNOWN)} {_CONTENT_SENTINEL}"),
            MediaSuggestionProviderInvalidResponseError,
            "PROVIDER_INVALID_RESPONSE",
        ),
        (
            _response_payload(
                f"{json.dumps(VALID_UNKNOWN)}{json.dumps(VALID_UNKNOWN)}"
            ),
            MediaSuggestionProviderInvalidResponseError,
            "PROVIDER_INVALID_RESPONSE",
        ),
        (
            _response_payload(""),
            MediaSuggestionProviderInvalidResponseError,
            "PROVIDER_INVALID_RESPONSE",
        ),
        (
            {"choices": [{"finish_reason": "stop", "message": {}}]},
            MediaSuggestionProviderInvalidResponseError,
            "PROVIDER_INVALID_RESPONSE",
        ),
        (
            _response_payload(None),
            MediaSuggestionProviderInvalidResponseError,
            "PROVIDER_INVALID_RESPONSE",
        ),
        (
            _response_payload(42),
            MediaSuggestionProviderInvalidResponseError,
            "PROVIDER_INVALID_RESPONSE",
        ),
        (
            _response_payload(
                '{"identified_title":null',
                finish_reason="length",
            ),
            MediaSuggestionProviderTruncatedResponseError,
            "PROVIDER_RESPONSE_TRUNCATED",
        ),
        (
            _response_payload("{not-json}"),
            MediaSuggestionProviderInvalidResponseError,
            "PROVIDER_INVALID_RESPONSE",
        ),
        (
            _response_payload(json.dumps(["not", "an", "object"])),
            MediaSuggestionProviderInvalidResponseError,
            "PROVIDER_INVALID_RESPONSE",
        ),
        (
            _response_payload(
                json.dumps(
                    {
                        key: value
                        for key, value in VALID_UNKNOWN.items()
                        if key != "evidence_summary"
                    }
                )
            ),
            MediaSuggestionProviderInvalidResponseError,
            "PROVIDER_INVALID_RESPONSE",
        ),
        (
            _response_payload(
                json.dumps({**VALID_UNKNOWN, "candidate_titles": [123]})
            ),
            MediaSuggestionProviderInvalidResponseError,
            "PROVIDER_INVALID_RESPONSE",
        ),
        (
            {"unexpected": "envelope"},
            MediaSuggestionProviderInvalidResponseError,
            "PROVIDER_INVALID_RESPONSE",
        ),
    ],
)
def test_movie_response_rejects_ambiguous_or_invalid_shapes_without_leakage(
    payload: object,
    expected_error: type[Exception],
    error_code: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    transport = _FakeTransport(body=_json_body(payload))
    logger = _RecordingLogger()
    monkeypatch.setattr(nvidia_nim, "LOGGER", logger)
    provider = NvidiaNimMediaSuggestionProvider(
        NvidiaApiCredential(_SECRET),
        transport,
    )

    with pytest.raises(expected_error) as exc_info:
        provider.identify_movie(_movie_request())

    if expected_error is MediaSuggestionProviderInvalidResponseError:
        assert type(exc_info.value) is MediaSuggestionProviderInvalidResponseError
    assert len(transport.post_calls) == 1
    assert transport.get_calls == []
    assert len(logger.events) == 1
    event = logger.events[0]
    assert event["level"] == "WARNING"
    assert event["error_code"] == error_code
    assert event["context"]["terminal_domain_error"] == error_code
    diagnostic_text = json.dumps(logger.events, sort_keys=True)
    assert _REASONING_SENTINEL not in diagnostic_text
    assert _CONTENT_SENTINEL not in diagnostic_text
    assert "Unknown film." not in diagnostic_text
    assert _SECRET not in diagnostic_text


def test_movie_response_classification_records_only_bounded_structure() -> None:
    payload = _response_payload(
        json.dumps(VALID_UNKNOWN),
        reasoning_field=_REASONING_SENTINEL,
    )
    facts = classify_chat_completion_choice(payload)

    assert facts["choice_count"] == 1
    assert facts["selected_choice_index"] == 0
    assert facts["finish_reason"] == "stop"
    assert facts["content_repr"] == "string"
    assert facts["final_content_length_bucket"] in {"1-256", "257-1024"}
    assert facts["final_content_empty"] is False
    assert facts["has_reasoning_field"] is True
    assert facts["reasoning_repr"] == "string"
    assert facts["detected_wrapper_category"] == "raw_json_object"
    serialized = json.dumps(facts, sort_keys=True)
    assert _REASONING_SENTINEL not in serialized
    assert "Unknown film." not in serialized


def test_movie_response_rejects_non_object_provider_envelope(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    transport = _FakeTransport(body=_json_body(["choices"]))
    logger = _RecordingLogger()
    monkeypatch.setattr(nvidia_nim, "LOGGER", logger)
    provider = NvidiaNimMediaSuggestionProvider(
        NvidiaApiCredential(_SECRET),
        transport,
    )

    with pytest.raises(MediaSuggestionProviderInvalidResponseError):
        provider.identify_movie(_movie_request())

    assert len(transport.post_calls) == 1
    assert logger.events[0]["context"]["parser_stage"] == "provider_envelope_json"
    assert logger.events[0]["context"]["json_decode_stage"] == "provider_envelope_failed"


def test_movie_response_http_202_poll_path_succeeds(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pending = _json_body({"requestId": "req_movie_1"})
    final = _json_body(_response_payload(json.dumps(VALID_UNKNOWN)))

    class _PollingTransport(_FakeTransport):
        def __init__(self) -> None:
            super().__init__(body=pending, status_code=202)
            self.get_responses = [
                HttpsJsonResponse(
                    status_code=202,
                    body=pending,
                    content_type="application/json",
                ),
                HttpsJsonResponse(
                    status_code=200,
                    body=final,
                    content_type="application/json",
                ),
            ]

        def get_json(
            self,
            url: str,
            *,
            headers: dict[str, str],
        ) -> HttpsJsonResponse:
            self.get_calls.append((url, dict(headers)))
            return self.get_responses.pop(0)

    transport = _PollingTransport()
    logger = _RecordingLogger()
    monkeypatch.setattr(nvidia_nim, "LOGGER", logger)
    provider = NvidiaNimMediaSuggestionProvider(
        NvidiaApiCredential(_SECRET),
        transport,
        pending_poll_interval_seconds=0.0,
        pending_timeout_seconds=5.0,
    )

    suggestion = provider.identify_movie(_movie_request())

    assert suggestion.identification_status.value == "unknown"
    assert len(transport.post_calls) == 1
    assert len(transport.get_calls) == 2
    context = logger.events[0]["context"]
    assert context["response_lifecycle"] == "http_202_poll"
    assert context["initial_http_status_class"] == "2xx"
    assert context["http_status_class"] == "2xx"
