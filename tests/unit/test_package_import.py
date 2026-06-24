from importlib import import_module
from pathlib import Path


def test_framenest_package_resolves_from_src_layout() -> None:
    module = import_module("framenest")

    module_path = Path(module.__file__).resolve()
    expected_package_directory = (
        Path(__file__).resolve().parents[2] / "src" / "framenest"
    )

    assert module_path.parent == expected_package_directory
