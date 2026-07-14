"""FastAPI application factory for the FrameNest presentation adapter."""

from __future__ import annotations

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from importlib import resources
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, Response
from pydantic import BaseModel

from framenest.adapters.api.media_analysis_api import (
    MediaAnalysisApiDependencies,
    create_media_analysis_api_router,
)
from framenest.adapters.api.gallery_preview_api import (
    GalleryPreviewApiDependencies,
    create_gallery_preview_api_router,
)
from framenest.adapters.api.media_content_api import (
    MediaContentApiDependencies,
    create_media_content_api_router,
)
from framenest.adapters.api.media_import_api import (
    MediaImportApiDependencies,
    create_media_import_api_router,
)
from framenest.adapters.api.media_catalog_api import (
    MediaCatalogApiDependencies,
    create_media_catalog_api_router,
)
from framenest.adapters.api.media_metadata_api import (
    MediaMetadataApiDependencies,
    create_media_metadata_api_router,
)
from framenest.adapters.api.media_suggestion_api import (
    MediaSuggestionApiDependencies,
    MediaSuggestionStatusRead,
    create_media_suggestion_api_router,
)
from framenest.adapters.api.upload_api import (
    UploadApiDependencies,
    create_upload_api_router,
)
from framenest.application.library_scan import PreviewLibraryScan
from framenest.application.media_catalog import ListMediaCatalog
from framenest.application.media_import import ImportMediaFromScanCandidate
from framenest.application.media_metadata import (
    CreateCanonicalTag,
    GetMediaMetadata,
    ListCanonicalTags,
    SaveMediaMetadata,
)
from framenest.application.media_analysis import PrepareLocalMediaAnalysis
from framenest.application.media_content import ResolveMediaContent
from framenest.application.gallery_preview import GalleryPreviewService
from framenest.application.media_suggestion import PreviewMediaSuggestion
from framenest.application.media_suggestion import PreviewImportedMediaSuggestion
from framenest.application.upload_transport import UploadTransportLimits, UploadTransportService
from framenest.application.upload_transport import UploadSessionLockRegistry
from framenest.application.upload_validation import ValidateReceivedUpload
from framenest.adapters.api.library_api import (
    LibraryApiDependencies,
    create_library_api_router,
)
import framenest.adapters.api.web as web_resources
from framenest.configuration import FrameNestSettings, load_settings
from framenest.infrastructure.ai.registry import ai_provider_persisted_status_reader, resolve_ai_provider
from framenest.infrastructure.filesystem.library_scanner import LocalLibraryScanner
from framenest.infrastructure.filesystem.media_content import LocalMediaContentReader
from framenest.infrastructure.filesystem.quarantine_storage import FilesystemQuarantineStorage
from framenest.infrastructure.media_analysis import LocalMediaAnalysisAdapter
from framenest.infrastructure.media_validation import BoundedUploadMediaValidator
from framenest.infrastructure.media_analysis.gallery_preview import (
    FilesystemGalleryPreviewCache,
    PillowGalleryPreviewEncoder,
)
from framenest.infrastructure.persistence.engine import create_sqlite_engine, dispose_engine
from framenest.infrastructure.persistence.library_repository import SqliteLibraryRepository
from framenest.infrastructure.persistence.media_repository import SqliteMediaRepository
from framenest.infrastructure.persistence.media_catalog_repository import (
    SqliteMediaCatalogRepository,
)
from framenest.infrastructure.persistence.media_metadata_repository import (
    SqliteMediaMetadataRepository,
)
from framenest.infrastructure.persistence.upload_session_repository import (
    SqliteUploadSessionRepository,
)


class HealthResponse(BaseModel):
    status: Literal["ok"]


class CloudStatusResponse(BaseModel):
    server: Literal["connected", "unavailable"]
    connection: Literal["loopback", "lan", "tailscale", "unknown"]
    remote_access: str | None = None


_ASSET_MEDIA_TYPES = {
    "styles.css": "text/css; charset=utf-8",
    "app.js": "text/javascript; charset=utf-8",
}


def _read_web_resource(resource_name: str) -> bytes:
    resource = resources.files(web_resources).joinpath(resource_name)
    if not resource.is_file():
        raise HTTPException(status_code=404, detail="Not found")
    return resource.read_bytes()


