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


def _process_group_exists(pgid: int) -> bool:
    try:
        os.killpg(pgid, 0)
    except ProcessLookupError:
        return False
    except OSError:
        raise ProcessExecutionError(PROCESS_FAILED_MESSAGE) from None
    return True


def _signal_process_group(pgid: int, sig: signal.Signals) -> None:
    try:
        os.killpg(pgid, sig)
    except ProcessLookupError:
        return
    except OSError:
        raise ProcessExecutionError(PROCESS_FAILED_MESSAGE) from None


def _wait_for_process_group_absence(pgid: int, *, timeout_seconds: float) -> bool:
    deadline = time.monotonic() + timeout_seconds
    while True:
        if not _process_group_exists(pgid):
            return True
        if time.monotonic() >= deadline:
            return False
        time.sleep(_POLL_INTERVAL_SECONDS)


def _wait_for_direct_child(process: subprocess.Popen[bytes], *, timeout_seconds: float) -> bool:
    if process.poll() is not None:
        return True
    try:
        process.wait(timeout=timeout_seconds)
    except subprocess.TimeoutExpired:
        return process.poll() is not None
    return True


def _poll_direct_child_without_reaping(process: subprocess.Popen[bytes]) -> int | None:
    if process.returncode is not None:
        return process.returncode
    if not all(
        hasattr(os, name)
        for name in ("waitid", "P_PID", "WEXITED", "WNOHANG", "WNOWAIT")
        + ("CLD_EXITED", "CLD_KILLED", "CLD_DUMPED")
    ):
        return process.poll()
    try:
        status = os.waitid(
            os.P_PID,
            process.pid,
            os.WEXITED | os.WNOHANG | os.WNOWAIT,
        )
    except ChildProcessError:
        return process.poll()
    if status is None:
        return None
    if status.si_code == os.CLD_EXITED:
        return int(status.si_status)
    if status.si_code in {os.CLD_KILLED, os.CLD_DUMPED}:
        return -int(status.si_status)
    return process.poll()


def _cleanup_owned_process_group(process: subprocess.Popen[bytes]) -> None:
    pgid = process.pid
    if pgid <= 0:
        raise ProcessExecutionError(PROCESS_FAILED_MESSAGE)

    group_exists = _process_group_exists(pgid)
    if group_exists:
        _signal_process_group(pgid, signal.SIGTERM)
        _wait_for_direct_child(process, timeout_seconds=_TERMINATE_GRACE_SECONDS)
        group_exists = not _wait_for_process_group_absence(
            pgid,
            timeout_seconds=_TERMINATE_GRACE_SECONDS,
        )

    if group_exists:
        _signal_process_group(pgid, signal.SIGKILL)
        _wait_for_direct_child(process, timeout_seconds=_JOIN_TIMEOUT_SECONDS)
        if not _wait_for_process_group_absence(pgid, timeout_seconds=_JOIN_TIMEOUT_SECONDS):
            raise ProcessExecutionError(PROCESS_FAILED_MESSAGE)

    if not _wait_for_direct_child(process, timeout_seconds=_JOIN_TIMEOUT_SECONDS):
        raise ProcessExecutionError(PROCESS_FAILED_MESSAGE)


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


def _cleanup_owned_group_and_finalize_readers(
    process: subprocess.Popen[bytes],
    *,
    stdout_thread: threading.Thread,
    stderr_thread: threading.Thread,
    stdout_state: _ReaderState,
    stderr_state: _ReaderState,
) -> None:
    cleanup_error: ProcessExecutionError | None = None
    try:
        _cleanup_owned_process_group(process)
    except ProcessExecutionError as exc:
        cleanup_error = exc
        _close_pipe(process.stdout)
        _close_pipe(process.stderr)

    try:
        _finalize_readers(
            stdout_thread=stdout_thread,
            stderr_thread=stderr_thread,
            stdout_state=stdout_state,
            stderr_state=stderr_state,
        )
    except ProcessExecutionError:
        if cleanup_error is not None:
            raise cleanup_error
        raise

    if cleanup_error is not None:
        raise cleanup_error


def _handle_output_overflow(
    process: subprocess.Popen[bytes],
    *,
    stdout_thread: threading.Thread,
    stderr_thread: threading.Thread,
    stdout_state: _ReaderState,
    stderr_state: _ReaderState,
) -> None:
    _cleanup_owned_group_and_finalize_readers(
        process,
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
            _cleanup_owned_process_group(process)
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

                returncode = _poll_direct_child_without_reaping(process)
                if returncode is not None:
                    _cleanup_owned_group_and_finalize_readers(
                        process,
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
                    _cleanup_owned_group_and_finalize_readers(
                        process,
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
            try:
                _cleanup_owned_process_group(process)
            except ProcessExecutionError:
                pass
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
