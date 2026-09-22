"""Typed client for the loopback ask bridge."""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from kronika import paths
from kronika.config import (
    DEFAULT_ASK_TIMEOUT_S,
    DEFAULT_BRIDGE_HOST,
    DEFAULT_BRIDGE_PORT,
    NEXT_WAIT_DEFAULT_S,
)


class BridgeUnreachable(Exception):
    """The bridge is not listening on the configured loopback address."""


class BridgeNoToken(Exception):
    """No per-install token exists in the state directory yet."""


class BridgeError(Exception):
    """The bridge answered with an error envelope."""

    def __init__(self, code: str, step: str, message: str, status: int = 0) -> None:
        super().__init__(message)
        self.code = code
        self.step = step
        self.message = message
        self.status = status


def configured_port(state_dir: Path | str | None = None) -> int | None:
    """Return the port the bridge last listened on, if state records one."""

    try:
        payload = json.loads(paths.config_path(state_dir).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    port = payload.get("port") if isinstance(payload, dict) else None
    if isinstance(port, int) and not isinstance(port, bool) and 1 <= port <= 65535:
        return port
    return None


class BridgeClient:
    def __init__(
        self,
        host: str = DEFAULT_BRIDGE_HOST,
        port: int | None = None,
        token: str | None = None,
        timeout: float = 30.0,
        state_dir: Path | str | None = None,
    ) -> None:
        self.state_dir = paths.state_dir(state_dir)
        if port is None:
            port = configured_port(self.state_dir) or DEFAULT_BRIDGE_PORT
        self.host = host
        self.port = port
        self.base_url = f"http://{host}:{port}"
        self.timeout = timeout
        self.token = token if token is not None else self._read_token()

    def _read_token(self) -> str | None:
        try:
            token = paths.token_path(self.state_dir).read_text(encoding="utf-8").strip()
        except OSError:
            return None
        return token or None

    def _request(
        self,
        method: str,
        path: str,
        body: dict | None = None,
        params: dict | None = None,
        *,
        auth_required: bool = True,
        timeout: float | None = None,
    ) -> tuple[int, dict]:
        if auth_required and not self.token:
            raise BridgeNoToken("no bridge token in the state directory")
        url = self.base_url + path
        if params:
            url = f"{url}?{urllib.parse.urlencode(params)}"
        data = None
        if body is not None:
            data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        request = urllib.request.Request(url, data=data, method=method)
        request.add_header("Accept", "application/json")
        if data is not None:
            request.add_header("Content-Type", "application/json")
        if auth_required and self.token:
            request.add_header("X-Bridge-Token", self.token)
        try:
            with urllib.request.urlopen(
                request, timeout=timeout if timeout is not None else self.timeout
            ) as response:
                raw = response.read()
                status = response.status
        except urllib.error.HTTPError as exc:
            raw = exc.read()
            payload = self._decode(raw)
            if isinstance(payload, dict) and isinstance(payload.get("error"), dict):
                error = payload["error"]
                raise BridgeError(
                    str(error.get("code") or "E_INTERNAL"),
                    str(error.get("step") or "bridge"),
                    str(error.get("message") or ""),
                    exc.code,
                ) from exc
            raise BridgeError("E_INTERNAL", "bridge", f"HTTP {exc.code}", exc.code) from exc
        except (urllib.error.URLError, TimeoutError, ConnectionError, OSError) as exc:
            raise BridgeUnreachable(str(exc)) from exc
        return status, (self._decode(raw) or {})

    @staticmethod
    def _decode(raw: bytes) -> dict | None:
        if not raw:
            return None
        try:
            payload = json.loads(raw.decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            return None
        return payload if isinstance(payload, dict) else None

    def status(self) -> dict:
        _, payload = self._request("GET", "/v1/status")
        return payload

    def hello(self, payload: dict) -> dict:
        _, body = self._request("POST", "/v1/hello", body=payload)
        return body

    def create_job(
        self,
        prompt: str,
        *,
        new_chat: bool = True,
        timeout_s: int = DEFAULT_ASK_TIMEOUT_S,
        project: str | None = None,
    ) -> str:
        body: dict = {
            "prompt": prompt,
            "files": [],
            "new_chat": new_chat,
            "timeout_s": timeout_s,
        }
        if project is not None:
            body["project"] = project
        _, payload = self._request("POST", "/v1/jobs", body=body)
        return str(payload.get("job_id") or "")

    def get_job(self, job_id: str, since: int = 0) -> dict:
        _, payload = self._request("GET", f"/v1/jobs/{job_id}", params={"since": since})
        return payload

    def cancel(self, job_id: str) -> dict:
        _, payload = self._request("POST", f"/v1/jobs/{job_id}/cancel", body={})
        return payload
