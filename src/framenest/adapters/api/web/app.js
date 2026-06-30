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
const MAX_METADATA_DESCRIPTION_CODE_POINTS = 10000;
const MAX_METADATA_TAGS = 32;
const TAG_KEY_PATTERN = /^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$/;
const PROCESSED_COLLECTION = "processed";
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
const MAX_PREVIEW_CACHE = 12;
const PREVIEW_FRAME_INTERVAL_MS = 1200;
let previewCacheMap = new Map();
let previewRequestToken = 0;
let activePreviewMediaId = null;
let activePreviewTimer = null;
let cardMediaElements = new Set();
let detailsMediaToken = 0;
let detailsMediaElement = null;
const prefersReducedMotion = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
let metadataBeforeUnloadAttached = false;
let metadataAiRequestToken = 0;
let catalogState = {
  q: "",
  tagKeys: [],
  collection: "",
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
  analyzing: false,
  aiDraft: null,
  aiDraftDirty: false,
  baseline: { displayTitle: null, description: null, tagKeys: [], collectionKey: null, processedAtMs: null },
  current: { displayTitle: "", description: "", tagKeys: [], collectionKey: null, processedAtMs: null },
};
let metadataTagSuggestionState = {
  items: [],
  activeIndex: -1,
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
const serverHealthButton = document.querySelector("#server-health-button");
const serverHealthButtonText = document.querySelector("#server-health-button-text");
const aiStatusButton = document.querySelector("#ai-status-button");
const aiStatusButtonText = document.querySelector("#ai-status-button-text");
const settingsDialog = document.querySelector("#settings-dialog");
const settingsCloseButton = document.querySelector("#settings-close-button");
const settingsAiStatus = document.querySelector("#settings-ai-status");
const settingsAiStatusText = document.querySelector("#settings-ai-status-text");
const settingsAiProvider = document.querySelector("#settings-ai-provider");
let healthCheckInFlight = false;
let lastFocusedElementBeforeSettings = null;
const libraryList = document.querySelector("#library-list");
const libraryStateLoading = document.querySelector("#library-state-loading");
const libraryStateEmpty = document.querySelector("#library-state-empty");
const libraryStateUnavailable = document.querySelector("#library-state-unavailable");
const libraryStateError = document.querySelector("#library-state-error");
const libraryCardTemplate = document.querySelector("#library-card-template");
const catalogTagFilters = document.querySelector("#catalog-tag-filters");
const catalogTagsState = document.querySelector("#catalog-tags-state");
const commandSearchInput = document.querySelector("#command-search-input");
const commandSearchClear = document.querySelector("#command-search-clear");
const commandSearchSuggestions = document.querySelector("#command-search-suggestions");
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
const metadataStatus = document.querySelector("#metadata-status");
const metadataTitleInput = document.querySelector("#metadata-title-input");
const metadataTitleFallback = document.querySelector("#metadata-title-fallback");
const metadataValidationMessage = document.querySelector("#metadata-validation-message");
const metadataDescriptionInput = document.querySelector("#metadata-description-input");
const metadataDescriptionStatus = document.querySelector("#metadata-description-status");
const metadataTagSearchInput = document.querySelector("#metadata-tag-search-input");
const metadataTagSuggestions = document.querySelector("#metadata-tag-suggestions");
const metadataSelectedTags = document.querySelector("#metadata-selected-tags");
const metadataTagStatus = document.querySelector("#metadata-tag-status");
const metadataAiPanel = document.querySelector("#metadata-ai-panel");
const metadataAiCapability = document.querySelector("#metadata-ai-capability");
const metadataAiAnalyzeButton = document.querySelector("#metadata-ai-analyze-button");
const metadataAiStatus = document.querySelector("#metadata-ai-status");
const metadataAiLoading = document.querySelector("#metadata-ai-loading");
const metadataAiDraft = document.querySelector("#metadata-ai-draft");
const metadataAiTitleInput = document.querySelector("#metadata-ai-title-input");
const metadataAiDescriptionInput = document.querySelector("#metadata-ai-description-input");
const metadataAiTagsInput = document.querySelector("#metadata-ai-tags-input");
const metadataAiFilenameInput = document.querySelector("#metadata-ai-filename-input");
const metadataAiUseButton = document.querySelector("#metadata-ai-use-button");
const metadataAiDiscardButton = document.querySelector("#metadata-ai-discard-button");
const metadataDialog = document.querySelector("#metadata-dialog");
const detailsDialog = document.querySelector("#media-details-dialog");
const detailsCloseButton = document.querySelector("#media-details-close");
const detailsEditButton = document.querySelector("#media-details-edit");
const detailsLoading = document.querySelector("#media-details-loading");
const detailsError = document.querySelector("#media-details-error");
const detailsContent = document.querySelector("#media-details-content");
const detailsPreviewContainer = document.querySelector("#details-preview-container");
const detailsDialogTitle = document.querySelector("#media-details-title");
const detailsKind = document.querySelector("#media-details-kind");
const detailsTagsContainer = document.querySelector("#media-details-tags");
const detailsProcessedContainer = document.querySelector("#media-details-processed");
const detailsDescription = document.querySelector("#media-details-description");
const detailsTechnical = document.querySelector("#media-details-technical");
const detailsTechnicalList = document.querySelector("#media-details-technical-list");
let metadataOpenerElement = null;
let detailsOpenerElement = null;
let detailsCurrentItem = null;
let detailsMetadataToken = 0;
let detailsPlayRequested = false;
const metadataSaveButton = document.querySelector("#metadata-save-button");
const metadataDiscardButton = document.querySelector("#metadata-discard-button");

function setStatusClass(className) {
  statusContainer.classList.remove("status--loading", "status--healthy", "status--error");
  statusContainer.classList.add(className);
}

function setLoadingState() {
  setStatusClass("status--loading");
  statusText.textContent = "Checking local server...";
  statusDetail.textContent = "Waiting for the same-origin health response.";
  setServerHealthButtonState("checking", "Checking");
}

function setHealthyState() {
  setStatusClass("status--healthy");
  statusText.textContent = "Local server healthy";
  statusDetail.textContent = "The FrameNest application process answered the health check.";
  setServerHealthButtonState("healthy", "Healthy");
}

function setErrorState() {
  setStatusClass("status--error");
  statusText.textContent = "Health check unavailable";
  statusDetail.textContent =
    "The page loaded, but the local health endpoint did not return the expected response.";
  setServerHealthButtonState("unhealthy", "Unhealthy");
}

function setServerHealthButtonState(state, label) {
  if (!serverHealthButton) return;
  serverHealthButton.classList.remove("status-button--checking", "status-button--healthy", "status-button--unhealthy");
  serverHealthButton.classList.add("status-button--" + state);
  if (serverHealthButtonText) serverHealthButtonText.textContent = label;
  if (state === "healthy") {
    serverHealthButton.setAttribute("aria-label", "Local server healthy");
    serverHealthButton.title = "Local server healthy";
  } else if (state === "unhealthy") {
    serverHealthButton.setAttribute("aria-label", "Local server unhealthy or unreachable");
    serverHealthButton.title = "Local server unhealthy or unreachable. Click to retry.";
  } else {
    serverHealthButton.setAttribute("aria-label", "Checking local server");
    serverHealthButton.title = "Checking local server...";
  }
}

function setAiStatusButtonState(state, label) {
  if (!aiStatusButton) return;
  aiStatusButton.classList.remove("status-button--checking", "status-button--healthy", "status-button--unhealthy");
  aiStatusButton.classList.add("status-button--" + state);
  if (aiStatusButtonText) aiStatusButtonText.textContent = label;
  if (state === "healthy") {
    aiStatusButton.setAttribute("aria-label", "AI available");
    aiStatusButton.title = "AI available. Click to open settings.";
  } else if (state === "unhealthy") {
    aiStatusButton.setAttribute("aria-label", "AI unavailable");
    aiStatusButton.title = "AI unavailable. Click to open settings.";
  } else {
    aiStatusButton.setAttribute("aria-label", "Checking AI status");
    aiStatusButton.title = "Checking AI capability...";
  }
}

async function checkHealth() {
  if (healthCheckInFlight) return;
  healthCheckInFlight = true;
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
  } finally {
    healthCheckInFlight = false;
  }
}

async function retryHealth() {
  await checkHealth();
}

function setAiStatusClass(className) {
  aiStatus.classList.remove("status--loading", "status--healthy", "status--error");
  aiStatus.classList.add(className);
}

function updateSettingsAiStatus(state, text, providerInfo) {
  if (!settingsAiStatus) return;
  settingsAiStatus.classList.remove("is-available", "is-unavailable");
  if (state === "available") settingsAiStatus.classList.add("is-available");
  else if (state === "unavailable") settingsAiStatus.classList.add("is-unavailable");
  if (settingsAiStatusText) settingsAiStatusText.textContent = text;
  if (settingsAiProvider) settingsAiProvider.textContent = providerInfo || "";
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
    setAiStatusButtonState("healthy", "Available");
    updateSettingsAiStatus("available", "Available", `${aiCapability.provider_id} / ${aiCapability.model_id}`);
    return;
  }
  setAiStatusClass("status--error");
  aiStatusText.textContent = "AI unavailable";
  aiStatusDetail.textContent = "Configure the server-side NVIDIA credential before starting FrameNest.";
  setAiStatusButtonState("unhealthy", "Unavailable");
  updateSettingsAiStatus("unavailable", "Unavailable", "");
}

