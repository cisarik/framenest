"""Explicit state directories and packaged extension assets.

No default resolves to ``~/.local/state/kronika`` or
``~/.local/state/chatgpt-cli``. A development process may use the XDG state
home with the name ``framenest-chatgpt-page``. Deployment passes
``/var/lib/kronika-capture`` as an explicit directory.

When systemd sets ``CREDENTIALS_DIRECTORY`` and the bridge-token credential
file is present, token lookup uses that file. Otherwise the state-directory
``token`` file remains the source.
"""

from __future__ import annotations

import os
import stat
from collections.abc import Mapping
from importlib.resources import files
from pathlib import Path

from kronika_capture.config import (
    STATE_DIR_NAME,
    SYSTEMD_BRIDGE_TOKEN_CREDENTIAL,
    SYSTEMD_BRIDGE_TOKEN_MAX_BYTES,
)


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


def systemd_bridge_token_path(
    environ: Mapping[str, str] | None = None,
) -> Path | None:
    """Return the systemd credential file when that regular file exists.

    A missing directory, a relative path, a symlink, or a missing credential
    returns ``None`` so callers keep the state-directory fallback.
    """

    env = os.environ if environ is None else environ
    raw = env.get("CREDENTIALS_DIRECTORY", "")
    if not raw or raw != raw.strip() or "\x00" in raw:
        return None
    directory = Path(raw)
    if not directory.is_absolute() or any(part in (".", "..") for part in directory.parts):
        return None
    candidate = directory / SYSTEMD_BRIDGE_TOKEN_CREDENTIAL
    try:
        info = candidate.lstat()
    except OSError:
        return None
    if not stat.S_ISREG(info.st_mode):
        return None
    return candidate


def read_systemd_bridge_token(
    environ: Mapping[str, str] | None = None,
) -> str | None:
    """Return the credential text, ``""`` when the file is unusable, or ``None``.

    ``None`` means systemd did not provide the credential. An empty string
    means the credential file is present but must not be replaced with a newly
    minted token.
    """

    path = systemd_bridge_token_path(environ)
    if path is None:
        return None
    try:
        data = path.read_bytes()
    except OSError:
        return ""
    if len(data) > SYSTEMD_BRIDGE_TOKEN_MAX_BYTES or b"\x00" in data:
        return ""
    try:
        text = data.decode("utf-8").strip()
    except UnicodeDecodeError:
        return ""
    if "\n" in text or "\r" in text:
        return ""
    return text


def token_path(
    explicit: Path | str | None = None,
    environ: Mapping[str, str] | None = None,
) -> Path:
    credential = systemd_bridge_token_path(environ)
    if credential is not None:
        return credential
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
