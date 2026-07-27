const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");

const APP_PATH = path.resolve(__dirname, "../src/framenest/adapters/api/web/app.js");
const STYLES_PATH = path.resolve(__dirname, "../src/framenest/adapters/api/web/styles.css");
const INDEX_PATH = path.resolve(__dirname, "../src/framenest/adapters/api/web/index.html");
const APP_SOURCE = fs.readFileSync(APP_PATH, "utf8");
const STYLES_SOURCE = fs.readFileSync(STYLES_PATH, "utf8");
const INDEX_SOURCE = fs.readFileSync(INDEX_PATH, "utf8");

function extractFunction(source, name) {
  const markers = [`async function ${name}(`, `function ${name}(`];
  let start = -1;
  for (const marker of markers) {
    start = source.indexOf(marker);
    if (start !== -1) break;
  }
  assert.notEqual(start, -1, `missing production function ${name}`);
  let depth = 0;
  let quote = null;
  let escaped = false;
  let lineComment = false;
  let blockComment = false;
  const bodyStart = source.indexOf("{", start);
  for (let index = bodyStart; index < source.length; index += 1) {
    const character = source[index];
    const next = source[index + 1];
    if (lineComment) {
      if (character === "\n") lineComment = false;
      continue;
    }
    if (blockComment) {
      if (character === "*" && next === "/") {
        blockComment = false;
        index += 1;
      }
      continue;
    }
    if (quote) {
      if (escaped) escaped = false;
      else if (character === "\\") escaped = true;
      else if (character === quote) quote = null;
      continue;
    }
    if (character === "/" && next === "/") {
      lineComment = true;
      index += 1;
      continue;
    }
    if (character === "/" && next === "*") {
      blockComment = true;
      index += 1;
      continue;
    }
    if (character === '"' || character === "'" || character === "`") {
      quote = character;
      continue;
    }
    if (character === "{") depth += 1;
    if (character === "}") {
      depth -= 1;
      if (depth === 0) return source.slice(start, index + 1);
    }
  }
  throw new Error(`unterminated production function ${name}`);
}

function flushMicrotasks() {
  return new Promise((resolve) => setImmediate(resolve));
}

async function flushAll() {
  for (let index = 0; index < 40; index += 1) {
    await flushMicrotasks();
  }
}

function response(payload, status = 200) {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: async () => payload,
  };
}

class FakeElement {
  constructor(tagName) {
    this.tagName = String(tagName).toUpperCase();
    this.children = [];
    this.parentNode = null;
    this.dataset = {};
    this.attributes = new Map();
    this.listeners = new Map();
    this.className = "";
    this.hidden = false;
    this.disabled = false;
    this.textContent = "";
    this.title = "";
    this.isConnected = true;
  }

  setAttribute(name, value) {
    this.attributes.set(String(name).toLowerCase(), String(value));
  }

  getAttribute(name) {
    const key = String(name).toLowerCase();
    return this.attributes.has(key) ? this.attributes.get(key) : null;
  }

  removeAttribute(name) {
    this.attributes.delete(String(name).toLowerCase());
  }

  addEventListener(type, listener) {
    if (!this.listeners.has(type)) this.listeners.set(type, []);
    this.listeners.get(type).push(listener);
  }

  dispatchEvent(event) {
    if (!event.target) event.target = this;
    if (typeof event.preventDefault !== "function") event.preventDefault = () => {};
    if (typeof event.stopPropagation !== "function") event.stopPropagation = () => {};
    for (const listener of [...(this.listeners.get(event.type) || [])]) listener(event);
    return true;
  }

  appendChild(node) {
    node.parentNode = this;
    this.children.push(node);
    return node;
  }

  replaceChildren(...nodes) {
    this.children.forEach((node) => {
      node.parentNode = null;
    });
    this.children = [];
    nodes.forEach((node) => this.appendChild(node));
  }

  replaceWith(node) {
    if (!this.parentNode) return;
    const siblings = this.parentNode.children;
    const index = siblings.indexOf(this);
    if (index === -1) return;
    siblings.splice(index, 1, node);
    node.parentNode = this.parentNode;
    this.parentNode = null;
  }

  querySelector(selector) {
    const match = (node) => {
      if (selector.startsWith(".") && String(node.className || "").split(/\s+/).includes(selector.slice(1))) {
        return node;
      }
      for (const child of node.children || []) {
        const found = match(child);
        if (found) return found;
      }
      return null;
    };
    return match(this);
  }

