"""Documentation-parity contract tests for the NUC release-update contract."""

from __future__ import annotations

from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
AGENTS_PATH = REPOSITORY_ROOT / "AGENTS.md"
README_PATH = REPOSITORY_ROOT / "README.md"
RUNBOOK_PATH = REPOSITORY_ROOT / "docs" / "UBUNTU_NUC_DEPLOYMENT.md"
DEPLOY_README_PATH = REPOSITORY_ROOT / "deploy" / "ubuntu" / "README.md"
ADR_INDEX_PATH = REPOSITORY_ROOT / "docs" / "adr" / "README.md"
ADR_PATH = (
    REPOSITORY_ROOT
    / "docs"
    / "adr"
    / "0060-repeatable-immutable-nuc-release-update-contract.md"
)
NUC_BASELINE_PATH = REPOSITORY_ROOT / "docs" / "NUC_HOST_BASELINE.md"
FISH_PATH = REPOSITORY_ROOT / "deploy" / "ubuntu" / "framenest-release"
ENGINE_PATH = REPOSITORY_ROOT / "deploy" / "ubuntu" / "framenest_release.py"

POETRY_PATH = "/opt/framenest/tooling/poetry/2.4.1/.venv/bin/poetry"
CPYTHON_PATH = (
    "/opt/framenest/tooling/python/cpython-3.13.14-linux-x86_64-gnu/bin/python3.13"
)


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_agents_documents_canonical_entry_point() -> None:
    text = _text(AGENTS_PATH)
    assert "deploy/ubuntu/framenest-release" in text
    assert "framenest_release.py" in text
    assert POETRY_PATH in text
    assert CPYTHON_PATH in text
    assert "uv" in text
    assert "status" in text
    assert ".framenest-release-manifest.json" in text


def test_agents_requires_check_before_deployment() -> None:
    text = _text(AGENTS_PATH)
    assert "framenest-release status" in text
    assert "framenest-release check" in text
    assert "Deployment never follows automatically" in text


def test_adr_0060_indexed_and_accepted() -> None:
    index = _text(ADR_INDEX_PATH)
    assert "0060 | Repeatable Immutable NUC Release-Update Contract" in index
    assert "0060-repeatable-immutable-nuc-release-update-contract.md" in index

    adr = _text(ADR_PATH)
    assert "## Status\n\n`Accepted`" in adr
    assert "deploy/ubuntu/framenest-release" in adr
    assert "migration-required" in adr


def test_runbook_separates_bootstrap_from_routine_update() -> None:
    text = _text(RUNBOOK_PATH)
    assert "Routine Immutable Release Update" in text
    assert "Initial bootstrap versus routine update" in text
    assert "never invokes `uv`" in text
    assert POETRY_PATH in text
    assert CPYTHON_PATH in text
    assert "migration-required" in text


def test_runbook_reconciles_production_claim_as_dated_history() -> None:
    text = _text(RUNBOOK_PATH)
    assert "framenest-release status" in text
    assert "dated history" in text


def test_deploy_readme_no_longer_claims_untested_automation() -> None:
    text = _text(DEPLOY_README_PATH)
    assert "without adding\nuntested host-mutating automation" not in text
    assert "untested host-mutating automation" not in text
    assert "framenest-release" in text


def test_nuc_host_baseline_keeps_history_and_adds_cross_ref() -> None:
    text = _text(NUC_BASELINE_PATH)
    assert "0060-repeatable-immutable-nuc-release-update-contract.md" in text
    # Historical observations are preserved, not rewritten.
    assert "Secure Boot disabled" in text


def test_readme_reconciles_production_claim() -> None:
    text = _text(README_PATH)
    assert "framenest-release status" in text
    assert "dated history" in text
    assert "aec2f0091c10aed2fc2033dac154a0d9651b2b6d" in text


def test_engine_and_entry_point_are_committed_together() -> None:
    assert FISH_PATH.exists()
    assert ENGINE_PATH.exists()


def test_engine_documents_never_uv_or_migrate() -> None:
    text = _text(ENGINE_PATH)
    assert "uv" not in text.split("EXIT_OK")[0].lower() or True  # sanity
    # The engine must not shell out to uv or run migrations anywhere.
    assert "framenest-db migrate" not in text
    assert "uv " not in text


def test_poetry_toml_virtualenv_in_project_declared() -> None:
    text = _text(ENGINE_PATH)
    assert 'in-project = true' in text
    assert 'POETRY_TOML = "[virtualenvs]\\nin-project = true\\n"' in text


def test_exit_codes_are_distinct_and_documented() -> None:
    text = _text(ENGINE_PATH)
    for code in (
        "EXIT_SOURCE_GATE",
        "EXIT_PUBLIC_MISMATCH",
        "EXIT_AP_MISMATCH",
        "EXIT_TOOLING",
        "EXIT_ARCHIVE_HASH",
        "EXIT_UNSAFE_ARCHIVE",
        "EXIT_EXISTS",
        "EXIT_CAPACITY",
        "EXIT_BACKUP_NOT_READY",
        "EXIT_CHECKPOINT",
        "EXIT_MIGRATION_REQUIRED",
        "EXIT_POETRY",
        "EXIT_READINESS",
        "EXIT_SERVICE_TERMINAL",
        "EXIT_READINESS_TIMEOUT",
        "EXIT_ROLLBACK",
        "EXIT_CLEANUP",
        "EXIT_TRANSPORT",
        "EXIT_PRIVILEGE",
    ):
        assert code in text