async function loadAiCapability() {
  setAiStatusClass("status--loading");
  aiStatusText.textContent = "Checking AI capability...";
  aiStatusDetail.textContent = "No provider request is made for capability discovery.";
  setAiStatusButtonState("checking", "Checking");
  updateSettingsAiStatus("checking", "Checking...", "");
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

function mediaAiSuggestionEndpoint(mediaId, locationId) {
  return `${MEDIA_CATALOG_ENDPOINT}/${mediaId}/locations/${locationId}/ai-suggestion-preview`;
}

function unicodeCodePointLength(value) {
  return [...value].length;
}

function hasControlCharacter(value) {
  return [...value].some((character) => {
    const codePoint = character.codePointAt(0);
    return (codePoint >= 0 && codePoint <= 31) || codePoint === 127;
  });
}

function hasForbiddenDescriptionControlChar(value) {
  for (const character of value) {
    const codePoint = character.codePointAt(0);
    if (codePoint === 0x0a) {
      continue;
    }
    if (
      codePoint <= 0x1f ||
      (codePoint >= 0x7f && codePoint <= 0x9f)
    ) {
      return true;
    }
  }
  return false;
}

function semanticArraysEqual(left, right) {
  if (left.length !== right.length) {
    return false;
  }
  return left.every((value, index) => value === right[index]);
}

function normalizedDescriptionState() {
  const rawDescription = metadataDescriptionInput.value;
  if (hasForbiddenDescriptionControlChar(rawDescription)) {
    return { error: "Description must not contain NUL, tab, carriage return, or control characters." };
  }
  if (unicodeCodePointLength(rawDescription) > MAX_METADATA_DESCRIPTION_CODE_POINTS) {
    return { error: `Description must be ${MAX_METADATA_DESCRIPTION_CODE_POINTS} characters or fewer.` };
  }
  const trimmed = rawDescription.trim();
  if (trimmed === "") {
    return { description: null };
  }
  if (trimmed !== rawDescription) {
    return { error: "Non-empty descriptions must not start or end with whitespace." };
  }
  if (/[\r\t]/.test(rawDescription)) {
    return { error: "Description must not contain tab or carriage return characters." };
  }
  return { description: rawDescription };
}

function normalizedMetadataFormState() {
  const rawTitle = metadataTitleInput.value;
  if (hasControlCharacter(rawTitle)) {
    return { error: "Title must not contain NUL or control characters." };
  }
  if (rawTitle.length > MAX_METADATA_TITLE_CODE_POINTS) {
    return { error: "Title must be 240 characters or fewer." };
  }
  if (rawTitle.trim() === "") {
    const desc = normalizedDescriptionState();
    if (desc.error) {
      return desc;
    }
    return { displayTitle: null, description: desc.description, tagKeys: [...metadataWorkspace.current.tagKeys] };
  }
  if (rawTitle.trim() !== rawTitle) {
    return { error: "Non-empty titles must not start or end with whitespace." };
  }
  const desc = normalizedDescriptionState();
  if (desc.error) {
    return desc;
  }
  return { displayTitle: rawTitle, description: desc.description, tagKeys: [...metadataWorkspace.current.tagKeys] };
}

function metadataIsDirty() {
  const normalized = normalizedMetadataFormState();
  if (normalized.error) {
    return true;
  }
  return normalized.displayTitle !== metadataWorkspace.baseline.displayTitle
    || normalized.description !== metadataWorkspace.baseline.description
    || !semanticArraysEqual(normalized.tagKeys, metadataWorkspace.baseline.tagKeys);
}

function selectedTagDefinition(key) {
  return canonicalTagDefinitions.find((tag) => tag.key === key) || null;
}

function normalizedTagDisplayName(value) {
  return value.trim().replace(/\s+/g, " ");
}

function tagDisplayNameError(displayName) {
  if (!displayName) {
    return "Enter a tag name.";
  }
  if (unicodeCodePointLength(displayName) > 80 || hasControlCharacter(displayName)) {
    return "Tag names must be 1 to 80 characters and contain no control characters.";
  }
  return "";
}

function tagSlugFromDisplayName(displayName) {
  const slug = displayName
    .normalize("NFKD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .replace(/-{2,}/g, "-");
  if (!slug || !/^[a-z]/.test(slug)) {
    return "";
  }
  return slug.slice(0, 64).replace(/-+$/g, "");
}

function uniqueTagKeyForDisplayName(displayName) {
  const base = tagSlugFromDisplayName(displayName);
  if (!base || !TAG_KEY_PATTERN.test(base)) {
    return "";
  }
  const existingKeys = new Set(canonicalTagDefinitions.map((tag) => tag.key));
  if (!existingKeys.has(base)) {
    return base;
  }
  for (let suffix = 2; suffix < 100; suffix += 1) {
    const suffixText = `-${suffix}`;
    const candidate = `${base.slice(0, 64 - suffixText.length).replace(/-+$/g, "")}${suffixText}`;
    if (TAG_KEY_PATTERN.test(candidate) && !existingKeys.has(candidate)) {
      return candidate;
    }
  }
  return "";
}

function findTagByDisplayName(displayName) {
  const normalized = displayName.toLocaleLowerCase();
  return canonicalTagDefinitions.find((tag) => tag.display_name.toLocaleLowerCase() === normalized) || null;
}

function metadataDirtyForBeforeUnload() {
  return metadataWorkspace.openMediaId !== null && (metadataIsDirty() || metadataWorkspace.aiDraftDirty);
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

function selectPreviewableLocation(item) {
  if (!item.locations || item.locations.length === 0) return null;
  for (const location of item.locations) {
    if (location.availability === "available" && location.library_id && location.relative_path) {
      return { libraryId: location.library_id, relativePath: location.relative_path };
    }
  }
  return null;
}

function getCachedPreview(mediaId) {
  if (previewCacheMap.has(mediaId)) {
    const entry = previewCacheMap.get(mediaId);
    previewCacheMap.delete(mediaId);
    previewCacheMap.set(mediaId, entry);
    return entry;
  }
  return null;
}

function setCachedPreview(mediaId, entry) {
  if (previewCacheMap.has(mediaId)) {
    previewCacheMap.delete(mediaId);
  }
  previewCacheMap.set(mediaId, entry);
  while (previewCacheMap.size > MAX_PREVIEW_CACHE) {
    const oldestKey = previewCacheMap.keys().next().value;
    previewCacheMap.delete(oldestKey);
  }
}

function stopCardPreviewTimer() {
  if (activePreviewTimer) {
    clearInterval(activePreviewTimer);
    activePreviewTimer = null;
  }
  activePreviewMediaId = null;
}

function cleanupCatalogCardMedia() {
  cardMediaElements.forEach((element) => {
    if (element.tagName === "VIDEO") {
      element.pause();
      element.removeAttribute("src");
      try {
        element.load();
      } catch {
        // Ignore load failures during card media cleanup.
      }
    } else if (element.tagName === "IMG") {
      element.removeAttribute("src");
    }
    element.onerror = null;
    element.onload = null;
    element.onloadeddata = null;
    element.onloadedmetadata = null;
    element.oncanplay = null;
  });
  cardMediaElements = new Set();
}

function cleanupDetailsMedia({ invalidate = true } = {}) {
  if (invalidate) {
    detailsMediaToken += 1;
  }
  if (detailsMediaElement) {
    if (detailsMediaElement.tagName === "VIDEO") {
      detailsMediaElement.pause();
      detailsMediaElement.removeAttribute("src");
      detailsMediaElement.querySelectorAll("source").forEach((source) => source.remove());
      try {
        detailsMediaElement.load();
      } catch {
        // Ignore load failures during cleanup.
      }
    }
    detailsMediaElement.onerror = null;
    detailsMediaElement.onload = null;
    detailsMediaElement.onloadeddata = null;
    detailsMediaElement.oncanplay = null;
    detailsMediaElement = null;
  }
  if (detailsPreviewContainer) {
    detailsPreviewContainer.onclick = null;
    detailsPreviewContainer.onkeydown = null;
    detailsPreviewContainer.replaceChildren();
  }
}

async function handleCardPreview(item, card, placeholder) {
  if (activePreviewMediaId === item.media_id) {
    stopCardPreviewTimer();
    const cached = getCachedPreview(item.media_id);
    if (cached && !cached.error && cached.frames) {
      renderCardPreviewFrames(card, item, cached);
    }
    return;
  }
  stopCardPreviewTimer();
  const cached = getCachedPreview(item.media_id);
  if (cached) {
    if (cached.error) {
      renderCardPreviewState(card, item, "error");
      return;
    }
    renderCardPreviewFrames(card, item, cached);
    startCardPreviewCycling(card, item, cached);
    return;
  }
  const location = selectPreviewableLocation(item);
  if (!location) {
    renderCardPreviewState(card, item, "unavailable-location");
    return;
  }
  const token = ++previewRequestToken;
  renderCardPreviewState(card, item, "loading");
  try {
    const response = await fetch(`${LIBRARIES_ENDPOINT}/${location.libraryId}/media-analysis-preview`, {
      method: "POST",
      headers: { Accept: "application/json", "Content-Type": "application/json" },
      body: JSON.stringify({ relative_path: location.relativePath }),
      cache: "no-store",
    });
    if (token !== previewRequestToken) return;
    const payload = await response.json();
    if (token !== previewRequestToken) return;
    if (!response.ok) {
      setCachedPreview(item.media_id, { error: true });
      renderCardPreviewState(card, item, "error");
      return;
    }
    const frames = (payload.representative_frames || []).map((frame) => ({
      timestampMs: frame.timestamp_ms,
      objectUrl: URL.createObjectURL(decodeBase64Png(frame.payload_base64)),
    }));
    const cacheEntry = { frames, technicalMetadata: payload.technical_metadata || null };
    setCachedPreview(item.media_id, cacheEntry);
    renderCardPreviewFrames(card, item, cacheEntry);
    startCardPreviewCycling(card, item, cacheEntry);
  } catch {
    if (token === previewRequestToken) {
      setCachedPreview(item.media_id, { error: true });
      renderCardPreviewState(card, item, "error");
    }
  }
}

function renderCardPreviewState(card, item, state) {
  const placeholder = card.querySelector(".media-placeholder");
  if (!placeholder) return;
  placeholder.replaceChildren();
  placeholder.removeAttribute("data-preview-state");
  if (state === "loading") {
    placeholder.setAttribute("data-preview-state", "loading");
    const text = document.createElement("span");
    text.className = "media-placeholder__loading";
    text.textContent = "Loading preview…";
    placeholder.appendChild(text);
  } else if (state === "error") {
    placeholder.setAttribute("data-preview-state", "error");
    const text = document.createElement("span");
    text.className = "media-placeholder__error";
    text.textContent = "Preview unavailable.";
    placeholder.appendChild(text);
    const retry = document.createElement("button");
    retry.className = "media-placeholder__retry";
    retry.type = "button";
    retry.textContent = "Retry";
    retry.setAttribute("aria-label", "Retry preview");
    retry.addEventListener("click", () => {
      previewCacheMap.delete(item.media_id);
      const ph = card.querySelector(".media-placeholder");
      handleCardPreview(item, card, ph);
    });
    placeholder.appendChild(retry);
  } else if (state === "unavailable-location") {
    placeholder.setAttribute("data-preview-state", "unavailable");
    const text = document.createElement("span");
    text.className = "media-placeholder__error";
    text.textContent = "No local preview available.";
    placeholder.appendChild(text);
  } else if (state === "stopped") {
    placeholder.setAttribute("data-preview-state", "stopped");
    const text = document.createElement("span");
    text.className = "media-placeholder__stopped";
    text.textContent = "Preview stopped.";
    placeholder.appendChild(text);
  }
}

function renderCardPreviewFrames(card, item, cacheEntry) {
  const placeholder = card.querySelector(".media-placeholder");
  if (!placeholder) return;
  placeholder.replaceChildren();
  placeholder.removeAttribute("data-preview-state");
  if (!cacheEntry.frames || cacheEntry.frames.length === 0) {
    placeholder.setAttribute("data-preview-state", "no-frames");
    const text = document.createElement("span");
    text.className = "media-placeholder__error";
    text.textContent = "No preview frame available.";
    placeholder.appendChild(text);
    return;
  }
  placeholder.setAttribute("data-preview-state", "loaded");
  const img = document.createElement("img");
  img.className = "media-placeholder__preview-img";
  img.src = cacheEntry.frames[0].objectUrl;
  img.alt = `Local preview frame for ${item.display_title || deriveCatalogFallbackTitle(item)}`;
  img.style.width = "100%";
  img.style.height = "100%";
  img.style.objectFit = "contain";
  placeholder.appendChild(img);
}

function startCardPreviewCycling(card, item, cacheEntry) {
  if (!cacheEntry.frames || cacheEntry.frames.length <= 1) return;
  if (prefersReducedMotion) return;
  stopCardPreviewTimer();
  activePreviewMediaId = item.media_id;
  let frameIndex = 0;
  const img = card.querySelector(".media-placeholder__preview-img");
  if (!img) return;
  activePreviewTimer = setInterval(() => {
    frameIndex = (frameIndex + 1) % cacheEntry.frames.length;
    img.src = cacheEntry.frames[frameIndex].objectUrl;
  }, PREVIEW_FRAME_INTERVAL_MS);
}

function selectPlaybackLocation(item) {
  if (!item.locations || item.locations.length === 0) return null;
  return item.locations.find((location) => location.availability === "available" && location.location_id) || null;
}

function mediaContentUrl(mediaId, locationId) {
  return `${MEDIA_CATALOG_ENDPOINT}/${mediaId}/locations/${locationId}/content`;
}

function renderDetailsMediaUnavailable(container) {
  if (!container) return;
  container.replaceChildren();
  const text = document.createElement("p");
  text.className = "details-media-unavailable";
  text.textContent = "Media unavailable.";
  container.appendChild(text);
}

function renderDetailsMedia(item, { playWhenReady = false } = {}) {
  if (!detailsPreviewContainer) return;
  cleanupDetailsMedia();
  const token = ++detailsMediaToken;
  detailsPreviewContainer.className = "details-preview-container";
  detailsPreviewContainer.removeAttribute("role");
  detailsPreviewContainer.removeAttribute("tabindex");
  detailsPreviewContainer.removeAttribute("aria-label");
  detailsPreviewContainer.removeAttribute("title");

  const location = selectPlaybackLocation(item);
  if (!location) {
    renderDetailsMediaUnavailable(detailsPreviewContainer);
    return;
  }

  const loading = document.createElement("p");
  loading.className = "details-media-loading";
  loading.textContent = "Loading media…";
  detailsPreviewContainer.appendChild(loading);

  const url = mediaContentUrl(item.media_id, location.location_id);
  const title = item.display_title || deriveCatalogFallbackTitle(item);

  if (item.media_kind === "video") {
    const video = document.createElement("video");
    video.className = "details-media-video";
    video.controls = true;
    video.preload = "metadata";
    video.playsInline = true;
    video.autoplay = false;
    video.setAttribute("aria-label", title);
    video.hidden = true;

    video.onloadeddata = () => {
      if (token !== detailsMediaToken) return;
      loading.remove();
      video.hidden = false;
    };
    video.oncanplay = () => {
      if (token !== detailsMediaToken) return;
      loading.remove();
      video.hidden = false;
      if (playWhenReady) {
        video.play().catch(() => {
          // Native controls remain available when the browser blocks playback.
        });
        playWhenReady = false;
      }
    };
    video.onerror = () => {
      if (token !== detailsMediaToken) return;
      cleanupDetailsMedia({ invalidate: false });
      renderDetailsMediaUnavailable(detailsPreviewContainer);
    };
    detailsMediaElement = video;
    video.src = url;
    if (token === detailsMediaToken && detailsMediaElement === video) {
      detailsPreviewContainer.appendChild(video);
    }
  } else {
    const img = document.createElement("img");
    img.className = "details-media-img";
    img.alt = title;
    img.hidden = true;

    img.onload = () => {
      if (token !== detailsMediaToken) return;
      loading.remove();
      img.hidden = false;
    };
    img.onerror = () => {
      if (token !== detailsMediaToken) return;
      cleanupDetailsMedia({ invalidate: false });
      renderDetailsMediaUnavailable(detailsPreviewContainer);
    };
    detailsMediaElement = img;
    img.src = url;
    if (token === detailsMediaToken && detailsMediaElement === img) {
      detailsPreviewContainer.appendChild(img);
    }
  }
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

function buildProcessedTimeElement(processedAtMs) {
  if (processedAtMs === null || processedAtMs === undefined) {
    return null;
  }
  const numeric = Number(processedAtMs);
  if (!Number.isFinite(numeric)) {
    return null;
  }
  const date = new Date(numeric);
  if (Number.isNaN(date.getTime())) {
    return null;
  }
  const iso = date.toISOString();
  const time = document.createElement("time");
  time.datetime = iso;
  time.textContent = iso;
  return time;
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
  elements.prompt.textContent = aiCapability.prompt_version || "framenest-media-suggestion-v3";
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
  if (catalogState.collection) {
    params.set("collection", catalogState.collection);
  }
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

function openPlaybackDetails(item, openerElement) {
  openDetailsDialog(item, openerElement, { playWhenReady: true });
}

function renderUnavailableCardMediaSurface(item, title) {
  const surface = document.createElement("div");
  surface.className = "media-placeholder media-placeholder--unavailable";
  surface.setAttribute("data-media-state", "unavailable");
  surface.setAttribute("aria-label", `No local playback available for ${title}`);
  const text = document.createElement("span");
  text.className = "media-placeholder__error";
  text.textContent = "Unavailable";
  surface.appendChild(text);
  return surface;
}

function renderCatalogCardMediaSurface(item) {
  const title = item.display_title || deriveCatalogFallbackTitle(item);
  const location = selectPlaybackLocation(item);
  if (!location) {
    return renderUnavailableCardMediaSurface(item, title);
  }

  const surface = document.createElement("div");
  surface.className = `media-placeholder media-placeholder--live media-placeholder--${item.media_kind}`;
  surface.setAttribute("data-media-state", "live");
  surface.setAttribute("aria-label", `Open playback for ${title}`);
  surface.title = "Open playback";

  const url = mediaContentUrl(item.media_id, location.location_id);
  const showUnavailable = () => {
    surface.replaceChildren();
    surface.className = "media-placeholder media-placeholder--unavailable";
    surface.setAttribute("data-media-state", "unavailable");
    const text = document.createElement("span");
    text.className = "media-placeholder__error";
    text.textContent = "Media unavailable.";
    surface.appendChild(text);
  };

  if (item.media_kind === "video") {
    const video = document.createElement("video");
    video.className = "media-placeholder__video";
    video.preload = "metadata";
    video.playsInline = true;
    video.autoplay = false;
    video.muted = true;
    video.controls = false;
    video.loop = false;
    video.setAttribute("aria-label", `Paused video preview for ${title}`);
    video.onerror = showUnavailable;
    cardMediaElements.add(video);
    video.src = url;
    surface.appendChild(video);
  } else {
    const img = document.createElement("img");
    img.className = "media-placeholder__image";
    img.alt = `Animated preview for ${title}`;
    img.onerror = showUnavailable;
    cardMediaElements.add(img);
    img.src = url;
    surface.appendChild(img);
  }

  const playButton = document.createElement("button");
  playButton.className = "media-placeholder__play";
  playButton.type = "button";
  playButton.textContent = "▶";
  playButton.setAttribute("aria-label", `Play ${title}`);
  playButton.addEventListener("click", (event) => {
    event.stopPropagation();
    openPlaybackDetails(item, playButton);
  });
  surface.appendChild(playButton);

  surface.addEventListener("click", () => openPlaybackDetails(item, surface));
  surface.addEventListener("keydown", (event) => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      openPlaybackDetails(item, surface);
    }
  });
  surface.setAttribute("role", "button");
  surface.setAttribute("tabindex", "0");
  return surface;
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
  card.dataset.mediaId = item.media_id;
  if (metadataWorkspace.openMediaId === item.media_id) {
    card.classList.add("catalog-card--selected");
  }

  const mediaSurface = renderCatalogCardMediaSurface(item);

  const body = document.createElement("div");
  body.className = "catalog-card__body";
  const title = document.createElement("h3");
  title.textContent = item.display_title || deriveCatalogFallbackTitle(item);
  body.appendChild(title);

  if (item.tags.length > 0) {
    const tagsDiv = document.createElement("div");
    tagsDiv.className = "catalog-card__tags";
    const maxVisible = 3;
    item.tags.slice(0, maxVisible).forEach((tag) => {
      const pill = document.createElement("span");
      pill.className = "catalog-card__tag";
      pill.textContent = tag.display_name;
      tagsDiv.appendChild(pill);
    });
    if (item.tags.length > maxVisible) {
      const more = document.createElement("span");
      more.className = "catalog-card__tag-more";
      more.textContent = `+${item.tags.length - maxVisible}`;
      tagsDiv.appendChild(more);
    }
    body.appendChild(tagsDiv);
  }

  const status = document.createElement("div");
  status.className = "catalog-card__status";
  if (item.collection_key === "processed") {
    status.classList.add("catalog-card__status--processed");
    const dot = document.createElement("span");
    dot.className = "catalog-card__status-dot";
    dot.setAttribute("aria-hidden", "true");
    status.appendChild(dot);
    const label = document.createElement("span");
    label.textContent = "Processed";
    status.appendChild(label);
    const processedTime = buildProcessedTimeElement(item.processed_at_ms);
    if (processedTime !== null) {
      status.appendChild(processedTime);
    }
  } else {
    const dot = document.createElement("span");
    dot.className = "catalog-card__status-dot";
    dot.setAttribute("aria-hidden", "true");
    status.appendChild(dot);
  }
  body.appendChild(status);

  const actions = document.createElement("div");
  actions.className = "catalog-card__actions";
  const detailsButton = document.createElement("button");
  detailsButton.className = "catalog-card__action";
  detailsButton.type = "button";
  detailsButton.textContent = "Details";
  detailsButton.setAttribute("aria-label", `Details for ${item.display_title || deriveCatalogFallbackTitle(item)}`);
  detailsButton.addEventListener("click", () => openDetailsDialog(item, detailsButton));
  const editButton = document.createElement("button");
  editButton.className = "catalog-card__action catalog-card__action--primary";
  editButton.type = "button";
  editButton.textContent = "Edit";
  editButton.setAttribute("aria-label", `Edit ${item.display_title || deriveCatalogFallbackTitle(item)}`);
  editButton.addEventListener("click", () => handleOpenMetadataWorkspace(item, editButton));
  actions.append(detailsButton, editButton);

  card.append(mediaSurface, body, actions);
  return card;
}

function renderCatalogSuccess(page) {
  cleanupCatalogCardMedia();
  catalogResults.replaceChildren();
  catalogState.total = page.total;
  catalogState.offset = page.offset;
  if (commandSearchInput) commandSearchInput.value = page.q || catalogState.q;
  renderCatalogTagFilterStates();
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

function renderCatalogTagFilterStates() {
  if (!catalogTagFilters) return;
  const buttons = catalogTagFilters.querySelectorAll(".catalog-filter-chip");
  buttons.forEach((button) => {
    const key = button.dataset.tagKey;
    const isActive = catalogState.tagKeys.includes(key);
    button.setAttribute("aria-pressed", String(isActive));
    const removeSpan = button.querySelector(".catalog-filter-chip__remove");
    if (removeSpan) {
      removeSpan.style.display = isActive ? "" : "none";
    }
  });
}

function renderCatalogTagFilters(tags) {
  canonicalTagDefinitions = tags;
  canonicalTagsLoaded = true;
  catalogTagFilters.replaceChildren();
  if (tags.length === 0) {
    if (catalogTagsState) {
      catalogTagsState.hidden = false;
      catalogTagsState.textContent = "No tags.";
    }
    return;
  }
  if (catalogTagsState) catalogTagsState.hidden = true;
  tags.forEach((tag) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "catalog-filter-chip";
    button.dataset.tagKey = tag.key;
    button.setAttribute("aria-pressed", "false");
    button.textContent = tag.display_name;
    const removeSpan = document.createElement("span");
    removeSpan.className = "catalog-filter-chip__remove";
    removeSpan.textContent = " ×";
    removeSpan.setAttribute("aria-hidden", "true");
    removeSpan.style.display = "none";
    button.appendChild(removeSpan);
    button.addEventListener("click", () => {
      if (catalogState.tagKeys.includes(tag.key)) {
        catalogState.tagKeys = catalogState.tagKeys.filter((activeKey) => activeKey !== tag.key);
      } else {
        catalogState.tagKeys = [...catalogState.tagKeys, tag.key];
      }
      catalogState.offset = 0;
      renderCatalogTagFilterStates();
      loadCatalog();
    });
    catalogTagFilters.appendChild(button);
  });
  renderCatalogTagFilterStates();
  if (metadataWorkspace.openMediaId !== null) {
    renderMetadataWorkspace();
  }
}

async function loadCatalogTags() {
  if (catalogTagsState) {
    catalogTagsState.hidden = false;
    catalogTagsState.textContent = "Loading tags...";
  }
  try {
    const response = await fetch(CANONICAL_TAGS_ENDPOINT, {
      headers: { Accept: "application/json" },
      cache: "no-store",
    });
    const payload = await response.json();
    if (!response.ok) {
      if (catalogTagsState) catalogTagsState.textContent = "Tags unavailable.";
      return false;
    }
    renderCatalogTagFilters(payload.tags || []);
    return true;
  } catch {
    if (catalogTagsState) catalogTagsState.textContent = "Tags could not be loaded.";
    return false;
  }
}

async function ensureCanonicalTags() {
  if (canonicalTagsLoaded) {
    return true;
  }
  return loadCatalogTags();
}

function setMetadataStatus(state, message) {
  metadataWorkspace.statusOverride = state;
  if (metadataStatus && message) {
    metadataStatus.textContent = message;
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
  metadataSaveButton.textContent = metadataWorkspace.saving ? "Saving..." : "Save";
  metadataSaveButton.disabled = metadataWorkspace.loading || metadataWorkspace.saving || !dirty || Boolean(validation);
  metadataDiscardButton.disabled = metadataWorkspace.saving;
  syncMetadataBeforeUnloadProtection();
  if (metadataWorkspace.loading) {
    metadataStatus.textContent = "Loading...";
  } else if (metadataWorkspace.saving) {
    metadataStatus.textContent = "Saving...";
  } else if (metadataWorkspace.statusOverride === "saving") {
    metadataStatus.textContent = metadataStatus.textContent || "Working...";
  } else if (metadataWorkspace.unavailable) {
    metadataStatus.textContent = "Catalog unavailable.";
  } else if (metadataWorkspace.notFound) {
    metadataStatus.textContent = "Medium no longer available.";
  } else if (validation) {
    metadataStatus.textContent = validation;
  } else if (metadataWorkspace.statusOverride === "validation") {
    metadataStatus.textContent = metadataStatus.textContent || "Please check this edit.";
  } else if (metadataWorkspace.statusOverride === "error") {
    metadataStatus.textContent = metadataStatus.textContent || "Save failed.";
  } else if (metadataWorkspace.statusOverride === "saved") {
    metadataStatus.textContent = "Saved.";
  } else {
    metadataStatus.textContent = "";
  }
}

function renderSelectedMetadataTags() {
  metadataSelectedTags.replaceChildren();
  metadataWorkspace.current.tagKeys.forEach((key) => {
    const definition = selectedTagDefinition(key);
    const chip = document.createElement("span");
    chip.className = "metadata-tag-chip";
    const label = document.createElement("span");
    const displayName = definition ? definition.display_name : "Tag";
    label.textContent = displayName;
    const remove = document.createElement("button");
    remove.type = "button";
    remove.textContent = "×";
    remove.setAttribute("aria-label", `Remove ${displayName}`);
    remove.addEventListener("click", () => removeSelectedMetadataTag(key));
    chip.append(label, remove);
    metadataSelectedTags.appendChild(chip);
  });
  metadataTagStatus.textContent = metadataWorkspace.current.tagKeys.length >= MAX_METADATA_TAGS ? "Tag limit reached." : "";
}

function renderMetadataTagSuggestions() {
  metadataTagSuggestions.replaceChildren();
  const displayName = normalizedTagDisplayName(metadataTagSearchInput.value);
  const query = displayName.toLocaleLowerCase();
  const matches = canonicalTagDefinitions.filter((tag) => {
    return query
      && !metadataWorkspace.current.tagKeys.includes(tag.key)
      && tag.display_name.toLocaleLowerCase().includes(query);
  });
  const exactMatch = displayName ? findTagByDisplayName(displayName) : null;
  const items = matches.map((tag) => ({ type: "select", tag, label: tag.display_name }));
  if (displayName && !exactMatch) {
    items.push({ type: "add", displayName, label: `Add “${displayName}”` });
  }
  metadataTagSuggestionState.items = items;
  if (items.length === 0) {
    metadataTagSuggestionState.activeIndex = -1;
    metadataTagSearchInput.setAttribute("aria-expanded", "false");
    return;
  }
  if (metadataTagSuggestionState.activeIndex < 0 || metadataTagSuggestionState.activeIndex >= items.length) {
    metadataTagSuggestionState.activeIndex = 0;
  }
  metadataTagSearchInput.setAttribute("aria-expanded", "true");
  items.forEach((item, index) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "metadata-tag-suggestion";
    button.id = `metadata-tag-suggestion-${index}`;
    button.setAttribute("role", "option");
    button.setAttribute("aria-selected", String(index === metadataTagSuggestionState.activeIndex));
    button.textContent = item.label;
    button.disabled = metadataWorkspace.current.tagKeys.length >= MAX_METADATA_TAGS;
    button.addEventListener("mousedown", (event) => event.preventDefault());
    button.addEventListener("click", () => activateMetadataTagSuggestion(index));
    metadataTagSuggestions.appendChild(button);
  });
}

function updateDescriptionStatus() {
  const length = unicodeCodePointLength(metadataDescriptionInput.value);
  if (length > MAX_METADATA_DESCRIPTION_CODE_POINTS) {
    metadataDescriptionStatus.hidden = false;
    metadataDescriptionStatus.textContent = `Description must be ${MAX_METADATA_DESCRIPTION_CODE_POINTS} characters or fewer.`;
    return;
  }
  metadataDescriptionStatus.hidden = true;
  metadataDescriptionStatus.textContent = "";
}

function renderMetadataWorkspace() {
  if (metadataWorkspace.openMediaId === null) {
    metadataWorkspaceElement.hidden = true;
    syncMetadataBeforeUnloadProtection();
    return;
  }
  metadataWorkspaceElement.hidden = false;
  metadataWorkspaceContext.textContent = metadataWorkspace.openItem
    ? (metadataWorkspace.openItem.display_title || deriveCatalogFallbackTitle(metadataWorkspace.openItem))
    : `Media ID ${metadataWorkspace.openMediaId}`;
  metadataTitleInput.value = metadataWorkspace.current.displayTitle || "";
  if (metadataWorkspace.baseline.displayTitle === null && metadataWorkspace.openItem) {
    metadataTitleFallback.hidden = false;
    metadataTitleFallback.textContent = `Fallback: ${deriveCatalogFallbackTitle(metadataWorkspace.openItem)}`;
  } else {
    metadataTitleFallback.hidden = true;
  }
  metadataDescriptionInput.value = metadataWorkspace.current.description || "";
  updateDescriptionStatus();

  renderSelectedMetadataTags();
  renderMetadataTagSuggestions();
  renderMetadataAiPanel();
  updateMetadataControls();
}

function metadataAiLocation() {
  if (!metadataWorkspace.openItem) return null;
  return selectPlaybackLocation(metadataWorkspace.openItem);
}

function renderMetadataAiPanel() {
  if (!metadataAiPanel) return;
  const location = metadataAiLocation();
  const available = Boolean(aiCapability.available && location);
  metadataAiCapability.textContent = aiCapability.available
    ? `${aiCapability.provider_id || "AI"} / ${aiCapability.model_id || "configured model"}`
    : "AI analysis is not configured.";
  if (aiCapability.available && !location) {
    metadataAiCapability.textContent = "AI analysis needs an available local GIF or MP4.";
  }
  metadataAiAnalyzeButton.disabled = metadataWorkspace.loading
    || metadataWorkspace.saving
    || metadataWorkspace.analyzing
    || !available;
  metadataAiLoading.hidden = !metadataWorkspace.analyzing;
  if (metadataWorkspace.aiDraft) {
    metadataAiDraft.hidden = false;
    metadataAiTitleInput.value = metadataWorkspace.aiDraft.title;
    metadataAiDescriptionInput.value = metadataWorkspace.aiDraft.description;
    metadataAiTagsInput.value = metadataWorkspace.aiDraft.tags.join(", ");
    metadataAiFilenameInput.value = metadataWorkspace.aiDraft.suggestedFilename;
  } else {
    metadataAiDraft.hidden = true;
    metadataAiTitleInput.value = "";
    metadataAiDescriptionInput.value = "";
    metadataAiTagsInput.value = "";
    metadataAiFilenameInput.value = "";
  }
}

function metadataAiDraftFromInputs() {
  const tags = metadataAiTagsInput.value
    .split(",")
    .map((tag) => normalizedTagDisplayName(tag))
    .filter((tag) => tag.length > 0);
  return {
    title: metadataAiTitleInput.value.trim(),
    description: metadataAiDescriptionInput.value.trim(),
    tags,
    suggestedFilename: metadataAiFilenameInput.value.trim(),
  };
}

function storeMetadataAiDraftFromInputs() {
  if (!metadataWorkspace.aiDraft) return;
  metadataWorkspace.aiDraft = metadataAiDraftFromInputs();
  metadataWorkspace.aiDraftDirty = true;
}

function aiSuggestionFromPayload(payload) {
  const suggestion = payload.suggestion || {};
  return {
    title: String(suggestion.title || ""),
    description: String(suggestion.description || ""),
    tags: Array.isArray(suggestion.tags) ? suggestion.tags.map((tag) => String(tag)) : [],
    suggestedFilename: String(suggestion.suggested_filename || ""),
  };
}

function confirmDiscardEditedAiDraft() {
  if (!metadataWorkspace.aiDraft || !metadataWorkspace.aiDraftDirty) {
    return true;
  }
  return confirm("Discard the edited AI Draft?");
}

async function handleAnalyzeMetadataByAi() {
  if (!aiCapability.available) {
    metadataAiStatus.textContent = "AI analysis is not configured.";
    return;
  }
  if (!confirmDiscardEditedAiDraft()) return;
  const location = metadataAiLocation();
  if (!location) {
    metadataAiStatus.textContent = "AI analysis needs an available local GIF or MP4.";
    return;
  }
  const provider = aiCapability.provider_id || "configured provider";
  const model = aiCapability.model_id || "configured model";
  const accepted = confirm(
    `FrameNest will send up to 3 optimized preview frames and limited media metadata to NVIDIA for analysis using ${provider} / ${model}. The original media file, local path, and API key are not uploaded.`,
  );
  if (!accepted) {
    metadataAiStatus.textContent = "AI analysis cancelled.";
    return;
  }
  const token = ++metadataAiRequestToken;
  metadataWorkspace.analyzing = true;
  metadataWorkspace.aiDraft = null;
  metadataWorkspace.aiDraftDirty = false;
  metadataAiStatus.textContent = "Analyzing media...";
  renderMetadataAiPanel();
  try {
    const response = await fetch(mediaAiSuggestionEndpoint(metadataWorkspace.openMediaId, location.location_id), {
      method: "POST",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ confirm_cloud_upload: true }),
      cache: "no-store",
    });
    const payload = await response.json();
    if (token !== metadataAiRequestToken || metadataWorkspace.openMediaId === null) return;
    metadataWorkspace.analyzing = false;
    if (!response.ok) {
      metadataAiStatus.textContent = aiSuggestionErrorMessage(payload);
      renderMetadataAiPanel();
      return;
    }
    metadataWorkspace.aiDraft = aiSuggestionFromPayload(payload);
    metadataWorkspace.aiDraftDirty = false;
    metadataAiStatus.textContent = "AI Draft ready. Review before using it.";
    renderMetadataAiPanel();
  } catch {
    if (token === metadataAiRequestToken) {
      metadataWorkspace.analyzing = false;
      metadataAiStatus.textContent = "AI analysis failed.";
      renderMetadataAiPanel();
    }
  }
}

function aiSuggestionErrorMessage(payload) {
  const code = payload && payload.error ? payload.error.code : "";
  if (code === "AI_PROVIDER_NOT_CONFIGURED") return "AI analysis is not configured.";
  if (code === "CLOUD_CONFIRMATION_REQUIRED") return "AI analysis needs confirmation.";
  if (code === "MEDIA_PREPARATION_UNAVAILABLE") return "This media cannot be analyzed locally.";
  if (code === "AI_PROVIDER_AUTHENTICATION_FAILED") return "AI provider authentication was rejected.";
  if (code === "AI_PROVIDER_RATE_LIMITED") return "AI provider rate limit was reached.";
  if (code === "AI_PROVIDER_INVALID_RESPONSE") return "AI response was invalid.";
  if (code === "AI_PROVIDER_UNAVAILABLE") return "AI provider is not available.";
  return "AI analysis failed.";
}

async function ensureMetadataTagKey(displayName) {
  const normalized = normalizedTagDisplayName(displayName);
  const validation = tagDisplayNameError(normalized);
  if (validation) throw new Error(validation);
  const existing = findTagByDisplayName(normalized);
  if (existing) return existing.key;
  const key = uniqueTagKeyForDisplayName(normalized);
  if (!key) throw new Error("Tag could not be added.");
  const response = await fetch(CANONICAL_TAGS_ENDPOINT, {
    method: "POST",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ key, display_name: normalized }),
    cache: "no-store",
  });
  const payload = await response.json();
  if (!response.ok) throw new Error("Tag could not be added.");
  await loadCatalogTags();
  return payload.tag.key;
}