  querySelectorAll(selector) {
    const matches = [];
    const walk = (node) => {
      if (selector.startsWith(".") && String(node.className || "").split(/\s+/).includes(selector.slice(1))) {
        matches.push(node);
      }
      if (selector.startsWith("[data-media-id]") && node.dataset && node.dataset.mediaId) {
        matches.push(node);
      }
      for (const child of node.children || []) walk(child);
    };
    walk(this);
    return matches;
  }

  closest(selector) {
    let node = this;
    while (node) {
      if (selector.startsWith(".") && String(node.className || "").split(/\s+/).includes(selector.slice(1))) {
        return node;
      }
      node = node.parentNode;
    }
    return null;
  }

  focus() {}
}

function createFlowHarness({ confirmAccepted = true } = {}) {
  const fetchCalls = [];
  const routes = new Map();
  const catalogResults = new FakeElement("div");
  catalogResults.className = "catalog-results";
  const document = {
    createElement(tagName) {
      return new FakeElement(tagName);
    },
    activeElement: null,
    querySelector() {
      return null;
    },
  };
  const context = {
    document,
    console,
    Set,
    Map,
    Object,
    Array,
    String,
    Boolean,
    Number,
    Math,
    Promise,
    JSON,
    encodeURIComponent,
    aiCapability: { available: true },
    identityState: {
      available: true,
      capabilities: new Set(["analysis.run", "metadata.canonical.write", "gallery.read"]),
    },
    cardAiQuickActionByMediaId: new Map(),
    CARD_AI_QUICK_ACTION_LOCKED: new Set(["confirming", "analyzing", "applying"]),
    canonicalTagDefinitions: [],
    canonicalTagsLoaded: true,
    catalogResults,
    catalogState: { tagKeys: [] },
    detailsCurrentItem: null,
    detailsDialogTitle: new FakeElement("h2"),
    detailsTagsContainer: new FakeElement("div"),
    detailsDescription: new FakeElement("p"),
    automaticAnalysisByMediaId: new Map(),
    MEDIA_CATALOG_ENDPOINT: "/api/media",
    CANONICAL_TAGS_ENDPOINT: "/api/canonical-tags",
    MAX_METADATA_TAGS: 32,
    openStatusDialogCalls: [],
    openStatusDialog(tab) {
      context.openStatusDialogCalls.push(tab);
    },
    async requestConfirmation() {
      return confirmAccepted;
    },
    identityHasCapability(capability) {
      if (!context.identityState.available) return true;
      return context.identityState.capabilities.has(capability);
    },
    framenestMutationHeaders(headers) {
      return Object.assign({ "X-FrameNest-Request": "1" }, headers);
    },
    mediaAiSuggestionEndpoint(mediaId, locationId) {
      return `/api/media/${mediaId}/locations/${locationId}/ai-suggestion-preview`;
    },
    metadataEndpoint(mediaId) {
      return `/api/media/${mediaId}/metadata`;
    },
    deriveCatalogFallbackTitle(item) {
      return item.display_title || "Untitled";
    },
    activateDetailsTagFilter() {},
    toggleCatalogCardTagFilter() {},
    catalogTagActivationShouldFocusChip() {
      return false;
    },
    normalizedTagDisplayName(value) {
      return String(value || "").trim();
    },
    tagDisplayNameError() {
      return null;
    },
    uniqueTagKeyForDisplayName(displayName) {
      return String(displayName).toLowerCase().replace(/\s+/g, "-");
    },
    findTagByDisplayName(displayName) {
      const normalized = String(displayName).toLocaleLowerCase();
      return context.canonicalTagDefinitions.find(
        (tag) => tag.display_name.toLocaleLowerCase() === normalized,
      ) || null;
    },
    async ensureCanonicalTags() {
      return true;
    },
    async loadCatalogTags() {
      return true;
    },
    async ensureMetadataTagKey(displayName) {
      const existing = context.findTagByDisplayName(displayName);
      if (existing) return existing.key;
      const key = context.uniqueTagKeyForDisplayName(displayName);
      const endpoint = context.CANONICAL_TAGS_ENDPOINT;
      const result = await context.fetch(endpoint, {
        method: "POST",
        headers: context.framenestMutationHeaders({
          Accept: "application/json",
          "Content-Type": "application/json",
        }),
        body: JSON.stringify({ key, display_name: displayName }),
      });
      const payload = await result.json();
      if (!result.ok) throw new Error("Tag could not be added.");
      context.canonicalTagDefinitions.push(payload.tag);
      return payload.tag.key;
    },
    async metadataTagKeysFromSuggestion(tags) {
      const tagKeys = [];
      for (const tag of tags) {
        const key = await context.ensureMetadataTagKey(tag);
        if (!tagKeys.includes(key)) tagKeys.push(key);
      }
      return tagKeys;
    },
    aiSuggestionFromPayload(payload) {
      const suggestion = payload.suggestion || {};
      return {
        title: String(suggestion.title || ""),
        description: String(suggestion.description || ""),
        tags: Array.isArray(suggestion.tags) ? suggestion.tags.map((tag) => String(tag)) : [],
        suggestedFilename: String(suggestion.suggested_filename || ""),
      };
    },
    aiSuggestionErrorMessage(payload) {
      const code = payload && payload.error ? payload.error.code : "";
      if (code === "AI_PROVIDER_UNAVAILABLE") return "AI provider is not available.";
      return "AI analysis failed.";
    },
    selectSupportedAvailableLocation(item) {
      if (!item.locations || item.locations.length === 0) return null;
      if (
        item.media_kind !== "video"
        && item.media_kind !== "animated_image"
        && item.media_kind !== "image"
      ) {
        return null;
      }
      return item.locations.find((location) => location.availability === "available" && location.location_id) || null;
    },
    async fetch(url, options = {}) {
      const method = options.method || "GET";
      fetchCalls.push({
        url: String(url),
        method,
        headers: options.headers || {},
        body: options.body || null,
      });
      const key = `${method} ${url}`;
      if (!routes.has(key)) {
        return response({ error: { code: "NOT_FOUND", message: "missing route" } }, 404);
      }
      const queued = routes.get(key);
      const next = Array.isArray(queued) ? queued.shift() : queued;
      return typeof next === "function" ? next(options) : next;
    },
  };
  context.window = context;
  const source = [
    extractFunction(APP_SOURCE, "cardNeedsMetadata"),
    extractFunction(APP_SOURCE, "cardAiQuickActionEligible"),
    extractFunction(APP_SOURCE, "getCardAiQuickAction"),
    extractFunction(APP_SOURCE, "setCardAiQuickActionController"),
    extractFunction(APP_SOURCE, "cardAiQuickActionIsLocked"),
    extractFunction(APP_SOURCE, "cardAiQuickActionStatusMessage"),
    extractFunction(APP_SOURCE, "setCardAnalyzeButtonState"),
    extractFunction(APP_SOURCE, "reconcileCatalogCardAiQuickActions"),
    extractFunction(APP_SOURCE, "suggestionIsUsableForCanonicalSave"),
    extractFunction(APP_SOURCE, "renderCatalogCardTags"),
    extractFunction(APP_SOURCE, "applySavedAiMetadataToCatalogSurfaces"),
    extractFunction(APP_SOURCE, "handleAnalyzeCatalogCard"),
  ].join("\n");
  vm.createContext(context);
  vm.runInContext(source, context);
  return {
    context,
    fetchCalls,
    catalogResults,
    enqueue(method, url, value) {
      const key = `${method} ${url}`;
      if (!routes.has(key)) routes.set(key, []);
      const bucket = routes.get(key);
      if (Array.isArray(bucket)) bucket.push(value);
      else routes.set(key, value);
    },
  };
}

