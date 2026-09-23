"""Per-install token lifecycle and loopback Host, Origin, and token checks."""

from __future__ import annotations

import hmac
import os
import secrets
import tempfile
from dataclasses import dataclass
from pathlib import Path

TOKEN_BYTES = 32


@dataclass(frozen=True)
class AuthResult:
    ok: bool
    status: int = 200
    code: str | None = None
    message: str = ""
    allow_origin: str | None = None


def _write_token(path: Path, token: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    os.chmod(path.parent, 0o700)
    descriptor, tmp_name = tempfile.mkstemp(dir=str(path.parent), prefix=".token-")
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(token + "\n")
        os.replace(tmp_name, path)
    except BaseException:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise
    os.chmod(path, 0o600)


def load_or_create_token(path: Path | str) -> str:
    token_path = Path(path)
    try:
        existing = token_path.read_text(encoding="utf-8").strip()
    except OSError:
        existing = ""
    if existing:
        return existing
    return rotate_token(token_path)


def rotate_token(path: Path | str) -> str:
    token_path = Path(path)
    token = secrets.token_urlsafe(TOKEN_BYTES)
    _write_token(token_path, token)
    return token


def _header(headers, name: str) -> str | None:
    getter = getattr(headers, "get", None)
    if getter is None:
        return None
    value = getter(name)
    if value is not None:
        return value
    lowered = name.lower()
    for key, item in headers.items():
        if str(key).lower() == lowered:
            return item
    return None


def check_request(
    headers,
    host_header: str | None,
    token: str | None,
    *,
    port: int,
    origin: str | None = None,
    exempt_token: bool = False,
) -> AuthResult:
    """Require Host ``127.0.0.1:<port>``, an absent or exact loopback Origin, and the token.

    A ``chrome-extension://`` origin is rejected. Manager and render secrets
    are not accepted on this surface.
    """

    expected_host = f"127.0.0.1:{port}"
    if host_header is None or host_header.strip() == "":
        return AuthResult(False, 403, "E_INTERNAL", "missing Host header")
    if host_header.strip().lower() != expected_host.lower():
        return AuthResult(False, 403, "E_INTERNAL", "forbidden Host header")

    allow_origin = None
    if origin is not None and origin != "":
        allowed = f"http://{expected_host}"
        if origin != allowed:
            return AuthResult(False, 403, "E_INTERNAL", "forbidden Origin")
        allow_origin = origin

    if not exempt_token:
        presented = _header(headers, "X-Bridge-Token") or ""
        expected = token or ""
        if not expected or not hmac.compare_digest(str(presented), expected):
            return AuthResult(False, 401, "E_INTERNAL", "missing or invalid token")

    return AuthResult(True, 200, allow_origin=allow_origin)
