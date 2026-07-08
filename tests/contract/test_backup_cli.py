"""Contract tests for the FrameNest catalog backup command boundary."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any

import pytest

from framenest.configuration import FrameNestSettings
from framenest.infrastructure.persistence.migrations import upgrade_database_to_head

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
BACKUP_CONSOLE_SCRIPT = REPOSITORY_ROOT / ".venv" / "bin" / "framenest-backup"
PYTHON_EXECUTABLE = REPOSITORY_ROOT / ".venv" / "bin" / "python"


def _require_backup_console_script() -> Path:
    if not BACKUP_CONSOLE_SCRIPT.is_file():
        pytest.fail(f"Expected installed console script at {BACKUP_CONSOLE_SCRIPT}")
    return BACKUP_CONSOLE_SCRIPT


def _run_backup_command(*args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env.pop("FRAMENEST_API_KEY", None)
    return subprocess.run(
        [str(_require_backup_console_script()), *args],
        cwd=cwd,
        env=env,
        check=False,
        capture_output=True,
        text=True,
        timeout=8.0,
    )


def _payload(output: str) -> dict[str, Any]:
    lines = [line for line in output.splitlines() if line.strip()]
    assert len(lines) == 1
    parsed = json.loads(lines[0])
    assert isinstance(parsed, dict)
    return parsed


def _migrated_database(path: Path) -> Path:
    upgrade_database_to_head(FrameNestSettings(database_path=path, _env_file=None))
    return path


def test_backup_console_script_is_installed() -> None:
    assert BACKUP_CONSOLE_SCRIPT.is_file()


def test_importing_backup_cli_has_no_execution_side_effects(tmp_path: Path) -> None:
    result = subprocess.run(
        [str(PYTHON_EXECUTABLE), "-c", "import framenest.adapters.cli.backup"],
        cwd=tmp_path,
        check=False,
        capture_output=True,
        text=True,
        timeout=8.0,
    )

    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""


def test_backup_help_succeeds(tmp_path: Path) -> None:
    result = _run_backup_command("--help", cwd=tmp_path)

    assert result.returncode == 0
    assert "create" in result.stdout
    assert "verify" in result.stdout
    assert "restore" in result.stdout


def test_create_verify_restore_cli_round_trip_with_sanitized_output(tmp_path: Path) -> None:
    database_path = _migrated_database(tmp_path / "private" / "catalog.sqlite3")
    bundle = tmp_path / "bundle"
    restored = tmp_path / "restored" / "catalog.sqlite3"

    create = _run_backup_command("create", "--source", str(database_path), "--output", str(bundle), cwd=tmp_path)
    verify = _run_backup_command("verify", "--bundle", str(bundle), cwd=tmp_path)
    restore = _run_backup_command("restore", "--bundle", str(bundle), "--destination", str(restored), cwd=tmp_path)

    assert create.returncode == 0
    assert verify.returncode == 0
    assert restore.returncode == 0
    assert create.stderr == verify.stderr == restore.stderr == ""
    assert _payload(create.stdout)["state"] == "created"
    assert _payload(verify.stdout)["state"] == "verified"
    assert _payload(restore.stdout)["state"] == "restored"
    combined = create.stdout + verify.stdout + restore.stdout
    assert str(database_path) not in combined
    assert str(bundle) not in combined
    assert str(restored) not in combined
    assert "private" not in combined


def test_failure_output_is_sanitized_and_stable(tmp_path: Path) -> None:
    supplied_path = tmp_path / "private" / "missing.sqlite3"

    result = _run_backup_command(
        "create",
        "--source",
        str(supplied_path),
        "--output",
        str(tmp_path / "bundle"),
        cwd=tmp_path,
    )

    assert result.returncode == 1
    assert result.stdout == ""
    payload = _payload(result.stderr)
    assert payload == {
        "operation": "create",
        "state": "error",
        "error_code": "FRAMENEST_BACKUP_COMMAND_FAILED",
        "message": "Backup command failed.",
    }
    assert str(supplied_path) not in result.stderr
    assert "private" not in result.stderr
    assert "Traceback" not in result.stderr


def test_invalid_usage_returns_exit_2_with_sanitized_json(tmp_path: Path) -> None:
    result = _run_backup_command("create", "--source", "relative.sqlite3", cwd=tmp_path)

    assert result.returncode == 2
    assert result.stdout == ""
    payload = _payload(result.stderr)
    assert payload["operation"] == "unknown"
    assert payload["error_code"] == "FRAMENEST_BACKUP_INVALID_INPUT"
    assert "relative.sqlite3" not in result.stderr
