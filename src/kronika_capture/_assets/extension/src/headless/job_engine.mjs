// Headless job engine: one plain ask over an owned Chromium driver.
//
// Search, web search, deep research, ingest, and authoring fail closed before
// any page action and are never rewritten into a plain ask. Selectors are
// read from the packaged pack_v5.json. File upload stays a hard failure.
//
// The engine uses the driver's public seam only: navigate, evaluate, send (raw
// CDP input events), clickXY, loginState, and stop. Page reads and writes go
// through generated expressions tagged `he4:<step>`.

import { setTimeout as delay } from "node:timers/promises";

import { BridgeHttpError } from "./bridge_client.mjs";

export const ROOT_URL = "https://chatgpt.com/";
export const ANSWER_HTML_MAX_CHARS = 1.5 * 1024 * 1024;
// WSC-3A correction: the ingest thresholds mirror the bridge caps exactly
// (src/kronika/config.py INGEST_PROMPT_MAX_CHARS,
// INGEST_ANSWER_MAX_CHARS, INGEST_ANSWER_HTML_MAX_CHARS): over-cap prompt or
// answer text fails the turn typed before staging, and over-cap answer HTML is
// omitted with the text fallback, exactly like the ask path.
export const INGEST_PROMPT_MAX_CHARS = 200000;
export const INGEST_ANSWER_MAX_CHARS = 1500000;
export const INGEST_ANSWER_HTML_MAX_CHARS = 1500000;
// WSC-5: the authoring prompt cap mirrors src/kronika/config.py
// AUTHOR_PROMPT_MAX_CHARS; the answer caps stay the ingest caps.
export const AUTHOR_PROMPT_MAX_CHARS = 4000;
export const COMPOSER_TIMEOUT_MS = 15000;
export const SUBMIT_TIMEOUT_MS = 10000;
// WSC6-CORRECTION-2: the deep-research acceptance window is longer than the
// default submit window because the initial research turn can take a moment to
// surface; every other mode keeps SUBMIT_TIMEOUT_MS. The bounded retry is
// decided once, after the smaller of SUBMIT_RETRY_AFTER_MS and half the mode
// window, and never exceeds two clicks in total.
export const DEEP_RESEARCH_SUBMIT_TIMEOUT_MS = 60000;
export const SUBMIT_RETRY_AFTER_MS = 5000;
export const CLEAR_TIMEOUT_MS = 3000;
export const MODE_TIMEOUT_MS = 5000;
export const DEFAULT_STABILITY_MS = 2500;
export const DEFAULT_POLL_MS = 500;
export const STOP_LINGER_FACTOR = 4;
export const ANSWER_TEXT_SELECTOR = ".markdown";
// HE-4b (live evidence 2026-09-17): the answer's `.markdown` wrapper can also
// contain follow-up suggestion chips. Their structural testid family is
// `writing-block-suggested-followups` (the container and its nested
// `-surface`); the family is excluded from the extracted text and HTML while
// the message body (including its writing-block title and heading lines)
// stays complete.
export const ANSWER_EXCLUDED_SELECTOR =
  '[data-testid^="writing-block-suggested-followups"]';
export const MAX_DIAGNOSTIC_CHARS = 200;

export class JobEngineError extends Error {
  constructor(code, step, message, diagnostics = null) {
    super(message);
    this.name = "JobEngineError";
    this.code = code;
    this.step = step;
    this.diagnostics = diagnostics;
  }
}

export function unsupportedJob(job) {
  if (!job || typeof job !== "object") {
    return new JobEngineError("E_INTERNAL", "kind", "unsupported job; nothing was sent");
  }
  if (job.kind !== "ask") {
    return new JobEngineError("E_INTERNAL", "kind", "unsupported kind; nothing was sent");
  }
  if (job.mode !== null && job.mode !== undefined) {
    const code =
      job.mode === "web_search"
        ? "E_WEB_SEARCH_UNAVAILABLE"
        : job.mode === "deep_research"
          ? "E_DEEP_RESEARCH_UNAVAILABLE"
          : "E_INTERNAL";
    return new JobEngineError(code, "mode", "unsupported mode; nothing was sent");
  }
  if (Array.isArray(job.files) && job.files.length > 0) {
    return new JobEngineError(
      "E_UPLOAD_FAILED",
      "upload",
      "file upload is not available in this build"
    );
  }
  return null;
}

export function normalizeText(value) {
  return String(value == null ? "" : value)
    .replace(/\s+/g, " ")
    .trim();
}

function boundedString(value, limit) {
  return typeof value === "string" ? value.slice(0, limit) : "";
}

/**
 * Parse a bridge-provided project object into a same-origin project URL and
 * its `g-p-...` path token, mirroring the extension semantics. Returns null
 * for anything that is not a chatgpt.com project URL.
 */
export function parseProject(project) {
  const url = project && typeof project.url === "string" ? project.url : "";
  let parsed = null;
  try {
    parsed = new URL(url);
  } catch {
    return null;
  }
  if (parsed.origin !== "https://chatgpt.com") return null;
  const segments = parsed.pathname.split("/").filter(Boolean);
  const token = segments.length > 1 ? segments[1] : "";
  if (segments[0] !== "g" || !token.startsWith("g-p-") || token.length <= 4) {
    return null;
  }
  return { url: parsed.href, token, pathname: parsed.pathname };
}

// WSC-3a conversation allowlist, mirroring src/kronika/bridge/jobs.py:
// exactly https://chatgpt.com/c/{id} or https://chatgpt.com/g/{slug}/c/{id},
// with no credentials, no non-default port, no query, and no fragment.
export const CONVERSATION_PATH_RE =
  /^\/(?:c\/[A-Za-z0-9_-]{1,64}|g\/[A-Za-z0-9_-]{1,64}\/c\/[A-Za-z0-9_-]{1,64})$/;
export const CONVERSATION_URL_MAX_CHARS = 2048;

export function validConversationUrl(url) {
  if (typeof url !== "string" || !url || url.length > CONVERSATION_URL_MAX_CHARS) {
    return false;
  }
  let parsed = null;
  try {
    parsed = new URL(url);
  } catch (error) {
    return false;
  }
  if (parsed.protocol !== "https:") return false;
  if (parsed.hostname !== "chatgpt.com") return false;
  if (parsed.username || parsed.password) return false;
  if (parsed.port && parsed.port !== "443") return false;
  if (parsed.search || parsed.hash) return false;
  return CONVERSATION_PATH_RE.test(parsed.pathname);
}

