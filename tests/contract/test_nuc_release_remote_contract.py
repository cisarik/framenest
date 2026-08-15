"""Remote contract tests for the NUC release-update engine.

These tests exercise command building and the deploy/rollback orchestration flow
using a fake command runner and synthetic archives. They never contact a real
NUC, never use real sudo/systemd, and never inspect credentials or media.
"""

from __future__ import annotations

import importlib.util
import io
import json
from pathlib import Path
import shlex
import subprocess
import sys
import tarfile

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
ENGINE_PATH = REPOSITORY_ROOT / "deploy" / "ubuntu" / "framenest_release.py"

_SPEC = importlib.util.spec_from_file_location("framenest_release", ENGINE_PATH)
assert _SPEC is not None and _SPEC.loader is not None
engine = importlib.util.module_from_spec(_SPEC)
sys.modules["framenest_release"] = engine
_SPEC.loader.exec_module(engine)

RELEASE = "a" * 40
AP_PIN = "b" * 40
PREV = "c" * 40
TARGET = f"/opt/framenest/releases/{RELEASE}"
STAGING = f"/opt/framenest/releases/{RELEASE}.staging"
PREV_PATH = f"/opt/framenest/releases/{PREV}"

SSH = ["ssh", *engine.SSH_OPTIONS, "-i", "identity", "op@nuc"]


def _write_tar(path: str) -> None:
    with tarfile.open(path, "w") as archive:
        for member, content in (("pyproject.toml", b"[tool.poetry]\n"), ("poetry.lock", b"lock")):
            info = tarfile.TarInfo(name=member)
            info.size = len(content)
            archive.addfile(info, io.BytesIO(content))


