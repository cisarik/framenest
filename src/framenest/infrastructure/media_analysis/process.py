"""FrameNest-owned bounded subprocess execution."""

from __future__ import annotations

import subprocess
import threading
import time
from collections.abc import Sequence
from dataclasses import dataclass
from typing import IO, Protocol

EXECUTABLE_NOT_FOUND_MESSAGE = "External tool is not available."
PROCESS_TIMEOUT_MESSAGE = "External tool timed out."
PROCESS_OUTPUT_LIMIT_MESSAGE = "External tool output exceeded the allowed limit."
PROCESS_FAILED_MESSAGE = "External tool execution failed."

_READ_CHUNK_SIZE = 8192
_JOIN_TIMEOUT_SECONDS = 5.0
_POLL_INTERVAL_SECONDS = 0.01


class ProcessExecutionError(RuntimeError):
    """Sanitized error raised when subprocess execution fails."""


@dataclass(frozen=True, slots=True)
class ProcessRunResult:
    """Bounded result from one subprocess invocation."""

    returncode: int
    stdout: bytes
    stderr: bytes


class ProcessRunner(Protocol):
    """Injectable subprocess runner for tests and infrastructure adapters."""

    def run(
        self,
        *,
        executable: str,
        argv: Sequence[str],
        timeout_seconds: float,
        stdout_max_bytes: int,
        stderr_max_bytes: int,
    ) -> ProcessRunResult:
        """Execute one argv-based process without a shell."""


def _close_pipe(pipe: IO[bytes] | None) -> None:
    if pipe is None:
        return
    try:
        pipe.close()
    except OSError:
        pass


def _terminate_process(process: subprocess.Popen[bytes]) -> None:
    if process.poll() is not None:
        return
    process.kill()
    try:
        process.wait(timeout=_JOIN_TIMEOUT_SECONDS)
    except subprocess.TimeoutExpired:
        pass


def _read_stdout_bounded(
    pipe: IO[bytes],
    *,
    max_bytes: int,
    overflow_event: threading.Event,
    reader_error: list[BaseException | None],
    retained: list[bytes],
) -> None:
    buffer = bytearray()
    overflow = False
    try:
        while True:
            chunk = pipe.read(_READ_CHUNK_SIZE)
            if not chunk:
                break
            if overflow:
                continue
            next_length = len(buffer) + len(chunk)
            if next_length <= max_bytes:
                buffer.extend(chunk)
                continue
            overflow = True
            overflow_event.set()
            allowed = (max_bytes + _READ_CHUNK_SIZE) - len(buffer)
            if allowed > 0:
                buffer.extend(chunk[:allowed])
    except Exception as exc:
        reader_error[0] = exc
    finally:
        _close_pipe(pipe)
        retained.append(bytes(buffer[:max_bytes]) if len(buffer) > max_bytes else bytes(buffer))


def _read_stderr_bounded(
    pipe: IO[bytes],
    *,
    max_bytes: int,
    reader_error: list[BaseException | None],
    retained: list[bytes],
) -> None:
    buffer = bytearray()
    try:
        while True:
            chunk = pipe.read(_READ_CHUNK_SIZE)
            if not chunk:
                break
            if len(buffer) < max_bytes:
                buffer.extend(chunk[: max_bytes - len(buffer)])
    except Exception as exc:
        reader_error[0] = exc
    finally:
        _close_pipe(pipe)
        retained.append(bytes(buffer))


def _join_reader_threads(*threads: threading.Thread) -> None:
    deadline = time.monotonic() + _JOIN_TIMEOUT_SECONDS
    for thread in threads:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            thread.join(timeout=0)
            continue
        thread.join(timeout=remaining)


def _reader_failure(reader_error: BaseException | None) -> None:
    if reader_error is not None:
        raise ProcessExecutionError(PROCESS_FAILED_MESSAGE) from None


class SubprocessRunner:
    """Standard-library subprocess runner with bounded output retention."""

    def run(
        self,
        *,
        executable: str,
        argv: Sequence[str],
        timeout_seconds: float,
        stdout_max_bytes: int,
        stderr_max_bytes: int,
    ) -> ProcessRunResult:
        if not executable or not argv:
            raise ProcessExecutionError(PROCESS_FAILED_MESSAGE)
        command = (executable, *argv)
        try:
            process = subprocess.Popen(
                command,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        except FileNotFoundError:
            raise ProcessExecutionError(EXECUTABLE_NOT_FOUND_MESSAGE) from None
        except OSError:
            raise ProcessExecutionError(PROCESS_FAILED_MESSAGE) from None

        if process.stdout is None or process.stderr is None:
            _terminate_process(process)
            raise ProcessExecutionError(PROCESS_FAILED_MESSAGE)

        overflow_event = threading.Event()
        stdout_error: list[BaseException | None] = [None]
        stderr_error: list[BaseException | None] = [None]
        stdout_retained: list[bytes] = []
        stderr_retained: list[bytes] = []

        stdout_thread = threading.Thread(
            target=_read_stdout_bounded,
            args=(process.stdout,),
            kwargs={
                "max_bytes": stdout_max_bytes,
                "overflow_event": overflow_event,
                "reader_error": stdout_error,
                "retained": stdout_retained,
            },
            daemon=True,
        )
        stderr_thread = threading.Thread(
            target=_read_stderr_bounded,
            args=(process.stderr,),
            kwargs={
                "max_bytes": stderr_max_bytes,
                "reader_error": stderr_error,
                "retained": stderr_retained,
            },
            daemon=True,
        )
        stdout_thread.start()
        stderr_thread.start()

        deadline = time.monotonic() + timeout_seconds
        try:
            while True:
                if overflow_event.is_set():
                    _terminate_process(process)
                    _join_reader_threads(stdout_thread, stderr_thread)
                    _reader_failure(stdout_error[0])
                    _reader_failure(stderr_error[0])
                    raise ProcessExecutionError(PROCESS_OUTPUT_LIMIT_MESSAGE)

                returncode = process.poll()
                if returncode is not None:
                    _join_reader_threads(stdout_thread, stderr_thread)
                    _reader_failure(stdout_error[0])
                    _reader_failure(stderr_error[0])
                    stdout = stdout_retained[0] if stdout_retained else b""
                    if len(stdout) > stdout_max_bytes:
                        raise ProcessExecutionError(PROCESS_OUTPUT_LIMIT_MESSAGE)
                    return ProcessRunResult(
                        returncode=returncode,
                        stdout=stdout,
                        stderr=stderr_retained[0] if stderr_retained else b"",
                    )

                if time.monotonic() >= deadline:
                    _terminate_process(process)
                    _join_reader_threads(stdout_thread, stderr_thread)
                    _reader_failure(stdout_error[0])
                    _reader_failure(stderr_error[0])
                    raise ProcessExecutionError(PROCESS_TIMEOUT_MESSAGE)

                time.sleep(_POLL_INTERVAL_SECONDS)
        except ProcessExecutionError:
            raise
        except Exception:
            _terminate_process(process)
            _join_reader_threads(stdout_thread, stderr_thread)
            raise ProcessExecutionError(PROCESS_FAILED_MESSAGE) from None
