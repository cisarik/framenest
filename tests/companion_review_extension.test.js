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
    claimBody: (options && options.claimBody) || { state: "completed", assets: [] },
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
    if (typeof url === "string" && url.indexOf("/api/companion/review-inbox") !== -1) {
      return jsonResponse(state.inboxStatus, state.inboxBody);
    }
    if (typeof url === "string" && url.indexOf("/api/x/requests/") !== -1) {
      return jsonResponse(200, state.claimBody);
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

function loadReviewInbox() {
  const context = {
    FrameNestCompanion: companion,
    document: {
      getElementById() {
        return null;
      },
    },
    chrome: {},
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
        return { tagName: String(tag).toUpperCase(), textContent: "" };
      },
    },
  };
  return list;
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
  assert.equal(fs.existsSync(path.join(REPO, "extension/ui/review.html")), false);
  assert.equal(fs.existsSync(path.join(REPO, "extension/ui/review.js")), false);
  assert.equal(fs.existsSync(path.join(REPO, "extension/ui/review.css")), false);
});

test("review inbox protocol uses pathFor GET and dropUnknown still rejects overlay types", () => {
  assert.equal(companion.TYPES.REVIEW_INBOX, "review_inbox");
  assert.ok(
    companion.dropUnknown({
      v: companion.PROTOCOL,
      type: companion.TYPES.REVIEW_INBOX,
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
  assert.equal(companion.reviewInboxQuerySuffix(1), "?limit=1");
  assert.equal(companion.reviewInboxQuerySuffix("1"), "");
  assert.equal(companion.reviewInboxQuerySuffix(101), "");
  assert.equal(companion.reviewInboxQuerySuffix(0), "");
  assert.doesNotMatch(workerSource, /fetch\(payload\.url\)/);
  assert.doesNotMatch(workerSource, /fetch\(message\.url\)/);
  assert.match(workerSource, /fetchJson\("reviewInbox"/);
  assert.doesNotMatch(workerSource, /setInterval/);
  assert.doesNotMatch(workerSource, /chrome\.notifications/);
  assert.doesNotMatch(extractNamedFunction(workerSource, "reviewInbox"), /method:\s*"POST"/);
  assert.doesNotMatch(workerSource, /review-inbox\/.+\/opened/);
  assert.doesNotMatch(workerSource, /review-inbox\/.+\/apply/);
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
  assert.equal(listCall.url, ORIGIN + "/api/companion/review-inbox");
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

test("S1 chrome sits between status and iframe and empty copy is exact", () => {
  const statusAt = sidebarHtml.indexOf('id="shell-status"');
  const inboxAt = sidebarHtml.indexOf('id="review-inbox"');
  const frameAt = sidebarHtml.indexOf('id="frame"');
  assert.ok(statusAt >= 0 && inboxAt > statusAt && frameAt > inboxAt);
  assert.match(sidebarHtml, />No analyzed items\.</);
  assert.doesNotMatch(sidebarHtml, /review\.html/);
  assert.match(sidebarCss, /#review-inbox\.is-collapsed \.review-inbox__panel/);
  assert.match(sidebarCss, /max-height:\s*8\.5rem/);
  assert.match(sidebarCss, /overflow-y:\s*auto/);
  assert.doesNotMatch(extractNamedFunction(sidebarSource, "hideInboxSection"), /clearFrame/);
  assert.doesNotMatch(extractNamedFunction(sidebarSource, "hideInboxSection"), /frame/);
  assert.doesNotMatch(extractNamedFunction(sidebarSource, "applyInboxCollapse"), /clearFrame/);
  assert.doesNotMatch(extractNamedFunction(sidebarSource, "onInboxToggle"), /clearFrame/);
  assert.doesNotMatch(sidebarSource, /innerHTML/);
  assert.doesNotMatch(sidebarSource, /\bfetch\s*\(/);
  assert.match(sidebarSource, /setInterval/);
  assert.match(sidebarSource, /visibilitychange/);
  assert.match(sidebarSource, /TYPES\.REVIEW_INBOX/);
});

test("native list renders titles with textContent and collapse rules skip title storage", () => {
  const inbox = loadReviewInbox();
  assert.equal(inbox.EMPTY_COPY, "No analyzed items.");
  assert.equal(inbox.HINT_COPY, "Awaiting analysis");
  assert.equal(inbox.POLL_MS, 15000);
  assert.equal(inbox.visualCollapsed(false, 0), true);
  assert.equal(inbox.visualCollapsed(true, 2), true);
  assert.equal(inbox.visualCollapsed(false, 2), false);
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
  assert.equal(inbox.newestRunId(items), RUN_NEW);
  const list = fakeListNode();
  inbox.renderList(list, items);
  assert.equal(list.childNodes.length, 2);
  assert.equal(list.childNodes[0].textContent, "<img src=x onerror=alert(1)>");
  assert.equal(list.childNodes[0].tagName, "LI");
  const persistFn = extractNamedFunction(sidebarSource, "persistInboxPrefs");
  assert.match(persistFn, /explicitCollapsedKey/);
  assert.match(persistFn, /seenRunIdKey/);
  assert.doesNotMatch(persistFn, /title/);
  assert.doesNotMatch(persistFn, /description/);
  assert.doesNotMatch(persistFn, /result_json/);
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
