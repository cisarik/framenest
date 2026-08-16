/* global importScripts, chrome, FrameNestCompanion */
importScripts(chrome.runtime.getURL("shared/messages.js"));

const companion = self.FrameNestCompanion;
let boundTabId = null;
const STORAGE_KEYS = Object.freeze({
  origin: "frameNestOrigin",
  inflight: "inflightClaims",
  acknowledged: "adapterAcknowledged",
});

chrome.runtime.onInstalled.addListener(() => {
  if (chrome.sidePanel && chrome.sidePanel.setPanelBehavior) {
    chrome.sidePanel.setPanelBehavior({ openPanelOnActionClick: true }).catch(() => {});
  }
});

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  const parsed = companion.dropUnknown(message);
  if (!parsed) {
    return false;
  }
  if (sender && sender.tab && typeof sender.tab.id === "number") {
    boundTabId = sender.tab.id;
  }
  handle(parsed, sender)
    .then(sendResponse)
    .catch((error) => {
      sendResponse({ ok: false, error: "internal_error" });
      void error;
    });
  return true;
});

chrome.runtime.onConnect.addListener((port) => {
  if (!port || port.name !== "framenest-attach") {
    return;
  }
  port.onMessage.addListener((message) => {
    const parsed = companion.dropUnknown(message);
    if (!parsed || parsed.type !== companion.TYPES.ATTACH_BEGIN) {
      return;
    }
    transferAttach(port, parsed.payload || {}).catch(() => {
      try {
        port.postMessage({
          v: companion.PROTOCOL,
          type: companion.TYPES.ERROR,
          payload: { error: "attach_failed" },
        });
      } catch {
        /* worker may already be closing */
      }
    });
  });
});

async function handle(message) {
  switch (message.type) {
    case companion.TYPES.CONFIGURE_ORIGIN:
      return configureOrigin(message.payload || {});
    case companion.TYPES.RESET:
      return resetState();
    case companion.TYPES.IDENTITY:
      return fetchJson("identity");
    case companion.TYPES.SAVE_POST:
      return savePost(message.payload || {});
    case companion.TYPES.POLL_CLAIM:
      return pollClaim(message.payload || {});
    case companion.TYPES.RECOVER_INFLIGHT:
      return recoverInflight();
    case companion.TYPES.PICKER_QUERY:
      return pickerQuery(message.payload || {});
    case companion.TYPES.ATTACH_BEGIN:
      return startAttach(message.payload || {});
    case companion.TYPES.ACK:
      if (message.payload && message.payload.openPicker) {
        await openPicker();
      }
      return { ok: true };
    default:
      return { ok: false, error: "unknown_type" };
  }
}

async function configureOrigin(payload) {
  const origin = payload.origin;
  if (!companion.acceptFrameNestOrigin(origin)) {
    return { ok: false, error: "invalid_origin" };
  }
  const granted = await chrome.permissions.request({ origins: [origin + "/*"] });
  if (!granted) {
    return { ok: false, error: "permission_denied" };
  }
  await chrome.storage.local.set({ [STORAGE_KEYS.origin]: origin });
  return { ok: true, origin };
}

async function resetState() {
  const stored = await chrome.storage.local.get(STORAGE_KEYS.origin);
  const origin = stored[STORAGE_KEYS.origin];
  if (origin) {
    try {
      await chrome.permissions.remove({ origins: [origin + "/*"] });
    } catch {
      /* optional */
    }
  }
  await chrome.storage.local.remove(Object.values(STORAGE_KEYS));
  return { ok: true };
}

async function savePost(payload) {
  const accepted = companion.acceptXPostUrl(payload.url);
  if (!accepted) {
    return { ok: false, error: "invalid_url" };
  }
  const response = await fetchJson("xRequests", {
    method: "POST",
    body: { url: accepted.submittedUrl },
  });
  if (!response.ok) {
    return response;
  }
  const claimId = response.body.request_id || response.body.claim_id;
  if (companion.isUuid(claimId)) {
    await persistInflight(claimId);
  }
  return {
    ok: true,
    claimId,
    state: response.body.state,
    failureCode: response.body.failure_code || null,
    terminal: isTerminal(response.body),
  };
}

