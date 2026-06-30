from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import signal
import subprocess
from typing import Any

import pytest

from framenest.infrastructure.runtime import development
from framenest.infrastructure.runtime.development import (
    DevelopmentRuntime,
    DevelopmentRuntimeError,
    ManagedState,
    ProcessSnapshot,
    resolve_development_paths,
)


@dataclass(frozen=True)
class _Migration:
    state: str


@dataclass
class _Process:
    pid: int


def _env(tmp_path: Path, *, port: int = 48123) -> dict[str, str]:
    return {
        "FRAMENEST_DATABASE_PATH": str(tmp_path / "data" / "catalog.sqlite3"),
        "FRAMENEST_DEVELOPMENT_RUNTIME_DIR": str(tmp_path / "state"),
        "FRAMENEST_DEVELOPMENT_LOG_DIR": str(tmp_path / "logs"),
        "FRAMENEST_PORT": str(port),
    }


def _runtime(tmp_path: Path, *, port: int = 48123) -> DevelopmentRuntime:
    return DevelopmentRuntime(environ=_env(tmp_path, port=port))


def _state(runtime: DevelopmentRuntime, *, pid: int = 4242, start: str = "started") -> ManagedState:
    return ManagedState(
        schema=development.STATE_SCHEMA,
        pid=pid,
        process_start_identity=start,
        executable="/tmp/python",
        launch_module=development.LAUNCH_MODULE,
        host=development.LOOPBACK_HOST,
        port=48123,
        database_path=runtime.paths.database_path,
        log_path=runtime.paths.log_path,
        created_at=1.0,
    )


def test_macos_development_path_resolution_uses_user_library(tmp_path: Path) -> None:
    paths = resolve_development_paths(environ={}, platform_name="darwin", home=tmp_path)

    assert paths.database_path == (
        tmp_path / "Library" / "Application Support" / "FrameNest" / "development" / "catalog.sqlite3"
    )
    assert paths.runtime_dir == (
        tmp_path / "Library" / "Application Support" / "FrameNest" / "development" / "runtime"
    )
    assert paths.log_path == tmp_path / "Library" / "Logs" / "FrameNest" / "development" / "server.log"


def test_xdg_fallback_path_resolution(tmp_path: Path) -> None:
    env = {
        "XDG_DATA_HOME": str(tmp_path / "xdg-data"),
        "XDG_STATE_HOME": str(tmp_path / "xdg-state"),
    }

    paths = resolve_development_paths(environ=env, platform_name="linux", home=tmp_path)

    assert paths.database_path == tmp_path / "xdg-data" / "FrameNest" / "development" / "catalog.sqlite3"
    assert paths.runtime_dir == tmp_path / "xdg-state" / "FrameNest" / "development" / "runtime"
    assert paths.log_path == tmp_path / "xdg-state" / "FrameNest" / "development" / "logs" / "server.log"


def test_absolute_override_validation_rejects_relative_paths(tmp_path: Path) -> None:
    env = _env(tmp_path)
    env["FRAMENEST_DEVELOPMENT_RUNTIME_DIR"] = "relative-state"

    with pytest.raises(DevelopmentRuntimeError, match="absolute path"):
        DevelopmentRuntime(environ=env)


def test_atomic_state_write_and_read_round_trip(tmp_path: Path) -> None:
    runtime = _runtime(tmp_path)
    state = _state(runtime)

    runtime._write_state(state)

    assert runtime.paths.state_path.exists()
    assert runtime._read_state() == state
    assert not list(runtime.paths.runtime_dir.glob("*.tmp"))


def test_malformed_state_reports_conflict(tmp_path: Path) -> None:
    runtime = _runtime(tmp_path)
    runtime.paths.runtime_dir.mkdir(parents=True)
    runtime.paths.state_path.write_text("{not-json", encoding="utf-8")

    status = runtime.status()

    assert status.kind == "conflict"
    assert "malformed" in status.message


def test_missing_state_reports_stopped(tmp_path: Path) -> None:
    runtime = _runtime(tmp_path)

    assert runtime.status().kind == "stopped"


def test_stale_dead_pid_is_detected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    runtime = _runtime(tmp_path)
    runtime._write_state(_state(runtime))
    monkeypatch.setattr(runtime, "_process_snapshot", lambda pid: None)

    assert runtime.status().kind == "stale"


