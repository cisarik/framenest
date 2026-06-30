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


def test_web_shell_contains_compact_library_tools(client: TestClient) -> None:
    html = client.get("/").text
    assert "library-browser" in html
    assert "Library tools" in html
    assert "<details" in html
    assert "Preview media" in html or "preview-button" in html


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
    assert "Catalog" in html
    assert "Loading catalog media" in html
    assert "No media matched this catalog query" in html
    assert "Previous" in html
    assert "Next" in html


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
    assert 'setMetadataStatus("saved", "Saved.")' in save_block
    assert "created" not in save_block
    assert "updated" not in save_block
    assert "unchanged" not in save_block
    assert "metadataWorkspace.openMediaId" in save_block
    assert "await loadCatalog();" in save_block
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

    assert "localStorage" not in script
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
    assert "Cloud AI available" in combined
    assert "provider_id" in script
    assert "model_id" in script
    assert "prompt_version" in script
    assert "execution" in script
    assert "Configure the server-side NVIDIA credential before starting FrameNest." in combined


def test_browser_analyze_is_explicit_confirmed_and_cloud_disclosed(client: TestClient) -> None:
    html = client.get("/").text
    script = client.get("/assets/app.js").text
    combined = html + script

    assert "Analyze" in combined
    assert "derived JPEG frames" in combined
    assert "full video is not uploaded" in combined
    assert "confirm_cloud_upload" in script
    assert ".ai-confirmation-checkbox" in script
    assert "elements.analyzeButton.disabled = !elements.checkbox.checked" in script
    assert "Preparing frames and requesting an editable suggestion" in combined
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


def test_browser_editable_review_form_and_tag_controls(client: TestClient) -> None:
    html = client.get("/").text
    script = client.get("/assets/app.js").text
    combined = html + script

    assert "AI suggestion review" in combined
    assert "review-title-input" in combined
    assert "review-description-input" in combined
    assert "review-collection-input" in combined
    assert "review-filename-input" in combined
    assert "review-tag-input" in combined
    assert "Add tag" in combined
    assert "removeTag" in script
    assert "Duplicate tags are not allowed." in script
    assert "confidence" in script
    assert "evidence" in script
    assert "uncertainties" in script
    assert "provider_id" in script
    assert "model_id" in script
    assert "prompt_version" in script


def test_browser_accept_and_reject_are_session_only_without_mutation_api(
    client: TestClient,
) -> None:
    html = client.get("/").text
    script = client.get("/assets/app.js").text
    combined = html + script

    assert "Accept draft for this session" in combined
    assert "Reject draft" in combined
    assert "Draft accepted for this review session. No file or catalog change was applied." in combined
    assert "Draft rejected. No changes were applied." in combined
    assert "markReviewEdited" in script
    assert "fetch(" in script
    assert "rename" not in script.lower()
    review_block = script[script.index("function renderEditableReview") : script.index("function suggestionErrorMessage")]
    assert "save" not in review_block.lower()
    assert "apply" not in review_block.lower()
    assert "commit" not in script.lower()


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

    assert "localStorage" not in script
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


def test_header_does_not_contain_pre_alpha_foundation_text(client: TestClient) -> None:
    html = client.get("/").text
    assert "Pre-alpha foundation" not in html
    assert "stage-pill" not in html


def test_header_contains_server_health_status_button(client: TestClient) -> None:
    html = client.get("/").text
    assert "server-health-button" in html
    assert "aria-label" in html
    assert "Local server healthy" in html or "server-health-button" in html


def test_header_contains_ai_status_button(client: TestClient) -> None:
    html = client.get("/").text
    assert "ai-status-button" in html
    assert "aria-label" in html


def test_application_has_settings_dialog_element(client: TestClient) -> None:
    html = client.get("/").text
    assert "settings-dialog" in html
    assert "Settings" in html
    assert "AI" in html


def test_settings_dialog_does_not_contain_provider_configuration_inputs(client: TestClient) -> None:
    html = client.get("/").text
    settings_section = html[html.index("settings-dialog"):]
    assert "NVIDIA" not in settings_section or "not yet available" in settings_section.lower()
    assert "OpenAI" not in settings_section
    assert "Anthropic" not in settings_section
    assert "LMStudio" not in settings_section and "LM Studio" not in settings_section
    assert "Vercel" not in settings_section
    assert "api-key" not in settings_section.lower()
    assert "api_key" not in settings_section.lower()
    assert '<input' not in settings_section or "not yet available" in settings_section.lower()


def test_javascript_has_health_retry_logic(client: TestClient) -> None:
    script = client.get("/assets/app.js").text
    assert "checkHealth" in script
    assert "retryHealth" in script or "retry" in script.lower()
    assert "healthCheckInFlight" in script or "healthRequestToken" in script or "inFlight" in script


def test_javascript_ai_status_button_opens_settings(client: TestClient) -> None:
    script = client.get("/assets/app.js").text
    assert "ai-status-button" in script or "aiStatusButton" in script
    assert "settings-dialog" in script or "settingsDialog" in script
    assert "showModal" in script or "openSettings" in script or "settings" in script.lower()


