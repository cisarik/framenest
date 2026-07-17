const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");

const APP_PATH = path.resolve(__dirname, "../src/framenest/adapters/api/web/app.js");
const INDEX_PATH = path.resolve(__dirname, "../src/framenest/adapters/api/web/index.html");
const APP_SOURCE = fs.readFileSync(APP_PATH, "utf8");
const INDEX_SOURCE = fs.readFileSync(INDEX_PATH, "utf8");
const RECOVERY_KEY = "framenest.upload.recovery.v1";

const UPLOAD_A = "11111111-1111-4111-8111-111111111111";
const UPLOAD_B = "22222222-2222-4222-8222-222222222222";
const UPLOAD_C = "33333333-3333-4333-8333-333333333333";
const MEDIA_A = 101;
const MEDIA_B = 202;
const LOCATION_A = 1001;
const LOCATION_B = 2002;

function deferred() {
  let resolve;
  let reject;
  const promise = new Promise((promiseResolve, promiseReject) => {
    resolve = promiseResolve;
    reject = promiseReject;
  });
  return { promise, resolve, reject };
}

function flushPromises() {
  return new Promise((resolve) => {
    setImmediate(resolve);
  });
}

async function flushAll() {
  await flushPromises();
  await flushPromises();
  await flushPromises();
}

function response(payload, status = 200) {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: async () => payload,
  };
}

function snapshot(
  id,
  state,
  receivedSizeBytes,
  declaredSizeBytes = 8,
  displayFilename = "sample.gif",
) {
  return {
    id,
    state,
    display_filename: displayFilename,
    declared_size_bytes: declaredSizeBytes,
    received_size_bytes: receivedSizeBytes,
    expires_at: 999999,
    failure_code: null,
  };
}

function makeFile(name = "sample.gif", size = 8, lastModified = 1234) {
  return {
    name,
    size,
    lastModified,
    slice(start, end) {
      return {
        name,
        start,
        end,
        size: end - start,
      };
    },
  };
}

function requestMethod(options) {
  return options && options.method ? String(options.method).toUpperCase() : "GET";
}

function createFetchController() {
  const calls = [];
  const queued = [];

  function enqueue(match, result) {
    queued.push({ match, result });
  }

  async function fetch(url, options = {}) {
    const call = {
      url: String(url),
      method: requestMethod(options),
      options,
    };
    calls.push(call);
    const index = queued.findIndex((entry) => entry.match(call));
    if (index !== -1) {
      const [entry] = queued.splice(index, 1);
      const result = typeof entry.result === "function" ? entry.result(call) : entry.result;
      return result && typeof result.then === "function" ? result : Promise.resolve(result);
    }
    return defaultFetchResponse(call);
  }

  function defaultFetchResponse(call) {
    if (call.url === "/health") return response({ status: "ok" });
    if (call.url === "/api/ai/media-suggestion-capability") {
      return response({ available: false, status: "not_configured" });
    }
    if (call.url === "/api/status/cloud") {
      return response({ server: "connected", connection: "loopback" });
    }
    if (call.url === "/api/uploads/capability") {
      return response({
        uploads_enabled: true,
        max_total_size_bytes: 1024,
        max_chunk_size_bytes: 4,
        session_ttl_seconds: 60,
      });
    }
    if (call.url === "/api/canonical-tags") return response({ tags: [] });
    if (call.url.startsWith("/api/media?")) {
      return response({ items: [], total: 0, offset: 0, limit: 30, q: "" });
    }
    if (call.url === "/api/libraries") return response({ libraries: [] });
    return response({ error: { code: "UPLOAD_SESSION_NOT_FOUND" } }, 404);
  }

  return {
    calls,
    fetch,
    enqueue,
    clearCalls() {
      calls.length = 0;
    },
    matching(method, url) {
      return calls.filter((call) => call.method === method && call.url === url);
    },
    matchingPrefix(method, prefix) {
      return calls.filter((call) => call.method === method && call.url.startsWith(prefix));
    },
  };
}

function createClassList() {
  const values = new Set();
  return {
    add(...names) {
      names.forEach((name) => values.add(name));
    },
    remove(...names) {
      names.forEach((name) => values.delete(name));
    },
    toggle(name, force) {
      if (force === undefined ? !values.has(name) : force) {
        values.add(name);
        return true;
      }
      values.delete(name);
      return false;
    },
    contains(name) {
      return values.has(name);
    },
  };
}

function canReceiveProgrammaticFocus(element) {
  if (element.hidden || element.disabled) return false;
  if (element.hasAttribute("tabindex")) return true;
  if (["BUTTON", "INPUT", "SELECT", "TEXTAREA"].includes(element.tagName)) return true;
  return element.tagName === "A" && element.hasAttribute("href");
}

function isInNormalTabSequence(element) {
  if (!canReceiveProgrammaticFocus(element)) return false;
  const tabindex = element.getAttribute("tabindex");
  return tabindex === null || Number(tabindex) >= 0;
}

function createElement(document, tagName = "div") {
  const attributes = new Map();
  const listeners = new Map();
  const element = {
    tagName: String(tagName).toUpperCase(),
    children: [],
    parentNode: null,
    dataset: {},
    style: {},
    classList: createClassList(),
    hidden: false,
    disabled: false,
    textContent: "",
    value: "",
    checked: false,
    files: [],
    title: "",
    type: "",
    max: 100,
    href: "",
    src: "",
    focusCount: 0,
    addEventListener(type, listener) {
      if (!listeners.has(type)) listeners.set(type, []);
      listeners.get(type).push(listener);
    },
    removeEventListener(type, listener) {
      if (!listener) {
        listeners.delete(type);
        return;
      }
      const retained = (listeners.get(type) || []).filter((candidate) => candidate !== listener);
      if (retained.length > 0) listeners.set(type, retained);
      else listeners.delete(type);
    },
    dispatchEvent(event) {
      if (!event.target) event.target = this;
      let current = this;
      while (current) {
        event.currentTarget = current;
        const currentListeners = current.__listeners.get(event.type) || [];
        for (const listener of [...currentListeners]) {
          listener(event);
          if (event.immediatePropagationStopped) break;
        }
        if (event.propagationStopped || event.bubbles === false) break;
        current = current.parentNode;
      }
      event.currentTarget = null;
      return !event.defaultPrevented;
    },
    append(...nodes) {
      nodes.forEach((node) => {
        if (node && typeof node === "object") node.parentNode = this;
      });
      this.children.push(...nodes);
    },
    appendChild(node) {
      if (node && typeof node === "object") node.parentNode = this;
      this.children.push(node);
      return node;
    },
    replaceChildren(...nodes) {
      this.children.forEach((node) => {
        if (node && node.parentNode === this) node.parentNode = null;
      });
      nodes.forEach((node) => {
        if (node && typeof node === "object") node.parentNode = this;
      });
      this.children = [...nodes];
    },
    remove() {},
    focus() {
      if (!canReceiveProgrammaticFocus(this)) return;
      document.activeElement = this;
      this.focusCount += 1;
    },
    setAttribute(name, value) {
      const normalizedName = String(name).toLowerCase();
      attributes.set(normalizedName, String(value));
      if (normalizedName === "hidden") this.hidden = true;
      if (normalizedName === "disabled") this.disabled = true;
      if (normalizedName === "href") this.href = String(value);
      if (normalizedName === "type") this.type = String(value);
    },
    removeAttribute(name) {
      const normalizedName = String(name).toLowerCase();
      attributes.delete(normalizedName);
      if (normalizedName === "hidden") this.hidden = false;
      if (normalizedName === "disabled") this.disabled = false;
      if (normalizedName === "href") this.href = "";
    },
    hasAttribute(name) {
      return attributes.has(String(name).toLowerCase());
    },
    getAttribute(name) {
      const normalizedName = String(name).toLowerCase();
      return attributes.has(normalizedName) ? attributes.get(normalizedName) : null;
    },
    querySelector() {
      return createElement(document);
    },
    querySelectorAll() {
      return [];
    },
    closest() {
      return null;
    },
    cloneNode() {
      return createElement(document, tagName);
    },
    showModal() {
      attributes.set("open", "");
    },
    close() {
      attributes.delete("open");
    },
    __listeners: listeners,
  };
  return element;
}

function applySelectorDefaults(selector, element) {
  if (selector.startsWith("#")) {
    const id = selector.slice(1).replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    const markup = INDEX_SOURCE.match(new RegExp(`<([a-z][a-z0-9-]*)\\b([^>]*\\bid="${id}"[^>]*)>`, "i"));
    if (markup) {
      element.tagName = markup[1].toUpperCase();
      for (const attribute of markup[2].matchAll(/([a-z][a-z0-9:-]*)(?:="([^"]*)")?/gi)) {
        element.setAttribute(attribute[1], attribute[2] === undefined ? "" : attribute[2]);
      }
    }
  }
  if (selector === "#upload-cancel-button") {
    element.textContent = "Cancel";
  }
}

function createDocument() {
  const elements = new Map();
  const selectorParents = new Map([
    ["#confirmation-dialog-title", "#confirmation-dialog"],
    ["#confirmation-dialog-message", "#confirmation-dialog"],
    ["#confirmation-dismiss-button", "#confirmation-dialog"],
    ["#confirmation-confirm-button", "#confirmation-dialog"],
  ]);
  const document = {
    activeElement: null,
    querySelector(selector) {
      if (!elements.has(selector)) {
        const element = createElement(document);
        applySelectorDefaults(selector, element);
        elements.set(selector, element);
        const parentSelector = selectorParents.get(selector);
        if (parentSelector) {
          element.parentNode = document.querySelector(parentSelector);
        }
      }
      return elements.get(selector);
    },
    querySelectorAll() {
      return [];
    },
    createElement(tagName) {
      return createElement(document, tagName);
    },
    createElementNS(_namespace, tagName) {
      return createElement(document, tagName);
    },
    createTextNode(value) {
      return { textContent: String(value) };
    },
    createDocumentFragment() {
      return createElement(document, "fragment");
    },
  };
  document.activeElement = createElement(document);
  return document;
}

function createLocalStorage() {
  const values = new Map();
  return {
    getItem(key) {
      return values.has(key) ? values.get(key) : null;
    },
    setItem(key, value) {
      values.set(key, String(value));
    },
    removeItem(key) {
      values.delete(key);
    },
    clear() {
      values.clear();
    },
  };
}

