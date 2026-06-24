"""Contract tests for the FrameNest catalog command boundary."""

from __future__ import annotations

import importlib
import json
import os
import socket
import subprocess
import sys
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
CATALOG_CONSOLE_SCRIPT = REPOSITORY_ROOT / ".venv" / "bin" / "framenest-catalog"
DB_CONSOLE_SCRIPT = REPOSITORY_ROOT / ".venv" / "bin" / "framenest-db"
PYTHON_EXECUTABLE = REPOSITORY_ROOT / ".venv" / "bin" / "python"
PRIVATE_DATABASE_PATH = "/Users/agile/private/catalog.sqlite3"
CANONICAL_UUID4_TEXT = "12345678-1234-4234-9234-123456789abc"
SECOND_CANONICAL_UUID4_TEXT = "abcdefab-cdef-4abc-8def-abcdefabcdef"


def _require_catalog_console_script() -> Path:
    if not CATALOG_CONSOLE_SCRIPT.is_file():
        pytest.fail(f"Expected installed console script at {CATALOG_CONSOLE_SCRIPT}")
    return CATALOG_CONSOLE_SCRIPT


def _run_db_migrate(*, cwd: Path, database_path: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["FRAMENEST_DATABASE_PATH"] = database_path
    env.pop("FRAMENEST_API_KEY", None)
    return subprocess.run(
        [str(DB_CONSOLE_SCRIPT), "migrate"],
        cwd=cwd,
        env=env,
        check=False,
        capture_output=True,
        text=True,
        timeout=8.0,
    )


def _run_catalog_command(
    *args: str,
    cwd: Path,
    database_path: str,
) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["FRAMENEST_DATABASE_PATH"] = database_path
    env.pop("FRAMENEST_API_KEY", None)
    return subprocess.run(
        [str(_require_catalog_console_script()), *args],
        cwd=cwd,
        env=env,
        check=False,
        capture_output=True,
        text=True,
        timeout=8.0,
    )


def _parse_single_json_line(output: str) -> dict[str, Any]:
    lines = [line for line in output.splitlines() if line.strip()]
    assert len(lines) == 1
    payload = json.loads(lines[0])
    assert isinstance(payload, dict)
    return payload


def _upgrade_database_to_revision(database_path: Path, revision: str) -> None:
    from alembic import command

    from framenest.configuration import FrameNestSettings
    from framenest.infrastructure.persistence.engine import create_sqlite_engine, dispose_engine
    from framenest.infrastructure.persistence.migrations import _alembic_config

    settings = FrameNestSettings(database_path=database_path, _env_file=None)
    settings.database_path.parent.mkdir(parents=True, exist_ok=True)
    engine = create_sqlite_engine(settings.database_path)
    try:
        with engine.connect() as connection:
            with _alembic_config(
                "framenest.infrastructure.persistence.alembic_environment"
            ) as config:
                config.attributes["connection"] = connection
                command.upgrade(config, revision)
    finally:
        dispose_engine(engine)


def test_catalog_console_script_is_installed() -> None:
    assert CATALOG_CONSOLE_SCRIPT.is_file()


def test_importing_catalog_module_has_no_execution_side_effects(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            str(PYTHON_EXECUTABLE),
            "-c",
            "import framenest.adapters.cli.catalog",
        ],
        cwd=tmp_path,
        check=False,
        capture_output=True,
        text=True,
        timeout=8.0,
    )
    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""


def test_catalog_help_succeeds(tmp_path: Path) -> None:
    result = subprocess.run(
        [str(_require_catalog_console_script()), "--help"],
        cwd=tmp_path,
        check=False,
        capture_output=True,
        text=True,
        timeout=8.0,
    )
    assert result.returncode == 0
    assert "device" in result.stdout


def test_invalid_usage_returns_exit_2_with_sanitized_json(tmp_path: Path) -> None:
    database_path = tmp_path / "catalog.sqlite3"
    rejected_id = "NOT-A-VALID-ID"

    result = _run_catalog_command(
        "device",
        "get",
        "--id",
        rejected_id,
        cwd=tmp_path,
        database_path=str(database_path),
    )

    assert result.returncode == 2
    assert result.stdout == ""
    payload = _parse_single_json_line(result.stderr)
    assert payload == {
        "operation": "device.get",
        "state": "error",
        "error_code": "FRAMENEST_CATALOG_INVALID_INPUT",
        "message": "Invalid catalog command.",
    }
    combined = result.stdout + result.stderr
    assert rejected_id not in combined
    assert "argument" not in combined.lower()


def test_nonexistent_database_returns_exit_4_without_creating_file(tmp_path: Path) -> None:
    database_path = tmp_path / "missing" / "catalog.sqlite3"

    result = _run_catalog_command(
        "device",
        "list",
        cwd=tmp_path,
        database_path=str(database_path),
    )

    assert result.returncode == 4
    assert result.stdout == ""
    payload = _parse_single_json_line(result.stderr)
    assert payload == {
        "operation": "device.list",
        "state": "error",
        "error_code": "FRAMENEST_CATALOG_NOT_READY",
        "message": "Catalog database is not ready. Run framenest-db migrate.",
    }
    assert not database_path.exists()
    assert not database_path.parent.exists()
    assert str(database_path) not in result.stderr