async function handleUseMetadataAiDraft() {
  if (!metadataWorkspace.aiDraft) return;
  const draft = metadataAiDraftFromInputs();
  const folded = new Set();
  const tagNames = [];
  for (const tag of draft.tags) {
    const key = tag.toLocaleLowerCase();
    if (!folded.has(key)) {
      folded.add(key);
      tagNames.push(tag);
    }
  }
  if (tagNames.length > MAX_METADATA_TAGS) {
    metadataAiStatus.textContent = "Tag limit reached.";
    return;
  }
  try {
    const tagKeys = [];
    for (const tag of tagNames) {
      const key = await ensureMetadataTagKey(tag);
      if (!tagKeys.includes(key)) tagKeys.push(key);
    }
    metadataWorkspace.current.displayTitle = draft.title;
    metadataWorkspace.current.description = draft.description;
    metadataWorkspace.current.tagKeys = tagKeys.slice(0, MAX_METADATA_TAGS);
    metadataWorkspace.statusOverride = null;
    metadataWorkspace.aiDraft = draft;
    metadataWorkspace.aiDraftDirty = false;
    metadataAiStatus.textContent = "Draft copied into the editor. Save when ready.";
    renderMetadataWorkspace();
  } catch {
    metadataAiStatus.textContent = "Draft could not be applied. Manual edits are unchanged.";
    metadataWorkspace.aiDraft = draft;
    metadataWorkspace.aiDraftDirty = true;
    renderMetadataAiPanel();
  }
}

