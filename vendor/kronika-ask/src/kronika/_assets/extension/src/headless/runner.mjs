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

import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import { basename, join } from "node:path";
import { pathToFileURL } from "node:url";

import {
  BridgeClient,
  BridgeHttpError,
  BridgeUnreachableError,
  DEFAULT_BRIDGE_PORT,
  readConfiguredPort,
  readToken,
  resolveStateDir,
} from "./bridge_client.mjs";
import { CLIENT_CAPABILITIES } from "../protocol.js";
import { ChromiumDriver } from "./driver.mjs";
import { JobEngine } from "./job_engine.mjs";
import { applyResourcePolicy, COUNTER_KEYS } from "./resource_policy.mjs";

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
    "  --stealth           Chromium: add the bounded stealth launch flags",
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
    } else if (flag === "--stealth") {
      options.stealth = true;
      seen.add("stealth");
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
      "stealth",
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

async function modeConnect(client, waitSeconds) {
  const { pack, sha256 } = loadPack();
  const hello = await client.hello({
    proto: PROTO,
    client: CLIENT_KIND,
    pack_version: pack.pack_version,
    pack_sha256: sha256,
    capabilities: [...CLIENT_CAPABILITIES],
  });
  const result = {
    mode: "connect",
    client: CLIENT_KIND,
    proto: PROTO,
    pack_version: pack.pack_version,
    pack_sha256: sha256,
    hello,
    next: null,
  };
  const offer = await client.nextOffer(waitSeconds, CLIENT_KIND);
  if (offer.status === 204 && offer.job === null) {
    result.next = { status: 204, job: null };
    console.log(JSON.stringify(result, null, 2));
    return EXIT_OK;
  }
  if (offer.job === null) {
    result.next = { status: offer.status, job: null };
    console.log(JSON.stringify(result, null, 2));
    return EXIT_OK;
  }
  result.next = { status: offer.status, job_id: offer.job.job_id, kind: offer.job.kind };
  console.log(JSON.stringify(result, null, 2));
  console.error(
    `error: [E_HEADLESS_JOB_OFFER] received an offer for job ${offer.job.job_id}; ` +
      "the connect mode is a connectivity check and never executes jobs"
  );
  return EXIT_REFUSED;
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

async function executeOffer({
  client,
  driver,
  pack,
  job,
  log,
  signal = null,
  resourcePolicy = null,
  heartbeatMs = JOB_HEARTBEAT_MS,
}) {
  const jobState = { cancelRequested: false, timedOut: false };
  const policyBefore = resourcePolicy ? resourcePolicy.snapshot() : null;
  const emit = async (type, data) => {
    try {
      const payload = await client.events(job.job_id, [{ type, data }]);
      if (payload && payload.cancel_requested === true) {
        jobState.cancelRequested = true;
      }
    } catch (error) {
      log(
        `job ${job.job_id}: event post failed (${errorCode(error)}); job continues`
      );
    }
  };
  await emit("status", { status: "accepted" });
  let result;
  const unsupportedKind = job.kind !== "ask";
  const unsupportedMode = job.mode !== null && job.mode !== undefined;
  if (Array.isArray(job.files) && job.files.length > 0) {
    result = failedResult("E_UPLOAD_FAILED", "upload");
  } else if (unsupportedKind || unsupportedMode) {
    result = failedResult(
      job.mode === "web_search"
        ? "E_WEB_SEARCH_UNAVAILABLE"
        : job.mode === "deep_research"
          ? "E_DEEP_RESEARCH_UNAVAILABLE"
          : "E_INTERNAL",
      unsupportedKind ? "kind" : "mode"
    );
  } else {
    const timeoutMs = Math.max(1, Number(job.timeout_s) || 600) * 1000;
    const engine = new JobEngine({
      driver,
      pack,
      emit,
      isCancelled: () =>
        jobState.cancelRequested || Boolean(signal && signal.aborted),
      deadlineMs: Date.now() + timeoutMs,
      log,
    });
    const timer = setTimeout(() => {
      jobState.cancelRequested = true;
      jobState.timedOut = true;
    }, timeoutMs);
    const heartbeat = setInterval(() => {
      emit("progress", { phase: engine.phase });
    }, heartbeatMs);
    try {
      result = await engine.run(job);
    } catch (error) {
      result = failedResult(errorCode(error), "engine");
      if (error && error.message) {
        log(`job ${job.job_id}: engine failure: ${String(error.message)}`);
      }
    } finally {
      clearTimeout(timer);
      clearInterval(heartbeat);
    }
  }
  if (result.status !== "done" && jobState.timedOut) {
    result = failedResult("E_RESPONSE_TIMEOUT", "observe");
  } else if (result.status !== "done" && jobState.cancelRequested) {
    result = {
      status: "cancelled",
      answer: null,
      answer_html: null,
      error_code: "E_CANCELLED",
      url: null,
    };
  }
  if (result.diagnostics) {
    log(`job ${job.job_id}: diagnostics ${JSON.stringify(result.diagnostics)}`);
  }
  if (result.message) {
    log(`job ${job.job_id}: ${result.message}`);
  }
  const payload = {
    job_id: job.job_id,
    status: result.status,
    answer: result.answer === undefined ? null : result.answer,
    answer_html: result.answer_html === undefined ? null : result.answer_html,
    error_code: result.error_code === undefined ? null : result.error_code,
    url: result.url === undefined ? null : result.url,
    proto: PROTO,
  };
  if (result.project_ok !== undefined) payload.project_ok = result.project_ok;
  if (result.appended !== undefined) payload.appended = result.appended;
  if (result.status === "failed" && typeof result.step === "string") {
    payload.step = result.step;
  }
  try {
    await client.result(job.job_id, payload);
  } catch (error) {
    log(`job ${job.job_id}: result post failed (${errorCode(error)})`);
  }
  if (resourcePolicy && policyBefore) {
    const policyAfter = resourcePolicy.snapshot();
    const parts = COUNTER_KEYS.map(
      (key) => `${key}=${(policyAfter[key] || 0) - (policyBefore[key] || 0)}`
    );
    log(`resource_policy counters ${parts.join(" ")}`);
  }
  log(`job ${job.job_id}: ${result.status} ${result.error_code || ""}`.trim());
  return result;
}

export async function runJobLoop({
  client,
  driver,
  pack,
  packSha256 = null,
  signal = null,
  waitSeconds = NEXT_WAIT_S,
  once = false,
  resourcePolicy = null,
  heartbeatMs = JOB_HEARTBEAT_MS,
  log = () => {},
}) {
  const state = { jobs: 0 };
  const hello = () =>
    client.hello({
      proto: PROTO,
      client: CLIENT_KIND,
      pack_version: pack.pack_version,
      pack_sha256: packSha256,
      capabilities: [...CLIENT_CAPABILITIES],
    });
  await hello();
  const heartbeat = setInterval(() => {
    hello().catch(() => {});
  }, HELLO_INTERVAL_MS);
  try {
    while (!(signal && signal.aborted)) {
      let offer;
      try {
        offer = await client.nextOffer(waitSeconds, CLIENT_KIND, signal);
      } catch (error) {
        if (signal && signal.aborted) break;
        throw error;
      }
      if (signal && signal.aborted) break;
      if (!offer.job) continue;
      const job = offer.job;
      log(`offer ${job.job_id} kind=${job.kind}${job.project ? " project" : ""}`);
      await executeOffer({
        client,
        driver,
        pack,
        job,
        log,
        signal,
        resourcePolicy,
        heartbeatMs,
      });
      state.jobs += 1;
      if (once) break;
    }
  } finally {
    clearInterval(heartbeat);
  }
  return state;
}

async function modeRun(options) {
  const stateDir = options.stateDir || resolveStateDir();
  const profileDir = options.profile || join(stateDir, "chromium-profile");
  const { pack, sha256 } = loadPack();
  const client = buildClient(options);
  const driver = new ChromiumDriver({
    profileDir,
    headed: options.headed,
    stealth: options.stealth,
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
    log(
      `engine chromium, profile ${basename(profileDir)}, stealth ${
        options.stealth ? "on" : "off"
      }`
    );
    await driver.start();
    await driver.openPage();
    // HE-5a: the policy applies only to the run mode, after the page exists and
    // before the first chatgpt.com navigation; it is fail-open by design.
    if (options.resourcePolicy) {
      resourcePolicy = await applyResourcePolicy({ driver, log });
    }
    log("page open; hello and job loop");
    const state = await runJobLoop({
      client,
      driver,
      pack,
      packSha256: sha256,
      signal: controller.signal,
      waitSeconds: options.wait,
      once: options.once,
      resourcePolicy,
      log,
    });
    log(`stopped after ${state.jobs} job(s)`);
    return EXIT_OK;
  } finally {
    process.removeListener("SIGINT", onSignal);
    process.removeListener("SIGTERM", onSignal);
    if (resourcePolicy) resourcePolicy.dispose();
    await driver.stop();
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