function messageNodesPrelude(pack) {
  const assistantSelectors = locatorSelectors(pack, "assistant_message");
  const userSelectors = locatorSelectors(pack, "user_message");
  return `
  const assistantSelectors = ${JSON.stringify(assistantSelectors)};
  const userSelectors = ${JSON.stringify(userSelectors)};
  const maxText = ${INGEST_PROMPT_MAX_CHARS + 1};
  const nodes = [];
  const pushAll = (selectors, role) => {
    for (const selector of selectors) {
      try {
        for (const node of document.querySelectorAll(selector)) nodes.push({ node, role });
      } catch (error) { /* a broken selector contributes nothing */ }
    }
  };
  pushAll(assistantSelectors, "assistant");
  pushAll(userSelectors, "user");
  nodes.sort((left, right) => {
    if (left.node === right.node) return 0;
    try {
      const position = left.node.compareDocumentPosition(right.node);
      if (position & Node.DOCUMENT_POSITION_FOLLOWING) return -1;
      if (position & Node.DOCUMENT_POSITION_PRECEDING) return 1;
    } catch (error) { /* keep the insertion order */ }
    return 0;
  });
  const boundText = (value) => {
    const text = String(value == null ? "" : value);
    return text.length > maxText ? text.slice(0, maxText) : text;
  };
  `;
}

export function conversationMessagesExpression(pack) {
  return `/* wsc3a:conversation_scan */ (() => {${messageNodesPrelude(pack)}
  const messages = nodes.map((entry) => ({ role: entry.role }));
  const assistant_count = messages.filter((entry) => entry.role === "assistant").length;
  return { messages, assistant_count };
})()`;
}

export function messageTextExpression(pack, ordinal) {
  const index = Number.isInteger(ordinal) && ordinal >= 0 ? ordinal : -1;
  return `/* wsc3a:message_text */ (() => {${messageNodesPrelude(pack)}
  const entry = nodes[${index}];
  if (!entry) return null;
  return { role: entry.role, text: boundText(entry.node.innerText || entry.node.textContent || "") };
})()`;
}

function cssSelectorFor(strategy) {
  if (!strategy || typeof strategy.value !== "string" || !strategy.value) {
    return null;
  }
  if (strategy.kind === "css") return strategy.value;
  if (strategy.kind === "testid") {
    return `[data-testid=${JSON.stringify(strategy.value)}]`;
  }
  if (strategy.kind === "role") {
    return `[role=${JSON.stringify(strategy.value)}]`;
  }
  return null;
}

function locatorSelectors(pack, key) {
  const locator = pack && pack.locators ? pack.locators[key] : null;
  if (!locator || !Array.isArray(locator.strategies)) return [];
  const selectors = [];
  for (const strategy of locator.strategies) {
    const selector = cssSelectorFor(strategy);
    if (selector && !selectors.includes(selector)) selectors.push(selector);
  }
  return selectors;
}

/**
 * Serialize locator strategies for page-context resolution. css/testid/role
 * stay selector-based; `text` carries the adapter-pack match fields.
 */
function locatorStrategiesPayload(pack, key) {
  const locator = pack && pack.locators ? pack.locators[key] : null;
  if (!locator || !Array.isArray(locator.strategies)) return [];
  const payload = [];
  for (const strategy of locator.strategies) {
    if (!strategy || typeof strategy.kind !== "string") continue;
    if (strategy.kind === "text") {
      if (typeof strategy.value !== "string" || !strategy.value) continue;
      payload.push({
        kind: "text",
        value: strategy.value,
        exact: strategy.exact !== false,
      });
      continue;
    }
    const selector = cssSelectorFor(strategy);
    if (selector) payload.push({ kind: strategy.kind, selector });
  }
  return payload;
}

export function locatorHitExpression(pack, key) {
  const strategies = locatorStrategiesPayload(pack, key);
  const composerSelectors =
    key === "web_search_pill" || key === "deep_research_pill"
      ? locatorSelectors(pack, "composer")
      : [];
  return tagged(
    key,
    `(() => {
  const __strategies = ${JSON.stringify(strategies)};
  const __composerSelectors = ${JSON.stringify(composerSelectors)};
  const __visible = (el) => {
    if (!el || el.nodeType !== 1 || !el.isConnected) return false;
    const style = window.getComputedStyle(el);
    if (!style || style.display === "none") return false;
    if (style.visibility === "hidden" || style.visibility === "collapse") return false;
    const rect = el.getBoundingClientRect();
    return rect.width > 0 && rect.height > 0;
  };
  const __normalize = (text) => String(text || "").replace(/\\s+/g, " ").trim().toLowerCase();
  const __clickableAncestor = (element, root) => {
    let node = element;
    while (node && node.nodeType === 1) {
      const tag = node.tagName ? node.tagName.toLowerCase() : "";
      if (tag === "button" || node.hasAttribute("role") || node.hasAttribute("tabindex")) {
        return node;
      }
      if (node === root || node === document.documentElement) break;
      node = node.parentElement;
    }
    return element;
  };
  const __hitFrom = (root, strategy) => {
    if (strategy.kind === "text") {
      const expected = __normalize(strategy.value);
      if (!expected) return null;
      let candidates = [];
      try { candidates = root.querySelectorAll("button, a, [role], div, span"); } catch (error) { return null; }
      for (const element of candidates) {
        if (!__visible(element)) continue;
        const text = __normalize(element.textContent);
        if (!text) continue;
        const matched = strategy.exact !== false ? text === expected : text.includes(expected);
        if (!matched) continue;
        return __clickableAncestor(element, root);
      }
      return null;
    }
    if (!strategy.selector) return null;
    let nodes = [];
    try { nodes = root.querySelectorAll(strategy.selector); } catch (error) { return null; }
    for (const node of nodes) { if (__visible(node)) return node; }
    return null;
  };
  let root = document;
  if (__composerSelectors.length > 0) {
    let composer = null;
    for (const selector of __composerSelectors) {
      let nodes = [];
      try { nodes = document.querySelectorAll(selector); } catch (error) { nodes = []; }
      for (const node of nodes) {
        if (__visible(node)) { composer = node; break; }
      }
      if (composer) break;
    }
    if (!composer) return null;
    root = composer;
  }
  for (const strategy of __strategies) {
    const node = __hitFrom(root, strategy);
    if (!node) continue;
    const rect = node.getBoundingClientRect();
    return {
      found: true,
      disabled:
        node.disabled === true || node.getAttribute("aria-disabled") === "true",
      rect: { x: rect.x, y: rect.y, width: rect.width, height: rect.height },
    };
  }
  return null;
})()`
  );
}

function tagged(tag, body) {
  return `/* he4:${tag} */ ${body}`;
}

const PAGE_HELPERS = (selectors) => `
  const __selectors = ${JSON.stringify(selectors)};
  const __visible = (el) => !!el && el.isConnected && el.getClientRects().length > 0;
  const __findAll = () => {
    const out = [];
    for (const selector of __selectors) {
      let nodes = [];
      try { nodes = document.querySelectorAll(selector); } catch (error) { nodes = []; }
      for (const node of nodes) { if (!out.includes(node)) out.push(node); }
    }
    return out;
  };
  const __findVisible = () => {
    for (const node of __findAll()) { if (__visible(node)) return node; }
    return null;
  };
`;