function handleDiscardMetadataAiDraft() {
  metadataWorkspace.aiDraft = null;
  metadataWorkspace.aiDraftDirty = false;
  metadataAiStatus.textContent = "AI Draft discarded.";
  renderMetadataAiPanel();
}

function applyMetadataPayloadToWorkspace(payload) {
  const tagKeys = (payload.tags || []).map((tag) => tag.key);
  const collectionKey = payload.collection_key ?? null;
  const processedAtMs = payload.processed_at_ms ?? null;
  metadataWorkspace.baseline = {
    displayTitle: payload.display_title === null ? null : payload.display_title,
    description: payload.description === null ? null : payload.description,
    tagKeys,
    collectionKey,
    processedAtMs,
  };
  metadataWorkspace.current = {
    displayTitle: payload.display_title === null ? "" : payload.display_title,
    description: payload.description === null ? "" : payload.description,
    tagKeys: [...tagKeys],
    collectionKey,
    processedAtMs,
  };
}

function openDetailsDialog(item, openerElement, { playWhenReady = false } = {}) {
  if (!detailsDialog) return;
  if (metadataWorkspace.openMediaId !== null) {
    if (!confirmDiscardDirtyMetadata()) return;
    closeMetadataWorkspace();
  }
  stopCardPreviewTimer();
  cleanupDetailsMedia();
  detailsOpenerElement = openerElement || document.activeElement;
  detailsCurrentItem = item;
  detailsPlayRequested = playWhenReady;
  detailsLoading.hidden = false;
  detailsError.hidden = true;
  detailsContent.hidden = true;
  if (typeof detailsDialog.showModal === "function") {
    detailsDialog.showModal();
  } else {
    detailsDialog.setAttribute("open", "");
  }
  detailsCloseButton.focus();
  populateDetailsDialog(item);
}

