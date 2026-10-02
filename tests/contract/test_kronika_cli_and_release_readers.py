"""Contract tests for ADR-0085 CLI fail-closed and release-marker readers.

The release helper and the AI credential helper are standard-library-only engines
that run without the application package on ``sys.path``. These tests prove their
local mirror of the resolver fails closed with exit status 2 and the two variable
names only, and that release markers and manifest keys are read under both
accepted spellings while their writers stay unchanged.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
RELEASE_HELPER = REPOSITORY_ROOT / "deploy" / "ubuntu" / "framenest_release.py"
AI_DEPLOY_HELPER = REPOSITORY_ROOT / "deploy" / "ubuntu" / "production_ai_deploy.py"

SUFFIX = "NUC_SSH_TARGET"
PRIMARY = "KRONIKA_"
COMPATIBLE = "FRAMENEST_"


def _load_helper(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def release_helper() -> Any:
    return _load_helper("_c1_release_helper", RELEASE_HELPER)


@pytest.fixture(scope="module")
def ai_deploy_helper() -> Any:
    return _load_helper("_c1_ai_deploy_helper", AI_DEPLOY_HELPER)


# ---------------------------------------------------------------------------
# Standard-library-only resolver mirrors
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("helper_name", ["release_helper", "ai_deploy_helper"])
def test_both_helpers_mirror_the_same_prefix_pair(
    helper_name: str,
    request: pytest.FixtureRequest,
) -> None:
    helper = request.getfixturevalue(helper_name)

    assert helper.IDENTITY_ENVIRONMENT_PREFIX == PRIMARY
    assert helper.COMPATIBLE_ENVIRONMENT_PREFIX == COMPATIBLE


def test_release_helper_resolves_either_prefix(release_helper: Any) -> None:
    assert release_helper.lookup_env(SUFFIX, environ={f"{PRIMARY}{SUFFIX}": "a"}) == "a"
    assert release_helper.lookup_env(SUFFIX, environ={f"{COMPATIBLE}{SUFFIX}": "b"}) == "b"
    assert release_helper.lookup_env(SUFFIX, environ={}) is None
    assert (
        release_helper.lookup_env(
            SUFFIX, environ={f"{PRIMARY}{SUFFIX}": "c", f"{COMPATIBLE}{SUFFIX}": "c"}
        )
        == "c"
    )
    assert release_helper.lookup_env(SUFFIX, environ={f"{PRIMARY}{SUFFIX}": ""}) is None


def test_release_helper_conflict_fails_closed_with_status_two(release_helper: Any) -> None:
    with pytest.raises(release_helper.ReleaseError) as excinfo:
        release_helper.lookup_env(
            SUFFIX, environ={f"{PRIMARY}{SUFFIX}": "alpha", f"{COMPATIBLE}{SUFFIX}": "beta"}
        )

    error = excinfo.value
    assert error.exit_code == 2
    rendered = str(error)
    assert f"{PRIMARY}{SUFFIX}" in rendered
    assert f"{COMPATIBLE}{SUFFIX}" in rendered
    assert "alpha" not in rendered
    assert "beta" not in rendered


def test_release_helper_transport_conflict_is_reported_not_raised_as_traceback(
    release_helper: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import argparse

    monkeypatch.setenv(f"{PRIMARY}{SUFFIX}", "alpha-host")
    monkeypatch.setenv(f"{COMPATIBLE}{SUFFIX}", "beta-host")
    args = argparse.Namespace(target=None, user=None, identity="/nonexistent")

    with pytest.raises(release_helper.ReleaseError) as excinfo:
        release_helper._resolve_transport(args)

    assert excinfo.value.exit_code == 2
    assert "alpha-host" not in str(excinfo.value)
    assert "beta-host" not in str(excinfo.value)


def test_ai_deploy_helper_conflict_exits_two(
    ai_deploy_helper: Any,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv(f"{PRIMARY}{ai_deploy_helper.SSH_TARGET_ENVIRONMENT_SUFFIX}", "alpha-host")
    monkeypatch.setenv(
        f"{COMPATIBLE}{ai_deploy_helper.SSH_TARGET_ENVIRONMENT_SUFFIX}", "beta-host"
    )
    argv = [
        "--expected-hostname",
        "nuc",
        "--provider",
        "nvidia-nim",
        "--model",
        "example-model",
        "--credential-file",
        "/nonexistent",
    ]

    exit_code = ai_deploy_helper.main(argv)
    captured = capsys.readouterr()

    assert exit_code == 2
    suffix = ai_deploy_helper.SSH_TARGET_ENVIRONMENT_SUFFIX
    assert f"{PRIMARY}{suffix}" in captured.err
    assert f"{COMPATIBLE}{suffix}" in captured.err
    assert "alpha-host" not in captured.err
    assert "beta-host" not in captured.err
    assert "alpha-host" not in captured.out
    assert "beta-host" not in captured.out


def test_ai_deploy_helper_accepts_either_prefix_alone(
    ai_deploy_helper: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    suffix = ai_deploy_helper.SSH_TARGET_ENVIRONMENT_SUFFIX
    monkeypatch.setenv(f"{PRIMARY}{suffix}", "alpha-host")

    assert ai_deploy_helper.lookup_env(suffix) == "alpha-host"

    monkeypatch.delenv(f"{PRIMARY}{suffix}")
    monkeypatch.setenv(f"{COMPATIBLE}{suffix}", "beta-host")

    assert ai_deploy_helper.lookup_env(suffix) == "beta-host"


# ---------------------------------------------------------------------------
# Release markers and manifest keys
# ---------------------------------------------------------------------------


def test_release_markers_and_manifest_keys_keep_their_writer_spelling(
    release_helper: Any,
) -> None:
    assert release_helper.RELEASE_SHA_MARKER == ".framenest-release-sha"
    assert release_helper.RELEASE_MANIFEST_MARKER == ".framenest-release-manifest.json"
    assert release_helper.RELEASE_SHA_MANIFEST_KEY == "framenest_release_sha"
    assert release_helper.make_manifest(
        release_sha="0" * 40,
        ap_pin="1" * 40,
        superproject_sha256="a" * 64,
        ap_archive_sha256="b" * 64,
        capture_code_tree="2" * 40,
        capture_runtime_contract_sha256="c" * 64,
        capture_unit_contract_sha256="d" * 64,
        capture_bridge_protocol=release_helper.CAPTURE_BRIDGE_PROTOCOL,
    )["framenest_release_sha"] == "0" * 40


def test_release_marker_probe_accepts_both_spellings(release_helper: Any) -> None:
    command = release_helper.cmd_remote_probe_release_markers("/opt/framenest/releases/abc")

    assert ".framenest-release-manifest.json" in command
    assert ".kronika-release-manifest.json" in command
    assert ".framenest-release-sha" in command
    assert ".kronika-release-sha" in command
    assert command.index(".framenest-release-manifest.json") < command.index(
        ".kronika-release-manifest.json"
    )
    assert command.index(".kronika-release-manifest.json") < command.index(
        ".framenest-release-sha"
    )


def test_release_marker_probe_prefers_manifest_over_sha(release_helper: Any) -> None:
    script = release_helper.cmd_remote_probe_release_markers("/opt/framenest/releases/abc")

    assert script.count("echo manifest") == 2
    assert script.count("echo sha") == 2
    assert script.rstrip().endswith("else echo none; fi'")


def test_release_read_commands_keep_the_writer_marker_names(release_helper: Any) -> None:
    assert ".framenest-release-sha" in release_helper.cmd_remote_read_release_sha("/opt/x")
    assert ".framenest-release-manifest.json" in release_helper.cmd_remote_read_manifest("/opt/x")


@pytest.mark.parametrize(
    "manifest",
    [
        {"framenest_release_sha": "a" * 40},
        {"kronika_release_sha": "a" * 40},
    ],
)
def test_manifest_release_sha_is_read_under_both_keys(
    release_helper: Any,
    manifest: dict,
) -> None:
    assert release_helper.manifest_release_sha(manifest) == "a" * 40


def test_manifest_release_sha_absent_key_returns_none(release_helper: Any) -> None:
    assert release_helper.manifest_release_sha({"other": 1}) is None
    assert release_helper.manifest_release_sha("not-a-mapping") is None


def test_release_helper_still_injects_the_old_env_file_name(release_helper: Any) -> None:
    prefix = release_helper.service_account_prefix("/opt/framenest/releases/abc")

    assert f"env {COMPATIBLE}ENV_FILE={release_helper.ENV_FILE}" in prefix
    assert f"{PRIMARY}ENV_FILE" not in prefix


def test_release_helper_env_file_path_constant_is_unchanged(release_helper: Any) -> None:
    assert release_helper.ENV_FILE == "/etc/framenest/framenest.env"
    assert release_helper.RELEASE_ROOT == "/opt/framenest/releases"
    assert release_helper.SERVICE == "framenest.service"


def test_protocol_magic_and_version_reads_are_unchanged() -> None:
    from importlib.metadata import version

    from framenest.infrastructure.persistence.catalog_backup_transfer import PROTOCOL_MAGIC

    assert PROTOCOL_MAGIC == b"FNCBE01\0"
    assert isinstance(version("framenest"), str)


def test_development_database_directory_is_unchanged() -> None:
    from framenest.configuration import DEVELOPMENT_DATABASE_DIRECTORY

    assert DEVELOPMENT_DATABASE_DIRECTORY == "framenest-development"


def test_emitted_cli_error_codes_stay_on_the_former_prefix() -> None:
    from framenest.adapters.cli.backup import COMMAND_FAILED_CODE, INVALID_INPUT_CODE
    from framenest.infrastructure.persistence.cli import (
        COMMAND_ERROR_CODE,
        CONFIGURATION_ERROR_CODE,
    )
    from framenest.infrastructure.runtime.production import (
        DATABASE_NOT_READY_CODE,
        HEALTH_CHECK_FAILED_CODE,
    )

    codes = (
        COMMAND_FAILED_CODE,
        INVALID_INPUT_CODE,
        COMMAND_ERROR_CODE,
        CONFIGURATION_ERROR_CODE,
        DATABASE_NOT_READY_CODE,
        HEALTH_CHECK_FAILED_CODE,
    )
    assert all(code.startswith("FRAMENEST_") for code in codes)
    assert not any("KRONIKA_" in code for code in codes)


def test_catalog_cli_error_codes_stay_on_the_former_prefix() -> None:
    from framenest.adapters.cli import catalog

    codes = [
        value
        for name, value in vars(catalog).items()
        if name.endswith("_CODE") and isinstance(value, str)
    ]
    assert codes
    assert all(code.startswith("FRAMENEST_") for code in codes)


def test_json_manifest_key_reader_is_used_for_the_current_release_fallback(
    release_helper: Any,
) -> None:
    payload = json.loads(json.dumps({"kronika_release_sha": "b" * 40}))

    assert release_helper.manifest_release_sha(payload) == "b" * 40
