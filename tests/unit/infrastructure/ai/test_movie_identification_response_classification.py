"""Focused fixtures for movie-identification request and response classification."""

from __future__ import annotations

import io
import json

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
    parse_movie_identification_payload,
)
from framenest.domain.media_classification import (
    MOVIE_IDENTIFICATION_MAX_TOKENS,
    MOVIE_IDENTIFICATION_REASONING_BUDGET,
    MOVIE_IDENTIFICATION_REASONING_GRACE_TOKENS,
)
from framenest.infrastructure.ai.credentials import NvidiaApiCredential
from framenest.infrastructure.ai.nvidia_nim import (
    NvidiaNimMediaSuggestionProvider,
    build_nvidia_movie_identification_body,
    classify_chat_completion_choice,
    extract_message_content,
    parse_json_object_content_text,
)
from framenest.infrastructure.ai.transport import HttpsJsonResponse
from framenest.infrastructure.media_analysis.contact_sheet import compose_contact_sheet


VALID = {
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


def _png(color: tuple[int, int, int]) -> bytes:
    image = Image.new("RGB", (48, 32), color)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def _movie_request() -> MovieIdentificationRequest:
    frames = tuple(
        build_representative_frame(timestamp_ms=i * 100, payload=_png((30 + i * 40, 90, 120)))
        for i in range(3)
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
    def __init__(self, *, body: bytes, status_code: int = 200) -> None:
        self.post_response = HttpsJsonResponse(status_code=status_code, body=body)
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


def test_movie_request_contract_includes_thinking_budget_and_headroom() -> None:
    body = build_nvidia_movie_identification_body(_movie_request(), model_id="fake-model")
    assert body["max_tokens"] == MOVIE_IDENTIFICATION_MAX_TOKENS == 4096
    assert body["thinking_token_budget"] == (
        MOVIE_IDENTIFICATION_REASONING_BUDGET + MOVIE_IDENTIFICATION_REASONING_GRACE_TOKENS
    )
    assert body["chat_template_kwargs"]["enable_thinking"] is True
    assert body["chat_template_kwargs"]["reasoning_budget"] == 2048
    assert body["stream"] is False
    assert body["max_tokens"] > body["thinking_token_budget"]
    content = body["messages"][0]["content"]
    assert sum(1 for part in content if part.get("type") == "text") == 1
    assert sum(1 for part in content if part.get("type") == "image_url") == 1
    assert "/home/" not in str(body)
    assert "/srv/" not in str(body)


@pytest.mark.parametrize(
    ("payload", "expected"),
    [
        (
            {
                "choices": [
                    {
                        "finish_reason": "stop",
                        "message": {
                            "content": json.dumps(VALID),
                            "reasoning_content": "ignore-this-reasoning",
                        },
                    }
                ]
            },
            "ok",
        ),
        (
            {
                "choices": [
                    {
                        "finish_reason": "length",
                        "message": {"content": "", "reasoning": "trace"},
                    }
                ]
            },
            "truncated",
        ),
        (
            {
                "choices": [
                    {
                        "finish_reason": "stop",
                        "message": {"content": None, "reasoning_content": "trace"},
                    }
                ]
            },
            "truncated",
        ),
        (
            {
                "choices": [
                    {
                        "finish_reason": "length",
                        "message": {
                            "content": '{"identified_title": null, "identification_status": "unk',
                        },
                    }
                ]
            },
            "truncated_json",
        ),
        (
            {
                "choices": [
                    {
                        "finish_reason": "stop",
                        "message": {"content": '{"not": "a movie schema"}'},
                    }
                ]
            },
            "invalid_schema",
        ),
        (
            {
                "choices": [
                    {
                        "finish_reason": "stop",
                        "message": {"content": "{not-json"},
                    }
                ]
            },
            "invalid_json",
        ),
        (
            {
                "choices": [
                    {
                        "finish_reason": "stop",
                        "message": {
                            "content": [{"type": "text", "text": json.dumps(VALID)}],
                        },
                    }
                ]
            },
            "invalid",
        ),
        (
            {"choices": []},
            "invalid",
        ),
    ],
)
def test_movie_response_fixture_matrix(payload: dict, expected: str) -> None:
    facts = classify_chat_completion_choice(payload)
    assert "parser_stage" in facts
    assert "final_content_empty" in facts
    assert "has_reasoning_field" in facts
    assert isinstance(facts.get("top_level_keys"), list)

    if expected == "truncated":
        with pytest.raises(MediaSuggestionProviderTruncatedResponseError):
            extract_message_content(payload)
        return
    if expected == "invalid":
        with pytest.raises(MediaSuggestionProviderInvalidResponseError) as exc_info:
            extract_message_content(payload)
        assert type(exc_info.value) is MediaSuggestionProviderInvalidResponseError
        return

    text = extract_message_content(payload)
    if expected == "truncated_json":
        with pytest.raises(MediaSuggestionProviderInvalidResponseError):
            parse_json_object_content_text(text)
        transport = _FakeTransport(
            body=json.dumps(payload, separators=(",", ":")).encode("utf-8")
        )
        provider = NvidiaNimMediaSuggestionProvider(
            NvidiaApiCredential(_SECRET),
            transport,
        )
        with pytest.raises(MediaSuggestionProviderTruncatedResponseError):
            provider.identify_movie(_movie_request())
        assert len(transport.post_calls) == 1
        return
    if expected == "invalid_json":
        with pytest.raises(MediaSuggestionProviderInvalidResponseError) as exc_info:
            parse_json_object_content_text(text)
        assert type(exc_info.value) is MediaSuggestionProviderInvalidResponseError
        return
    if expected == "invalid_schema":
        parsed = parse_json_object_content_text(text)
        with pytest.raises(Exception):
            parse_movie_identification_payload(
                parsed,
                provider_id="fake",
                model_id="fake-model",
                derivative_count=1,
            )
        return

    parsed = parse_json_object_content_text(text)
    suggestion = parse_movie_identification_payload(
        parsed,
        provider_id="fake",
        model_id="fake-model",
        derivative_count=1,
    )
    assert suggestion.identification_status.value == "unknown"
    assert "ignore-this-reasoning" not in json.dumps(VALID)


def test_identify_movie_ignores_reasoning_and_parses_final_content() -> None:
    payload = {
        "id": "chatcmpl-test",
        "choices": [
            {
                "finish_reason": "stop",
                "message": {
                    "content": json.dumps(VALID),
                    "reasoning_content": "do-not-parse-this",
                },
            }
        ],
    }
    transport = _FakeTransport(body=json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    provider = NvidiaNimMediaSuggestionProvider(NvidiaApiCredential(_SECRET), transport)
    suggestion = provider.identify_movie(_movie_request())
    assert suggestion.identification_status.value == "unknown"
    assert len(transport.post_calls) == 1
    request_body = json.loads(transport.post_calls[0][2].decode("utf-8"))
    assert request_body["thinking_token_budget"] == 2304
    assert request_body["max_tokens"] == 4096
    assert request_body["stream"] is False
    assert request_body["chat_template_kwargs"]["enable_thinking"] is True


def test_identify_movie_http_202_poll_path_classifies_truncation() -> None:
    pending = json.dumps({"requestId": "req_movie_1"}, separators=(",", ":")).encode("utf-8")
    final = json.dumps(
        {
            "choices": [
                {
                    "finish_reason": "length",
                    "message": {"content": "", "reasoning": "trace"},
                }
            ]
        },
        separators=(",", ":"),
    ).encode("utf-8")

    class _PollingTransport(_FakeTransport):
        def __init__(self) -> None:
            super().__init__(body=pending, status_code=202)
            self.get_responses = [
                HttpsJsonResponse(status_code=202, body=pending),
                HttpsJsonResponse(status_code=200, body=final),
            ]

        def get_json(self, url: str, *, headers: dict[str, str]) -> HttpsJsonResponse:
            self.get_calls.append((url, dict(headers)))
            return self.get_responses.pop(0)

    transport = _PollingTransport()
    provider = NvidiaNimMediaSuggestionProvider(
        NvidiaApiCredential(_SECRET),
        transport,
        pending_poll_interval_seconds=0.0,
        pending_timeout_seconds=5.0,
    )
    with pytest.raises(MediaSuggestionProviderTruncatedResponseError):
        provider.identify_movie(_movie_request())
    assert len(transport.post_calls) == 1
    assert len(transport.get_calls) == 2
