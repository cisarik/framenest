"""Application port for bounded upload media validation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from framenest.application.ports.quarantine_storage import QuarantineReader
from framenest.domain.uploads import UploadValidatedFormat, UploadValidatedMediaKind


@dataclass(frozen=True, slots=True)
class UploadMediaValidationEvidence:
    """Normalized media validation evidence safe for durable persistence."""

    media_kind: UploadValidatedMediaKind
    media_format: UploadValidatedFormat


class UploadMediaValidationRejectedError(ValueError):
    """Raised for permanent content or validation-policy rejection."""

    def __init__(self, failure_code: str) -> None:
        super().__init__("upload media validation rejected")
        self.failure_code = failure_code


class UploadMediaValidationInfrastructureError(RuntimeError):
    """Raised for infrastructure or quarantine-consistency validation failure."""

    def __init__(self, failure_code: str) -> None:
        super().__init__("upload media validation failed")
        self.failure_code = failure_code


class UploadMediaValidator(Protocol):
    """Validate content from one stable quarantine object."""

    def validate(self, reader: QuarantineReader) -> UploadMediaValidationEvidence:
        """Return normalized media evidence or raise a sanitized validation error."""
