// Bounded headless Chromium driver over raw CDP (HE-3c).
//
// Chromium uses an explicit executable and a durable launch brake outside its profile.
// CDP discovery consumes only a bounded endpoint line from process stderr.
//
// The HE-2d wizard helpers read only structural login state (`loginState`),
// focus and fill a login field (`fillField`), click a known control
// (`clickTarget`) or a viewport point (`clickXY`), and capture a single
// bounded snapshot (`snapshotPng`). No continuous streaming exists here.
//
// HE-2f makes the login interaction verifiable: `fillField` verifies the value
// and, when a submit control exists, that it is not disabled, falling back to
// the native setter and then to per-character key events, and finally failing
// with the typed `E_LOGIN_FILL_FAILED`; `clickTarget` rejects a missing or
// disabled control with `E_LOGIN_CLICK_FAILED` and a submit click that leaves
// the step and messages unchanged for the bounded wait with
// `E_LOGIN_NO_PROGRESS`. No value is ever included in an error.

import { spawn, spawnSync } from "node:child_process";
import { constants, openSync, closeSync, fsyncSync, writeFileSync, readFileSync, mkdirSync, rmdirSync, renameSync, statSync, lstatSync, realpathSync } from "node:fs";
import { access } from "node:fs/promises";
import { basename, dirname, isAbsolute, join } from "node:path";
import { setTimeout as delay } from "node:timers/promises";

import {
  CdpClient,
  DriverError,
  assertLoopbackHost,
  loopbackUrl,
} from "./cdp_client.mjs";

export { DriverError, loopbackUrl };

export const DEFAULT_START_TIMEOUT_MS = 20000;
export const DEFAULT_STOP_GRACE_MS = 5000;
export const DEFAULT_CDP_TIMEOUT_MS = 20000;
export const DEFAULT_LOAD_TIMEOUT_MS = 30000;
export const DEFAULT_SETTLE_MS = 1500;
export const DEFAULT_NO_PROGRESS_TIMEOUT_MS = 8000;
export const DEFAULT_NO_PROGRESS_POLL_MS = 500;

export const MAX_LABELS = 5;
export const MAX_LABEL_CHARS = 120;
export const MAX_MESSAGES = 4;
export const MAX_MESSAGE_CHARS = 200;
export const MAX_URL_PATH_CHARS = 200;
export const MAX_FINGERPRINT_UA_CHARS = 300;

const LOGIN_STEPS = new Set([
  "email",
  "password",
  "otp",
  "captcha",
  "sso",
  "done",
  "unknown",
]);

export const LOGIN_FIELDS = {
  email: ["input#email-input", "input[name='email']", "input[type='email']"],
  password: ["input[type='password']", "input#password"],
  otp: [
    "input[autocomplete='one-time-code']",
    "input#code",
    "input[name='code']",
  ],
};

const LOGIN_STATE_EXPRESSION = `(() => {
  const visible = (el) => !!el && el.getClientRects().length > 0;
  const pick = (selectors) => {
    for (const selector of selectors) {
      const candidate = document.querySelector(selector);
      if (visible(candidate)) return candidate;
    }
    return null;
  };
  const clampText = (value, limit) =>
    String(value || "").replace(/\\s+/g, " ").trim().slice(0, limit);
  const rectOf = (el) => {
    if (!el) return null;
    const rect = el.getBoundingClientRect();
    if (!(rect.width > 1) || !(rect.height > 1)) return null;
    return {
      x: Math.round(rect.x),
      y: Math.round(rect.y),
      w: Math.round(rect.width),
      h: Math.round(rect.height),
    };
  };
  const emailInput = pick([
    "input#email-input",
    "input[name='email']",
    "input[type='email']",
  ]);
  const passwordInput = pick(["input[type='password']", "input#password"]);
  const otpInput = pick([
    "input[autocomplete='one-time-code']",
    "input#code",
    "input[name='code']",
  ]);
  const composer = pick([
    "div#prompt-textarea[contenteditable='true']",
    "textarea[name='prompt-textarea']",
  ]);
  const captcha = pick([
    "iframe[src*='hcaptcha.com']",
    "iframe[src*='challenges.cloudflare.com']",
    "iframe[src*='recaptcha']",
    "iframe[title*='captcha' i]",
    "[data-sitekey]",
    "[class*='h-captcha']",
  ]);
  const labels = [];
  for (const el of document.querySelectorAll("h1, h2, [role='heading'], label")) {
    if (labels.length >= ${MAX_LABELS}) break;
    if (!visible(el)) continue;
    const value = clampText(
      el.getAttribute("aria-label") || el.textContent,
      ${MAX_LABEL_CHARS}
    );
    if (value) labels.push(value);
  }
  const messages = [];
  for (const el of document.querySelectorAll("[role='alert'], [role='status']")) {
    if (messages.length >= ${MAX_MESSAGES}) break;
    if (!visible(el)) continue;
    const value = clampText(el.textContent, ${MAX_MESSAGE_CHARS});
    if (value) messages.push(value);
  }
  const host = location.hostname;
  const authHost =
    host === "chatgpt.com" ||
    host.endsWith(".chatgpt.com") ||
    host === "openai.com" ||
    host.endsWith(".openai.com");
  let step = "unknown";
  if (composer) step = "done";
  else if (!authHost) step = "sso";
  else if (passwordInput) step = "password";
  else if (otpInput) step = "otp";
  else if (emailInput) step = "email";
  else if (captcha) step = "captcha";
  return {
    step,
    labels,
    has_captcha: captcha !== null,
    captcha_rect: rectOf(captcha),
    messages,
    url_path: location.pathname,
  };
})()`;

