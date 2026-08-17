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

function cssDeclarationsAfter(source, selector, offset = 0) {
  const selectorIndex = source.indexOf(selector, offset);
  assert.notEqual(selectorIndex, -1, `missing production CSS selector ${selector}`);
  const blockStart = source.indexOf("{", selectorIndex + selector.length);
  const blockEnd = source.indexOf("}", blockStart);
  assert.notEqual(blockStart, -1, `missing declaration block for ${selector}`);
  assert.notEqual(blockEnd, -1, `unterminated declaration block for ${selector}`);
  return Object.fromEntries(
    source
      .slice(blockStart + 1, blockEnd)
      .split(";")
      .map((declaration) => declaration.trim())
      .filter(Boolean)
      .map((declaration) => {
        const colon = declaration.indexOf(":");
        assert.notEqual(colon, -1, `invalid declaration ${declaration}`);
        return [
          declaration.slice(0, colon).trim(),
          declaration.slice(colon + 1).trim(),
        ];
      }),
  );
}

function catalogActionPresentation(pointer, reveal = false) {
  const baseOverlay = cssDeclarationsAfter(STYLES_SOURCE, ".catalog-card__actions--overlay");
  const fineMedia = STYLES_SOURCE.indexOf("@media (hover: hover) and (pointer: fine)");
  const coarseMedia = STYLES_SOURCE.indexOf("@media (hover: none), (pointer: coarse)");
  const presentation = {
    overlay: { ...baseOverlay },
    action: { opacity: "1", visibility: "visible", "pointer-events": "auto" },
  };

  if (pointer === "fine") {
    Object.assign(
      presentation.overlay,
      cssDeclarationsAfter(STYLES_SOURCE, ".catalog-card__actions--overlay", fineMedia),
    );
    Object.assign(
      presentation.action,
      cssDeclarationsAfter(
        STYLES_SOURCE,
        ".catalog-card__actions--overlay .catalog-card__action",
        fineMedia,
      ),
    );
    if (reveal) {
      Object.assign(
        presentation.overlay,
        cssDeclarationsAfter(
          STYLES_SOURCE,
          ".catalog-card:hover .catalog-card__actions--overlay",
          fineMedia,
        ),
      );
      Object.assign(
        presentation.action,
        cssDeclarationsAfter(
          STYLES_SOURCE,
          ".catalog-card:hover .catalog-card__action,\n"
            + "  .catalog-card:focus-within .catalog-card__action",
          fineMedia,
        ),
      );
    }
  } else {
    Object.assign(
      presentation.overlay,
      cssDeclarationsAfter(STYLES_SOURCE, ".catalog-card__actions--overlay", coarseMedia),
    );
    Object.assign(
      presentation.action,
      cssDeclarationsAfter(
        STYLES_SOURCE,
        ".catalog-card__actions--overlay .catalog-card__action",
        coarseMedia,
      ),
    );
  }

  return presentation;
}

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
    this.style = {};
    this._rect = { left: 0, top: 0, width: 200, height: 120 };
  }

  get classList() {
    const element = this;
    return {
      add(...tokens) {
        const current = new Set(String(element.className || "").split(/\s+/).filter(Boolean));
        tokens.forEach((token) => current.add(String(token)));
        element.className = [...current].join(" ");
      },
      remove(...tokens) {
        const current = new Set(String(element.className || "").split(/\s+/).filter(Boolean));
        tokens.forEach((token) => current.delete(String(token)));
        element.className = [...current].join(" ");
      },
      contains(token) {
        return String(element.className || "").split(/\s+/).includes(String(token));
      },
      toggle(token, force) {
        const has = this.contains(token);
        if (force === true || (force === undefined && !has)) this.add(token);
        else this.remove(token);
        return this.contains(token);
      },
    };
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

  removeEventListener(type, listener) {
    const listeners = this.listeners.get(type);
    if (!listeners) return;
    const index = listeners.indexOf(listener);
    if (index !== -1) listeners.splice(index, 1);
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
    node.isConnected = true;
    this.children.push(node);
    return node;
  }

  append(...nodes) {
    nodes.forEach((node) => this.appendChild(node));
  }

  replaceChildren(...nodes) {
    this.children.forEach((node) => {
      node.parentNode = null;
      node.isConnected = false;
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
    node.isConnected = true;
    this.parentNode = null;
    this.isConnected = false;
  }

  remove() {
    if (!this.parentNode) {
      this.isConnected = false;
      return;
    }
    const siblings = this.parentNode.children;
    const index = siblings.indexOf(this);
    if (index !== -1) siblings.splice(index, 1);
    this.parentNode = null;
    this.isConnected = false;
  }

  getBoundingClientRect() {
    return {
      left: this._rect.left,
      top: this._rect.top,
      width: this._rect.width,
      height: this._rect.height,
      right: this._rect.left + this._rect.width,
      bottom: this._rect.top + this._rect.height,
    };
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

  click() {
    if (this.disabled) return false;
    return this.dispatchEvent({ type: "click" });
  }
}

function createFlowHarness({ confirmAccepted = true, reducedMotion = true } = {}) {
  const fetchCalls = [];
  const routes = new Map();
  const catalogResults = new FakeElement("div");
  catalogResults.className = "catalog-results";
  const context = {
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
    setTimeout,
    clearTimeout,
    reducedMotion,
    prefersReducedMotion: reducedMotion,
    CATALOG_CARD_REFLOW_MS: 220,
    catalogCardReflowGeneration: 0,
    aiCapability: { available: true },
    aiCapabilityDiscoveryPending: false,
    identityState: {
      resolved: true,
      available: true,
      role: "admin",
      capabilities: new Set(["analysis.run", "metadata.canonical.write", "gallery.read"]),
    },
    cardAiQuickActionByMediaId: new Map(),
    CARD_AI_QUICK_ACTION_LOCKED: new Set(["confirming", "analyzing", "applying"]),
    canonicalTagDefinitions: [],
    canonicalTagsLoaded: true,
    catalogResults,
    catalogState: { tagKeys: [], collection: "", contentCategory: "", acquisitionSource: "", creatorAttributionKind: "", creatorStableId: "", creatorHandle: "" },
    PROCESSED_COLLECTION: "processed",
    detailsCurrentItem: null,
    detailsDialogTitle: new FakeElement("h2"),
    detailsTagsContainer: new FakeElement("div"),
    detailsDescription: new FakeElement("p"),
    automaticAnalysisByMediaId: new Map(),
    MEDIA_CATALOG_ENDPOINT: "/api/media",
    CANONICAL_TAGS_ENDPOINT: "/api/canonical-tags",
    MAX_METADATA_TAGS: 32,
    openStatusDialogCalls: [],
    confirmationCalls: 0,
    loadCatalog() {},
    syncCatalogFilterControls() {},
    advanceMetadataWorkspaceRevision() {},
    layoutSnapshots: [],
    openStatusDialog(tab) {
      context.openStatusDialogCalls.push(tab);
    },
    async requestConfirmation() {
      context.confirmationCalls += 1;
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
  const document = {
    createElement(tagName) {
      return new FakeElement(tagName);
    },
    activeElement: null,
    querySelector() {
      return null;
    },
  };
  context.document = document;
  context.window = {
    matchMedia(query) {
      return {
        matches: Boolean(context.reducedMotion && String(query).includes("prefers-reduced-motion")),
        media: query,
        addListener() {},
        removeListener() {},
        addEventListener() {},
        removeEventListener() {},
      };
    },
    requestAnimationFrame(callback) {
      return setTimeout(callback, 0);
    },
    setTimeout,
    clearTimeout,
  };
  const source = [
    extractFunction(APP_SOURCE, "identityAllowsCardAiQuickAction"),
    extractFunction(APP_SOURCE, "catalogItemHasCompleteMetadata"),
    extractFunction(APP_SOURCE, "cardNeedsMetadata"),
    extractFunction(APP_SOURCE, "cardAiQuickActionEligible"),
    extractFunction(APP_SOURCE, "catalogItemsForCurrentScope"),
    extractFunction(APP_SOURCE, "galleryMotionPreferred"),
    extractFunction(APP_SOURCE, "cardAiQuickActionProviderBlocked"),
    extractFunction(APP_SOURCE, "cardAiPreviewResponseMatchesRequest"),
    extractFunction(APP_SOURCE, "getCardAiQuickAction"),
    extractFunction(APP_SOURCE, "setCardAiQuickActionController"),
    extractFunction(APP_SOURCE, "cardAiQuickActionIsLocked"),
    extractFunction(APP_SOURCE, "cardAiQuickActionStatusMessage"),
    extractFunction(APP_SOURCE, "setCardAnalysisStatus"),
    extractFunction(APP_SOURCE, "announceCardAiQuickActionSuccess"),
    extractFunction(APP_SOURCE, "dismissCardAiQuickActionButton"),
    extractFunction(APP_SOURCE, "clearCatalogCardReflowInlineStyles"),
    extractFunction(APP_SOURCE, "captureCatalogCardLayoutSnapshot"),
    extractFunction(APP_SOURCE, "animateCatalogCardMetadataReflow"),
    extractFunction(APP_SOURCE, "setCardAnalyzeButtonState"),
    extractFunction(APP_SOURCE, "reconcileCatalogCardAiQuickActions"),
    extractFunction(APP_SOURCE, "suggestionIsUsableForCanonicalSave"),
    extractFunction(APP_SOURCE, "mediaCreatorAttributionFields"),
    extractFunction(APP_SOURCE, "mediaHasCreatorAttribution"),
    extractFunction(APP_SOURCE, "mediaCreatorChipLabel"),
    extractFunction(APP_SOURCE, "catalogCreatorFilterIsActive"),
    extractFunction(APP_SOURCE, "setCatalogCreatorFilter"),
    extractFunction(APP_SOURCE, "appendCatalogCreatorChip"),
    extractFunction(APP_SOURCE, "appendDetailsCreatorChip"),
    extractFunction(APP_SOURCE, "renderCatalogCardTags"),
    extractFunction(APP_SOURCE, "applySavedAiMetadataToCatalogSurfaces"),
    extractFunction(APP_SOURCE, "handleAnalyzeCatalogCard"),
    extractFunction(APP_SOURCE, "companionWebHosted"),
  ].join("\n");
  vm.createContext(context);
  vm.runInContext(source, context);
  const capture = context.captureCatalogCardLayoutSnapshot;
  context.captureCatalogCardLayoutSnapshot = function wrappedCapture() {
    const snapshot = capture.call(context);
    context.layoutSnapshots.push(snapshot);
    return snapshot;
  };
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

function previewPayload(item, suggestionOverrides = {}) {
  return {
    media_id: item.media_id,
    location_id: item.locations[0].location_id,
    suggestion: {
      title: "AI Sunset",
      description: "Warm light",
      tags: ["Nature"],
      suggested_filename: "sunset.jpg",
      ...suggestionOverrides,
    },
  };
}

function sampleItem(overrides = {}) {
  return {
    media_id: "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
    media_kind: "image",
    display_title: "Sunset Still",
    description: null,
    content_category: "general",
    acquisition_source: "manual_upload",
    tags: [],
    locations: [{
      location_id: "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb",
      availability: "available",
      relative_path: "stills/sunset.jpg",
    }],
    ...overrides,
  };
}

function renderCatalogCardForCapabilities(capabilities, overrides = {}, options = {}) {
  const harness = createFlowHarness();
  const { context } = harness;
  const detailsCalls = [];
  const editCalls = [];
  const attachCalls = [];
  context.identityState.capabilities = new Set(capabilities);
  context.renderCatalogCardMediaSurface = () => new FakeElement("div");
  context.renderCatalogCardTags = () => new FakeElement("div");
  context.openDetailsDialog = (item, opener) => detailsCalls.push({ item, opener });
  context.handleOpenMetadataWorkspace = (item, opener) => editCalls.push({ item, opener });
  context.editIcon = () => new FakeElement("span");
  context.openOriginalIcon = () => new FakeElement("span");
  context.mediaContentUrl = (mediaId, locationId) =>
    `/api/media/${mediaId}/locations/${locationId}/content`;
  context.automaticAnalysisStatusMessage = () => "";
  if (options.hosted) {
    context.FrameNestCompanionWeb = {
      isHosted() {
        return true;
      },
      attach(mediaId, locationId) {
        attachCalls.push({ mediaId, locationId });
        return Promise.resolve({ ok: true });
      },
      onHostedChange() {},
    };
  }
  vm.runInContext(extractFunction(APP_SOURCE, "companionWebHosted"), context);
  vm.runInContext(extractFunction(APP_SOURCE, "renderCatalogCard"), context);
  const item = sampleItem(overrides);
  return {
    card: vm.runInContext("renderCatalogCard(__item)", Object.assign(context, { __item: item })),
    detailsCalls,
    editCalls,
    attachCalls,
    item,
  };
}

test("Gallery card actions reflect ordinary admin and removed capabilities without placeholders", () => {
  const ordinary = renderCatalogCardForCapabilities([
    "gallery.read",
    "media.original.read",
    "media.download",
  ]);
  const ordinaryTitle = ordinary.card.querySelector(".catalog-card__title-button");
  const ordinaryOriginal = ordinary.card.querySelector(".catalog-card__action--open-original");
  const ordinaryActions = ordinary.card.querySelector(".catalog-card__actions");
  assert.ok(ordinaryTitle);
  ordinaryTitle.click();
  assert.equal(ordinary.detailsCalls.length, 1);
  assert.equal(ordinary.detailsCalls[0].opener, ordinaryTitle);
  assert.ok(ordinaryOriginal);
  assert.equal(
    ordinaryOriginal.href,
    `/api/media/${ordinary.item.media_id}/locations/${ordinary.item.locations[0].location_id}/content`,
  );
  assert.equal(ordinaryOriginal.title, "Open original media");
  assert.match(ordinaryOriginal.className, /catalog-card__action--bottom-right/);
  assert.equal(ordinary.card.querySelector(".catalog-card__action--edit"), null);
  assert.equal(ordinary.card.querySelector(".catalog-card__action--analyze"), null);
  assert.equal(ordinaryActions.children.length, 1);

  const admin = renderCatalogCardForCapabilities([
    "gallery.read",
    "media.original.read",
    "media.download",
    "metadata.canonical.write",
    "analysis.run",
  ]);
  assert.ok(admin.card.querySelector(".catalog-card__action--edit"));
  assert.ok(admin.card.querySelector(".catalog-card__action--analyze"));
  assert.ok(admin.card.querySelector(".catalog-card__action--open-original"));

  const noMetadata = renderCatalogCardForCapabilities([
    "gallery.read",
    "media.download",
    "analysis.run",
  ]);
  assert.equal(noMetadata.card.querySelector(".catalog-card__action--edit"), null);
  assert.equal(noMetadata.card.querySelector(".catalog-card__action--analyze"), null);
  assert.ok(noMetadata.card.querySelector(".catalog-card__action--open-original"));

  const noAnalysis = renderCatalogCardForCapabilities([
    "gallery.read",
    "media.download",
    "metadata.canonical.write",
  ]);
  assert.ok(noAnalysis.card.querySelector(".catalog-card__action--edit"));
  assert.equal(noAnalysis.card.querySelector(".catalog-card__action--analyze"), null);
  assert.ok(noAnalysis.card.querySelector(".catalog-card__action--open-original"));

  const noDownload = renderCatalogCardForCapabilities([
    "gallery.read",
    "metadata.canonical.write",
  ]);
  assert.ok(noDownload.card.querySelector(".catalog-card__action--open-original"));
  assert.ok(noDownload.card.querySelector(".catalog-card__action--edit"));
});

test("Gallery action presentation is hidden by default and renderable on reveal or coarse pointers", () => {
  const ordinary = renderCatalogCardForCapabilities([
    "gallery.read",
    "media.original.read",
    "media.download",
  ]);
  const admin = renderCatalogCardForCapabilities([
    "gallery.read",
    "media.original.read",
    "media.download",
    "metadata.canonical.write",
    "analysis.run",
  ]);
  const renderedActions = [
    ordinary.card.querySelector(".catalog-card__action--open-original"),
    admin.card.querySelector(".catalog-card__action--analyze"),
    admin.card.querySelector(".catalog-card__action--edit"),
    admin.card.querySelector(".catalog-card__action--open-original"),
  ];
  for (const action of renderedActions) {
    assert.ok(action);
    assert.equal(action.hidden, false);
    assert.notEqual(action.getAttribute("aria-hidden"), "true");
    assert.notEqual(action.getAttribute("tabindex"), "-1");
    assert.ok(action.classList.contains("catalog-card__action"));
  }

  const fineDefault = catalogActionPresentation("fine");
  assert.equal(fineDefault.overlay["z-index"], "3");
  assert.equal(fineDefault.overlay.opacity, "0");
  assert.equal(fineDefault.action.opacity, "0");
  assert.equal(fineDefault.action["pointer-events"], "none");

  const fineReveal = catalogActionPresentation("fine", true);
  assert.equal(fineReveal.overlay.opacity, "1");
  assert.equal(fineReveal.action.opacity, "1");
  assert.equal(fineReveal.action.visibility, "visible");
  assert.equal(fineReveal.action["pointer-events"], "auto");

  const coarse = catalogActionPresentation("coarse");
  assert.equal(coarse.overlay.opacity, "1");
  assert.equal(coarse.overlay.visibility, "visible");
  assert.equal(coarse.action.opacity, "1");
  assert.equal(coarse.action.visibility, "visible");
  assert.equal(coarse.action["pointer-events"], "auto");
});

test("Gallery original media action uses the content endpoint and compact placement", () => {
  const cardBody = extractFunction(APP_SOURCE, "renderCatalogCard");
  const contentUrl = extractFunction(APP_SOURCE, "mediaContentUrl");
  assert.doesNotMatch(cardBody, /identityHasCapability\("media\.download"\)/);
  assert.match(cardBody, /catalog-card__action--open-original catalog-card__action--bottom-right/);
  assert.match(cardBody, /openOriginalLink\.title = "Open original media"/);
  assert.match(cardBody, /mediaContentUrl\(item\.media_id, supportedLocation\.location_id\)/);
  assert.ok(contentUrl.includes("/content`"));
  assert.match(STYLES_SOURCE, /\.catalog-card__action--open-original\s*\{/);
  assert.match(STYLES_SOURCE, /\.catalog-card__action--attach\s*\{/);
  assert.match(INDEX_SOURCE, /src="\/assets\/companion_host\.js"/);
  assert.ok(INDEX_SOURCE.indexOf("/assets/companion_host.js") < INDEX_SOURCE.indexOf("/assets/app.js"));
  assert.doesNotMatch(INDEX_SOURCE, /https:\/\//);
  assert.doesNotMatch(cardBody, /addEventListener\("message"/);
});

test("companion-hosted Gallery replaces open-original with Attach and does not keep both", () => {
  const ordinary = renderCatalogCardForCapabilities([
    "gallery.read",
    "media.original.read",
    "media.download",
  ]);
  assert.ok(ordinary.card.querySelector(".catalog-card__action--open-original"));
  assert.equal(ordinary.card.querySelector(".catalog-card__action--attach"), null);

  const hosted = renderCatalogCardForCapabilities(
    ["gallery.read", "media.original.read", "media.download"],
    {},
    { hosted: true },
  );
  const attach = hosted.card.querySelector(".catalog-card__action--attach");
  assert.ok(attach);
  assert.equal(attach.tagName, "BUTTON");
  assert.equal(attach.type, "button");
  assert.equal(attach.textContent, "📎");
  assert.equal(attach.title, "Attach to X composer");
  assert.equal(attach.getAttribute("aria-label"), "Attach to X composer");
  assert.match(attach.className, /catalog-card__action--bottom-right/);
  assert.equal(hosted.card.querySelector(".catalog-card__action--open-original"), null);
  attach.click();
  assert.equal(hosted.attachCalls.length, 1);
  assert.equal(hosted.attachCalls[0].mediaId, hosted.item.media_id);
  assert.equal(hosted.attachCalls[0].locationId, hosted.item.locations[0].location_id);
});

test("brain eligibility requires metadata need, both capabilities, supported location, and excludes movies", () => {
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
    description: "Complete description",
    tags: [{ key: "funny", display_name: "Funny" }],
  })), false);
  assert.equal(context.cardAiQuickActionEligible(sampleItem({
    media_kind: "video",
    content_category: "meme",
    display_title: "Clip",
  })), true);
  assert.equal(context.cardAiQuickActionEligible(sampleItem({
    display_title: "Populated",
    description: "Complete description",
    tags: [
      { key: "alpha", display_name: "Alpha" },
      { key: "beta", display_name: "Beta" },
    ],
  })), false);
  assert.equal(context.cardNeedsMetadata(sampleItem({ tags: [{ key: "nature", display_name: "Nature" }] })), true);
  assert.equal(context.cardAiQuickActionEligible(sampleItem({ tags: [{ key: "nature", display_name: "Nature" }] })), true);
  const fixtureOnly = sampleItem({
    display_title: null,
    description: "Complete description",
    tags: [{ key: "acceptance", display_name: "Acceptance" }],
  });
  assert.equal(context.catalogItemHasCompleteMetadata(fixtureOnly), false);
  assert.equal(context.cardNeedsMetadata(fixtureOnly), true);
  assert.equal(context.cardAiQuickActionEligible(fixtureOnly), true);
  assert.equal(context.catalogItemHasCompleteMetadata(sampleItem({ tags: [] })), false);
  assert.equal(
    context.catalogItemHasCompleteMetadata(sampleItem({
      description: "Complete description",
      tags: [{ key: "nature", display_name: "Nature" }],
    })),
    true,
  );
});

test("metadata completeness requires persisted trimmed title, description, and a canonical tag", () => {
  const { context } = createFlowHarness();
  const tag = [{ key: "acceptance", display_name: "Acceptance" }];
  const emptyDescription = sampleItem({ description: "", tags: tag });
  const whitespaceDescription = sampleItem({ description: " \n\t ", tags: tag });
  const noTags = sampleItem({ description: "Complete description", tags: [] });
  const noPersistedTitle = sampleItem({
    display_title: null,
    description: "Complete description",
    tags: tag,
  });
  const filenameFallbackOnly = sampleItem({
    display_title: null,
    description: "Complete description",
    tags: tag,
  });
  const complete = sampleItem({ description: "Complete description", tags: tag });

  assert.equal(context.catalogItemHasCompleteMetadata(emptyDescription), false);
  assert.equal(context.catalogItemHasCompleteMetadata(whitespaceDescription), false);
  assert.equal(context.catalogItemHasCompleteMetadata(noTags), false);
  assert.equal(context.catalogItemHasCompleteMetadata(noPersistedTitle), false);
  assert.equal(filenameFallbackOnly.locations[0].relative_path, "stills/sunset.jpg");
  assert.equal(context.catalogItemHasCompleteMetadata(filenameFallbackOnly), false);
  assert.equal(
    extractFunction(APP_SOURCE, "catalogItemHasCompleteMetadata").includes("deriveCatalogFallbackTitle"),
    false,
  );
  assert.equal(context.catalogItemHasCompleteMetadata(complete), true);
  assert.equal(context.cardAiQuickActionEligible(emptyDescription), true);
  assert.equal(context.cardAiQuickActionEligible(complete), false);
});

test("Processed presentation uses the same metadata-completeness predicate as brain eligibility", () => {
  const { context } = createFlowHarness();
  const fixtureOnly = sampleItem({
    display_title: "Acceptance JPEG meme",
    description: "",
    tags: [{ key: "acceptance", display_name: "Acceptance" }],
    collection_key: "processed",
  });
  const complete = sampleItem({
    media_id: "cccccccc-cccc-4ccc-8ccc-cccccccccccc",
    display_title: "Reviewed still",
    description: "Complete description",
    tags: [{ key: "nature", display_name: "Nature" }],
    collection_key: "processed",
  });

  context.catalogState.collection = "processed";
  assert.deepEqual(
    context.catalogItemsForCurrentScope([fixtureOnly, complete]).map((item) => item.media_id),
    [complete.media_id],
  );
  context.catalogState.collection = "";
  assert.deepEqual(
    context.catalogItemsForCurrentScope([fixtureOnly, complete]).map((item) => item.media_id),
    [fixtureOnly.media_id, complete.media_id],
  );

  const renderBody = extractFunction(APP_SOURCE, "renderCatalogSuccess");
  assert.ok(renderBody.includes("catalogItemsForCurrentScope(page.items)"));
  assert.ok(renderBody.includes("setCatalogPagination(page, visibleItems.length)"));
  assert.ok(renderBody.includes("visibleItems.forEach"));
  const paginationBody = extractFunction(APP_SOURCE, "setCatalogPagination");
  assert.ok(paginationBody.includes("processedPageWasRefined"));
  assert.ok(paginationBody.includes("metadata-complete"));
});

test("ordinary missing-capability role-only and missing identity fail closed for brain eligibility", () => {
  const { context } = createFlowHarness();
  const item = sampleItem();

  context.identityState.capabilities = new Set(["gallery.read"]);
  assert.equal(context.cardAiQuickActionEligible(item), false);

  context.identityState.capabilities = new Set();
  assert.equal(context.cardAiQuickActionEligible(item), false);

  context.identityState.role = "admin";
  context.identityState.capabilities = new Set();
  assert.equal(context.identityHasCapability("analysis.run"), false);
  assert.equal(context.cardAiQuickActionEligible(item), false);

  context.identityState.resolved = true;
  context.identityState.available = false;
  context.identityState.capabilities = new Set(["analysis.run", "metadata.canonical.write"]);
  assert.equal(context.identityHasCapability("analysis.run"), true);
  assert.equal(context.cardAiQuickActionEligible(item), false);

  context.identityState.resolved = false;
  context.identityState.available = true;
  context.identityState.capabilities = new Set(["analysis.run", "metadata.canonical.write"]);
  assert.equal(context.cardAiQuickActionEligible(item), false);

  context.identityState.resolved = true;
  context.identityState.available = true;
  context.identityState.capabilities = new Set(["analysis.run", "metadata.canonical.write"]);
  assert.equal(context.cardAiQuickActionEligible(item), true);
});

test("source wiring gates brain on metadata need and positively resolved identity capabilities", () => {
  const cardBody = extractFunction(APP_SOURCE, "renderCatalogCard");
  const handleBody = extractFunction(APP_SOURCE, "handleAnalyzeCatalogCard");
  const eligibleBody = extractFunction(APP_SOURCE, "cardAiQuickActionEligible");
  const identityGateBody = extractFunction(APP_SOURCE, "identityAllowsCardAiQuickAction");
  assert.ok(cardBody.includes("cardAiQuickActionEligible(item)"));
  assert.ok(eligibleBody.includes("cardNeedsMetadata(item)"));
  assert.ok(identityGateBody.includes("identityState.resolved"));
  assert.ok(identityGateBody.includes("identityState.available"));
  assert.ok(identityGateBody.includes('capabilities.has("analysis.run")'));
  assert.ok(identityGateBody.includes('capabilities.has("metadata.canonical.write")'));
  assert.equal(eligibleBody.includes("identityHasCapability("), false);
  assert.ok(eligibleBody.includes("identityAllowsCardAiQuickAction()"));
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
  assert.ok(handleBody.includes("cardAiPreviewResponseMatchesRequest(payload, mediaId, location.location_id)"));
  assert.ok(handleBody.includes("cardAiQuickActionIsLocked(mediaId)"));
  assert.ok(handleBody.includes("content_category: metadataPayload.content_category"));
  assert.equal(handleBody.includes("acquisition_source: metadataPayload.acquisition_source"), false);
  assert.ok(handleBody.includes("creator_attribution_kind: metadataPayload.creator_attribution_kind"));
  assert.ok(handleBody.includes("genres: Array.isArray(metadataPayload.genres)"));
  assert.equal(handleBody.includes('openStatusDialog("ai"'), false);
  assert.ok(handleBody.includes('state: "idle"'));
  assert.equal(handleBody.includes('state: "saved"'), false);
  assert.ok(APP_SOURCE.includes("dismissCardAiQuickActionButton"));
  assert.ok(APP_SOURCE.includes("announceCardAiQuickActionSuccess"));
  assert.ok(APP_SOURCE.includes("captureCatalogCardLayoutSnapshot"));
  assert.ok(APP_SOURCE.includes("animateCatalogCardMetadataReflow"));
  const applyBody = extractFunction(APP_SOURCE, "applySavedAiMetadataToCatalogSurfaces");
  assert.equal(applyBody.includes("loadCatalog("), false);
  assert.equal(handleBody.includes("loadCatalog("), false);
});

test("Edit Analyze remains draft-only and does not auto-save", () => {
  const analyzeBody = extractFunction(APP_SOURCE, "handleAnalyzeMetadataByAi");
  assert.ok(analyzeBody.includes("applyResolvedAiSuggestionToMetadataWorkspace(suggestion, tagKeys)"));
  assert.equal(analyzeBody.includes('method: "PUT"'), false);
  assert.equal(analyzeBody.includes("applySavedAiMetadataToCatalogSurfaces"), false);
  assert.ok(analyzeBody.includes("await requestConfirmation({"));
});

test("Edit remains available in card source after brain eligibility disappears", () => {
  const cardBody = extractFunction(APP_SOURCE, "renderCatalogCard");
  assert.ok(cardBody.includes('identityHasCapability("metadata.canonical.write")'));
  assert.ok(cardBody.includes("handleOpenMetadataWorkspace(item, editButton)"));
  assert.ok(cardBody.includes("cardAiQuickActionEligible(item)"));
  const analyzeGate = cardBody.slice(
    cardBody.indexOf("if (cardAiQuickActionEligible(item))"),
    cardBody.indexOf('identityHasCapability("metadata.canonical.write")'),
  );
  assert.ok(analyzeGate.includes("analyzeButton"));
  assert.equal(analyzeGate.includes("editButton"), false);
});

test("unavailable and pending provider use native disabled without Status confirmation or preview", async () => {
  const harness = createFlowHarness();
  harness.context.aiCapability.available = false;
  harness.context.aiCapabilityDiscoveryPending = false;
  const item = sampleItem();
  const button = new FakeElement("button");
  button.className = "catalog-card__action--analyze";
  button.dataset.mediaTitle = item.display_title;
  const card = new FakeElement("article");
  card.className = "catalog-card";
  const status = new FakeElement("p");
  status.className = "catalog-card__analysis-status";
  card.appendChild(button);
  card.appendChild(status);
  harness.catalogResults.appendChild(card);
  harness.context.setCardAnalyzeButtonState(button, "idle");

  assert.equal(button.disabled, true);
  assert.equal(button.getAttribute("aria-disabled"), "true");
  assert.match(button.getAttribute("aria-label"), /AI analysis unavailable for Sunset Still/);
  assert.equal(button.title, "AI analysis unavailable for Sunset Still");

  button.click();
  button.dispatchEvent({ type: "click" });
  button.dispatchEvent({ type: "keydown", key: "Enter" });
  button.dispatchEvent({ type: "keydown", key: " " });
  await harness.context.handleAnalyzeCatalogCard(item, button);
  await flushAll();
  assert.deepEqual(harness.context.openStatusDialogCalls, []);
  assert.equal(harness.context.confirmationCalls, 0);
  assert.equal(harness.fetchCalls.length, 0);
  assert.equal(button.dataset.analysisState, "idle");

  harness.context.aiCapabilityDiscoveryPending = true;
  harness.context.reconcileCatalogCardAiQuickActions();
  assert.equal(button.disabled, true);
  assert.equal(button.getAttribute("aria-disabled"), "true");
  assert.match(button.getAttribute("aria-label"), /Checking AI availability for Sunset Still/);
  assert.equal(button.title, "Checking AI availability for Sunset Still");
  await harness.context.handleAnalyzeCatalogCard(item, button);
  await flushAll();
  assert.deepEqual(harness.context.openStatusDialogCalls, []);
  assert.equal(harness.fetchCalls.length, 0);
});

test("capability reconciliation enables operable brain without remounting or resetting locked state", () => {
  const harness = createFlowHarness();
  const idleButton = new FakeElement("button");
  idleButton.className = "catalog-card__action--analyze";
  idleButton.dataset.analysisState = "idle";
  idleButton.dataset.mediaTitle = "Sunset Still";
  idleButton.disabled = true;
  idleButton.setAttribute("aria-disabled", "true");
  const lockedButton = new FakeElement("button");
  lockedButton.className = "catalog-card__action--analyze";
  lockedButton.dataset.analysisState = "analyzing";
  lockedButton.dataset.mediaTitle = "Busy Still";
  lockedButton.disabled = true;
  lockedButton.setAttribute("aria-busy", "true");
  lockedButton.setAttribute("aria-label", "Analyzing Busy Still");
  harness.catalogResults.appendChild(idleButton);
  harness.catalogResults.appendChild(lockedButton);

  harness.context.aiCapability.available = false;
  harness.context.aiCapabilityDiscoveryPending = false;
  harness.context.reconcileCatalogCardAiQuickActions();
  assert.equal(idleButton.disabled, true);
  assert.equal(idleButton.getAttribute("aria-disabled"), "true");

  harness.context.aiCapability.available = true;
  harness.context.aiCapabilityDiscoveryPending = false;
  harness.context.reconcileCatalogCardAiQuickActions();
  assert.equal(idleButton.disabled, false);
  assert.equal(idleButton.getAttribute("aria-disabled"), null);
  assert.equal(idleButton.getAttribute("aria-label"), "Generate first-pass AI metadata for Sunset Still");
  assert.equal(idleButton.title, "Analyze by AI");
  assert.equal(lockedButton.disabled, true);
  assert.equal(lockedButton.dataset.analysisState, "analyzing");
  assert.equal(lockedButton.getAttribute("aria-label"), "Analyzing Busy Still");
  assert.equal(harness.catalogResults.children.length, 2);
  assert.equal(harness.catalogResults.children[0], idleButton);
  assert.equal(harness.fetchCalls.length, 0);
});

test("successful save removes brain, keeps accessible announcement, and does not recreate on reload eligibility", async () => {
  const harness = createFlowHarness();
  const item = sampleItem();
  const mediaId = item.media_id;
  const locationId = item.locations[0].location_id;
  harness.context.canonicalTagDefinitions = [{ key: "nature", display_name: "Nature" }];
  harness.enqueue(
    "POST",
    `/api/media/${mediaId}/locations/${locationId}/ai-suggestion-preview`,
    response(previewPayload(item)),
  );
  harness.enqueue(
    "GET",
    `/api/media/${mediaId}/metadata`,
    response({
      display_title: "Sunset Still",
      description: "old",
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
        tags: [{ key: "nature", display_name: "Nature" }],
        content_category: "general",
        acquisition_source: "unknown",
        genres: [],
      },
    }),
  );
  const button = new FakeElement("button");
  button.className = "catalog-card__action catalog-card__action--analyze";
  button.dataset.mediaTitle = item.display_title;
  const card = new FakeElement("article");
  card.className = "catalog-card";
  card.dataset.mediaId = mediaId;
  const actions = new FakeElement("div");
  actions.className = "catalog-card__actions";
  const editButton = new FakeElement("button");
  editButton.className = "catalog-card__action--edit";
  const status = Object.assign(new FakeElement("p"), { className: "catalog-card__analysis-status" });
  const titleButton = Object.assign(new FakeElement("button"), { className: "catalog-card__title-button" });
  const tags = Object.assign(new FakeElement("div"), { className: "catalog-card__tags" });
  const mediaSurface = Object.assign(new FakeElement("div"), { className: "media-placeholder" });
  mediaSurface.dataset.mediaState = "playing";
  actions.appendChild(button);
  actions.appendChild(editButton);
  card.appendChild(mediaSurface);
  card.appendChild(actions);
  card.appendChild(titleButton);
  card.appendChild(tags);
  card.appendChild(status);
  harness.catalogResults.appendChild(card);

  await harness.context.handleAnalyzeCatalogCard(item, button);
  await flushAll();

  assert.equal(item.tags.length, 1);
  assert.equal(item.display_title, "AI Sunset");
  assert.equal(item.description, "Warm light");
  assert.equal(titleButton.textContent, "AI Sunset");
  assert.equal(card.querySelector(".catalog-card__action--analyze"), null);
  assert.equal(button.isConnected, false);
  assert.equal(editButton.isConnected, true);
  assert.equal(mediaSurface.dataset.mediaState, "playing");
  assert.equal(status.textContent, "AI metadata saved");
  assert.equal(status.classList.contains("visually-hidden"), true);
  assert.equal(status.hidden, false);
  assert.equal(status.dataset.analysisSuccess, "true");
  assert.equal(harness.context.cardAiQuickActionEligible(item), false);
  assert.equal(harness.context.getCardAiQuickAction(mediaId).state, "idle");
  assert.equal(harness.fetchCalls.some((call) => call.url.includes("loadCatalog") || call.method === "GET" && call.url === "/api/media"), false);

  const reloaded = sampleItem({
    display_title: "AI Sunset",
    description: "Warm light",
    tags: [{ key: "nature", display_name: "Nature" }],
  });
  assert.equal(harness.context.cardNeedsMetadata(reloaded), false);
  assert.equal(harness.context.cardAiQuickActionEligible(reloaded), false);
});

test("busy analyzing and applying keep brain glyph with pulse contract and no visible progress text", () => {
  const harness = createFlowHarness();
  const button = new FakeElement("button");
  button.className = "catalog-card__action--analyze";
  button.dataset.mediaTitle = "Sunset Still";
  const other = new FakeElement("button");
  other.className = "catalog-card__action--analyze";
  other.dataset.mediaTitle = "Other";
  other.dataset.analysisState = "idle";
  other.textContent = "🧠";
  const card = new FakeElement("article");
  card.className = "catalog-card";
  const status = Object.assign(new FakeElement("p"), { className: "catalog-card__analysis-status" });
  card.appendChild(button);
  card.appendChild(status);
  harness.catalogResults.appendChild(card);
  harness.catalogResults.appendChild(other);

  harness.context.setCardAnalyzeButtonState(button, "analyzing");
  assert.equal(button.dataset.analysisState, "analyzing");
  assert.equal(button.getAttribute("aria-busy"), "true");
  assert.equal(button.disabled, true);
  assert.equal(button.textContent, "🧠");
  assert.equal(status.hidden, true);
  assert.equal(status.textContent, "");
  assert.match(STYLES_SOURCE, /catalog-card-analyze-pulse/);
  assert.match(
    STYLES_SOURCE,
    /\.catalog-card__action--analyze\[data-analysis-state="analyzing"\][\s\S]*animation:\s*catalog-card-analyze-pulse/,
  );
  assert.match(
    STYLES_SOURCE,
    /\.catalog-card__actions--overlay \.catalog-card__action--analyze\[data-analysis-state="analyzing"\][^{]*\{[^}]*opacity:\s*1;[^}]*pointer-events:\s*auto;/s,
  );
  assert.equal(
    /\.catalog-card__actions--overlay \.catalog-card__action--analyze\s*\{[^}]*opacity:\s*1/s.test(STYLES_SOURCE),
    false,
  );
  assert.match(
    STYLES_SOURCE,
    /\.catalog-card__action--analyze\s*\{[^}]*background:\s*#000/s,
  );
  assert.match(
    STYLES_SOURCE,
    /\.catalog-card__action--analyze\[data-analysis-state="analyzing"\],[\s\S]*background:\s*#000/s,
  );
  assert.match(STYLES_SOURCE, /prefers-reduced-motion: reduce[\s\S]*animation:\s*none !important/);
  assert.equal(STYLES_SOURCE.includes("catalog-card__analyze-busy"), false);

  harness.context.setCardAnalyzeButtonState(button, "applying");
  assert.equal(button.dataset.analysisState, "applying");
  assert.equal(button.textContent, "🧠");
  assert.equal(status.hidden, true);

  harness.context.setCardAnalyzeButtonState(button, "failed_analysis", "AI analysis failed.");
  assert.equal(button.dataset.analysisState, "failed_analysis");
  assert.equal(button.getAttribute("aria-busy"), "false");
  assert.equal(status.textContent, "AI analysis failed.");
  assert.equal(status.hidden, false);
  assert.equal(status.classList.contains("visually-hidden"), false);
  assert.equal(other.dataset.analysisState, "idle");
  assert.equal(other.textContent, "🧠");
});

test("failed analysis and failed save keep the brain available for confirmed retry", async () => {
  const analysisHarness = createFlowHarness();
  const item = sampleItem();
  const mediaId = item.media_id;
  const locationId = item.locations[0].location_id;
  analysisHarness.enqueue(
    "POST",
    `/api/media/${mediaId}/locations/${locationId}/ai-suggestion-preview`,
    response({ error: { code: "AI_PROVIDER_UNAVAILABLE", message: "down" } }, 503),
  );
  const button = new FakeElement("button");
  button.className = "catalog-card__action--analyze";
  button.dataset.mediaTitle = item.display_title;
  const card = new FakeElement("article");
  card.className = "catalog-card";
  card.dataset.mediaId = mediaId;
  const status = Object.assign(new FakeElement("p"), { className: "catalog-card__analysis-status" });
  card.appendChild(button);
  card.appendChild(status);
  analysisHarness.catalogResults.appendChild(card);
  await analysisHarness.context.handleAnalyzeCatalogCard(item, button);
  await flushAll();
  assert.equal(button.dataset.analysisState, "failed_analysis");
  assert.equal(button.isConnected, true);
  assert.equal(status.textContent, "AI provider is not available.");
  assert.equal(status.classList.contains("visually-hidden"), false);
  assert.equal(analysisHarness.context.cardAiQuickActionEligible(item), true);

  const saveHarness = createFlowHarness();
  saveHarness.context.canonicalTagDefinitions = [];
  saveHarness.enqueue(
    "POST",
    `/api/media/${mediaId}/locations/${locationId}/ai-suggestion-preview`,
    response(previewPayload(item, { tags: ["Brand New"] })),
  );
  saveHarness.enqueue(
    "POST",
    "/api/canonical-tags",
    response({ status: "created", tag: { key: "brand-new", display_name: "Brand New" } }, 201),
  );
  saveHarness.enqueue(
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
  saveHarness.enqueue(
    "PUT",
    `/api/media/${mediaId}/metadata`,
    response({ error: { code: "MEDIA_METADATA_OPERATION_FAILED", message: "failed" } }, 500),
  );
  const saveButton = new FakeElement("button");
  saveButton.className = "catalog-card__action--analyze";
  saveButton.dataset.mediaTitle = item.display_title;
  const saveCard = new FakeElement("article");
  saveCard.className = "catalog-card";
  const saveStatus = Object.assign(new FakeElement("p"), { className: "catalog-card__analysis-status" });
  saveCard.appendChild(saveButton);
  saveCard.appendChild(saveStatus);
  saveHarness.catalogResults.appendChild(saveCard);
  await saveHarness.context.handleAnalyzeCatalogCard(item, saveButton);
  await flushAll();
  assert.equal(saveButton.dataset.analysisState, "failed_save");
  assert.equal(saveButton.isConnected, true);
  assert.match(saveStatus.textContent, /could not be saved/);
  assert.equal(saveHarness.context.cardAiQuickActionEligible(item), true);
});

test("success reflow captures layout before patch, animates moved cards, and clears temporary styles", async () => {
  const harness = createFlowHarness({ reducedMotion: false });
  const item = sampleItem();
  const neighbor = sampleItem({
    media_id: "cccccccc-cccc-4ccc-8ccc-cccccccccccc",
    display_title: "Neighbor",
  });
  const mediaId = item.media_id;
  harness.context.canonicalTagDefinitions = [{ key: "nature", display_name: "Nature" }];
  const card = new FakeElement("article");
  card.className = "catalog-card";
  card.dataset.mediaId = mediaId;
  card._rect = { left: 0, top: 0, width: 200, height: 120 };
  const neighborCard = new FakeElement("article");
  neighborCard.className = "catalog-card";
  neighborCard.dataset.mediaId = neighbor.media_id;
  neighborCard._rect = { left: 220, top: 0, width: 200, height: 120 };
  const button = new FakeElement("button");
  button.className = "catalog-card__action--analyze";
  const titleButton = Object.assign(new FakeElement("button"), {
    className: "catalog-card__title-button",
    textContent: item.display_title,
  });
  const tags = Object.assign(new FakeElement("div"), { className: "catalog-card__tags" });
  const status = Object.assign(new FakeElement("p"), { className: "catalog-card__analysis-status" });
  const mediaSurface = Object.assign(new FakeElement("video"), { className: "media-placeholder" });
  mediaSurface.dataset.kept = "true";
  card.appendChild(mediaSurface);
  card.appendChild(button);
  card.appendChild(titleButton);
  card.appendChild(tags);
  card.appendChild(status);
  harness.catalogResults.appendChild(card);
  harness.catalogResults.appendChild(neighborCard);

  const capture = harness.context.captureCatalogCardLayoutSnapshot;
  harness.context.captureCatalogCardLayoutSnapshot = function wrapped() {
    const snapshot = capture.call(harness.context);
    card._rect = { left: 0, top: 0, width: 200, height: 180 };
    neighborCard._rect = { left: 220, top: 60, width: 200, height: 120 };
    return snapshot;
  };

  harness.context.applySavedAiMetadataToCatalogSurfaces(item, {
    display_title: "AI Sunset",
    description: "Warm light",
    tags: [{ key: "nature", display_name: "Nature" }],
    content_category: "general",
    acquisition_source: "unknown",
    genres: [],
  });
  await flushAll();
  await new Promise((resolve) => setTimeout(resolve, 20));

  assert.equal(harness.context.layoutSnapshots.length, 1);
  assert.equal(titleButton.textContent, "AI Sunset");
  assert.ok(card.querySelector(".catalog-card__tags"));
  assert.equal(mediaSurface.dataset.kept, "true");
  assert.equal(neighborCard.isConnected, true);
  assert.equal(harness.catalogResults.children[0], card);
  assert.equal(harness.catalogResults.children[1], neighborCard);
  assert.ok(
    card.classList.contains("catalog-card--reflowing")
    || neighborCard.classList.contains("catalog-card--reflowing")
    || card.style.height
    || neighborCard.style.transform,
  );
  await new Promise((resolve) => setTimeout(resolve, 300));
  assert.equal(card.style.transform || "", "");
  assert.equal(card.style.height || "", "");
  assert.equal(neighborCard.style.transform || "", "");
  assert.equal(card.classList.contains("catalog-card--reflowing"), false);
  assert.equal(neighborCard.classList.contains("catalog-card--reflowing"), false);
});

test("reduced motion bypasses FLIP movement and removes brain immediately", () => {
  const harness = createFlowHarness({ reducedMotion: true });
  const item = sampleItem();
  const card = new FakeElement("article");
  card.className = "catalog-card";
  card.dataset.mediaId = item.media_id;
  const button = new FakeElement("button");
  button.className = "catalog-card__action--analyze";
  const titleButton = Object.assign(new FakeElement("button"), { className: "catalog-card__title-button" });
  const tags = Object.assign(new FakeElement("div"), { className: "catalog-card__tags" });
  const status = Object.assign(new FakeElement("p"), { className: "catalog-card__analysis-status" });
  card.appendChild(button);
  card.appendChild(titleButton);
  card.appendChild(tags);
  card.appendChild(status);
  harness.catalogResults.appendChild(card);

  harness.context.applySavedAiMetadataToCatalogSurfaces(item, {
    display_title: "AI Sunset",
    tags: [{ key: "nature", display_name: "Nature" }],
  });

  assert.equal(harness.context.layoutSnapshots.length, 0);
  assert.equal(button.isConnected, false);
  assert.equal(titleButton.textContent, "AI Sunset");
  assert.equal(status.textContent, "AI metadata saved");
  assert.equal(status.classList.contains("visually-hidden"), true);
});

test("matching Details updates while non-matching Details stay unchanged", () => {
  const harness = createFlowHarness();
  const item = sampleItem();
  const other = sampleItem({
    media_id: "cccccccc-cccc-4ccc-8ccc-cccccccccccc",
    display_title: "Other Still",
  });
  harness.context.detailsCurrentItem = {
    media_id: item.media_id,
    display_title: item.display_title,
    tags: [],
  };
  const card = new FakeElement("article");
  card.className = "catalog-card";
  card.dataset.mediaId = item.media_id;
  card.appendChild(Object.assign(new FakeElement("button"), { className: "catalog-card__title-button" }));
  card.appendChild(Object.assign(new FakeElement("div"), { className: "catalog-card__tags" }));
  card.appendChild(Object.assign(new FakeElement("p"), { className: "catalog-card__analysis-status" }));
  harness.catalogResults.appendChild(card);

  harness.context.applySavedAiMetadataToCatalogSurfaces(item, {
    display_title: "AI Sunset",
    description: "Warm light",
    tags: [{ key: "nature", display_name: "Nature" }],
  });
  assert.equal(harness.context.detailsCurrentItem.display_title, "AI Sunset");
  assert.equal(harness.context.detailsDialogTitle.textContent, "AI Sunset");
  assert.equal(harness.context.detailsDescription.textContent, "Warm light");
  assert.equal(harness.context.detailsTagsContainer.children.length, 1);

  harness.context.detailsCurrentItem = {
    media_id: other.media_id,
    display_title: other.display_title,
    tags: [],
  };
  harness.context.detailsDialogTitle.textContent = other.display_title;
  harness.context.detailsDescription.textContent = "keep";
  harness.context.detailsTagsContainer.replaceChildren();
  harness.context.applySavedAiMetadataToCatalogSurfaces(item, {
    display_title: "AI Sunset Again",
    description: "Changed",
    tags: [{ key: "nature", display_name: "Nature" }],
  });
  assert.equal(harness.context.detailsCurrentItem.display_title, other.display_title);
  assert.equal(harness.context.detailsDialogTitle.textContent, other.display_title);
  assert.equal(harness.context.detailsDescription.textContent, "keep");
  assert.equal(harness.context.detailsTagsContainer.children.length, 0);
});

test("failed_analysis pending then available restores retry analysis label", async () => {
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
  button.className = "catalog-card__action--analyze";
  button.dataset.mediaTitle = item.display_title;
  const card = new FakeElement("article");
  card.className = "catalog-card";
  card.dataset.mediaId = mediaId;
  const status = Object.assign(new FakeElement("p"), { className: "catalog-card__analysis-status" });
  card.appendChild(button);
  card.appendChild(status);
  harness.catalogResults.appendChild(card);

  await harness.context.handleAnalyzeCatalogCard(item, button);
  await flushAll();
  assert.equal(button.dataset.analysisState, "failed_analysis");
  assert.equal(status.textContent, "AI provider is not available.");
  const requestsBeforeReconcile = harness.fetchCalls.length;

  harness.context.aiCapability.available = false;
  harness.context.aiCapabilityDiscoveryPending = false;
  harness.context.reconcileCatalogCardAiQuickActions();
  assert.equal(button.disabled, true);
  assert.equal(button.getAttribute("aria-label"), "AI analysis unavailable for Sunset Still");
  assert.equal(button.dataset.analysisState, "failed_analysis");
  assert.equal(status.textContent, "AI provider is not available.");

  harness.context.aiCapability.available = true;
  harness.context.reconcileCatalogCardAiQuickActions();
  assert.equal(harness.catalogResults.children[0], card);
  assert.equal(button.disabled, false);
  assert.equal(button.getAttribute("aria-disabled"), null);
  assert.equal(button.dataset.analysisState, "failed_analysis");
  assert.equal(status.textContent, "AI provider is not available.");
  assert.equal(
    button.getAttribute("aria-label"),
    "AI analysis failed for Sunset Still. Retry Analyze by AI",
  );
  assert.equal(button.title, "AI analysis failed — retry");
  assert.equal(harness.fetchCalls.length, requestsBeforeReconcile);
  assert.deepEqual(harness.context.openStatusDialogCalls, []);

  const retryHarness = createFlowHarness({ confirmAccepted: false });
  retryHarness.context.setCardAiQuickActionController(mediaId, { state: "failed_analysis" });
  retryHarness.context.setCardAnalyzeButtonState(
    button,
    "failed_analysis",
    "AI provider is not available.",
  );
  await retryHarness.context.handleAnalyzeCatalogCard(item, button);
  await flushAll();
  assert.equal(retryHarness.context.confirmationCalls, 1);
  assert.equal(retryHarness.fetchCalls.length, 0);
});

test("failed_save pending then available restores full retry metadata label", async () => {
  const harness = createFlowHarness();
  const item = sampleItem({ tags: [] });
  harness.context.canonicalTagDefinitions = [];
  const mediaId = item.media_id;
  const locationId = item.locations[0].location_id;
  harness.enqueue(
    "POST",
    `/api/media/${mediaId}/locations/${locationId}/ai-suggestion-preview`,
    response(previewPayload(item, { tags: ["Brand New"] })),
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
  button.className = "catalog-card__action--analyze";
  button.dataset.mediaTitle = item.display_title;
  const card = new FakeElement("article");
  card.className = "catalog-card";
  card.dataset.mediaId = mediaId;
  const status = Object.assign(new FakeElement("p"), { className: "catalog-card__analysis-status" });
  card.appendChild(button);
  card.appendChild(status);
  harness.catalogResults.appendChild(card);

  await harness.context.handleAnalyzeCatalogCard(item, button);
  await flushAll();
  assert.equal(button.dataset.analysisState, "failed_save");
  assert.equal(
    status.textContent,
    "AI metadata could not be saved. Existing media metadata was not replaced.",
  );
  const requestsBeforeReconcile = harness.fetchCalls.length;

  harness.context.aiCapabilityDiscoveryPending = true;
  harness.context.aiCapability.available = false;
  harness.context.reconcileCatalogCardAiQuickActions();
  assert.equal(button.disabled, true);
  assert.equal(button.getAttribute("aria-label"), "Checking AI availability for Sunset Still");
  assert.equal(button.dataset.analysisState, "failed_save");
  assert.equal(
    status.textContent,
    "AI metadata could not be saved. Existing media metadata was not replaced.",
  );

  harness.context.aiCapabilityDiscoveryPending = false;
  harness.context.aiCapability.available = true;
  harness.context.reconcileCatalogCardAiQuickActions();
  assert.equal(harness.catalogResults.children[0], card);
  assert.equal(button.disabled, false);
  assert.equal(button.getAttribute("aria-disabled"), null);
  assert.equal(button.dataset.analysisState, "failed_save");
  assert.equal(
    status.textContent,
    "AI metadata could not be saved. Existing media metadata was not replaced.",
  );
  assert.equal(
    button.getAttribute("aria-label"),
    "AI metadata save failed for Sunset Still. Retry Analyze by AI",
  );
  assert.equal(button.title, "AI metadata save failed — retry");
  assert.equal(harness.fetchCalls.length, requestsBeforeReconcile);
  assert.deepEqual(harness.context.openStatusDialogCalls, []);

  const retryHarness = createFlowHarness({ confirmAccepted: false });
  retryHarness.context.setCardAiQuickActionController(mediaId, { state: "failed_save" });
  retryHarness.context.setCardAnalyzeButtonState(button, "failed_save", status.textContent);
  await retryHarness.context.handleAnalyzeCatalogCard(item, button);
  await flushAll();
  assert.equal(retryHarness.context.confirmationCalls, 1);
  assert.equal(retryHarness.fetchCalls.length, 0);
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
    response(previewPayload(item)),
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
  button.className = "catalog-card__action--analyze";
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
  assert.equal("acquisition_source" in putBody, false);
  assert.deepEqual(putBody.genres, ["Documentary"]);
  assert.equal(button.isConnected, false);
  assert.equal(status.textContent, "AI metadata saved");
  assert.equal(status.classList.contains("visually-hidden"), true);
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
    response(previewPayload(item, { tags: ["Nature", "Golden Hour"] })),
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
  button.className = "catalog-card__action--analyze";
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
  assert.equal(button.isConnected, false);
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

test("mismatched or missing preview identity fails before tag or metadata mutation", async () => {
  async function runMismatch(payload) {
    const harness = createFlowHarness();
    const item = sampleItem();
    const mediaId = item.media_id;
    const locationId = item.locations[0].location_id;
    harness.enqueue(
      "POST",
      `/api/media/${mediaId}/locations/${locationId}/ai-suggestion-preview`,
      response(payload),
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
    assert.equal(button.dataset.analysisState, "failed_analysis");
    assert.equal(
      status.textContent,
      "AI response did not match the selected media. No metadata was changed.",
    );
    assert.equal(harness.fetchCalls.some((call) => call.method === "POST" && call.url === "/api/canonical-tags"), false);
    assert.equal(harness.fetchCalls.some((call) => call.method === "GET" && call.url.includes("/metadata")), false);
    assert.equal(harness.fetchCalls.some((call) => call.method === "PUT"), false);
    return harness;
  }

  await runMismatch(previewPayload(sampleItem({
    media_id: "cccccccc-cccc-4ccc-8ccc-cccccccccccc",
  })));
  await runMismatch({
    ...previewPayload(sampleItem()),
    location_id: "dddddddd-dddd-4ddd-8ddd-dddddddddddd",
  });
  await runMismatch({
    location_id: sampleItem().locations[0].location_id,
    suggestion: previewPayload(sampleItem()).suggestion,
  });
  await runMismatch({
    media_id: sampleItem().media_id,
    suggestion: previewPayload(sampleItem()).suggestion,
  });
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
      resolvePreview = () => resolve(response(previewPayload(item, {
        title: "Late",
        description: "Late",
      })));
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

test("preview for another media controller identity is rejected by response match", () => {
  const { context } = createFlowHarness();
  const item = sampleItem();
  assert.equal(
    context.cardAiPreviewResponseMatchesRequest(
      previewPayload(item),
      item.media_id,
      item.locations[0].location_id,
    ),
    true,
  );
  assert.equal(
    context.cardAiPreviewResponseMatchesRequest(
      previewPayload(item),
      "cccccccc-cccc-4ccc-8ccc-cccccccccccc",
      item.locations[0].location_id,
    ),
    false,
  );
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
    response(previewPayload(item, { tags: ["Brand New"] })),
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
    response(previewPayload(item, { tags: ["Brand New"] })),
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

test("invalid suggestion does not erase metadata via PUT", async () => {
  const harness = createFlowHarness();
  const item = sampleItem();
  const mediaId = item.media_id;
  const locationId = item.locations[0].location_id;
  harness.enqueue(
    "POST",
    `/api/media/${mediaId}/locations/${locationId}/ai-suggestion-preview`,
    response({
      media_id: mediaId,
      location_id: locationId,
      suggestion: { title: "", description: "", tags: [], suggested_filename: "" },
    }),
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
  assert.ok(INDEX_SOURCE.includes('option value="youtube"'));
  assert.ok(INDEX_SOURCE.includes('id="metadata-acquisition-source"'));
  assert.ok(INDEX_SOURCE.includes('id="metadata-acquisition-source" disabled'));
  assert.ok(INDEX_SOURCE.includes('data-content-category="youtube"'));
  assert.equal(INDEX_SOURCE.includes('data-acquisition-source="youtube_manual_claim"'), false);
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
