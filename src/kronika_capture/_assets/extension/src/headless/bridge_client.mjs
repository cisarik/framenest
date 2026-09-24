// Node ESM port of extension/src/bridge_client.js for the headless runner.
//
// Same envelopes, same error classes, and the same long-poll semantics as the
// extension client: a 204 answer means "no job offer" and is not an error. The
// headless additions are a configured port/token file lookup and an explicit
// client-kind query parameter on the long poll, because the bridge arbitrates
// offers by executor kind.

import { readFileSync } from "node:fs";
import { homedir } from "node:os";
import { join } from "node:path";

export const DEFAULT_BRIDGE_PORT = 8765;
export const DEFAULT_CLIENT_KIND = "headless";

export class BridgeHttpError extends Error {
  constructor(code, step, message, status) {
    super(message);
    this.name = "BridgeHttpError";
    this.code = code;
    this.step = step;
    this.status = status;
  }
}

export class BridgeUnreachableError extends Error {
  constructor(message) {
    super(message);
    this.name = "BridgeUnreachableError";
  }
}

export function resolveStateDir(env = process.env) {
  const xdg = env.XDG_STATE_HOME;
  const base =
    xdg && String(xdg).trim() ? String(xdg) : join(homedir(), ".local", "state");
  return join(base, "framenest-chatgpt-page");
}

export function readToken(stateDir) {
  try {
    const token = readFileSync(join(stateDir, "token"), "utf8").trim();
    return token || null;
  } catch {
    return null;
  }
}

export function readConfiguredPort(stateDir) {
  try {
    const payload = JSON.parse(readFileSync(join(stateDir, "config.json"), "utf8"));
    const port = payload.port;
    if (Number.isInteger(port) && port >= 1 && port <= 65535) return port;
  } catch {
    // fall through to the default port
  }
  return null;
}

export class BridgeClient {
  constructor({ url, token, timeoutMs = 30000 }) {
    this.url = String(url || "").replace(/\/+$/, "");
    this.token = String(token || "");
    this.timeoutMs = timeoutMs;
    this.runnerId = null;
    this.epoch = null;
  }

