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
  let depth = 0;
  let began = false;
  for (let index = start; index < source.length; index += 1) {
    const character = source[index];
    if (character === "{") {
      depth += 1;
      began = true;
    } else if (character === "}") {
      depth -= 1;
      if (began && depth === 0) return source.slice(start, index + 1);
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

function createIdentityHarness(fetchImpl) {
  const uploadOpenButton = { hidden: false };
  const detailsEditButton = { hidden: false };
  const identityBadge = {
    hidden: true,
    textContent: "",
    title: "",
    replaceChildren() {
      this.textContent = "";
    },
  };
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
    "  capabilities: new Set(),",
    "};",
    'const IDENTITY_ENDPOINT = "/api/identity/me";',
    extractFunction(APP_SOURCE, "identityHasCapability"),
    extractFunction(APP_SOURCE, "framenestMutationHeaders"),
    extractFunction(APP_SOURCE, "applyIdentityCapabilities"),
    extractFunction(APP_SOURCE, "renderIdentityBadge"),
    extractFunction(APP_SOURCE, "loadIdentity"),
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
  assert.equal(mutationSites.length, 16);
  assert.equal(wrappedSites.length, 16);
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

test("identity badge markup and styles exist and stay hidden by default", () => {
  assert.ok(INDEX_SOURCE.includes('id="identity-badge" class="identity-badge" hidden'));
  assert.ok(STYLES_SOURCE.includes(".identity-badge {"));
  assert.ok(STYLES_SOURCE.includes(".identity-badge[hidden]"));
});

test("privileged controls are gated by capabilities in source", () => {
  assert.ok(APP_SOURCE.includes('identityHasCapability("upload.manage")'));
  assert.ok(APP_SOURCE.includes('identityHasCapability("metadata.canonical.write")'));
  assert.ok(APP_SOURCE.includes('identityHasCapability("analysis.run")'));
  const cardBody = extractFunction(APP_SOURCE, "renderCatalogCard");
  assert.ok(cardBody.includes('cardNeedsMetadata(item) && identityHasCapability("analysis.run")'));
  assert.ok(cardBody.includes('if (identityHasCapability("metadata.canonical.write")) {'));
});

test("admin identity populates badge and unlocks privileged controls", async () => {
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
  assert.equal(context.identityBadge.hidden, false);
  assert.equal(context.identityBadge.textContent, "Admin User · Admin");
  assert.equal(context.identityBadge.title, "Signed in as admin@example.com");
  assert.equal(context.uploadOpenButton.hidden, false);
  assert.equal(context.detailsEditButton.hidden, false);
  assert.equal(context.metadataControlCalls, 1);
  assert.equal(vm.runInContext('identityHasCapability("upload.manage")', context), true);
});

test("ordinary user identity hides privileged controls", async () => {
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
  assert.equal(context.identityBadge.textContent, "Reader · User");
  assert.equal(context.uploadOpenButton.hidden, true);
  assert.equal(context.detailsEditButton.hidden, true);
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
