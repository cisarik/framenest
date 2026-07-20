const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");

const APP_PATH = path.resolve(__dirname, "../src/framenest/adapters/api/web/app.js");
const APP_SOURCE = fs.readFileSync(APP_PATH, "utf8");

function productionFunction(name) {
  const asyncMarker = `async function ${name}(`;
  const regularMarker = `function ${name}(`;
  const asyncStart = APP_SOURCE.indexOf(asyncMarker);
  const marker = asyncStart === -1 ? regularMarker : asyncMarker;
  const start = asyncStart === -1 ? APP_SOURCE.indexOf(marker) : asyncStart;
  assert.notEqual(start, -1, `missing production function ${name}`);
  let depth = 0;
  let quote = null;
  let escaped = false;
  let lineComment = false;
  let blockComment = false;
  const bodyStart = APP_SOURCE.indexOf("{", start);
  for (let index = bodyStart; index < APP_SOURCE.length; index += 1) {
    const character = APP_SOURCE[index];
    const next = APP_SOURCE[index + 1];
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
      if (depth === 0) return APP_SOURCE.slice(start, index + 1);
    }
  }
  throw new Error(`unterminated production function ${name}`);
}

class FakeElement {
  constructor(document, tagName) {
    this.ownerDocument = document;
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
    this.src = "";
    this.alt = "";
    this.title = "";
    this.loading = "";
    this.decoding = "";
    this.preload = "";
    this.playsInline = false;
    this.autoplay = false;
    this.muted = false;
    this.controls = false;
    this.loop = false;
    this.onerror = null;
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
    for (const listener of [...(this.listeners.get(event.type) || [])]) {
      listener(event);
    }
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

  play() {
    return Promise.resolve();
  }

  pause() {}

  load() {}
}

function createHarness() {
  const document = {
    createElement(tagName) {
      return new FakeElement(document, tagName);
    },
  };
  const fetchCalls = [];
  const context = {
    document,
    activeCardMediaSurface: null,
    activeCardMediaRestore: null,
    cardMediaElements: new Set(),
    fetch(url, options = {}) {
      fetchCalls.push({ url: String(url), method: options.method || "GET" });
      return Promise.resolve({ ok: true, status: 200, json: async () => ({}) });
    },
  };
  const names = [
    "mediaContentUrl",
    "mediaGalleryPreviewUrl",
    "selectSupportedAvailableLocation",
    "renderPreviewFallback",
    "renderPersistentPreview",
    "renderCardOriginalPlayback",
    "cleanupCatalogCardMedia",
    "syncCardMediaSurfaceToggleState",
    "activateCardPlayback",
    "renderCatalogCardMediaSurface",
    "renderUnavailableCardMediaSurface",
  ];
  // Provide MEDIA_CATALOG_ENDPOINT used by URL helpers.
  vm.runInNewContext(
    [
      'const MEDIA_CATALOG_ENDPOINT = "/api/media";',
      ...names.map((name) => productionFunction(name)),
    ].join("\n"),
    context,
  );
  return { context, document, fetchCalls };
}

function gifItem() {
  return {
    media_id: "11111111-1111-4111-8111-111111111111",
    media_kind: "animated_image",
    display_title: "Reaction GIF",
    locations: [{
      location_id: "22222222-2222-4222-8222-222222222222",
      availability: "available",
      relative_path: "reactions/wave.gif",
    }],
    tags: [{ key: "funny", display_name: "funny" }],
  };
}

function mp4Item() {
  return {
    media_id: "33333333-3333-4333-8333-333333333333",
    media_kind: "video",
    display_title: "Clip MP4",
    locations: [{
      location_id: "44444444-4444-4444-8444-444444444444",
      availability: "available",
      relative_path: "clips/clip.mp4",
    }],
    tags: [],
  };
}

function mediaChild(surface) {
  return surface.children.find((child) => child.tagName === "IMG" || child.tagName === "VIDEO") || null;
}

test("GIF gallery surface toggles static preview and original animated content", () => {
  const { context, fetchCalls } = createHarness();
  const item = gifItem();
  const surface = context.renderCatalogCardMediaSurface(item);
  const previewUrl = context.mediaGalleryPreviewUrl(item.media_id, item.locations[0].location_id);
  const originalUrl = context.mediaContentUrl(item.media_id, item.locations[0].location_id);

  assert.equal(surface.getAttribute("data-media-state"), "preview");
  assert.equal(surface.getAttribute("aria-pressed"), "false");
  assert.equal(mediaChild(surface).src, previewUrl);

  surface.dispatchEvent({ type: "click", preventDefault() {}, key: "" });
  assert.equal(surface.getAttribute("data-media-state"), "playing");
  assert.equal(surface.getAttribute("aria-pressed"), "true");
  assert.equal(mediaChild(surface).src, originalUrl);

  surface.dispatchEvent({ type: "click", preventDefault() {}, key: "" });
  assert.equal(surface.getAttribute("data-media-state"), "preview");
  assert.equal(surface.getAttribute("aria-pressed"), "false");
  assert.equal(mediaChild(surface).src, previewUrl);

  surface.dispatchEvent({ type: "click", preventDefault() {}, key: "" });
  assert.equal(surface.getAttribute("data-media-state"), "playing");
  assert.equal(mediaChild(surface).src, originalUrl);

  assert.equal(fetchCalls.length, 0);
});

test("GIF keyboard activation toggles the same preview and original URLs", () => {
  const { context } = createHarness();
  const item = gifItem();
  const surface = context.renderCatalogCardMediaSurface(item);
  const previewUrl = context.mediaGalleryPreviewUrl(item.media_id, item.locations[0].location_id);
  const originalUrl = context.mediaContentUrl(item.media_id, item.locations[0].location_id);

  surface.dispatchEvent({ type: "keydown", key: "Enter", preventDefault() {} });
  assert.equal(mediaChild(surface).src, originalUrl);
  surface.dispatchEvent({ type: "keydown", key: " ", preventDefault() {} });
  assert.equal(mediaChild(surface).src, previewUrl);
  assert.equal(surface.getAttribute("aria-pressed"), "false");
});

test("MP4 activation continues to use original content without GIF toggle semantics", () => {
  const { context } = createHarness();
  const item = mp4Item();
  const surface = context.renderCatalogCardMediaSurface(item);
  const previewUrl = context.mediaGalleryPreviewUrl(item.media_id, item.locations[0].location_id);
  const originalUrl = context.mediaContentUrl(item.media_id, item.locations[0].location_id);

  assert.equal(mediaChild(surface).src, previewUrl);
  assert.equal(surface.getAttribute("aria-pressed"), null);

  surface.dispatchEvent({ type: "click", preventDefault() {}, key: "" });
  assert.equal(mediaChild(surface).tagName, "VIDEO");
  assert.equal(mediaChild(surface).src, originalUrl);
  assert.equal(surface.getAttribute("aria-pressed"), null);

  // Second activation restarts playback rather than restoring static preview.
  surface.dispatchEvent({ type: "click", preventDefault() {}, key: "" });
  assert.equal(mediaChild(surface).tagName, "VIDEO");
  assert.equal(mediaChild(surface).src, originalUrl);
  assert.equal(surface.getAttribute("data-media-state"), "playing");
});

test("Unavailable GIF preview fallback remains truthful and does not invent persistence", () => {
  const { context, fetchCalls } = createHarness();
  const item = {
    media_id: "55555555-5555-4555-8555-555555555555",
    media_kind: "animated_image",
    display_title: "Missing",
    locations: [],
    tags: [],
  };
  const surface = context.renderCatalogCardMediaSurface(item);
  assert.match(surface.textContent || surface.children[0].textContent, /Unavailable/i);
  assert.equal(fetchCalls.length, 0);
});