const SUBMIT_STATE_EXPRESSION = `(() => {
  const visible = (el) => !!el && el.getClientRects().length > 0;
  const stateOf = (el) => {
    const rect = el.getBoundingClientRect();
    if (!(rect.width > 1) || !(rect.height > 1)) return null;
    return {
      x: rect.x,
      y: rect.y,
      width: rect.width,
      height: rect.height,
      disabled: el.disabled === true || el.getAttribute("aria-disabled") === "true",
    };
  };
  const direct = document.querySelector("button[type='submit']");
  if (direct && visible(direct)) {
    const directState = stateOf(direct);
    if (directState) return directState;
  }
  for (const button of document.querySelectorAll("button")) {
    if (!visible(button)) continue;
    const text = String(button.textContent || "").replace(/\\s+/g, " ").trim();
    if (/^(continue|next|log ?in|sign ?in|verify|submit)$/i.test(text)) {
      const buttonState = stateOf(button);
      if (buttonState) return buttonState;
    }
  }
  return null;
})()`;

const CAPTCHA_RECT_EXPRESSION = `(() => {
  const visible = (el) => !!el && el.getClientRects().length > 0;
  const selectors = [
    "iframe[src*='hcaptcha.com']",
    "iframe[src*='challenges.cloudflare.com']",
    "iframe[src*='recaptcha']",
    "iframe[title*='captcha' i]",
    "[data-sitekey]",
    "[class*='h-captcha']",
  ];
  for (const selector of selectors) {
    const el = document.querySelector(selector);
    if (!visible(el)) continue;
    const rect = el.getBoundingClientRect();
    if (rect.width > 1 && rect.height > 1) {
      return { x: rect.x, y: rect.y, width: rect.width, height: rect.height };
    }
  }
  return null;
})()`;

function boundedString(value, limit) {
  return typeof value === "string" ? value.slice(0, limit) : "";
}

export function normalizeLoginState(raw) {
  const state = raw && typeof raw === "object" ? raw : {};
  const step = LOGIN_STEPS.has(state.step) ? state.step : "unknown";
  const labels = Array.isArray(state.labels)
    ? state.labels
        .filter((value) => typeof value === "string")
        .slice(0, MAX_LABELS)
        .map((value) => value.slice(0, MAX_LABEL_CHARS))
    : [];
  const messages = Array.isArray(state.messages)
    ? state.messages
        .filter((value) => typeof value === "string")
        .slice(0, MAX_MESSAGES)
        .map((value) => value.slice(0, MAX_MESSAGE_CHARS))
    : [];
  const rect = state.captcha_rect;
  const captchaRect =
    rect &&
    typeof rect === "object" &&
    Number.isFinite(rect.x) &&
    Number.isFinite(rect.y) &&
    Number.isFinite(rect.w) &&
    Number.isFinite(rect.h) &&
    rect.w > 0 &&
    rect.h > 0
      ? {
          x: Math.round(rect.x),
          y: Math.round(rect.y),
          w: Math.round(rect.w),
          h: Math.round(rect.h),
        }
      : null;
  return {
    step,
    labels,
    has_captcha: state.has_captcha === true,
    captcha_rect: captchaRect,
    messages,
    url_path: boundedString(state.url_path, MAX_URL_PATH_CHARS),
  };
}