class FakeRunner:
    def __init__(self, *, fail: str | None = None, fail_occurrence: int = 1,
                 fail_message: str = "simulated failure", exit_code: int | None = None) -> None:
        self.calls: list[tuple[list[str], bytes | None]] = []
        self.fail = fail
        self.fail_occurrence = fail_occurrence
        self.fail_message = fail_message
        self.exit_code = exit_code
        self._matches = 0
        self.current = PREV_PATH

    def __call__(self, argv: list[str], input_bytes: bytes | None) -> str:
        self.calls.append((list(argv), input_bytes))
        combined = " ".join(argv)
        if self.fail is not None and self.fail in combined:
            self._matches += 1
            if self._matches == self.fail_occurrence:
                raise engine.ReleaseError(self.fail_message, self.exit_code or engine.EXIT_TRANSPORT)
        return self._respond(combined, input_bytes)

    def _respond(self, combined: str, input_bytes: bytes | None) -> str:
        if combined.startswith("git "):
            return self._git_respond(combined)
        if combined.startswith("ssh "):
            return self._ssh_respond(combined, input_bytes)
        raise AssertionError(f"unexpected command: {combined}")

    def _git_respond(self, combined: str) -> str:
        if "rev-parse --show-toplevel" in combined:
            return "/repo"
        if "-C .ap rev-parse HEAD" in combined:
            return AP_PIN
        if "rev-parse HEAD" in combined:
            return RELEASE
        if "status --porcelain" in combined:
            return ""
        if "ls-remote origin refs/heads/main" in combined:
            return f"{RELEASE}\trefs/heads/main"
        if "ls-tree" in combined and ".ap" in combined:
            return f"160000 commit {AP_PIN}\t.ap"
        if "archive --format=tar" in combined:
            idx = combined.split().index("--output") + 1
            _write_tar(combined.split()[idx])
            return ""
        raise AssertionError(f"unexpected git command: {combined}")

    def _ssh_respond(self, combined: str, input_bytes: bytes | None) -> str:
        if "mkdir -m 0700 /run/framenest-release-deploy" in combined:
            return ""
        if "test ! -e" in combined:
            return ""
        if (
            "echo manifest" in combined
            and "echo sha" in combined
            and "echo none" in combined
        ):
            return "manifest"
        if "test -x /opt/framenest/tooling" in combined:
            return ""
        if "poetry --version" in combined:
            return "Poetry (version 2.4.1)"
        if "python3.13 --version" in combined:
            return "Python 3.13.14"
        if "df -Pk /opt/framenest" in combined:
            return "/dev/sda1 100000000 1000 99999000 1% /opt/framenest"
        if "cat > /run/framenest-release-deploy/framenest_release.py" in combined:
            return ""
        if "cat > /run/framenest-release-deploy/superproject.tar" in combined:
            return ""
        if "cat > /run/framenest-release-deploy/ap.tar" in combined:
            return ""
        if "install -d -o root -g root -m 0755" in combined:
            return ""
        if "_remote-extract" in combined:
            return ""
        if "_remote-relocate-venv-shebangs" in combined:
            return ""
        if "cat > /opt/framenest/releases/" in combined and "poetry.toml" in combined:
            return ""
        if (
            "cat > /opt/framenest/releases/" in combined
            and ".framenest-release-manifest.json" in combined
        ):
            return ""
        if (
            "cat > /opt/framenest/releases/" in combined
            and ".framenest-release-sha" in combined
        ):
            return ""
        if "sha256sum /opt/framenest/releases/" in combined and "poetry.lock" in combined:
            return "deadbeef  /opt/framenest/releases/placeholder/poetry.lock"
        if "check --lock" in combined:
            return ""
        if "env use" in combined:
            return ""
        if "install --only main" in combined:
            return ""
        if "chown -R root:root" in combined:
            return ""
        if "chmod -R a-w" in combined:
            return ""
        if "cat /opt/framenest/releases/" in combined and "framenest-release-sha" in combined:
            return RELEASE
        if "cat /opt/framenest/releases/" in combined and "manifest" in combined:
            return json.dumps(engine.make_manifest(
                release_sha=RELEASE, ap_pin=AP_PIN,
                superproject_sha256="e" * 64, ap_archive_sha256="f" * 64,
            ))
        if "mv /opt/framenest/releases/" in combined and ".staging" in combined:
            return ""
        if "framenest-db status" in combined:
            return '{"operation":"status","state":"at_head","current_revision":"0028","head_revision":"0028"}'
        if "framenest-backup status" in combined:
            return '{"operation":"status","restore_readiness":"ready"}'
        if "framenest-backup run-scheduled" in combined:
            return '{"operation":"run-scheduled","state":"succeeded","bundle_id":"b1"}'
        if "readlink -n /opt/framenest/current" in combined:
            return self.current
        if "previous-release" in combined and "printf" in combined:
            return ""
        if "check-database-ready" in combined:
            return '{"operation":"check-database-ready","state":"ready"}'
        if "ln -s" in combined and "current.next" in combined:
            parts = combined.split()
            idx = next(i for i, part in enumerate(parts) if part.endswith("current.next"))
            self.current = parts[idx - 1]
            return ""
        if "mv -T /opt/framenest/current.next" in combined:
            return ""
        if "restart framenest.service" in combined:
            return ""
        if "systemctl is-active" in combined:
            return "active"
        if "WorkingDirectory" in combined:
            return "/opt/framenest/current"
        if "check-health" in combined:
            return '{"operation":"check-health","state":"ready"}'
        if "journalctl -u framenest.service" in combined:
            return ""
        if "rm -f /run/framenest-release-deploy" in combined:
            return ""
        if "rmdir /run/framenest-release-deploy" in combined:
            return ""
        if "cat /run/framenest-release-deploy/previous-release" in combined:
            return PREV_PATH
        if "cat /run/framenest-release-deploy/rollback-previous-release" in combined:
            return PREV_PATH
        raise AssertionError(f"unexpected ssh command: {combined}")


def _args(command: str, extra: list[str] | None = None) -> list[str]:
    argv = [command]
    if command in ("check", "deploy", "rollback"):
        argv += ["--release", RELEASE]
    if command in ("deploy", "rollback"):
        argv += ["--yes"]
    argv += ["--target", "nuc", "--user", "op", "--identity", "identity"]
    if extra:
        argv += extra
    return argv


def _combined(runner: FakeRunner) -> str:
    return "\n".join(" ".join(argv) for argv, _ in runner.calls)


def _index(runner: FakeRunner, needle: str) -> int:
    for i, (argv, _) in enumerate(runner.calls):
        if argv and argv[0] == "ssh" and needle in " ".join(argv):
            return i
    raise AssertionError(f"missing ssh command containing {needle!r}")


def _ssh_combined(runner: FakeRunner) -> str:
    return "\n".join(" ".join(argv) for argv, _ in runner.calls if argv and argv[0] == "ssh")


