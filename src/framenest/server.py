"""Uvicorn ASGI runtime composition for FrameNest."""

from __future__ import annotations

import sys

import uvicorn

from framenest.adapters.api.application import create_app
from framenest.configuration import (
    INGRESS_MODE_TAILSCALE_UDS,
    FrameNestConfigurationError,
    FrameNestSettings,
    load_settings,
)
from framenest.structured_logging import build_uvicorn_log_config


def create_server(
    settings: FrameNestSettings | None = None,
) -> uvicorn.Server:
    resolved_settings = settings if settings is not None else load_settings()
    config_kwargs: dict[str, object] = {}
    if resolved_settings.ingress_mode == INGRESS_MODE_TAILSCALE_UDS:
        assert resolved_settings.uds_path is not None
        config_kwargs["uds"] = str(resolved_settings.uds_path)
    else:
        config_kwargs["host"] = resolved_settings.host
        config_kwargs["port"] = resolved_settings.port
    config = uvicorn.Config(
        app=create_app(settings=resolved_settings),
        reload=False,
        workers=1,
        proxy_headers=False,
        forwarded_allow_ips="",
        access_log=False,
        log_config=build_uvicorn_log_config(),
        **config_kwargs,
    )
    return uvicorn.Server(config)


def run_server(
    settings: FrameNestSettings | None = None,
) -> None:
    server = create_server(settings=settings)
    server.run()


def main() -> None:
    try:
        run_server()
    except KeyboardInterrupt:
        return
    except FrameNestConfigurationError as exc:
        print(f"FrameNest configuration error: {exc}", file=sys.stderr)
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