export class LaunchBrake {
  constructor(directory, { now = Date.now } = {}) {
    this.directory = directory;
    this.now = now;
    this.locked = false;
  }
  acquire() {
    const now = this.now();
    if (!Number.isFinite(now) || now < 0) throw new DriverError("E_BROWSER_UNAVAILABLE", "Launch time is unverifiable.");
    let fresh = false;
    try { mkdirSync(this.directory, { mode: 0o700 }); fresh = true; }
    catch (error) { if (error.code !== "EEXIST") throw new DriverError("E_BROWSER_UNAVAILABLE", "Launch state is unavailable."); }
    if (!lstatSync(this.directory).isDirectory() || lstatSync(this.directory).isSymbolicLink())
      throw new DriverError("E_BROWSER_UNAVAILABLE", "Launch state is unavailable.");
    try { mkdirSync(join(this.directory, "lock"), { mode: 0o700 }); this.locked = true; }
    catch { throw new DriverError("E_BROWSER_UNAVAILABLE", "A browser launch is locked."); }
    try {
      const metadata = join(this.directory, "last-start.json");
      if (!fresh) {
        const stat = lstatSync(metadata);
        if (!stat.isFile() || stat.size > 256) throw new Error();
        const previous = JSON.parse(readFileSync(metadata, "utf8"));
        if (!Number.isFinite(previous.started_ms) || previous.started_ms < 0 ||
            now < previous.started_ms || now - previous.started_ms < 300000) throw new Error();
      }
      const temporary = join(this.directory, "last-start.tmp");
      const fd = openSync(temporary, constants.O_WRONLY | constants.O_CREAT | constants.O_TRUNC | constants.O_NOFOLLOW, 0o600);
      try { writeFileSync(fd, JSON.stringify({ started_ms: now })); fsyncSync(fd); }
      finally { closeSync(fd); }
      renameSync(temporary, metadata);
      const directory = openSync(this.directory, "r");
      try { fsyncSync(directory); } finally { closeSync(directory); }
      const parent = openSync(dirname(this.directory), "r");
      try { fsyncSync(parent); } finally { closeSync(parent); }
    } catch {
      this.release();
      throw new DriverError("E_BROWSER_UNAVAILABLE", "Browser launch brake requires manual recovery or more time.");
    }
  }
  release() {
    if (this.locked) { rmdirSync(join(this.directory, "lock")); this.locked = false; }
  }
}

export function endpointParser() {
  let buffer = "", consumed = 0, endpoint = null, discard = false;
  return {
    feed(chunk) {
      if (endpoint || consumed >= 65536) return;
      const text = Buffer.from(chunk).subarray(0, 65536 - consumed).toString("utf8");
      consumed += Buffer.byteLength(text);
      for (const character of text) {
        if (character === "\n") {
          const match = !discard && buffer.match(/^DevTools listening on (ws:\/\/127\.0\.0\.1:(\d+)\/devtools\/browser\/[a-zA-Z0-9-]+)\r?$/);
          if (match && Number(match[2]) > 0 && Number(match[2]) <= 65535)
            endpoint = { wsUrl: match[1], port: Number(match[2]) };
          buffer = ""; discard = false;
        } else if (!discard && buffer.length < 4096) buffer += character;
        else { buffer = ""; discard = true; }
      }
    },
    get endpoint() { return endpoint; },
  };
}

export function readinessExpression(pack) {
  const selectors = {};
  for (const key of ["composer", "send", "stop_control", "login_wall"]) {
    selectors[key] = (pack?.locators?.[key]?.strategies || []).flatMap((s) =>
      s.kind === "css" ? [s.value] : s.kind === "testid" ? ['[data-testid=' + JSON.stringify(s.value) + ']']
        : s.kind === "role" ? ['[role=' + JSON.stringify(s.value) + ']'] : []);
  }
  return "/* capture_readiness */(" + ((locators) => {
    const visible = (node) => !!node && node.isConnected && node.getClientRects().length > 0;
    const any = (queries) => queries.some((query) => {
      try { return [...document.querySelectorAll(query)].slice(0, 64).some(visible); } catch { return false; }
    });
    if (location.origin !== "https://chatgpt.com") return { state: "needs_admin", reason: "E_NEEDS_ADMIN" };
    if (any(['iframe[src*="challenges.cloudflare.com"]', '[name="cf-turnstile-response"]', '[data-testid="challenge"]']))
      return { state: "needs_admin", reason: "E_CAPTCHA_REQUIRED" };
    if (any(locators.login_wall) || any(['input[type="password"]', 'input[autocomplete="one-time-code"]']))
      return { state: "needs_admin", reason: "E_LOGIN_REQUIRED" };
    const alerts = [...document.querySelectorAll('[role="alert"], [role="dialog"]')].slice(0, 8)
      .filter(visible).map((n) => String(n.textContent || "").slice(0, 512)).join(" ");
    if (/limit reached|usage limit|try again later/i.test(alerts))
      return { state: "needs_admin", reason: "E_LIMIT_REACHED" };
    if (/consent|accept.*(terms|cookies)|agree.*terms/i.test(alerts))
      return { state: "needs_admin", reason: "E_CONSENT_REQUIRED" };
    if (!any(locators.composer)) return { state: "needs_admin", reason: "E_COMPOSER_NOT_FOUND" };
    return { state: "ready", generating: any(locators.stop_control), send_present: any(locators.send) };
  }).toString() + ")(" + JSON.stringify(selectors) + ")";
}

