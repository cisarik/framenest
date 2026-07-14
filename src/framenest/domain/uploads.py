"""Pure-domain upload-session state and invariants."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import PurePosixPath, PureWindowsPath
import re
import uuid

INVALID_UPLOAD_SESSION_MESSAGE = "Invalid FrameNest upload session."
INVALID_UPLOAD_TRANSITION_MESSAGE = "Invalid upload session transition."
INCOMPLETE_UPLOAD_SESSION_MESSAGE = "Incomplete upload session."
INVALID_UPLOAD_OFFSET_MESSAGE = "Invalid upload offset."
INVALID_UPLOAD_CHECKSUM_MESSAGE = "Invalid upload checksum."

_SHA256_HEX_PATTERN = re.compile(r"[0-9a-f]{64}")
_STORAGE_KEY_PATTERN = re.compile(r"[a-z0-9][a-z0-9._-]{15,127}")
_FAILURE_CODE_PATTERN = re.compile(r"[A-Z0-9_]{1,80}")


class FrameNestUploadSessionError(ValueError):
    """Sanitized error raised when upload-session construction is invalid."""


class FrameNestUploadSessionTransitionError(FrameNestUploadSessionError):
    """Sanitized error raised when an upload-session transition is invalid."""


class FrameNestIncompleteUploadSessionError(FrameNestUploadSessionTransitionError):
    """Sanitized error raised when a state requires complete received bytes."""


class FrameNestUploadOffsetError(FrameNestUploadSessionError):
    """Sanitized error raised when upload offset arithmetic is invalid."""


class FrameNestUploadChecksumError(FrameNestUploadSessionError):
    """Sanitized error raised when upload checksum metadata is invalid."""


class UploadSessionState(StrEnum):
    """Canonical durable upload-session states."""

    CREATED = "created"
    RECEIVING = "receiving"
    RECEIVED = "received"
    VALIDATING = "validating"
    DUPLICATE_PENDING = "duplicate_pending"
    PUBLISH_PENDING = "publish_pending"
    PUBLISHED = "published"
    CATALOGED = "cataloged"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    FAILED = "failed"


TERMINAL_UPLOAD_SESSION_STATES = frozenset(
    {
        UploadSessionState.CATALOGED,
        UploadSessionState.REJECTED,
        UploadSessionState.CANCELLED,
        UploadSessionState.EXPIRED,
        UploadSessionState.FAILED,
    }
)

COMPLETE_UPLOAD_SESSION_STATES = frozenset(
    {
        UploadSessionState.RECEIVED,
        UploadSessionState.VALIDATING,
        UploadSessionState.DUPLICATE_PENDING,
        UploadSessionState.PUBLISH_PENDING,
        UploadSessionState.PUBLISHED,
        UploadSessionState.CATALOGED,
        UploadSessionState.REJECTED,
    }
)

PARTIAL_OR_COMPLETE_UPLOAD_SESSION_STATES = frozenset(
    {
        UploadSessionState.RECEIVING,
        UploadSessionState.CANCELLED,
        UploadSessionState.EXPIRED,
        UploadSessionState.FAILED,
    }
)

ALLOWED_UPLOAD_SESSION_TRANSITIONS = {
    UploadSessionState.CREATED: frozenset(
        {
            UploadSessionState.RECEIVING,
            UploadSessionState.CANCELLED,
            UploadSessionState.EXPIRED,
            UploadSessionState.FAILED,
        }
    ),
    UploadSessionState.RECEIVING: frozenset(
        {
            UploadSessionState.RECEIVED,
            UploadSessionState.CANCELLED,
            UploadSessionState.EXPIRED,
            UploadSessionState.FAILED,
        }
    ),
    UploadSessionState.RECEIVED: frozenset(
        {
            UploadSessionState.VALIDATING,
            UploadSessionState.CANCELLED,
            UploadSessionState.EXPIRED,
            UploadSessionState.FAILED,
        }
    ),
    UploadSessionState.VALIDATING: frozenset(
        {
            UploadSessionState.DUPLICATE_PENDING,
            UploadSessionState.PUBLISH_PENDING,
            UploadSessionState.REJECTED,
            UploadSessionState.FAILED,
        }
    ),
    UploadSessionState.DUPLICATE_PENDING: frozenset(
        {
            UploadSessionState.PUBLISH_PENDING,
            UploadSessionState.CANCELLED,
            UploadSessionState.EXPIRED,
            UploadSessionState.FAILED,
        }
    ),
    UploadSessionState.PUBLISH_PENDING: frozenset(
        {
            UploadSessionState.PUBLISHED,
            UploadSessionState.FAILED,
        }
    ),
    UploadSessionState.PUBLISHED: frozenset({UploadSessionState.CATALOGED}),
    UploadSessionState.CATALOGED: frozenset(),
    UploadSessionState.REJECTED: frozenset(),
    UploadSessionState.CANCELLED: frozenset(),
    UploadSessionState.EXPIRED: frozenset(),
    UploadSessionState.FAILED: frozenset(),
}


@dataclass(frozen=True, slots=True, repr=False)
class UploadSessionId:
    """Stable opaque UUIDv4 identity for one upload session."""

    value: uuid.UUID

    def __post_init__(self) -> None:
        if not isinstance(self.value, uuid.UUID):
            raise FrameNestUploadSessionError(INVALID_UPLOAD_SESSION_MESSAGE)
        if self.value.variant != uuid.RFC_4122 or self.value.version != 4:
            raise FrameNestUploadSessionError(INVALID_UPLOAD_SESSION_MESSAGE)

    @classmethod
    def new(cls) -> "UploadSessionId":
        """Generate a new application-owned upload-session identity."""
        return cls(uuid.uuid4())

    @classmethod
    def from_string(cls, value: str) -> "UploadSessionId":
        """Parse a canonical lowercase hyphenated UUIDv4 string."""
        if not isinstance(value, str):
            raise FrameNestUploadSessionError(INVALID_UPLOAD_SESSION_MESSAGE)
        try:
            parsed = uuid.UUID(value)
        except (AttributeError, TypeError, ValueError):
            raise FrameNestUploadSessionError(INVALID_UPLOAD_SESSION_MESSAGE) from None
        if str(parsed) != value:
            raise FrameNestUploadSessionError(INVALID_UPLOAD_SESSION_MESSAGE)
        return cls(parsed)

    def to_string(self) -> str:
        """Serialize the identity as canonical lowercase hyphenated UUID text."""
        return str(self.value)

    def __str__(self) -> str:
        return self.to_string()

    def __repr__(self) -> str:
        return f"UploadSessionId('{self.to_string()}')"


@dataclass(frozen=True, slots=True)
class UploadStorageKey:
    """Server-generated opaque storage identity, not a filesystem path."""

    value: str

    def __init__(self, value: object) -> None:
        if not isinstance(value, str) or not _STORAGE_KEY_PATTERN.fullmatch(value):
            raise FrameNestUploadSessionError(INVALID_UPLOAD_SESSION_MESSAGE)
        if _looks_like_path(value):
            raise FrameNestUploadSessionError(INVALID_UPLOAD_SESSION_MESSAGE)
        object.__setattr__(self, "value", value)

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class UploadDisplayFilename:
    """Display-only upload filename metadata."""

    value: str

    def __init__(self, value: object) -> None:
        if not isinstance(value, str) or not value or len(value) > 255:
            raise FrameNestUploadSessionError(INVALID_UPLOAD_SESSION_MESSAGE)
        if "\x00" in value or "/" in value or "\\" in value:
            raise FrameNestUploadSessionError(INVALID_UPLOAD_SESSION_MESSAGE)
        if PurePosixPath(value).is_absolute() or PureWindowsPath(value).is_absolute():
            raise FrameNestUploadSessionError(INVALID_UPLOAD_SESSION_MESSAGE)
        object.__setattr__(self, "value", value)

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class UploadSession:
    """Durable upload-session domain object independent from transport."""

    id: UploadSessionId
    state: UploadSessionState
    storage_key: UploadStorageKey
    display_filename: UploadDisplayFilename
    declared_size_bytes: int
    received_size_bytes: int
    checksum_algorithm: str | None
    checksum_hex: str | None
    created_at_ms: int
    updated_at_ms: int
    expires_at_ms: int
    failure_code: str | None
    version: int

    def __post_init__(self) -> None:
        if not isinstance(self.id, UploadSessionId):
            raise FrameNestUploadSessionError(INVALID_UPLOAD_SESSION_MESSAGE)
        if not isinstance(self.state, UploadSessionState):
            raise FrameNestUploadSessionError(INVALID_UPLOAD_SESSION_MESSAGE)
        if not isinstance(self.storage_key, UploadStorageKey):
            raise FrameNestUploadSessionError(INVALID_UPLOAD_SESSION_MESSAGE)
        if not isinstance(self.display_filename, UploadDisplayFilename):
            raise FrameNestUploadSessionError(INVALID_UPLOAD_SESSION_MESSAGE)
        _validate_positive_int(self.declared_size_bytes)
        _validate_non_negative_int(self.received_size_bytes)
        if self.received_size_bytes > self.declared_size_bytes:
            raise FrameNestUploadSessionError(INVALID_UPLOAD_SESSION_MESSAGE)
        _validate_upload_session_byte_state(
            state=self.state,
            declared_size_bytes=self.declared_size_bytes,
            received_size_bytes=self.received_size_bytes,
        )
        _validate_checksum_pair(self.checksum_algorithm, self.checksum_hex)
        _validate_non_negative_int(self.created_at_ms)
        _validate_non_negative_int(self.updated_at_ms)
        _validate_non_negative_int(self.expires_at_ms)
        if self.expires_at_ms <= self.created_at_ms:
            raise FrameNestUploadSessionError(INVALID_UPLOAD_SESSION_MESSAGE)
        if self.updated_at_ms < self.created_at_ms:
            raise FrameNestUploadSessionError(INVALID_UPLOAD_SESSION_MESSAGE)
        if self.failure_code is not None and not _FAILURE_CODE_PATTERN.fullmatch(
            self.failure_code
        ):
            raise FrameNestUploadSessionError(INVALID_UPLOAD_SESSION_MESSAGE)
        _validate_non_negative_int(self.version)


def is_terminal_upload_session_state(state: UploadSessionState) -> bool:
    """Return whether a state has no valid outgoing transitions."""
    return state in TERMINAL_UPLOAD_SESSION_STATES


def ensure_upload_session_transition_allowed(
    current: UploadSessionState,
    target: UploadSessionState,
) -> None:
    """Validate a state transition against the durable upload policy."""
    if target not in ALLOWED_UPLOAD_SESSION_TRANSITIONS[current]:
        raise FrameNestUploadSessionTransitionError(INVALID_UPLOAD_TRANSITION_MESSAGE)


def ensure_upload_session_can_transition(
    session: UploadSession,
    target: UploadSessionState,
) -> None:
    """Validate a state transition and target-state byte completeness."""
    ensure_upload_session_transition_allowed(session.state, target)
    if _state_requires_complete_upload(target) and (
        session.received_size_bytes != session.declared_size_bytes
    ):
        raise FrameNestIncompleteUploadSessionError(INCOMPLETE_UPLOAD_SESSION_MESSAGE)


def validate_upload_offset_advance(
    *,
    current_offset: int,
    accepted_bytes: int,
    declared_size_bytes: int,
) -> int:
    """Return the next offset for a positive exact upload byte advance."""
    _validate_non_negative_int(current_offset)
    _validate_positive_int(accepted_bytes, message=INVALID_UPLOAD_OFFSET_MESSAGE)
    _validate_positive_int(declared_size_bytes)
    next_offset = current_offset + accepted_bytes
    if next_offset > declared_size_bytes:
        raise FrameNestUploadOffsetError(INVALID_UPLOAD_OFFSET_MESSAGE)
    return next_offset


def validate_sha256_checksum_hex(value: object) -> str:
    """Return a validated lowercase SHA-256 hex digest."""
    if not isinstance(value, str) or not _SHA256_HEX_PATTERN.fullmatch(value):
        raise FrameNestUploadChecksumError(INVALID_UPLOAD_CHECKSUM_MESSAGE)
    return value


def validate_upload_failure_code(value: object) -> str:
    """Return a sanitized bounded failure code."""
    if not isinstance(value, str) or not _FAILURE_CODE_PATTERN.fullmatch(value):
        raise FrameNestUploadSessionError(INVALID_UPLOAD_SESSION_MESSAGE)
    return value


def _validate_upload_session_byte_state(
    *,
    state: UploadSessionState,
    declared_size_bytes: int,
    received_size_bytes: int,
) -> None:
    if state is UploadSessionState.CREATED and received_size_bytes != 0:
        raise FrameNestUploadSessionError(INVALID_UPLOAD_SESSION_MESSAGE)
    if _state_requires_complete_upload(state) and received_size_bytes != declared_size_bytes:
        raise FrameNestIncompleteUploadSessionError(INCOMPLETE_UPLOAD_SESSION_MESSAGE)


def _state_requires_complete_upload(state: UploadSessionState) -> bool:
    return state in COMPLETE_UPLOAD_SESSION_STATES


def _validate_checksum_pair(algorithm: object, checksum_hex: object) -> None:
    if algorithm is None and checksum_hex is None:
        return
    if algorithm != "sha256":
        raise FrameNestUploadChecksumError(INVALID_UPLOAD_CHECKSUM_MESSAGE)
    validate_sha256_checksum_hex(checksum_hex)


def _validate_positive_int(
    value: object,
    *,
    message: str = INVALID_UPLOAD_SESSION_MESSAGE,
) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise FrameNestUploadSessionError(message)


def _validate_non_negative_int(value: object) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise FrameNestUploadSessionError(INVALID_UPLOAD_SESSION_MESSAGE)


def _looks_like_path(value: str) -> bool:
    return (
        "/" in value
        or "\\" in value
        or PurePosixPath(value).is_absolute()
        or PureWindowsPath(value).is_absolute()
    )
