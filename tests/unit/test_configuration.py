"""Behavioral tests for the centralized FrameNest settings boundary."""

from __future__ import annotations

import json
import logging
import logging.config
import subprocess
import tempfile
from io import StringIO
from pathlib import Path

import pytest
from pydantic import SecretStr, ValidationError

from framenest.configuration import load_settings

FRAMENEST_ENV_VARS = (
    "FRAMENEST_HOST",
    "FRAMENEST_PORT",
    "FRAMENEST_API_KEY",
    "FRAMENEST_DATABASE_PATH",
    "FRAMENEST_AI_PROVIDER_ID",
    "FRAMENEST_AI_MODEL_ID",
)


@pytest.fixture(autouse=True)
def isolate_framenest_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Remove FrameNest configuration variables before and after each test."""
    for variable in FRAMENEST_ENV_VARS:
        monkeypatch.delenv(variable, raising=False)


def test_settings_load_without_real_env_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    settings = load_settings(env_file=None)
    assert settings.host == "127.0.0.1"


def test_default_host_is_loopback(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    settings = load_settings(env_file=None)
    assert settings.host == "127.0.0.1"


def test_default_port_is_8000(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    settings = load_settings(env_file=None)
    assert settings.port == 8000


def test_database_path_is_typed_path_and_safe_temporary_default(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    configured_temp_root = tmp_path / "system-temp"
    monkeypatch.setattr(tempfile, "gettempdir", lambda: str(configured_temp_root))

    settings = load_settings(env_file=None)

    assert isinstance(settings.database_path, Path)
    assert settings.database_path == (
        configured_temp_root / "framenest-development" / "catalog.sqlite3"
    )
    assert settings.database_path.is_absolute()
    assert Path(__file__).resolve().parents[2] not in settings.database_path.parents


def test_default_database_path_loading_creates_no_directory_or_database(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    configured_temp_root = tmp_path / "system-temp"
    monkeypatch.setattr(tempfile, "gettempdir", lambda: str(configured_temp_root))

    settings = load_settings(env_file=None)

    assert settings.database_path.parent == configured_temp_root / "framenest-development"
    assert not settings.database_path.parent.exists()
    assert not settings.database_path.exists()


def test_temporary_env_file_sets_database_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    configured_path = tmp_path / "configured" / "catalog.sqlite3"
    env_file = tmp_path / ".env"
    env_file.write_text(
        f"FRAMENEST_DATABASE_PATH={configured_path}\n",
        encoding="utf-8",
    )

    settings = load_settings(env_file=env_file)

    assert settings.database_path == configured_path


def test_process_environment_overrides_temporary_env_file_database_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    env_file_path = tmp_path / "env-file" / "catalog.sqlite3"
    process_path = tmp_path / "process-env" / "catalog.sqlite3"
    env_file = tmp_path / ".env"
    env_file.write_text(
        f"FRAMENEST_DATABASE_PATH={env_file_path}\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("FRAMENEST_DATABASE_PATH", str(process_path))

    settings = load_settings(env_file=env_file)

    assert settings.database_path == process_path


def test_database_path_expands_user_and_normalizes_to_absolute_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    home = tmp_path / "home"
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("FRAMENEST_DATABASE_PATH", "~/catalogs/../catalog.sqlite3")

    settings = load_settings(env_file=None)

    assert settings.database_path == home / "catalog.sqlite3"
    assert settings.database_path.is_absolute()
    assert not settings.database_path.exists()


def test_relative_database_path_is_rejected_with_sanitized_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    supplied_path = "relative/private/catalog.sqlite3"
    monkeypatch.setenv("FRAMENEST_DATABASE_PATH", supplied_path)

    with pytest.raises(ValidationError) as exc_info:
        load_settings(env_file=None)

    error_text = str(exc_info.value)
    assert supplied_path not in error_text
    assert "relative/private" not in error_text


def test_database_path_absent_from_settings_repr_logs_api_and_openapi(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from fastapi.testclient import TestClient

    from framenest.adapters.api.application import create_app
    from framenest.structured_logging import build_uvicorn_log_config, get_logger

    monkeypatch.chdir(tmp_path)
    private_path = tmp_path / "private" / "catalog.sqlite3"
    monkeypatch.setenv("FRAMENEST_DATABASE_PATH", str(private_path))
    settings = load_settings(env_file=None)

    rendered_settings = f"{settings!r}{settings!s}"
    assert str(private_path) not in rendered_settings

    logging.config.dictConfig(build_uvicorn_log_config())
    stream = StringIO()
    logger = logging.getLogger("framenest")
    handler = logger.handlers[0]
    handler.stream = stream  # type: ignore[attr-defined]
    get_logger("configuration").emit(
        level="INFO",
        event="settings_loaded",
        operation="test",
        context={"path": str(private_path), "settings": settings},
    )
    log_output = stream.getvalue()
    assert str(private_path) not in log_output
    assert json.loads(log_output)

    app = create_app(settings=settings)
    api_output = TestClient(app).get("/health").text
    openapi_output = json.dumps(app.openapi())
    assert str(private_path) not in api_output
    assert str(private_path) not in openapi_output


def test_temporary_env_file_sets_port(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    env_file = tmp_path / ".env"
    env_file.write_text("FRAMENEST_PORT=9001\n", encoding="utf-8")
    settings = load_settings(env_file=env_file)
    assert settings.port == 9001


def test_process_environment_overrides_temporary_env_file_port(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    env_file = tmp_path / ".env"
    env_file.write_text("FRAMENEST_PORT=9001\n", encoding="utf-8")
    monkeypatch.setenv("FRAMENEST_PORT", "9002")
    settings = load_settings(env_file=env_file)
    assert settings.port == 9002


def test_invalid_port_produces_sanitized_validation_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    invalid_port = "70000"
    secret_value = "must-not-appear-in-error-output"
    monkeypatch.setenv("FRAMENEST_PORT", invalid_port)
    monkeypatch.setenv("FRAMENEST_API_KEY", secret_value)
    with pytest.raises(ValidationError) as exc_info:
        load_settings(env_file=None)
    error_text = str(exc_info.value)
    assert invalid_port not in error_text
    assert secret_value not in error_text


def test_temporary_env_file_overrides_default(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    env_file = tmp_path / ".env"
    env_file.write_text("FRAMENEST_HOST=192.168.1.1\n", encoding="utf-8")
    settings = load_settings(env_file=env_file)
    assert settings.host == "192.168.1.1"


def test_process_environment_overrides_temporary_env_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    env_file = tmp_path / ".env"
    env_file.write_text("FRAMENEST_HOST=192.168.1.1\n", encoding="utf-8")
    monkeypatch.setenv("FRAMENEST_HOST", "10.0.0.1")
    settings = load_settings(env_file=env_file)
    assert settings.host == "10.0.0.1"


def test_secret_field_uses_secret_str(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("FRAMENEST_API_KEY", "representative-secret-value")
    settings = load_settings(env_file=None)
    assert isinstance(settings.api_key, SecretStr)


def test_secret_plaintext_not_in_repr_or_str(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    secret_value = "representative-secret-value"
    monkeypatch.setenv("FRAMENEST_API_KEY", secret_value)
    settings = load_settings(env_file=None)
    rendered = f"{settings!r}{settings!s}"
    assert secret_value not in rendered


def test_invalid_configuration_produces_sanitized_validation_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    invalid_host = "not-a-valid-ip-address"
    secret_value = "must-not-appear-in-error-output"
    monkeypatch.setenv("FRAMENEST_HOST", invalid_host)
    monkeypatch.setenv("FRAMENEST_API_KEY", secret_value)
    with pytest.raises(ValidationError) as exc_info:
        load_settings(env_file=None)
    error_text = str(exc_info.value)
    assert invalid_host not in error_text
    assert secret_value not in error_text


def test_dotenv_is_gitignored() -> None:
    result = subprocess.run(
        ["git", "check-ignore", "-v", ".env"],
        cwd=Path(__file__).resolve().parents[2],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert ".env" in result.stdout