export function parseChromiumMajorVersion(text) {
  const match = String(text || "").match(/(?:Chromium|Chrome)\s+(\d+)\./i);
  return match ? Number(match[1]) : null;
}

export function readChromiumMajorVersion(binaryPath, { timeoutMs = 5000 } = {}) {
  const result = spawnSync(binaryPath, ["--version"], {
    encoding: "utf8",
    timeout: timeoutMs,
  });
  const text = `${result.stdout || ""}\n${result.stderr || ""}`;
  const major = parseChromiumMajorVersion(text);
  if (major === null) {
    throw new DriverError(
      "E_DRIVER_VERSION",
      `cannot read the major version of ${basename(binaryPath)}`
    );
  }
  return major;
}

export function chromiumUserAgent(majorVersion) {
  // The normal (non-headless) Chromium UA for this binary's major version.
  const major = Number.parseInt(String(majorVersion), 10);
  if (!Number.isInteger(major) || major <= 0) {
    throw new DriverError(
      "E_DRIVER_VERSION",
      "cannot derive the Chromium major version for the stealth user agent"
    );
  }
  return (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 " +
    `(KHTML, like Gecko) Chrome/${major}.0.0.0 Safari/537.36`
  );
}

export function chromiumLaunchArgs({
  profileDir,
  headless = true,
  windowSize = "1280,720",
  remoteDebuggingPort = 0,
  stealth = false,
  majorVersion = null,
} = {}) {
  const args = [
    `--user-data-dir=${profileDir}`,
    `--remote-debugging-port=${remoteDebuggingPort}`,
    "--remote-debugging-address=127.0.0.1",
    "--no-first-run",
    "--no-default-browser-check",
    `--window-size=${windowSize}`,
  ];
  if (headless) args.push("--headless=new");
  if (stealth) throw new DriverError("E_BROWSER_UNAVAILABLE", "Stealth is not supported.");
  return args;
}

export class BaseCdpDriver {
  // Engine-neutral base: owns the shared CDP client and every wizard helper
  // plus the shared primitives (openPage, navigate with the bounded retry,
  // evaluate, screenshot). Subclasses provide start()/stop() and the
  // process/endpoint handling for their engine.
  constructor({ cdpTimeoutMs = DEFAULT_CDP_TIMEOUT_MS } = {}) {
    this.cdpTimeoutMs = cdpTimeoutMs;
    this.client = null;
    this.onLog = null;
  }

  get sessionId() {
    return this.client ? this.client.sessionId : null;
  }

  set sessionId(value) {
    if (!this.client) {
      throw new DriverError("E_DRIVER_STATE", "engine is not connected");
    }
    this.client.sessionId = value;
  }

  async navigate(url) {
    if (!this.client) throw new DriverError("E_DRIVER_STATE", "no page is open");
    const maxAttempts = 1 + this.navigateRetries;
    const budgetMs = this.cdpTimeoutMs * maxAttempts;
    const startedAt = Date.now();
    for (let attempt = 1; attempt <= maxAttempts; attempt += 1) {
      try {
        const outcome = await this._navigateOnce(url);
        return { ...outcome, attempts: attempt };
      } catch (error) {
        const isNavigateTimeout =
          error instanceof DriverError &&
          error.code === "E_DRIVER_TIMEOUT" &&
          String(error.message).includes("Page.navigate");
        const attemptsLeft = attempt < maxAttempts;
        const withinBudget = Date.now() - startedAt < budgetMs;
        if (!isNavigateTimeout || !attemptsLeft || !withinBudget) throw error;
        this.logLine(
          "E_DRIVER_NAVIGATE_RETRY",
          `Page.navigate timed out; retrying once (attempt ${attempt + 1}/${maxAttempts})`
        );
      }
    }
    throw new DriverError("E_DRIVER_STATE", "navigation retry loop exhausted");
  }

  async _navigateOnce(url) {
    const loadFired = this._once("Page.loadEventFired", this.loadTimeoutMs);
    const result = await this._cdp("Page.navigate", { url });
    if (result && result.errorText) {
      throw new DriverError(
        "E_DRIVER_NAVIGATE",
        `navigation to ${url} failed: ${result.errorText}`
      );
    }
    const fired = await loadFired;
    await delay(this.settleMs);
    return { loadFired: fired };
  }

