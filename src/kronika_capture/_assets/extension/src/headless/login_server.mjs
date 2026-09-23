// Loopback login wizard server (HE-2d).
//
// Serves the DOM-mirror login wizard and bridges it to the engine over the
// loopback CDP connection. Node built-ins only.
//
// Boundaries: binds 127.0.0.1 only; a fresh 32-byte URL-safe path secret per
// session with a constant-time compare and a plain 404 on mismatch; strict Host
// and Sec-Fetch-Site/Sec-Fetch-Dest checks; no CORS; the frozen security
// headers with an exact CSP on every response. `/state` reads only structural
// login state; `/snapshot` returns single bounded PNGs and never persists them;
// `/action` values transit in memory only, are forwarded to the engine's CDP,
// and are never logged, stored, or echoed. A verifiable interaction failure
// (fill, click, or no step progress) returns HTTP 409
// `{ok:false, error:{code, message}}` with the typed engine code and a value-free
// message so the wizard can show it and fall back to the page view. There is no
// continuous stream and no keystroke or frame logging.

import { createHash, randomBytes, timingSafeEqual } from "node:crypto";
import { readFileSync } from "node:fs";
import { createServer } from "node:http";

export const BIND_ADDRESS = "127.0.0.1";
export const SECRET_BYTES = 32;
export const MAX_BODY_BYTES = 64 * 1024;
export const HARD_DRAIN_BYTES = 4 * 1024 * 1024;
export const MAX_VALUE_CHARS = 256;
export const MAX_COORDINATE = 100000;
export const MAX_SNAPSHOT_DIMENSION = 4096;
export const MAX_SNAPSHOT_PIXELS = 4_000_000;

export const CSP =
  "default-src 'none'; script-src 'self'; style-src 'self'; " +
  "img-src 'self'; connect-src 'self'; base-uri 'none'; form-action 'none'; " +
  "frame-ancestors 'none'";

export class LoginServerError extends Error {
  constructor(code, message) {
    super(message);
    this.name = "LoginServerError";
    this.code = code;
  }
}

const BASE_HEADERS = {
  "Content-Security-Policy": CSP,
  "X-Content-Type-Options": "nosniff",
  "Referrer-Policy": "no-referrer",
  "Cache-Control": "no-store",
};

const STATIC_ROUTES = {
  "/": { file: "index.html", type: "text/html; charset=utf-8" },
  "/app.js": { file: "app.js", type: "text/javascript; charset=utf-8" },
  "/app.css": { file: "app.css", type: "text/css; charset=utf-8" },
};

const ROUTES = {
  "/": { method: "GET", dest: ["document"] },
  "/app.js": { method: "GET", dest: ["script"] },
  "/app.css": { method: "GET", dest: ["style"] },
  "/state": { method: "GET", dest: ["empty"] },
  "/snapshot": { method: "GET", dest: ["image"] },
  "/action": { method: "POST", dest: ["empty"] },
  "/done": { method: "POST", dest: ["empty"] },
};

const FILL_FIELDS = new Set(["email", "password", "otp", "focused"]);
const CLICK_TARGETS = new Set(["submit", "captcha"]);
const SNAPSHOT_PARAMS = ["x", "y", "w", "h"];
const CONTROL_ERRORS = new Set([
  "E_DRIVER_FIELD",
  "E_DRIVER_TARGET",
  "E_LOGIN_FILL_FAILED",
  "E_LOGIN_CLICK_FAILED",
  "E_LOGIN_NO_PROGRESS",
]);

function secretMatches(candidate, secret) {
  if (typeof candidate !== "string" || typeof secret !== "string") return false;
  const presented = createHash("sha256").update(candidate).digest();
  const expected = createHash("sha256").update(secret).digest();
  return timingSafeEqual(presented, expected);
}

function isFiniteNumber(value) {
  return typeof value === "number" && Number.isFinite(value);
}

function hasExactKeys(payload, names) {
  const keys = Object.keys(payload).sort();
  const expected = [...names].sort();
  if (keys.length !== expected.length) return false;
  return keys.every((key, index) => key === expected[index]);
}

