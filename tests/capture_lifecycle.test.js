import assert from "node:assert/strict";
import test from "node:test";
import vm from "node:vm";
import { randomUUID } from "node:crypto";
import { mkdtempSync, mkdirSync, writeFileSync, rmSync, readFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

import { JobEngine } from "../src/kronika_capture/_assets/extension/src/headless/job_engine.mjs";
import { LaunchBrake, endpointParser, chromiumLaunchArgs, ChromiumDriver, readinessExpression } from "../src/kronika_capture/_assets/extension/src/headless/driver.mjs";
import { executeOffer, runPersistentService, parseArgs } from "../src/kronika_capture/_assets/extension/src/headless/runner.mjs";

const pack = JSON.parse(readFileSync(new URL("../src/kronika_capture/_assets/extension/src/adapters/pack_v5.json", import.meta.url)));
const uuid = () => randomUUID();
const job = () => ({ job_id: "a".repeat(16), request_id: uuid(), kind: "ask", mode: null,
  files: [], prompt: "synthetic", timeout_s: 10, runner_id: uuid(), offer_id: uuid(), epoch: uuid() });

class FakeDriver {
  constructor() { this.starts = 0; this.stops = 0; this.opens = 0; this.crashed = false; }
  async start() { this.starts++; }
  async stop() { this.stops++; }
  async openPage() { this.opens++; }
  async navigate() {}
  async readiness() { return this.crashed ? { state: "browser_unavailable", reason: "E_BROWSER_UNAVAILABLE" } : { state: "ready" }; }
}

test("one persistent browser/page across jobs and capped bridge reconnect, no shutdown on outage", async () => {
  const driver = new FakeDriver(), controller = new AbortController();
  let hellos = 0, offers = 0, executions = 0;
  const sleeps = [];
  const epoch = uuid();
  const client = {
    async hello() {
      hellos++;
      if (hellos <= 10 || hellos === 12) throw new Error("synthetic transport");
      return { epoch, service_state: "ready" };
    },
    async nextOffer() {
      offers++;
      return { job: { ...job(), runner_id: this.runnerId, epoch } };
    },
  };
  const state = await runPersistentService({ driver, client, pack, signal: controller.signal,
    sleep: async (ms) => { sleeps.push(ms); assert.equal(driver.stops, 0); },
    execute: async () => {
      executions++;
      assert.equal(driver.starts, 1);
      assert.equal(driver.opens, 1);
      if (executions === 2) controller.abort();
    },
  });
  assert.equal(state.jobs, 2);
  assert.equal(offers, 2);
  assert.equal(driver.starts, 1);
  assert.equal(driver.stops, 1); // explicit shutdown only
  assert.equal(Math.max(...sleeps), 30000);
});

test("browser crash blocks readiness and never automatically starts another browser", async () => {
  const driver = new FakeDriver(), controller = new AbortController();
  let offers = 0, blocked = 0;
  const epoch = uuid();
  const client = {
    async hello(payload) {
      if (payload.readiness.state === "browser_unavailable") blocked++;
      return { epoch, service_state: payload.readiness.state };
    },
    async nextOffer() { offers++; return { job: { ...job(), runner_id: this.runnerId, epoch } }; },
  };
  await runPersistentService({ driver, client, pack, signal: controller.signal,
    execute: async () => { driver.crashed = true; },
    sleep: async () => { if (blocked >= 3) controller.abort(); },
  });
  assert.equal(offers, 1);
  assert.equal(blocked, 3);
  assert.equal(driver.starts, 1);
});

function submitEngine({ failIntent = false, clickThrows = false, noResponse = false, failConfirm = false } = {}) {
  let clicks = 0, intents = 0, confirmations = 0, tick = 0;
  const engine = new JobEngine({
    driver: { async clickXY() { clicks++; if (clickThrows) throw new Error("lost CDP acknowledgement"); } },
    now: () => tick++, submitTimeoutMs: 6,
    emit: async (type) => {
      if (type === "send_intent") { intents++; if (failIntent) throw new Error("journal unavailable"); }
      if (type === "send_confirmed") { confirmations++; if (failConfirm) throw new Error("lost result"); }
      return { submission: type === "send_intent" ? "send_intent_persisted" : "send_confirmed" };
    },
  });
  engine.pollMs = 1;
  engine.prompt = "synthetic";
  engine._composerContains = async () => true;
  engine._sendState = async () => ({ disabled: false, rect: { x: 0, y: 0, width: 5, height: 5 } });
  engine._assistantState = async () => ({ count: clicks && !noResponse ? 1 : 0, response_key: "message-1" });
  return { engine, counts: () => ({ clicks, intents, confirmations }) };
}

test("send click is strictly after the acknowledged durable intent", async () => {
  const { engine, counts } = submitEngine();
  const out = await engine._submit();
  assert.equal(out.submit_clicks, 1);
  assert.deepEqual(counts(), { clicks: 1, intents: 1, confirmations: 1 });
  await assert.rejects(engine._submit(), { code: "E_AMBIGUOUS_SEND" });
  assert.equal(counts().clicks, 1);
});

test("admission to send cannot occur on missing intent acknowledgement", async () => {
  const { engine, counts } = submitEngine({ failIntent: true });
  await assert.rejects(engine._submit());
  assert.equal(counts().clicks, 0);
  await assert.rejects(engine._submit(), { code: "E_AMBIGUOUS_SEND" });
  assert.equal(counts().clicks, 0);
});

for (const boundary of ["clickThrows", "noResponse", "failConfirm"]) {
  test("uncertainty at " + boundary + " never re-clicks Send", async () => {
    const { engine, counts } = submitEngine({ [boundary]: true });
    await assert.rejects(engine._submit(), { code: "E_AMBIGUOUS_SEND" });
    await assert.rejects(engine._submit(), { code: "E_AMBIGUOUS_SEND" });
    assert.equal(counts().clicks, 1);
  });
}

test("result transport retry keeps the same identity/body and executes only once", async () => {
  const driver = new FakeDriver(), offered = job();
  let executions = 0, posts = 0;
  const bodies = [];
  const client = {
    async events() { return { epoch: offered.epoch, service_state: "ready" }; },
    async result(_id, body) { posts++; bodies.push(JSON.stringify(body)); if (posts < 3) throw new Error("outage"); },
  };
  class Engine {
    async run() { executions++; return { status: "done", answer: "synthetic", activity_stopped: true }; }
  }
  await executeOffer({ client, driver, pack, job: offered, Engine, sleep: async () => {} });
  assert.equal(executions, 1);
  assert.equal(posts, 3);
  assert.equal(new Set(bodies).size, 1);
  assert.equal(driver.stops, 0);
});

test("offer acceptance failure prevents all browser execution", async () => {
  const offered = job();
  let executions = 0;
  class Engine { async run() { executions++; } }
  await executeOffer({ client: {
    async events() { throw new Error("offer invalidated"); },
    async result() {},
  }, driver: new FakeDriver(), pack, job: offered, Engine });
  assert.equal(executions, 0);
});

for (const submission of ["not_started", "send_confirmed"]) {
test("admin wait needs explicit resume, fresh readiness and same page; excluded from deadline: " + submission, async () => {
  const offered = job(), driver = new FakeDriver();
  let checks = 0, elapsed = 1000, pause = false, resumed = false, heartbeat = 0;
  driver.readiness = async () => {
    checks++;
    return checks === 1 ? { state: "needs_admin", reason: "E_LOGIN_REQUIRED" } : { state: "ready" };
  };
  const intervention = uuid(), resume = uuid();
  const client = {
    async events(_id, events) {
      const { type, data } = events[0];
      if (type === "needs_admin") pause = true;
      if (pause && type === "heartbeat") heartbeat++;
      if (type === "resumed") {
        assert.equal(data.intervention_id, intervention);
        assert.equal(data.resume_id, resume);
        assert.equal(data.ready, true);
        resumed = true;
      }
      return { epoch: offered.epoch, service_state: resumed ? "ready" : pause ? "needs_admin" : "ready",
        intervention_id: intervention, resume_id: heartbeat >= 3 ? resume : null };
    },
    async result() {},
  };
  class Engine {
    constructor(options) { Object.assign(this, options); this.submission = submission; this.responseId = submission === "send_confirmed" ? uuid() : null; }
    async association() { return true; }
    async run() {
      const initial = this.deadlineMs;
      await this.checkpoint(this);
      assert.equal(this.deadlineMs, initial + 1500);
      assert.equal(this.deadlineMs - elapsed, 10000);
      return { status: "done", answer: "synthetic", activity_stopped: true };
    }
  }
  await executeOffer({ client, driver, pack, job: offered, Engine,
    now: () => elapsed, sleep: async (ms) => { elapsed += ms; } });
  assert.equal(resumed, true);
  assert.equal(checks, 2);
  assert.equal(driver.stops, 0);
});

}

test("lost page/response association on explicit resume fails without execution retry", async () => {
  const offered = job(), driver = new FakeDriver();
  let checks = 0, deliveries = [];
  driver.readiness = async () => (++checks === 1 ? { state: "needs_admin", reason: "E_CAPTCHA_REQUIRED" } : { state: "ready" });
  const client = {
    async events() { return { epoch: offered.epoch, service_state: "needs_admin", resume_id: uuid(), intervention_id: uuid() }; },
    async result(_id, body) { deliveries.push(body); },
  };
  class Engine {
    constructor(options) { Object.assign(this, options); this.submission = "send_confirmed"; }
    async association() { return false; }
    async run() { await this.checkpoint(this); throw new Error("unreachable"); }
  }
  await executeOffer({ client, driver, pack, job: offered, Engine, sleep: async () => {} });
  assert.equal(deliveries[0].error_code, "E_AMBIGUOUS_SEND");
  assert.equal(deliveries.length, 1);
});

test("administrator timeout ends job without terminating Chromium", async () => {
  const offered = job(), driver = new FakeDriver();
  let elapsed = 0, delivered;
  driver.readiness = async () => ({ state: "needs_admin", reason: "E_LOGIN_REQUIRED" });
  const client = {
    async events() { return { epoch: offered.epoch, service_state: "needs_admin" }; },
    async result(_id, body) { delivered = body; },
  };
  class Engine {
    constructor(options) { Object.assign(this, options); this.submission = "not_started"; }
    async run() { await this.checkpoint(this); }
  }
  await executeOffer({ client, driver, pack, job: offered, Engine,
    now: () => elapsed, sleep: async () => { elapsed += 1800000; } });
  assert.equal(delivered.error_code, "E_INTERVENTION_TIMEOUT");
  assert.equal(driver.stops, 0);
});

test("durable launch brake enforces 300 seconds, exclusivity, backward clock and malformed/missing state", () => {
  const root = mkdtempSync(join(tmpdir(), "capture-brake-"));
  try {
    let now = 1000000;
    const directory = join(root, "launch");
    const first = new LaunchBrake(directory, { now: () => now });
    first.acquire();
    assert.throws(() => new LaunchBrake(directory, { now: () => now + 400000 }).acquire());
    first.release();
    now += 299999;
    assert.throws(() => new LaunchBrake(directory, { now: () => now }).acquire());
    now -= 400000;
    assert.throws(() => new LaunchBrake(directory, { now: () => now }).acquire());
    now = 1300000;
    const allowed = new LaunchBrake(directory, { now: () => now });
    allowed.acquire(); allowed.release();
    writeFileSync(join(directory, "last-start.json"), "invalid");
    assert.throws(() => new LaunchBrake(directory, { now: () => 99999999 }).acquire());
    const missing = join(root, "missing");
    mkdirSync(missing);
    assert.throws(() => new LaunchBrake(missing).acquire());
  } finally { rmSync(root, { recursive: true, force: true }); }
});

test("endpoint parsing is bounded, loopback-only and consumes stderr in memory", () => {
  const parser = endpointParser();
  parser.feed("unrelated private browser stderr\nDevTools listen");
  parser.feed("ing on ws://127.0.0.1:9222/devtools/browser/abc-123\n");
  assert.deepEqual(parser.endpoint, { wsUrl: "ws://127.0.0.1:9222/devtools/browser/abc-123", port: 9222 });
  const wrong = endpointParser();
  wrong.feed("DevTools listening on ws://example.test:9222/devtools/browser/abc\n");
  assert.equal(wrong.endpoint, null);
  const bounded = endpointParser();
  bounded.feed("x".repeat(70000));
  bounded.feed("\nDevTools listening on ws://127.0.0.1:9222/devtools/browser/abc\n");
  assert.equal(bounded.endpoint, null);
});

test("launch configuration rejects stealth and automatic binary discovery", () => {
  assert.equal(ChromiumDriver.defaultBinary(), null);
  assert.throws(() => chromiumLaunchArgs({ profileDir: "/synthetic", stealth: true }));
  assert.ok(parseArgs(["run"]).error);
  assert.ok(parseArgs(["run", "--stealth"]).error);
  assert.ok(!parseArgs(["run", "--chrome-path", "/synthetic/chromium"]).error);
  const flags = chromiumLaunchArgs({ profileDir: "/synthetic" });
  assert.ok(!flags.includes("--no-sandbox"));
});

test("owned page readiness inspects structural blockers without model/profile access", () => {
  const expression = readinessExpression(pack);
  const visible = (text = "") => ({ isConnected: true, getClientRects: () => [1], textContent: text });
  function evaluate(hits, origin = "https://chatgpt.com") {
    return vm.runInNewContext(expression, {
      location: { origin }, document: { querySelectorAll: (selector) => hits[selector] || [] },
    });
  }
  const composer = 'div#prompt-textarea[contenteditable="true"]';
  assert.equal(evaluate({ [composer]: [visible()], "#composer-submit-button": [visible()] }).state, "ready");
  assert.equal(evaluate({ [composer]: [visible()], 'iframe[src*="challenges.cloudflare.com"]': [visible()] }).reason, "E_CAPTCHA_REQUIRED");
  assert.equal(evaluate({ '[role="alert"], [role="dialog"]': [visible("usage limit")] }).reason, "E_LIMIT_REACHED");
  assert.equal(evaluate({ '[role="alert"], [role="dialog"]': [visible("accept cookies")] }).reason, "E_CONSENT_REQUIRED");
  assert.equal(evaluate({ 'input[type="password"]': [visible()] }).reason, "E_LOGIN_REQUIRED");
  assert.equal(evaluate({}, "https://example.test").state, "needs_admin");
  assert.doesNotMatch(expression, /localStorage|cookie\b|model|reasoning/);
});

test("browser/CDP disappearance reports unavailability without a start attempt", async () => {
  const driver = new ChromiumDriver({ chromePath: "/synthetic/chromium", profileDir: "/synthetic/profile" });
  assert.equal((await driver.readiness(pack)).state, "browser_unavailable");
  driver.startedOnce = true;
  await assert.rejects(driver.start(), { code: "E_BROWSER_UNAVAILABLE" });
});

test("real job engine and runner cooperate through one barrier and isolated response association", async () => {
  const offered = job(), driver = new FakeDriver();
  let clicked = 0, intent = false, pageKey, delivered;
  driver.clickXY = async () => { assert.equal(intent, true); clicked++; };
  driver.evaluate = async (expression) => {
    if (expression.includes("capture_bind")) {
      pageKey = expression.match(/"([a-f0-9-]{36})"/)[1]; return pageKey;
    }
    if (expression.includes("capture_page")) return pageKey;
    if (expression.includes("composer_state")) return { kind: "textarea", empty: false };
    if (expression.includes("composer_insert") || expression.includes("composer_clear")) return { ok: true };
    if (expression.includes("composer_contains")) return true;
    if (expression.includes("send_state")) return { disabled: false, rect: { x: 1, y: 1, width: 5, height: 5 } };
    if (expression.includes("assistant_state")) return { count: clicked, text: clicked ? "synthetic answer" : "",
      response_key: clicked ? "response-owned" : null, url: "https://chatgpt.com/" };
    if (expression.includes("stop_visible")) return false;
    if (expression.includes("/*kronika:url*/")) return "https://chatgpt.com/";
    if (expression.includes("location.href")) return "https://chatgpt.com/";
    throw new Error("Unexpected fake-driver expression");
  };
  const client = {
    async events(_id, events) {
      if (events[0].type === "send_intent") intent = true;
      return { epoch: offered.epoch, service_state: "ready", submission:
        events[0].type === "send_confirmed" ? "send_confirmed" : intent ? "send_intent_persisted" : "not_started" };
    },
    async result(_id, body) { delivered = body; },
  };
  await executeOffer({ client, driver, pack: { ...pack, constants: { poll_ms: 1, stability_ms: 1 } }, job: offered });
  assert.equal(delivered.status, "done");
  assert.equal(delivered.answer, "synthetic answer");
  assert.equal(clicked, 1);
  assert.equal(delivered.activity_stopped, true);
});

test("newline composition never dispatches an Enter-equivalent key before the send barrier", async () => {
  const calls = [];
  const engine = new JobEngine({ driver: { async send(method, params) { calls.push({ method, params }); } } });
  await engine._typeCharacters("a\nb\r");
  assert.equal(calls.filter((call) => call.method === "Input.insertText").length, 2);
  assert.ok(calls.filter((call) => call.method === "Input.dispatchKeyEvent")
    .every((call) => !["\n", "\r", "Enter"].includes(call.params.key)));
});

test("startup failure stays unavailable without an automatic launch retry", async () => {
  const driver = new FakeDriver(), controller = new AbortController();
  let unavailable = 0;
  driver.start = async () => { driver.starts++; throw new Error("synthetic startup failure"); };
  const client = {
    async hello(body) {
      assert.equal(body.readiness.state, "browser_unavailable");
      unavailable++;
      return { epoch: uuid(), service_state: "browser_unavailable" };
    },
    async nextOffer() { throw new Error("must not offer"); },
  };
  await runPersistentService({ driver, client, pack, signal: controller.signal,
    sleep: async () => { if (unavailable === 3) controller.abort(); },
  });
  assert.equal(driver.starts, 1);
  assert.equal(driver.opens, 0);
});

test("readiness blocks an unidentified generation and permits only an associated observation", async () => {
  const driver = new ChromiumDriver({ chromePath: "/synthetic/chromium", profileDir: "/synthetic/profile" });
  driver.child = { exitCode: null, signalCode: null };
  driver.client = {};
  driver.targetId = "owned-target";
  driver.evaluate = async () => ({ state: "ready", generating: true, send_present: false });
  assert.equal((await driver.readiness(pack)).reason, "E_AMBIGUOUS_SEND");
  assert.equal((await driver.readiness(pack, { observing: true })).state, "ready");
  driver.evaluate = async () => { throw new Error("CDP disconnected"); };
  assert.equal((await driver.readiness(pack)).state, "browser_unavailable");
});

test("actual observation failure on response association loss never sends again", async () => {
  const engine = new JobEngine({ driver: {}, deadlineMs: 100, now: () => 1 });
  engine.submission = "send_confirmed";
  engine.association = async () => false;
  await assert.rejects(engine._observeAnswer({ baseline: 0 }), { code: "E_AMBIGUOUS_SEND" });
});

test("stop cannot release the launch lock while browser termination is unconfirmed", async () => {
  let released = 0;
  const driver = new ChromiumDriver({ chromePath: "/synthetic/chromium",
    profileDir: "/synthetic/profile", stopGraceMs: 0,
    launchBrake: { release() { released++; } },
  });
  driver.child = { exitCode: null, signalCode: null, kill() {} };
  await assert.rejects(driver.stop(), { code: "E_BROWSER_UNAVAILABLE" });
  assert.equal(released, 0);
  assert.ok(driver.child); // a second stop cannot forget the still-running process
});
