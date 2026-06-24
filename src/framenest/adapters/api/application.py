"""FastAPI application factory for the FrameNest presentation adapter."""

from __future__ import annotations

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from importlib import resources
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, Response
from pydantic import BaseModel

from framenest.application.library_scan import PreviewLibraryScan
from framenest.adapters.api.library_api import (
    LibraryApiDependencies,
    create_library_api_router,
)
import framenest.adapters.api.web as web_resources
from framenest.configuration import FrameNestSettings, load_settings
from framenest.infrastructure.filesystem.library_scanner import LocalLibraryScanner
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
) -> FastAPI:
    resolved_settings = settings if settings is not None else load_settings()
    owned_engine = None
    if library_api_dependencies is None:
        owned_engine = create_sqlite_engine(resolved_settings.database_path)
        library_repository = SqliteLibraryRepository(owned_engine)
        library_api_dependencies = LibraryApiDependencies(
            repository=library_repository,
            scan_preview=PreviewLibraryScan(
                library_repository,
                LocalLibraryScanner(),
            ),
            catalog_available=resolved_settings.database_path.exists,
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
