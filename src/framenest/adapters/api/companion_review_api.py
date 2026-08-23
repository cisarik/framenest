"""Administrator companion review inbox HTTP adapter."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict

from framenest.adapters.api.tailscale_ingress import SCOPE_IDENTITY
from framenest.application.companion_review import (
    COMPANION_REVIEW_QUERY_INVALID_MESSAGE,
    DEFAULT_COMPANION_REVIEW_LIMIT,
    MAX_COMPANION_REVIEW_LIMIT,
    CompanionReviewDetail,
    CompanionReviewInboxItem,
    CompanionReviewInboxPage,
    CompanionReviewQueryError,
    GetCompanionReviewDetail,
    ListCompanionReviewInbox,
    MappedSuggestedTag,
)
from framenest.application.ports.companion_review_repository import (
    CompanionReviewMediaNotFoundError,
    CompanionReviewMovieExcludedError,
    CompanionReviewStoredResultError,
    FrameNestCompanionReviewRepositoryError,
)
from framenest.domain.identity_access import (
    CAPABILITY_MEDIA_WORKFLOW_READ,
    IdentityContext,
)

CATALOG_UNAVAILABLE_CODE = "CATALOG_UNAVAILABLE"
CATALOG_UNAVAILABLE_MESSAGE = "The local catalog is not available."
QUERY_INVALID_CODE = "INVALID_COMPANION_REVIEW_QUERY"
QUERY_FAILED_CODE = "COMPANION_REVIEW_QUERY_FAILED"
QUERY_FAILED_MESSAGE = "Companion review query failed."
MEDIA_NOT_FOUND_CODE = "MEDIA_NOT_FOUND"
MEDIA_NOT_FOUND_MESSAGE = "The requested media item was not found."
MOVIE_EXCLUDED_CODE = "COMPANION_REVIEW_MOVIE_EXCLUDED"
MOVIE_EXCLUDED_MESSAGE = "Movie workflows are excluded from companion review."
RESULT_INVALID_CODE = "COMPANION_REVIEW_RESULT_INVALID"
RESULT_INVALID_MESSAGE = "Stored analysis result is invalid."

_NO_STORE_HEADERS = {"Cache-Control": "no-store"}


class CompanionErrorBody(BaseModel):
    code: str
    message: str


class CompanionErrorResponse(BaseModel):
    error: CompanionErrorBody


class CompanionReviewInboxItemResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    media_id: str
    title: str
    analysis_run_id: str
    completed_at_ms: int
    unopened: bool


class CompanionReviewInboxListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[CompanionReviewInboxItemResponse]
    unopened_count: int
    next_cursor: str | None


@dataclass(frozen=True, slots=True)
class CompanionReviewApiDependencies:
    """Injected companion review read behavior."""

    list_inbox: ListCompanionReviewInbox | None
    get_detail: GetCompanionReviewDetail | None
    catalog_available: Callable[[], bool]


def create_companion_review_api_router(
    dependencies: CompanionReviewApiDependencies,
) -> APIRouter:
    router = APIRouter()

    @router.get(
        "/api/companion/review-inbox",
        response_model=CompanionReviewInboxListResponse,
        responses={
            422: {"model": CompanionErrorResponse},
            500: {"model": CompanionErrorResponse},
            503: {"model": CompanionErrorResponse},
        },
    )
    def list_review_inbox(
        request: Request,
        limit: int = Query(default=DEFAULT_COMPANION_REVIEW_LIMIT),
        cursor: str | None = None,
    ) -> JSONResponse:
        identity = _require_identity(request)
        if (
            not dependencies.catalog_available()
            or dependencies.list_inbox is None
        ):
            return _error(
                CATALOG_UNAVAILABLE_CODE, CATALOG_UNAVAILABLE_MESSAGE, 503
            )
        if limit < 1 or limit > MAX_COMPANION_REVIEW_LIMIT:
            return _error(
                QUERY_INVALID_CODE, COMPANION_REVIEW_QUERY_INVALID_MESSAGE, 422
            )
        try:
            page = dependencies.list_inbox.execute(
                actor_login_key=identity.login_key,
                limit=limit,
                cursor=cursor,
            )
        except CompanionReviewQueryError:
            return _error(
                QUERY_INVALID_CODE, COMPANION_REVIEW_QUERY_INVALID_MESSAGE, 422
            )
        except CompanionReviewStoredResultError:
            return _error(RESULT_INVALID_CODE, RESULT_INVALID_MESSAGE, 500)
        except FrameNestCompanionReviewRepositoryError:
            return _error(QUERY_FAILED_CODE, QUERY_FAILED_MESSAGE, 500)
        return JSONResponse(
            status_code=200,
            content=_inbox_page_dict(page),
            headers=_NO_STORE_HEADERS,
        )

    @router.get(
        "/api/companion/review-inbox/{media_id}",
        responses={
            404: {"model": CompanionErrorResponse},
            409: {"model": CompanionErrorResponse},
            422: {"model": CompanionErrorResponse},
            500: {"model": CompanionErrorResponse},
            503: {"model": CompanionErrorResponse},
        },
    )
    def get_review_detail(
        media_id: str,
        request: Request,
        limit: int = Query(default=DEFAULT_COMPANION_REVIEW_LIMIT),
        cursor: str | None = None,
    ) -> JSONResponse:
        identity = _require_identity(request)
        if (
            not dependencies.catalog_available()
            or dependencies.get_detail is None
        ):
            return _error(
                CATALOG_UNAVAILABLE_CODE, CATALOG_UNAVAILABLE_MESSAGE, 503
            )
        if limit < 1 or limit > MAX_COMPANION_REVIEW_LIMIT:
            return _error(
                QUERY_INVALID_CODE, COMPANION_REVIEW_QUERY_INVALID_MESSAGE, 422
            )
        try:
            detail = dependencies.get_detail.execute(
                media_id=media_id,
                actor_login_key=identity.login_key,
                limit=limit,
                cursor=cursor,
            )
        except CompanionReviewQueryError:
            return _error(
                QUERY_INVALID_CODE, COMPANION_REVIEW_QUERY_INVALID_MESSAGE, 422
            )
        except CompanionReviewMediaNotFoundError:
            return _error(MEDIA_NOT_FOUND_CODE, MEDIA_NOT_FOUND_MESSAGE, 404)
        except CompanionReviewMovieExcludedError:
            return _error(MOVIE_EXCLUDED_CODE, MOVIE_EXCLUDED_MESSAGE, 409)
        except CompanionReviewStoredResultError:
            return _error(RESULT_INVALID_CODE, RESULT_INVALID_MESSAGE, 500)
        except FrameNestCompanionReviewRepositoryError:
            return _error(QUERY_FAILED_CODE, QUERY_FAILED_MESSAGE, 500)
        return JSONResponse(
            status_code=200,
            content=_detail_dict(detail),
            headers=_NO_STORE_HEADERS,
        )

    return router


def _require_identity(request: Request) -> IdentityContext:
    identity = request.scope.get(SCOPE_IDENTITY)
    if not isinstance(identity, IdentityContext):
        raise HTTPException(status_code=401, detail={"code": "IDENTITY_REQUIRED"})
    if not identity.has_capability(CAPABILITY_MEDIA_WORKFLOW_READ):
        raise HTTPException(status_code=403, detail={"code": "CAPABILITY_DENIED"})
    return identity


def _inbox_page_dict(page: CompanionReviewInboxPage) -> dict:
    return {
        "items": [_inbox_item_dict(item) for item in page.items],
        "unopened_count": page.unopened_count,
        "next_cursor": page.next_cursor,
    }


def _inbox_item_dict(item: CompanionReviewInboxItem) -> dict:
    return {
        "media_id": item.media_id,
        "title": item.title,
        "analysis_run_id": item.analysis_run_id,
        "completed_at_ms": item.completed_at_ms,
        "unopened": item.unopened,
    }


def _detail_dict(detail: CompanionReviewDetail) -> dict:
    publication = detail.publication
    return {
        "media_id": detail.media_id,
        "canonical": {
            "display_title": detail.display_title,
            "description": detail.description,
            "tags": [
                {
                    "key": tag.key,
                    "display_name": tag.display_name,
                    "position": tag.position,
                }
                for tag in detail.tags
            ],
            "field_sources": {
                name: None
                if receipt is None
                else {
                    "analysis_run_id": receipt.analysis_run_id,
                    "completed_at_ms": receipt.completed_at_ms,
                    "provider_id": receipt.provider_id,
                    "model_id": receipt.model_id,
                    "applied_at_ms": receipt.applied_at_ms,
                }
                for name, receipt in detail.field_sources.items()
            },
        },
        "publication": {
            "state": "published" if publication is not None else "unpublished",
            "origin": (
                None if publication is None else publication.publication_origin.value
            ),
            "published_at_ms": (
                None if publication is None else publication.published_at_ms
            ),
            "ready": detail.readiness.ready,
            "missing_fields": list(detail.readiness.missing_fields),
        },
        "suggestions": [
            {
                "analysis_run_id": suggestion.analysis_run_id,
                "completed_at_ms": suggestion.completed_at_ms,
                "provider_id": suggestion.provider_id,
                "model_id": suggestion.model_id,
                "prompt_version": suggestion.prompt_version,
                "title": suggestion.title,
                "description": suggestion.description,
                "tags": [_tag_dict(tag) for tag in suggestion.tags],
            }
            for suggestion in detail.suggestions
        ],
        "next_cursor": detail.next_cursor,
    }


def _tag_dict(tag: MappedSuggestedTag) -> dict:
    return {
        "value": tag.value,
        "status": tag.status.value,
        "key": tag.key,
        "display_name": tag.display_name,
    }


def _error(code: str, message: str, status: int) -> JSONResponse:
    return JSONResponse(
        status_code=status,
        content={"error": {"code": code, "message": message}},
        headers=_NO_STORE_HEADERS,
    )
