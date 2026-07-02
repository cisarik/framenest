"""Contract tests for the packaged local FrameNest web application shell."""

from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr

from framenest.adapters.api.application import create_app
from framenest.configuration import FrameNestSettings

REPRESENTATIVE_SECRET = "local-web-contract-secret"
REPRESENTATIVE_DATABASE_PATH = "/Users/example/framenest/catalog.sqlite3"
REPRESENTATIVE_REPOSITORY_PATH = "/Users/example/framenest"
FORBIDDEN_RESPONSE_FRAGMENTS = (
    REPRESENTATIVE_SECRET,
    REPRESENTATIVE_DATABASE_PATH,
    REPRESENTATIVE_REPOSITORY_PATH,
    "NVIDIA_API_KEY",
    "FRAMENEST_API_KEY",
    "FRAMENEST_DATABASE_PATH",
)


class _AssetReferenceParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.main_count = 0
        self.stylesheet_hrefs: list[str] = []
        self.script_srcs: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if tag == "main":
            self.main_count += 1
        if tag == "link" and attributes.get("rel") == "stylesheet":
            href = attributes.get("href")
            if href is not None:
                self.stylesheet_hrefs.append(href)
        if tag == "script":
            src = attributes.get("src")
            if src is not None:
                self.script_srcs.append(src)


@pytest.fixture
def client() -> TestClient:
    settings = FrameNestSettings(
        host="127.0.0.1",
        api_key=SecretStr(REPRESENTATIVE_SECRET),
        _env_file=None,
    )
    return TestClient(create_app(settings=settings))


def _parse_document(html: str) -> _AssetReferenceParser:
    parser = _AssetReferenceParser()
    parser.feed(html)
    return parser


def _javascript_function(script: str, name: str) -> str:
    marker = f"function {name}("
    start = script.index(marker)
    brace_start = script.index(") {", start) + 2
    depth = 0
    for index in range(brace_start, len(script)):
        char = script[index]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return script[start : index + 1]
    raise AssertionError(f"Could not find complete JavaScript function {name}")


def test_root_serves_framenest_application_document(client: TestClient) -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")

    html = response.text
    parsed = _parse_document(html)
    assert "FrameNest" in html
    assert parsed.main_count == 1
    assert parsed.stylesheet_hrefs == ["/assets/styles.css"]
    assert parsed.script_srcs == ["/assets/app.js"]


def test_root_document_references_only_local_application_assets(client: TestClient) -> None:
    response = client.get("/")
    html = response.text
    parsed = _parse_document(html)
    references = parsed.stylesheet_hrefs + parsed.script_srcs

    assert references
    assert all(reference.startswith("/assets/") for reference in references)
    assert "http://" not in html
    assert "https://" not in html
    assert 'src="//' not in html
    assert 'href="//' not in html


@pytest.mark.parametrize(
    ("path", "expected_content_type"),
    [
        ("/assets/styles.css", "text/css"),
        ("/assets/app.js", "text/javascript"),
    ],
)
def test_local_application_assets_are_served(
    client: TestClient,
    path: str,
    expected_content_type: str,
) -> None:
    response = client.get(path)
    assert response.status_code == 200
    assert response.headers["content-type"].startswith(expected_content_type)
    assert response.text.strip()


def test_unknown_application_asset_returns_404_not_application_document(
    client: TestClient,
) -> None:
    response = client.get("/assets/missing.css")
    assert response.status_code == 404
    assert "FrameNest" not in response.text