function sampleItem(overrides = {}) {
  return {
    media_id: "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
    media_kind: "image",
    display_title: "Sunset Still",
    content_category: "general",
    acquisition_source: "manual_upload",
    tags: [{ key: "nature", display_name: "Nature" }],
    locations: [{
      location_id: "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb",
      availability: "available",
      relative_path: "stills/sunset.jpg",
    }],
    ...overrides,
  };
}

test("brain eligibility requires both capabilities, supported location, and excludes movies", () => {
  const { context } = createFlowHarness();
  const item = sampleItem();
  assert.equal(context.cardAiQuickActionEligible(item), true);

  context.identityState.capabilities.delete("metadata.canonical.write");
  assert.equal(context.cardAiQuickActionEligible(item), false);
  context.identityState.capabilities.add("metadata.canonical.write");
  context.identityState.capabilities.delete("analysis.run");
  assert.equal(context.cardAiQuickActionEligible(item), false);
  context.identityState.capabilities.add("analysis.run");

  assert.equal(context.cardAiQuickActionEligible(sampleItem({ content_category: "movie" })), false);
  assert.equal(context.cardAiQuickActionEligible(sampleItem({
    media_kind: "animated_image",
    tags: [{ key: "funny", display_name: "Funny" }],
  })), true);
  assert.equal(context.cardAiQuickActionEligible(sampleItem({
    media_kind: "video",
    content_category: "meme",
    display_title: "Clip",
  })), true);
  assert.equal(context.cardAiQuickActionEligible(sampleItem({
    display_title: "Populated",
    tags: [
      { key: "alpha", display_name: "Alpha" },
      { key: "beta", display_name: "Beta" },
    ],
  })), true);
  assert.equal(context.cardNeedsMetadata(sampleItem({ tags: [{ key: "nature", display_name: "Nature" }] })), false);
  assert.equal(context.cardAiQuickActionEligible(sampleItem({ tags: [{ key: "nature", display_name: "Nature" }] })), true);
});

