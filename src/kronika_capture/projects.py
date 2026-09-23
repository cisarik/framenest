"""Read-only resolution of one configured ChatGPT scratch project.

The registry is ``projects`` inside the bridge ``config.json``. This module
does not add, remove, or retarget projects. Resolution succeeds only when the
file contains exactly one project whose URL is ``https://chatgpt.com`` and
whose path is contained in one ``/g/g-p-…`` project route.
"""

from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import urlsplit

from kronika_capture.bridge.store import Store

PROJECT_NAME_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]{0,31}$")
PROJECT_PATH_RE = re.compile(r"^/g/(g-p-[A-Za-z0-9_-]+)(?:/[A-Za-z0-9._~-]+)*$")
PROJECTS_KEY = "projects"
DEFAULT_PROJECT_KEY = "default_project"
CHATGPT_HOST = "chatgpt.com"


class ProjectError(ValueError):
    """Invalid project registry read, carrying an operator message."""


def _store(state_dir: Store | Path | str | None = None) -> Store:
    if isinstance(state_dir, Store):
        return state_dir
    return Store(state_dir)


def project_url_contained(url: str) -> bool:
    """True when ``url`` is exactly the ChatGPT origin and one project route.

    Credentials, a non-default port, a query, a fragment, another host, a
    scheme other than ``https``, or a path outside ``/g/g-p-…`` are rejected.
    """

    if not isinstance(url, str) or not url or any(char in url for char in ("\\", "\n", "\r")):
        return False
    try:
        parts = urlsplit(url)
        port = parts.port
    except ValueError:
        return False
    if parts.scheme != "https" or parts.hostname != CHATGPT_HOST:
        return False
    if parts.username or parts.password:
        return False
    if port not in (None, 443):
        return False
    if parts.query or parts.fragment:
        return False
    if ".." in parts.path.split("/"):
        return False
    return PROJECT_PATH_RE.fullmatch(parts.path) is not None


def _projects(config: dict) -> dict:
    entries = config.get(PROJECTS_KEY)
    if not isinstance(entries, dict):
        return {}
    kept: dict[str, dict] = {}
    for name, entry in entries.items():
        if not isinstance(name, str) or PROJECT_NAME_PATTERN.fullmatch(name) is None:
            continue
        if not isinstance(entry, dict):
            continue
        url = entry.get("url")
        if not isinstance(url, str) or not project_url_contained(url):
            continue
        kept[name] = {"name": name, "url": url}
    return kept


def configured_project(state_dir: Store | Path | str | None = None) -> dict | None:
    """Return the single configured project, or None when the registry is not exactly one."""

    projects = _projects(_store(state_dir).load_config())
    if len(projects) != 1:
        return None
    name = next(iter(projects))
    return dict(projects[name])


def resolve(
    name: str | None = None, state_dir: Store | Path | str | None = None
) -> dict | None:
    """Resolve the one configured project.

    ``name`` must be omitted or equal that project's name. Any other registry
    shape, including zero or several projects, resolves to None.
    """

    project = configured_project(state_dir)
    if project is None:
        return None
    if name is not None and name != project["name"]:
        return None
    return project
