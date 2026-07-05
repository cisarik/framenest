"""Contract tests for repository-native Fedora systemd artifacts."""

from __future__ import annotations

import configparser
import re
import tomllib
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
SERVICE_PATH = REPOSITORY_ROOT / "deploy" / "systemd" / "framenest.service"
ENV_TEMPLATE_PATH = REPOSITORY_ROOT / "deploy" / "systemd" / "framenest.env.example"
FEDORA_DOC_PATH = REPOSITORY_ROOT / "docs" / "FEDORA_SERVICE.md"
ADR_PATH = REPOSITORY_ROOT / "docs" / "adr" / "0031-fedora-systemd-service-foundation.md"

INSTALL_ROOT = "/opt/framenest/current"
PRODUCTION_BIN = f"{INSTALL_ROOT}/.venv/bin/framenest-production"
SUPERSEDED_INSTALL_BIN = "/opt/" + "framenest/.venv"
SUPERSEDED_AI_CONFIG = "/etc/" + "framenest/ai/config.json"
REMOVED_SECRET_ENVIRONMENT = "framenest-" + "secrets.env"
OPTIONAL_ENVIRONMENT_FILE_PREFIX = "EnvironmentFile" + "=-"


def _read_service() -> configparser.ConfigParser:
    parser = configparser.ConfigParser(interpolation=None, strict=False)
    parser.optionxform = str
    assert parser.read(SERVICE_PATH, encoding="utf-8") == [str(SERVICE_PATH)]
    return parser


def _service_text() -> str:
    return SERVICE_PATH.read_text(encoding="utf-8")


def _env_template_values() -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in ENV_TEMPLATE_PATH.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        key, value = line.split("=", 1)
        values[key] = value
    return values


def test_systemd_service_uses_current_release_working_directory() -> None:
    service = _read_service()["Service"]

    assert service["User"] == "framenest"
    assert service["Group"] == "framenest"
    assert service["WorkingDirectory"] == INSTALL_ROOT


def test_systemd_service_uses_production_executable_for_readiness_and_serve() -> None:
    service = _read_service()["Service"]

    assert service["ExecStartPre"] == f"{PRODUCTION_BIN} check-database-ready"
    assert service["ExecStart"] == f"{PRODUCTION_BIN} serve"
    assert service["ExecStartPre"].startswith(f"{INSTALL_ROOT}/.venv/bin/")
    assert service["ExecStart"].startswith(f"{INSTALL_ROOT}/.venv/bin/")


def test_systemd_service_avoids_development_wrappers_and_shells() -> None:
    text = _service_text()

    forbidden = [
        "./framenest",
        "framenest-server",
        "poetry",
        "uv ",
        "fish",
        "open ",
        "xdg-open",
        "/bin/sh",
        "/usr/bin/env",
    ]
    for marker in forbidden:
        assert marker not in text


def test_systemd_environment_file_contract_contains_no_secret_file() -> None:
    text = _service_text()

    assert "EnvironmentFile=/etc/framenest/framenest.env" in text
    assert OPTIONAL_ENVIRONMENT_FILE_PREFIX not in text
    assert REMOVED_SECRET_ENVIRONMENT not in text
    assert "NVIDIA_API_KEY" not in text
    assert "AI_GATEWAY_API_KEY" not in text


def test_systemd_service_directory_boundaries_are_mutable_state_cache_runtime_only() -> None:
    service = _read_service()["Service"]
    text = _service_text()

    assert service["StateDirectory"] == "framenest"
    assert service["CacheDirectory"] == "framenest"
    assert service["RuntimeDirectory"] == "framenest"
    assert "ConfigurationDirectory" not in service
    assert "LogsDirectory" not in service
    assert "ReadWritePaths" not in text
    assert "/media" not in text
    assert "/mnt" not in text
    assert "/home" not in text


def test_systemd_service_lifecycle_uses_bounded_sigterm_and_failure_restart() -> None:
    service = _read_service()["Service"]

    assert service["KillSignal"] == "SIGTERM"
    assert service["TimeoutStopSec"] == "30s"
    assert service["Restart"] == "on-failure"
    assert service["RestartSec"] == "5s"


def test_systemd_service_logs_to_journald_explicitly() -> None:
    service = _read_service()["Service"]

    assert service["StandardOutput"] == "journal"
    assert service["StandardError"] == "journal"