async function pollClaim(payload) {
  if (!companion.isUuid(payload.claimId)) {
    return { ok: false, error: "invalid_claim" };
  }
  const response = await fetchJson("xRequest", {
    ids: { claimId: payload.claimId },
  });
  if (!response.ok) {
    return response;
  }
  const terminal = isTerminal(response.body);
  if (terminal) {
    await dropInflight(payload.claimId);
  }
  return {
    ok: true,
    claimId: payload.claimId,
    state: response.body.state,
    failureCode: response.body.failure_code || null,
    terminal,
  };
}

async function recoverInflight() {
  const stored = await chrome.storage.local.get(STORAGE_KEYS.inflight);
  const claimIds = Array.isArray(stored[STORAGE_KEYS.inflight])
    ? stored[STORAGE_KEYS.inflight].filter(companion.isUuid)
    : [];
  return { ok: true, claimIds };
}

async function pickerQuery(payload) {
  const params = new URLSearchParams();
  if (payload.q) {
    params.set("q", String(payload.q).slice(0, 240));
  }
  if (payload.kind) {
    params.set("kind", String(payload.kind));
  }
  if (payload.cursor) {
    params.set("cursor", String(payload.cursor));
  }
  if (Array.isArray(payload.tags)) {
    payload.tags.forEach((tag) => params.append("tag", String(tag)));
  }
  const suffix = params.toString() ? "?" + params.toString() : "";
  const response = await fetchJson("companionMedia", { suffix });
  if (!response.ok) {
    return response;
  }
  if (response.body.companion_api_version !== companion.API_VERSION) {
    return { ok: false, error: "version_skew", disable: true };
  }
  return { ok: true, page: response.body };
}

async function openPicker() {
  if (chrome.sidePanel && chrome.sidePanel.open) {
    try {
      await chrome.sidePanel.open({ windowId: chrome.windows.WINDOW_ID_CURRENT });
      return;
    } catch {
      /* popup fallback */
    }
  }
}

function isTerminal(body) {
  const state = body && body.state;
  return (
    state === "completed" ||
    state === "completed_partial" ||
    state === "failed" ||
    state === "duplicate_resolved" ||
    Boolean(body && body.failure_code === "X_NO_SUPPORTED_MEDIA")
  );
}

async function persistInflight(claimId) {
  const stored = await chrome.storage.local.get(STORAGE_KEYS.inflight);
  const current = Array.isArray(stored[STORAGE_KEYS.inflight])
    ? stored[STORAGE_KEYS.inflight]
    : [];
  if (!current.includes(claimId)) {
    current.push(claimId);
  }
  await chrome.storage.local.set({ [STORAGE_KEYS.inflight]: current.slice(-16) });
}

async function dropInflight(claimId) {
  const stored = await chrome.storage.local.get(STORAGE_KEYS.inflight);
  const current = Array.isArray(stored[STORAGE_KEYS.inflight])
    ? stored[STORAGE_KEYS.inflight].filter((id) => id !== claimId)
    : [];
  await chrome.storage.local.set({ [STORAGE_KEYS.inflight]: current });
}

async function configuredOrigin() {
  const stored = await chrome.storage.local.get(STORAGE_KEYS.origin);
  const origin = stored[STORAGE_KEYS.origin];
  if (!companion.acceptFrameNestOrigin(origin)) {
    return null;
  }
  return origin;
}