  async requestWithStatus(
    method,
    path,
    body = null,
    timeoutMs = this.timeoutMs,
    signal = null
  ) {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), timeoutMs);
    if (signal) {
      if (signal.aborted) controller.abort();
      else signal.addEventListener("abort", () => controller.abort(), { once: true });
    }
    try {
      const headers = { Accept: "application/json" };
      if (body !== null) headers["Content-Type"] = "application/json";
      if (this.token) headers["X-Bridge-Token"] = this.token;
      const response = await fetch(this.url + path, {
        method,
        headers,
        body: body === null ? undefined : JSON.stringify(body),
        signal: controller.signal,
      });
      const text = await response.text();
      let payload = null;
      if (text) {
        try {
          payload = JSON.parse(text);
        } catch {
          payload = null;
        }
      }
      if (!response.ok) {
        const error = payload && payload.error ? payload.error : {};
        throw new BridgeHttpError(
          String(error.code || "E_INTERNAL"),
          String(error.step || "bridge"),
          String(error.message || "HTTP " + response.status),
          response.status
        );
      }
      return { status: response.status, payload: payload || {} };
    } catch (error) {
      if (error instanceof BridgeHttpError) throw error;
      throw new BridgeUnreachableError(
        String(error && error.message ? error.message : error)
      );
    } finally {
      clearTimeout(timer);
    }
  }

  async requestRawWithStatus(method, path, body, headers, timeoutMs = this.timeoutMs) {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), timeoutMs);
    try {
      const response = await fetch(this.url + path, {
        method,
        headers,
        body,
        signal: controller.signal,
      });
      const text = await response.text();
      let payload = null;
      if (text) {
        try {
          payload = JSON.parse(text);
        } catch {
          payload = null;
        }
      }
      if (!response.ok) {
        const error = payload && payload.error ? payload.error : {};
        throw new BridgeHttpError(
          String(error.code || "E_INTERNAL"),
          String(error.step || "assets"),
          String(error.message || "HTTP " + response.status),
          response.status
        );
      }
      return { status: response.status, payload: payload || {} };
    } catch (error) {
      if (error instanceof BridgeHttpError) throw error;
      throw new BridgeUnreachableError(
        String(error && error.message ? error.message : error)
      );
    } finally {
      clearTimeout(timer);
    }
  }

  async request(method, path, body = null, timeoutMs = this.timeoutMs) {
    const { payload } = await this.requestWithStatus(method, path, body, timeoutMs);
    return payload;
  }

  // HE-5b: post one staged answer asset (image bytes or the style table). An
  // over-cap buffer is dropped before sending; the caller keeps the answer.
  // WSC-3a ingest adds the optional per-turn association header.
  async postAsset(jobId, { kind, name, body, turnOrdinal = null }) {
    const caps = { image: 2 * 1024 * 1024, style: 64 * 1024 };
    const cap = caps[String(kind)];
    if (!cap) {
      throw new BridgeHttpError(
        "E_UPLOAD_FAILED",
        "assets",
        "unsupported asset kind",
        0
      );
    }
    const data = Buffer.isBuffer(body) ? body : Buffer.from(body || "");
    if (data.length === 0 || data.length > cap) {
      return { skipped: true };
    }
    const headers = { Accept: "application/json" };
    if (this.token) headers["X-Bridge-Token"] = this.token;
    headers["X-Asset-Kind"] = String(kind);
    headers["X-Asset-Name"] = String(name || "");
    if (Number.isInteger(turnOrdinal) && turnOrdinal >= 1) {
      headers["X-Turn-Ordinal"] = String(turnOrdinal);
    }
    headers["Content-Type"] =
      String(kind) === "image" ? "application/octet-stream" : "application/json";
    const { payload } = await this.requestRawWithStatus(
      "POST",
      "/v1/jobs/" + encodeURIComponent(jobId) + "/assets",
      data,
      headers
    );
    return payload;
  }

  // WSC-3a: stage one bounded ingest turn before its per-turn assets.
  stageTurn(jobId, turn) {
    return this.request(
      "POST",
      "/v1/jobs/" + encodeURIComponent(jobId) + "/turns",
      turn
    );
  }

  hello(payload) {
    return this.request("POST", "/v1/hello", payload);
  }

  nextPath(waitSeconds, clientKind) {
    let path = "/v1/next?wait=" + encodeURIComponent(String(waitSeconds));
    if (clientKind) path += "&client=" + encodeURIComponent(String(clientKind));
    path += "&runner_id=" + encodeURIComponent(this.runnerId || "");
    path += "&epoch=" + encodeURIComponent(this.epoch || "");
    return path;
  }

  async next(waitSeconds, clientKind = null) {
    const { payload } = await this.requestWithStatus(
      "GET",
      this.nextPath(waitSeconds, clientKind),
      null,
      (Number(waitSeconds) + 10) * 1000
    );
    return payload.job || null;
  }

  async nextOffer(waitSeconds, clientKind = null, signal = null) {
    const { status, payload } = await this.requestWithStatus(
      "GET",
      this.nextPath(waitSeconds, clientKind),
      null,
      (Number(waitSeconds) + 10) * 1000,
      signal
    );
    return { status, job: payload.job || null };
  }

  events(jobId, events, identity = {}) {
    return this.request(
      "POST",
      "/v1/jobs/" + encodeURIComponent(jobId) + "/events",
      { events, ...identity }
    );
  }

  result(jobId, result) {
    return this.request(
      "POST",
      "/v1/jobs/" + encodeURIComponent(jobId) + "/result",
      result
    );
  }

  status() {
    return this.request("GET", "/v1/status");
  }
}
