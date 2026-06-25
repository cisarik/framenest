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
from framenest.adapters.api.media_suggestion_api import (
    MediaSuggestionApiDependencies,
    create_media_suggestion_api_router,
)
from framenest.application.library_scan import PreviewLibraryScan
from framenest.application.media_analysis import PrepareLocalMediaAnalysis
from framenest.application.media_suggestion import PreviewMediaSuggestion
from framenest.adapters.api.library_api import (
    LibraryApiDependencies,
    create_library_api_router,
)
import framenest.adapters.api.web as web_resources
from framenest.configuration import FrameNestSettings, load_settings
from framenest.infrastructure.ai import NvidiaNimMediaSuggestionProvider
from framenest.infrastructure.ai.credentials import load_nvidia_api_credential
from framenest.infrastructure.filesystem.library_scanner import LocalLibraryScanner
from framenest.infrastructure.media_analysis import LocalMediaAnalysisAdapter
from framenest.infrastructure.persistence.engine import create_sqlite_engine, dispose_engine
from framenest.infrastructure.persistence.library_repository import SqliteLibraryRepository


class HealthResponse(BaseModel):
    status: Literal["ok"]


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
    media_analysis_api_dependencies: MediaAnalysisApiDependencies | None = None,
    media_suggestion_api_dependencies: MediaSuggestionApiDependencies | None = None,
) -> FastAPI:
    resolved_settings = settings if settings is not None else load_settings()
    owned_engine = None
    owned_library_repository = None
    if (
        library_api_dependencies is None
        or media_analysis_api_dependencies is None
        or media_suggestion_api_dependencies is None
    ):
        owned_engine = create_sqlite_engine(resolved_settings.database_path)
        owned_library_repository = SqliteLibraryRepository(owned_engine)
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
    if media_analysis_api_dependencies is None:
        assert owned_library_repository is not None
        media_analysis_api_dependencies = MediaAnalysisApiDependencies(
            prepare_preview=PrepareLocalMediaAnalysis(
                owned_library_repository,
                LocalMediaAnalysisAdapter(),
            ),
            catalog_available=resolved_settings.database_path.exists,
        )
    if media_suggestion_api_dependencies is None:
        assert owned_library_repository is not None
        credential = load_nvidia_api_credential()
        suggestion_preview = None
        if credential is not None:
            suggestion_preview = PreviewMediaSuggestion(
                owned_library_repository,
                LocalMediaAnalysisAdapter(),
                NvidiaNimMediaSuggestionProvider(credential),
            )
        media_suggestion_api_dependencies = MediaSuggestionApiDependencies(
            preview_suggestion=suggestion_preview,
            provider_configured=suggestion_preview is not None,
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
    app.include_router(create_library_api_router(library_api_dependencies))
    app.include_router(create_media_analysis_api_router(media_analysis_api_dependencies))
    app.include_router(create_media_suggestion_api_router(media_suggestion_api_dependencies))

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

    return app
