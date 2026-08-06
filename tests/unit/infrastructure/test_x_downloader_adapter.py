"""YtDlpXExtractor tests using a fake executable and local synthetic JSON."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from framenest.application.ports.x_extractor import XExtractionError
from framenest.domain.x_acquisition import (
    XMediaType,
    XNormalizedInspection,
)
from framenest.infrastructure.x.downloader import YtDlpXExtractor


def _write_fake_executable(path: Path, stdout_json: str | None = None, *,
                           exit_code: int = 0, artifact_name: str | None = None,
                           delay: float = 0.0) -> Path:
    json_literal = "None"
    if stdout_json is not None:
        json_literal = "'''" + stdout_json + "'''"
    artifact_literal = "'artifact.mp4'" if artifact_name is None else "'" + artifact_name + "'"
    header = (
        "#!/usr/bin/env python3\n"
        "import sys, time, os\n"
        "time.sleep(%.2f)\n"
        "args = sys.argv[1:]\n"
        "if '--version' in args:\n"
        "    sys.stdout.write('2025.01.01\\n')\n"
        "    sys.exit(%d)\n"
        "if '--dump-single-json' in args:\n"
        "    payload = %s\n"
        "    if payload is not None:\n"
        "        sys.stdout.write(payload)\n"
        "    sys.exit(%d)\n"
        "if '--output' in args:\n"
        "    name = %s\n"
        "    with open(name, 'wb') as f:\n"
        "        f.write(b'\\x00\\x00\\x00\\x18ftypmp42fake')\n"
        "    sys.exit(%d)\n"
        "sys.exit(%d)\n"
    )
    path.write_text(header % (delay, exit_code, json_literal, exit_code,
                              artifact_literal, exit_code, exit_code))
    path.chmod(0o755)
    return path


def _video_json(post_id: str = "123456789") -> str:
    return json.dumps(
        {
            "id": f"asset-{post_id}",
            "ext": "mp4",
            "description": "A cat video",
            "uploader_id": "user_1",
            "uploader": "author",
            "channel": "Author Name",
            "width": 640,
            "height": 360,
            "duration": 12,
            "timestamp": 1700000000,
            "webpage_url": f"https://x.com/author/status/{post_id}",
            "extractor_version": "2025.01.01",
        }
    )


def test_inspect_one_video_with_fake_executable(tmp_path: Path) -> None:
    exe = _write_fake_executable(tmp_path / "fake_x", stdout_json=_video_json())
    extractor = YtDlpXExtractor(executable=str(exe))
    inspection = extractor.inspect(
        post_id="123456789", submitted_url="https://x.com/author/status/123456789"
    )
    assert isinstance(inspection, XNormalizedInspection)
    assert inspection.assets[0].media_type is XMediaType.VIDEO
    assert inspection.author_handle == "author"
    assert inspection.post_text == "A cat video"


def test_inspect_authentication_required(tmp_path: Path) -> None:
    payload = json.loads(_video_json())
    payload["availability"] = "needs_auth"
    exe = _write_fake_executable(tmp_path / "fake_x", stdout_json=json.dumps(payload))
    extractor = YtDlpXExtractor(executable=str(exe))
    with pytest.raises(XExtractionError) as ctx:
        extractor.inspect(
            post_id="123456789", submitted_url="https://x.com/a/status/123456789"
        )
    assert ctx.value.code == "X_AUTHENTICATION_REQUIRED"


def test_inspect_malformed_json(tmp_path: Path) -> None:
    exe = _write_fake_executable(tmp_path / "fake_x", stdout_json="not json")
    extractor = YtDlpXExtractor(executable=str(exe))
    with pytest.raises(XExtractionError) as ctx:
        extractor.inspect(
            post_id="123456789", submitted_url="https://x.com/a/status/123456789"
        )
    assert ctx.value.code == "X_EXTRACTOR_MALFORMED"


def test_inspect_nonzero_exit(tmp_path: Path) -> None:
    exe = _write_fake_executable(tmp_path / "fake_x", stdout_json="{}", exit_code=1)
    extractor = YtDlpXExtractor(executable=str(exe))
    with pytest.raises(XExtractionError):
        extractor.inspect(
            post_id="123456789", submitted_url="https://x.com/a/status/123456789"
        )


def test_inspect_too_many_assets(tmp_path: Path) -> None:
    payload = json.loads(_video_json())
    payload["entries"] = [
        {"id": f"a{i}", "ext": "mp4", "width": 10, "height": 10, "duration": 1}
        for i in range(5)
    ]
    exe = _write_fake_executable(tmp_path / "fake_x", stdout_json=json.dumps(payload))
    extractor = YtDlpXExtractor(executable=str(exe))
    with pytest.raises(XExtractionError) as ctx:
        extractor.inspect(
            post_id="123456789", submitted_url="https://x.com/a/status/123456789"
        )
    assert ctx.value.code == "X_TOO_MANY_ASSETS"


def test_inspect_no_supported_media(tmp_path: Path) -> None:
    payload = json.loads(_video_json())
    payload.pop("ext", None)
    payload["formats"] = []
    payload["width"] = None
    payload["vcodec"] = None
    exe = _write_fake_executable(tmp_path / "fake_x", stdout_json=json.dumps(payload))
    extractor = YtDlpXExtractor(executable=str(exe))
    with pytest.raises(XExtractionError) as ctx:
        extractor.inspect(
            post_id="123456789", submitted_url="https://x.com/a/status/123456789"
        )
    assert ctx.value.code == "X_NO_SUPPORTED_MEDIA"


def test_inspect_timeout(tmp_path: Path) -> None:
    exe = _write_fake_executable(tmp_path / "fake_x", stdout_json=_video_json(), delay=2.0)
    extractor = YtDlpXExtractor(
        executable=str(exe), inspect_timeout_seconds=0.2
    )
    with pytest.raises(XExtractionError) as ctx:
        extractor.inspect(
            post_id="123456789", submitted_url="https://x.com/a/status/123456789"
        )
    assert ctx.value.code == "X_DOWNLOAD_TIMEOUT"


def test_download_produces_artifact(tmp_path: Path) -> None:
    staging_root = tmp_path / "xroot"
    staging_root.mkdir(parents=True, exist_ok=True)
    staging_root.chmod(0o700)
    from framenest.infrastructure.x.staging import FilesystemXStaging

    staging = FilesystemXStaging(staging_root)
    exe = _write_fake_executable(tmp_path / "fake_x", artifact_name="artifact.mp4")
    extractor = YtDlpXExtractor(executable=str(exe))
    result = extractor.download(
        post_id="123456789",
        ordinal=0,
        media_type="video",
        expected_mime="video/mp4",
        source_media_key="asset-0",
        stage_key="f" * 32,
        staging=staging,
    )
    assert result.size_bytes > 0
    assert len(result.sha256) == 64


def test_attest_version_with_fake_executable(tmp_path: Path) -> None:
    exe = _write_fake_executable(tmp_path / "fake_x", stdout_json=_video_json())
    extractor = YtDlpXExtractor(executable=str(exe))
    assert extractor.attest_version() == "2025.01.01"
