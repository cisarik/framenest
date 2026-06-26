"use strict";

const HEALTH_ENDPOINT = "/health";
const LIBRARIES_ENDPOINT = "/api/libraries";
const MEDIA_CATALOG_ENDPOINT = "/api/media";
const MEDIA_METADATA_ENDPOINT_PREFIX = "/api/media";
const CANONICAL_TAGS_ENDPOINT = "/api/canonical-tags";
const AI_CAPABILITY_ENDPOINT = "/api/ai/media-suggestion-capability";
const MEDIA_IMPORTS_ENDPOINT = "media-imports";
const CATALOG_PAGE_SIZE = 24;
const MAX_METADATA_TITLE_CODE_POINTS = 240;
const MAX_METADATA_TAGS = 32;
const TAG_KEY_PATTERN = /^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$/;
const MAX_REVIEW_TEXT = {
  title: 120,
  description: 600,
  collection: 40,
  tag: 40,
  filename: 180,
};

let analysisRequestToken = 0;
let suggestionRequestToken = 0;
let previewObjectUrls = [];
let catalogRequestToken = 0;
let metadataRequestToken = 0;
let canonicalTagDefinitions = [];
let canonicalTagsLoaded = false;
let metadataBeforeUnloadAttached = false;
let catalogState = {
  q: "",
  tagKeys: [],
  limit: CATALOG_PAGE_SIZE,
  offset: 0,
  total: 0,
};
let metadataWorkspace = {
  openMediaId: null,
  openItem: null,
  loading: false,
  saving: false,
  unavailable: false,
  notFound: false,
  statusOverride: null,
  baseline: { displayTitle: null, tagKeys: [] },
  current: { displayTitle: "", tagKeys: [] },
};
let aiCapability = {
  available: false,
  provider_id: "",
  model_id: "",
  prompt_version: "",
  execution: "cloud",
  requires_explicit_confirmation: true,
};

const statusContainer = document.querySelector("#server-status");
const statusText = document.querySelector("#server-status-text");
const statusDetail = document.querySelector("#server-status-detail");
const aiStatus = document.querySelector("#ai-status");
const aiStatusText = document.querySelector("#ai-status-text");
const aiStatusDetail = document.querySelector("#ai-status-detail");
const libraryList = document.querySelector("#library-list");
const libraryStateLoading = document.querySelector("#library-state-loading");
const libraryStateEmpty = document.querySelector("#library-state-empty");
const libraryStateUnavailable = document.querySelector("#library-state-unavailable");
const libraryStateError = document.querySelector("#library-state-error");
const libraryCardTemplate = document.querySelector("#library-card-template");
const catalogSearchForm = document.querySelector("#catalog-search-form");
const catalogSearchInput = document.querySelector("#catalog-search-input");
const catalogClearButton = document.querySelector("#catalog-clear-button");
const catalogTagFilters = document.querySelector("#catalog-tag-filters");
const catalogActiveFilters = document.querySelector("#catalog-active-filters");
const catalogTagsState = document.querySelector("#catalog-tags-state");
const catalogStateLoading = document.querySelector("#catalog-state-loading");
const catalogStateEmpty = document.querySelector("#catalog-state-empty");
const catalogStateUnavailable = document.querySelector("#catalog-state-unavailable");
const catalogStateError = document.querySelector("#catalog-state-error");
const catalogResults = document.querySelector("#catalog-results");
const catalogPrevButton = document.querySelector("#catalog-prev-button");
const catalogNextButton = document.querySelector("#catalog-next-button");
const catalogPageSummary = document.querySelector("#catalog-page-summary");
const metadataWorkspaceElement = document.querySelector("#metadata-workspace");
const metadataWorkspaceTitle = document.querySelector("#metadata-workspace-title");
const metadataWorkspaceContext = document.querySelector("#metadata-workspace-context");
const metadataCloseButton = document.querySelector("#metadata-close-button");
const metadataTitleInput = document.querySelector("#metadata-title-input");
const metadataTitleFallback = document.querySelector("#metadata-title-fallback");
const metadataValidationMessage = document.querySelector("#metadata-validation-message");
const metadataTagSearchInput = document.querySelector("#metadata-tag-search-input");
const metadataTagSuggestions = document.querySelector("#metadata-tag-suggestions");
const metadataSelectedTags = document.querySelector("#metadata-selected-tags");
const metadataSelectedCount = document.querySelector("#metadata-selected-count");
const metadataCreateTagForm = document.querySelector("#metadata-create-tag-form");
const metadataCreateKeyInput = document.querySelector("#metadata-create-key-input");
const metadataCreateNameInput = document.querySelector("#metadata-create-name-input");
const metadataCreateStatus = document.querySelector("#metadata-create-status");
const metadataSaveButton = document.querySelector("#metadata-save-button");
const metadataDiscardButton = document.querySelector("#metadata-discard-button");
const metadataStateNodes = {
  loading: document.querySelector("#metadata-state-loading"),
  ready: document.querySelector("#metadata-state-ready"),
  dirty: document.querySelector("#metadata-state-dirty"),
  saving: document.querySelector("#metadata-state-saving"),
  saved: document.querySelector("#metadata-state-saved"),
  unavailable: document.querySelector("#metadata-state-unavailable"),
  notFound: document.querySelector("#metadata-state-not-found"),
  validation: document.querySelector("#metadata-state-validation"),
  error: document.querySelector("#metadata-state-error"),
};

function setStatusClass(className) {
  statusContainer.classList.remove("status--loading", "status--healthy", "status--error");
  statusContainer.classList.add(className);
}

function setLoadingState() {
  setStatusClass("status--loading");
  statusText.textContent = "Checking local server...";
  statusDetail.textContent = "Waiting for the same-origin health response.";
}

function setHealthyState() {
  setStatusClass("status--healthy");
  statusText.textContent = "Local server healthy";
  statusDetail.textContent = "The FrameNest application process answered the health check.";
}

function setErrorState() {
  setStatusClass("status--error");
  statusText.textContent = "Health check unavailable";
  statusDetail.textContent =
    "The page loaded, but the local health endpoint did not return the expected response.";
}

async function checkHealth() {
  setLoadingState();
  try {
    const response = await fetch(HEALTH_ENDPOINT, {
      headers: { Accept: "application/json" },
      cache: "no-store",
    });
    if (!response.ok) {
      setErrorState();
      return;
    }
    const payload = await response.json();
    if (payload && payload.status === "ok") {
      setHealthyState();
      return;
    }
    setErrorState();
  } catch {
    setErrorState();
  }
}

function setAiStatusClass(className) {
  aiStatus.classList.remove("status--loading", "status--healthy", "status--error");
  aiStatus.classList.add(className);
}

function renderAiCapability(payload) {
  aiCapability = {
    available: payload && payload.available === true,
    provider_id: payload && payload.provider_id ? String(payload.provider_id) : "",
    model_id: payload && payload.model_id ? String(payload.model_id) : "",
    prompt_version: payload && payload.prompt_version ? String(payload.prompt_version) : "",
    execution: payload && payload.execution ? String(payload.execution) : "cloud",
    requires_explicit_confirmation: !payload || payload.requires_explicit_confirmation !== false,
  };
  if (aiCapability.available) {
    setAiStatusClass("status--healthy");
    aiStatusText.textContent = "Cloud AI available";
    aiStatusDetail.textContent =
      `${aiCapability.provider_id} / ${aiCapability.model_id}; prompt ${aiCapability.prompt_version}; ${aiCapability.execution}.`;
    return;
  }
  setAiStatusClass("status--error");
  aiStatusText.textContent = "AI unavailable";
  aiStatusDetail.textContent = "Configure the server-side NVIDIA credential before starting FrameNest.";
}

async function loadAiCapability() {
  setAiStatusClass("status--loading");
  aiStatusText.textContent = "Checking AI capability...";
  aiStatusDetail.textContent = "No provider request is made for capability discovery.";
  try {
    const response = await fetch(AI_CAPABILITY_ENDPOINT, {
      headers: { Accept: "application/json" },
      cache: "no-store",
    });
    if (!response.ok) {
      renderAiCapability({ available: false });
      return;
    }
    renderAiCapability(await response.json());
  } catch {
    renderAiCapability({ available: false });
  }
}