# --- Command builder contracts ---

def test_remote_commands_never_invoke_uv_or_migrate() -> None:
    builders = [
        engine.cmd_remote_poetry_check_lock(TARGET),
        engine.cmd_remote_poetry_env_use(TARGET),
        engine.cmd_remote_poetry_install(TARGET),
        engine.cmd_remote_atomic_switch(TARGET),
        engine.cmd_remote_restart_service(),
        engine.cmd_remote_check_database_ready(TARGET),
        engine.cmd_remote_run_scheduled_backup(TARGET),
    ]
    for command in builders:
        assert "uv " not in command
        assert "migrate" not in command
        assert "uv:" not in command


def test_poetry_commands_use_exact_tooling_paths() -> None:
    assert engine.POETRY_BIN in engine.cmd_remote_poetry_check_lock(TARGET)
    assert engine.POETRY_BIN in engine.cmd_remote_poetry_env_use(TARGET)
    assert engine.CPYTHON_BIN in engine.cmd_remote_poetry_env_use(TARGET)
    assert engine.POETRY_BIN in engine.cmd_remote_poetry_install(TARGET)
    assert "--only main" in engine.cmd_remote_poetry_install(TARGET)
    assert "--no-interaction" in engine.cmd_remote_poetry_install(TARGET)
    assert "--no-ansi" in engine.cmd_remote_poetry_install(TARGET)


def test_atomic_switch_creates_new_symlink_then_renames() -> None:
    command = engine.cmd_remote_atomic_switch(TARGET)
    assert "ln -s" in command
    assert "/opt/framenest/current.next" in command
    assert "mv -T /opt/framenest/current.next" in command
    assert command.index("ln -s") < command.index("mv -T")


def test_service_account_commands_establish_release_cwd_and_env() -> None:
    for command in (
        engine.cmd_remote_db_status(TARGET),
        engine.cmd_remote_check_database_ready(TARGET),
    ):
        assert f"--chdir={TARGET}" in command
        assert f"env FRAMENEST_ENV_FILE={engine.ENV_FILE}" in command
        assert "-u framenest" in command


def test_cmd_remote_extract_emits_nested_private_argv_and_extracts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Transferred-engine extract must be nested ``_remote _remote-extract``.

    Top-level ``_remote-extract`` is invalid parser input and must stay so.
    """
    monkeypatch.setattr(engine, "REMOTE_DEPLOY_DIR", str(tmp_path))
    monkeypatch.setattr(engine, "RELEASE_ROOT", str(tmp_path))
    archive = tmp_path / "safe.tar"
    destination = tmp_path / "out"
    destination.mkdir()
    _write_tar(str(archive))
    remote_engine = str(tmp_path / "framenest_release.py")

    command = engine.cmd_remote_extract(str(archive), str(destination), remote_engine)
    argv = shlex.split(command)
    assert argv[:3] == ["sudo", "-n", "python3"]
    remaining = argv[4:]

    parsed = engine._build_parser().parse_args(remaining)
    assert parsed.command == "_remote"
    assert parsed.remote_command == "_remote-extract"
    assert parsed.archive == str(archive)
    assert parsed.destination == str(destination)

    result = engine.main(remaining)
    assert result == engine.EXIT_OK
    assert (destination / "pyproject.toml").read_bytes() == b"[tool.poetry]\n"
    assert (destination / "poetry.lock").read_bytes() == b"lock"

    with pytest.raises(SystemExit) as exc:
        engine._build_parser().parse_args(
            ["_remote-extract", "--archive", str(archive), "--destination", str(destination)]
        )
    assert exc.value.code == 2


def test_cmd_remote_relocate_venv_shebangs_emits_nested_private_argv(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Transferred-engine shebang relocation must be nested ``_remote _remote-relocate-venv-shebangs``.

    Top-level ``_remote-relocate-venv-shebangs`` is invalid parser input and must stay so.
    """
    monkeypatch.setattr(engine, "RELEASE_ROOT", str(tmp_path))
    sha = RELEASE
    staging = tmp_path / f"{sha}.staging"
    final = tmp_path / sha
    bindir = staging / ".venv" / "bin"
    bindir.mkdir(parents=True)
    (bindir / "framenest-db").write_text(
        f"#!{staging}/.venv/bin/python\nprint('db')\n", encoding="utf-8"
    )
    (bindir / "framenest-backup").write_text(
        f"#!{staging}/.venv/bin/python\nprint('backup')\n", encoding="utf-8"
    )
    remote_engine = str(tmp_path / "framenest_release.py")

    command = engine.cmd_remote_relocate_venv_shebangs(
        str(staging), str(final), remote_engine
    )
    argv = shlex.split(command)
    assert argv[:3] == ["sudo", "-n", "python3"]
    remaining = argv[4:]

    parsed = engine._build_parser().parse_args(remaining)
    assert parsed.command == "_remote"
    assert parsed.remote_command == "_remote-relocate-venv-shebangs"
    assert parsed.staging == str(staging)
    assert parsed.final == str(final)

    result = engine.main(remaining)
    assert result == engine.EXIT_OK
    assert (bindir / "framenest-db").read_text(encoding="utf-8").startswith(
        f"#!{final}/.venv/bin/python"
    )

    with pytest.raises(SystemExit) as exc:
        engine._build_parser().parse_args(
            [
                "_remote-relocate-venv-shebangs",
                "--staging",
                str(staging),
                "--final",
                str(final),
            ]
        )
    assert exc.value.code == 2


