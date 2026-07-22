"""Sanitized API for durable automatic media analysis lifecycle status."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from framenest.application.media_analysis_lifecycle import (
    AutomaticAnalysisPublicView,
    MediaAnalysisLifecycleError,
    ReadAutomaticMediaAnalysis,
    public_view_from_run,
)
from framenest.domain.identities import FrameNestIdentityError, MediaId, MediaLocationId
from framenest.domain.media_analysis_runs import (
    AUTOMATIC_POST_CATALOG_ANALYSIS_DEFINITION,
    MediaAnalysisRun,
    RESULT_SCHEMA_VERSION,
)


class ErrorBody(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    error: ErrorBody


class AutomaticAnalysisSuggestionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    description: str
    collection: str
    tags: list[str]
    suggested_filename: str
    confidence: float
    evidence: list[str]
    uncertainties: list[str]


class AutomaticAnalysisStatusResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    media_id: str
    state: str
    automatic_analysis_enabled: bool
    analysis_definition: str | None = None
    analysis_profile: str | None = None
    reasoning_enabled: bool | None = None
    derivative_strategy: str | None = None
    derivative_count: int | None = None
    provider_submission_occurred: bool | None = None
    provider_id: str | None = None
    model_id: str | None = None
    prompt_version: str | None = None
    result_schema_version: str | None = None
    result: AutomaticAnalysisSuggestionResponse | None = None
    movie_identification_result: dict[str, object] | None = None
    error_code: str | None = None
    error_message: str | None = None
    attempt_count: int | None = None
    created_at_ms: int | None = None
    started_at_ms: int | None = None
    completed_at_ms: int | None = None


class AutomaticAnalysisCapabilityResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    automatic_analysis_enabled: bool
    analysis_definition: str = Field(
        default=AUTOMATIC_POST_CATALOG_ANALYSIS_DEFINITION
    )
    result_schema_version: str = Field(default=RESULT_SCHEMA_VERSION)
    provider_configured: bool
    provider_id: str | None = None
    model_id: str | None = None


class ManualDurableAnalysisRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    confirm_cloud_upload: bool


class ManualMovieIdentificationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    confirm_cloud_upload: bool


@dataclass(frozen=True, slots=True)
class MediaAnalysisLifecycleApiDependencies:
    """Injected dependencies for automatic analysis status routes."""

    read_analysis: ReadAutomaticMediaAnalysis | None
    automatic_analysis_enabled: bool
    provider_configured: bool
    provider_id: str | None = None
    model_id: str | None = None
    request_manual_analysis: (
        Callable[[MediaId, MediaLocationId], MediaAnalysisRun] | None
    ) = None
    request_movie_identification: (
        Callable[[MediaId, MediaLocationId], MediaAnalysisRun] | None
    ) = None
    read_movie_identification: (
        Callable[[MediaId], AutomaticAnalysisPublicView] | None
    ) = None
    execute_movie_identification: Callable[[MediaAnalysisRun], MediaAnalysisRun] | None = None


def create_media_analysis_lifecycle_api_router(
    dependencies: MediaAnalysisLifecycleApiDependencies,
) -> APIRouter:
    """Create the durable automatic analysis status router."""
    router = APIRouter()

    @router.get(
        "/api/ai/automatic-analysis-capability",
        response_model=AutomaticAnalysisCapabilityResponse,
    )
    def automatic_analysis_capability() -> AutomaticAnalysisCapabilityResponse:
        return AutomaticAnalysisCapabilityResponse(
            automatic_analysis_enabled=dependencies.automatic_analysis_enabled,
            provider_configured=dependencies.provider_configured,
            provider_id=dependencies.provider_id,
            model_id=dependencies.model_id,
        )

    @router.get(
        "/api/media/{media_id}/automatic-analysis",
        response_model=AutomaticAnalysisStatusResponse,
    )
    def automatic_analysis_status(media_id: str) -> AutomaticAnalysisStatusResponse | JSONResponse:
        try:
            parsed_media_id = MediaId.from_string(media_id)
        except FrameNestIdentityError:
            return _error("MEDIA_NOT_FOUND", "Media was not found.", 404)
        if dependencies.read_analysis is None:
            view = AutomaticAnalysisPublicView(
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
        else:
            try:
                view = dependencies.read_analysis.execute(parsed_media_id)
            except MediaAnalysisLifecycleError:
                return _error(
                    "ANALYSIS_STATUS_UNAVAILABLE",
                    "Automatic analysis status is unavailable.",
                    503,
                )
        return _status_response(
            media_id=parsed_media_id.to_string(),
            view=view,
            automatic_analysis_enabled=dependencies.automatic_analysis_enabled,
        )

    @router.post(
        "/api/media/{media_id}/locations/{location_id}/durable-analysis",
        response_model=AutomaticAnalysisStatusResponse,
        responses={
            404: {"model": ErrorResponse},
            409: {"model": ErrorResponse},
            503: {"model": ErrorResponse},
        },
    )
    def request_durable_analysis(
        media_id: str,
        location_id: str,
        request: ManualDurableAnalysisRequest,
    ) -> AutomaticAnalysisStatusResponse | JSONResponse:
        if request.confirm_cloud_upload is not True:
            return _error(
                "CLOUD_CONFIRMATION_REQUIRED",
                "Cloud frame upload confirmation is required.",
                409,
            )
        if not dependencies.provider_configured:
            return _error(
                "AI_PROVIDER_NOT_CONFIGURED",
                "AI analysis is not configured.",
                503,
            )
        if dependencies.request_manual_analysis is None:
            return _error(
                "ANALYSIS_REQUEST_UNAVAILABLE",
                "Durable analysis request is unavailable.",
                503,
            )
        try:
            parsed_media_id = MediaId.from_string(media_id)
            parsed_location_id = MediaLocationId.from_string(location_id)
        except FrameNestIdentityError:
            return _error("MEDIA_NOT_FOUND", "Media was not found.", 404)
        try:
            run = dependencies.request_manual_analysis(
                parsed_media_id,
                parsed_location_id,
            )
        except MediaAnalysisLifecycleError:
            return _error(
                "ANALYSIS_REQUEST_UNAVAILABLE",
                "Durable analysis request is unavailable.",
                503,
            )
        return _status_response(
            media_id=parsed_media_id.to_string(),
            view=public_view_from_run(run),
            automatic_analysis_enabled=dependencies.automatic_analysis_enabled,
        )

    @router.get(
        "/api/media/{media_id}/movie-identification",
        response_model=AutomaticAnalysisStatusResponse,
    )
    def movie_identification_status(
        media_id: str,
    ) -> AutomaticAnalysisStatusResponse | JSONResponse:
        try:
            parsed_media_id = MediaId.from_string(media_id)
        except FrameNestIdentityError:
            return _error("MEDIA_NOT_FOUND", "Media was not found.", 404)
        if dependencies.read_movie_identification is None:
            view = public_view_from_run(None)
        else:
            try:
                view = dependencies.read_movie_identification(parsed_media_id)
            except MediaAnalysisLifecycleError:
                return _error(
                    "ANALYSIS_STATUS_UNAVAILABLE",
                    "Movie identification status is unavailable.",
                    503,
                )
        return _status_response(
            media_id=parsed_media_id.to_string(),
            view=view,
            automatic_analysis_enabled=dependencies.automatic_analysis_enabled,
        )

    @router.post(
        "/api/media/{media_id}/locations/{location_id}/movie-identification",
        response_model=AutomaticAnalysisStatusResponse,
        responses={
            404: {"model": ErrorResponse},
            409: {"model": ErrorResponse},
            503: {"model": ErrorResponse},
        },
    )
    def request_movie_identification(
        media_id: str,
        location_id: str,
        request: ManualMovieIdentificationRequest,
    ) -> AutomaticAnalysisStatusResponse | JSONResponse:
        if request.confirm_cloud_upload is not True:
            return _error(
                "CLOUD_CONFIRMATION_REQUIRED",
                "Cloud frame upload confirmation is required.",
                409,
            )
        if not dependencies.provider_configured:
            return _error(
                "AI_PROVIDER_NOT_CONFIGURED",
                "AI analysis is not configured.",
                503,
            )
        if (
            dependencies.request_movie_identification is None
            or dependencies.execute_movie_identification is None
        ):
            return _error(
                "ANALYSIS_REQUEST_UNAVAILABLE",
                "Movie identification request is unavailable.",
                503,
            )
        try:
            parsed_media_id = MediaId.from_string(media_id)
            parsed_location_id = MediaLocationId.from_string(location_id)
        except FrameNestIdentityError:
            return _error("MEDIA_NOT_FOUND", "Media was not found.", 404)
        try:
            run = dependencies.request_movie_identification(
                parsed_media_id,
                parsed_location_id,
            )
            if run.state.value == "pending":
                run = dependencies.execute_movie_identification(run)
        except MediaAnalysisLifecycleError:
            return _error(
                "ANALYSIS_REQUEST_UNAVAILABLE",
                "Movie identification request is unavailable.",
                503,
            )
        return _status_response(
            media_id=parsed_media_id.to_string(),
            view=public_view_from_run(run),
            automatic_analysis_enabled=dependencies.automatic_analysis_enabled,
        )

    return router


def _status_response(
    *,
    media_id: str,
    view: AutomaticAnalysisPublicView,
    automatic_analysis_enabled: bool,
) -> AutomaticAnalysisStatusResponse:
    from framenest.domain.media_classification import (
        MOVIE_IDENTIFICATION_ANALYSIS_DEFINITION,
        MOVIE_IDENTIFICATION_RESULT_SCHEMA_VERSION,
    )

    result = None
    movie_result = None
    result_schema_version = None
    if view.state == "analyzed" and view.result is not None:
        if view.analysis_definition == MOVIE_IDENTIFICATION_ANALYSIS_DEFINITION:
            movie_result = view.result
            result_schema_version = MOVIE_IDENTIFICATION_RESULT_SCHEMA_VERSION
        elif "title" in view.result:
            result = AutomaticAnalysisSuggestionResponse(
                title=str(view.result["title"]),
                description=str(view.result["description"]),
                collection=str(view.result["collection"]),
                tags=[str(tag) for tag in view.result["tags"]],
                suggested_filename=str(view.result["suggested_filename"]),
                confidence=float(view.result["confidence"]),
                evidence=[str(item) for item in view.result["evidence"]],
                uncertainties=[str(item) for item in view.result["uncertainties"]],
            )
            result_schema_version = RESULT_SCHEMA_VERSION
    return AutomaticAnalysisStatusResponse(
        media_id=media_id,
        state=view.state,
        automatic_analysis_enabled=automatic_analysis_enabled,
        analysis_definition=view.analysis_definition,
        analysis_profile=view.analysis_profile,
        reasoning_enabled=view.reasoning_enabled,
        derivative_strategy=view.derivative_strategy,
        derivative_count=view.derivative_count,
        provider_submission_occurred=view.provider_submission_occurred,
        provider_id=view.provider_id if view.state != "not_requested" else None,
        model_id=view.model_id if view.state != "not_requested" else None,
        prompt_version=view.prompt_version if view.state != "not_requested" else None,
        result_schema_version=result_schema_version,
        result=result,
        movie_identification_result=movie_result,
        error_code=view.error_code if view.state == "failed" else None,
        error_message=view.error_message if view.state == "failed" else None,
        attempt_count=view.attempt_count,
        created_at_ms=view.created_at_ms,
        started_at_ms=view.started_at_ms,
        completed_at_ms=view.completed_at_ms,
    )


def _error(code: str, message: str, status_code: int) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content=ErrorResponse(error=ErrorBody(code=code, message=message)).model_dump(),
    )
