"""FastAPI routes for explicit AI media suggestion preview."""

from __future__ import annotations

from dataclasses import dataclass

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel, UUID4

from framenest.application.media_analysis import (
    FrameNestMediaAnalysisError,
    MediaRelativePath,
    candidate_kind_for_relative_path,
)
from framenest.application.media_suggestion import (
    FrameNestMediaSuggestionError,
    ImportedMediaSuggestionPreviewResult,
    MediaSuggestion,
    MediaSuggestionNotFoundError,
    MediaSuggestionPreparationFailedError,
    MediaSuggestionPreparationUnavailableError,
    MediaSuggestionProviderAuthError,
    MediaSuggestionProviderFailedError,
    MediaSuggestionProviderInvalidResponseError,
    MediaSuggestionProviderRateLimitedError,
    MediaSuggestionProviderUnavailableError,
    MediaSuggestionPreviewResult,
    PROMPT_VERSION,
)
from framenest.application.ports.library_repository import FrameNestLibraryRepositoryError
from framenest.domain import LibraryId, MediaId, MediaLocationId
from framenest.infrastructure.ai.constants import DEFAULT_MODEL_ID, DEFAULT_PROVIDER_ID

NO_STORE_HEADERS = {"Cache-Control": "no-store"}
MAX_RELATIVE_PATH_LENGTH = 4096

CLOUD_CONFIRMATION_REQUIRED_CODE = "CLOUD_CONFIRMATION_REQUIRED"
CLOUD_CONFIRMATION_REQUIRED_MESSAGE = "Explicit cloud upload confirmation is required."
AI_PROVIDER_NOT_CONFIGURED_CODE = "AI_PROVIDER_NOT_CONFIGURED"
AI_PROVIDER_NOT_CONFIGURED_MESSAGE = "The AI suggestion provider is not configured."
LIBRARY_NOT_FOUND_CODE = "LIBRARY_NOT_FOUND"
LIBRARY_NOT_FOUND_MESSAGE = "Library not found."
INVALID_MEDIA_PATH_CODE = "INVALID_MEDIA_PATH"
INVALID_MEDIA_PATH_MESSAGE = "Invalid media relative path."
MEDIA_PREPARATION_UNAVAILABLE_CODE = "MEDIA_PREPARATION_UNAVAILABLE"
MEDIA_PREPARATION_UNAVAILABLE_MESSAGE = "Local media preparation is not available."
MEDIA_PREPARATION_FAILED_CODE = "MEDIA_PREPARATION_FAILED"
MEDIA_PREPARATION_FAILED_MESSAGE = "Local media preparation failed."
AI_PROVIDER_AUTHENTICATION_FAILED_CODE = "AI_PROVIDER_AUTHENTICATION_FAILED"
AI_PROVIDER_AUTHENTICATION_FAILED_MESSAGE = "The configured AI provider credential was rejected."
AI_PROVIDER_RATE_LIMITED_CODE = "AI_PROVIDER_RATE_LIMITED"
AI_PROVIDER_RATE_LIMITED_MESSAGE = "The AI suggestion provider rate limit was reached."
AI_PROVIDER_UNAVAILABLE_CODE = "AI_PROVIDER_UNAVAILABLE"
AI_PROVIDER_UNAVAILABLE_MESSAGE = "The AI suggestion provider is not available."
AI_PROVIDER_INVALID_RESPONSE_CODE = "AI_PROVIDER_INVALID_RESPONSE"
AI_PROVIDER_INVALID_RESPONSE_MESSAGE = "The AI suggestion provider response was invalid."
AI_PROVIDER_FAILED_CODE = "AI_PROVIDER_FAILED"
AI_PROVIDER_FAILED_MESSAGE = "The AI suggestion provider request failed."


