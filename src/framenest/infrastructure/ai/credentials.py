"""Server-side AI credential wrappers."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
import stat

CREDENTIAL_MISSING_MESSAGE = "NVIDIA API credential is not available."
VERCEL_CREDENTIAL_MISSING_MESSAGE = "Vercel AI Gateway credential is not available."
NVIDIA_API_KEY_ENVIRONMENT_NAME = "NVIDIA_API_KEY"
VERCEL_AI_GATEWAY_API_KEY_ENVIRONMENT_NAME = "AI_GATEWAY_API_KEY"
CREDENTIALS_DIRECTORY_ENVIRONMENT_NAME = "CREDENTIALS_DIRECTORY"
AI_CREDENTIAL_MAX_BYTES = 4096


@dataclass(frozen=True, slots=True)
class NvidiaApiCredential:
    """Bearer credential read at a controlled CLI or server composition boundary."""

    _secret: str

    def __post_init__(self) -> None:
        if not isinstance(self._secret, str) or not self._secret.strip():
            raise ValueError(CREDENTIAL_MISSING_MESSAGE)

    def __repr__(self) -> str:
        return "NvidiaApiCredential(<redacted>)"

    def authorization_header(self) -> str:
        return f"Bearer {self._secret.strip()}"


@dataclass(frozen=True, slots=True)
class VercelAiGatewayCredential:
    """Bearer credential read at a controlled server composition boundary."""

    _secret: str

    def __post_init__(self) -> None:
        if not isinstance(self._secret, str) or not self._secret.strip():
            raise ValueError(VERCEL_CREDENTIAL_MISSING_MESSAGE)

    def __repr__(self) -> str:
        return "VercelAiGatewayCredential(<redacted>)"

    def authorization_header(self) -> str:
        return f"Bearer {self._secret.strip()}"


def load_nvidia_api_credential(
    environ: Mapping[str, str] | None = None,
) -> NvidiaApiCredential | None:
    """Load the NVIDIA credential from environment or systemd credentials."""
    source = os.environ if environ is None else environ
    value = _load_credential_value(NVIDIA_API_KEY_ENVIRONMENT_NAME, source)
    if value is None:
        return None
    return NvidiaApiCredential(value)


def load_vercel_ai_gateway_credential(
    environ: Mapping[str, str] | None = None,
) -> VercelAiGatewayCredential | None:
    """Load the Vercel AI Gateway credential from environment or systemd credentials."""
    source = os.environ if environ is None else environ
    value = _load_credential_value(VERCEL_AI_GATEWAY_API_KEY_ENVIRONMENT_NAME, source)
    if value is None:
        return None
    return VercelAiGatewayCredential(value)


def _load_credential_value(name: str, environ: Mapping[str, str]) -> str | None:
    environment_value = environ.get(name)
    if environment_value is not None:
        return _sanitize_credential_text(environment_value)
    credentials_directory = environ.get(CREDENTIALS_DIRECTORY_ENVIRONMENT_NAME)
    if credentials_directory is None or not credentials_directory.strip():
        return None
    return _read_systemd_credential(Path(credentials_directory) / name)


def _read_systemd_credential(path: Path) -> str | None:
    try:
        metadata = path.lstat()
    except OSError:
        return None
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
        return None
    if metadata.st_size < 1 or metadata.st_size > AI_CREDENTIAL_MAX_BYTES:
        return None
    try:
        payload = path.read_bytes()
    except OSError:
        return None
    if len(payload) > AI_CREDENTIAL_MAX_BYTES:
        return None
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError:
        return None
    return _sanitize_credential_text(text)


def _sanitize_credential_text(value: str) -> str | None:
    if "\x00" in value:
        return None
    if value.endswith("\r\n"):
        value = value[:-2]
    elif value.endswith("\n"):
        value = value[:-1]
    if "\n" in value or "\r" in value:
        return None
    value = value.strip()
    if not value:
        return None
    if len(value.encode("utf-8")) > AI_CREDENTIAL_MAX_BYTES:
        return None
    return value
