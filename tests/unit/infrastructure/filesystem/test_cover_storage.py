"""Filesystem and Pillow adapters for durable cover artifacts and thumbnails."""

from __future__ import annotations

import io
from pathlib import Path

import pytest
from PIL import Image

from framenest.application.media_analysis import RepresentativeFrame
from framenest.application.ports.cover_storage import (
    CoverArtifact,
    CoverStorageError,
    CoverThumbnailImage,
    CoverThumbnailUnavailableError,
)
from framenest.domain.identities import MediaId
from framenest.domain.media_cover import (
    COVER_ARTIFACT_MEDIA_TYPE,
    COVER_ARTIFACT_PROFILE,
    COVER_THUMBNAIL_ALGORITHM,
)
from framenest.infrastructure.filesystem.cover_storage import (
    COVER_ARTIFACT_MAX_BYTES,
    COVER_ARTIFACT_MAX_LONG_EDGE,
    FilesystemCoverThumbnailCache,
    FilesystemDurableCoverStorage,
    PillowCoverEncoder,
)

MEDIA_ID = MediaId.from_string("11111111-1111-4111-8111-111111111111")
DIGEST = "b" * 64


def _png_frame(width: int = 160, height: int = 90, color: tuple[int, int, int] = (200, 30, 30)) -> RepresentativeFrame:
    buffer = io.BytesIO()
    Image.new("RGB", (width, height), color).save(buffer, format="PNG")
    return RepresentativeFrame(
        timestamp_ms=250,
        mime_type="image/png",
        sha256=__import__("hashlib").sha256(buffer.getvalue()).hexdigest(),
        byte_size=len(buffer.getvalue()),
        payload=buffer.getvalue(),
    )


def _artifact_from_payload(payload: bytes, width: int, height: int) -> CoverArtifact:
    import hashlib

    return CoverArtifact(
        profile=COVER_ARTIFACT_PROFILE,
        media_type=COVER_ARTIFACT_MEDIA_TYPE,
        digest=hashlib.sha256(payload).hexdigest(),
        width=width,
        height=height,
        byte_size=len(payload),
        payload=payload,
    )


def test_encoder_produces_bounded_durable_artifact() -> None:
    encoder = PillowCoverEncoder()
    artifact = encoder.encode_artifact_frame(_png_frame(width=1100, height=800))
    assert artifact.media_type == COVER_ARTIFACT_MEDIA_TYPE
    assert artifact.profile == COVER_ARTIFACT_PROFILE
    assert artifact.width <= COVER_ARTIFACT_MAX_LONG_EDGE
    assert artifact.height <= COVER_ARTIFACT_MAX_LONG_EDGE
    assert artifact.byte_size == len(artifact.payload)
    assert artifact.byte_size <= COVER_ARTIFACT_MAX_BYTES
    assert len(artifact.digest) == 64


def test_encoder_produces_bounded_thumbnail_from_artifact() -> None:
    encoder = PillowCoverEncoder()
    artifact = encoder.encode_artifact_frame(_png_frame())
    thumbnail = encoder.encode_thumbnail(artifact.payload)
    assert thumbnail.media_type == COVER_ARTIFACT_MEDIA_TYPE
    assert thumbnail.byte_size == len(thumbnail.payload)
    assert len(thumbnail.sha256) == 64


def test_storage_publishes_and_validates_immutable_artifact(tmp_path: Path) -> None:
    root = tmp_path / "covers"
    storage = FilesystemDurableCoverStorage(root)
    encoder = PillowCoverEncoder()
    artifact = encoder.encode_artifact_frame(_png_frame())

    storage.publish(media_id=MEDIA_ID, artifact=artifact)
    assert storage.artifact_valid(media_id=MEDIA_ID, digest=artifact.digest) is True
    assert storage.read_bytes(media_id=MEDIA_ID, digest=artifact.digest) == artifact.payload

    # Idempotent re-publish of identical bytes is a no-op.
    storage.publish(media_id=MEDIA_ID, artifact=artifact)

    final = root / MEDIA_ID.to_string() / f"{artifact.digest}.jpg"
    assert final.is_file()
    assert storage.artifact_valid(media_id=MEDIA_ID, digest="0" * 64) is False


def test_storage_never_replaces_existing_immutable_identity(tmp_path: Path) -> None:
    root = tmp_path / "covers"
    storage = FilesystemDurableCoverStorage(root)
    encoder = PillowCoverEncoder()
    artifact = encoder.encode_artifact_frame(_png_frame())
    storage.publish(media_id=MEDIA_ID, artifact=artifact)

    final = root / MEDIA_ID.to_string() / f"{artifact.digest}.jpg"
    original = final.read_bytes()

    # Pre-place different bytes at the same immutable identity: publish must
    # refuse to clobber and leave the differing bytes untouched.
    tampered = artifact.payload[:-1] + bytes([artifact.payload[-1] ^ 0xFF])
    final.write_bytes(tampered)
    with pytest.raises(CoverStorageError):
        storage.publish(media_id=MEDIA_ID, artifact=artifact)
    assert final.read_bytes() == tampered


