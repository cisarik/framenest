"""FastAPI application factory for the FrameNest presentation adapter."""

from __future__ import annotations

from typing import Literal

from fastapi import FastAPI
from pydantic import BaseModel

from framenest.configuration import FrameNestSettings, load_settings


class HealthResponse(BaseModel):
    status: Literal["ok"]


def create_app(
    settings: FrameNestSettings | None = None,
) -> FastAPI:
    resolved_settings = settings if settings is not None else load_settings()
    app = FastAPI()
    app.state.settings = resolved_settings

    @app.get("/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        return HealthResponse(status="ok")

    return app
