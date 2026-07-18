const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");

const APP_PATH = path.resolve(__dirname, "../src/framenest/adapters/api/web/app.js");
const INDEX_PATH = path.resolve(__dirname, "../src/framenest/adapters/api/web/index.html");
const APP_SOURCE = fs.readFileSync(APP_PATH, "utf8");
const INDEX_SOURCE = fs.readFileSync(INDEX_PATH, "utf8");

function deferred() {
  let resolve;
  let reject;
  const promise = new Promise((promiseResolve, promiseReject) => {
    resolve = promiseResolve;
    reject = promiseReject;
  });
  return { promise, resolve, reject };
}

function response(payload, status = 200) {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: async () => payload,
  };
}

function productionFunction(name) {
  const asyncMarker = `async function ${name}(`;
  const regularMarker = `function ${name}(`;
  const asyncStart = APP_SOURCE.indexOf(asyncMarker);
  const marker = asyncStart === -1 ? regularMarker : asyncMarker;
  const start = asyncStart === -1 ? APP_SOURCE.indexOf(marker) : asyncStart;
  assert.notEqual(start, -1, `missing production function ${name}`);
  const signatureEnd = APP_SOURCE.indexOf("\n", start);
  const bodyStart = APP_SOURCE.lastIndexOf("{", signatureEnd);
  assert.ok(bodyStart > start, `missing body for production function ${name}`);

  let depth = 0;
  let quote = null;
  let escaped = false;
  let lineComment = false;
  let blockComment = false;
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
      if (escaped) {
        escaped = false;
      } else if (character === "\\") {
        escaped = true;
      } else if (character === quote) {
        quote = null;
      }
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

class TestEvent {
  constructor(type, { key = "", bubbles = true } = {}) {
    this.type = type;
    this.key = key;
    this.bubbles = bubbles;
    this.target = null;
    this.currentTarget = null;
    this.defaultPrevented = false;
    this.propagationStopped = false;
  }

  preventDefault() {
    this.defaultPrevented = true;
  }

  stopPropagation() {
    this.propagationStopped = true;
  }
}

class TestClassList {
  constructor(element) {
    this.element = element;
    this.values = new Set();
  }

  setFromString(value) {
    this.values = new Set(String(value).split(/\s+/).filter(Boolean));
  }

  add(...names) {
    names.forEach((name) => this.values.add(name));
  }

  remove(...names) {
    names.forEach((name) => this.values.delete(name));
  }

  contains(name) {
    return this.values.has(name);
  }

  toggle(name, force) {
    const enabled = force === undefined ? !this.values.has(name) : Boolean(force);
    if (enabled) this.values.add(name);
    else this.values.delete(name);
    return enabled;
  }

  toString() {
    return [...this.values].join(" ");
  }
}

function selectorMatcher(selector) {
  const match = selector.match(/^\.([a-z0-9_-]+)(?:\[data-tag-key="([^"]+)"\])?$/i);
  if (!match) throw new Error(`unsupported test selector: ${selector}`);
  return (element) => element.classList.contains(match[1])
    && (match[2] === undefined || element.dataset.tagKey === match[2]);
}

class TestElement {
  constructor(document, tagName) {
    this.ownerDocument = document;
    this.tagName = String(tagName).toUpperCase();
    this.children = [];
    this.parentNode = null;
    this.dataset = {};
    this.attributes = new Map();
    this.listeners = new Map();
    this.classList = new TestClassList(this);
    this.hidden = false;
    this.disabled = false;
    this.textContent = "";
    this.type = "";
    this.value = "";
  }

  get className() {
    return this.classList.toString();
  }

  set className(value) {
    this.classList.setFromString(value);
  }

  addEventListener(type, listener) {
    if (!this.listeners.has(type)) this.listeners.set(type, []);
    this.listeners.get(type).push(listener);
  }

  dispatchEvent(event) {
    if (!event.target) event.target = this;
    let current = this;
    while (current) {
      event.currentTarget = current;
      for (const listener of [...(current.listeners.get(event.type) || [])]) {
        listener(event);
      }
      if (!event.bubbles || event.propagationStopped) break;
      current = current.parentNode;
    }
    event.currentTarget = null;
    return !event.defaultPrevented;
  }

  click() {
    if (this.disabled) return;
    this.dispatchEvent(new TestEvent("click"));
  }

  focus() {
    if (!this.hidden && !this.disabled) this.ownerDocument.activeElement = this;
  }

  append(...nodes) {
    nodes.forEach((node) => this.appendChild(node));
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
    this.append(...nodes);
  }

  setAttribute(name, value) {
    this.attributes.set(String(name).toLowerCase(), String(value));
  }

  getAttribute(name) {
    const key = String(name).toLowerCase();
    return this.attributes.has(key) ? this.attributes.get(key) : null;
  }

  contains(candidate) {
    let current = candidate;
    while (current) {
      if (current === this) return true;
      current = current.parentNode;
    }
    return false;
  }

  querySelectorAll(selector) {
    const matches = selectorMatcher(selector);
    const results = [];
    const visit = (node) => {
      node.children.forEach((child) => {
        if (matches(child)) results.push(child);
        visit(child);
      });
    };
    visit(this);
    return results;
  }

  querySelector(selector) {
    return this.querySelectorAll(selector)[0] || null;
  }
}

class TestDocument {
  constructor() {
    this.activeElement = null;
  }

  createElement(tagName) {
    return new TestElement(this, tagName);
  }
}

function keyboardActivate(button, key) {
  const keydown = new TestEvent("keydown", { key });
  button.dispatchEvent(keydown);
  if (!keydown.defaultPrevented && key === "Enter") button.click();
  const keyup = new TestEvent("keyup", { key });
  button.dispatchEvent(keyup);
  if (!keyup.defaultPrevented && key === " ") button.click();
}

function createInteractionHarness() {
  const document = new TestDocument();
  const catalogTagFilters = document.createElement("div");
  const catalogResults = document.createElement("div");
  const commandSearchInput = document.createElement("input");
  const catalogStateEmpty = document.createElement("p");
  const context = {
    console,
    document,
    URLSearchParams,
    catalogTagFilters,
    catalogResults,
    commandSearchInput,
    catalogStateEmpty,
  };
  context.globalThis = context;
  vm.createContext(context);
  const functions = [
    "semanticArraysEqual",
    "selectedTagDefinition",
    "snapshotCatalogQueryState",
    "buildCatalogQueryParams",
    "setCatalogSearchText",
    "renderCatalogCardTags",
    "reconcileCatalogSelectedCard",
    "renderCatalogEmptyState",
    "renderCatalogTagFilterStates",
    "catalogTagDisplayName",
    "renderActiveCatalogTagFilters",
    "focusCatalogFilterChip",
    "activateCatalogTagFilter",
    "removeCatalogTagFilter",
  ].map(productionFunction).join("\n");
  vm.runInContext(`
    const CATALOG_PAGE_SIZE_OPTIONS = [10, 30, 60, 90];
    const CATALOG_PAGE_SIZE = 30;
    let catalogState = { q: "", tagKeys: [], collection: "", limit: 30, offset: 0, total: 0 };
    let canonicalTagDefinitions = [];
    let metadataWorkspace = { openMediaId: null };
    let catalogLoadCalls = 0;
    function loadCatalog() { catalogLoadCalls += 1; }
    ${functions}
  `, context, { filename: APP_PATH });
  return {
    context,
    document,
    catalogTagFilters,
    catalogResults,
    commandSearchInput,
    catalogStateEmpty,
    run(code) {
      return vm.runInContext(code, context);
    },
  };
}

function createRequestHarness(fetch) {
  const context = { console, fetch, URLSearchParams };
  context.globalThis = context;
  vm.createContext(context);
  const functions = [
    "semanticArraysEqual",
    "snapshotCatalogQueryState",
    "buildCatalogQueryParams",
    "claimCatalogRequest",
    "catalogRequestOwnerIsCurrent",
    "releaseCatalogRequest",
    "setCatalogSearchText",
    "loadCatalog",
  ].map(productionFunction).join("\n");
  vm.runInContext(`
    const CATALOG_PAGE_SIZE_OPTIONS = [10, 30, 60, 90];
    const CATALOG_PAGE_SIZE = 30;
    const MEDIA_CATALOG_ENDPOINT = "/api/media";
    let catalogRequestToken = 0;
    let catalogRequestOwner = null;
    let catalogState = { q: "", tagKeys: [], collection: "", limit: 30, offset: 0, total: 0 };
    const catalogPrevButton = { disabled: false };
    const catalogNextButton = { disabled: false };
    const catalogPageSummary = { textContent: "" };
    let catalogVisibleState = "idle";
    let renderedPages = [];
    function showCatalogState(state) { catalogVisibleState = state; }
    function renderCatalogSuccess(page) {
      renderedPages.push(page.marker);
      catalogState.total = page.total;
      catalogState.offset = page.offset;
      catalogState.limit = page.limit;
      catalogVisibleState = "success";
    }
    ${functions}
  `, context, { filename: APP_PATH });
  return {
    context,
    run(code) {
      return vm.runInContext(code, context);
    },
  };
}

test("Search markup keeps an exact prominent-purpose placeholder and an independent accessible name", () => {
  const inputStart = INDEX_SOURCE.indexOf('id="command-search-input"');
  const input = INDEX_SOURCE.slice(inputStart, INDEX_SOURCE.indexOf(">", inputStart));
  assert.match(input, /placeholder="Search titles and tags"/);
  assert.match(input, /aria-label="Search catalog by title or tag"/);
  assert.notEqual("Search titles and tags", "Search catalog by title or tag");
  assert.match(INDEX_SOURCE, /header-search__prompt[^>]*aria-hidden="true"[^>]*>&gt;</);
  assert.match(INDEX_SOURCE, /id="catalog-tag-filters"[^>]*aria-label="Active tag filters"/);
});

test("Canonical card tags compose with text as ordered AND query parameters without duplicates", () => {
  const h = createInteractionHarness();
  h.run(`canonicalTagDefinitions = [
    { key: "alpha", display_name: "Alpha" },
    { key: "beta", display_name: "Beta" }
  ]`);
  const searchOffset = h.run("catalogState.offset = 60; setCatalogSearchText('needle'); catalogState.offset");
  assert.equal(searchOffset, 0);
  h.run("catalogState.offset = 60; activateCatalogTagFilter('alpha'); activateCatalogTagFilter('beta'); activateCatalogTagFilter('alpha')");

  const state = JSON.parse(h.run("JSON.stringify({ q: catalogState.q, tagKeys: catalogState.tagKeys, offset: catalogState.offset, loads: catalogLoadCalls })"));
  assert.deepEqual(state, { q: "needle", tagKeys: ["alpha", "beta"], offset: 0, loads: 2 });
  const params = h.run("buildCatalogQueryParams().toString()");
  assert.equal(params, "q=needle&tag=alpha&tag=beta&limit=30&offset=0");
  assert.equal(h.catalogTagFilters.children.length, 2);
  assert.equal(h.catalogTagFilters.hidden, false);
  assert.equal(h.catalogTagFilters.children[0].getAttribute("aria-label"), "Remove Alpha tag filter");
});

test("Native keyboard tag activation is isolated from card actions and focuses the active chip", () => {
  const h = createInteractionHarness();
  h.context.item = { tags: [{ key: "alpha", display_name: "Alpha" }] };
  const tagRegion = h.run("renderCatalogCardTags(item)");
  const card = h.document.createElement("article");
  const title = h.document.createElement("button");
  const mediaSurface = h.document.createElement("button");
  const contextualAction = h.document.createElement("button");
  const activations = { card: 0, cardKeyboard: 0, details: 0, playback: 0, contextual: 0 };
  card.addEventListener("click", () => { activations.card += 1; });
  card.addEventListener("keydown", () => { activations.cardKeyboard += 1; });
  title.addEventListener("click", () => { activations.details += 1; });
  mediaSurface.addEventListener("click", () => { activations.playback += 1; });
  contextualAction.addEventListener("click", () => { activations.contextual += 1; });
  card.append(mediaSurface, title, tagRegion, contextualAction);
  h.catalogResults.appendChild(card);

  const tagButton = tagRegion.children[0];
  assert.equal(tagRegion.getAttribute("role"), "group");
  assert.equal(tagRegion.getAttribute("aria-label"), "Media tags");
  assert.equal(tagButton.tagName, "BUTTON");
  assert.equal(tagButton.getAttribute("aria-label"), "Filter Gallery by Alpha");
  keyboardActivate(tagButton, " ");

  assert.deepEqual(activations, { card: 0, cardKeyboard: 0, details: 0, playback: 0, contextual: 0 });
  assert.equal(h.run("catalogState.tagKeys.join(',')"), "alpha");
  assert.equal(tagButton.getAttribute("aria-pressed"), "true");
  assert.equal(h.document.activeElement, h.catalogTagFilters.children[0]);
  assert.equal(h.catalogTagFilters.children[0].getAttribute("aria-label"), "Remove Alpha tag filter");

  const secondRegion = h.run("renderCatalogCardTags(item)");
  keyboardActivate(secondRegion.children[0], "Enter");
  assert.equal(h.run("catalogState.tagKeys.length"), 1);
  assert.equal(h.run("catalogLoadCalls"), 1);
});

test("Chip removal prefers next, then previous, then Search focus and permits removing all tags", () => {
  const h = createInteractionHarness();
  h.run(`canonicalTagDefinitions = [
    { key: "alpha", display_name: "Alpha" },
    { key: "beta", display_name: "Beta" },
    { key: "gamma", display_name: "Gamma" }
  ]; activateCatalogTagFilter("alpha"); activateCatalogTagFilter("beta"); activateCatalogTagFilter("gamma")`);

  keyboardActivate(h.catalogTagFilters.children[1], "Enter");
  assert.equal(h.run("catalogState.tagKeys.join(',')"), "alpha,gamma");
  assert.equal(h.document.activeElement.dataset.tagKey, "gamma");

  keyboardActivate(h.document.activeElement, "Enter");
  assert.equal(h.run("catalogState.tagKeys.join(',')"), "alpha");
  assert.equal(h.document.activeElement.dataset.tagKey, "alpha");

  keyboardActivate(h.document.activeElement, "Enter");
  assert.equal(h.run("catalogState.tagKeys.length"), 0);
  assert.equal(h.catalogTagFilters.hidden, true);
  assert.equal(h.document.activeElement, h.commandSearchInput);
});

test("Selected-card and empty-result presentation reconcile with filtered results", () => {
  const h = createInteractionHarness();
  const selected = h.document.createElement("article");
  selected.className = "catalog-card";
  selected.dataset.mediaId = "media-a";
  const other = h.document.createElement("article");
  other.className = "catalog-card";
  other.dataset.mediaId = "media-b";
  h.catalogResults.append(selected, other);
  h.run('metadataWorkspace.openMediaId = "media-a"; reconcileCatalogSelectedCard()');
  assert.equal(selected.classList.contains("catalog-card--selected"), true);
  assert.equal(other.classList.contains("catalog-card--selected"), false);

  h.catalogResults.replaceChildren(other);
  h.run("reconcileCatalogSelectedCard(); catalogState.q = 'needle'; catalogState.tagKeys = ['alpha']; renderCatalogEmptyState()");
  assert.equal(other.classList.contains("catalog-card--selected"), false);
  assert.equal(h.catalogStateEmpty.textContent, "No media match the current search and tag filters.");
});

test("Catalog request owners reject stale success, error, and finally work under adversarial timing", async () => {
  const requests = [];
  const h = createRequestHarness((url) => {
    const pending = deferred();
    requests.push({ url: String(url), pending });
    return pending.promise;
  });

  const oldRequest = h.run("loadCatalog()");
  h.run("setCatalogSearchText('new title'); catalogState.tagKeys = ['alpha', 'beta']; catalogState.collection = 'processed'; catalogState.offset = 30");
  const newRequest = h.run("loadCatalog()");
  assert.equal(requests[1].url, "/api/media?q=new+title&tag=alpha&tag=beta&collection=processed&limit=30&offset=30");

  requests[0].pending.resolve(response({ marker: "old", items: [], total: 1, limit: 30, offset: 0, q: "" }));
  await oldRequest;
  assert.equal(h.run("catalogRequestOwner.token"), 2, "stale finally must not release the newer owner");
  assert.deepEqual(JSON.parse(h.run("JSON.stringify(renderedPages)")), []);

  requests[1].pending.resolve(response({ marker: "new", items: [], total: 1, limit: 30, offset: 30, q: "new title" }));
  await newRequest;
  assert.deepEqual(JSON.parse(h.run("JSON.stringify(renderedPages)")), ["new"]);
  assert.equal(h.run("catalogRequestOwner"), null);

  const staleError = h.run("setCatalogSearchText('older error'); loadCatalog()");
  h.run("setCatalogSearchText('current'); catalogState.tagKeys = []; catalogState.collection = ''; catalogState.offset = 0");
  const current = h.run("loadCatalog()");
  requests[3].pending.resolve(response({ marker: "current", items: [], total: 0, limit: 30, offset: 0, q: "current" }));
  await current;
  requests[2].pending.reject(new Error("stale network failure"));
  await staleError;

  assert.deepEqual(JSON.parse(h.run("JSON.stringify(renderedPages)")), ["new", "current"]);
  assert.equal(h.run("catalogVisibleState"), "success");
  assert.notEqual(h.run("catalogPageSummary.textContent"), "Catalog page unavailable.");
});
