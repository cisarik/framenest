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
      listeners.set(type, listener);
    },
    removeEventListener(type) {
      listeners.delete(type);
    },
    dispatchEvent(event) {
      const listener = listeners.get(event.type);
      if (listener) listener(event);
    },
    append(...nodes) {
      this.children.push(...nodes);
    },
    appendChild(node) {
      this.children.push(node);
      return node;
    },
    replaceChildren(...nodes) {
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
  const document = {
    activeElement: null,
    querySelector(selector) {
      if (!elements.has(selector)) {
        const element = createElement(document);
        applySelectorDefaults(selector, element);
        elements.set(selector, element);
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
      return true;
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

test("Cancel uses native confirmation and keeps danger action semantics", async () => {
  const h = await createHarness();
  setActiveUpload(h, { id: UPLOAD_A, state: "receiving", received: 4 });
  let confirmations = 0;
  h.context.confirm = () => {
    confirmations += 1;
    return false;
  };

  await h.run("handleCancelUpload()");
  assert.equal(confirmations, 1);
  assert.equal(h.fetchController.matching("DELETE", `/api/uploads/${UPLOAD_A}`).length, 0);
  assert.equal(stateOf(h).snapshotState, "receiving");
  assert.equal(stateOf(h).cancelHidden, false);
  assert.equal(stateOf(h).cancelLabel, "Cancel");

  h.context.confirm = () => {
    confirmations += 1;
    return true;
  };
  const cancellation = deferred();
  enqueue(h, "DELETE", `/api/uploads/${UPLOAD_A}`, cancellation.promise);
  const cancelPromise = h.run("handleCancelUpload()");
  await h.flush();
  assert.equal(stateOf(h).stateLabel, "Cancelling");
  assert.equal(stateOf(h).cancelHidden, true);

  cancellation.resolve(response(snapshot(UPLOAD_A, "cancelled", 4)));
  await cancelPromise;
  await h.flush();

  assert.equal(confirmations, 2);
  assert.equal(h.fetchController.matching("DELETE", `/api/uploads/${UPLOAD_A}`).length, 1);
  assert.equal(stateOf(h).snapshotState, "cancelled");
  assert.equal(stateOf(h).stateLabel, "Cancelled");
  assert.equal(stateOf(h).cancelHidden, true);
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
  await h.run("handleCancelUpload()");
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