function showLibraryState(state) {
  libraryStateLoading.hidden = state !== "loading";
  libraryStateEmpty.hidden = state !== "empty";
  libraryStateUnavailable.hidden = state !== "unavailable";
  libraryStateError.hidden = state !== "error";
  libraryList.hidden = state !== "success";
}

function showCatalogState(state) {
  catalogStateLoading.hidden = state !== "loading";
  catalogStateEmpty.hidden = state !== "empty";
  catalogStateUnavailable.hidden = state !== "unavailable";
  catalogStateError.hidden = state !== "error";
  catalogResults.hidden = state !== "success";
}

function appendText(parent, value) {
  parent.appendChild(document.createTextNode(String(value)));
}

function metadataEndpoint(mediaId) {
  return `${MEDIA_METADATA_ENDPOINT_PREFIX}/${mediaId}/metadata`;
}

function hasControlCharacter(value) {
  return [...value].some((character) => {
    const codePoint = character.codePointAt(0);
    return (codePoint >= 0 && codePoint <= 31) || codePoint === 127;
  });
}

function semanticArraysEqual(left, right) {
  if (left.length !== right.length) {
    return false;
  }
  return left.every((value, index) => value === right[index]);
}

function normalizedMetadataFormState() {
  const rawTitle = metadataTitleInput.value;
  if (hasControlCharacter(rawTitle)) {
    return { error: "Display title must not contain NUL or control characters." };
  }
  if (rawTitle.length > MAX_METADATA_TITLE_CODE_POINTS) {
    return { error: "Display title must be 240 characters or fewer." };
  }
  if (rawTitle.trim() === "") {
    return { displayTitle: null, tagKeys: [...metadataWorkspace.current.tagKeys] };
  }
  if (rawTitle.trim() !== rawTitle) {
    return { error: "Non-empty display titles must not start or end with whitespace." };
  }
  return { displayTitle: rawTitle, tagKeys: [...metadataWorkspace.current.tagKeys] };
}

function metadataIsDirty() {
  const normalized = normalizedMetadataFormState();
  if (normalized.error) {
    return true;
  }
  return normalized.displayTitle !== metadataWorkspace.baseline.displayTitle
    || !semanticArraysEqual(normalized.tagKeys, metadataWorkspace.baseline.tagKeys);
}

function selectedTagDefinition(key) {
  return canonicalTagDefinitions.find((tag) => tag.key === key) || null;
}

function metadataDirtyForBeforeUnload() {
  return metadataWorkspace.openMediaId !== null && metadataIsDirty();
}

function metadataBeforeUnloadHandler(event) {
  if (!metadataDirtyForBeforeUnload()) {
    return;
  }
  event.preventDefault();
  event.returnValue = "";
}

function syncMetadataBeforeUnloadProtection() {
  const shouldAttach = metadataDirtyForBeforeUnload();
  if (shouldAttach && !metadataBeforeUnloadAttached) {
    window.addEventListener("beforeunload", metadataBeforeUnloadHandler);
    metadataBeforeUnloadAttached = true;
  }
  if (!shouldAttach && metadataBeforeUnloadAttached) {
    window.removeEventListener("beforeunload", metadataBeforeUnloadHandler);
    metadataBeforeUnloadAttached = false;
  }
}

function formatSize(sizeBytes) {
  if (sizeBytes < 1024) {
    return `${sizeBytes} B`;
  }
  if (sizeBytes < 1024 * 1024) {
    return `${(sizeBytes / 1024).toFixed(1)} KiB`;
  }
  return `${(sizeBytes / (1024 * 1024)).toFixed(1)} MiB`;
}

function formatDuration(durationMs) {
  if (durationMs === null || durationMs === undefined) {
    return "Unknown";
  }
  const totalSeconds = Math.floor(durationMs / 1000);
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = totalSeconds % 60;
  const millis = durationMs % 1000;
  if (hours > 0) {
    return `${hours}:${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}.${String(millis).padStart(3, "0")}`;
  }
  return `${minutes}:${String(seconds).padStart(2, "0")}.${String(millis).padStart(3, "0")}`;
}

function formatTimestamp(timestampMs) {
  return `${formatDuration(timestampMs)} (${timestampMs} ms)`;
}

function addSummaryValue(summaryList, label, value) {
  const wrapper = document.createElement("div");
  const term = document.createElement("dt");
  const detail = document.createElement("dd");
  term.textContent = label;
  detail.textContent = value;
  wrapper.append(term, detail);
  summaryList.appendChild(wrapper);
}

function setInspectActionsDisabled(disabled) {
  document.querySelectorAll(".inspect-button").forEach((button) => {
    button.disabled = disabled;
  });
}

function setAnalyzeActionsDisabled(disabled) {
  document.querySelectorAll(".analyze-button").forEach((button) => {
    button.disabled = disabled || button.dataset.confirmed !== "true";
  });
}

function revokePreviewObjectUrls() {
  previewObjectUrls.forEach((url) => {
    URL.revokeObjectURL(url);
  });
  previewObjectUrls = [];
}

function decodeBase64Png(payloadBase64) {
  const binary = atob(payloadBase64);
  const bytes = new Uint8Array(binary.length);
  for (let index = 0; index < binary.length; index += 1) {
    bytes[index] = binary.charCodeAt(index);
  }
  return new Blob([bytes], { type: "image/png" });
}

function previewElements(card) {
  return {
    preview: card.querySelector(".local-preview"),
    path: card.querySelector(".local-preview-path"),
    kind: card.querySelector(".local-preview-kind"),
    status: card.querySelector(".local-preview-status"),
    metadata: card.querySelector(".analysis-metadata"),
    warnings: card.querySelector(".analysis-warnings"),
    frames: card.querySelector(".representative-frames"),
  };
}

function aiElements(card) {
  return {
    panel: card.querySelector(".ai-panel"),
    capability: card.querySelector(".ai-capability"),
    provider: card.querySelector(".ai-provider"),
    model: card.querySelector(".ai-model"),
    prompt: card.querySelector(".ai-prompt"),
    execution: card.querySelector(".ai-execution"),
    checkbox: card.querySelector(".ai-confirmation-checkbox"),
    analyzeButton: card.querySelector(".analyze-button"),
    status: card.querySelector(".ai-status-message"),
    review: card.querySelector(".ai-review"),
    reviewStatus: card.querySelector(".review-status"),
    acceptedTemplate: card.querySelector(".accepted-message-template"),
    rejectedTemplate: card.querySelector(".rejected-message-template"),
  };
}

function setLocalPreviewState(card, state, message) {
  const elements = previewElements(card);
  elements.preview.hidden = false;
  elements.preview.dataset.state = state;
  elements.status.textContent = message;
}

function resetAiReview(card) {
  const elements = aiElements(card);
  elements.panel.hidden = true;
  elements.panel.dataset.state = "idle";
  elements.capability.textContent = "";
  elements.provider.textContent = "";
  elements.model.textContent = "";
  elements.prompt.textContent = "";
  elements.execution.textContent = "";
  elements.checkbox.checked = false;
  elements.analyzeButton.dataset.confirmed = "false";
  elements.analyzeButton.disabled = true;
  elements.status.textContent = "";
  elements.review.replaceChildren();
  elements.review.hidden = true;
  elements.reviewStatus.textContent = "";
}

function resetLocalPreview(card) {
  revokePreviewObjectUrls();
  resetAiReview(card);
  const elements = previewElements(card);
  elements.preview.hidden = true;
  elements.preview.dataset.state = "idle";
  elements.path.textContent = "";
  elements.kind.textContent = "";
  elements.status.textContent = "Local preview has not been requested.";
  elements.metadata.replaceChildren();
  elements.metadata.hidden = true;
  elements.warnings.replaceChildren();
  elements.warnings.hidden = true;
  elements.frames.replaceChildren();
  elements.frames.hidden = true;
}

function addMetadataValue(metadataList, label, value) {
  const wrapper = document.createElement("div");
  const term = document.createElement("dt");
  const detail = document.createElement("dd");
  term.textContent = label;
  detail.textContent = value;
  wrapper.append(term, detail);
  metadataList.appendChild(wrapper);
}

