"""NVIDIA NIM media suggestion adapter."""

from __future__ import annotations

import base64
import json
import re
import time
from typing import Any, Callable, Protocol

from framenest.application.media_suggestion import (
    FrameNestMediaSuggestionError,
    INVALID_SUGGESTION_MESSAGE,
    MediaSuggestion,
    MediaSuggestionProviderAuthError,
    MediaSuggestionProviderFailedError,
    MediaSuggestionProviderInvalidResponseError,
    MediaSuggestionProviderRateLimitedError,
    MediaSuggestionProviderUnavailableError,
    MediaSuggestionRequest,
    PROMPT_VERSION,
    SUGGESTION_PROVIDER_AUTH_MESSAGE,
    SUGGESTION_PROVIDER_FAILED_MESSAGE,
    SUGGESTION_PROVIDER_INVALID_RESPONSE_MESSAGE,
    SUGGESTION_PROVIDER_RATE_LIMITED_MESSAGE,
    SUGGESTION_PROVIDER_UNAVAILABLE_MESSAGE,
    validate_suggested_filename,
)
from framenest.infrastructure.ai.constants import (
    DEFAULT_MODEL_ID,
    DEFAULT_PROVIDER_ID,
    MAX_REQUEST_BODY_BYTES,
    MAX_RESPONSE_BODY_BYTES,
    NVIDIA_CHAT_COMPLETIONS_URL,
    REQUEST_TIMEOUT_SECONDS,
    TEMPERATURE,
    MAX_TOKENS,
)
from framenest.infrastructure.ai.credentials import NvidiaApiCredential
from framenest.infrastructure.ai.prompts import MEDIA_SUGGESTION_PROMPT
from framenest.infrastructure.ai.transport import (
    HttpsJsonTransport,
    HttpsTransportError,
    TRANSPORT_AUTH_REJECTED_MESSAGE,
    TRANSPORT_INVALID_RESPONSE_MESSAGE,
    TRANSPORT_RATE_LIMITED_MESSAGE,
    TRANSPORT_UNAVAILABLE_MESSAGE,
)

_JSON_FENCE_PATTERN = re.compile(r"^```json\s*\n(?P<body>.*)\n```\s*$", re.DOTALL)
_REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{1,128}$")
_NVIDIA_STATUS_URL_PREFIX = "https://integrate.api.nvidia.com/v1/status/"
_PENDING_POLL_INTERVAL_SECONDS = 1.0
_PENDING_TIMEOUT_SECONDS = 120.0
_ALLOWED_SUGGESTION_KEYS = frozenset(
    {
        "title",
        "description",
        "collection",
        "tags",
        "suggested_filename",
        "confidence",
        "evidence",
        "uncertainties",
    }
)


class JsonTransport(Protocol):
    def post_json(
        self,
        url: str,
        *,
        headers: dict[str, str],
        body: bytes,
        max_request_bytes: int,
    ) -> object:
        """Post one bounded JSON request."""

    def get_json(
        self,
        url: str,
        *,
        headers: dict[str, str],
    ) -> object:
        """Get one bounded JSON response."""


def _extension_from_basename(basename: str) -> str:
    if "." not in basename:
        raise MediaSuggestionProviderInvalidResponseError(
            SUGGESTION_PROVIDER_INVALID_RESPONSE_MESSAGE
        )
    return "." + basename.rsplit(".", 1)[-1].lower()


def _metadata_summary(request: MediaSuggestionRequest) -> str:
    metadata = request.technical_metadata
    duration = "unknown" if metadata.duration_ms is None else str(metadata.duration_ms)
    containers = ", ".join(metadata.container_formats)
    return (
        f"Duration milliseconds: {duration}\n"
        f"Dimensions: {metadata.width}x{metadata.height}\n"
        f"Video codec: {metadata.video_codec}\n"
        f"Container formats: {containers}\n"
        f"Audio present: {metadata.has_audio}"
    )


def build_nvidia_request_body(request: MediaSuggestionRequest, *, model_id: str) -> dict[str, Any]:
    """Build the NVIDIA chat-completions request body for one suggestion request."""
    content: list[dict[str, Any]] = [
        {
            "type": "text",
            "text": "\n\n".join(
                [
                    MEDIA_SUGGESTION_PROMPT,
                    f"Filename basename: {request.basename}",
                    f"Candidate kind: {request.candidate_kind.value}",
                    _metadata_summary(request),
                ]
            ),
        }
    ]
    for frame in request.representative_frames:
        encoded = base64.b64encode(frame.payload).decode("ascii")
        content.append(
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{encoded}"},
            }
        )
    return {
        "model": model_id,
        "messages": [
            {"role": "system", "content": "/no_think"},
            {"role": "user", "content": content},
        ],
        "stream": False,
        "temperature": TEMPERATURE,
        "max_tokens": MAX_TOKENS,
    }


