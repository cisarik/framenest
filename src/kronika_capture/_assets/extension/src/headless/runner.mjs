// Headless runner: registers a headless client with the local bridge, accepts
// job offers, and executes them through the job engine on the configured
// Chromium profile.
//
// Modes:
//   run      hello/heartbeat, long-poll `GET /v1/next` as client "headless",
//            accept an offer, run the job engine, post progress events and the
//            terminal result, and observe cancellation. Runs until SIGINT or
//            SIGTERM; `--once` stops after one executed offer.
//   connect  send `hello` and long-poll once; a 204 is the expected answer. If
//            an offer ever arrives it is refused with a typed log and a
//            non-zero exit (connectivity check only; it never executes).
//   status   read `GET /v1/status` and print it, including the configured
//            job executor and the connected client kind.
//
// The runner never reads browser profiles, cookies, or page content; it only
// drives the engine page through the driver. Logs carry job ids, phases, and
// error codes, never prompts or answers.

import { createHash, randomUUID } from "node:crypto";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { pathToFileURL } from "node:url";
import { setTimeout as delay } from "node:timers/promises";
import { performance } from "node:perf_hooks";

import {
  BridgeClient,
  BridgeHttpError,
  BridgeUnreachableError,
  DEFAULT_BRIDGE_PORT,
  readConfiguredPort,
  readToken,
  resolveStateDir,
} from "./bridge_client.mjs";
import { CLIENT_CAPABILITIES, RESULT_MAX_BYTES } from "../protocol.js";
import { ChromiumDriver } from "./driver.mjs";
import { JobEngine, JobEngineError } from "./job_engine.mjs";
import { applyResourcePolicy } from "./resource_policy.mjs";

const PROTO = 1;
const CLIENT_KIND = "headless";
const NEXT_WAIT_S = 20;
const HELLO_INTERVAL_MS = 25000;
const JOB_HEARTBEAT_MS = 25000;
const EXIT_OK = 0;
const EXIT_ERROR = 1;
const EXIT_REFUSED = 2;

const MODES = new Set(["run", "connect", "status"]);

function usage() {
  return [
    "usage: runner.mjs <run|connect|status> [options]",
    "",
    "options:",
    "  --state-dir <dir>   bridge state directory (default: XDG state)",
    "  --port <port>       bridge port (default: recorded port or 8765)",
    "  --profile <dir>     engine profile for run (default: <state>/chromium-profile)",
    "  --engine <name>     engine for run (chromium only; default: chromium)",
    "  --chrome-path <file>  explicitly configured, preflight-verified Chromium",
    "  --headed            Chromium: run with a visible window",
    "  --no-resource-policy  run: disable the HE-5a resource policy (diagnosis only)",
    "  --once              run: stop after one executed offer",
    "  --wait <seconds>    long-poll wait (default: 20 for run, 0 for connect; max 25)",
  ].join("\n");
}

export function parseArgs(argv) {
  const options = {
    mode: null,
    stateDir: null,
    port: null,
    wait: null,
    profile: null,
    engine: "chromium",
    stealth: false,
    chromePath: null,
    headed: false,
    resourcePolicy: true,
    once: false,
  };
  const rest = [...argv];
  const seen = new Set();
  options.mode = rest.shift() || null;
  if (!MODES.has(options.mode)) {
    return { error: usage() };
  }
  while (rest.length > 0) {
    const flag = rest.shift();
    if (flag === "--state-dir" && rest.length > 0) {
      options.stateDir = rest.shift();
    } else if (flag === "--port" && rest.length > 0) {
      options.port = Number(rest.shift());
    } else if (flag === "--wait" && rest.length > 0) {
      options.wait = Number(rest.shift());
    } else if (flag === "--profile" && rest.length > 0) {
      options.profile = rest.shift();
      seen.add("profile");
    } else if (flag === "--engine" && rest.length > 0) {
      options.engine = rest.shift();
      seen.add("engine");
    } else if (flag === "--chrome-path" && rest.length > 0) {
      options.chromePath = rest.shift();
      seen.add("chrome-path");
    } else if (flag === "--stealth") {
      return { error: "stealth is not supported" };
    } else if (flag === "--headed") {
      options.headed = true;
      seen.add("headed");
    } else if (flag === "--no-resource-policy") {
      options.resourcePolicy = false;
      seen.add("no-resource-policy");
    } else if (flag === "--once") {
      options.once = true;
      seen.add("once");
    } else {
      return { error: `unknown argument ${flag}\n\n${usage()}` };
    }
  }
  if (options.port !== null && !(Number.isInteger(options.port) && options.port >= 1 && options.port <= 65535)) {
    return { error: "--port must be an integer in 1..65535" };
  }
  if (options.wait === null) {
    options.wait = options.mode === "run" ? NEXT_WAIT_S : 0;
  }
  if (!(Number.isFinite(options.wait) && options.wait >= 0 && options.wait <= 25)) {
    return { error: "--wait must be a number in 0..25" };
  }
  if (options.mode !== "run") {
    for (const flag of [
      "profile",
      "engine",
      "chrome-path",
      "headed",
      "no-resource-policy",
      "once",
    ]) {
      if (seen.has(flag)) {
        return { error: `--${flag} is only valid with the run mode` };
      }
    }
  }
  if (options.engine !== "chromium") {
    return { error: "headless job execution is Chromium-only in this grant" };
  }
  if (options.mode === "run" && !options.chromePath) return { error: "--chrome-path is required" };
  return { options };
}

