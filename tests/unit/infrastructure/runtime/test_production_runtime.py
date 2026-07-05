"""Unit tests for production runtime readiness checks."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from framenest.configuration import FrameNestSettings
from framenest.infrastructure.persistence.migrations import upgrade_database_to_head
from framenest.infrastructure.runtime import production


def _payload(output: str) -> dict[str, object]:
    lines = [line for line in output.splitlines() if line.strip()]
    assert len(lines) == 1
    parsed = json.loads(lines[0])
    assert isinstance(parsed, dict)
    return parsed


def test_check_database_ready_succeeds_only_at_head(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    database_path = tmp_path / "catalog.sqlite3"
    upgrade_database_to_head(FrameNestSettings(database_path=database_path))
    monkeypatch.setenv("FRAMENEST_DATABASE_PATH", str(database_path))

    assert production.main(["check-database-ready"]) == 0

    output = capsys.readouterr()
    assert output.err == ""
    assert _payload(output.out) == {
        "operation": "check-database-ready",
        "state": "ready",
        "current_revision": "0007",
    }
    assert str(database_path) not in output.out


def test_check_database_ready_rejects_missing_database_without_creating_it(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    database_path = tmp_path / "missing" / "catalog.sqlite3"
    monkeypatch.setenv("FRAMENEST_DATABASE_PATH", str(database_path))

    assert production.main(["check-database-ready"]) == 4

    output = capsys.readouterr()
    assert output.out == ""
    payload = _payload(output.err)
    assert payload["error_code"] == "FRAMENEST_DATABASE_NOT_READY"
    assert str(database_path) not in output.err
    assert not database_path.exists()
    assert not database_path.parent.exists()


def test_check_database_ready_rejects_behind_database_without_migrating_it(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    database_path = tmp_path / "behind.sqlite3"
    with sqlite3.connect(database_path) as connection:
        connection.execute("CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL)")
        connection.execute("INSERT INTO alembic_version (version_num) VALUES ('0006')")
    monkeypatch.setenv("FRAMENEST_DATABASE_PATH", str(database_path))

    assert production.main(["check-database-ready"]) == 4

    output = capsys.readouterr()
    assert output.out == ""
    assert _payload(output.err)["error_code"] == "FRAMENEST_DATABASE_NOT_READY"
    with sqlite3.connect(database_path) as connection:
        revision = connection.execute("SELECT version_num FROM alembic_version").fetchone()[0]
    assert revision == "0006"
    assert str(database_path) not in output.err


def test_invalid_database_path_error_is_sanitized(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(tmp_path)
    supplied_path = "relative/private/catalog.sqlite3"
    monkeypatch.setenv("FRAMENEST_DATABASE_PATH", supplied_path)

    assert production.main(["check-database-ready"]) == 1

    output = capsys.readouterr()
    assert output.out == ""
    payload = _payload(output.err)
    assert payload["error_code"] == "FRAMENEST_PRODUCTION_COMMAND_FAILED"
    assert supplied_path not in output.err
    assert "relative/private" not in output.err