def test_storage_rejects_mismatched_digest_without_publishing(tmp_path: Path) -> None:
    storage = FilesystemDurableCoverStorage(tmp_path / "covers")
    encoder = PillowCoverEncoder()
    artifact = encoder.encode_artifact_frame(_png_frame())
    corrupted = CoverArtifact(
        profile=artifact.profile,
        media_type=artifact.media_type,
        digest="0" * 64,
        width=artifact.width,
        height=artifact.height,
        byte_size=artifact.byte_size,
        payload=artifact.payload,
    )
    with pytest.raises(CoverStorageError):
        storage.publish(media_id=MEDIA_ID, artifact=corrupted)
    assert storage.artifact_valid(media_id=MEDIA_ID, digest="0" * 64) is False


def test_storage_rejects_non_regular_and_symlinked_targets(tmp_path: Path) -> None:
    root = tmp_path / "covers"
    storage = FilesystemDurableCoverStorage(root)
    encoder = PillowCoverEncoder()
    artifact = encoder.encode_artifact_frame(_png_frame())
    media_dir = root / MEDIA_ID.to_string()
    media_dir.mkdir(parents=True)
    final = media_dir / f"{artifact.digest}.jpg"
    final.mkdir()  # directory where a file is expected
    with pytest.raises(CoverStorageError):
        storage.publish(media_id=MEDIA_ID, artifact=artifact)
    assert storage.artifact_valid(media_id=MEDIA_ID, digest=artifact.digest) is False

    final.rmdir()
    outside = tmp_path / "outside0"
    outside.write_bytes(artifact.payload)
    final.symlink_to(outside)
    assert storage.artifact_valid(media_id=MEDIA_ID, digest=artifact.digest) is False
    with pytest.raises(CoverStorageError):
        storage.publish(media_id=MEDIA_ID, artifact=artifact)


def test_thumbnail_cache_no_clobber_contains_and_open(tmp_path: Path) -> None:
    root = tmp_path / "thumbnails"
    cache = FilesystemCoverThumbnailCache(root)
    assert cache.algorithm == COVER_THUMBNAIL_ALGORITHM
    encoder = PillowCoverEncoder()
    artifact = encoder.encode_artifact_frame(_png_frame())
    thumbnail = encoder.encode_thumbnail(artifact.payload)
    key = cache.key_for(media_id=MEDIA_ID, artifact_digest=artifact.digest)

    assert cache.contains(key) is False
    cache.publish(key, thumbnail)
    assert cache.contains(key) is True
    assert cache.contains_many((key,)) == {key}

    # No-clobber on identical re-publish.
    cache.publish(key, thumbnail)

    opened = cache.open(key)
    assert opened.media_type == COVER_ARTIFACT_MEDIA_TYPE
    assert opened.byte_size == len(thumbnail.payload)
    assert opened.payload == thumbnail.payload
    opened.close()

    cached_path = root / COVER_THUMBNAIL_ALGORITHM / MEDIA_ID.to_string() / f"{artifact.digest}.jpg"
    assert cached_path.is_file()


def test_thumbnail_cache_rejects_traversal_and_corruption(tmp_path: Path) -> None:
    cache = FilesystemCoverThumbnailCache(tmp_path / "thumbnails")
    encoder = PillowCoverEncoder()
    artifact = encoder.encode_artifact_frame(_png_frame())
    thumbnail = encoder.encode_thumbnail(artifact.payload)

    with pytest.raises(CoverStorageError):
        cache.key_for(media_id=MEDIA_ID, artifact_digest="not-a-hex")
    cache.publish(
        cache.key_for(media_id=MEDIA_ID, artifact_digest=artifact.digest),
        thumbnail,
    )
    with pytest.raises(CoverStorageError):
        cache.publish(
            cache.key_for(media_id=MEDIA_ID, artifact_digest=artifact.digest),
            CoverThumbnailImage(
                media_type=COVER_ARTIFACT_MEDIA_TYPE,
                byte_size=len(b"not-a-jpeg"),
                sha256=__import__("hashlib").sha256(b"not-a-jpeg").hexdigest(),
                payload=b"not-a-jpeg",
            ),
        )


def test_thumbnail_open_reports_unavailable_for_corrupt_or_absent(tmp_path: Path) -> None:
    root = tmp_path / "thumbnails"
    cache = FilesystemCoverThumbnailCache(root)
    encoder = PillowCoverEncoder()
    artifact = encoder.encode_artifact_frame(_png_frame())
    key = cache.key_for(media_id=MEDIA_ID, artifact_digest=artifact.digest)
    with pytest.raises(CoverThumbnailUnavailableError):
        cache.open(key)

    target = (
        root
        / COVER_THUMBNAIL_ALGORITHM
        / MEDIA_ID.to_string()
        / f"{artifact.digest}.jpg"
    )
    target.parent.mkdir(parents=True)
    target.write_bytes(b"broken")
    assert cache.contains(key) is False
    with pytest.raises(CoverThumbnailUnavailableError):
        cache.open(key)