async function fetchJson(pathName, options) {
  const origin = await configuredOrigin();
  if (!origin) {
    return { ok: false, error: "not_configured" };
  }
  const path = companion.pathFor(pathName, options && options.ids);
  if (!path) {
    return { ok: false, error: "invalid_path" };
  }
  const method = (options && options.method) || "GET";
  const suffix = (options && options.suffix) || "";
  const headers = { "X-FrameNest-Request": "1" };
  const init = { method, headers };
  if (options && options.body) {
    headers["Content-Type"] = "application/json";
    init.body = JSON.stringify(options.body);
  }
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), companion.FETCH_TIMEOUT_MS);
  init.signal = controller.signal;
  try {
    const response = await fetch(origin + path + suffix, init);
    const body = await response.json().catch(() => ({}));
    if (!response.ok) {
      const code = body && body.error && body.error.code;
      return { ok: false, error: code || "http_" + response.status, status: response.status };
    }
    return { ok: true, body };
  } catch {
    return { ok: false, error: "network_failed" };
  } finally {
    clearTimeout(timer);
  }
}

async function startAttach(payload) {
  if (boundTabId == null) {
    return { ok: false, error: "composer_unbound" };
  }
  const port = chrome.tabs.connect(boundTabId, { name: "framenest-attach" });
  await transferAttach(port, payload);
  return { ok: true };
}

async function transferAttach(port, payload) {
  const origin = await configuredOrigin();
  const path = companion.pathFor("content", {
    mediaId: payload.mediaId,
    locationId: payload.locationId,
  });
  if (!origin || !path) {
    port.postMessage({
      v: companion.PROTOCOL,
      type: companion.TYPES.ERROR,
      payload: { error: "invalid_attach" },
    });
    return;
  }
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), companion.FETCH_TIMEOUT_MS);
  try {
    const response = await fetch(origin + path, {
      method: "GET",
      headers: { "X-FrameNest-Request": "1" },
      signal: controller.signal,
    });
    const lengthHeader = response.headers.get("content-length");
    const length = lengthHeader ? Number(lengthHeader) : NaN;
    if (!response.ok || !Number.isFinite(length) || length <= 0 || length > companion.MAX_ATTACH_BYTES) {
      if (length > companion.MAX_ATTACH_BYTES) {
        await fallbackDownload(origin + path, payload.filename);
      }
      port.postMessage({
        v: companion.PROTOCOL,
        type: companion.TYPES.ERROR,
        payload: { error: "too_large_or_invalid" },
      });
      return;
    }
    port.postMessage({
      v: companion.PROTOCOL,
      type: companion.TYPES.ATTACH_BEGIN,
      payload: {
        phase: "meta",
        mediaType: response.headers.get("content-type") || payload.mediaType,
        filename: payload.filename || "framenest-media.bin",
      },
    });
    const reader = response.body.getReader();
    let seen = 0;
    while (true) {
      const { done, value } = await reader.read();
      if (done) {
        break;
      }
      seen += value.byteLength;
      if (seen > companion.MAX_ATTACH_BYTES) {
        reader.cancel();
        port.postMessage({
          v: companion.PROTOCOL,
          type: companion.TYPES.ERROR,
          payload: { error: "too_large" },
        });
        return;
      }
      let offset = 0;
      while (offset < value.byteLength) {
        const slice = value.subarray(offset, offset + companion.CHUNK_BYTES);
        offset += slice.byteLength;
        let binary = "";
        for (let i = 0; i < slice.byteLength; i += 1) {
          binary += String.fromCharCode(slice[i]);
        }
        port.postMessage({
          v: companion.PROTOCOL,
          type: companion.TYPES.ATTACH_BEGIN,
          payload: { chunk: btoa(binary) },
        });
      }
    }
    port.postMessage({
      v: companion.PROTOCOL,
      type: companion.TYPES.ATTACH_BEGIN,
      payload: { phase: "end" },
    });
  } finally {
    clearTimeout(timer);
  }
}

async function fallbackDownload(url, filename) {
  const optional = await chrome.permissions.contains({ permissions: ["downloads"] });
  if (!optional) {
    const granted = await chrome.permissions.request({ permissions: ["downloads"] });
    if (!granted) {
      return;
    }
  }
  await chrome.downloads.download({ url, filename: filename || "framenest-media.bin", saveAs: true });
}
