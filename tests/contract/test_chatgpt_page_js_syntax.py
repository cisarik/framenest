"""JavaScript syntax, protocol version, and retained pack keys."""

from __future__ import annotations

import ast
import json
import re
import subprocess
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
EXTENSION_ROOT = (
    REPOSITORY_ROOT
    / "vendor"
    / "kronika-ask"
    / "src"
    / "kronika"
    / "_assets"
    / "extension"
    / "src"
)
PROTOCOL_TEST = REPOSITORY_ROOT / "tests" / "chatgpt_page_protocol.test.js"
FORBIDDEN_IMPORT_ROOTS = frozenset(
    {
        "kronika.library",
        "kronika.markdown",
        "kronika.sanitize",
    }
)
FORBIDDEN_MODULES = frozenset(
    {
        "kronika.bridge.render",
        "kronika.bridge.assets",
        "kronika.bridge.capture_auth",
    }
)


def test_retained_javascript_parses() -> None:
    files = sorted(
        path
        for path in EXTENSION_ROOT.rglob("*")
        if path.suffix in {".js", ".mjs"} and path.is_file()
    )
    assert files
    for path in files:
        check = subprocess.run(
            ["node", "--check", str(path)],
            cwd=REPOSITORY_ROOT,
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert check.returncode == 0, f"{path}: {check.stderr}"
    protocol = subprocess.run(
        ["node", "--test", str(PROTOCOL_TEST)],
        cwd=REPOSITORY_ROOT,
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert protocol.returncode == 0, protocol.stderr + protocol.stdout


def test_protocol_version_error_codes_and_upload_locator_stay() -> None:
    protocol = (EXTENSION_ROOT / "protocol.js").read_text(encoding="utf-8")
    assert re.search(r"export const PROTO_VERSION = 1;", protocol)
    pack = json.loads((EXTENSION_ROOT / "adapters" / "pack_v5.json").read_text(encoding="utf-8"))
    assert "upload_input" in pack["locators"]
    errors = (REPOSITORY_ROOT / "vendor" / "kronika-ask" / "src" / "kronika" / "errors.py").read_text(
        encoding="utf-8"
    )
    for code in (
        "E_UPLOAD_FAILED",
        "E_BUSY",
        "E_CANCELLED",
        "E_RESPONSE_TIMEOUT",
        "E_WEB_SEARCH_UNAVAILABLE",
        "E_DEEP_RESEARCH_UNAVAILABLE",
        "E_LOGIN_REQUIRED",
    ):
        assert f'"{code}"' in protocol
        assert f'"{code}"' in errors


def test_vendored_python_does_not_import_removed_modules() -> None:
    package = REPOSITORY_ROOT / "vendor" / "kronika-ask" / "src" / "kronika"
    violations: list[str] = []
    for path in sorted(package.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                module = node.module
            elif isinstance(node, ast.Import):
                module = node.names[0].name
            else:
                continue
            if module in FORBIDDEN_MODULES or module.startswith("kronika.library"):
                violations.append(f"{path.name}: {module}")
            if module.split(".")[0] in {"markdown", "sanitize"} or module in FORBIDDEN_IMPORT_ROOTS:
                violations.append(f"{path.name}: {module}")
    assert violations == []