  async evaluate(expression) {
    return await this._evaluate(expression, false);
  }

  async evaluateAsync(expression) {
    // Same evaluation seam with `awaitPromise` on (HE-5a canary); existing
    // callers keep the synchronous `evaluate` behavior unchanged.
    return await this._evaluate(expression, true);
  }

  async _evaluate(expression, awaitPromise) {
    if (!this.client) throw new DriverError("E_DRIVER_STATE", "no page is open");
    const result = await this._cdp("Runtime.evaluate", {
      expression,
      returnByValue: true,
      awaitPromise,
    });
    if (result && result.exceptionDetails) {
      const detail =
        (result.exceptionDetails.exception &&
          result.exceptionDetails.exception.description) ||
        "evaluation failed";
      throw new DriverError("E_DRIVER_EVAL", detail);
    }
    return result && result.result ? result.result.value : undefined;
  }

  async fingerprint() {
    // Diagnosis only (HE-3e): the page-side automation signals after the
    // first navigation. Never used for control flow.
    if (!this.client) throw new DriverError("E_DRIVER_STATE", "no page is open");
    const raw = await this.evaluate(
      "(() => ({ webdriver: navigator.webdriver === true, user_agent: String(navigator.userAgent || '') }))()"
    );
    return {
      webdriver: !!(raw && raw.webdriver === true),
      user_agent: boundedString(raw && raw.user_agent, MAX_FINGERPRINT_UA_CHARS),
    };
  }

  logLine(code, message) {
    if (typeof this.onLog === "function") {
      this.onLog(code, message);
      return;
    }
    try {
      console.error(`[${code}] ${message}`);
    } catch {
      // logging must never mask the primary result
    }
  }

  async clickXY(x, y) {
    if (!this.client) throw new DriverError("E_DRIVER_STATE", "no page is open");
    const base = { x, y, button: "left", clickCount: 1, modifiers: 0 };
    await this._cdp("Input.dispatchMouseEvent", {
      type: "mouseMoved",
      x,
      y,
      button: "none",
      modifiers: 0,
    });
    await this._cdp("Input.dispatchMouseEvent", {
      type: "mousePressed",
      ...base,
      buttons: 1,
    });
    await this._cdp("Input.dispatchMouseEvent", {
      type: "mouseReleased",
      ...base,
      buttons: 0,
    });
    return { x, y };
  }

  async loginState() {
    if (!this.client) throw new DriverError("E_DRIVER_STATE", "no page is open");
    const raw = await this.evaluate(LOGIN_STATE_EXPRESSION);
    return normalizeLoginState(raw);
  }

  async screenshotPng() {
    return await this.snapshotPng(null);
  }

  async snapshotPng(region = null) {
    if (!this.client) throw new DriverError("E_DRIVER_STATE", "no page is open");
    const params = { format: "png" };
    if (region) {
      const scroll = await this.evaluate(
        "(() => ({ x: window.scrollX, y: window.scrollY }))()"
      );
      params.clip = {
        x: region.x + Number(scroll && Number.isFinite(scroll.x) ? scroll.x : 0),
        y: region.y + Number(scroll && Number.isFinite(scroll.y) ? scroll.y : 0),
        width: region.width,
        height: region.height,
        scale: 1,
      };
    }
    const result = await this._cdp("Page.captureScreenshot", params);
    return Buffer.from(String(result.data || ""), "base64");
  }