function composerStateExpression(pack) {
  const selectors = locatorSelectors(pack, "composer");
  return tagged(
    "composer_state",
    `(() => {
${PAGE_HELPERS(selectors)}
  const el = __findVisible();
  if (!el) return null;
  const tag = el.tagName ? el.tagName.toLowerCase() : "";
  const kind =
    tag === "textarea" ? "textarea" : el.isContentEditable ? "contenteditable" : "other";
  const rect = el.getBoundingClientRect();
  const raw = kind === "textarea" ? String(el.value || "") : el.innerText || el.textContent || "";
  return {
    kind,
    empty: raw.replace(/\\s+/g, " ").trim() === "",
    text_length: raw.length,
    rect: { x: rect.x, y: rect.y, width: rect.width, height: rect.height },
  };
})()`
  );
}

function composerInsertExpression(pack, value) {
  const selectors = locatorSelectors(pack, "composer");
  const literal = JSON.stringify(String(value));
  return tagged(
    "composer_insert",
    `(() => {
${PAGE_HELPERS(selectors)}
  const el = __findVisible();
  if (!el) return { ok: false, reason: "composer_missing", kind: null };
  try { el.focus(); } catch (error) { /* verification below decides */ }
  const tag = el.tagName ? el.tagName.toLowerCase() : "";
  if (tag === "textarea") {
    const descriptor = Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, "value");
    if (!descriptor || typeof descriptor.set !== "function") {
      return { ok: false, reason: "no_native_setter", kind: "textarea" };
    }
    descriptor.set.call(el, ${literal});
    el.dispatchEvent(new Event("input", { bubbles: true }));
    return { ok: true, reason: null, kind: "textarea" };
  }
  if (el.isContentEditable) {
    const selection = window.getSelection();
    if (!selection) return { ok: false, reason: "no_selection", kind: "contenteditable" };
    const range = document.createRange();
    range.selectNodeContents(el);
    range.collapse(false);
    selection.removeAllRanges();
    selection.addRange(range);
    let inserted = false;
    try { inserted = document.execCommand("insertText", false, ${literal}); } catch (error) { inserted = false; }
    return { ok: inserted === true, reason: inserted ? null : "exec_command_rejected", kind: "contenteditable" };
  }
  return { ok: false, reason: "unsupported_composer", kind: "other" };
})()`
  );
}

function composerContainsExpression(pack, value) {
  const selectors = locatorSelectors(pack, "composer");
  const literal = JSON.stringify(normalizeText(value));
  return tagged(
    "composer_contains",
    `(() => {
${PAGE_HELPERS(selectors)}
  const el = __findVisible();
  if (!el) return false;
  const tag = el.tagName ? el.tagName.toLowerCase() : "";
  const raw = tag === "textarea" ? String(el.value || "") : el.innerText || el.textContent || "";
  const normalize = (text) => String(text || "").replace(/\\s+/g, " ").trim();
  return normalize(raw).includes(${literal});
})()`
  );
}

function composerClearExpression(pack) {
  const selectors = locatorSelectors(pack, "composer");
  return tagged(
    "composer_clear",
    `(() => {
${PAGE_HELPERS(selectors)}
  const el = __findVisible();
  if (!el) return { ok: false, reason: "composer_missing" };
  try { el.focus(); } catch (error) { /* clearing still attempts below */ }
  const tag = el.tagName ? el.tagName.toLowerCase() : "";
  if (tag === "textarea") {
    const descriptor = Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, "value");
    if (descriptor && typeof descriptor.set === "function") {
      descriptor.set.call(el, "");
      el.dispatchEvent(new Event("input", { bubbles: true }));
    }
  } else if (el.isContentEditable) {
    const selection = window.getSelection();
    if (selection) {
      const range = document.createRange();
      range.selectNodeContents(el);
      selection.removeAllRanges();
      selection.addRange(range);
    }
    try { document.execCommand("delete"); } catch (error) { /* reported as not_empty */ }
  }
  const raw = tag === "textarea" ? String(el.value || "") : el.innerText || el.textContent || "";
  const empty = raw.replace(/\\s+/g, " ").trim() === "";
  return { ok: empty, reason: empty ? null : "not_empty" };
})()`
  );
}

function sendStateExpression(pack) {
  const selectors = locatorSelectors(pack, "send");
  return tagged(
    "send_state",
    `(() => {
${PAGE_HELPERS(selectors)}
  const el = __findVisible();
  if (!el) return null;
  const rect = el.getBoundingClientRect();
  return {
    disabled: el.disabled === true || el.getAttribute("aria-disabled") === "true",
    rect: { x: rect.x, y: rect.y, width: rect.width, height: rect.height },
  };
})()`
  );
}

