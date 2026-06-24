"""FrameNest-owned bounded subprocess execution."""

from __future__ import annotations

import subprocess
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol

EXECUTABLE_NOT_FOUND_MESSAGE = "External tool is not available."
PROCESS_TIMEOUT_MESSAGE = "External tool timed out."
PROCESS_OUTPUT_LIMIT_MESSAGE = "External tool output exceeded the allowed limit."
PROCESS_FAILED_MESSAGE = "External tool execution failed."


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
        try:
            stdout, stderr = process.communicate(timeout=timeout_seconds)
        except subprocess.TimeoutExpired:
            process.kill()
            process.communicate()
            raise ProcessExecutionError(PROCESS_TIMEOUT_MESSAGE) from None
        except FileNotFoundError:
            raise ProcessExecutionError(EXECUTABLE_NOT_FOUND_MESSAGE) from None
        except OSError:
            raise ProcessExecutionError(PROCESS_FAILED_MESSAGE) from None

        if len(stdout) > stdout_max_bytes:
            raise ProcessExecutionError(PROCESS_OUTPUT_LIMIT_MESSAGE)
        return ProcessRunResult(
            returncode=process.returncode or 0,
            stdout=stdout,
            stderr=stderr[:stderr_max_bytes],
        )