test("ordinary and missing-capability identities do not unlock the brain eligibility helper", () => {
  const { context } = createFlowHarness();
  context.identityState.capabilities = new Set(["gallery.read"]);
  assert.equal(context.cardAiQuickActionEligible(sampleItem()), false);
  context.identityState.available = true;
  context.identityState.capabilities = new Set();
  assert.equal(context.cardAiQuickActionEligible(sampleItem()), false);
});

test("source wiring gates brain on both capabilities and excludes cardNeedsMetadata as visibility rule", () => {
  const cardBody = extractFunction(APP_SOURCE, "renderCatalogCard");
  const handleBody = extractFunction(APP_SOURCE, "handleAnalyzeCatalogCard");
  assert.ok(cardBody.includes("cardAiQuickActionEligible(item)"));
  assert.equal(cardBody.includes("cardNeedsMetadata(item)"), false);
  assert.ok(APP_SOURCE.includes('identityHasCapability("analysis.run")'));
  assert.ok(APP_SOURCE.includes('identityHasCapability("metadata.canonical.write")'));
  assert.ok(APP_SOURCE.includes('(item.content_category || "general") !== "movie"'));
  assert.ok(handleBody.includes("await requestConfirmation({"));
  assert.ok(handleBody.includes('title: "Analyze and save with AI?"'));
  assert.ok(handleBody.includes("will replace the current canonical values"));
  assert.ok(handleBody.includes("framenestMutationHeaders("));
  assert.ok(handleBody.includes("metadataTagKeysFromSuggestion(suggestion.tags)"));
  assert.ok(handleBody.includes("fetch(metadataEndpoint(mediaId)"));
  assert.ok(handleBody.includes('method: "PUT"'));
  assert.equal(handleBody.includes("handleOpenMetadataWorkspace"), false);
  assert.ok(handleBody.includes("applySavedAiMetadataToCatalogSurfaces(item, savePayload.metadata)"));
  assert.ok(handleBody.includes('state: "failed_save"'));
  assert.ok(handleBody.includes('state: "failed_analysis"'));
  assert.ok(handleBody.includes("suggestionIsUsableForCanonicalSave(suggestion)"));
  assert.ok(handleBody.includes("cardAiQuickActionIsLocked(mediaId)"));
  assert.ok(handleBody.includes("content_category: metadataPayload.content_category"));
  assert.ok(handleBody.includes("acquisition_source: metadataPayload.acquisition_source"));
  assert.ok(handleBody.includes("genres: Array.isArray(metadataPayload.genres)"));
});

test("Edit Analyze remains draft-only and does not auto-save", () => {
  const analyzeBody = extractFunction(APP_SOURCE, "handleAnalyzeMetadataByAi");
  assert.ok(analyzeBody.includes("applyResolvedAiSuggestionToMetadataWorkspace(suggestion, tagKeys)"));
  assert.equal(analyzeBody.includes('method: "PUT"'), false);
  assert.equal(analyzeBody.includes("applySavedAiMetadataToCatalogSurfaces"), false);
  assert.ok(analyzeBody.includes("await requestConfirmation({"));
});

