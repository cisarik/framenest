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


def test_root_serves_framenest_pre_alpha_application_document(client: TestClient) -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")

    html = response.text
    parsed = _parse_document(html)
    assert "FrameNest" in html
    assert "pre-alpha" in html.lower()
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


def test_javascript_loads_library_list_without_auto_scanning(client: TestClient) -> None:
    script = client.get("/assets/app.js").text
    assert 'const LIBRARIES_ENDPOINT = "/api/libraries";' in script
    assert "fetch(LIBRARIES_ENDPOINT" in script
    assert "loadLibraries();" in script
    assert "scan-preview" in script
    assert "addEventListener(\"click\"" in script
    assert "function handlePreviewClick" in script
    assert "handlePreviewClick(library, card);" in script


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
    assert "No media catalog record was created" in combined
    assert "No AI provider was contacted" in combined
    assert "No cloud transmission occurred" in combined


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


def test_browser_presents_no_ai_controls_or_fake_cancel(client: TestClient) -> None:
    html = client.get("/").text
    script = client.get("/assets/app.js").text
    combined = html + script

    assert "Cancel analysis" not in combined
    assert "Provider selection" not in combined
    assert "Model selection" not in combined
    assert ">Analyze<" not in combined


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
