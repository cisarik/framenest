const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");

const APP_SOURCE = fs.readFileSync(
  path.resolve(__dirname, "../src/framenest/adapters/api/web/app.js"),
  "utf8",
);
const INDEX_SOURCE = fs.readFileSync(
  path.resolve(__dirname, "../src/framenest/adapters/api/web/index.html"),
  "utf8",
);
const STYLES_SOURCE = fs.readFileSync(
  path.resolve(__dirname, "../src/framenest/adapters/api/web/styles.css"),
  "utf8",
);

const RECOVERY_KEY = "framenest.youtube.currentClaim.v1";

function extractFunction(source, name) {
  const marker = `function ${name}(`;
  const start = source.indexOf(marker);
  assert.notEqual(start, -1, `missing production function ${name}`);
  const bodyOpen = source.indexOf("{", source.indexOf(")", start));
  let depth = 0;
  for (let index = bodyOpen; index < source.length; index += 1) {
    if (source[index] === "{") depth += 1;
    if (source[index] === "}") {
      depth -= 1;
      if (depth === 0) return source.slice(start, index + 1);
    }
  }
  throw new Error(`unterminated production function ${name}`);
}

function evaluate(source, prelude, expression) {
  const context = { console, Set, Array, String, Boolean, Object, Number };
  context.globalThis = context;
  vm.createContext(context);
  vm.runInContext(`${prelude}\n${source}\n`, context);
  return expression ? vm.runInContext(expression, context) : context;
}

test("YouTube cockpit markup is administrator-gated and accessible", () => {
  assert.match(INDEX_SOURCE, /id="youtube-claim-open-button"[^>]*hidden/);
  assert.match(INDEX_SOURCE, /id="youtube-claim-dialog"[^>]*aria-labelledby="youtube-claim-dialog-title"/);
  assert.match(INDEX_SOURCE, /id="youtube-claim-form"/);
  assert.match(INDEX_SOURCE, /id="youtube-claim-url"[^>]*type="url"/);
  assert.match(INDEX_SOURCE, /id="youtube-claim-message"[^>]*role="status"/);
  assert.match(INDEX_SOURCE, /id="youtube-claim-failure"[^>]*role="alert"/);
  assert.match(INDEX_SOURCE, /id="youtube-claim-manage-media-button"/);
  assert.match(APP_SOURCE, /capabilities\.has\("youtube\.acquire"\)/);
  assert.match(APP_SOURCE, /function identityAllowsYouTubeClaim\(\)/);
});

test("YouTube capability fails closed until exact identity resolution", () => {
  const predicate = extractFunction(APP_SOURCE, "identityAllowsYouTubeClaim");
  const context = evaluate(
    predicate,
    `let identityState = {
      resolved: false,
      available: false,
      capabilities: new Set(),
    };`,
  );
  assert.equal(vm.runInContext("identityAllowsYouTubeClaim()", context), false);
  vm.runInContext("identityState = { resolved: true, available: true, capabilities: new Set() }", context);
  assert.equal(vm.runInContext("identityAllowsYouTubeClaim()", context), false);
  vm.runInContext('identityState.capabilities.add("youtube.acquire")', context);
  assert.equal(vm.runInContext("identityAllowsYouTubeClaim()", context), true);
});

test("claim recovery stores only the opaque claim ID in session storage", () => {
  const storage = new Map();
  const context = evaluate(
    [
      "const YOUTUBE_CLAIM_RECOVERY_STORAGE_KEY = \"framenest.youtube.currentClaim.v1\";",
      "let youtubeClaimState = { claimId: \"claim-opaque-1\", message: \"\" };",
      extractFunction(APP_SOURCE, "youtubeClaimStorage"),
      extractFunction(APP_SOURCE, "saveYouTubeClaimRecovery"),
      extractFunction(APP_SOURCE, "clearYouTubeClaimRecovery"),
      extractFunction(APP_SOURCE, "loadYouTubeClaimRecovery"),
    ].join("\n"),
    "",
  );
  context.window = {
    sessionStorage: {
      setItem(key, value) {
        storage.set(key, String(value));
      },
      getItem(key) {
        return storage.has(key) ? storage.get(key) : null;
      },
      removeItem(key) {
        storage.delete(key);
      },
    },
  };
  vm.runInContext("saveYouTubeClaimRecovery()", context);
  assert.equal(storage.get(RECOVERY_KEY), "claim-opaque-1");
  assert.equal(storage.get(RECOVERY_KEY).includes("youtube.com"), false);
  assert.equal(vm.runInContext("loadYouTubeClaimRecovery()", context), "claim-opaque-1");
  vm.runInContext("clearYouTubeClaimRecovery()", context);
  assert.equal(storage.has(RECOVERY_KEY), false);
});

test("claim lifecycle uses the Phase A endpoints and interactive confirmation", () => {
  assert.match(APP_SOURCE, /const YOUTUBE_CLAIMS_ENDPOINT = "\/api\/admin\/youtube\/claims";/);
  assert.match(APP_SOURCE, /method: "POST"[\s\S]*body: JSON\.stringify\(\{ url, confirmation_method: "interactive" \}\)/);
  assert.match(APP_SOURCE, /\/retry[\s\S]*body: JSON\.stringify\(\{ confirmation_method: "interactive" \}\)/);
  assert.match(APP_SOURCE, /headers: framenestMutationHeaders\([\s\S]*"Content-Type": "application\/json"/);
  assert.match(APP_SOURCE, /function scheduleYouTubeClaimPolling\(\s*owner = youtubeClaimContext\(\),/);
  assert.match(APP_SOURCE, /const YOUTUBE_CLAIM_POLL_INTERVAL_MS = 1000;/);
  assert.match(APP_SOURCE, /const YOUTUBE_CLAIM_POLL_RETRY_MAX_MS = 10000;/);
});

test("polling stops for every terminal claim state and keeps bounded backoff", () => {
  const functions = [
    extractFunction(APP_SOURCE, "youtubeClaimStateIsTerminal"),
    extractFunction(APP_SOURCE, "youtubeClaimShouldPoll"),
  ].join("\n");
  const context = evaluate(functions, "");
  for (const state of ["failed", "cataloged", "duplicate_resolved"]) {
    assert.equal(vm.runInContext(`youtubeClaimShouldPoll({ state: "${state}" })`, context), false);
  }
  assert.equal(vm.runInContext('youtubeClaimShouldPoll({ state: "downloading" })', context), true);
  assert.match(APP_SOURCE, /Math\.min\([\s\S]*YOUTUBE_CLAIM_POLL_RETRY_MAX_MS/);
});

test("claim cockpit styles wrap on narrow screens and honor reduced motion", () => {
  assert.match(STYLES_SOURCE, /\.youtube-claim-dialog\s*\{[\s\S]*width: min\(680px/);
  assert.match(STYLES_SOURCE, /@media \(max-width: 620px\)[\s\S]*\.youtube-claim-dialog\s*\{[\s\S]*width: calc\(100% - 20px\)/);
  assert.match(STYLES_SOURCE, /@media \(prefers-reduced-motion: reduce\)/);
  assert.match(STYLES_SOURCE, /\.youtube-claim-message[\s\S]*overflow-wrap: anywhere/);
});
