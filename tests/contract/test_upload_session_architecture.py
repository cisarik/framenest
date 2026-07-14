"""Negative architecture contracts for the upload-session foundation."""

from __future__ import annotations

import ast
from pathlib import Path

from fastapi.routing import APIRoute

from framenest.adapters.api.application import create_app

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
UPLOAD_FOUNDATION_FILES = (
    REPOSITORY_ROOT / "src" / "framenest" / "domain" / "uploads.py",
    REPOSITORY_ROOT / "src" / "framenest" / "application" / "ports" / "upload_sessions.py",
    REPOSITORY_ROOT
    / "src"
    / "framenest"
    / "infrastructure"
    / "persistence"
    / "upload_session_repository.py",
    REPOSITORY_ROOT / "src" / "framenest" / "infrastructure" / "persistence" / "upload_schema.py",
)


def test_upload_session_foundation_exposes_no_upload_route() -> None:
    app = create_app()
    routes = [route for route in app.routes if isinstance(route, APIRoute)]

    assert all("upload" not in route.path.lower() for route in routes)
    assert all("upload" not in route.name.lower() for route in routes)


def test_upload_session_foundation_contains_no_media_filesystem_or_provider_calls() -> None:
    forbidden_import_roots = {
        "openai",
        "requests",
        "httpx",
        "PIL",
        "subprocess",
    }
    forbidden_call_names = {
        "open",
        "read_bytes",
        "write_bytes",
        "rename",
        "replace",
        "unlink",
        "rmdir",
        "mkdir",
    }
    found_imports: list[str] = []
    found_calls: list[str] = []
    for path in UPLOAD_FOUNDATION_FILES:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                found_imports.extend(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module is not None:
                found_imports.append(node.module.split(".")[0])
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    found_calls.append(node.func.id)
                elif isinstance(node.func, ast.Attribute):
                    found_calls.append(node.func.attr)

    assert sorted(set(found_imports) & forbidden_import_roots) == []
    assert sorted(set(found_calls) & forbidden_call_names) == []


def test_upload_session_foundation_does_not_insert_catalog_or_analysis_state() -> None:
    combined = "\n".join(path.read_text(encoding="utf-8") for path in UPLOAD_FOUNDATION_FILES)

    assert "logical_media" not in combined
    assert "physical_media_locations" not in combined
    assert "media_metadata" not in combined
    assert "media_canonical_tags" not in combined
    assert "media_analysis" not in combined
    assert "suggestion" not in combined
    assert "provider" not in combined