test("unavailable provider opens status without preview request", async () => {
  const harness = createFlowHarness();
  harness.context.aiCapability.available = false;
  const item = sampleItem();
  const button = new FakeElement("button");
  button.dataset.mediaTitle = item.display_title;
  const card = new FakeElement("article");
  card.className = "catalog-card";
  const status = new FakeElement("p");
  status.className = "catalog-card__analysis-status";
  card.appendChild(button);
  card.appendChild(status);
  await harness.context.handleAnalyzeCatalogCard(item, button);
  await flushAll();
  assert.deepEqual(harness.context.openStatusDialogCalls, ["ai"]);
  assert.equal(harness.fetchCalls.length, 0);
  assert.equal(button.dataset.analysisState, "unavailable");
});

test("confirmation cancel performs no mutation", async () => {
  const harness = createFlowHarness({ confirmAccepted: false });
  const item = sampleItem();
  const button = new FakeElement("button");
  button.dataset.mediaTitle = item.display_title;
  const card = new FakeElement("article");
  card.className = "catalog-card";
  card.appendChild(button);
  card.appendChild(Object.assign(new FakeElement("p"), { className: "catalog-card__analysis-status" }));
  await harness.context.handleAnalyzeCatalogCard(item, button);
  await flushAll();
  assert.equal(harness.fetchCalls.length, 0);
  assert.equal(button.dataset.analysisState, "idle");
});

test("one acceptance creates one preview and locks through metadata save", async () => {
  const harness = createFlowHarness();
  const item = sampleItem({ tags: [] });
  harness.context.canonicalTagDefinitions = [{ key: "nature", display_name: "Nature" }];
  const mediaId = item.media_id;
  const locationId = item.locations[0].location_id;
  harness.enqueue(
    "POST",
    `/api/media/${mediaId}/locations/${locationId}/ai-suggestion-preview`,
    response({
      suggestion: {
        title: "AI Sunset",
        description: "Warm light",
        tags: ["Nature"],
        suggested_filename: "sunset.jpg",
      },
    }),
  );
  harness.enqueue(
    "GET",
    `/api/media/${mediaId}/metadata`,
    response({
      display_title: "Sunset Still",
      description: "old",
      tags: [],
      content_category: "meme",
      acquisition_source: "library_scan",
      genres: ["Documentary"],
    }),
  );
  harness.enqueue(
    "PUT",
    `/api/media/${mediaId}/metadata`,
    response({
      status: "saved",
      metadata: {
        display_title: "AI Sunset",
        description: "Warm light",
        tags: [{ key: "nature", display_name: "Nature" }],
        content_category: "meme",
        acquisition_source: "library_scan",
        genres: ["Documentary"],
      },
    }),
  );
  const button = new FakeElement("button");
  button.dataset.mediaTitle = item.display_title;
  const card = new FakeElement("article");
  card.className = "catalog-card";
  card.dataset.mediaId = mediaId;
  const titleButton = new FakeElement("button");
  titleButton.className = "catalog-card__title-button";
  titleButton.textContent = item.display_title;
  const tags = new FakeElement("div");
  tags.className = "catalog-card__tags";
  const status = new FakeElement("p");
  status.className = "catalog-card__analysis-status";
  card.appendChild(titleButton);
  card.appendChild(button);
  card.appendChild(tags);
  card.appendChild(status);
  harness.catalogResults.appendChild(card);

  const first = harness.context.handleAnalyzeCatalogCard(item, button);
  const second = harness.context.handleAnalyzeCatalogCard(item, button);
  await Promise.all([first, second]);
  await flushAll();

  const previewCalls = harness.fetchCalls.filter((call) => call.url.includes("ai-suggestion-preview"));
  assert.equal(previewCalls.length, 1);
  assert.equal(previewCalls[0].headers["X-FrameNest-Request"], "1");
  const putCalls = harness.fetchCalls.filter((call) => call.method === "PUT");
  assert.equal(putCalls.length, 1);
  assert.equal(putCalls[0].headers["X-FrameNest-Request"], "1");
  const putBody = JSON.parse(putCalls[0].body);
  assert.equal(putBody.content_category, "meme");
  assert.equal(putBody.acquisition_source, "library_scan");
  assert.deepEqual(putBody.genres, ["Documentary"]);
  assert.equal(button.dataset.analysisState, "saved");
  assert.equal(status.textContent, "AI metadata saved");
  assert.equal(titleButton.textContent, "AI Sunset");
  assert.equal(harness.fetchCalls.some((call) => call.method === "POST" && call.url === "/api/canonical-tags"), false);
});

