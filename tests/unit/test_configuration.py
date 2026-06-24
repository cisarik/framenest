"""Behavioral tests for the centralized FrameNest settings boundary."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
from pydantic import SecretStr, ValidationError

from framenest.configuration import load_settings

FRAMENEST_ENV_VARS = ("FRAMENEST_HOST", "FRAMENEST_PORT", "FRAMENEST_API_KEY")


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
