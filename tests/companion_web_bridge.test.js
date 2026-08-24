const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");

const REPO = path.resolve(__dirname, "..");
const companion = require(path.join(REPO, "extension/shared/messages.js"));
const webHost = require(path.join(REPO, "src/framenest/adapters/api/web/companion_host.js"));
const sidebarSource = fs.readFileSync(path.join(REPO, "extension/ui/sidebar.js"), "utf8");
const hostSource = fs.readFileSync(
  path.join(REPO, "src/framenest/adapters/api/web/companion_host.js"),
  "utf8"
);
const appSource = fs.readFileSync(
  path.join(REPO, "src/framenest/adapters/api/web/app.js"),
  "utf8"
);

const PIN = "chrome-extension://omiihmnlkmieaafaphohakcgmbggppap";
const ORIGIN = "https://nuc-1.example.ts.net";

function loadSidebarBridge() {
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
    Promise,
    setTimeout,
    clearTimeout,
  };
  vm.createContext(context);
  vm.runInContext(sidebarSource, context);
  return context.FrameNestSidebarBridge;
}

test("web and shell share the companion web protocol and never use a wildcard target", () => {
  const bridge = loadSidebarBridge();
  assert.equal(webHost.PROTOCOL, "framenest.companion.web.v1");
  assert.equal(bridge.WEB_PROTOCOL, webHost.PROTOCOL);
  assert.notEqual(webHost.PROTOCOL, companion.PROTOCOL);
  assert.equal(webHost.PINNED_EXTENSION_ORIGIN, PIN);
  assert.doesNotMatch(hostSource, /postMessage\([^)]*,\s*["']\*["']/);
  assert.doesNotMatch(sidebarSource, /postMessage\([^)]*,\s*["']\*["']/);
  assert.doesNotMatch(appSource, /addEventListener\(\s*["']message["']/);
  assert.equal(webHost.TYPES.OPEN_DETAILS, "open_details");
  assert.equal(bridge.WEB_TYPES.OPEN_DETAILS, "open_details");
  assert.doesNotMatch(hostSource, /framenest\.companion\.v1/);
});

test("WEB_READY is sent only to the pinned extension origin when framed", () => {
  const posted = [];
  const iframeWindow = {
    parent: {},
    addEventListener() {},
    postMessage() {},
  };
  iframeWindow.parent.postMessage = function postMessage(message, targetOrigin) {
    posted.push({ message, targetOrigin });
  };
  const host = webHost.createHost({ window: iframeWindow, parent: iframeWindow.parent });
  assert.equal(host.isHosted(), false);
  assert.equal(posted.length, 1);
  assert.equal(posted[0].targetOrigin, PIN);
  assert.equal(posted[0].message.v, webHost.PROTOCOL);
  assert.equal(posted[0].message.type, webHost.TYPES.WEB_READY);
});

test("a same-window page does not announce WEB_READY or become hosted", () => {
  const posted = [];
  const page = {
    parent: null,
    addEventListener() {},
  };
  page.parent = page;
  page.parent.postMessage = function postMessage(message, targetOrigin) {
    posted.push({ message, targetOrigin });
  };
  const host = webHost.createHost({ window: page, parent: page });
  assert.equal(host.isHosted(), false);
  assert.equal(posted.length, 0);
  host.handleMessage({
    origin: PIN,
    source: page,
    data: { v: webHost.PROTOCOL, type: webHost.TYPES.HOST_HELLO },
  });
  assert.equal(host.isHosted(), false);
});

test("spoofed https parent cannot set hosted without the pinned extension origin", () => {
  const posted = [];
  const parentWindow = {
    postMessage(message, targetOrigin) {
      posted.push({ message, targetOrigin });
    },
  };
  const iframeWindow = {
    parent: parentWindow,
    addEventListener() {},
  };
  const host = webHost.createHost({ window: iframeWindow, parent: parentWindow });
  host.handleMessage({
    origin: "https://evil.example",
    source: parentWindow,
    data: { v: webHost.PROTOCOL, type: webHost.TYPES.HOST_HELLO },
  });
  assert.equal(host.isHosted(), false);
  host.handleMessage({
    origin: PIN,
    source: parentWindow,
    data: { v: webHost.PROTOCOL, type: webHost.TYPES.HOST_HELLO },
  });
  assert.equal(host.isHosted(), true);
  assert.equal(posted.some((entry) => entry.message.type === webHost.TYPES.HOST_ACK), true);
  posted.forEach((entry) => {
    assert.equal(entry.targetOrigin, PIN);
  });
});

test("ATTACH_REQUEST rejects non-UUIDs and forwards only catalog ids", async () => {
  const posted = [];
  const parentWindow = {
    postMessage(message, targetOrigin) {
      posted.push({ message, targetOrigin });
    },
  };
  const iframeWindow = {
    parent: parentWindow,
    addEventListener() {},
  };
  const host = webHost.createHost({ window: iframeWindow, parent: parentWindow });
  host.handleMessage({
    origin: PIN,
    source: parentWindow,
    data: { v: webHost.PROTOCOL, type: webHost.TYPES.HOST_HELLO },
  });
  const rejected = await host.attach("https://evil.example/media.bin", "not-a-uuid");
  assert.equal(rejected.ok, false);
  assert.equal(rejected.error, "invalid_attach");
  const attachPosts = posted.filter((entry) => entry.message.type === webHost.TYPES.ATTACH_REQUEST);
  assert.equal(attachPosts.length, 0);

  const mediaId = "11111111-1111-4111-8111-111111111111";
  const locationId = "22222222-2222-4222-8222-222222222222";
  const pending = host.attach(mediaId, locationId);
  const request = posted.filter((entry) => entry.message.type === webHost.TYPES.ATTACH_REQUEST).pop();
  assert.ok(request);
  assert.deepEqual(request.message.payload, { mediaId, locationId });
  assert.equal("url" in request.message.payload, false);
  host.handleMessage({
    origin: PIN,
    source: parentWindow,
    data: {
      v: webHost.PROTOCOL,
      type: webHost.TYPES.ATTACH_RESULT,
      payload: { ok: false, error: "composer_unbound" },
    },
  });
  const result = await pending;
  assert.equal(result.ok, false);
  assert.equal(result.error, "composer_unbound");
});

test("shell accepts only the framed stored origin and UUID attach ids", () => {
  const bridge = loadSidebarBridge();
  const iframeWindow = {};
  const otherWindow = {};
  assert.equal(
    bridge.acceptIncomingWebMessage(
      {
        source: otherWindow,
        origin: ORIGIN,
        data: { v: bridge.WEB_PROTOCOL, type: bridge.WEB_TYPES.WEB_READY },
      },
      iframeWindow,
      ORIGIN
    ),
    null
  );
  assert.equal(
    bridge.acceptIncomingWebMessage(
      {
        source: iframeWindow,
        origin: "https://evil.example",
        data: { v: bridge.WEB_PROTOCOL, type: bridge.WEB_TYPES.WEB_READY },
      },
      iframeWindow,
      ORIGIN
    ),
    null
  );
  assert.equal(
    bridge.acceptIncomingWebMessage(
      {
        source: iframeWindow,
        origin: PIN,
        data: { v: bridge.WEB_PROTOCOL, type: bridge.WEB_TYPES.WEB_READY },
      },
      iframeWindow,
      PIN
    ),
    null
  );
  const accepted = bridge.acceptIncomingWebMessage(
    {
      source: iframeWindow,
      origin: ORIGIN,
      data: { v: bridge.WEB_PROTOCOL, type: bridge.WEB_TYPES.WEB_READY },
    },
    iframeWindow,
    ORIGIN
  );
  assert.ok(accepted);
  assert.equal(accepted.type, bridge.WEB_TYPES.WEB_READY);
  assert.equal(
    bridge.attachIdsFromWebRequest({
      payload: { mediaId: "https://evil.example", locationId: "x", url: "https://evil.example/file" },
    }),
    null
  );
  const ids = bridge.attachIdsFromWebRequest({
    payload: {
      mediaId: "11111111-1111-4111-8111-111111111111",
      locationId: "22222222-2222-4222-8222-222222222222",
      url: "https://evil.example/file",
    },
  });
  assert.equal(ids.mediaId, "11111111-1111-4111-8111-111111111111");
  assert.equal(ids.locationId, "22222222-2222-4222-8222-222222222222");
  assert.equal(Object.prototype.hasOwnProperty.call(ids, "url"), false);
  assert.match(sidebarSource, /TYPES\.ATTACH_BEGIN/);
  assert.doesNotMatch(sidebarSource, /payload\.url/);
});

test("open_details opens hosted media-details from the pinned extension only", () => {
  const opened = [];
  const posted = [];
  const parentWindow = {
    postMessage(message, targetOrigin) {
      posted.push({ message, targetOrigin });
    },
  };
  const iframeWindow = {
    parent: parentWindow,
    addEventListener() {},
  };
  const host = webHost.createHost({
    window: iframeWindow,
    parent: parentWindow,
    onOpenDetails(mediaId) {
      opened.push(mediaId);
    },
  });
  host.handleMessage({
    origin: PIN,
    source: parentWindow,
    data: { v: webHost.PROTOCOL, type: webHost.TYPES.HOST_HELLO },
  });
  const mediaId = "11111111-1111-4111-8111-111111111111";
  host.handleMessage({
    origin: "https://evil.example",
    source: parentWindow,
    data: {
      v: webHost.PROTOCOL,
      type: webHost.TYPES.OPEN_DETAILS,
      payload: { mediaId: mediaId },
    },
  });
  assert.deepEqual(opened, []);
  host.handleMessage({
    origin: PIN,
    source: parentWindow,
    data: {
      v: webHost.PROTOCOL,
      type: webHost.TYPES.OPEN_DETAILS,
      payload: { mediaId: "not-a-uuid" },
    },
  });
  assert.deepEqual(opened, []);
  host.handleMessage({
    origin: PIN,
    source: parentWindow,
    data: {
      v: webHost.PROTOCOL,
      type: webHost.TYPES.OPEN_DETAILS,
      payload: { mediaId: mediaId },
    },
  });
  assert.deepEqual(opened, [mediaId]);
  assert.equal(webHost.TYPES.OPEN_DETAILS, "open_details");
  const bridge = loadSidebarBridge();
  assert.equal(bridge.WEB_TYPES.OPEN_DETAILS, webHost.TYPES.OPEN_DETAILS);
  assert.match(appSource, /onOpenDetails/);
  assert.match(appSource, /openDetailsDialog\(\s*\{\s*media_id:\s*mediaId\s*\}/);
  posted.forEach((entry) => {
    assert.equal(entry.targetOrigin, PIN);
  });
});

test("sidebar Attached follows ATTACH_BEGIN result.ok", () => {
  const handle = sidebarSource.match(/async function handleAttachRequest\([\s\S]*?\n  \}/);
  assert.ok(handle, "handleAttachRequest()");
  assert.match(handle[0], /TYPES\.ATTACH_BEGIN/);
  assert.match(handle[0], /const ok = Boolean\(result && result\.ok\)/);
  assert.match(handle[0], /else if \(ok\) \{\s*setText\(shellStatus, "Attached"\);/);
  assert.match(handle[0], /error === "composer_unbound"/);
});

test("handshake timeout copy does not claim framing failed when the iframe loaded", () => {
  const bridge = loadSidebarBridge();
  assert.equal(bridge.handshakeTimeoutCopy(false), bridge.framingFailureCopy());
  assert.equal(bridge.handshakeTimeoutCopy(true), bridge.companionHostMissingCopy());
  assert.match(bridge.framingFailureCopy(), /did not load in this panel/);
  assert.match(bridge.companionHostMissingCopy(), /cannot host companion Attach yet/);
  assert.doesNotMatch(bridge.framingFailureCopy(), /could not be framed/i);
  assert.doesNotMatch(bridge.companionHostMissingCopy(), /could not be framed/i);
  assert.doesNotMatch(bridge.handshakeTimeoutCopy(true), /could not be framed/i);
  assert.doesNotMatch(sidebarSource, /could not be framed/);
  assert.match(sidebarSource, /frameLoaded = true/);
  assert.match(sidebarSource, /handshakeTimeoutCopy\(loaded\)/);
});
