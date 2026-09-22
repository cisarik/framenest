"""Packaged kronika assets and the installed entry point."""

from __future__ import annotations

import importlib.util
import subprocess
import zipfile
from importlib import resources
from pathlib import Path

_SUPPORT = Path(__file__).resolve().parents[1] / "support" / "chatgpt_page_import.py"
_SPEC = importlib.util.spec_from_file_location("chatgpt_page_import", _SUPPORT)
assert _SPEC is not None and _SPEC.loader is not None
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
ASSET_PATHS = (
    "_assets/extension/src/headless/runner.mjs",
    "_assets/extension/src/adapters/pack_v5.json",
    "_assets/extension/src/headless/login_app/index.html",
)


def test_importlib_resources_resolve_packaged_assets() -> None:
    root = resources.files("kronika")
    for relative in ASSET_PATHS:
        asset = root.joinpath(relative)
        assert asset.is_file(), relative


def test_wheel_contains_kernel_assets_and_entry_point(tmp_path: Path) -> None:
    wheelhouse = tmp_path / "wheelhouse"
    wheelhouse.mkdir()
    build = subprocess.run(
        ["poetry", "build", "--format", "wheel", "--output", str(wheelhouse)],
        cwd=REPOSITORY_ROOT,
        check=False,
        capture_output=True,
        text=True,
        timeout=120.0,
    )
    assert build.returncode == 0, build.stderr
    wheels = sorted(wheelhouse.glob("framenest-*.whl"))
    assert len(wheels) == 1
    with zipfile.ZipFile(wheels[0]) as wheel:
        names = set(wheel.namelist())
        entry_points = wheel.read("framenest-0.1.0.dist-info/entry_points.txt").decode("utf-8")
    for relative in ASSET_PATHS:
        assert f"kronika/{relative}" in names
    assert "kronika/__init__.py" in names
    assert "framenest-chatgpt-page=kronika.cli:main" in entry_points.replace(" ", "")
    assert not (REPOSITORY_ROOT / "dist").exists()
