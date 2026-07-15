const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");

const APP_PATH = path.resolve(__dirname, "../src/framenest/adapters/api/web/app.js");
const APP_SOURCE = fs.readFileSync(APP_PATH, "utf8");
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
      document.activeElement = this;
    },
    setAttribute(name, value) {
      attributes.set(name, String(value));
    },
    removeAttribute(name) {
      attributes.delete(name);
    },
    hasAttribute(name) {
      return attributes.has(name);
    },
    getAttribute(name) {
      return attributes.get(name) || null;
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

function createDocument() {
  const elements = new Map();
  const document = {
    activeElement: null,
    querySelector(selector) {
      if (!elements.has(selector)) {
        elements.set(selector, createElement(document));
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
