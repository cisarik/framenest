"""Resolve host tools for tests, including macOS Homebrew locations.

The AP-sanitized execution envelope fixes PATH to ``/usr/bin:/bin``. On macOS
development hosts the project tools (ffmpeg, ffprobe, node, fish, poetry) live
in Homebrew directories. Tests use this helper so subprocesses can find them
without changing the sanitized environment itself.
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path

FALLBACK_TOOL_DIRECTORIES = ("/opt/homebrew/bin", "/usr/local/bin")


def resolve_tool(name: str) -> str:
    """Return an absolute executable path, or raise FileNotFoundError."""
    found = shutil.which(name)
    if found:
        return found
    for directory in FALLBACK_TOOL_DIRECTORIES:
        candidate = Path(directory) / name
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return str(candidate)
    raise FileNotFoundError(name)


def resolve_tool_optional(name: str) -> str | None:
    try:
        return resolve_tool(name)
    except FileNotFoundError:
        return None
