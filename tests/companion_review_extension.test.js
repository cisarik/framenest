const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");

const REPO = path.resolve(__dirname, "..");
const companion = require(path.join(REPO, "extension/shared/messages.js"));
const workerSource = fs.readFileSync(
  path.join(REPO, "extension/background/service_worker.js"),
  "utf8"
);
const sidebarSource = fs.readFileSync(path.join(REPO, "extension/ui/sidebar.js"), "utf8");
const sidebarHtml = fs.readFileSync(path.join(REPO, "extension/ui/sidebar.html"), "utf8");
const sidebarCss = fs.readFileSync(path.join(REPO, "extension/ui/sidebar.css"), "utf8");
const reviewSource = fs.readFileSync(path.join(REPO, "extension/ui/review.js"), "utf8");
const reviewHtml = fs.readFileSync(path.join(REPO, "extension/ui/review.html"), "utf8");
const reviewCss = fs.readFileSync(path.join(REPO, "extension/ui/review.css"), "utf8");
const manifest = JSON.parse(
  fs.readFileSync(path.join(REPO, "extension/manifest.json"), "utf8")
);

const ORIGIN = "https://nuc-1.example.ts.net";
const MEDIA_A = "11111111-1111-4111-8111-111111111111";
const MEDIA_B = "22222222-2222-4222-8222-222222222222";
const RUN_NEW = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa";
const RUN_OLD = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb";
const CLAIM_ID = "cccccccc-cccc-4ccc-8ccc-cccccccccccc";
const ALARM = companion.REVIEW_INBOX.alarmName;

function extractNamedFunction(source, name) {
  const start = source.indexOf("function " + name);
  assert.ok(start >= 0, name);
  const bodyStart = source.indexOf("{", start);
  let depth = 0;
  let end = bodyStart;
  for (let index = bodyStart; index < source.length; index += 1) {
    if (source[index] === "{") {
      depth += 1;
    }
    if (source[index] === "}") {
      depth -= 1;
      if (depth === 0) {
        end = index + 1;
        break;
      }
    }
  }
  return source.slice(start, end);
}

function jsonResponse(status, body) {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: async () => body,
    headers: { get() { return null; } },
  };
}

function createChromeFake(options) {
  const storage = Object.assign({}, (options && options.storage) || {});
  const alarms = {};
  const state = {
    storage,
    alarms,
    badgeText: "",
    badgeWrites: [],
    fetchCalls: [],
    installed: [],
    startup: [],
    alarmListeners: [],
    inboxStatus: (options && options.inboxStatus) || 200,
    inboxBody:
      (options && options.inboxBody) || {
        items: [],
        unopened_count: 0,
        next_cursor: null,
      },
    inboxResponses: (options && options.inboxResponses) || null,
    inboxResponseIndex: 0,
    claimBody: (options && options.claimBody) || { state: "completed", assets: [] },
    detailStatus: (options && options.detailStatus) || 200,
    detailBody: (options && options.detailBody) || {},
    openedStatus: (options && options.openedStatus) || 200,
    openedBody: (options && options.openedBody) || { unopened: false },
    applyStatus: (options && options.applyStatus) || 200,
    applyBody:
      (options && options.applyBody) || {
        publication: { status: "not_ready", state: "unpublished", ready: false },
      },
  };

  function pickStorage(keys) {
    if (typeof keys === "string") {
      const out = {};
      out[keys] = storage[keys];
      return out;
    }
    if (Array.isArray(keys)) {
      const out = {};
      keys.forEach((key) => {
        out[key] = storage[key];
      });
      return out;
    }
    if (keys && typeof keys === "object") {
      const out = {};
      Object.keys(keys).forEach((key) => {
        out[key] = Object.prototype.hasOwnProperty.call(storage, key) ? storage[key] : keys[key];
      });
      return out;
    }
    return Object.assign({}, storage);
  }

  const chrome = {
    runtime: {
      getURL(rel) {
        return rel;
      },
      lastError: null,
      onInstalled: {
        addListener(fn) {
          state.installed.push(fn);
        },
      },
      onStartup: {
        addListener(fn) {
          state.startup.push(fn);
        },
      },
      onMessage: {
        addListener() {},
      },
      onConnect: {
        addListener() {},
      },
    },
    sidePanel: {
      setPanelBehavior() {
        return Promise.resolve();
      },
    },
    storage: {
      local: {
        get(keys) {
          return Promise.resolve(pickStorage(keys));
        },
        set(values) {
          Object.assign(storage, values);
          return Promise.resolve();
        },
        remove(keys) {
          (Array.isArray(keys) ? keys : [keys]).forEach((key) => {
            delete storage[key];
          });
          return Promise.resolve();
        },
      },
    },
    permissions: {
      request() {
        return Promise.resolve(true);
      },
      remove() {
        return Promise.resolve(true);
      },
      contains() {
        return Promise.resolve(false);
      },
    },
    alarms: {
      create(name, info) {
        alarms[name] = Object.assign({ name: name }, info || {});
        return Promise.resolve();
      },
      clear(name) {
        const existed = Object.prototype.hasOwnProperty.call(alarms, name);
        delete alarms[name];
        return Promise.resolve(existed);
      },
      onAlarm: {
        addListener(fn) {
          state.alarmListeners.push(fn);
        },
      },
    },
    action: {
      setBadgeText(detail) {
        const text = detail && typeof detail.text === "string" ? detail.text : "";
        state.badgeText = text;
        state.badgeWrites.push(text);
        return Promise.resolve();
      },
    },
  };

  async function fetchImpl(url, init) {
    state.fetchCalls.push({ url: String(url), init: init || {} });
    const href = String(url);
    if (href.indexOf("/api/x/requests/") !== -1) {
      return jsonResponse(200, state.claimBody);
    }
    if (/\/api\/companion\/review-inbox\/[^/?]+\/apply(?:\?|$)/.test(href)) {
      return jsonResponse(state.applyStatus, state.applyBody);
    }
    if (/\/api\/companion\/review-inbox\/[^/?]+\/opened(?:\?|$)/.test(href)) {
      return jsonResponse(state.openedStatus, state.openedBody);
    }
    if (/\/api\/companion\/review-inbox\/[^/?]+(?:\?|$)/.test(href)) {
      return jsonResponse(state.detailStatus, state.detailBody);
    }
    if (href.indexOf("/api/companion/review-inbox") !== -1) {
      if (Array.isArray(state.inboxResponses)) {
        const response = state.inboxResponses[state.inboxResponseIndex];
        state.inboxResponseIndex += 1;
        return jsonResponse(response.status, response.body);
      }
      return jsonResponse(state.inboxStatus, state.inboxBody);
    }
    return jsonResponse(404, {});
  }

  return { chrome, state, fetchImpl };
}

