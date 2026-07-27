const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");

const APP_PATH = path.resolve(__dirname, "../src/framenest/adapters/api/web/app.js");
const INDEX_PATH = path.resolve(__dirname, "../src/framenest/adapters/api/web/index.html");
const STYLES_PATH = path.resolve(__dirname, "../src/framenest/adapters/api/web/styles.css");
const APP_SOURCE = fs.readFileSync(APP_PATH, "utf8");
const INDEX_SOURCE = fs.readFileSync(INDEX_PATH, "utf8");
const STYLES_SOURCE = fs.readFileSync(STYLES_PATH, "utf8");

function extractFunction(source, name) {
  const markers = [`async function ${name}(`, `function ${name}(`];
  let start = -1;
  for (const marker of markers) {
    start = source.indexOf(marker);
    if (start !== -1) break;
  }
  assert.notEqual(start, -1, `missing production function ${name}`);
  const headerOpen = source.indexOf("(", start);
  assert.notEqual(headerOpen, -1, `missing parameter list for ${name}`);
  let depth = 0;
  let headerClose = -1;
  for (let index = headerOpen; index < source.length; index += 1) {
    const character = source[index];
    if (character === "(") depth += 1;
    else if (character === ")") {
      depth -= 1;
      if (depth === 0) {
        headerClose = index;
        break;
      }
    }
  }
  assert.notEqual(headerClose, -1, `unterminated parameter list for ${name}`);
  const bodyOpen = source.indexOf("{", headerClose);
  assert.notEqual(bodyOpen, -1, `missing body for ${name}`);
  depth = 0;
  for (let index = bodyOpen; index < source.length; index += 1) {
    const character = source[index];
    if (character === "{") depth += 1;
    else if (character === "}") {
      depth -= 1;
      if (depth === 0) return source.slice(start, index + 1);
    }
  }
  throw new Error(`unterminated production function ${name}`);
}

function response(payload, status = 200) {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: async () => payload,
  };
}

function createIdentityControlMock() {
  const attrs = { "aria-label": "Tailscale identity status" };
  const classes = new Set(["status-button", "identity-badge"]);
  return {
    hidden: true,
    textContent: "",
    title: "Open Tailscale identity status",
    classList: {
      add(name) {
        classes.add(name);
      },
      remove(...names) {
        for (const name of names) classes.delete(name);
      },
      contains(name) {
        return classes.has(name);
      },
    },
    setAttribute(name, value) {
      attrs[name] = String(value);
    },
    removeAttribute(name) {
      delete attrs[name];
    },
    getAttribute(name) {
      return Object.prototype.hasOwnProperty.call(attrs, name) ? attrs[name] : null;
    },
  };
}

function createAdminOnlyRows() {
  return [
    { hidden: true, name: "connection" },
    { hidden: true, name: "hostname" },
    { hidden: true, name: "url" },
    { hidden: true, name: "provenance" },
  ];
}

function createIdentityHarness(fetchImpl) {
  const uploadOpenButton = { hidden: false };
  const detailsEditButton = { hidden: false };
  const identityBadge = createIdentityControlMock();
  const identityStatusName = { textContent: "" };
  const statusTailscaleAdminOnlyRows = createAdminOnlyRows();
  const context = {
    console,
    fetch: fetchImpl,
    Set,
    Object,
    Array,
    Boolean,
    uploadOpenButton,
    detailsEditButton,
    identityBadge,
    identityStatusName,
    statusTailscaleAdminOnlyRows,
    metadataControlCalls: 0,
  };
  context.updateMetadataControls = () => {
    context.metadataControlCalls += 1;
  };
  context.globalThis = context;
  vm.createContext(context);
  const prelude = [
    "let identityState = {",
    "  resolved: false,",
    "  available: false,",
    '  login: "",',
    '  displayName: "",',
    '  role: "",',
    '  provenance: "",',
    "  capabilities: new Set(),",
    "};",
    'const IDENTITY_ENDPOINT = "/api/identity/me";',
    extractFunction(APP_SOURCE, "identityHasCapability"),
    extractFunction(APP_SOURCE, "framenestMutationHeaders"),
    extractFunction(APP_SOURCE, "applyIdentityCapabilities"),
    extractFunction(APP_SOURCE, "applyTailscalePanelDensity"),
    extractFunction(APP_SOURCE, "renderIdentityBadge"),
    extractFunction(APP_SOURCE, "loadIdentity"),
  ].join("\n");
  vm.runInContext(prelude, context);
  return context;
}