async function populateDetailsDialog(item) {
  const token = ++detailsMetadataToken;
  try {
    const response = await fetch(metadataEndpoint(item.media_id), {
      headers: { Accept: "application/json" },
      cache: "no-store",
    });
    if (token !== detailsMetadataToken) return;
    const payload = await response.json();
    if (token !== detailsMetadataToken) return;
    if (!response.ok) {
      detailsLoading.hidden = true;
      detailsError.hidden = false;
      return;
    }
    detailsLoading.hidden = true;
    detailsContent.hidden = false;

    renderDetailsMedia(item, { playWhenReady: detailsPlayRequested });

    if (detailsDialogTitle) {
      detailsDialogTitle.textContent = item.display_title || deriveCatalogFallbackTitle(item);
    }
    detailsKind.textContent = formatCatalogKind(item.media_kind);

    detailsTagsContainer.replaceChildren();
    (item.tags || []).forEach((tag) => {
      const pill = document.createElement("span");
      pill.className = "media-details-dialog__tag";
      pill.textContent = tag.display_name;
      detailsTagsContainer.appendChild(pill);
    });

    if (item.collection_key === "processed" || payload.collection_key === "processed") {
      detailsProcessedContainer.hidden = false;
      detailsProcessedContainer.replaceChildren();
      const label = document.createTextNode("Processed");
      detailsProcessedContainer.appendChild(label);
      const processedTime = buildProcessedTimeElement(item.processed_at_ms ?? payload.processed_at_ms);
      if (processedTime !== null) {
        detailsProcessedContainer.appendChild(document.createTextNode(" since "));
        detailsProcessedContainer.appendChild(processedTime);
      }
    } else {
      detailsProcessedContainer.hidden = true;
    }

    detailsDescription.textContent = payload.description || "";
    if (!payload.description) {
      detailsDescription.hidden = true;
    } else {
      detailsDescription.hidden = false;
    }

    detailsTechnicalList.replaceChildren();
    if (detailsTechnical) {
      detailsTechnical.removeAttribute("open");
    }
    addMetadataValue(detailsTechnicalList, "Media ID", item.media_id);
    addMetadataValue(detailsTechnicalList, "Kind", formatCatalogKind(item.media_kind));
    addMetadataValue(detailsTechnicalList, "Created", new Date(item.created_at_ms).toISOString());
    addMetadataValue(detailsTechnicalList, "Collection", item.collection_key || "none");
    if (item.processed_at_ms !== null && item.processed_at_ms !== undefined) {
      addMetadataValue(detailsTechnicalList, "Processed at", new Date(item.processed_at_ms).toISOString());
    }
    item.locations.forEach((location, index) => {
      addMetadataValue(detailsTechnicalList, `Location ${index + 1}`, location.relative_path);
      addMetadataValue(detailsTechnicalList, `Availability ${index + 1}`, location.availability);
    });
  } catch {
    if (token === detailsMetadataToken) {
      detailsLoading.hidden = true;
      detailsError.hidden = false;
    }
  }
}