def extract_message_content(payload: dict[str, Any]) -> str:
    """Extract provider message content from one chat-completions envelope."""
    choices = payload.get("choices")
    if not isinstance(choices, list) or not choices:
        raise MediaSuggestionProviderInvalidResponseError(
            SUGGESTION_PROVIDER_INVALID_RESPONSE_MESSAGE
        )
    first = choices[0]
    if not isinstance(first, dict):
        raise MediaSuggestionProviderInvalidResponseError(
            SUGGESTION_PROVIDER_INVALID_RESPONSE_MESSAGE
        )
    message = first.get("message")
    if not isinstance(message, dict):
        raise MediaSuggestionProviderInvalidResponseError(
            SUGGESTION_PROVIDER_INVALID_RESPONSE_MESSAGE
        )
    content = message.get("content")
    if not isinstance(content, str) or not content.strip():
        raise MediaSuggestionProviderInvalidResponseError(
            SUGGESTION_PROVIDER_INVALID_RESPONSE_MESSAGE
        )
    return content.strip()


def parse_suggestion_content_text(text: str) -> dict[str, Any]:
    """Parse one raw or fenced JSON suggestion object."""
    candidate = text.strip()
    fence_match = _JSON_FENCE_PATTERN.fullmatch(candidate)
    if fence_match:
        candidate = fence_match.group("body").strip()
    else:
        if not candidate.startswith("{") or not candidate.endswith("}"):
            raise MediaSuggestionProviderInvalidResponseError(
                SUGGESTION_PROVIDER_INVALID_RESPONSE_MESSAGE
            )
    try:
        parsed = json.loads(candidate)
    except json.JSONDecodeError:
        raise MediaSuggestionProviderInvalidResponseError(
            SUGGESTION_PROVIDER_INVALID_RESPONSE_MESSAGE
        ) from None
    if not isinstance(parsed, dict):
        raise MediaSuggestionProviderInvalidResponseError(
            SUGGESTION_PROVIDER_INVALID_RESPONSE_MESSAGE
        )
    if set(parsed.keys()) != _ALLOWED_SUGGESTION_KEYS:
        raise MediaSuggestionProviderInvalidResponseError(
            SUGGESTION_PROVIDER_INVALID_RESPONSE_MESSAGE
        )
    return parsed


def build_media_suggestion(
    parsed: dict[str, Any],
    *,
    required_extension: str,
    provider_id: str,
    model_id: str,
) -> MediaSuggestion:
    """Validate provider JSON and attach trusted FrameNest metadata."""
    try:
        return MediaSuggestion(
            title=parsed["title"],
            description=parsed["description"],
            collection=parsed["collection"],
            tags=tuple(parsed["tags"]),
            suggested_filename=validate_suggested_filename(
                parsed["suggested_filename"],
                required_extension=required_extension,
            ),
            confidence=parsed["confidence"],
            evidence=tuple(parsed["evidence"]),
            uncertainties=tuple(parsed["uncertainties"]),
            provider_id=provider_id,
            model_id=model_id,
            prompt_version=PROMPT_VERSION,
        )
    except (FrameNestMediaSuggestionError, TypeError, ValueError, KeyError):
        raise MediaSuggestionProviderInvalidResponseError(
            SUGGESTION_PROVIDER_INVALID_RESPONSE_MESSAGE
        ) from None


def _response_status_code(response: object) -> int:
    status_code = getattr(response, "status_code", 200)
    if not isinstance(status_code, int):
        raise MediaSuggestionProviderInvalidResponseError(
            SUGGESTION_PROVIDER_INVALID_RESPONSE_MESSAGE
        )
    return status_code


def _response_body(response: object) -> bytes | bytearray:
    body = getattr(response, "body", response)
    if not isinstance(body, (bytes, bytearray)):
        raise MediaSuggestionProviderInvalidResponseError(
            SUGGESTION_PROVIDER_INVALID_RESPONSE_MESSAGE
        )
    return body


def _decode_json_body(response: object) -> dict[str, Any]:
    body = _response_body(response)
    payload = json.loads(body.decode("utf-8"))
    if not isinstance(payload, dict):
        raise MediaSuggestionProviderInvalidResponseError(
            SUGGESTION_PROVIDER_INVALID_RESPONSE_MESSAGE
        )
    return payload


def _extract_request_id(response: object) -> str:
    try:
        payload = _decode_json_body(response)
    except json.JSONDecodeError:
        raise MediaSuggestionProviderInvalidResponseError(
            SUGGESTION_PROVIDER_INVALID_RESPONSE_MESSAGE
        ) from None
    if set(payload.keys()) != {"requestId"}:
        raise MediaSuggestionProviderInvalidResponseError(
            SUGGESTION_PROVIDER_INVALID_RESPONSE_MESSAGE
        )
    request_id = payload["requestId"]
    if not isinstance(request_id, str) or not _REQUEST_ID_PATTERN.fullmatch(request_id):
        raise MediaSuggestionProviderInvalidResponseError(
            SUGGESTION_PROVIDER_INVALID_RESPONSE_MESSAGE
        )
    return request_id


