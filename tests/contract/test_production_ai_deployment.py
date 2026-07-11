"""Contract tests for production AI credential deployment support."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import shutil
import stat
import subprocess
import sys
from typing import Any

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
FISH_ENTRYPOINT = REPOSITORY_ROOT / "deploy" / "ubuntu" / "fn-production-env-deploy"
HELPER_PATH = REPOSITORY_ROOT / "deploy" / "ubuntu" / "production_ai_deploy.py"
SYNTHETIC_SECRET = "synthetic-provider-credential"

_SPEC = importlib.util.spec_from_file_location("production_ai_deploy", HELPER_PATH)
assert _SPEC is not None
assert _SPEC.loader is not None
production_ai_deploy = importlib.util.module_from_spec(_SPEC)
sys.modules["production_ai_deploy"] = production_ai_deploy
_SPEC.loader.exec_module(production_ai_deploy)


class _Runner:
    def __init__(
        self,
        *,
        fail_on: str | None = None,
        fail_on_occurrence: int = 1,
        fail_plan: list[str] | None = None,
    ) -> None:
        self.calls: list[tuple[list[str], bytes | None]] = []
        self.fail_on = fail_on
        self.fail_on_occurrence = fail_on_occurrence
        self.fail_plan = [] if fail_plan is None else list(fail_plan)
        self._matches = 0

    def __call__(self, argv: list[str], input_bytes: bytes | None = None) -> None:
        self.calls.append((argv, input_bytes))
        combined = " ".join(argv)
        if self.fail_plan and self.fail_plan[0] in combined:
            self.fail_plan.pop(0)
            raise production_ai_deploy.DeploymentCommandError("simulated failure")
        if self.fail_on is not None and self.fail_on in combined:
            self._matches += 1
            if self._matches == self.fail_on_occurrence:
                raise production_ai_deploy.DeploymentCommandError("simulated failure")


def _credential_file(tmp_path: Path) -> Path:
    path = tmp_path / "credential.txt"
    path.write_text(SYNTHETIC_SECRET + "\n", encoding="utf-8")
    path.chmod(0o600)
    return path


def _base_args(tmp_path: Path) -> list[str]:
    return [
        "--target",
        "framenest-nuc",
        "--expected-hostname",
        "framenest-nuc",
        "--provider",
        "vercel-ai-gateway",
        "--model",
        "google/gemini-3.1-flash-lite",
        "--credential-file",
        str(_credential_file(tmp_path)),
    ]


def _combined(runner: _Runner) -> str:
    return "\n".join(" ".join(argv) for argv, _input in runner.calls)


def test_fish_entrypoint_has_valid_syntax() -> None:
    first_line = FISH_ENTRYPOINT.read_text(encoding="utf-8").splitlines()[0]

    assert first_line == "#!/usr/bin/env fish"
    subprocess.run(["fish", "--no-execute", str(FISH_ENTRYPOINT)], check=True)


def test_fish_entrypoint_avoids_shell_tracing_and_bash_secret_patterns() -> None:
    text = FISH_ENTRYPOINT.read_text(encoding="utf-8")

    assert "set -x" not in text
    assert "sudo -S" not in text
    assert "NOPASSWD" not in text
    assert "eval" not in text
    assert "[[" not in text


def test_check_mode_validates_inputs_and_does_not_mutate(tmp_path: Path, capsys: Any) -> None:
    runner = _Runner()

    result = production_ai_deploy.main([*_base_args(tmp_path), "--check"], runner=runner)

    output = capsys.readouterr().out
    assert result == 0
    assert runner.calls == []
    assert "Provider: vercel-ai-gateway" in output
    assert "Model: google/gemini-3.1-flash-lite" in output
    assert "Credential identity: AI_GATEWAY_API_KEY" in output
    assert SYNTHETIC_SECRET not in output


def test_exact_provider_to_credential_mapping(tmp_path: Path, capsys: Any) -> None:
    credential = _credential_file(tmp_path)

    assert (
        production_ai_deploy.main(
            [
                "--target",
                "framenest-nuc",
                "--expected-hostname",
                "framenest-nuc",
                "--provider",
                "nvidia-nim",
                "--model",
                "nvidia/default",
                "--credential-file",
                str(credential),
                "--check",
            ],
            runner=_Runner(),
        )
        == 0
    )

    assert "Credential identity: NVIDIA_API_KEY" in capsys.readouterr().out


def test_model_punctuation_is_quoted_and_shell_metacharacters_are_rejected(
    tmp_path: Path,
) -> None:
    runner = _Runner()

    assert (
        production_ai_deploy.main(
            [
                "--target",
                "framenest-nuc",
                "--expected-hostname",
                "framenest-nuc",
                "--provider",
                "vercel-ai-gateway",
                "--model",
                "vendor/model.name:1",
                "--credential-file",
                str(_credential_file(tmp_path)),
            ],
            runner=runner,
        )
        == 0
    )
    combined = "\n".join(" ".join(argv) for argv, _input in runner.calls)
    assert "--model-id vendor/model.name:1" in combined

    blocked = production_ai_deploy.main(
        [
            "--target",
            "framenest-nuc",
            "--expected-hostname",
            "framenest-nuc",
            "--provider",
            "vercel-ai-gateway",
            "--model",
            "vendor/model;touch",
            "--credential-file",
            str(_credential_file(tmp_path)),
        ],
        runner=_Runner(),
    )
    assert blocked == 1


def test_deploy_never_places_secret_in_ssh_argv_or_output(tmp_path: Path, capsys: Any) -> None:
    runner = _Runner()

    result = production_ai_deploy.main(_base_args(tmp_path), runner=runner)

    captured = capsys.readouterr()
    assert result == 0
    assert runner.calls
    for argv, _input in runner.calls:
        command_text = " ".join(argv)
        assert argv[:4] == ["ssh", "-o", "BatchMode=yes", "--"]
        assert SYNTHETIC_SECRET not in command_text
    assert any(input_bytes == SYNTHETIC_SECRET.encode("utf-8") for _, input_bytes in runner.calls)
    assert SYNTHETIC_SECRET not in captured.out + captured.err


def test_deploy_uses_sudo_n_only_and_no_remote_access_mutation_terms(tmp_path: Path) -> None:
    runner = _Runner()

    assert production_ai_deploy.main(_base_args(tmp_path), runner=runner) == 0

    combined = "\n".join(" ".join(argv) for argv, _input in runner.calls)
    assert "sudo -n" in combined
    assert "sudo -S" not in combined
    assert "NOPASSWD" not in combined
    for forbidden in ["ufw", "firewall", "tailscale", "0.0.0.0", "proxy_pass"]:
        assert forbidden not in combined.lower()


def test_deploy_sequences_atomic_installation_and_cleanup(tmp_path: Path) -> None:
    runner = _Runner()

    assert production_ai_deploy.main(_base_args(tmp_path), runner=runner) == 0

    combined = _combined(runner)
    assert "install -d -o root -g root -m 0700 /etc/framenest/credentials" in combined
    assert "mv /etc/framenest/credentials/AI_GATEWAY_API_KEY.next" in combined
    assert "mv /etc/systemd/system/framenest.service.d/20-ai-credential.conf.next" in combined
    assert "LoadCredential=AI_GATEWAY_API_KEY:/etc/framenest/credentials/AI_GATEWAY_API_KEY" in combined
    assert "rm -f /etc/framenest/credentials/AI_GATEWAY_API_KEY.next" in combined
    assert "rm -f /etc/framenest/credentials/AI_GATEWAY_API_KEY.next /etc/systemd/system/framenest.service.d/20-ai-credential.conf.next" in combined
    assert "rm -rf /run/framenest-ai-credential-deploy" in combined


def test_identity_failure_performs_no_rollback_command(tmp_path: Path) -> None:
    runner = _Runner(fail_on='test "$(hostname)"')

    result = production_ai_deploy.main(_base_args(tmp_path), runner=runner)

    combined = _combined(runner)
    assert result == 1
    assert "restore deployment-controlled files" not in combined
    assert "rm -rf /run/framenest-ai-credential-deploy" not in combined


def test_backup_failure_performs_no_production_state_rollback(tmp_path: Path) -> None:
    runner = _Runner(fail_on="transaction.complete")

    result = production_ai_deploy.main(_base_args(tmp_path), runner=runner)

    combined = _combined(runner)
    assert result == 1
    assert "restore deployment-controlled files" not in combined


def test_backup_records_credential_dropin_config_and_complete_marker() -> None:
    command = production_ai_deploy._remote_backup("AI_GATEWAY_API_KEY")

    assert "/run/framenest-ai-credential-deploy/AI_GATEWAY_API_KEY.present" in command
    assert "/run/framenest-ai-credential-deploy/AI_GATEWAY_API_KEY.absent" in command
    assert "/run/framenest-ai-credential-deploy/20-ai-credential.conf.present" in command
    assert "/run/framenest-ai-credential-deploy/20-ai-credential.conf.absent" in command
    assert "/run/framenest-ai-credential-deploy/config.json.present" in command
    assert "/run/framenest-ai-credential-deploy/config.json.absent" in command
    assert "/run/framenest-ai-credential-deploy/transaction.complete" in command
    assert "/var/lib/framenest/ai/config.json" in command


@pytest.mark.parametrize("failure", ["systemctl restart", "curl --fail"])
def test_deploy_rolls_back_on_restart_or_health_failure(
    tmp_path: Path,
    failure: str,
) -> None:
    runner = _Runner(fail_on=failure)

    result = production_ai_deploy.main(_base_args(tmp_path), runner=runner)

    combined = _combined(runner)
    assert result == 1
    assert "restore deployment-controlled files" in combined
    assert "/run/framenest-ai-credential-deploy/AI_GATEWAY_API_KEY.present" in combined
    assert "/run/framenest-ai-credential-deploy/AI_GATEWAY_API_KEY.absent" in combined
    assert "rm -f /etc/framenest/credentials/AI_GATEWAY_API_KEY" in combined
    assert "/run/framenest-ai-credential-deploy/20-ai-credential.conf.present" in combined
    assert "/run/framenest-ai-credential-deploy/20-ai-credential.conf.absent" in combined
    assert "rm -f /etc/systemd/system/framenest.service.d/20-ai-credential.conf" in combined
    assert "/run/framenest-ai-credential-deploy/config.json.present" in combined
    assert "/run/framenest-ai-credential-deploy/config.json.absent" in combined
    assert "rm -f /var/lib/framenest/ai/config.json" in combined
    assert "systemctl daemon-reload" in combined
    assert "systemctl restart framenest.service" in combined
    assert "curl --fail --silent --show-error --max-time 5 http://127.0.0.1:8000/health" in combined
    assert "rm -f /etc/framenest/credentials/AI_GATEWAY_API_KEY.next /etc/systemd/system/framenest.service.d/20-ai-credential.conf.next" in combined
    assert "rm -rf /run/framenest-ai-credential-deploy" in combined


def test_rollback_restore_failure_preserves_recovery_directory(tmp_path: Path, capsys: Any) -> None:
    runner = _Runner(
        fail_plan=[
            "systemctl restart framenest.service",
            "restore deployment-controlled files",
        ]
    )

    result = production_ai_deploy.main(_base_args(tmp_path), runner=runner)

    combined = _combined(runner)
    captured = capsys.readouterr()
    assert result == 1
    assert "rollback failed" in captured.err
    assert "restore" in captured.err
    assert "/run/framenest-ai-credential-deploy" in captured.err
    assert combined.count("rm -rf /run/framenest-ai-credential-deploy") == 1


def test_rollback_restart_failure_preserves_recovery_directory(tmp_path: Path, capsys: Any) -> None:
    runner = _Runner(
        fail_plan=[
            "systemctl restart framenest.service",
            "systemctl restart framenest.service",
        ]
    )

    result = production_ai_deploy.main(_base_args(tmp_path), runner=runner)

    combined = _combined(runner)
    captured = capsys.readouterr()
    assert result == 1
    assert "rollback failed" in captured.err
    assert "restart" in captured.err
    assert "/run/framenest-ai-credential-deploy" in captured.err
    assert combined.count("rm -rf /run/framenest-ai-credential-deploy") == 1


def test_rollback_health_failure_preserves_recovery_directory(tmp_path: Path, capsys: Any) -> None:
    runner = _Runner(fail_plan=["curl --fail", "curl --fail"])

    result = production_ai_deploy.main(_base_args(tmp_path), runner=runner)

    combined = _combined(runner)
    captured = capsys.readouterr()
    assert result == 1
    assert "rollback failed" in captured.err
    assert "health" in captured.err
    assert "/run/framenest-ai-credential-deploy" in captured.err
    assert combined.count("rm -rf /run/framenest-ai-credential-deploy") == 1


def test_successful_deployment_cleanup_failure_reports_sanitized_failure(
    tmp_path: Path,
    capsys: Any,
) -> None:
    runner = _Runner(fail_on="rm -rf /run/framenest-ai-credential-deploy", fail_on_occurrence=2)

    result = production_ai_deploy.main(_base_args(tmp_path), runner=runner)

    captured = capsys.readouterr()
    assert result == 1
    assert "cleanup failed" in captured.err
    assert "/run/framenest-ai-credential-deploy" in captured.err


def test_successful_rollback_cleans_recovery_directory(tmp_path: Path) -> None:
    runner = _Runner(fail_on="systemctl restart framenest.service")

    result = production_ai_deploy.main(_base_args(tmp_path), runner=runner)

    combined = _combined(runner)
    assert result == 1
    assert "rm -rf /run/framenest-ai-credential-deploy" in combined


def test_local_ai_env_source_validation_and_extraction(tmp_path: Path) -> None:
    env_path = tmp_path / "ai.env.fish"
    env_path.write_text(
        "\n".join(
            [
                "set -gx NVIDIA_API_KEY unrelated-sentinel",
                f"set -gx AI_GATEWAY_API_KEY {SYNTHETIC_SECRET}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    env_path.chmod(0o600)

    secret = production_ai_deploy.load_local_secret(
        provider_id="vercel-ai-gateway",
        credential_file=None,
        local_ai_env=env_path,
    )

    assert secret.value == SYNTHETIC_SECRET
    assert secret.identity == "AI_GATEWAY_API_KEY"


def test_local_ai_env_rejects_symlink_and_insecure_permissions(tmp_path: Path) -> None:
    target = tmp_path / "target.env.fish"
    target.write_text(f"set -gx AI_GATEWAY_API_KEY {SYNTHETIC_SECRET}\n", encoding="utf-8")
    target.chmod(0o600)
    link = tmp_path / "ai.env.fish"
    link.symlink_to(target)

    with pytest.raises(production_ai_deploy.DeploymentInputError):
        production_ai_deploy.load_local_secret(
            provider_id="vercel-ai-gateway",
            credential_file=None,
            local_ai_env=link,
        )

    insecure = tmp_path / "insecure.env.fish"
    insecure.write_text(f"set -gx AI_GATEWAY_API_KEY {SYNTHETIC_SECRET}\n", encoding="utf-8")
    insecure.chmod(0o644)
    if stat.S_IMODE(insecure.stat().st_mode) != 0o644:
        pytest.skip("platform did not preserve test file permissions")
    with pytest.raises(production_ai_deploy.DeploymentInputError):
        production_ai_deploy.load_local_secret(
            provider_id="vercel-ai-gateway",
            credential_file=None,
            local_ai_env=insecure,
        )


def test_no_provider_or_nuc_network_call_occurs_in_contract_tests(tmp_path: Path) -> None:
    runner = _Runner()

    assert production_ai_deploy.main(_base_args(tmp_path), runner=runner) == 0

    assert shutil.which("ssh") is not None or runner.calls
    combined = "\n".join(" ".join(argv) for argv, _input in runner.calls)
    assert "api.nvidia.com" not in combined
    assert "api.vercel.com" not in combined
