"""Documentation contract for ADR-0073 successor wording."""

from __future__ import annotations

from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
ADR_INDEX_PATH = REPOSITORY_ROOT / "docs" / "adr" / "README.md"
ADR_0073_PATH = (
    REPOSITORY_ROOT
    / "docs"
    / "adr"
    / "0073-companion-merged-history-chrome-pending-visibility-x-seed-tag-and-preserving-apply.md"
)
ADR_0068_PATH = (
    REPOSITORY_ROOT
    / "docs"
    / "adr"
    / "0068-companion-review-save-and-readiness-triggered-publication.md"
)
ADR_0072_PATH = (
    REPOSITORY_ROOT
    / "docs"
    / "adr"
    / "0072-native-side-panel-unread-inbox-and-title-bar-history-chrome.md"
)
LIVING_PATHS = (
    REPOSITORY_ROOT / "README.md",
    REPOSITORY_ROOT / "SPEC.md",
    REPOSITORY_ROOT / "PRODUCT.md",
    REPOSITORY_ROOT / "ROADMAP.md",
    REPOSITORY_ROOT / "docs" / "X_COMPANION.md",
    ADR_INDEX_PATH,
)
FORBIDDEN_CURRENT_PHRASES = (
    "#review-inbox-list",
    "replace selected tags rather than union",
)


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_adr_0073_is_accepted_and_indexed() -> None:
    adr = _text(ADR_0073_PATH)
    index = _text(ADR_INDEX_PATH)
    assert "# ADR-0073: Companion Merged History Chrome, Pending Visibility, 𝕏 Seed Tag, and Preserving Apply" in adr
    assert "`Accepted`" in adr
    assert "`2026-08-24`" in adr
    assert "COMPANION_REVIEW_TAG_LIMIT_CONFLICT" in adr
    assert "surface=x-companion-save" in adr
    assert "companion_review_tag_sources" in adr
    assert "0073-companion-merged-history-chrome-pending-visibility-x-seed-tag-and-preserving-apply.md" in index
    assert "Companion Merged History Chrome, Pending Visibility, 𝕏 Seed Tag, and Preserving Apply" in index


def test_adr_0068_and_0072_remain_accepted_with_successor_notes() -> None:
    index = _text(ADR_INDEX_PATH)
    assert "Tags replace, they do not union." in _text(ADR_0068_PATH)
    assert "Unread and history may contain the same title." in _text(ADR_0072_PATH)
    assert (
        "Accepted; “Tags replace, they do not union.” succeeded by [ADR-0073]"
        in index
    )
    assert "separate unread/history lists" in index
    assert "succeeded by [ADR-0073]" in index


def test_living_docs_drop_two_list_and_replace_current_contract() -> None:
    for path in LIVING_PATHS:
        text = _text(path)
        for phrase in FORBIDDEN_CURRENT_PHRASES:
            assert phrase not in text, f"{path} still contains {phrase!r}"


def test_current_schema_head_is_0033() -> None:
    assert "schema head `0033`" in _text(REPOSITORY_ROOT / "README.md")
    assert "schema head `0033`" in _text(REPOSITORY_ROOT / "SPEC.md")
    assert "schema head `0033`" in _text(REPOSITORY_ROOT / "PRODUCT.md")
    roadmap = _text(REPOSITORY_ROOT / "ROADMAP.md")
    assert "revision `0033`" in roadmap
    assert "companion_review_tag_sources" in roadmap
    assert "ADR-0031" in roadmap
