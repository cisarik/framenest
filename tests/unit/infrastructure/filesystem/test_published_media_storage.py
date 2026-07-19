"""Filesystem safety tests for atomic published-original ownership."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
import stat
import uuid

import pytest

from framenest.application.ports.published_media_storage import (
    PublishedMediaStorageUnavailableError,
    PublishedMediaTargetCollisionError,
    PublishedMediaVerificationError,
    PublishedMediaWriteError,
)
from framenest.domain.identities import LibraryId, MediaByteIdentityId
from framenest.domain.upload_publications import new_upload_publication_reservation
from framenest.domain.uploads import (
    UploadDisplayFilename,
    UploadSession,
    UploadSessionId,
    UploadSessionState,
    UploadStorageKey,
    UploadValidatedFormat,
    UploadValidatedMediaKind,
)
from framenest.infrastructure.filesystem.published_media_storage import (
    FilesystemPublishedMediaStorage,
)
import framenest.infrastructure.filesystem.published_media_storage as storage_module
from framenest.infrastructure.filesystem.quarantine_storage import (
    FilesystemQuarantineStorage,
)


def _publication(data: bytes):
    digest = hashlib.sha256(data).hexdigest()
    upload = UploadSession(
        id=UploadSessionId(uuid.UUID("11111111-1111-4111-8111-111111111111")),
        state=UploadSessionState.PUBLISH_PENDING,
        storage_key=UploadStorageKey("synthetic-upload-0001"),
        display_filename=UploadDisplayFilename("private-client-name.mp4"),
        declared_size_bytes=len(data),
        received_size_bytes=len(data),
        checksum_algorithm="sha256",
        checksum_hex=digest,
        validated_media_kind=UploadValidatedMediaKind.VIDEO,
        validated_format=UploadValidatedFormat.MP4,
        byte_identity_id=MediaByteIdentityId(
            uuid.UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")
        ),
        created_at_ms=10,
        updated_at_ms=20,
        expires_at_ms=100,
        failure_code=None,
        version=2,
    )
    return new_upload_publication_reservation(
        upload,
        destination_id=LibraryId(
            uuid.UUID("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb")
        ),
        now_ms=20,
    )


def _quarantine(tmp_path: Path, data: bytes):
    root = tmp_path / "quarantine"
    root.mkdir()
    storage = FilesystemQuarantineStorage(root)
    key = UploadStorageKey("synthetic-upload-0001")
    writer = storage.open_writer(key, offset=0, create=True)
    try:
        assert writer.write(data) == len(data)
        writer.flush_and_fsync()
    finally:
        writer.close()
    return storage, key, root


def _published_storage(tmp_path: Path, publication):
    root = tmp_path / "published"
    root.mkdir()
    return FilesystemPublishedMediaStorage(
        publication.destination_id,
        root,
    ), root


def test_streams_hashes_fsyncs_and_atomically_links_without_replacement(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    data = (b"synthetic-mp4-payload" * 70_000) + b"end"
    publication = _publication(data)
    quarantine, key, _ = _quarantine(tmp_path, data)
    published, root = _published_storage(tmp_path, publication)
    reader = quarantine.open_reader(key, expected_size_bytes=len(data))
    real_link = os.link
    calls: list[tuple[object, ...]] = []

    def recording_link(*args, **kwargs):
        calls.append((args, kwargs))
        return real_link(*args, **kwargs)

    monkeypatch.setattr(storage_module.os, "link", recording_link)
    try:
        published.publish_from_reader(publication, reader)
    finally:
        reader.close()

    final = root / publication.relative_path.value
    assert final.read_bytes() == data
    assert stat.S_IMODE(final.stat().st_mode) == 0o600
    assert published.verify_target(publication) is True
    assert len(calls) == 1
    assert calls[0][1]["follow_symlinks"] is False
    assert not list(root.glob("*.publish.tmp"))


@pytest.mark.parametrize(
    "temporary_bytes",
    [b"synt", b"synthetic-safe-recovery"],
    ids=["partial", "complete"],
)
def test_owned_partial_or_complete_temporary_is_rebuilt_and_target_is_reconstructed(
    tmp_path: Path,
    temporary_bytes: bytes,
) -> None:
    data = b"synthetic-safe-recovery"
    publication = _publication(data)
    quarantine, key, _ = _quarantine(tmp_path, data)
    published, root = _published_storage(tmp_path, publication)
    temp = root / f".{publication.publication_id.value.hex}.publish.tmp"
    temp.write_bytes(temporary_bytes)
    temp.chmod(0o600)

    reader = quarantine.open_reader(key, expected_size_bytes=len(data))
    try:
        published.publish_from_reader(publication, reader)
    finally:
        reader.close()

    assert published.verify_target(publication) is True
    assert not temp.exists()
    quarantine.remove(key)
    assert published.verify_target(publication) is True


def test_hard_linked_existing_temporary_is_rejected_before_truncation(
    tmp_path: Path,
) -> None:
    data = b"synthetic-hard-link-guard"
    publication = _publication(data)
    quarantine, key, _ = _quarantine(tmp_path, data)
    published, root = _published_storage(tmp_path, publication)
    temp = root / f".{publication.publication_id.value.hex}.publish.tmp"
    temp.write_bytes(b"synthetic-stale-temporary")
    temp.chmod(0o600)
    alias = root / ".synthetic-hard-link-alias"
    os.link(temp, alias)

    reader = quarantine.open_reader(key, expected_size_bytes=len(data))
    try:
        with pytest.raises(PublishedMediaWriteError):
            published.publish_from_reader(publication, reader)
    finally:
        reader.close()

    assert temp.read_bytes() == b"synthetic-stale-temporary"
    assert alias.read_bytes() == b"synthetic-stale-temporary"
    assert not (root / publication.relative_path.value).exists()
    assert quarantine.file_size(key) == len(data)


def test_unexpected_final_collision_is_never_overwritten_or_adopted(
    tmp_path: Path,
) -> None:
    expected = b"expected-source"
    unexpected = b"unexpected-existing-object"
    publication = _publication(expected)
    quarantine, key, _ = _quarantine(tmp_path, expected)
    published, root = _published_storage(tmp_path, publication)
    final = root / publication.relative_path.value
    final.write_bytes(unexpected)
    final.chmod(0o600)
    reader = quarantine.open_reader(key, expected_size_bytes=len(expected))
    try:
        with pytest.raises(PublishedMediaTargetCollisionError):
            published.publish_from_reader(publication, reader)
    finally:
        reader.close()

    assert final.read_bytes() == unexpected
    assert quarantine.file_size(key) == len(expected)


def test_failure_before_durable_target_leaves_source_and_owned_partial_retryable(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    data = b"synthetic-fsync-failure"
    publication = _publication(data)
    quarantine, key, _ = _quarantine(tmp_path, data)
    published, root = _published_storage(tmp_path, publication)
    reader = quarantine.open_reader(key, expected_size_bytes=len(data))
    real_fsync_file = storage_module._fsync_file

    def fail_fsync(_: int) -> None:
        raise PublishedMediaWriteError("published media write failed")

    monkeypatch.setattr(storage_module, "_fsync_file", fail_fsync)
    try:
        with pytest.raises(PublishedMediaWriteError):
            published.publish_from_reader(publication, reader)
    finally:
        reader.close()

    assert quarantine.file_size(key) == len(data)
    assert not (root / publication.relative_path.value).exists()
    assert (root / f".{publication.publication_id.value.hex}.publish.tmp").exists()

    monkeypatch.setattr(storage_module, "_fsync_file", real_fsync_file)
    retry_reader = quarantine.open_reader(key, expected_size_bytes=len(data))
    try:
        published.publish_from_reader(publication, retry_reader)
    finally:
        retry_reader.close()
    assert published.verify_target(publication) is True


def test_source_mutation_and_symlink_or_non_regular_targets_fail_closed(
    tmp_path: Path,
) -> None:
    data = b"stable-source"
    publication = _publication(data)
    quarantine, key, quarantine_root = _quarantine(tmp_path, data)
    published, root = _published_storage(tmp_path, publication)
    reader = quarantine.open_reader(key, expected_size_bytes=len(data))
    quarantine_file = quarantine_root / "synthetic-upload-0001.part"
    quarantine_file.write_bytes(b"changed-bytes")
    try:
        with pytest.raises(PublishedMediaVerificationError):
            published.publish_from_reader(publication, reader)
    finally:
        reader.close()

    final = root / publication.relative_path.value
    external = tmp_path / "external"
    external.write_bytes(data)
    final.symlink_to(external)
    with pytest.raises(PublishedMediaTargetCollisionError):
        published.verify_target(publication)
    assert external.read_bytes() == data


def test_root_must_be_native_non_symlink_writable_and_separate(
    tmp_path: Path,
) -> None:
    data = b"root-safety"
    publication = _publication(data)
    real_root = tmp_path / "real-published"
    real_root.mkdir()
    symlink_root = tmp_path / "published-link"
    symlink_root.symlink_to(real_root, target_is_directory=True)

    symlinked = FilesystemPublishedMediaStorage(
        publication.destination_id,
        symlink_root,
    )
    overlapping = FilesystemPublishedMediaStorage(
        publication.destination_id,
        real_root,
        forbidden_roots=(real_root / "database",),
    )
    missing = FilesystemPublishedMediaStorage(
        publication.destination_id,
        tmp_path / "missing",
    )

    assert symlinked.root_available is False
    assert overlapping.root_available is False
    assert missing.root_available is False
    with pytest.raises(PublishedMediaStorageUnavailableError):
        overlapping.verify_target(publication)