function createStatusTabHarness(fetchImpl, locationStub, role = "admin") {
  const makeTab = (selected) => ({
    classList: {
      _active: selected,
      toggle(name, force) {
        if (name === "settings-dialog__tab--active") this._active = force;
      },
    },
    attrs: { "aria-selected": String(selected) },
    tabIndex: selected ? 0 : -1,
    setAttribute(name, value) {
      this.attrs[name] = String(value);
    },
    getAttribute(name) {
      return this.attrs[name] || null;
    },
    focus() {
      this.focused = true;
    },
    focused: false,
  });
  const makePanel = (hidden) => ({
    hidden,
    focus() {
      this.focused = true;
    },
    focused: false,
  });
  const fields = {};
  for (const id of [
    "statusTailscaleConnection",
    "statusTailscaleAccessMethod",
    "statusTailscaleHostname",
    "statusTailscaleUrl",
    "statusTailscaleHttps",
    "statusTailscaleLogin",
    "statusTailscaleDisplayName",
    "statusTailscaleRole",
    "statusTailscaleProvenance",
    "statusCloudServer",
    "statusCloudConnection",
    "statusCloudRemote",
  ]) {
    fields[id] = { textContent: "" };
  }
  const statusCloudRemoteRow = { hidden: true };
  const statusTailscaleAdminOnlyRows = createAdminOnlyRows();
  const statusDialog = {
    open: false,
    showModal() {
      this.open = true;
      this.setAttribute("open", "");
    },
    close() {
      this.open = false;
      this.removeAttribute("open");
    },
    attrs: {},
    setAttribute(name, value) {
      this.attrs[name] = value;
    },
    removeAttribute(name) {
      delete this.attrs[name];
    },
    hasAttribute(name) {
      return Object.prototype.hasOwnProperty.call(this.attrs, name);
    },
  };
  const context = {
    console,
    fetch: fetchImpl,
    Set,
    Object,
    Array,
    Boolean,
    String,
    Math,
    location: locationStub,
    document: { activeElement: null },
    statusTabAi: makeTab(true),
    statusTabCloud: makeTab(false),
    statusTabTailscale: makeTab(false),
    statusPanelAi: makePanel(false),
    statusPanelCloud: makePanel(true),
    statusPanelTailscale: makePanel(true),
    statusDialog,
    statusCloudRemoteRow,
    statusTailscaleAdminOnlyRows,
    lastFocusedElementBeforeStatus: null,
    lastCloudStatusPayload: null,
    identityState: {
      resolved: true,
      available: true,
      login: role === "admin" ? "aecrypto@gmail.com" : "user@example.com",
      displayName: role === "admin" ? "ae crypto" : "Reader",
      role,
      provenance: "tailscale-serve",
      capabilities: new Set(["gallery.read"]),
    },
    aiStatusButton: { focus() {} },
    ...fields,
  };
  context.globalThis = context;
  vm.createContext(context);
  const prelude = [
    'const CLOUD_STATUS_ENDPOINT = "/api/status/cloud";',
    "let lastCloudStatusPayload = null;",
    "let lastFocusedElementBeforeStatus = null;",
    extractFunction(APP_SOURCE, "identityRoleLabel"),
    extractFunction(APP_SOURCE, "applyTailscalePanelDensity"),
    extractFunction(APP_SOURCE, "renderTailscaleConnectionFields"),
    extractFunction(APP_SOURCE, "renderTailscaleIdentityFields"),
    extractFunction(APP_SOURCE, "renderCloudStatus"),
    extractFunction(APP_SOURCE, "renderTailscaleStatus"),
    extractFunction(APP_SOURCE, "loadCloudStatus"),
    extractFunction(APP_SOURCE, "loadTailscaleStatus"),
    "async function loadAiCapability() { contextAiRefreshCount += 1; }",
    "let contextAiRefreshCount = 0;",
    extractFunction(APP_SOURCE, "setActiveStatusTab"),
    extractFunction(APP_SOURCE, "openStatusDialog"),
  ].join("\n");
  vm.runInContext(prelude, context);
  return context;
}

