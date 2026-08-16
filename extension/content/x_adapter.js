(function () {
  const companion = globalThis.FrameNestCompanion;
  const contract = globalThis.FrameNestXAdapterContractV1;
  if (!companion || !contract) {
    return;
  }

  const injected = new WeakSet();
  const inflightByClaim = new Map();
  let stale = false;
  let boundComposer = null;
  const SAVE_NAME = "Save to FrameNest";
  const SAVE_UNAVAILABLE = "FrameNest unavailable";

  function first(root, selectors) {
    for (const selector of selectors) {
      const node = root.querySelector(selector);
      if (node) {
        return node;
      }
    }
    return null;
  }

  function matchesPostRoot(node) {
    if (!node || !node.matches) {
      return false;
    }
    return contract.postRoots.some((selector) => node.matches(selector));
  }

  function isInsideNestedPost(node, postRoot) {
    let current = node.parentElement;
    while (current && current !== postRoot) {
      if (matchesPostRoot(current)) {
        return true;
      }
      current = current.parentElement;
    }
    return false;
  }

  function ownActionGroup(postRoot) {
    for (const groupSelector of contract.actionGroupSelectors) {
      const groups = postRoot.querySelectorAll(groupSelector);
      for (const group of groups) {
        if (isInsideNestedPost(group, postRoot)) {
          continue;
        }
        if (first(group, contract.actionBarSignals)) {
          return group;
        }
      }
    }
    return null;
  }

  function shareActionColumn(share, actionGroup) {
    let column = share;
    while (column.parentElement && column.parentElement !== actionGroup) {
      column = column.parentElement;
    }
    if (column.parentElement !== actionGroup) {
      return null;
    }
    return column;
  }

  function permalinkFrom(postRoot) {
    for (const selector of contract.permalinkSelectors) {
      const node = postRoot.querySelector(selector);
      if (!node) {
        continue;
      }
      const href = node.getAttribute("href") || (node.closest && node.closest("a") && node.closest("a").getAttribute("href"));
      if (!href) {
        continue;
      }
      const absolute = href.startsWith("http") ? href : "https://x.com" + href.split("?")[0];
      const accepted = companion.acceptXPostUrl(absolute.split("?")[0].split("#")[0]);
      if (accepted) {
        return accepted;
      }
    }
    return null;
  }

  function markStale(reason) {
    stale = true;
    document.querySelectorAll("[data-framenest-companion]").forEach((node) => {
      node.setAttribute("disabled", "true");
      if (node.getAttribute("data-framenest-companion") === "save") {
        setSaveName(node, SAVE_UNAVAILABLE);
        node.removeAttribute("aria-busy");
        return;
      }
      node.textContent = SAVE_UNAVAILABLE;
    });
    void reason;
  }

  function send(type, payload) {
    return chrome.runtime.sendMessage(
      { v: companion.PROTOCOL, type, payload: payload || {} },
      function () {
        return undefined;
      }
    );
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

  function addButton(parent, label, onClick) {
    const button = document.createElement("button");
    button.type = "button";
    button.setAttribute("data-framenest-companion", label);
    button.textContent = label;
    button.addEventListener("click", (event) => {
      event.preventDefault();
      event.stopPropagation();
      onClick(button);
    });
    parent.appendChild(button);
    return button;
  }

  function svgEl(name, attrs) {
    const node = document.createElementNS("http://www.w3.org/2000/svg", name);
    Object.keys(attrs).forEach((key) => {
      node.setAttribute(key, attrs[key]);
    });
    return node;
  }

  function saveIconSvg(kind) {
    const svg = svgEl("svg", { viewBox: "0 0 24 24", "aria-hidden": "true", focusable: "false" });
    svg.style.width = "22px";
    svg.style.height = "22px";
    svg.style.display = "block";
    svg.style.flex = "0 0 auto";
    svg.style.pointerEvents = "none";
    const g = svgEl("g", {
      fill: "none",
      stroke: "currentColor",
      "stroke-width": "1.75",
      "stroke-linecap": "round",
      "stroke-linejoin": "round",
    });
    if (kind === "busy") {
      g.appendChild(svgEl("path", { d: "M12 5.25a6.75 6.75 0 1 1-4.77 1.98" }));
    } else if (kind === "done") {
      g.appendChild(svgEl("path", { d: "M6.5 12.25l3.6 3.5 7.4-8" }));
    } else if (kind === "failed") {
      g.appendChild(svgEl("path", { d: "M8 8l8 8M16 8l-8 8" }));
    } else {
      g.appendChild(svgEl("rect", { x: "4.5", y: "4.5", width: "15", height: "15", rx: "2" }));
      g.appendChild(svgEl("path", { d: "M12 8.5v7M8.5 12h7" }));
    }
    svg.appendChild(g);
    return svg;
  }

  function setSaveName(button, name) {
    button.setAttribute("aria-label", name);
    button.setAttribute("title", name);
  }

  function setSaveStatus(button, kind, name, busy) {
    setSaveName(button, name);
    if (busy) {
      button.setAttribute("aria-busy", "true");
    } else {
      button.removeAttribute("aria-busy");
    }
    while (button.firstChild) {
      button.removeChild(button.firstChild);
    }
    button.appendChild(saveIconSvg(kind));
  }

  function copyActionColor(fromNode, toNode) {
    const source = (fromNode.querySelector && fromNode.querySelector("svg")) || fromNode;
    const color = window.getComputedStyle(source).color;
    if (color && color !== "rgba(0, 0, 0, 0)") {
      toNode.style.color = color;
    }
  }

  function applySaveChrome(button) {
    button.style.display = "inline-flex";
    button.style.alignItems = "center";
    button.style.justifyContent = "center";
    button.style.width = "36px";
    button.style.height = "36px";
    button.style.minWidth = "36px";
    button.style.minHeight = "36px";
    button.style.maxWidth = "36px";
    button.style.maxHeight = "36px";
    button.style.padding = "0";
    button.style.margin = "0";
    button.style.border = "0";
    button.style.background = "transparent";
    button.style.color = "inherit";
    button.style.cursor = "pointer";
    button.style.borderRadius = "999px";
    button.style.flex = "0 0 auto";
    button.style.alignSelf = "center";
    button.style.boxSizing = "border-box";
    button.style.appearance = "none";
    button.style.webkitAppearance = "none";
    button.style.lineHeight = "0";
    button.style.overflow = "hidden";
  }

  function applySaveColumnChrome(column) {
    column.style.display = "flex";
    column.style.alignItems = "center";
    column.style.justifyContent = "center";
    column.style.alignSelf = "center";
    column.style.flex = "0 0 auto";
    column.style.minWidth = "36px";
    column.style.height = "36px";
  }

  function haltHostAction(event) {
    event.preventDefault();
    event.stopPropagation();
    event.stopImmediatePropagation();
  }

  function haltHostBubble(event) {
    event.stopPropagation();
    event.stopImmediatePropagation();
  }

  function createSaveControl(accepted, share) {
    const column = document.createElement("div");
    applySaveColumnChrome(column);
    const button = document.createElement("button");
    button.type = "button";
    button.setAttribute("data-framenest-companion", "save");
    applySaveChrome(button);
    copyActionColor(share, button);
    setSaveStatus(button, "idle", SAVE_NAME, false);
    button.addEventListener("mouseenter", () => {
      if (!button.disabled) {
        button.style.background = "rgba(127, 127, 127, 0.12)";
      }
    });
    button.addEventListener("mouseleave", () => {
      button.style.background = "transparent";
    });
    ["pointerdown", "mousedown"].forEach((type) => {
      button.addEventListener(type, haltHostBubble);
    });
    button.addEventListener("click", (event) => {
      haltHostAction(event);
      void savePost(button, accepted);
    });
    column.appendChild(button);
    return column;
  }

  async function savePost(button, accepted) {
    if (stale || button.disabled || button.getAttribute("aria-busy") === "true") {
      return;
    }
    setSaveStatus(button, "busy", "Saving to FrameNest", true);
    const result = await request(companion.TYPES.SAVE_POST, {
      url: accepted.submittedUrl,
    });
    if (!result.ok) {
      setSaveStatus(button, "failed", "Save to FrameNest failed", false);
      return;
    }
    if (result.claimId) {
      inflightByClaim.set(result.claimId, button);
      setSaveStatus(button, "busy", "Saving to FrameNest", true);
      pollClaim(result.claimId);
      return;
    }
    setSaveStatus(button, "done", "Saved to FrameNest", false);
  }

  function injectSave(postRoot) {
    if (injected.has(postRoot)) {
      return "placed";
    }
    const accepted = permalinkFrom(postRoot);
    if (!accepted) {
      return "skipped";
    }
    const actionGroup = ownActionGroup(postRoot);
    if (!actionGroup) {
      return "missing_bar";
    }
    const share = first(actionGroup, contract.shareSelectors);
    if (!share) {
      return "missing_share";
    }
    const column = shareActionColumn(share, actionGroup);
    if (!column) {
      return "missing_share";
    }
    const saveColumn = createSaveControl(accepted, share);
    column.insertAdjacentElement("afterend", saveColumn);
    injected.add(postRoot);
    return "placed";
  }

  function injectAttach(composerRoot) {
    if (injected.has(composerRoot)) {
      return;
    }
    const fileInput = first(composerRoot, contract.composerFileInputs) ||
      first(document, contract.composerFileInputs);
    if (!fileInput) {
      markStale("missing_composer_file_input");
      return;
    }
    injected.add(composerRoot);
    addButton(composerRoot, "Attach from FrameNest", async () => {
      if (stale) {
        return;
      }
      boundComposer = { root: composerRoot, fileInput };
      await request(companion.TYPES.ACK, { composerBound: true });
      chrome.runtime.sendMessage({
        v: companion.PROTOCOL,
        type: companion.TYPES.ACK,
        payload: { openPicker: true },
      });
    });
  }

  async function pollClaim(claimId) {
    const button = inflightByClaim.get(claimId);
    if (!button || !document.contains(button)) {
      return;
    }
    const result = await request(companion.TYPES.POLL_CLAIM, { claimId });
    if (!result.ok) {
      setSaveStatus(button, "failed", "Save to FrameNest failed", false);
      inflightByClaim.delete(claimId);
      return;
    }
    if (result.terminal) {
      inflightByClaim.delete(claimId);
      setSaveStatus(button, "done", "Saved to FrameNest", false);
      return;
    }
    setSaveStatus(button, "busy", "Saving to FrameNest", true);
    window.setTimeout(() => {
      pollClaim(claimId);
    }, 1500);
  }

  async function recover() {
    const result = await request(companion.TYPES.RECOVER_INFLIGHT, {});
    if (!result.ok || !Array.isArray(result.claimIds)) {
      return;
    }
    result.claimIds.forEach((claimId) => {
      pollClaim(claimId);
    });
  }

  chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
    const parsed = companion.dropUnknown(message);
    if (!parsed) {
      return false;
    }
    if (parsed.type === companion.TYPES.ATTACH_BEGIN) {
      attachSelected(parsed.payload || {}).then((result) => sendResponse(result));
      return true;
    }
    return false;
  });

  chrome.runtime.onConnect.addListener((port) => {
    if (!port || port.name !== "framenest-attach") {
      return;
    }
    const chunks = [];
    let total = 0;
    let mediaType = "application/octet-stream";
    let filename = "framenest-media.bin";
    port.onMessage.addListener((message) => {
      const parsed = companion.dropUnknown(message);
      if (!parsed) {
        return;
      }
      if (parsed.payload && parsed.payload.phase === "meta") {
        mediaType = parsed.payload.mediaType || mediaType;
        filename = parsed.payload.filename || filename;
        return;
      }
      if (parsed.payload && parsed.payload.chunk) {
        const bytes = companion.bytesFromBase64(parsed.payload.chunk);
        total += bytes.byteLength;
        if (total > companion.MAX_ATTACH_BYTES) {
          port.postMessage({
            v: companion.PROTOCOL,
            type: companion.TYPES.ERROR,
            payload: { error: "too_large" },
          });
          port.disconnect();
          return;
        }
        chunks.push(bytes);
        return;
      }
      if (parsed.payload && parsed.payload.phase === "end") {
        const fileInput = boundComposer && boundComposer.fileInput;
        if (!fileInput) {
          port.postMessage({
            v: companion.PROTOCOL,
            type: companion.TYPES.ERROR,
            payload: { error: "composer_unbound" },
          });
          return;
        }
        const bytes = companion.concatChunks(chunks, total);
        const file = new File([bytes], filename, { type: mediaType });
        const transfer = new DataTransfer();
        transfer.items.add(file);
        fileInput.files = transfer.files;
        fileInput.dispatchEvent(new Event("change", { bubbles: true }));
        port.postMessage({
          v: companion.PROTOCOL,
          type: companion.TYPES.ACK,
          payload: { attached: true, bytes: total },
        });
      }
    });
  });

  async function attachSelected() {
    return { ok: Boolean(boundComposer && boundComposer.fileInput) };
  }

  function scan() {
    if (stale) {
      return;
    }
    const posts = document.querySelectorAll(contract.postRoots.join(","));
    let eligible = 0;
    let placed = 0;
    let missingBar = 0;
    let missingShare = 0;
    posts.forEach((post) => {
      const outcome = injectSave(post);
      if (outcome === "skipped") {
        return;
      }
      eligible += 1;
      if (outcome === "placed") {
        placed += 1;
      } else if (outcome === "missing_bar") {
        missingBar += 1;
      } else if (outcome === "missing_share") {
        missingShare += 1;
      }
    });
    if (eligible > 0 && placed === 0 && missingShare > 0 && missingBar === 0) {
      markStale("adapter_drift");
    }
    const composers = document.querySelectorAll(contract.composerRoots.join(","));
    composers.forEach((composer) => injectAttach(composer));
  }

  const observer = new MutationObserver(() => scan());
  observer.observe(document.documentElement, { childList: true, subtree: true });
  scan();
  recover();
})();