function loadWorker(options) {
  const fake = createChromeFake(options);
  const context = {
    chrome: fake.chrome,
    FrameNestCompanion: companion,
    fetch: fake.fetchImpl,
    importScripts() {},
    setTimeout,
    clearTimeout,
    AbortController,
    URL,
    URLSearchParams,
    JSON,
    Date,
    Math,
    Number,
    String,
    Boolean,
    Array,
    Object,
    Promise,
    console,
  };
  context.self = context;
  context.globalThis = context;
  vm.createContext(context);
  const source = workerSource.replace(/importScripts\([^)]+\);\s*/, "");
  vm.runInContext(source, context);
  return { context, state: fake.state, chrome: fake.chrome };
}

function loadReviewInbox(options) {
  const runtime =
    (options && options.runtime) ||
    {
      id: "sidebar-test",
      lastError: null,
      getURL(rel) {
        return "chrome-extension://abc/" + rel;
      },
      sendMessage(_message, callback) {
        callback({ ok: true });
      },
    };
  const context = {
    FrameNestCompanion: companion,
    document: {
      getElementById() {
        return null;
      },
    },
    chrome: { runtime },
    window: {},
    Object,
    Boolean,
    String,
    Number,
    Array,
    Date,
    Promise,
    setTimeout,
    clearTimeout,
    setInterval() {
      return 0;
    },
    clearInterval() {},
  };
  context.globalThis = context;
  vm.createContext(context);
  vm.runInContext(sidebarSource, context);
  return context.FrameNestReviewInbox;
}

function loadReviewOverlay(options) {
  const runtime =
    (options && options.runtime) ||
    {
      id: "review-test",
      lastError: null,
      getURL(rel) {
        return "chrome-extension://abc/" + rel;
      },
      sendMessage() {},
    };
  const context = {
    FrameNestCompanion: companion,
    document: {
      getElementById() {
        return null;
      },
    },
    chrome: { runtime },
    window: {},
    location: { hash: "", protocol: "chrome-extension:", origin: "chrome-extension://abc" },
    Object,
    Boolean,
    String,
    Number,
    Array,
    Date,
    Promise,
    URL,
    setTimeout,
    clearTimeout,
  };
  context.globalThis = context;
  vm.createContext(context);
  vm.runInContext(reviewSource, context);
  return context.FrameNestReviewOverlay;
}

function fakeListNode() {
  const nodes = [];
  const list = {
    childNodes: nodes,
    get firstChild() {
      return nodes[0] || null;
    },
    removeChild(node) {
      const index = nodes.indexOf(node);
      if (index >= 0) {
        nodes.splice(index, 1);
      }
      return node;
    },
    appendChild(node) {
      nodes.push(node);
      return node;
    },
    ownerDocument: {
      createElement(tag) {
        const childNodes = [];
        const attributes = {};
        const node = {
          tagName: String(tag).toUpperCase(),
          childNodes,
          attributes,
          dataset: {},
          setAttribute(name, value) {
            attributes[name] = String(value);
            if (name === "data-media-id") {
              this.dataset.mediaId = String(value);
            }
          },
          getAttribute(name) {
            return attributes[name] || null;
          },
          appendChild(child) {
            childNodes.push(child);
            return child;
          },
        };
        let text = "";
        Object.defineProperty(node, "textContent", {
          get() {
            if (childNodes.length) {
              return childNodes.map((child) => child.textContent || "").join("");
            }
            return text;
          },
          set(value) {
            text = value == null ? "" : String(value);
          },
        });
        return node;
      },
    },
  };
  return list;
}

function fakeReviewChromeNodes() {
  const attributes = { "aria-expanded": "false" };
  return {
    toggle: {
      disabled: false,
      setAttribute(name, value) {
        attributes[name] = String(value);
      },
      getAttribute(name) {
        return attributes[name] || null;
      },
    },
    history: { hidden: true },
    historyList: fakeListNode(),
    inbox: { hidden: true },
    inboxList: fakeListNode(),
  };
}