// WSC6-CORRECTION-2: bounded metadata-only submit diagnostics. The read
// returns the send-control state, the composer shape (never its text), the
// user/assistant message counts straight from the pack locators, and up to
// three visible generic-ARIA dialog texts (120 chars each); the engine bounds
// every field again before it reaches a log or a result envelope.
function submitDiagnosticsExpression(pack) {
  const sendSelectors = locatorSelectors(pack, "send");
  const composerSelectors = locatorSelectors(pack, "composer");
  const assistantSelectors = locatorSelectors(pack, "assistant_message");
  const userSelectors = locatorSelectors(pack, "user_message");
  const webSearchPillSelectors = locatorSelectors(pack, "web_search_pill");
  const deepResearchPillSelectors = locatorSelectors(pack, "deep_research_pill");
  return tagged(
    "submit_diagnostics",
    `(() => {
  const __sendSelectors = ${JSON.stringify(sendSelectors)};
  const __composerSelectors = ${JSON.stringify(composerSelectors)};
  const __assistantSelectors = ${JSON.stringify(assistantSelectors)};
  const __userSelectors = ${JSON.stringify(userSelectors)};
  const __webSearchPillSelectors = ${JSON.stringify(webSearchPillSelectors)};
  const __deepResearchPillSelectors = ${JSON.stringify(deepResearchPillSelectors)};
  const __visible = (el) => !!el && el.isConnected && el.getClientRects().length > 0;
  const __firstVisible = (selectors) => {
    for (const selector of selectors) {
      let nodes = [];
      try { nodes = document.querySelectorAll(selector); } catch (error) { nodes = []; }
      for (const node of nodes) { if (__visible(node)) return node; }
    }
    return null;
  };
  const __countMatches = (selectors) => {
    let count = 0;
    for (const selector of selectors) {
      try { count += document.querySelectorAll(selector).length; } catch (error) { /* nothing */ }
    }
    return count;
  };
  const __rect = (el) => {
    try {
      const rect = el.getBoundingClientRect();
      return { x: rect.x, y: rect.y, width: rect.width, height: rect.height };
    } catch (error) { return null; }
  };
  const send = __firstVisible(__sendSelectors);
  const composer = __firstVisible(__composerSelectors);
  const composerTag = composer && composer.tagName ? composer.tagName.toLowerCase() : null;
  let composerText = "";
  if (composer) {
    composerText =
      composerTag === "textarea" ? String(composer.value || "") : composer.innerText || composer.textContent || "";
  }
  const dialogNodes = [];
  try {
    for (const node of document.querySelectorAll('[role="dialog"], [role="alertdialog"], [aria-modal="true"]')) {
      if (dialogNodes.length >= 64) break;
      dialogNodes.push(node);
    }
  } catch (error) { /* a broken dialog read contributes nothing */ }
  const dialogs = [];
  let dialogCount = 0;
  const seen = new Set();
  for (const node of dialogNodes) {
    if (!__visible(node) || seen.has(node)) continue;
    seen.add(node);
    dialogCount += 1;
    if (dialogs.length < 3) {
      dialogs.push(
        String(node.innerText || node.textContent || "").replace(/\\s+/g, " ").trim().slice(0, 120)
      );
    }
  }
  return {
    url_path: location.pathname,
    send: send
      ? {
          present: true,
          disabled: send.disabled === true || send.getAttribute("aria-disabled") === "true",
          rect: __rect(send),
        }
      : { present: false, disabled: null, rect: null },
    composer: {
      present: composer !== null,
      kind: composerTag,
      empty: composer !== null ? composerText.replace(/\\s+/g, " ").trim() === "" : null,
      text_length: composer !== null ? composerText.length : 0,
      web_search_pill: __firstVisible(__webSearchPillSelectors) !== null,
      deep_research_pill: __firstVisible(__deepResearchPillSelectors) !== null,
    },
    user_count: __countMatches(__userSelectors),
    assistant_count: __countMatches(__assistantSelectors),
    dialog_count: dialogCount,
    dialogs,
  };
})()`
  );
}

function stopVisibleExpression(pack) {
  const selectors = locatorSelectors(pack, "stop_control");
  return tagged(
    "stop_visible",
    `(() => {
${PAGE_HELPERS(selectors)}
  return __findVisible() !== null;
})()`
  );
}

export function assistantStateExpression(pack) {
  const selectors = locatorSelectors(pack, "assistant_message");
  return tagged(
    "assistant_state",
    `(() => {
${PAGE_HELPERS(selectors)}
  const nodes = __findAll();
  if (nodes.length === 0) return { count: 0, text: "", html: null, url: location.href };
  const node = nodes[nodes.length - 1];
  const markdown = node.querySelector ? node.querySelector(${JSON.stringify(ANSWER_TEXT_SELECTOR)}) : null;
  const source = markdown || node;
  const excluded = [];
  try {
    for (const element of source.querySelectorAll(${JSON.stringify(ANSWER_EXCLUDED_SELECTOR)})) {
      excluded.push(element);
    }
  } catch (error) { /* an unreadable exclusion list keeps the unfiltered read */ }
  // Text: hide the excluded suggestion/action containers for the read (innerText
  // keeps the body's rendering semantics) and restore them in the same call.
  const hidden = [];
  let text = "";
  try {
    for (const element of excluded) {
      hidden.push([element, element.style.display]);
      element.style.display = "none";
    }
    text = String(source.innerText || source.textContent || "").trim();
  } finally {
    for (const [element, previous] of hidden) {
      element.style.display = previous;
    }
  }
  // HTML: remove the same containers from a clone so the live page is untouched.
  let html = null;
  try {
    if (markdown) {
      const clone = markdown.cloneNode(true);
      for (const element of clone.querySelectorAll(${JSON.stringify(ANSWER_EXCLUDED_SELECTOR)})) {
        element.remove();
      }
      const raw = clone.innerHTML;
      if (typeof raw === "string" && raw.length > 0 && raw.length <= ${ANSWER_HTML_MAX_CHARS}) {
        html = raw;
      }
    }
  } catch (error) { html = null; }
  return { count: nodes.length, text, html, url: location.href };
})()`
  );
}

function loginWallExpression(pack) {
  const locator = pack && pack.locators ? pack.locators.login_wall : null;
  const strategies = (locator && Array.isArray(locator.strategies) ? locator.strategies : [])
    .filter((strategy) => strategy && typeof strategy.value === "string")
    .map((strategy) => ({ kind: strategy.kind, value: strategy.value }));
  return tagged(
    "login_wall",
    `(() => {
  const __strategies = ${JSON.stringify(strategies)};
  const __visible = (el) => !!el && el.isConnected && el.getClientRects().length > 0;
  for (const strategy of __strategies) {
    if (strategy.kind === "url_path") {
      if (location.pathname.includes(strategy.value)) return true;
      continue;
    }
    const selector =
      strategy.kind === "css" ? strategy.value
      : strategy.kind === "testid" ? "[data-testid=" + JSON.stringify(strategy.value) + "]"
      : strategy.kind === "role" ? "[role=" + JSON.stringify(strategy.value) + "]"
      : null;
    if (!selector) continue;
    let nodes = [];
    try { nodes = document.querySelectorAll(selector); } catch (error) { nodes = []; }
    for (const node of nodes) { if (__visible(node)) return true; }
  }
  return false;
})()`
  );
}

function urlExpression() {
  return tagged("url", "(() => location.href)()");
}

function pageDiagnosticsExpression() {
  return tagged(
    "page",
    `(() => ({ url_path: location.pathname, title: document.title || "" }))()`
  );
}

function projectTokenExpression(token) {
  return tagged(
    "project_token",
    `(() => location.pathname.includes(${JSON.stringify(String(token))}))()`
  );
}