def test_live_verified_managed_pid_is_running(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    runtime = _runtime(tmp_path)
    runtime._write_state(_state(runtime, start="same"))
    monkeypatch.setattr(
        runtime,
        "_process_snapshot",
        lambda pid: ProcessSnapshot(pid=pid, start_identity="same", command="python -m framenest.server"),
    )
    monkeypatch.setattr(runtime, "_health_is_ok", lambda port: True)

    status = runtime.status()

    assert status.kind == "running"
    assert status.pid == 4242


def test_pid_identity_mismatch_is_conflict(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    runtime = _runtime(tmp_path)
    runtime._write_state(_state(runtime, start="expected"))
    monkeypatch.setattr(
        runtime,
        "_process_snapshot",
        lambda pid: ProcessSnapshot(pid=pid, start_identity="other", command="python -m framenest.server"),
    )

    assert runtime.status().kind == "conflict"


def test_pid_reuse_without_launcher_marker_is_conflict(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runtime = _runtime(tmp_path)
    runtime._write_state(_state(runtime, start="same"))
    monkeypatch.setattr(
        runtime,
        "_process_snapshot",
        lambda pid: ProcessSnapshot(pid=pid, start_identity="same", command="python unrelated.py"),
    )

    assert runtime.status().kind == "conflict"


def test_start_is_idempotent_for_healthy_managed_process(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    opened: list[str] = []
    runtime = DevelopmentRuntime(environ=_env(tmp_path), open_browser=opened.append)
    runtime._write_state(_state(runtime, start="same"))
    monkeypatch.setattr(
        runtime,
        "_process_snapshot",
        lambda pid: ProcessSnapshot(pid=pid, start_identity="same", command="python -m framenest.server"),
    )
    monkeypatch.setattr(runtime, "_health_is_ok", lambda port: True)

    result = runtime.start(open_after_start=True)

    assert result.ok is True
    assert "already running" in result.message
    assert opened == [runtime.url]


def test_start_refuses_unmanaged_port_conflict(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runtime = _runtime(tmp_path)
    monkeypatch.setattr(runtime, "_port_is_occupied", lambda: True)

    result = runtime.start(open_after_start=False)

    assert result.ok is False
    assert result.status.kind == "conflict"


def test_start_reports_migration_failure_without_spawning(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runtime = _runtime(tmp_path)
    spawned = False
    monkeypatch.setattr(runtime, "_migrate_database", lambda: (_ for _ in ()).throw(RuntimeError("secret path")))
    monkeypatch.setattr(runtime, "_spawn_server_process", lambda: spawned)

    result = runtime.start(open_after_start=False)

    assert result.ok is False
    assert result.message == "Development database migration failed."
    assert str(tmp_path) not in result.message
    assert spawned is False


def test_child_spawn_failure_is_sanitized(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    runtime = _runtime(tmp_path)
    monkeypatch.setattr(runtime, "_migrate_database", lambda: _Migration("at_head"))
    monkeypatch.setattr(runtime, "_spawn_server_process", lambda: (_ for _ in ()).throw(OSError("boom")))

    result = runtime.start(open_after_start=False)

    assert result.ok is False
    assert result.status.kind == "unhealthy"
    assert result.message == "FrameNest startup failed. Check logs for details."


def test_health_timeout_terminates_only_new_child_and_cleans_state(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runtime = _runtime(tmp_path)
    terminated: list[int] = []
    monkeypatch.setattr(runtime, "_migrate_database", lambda: _Migration("at_head"))
    monkeypatch.setattr(runtime, "_spawn_server_process", lambda: _Process(9090))
    monkeypatch.setattr(
        runtime,
        "_wait_for_process_snapshot",
        lambda pid: ProcessSnapshot(pid=pid, start_identity="same", command="python -m framenest.server"),
    )
    monkeypatch.setattr(runtime, "_wait_for_health", lambda: False)
    monkeypatch.setattr(runtime, "_is_pid_live", lambda pid: True)
    monkeypatch.setattr(runtime, "_terminate_pid", terminated.append)
    monkeypatch.setattr(runtime, "_wait_for_pid_exit", lambda pid, timeout_seconds: True)

    result = runtime.start(open_after_start=False)

    assert result.ok is False
    assert terminated == [9090]
    assert not runtime.paths.state_path.exists()


def test_health_payload_mismatch_is_not_ready(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class _Response:
        status = 200

        def __enter__(self) -> "_Response":
            return self

        def __exit__(self, *args: object) -> None:
            return None

        def read(self) -> bytes:
            return json.dumps({"status": "not-ok"}).encode()

    runtime = _runtime(tmp_path)
    monkeypatch.setattr(development, "urlopen", lambda url, timeout: _Response())

    assert runtime._health_is_ok(48123) is False


def test_successful_readiness_accepts_health_payload(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    checks = iter([False, True])
    runtime = _runtime(tmp_path)
    monkeypatch.setattr(runtime, "_health_is_ok", lambda port: next(checks))
    monkeypatch.setattr(runtime, "_sleep", lambda seconds: None)

    assert runtime._wait_for_health() is True


def test_graceful_stop_removes_state_after_verified_process_exits(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runtime = _runtime(tmp_path)
    runtime._write_state(_state(runtime, start="same"))
    terminated: list[int] = []
    monkeypatch.setattr(
        runtime,
        "_process_snapshot",
        lambda pid: ProcessSnapshot(pid=pid, start_identity="same", command="python -m framenest.server"),
    )
    monkeypatch.setattr(runtime, "_health_is_ok", lambda port: True)
    monkeypatch.setattr(runtime, "_terminate_pid", terminated.append)
    monkeypatch.setattr(runtime, "_wait_for_pid_exit", lambda pid, timeout_seconds: True)

    result = runtime.stop()

    assert result.ok is True
    assert terminated == [4242]
    assert not runtime.paths.state_path.exists()


def test_stop_timeout_does_not_force_kill(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    runtime = _runtime(tmp_path)
    runtime._write_state(_state(runtime, start="same"))
    signals: list[int] = []
    monkeypatch.setattr(
        runtime,
        "_process_snapshot",
        lambda pid: ProcessSnapshot(pid=pid, start_identity="same", command="python -m framenest.server"),
    )
    monkeypatch.setattr(runtime, "_health_is_ok", lambda port: True)
    monkeypatch.setattr(runtime, "_terminate_pid", lambda pid: signals.append(signal.SIGTERM))
    monkeypatch.setattr(runtime, "_wait_for_pid_exit", lambda pid, timeout_seconds: False)

    result = runtime.stop()

    assert result.ok is False
    assert signals == [signal.SIGTERM]
    assert runtime.paths.state_path.exists()


def test_browser_open_failure_is_sanitized(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    runtime = DevelopmentRuntime(environ=_env(tmp_path), open_browser=lambda url: False)
    runtime._write_state(_state(runtime, start="same"))
    monkeypatch.setattr(
        runtime,
        "_process_snapshot",
        lambda pid: ProcessSnapshot(pid=pid, start_identity="same", command="python -m framenest.server"),
    )
    monkeypatch.setattr(runtime, "_health_is_ok", lambda port: True)

    result = runtime.open()

    assert result.ok is False
    assert result.message == "Browser opening failed."


def test_spawn_environment_enforces_loopback_and_disposable_database(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, Any] = {}

    def spawn(*args: Any, **kwargs: Any) -> _Process:
        captured["args"] = args
        captured["kwargs"] = kwargs
        return _Process(6060)

    runtime = DevelopmentRuntime(environ=_env(tmp_path), spawn_process=spawn)
    monkeypatch.setattr(runtime, "_migrate_database", lambda: _Migration("at_head"))
    monkeypatch.setattr(
        runtime,
        "_wait_for_process_snapshot",
        lambda pid: ProcessSnapshot(pid=pid, start_identity="same", command="python -m framenest.server"),
    )
    monkeypatch.setattr(runtime, "_wait_for_health", lambda: True)

    result = runtime.start(open_after_start=False)

    assert result.ok is True
    assert captured["args"][0][1:] == ["-m", "framenest.server"]
    env = captured["kwargs"]["env"]
    assert env["FRAMENEST_HOST"] == "127.0.0.1"
    assert env["FRAMENEST_DATABASE_PATH"] == str(tmp_path / "data" / "catalog.sqlite3")


def test_no_sigkill_literal_in_runtime_source() -> None:
    source = Path(development.__file__).read_text(encoding="utf-8")

    assert "SIGKILL" not in source
    assert "killall" not in source
    assert "pkill" not in source
    assert "0.0.0.0" not in source
