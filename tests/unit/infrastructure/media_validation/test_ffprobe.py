"""Unit tests for bounded upload media validation."""

from __future__ import annotations

import json
from collections.abc import Sequence

import pytest

from framenest.application.ports.quarantine_storage import QuarantineStateInconsistentError
from framenest.application.ports.upload_media_validation import (
    UploadMediaValidationInfrastructureError,
    UploadMediaValidationRejectedError,
)
from framenest.application.upload_validation import (
    UPLOAD_VALIDATION_AMBIGUOUS_MEDIA_TYPE,
    UPLOAD_VALIDATION_INVALID_MEDIA,
    UPLOAD_VALIDATION_MEDIA_POLICY_LIMIT,
    UPLOAD_VALIDATION_OUTPUT_LIMIT,
    UPLOAD_VALIDATION_TIMEOUT,
    UPLOAD_VALIDATION_TOOL_UNAVAILABLE,
    UPLOAD_VALIDATION_UNSUPPORTED_MEDIA_TYPE,
)
from framenest.domain.uploads import UploadValidatedFormat, UploadValidatedMediaKind
from framenest.infrastructure.media_analysis.process import (
    EXECUTABLE_NOT_FOUND_MESSAGE,
    PROCESS_OUTPUT_LIMIT_MESSAGE,
    PROCESS_TIMEOUT_MESSAGE,
    ProcessExecutionError,
    ProcessRunResult,
)
from framenest.infrastructure.media_validation.ffprobe import BoundedUploadMediaValidator


class _Reader:
    def __init__(self, payload: bytes) -> None:
        self._payload = payload
        self._offset = 0
        self.closed = False

    @property
    def size_bytes(self) -> int:
        return len(self._payload)

    @property
    def file_descriptor(self) -> int:
        return 123

    def read(self, size: int) -> bytes:
        chunk = self._payload[self._offset : self._offset + size]
        self._offset += len(chunk)
        return chunk

    def seek_start(self) -> None:
        self._offset = 0

    def verify_still_consistent(self) -> None:
        return None

    def close(self) -> None:
        self.closed = True


class _Runner:
    def __init__(
        self,
        result: ProcessRunResult | None = None,
        error: ProcessExecutionError | None = None,
    ) -> None:
        self._result = result
        self._error = error
        self.calls: list[dict[str, object]] = []

    def run(
        self,
        *,
        executable: str,
        argv: Sequence[str],
        timeout_seconds: float,
        stdout_max_bytes: int,
        stderr_max_bytes: int,
        pass_fds: Sequence[int] = (),
    ) -> ProcessRunResult:
        self.calls.append(
            {
                "executable": executable,
                "argv": tuple(argv),
                "pass_fds": tuple(pass_fds),
                "stdout_max_bytes": stdout_max_bytes,
                "stderr_max_bytes": stderr_max_bytes,
            }
        )
        if self._error is not None:
            raise self._error
        assert self._result is not None
        return self._result


def _gif_bytes(signature: bytes = b"GIF89a", *, width: int = 1, height: int = 1) -> bytes:
    return signature + width.to_bytes(2, "little") + height.to_bytes(2, "little") + b"\x80"


def _mp4_bytes() -> bytes:
    return b"\x00\x00\x00\x14ftypisom\x00\x00\x02\x00mp42"


def _probe_payload(
    *,
    format_name: str,
    codec: str,
    width: int = 1,
    height: int = 1,
    include_video: bool = True,
    extra_streams: int = 0,
    duration: str = "1.0",
) -> bytes:
    streams: list[dict[str, object]] = []
    if include_video:
        streams.append(
            {
                "codec_type": "video",
                "codec_name": codec,
                "width": width,
                "height": height,
                "disposition": {"attached_pic": 0},
            }
        )
    streams.extend({"codec_type": "audio", "codec_name": "aac"} for _ in range(extra_streams))
    return json.dumps(
        {
            "streams": streams,
            "format": {"format_name": format_name, "duration": duration},
        }
    ).encode("utf-8")


def _validator(stdout: bytes) -> tuple[BoundedUploadMediaValidator, _Runner]:
    runner = _Runner(ProcessRunResult(returncode=0, stdout=stdout, stderr=b""))
    return BoundedUploadMediaValidator(runner, ffprobe_executable="/usr/bin/ffprobe"), runner


def test_valid_gif89a_is_accepted_from_content_not_filename_or_mime() -> None:
    validator, runner = _validator(_probe_payload(format_name="gif", codec="gif"))

    evidence = validator.validate(_Reader(_gif_bytes()))

    assert evidence.media_kind is UploadValidatedMediaKind.ANIMATED_IMAGE
    assert evidence.media_format is UploadValidatedFormat.GIF
    assert runner.calls[0]["pass_fds"] == (123,)
    assert "/dev/fd/123" in runner.calls[0]["argv"]