function renderUnavailablePreview(card) {
  setLocalPreviewState(card, "unavailable", "Local media analysis is not available.");
}

function renderInvalidCandidatePreview(card) {
  setLocalPreviewState(card, "invalid", "Invalid media relative path.");
}

function renderGenericPreviewError(card) {
  setLocalPreviewState(card, "error", "Local media analysis failed.");
}

function renderAiPanelUnavailable(card) {
  const elements = aiElements(card);
  elements.panel.hidden = false;
  elements.panel.dataset.state = "unavailable";
  elements.capability.textContent = "AI unavailable";
  elements.provider.textContent = aiCapability.provider_id || "nvidia-nim";
  elements.model.textContent = aiCapability.model_id || "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning";
  elements.prompt.textContent = aiCapability.prompt_version || "framenest-media-suggestion-v2";
  elements.execution.textContent = aiCapability.execution || "cloud";
  elements.status.textContent = "Configure the server-side NVIDIA credential before starting FrameNest.";
  elements.checkbox.checked = false;
  elements.analyzeButton.dataset.confirmed = "false";
  elements.analyzeButton.disabled = true;
}

function renderAiPanelReady(card, payload) {
  const elements = aiElements(card);
  elements.panel.hidden = false;
  elements.panel.dataset.state = "ready";
  elements.capability.textContent = "Cloud AI available";
  elements.provider.textContent = aiCapability.provider_id;
  elements.model.textContent = aiCapability.model_id;
  elements.prompt.textContent = aiCapability.prompt_version;
  elements.execution.textContent = aiCapability.execution;
  elements.status.textContent =
    "Cloud analysis is available for this inspected candidate. The full video is not uploaded.";
  elements.checkbox.checked = false;
  elements.analyzeButton.dataset.confirmed = "false";
  elements.analyzeButton.disabled = true;
  elements.analyzeButton.dataset.libraryId = payload.library_id;
  elements.analyzeButton.dataset.relativePath = payload.relative_path;
}

function updateAnalyzeButton(card) {
  const elements = aiElements(card);
  elements.analyzeButton.dataset.confirmed = elements.checkbox.checked ? "true" : "false";
  elements.analyzeButton.disabled = !elements.checkbox.checked || elements.panel.dataset.state === "pending";
}

function renderAnalysisSuccess(card, payload) {
  if (!payload.representative_frames || payload.representative_frames.length === 0) {
    renderGenericPreviewError(card);
    return;
  }
  revokePreviewObjectUrls();
  resetAiReview(card);
  const elements = previewElements(card);
  const metadata = payload.technical_metadata;
  elements.preview.hidden = false;
  elements.preview.dataset.state = "success";
  elements.path.textContent = payload.relative_path;
  elements.kind.textContent = payload.candidate_kind;
  elements.status.textContent = "Local analysis results are ephemeral and ready for inspection.";

  elements.metadata.replaceChildren();
  addMetadataValue(elements.metadata, "Duration", formatDuration(metadata.duration_ms));
  addMetadataValue(elements.metadata, "Dimensions", `${metadata.width} x ${metadata.height}`);
  addMetadataValue(elements.metadata, "Video codec", metadata.video_codec);
  addMetadataValue(elements.metadata, "Container", metadata.container_formats.join(", "));
  addMetadataValue(elements.metadata, "Audio", metadata.has_audio ? "Present" : "Not detected");
  addMetadataValue(elements.metadata, "Frames", `${payload.representative_frames.length} of ${payload.requested_frame_count}`);
  elements.metadata.hidden = false;

  elements.warnings.replaceChildren();
  if (payload.warnings.length > 0) {
    payload.warnings.forEach((warning) => {
      const item = document.createElement("p");
      item.textContent = warning;
      elements.warnings.appendChild(item);
    });
    elements.warnings.hidden = false;
  } else {
    elements.warnings.hidden = true;
  }

  elements.frames.replaceChildren();
  payload.representative_frames.forEach((frame) => {
    const blob = decodeBase64Png(frame.payload_base64);
    const objectUrl = URL.createObjectURL(blob);
    previewObjectUrls.push(objectUrl);
    const figure = document.createElement("figure");
    figure.className = "representative-frame";
    const image = document.createElement("img");
    image.src = objectUrl;
    image.alt = `Representative frame at ${formatTimestamp(frame.timestamp_ms)} for ${payload.relative_path}`;
    const caption = document.createElement("figcaption");
    caption.textContent = `Timestamp ${formatTimestamp(frame.timestamp_ms)}`;
    figure.append(image, caption);
    elements.frames.appendChild(figure);
  });
  elements.frames.hidden = false;

  if (aiCapability.available) {
    renderAiPanelReady(card, payload);
  } else {
    renderAiPanelUnavailable(card);
  }
}

function renderScanResult(card, payload) {
  const summaryList = card.querySelector(".scan-summary");
  const candidates = card.querySelector(".scan-candidates");
  const status = card.querySelector(".scan-status");
  resetLocalPreview(card);
  summaryList.replaceChildren();
  candidates.replaceChildren();

  addSummaryValue(summaryList, "Entries", payload.summary.entries_seen);
  addSummaryValue(summaryList, "Candidates", payload.summary.candidate_files_seen);
  addSummaryValue(summaryList, "Bytes", formatSize(payload.summary.candidate_bytes_seen));
  addSummaryValue(summaryList, "Hidden skipped", payload.summary.skipped_hidden_entries);
  addSummaryValue(summaryList, "Symlinks skipped", payload.summary.skipped_symlink_entries);
  addSummaryValue(summaryList, "Inaccessible", payload.summary.inaccessible_entries);
  addSummaryValue(summaryList, "Entry limit", payload.summary.truncated ? "Reached" : "Not reached");
  addSummaryValue(
    summaryList,
    "Candidate limit",
    payload.summary.candidates_truncated ? "Reached" : "Not reached",
  );

  if (payload.candidates.length === 0) {
    const empty = document.createElement("p");
    empty.className = "scan-status";
    empty.textContent = "No media candidates were found in this read-only preview.";
    candidates.appendChild(empty);
  } else {
    payload.candidates.forEach((candidate) => {
      const row = document.createElement("div");
      row.className = "candidate-row";
      const path = document.createElement("span");
      path.className = "candidate-path";
      path.textContent = candidate.relative_path;
      const kind = document.createElement("span");
      kind.className = "candidate-pill";
      appendText(kind, candidate.kind);
      const detail = document.createElement("span");
      detail.className = "candidate-pill";
      appendText(detail, `${candidate.extension} ${formatSize(candidate.size_bytes)}`);
      const inspect = document.createElement("button");
      inspect.className = "inspect-button";
      inspect.type = "button";
      inspect.textContent = "Inspect locally";
      inspect.addEventListener("click", () => {
        handleInspectClick(payload.library_id, candidate, card);
      });
      const importButton = document.createElement("button");
      importButton.className = "import-button";
      importButton.type = "button";
      importButton.textContent = "Import";
      const importStatus = document.createElement("span");
      importStatus.className = "import-status";
      importStatus.textContent = "Not imported";
      importButton.addEventListener("click", () => {
        handleImportClick(payload.library_id, candidate, importButton, importStatus);
      });
      row.append(path, kind, detail, importButton, inspect, importStatus);
      candidates.appendChild(row);
    });
  }

  summaryList.hidden = false;
  candidates.hidden = false;
  status.textContent = "Read-only scan preview complete. Candidates are not persisted catalog media.";
}

function buildCatalogQueryParams() {
  const params = new URLSearchParams();
  const trimmed = catalogState.q.trim();
  if (trimmed) {
    params.set("q", trimmed);
  }
  catalogState.tagKeys.forEach((key) => {
    params.append("tag", key);
  });
  params.set("limit", String(catalogState.limit));
  params.set("offset", String(catalogState.offset));
  return params;
}

function deriveCatalogFallbackTitle(item) {
  if (!item.locations || item.locations.length === 0) {
    return "Untitled media";
  }
  const firstPath = String(item.locations[0].relative_path || "");
  const parts = firstPath.split("/");
  return parts[parts.length - 1] || "Untitled media";
}

