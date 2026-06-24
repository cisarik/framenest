"""NVIDIA NIM media suggestion adapter."""

from __future__ import annotations

import base64
import json
import re
from typing import Any, Protocol

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
        "messages": [{"role": "user", "content": content}],
        "stream": False,
        "temperature": TEMPERATURE,
        "max_tokens": MAX_TOKENS,
        "chat_template_kwargs": {"enable_thinking": False},
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
    ) -> None:
        self._credential = credential
        self._transport = transport or HttpsJsonTransport(
            timeout_seconds=REQUEST_TIMEOUT_SECONDS,
            max_response_bytes=MAX_RESPONSE_BODY_BYTES,
        )
        self._model_id = model_id
        self._provider_id = provider_id

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
            response_body = getattr(response, "body", response)
            if not isinstance(response_body, (bytes, bytearray)):
                raise MediaSuggestionProviderInvalidResponseError(
                    SUGGESTION_PROVIDER_INVALID_RESPONSE_MESSAGE
                )
            payload = json.loads(response_body.decode("utf-8"))
        except HttpsTransportError as exc:
            raise _map_transport_error(exc) from None
        except MediaSuggestionProviderInvalidResponseError:
            raise
        except Exception:
            raise MediaSuggestionProviderFailedError(SUGGESTION_PROVIDER_FAILED_MESSAGE) from None
        if not isinstance(payload, dict):
            raise MediaSuggestionProviderInvalidResponseError(
                SUGGESTION_PROVIDER_INVALID_RESPONSE_MESSAGE
            )
        content_text = extract_message_content(payload)
        parsed = parse_suggestion_content_text(content_text)
        return build_media_suggestion(
            parsed,
            required_extension=required_extension,
            provider_id=self._provider_id,
            model_id=self._model_id,
        )

    def __repr__(self) -> str:
        return "NvidiaNimMediaSuggestionProvider(<redacted>)"