export class JobEngine {
  constructor({
    driver,
    pack,
    emit = async () => {},
    isCancelled = () => false,
    deadlineMs = null,
    log = null,
    capture = null,
    captureIngest = null,
    postAsset = null,
    stageTurn = null,
    composerTimeoutMs = COMPOSER_TIMEOUT_MS,
    submitTimeoutMs = SUBMIT_TIMEOUT_MS,
    deepResearchSubmitTimeoutMs = DEEP_RESEARCH_SUBMIT_TIMEOUT_MS,
    submitRetryAfterMs = null,
    clearTimeoutMs = CLEAR_TIMEOUT_MS,
    modeTimeoutMs = MODE_TIMEOUT_MS,
  } = {}) {
    this.driver = driver;
    this.pack = pack && typeof pack === "object" ? pack : {};
    this.emit = emit;
    this.isCancelled = isCancelled;
    this.deadlineMs = Number.isFinite(deadlineMs) ? deadlineMs : null;
    this.log = typeof log === "function" ? log : () => {};
    this.capture = typeof capture === "function" ? capture : null;
    this.captureIngest = typeof captureIngest === "function" ? captureIngest : null;
    this.postAsset = typeof postAsset === "function" ? postAsset : null;
    this.stageTurn = typeof stageTurn === "function" ? stageTurn : null;
    this.composerTimeoutMs = composerTimeoutMs;
    this.submitTimeoutMs = submitTimeoutMs;
    this.deepResearchSubmitTimeoutMs =
      Number.isFinite(deepResearchSubmitTimeoutMs) &&
      deepResearchSubmitTimeoutMs > 0
        ? deepResearchSubmitTimeoutMs
        : DEEP_RESEARCH_SUBMIT_TIMEOUT_MS;
    this.submitRetryAfterMs =
      Number.isFinite(submitRetryAfterMs) && submitRetryAfterMs > 0
        ? submitRetryAfterMs
        : null;
    this.clearTimeoutMs = clearTimeoutMs;
    this.modeTimeoutMs =
      Number.isFinite(modeTimeoutMs) && modeTimeoutMs > 0
        ? modeTimeoutMs
        : MODE_TIMEOUT_MS;
    this.phase = "accepted";
    const constants = this.pack.constants || {};
    this.stabilityMs =
      Number.isFinite(constants.stability_ms) && constants.stability_ms > 0
        ? constants.stability_ms
        : DEFAULT_STABILITY_MS;
    this.pollMs =
      Number.isFinite(constants.poll_ms) && constants.poll_ms > 0
        ? constants.poll_ms
        : DEFAULT_POLL_MS;
    // Live evidence (2026-09-17): this ChatGPT build keeps the stop control
    // visible after a complete answer, so a still-visible control uses a
    // bounded linger window instead of blocking completion forever.
    this.stopLingerMs =
      Number.isFinite(constants.stop_linger_ms) && constants.stop_linger_ms > 0
        ? constants.stop_linger_ms
        : this.stabilityMs * STOP_LINGER_FACTOR;
  }

  async progress(phase) {
    this.phase = phase;
    await this.emit("progress", { phase });
  }

  async run(job) {
    let project = null;
    let result = null;
    const unsupported = unsupportedJob(job);
    if (unsupported) {
      return this._failureResult(unsupported);
    }
    try {
      if (job.project) {
        await this.progress("project");
        project = parseProject(job.project);
        if (!project) {
          throw new JobEngineError(
            "E_PROJECT_UNAVAILABLE",
            "project",
            "the configured project is not a chatgpt.com project URL; nothing was sent"
          );
        }
        await this._navigate(project.url, {
          code: "E_PROJECT_UNAVAILABLE",
          step: "project",
          message: "the project page did not load; nothing was sent",
        });
      }
      await this.progress("new_chat");
      if (!project && job.new_chat !== false) {
        await this._navigate(ROOT_URL, {
          code: "E_INTERNAL",
          step: "new_chat",
          message: "the chatgpt.com page did not load",
        });
      } else if (!project) {
        const href = await this._currentUrl();
        if (!/^https:\/\/chatgpt\.com\//.test(href)) {
          await this._navigate(ROOT_URL, {
            code: "E_INTERNAL",
            step: "new_chat",
            message: "the chatgpt.com page did not load",
          });
        }
      }
      await this._ensureComposer();
      if (project && !(await this._assertProject(project))) {
        throw new JobEngineError(
          "E_PROJECT_UNAVAILABLE",
          "project",
          "the page is not inside the configured project; nothing was sent",
          await this._pageDiagnostics()
        );
      }
      await this.progress("composed");
      await this._insertPrompt(job.prompt);
      await this.progress("sent");
      const submitted = await this._submit({});
      await this.progress("observing");
      const observed = await this._observeAnswer({ baseline: submitted.baseline });
      const answerHtml = null;
      let projectOk;
      if (project) {
        projectOk = await this._assertProject(project);
        if (!projectOk) await this.progress("project_warning");
      }
      result = {
        status: "done",
        answer: observed.text,
        answer_html: answerHtml,
        error_code: null,
        url: observed.url,
      };
      if (project) result.project_ok = projectOk === true;
    } catch (error) {
      result = this._failureResult(error);
    } finally {
      try {
        await this._clearComposer();
      } catch (error) {
        try {
          await this.emit("progress", { phase: "cleanup_warning" });
        } catch (emitError) {
          // a failed warning must never mask the job result
        }
      }
    }
    return result;
  }

  async _runDeepResearch() {
    throw new JobEngineError(
      "E_DEEP_RESEARCH_UNAVAILABLE",
      "mode",
      "deep research is not available in this build; nothing was sent"
    );
  }

  async _captureAssets() {
    return null;
  }

  async runIngest() {
    throw new JobEngineError(
      "E_INTERNAL",
      "kind",
      "ingest is not available in this build; nothing was sent"
    );
  }

  async runAuthor() {
    throw new JobEngineError(
      "E_INTERNAL",
      "kind",
      "authoring is not available in this build; nothing was sent"
    );
  }

  async _lastUserMessageText(conversation) {
    const messages = conversation.messages || [];
    for (let index = messages.length - 1; index >= 0; index -= 1) {
      if (messages[index] && messages[index].role === "user") {
        const entry = await this.driver.evaluate(
          messageTextExpression(this.pack, index)
        );
        return entry && typeof entry.text === "string" ? entry.text : "";
      }
    }
    return "";
  }

  async _conversationMessages() {
    const state = await this.driver.evaluate(
      conversationMessagesExpression(this.pack)
    );
    if (!state || typeof state !== "object" || !Array.isArray(state.messages)) {
      return null;
    }
    const messages = state.messages;
    return {
      messages,
      assistant_count: Number.isInteger(state.assistant_count)
        ? state.assistant_count
        : messages.filter((message) => message && message.role === "assistant")
            .length,
    };
  }

  async _classifyConversationBlocked(count, expected) {
    const diagnostics = await this._pageDiagnostics();
    try {
      if (await this.driver.evaluate(loginWallExpression(this.pack))) {
        return new JobEngineError(
          "E_LOGIN_REQUIRED",
          "conversation",
          "the chatgpt.com page is a login wall; log in first",
          diagnostics
        );
      }
    } catch (error) {
      // a failed wall read falls through to the structural login state
    }
    try {
      const state = await this.driver.loginState();
      const withStep = diagnostics
        ? { ...diagnostics, login_step: boundedString(state && state.step, 32) }
        : diagnostics;
      if (state && state.has_captcha === true) {
        return new JobEngineError(
          "E_CAPTCHA_REQUIRED",
          "conversation",
          "a CAPTCHA challenge is present; solving is manual",
          withStep
        );
      }
      if (
        state &&
        (state.step === "email" ||
          state.step === "password" ||
          state.step === "otp" ||
          state.step === "sso")
      ) {
        return new JobEngineError(
          "E_LOGIN_REQUIRED",
          "conversation",
          "the chatgpt.com page requires login before the check can run",
          withStep
        );
      }
      if (state && state.step === "unknown") {
        return new JobEngineError(
          "E_LOGIN_REQUIRED",
          "conversation",
          "no conversation and no known login step appeared; the page is likely a login wall",
          withStep
        );
      }
    } catch (error) {
      // structural login-state read failure does not mask the baseline error
    }
    return new JobEngineError(
      "E_CONVERSATION_UNAVAILABLE",
      "conversation",
      `the conversation shows ${count} assistant messages; the stored baseline is ${expected}`,
      diagnostics
    );
  }