function loadPack() {
  const packUrl = new URL("../adapters/pack_v5.json", import.meta.url);
  const bytes = readFileSync(packUrl);
  const pack = JSON.parse(bytes.toString("utf8"));
  const sha256 = createHash("sha256").update(bytes).digest("hex");
  return { pack, sha256 };
}

function buildClient(options) {
  const stateDir = options.stateDir || resolveStateDir();
  const port = options.port || readConfiguredPort(stateDir) || DEFAULT_BRIDGE_PORT;
  const token = readToken(stateDir);
  if (!token) {
    throw new BridgeHttpError(
      "E_HEADLESS_NO_TOKEN",
      "runner",
      `no bridge token under ${stateDir}; run 'kronika setup' first`,
      0
    );
  }
  return new BridgeClient({ url: `http://127.0.0.1:${port}`, token });
}

async function modeConnect(client) {
  // A connectivity probe never registers an executor or consumes an offer.
  await modeStatus(client);
  return EXIT_OK;
}

async function modeStatus(client) {
  const status = await client.status();
  console.log(JSON.stringify({ mode: "status", client: CLIENT_KIND, status }, null, 2));
  return EXIT_OK;
}

function failedResult(errorCode, step) {
  return {
    status: "failed",
    answer: null,
    answer_html: null,
    error_code: errorCode,
    url: null,
    step,
  };
}

function errorCode(error) {
  if (!error) return "E_INTERNAL";
  return typeof error.code === "string" && error.code ? error.code : "E_INTERNAL";
}

export function offerIdentity(job) {
  return { runner_id: job.runner_id, offer_id: job.offer_id, epoch: job.epoch };
}

function lifecycleError(code) {
  return new JobEngineError(code, "lifecycle", "Capture lifecycle could not continue safely.");
}

