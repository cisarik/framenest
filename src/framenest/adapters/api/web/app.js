"use strict";

const HEALTH_ENDPOINT = "/health";
const LIBRARIES_ENDPOINT = "/api/libraries";
let analysisRequestToken = 0;
let previewObjectUrls = [];

const statusContainer = document.querySelector("#server-status");
const statusText = document.querySelector("#server-status-text");
const statusDetail = document.querySelector("#server-status-detail");
const libraryList = document.querySelector("#library-list");
const libraryStateLoading = document.querySelector("#library-state-loading");
const libraryStateEmpty = document.querySelector("#library-state-empty");
const libraryStateUnavailable = document.querySelector("#library-state-unavailable");
const libraryStateError = document.querySelector("#library-state-error");
const libraryCardTemplate = document.querySelector("#library-card-template");

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

function showLibraryState(state) {
  libraryStateLoading.hidden = state !== "loading";
  libraryStateEmpty.hidden = state !== "empty";
  libraryStateUnavailable.hidden = state !== "unavailable";
  libraryStateError.hidden = state !== "error";
  libraryList.hidden = state !== "success";
}

function appendText(parent, value) {
  parent.appendChild(document.createTextNode(String(value)));
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

function setLocalPreviewState(card, state, message) {
  const elements = previewElements(card);
  elements.preview.hidden = false;
  elements.preview.dataset.state = state;
  elements.status.textContent = message;
}

function resetLocalPreview(card) {
  revokePreviewObjectUrls();
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

function renderAnalysisSuccess(card, payload) {
  if (!payload.representative_frames || payload.representative_frames.length === 0) {
    renderGenericPreviewError(card);
    return;
  }
  revokePreviewObjectUrls();
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
      row.append(path, kind, detail, inspect);
      candidates.appendChild(row);
    });
  }

  summaryList.hidden = false;
  candidates.hidden = false;
  status.textContent = "Read-only scan preview complete. Candidates are not persisted catalog media.";
}

async function handleInspectClick(libraryId, candidate, card) {
  const token = analysisRequestToken + 1;
  analysisRequestToken = token;
  const elements = previewElements(card);
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

checkHealth();
loadLibraries();
window.addEventListener("beforeunload", revokePreviewObjectUrls);