function closeDetailsDialog() {
  if (!detailsDialog) return;
  cleanupDetailsMedia();
  if (typeof detailsDialog.close === "function") {
    detailsDialog.close();
  } else {
    detailsDialog.removeAttribute("open");
  }
  detailsCurrentItem = null;
  detailsPlayRequested = false;
  detailsMetadataToken++;
  if (detailsOpenerElement) {
    detailsOpenerElement.focus();
    detailsOpenerElement = null;
  }
}

async function handleOpenMetadataWorkspace(item, openerElement) {
  if (!confirmDiscardDirtyMetadata()) {
    return;
  }
  if (detailsDialog && detailsDialog.hasAttribute("open")) {
    closeDetailsDialog();
  }
  metadataOpenerElement = openerElement || document.activeElement;
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
    analyzing: false,
    aiDraft: null,
    aiDraftDirty: false,
    baseline: { displayTitle: null, description: null, tagKeys: [], collectionKey: null, processedAtMs: null },
    current: { displayTitle: "", description: "", tagKeys: [], collectionKey: null, processedAtMs: null },
  };
  metadataStatus.textContent = "";
  metadataValidationMessage.textContent = "";
  metadataAiStatus.textContent = "";
  metadataTagSearchInput.value = "";
  metadataTagSuggestionState = { items: [], activeIndex: -1 };
  if (metadataDialog && typeof metadataDialog.showModal === "function") {
    metadataDialog.showModal();
  }
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
    metadataTagSearchInput.value = "";
    renderMetadataTagSuggestions();
    return;
  }
  if (metadataWorkspace.current.tagKeys.length >= MAX_METADATA_TAGS) {
    setMetadataStatus("validation", "Tag limit reached.");
    updateMetadataControls();
    return;
  }
  metadataWorkspace.current.tagKeys = [...metadataWorkspace.current.tagKeys, key];
  metadataWorkspace.statusOverride = null;
  metadataTagSearchInput.value = "";
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
    description: metadataWorkspace.baseline.description || "",
    tagKeys: [...metadataWorkspace.baseline.tagKeys],
    collectionKey: metadataWorkspace.baseline.collectionKey,
    processedAtMs: metadataWorkspace.baseline.processedAtMs,
  };
  metadataWorkspace.statusOverride = null;
  renderMetadataWorkspace();
}

function handleDiscardMetadataChanges() {
  closeMetadataWorkspace();
}

function closeMetadataWorkspace() {
  if (!confirmDiscardDirtyMetadata()) {
    return;
  }
  metadataRequestToken += 1;
  metadataAiRequestToken += 1;
  metadataWorkspace = {
    openMediaId: null,
    openItem: null,
    loading: false,
    saving: false,
    unavailable: false,
    notFound: false,
    statusOverride: null,
    analyzing: false,
    aiDraft: null,
    aiDraftDirty: false,
    baseline: { displayTitle: null, description: null, tagKeys: [], collectionKey: null, processedAtMs: null },
    current: { displayTitle: "", description: "", tagKeys: [], collectionKey: null, processedAtMs: null },
  };
  metadataWorkspaceElement.hidden = true;
  metadataStatus.textContent = "";
  metadataValidationMessage.textContent = "";
  metadataAiStatus.textContent = "";
  metadataTagSearchInput.value = "";
  metadataTagSuggestionState = { items: [], activeIndex: -1 };
  metadataTagSuggestions.replaceChildren();
  metadataTagSearchInput.setAttribute("aria-expanded", "false");
  if (metadataDialog && typeof metadataDialog.close === "function") {
    metadataDialog.close();
  }
  syncMetadataBeforeUnloadProtection();
  if (metadataOpenerElement) {
    metadataOpenerElement.focus();
    metadataOpenerElement = null;
  }
  loadCatalog();
}