async function createHarness() {
  const fetchController = createFetchController();
  const document = createDocument();
  const timers = [];
  const context = {
    console,
    document,
    fetch: fetchController.fetch,
    localStorage: createLocalStorage(),
    URL: {
      createObjectURL: () => "blob:framenest-test",
      revokeObjectURL: () => {},
    },
    Blob: global.Blob,
    Uint8Array: global.Uint8Array,
    Date: global.Date,
    JSON: global.JSON,
    Number: global.Number,
    String: global.String,
    Boolean: global.Boolean,
    Math: global.Math,
    Set: global.Set,
    Map: global.Map,
    RegExp: global.RegExp,
    Array: global.Array,
    Object: global.Object,
    Promise: global.Promise,
    encodeURIComponent,
    URLSearchParams,
    atob: global.atob || ((value) => Buffer.from(value, "base64").toString("binary")),
    setTimeout(callback, delay) {
      const timer = { callback, delay, active: true };
      timers.push(timer);
      return timer;
    },
    clearTimeout(timer) {
      if (timer) timer.active = false;
    },
    confirm() {
      throw new Error("native confirmation must not be invoked");
    },
    addEventListener() {},
    removeEventListener() {},
  };
  context.window = context;
  context.self = context;
  context.globalThis = context;
  vm.createContext(context);
  vm.runInContext(APP_SOURCE, context, { filename: APP_PATH });
  await flushAll();
  fetchController.clearCalls();
  return {
    context,
    document,
    fetchController,
    timers,
    run(code) {
      return vm.runInContext(code, context);
    },
    async flush() {
      await flushAll();
    },
    runNextTimer() {
      const timer = timers.find((candidate) => candidate.active);
      assert.ok(timer, "expected an active timer");
      timer.active = false;
      timer.callback();
      return timer.delay;
    },
  };
}

function stateOf(harness) {
  return harness.run(`({
    generation: uploadState.generation,
    uploadId: uploadState.uploadId,
    snapshotState: uploadState.snapshot ? uploadState.snapshot.state : null,
    received: uploadState.snapshot ? uploadState.snapshot.received_size_bytes : null,
    actionKind: uploadState.actionOwner ? uploadState.actionOwner.kind : null,
    preparing: uploadState.preparing,
    running: uploadState.running,
    paused: uploadState.paused,
    completing: uploadState.completing,
    hasLoopOwner: Boolean(uploadState.uploadLoopOwner),
    hasCompletionOwner: Boolean(uploadState.completionOwner),
    hasPollOwner: Boolean(uploadState.pollOwner),
    hasPollTimer: Boolean(uploadState.pollTimer),
    pollRetryDelayMs: uploadState.pollRetryDelayMs,
    message: uploadState.message,
    stateLabel: document.querySelector("#upload-state-label").textContent,
    visibleMessage: document.querySelector("#upload-message").textContent,
    byteCount: document.querySelector("#upload-byte-count").textContent,
    fileName: document.querySelector("#upload-file-name").textContent,
    startHidden: document.querySelector("#upload-start-button").hidden,
    pauseHidden: document.querySelector("#upload-pause-button").hidden,
    resumeHidden: document.querySelector("#upload-resume-button").hidden,
    cancelHidden: document.querySelector("#upload-cancel-button").hidden,
    startDisabled: document.querySelector("#upload-start-button").disabled,
    pauseDisabled: document.querySelector("#upload-pause-button").disabled,
    resumeDisabled: document.querySelector("#upload-resume-button").disabled,
    cancelDisabled: document.querySelector("#upload-cancel-button").disabled,
    focusedStatus: document.activeElement === document.querySelector("#upload-message"),
    cancelLabel: document.querySelector("#upload-cancel-button").textContent,
    recovery: window.localStorage.getItem("${RECOVERY_KEY}"),
  })`);
}

function confirmationStateOf(harness) {
  return JSON.parse(JSON.stringify(harness.run(`({
    open: document.querySelector("#confirmation-dialog").hasAttribute("open"),
    activeRequestId: activeConfirmationRequest ? activeConfirmationRequest.id : null,
    title: document.querySelector("#confirmation-dialog-title").textContent,
    message: document.querySelector("#confirmation-dialog-message").textContent,
    dismissLabel: document.querySelector("#confirmation-dismiss-button").textContent,
    confirmLabel: document.querySelector("#confirmation-confirm-button").textContent,
    destructive: document.querySelector("#confirmation-confirm-button").classList.contains("danger-button"),
    focusedDismiss: document.activeElement === document.querySelector("#confirmation-dismiss-button"),
    focusedConfirm: document.activeElement === document.querySelector("#confirmation-confirm-button"),
  })`)));
}

function makeCatalogItem(mediaId = MEDIA_A, locationId = LOCATION_A) {
  return {
    media_id: mediaId,
    display_title: `Media ${mediaId}`,
    media_kind: "video",
    collection_key: null,
    created_at_ms: 1,
    tags: [],
    locations: [{
      location_id: locationId,
      availability: "available",
      relative_path: `media-${mediaId}.mp4`,
    }],
  };
}

function makeMetadataPayload({
  mediaId = MEDIA_A,
  title = "Persisted title",
  description = "Persisted description",
  tagKeys = ["persisted"],
} = {}) {
  return {
    media_id: mediaId,
    display_title: title,
    description,
    tags: tagKeys.map((key) => ({ key, display_name: key })),
    collection_key: null,
    processed_at_ms: null,
  };
}

function setMetadataWorkspace(
  harness,
  {
    mediaId = MEDIA_A,
    locationId = LOCATION_A,
    baselineTitle = "Persisted title",
    currentTitle = "Unsaved title",
    baselineDescription = "Persisted description",
    currentDescription = "Unsaved description",
    baselineTags = ["persisted"],
    currentTags = ["persisted", "unsaved"],
    scope = "",
  } = {},
) {
  harness.context.__metadataItem = makeCatalogItem(mediaId, locationId);
  harness.context.__metadataFixture = {
    baselineTitle,
    currentTitle,
    baselineDescription,
    currentDescription,
    baselineTags,
    currentTags,
    scope,
  };
  harness.run(`
    catalogState.collection = __metadataFixture.scope;
    metadataWorkspace = {
      openMediaId: __metadataItem.media_id,
      openItem: __metadataItem,
      loading: false,
      saving: false,
      unavailable: false,
      notFound: false,
      statusOverride: null,
      analyzing: false,
      aiSuggestionApplied: false,
      suggestedFilename: "",
      baseline: {
        displayTitle: __metadataFixture.baselineTitle,
        description: __metadataFixture.baselineDescription,
        tagKeys: [...__metadataFixture.baselineTags],
        collectionKey: null,
        processedAtMs: null,
      },
      current: {
        displayTitle: __metadataFixture.currentTitle,
        description: __metadataFixture.currentDescription,
        tagKeys: [...__metadataFixture.currentTags],
        collectionKey: null,
        processedAtMs: null,
      },
    };
    advanceMetadataWorkspaceRevision();
    document.querySelector("#metadata-dialog").setAttribute("open", "");
    renderMetadataWorkspace();
  `);
  harness.fetchController.clearCalls();
}

function metadataStateOf(harness) {
  return JSON.parse(JSON.stringify(harness.run(`({
    mediaId: metadataWorkspace.openMediaId,
    openItemMediaId: metadataWorkspace.openItem ? metadataWorkspace.openItem.media_id : null,
    locationId: metadataAiLocation() ? metadataAiLocation().location_id : null,
    revision: metadataWorkspaceRevision,
    currentTitle: metadataWorkspace.current.displayTitle,
    currentDescription: metadataWorkspace.current.description,
    currentTags: [...metadataWorkspace.current.tagKeys],
    baselineTitle: metadataWorkspace.baseline.displayTitle,
    baselineDescription: metadataWorkspace.baseline.description,
    baselineTags: [...metadataWorkspace.baseline.tagKeys],
    suggestedFilename: metadataWorkspace.suggestedFilename,
    dirty: metadataWorkspace.openMediaId === null ? false : metadataIsDirty(),
    saving: metadataWorkspace.saving,
    analyzing: metadataWorkspace.analyzing,
    aiSuggestionApplied: metadataWorkspace.aiSuggestionApplied,
    metadataOpen: document.querySelector("#metadata-dialog").hasAttribute("open"),
    status: document.querySelector("#metadata-status").textContent,
    scope: catalogState.collection,
    saveRequestToken: metadataSaveRequestToken,
    saveOwnerToken: metadataSaveOwner ? metadataSaveOwner.token : null,
    saveOwnerMediaId: metadataSaveOwner ? metadataSaveOwner.mediaId : null,
    confirmationRequestId: activeConfirmationRequest ? activeConfirmationRequest.id : null,
    focusedClose: document.activeElement === document.querySelector("#metadata-close-button"),
    focusedAnalyze: document.activeElement === document.querySelector("#metadata-ai-analyze-button"),
  })`)));
}

function enableMetadataAi(harness) {
  harness.run(`renderAiCapability({
    available: true,
    provider_id: "test-provider",
    provider_display_name: "Test provider",
    model_id: "test-model",
    prompt_version: "test-prompt",
    execution: "server",
    status: "available",
    configured: true,
    credential_available: true,
    requires_explicit_confirmation: true,
  }); updateMetadataControls()`);
  harness.fetchController.clearCalls();
}

function metadataAiEndpoint(mediaId = MEDIA_A, locationId = LOCATION_A) {
  return `/api/media/${mediaId}/locations/${locationId}/ai-suggestion-preview`;
}

function metadataEndpoint(mediaId = MEDIA_A) {
  return `/api/media/${mediaId}/metadata`;
}

function dispatch(element, type, values = {}) {
  const event = {
    type,
    bubbles: true,
    defaultPrevented: false,
    propagationStopped: false,
    immediatePropagationStopped: false,
    preventDefault() {
      this.defaultPrevented = true;
    },
    stopPropagation() {
      this.propagationStopped = true;
    },
    stopImmediatePropagation() {
      this.immediatePropagationStopped = true;
      this.propagationStopped = true;
    },
    ...values,
  };
  element.dispatchEvent(event);
  return event;
}

function activateConfirmation(harness, action) {
  const selector = action === "confirm"
    ? "#confirmation-confirm-button"
    : "#confirmation-dismiss-button";
  return dispatch(harness.document.querySelector(selector), "click");
}

function dismissConfirmationWithEscape(harness) {
  return dispatch(harness.document.querySelector("#confirmation-dialog"), "cancel");
}

function setSelectedFile(harness, file = makeFile()) {
  harness.context.__file = file;
  harness.run("resetUploadForFile(__file)");
  harness.fetchController.clearCalls();
}

function setActiveUpload(
  harness,
  {
    id = UPLOAD_A,
    state = "receiving",
    received = 0,
    size = 8,
    file = makeFile("sample.gif", size),
  } = {},
) {
  harness.context.__file = file;
  harness.context.__snapshot = snapshot(id, state, received, size, file.name);
  harness.run(`
    resetUploadForFile(__file);
    uploadState.uploadId = __snapshot.id;
    uploadState.snapshot = __snapshot;
    uploadState.fileNameHint = __snapshot.display_filename;
    uploadState.expectedSizeBytes = __snapshot.declared_size_bytes;
    saveUploadRecovery(__snapshot);
    renderUploadCockpit();
  `);
  harness.fetchController.clearCalls();
}