def test_database_at_revision_0001_returns_exit_4(tmp_path: Path) -> None:
    database_path = tmp_path / "behind.sqlite3"
    _upgrade_database_to_revision(database_path, "0001")

    result = _run_catalog_command(
        "device",
        "list",
        cwd=tmp_path,
        database_path=str(database_path),
    )

    assert result.returncode == 4
    payload = _parse_single_json_line(result.stderr)
    assert payload["error_code"] == "FRAMENEST_CATALOG_NOT_READY"
    assert "0001" not in result.stderr
    assert "0002" not in result.stderr


def test_catalog_cli_does_not_execute_migrations(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from framenest.adapters.cli import catalog

    database_path = tmp_path / "no-migrate.sqlite3"
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("FRAMENEST_DATABASE_PATH", str(database_path))

    def fail_upgrade(*args: object, **kwargs: object) -> object:
        raise AssertionError("catalog CLI must not execute migrations")

    monkeypatch.setattr(
        "framenest.infrastructure.persistence.migrations.upgrade_database_to_head",
        fail_upgrade,
    )

    assert catalog.main(["device", "list"]) == 4
    assert not database_path.exists()


@pytest.mark.parametrize(
    ("device_id",),
    [
        ("12345678-1234-4234-9234-123456789ABC",),
        (" 12345678-1234-4234-9234-123456789abc",),
        ("{12345678-1234-4234-9234-123456789abc}",),
        ("urn:uuid:12345678-1234-4234-9234-123456789abc",),
        ("12345678123442349234123456789abc",),
        ("a8098c1a-f86e-11da-bd1a-00112444be1e",),
    ],
)
def test_get_rejects_malformed_device_ids(tmp_path: Path, device_id: str) -> None:
    database_path = tmp_path / "catalog.sqlite3"
    _run_db_migrate(cwd=tmp_path, database_path=str(database_path))

    result = _run_catalog_command(
        "device",
        "get",
        "--id",
        device_id,
        cwd=tmp_path,
        database_path=str(database_path),
    )

    assert result.returncode == 2
    payload = _parse_single_json_line(result.stderr)
    assert payload["error_code"] == "FRAMENEST_CATALOG_INVALID_INPUT"
    assert device_id not in result.stdout + result.stderr


def test_register_valid_unicode_display_name(tmp_path: Path) -> None:
    database_path = tmp_path / "catalog.sqlite3"
    _run_db_migrate(cwd=tmp_path, database_path=str(database_path))
    display_name = "Café 🎬"

    result = _run_catalog_command(
        "device",
        "register",
        "--display-name",
        display_name,
        cwd=tmp_path,
        database_path=str(database_path),
    )

    assert result.returncode == 0
    assert result.stderr == ""
    payload = _parse_single_json_line(result.stdout)
    assert payload["operation"] == "device.register"
    assert payload["state"] == "ok"
    device = payload["device"]
    assert device["display_name"] == display_name
    assert device["id"] == device["id"].lower()
    assert len(device["id"]) == 36


def test_register_invalid_display_name_returns_exit_2(tmp_path: Path) -> None:
    from framenest.adapters.cli import catalog

    database_path = tmp_path / "catalog.sqlite3"
    _run_db_migrate(cwd=tmp_path, database_path=str(database_path))

    exit_code = catalog.main(["device", "register", "--display-name", " leading"])
    assert exit_code == 2


def test_register_invalid_display_name_via_subprocess_returns_exit_2(tmp_path: Path) -> None:
    database_path = tmp_path / "catalog.sqlite3"
    _run_db_migrate(cwd=tmp_path, database_path=str(database_path))

    result = _run_catalog_command(
        "device",
        "register",
        "--display-name",
        "",
        cwd=tmp_path,
        database_path=str(database_path),
    )

    assert result.returncode == 2
    payload = _parse_single_json_line(result.stderr)
    assert payload["error_code"] == "FRAMENEST_CATALOG_INVALID_INPUT"
    assert "leading" not in result.stdout + result.stderr


def test_register_persists_and_get_returns_device(tmp_path: Path) -> None:
    database_path = tmp_path / "catalog.sqlite3"
    _run_db_migrate(cwd=tmp_path, database_path=str(database_path))

    register = _run_catalog_command(
        "device",
        "register",
        "--display-name",
        "Studio Mac",
        cwd=tmp_path,
        database_path=str(database_path),
    )
    device_id = _parse_single_json_line(register.stdout)["device"]["id"]

    get_result = _run_catalog_command(
        "device",
        "get",
        "--id",
        device_id,
        cwd=tmp_path,
        database_path=str(database_path),
    )

    assert get_result.returncode == 0
    payload = _parse_single_json_line(get_result.stdout)
    assert payload == {
        "operation": "device.get",
        "state": "ok",
        "device": {"id": device_id, "display_name": "Studio Mac"},
    }


def test_get_missing_device_returns_exit_3(tmp_path: Path) -> None:
    database_path = tmp_path / "catalog.sqlite3"
    _run_db_migrate(cwd=tmp_path, database_path=str(database_path))

    result = _run_catalog_command(
        "device",
        "get",
        "--id",
        CANONICAL_UUID4_TEXT,
        cwd=tmp_path,
        database_path=str(database_path),
    )

    assert result.returncode == 3
    payload = _parse_single_json_line(result.stderr)
    assert payload == {
        "operation": "device.get",
        "state": "error",
        "error_code": "FRAMENEST_DEVICE_NOT_FOUND",
        "message": "Device not found.",
    }
    assert CANONICAL_UUID4_TEXT not in result.stderr


def test_list_empty_registry_returns_empty_array(tmp_path: Path) -> None:
    database_path = tmp_path / "catalog.sqlite3"
    _run_db_migrate(cwd=tmp_path, database_path=str(database_path))

    result = _run_catalog_command(
        "device",
        "list",
        cwd=tmp_path,
        database_path=str(database_path),
    )

    assert result.returncode == 0
    payload = _parse_single_json_line(result.stdout)
    assert payload == {
        "operation": "device.list",
        "state": "ok",
        "devices": [],
    }


def test_list_preserves_repository_ordering(tmp_path: Path) -> None:
    database_path = tmp_path / "catalog.sqlite3"
    _run_db_migrate(cwd=tmp_path, database_path=str(database_path))

    from framenest.application.ports.device_repository import DeviceRepository
    from framenest.domain import Device, DeviceId
    from framenest.infrastructure.persistence.device_repository import SqliteDeviceRepository
    from framenest.infrastructure.persistence.engine import create_sqlite_engine, dispose_engine

    engine = create_sqlite_engine(database_path)
    try:
        repository = SqliteDeviceRepository(engine)
        repository.add(Device(id=DeviceId.from_string(CANONICAL_UUID4_TEXT), display_name="alpha"))
        repository.add(
            Device(id=DeviceId.from_string(SECOND_CANONICAL_UUID4_TEXT), display_name="Beta")
        )
        repository.add(Device(id=DeviceId.new(), display_name="zebra"))
        expected = [
            {"id": device.id.to_string(), "display_name": device.display_name}
            for device in repository.list_all()
        ]
    finally:
        engine.dispose()

    result = _run_catalog_command(
        "device",
        "list",
        cwd=tmp_path,
        database_path=str(database_path),
    )

    assert result.returncode == 0
    payload = _parse_single_json_line(result.stdout)
    assert payload["devices"] == expected


def test_direct_process_emits_single_json_line_without_traceback(tmp_path: Path) -> None:
    database_path = tmp_path / "process.sqlite3"
    _run_db_migrate(cwd=tmp_path, database_path=str(database_path))

    result = _run_catalog_command(
        "device",
        "list",
        cwd=tmp_path,
        database_path=str(database_path),
    )

    assert result.returncode == 0
    assert result.stderr == ""
    assert len([line for line in result.stdout.splitlines() if line.strip()]) == 1
    assert "Traceback" not in result.stdout + result.stderr
    assert PRIVATE_DATABASE_PATH not in result.stdout + result.stderr
    assert "INSERT INTO" not in result.stdout + result.stderr
    assert "sqlite" not in (result.stdout + result.stderr).lower()


def test_direct_process_starts_no_listener(tmp_path: Path) -> None:
    database_path = tmp_path / "no-listener.sqlite3"
    _run_db_migrate(cwd=tmp_path, database_path=str(database_path))

    with patch("socket.socket.bind", side_effect=AssertionError("socket bind must not run")):
        result = _run_catalog_command(
            "device",
            "list",
            cwd=tmp_path,
            database_path=str(database_path),
        )

    assert result.returncode == 0


def test_repository_failure_returns_exit_1(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from framenest.adapters.cli import catalog
    from framenest.application.ports.device_repository import FrameNestDeviceRepositoryError

    database_path = tmp_path / "failure.sqlite3"
    _run_db_migrate(cwd=tmp_path, database_path=str(database_path))
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("FRAMENEST_DATABASE_PATH", str(database_path))

    def fail_add(self: object, device: object) -> None:
        raise FrameNestDeviceRepositoryError("Device registry operation failed.")

    monkeypatch.setattr(
        "framenest.infrastructure.persistence.device_repository.SqliteDeviceRepository.add",
        fail_add,
    )

    exit_code = catalog.main(["device", "register", "--display-name", "Studio Mac"])
    assert exit_code == 1


def test_catalog_works_from_working_directory_outside_repository(tmp_path: Path) -> None:
    database_path = tmp_path / "outside" / "catalog.sqlite3"
    _run_db_migrate(cwd=tmp_path, database_path=str(database_path))
    outside_cwd = tmp_path / "outside-cwd"
    outside_cwd.mkdir()

    result = _run_catalog_command(
        "device",
        "register",
        "--display-name",
        "Remote CWD",
        cwd=outside_cwd,
        database_path=str(database_path),
    )

    assert result.returncode == 0
    assert _parse_single_json_line(result.stdout)["device"]["display_name"] == "Remote CWD"