function formatCatalogKind(kind) {
  if (kind === "animated_image") {
    return "animated image";
  }
  return String(kind).replaceAll("_", " ");
}

function summarizeAvailability(locations) {
  if (!locations || locations.length === 0) {
    return "No known locations";
  }
  const counts = new Map();
  locations.forEach((location) => {
    const key = String(location.availability || "unknown");
    counts.set(key, (counts.get(key) || 0) + 1);
  });
  return [...counts.entries()]
    .map(([key, count]) => `${count} ${key}`)
    .join(", ");
}

function setCatalogPagination(page) {
  const start = page.total === 0 ? 0 : page.offset + 1;
  const end = Math.min(page.offset + page.limit, page.total);
  catalogPageSummary.textContent = page.total === 0
    ? "No catalog results."
    : `${start}-${end} of ${page.total}`;
  catalogPrevButton.disabled = page.offset <= 0;
  catalogNextButton.disabled = page.offset + page.limit >= page.total;
}

function renderCatalogCard(item) {
  const card = document.createElement("article");
  card.className = "catalog-card";
  if (metadataWorkspace.openMediaId === item.media_id) {
    card.classList.add("catalog-card--selected");
  }
  const header = document.createElement("div");
  header.className = "catalog-card__header";
  const titleGroup = document.createElement("div");
  const title = document.createElement("h3");
  title.textContent = item.display_title || deriveCatalogFallbackTitle(item);
  const subtitle = document.createElement("p");
  subtitle.textContent = item.display_title
    ? "Persisted display title"
    : "Fallback label from first deterministic relative location";
  titleGroup.append(title, subtitle);
  const kind = document.createElement("span");
  kind.className = "catalog-kind";
  kind.textContent = formatCatalogKind(item.media_kind);
  header.append(titleGroup, kind);

  const facts = document.createElement("dl");
  facts.className = "catalog-facts";
  addMetadataValue(facts, "Locations", String(item.locations.length));
  addMetadataValue(facts, "Availability", summarizeAvailability(item.locations));
  addMetadataValue(facts, "Media ID", item.media_id);

  const tags = document.createElement("div");
  tags.className = "catalog-tags";
  if (item.tags.length === 0) {
    const emptyTag = document.createElement("span");
    emptyTag.className = "catalog-tag catalog-tag--empty";
    emptyTag.textContent = "No canonical tags";
    tags.appendChild(emptyTag);
  } else {
    item.tags.forEach((tag) => {
      const chip = document.createElement("span");
      chip.className = "catalog-tag";
      chip.textContent = `${tag.display_name} (${tag.position})`;
      tags.appendChild(chip);
    });
  }

  const locations = document.createElement("ul");
  locations.className = "catalog-locations";
  item.locations.forEach((location) => {
    const row = document.createElement("li");
    const path = document.createElement("span");
    path.className = "catalog-location-path";
    path.textContent = location.relative_path;
    const availability = document.createElement("span");
    availability.className = "catalog-location-availability";
    availability.textContent = location.availability;
    row.append(path, availability);
    locations.appendChild(row);
  });
  const actions = document.createElement("div");
  actions.className = "catalog-card__actions";
  const button = document.createElement("button");
  button.className = "catalog-edit-button";
  button.type = "button";
  button.textContent = "Edit metadata";
  button.addEventListener("click", () => handleOpenMetadataWorkspace(item));
  actions.appendChild(button);
  card.append(header, facts, tags, locations, actions);
  return card;
}

function renderCatalogSuccess(page) {
  catalogResults.replaceChildren();
  catalogState.total = page.total;
  catalogState.offset = page.offset;
  catalogSearchInput.value = page.q || catalogState.q;
  renderActiveCatalogFilters(page.tag_keys || catalogState.tagKeys);
  setCatalogPagination(page);
  if (page.items.length === 0) {
    showCatalogState("empty");
    return;
  }
  page.items.forEach((item) => {
    catalogResults.appendChild(renderCatalogCard(item));
  });
  showCatalogState("success");
}

function renderActiveCatalogFilters(tagKeys) {
  catalogActiveFilters.replaceChildren();
  if (tagKeys.length === 0) {
    const empty = document.createElement("p");
    empty.textContent = "No active canonical tag filters.";
    catalogActiveFilters.appendChild(empty);
    return;
  }
  tagKeys.forEach((key) => {
    const chip = document.createElement("button");
    chip.type = "button";
    chip.className = "catalog-active-filter";
    chip.textContent = `Remove ${key}`;
    chip.addEventListener("click", () => {
      catalogState.tagKeys = catalogState.tagKeys.filter((activeKey) => activeKey !== key);
      catalogState.offset = 0;
      renderActiveCatalogFilters(catalogState.tagKeys);
      loadCatalog();
    });
    catalogActiveFilters.appendChild(chip);
  });
}

function renderCatalogTagFilters(tags) {
  canonicalTagDefinitions = tags;
  canonicalTagsLoaded = true;
  catalogTagFilters.replaceChildren();
  if (tags.length === 0) {
    catalogTagsState.textContent = "No canonical tag definitions exist yet.";
    return;
  }
  catalogTagsState.textContent = "Canonical tag filters loaded.";
  tags.forEach((tag) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "catalog-filter-chip";
    button.dataset.tagKey = tag.key;
    button.textContent = tag.display_name;
    button.addEventListener("click", () => {
      if (catalogState.tagKeys.includes(tag.key)) {
        return;
      }
      catalogState.tagKeys = [...catalogState.tagKeys, tag.key];
      catalogState.offset = 0;
      renderActiveCatalogFilters(catalogState.tagKeys);
      loadCatalog();
    });
    catalogTagFilters.appendChild(button);
  });
  if (metadataWorkspace.openMediaId !== null) {
    renderMetadataWorkspace();
  }
}

async function loadCatalogTags() {
  catalogTagsState.textContent = "Loading canonical tag filters...";
  try {
    const response = await fetch(CANONICAL_TAGS_ENDPOINT, {
      headers: { Accept: "application/json" },
      cache: "no-store",
    });
    const payload = await response.json();
    if (!response.ok) {
      catalogTagsState.textContent = "Canonical tag filters are unavailable.";
      return false;
    }
    renderCatalogTagFilters(payload.tags || []);
    return true;
  } catch {
    catalogTagsState.textContent = "Canonical tag filters could not be loaded.";
    return false;
  }
}

async function ensureCanonicalTags() {
  if (canonicalTagsLoaded) {
    return true;
  }
  return loadCatalogTags();
}

function setMetadataState(state) {
  Object.entries(metadataStateNodes).forEach(([key, node]) => {
    node.hidden = key !== state;
  });
}

function setMetadataStatus(state, message) {
  setMetadataState(state);
  metadataWorkspace.statusOverride = state;
  if (message && metadataStateNodes[state]) {
    metadataStateNodes[state].textContent = message;
  }
}

function describeCatalogItem(item) {
  const label = item.display_title || deriveCatalogFallbackTitle(item);
  const location = item.locations && item.locations.length > 0
    ? item.locations[0].relative_path
    : "No known relative location";
  return `${label}; ${formatCatalogKind(item.media_kind)}; ${location}; media ID ${item.media_id}`;
}

function confirmDiscardDirtyMetadata() {
  if (!metadataDirtyForBeforeUnload()) {
    return true;
  }
  return confirm("Discard unsaved metadata changes?");
}

function updateMetadataControls() {
  const normalized = normalizedMetadataFormState();
  const validation = normalized.error || "";
  const dirty = metadataIsDirty();
  metadataValidationMessage.textContent = validation;
  if (validation) {
    metadataStateNodes.validation.textContent = validation;
  } else if (metadataWorkspace.statusOverride !== "validation") {
    metadataStateNodes.validation.textContent = "Metadata validation failed.";
  }
  metadataSaveButton.disabled = metadataWorkspace.loading || metadataWorkspace.saving || !dirty || Boolean(validation);
  metadataDiscardButton.disabled = metadataWorkspace.loading || metadataWorkspace.saving || !dirty;
  syncMetadataBeforeUnloadProtection();
  if (metadataWorkspace.loading) {
    setMetadataState("loading");
  } else if (metadataWorkspace.saving) {
    setMetadataState("saving");
  } else if (metadataWorkspace.unavailable) {
    setMetadataState("unavailable");
  } else if (metadataWorkspace.notFound) {
    setMetadataState("notFound");
  } else if (validation) {
    setMetadataState("validation");
  } else if (metadataWorkspace.statusOverride === "validation") {
    setMetadataState("validation");
  } else if (metadataWorkspace.statusOverride === "error") {
    setMetadataState("error");
  } else if (dirty) {
    setMetadataState("dirty");
  } else if (metadataWorkspace.statusOverride === "saved") {
    setMetadataState("saved");
  } else {
    setMetadataState("ready");
  }
}

