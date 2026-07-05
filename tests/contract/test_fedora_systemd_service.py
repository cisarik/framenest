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


def _read_service() -> configparser.ConfigParser:
    parser = configparser.ConfigParser(interpolation=None, strict=False)
    parser.optionxform = str
    assert parser.read(SERVICE_PATH, encoding="utf-8") == [str(SERVICE_PATH)]
    return parser


def _env_template_values() -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in ENV_TEMPLATE_PATH.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        key, value = line.split("=", 1)
        values[key] = value
    return values


def test_systemd_service_declares_stable_service_boundaries() -> None:
    service = _read_service()["Service"]

    assert service["User"] == "framenest"
    assert service["Group"] == "framenest"
    assert service["WorkingDirectory"] == "/opt/framenest"
    assert service["StateDirectory"] == "framenest"
    assert service["CacheDirectory"] == "framenest"
    assert service["ConfigurationDirectory"] == "framenest"
    assert service["RuntimeDirectory"] == "framenest"
    assert service["UMask"] == "0077"


def test_systemd_service_uses_direct_server_and_readiness_gate() -> None:
    service = _read_service()["Service"]
    service_text = SERVICE_PATH.read_text(encoding="utf-8")

    assert (
        service["ExecStartPre"]
        == "/opt/framenest/.venv/bin/framenest-production check-database-ready"
    )
    assert service["ExecStart"] == "/opt/framenest/.venv/bin/framenest-server"
    assert "EnvironmentFile=/etc/framenest/framenest.env" in service_text
    assert "EnvironmentFile=-/etc/framenest/framenest-secrets.env" in service_text
    assert "./framenest" not in service_text


def test_systemd_service_hardening_keeps_no_public_exposure_shortcut() -> None:
    service = _read_service()["Service"]

    assert service["NoNewPrivileges"] == "true"
    assert service["PrivateTmp"] == "true"
    assert service["ProtectSystem"] == "strict"
    assert service["ProtectHome"] == "read-only"
    assert service["RestrictSUIDSGID"] == "true"
    assert service["LockPersonality"] == "true"


def test_non_secret_environment_template_is_loopback_first_and_path_explicit() -> None:
    values = _env_template_values()

    assert values == {
        "FRAMENEST_HOST": "127.0.0.1",
        "FRAMENEST_PORT": "8000",
        "FRAMENEST_DATABASE_PATH": "/var/lib/framenest/catalog.sqlite3",
        "FRAMENEST_GALLERY_PREVIEW_CACHE_PATH": "/var/cache/framenest/gallery-previews",
        "FRAMENEST_AI_CONFIG_PATH": "/etc/framenest/ai/config.json",
    }


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


def test_fedora_operator_documentation_records_no_host_activation_scope() -> None:
    text = FEDORA_DOC_PATH.read_text(encoding="utf-8")

    assert "not an installer" in text
    assert "does not\ninstall, enable, start, stop, reload, or inspect a real service" in text
    assert "/var/lib/framenest/catalog.sqlite3" in text
    assert "/var/cache/framenest/gallery-previews" in text
    assert "/etc/framenest/framenest.env" in text
    assert "/run/framenest" in text
    assert "./framenest` launcher remains macOS/local browser-development" in text


def test_adr_records_fedora_systemd_architecture_and_deferred_scope() -> None:
    text = ADR_PATH.read_text(encoding="utf-8")

    assert "Status\n\n`Accepted`" in text
    assert "read-only" in text
    assert "/opt/framenest/.venv/bin/framenest-production check-database-ready" in text
    assert "/etc/framenest/framenest-secrets.env" in text
    assert "Tailscale Serve" in text
    assert "automatic migrations during service\nstartup" in text