export function validateAction(payload) {
  if (payload === null || typeof payload !== "object" || Array.isArray(payload)) {
    throw new LoginServerError("E_LOGIN_SERVER_INPUT", "action must be a JSON object");
  }
  const type = payload.type;
  if (type === "fill") {
    if (!hasExactKeys(payload, ["type", "field", "value"])) {
      throw new LoginServerError("E_LOGIN_SERVER_INPUT", "fill takes exactly type, field, value");
    }
    if (typeof payload.field !== "string" || !FILL_FIELDS.has(payload.field)) {
      throw new LoginServerError("E_LOGIN_SERVER_INPUT", "unknown fill field");
    }
    if (typeof payload.value !== "string" || payload.value.length === 0) {
      throw new LoginServerError("E_LOGIN_SERVER_INPUT", "fill value must be a non-empty string");
    }
    if (payload.value.length > MAX_VALUE_CHARS) {
      throw new LoginServerError("E_LOGIN_SERVER_INPUT", "fill value is too long");
    }
    return { type, field: payload.field, value: payload.value };
  }
  if (type === "click") {
    if (!hasExactKeys(payload, ["type", "target"])) {
      throw new LoginServerError("E_LOGIN_SERVER_INPUT", "click takes exactly type, target");
    }
    if (typeof payload.target !== "string" || !CLICK_TARGETS.has(payload.target)) {
      throw new LoginServerError("E_LOGIN_SERVER_INPUT", "unknown click target");
    }
    return { type, target: payload.target };
  }
  if (type === "click-xy") {
    if (!hasExactKeys(payload, ["type", "x", "y"])) {
      throw new LoginServerError("E_LOGIN_SERVER_INPUT", "click-xy takes exactly type, x, y");
    }
    if (!isFiniteNumber(payload.x) || !isFiniteNumber(payload.y)) {
      throw new LoginServerError("E_LOGIN_SERVER_INPUT", "click-xy coordinates must be numbers");
    }
    if (
      payload.x < 0 ||
      payload.y < 0 ||
      payload.x > MAX_COORDINATE ||
      payload.y > MAX_COORDINATE
    ) {
      throw new LoginServerError("E_LOGIN_SERVER_INPUT", "click-xy coordinates out of bounds");
    }
    return { type, x: payload.x, y: payload.y };
  }
  throw new LoginServerError("E_LOGIN_SERVER_INPUT", "unknown action type");
}

export function parseSnapshotRegion(url) {
  const params = new URL(url, `http://${BIND_ADDRESS}`).searchParams;
  const present = SNAPSHOT_PARAMS.filter((name) => params.has(name));
  if (present.length === 0) return null;
  if (present.length !== SNAPSHOT_PARAMS.length) {
    throw new LoginServerError(
      "E_LOGIN_SERVER_SNAPSHOT",
      "a snapshot region requires x, y, w, and h"
    );
  }
  const x = Number(params.get("x"));
  const y = Number(params.get("y"));
  const w = Number(params.get("w"));
  const h = Number(params.get("h"));
  if (![x, y, w, h].every(Number.isFinite)) {
    throw new LoginServerError("E_LOGIN_SERVER_SNAPSHOT", "snapshot numbers are invalid");
  }
  if (Math.abs(x) > MAX_COORDINATE || Math.abs(y) > MAX_COORDINATE) {
    throw new LoginServerError("E_LOGIN_SERVER_SNAPSHOT", "snapshot origin out of bounds");
  }
  if (!(w > 0) || !(h > 0) || w > MAX_SNAPSHOT_DIMENSION || h > MAX_SNAPSHOT_DIMENSION) {
    throw new LoginServerError("E_LOGIN_SERVER_SNAPSHOT", "snapshot size out of bounds");
  }
  if (w * h > MAX_SNAPSHOT_PIXELS) {
    throw new LoginServerError("E_LOGIN_SERVER_SNAPSHOT", "snapshot area out of bounds");
  }
  return { x, y, width: w, height: h };
}

export class LoginServer {
  constructor({
    engine,
    port = 0,
    secret = null,
    appDir = null,
    maxBodyBytes = MAX_BODY_BYTES,
  } = {}) {
    if (
      !engine ||
      typeof engine.loginState !== "function" ||
      typeof engine.fill !== "function" ||
      typeof engine.clickTarget !== "function" ||
      typeof engine.clickXY !== "function" ||
      typeof engine.snapshot !== "function"
    ) {
      throw new LoginServerError("E_LOGIN_SERVER_STATE", "a login engine is required");
    }
    this.engine = engine;
    this.requestedPort = port;
    this.secret =
      secret === null ? randomBytes(SECRET_BYTES).toString("base64url") : String(secret);
    this.appDir = appDir || new URL("./login_app/", import.meta.url);
    this.maxBodyBytes = maxBodyBytes;
    this.port = null;
    this.url = null;
    this.server = null;
    this.assets = new Map();
    this.inputChain = Promise.resolve();
    this.exitReason = null;
    this.fatalError = null;
    this.closed = false;
    this.waitPromise = new Promise((resolve, reject) => {
      this.resolveWait = resolve;
      this.rejectWait = reject;
    });
  }