class ErrorBody(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    error: ErrorBody


class MediaSuggestionCapabilityResponse(BaseModel):
    available: bool
    provider_id: str
    model_id: str
    prompt_version: str
    execution: str
    requires_explicit_confirmation: bool


class MediaSuggestionPreviewRequest(BaseModel):
    relative_path: object
    confirm_cloud_upload: object


class ImportedMediaSuggestionPreviewRequest(BaseModel):
    confirm_cloud_upload: object


class SuggestionBodyResponse(BaseModel):
    title: str
    description: str
    collection: str
    tags: list[str]
    suggested_filename: str
    confidence: float
    evidence: list[str]
    uncertainties: list[str]


class MediaSuggestionPreviewResponse(BaseModel):
    library_id: str
    relative_path: str
    sent_frame_count: int
    provider_id: str
    model_id: str
    prompt_version: str
    suggestion: SuggestionBodyResponse


class ImportedMediaSuggestionPreviewResponse(BaseModel):
    media_id: str
    location_id: str
    sent_frame_count: int
    provider_id: str
    model_id: str
    prompt_version: str
    suggestion: SuggestionBodyResponse


@dataclass(frozen=True, slots=True)
class MediaSuggestionApiDependencies:
    """Injected dependencies for explicit AI media suggestion API routes."""

    preview_suggestion: object | None
    provider_configured: bool
    preview_imported_suggestion: object | None = None
    provider_id: str = DEFAULT_PROVIDER_ID
    model_id: str = DEFAULT_MODEL_ID
    prompt_version: str = PROMPT_VERSION


def create_media_suggestion_api_router(dependencies: MediaSuggestionApiDependencies) -> APIRouter:
    """Create the explicit AI media suggestion preview router."""
    router = APIRouter()

    @router.get(
        "/api/ai/media-suggestion-capability",
        response_model=MediaSuggestionCapabilityResponse,
    )
    def media_suggestion_capability() -> JSONResponse:
        return _json_response(
            MediaSuggestionCapabilityResponse(
                available=dependencies.provider_configured,
                provider_id=dependencies.provider_id,
                model_id=dependencies.model_id,
                prompt_version=dependencies.prompt_version,
                execution="cloud",
                requires_explicit_confirmation=True,
            )
        )

    @router.post(
        "/api/libraries/{library_id}/media-suggestion-preview",
        response_model=MediaSuggestionPreviewResponse,
        responses={
            404: {"model": ErrorResponse},
            409: {"model": ErrorResponse},
            422: {"model": ErrorResponse},
            429: {"model": ErrorResponse},
            500: {"model": ErrorResponse},
            502: {"model": ErrorResponse},
            503: {"model": ErrorResponse},
        },
    )
    def preview_media_suggestion(
        library_id: UUID4,
        request: MediaSuggestionPreviewRequest,
    ) -> MediaSuggestionPreviewResponse | JSONResponse:
        if request.confirm_cloud_upload is not True:
            return _error_response(
                409,
                CLOUD_CONFIRMATION_REQUIRED_CODE,
                CLOUD_CONFIRMATION_REQUIRED_MESSAGE,
            )
        if dependencies.preview_suggestion is None or not dependencies.provider_configured:
            return _error_response(
                503,
                AI_PROVIDER_NOT_CONFIGURED_CODE,
                AI_PROVIDER_NOT_CONFIGURED_MESSAGE,
            )
        try:
            relative_path = _media_relative_path_from_request(request.relative_path)
            result = dependencies.preview_suggestion.execute(
                LibraryId.from_string(str(library_id)),
                relative_path,
            )
        except FrameNestLibraryRepositoryError:
            return _error_response(503, AI_PROVIDER_UNAVAILABLE_CODE, AI_PROVIDER_UNAVAILABLE_MESSAGE)
        except MediaSuggestionNotFoundError:
            return _error_response(404, LIBRARY_NOT_FOUND_CODE, LIBRARY_NOT_FOUND_MESSAGE)
        except (FrameNestMediaAnalysisError, FrameNestMediaSuggestionError):
            return _error_response(422, INVALID_MEDIA_PATH_CODE, INVALID_MEDIA_PATH_MESSAGE)
        except MediaSuggestionPreparationUnavailableError:
            return _error_response(
                409,
                MEDIA_PREPARATION_UNAVAILABLE_CODE,
                MEDIA_PREPARATION_UNAVAILABLE_MESSAGE,
            )
        except MediaSuggestionPreparationFailedError:
            return _error_response(
                500,
                MEDIA_PREPARATION_FAILED_CODE,
                MEDIA_PREPARATION_FAILED_MESSAGE,
            )
        except MediaSuggestionProviderAuthError:
            return _error_response(
                503,
                AI_PROVIDER_AUTHENTICATION_FAILED_CODE,
                AI_PROVIDER_AUTHENTICATION_FAILED_MESSAGE,
            )
        except MediaSuggestionProviderRateLimitedError:
            return _error_response(429, AI_PROVIDER_RATE_LIMITED_CODE, AI_PROVIDER_RATE_LIMITED_MESSAGE)
        except MediaSuggestionProviderUnavailableError:
            return _error_response(503, AI_PROVIDER_UNAVAILABLE_CODE, AI_PROVIDER_UNAVAILABLE_MESSAGE)
        except MediaSuggestionProviderInvalidResponseError:
            return _error_response(
                502,
                AI_PROVIDER_INVALID_RESPONSE_CODE,
                AI_PROVIDER_INVALID_RESPONSE_MESSAGE,
            )
        except MediaSuggestionProviderFailedError:
            return _error_response(502, AI_PROVIDER_FAILED_CODE, AI_PROVIDER_FAILED_MESSAGE)
        except Exception:
            return _error_response(502, AI_PROVIDER_FAILED_CODE, AI_PROVIDER_FAILED_MESSAGE)
        return _json_response(_preview_response(result))

    @router.post(
        "/api/media/{media_id}/locations/{location_id}/ai-suggestion-preview",
        response_model=ImportedMediaSuggestionPreviewResponse,
        responses={
            404: {"model": ErrorResponse},
            409: {"model": ErrorResponse},
            422: {"model": ErrorResponse},
            429: {"model": ErrorResponse},
            500: {"model": ErrorResponse},
            502: {"model": ErrorResponse},
            503: {"model": ErrorResponse},
        },
    )
    def preview_imported_media_suggestion(
        media_id: UUID4,
        location_id: UUID4,
        request: ImportedMediaSuggestionPreviewRequest,
    ) -> ImportedMediaSuggestionPreviewResponse | JSONResponse:
        if request.confirm_cloud_upload is not True:
            return _error_response(
                409,
                CLOUD_CONFIRMATION_REQUIRED_CODE,
                CLOUD_CONFIRMATION_REQUIRED_MESSAGE,
            )
        if dependencies.preview_imported_suggestion is None or not dependencies.provider_configured:
            return _error_response(
                503,
                AI_PROVIDER_NOT_CONFIGURED_CODE,
                AI_PROVIDER_NOT_CONFIGURED_MESSAGE,
            )
        try:
            result = dependencies.preview_imported_suggestion.execute(
                MediaId.from_string(str(media_id)),
                MediaLocationId.from_string(str(location_id)),
            )
        except MediaSuggestionNotFoundError:
            return _error_response(404, LIBRARY_NOT_FOUND_CODE, LIBRARY_NOT_FOUND_MESSAGE)
        except (FrameNestMediaAnalysisError, FrameNestMediaSuggestionError):
            return _error_response(422, INVALID_MEDIA_PATH_CODE, INVALID_MEDIA_PATH_MESSAGE)
        except MediaSuggestionPreparationUnavailableError:
            return _error_response(
                409,
                MEDIA_PREPARATION_UNAVAILABLE_CODE,
                MEDIA_PREPARATION_UNAVAILABLE_MESSAGE,
            )
        except MediaSuggestionPreparationFailedError:
            return _error_response(
                500,
                MEDIA_PREPARATION_FAILED_CODE,
                MEDIA_PREPARATION_FAILED_MESSAGE,
            )
        except MediaSuggestionProviderAuthError:
            return _error_response(
                503,
                AI_PROVIDER_AUTHENTICATION_FAILED_CODE,
                AI_PROVIDER_AUTHENTICATION_FAILED_MESSAGE,
            )
        except MediaSuggestionProviderRateLimitedError:
            return _error_response(429, AI_PROVIDER_RATE_LIMITED_CODE, AI_PROVIDER_RATE_LIMITED_MESSAGE)
        except MediaSuggestionProviderUnavailableError:
            return _error_response(503, AI_PROVIDER_UNAVAILABLE_CODE, AI_PROVIDER_UNAVAILABLE_MESSAGE)
        except MediaSuggestionProviderInvalidResponseError:
            return _error_response(
                502,
                AI_PROVIDER_INVALID_RESPONSE_CODE,
                AI_PROVIDER_INVALID_RESPONSE_MESSAGE,
            )
        except MediaSuggestionProviderFailedError:
            return _error_response(502, AI_PROVIDER_FAILED_CODE, AI_PROVIDER_FAILED_MESSAGE)
        except Exception:
            return _error_response(502, AI_PROVIDER_FAILED_CODE, AI_PROVIDER_FAILED_MESSAGE)
        return _json_response(_imported_preview_response(result))

    return router


def _media_relative_path_from_request(value: object) -> MediaRelativePath:
    if not isinstance(value, str) or len(value) > MAX_RELATIVE_PATH_LENGTH:
        raise FrameNestMediaAnalysisError(INVALID_MEDIA_PATH_MESSAGE)
    relative_path = MediaRelativePath(value)
    candidate_kind_for_relative_path(relative_path)
    return relative_path


def _error_response(status_code: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"error": {"code": code, "message": message}},
        headers=NO_STORE_HEADERS,
    )


