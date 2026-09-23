// Operator login wizard launcher.
//
// The only mode is `login`. It starts the owned Chromium profile, serves the
// loopback login wizard, and prints the wizard URL once. Deep research,
// profile walks, arbitrary navigation, screenshots, and verification modes
// are not available. Credentials stay in the wizard process memory.

import { chmodSync, existsSync, mkdirSync, readFileSync } from "node:fs";
import { basename, resolve } from "node:path";

import { ChromiumDriver, DriverError } from "./driver.mjs";
import { LoginServer, LoginServerError } from "./login_server.mjs";

const PACK_URL = new URL("../adapters/pack_v5.json", import.meta.url);
const DEFAULT_LOGIN_URL = "https://chatgpt.com/auth/login";
const MAX_TITLE_CHARS = 200;
const LOGIN_STOP_GRACE_MS = 15000;
const EXIT_OK = 0;
const EXIT_CHECK_FAILED = 1;
const EXIT_HARD_ERROR = 2;

function usage() {
  return [
    "usage: probe.mjs login --profile <dir> [options]",
    "",
    "options:",
    "  --profile <dir>    owned Chromium profile directory (required)",
    "  --chrome-path <p>  Chromium binary",
    "  --headed           run Chromium with a visible window",
    "  --stealth          add the bounded Chromium stealth launch flags",
    "  --url <url>        login target; must be https://chatgpt.com/...",
  ].join("\n");
}

function parseArgs(argv) {
  const options = {
    mode: null,
    profile: null,
    url: null,
    stealth: false,
    chromePath: null,
    headed: false,
  };
  const rest = [...argv];
  options.mode = rest.shift() || null;
  if (options.mode !== "login") return { error: usage() };
  while (rest.length > 0) {
    const flag = rest.shift();
    if (flag === "--profile" && rest.length > 0) options.profile = rest.shift();
    else if (flag === "--url" && rest.length > 0) options.url = rest.shift();
    else if (flag === "--chrome-path" && rest.length > 0) options.chromePath = rest.shift();
    else if (flag === "--headed") options.headed = true;
    else if (flag === "--stealth") options.stealth = true;
    else return { error: `unknown argument ${flag}\n\n${usage()}` };
  }
  if (!options.profile) return { error: "--profile is required" };
  let parsedUrl;
  try {
    parsedUrl = new URL(options.url || DEFAULT_LOGIN_URL);
  } catch {
    return { error: "--url must be an absolute URL" };
  }
  if (parsedUrl.protocol !== "https:" || parsedUrl.hostname !== "chatgpt.com") {
    return { error: "--url must be an https://chatgpt.com/ URL" };
  }
  if (parsedUrl.username || parsedUrl.password || parsedUrl.search || parsedUrl.hash) {
    return { error: "--url must not carry credentials, a query, or a fragment" };
  }
  options.url = parsedUrl.toString();
  options.chromePath = options.chromePath || ChromiumDriver.defaultBinary();
  return { options };
}

function printJson(payload) {
  console.log(JSON.stringify(payload, null, 2));
}

function ensureProfileDir(profileDir) {
  mkdirSync(profileDir, { recursive: true, mode: 0o700 });
  chmodSync(profileDir, 0o700);
}

function loadPack() {
  return JSON.parse(readFileSync(PACK_URL, "utf8"));
}

function prepareStrategies(strategies) {
  return (strategies || []).map((strategy) => {
    const prepared = { kind: strategy.kind, value: strategy.value };
    if (strategy.kind === "css") prepared.selector = strategy.value;
    else if (strategy.kind === "testid") {
      prepared.selector = `[data-testid=${JSON.stringify(strategy.value)}]`;
    } else if (strategy.kind === "role") {
      prepared.selector = `[role=${JSON.stringify(strategy.value)}]`;
    }
    return prepared;
  });
}

function pageExpression(pack) {
  const locators = pack.locators || {};
  const composer = prepareStrategies(locators.composer ? locators.composer.strategies : []);
  const loginWall = prepareStrategies(locators.login_wall ? locators.login_wall.strategies : []);
  return `(() => {
  const composerStrategies = ${JSON.stringify(composer)};
  const loginWallStrategies = ${JSON.stringify(loginWall)};
  const visible = (element) => !!element && element.getClientRects().length > 0;
  const findElement = (strategy) => {
    if (strategy.selector !== undefined) return document.querySelector(strategy.selector);
    return null;
  };
  const matchStrategies = (strategies, useUrlPath) => {
    for (const strategy of strategies) {
      if (strategy.kind === "url_path") {
        if (useUrlPath && location.pathname.startsWith(strategy.value)) {
          return "url_path:" + strategy.value;
        }
        continue;
      }
      if (visible(findElement(strategy))) return strategy.kind + ":" + strategy.value;
    }
    return null;
  };
  const composerMatch = matchStrategies(composerStrategies, false);
  const loginMatch = matchStrategies(loginWallStrategies, true);
  return {
    final_url_path: location.pathname,
    title: document.title,
    composer: { present: composerMatch !== null, strategy: composerMatch },
    login_wall: { present: loginMatch !== null, strategy: loginMatch },
  };
})()`;
}