  _failureResult(error) {
    if (error instanceof JobEngineError) {
      if (error.code === "E_CANCELLED") {
        return {
          status: "cancelled",
          answer: null,
          answer_html: null,
          error_code: "E_CANCELLED",
          url: null,
          step: error.step,
        };
      }
      return {
        status: "failed",
        answer: null,
        answer_html: null,
        error_code: error.code,
        url: null,
        step: error.step,
        diagnostics: error.diagnostics || null,
      };
    }
    if (error instanceof BridgeHttpError) {
      const step =
        typeof error.step === "string" && error.step ? error.step : this.phase;
      return {
        status: "failed",
        answer: null,
        answer_html: null,
        error_code: error.code,
        url: null,
        step,
        diagnostics: null,
        message: error.message ? String(error.message) : null,
      };
    }
    return {
      status: "failed",
      answer: null,
      answer_html: null,
      error_code: "E_INTERNAL",
      url: null,
      step: this.phase,
      diagnostics: null,
      message: error && error.message ? String(error.message) : null,
    };
  }

  async _navigate(url, failure) {
    try {
      await this.driver.navigate(url);
    } catch (error) {
      const detail = error && error.code ? String(error.code) : "navigation failed";
      throw new JobEngineError(
        failure.code,
        failure.step,
        `${failure.message} (${detail})`,
        await this._pageDiagnostics()
      );
    }
  }

  async _currentUrl() {
    const value = await this.driver.evaluate(urlExpression());
    return typeof value === "string" ? value : "";
  }

  async _pageDiagnostics() {
    try {
      const raw = await this.driver.evaluate(pageDiagnosticsExpression());
      return {
        url_path: boundedString(raw && raw.url_path, MAX_DIAGNOSTIC_CHARS),
        title: boundedString(raw && raw.title, MAX_DIAGNOSTIC_CHARS),
      };
    } catch (error) {
      return null;
    }
  }

  async _composerState() {
    return await this.driver.evaluate(composerStateExpression(this.pack));
  }

  async _ensureComposer() {
    const deadline = Date.now() + this.composerTimeoutMs;
    for (;;) {
      if (this.isCancelled()) {
        throw new JobEngineError("E_CANCELLED", "composer", "cancelled");
      }
      const state = await this._composerState();
      if (state && state.kind !== "other") return state;
      if (Date.now() >= deadline) break;
      await delay(Math.min(this.pollMs, Math.max(1, deadline - Date.now())));
    }
    throw await this._classifyBlocked();
  }

  async _classifyBlocked() {
    const diagnostics = await this._pageDiagnostics();
    try {
      if (await this.driver.evaluate(loginWallExpression(this.pack))) {
        return new JobEngineError(
          "E_LOGIN_REQUIRED",
          "composer",
          "the chatgpt.com page is a login wall; log in first",
          diagnostics
        );
      }
    } catch (error) {
      // a failed wall read falls through to the structural login state
    }
    try {
      const state = await this.driver.loginState();
      const withStep = diagnostics
        ? { ...diagnostics, login_step: boundedString(state && state.step, 32) }
        : diagnostics;
      if (state && state.has_captcha === true) {
        return new JobEngineError(
          "E_CAPTCHA_REQUIRED",
          "composer",
          "a CAPTCHA challenge is present; solving is manual",
          withStep
        );
      }
      if (
        state &&
        (state.step === "email" ||
          state.step === "password" ||
          state.step === "otp" ||
          state.step === "sso")
      ) {
        return new JobEngineError(
          "E_LOGIN_REQUIRED",
          "composer",
          "the chatgpt.com page requires login before the job can run",
          withStep
        );
      }
      if (state && state.step === "unknown") {
        return new JobEngineError(
          "E_LOGIN_REQUIRED",
          "composer",
          "no composer and no known login step appeared; the page is likely a login wall or an interstitial",
          withStep
        );
      }
    } catch (error) {
      // structural login-state read failure does not mask the composer error
    }
    return new JobEngineError(
      "E_COMPOSER_NOT_FOUND",
      "composer",
      `the composer did not appear within ${this.composerTimeoutMs} ms`,
      diagnostics
    );
  }

  async _assertProject(project) {
    return (await this.driver.evaluate(projectTokenExpression(project.token))) === true;
  }

  _validRect(rect) {
    return (
      rect &&
      Number.isFinite(rect.x) &&
      Number.isFinite(rect.y) &&
      Number.isFinite(rect.width) &&
      Number.isFinite(rect.height)
    );
  }

  async _locatorHit(key) {
    const raw = await this.driver.evaluate(locatorHitExpression(this.pack, key));
    if (!raw || raw.found !== true || !this._validRect(raw.rect)) return null;
    return raw;
  }

  async _webSearchActive() {
    return (await this._locatorHit("web_search_pill")) !== null;
  }

  async _clickRect(rect) {
    const x = Math.round(rect.x + rect.width / 2);
    const y = Math.round(rect.y + rect.height / 2);
    await this.driver.clickXY(x, y);
  }

  async _pressEscape() {
    try {
      await this.driver.send("Input.dispatchKeyEvent", {
        type: "keyDown",
        key: "Escape",
        code: "Escape",
      });
      await this.driver.send("Input.dispatchKeyEvent", {
        type: "keyUp",
        key: "Escape",
        code: "Escape",
      });
    } catch (error) {
      // best-effort close of the plus menu on mode failure only
    }
  }

  _modeFailure(error, fallbackMessage, code = "E_WEB_SEARCH_UNAVAILABLE") {
    if (
      error instanceof JobEngineError &&
      (error.code === "E_CANCELLED" || error.code === code)
    ) {
      return error;
    }
    const message =
      error && error.message
        ? String(error.message)
        : fallbackMessage || "the mode could not be enabled";
    return new JobEngineError(code, "mode", message);
  }

  async _enableWebSearch() {
    throw new JobEngineError(
      "E_WEB_SEARCH_UNAVAILABLE",
      "mode",
      "web search is not available in this build; nothing was sent"
    );
  }

  async _deepResearchActive() {
    return (await this._locatorHit("deep_research_pill")) !== null;
  }