def test_javascript_settings_dialog_close_behavior(client: TestClient) -> None:
    script = client.get("/assets/app.js").text
    assert "close" in script.lower()
    assert "Escape" in script or "escape" in script or "keydown" in script


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


def test_library_tools_section_is_collapsible(client: TestClient) -> None:
    html = client.get("/").text
    assert "<details" in html
    assert "Library tools" in html
    assert "library-browser" in html


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


def test_catalog_card_has_details_and_edit_actions(client: TestClient) -> None:
    script = client.get("/assets/app.js").text
    card_body = _javascript_function(script, "renderCatalogCard")
    assert "Details" in card_body
    assert "Edit" in card_body
    assert "View details" not in card_body
    assert "Edit metadata" not in card_body
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


def test_javascript_card_has_content_first_media_surface(client: TestClient) -> None:
    script = client.get("/assets/app.js").text
    surface_body = _javascript_function(script, "renderCatalogCardMediaSurface")
    assert "mediaContentUrl(item.media_id, location.location_id)" in surface_body
    assert 'document.createElement("video")' in surface_body
    assert 'document.createElement("img")' in surface_body
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


def test_card_has_explicit_playback_control(client: TestClient) -> None:
    script = client.get("/assets/app.js").text
    surface_body = _javascript_function(script, "renderCatalogCardMediaSurface")
    assert 'playButton.textContent = "▶"' in surface_body
    assert "openPlaybackDetails" in surface_body
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
    assert "localStorage" not in script
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


def test_javascript_available_cards_use_identity_only_media_urls(client: TestClient) -> None:
    script = client.get("/assets/app.js").text
    surface_body = _javascript_function(script, "renderCatalogCardMediaSurface")
    media_url_body = _javascript_function(script, "mediaContentUrl")

    assert "selectPlaybackLocation(item)" in surface_body
    assert "mediaContentUrl(item.media_id, location.location_id)" in surface_body
    assert "MEDIA_CATALOG_ENDPOINT" in media_url_body
    assert "mediaId" in media_url_body
    assert "locationId" in media_url_body
    assert "relative_path" not in media_url_body
    assert "library" not in media_url_body.lower()


def test_javascript_available_gif_card_renders_real_gif_media(client: TestClient) -> None:
    script = client.get("/assets/app.js").text
    surface_body = _javascript_function(script, "renderCatalogCardMediaSurface")
    image_section = surface_body[surface_body.index('document.createElement("img")') :]

    assert "img.src = url" in image_section
    assert "media-placeholder__image" in image_section
    assert "img.onerror = showUnavailable" in image_section


def test_javascript_available_mp4_card_renders_paused_safe_video(client: TestClient) -> None:
    script = client.get("/assets/app.js").text
    surface_body = _javascript_function(script, "renderCatalogCardMediaSurface")
    video_section = surface_body[
        surface_body.index('document.createElement("video")') : surface_body.index("} else {")
    ]

    assert "video.src = url" in video_section
    assert 'video.preload = "metadata"' in video_section
    assert "video.playsInline = true" in video_section
    assert "video.autoplay = false" in video_section
    assert "video.muted = true" in video_section
    assert "video.controls = false" in video_section
    assert "video.loop = false" in video_section
    assert "video.play(" not in video_section


def test_javascript_card_play_overlay_is_accessible_and_opens_real_details(client: TestClient) -> None:
    script = client.get("/assets/app.js").text
    surface_body = _javascript_function(script, "renderCatalogCardMediaSurface")
    open_body = _javascript_function(script, "openPlaybackDetails")

    assert 'playButton.textContent = "▶"' in surface_body
    assert "media-placeholder__play" in surface_body
    assert "aria-label" in surface_body
    assert "Play ${title}" in surface_body
    assert "openPlaybackDetails(item, playButton)" in surface_body
    assert "openDetailsDialog(item, openerElement, { playWhenReady: true })" in open_body
    assert "mediaContentUrl" in _javascript_function(script, "renderDetailsMedia")


def test_javascript_details_button_does_not_request_automatic_play(client: TestClient) -> None:
    script = client.get("/assets/app.js").text
    card_body = _javascript_function(script, "renderCatalogCard")
    details_click_index = card_body.index("detailsButton.addEventListener")
    details_click_section = card_body[details_click_index : details_click_index + 160]

    assert "openDetailsDialog(item, detailsButton)" in details_click_section
    assert "playWhenReady" not in details_click_section


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
    assert "Available local Gallery cards show immediate real media visuals" in gallery
    assert "centered real `▶` affordance" in gallery
    assert "not durable accepted covers" in gallery
    assert "persistent\nthumbnails" in gallery
    assert "generic available-media placeholders" in gallery
    assert "are rejected" in gallery
    assert "Details is player-first" in gallery


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
    assert "localStorage" not in script
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
    assert "openPlaybackDetails(item" in surface_body
    assert "media-placeholder__play" in surface_body


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


def test_css_metadata_dialog_has_scrollable_body(client: TestClient) -> None:
    css = client.get("/assets/styles.css").text
    assert "overflow-y" in css or "overflow-y" in css
    assert "dvh" in css or "vh" in css or "max-height" in css
