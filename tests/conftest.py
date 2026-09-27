"""Synthetic fixture files stay private. No identity and no permissive policy."""

from __future__ import annotations

import os

import pytest


@pytest.fixture(autouse=True)
def _private_synthetic_file_mode() -> object:
    """Create incidental test files as 0600 without a process-wide application umask."""
    previous = os.umask(0o077)
    try:
        yield
    finally:
        os.umask(previous)
