(function () {
  const companion = globalThis.FrameNestCompanion;
  const originInput = document.getElementById("origin");
  const setupStatus = document.getElementById("setup-status");
  const picker = document.getElementById("picker");
  const pickerStatus = document.getElementById("picker-status");
  const search = document.getElementById("search");
  const kind = document.getElementById("kind");
  const preview = document.getElementById("preview");
  const previewTitle = document.getElementById("preview-title");
  const previewPrev = document.getElementById("preview-prev");
  const previewNext = document.getElementById("preview-next");
  const attachSelected = document.getElementById("attach-selected");
  let items = [];
  let selectedIndex = 0;

  function setText(node, value) {
    node.textContent = value;
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

  function renderPreview() {
    const item = selectedItem();
    if (!item) {
      preview.hidden = true;
      setText(previewTitle, "");
      previewPrev.disabled = true;
      previewNext.disabled = true;
      attachSelected.disabled = true;
      return;
    }
    preview.hidden = false;
    setText(previewTitle, item.display_title || item.media_id);
    const many = items.length > 1;
    previewPrev.disabled = !many;
    previewNext.disabled = !many;
    attachSelected.disabled = false;
  }

  function moveSelection(delta) {
    if (!items.length) {
      return;
    }
    selectedIndex = (selectedIndex + delta + items.length) % items.length;
    renderPreview();
  }

  async function connect() {
    const origin = originInput.value.trim();
    const result = await request(companion.TYPES.CONFIGURE_ORIGIN, { origin });
    setText(setupStatus, result.ok ? "Connected" : result.error || "Failed");
    if (result.ok) {
      picker.hidden = false;
      await refresh();
    }
  }

  async function reset() {
    await request(companion.TYPES.RESET, {});
    picker.hidden = true;
    items = [];
    selectedIndex = 0;
    renderPreview();
    setText(setupStatus, "Cleared");
  }

  async function refresh() {
    const result = await request(companion.TYPES.PICKER_QUERY, {
      q: search.value || undefined,
      kind: kind.value || undefined,
    });
    items = [];
    selectedIndex = 0;
    if (!result.ok) {
      setText(pickerStatus, result.error || "Picker unavailable");
      renderPreview();
      if (result.disable) {
        picker.hidden = true;
      }
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
    const item = selectedItem();
    if (!item) {
      return;
    }
    void attachItem(item);
  }

  document.getElementById("save-origin").addEventListener("click", connect);
  document.getElementById("reset").addEventListener("click", reset);
  document.getElementById("refresh").addEventListener("click", refresh);
  kind.addEventListener("change", refresh);
  search.addEventListener("input", refresh);
  search.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      attachCurrent(event);
    }
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
    if (stored.frameNestOrigin) {
      originInput.value = stored.frameNestOrigin;
      picker.hidden = false;
      refresh();
    }
  });
})();