  async start() {
    if (this.server) return { port: this.port, url: this.url };
    const server = createServer((request, response) => {
      this.handleRequest(request, response).catch(() => {
        this.sendJson(response, 500, { ok: false });
      });
    });
    server.on("clientError", (error, socket) => {
      try {
        socket.end("HTTP/1.1 400 Bad Request\r\nConnection: close\r\n\r\n");
      } catch {
        // a socket that is already gone needs no reply
      }
    });
    this.server = server;
    await new Promise((resolve, reject) => {
      const onError = (error) => {
        server.removeListener("listening", onListening);
        reject(new LoginServerError("E_LOGIN_SERVER_START", String(error.message || error)));
      };
      const onListening = () => {
        server.removeListener("error", onError);
        resolve();
      };
      server.once("error", onError);
      server.once("listening", onListening);
      server.listen(this.requestedPort, BIND_ADDRESS);
    });
    this.port = server.address().port;
    this.url = `http://${BIND_ADDRESS}:${this.port}/s/${this.secret}/`;
    return { port: this.port, url: this.url };
  }

  waitForDone() {
    return this.waitPromise;
  }

  requestClose(reason) {
    if (this.exitReason !== null) return;
    this.exitReason = String(reason || "closed");
    this.resolveWait({ reason: this.exitReason });
  }

  fail(error) {
    if (this.fatalError) return;
    this.fatalError =
      error instanceof LoginServerError
        ? error
        : new LoginServerError(
            "E_LOGIN_SERVER_ENGINE",
            String(error && error.message ? error.message : error)
          );
    this.requestClose("error");
  }

  async close(reason = "closed") {
    if (this.closed) return;
    this.closed = true;
    this.requestClose(reason);
    const server = this.server;
    this.server = null;
    if (server) {
      const closed = new Promise((resolve) => server.close(() => resolve()));
      if (typeof server.closeIdleConnections === "function") {
        server.closeIdleConnections();
      }
      await closed;
    }
  }

  sendJson(response, status, payload, extra = {}) {
    if (response.writableEnded || response.headersSent) return;
    const body = Buffer.from(JSON.stringify(payload));
    response.writeHead(status, {
      ...BASE_HEADERS,
      "Content-Type": "application/json; charset=utf-8",
      "Content-Length": String(body.length),
      ...extra,
    });
    response.end(body);
  }

  async handleRequest(request, response) {
    const host = request.headers.host;
    if (
      typeof host !== "string" ||
      host.toLowerCase() !== `${BIND_ADDRESS}:${this.port}`
    ) {
      this.sendJson(response, 403, { ok: false });
      return;
    }
    const rawUrl = typeof request.url === "string" ? request.url : "";
    const path = rawUrl.split("?", 1)[0].split("#", 1)[0];
    const prefix = "/s/";
    if (!path.startsWith(prefix)) {
      this.sendJson(response, 404, { ok: false });
      return;
    }
    const rest = path.slice(prefix.length);
    const slash = rest.indexOf("/");
    if (slash === -1) {
      this.sendJson(response, 404, { ok: false });
      return;
    }
    const candidate = rest.slice(0, slash);
    if (!secretMatches(candidate, this.secret)) {
      this.sendJson(response, 404, { ok: false });
      return;
    }
    const routePath = rest.slice(slash);
    const route = ROUTES[routePath];
    if (!route) {
      this.sendJson(response, 404, { ok: false });
      return;
    }
    if (request.method !== route.method) {
      this.sendJson(response, 405, { ok: false }, { Allow: route.method });
      return;
    }
    const site = request.headers["sec-fetch-site"];
    if (site !== undefined && site !== "none" && site !== "same-origin") {
      this.sendJson(response, 403, { ok: false });
      return;
    }
    const dest = request.headers["sec-fetch-dest"];
    if (dest !== undefined && !route.dest.includes(dest)) {
      this.sendJson(response, 403, { ok: false });
      return;
    }
    try {
      if (STATIC_ROUTES[routePath]) {
        this.serveStatic(response, routePath);
        return;
      }
      if (routePath === "/state") {
        try {
          await this.handleState(response);
        } catch {
          this.sendJson(response, 502, {
            ok: false,
            error: { code: "E_LOGIN_SERVER_ENGINE" },
          });
        }
        return;
      }
      if (routePath === "/snapshot") {
        try {
          await this.handleSnapshot(response, rawUrl);
        } catch (error) {
          if (
            error instanceof LoginServerError &&
            error.code === "E_LOGIN_SERVER_SNAPSHOT"
          ) {
            this.sendJson(response, 400, { ok: false, error: { code: error.code } });
            return;
          }
          this.sendJson(response, 502, {
            ok: false,
            error: { code: "E_LOGIN_SERVER_ENGINE" },
          });
        }
        return;
      }
      if (routePath === "/action") {
        await this.handleAction(request, response);
        return;
      }
      this.handleDone(response);
    } catch (error) {
      if (error instanceof LoginServerError && error.code === "E_LOGIN_SERVER_INPUT") {
        this.sendJson(response, 400, { ok: false, error: { code: error.code } });
        return;
      }
      this.sendJson(response, 500, { ok: false });
    }
  }