  async fillField(field, value) {
    if (!this.client) throw new DriverError("E_DRIVER_STATE", "no page is open");
    const selectors = field === "focused" ? null : LOGIN_FIELDS[field];
    if (field !== "focused" && selectors === undefined) {
      throw new DriverError("E_DRIVER_FIELD", "unknown fill field");
    }
    if (selectors) {
      const document = await this._cdp("DOM.getDocument", {
        depth: -1,
        pierce: false,
      });
      const rootId = document && document.root ? document.root.nodeId : 0;
      let nodeId = 0;
      for (const selector of selectors) {
        const found = await this._cdp("DOM.querySelector", {
          nodeId: rootId,
          selector,
        });
        if (found && found.nodeId) {
          nodeId = found.nodeId;
          break;
        }
      }
      if (!nodeId) {
        throw new DriverError("E_DRIVER_FIELD", "the page does not expose that field");
      }
      await this._cdp("DOM.focus", { nodeId });
    }
    const focused = await this.evaluate(
      "(() => { const el = document.activeElement; return !!(el && (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA' || el.isContentEditable)); })()"
    );
    if (!focused) {
      throw new DriverError("E_DRIVER_FIELD", "the page has no focused editable field");
    }
    await this.evaluate(
      "(() => { const el = document.activeElement; if (el && typeof el.select === 'function') el.select(); return true; })()"
    );
    await this._cdp("Input.insertText", { text: value });
    if (await this._fillVerified(field, value)) {
      return { field, filled: true };
    }
    try {
      await this._nativeSetValue(value);
    } catch {
      // a rejected native-setter stage falls through to per-character typing
    }
    if (await this._fillVerified(field, value)) {
      return { field, filled: true };
    }
    try {
      await this._typeCharacters(value);
    } catch {
      // a rejected typing stage reaches the final verification below
    }
    if (await this._fillVerified(field, value)) {
      return { field, filled: true };
    }
    throw new DriverError(
      "E_LOGIN_FILL_FAILED",
      `the ${field} field could not be filled and verified`
    );
  }

  async _fillVerified(field, value) {
    const selectors = field === "focused" ? null : LOGIN_FIELDS[field];
    const locate = selectors
      ? `(() => {
  for (const selector of ${JSON.stringify(selectors)}) {
    const candidate = document.querySelector(selector);
    if (candidate && typeof candidate.value === "string") return candidate;
  }
  return null;
})()`
      : "document.activeElement";
    const valueOk = await this.evaluate(
      `(() => {
  const el = ${locate};
  return !!(el && typeof el.value === "string" && el.value === ${JSON.stringify(value)});
})()`
    );
    if (valueOk !== true) return false;
    if (field === "focused") return true;
    const submit = await this.evaluate(SUBMIT_STATE_EXPRESSION);
    if (submit && submit.disabled === true) return false;
    return true;
  }

  async _nativeSetValue(value) {
    const expression = `(() => {
  const el = document.activeElement;
  if (!el || !(el.tagName === "INPUT" || el.tagName === "TEXTAREA")) return false;
  const proto = el.tagName === "TEXTAREA" ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype;
  const descriptor = Object.getOwnPropertyDescriptor(proto, "value");
  if (!descriptor || typeof descriptor.set !== "function") return false;
  descriptor.set.call(el, ${JSON.stringify(value)});
  el.dispatchEvent(new Event("input", { bubbles: true }));
  el.dispatchEvent(new Event("change", { bubbles: true }));
  return true;
})()`;
    const ok = await this.evaluate(expression);
    if (ok !== true) {
      throw new DriverError("E_DRIVER_FIELD", "the page rejected the native-setter fill");
    }
    return { field: "focused", filled: true };
  }

  async _typeCharacters(value) {
    for (const character of String(value)) {
      await this._cdp("Input.dispatchKeyEvent", {
        type: "keyDown",
        key: character,
      });
      await this._cdp("Input.dispatchKeyEvent", {
        type: "char",
        key: character,
        text: character,
        unmodifiedText: character,
      });
      await this._cdp("Input.dispatchKeyEvent", {
        type: "keyUp",
        key: character,
      });
    }
    return { field: "focused", typed: true };
  }

  async clickTarget(target) {
    if (!this.client) throw new DriverError("E_DRIVER_STATE", "no page is open");
    if (target !== "submit" && target !== "captcha") {
      throw new DriverError("E_DRIVER_TARGET", "unknown click target");
    }
    const state = await this.evaluate(
      target === "captcha" ? CAPTCHA_RECT_EXPRESSION : SUBMIT_STATE_EXPRESSION
    );
    if (
      !state ||
      !Number.isFinite(state.x) ||
      !Number.isFinite(state.y) ||
      !Number.isFinite(state.width) ||
      !Number.isFinite(state.height)
    ) {
      throw new DriverError("E_LOGIN_CLICK_FAILED", `the ${target} control is missing`);
    }
    if (target === "submit" && state.disabled === true) {
      throw new DriverError("E_LOGIN_CLICK_FAILED", "the submit control is disabled");
    }
    const before = target === "submit" ? await this.loginState() : null;
    const x = Math.round(state.x + state.width / 2);
    const y = Math.round(state.y + state.height / 2);
    await this.clickXY(x, y);
    if (target === "submit") {
      const outcome = await this._waitForLoginChange(before);
      if (!outcome.changed) {
        throw new DriverError(
          "E_LOGIN_NO_PROGRESS",
          `no progress after clicking submit (the step stayed "${outcome.step}")`
        );
      }
    }
    return { target, x, y };
  }

