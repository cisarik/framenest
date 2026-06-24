"""Contract tests for the live Uvicorn loopback runtime."""

from __future__ import annotations

import json
import os
import socket
import subprocess
import threading
import time
import urllib.error
import urllib.request
from typing import Any

import pytest
from pydantic import SecretStr

from framenest.configuration import FrameNestSettings
from framenest.server import create_server

REPRESENTATIVE_SECRET = "contract-runtime-api-key-secret"
STARTUP_TIMEOUT_SECONDS = 5.0
SHUTDOWN_TIMEOUT_SECONDS = 5.0


def _find_free_loopback_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _wait_until_port_listening(host: str, port: int, timeout: float) -> None:
    deadline = time.monotonic() + timeout
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        try:
            with socket.create_connection((host, port), timeout=0.2):
                return
        except OSError as exc:
            last_error = exc
            time.sleep(0.05)
    raise TimeoutError(f"Timed out waiting for {host}:{port} to accept connections") from last_error


def _wait_until_port_closed(host: str, port: int, timeout: float) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with socket.create_connection((host, port), timeout=0.2):
                time.sleep(0.05)
        except OSError:
            return
    raise TimeoutError(f"Timed out waiting for {host}:{port} to close")


def _http_get_json(url: str) -> tuple[int, dict[str, Any]]:
    with urllib.request.urlopen(url, timeout=2.0) as response:
        status = response.status
        body = json.loads(response.read().decode("utf-8"))
        return status, body


def _child_pids() -> set[int]:
    if os.name != "posix":
        return set()
    result = subprocess.run(
        ["pgrep", "-P", str(os.getpid())],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return set()
    return {int(pid) for pid in result.stdout.splitlines() if pid.strip()}


def test_live_loopback_runtime_health_shutdown_and_cleanup(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("UVICORN_HOST", raising=False)
    monkeypatch.delenv("UVICORN_PORT", raising=False)
    monkeypatch.delenv("FORWARDED_ALLOW_IPS", raising=False)

    settings = FrameNestSettings(
        host="127.0.0.1",
        port=0,
        api_key=SecretStr(REPRESENTATIVE_SECRET),
        _env_file=None,
    )
    server = create_server(settings=settings)
    assert server.config.host == "127.0.0.1"
    assert server.config.host not in {"0.0.0.0", "::"}

    runtime_thread: threading.Thread | None = None
    bound_port: int | None = None
    baseline_children = _child_pids()

    try:
        runtime_thread = threading.Thread(target=server.run, name="uvicorn-runtime-contract")
        runtime_thread.start()

        deadline = time.monotonic() + STARTUP_TIMEOUT_SECONDS
        while time.monotonic() < deadline:
            if server.started and server.servers:
                sockets = server.servers[0].sockets
                if sockets:
                    bound_port = int(sockets[0].getsockname()[1])
                    break
            time.sleep(0.05)
        if bound_port is None:
            raise TimeoutError("Timed out waiting for Uvicorn to bind an ephemeral loopback port")

        _wait_until_port_listening("127.0.0.1", bound_port, STARTUP_TIMEOUT_SECONDS)

        status, body = _http_get_json(f"http://127.0.0.1:{bound_port}/health")
        assert status == 200
        assert body == {"status": "ok"}

        server.should_exit = True
        runtime_thread.join(timeout=SHUTDOWN_TIMEOUT_SECONDS)
        assert not runtime_thread.is_alive()

        _wait_until_port_closed("127.0.0.1", bound_port, SHUTDOWN_TIMEOUT_SECONDS)
        assert _child_pids() - baseline_children == set()
    finally:
        server.should_exit = True
        if runtime_thread is not None and runtime_thread.is_alive():
            runtime_thread.join(timeout=SHUTDOWN_TIMEOUT_SECONDS)
        if bound_port is not None:
            try:
                _wait_until_port_closed("127.0.0.1", bound_port, SHUTDOWN_TIMEOUT_SECONDS)
            except TimeoutError:
                pytest.fail("Listener remained open after contract test cleanup")
