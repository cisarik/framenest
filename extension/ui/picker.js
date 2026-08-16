(function () {
  const companion = globalThis.FrameNestCompanion;
  const originInput = document.getElementById("origin");
  const setupStatus = document.getElementById("setup-status");
  const picker = document.getElementById("picker");
  const results = document.getElementById("results");
  const pickerStatus = document.getElementById("picker-status");
  const search = document.getElementById("search");
  const kind = document.getElementById("kind");

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
    results.replaceChildren();
    setText(setupStatus, "Cleared");
  }

  async function refresh() {
    const result = await request(companion.TYPES.PICKER_QUERY, {
      q: search.value || undefined,
      kind: kind.value || undefined,
    });
    results.replaceChildren();
    if (!result.ok) {
      setText(pickerStatus, result.error || "Picker unavailable");
      if (result.disable) {
        picker.hidden = true;
      }
      return;
    }
    const items = (result.page && result.page.items) || [];
    setText(pickerStatus, items.length ? "" : "No eligible memes");
    items.forEach((item) => {
      const entry = document.createElement("li");
      const title = document.createElement("p");
      title.textContent = item.display_title || item.media_id;
      const attach = document.createElement("button");
      attach.type = "button";
      attach.textContent = "Attach";
      attach.addEventListener("click", () => attachItem(item));
      entry.appendChild(title);
      entry.appendChild(attach);
      results.appendChild(entry);
    });
  }

  async function attachItem(item) {
    const result = await request(companion.TYPES.ATTACH_BEGIN, {
      mediaId: item.media_id,
      locationId: item.location.location_id,
      mediaType: item.location.media_type,
      filename: "framenest-media.bin",
    });
    setText(pickerStatus, result.ok ? "Attached" : result.error || "Attach failed");
  }

  document.getElementById("save-origin").addEventListener("click", connect);
  document.getElementById("reset").addEventListener("click", reset);
  document.getElementById("refresh").addEventListener("click", refresh);
  chrome.storage.local.get("frameNestOrigin", (stored) => {
    if (stored.frameNestOrigin) {
      originInput.value = stored.frameNestOrigin;
      picker.hidden = false;
      refresh();
    }
  });
})();
