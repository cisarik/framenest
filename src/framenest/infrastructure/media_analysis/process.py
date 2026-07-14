"""FrameNest-owned bounded subprocess execution."""

from __future__ import annotations

import os
import signal
import subprocess
import threading
import time
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import IO, Protocol

EXECUTABLE_NOT_FOUND_MESSAGE = "External tool is not available."
PROCESS_TIMEOUT_MESSAGE = "External tool timed out."
PROCESS_OUTPUT_LIMIT_MESSAGE = "External tool output exceeded the allowed limit."
PROCESS_FAILED_MESSAGE = "External tool execution failed."

_READ_CHUNK_SIZE = 8192
_JOIN_TIMEOUT_SECONDS = 5.0
_TERMINATE_GRACE_SECONDS = 0.2
_POLL_INTERVAL_SECONDS = 0.01
_STDOUT_READER_THREAD_NAME = "framenest-media-analysis-stdout-reader"
_STDERR_READER_THREAD_NAME = "framenest-media-analysis-stderr-reader"


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
        pass_fds: Sequence[int] = (),
    ) -> ProcessRunResult:
        """Execute one argv-based process without a shell."""


@dataclass(slots=True)
class _ReaderState:
    """Bounded completion state for one pipe reader thread."""

    retained: bytes = b""
    error: BaseException | None = None
    overflow: bool = False
    completed: threading.Event = field(default_factory=threading.Event)


def _close_pipe(pipe: IO[bytes] | None) -> None:
    if pipe is None:
        return
    try:
        pipe.close()
    except OSError:
        pass


def _terminate_process(process: subprocess.Popen[bytes]) -> None:
    _signal_process_tree(process, signal.SIGTERM)
    if process.poll() is None:
        try:
            process.wait(timeout=_TERMINATE_GRACE_SECONDS)
        except subprocess.TimeoutExpired:
            pass
    _signal_process_tree(process, signal.SIGKILL)
    if process.poll() is None:
        try:
            process.wait(timeout=_JOIN_TIMEOUT_SECONDS)
        except subprocess.TimeoutExpired:
            pass


def _signal_process_tree(process: subprocess.Popen[bytes], sig: signal.Signals) -> None:
    if hasattr(os, "killpg"):
        try:
            os.killpg(process.pid, sig)
            return
        except ProcessLookupError:
            return
        except OSError:
            pass
    try:
        if sig is signal.SIGTERM:
            process.terminate()
        else:
            process.kill()
    except ProcessLookupError:
        return


def _read_stdout_bounded(
    pipe: IO[bytes],
    *,
    max_bytes: int,
    state: _ReaderState,
    wake_event: threading.Event,
) -> None:
    buffer = bytearray()
    discard_mode = False
    try:
        while True:
            chunk = pipe.read(_READ_CHUNK_SIZE)
            if not chunk:
                break
            if discard_mode:
                continue
            next_length = len(buffer) + len(chunk)
            if next_length <= max_bytes:
                buffer.extend(chunk)
                continue
            discard_mode = True
            state.overflow = True
            wake_event.set()
            allowed = (max_bytes + _READ_CHUNK_SIZE) - len(buffer)
            if allowed > 0:
                buffer.extend(chunk[:allowed])
    except Exception as exc:
        state.error = exc
    finally:
        _close_pipe(pipe)
        state.retained = bytes(buffer[:max_bytes]) if len(buffer) > max_bytes else bytes(buffer)
        state.completed.set()


def _read_stderr_bounded(
    pipe: IO[bytes],
    *,
    max_bytes: int,
    state: _ReaderState,
    wake_event: threading.Event,
) -> None:
    buffer = bytearray()
    discard_mode = False
    try:
        while True:
            chunk = pipe.read(_READ_CHUNK_SIZE)
            if not chunk:
                break
            if discard_mode:
                continue
            next_length = len(buffer) + len(chunk)
            if next_length <= max_bytes:
                buffer.extend(chunk)
                continue
            discard_mode = True
            state.overflow = True
            wake_event.set()
            remaining = max_bytes - len(buffer)
            if remaining > 0:
                buffer.extend(chunk[:remaining])
    except Exception as exc:
        state.error = exc
    finally:
        _close_pipe(pipe)
        state.retained = bytes(buffer)
        state.completed.set()


def _await_reader_threads(*threads: threading.Thread) -> None:
    deadline = time.monotonic() + _JOIN_TIMEOUT_SECONDS
    for thread in threads:
        remaining = deadline - time.monotonic()
        if remaining > 0:
            thread.join(timeout=remaining)
    if any(thread.is_alive() for thread in threads):
        raise ProcessExecutionError(PROCESS_FAILED_MESSAGE)