  async _waitForLoginChange(reference) {
    const startedAt = Date.now();
    let current = reference;
    while (Date.now() - startedAt <= this.noProgressTimeoutMs) {
      await delay(this.noProgressPollMs);
      try {
        current = await this.loginState();
      } catch (error) {
        if (error instanceof DriverError) {
          return { changed: true, step: reference.step };
        }
        throw error;
      }
      if (current.step !== reference.step) {
        return { changed: true, step: current.step };
      }
      if (
        JSON.stringify(current.messages) !== JSON.stringify(reference.messages)
      ) {
        return { changed: true, step: current.step };
      }
    }
    return { changed: false, step: current.step };
  }

  on(method, handler) {
    return this.client.on(method, handler);
  }

  onSession(sessionId, method, handler) {
    if (!this.client) throw new DriverError("E_DRIVER_STATE", "engine is not connected");
    return this.client.onSession(sessionId, method, handler);
  }

  send(method, params = {}) {
    if (!this.client) throw new DriverError("E_DRIVER_STATE", "engine is not connected");
    return this._cdp(method, params);
  }

  sendTo(sessionId, method, params = {}) {
    if (!this.client) throw new DriverError("E_DRIVER_STATE", "engine is not connected");
    return this.client.sendTo(sessionId, method, params);
  }

  async evaluateIn(sessionId, expression, options = {}) {
    if (!this.client) throw new DriverError("E_DRIVER_STATE", "no page is open");
    const { awaitPromise = false, userGesture = false } = options;
    const result = await this.client.sendTo(sessionId, "Runtime.evaluate", {
      expression,
      returnByValue: true,
      awaitPromise,
      userGesture,
    });
    if (result && result.exceptionDetails) {
      const detail =
        (result.exceptionDetails.exception &&
          result.exceptionDetails.exception.description) ||
        "evaluation failed";
      throw new DriverError("E_DRIVER_EVAL", detail);
    }
    return result && result.result ? result.result.value : undefined;
  }

  async closePage() {
    if (!this.client) return;
    try {
      await this._cdp("Page.close");
    } catch (error) {
      // closing an already-closed page is not an error
    }
  }

  _cdp(method, params = {}) {
    return this.client.send(method, params);
  }

  _once(method, timeoutMs) {
    return this.client.once(method, timeoutMs);
  }

  async _openPage(url) {
    if (!this.client) {
      if (!this.browserWsUrl) {
        throw new DriverError("E_DRIVER_STATE", "engine is not started");
      }
      this.client = new CdpClient({
        wsUrl: this.browserWsUrl,
        cdpTimeoutMs: this.cdpTimeoutMs,
      });
    }
    await this.client.connect();
    const created = await this.client.sendBrowser("Target.createTarget", { url });
    const attached = await this.client.sendBrowser(
      "Target.attachToTarget",
      { targetId: created.targetId, flatten: true }
    );
    this.client.sessionId = attached.sessionId;
    this.targetId = created.targetId;
    await this._cdp("Page.enable");
    await this._cdp("Runtime.enable");
  }

  async openPage() {
    await this._openPage("about:blank");
  }
}

export class ChromiumDriver extends BaseCdpDriver {
  constructor({
    chromePath = null,
    launchBrake = null,
    spawnProcess = spawn,
    profileDir,
    headed = false,
    stealth = false,
    startTimeoutMs = DEFAULT_START_TIMEOUT_MS,
    stopGraceMs = DEFAULT_STOP_GRACE_MS,
    cdpTimeoutMs = DEFAULT_CDP_TIMEOUT_MS,
    loadTimeoutMs = DEFAULT_LOAD_TIMEOUT_MS,
    settleMs = DEFAULT_SETTLE_MS,
    navigateRetries = 1,
    noProgressTimeoutMs = DEFAULT_NO_PROGRESS_TIMEOUT_MS,
    noProgressPollMs = DEFAULT_NO_PROGRESS_POLL_MS,
  } = {}) {
    super({ cdpTimeoutMs });
    this.chromePath = chromePath;
    this.spawnProcess = spawnProcess;
    this.launchBrake = launchBrake;
    this.startedOnce = false;
    this.profileDir = profileDir;
    this.headed = Boolean(headed);
    this.stealth = Boolean(stealth);
    this.majorVersion = null;
    this.startTimeoutMs = startTimeoutMs;
    this.stopGraceMs = stopGraceMs;
    this.loadTimeoutMs = loadTimeoutMs;
    this.settleMs = settleMs;
    this.navigateRetries = navigateRetries;
    this.noProgressTimeoutMs = noProgressTimeoutMs;
    this.noProgressPollMs = noProgressPollMs;
    this.child = null;
    this.spawnError = null;
    this.port = null;
    this.browserWsUrl = null;
    this.targetId = null;
    this.version = null;
  }

