"""Production AI credential deployment helper support."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import os
from pathlib import Path
import shlex
import stat
import subprocess
import sys
from typing import Callable, Sequence

AI_CREDENTIAL_MAX_BYTES = 4096
SERVICE_NAME = "framenest.service"
REMOTE_CREDENTIAL_DIR = "/etc/framenest/credentials"
REMOTE_DROPIN_PATH = "/etc/systemd/system/framenest.service.d/20-ai-credential.conf"
REMOTE_AI_CONFIG_PATH = "/var/lib/framenest/ai/config.json"
REMOTE_AI_BIN = "/opt/framenest/current/.venv/bin/framenest-ai"
REMOTE_ROLLBACK_DIR = "/run/framenest-ai-credential-deploy"

PROVIDER_CREDENTIALS = {
    "nvidia-nim": "NVIDIA_API_KEY",
    "vercel-ai-gateway": "AI_GATEWAY_API_KEY",
}


class DeploymentInputError(Exception):
    """Sanitized operator input failure."""


class DeploymentCommandError(Exception):
    """Sanitized deployment command failure."""


@dataclass(frozen=True, slots=True)
class LocalSecret:
    identity: str
    value: str


Runner = Callable[[list[str]], None]


def main(
    argv: Sequence[str] | None = None,
    *,
    runner: Callable[[list[str], bytes | None], None] | None = None,
) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    command_runner = _subprocess_runner if runner is None else runner
    try:
        target = args.target or os.environ.get("FRAMENEST_PRODUCTION_SSH_TARGET", "")
        if not target:
            raise DeploymentInputError("SSH target is required.")
        secret = load_local_secret(
            provider_id=args.provider,
            credential_file=args.credential_file,
            local_ai_env=args.local_ai_env,
        )
        _validate_model(args.model)
        _print_plan(args=args, target=target, secret=secret)
        if args.check:
            return 0
        deploy(
            target=target,
            expected_hostname=args.expected_hostname,
            provider_id=args.provider,
            model_id=args.model,
            secret=secret,
            health_url=args.health_url,
            runner=command_runner,
        )
    except (DeploymentInputError, DeploymentCommandError) as exc:
        print(f"FrameNest production AI deployment failed: {exc}", file=sys.stderr)
        return 1
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="fn-production-env-deploy")
    parser.add_argument("--target", default=None, help="SSH target alias.")
    parser.add_argument("--expected-hostname", required=True, help="Expected remote hostname.")
    parser.add_argument("--provider", choices=tuple(PROVIDER_CREDENTIALS), required=True)
    parser.add_argument("--model", required=True)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--credential-file", type=Path, default=None)
    source.add_argument("--local-ai-env", type=Path, default=None)
    parser.add_argument("--health-url", default="http://127.0.0.1:8000/health")
    parser.add_argument("--check", action="store_true", help="Validate and print a sanitized plan.")
    return parser


def load_local_secret(
    *,
    provider_id: str,
    credential_file: Path | None,
    local_ai_env: Path | None,
) -> LocalSecret:
    identity = _credential_identity(provider_id)
    if credential_file is not None:
        payload = _read_private_file(credential_file)
        try:
            text = payload.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise DeploymentInputError("Credential source is invalid.") from exc
        return LocalSecret(identity=identity, value=_sanitize_secret(text))
    if local_ai_env is None:
        raise DeploymentInputError("Credential source is required.")
    _validate_private_file(local_ai_env)
    _run_fish_no_execute(local_ai_env)
    value = _extract_fish_secret(local_ai_env, identity)
    return LocalSecret(identity=identity, value=_sanitize_secret(value))


def deploy(
    *,
    target: str,
    expected_hostname: str,
    provider_id: str,
    model_id: str,
    secret: LocalSecret,
    health_url: str,
    runner: Callable[[list[str], bytes | None], None],
) -> None:
    try:
        _ssh(
            target,
            _remote_identity_check(expected_hostname),
            runner=runner,
            input_bytes=None,
        )
        _ssh(target, _remote_backup(secret.identity), runner=runner, input_bytes=None)
        _ssh(
            target,
            _remote_install_credential(secret.identity),
            runner=runner,
            input_bytes=secret.value.encode("utf-8"),
        )
        _ssh(
            target,
            _remote_install_dropin(_dropin_text(secret.identity)),
            runner=runner,
            input_bytes=None,
        )
        _ssh(
            target,
            _remote_configure_ai(provider_id=provider_id, model_id=model_id),
            runner=runner,
            input_bytes=None,
        )
        _ssh(target, _remote_restart(), runner=runner, input_bytes=None)
        _ssh(target, _remote_health(health_url), runner=runner, input_bytes=None)
        _ssh(target, _remote_cleanup(secret.identity), runner=runner, input_bytes=None)
    except DeploymentCommandError:
        try:
            _ssh(target, _remote_rollback(secret.identity), runner=runner, input_bytes=None)
        finally:
            _ssh(target, _remote_cleanup(secret.identity), runner=runner, input_bytes=None)
        raise


def _subprocess_runner(argv: list[str], input_bytes: bytes | None) -> None:
    result = subprocess.run(argv, input=input_bytes, check=False)
    if result.returncode != 0:
        raise DeploymentCommandError("remote command failed")


def _ssh(
    target: str,
    remote_command: str,
    *,
    runner: Callable[[list[str], bytes | None], None],
    input_bytes: bytes | None,
) -> None:
    runner(["ssh", "-o", "BatchMode=yes", "--", target, remote_command], input_bytes)


def _credential_identity(provider_id: str) -> str:
    try:
        return PROVIDER_CREDENTIALS[provider_id]
    except KeyError as exc:
        raise DeploymentInputError("Unsupported provider.") from exc


def _validate_model(model_id: str) -> None:
    allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._/-:")
    if not model_id or any(ch not in allowed for ch in model_id):
        raise DeploymentInputError("Model ID is invalid.")


def _validate_private_file(path: Path) -> None:
    try:
        metadata = path.lstat()
    except OSError as exc:
        raise DeploymentInputError("Credential source is unavailable.") from exc
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
        raise DeploymentInputError("Credential source is unsafe.")
    if metadata.st_uid != os.getuid():
        raise DeploymentInputError("Credential source is unsafe.")
    if stat.S_IMODE(metadata.st_mode) & 0o077:
        raise DeploymentInputError("Credential source is unsafe.")
    if metadata.st_size < 1 or metadata.st_size > AI_CREDENTIAL_MAX_BYTES:
        raise DeploymentInputError("Credential source is invalid.")


def _read_private_file(path: Path) -> bytes:
    _validate_private_file(path)
    payload = path.read_bytes()
    if len(payload) > AI_CREDENTIAL_MAX_BYTES:
        raise DeploymentInputError("Credential source is invalid.")
    return payload


def _sanitize_secret(value: str) -> str:
    if "\x00" in value:
        raise DeploymentInputError("Credential source is invalid.")
    if value.endswith("\r\n"):
        value = value[:-2]
    elif value.endswith("\n"):
        value = value[:-1]
    if "\n" in value or "\r" in value:
        raise DeploymentInputError("Credential source is invalid.")
    if not value.strip():
        raise DeploymentInputError("Credential source is invalid.")
    if len(value.encode("utf-8")) > AI_CREDENTIAL_MAX_BYTES:
        raise DeploymentInputError("Credential source is invalid.")
    return value.strip()


def _run_fish_no_execute(path: Path) -> None:
    result = subprocess.run(["fish", "--no-execute", str(path)], check=False, capture_output=True)
    if result.returncode != 0:
        raise DeploymentInputError("Credential source is invalid.")


def _extract_fish_secret(path: Path, identity: str) -> str:
    script = (
        "set -e NVIDIA_API_KEY; "
        "set -e AI_GATEWAY_API_KEY; "
        "source $argv[1] >/dev/null 2>/dev/null; "
        "switch $argv[2]; "
        "case NVIDIA_API_KEY; printf '%s' $NVIDIA_API_KEY; "
        "case AI_GATEWAY_API_KEY; printf '%s' $AI_GATEWAY_API_KEY; "
        "case '*'; exit 2; "
        "end"
    )
    result = subprocess.run(
        ["fish", "-c", script, str(path), identity],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise DeploymentInputError("Credential source is invalid.")
    return result.stdout


def _print_plan(*, args: argparse.Namespace, target: str, secret: LocalSecret) -> None:
    mode = "check" if args.check else "deploy"
    print(f"FrameNest production AI credential {mode}")
    print(f"Target: {target}")
    print(f"Expected hostname: {args.expected_hostname}")
    print(f"Provider: {args.provider}")
    print(f"Model: {args.model}")
    print(f"Credential identity: {secret.identity}")
    print(f"Credential destination: {REMOTE_CREDENTIAL_DIR}/{secret.identity}")
    print(f"Drop-in: {REMOTE_DROPIN_PATH}")
    print(f"Service: {SERVICE_NAME}")


def _remote_identity_check(expected_hostname: str) -> str:
    quoted_hostname = shlex.quote(expected_hostname)
    return "\n".join(
        [
            "set -e",
            f'test "$(hostname)" = {quoted_hostname}',
            "sudo -n test -n \"$(id -u framenest 2>/dev/null)\"",
            f"sudo -n systemctl show --property=FragmentPath --value {SERVICE_NAME} >/dev/null",
        ]
    )


def _remote_backup(identity: str) -> str:
    credential_path = f"{REMOTE_CREDENTIAL_DIR}/{identity}"
    return "\n".join(
        [
            "set -e",
            f"sudo -n rm -rf {REMOTE_ROLLBACK_DIR}",
            f"sudo -n install -d -o root -g root -m 0700 {REMOTE_ROLLBACK_DIR}",
            f"if sudo -n test -e {credential_path}; then sudo -n cp -a {credential_path} {REMOTE_ROLLBACK_DIR}/{identity}; sudo -n touch {REMOTE_ROLLBACK_DIR}/{identity}.present; fi",
            f"if sudo -n test -e {REMOTE_DROPIN_PATH}; then sudo -n cp -a {REMOTE_DROPIN_PATH} {REMOTE_ROLLBACK_DIR}/20-ai-credential.conf; sudo -n touch {REMOTE_ROLLBACK_DIR}/20-ai-credential.conf.present; fi",
        ]
    )


def _remote_install_credential(identity: str) -> str:
    credential_path = f"{REMOTE_CREDENTIAL_DIR}/{identity}"
    next_path = f"{credential_path}.next"
    return "\n".join(
        [
            "set -e",
            f"sudo -n install -d -o root -g root -m 0700 {REMOTE_CREDENTIAL_DIR}",
            f"sudo -n sh -c 'umask 077; cat > {next_path}; chown root:root {next_path}; chmod 0600 {next_path}; mv {next_path} {credential_path}'",
        ]
    )


def _dropin_text(identity: str) -> str:
    return f"[Service]\\nLoadCredential={identity}:{REMOTE_CREDENTIAL_DIR}/{identity}\\n"


def _remote_install_dropin(dropin: str) -> str:
    escaped = dropin.replace("'", "'\"'\"'")
    next_path = f"{REMOTE_DROPIN_PATH}.next"
    return "\n".join(
        [
            "set -e",
            "sudo -n install -d -o root -g root -m 0755 /etc/systemd/system/framenest.service.d",
            f"printf '%s' '{escaped}' | sudo -n sh -c 'umask 022; cat > {next_path}; chown root:root {next_path}; chmod 0644 {next_path}; mv {next_path} {REMOTE_DROPIN_PATH}'",
        ]
    )


def _remote_configure_ai(*, provider_id: str, model_id: str) -> str:
    quoted_provider = shlex.quote(provider_id)
    quoted_model = shlex.quote(model_id)
    return "\n".join(
        [
            "set -e",
            f"sudo -n -u framenest {REMOTE_AI_BIN} --config-path {REMOTE_AI_CONFIG_PATH} configure --provider-id {quoted_provider} --model-id {quoted_model} --yes",
        ]
    )


def _remote_restart() -> str:
    return "\n".join(["set -e", "sudo -n systemctl daemon-reload", f"sudo -n systemctl restart {SERVICE_NAME}"])


def _remote_health(health_url: str) -> str:
    return f"curl --fail --silent --show-error --max-time 5 {shlex.quote(health_url)} >/dev/null"


def _remote_rollback(identity: str) -> str:
    credential_path = f"{REMOTE_CREDENTIAL_DIR}/{identity}"
    return "\n".join(
        [
            "set -e",
            "# restore deployment-controlled files",
            f"if sudo -n test -e {REMOTE_ROLLBACK_DIR}/{identity}.present; then sudo -n cp -a {REMOTE_ROLLBACK_DIR}/{identity} {credential_path}; else sudo -n rm -f {credential_path}; fi",
            f"if sudo -n test -e {REMOTE_ROLLBACK_DIR}/20-ai-credential.conf.present; then sudo -n cp -a {REMOTE_ROLLBACK_DIR}/20-ai-credential.conf {REMOTE_DROPIN_PATH}; else sudo -n rm -f {REMOTE_DROPIN_PATH}; fi",
            "sudo -n systemctl daemon-reload",
        ]
    )


def _remote_cleanup(identity: str) -> str:
    return "\n".join(
        [
            f"sudo -n rm -f {REMOTE_CREDENTIAL_DIR}/{identity}.next {REMOTE_DROPIN_PATH}.next",
            f"sudo -n rm -rf {REMOTE_ROLLBACK_DIR}",
        ]
    )


if __name__ == "__main__":
    raise SystemExit(main())