  serveStatic(response, routePath) {
    let body = this.assets.get(routePath);
    if (body === undefined) {
      const route = STATIC_ROUTES[routePath];
      try {
        body = readFileSync(new URL(route.file, this.appDir));
      } catch {
        this.sendJson(response, 500, { ok: false });
        return;
      }
      this.assets.set(routePath, body);
    }
    response.writeHead(200, {
      ...BASE_HEADERS,
      "Content-Type": STATIC_ROUTES[routePath].type,
      "Content-Length": String(body.length),
    });
    response.end(body);
  }

  async handleState(response) {
    const state = await this.engine.loginState();
    if (state === null || typeof state !== "object") {
      throw new LoginServerError("E_LOGIN_SERVER_ENGINE", "engine returned no state");
    }
    this.sendJson(response, 200, state);
  }

  async handleSnapshot(response, rawUrl) {
    const region = parseSnapshotRegion(rawUrl);
    const png = await this.engine.snapshot(region);
    if (!Buffer.isBuffer(png) || png.length === 0) {
      throw new LoginServerError("E_LOGIN_SERVER_ENGINE", "engine returned no snapshot");
    }
    response.writeHead(200, {
      ...BASE_HEADERS,
      "Content-Type": "image/png",
      "Content-Length": String(png.length),
    });
    response.end(png);
  }

  readBody(request) {
    return new Promise((resolve, reject) => {
      const chunks = [];
      let size = 0;
      let overflow = false;
      let settled = false;
      const rejectOnce = (code, message) => {
        if (settled) return;
        settled = true;
        reject(new LoginServerError(code, message));
      };
      request.on("data", (chunk) => {
        if (settled) return;
        if (overflow) {
          size += chunk.length;
          if (size > this.maxBodyBytes + HARD_DRAIN_BYTES) {
            rejectOnce("E_LOGIN_SERVER_BODY", "request body rejected");
            request.destroy();
          }
          return;
        }
        size += chunk.length;
        if (size > this.maxBodyBytes) {
          overflow = true;
          chunks.length = 0;
          return;
        }
        chunks.push(chunk);
      });
      request.on("end", () => {
        if (settled) return;
        if (overflow) {
          rejectOnce("E_LOGIN_SERVER_BODY", "request body too large");
          return;
        }
        settled = true;
        resolve(Buffer.concat(chunks));
      });
      request.on("error", () =>
        rejectOnce("E_LOGIN_SERVER_BODY", "request body error")
      );
    });
  }

  async handleAction(request, response) {
    const contentType = String(request.headers["content-type"] || "").toLowerCase();
    if (!contentType.startsWith("application/json")) {
      this.sendJson(response, 400, { ok: false });
      return;
    }
    let body = null;
    try {
      body = await this.readBody(request);
    } catch (error) {
      this.sendJson(response, 400, { ok: false, error: { code: error.code } });
      return;
    }
    let payload = null;
    try {
      payload = JSON.parse(body.toString("utf8"));
    } catch {
      this.sendJson(response, 400, { ok: false });
      return;
    }
    let command = null;
    try {
      command = validateAction(payload);
    } catch (error) {
      this.sendJson(response, 400, { ok: false, error: { code: error.code } });
      return;
    }
    try {
      await this.dispatch(command);
    } catch (error) {
      const code = String(error && error.code ? error.code : "");
      if (CONTROL_ERRORS.has(code)) {
        const message = String(
          error && error.message ? error.message : "the action failed"
        );
        this.sendJson(response, 409, { ok: false, error: { code, message } });
        return;
      }
      this.fail(error);
      this.sendJson(response, 502, { ok: false, error: { code: "E_LOGIN_SERVER_ENGINE" } });
      return;
    }
    this.sendJson(response, 200, { ok: true });
  }

  dispatch(command) {
    const run = this.inputChain.then(() => {
      if (command.type === "fill") return this.engine.fill(command.field, command.value);
      if (command.type === "click") return this.engine.clickTarget(command.target);
      return this.engine.clickXY(command.x, command.y);
    });
    this.inputChain = run.catch(() => {});
    return run;
  }

  handleDone(response) {
    this.sendJson(response, 200, { ok: true });
    setImmediate(() => this.requestClose("done"));
  }
}
