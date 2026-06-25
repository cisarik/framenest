"""Temporary NVIDIA API credential wrapper for the prototype adapter."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass

CREDENTIAL_MISSING_MESSAGE = "NVIDIA API credential is not available."
NVIDIA_API_KEY_ENVIRONMENT_NAME = "NVIDIA_API_KEY"


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


def load_nvidia_api_credential(
    environ: Mapping[str, str] | None = None,
) -> NvidiaApiCredential | None:
    """Load the temporary NVIDIA credential from one controlled mapping."""
    source = os.environ if environ is None else environ
    value = source.get(NVIDIA_API_KEY_ENVIRONMENT_NAME)
    if value is None or not value.strip():
        return None
    return NvidiaApiCredential(value)
