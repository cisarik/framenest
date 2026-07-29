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
  const start = markers
    .map((marker) => source.indexOf(marker))
    .find((position) => position !== -1);
  assert.notEqual(start, undefined, `missing production function ${name}`);
  const headerOpen = source.indexOf("(", start);
  let depth = 0;
  let bodyOpen = -1;
  for (let index = headerOpen; index < source.length; index += 1) {
    if (source[index] === "(") depth += 1;
    if (source[index] === ")") depth -= 1;
    if (depth === 0) {
      bodyOpen = source.indexOf("{", index);
      break;
    }
  }
  assert.notEqual(bodyOpen, -1, `missing body for ${name}`);
  depth = 0;
  for (let index = bodyOpen; index < source.length; index += 1) {
    if (source[index] === "{") depth += 1;
    if (source[index] === "}") {
      depth -= 1;
      if (depth === 0) return source.slice(start, index + 1);
    }
  }
  throw new Error(`unterminated production function ${name}`);
}

function deferred() {
  let resolve;
  const promise = new Promise((settle) => {
    resolve = settle;
  });
  return { promise, resolve };
}

function response(payload, status = 200) {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: async () => payload,
  };
}

test("admin navigation is hidden by default and requires the explicit workflow capability", () => {
  assert.match(
    INDEX_SOURCE,
    /id="admin-media-open-button"[\s\S]*?hidden[\s\S]*?>[\s\S]*?Manage media/,
  );
  const gate = extractFunction(APP_SOURCE, "identityAllowsAdminWorkflow");
  assert.match(gate, /identityState\.resolved/);
  assert.match(gate, /identityState\.available/);
  assert.match(gate, /capabilities\.has\("media\.workflow\.read"\)/);
  assert.doesNotMatch(gate, /identityHasCapability/);
  assert.match(extractFunction(APP_SOURCE, "applyIdentityCapabilities"), /identityAllowsAdminWorkflow/);
});

test("admin surface owns independent filters, requests, items, and per-item publication state", () => {
  const stateSource = APP_SOURCE.slice(
    APP_SOURCE.indexOf("let adminCatalogState = {"),
    APP_SOURCE.indexOf("let uploadCapability = {"),
  );
  for (const field of [
    "publication",
    "readiness",
    "analysis",
    "limit",
    "offset",
    "requestOwner",
    "items",
    "publishOwners",
    "actionStatusByMediaId",
    "loading",
    "error",
  ]) {
    assert.match(stateSource, new RegExp(`${field}:`));
  }
  assert.match(stateSource, /publication: "unpublished"/);
});

test("admin list request ownership suppresses an older response", async () => {
  const pending = [];
  const rendered = [];
  const context = {
    URLSearchParams,
    Object,
    Boolean,
    String,
    Number,
    Math,
    adminCatalogRequestToken: 0,
    adminCatalogState: {
      q: "older",
      publication: "unpublished",
      readiness: "all",
      analysis: "all",
      limit: 24,
      offset: 0,
      requestOwner: null,
    },
    ADMIN_MEDIA_ENDPOINT: "/api/admin/media",
    ADMIN_MEDIA_PAGE_SIZE: 24,
    adminMediaPrevButton: { disabled: false },
    adminMediaNextButton: { disabled: false },
    adminMediaPageSummary: { textContent: "" },
    identityAllowsAdminWorkflow: () => true,
    setAdminCatalogViewState: () => {},
    renderAdminCatalogPage: (page) => rendered.push(page.marker),
    fetch: () => {
      const request = deferred();
      pending.push(request);
      return request.promise;
    },
  };
  context.globalThis = context;
  vm.createContext(context);
  vm.runInContext(
    [
      extractFunction(APP_SOURCE, "snapshotAdminCatalogQueryState"),
      extractFunction(APP_SOURCE, "buildAdminCatalogQueryParams"),
      extractFunction(APP_SOURCE, "claimAdminCatalogRequest"),
      extractFunction(APP_SOURCE, "adminCatalogRequestOwnerIsCurrent"),
      extractFunction(APP_SOURCE, "releaseAdminCatalogRequest"),
      extractFunction(APP_SOURCE, "loadAdminCatalog"),
    ].join("\n"),
    context,
  );

  const older = vm.runInContext("loadAdminCatalog()", context);
  context.adminCatalogState.q = "newer";
  const newer = vm.runInContext("loadAdminCatalog()", context);
  pending[1].resolve(response({ marker: "newer", items: [] }));
  await newer;
  pending[0].resolve(response({ marker: "older", items: [] }));
  await older;
  assert.deepEqual(rendered, ["newer"]);
});

