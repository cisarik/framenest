"""Repository contracts for capture units and capture activation.

These tests read unit sources and drive the release helper with a fake command
runner. They do not contact a host, create a real token, or start a service.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import shlex
import sys

import pytest

from kronika_capture.config import CAPTURE_RESTART_BRAKE_MS, PROTO_VERSION

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
ENGINE_PATH = REPOSITORY_ROOT / "deploy" / "ubuntu" / "framenest_release.py"
SYSTEMD = REPOSITORY_ROOT / "deploy" / "systemd"
ENV_EXAMPLE = SYSTEMD / "kronika-capture.env.example"
PROTOCOL_JS = (
    REPOSITORY_ROOT
    / "src"
    / "kronika_capture"
    / "_assets"
    / "extension"
    / "src"
    / "protocol.js"
)
DRIVER_JS = (
    REPOSITORY_ROOT
    / "src"
    / "kronika_capture"
    / "_assets"
    / "extension"
    / "src"
    / "headless"
    / "driver.mjs"
)

_SPEC = importlib.util.spec_from_file_location("framenest_release_capture", ENGINE_PATH)
assert _SPEC is not None and _SPEC.loader is not None
engine = importlib.util.module_from_spec(_SPEC)
sys.modules["framenest_release_capture"] = engine
_SPEC.loader.exec_module(engine)

RELEASE = "a" * 40
PREV = "c" * 40
PREV_PATH = f"/opt/framenest/releases/{PREV}"
TARGET = f"/opt/framenest/releases/{RELEASE}"

UNITS = {
    "xvfb": SYSTEMD / "kronika-capture-xvfb.service",
    "bridge": SYSTEMD / "kronika-capture-bridge.service",
    "runner": SYSTEMD / "kronika-capture-runner.service",
    "vnc": SYSTEMD / "kronika-capture-vnc.service",
    "view": SYSTEMD / "kronika-capture-view.service",
}


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _git_response(combined: str) -> str:
    if "src/kronika_capture" in combined and "rev-parse" in combined:
        return "d" * 40
    if " show " in combined and "kronika-capture" in combined:
        return "capture-contract\n"
    raise AssertionError(f"unexpected git command: {combined}")


class _Git:
    def __call__(self, argv: list[str], input_bytes: bytes | None) -> str:
        return _git_response(" ".join(argv))


def _identity() -> dict[str, str]:
    return engine.capture_runtime_identity(_Git(), RELEASE)


def _target_manifest(**overrides: str) -> str:
    payload = engine.make_manifest(
        release_sha=RELEASE,
        ap_pin="b" * 40,
        superproject_sha256="a" * 64,
        ap_archive_sha256="b" * 64,
        **_identity(),
    )
    payload.update(overrides)
    return json.dumps(payload)


class CaptureRunner:
    def __init__(
        self,
        *,
        blocked: list[str] | None = None,
        brake: str = "brake=ok",
        readiness: str = "readiness=ready",
        capture_link: str = "absent",
        capture_protocol: str = "1",
        manifest_overrides: dict[str, str] | None = None,
    ) -> None:
        self.calls: list[tuple[list[str], bytes | None]] = []
        self.blocked = list(blocked or ["blocked=none"])
        self.brake = brake
        self.readiness = readiness
        self.capture_link = capture_link
        self.capture_protocol = capture_protocol
        self.manifest_overrides = manifest_overrides or {}

    def __call__(self, argv: list[str], input_bytes: bytes | None) -> str:
        self.calls.append((list(argv), input_bytes))
        combined = " ".join(argv)
        if combined.startswith("git "):
            return _git_response(combined)
        if combined.startswith("ssh "):
            return self._ssh(combined)
        raise AssertionError(combined)

    def _ssh(self, combined: str) -> str:
        if "kronika-capture-work-gate" in combined:
            if not self.blocked:
                return "blocked=none"
            return self.blocked.pop(0)
        if "kronika-capture-brake-gate" in combined:
            return self.brake
        if "kronika-capture-readiness-gate" in combined:
            return self.readiness
        if "test -L /opt/framenest/capture-current" in combined:
            return self.capture_link
        if "readlink -n /opt/framenest/current" in combined:
            return PREV_PATH
        if ".framenest-release-manifest.json" in combined and PREV in combined:
            return json.dumps(
                {
                    "framenest_release_sha": PREV,
                    "capture_bridge_protocol": self.capture_protocol,
                }
            )
        if ".framenest-release-manifest.json" in combined:
            return _target_manifest(**self.manifest_overrides)
        if ".framenest-release-sha" in combined and "cat" in combined:
            return RELEASE + "\n"
        if "test -e " in combined or "test -x " in combined:
            return ""
        if "capture-current.next" in combined:
            return ""
        if "restart kronika-capture-runner.service" in combined:
            return ""
        raise AssertionError(f"unexpected ssh command: {combined}")


def _ssh(runner: CaptureRunner) -> str:
    return "\n".join(" ".join(argv) for argv, _ in runner.calls if argv and argv[0] == "ssh")


def _index(runner: CaptureRunner, needle: str) -> int:
    for index, (argv, _) in enumerate(runner.calls):
        if argv and argv[0] == "ssh" and needle in " ".join(argv):
            return index
    raise AssertionError(needle)


def _activate(extra: list[str] | None = None, command: str = "activate-capture") -> list[str]:
    argv = [command, "--release", RELEASE, "--yes", "--target", "nuc", "--user", "op", "--identity", "identity"]
    if extra:
        argv.extend(extra)
    return argv


def test_unit_sources_parse_and_keep_the_capture_boundary() -> None:
    for name, path in UNITS.items():
        text = _text(path)
        assert "[Unit]" in text
        assert "[Service]" in text
        assert "PartOf=framenest.service" not in text
        assert "Group=framenest" not in text
        assert "SupplementaryGroups=" not in text
        assert "User=kronika-capture" in text
        assert name in path.name

    xvfb = _text(UNITS["xvfb"])
    runner = _text(UNITS["runner"])
    bridge = _text(UNITS["bridge"])
    vnc = _text(UNITS["vnc"])
    view = _text(UNITS["view"])

    assert "Restart=no" in xvfb
    assert "Restart=on-failure" not in xvfb
    assert "Restart=no" in runner
    assert "Restart=on-failure" not in runner
    assert "Restart=on-failure" in bridge
    assert "PrivateTmp=true" not in xvfb
    assert "PrivateTmp=true" not in runner
    assert "/tmp/.X11-unix" in xvfb
    assert "/tmp/.X11-unix" in runner
    assert "/run/kronika-capture/Xauthority" in xvfb
    assert "/run/kronika-capture/Xauthority" in runner
    assert "-auth /run/kronika-capture/Xauthority" in xvfb
    assert "-nolisten tcp" in xvfb
    assert " -ac" not in xvfb
    assert "-ac\n" not in xvfb
    assert "LoadCredential=token:/etc/kronika-capture/credentials/kronika-bridge-token" in bridge
    assert "LoadCredential=token:/etc/kronika-capture/credentials/kronika-bridge-token" in runner
    for unit in (bridge, runner, vnc, view, xvfb):
        assert "0.0.0.0" not in unit
    assert "--profile /var/lib/kronika-capture/profile" in runner
    assert "WorkingDirectory=/opt/framenest/capture-current" in bridge
    assert "WorkingDirectory=/opt/framenest/capture-current" in runner
    assert "[Install]" in xvfb and "[Install]" in bridge and "[Install]" in runner
    assert "[Install]" not in vnc
    assert "[Install]" not in view
    assert "RuntimeMaxSec=1800" in vnc
    assert "RuntimeMaxSec=1800" in view
    assert "-localhost" in vnc
    assert "-rfbport 5900" in vnc
    assert "127.0.0.1:6080" in view
    assert "127.0.0.1:5900" in view
    assert "Restart=no" in vnc
    assert "Restart=no" in view
    assert "StateDirectoryMode=0700" in bridge
    assert "StateDirectoryMode=0700" in runner


def _exec_start_args(unit_text: str) -> list[str]:
    for line in unit_text.splitlines():
        if line.startswith("ExecStart="):
            argv = shlex.split(line.split("=", 1)[1])
            assert len(argv) >= 2
            return argv[1:]
    raise AssertionError("ExecStart missing")


def test_cli_execstart_parses_and_rejects_the_old_option_order() -> None:
    from kronika_capture.cli import build_parser

    parser = build_parser()
    expected = {
        "bridge": [
            "--state-dir",
            "/var/lib/kronika-capture",
            "bridge",
            "run",
            "--port",
            "8765",
        ],
        "runner": [
            "--state-dir",
            "/var/lib/kronika-capture",
            "runner",
            "run",
            "--profile",
            "/var/lib/kronika-capture/profile",
            "--port",
            "8765",
            "--headed",
        ],
    }
    for name, args in expected.items():
        assert _exec_start_args(_text(UNITS[name])) == args
        parser.parse_args(args)

    rejected = [
        ["bridge", "run", "--state-dir", "/var/lib/kronika-capture", "--port", "8765"],
        [
            "runner",
            "run",
            "--state-dir",
            "/var/lib/kronika-capture",
            "--profile",
            "/var/lib/kronika-capture/profile",
            "--port",
            "8765",
            "--headed",
        ],
    ]
    for old in rejected:
        with pytest.raises(SystemExit) as caught:
            parser.parse_args(old)
        assert caught.value.code == 2


def test_xvfb_lock_strategy_keeps_tmp_writable() -> None:
    xvfb = _text(UNITS["xvfb"])
    runner = _text(UNITS["runner"])
    exec_start = next(line for line in xvfb.splitlines() if line.startswith("ExecStart="))
    assert exec_start == (
        "ExecStart=/usr/bin/Xvfb :99 -screen 0 1280x800x24 "
        "-nolisten tcp -auth /run/kronika-capture/Xauthority"
    )
    assert "-nolisten tcp" in exec_start
    assert "-auth /run/kronika-capture/Xauthority" in exec_start
    assert "-nolock" not in exec_start
    assert "-ac" not in exec_start
    assert "ReadWritePaths=/tmp /tmp/.X11-unix /run/kronika-capture" in xvfb
    assert "PrivateTmp=true" not in xvfb
    assert "PrivateTmp=true" not in runner


def test_env_template_has_no_secret_and_matches_documented_paths() -> None:
    text = _text(ENV_EXAMPLE)
    assert "KRONIKA_CHROMIUM_PATH=/usr/bin/chromium" in text
    for path in (
        "/var/lib/kronika-capture",
        "/var/lib/kronika-capture/profile",
        "/var/lib/kronika-capture/capture-journal.sqlite3",
        "/var/lib/kronika-capture/staging",
        "/run/kronika-capture",
        "/opt/framenest/capture-current",
        "/etc/kronika-capture/capture.env",
    ):
        assert path in text
    lowered = text.lower()
    for forbidden in ("password=", "api_key=", "begin private", "bearer ", "cookie="):
        assert forbidden not in lowered
    assert "do not put" in lowered


def test_capture_gate_scripts_compile() -> None:
    for builder in (
        engine.cmd_remote_capture_work_gate,
        engine.cmd_remote_capture_brake_gate,
        engine.cmd_remote_capture_readiness_gate,
    ):
        parts = shlex.split(builder())
        assert parts[:4] == ["sudo", "-n", "python3", "-c"]
        compile(parts[4], "<capture-gate>", "exec")
        assert "LoadCredential" not in parts[4]


def test_brake_and_protocol_constants_match_the_capture_sources() -> None:
    assert engine.CAPTURE_BRAKE_MS == CAPTURE_RESTART_BRAKE_MS == 300_000
    assert engine.CAPTURE_BRIDGE_PROTOCOL == str(PROTO_VERSION) == "1"
    assert "export const PROTO_VERSION = 1;" in _text(PROTOCOL_JS)
    assert "300000" in _text(DRIVER_JS)
    assert engine.CAPTURE_BRAKE_DIRECTORY == (
        "/var/lib/kronika-capture/profile.capture-launch"
    )


def test_capture_activation_switches_once_and_reports_both_shas(
    capsys: pytest.CaptureFixture[str],
) -> None:
    runner = CaptureRunner()
    result = engine.main(_activate(), runner=runner)
    captured = capsys.readouterr()
    assert result == engine.EXIT_OK
    assert f"web_release: {PREV}" in captured.out
    assert f"capture_release: {RELEASE}" in captured.out
    transcript = _ssh(runner)
    assert transcript.count("restart kronika-capture-runner.service") == 1
    assert "restart framenest.service" not in transcript
    assert "framenest-db" not in transcript
    assert "migrate" not in transcript
    assert _index(runner, "kronika-capture-work-gate") < _index(runner, "kronika-capture-brake-gate")
    assert _index(runner, "kronika-capture-brake-gate") < _index(runner, "capture-current.next")
    assert _index(runner, "capture-current.next") < _index(
        runner, "restart kronika-capture-runner.service"
    )
    assert _index(runner, "restart kronika-capture-runner.service") < _index(
        runner, "kronika-capture-readiness-gate"
    )


def test_capture_activation_refuses_live_or_paused_work() -> None:
    for blocked in ("blocked=live", "blocked=paused"):
        runner = CaptureRunner(blocked=[blocked])
        result = engine.main(_activate(), runner=runner)
        assert result == engine.EXIT_CAPTURE_BUSY
        transcript = _ssh(runner)
        assert "capture-current.next" not in transcript
        assert "restart kronika-capture-runner.service" not in transcript


def test_capture_activation_drains_queued_work_then_restarts_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(engine.time, "sleep", lambda _seconds: None)
    runner = CaptureRunner(blocked=["blocked=queued", "blocked=none"])
    assert engine.main(_activate(), runner=runner) == engine.EXIT_OK
    assert _ssh(runner).count("kronika-capture-work-gate") == 2
    assert _ssh(runner).count("restart kronika-capture-runner.service") == 1


def test_capture_activation_stops_when_queued_work_does_not_drain(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class _Clock:
        def __init__(self) -> None:
            self.now = 50.0

        def monotonic(self) -> float:
            return self.now

        def sleep(self, seconds: float) -> None:
            self.now += seconds

    clock = _Clock()
    monkeypatch.setattr(engine.time, "monotonic", clock.monotonic)
    monkeypatch.setattr(engine.time, "sleep", clock.sleep)
    monkeypatch.setattr(engine, "CAPTURE_DRAIN_DEADLINE_SECONDS", 0)
    runner = CaptureRunner(blocked=["blocked=queued"])
    assert engine.main(_activate(), runner=runner) == engine.EXIT_CAPTURE_BUSY
    assert "restart kronika-capture-runner.service" not in _ssh(runner)


def test_capture_activation_enforces_the_brake_before_switch() -> None:
    runner = CaptureRunner(brake="brake=refuse")
    assert engine.main(_activate(), runner=runner) == engine.EXIT_CAPTURE_BRAKE
    transcript = _ssh(runner)
    assert "kronika-capture-brake-gate" in transcript
    assert "capture-current.next" not in transcript
    assert "restart kronika-capture-runner.service" not in transcript


def test_failed_browser_readiness_does_not_restart_again(
    capsys: pytest.CaptureFixture[str],
) -> None:
    runner = CaptureRunner(readiness="readiness=browser_unavailable")
    result = engine.main(_activate(), runner=runner)
    captured = capsys.readouterr()
    assert result == engine.EXIT_SERVICE_TERMINAL
    assert _ssh(runner).count("restart kronika-capture-runner.service") == 1
    assert _ssh(runner).count("kronika-capture-readiness-gate") == 1
    assert f"web_release: {PREV}" in captured.out
    assert f"capture_release: {RELEASE}" in captured.out
    assert "restart framenest.service" not in _ssh(runner)


def test_incompatible_capture_protocol_refuses_before_restart() -> None:
    runner = CaptureRunner(capture_link=PREV_PATH, capture_protocol="9")
    assert engine.main(_activate(), runner=runner) == engine.EXIT_SOURCE_GATE
    assert "restart kronika-capture-runner.service" not in _ssh(runner)


def test_capture_rollback_uses_the_same_single_runner_restart() -> None:
    runner = CaptureRunner()
    assert engine.main(_activate(command="rollback-capture"), runner=runner) == engine.EXIT_OK
    transcript = _ssh(runner)
    assert transcript.count("restart kronika-capture-runner.service") == 1
    assert "restart framenest.service" not in transcript
    assert "/opt/framenest/current.next" not in transcript


def test_web_rollback_leaves_capture_untouched(capsys: pytest.CaptureFixture[str]) -> None:
    from tests.contract import test_nuc_release_remote_contract as remote

    class _Rollback(remote.FakeRunner):
        def _ssh_respond(self, combined: str, input_bytes: bytes | None) -> str:
            if "test -e /opt/framenest/releases/" in combined and ".framenest-release-sha" not in combined:
                return ""
            if ".framenest-release-sha" in combined and "test -e" in combined:
                return ""
            if "test -x /opt/framenest/releases/" in combined:
                return ""
            return super()._ssh_respond(combined, input_bytes)

    runner = _Rollback()
    result = remote.engine.main(remote._args("rollback"), runner=runner)
    output = capsys.readouterr().out
    assert result == remote.engine.EXIT_OK
    transcript = remote._ssh_combined(runner)
    assert "capture-current.next" not in transcript
    assert "kronika-capture-runner" not in transcript
    assert transcript.count("restart framenest.service") == 1
    assert "capture_release: absent" in output
    assert f"web_release: {RELEASE}" in output


def test_referenced_release_paths_keep_both_pointers() -> None:
    assert engine.retained_release_paths(TARGET, PREV_PATH) == (TARGET, PREV_PATH)
    assert engine.retained_release_paths(TARGET, TARGET) == (TARGET,)
    assert engine.retained_release_paths(TARGET, "absent") == (TARGET,)
