"""Unit tests for the Tailscale UDS ingress configuration boundary."""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from framenest.configuration import FrameNestSettings


def _tailscale_values(**overrides: object) -> dict[str, object]:
    values: dict[str, object] = {
        "ingress_mode": "tailscale_uds",
        "uds_path": "/run/framenest/framenest.sock",
        "external_origin": "https://nuc-1.tail247768.ts.net",
        "identity_map": {"aecrypto@gmail.com": "admin"},
    }
    values.update(overrides)
    return values


def test_default_ingress_mode_is_tcp_without_remote_fields() -> None:
    settings = FrameNestSettings(_env_file=None)
    assert settings.ingress_mode == "tcp"
    assert settings.uds_path is None
    assert settings.external_origin is None
    assert settings.identity_map == {}


def test_tailscale_uds_mode_accepts_exact_configuration() -> None:
    settings = FrameNestSettings(**_tailscale_values(), _env_file=None)
    assert settings.ingress_mode == "tailscale_uds"
    assert settings.uds_path == Path("/run/framenest/framenest.sock")
    assert settings.external_origin == "https://nuc-1.tail247768.ts.net"
    assert settings.identity_map == {"aecrypto@gmail.com": "admin"}


def test_tailscale_uds_mode_rejects_explicit_port_origin() -> None:
    with pytest.raises(ValidationError):
        FrameNestSettings(
            **_tailscale_values(external_origin="https://nuc-1.example.ts.net:8443"),
            _env_file=None,
        )


@pytest.mark.parametrize(
    "field, value",
    [
        ("uds_path", None),
        ("external_origin", None),
        ("identity_map", {}),
        ("identity_map", {"user@example.com": "user"}),
    ],
)
def test_tailscale_uds_mode_requires_socket_origin_and_admin(
    field: str, value: object
) -> None:
    with pytest.raises(ValidationError):
        FrameNestSettings(**_tailscale_values(**{field: value}), _env_file=None)


@pytest.mark.parametrize(
    "origin",
    [
        "http://nuc-1.tail247768.ts.net",
        "https://NUC-1.tail247768.ts.net",
        "https://nuc-1.tail247768.ts.net/",
        "https://nuc-1.tail247768.ts.net/path",
        "https://nuc-1.tail247768.ts.net?query=1",
        "https://nuc-1.tail247768.ts.net#fragment",
        "https://user@nuc-1.tail247768.ts.net",
        "https://localhost",
        "https://nuc-1.tail247768.ts.net:443",
        "https://nuc-1.tail247768.ts.net:0",
        "https://nuc-1.tail247768.ts.net:99999",
        "https://nuc-1.tail247768.ts.net:abc",
        "https://nuc-1.tail247768.ts.net:",
        "nuc-1.tail247768.ts.net",
        "",
    ],
)
def test_external_origin_must_be_an_exact_https_origin(origin: str) -> None:
    with pytest.raises(ValidationError):
        FrameNestSettings(
            **_tailscale_values(external_origin=origin), _env_file=None
        )


def test_uds_path_must_be_absolute() -> None:
    with pytest.raises(ValidationError):
        FrameNestSettings(
            **_tailscale_values(uds_path="relative/framenest.sock"), _env_file=None
        )


def test_identity_map_rejects_unknown_roles() -> None:
    with pytest.raises(ValidationError):
        FrameNestSettings(
            **_tailscale_values(identity_map={"aecrypto@gmail.com": "superuser"}),
            _env_file=None,
        )


def test_tcp_mode_tolerates_absent_remote_fields() -> None:
    settings = FrameNestSettings(ingress_mode="tcp", _env_file=None)
    assert settings.ingress_mode == "tcp"


def test_unknown_ingress_mode_is_rejected() -> None:
    with pytest.raises(ValidationError):
        FrameNestSettings(ingress_mode="lan", _env_file=None)


def test_tailscale_settings_load_from_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("FRAMENEST_INGRESS_MODE", "tailscale_uds")
    monkeypatch.setenv("FRAMENEST_UDS_PATH", "/run/framenest/framenest.sock")
    monkeypatch.setenv(
        "FRAMENEST_EXTERNAL_ORIGIN", "https://nuc-1.tail247768.ts.net"
    )
    monkeypatch.setenv(
        "FRAMENEST_IDENTITY_MAP", '{"aecrypto@gmail.com": "admin"}'
    )
    settings = FrameNestSettings(_env_file=None)
    assert settings.ingress_mode == "tailscale_uds"
    assert settings.uds_path == Path("/run/framenest/framenest.sock")
    assert settings.identity_map == {"aecrypto@gmail.com": "admin"}


def test_ingress_env_vars_do_not_leak_into_repr() -> None:
    settings = FrameNestSettings(**_tailscale_values(), _env_file=None)
    rendered = repr(settings)
    assert "aecrypto@gmail.com" not in rendered
    assert "framenest.sock" not in rendered