test("existing tags skip canonical POST while missing tags create definitions before PUT", async () => {
  const harness = createFlowHarness();
  const item = sampleItem({ tags: [] });
  harness.context.canonicalTagDefinitions = [{ key: "nature", display_name: "Nature" }];
  const mediaId = item.media_id;
  const locationId = item.locations[0].location_id;
  harness.enqueue(
    "POST",
    `/api/media/${mediaId}/locations/${locationId}/ai-suggestion-preview`,
    response({
      suggestion: {
        title: "AI Sunset",
        description: "Warm light",
        tags: ["Nature", "Golden Hour"],
        suggested_filename: "sunset.jpg",
      },
    }),
  );
  harness.enqueue(
    "POST",
    "/api/canonical-tags",
    response({ status: "created", tag: { key: "golden-hour", display_name: "Golden Hour" } }, 201),
  );
  harness.enqueue(
    "GET",
    `/api/media/${mediaId}/metadata`,
    response({
      display_title: "Sunset Still",
      description: null,
      tags: [],
      content_category: "general",
      acquisition_source: "unknown",
      genres: [],
    }),
  );
  harness.enqueue(
    "PUT",
    `/api/media/${mediaId}/metadata`,
    response({
      status: "saved",
      metadata: {
        display_title: "AI Sunset",
        description: "Warm light",
        tags: [
          { key: "nature", display_name: "Nature" },
          { key: "golden-hour", display_name: "Golden Hour" },
        ],
        content_category: "general",
        acquisition_source: "unknown",
        genres: [],
      },
    }),
  );
  const button = new FakeElement("button");
  button.dataset.mediaTitle = item.display_title;
  const card = new FakeElement("article");
  card.className = "catalog-card";
  card.dataset.mediaId = mediaId;
  card.appendChild(button);
  card.appendChild(Object.assign(new FakeElement("p"), { className: "catalog-card__analysis-status" }));
  card.appendChild(Object.assign(new FakeElement("div"), { className: "catalog-card__tags" }));
  card.appendChild(Object.assign(new FakeElement("button"), { className: "catalog-card__title-button" }));
  harness.catalogResults.appendChild(card);

  await harness.context.handleAnalyzeCatalogCard(item, button);
  await flushAll();

  const tagPosts = harness.fetchCalls.filter((call) => call.method === "POST" && call.url === "/api/canonical-tags");
  assert.equal(tagPosts.length, 1);
  assert.equal(JSON.parse(tagPosts[0].body).display_name, "Golden Hour");
  assert.equal(tagPosts[0].headers["X-FrameNest-Request"], "1");
  assert.equal(button.dataset.analysisState, "saved");
});

test("preview failure creates no tags and saves no metadata", async () => {
  const harness = createFlowHarness();
  const item = sampleItem();
  const mediaId = item.media_id;
  const locationId = item.locations[0].location_id;
  harness.enqueue(
    "POST",
    `/api/media/${mediaId}/locations/${locationId}/ai-suggestion-preview`,
    response({ error: { code: "AI_PROVIDER_UNAVAILABLE", message: "down" } }, 503),
  );
  const button = new FakeElement("button");
  button.dataset.mediaTitle = item.display_title;
  const card = new FakeElement("article");
  card.className = "catalog-card";
  card.appendChild(button);
  card.appendChild(Object.assign(new FakeElement("p"), { className: "catalog-card__analysis-status" }));
  await harness.context.handleAnalyzeCatalogCard(item, button);
  await flushAll();
  assert.equal(harness.fetchCalls.length, 1);
  assert.equal(button.dataset.analysisState, "failed_analysis");
});