test("manifest adds alarms, keeps action, and does not add notifications or overlay WAR", () => {
  assert.deepEqual(manifest.permissions.sort(), ["alarms", "sidePanel", "storage"]);
  assert.equal((manifest.permissions || []).includes("alarms"), true);
  assert.equal((manifest.permissions || []).includes("notifications"), false);
  assert.equal((manifest.permissions || []).includes("tabs"), false);
  assert.equal("host_permissions" in manifest, false);
  assert.equal("externally_connectable" in manifest, false);
  assert.equal(typeof manifest.action, "object");
  assert.equal("default_popup" in manifest.action, false);
  assert.equal(manifest.action.default_title, "FrameNest companion");
  const war = manifest.web_accessible_resources[0].resources.slice().sort();
  assert.deepEqual(war, [
    "ui/picker.css",
    "ui/picker.html",
    "ui/picker.js",
    "ui/save.css",
    "ui/save.html",
    "ui/save.js",
  ]);
  assert.equal(war.includes("ui/sidebar.html"), false);
  assert.equal(war.includes("ui/sidebar.js"), false);
  assert.equal(war.includes("ui/review.html"), false);
  assert.equal(war.includes("ui/review.js"), false);
  assert.equal(war.includes("ui/review.css"), false);
  assert.equal(fs.existsSync(path.join(REPO, "extension/ui/review.html")), true);
  assert.equal(fs.existsSync(path.join(REPO, "extension/ui/review.js")), true);
  assert.equal(fs.existsSync(path.join(REPO, "extension/ui/review.css")), true);
  assert.doesNotMatch(reviewSource, /innerHTML/);
  assert.doesNotMatch(reviewSource, /\bfetch\s*\(/);
  assert.doesNotMatch(reviewSource, /postMessage\([^)]*,\s*["']\*["']/);
  assert.doesNotMatch(reviewSource, /chrome\.storage/);
});

test("review overlay protocol uses UUID pathFor and dropUnknown rejects unknown types", () => {
  assert.equal(companion.TYPES.REVIEW_INBOX, "review_inbox");
  assert.ok(
    companion.dropUnknown({
      v: companion.PROTOCOL,
      type: companion.TYPES.REVIEW_INBOX,
    })
  );
  assert.ok(
    companion.dropUnknown({
      v: companion.PROTOCOL,
      type: companion.TYPES.REVIEW_INBOX_DETAIL,
    })
  );
  assert.ok(
    companion.dropUnknown({
      v: companion.PROTOCOL,
      type: companion.TYPES.REVIEW_INBOX_OPENED,
    })
  );
  assert.ok(
    companion.dropUnknown({
      v: companion.PROTOCOL,
      type: companion.TYPES.REVIEW_INBOX_APPLY,
    })
  );
  assert.equal(companion.dropUnknown({ v: companion.PROTOCOL, type: "review_apply" }), null);
  assert.equal(companion.dropUnknown({ v: companion.PROTOCOL, type: "mark_opened" }), null);
  assert.equal(companion.dropUnknown({ v: companion.PROTOCOL, type: "review_opened" }), null);
  assert.equal(companion.pathFor("reviewInbox"), "/api/companion/review-inbox");
  assert.equal(
    companion.pathFor("reviewInbox", { url: "https://evil.example", claimId: "../x" }),
    "/api/companion/review-inbox"
  );
  assert.equal(companion.pathFor("https://evil.example"), null);
  assert.equal(
    companion.pathFor("reviewInboxDetail", { mediaId: MEDIA_A }),
    "/api/companion/review-inbox/" + MEDIA_A
  );
  assert.equal(
    companion.pathFor("reviewInboxOpened", { mediaId: MEDIA_A }),
    "/api/companion/review-inbox/" + MEDIA_A + "/opened"
  );
  assert.equal(
    companion.pathFor("reviewInboxApply", { mediaId: MEDIA_A }),
    "/api/companion/review-inbox/" + MEDIA_A + "/apply"
  );
  assert.equal(companion.pathFor("reviewInboxDetail", { mediaId: "not-a-uuid" }), null);
  assert.equal(companion.pathFor("reviewInboxOpened", { mediaId: "../" + MEDIA_A }), null);
  assert.equal(
    companion.pathFor("reviewInboxApply", { mediaId: "https://evil.example/" + MEDIA_A }),
    null
  );
  assert.equal(
    companion.pathFor("reviewInboxDetail", { mediaId: MEDIA_A, url: "https://evil.example" }),
    "/api/companion/review-inbox/" + MEDIA_A
  );
  assert.equal(companion.reviewInboxQuerySuffix(1), "?limit=1");
  assert.doesNotMatch(workerSource, /fetch\(payload\.url\)/);
  assert.doesNotMatch(workerSource, /fetch\(message\.url\)/);
  assert.match(workerSource, /fetchJson\("reviewInbox"/);
  assert.match(workerSource, /fetchJson\("reviewInboxDetail"/);
  assert.match(workerSource, /fetchJson\("reviewInboxOpened"/);
  assert.match(workerSource, /fetchJson\("reviewInboxApply"/);
  assert.doesNotMatch(workerSource, /setInterval/);
  assert.doesNotMatch(workerSource, /chrome\.notifications/);
  assert.doesNotMatch(extractNamedFunction(workerSource, "reviewInbox"), /method:\s*"POST"/);
});

test("shared extension-context classifier is exact and exposes one recovery copy", () => {
  const signature = companion.EXTENSION_CONTEXT_INVALIDATED_SIGNATURE;
  const copy = companion.EXTENSION_CONTEXT_RECOVERY_COPY;
  assert.equal(signature, "Extension context invalidated");
  assert.equal(copy, "FrameNest was reloaded. Refresh X and reopen the side panel.");
  assert.equal(companion.isExtensionContextInvalidated(null), true);
  assert.equal(companion.isExtensionContextInvalidated({ id: "" }), true);
  assert.equal(
    companion.isExtensionContextInvalidated(
      { id: "abc" },
      new Error("Unchecked runtime.lastError: Extension context invalidated.")
    ),
    true
  );
  assert.equal(
    companion.isExtensionContextInvalidated(
      { id: "abc" },
      { message: "Extension context invalidated while sending" }
    ),
    true
  );
  assert.equal(
    companion.isExtensionContextInvalidated({ id: "abc" }, { message: "Receiving end does not exist" }),
    false
  );
  assert.equal(
    companion.isExtensionContextInvalidated({ id: "abc" }, "Extension context invalidated"),
    false
  );
});

test("badge text uses unopened_count bounds and never a title", () => {
  assert.equal(companion.badgeTextForUnopenedCount(1), "1");
  assert.equal(companion.badgeTextForUnopenedCount(99), "99");
  assert.equal(companion.badgeTextForUnopenedCount(100), "99+");
  assert.equal(companion.badgeTextForUnopenedCount(0), "");
  assert.equal(companion.badgeTextForUnopenedCount(-4), "");
  assert.equal(companion.badgeTextForUnopenedCount("12"), "");
  assert.equal(
    companion.unopenedCountFromBody({
      unopened_count: 2,
      items: [{ title: "Secret title" }, { title: "Other" }, { title: "Third" }],
    }),
    2
  );
  assert.notEqual(
    companion.badgeTextForUnopenedCount(
      companion.unopenedCountFromBody({
        unopened_count: 2,
        items: [1, 2, 3, 4, 5],
      })
    ),
    "5"
  );
});

test("named one-minute alarm is created on configure and cleared on reset", async () => {
  const worker = loadWorker({});
  const configured = await worker.context.configureOrigin({ origin: ORIGIN });
  assert.equal(configured.ok, true);
  assert.ok(worker.state.alarms[ALARM]);
  assert.equal(worker.state.alarms[ALARM].periodInMinutes, 1);
  assert.equal(worker.state.alarms[ALARM].name, ALARM);
  worker.state.inboxBody = { items: [], unopened_count: 7, next_cursor: null };
  await worker.context.refreshReviewInboxBadge();
  assert.equal(worker.state.badgeText, "7");
  const reset = await worker.context.resetState();
  assert.equal(reset.ok, true);
  assert.equal(worker.state.alarms[ALARM], undefined);
  assert.equal(worker.state.badgeText, "");
  assert.equal(worker.state.storage[companion.REVIEW_INBOX.awaitingKey], undefined);
});

test("alarm is ensured on install and startup when a valid origin is stored", async () => {
  const worker = loadWorker({ storage: { frameNestOrigin: ORIGIN } });
  assert.ok(worker.state.installed.length >= 1);
  assert.ok(worker.state.startup.length >= 1);
  Object.keys(worker.state.alarms).forEach((name) => {
    delete worker.state.alarms[name];
  });
  worker.state.installed.forEach((fn) => fn());
  await worker.context.ensureReviewInboxAlarm();
  assert.ok(worker.state.alarms[ALARM]);
  assert.equal(worker.state.alarms[ALARM].periodInMinutes, 1);
  delete worker.state.alarms[ALARM];
  worker.state.startup.forEach((fn) => fn());
  await worker.context.ensureReviewInboxAlarm();
  assert.ok(worker.state.alarms[ALARM]);
});

test("badge refresh uses unopened_count, limit=1, and clears on 0, 403, and failure", async () => {
  const worker = loadWorker({ storage: { frameNestOrigin: ORIGIN } });
  worker.state.inboxBody = {
    items: [
      {
        media_id: MEDIA_A,
        title: "Leaked title",
        analysis_run_id: RUN_NEW,
        completed_at_ms: 1,
        unopened: true,
      },
      {
        media_id: MEDIA_B,
        title: "Second",
        analysis_run_id: RUN_OLD,
        completed_at_ms: 0,
        unopened: true,
      },
    ],
    unopened_count: 1,
    next_cursor: null,
  };
  await worker.context.refreshReviewInboxBadge();
  const badgeCall = worker.state.fetchCalls.find((call) =>
    call.url.indexOf("/api/companion/review-inbox") !== -1
  );
  assert.ok(badgeCall);
  assert.equal(badgeCall.url, ORIGIN + "/api/companion/review-inbox?limit=1");
  assert.equal(badgeCall.init.method || "GET", "GET");
  assert.equal(badgeCall.init.headers["X-FrameNest-Request"], "1");
  assert.equal(worker.state.badgeText, "1");
  assert.equal(worker.state.badgeText.indexOf("Leaked"), -1);

  worker.state.inboxBody = { items: [{ title: "x" }], unopened_count: 0, next_cursor: null };
  await worker.context.refreshReviewInboxBadge();
  assert.equal(worker.state.badgeText, "");

  worker.state.inboxBody = { items: [], unopened_count: 140, next_cursor: null };
  await worker.context.refreshReviewInboxBadge();
  assert.equal(worker.state.badgeText, "99+");

  worker.state.inboxStatus = 403;
  worker.state.inboxBody = {
    items: [{ title: "Should not badge" }],
    unopened_count: 9,
  };
  await worker.context.refreshReviewInboxBadge();
  assert.equal(worker.state.badgeText, "");

  worker.state.inboxStatus = 500;
  await worker.context.refreshReviewInboxBadge();
  assert.equal(worker.state.badgeText, "");
});

test("alarm handler refreshes the badge and ignores other alarm names", async () => {
  const worker = loadWorker({ storage: { frameNestOrigin: ORIGIN } });
  assert.equal(worker.state.alarmListeners.length, 1);
  worker.state.inboxBody = { items: [], unopened_count: 4, next_cursor: null };
  worker.state.badgeText = "stay";
  worker.state.alarmListeners[0]({ name: "other.alarm" });
  await new Promise((resolve) => setTimeout(resolve, 20));
  assert.equal(worker.state.badgeText, "stay");
  worker.state.alarmListeners[0]({ name: ALARM });
  await new Promise((resolve) => setTimeout(resolve, 20));
  assert.equal(worker.state.badgeText, "4");
});

test("REVIEW_INBOX hides titles on 403 and does not fetch caller URLs", async () => {
  const worker = loadWorker({ storage: { frameNestOrigin: ORIGIN } });
  worker.state.inboxBody = {
    items: [
      {
        media_id: MEDIA_A,
        title: "Admin title",
        analysis_run_id: RUN_NEW,
        completed_at_ms: 10,
        unopened: true,
      },
    ],
    unopened_count: 3,
    next_cursor: null,
  };
  const listed = await worker.context.handle({
    v: companion.PROTOCOL,
    type: companion.TYPES.REVIEW_INBOX,
    payload: { url: "https://evil.example/steal" },
  });
  assert.equal(listed.ok, true);
  assert.equal(listed.forbidden, false);
  assert.equal(listed.unopened_count, 3);
  assert.equal(listed.items.length, 1);
  assert.equal(listed.items[0].title, "Admin title");
  const listCall = worker.state.fetchCalls[worker.state.fetchCalls.length - 1];
  assert.equal(listCall.url, ORIGIN + "/api/companion/review-inbox?limit=100");
  assert.equal(listCall.url.indexOf("evil.example"), -1);

  worker.state.inboxStatus = 403;
  worker.state.inboxBody = {
    items: [{ title: "Ordinary must not see this" }],
    unopened_count: 8,
  };
  const denied = await worker.context.reviewInbox();
  assert.equal(denied.ok, false);
  assert.equal(denied.forbidden, true);
  assert.equal(Array.isArray(denied.items), true);
  assert.equal(denied.items.length, 0);
  assert.equal(denied.unopened_count, 0);
  assert.equal(JSON.stringify(denied).indexOf("Ordinary must not see this"), -1);
  assert.equal(worker.state.badgeText, "");
});

test("REVIEW_INBOX aggregates encoded cursor pages in server order", async () => {
  const cursor = "next page +/&=";
  const worker = loadWorker({
    storage: { frameNestOrigin: ORIGIN },
    inboxResponses: [
      {
        status: 200,
        body: {
          items: [
            {
              media_id: MEDIA_A,
              title: "Newest",
              analysis_run_id: RUN_NEW,
              completed_at_ms: 20,
              unopened: true,
            },
          ],
          unopened_count: 1,
          next_cursor: cursor,
        },
      },
      {
        status: 200,
        body: {
          items: [
            {
              media_id: MEDIA_B,
              title: "Older",
              analysis_run_id: RUN_OLD,
              completed_at_ms: 10,
              unopened: false,
            },
          ],
          unopened_count: 1,
          next_cursor: null,
        },
      },
    ],
  });
  const result = await worker.context.reviewInbox();
  assert.equal(result.ok, true);
  assert.equal(result.unopened_count, 1);
  assert.deepEqual(
    Array.from(result.items, (item) => item.title),
    ["Newest", "Older"]
  );
  assert.equal(worker.state.fetchCalls.length, 2);
  const first = new URL(worker.state.fetchCalls[0].url);
  const second = new URL(worker.state.fetchCalls[1].url);
  assert.equal(first.searchParams.get("limit"), "100");
  assert.equal(first.searchParams.has("cursor"), false);
  assert.equal(second.searchParams.get("limit"), "100");
  assert.equal(second.searchParams.get("cursor"), cursor);
  assert.equal(worker.state.badgeText, "1");
});

test("REVIEW_INBOX rejects cursor cycles and later-page failures without partial titles", async () => {
  const firstPage = {
    items: [
      {
        media_id: MEDIA_A,
        title: "Must not escape",
        analysis_run_id: RUN_NEW,
        completed_at_ms: 20,
        unopened: true,
      },
    ],
    unopened_count: 1,
    next_cursor: "repeat",
  };
  const cycleWorker = loadWorker({
    storage: { frameNestOrigin: ORIGIN },
    inboxResponses: [
      { status: 200, body: firstPage },
      {
        status: 200,
        body: { items: [], unopened_count: 1, next_cursor: "repeat" },
      },
    ],
  });
  cycleWorker.state.badgeText = "9";
  const cycle = await cycleWorker.context.reviewInbox();
  assert.equal(cycle.ok, false);
  assert.equal(cycle.error, "cursor_cycle");
  assert.deepEqual(Array.from(cycle.items), []);
  assert.equal(JSON.stringify(cycle).includes("Must not escape"), false);
  assert.equal(cycleWorker.state.fetchCalls.length, 2);
  assert.equal(cycleWorker.state.badgeText, "");

  const failedWorker = loadWorker({
    storage: { frameNestOrigin: ORIGIN },
    inboxResponses: [
      { status: 200, body: firstPage },
      { status: 500, body: { items: [{ title: "also private" }] } },
    ],
  });
  failedWorker.state.badgeText = "8";
  const failed = await failedWorker.context.reviewInbox();
  assert.equal(failed.ok, false);
  assert.equal(failed.status, 500);
  assert.deepEqual(Array.from(failed.items), []);
  assert.equal(JSON.stringify(failed).includes("Must not escape"), false);
  assert.equal(failedWorker.state.badgeText, "");
});

test("awaiting-analysis stores media UUIDs for 30 minutes and does not change badge math", async () => {
  const worker = loadWorker({ storage: { frameNestOrigin: ORIGIN } });
  const now = Date.now();
  worker.state.claimBody = {
    state: "completed",
    x_post_id: "123456789",
    assets: [
      { media_id: MEDIA_A, state: "cataloged", title: "must not persist" },
      { media_id: "not-a-uuid", state: "cataloged" },
    ],
  };
  const snapshot = await worker.context.pollClaim({ claimId: CLAIM_ID });
  assert.equal(snapshot.ok, true);
  const awaiting = worker.state.storage[companion.REVIEW_INBOX.awaitingKey];
  assert.equal(awaiting.length, 1);
  assert.equal(awaiting[0].media_id, MEDIA_A);
  assert.equal("title" in awaiting[0], false);
  assert.ok(awaiting[0].expires_at_ms >= now + companion.REVIEW_INBOX.awaitingMs - 50);
  assert.ok(awaiting[0].expires_at_ms <= now + companion.REVIEW_INBOX.awaitingMs + 2000);

  worker.state.inboxBody = {
    items: [
      {
        media_id: MEDIA_B,
        title: "Other item",
        analysis_run_id: RUN_NEW,
        completed_at_ms: 1,
        unopened: true,
      },
    ],
    unopened_count: 0,
    next_cursor: null,
  };
  const stillHint = await worker.context.reviewInbox();
  assert.equal(stillHint.unopened_count, 0);
  assert.equal(worker.state.badgeText, "");
  assert.equal(stillHint.awaiting.length, 1);
  assert.equal(stillHint.awaiting[0].media_id, MEDIA_A);

  worker.state.inboxBody.items[0].media_id = MEDIA_A;
  const pruned = await worker.context.reviewInbox();
  assert.equal(pruned.awaiting.length, 0);
  assert.equal(worker.state.badgeText, "");

  const expired = companion.normalizeAwaitingRecords(
    [{ media_id: MEDIA_B, expires_at_ms: 1, title: "nope" }],
    Date.now()
  );
  assert.deepEqual(expired, []);
});

test("title-bar history and unread chrome have the accepted DOM, ARIA, and status contract", () => {
  const titleBarAt = sidebarHtml.indexOf('class="title-bar"');
  const titleBarEnd = sidebarHtml.indexOf("</div>", titleBarAt);
  const toggleAt = sidebarHtml.indexOf('id="review-history-toggle"');
  const wordmarkAt = sidebarHtml.indexOf('class="title-bar__wordmark"');
  const settingsAt = sidebarHtml.indexOf('id="settings-open"');
  const actionAt = sidebarHtml.indexOf('id="chrome-action"');
  const historyAt = sidebarHtml.indexOf('id="review-history"');
  const statusAt = sidebarHtml.indexOf('id="shell-status"');
  const inboxAt = sidebarHtml.indexOf('id="review-inbox"');
  const frameAt = sidebarHtml.indexOf('id="frame"');
  assert.ok(titleBarAt >= 0 && toggleAt > titleBarAt && toggleAt < titleBarEnd);
  assert.ok(wordmarkAt > toggleAt && settingsAt > wordmarkAt && actionAt > settingsAt);
  assert.ok(historyAt > titleBarEnd && statusAt > historyAt && inboxAt > statusAt && frameAt > inboxAt);
  assert.match(
    sidebarHtml,
    /id="review-history-toggle"[\s\S]*?type="button"[\s\S]*?aria-label="Analysis history"[\s\S]*?aria-expanded="false"[\s\S]*?aria-controls="review-history"[\s\S]*?disabled/
  );
  assert.match(sidebarHtml, /id="review-history-list"[^>]+aria-label="Analysis history"/);
  assert.match(sidebarHtml, /id="review-inbox-list"[^>]+aria-label="Unread analyses"/);
  assert.doesNotMatch(sidebarHtml, />\s*Review inbox\s*</);
  assert.doesNotMatch(sidebarHtml, /No analyzed items\./);
  assert.doesNotMatch(sidebarHtml, /Awaiting analysis/);
  assert.match(sidebarHtml, /id="review-dialog"/);
  assert.match(sidebarHtml, /id="review-frame"/);
  assert.match(sidebarSource, /ui\/review\.html/);
  assert.doesNotMatch(sidebarSource, /explicitCollapsedKey|seenRunIdKey/);
  assert.doesNotMatch(sidebarSource, /setText\(shellStatus,\s*"Connected"/);
  assert.match(sidebarSource, /Connect FrameNest in Settings/);
  assert.match(sidebarSource, /setText\(shellStatus, "Cleared"\)/);
  assert.match(sidebarSource, /setText\(shellStatus, "Attached"\)/);
  assert.doesNotMatch(extractNamedFunction(sidebarSource, "openReviewOverlay"), /clearFrame/);
  assert.doesNotMatch(extractNamedFunction(sidebarSource, "closeReviewOverlay"), /clearFrame/);
  assert.match(sidebarCss, /\.title-bar__history-toggle\s*{[\s\S]*?position:\s*absolute;[\s\S]*?inset:\s*0;/);
  assert.match(sidebarCss, /\.title-bar__wordmark\s*{[\s\S]*?pointer-events:\s*none/);
  assert.match(sidebarCss, /\.title-bar__settings\s*{[\s\S]*?z-index:\s*2/);
  assert.match(sidebarCss, /\.title-bar__action\s*{[\s\S]*?z-index:\s*2/);
  assert.match(sidebarCss, /\.shell-status:empty\s*{[\s\S]*?display:\s*none/);
  assert.match(sidebarCss, /\.review-list:empty\s*{[\s\S]*?display:\s*none/);
  assert.match(sidebarCss, /max-height:\s*8\.5rem/);
  assert.match(sidebarCss, /overflow-y:\s*auto/);
  assert.doesNotMatch(extractNamedFunction(sidebarSource, "hideInboxSection"), /clearFrame/);
  assert.doesNotMatch(extractNamedFunction(sidebarSource, "hideInboxSection"), /frame/);
  assert.doesNotMatch(extractNamedFunction(sidebarSource, "setReviewHistoryExpanded"), /frame/);
  assert.doesNotMatch(extractNamedFunction(sidebarSource, "renderReviewCollections"), /frame/);
  assert.doesNotMatch(extractNamedFunction(sidebarSource, "hideReviewCollections"), /frame/);
  assert.doesNotMatch(sidebarSource, /innerHTML/);
  assert.doesNotMatch(sidebarSource, /\bfetch\s*\(/);
  assert.doesNotMatch(sidebarSource, /addEventListener\(["'](?:hover|mouseover|mouseenter|focus|focusin)["']/);
  assert.match(sidebarSource, /setInterval/);
  assert.match(sidebarSource, /visibilitychange/);
  assert.match(sidebarSource, /TYPES\.REVIEW_INBOX/);
  assert.match(sidebarSource, /onReviewListClick\(event, reviewHistoryList\)/);
  assert.match(sidebarSource, /onReviewListClick\(event, reviewInboxList\)/);
});

test("history keeps all rows while unread filters exact true and chrome never mutates the iframe", () => {
  const inbox = loadReviewInbox();
  assert.equal(inbox.POLL_MS, 15000);
  const items = [
    {
      media_id: MEDIA_A,
      title: "<img src=x onerror=alert(1)>",
      analysis_run_id: RUN_NEW,
      completed_at_ms: 9,
      unopened: true,
    },
    {
      media_id: MEDIA_B,
      title: "Older",
      analysis_run_id: RUN_OLD,
      completed_at_ms: 1,
      unopened: false,
    },
  ];
  assert.equal(inbox.unreadItems(items).length, 1);
  assert.equal(inbox.unreadItems(items)[0].analysis_run_id, RUN_NEW);
  const nodes = fakeReviewChromeNodes();
  const hostFrame = { hidden: false, src: ORIGIN };
  const result = inbox.renderCollections(nodes, items);
  assert.deepEqual(
    Array.from(result.historyItems, (item) => item.analysis_run_id),
    [RUN_NEW, RUN_OLD]
  );
  assert.deepEqual(Array.from(result.unreadItems, (item) => item.analysis_run_id), [RUN_NEW]);
  assert.equal(nodes.historyList.childNodes.length, 2);
  assert.equal(nodes.inboxList.childNodes.length, 1);
  assert.equal(nodes.historyList.childNodes[0].textContent, "<img src=x onerror=alert(1)>");
  assert.equal(nodes.inboxList.childNodes[0].textContent, "<img src=x onerror=alert(1)>");
  assert.equal(nodes.historyList.childNodes[0].tagName, "LI");
  assert.equal(nodes.historyList.childNodes[0].childNodes[0].tagName, "BUTTON");
  assert.equal(
    nodes.historyList.childNodes[0].childNodes[0].getAttribute("data-media-id"),
    MEDIA_A
  );
  assert.equal(inbox.setHistoryExpanded(nodes.toggle, nodes.history, true), true);
  assert.equal(nodes.toggle.getAttribute("aria-expanded"), "true");
  assert.equal(nodes.history.hidden, false);
  assert.equal(inbox.setHistoryExpanded(nodes.toggle, nodes.history, false), false);
  assert.equal(nodes.history.hidden, true);

  const openedItems = items.map((item) => Object.assign({}, item, { unopened: false }));
  inbox.renderCollections(nodes, openedItems);
  assert.equal(nodes.historyList.childNodes.length, 2);
  assert.equal(nodes.inboxList.childNodes.length, 0);
  assert.equal(nodes.inbox.hidden, true);
  inbox.hideCollections(nodes, true);
  assert.equal(nodes.toggle.disabled, true);
  assert.equal(nodes.toggle.getAttribute("aria-expanded"), "false");
  assert.equal(nodes.history.hidden, true);
  assert.equal(nodes.historyList.childNodes.length, 0);
  assert.equal(nodes.inboxList.childNodes.length, 0);
  assert.equal(inbox.setHistoryExpanded(nodes.toggle, nodes.history, true), false);
  assert.equal(hostFrame.hidden, false);
  assert.equal(hostFrame.src, ORIGIN);
  assert.doesNotMatch(extractNamedFunction(sidebarSource, "renderReviewInboxList"), /innerHTML/);
});

test("cataloged asset helper keeps only UUID media ids", () => {
  assert.deepEqual(
    companion.catalogedMediaIdsFromAssets([
      { media_id: MEDIA_A, filename: "secret.mp4" },
      { media_id: MEDIA_A },
      { media_id: "https://evil.example" },
      { title: "no id" },
    ]),
    [MEDIA_A]
  );
  const pruned = companion.pruneAwaitingRecords(
    [
      { media_id: MEDIA_A, expires_at_ms: Date.now() + 60000 },
      { media_id: MEDIA_B, expires_at_ms: Date.now() + 60000 },
    ],
    [MEDIA_A],
    Date.now()
  );
  assert.equal(pruned.length, 1);
  assert.equal(pruned[0].media_id, MEDIA_B);
});

test("worker GET detail and POST opened/apply send W04 JSON only", async () => {
  const worker = loadWorker({ storage: { frameNestOrigin: ORIGIN } });
  worker.state.detailBody = {
    suggestions: [{ analysis_run_id: RUN_NEW, title: "Secret title" }],
    canonical: { display_title: "Now" },
  };
  const detail = await worker.context.handle({
    v: companion.PROTOCOL,
    type: companion.TYPES.REVIEW_INBOX_DETAIL,
    payload: { mediaId: MEDIA_A, url: "https://evil.example/steal" },
  });
  assert.equal(detail.ok, true);
  assert.equal(detail.forbidden, false);
  const detailCall = worker.state.fetchCalls[worker.state.fetchCalls.length - 1];
  assert.equal(detailCall.url, ORIGIN + "/api/companion/review-inbox/" + MEDIA_A);
  assert.equal((detailCall.init.method || "GET").toUpperCase(), "GET");
  assert.equal(detailCall.init.headers["X-FrameNest-Request"], "1");
  assert.equal(detailCall.url.indexOf("evil.example"), -1);

  const opened = await worker.context.handle({
    v: companion.PROTOCOL,
    type: companion.TYPES.REVIEW_INBOX_OPENED,
    payload: { mediaId: MEDIA_A, analysis_run_id: RUN_NEW, title: "ignore me" },
  });
  assert.equal(opened.ok, true);
  const openedCall = worker.state.fetchCalls[worker.state.fetchCalls.length - 1];
  assert.equal(openedCall.url, ORIGIN + "/api/companion/review-inbox/" + MEDIA_A + "/opened");
  assert.equal(openedCall.init.method, "POST");
  assert.deepEqual(JSON.parse(openedCall.init.body), { analysis_run_id: RUN_NEW });
  assert.equal("title" in JSON.parse(openedCall.init.body), false);

  const apply = await worker.context.handle({
    v: companion.PROTOCOL,
    type: companion.TYPES.REVIEW_INBOX_APPLY,
    payload: {
      mediaId: MEDIA_A,
      analysis_run_id: RUN_NEW,
      fields: ["display_title", "tags"],
      tag_keys: ["alpha", "beta"],
      display_title: "client title",
      description: "client description",
      url: "https://evil.example/apply",
    },
  });
  assert.equal(apply.ok, true);
  const applyCall = worker.state.fetchCalls[worker.state.fetchCalls.length - 1];
  assert.equal(applyCall.url, ORIGIN + "/api/companion/review-inbox/" + MEDIA_A + "/apply");
  assert.equal(applyCall.init.method, "POST");
  assert.equal(applyCall.init.headers["X-FrameNest-Request"], "1");
  const posted = JSON.parse(applyCall.init.body);
  assert.deepEqual(Object.keys(posted).sort(), ["analysis_run_id", "fields", "tag_keys"]);
  assert.deepEqual(posted, {
    analysis_run_id: RUN_NEW,
    fields: ["display_title", "tags"],
    tag_keys: ["alpha", "beta"],
  });
  assert.equal(applyCall.url.indexOf("evil.example"), -1);

  const rejected = await worker.context.handle({
    v: companion.PROTOCOL,
    type: companion.TYPES.REVIEW_INBOX_APPLY,
    payload: { mediaId: "not-a-uuid", analysis_run_id: RUN_NEW, fields: ["display_title"] },
  });
  assert.equal(rejected.ok, false);
  assert.equal(rejected.error, "invalid_apply");
});

test("opening overlay keeps #frame mounted and uses exact extension origin", () => {
  const inbox = loadReviewInbox();
  const hostFrame = { hidden: false, src: ORIGIN, removed: false };
  const dialog = {
    open: false,
    show() {
      this.open = true;
    },
    close() {
      this.open = false;
    },
    setAttribute() {},
    removeAttribute() {},
  };
  const overlayFrame = {
    attrs: {},
    setAttribute(name, value) {
      this.attrs[name] = value;
    },
    removeAttribute(name) {
      delete this.attrs[name];
    },
  };
  assert.equal(inbox.openOverlay(MEDIA_A, dialog, overlayFrame), true);
  assert.equal(dialog.open, true);
  assert.match(overlayFrame.attrs.src, /ui\/review\.html#media=/);
  assert.ok(String(overlayFrame.attrs.src).indexOf(MEDIA_A) !== -1);
  assert.equal(hostFrame.hidden, false);
  assert.equal(hostFrame.src, ORIGIN);
  inbox.closeOverlay(dialog, overlayFrame);
  assert.equal(dialog.open, false);
  assert.equal("src" in overlayFrame.attrs, false);
  assert.equal(hostFrame.hidden, false);
  const accepted = companion.acceptReviewOverlayMessage(
    {
      source: overlayFrame,
      origin: "chrome-extension://abc",
      data: { v: companion.REVIEW_OVERLAY.protocol, type: companion.REVIEW_OVERLAY.types.INBOX_REFRESH },
    },
    overlayFrame,
    "chrome-extension://abc"
  );
  assert.equal(accepted.type, companion.REVIEW_OVERLAY.types.INBOX_REFRESH);
  assert.equal(
    companion.acceptReviewOverlayMessage(
      {
        source: overlayFrame,
        origin: "chrome-extension://abc",
        data: { v: companion.REVIEW_OVERLAY.protocol, type: companion.REVIEW_OVERLAY.types.INBOX_REFRESH },
      },
      overlayFrame,
      "*"
    ),
    null
  );
  assert.doesNotMatch(sidebarSource, /postMessage\([^)]*,\s*["']\*["']/);
  assert.doesNotMatch(reviewSource, /postMessage\([^)]*,\s*["']\*["']/);
});

test("sidebar and review requests recover only invalidated contexts and disable affected UI", async () => {
  const invalidLastError = {
    id: "sidebar-test",
    lastError: { message: "Extension context invalidated." },
    getURL(rel) {
      return "chrome-extension://abc/" + rel;
    },
    sendMessage(_message, callback) {
      callback(undefined);
    },
  };
  const staleSidebar = loadReviewInbox({ runtime: invalidLastError });
  const staleResult = await staleSidebar.request(companion.TYPES.REVIEW_INBOX, {});
  assert.equal(staleResult.ok, false);
  assert.equal(staleResult.stale, true);
  assert.equal(staleResult.error, "extension_context_invalidated");

  const ordinarySidebar = loadReviewInbox({
    runtime: {
      id: "sidebar-test",
      lastError: { message: "Receiving end does not exist" },
      getURL(rel) {
        return "chrome-extension://abc/" + rel;
      },
      sendMessage(_message, callback) {
        callback(undefined);
      },
    },
  });
  const ordinary = await ordinarySidebar.request(companion.TYPES.REVIEW_INBOX, {});
  assert.equal(ordinary.error, "extension_unavailable");
  assert.equal(ordinary.stale, undefined);

  const invalidUrlSidebar = loadReviewInbox({
    runtime: {
      id: "sidebar-test",
      lastError: null,
      getURL() {
        throw new Error("Extension context invalidated.");
      },
      sendMessage() {},
    },
  });
  assert.equal(invalidUrlSidebar.overlayUrl(MEDIA_A), "");
  const unrelatedUrlSidebar = loadReviewInbox({
    runtime: {
      id: "sidebar-test",
      lastError: null,
      getURL() {
        throw new Error("unrelated runtime failure");
      },
      sendMessage() {},
    },
  });
  assert.throws(() => unrelatedUrlSidebar.overlayUrl(MEDIA_A), /unrelated runtime failure/);

  const staleReview = loadReviewOverlay({
    runtime: {
      id: "review-test",
      lastError: null,
      getURL(rel) {
        return "chrome-extension://abc/" + rel;
      },
      sendMessage() {
        throw new Error("Extension context invalidated.");
      },
    },
  });
  const reviewResult = await staleReview.request(companion.TYPES.REVIEW_INBOX_DETAIL, {
    mediaId: MEDIA_A,
  });
  assert.equal(reviewResult.stale, true);
  assert.equal(reviewResult.error, "extension_context_invalidated");

  const unrelatedReview = loadReviewOverlay({
    runtime: {
      id: "review-test",
      lastError: null,
      getURL(rel) {
        return "chrome-extension://abc/" + rel;
      },
      sendMessage() {
        throw new Error("unrelated review runtime failure");
      },
    },
  });
  await assert.rejects(
    unrelatedReview.request(companion.TYPES.REVIEW_INBOX_DETAIL, { mediaId: MEDIA_A }),
    /unrelated review runtime failure/
  );

  let state = null;
  const controller = loadReviewOverlay().createController({
    request: async () => ({
      ok: false,
      error: "extension_context_invalidated",
      stale: true,
    }),
    notifyParent() {},
    render(next) {
      state = next;
    },
  });
  await controller.open(MEDIA_A);
  assert.equal(state.runtimeStale, true);
  assert.equal(state.lastError, companion.EXTENSION_CONTEXT_RECOVERY_COPY);
  assert.equal(state.saveEnabled, false);
  controller.setField("display_title", true);
  assert.equal(state.fields.display_title, false);

  assert.match(sidebarSource, /handleRuntimeStale[\s\S]*chromeAction\.disabled = true/);
  assert.match(sidebarSource, /handleRuntimeStale[\s\S]*settingsConnect\.disabled = true/);
  assert.match(reviewSource, /handleRuntimeStale[\s\S]*saveButton\.disabled = true/);
  assert.doesNotMatch(sidebarSource, /catch\s*\{\s*return\s+"";\s*\}/);
  assert.doesNotMatch(reviewSource, /catch\s*\{\s*return\s+"";\s*\}/);
});

test("dropdown label, field gates, chip removal, stay-open apply, and 403 wipe", async () => {
  const overlay = loadReviewOverlay();
  const label = overlay.formatRunLabel({
    completed_at_ms: Date.UTC(2026, 7, 23, 12, 0, 0),
    model_id: "meta/llama-test",
    title: "Suggested title",
  });
  assert.match(label, /meta\/llama-test/);
  assert.match(label, /Suggested title/);
  assert.match(label, / · /);
  assert.equal(overlay.parseMediaHash("#media=" + MEDIA_A), MEDIA_A);
  assert.equal(overlay.parseMediaHash("#url=https://x.com/a/status/1"), null);
  const tags = [
    { status: "mapped", key: "alpha", display_name: "Alpha", value: "Alpha" },
    { status: "unknown", key: null, value: "Nope", status: "unknown" },
    { status: "mapped", key: "beta", display_name: "Beta", value: "Beta" },
  ];
  const remaining = overlay.remainingMappedKeys(tags, { beta: true });
  assert.equal(remaining.length, 1);
  assert.equal(remaining[0], "alpha");
  assert.equal(overlay.tagsCanBeChecked(0), false);
  assert.equal(overlay.saveEnabled({ display_title: false, tags: false, description: false }, 2), false);
  assert.equal(overlay.saveEnabled({ display_title: true, tags: false, description: false }, 0), true);

  const calls = [];
  let lastState = null;
  const session = overlay.createController({
    request: async (type, payload) => {
      calls.push({ type, payload });
      if (type === companion.TYPES.REVIEW_INBOX_DETAIL) {
        return {
          ok: true,
          status: 200,
          forbidden: false,
          body: {
            suggestions: [
              {
                analysis_run_id: RUN_NEW,
                completed_at_ms: 2,
                model_id: "meta/llama-test",
                title: "New title",
                description: "New description",
                tags: tags,
              },
              {
                analysis_run_id: RUN_OLD,
                completed_at_ms: 1,
                model_id: "meta/llama-old",
                title: "Old title",
                description: "Old description",
                tags: tags,
              },
            ],
            canonical: { display_title: "Current", field_sources: {} },
            publication: { state: "unpublished", ready: false, missing_fields: ["display_title"] },
          },
        };
      }
      if (type === companion.TYPES.REVIEW_INBOX_OPENED) {
        return { ok: true, status: 200, forbidden: false, body: {} };
      }
      if (type === companion.TYPES.REVIEW_INBOX_APPLY) {
        if (payload && payload.fail) {
          return { ok: false, status: 409, forbidden: false, error: "conflict" };
        }
        return {
          ok: true,
          status: 200,
          forbidden: false,
          body: {
            canonical: { display_title: "Applied", field_sources: { display_title: { analysis_run_id: RUN_NEW } } },
            publication: { status: "not_ready", state: "unpublished", ready: false },
          },
        };
      }
      return { ok: false, error: "unexpected" };
    },
    notifyParent() {},
    render(state) {
      lastState = state;
    },
  });

  await session.open(MEDIA_A);
  assert.equal(lastState.overlayOpen, true);
  assert.equal(lastState.runId, RUN_NEW);
  assert.equal(
    calls.filter((call) => call.type === companion.TYPES.REVIEW_INBOX_OPENED).length,
    1
  );
  assert.equal(lastState.saveEnabled, false);
  session.setField("display_title", true);
  assert.equal(lastState.saveEnabled, true);
  session.removeChip("alpha");
  session.removeChip("beta");
  session.setField("tags", true);
  assert.equal(lastState.fields.tags, false);
  assert.equal(lastState.tagsDisabled, true);

  session.setField("display_title", true);
  const success = await session.save();
  assert.equal(success.ok, true);
  assert.equal(
    calls.filter((call) => call.type === companion.TYPES.REVIEW_INBOX_OPENED).length,
    1
  );
  const applyCall = calls.filter((call) => call.type === companion.TYPES.REVIEW_INBOX_APPLY).pop();
  assert.deepEqual(applyCall.payload.fields, ["display_title"]);
  assert.equal(applyCall.payload.display_title, undefined);
  assert.equal(applyCall.payload.description, undefined);
  assert.equal(lastState.overlayOpen, true);
  assert.equal(lastState.fields.display_title, false);
  assert.equal(lastState.canonical.display_title, "Applied");
  assert.equal(lastState.publication.status, "not_ready");

  session.setField("display_title", true);
  const previousCalls = calls.length;
  await session.selectRun(RUN_OLD);
  assert.equal(lastState.fields.display_title, false);
  assert.equal(lastState.runId, RUN_OLD);
  const afterSwitch = calls.slice(previousCalls);
  assert.equal(afterSwitch.some((call) => call.type === companion.TYPES.REVIEW_INBOX_OPENED), true);
  assert.equal(afterSwitch.some((call) => call.type === companion.TYPES.REVIEW_INBOX_APPLY), false);

  const forbiddenSession = overlay.createController({
    request: async () => ({ ok: false, status: 403, forbidden: true, error: "http_403" }),
    notifyParent() {},
    render(state) {
      lastState = state;
    },
  });
  await forbiddenSession.open(MEDIA_A);
  assert.equal(lastState.overlayOpen, false);
  assert.equal(lastState.suggestion, null);
  assert.equal(lastState.lastError, "");
  assert.doesNotMatch(reviewHtml, /<input[^>]+id="suggestion-title"/);
  assert.match(reviewHtml, /History \(run completion time\)/);
  assert.match(reviewCss, /--background/);
  assert.match(reviewCss, /#00ff41/);
});

test("Review Save retries opened after failure and blocks Apply until opened succeeds", async () => {
  const overlay = loadReviewOverlay();
  const calls = [];
  let openedAttempts = 0;
  let lastState = null;
  const session = overlay.createController({
    request: async (type, payload) => {
      calls.push({ type, payload });
      if (type === companion.TYPES.REVIEW_INBOX_DETAIL) {
        return {
          ok: true,
          status: 200,
          forbidden: false,
          body: {
            suggestions: [
              {
                analysis_run_id: RUN_NEW,
                completed_at_ms: 2,
                model_id: "meta/llama-test",
                title: "New title",
                description: "New description",
                tags: [],
              },
            ],
            canonical: { display_title: "Current", field_sources: {} },
            publication: { state: "unpublished", ready: false, missing_fields: [] },
          },
        };
      }
      if (type === companion.TYPES.REVIEW_INBOX_OPENED) {
        openedAttempts += 1;
        if (openedAttempts <= 2) {
          return { ok: false, status: 500, forbidden: false, error: "opened_failed" };
        }
        return { ok: true, status: 200, forbidden: false, body: { unopened: false } };
      }
      if (type === companion.TYPES.REVIEW_INBOX_APPLY) {
        return {
          ok: true,
          status: 200,
          forbidden: false,
          body: {
            canonical: { display_title: "Applied", field_sources: {} },
            publication: { state: "unpublished", ready: false, status: "not_ready" },
          },
        };
      }
      return { ok: false, error: "unexpected" };
    },
    notifyParent() {},
    render(state) {
      lastState = state;
    },
  });

  await session.open(MEDIA_A);
  assert.equal(openedAttempts, 1);
  session.setField("display_title", true);
  const blocked = await session.save();
  assert.equal(blocked.ok, false);
  assert.equal(openedAttempts, 2);
  assert.equal(
    calls.filter((call) => call.type === companion.TYPES.REVIEW_INBOX_APPLY).length,
    0
  );
  assert.equal(lastState.fields.display_title, true);
  assert.equal(lastState.lastError, "This review could not be marked opened.");

  const applied = await session.save();
  assert.equal(applied.ok, true);
  assert.equal(openedAttempts, 3);
  assert.equal(
    calls.filter((call) => call.type === companion.TYPES.REVIEW_INBOX_APPLY).length,
    1
  );
  assert.equal(lastState.fields.display_title, false);
  assert.equal(lastState.canonical.display_title, "Applied");
});