export async function executeOffer({
  client, driver, pack, job, signal = null, heartbeatMs = JOB_HEARTBEAT_MS,
  sleep = (ms) => delay(ms), now = () => performance.now(), Engine = JobEngine, refresh = async () => {},
}) {
  const identity = offerIdentity(job);
  let cancelled = false, heartbeatError = null, adminWait = 0;
  const emit = async (type, data) => {
    const reply = await client.events(job.job_id, [{ type, data }], identity);
    if (reply.epoch !== job.epoch) throw lifecycleError("E_AMBIGUOUS_SEND");
    cancelled ||= reply.cancel_requested === true || reply.terminal === true;
    return reply;
  };
  const checkpoint = async (engine) => {
    if (heartbeatError) throw heartbeatError;
    await refresh();
    const control = await emit("heartbeat", {});
    if (cancelled || signal?.aborted) throw lifecycleError("E_CANCELLED");
    const ready = await driver.readiness(pack, { observing: engine.submission === "send_confirmed" });
    if (ready.state === "browser_unavailable") throw lifecycleError("E_BROWSER_UNAVAILABLE");
    if (ready.state === "ready" && control.service_state === "ready") return;
    if (engine.submission === "send_intent_persisted") throw lifecycleError("E_AMBIGUOUS_SEND");
    const reason = ["E_LOGIN_REQUIRED", "E_CAPTCHA_REQUIRED", "E_CONSENT_REQUIRED",
      "E_LIMIT_REACHED", "E_COMPOSER_NOT_FOUND"].includes(ready.reason) ? ready.reason : "E_NEEDS_ADMIN";
    let pause = await emit("needs_admin", { reason });
    const started = now();
    for (;;) {
      if (adminWait + now() - started >= 1800000) throw lifecycleError("E_INTERVENTION_TIMEOUT");
      if (signal?.aborted || cancelled) throw lifecycleError("E_CANCELLED");
      await sleep(500);
      pause = await emit("heartbeat", {});
      if (cancelled) throw lifecycleError("E_CANCELLED");
      if (!pause.resume_id) continue;
      const recheck = await driver.readiness(pack, { observing: engine.submission === "send_confirmed" });
      if (recheck.state !== "ready") continue;
      if (!(await engine.association())) throw lifecycleError("E_AMBIGUOUS_SEND");
      const resumed = await emit("resumed", {
        resume_id: pause.resume_id, intervention_id: pause.intervention_id,
        ready: true, response_id: engine.responseId,
      });
      if (resumed.terminal || resumed.service_state !== "ready") throw lifecycleError("E_INTERVENTION_TIMEOUT");
      const waited = now() - started;
      adminWait += waited;
      engine.deadlineMs += waited;
      return;
    }
  };
  let result;
  let heartbeat;
  try {
    const accepted = await emit("status", { status: "accepted" });
    if (accepted.terminal || cancelled) throw lifecycleError("E_AMBIGUOUS_SEND");
    const engine = new Engine({ driver, pack, emit, checkpoint, now,
      isCancelled: () => cancelled || Boolean(signal?.aborted),
      deadlineMs: now() + Math.max(1, Number(job.timeout_s) || 600) * 1000,
    });
    heartbeat = setInterval(() => {
      refresh().then(() => emit("heartbeat", {})).catch((error) => { heartbeatError = error; });
    }, heartbeatMs);
    result = await engine.run(job);
  } catch (error) {
    result = { ...failedResult(errorCode(error), "lifecycle"), activity_stopped: false };
  } finally { clearInterval(heartbeat); }
  // Freeze one delivery identity. A size rejection replaces content with a small
  // terminal failure; only delivery of that envelope, never execution, retries.
  let payload = {
    ...identity, job_id: job.job_id, delivery_id: randomUUID(), status: result.status,
    answer: result.answer ?? null, error_code: result.error_code ?? null,
    answer_html: result.answer_html ?? null,
    url: result.url ?? null, step: result.step || "engine",
    activity_stopped: result.activity_stopped === true, proto: PROTO,
  };
  if (result.project_ok !== undefined) payload.project_ok = result.project_ok;
  if (result.appended !== undefined) payload.appended = result.appended;
  const rejectSize = () => {
    result = { ...failedResult("E_RESULT_TOO_LARGE", "delivery"),
      activity_stopped: payload.activity_stopped };
    payload = { ...identity, job_id: job.job_id, delivery_id: payload.delivery_id,
      ...result, proto: PROTO };
  };
  if (Buffer.byteLength(JSON.stringify(payload), "utf8") > RESULT_MAX_BYTES) rejectSize();
  let attempt = 0;
  while (!signal?.aborted) {
    try { await client.result(job.job_id, payload); return result; }
    catch (error) {
      if (error.status === 409 || error.status === 404) return failedResult("E_AMBIGUOUS_SEND", "delivery");
      if (error.status === 413 || error.code === "E_RESULT_TOO_LARGE") {
        if (payload.error_code === "E_RESULT_TOO_LARGE") throw error;
        rejectSize();
        continue;
      }
      await sleep(Math.min(30000, 250 * 2 ** Math.min(attempt++, 7)));
    }
  }
  return result;
}

export async function runJobLoop({
  client, driver, pack, packSha256 = null, signal = null, waitSeconds = NEXT_WAIT_S,
  once = false, heartbeatMs = JOB_HEARTBEAT_MS, log = () => {},
  sleep = (ms) => delay(ms), execute = executeOffer,
}) {
  const state = { jobs: 0 };
  const runnerId = randomUUID(), browserSession = randomUUID();
  client.runnerId = runnerId;
  let attempt = 0, resumeId = null;
  const seenOffers = new Set();
  while (!signal?.aborted) {
    try {
      const readiness = await driver.readiness(pack);
      const hello = await client.hello({
        proto: PROTO, client: CLIENT_KIND, runner_id: runnerId,
        browser_session: browserSession, pack_version: pack.pack_version,
        pack_sha256: packSha256, capabilities: [...CLIENT_CAPABILITIES],
        readiness, resume_id: resumeId,
      });
      client.epoch = hello.epoch;
      resumeId = hello.resume_id;
      if (hello.service_state !== "ready" || readiness.state !== "ready") {
        await sleep(1000);
        continue;
      }
      const offer = await client.nextOffer(waitSeconds, CLIENT_KIND, signal);
      attempt = 0;
      if (signal?.aborted) break;
      if (!offer.job) continue;
      const job = offer.job;
      if (job.runner_id !== runnerId || job.epoch !== client.epoch || seenOffers.has(job.offer_id)) {
        throw lifecycleError("E_AMBIGUOUS_SEND");
      }
      seenOffers.add(job.offer_id);
      // Bound memory without permitting a previously consumed offer to execute:
      // the bridge never offers a non-queued job; a new loop has a new runner identity.
      if (seenOffers.size > 256) seenOffers.delete(seenOffers.values().next().value);
      const refresh = async () => {
        const hello = await client.hello({
          proto: PROTO, client: CLIENT_KIND, runner_id: runnerId, browser_session: browserSession,
          pack_version: pack.pack_version, capabilities: [...CLIENT_CAPABILITIES],
          readiness: await driver.readiness(pack, { observing: true }),
        });
        if (hello.epoch !== job.epoch) throw lifecycleError("E_AMBIGUOUS_SEND");
      };
      await execute({ client, driver, pack, job, signal, heartbeatMs, sleep, refresh });
      state.jobs++;
      if (once) break;
    } catch {
      if (signal?.aborted) break;
      log("bridge unavailable; browser retained");
      await sleep(Math.min(30000, 250 * 2 ** Math.min(attempt++, 7)));
    }
  }
  return state;
}