def _status_error(status_code: int) -> Exception:
    if status_code in {401, 403}:
        return MediaSuggestionProviderAuthError(SUGGESTION_PROVIDER_AUTH_MESSAGE)
    if status_code == 429:
        return MediaSuggestionProviderRateLimitedError(SUGGESTION_PROVIDER_RATE_LIMITED_MESSAGE)
    if status_code >= 500:
        return MediaSuggestionProviderUnavailableError(SUGGESTION_PROVIDER_UNAVAILABLE_MESSAGE)
    return MediaSuggestionProviderInvalidResponseError(SUGGESTION_PROVIDER_INVALID_RESPONSE_MESSAGE)


def _map_transport_error(exc: HttpsTransportError) -> Exception:
    message = str(exc)
    if message == TRANSPORT_AUTH_REJECTED_MESSAGE:
        return MediaSuggestionProviderAuthError(SUGGESTION_PROVIDER_AUTH_MESSAGE)
    if message == TRANSPORT_RATE_LIMITED_MESSAGE:
        return MediaSuggestionProviderRateLimitedError(SUGGESTION_PROVIDER_RATE_LIMITED_MESSAGE)
    if message in {
        TRANSPORT_UNAVAILABLE_MESSAGE,
        TRANSPORT_INVALID_RESPONSE_MESSAGE,
    }:
        return MediaSuggestionProviderUnavailableError(SUGGESTION_PROVIDER_UNAVAILABLE_MESSAGE)
    return MediaSuggestionProviderFailedError(SUGGESTION_PROVIDER_FAILED_MESSAGE)


class NvidiaNimMediaSuggestionProvider:
    """NVIDIA NIM adapter for one media suggestion request."""

    def __init__(
        self,
        credential: NvidiaApiCredential,
        transport: JsonTransport | None = None,
        *,
        model_id: str = DEFAULT_MODEL_ID,
        provider_id: str = DEFAULT_PROVIDER_ID,
        pending_poll_interval_seconds: float = _PENDING_POLL_INTERVAL_SECONDS,
        pending_timeout_seconds: float = _PENDING_TIMEOUT_SECONDS,
        monotonic_clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self._credential = credential
        self._transport = transport or HttpsJsonTransport(
            timeout_seconds=REQUEST_TIMEOUT_SECONDS,
            max_response_bytes=MAX_RESPONSE_BODY_BYTES,
        )
        self._model_id = model_id
        self._provider_id = provider_id
        self._pending_poll_interval_seconds = pending_poll_interval_seconds
        self._pending_timeout_seconds = pending_timeout_seconds
        self._monotonic_clock = monotonic_clock
        self._sleep = sleep

    def suggest(self, request: MediaSuggestionRequest) -> MediaSuggestion:
        required_extension = _extension_from_basename(request.basename)
        body_dict = build_nvidia_request_body(request, model_id=self._model_id)
        body = json.dumps(body_dict, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        headers = {
            "Authorization": self._credential.authorization_header(),
            "Content-Type": "application/json",
        }
        try:
            response = self._transport.post_json(
                NVIDIA_CHAT_COMPLETIONS_URL,
                headers=headers,
                body=body,
                max_request_bytes=MAX_REQUEST_BODY_BYTES,
            )
            response = self._resolve_pending_response(
                response,
                headers={"Authorization": headers["Authorization"]},
            )
            payload = _decode_json_body(response)
        except HttpsTransportError as exc:
            raise _map_transport_error(exc) from None
        except (
            MediaSuggestionProviderAuthError,
            MediaSuggestionProviderInvalidResponseError,
            MediaSuggestionProviderRateLimitedError,
            MediaSuggestionProviderUnavailableError,
        ):
            raise
        except Exception:
            raise MediaSuggestionProviderFailedError(SUGGESTION_PROVIDER_FAILED_MESSAGE) from None
        content_text = extract_message_content(payload)
        parsed = parse_suggestion_content_text(content_text)
        return build_media_suggestion(
            parsed,
            required_extension=required_extension,
            provider_id=self._provider_id,
            model_id=self._model_id,
        )

    def _resolve_pending_response(
        self,
        response: object,
        *,
        headers: dict[str, str],
    ) -> object:
        status_code = _response_status_code(response)
        if status_code == 200:
            return response
        if status_code != 202:
            raise _status_error(status_code)

        request_id = _extract_request_id(response)
        status_url = _NVIDIA_STATUS_URL_PREFIX + request_id
        deadline = self._monotonic_clock() + self._pending_timeout_seconds
        while True:
            if self._monotonic_clock() >= deadline:
                raise MediaSuggestionProviderUnavailableError(
                    SUGGESTION_PROVIDER_UNAVAILABLE_MESSAGE
                )
            self._sleep(self._pending_poll_interval_seconds)
            status_response = self._transport.get_json(status_url, headers=headers)
            status_code = _response_status_code(status_response)
            if status_code == 200:
                return status_response
            if status_code == 202:
                continue
            raise _status_error(status_code)

    def __repr__(self) -> str:
        return "NvidiaNimMediaSuggestionProvider(<redacted>)"