function boundedTitle(title) {
  const text = String(title === undefined || title === null ? "" : title);
  return text.length > MAX_TITLE_CHARS ? text.slice(0, MAX_TITLE_CHARS) : text;
}

async function collectPageMetrics(driver, pack) {
  const metrics = await driver.evaluate(pageExpression(pack));
  return {
    final_url_path: String(metrics.final_url_path || ""),
    title: boundedTitle(metrics.title),
    composer: metrics.composer,
    login_wall: metrics.login_wall,
  };
}

function newDriver(options, profileDir) {
  if (!options.chromePath || !existsSync(options.chromePath)) {
    throw new DriverError(
      "E_PROBE_CHROME_MISSING",
      `no Chromium binary found: ${options.chromePath || "none of the default candidates"}`
    );
  }
  return new ChromiumDriver({
    chromePath: options.chromePath,
    profileDir,
    headed: options.headed,
    stealth: options.stealth,
  });
}

async function loginProbe(options) {
  const profileDir = resolve(options.profile);
  ensureProfileDir(profileDir);
  const pack = loadPack();
  const target = new URL(options.url);
  const driver = newDriver(options, profileDir);
  driver.stopGraceMs = LOGIN_STOP_GRACE_MS;
  const server = new LoginServer({
    engine: {
      loginState: () => driver.loginState(),
      fill: (field, value) => driver.fillField(field, value),
      clickTarget: (targetName) => driver.clickTarget(targetName),
      clickXY: (x, y) => driver.clickXY(x, y),
      snapshot: (region) => driver.snapshotPng(region),
    },
  });
  const startedAt = Date.now();
  const result = {
    ok: false,
    mode: "login",
    stealth: options.stealth,
    url_host: target.host,
    engine: "chromium",
    engine_binary: basename(options.chromePath),
    profile_path_name: basename(profileDir),
    listener: null,
    login_port: null,
    duration_seconds: 0,
    exit_reason: null,
    url_path: null,
    title: null,
    composer: null,
    login_wall: null,
  };
  const onSignal = (signal) =>
    server.requestClose(signal === "SIGINT" ? "interrupt" : signal.toLowerCase());
  process.once("SIGINT", onSignal);
  process.once("SIGTERM", onSignal);
  process.once("SIGHUP", onSignal);
  try {
    await driver.start();
    result.listener = driver.listener;
    await driver.openPage();
    await driver.navigate(options.url);
    await server.start();
    result.login_port = server.port;
    console.log(server.url);
    const outcome = await server.waitForDone();
    result.exit_reason = outcome.reason;
    if (server.fatalError) throw server.fatalError;
    const metrics = await collectPageMetrics(driver, pack);
    result.url_path = metrics.final_url_path;
    result.title = metrics.title;
    result.composer = metrics.composer;
    result.login_wall = metrics.login_wall;
  } finally {
    process.removeListener("SIGINT", onSignal);
    process.removeListener("SIGTERM", onSignal);
    process.removeListener("SIGHUP", onSignal);
    await server.close("shutdown").catch(() => {});
    await driver.stop();
  }
  result.duration_seconds = Math.round((Date.now() - startedAt) / 1000);
  result.ok = result.url_path !== null;
  printJson(result);
  return result.ok ? EXIT_OK : EXIT_CHECK_FAILED;
}

async function main(argv) {
  const parsed = parseArgs(argv);
  if (parsed.error) {
    console.error(`error: [E_PROBE_USAGE] ${parsed.error}`);
    printJson({ ok: false, error: { code: "E_PROBE_USAGE", message: parsed.error } });
    return EXIT_HARD_ERROR;
  }
  try {
    return await loginProbe(parsed.options);
  } catch (error) {
    const code =
      error instanceof DriverError || error instanceof LoginServerError
        ? error.code
        : "E_PROBE_INTERNAL";
    const message = String(error && error.message ? error.message : error);
    console.error(`error: [${code}] ${message}`);
    printJson({ ok: false, mode: "login", error: { code, message } });
    return EXIT_HARD_ERROR;
  }
}

process.exitCode = await main(process.argv.slice(2));