async function createAndSelectMetadataTag(displayName) {
  const validation = tagDisplayNameError(displayName);
  if (validation) {
    setMetadataStatus("validation", validation);
    updateMetadataControls();
    return;
  }
  const existing = findTagByDisplayName(displayName);
  if (existing) {
    selectMetadataTag(existing.key);
    return;
  }
  const key = uniqueTagKeyForDisplayName(displayName);
  if (!key) {
    setMetadataStatus("validation", "Use at least one English letter or number in the tag name.");
    updateMetadataControls();
    return;
  }
  setMetadataStatus("saving", "Adding tag...");
  updateMetadataControls();
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
      selectMetadataTag(payload.tag.key);
      return;
    }
    const code = payload.error ? payload.error.code : "";
    if (code === "CANONICAL_TAG_DEFINITION_CONFLICT") {
      await loadCatalogTags();
      setMetadataStatus("validation", "That tag could not be added. Try a different name.");
      updateMetadataControls();
      return;
    }
    if (code === "CATALOG_UNAVAILABLE") {
      setMetadataStatus("unavailable", "The local catalog is not available. Unsaved edits are preserved.");
      updateMetadataControls();
      return;
    }
    setMetadataStatus("error", "Tag could not be added.");
    updateMetadataControls();
  } catch {
    setMetadataStatus("error", "Tag could not be added.");
    updateMetadataControls();
  }
}

function activateMetadataTagSuggestion(index) {
  const item = metadataTagSuggestionState.items[index];
  if (!item) return;
  if (metadataWorkspace.current.tagKeys.length >= MAX_METADATA_TAGS) {
    setMetadataStatus("validation", "Tag limit reached.");
    updateMetadataControls();
    return;
  }
  if (item.type === "select") {
    selectMetadataTag(item.tag.key);
    return;
  }
  createAndSelectMetadataTag(item.displayName);
}

