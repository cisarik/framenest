"""Uvicorn ASGI runtime composition for FrameNest."""

from __future__ import annotations

import uvicorn

from framenest.adapters.api.application import create_app
from framenest.configuration import FrameNestSettings, load_settings
from framenest.structured_logging import build_uvicorn_log_config


def create_server(
    settings: FrameNestSettings | None = None,
) -> uvicorn.Server:
    resolved_settings = settings if settings is not None else load_settings()
    config = uvicorn.Config(
        app=create_app(settings=resolved_settings),
        host=resolved_settings.host,
        port=resolved_settings.port,
        reload=False,
        workers=1,
        proxy_headers=False,
        forwarded_allow_ips="",
        access_log=False,
        log_config=build_uvicorn_log_config(),
    )
    return uvicorn.Server(config)


def run_server(
    settings: FrameNestSettings | None = None,
) -> None:
    server = create_server(settings=settings)
    server.run()


def main() -> None:
    run_server()


if __name__ == "__main__":
    main()
