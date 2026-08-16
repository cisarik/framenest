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
  const GALLERY_ACCENT = "#00ff41";
  const GALLERY_ACCENT_STRONG = "#39ff14";
  const GALLERY_ACCENT_SOFT = "rgba(0, 255, 65, 0.12)";
  const GALLERY_ACCENT_GLOW = "rgba(0, 255, 65, 0.18)";
  const GALLERY_ACCENT_BORDER = "rgba(0, 255, 65, 0.42)";
  const GALLERY_DANGER = "#ff4d4d";
  const GALLERY_RADIUS_SM = "6px";
  const GALLERY_FONT_MONO =
    'ui-monospace, "SF Mono", "JetBrains Mono", "Fira Code", "Cascadia Code", Menlo, Monaco, Consolas, monospace';

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
    button.dataset.framenestSaveKind = kind;
    button.style.color = kind === "failed" ? GALLERY_DANGER : GALLERY_ACCENT;
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
    button.style.color = GALLERY_ACCENT;
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

  function matchesAny(node, selectors) {
    if (!node || !node.matches) {
      return false;
    }
    return selectors.some((selector) => node.matches(selector));
  }

  function bookmarkActionColumn(actionGroup, shareColumn) {
    const bookmark = first(actionGroup, contract.bookmarkSelectors);
    if (!bookmark) {
      return null;
    }
    const column = shareActionColumn(bookmark, actionGroup);
    if (!column || column === shareColumn) {
      return null;
    }
    return column;
  }

  function applySaveColumnAlignment(column, button, share, shareColumn, actionGroup) {
    const shareStyle = window.getComputedStyle(shareColumn);
    const shareRect = shareColumn.getBoundingClientRect();
    const styleHeight = Number.parseFloat(shareStyle.height);
    const height = Math.max(
      36,
      Math.round(shareRect.height) || (Number.isFinite(styleHeight) ? Math.round(styleHeight) : 36)
    );
    const display = shareStyle.display;
    column.style.display = display === "flex" || display === "inline-flex" ? display : "flex";
    column.style.flexDirection = shareStyle.flexDirection;
    column.style.alignItems = shareStyle.alignItems === "normal" ? "center" : shareStyle.alignItems;
    column.style.justifyContent =
      shareStyle.justifyContent === "normal" ? "center" : shareStyle.justifyContent;
    column.style.height = height + "px";
    column.style.minHeight = height + "px";
    column.style.minWidth = "36px";
    column.style.flex = "0 0 auto";
    column.style.boxSizing = "border-box";
    column.style.alignSelf = shareStyle.alignSelf === "auto" ? "stretch" : shareStyle.alignSelf;

    const controlRect = share.getBoundingClientRect();
    const topOffset = Math.round(controlRect.top - shareRect.top);
    if (topOffset > 1) {
      button.style.marginTop = topOffset + "px";
      column.style.alignItems = "flex-start";
      column.style.justifyContent = "center";
    }

    const bookmarkColumn = bookmarkActionColumn(actionGroup, shareColumn);
    let gap = 0;
    if (bookmarkColumn) {
      const bookmarkRect = bookmarkColumn.getBoundingClientRect();
      gap = Math.round(shareRect.left - bookmarkRect.right);
      if (!Number.isFinite(gap) || gap < 0) {
        gap = 0;
      }
    }
    if (gap === 0) {
      gap = 8;
    }
    column.style.marginLeft = gap + "px";
  }

  function applyAttachChrome(button) {
    button.style.display = "inline-flex";
    button.style.alignItems = "center";
    button.style.justifyContent = "center";
    button.style.fontFamily = GALLERY_FONT_MONO;
    button.style.fontSize = "0.78rem";
    button.style.fontWeight = "700";
    button.style.background = GALLERY_ACCENT_SOFT;
    button.style.border = "1px solid " + GALLERY_ACCENT_BORDER;
    button.style.color = GALLERY_ACCENT;
    button.style.borderRadius = GALLERY_RADIUS_SM;
    button.style.padding = "6px 10px";
    button.style.margin = "4px 0 0 8px";
    button.style.cursor = "pointer";
    button.style.lineHeight = "1.2";
    button.style.flex = "0 0 auto";
    button.style.alignSelf = "center";
    button.style.boxSizing = "border-box";
    button.style.appearance = "none";
    button.style.webkitAppearance = "none";
    button.style.whiteSpace = "nowrap";
  }

  function findComposerToolbar(composerRoot) {
    if (matchesAny(composerRoot, contract.composerToolbarSelectors)) {
      return composerRoot;
    }
    const nested = first(composerRoot, contract.composerToolbarSelectors);
    if (nested) {
      return nested;
    }
    let node = composerRoot;
    let hops = 0;
    while (node.parentElement && hops < 8) {
      const parent = node.parentElement;
      if (matchesAny(parent, contract.composerToolbarSelectors)) {
        return parent;
      }
      for (const child of parent.children) {
        if (matchesAny(child, contract.composerToolbarSelectors)) {
          return child;
        }
        if (child !== node) {
          const nestedSibling = first(child, contract.composerToolbarSelectors);
          if (nestedSibling) {
            return nestedSibling;
          }
        }
      }
      node = parent;
      hops += 1;
    }
    return null;
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

  function createSaveControl(accepted, share, shareColumn, actionGroup) {
    const column = document.createElement("div");
    const button = document.createElement("button");
    button.type = "button";
    button.setAttribute("data-framenest-companion", "save");
    applySaveChrome(button);
    setSaveStatus(button, "idle", SAVE_NAME, false);
    button.addEventListener("mouseenter", () => {
      if (!button.disabled) {
        button.style.background = GALLERY_ACCENT_SOFT;
        button.style.boxShadow = "0 0 10px " + GALLERY_ACCENT_GLOW;
        if (button.dataset.framenestSaveKind !== "failed") {
          button.style.color = GALLERY_ACCENT_STRONG;
        }
      }
    });
    button.addEventListener("mouseleave", () => {
      button.style.background = "transparent";
      button.style.boxShadow = "none";
      button.style.color =
        button.dataset.framenestSaveKind === "failed" ? GALLERY_DANGER : GALLERY_ACCENT;
    });
    ["pointerdown", "mousedown"].forEach((type) => {
      button.addEventListener(type, haltHostBubble);
    });
    button.addEventListener("click", (event) => {
      haltHostAction(event);
      void savePost(button, accepted);
    });
    column.appendChild(button);
    applySaveColumnAlignment(column, button, share, shareColumn, actionGroup);
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
    const saveColumn = createSaveControl(accepted, share, column, actionGroup);
    column.insertAdjacentElement("afterend", saveColumn);
    injected.add(postRoot);
    return "placed";
  }

  function injectAttach(composerRoot) {
    if (injected.has(composerRoot)) {
      return;
    }
    const toolbar = findComposerToolbar(composerRoot);
    if (!toolbar) {
      return;
    }
    if (toolbar.querySelector("[data-framenest-companion='attach']")) {
      injected.add(composerRoot);
      return;
    }
    const fileInput = first(composerRoot, contract.composerFileInputs) ||
      first(document, contract.composerFileInputs);
    if (!fileInput) {
      markStale("missing_composer_file_input");
      return;
    }
    injected.add(composerRoot);
    const button = document.createElement("button");
    button.type = "button";
    button.setAttribute("data-framenest-companion", "attach");
    button.textContent = "Attach from FrameNest";
    applyAttachChrome(button);
    button.addEventListener("click", (event) => {
      haltHostAction(event);
      if (stale) {
        return;
      }
      boundComposer = { root: composerRoot, fileInput };
      void request(companion.TYPES.ACK, { composerBound: true }).then(() => {
        chrome.runtime.sendMessage({
          v: companion.PROTOCOL,
          type: companion.TYPES.ACK,
          payload: { openPicker: true },
        });
      });
    });
    toolbar.appendChild(button);
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