def _sudo_sh_c_script(command: str) -> str:
    parts = shlex.split(command)
    assert parts[:4] == ["sudo", "-n", "sh", "-c"], command
    assert len(parts) == 5, command
    return parts[4]


def test_cmd_remote_write_poetry_toml_uses_stdin_not_nested_quotes(
    tmp_path: Path,
) -> None:
    """Payload must travel as stdin; nested shlex quotes made in-project a command."""
    command = engine.cmd_remote_write_poetry_toml(str(tmp_path))
    assert "in-project" not in command
    assert engine.POETRY_TOML not in command
    script = _sudo_sh_c_script(command)
    dest = tmp_path / "poetry.toml"
    assert script == f"umask 077; cat > {shlex.quote(str(dest))}"
    subprocess.run(["sh", "-c", script], input=engine.POETRY_TOML.encode("utf-8"), check=True)
    assert dest.read_bytes() == engine.POETRY_TOML.encode("utf-8")


def test_cmd_remote_write_markers_uses_stdin_not_nested_quotes(tmp_path: Path) -> None:
    """Manifest JSON and SHA must not be nested inside single-quoted sh -c strings."""
    manifest_json = json.dumps(
        engine.make_manifest(
            release_sha=RELEASE,
            ap_pin=AP_PIN,
            superproject_sha256="e" * 64,
            ap_archive_sha256="f" * 64,
        ),
        sort_keys=True,
        separators=(",", ":"),
    )
    sha_payload = RELEASE + "\n"
    manifest_cmd, sha_cmd = engine.cmd_remote_write_markers(str(tmp_path))
    for command in (manifest_cmd, sha_cmd):
        assert manifest_json not in command
        assert RELEASE not in command
        assert "printf %s" not in command
    manifest_script = _sudo_sh_c_script(manifest_cmd)
    sha_script = _sudo_sh_c_script(sha_cmd)
    manifest_dest = tmp_path / ".framenest-release-manifest.json"
    sha_dest = tmp_path / ".framenest-release-sha"
    assert manifest_script == f"umask 077; cat > {shlex.quote(str(manifest_dest))}"
    assert sha_script == f"umask 077; cat > {shlex.quote(str(sha_dest))}"
    subprocess.run(
        ["sh", "-c", manifest_script], input=manifest_json.encode("utf-8"), check=True
    )
    subprocess.run(["sh", "-c", sha_script], input=sha_payload.encode("utf-8"), check=True)
    assert manifest_dest.read_bytes() == manifest_json.encode("utf-8")
    assert sha_dest.read_bytes() == sha_payload.encode("utf-8")


# --- status flow ---

def test_status_positive_path(capsys: pytest.CaptureFixture) -> None:
    runner = FakeRunner()
    result = engine.main(_args("status"), runner=runner)
    captured = capsys.readouterr()
    assert result == engine.EXIT_OK
    assert "service_active: active" in captured.out
    assert "database_revision: 0028" in captured.out
    assert "backup_restore_readiness: ready" in captured.out
    # Status never transfers a helper or mutates.
    assert not any("cat > /run/framenest-release-deploy" in " ".join(a) for a, _ in runner.calls)


