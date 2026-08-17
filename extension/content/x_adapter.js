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
  const GALLERY_DANGER = "#ff4d4d";
  const ATTACH_NAME = "Attach from FrameNest";
  const COMPANION_STYLE = [
    "[data-framenest-companion='save'] {",
    "  position: absolute;",
    "  top: 0;",
    "  left: 0;",
    "  margin: 0;",
    "  z-index: 5;",
    "  display: inline-flex;",
    "  align-items: center;",
    "  justify-content: center;",
    "  width: 32px;",
    "  height: 32px;",
    "  min-width: 32px;",
    "  min-height: 32px;",
    "  padding: 0;",
    "  border: 1px solid #00ff41;",
    "  border-radius: 6px;",
    "  background: #000000;",
    "  color: #00ff41;",
    "  cursor: pointer;",
    "  box-sizing: border-box;",
    "  appearance: none;",
    "  -webkit-appearance: none;",
    "  line-height: 0;",
    "  overflow: hidden;",
    "  opacity: 0;",
    "  pointer-events: none;",
    "}",
    "[data-framenest-media-host]:hover > [data-framenest-companion='save'],",
    "[data-framenest-media-host]:focus-within > [data-framenest-companion='save'],",
    "[data-framenest-companion='save']:focus,",
    "[data-framenest-companion='save']:focus-visible {",
    "  opacity: 1;",
    "  pointer-events: auto;",
    "}",
    "[data-framenest-companion='save']:hover,",
    "[data-framenest-companion='attach']:hover {",
    "  color: #39ff14;",
    "}",
    "[data-framenest-companion='save']:focus-visible,",
    "[data-framenest-companion='attach']:focus-visible {",
    "  outline: 2px solid #00ff41;",
    "  outline-offset: 2px;",
    "}",
    "[data-framenest-companion='attach'] {",
    "  position: absolute;",
    "  right: 0;",
    "  bottom: 0;",
    "  margin: 0;",
    "  z-index: 5;",
    "  display: inline-flex;",
    "  align-items: center;",
    "  justify-content: center;",
    "  width: 32px;",
    "  height: 32px;",
    "  min-width: 32px;",
    "  min-height: 32px;",
    "  padding: 0;",
    "  border: 1px solid #00ff41;",
    "  border-radius: 6px;",
    "  background: #000000;",
    "  color: #00ff41;",
    "  cursor: pointer;",
    "  box-sizing: border-box;",
    "  appearance: none;",
    "  -webkit-appearance: none;",
    "  line-height: 0;",
    "  overflow: hidden;",
    "}",
  ].join("\n");

  function first(root, selectors) {
    for (const selector of selectors) {
      const node = root.querySelector(selector);
      if (node) {
        return node;
      }
    }
    return null;
  }

  function matchesAny(node, selectors) {
    if (!node || !node.matches) {
      return false;
    }
    return selectors.some((selector) => node.matches(selector));
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

  function isDistinctLinkCard(node, postRoot) {
    if (!node.closest) {
      return false;
    }
    const card = node.closest(
      "[data-testid='card.wrapper'], [data-testid='card.layoutSmall.media'], [data-testid='card.layoutLarge.media']"
    );
    if (!card || !postRoot.contains(card)) {
      return false;
    }
    return !matchesAny(node, [
      "[data-testid='tweetPhoto']",
      "[data-testid='videoPlayer']",
      "[data-testid='videoComponent']",
    ]);
  }

  function ownMediaHosts(postRoot) {
    const hosts = [];
    const seen = new Set();
    for (const selector of contract.mediaHostSelectors) {
      const nodes = postRoot.querySelectorAll(selector);
      for (const node of nodes) {
        if (seen.has(node)) {
          continue;
        }
        if (isInsideNestedPost(node, postRoot)) {
          continue;
        }
        if (isDistinctLinkCard(node, postRoot)) {
          continue;
        }
        seen.add(node);
        hosts.push(node);
      }
    }
    return hosts.filter((node) => {
      return !hosts.some((other) => other !== node && other.contains(node));
    });
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
      node.setAttribute("aria-label", SAVE_UNAVAILABLE);
      node.setAttribute("title", SAVE_UNAVAILABLE);
    });
    void reason;
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
    svg.style.width = "18px";
    svg.style.height = "18px";
    svg.style.display = "block";
    svg.style.flex = "0 0 auto";
    svg.style.pointerEvents = "none";
    const g = svgEl("g", {
      fill: "none",
      stroke: "currentColor",
      "stroke-width": "2",
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
      g.appendChild(svgEl("path", { d: "M12 6.5v11M6.5 12h11" }));
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

  function ensureCompanionStyle() {
    if (document.querySelector("style[data-framenest-companion-style]")) {
      return;
    }
    const style = document.createElement("style");
    style.setAttribute("data-framenest-companion-style", "");
    style.textContent = COMPANION_STYLE;
    const parent = document.head || document.documentElement;
    parent.appendChild(style);
  }

  function ensureContainingBlock(node) {
    const position = window.getComputedStyle(node).position;
    if (position === "static") {
      node.style.position = "relative";
    }
  }

  function haltHostAction(event) {
    event.preventDefault();
    event.stopPropagation();
    event.stopImmediatePropagation();
  }

  function createSaveControl(accepted) {
    const button = document.createElement("button");
    button.type = "button";
    button.setAttribute("data-framenest-companion", "save");
    setSaveStatus(button, "idle", SAVE_NAME, false);
    ["pointerdown", "mousedown", "click"].forEach((type) => {
      button.addEventListener(type, (event) => {
        haltHostAction(event);
        if (type === "click") {
          void savePost(button, accepted);
        }
      });
    });
    return button;
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
    const accepted = permalinkFrom(postRoot);
    if (!accepted) {
      return "skipped";
    }
    const hosts = ownMediaHosts(postRoot);
    if (!hosts.length) {
      return "no_media";
    }
    hosts.forEach((host) => {
      if (injected.has(host)) {
        return;
      }
      if (host.querySelector(":scope > [data-framenest-companion='save']")) {
        injected.add(host);
        return;
      }
      host.setAttribute("data-framenest-media-host", "");
      ensureContainingBlock(host);
      host.appendChild(createSaveControl(accepted));
      injected.add(host);
    });
    return "placed";
  }

  function attachIconSvg() {
    const svg = svgEl("svg", { viewBox: "0 0 24 24", "aria-hidden": "true", focusable: "false" });
    svg.style.width = "18px";
    svg.style.height = "18px";
    svg.style.display = "block";
    svg.style.flex = "0 0 auto";
    svg.style.pointerEvents = "none";
    const g = svgEl("g", {
      fill: "none",
      stroke: "currentColor",
      "stroke-width": "2",
      "stroke-linecap": "round",
      "stroke-linejoin": "round",
    });
    g.appendChild(svgEl("path", { d: "M12 6.5v11M6.5 12h11" }));
    svg.appendChild(g);
    return svg;
  }

  function isEditableComposerNode(node) {
    if (!node || !node.getAttribute) {
      return false;
    }
    return (
      node.getAttribute("contenteditable") === "true" ||
      node.getAttribute("data-testid") === "tweetTextarea_0"
    );
  }

  function findComposerChrome(composerRoot) {
    if (!composerRoot) {
      return null;
    }
    let node = composerRoot;
    let hops = 0;
    while (node && hops < 12) {
      if (matchesAny(node, contract.composerChromeSelectors)) {
        return node;
      }
      const toolbar =
        matchesAny(node, contract.composerToolbarSelectors) ||
        first(node, contract.composerToolbarSelectors);
      if (toolbar && !isEditableComposerNode(node)) {
        return node;
      }
      node = node.parentElement;
      hops += 1;
    }
    return null;
  }

  function createAttachControl(composerRoot, fileInput) {
    const button = document.createElement("button");
    button.type = "button";
    button.setAttribute("data-framenest-companion", "attach");
    button.setAttribute("aria-label", ATTACH_NAME);
    button.setAttribute("title", ATTACH_NAME);
    button.appendChild(attachIconSvg());
    ["pointerdown", "mousedown", "click"].forEach((type) => {
      button.addEventListener(type, (event) => {
        haltHostAction(event);
        if (type !== "click" || stale) {
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
    });
    return button;
  }

  function injectAttach(composerRoot) {
    if (injected.has(composerRoot)) {
      return;
    }
    const composerChrome = findComposerChrome(composerRoot);
    if (!composerChrome) {
      return;
    }
    if (composerChrome.querySelector("[data-framenest-companion='attach']")) {
      injected.add(composerRoot);
      return;
    }
    const fileInput =
      first(composerChrome, contract.composerFileInputs) ||
      first(composerRoot, contract.composerFileInputs) ||
      first(document, contract.composerFileInputs);
    if (!fileInput) {
      markStale("missing_composer_file_input");
      return;
    }
    ensureContainingBlock(composerChrome);
    composerChrome.appendChild(createAttachControl(composerRoot, fileInput));
    injected.add(composerRoot);
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
    ensureCompanionStyle();
    const posts = document.querySelectorAll(contract.postRoots.join(","));
    posts.forEach((post) => {
      injectSave(post);
    });
    const composers = document.querySelectorAll(contract.composerRoots.join(","));
    composers.forEach((composer) => injectAttach(composer));
  }

  const observer = new MutationObserver(() => scan());
  observer.observe(document.documentElement, { childList: true, subtree: true });
  scan();
  recover();
})();
