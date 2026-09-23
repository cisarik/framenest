"""Explicit state directories and packaged extension assets.

No default resolves to ``~/.local/state/kronika`` or
``~/.local/state/chatgpt-cli``. A development process may use the XDG state
home with the name ``framenest-chatgpt-page``. Deployment passes
``/var/lib/framenest/chatgpt-page`` as an explicit directory.
"""

from __future__ import annotations

import os
from importlib.resources import files
from pathlib import Path

from kronika_capture.config import STATE_DIR_NAME


def state_dir(explicit: Path | str | None = None) -> Path:
    """Return one state directory.

    An explicit path is used unchanged. Otherwise the directory is
    ``$XDG_STATE_HOME/framenest-chatgpt-page``, or
    ``~/.local/state/framenest-chatgpt-page`` when ``XDG_STATE_HOME`` is unset.
    """

    if explicit is not None:
        return Path(explicit)
    xdg_state_home = os.environ.get("XDG_STATE_HOME")
    base = Path(xdg_state_home) if xdg_state_home else Path.home() / ".local" / "state"
    return base / STATE_DIR_NAME


def token_path(explicit: Path | str | None = None) -> Path:
    return state_dir(explicit) / "token"


def config_path(explicit: Path | str | None = None) -> Path:
    return state_dir(explicit) / "config.json"


def packaged_extension_path(*parts: str) -> Path:
    """Resolve one file under the packaged extension tree.

    Lookup uses :func:`importlib.resources.files` anchored at this package.
    It does not consult the Git root or the process working directory.
    """

    node = files("kronika_capture").joinpath("_assets", "extension", "src", *parts)
    return Path(str(node))
