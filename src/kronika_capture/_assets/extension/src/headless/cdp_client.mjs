// Shared raw-CDP client used by the Chromium headless driver (HE-3c).
//
// WebSocket message framing, the pending-request map with per-call timeouts,
// the one-shot event waiter, the named-event subscription, and the loopback
// listener check. A method that must reach the browser-level session passes
// useSession=false.

import { setTimeout as delay } from "node:timers/promises";

export class DriverError extends Error {
  constructor(code, message) {
    super(message);
    this.name = "DriverError";
    this.code = code;
  }
}

export function loopbackUrl(port) {
  return `http://127.0.0.1:${port}`;
}

export function assertLoopbackHost(hostname, code = "E_DRIVER_HOST") {
  if (hostname !== "127.0.0.1") {
    throw new DriverError(code, `engine advertises a non-loopback listener: ${hostname}`);
  }
}

export class CdpClient {
  constructor({ wsUrl, cdpTimeoutMs = 20000, sessionId = null }) {
    this.wsUrl = wsUrl;
    this.cdpTimeoutMs = cdpTimeoutMs;
    this.sessionId = sessionId;
    this.ws = null;
    this.nextId = 1;
    this.pending = new Map();
    this.eventHandlers = new Set();
  }

  async connect() {
    if (this.ws) return;
    const ws = new WebSocket(this.wsUrl);
    ws.addEventListener("message", (event) => {
      let message = null;
      try {
        message = JSON.parse(event.data);
      } catch {
        return;
      }
      if (message.id && this.pending.has(message.id)) {
        const { resolve, reject } = this.pending.get(message.id);
        this.pending.delete(message.id);
        if (message.error) {
          reject(
            new DriverError(
              "E_DRIVER_CDP",
              `${message.error.message || "CDP error"} (${message.error.code})`
            )
          );
        } else {
          resolve(message.result);
        }
        return;
      }
      if (message.method) {
        for (const handler of [...this.eventHandlers]) handler(message);
      }
    });
    await new Promise((resolve, reject) => {
      ws.addEventListener("open", resolve, { once: true });
      ws.addEventListener(
        "error",
        () => reject(new DriverError("E_DRIVER_WS", "CDP websocket failed")),
        { once: true }
      );
    });
    this.ws = ws;
  }

  send(method, params = {}) {
    if (!this.ws) throw new DriverError("E_DRIVER_STATE", "engine is not connected");
    return this._send(method, params, this.sessionId);
  }

  sendBrowser(method, params = {}) {
    if (!this.ws) throw new DriverError("E_DRIVER_STATE", "engine is not connected");
    return this._send(method, params, null);
  }

  sendTo(sessionId, method, params = {}) {
    if (!this.ws) throw new DriverError("E_DRIVER_STATE", "engine is not connected");
    return this._send(method, params, sessionId || this.sessionId);
  }

  _send(method, params, sessionId) {
    return new Promise((resolve, reject) => {
      const id = this.nextId++;
      const timer = setTimeout(() => {
        if (this.pending.has(id)) {
          this.pending.delete(id);
          reject(new DriverError("E_DRIVER_TIMEOUT", `CDP timeout: ${method}`));
        }
      }, this.cdpTimeoutMs);
      this.pending.set(id, {
        resolve: (value) => {
          clearTimeout(timer);
          resolve(value);
        },
        reject: (error) => {
          clearTimeout(timer);
          reject(error);
        },
      });
      const message = { id, method, params };
      if (sessionId) message.sessionId = sessionId;
      this.ws.send(JSON.stringify(message));
    });
  }

  once(method, timeoutMs) {
    return new Promise((resolve) => {
      const handler = (message) => {
        if (message.method !== method) return;
        if (this.sessionId && message.sessionId !== this.sessionId) return;
        clearTimeout(timer);
        this.eventHandlers.delete(handler);
        resolve(true);
      };
      const timer = setTimeout(() => {
        this.eventHandlers.delete(handler);
        resolve(false);
      }, timeoutMs);
      this.eventHandlers.add(handler);
    });
  }

  on(method, handler) {
    const listener = (message) => {
      if (message.method !== method) return;
      if (this.sessionId && message.sessionId !== this.sessionId) return;
      handler(message.params);
    };
    this.eventHandlers.add(listener);
    return () => this.eventHandlers.delete(listener);
  }

  onSession(sessionId, method, handler) {
    const listener = (message) => {
      if (message.method !== method) return;
      if (message.sessionId !== sessionId) return;
      handler(message.params);
    };
    this.eventHandlers.add(listener);
    return () => this.eventHandlers.delete(listener);
  }

  async close() {
    if (!this.ws) return;
    try {
      this.ws.close();
    } catch {
      // closing an already-closed socket is not an error
    }
    this.ws = null;
  }
}

export async function waitForEndpoint(check, { timeoutMs, pollMs = 150, delayFn = delay } = {}) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    try {
      const value = await check();
      if (value) return value;
    } catch {
      // a not-yet-ready endpoint is expected during startup
    }
    await delayFn(pollMs);
  }
  throw new DriverError("E_DRIVER_START", "engine did not expose a CDP endpoint in time");
}