export async function runPersistentService({ driver, pack, client, afterOpen = async () => {}, ...options }) {
  let startupFailed = false;
  try {
    await driver.start();
    await driver.openPage();
    await afterOpen();
    await driver.navigate("https://chatgpt.com/");
  } catch {
    startupFailed = true;
  }
  // A failed startup is an unavailable service, never a browser restart loop.
  const ownedDriver = startupFailed ? {
    readiness: async () => ({ state: "browser_unavailable", reason: "E_BROWSER_UNAVAILABLE" }),
  } : driver;
  try { return await runJobLoop({ driver: ownedDriver, pack, client, ...options }); }
  finally {
    if (options.signal?.aborted || options.once) await driver.stop();
  }
}

async function modeRun(options) {
  const stateDir = options.stateDir || resolveStateDir();
  const profileDir = options.profile || join(stateDir, "chromium-profile");
  const { pack, sha256 } = loadPack();
  const client = buildClient(options);
  const driver = new ChromiumDriver({
    profileDir,
    chromePath: options.chromePath,
    headed: options.headed,
  });
  const controller = new AbortController();
  let stopping = false;
  const onSignal = (signal) => {
    if (stopping) return;
    stopping = true;
    console.error(`[headless] signal ${signal}; stopping the job loop`);
    controller.abort();
  };
  process.once("SIGINT", onSignal);
  process.once("SIGTERM", onSignal);
  const log = (message) => console.error(`[headless] ${message}`);
  let resourcePolicy = null;
  try {
    const state = await runPersistentService({
      client, driver, pack, packSha256: sha256, signal: controller.signal,
      waitSeconds: options.wait, once: options.once, log,
      afterOpen: async () => {
        if (options.resourcePolicy) resourcePolicy = await applyResourcePolicy({ driver, log });
      },
    });
    log(`stopped after ${state.jobs} job(s)`);
    return EXIT_OK;
  } finally {
    process.removeListener("SIGINT", onSignal);
    process.removeListener("SIGTERM", onSignal);
    if (resourcePolicy) resourcePolicy.dispose();
  }
}

export async function main(argv) {
  const parsed = parseArgs(argv);
  if (parsed.error) {
    console.error(`error: [E_HEADLESS_USAGE] ${parsed.error}`);
    return EXIT_ERROR;
  }
  const options = parsed.options;
  let client;
  try {
    client = buildClient(options);
  } catch (error) {
    console.error(`error: [${error.code || "E_INTERNAL"}] ${error.message}`);
    return EXIT_ERROR;
  }
  try {
    if (options.mode === "connect") {
      return await modeConnect(client, options.wait);
    }
    if (options.mode === "run") {
      return await modeRun(options);
    }
    return await modeStatus(client);
  } catch (error) {
    if (error instanceof BridgeHttpError) {
      console.error(`error: [${error.code}] ${error.step}: ${error.message}`);
    } else if (error instanceof BridgeUnreachableError) {
      console.error(
        `error: [E_HEADLESS_UNREACHABLE] bridge unreachable at ${client.url}: ${error.message}`
      );
    } else {
      const code =
        typeof error.code === "string" && error.code
          ? error.code
          : "E_HEADLESS_INTERNAL";
      console.error(`error: [${code}] ${error.message}`);
    }
    return EXIT_ERROR;
  }
}

const isMain =
  process.argv[1] &&
  import.meta.url === pathToFileURL(process.argv[1]).href;

if (isMain) {
  process.exitCode = await main(process.argv.slice(2));
}
