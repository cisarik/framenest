from __future__ import annotations

import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
from typing import Any

import pytest

from framenest.adapters.cli import development as cli
from framenest.infrastructure.runtime.development import RuntimeStatus

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
ROOT_WRAPPER = REPOSITORY_ROOT / "framenest"


class _Runtime:
    last: "_Runtime | None" = None

    def __init__(self) -> None:
        self.open_after_start: list[bool] = []
        self.opened = False
        self.log_lines = ["one\n", "two\n"]
        _Runtime.last = self

    def start(self, *, open_after_start: bool) -> Any:
        self.open_after_start.append(open_after_start)
        return _result(True, "running", "started")

    def stop(self) -> Any:
        return _result(True, "stopped", "stopped")

    def restart(self, *, open_after_start: bool) -> Any:
        self.open_after_start.append(open_after_start)
        return _result(True, "running", "restarted")

    def status(self) -> RuntimeStatus:
        return RuntimeStatus(
            kind="running",
            url="http://127.0.0.1:8000/",
            pid=123,
            database_state="at_head",
            log_available=True,
            message="FrameNest is running.",
        )

    def open(self) -> Any:
        self.opened = True
        return _result(True, "running", "opened")

    def read_log_tail(self, *, lines: int) -> list[str]:
        return self.log_lines[-lines:]

    def follow_log(self) -> Any:
        return iter(())


def _result(ok: bool, kind: str, message: str) -> Any:
    status = RuntimeStatus(
        kind=kind,  # type: ignore[arg-type]
        url="http://127.0.0.1:8000/" if kind == "running" else None,
        pid=123 if kind == "running" else None,
        database_state="at_head",
        log_available=True,
        message=message,
    )
    return type("Result", (), {"ok": ok, "status": status, "message": message})()


def test_root_wrapper_is_executable_fish_script() -> None:
    mode = ROOT_WRAPPER.stat().st_mode

    assert mode & stat.S_IXUSR
    assert ROOT_WRAPPER.read_text(encoding="utf-8").splitlines()[0] == "#!/usr/bin/env fish"
    subprocess.run(["fish", "--no-execute", str(ROOT_WRAPPER)], check=True)


def test_root_wrapper_avoids_eval_and_bash_only_constructs() -> None:
    source = ROOT_WRAPPER.read_text(encoding="utf-8")

    assert "eval" not in source
    assert "[[" not in source
    assert "$?" not in source
    assert "function " in source
    assert "POETRY_VIRTUALENVS_IN_PROJECT" in source
    assert "uv python find 3.13.14" in source
    assert "uv python install 3.13.14" in source
    assert "poetry install --no-interaction" in source