def test_valid_gif87a_is_accepted() -> None:
    validator, _runner = _validator(_probe_payload(format_name="gif", codec="gif"))

    evidence = validator.validate(_Reader(_gif_bytes(b"GIF87a")))

    assert evidence.media_format is UploadValidatedFormat.GIF


def test_valid_mp4_with_visual_stream_is_accepted() -> None:
    validator, _runner = _validator(
        _probe_payload(format_name="mov,mp4,m4a,3gp,3g2,mj2", codec="h264")
    )

    evidence = validator.validate(_Reader(_mp4_bytes()))

    assert evidence.media_kind is UploadValidatedMediaKind.VIDEO
    assert evidence.media_format is UploadValidatedFormat.MP4


@pytest.mark.parametrize(
    ("payload", "stdout", "code"),
    [
        (b"not-media", _probe_payload(format_name="gif", codec="gif"), UPLOAD_VALIDATION_UNSUPPORTED_MEDIA_TYPE),
        (_gif_bytes()[:8], _probe_payload(format_name="gif", codec="gif"), UPLOAD_VALIDATION_INVALID_MEDIA),
        (_gif_bytes(), _probe_payload(format_name="mov,mp4,m4a", codec="h264"), UPLOAD_VALIDATION_AMBIGUOUS_MEDIA_TYPE),
        (_mp4_bytes(), _probe_payload(format_name="mov,mp4,m4a", codec="h264", include_video=False), UPLOAD_VALIDATION_INVALID_MEDIA),
        (_mp4_bytes(), _probe_payload(format_name="gif", codec="gif"), UPLOAD_VALIDATION_AMBIGUOUS_MEDIA_TYPE),
        (_mp4_bytes(), _probe_payload(format_name="matroska,webm", codec="h264"), UPLOAD_VALIDATION_UNSUPPORTED_MEDIA_TYPE),
        (_mp4_bytes(), _probe_payload(format_name="mov,mp4,m4a", codec="h264", width=9000), UPLOAD_VALIDATION_MEDIA_POLICY_LIMIT),
        (_mp4_bytes(), _probe_payload(format_name="mov,mp4,m4a", codec="h264", extra_streams=20), UPLOAD_VALIDATION_MEDIA_POLICY_LIMIT),
        (_mp4_bytes(), _probe_payload(format_name="mov,mp4,m4a", codec="h264", duration="999999"), UPLOAD_VALIDATION_MEDIA_POLICY_LIMIT),
        (_mp4_bytes(), b"{", UPLOAD_VALIDATION_INVALID_MEDIA),
    ],
)
def test_invalid_or_unsupported_media_is_rejected_with_sanitized_code(
    payload: bytes,
    stdout: bytes,
    code: str,
) -> None:
    validator, _runner = _validator(stdout)

    with pytest.raises(UploadMediaValidationRejectedError) as error:
        validator.validate(_Reader(payload))

    assert error.value.failure_code == code


@pytest.mark.parametrize(
    ("message", "error_type", "code"),
    [
        (PROCESS_TIMEOUT_MESSAGE, UploadMediaValidationRejectedError, UPLOAD_VALIDATION_TIMEOUT),
        (
            PROCESS_OUTPUT_LIMIT_MESSAGE,
            UploadMediaValidationRejectedError,
            UPLOAD_VALIDATION_OUTPUT_LIMIT,
        ),
        (
            EXECUTABLE_NOT_FOUND_MESSAGE,
            UploadMediaValidationInfrastructureError,
            UPLOAD_VALIDATION_TOOL_UNAVAILABLE,
        ),
    ],
)
def test_process_errors_are_sanitized(message: str, error_type: type[Exception], code: str) -> None:
    runner = _Runner(error=ProcessExecutionError(message))
    validator = BoundedUploadMediaValidator(runner, ffprobe_executable="/usr/bin/ffprobe")

    with pytest.raises(error_type) as error:
        validator.validate(_Reader(_mp4_bytes()))

    assert getattr(error.value, "failure_code") == code


def test_reader_io_error_is_sanitized_as_infrastructure_failure() -> None:
    class _BrokenReader(_Reader):
        def read(self, size: int) -> bytes:
            raise QuarantineStateInconsistentError("private/path")

    validator, _runner = _validator(_probe_payload(format_name="gif", codec="gif"))

    with pytest.raises(QuarantineStateInconsistentError):
        validator.validate(_BrokenReader(_gif_bytes()))
