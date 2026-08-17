(function () {
  const companion = globalThis.FrameNestCompanion;
  const form = document.getElementById("save-form");
  const title = document.getElementById("title");
  const description = document.getElementById("description");
  const tags = document.getElementById("tags");
  const tagsStatus = document.getElementById("tags-status");
  const formStatus = document.getElementById("form-status");
  const cancel = document.getElementById("cancel");

  function setStatus(node, value, kind) {
    node.textContent = value;
    if (kind) {
      node.setAttribute("data-kind", kind);
    } else {
      node.removeAttribute("data-kind");
    }
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

  function submittedUrl() {
    const raw = window.location.hash.startsWith("#")
      ? window.location.hash.slice(1)
      : "";
    const params = new URLSearchParams(raw);
    const accepted = companion.acceptXPostUrl(params.get("url") || "");
    return accepted ? accepted.submittedUrl : null;
  }

  function notifyParent(action, result) {
    window.parent.postMessage(
      {
        v: companion.PROTOCOL,
        source: "framenest-save-popup",
        action: action,
        result: result || null,
      },
      "*"
    );
  }

  function selectedTagKeys() {
    return Array.prototype.slice
      .call(tags.querySelectorAll("input[type='checkbox']:checked"))
      .map((node) => node.value);
  }

  function renderTags(items) {
    tags.replaceChildren();
    items.forEach((item) => {
      const key = item && item.key;
      if (typeof key !== "string") {
        return;
      }
      const label = document.createElement("label");
      const input = document.createElement("input");
      input.type = "checkbox";
      input.value = key;
      const name = document.createElement("span");
      name.textContent = typeof item.display_name === "string" ? item.display_name : key;
      label.appendChild(input);
      label.appendChild(name);
      tags.appendChild(label);
    });
  }

  async function loadTags() {
    const response = await request(companion.TYPES.CANONICAL_TAGS, {});
    if (!response.ok) {
      setStatus(tagsStatus, "Tags unavailable.", "error");
      return;
    }
    const list = (response.body && response.body.tags) || [];
    renderTags(Array.isArray(list) ? list : []);
    setStatus(tagsStatus, list.length ? "" : "No canonical tags yet.");
  }

  function aliasPayload() {
    const payload = {};
    const titleValue = title.value;
    const descriptionValue = description.value;
    const tagKeys = selectedTagKeys();
    if (titleValue) {
      payload.display_title = titleValue;
    }
    if (descriptionValue) {
      payload.description = descriptionValue;
    }
    if (tagKeys.length) {
      payload.tag_keys = tagKeys;
    }
    return payload;
  }

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    const url = submittedUrl();
    if (!url) {
      setStatus(formStatus, "Invalid post URL.", "error");
      return;
    }
    setStatus(formStatus, "Saving…");
    request(companion.TYPES.SAVE_POST, { url: url, alias: aliasPayload() }).then(
      (result) => {
        if (!result.ok) {
          setStatus(formStatus, "Save failed.", "error");
          notifyParent("result", result);
          return;
        }
        notifyParent("result", result);
      }
    );
  });

  cancel.addEventListener("click", () => {
    notifyParent("cancel");
  });

  void loadTags();
})();