test("tag creation failure prevents metadata PUT", async () => {
  const harness = createFlowHarness();
  const item = sampleItem({ tags: [] });
  harness.context.canonicalTagDefinitions = [];
  const mediaId = item.media_id;
  const locationId = item.locations[0].location_id;
  harness.enqueue(
    "POST",
    `/api/media/${mediaId}/locations/${locationId}/ai-suggestion-preview`,
    response({
      suggestion: {
        title: "AI Sunset",
        description: "Warm light",
        tags: ["Brand New"],
        suggested_filename: "sunset.jpg",
      },
    }),
  );
  harness.enqueue(
    "POST",
    "/api/canonical-tags",
    response({ error: { code: "CANONICAL_TAG_OPERATION_FAILED", message: "nope" } }, 500),
  );
  const button = new FakeElement("button");
  button.dataset.mediaTitle = item.display_title;
  const card = new FakeElement("article");
  card.className = "catalog-card";
  card.appendChild(button);
  card.appendChild(Object.assign(new FakeElement("p"), { className: "catalog-card__analysis-status" }));
  await harness.context.handleAnalyzeCatalogCard(item, button);
  await flushAll();
  assert.equal(harness.fetchCalls.some((call) => call.method === "PUT"), false);
  assert.equal(button.dataset.analysisState, "failed_save");
  assert.match(card.querySelector(".catalog-card__analysis-status").textContent, /could not be saved/);
});

test("metadata PUT failure is failed_save and does not claim success after tag definitions may exist", async () => {
  const harness = createFlowHarness();
  const item = sampleItem({ tags: [] });
  harness.context.canonicalTagDefinitions = [];
  const mediaId = item.media_id;
  const locationId = item.locations[0].location_id;
  harness.enqueue(
    "POST",
    `/api/media/${mediaId}/locations/${locationId}/ai-suggestion-preview`,
    response({
      suggestion: {
        title: "AI Sunset",
        description: "Warm light",
        tags: ["Brand New"],
        suggested_filename: "sunset.jpg",
      },
    }),
  );
  harness.enqueue(
    "POST",
    "/api/canonical-tags",
    response({ status: "created", tag: { key: "brand-new", display_name: "Brand New" } }, 201),
  );
  harness.enqueue(
    "GET",
    `/api/media/${mediaId}/metadata`,
    response({
      display_title: "Sunset Still",
      description: "keep me",
      tags: [],
      content_category: "general",
      acquisition_source: "unknown",
      genres: [],
    }),
  );
  harness.enqueue(
    "PUT",
    `/api/media/${mediaId}/metadata`,
    response({ error: { code: "MEDIA_METADATA_OPERATION_FAILED", message: "failed" } }, 500),
  );
  const button = new FakeElement("button");
  button.dataset.mediaTitle = item.display_title;
  const card = new FakeElement("article");
  card.className = "catalog-card";
  const status = Object.assign(new FakeElement("p"), { className: "catalog-card__analysis-status" });
  card.appendChild(button);
  card.appendChild(status);
  await harness.context.handleAnalyzeCatalogCard(item, button);
  await flushAll();
  assert.equal(button.dataset.analysisState, "failed_save");
  assert.equal(
    status.textContent,
    "AI metadata could not be saved. Existing media metadata was not replaced.",
  );
  assert.equal(harness.context.canonicalTagDefinitions.some((tag) => tag.key === "brand-new"), true);
});

test("stale request token does not apply another media response", async () => {
  const harness = createFlowHarness();
  const item = sampleItem();
  const mediaId = item.media_id;
  const locationId = item.locations[0].location_id;
  let resolvePreview;
  harness.enqueue(
    "POST",
    `/api/media/${mediaId}/locations/${locationId}/ai-suggestion-preview`,
    () => new Promise((resolve) => {
      resolvePreview = () => resolve(response({
        suggestion: {
          title: "Late",
          description: "Late",
          tags: ["Nature"],
          suggested_filename: "late.jpg",
        },
      }));
    }),
  );
  const button = new FakeElement("button");
  button.dataset.mediaTitle = item.display_title;
  const card = new FakeElement("article");
  card.className = "catalog-card";
  card.appendChild(button);
  card.appendChild(Object.assign(new FakeElement("p"), { className: "catalog-card__analysis-status" }));
  const pending = harness.context.handleAnalyzeCatalogCard(item, button);
  await flushAll();
  harness.context.setCardAiQuickActionController(mediaId, { state: "analyzing", requestToken: 999 });
  resolvePreview();
  await pending;
  await flushAll();
  assert.equal(harness.fetchCalls.some((call) => call.method === "PUT"), false);
  assert.equal(button.dataset.analysisState, "analyzing");
});

