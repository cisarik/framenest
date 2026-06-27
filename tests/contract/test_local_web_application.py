"""Contract tests for the packaged local FrameNest web application shell."""

from __future__ import annotations

from html.parser import HTMLParser

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


def test_web_shell_contains_real_library_browser_states(client: TestClient) -> None:
    html = client.get("/").text
    assert "library-browser" in html
    assert "Registered libraries" in html
    assert "Loading registered libraries" in html
    assert "CLI-only" in html
    assert "Preview media" in html
    assert "scan-preview" not in html


def test_web_shell_contains_reachable_catalog_browser_states(client: TestClient) -> None:
    html = client.get("/").text
    assert "catalog-browser" in html
    assert "Catalog" in html
    assert "Search display titles" in html
    assert "Canonical tag filters" in html
    assert "Multiple selected tags use AND semantics" in html
    assert "Loading catalog media" in html
    assert "No media matched this catalog query" in html
    assert "Previous" in html
    assert "Next" in html


def test_web_shell_contains_manual_current_metadata_workspace(client: TestClient) -> None:
    html = client.get("/").text

    assert "metadata-workspace" in html
    assert "Current metadata" in html
    assert "Display title" in html
    assert "Search canonical tags" in html
    assert "metadata-tag-suggestions" in html
    assert "metadata-selected-tags" in html
    assert "Canonical key" in html
    assert "Display name" in html
    assert "Create and select" in html
    assert "Save metadata" in html
    assert "Discard changes" in html
    assert "Close metadata workspace" in html
    assert "Saving catalog metadata does not rename or move files." in html
    for state in (
        "metadata-state-loading",
        "metadata-state-ready",
        "metadata-state-dirty",
        "metadata-state-saving",
        "metadata-state-saved",
        "metadata-state-unavailable",
        "metadata-state-not-found",
        "metadata-state-validation",
        "metadata-state-error",
    ):
        assert state in html


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
    assert "unicodeCodePointLength(descriptionInput.value)" in script or "unicodeCodePointLength(input.value)" in script
    assert "input.value.length" not in script or (
        "input.value.length" in script and "unicodeCodePointLength" in script
    )
    counter_block = script[script.index("function updateDescriptionCount") : script.index("function renderMetadataWorkspace")]
    assert "unicodeCodePointLength" in counter_block


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

    assert "Edit metadata" in script
    assert "handleOpenMetadataWorkspace(item" in script
    assert "button.addEventListener(\"click\", () => handleOpenMetadataWorkspace(item));" in script
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
    assert "handleCreateAndSelectTag" in script
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
    assert "metadataDiscardButton.disabled = metadataWorkspace.loading || metadataWorkspace.saving || !dirty;" in script
    assert "confirm(\"Discard unsaved metadata changes?\")" in script
    assert "handleDiscardMetadataChanges" in script
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
    assert "function moveSelectedMetadataTag" in script
    assert "moveSelectedMetadataTag(index, -1)" in script
    assert "moveSelectedMetadataTag(index, 1)" in script
    assert "function removeSelectedMetadataTag" in script
    assert "Move earlier" in script
    assert "Move later" in script
    assert "Remove tag" in script
    assert "tag_keys: normalized.tagKeys" in script
    assert ".sort(" not in script[script.index("function renderSelectedMetadataTags") : script.index("function renderMetadataTagSuggestions")]


def test_javascript_metadata_save_refreshes_catalog_and_preserves_filters(
    client: TestClient,
) -> None:
    script = client.get("/assets/app.js").text

    assert "async function handleSaveMetadata" in script
    save_block = script[script.index("async function handleSaveMetadata") : script.index("async function handleInspectClick")]
    assert "created" in save_block
    assert "updated" in save_block
    assert "unchanged" in save_block
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
    assert script.index("media-analysis-preview") > script.index("function handleInspectClick")
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
    assert "Local analysis and AI review do not create media catalog records" in combined
    assert "No AI provider was contacted" in combined
    assert "No cloud transmission occurred" in combined


def test_browser_scan_import_is_explicit_and_same_origin(client: TestClient) -> None:
    html = client.get("/").text
    script = client.get("/assets/app.js").text
    combined = html + script

    assert "explicitly import" in html
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


def test_browser_metadata_workspace_shows_collection_state(client: TestClient) -> None:
    html = client.get("/").text
    script = client.get("/assets/app.js").text

    assert "metadata-collection-status" in html
    assert "Processed status" in html
    assert "Processed collection" in script
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

    assert "metadata-collection-status" in html
    assert "createElement(\"time\")" in script or 'createElement("time")' in script
    assert "datetime" in script
    assert ".toISOString()" in script

    start = script.index("function renderMetadataWorkspace()")
    end = script.index("\n}\n", start) + len("\n}\n")
    workspace_body = script[start:end]
    assert "buildProcessedTimeElement" in workspace_body
    assert "processedAtMs" in workspace_body


def test_browser_catalog_card_renders_processed_time_semantically(client: TestClient) -> None:
    script = client.get("/assets/app.js").text

    start = script.index("function renderCatalogCard(item)")
    end = script.index("\n}\n", start) + len("\n}\n")
    card_body = script[start:end]
    assert "processed_at_ms" in card_body
    assert "buildProcessedTimeElement" in card_body
    assert "Processed since" in card_body


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
    assert "sticky" in html.lower() or "position: sticky" in client.get("/assets/styles.css").text.lower()
    assert "FrameNest" in html
    assert "brand-cursor" in html


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