function renderSelectedMetadataTags() {
  metadataSelectedTags.replaceChildren();
  metadataSelectedCount.textContent = `${metadataWorkspace.current.tagKeys.length} of ${MAX_METADATA_TAGS} selected.`;
  if (metadataWorkspace.current.tagKeys.length === 0) {
    const empty = document.createElement("p");
    empty.className = "metadata-note";
    empty.textContent = "No canonical tags selected.";
    metadataSelectedTags.appendChild(empty);
    return;
  }
  metadataWorkspace.current.tagKeys.forEach((key, index) => {
    const definition = selectedTagDefinition(key);
    const chip = document.createElement("span");
    chip.className = "metadata-tag-chip";
    const label = document.createElement("span");
    label.textContent = definition ? definition.display_name : key;
    const stableKey = document.createElement("span");
    stableKey.className = "metadata-tag-key";
    stableKey.textContent = key;
    const earlier = document.createElement("button");
    earlier.type = "button";
    earlier.textContent = "Earlier";
    earlier.setAttribute("aria-label", `Move earlier ${definition ? definition.display_name : key}`);
    earlier.disabled = index === 0;
    earlier.addEventListener("click", () => moveSelectedMetadataTag(index, -1));
    const later = document.createElement("button");
    later.type = "button";
    later.textContent = "Later";
    later.setAttribute("aria-label", `Move later ${definition ? definition.display_name : key}`);
    later.disabled = index === metadataWorkspace.current.tagKeys.length - 1;
    later.addEventListener("click", () => moveSelectedMetadataTag(index, 1));
    const remove = document.createElement("button");
    remove.type = "button";
    remove.textContent = "Remove";
    remove.setAttribute("aria-label", `Remove tag ${definition ? definition.display_name : key}`);
    remove.addEventListener("click", () => removeSelectedMetadataTag(key));
    chip.append(label, stableKey, earlier, later, remove);
    metadataSelectedTags.appendChild(chip);
  });
}

function renderMetadataTagSuggestions() {
  metadataTagSuggestions.replaceChildren();
  const query = metadataTagSearchInput.value.trim().toLowerCase();
  const matches = canonicalTagDefinitions.filter((tag) => {
    if (!query) {
      return true;
    }
    return tag.key.toLowerCase().includes(query) || tag.display_name.toLowerCase().includes(query);
  });
  if (matches.length === 0) {
    const empty = document.createElement("p");
    empty.className = "metadata-note";
    empty.textContent = "No matching canonical tags.";
    metadataTagSuggestions.appendChild(empty);
    return;
  }
  matches.forEach((tag) => {
    const selected = metadataWorkspace.current.tagKeys.includes(tag.key);
    const button = document.createElement("button");
    button.type = "button";
    button.className = "metadata-tag-suggestion";
    button.textContent = selected ? `${tag.display_name} selected` : `${tag.display_name} (${tag.key})`;
    button.setAttribute("aria-disabled", selected ? "true" : "false");
    button.disabled = selected || metadataWorkspace.current.tagKeys.length >= MAX_METADATA_TAGS;
    button.addEventListener("click", () => selectMetadataTag(tag.key));
    metadataTagSuggestions.appendChild(button);
  });
}

function renderMetadataWorkspace() {
  if (metadataWorkspace.openMediaId === null) {
    metadataWorkspaceElement.hidden = true;
    syncMetadataBeforeUnloadProtection();
    return;
  }
  metadataWorkspaceElement.hidden = false;
  metadataWorkspaceContext.textContent = metadataWorkspace.openItem
    ? describeCatalogItem(metadataWorkspace.openItem)
    : `Media ID ${metadataWorkspace.openMediaId}`;
  metadataTitleInput.value = metadataWorkspace.current.displayTitle || "";
  metadataTitleFallback.textContent = metadataWorkspace.baseline.displayTitle === null && metadataWorkspace.openItem
    ? `Catalog fallback label: ${deriveCatalogFallbackTitle(metadataWorkspace.openItem)}. This is presentation-only and is not persisted as title truth.`
    : "Display title is persisted catalog metadata and remains separate from the physical filename.";
  renderSelectedMetadataTags();
  renderMetadataTagSuggestions();
  updateMetadataControls();
}

function applyMetadataPayloadToWorkspace(payload) {
  const tagKeys = (payload.tags || []).map((tag) => tag.key);
  metadataWorkspace.baseline = {
    displayTitle: payload.display_title === null ? null : payload.display_title,
    tagKeys,
  };
  metadataWorkspace.current = {
    displayTitle: payload.display_title === null ? "" : payload.display_title,
    tagKeys: [...tagKeys],
  };
}

async function handleOpenMetadataWorkspace(item) {
  if (!confirmDiscardDirtyMetadata()) {
    return;
  }
  const token = metadataRequestToken + 1;
  metadataRequestToken = token;
  metadataWorkspace = {
    openMediaId: item.media_id,
    openItem: item,
    loading: true,
    saving: false,
    unavailable: false,
    notFound: false,
    statusOverride: null,
    baseline: { displayTitle: null, tagKeys: [] },
    current: { displayTitle: "", tagKeys: [] },
  };
  metadataCreateStatus.textContent = "";
  renderMetadataWorkspace();
  metadataWorkspaceTitle.focus();
  const tagsReady = await ensureCanonicalTags();
  if (token !== metadataRequestToken) {
    return;
  }
  if (!tagsReady) {
    metadataWorkspace.loading = false;
    metadataWorkspace.unavailable = true;
    setMetadataStatus("unavailable", "Canonical tag definitions are unavailable.");
    updateMetadataControls();
    return;
  }
  try {
    const mediaId = item.media_id;
    const response = await fetch(metadataEndpoint(mediaId), {
      headers: { Accept: "application/json" },
      cache: "no-store",
    });
    const payload = await response.json();
    if (token !== metadataRequestToken) {
      return;
    }
    metadataWorkspace.loading = false;
    if (!response.ok) {
      const code = payload.error ? payload.error.code : "";
      if (code === "MEDIA_NOT_FOUND") {
        metadataWorkspace.notFound = true;
        setMetadataStatus("notFound", "The selected medium is no longer available.");
        loadCatalog();
      } else if (code === "CATALOG_UNAVAILABLE") {
        metadataWorkspace.unavailable = true;
        setMetadataStatus("unavailable", "The local catalog is not available.");
      } else {
        setMetadataStatus("error", "Metadata could not be loaded from the local catalog.");
      }
      updateMetadataControls();
      return;
    }
    applyMetadataPayloadToWorkspace(payload);
    renderMetadataWorkspace();
    metadataTitleInput.focus();
  } catch {
    if (token === metadataRequestToken) {
      metadataWorkspace.loading = false;
      setMetadataStatus("error", "Metadata could not be loaded from the local catalog.");
      updateMetadataControls();
    }
  }
}

function selectMetadataTag(key) {
  if (metadataWorkspace.current.tagKeys.includes(key)) {
    return;
  }
  if (metadataWorkspace.current.tagKeys.length >= MAX_METADATA_TAGS) {
    setMetadataStatus("validation", "A medium can have at most 32 canonical tags.");
    updateMetadataControls();
    return;
  }
  metadataWorkspace.current.tagKeys = [...metadataWorkspace.current.tagKeys, key];
  metadataWorkspace.statusOverride = null;
  renderMetadataWorkspace();
}