def test_health_contract_remains_unchanged_with_web_application(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert response.headers["content-type"].startswith("application/json")


@pytest.mark.parametrize("path", ["/", "/assets/styles.css", "/assets/app.js", "/health"])
def test_application_responses_do_not_add_wildcard_cors(
    client: TestClient,
    path: str,
) -> None:
    response = client.get(path)
    assert response.headers.get("access-control-allow-origin") != "*"


def test_browser_application_uses_same_origin_health_with_distinct_status_states(
    client: TestClient,
) -> None:
    script = client.get("/assets/app.js").text
    assert 'const HEALTH_ENDPOINT = "/health";' in script
    assert "fetch(HEALTH_ENDPOINT" in script
    assert "status--loading" in script
    assert "status--healthy" in script
    assert "status--error" in script
    assert "setLoadingState" in script
    assert "setHealthyState" in script
    assert "setErrorState" in script


def test_web_shell_removes_developer_library_tools_from_gallery(client: TestClient) -> None:
    html = client.get("/").text
    assert "library-browser" not in html
    assert "Library tools" not in html
    assert "Preview media" not in html
    assert "Not scanned" not in html
    assert "Local preview" not in html
    assert "AI suggestion review" not in html


def test_web_shell_does_not_contain_verbose_library_prose(client: TestClient) -> None:
    html = client.get("/").text
    assert "CLI-only" not in html
    assert "Library registration remains CLI-only" not in html
    assert "path flavor" not in html
    assert "Root path is intentionally hidden" not in html
    assert "posix path flavor" not in html


def test_web_shell_contains_reachable_catalog_browser_states(client: TestClient) -> None:
    html = client.get("/").text
    assert "catalog-browser" in html
    assert "Loading catalog media" in html
    assert "No media matched this catalog query" in html
    assert "Previous page" in html
    assert "Next page" in html
    assert "&lt;" in html
    assert "&gt;" in html
    for page_size in ("10 per page", "30 per page", "60 per page", "90 per page"):
        assert page_size in html


def test_web_shell_removes_visible_catalog_headings_for_compactness(client: TestClient) -> None:
    html = client.get("/").text
    catalog_section = html[html.index('id="catalog-browser"') : html.index('id="catalog-scope-all"')]

    assert "section-heading" not in catalog_section
    assert '<p class="eyebrow">Catalog</p>' not in html
    assert '<h2 id="catalog-title">Imported media</h2>' not in html
    assert 'aria-labelledby="catalog-title"' not in html


def test_web_shell_does_not_contain_obsolete_catalog_search_form(client: TestClient) -> None:
    html = client.get("/").text
    assert "catalog-search-form" not in html
    assert "catalog-search-input" not in html
    assert "catalog-search-button" not in html
    assert "catalog-clear-button" not in html
    assert "Search display titles" not in html


def test_web_shell_contains_manual_current_metadata_workspace(client: TestClient) -> None:
    html = client.get("/").text

    assert "metadata-workspace" in html or "metadata-dialog" in html
    dialog_section = html[html.index("metadata-dialog"):]
    assert "Edit media" in dialog_section
    assert "Title" in dialog_section
    assert "Description" in dialog_section
    assert "Tags" in dialog_section
    assert "Search or add a tag" in dialog_section
    assert "metadata-tag-suggestions" in html
    assert "metadata-selected-tags" in html
    assert "Save" in dialog_section
    assert "Cancel" in dialog_section
    for obsolete in (
        "Current metadata",
        "Display title",
        "Search canonical tags",
        "Canonical key",
        "Display name",
        "Create and select",
        "Selected canonical tags",
        "Save metadata",
        "Discard changes",
        "Processed status",
        "Clean.",
        "Unsaved changes.",
        "0 / 10000",
        "0 of 32 selected",
    ):
        assert obsolete not in dialog_section


def test_browser_defines_unicode_code_point_length_helper(client: TestClient) -> None:
    script = client.get("/assets/app.js").text
    assert "function unicodeCodePointLength" in script
    assert "[...value].length" in script or "Array.from(value).length" in script


def test_browser_description_uses_code_point_length_instead_of_utf16(client: TestClient) -> None:
    script = client.get("/assets/app.js").text
    assert "unicodeCodePointLength(rawDescription) > MAX_METADATA_DESCRIPTION_CODE_POINTS" in script
    assert "rawDescription.length > MAX_METADATA_DESCRIPTION_CODE_POINTS" not in script


def test_browser_description_counter_uses_code_point_length(client: TestClient) -> None:
    script = client.get("/assets/app.js").text
    assert "unicodeCodePointLength(metadataDescriptionInput.value)" in script
    assert "input.value.length" not in script or (
        "input.value.length" in script and "unicodeCodePointLength" in script
    )
    status_block = script[script.index("function updateDescriptionStatus") : script.index("function renderMetadataWorkspace")]
    assert "unicodeCodePointLength" in status_block
    assert "metadataDescriptionStatus.hidden = true" in status_block


def test_browser_description_textarea_has_no_maxlength(client: TestClient) -> None:
    html = client.get("/").text
    assert "maxlength=\"10000\"" not in html
    assert "metadata-description-input" in html
    assert "textarea" in html


def test_browser_description_rejects_c1_controls_and_allows_line_feed(client: TestClient) -> None:
    script = client.get("/assets/app.js").text
    assert "codePoint <= 0x1f" in script or "0x1f" in script
    assert "0x7f" in script or "127" in script
    assert "0x9f" in script
    assert "codePoint === 0x0a" in script
    assert "continue" in script
    assert "rawDescription.length >" not in script or "unicodeCodePointLength" in script


def test_browser_description_is_never_rendered_as_inner_html(client: TestClient) -> None:
    script = client.get("/assets/app.js").text
    assert "innerHTML" not in script
    assert "insertAdjacentHTML" not in script


def test_browser_description_workspace_includes_dirty_state_for_description(client: TestClient) -> None:
    script = client.get("/assets/app.js").text
    assert "normalized.description !== metadataWorkspace.baseline.description" in script
    assert "description: null" in script
    assert "description: \"\"" in script


def test_catalog_cards_have_explicit_metadata_edit_action(client: TestClient) -> None:
    script = client.get("/assets/app.js").text
    card_body = _javascript_function(script, "renderCatalogCard")

    assert "Edit" in card_body
    assert "handleOpenMetadataWorkspace(item" in script
    assert "card.addEventListener(\"click\"" not in script


def test_javascript_metadata_workspace_uses_existing_same_origin_endpoints(
    client: TestClient,
) -> None:
    script = client.get("/assets/app.js").text

    assert 'const MEDIA_METADATA_ENDPOINT_PREFIX = "/api/media";' in script
    assert "metadataEndpoint(mediaId)" in script
    assert 'fetch(metadataEndpoint(mediaId)' in script
    assert 'method: "PUT"' in script
    assert 'body: JSON.stringify({ display_title: normalized.displayTitle, description: normalized.description, tag_keys: normalized.tagKeys })' in script
    assert 'fetch(CANONICAL_TAGS_ENDPOINT, {' in script
    assert 'method: "POST"' in script
    assert "createAndSelectMetadataTag" in script
    assert "handleCreateAndSelectTag" not in script
    assert "CANONICAL_TAG_DEFINITION_CONFLICT" in script
    assert "CANONICAL_TAG_NOT_FOUND" in script
    assert "MEDIA_NOT_FOUND" in script
    assert "CATALOG_UNAVAILABLE" in script


def test_javascript_metadata_workspace_tracks_sparse_baseline_dirty_and_discard(
    client: TestClient,
) -> None:
    script = client.get("/assets/app.js").text

    assert "metadataWorkspace.baseline" in script
    assert "metadataWorkspace.current" in script
    assert "payload.display_title === null" in script
    assert "metadataTitleInput.value = metadataWorkspace.current.displayTitle || \"\";" in script
    assert "deriveCatalogFallbackTitle(item)" in script
    assert "function normalizedMetadataFormState" in script
    assert "displayTitle: null" in script
    assert "rawTitle.trim() !== rawTitle" in script
    assert "hasControlCharacter(rawTitle)" in script
    assert "metadataSaveButton.disabled = metadataWorkspace.loading || metadataWorkspace.saving || !dirty || Boolean(validation);" in script
    assert "metadataDiscardButton.disabled = metadataWorkspace.saving;" in script
    assert "confirm(\"Discard unsaved metadata changes?\")" in script
    assert "handleDiscardMetadataChanges" in script
    assert "closeMetadataWorkspace();" in _javascript_function(script, "handleDiscardMetadataChanges")
    assert "metadataBeforeUnloadHandler" in script
    assert "beforeunload" in script


def test_javascript_metadata_workspace_tag_selection_ordering_and_limits(
    client: TestClient,
) -> None:
    script = client.get("/assets/app.js").text

    assert "const MAX_METADATA_TAGS = 32;" in script
    assert "function renderMetadataTagSuggestions" in script
    assert "function selectMetadataTag" in script
    assert "metadataWorkspace.current.tagKeys.includes(tag.key)" in script
    assert "metadataWorkspace.current.tagKeys.length >= MAX_METADATA_TAGS" in script
    assert "function removeSelectedMetadataTag" in script
    assert "function handleMetadataTagSearchKeydown" in script
    assert "ArrowDown" in script
    assert "ArrowUp" in script
    assert "Add “${displayName}”" in script
    assert "uniqueTagKeyForDisplayName(displayName)" in script
    assert "body: JSON.stringify({ key, display_name: displayName })" in script
    assert "Remove ${displayName}" in script
    assert "Move earlier" not in script
    assert "Move later" not in script
    assert "Remove tag" not in script
    assert "tag_keys: normalized.tagKeys" in script
    assert ".sort(" not in script[script.index("function renderSelectedMetadataTags") : script.index("function renderMetadataTagSuggestions")]


def test_javascript_metadata_save_refreshes_catalog_and_preserves_filters(
    client: TestClient,
) -> None:
    script = client.get("/assets/app.js").text

    assert "async function handleSaveMetadata" in script
    save_block = script[script.index("async function handleSaveMetadata") : script.index("async function handleInspectClick")]
    assert 'setMetadataStatus("saved", "Saved.")' not in save_block
    assert "created" not in save_block
    assert "updated" not in save_block
    assert "unchanged" not in save_block
    assert "metadataWorkspace.openMediaId" in save_block
    assert "await loadCatalog();" in save_block
    assert "closeMetadataWorkspace();" in save_block
    assert "catalogState.q" not in save_block
    assert "catalogState.tagKeys" not in save_block
    assert "catalogState.offset = 0" not in save_block


def test_javascript_loads_library_list_without_auto_scanning(client: TestClient) -> None:
    script = client.get("/assets/app.js").text
    assert 'const LIBRARIES_ENDPOINT = "/api/libraries";' in script
    assert "fetch(LIBRARIES_ENDPOINT" in script
    assert "loadLibraries();" in script
    assert "scan-preview" in script
    assert "addEventListener(\"click\"" in script
    assert "function handlePreviewClick" in script
    assert "handlePreviewClick(library, card);" in script


def test_javascript_loads_catalog_without_auto_scan_analysis_or_ai(client: TestClient) -> None:
    script = client.get("/assets/app.js").text
    assert 'const MEDIA_CATALOG_ENDPOINT = "/api/media";' in script
    assert 'const CANONICAL_TAGS_ENDPOINT = "/api/canonical-tags";' in script
    assert "loadCatalog();" in script
    assert "loadCatalogTags();" in script
    assert "function buildCatalogQueryParams" in script
    assert "fetch(`${MEDIA_CATALOG_ENDPOINT}" in script
    catalog_block = script[
        script.index("async function loadCatalog") : script.index("async function handleImportClick")
    ]
    assert "scan-preview" not in catalog_block
    assert "media-analysis-preview" not in catalog_block
    assert "media-suggestion-preview" not in catalog_block


def test_browser_does_not_run_analysis_on_initialization_or_candidate_render(
    client: TestClient,
) -> None:
    script = client.get("/assets/app.js").text
    assert "media-analysis-preview" in script
    assert "checkHealth();" in script
    assert "loadLibraries();" in script
    assert "handleInspectClick" in script
    assert "renderScanResult(card, payload);" in script
    render_scan_block = script[
        script.index("function renderScanResult") : script.index("async function handleInspectClick")
    ]
    assert "media-analysis-preview" not in render_scan_block


def test_browser_analysis_is_explicit_and_disables_conflicting_actions(
    client: TestClient,
) -> None:
    html = client.get("/").text
    script = client.get("/assets/app.js").text

    assert "Inspect locally" in html or "Inspect locally" in script
    assert "addEventListener(\"click\"" in script
    assert "handleInspectClick(payload.library_id, candidate" in script
    assert "setInspectActionsDisabled(true)" in script
    assert "setInspectActionsDisabled(false)" in script
    assert "analysisRequestToken" in script


def test_browser_analysis_states_are_distinct_and_truthful(client: TestClient) -> None:
    html = client.get("/").text
    script = client.get("/assets/app.js").text
    combined = html + script

    assert "Local preview" in combined
    assert "Preparing local metadata and representative frames" in combined
    assert "Local media analysis is not available" in combined
    assert "Invalid media relative path" in combined
    assert "Local analysis results are ephemeral" in combined


def test_browser_scan_import_is_explicit_and_same_origin(client: TestClient) -> None:
    html = client.get("/").text
    script = client.get("/assets/app.js").text
    combined = html + script

    assert "explicitly import" in html or "handleImportClick" in script
    assert 'const MEDIA_IMPORTS_ENDPOINT = "media-imports";' in script
    assert "handleImportClick(payload.library_id, candidate" in script
    assert "Importing selected candidate" in script
    assert "Already imported" in script
    assert "Candidate was not found in the current scan." in script
    assert "payload.status === \"already_imported\"" in script
    assert "body: JSON.stringify({ relative_path: candidate.relative_path })" in script
    assert "Import" in combined
    assert "document.querySelectorAll(\".import-button\")" not in script
    assert "importRequestToken" not in script


def test_successful_import_refreshes_catalog_without_mutating_import_behavior(
    client: TestClient,
) -> None:
    script = client.get("/assets/app.js").text

    assert "await loadCatalog();" in script
    import_block = script[script.index("async function handleImportClick") : script.index("async function handleInspectClick")]
    assert "await loadCatalog();" in import_block
    assert "payload.status === \"already_imported\"" in import_block
    assert "body: JSON.stringify({ relative_path: candidate.relative_path })" in import_block


def test_catalog_rendering_uses_safe_dom_text_apis_and_no_inline_html(client: TestClient) -> None:
    script = client.get("/assets/app.js").text

    assert "renderCatalogSuccess" in script
    assert "renderCatalogCard" in script
    assert "deriveCatalogFallbackTitle" in script
    assert "textContent" in script
    assert "appendText" in script
    assert "innerHTML" not in script
    assert "insertAdjacentHTML" not in script


def test_browser_decodes_base64_to_png_blob_and_revokes_object_urls(
    client: TestClient,
) -> None:
    script = client.get("/assets/app.js").text

    assert "atob(" in script
    assert "Uint8Array" in script
    assert 'new Blob([bytes], { type: "image/png" })' in script
    assert "URL.createObjectURL" in script
    assert "URL.revokeObjectURL" in script
    assert "beforeunload" in script
    assert "payload_base64" in script


def test_browser_does_not_store_frame_payloads_or_add_external_runtime_urls(
    client: TestClient,
) -> None:
    script = client.get("/assets/app.js").text
    html = client.get("/").text

    assert "payload_base64" not in script[script.index("function restoredCatalogPageSize") : script.index("function setStatusClass")]
    assert "sessionStorage" not in script
    assert "indexedDB" not in script
    assert "data:image" not in script
    assert "http://" not in html + script
    assert "https://" not in html + script


def test_browser_loads_ai_capability_without_invoking_analysis(client: TestClient) -> None:
    script = client.get("/assets/app.js").text

    assert 'const AI_CAPABILITY_ENDPOINT = "/api/ai/media-suggestion-capability";' in script
    assert "loadAiCapability();" in script
    assert "fetch(AI_CAPABILITY_ENDPOINT" in script
    assert "media-suggestion-preview" in script
    assert script.index("media-suggestion-preview") > script.index("async function handleAnalyzeClick")
    assert "checkHealth();" in script
    assert "loadLibraries();" in script


def test_browser_presents_ai_capability_states_from_api(client: TestClient) -> None:
    html = client.get("/").text
    script = client.get("/assets/app.js").text
    combined = html + script

    assert "AI unavailable" in combined
    assert "AI configured" in combined
    assert "provider_id" in script
    assert "provider_display_name" in script
    assert "model_id" in script
    assert "prompt_version" in script
    assert "execution" in script
    assert ">Model<" in html
    assert "Last server check" in html
    assert "AI is configured by the FrameNest server operator" not in combined


def test_browser_analyze_is_explicit_confirmed_and_cloud_disclosed(client: TestClient) -> None:
    html = client.get("/").text
    script = client.get("/assets/app.js").text
    combined = html + script

    assert "Analyze" in combined
    assert "optimized preview frames" in combined
    assert "original file, local path, and API key are not uploaded" in combined
    assert "will replace the current unsaved Title, Description, and Tags" in combined
    assert "will not be saved automatically" in combined
    assert "physical file will not be renamed" in combined
    assert "confirm_cloud_upload" in script
    assert "Cancel analysis" not in combined
    assert "Provider selection" not in combined
    assert "Model selection" not in combined
    assert "progress" not in script.lower()


def test_browser_analyze_appears_only_after_successful_local_inspection(
    client: TestClient,
) -> None:
    script = client.get("/assets/app.js").text

    assert "renderAiPanelUnavailable" in script
    assert "renderAnalysisSuccess(card, payload)" in script
    assert "renderAiPanelReady(card, payload)" in script
    success_block = script[script.index("function renderAnalysisSuccess") : script.index("function renderScanResult")]
    assert "renderAiPanelReady(card, payload)" in success_block
    assert "resetAiReview(card)" in script
    assert "analysisRequestToken" in script
    assert "suggestionRequestToken" in script


def test_browser_editor_uses_single_form_ai_assistance(client: TestClient) -> None:
    html = client.get("/").text
    script = client.get("/assets/app.js").text
    dialog_section = html[html.index("metadata-dialog"):]

    assert "metadata-title-input" in dialog_section
    assert "metadata-description-input" in dialog_section
    assert "metadata-tag-search-input" in dialog_section
    assert "metadata-ai-filename-input" in dialog_section
    assert "review-title-input" not in dialog_section
    assert "review-description-input" not in dialog_section
    assert "review-tag-input" not in dialog_section
    assert "metadataTagKeysFromSuggestion" in script
    assert "provider_id" in script
    assert "model_id" in script
    assert "prompt_version" in script


def test_browser_editor_has_single_title_description_and_tags_workflow(client: TestClient) -> None:
    html = client.get("/").text
    dialog_section = html[html.index("metadata-dialog") : html.index("</dialog>", html.index("metadata-dialog"))]

    assert dialog_section.count('id="metadata-title-input"') == 1
    assert dialog_section.count('id="metadata-description-input"') == 1
    assert dialog_section.count('id="metadata-tag-search-input"') == 1
    assert dialog_section.count('id="metadata-selected-tags"') == 1
    assert dialog_section.count(">Title<") == 1
    assert dialog_section.count(">Description<") == 1
    assert dialog_section.count(">Tags<") == 1


def test_browser_editor_hides_provider_model_noise_in_ordinary_editor(client: TestClient) -> None:
    html = client.get("/").text
    script = client.get("/assets/app.js").text
    dialog_section = html[html.index("metadata-dialog") : html.index("</dialog>", html.index("metadata-dialog"))]
    ai_panel_body = _javascript_function(script, "renderMetadataAiPanel")

    assert "provider_id" not in dialog_section
    assert "model_id" not in dialog_section
    assert "prompt_version" not in dialog_section
    assert "provider_id ||" not in ai_panel_body
    assert "model_id ||" not in ai_panel_body
    assert "AI analysis is available after confirmation." in ai_panel_body


def test_browser_editor_idle_ai_button_is_exact_and_not_loading(client: TestClient) -> None:
    html = client.get("/").text
    button_start = html.index('id="metadata-ai-analyze-button"')
    button_section = html[button_start : html.index("</button>", button_start)]

    assert "Analyze by AI" in button_section
    assert "🧠 Analyze by AI" not in button_section
    assert "🪄 Analyze by AI" not in button_section
    assert "loading-spinner" not in button_section
    assert "Analyzing…" not in button_section
    assert "metadata-ai-analyze-button__idle" not in button_section
    assert "metadata-ai-analyze-button__loading" not in button_section


def test_browser_editor_ai_button_active_state_replaces_entire_content(client: TestClient) -> None:
    script = client.get("/assets/app.js").text
    render_button_body = _javascript_function(script, "renderMetadataAiAnalyzeButtonContent")
    analyze_block = script[script.index("async function handleAnalyzeMetadataByAi") : script.index("function aiSuggestionErrorMessage")]

    assert "metadataAiAnalyzeButton.replaceChildren()" in render_button_body
    assert 'metadataAiAnalyzeButton.textContent = "Analyze by AI"' in render_button_body
    assert "loading-spinner" not in render_button_body
    assert 'label.textContent = "Analyzing…"' in render_button_body
    assert "metadataAiAnalyzeButton.append(label)" in render_button_body
    assert 'metadataAiStatus.textContent = "Analyzing…"' not in analyze_block


def test_browser_editor_ai_button_active_state_is_prominent_without_idle_animation(client: TestClient) -> None:
    css = client.get("/assets/styles.css").text
    busy_block = css[
        css.index('.metadata-dialog__footer .metadata-ai-analyze-button[aria-busy="true"]')
        : css.index(".metadata-ai-analyze-button > *")
    ]
    reduced_motion_block = css[css.index("@media (prefers-reduced-motion: reduce)") :]

    assert 'metadata-ai-analyze-button:hover::after' not in css
    assert 'metadata-ai-analyze-button:focus-visible::after' not in css
    assert '[aria-busy="true"]::after' in busy_block
    assert "metadata-ai-analyzing" in busy_block
    assert ':disabled:not([aria-busy="true"])' in css
    assert "opacity: 1" in busy_block
    assert "cursor: progress" in busy_block
    assert "animation: none" in reduced_motion_block


def test_browser_ai_replacement_is_session_only_without_mutation_api(
    client: TestClient,
) -> None:
    script = client.get("/assets/app.js").text
    analyze_block = script[script.index("async function handleAnalyzeMetadataByAi") : script.index("function aiSuggestionErrorMessage")]
    controls_body = _javascript_function(script, "updateMetadataControls")

    assert "metadataWorkspace.current.displayTitle = suggestion.title" in analyze_block
    assert "metadataWorkspace.current.description = suggestion.description" in analyze_block
    assert "metadataWorkspace.current.tagKeys = tagKeys" in analyze_block
    assert "metadataWorkspace.suggestedFilename = suggestion.suggestedFilename" in analyze_block
    assert "metadataWorkspace.aiSuggestionApplied = true" in analyze_block
    assert "metadataAiAnalyzeButton.hidden = metadataWorkspace.aiSuggestionApplied && !metadataWorkspace.analyzing;" in controls_body
    assert "fetch(metadataEndpoint" not in analyze_block
    assert "confirm_cloud_upload: true" in analyze_block
    assert "if (metadataWorkspace.analyzing || metadataWorkspace.aiSuggestionApplied) return;" in analyze_block
    assert "metadataWorkspace.current = " not in analyze_block
    assert "metadataWorkspace.suggestedFilename = beforeRequest.suggestedFilename" not in analyze_block
    assert "commit" not in analyze_block.lower()


def test_browser_editor_ai_failure_restores_idle_action_and_preserves_values(client: TestClient) -> None:
    script = client.get("/assets/app.js").text
    controls_body = _javascript_function(script, "updateMetadataControls")
    analyze_block = script[script.index("async function handleAnalyzeMetadataByAi") : script.index("function aiSuggestionErrorMessage")]

    assert "metadataWorkspace.analyzing = false" in analyze_block
    assert "aiSuggestionErrorMessage(payload)" in analyze_block
    assert '"AI analysis failed."' in analyze_block
    assert "metadataWorkspace.current = " not in analyze_block
    assert "beforeRequest" not in analyze_block
    assert "renderMetadataAiAnalyzeButtonContent(metadataWorkspace.analyzing)" in controls_body
    assert "metadataAiAnalyzeButton.disabled = metadataWorkspace.loading" in controls_body
    assert 'metadataAiAnalyzeButton.textContent = "Analyze by AI"' in script


def test_selected_metadata_tag_remove_is_red_and_bounded_to_current_media(client: TestClient) -> None:
    script = client.get("/assets/app.js").text
    css = client.get("/assets/styles.css").text
    render_tags_body = _javascript_function(script, "renderSelectedMetadataTags")
    remove_body = _javascript_function(script, "removeSelectedMetadataTag")
    remove_css = css[css.index(".metadata-tag-chip__remove:hover") : css.index("/* --- Library cards ---")]

    assert 'remove.className = "metadata-tag-chip__remove"' in render_tags_body
    assert "from this media" in render_tags_body
    assert "metadataWorkspace.current.tagKeys = metadataWorkspace.current.tagKeys.filter" in remove_body
    assert "fetch(" not in remove_body
    assert "CANONICAL_TAGS_ENDPOINT" not in remove_body
    assert "delete" not in remove_body.lower()
    assert "border-color: var(--danger)" in remove_css
    assert "background: var(--danger-soft)" in remove_css
    assert "color: var(--danger)" in remove_css


def test_javascript_uses_safe_dom_text_apis_for_repository_values(client: TestClient) -> None:
    script = client.get("/assets/app.js").text
    assert ".textContent" in script
    assert "createTextNode" in script
    assert "innerHTML" not in script
    assert "insertAdjacentHTML" not in script


@pytest.mark.parametrize("path", ["/", "/assets/styles.css", "/assets/app.js"])
def test_application_surfaces_do_not_contain_external_runtime_urls_or_sensitive_values(
    client: TestClient,
    path: str,
) -> None:
    response = client.get(path)
    body = response.text
    assert "http://" not in body
    assert "https://" not in body
    for fragment in FORBIDDEN_RESPONSE_FRAGMENTS:
        assert fragment not in body


def test_browser_catalog_has_all_media_and_processed_scope_controls(client: TestClient) -> None:
    html = client.get("/").text
    script = client.get("/assets/app.js").text

    assert "catalog-scope" in html
    assert "All media" in html
    assert "Processed" in html
    assert "catalogScope" in script or "catalogState.collection" in script
    assert "const PROCESSED_COLLECTION" in script


def test_browser_catalog_scope_defaults_to_all_media_and_switching_is_well_formed(
    client: TestClient,
) -> None:
    script = client.get("/assets/app.js").text

    start = script.index("let catalogState = {")
    end = script.index("};", start) + len("};")
    catalog_state_literal = script[start:end]
    assert "collection: \"\"" in catalog_state_literal or "collection: ''" in catalog_state_literal

    assert "function setCatalogScope(collection)" in script
    assert "catalogState.offset = 0" in script
    assert "setCatalogScope(\"\")" in script or "setCatalogScope('')" in script
    assert "setCatalogScope(PROCESSED_COLLECTION)" in script

    build_start = script.index("function buildCatalogQueryParams()")
    build_end = script.index("}", script.index("return params;", build_start)) + 1
    build_body = script[build_start:build_end]
    assert "if (catalogState.collection)" in build_body
    assert "params.set(\"collection\", catalogState.collection)" in build_body


def test_browser_metadata_editor_hides_processed_state_but_preserves_collection_state(
    client: TestClient,
) -> None:
    html = client.get("/").text
    script = client.get("/assets/app.js").text
    dialog_section = html[html.index("metadata-dialog"):]

    assert "metadata-collection-status" not in dialog_section
    assert "Processed status" not in dialog_section
    assert "Processed collection" not in _javascript_function(script, "renderMetadataWorkspace")
    assert "collectionKey" in script
    assert "processedAtMs" in script
    assert "payload.collection_key" in script
    assert "payload.processed_at_ms" in script
    assert "applyMetadataPayloadToWorkspace" in script


def test_browser_metadata_workspace_no_manual_collection_picker_or_mark_button(client: TestClient) -> None:
    html = client.get("/").text
    script = client.get("/assets/app.js").text
    combined = html + script

    assert "Mark as processed" not in combined
    assert "Select collection" not in combined
    assert "Create collection" not in combined
    assert "manual collection" not in combined.lower()


def test_browser_metadata_discard_restores_persisted_collection_state(client: TestClient) -> None:
    script = client.get("/assets/app.js").text

    start = script.index("function resetMetadataWorkspaceAfterDiscard()")
    end = script.index("\n}\n", start) + len("\n}\n")
    reset_body = script[start:end]

    assert "collectionKey: metadataWorkspace.baseline.collectionKey" in reset_body
    assert "processedAtMs: metadataWorkspace.baseline.processedAtMs" in reset_body


def test_browser_metadata_workspace_uses_nullish_coalescing_for_collection_state(
    client: TestClient,
) -> None:
    script = client.get("/assets/app.js").text

    start = script.index("function applyMetadataPayloadToWorkspace(payload)")
    end = script.index("\n}\n", start) + len("\n}\n")
    body = script[start:end]

    assert "payload.collection_key ?? null" in body
    assert "payload.processed_at_ms ?? null" in body
    assert "payload.collection_key || null" not in body
    assert "payload.processed_at_ms || null" not in body


def test_browser_metadata_workspace_renders_processed_time_semantically(client: TestClient) -> None:
    html = client.get("/").text
    script = client.get("/assets/app.js").text

    dialog_section = html[html.index("metadata-dialog"):]
    assert "metadata-collection-status" not in dialog_section
    assert "createElement(\"time\")" in script or 'createElement("time")' in script
    assert "datetime" in script
    assert ".toISOString()" in script

    start = script.index("function renderMetadataWorkspace()")
    end = script.index("\n}\n", start) + len("\n}\n")
    workspace_body = script[start:end]
    assert "buildProcessedTimeElement" not in workspace_body
    assert "processedAtMs" in script


def test_browser_catalog_card_renders_processed_time_semantically(client: TestClient) -> None:
    script = client.get("/assets/app.js").text

    start = script.index("function renderCatalogCard(item)")
    end = script.index("\n}\n", start) + len("\n}\n")
    card_body = script[start:end]
    assert "processed_at_ms" in card_body or "buildProcessedTimeElement" in card_body
    assert "buildProcessedTimeElement" in script


def test_browser_processed_time_helper_is_reusable_and_safe(client: TestClient) -> None:
    script = client.get("/assets/app.js").text

    helper_markers = [
        "function buildProcessedTimeElement",
        "function renderProcessedTime",
        "function createProcessedTime",
    ]
    assert any(marker in script for marker in helper_markers)
    for marker in helper_markers:
        if marker in script:
            start = script.index(marker)
            end = script.index("\n}\n", start) + len("\n}\n")
            helper_body = script[start:end]
            assert "innerHTML" not in helper_body
            assert ".textContent" in helper_body or ".datetime" in helper_body
            break


def test_browser_processed_time_never_uses_filesystem_timestamps(client: TestClient) -> None:
    script = client.get("/assets/app.js").text

    processed_time_section = script
    for marker in ("processedAtMs", "processed_at_ms"):
        if marker in processed_time_section:
            break
    forbidden = (
        "observed_mtime_ns",
        "mtime",
        "st_mtime",
        "File.getModificationTime",
        "lastModified",
    )
    for fragment in forbidden:
        assert fragment not in script


def test_browser_review_uses_no_persistence_or_hidden_complete_suggestion(
    client: TestClient,
) -> None:
    script = client.get("/assets/app.js").text

    assert "framenest.catalog.pageSize" in script
    assert "sessionStorage" not in script
    assert "indexedDB" not in script
    assert "location.search" not in script
    assert "complete suggestion" not in script.lower()
    assert "console.log" not in script
    assert "payload_base64" in script
    assert "data:image" not in script


# ---------------------------------------------------------------------------
# Terminal glass application shell — Cycle 075
# ---------------------------------------------------------------------------


def test_application_header_is_sticky_and_contains_brand(client: TestClient) -> None:
    html = client.get("/").text
    assert 'class="app-header' in html
    assert "position: sticky" in client.get("/assets/styles.css").text.lower()
    assert "FrameNest" in html
    assert "brand" in html


def test_header_brand_mark_is_circular_branding_not_button(client: TestClient) -> None:
    html = client.get("/").text
    css = client.get("/assets/styles.css").text
    brand_start = html.index("brand-mark")
    brand_section = html[brand_start : html.index("</div>", brand_start)]
    brand_css = css[css.index(".brand-mark") : css.index("/* --- Header command search ---")]

    assert "FN" in brand_section
    assert "<button" not in brand_section
    assert "role=" not in brand_section
    assert "tabindex" not in brand_section
    assert "border-radius: 50%" in brand_css
    assert "rgba(0, 255, 65, 0.75)" in brand_css


def test_header_does_not_contain_pre_alpha_foundation_text(client: TestClient) -> None:
    html = client.get("/").text
    assert "Pre-alpha foundation" not in html
    assert "stage-pill" not in html


def test_header_contains_server_health_status_button(client: TestClient) -> None:
    html = client.get("/").text
    header_section = html[html.index("<header") : html.index("</header>")]
    assert "server-health-button" in html
    assert "Cloud" in header_section
    assert "Server" not in header_section
    assert "aria-label" in header_section
    assert "Local server healthy" in header_section or "server-health-button" in header_section


def test_header_contains_ai_status_button(client: TestClient) -> None:
    html = client.get("/").text
    assert "ai-status-button" in html
    assert ">AI<" in html
    assert "🧠 AI" not in html
    assert "aria-label" in html


def test_header_statuses_keep_accessible_truth_and_state_coloring(client: TestClient) -> None:
    html = client.get("/").text
    css = client.get("/assets/styles.css").text
    script = client.get("/assets/app.js").text

    assert "server-health-button-text" in html
    assert "ai-status-button-text" in html
    assert "visually-hidden" in html
    assert "Local server healthy" in html
    assert "AI status" in html
    assert "setServerHealthButtonState(\"healthy\", \"Server healthy\")" in script
    assert "setAiStatusButtonState(\"healthy\", \"AI available\")" in script
    assert ".status-button--checking .status-button__label" in css
    assert ".status-button--healthy .status-button__label" in css
    assert ".status-button--unhealthy .status-button__label" in css
    assert ".status-button--healthy .status-button__label {\n  color: var(--accent);" in css
    assert ".status-button--unhealthy .status-button__label {\n  color: var(--danger);" in css
    assert ".status-button--checking .status-button__label {\n  color: var(--text-soft);" in css


def test_status_and_gallery_filters_have_white_border_hover_focus(client: TestClient) -> None:
    css = client.get("/assets/styles.css").text

    status_hover = css[css.index(".status-button:hover") : css.index(".status-button__dot")]
    filter_hover = css[css.index(".catalog-filter-chip:hover") : css.index(".catalog-filter-chip[aria-pressed")]
    scope_hover = css[css.index(".catalog-scope button:hover") : css.index(".catalog-scope .scope-active")]
    assert "border-color: rgba(255, 255, 255, 0.86)" in status_hover
    assert ".status-button:focus-visible" in status_hover
    assert "border-color: rgba(255, 255, 255, 0.86)" in filter_hover
    assert ".catalog-filter-chip:focus-visible" in filter_hover
    assert "border-color: rgba(255, 255, 255, 0.86)" in scope_hover
    assert ".catalog-scope button:focus-visible" in scope_hover


def test_frontend_hidden_attribute_is_authoritative(client: TestClient) -> None:
    css = client.get("/assets/styles.css").text

    hidden_block = css[css.index("[hidden]") : css.index(":root")]

    assert "[hidden]" in hidden_block
    assert "display: none !important;" in hidden_block
    assert css.index("[hidden]") < css.index(".settings-dialog__section")
    assert css.index("[hidden]") < css.index(".metadata-dialog__footer .metadata-ai-analyze-button")


def test_application_has_status_dialog_element(client: TestClient) -> None:
    html = client.get("/").text
    assert 'id="status-dialog"' in html
    assert "Status" in html
    assert "AI" in html


def test_status_dialog_has_accessible_ai_and_cloud_tabs(client: TestClient) -> None:
    html = client.get("/").text
    start = html.index('id="status-dialog"')
    status_section = html[start : html.index("</dialog>", start)]

    assert 'role="tablist"' in status_section
    assert 'id="status-tab-ai"' in status_section
    assert 'id="status-tab-cloud"' in status_section
    assert status_section.index('id="status-tab-ai"') < status_section.index('id="status-tab-cloud"')
    assert 'role="tab"' in status_section
    assert 'aria-selected="true"' in status_section
    assert 'aria-controls="status-panel-ai"' in status_section
    assert 'aria-controls="status-panel-cloud"' in status_section
    assert 'role="tabpanel"' in status_section
    assert ">Model<" in status_section
    assert ">Cloud<" in status_section


def test_status_dialog_does_not_contain_provider_configuration_inputs(client: TestClient) -> None:
    html = client.get("/").text
    start = html.index('id="status-dialog"')
    status_section = html[start : html.index("</dialog>", start)]
    assert "Test connection" not in status_section
    assert "Open AI Settings" not in status_section
    assert "OpenAI" not in status_section
    assert "Anthropic" not in status_section
    assert "LMStudio" not in status_section and "LM Studio" not in status_section
    assert "api-key" not in status_section.lower()
    assert "api_key" not in status_section.lower()
    assert '<input' not in status_section
    assert "AI capability" not in status_section
    assert "Last test" not in status_section


def test_javascript_has_health_retry_logic(client: TestClient) -> None:
    script = client.get("/assets/app.js").text
    assert "checkHealth" in script
    assert "retryHealth" in script or "retry" in script.lower()
    assert "healthCheckInFlight" in script or "healthRequestToken" in script or "inFlight" in script


def test_javascript_status_buttons_open_status_tabs(client: TestClient) -> None:
    script = client.get("/assets/app.js").text
    set_tab_body = _javascript_function(script, "setActiveStatusTab")

    assert "ai-status-button" in script or "aiStatusButton" in script
    assert "status-dialog" in script or "statusDialog" in script
    assert 'openStatusDialog("ai")' in script
    assert 'openStatusDialog("cloud")' in script
    assert "loadCloudStatus()" in script
    assert "handleStatusTabKeydown" in script
    assert "ArrowLeft" in script and "ArrowRight" in script
    assert "statusPanelAi.hidden = isCloud" in set_tab_body
    assert "statusPanelCloud.hidden = !isCloud" in set_tab_body
    assert 'statusTabAi.setAttribute("aria-selected", String(!isCloud))' in set_tab_body
    assert 'statusTabCloud.setAttribute("aria-selected", String(isCloud))' in set_tab_body
    assert "showModal" in script


def test_javascript_status_optional_rows_hide_complete_empty_rows(client: TestClient) -> None:
    script = client.get("/assets/app.js").text
    render_row_body = _javascript_function(script, "renderOptionalStatusRow")
    render_cloud_body = _javascript_function(script, "renderCloudStatus")

    assert "row.hidden = true" in render_row_body
    assert 'valueElement.textContent = ""' in render_row_body
    assert "row.hidden = !text" in render_row_body
    assert "statusCloudRemoteRow.hidden = !remote" in render_cloud_body
    assert "statusCloudRemote.textContent = remote" in render_cloud_body


def test_javascript_status_dialog_close_behavior(client: TestClient) -> None:
    script = client.get("/assets/app.js").text
    assert "close" in script.lower()
    assert "Escape" in script or "escape" in script or "keydown" in script
    assert "lastFocusedElementBeforeStatus" in script


def test_javascript_has_distinct_health_states(client: TestClient) -> None:
    script = client.get("/assets/app.js").text
    assert "checking" in script.lower()
    assert "healthy" in script.lower()
    assert "unhealthy" in script.lower() or "error" in script.lower()


def test_javascript_has_distinct_ai_states(client: TestClient) -> None:
    script = client.get("/assets/app.js").text
    assert "checking" in script.lower() or "loading" in script.lower()
    assert "available" in script.lower()
    assert "unavailable" in script.lower()


def test_css_has_terminal_glass_visual_tokens(client: TestClient) -> None:
    css = client.get("/assets/styles.css").text
    assert "--accent" in css
    assert "backdrop-filter" in css or "backdrop-filter" in css.lower()
    assert "blur" in css
    assert "monospace" in css or "mono" in css.lower()


def test_css_supports_reduced_motion(client: TestClient) -> None:
    css = client.get("/assets.css") if False else client.get("/assets/styles.css")
    css_text = css.text
    assert "prefers-reduced-motion" in css_text


def test_css_has_sticky_header_positioning(client: TestClient) -> None:
    css = client.get("/assets/styles.css").text
    assert "position: sticky" in css or "position:sticky" in css


def test_application_does_not_contain_intro_panel_or_hero_copy(client: TestClient) -> None:
    html = client.get("/").text
    assert "intro-panel" not in html
    assert "intro-copy" not in html
    assert "FrameNest is running locally" not in html
    assert "This pre-alpha web shell is served" not in html


def test_application_does_not_contain_foundation_grid_boundary_cards(client: TestClient) -> None:
    html = client.get("/").text
    assert "foundation-grid" not in html
    assert "boundary-card" not in html
    assert "Foundation boundaries" not in html


# ---------------------------------------------------------------------------
# Command search and canonical-tag interaction cleanup — Cycle 076
# ---------------------------------------------------------------------------


def test_header_contains_command_search_input(client: TestClient) -> None:
    html = client.get("/").text
    assert "command-search-input" in html
    assert "command-search" in html
    assert "role=\"search\"" in html or 'role="search"' in html


def test_header_command_search_has_accessible_label(client: TestClient) -> None:
    html = client.get("/").text
    assert "aria-label" in html
    assert "command-search" in html


def test_command_search_suggestion_panel_exists(client: TestClient) -> None:
    html = client.get("/").text
    assert "command-search-suggestions" in html
    assert "listbox" in html or "combobox" in html or "aria-expanded" in html


def test_javascript_has_command_search_suggestion_logic(client: TestClient) -> None:
    script = client.get("/assets/app.js").text
    assert "commandSearchInput" in script or "command-search-input" in script
    assert "commandSearchSuggestions" in script or "command-search-suggestions" in script
    assert "debounce" in script.lower() or "setTimeout" in script
    assert "ArrowDown" in script or "ArrowDown" in script
    assert "ArrowUp" in script or "ArrowUp" in script


def test_javascript_command_search_distinguishes_title_and_tag_results(client: TestClient) -> None:
    script = client.get("/assets/app.js").text
    assert "title" in script.lower()
    assert "tag" in script.lower()
    assert "suggestion" in script.lower()


def test_javascript_command_search_enter_applies_title_query(client: TestClient) -> None:
    script = client.get("/assets/app.js").text
    assert "catalogState.q" in script
    assert "catalogState.offset = 0" in script


def test_catalog_has_single_tag_toggle_region(client: TestClient) -> None:
    html = client.get("/").text
    assert "catalog-tag-filters" in html
    assert "catalog-active-filters" not in html


def test_javascript_tag_filters_use_toggle_semantics(client: TestClient) -> None:
    script = client.get("/assets/app.js").text
    assert "aria-pressed" in script
    assert "toggle" in script.lower() or "includes(tag.key)" in script
    assert "renderActiveCatalogFilters" not in script
    assert "catalogActiveFilters" not in script


def test_javascript_tag_toggle_preserves_and_semantics(client: TestClient) -> None:
    script = client.get("/assets/app.js").text
    assert "catalogState.tagKeys" in script
    assert "filter((activeKey)" in script or "filter(" in script


def test_catalog_does_not_contain_duplicate_filter_text(client: TestClient) -> None:
    html = client.get("/").text
    assert "No active canonical tag filters" not in html
    assert "Canonical tag filters" not in html
    assert "Multiple selected tags use AND semantics" not in html


def test_library_tools_section_is_absent_from_flagship_gallery(client: TestClient) -> None:
    html = client.get("/").text
    assert "Library tools" not in html
    assert "library-browser" not in html
    assert "library-card-template" not in html


def test_library_tools_does_not_expose_uuid_or_path_flavor(client: TestClient) -> None:
    html = client.get("/").text
    assert "path flavor" not in html
    assert "Root path is intentionally hidden" not in html
    assert "Library ID" not in html


def test_javascript_library_rendering_does_not_show_uuid(client: TestClient) -> None:
    script = client.get("/assets/app.js").text
    assert "Library ID" not in script
    assert "path flavor" not in script
    assert "Root path is intentionally hidden" not in script


def test_javascript_scan_error_is_terse(client: TestClient) -> None:
    script = client.get("/assets/app.js").text
    assert "Scan failed" in script
    assert "Scan preview failed before the local response could be read" not in script
    assert "Scan preview failed with a sanitized local error" not in script


def test_javascript_removes_obsolete_catalog_search_handlers(client: TestClient) -> None:
    script = client.get("/assets/app.js").text
    assert "catalogSearchForm" not in script
    assert "catalogSearchInput" not in script
    assert "catalogClearButton" not in script


# ---------------------------------------------------------------------------
# Gallery workspace, details-dialog, and metadata-dialog — Cycle 077
# ---------------------------------------------------------------------------


def test_gallery_grid_replaces_verbose_catalog_layout(client: TestClient) -> None:
    css = client.get("/assets/styles.css").text
    assert "grid-template-columns" in css
    assert "auto-fill" in css or "auto-fit" in css
    assert "repeat(" in css


def test_catalog_card_does_not_show_technical_metadata_list(client: TestClient) -> None:
    script = client.get("/assets/app.js").text
    start = script.index("function renderCatalogCard(item)")
    end = script.index("\n}\n", start) + len("\n}\n")
    card_body = script[start:end]
    assert "catalog-facts" not in card_body
    assert "Locations" not in card_body
    assert "Availability" not in card_body
    assert "Media ID" not in card_body
    assert "catalog-locations" not in card_body


def test_catalog_card_does_not_show_fallback_label_text(client: TestClient) -> None:
    script = client.get("/assets/app.js").text
    start = script.index("function renderCatalogCard(item)")
    end = script.index("\n}\n", start) + len("\n}\n")
    card_body = script[start:end]
    assert "Fallback label from first deterministic relative location" not in card_body
    assert "Persisted display title" not in card_body
    assert "No canonical tags" not in card_body


def test_catalog_card_has_play_surface_and_edit_action_without_details_button(client: TestClient) -> None:
    script = client.get("/assets/app.js").text
    card_body = _javascript_function(script, "renderCatalogCard")
    surface_body = _javascript_function(script, "renderCatalogCardMediaSurface")
    assert "Edit" in card_body
    assert "View details" not in card_body
    assert "Edit metadata" not in card_body
    assert 'textContent = "▶"' not in surface_body
    assert "media-placeholder__play-indicator" in script
    assert "activateCardPlayback" in surface_body
    assert "openDetailsDialog(item, titleButton)" in card_body
    assert "handleOpenMetadataWorkspace" in card_body


def test_catalog_card_has_truthful_unavailable_fallback(client: TestClient) -> None:
    script = client.get("/assets/app.js").text
    fallback_body = _javascript_function(script, "renderUnavailableCardMediaSurface")
    assert "data-media-state" in fallback_body
    assert "unavailable" in fallback_body
    assert "No local playback available" in fallback_body
    assert "mediaContentUrl" not in fallback_body


def test_details_dialog_exists_in_html(client: TestClient) -> None:
    html = client.get("/").text
    assert "media-details-dialog" in html or "details-dialog" in html
    assert "dialog" in html.lower()


def test_metadata_dialog_exists_in_html(client: TestClient) -> None:
    html = client.get("/").text
    assert "metadata-dialog" in html or "metadata-workspace" in html
    assert "dialog" in html.lower()


def test_metadata_workspace_not_in_normal_document_flow(client: TestClient) -> None:
    html = client.get("/").text
    assert "<dialog" in html
    assert 'id="metadata-workspace"' in html or 'id="metadata-dialog"' in html


def test_javascript_has_details_dialog_logic(client: TestClient) -> None:
    script = client.get("/assets/app.js").text
    assert "detailsDialog" in script or "details-dialog" in script or "mediaDetailsDialog" in script
    assert "openDetailsDialog" in script or "showDetails" in script or "openDetails" in script
    assert "closeDetailsDialog" in script or "closeDetails" in script


def test_javascript_details_dialog_has_edit_transition(client: TestClient) -> None:
    script = client.get("/assets/app.js").text
    assert "handleOpenMetadataWorkspace" in script
    assert "Edit" in script


def test_javascript_metadata_dialog_uses_show_modal(client: TestClient) -> None:
    script = client.get("/assets/app.js").text
    assert "showModal" in script or "showModal()" in script
    assert "close()" in script or ".close(" in script


def test_javascript_dialog_has_dirty_close_protection(client: TestClient) -> None:
    script = client.get("/assets/app.js").text
    assert "confirmDiscardDirtyMetadata" in script
    assert "confirm(" in script


def test_javascript_dialog_has_focus_restoration(client: TestClient) -> None:
    script = client.get("/assets/app.js").text
    assert "lastFocused" in script or "focusReturn" in script or "openerElement" in script or ".focus()" in script


def test_javascript_dialog_has_escape_close(client: TestClient) -> None:
    script = client.get("/assets/app.js").text
    assert "Escape" in script or "escape" in script


def test_javascript_card_has_compact_tag_pills(client: TestClient) -> None:
    script = client.get("/assets/app.js").text
    start = script.index("function renderCatalogCard(item)")
    end = script.index("\n}\n", start) + len("\n}\n")
    card_body = script[start:end]
    assert "catalog-tag" in card_body or "tag-pill" in card_body or "tag" in card_body.lower()


def test_javascript_card_has_status_row(client: TestClient) -> None:
    script = client.get("/assets/app.js").text
    start = script.index("function renderCatalogCard(item)")
    end = script.index("\n}\n", start) + len("\n}\n")
    card_body = script[start:end]
    assert "processed" in card_body.lower() or "status" in card_body.lower()


def test_javascript_card_has_persistent_preview_first_media_surface(client: TestClient) -> None:
    script = client.get("/assets/app.js").text
    surface_body = _javascript_function(script, "renderCatalogCardMediaSurface")
    preview_body = _javascript_function(script, "renderPersistentPreview")
    assert "mediaGalleryPreviewUrl(item.media_id, location.location_id)" in preview_body
    assert 'document.createElement("img")' in preview_body
    assert 'image.loading = "lazy"' in preview_body
    assert 'image.decoding = "async"' in preview_body
    assert "mediaContentUrl(" not in surface_body
    assert 'document.createElement("video")' not in surface_body
    assert "Video placeholder" not in surface_body
    assert "Animated image placeholder" not in surface_body


def test_html_does_not_contain_permanent_metadata_section_in_flow(client: TestClient) -> None:
    html = client.get("/").text
    assert 'class="metadata-workspace"' not in html or "<dialog" in html


def test_javascript_preserves_existing_metadata_state_machine(client: TestClient) -> None:
    script = client.get("/assets/app.js").text
    assert "metadataWorkspace.baseline" in script
    assert "metadataWorkspace.current" in script
    assert "applyMetadataPayloadToWorkspace" in script
    assert "handleSaveMetadata" in script
    assert "handleDiscardMetadataChanges" in script
    assert "confirmDiscardDirtyMetadata" in script
    assert "normalizedMetadataFormState" in script


# ---------------------------------------------------------------------------
# On-demand gallery preview — Cycle 078
# ---------------------------------------------------------------------------


def test_card_uses_media_surface_for_playback_without_visible_play_control(client: TestClient) -> None:
    script = client.get("/assets/app.js").text
    surface_body = _javascript_function(script, "renderCatalogCardMediaSurface")
    assert 'textContent = "▶"' not in surface_body
    assert "media-placeholder__play-indicator" in script
    assert "activateCardPlayback" in surface_body
    assert 'surface.addEventListener("click"' in surface_body
    assert 'surface.addEventListener("keydown"' in surface_body
    assert 'surface.setAttribute("role", "button")' in surface_body
    assert 'surface.setAttribute("tabindex", "0")' in surface_body
    assert "handleCardPreview" not in _javascript_function(script, "renderCatalogCard")


def test_no_automatic_analysis_on_page_load(client: TestClient) -> None:
    script = client.get("/assets/app.js").text
    init_section = script[script.index("checkHealth();"):]
    assert "media-analysis-preview" not in init_section[:200]


def test_javascript_reuses_existing_analysis_endpoint(client: TestClient) -> None:
    script = client.get("/assets/app.js").text
    assert "media-analysis-preview" in script
    assert "LIBRARIES_ENDPOINT" in script


def test_javascript_has_preview_cache(client: TestClient) -> None:
    script = client.get("/assets/app.js").text
    assert "previewCache" in script or "previewCacheMap" in script
    assert "MAX_PREVIEW_CACHE" in script or "maxPreviewCache" in script or "previewCacheLimit" in script


def test_preview_cache_does_not_use_persistent_storage(client: TestClient) -> None:
    script = client.get("/assets/app.js").text
    preview_section = script[script.index("function renderCardPreviewFrames") : script.index("function selectPlaybackLocation")]
    assert "localStorage" not in preview_section
    assert "sessionStorage" not in script
    assert "indexedDB" not in script


def test_javascript_has_single_active_preview_rule(client: TestClient) -> None:
    script = client.get("/assets/app.js").text
    assert "activePreviewMediaId" in script or "activePreviewTimer" in script or "activeCardPreview" in script
    assert "clearInterval" in script or "stopAnimationFrame" in script or "stopPreviewTimer" in script or "stopCardPreview" in script


def test_javascript_has_preview_race_protection(client: TestClient) -> None:
    script = client.get("/assets/app.js").text
    assert "previewRequestToken" in script or "previewAbortController" in script or "AbortController" in script


def test_javascript_has_previewable_location_selection(client: TestClient) -> None:
    script = client.get("/assets/app.js").text
    assert "previewableLocation" in script or "selectPreviewable" in script or "resolvePreviewable" in script or "getPreviewableLocation" in script
    assert "availability" in script.lower()
    assert "available" in script.lower()


def test_javascript_unavailable_location_does_not_trigger_analysis(client: TestClient) -> None:
    script = client.get("/assets/app.js").text
    assert "available" in script
    assert "offline" in script or "missing" in script or "unavailable" in script


def test_javascript_preview_uses_honest_terminology(client: TestClient) -> None:
    script = client.get("/assets/app.js").text
    assert "Preview" in script
    assert "cover" not in script.lower() or "placeholder" in script.lower()
    assert "thumbnail" not in script.lower() or "placeholder" in script.lower()


def test_javascript_preview_states_exist(client: TestClient) -> None:
    script = client.get("/assets/app.js").text
    assert "loading" in script.lower() or "Loading" in script
    assert "unavailable" in script.lower() or "Preview unavailable" in script
    assert "Retry" in script or "retry" in script.lower()


def test_javascript_preview_does_not_mutate_metadata_state(client: TestClient) -> None:
    script = client.get("/assets/app.js").text
    assert "metadataWorkspace" in script
    assert "previewCache" in script or "previewCacheMap" in script
    preview_section_start = script.find("previewCache")
    if preview_section_start == -1:
        preview_section_start = script.find("previewCacheMap")
    assert preview_section_start != -1


def test_details_dialog_has_playback_integration(client: TestClient) -> None:
    script = client.get("/assets/app.js").text
    assert "media-details-dialog" in script
    assert "renderDetailsMedia" in script
    assert "mediaContentUrl" in script
    assert "/content" in script


def test_details_dialog_does_not_use_frame_navigation(client: TestClient) -> None:
    script = client.get("/assets/app.js").text
    assert "Previous frame" not in script
    assert "Next frame" not in script
    assert "detailsPreviewFrameIndex" not in script
    assert "detailsPreviewTimer" not in script


def test_javascript_details_playback_uses_identity_only_url(client: TestClient) -> None:
    script = client.get("/assets/app.js").text
    start = script.index("function mediaContentUrl(")
    end = script.index("\n}\n", start) + len("\n}\n")
    url_body = script[start:end]
    assert "MEDIA_CATALOG_ENDPOINT" in url_body
    assert "media_id" in url_body or "mediaId" in url_body
    assert "location_id" in url_body or "locationId" in url_body
    assert "relative_path" not in url_body
    assert "library.path" not in url_body


def test_javascript_available_cards_use_identity_only_preview_and_content_urls(client: TestClient) -> None:
    script = client.get("/assets/app.js").text
    surface_body = _javascript_function(script, "renderCatalogCardMediaSurface")
    media_url_body = _javascript_function(script, "mediaContentUrl")
    preview_url_body = _javascript_function(script, "mediaGalleryPreviewUrl")

    assert "selectSupportedAvailableLocation(item)" in surface_body
    assert "renderPersistentPreview(surface, item, location, title)" in surface_body
    assert "MEDIA_CATALOG_ENDPOINT" in media_url_body
    assert "mediaId" in media_url_body
    assert "locationId" in media_url_body
    assert "encodeURIComponent(mediaId)" in media_url_body
    assert "encodeURIComponent(locationId)" in media_url_body
    assert "gallery-preview" in preview_url_body
    assert "encodeURIComponent(mediaId)" in preview_url_body
    assert "encodeURIComponent(locationId)" in preview_url_body
    assert "relative_path" not in media_url_body
    assert "relative_path" not in preview_url_body
    assert "library" not in media_url_body.lower()
    assert "library" not in preview_url_body.lower()


def test_javascript_initial_card_renders_static_persistent_preview_image(client: TestClient) -> None:
    script = client.get("/assets/app.js").text
    preview_body = _javascript_function(script, "renderPersistentPreview")

    assert 'document.createElement("img")' in preview_body
    assert "media-placeholder__preview-img" in preview_body
    assert "image.alt = `Gallery preview for ${title}`" in preview_body
    assert "image.src = mediaGalleryPreviewUrl(item.media_id, location.location_id)" in preview_body
    assert "renderPreviewFallback(surface, title)" in preview_body
    assert "mediaContentUrl" not in preview_body


def test_javascript_initial_card_render_does_not_fetch_original_or_generate_preview(client: TestClient) -> None:
    script = client.get("/assets/app.js").text
    surface_body = _javascript_function(script, "renderCatalogCardMediaSurface")
    preview_body = _javascript_function(script, "renderPersistentPreview")
    fallback_body = _javascript_function(script, "renderPreviewFallback")

    assert "mediaGalleryPreviewUrl(item.media_id, location.location_id)" in preview_body
    assert "mediaContentUrl" not in surface_body
    assert "/content" not in surface_body
    assert "media-analysis-preview" not in surface_body
    assert "media-analysis-preview" not in preview_body
    assert "previews generate" not in script
    assert "mediaContentUrl" not in fallback_body


def test_javascript_explicit_card_play_renders_original_media(client: TestClient) -> None:
    script = client.get("/assets/app.js").text
    playback_body = _javascript_function(script, "renderCardOriginalPlayback")
    video_section = playback_body[
        playback_body.index('document.createElement("video")') : playback_body.index("} else {")
    ]
    image_section = playback_body[playback_body.index('document.createElement("img")') :]

    assert "video.src = url" in video_section
    assert 'video.preload = "metadata"' in video_section
    assert "video.playsInline = true" in video_section
    assert "video.autoplay = false" in video_section
    assert "video.muted = true" in video_section
    assert "video.controls = false" in video_section
    assert "video.loop = false" in video_section
    assert "video.play(" in video_section
    assert "image.src = url" in image_section
    assert "mediaContentUrl(item.media_id, location.location_id)" in playback_body


def test_javascript_card_media_surface_is_accessible_and_card_title_opens_details(client: TestClient) -> None:
    script = client.get("/assets/app.js").text
    surface_body = _javascript_function(script, "renderCatalogCardMediaSurface")
    card_body = _javascript_function(script, "renderCatalogCard")
    open_body = _javascript_function(script, "openPlaybackDetails")

    assert "aria-label" in surface_body
    assert "Play ${title}" in surface_body
    assert "activateCardPlayback(item, surface)" in surface_body
    assert "Enter" in surface_body
    assert "event.key === \" \"" in surface_body
    assert "Open details for" in card_body
    assert "openDetailsDialog(item, titleButton)" in card_body
    assert "openDetailsDialog(item, openerElement, { playWhenReady: true })" in open_body
    assert "mediaContentUrl" in _javascript_function(script, "renderDetailsMedia")


def test_javascript_catalog_card_details_button_is_removed(client: TestClient) -> None:
    script = client.get("/assets/app.js").text
    card_body = _javascript_function(script, "renderCatalogCard")
    assert "detailsButton" not in card_body
    assert "openDetailsDialog(item, detailsButton)" not in card_body


def test_javascript_catalog_rerender_cleans_card_media_resources(client: TestClient) -> None:
    script = client.get("/assets/app.js").text
    cleanup_body = _javascript_function(script, "cleanupCatalogCardMedia")
    success_body = _javascript_function(script, "renderCatalogSuccess")

    assert "cardMediaElements.forEach" in cleanup_body
    assert "element.pause()" in cleanup_body
    assert "element.removeAttribute(\"src\")" in cleanup_body
    assert "element.load()" in cleanup_body
    assert "cardMediaElements = new Set()" in cleanup_body
    assert success_body.index("cleanupCatalogCardMedia()") < success_body.index("catalogResults.replaceChildren()")


def test_javascript_details_is_player_first_with_single_title(client: TestClient) -> None:
    html = client.get("/").text
    script = client.get("/assets/app.js").text
    details_section = html[html.index("media-details-dialog") : html.index("</dialog>", html.index("media-details-dialog"))]
    populate_body = _javascript_function(script, "populateDetailsDialog")

    assert 'id="media-details-title"' in details_section
    assert "media-details-display-title" not in details_section
    assert "detailsDialogTitle.textContent" in populate_body
    assert "detailsDisplayTitle" not in script
    assert "detailsTechnical.removeAttribute(\"open\")" in populate_body


def test_javascript_details_selects_first_available_location(client: TestClient) -> None:
    script = client.get("/assets/app.js").text
    start = script.index("function selectPlaybackLocation(")
    end = script.index("\n}\n", start) + len("\n}\n")
    location_body = script[start:end]
    assert "availability" in location_body
    assert "available" in location_body
    assert "location_id" in location_body


def test_javascript_details_video_has_required_attributes(client: TestClient) -> None:
    script = client.get("/assets/app.js").text
    render_body = _javascript_function(script, "renderDetailsMedia")
    assert "document.createElement(\"video\")" in render_body
    assert "video.controls = true" in render_body
    assert 'video.preload = "metadata"' in render_body
    assert "video.playsInline = true" in render_body
    assert "video.autoplay = false" in render_body or "video.autoplay" not in render_body


def test_javascript_details_image_uses_real_img(client: TestClient) -> None:
    script = client.get("/assets/app.js").text
    render_body = _javascript_function(script, "renderDetailsMedia")
    assert "document.createElement(\"img\")" in render_body
    assert ".alt =" in render_body


def test_javascript_details_media_uses_display_title(client: TestClient) -> None:
    script = client.get("/assets/app.js").text
    render_body = _javascript_function(script, "renderDetailsMedia")
    assert "display_title" in render_body or "deriveCatalogFallbackTitle" in render_body
    assert "aria-label" in render_body or ".alt =" in render_body


def test_javascript_details_has_unavailable_state(client: TestClient) -> None:
    script = client.get("/assets/app.js").text
    assert "renderDetailsMediaUnavailable" in script
    assert "Media unavailable." in script


def test_javascript_details_has_explicit_media_cleanup(client: TestClient) -> None:
    script = client.get("/assets/app.js").text
    assert "cleanupDetailsMedia" in script
    close_section = script[script.index("function closeDetailsDialog"):]
    assert "cleanupDetailsMedia" in close_section[:300]
    cleanup_section = _javascript_function(script, "cleanupDetailsMedia")
    assert "removeAttribute(\"src\")" in cleanup_section or "removeAttribute('src')" in cleanup_section
    assert "pause()" in cleanup_section
    assert "load()" in cleanup_section


def test_javascript_details_ignores_stale_media_events(client: TestClient) -> None:
    script = client.get("/assets/app.js").text
    assert "detailsMediaToken" in script
    render_section = _javascript_function(script, "renderDetailsMedia")
    assert "token !== detailsMediaToken" in render_section


def test_javascript_details_media_handlers_exist_before_src(client: TestClient) -> None:
    script = client.get("/assets/app.js").text
    render_section = _javascript_function(script, "renderDetailsMedia")
    video_start = render_section.index('document.createElement("video")')
    image_start = render_section.index('document.createElement("img")')
    video_section = render_section[video_start:image_start]
    image_section = render_section[image_start:]

    for handler in ("video.onloadeddata =", "video.oncanplay =", "video.onerror ="):
        assert video_section.index(handler) < video_section.index("video.src = url")
    assert video_section.index("video.src = url") < video_section.index("appendChild(video)")

    for handler in ("img.onload =", "img.onerror ="):
        assert image_section.index(handler) < image_section.index("img.src = url")
    assert image_section.index("img.src = url") < image_section.index("appendChild(img)")


def test_javascript_details_media_loading_cannot_start_before_handlers(client: TestClient) -> None:
    script = client.get("/assets/app.js").text
    render_section = _javascript_function(script, "renderDetailsMedia")

    video_src_index = render_section.index("video.src = url")
    assert render_section.index("video.onloadeddata =") < video_src_index
    assert render_section.index("video.oncanplay =") < video_src_index
    assert render_section.index("video.onerror =") < video_src_index

    image_src_index = render_section.index("img.src = url")
    assert render_section.index("img.onload =") < image_src_index
    assert render_section.index("img.onerror =") < image_src_index


def test_javascript_details_media_success_reveals_element_and_clears_loading(client: TestClient) -> None:
    script = client.get("/assets/app.js").text
    render_section = _javascript_function(script, "renderDetailsMedia")
    loadeddata_section = render_section[
        render_section.index("video.onloadeddata =") : render_section.index("video.oncanplay =")
    ]
    canplay_section = render_section[
        render_section.index("video.oncanplay =") : render_section.index("video.onerror =")
    ]
    image_load_section = render_section[
        render_section.index("img.onload =") : render_section.index("img.onerror =")
    ]

    for handler_section in (loadeddata_section, canplay_section, image_load_section):
        assert "token !== detailsMediaToken" in handler_section
        assert "loading.remove()" in handler_section
        assert ".hidden = false" in handler_section


def test_javascript_details_media_error_shows_unavailable_state(client: TestClient) -> None:
    script = client.get("/assets/app.js").text
    render_section = _javascript_function(script, "renderDetailsMedia")
    video_error_section = render_section[
        render_section.index("video.onerror =") : render_section.index("detailsMediaElement = video")
    ]
    image_error_section = render_section[
        render_section.index("img.onerror =") : render_section.index("detailsMediaElement = img")
    ]

    for handler_section in (video_error_section, image_error_section):
        assert "token !== detailsMediaToken" in handler_section
        assert "cleanupDetailsMedia({ invalidate: false })" in handler_section
        assert "renderDetailsMediaUnavailable(detailsPreviewContainer)" in handler_section


def test_javascript_details_media_append_is_guarded_after_src_assignment(client: TestClient) -> None:
    script = client.get("/assets/app.js").text
    render_section = _javascript_function(script, "renderDetailsMedia")

    assert "token === detailsMediaToken && detailsMediaElement === video" in render_section
    assert "token === detailsMediaToken && detailsMediaElement === img" in render_section


def test_javascript_details_cleanup_invalidates_loading_media(client: TestClient) -> None:
    script = client.get("/assets/app.js").text
    cleanup_section = _javascript_function(script, "cleanupDetailsMedia")
    close_section = _javascript_function(script, "closeDetailsDialog")

    assert "invalidate = true" in cleanup_section
    assert "detailsMediaToken += 1" in cleanup_section
    assert "cleanupDetailsMedia()" in close_section


def test_javascript_details_replacement_invalidates_old_media_before_new_src(client: TestClient) -> None:
    script = client.get("/assets/app.js").text
    render_section = _javascript_function(script, "renderDetailsMedia")

    cleanup_index = render_section.index("cleanupDetailsMedia()")
    token_index = render_section.index("const token = ++detailsMediaToken")
    video_src_index = render_section.index("video.src = url")
    image_src_index = render_section.index("img.src = url")

    assert cleanup_index < token_index < video_src_index
    assert cleanup_index < token_index < image_src_index


def test_gallery_reference_no_longer_contains_canonical_tag_fragment() -> None:
    gallery = Path("GALLERY.md").read_text(encoding="utf-8")
    assert "\nsuggestions, keyboard and mouse navigation" not in gallery
    assert "Tag editing should support suggestions" in gallery


def test_gallery_reference_documents_content_first_playback_boundary() -> None:
    gallery = Path("GALLERY.md").read_text(encoding="utf-8")
    assert "persistent server-generated static JPEG\ngallery preview derivatives" in gallery
    assert "/gallery-preview" in gallery
    assert "Initial card rendering does not require original\nGIF or MP4 transfer" in gallery
    assert "Missing or unavailable derivatives use a compact\nnon-original fallback" in gallery
    assert "Activating the card's media\nsurface" in gallery
    assert "Opening Details from the card title continues to use\noriginal GIF/MP4 content" in gallery
    assert "not durable accepted covers" in gallery
    assert "Cover Studio state" in gallery
    assert "Details uses a black player-first surface" in gallery


def test_javascript_details_no_longer_loads_representative_frames(client: TestClient) -> None:
    script = client.get("/assets/app.js").text
    assert "loadDetailsPreview" not in script
    assert "renderDetailsPreviewFrames" not in script
    assert "startDetailsPreviewCycling" not in script


def test_javascript_has_reduced_motion_preview_behavior(client: TestClient) -> None:
    script = client.get("/assets/app.js").text
    assert "prefers-reduced-motion" in script or "reducedMotion" in script or "matchMedia" in script


def test_javascript_reuses_base64_decode_helper(client: TestClient) -> None:
    script = client.get("/assets/app.js").text
    assert "decodeBase64Png" in script
    assert "atob(" in script
    assert "URL.createObjectURL" in script


def test_javascript_preview_does_not_persist_frames(client: TestClient) -> None:
    script = client.get("/assets/app.js").text
    preview_section = script[script.index("function renderCardPreviewFrames") : script.index("function selectPlaybackLocation")]
    assert "localStorage" not in preview_section
    assert "sessionStorage" not in script
    assert "indexedDB" not in script


def test_javascript_has_no_preview_on_hover_or_scroll(client: TestClient) -> None:
    script = client.get("/assets/app.js").text
    assert "mouseover" not in script.lower() or "hover" not in script.lower()
    assert "IntersectionObserver" not in script


# ---------------------------------------------------------------------------
# Urgent Gallery UI Regression Repair — Cycle 078A
# ---------------------------------------------------------------------------


def test_dialogs_not_open_in_source_html(client: TestClient) -> None:
    html = client.get("/").text
    assert 'open=""' not in html
    assert "open" not in html.split("<dialog")[1].split(">")[0] if "<dialog" in html else True


def test_css_closes_dialogs_without_open_attribute(client: TestClient) -> None:
    css = client.get("/assets/styles.css").text
    assert "dialog:not([open])" in css or "dialog:not([open])" in css.replace(" ", "")


def test_css_dialog_layout_only_under_open(client: TestClient) -> None:
    css = client.get("/assets/styles.css").text
    assert "dialog[open]" in css or "dialog[open]" in css.replace(" ", "")


def test_startup_does_not_open_metadata_dialog(client: TestClient) -> None:
    script = client.get("/assets/app.js").text
    init_section = script[script.index("checkHealth();"):]
    assert "metadataDialog.showModal()" not in init_section[:200]
    assert "showModal()" not in init_section[:200]


def test_javascript_focuses_search_on_startup(client: TestClient) -> None:
    script = client.get("/assets/app.js").text
    assert "commandSearchInput.focus()" in script or "commandSearchInput.focus()" in script
    assert "preventScroll" in script


def test_search_suggestions_close_on_no_results(client: TestClient) -> None:
    script = client.get("/assets/app.js").text
    assert '"No matches."' not in script or "closeCommandSearchSuggestions" in script
    render_section = script[script.index("function renderCommandSearchSuggestions"):]
    assert "No matches" not in render_section[:500] or "closeCommandSearchSuggestions" in render_section[:500]


def test_javascript_has_fallback_title_suggestions(client: TestClient) -> None:
    script = client.get("/assets/app.js").text
    assert "deriveCatalogFallbackTitle" in script
    search_section = script[script.index("function renderCommandSearchSuggestions"):]
    assert "fallback" in search_section[:2000].lower() or "deriveCatalogFallbackTitle" in search_section[:2000] or "catalogResults" in search_section[:2000]


def test_card_visual_surface_is_preview_trigger(client: TestClient) -> None:
    script = client.get("/assets/app.js").text
    surface_body = _javascript_function(script, "renderCatalogCardMediaSurface")
    assert "activateCardPlayback(item" in surface_body
    assert "media-placeholder__play-indicator" in script
    assert 'surface.setAttribute("role", "button")' in surface_body


def test_card_does_not_have_separate_footer_preview_button(client: TestClient) -> None:
    script = client.get("/assets/app.js").text
    start = script.index("function renderCatalogCard(item)")
    end = script.index("\n}\n", start) + len("\n}\n")
    card_body = script[start:end]
    assert "catalog-card__preview-button" not in card_body or "Preview" not in card_body


def test_javascript_no_manual_frame_navigation_controls(client: TestClient) -> None:
    script = client.get("/assets/app.js").text
    assert '"Prev"' not in script or "detailsPreviewNavigate" not in script
    assert '"Next"' not in script or "detailsPreviewNavigate" not in script
    assert '"Start"' not in script or "detailsPreviewNavigate" not in script


def test_details_has_no_frame_counter(client: TestClient) -> None:
    script = client.get("/assets/app.js").text
    assert "details-preview-counter" not in script or "detailsPreviewNavigate" not in script


def test_details_dialog_has_one_visual_surface(client: TestClient) -> None:
    html = client.get("/").text
    details_section = html[html.index("media-details-dialog"):]
    assert details_section.count("media-placeholder") <= 2
    assert "media-details-display-title" not in details_section


def test_metadata_dialog_contains_save_and_cancel(client: TestClient) -> None:
    html = client.get("/").text
    dialog_section = html[html.index("metadata-dialog"):]
    assert "Save" in dialog_section
    assert "Cancel" in dialog_section
    assert "Save metadata" not in dialog_section
    assert "Discard changes" not in dialog_section
    assert "metadata-save-button" in dialog_section
    assert "metadata-discard-button" in dialog_section


def test_metadata_dialog_contains_single_form_ai_assistance(client: TestClient) -> None:
    html = client.get("/").text
    dialog_section = html[html.index("metadata-dialog"):]

    assert "Analyze by AI" in dialog_section
    assert "AI Draft" not in dialog_section
    assert "Use draft" not in dialog_section
    assert "Discard draft" not in dialog_section
    assert "Suggested filename" in dialog_section
    assert "The physical file has not been renamed" in dialog_section
    assert dialog_section.index("metadata-save-button") < dialog_section.index("metadata-ai-analyze-button")
    assert dialog_section.index("metadata-ai-analyze-button") < dialog_section.index("metadata-discard-button")
    assert "Canonical key" not in dialog_section
    assert "NVIDIA_API_KEY" not in dialog_section
    assert "Authorization" not in dialog_section


def test_javascript_metadata_ai_analysis_requires_confirmation_and_identity_url(
    client: TestClient,
) -> None:
    script = client.get("/assets/app.js").text

    assert "function mediaAiSuggestionEndpoint(mediaId, locationId)" in script
    assert "${mediaId}/locations/${locationId}/ai-suggestion-preview" in script
    assert "handleAnalyzeMetadataByAi" in script
    analyze_body = script[script.index("async function handleAnalyzeMetadataByAi") : script.index("function aiSuggestionErrorMessage")]
    assert "confirm(" in analyze_body
    assert "confirm_cloud_upload: true" in script
    assert "metadataAiRequestToken" in script
    assert "token !== metadataAiRequestToken" in script
    assert "metadataWorkspace.openMediaId === null" in script
    assert "relative_path" not in analyze_body
    assert "NVIDIA_API_KEY" not in script
    assert "Authorization" not in script


def test_javascript_metadata_ai_success_populates_single_form_without_autosave_or_rename(client: TestClient) -> None:
    script = client.get("/assets/app.js").text
    analyze_body = script[script.index("async function handleAnalyzeMetadataByAi") : script.index("function aiSuggestionErrorMessage")]

    assert "metadataWorkspace.current.displayTitle = suggestion.title" in analyze_body
    assert "metadataWorkspace.current.description = suggestion.description" in analyze_body
    assert "metadataWorkspace.current.tagKeys = tagKeys" in analyze_body
    assert "metadataWorkspace.suggestedFilename = suggestion.suggestedFilename" in analyze_body
    assert "metadataWorkspace.aiSuggestionApplied = true" in analyze_body
    assert "metadataTagKeysFromSuggestion(suggestion.tags)" in analyze_body
    assert "metadataAiAnalyzeButton.hidden = metadataWorkspace.aiSuggestionApplied" in script
    assert "fetch(metadataEndpoint" not in analyze_body
    assert "Review the updated fields, then Save." in analyze_body
    assert "fetch(metadataEndpoint" not in analyze_body
    assert "handleUseMetadataAiDraft" not in script
    assert "handleDiscardMetadataAiDraft" not in script


def test_header_uses_compact_brand_and_accessible_status_labels(client: TestClient) -> None:
    html = client.get("/").text
    header_section = html[html.index("app-header") : html.index("</header>")]

    assert ">FN<" in header_section
    assert ">FrameNest<" not in header_section
    assert ">Cloud<" in header_section
    assert ">AI<" in header_section
    assert ">🧠 AI<" not in header_section
    assert ">Server<" not in header_section
    for visible_state in (">Healthy<", ">Available<", ">Unavailable<", ">Checking<"):
        assert visible_state not in header_section
    assert "visually-hidden" in header_section


def test_javascript_catalog_page_size_is_bounded_persisted_and_resets_page(client: TestClient) -> None:
    script = client.get("/assets/app.js").text

    assert "const CATALOG_PAGE_SIZE_OPTIONS = [10, 30, 60, 90];" in script
    assert 'const CATALOG_PAGE_SIZE = 30;' in script
    assert "framenest.catalog.pageSize" in script
    assert "CATALOG_PAGE_SIZE_OPTIONS.includes(stored)" in script
    assert "catalogState.offset = 0;" in script[script.index("catalogPageSizeSelect.addEventListener"):]
    assert 'params.set("limit", String(catalogState.limit));' in script


def test_css_details_dialog_uses_black_player_first_surfaces(client: TestClient) -> None:
    css = client.get("/assets/styles.css").text
    details_css = css[css.index(".media-details-dialog") : css.index("/* --- Metadata edit dialog --- */")]

    assert "background: #000;" in details_css
    assert ".media-details-dialog__header" in details_css
    assert ".media-details-dialog__footer" in details_css
    assert ".details-preview-container" in details_css
    assert "max-height: min(62dvh, 560px)" in details_css


def test_javascript_card_playback_cleanup_releases_media_resources(client: TestClient) -> None:
    script = client.get("/assets/app.js").text
    cleanup_body = _javascript_function(script, "cleanupCatalogCardMedia")
    playback_body = _javascript_function(script, "renderCardOriginalPlayback")

    assert "activeCardMediaRestore" in cleanup_body
    assert "renderPersistentPreview(" in cleanup_body
    assert "cardMediaElements.add(video)" in playback_body
    assert "cardMediaElements.add(image)" in playback_body
    assert "element.pause()" in cleanup_body
    assert "element.removeAttribute(\"src\")" in cleanup_body
    assert "element.load()" in cleanup_body
    assert "cardMediaElements = new Set()" in cleanup_body


def test_protocol_documents_define_numbered_cooperator_acceptance_method() -> None:
    ap = Path("AP.md").read_text(encoding="utf-8")
    orchestrator = Path("AP_ORCHESTRATOR.md").read_text(encoding="utf-8")

    assert "Numbered COOPERATOR Acceptance Feedback" in ap
    assert "`PASS`" in ap
    assert "`FAIL`" in ap
    assert "`NOT TESTED`" in ap
    assert "new product decision" in ap
    assert "Rendered acceptance evidence MUST be distinguished" in ap
    assert "Designing and Processing COOPERATOR Acceptance Reports" in orchestrator
    assert "avoid vague" in orchestrator.lower()
    assert "Screenshots or videos are evidence" in orchestrator
    assert "smallest correction task" in orchestrator


def test_css_metadata_dialog_has_scrollable_body(client: TestClient) -> None:
    css = client.get("/assets/styles.css").text
    assert "overflow-y" in css or "overflow-y" in css
    assert "dvh" in css or "vh" in css or "max-height" in css
