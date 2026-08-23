"""FastAPI application factory for the FrameNest presentation adapter."""

from __future__ import annotations

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from importlib import resources
from ipaddress import ip_address
from pathlib import Path
import time
from typing import Literal

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, Response
from pydantic import BaseModel

from framenest.adapters.api.media_analysis_api import (
    MediaAnalysisApiDependencies,
    create_media_analysis_api_router,
)
from framenest.adapters.api.catalog_removal_api import (
    CatalogRemovalApiDependencies,
    create_catalog_removal_api_router,
)
from framenest.adapters.api.content_publication_api import (
    ContentPublicationApiDependencies,
    create_content_publication_api_router,
)
from framenest.adapters.api.cover_api import (
    CoverApiDependencies,
    create_cover_api_router,
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
from framenest.adapters.api.media_alias_api import (
    MediaAliasApiDependencies,
    create_media_alias_api_router,
)
from framenest.adapters.api.media_suggestion_api import (
    MediaSuggestionApiDependencies,
    MediaSuggestionStatusRead,
    create_media_suggestion_api_router,
)
from framenest.adapters.api.media_analysis_lifecycle_api import (
    MediaAnalysisLifecycleApiDependencies,
    create_media_analysis_lifecycle_api_router,
)
from framenest.adapters.api.upload_api import (
    UploadApiDependencies,
    create_upload_api_router,
)
from framenest.adapters.api.youtube_operator_api import (
    YouTubeOperatorApiDependencies,
    create_youtube_operator_api_router,
)
from framenest.adapters.api.youtube_browser_api import (
    YouTubeBrowserApiDependencies,
    create_youtube_browser_api_router,
)
from framenest.adapters.api.youtube_request_api import (
    YouTubeRequestApiDependencies,
    create_youtube_request_api_router,
)
from framenest.adapters.api.tailscale_ingress import (
    SCOPE_IDENTITY,
    TailscaleIngressMiddleware,
)
from framenest.application.in_process_lifecycle import (
    APPLICATION_LIFESPAN_SHUTDOWN_BUDGET_SECONDS,
    StartedResource,
    create_application_shutdown_deadline,
    shutdown_started_resources,
)
from framenest.application.library_scan import PreviewLibraryScan
from framenest.application.catalog_removal import CatalogMediaRemovalService
from framenest.application.content_publication import (
    ContentAudiencePolicy,
    GetMediaWorkflowStatus,
    ListAdminMedia,
    PublishContent,
)
from framenest.application.media_catalog import GetMediaCatalogItem, ListMediaCatalog
from framenest.application.companion_picker import ListCompanionPickerMedia
from framenest.application.media_import import ImportMediaFromScanCandidate
from framenest.application.media_metadata import (
    CreateCanonicalTag,
    GetMediaMetadata,
    ListCanonicalTags,
    SaveMediaMetadata,
)
from framenest.application.media_user_alias import GetMediaUserAlias, SaveMediaUserAlias
from framenest.application.media_analysis import PrepareLocalMediaAnalysis
from framenest.application.media_content import ResolveMediaContent
from framenest.application.gallery_preview import GalleryPreviewService
from framenest.application.media_cover import CoverService
from framenest.application.media_suggestion import PreviewMediaSuggestion
from framenest.application.media_suggestion import PreviewImportedMediaSuggestion
from framenest.application.upload_transport import (
    UploadTransportLimits,
    UploadTransportService,
    UploadSessionLockRegistry,
    default_now_ms,
)
from framenest.application.upload_catalog import (
    CatalogPublishedUpload,
    CatalogUploadClassification,
)
from framenest.application.upload_catalog_coordinator import UploadCatalogCoordinator
from framenest.application.media_analysis_coordinator import (
    InterruptAwareMediaAnalysisRunExecutor,
    MediaAnalysisCoordinator,
)
from framenest.application.media_analysis_lifecycle import (
    AutomaticImportedMediaSuggestionExecutor,
    CatalogedAnalysisTarget,
    ReadAutomaticMediaAnalysis,
    RequestManualMediaAnalysis,
    ScheduleAutomaticMediaAnalysis,
)
from framenest.domain.media_classification import MOVIE_IDENTIFICATION_ANALYSIS_DEFINITION
from framenest.application.upload_publication import PublishPendingUpload
from framenest.application.upload_publication_coordinator import (
    UploadPublicationCoordinator,
)
from framenest.application.upload_validation import ValidateReceivedUpload
from framenest.application.upload_validation_coordinator import UploadValidationCoordinator
from framenest.application.youtube_acquisition import (
    YouTubeAcquisitionCoordinator,
    YouTubeAcquisitionService,
    YouTubeRequestLimits,
    YouTubeRequestService,
    automatic_analysis_allowed_for_upload,
    youtube_classification_for_upload,
)
from framenest.application.x_acquisition import (
    XAcquisitionAdministrationService,
    XAcquisitionCoordinator,
    XAcquisitionRequestService,
    XRequestLimits,
    automatic_analysis_allowed_for_upload as x_automatic_analysis_allowed_for_upload,
    x_classification_for_upload,
)
from framenest.adapters.api.x_request_api import (
    XRequestApiDependencies,
    create_x_request_api_router,
)
from framenest.adapters.api.x_companion_api import (
    XCompanionApiDependencies,
    create_x_companion_api_router,
)
from framenest.adapters.api.x_admin_api import (
    XAdminApiDependencies,
    create_x_admin_api_router,
)
from framenest.adapters.api.library_api import (
    LibraryApiDependencies,
    create_library_api_router,
)
from framenest.domain import LibraryId, LibraryPathFlavor
from framenest.domain.uploads import UploadSessionId
from framenest.domain.identity_access import (
    IdentityContext,
    build_identity_mapping,
)
import framenest.adapters.api.web as web_resources
from framenest.configuration import (
    INGRESS_MODE_TAILSCALE_UDS,
    FrameNestSettings,
    load_settings,
)
from framenest.infrastructure.ai.registry import ai_provider_persisted_status_reader, resolve_ai_provider
from framenest.infrastructure.filesystem.library_scanner import LocalLibraryScanner
from framenest.infrastructure.filesystem.media_content import LocalMediaContentReader
from framenest.infrastructure.filesystem.quarantine_storage import FilesystemQuarantineStorage
from framenest.infrastructure.filesystem.published_media_storage import (
    FilesystemPublishedMediaStorage,
)
from framenest.infrastructure.filesystem.derived_artifact_cleanup import (
    FilesystemDerivedArtifactCleanup,
)
from framenest.infrastructure.filesystem.cover_storage import (
    FilesystemCoverThumbnailCache,
    FilesystemDurableCoverStorage,
    PillowCoverEncoder,
)
from framenest.infrastructure.media_analysis import LocalMediaAnalysisAdapter
from framenest.infrastructure.media_analysis.process import SubprocessRunner
from framenest.infrastructure.media_analysis.cover_frame import LocalCoverSourceAdapter
from framenest.infrastructure.media_validation import BoundedUploadMediaValidator
from framenest.infrastructure.media_analysis.gallery_preview import (
    FilesystemGalleryPreviewCache,
    PillowGalleryPreviewEncoder,
)
from framenest.infrastructure.persistence.engine import create_sqlite_engine, dispose_engine
from framenest.infrastructure.persistence.catalog_removal_repository import (
    SqliteCatalogRemovalRepository,
)
from framenest.infrastructure.persistence.content_publication_repository import (
    SqliteContentPublicationRepository,
)
from framenest.infrastructure.persistence.library_repository import SqliteLibraryRepository
from framenest.infrastructure.persistence.media_cover_repository import (
    SqliteMediaCoverRepository,
)
from framenest.infrastructure.persistence.media_repository import SqliteMediaRepository
from framenest.infrastructure.persistence.media_catalog_repository import (
    SqliteMediaCatalogRepository,
)
from framenest.infrastructure.persistence.media_metadata_repository import (
    SqliteMediaMetadataRepository,
)
from framenest.infrastructure.persistence.media_user_alias_repository import (
    SqliteMediaUserAliasRepository,
)
from framenest.infrastructure.persistence.upload_session_repository import (
    SqliteUploadSessionRepository,
)
from framenest.infrastructure.persistence.upload_publication_repository import (
    SqliteUploadPublicationRepository,
)
from framenest.infrastructure.persistence.media_analysis_run_repository import (
    SqliteMediaAnalysisRunRepository,
)
from framenest.infrastructure.persistence.security_audit_repository import (
    SqliteSecurityAuditRepository,
)
from framenest.infrastructure.persistence.youtube_acquisition_claim_repository import (
    SqliteYouTubeAcquisitionClaimRepository,
)
from framenest.infrastructure.persistence.x_acquisition_claim_repository import (
    SqliteXAcquisitionClaimRepository,
)
from framenest.infrastructure.youtube.downloader import YtDlpYouTubeDownloader
from framenest.infrastructure.youtube.staging import FilesystemYouTubeStaging
from framenest.infrastructure.x.downloader import YtDlpXExtractor
from framenest.infrastructure.x.staging import FilesystemXStaging
from framenest.structured_logging import get_logger

LOGGER = get_logger("api_application")


class HealthResponse(BaseModel):
    status: Literal["ok"]


class CloudStatusResponse(BaseModel):
    server: Literal["connected", "unavailable"]
    connection: Literal["loopback", "lan", "tailscale", "unknown"]
    remote_access: str | None = None


class IdentityMeResponse(BaseModel):
    login: str
    display_name: str
    role: str
    capabilities: list[str]
    provenance: str


_ASSET_MEDIA_TYPES = {
    "styles.css": "text/css; charset=utf-8",
    "app.js": "text/javascript; charset=utf-8",
    "companion_host.js": "text/javascript; charset=utf-8",
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
    media_alias_api_dependencies: MediaAliasApiDependencies | None = None,
    media_analysis_api_dependencies: MediaAnalysisApiDependencies | None = None,
    media_content_api_dependencies: MediaContentApiDependencies | None = None,
    gallery_preview_api_dependencies: GalleryPreviewApiDependencies | None = None,
    media_suggestion_api_dependencies: MediaSuggestionApiDependencies | None = None,
    media_analysis_lifecycle_api_dependencies: (
        MediaAnalysisLifecycleApiDependencies | None
    ) = None,
    content_publication_api_dependencies: ContentPublicationApiDependencies
    | None = None,
    catalog_removal_api_dependencies: CatalogRemovalApiDependencies | None = None,
    cover_api_dependencies: CoverApiDependencies | None = None,
    upload_api_dependencies: UploadApiDependencies | None = None,
    youtube_operator_api_dependencies: YouTubeOperatorApiDependencies
    | None = None,
    youtube_browser_api_dependencies: YouTubeBrowserApiDependencies | None = None,
    youtube_request_api_dependencies: YouTubeRequestApiDependencies | None = None,
    youtube_downloader: object | None = None,
    x_extractor: object | None = None,
    x_request_api_dependencies: XRequestApiDependencies | None = None,
    x_admin_api_dependencies: XAdminApiDependencies | None = None,
    x_companion_api_dependencies: XCompanionApiDependencies | None = None,
    security_audit_recorder: object | None = None,
    lifespan_shutdown_budget_seconds: float | None = None,
    shutdown_clock: object | None = None,
) -> FastAPI:
    resolved_settings = settings if settings is not None else load_settings()
    tailscale_ingress_enabled = (
        resolved_settings.ingress_mode == INGRESS_MODE_TAILSCALE_UDS
    )
    identity_mapping = build_identity_mapping(resolved_settings.identity_map)
    owned_engine = None
    owned_library_repository = None
    owned_media_repository = None
    owned_media_catalog_repository = None
    owned_media_metadata_repository = None
    owned_media_user_alias_repository = None
    owned_upload_session_repository = None
    owned_upload_validation = None
    owned_upload_validation_coordinator = None
    owned_upload_publication = None
    owned_upload_publication_coordinator = None
    owned_upload_catalog = None
    owned_upload_catalog_coordinator = None
    owned_media_analysis_run_repository = None
    owned_content_publication_repository = None
    owned_content_audience_policy = None
    owned_cover_repository = None
    owned_cover_service = None
    owned_cover_storage = None
    owned_cover_thumbnail_cache = None
    owned_gallery_preview_cache = None
    owned_media_analysis_coordinator = None
    owned_youtube_claim_repository = None
    owned_youtube_staging = None
    owned_youtube_acquisition_coordinator = None
    owned_youtube_acquisition_service = None
    owned_youtube_request_service = None
    owned_x_claim_repository = None
    owned_x_staging = None
    owned_x_acquisition_coordinator = None
    owned_x_request_service = None
    owned_x_admin_service = None
    if (
        library_api_dependencies is None
        or media_import_api_dependencies is None
        or media_catalog_api_dependencies is None
        or media_metadata_api_dependencies is None
        or media_analysis_api_dependencies is None
        or media_content_api_dependencies is None
        or gallery_preview_api_dependencies is None
        or media_suggestion_api_dependencies is None
        or media_analysis_lifecycle_api_dependencies is None
        or content_publication_api_dependencies is None
        or cover_api_dependencies is None
        or upload_api_dependencies is None
    ):
        owned_engine = create_sqlite_engine(resolved_settings.database_path)
        owned_library_repository = SqliteLibraryRepository(owned_engine)
        owned_media_repository = SqliteMediaRepository(owned_engine)
        owned_media_catalog_repository = SqliteMediaCatalogRepository(owned_engine)
        owned_media_metadata_repository = SqliteMediaMetadataRepository(owned_engine)
        owned_media_user_alias_repository = SqliteMediaUserAliasRepository(owned_engine)
        owned_upload_session_repository = SqliteUploadSessionRepository(owned_engine)
        owned_media_analysis_run_repository = SqliteMediaAnalysisRunRepository(
            owned_engine
        )
        owned_content_publication_repository = (
            SqliteContentPublicationRepository(owned_engine)
        )
        owned_cover_repository = SqliteMediaCoverRepository(owned_engine)
        owned_youtube_claim_repository = (
            SqliteYouTubeAcquisitionClaimRepository(owned_engine)
        )
        owned_x_claim_repository = SqliteXAcquisitionClaimRepository(owned_engine)
        owned_content_audience_policy = ContentAudiencePolicy(
            owned_content_publication_repository,
            youtube_requester_private_access=owned_youtube_claim_repository,
            x_requester_private_access=owned_x_claim_repository,
        )
    if cover_api_dependencies is None:
        assert owned_media_repository is not None
        assert owned_library_repository is not None
        assert owned_cover_repository is not None
        cover_storage, cover_thumbnail_cache = _resolve_cover_storage(
            resolved_settings,
            owned_library_repository,
        )
        owned_cover_storage = cover_storage
        owned_cover_thumbnail_cache = cover_thumbnail_cache
        owned_cover_service = CoverService(
            owned_media_repository,
            owned_library_repository,
            LocalCoverSourceAdapter(),
            PillowCoverEncoder(),
            cover_storage,
            cover_thumbnail_cache,
            owned_cover_repository,
        )
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
        _catalog_cover_states = (
            owned_cover_service.cover_ready_map
            if owned_cover_service is not None
            else None
        )
        media_catalog_api_dependencies = MediaCatalogApiDependencies(
            list_media=ListMediaCatalog(
                owned_media_catalog_repository,
                cover_states=_catalog_cover_states,
            ),
            get_media=GetMediaCatalogItem(
                owned_media_catalog_repository,
                cover_states=_catalog_cover_states,
            ),
            catalog_available=resolved_settings.database_path.exists,
            audience_policy=owned_content_audience_policy,
        )
    if media_metadata_api_dependencies is None:
        assert owned_media_metadata_repository is not None
        media_metadata_api_dependencies = MediaMetadataApiDependencies(
            create_tag=CreateCanonicalTag(owned_media_metadata_repository),
            list_tags=ListCanonicalTags(owned_media_metadata_repository),
            get_metadata=GetMediaMetadata(owned_media_metadata_repository),
            save_metadata=SaveMediaMetadata(owned_media_metadata_repository),
            catalog_available=resolved_settings.database_path.exists,
            audience_policy=owned_content_audience_policy,
        )
    if media_alias_api_dependencies is None:
        if owned_media_user_alias_repository is not None:
            media_alias_api_dependencies = MediaAliasApiDependencies(
                get_alias=GetMediaUserAlias(owned_media_user_alias_repository),
                save_alias=SaveMediaUserAlias(owned_media_user_alias_repository),
                catalog_available=resolved_settings.database_path.exists,
                audience_policy=owned_content_audience_policy,
            )
        else:
            media_alias_api_dependencies = MediaAliasApiDependencies(
                get_alias=None,
                save_alias=None,
                catalog_available=lambda: False,
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
            audience_policy=owned_content_audience_policy,
        )
    if gallery_preview_api_dependencies is None:
        assert owned_media_repository is not None
        assert owned_library_repository is not None
        owned_gallery_preview_cache = FilesystemGalleryPreviewCache(
            resolved_settings.gallery_preview_cache_path
        )
        gallery_preview_api_dependencies = GalleryPreviewApiDependencies(
            preview_service=GalleryPreviewService(
                owned_media_repository,
                owned_library_repository,
                LocalMediaContentReader(),
                LocalMediaAnalysisAdapter(),
                PillowGalleryPreviewEncoder(),
                owned_gallery_preview_cache,
            ),
            catalog_available=resolved_settings.database_path.exists,
            audience_policy=owned_content_audience_policy,
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
            audience_policy=owned_content_audience_policy,
        )
    if media_analysis_lifecycle_api_dependencies is None:
        assert owned_media_analysis_run_repository is not None
        assert owned_media_repository is not None
        assert owned_library_repository is not None
        resolved_analysis_ai = resolve_ai_provider(resolved_settings)
        analysis_provider = resolved_analysis_ai.provider
        analysis_scheduler = ScheduleAutomaticMediaAnalysis(
            owned_media_analysis_run_repository,
            enabled=resolved_settings.automatic_media_analysis_enabled,
        )
        analysis_manual_requester = RequestManualMediaAnalysis(
            owned_media_analysis_run_repository,
        )
        analysis_process_runner = SubprocessRunner()
        analysis_executor = InterruptAwareMediaAnalysisRunExecutor(
            owned_media_analysis_run_repository,
            AutomaticImportedMediaSuggestionExecutor(
                owned_media_repository,
                owned_library_repository,
                LocalMediaAnalysisAdapter(analysis_process_runner),
                analysis_provider,
            ),
            max_attempts=resolved_settings.automatic_media_analysis_max_attempts,
            process_runner=analysis_process_runner,
        )
        owned_media_analysis_coordinator = MediaAnalysisCoordinator(
            owned_media_analysis_run_repository,
            analysis_scheduler,
            analysis_executor,
            manual_requester=analysis_manual_requester,
            process_runner=analysis_process_runner,
        )
        movie_identification_executor = None
        movie_identification_requester = None
        if analysis_provider is not None and hasattr(analysis_provider, "identify_movie"):
            from framenest.application.movie_identification_lifecycle import (
                ExecuteMovieIdentificationRun,
                request_movie_identification,
            )
            from framenest.infrastructure.media_analysis.movie_identification import (
                LocalMovieIdentificationAdapter,
            )

            movie_identification_executor = ExecuteMovieIdentificationRun(
                owned_media_analysis_run_repository,
                owned_media_repository,
                owned_library_repository,
                LocalMovieIdentificationAdapter(),
                analysis_provider,
                provider_id=resolved_analysis_ai.provider_id,
                model_id=resolved_analysis_ai.model_id,
            )

            def _request_movie_identification(media_id, location_id):
                return request_movie_identification(
                    owned_media_analysis_run_repository,
                    CatalogedAnalysisTarget(
                        media_id=media_id,
                        media_location_id=location_id,
                    ),
                )

            movie_identification_requester = _request_movie_identification

        media_analysis_lifecycle_api_dependencies = MediaAnalysisLifecycleApiDependencies(
            read_analysis=ReadAutomaticMediaAnalysis(
                owned_media_analysis_run_repository
            ),
            automatic_analysis_enabled=(
                resolved_settings.automatic_media_analysis_enabled
            ),
            provider_configured=analysis_provider is not None,
            provider_id=resolved_analysis_ai.provider_id,
            model_id=resolved_analysis_ai.model_id,
            request_manual_analysis=owned_media_analysis_coordinator.request_manual,
            request_movie_identification=movie_identification_requester,
            read_movie_identification=ReadAutomaticMediaAnalysis(
                owned_media_analysis_run_repository,
                analysis_definition=MOVIE_IDENTIFICATION_ANALYSIS_DEFINITION,
            ).execute,
            execute_movie_identification=(
                movie_identification_executor.execute
                if movie_identification_executor is not None
                else None
            ),
            audience_policy=owned_content_audience_policy,
        )
    if content_publication_api_dependencies is None:
        assert owned_content_publication_repository is not None
        content_publication_api_dependencies = ContentPublicationApiDependencies(
            list_admin_media=ListAdminMedia(
                owned_content_publication_repository
            ),
            publish_content=PublishContent(
                owned_content_publication_repository
            ),
            catalog_available=resolved_settings.database_path.exists,
        )
    if catalog_removal_api_dependencies is None and owned_engine is not None:
        if owned_gallery_preview_cache is None:
            owned_gallery_preview_cache = FilesystemGalleryPreviewCache(
                resolved_settings.gallery_preview_cache_path
            )
        if owned_cover_storage is None or owned_cover_thumbnail_cache is None:
            assert owned_library_repository is not None
            owned_cover_storage, owned_cover_thumbnail_cache = _resolve_cover_storage(
                resolved_settings,
                owned_library_repository,
            )
        catalog_removal_api_dependencies = CatalogRemovalApiDependencies(
            service=CatalogMediaRemovalService(
                repository=SqliteCatalogRemovalRepository(owned_engine),
                cleanup=FilesystemDerivedArtifactCleanup(
                    cover_storage=owned_cover_storage,
                    thumbnail_cache=owned_cover_thumbnail_cache,
                    preview_cache=owned_gallery_preview_cache,
                ),
                now_ms=default_now_ms,
            )
        )
    if cover_api_dependencies is None:
        assert owned_cover_service is not None
        cover_api_dependencies = CoverApiDependencies(
            cover_service=owned_cover_service,
            catalog_available=resolved_settings.database_path.exists,
            audience_policy=owned_content_audience_policy,
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
        owned_youtube_staging = _resolve_youtube_staging(
            resolved_settings,
            owned_library_repository,
        )
        published_storage = _resolve_published_storage(
            resolved_settings,
            owned_library_repository,
            quarantine_configured=storage is not None,
        )
        owned_upload_publication_repository = None
        if published_storage is not None:
            assert owned_engine is not None
            assert storage is not None
            owned_upload_publication_repository = SqliteUploadPublicationRepository(
                owned_engine
            )
            owned_upload_publication = PublishPendingUpload(
                owned_upload_publication_repository,
                published_storage,
                storage,
            )
            def _combined_classification(
                upload_id: UploadSessionId,
            ) -> CatalogUploadClassification | None:
                if owned_youtube_claim_repository is not None:
                    result = youtube_classification_for_upload(
                        owned_youtube_claim_repository, upload_id
                    )
                    if result is not None:
                        return result
                if owned_x_claim_repository is not None:
                    return x_classification_for_upload(
                        owned_x_claim_repository, upload_id
                    )
                return None

            def _combined_analysis_allowed(upload_id: UploadSessionId) -> bool:
                if owned_x_claim_repository is not None and (
                    x_automatic_analysis_allowed_for_upload(
                        owned_x_claim_repository, upload_id, identity_mapping
                    )
                    is False
                ):
                    return False
                if owned_youtube_claim_repository is not None:
                    return automatic_analysis_allowed_for_upload(
                        owned_youtube_claim_repository, upload_id
                    )
                return True

            owned_upload_catalog = CatalogPublishedUpload(
                owned_upload_publication_repository,
                classification_for_upload=_combined_classification,
            )
            owned_upload_catalog_coordinator = UploadCatalogCoordinator(
                owned_upload_publication_repository,
                owned_upload_catalog,
                upload_locks,
                analysis_notifier=owned_media_analysis_coordinator,
                analysis_allowed_for_upload=_combined_analysis_allowed,
            )
            owned_upload_publication_coordinator = UploadPublicationCoordinator(
                owned_upload_publication_repository,
                owned_upload_publication,
                upload_locks,
                catalog_coordinator=owned_upload_catalog_coordinator,
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
            publication_repository=owned_upload_publication_repository,
        )
        validation_process_runner = SubprocessRunner()
        if storage is not None:
            owned_upload_validation = ValidateReceivedUpload(
                owned_upload_session_repository,
                storage,
                BoundedUploadMediaValidator(validation_process_runner),
                locks=upload_locks,
            )
            owned_upload_validation_coordinator = UploadValidationCoordinator(
                owned_upload_session_repository,
                owned_upload_validation,
                upload_locks,
                publication_coordinator=owned_upload_publication_coordinator,
                process_runner=validation_process_runner,
            )
            upload_api_dependencies = UploadApiDependencies(
                transport=upload_api_dependencies.transport,
                validation_coordinator=owned_upload_validation_coordinator,
                publication_coordinator=owned_upload_publication_coordinator,
                publication_repository=upload_api_dependencies.publication_repository,
            )
        if (
            owned_youtube_staging is not None
            and owned_youtube_claim_repository is not None
            and owned_upload_publication_repository is not None
            and owned_upload_validation_coordinator is not None
            and ip_address(resolved_settings.host).is_loopback
        ):
            selected_downloader = (
                youtube_downloader
                if youtube_downloader is not None
                else YtDlpYouTubeDownloader(
                    owned_youtube_staging,
                    max_final_size_bytes=resolved_settings.upload_max_total_bytes,
                    max_staging_size_bytes=(
                        resolved_settings.youtube_acquisition_max_staging_bytes
                    ),
                    free_space_reserve_bytes=(
                        resolved_settings.upload_min_free_space_reserve_bytes
                    ),
                )
            )
            owned_youtube_acquisition_coordinator = YouTubeAcquisitionCoordinator(
                owned_youtube_claim_repository,
                selected_downloader,
                owned_youtube_staging,
                upload_api_dependencies.transport,
                owned_upload_session_repository,
                owned_upload_publication_repository,
                validation_coordinator=owned_upload_validation_coordinator,
                publication_coordinator=owned_upload_publication_coordinator,
                chunk_size_bytes=resolved_settings.upload_max_patch_bytes,
            )
            owned_youtube_acquisition_service = YouTubeAcquisitionService(
                owned_youtube_claim_repository,
                owned_upload_session_repository,
                owned_youtube_staging,
                notifier=owned_youtube_acquisition_coordinator,
            )
            assert owned_content_publication_repository is not None

            def _youtube_request_free_space() -> int:
                assert owned_youtube_staging is not None
                return int(owned_youtube_staging.available_bytes())

            owned_youtube_request_service = YouTubeRequestService(
                owned_youtube_claim_repository,
                owned_content_publication_repository,
                owned_youtube_staging,
                limits=YouTubeRequestLimits(
                    max_active_per_user=(
                        resolved_settings.youtube_request_max_active_per_user
                    ),
                    max_global_active=(
                        resolved_settings.youtube_request_max_global_active
                    ),
                    max_submits_per_hour=(
                        resolved_settings.youtube_request_max_submits_per_hour
                    ),
                    max_failed_per_24h=(
                        resolved_settings.youtube_request_max_failed_per_24h
                    ),
                    max_private_items=(
                        resolved_settings.youtube_request_max_private_items
                    ),
                    max_private_bytes=(
                        resolved_settings.youtube_request_max_private_bytes
                    ),
                    min_free_space_reserve_bytes=(
                        resolved_settings.upload_min_free_space_reserve_bytes
                    ),
                    max_final_media_bytes=resolved_settings.upload_max_total_bytes,
                    free_space_bytes=_youtube_request_free_space,
                ),
                notifier=owned_youtube_acquisition_coordinator,
            )
    if youtube_operator_api_dependencies is None:
        youtube_operator_api_dependencies = YouTubeOperatorApiDependencies(
            service=owned_youtube_acquisition_service,
            enabled=(
                owned_youtube_acquisition_service is not None
                and ip_address(resolved_settings.host).is_loopback
            ),
        )

    # ------------------------------------------------------------------ X
    if (
        resolved_settings.x_acquisition_root is not None
        and owned_upload_validation_coordinator is not None
        and owned_upload_publication_coordinator is not None
        and owned_x_claim_repository is not None
        and ip_address(resolved_settings.host).is_loopback
    ):
        owned_forbidden_x_roots = _x_forbidden_roots(
            resolved_settings, owned_library_repository
        )
        owned_x_staging = FilesystemXStaging(
            resolved_settings.x_acquisition_root,
            forbidden_roots=owned_forbidden_x_roots,
        )
        selected_x_extractor = (
            x_extractor
            if x_extractor is not None
            else YtDlpXExtractor(owned_x_staging)
        )
        owned_x_acquisition_coordinator = XAcquisitionCoordinator(
            owned_x_claim_repository,
            selected_x_extractor,
            owned_x_staging,
            upload_api_dependencies.transport,
            owned_upload_session_repository,
            owned_upload_publication_repository,
            validation_coordinator=owned_upload_validation_coordinator,
            publication_coordinator=owned_upload_publication_coordinator,
            chunk_size_bytes=resolved_settings.upload_max_patch_bytes,
            alias_repository=owned_media_user_alias_repository,
        )
        owned_x_admin_service = XAcquisitionAdministrationService(
            owned_x_claim_repository
        )

        def _x_request_free_space() -> int:
            assert owned_x_staging is not None
            return int(owned_x_staging.available_bytes())

        owned_x_request_service = XAcquisitionRequestService(
            owned_x_claim_repository,
            limits=XRequestLimits(
                max_active_per_requester=(
                    resolved_settings.x_request_max_active_per_user
                ),
                max_global_active=resolved_settings.x_request_max_global_active,
                max_submits_per_hour=resolved_settings.x_request_max_submits_per_hour,
                max_failed_per_24h=resolved_settings.x_request_max_failed_per_24h,
                min_free_space_reserve_bytes=(
                    resolved_settings.upload_min_free_space_reserve_bytes
                ),
                free_space_bytes=_x_request_free_space,
            ),
            alias_repository=owned_media_user_alias_repository,
            metadata_repository=owned_media_metadata_repository,
        )
    if x_request_api_dependencies is None:
        x_request_api_dependencies = XRequestApiDependencies(
            service=owned_x_request_service,
            audit_recorder=security_audit_recorder,
            enabled=(
                owned_x_request_service is not None
                and ip_address(resolved_settings.host).is_loopback
            ),
        )
    if x_admin_api_dependencies is None:
        x_admin_api_dependencies = XAdminApiDependencies(
            service=owned_x_admin_service,
            enabled=(
                owned_x_admin_service is not None
                and ip_address(resolved_settings.host).is_loopback
            ),
        )
    if x_companion_api_dependencies is None:
        x_companion_api_dependencies = XCompanionApiDependencies(
            list_media=(
                None
                if owned_media_catalog_repository is None
                else ListCompanionPickerMedia(owned_media_catalog_repository)
            ),
            catalog_available=resolved_settings.database_path.exists,
        )

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        validation_coordinator = owned_upload_validation_coordinator
        publication_coordinator = owned_upload_publication_coordinator
        catalog_coordinator = owned_upload_catalog_coordinator
        analysis_coordinator = owned_media_analysis_coordinator
        youtube_coordinator = owned_youtube_acquisition_coordinator
        x_coordinator = owned_x_acquisition_coordinator
        started: list[StartedResource] = []
        budget = (
            APPLICATION_LIFESPAN_SHUTDOWN_BUDGET_SECONDS
            if lifespan_shutdown_budget_seconds is None
            else float(lifespan_shutdown_budget_seconds)
        )
        clock = time.monotonic if shutdown_clock is None else shutdown_clock
        try:
            if analysis_coordinator is not None:
                await analysis_coordinator.start()
                started.append(
                    StartedResource("media_analysis", analysis_coordinator.shutdown)
                )
            if catalog_coordinator is not None:
                await catalog_coordinator.start()
                started.append(
                    StartedResource("upload_catalog", catalog_coordinator.shutdown)
                )
            if publication_coordinator is not None:
                await publication_coordinator.start()
                started.append(
                    StartedResource(
                        "upload_publication", publication_coordinator.shutdown
                    )
                )
            if validation_coordinator is not None:
                await validation_coordinator.start()
                started.append(
                    StartedResource(
                        "upload_validation", validation_coordinator.shutdown
                    )
                )
            if youtube_coordinator is not None:
                await youtube_coordinator.start()
                started.append(
                    StartedResource(
                        "youtube_acquisition", youtube_coordinator.shutdown
                    )
                )
            if x_coordinator is not None:
                await x_coordinator.start()
                started.append(
                    StartedResource("x_acquisition", x_coordinator.shutdown)
                )
            yield
        finally:
            deadline = create_application_shutdown_deadline(
                budget_seconds=budget,
                clock=clock,
            )
            cancelled = await shutdown_started_resources(
                started,
                deadline,
                log_fault=_log_lifecycle_shutdown_fault,
            )
            try:
                if owned_engine is not None:
                    dispose_engine(owned_engine)
            except Exception:
                _log_lifecycle_shutdown_fault(resource_name="engine")
            if cancelled is not None:
                raise cancelled

    resolved_audit_recorder = security_audit_recorder
    if tailscale_ingress_enabled:
        if resolved_audit_recorder is None:
            if owned_engine is None:
                raise ValueError(
                    "Tailscale UDS ingress requires a security audit recorder."
                )
            resolved_audit_recorder = SqliteSecurityAuditRepository(owned_engine)

    if youtube_browser_api_dependencies is None:
        youtube_browser_api_dependencies = YouTubeBrowserApiDependencies(
            service=owned_youtube_acquisition_service,
            workflow_status=(
                None
                if owned_content_publication_repository is None
                else GetMediaWorkflowStatus(owned_content_publication_repository)
            ),
            audit_recorder=resolved_audit_recorder,
            enabled=(
                owned_youtube_acquisition_service is not None
                and owned_content_publication_repository is not None
                and tailscale_ingress_enabled
            ),
        )
    if youtube_request_api_dependencies is None:
        youtube_request_api_dependencies = YouTubeRequestApiDependencies(
            service=owned_youtube_request_service,
            audit_recorder=resolved_audit_recorder,
            enabled=(
                owned_youtube_request_service is not None
                and tailscale_ingress_enabled
            ),
        )

    if tailscale_ingress_enabled:
        app = FastAPI(
            lifespan=lifespan,
            docs_url=None,
            redoc_url=None,
            openapi_url=None,
        )
    else:
        app = FastAPI(lifespan=lifespan)
    app.state.settings = resolved_settings
    app.state.upload_validation = owned_upload_validation
    app.state.upload_validation_coordinator = (
        owned_upload_validation_coordinator
        if owned_upload_validation_coordinator is not None
        else _upload_validation_coordinator(upload_api_dependencies)
    )
    app.state.upload_publication = owned_upload_publication
    app.state.upload_publication_coordinator = (
        owned_upload_publication_coordinator
        if owned_upload_publication_coordinator is not None
        else _upload_publication_coordinator(upload_api_dependencies)
    )
    app.state.upload_catalog = owned_upload_catalog
    app.state.upload_catalog_coordinator = owned_upload_catalog_coordinator
    app.state.media_analysis_coordinator = owned_media_analysis_coordinator
    app.state.youtube_acquisition_service = owned_youtube_acquisition_service
    app.state.youtube_acquisition_coordinator = (
        owned_youtube_acquisition_coordinator
    )
    app.state.youtube_acquisition_staging = owned_youtube_staging
    app.state.youtube_operator_api_dependencies = (
        youtube_operator_api_dependencies
    )
    app.state.youtube_browser_api_dependencies = youtube_browser_api_dependencies
    app.state.x_request_api_dependencies = x_request_api_dependencies
    app.state.x_admin_api_dependencies = x_admin_api_dependencies
    app.state.x_acquisition_coordinator = owned_x_acquisition_coordinator
    app.state.x_acquisition_staging = owned_x_staging
    app.include_router(create_library_api_router(library_api_dependencies))
    app.include_router(create_media_import_api_router(media_import_api_dependencies))
    app.include_router(create_media_catalog_api_router(media_catalog_api_dependencies))
    app.include_router(create_media_metadata_api_router(media_metadata_api_dependencies))
    app.include_router(create_media_alias_api_router(media_alias_api_dependencies))
    app.include_router(create_media_analysis_api_router(media_analysis_api_dependencies))
    app.include_router(create_media_content_api_router(media_content_api_dependencies))
    app.include_router(create_gallery_preview_api_router(gallery_preview_api_dependencies))
    app.include_router(create_media_suggestion_api_router(media_suggestion_api_dependencies))
    app.include_router(
        create_media_analysis_lifecycle_api_router(
            media_analysis_lifecycle_api_dependencies
        )
    )
    app.include_router(
        create_content_publication_api_router(
            content_publication_api_dependencies
        )
    )
    if catalog_removal_api_dependencies is not None:
        app.include_router(
            create_catalog_removal_api_router(catalog_removal_api_dependencies)
        )
    app.include_router(create_cover_api_router(cover_api_dependencies))
    app.include_router(create_upload_api_router(upload_api_dependencies))
    app.include_router(
        create_youtube_operator_api_router(youtube_operator_api_dependencies)
    )
    app.include_router(
        create_youtube_browser_api_router(youtube_browser_api_dependencies)
    )
    app.include_router(
        create_youtube_request_api_router(youtube_request_api_dependencies)
    )
    app.include_router(create_x_request_api_router(x_request_api_dependencies))
    app.include_router(create_x_admin_api_router(x_admin_api_dependencies))
    app.include_router(create_x_companion_api_router(x_companion_api_dependencies))
    if tailscale_ingress_enabled:
        assert identity_mapping is not None
        app.add_middleware(
            TailscaleIngressMiddleware,
            identity_mapping=identity_mapping,
            external_origin=resolved_settings.external_origin,
            audit_recorder=resolved_audit_recorder,
            companion_extension_origins=tuple(
                resolved_settings.companion_extension_origins
            ),
        )

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
        if tailscale_ingress_enabled:
            return CloudStatusResponse(
                server="connected",
                connection="tailscale",
                remote_access=resolved_settings.external_origin,
            )
        return CloudStatusResponse(server="connected", connection="loopback", remote_access=None)

    if tailscale_ingress_enabled:

        @app.get("/api/identity/me", response_model=IdentityMeResponse)
        def identity_me(request: Request) -> IdentityMeResponse:
            identity = request.scope.get(SCOPE_IDENTITY)
            if not isinstance(identity, IdentityContext):
                raise HTTPException(status_code=401, detail="Not authenticated")
            return IdentityMeResponse(
                login=identity.login,
                display_name=identity.display_name,
                role=identity.role,
                capabilities=sorted(identity.capabilities),
                provenance=identity.provenance,
            )

    return app


def _log_lifecycle_shutdown_fault(*, resource_name: str) -> None:
    del resource_name
    try:
        LOGGER.emit(
            level="WARNING",
            event="lifecycle_resource_shutdown_fault",
            operation="lifecycle_shutdown",
            error_code="LIFECYCLE_RESOURCE_SHUTDOWN_FAULT",
            retryable=False,
        )
    except Exception:
        return


def _upload_validation_coordinator(dependencies: UploadApiDependencies) -> object | None:
    return dependencies.validation_coordinator


def _upload_publication_coordinator(
    dependencies: UploadApiDependencies,
) -> object | None:
    return dependencies.publication_coordinator


def _resolve_cover_storage(
    settings: FrameNestSettings,
    library_repository: SqliteLibraryRepository,
) -> tuple[FilesystemDurableCoverStorage, FilesystemCoverThumbnailCache]:
    """Resolve durable cover storage and thumbnail cache with library disjointness."""
    try:
        storage = FilesystemDurableCoverStorage(settings.cover_storage_root)
        thumbnail = FilesystemCoverThumbnailCache(settings.cover_thumbnail_cache_path)
        if _cover_paths_overlap(storage.root, thumbnail.root):
            raise ValueError("Cover storage configuration is invalid.")
        library_roots: list[Path] = []
        if settings.database_path.exists():
            try:
                library_roots = [
                    Path(library.root.path)
                    for library in library_repository.list_all()
                    if library.root.flavor is LibraryPathFlavor.POSIX
                ]
            except Exception:
                # An absent or unmigrated catalog has no registered libraries to
                # conflict with; runtime publish paths always serve a migrated DB.
                library_roots = []
        _require_cover_root_disjoint(storage.root, library_roots)
        _require_cover_root_disjoint(thumbnail.root, library_roots)
    except ValueError:
        raise
    except Exception as exc:
        raise ValueError("Cover storage configuration is invalid.") from exc
    return storage, thumbnail


def _require_cover_root_disjoint(root: Path, others: list[Path]) -> None:
    for other in others:
        if _cover_paths_overlap(root, other):
            raise ValueError("Cover storage configuration is invalid.")


def _cover_paths_overlap(first: Path, second: Path) -> bool:
    return first == second or first in second.parents or second in first.parents


def _resolve_published_storage(
    settings: FrameNestSettings,
    library_repository: SqliteLibraryRepository,
    *,
    quarantine_configured: bool,
) -> FilesystemPublishedMediaStorage | None:
    destination_text = settings.upload_publication_library_id
    if destination_text is None:
        return None
    if not quarantine_configured or settings.upload_quarantine_root is None:
        raise ValueError("Upload publication configuration is invalid.")
    try:
        destination_id = LibraryId.from_string(destination_text)
        destination = library_repository.get(destination_id)
        libraries = library_repository.list_all()
    except Exception:
        raise ValueError("Upload publication configuration is invalid.") from None
    if destination is None or destination.root.flavor is not LibraryPathFlavor.POSIX:
        raise ValueError("Upload publication configuration is invalid.")
    forbidden_roots = [
        settings.upload_quarantine_root,
        settings.gallery_preview_cache_path,
        settings.database_path.parent,
    ]
    if settings.youtube_acquisition_root is not None:
        forbidden_roots.append(settings.youtube_acquisition_root)
    forbidden_roots.extend(
        Path(library.root.path)
        for library in libraries
        if library.id != destination_id
        and library.root.flavor is LibraryPathFlavor.POSIX
    )
    storage = FilesystemPublishedMediaStorage(
        destination_id,
        Path(destination.root.path),
        forbidden_roots=tuple(forbidden_roots),
        min_free_space_reserve_bytes=settings.upload_min_free_space_reserve_bytes,
    )
    if not storage.root_available:
        raise ValueError("Upload publication configuration is invalid.")
    return storage


def _resolve_youtube_staging(
    settings: FrameNestSettings,
    library_repository: SqliteLibraryRepository,
) -> FilesystemYouTubeStaging | None:
    root = settings.youtube_acquisition_root
    if root is None:
        return None
    forbidden_roots = [
        settings.gallery_preview_cache_path,
        settings.database_path,
    ]
    if settings.upload_quarantine_root is not None:
        forbidden_roots.append(settings.upload_quarantine_root)
    try:
        forbidden_roots.extend(
            Path(library.root.path)
            for library in library_repository.list_all()
            if library.root.flavor is LibraryPathFlavor.POSIX
        )
        staging = FilesystemYouTubeStaging(
            root,
            forbidden_roots=tuple(forbidden_roots),
        )
    except Exception:
        raise ValueError("YouTube acquisition configuration is invalid.") from None
    if not staging.root_available:
        raise ValueError("YouTube acquisition configuration is invalid.")
    return staging


def _x_forbidden_roots(
    settings: FrameNestSettings,
    library_repository: SqliteLibraryRepository,
) -> tuple[Path, ...]:
    if settings.x_acquisition_root is None:
        return ()
    forbidden_roots = [
        settings.gallery_preview_cache_path,
        settings.database_path,
    ]
    if settings.upload_quarantine_root is not None:
        forbidden_roots.append(settings.upload_quarantine_root)
    if settings.youtube_acquisition_root is not None:
        forbidden_roots.append(settings.youtube_acquisition_root)
    try:
        forbidden_roots.extend(
            Path(library.root.path)
            for library in library_repository.list_all()
            if library.root.flavor is LibraryPathFlavor.POSIX
        )
    except Exception:
        forbidden_roots = forbidden_roots
    return tuple(forbidden_roots)


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
