"""Systemd credential sourcing for the bridge token. Values here are synthetic."""

from __future__ import annotations

import os
import stat

import pytest

from kronika_capture import paths
from kronika_capture.bridge import auth
from kronika_capture.bridge.server import build_state
from kronika_capture.bridge.store import Store
from kronika_capture.cli import build_parser, build_runner_argv, configured_chromium


SECRET = "synthetic-bridge-token"


def _credential(tmp_path, text: str):
    directory = tmp_path / "credentials"
    directory.mkdir()
    path = directory / "token"
    path.write_text(text, encoding="utf-8")
    os.chmod(path, 0o600)
    return directory


def test_systemd_credential_is_used_and_does_not_mint_state_token(tmp_path, monkeypatch) -> None:
    directory = _credential(tmp_path, SECRET + "\n")
    monkeypatch.setenv("CREDENTIALS_DIRECTORY", str(directory))
    state = tmp_path / "state" / "token"
    assert auth.load_or_create_token(state) == SECRET
    assert not state.exists()
    assert paths.token_path(tmp_path / "state") == directory / "token"


def test_bridge_state_uses_the_systemd_credential(tmp_path, monkeypatch) -> None:
    directory = _credential(tmp_path, SECRET + "\n")
    monkeypatch.setenv("CREDENTIALS_DIRECTORY", str(directory))
    state_dir = tmp_path / "state"
    bridge = build_state(Store(state_dir))
    assert bridge.token == SECRET
    assert not (state_dir / "token").exists()


def test_missing_systemd_credential_keeps_the_state_file(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv("CREDENTIALS_DIRECTORY", raising=False)
    path = tmp_path / "token"
    path.write_text("existing-token\n", encoding="utf-8")
    assert auth.load_or_create_token(path) == "existing-token"
    assert paths.token_path(tmp_path) == path


def test_absent_credential_directory_still_mints_with_the_same_writer(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CREDENTIALS_DIRECTORY", str(tmp_path / "missing"))
    path = tmp_path / "state" / "token"
    minted = auth.load_or_create_token(path)
    assert minted
    assert path.read_text(encoding="utf-8").strip() == minted
    assert len(minted) >= 32
    assert stat.S_IMODE(path.stat().st_mode) == 0o600


def test_empty_credential_does_not_fall_through_to_minting(tmp_path, monkeypatch) -> None:
    directory = _credential(tmp_path, "\n")
    monkeypatch.setenv("CREDENTIALS_DIRECTORY", str(directory))
    state = tmp_path / "token"
    assert auth.load_or_create_token(state) == ""
    assert not state.exists()


def test_symlink_credential_is_ignored(tmp_path, monkeypatch) -> None:
    real = tmp_path / "real-token"
    real.write_text(SECRET + "\n", encoding="utf-8")
    directory = tmp_path / "credentials"
    directory.mkdir()
    (directory / "token").symlink_to(real)
    monkeypatch.setenv("CREDENTIALS_DIRECTORY", str(directory))
    assert paths.systemd_bridge_token_path() is None
    path = tmp_path / "state-token"
    path.write_text("existing-token\n", encoding="utf-8")
    assert auth.load_or_create_token(path) == "existing-token"


def test_host_origin_and_token_comparison_stay_the_same() -> None:
    headers = {"X-Bridge-Token": SECRET}
    accepted = auth.check_request(headers, "127.0.0.1:8765", SECRET, port=8765)
    rejected = auth.check_request(headers, "127.0.0.1:8765", "other-token", port=8765)
    forbidden = auth.check_request(headers, "example.test", SECRET, port=8765)
    assert accepted.ok is True
    assert rejected.ok is False
    assert rejected.status == 401
    assert forbidden.status == 403


def test_runner_argv_uses_the_credential_directory_without_the_token(
    tmp_path, monkeypatch
) -> None:
    chrome = tmp_path / "chromium"
    chrome.write_text("", encoding="utf-8")
    chrome.chmod(0o755)
    directory = _credential(tmp_path, SECRET + "\n")
    monkeypatch.setenv("CREDENTIALS_DIRECTORY", str(directory))
    monkeypatch.delenv("KRONIKA_CHROMIUM_PATH", raising=False)
    args = build_parser().parse_args(
        [
            "--state-dir",
            str(tmp_path / "state"),
            "runner",
            "run",
            "--chrome-path",
            str(chrome),
            "--headed",
        ]
    )
    argv = build_runner_argv(args)
    assert argv is not None
    rendered = " ".join(argv)
    assert SECRET not in rendered
    assert str(directory) in argv
    assert "--headed" in argv
    assert "--chrome-path" in argv
    assert str(chrome) in argv
    assert "--no-sandbox" not in argv
    assert "--stealth" not in argv


def test_chromium_path_must_be_absolute_and_executable(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv("KRONIKA_CHROMIUM_PATH", raising=False)
    assert configured_chromium("chromium") is None
    assert configured_chromium(None) is None
    chrome = tmp_path / "chromium"
    chrome.write_text("", encoding="utf-8")
    assert configured_chromium(str(chrome)) is None
    chrome.chmod(0o755)
    monkeypatch.setenv("KRONIKA_CHROMIUM_PATH", str(chrome))
    assert configured_chromium(None) == chrome