function moveSelectedMetadataTag(index, direction) {
  const nextIndex = index + direction;
  if (nextIndex < 0 || nextIndex >= metadataWorkspace.current.tagKeys.length) {
    return;
  }
  const keys = [...metadataWorkspace.current.tagKeys];
  const current = keys[index];
  keys[index] = keys[nextIndex];
  keys[nextIndex] = current;
  metadataWorkspace.current.tagKeys = keys;
  metadataWorkspace.statusOverride = null;
  renderMetadataWorkspace();
}

function removeSelectedMetadataTag(key) {
  metadataWorkspace.current.tagKeys = metadataWorkspace.current.tagKeys.filter((tagKey) => tagKey !== key);
  metadataWorkspace.statusOverride = null;
  renderMetadataWorkspace();
}

function resetMetadataWorkspaceAfterDiscard() {
  metadataWorkspace.current = {
    displayTitle: metadataWorkspace.baseline.displayTitle || "",
    tagKeys: [...metadataWorkspace.baseline.tagKeys],
  };
  metadataWorkspace.statusOverride = null;
  metadataCreateStatus.textContent = "";
  renderMetadataWorkspace();
}

function handleDiscardMetadataChanges() {
  resetMetadataWorkspaceAfterDiscard();
}

function closeMetadataWorkspace() {
  if (!confirmDiscardDirtyMetadata()) {
    return;
  }
  metadataRequestToken += 1;
  metadataWorkspace = {
    openMediaId: null,
    openItem: null,
    loading: false,
    saving: false,
    unavailable: false,
    notFound: false,
    statusOverride: null,
    baseline: { displayTitle: null, tagKeys: [] },
    current: { displayTitle: "", tagKeys: [] },
  };
  metadataWorkspaceElement.hidden = true;
  syncMetadataBeforeUnloadProtection();
  loadCatalog();
}

function createTagValidationError(key, displayName) {
  if (!TAG_KEY_PATTERN.test(key)) {
    return "Canonical key must be a lowercase English slug.";
  }
  if (key.length > 64) {
    return "Canonical key must be 64 characters or fewer.";
  }
  if (!displayName.trim() || displayName.trim().length > 80 || hasControlCharacter(displayName)) {
    return "Display name must be 1 to 80 characters and contain no control characters.";
  }
  return "";
}

async function handleCreateAndSelectTag(event) {
  event.preventDefault();
  const key = metadataCreateKeyInput.value;
  const displayName = metadataCreateNameInput.value;
  const validation = createTagValidationError(key, displayName);
  if (validation) {
    metadataCreateStatus.textContent = validation;
    return;
  }
  metadataCreateStatus.textContent = "Creating canonical tag definition...";
  try {
    const response = await fetch(CANONICAL_TAGS_ENDPOINT, {
      method: "POST",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ key, display_name: displayName }),
      cache: "no-store",
    });
    const payload = await response.json();
    if (response.ok) {
      await loadCatalogTags();
      if (!metadataWorkspace.current.tagKeys.includes(payload.tag.key)
        && metadataWorkspace.current.tagKeys.length < MAX_METADATA_TAGS) {
        metadataWorkspace.current.tagKeys = [...metadataWorkspace.current.tagKeys, payload.tag.key];
      }
      metadataCreateKeyInput.value = "";
      metadataCreateNameInput.value = "";
      metadataCreateStatus.textContent = payload.status === "already_exists"
        ? "Canonical tag already existed with the same definition and is selected."
        : "Canonical tag created and selected.";
      renderMetadataWorkspace();
      return;
    }
    const code = payload.error ? payload.error.code : "";
    if (code === "CANONICAL_TAG_DEFINITION_CONFLICT") {
      metadataCreateStatus.textContent = "This key already exists with a different display name.";
      await loadCatalogTags();
      return;
    }
    if (code === "CATALOG_UNAVAILABLE") {
      metadataCreateStatus.textContent = "The local catalog is not available. Unsaved metadata is preserved.";
      return;
    }
    metadataCreateStatus.textContent = "Canonical tag could not be created.";
  } catch {
    metadataCreateStatus.textContent = "Canonical tag could not be created.";
  }
}

async function handleSaveMetadata() {
  const normalized = normalizedMetadataFormState();
  if (normalized.error || metadataWorkspace.openMediaId === null) {
    updateMetadataControls();
    return;
  }
  metadataWorkspace.saving = true;
  metadataWorkspace.unavailable = false;
  metadataWorkspace.notFound = false;
  setMetadataStatus("saving", "Saving metadata...");
  updateMetadataControls();
  try {
    const mediaId = metadataWorkspace.openMediaId;
    const response = await fetch(metadataEndpoint(mediaId), {
      method: "PUT",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ display_title: normalized.displayTitle, tag_keys: normalized.tagKeys }),
      cache: "no-store",
    });
    const payload = await response.json();
    metadataWorkspace.saving = false;
    if (response.ok) {
      applyMetadataPayloadToWorkspace(payload.metadata);
      setMetadataStatus(
        "saved",
        payload.status === "created"
          ? "Metadata saved as a new catalog metadata row."
          : payload.status === "updated"
            ? "Metadata updated."
            : payload.status === "unchanged"
              ? "No metadata changes were required."
              : "Metadata saved.",
      );
      renderMetadataWorkspace();
      await loadCatalog();
      return;
    }
    const code = payload.error ? payload.error.code : "";
    if (code === "CANONICAL_TAG_NOT_FOUND") {
      await loadCatalogTags();
      setMetadataStatus("validation", "One selected canonical tag is no longer available. Resolve the selection before retrying.");
    } else if (code === "MEDIA_NOT_FOUND") {
      metadataWorkspace.notFound = true;
      setMetadataStatus("notFound", "The selected medium is no longer available.");
      await loadCatalog();
    } else if (code === "CATALOG_UNAVAILABLE") {
      metadataWorkspace.unavailable = true;
      setMetadataStatus("unavailable", "The local catalog is not available. Unsaved metadata is preserved.");
    } else {
      setMetadataStatus("error", "Metadata save failed with a sanitized local error.");
    }
    updateMetadataControls();
  } catch {
    metadataWorkspace.saving = false;
    setMetadataStatus("error", "Metadata save failed with a sanitized local error.");
    updateMetadataControls();
  }
}

async function loadCatalog() {
  const token = catalogRequestToken + 1;
  catalogRequestToken = token;
  showCatalogState("loading");
  catalogPrevButton.disabled = true;
  catalogNextButton.disabled = true;
  catalogPageSummary.textContent = "Loading catalog page...";
  try {
    const params = buildCatalogQueryParams();
    const response = await fetch(`${MEDIA_CATALOG_ENDPOINT}?${params.toString()}`, {
      headers: { Accept: "application/json" },
      cache: "no-store",
    });
    const payload = await response.json();
    if (token !== catalogRequestToken) {
      return;
    }
    if (!response.ok) {
      const code = payload.error ? payload.error.code : "";
      showCatalogState(code === "CATALOG_UNAVAILABLE" ? "unavailable" : "error");
      catalogPageSummary.textContent = "Catalog page unavailable.";
      return;
    }
    renderCatalogSuccess(payload);
  } catch {
    if (token === catalogRequestToken) {
      showCatalogState("error");
      catalogPageSummary.textContent = "Catalog page unavailable.";
    }
  }
}

async function handleImportClick(libraryId, candidate, button, status) {
  button.disabled = true;
  status.textContent = "Importing selected candidate...";
  try {
    const response = await fetch(`${LIBRARIES_ENDPOINT}/${libraryId}/${MEDIA_IMPORTS_ENDPOINT}`, {
      method: "POST",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ relative_path: candidate.relative_path }),
      cache: "no-store",
    });
    const payload = await response.json();
    if (response.ok) {
      button.disabled = true;
      const imported = payload.status === "already_imported" ? "Already imported" : "Imported";
      status.textContent = `${imported}: ${payload.location.relative_path}`;
      await loadCatalog();
      return;
    }
    const code = payload.error ? payload.error.code : "";
    if (code === "MEDIA_IMPORT_CANDIDATE_UNAVAILABLE") {
      status.textContent = "Candidate was not found in the current scan.";
      return;
    }
    if (code === "LIBRARY_UNAVAILABLE") {
      status.textContent = "Library is not available for import.";
      return;
    }
    if (code === "CATALOG_UNAVAILABLE") {
      status.textContent = "Catalog is not available for import.";
      return;
    }
    status.textContent = "Import failed with a sanitized local error.";
  } catch {
    status.textContent = "Import failed before the local response could be read.";
  } finally {
    if (status.textContent.startsWith("Imported") || status.textContent.startsWith("Already")) {
      button.disabled = true;
    } else {
      button.disabled = false;
    }
  }
}