function handleMetadataTagSearchKeydown(event) {
  if (event.key === "ArrowDown") {
    event.preventDefault();
    if (metadataTagSuggestionState.items.length === 0) {
      renderMetadataTagSuggestions();
      return;
    }
    metadataTagSuggestionState.activeIndex = Math.min(
      metadataTagSuggestionState.activeIndex + 1,
      metadataTagSuggestionState.items.length - 1,
    );
    renderMetadataTagSuggestions();
    return;
  }
  if (event.key === "ArrowUp") {
    event.preventDefault();
    if (metadataTagSuggestionState.items.length === 0) {
      renderMetadataTagSuggestions();
      return;
    }
    metadataTagSuggestionState.activeIndex = Math.max(metadataTagSuggestionState.activeIndex - 1, 0);
    renderMetadataTagSuggestions();
    return;
  }
  if (event.key === "Escape") {
    if (metadataTagSuggestionState.items.length > 0) {
      event.stopPropagation();
    }
    metadataTagSuggestionState = { items: [], activeIndex: -1 };
    metadataTagSuggestions.replaceChildren();
    metadataTagSearchInput.setAttribute("aria-expanded", "false");
    return;
  }
  if (event.key === "Enter") {
    event.preventDefault();
    const displayName = normalizedTagDisplayName(metadataTagSearchInput.value);
    const exactMatch = displayName ? findTagByDisplayName(displayName) : null;
    if (exactMatch && !metadataWorkspace.current.tagKeys.includes(exactMatch.key)) {
      selectMetadataTag(exactMatch.key);
      return;
    }
    if (metadataTagSuggestionState.activeIndex >= 0) {
      activateMetadataTagSuggestion(metadataTagSuggestionState.activeIndex);
      return;
    }
    if (displayName) {
      createAndSelectMetadataTag(displayName);
    }
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
  setMetadataStatus("saving", "Saving...");
  updateMetadataControls();
  try {
    const mediaId = metadataWorkspace.openMediaId;
    const response = await fetch(metadataEndpoint(mediaId), {
      method: "PUT",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ display_title: normalized.displayTitle, description: normalized.description, tag_keys: normalized.tagKeys }),
      cache: "no-store",
    });
    const payload = await response.json();
    metadataWorkspace.saving = false;
    if (response.ok) {
      applyMetadataPayloadToWorkspace(payload.metadata);
      setMetadataStatus("saved", "Saved.");
      renderMetadataWorkspace();
      await loadCatalog();
      return;
    }
    const code = payload.error ? payload.error.code : "";
    if (code === "CANONICAL_TAG_NOT_FOUND") {
      await loadCatalogTags();
      setMetadataStatus("validation", "One selected tag is no longer available. Update the tags before retrying.");
    } else if (code === "MEDIA_NOT_FOUND") {
      metadataWorkspace.notFound = true;
      setMetadataStatus("notFound", "The selected medium is no longer available.");
      await loadCatalog();
    } else if (code === "CATALOG_UNAVAILABLE") {
      metadataWorkspace.unavailable = true;
      setMetadataStatus("unavailable", "The local catalog is not available. Unsaved edits are preserved.");
    } else {
      setMetadataStatus("error", "Save failed.");
    }
    updateMetadataControls();
  } catch {
    metadataWorkspace.saving = false;
    setMetadataStatus("error", "Save failed.");
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
  status.textContent = "Scanning...";
  try {
    const response = await fetch(`${LIBRARIES_ENDPOINT}/${library.id}/scan-preview`, {
      method: "POST",
      headers: { Accept: "application/json" },
      cache: "no-store",
    });
    const payload = await response.json();
    if (!response.ok) {
      status.textContent = "Scan failed.";
      return;
    }
    renderScanResult(card, payload);
  } catch {
    status.textContent = "Scan failed.";
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

function setCatalogScope(collection) {
  catalogState.collection = collection;
  catalogState.offset = 0;
  const allButton = document.querySelector("#catalog-scope-all");
  const processedButton = document.querySelector("#catalog-scope-processed");
  if (allButton && processedButton) {
    allButton.classList.toggle("scope-active", collection === "");
    processedButton.classList.toggle("scope-active", collection === PROCESSED_COLLECTION);
  }
  loadCatalog();
}

document.querySelector("#catalog-scope-all").addEventListener("click", () => {
  if (!confirmDiscardDirtyMetadata()) {
    return;
  }
  if (metadataWorkspace.openMediaId !== null) {
    closeMetadataWorkspace();
  }
  setCatalogScope("");
});

document.querySelector("#catalog-scope-processed").addEventListener("click", () => {
  if (!confirmDiscardDirtyMetadata()) {
    return;
  }
  if (metadataWorkspace.openMediaId !== null) {
    closeMetadataWorkspace();
  }
  setCatalogScope(PROCESSED_COLLECTION);
});

let commandSearchDebounceTimer = null;
let commandSearchRequestToken = 0;
let commandSearchActiveIndex = -1;
let commandSearchCurrentSuggestions = [];

function closeCommandSearchSuggestions() {
  if (!commandSearchSuggestions) return;
  commandSearchSuggestions.hidden = true;
  commandSearchSuggestions.replaceChildren();
  commandSearchInput.setAttribute("aria-expanded", "false");
  commandSearchActiveIndex = -1;
  commandSearchCurrentSuggestions = [];
}

function renderCommandSearchSuggestions(titleItems, tagMatches, fallbackItems) {
  if (!commandSearchSuggestions) return;
  const hasRealSuggestions = (titleItems && titleItems.length > 0) || (tagMatches && tagMatches.length > 0) || (fallbackItems && fallbackItems.length > 0);
  if (!hasRealSuggestions) {
    closeCommandSearchSuggestions();
    return;
  }
  commandSearchSuggestions.replaceChildren();
  commandSearchCurrentSuggestions = [];
  const maxTitles = 5;
  const maxTags = 5;
  const maxFallback = 3;
  let count = 0;
  titleItems.forEach((item) => {
    if (count >= maxTitles) return;
    const li = document.createElement("li");
    li.className = "command-search-suggestion";
    li.setAttribute("role", "option");
    li.dataset.suggestionType = "title";
    li.dataset.suggestionMediaId = item.media_id;
    const typeSpan = document.createElement("span");
    typeSpan.className = "command-search-suggestion__type";
    typeSpan.textContent = "Title";
    const labelSpan = document.createElement("span");
    labelSpan.className = "command-search-suggestion__label";
    labelSpan.textContent = item.display_title || item.media_id;
    li.appendChild(typeSpan);
    li.appendChild(labelSpan);
    li.addEventListener("click", () => {
      commandSearchInput.value = item.display_title || "";
      catalogState.q = item.display_title || "";
      catalogState.offset = 0;
      closeCommandSearchSuggestions();
      loadCatalog();
    });
    commandSearchSuggestions.appendChild(li);
    commandSearchCurrentSuggestions.push(li);
    count++;
  });
  if (fallbackItems) {
    fallbackItems.forEach((item) => {
      if (commandSearchCurrentSuggestions.length >= maxTitles + maxFallback) return;
      const li = document.createElement("li");
      li.className = "command-search-suggestion";
      li.setAttribute("role", "option");
      li.dataset.suggestionType = "title";
      li.dataset.suggestionMediaId = item.media_id;
      const typeSpan = document.createElement("span");
      typeSpan.className = "command-search-suggestion__type";
      typeSpan.textContent = "File";
      const labelSpan = document.createElement("span");
      labelSpan.className = "command-search-suggestion__label";
      labelSpan.textContent = deriveCatalogFallbackTitle(item);
      li.appendChild(typeSpan);
      li.appendChild(labelSpan);
      li.addEventListener("click", () => {
        closeCommandSearchSuggestions();
        const card = document.querySelector(`[data-media-id="${item.media_id}"]`);
        if (card) {
          card.scrollIntoView({ block: "center", behavior: "smooth" });
          card.classList.add("catalog-card--flash");
          setTimeout(() => card.classList.remove("catalog-card--flash"), 1500);
        }
      });
      commandSearchSuggestions.appendChild(li);
      commandSearchCurrentSuggestions.push(li);
    });
  }
  tagMatches.forEach((tag) => {
    if (commandSearchCurrentSuggestions.length >= maxTitles + maxTags + maxFallback) return;
    const li = document.createElement("li");
    li.className = "command-search-suggestion";
    li.setAttribute("role", "option");
    li.dataset.suggestionType = "tag";
    li.dataset.suggestionTagKey = tag.key;
    const typeSpan = document.createElement("span");
    typeSpan.className = "command-search-suggestion__type";
    typeSpan.textContent = "Tag";
    const labelSpan = document.createElement("span");
    labelSpan.className = "command-search-suggestion__label";
    labelSpan.textContent = tag.display_name;
    li.appendChild(typeSpan);
    li.appendChild(labelSpan);
    li.addEventListener("click", () => {
      if (!catalogState.tagKeys.includes(tag.key)) {
        catalogState.tagKeys = [...catalogState.tagKeys, tag.key];
        catalogState.offset = 0;
        renderCatalogTagFilterStates();
        loadCatalog();
      }
      commandSearchInput.value = "";
      closeCommandSearchSuggestions();
    });
    commandSearchSuggestions.appendChild(li);
    commandSearchCurrentSuggestions.push(li);
  });
  commandSearchSuggestions.hidden = false;
  commandSearchInput.setAttribute("aria-expanded", "true");
  commandSearchActiveIndex = -1;
}

function updateSuggestionActiveState() {
  commandSearchCurrentSuggestions.forEach((li, index) => {
    li.classList.toggle("command-search-suggestion--active", index === commandSearchActiveIndex);
  });
  if (commandSearchActiveIndex >= 0 && commandSearchCurrentSuggestions[commandSearchActiveIndex]) {
    commandSearchCurrentSuggestions[commandSearchActiveIndex].scrollIntoView({ block: "nearest" });
  }
}

async function performCommandSearch(query) {
  if (!query || query.trim().length === 0) {
    closeCommandSearchSuggestions();
    return;
  }
  const token = ++commandSearchRequestToken;
  const lowerQuery = query.toLowerCase();
  const tagMatches = canonicalTagDefinitions
    .filter((tag) =>
      tag.key.toLowerCase().includes(lowerQuery) ||
      tag.display_name.toLowerCase().includes(lowerQuery)
    )
    .slice(0, 5);
  const fallbackMatches = [];
  const cardElements = catalogResults.querySelectorAll(".catalog-card");
  cardElements.forEach((card) => {
    const mediaId = card.dataset.mediaId;
    if (!mediaId) return;
    const titleEl = card.querySelector("h3");
    if (!titleEl) return;
    const title = titleEl.textContent || "";
    if (title.toLowerCase().includes(lowerQuery)) {
      fallbackMatches.push({ media_id: mediaId, _fallbackTitle: title });
    }
  });
  try {
    const params = new URLSearchParams();
    params.set("q", query);
    params.set("limit", "5");
    params.set("offset", "0");
    const response = await fetch(`${MEDIA_CATALOG_ENDPOINT}?${params.toString()}`, {
      headers: { Accept: "application/json" },
      cache: "no-store",
    });
    if (token !== commandSearchRequestToken) return;
    if (!response.ok) {
      renderCommandSearchSuggestions([], tagMatches, fallbackMatches.slice(0, 3));
      return;
    }
    const payload = await response.json();
    if (token !== commandSearchRequestToken) return;
    const titleItems = (payload.items || []).filter((item) => item.display_title);
    const filteredFallback = fallbackMatches.filter((fm) =>
      !titleItems.some((ti) => ti.media_id === fm.media_id)
    ).slice(0, 3);
    renderCommandSearchSuggestions(titleItems, tagMatches, filteredFallback);
  } catch {
    if (token !== commandSearchRequestToken) return;
    renderCommandSearchSuggestions([], tagMatches, fallbackMatches.slice(0, 3));
  }
}

if (commandSearchInput) {
  commandSearchInput.addEventListener("input", () => {
    if (commandSearchClear) commandSearchClear.hidden = commandSearchInput.value.length === 0;
    if (commandSearchDebounceTimer) clearTimeout(commandSearchDebounceTimer);
    const query = commandSearchInput.value;
    if (query.trim().length === 0) {
      closeCommandSearchSuggestions();
      return;
    }
    commandSearchDebounceTimer = setTimeout(() => {
      performCommandSearch(query);
    }, 200);
  });

  commandSearchInput.addEventListener("keydown", (event) => {
    if (event.key === "ArrowDown") {
      event.preventDefault();
      if (commandSearchCurrentSuggestions.length === 0) return;
      commandSearchActiveIndex = Math.min(commandSearchActiveIndex + 1, commandSearchCurrentSuggestions.length - 1);
      updateSuggestionActiveState();
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      if (commandSearchCurrentSuggestions.length === 0) return;
      commandSearchActiveIndex = Math.max(commandSearchActiveIndex - 1, -1);
      updateSuggestionActiveState();
    } else if (event.key === "Enter") {
      if (commandSearchActiveIndex >= 0 && commandSearchCurrentSuggestions[commandSearchActiveIndex]) {
        event.preventDefault();
        commandSearchCurrentSuggestions[commandSearchActiveIndex].click();
      } else {
        catalogState.q = commandSearchInput.value;
        catalogState.offset = 0;
        closeCommandSearchSuggestions();
        loadCatalog();
      }
    } else if (event.key === "Escape") {
      closeCommandSearchSuggestions();
    }
  });

  commandSearchInput.addEventListener("blur", () => {
    setTimeout(() => {
      closeCommandSearchSuggestions();
    }, 150);
  });
}

if (commandSearchClear) {
  commandSearchClear.addEventListener("click", () => {
    commandSearchInput.value = "";
    commandSearchClear.hidden = true;
    catalogState.q = "";
    catalogState.offset = 0;
    closeCommandSearchSuggestions();
    loadCatalog();
    commandSearchInput.focus();
  });
}

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

metadataTagSearchInput.addEventListener("input", () => {
  metadataTagSuggestionState.activeIndex = -1;
  renderMetadataTagSuggestions();
});
metadataTagSearchInput.addEventListener("keydown", handleMetadataTagSearchKeydown);
metadataTagSearchInput.addEventListener("blur", () => {
  window.setTimeout(() => {
    metadataTagSuggestionState = { items: [], activeIndex: -1 };
    metadataTagSuggestions.replaceChildren();
    metadataTagSearchInput.setAttribute("aria-expanded", "false");
  }, 120);
});
metadataDescriptionInput.addEventListener("input", () => {
  metadataWorkspace.current.description = metadataDescriptionInput.value;
  metadataWorkspace.statusOverride = null;
  updateDescriptionStatus();
  updateMetadataControls();
});
metadataSaveButton.addEventListener("click", handleSaveMetadata);
metadataDiscardButton.addEventListener("click", handleDiscardMetadataChanges);
metadataAiAnalyzeButton.addEventListener("click", handleAnalyzeMetadataByAi);
metadataAiUseButton.addEventListener("click", handleUseMetadataAiDraft);
metadataAiDiscardButton.addEventListener("click", handleDiscardMetadataAiDraft);
[metadataAiTitleInput, metadataAiDescriptionInput, metadataAiTagsInput, metadataAiFilenameInput].forEach((input) => {
  input.addEventListener("input", storeMetadataAiDraftFromInputs);
});

function openSettingsDialog() {
  if (!settingsDialog) return;
  lastFocusedElementBeforeSettings = document.activeElement;
  if (typeof settingsDialog.showModal === "function") {
    settingsDialog.showModal();
  } else {
    settingsDialog.setAttribute("open", "");
  }
  settingsCloseButton.focus();
}

function closeSettingsDialog() {
  if (!settingsDialog) return;
  if (typeof settingsDialog.close === "function") {
    settingsDialog.close();
  } else {
    settingsDialog.removeAttribute("open");
  }
  if (lastFocusedElementBeforeSettings) {
    lastFocusedElementBeforeSettings.focus();
    lastFocusedElementBeforeSettings = null;
  } else {
    aiStatusButton.focus();
  }
}

if (serverHealthButton) {
  serverHealthButton.addEventListener("click", () => {
    retryHealth();
  });
}

if (aiStatusButton) {
  aiStatusButton.addEventListener("click", () => {
    openSettingsDialog();
  });
}

if (settingsCloseButton) {
  settingsCloseButton.addEventListener("click", () => {
    closeSettingsDialog();
  });
}

if (settingsDialog) {
  settingsDialog.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      event.preventDefault();
      closeSettingsDialog();
    }
  });
  settingsDialog.addEventListener("click", (event) => {
    if (event.target === settingsDialog) {
      closeSettingsDialog();
    }
  });
}

if (detailsCloseButton) {
  detailsCloseButton.addEventListener("click", () => closeDetailsDialog());
}

if (detailsDialog) {
  detailsDialog.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      event.preventDefault();
      closeDetailsDialog();
    }
  });
  detailsDialog.addEventListener("click", (event) => {
    if (event.target === detailsDialog) {
      closeDetailsDialog();
    }
  });
}

if (detailsEditButton) {
  detailsEditButton.addEventListener("click", () => {
    if (detailsCurrentItem) {
      const item = detailsCurrentItem;
      closeDetailsDialog();
      handleOpenMetadataWorkspace(item, null);
    }
  });
}

if (metadataDialog) {
  metadataDialog.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      event.preventDefault();
      closeMetadataWorkspace();
    }
  });
  metadataDialog.addEventListener("click", (event) => {
    if (event.target === metadataDialog) {
      closeMetadataWorkspace();
    }
  });
}

if (metadataCloseButton) {
  metadataCloseButton.addEventListener("click", () => closeMetadataWorkspace());
}

checkHealth();
loadAiCapability();
loadCatalogTags();
loadCatalog();
loadLibraries();
if (commandSearchInput) {
  commandSearchInput.focus({ preventScroll: true });
}
window.addEventListener("pagehide", revokePreviewObjectUrls);
