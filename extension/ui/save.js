(function () {
  const companion = globalThis.FrameNestCompanion;
  const SUGGESTION_LIMIT = 8;
  const TAG_LIMIT = 32;
  const ANALYZE_HINT =
    "Saves now. Analyze by AI is available in FrameNest after this item is cataloged.";
  const form = document.getElementById("save-form");
  const title = document.getElementById("title");
  const description = document.getElementById("description");
  const tagSearch = document.getElementById("tag-search");
  const suggestions = document.getElementById("tag-suggestions");
  const selectedTags = document.getElementById("selected-tags");
  const tagsStatus = document.getElementById("tags-status");
  const formStatus = document.getElementById("form-status");
  const closeButton = document.getElementById("close");
  const analyze = document.getElementById("analyze");
  const catalog = [];
  const chosen = [];
  let activeSuggestion = -1;

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

  function displayNameOf(item) {
    if (item && typeof item.display_name === "string" && item.display_name) {
      return item.display_name;
    }
    return item && typeof item.key === "string" ? item.key : "";
  }

  function selectedKeys() {
    return chosen.map((item) => item.key);
  }

  function matchingTags(query) {
    const needle = query.toLocaleLowerCase();
    if (!needle) {
      return [];
    }
    const selected = selectedKeys();
    return catalog
      .filter((item) => {
        if (selected.indexOf(item.key) !== -1) {
          return false;
        }
        const name = displayNameOf(item).toLocaleLowerCase();
        const key = item.key.toLocaleLowerCase();
        return name.indexOf(needle) !== -1 || key.indexOf(needle) !== -1;
      })
      .slice(0, SUGGESTION_LIMIT);
  }

  function renderSelected() {
    selectedTags.replaceChildren();
    chosen.forEach((item) => {
      const chip = document.createElement("span");
      chip.className = "tag-chip";
      const label = document.createElement("span");
      label.textContent = displayNameOf(item);
      const remove = document.createElement("button");
      remove.type = "button";
      remove.className = "tag-chip__remove";
      remove.textContent = "X";
      remove.setAttribute("aria-label", "Remove " + displayNameOf(item));
      remove.addEventListener("click", () => {
        const index = chosen.findIndex((entry) => entry.key === item.key);
        if (index >= 0) {
          chosen.splice(index, 1);
          renderSelected();
          renderSuggestions();
        }
      });
      chip.appendChild(label);
      chip.appendChild(remove);
      selectedTags.appendChild(chip);
    });
  }

  function renderSuggestions() {
    suggestions.replaceChildren();
    const matches = matchingTags(tagSearch.value.trim());
    if (!matches.length) {
      activeSuggestion = -1;
      tagSearch.setAttribute("aria-expanded", "false");
      return;
    }
    if (activeSuggestion < 0 || activeSuggestion >= matches.length) {
      activeSuggestion = 0;
    }
    tagSearch.setAttribute("aria-expanded", "true");
    matches.forEach((item, index) => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "tag-suggestion";
      button.id = "tag-suggestion-" + String(index);
      button.setAttribute("role", "option");
      button.setAttribute("aria-selected", String(index === activeSuggestion));
      button.textContent = displayNameOf(item);
      button.addEventListener("mousedown", (event) => {
        event.preventDefault();
      });
      button.addEventListener("click", () => {
        addTag(item);
      });
      suggestions.appendChild(button);
    });
  }

  function addTag(item) {
    if (!item || typeof item.key !== "string") {
      return;
    }
    if (chosen.some((entry) => entry.key === item.key)) {
      return;
    }
    if (chosen.length >= TAG_LIMIT) {
      setStatus(tagsStatus, "Tag limit reached.", "error");
      return;
    }
    chosen.push({ key: item.key, display_name: displayNameOf(item) });
    tagSearch.value = "";
    activeSuggestion = -1;
    setStatus(tagsStatus, "");
    renderSelected();
    renderSuggestions();
    tagSearch.focus();
  }

  function aliasPayload() {
    const payload = {};
    const titleValue = title.value;
    const descriptionValue = description.value.trim();
    const tagKeys = selectedKeys();
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

  function gateAnalyze(identityBody) {
    analyze.hidden = true;
    analyze.disabled = true;
    analyze.title = ANALYZE_HINT;
    analyze.setAttribute("aria-label", ANALYZE_HINT);
    if (!identityBody || !Array.isArray(identityBody.capabilities)) {
      return;
    }
    if (identityBody.capabilities.indexOf("analysis.run") === -1) {
      return;
    }
    analyze.hidden = false;
    analyze.disabled = false;
  }

  function submitSave() {
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
  }

  async function loadTags() {
    const response = await request(companion.TYPES.CANONICAL_TAGS, {});
    if (!response.ok) {
      setStatus(tagsStatus, "Tags unavailable.", "error");
      return;
    }
    const list = (response.body && response.body.tags) || [];
    catalog.length = 0;
    (Array.isArray(list) ? list : []).forEach((item) => {
      if (item && typeof item.key === "string") {
        catalog.push({ key: item.key, display_name: displayNameOf(item) });
      }
    });
    setStatus(tagsStatus, catalog.length ? "" : "No canonical tags yet.");
    renderSuggestions();
  }

  async function loadIdentity() {
    const response = await request(companion.TYPES.IDENTITY, {});
    if (!response.ok) {
      gateAnalyze(null);
      return;
    }
    gateAnalyze(response.body || null);
  }

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    submitSave();
  });

  closeButton.addEventListener("click", () => {
    notifyParent("cancel");
  });

  analyze.addEventListener("click", (event) => {
    event.preventDefault();
    submitSave();
  });

  tagSearch.addEventListener("input", () => {
    activeSuggestion = -1;
    renderSuggestions();
  });

  tagSearch.addEventListener("keydown", (event) => {
    const matches = matchingTags(tagSearch.value.trim());
    if (event.key === "ArrowDown" && matches.length) {
      event.preventDefault();
      activeSuggestion = (activeSuggestion + 1) % matches.length;
      renderSuggestions();
      return;
    }
    if (event.key === "ArrowUp" && matches.length) {
      event.preventDefault();
      activeSuggestion = activeSuggestion <= 0 ? matches.length - 1 : activeSuggestion - 1;
      renderSuggestions();
      return;
    }
    if (event.key === "Enter") {
      event.preventDefault();
      if (matches.length) {
        const index = activeSuggestion >= 0 ? activeSuggestion : 0;
        addTag(matches[index]);
      }
    }
  });

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      event.preventDefault();
      notifyParent("cancel");
    }
  });

  void loadTags();
  void loadIdentity();
})();