async function handleInspectClick(libraryId, candidate, card) {
  const token = analysisRequestToken + 1;
  analysisRequestToken = token;
  const elements = previewElements(card);
  resetAiReview(card);
  elements.path.textContent = candidate.relative_path;
  elements.kind.textContent = candidate.kind;
  elements.metadata.replaceChildren();
  elements.metadata.hidden = true;
  elements.warnings.replaceChildren();
  elements.warnings.hidden = true;
  elements.frames.replaceChildren();
  elements.frames.hidden = true;
  setInspectActionsDisabled(true);
  setLocalPreviewState(card, "preparing", "Preparing local metadata and representative frames...");
  try {
    const response = await fetch(`${LIBRARIES_ENDPOINT}/${libraryId}/media-analysis-preview`, {
      method: "POST",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ relative_path: candidate.relative_path }),
      cache: "no-store",
    });
    const payload = await response.json();
    if (token !== analysisRequestToken) {
      return;
    }
    if (response.ok) {
      renderAnalysisSuccess(card, payload);
      return;
    }
    const code = payload.error ? payload.error.code : "";
    if (code === "MEDIA_ANALYSIS_UNAVAILABLE") {
      renderUnavailablePreview(card);
      return;
    }
    if (code === "INVALID_MEDIA_PATH") {
      renderInvalidCandidatePreview(card);
      return;
    }
    renderGenericPreviewError(card);
  } catch {
    if (token === analysisRequestToken) {
      renderGenericPreviewError(card);
    }
  } finally {
    if (token === analysisRequestToken) {
      setInspectActionsDisabled(false);
    }
  }
}

function reviewField(labelText, control) {
  const label = document.createElement("label");
  const span = document.createElement("span");
  span.textContent = labelText;
  label.append(span, control);
  return label;
}

function buildTextInput(className, value, maximum) {
  const input = document.createElement("input");
  input.className = className;
  input.type = "text";
  input.maxLength = maximum;
  input.value = value;
  input.addEventListener("input", markReviewEdited);
  return input;
}

function buildTextarea(className, value, maximum) {
  const textarea = document.createElement("textarea");
  textarea.className = className;
  textarea.maxLength = maximum;
  textarea.rows = 4;
  textarea.value = value;
  textarea.addEventListener("input", markReviewEdited);
  return textarea;
}

function currentTags(review) {
  return [...review.querySelectorAll(".review-tag-value")].map((item) => item.textContent.trim());
}

function removeTag(button) {
  const tag = button.closest(".review-tag");
  if (tag) {
    tag.remove();
  }
  markReviewEdited();
}

function addTag(review, value) {
  const trimmed = value.trim();
  const status = review.querySelector(".review-validation");
  if (!trimmed || trimmed.length > MAX_REVIEW_TEXT.tag) {
    if (status) {
      status.textContent = "Tags must be non-empty and fit the review limits.";
    }
    return;
  }
  if (currentTags(review).some((tag) => tag.toLowerCase() === trimmed.toLowerCase())) {
    if (status) {
      status.textContent = "Duplicate tags are not allowed.";
    }
    return;
  }
  const item = document.createElement("span");
  item.className = "review-tag";
  const valueNode = document.createElement("span");
  valueNode.className = "review-tag-value";
  valueNode.textContent = trimmed;
  const remove = document.createElement("button");
  remove.type = "button";
  remove.textContent = "Remove";
  remove.addEventListener("click", () => removeTag(remove));
  item.append(valueNode, remove);
  review.querySelector(".review-tags").appendChild(item);
  if (status) {
    status.textContent = "";
  }
  markReviewEdited();
}

function validateReview(review) {
  const title = review.querySelector(".review-title-input").value.trim();
  const description = review.querySelector(".review-description-input").value.trim();
  const collection = review.querySelector(".review-collection-input").value.trim();
  const filename = review.querySelector(".review-filename-input").value.trim();
  const tags = currentTags(review);
  const folded = new Set(tags.map((tag) => tag.toLowerCase()));
  if (!title || title.length > MAX_REVIEW_TEXT.title) {
    return "Title is required.";
  }
  if (!description || description.length > MAX_REVIEW_TEXT.description) {
    return "Description is required.";
  }
  if (!collection || collection.length > MAX_REVIEW_TEXT.collection) {
    return "Collection is required.";
  }
  if (!filename || filename.length > MAX_REVIEW_TEXT.filename || /[/\\:*?"<>|]/.test(filename)) {
    return "Suggested filename is required and must avoid filesystem-forbidden characters.";
  }
  if (tags.length < 1 || tags.length > 12 || tags.some((tag) => !tag || tag.length > MAX_REVIEW_TEXT.tag)) {
    return "Review requires 1 to 12 non-empty tags.";
  }
  if (folded.size !== tags.length) {
    return "Duplicate tags are not allowed.";
  }
  return "";
}

function markReviewEdited(event) {
  const review = event && event.target ? event.target.closest(".ai-review") : document.querySelector(".ai-review:not([hidden])");
  if (!review) {
    return;
  }
  if (review.dataset.state === "accepted") {
    review.dataset.state = "edited";
    const status = review.querySelector(".review-status");
    status.textContent = "Draft edited after session acceptance.";
  }
}

function renderList(parent, label, values) {
  const section = document.createElement("div");
  const heading = document.createElement("h5");
  const list = document.createElement("ul");
  heading.textContent = label;
  values.forEach((value) => {
    const item = document.createElement("li");
    item.textContent = value;
    list.appendChild(item);
  });
  section.append(heading, list);
  parent.appendChild(section);
}

function renderEditableReview(card, payload) {
  const elements = aiElements(card);
  const review = elements.review;
  const suggestion = payload.suggestion;
  review.replaceChildren();
  review.hidden = false;
  review.dataset.state = "editing";

  const title = buildTextInput("review-title-input", suggestion.title, MAX_REVIEW_TEXT.title);
  const description = buildTextarea("review-description-input", suggestion.description, MAX_REVIEW_TEXT.description);
  const collection = buildTextInput("review-collection-input", suggestion.collection, MAX_REVIEW_TEXT.collection);
  const filename = buildTextInput("review-filename-input", suggestion.suggested_filename, MAX_REVIEW_TEXT.filename);

  const tagList = document.createElement("div");
  tagList.className = "review-tags";
  const tagControl = document.createElement("div");
  tagControl.className = "review-tag-control";
  const tagInput = buildTextInput("review-tag-input", "", MAX_REVIEW_TEXT.tag);
  const addButton = document.createElement("button");
  addButton.type = "button";
  addButton.textContent = "Add tag";
  addButton.addEventListener("click", () => {
    addTag(review, tagInput.value);
    tagInput.value = "";
  });
  tagControl.append(tagInput, addButton);
  suggestion.tags.forEach((tag) => {
    const item = document.createElement("span");
    item.className = "review-tag";
    const valueNode = document.createElement("span");
    valueNode.className = "review-tag-value";
    valueNode.textContent = tag;
    const remove = document.createElement("button");
    remove.type = "button";
    remove.textContent = "Remove";
    remove.addEventListener("click", () => removeTag(remove));
    item.append(valueNode, remove);
    tagList.appendChild(item);
  });

  const validation = document.createElement("p");
  validation.className = "review-validation";
  validation.setAttribute("role", "status");

  const facts = document.createElement("dl");
  facts.className = "review-facts";
  addMetadataValue(facts, "Confidence", String(suggestion.confidence));
  addMetadataValue(facts, "Provider", payload.provider_id);
  addMetadataValue(facts, "Model", payload.model_id);
  addMetadataValue(facts, "Prompt", payload.prompt_version);

  const evidence = document.createElement("div");
  evidence.className = "review-evidence";
  renderList(evidence, "Evidence", suggestion.evidence || []);
  renderList(evidence, "Uncertainties", suggestion.uncertainties || []);

  const actions = document.createElement("div");
  actions.className = "review-actions";
  const accept = document.createElement("button");
  accept.type = "button";
  accept.textContent = "Accept draft for this session";
  accept.addEventListener("click", () => {
    const error = validateReview(review);
    if (error) {
      validation.textContent = error;
      return;
    }
    review.dataset.state = "accepted";
    validation.textContent = "";
    review.querySelector(".review-status").textContent = elements.acceptedTemplate.textContent;
  });
  const reject = document.createElement("button");
  reject.type = "button";
  reject.textContent = "Reject draft";
  reject.addEventListener("click", () => {
    review.replaceChildren();
    review.hidden = true;
    elements.status.textContent = elements.rejectedTemplate.textContent;
  });
  actions.append(accept, reject);

  const status = document.createElement("p");
  status.className = "review-status";
  status.setAttribute("role", "status");

  review.append(
    reviewField("Title", title),
    reviewField("Description", description),
    reviewField("Collection", collection),
    reviewField("Suggested filename", filename),
    tagList,
    tagControl,
    validation,
    facts,
    evidence,
    actions,
    status,
  );
  validation.textContent = "";
}

function suggestionErrorMessage(code) {
  if (code === "AI_PROVIDER_NOT_CONFIGURED") {
    return "AI provider is not configured.";
  }
  if (code === "CLOUD_CONFIRMATION_REQUIRED") {
    return "Explicit cloud upload confirmation is required.";
  }
  if (code === "AI_PROVIDER_AUTHENTICATION_FAILED") {
    return "The configured AI provider credential was rejected.";
  }
  if (code === "AI_PROVIDER_RATE_LIMITED") {
    return "The AI suggestion provider rate limit was reached.";
  }
  if (code === "AI_PROVIDER_UNAVAILABLE") {
    return "The AI suggestion provider is not available.";
  }
  if (code === "AI_PROVIDER_INVALID_RESPONSE") {
    return "The AI suggestion provider response was invalid.";
  }
  if (code === "MEDIA_PREPARATION_UNAVAILABLE") {
    return "Local media preparation is not available.";
  }
  if (code === "INVALID_MEDIA_PATH") {
    return "Invalid media relative path.";
  }
  return "The AI suggestion provider request failed.";
}

async function handleAnalyzeClick(card) {
  const elements = aiElements(card);
  const token = suggestionRequestToken + 1;
  suggestionRequestToken = token;
  const libraryId = elements.analyzeButton.dataset.libraryId;
  const relativePath = elements.analyzeButton.dataset.relativePath;
  elements.checkbox.checked = false;
  updateAnalyzeButton(card);
  setAnalyzeActionsDisabled(true);
  elements.panel.dataset.state = "pending";
  elements.review.replaceChildren();
  elements.review.hidden = true;
  elements.status.textContent = "Preparing frames and requesting an editable suggestion...";
  try {
    const response = await fetch(`${LIBRARIES_ENDPOINT}/${libraryId}/media-suggestion-preview`, {
      method: "POST",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        relative_path: relativePath,
        confirm_cloud_upload: true,
      }),
      cache: "no-store",
    });
    const payload = await response.json();
    if (token !== suggestionRequestToken) {
      return;
    }
    if (response.ok) {
      elements.panel.dataset.state = "review";
      elements.status.textContent = "Editable AI suggestion ready.";
      renderEditableReview(card, payload);
      return;
    }
    const code = payload.error ? payload.error.code : "";
    elements.panel.dataset.state = "error";
    elements.status.textContent = suggestionErrorMessage(code);
  } catch {
    if (token === suggestionRequestToken) {
      elements.panel.dataset.state = "error";
      elements.status.textContent = "The AI suggestion provider request failed.";
    }
  } finally {
    if (token === suggestionRequestToken) {
      setAnalyzeActionsDisabled(false);
      updateAnalyzeButton(card);
    }
  }
}