class _PreManifest(FakeRunner):
    """Live pre-ADR-0060 tree: SHA marker present, manifest absent."""

    def _ssh_respond(self, combined: str, input_bytes: bytes | None) -> str:
        if (
            "echo manifest" in combined
            and "echo sha" in combined
            and "echo none" in combined
        ):
            return "sha"
        if "framenest-release-manifest.json" in combined and "cat" in combined:
            raise engine.ReleaseError("command failed", engine.EXIT_TRANSPORT)
        if "framenest-release-sha" in combined and "cat" in combined:
            return PREV
        return super()._ssh_respond(combined, input_bytes)


def test_status_pre_manifest_sha_only(capsys: pytest.CaptureFixture) -> None:
    runner = _PreManifest()
    result = engine.main(_args("status"), runner=runner)
    captured = capsys.readouterr()
    assert result == engine.EXIT_OK
    assert f"active_release: {PREV}" in captured.out
    assert "release_manifest: absent" in captured.out
    assert AP_PIN not in captured.out
    assert "e" * 64 not in captured.out
    assert "f" * 64 not in captured.out
    assert "superproject_archive_sha256" not in captured.out
    assert "ap_archive_sha256" not in captured.out
    assert "ap_gitlink" not in captured.out


def test_check_pre_manifest_uses_current_path_for_backup(
    capsys: pytest.CaptureFixture,
) -> None:
    runner = _PreManifest()
    result = engine.main(_args("check"), runner=runner)
    captured = capsys.readouterr()
    assert result == engine.EXIT_OK
    assert "backup_restore_readiness: ready" in captured.out
    assert f"current_release: {PREV_PATH}" in captured.out
    assert any(
        "framenest-backup status" in " ".join(argv) for argv, _ in runner.calls
    )


def test_status_missing_both_markers_fails_closed(capsys: pytest.CaptureFixture) -> None:
    class _NoMarkers(FakeRunner):
        def _ssh_respond(self, combined: str, input_bytes: bytes | None) -> str:
            if (
                "echo manifest" in combined
                and "echo sha" in combined
                and "echo none" in combined
            ):
                return "none"
            if "framenest-release-manifest.json" in combined and "cat" in combined:
                raise engine.ReleaseError("command failed", engine.EXIT_TRANSPORT)
            if "framenest-release-sha" in combined and "cat" in combined:
                raise engine.ReleaseError("command failed", engine.EXIT_TRANSPORT)
            return super()._ssh_respond(combined, input_bytes)

    result = engine.main(_args("status"), runner=_NoMarkers())
    captured = capsys.readouterr()
    assert result != engine.EXIT_OK
    assert "command failed" not in captured.err
    assert "absent" in captured.err
    assert "manifest" in captured.err
    assert "SHA" in captured.err or "sha" in captured.err


def test_status_invalid_sha_marker_fails_closed(capsys: pytest.CaptureFixture) -> None:
    class _InvalidSha(FakeRunner):
        def _ssh_respond(self, combined: str, input_bytes: bytes | None) -> str:
            if (
                "echo manifest" in combined
                and "echo sha" in combined
                and "echo none" in combined
            ):
                return "sha"
            if "framenest-release-manifest.json" in combined and "cat" in combined:
                raise engine.ReleaseError("command failed", engine.EXIT_TRANSPORT)
            if "framenest-release-sha" in combined and "cat" in combined:
                return "not-a-valid-release-sha"
            return super()._ssh_respond(combined, input_bytes)

    result = engine.main(_args("status"), runner=_InvalidSha())
    captured = capsys.readouterr()
    assert result != engine.EXIT_OK
    assert "command failed" not in captured.err
    assert "invalid" in captured.err


# --- check flow ---

