"""Repeatable immutable Ubuntu NUC release-update engine.

This module is the repository-owned routine NUC release-update contract. It is
executed locally by the operator through the thin Fish entry point
``deploy/ubuntu/framenest-release``, and, for the mutating deploy/rollback
paths, the same file is transferred to the NUC and run in a private remote mode
under Ubuntu system Python 3.12. It uses only the Python standard library.

It never stores, prints, or transmits secrets; never invokes ``uv``; never
runs migrations; and never accepts user-supplied remote shell commands.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys
import tarfile
import tempfile
from typing import Callable, Sequence

PROGRAM = "framenest-release"

# Accepted exact NUC tooling.
SERVICE = "framenest.service"
SERVICE_USER = "framenest"
SERVICE_GROUP = "framenest"
RELEASE_ROOT = "/opt/framenest/releases"
CURRENT = "/opt/framenest/current"
ENV_FILE = "/etc/framenest/framenest.env"
POETRY_BIN = "/opt/framenest/tooling/poetry/2.4.1/.venv/bin/poetry"
CPYTHON_BIN = (
    "/opt/framenest/tooling/python/cpython-3.13.14-linux-x86_64-gnu/bin/python3.13"
)
EXPECTED_POETRY_VERSION = "2.4.1"
EXPECTED_CPYTHON_VERSION = "3.13.14"
REMOTE_DEPLOY_DIR = "/run/framenest-release-deploy"

POETRY_TOML = "[virtualenvs]\nin-project = true\n"

# Minimum free capacity required under /opt/framenest beyond transferred bytes.
MIN_FREE_CAPACITY_BYTES = 1 << 30  # 1 GiB safety margin for the release-local .venv.

SHA_PATTERN = re.compile(r"^[0-9a-f]{40}$")

# Exit codes are part of the sanitized evidence model. Each outcome is distinct.
EXIT_OK = 0
EXIT_USAGE = 2
EXIT_SOURCE_GATE = 3
EXIT_PUBLIC_MISMATCH = 4
EXIT_AP_MISMATCH = 5
EXIT_TOOLING = 6
EXIT_ARCHIVE_HASH = 7
EXIT_UNSAFE_ARCHIVE = 8
EXIT_EXISTS = 9
EXIT_CAPACITY = 10
EXIT_BACKUP_NOT_READY = 11
EXIT_CHECKPOINT = 12
EXIT_MIGRATION_REQUIRED = 13
EXIT_POETRY = 14
EXIT_READINESS = 15
EXIT_SERVICE_TERMINAL = 16
EXIT_READINESS_TIMEOUT = 17
EXIT_ROLLBACK = 18
EXIT_CLEANUP = 19
EXIT_TRANSPORT = 20
EXIT_PRIVILEGE = 21


class ReleaseError(Exception):
    """Sanitized failure with a stable exit code."""

    def __init__(self, message: str, exit_code: int = EXIT_TRANSPORT) -> None:
        super().__init__(message)
        self.exit_code = exit_code


# A command runner executes ``argv`` with optional stdin bytes and returns the
# combined decoded output. It raises ReleaseError on non-zero exit. Tests inject
# a fake runner; production uses subprocess.
Runner = Callable[[Sequence[str], bytes | None], str]


def subprocess_runner(argv: Sequence[str], input_bytes: bytes | None) -> str:
    result = subprocess.run(
        list(argv), input=input_bytes, capture_output=True, text=False
    )
    if result.returncode != 0:
        raise ReleaseError("command failed")
    return result.stdout.decode("utf-8", "replace")


# ---------------------------------------------------------------------------
# Input validation (pure)
# ---------------------------------------------------------------------------

def validate_release_sha(sha: str) -> None:
    if not SHA_PATTERN.match(sha):
        raise ReleaseError(
            "release must be a full lowercase 40-hex commit SHA", EXIT_USAGE
        )


def validate_remote_path(value: str, *prefixes: str) -> None:
    if not value.startswith("/"):
        raise ReleaseError("unsafe remote path", EXIT_TRANSPORT)
    parts = [part for part in value.split("/") if part]
    if any(part in (".", "..") for part in parts):
        raise ReleaseError("unsafe remote path", EXIT_TRANSPORT)
    if not any(value == prefix or value.startswith(prefix + "/") for prefix in prefixes):
        raise ReleaseError("unsafe remote path", EXIT_TRANSPORT)


def release_dir(sha: str) -> str:
    return f"{RELEASE_ROOT}/{sha}"


def staging_dir(sha: str) -> str:
    return f"{RELEASE_ROOT}/{sha}.staging"


# ---------------------------------------------------------------------------
# Manifest and marker construction (pure)
# ---------------------------------------------------------------------------

def make_manifest(
    *,
    release_sha: str,
    ap_pin: str,
    superproject_sha256: str,
    ap_archive_sha256: str,
) -> dict[str, str]:
    return {
        "framenest_release_sha": release_sha,
        "ap_gitlink": ap_pin,
        "superproject_archive_sha256": superproject_sha256,
        "ap_archive_sha256": ap_archive_sha256,
    }


def sha256_of_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


# ---------------------------------------------------------------------------
# Archive member validation (pure; safe on Python 3.12)
# ---------------------------------------------------------------------------

def _parts_unsafe(rel: str) -> bool:
    return any(part == ".." for part in Path(rel).parts)


def validate_archive_member(name: str, *, linkname: str | None, isdev: bool) -> None:
    if not name or name.startswith("/") or "\x00" in name or "\\" in name:
        raise ReleaseError("unsafe archive member", EXIT_UNSAFE_ARCHIVE)
    if _parts_unsafe(name):
        raise ReleaseError("unsafe archive member", EXIT_UNSAFE_ARCHIVE)
    if isdev:
        raise ReleaseError("unsafe archive member", EXIT_UNSAFE_ARCHIVE)
    if linkname is not None:
        if (
            linkname.startswith("/")
            or "\x00" in linkname
            or "\\" in linkname
            or _parts_unsafe(linkname)
        ):
            raise ReleaseError("unsafe archive member", EXIT_UNSAFE_ARCHIVE)


def extract_validated_archive(archive_path: Path, destination: str) -> None:
    with tarfile.open(archive_path, "r:*") as archive:
        members = archive.getmembers()
        for member in members:
            validate_archive_member(
                member.name,
                linkname=member.linkname if (member.issym() or member.islnk()) else None,
                isdev=member.isdev(),
            )
        for member in members:
            archive.extract(member, path=destination, filter="data")  # validated above


# ---------------------------------------------------------------------------
# JSON parsing (sanitized)
# ---------------------------------------------------------------------------

def parse_json_status(output: str) -> dict[str, object]:
    try:
        payload = json.loads(output.strip())
    except json.JSONDecodeError as exc:
        raise ReleaseError("unexpected remote output", EXIT_TRANSPORT) from exc
    if not isinstance(payload, dict):
        raise ReleaseError("unexpected remote output", EXIT_TRANSPORT)
    return payload


# ---------------------------------------------------------------------------
# SSH transport
# ---------------------------------------------------------------------------

SSH_OPTIONS = [
    "-o", "BatchMode=yes",
    "-o", "RequestTTY=no",
    "-o", "StrictHostKeyChecking=yes",
    "-o", "IdentitiesOnly=yes",
    "-o", "ForwardAgent=no",
    "-o", "ClearAllForwardings=yes",
    "-o", "ConnectTimeout=10",
    "-o", "ServerAliveInterval=15",
    "-o", "ServerAliveCountMax=2",
]


def ssh(
    runner: Runner,
    *,
    target: str,
    user: str,
    identity: str,
    remote_command: str,
    input_bytes: bytes | None = None,
) -> str:
    argv = ["ssh", *SSH_OPTIONS, "-i", identity, f"{user}@{target}", remote_command]
    return runner(argv, input_bytes)


# ---------------------------------------------------------------------------
# Fixed remote command builders (single source of truth for remote work)
# ---------------------------------------------------------------------------

def cmd_remote_mkdir_deploy_dir() -> str:
    return f"sudo -n mkdir -m 0700 {REMOTE_DEPLOY_DIR}"


def cmd_remote_rm_deploy_dir() -> str:
    return f"sudo -n rmdir {REMOTE_DEPLOY_DIR}"


def cmd_remote_write_file(path: str, sha256: str) -> str:
    return (
        "set -e\n"
        f"sudo -n sh -c 'umask 077; cat > {shlex.quote(path)}'\n"
        f"test \"$(sudo -n sha256sum {shlex.quote(path)} | cut -d' ' -f1)\" = "
        f"{shlex.quote(sha256)}"
    )


def cmd_remote_readlink_current() -> str:
    return f"sudo -n readlink -n {CURRENT}"


def cmd_remote_read_release_sha(path: str) -> str:
    return f"sudo -n cat {shlex.quote(path)}/.framenest-release-sha"


def cmd_remote_read_manifest(path: str) -> str:
    return f"sudo -n cat {shlex.quote(path)}/.framenest-release-manifest.json"


def cmd_remote_probe_release_markers(path: str) -> str:
    """Classify current-tree markers without treating absence as transport failure.

    Returns a remote command whose stdout is exactly one of ``manifest``,
    ``sha``, or ``none`` when sudo succeeds. Absence is not ``test -e`` failure.
    """
    manifest = shlex.quote(f"{path}/.framenest-release-manifest.json")
    sha = shlex.quote(f"{path}/.framenest-release-sha")
    script = (
        f"if test -e {manifest}; then echo manifest; "
        f"elif test -e {sha}; then echo sha; "
        f"else echo none; fi"
    )
    return f"sudo -n sh -c {shlex.quote(script)}"


def cmd_remote_test_not_exists(path: str) -> str:
    return f"sudo -n test ! -e {shlex.quote(path)}"


def cmd_remote_test_exists(path: str) -> str:
    return f"sudo -n test -e {shlex.quote(path)}"


def cmd_remote_test_executable(path: str) -> str:
    return f"sudo -n test -x {shlex.quote(path)}"


def cmd_remote_service_is_active() -> str:
    return f"sudo -n systemctl is-active {SERVICE}"


def cmd_remote_systemd_working_directory() -> str:
    return f"sudo -n systemctl show -p WorkingDirectory --value {SERVICE}"


def cmd_remote_service_fragment_path() -> str:
    return f"sudo -n systemctl show -p FragmentPath --value {SERVICE}"


def cmd_remote_restart_service() -> str:
    return f"sudo -n systemctl restart {SERVICE}"


def cmd_remote_journal() -> str:
    return (
        f"sudo -n journalctl -u {SERVICE} -n 40 --no-pager "
        "--output=cat | grep -Ev '^$' || true"
    )


def cmd_remote_df_capacity() -> str:
    return "sudo -n df -Pk /opt/framenest | tail -n 1"


def cmd_remote_capture_current(target_path: str) -> str:
    quoted = shlex.quote(target_path)
    return (
        "set -e\n"
        f"prev=$(sudo -n readlink -n {CURRENT})\n"
        + 'test -n "$prev"\n'
        + "sudo -n sh -c 'printf %s \"$1\" > " + quoted + "' sh \"$prev\"\n"
    )


def service_account_prefix(release_path: str) -> str:
    return (
        f"sudo -n -u {SERVICE_USER} --chdir={shlex.quote(release_path)} "
        f"env FRAMENEST_ENV_FILE={ENV_FILE} "
        f"{shlex.quote(release_path)}/.venv/bin"
    )


def cmd_remote_db_status(release_path: str) -> str:
    return f"{service_account_prefix(release_path)}/framenest-db status"


def cmd_remote_backup_status(release_path: str) -> str:
    return f"{service_account_prefix(release_path)}/framenest-backup status"


def cmd_remote_check_database_ready(release_path: str) -> str:
    return (
        f"{service_account_prefix(release_path)}"
        "/framenest-production check-database-ready"
    )


def cmd_remote_check_health(release_path: str) -> str:
    return f"{service_account_prefix(release_path)}/framenest-production check-health"


def cmd_remote_run_scheduled_backup(release_path: str) -> str:
    return f"{service_account_prefix(release_path)}/framenest-backup run-scheduled"


def cmd_remote_prepare_dir(release_path: str) -> str:
    return f"sudo -n install -d -o root -g root -m 0755 {shlex.quote(release_path)}"


def cmd_remote_extract(archive_path: str, destination: str, engine_path: str) -> str:
    return (
        f"sudo -n python3 {shlex.quote(engine_path)} _remote _remote-extract "
        f"--archive {shlex.quote(archive_path)} "
        f"--destination {shlex.quote(destination)}"
    )


def cmd_remote_relocate_venv_shebangs(
    staging_path: str, final_path: str, engine_path: str
) -> str:
    return (
        f"sudo -n python3 {shlex.quote(engine_path)} _remote "
        f"_remote-relocate-venv-shebangs "
        f"--staging {shlex.quote(staging_path)} "
        f"--final {shlex.quote(final_path)}"
    )


def cmd_remote_cat_stdin(path: str) -> str:
    """Write runner stdin to ``path``; payload bytes must not enter the command string."""
    return f"sudo -n sh -c 'umask 077; cat > {shlex.quote(path)}'"


def cmd_remote_write_markers(release_path: str) -> tuple[str, str]:
    return (
        cmd_remote_cat_stdin(f"{release_path}/.framenest-release-manifest.json"),
        cmd_remote_cat_stdin(f"{release_path}/.framenest-release-sha"),
    )


def cmd_remote_write_poetry_toml(release_path: str) -> str:
    return cmd_remote_cat_stdin(f"{release_path}/poetry.toml")


def cmd_remote_poetry_check_lock(release_path: str) -> str:
    return (
        f"sudo -n {shlex.quote(POETRY_BIN)} check --lock "
        f"--directory {shlex.quote(release_path)}"
    )


def cmd_remote_poetry_env_use(release_path: str) -> str:
    return (
        f"sudo -n {shlex.quote(POETRY_BIN)} env use {shlex.quote(CPYTHON_BIN)} "
        f"--directory {shlex.quote(release_path)}"
    )


def cmd_remote_poetry_install(release_path: str) -> str:
    return (
        f"sudo -n {shlex.quote(POETRY_BIN)} install --only main "
        f"--no-interaction --no-ansi --directory {shlex.quote(release_path)}"
    )


def cmd_remote_poetry_version() -> str:
    return f"sudo -n {shlex.quote(POETRY_BIN)} --version"


def cmd_remote_cpython_version() -> str:
    return f"sudo -n {shlex.quote(CPYTHON_BIN)} --version"


def cmd_remote_sha256(path: str) -> str:
    return f"sudo -n sha256sum {shlex.quote(path)}"


def cmd_remote_chown_root(release_path: str) -> str:
    return (
        f"sudo -n chown -R root:root {shlex.quote(release_path)}"
    )


def cmd_remote_remove_release_writable_bits(release_path: str) -> str:
    return (
        f"sudo -n chmod -R a-w {shlex.quote(release_path)}"
    )


def cmd_remote_remove_file(path: str) -> str:
    return f"sudo -n rm -f {shlex.quote(path)}"


def cmd_remote_rename_staging(staging_path: str, release_path: str) -> str:
    return (
        f"sudo -n mv {shlex.quote(staging_path)} {shlex.quote(release_path)}"
    )


def cmd_remote_atomic_switch(release_path: str) -> str:
    return (
        "set -e\n"
        f"sudo -n ln -s {shlex.quote(release_path)} /opt/framenest/current.next\n"
        f"sudo -n mv -T /opt/framenest/current.next {CURRENT}"
    )


def cmd_remote_lock_hash(release_path: str) -> str:
    return f"sudo -n sha256sum {shlex.quote(release_path)}/poetry.lock"


# ---------------------------------------------------------------------------
# Local git source/public gates
# ---------------------------------------------------------------------------

def run_local_git(runner: Runner, argv: Sequence[str]) -> str:
    try:
        return runner(["git", *argv], None).strip()
    except ReleaseError as exc:
        raise ReleaseError("source gate failed", EXIT_SOURCE_GATE) from exc


def resolve_repo_root(runner: Runner) -> str:
    return run_local_git(runner, ["rev-parse", "--show-toplevel"])


def verify_local_head(runner: Runner, release_sha: str) -> None:
    head = run_local_git(runner, ["rev-parse", "HEAD"])
    if head != release_sha:
        raise ReleaseError("local HEAD does not match the requested release", EXIT_SOURCE_GATE)


def verify_clean_worktrees(runner: Runner) -> None:
    for argv in (
        ["status", "--porcelain", "--untracked-files=no"],
        ["-C", ".ap", "status", "--porcelain", "--untracked-files=no"],
    ):
        output = run_local_git(runner, argv)
        if output.strip():
            raise ReleaseError("worktree is not clean", EXIT_SOURCE_GATE)


def verify_public_main(runner: Runner, release_sha: str) -> None:
    output = run_local_git(runner, ["ls-remote", "origin", "refs/heads/main"])
    fields = output.split()
    if not fields or fields[0] != release_sha:
        raise ReleaseError("public main does not equal the requested release", EXIT_PUBLIC_MISMATCH)


def ap_gitlink_of(runner: Runner, release_sha: str) -> str:
    output = run_local_git(runner, ["ls-tree", release_sha, ".ap"])
    fields = output.split()
    if len(fields) < 3 or fields[1] != "commit":
        raise ReleaseError("unable to resolve the release .ap gitlink", EXIT_AP_MISMATCH)
    return fields[2]


def verify_ap_pin(runner: Runner, release_sha: str) -> str:
    gitlink = ap_gitlink_of(runner, release_sha)
    ap_head = run_local_git(runner, ["-C", ".ap", "rev-parse", "HEAD"])
    if ap_head != gitlink:
        raise ReleaseError("local .ap HEAD differs from the release gitlink", EXIT_AP_MISMATCH)
    return gitlink


def build_archives(
    runner: Runner,
    *,
    repo_root: str,
    release_sha: str,
    ap_gitlink: str,
    destination: Path,
) -> tuple[Path, Path]:
    superproject = destination / "superproject.tar"
    ap_archive = destination / "ap.tar"
    run_local_git(
        runner,
        ["archive", "--format=tar", "--output", str(superproject), release_sha],
    )
    run_local_git(
        runner,
        ["-C", ".ap", "archive", "--format=tar", "--output", str(ap_archive), ap_gitlink],
    )
    return superproject, ap_archive


# ---------------------------------------------------------------------------
# Remote phase execution (deploy / rollback)
# ---------------------------------------------------------------------------

def remote_exec(runner: Runner, command: str) -> str:
    try:
        return runner(["/bin/sh", "-c", command], None)
    except ReleaseError as exc:
        raise ReleaseError("remote command failed", EXIT_TRANSPORT) from exc


# ---------------------------------------------------------------------------
# Remote engine private subcommands
# ---------------------------------------------------------------------------

def remote_extract(runner: Runner, archive: str, destination: str) -> None:
    validate_remote_path(archive, REMOTE_DEPLOY_DIR, RELEASE_ROOT)
    validate_remote_path(destination, RELEASE_ROOT)
    try:
        extract_validated_archive(Path(archive), destination)
    except tarfile.TarError as exc:
        raise ReleaseError("archive extraction failed", EXIT_UNSAFE_ARCHIVE) from exc


def relocate_venv_shebangs(staging_path: str, final_path: str) -> None:
    """Rewrite staging-prefix shebangs under ``.venv/bin`` to the final release path."""
    validate_remote_path(staging_path, RELEASE_ROOT)
    validate_remote_path(final_path, RELEASE_ROOT)
    if staging_path != f"{final_path}.staging":
        raise ReleaseError("staging path does not match release", EXIT_TRANSPORT)

    venv_bin = Path(staging_path) / ".venv" / "bin"
    if not venv_bin.is_dir():
        raise ReleaseError("release venv is missing", EXIT_POETRY)

    rewritten = 0
    for path in sorted(venv_bin.iterdir()):
        if path.is_symlink() or not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if not text.startswith("#!"):
            continue
        if staging_path not in text:
            continue
        replacement = text.replace(staging_path, final_path)
        mode = path.stat().st_mode
        path.write_text(replacement, encoding="utf-8")
        path.chmod(mode)
        rewritten += 1

    if rewritten == 0:
        raise ReleaseError("venv shebangs were not relocated", EXIT_POETRY)

    for name in ("framenest-db", "framenest-backup"):
        script = venv_bin / name
        if not script.is_file() or script.is_symlink():
            raise ReleaseError("required console script is missing", EXIT_POETRY)
        content = script.read_text(encoding="utf-8")
        if ".staging" in content:
            raise ReleaseError("console script still names staging path", EXIT_POETRY)
        first = content.splitlines()[0] if content else ""
        expected = f"#!{final_path}/.venv/bin/python"
        if not first.startswith(expected):
            raise ReleaseError("console script does not name release interpreter", EXIT_POETRY)


def remote_relocate_venv_shebangs(
    runner: Runner, staging_path: str, final_path: str
) -> None:
    relocate_venv_shebangs(staging_path, final_path)


# ---------------------------------------------------------------------------
# Status and check read-only remote probes
# ---------------------------------------------------------------------------

def read_current_release(runner: Runner, transport: dict[str, str]) -> tuple[str, str, dict[str, object]]:
    raw = ssh(runner, **transport, remote_command=cmd_remote_readlink_current())
    current_path = raw.strip()
    if not current_path.startswith(RELEASE_ROOT):
        raise ReleaseError("current release path is unexpected", EXIT_TRANSPORT)
    probe = ssh(
        runner,
        **transport,
        remote_command=cmd_remote_probe_release_markers(current_path),
    ).strip()
    if probe == "manifest":
        manifest_raw = ssh(
            runner, **transport, remote_command=cmd_remote_read_manifest(current_path)
        )
        manifest = parse_json_status(manifest_raw)
        return current_path, manifest_raw, manifest
    if probe == "sha":
        sha_raw = ssh(
            runner, **transport, remote_command=cmd_remote_read_release_sha(current_path)
        ).strip()
        if not SHA_PATTERN.match(sha_raw):
            raise ReleaseError("current release SHA marker is invalid", EXIT_TRANSPORT)
        return current_path, "", {"framenest_release_sha": sha_raw}
    if probe == "none":
        raise ReleaseError(
            "current release SHA marker and manifest are absent", EXIT_TRANSPORT
        )
    raise ReleaseError("current release markers are unreadable", EXIT_TRANSPORT)


def read_backup_readiness(runner: Runner, transport: dict[str, str], release_path: str) -> str:
    raw = ssh(runner, **transport, remote_command=cmd_remote_backup_status(release_path))
    payload = parse_json_status(raw)
    readiness = payload.get("restore_readiness")
    if not isinstance(readiness, str):
        raise ReleaseError("backup readiness unavailable", EXIT_BACKUP_NOT_READY)
    return readiness


def read_db_current_revision(
    runner: Runner, transport: dict[str, str], release_path: str
) -> str:
    raw = ssh(runner, **transport, remote_command=cmd_remote_db_status(release_path))
    payload = parse_json_status(raw)
    current = payload.get("current_revision")
    if not isinstance(current, str):
        raise ReleaseError("database revision unavailable", EXIT_TRANSPORT)
    return current


def verify_tooling(runner: Runner, transport: dict[str, str]) -> None:
    for path in (POETRY_BIN, CPYTHON_BIN):
        ssh(runner, **transport, remote_command=cmd_remote_test_executable(path))
    poetry_version = ssh(runner, **transport, remote_command=cmd_remote_poetry_version()).strip()
    cpython_version = ssh(runner, **transport, remote_command=cmd_remote_cpython_version()).strip()
    if EXPECTED_POETRY_VERSION not in poetry_version:
        raise ReleaseError("Poetry tooling is mismatched", EXIT_TOOLING)
    if EXPECTED_CPYTHON_VERSION not in cpython_version:
        raise ReleaseError("CPython tooling is mismatched", EXIT_TOOLING)


def verify_capacity(
    runner: Runner, transport: dict[str, str], required_bytes: int
) -> None:
    raw = ssh(runner, **transport, remote_command=cmd_remote_df_capacity()).strip()
    fields = raw.split()
    if len(fields) < 4:
        raise ReleaseError("capacity check failed", EXIT_CAPACITY)
    try:
        available_kb = int(fields[3])
    except ValueError as exc:
        raise ReleaseError("capacity check failed", EXIT_CAPACITY) from exc
    if available_kb * 1024 < required_bytes + MIN_FREE_CAPACITY_BYTES:
        raise ReleaseError("insufficient capacity for the release", EXIT_CAPACITY)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog=PROGRAM)
    subcommands = parser.add_subparsers(dest="command", required=True)

    status = subcommands.add_parser("status", help="Read-only current release status.")
    _add_transport_args(status)

    check = subcommands.add_parser("check", help="Read-only pre-deployment gate.")
    check.add_argument("--release", required=True)
    _add_transport_args(check)

    deploy = subcommands.add_parser("deploy", help="Prepare and switch a routine release.")
    deploy.add_argument("--release", required=True)
    deploy.add_argument("--yes", action="store_true")
    _add_transport_args(deploy)

    rollback = subcommands.add_parser("rollback", help="Switch to an existing complete release.")
    rollback.add_argument("--release", required=True)
    rollback.add_argument("--yes", action="store_true")
    _add_transport_args(rollback)

    remote = subcommands.add_parser("_remote", help=argparse.SUPPRESS)
    remote_sub = remote.add_subparsers(dest="remote_command", required=True)
    remote_extract_p = remote_sub.add_parser("_remote-extract", help=argparse.SUPPRESS)
    remote_extract_p.add_argument("--archive", required=True)
    remote_extract_p.add_argument("--destination", required=True)
    remote_relocate_p = remote_sub.add_parser(
        "_remote-relocate-venv-shebangs", help=argparse.SUPPRESS
    )
    remote_relocate_p.add_argument("--staging", required=True)
    remote_relocate_p.add_argument("--final", required=True)

    return parser


def _add_transport_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--target", default=None)
    parser.add_argument("--user", default=None)
    parser.add_argument("--identity", default=None)


def _resolve_transport(args: argparse.Namespace) -> dict[str, str]:
    target = args.target or os.environ.get("FRAMENEST_NUC_SSH_TARGET", "")
    user = args.user or os.environ.get("FRAMENEST_NUC_SSH_USER", "")
    identity = args.identity or os.environ.get("FRAMENEST_NUC_SSH_IDENTITY", "")
    if not target:
        raise ReleaseError("SSH target is required", EXIT_USAGE)
    if not user:
        raise ReleaseError("SSH user is required", EXIT_USAGE)
    if not identity:
        raise ReleaseError("SSH identity is required", EXIT_USAGE)
    return {"target": target, "user": user, "identity": identity}


def main(
    argv: Sequence[str] | None = None,
    *,
    runner: Runner | None = None,
) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    command_runner = runner if runner is not None else subprocess_runner
    try:
        if args.command == "status":
            return _cmd_status(args, command_runner)
        if args.command == "check":
            return _cmd_check(args, command_runner)
        if args.command == "deploy":
            return _cmd_deploy(args, command_runner)
        if args.command == "rollback":
            return _cmd_rollback(args, command_runner)
        if args.command == "_remote":
            return _cmd_remote(args, command_runner)
        raise ReleaseError("invalid command", EXIT_USAGE)
    except ReleaseError as exc:
        print(f"{PROGRAM}: {exc}", file=sys.stderr)
        return exc.exit_code


def _cmd_remote(args: argparse.Namespace, runner: Runner) -> int:
    if args.remote_command == "_remote-extract":
        remote_extract(runner, args.archive, args.destination)
        return EXIT_OK
    if args.remote_command == "_remote-relocate-venv-shebangs":
        remote_relocate_venv_shebangs(runner, args.staging, args.final)
        return EXIT_OK
    raise ReleaseError("invalid remote command", EXIT_USAGE)


def _cmd_status(args: argparse.Namespace, runner: Runner) -> int:
    transport = _resolve_transport(args)
    current_path, manifest_raw, manifest = read_current_release(runner, transport)
    active = ssh(runner, **transport, remote_command=cmd_remote_service_is_active()).strip()
    db_revision = read_db_current_revision(runner, transport, current_path)
    backup = read_backup_readiness(runner, transport, current_path)
    print("framenest-release status")
    print(f"active_release: {manifest.get('framenest_release_sha', '')}")
    print(f"release_path: {current_path}")
    print(f"service_active: {active}")
    print(f"database_revision: {db_revision}")
    print(f"backup_restore_readiness: {backup}")
    if not manifest_raw:
        print("release_manifest: absent")
    return EXIT_OK


def _cmd_check(args: argparse.Namespace, runner: Runner) -> int:
    release_sha = args.release
    validate_release_sha(release_sha)
    transport = _resolve_transport(args)

    repo_root = resolve_repo_root(runner)
    verify_local_head(runner, release_sha)
    verify_clean_worktrees(runner)
    verify_public_main(runner, release_sha)
    ap_gitlink = verify_ap_pin(runner, release_sha)

    with tempfile.TemporaryDirectory(prefix="framenest-release-check-") as temp:
        temp_path = Path(temp)
        superproject, ap_archive = build_archives(
            runner,
            repo_root=repo_root,
            release_sha=release_sha,
            ap_gitlink=ap_gitlink,
            destination=temp_path,
        )
        super_hash = sha256_of_file(superproject)
        ap_hash = sha256_of_file(ap_archive)

    verify_tooling(runner, transport)
    current_path, _manifest_raw, _manifest = read_current_release(runner, transport)
    readiness = read_backup_readiness(runner, transport, current_path)
    if readiness != "ready":
        raise ReleaseError("catalog backup is not restore-ready", EXIT_BACKUP_NOT_READY)

    print("framenest-release check")
    print(f"release: {release_sha}")
    print(f"ap_gitlink: {ap_gitlink}")
    print(f"public_main: {release_sha}")
    print(f"superproject_sha256: {super_hash}")
    print(f"ap_archive_sha256: {ap_hash}")
    print(f"current_release: {current_path}")
    print(f"backup_restore_readiness: {readiness}")
    return EXIT_OK


def _cmd_deploy(args: argparse.Namespace, runner: Runner) -> int:
    release_sha = args.release
    validate_release_sha(release_sha)
    if not args.yes:
        raise ReleaseError("deploy requires --yes to confirm", EXIT_USAGE)
    transport = _resolve_transport(args)

    # Re-run all check gates first.
    _cmd_check(args, runner)

    repo_root = resolve_repo_root(runner)
    ap_gitlink = verify_ap_pin(runner, release_sha)

    with tempfile.TemporaryDirectory(prefix="framenest-release-deploy-") as temp:
        temp_path = Path(temp)
        superproject, ap_archive = build_archives(
            runner,
            repo_root=repo_root,
            release_sha=release_sha,
            ap_gitlink=ap_gitlink,
            destination=temp_path,
        )
        super_hash = sha256_of_file(superproject)
        ap_hash = sha256_of_file(ap_archive)
        super_size = superproject.stat().st_size
        ap_size = ap_archive.stat().st_size

        engine_bytes = Path(__file__).read_bytes()
        engine_hash = hashlib.sha256(engine_bytes).hexdigest()

        target = release_dir(release_sha)
        staging = staging_dir(release_sha)
        remote_super = f"{REMOTE_DEPLOY_DIR}/superproject.tar"
        remote_ap = f"{REMOTE_DEPLOY_DIR}/ap.tar"
        remote_engine = f"{REMOTE_DEPLOY_DIR}/framenest_release.py"
        remote_prev = f"{REMOTE_DEPLOY_DIR}/previous-release"

        # Remote lock and pre-existence gates.
        try:
            ssh(runner, **transport, remote_command=cmd_remote_mkdir_deploy_dir())
        except ReleaseError as exc:
            raise ReleaseError(
                "existing remote lock or recovery state", EXIT_EXISTS
            ) from exc
        ssh(runner, **transport, remote_command=cmd_remote_test_not_exists(target))
        ssh(runner, **transport, remote_command=cmd_remote_test_not_exists(staging))

        verify_tooling(runner, transport)
        verify_capacity(runner, transport, super_size + ap_size)

        # Transfer the engine, then the two archives; verify each SHA-256.
        ssh(
            runner,
            **transport,
            remote_command=cmd_remote_write_file(remote_engine, engine_hash),
            input_bytes=engine_bytes,
        )
        ssh(
            runner,
            **transport,
            remote_command=cmd_remote_write_file(remote_super, super_hash),
            input_bytes=superproject.read_bytes(),
        )
        ssh(
            runner,
            **transport,
            remote_command=cmd_remote_write_file(remote_ap, ap_hash),
            input_bytes=ap_archive.read_bytes(),
        )

        # Prepare the staging tree: extract, materialize AP, write markers/poetry.
        ssh(
            runner,
            **transport,
            remote_command=cmd_remote_prepare_dir(staging),
        )
        ssh(
            runner,
            **transport,
            remote_command=cmd_remote_extract(remote_super, staging, remote_engine),
        )
        ssh(
            runner,
            **transport,
            remote_command=(
                f"sudo -n install -d -o root -g root -m 0755 "
                f"{shlex.quote(staging)}/.ap"
            ),
        )
        ssh(
            runner,
            **transport,
            remote_command=cmd_remote_extract(remote_ap, f"{staging}/.ap", remote_engine),
        )
        ssh(
            runner,
            **transport,
            remote_command=cmd_remote_write_poetry_toml(staging),
            input_bytes=POETRY_TOML.encode("utf-8"),
        )

        # Poetry preparation against the committed lock; never update the lock.
        lock_before = ssh(
            runner, **transport, remote_command=cmd_remote_lock_hash(staging)
        ).strip()
        ssh(runner, **transport, remote_command=cmd_remote_poetry_check_lock(staging))
        ssh(runner, **transport, remote_command=cmd_remote_poetry_env_use(staging))
        ssh(runner, **transport, remote_command=cmd_remote_poetry_install(staging))
        lock_after = ssh(
            runner, **transport, remote_command=cmd_remote_lock_hash(staging)
        ).strip()
        if lock_before != lock_after:
            raise ReleaseError("poetry.lock changed during installation", EXIT_POETRY)

        ssh(
            runner,
            **transport,
            remote_command=cmd_remote_relocate_venv_shebangs(
                staging, target, remote_engine
            ),
        )
        ssh(runner, **transport, remote_command=cmd_remote_chown_root(staging))
        ssh(
            runner,
            **transport,
            remote_command=cmd_remote_remove_release_writable_bits(staging),
        )

        # Write markers and publish atomically.
        manifest_json = json.dumps(
            make_manifest(
                release_sha=release_sha,
                ap_pin=ap_gitlink,
                superproject_sha256=super_hash,
                ap_archive_sha256=ap_hash,
            ),
            sort_keys=True,
            separators=(",", ":"),
        )
        manifest_cmd, sha_cmd = cmd_remote_write_markers(staging)
        ssh(
            runner,
            **transport,
            remote_command=manifest_cmd,
            input_bytes=manifest_json.encode("utf-8"),
        )
        ssh(
            runner,
            **transport,
            remote_command=sha_cmd,
            input_bytes=(release_sha + "\n").encode("utf-8"),
        )
        ssh(
            runner,
            **transport,
            remote_command=cmd_remote_rename_staging(staging, target),
        )

        # Same-schema gate: packaged head must equal the current production revision.
        status_raw = ssh(
            runner, **transport, remote_command=cmd_remote_db_status(target)
        )
        db_payload = parse_json_status(status_raw)
        current_revision = db_payload.get("current_revision")
        head_revision = db_payload.get("head_revision")
        if current_revision != head_revision:
            raise ReleaseError("migration-required", EXIT_MIGRATION_REQUIRED)

        # Fresh verified checkpoint before cutover.
        checkpoint = ssh(
            runner, **transport, remote_command=cmd_remote_run_scheduled_backup(target)
        )
        checkpoint_payload = parse_json_status(checkpoint)
        if checkpoint_payload.get("state") != "succeeded":
            raise ReleaseError("checkpoint failed", EXIT_CHECKPOINT)

        # Capture the previous release for rollback.
        ssh(
            runner,
            **transport,
            remote_command=cmd_remote_capture_current(remote_prev),
        )

        try:
            # Pre-cutover readiness under the target release.
            ssh(
                runner,
                **transport,
                remote_command=cmd_remote_check_database_ready(target),
            )
            ssh(runner, **transport, remote_command=cmd_remote_atomic_switch(target))
            ssh(runner, **transport, remote_command=cmd_remote_restart_service())
            _verify_cutover(runner, transport, target)
        except ReleaseError as exc:
            _rollback(runner, transport, remote_prev)
            raise ReleaseError(
                f"deployment failed; rollback attempted ({exc})", exc.exit_code
            ) from exc

        # Cleanup exact owned temporary remote state.
        try:
            ssh(runner, **transport, remote_command=cmd_remote_remove_file(remote_super))
            ssh(runner, **transport, remote_command=cmd_remote_remove_file(remote_ap))
            ssh(runner, **transport, remote_command=cmd_remote_remove_file(remote_engine))
            ssh(runner, **transport, remote_command=cmd_remote_remove_file(remote_prev))
            ssh(runner, **transport, remote_command=cmd_remote_rm_deploy_dir())
        except ReleaseError as exc:
            raise ReleaseError("cleanup failed", EXIT_CLEANUP) from exc

    print(f"framenest-release deploy complete: {release_sha}")
    return EXIT_OK


def _verify_cutover(runner: Runner, transport: dict[str, str], target: str) -> None:
    current_path = ssh(
        runner, **transport, remote_command=cmd_remote_readlink_current()
    ).strip()
    if current_path != target:
        raise ReleaseError("cutover failed", EXIT_READINESS)
    active = ssh(
        runner, **transport, remote_command=cmd_remote_service_is_active()
    ).strip()
    if active != "active":
        raise ReleaseError("service terminal failure", EXIT_SERVICE_TERMINAL)
    working_dir = ssh(
        runner, **transport, remote_command=cmd_remote_systemd_working_directory()
    ).strip()
    if working_dir != CURRENT:
        raise ReleaseError("service working directory is unexpected", EXIT_READINESS)
    ssh(runner, **transport, remote_command=cmd_remote_check_database_ready(target))
    ssh(runner, **transport, remote_command=cmd_remote_check_health(target))
    logs = ssh(runner, **transport, remote_command=cmd_remote_journal())
    _assert_logs_sanitized(logs)


def _assert_logs_sanitized(logs: str) -> None:
    for token in ("/etc/framenest/credentials", "Authorization:", "Bearer ", "BEGIN "):
        if token in logs:
            raise ReleaseError("unsanitized log content", EXIT_SERVICE_TERMINAL)


def _rollback(runner: Runner, transport: dict[str, str], previous_path: str) -> None:
    try:
        prev = ssh(
            runner,
            **transport,
            remote_command=f"sudo -n cat {shlex.quote(previous_path)}",
        ).strip()
        validate_remote_path(prev, RELEASE_ROOT)
        ssh(runner, **transport, remote_command=cmd_remote_atomic_switch(prev))
        ssh(runner, **transport, remote_command=cmd_remote_check_database_ready(prev))
        ssh(runner, **transport, remote_command=cmd_remote_restart_service())
        _verify_cutover(runner, transport, prev)
    except ReleaseError as exc:
        raise ReleaseError("rollback failed", EXIT_ROLLBACK) from exc


def _cmd_rollback(args: argparse.Namespace, runner: Runner) -> int:
    release_sha = args.release
    validate_release_sha(release_sha)
    if not args.yes:
        raise ReleaseError("rollback requires --yes to confirm", EXIT_USAGE)
    transport = _resolve_transport(args)

    target = release_dir(release_sha)
    ssh(runner, **transport, remote_command=cmd_remote_test_exists(target))
    ssh(runner, **transport, remote_command=cmd_remote_test_exists(f"{target}/.framenest-release-sha"))
    ssh(runner, **transport, remote_command=cmd_remote_test_executable(f"{target}/.venv/bin/framenest-production"))

    remote_prev = f"{REMOTE_DEPLOY_DIR}/rollback-previous-release"
    ssh(runner, **transport, remote_command=cmd_remote_mkdir_deploy_dir())
    try:
        ssh(runner, **transport, remote_command=cmd_remote_capture_current(remote_prev))
        try:
            ssh(runner, **transport, remote_command=cmd_remote_check_database_ready(target))
            ssh(runner, **transport, remote_command=cmd_remote_atomic_switch(target))
            ssh(runner, **transport, remote_command=cmd_remote_restart_service())
            _verify_cutover(runner, transport, target)
        except ReleaseError as exc:
            _rollback(runner, transport, remote_prev)
            raise ReleaseError(
                f"rollback target failed; previous release restored ({exc})",
                exc.exit_code,
            ) from exc
    finally:
        ssh(runner, **transport, remote_command=cmd_remote_remove_file(remote_prev))
        ssh(runner, **transport, remote_command=cmd_remote_rm_deploy_dir())

    print(f"framenest-release rollback complete: {release_sha}")
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
