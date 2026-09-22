"""Load the vendored kronika package for chatgpt-page unit tests."""

from __future__ import annotations

import importlib.util
from pathlib import Path

_SUPPORT = Path(__file__).resolve().parents[2] / "support" / "chatgpt_page_import.py"
_SPEC = importlib.util.spec_from_file_location("chatgpt_page_import", _SUPPORT)
assert _SPEC is not None and _SPEC.loader is not None
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)
