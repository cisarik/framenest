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

  globalThis.FrameNestSidebarBridge = {
    WEB_PROTOCOL,
    WEB_TYPES,
    acceptIncomingWebMessage,
    attachIdsFromWebRequest,
  };

  const originInput = document.getElementById("origin");
  const shellStatus = document.getElementById("shell-status");
  const frame = document.getElementById("frame");
  if (!originInput || !shellStatus || !frame) {
    return;
  }

  let storedOrigin = "";
  let handshakeTimer = 0;
  let handshakeSeen = false;

  function setText(node, value, kind) {
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

  function clearHandshakeWait() {
    if (handshakeTimer) {
      clearTimeout(handshakeTimer);
      handshakeTimer = 0;
    }
  }

  function clearFrame() {
    clearHandshakeWait();
    handshakeSeen = false;
    frame.removeAttribute("src");
    frame.hidden = true;
  }

  function showFramingError() {
    setText(shellStatus, "FrameNest could not be framed in this panel.", "error");
  }

  function hostFrame(origin) {
    if (!companion.acceptFrameNestOrigin(origin)) {
      clearFrame();
      return;
    }
    handshakeSeen = false;
    clearHandshakeWait();
    frame.hidden = false;
    frame.src = origin;
    handshakeTimer = setTimeout(() => {
      if (!handshakeSeen) {
        showFramingError();
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
    const result = await request(companion.TYPES.CONFIGURE_ORIGIN, { origin });
    if (!result.ok) {
      setText(shellStatus, result.error || "Failed", "error");
      return;
    }
    storedOrigin = result.origin || origin;
    originInput.value = storedOrigin;
    setText(shellStatus, "Connected");
    hostFrame(storedOrigin);
  }

  async function reset() {
    await request(companion.TYPES.RESET, {});
    storedOrigin = "";
    originInput.value = "";
    clearFrame();
    setText(shellStatus, "Cleared");
  }

  function onFrameError() {
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

  function onWindowMessage(event) {
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

  document.getElementById("save-origin").addEventListener("click", connect);
  document.getElementById("reset").addEventListener("click", reset);
  frame.addEventListener("error", onFrameError);
  window.addEventListener("message", onWindowMessage);
  chrome.storage.local.get("frameNestOrigin", (stored) => {
    const origin = stored.frameNestOrigin || "";
    if (companion.acceptFrameNestOrigin(origin)) {
      storedOrigin = origin;
      originInput.value = origin;
      setText(shellStatus, "Connected");
      hostFrame(origin);
      return;
    }
    clearFrame();
    setText(shellStatus, "Connect FrameNest to open the library");
  });
})();
