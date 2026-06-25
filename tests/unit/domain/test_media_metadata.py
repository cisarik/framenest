"""Unit tests for persistent media metadata domain values."""

from __future__ import annotations

import pytest

from framenest.domain import MediaId
from framenest.domain.media_metadata import (
    CanonicalTag,
    CanonicalTagDisplayName,
    CanonicalTagKey,
    FrameNestMediaMetadataError,
    MediaDisplayTitle,
    MediaMetadata,
)


MEDIA_ID = MediaId.from_string("12345678-1234-4234-9234-123456789abc")


@pytest.mark.parametrize(
    "value",
    ["mathematics", "compression", "meme", "reaction-video", "a1", "a-b2"],
)
def test_valid_canonical_tag_keys(value: str) -> None:
    assert CanonicalTagKey(value).value == value


@pytest.mark.parametrize(
    "value",
    ["", "Math", " math", "math ", "-math", "math-", "math--logic", "méme", "a_b", "a.b"],
)
def test_invalid_canonical_tag_keys(value: str) -> None:
    with pytest.raises(FrameNestMediaMetadataError):
        CanonicalTagKey(value)


def test_canonical_tag_key_maximum_length() -> None:
    assert CanonicalTagKey("a" * 64).value == "a" * 64
    with pytest.raises(FrameNestMediaMetadataError):
        CanonicalTagKey("a" * 65)


@pytest.mark.parametrize("value", ["Math", "Compression", "Meme", "Žánr"])
def test_valid_display_names(value: str) -> None:
    assert CanonicalTagDisplayName(value).value == value


def test_display_names_are_trimmed_and_controls_rejected() -> None:
    assert CanonicalTagDisplayName("  Math  ").value == "Math"
    with pytest.raises(FrameNestMediaMetadataError):
        CanonicalTagDisplayName("")
    with pytest.raises(FrameNestMediaMetadataError):
        CanonicalTagDisplayName("Math\n")
    with pytest.raises(FrameNestMediaMetadataError):
        CanonicalTagDisplayName("Bad\x00Name")


def test_display_name_maximum_counts_unicode_code_points() -> None:
    assert len(CanonicalTagDisplayName("é" * 80).value) == 80
    with pytest.raises(FrameNestMediaMetadataError):
        CanonicalTagDisplayName("é" * 81)


def test_display_title_validation_and_maximum() -> None:
    assert MediaDisplayTitle("Reinventing Entropy").value == "Reinventing Entropy"
    assert len(MediaDisplayTitle("é" * 240).value) == 240
    for value in ("", " Title", "Title ", "Bad\nTitle", "Bad\x00Title", "é" * 241):
        with pytest.raises(FrameNestMediaMetadataError):
            MediaDisplayTitle(value)


def test_canonical_tag_validates_types_and_timestamps() -> None:
    tag = CanonicalTag(
        key=CanonicalTagKey("mathematics"),
        display_name=CanonicalTagDisplayName("Math"),
        created_at_ms=1,
        updated_at_ms=2,
    )
    assert tag.key == CanonicalTagKey("mathematics")

    with pytest.raises(FrameNestMediaMetadataError):
        CanonicalTag(
            key=CanonicalTagKey("mathematics"),
            display_name=CanonicalTagDisplayName("Math"),
            created_at_ms=2,
            updated_at_ms=1,
        )
    with pytest.raises(FrameNestMediaMetadataError):
        CanonicalTag(
            key=CanonicalTagKey("mathematics"),
            display_name=CanonicalTagDisplayName("Math"),
            created_at_ms=-1,
            updated_at_ms=1,
        )


def test_media_metadata_rejects_duplicate_or_too_many_tag_keys() -> None:
    first = CanonicalTagKey("mathematics")
    second = CanonicalTagKey("compression")

    metadata = MediaMetadata(
        media_id=MEDIA_ID,
        display_title=None,
        tag_keys=(first, second),
        created_at_ms=1,
        updated_at_ms=1,
    )
    assert metadata.tag_keys == (first, second)

    with pytest.raises(FrameNestMediaMetadataError):
        MediaMetadata(
            media_id=MEDIA_ID,
            display_title=None,
            tag_keys=(first, first),
            created_at_ms=1,
            updated_at_ms=1,
        )
    with pytest.raises(FrameNestMediaMetadataError):
        MediaMetadata(
            media_id=MEDIA_ID,
            display_title=None,
            tag_keys=tuple(CanonicalTagKey(f"tag-{index}") for index in range(33)),
            created_at_ms=1,
            updated_at_ms=1,
        )


def test_media_metadata_validates_media_id_title_and_timestamps() -> None:
    with pytest.raises(FrameNestMediaMetadataError):
        MediaMetadata(
            media_id="not-media-id",  # type: ignore[arg-type]
            display_title=None,
            tag_keys=(),
            created_at_ms=1,
            updated_at_ms=1,
        )
    with pytest.raises(FrameNestMediaMetadataError):
        MediaMetadata(
            media_id=MEDIA_ID,
            display_title="Title",  # type: ignore[arg-type]
            tag_keys=(),
            created_at_ms=1,
            updated_at_ms=1,
        )
    with pytest.raises(FrameNestMediaMetadataError):
        MediaMetadata(
            media_id=MEDIA_ID,
            display_title=None,
            tag_keys=(),
            created_at_ms=2,
            updated_at_ms=1,
        )
