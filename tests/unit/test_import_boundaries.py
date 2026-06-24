"""Import-boundary tests for the pure FrameNest domain package."""

from __future__ import annotations

import ast
import importlib
import socket
import sys
from pathlib import Path
from typing import Any

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
DOMAIN_ROOT = REPOSITORY_ROOT / "src" / "framenest" / "domain"
FORBIDDEN_DOMAIN_IMPORT_ROOTS = frozenset(
    {
        "alembic",
        "fastapi",
        "pydantic",
        "pydantic_settings",
        "sqlalchemy",
        "starlette",
        "uvicorn",
    }
)


def _module_name_from_import(node: ast.Import | ast.ImportFrom) -> str | None:
    if isinstance(node, ast.Import):
        return node.names[0].name.split(".")[0]
    if node.module is None:
        return None
    return node.module.split(".")[0]


def test_domain_package_imports_no_framework_or_persistence_modules() -> None:
    violations: list[str] = []
    for path in sorted(DOMAIN_ROOT.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        forbidden_roots: list[str] = []
        for node in ast.walk(tree):
            if not isinstance(node, (ast.Import, ast.ImportFrom)):
                continue
            root = _module_name_from_import(node)
            if root in FORBIDDEN_DOMAIN_IMPORT_ROOTS:
                forbidden_roots.append(root)
            if root == "framenest":
                module = node.module if isinstance(node, ast.ImportFrom) else node.names[0].name
                if module.startswith("framenest.infrastructure") or module.startswith(
                    "framenest.adapters"
                ):
                    forbidden_roots.append(module)
        if forbidden_roots:
            violations.append(
                f"{path.relative_to(REPOSITORY_ROOT)}: {sorted(set(forbidden_roots))}"
            )
    assert violations == []


def test_importing_domain_has_no_identity_or_io_side_effects(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bind_attempts: list[tuple[Any, ...]] = []
    original_bind = socket.socket.bind

    def tracked_bind(self: socket.socket, address: tuple[Any, ...]) -> None:
        bind_attempts.append(address)
        return original_bind(self, address)

    def fail_uuid4() -> object:
        raise AssertionError("domain import must not generate identities")

    def fail_open(*args: Any, **kwargs: Any) -> object:
        raise AssertionError("domain import must not open files or databases")

    def fail_getenv(*args: Any, **kwargs: Any) -> object:
        raise AssertionError("domain import must not read environment settings")

    monkeypatch.setattr(socket.socket, "bind", tracked_bind)
    monkeypatch.setattr("uuid.uuid4", fail_uuid4)
    monkeypatch.setattr("builtins.open", fail_open)
    monkeypatch.setattr("pathlib.Path.open", fail_open)
    monkeypatch.setattr("os.getenv", fail_getenv)
    monkeypatch.setattr("os.environ.get", fail_getenv)

    sys.modules.pop("framenest.domain.identities", None)
    sys.modules.pop("framenest.domain", None)

    importlib.import_module("framenest.domain")

    assert bind_attempts == []