function enqueue(harness, method, url, result) {
  harness.fetchController.enqueue(
    (call) => call.method === method && call.url === url,
    result,
  );
}

function enqueueStatus(harness, uploadId, result) {
  enqueue(harness, "GET", `/api/uploads/${encodeURIComponent(uploadId)}`, result);
}

function configureControlScenario(harness, scenario) {
  const file = scenario.hasFile === false ? null : makeFile("scenario.gif", 8);
  const currentSnapshot = scenario.snapshotState
    ? snapshot(
      UPLOAD_A,
      scenario.snapshotState,
      scenario.received === undefined ? 8 : scenario.received,
      8,
      "scenario.gif",
    )
    : null;
  harness.context.__controlScenario = {
    file,
    snapshot: currentSnapshot,
    actionKind: scenario.actionKind || null,
    preparing: Boolean(scenario.preparing),
    running: Boolean(scenario.running),
    paused: Boolean(scenario.paused),
    needsReselection: Boolean(scenario.needsReselection),
    completing: Boolean(scenario.completing),
  };
  harness.run(`
    resetUploadForFile(__controlScenario.file);
    uploadState.uploadId = __controlScenario.snapshot ? __controlScenario.snapshot.id : null;
    uploadState.snapshot = __controlScenario.snapshot;
    uploadState.fileNameHint = __controlScenario.snapshot ? __controlScenario.snapshot.display_filename : "";
    uploadState.expectedSizeBytes = __controlScenario.snapshot ? __controlScenario.snapshot.declared_size_bytes : 0;
    uploadState.preparing = __controlScenario.preparing;
    uploadState.running = __controlScenario.running;
    uploadState.paused = __controlScenario.paused;
    uploadState.needsReselection = __controlScenario.needsReselection;
    uploadState.completing = __controlScenario.completing;
    uploadState.actionOwner = __controlScenario.actionKind
      ? { ...currentUploadContext(), kind: __controlScenario.actionKind }
      : null;
    renderUploadCockpit();
  `);
}

function assertExactUploadActions(harness, scenarioName, expectedActions) {
  const state = stateOf(harness);
  const expected = new Set(expectedActions);
  for (const action of ["start", "pause", "resume", "cancel"]) {
    const available = expected.has(action);
    assert.equal(state[`${action}Hidden`], !available, `${scenarioName}: ${action} hidden`);
    assert.equal(state[`${action}Disabled`], !available, `${scenarioName}: ${action} disabled`);
  }
  assert.equal(
    expected.has("pause") && expected.has("resume"),
    false,
    `${scenarioName}: Pause and Resume must never be simultaneously available`,
  );
}