def test_check_positive_path_passes_all_gates(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    runner = FakeRunner()
    result = engine.main(_args("check"), runner=runner)
    captured = capsys.readouterr()
    assert result == engine.EXIT_OK
    assert RELEASE in captured.out
    assert AP_PIN in captured.out


def test_check_requires_backup_ready(capsys: pytest.CaptureFixture) -> None:
    class _BackupNotReady(FakeRunner):
        def _ssh_respond(self, combined, input_bytes):
            if "framenest-backup status" in combined:
                return '{"operation":"status","restore_readiness":"stale"}'
            return super()._ssh_respond(combined, input_bytes)

    result = engine.main(_args("check"), runner=_BackupNotReady())
    assert result == engine.EXIT_BACKUP_NOT_READY


def test_check_requires_matching_tooling() -> None:
    class _BadTooling(FakeRunner):
        def _ssh_respond(self, combined, input_bytes):
            if "poetry --version" in combined:
                return "Poetry (version 1.8.0)"
            return super()._ssh_respond(combined, input_bytes)

    assert engine.main(_args("check"), runner=_BadTooling()) == engine.EXIT_TOOLING


# --- deploy flow ---

def test_deploy_happy_path_sequence(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    runner = FakeRunner()
    result = engine.main(_args("deploy"), runner=runner)
    combined = _combined(runner)
    assert result == engine.EXIT_OK
    assert "deploy complete" in capsys.readouterr().out

    # Lock and pre-existence gates precede any transfer.
    assert _index(runner, "mkdir -m 0700 /run/framenest-release-deploy") < _index(runner, "cat > /run/framenest-release-deploy/framenest_release.py")
    # Engine transfer precedes archive transfers.
    assert _index(runner, "framenest_release.py") < _index(runner, "superproject.tar")
    assert _index(runner, "superproject.tar") < _index(runner, "ap.tar")
    # Poetry install, then shebang rewrite, then chown/chmod, then rename.
    assert _index(runner, "install --only main") < _index(
        runner, "_remote-relocate-venv-shebangs"
    )
    assert _index(runner, "_remote-relocate-venv-shebangs") < _index(
        runner, "chmod -R a-w"
    )
    assert _index(runner, "_remote-relocate-venv-shebangs") < _index(
        runner, "chown -R root:root"
    )
    assert _index(runner, "chown -R root:root") < _index(runner, "mv /opt/framenest/releases/")
    assert _index(runner, "chmod -R a-w") < _index(runner, "mv /opt/framenest/releases/")
    assert _index(runner, "mv /opt/framenest/releases/") < _index(
        runner, "framenest-db status"
    )
    # Schema and checkpoint before atomic switch.
    assert _index(runner, "framenest-db status") < _index(runner, "ln -s")
    assert _index(runner, "framenest-backup run-scheduled") < _index(runner, "ln -s")
    # Single restart.
    assert _ssh_combined(runner).count("restart framenest.service") == 1
    # Cleanup present.
    assert _index(runner, "rmdir /run/framenest-release-deploy") > _index(runner, "restart framenest.service")


def test_deploy_transfers_engine_and_both_archives_as_stdin() -> None:
    runner = FakeRunner()
    assert engine.main(_args("deploy"), runner=runner) == engine.EXIT_OK
    payloads = [(argv, data) for argv, data in runner.calls if data is not None]
    transferred = [" ".join(argv) for argv, _ in payloads]
    assert any("framenest_release.py" in c for c in transferred)
    assert any("superproject.tar" in c for c in transferred)
    assert any("ap.tar" in c for c in transferred)
    poetry = next(data for argv, data in payloads if any("poetry.toml" in part for part in argv))
    manifest = next(
        data
        for argv, data in payloads
        if any(".framenest-release-manifest.json" in part for part in argv)
    )
    sha = next(
        data for argv, data in payloads if any(".framenest-release-sha" in part for part in argv)
    )
    assert poetry == engine.POETRY_TOML.encode("utf-8")
    assert json.loads(manifest.decode("utf-8"))["framenest_release_sha"] == RELEASE
    assert sha == (RELEASE + "\n").encode("utf-8")
    # Engine, two archives, poetry.toml, manifest JSON, and SHA marker.
    assert len(payloads) == 6


def test_deploy_verifies_archive_hashes_remotely() -> None:
    runner = FakeRunner()
    assert engine.main(_args("deploy"), runner=runner) == engine.EXIT_OK
    combined = _ssh_combined(runner)
    assert "sha256sum /run/framenest-release-deploy/framenest_release.py" in combined
    assert "sha256sum /run/framenest-release-deploy/superproject.tar" in combined
    assert "sha256sum /run/framenest-release-deploy/ap.tar" in combined


def test_deploy_verifies_committed_lock_unchanged() -> None:
    runner = FakeRunner()
    assert engine.main(_args("deploy"), runner=runner) == engine.EXIT_OK
    hashes = [c for c in _ssh_combined(runner).splitlines() if "poetry.lock" in c and "sha256sum" in c]
    assert len(hashes) == 2


def test_deploy_materializes_ap_under_release() -> None:
    runner = FakeRunner()
    assert engine.main(_args("deploy"), runner=runner) == engine.EXIT_OK
    combined = _ssh_combined(runner)
    assert ".staging/.ap" in combined or ".ap" in combined


def test_deploy_rejects_existing_target() -> None:
    class _Existing(FakeRunner):
        def _ssh_respond(self, combined, input_bytes):
            if "test ! -e /opt/framenest/releases/" in combined and ".staging" not in combined:
                raise engine.ReleaseError("exists", engine.EXIT_EXISTS)
            return super()._ssh_respond(combined, input_bytes)

    assert engine.main(_args("deploy"), runner=_Existing()) == engine.EXIT_EXISTS


def test_deploy_rejects_existing_remote_lock() -> None:
    class _Locked(FakeRunner):
        def _ssh_respond(self, combined, input_bytes):
            if "mkdir -m 0700 /run/framenest-release-deploy" in combined:
                raise engine.ReleaseError("locked", engine.EXIT_EXISTS)
            return super()._ssh_respond(combined, input_bytes)

    assert engine.main(_args("deploy"), runner=_Locked()) == engine.EXIT_EXISTS


def test_deploy_rejects_insufficient_capacity() -> None:
    class _NoSpace(FakeRunner):
        def _ssh_respond(self, combined, input_bytes):
            if "df -Pk /opt/framenest" in combined:
                return "Filesystem 1K-blocks Used Available Use% Mounted\n/dev/sda1 100 50 10 50% /opt/framenest"
            return super()._ssh_respond(combined, input_bytes)

    assert engine.main(_args("deploy"), runner=_NoSpace()) == engine.EXIT_CAPACITY


def test_deploy_schema_mismatch_stops_before_cutover() -> None:
    class _SchemaDiff(FakeRunner):
        def _ssh_respond(self, combined, input_bytes):
            if "framenest-db status" in combined:
                return '{"operation":"status","state":"behind","current_revision":"0027","head_revision":"0028"}'
            return super()._ssh_respond(combined, input_bytes)

    runner = _SchemaDiff()
    assert engine.main(_args("deploy"), runner=runner) == engine.EXIT_MIGRATION_REQUIRED
    assert "ln -s" not in _ssh_combined(runner)
    assert "restart framenest.service" not in _ssh_combined(runner)


def test_deploy_checkpoint_failure_stops_before_cutover() -> None:
    class _BadCheckpoint(FakeRunner):
        def _ssh_respond(self, combined, input_bytes):
            if "framenest-backup run-scheduled" in combined:
                return '{"operation":"run-scheduled","state":"failed"}'
            return super()._ssh_respond(combined, input_bytes)

    runner = _BadCheckpoint()
    assert engine.main(_args("deploy"), runner=runner) == engine.EXIT_CHECKPOINT
    assert "ln -s" not in _ssh_combined(runner)


def test_deploy_lock_changed_is_poetry_failure() -> None:
    class _LockChanged(FakeRunner):
        def __init__(self):
            super().__init__()
            self._count = 0

        def _ssh_respond(self, combined, input_bytes):
            if "sha256sum /opt/framenest/releases/" in combined and "poetry.lock" in combined:
                self._count += 1
                return f"{'deadbeef' if self._count == 1 else 'cafebabe'}  /x/poetry.lock"
            return super()._ssh_respond(combined, input_bytes)

    assert engine.main(_args("deploy"), runner=_LockChanged()) == engine.EXIT_POETRY


def test_deploy_post_switch_failure_rolls_back(capsys: pytest.CaptureFixture) -> None:
    class _PostSwitchFail(FakeRunner):
        def __init__(self) -> None:
            super().__init__()
            self._journal_failures = 0

        def _ssh_respond(self, combined, input_bytes):
            if "journalctl -u framenest.service" in combined:
                self._journal_failures += 1
                if self._journal_failures == 1:
                    raise engine.ReleaseError("terminal", engine.EXIT_SERVICE_TERMINAL)
            return super()._ssh_respond(combined, input_bytes)

    runner = _PostSwitchFail()
    result = engine.main(_args("deploy"), runner=runner)
    assert result == engine.EXIT_SERVICE_TERMINAL
    # Rollback restores the previous release symlink and restarts once more.
    assert _ssh_combined(runner).count("restart framenest.service") == 2
    assert _index(runner, "cat /run/framenest-release-deploy/previous-release") > 0


def test_deploy_rollback_failure_is_distinct(capsys: pytest.CaptureFixture) -> None:
    class _RollbackFail(FakeRunner):
        def __init__(self):
            super().__init__()
            self._restarts = 0

        def _ssh_respond(self, combined, input_bytes):
            if "journalctl -u framenest.service" in combined:
                raise engine.ReleaseError("terminal", engine.EXIT_SERVICE_TERMINAL)
            if "restart framenest.service" in combined:
                self._restarts += 1
                if self._restarts == 2:
                    raise engine.ReleaseError("rollback restart failed", engine.EXIT_ROLLBACK)
            return super()._ssh_respond(combined, input_bytes)

    assert engine.main(_args("deploy"), runner=_RollbackFail()) == engine.EXIT_ROLLBACK


def test_deploy_cleanup_failure_is_distinct(capsys: pytest.CaptureFixture) -> None:
    class _CleanupFail(FakeRunner):
        def _ssh_respond(self, combined, input_bytes):
            if "rmdir /run/framenest-release-deploy" in combined:
                raise engine.ReleaseError("cleanup failed", engine.EXIT_CLEANUP)
            return super()._ssh_respond(combined, input_bytes)

    assert engine.main(_args("deploy"), runner=_CleanupFail()) == engine.EXIT_CLEANUP


# --- rollback flow ---

def test_rollback_happy_path(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    class _RollbackRunner(FakeRunner):
        def _ssh_respond(self, combined, input_bytes):
            if "test -e /opt/framenest/releases/" in combined and ".framenest-release-sha" not in combined:
                return ""
            if ".framenest-release-sha" in combined and "test -e" in combined:
                return ""
            if "test -x /opt/framenest/releases/" in combined:
                return ""
            return super()._ssh_respond(combined, input_bytes)

    runner = _RollbackRunner()
    result = engine.main(_args("rollback"), runner=runner)
    assert result == engine.EXIT_OK
    assert "rollback complete" in capsys.readouterr().out
    assert _ssh_combined(runner).count("restart framenest.service") == 1


def test_rollback_requires_yes() -> None:
    runner = FakeRunner()
    argv = ["rollback", "--release", RELEASE, "--target", "nuc", "--user", "op", "--identity", "identity"]
    assert engine.main(argv, runner=runner) == engine.EXIT_USAGE


def test_rollback_missing_target_release_fails() -> None:
    class _Missing(FakeRunner):
        def _ssh_respond(self, combined, input_bytes):
            if "test -e /opt/framenest/releases/" in combined and ".framenest-release-sha" not in combined and "test -x" not in combined:
                raise engine.ReleaseError("missing", engine.EXIT_EXISTS)
            return super()._ssh_respond(combined, input_bytes)

    assert engine.main(_args("rollback"), runner=_Missing()) == engine.EXIT_EXISTS


# --- sanitized output ---

def test_output_never_contains_secrets_or_identity() -> None:
    runner = FakeRunner()
    engine.main(_args("deploy"), runner=runner)
    # The engine prints no transport identity, no secret-bearing patterns.
    for argv, _ in runner.calls:
        command = " ".join(argv)
        assert "password" not in command.lower()
        assert "BEGIN " not in command
        assert "NOPASSWD" not in command
        assert "sudo -S" not in command


def test_first_causal_error_is_preserved(capsys: pytest.CaptureFixture) -> None:
    class _SchemaDiff(FakeRunner):
        def _ssh_respond(self, combined, input_bytes):
            if "framenest-db status" in combined:
                return '{"operation":"status","state":"behind","current_revision":"0027","head_revision":"0028"}'
            return super()._ssh_respond(combined, input_bytes)

    result = engine.main(_args("deploy"), runner=_SchemaDiff())
    assert result == engine.EXIT_MIGRATION_REQUIRED
    assert "migration-required" in capsys.readouterr().err
