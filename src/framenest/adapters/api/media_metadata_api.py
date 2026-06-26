"""FastAPI routes for persistent media metadata and canonical tags."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel, UUID4, field_validator

from framenest.application.ports.media_metadata_repository import (
    CanonicalTagDefinitionConflictError,
    CanonicalTagNotFoundError,
    FrameNestMediaMetadataRepositoryError,
    MediaMetadataMediaNotFoundError,
)
from framenest.domain import FrameNestIdentityError
from framenest.domain.media_metadata import (
    CanonicalTagDisplayName,
    CanonicalTagKey,
    FrameNestMediaMetadataError,
    MediaDescription,
    MediaDisplayTitle,
)

CATALOG_UNAVAILABLE_CODE = "CATALOG_UNAVAILABLE"
CATALOG_UNAVAILABLE_MESSAGE = "The local catalog is not available."
MEDIA_NOT_FOUND_CODE = "MEDIA_NOT_FOUND"
MEDIA_NOT_FOUND_MESSAGE = "Media not found."
CANONICAL_TAG_NOT_FOUND_CODE = "CANONICAL_TAG_NOT_FOUND"
CANONICAL_TAG_NOT_FOUND_MESSAGE = "Canonical tag not found."
CANONICAL_TAG_DEFINITION_CONFLICT_CODE = "CANONICAL_TAG_DEFINITION_CONFLICT"
CANONICAL_TAG_DEFINITION_CONFLICT_MESSAGE = "Canonical tag definition conflicts."
CANONICAL_TAG_OPERATION_FAILED_CODE = "CANONICAL_TAG_OPERATION_FAILED"
CANONICAL_TAG_OPERATION_FAILED_MESSAGE = "Canonical tag operation failed."
MEDIA_METADATA_OPERATION_FAILED_CODE = "MEDIA_METADATA_OPERATION_FAILED"
MEDIA_METADATA_OPERATION_FAILED_MESSAGE = "Media metadata operation failed."


class ErrorBody(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    error: ErrorBody


class CanonicalTagRequest(BaseModel):
    key: str
    display_name: str

    @field_validator("key")
    @classmethod
    def validate_key(cls, value: str) -> str:
        CanonicalTagKey(value)
        return value

    @field_validator("display_name")
    @classmethod
    def validate_display_name(cls, value: str) -> str:
        return CanonicalTagDisplayName(value).value


class CanonicalTagResponse(BaseModel):
    key: str
    display_name: str


class CanonicalTagCreateResponse(BaseModel):
    status: str
    tag: CanonicalTagResponse


class CanonicalTagListResponse(BaseModel):
    tags: list[CanonicalTagResponse]


class MediaMetadataResponse(BaseModel):
    persisted: bool
    display_title: str | None
    description: str | None
    tags: list[CanonicalTagResponse]
    collection_key: str | None
    processed_at_ms: int | None
    created_at_ms: int | None
    updated_at_ms: int | None


class MediaMetadataSaveRequest(BaseModel):
    display_title: str | None
    description: str | None
    tag_keys: list[str]

    @field_validator("display_title")
    @classmethod
    def validate_display_title(cls, value: str | None) -> str | None:
        if value is None:
            return None
        MediaDisplayTitle(value)
        return value

    @field_validator("description")
    @classmethod
    def validate_description(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        if not stripped:
            return None
        MediaDescription(value)
        return value

    @field_validator("tag_keys")
    @classmethod
    def validate_tag_keys(cls, value: list[str]) -> list[str]:
        keys = [CanonicalTagKey(key) for key in value]
        if len(keys) > 32 or len(set(keys)) != len(keys):
            raise ValueError(MEDIA_METADATA_OPERATION_FAILED_MESSAGE)
        return value


class MediaMetadataSaveResponse(BaseModel):
    status: str
    metadata: MediaMetadataResponse


@dataclass(frozen=True, slots=True)
class MediaMetadataApiDependencies:
    """Injected dependencies for media metadata routes."""

    create_tag: object
    list_tags: object
    get_metadata: object
    save_metadata: object
    catalog_available: Callable[[], bool]


def create_media_metadata_api_router(dependencies: MediaMetadataApiDependencies) -> APIRouter:
    """Create the persistent media metadata API router."""
    router = APIRouter()

    @router.post(
        "/api/canonical-tags",
        response_model=CanonicalTagCreateResponse,
        responses={
            409: {"model": ErrorResponse},
            500: {"model": ErrorResponse},
            503: {"model": ErrorResponse},
        },
    )
    def create_tag(request: CanonicalTagRequest) -> CanonicalTagCreateResponse | JSONResponse:
        if not dependencies.catalog_available():
            return _catalog_unavailable_response()
        try:
            result = dependencies.create_tag.execute(request.key, request.display_name)
        except CanonicalTagDefinitionConflictError:
            return _error_response(
                409,
                CANONICAL_TAG_DEFINITION_CONFLICT_CODE,
                CANONICAL_TAG_DEFINITION_CONFLICT_MESSAGE,
            )
        except FrameNestMediaMetadataRepositoryError:
            return _error_response(
                500,
                CANONICAL_TAG_OPERATION_FAILED_CODE,
                CANONICAL_TAG_OPERATION_FAILED_MESSAGE,
            )
        except Exception:
            return _error_response(
                500,
                CANONICAL_TAG_OPERATION_FAILED_CODE,
                CANONICAL_TAG_OPERATION_FAILED_MESSAGE,
            )
        return JSONResponse(
            status_code=201 if result.status == "created" else 200,
            content={
                "status": result.status,
                "tag": _tag_response(result.tag).model_dump(),
            },
        )

    @router.get(
        "/api/canonical-tags",
        response_model=CanonicalTagListResponse,
        responses={500: {"model": ErrorResponse}, 503: {"model": ErrorResponse}},
    )
    def list_tags() -> CanonicalTagListResponse | JSONResponse:
        if not dependencies.catalog_available():
            return _catalog_unavailable_response()
        try:
            result = dependencies.list_tags.execute()
        except Exception:
            return _error_response(
                500,
                CANONICAL_TAG_OPERATION_FAILED_CODE,
                CANONICAL_TAG_OPERATION_FAILED_MESSAGE,
            )
        return CanonicalTagListResponse(tags=[_tag_response(tag) for tag in result.tags])

    @router.get(
        "/api/media/{media_id}/metadata",
        response_model=MediaMetadataResponse,
        responses={
            404: {"model": ErrorResponse},
            500: {"model": ErrorResponse},
            503: {"model": ErrorResponse},
        },
    )
    def get_metadata(media_id: UUID4) -> MediaMetadataResponse | JSONResponse:
        if not dependencies.catalog_available():
            return _catalog_unavailable_response()
        try:
            result = dependencies.get_metadata.execute(str(media_id))
        except MediaMetadataMediaNotFoundError:
            return _error_response(404, MEDIA_NOT_FOUND_CODE, MEDIA_NOT_FOUND_MESSAGE)
        except Exception:
            return _error_response(
                500,
                MEDIA_METADATA_OPERATION_FAILED_CODE,
                MEDIA_METADATA_OPERATION_FAILED_MESSAGE,
            )
        return _metadata_response(result)

    @router.put(
        "/api/media/{media_id}/metadata",
        response_model=MediaMetadataSaveResponse,
        responses={
            404: {"model": ErrorResponse},
            409: {"model": ErrorResponse},
            500: {"model": ErrorResponse},
            503: {"model": ErrorResponse},
        },
    )
    def save_metadata(
        media_id: UUID4,
        request: MediaMetadataSaveRequest,
    ) -> MediaMetadataSaveResponse | JSONResponse:
        if not dependencies.catalog_available():
            return _catalog_unavailable_response()
        try:
            result = dependencies.save_metadata.execute(
                str(media_id),
                request.display_title,
                request.description,
                request.tag_keys,
            )
        except MediaMetadataMediaNotFoundError:
            return _error_response(404, MEDIA_NOT_FOUND_CODE, MEDIA_NOT_FOUND_MESSAGE)
        except CanonicalTagNotFoundError:
            return _error_response(
                409,
                CANONICAL_TAG_NOT_FOUND_CODE,
                CANONICAL_TAG_NOT_FOUND_MESSAGE,
            )
        except (FrameNestMediaMetadataRepositoryError, FrameNestIdentityError):
            return _error_response(
                500,
                MEDIA_METADATA_OPERATION_FAILED_CODE,
                MEDIA_METADATA_OPERATION_FAILED_MESSAGE,
            )
        except (FrameNestMediaMetadataError, ValueError):
            return _error_response(
                500,
                MEDIA_METADATA_OPERATION_FAILED_CODE,
                MEDIA_METADATA_OPERATION_FAILED_MESSAGE,
            )
        except Exception:
            return _error_response(
                500,
                MEDIA_METADATA_OPERATION_FAILED_CODE,
                MEDIA_METADATA_OPERATION_FAILED_MESSAGE,
            )
        return MediaMetadataSaveResponse(
            status=result.status,
            metadata=_metadata_response(result.metadata),
        )

    return router


def _catalog_unavailable_response() -> JSONResponse:
    return _error_response(503, CATALOG_UNAVAILABLE_CODE, CATALOG_UNAVAILABLE_MESSAGE)


def _error_response(status_code: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"error": {"code": code, "message": message}})


def _tag_response(tag: object) -> CanonicalTagResponse:
    return CanonicalTagResponse(
        key=tag.key.value,
        display_name=tag.display_name.value,
    )


def _metadata_response(metadata: object) -> MediaMetadataResponse:
    display_title = metadata.display_title
    if display_title is not None and hasattr(display_title, "value"):
        display_title = display_title.value
    raw_description = getattr(metadata, "description", None)
    description = raw_description.value if raw_description is not None and hasattr(raw_description, "value") else raw_description
    tags = getattr(metadata, "tags", ())
    return MediaMetadataResponse(
        persisted=metadata.persisted,
        display_title=display_title,
        description=description,
        tags=[_tag_response(tag) for tag in tags],
        collection_key=metadata.collection_key,
        processed_at_ms=metadata.processed_at_ms,
        created_at_ms=metadata.created_at_ms,
        updated_at_ms=metadata.updated_at_ms,
    )
