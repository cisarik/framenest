(function () {
  const companion = globalThis.FrameNestCompanion;
  const WEB_PROTOCOL = "framenest.companion.web.v1";
  const WEB_TYPES = Object.freeze({
    WEB_READY: "web_ready",
    HOST_HELLO: "host_hello",
    HOST_ACK: "host_ack",
    ATTACH_REQUEST: "attach_request",
    ATTACH_RESULT: "attach_result",
  });
  const HANDSHAKE_WAIT_MS = 10000;
  const RELOAD_RECOVERY = companion.EXTENSION_CONTEXT_RECOVERY_COPY;
  let runtimeStale = false;
  let runtimeStaleHandler = function handleEarlyRuntimeStale() {};

  function acceptIncomingWebMessage(event, iframeWindow, storedOrigin) {
    if (!iframeWindow || !event || event.source !== iframeWindow) {
      return null;
    }
    if (typeof storedOrigin !== "string" || event.origin !== storedOrigin) {
      return null;
    }
    if (!companion.acceptFrameNestOrigin(event.origin)) {
      return null;
    }
    const data = event.data;
    if (!data || typeof data !== "object" || data.v !== WEB_PROTOCOL || typeof data.type !== "string") {
      return null;
    }
    return data;
  }

  function attachIdsFromWebRequest(data) {
    const payload = data && data.payload;
    if (!payload || typeof payload !== "object") {
      return null;
    }
    if (!companion.isUuid(payload.mediaId) || !companion.isUuid(payload.locationId)) {
      return null;
    }
    return { mediaId: payload.mediaId, locationId: payload.locationId };
  }

  function framingFailureCopy() {
    return "FrameNest did not load in this panel.";
  }

  function companionHostMissingCopy() {
    return "This FrameNest server cannot host companion Attach yet. The library below is an older web without the companion host.";
  }

  function handshakeTimeoutCopy(frameLoaded) {
    return frameLoaded ? companionHostMissingCopy() : framingFailureCopy();
  }

  globalThis.FrameNestSidebarBridge = {
    WEB_PROTOCOL,
    WEB_TYPES,
    acceptIncomingWebMessage,
    attachIdsFromWebRequest,
    framingFailureCopy,
    companionHostMissingCopy,
    handshakeTimeoutCopy,
  };

  const REVIEW = companion.REVIEW_INBOX;

  function renderReviewInboxList(listNode, items) {
    if (!listNode) {
      return;
    }
    while (listNode.firstChild) {
      listNode.removeChild(listNode.firstChild);
    }
    const doc = listNode.ownerDocument || globalThis.document;
    (Array.isArray(items) ? items : []).forEach((item) => {
      if (!item || typeof item.title !== "string" || !companion.isUuid(item.media_id)) {
        return;
      }
      const li = doc.createElement("li");
      const button = doc.createElement("button");
      button.type = "button";
      button.className =
        "review-history-button " +
        (item.analyzed === true
          ? "review-history-button--analyzed"
          : "review-history-button--pending");
      if (typeof button.setAttribute === "function") {
        button.setAttribute("data-media-id", item.media_id);
      }
      button.textContent = item.title;
      if (typeof li.appendChild === "function") {
        li.appendChild(button);
      } else {
        li.textContent = item.title;
        if (typeof li.setAttribute === "function") {
          li.setAttribute("data-media-id", item.media_id);
        }
      }
      listNode.appendChild(li);
    });
  }

  function setReviewHistoryExpanded(toggleNode, historyNode, expanded) {
    const next = Boolean(expanded && toggleNode && toggleNode.disabled !== true);
    if (toggleNode) {
      toggleNode.setAttribute("aria-expanded", next ? "true" : "false");
    }
    if (historyNode) {
      historyNode.hidden = !next;
    }
    return next;
  }

  function renderReviewCollections(nodes, rawItems) {
    const historyItems = companion.sanitizeReviewInboxItems(rawItems);
    renderReviewInboxList(nodes.historyList, historyItems);
    nodes.toggle.disabled = historyItems.length === 0;
    if (!historyItems.length) {
      setReviewHistoryExpanded(nodes.toggle, nodes.history, false);
    }
    return { historyItems };
  }

  function hideReviewCollections(nodes, disableToggle) {
    renderReviewInboxList(nodes.historyList, []);
    nodes.toggle.disabled = disableToggle === true;
    setReviewHistoryExpanded(nodes.toggle, nodes.history, false);
  }

  function markRuntimeStale(error) {
    if (runtimeStale) {
      return;
    }
    runtimeStale = true;
    runtimeStaleHandler();
    void error;
  }

  function runtimeObject() {
    return globalThis.chrome && globalThis.chrome.runtime;
  }

  function staleRuntimeResult() {
    return { ok: false, error: "extension_context_invalidated", stale: true };
  }

  function guardInvalidatedRuntime(runtime, error) {
    if (!companion.isExtensionContextInvalidated(runtime, error)) {
      return false;
    }
    markRuntimeStale(error);
    return true;
  }

  function runtimeUrl(resource) {
    if (runtimeStale) {
      return "";
    }
    const runtime = runtimeObject();
    if (guardInvalidatedRuntime(runtime)) {
      return "";
    }
    try {
      return runtime.getURL(resource);
    } catch (error) {
      if (guardInvalidatedRuntime(runtime, error)) {
        return "";
      }
      throw error;
    }
  }

  function reviewOverlayUrl(mediaId) {
    if (!companion.isUuid(mediaId)) {
      return "";
    }
    const base = runtimeUrl("ui/review.html");
    return base ? base + "#media=" + mediaId : "";
  }

  function openReviewOverlay(mediaId, dialogNode, frameNode) {
    if (!companion.isUuid(mediaId) || !dialogNode || !frameNode) {
      return false;
    }
    const url = reviewOverlayUrl(mediaId);
    if (!url) {
      return false;
    }
    frameNode.setAttribute("src", url);
    if (typeof dialogNode.show === "function") {
      dialogNode.show();
    } else {
      dialogNode.setAttribute("open", "");
    }
    return true;
  }

  function closeReviewOverlay(dialogNode, frameNode) {
    if (frameNode) {
      frameNode.removeAttribute("src");
    }
    if (!dialogNode) {
      return;
    }
    if (typeof dialogNode.close === "function" && dialogNode.open) {
      dialogNode.close();
      return;
    }
    dialogNode.removeAttribute("open");
  }

  function extensionOrigin() {
    try {
      if (typeof location !== "undefined" && location.protocol === "chrome-extension:") {
        return location.origin;
      }
    } catch {
      /* ignore */
    }
    const raw = runtimeUrl("ui/review.html");
    if (raw) {
      try {
        return new URL(raw).origin;
      } catch {
        if (raw.indexOf("chrome-extension://") === 0) {
          return raw.split("/").slice(0, 3).join("/");
        }
      }
    }
    return "";
  }

  globalThis.FrameNestReviewInbox = {
    POLL_MS: REVIEW.pollMs,
    renderList: renderReviewInboxList,
    renderCollections: renderReviewCollections,
    hideCollections: hideReviewCollections,
    setHistoryExpanded: setReviewHistoryExpanded,
    request: request,
    runtimeUrl: runtimeUrl,
    overlayUrl: reviewOverlayUrl,
    openOverlay: openReviewOverlay,
    closeOverlay: closeReviewOverlay,
  };

  const originInput = document.getElementById("origin");
  const shellStatus = document.getElementById("shell-status");
  const frame = document.getElementById("frame");
  const chromeAction = document.getElementById("chrome-action");
  const settingsDialog = document.getElementById("settings-dialog");
  const settingsOpen = document.getElementById("settings-open");
  const settingsClose = document.getElementById("settings-close");
  const settingsConnect = document.getElementById("settings-connect");
  const reviewHistoryToggle = document.getElementById("review-history-toggle");
  const reviewHistory = document.getElementById("review-history");
  const reviewHistoryList = document.getElementById("review-history-list");
  const reviewDialog = document.getElementById("review-dialog");
  const reviewFrame = document.getElementById("review-frame");
  if (
    !originInput ||
    !shellStatus ||
    !frame ||
    !chromeAction ||
    !settingsDialog ||
    !settingsOpen ||
    !settingsClose ||
    !settingsConnect ||
    !reviewHistoryToggle ||
    !reviewHistory ||
    !reviewHistoryList ||
    !reviewDialog ||
    !reviewFrame
  ) {
    return;
  }

  let storedOrigin = "";
  let handshakeTimer = 0;
  let handshakeSeen = false;
  let frameLoaded = false;
  let inboxPollTimer = 0;
  const reviewChromeNodes = {
    toggle: reviewHistoryToggle,
    history: reviewHistory,
    historyList: reviewHistoryList,
  };

  function setText(node, value, kind) {
    node.textContent = value;
    if (kind) {
      node.setAttribute("data-kind", kind);
    } else {
      node.removeAttribute("data-kind");
    }
  }

  runtimeStaleHandler = function handleRuntimeStale() {
    setText(shellStatus, RELOAD_RECOVERY, "error");
    chromeAction.disabled = true;
    settingsConnect.disabled = true;
    reviewHistoryToggle.disabled = true;
    setReviewHistoryExpanded(reviewHistoryToggle, reviewHistory, false);
    reviewHistoryList.querySelectorAll("button").forEach((button) => {
      button.disabled = true;
    });
  };

  function syncChromeAction() {
    const connected = Boolean(storedOrigin);
    chromeAction.textContent = connected ? "Disconnect" : "Connect";
    chromeAction.setAttribute("aria-label", connected ? "Disconnect FrameNest" : "Connect FrameNest");
  }

  function request(type, payload) {
    return new Promise((resolve, reject) => {
      if (runtimeStale) {
        resolve(staleRuntimeResult());
        return;
      }
      const runtime = runtimeObject();
      if (guardInvalidatedRuntime(runtime)) {
        resolve(staleRuntimeResult());
        return;
      }
      try {
        runtime.sendMessage(
          { v: companion.PROTOCOL, type, payload: payload || {} },
          (response) => {
            let lastError;
            try {
              lastError = runtime.lastError;
            } catch (error) {
              if (guardInvalidatedRuntime(runtime, error)) {
                resolve(staleRuntimeResult());
                return;
              }
              reject(error);
              return;
            }
            if (lastError) {
              if (guardInvalidatedRuntime(runtime, lastError)) {
                resolve(staleRuntimeResult());
                return;
              }
              resolve({ ok: false, error: "extension_unavailable" });
              return;
            }
            resolve(response || { ok: false, error: "empty_response" });
          }
        );
      } catch (error) {
        if (guardInvalidatedRuntime(runtime, error)) {
          resolve(staleRuntimeResult());
          return;
        }
        reject(error);
      }
    });
  }

  function stopInboxPoll() {
    if (inboxPollTimer) {
      clearInterval(inboxPollTimer);
      inboxPollTimer = 0;
    }
  }

  function startInboxPoll() {
    stopInboxPoll();
    void refreshInbox();
    inboxPollTimer = setInterval(() => {
      if (globalThis.document && document.hidden) {
        return;
      }
      void refreshInbox();
    }, REVIEW.pollMs);
  }

  function hideInboxSection() {
    hideReviewCollections(reviewChromeNodes, true);
  }

  function applyInboxResult(result) {
    if (!result || result.ok !== true || result.forbidden === true || result.status === 403) {
      hideInboxSection();
      return;
    }
    const rendered = renderReviewCollections(reviewChromeNodes, result.items);
    setReviewHistoryExpanded(
      reviewHistoryToggle,
      reviewHistory,
      rendered.historyItems.length > 0 &&
        reviewHistoryToggle.getAttribute("aria-expanded") === "true"
    );
  }

  async function refreshInbox() {
    if (!storedOrigin) {
      hideInboxSection();
      return;
    }
    const result = await request(companion.TYPES.REVIEW_INBOX, {});
    applyInboxResult(result);
  }

  function onHistoryToggle() {
    setReviewHistoryExpanded(
      reviewHistoryToggle,
      reviewHistory,
      reviewHistoryToggle.getAttribute("aria-expanded") !== "true"
    );
  }

  function clearHandshakeWait() {
    if (handshakeTimer) {
      clearTimeout(handshakeTimer);
      handshakeTimer = 0;
    }
  }

  function clearFrame() {
    clearHandshakeWait();
    handshakeSeen = false;
    frameLoaded = false;
    frame.removeAttribute("src");
    frame.hidden = true;
  }

  function showFramingError() {
    setText(shellStatus, framingFailureCopy(), "error");
  }

  function showHandshakeTimeout() {
    const loaded = frameLoaded;
    setText(shellStatus, handshakeTimeoutCopy(loaded), loaded ? "notice" : "error");
  }

  function openSettings() {
    if (!settingsDialog.open) {
      if (typeof settingsDialog.show === "function") {
        settingsDialog.show();
      } else {
        settingsDialog.setAttribute("open", "");
      }
      settingsOpen.setAttribute("aria-expanded", "true");
    }
    originInput.focus();
  }

  function promptConnectInSettings() {
    setText(shellStatus, "Connect FrameNest in Settings");
    openSettings();
  }

  function closeSettings() {
    settingsOpen.setAttribute("aria-expanded", "false");
    if (typeof settingsDialog.close === "function" && settingsDialog.open) {
      settingsDialog.close();
      return;
    }
    settingsDialog.removeAttribute("open");
  }

  function hostFrame(origin) {
    if (!companion.acceptFrameNestOrigin(origin)) {
      clearFrame();
      return;
    }
    handshakeSeen = false;
    frameLoaded = false;
    clearHandshakeWait();
    frame.hidden = false;
    frame.src = origin;
    handshakeTimer = setTimeout(() => {
      if (!handshakeSeen) {
        showHandshakeTimeout();
      }
    }, HANDSHAKE_WAIT_MS);
  }

  function postToFrame(message, origin) {
    if (!frame.contentWindow || !companion.acceptFrameNestOrigin(origin)) {
      return;
    }
    frame.contentWindow.postMessage(message, origin);
  }

  async function connect() {
    const origin = originInput.value.trim();
    if (!origin) {
      setText(shellStatus, "Enter a FrameNest origin in Settings", "error");
      openSettings();
      return;
    }
    const result = await request(companion.TYPES.CONFIGURE_ORIGIN, { origin });
    if (runtimeStale || (result && result.stale === true)) {
      return;
    }
    if (!result.ok) {
      setText(shellStatus, result.error || "Failed", "error");
      return;
    }
    storedOrigin = result.origin || origin;
    originInput.value = storedOrigin;
    syncChromeAction();
    closeSettings();
    setText(shellStatus, "");
    hostFrame(storedOrigin);
    startInboxPoll();
  }

  async function reset() {
    stopInboxPoll();
    hideInboxSection();
    const result = await request(companion.TYPES.RESET, {});
    if (runtimeStale || (result && result.stale === true)) {
      return;
    }
    storedOrigin = "";
    originInput.value = "";
    syncChromeAction();
    clearFrame();
    setText(shellStatus, "Cleared");
    openSettings();
  }

  function onChromeAction() {
    if (storedOrigin) {
      void reset();
      return;
    }
    if (!originInput.value.trim()) {
      promptConnectInSettings();
      return;
    }
    void connect();
  }

  function onFrameLoad() {
    if (!frame.getAttribute("src")) {
      return;
    }
    frameLoaded = true;
  }

  function onFrameError() {
    clearHandshakeWait();
    showFramingError();
  }

  async function handleAttachRequest(event, ids) {
    const result = await request(companion.TYPES.ATTACH_BEGIN, {
      mediaId: ids.mediaId,
      locationId: ids.locationId,
      filename: "framenest-media.bin",
    });
    if (runtimeStale || (result && result.stale === true)) {
      return;
    }
    const ok = Boolean(result && result.ok);
    const error = (result && result.error) || "attach_failed";
    postToFrame(
      {
        v: WEB_PROTOCOL,
        type: WEB_TYPES.ATTACH_RESULT,
        payload: ok ? { ok: true } : { ok: false, error: error },
      },
      event.origin
    );
    if (!ok && error === "composer_unbound") {
      setText(shellStatus, "Composer is not bound", "error");
    } else if (ok) {
      setText(shellStatus, "Attached");
    } else {
      setText(shellStatus, error, "error");
    }
  }

  function mediaIdFromReviewEvent(event, listNode) {
    let node = event && event.target;
    while (node && node !== listNode) {
      const mediaId =
        (node.dataset && node.dataset.mediaId) ||
        (typeof node.getAttribute === "function" ? node.getAttribute("data-media-id") : "");
      if (companion.isUuid(mediaId)) {
        return mediaId;
      }
      node = node.parentNode;
    }
    return "";
  }

  function onReviewListClick(event, listNode) {
    const mediaId = mediaIdFromReviewEvent(event, listNode);
    if (!mediaId) {
      return;
    }
    openReviewOverlay(mediaId, reviewDialog, reviewFrame);
  }

  function onReviewOverlayMessage(event) {
    const message = companion.acceptReviewOverlayMessage(
      event,
      reviewFrame.contentWindow,
      extensionOrigin()
    );
    if (!message) {
      return false;
    }
    if (message.type === companion.REVIEW_OVERLAY.types.FORBIDDEN) {
      closeReviewOverlay(reviewDialog, reviewFrame);
      hideInboxSection();
      return true;
    }
    if (message.type === companion.REVIEW_OVERLAY.types.CLOSE) {
      closeReviewOverlay(reviewDialog, reviewFrame);
      return true;
    }
    if (message.type === companion.REVIEW_OVERLAY.types.INBOX_REFRESH) {
      void refreshInbox();
      return true;
    }
    return true;
  }

  function onWindowMessage(event) {
    if (onReviewOverlayMessage(event)) {
      return;
    }
    const data = acceptIncomingWebMessage(event, frame.contentWindow, storedOrigin);
    if (!data) {
      return;
    }
    if (data.type === WEB_TYPES.WEB_READY) {
      handshakeSeen = true;
      clearHandshakeWait();
      postToFrame({ v: WEB_PROTOCOL, type: WEB_TYPES.HOST_HELLO }, event.origin);
      setText(shellStatus, "");
      return;
    }
    if (data.type === WEB_TYPES.HOST_ACK) {
      handshakeSeen = true;
      clearHandshakeWait();
      return;
    }
    if (data.type === WEB_TYPES.ATTACH_REQUEST) {
      const ids = attachIdsFromWebRequest(data);
      if (!ids) {
        postToFrame(
          {
            v: WEB_PROTOCOL,
            type: WEB_TYPES.ATTACH_RESULT,
            payload: { ok: false, error: "invalid_attach" },
          },
          event.origin
        );
        return;
      }
      void handleAttachRequest(event, ids);
    }
  }

  chromeAction.addEventListener("click", onChromeAction);
  reviewHistoryToggle.addEventListener("click", onHistoryToggle);
  reviewHistoryList.addEventListener("click", (event) => {
    onReviewListClick(event, reviewHistoryList);
  });
  document.addEventListener("visibilitychange", () => {
    if (document.hidden) {
      stopInboxPoll();
      return;
    }
    if (storedOrigin) {
      startInboxPoll();
    }
  });
  settingsConnect.addEventListener("click", () => {
    void connect();
  });
  settingsOpen.addEventListener("click", openSettings);
  settingsClose.addEventListener("click", closeSettings);
  settingsDialog.addEventListener("click", (event) => {
    if (event.target === settingsDialog) {
      closeSettings();
    }
  });
  settingsDialog.addEventListener("close", () => {
    settingsOpen.setAttribute("aria-expanded", "false");
  });
  window.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && reviewDialog.open) {
      closeReviewOverlay(reviewDialog, reviewFrame);
    }
    if (event.key === "Escape" && settingsDialog.open) {
      closeSettings();
    }
  });
  reviewDialog.addEventListener("close", () => {
    reviewFrame.removeAttribute("src");
  });
  frame.addEventListener("load", onFrameLoad);
  frame.addEventListener("error", onFrameError);
  window.addEventListener("message", onWindowMessage);
  chrome.storage.local.get(
    ["frameNestOrigin"],
    (stored) => {
      const origin = stored.frameNestOrigin || "";
      if (companion.acceptFrameNestOrigin(origin)) {
        storedOrigin = origin;
        originInput.value = origin;
        syncChromeAction();
        setText(shellStatus, "");
        hostFrame(origin);
        startInboxPoll();
        return;
      }
      storedOrigin = "";
      originInput.value = "";
      syncChromeAction();
      hideInboxSection();
      clearFrame();
      setText(shellStatus, "Connect FrameNest in Settings");
    }
  );
})();