def create_app(
    settings: FrameNestSettings | None = None,
    library_api_dependencies: LibraryApiDependencies | None = None,
    media_import_api_dependencies: MediaImportApiDependencies | None = None,
    media_catalog_api_dependencies: MediaCatalogApiDependencies | None = None,
    media_metadata_api_dependencies: MediaMetadataApiDependencies | None = None,
    media_analysis_api_dependencies: MediaAnalysisApiDependencies | None = None,
    media_content_api_dependencies: MediaContentApiDependencies | None = None,
    gallery_preview_api_dependencies: GalleryPreviewApiDependencies | None = None,
    media_suggestion_api_dependencies: MediaSuggestionApiDependencies | None = None,
    upload_api_dependencies: UploadApiDependencies | None = None,
) -> FastAPI:
    resolved_settings = settings if settings is not None else load_settings()
    owned_engine = None
    owned_library_repository = None
    owned_media_repository = None
    owned_media_catalog_repository = None
    owned_media_metadata_repository = None
    owned_upload_session_repository = None
    owned_upload_validation = None
    if (
        library_api_dependencies is None
        or media_import_api_dependencies is None
        or media_catalog_api_dependencies is None
        or media_metadata_api_dependencies is None
        or media_analysis_api_dependencies is None
        or media_content_api_dependencies is None
        or gallery_preview_api_dependencies is None
        or media_suggestion_api_dependencies is None
        or upload_api_dependencies is None
    ):
        owned_engine = create_sqlite_engine(resolved_settings.database_path)
        owned_library_repository = SqliteLibraryRepository(owned_engine)
        owned_media_repository = SqliteMediaRepository(owned_engine)
        owned_media_catalog_repository = SqliteMediaCatalogRepository(owned_engine)
        owned_media_metadata_repository = SqliteMediaMetadataRepository(owned_engine)
        owned_upload_session_repository = SqliteUploadSessionRepository(owned_engine)
    if library_api_dependencies is None:
        assert owned_library_repository is not None
        library_api_dependencies = LibraryApiDependencies(
            repository=owned_library_repository,
            scan_preview=PreviewLibraryScan(
                owned_library_repository,
                LocalLibraryScanner(),
            ),
            catalog_available=resolved_settings.database_path.exists,
        )
    if media_import_api_dependencies is None:
        assert owned_library_repository is not None
        assert owned_media_repository is not None
        media_import_api_dependencies = MediaImportApiDependencies(
            import_media=ImportMediaFromScanCandidate(
                owned_library_repository,
                owned_media_repository,
                LocalLibraryScanner(),
            ),
            catalog_available=resolved_settings.database_path.exists,
        )
    if media_catalog_api_dependencies is None:
        assert owned_media_catalog_repository is not None
        media_catalog_api_dependencies = MediaCatalogApiDependencies(
            list_media=ListMediaCatalog(owned_media_catalog_repository),
            catalog_available=resolved_settings.database_path.exists,
        )
    if media_metadata_api_dependencies is None:
        assert owned_media_metadata_repository is not None
        media_metadata_api_dependencies = MediaMetadataApiDependencies(
            create_tag=CreateCanonicalTag(owned_media_metadata_repository),
            list_tags=ListCanonicalTags(owned_media_metadata_repository),
            get_metadata=GetMediaMetadata(owned_media_metadata_repository),
            save_metadata=SaveMediaMetadata(owned_media_metadata_repository),
            catalog_available=resolved_settings.database_path.exists,
        )
    if media_analysis_api_dependencies is None:
        assert owned_library_repository is not None
        media_analysis_api_dependencies = MediaAnalysisApiDependencies(
            prepare_preview=PrepareLocalMediaAnalysis(
                owned_library_repository,
                LocalMediaAnalysisAdapter(),
            ),
            catalog_available=resolved_settings.database_path.exists,
        )
    if media_content_api_dependencies is None:
        assert owned_media_repository is not None
        assert owned_library_repository is not None
        media_content_api_dependencies = MediaContentApiDependencies(
            resolve_content=ResolveMediaContent(
                owned_media_repository,
                owned_library_repository,
                LocalMediaContentReader(),
            ),
            catalog_available=resolved_settings.database_path.exists,
        )
    if gallery_preview_api_dependencies is None:
        assert owned_media_repository is not None
        assert owned_library_repository is not None
        gallery_preview_api_dependencies = GalleryPreviewApiDependencies(
            preview_service=GalleryPreviewService(
                owned_media_repository,
                owned_library_repository,
                LocalMediaContentReader(),
                LocalMediaAnalysisAdapter(),
                PillowGalleryPreviewEncoder(),
                FilesystemGalleryPreviewCache(resolved_settings.gallery_preview_cache_path),
            ),
            catalog_available=resolved_settings.database_path.exists,
        )
    if media_suggestion_api_dependencies is None:
        assert owned_library_repository is not None
        resolved_ai = resolve_ai_provider(resolved_settings)
        provider = resolved_ai.provider
        suggestion_preview = None
        imported_suggestion_preview = None
        if provider is not None:
            suggestion_preview = PreviewMediaSuggestion(
                owned_library_repository,
                LocalMediaAnalysisAdapter(),
                provider,
            )
            imported_suggestion_preview = PreviewImportedMediaSuggestion(
                owned_media_repository,
                owned_library_repository,
                LocalMediaAnalysisAdapter(),
                provider,
            )
        media_suggestion_api_dependencies = MediaSuggestionApiDependencies(
            preview_suggestion=suggestion_preview,
            preview_imported_suggestion=imported_suggestion_preview,
            provider_configured=suggestion_preview is not None,
            provider_id=resolved_ai.provider_id,
            provider_display_name=resolved_ai.display_name,
            model_id=resolved_ai.model_id,
            credential_available=resolved_ai.credential_available,
            status=_ai_status_from_last_test(
                provider_selected=resolved_ai.provider_id is not None,
                credential_available=resolved_ai.credential_available,
                last_status=None if resolved_ai.last_test is None else resolved_ai.last_test.status,
            ),
            last_status_check=_last_status_payload(resolved_ai.last_status),
            last_connection_test=_last_test_payload(resolved_ai.last_test),
            read_status=_media_suggestion_status_reader(resolved_ai),
        )
    if upload_api_dependencies is None:
        assert owned_upload_session_repository is not None
        assert owned_library_repository is not None
        upload_locks = UploadSessionLockRegistry()
        storage = (
            None
            if resolved_settings.upload_quarantine_root is None
            else FilesystemQuarantineStorage(resolved_settings.upload_quarantine_root)
        )
        upload_api_dependencies = UploadApiDependencies(
            transport=UploadTransportService(
                owned_upload_session_repository,
                storage,
                owned_library_repository,
                UploadTransportLimits(
                    max_total_bytes=resolved_settings.upload_max_total_bytes,
                    max_patch_bytes=resolved_settings.upload_max_patch_bytes,
                    session_ttl_seconds=resolved_settings.upload_session_ttl_seconds,
                    min_free_space_reserve_bytes=(
                        resolved_settings.upload_min_free_space_reserve_bytes
                    ),
                ),
                quarantine_root=resolved_settings.upload_quarantine_root,
                preview_cache_root=resolved_settings.gallery_preview_cache_path,
                locks=upload_locks,
            ),
        )
        if storage is not None:
            owned_upload_validation = ValidateReceivedUpload(
                owned_upload_session_repository,
                storage,
                BoundedUploadMediaValidator(),
                locks=upload_locks,
            )

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        try:
            yield
        finally:
            if owned_engine is not None:
                dispose_engine(owned_engine)

    app = FastAPI(lifespan=lifespan)
    app.state.settings = resolved_settings
    app.state.upload_validation = owned_upload_validation
    app.include_router(create_library_api_router(library_api_dependencies))
    app.include_router(create_media_import_api_router(media_import_api_dependencies))
    app.include_router(create_media_catalog_api_router(media_catalog_api_dependencies))
    app.include_router(create_media_metadata_api_router(media_metadata_api_dependencies))
    app.include_router(create_media_analysis_api_router(media_analysis_api_dependencies))
    app.include_router(create_media_content_api_router(media_content_api_dependencies))
    app.include_router(create_gallery_preview_api_router(gallery_preview_api_dependencies))
    app.include_router(create_media_suggestion_api_router(media_suggestion_api_dependencies))
    app.include_router(create_upload_api_router(upload_api_dependencies))

    @app.get("/", response_class=HTMLResponse)
    def root() -> HTMLResponse:
        return HTMLResponse(
            content=_read_web_resource("index.html").decode("utf-8"),
            media_type="text/html; charset=utf-8",
        )

    @app.get("/assets/{asset_name}")
    def asset(asset_name: str) -> Response:
        media_type = _ASSET_MEDIA_TYPES.get(asset_name)
        if media_type is None:
            raise HTTPException(status_code=404, detail="Not found")
        return Response(
            content=_read_web_resource(asset_name),
            media_type=media_type,
        )

    @app.get("/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        return HealthResponse(status="ok")

    @app.get("/api/status/cloud", response_model=CloudStatusResponse)
    def cloud_status() -> CloudStatusResponse:
        return CloudStatusResponse(server="connected", connection="loopback", remote_access=None)

    return app


def _ai_status_from_last_test(
    *,
    provider_selected: bool,
    credential_available: bool,
    last_status: str | None,
) -> str:
    if not provider_selected:
        return "not_configured"
    if not credential_available:
        return "credential_unavailable"
    if last_status == "success":
        return "available"
    if last_status in {
        "authentication_failed",
        "rate_limited_or_quota_exhausted",
        "model_unavailable",
    }:
        return last_status
    if last_status == "provider_unreachable":
        return "provider_unreachable"
    if last_status in {"invalid_response", "provider_error"}:
        return "provider_error"
    return "configured_unverified"


def _last_test_payload(last_test: object | None) -> dict[str, object] | None:
    if last_test is None:
        return None
    return {
        "status": getattr(last_test, "status"),
        "tested_at_ms": getattr(last_test, "tested_at_ms"),
    }


def _last_status_payload(last_status: object | None) -> dict[str, object] | None:
    if last_status is None:
        return None
    return {
        "configuration_state": getattr(last_status, "configuration_state"),
        "checked_at_ms": getattr(last_status, "checked_at_ms"),
    }


def _media_suggestion_status_reader(resolved_ai: object):
    read_persisted_status = ai_provider_persisted_status_reader(
        provider_id=getattr(resolved_ai, "provider_id"),
        model_id=getattr(resolved_ai, "model_id"),
        test_state_path=getattr(resolved_ai, "test_state_path"),
        status_snapshot_path=getattr(resolved_ai, "status_snapshot_path"),
    )

    def read_status() -> MediaSuggestionStatusRead:
        persisted_status = read_persisted_status()
        return MediaSuggestionStatusRead(
            last_status_check=_last_status_payload(persisted_status.last_status),
            last_connection_test=_last_test_payload(persisted_status.last_test),
        )

    return read_status