  _assertDeepResearchDeadline() {
    if (this.deadlineMs !== null && Date.now() >= this.deadlineMs) {
      throw new JobEngineError(
        "E_DEEP_RESEARCH_UNAVAILABLE",
        "mode",
        "the job deadline expired before the deep-research query was sent; nothing was sent"
      );
    }
  }

  async _assertDeepResearchActive(message) {
    if (!(await this._deepResearchActive())) {
      throw new JobEngineError(
        "E_DEEP_RESEARCH_UNAVAILABLE",
        "mode",
        message || "the deep-research pill was lost; nothing was sent"
      );
    }
    if (await this._webSearchActive()) {
      throw new JobEngineError(
        "E_DEEP_RESEARCH_UNAVAILABLE",
        "mode",
        "a web-search pill is simultaneously present; nothing was sent"
      );
    }
  }

  async _enableDeepResearch() {
    throw new JobEngineError(
      "E_DEEP_RESEARCH_UNAVAILABLE",
      "mode",
      "deep research is not available in this build; nothing was sent"
    );
  }

  async _insertPrompt(prompt, { webSearch = false, deepResearch = false } = {}) {
    const value = String(prompt == null ? "" : prompt);
    const label = deepResearch ? "deep-research" : "web-search";
    const verifyMode = async (message) => {
      if (webSearch && !(await this._webSearchActive())) {
        throw new JobEngineError(
          "E_WEB_SEARCH_UNAVAILABLE",
          "mode",
          `the ${label} ${message}`
        );
      }
      if (deepResearch) {
        await this._assertDeepResearchActive(`the ${label} ${message}`);
      }
    };
    await verifyMode("pill is not active before insertion");
    await this.driver.evaluate(composerInsertExpression(this.pack, value));
    if (await this._composerContains(value)) {
      await verifyMode("pill was lost during insertion");
      return;
    }
    if (!webSearch && !deepResearch) {
      await this._clearComposer({ strict: false });
    }
    try {
      await this.driver.send("Input.insertText", { text: value });
    } catch (error) {
      // the next verification decides
    }
    if (await this._composerContains(value)) {
      await verifyMode("pill was lost during insertion");
      return;
    }
    if (!webSearch && !deepResearch) {
      await this._clearComposer({ strict: false });
    }
    try {
      await this._typeCharacters(value);
    } catch (error) {
      // the final verification below fails typed
    }
    if (await this._composerContains(value)) {
      await verifyMode("pill was lost during insertion");
      return;
    }
    throw new JobEngineError(
      "E_INPUT_FAILED",
      "compose",
      "the composer text does not contain the prompt after the verified insertion attempts"
    );
  }

  async _composerContains(value) {
    const contained = await this.driver.evaluate(
      composerContainsExpression(this.pack, value)
    );
    return contained === true;
  }

  async _typeCharacters(value) {
    for (const character of String(value)) {
      if (this.isCancelled()) {
        throw new JobEngineError("E_CANCELLED", "compose", "cancelled");
      }
      await this.driver.send("Input.dispatchKeyEvent", {
        type: "keyDown",
        key: character,
      });
      await this.driver.send("Input.dispatchKeyEvent", {
        type: "char",
        key: character,
        text: character,
        unmodifiedText: character,
      });
      await this.driver.send("Input.dispatchKeyEvent", {
        type: "keyUp",
        key: character,
      });
    }
  }

  async _clearComposer({ strict = true } = {}) {
    const outcome = await this.driver.evaluate(composerClearExpression(this.pack));
    if (strict && (!outcome || outcome.ok !== true)) {
      throw new JobEngineError(
        "E_INPUT_FAILED",
        "cleanup",
        "the composer could not be cleared"
      );
    }
    return outcome;
  }

  async _sendState() {
    return await this.driver.evaluate(sendStateExpression(this.pack));
  }

  async _stopVisible() {
    return (await this.driver.evaluate(stopVisibleExpression(this.pack))) === true;
  }

  async _assistantState() {
    const state = await this.driver.evaluate(assistantStateExpression(this.pack));
    if (!state || typeof state !== "object") {
      return { count: 0, text: "", html: null, url: "" };
    }
    return state;
  }

  async _waitFor(predicate, timeoutMs, step) {
    const deadline = Date.now() + timeoutMs;
    for (;;) {
      if (this.isCancelled()) {
        throw new JobEngineError("E_CANCELLED", step, "cancelled");
      }
      const value = await predicate();
      if (value) return value;
      if (Date.now() >= deadline) return null;
      await delay(Math.min(this.pollMs, Math.max(1, deadline - Date.now())));
    }
  }

  _submitAcceptanceWindowMs(mode) {
    const windowMs =
      mode === "deep_research"
        ? this.deepResearchSubmitTimeoutMs
        : this.submitTimeoutMs;
    return Number.isFinite(windowMs) && windowMs > 0
      ? windowMs
      : SUBMIT_TIMEOUT_MS;
  }

  _submitRetryAfterMs(windowMs) {
    if (this.submitRetryAfterMs !== null) {
      return Math.min(this.submitRetryAfterMs, windowMs);
    }
    return Math.min(SUBMIT_RETRY_AFTER_MS, Math.max(1, Math.floor(windowMs / 2)));
  }

  async _conversationUserCount() {
    const scan = await this._conversationMessages();
    const messages = scan && Array.isArray(scan.messages) ? scan.messages : [];
    let count = 0;
    for (const message of messages) {
      if (message && message.role === "user") count += 1;
    }
    return count;
  }

  async _submitSignal({ userBaseline, assistantBaseline }) {
    const send = await this._sendState();
    if (!send || send.disabled === true) return "sendGone";
    if ((await this._conversationUserCount()) > userBaseline) {
      return "userAppeared";
    }
    if ((await this._assistantState()).count > assistantBaseline) {
      return "assistantAppeared";
    }
    return null;
  }

  async _retrySubmitCandidate(mode, userBaseline, assistantBaseline) {
    // WSC6-CORRECTION-2: the single bounded retry is allowed only while every
    // observable "the first click did nothing" precondition still holds. All
    // reads happen immediately before the click; a single no-change failure
    // cancels the retry, so the click can never become a third click.
    const composer = await this._composerState();
    if (!composer || composer.empty === true) return null;
    const send = await this._sendState();
    if (!send || send.disabled === true || !this._validRect(send.rect)) {
      return null;
    }
    if ((await this._conversationUserCount()) > userBaseline) return null;
    if (mode === "deep_research") {
      await this._assertDeepResearchActive(
        "the deep-research pill was lost before the optional second send click; nothing was sent"
      );
    }
    if ((await this._assistantState()).count > assistantBaseline) return null;
    const remeasured = await this._sendState();
    if (
      !remeasured ||
      remeasured.disabled === true ||
      !this._validRect(remeasured.rect)
    ) {
      return null;
    }
    return remeasured;
  }