def _json_response(response: BaseModel) -> JSONResponse:
    return JSONResponse(
        status_code=200,
        content=response.model_dump(),
        headers=NO_STORE_HEADERS,
    )


def _suggestion_response(suggestion: MediaSuggestion) -> SuggestionBodyResponse:
    return SuggestionBodyResponse(
        title=suggestion.title,
        description=suggestion.description,
        collection=suggestion.collection,
        tags=list(suggestion.tags),
        suggested_filename=suggestion.suggested_filename,
        confidence=suggestion.confidence,
        evidence=list(suggestion.evidence),
        uncertainties=list(suggestion.uncertainties),
    )


def _preview_response(result: MediaSuggestionPreviewResult) -> MediaSuggestionPreviewResponse:
    return MediaSuggestionPreviewResponse(
        library_id=result.library_id.to_string(),
        relative_path=result.relative_path.value,
        sent_frame_count=result.sent_frame_count,
        provider_id=result.suggestion.provider_id,
        model_id=result.suggestion.model_id,
        prompt_version=result.suggestion.prompt_version,
        suggestion=_suggestion_response(result.suggestion),
    )


def _imported_preview_response(
    result: ImportedMediaSuggestionPreviewResult,
) -> ImportedMediaSuggestionPreviewResponse:
    return ImportedMediaSuggestionPreviewResponse(
        media_id=result.media_id.to_string(),
        location_id=result.location_id.to_string(),
        sent_frame_count=result.sent_frame_count,
        provider_id=result.suggestion.provider_id,
        model_id=result.suggestion.model_id,
        prompt_version=result.suggestion.prompt_version,
        suggestion=_suggestion_response(result.suggestion),
    )
