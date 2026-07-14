"""Unit tests for server-owned quarantine upload storage."""

from __future__ import annotations

import os
import stat
from pathlib import Path

import pytest

from framenest.application.ports.quarantine_storage import QuarantineStateInconsistentError
from framenest.domain.uploads import FrameNestUploadSessionError, UploadStorageKey
from framenest.infrastructure.filesystem.quarantine_storage import FilesystemQuarantineStorage


def _key(value: str = "uploadquarantinekey0001") -> UploadStorageKey:
    return UploadStorageKey(value)


def test_root_must_exist_and_not_be_symlink(tmp_path: Path) -> None:
    missing = FilesystemQuarantineStorage(tmp_path / "missing")
    assert not missing.root_available

    target = tmp_path / "target"
    target.mkdir()
    link = tmp_path / "link"
    link.symlink_to(target, target_is_directory=True)

    assert not FilesystemQuarantineStorage(link).root_available


def test_exclusive_regular_file_creation_permissions_append_truncate_and_remove(
    tmp_path: Path,
) -> None:
    storage = FilesystemQuarantineStorage(tmp_path)
    key = _key()

    writer = storage.open_writer(key, offset=0, create=True)
    try:
        assert writer.write(b"abc") == 3
        writer.flush_and_fsync()
    finally:
        writer.close()

    path = next(tmp_path.iterdir())
    assert path.name == f"{key.value}.part"
    assert path.read_bytes() == b"abc"
    assert stat.S_IMODE(path.stat().st_mode) & 0o111 == 0
    assert storage.file_size(key) == 3

    with pytest.raises(Exception):
        storage.open_writer(key, offset=3, create=True)

    writer = storage.open_writer(key, offset=3, create=False)
    try:
        assert writer.write(b"def") == 3
        writer.truncate_and_fsync(4)
    finally:
        writer.close()

    assert path.read_bytes() == b"abcd"
    storage.truncate(key, 2)
    assert path.read_bytes() == b"ab"
    storage.remove(key)
    storage.remove(key)
    assert not path.exists()


def test_storage_key_cannot_select_path_or_client_filename(tmp_path: Path) -> None:
    storage = FilesystemQuarantineStorage(tmp_path)
    with pytest.raises(FrameNestUploadSessionError):
        UploadStorageKey("../private-file")

    key = _key("clientfilenameignored001")
    writer = storage.open_writer(key, offset=0, create=True)
    try:
        writer.write(b"x")
        writer.flush_and_fsync()
    finally:
        writer.close()

    assert sorted(path.name for path in tmp_path.iterdir()) == [f"{key.value}.part"]


@pytest.mark.skipif(not hasattr(os, "symlink"), reason="symlink unavailable")
def test_symlink_file_is_rejected_without_following_target(tmp_path: Path) -> None:
    outside = tmp_path.parent / "outside-upload-target"
    outside.write_bytes(b"outside")
    key = _key("symlinkuploadkey001")
    (tmp_path / f"{key.value}.part").symlink_to(outside)

    storage = FilesystemQuarantineStorage(tmp_path)

    with pytest.raises(QuarantineStateInconsistentError):
        storage.file_size(key)
    assert outside.read_bytes() == b"outside"