async function handlePreviewClick(library, card) {
  const button = card.querySelector(".preview-button");
  const status = card.querySelector(".scan-status");
  button.disabled = true;
  status.textContent = "Running a bounded read-only scan preview...";
  try {
    const response = await fetch(`${LIBRARIES_ENDPOINT}/${library.id}/scan-preview`, {
      method: "POST",
      headers: { Accept: "application/json" },
      cache: "no-store",
    });
    const payload = await response.json();
    if (!response.ok) {
      status.textContent = payload.error
        ? payload.error.message
        : "Scan preview failed with a sanitized local error.";
      return;
    }
    renderScanResult(card, payload);
  } catch {
    status.textContent = "Scan preview failed before the local response could be read.";
  } finally {
    button.disabled = false;
  }
}

function prepareAiControls(card) {
  const elements = aiElements(card);
  elements.checkbox.addEventListener("change", () => updateAnalyzeButton(card));
  elements.analyzeButton.addEventListener("click", () => handleAnalyzeClick(card));
}

function renderLibraries(libraries) {
  libraryList.replaceChildren();
  if (libraries.length === 0) {
    showLibraryState("empty");
    return;
  }
  libraries.forEach((library) => {
    const fragment = libraryCardTemplate.content.cloneNode(true);
    const card = fragment.querySelector(".library-card");
    fragment.querySelector(".library-name").textContent = library.display_name;
    fragment.querySelector(".library-meta").textContent = `Library ID ${library.id}; ${library.path_flavor} path flavor. Root path is intentionally hidden.`;
    fragment.querySelector(".preview-button").addEventListener("click", () => {
      handlePreviewClick(library, card);
    });
    prepareAiControls(card);
    libraryList.appendChild(fragment);
  });
  showLibraryState("success");
}

async function loadLibraries() {
  showLibraryState("loading");
  try {
    const response = await fetch(LIBRARIES_ENDPOINT, {
      headers: { Accept: "application/json" },
      cache: "no-store",
    });
    const payload = await response.json();
    if (!response.ok) {
      showLibraryState(payload.error && payload.error.code === "CATALOG_UNAVAILABLE" ? "unavailable" : "error");
      return;
    }
    renderLibraries(payload.libraries || []);
  } catch {
    showLibraryState("error");
  }
}

catalogSearchForm.addEventListener("submit", (event) => {
  event.preventDefault();
  catalogState.q = catalogSearchInput.value;
  catalogState.offset = 0;
  loadCatalog();
});

catalogClearButton.addEventListener("click", () => {
  if (!confirmDiscardDirtyMetadata()) {
    return;
  }
  if (metadataWorkspace.openMediaId !== null) {
    metadataWorkspace.openMediaId = null;
    metadataWorkspaceElement.hidden = true;
    syncMetadataBeforeUnloadProtection();
  }
  catalogState.q = "";
  catalogState.tagKeys = [];
  catalogState.offset = 0;
  catalogSearchInput.value = "";
  renderActiveCatalogFilters(catalogState.tagKeys);
  loadCatalog();
});

catalogPrevButton.addEventListener("click", () => {
  catalogState.offset = Math.max(0, catalogState.offset - catalogState.limit);
  loadCatalog();
});

catalogNextButton.addEventListener("click", () => {
  if (catalogState.offset + catalogState.limit >= catalogState.total) {
    return;
  }
  catalogState.offset += catalogState.limit;
  loadCatalog();
});

metadataTitleInput.addEventListener("input", () => {
  metadataWorkspace.current.displayTitle = metadataTitleInput.value;
  metadataWorkspace.statusOverride = null;
  updateMetadataControls();
});

metadataTagSearchInput.addEventListener("input", renderMetadataTagSuggestions);
metadataSaveButton.addEventListener("click", handleSaveMetadata);
metadataDiscardButton.addEventListener("click", handleDiscardMetadataChanges);
metadataCloseButton.addEventListener("click", closeMetadataWorkspace);
metadataCreateTagForm.addEventListener("submit", handleCreateAndSelectTag);

renderActiveCatalogFilters(catalogState.tagKeys);
checkHealth();
loadAiCapability();
loadCatalogTags();
loadCatalog();
loadLibraries();
window.addEventListener("pagehide", revokePreviewObjectUrls);
