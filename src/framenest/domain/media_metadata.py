"""Pure-domain media metadata and canonical tag values."""

from __future__ import annotations

from dataclasses import dataclass
import re
import unicodedata

from framenest.domain.identities import MediaId

INVALID_MEDIA_METADATA_MESSAGE = "Invalid FrameNest media metadata."
MAX_DISPLAY_TITLE_CODE_POINTS = 240
MAX_TAG_KEY_CODE_POINTS = 64
MAX_TAG_DISPLAY_NAME_CODE_POINTS = 80
MAX_MEDIA_TAGS = 32
MAX_DESCRIPTION_CODE_POINTS = 10_000

_TAG_KEY_PATTERN = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")


class FrameNestMediaMetadataError(ValueError):
    """Sanitized error raised when media metadata construction is invalid."""


def _has_control_character(value: str) -> bool:
    return any(unicodedata.category(character) == "Cc" for character in value)


def _validate_non_negative_int(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise FrameNestMediaMetadataError(INVALID_MEDIA_METADATA_MESSAGE)
    return value


@dataclass(frozen=True, slots=True)
class CanonicalTagKey:
    """Stable English lowercase ASCII slug for a canonical tag."""

    value: str

    def __init__(self, value: object) -> None:
        if not isinstance(value, str):
            raise FrameNestMediaMetadataError(INVALID_MEDIA_METADATA_MESSAGE)
        if len(value) > MAX_TAG_KEY_CODE_POINTS or _TAG_KEY_PATTERN.fullmatch(value) is None:
            raise FrameNestMediaMetadataError(INVALID_MEDIA_METADATA_MESSAGE)
        object.__setattr__(self, "value", value)

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class CanonicalTagDisplayName:
    """Presentation text for one canonical tag definition."""

    value: str

    def __init__(self, value: object) -> None:
        if not isinstance(value, str):
            raise FrameNestMediaMetadataError(INVALID_MEDIA_METADATA_MESSAGE)
        if _has_control_character(value):
            raise FrameNestMediaMetadataError(INVALID_MEDIA_METADATA_MESSAGE)
        trimmed = value.strip()
        if (
            not trimmed
            or len(trimmed) > MAX_TAG_DISPLAY_NAME_CODE_POINTS
        ):
            raise FrameNestMediaMetadataError(INVALID_MEDIA_METADATA_MESSAGE)
        object.__setattr__(self, "value", trimmed)

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class MediaDisplayTitle:
    """User-editable display title stored separately from physical filenames."""

    value: str

    def __init__(self, value: object) -> None:
        if not isinstance(value, str):
            raise FrameNestMediaMetadataError(INVALID_MEDIA_METADATA_MESSAGE)
        if (
            not value
            or value.strip() != value
            or len(value) > MAX_DISPLAY_TITLE_CODE_POINTS
            or _has_control_character(value)
        ):
            raise FrameNestMediaMetadataError(INVALID_MEDIA_METADATA_MESSAGE)
        object.__setattr__(self, "value", value)

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class MediaDescription:
    """Plain-text description for a logical media item."""

    value: str

    def __init__(self, value: object) -> None:
        if not isinstance(value, str):
            raise FrameNestMediaMetadataError(INVALID_MEDIA_METADATA_MESSAGE)
        if not value:
            raise FrameNestMediaMetadataError(INVALID_MEDIA_METADATA_MESSAGE)
        if value.strip() != value:
            raise FrameNestMediaMetadataError(INVALID_MEDIA_METADATA_MESSAGE)
        if len(value) > MAX_DESCRIPTION_CODE_POINTS:
            raise FrameNestMediaMetadataError(INVALID_MEDIA_METADATA_MESSAGE)
        if _has_forbidden_control_char(value):
            raise FrameNestMediaMetadataError(INVALID_MEDIA_METADATA_MESSAGE)
        object.__setattr__(self, "value", value)

    def __str__(self) -> str:
        return self.value


def _has_forbidden_control_char(value: str) -> bool:
    for ch in value:
        if unicodedata.category(ch) == "Cc" and ch != "\n":
            return True
    return False


@dataclass(frozen=True, slots=True)
class CanonicalTag:
    """One canonical content/organization tag definition."""

    key: CanonicalTagKey
    display_name: CanonicalTagDisplayName
    created_at_ms: int
    updated_at_ms: int

    def __post_init__(self) -> None:
        if not isinstance(self.key, CanonicalTagKey):
            raise FrameNestMediaMetadataError(INVALID_MEDIA_METADATA_MESSAGE)
        if not isinstance(self.display_name, CanonicalTagDisplayName):
            raise FrameNestMediaMetadataError(INVALID_MEDIA_METADATA_MESSAGE)
        _validate_non_negative_int(self.created_at_ms)
        _validate_non_negative_int(self.updated_at_ms)
        if self.updated_at_ms < self.created_at_ms:
            raise FrameNestMediaMetadataError(INVALID_MEDIA_METADATA_MESSAGE)


@dataclass(frozen=True, slots=True)
class MediaMetadata:
    """Persisted user metadata for one logical media item."""

    media_id: MediaId
    display_title: MediaDisplayTitle | None
    description: MediaDescription | None
    tag_keys: tuple[CanonicalTagKey, ...]
    created_at_ms: int
    updated_at_ms: int

    def __post_init__(self) -> None:
        if not isinstance(self.media_id, MediaId):
            raise FrameNestMediaMetadataError(INVALID_MEDIA_METADATA_MESSAGE)
        if self.display_title is not None and not isinstance(
            self.display_title,
            MediaDisplayTitle,
        ):
            raise FrameNestMediaMetadataError(INVALID_MEDIA_METADATA_MESSAGE)
        if self.description is not None and not isinstance(
            self.description,
            MediaDescription,
        ):
            raise FrameNestMediaMetadataError(INVALID_MEDIA_METADATA_MESSAGE)
        if not isinstance(self.tag_keys, tuple) or any(
            not isinstance(key, CanonicalTagKey) for key in self.tag_keys
        ):
            raise FrameNestMediaMetadataError(INVALID_MEDIA_METADATA_MESSAGE)
        if len(self.tag_keys) > MAX_MEDIA_TAGS or len(set(self.tag_keys)) != len(self.tag_keys):
            raise FrameNestMediaMetadataError(INVALID_MEDIA_METADATA_MESSAGE)
        _validate_non_negative_int(self.created_at_ms)
        _validate_non_negative_int(self.updated_at_ms)
        if self.updated_at_ms < self.created_at_ms:
            raise FrameNestMediaMetadataError(INVALID_MEDIA_METADATA_MESSAGE)
