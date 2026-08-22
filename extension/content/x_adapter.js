(function () {
  const companion = globalThis.FrameNestCompanion;
  const contract = globalThis.FrameNestXAdapterContractV1;
  if (!companion || !contract) {
    return;
  }

  const injected = new WeakSet();
  const inflightByClaim = new Map();
  const postOutcomeById = new Map();
  const attachByComposer = new WeakMap();
  const attachEditable = new WeakMap();
  const plusPlusBound = new WeakSet();
  let stale = false;
  let boundComposer = null;
  let attachPopup = null;
  let savePopup = null;
  let attachPositionBound = false;
  let composerFocusBound = false;
  const SAVE_NAME = "Save to FrameNest";
  const SAVE_UNAVAILABLE = "FrameNest unavailable";
  const GALLERY_ACCENT = "#00ff41";
  const GALLERY_DANGER = "#ff4d4d";
  const GALLERY_WARNING = "#e6b800";
  const POLL_FAILURE_BUDGET_MS = 120000;
  const POLL_BASE_DELAY_MS = 1500;
  const POLL_MAX_DELAY_MS = 15000;
  const ATTACH_NAME = "Attach from FrameNest";
  const COMPANION_STYLE = [
    "[data-framenest-companion='save'] {",
    "  position: absolute;",
    "  bottom: 8px;",
    "  right: 8px;",
    "  margin: 0;",
    "  z-index: 8;",
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
    "  opacity: 0;",
    "  pointer-events: none;",
    "}",
    "[data-framenest-media-host] [aria-label='Edit image'],",
    "[data-framenest-media-host] [title='Edit image'] {",
    "  position: absolute !important;",
    "  left: 8px !important;",
    "  bottom: 8px !important;",
    "  right: auto !important;",
    "  top: auto !important;",
    "  z-index: 4 !important;",
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
    "[data-framenest-companion='save'][data-framenest-save-kind='failed'] {",
    "  color: #ff4d4d;",
    "  border-color: #ff4d4d;",
    "}",
    "[data-framenest-companion='save'][data-framenest-save-kind='partial'],",
    "[data-framenest-companion='save'][data-framenest-save-kind='unknown'] {",
    "  color: #e6b800;",
    "  border-color: #e6b800;",
    "}",
    ".framenest-save-live {",
    "  position: absolute;",
    "  width: 1px;",
    "  height: 1px;",
    "  overflow: hidden;",
    "  clip: rect(0 0 0 0);",
    "}",
    "[data-framenest-companion='save'][data-framenest-save-kind='busy'] svg {",
    "  opacity: 0.7;",
    "}",
    "[data-framenest-companion='attach'] {",
    "  position: fixed;",
    "  margin: 0;",
    "  z-index: 2147483645;",
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
    "[data-framenest-companion='attach']::-webkit-inner-spin-button,",
    "[data-framenest-companion='attach']::-webkit-outer-spin-button {",
    "  appearance: none;",
    "  -webkit-appearance: none;",
    "  margin: 0;",
    "  display: none;",
    "}",
    "[data-framenest-companion='attach'][data-framenest-attach-visible],",
    "[data-framenest-companion='attach']:focus,",
    "[data-framenest-companion='attach']:focus-visible {",
    "  opacity: 1;",
    "  pointer-events: auto;",
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
      g.appendChild(svgEl("path", { d: "M12 6.5v11M6.5 12h11" }));
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
    button.setAttribute("data-framenest-save-kind", kind);
    let tone = GALLERY_ACCENT;
    if (kind === "failed") {
      tone = GALLERY_DANGER;
    } else if (kind === "partial" || kind === "unknown") {
      tone = GALLERY_WARNING;
    }
    button.style.color = tone;
    button.style.borderColor = tone;
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

  const EDIT_IMAGE_NAME = "Edit image";

  function inHostAccessibleName(node) {
    if (!node || typeof node.getAttribute !== "function") {
      return "";
    }
    const labelled = node.getAttribute("aria-label");
    if (labelled) {
      return labelled;
    }
    const title = node.getAttribute("title");
    if (title) {
      return title;
    }
    const text = node.textContent;
    return typeof text === "string" ? text.replace(/\s+/g, " ").trim() : "";
  }

  function isCandidateEditImageControl(node) {
    if (!node || !node.tagName) {
      return false;
    }
    if (node.getAttribute && node.getAttribute("data-framenest-companion")) {
      return false;
    }
    const tag = String(node.tagName).toLowerCase();
    if (tag === "button" || tag === "a") {
      return true;
    }
    const role = node.getAttribute && node.getAttribute("role");
    if (role === "button") {
      return true;
    }
    return (
      (node.getAttribute && node.getAttribute("aria-label") === EDIT_IMAGE_NAME) ||
      (node.getAttribute && node.getAttribute("title") === EDIT_IMAGE_NAME)
    );
  }

  function applyEditImageGeometry(node) {
    node.style.position = "absolute";
    node.style.left = "8px";
    node.style.bottom = "8px";
    node.style.right = "auto";
    node.style.top = "auto";
    node.style.zIndex = "4";
    if (typeof node.style.setProperty === "function") {
      node.style.setProperty("position", "absolute", "important");
      node.style.setProperty("left", "8px", "important");
      node.style.setProperty("bottom", "8px", "important");
      node.style.setProperty("right", "auto", "important");
      node.style.setProperty("top", "auto", "important");
      node.style.setProperty("z-index", "4", "important");
    }
  }

  function relocateInHostEditImage(host) {
    if (!host) {
      return;
    }
    const visit = (node) => {
      if (!node) {
        return;
      }
      if (node !== host && isCandidateEditImageControl(node) && inHostAccessibleName(node) === EDIT_IMAGE_NAME) {
        applyEditImageGeometry(node);
      }
      const children = node.children || [];
      for (let index = 0; index < children.length; index += 1) {
        visit(children[index]);
      }
    };
    visit(host);
  }

  function haltHostAction(event) {
    event.preventDefault();
    event.stopPropagation();
    event.stopImmediatePropagation();
  }

  function mediaKindForHost(host) {
    if (!host) {
      return "unknown";
    }
    if (typeof host.matches === "function" && host.matches("[data-testid='tweetPhoto']")) {
      return "image";
    }
    if (host.querySelector && host.querySelector("[data-testid='tweetPhoto']")) {
      return "image";
    }
    if (
      typeof host.matches === "function" &&
      (host.matches("[data-testid='videoPlayer']") ||
        host.matches("[data-testid='videoComponent']"))
    ) {
      return "video";
    }
    if (
      host.querySelector &&
      (host.querySelector("[data-testid='videoPlayer']") ||
        host.querySelector("[data-testid='videoComponent']") ||
        host.querySelector("video"))
    ) {
      return "video";
    }
    return "unknown";
  }

  function saveButtonsForPost(postId) {
    const accepted = companion.acceptXPostId(postId);
    if (!accepted) {
      return [];
    }
    return Array.prototype.slice.call(
      document.querySelectorAll(
        "[data-framenest-companion='save'][data-framenest-post-id='" + accepted + "']"
      )
    );
  }

  function announce(message) {
    if (typeof message !== "string" || !message || typeof document.getElementById !== "function") {
      return;
    }
    let live = document.getElementById("framenest-save-live");
    if (!live) {
      live = document.createElement("div");
      live.id = "framenest-save-live";
      live.setAttribute("id", "framenest-save-live");
      live.setAttribute("aria-live", "polite");
      live.setAttribute("aria-atomic", "true");
      live.className = "framenest-save-live";
      const parent = document.body || document.documentElement;
      parent.appendChild(live);
    }
    live.textContent = "";
    live.textContent = message;
  }

  function paintPostSaveOutcome(postId, outcome, claimId) {
    const accepted = companion.acceptXPostId(postId);
    if (!accepted || !outcome) {
      return;
    }
    postOutcomeById.set(accepted, {
      kind: outcome.kind,
      name: outcome.name,
      busy: outcome.busy,
      claimId: claimId || null,
    });
    saveButtonsForPost(accepted).forEach((button) => {
      setSaveStatus(button, outcome.kind, outcome.name, outcome.busy);
    });
    announce(outcome.name);
    if (!outcome.retainInflight && companion.isUuid(claimId)) {
      inflightByClaim.delete(claimId);
    }
  }

  function createSaveControl(accepted, mediaKind) {
    const button = document.createElement("button");
    button.type = "button";
    button.setAttribute("data-framenest-companion", "save");
    button.setAttribute("data-framenest-post-id", accepted.postId);
    button.setAttribute("data-framenest-media-kind", mediaKind || "unknown");
    button.setAttribute("aria-haspopup", "dialog");
    button.setAttribute("aria-expanded", "false");
    setSaveStatus(button, "idle", SAVE_NAME, false);
    ["pointerdown", "mousedown", "click"].forEach((type) => {
      button.addEventListener(type, (event) => {
        haltHostAction(event);
        if (type === "click") {
          openSavePopup(button, accepted);
        }
      });
    });
    return button;
  }

  function closeSavePopup() {
    if (!savePopup) {
      return;
    }
    const state = savePopup;
    savePopup = null;
    window.removeEventListener("resize", state.reposition);
    window.removeEventListener("scroll", state.reposition, true);
    document.removeEventListener("keydown", state.onKey, true);
    document.removeEventListener("mousedown", state.onMouseDown, true);
    window.removeEventListener("message", state.onMessage);
    if (state.host && state.host.parentNode) {
      state.host.parentNode.removeChild(state.host);
    }
    if (state.button && document.contains(state.button)) {
      state.button.setAttribute("aria-expanded", "false");
      if (typeof state.button.focus === "function") {
        state.button.focus();
      }
    }
  }

  function positionSavePopup() {
    if (!savePopup) {
      return;
    }
    const button = savePopup.button;
    const host = savePopup.host;
    if (!button || !document.contains(button)) {
      closeSavePopup();
      return;
    }
    const rect = button.getBoundingClientRect();
    const width = Math.min(360, Math.max(280, window.innerWidth - 16));
    const height = Math.min(520, Math.max(240, window.innerHeight - 16));
    const gap = 8;
    const enoughAbove = rect.top >= height + gap;
    let top = enoughAbove ? rect.top - height - gap : rect.bottom + gap;
    let left = rect.right - width;
    const maxLeft = window.innerWidth - width - 8;
    const maxTop = window.innerHeight - height - 8;
    if (left < 8) {
      left = 8;
    }
    if (left > maxLeft) {
      left = Math.max(8, maxLeft);
    }
    if (top < 8) {
      top = 8;
    }
    if (top > maxTop) {
      top = Math.max(8, maxTop);
    }
    host.style.position = "fixed";
    host.style.left = String(left) + "px";
    host.style.top = String(top) + "px";
    host.style.width = String(width) + "px";
    host.style.height = String(height) + "px";
    host.style.zIndex = "2147483646";
    host.style.margin = "0";
    host.style.padding = "0";
    host.style.border = "0";
  }

  function openSavePopup(button, accepted) {
    if (stale || !button) {
      return;
    }
    if (savePopup && savePopup.button === button) {
      closeSavePopup();
      return;
    }
    closeSavePopup();
    const host = document.createElement("div");
    host.setAttribute("data-framenest-companion-save-host", "");
    host.setAttribute("role", "dialog");
    host.setAttribute("aria-label", SAVE_NAME);
    const shadow = host.attachShadow({ mode: "closed" });
    const style = document.createElement("style");
    style.textContent = [
      ":host { display: block; }",
      ".frame { display: flex; flex-direction: column; width: 100%; height: 100%;",
      "  border: 1px solid #00ff41; border-radius: 8px; background: #000000; overflow: hidden;",
      "  box-shadow: 0 16px 48px rgba(0, 0, 0, 0.65); }",
      "iframe { flex: 1 1 auto; width: 100%; height: 100%; border: 0; background: #000000; }",
    ].join("\n");
    const frame = document.createElement("div");
    frame.className = "frame";
    const iframe = document.createElement("iframe");
    const mediaKind = button.getAttribute("data-framenest-media-kind") || "unknown";
    iframe.src =
      chrome.runtime.getURL("ui/save.html") +
      "#url=" +
      encodeURIComponent(accepted.submittedUrl) +
      "&media=" +
      encodeURIComponent(mediaKind);
    iframe.title = SAVE_NAME;
    iframe.setAttribute("aria-label", SAVE_NAME);
    frame.appendChild(iframe);
    shadow.appendChild(style);
    shadow.appendChild(frame);
    button.setAttribute("aria-expanded", "true");
    const reposition = () => {
      positionSavePopup();
    };
    const onKey = (event) => {
      if (event.key === "Escape") {
        event.preventDefault();
        event.stopPropagation();
        closeSavePopup();
      }
    };
    const onMouseDown = (event) => {
      if (button.contains(event.target) || host === event.target || host.contains(event.target)) {
        return;
      }
      closeSavePopup();
    };
    const onSaveIframeReady = () => {
      if (!savePopup || savePopup.iframe !== iframe) {
        return;
      }
      if (typeof iframe.focus === "function") {
        iframe.focus();
      }
      requestSaveTitleFocus(iframe);
    };
    const onMessage = (event) => {
      if (!savePopup || event.source !== savePopup.iframe.contentWindow) {
        return;
      }
      const data = event.data;
      if (!data || data.v !== companion.PROTOCOL) {
        return;
      }
      if (data.source === "framenest-save-popup" && data.action === "ready") {
        onSaveIframeReady();
        return;
      }
      if (data.source !== "framenest-save-popup") {
        return;
      }
      if (data.action === "cancel") {
        closeSavePopup();
        return;
      }
      if (data.action === "result") {
        const result = data.result || { ok: false };
        closeSavePopup();
        applySaveResult(button, result);
      }
    };
    savePopup = {
      host: host,
      button: button,
      iframe: iframe,
      reposition: reposition,
      onKey: onKey,
      onMouseDown: onMouseDown,
      onMessage: onMessage,
    };
    iframe.addEventListener("load", onSaveIframeReady);
    window.addEventListener("resize", reposition);
    window.addEventListener("scroll", reposition, true);
    document.addEventListener("keydown", onKey, true);
    document.addEventListener("mousedown", onMouseDown, true);
    window.addEventListener("message", onMessage);
    document.documentElement.appendChild(host);
    positionSavePopup();
  }

  function savePopupTargetOrigin() {
    const href = chrome.runtime.getURL("ui/save.html");
    if (typeof href !== "string" || !href) {
      return "";
    }
    const schemeEnd = href.indexOf("://");
    if (schemeEnd < 0) {
      return "";
    }
    const pathStart = href.indexOf("/", schemeEnd + 3);
    return pathStart < 0 ? href : href.slice(0, pathStart);
  }

  function requestSaveTitleFocus(iframe) {
    const origin = savePopupTargetOrigin();
    if (!origin || !iframe || !iframe.contentWindow || typeof iframe.contentWindow.postMessage !== "function") {
      return;
    }
    iframe.contentWindow.postMessage(
      {
        v: companion.PROTOCOL,
        source: "framenest-save-host",
        action: "focus-title",
      },
      origin
    );
  }

  function applySaveResult(button, result) {
    const postId =
      companion.acceptXPostId(button && button.getAttribute && button.getAttribute("data-framenest-post-id")) ||
      companion.acceptXPostId(result && result.postId);
    const outcome = companion.reduceXSaveOutcome(result);
    const claimId = result && result.claimId;
    if (postId) {
      paintPostSaveOutcome(postId, outcome, claimId);
    } else if (button) {
      setSaveStatus(button, outcome.kind, outcome.name, outcome.busy);
    }
    if (companion.isUuid(claimId) && outcome.busy && postId) {
      inflightByClaim.set(claimId, postId);
      pollClaim(claimId, postId, null, 0);
    }
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
      host.setAttribute("data-framenest-media-host", "");
      ensureContainingBlock(host);
      relocateInHostEditImage(host);
      if (injected.has(host)) {
        return;
      }
      if (host.querySelector(":scope > [data-framenest-companion='save']")) {
        injected.add(host);
        return;
      }
      const button = createSaveControl(accepted, mediaKindForHost(host));
      host.appendChild(button);
      const remembered = postOutcomeById.get(accepted.postId);
      if (remembered) {
        setSaveStatus(button, remembered.kind, remembered.name, remembered.busy);
      }
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

  function isDocumentRoot(node) {
    return !node || node === document.documentElement || node === document.body;
  }

  function composerChromeHasSignal(node) {
    if (!node || isEditableComposerNode(node) || isDocumentRoot(node)) {
      return false;
    }
    if (matchesAny(node, contract.composerChromeSelectors)) {
      return true;
    }
    if (
      matchesAny(node, contract.composerToolbarSelectors) ||
      first(node, contract.composerToolbarSelectors)
    ) {
      return true;
    }
    if (first(node, contract.composerFileInputs)) {
      return true;
    }
    return Boolean(
      matchesAny(node, contract.composerMediaButtonSelectors) ||
        first(node, contract.composerMediaButtonSelectors)
    );
  }

  function findComposerChrome(composerRoot) {
    if (!composerRoot) {
      return null;
    }
    let node = composerRoot;
    let hops = 0;
    while (node && hops < 48) {
      if (isDocumentRoot(node)) {
        return null;
      }
      if (composerChromeHasSignal(node) && (node === composerRoot || node.contains(composerRoot))) {
        return node;
      }
      node = node.parentElement;
      hops += 1;
    }
    return null;
  }

  function findComposerTextRow(composerRoot, composerChrome) {
    if (!composerRoot || !composerChrome) {
      return null;
    }
    const explicit =
      first(composerChrome, contract.composerTextRowSelectors) ||
      (composerChrome.contains(composerRoot) ? first(composerRoot, contract.composerTextRowSelectors) : null);
    if (explicit && composerChrome.contains(explicit) && !isEditableComposerNode(explicit)) {
      return explicit;
    }
    const editable = isEditableComposerNode(composerRoot)
      ? composerRoot
      : first(composerChrome, contract.composerRoots);
    if (!editable || !composerChrome.contains(editable)) {
      return null;
    }
    let row = editable.parentElement;
    while (row && isEditableComposerNode(row) && row !== composerChrome) {
      row = row.parentElement;
    }
    if (!row) {
      return null;
    }
    if (row !== composerChrome && !composerChrome.contains(row)) {
      return null;
    }
    if (matchesAny(row, contract.composerToolbarSelectors) || isEditableComposerNode(row)) {
      return null;
    }
    return row;
  }

  function findComposerEditable(composerRoot, composerChrome) {
    if (isEditableComposerNode(composerRoot)) {
      return composerRoot;
    }
    const selectors = ["[data-testid='tweetTextarea_0']", "[aria-label='Post your reply']"];
    if (composerChrome) {
      const fromChrome = first(composerChrome, selectors);
      if (fromChrome) {
        return fromChrome;
      }
    }
    return composerRoot ? first(composerRoot, selectors) : null;
  }

  function plusPlusTokenAtCaret(textBeforeCaret) {
    if (typeof textBeforeCaret !== "string" || textBeforeCaret.length < 2) {
      return false;
    }
    if (textBeforeCaret.slice(textBeforeCaret.length - 2) !== "++") {
      return false;
    }
    if (textBeforeCaret.length === 2) {
      return true;
    }
    return /\s/.test(textBeforeCaret.charAt(textBeforeCaret.length - 3));
  }

  function consumePlusPlusFromValue(value, caret) {
    if (typeof value !== "string" || typeof caret !== "number" || caret < 2 || caret > value.length) {
      return null;
    }
    if (!plusPlusTokenAtCaret(value.slice(0, caret))) {
      return null;
    }
    return {
      value: value.slice(0, caret - 2) + value.slice(caret),
      caret: caret - 2,
    };
  }

  function composerTextBeforeCaret(editable) {
    if (!editable) {
      return "";
    }
    if (typeof editable.value === "string" && typeof editable.selectionStart === "number") {
      return editable.value.slice(0, editable.selectionStart);
    }
    const doc = editable.ownerDocument || document;
    const view = doc.defaultView || window;
    const selection = view.getSelection ? view.getSelection() : null;
    if (!selection || selection.rangeCount === 0) {
      return editable.textContent || "";
    }
    try {
      const range = selection.getRangeAt(0);
      const root = range.endContainer;
      if (root !== editable && !(editable.contains && editable.contains(root))) {
        return editable.textContent || "";
      }
      const pre = range.cloneRange();
      pre.selectNodeContents(editable);
      pre.setEnd(range.endContainer, range.endOffset);
      return pre.toString();
    } catch {
      return editable.textContent || "";
    }
  }

  function deleteBeforeCaret(editable, count) {
    if (!editable || count <= 0) {
      return false;
    }
    if (typeof editable.value === "string" && typeof editable.selectionStart === "number") {
      const caret = editable.selectionStart;
      if (caret < count) {
        return false;
      }
      editable.value = editable.value.slice(0, caret - count) + editable.value.slice(caret);
      const next = caret - count;
      editable.selectionStart = next;
      editable.selectionEnd = next;
      return true;
    }
    const doc = editable.ownerDocument || document;
    const view = doc.defaultView || window;
    const selection = view.getSelection ? view.getSelection() : null;
    if (!selection || typeof selection.modify !== "function") {
      return false;
    }
    if (selection.rangeCount && !selection.isCollapsed && typeof selection.collapseToEnd === "function") {
      selection.collapseToEnd();
    }
    for (let i = 0; i < count; i += 1) {
      selection.modify("extend", "backward", "character");
    }
    if (typeof selection.deleteFromDocument === "function") {
      selection.deleteFromDocument();
      return true;
    }
    return false;
  }

  function fileInputStillLive(fileInput) {
    return Boolean(fileInput && document.contains(fileInput));
  }

  function fileInputForComposer(composerRoot) {
    if (!composerRoot) {
      return null;
    }
    const composerChrome = findComposerChrome(composerRoot);
    if (!composerChrome) {
      return null;
    }
    const fileInput =
      first(composerChrome, contract.composerFileInputs) ||
      first(composerRoot, contract.composerFileInputs);
    if (!fileInputStillLive(fileInput)) {
      return null;
    }
    return fileInput;
  }

  function bindComposerIfLive(composerRoot) {
    const fileInput = fileInputForComposer(composerRoot);
    if (!fileInput) {
      return null;
    }
    boundComposer = { root: composerRoot, fileInput };
    return fileInput;
  }

  function focusedComposerRoot() {
    const active = document.activeElement;
    if (!active) {
      return null;
    }
    if (
      active.matches &&
      (active.matches("[data-testid='tweetTextarea_0']") ||
        active.matches("[aria-label='Post your reply']"))
    ) {
      return active;
    }
    if (active.closest) {
      return (
        active.closest("[data-testid='tweetTextarea_0']") ||
        active.closest("[aria-label='Post your reply']")
      );
    }
    return null;
  }

  function resolveLiveComposerFileInput() {
    if (boundComposer && fileInputStillLive(boundComposer.fileInput)) {
      return boundComposer.fileInput;
    }
    return bindComposerIfLive(focusedComposerRoot());
  }

  function completeAttachTransfer(port, filename, mediaType, chunks, total) {
    const fileInput = resolveLiveComposerFileInput();
    if (!fileInput) {
      port.postMessage({
        v: companion.PROTOCOL,
        type: companion.TYPES.ERROR,
        payload: { error: "composer_unbound" },
      });
      return { ok: false, error: "composer_unbound" };
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
    return { ok: true, bytes: total };
  }

  function mountedAttachNode(composerRoot) {
    const fromMap = composerRoot && attachByComposer.get(composerRoot);
    if (fromMap && document.contains(fromMap)) {
      return fromMap;
    }
    return null;
  }

  function findAttachForEditable(editable) {
    if (!editable) {
      return null;
    }
    const mapped = attachByComposer.get(editable);
    if (mapped && document.contains(mapped)) {
      return mapped;
    }
    const nodes = document.querySelectorAll("[data-framenest-companion='attach']");
    for (let i = 0; i < nodes.length; i += 1) {
      const button = nodes[i];
      const bound = attachEditable.get(button);
      if (!bound) {
        continue;
      }
      if (bound === editable) {
        return button;
      }
      if (bound.contains && bound.contains(editable)) {
        return button;
      }
      if (editable.contains && editable.contains(bound)) {
        return button;
      }
    }
    return null;
  }

  function existingAttachFor(composerChrome, editable) {
    const fromEditable = findAttachForEditable(editable);
    if (fromEditable) {
      return fromEditable;
    }
    if (!composerChrome) {
      return null;
    }
    const nodes = document.querySelectorAll("[data-framenest-companion='attach']");
    for (let i = 0; i < nodes.length; i += 1) {
      const button = nodes[i];
      const bound = attachEditable.get(button);
      if (bound && composerChrome.contains(bound) && document.contains(button)) {
        return button;
      }
    }
    return null;
  }

  function attachPopupIsOpen() {
    return Boolean(attachPopup && attachPopup.host && document.contains(attachPopup.host));
  }

  function composerHoldsFocus(editable, button) {
    const active = document.activeElement;
    if (!active) {
      return false;
    }
    if (button && (active === button || (button.contains && button.contains(active)))) {
      return true;
    }
    if (editable && (active === editable || (editable.contains && editable.contains(active)))) {
      return true;
    }
    return false;
  }

  function positionAttachControl(button) {
    const editable = attachEditable.get(button);
    if (!button || !editable || !document.contains(button) || !document.contains(editable)) {
      return;
    }
    if (typeof editable.getBoundingClientRect !== "function") {
      return;
    }
    const rect = editable.getBoundingClientRect();
    const size = 32;
    const inset = 4;
    const top = rect.top + rect.height / 2 - size / 2;
    let left = rect.right - size - inset;
    if (left < 8) {
      left = 8;
    }
    button.style.position = "fixed";
    button.style.top = String(top) + "px";
    button.style.left = String(left) + "px";
    button.style.right = "auto";
    button.style.bottom = "auto";
    button.style.margin = "0";
    button.style.zIndex = "2147483645";
  }

  function repositionVisibleAttaches() {
    const nodes = document.querySelectorAll("[data-framenest-companion='attach']");
    for (let i = 0; i < nodes.length; i += 1) {
      const button = nodes[i];
      if (button.hasAttribute("data-framenest-attach-visible")) {
        positionAttachControl(button);
      }
    }
  }

  function ensureAttachPositionListeners() {
    if (attachPositionBound) {
      return;
    }
    attachPositionBound = true;
    window.addEventListener("resize", repositionVisibleAttaches);
    window.addEventListener("scroll", repositionVisibleAttaches, true);
  }

  function showAttachControl(button) {
    if (!button || !document.contains(button)) {
      return;
    }
    positionAttachControl(button);
    button.setAttribute("data-framenest-attach-visible", "");
  }

  function syncAttachVisibility(editable, button) {
    if (!button || !document.contains(button)) {
      return;
    }
    if (attachPopupIsOpen() && attachPopup.button === button) {
      showAttachControl(button);
      return;
    }
    if (composerHoldsFocus(editable, button)) {
      showAttachControl(button);
      return;
    }
    button.removeAttribute("data-framenest-attach-visible");
  }

  function bindComposerAttachVisibility(editable, button) {
    const show = () => {
      showAttachControl(button);
    };
    const hideSoon = () => {
      window.setTimeout(() => {
        syncAttachVisibility(editable, button);
      }, 0);
    };
    editable.addEventListener("focusin", show, true);
    editable.addEventListener("focus", show, true);
    editable.addEventListener("focusout", hideSoon, true);
    button.addEventListener("focusin", show, true);
    button.addEventListener("focusout", hideSoon, true);
  }

  function onComposerFocusIn(event) {
    const target = event.target;
    if (!target) {
      return;
    }
    if (target.getAttribute && target.getAttribute("data-framenest-companion") === "attach") {
      return;
    }
    let editable = null;
    if (target.matches && (target.matches("[data-testid='tweetTextarea_0']") || target.matches("[aria-label='Post your reply']"))) {
      editable = target;
    } else if (target.closest) {
      editable =
        target.closest("[data-testid='tweetTextarea_0']") || target.closest("[aria-label='Post your reply']");
    }
    if (!editable) {
      return;
    }
    injectAttach(editable);
    bindComposerIfLive(editable);
    const button = findAttachForEditable(editable);
    if (button) {
      showAttachControl(button);
    }
  }

  function ensureComposerFocusCapture() {
    if (composerFocusBound) {
      return;
    }
    composerFocusBound = true;
    document.addEventListener("focusin", onComposerFocusIn, true);
  }

  function pruneOrphanAttaches() {
    const nodes = document.querySelectorAll("[data-framenest-companion='attach']");
    for (let i = 0; i < nodes.length; i += 1) {
      const button = nodes[i];
      if (attachPopupIsOpen() && attachPopup.button === button) {
        continue;
      }
      const editable = attachEditable.get(button);
      if (editable && document.contains(editable)) {
        continue;
      }
      if (button.parentNode) {
        button.parentNode.removeChild(button);
      }
    }
  }

  function closeAttachPopup() {
    if (!attachPopup) {
      return;
    }
    const state = attachPopup;
    attachPopup = null;
    window.removeEventListener("resize", state.reposition);
    window.removeEventListener("scroll", state.reposition, true);
    document.removeEventListener("keydown", state.onKey, true);
    document.removeEventListener("mousedown", state.onMouseDown, true);
    if (state.host && state.host.parentNode) {
      state.host.parentNode.removeChild(state.host);
    }
    if (state.button && document.contains(state.button)) {
      state.button.removeAttribute("aria-expanded");
      syncAttachVisibility(attachEditable.get(state.button), state.button);
    }
  }

  function positionAttachPopup() {
    if (!attachPopupIsOpen()) {
      return;
    }
    const button = attachPopup.button;
    const host = attachPopup.host;
    if (!button || !document.contains(button)) {
      closeAttachPopup();
      return;
    }
    const rect = button.getBoundingClientRect();
    const width = Math.min(320, Math.max(280, window.innerWidth - 16));
    const height = attachPopup.compact
      ? Math.min(128, Math.max(96, window.innerHeight - 16))
      : Math.min(360, Math.max(280, window.innerHeight - 16));
    const gap = 8;
    const enoughAbove = rect.top >= height + gap;
    let top = enoughAbove ? rect.top - height - gap : rect.bottom + gap;
    let left = rect.right - width;
    const maxLeft = window.innerWidth - width - 8;
    const maxTop = window.innerHeight - height - 8;
    if (left < 8) {
      left = 8;
    }
    if (left > maxLeft) {
      left = Math.max(8, maxLeft);
    }
    if (top < 8) {
      top = 8;
    }
    if (top > maxTop) {
      top = Math.max(8, maxTop);
    }
    host.style.position = "fixed";
    host.style.left = String(left) + "px";
    host.style.top = String(top) + "px";
    host.style.width = String(width) + "px";
    host.style.height = String(height) + "px";
    host.style.zIndex = "2147483646";
    host.style.margin = "0";
    host.style.padding = "0";
    host.style.border = "0";
  }

  function applyPickerLayout(payload) {
    if (!attachPopupIsOpen()) {
      return;
    }
    if (!payload || (payload.compact !== true && payload.compact !== false)) {
      return;
    }
    attachPopup.compact = payload.compact === true;
    positionAttachPopup();
  }

  function openAttachPopup(button, composerChrome, options) {
    if (stale || !button) {
      return;
    }
    const keepOpen = Boolean(options && options.keepOpen);
    if (attachPopupIsOpen() && attachPopup.button === button) {
      if (keepOpen) {
        return;
      }
      closeAttachPopup();
      return;
    }
    closeAttachPopup();
    const host = document.createElement("div");
    host.setAttribute("data-framenest-companion-popup-host", "");
    host.setAttribute("role", "dialog");
    host.setAttribute("aria-label", ATTACH_NAME);
    const shadow = host.attachShadow({ mode: "closed" });
    const style = document.createElement("style");
    style.textContent = [
      ":host { display: block; }",
      ".frame { display: flex; flex-direction: column; width: 100%; height: 100%;",
      "  border: 1px solid #00ff41; border-radius: 8px; background: #0a0e0a; overflow: hidden;",
      "  box-shadow: 0 16px 48px rgba(0, 0, 0, 0.65); }",
      ".close { align-self: flex-end; margin: 6px 6px 0; padding: 2px 8px; border: 0;",
      "  border-radius: 6px; background: transparent; color: #a8b8a8; cursor: pointer;",
      "  font: 700 1rem ui-monospace, monospace; line-height: 1; }",
      ".close:hover, .close:focus-visible { color: #ff4d4d; }",
      "iframe { flex: 1 1 auto; width: 100%; border: 0; background: #0a0e0a; }",
    ].join("\n");
    const frame = document.createElement("div");
    frame.className = "frame";
    const closeBtn = document.createElement("button");
    closeBtn.type = "button";
    closeBtn.className = "close";
    closeBtn.setAttribute("aria-label", "Close FrameNest picker");
    closeBtn.textContent = "\u2715";
    closeBtn.addEventListener("click", () => {
      closeAttachPopup();
    });
    const iframe = document.createElement("iframe");
    iframe.src = chrome.runtime.getURL("ui/picker.html");
    iframe.title = "FrameNest search";
    iframe.setAttribute("aria-label", "Search memes");
    frame.appendChild(closeBtn);
    frame.appendChild(iframe);
    shadow.appendChild(style);
    shadow.appendChild(frame);
    document.documentElement.appendChild(host);
    button.setAttribute("aria-expanded", "true");
    button.setAttribute("data-framenest-attach-visible", "");
    const reposition = () => {
      positionAttachPopup();
    };
    const onKey = (event) => {
      if (event.key === "Escape") {
        event.preventDefault();
        event.stopPropagation();
        closeAttachPopup();
      }
    };
    const onMouseDown = (event) => {
      if (button.contains(event.target) || host === event.target || host.contains(event.target)) {
        return;
      }
      closeAttachPopup();
    };
    attachPopup = {
      host: host,
      button: button,
      chrome: composerChrome,
      iframe: iframe,
      compact: true,
      reposition: reposition,
      onKey: onKey,
      onMouseDown: onMouseDown,
    };
    window.addEventListener("resize", reposition);
    window.addEventListener("scroll", reposition, true);
    document.addEventListener("keydown", onKey, true);
    document.addEventListener("mousedown", onMouseDown, true);
    positionAttachPopup();
  }

  let plusPlusOpenGuard = false;

  function openAttachPickerFromKeyboard(button, composerRoot, fileInput, composerChrome) {
    if (stale || !button) {
      return;
    }
    if (plusPlusOpenGuard) {
      return;
    }
    plusPlusOpenGuard = true;
    window.setTimeout(() => {
      plusPlusOpenGuard = false;
    }, 0);
    boundComposer = { root: composerRoot, fileInput };
    void request(companion.TYPES.ACK, { composerBound: true }).then(() => {
      openAttachPopup(button, composerChrome, { keepOpen: true });
    });
  }

  function handleComposerPlusPlusInsert(event, editable, button, composerRoot, fileInput, composerChrome) {
    if (!event || event.isComposing) {
      return;
    }
    const inputType = event.inputType || "insertText";
    if (inputType !== "insertText" && inputType !== "insertFromPaste" && inputType !== "insertFromDrop") {
      return;
    }
    const data = event.data;
    if (data !== "+" && data !== "++") {
      return;
    }
    const before = composerTextBeforeCaret(editable);
    if (!plusPlusTokenAtCaret(before + data)) {
      return;
    }
    if (typeof event.preventDefault === "function") {
      event.preventDefault();
    }
    if (data === "+") {
      deleteBeforeCaret(editable, 1);
    }
    openAttachPickerFromKeyboard(button, composerRoot, fileInput, composerChrome);
  }

  function handleComposerPlusPlusFallback(event, editable, button, composerRoot, fileInput, composerChrome) {
    if (event && event.isComposing) {
      return;
    }
    const before = composerTextBeforeCaret(editable);
    if (!plusPlusTokenAtCaret(before)) {
      return;
    }
    deleteBeforeCaret(editable, 2);
    openAttachPickerFromKeyboard(button, composerRoot, fileInput, composerChrome);
  }

  function bindComposerPlusPlus(editable, button, composerRoot, fileInput, composerChrome) {
    if (!editable || plusPlusBound.has(editable)) {
      return;
    }
    plusPlusBound.add(editable);
    editable.addEventListener("beforeinput", (event) => {
      handleComposerPlusPlusInsert(event, editable, button, composerRoot, fileInput, composerChrome);
    });
    const onFallback = (event) => {
      handleComposerPlusPlusFallback(event, editable, button, composerRoot, fileInput, composerChrome);
    };
    editable.addEventListener("input", onFallback);
    editable.addEventListener("compositionend", onFallback);
  }

  function createAttachControl(composerRoot, fileInput, composerChrome) {
    const button = document.createElement("button");
    button.type = "button";
    button.setAttribute("data-framenest-companion", "attach");
    button.setAttribute("aria-label", ATTACH_NAME);
    button.setAttribute("title", ATTACH_NAME);
    button.setAttribute("aria-haspopup", "dialog");
    button.setAttribute("aria-expanded", "false");
    button.appendChild(attachIconSvg());
    ["pointerdown", "mousedown", "click"].forEach((type) => {
      button.addEventListener(type, (event) => {
        haltHostAction(event);
        if (type !== "click" || stale) {
          return;
        }
        boundComposer = { root: composerRoot, fileInput };
        void request(companion.TYPES.ACK, { composerBound: true }).then(() => {
          openAttachPopup(button, composerChrome);
        });
      });
    });
    return button;
  }

  function injectAttach(composerRoot) {
    const composerChrome = findComposerChrome(composerRoot);
    if (injected.has(composerRoot)) {
      const mounted = mountedAttachNode(composerRoot);
      if (mounted && document.contains(mounted)) {
        if (mounted.hasAttribute("data-framenest-attach-visible")) {
          positionAttachControl(mounted);
        }
        const liveEditable = findComposerEditable(composerRoot, composerChrome);
        const liveFile =
          first(composerChrome, contract.composerFileInputs) ||
          first(composerRoot, contract.composerFileInputs);
        if (liveEditable) {
          bindComposerPlusPlus(liveEditable, mounted, composerRoot, liveFile, composerChrome);
        }
        return;
      }
    }
    if (!composerChrome) {
      return;
    }
    const fileInput =
      first(composerChrome, contract.composerFileInputs) ||
      first(composerRoot, contract.composerFileInputs);
    if (!fileInput) {
      return;
    }
    const editable = findComposerEditable(composerRoot, composerChrome);
    if (!editable) {
      return;
    }
    const existing = existingAttachFor(composerChrome, editable) || mountedAttachNode(composerRoot);
    if (existing && document.contains(existing)) {
      attachByComposer.set(composerRoot, existing);
      attachByComposer.set(editable, existing);
      injected.add(composerRoot);
      bindComposerPlusPlus(editable, existing, composerRoot, fileInput, composerChrome);
      if (existing.hasAttribute("data-framenest-attach-visible")) {
        positionAttachControl(existing);
      }
      return;
    }
    const button = createAttachControl(composerRoot, fileInput, composerChrome);
    attachByComposer.set(composerRoot, button);
    attachByComposer.set(editable, button);
    attachEditable.set(button, editable);
    document.documentElement.appendChild(button);
    ensureAttachPositionListeners();
    ensureComposerFocusCapture();
    bindComposerAttachVisibility(editable, button);
    bindComposerPlusPlus(editable, button, composerRoot, fileInput, composerChrome);
    positionAttachControl(button);
    syncAttachVisibility(editable, button);
    injected.add(composerRoot);
  }

  if (globalThis.FrameNestXAdapterTestHooks) {
    globalThis.FrameNestXAdapterTestHooks.findComposerChrome = findComposerChrome;
    globalThis.FrameNestXAdapterTestHooks.findComposerTextRow = findComposerTextRow;
    globalThis.FrameNestXAdapterTestHooks.injectAttach = injectAttach;
    globalThis.FrameNestXAdapterTestHooks.injectSave = injectSave;
    globalThis.FrameNestXAdapterTestHooks.saveIconSvg = saveIconSvg;
    globalThis.FrameNestXAdapterTestHooks.onComposerFocusIn = onComposerFocusIn;
    globalThis.FrameNestXAdapterTestHooks.bindComposerIfLive = bindComposerIfLive;
    globalThis.FrameNestXAdapterTestHooks.resolveLiveComposerFileInput = resolveLiveComposerFileInput;
    globalThis.FrameNestXAdapterTestHooks.completeAttachTransfer = completeAttachTransfer;
    globalThis.FrameNestXAdapterTestHooks.plusPlusTokenAtCaret = plusPlusTokenAtCaret;
    globalThis.FrameNestXAdapterTestHooks.consumePlusPlusFromValue = consumePlusPlusFromValue;
    globalThis.FrameNestXAdapterTestHooks.applySaveResult = applySaveResult;
    globalThis.FrameNestXAdapterTestHooks.createSaveControl = createSaveControl;
    globalThis.FrameNestXAdapterTestHooks.closeSavePopup = closeSavePopup;
    globalThis.FrameNestXAdapterTestHooks.mediaKindForHost = mediaKindForHost;
    globalThis.FrameNestXAdapterTestHooks.paintPostSaveOutcome = paintPostSaveOutcome;
    globalThis.FrameNestXAdapterTestHooks.pollClaim = pollClaim;
    globalThis.FrameNestXAdapterTestHooks.recover = recover;
    globalThis.FrameNestXAdapterTestHooks.relocateInHostEditImage = relocateInHostEditImage;
    return;
  }

  async function pollClaim(claimId, postId, failureStartedAt, attempt) {
    const result = await request(companion.TYPES.POLL_CLAIM, { claimId: claimId });
    const resolvedPostId =
      companion.acceptXPostId(result && result.postId) || companion.acceptXPostId(postId);
    if (!result.ok) {
      const origin = failureStartedAt || Date.now();
      const elapsed = Date.now() - origin;
      if (elapsed < POLL_FAILURE_BUDGET_MS) {
        const step = attempt || 0;
        const delay = Math.min(
          POLL_BASE_DELAY_MS * Math.pow(1.5, step),
          POLL_MAX_DELAY_MS
        );
        window.setTimeout(() => {
          pollClaim(claimId, resolvedPostId, origin, step + 1);
        }, delay);
        return;
      }
      if (resolvedPostId) {
        paintPostSaveOutcome(
          resolvedPostId,
          companion.reduceXSaveOutcome({ ok: false, error: "network_failed", ambiguous: true }),
          claimId
        );
      }
      return;
    }
    const outcome = companion.reduceXSaveOutcome(result);
    if (resolvedPostId) {
      if (outcome.busy) {
        inflightByClaim.set(claimId, resolvedPostId);
      }
      paintPostSaveOutcome(resolvedPostId, outcome, claimId);
    }
    if (outcome.busy) {
      window.setTimeout(() => {
        pollClaim(claimId, resolvedPostId, null, 0);
      }, POLL_BASE_DELAY_MS);
    }
  }

  async function recover() {
    const result = await request(companion.TYPES.RECOVER_INFLIGHT, {});
    if (!result.ok) {
      return;
    }
    const records = Array.isArray(result.claims) ? result.claims : [];
    const claimIds = Array.isArray(result.claimIds) ? result.claimIds : [];
    const seen = {};
    const busyOutcome = companion.reduceXSaveOutcome({ ok: true });
    records.forEach((record) => {
      if (!record || !companion.isUuid(record.claimId) || seen[record.claimId]) {
        return;
      }
      seen[record.claimId] = true;
      const recoveredPostId = companion.acceptXPostId(record.postId);
      if (recoveredPostId) {
        inflightByClaim.set(record.claimId, recoveredPostId);
        paintPostSaveOutcome(recoveredPostId, busyOutcome, record.claimId);
      }
      pollClaim(record.claimId, recoveredPostId, null, 0);
    });
    claimIds.forEach((claimId) => {
      if (!companion.isUuid(claimId) || seen[claimId]) {
        return;
      }
      seen[claimId] = true;
      pollClaim(claimId, inflightByClaim.get(claimId) || null, null, 0);
    });
  }

  chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
    const parsed = companion.dropUnknown(message);
    if (!parsed) {
      return false;
    }
    if (parsed.type === companion.TYPES.DISMISS_PICKER) {
      closeAttachPopup();
      sendResponse({ ok: true });
      return false;
    }
    if (parsed.type === companion.TYPES.PICKER_LAYOUT) {
      applyPickerLayout(parsed.payload || {});
      sendResponse({ ok: true });
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
        completeAttachTransfer(port, filename, mediaType, chunks, total);
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
    pruneOrphanAttaches();
    repositionVisibleAttaches();
  }

  const observer = new MutationObserver(() => scan());
  observer.observe(document.documentElement, { childList: true, subtree: true });
  ensureComposerFocusCapture();
  ensureAttachPositionListeners();
  scan();
  recover();
})();
