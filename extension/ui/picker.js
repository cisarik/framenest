(function () {
  const companion = globalThis.FrameNestCompanion;
  const pickerStatus = document.getElementById("picker-status");
  const search = document.getElementById("search");
  const preview = document.getElementById("preview");
  const previewTitle = document.getElementById("preview-title");
  const previewMedia = document.getElementById("preview-media");
  const previewPrev = document.getElementById("preview-prev");
  const previewNext = document.getElementById("preview-next");
  const attachSelected = document.getElementById("attach-selected");
  const previewNav = document.getElementById("preview-nav");
  let items = [];
  let selectedIndex = 0;
  let connected = false;
  let previewToken = 0;
  let queryToken = 0;
  let lastLayoutCompact = null;

  function setText(node, value) {
    node.textContent = value;
  }

  function disconnectedStatus() {
    return "Connect FrameNest in the side panel";
  }

  function trimmedQuery() {
    return (search.value || "").trim();
  }

  function request(type, payload) {
    return new Promise((resolve) => {
      chrome.runtime.sendMessage(
        { v: companion.PROTOCOL, type, payload: payload || {} },
        (response) => {
          if (chrome.runtime.lastError) {
            resolve({ ok: false, error: "extension_unavailable" });
            return;
          }
          resolve(response || { ok: false, error: "empty_response" });
        }
      );
    });
  }

  function selectedItem() {
    if (!items.length || selectedIndex < 0 || selectedIndex >= items.length) {
      return null;
    }
    return items[selectedIndex];
  }

  function clearPreviewMedia() {
    previewMedia.removeAttribute("src");
    previewMedia.hidden = true;
  }

  function syncPickerLayout() {
    const compact = Boolean(preview.hidden);
    if (lastLayoutCompact === compact) {
      return;
    }
    lastLayoutCompact = compact;
    void request(companion.TYPES.PICKER_LAYOUT, { compact: compact });
  }

  function renderPreview() {
    const item = selectedItem();
    const token = previewToken + 1;
    previewToken = token;
    clearPreviewMedia();
    if (!item) {
      preview.hidden = true;
      previewNav.hidden = true;
      setText(previewTitle, "");
      previewPrev.disabled = true;
      previewNext.disabled = true;
      attachSelected.disabled = true;
      syncPickerLayout();
      return;
    }
    preview.hidden = false;
    setText(previewTitle, item.display_title || item.media_id);
    const many = items.length > 1;
    previewNav.hidden = !many;
    previewPrev.disabled = !many;
    previewNext.disabled = !many;
    attachSelected.disabled = false;
    syncPickerLayout();
    const locationId = item.location && item.location.location_id;
    if (!companion.isUuid(item.media_id) || !companion.isUuid(locationId)) {
      return;
    }
    void request(companion.TYPES.PREVIEW_FETCH, {
      mediaId: item.media_id,
      locationId: locationId,
    }).then((result) => {
      if (token !== previewToken) {
        return;
      }
      if (!result.ok || typeof result.base64 !== "string" || !result.base64) {
        return;
      }
      const mediaType = typeof result.mediaType === "string" && result.mediaType.indexOf("image/") === 0
        ? result.mediaType
        : "image/jpeg";
      previewMedia.src = "data:" + mediaType + ";base64," + result.base64;
      previewMedia.hidden = false;
    });
  }

  function moveSelection(delta) {
    if (!items.length) {
      return;
    }
    selectedIndex = (selectedIndex + delta + items.length) % items.length;
    renderPreview();
  }

  function clearResults() {
    items = [];
    selectedIndex = 0;
    renderPreview();
  }

  function applyOrigin(origin) {
    connected = companion.acceptFrameNestOrigin(origin);
    if (!connected) {
      clearResults();
      setText(pickerStatus, disconnectedStatus());
      return false;
    }
    return true;
  }

  async function refresh() {
    if (!connected) {
      queryToken += 1;
      clearResults();
      setText(pickerStatus, disconnectedStatus());
      return;
    }
    const q = (search.value || "").trim();
    if (!q) {
      queryToken += 1;
      clearResults();
      setText(pickerStatus, "");
      return;
    }
    const token = queryToken + 1;
    queryToken = token;
    const result = await request(companion.TYPES.PICKER_QUERY, {
      q: q,
    });
    if (token !== queryToken) {
      return;
    }
    items = [];
    selectedIndex = 0;
    if (!result.ok) {
      setText(pickerStatus, result.error || "Picker unavailable");
      renderPreview();
      return;
    }
    items = (result.page && result.page.items) || [];
    setText(pickerStatus, items.length ? "" : "No eligible memes");
    renderPreview();
  }

  async function attachItem(item) {
    if (!item || !item.location) {
      return;
    }
    const result = await request(companion.TYPES.ATTACH_BEGIN, {
      mediaId: item.media_id,
      locationId: item.location.location_id,
      mediaType: item.location.media_type,
      filename: "framenest-media.bin",
    });
    setText(pickerStatus, result.ok ? "Attached" : result.error || "Attach failed");
  }

  function attachCurrent(event) {
    if (event) {
      event.preventDefault();
    }
    if (!trimmedQuery()) {
      return;
    }
    const item = selectedItem();
    if (!item) {
      return;
    }
    void attachItem(item);
  }

  function dismissPicker() {
    void request(companion.TYPES.DISMISS_PICKER, {});
  }

  function cycleHitsFromKey(event) {
    if (event.key === "ArrowLeft" && items.length > 1) {
      event.preventDefault();
      moveSelection(-1);
      return true;
    }
    if (event.key === "ArrowRight" && items.length > 1) {
      event.preventDefault();
      moveSelection(1);
      return true;
    }
    return false;
  }

  document.getElementById("refresh").addEventListener("click", refresh);
  search.addEventListener("input", refresh);
  search.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      attachCurrent(event);
      return;
    }
    cycleHitsFromKey(event);
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      event.preventDefault();
      dismissPicker();
      return;
    }
    if (event.target === search) {
      return;
    }
    cycleHitsFromKey(event);
  });
  preview.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      attachCurrent(event);
    }
  });
  previewPrev.addEventListener("click", () => moveSelection(-1));
  previewNext.addEventListener("click", () => moveSelection(1));
  attachSelected.addEventListener("click", () => attachCurrent());
  chrome.storage.local.get("frameNestOrigin", (stored) => {
    const origin = stored.frameNestOrigin || "";
    if (applyOrigin(origin)) {
      void refresh();
    }
  });
  chrome.storage.onChanged.addListener((changes, areaName) => {
    if (areaName !== "local" || !changes.frameNestOrigin) {
      return;
    }
    const origin = changes.frameNestOrigin.newValue || "";
    if (applyOrigin(origin)) {
      void refresh();
    }
  });
  search.focus();
})();
