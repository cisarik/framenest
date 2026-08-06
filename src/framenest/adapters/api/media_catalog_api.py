"""FastAPI routes for searchable media catalog browsing."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from fastapi import APIRouter, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, UUID4

from framenest.adapters.api.content_audience_api import (
    ContentAudienceUnavailableError,
    content_audience_allows,
)
from framenest.application.content_publication import ContentAudiencePolicy
from framenest.application.media_catalog import MediaCatalogValidationError
from framenest.application.ports.media_catalog_repository import (
    FrameNestMediaCatalogRepositoryError,
)
from framenest.domain.identities import MediaId
from framenest.domain.media_metadata import MediaCollectionKey

CATALOG_UNAVAILABLE_CODE = "CATALOG_UNAVAILABLE"
CATALOG_UNAVAILABLE_MESSAGE = "The local catalog is not available."
MEDIA_NOT_FOUND_CODE = "MEDIA_NOT_FOUND"
MEDIA_NOT_FOUND_MESSAGE = "Media not found."
MEDIA_CATALOG_INVALID_QUERY_CODE = "INVALID_MEDIA_CATALOG_QUERY"
MEDIA_CATALOG_INVALID_QUERY_MESSAGE = "Invalid media catalog query."
MEDIA_CATALOG_QUERY_FAILED_CODE = "MEDIA_CATALOG_QUERY_FAILED"
MEDIA_CATALOG_QUERY_FAILED_MESSAGE = "Media catalog query failed."


class ErrorBody(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    error: ErrorBody


class CatalogTagResponse(BaseModel):
    key: str
    display_name: str
    position: int


class CatalogLocationResponse(BaseModel):
    location_id: str
    library_id: str
    relative_path: str
    availability: str
    observed_size_bytes: int | None
    observed_mtime_ns: int | None


class CatalogMediaResponse(BaseModel):
    media_id: str
    media_kind: str
    created_at_ms: int
    updated_at_ms: int
    display_title: str | None
    collection_key: str | None
    processed_at_ms: int | None
    tags: list[CatalogTagResponse]
    locations: list[CatalogLocationResponse]
    content_category: str = "general"
    acquisition_source: str = "unknown"
    description: str | None = None
    cover_ready: bool = False


class MediaCatalogResponse(BaseModel):
    items: list[CatalogMediaResponse]
    total: int
    limit: int
    offset: int
    q: str | None
    tag_keys: list[str]
    content_category: str | None = None
    acquisition_source: str | None = None


@dataclass(frozen=True, slots=True)
class MediaCatalogApiDependencies:
    """Injected dependencies for media catalog routes."""

    list_media: object
    catalog_available: Callable[[], bool]
    get_media: object | None = None
    audience_policy: ContentAudiencePolicy | None = None


def create_media_catalog_api_router(dependencies: MediaCatalogApiDependencies) -> APIRouter:
    """Create the searchable media catalog API router."""
    router = APIRouter()

    @router.get(
        "/api/media",
        response_model=MediaCatalogResponse,
        responses={
            422: {"model": ErrorResponse},
            500: {"model": ErrorResponse},
            503: {"model": ErrorResponse},
        },
    )
    def list_media(
        q: str | None = None,
        tag: list[str] = Query(default=[]),
        limit: int = Query(default=24, ge=1, le=100),
        offset: int = Query(default=0, ge=0),
        collection: str | None = None,
        content_category: str | None = None,
        acquisition_source: str | None = None,
    ) -> MediaCatalogResponse | JSONResponse:
        if not dependencies.catalog_available():
            return _catalog_unavailable_response()
        parsed_collection: MediaCollectionKey | None = None
        if collection is not None:
            try:
                parsed_collection = MediaCollectionKey(collection)
            except Exception:
                return _error_response(
                    422,
                    MEDIA_CATALOG_INVALID_QUERY_CODE,
                    MEDIA_CATALOG_INVALID_QUERY_MESSAGE,
                )
        try:
            result = dependencies.list_media.execute(
                q=q,
                tag_keys=tag,
                limit=limit,
                offset=offset,
                collection_key=parsed_collection,
                content_category=content_category,
                acquisition_source=acquisition_source,
            )
        except MediaCatalogValidationError:
            return _error_response(
                422,
                MEDIA_CATALOG_INVALID_QUERY_CODE,
                MEDIA_CATALOG_INVALID_QUERY_MESSAGE,
            )
        except FrameNestMediaCatalogRepositoryError:
            return _error_response(
                500,
                MEDIA_CATALOG_QUERY_FAILED_CODE,
                MEDIA_CATALOG_QUERY_FAILED_MESSAGE,
            )
        except Exception:
            return _error_response(
                500,
                MEDIA_CATALOG_QUERY_FAILED_CODE,
                MEDIA_CATALOG_QUERY_FAILED_MESSAGE,
            )
        return _catalog_response(result)

    @router.get(
        "/api/media/{media_id}",
        response_model=CatalogMediaResponse,
        responses={
            404: {"model": ErrorResponse},
            500: {"model": ErrorResponse},
            503: {"model": ErrorResponse},
        },
    )
    def get_media(
        media_id: UUID4,
        request: Request,
    ) -> CatalogMediaResponse | JSONResponse:
        if not dependencies.catalog_available() or dependencies.get_media is None:
            return _catalog_unavailable_response()
        parsed_id = MediaId.from_string(str(media_id))
        try:
            if not content_audience_allows(
                request=request,
                media_id=parsed_id,
                policy=dependencies.audience_policy,
            ):
                return _error_response(
                    404,
                    MEDIA_NOT_FOUND_CODE,
                    MEDIA_NOT_FOUND_MESSAGE,
                )
        except ContentAudienceUnavailableError:
            return _error_response(
                500,
                MEDIA_CATALOG_QUERY_FAILED_CODE,
                MEDIA_CATALOG_QUERY_FAILED_MESSAGE,
            )
        try:
            item = dependencies.get_media.execute(str(media_id))
        except MediaCatalogValidationError:
            return _error_response(
                404,
                MEDIA_NOT_FOUND_CODE,
                MEDIA_NOT_FOUND_MESSAGE,
            )
        except FrameNestMediaCatalogRepositoryError:
            return _error_response(
                500,
                MEDIA_CATALOG_QUERY_FAILED_CODE,
                MEDIA_CATALOG_QUERY_FAILED_MESSAGE,
            )
        except Exception:
            return _error_response(
                500,
                MEDIA_CATALOG_QUERY_FAILED_CODE,
                MEDIA_CATALOG_QUERY_FAILED_MESSAGE,
            )
        if item is None:
            return _error_response(
                404,
                MEDIA_NOT_FOUND_CODE,
                MEDIA_NOT_FOUND_MESSAGE,
            )
        return _media_response(item)

    return router


def _catalog_unavailable_response() -> JSONResponse:
    return _error_response(503, CATALOG_UNAVAILABLE_CODE, CATALOG_UNAVAILABLE_MESSAGE)


def _error_response(status_code: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"error": {"code": code, "message": message}})


def _catalog_response(result: object) -> MediaCatalogResponse:
    return MediaCatalogResponse(
        items=[_media_response(item) for item in result.items],
        total=result.total,
        limit=result.limit,
        offset=result.offset,
        q=result.q,
        tag_keys=[key.value for key in result.tag_keys],
        content_category=getattr(result, "content_category", None),
        acquisition_source=getattr(result, "acquisition_source", None),
    )


def _media_response(item: object) -> CatalogMediaResponse:
    return CatalogMediaResponse(
        media_id=item.media_id,
        media_kind=item.media_kind,
        created_at_ms=item.created_at_ms,
        updated_at_ms=item.updated_at_ms,
        display_title=item.display_title,
        collection_key=item.collection_key,
        processed_at_ms=item.processed_at_ms,
        content_category=getattr(item, "content_category", "general"),
        acquisition_source=getattr(item, "acquisition_source", "unknown"),
        description=getattr(item, "description", None),
        cover_ready=getattr(item, "cover_ready", False),
        tags=[
            CatalogTagResponse(
                key=tag.key,
                display_name=tag.display_name,
                position=tag.position,
            )
            for tag in item.tags
        ],
        locations=[
            CatalogLocationResponse(
                location_id=location.location_id,
                library_id=location.library_id,
                relative_path=location.relative_path,
                availability=location.availability,
                observed_size_bytes=location.observed_size_bytes,
                observed_mtime_ns=location.observed_mtime_ns,
            )
            for location in item.locations
        ],
    )