def test_systemd_service_removes_capabilities_and_retains_compatible_hardening() -> None:
    service = _read_service()["Service"]

    assert service["CapabilityBoundingSet"] == ""
    assert service["AmbientCapabilities"] == ""
    assert service["NoNewPrivileges"] == "true"
    assert service["PrivateTmp"] == "true"
    assert service["ProtectSystem"] == "strict"
    assert service["ProtectHome"] == "read-only"
    assert service["ProtectControlGroups"] == "true"
    assert service["ProtectKernelModules"] == "true"
    assert service["ProtectKernelTunables"] == "true"
    assert service["RestrictSUIDSGID"] == "true"
    assert service["LockPersonality"] == "true"
    assert service["UMask"] == "0077"


def test_non_secret_environment_template_is_loopback_first_and_path_explicit() -> None:
    values = _env_template_values()

    assert values == {
        "FRAMENEST_HOST": "127.0.0.1",
        "FRAMENEST_PORT": "8000",
        "FRAMENEST_DATABASE_PATH": "/var/lib/framenest/catalog.sqlite3",
        "FRAMENEST_GALLERY_PREVIEW_CACHE_PATH": "/var/cache/framenest/gallery-previews",
        "FRAMENEST_AI_CONFIG_PATH": "/var/lib/framenest/ai/config.json",
    }


def test_service_artifacts_do_not_encode_public_network_or_proxy_shortcuts() -> None:
    combined = _service_text() + "\n" + ENV_TEMPLATE_PATH.read_text(encoding="utf-8")

    forbidden = [
        "0.0.0.0",
        "tailscale",
        "funnel",
        "firewall",
        "firewalld",
        "reverse-proxy",
        "proxy_pass",
        "ReadWritePaths",
    ]
    for marker in forbidden:
        assert marker.lower() not in combined.lower()


def test_non_secret_environment_template_contains_no_secret_variables() -> None:
    text = ENV_TEMPLATE_PATH.read_text(encoding="utf-8")

    forbidden = {
        "NVIDIA_API_KEY",
        "AI_GATEWAY_API_KEY",
        "PASSWORD",
        "TOKEN",
        "AUTHORIZATION",
        "COOKIE",
        "PRIVATE_KEY",
        REMOVED_SECRET_ENVIRONMENT,
    }
    for marker in forbidden:
        assert marker not in text
    assert re.search(r"YOUR|REPLACE|<redacted>|secret-value", text, re.IGNORECASE) is None


def test_production_console_script_is_declared() -> None:
    pyproject = tomllib.loads((REPOSITORY_ROOT / "pyproject.toml").read_text(encoding="utf-8"))

    assert (
        pyproject["project"]["scripts"]["framenest-production"]
        == "framenest.infrastructure.runtime.production:main"
    )


def test_fedora_operator_documentation_records_correct_boundaries() -> None:
    text = FEDORA_DOC_PATH.read_text(encoding="utf-8")

    assert "not an installer" in text
    assert "does not\ninstall, enable, start, stop, reload, or inspect a real service" in text
    assert INSTALL_ROOT in text
    assert f"{PRODUCTION_BIN} serve" in text
    assert "/var/lib/framenest/catalog.sqlite3" in text
    assert "/var/cache/framenest/gallery-previews" in text
    assert "/var/lib/framenest/ai/config.json" in text
    assert "/etc/framenest/framenest.env" in text
    assert "/run/framenest" in text
    assert "./framenest` launcher remains macOS/local browser-development" in text
    assert REMOVED_SECRET_ENVIRONMENT not in text
    assert SUPERSEDED_AI_CONFIG not in text
    assert SUPERSEDED_INSTALL_BIN not in text


def test_adr_records_correct_fedora_systemd_architecture_and_deferred_scope() -> None:
    text = ADR_PATH.read_text(encoding="utf-8")

    assert "Status\n\n`Accepted`" in text
    assert INSTALL_ROOT in text
    assert f"{PRODUCTION_BIN} check-database-ready" in text
    assert f"{PRODUCTION_BIN} serve" in text
    assert "read-only" in text
    assert "env_file=None" in text
    assert "/var/lib/framenest/ai/config.json" in text
    assert REMOVED_SECRET_ENVIRONMENT not in text
    assert SUPERSEDED_AI_CONFIG not in text
    assert SUPERSEDED_INSTALL_BIN not in text
    assert "systemd credentials" in text
    assert "Tailscale Serve" in text
    assert "automatic migrations during service startup" in text
