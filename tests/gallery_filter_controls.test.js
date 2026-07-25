const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");

const APP_PATH = path.resolve(__dirname, "../src/framenest/adapters/api/web/app.js");
const STYLES_PATH = path.resolve(__dirname, "../src/framenest/adapters/api/web/styles.css");
const APP_SOURCE = fs.readFileSync(APP_PATH, "utf8");
const STYLES_SOURCE = fs.readFileSync(STYLES_PATH, "utf8");

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

class TestClassList {
  constructor() {
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

class TestElement {
  constructor(document, tagName, id = "") {
    this.ownerDocument = document;
    this.tagName = String(tagName).toUpperCase();
    this.id = id;
    this.children = [];
    this.parentNode = null;
    this.dataset = {};
    this.attributes = new Map();
    this.listeners = new Map();
    this.classList = new TestClassList();
    this.hidden = false;
    this.disabled = false;
    this.textContent = "";
  }

  get className() {
    return this.classList.toString();
  }

  set className(value) {
    this.classList.setFromString(value);
  }

  setAttribute(name, value) {
    this.attributes.set(String(name).toLowerCase(), String(value));
  }

  getAttribute(name) {
    const key = String(name).toLowerCase();
    return this.attributes.has(key) ? this.attributes.get(key) : null;
  }

  addEventListener(type, listener) {
    if (!this.listeners.has(type)) this.listeners.set(type, []);
    this.listeners.get(type).push(listener);
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
    nodes.forEach((node) => this.appendChild(node));
  }

  focus() {}

  querySelectorAll(selector) {
    if (selector === ".catalog-filter-chip") {
      return this.children.filter((child) => child.classList.contains("catalog-filter-chip"));
    }
    if (selector === ".catalog-card__tag") {
      const results = [];
      const visit = (node) => {
        node.children.forEach((child) => {
          if (child.classList.contains("catalog-card__tag")) results.push(child);
          visit(child);
        });
      };
      visit(this);
      return results;
    }
    throw new Error(`unsupported selector: ${selector}`);
  }

  querySelector(selector) {
    return this.querySelectorAll(selector)[0] || null;
  }
}

class TestDocument {
  constructor() {
    this.body = new TestElement(this, "body");
    this.byId = new Map();
  }

  createElement(tagName) {
    return new TestElement(this, tagName);
  }

  register(element) {
    if (element.id) this.byId.set(element.id, element);
    this.body.appendChild(element);
    return element;
  }

  querySelector(selector) {
    const match = String(selector).match(/^#([A-Za-z0-9_-]+)$/);
    if (!match) throw new Error(`unsupported document selector: ${selector}`);
    return this.byId.get(match[1]) || null;
  }
}

function createFilterHarness() {
  const document = new TestDocument();
  const catalogScopeAll = document.register(new TestElement(document, "button", "catalog-scope-all"));
  catalogScopeAll.classList.add("scope-active");
  const catalogScopeProcessed = document.register(new TestElement(document, "button", "catalog-scope-processed"));
  const catalogFilterMemes = document.register(new TestElement(document, "button", "catalog-filter-memes"));
  catalogFilterMemes.setAttribute("aria-pressed", "false");
  const catalogFilterMovies = document.register(new TestElement(document, "button", "catalog-filter-movies"));
  catalogFilterMovies.setAttribute("aria-pressed", "false");
  const catalogFilterYoutube = document.register(new TestElement(document, "button", "catalog-filter-youtube"));
  catalogFilterYoutube.setAttribute("aria-pressed", "false");
  const catalogTagFilters = document.register(new TestElement(document, "div", "catalog-tag-filters"));
  catalogTagFilters.hidden = true;
  const catalogResults = document.register(new TestElement(document, "div", "catalog-results"));
  const commandSearchInput = document.register(new TestElement(document, "input", "command-search-input"));

  const context = {
    console,
    document,
    URLSearchParams,
    catalogTagFilters,
    catalogResults,
    commandSearchInput,
  };
  context.globalThis = context;
  vm.createContext(context);

  const functions = [
    "catalogHasNarrowingFilters",
    "catalogIsUnfilteredAllMedia",
    "syncCatalogFilterControls",
    "setCatalogClassificationFilter",
    "setCatalogScope",
    "resetCatalogToAllMedia",
    "snapshotCatalogQueryState",
    "buildCatalogQueryParams",
    "selectedTagDefinition",
    "catalogTagDisplayName",
    "renderActiveCatalogTagFilters",
    "renderCatalogTagFilterStates",
    "activateCatalogTagFilter",
    "removeCatalogTagFilter",
  ].map(productionFunction).join("\n");

  vm.runInContext(`
    const PROCESSED_COLLECTION = "processed";
    const CATALOG_PAGE_SIZE_OPTIONS = [10, 30, 60, 90];
    const CATALOG_PAGE_SIZE = 30;
    let catalogState = {
      q: "",
      tagKeys: [],
      collection: "",
      contentCategory: "",
      acquisitionSource: "",
      limit: 30,
      offset: 0,
      total: 0,
    };
    let canonicalTagDefinitions = [
      { key: "alpha", display_name: "Alpha" },
      { key: "beta", display_name: "Beta" },
    ];
    let metadataWorkspaceRevision = 0;
    let catalogLoadCalls = 0;
    function advanceMetadataWorkspaceRevision() { metadataWorkspaceRevision += 1; }
    function loadCatalog() { catalogLoadCalls += 1; }
    ${functions}
  `, context, { filename: APP_PATH });

  return {
    context,
    catalogScopeAll,
    catalogScopeProcessed,
    catalogFilterMemes,
    catalogFilterMovies,
    catalogFilterYoutube,
    catalogTagFilters,
    run(code) {
      return vm.runInContext(code, context);
    },
  };
}

test("All media is active only when no narrowing filters remain", () => {
  const h = createFilterHarness();
  assert.equal(h.run("catalogIsUnfilteredAllMedia()"), true);
  assert.equal(h.catalogScopeAll.classList.contains("scope-active"), true);

  h.run("activateCatalogTagFilter('alpha')");
  assert.equal(h.run("catalogIsUnfilteredAllMedia()"), false);
  assert.equal(h.catalogScopeAll.classList.contains("scope-active"), false);
  assert.equal(h.catalogTagFilters.hidden, false);
  assert.equal(h.catalogTagFilters.children.length, 1);

  h.run("setCatalogClassificationFilter({ contentCategory: 'meme' })");
  assert.equal(h.catalogFilterMemes.getAttribute("aria-pressed"), "true");
  assert.equal(h.catalogScopeAll.classList.contains("scope-active"), false);

  h.run("resetCatalogToAllMedia()");
  assert.equal(h.run("JSON.stringify(catalogState.tagKeys)"), "[]");
  assert.equal(h.run("catalogState.contentCategory"), "");
  assert.equal(h.run("catalogState.acquisitionSource"), "");
  assert.equal(h.run("catalogState.collection"), "");
  assert.equal(h.run("catalogIsUnfilteredAllMedia()"), true);
  assert.equal(h.catalogScopeAll.classList.contains("scope-active"), true);
  assert.equal(h.catalogFilterMemes.getAttribute("aria-pressed"), "false");
  assert.equal(h.catalogTagFilters.hidden, true);
});

test("All media clears quick collections and selected tags without changing AND query composition", () => {
  const h = createFilterHarness();
  h.run("activateCatalogTagFilter('alpha'); activateCatalogTagFilter('beta')");
  h.run("setCatalogClassificationFilter({ acquisitionSource: 'youtube_manual_claim' })");
  h.run("setCatalogScope(PROCESSED_COLLECTION)");

  assert.equal(h.catalogScopeProcessed.classList.contains("scope-active"), true);
  assert.equal(h.catalogFilterYoutube.getAttribute("aria-pressed"), "true");
  assert.equal(h.run("buildCatalogQueryParams().toString()"), "tag=alpha&tag=beta&collection=processed&acquisition_source=youtube_manual_claim&limit=30&offset=0");

  h.run("resetCatalogToAllMedia()");
  assert.equal(h.run("buildCatalogQueryParams().toString()"), "limit=30&offset=0");
  assert.equal(h.catalogScopeAll.classList.contains("scope-active"), true);
  assert.equal(h.catalogScopeProcessed.classList.contains("scope-active"), false);
  assert.equal(h.catalogFilterYoutube.getAttribute("aria-pressed"), "false");
});

test("Quick collection pressed state matches the actual catalog query", () => {
  const h = createFilterHarness();
  h.run("setCatalogClassificationFilter({ contentCategory: 'movie' })");
  assert.equal(h.catalogFilterMovies.getAttribute("aria-pressed"), "true");
  assert.equal(h.catalogFilterMemes.getAttribute("aria-pressed"), "false");
  assert.match(h.run("buildCatalogQueryParams().toString()"), /content_category=movie/);

  h.run("setCatalogClassificationFilter({ contentCategory: 'movie' })");
  assert.equal(h.catalogFilterMovies.getAttribute("aria-pressed"), "false");
  assert.equal(h.run("catalogState.contentCategory"), "");
  assert.equal(h.catalogScopeAll.classList.contains("scope-active"), true);
});

test("Selecting two tags keeps both active and preserves AND parameter order", () => {
  const h = createFilterHarness();
  h.run("activateCatalogTagFilter('alpha'); activateCatalogTagFilter('beta')");
  assert.equal(h.run("catalogState.tagKeys.join(',')"), "alpha,beta");
  assert.equal(h.run("buildCatalogQueryParams().toString()"), "tag=alpha&tag=beta&limit=30&offset=0");
  h.run("removeCatalogTagFilter('alpha', { restoreFocus: false })");
  assert.equal(h.run("catalogState.tagKeys.join(',')"), "beta");
  assert.equal(h.catalogScopeAll.classList.contains("scope-active"), false);
});

test("Quick-filter layout and active styles are FrameNest-owned rather than native-button defaults", () => {
  const classFiltersStart = STYLES_SOURCE.indexOf(".catalog-class-filters {");
  assert.notEqual(classFiltersStart, -1);
  const classFiltersEnd = STYLES_SOURCE.indexOf(".gallery-grid {", classFiltersStart);
  const classFiltersBlock = STYLES_SOURCE.slice(classFiltersStart, classFiltersEnd);
  assert.match(classFiltersBlock, /margin:\s*0 0 18px/);
  assert.match(classFiltersBlock, /appearance:\s*none/);
  assert.match(classFiltersBlock, /button\[aria-pressed="true"\]/);
  assert.match(classFiltersBlock, /var\(--accent-strong\)/);
  assert.match(classFiltersBlock, /outline:\s*2px solid var\(--focus\)/);

  const tagActiveStart = STYLES_SOURCE.indexOf('.catalog-card__tag[aria-pressed="true"]');
  const tagActiveBlock = STYLES_SOURCE.slice(tagActiveStart, tagActiveStart + 220);
  assert.match(tagActiveBlock, /var\(--accent-strong\)/);
  assert.match(tagActiveBlock, /rgba\(0, 255, 65, 0\.22\)/);
});