test("single-item publication ownership prevents duplicate activation", () => {
  const context = {
    Object,
    Boolean,
    adminPublicationRequestToken: 0,
    adminCatalogState: { publishOwners: new Map() },
  };
  context.globalThis = context;
  vm.createContext(context);
  vm.runInContext(
    [
      extractFunction(APP_SOURCE, "publicationOwnerIsCurrent"),
      extractFunction(APP_SOURCE, "claimPublicationRequest"),
      extractFunction(APP_SOURCE, "releasePublicationRequest"),
    ].join("\n"),
    context,
  );
  const first = vm.runInContext('claimPublicationRequest("media-1", null)', context);
  const duplicate = vm.runInContext('claimPublicationRequest("media-1", null)', context);
  assert.ok(first);
  assert.equal(duplicate, null);
  assert.equal(vm.runInContext("publicationOwnerIsCurrent(adminCatalogState.publishOwners.get('media-1'))", context), true);
  assert.equal(vm.runInContext("releasePublicationRequest(adminCatalogState.publishOwners.get('media-1'))", context), true);
});

test("publication UI waits for server truth and supports bounded failure recovery", () => {
  const publish = extractFunction(APP_SOURCE, "publishAdminMediaItem");
  assert.match(publish, /method: "PUT"/);
  assert.match(publish, /framenestMutationHeaders/);
  assert.match(publish, /claimPublicationRequest/);
  assert.match(publish, /aria-busy/);
  assert.match(publish, /if \(response\.ok\)/);
  assert.match(publish, /await loadAdminCatalog/);
  assert.match(publish, /response\.status === 409/);
  assert.match(publish, /item\.publication_ready = false/);
  assert.match(publish, /kind: "readiness"/);
  assert.match(publish, /response\.status === 401 \|\| response\.status === 403/);
  assert.match(publish, /kind: "authorization"/);
  assert.match(publish, /retryable: response\.status >= 500/);
  assert.match(publish, /retryable: true/);
  assert.doesNotMatch(publish.slice(0, publish.indexOf("if (response.ok)")), /published\./);
});

test("admin states use literal text and non-color icons without claiming AI application", () => {
  for (const label of [
    "Ready to publish",
    "Incomplete metadata",
    "AI suggestion ready",
    "Analysis queued",
    "Analysis failed",
    "Published",
    "Processed",
  ]) {
    assert.ok(APP_SOURCE.includes(label), `missing ${label}`);
  }
  assert.equal(APP_SOURCE.includes("AI applied"), false);
  assert.match(extractFunction(APP_SOURCE, "createAdminStateBadge"), /aria-hidden/);
  assert.match(extractFunction(APP_SOURCE, "renderAdminMediaItem"), /readyForPublication/);
});

test("Inspect reuses Details through a path-redacted adapter", () => {
  const renderItem = extractFunction(APP_SOURCE, "renderAdminMediaItem");
  const adapter = extractFunction(APP_SOURCE, "safeAdminDetailsItem");
  assert.match(renderItem, /openDetailsDialog\(safeAdminDetailsItem\(item\), inspectButton\)/);
  assert.match(adapter, /relative_path: "Local catalog location"/);
  assert.doesNotMatch(adapter, /location\.relative_path/);
});

test("admin controls expose loading empty error retry search filters and deterministic pagination", () => {
  for (const id of [
    "admin-media-search",
    "admin-media-publication-filter",
    "admin-media-readiness-filter",
    "admin-media-analysis-filter",
    "admin-media-refresh-button",
    "admin-media-loading",
    "admin-media-empty",
    "admin-media-error",
    "admin-media-retry-button",
    "admin-media-prev-button",
    "admin-media-next-button",
  ]) {
    assert.ok(INDEX_SOURCE.includes(`id="${id}"`), `missing ${id}`);
  }
  const params = extractFunction(APP_SOURCE, "buildAdminCatalogQueryParams");
  for (const key of ["q", "publication", "readiness", "analysis", "limit", "offset"]) {
    assert.match(params, new RegExp(`"${key}"`));
  }
});

test("responsive source contracts cover exact stacked wrapping and full-grid ranges", () => {
  assert.match(STYLES_SOURCE, /@media \(max-width: 720px\)/);
  assert.match(STYLES_SOURCE, /@media \(min-width: 721px\) and \(max-width: 1023px\)/);
  assert.match(STYLES_SOURCE, /@media \(min-width: 1024px\)/);
  assert.match(STYLES_SOURCE, /\.admin-media-row \{[\s\S]*?min-width: 0/);
  assert.match(STYLES_SOURCE, /\.admin-media-browser \{[\s\S]*?overflow: hidden/);
  assert.match(STYLES_SOURCE, /min-height: 44px/);
});

test("accessibility contracts include semantic rows, live status, focus recovery, and reduced motion", () => {
  assert.match(INDEX_SOURCE, /id="admin-media-results"[\s\S]*?role="table"/);
  assert.match(INDEX_SOURCE, /id="admin-media-action-status"[\s\S]*?aria-live="polite"/);
  assert.match(extractFunction(APP_SOURCE, "renderAdminMediaItem"), /setAttribute\("role", "row"\)/);
  assert.match(extractFunction(APP_SOURCE, "loadAdminCatalog"), /adminMediaHeading\.focus\(\)/);
  assert.match(STYLES_SOURCE, /\.admin-media-row:hover,\n\.admin-media-row:focus-within/);
  assert.match(STYLES_SOURCE, /@media \(prefers-reduced-motion: reduce\)/);
});
