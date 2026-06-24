"""Temporary NVIDIA API credential wrapper for the prototype adapter."""

from __future__ import annotations

from dataclasses import dataclass

CREDENTIAL_MISSING_MESSAGE = "NVIDIA API credential is not available."


@dataclass(frozen=True, slots=True)
class NvidiaApiCredential:
    """Bearer credential read at the CLI composition boundary only."""

    _secret: str

    def __post_init__(self) -> None:
        if not isinstance(self._secret, str) or not self._secret.strip():
            raise ValueError(CREDENTIAL_MISSING_MESSAGE)

    def __repr__(self) -> str:
        return "NvidiaApiCredential(<redacted>)"

    def authorization_header(self) -> str:
        return f"Bearer {self._secret.strip()}"
