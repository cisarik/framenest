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

  function reviewInboxVisualCollapsed(explicitCollapsed, itemCount) {
    if (itemCount <= 0) {
      return true;
    }
    return explicitCollapsed === true;
  }

  function reviewInboxNewestRunId(items) {
    if (!Array.isArray(items) || !items.length) {
      return "";
    }
    const first = items[0];
    return first && companion.isUuid(first.analysis_run_id) ? first.analysis_run_id : "";
  }

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

  function reviewOverlayUrl(mediaId) {
    if (!companion.isUuid(mediaId)) {
      return "";
    }
    if (!chrome.runtime || typeof chrome.runtime.getURL !== "function") {
      return "ui/review.html#media=" + mediaId;
    }
    return chrome.runtime.getURL("ui/review.html") + "#media=" + mediaId;
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
    if (chrome.runtime && typeof chrome.runtime.getURL === "function") {
      try {
        return new URL(chrome.runtime.getURL("ui/review.html")).origin;
      } catch {
        const raw = chrome.runtime.getURL("ui/review.html");
        if (typeof raw === "string" && raw.indexOf("chrome-extension://") === 0) {
          return raw.split("/").slice(0, 3).join("/");
        }
      }
    }
    return "";
  }

  globalThis.FrameNestReviewInbox = {
    EMPTY_COPY: REVIEW.emptyCopy,
    HINT_COPY: REVIEW.hintCopy,
    POLL_MS: REVIEW.pollMs,
    visualCollapsed: reviewInboxVisualCollapsed,
    newestRunId: reviewInboxNewestRunId,
    renderList: renderReviewInboxList,
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
  const reviewInbox = document.getElementById("review-inbox");
  const reviewInboxToggle = document.getElementById("review-inbox-toggle");
  const reviewInboxHint = document.getElementById("review-inbox-hint");
  const reviewInboxEmpty = document.getElementById("review-inbox-empty");
  const reviewInboxList = document.getElementById("review-inbox-list");
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
    !reviewInbox ||
    !reviewInboxToggle ||
    !reviewInboxHint ||
    !reviewInboxEmpty ||
    !reviewInboxList ||
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
  let explicitCollapsed = false;
  let seenRunId = "";

  function setText(node, value, kind) {
    node.textContent = value;
    if (kind) {
      node.setAttribute("data-kind", kind);
    } else {
      node.removeAttribute("data-kind");
    }
  }

  function syncChromeAction() {
    const connected = Boolean(storedOrigin);
    chromeAction.textContent = connected ? "Disconnect" : "Connect";
    chromeAction.setAttribute("aria-label", connected ? "Disconnect FrameNest" : "Connect FrameNest");
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

  function persistInboxPrefs() {
    const update = {};
    update[REVIEW.explicitCollapsedKey] = explicitCollapsed === true;
    if (companion.isUuid(seenRunId)) {
      update[REVIEW.seenRunIdKey] = seenRunId;
    }
    chrome.storage.local.set(update);
  }

  function hideInboxSection() {
    reviewInbox.hidden = true;
    reviewInbox.classList.add("is-collapsed");
    reviewInboxToggle.setAttribute("aria-expanded", "false");
    reviewInboxHint.hidden = true;
    reviewInboxHint.textContent = "";
    renderReviewInboxList(reviewInboxList, []);
  }

  function applyInboxCollapse(collapsed) {
    if (collapsed) {
      reviewInbox.classList.add("is-collapsed");
      reviewInboxToggle.setAttribute("aria-expanded", "false");
    } else {
      reviewInbox.classList.remove("is-collapsed");
      reviewInboxToggle.setAttribute("aria-expanded", "true");
    }
  }

  function renderInboxHint(awaiting) {
    const live = companion.normalizeAwaitingRecords(awaiting, Date.now());
    if (!live.length) {
      reviewInboxHint.hidden = true;
      reviewInboxHint.textContent = "";
      return;
    }
    reviewInboxHint.hidden = false;
    reviewInboxHint.textContent = REVIEW.hintCopy;
  }

  function applyInboxResult(result) {
    if (!result || result.forbidden === true || result.status === 403) {
      hideInboxSection();
      return;
    }
    if (result.ok !== true) {
      return;
    }
    const items = companion.sanitizeReviewInboxItems(result.items);
    const newest = reviewInboxNewestRunId(items);
    if (newest && newest !== seenRunId && explicitCollapsed !== true) {
      explicitCollapsed = false;
    }
    if (newest) {
      seenRunId = newest;
      persistInboxPrefs();
    }
    reviewInbox.hidden = false;
    const collapsed = reviewInboxVisualCollapsed(explicitCollapsed, items.length);
    applyInboxCollapse(collapsed);
    reviewInboxEmpty.hidden = items.length > 0;
    reviewInboxList.hidden = items.length === 0;
    renderReviewInboxList(reviewInboxList, items);
    renderInboxHint(result.awaiting);
  }

  async function refreshInbox() {
    if (!storedOrigin) {
      hideInboxSection();
      return;
    }
    const result = await request(companion.TYPES.REVIEW_INBOX, {});
    applyInboxResult(result);
  }

  function onInboxToggle() {
    const collapsed = reviewInbox.classList.contains("is-collapsed");
    if (collapsed) {
      explicitCollapsed = false;
      applyInboxCollapse(false);
    } else {
      explicitCollapsed = true;
      applyInboxCollapse(true);
    }
    persistInboxPrefs();
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
    if (!result.ok) {
      setText(shellStatus, result.error || "Failed", "error");
      return;
    }
    storedOrigin = result.origin || origin;
    originInput.value = storedOrigin;
    syncChromeAction();
    closeSettings();
    setText(shellStatus, "Connected");
    hostFrame(storedOrigin);
    startInboxPoll();
  }

  async function reset() {
    stopInboxPoll();
    hideInboxSection();
    await request(companion.TYPES.RESET, {});
    storedOrigin = "";
    originInput.value = "";
    explicitCollapsed = false;
    seenRunId = "";
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

  function mediaIdFromInboxEvent(event) {
    let node = event && event.target;
    while (node && node !== reviewInboxList) {
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

  function onReviewInboxClick(event) {
    const mediaId = mediaIdFromInboxEvent(event);
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
      setText(shellStatus, "Connected");
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
  reviewInboxToggle.addEventListener("click", onInboxToggle);
  reviewInboxList.addEventListener("click", onReviewInboxClick);
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
    ["frameNestOrigin", REVIEW.explicitCollapsedKey, REVIEW.seenRunIdKey],
    (stored) => {
      explicitCollapsed = stored[REVIEW.explicitCollapsedKey] === true;
      const storedSeen = stored[REVIEW.seenRunIdKey];
      seenRunId = companion.isUuid(storedSeen) ? storedSeen : "";
      const origin = stored.frameNestOrigin || "";
      if (companion.acceptFrameNestOrigin(origin)) {
        storedOrigin = origin;
        originInput.value = origin;
        syncChromeAction();
        setText(shellStatus, "Connected");
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
