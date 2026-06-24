"""Unit tests for bounded subprocess execution."""

from __future__ import annotations

import sys
import threading
import time
from collections.abc import Sequence

import pytest

import framenest.infrastructure.media_analysis.process as process_module
from framenest.infrastructure.media_analysis.process import (
    EXECUTABLE_NOT_FOUND_MESSAGE,
    PROCESS_FAILED_MESSAGE,
    PROCESS_OUTPUT_LIMIT_MESSAGE,
    PROCESS_TIMEOUT_MESSAGE,
    ProcessExecutionError,
    ProcessRunResult,
    SubprocessRunner,
    _STDERR_READER_THREAD_NAME,
    _STDOUT_READER_THREAD_NAME,
)

SENSITIVE_MEDIA_PATH = "/sensitive-example/private-media.mp4"

_ENDLESS_STDOUT_SCRIPT = (
    "import sys\n"
    "while True:\n"
    "    sys.stdout.write('x' * 4096)\n"
    "    sys.stdout.flush()\n"
)

_FINITE_OVERSIZED_STDOUT_SCRIPT = (
    "import sys\n"
    "sys.stdout.write('x' * 200)\n"
    "sys.stdout.flush()\n"
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


def _alive_media_analysis_reader_threads() -> list[threading.Thread]:
    return [
        thread
        for thread in threading.enumerate()
        if thread.name in {_STDOUT_READER_THREAD_NAME, _STDERR_READER_THREAD_NAME}
    ]


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
    assert _alive_media_analysis_reader_threads() == []


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
    assert _alive_media_analysis_reader_threads() == []


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
    assert _alive_media_analysis_reader_threads() == []


def test_subprocess_runner_rejects_finite_fast_oversized_stdout() -> None:
    runner = SubprocessRunner()
    with pytest.raises(ProcessExecutionError, match=PROCESS_OUTPUT_LIMIT_MESSAGE):
        runner.run(
            executable=sys.executable,
            argv=["-c", _FINITE_OVERSIZED_STDOUT_SCRIPT],
            timeout_seconds=5.0,
            stdout_max_bytes=16,
            stderr_max_bytes=64,
        )
    assert _alive_media_analysis_reader_threads() == []


def test_subprocess_runner_detects_overflow_published_during_completion_join(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured_stdout_state: list[process_module._ReaderState] = []
    original_read_stdout = process_module._read_stdout_bounded

    def capture_stdout_state(
        pipe: object,
        *,
        max_bytes: int,
        state: process_module._ReaderState,
        wake_event: threading.Event,
    ) -> None:
        captured_stdout_state.append(state)
        return original_read_stdout(
            pipe,
            max_bytes=max_bytes,
            state=state,
            wake_event=wake_event,
        )

    original_thread_join = threading.Thread.join

    def join_with_late_overflow(self: threading.Thread, timeout: float | None = None) -> None:
        if self.name == _STDOUT_READER_THREAD_NAME and captured_stdout_state:
            captured_stdout_state[0].overflow = True
        return original_thread_join(self, timeout=timeout)

    monkeypatch.setattr(process_module, "_read_stdout_bounded", capture_stdout_state)
    monkeypatch.setattr(threading.Thread, "join", join_with_late_overflow)

    runner = SubprocessRunner()
    with pytest.raises(ProcessExecutionError, match=PROCESS_OUTPUT_LIMIT_MESSAGE):
        runner.run(
            executable=sys.executable,
            argv=["-c", "print('ok')"],
            timeout_seconds=5.0,
            stdout_max_bytes=64,
            stderr_max_bytes=64,
        )
    assert _alive_media_analysis_reader_threads() == []


def test_subprocess_runner_rejects_unfinished_reader_after_join_deadline(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    reader_release = threading.Event()
    original_read_stdout = process_module._read_stdout_bounded

    def blocking_stdout_read(
        pipe: object,
        *,
        max_bytes: int,
        state: process_module._ReaderState,
        wake_event: threading.Event,
    ) -> None:
        try:
            if not reader_release.wait(timeout=2.0):
                state.error = RuntimeError("reader cleanup missed")
        finally:
            process_module._close_pipe(pipe)  # type: ignore[arg-type]
            state.completed.set()

    monkeypatch.setattr(process_module, "_read_stdout_bounded", blocking_stdout_read)
    monkeypatch.setattr(process_module, "_JOIN_TIMEOUT_SECONDS", 0.05)

    runner = SubprocessRunner()
    try:
        with pytest.raises(ProcessExecutionError, match=PROCESS_FAILED_MESSAGE) as exc_info:
            runner.run(
                executable=sys.executable,
                argv=["-c", "print('ok')"],
                timeout_seconds=5.0,
                stdout_max_bytes=64,
                stderr_max_bytes=64,
            )
        message = str(exc_info.value)
        assert SENSITIVE_MEDIA_PATH not in message
        assert "reader cleanup missed" not in message
    finally:
        reader_release.set()

    deadline = time.monotonic() + 2.0
    while _alive_media_analysis_reader_threads() and time.monotonic() < deadline:
        time.sleep(0.01)
    assert _alive_media_analysis_reader_threads() == []


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
    assert _alive_media_analysis_reader_threads() == []


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
    assert _alive_media_analysis_reader_threads() == []


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
    assert _alive_media_analysis_reader_threads() == []


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
    assert _alive_media_analysis_reader_threads() == []


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
    assert _alive_media_analysis_reader_threads() == []


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


def test_subprocess_runner_maps_reader_failure_to_sanitized_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def failing_stdout_read(
        pipe: object,
        *,
        max_bytes: int,
        state: process_module._ReaderState,
        wake_event: threading.Event,
    ) -> None:
        process_module._close_pipe(pipe)  # type: ignore[arg-type]
        state.error = RuntimeError("raw reader failure")
        state.completed.set()

    monkeypatch.setattr(process_module, "_read_stdout_bounded", failing_stdout_read)

    runner = SubprocessRunner()
    with pytest.raises(ProcessExecutionError, match=PROCESS_FAILED_MESSAGE) as exc_info:
        runner.run(
            executable=sys.executable,
            argv=["-c", "print('ok')"],
            timeout_seconds=5.0,
            stdout_max_bytes=64,
            stderr_max_bytes=64,
        )
    assert "raw reader failure" not in str(exc_info.value)
    assert _alive_media_analysis_reader_threads() == []


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