test("invalid suggestion does not erase metadata via PUT", async () => {
  const harness = createFlowHarness();
  const item = sampleItem();
  const mediaId = item.media_id;
  const locationId = item.locations[0].location_id;
  harness.enqueue(
    "POST",
    `/api/media/${mediaId}/locations/${locationId}/ai-suggestion-preview`,
    response({ suggestion: { title: "", description: "", tags: [], suggested_filename: "" } }),
  );
  const button = new FakeElement("button");
  button.dataset.mediaTitle = item.display_title;
  const card = new FakeElement("article");
  card.className = "catalog-card";
  card.appendChild(button);
  card.appendChild(Object.assign(new FakeElement("p"), { className: "catalog-card__analysis-status" }));
  await harness.context.handleAnalyzeCatalogCard(item, button);
  await flushAll();
  assert.equal(harness.fetchCalls.some((call) => call.method === "PUT"), false);
  assert.equal(button.dataset.analysisState, "failed_analysis");
});

test("capability reconciliation updates aria-disabled without remounting catalog cards", () => {
  const harness = createFlowHarness();
  const button = new FakeElement("button");
  button.className = "catalog-card__action--analyze";
  button.dataset.analysisState = "idle";
  button.dataset.mediaTitle = "Sunset Still";
  button.setAttribute("aria-disabled", "true");
  harness.catalogResults.appendChild(button);
  harness.context.aiCapability.available = true;
  harness.context.reconcileCatalogCardAiQuickActions();
  assert.equal(button.getAttribute("aria-disabled"), "false");
  assert.equal(harness.catalogResults.children.length, 1);
  assert.equal(harness.catalogResults.children[0], button);
});

test("brain click handlers stop propagation in source and do not open details or playback helpers", () => {
  const cardBody = extractFunction(APP_SOURCE, "renderCatalogCard");
  const handleBody = extractFunction(APP_SOURCE, "handleAnalyzeCatalogCard");
  assert.ok(cardBody.includes("event.stopPropagation()"));
  assert.equal(handleBody.includes("activateCardPlayback"), false);
  assert.equal(handleBody.includes("openDetailsDialog"), false);
  assert.equal(handleBody.includes("handleOpenMetadataWorkspace"), false);
});

test("Edit Analyze primary button uses near-white surface without black-green slab", () => {
  assert.ok(STYLES_SOURCE.includes(".metadata-dialog__footer .metadata-ai-analyze-button"));
  assert.ok(STYLES_SOURCE.includes("background: #f5f8f5"));
  assert.ok(STYLES_SOURCE.includes("color: #0c1a10"));
  assert.equal(STYLES_SOURCE.includes("linear-gradient(90deg, #0b2514, #00c853"), false);
  assert.equal(STYLES_SOURCE.includes("metadata-ai-analyzing"), false);
  assert.ok(STYLES_SOURCE.includes(".metadata-dialog__footer .metadata-ai-analyze-button[aria-busy=\"true\"]"));
  assert.ok(STYLES_SOURCE.includes(".metadata-dialog__footer .metadata-ai-analyze-button:disabled:not([aria-busy=\"true\"])"));
});

test("native metadata selects are styled and classification row stacks responsively", () => {
  assert.ok(INDEX_SOURCE.includes('class="metadata-classification-row"'));
  assert.ok(INDEX_SOURCE.includes('id="metadata-content-category"'));
  assert.ok(INDEX_SOURCE.includes('id="metadata-acquisition-source"'));
  assert.ok(STYLES_SOURCE.includes(".metadata-field select"));
  assert.ok(STYLES_SOURCE.includes("width: 100%"));
  assert.ok(STYLES_SOURCE.includes(".metadata-classification-row"));
  assert.ok(STYLES_SOURCE.includes("minmax(0, 1fr)"));
  assert.match(STYLES_SOURCE, /\.metadata-classification-row\s*\{[^}]*grid-template-columns:\s*1fr;/s);
});

test("quick-action mutations use the sole framenestMutationHeaders helper", () => {
  const handleBody = extractFunction(APP_SOURCE, "handleAnalyzeCatalogCard");
  const mutationSites = handleBody.match(/framenestMutationHeaders\(/g) || [];
  assert.ok(mutationSites.length >= 2);
  assert.equal(handleBody.includes('"X-FrameNest-Request": "1"'), false);
  assert.ok(APP_SOURCE.includes('function framenestMutationHeaders(headers)'));
  assert.ok(APP_SOURCE.includes('Object.assign({ "X-FrameNest-Request": "1" }, headers)'));
  assert.equal((APP_SOURCE.match(/function framenestMutationHeaders/g) || []).length, 1);
});
