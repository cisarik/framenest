"""Unit tests for the local media content filesystem reader."""

from __future__ import annotations

import os
import stat
import sys

import pytest

from framenest.application.media_content import MediaContentUnavailableError
from framenest.domain import LibraryPathFlavor, LibraryRoot
from framenest.domain.media import (
    FrameNestMediaRelativePathError,
    MediaKind,
    MediaRelativePath,
)
from framenest.infrastructure.filesystem.media_content import LocalMediaContentReader

MP4_BYTES = b"\x00\x00\x00\x18ftypmp42" + b"\x01" * 100
GIF_BYTES = b"GIF89a" + b"\x02" * 50
_WINDOWS_FLAVOR = LibraryPathFlavor.WINDOWS


def _reader():
    return LocalMediaContentReader()


def _posix_root(path):
    return LibraryRoot(flavor=LibraryPathFlavor.POSIX, path=str(path))


def _write_mp4(root, name="clip.mp4", content=MP4_BYTES):
    target = root / name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(content)
    return target


def _write_gif(root, name="anim.gif", content=GIF_BYTES):
    target = root / name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(content)
    return target


def test_valid_mp4_resolution_returns_content_type_and_size(tmp_path):
    root = tmp_path / "library"
    root.mkdir()
    _write_mp4(root)
    opened = _reader().open(
        _posix_root(root),
        MediaRelativePath("clip.mp4"),
        MediaKind.VIDEO,
    )
    assert opened.media_type == "video/mp4"
    assert opened.byte_size == len(MP4_BYTES)
    assert b"".join(opened.stream(0, None)) == MP4_BYTES


def test_valid_gif_resolution_returns_content_type_and_size(tmp_path):
    root = tmp_path / "library"
    root.mkdir()
    _write_gif(root)
    opened = _reader().open(
        _posix_root(root),
        MediaRelativePath("anim.gif"),
        MediaKind.ANIMATED_IMAGE,
    )
    assert opened.media_type == "image/gif"
    assert opened.byte_size == len(GIF_BYTES)
    assert b"".join(opened.stream(0, None)) == GIF_BYTES


def test_traversal_and_absolute_path_rejected_by_domain():
    with pytest.raises(FrameNestMediaRelativePathError):
        MediaRelativePath("../escape.mp4")
    with pytest.raises(FrameNestMediaRelativePathError):
        MediaRelativePath("/etc/passwd")


def test_symlink_escaping_root_rejected(tmp_path):
    root = tmp_path / "library"
    root.mkdir()
    outside = tmp_path / "outside.mp4"
    outside.write_bytes(MP4_BYTES)
    link = root / "link.mp4"
    os.symlink(outside, link)
    with pytest.raises(MediaContentUnavailableError):
        _reader().open(_posix_root(root), MediaRelativePath("link.mp4"), MediaKind.VIDEO)


def test_symlink_inside_root_accepted(tmp_path):
    root = tmp_path / "library"
    root.mkdir()
    real = _write_mp4(root, "real/video.mp4")
    link = root / "alias.mp4"
    os.symlink(real, link)
    opened = _reader().open(
        _posix_root(root),
        MediaRelativePath("alias.mp4"),
        MediaKind.VIDEO,
    )
    assert opened.media_type == "video/mp4"
    assert b"".join(opened.stream(0, None)) == MP4_BYTES


def test_absent_root_rejected(tmp_path):
    missing = tmp_path / "does-not-exist"
    with pytest.raises(MediaContentUnavailableError):
        _reader().open(_posix_root(missing), MediaRelativePath("clip.mp4"), MediaKind.VIDEO)


def test_root_not_a_directory_rejected(tmp_path):
    file_root = tmp_path / "file_root"
    file_root.write_bytes(b"data")
    with pytest.raises(MediaContentUnavailableError):
        _reader().open(_posix_root(file_root), MediaRelativePath("clip.mp4"), MediaKind.VIDEO)


def test_absent_target_rejected(tmp_path):
    root = tmp_path / "library"
    root.mkdir()
    with pytest.raises(MediaContentUnavailableError):
        _reader().open(_posix_root(root), MediaRelativePath("missing.mp4"), MediaKind.VIDEO)


def test_directory_target_rejected(tmp_path):
    root = tmp_path / "library"
    root.mkdir()
    (root / "subdir").mkdir()
    with pytest.raises(MediaContentUnavailableError):
        _reader().open(_posix_root(root), MediaRelativePath("subdir"), MediaKind.VIDEO)


def test_unsupported_extension_rejected(tmp_path):
    root = tmp_path / "library"
    root.mkdir()
    (root / "notes.txt").write_bytes(b"text")
    with pytest.raises(MediaContentUnavailableError):
        _reader().open(_posix_root(root), MediaRelativePath("notes.txt"), MediaKind.VIDEO)


def test_kind_extension_mismatch_rejected(tmp_path):
    root = tmp_path / "library"
    root.mkdir()
    _write_gif(root)
    with pytest.raises(MediaContentUnavailableError):
        _reader().open(_posix_root(root), MediaRelativePath("anim.gif"), MediaKind.VIDEO)


def test_bounded_byte_iteration_returns_exact_subset(tmp_path):
    root = tmp_path / "library"
    root.mkdir()
    payload = bytes(range(256))
    _write_mp4(root, "clip.mp4", payload)
    opened = _reader().open(_posix_root(root), MediaRelativePath("clip.mp4"), MediaKind.VIDEO)
    assert b"".join(opened.stream(10, 5)) == payload[10:15]
    assert b"".join(opened.stream(0, 0)) == b""
    assert b"".join(opened.stream(250, 100)) == payload[250:]


def test_handle_closed_after_full_iteration(tmp_path):
    root = tmp_path / "library"
    root.mkdir()
    _write_mp4(root)
    opened = _reader().open(_posix_root(root), MediaRelativePath("clip.mp4"), MediaKind.VIDEO)
    gen = opened.stream(0, None)
    list(gen)
    assert gen.gi_frame is None


def test_handle_closed_on_early_generator_close(tmp_path):
    root = tmp_path / "library"
    root.mkdir()
    _write_mp4(root, "big.mp4", b"\x00" * 200_000)
    opened = _reader().open(_posix_root(root), MediaRelativePath("big.mp4"), MediaKind.VIDEO)
    gen = opened.stream(0, None)
    next(gen)
    gen.close()
    assert gen.gi_frame is None


@pytest.mark.skipif(sys.platform == "win32" or os.geteuid() == 0, reason="requires non-root posix")
def test_unreadable_file_rejected(tmp_path):
    root = tmp_path / "library"
    root.mkdir()
    target = _write_mp4(root, "clip.mp4")
    os.chmod(target, 0o000)
    try:
        with pytest.raises(MediaContentUnavailableError):
            _reader().open(_posix_root(root), MediaRelativePath("clip.mp4"), MediaKind.VIDEO)
    finally:
        os.chmod(target, stat.S_IRUSR | stat.S_IWUSR)


def test_sanitized_failures_do_not_disclose_paths(tmp_path):
    root = tmp_path / "library"
    root.mkdir()
    try:
        _reader().open(_posix_root(root), MediaRelativePath("missing.mp4"), MediaKind.VIDEO)
    except MediaContentUnavailableError as exc:
        assert str(root) not in str(exc)
        assert "missing.mp4" not in str(exc)
    else:
        pytest.fail("expected MediaContentUnavailableError")
