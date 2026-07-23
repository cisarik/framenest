"""Loopback-only operator API for durable YouTube manual acquisition."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from ipaddress import ip_address
import json
from typing import Literal

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, ValidationError

from framenest.application.youtube_acquisition import (
    YouTubeAcquisitionInfrastructureError,
    YouTubeAcquisitionInvalidRequestError,
    YouTubeAcquisitionNotFoundError,
    YouTubeAcquisitionStateConflictError,
)
from framenest.domain.identities import (
    FrameNestIdentityError,
    YouTubeAcquisitionClaimId,
)
from framenest.domain.youtube_acquisition import YouTubeConfirmationMethod

YOUTUBE_OPERATOR_NOT_CONFIGURED = "YOUTUBE_OPERATOR_NOT_CONFIGURED"
YOUTUBE_OPERATOR_LOOPBACK_REQUIRED = "YOUTUBE_OPERATOR_LOOPBACK_REQUIRED"
YOUTUBE_OPERATOR_ORIGIN_FORBIDDEN = "YOUTUBE_OPERATOR_ORIGIN_FORBIDDEN"
YOUTUBE_OPERATOR_INVALID_MEDIA_TYPE = "YOUTUBE_OPERATOR_INVALID_MEDIA_TYPE"
YOUTUBE_OPERATOR_INVALID_REQUEST = "YOUTUBE_OPERATOR_INVALID_REQUEST"
YOUTUBE_OPERATOR_INVALID_URL = "YOUTUBE_OPERATOR_INVALID_URL"
YOUTUBE_OPERATOR_CLAIM_NOT_FOUND = "YOUTUBE_OPERATOR_CLAIM_NOT_FOUND"
YOUTUBE_OPERATOR_STATE_CONFLICT = "YOUTUBE_OPERATOR_STATE_CONFLICT"
YOUTUBE_OPERATOR_UNAVAILABLE = "YOUTUBE_OPERATOR_UNAVAILABLE"

_JSON_MEDIA_TYPE = b"application/json"
_MAX_REQUEST_BODY_BYTES = 4_096


class YouTubeClaimCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    url: str
    confirmation_method: Literal["interactive", "yes_flag"]


class YouTubeClaimRetryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    confirmation_method: Literal["interactive", "yes_flag"]


@dataclass(frozen=True, slots=True)
class YouTubeOperatorApiDependencies:
    """Injected loopback operator API behavior."""

    service: object | None
    enabled: bool


def create_youtube_operator_api_router(
    dependencies: YouTubeOperatorApiDependencies,
) -> APIRouter:
    """Create the intentionally non-browser operator routes."""
    router = APIRouter()

    @router.post("/api/operator/youtube/claims")
    async def create_claim(request: Request) -> JSONResponse:
        guard = _guard(request, dependencies)
        if guard is not None:
            return guard
        payload = await _read_json_model(request, YouTubeClaimCreateRequest)
        if isinstance(payload, JSONResponse):
            return payload
        try:
            result = dependencies.service.submit(  # type: ignore[union-attr]
                submitted_url=payload.url,
                confirmation_method=YouTubeConfirmationMethod(
                    payload.confirmation_method
                ),
            )
            return JSONResponse(
                status_code=201 if result.created else 200,
                content=asdict(result.snapshot),
            )
        except Exception as exc:
            return _map_service_error(exc)

    @router.get("/api/operator/youtube/claims/{claim_id}")
    async def get_claim(claim_id: str, request: Request) -> JSONResponse:
        guard = _guard(request, dependencies)
        if guard is not None:
            return guard
        parsed = _claim_id(claim_id)
        if isinstance(parsed, JSONResponse):
            return parsed
        try:
            snapshot = dependencies.service.get(parsed)  # type: ignore[union-attr]
            return JSONResponse(status_code=200, content=asdict(snapshot))
        except Exception as exc:
            return _map_service_error(exc)

    @router.post("/api/operator/youtube/claims/{claim_id}/retry")
    async def retry_claim(claim_id: str, request: Request) -> JSONResponse:
        guard = _guard(request, dependencies)
        if guard is not None:
            return guard
        parsed = _claim_id(claim_id)
        if isinstance(parsed, JSONResponse):
            return parsed
        payload = await _read_json_model(request, YouTubeClaimRetryRequest)
        if isinstance(payload, JSONResponse):
            return payload
        try:
            result = dependencies.service.retry(  # type: ignore[union-attr]
                parsed,
                confirmation_method=YouTubeConfirmationMethod(
                    payload.confirmation_method
                ),
            )
            return JSONResponse(
                status_code=201 if result.created else 200,
                content=asdict(result.snapshot),
            )
        except Exception as exc:
            return _map_service_error(exc)

    return router


def _guard(
    request: Request,
    dependencies: YouTubeOperatorApiDependencies,
) -> JSONResponse | None:
    if not dependencies.enabled or dependencies.service is None:
        return _error(
            503,
            YOUTUBE_OPERATOR_NOT_CONFIGURED,
            "YouTube operator ingestion is not configured.",
        )
    if any(
        name.lower() == b"origin"
        for name, _value in request.scope.get("headers", ())
    ):
        return _error(
            403,
            YOUTUBE_OPERATOR_ORIGIN_FORBIDDEN,
            "Browser-origin requests are forbidden.",
        )
    client = request.client
    try:
        is_loopback = client is not None and ip_address(client.host).is_loopback
    except ValueError:
        is_loopback = False
    if not is_loopback:
        return _error(
            403,
            YOUTUBE_OPERATOR_LOOPBACK_REQUIRED,
            "Loopback operator access is required.",
        )
    return None


async def _read_json_model(
    request: Request,
    model_type: type[BaseModel],
) -> BaseModel | JSONResponse:
    media_types = [
        value.strip().lower()
        for name, value in request.scope.get("headers", ())
        if name.lower() == b"content-type"
    ]
    if media_types != [_JSON_MEDIA_TYPE]:
        return _error(
            415,
            YOUTUBE_OPERATOR_INVALID_MEDIA_TYPE,
            "The request media type must be application/json.",
        )
    body = bytearray()
    try:
        async for chunk in request.stream():
            body.extend(chunk)
            if len(body) > _MAX_REQUEST_BODY_BYTES:
                return _error(
                    413,
                    YOUTUBE_OPERATOR_INVALID_REQUEST,
                    "The operator request is invalid.",
                )
        return model_type.model_validate_json(bytes(body))
    except (UnicodeDecodeError, ValidationError, ValueError, json.JSONDecodeError):
        return _error(
            400,
            YOUTUBE_OPERATOR_INVALID_REQUEST,
            "The operator request is invalid.",
        )


def _claim_id(value: str) -> YouTubeAcquisitionClaimId | JSONResponse:
    try:
        return YouTubeAcquisitionClaimId.from_string(value)
    except FrameNestIdentityError:
        return _error(
            404,
            YOUTUBE_OPERATOR_CLAIM_NOT_FOUND,
            "YouTube acquisition claim was not found.",
        )


def _map_service_error(exc: Exception) -> JSONResponse:
    if isinstance(exc, YouTubeAcquisitionInvalidRequestError):
        return _error(
            400,
            YOUTUBE_OPERATOR_INVALID_URL,
            "The public YouTube video URL is invalid.",
        )
    if isinstance(exc, YouTubeAcquisitionNotFoundError):
        return _error(
            404,
            YOUTUBE_OPERATOR_CLAIM_NOT_FOUND,
            "YouTube acquisition claim was not found.",
        )
    if isinstance(exc, YouTubeAcquisitionStateConflictError):
        return _error(
            409,
            YOUTUBE_OPERATOR_STATE_CONFLICT,
            "The YouTube acquisition state conflicts with this operation.",
        )
    if isinstance(exc, YouTubeAcquisitionInfrastructureError):
        return _error(
            503,
            YOUTUBE_OPERATOR_UNAVAILABLE,
            "YouTube acquisition is unavailable.",
        )
    return _error(
        503,
        YOUTUBE_OPERATOR_UNAVAILABLE,
        "YouTube acquisition is unavailable.",
    )


def _error(status_code: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"error": {"code": code, "message": message}},
    )