  async _submitDiagnostics() {
    const diagnostics = {
      url_path: "",
      send: { present: false, disabled: null, rect: null },
      composer: {
        present: false,
        kind: null,
        empty: null,
        text_length: 0,
        web_search_pill: false,
        deep_research_pill: false,
      },
      user_count: 0,
      assistant_count: 0,
      dialog_count: 0,
      dialogs: [],
    };
    try {
      const raw = await this.driver.evaluate(
        submitDiagnosticsExpression(this.pack)
      );
      if (!raw || typeof raw !== "object") return diagnostics;
      diagnostics.url_path = boundedString(raw.url_path, MAX_DIAGNOSTIC_CHARS);
      const send = raw.send && typeof raw.send === "object" ? raw.send : null;
      diagnostics.send = {
        present: Boolean(send && send.present === true),
        disabled: send && typeof send.disabled === "boolean" ? send.disabled : null,
        rect:
          send && this._validRect(send.rect)
            ? {
                x: send.rect.x,
                y: send.rect.y,
                width: send.rect.width,
                height: send.rect.height,
              }
            : null,
      };
      const composer =
        raw.composer && typeof raw.composer === "object" ? raw.composer : null;
      diagnostics.composer = {
        present: Boolean(composer && composer.present === true),
        kind: boundedString(composer && composer.kind, 32),
        empty: composer && typeof composer.empty === "boolean" ? composer.empty : null,
        text_length:
          composer && Number.isFinite(composer.text_length)
            ? Math.max(0, Math.floor(composer.text_length))
            : 0,
        web_search_pill: Boolean(composer && composer.web_search_pill === true),
        deep_research_pill: Boolean(composer && composer.deep_research_pill === true),
      };
      diagnostics.user_count =
        Number.isInteger(raw.user_count) && raw.user_count >= 0
          ? raw.user_count
          : 0;
      diagnostics.assistant_count =
        Number.isInteger(raw.assistant_count) && raw.assistant_count >= 0
          ? raw.assistant_count
          : 0;
      diagnostics.dialog_count =
        Number.isInteger(raw.dialog_count) && raw.dialog_count >= 0
          ? raw.dialog_count
          : 0;
      diagnostics.dialogs = Array.isArray(raw.dialogs)
        ? raw.dialogs
            .filter((text) => typeof text === "string")
            .slice(0, 3)
            .map((text) => text.slice(0, 120))
        : [];
    } catch (error) {
      // a failed diagnostics read keeps the structural defaults
    }
    return diagnostics;
  }

  async _submit({ mode = null } = {}) {
    const ready = await this._waitFor(
      async () => {
        const state = await this._sendState();
        if (!state || state.disabled === true) return null;
        if (!this._validRect(state.rect)) return null;
        return state;
      },
      this.submitTimeoutMs,
      "submit"
    );
    if (!ready) {
      throw new JobEngineError(
        "E_SEND_NOT_READY",
        "submit",
        "the send control never became ready"
      );
    }
    if (mode === "deep_research") {
      await this._assertDeepResearchActive(
        "the deep-research pill was lost after the send-ready wait; nothing was sent"
      );
    }
    if (mode === "deep_research") {
      await this._assertDeepResearchActive(
        "the deep-research pill was lost immediately before submit; nothing was sent"
      );
    }
    const assistantBaseline = (await this._assistantState()).count;
    const userBaseline = await this._conversationUserCount();
    const windowMs = this._submitAcceptanceWindowMs(mode);
    const retryAfterMs = this._submitRetryAfterMs(windowMs);
    const started = Date.now();
    const deadline = started + windowMs;
    let clicks = 1;
    let retried = false;
    await this._clickRect(ready.rect);
    for (;;) {
      if (this.isCancelled()) {
        throw new JobEngineError("E_CANCELLED", "submit", "cancelled");
      }
      const signal = await this._submitSignal({ userBaseline, assistantBaseline });
      if (signal) {
        this.log(`submit: accepted (${signal}) with ${clicks} click(s)`);
        return { baseline: assistantBaseline, submit_clicks: clicks };
      }
      const now = Date.now();
      if (!retried && now - started >= retryAfterMs) {
        retried = true;
        const candidate = await this._retrySubmitCandidate(
          mode,
          userBaseline,
          assistantBaseline
        );
        if (candidate) {
          clicks += 1;
          this.log(`submit: re-measured the send control and clicked once more (click ${clicks})`);
          await this.emit("progress", { phase: "sent", submit_clicks: clicks });
          await this._clickRect(candidate.rect);
          continue;
        }
      }
      if (now >= deadline) break;
      await delay(Math.min(this.pollMs, Math.max(1, deadline - Date.now())));
    }
    const diagnostics = await this._submitDiagnostics();
    diagnostics.submit_clicks = clicks;
    throw new JobEngineError(
      "E_SEND_FAILED",
      "submit",
      clicks > 1
        ? "neither send click was accepted within the mode window"
        : "the send click was not accepted within the mode window",
      diagnostics
    );
  }

  async _observeAnswer({ baseline }) {
    const requested =
      this.deadlineMs !== null ? this.deadlineMs - Date.now() : 600000;
    const deadline = Date.now() + Math.max(requested, 1);
    let lastText = null;
    let lastChange = Date.now();
    let lastStop = false;
    let started = false;
    for (;;) {
      if (this.isCancelled()) {
        throw new JobEngineError("E_CANCELLED", "observe", "cancelled");
      }
      const state = await this._assistantState();
      const now = Date.now();
      if (state.count > baseline) {
        started = true;
        const stop = await this._stopVisible();
        if (stop !== lastStop) {
          lastStop = stop;
          lastChange = now;
        }
        if (state.text !== lastText) {
          lastText = state.text;
          lastChange = now;
        } else if (
          state.text &&
          now - lastChange >= (stop ? this.stopLingerMs : this.stabilityMs)
        ) {
          if (stop) {
            this.log(
              "observe: the stop control stayed visible after the answer stabilized; returning the stable answer"
            );
          }
          return { text: state.text, html: state.html, url: state.url };
        } else if (
          !stop &&
          !state.text &&
          now - lastChange >= this.stabilityMs * 2
        ) {
          throw new JobEngineError(
            "E_RESPONSE_EMPTY",
            "observe",
            "the assistant message stayed empty"
          );
        }
      }
      if (Date.now() >= deadline) break;
      await delay(Math.min(this.pollMs, Math.max(1, deadline - Date.now())));
    }
    if (!started) {
      throw new JobEngineError(
        "E_RESPONSE_TIMEOUT",
        "observe",
        "no assistant message appeared before the deadline"
      );
    }
    throw new JobEngineError(
      "E_RESPONSE_TIMEOUT",
      "observe",
      "the answer did not stabilize before the deadline"
    );
  }
}