  static defaultBinary() {
    return null; // Explicit executable configuration is mandatory.
  }

  get listener() {
    return this.port ? `127.0.0.1:${this.port}` : null;
  }

  async start() {
    if (this.startedOnce) throw new DriverError("E_BROWSER_UNAVAILABLE", "Automatic browser restart is forbidden.");
    if (!this.chromePath || !isAbsolute(this.chromePath) || this.stealth) {
      throw new DriverError("E_BROWSER_UNAVAILABLE", "An explicit Chromium executable without stealth is required.");
    }
    try {
      await access(this.chromePath, constants.X_OK);
      if (!statSync(this.chromePath).isFile()) throw new Error();
      await access(this.profileDir);
      // Canonicalize the directory itself, never enumerate or read its contents.
      // Login and capture must share the same brake even through path aliases.
      const ownedProfile = realpathSync(this.profileDir);
      this.launchBrake ||= new LaunchBrake(ownedProfile + ".capture-launch");
    } catch {
      throw new DriverError("E_BROWSER_UNAVAILABLE", "Browser preflight failed.");
    }
    this.launchBrake.acquire();
    this.startedOnce = true;
    this.endpointReader = endpointParser();
    try {
      this.child = this.spawnProcess(this.chromePath, chromiumLaunchArgs({
        profileDir: this.profileDir, headless: !this.headed,
      }), { stdio: ["ignore", "ignore", "pipe"] });
      this.child.stderr.on("data", (chunk) => this.endpointReader.feed(chunk));
      this.child.on("error", () => { this.spawnError = true; });
      const endpoint = await this._awaitEndpoint();
      this.port = endpoint.port;
      this.browserWsUrl = endpoint.wsUrl;
      this.client = new CdpClient({ wsUrl: this.browserWsUrl, cdpTimeoutMs: this.cdpTimeoutMs });
      await this.client.connect();
    } catch {
      await this.stop();
      throw new DriverError("E_BROWSER_UNAVAILABLE", "Browser startup failed.");
    }
  }

  async readiness(pack, { observing = false } = {}) {
    if (!this.child || this.child.exitCode !== null || this.child.signalCode !== null || !this.client || !this.targetId) {
      return { state: "browser_unavailable", reason: "E_BROWSER_UNAVAILABLE" };
    }
    try {
      const result = await this.evaluate(readinessExpression(pack));
      if (result.state === "ready" && result.generating && !observing)
        return { state: "needs_admin", reason: "E_AMBIGUOUS_SEND" };
      if (result.state === "ready" && !result.generating && !result.send_present)
        return { state: "needs_admin", reason: "E_COMPOSER_NOT_FOUND" };
      return result;
    } catch {
      return { state: "browser_unavailable", reason: "E_BROWSER_UNAVAILABLE" };
    }
  }

  async _awaitEndpoint() {
    const deadline = Date.now() + this.startTimeoutMs;
    while (Date.now() < deadline) {
      if (this.spawnError || this.child.exitCode !== null || this.child.signalCode !== null)
        throw new DriverError("E_BROWSER_UNAVAILABLE", "Browser did not start.");
      if (this.endpointReader.endpoint) return this.endpointReader.endpoint;
      await delay(50);
    }
    throw new DriverError("E_BROWSER_UNAVAILABLE", "Browser endpoint unavailable.");
  }

  async _version(port) {
    const response = await fetch(loopbackUrl(port) + "/json/version", {
      signal: AbortSignal.timeout(1500),
    });
    if (!response.ok) {
      throw new DriverError(
        "E_DRIVER_START",
        `chrome /json/version answered ${response.status}`
      );
    }
    return await response.json();
  }

  async stop() {
    if (this.client) {
      await this.client.close();
      this.client = null;
    }
    const child = this.child;
    this.port = null;
    if (!child) { this.launchBrake?.release(); return; }
    if (child.exitCode === null && child.signalCode === null) {
      child.kill("SIGTERM");
      const deadline = Date.now() + this.stopGraceMs;
      while (
        Date.now() < deadline &&
        child.exitCode === null &&
        child.signalCode === null
      ) {
        await delay(100);
      }
      if (child.exitCode === null && child.signalCode === null) {
        child.kill("SIGKILL");
        await delay(300);
      }
    }
    if (child.exitCode === null && child.signalCode === null)
      throw new DriverError("E_BROWSER_UNAVAILABLE", "Browser termination is unconfirmed; launch remains locked.");
    this.child = null;
    this.launchBrake?.release();
  }
}