def test_root_wrapper_resolves_script_root_from_another_cwd_and_preserves_exit(
    tmp_path: Path,
) -> None:
    launcher = tmp_path / "framenest"
    shutil.copy2(ROOT_WRAPPER, launcher)
    venv_bin = tmp_path / ".venv" / "bin"
    venv_bin.mkdir(parents=True)
    controller = venv_bin / "framenest-dev"
    controller.write_text(
        "#!/bin/sh\nprintf '%s\\n' \"$PWD\" \"$1\" \"$2\"\nexit 37\n",
        encoding="utf-8",
    )
    controller.chmod(0o755)
    cwd = tmp_path / "elsewhere"
    cwd.mkdir()

    result = subprocess.run(
        ["fish", str(launcher), "status", "value with spaces"],
        cwd=cwd,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 37
    lines = result.stdout.splitlines()
    assert lines == [str(cwd), "status", "value with spaces"]


def test_root_wrapper_routes_ai_commands_to_ai_controller(tmp_path: Path) -> None:
    launcher = tmp_path / "framenest"
    shutil.copy2(ROOT_WRAPPER, launcher)
    venv_bin = tmp_path / ".venv" / "bin"
    venv_bin.mkdir(parents=True)
    controller = venv_bin / "framenest-ai"
    controller.write_text(
        "#!/bin/sh\nprintf '%s\\n' \"$1\" \"$2\"\nexit 23\n",
        encoding="utf-8",
    )
    controller.chmod(0o755)

    result = subprocess.run(
        ["fish", str(launcher), "ai", "status", "--config-path"],
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 23
    assert result.stdout.splitlines() == ["status", "--config-path"]


def test_setup_uses_uv_managed_python_and_poetry_install_without_real_download(
    tmp_path: Path,
) -> None:
    launcher = tmp_path / "framenest"
    shutil.copy2(ROOT_WRAPPER, launcher)
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    log = tmp_path / "commands.log"
    uv = bin_dir / "uv"
    uv.write_text(
        "#!/bin/sh\n"
        "echo uv:$* >> \"$LOG\"\n"
        "if [ \"$1 $2 $3\" = \"python find 3.13.14\" ]; then\n"
        "  if [ -f \"$FOUND\" ]; then echo /tmp/python-3.13.14; exit 0; fi\n"
        "  touch \"$FOUND\"; exit 1\n"
        "fi\n"
        "exit 0\n",
        encoding="utf-8",
    )
    poetry = bin_dir / "poetry"
    poetry.write_text(
        "#!/bin/sh\n"
        "echo poetry:$*:venv=$POETRY_VIRTUALENVS_IN_PROJECT >> \"$LOG\"\n"
        "mkdir -p .venv/bin\n"
        "printf '#!/bin/sh\\nexit 0\\n' > .venv/bin/framenest-dev\n"
        "chmod +x .venv/bin/framenest-dev\n"
        "exit 0\n",
        encoding="utf-8",
    )
    uv.chmod(0o755)
    poetry.chmod(0o755)

    env = os.environ.copy()
    env["PATH"] = f"{bin_dir}{os.pathsep}{env['PATH']}"
    env["LOG"] = str(log)
    env["FOUND"] = str(tmp_path / "found")
    result = subprocess.run(
        ["fish", "-C", f"fish_add_path -p {bin_dir}", str(launcher), "setup"],
        cwd=tmp_path / "bin",
        env=env,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 0
    recorded = log.read_text(encoding="utf-8")
    assert "uv:python find 3.13.14" in recorded
    assert "uv:python install 3.13.14" in recorded
    assert "poetry:env use /tmp/python-3.13.14:venv=true" in recorded
    assert "poetry:install --no-interaction:venv=true" in recorded


def test_cli_help_and_command_help(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as root_help:
        cli.main(["--help"])
    with pytest.raises(SystemExit) as command_help:
        cli.main(["start", "--help"])

    assert root_help.value.code == 0
    assert command_help.value.code == 0
    assert "start" in capsys.readouterr().out


def test_cli_invalid_command_exits_with_usage_code() -> None:
    with pytest.raises(SystemExit) as exc_info:
        cli.main(["server_start"])

    assert exc_info.value.code == cli.EXIT_USAGE


def test_cli_start_no_open_and_restart_no_open_delegate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(cli, "DevelopmentRuntime", _Runtime)

    assert cli.main(["start", "--no-open"]) == cli.EXIT_OK
    assert _Runtime.last is not None
    assert _Runtime.last.open_after_start == [False]
    assert cli.main(["restart", "--no-open"]) == cli.EXIT_OK
    assert _Runtime.last is not None
    assert _Runtime.last.open_after_start == [False]


def test_cli_status_open_and_logs(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setattr(cli, "DevelopmentRuntime", _Runtime)

    assert cli.main(["status"]) == cli.EXIT_OK
    assert cli.main(["open"]) == cli.EXIT_OK
    assert cli.main(["logs", "--lines", "1"]) == cli.EXIT_OK

    output = capsys.readouterr().out
    assert "Status: running" in output
    assert "opened" in output
    assert "two" in output


def test_cli_missing_log_is_clean(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    class MissingLogRuntime(_Runtime):
        def read_log_tail(self, *, lines: int) -> list[str]:
            return []

    monkeypatch.setattr(cli, "DevelopmentRuntime", MissingLogRuntime)

    assert cli.main(["logs"]) == cli.EXIT_OK
    assert "not yet available" in capsys.readouterr().out


def test_cli_maps_stopped_unhealthy_and_conflict_exit_codes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class StoppedRuntime(_Runtime):
        def status(self) -> RuntimeStatus:
            return RuntimeStatus("stopped", None, None, "uninitialized", False, "stopped")

    class UnhealthyRuntime(_Runtime):
        def start(self, *, open_after_start: bool) -> Any:
            return _result(False, "unhealthy", "not healthy")

    class ConflictRuntime(_Runtime):
        def start(self, *, open_after_start: bool) -> Any:
            return _result(False, "conflict", "conflict")

    monkeypatch.setattr(cli, "DevelopmentRuntime", StoppedRuntime)
    assert cli.main(["status"]) == cli.EXIT_STOPPED
    monkeypatch.setattr(cli, "DevelopmentRuntime", UnhealthyRuntime)
    assert cli.main(["start"]) == cli.EXIT_UNHEALTHY
    monkeypatch.setattr(cli, "DevelopmentRuntime", ConflictRuntime)
    assert cli.main(["start"]) == cli.EXIT_CONFLICT


def test_cli_sanitizes_runtime_errors(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    class BrokenRuntime:
        def __init__(self) -> None:
            raise cli.DevelopmentRuntimeError("sanitized failure")

    monkeypatch.setattr(cli, "DevelopmentRuntime", BrokenRuntime)

    assert cli.main(["status"]) == cli.EXIT_ERROR
    assert "sanitized failure" in capsys.readouterr().err


def test_cli_import_has_no_runtime_side_effects() -> None:
    command = [
        sys.executable,
        "-c",
        "import framenest.adapters.cli.development; print('imported')",
    ]

    result = subprocess.run(command, check=True, text=True, capture_output=True)

    assert result.stdout == "imported\n"
