"""Unit tests for bounded subprocess execution."""

from __future__ import annotations

import sys
import time
from collections.abc import Sequence

import pytest

from framenest.infrastructure.media_analysis.process import (
    EXECUTABLE_NOT_FOUND_MESSAGE,
    PROCESS_OUTPUT_LIMIT_MESSAGE,
    PROCESS_TIMEOUT_MESSAGE,
    ProcessExecutionError,
    ProcessRunResult,
    SubprocessRunner,
)

SENSITIVE_MEDIA_PATH = "/sensitive-example/private-media.mp4"

_ENDLESS_STDOUT_SCRIPT = (
    "import sys\n"
    "while True:\n"
    "    sys.stdout.write('x' * 4096)\n"
    "    sys.stdout.flush()\n"
)

_LARGE_STDERR_SCRIPT = (
    "import sys\n"
    "sys.stderr.write('e' * 10000)\n"
    "sys.stdout.write('ok')\n"
)

_COMBINED_PRESSURE_SCRIPT = (
    "import sys\n"
    "import threading\n"
    "def write_stderr():\n"
    "    sys.stderr.write('e' * 10000)\n"
    "threading.Thread(target=write_stderr, daemon=True).start()\n"
    "while True:\n"
    "    sys.stdout.write('x' * 4096)\n"
    "    sys.stdout.flush()\n"
)


class _FakeRunner:
    def __init__(self, result: ProcessRunResult | None = None, error: Exception | None = None) -> None:
        self.result = result
        self.error = error
        self.calls: list[dict[str, object]] = []

    def run(
        self,
        *,
        executable: str,
        argv: Sequence[str],
        timeout_seconds: float,
        stdout_max_bytes: int,
        stderr_max_bytes: int,
    ) -> ProcessRunResult:
        self.calls.append(
            {
                "executable": executable,
                "argv": tuple(argv),
                "timeout_seconds": timeout_seconds,
                "stdout_max_bytes": stdout_max_bytes,
                "stderr_max_bytes": stderr_max_bytes,
            }
        )
        if self.error is not None:
            raise self.error
        assert self.result is not None
        return self.result


def test_fake_runner_records_argv_without_shell() -> None:
    runner = _FakeRunner(ProcessRunResult(returncode=0, stdout=b"ok", stderr=b""))
    runner.run(
        executable="/bin/echo",
        argv=["hello"],
        timeout_seconds=1.0,
        stdout_max_bytes=10,
        stderr_max_bytes=10,
    )
    assert runner.calls[0]["argv"] == ("hello",)


def test_subprocess_runner_executes_without_shell() -> None:
    runner = SubprocessRunner()
    result = runner.run(
        executable=sys.executable,
        argv=["-c", "print('ok')"],
        timeout_seconds=5.0,
        stdout_max_bytes=64,
        stderr_max_bytes=64,
    )
    assert result.returncode == 0
    assert result.stdout.strip() == b"ok"


def test_subprocess_runner_timeout_terminates_process() -> None:
    runner = SubprocessRunner()
    with pytest.raises(ProcessExecutionError, match=PROCESS_TIMEOUT_MESSAGE):
        runner.run(
            executable=sys.executable,
            argv=["-c", "import time; time.sleep(5)"],
            timeout_seconds=0.2,
            stdout_max_bytes=64,
            stderr_max_bytes=64,
        )


def test_subprocess_runner_enforces_stdout_limit() -> None:
    runner = SubprocessRunner()
    with pytest.raises(ProcessExecutionError, match=PROCESS_OUTPUT_LIMIT_MESSAGE):
        runner.run(
            executable=sys.executable,
            argv=["-c", "print('x' * 200)"],
            timeout_seconds=5.0,
            stdout_max_bytes=16,
            stderr_max_bytes=64,
        )


def test_subprocess_runner_actively_bounds_endless_stdout_before_timeout() -> None:
    runner = SubprocessRunner()
    started = time.monotonic()
    with pytest.raises(ProcessExecutionError, match=PROCESS_OUTPUT_LIMIT_MESSAGE) as exc_info:
        runner.run(
            executable=sys.executable,
            argv=["-c", _ENDLESS_STDOUT_SCRIPT],
            timeout_seconds=5.0,
            stdout_max_bytes=64,
            stderr_max_bytes=64,
        )
    elapsed = time.monotonic() - started
    assert PROCESS_TIMEOUT_MESSAGE not in str(exc_info.value)
    assert elapsed < 4.0


def test_subprocess_runner_drains_stderr_concurrently_without_deadlock() -> None:
    runner = SubprocessRunner()
    result = runner.run(
        executable=sys.executable,
        argv=["-c", _LARGE_STDERR_SCRIPT],
        timeout_seconds=5.0,
        stdout_max_bytes=64,
        stderr_max_bytes=32,
    )
    assert result.returncode == 0
    assert result.stdout.strip() == b"ok"
    assert len(result.stderr) == 32
    assert result.stderr == b"e" * 32


def test_subprocess_runner_handles_combined_stream_pressure_without_deadlock() -> None:
    runner = SubprocessRunner()
    with pytest.raises(ProcessExecutionError, match=PROCESS_OUTPUT_LIMIT_MESSAGE):
        runner.run(
            executable=sys.executable,
            argv=["-c", _COMBINED_PRESSURE_SCRIPT],
            timeout_seconds=5.0,
            stdout_max_bytes=64,
            stderr_max_bytes=32,
        )


def test_subprocess_runner_retains_bounded_stderr() -> None:
    runner = SubprocessRunner()
    result = runner.run(
        executable=sys.executable,
        argv=["-c", "import sys; sys.stderr.write('e' * 200)"],
        timeout_seconds=5.0,
        stdout_max_bytes=64,
        stderr_max_bytes=32,
    )
    assert result.returncode == 0
    assert len(result.stderr) == 32


def test_subprocess_runner_preserves_bounded_nonzero_exit() -> None:
    runner = SubprocessRunner()
    result = runner.run(
        executable=sys.executable,
        argv=["-c", "import sys; sys.exit(3)"],
        timeout_seconds=5.0,
        stdout_max_bytes=64,
        stderr_max_bytes=64,
    )
    assert result.returncode == 3


def test_subprocess_runner_maps_missing_executable() -> None:
    runner = SubprocessRunner()
    with pytest.raises(ProcessExecutionError, match=EXECUTABLE_NOT_FOUND_MESSAGE):
        runner.run(
            executable="/nonexistent/framenest-tool",
            argv=["-version"],
            timeout_seconds=1.0,
            stdout_max_bytes=64,
            stderr_max_bytes=64,
        )


def test_process_errors_do_not_leak_sensitive_argv_paths() -> None:
    runner = SubprocessRunner()
    with pytest.raises(ProcessExecutionError) as exc_info:
        runner.run(
            executable="/nonexistent/framenest-media-tool",
            argv=["-i", SENSITIVE_MEDIA_PATH],
            timeout_seconds=1.0,
            stdout_max_bytes=64,
            stderr_max_bytes=64,
        )
    message = str(exc_info.value)
    assert SENSITIVE_MEDIA_PATH not in message