test("mutation helper always injects the FrameNest mutation header", () => {
  const context = createIdentityHarness(async () => response({}, 404));
  const merged = vm.runInContext(
    'framenestMutationHeaders({ Accept: "application/json", "Upload-Offset": "7" })',
    context,
  );
  assert.equal(merged["X-FrameNest-Request"], "1");
  assert.equal(merged.Accept, "application/json");
  assert.equal(merged["Upload-Offset"], "7");
});

test("every unsafe fetch call site sends the mutation header", () => {
  const mutationSites = APP_SOURCE.match(/method: "(?:POST|PUT|PATCH|DELETE)"/g) || [];
  const wrappedSites = APP_SOURCE.match(/headers: framenestMutationHeaders\(/g) || [];
  assert.equal(mutationSites.length, 17);
  assert.equal(wrappedSites.length, 17);
  assert.equal((APP_SOURCE.match(/"X-FrameNest-Request"/g) || []).length, 1);
});

test("identity bootstrap runs first and gates the initial catalog load", () => {
  const bootstrap = APP_SOURCE.slice(APP_SOURCE.indexOf("const identityReady = loadIdentity();"));
  assert.ok(bootstrap.startsWith("const identityReady = loadIdentity();\ncheckHealth();"));
  assert.match(bootstrap, /identityReady\.then\(\(\) => \{\n {2}loadCatalog\(\);\n\}\);/);
  assert.ok(bootstrap.indexOf("loadIdentity();") < bootstrap.indexOf("checkHealth();"));
});

test("identity fetch never sends the mutation header", () => {
  const loadIdentityBody = extractFunction(APP_SOURCE, "loadIdentity");
  assert.ok(!loadIdentityBody.includes("X-FrameNest-Request"));
  assert.ok(loadIdentityBody.includes('headers: { Accept: "application/json" }'));
});

test("header controls are compact icon-only with distinct identity name pill", () => {
  const headerStart = INDEX_SOURCE.indexOf('class="app-header"');
  const headerEnd = INDEX_SOURCE.indexOf("</header>", headerStart);
  const header = INDEX_SOURCE.slice(headerStart, headerEnd);
  assert.match(header, /id="upload-open-button"/);
  assert.match(header, /aria-label="Upload media"/);
  assert.match(header, /status-button--icon/);
  assert.match(header, />↑</);
  assert.ok(!/status-button__label">Upload</.test(header));
  assert.ok(!/>Local</.test(header));
  assert.match(header, /☁️/);
  assert.ok(!/status-button__label">Cloud</.test(header));
  assert.match(header, /🧠/);
  assert.ok(!/status-button__label">AI</.test(header));
  assert.ok(!/status-button__dot/.test(header));
  assert.match(header, /id="identity-status-name"/);
  assert.ok(!/identity-status-role/.test(header));
  assert.ok(!/identity-badge__sep/.test(header));
  assert.ok(STYLES_SOURCE.includes("grid-template-areas: \"brand search controls\""));
  assert.ok(STYLES_SOURCE.includes('"brand controls"'));
  assert.ok(STYLES_SOURCE.includes('"search search"'));
  assert.ok(STYLES_SOURCE.includes("@media (max-width: 900px)"));
  assert.ok(STYLES_SOURCE.includes("@media (max-width: 360px)"));
  assert.ok(STYLES_SOURCE.includes(".status-button--icon"));
  assert.ok(STYLES_SOURCE.includes(".status-button__glyph"));
  assert.ok(STYLES_SOURCE.includes("max-width: min(88px, 26vw)"));
  assert.ok(!/overflow-x:\s*hidden/.test(STYLES_SOURCE.match(/body\s*\{[^}]*\}/)?.[0] || ""));
  assert.ok(STYLES_SOURCE.includes("minmax(0, 1fr)"));
});

test("identity control opens Tailscale status tab in source wiring", () => {
  assert.ok(APP_SOURCE.includes('openStatusDialog("tailscale")'));
  assert.ok(APP_SOURCE.includes("if (identityBadge)"));
  assert.ok(APP_SOURCE.includes('setActiveStatusTab("tailscale")'));
  assert.ok(INDEX_SOURCE.includes('id="status-tab-tailscale"'));
  assert.ok(INDEX_SOURCE.includes('id="status-panel-tailscale"'));
  assert.ok(
    INDEX_SOURCE.indexOf('id="status-tab-cloud"') < INDEX_SOURCE.indexOf('id="status-tab-tailscale"'),
  );
});

test("privileged controls are gated by capabilities in source", () => {
  assert.ok(APP_SOURCE.includes('identityHasCapability("upload.manage")'));
  assert.ok(APP_SOURCE.includes('identityHasCapability("metadata.canonical.write")'));
  assert.ok(APP_SOURCE.includes('identityHasCapability("analysis.run")'));
  const cardBody = extractFunction(APP_SOURCE, "renderCatalogCard");
  assert.ok(cardBody.includes("cardAiQuickActionEligible(item)"));
  assert.equal(cardBody.includes("cardNeedsMetadata(item)"), false);
  assert.ok(cardBody.includes('if (identityHasCapability("metadata.canonical.write")) {'));
  const eligibleBody = extractFunction(APP_SOURCE, "cardAiQuickActionEligible");
  const identityGateBody = extractFunction(APP_SOURCE, "identityAllowsCardAiQuickAction");
  assert.ok(eligibleBody.includes("identityAllowsCardAiQuickAction()"));
  assert.equal(eligibleBody.includes("identityHasCapability("), false);
  assert.ok(identityGateBody.includes("identityState.resolved"));
  assert.ok(identityGateBody.includes("identityState.available"));
  assert.ok(identityGateBody.includes('capabilities.has("analysis.run")'));
  assert.ok(identityGateBody.includes('capabilities.has("metadata.canonical.write")'));
});

test("gallery AI quick action fails closed for missing unresolved and ordinary identity", () => {
  const identityGateBody = extractFunction(APP_SOURCE, "identityAllowsCardAiQuickAction");
  assert.ok(identityGateBody.includes("identityState.resolved"));
  assert.ok(identityGateBody.includes("identityState.available"));
  assert.ok(identityGateBody.includes('capabilities.has("analysis.run")'));
  assert.ok(identityGateBody.includes('capabilities.has("metadata.canonical.write")'));
  assert.equal(identityGateBody.includes("identityHasCapability("), false);
  assert.ok(APP_SOURCE.includes("function identityAllowsCardAiQuickAction()"));
});

test("admin identity populates name-only badge and unlocks privileged controls", async () => {
  const context = createIdentityHarness(async (url) => {
    assert.equal(url, "/api/identity/me");
    return response({
      login: "admin@example.com",
      display_name: "Admin User",
      role: "admin",
      capabilities: [
        "analysis.run",
        "gallery.read",
        "metadata.canonical.write",
        "upload.manage",
      ],
      provenance: "tailscale-serve",
    });
  });
  await vm.runInContext("loadIdentity()", context);
  const state = vm.runInContext("identityState", context);
  assert.equal(state.available, true);
  assert.equal(state.login, "admin@example.com");
  assert.equal(state.provenance, "tailscale-serve");
  assert.equal(context.identityBadge.hidden, false);
  assert.equal(context.identityStatusName.textContent, "Admin User");
  assert.match(context.identityBadge.getAttribute("aria-label"), /Signed in as Admin User/);
  assert.ok(!/Admin\./.test(context.identityBadge.getAttribute("aria-label").replace("Admin User", "")));
  assert.match(context.identityBadge.title, /Signed in as admin@example.com/);
  assert.equal(context.identityBadge.classList.contains("status-button--healthy"), false);
  assert.equal(context.uploadOpenButton.hidden, false);
  assert.equal(context.detailsEditButton.hidden, false);
  assert.equal(context.metadataControlCalls, 1);
  assert.equal(context.statusTailscaleAdminOnlyRows.every((row) => row.hidden === false), true);
});

test("ordinary user identity hides privileged controls and keeps admin Tailscale rows hidden", async () => {
  const context = createIdentityHarness(async () =>
    response({
      login: "user@example.com",
      display_name: "Reader",
      role: "user",
      capabilities: ["gallery.read", "media.download", "media.original.read"],
      provenance: "tailscale-serve",
    }),
  );
  await vm.runInContext("loadIdentity()", context);
  assert.equal(context.identityBadge.hidden, false);
  assert.equal(context.identityStatusName.textContent, "Reader");
  assert.match(context.identityBadge.getAttribute("aria-label"), /Signed in as Reader/);
  assert.ok(!context.identityBadge.getAttribute("aria-label").includes("Admin"));
  assert.equal(context.uploadOpenButton.hidden, true);
  assert.equal(context.detailsEditButton.hidden, true);
  assert.equal(context.statusTailscaleAdminOnlyRows.every((row) => row.hidden === true), true);
  assert.equal(vm.runInContext('identityHasCapability("upload.manage")', context), false);
  assert.equal(vm.runInContext('identityHasCapability("metadata.canonical.write")', context), false);
  assert.equal(vm.runInContext('identityHasCapability("gallery.read")', context), true);
});

test("denied identity fails closed and hides the badge", async () => {
  const context = createIdentityHarness(async () => response({}, 403));
  await vm.runInContext("loadIdentity()", context);
  const state = vm.runInContext("identityState", context);
  assert.equal(state.available, true);
  assert.equal(state.capabilities.size, 0);
  assert.equal(context.identityBadge.hidden, true);
  assert.equal(context.uploadOpenButton.hidden, true);
  assert.equal(context.detailsEditButton.hidden, true);
  assert.equal(context.statusTailscaleAdminOnlyRows.every((row) => row.hidden === true), true);
});

test("missing identity endpoint keeps legacy local behavior", async () => {
  const context = createIdentityHarness(async () => response({}, 404));
  await vm.runInContext("loadIdentity()", context);
  const state = vm.runInContext("identityState", context);
  assert.equal(state.available, false);
  assert.equal(vm.runInContext('identityHasCapability("upload.manage")', context), true);
  assert.equal(context.uploadOpenButton.hidden, false);
  assert.equal(context.identityBadge.hidden, true);
});

test("identity network failure keeps legacy local behavior", async () => {
  const context = createIdentityHarness(async () => {
    throw new Error("network down");
  });
  await vm.runInContext("loadIdentity()", context);
  const state = vm.runInContext("identityState", context);
  assert.equal(state.resolved, true);
  assert.equal(state.available, false);
  assert.equal(vm.runInContext('identityHasCapability("analysis.run")', context), true);
});

test("admin Tailscale panel shows diagnostic rows", async () => {
  const context = createStatusTabHarness(
    async (url) => {
      assert.equal(url, "/api/status/cloud");
      return response({
        server: "connected",
        connection: "tailscale",
        remote_access: "https://example.ts.net",
      });
    },
    {
      hostname: "example.ts.net",
      origin: "https://example.ts.net",
      protocol: "https:",
    },
    "admin",
  );
  await vm.runInContext('openStatusDialog("tailscale")', context);
  await vm.runInContext("loadTailscaleStatus()", context);
  assert.equal(context.statusDialog.open, true);
  assert.equal(context.statusPanelTailscale.hidden, false);
  assert.equal(context.statusTabTailscale.getAttribute("aria-selected"), "true");
  assert.equal(context.statusTailscaleLogin.textContent, "aecrypto@gmail.com");
  assert.equal(context.statusTailscaleDisplayName.textContent, "ae crypto");
  assert.equal(context.statusTailscaleRole.textContent, "Admin");
  assert.equal(context.statusTailscaleProvenance.textContent, "tailscale-serve");
  assert.equal(context.statusTailscaleHostname.textContent, "example.ts.net");
  assert.equal(context.statusTailscaleAccessMethod.textContent, "Tailscale");
  assert.equal(context.statusTailscaleAdminOnlyRows.every((row) => row.hidden === false), true);
  assert.equal(APP_SOURCE.includes("nuc-1.tail247768.ts.net"), false);
});

test("ordinary user Tailscale panel keeps admin diagnostics hidden", async () => {
  const context = createStatusTabHarness(
    async () =>
      response({
        server: "connected",
        connection: "tailscale",
      }),
    {
      hostname: "example.ts.net",
      origin: "https://example.ts.net",
      protocol: "https:",
    },
    "user",
  );
  await vm.runInContext('openStatusDialog("tailscale")', context);
  await vm.runInContext("loadTailscaleStatus()", context);
  assert.equal(context.statusTailscaleDisplayName.textContent, "Reader");
  assert.equal(context.statusTailscaleLogin.textContent, "user@example.com");
  assert.equal(context.statusTailscaleRole.textContent, "User");
  assert.equal(context.statusTailscaleAccessMethod.textContent, "Tailscale");
  assert.equal(context.statusTailscaleHttps.textContent, "Yes");
  assert.equal(context.statusTailscaleAdminOnlyRows.every((row) => row.hidden === true), true);
});

test("Cloud and AI status controls still select their tabs", async () => {
  const context = createStatusTabHarness(
    async () =>
      response({
        server: "connected",
        connection: "tailscale",
      }),
    {
      hostname: "example.ts.net",
      origin: "https://example.ts.net",
      protocol: "https:",
    },
  );
  await vm.runInContext('openStatusDialog("cloud")', context);
  assert.equal(context.statusPanelCloud.hidden, false);
  assert.equal(context.statusPanelAi.hidden, true);
  assert.equal(context.statusPanelTailscale.hidden, true);
  assert.equal(context.statusTabCloud.getAttribute("aria-selected"), "true");

  await vm.runInContext('openStatusDialog("ai", { refreshAiStatus: true })', context);
  assert.equal(context.statusPanelAi.hidden, false);
  assert.equal(context.statusPanelCloud.hidden, true);
  assert.equal(context.statusPanelTailscale.hidden, true);
  assert.equal(context.statusTabAi.getAttribute("aria-selected"), "true");
  assert.equal(vm.runInContext("contextAiRefreshCount", context), 1);
});

test("Tailscale admin-only rows are hidden by default in markup", () => {
  const matches = [...INDEX_SOURCE.matchAll(/class="status-tailscale-admin-only" hidden/g)];
  assert.equal(matches.length, 4);
  assert.ok(INDEX_SOURCE.includes("status-tailscale-login"));
  assert.ok(INDEX_SOURCE.includes("status-tailscale-provenance"));
  assert.ok(!INDEX_SOURCE.toLowerCase().includes("cookie"));
  assert.ok(!INDEX_SOURCE.includes("nuc-1.tail247768.ts.net"));
  assert.ok(INDEX_SOURCE.includes("tailnet"));
  assert.ok(APP_SOURCE.includes("applyTailscalePanelDensity"));
});

test("Cloud and AI accessible labels communicate status without emoji reliance", () => {
  const cloudBody = extractFunction(APP_SOURCE, "setServerHealthButtonState");
  const aiBody = extractFunction(APP_SOURCE, "setAiStatusButtonState");
  assert.ok(cloudBody.includes("Cloud status: connected"));
  assert.ok(cloudBody.includes("Cloud status: unavailable"));
  assert.ok(cloudBody.includes("Cloud status: checking"));
  assert.ok(aiBody.includes("AI status: available"));
  assert.ok(aiBody.includes("AI status: unavailable"));
  assert.ok(aiBody.includes("AI status: checking"));
});