def _raise_reader_error(state: _ReaderState) -> None:
    if state.error is not None:
        raise ProcessExecutionError(PROCESS_FAILED_MESSAGE)


def _raise_output_overflow(*states: _ReaderState) -> None:
    if any(state.overflow for state in states):
        raise ProcessExecutionError(PROCESS_OUTPUT_LIMIT_MESSAGE)


def _finalize_readers(
    *,
    stdout_thread: threading.Thread,
    stderr_thread: threading.Thread,
    stdout_state: _ReaderState,
    stderr_state: _ReaderState,
) -> None:
    _await_reader_threads(stdout_thread, stderr_thread)
    _raise_reader_error(stderr_state)
    _raise_reader_error(stdout_state)
    _raise_output_overflow(stdout_state, stderr_state)


def _handle_output_overflow(
    process: subprocess.Popen[bytes],
    *,
    stdout_thread: threading.Thread,
    stderr_thread: threading.Thread,
    stdout_state: _ReaderState,
    stderr_state: _ReaderState,
) -> None:
    _terminate_process(process)
    _finalize_readers(
        stdout_thread=stdout_thread,
        stderr_thread=stderr_thread,
        stdout_state=stdout_state,
        stderr_state=stderr_state,
    )
    raise ProcessExecutionError(PROCESS_OUTPUT_LIMIT_MESSAGE)


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
        pass_fds: Sequence[int] = (),
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
                pass_fds=tuple(pass_fds),
                start_new_session=True,
            )
        except FileNotFoundError:
            raise ProcessExecutionError(EXECUTABLE_NOT_FOUND_MESSAGE) from None
        except OSError:
            raise ProcessExecutionError(PROCESS_FAILED_MESSAGE) from None

        if process.stdout is None or process.stderr is None:
            _terminate_process(process)
            raise ProcessExecutionError(PROCESS_FAILED_MESSAGE)

        output_wake = threading.Event()
        stdout_state = _ReaderState()
        stderr_state = _ReaderState()

        stdout_thread = threading.Thread(
            target=_read_stdout_bounded,
            args=(process.stdout,),
            kwargs={
                "max_bytes": stdout_max_bytes,
                "state": stdout_state,
                "wake_event": output_wake,
            },
            name=_STDOUT_READER_THREAD_NAME,
            daemon=True,
        )
        stderr_thread = threading.Thread(
            target=_read_stderr_bounded,
            args=(process.stderr,),
            kwargs={
                "max_bytes": stderr_max_bytes,
                "state": stderr_state,
                "wake_event": output_wake,
            },
            name=_STDERR_READER_THREAD_NAME,
            daemon=True,
        )
        stdout_thread.start()
        stderr_thread.start()

        deadline = time.monotonic() + timeout_seconds
        try:
            while True:
                if stdout_state.overflow or stderr_state.overflow or output_wake.is_set():
                    _handle_output_overflow(
                        process,
                        stdout_thread=stdout_thread,
                        stderr_thread=stderr_thread,
                        stdout_state=stdout_state,
                        stderr_state=stderr_state,
                    )

                returncode = process.poll()
                if returncode is not None:
                    _finalize_readers(
                        stdout_thread=stdout_thread,
                        stderr_thread=stderr_thread,
                        stdout_state=stdout_state,
                        stderr_state=stderr_state,
                    )
                    return ProcessRunResult(
                        returncode=returncode,
                        stdout=stdout_state.retained,
                        stderr=stderr_state.retained,
                    )

                if time.monotonic() >= deadline:
                    _terminate_process(process)
                    _finalize_readers(
                        stdout_thread=stdout_thread,
                        stderr_thread=stderr_thread,
                        stdout_state=stdout_state,
                        stderr_state=stderr_state,
                    )
                    raise ProcessExecutionError(PROCESS_TIMEOUT_MESSAGE)

                output_wake.wait(timeout=_POLL_INTERVAL_SECONDS)
        except ProcessExecutionError:
            raise
        except Exception:
            _terminate_process(process)
            try:
                _finalize_readers(
                    stdout_thread=stdout_thread,
                    stderr_thread=stderr_thread,
                    stdout_state=stdout_state,
                    stderr_state=stderr_state,
                )
            except ProcessExecutionError:
                pass
            raise ProcessExecutionError(PROCESS_FAILED_MESSAGE) from None
