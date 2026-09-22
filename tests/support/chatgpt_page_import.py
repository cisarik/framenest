"""Put the vendored ask kernel on sys.path for tests.

The canonical AP execution environment sets PYTHONPATH to FrameNest ``src``
only. These tests do not require the project virtualenv to have installed
``kronika``.
"""

from __future__ import annotations

import sys
from pathlib import Path

VENDOR_SRC = Path(__file__).resolve().parents[2] / "vendor" / "kronika-ask" / "src"
if str(VENDOR_SRC) not in sys.path:
    sys.path.insert(0, str(VENDOR_SRC))