test("Production Upload cancellation contains no native browser confirmation", () => {
  assert.equal(APP_SOURCE.includes("window.confirm"), false);
  assert.equal(/(^|[^A-Za-z0-9_.])confirm\s*\(/m.test(APP_SOURCE), false);
});

test("Upload controls expose the exact action set for every accepted lifecycle state", async () => {
  const h = await createHarness();
  const scenarios = [
    { name: "No file", hasFile: false, stateLabel: "No file selected", actions: [] },
    { name: "Valid selected file", stateLabel: "Ready", actions: ["start"] },
    { name: "Preparing before session creation", preparing: true, actionKind: "start", stateLabel: "Preparing", actions: [] },
    { name: "Preparing after session creation", snapshotState: "created", received: 0, preparing: true, actionKind: "start", stateLabel: "Preparing", actions: ["cancel"] },
    { name: "Uploading", snapshotState: "receiving", received: 4, running: true, stateLabel: "Uploading", actions: ["pause", "cancel"] },
    { name: "Pausing", snapshotState: "receiving", received: 4, running: true, paused: true, stateLabel: "Pausing", actions: ["cancel"] },
    { name: "Paused", snapshotState: "receiving", received: 4, paused: true, stateLabel: "Paused", actions: ["resume", "cancel"] },
    { name: "Reselection required", hasFile: false, snapshotState: "receiving", received: 4, needsReselection: true, stateLabel: "Reselect file to resume", actions: ["cancel"] },
    { name: "Compatible file reselected", snapshotState: "receiving", received: 4, stateLabel: "Ready to resume", actions: ["resume", "cancel"] },
    { name: "Created session ready to resume", snapshotState: "created", received: 0, stateLabel: "Ready to resume", actions: ["resume", "cancel"] },
    { name: "Received", snapshotState: "received", stateLabel: "Validating", actions: ["cancel"] },
    { name: "Validating", snapshotState: "validating", stateLabel: "Validating", actions: [] },
    { name: "Duplicate pending", snapshotState: "duplicate_pending", stateLabel: "Validating", actions: ["cancel"] },
    { name: "Publish pending", snapshotState: "publish_pending", stateLabel: "Completed", actions: [] },
    { name: "Published", snapshotState: "published", stateLabel: "Completed", actions: [] },
    { name: "Cataloged", snapshotState: "cataloged", stateLabel: "Completed", actions: [] },
    { name: "Rejected", snapshotState: "rejected", stateLabel: "Failed", actions: [] },
    { name: "Failed", snapshotState: "failed", stateLabel: "Failed", actions: [] },
    { name: "Expired", snapshotState: "expired", stateLabel: "Failed", actions: [] },
    { name: "Cancelled", snapshotState: "cancelled", stateLabel: "Cancelled", actions: [] },
    { name: "Cancelling", snapshotState: "received", actionKind: "cancel", stateLabel: "Cancelling", actions: [] },
  ];

  for (const scenario of scenarios) {
    configureControlScenario(h, scenario);
    const state = stateOf(h);
    assert.equal(state.stateLabel, scenario.stateLabel, `${scenario.name}: visible state`);
    assertExactUploadActions(h, scenario.name, scenario.actions);
  }

  configureControlScenario(h, scenarios[0]);
  assert.equal(stateOf(h).fileName, "", "idle controls remain absent with no selected file");
});

test("A disappearing upload action moves focus to the live status", async () => {
  const h = await createHarness();
  setActiveUpload(h, { state: "receiving", received: 4 });
  h.run(`
    uploadState.running = true;
    renderUploadCockpit();
    document.querySelector("#upload-pause-button").focus();
    if (document.activeElement !== document.querySelector("#upload-pause-button")) {
      throw new Error("visible native Pause action should be focusable");
    }
    handlePauseUpload();
  `);

  const state = stateOf(h);
  assert.equal(state.pauseHidden, true);
  assert.equal(state.focusedStatus, true);
  assert.equal(state.stateLabel, "Pausing");
  assert.equal(h.run('document.querySelector("#upload-message").focusCount'), 1);
  h.run("renderUploadCockpit(); renderUploadCockpit()");
  assert.equal(h.run('document.querySelector("#upload-message").focusCount'), 1);
});

test("The centralized status is programmatically focusable but absent from the normal tab sequence", async () => {
  const h = await createHarness();
  assert.equal(h.run('document.querySelector("#upload-message").getAttribute("tabindex")'), "-1");
  assert.equal(isInNormalTabSequence(h.document.querySelector("#upload-message")), false);
  h.run('document.querySelector("#upload-message").focus()');
  assert.equal(stateOf(h).focusedStatus, true);
});

test("Polling preserves unrelated focus and never repeatedly focuses the upload status", async () => {
  const h = await createHarness();
  setActiveUpload(h, { state: "received", received: 8 });
  h.run(`
    document.querySelector("#upload-dialog").setAttribute("open", "");
    document.querySelector("#upload-close-button").focus();
    scheduleUploadPolling(currentUploadContext({ uploadId: uploadState.uploadId, file: uploadState.file }));
  `);
  assert.equal(
    h.run('document.activeElement === document.querySelector("#upload-close-button")'),
    true,
  );

  enqueueStatus(h, UPLOAD_A, response(snapshot(UPLOAD_A, "received", 8)));
  h.runNextTimer();
  await h.flush();
  enqueueStatus(h, UPLOAD_A, response(snapshot(UPLOAD_A, "validating", 8)));
  h.runNextTimer();
  await h.flush();

  assert.equal(
    h.run('document.activeElement === document.querySelector("#upload-close-button")'),
    true,
  );
  assert.equal(h.run('document.querySelector("#upload-message").focusCount'), 0);
});

test("Rendering without a disappearing focused action does not focus the upload status", async () => {
  const h = await createHarness();
  setActiveUpload(h, { state: "receiving", received: 4 });
  h.run(`
    uploadState.running = true;
    renderUploadCockpit();
    document.querySelector("#upload-cancel-button").focus();
    renderUploadCockpit();
  `);
  assert.equal(
    h.run('document.activeElement === document.querySelector("#upload-cancel-button")'),
    true,
  );
  assert.equal(h.run('document.querySelector("#upload-message").focusCount'), 0);
});

test("Reusable confirmation populates, settles once, resets, and restores focus", async () => {
  const h = await createHarness();
  const trigger = h.document.querySelector("#upload-cancel-button");
  trigger.hidden = false;
  trigger.disabled = false;
  trigger.focus();
  h.context.__confirmationSettlements = 0;
  const result = h.run(`requestConfirmation({
    title: "Remove item?",
    message: "This action cannot be undone.",
    dismissLabel: "Keep item",
    confirmLabel: "Remove item",
    destructive: true,
  }).then((accepted) => {
    __confirmationSettlements += 1;
    return accepted;
  })`);

  assert.deepEqual(confirmationStateOf(h), {
    open: true,
    activeRequestId: 1,
    title: "Remove item?",
    message: "This action cannot be undone.",
    dismissLabel: "Keep item",
    confirmLabel: "Remove item",
    destructive: true,
    focusedDismiss: true,
    focusedConfirm: false,
  });

  activateConfirmation(h, "dismiss");
  dismissConfirmationWithEscape(h);
  assert.equal(await result, false);
  await h.flush();
  assert.equal(h.context.__confirmationSettlements, 1);
  assert.deepEqual(confirmationStateOf(h), {
    open: false,
    activeRequestId: null,
    title: "",
    message: "",
    dismissLabel: "",
    confirmLabel: "",
    destructive: false,
    focusedDismiss: false,
    focusedConfirm: false,
  });
  assert.equal(h.document.activeElement, trigger);
});

test("Reusable confirmation rejects overlap and stale settlement cannot affect a later request", async () => {
  const h = await createHarness();
  const first = h.run(`requestConfirmation({
    title: "First request",
    message: "First message",
    dismissLabel: "Wait",
    confirmLabel: "Continue",
    destructive: true,
  })`);
  h.run("globalThis.__staleConfirmationRequest = activeConfirmationRequest");
  const overlapping = h.run(`requestConfirmation({
    title: "Overlapping request",
    message: "Must not replace the active request",
    dismissLabel: "No",
    confirmLabel: "Yes",
  })`);

  assert.equal(await overlapping, false);
  assert.equal(confirmationStateOf(h).title, "First request");
  assert.equal(confirmationStateOf(h).activeRequestId, 1);
  activateConfirmation(h, "confirm");
  assert.equal(await first, true);

  const later = h.run(`requestConfirmation({
    title: "Later request",
    message: "Later message",
    dismissLabel: "Stay",
    confirmLabel: "Proceed",
    destructive: false,
  })`);
  h.run("settleConfirmation(__staleConfirmationRequest, true)");
  assert.equal(confirmationStateOf(h).open, true);
  assert.equal(confirmationStateOf(h).title, "Later request");
  assert.equal(confirmationStateOf(h).destructive, false);
  const escapeEvent = dismissConfirmationWithEscape(h);
  assert.equal(escapeEvent.defaultPrevented, true);
  assert.equal(await later, false);
});

test("Confirmation traps action focus and Escape leaves the parent Upload modal open", async () => {
  const h = await createHarness();
  h.run('document.querySelector("#upload-dialog").setAttribute("open", "")');
  const result = h.run(`requestConfirmation({
    title: "Cancel upload?",
    message: "Uploaded progress will be discarded.",
    dismissLabel: "Keep upload",
    confirmLabel: "Cancel upload",
    destructive: true,
  })`);

  assert.equal(confirmationStateOf(h).focusedDismiss, true);
  const shiftTab = dispatch(h.document.querySelector("#confirmation-dialog"), "keydown", {
    key: "Tab",
    shiftKey: true,
  });
  assert.equal(shiftTab.defaultPrevented, true);
  assert.equal(confirmationStateOf(h).focusedConfirm, true);
  const tab = dispatch(h.document.querySelector("#confirmation-dialog"), "keydown", {
    key: "Tab",
    shiftKey: false,
  });
  assert.equal(tab.defaultPrevented, true);
  assert.equal(confirmationStateOf(h).focusedDismiss, true);

  dismissConfirmationWithEscape(h);
  assert.equal(await result, false);
  assert.equal(h.run('document.querySelector("#upload-dialog").hasAttribute("open")'), true);
});

test("Keep upload and Escape preserve upload ownership, offset, modal, and trigger focus", async () => {
  const h = await createHarness();
  setActiveUpload(h, { id: UPLOAD_A, state: "receiving", received: 4 });
  h.run(`
    document.querySelector("#upload-dialog").setAttribute("open", "");
    document.querySelector("#upload-cancel-button").focus();
  `);
  const initialGeneration = stateOf(h).generation;
  const keepUpload = h.run("handleCancelUpload()");

  assert.deepEqual(
    {
      title: confirmationStateOf(h).title,
      message: confirmationStateOf(h).message,
      dismissLabel: confirmationStateOf(h).dismissLabel,
      confirmLabel: confirmationStateOf(h).confirmLabel,
      destructive: confirmationStateOf(h).destructive,
    },
    {
      title: "Cancel upload?",
      message: "Uploaded progress will be discarded.",
      dismissLabel: "Keep upload",
      confirmLabel: "Cancel upload",
      destructive: true,
    },
  );
  assert.equal(stateOf(h).actionKind, null);
  assert.equal(stateOf(h).generation, initialGeneration);
  assert.equal(h.fetchController.matching("DELETE", `/api/uploads/${UPLOAD_A}`).length, 0);

  activateConfirmation(h, "dismiss");
  await keepUpload;
  assert.equal(stateOf(h).snapshotState, "receiving");
  assert.equal(stateOf(h).received, 4);
  assert.equal(stateOf(h).generation, initialGeneration);
  assert.equal(h.fetchController.matching("DELETE", `/api/uploads/${UPLOAD_A}`).length, 0);
  assert.equal(h.run('document.querySelector("#upload-dialog").hasAttribute("open")'), true);
  assert.equal(h.document.activeElement, h.document.querySelector("#upload-cancel-button"));

  const escape = h.run("handleCancelUpload()");
  dismissConfirmationWithEscape(h);
  await escape;
  assert.equal(stateOf(h).snapshotState, "receiving");
  assert.equal(stateOf(h).received, 4);
  assert.equal(stateOf(h).generation, initialGeneration);
  assert.equal(h.fetchController.matching("DELETE", `/api/uploads/${UPLOAD_A}`).length, 0);
  assert.equal(h.run('document.querySelector("#upload-dialog").hasAttribute("open")'), true);
  assert.equal(h.document.activeElement, h.document.querySelector("#upload-cancel-button"));
});

test("Upload cancellation revalidates eligibility after asynchronous confirmation", async () => {
  const h = await createHarness();
  setActiveUpload(h, { id: UPLOAD_A, state: "receiving", received: 4 });
  const cancellation = h.run("handleCancelUpload()");
  h.context.__validatingSnapshot = snapshot(UPLOAD_A, "validating", 8);
  h.run(`
    uploadState.snapshot = __validatingSnapshot;
    renderUploadCockpit();
  `);

  activateConfirmation(h, "confirm");
  await cancellation;
  await h.flush();

  assert.equal(stateOf(h).snapshotState, "validating");
  assert.equal(stateOf(h).received, 8);
  assert.equal(stateOf(h).actionKind, null);
  assert.equal(h.fetchController.matching("DELETE", `/api/uploads/${UPLOAD_A}`).length, 0);
});

test("Confirmation backdrop dismissal resolves false without closing the Upload modal", async () => {
  const h = await createHarness();
  h.run('document.querySelector("#upload-dialog").setAttribute("open", "")');
  const result = h.run(`requestConfirmation({
    title: "Leave upload?",
    message: "The upload will remain available.",
    dismissLabel: "Stay",
    confirmLabel: "Leave",
  })`);

  const dialog = h.document.querySelector("#confirmation-dialog");
  dispatch(dialog, "click", { target: dialog });
  assert.equal(await result, false);
  assert.equal(h.run('document.querySelector("#upload-dialog").hasAttribute("open")'), true);
});

test("Confirmation content click bubbles with a descendant target and does not dismiss", async () => {
  const h = await createHarness();
  h.run('document.querySelector("#upload-dialog").setAttribute("open", "")');
  const result = h.run(`requestConfirmation({
    title: "Leave upload?",
    message: "The upload will remain available.",
    dismissLabel: "Stay",
    confirmLabel: "Leave",
  })`);
  const dialog = h.document.querySelector("#confirmation-dialog");
  const title = h.document.querySelector("#confirmation-dialog-title");
  let observedTarget = null;
  let observedCurrentTarget = null;
  dialog.addEventListener("click", (event) => {
    observedTarget = event.target;
    observedCurrentTarget = event.currentTarget;
  });

  dispatch(title, "click");

  assert.equal(observedTarget, title);
  assert.equal(observedCurrentTarget, dialog);
  assert.equal(confirmationStateOf(h).open, true);
  assert.equal(confirmationStateOf(h).activeRequestId, 1);
  dispatch(dialog, "click", { target: dialog });
  assert.equal(await result, false);
  assert.equal(h.run('document.querySelector("#upload-dialog").hasAttribute("open")'), true);
});

test("Confirmation throwing open and cleanup fail closed, release ownership, and permit a later request", async () => {
  const h = await createHarness();
  const trigger = h.document.querySelector("#upload-cancel-button");
  trigger.hidden = false;
  trigger.disabled = false;
  trigger.focus();
  h.run(`
    globalThis.__workingShowModal = document.querySelector("#confirmation-dialog").showModal;
    globalThis.__workingConfirmationClose = document.querySelector("#confirmation-dialog").close;
    globalThis.__confirmationCloseAttempts = 0;
    document.querySelector("#confirmation-dialog").showModal = function showModalFailure() {
      this.setAttribute("open", "");
      throw new Error("synthetic showModal failure");
    };
    document.querySelector("#confirmation-dialog").close = function closeFailure() {
      globalThis.__failedConfirmationRequest = activeConfirmationRequest;
      globalThis.__confirmationCloseAttempts += 1;
      throw new Error("synthetic close failure");
    };
  `);

  let failed;
  assert.doesNotThrow(() => {
    failed = h.run(`requestConfirmation({
      title: "Dangerous request",
      message: "This must fail closed.",
      dismissLabel: "Stay",
      confirmLabel: "Proceed",
      destructive: true,
    })`);
  });

  assert.equal(await failed, false);
  const failedState = confirmationStateOf(h);
  const restoredTriggerFocus = h.document.activeElement === trigger;
  assert.equal(h.run("__confirmationCloseAttempts"), 1);

  h.run(`
    document.querySelector("#confirmation-dialog").showModal = __workingShowModal;
    document.querySelector("#confirmation-dialog").close = __workingConfirmationClose;
  `);
  const later = h.run(`requestConfirmation({
    title: "Later request",
    message: "This request must own the dialog.",
    dismissLabel: "No",
    confirmLabel: "Yes",
    destructive: false,
  })`);
  assert.equal(confirmationStateOf(h).open, true);
  assert.equal(confirmationStateOf(h).activeRequestId, 2);
  assert.equal(confirmationStateOf(h).destructive, false);
  h.run("settleConfirmation(__failedConfirmationRequest, true)");
  assert.equal(confirmationStateOf(h).activeRequestId, 2);
  assert.equal(confirmationStateOf(h).open, true);

  assert.deepEqual(failedState, {
    open: false,
    activeRequestId: null,
    title: "",
    message: "",
    dismissLabel: "",
    confirmLabel: "",
    destructive: false,
    focusedDismiss: false,
    focusedConfirm: false,
  });
  assert.equal(restoredTriggerFocus, true);
  activateConfirmation(h, "confirm");
  assert.equal(await later, true);
});

test("Metadata current save owns its request, response, baseline, and one post-save close", async () => {
  const h = await createHarness();
  setMetadataWorkspace(h);
  const saveResponse = deferred();
  const catalogResponse = deferred();
  enqueue(h, "PUT", metadataEndpoint(), saveResponse.promise);
  h.fetchController.enqueue(
    (call) => call.method === "GET" && call.url.startsWith("/api/media?"),
    catalogResponse.promise,
  );
  const initialMetadataRequestToken = h.run("metadataRequestToken");

  const saving = h.run("handleSaveMetadata()");
  await h.flush();

  const calls = h.fetchController.matching("PUT", metadataEndpoint());
  assert.equal(calls.length, 1);
  assert.deepEqual(JSON.parse(calls[0].options.body), {
    display_title: "Unsaved title",
    description: "Unsaved description",
    tag_keys: ["persisted", "unsaved"],
  });
  assert.equal(metadataStateOf(h).saving, true);

  saveResponse.resolve(response({
    metadata: makeMetadataPayload({
      title: "Unsaved title",
      description: "Unsaved description",
      tagKeys: ["persisted", "unsaved"],
    }),
  }));
  await h.flush();

  const applied = metadataStateOf(h);
  assert.equal(applied.metadataOpen, true);
  assert.equal(applied.saving, true);
  assert.equal(applied.currentTitle, "Unsaved title");
  assert.equal(applied.baselineTitle, "Unsaved title");
  assert.equal(applied.baselineDescription, "Unsaved description");
  assert.deepEqual(applied.baselineTags, ["persisted", "unsaved"]);
  assert.equal(applied.dirty, false);

  catalogResponse.resolve(response({ items: [], total: 0, offset: 0, limit: 30, q: "" }));
  await saving;
  await h.flush();

  const closed = metadataStateOf(h);
  assert.equal(closed.metadataOpen, false);
  assert.equal(closed.mediaId, null);
  assert.equal(closed.saving, false);
  assert.equal(closed.saveOwnerToken, null);
  assert.equal(h.run("metadataRequestToken"), initialMetadataRequestToken + 1);
  assert.equal(h.fetchController.matching("PUT", metadataEndpoint()).length, 1);
});

test("Metadata stale cross-media save cannot mutate, report against, confirm, or close a newer workspace", async () => {
  const h = await createHarness();
  setMetadataWorkspace(h);
  const saveResponse = deferred();
  enqueue(h, "PUT", metadataEndpoint(MEDIA_A), saveResponse.promise);
  const savingA = h.run("handleSaveMetadata()");
  await h.flush();

  const closingA = h.run("closeMetadataWorkspace()");
  activateConfirmation(h, "confirm");
  assert.equal(await closingA, true);
  h.context.__mediaBItem = makeCatalogItem(MEDIA_B, LOCATION_B);
  enqueue(h, "GET", metadataEndpoint(MEDIA_B), response(makeMetadataPayload({
    mediaId: MEDIA_B,
    title: "Persisted B",
    description: "Description B",
    tagKeys: ["persisted-b"],
  })));
  await h.run("handleOpenMetadataWorkspace(__mediaBItem, null)");
  const titleInput = h.document.querySelector("#metadata-title-input");
  titleInput.value = "Unsaved B";
  dispatch(titleInput, "input");
  const before = metadataStateOf(h);

  saveResponse.resolve(response({
    metadata: makeMetadataPayload({
      mediaId: MEDIA_A,
      title: "Saved A",
      description: "Saved description A",
      tagKeys: ["saved-a"],
    }),
  }));
  await savingA;
  await h.flush();

  const after = metadataStateOf(h);
  assert.equal(after.mediaId, MEDIA_B);
  assert.equal(after.openItemMediaId, MEDIA_B);
  assert.equal(after.locationId, LOCATION_B);
  assert.equal(after.currentTitle, before.currentTitle);
  assert.equal(after.currentDescription, before.currentDescription);
  assert.deepEqual(after.currentTags, before.currentTags);
  assert.equal(after.baselineTitle, before.baselineTitle);
  assert.equal(after.dirty, true);
  assert.equal(after.metadataOpen, true);
  assert.equal(after.status, before.status);
  assert.equal(after.confirmationRequestId, null);
  assert.equal(after.saveOwnerToken, null);
  assert.equal(h.document.activeElement, titleInput);
});

test("Metadata stale same-media save response preserves a newer edit and baseline", async () => {
  const h = await createHarness();
  setMetadataWorkspace(h);
  const saveResponse = deferred();
  enqueue(h, "PUT", metadataEndpoint(), saveResponse.promise);
  const saving = h.run("handleSaveMetadata()");
  await h.flush();

  const titleInput = h.document.querySelector("#metadata-title-input");
  titleInput.value = "Newer same-media edit";
  dispatch(titleInput, "input");
  saveResponse.resolve(response({
    metadata: makeMetadataPayload({ title: "Stale saved title" }),
  }));
  await saving;
  await h.flush();

  const state = metadataStateOf(h);
  assert.equal(state.currentTitle, "Newer same-media edit");
  assert.equal(state.baselineTitle, "Persisted title");
  assert.equal(state.dirty, true);
  assert.equal(state.saving, false);
  assert.equal(state.saveOwnerToken, null);
  assert.equal(state.metadataOpen, true);
});

test("Metadata save response rejects a replaced media identity independently of revision", async () => {
  const h = await createHarness();
  setMetadataWorkspace(h);
  const saveResponse = deferred();
  enqueue(h, "PUT", metadataEndpoint(MEDIA_A), saveResponse.promise);
  const saving = h.run("handleSaveMetadata()");
  await h.flush();

  h.context.__replacementItem = makeCatalogItem(MEDIA_B, LOCATION_A);
  h.run(`
    metadataWorkspace.openMediaId = __replacementItem.media_id;
    metadataWorkspace.openItem = __replacementItem;
    metadataWorkspace.current.displayTitle = "Replacement B";
    metadataWorkspace.baseline.displayTitle = "Persisted B";
  `);
  saveResponse.resolve(response({
    metadata: makeMetadataPayload({ mediaId: MEDIA_A, title: "Saved A" }),
  }));
  await saving;
  await h.flush();

  const state = metadataStateOf(h);
  assert.equal(state.mediaId, MEDIA_B);
  assert.equal(state.openItemMediaId, MEDIA_B);
  assert.equal(state.locationId, LOCATION_A);
  assert.equal(state.currentTitle, "Replacement B");
  assert.equal(state.baselineTitle, "Persisted B");
  assert.equal(state.metadataOpen, true);
});

test("Metadata post-save close cannot capture fresh authority after the saved workspace is replaced", async () => {
  const h = await createHarness();
  setMetadataWorkspace(h);
  const saveResponse = deferred();
  const catalogResponse = deferred();
  enqueue(h, "PUT", metadataEndpoint(MEDIA_A), saveResponse.promise);
  h.fetchController.enqueue(
    (call) => call.method === "GET" && call.url.startsWith("/api/media?"),
    catalogResponse.promise,
  );
  const savingA = h.run("handleSaveMetadata()");
  await h.flush();
  saveResponse.resolve(response({
    metadata: makeMetadataPayload({
      mediaId: MEDIA_A,
      title: "Unsaved title",
      description: "Unsaved description",
      tagKeys: ["persisted", "unsaved"],
    }),
  }));
  await h.flush();
  assert.equal(metadataStateOf(h).dirty, false);

  const closingA = h.run("closeMetadataWorkspace()");
  assert.equal(await closingA, true);
  h.context.__mediaBItem = makeCatalogItem(MEDIA_B, LOCATION_B);
  enqueue(h, "GET", metadataEndpoint(MEDIA_B), response(makeMetadataPayload({
    mediaId: MEDIA_B,
    title: "Persisted B",
    description: "Description B",
    tagKeys: ["persisted-b"],
  })));
  await h.run("handleOpenMetadataWorkspace(__mediaBItem, null)");
  const titleInput = h.document.querySelector("#metadata-title-input");
  titleInput.value = "Unsaved B";
  dispatch(titleInput, "input");
  const before = metadataStateOf(h);

  catalogResponse.resolve(response({ items: [], total: 0, offset: 0, limit: 30, q: "" }));
  await savingA;
  await h.flush();

  const after = metadataStateOf(h);
  assert.equal(after.mediaId, MEDIA_B);
  assert.equal(after.currentTitle, before.currentTitle);
  assert.equal(after.baselineTitle, before.baselineTitle);
  assert.equal(after.dirty, true);
  assert.equal(after.metadataOpen, true);
  assert.equal(after.confirmationRequestId, null);
  assert.equal(h.document.activeElement, titleInput);
});

test("Metadata stale save success, error, and finally cannot release a newer owner", async (t) => {
  for (const staleOutcome of ["success", "error"]) {
    await t.test(staleOutcome, async () => {
      const h = await createHarness();
      setMetadataWorkspace(h);
      const saveAResponse = deferred();
      enqueue(h, "PUT", metadataEndpoint(MEDIA_A), saveAResponse.promise);
      const savingA = h.run("handleSaveMetadata()");
      await h.flush();

      const closingA = h.run("closeMetadataWorkspace()");
      activateConfirmation(h, "confirm");
      assert.equal(await closingA, true);
      h.context.__mediaBItem = makeCatalogItem(MEDIA_B, LOCATION_B);
      enqueue(h, "GET", metadataEndpoint(MEDIA_B), response(makeMetadataPayload({
        mediaId: MEDIA_B,
        title: "Persisted B",
        description: "Description B",
        tagKeys: ["persisted-b"],
      })));
      await h.run("handleOpenMetadataWorkspace(__mediaBItem, null)");
      const titleInput = h.document.querySelector("#metadata-title-input");
      titleInput.value = "Unsaved B";
      dispatch(titleInput, "input");

      const saveBResponse = deferred();
      enqueue(h, "PUT", metadataEndpoint(MEDIA_B), saveBResponse.promise);
      const savingB = h.run("handleSaveMetadata()");
      await h.flush();
      const ownerB = metadataStateOf(h).saveOwnerToken;
      assert.ok(ownerB);

      if (staleOutcome === "success") {
        saveAResponse.resolve(response({
          metadata: makeMetadataPayload({ mediaId: MEDIA_A, title: "Saved A" }),
        }));
      } else {
        saveAResponse.reject(new Error("synthetic stale save failure"));
      }
      await savingA;
      await h.flush();

      const whileBIsSaving = metadataStateOf(h);
      assert.equal(whileBIsSaving.mediaId, MEDIA_B);
      assert.equal(whileBIsSaving.currentTitle, "Unsaved B");
      assert.equal(whileBIsSaving.saving, true);
      assert.equal(whileBIsSaving.status, "Saving...");
      assert.equal(whileBIsSaving.saveOwnerToken, ownerB);
      assert.equal(whileBIsSaving.saveOwnerMediaId, MEDIA_B);
      assert.equal(whileBIsSaving.confirmationRequestId, null);

      saveBResponse.resolve(response({
        metadata: makeMetadataPayload({
          mediaId: MEDIA_B,
          title: "Unsaved B",
          description: "Description B",
          tagKeys: ["persisted-b"],
        }),
      }));
      await savingB;
      await h.flush();
      assert.equal(metadataStateOf(h).mediaId, null);
      assert.equal(metadataStateOf(h).saveOwnerToken, null);
    });
  }
});

test("Metadata safe action, Escape, and backdrop preserve the dirty workspace and focus", async (t) => {
  for (const dismissal of ["safe action", "Escape", "backdrop"]) {
    await t.test(dismissal, async () => {
      const h = await createHarness();
      setMetadataWorkspace(h);
      const closeButton = h.document.querySelector("#metadata-close-button");
      closeButton.focus();
      const before = metadataStateOf(h);
      const closing = h.run("closeMetadataWorkspace()");

      if (dismissal === "safe action") activateConfirmation(h, "dismiss");
      else if (dismissal === "Escape") dismissConfirmationWithEscape(h);
      else dispatch(h.document.querySelector("#confirmation-dialog"), "click", {
        target: h.document.querySelector("#confirmation-dialog"),
      });

      assert.equal(await closing, false);
      const after = metadataStateOf(h);
      assert.equal(after.mediaId, before.mediaId);
      assert.equal(after.openItemMediaId, before.openItemMediaId);
      assert.equal(after.currentTitle, before.currentTitle);
      assert.equal(after.currentDescription, before.currentDescription);
      assert.deepEqual(after.currentTags, before.currentTags);
      assert.equal(after.dirty, true);
      assert.equal(after.metadataOpen, true);
      assert.equal(after.focusedClose, true);
      assert.equal(h.fetchController.matchingPrefix("GET", "/api/media?").length, 0);
    });
  }
});

test("Metadata current affirmative discard closes exactly once despite repeated triggering", async () => {
  const h = await createHarness();
  setMetadataWorkspace(h);
  const initialRequestToken = h.run("metadataRequestToken");
  const first = h.run("closeMetadataWorkspace()");
  const repeated = h.run("closeMetadataWorkspace()");

  activateConfirmation(h, "confirm");
  assert.equal(await first, true);
  assert.equal(await repeated, false);
  await h.flush();

  assert.equal(metadataStateOf(h).mediaId, null);
  assert.equal(metadataStateOf(h).metadataOpen, false);
  assert.equal(h.run("metadataRequestToken"), initialRequestToken + 1);
  assert.equal(h.fetchController.matchingPrefix("GET", "/api/media?").length, 1);
});

test("Metadata newer edit revision invalidates a pending affirmative discard", async () => {
  const h = await createHarness();
  setMetadataWorkspace(h);
  const closing = h.run("closeMetadataWorkspace()");
  const titleInput = h.document.querySelector("#metadata-title-input");
  titleInput.value = "Newer unsaved title";
  dispatch(titleInput, "input");

  activateConfirmation(h, "confirm");
  assert.equal(await closing, false);

  const state = metadataStateOf(h);
  assert.equal(state.mediaId, MEDIA_A);
  assert.equal(state.currentTitle, "Newer unsaved title");
  assert.equal(state.dirty, true);
  assert.equal(state.metadataOpen, true);
  assert.equal(h.fetchController.matchingPrefix("GET", "/api/media?").length, 0);
});

test("Metadata media identity change invalidates a pending affirmative discard", async () => {
  const h = await createHarness();
  setMetadataWorkspace(h);
  const closing = h.run("closeMetadataWorkspace()");
  h.context.__newerMetadataItem = makeCatalogItem(MEDIA_B, LOCATION_B);
  h.run(`
    metadataWorkspace.openMediaId = __newerMetadataItem.media_id;
    metadataWorkspace.openItem = __newerMetadataItem;
    metadataWorkspace.current.displayTitle = "Newer media edits";
    document.querySelector("#metadata-title-input").value = "Newer media edits";
    advanceMetadataWorkspaceRevision();
  `);

  activateConfirmation(h, "confirm");
  assert.equal(await closing, false);

  const state = metadataStateOf(h);
  assert.equal(state.mediaId, MEDIA_B);
  assert.equal(state.openItemMediaId, MEDIA_B);
  assert.equal(state.currentTitle, "Newer media edits");
  assert.equal(state.metadataOpen, true);
});

test("Metadata scope or workspace replacement invalidates a pending affirmative discard", async () => {
  const h = await createHarness();
  setMetadataWorkspace(h);
  const closing = h.run("closeMetadataWorkspace()");
  h.run("setCatalogScope(PROCESSED_COLLECTION)");

  activateConfirmation(h, "confirm");
  assert.equal(await closing, false);

  const state = metadataStateOf(h);
  assert.equal(state.mediaId, MEDIA_A);
  assert.equal(state.scope, "processed");
  assert.equal(state.currentTitle, "Unsaved title");
  assert.equal(state.metadataOpen, true);
});

test("Metadata AI safe action, Escape, and backdrop issue zero requests and preserve workspace", async (t) => {
  for (const dismissal of ["safe action", "Escape", "backdrop"]) {
    await t.test(dismissal, async () => {
      const h = await createHarness();
      setMetadataWorkspace(h);
      enableMetadataAi(h);
      const analyzeButton = h.document.querySelector("#metadata-ai-analyze-button");
      analyzeButton.focus();
      const before = metadataStateOf(h);
      const analysis = h.run("handleAnalyzeMetadataByAi()");

      if (dismissal === "safe action") activateConfirmation(h, "dismiss");
      else if (dismissal === "Escape") dismissConfirmationWithEscape(h);
      else dispatch(h.document.querySelector("#confirmation-dialog"), "click", {
        target: h.document.querySelector("#confirmation-dialog"),
      });

      await analysis;
      await h.flush();
      const after = metadataStateOf(h);
      assert.equal(h.fetchController.matchingPrefix("POST", "/api/media/").length, 0);
      assert.equal(after.mediaId, before.mediaId);
      assert.equal(after.currentTitle, before.currentTitle);
      assert.equal(after.currentDescription, before.currentDescription);
      assert.deepEqual(after.currentTags, before.currentTags);
      assert.equal(after.analyzing, false);
      assert.equal(after.metadataOpen, true);
      assert.equal(after.focusedAnalyze, true);
    });
  }
});

test("Metadata AI uses one revalidated media-location identity and one request owner", async () => {
  const h = await createHarness();
  setMetadataWorkspace(h);
  enableMetadataAi(h);
  const pendingResponse = deferred();
  enqueue(h, "POST", metadataAiEndpoint(), pendingResponse.promise);

  const first = h.run("handleAnalyzeMetadataByAi()");
  const repeated = h.run("handleAnalyzeMetadataByAi()");
  activateConfirmation(h, "confirm");
  activateConfirmation(h, "confirm");
  await h.flush();

  const calls = h.fetchController.matching("POST", metadataAiEndpoint());
  assert.equal(calls.length, 1);
  assert.equal(h.fetchController.matchingPrefix("POST", `/api/media/${MEDIA_B}/`).length, 0);
  assert.equal(metadataStateOf(h).analyzing, true);

  pendingResponse.resolve(response({
    suggestion: {
      title: "AI title",
      description: "AI description",
      tags: [],
      suggested_filename: "ai-title.mp4",
    },
  }));
  await Promise.all([first, repeated]);
  await h.flush();

  const state = metadataStateOf(h);
  assert.equal(state.analyzing, false);
  assert.equal(state.aiSuggestionApplied, true);
  assert.equal(state.currentTitle, "AI title");
  assert.equal(state.currentDescription, "AI description");
  assert.equal(state.suggestedFilename, "ai-title.mp4");
});

test("Metadata AI endpoint cannot mix live media with a captured location", async () => {
  const h = await createHarness();
  setMetadataWorkspace(h);
  enableMetadataAi(h);
  enqueue(h, "POST", metadataAiEndpoint(MEDIA_A, LOCATION_A), response({
    suggestion: {
      title: "Captured identity title",
      description: "Captured identity description",
      tags: [],
      suggested_filename: "captured.mp4",
    },
  }));
  const analysis = h.run("handleAnalyzeMetadataByAi()");
  h.run(`
    globalThis.__metadataMediaReads = 0;
    Object.defineProperty(metadataWorkspace, "openMediaId", {
      configurable: true,
      get() {
        globalThis.__metadataMediaReads += 1;
        return globalThis.__metadataMediaReads === 1 ? ${MEDIA_A} : ${MEDIA_B};
      },
    });
  `);

  activateConfirmation(h, "confirm");
  await analysis;
  await h.flush();

  assert.equal(h.fetchController.matching("POST", metadataAiEndpoint(MEDIA_A, LOCATION_A)).length, 1);
  assert.equal(h.fetchController.matching("POST", metadataAiEndpoint(MEDIA_B, LOCATION_A)).length, 0);
  assert.equal(h.fetchController.matchingPrefix("POST", "/api/media/").length, 1);
});

test("Metadata AI stale same-media error and finally cannot release a newer request owner", async () => {
  const h = await createHarness();
  setMetadataWorkspace(h);
  enableMetadataAi(h);
  const requestAResponse = deferred();
  const requestBResponse = deferred();
  enqueue(h, "POST", metadataAiEndpoint(), requestAResponse.promise);
  enqueue(h, "POST", metadataAiEndpoint(), requestBResponse.promise);

  const requestA = h.run("handleAnalyzeMetadataByAi()");
  activateConfirmation(h, "confirm");
  await h.flush();
  h.run(`
    metadataWorkspace.analyzing = false;
    advanceMetadataWorkspaceRevision();
    updateMetadataControls();
  `);
  const requestB = h.run("handleAnalyzeMetadataByAi()");
  activateConfirmation(h, "confirm");
  await h.flush();
  const ownerB = h.run("metadataAiRequestToken");
  assert.equal(h.fetchController.matching("POST", metadataAiEndpoint()).length, 2);
  assert.equal(metadataStateOf(h).analyzing, true);

  requestAResponse.reject(new Error("synthetic stale AI failure"));
  await requestA;
  await h.flush();

  assert.equal(h.run("metadataAiRequestToken"), ownerB);
  assert.equal(metadataStateOf(h).analyzing, true);
  assert.equal(h.document.querySelector("#metadata-ai-status").textContent, "");

  requestBResponse.resolve(response({
    suggestion: {
      title: "New owner title",
      description: "New owner description",
      tags: [],
      suggested_filename: "new-owner.mp4",
    },
  }));
  await requestB;
  await h.flush();

  const state = metadataStateOf(h);
  assert.equal(state.analyzing, false);
  assert.equal(state.aiSuggestionApplied, true);
  assert.equal(state.currentTitle, "New owner title");
  assert.equal(state.currentDescription, "New owner description");
  assert.equal(state.suggestedFilename, "new-owner.mp4");
});

test("Metadata AI stale response media, location, and capability cannot apply", async (t) => {
  for (const replacement of ["media", "location", "capability"]) {
    await t.test(replacement, async () => {
      const h = await createHarness();
      setMetadataWorkspace(h);
      enableMetadataAi(h);
      const pendingResponse = deferred();
      enqueue(h, "POST", metadataAiEndpoint(), pendingResponse.promise);
      const analysis = h.run("handleAnalyzeMetadataByAi()");
      activateConfirmation(h, "confirm");
      await h.flush();

      if (replacement === "media") {
        h.context.__replacementItem = makeCatalogItem(MEDIA_B, LOCATION_B);
        h.run(`
          metadataWorkspace.openMediaId = __replacementItem.media_id;
          metadataWorkspace.openItem = __replacementItem;
          metadataWorkspace.current.displayTitle = "Replacement media title";
          metadataWorkspace.analyzing = false;
          advanceMetadataWorkspaceRevision();
        `);
      } else if (replacement === "location") {
        h.context.__replacementItem = makeCatalogItem(MEDIA_A, LOCATION_B);
        h.run("metadataWorkspace.openItem = __replacementItem");
      } else {
        h.run('renderAiCapability({ available: false, status: "not_configured" })');
      }

      pendingResponse.resolve(response({
        suggestion: {
          title: "Stale AI title",
          description: "Stale AI description",
          tags: [],
          suggested_filename: "stale-ai.mp4",
        },
      }));
      await analysis;
      await h.flush();

      const state = metadataStateOf(h);
      assert.equal(state.aiSuggestionApplied, false);
      assert.equal(state.suggestedFilename, "");
      assert.notEqual(state.currentTitle, "Stale AI title");
      assert.equal(state.analyzing, false);
      if (replacement === "media") {
        assert.equal(state.mediaId, MEDIA_B);
        assert.equal(state.locationId, LOCATION_B);
        assert.equal(state.currentTitle, "Replacement media title");
      } else if (replacement === "location") {
        assert.equal(state.mediaId, MEDIA_A);
        assert.equal(state.locationId, LOCATION_B);
      }
    });
  }
});

test("Metadata AI stale media or location context issues zero requests and preserves newer workspace", async (t) => {
  await t.test("media identity", async () => {
    const h = await createHarness();
    setMetadataWorkspace(h);
    enableMetadataAi(h);
    const analysis = h.run("handleAnalyzeMetadataByAi()");
    h.context.__newerAiItem = makeCatalogItem(MEDIA_B, LOCATION_A);
    h.run(`
      metadataWorkspace.openMediaId = __newerAiItem.media_id;
      metadataWorkspace.openItem = __newerAiItem;
      metadataWorkspace.current.displayTitle = "Newer media title";
      document.querySelector("#metadata-title-input").value = "Newer media title";
      advanceMetadataWorkspaceRevision();
    `);

    activateConfirmation(h, "confirm");
    await analysis;
    await h.flush();

    assert.equal(h.fetchController.matching("POST", metadataAiEndpoint(MEDIA_B, LOCATION_A)).length, 0);
    assert.equal(h.fetchController.matchingPrefix("POST", "/api/media/").length, 0);
    assert.equal(metadataStateOf(h).mediaId, MEDIA_B);
    assert.equal(metadataStateOf(h).currentTitle, "Newer media title");
    assert.equal(metadataStateOf(h).analyzing, false);
  });

  await t.test("location identity", async () => {
    const h = await createHarness();
    setMetadataWorkspace(h);
    enableMetadataAi(h);
    const analysis = h.run("handleAnalyzeMetadataByAi()");
    h.context.__newerLocationItem = makeCatalogItem(MEDIA_A, LOCATION_B);
    h.run("metadataWorkspace.openItem = __newerLocationItem");

    activateConfirmation(h, "confirm");
    await analysis;
    await h.flush();

    assert.equal(h.fetchController.matchingPrefix("POST", "/api/media/").length, 0);
    assert.equal(metadataStateOf(h).mediaId, MEDIA_A);
    assert.equal(metadataStateOf(h).locationId, LOCATION_B);
    assert.equal(metadataStateOf(h).analyzing, false);
  });
});

test("Metadata AI capability or analyzing ownership change invalidates pending confirmation", async (t) => {
  await t.test("capability", async () => {
    const h = await createHarness();
    setMetadataWorkspace(h);
    enableMetadataAi(h);
    const analysis = h.run("handleAnalyzeMetadataByAi()");
    h.run('renderAiCapability({ available: false, status: "not_configured" })');

    activateConfirmation(h, "confirm");
    await analysis;
    await h.flush();

    assert.equal(h.fetchController.matchingPrefix("POST", "/api/media/").length, 0);
    assert.equal(metadataStateOf(h).analyzing, false);
  });

  await t.test("analysis ownership", async () => {
    const h = await createHarness();
    setMetadataWorkspace(h);
    enableMetadataAi(h);
    const analysis = h.run("handleAnalyzeMetadataByAi()");
    h.run(`
      metadataAiRequestToken += 1;
      metadataWorkspace.analyzing = true;
      advanceMetadataWorkspaceRevision();
    `);

    activateConfirmation(h, "confirm");
    await analysis;
    await h.flush();

    assert.equal(h.fetchController.matchingPrefix("POST", "/api/media/").length, 0);
    assert.equal(metadataStateOf(h).analyzing, true);
  });
});

test("Metadata AI response cannot overwrite a newer edit revision", async () => {
  const h = await createHarness();
  setMetadataWorkspace(h);
  enableMetadataAi(h);
  const pendingResponse = deferred();
  enqueue(h, "POST", metadataAiEndpoint(), pendingResponse.promise);
  const analysis = h.run("handleAnalyzeMetadataByAi()");
  activateConfirmation(h, "confirm");
  await h.flush();
  assert.equal(h.fetchController.matching("POST", metadataAiEndpoint()).length, 1);

  const titleInput = h.document.querySelector("#metadata-title-input");
  titleInput.value = "Edit made while AI was running";
  dispatch(titleInput, "input");
  pendingResponse.resolve(response({
    suggestion: {
      title: "Stale AI title",
      description: "Stale AI description",
      tags: [],
      suggested_filename: "stale.mp4",
    },
  }));
  await analysis;
  await h.flush();

  const state = metadataStateOf(h);
  assert.equal(state.currentTitle, "Edit made while AI was running");
  assert.equal(state.aiSuggestionApplied, false);
  assert.equal(state.suggestedFilename, "");
  assert.equal(state.analyzing, false);
  assert.equal(state.metadataOpen, true);
});

test("Cancel upload confirms once, sends one DELETE, fences stale work, and focuses status", async () => {
  const h = await createHarness();
  setActiveUpload(h, { id: UPLOAD_A, state: "receiving", received: 4 });
  h.run(`
    document.querySelector("#upload-dialog").setAttribute("open", "");
    document.querySelector("#upload-cancel-button").focus();
  `);
  const cancellation = deferred();
  enqueue(h, "DELETE", `/api/uploads/${UPLOAD_A}`, cancellation.promise);
  const cancelPromise = h.run("handleCancelUpload()");
  const duplicatePromise = h.run("handleCancelUpload()");
  activateConfirmation(h, "confirm");
  activateConfirmation(h, "confirm");
  await h.flush();

  await duplicatePromise;
  assert.equal(stateOf(h).stateLabel, "Cancelling");
  assert.equal(stateOf(h).cancelHidden, true);
  assert.equal(stateOf(h).focusedStatus, true);
  assert.equal(h.fetchController.matching("DELETE", `/api/uploads/${UPLOAD_A}`).length, 1);

  cancellation.resolve(response(snapshot(UPLOAD_A, "cancelled", 4)));
  await cancelPromise;
  await h.flush();

  assert.equal(h.fetchController.matching("DELETE", `/api/uploads/${UPLOAD_A}`).length, 1);
  assert.equal(stateOf(h).snapshotState, "cancelled");
  assert.equal(stateOf(h).stateLabel, "Cancelled");
  assert.equal(stateOf(h).cancelHidden, true);
});

test("Repeated destructive activation cannot send a second DELETE", async () => {
  const h = await createHarness();
  setActiveUpload(h, { id: UPLOAD_A, state: "receiving", received: 4 });
  const cancellation = deferred();
  enqueue(h, "DELETE", `/api/uploads/${UPLOAD_A}`, cancellation.promise);

  const first = h.run("handleCancelUpload()");
  const repeatedHandler = h.run("handleCancelUpload()");
  activateConfirmation(h, "confirm");
  activateConfirmation(h, "confirm");
  await h.flush();

  assert.equal(h.fetchController.matching("DELETE", `/api/uploads/${UPLOAD_A}`).length, 1);
  cancellation.resolve(response(snapshot(UPLOAD_A, "cancelled", 4)));
  await Promise.all([first, repeatedHandler]);
});

test("Start is synchronously fenced and stale create responses cannot replace newer state", async () => {
  const h = await createHarness();
  setSelectedFile(h, makeFile("first.gif", 8));
  const capability = deferred();
  const create = deferred();
  enqueue(h, "GET", "/api/uploads/capability", capability.promise);
  enqueue(h, "POST", "/api/uploads", create.promise);

  const first = h.run("handleStartUpload()");
  const second = h.run("handleStartUpload()");
  await h.flush();

  assert.equal(stateOf(h).actionKind, "start");
  assert.equal(h.fetchController.matching("GET", "/api/uploads/capability").length, 1);
  assert.equal(h.fetchController.matching("POST", "/api/uploads").length, 0);

  capability.resolve(response({
    uploads_enabled: true,
    max_total_size_bytes: 1024,
    max_chunk_size_bytes: 4,
    session_ttl_seconds: 60,
  }));
  await h.flush();

  assert.equal(h.fetchController.matching("POST", "/api/uploads").length, 1);

  setSelectedFile(h, makeFile("second.gif", 8, 5678));
  create.resolve(response(snapshot(UPLOAD_A, "created", 0)));
  await Promise.all([first, second]);
  await h.flush();

  assert.equal(stateOf(h).uploadId, null);
  assert.equal(stateOf(h).hasLoopOwner, false);
});

test("Resume is synchronously fenced and stale status cannot start an upload loop", async () => {
  const h = await createHarness();
  setActiveUpload(h, { id: UPLOAD_A, state: "receiving", received: 0 });
  const status = deferred();
  enqueueStatus(h, UPLOAD_A, status.promise);

  const first = h.run("handleResumeUpload()");
  const second = h.run("handleResumeUpload()");
  await h.flush();

  assert.equal(stateOf(h).actionKind, "resume");
  assert.equal(h.fetchController.matching("GET", `/api/uploads/${UPLOAD_A}`).length, 1);

  setSelectedFile(h, makeFile("new.gif", 8, 9999));
  status.resolve(response(snapshot(UPLOAD_A, "receiving", 0)));
  await Promise.all([first, second]);
  await h.flush();

  assert.equal(stateOf(h).uploadId, null);
  assert.equal(stateOf(h).hasLoopOwner, false);
  assert.equal(h.fetchController.matching("PATCH", `/api/uploads/${UPLOAD_A}`).length, 0);
});

test("Resume starts only one PATCH loop when the status owner is current", async () => {
  const h = await createHarness();
  setActiveUpload(h, { id: UPLOAD_A, state: "receiving", received: 0 });
  enqueueStatus(h, UPLOAD_A, response(snapshot(UPLOAD_A, "receiving", 0)));
  enqueueStatus(h, UPLOAD_A, response(snapshot(UPLOAD_A, "receiving", 0)));
  const patch = deferred();
  enqueue(h, "PATCH", `/api/uploads/${UPLOAD_A}`, patch.promise);

  const first = h.run("handleResumeUpload()");
  const second = h.run("handleResumeUpload()");
  await h.flush();

  assert.equal(h.fetchController.matching("PATCH", `/api/uploads/${UPLOAD_A}`).length, 1);
  patch.resolve(response(snapshot(UPLOAD_A, "receiving", 4)));
  await first;
  await second;
});

test("Delayed status from upload A is ignored after upload B becomes active", async () => {
  const h = await createHarness();
  setActiveUpload(h, { id: UPLOAD_A, state: "receiving", received: 0 });
  const delayedStatus = deferred();
  enqueueStatus(h, UPLOAD_A, delayedStatus.promise);

  const refresh = h.run("refreshUploadStatus(uploadState.uploadId)");
  await h.flush();

  setActiveUpload(h, { id: UPLOAD_B, state: "receiving", received: 0 });
  delayedStatus.resolve(response(snapshot(UPLOAD_A, "publish_pending", 8)));
  await refresh;
  await h.flush();

  assert.equal(stateOf(h).uploadId, UPLOAD_B);
  assert.equal(stateOf(h).snapshotState, "receiving");
});

test("Cancel invalidates a delayed PATCH and prevents another chunk from being scheduled", async () => {
  const h = await createHarness();
  setActiveUpload(h, { id: UPLOAD_A, state: "receiving", received: 0 });
  enqueueStatus(h, UPLOAD_A, response(snapshot(UPLOAD_A, "receiving", 0)));
  const patch = deferred();
  enqueue(h, "PATCH", `/api/uploads/${UPLOAD_A}`, patch.promise);

  const loop = h.run("runUploadLoop(currentUploadContext({ uploadId: uploadState.uploadId, file: uploadState.file }))");
  await h.flush();
  assert.equal(h.fetchController.matching("PATCH", `/api/uploads/${UPLOAD_A}`).length, 1);

  enqueue(h, "DELETE", `/api/uploads/${UPLOAD_A}`, response(snapshot(UPLOAD_A, "cancelled", 0)));
  const cancellation = h.run("handleCancelUpload()");
  activateConfirmation(h, "confirm");
  await cancellation;
  await h.flush();
  assert.equal(stateOf(h).snapshotState, "cancelled");

  patch.resolve(response(snapshot(UPLOAD_A, "receiving", 4)));
  await loop;
  await h.flush();

  assert.equal(stateOf(h).snapshotState, "cancelled");
  assert.equal(h.fetchController.matching("PATCH", `/api/uploads/${UPLOAD_A}`).length, 1);
});

test("Completion has one owner and stale completion cannot overwrite a newer upload", async () => {
  const h = await createHarness();
  setActiveUpload(h, { id: UPLOAD_A, state: "receiving", received: 8 });
  const completion = deferred();
  enqueue(h, "POST", `/api/uploads/${UPLOAD_A}/complete`, completion.promise);

  const first = h.run("completeUploadIfReady(currentUploadContext({ uploadId: uploadState.uploadId, file: uploadState.file }))");
  const second = h.run("completeUploadIfReady(currentUploadContext({ uploadId: uploadState.uploadId, file: uploadState.file }))");
  await h.flush();

  assert.equal(h.fetchController.matching("POST", `/api/uploads/${UPLOAD_A}/complete`).length, 1);
  assert.equal(stateOf(h).hasCompletionOwner, true);

  setActiveUpload(h, { id: UPLOAD_B, state: "receiving", received: 0 });
  completion.resolve(response(snapshot(UPLOAD_A, "received", 8)));
  await Promise.all([first, second]);
  await h.flush();

  assert.equal(stateOf(h).uploadId, UPLOAD_B);
  assert.equal(stateOf(h).snapshotState, "receiving");
});

test("Polling retries transient failures with bounded backoff and stops for unknown states", async () => {
  const h = await createHarness();
  setActiveUpload(h, { id: UPLOAD_A, state: "received", received: 8, file: makeFile("sample.gif", 8) });
  h.run('document.querySelector("#upload-dialog").setAttribute("open", "")');
  h.run("scheduleUploadPolling(currentUploadContext({ uploadId: uploadState.uploadId, file: uploadState.file }))");
  assert.equal(stateOf(h).hasPollTimer, true);

  enqueueStatus(h, UPLOAD_A, Promise.reject(new Error("temporary network failure")));
  const firstDelay = h.runNextTimer();
  assert.equal(firstDelay, 1200);
  await h.flush();

  assert.equal(stateOf(h).hasPollOwner, true);
  assert.equal(stateOf(h).pollRetryDelayMs, 2400);
  assert.match(stateOf(h).message, /temporarily unavailable/);

  enqueueStatus(h, UPLOAD_A, response(snapshot(UPLOAD_A, "validating", 8)));
  const retryDelay = h.runNextTimer();
  assert.equal(retryDelay, 2400);
  await h.flush();

  assert.equal(stateOf(h).pollRetryDelayMs, 1200);
  assert.equal(stateOf(h).hasPollOwner, true);

  enqueueStatus(h, UPLOAD_A, response(snapshot(UPLOAD_A, "future_state", 8)));
  h.runNextTimer();
  await h.flush();

  assert.equal(stateOf(h).snapshotState, "future_state");
  assert.equal(stateOf(h).hasPollOwner, false);
  assert.equal(stateOf(h).hasPollTimer, false);
});

test("Recovery parsing rejects malformed, invalid, unsafe, and terminal records", async () => {
  const h = await createHarness();
  h.context.localStorage.setItem(RECOVERY_KEY, "{bad json");
  assert.equal(h.run("loadUploadRecovery()"), null);
  assert.equal(h.context.localStorage.getItem(RECOVERY_KEY), null);

  for (const expectedSizeBytes of [-1, 0, 1.5, 9007199254740992]) {
    h.context.localStorage.setItem(RECOVERY_KEY, JSON.stringify({
      upload_id: UPLOAD_A,
      file_name_hint: "sample.gif",
      expected_size_bytes: expectedSizeBytes,
      last_modified_hint: 1,
      last_known_state: "receiving",
    }));
    assert.equal(h.run("loadUploadRecovery()"), null);
    assert.equal(h.context.localStorage.getItem(RECOVERY_KEY), null);
  }

  h.context.localStorage.setItem(RECOVERY_KEY, JSON.stringify({
    upload_id: "not-an-upload-id",
    file_name_hint: "sample.gif",
    expected_size_bytes: 8,
    last_known_state: "receiving",
  }));
  await h.run("restoreUploadRecovery()");
  assert.equal(h.context.localStorage.getItem(RECOVERY_KEY), null);
  assert.equal(h.fetchController.matchingPrefix("GET", "/api/uploads/not-an-upload-id").length, 0);

  h.context.localStorage.setItem(RECOVERY_KEY, JSON.stringify({
    upload_id: UPLOAD_A,
    file_name_hint: "sample.gif",
    expected_size_bytes: 8,
    last_known_state: "publish_pending",
  }));
  assert.equal(h.run("loadUploadRecovery()"), null);
  assert.equal(h.context.localStorage.getItem(RECOVERY_KEY), null);
});

test("Recovery not-found is cleared and persisted recovery stores no private bytes, handles, paths, or raw errors", async () => {
  const h = await createHarness();
  h.context.localStorage.setItem(RECOVERY_KEY, JSON.stringify({
    upload_id: UPLOAD_C,
    file_name_hint: "missing.gif",
    expected_size_bytes: 8,
    last_modified_hint: 1,
    last_known_state: "receiving",
  }));
  enqueueStatus(h, UPLOAD_C, response({ error: { code: "UPLOAD_SESSION_NOT_FOUND" } }, 404));
  await h.run("restoreUploadRecovery()");
  await h.flush();

  assert.equal(stateOf(h).uploadId, null);
  assert.equal(h.context.localStorage.getItem(RECOVERY_KEY), null);
  assert.match(stateOf(h).message, /not found/);

  setActiveUpload(h, { id: UPLOAD_A, state: "receiving", received: 4 });
  const stored = JSON.parse(stateOf(h).recovery);
  assert.deepEqual(Object.keys(stored).sort(), [
    "expected_size_bytes",
    "file_name_hint",
    "last_known_state",
    "last_modified_hint",
    "upload_id",
  ]);
  const serialized = JSON.stringify(stored);
  for (const forbidden of ["file_bytes", "payload_base64", "file_handle", "filesystem_path", "server_path", "storage_key", "traceback"]) {
    assert.equal(serialized.includes(forbidden), false);
  }

  h.context.__terminal = snapshot(UPLOAD_A, "failed", 8);
  h.run("applyUploadSnapshot(__terminal, currentUploadContext({ uploadId: uploadState.uploadId, file: uploadState.file }))");
  assert.equal(h.context.localStorage.getItem(RECOVERY_KEY), null);
});

test("Recovered upload is ready after source reselection and waits for explicit Resume before PATCH", async () => {
  const h = await createHarness();
  h.context.localStorage.setItem(RECOVERY_KEY, JSON.stringify({
    upload_id: UPLOAD_A,
    file_name_hint: "sample.gif",
    expected_size_bytes: 8,
    last_modified_hint: 1234,
    last_known_state: "receiving",
  }));
  enqueueStatus(h, UPLOAD_A, response(snapshot(UPLOAD_A, "receiving", 4)));

  await h.run("restoreUploadRecovery()");
  await h.flush();

  assert.equal(stateOf(h).snapshotState, "receiving");
  assert.equal(stateOf(h).received, 4);
  assert.equal(stateOf(h).stateLabel, "Reselect file to resume");
  assert.equal(stateOf(h).resumeDisabled, true);

  h.context.__file = makeFile("sample.gif", 8, 1234);
  h.run(`
    const input = document.querySelector("#upload-file-input");
    input.files = [__file];
    handleUploadFileSelection();
  `);
  await h.flush();

  const reselected = stateOf(h);
  assert.equal(reselected.received, 4);
  assert.equal(reselected.byteCount, "4 B / 8 B");
  assert.equal(reselected.stateLabel, "Ready to resume");
  assert.notEqual(reselected.stateLabel, "Uploading");
  assert.equal(reselected.visibleMessage, "Ready to resume.");
  assert.equal(reselected.visibleMessage.includes("Source file reselected"), false);
  assert.equal(reselected.pauseHidden, true);
  assert.equal(reselected.resumeHidden, false);
  assert.equal(reselected.resumeDisabled, false);
  assert.equal(reselected.cancelHidden, false);
  assert.equal(reselected.cancelLabel, "Cancel");
  assert.equal(h.fetchController.matching("PATCH", `/api/uploads/${UPLOAD_A}`).length, 0);

  enqueueStatus(h, UPLOAD_A, response(snapshot(UPLOAD_A, "receiving", 4)));
  enqueueStatus(h, UPLOAD_A, response(snapshot(UPLOAD_A, "receiving", 4)));
  enqueue(h, "PATCH", `/api/uploads/${UPLOAD_A}`, response(snapshot(UPLOAD_A, "receiving", 8)));

  await h.run("handleResumeUpload()");
  await h.flush();

  const patchCalls = h.fetchController.matching("PATCH", `/api/uploads/${UPLOAD_A}`);
  assert.equal(patchCalls.length, 1);
  assert.equal(patchCalls[0].options.headers["Upload-Offset"], "4");
  assert.equal(patchCalls[0].options.body.start, 4);
  assert.equal(patchCalls[0].options.body.end, 8);
});
