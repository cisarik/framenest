const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");

const APP_PATH = path.resolve(__dirname, "../src/framenest/adapters/api/web/app.js");
const APP_SOURCE = fs.readFileSync(APP_PATH, "utf8");

function extractFunction(name) {
  const marker = `function ${name}(`;
  const start = APP_SOURCE.indexOf(marker);
  assert.notEqual(start, -1, `missing ${name}`);
  let depth = 0;
  let started = false;
  for (let index = start; index < APP_SOURCE.length; index += 1) {
    const char = APP_SOURCE[index];
    if (char === "{") {
      depth += 1;
      started = true;
    } else if (char === "}") {
      depth -= 1;
      if (started && depth === 0) {
        return APP_SOURCE.slice(start, index + 1);
      }
    }
  }
  assert.fail(`unterminated ${name}`);
}

test("pending and analyzing never appear as success messages", () => {
  const context = {};
  vm.runInNewContext(extractFunction("automaticAnalysisStatusMessage"), context);
  const pending = context.automaticAnalysisStatusMessage({ state: "pending" });
  const analyzing = context.automaticAnalysisStatusMessage({ state: "analyzing" });
  const analyzed = context.automaticAnalysisStatusMessage({ state: "analyzed" });
  const failed = context.automaticAnalysisStatusMessage({
    state: "failed",
    error_message: "AI provider is temporarily unavailable.",
  });
  assert.match(pending, /queued/i);
  assert.match(analyzing, /progress/i);
  assert.match(analyzed, /ready/i);
  assert.match(failed, /unavailable|failed/i);
  assert.doesNotMatch(pending, /ready for review/i);
  assert.doesNotMatch(analyzing, /ready for review/i);
  assert.doesNotMatch(failed, /ready for review/i);
});

test("automatic analysis polling stops at terminal states and avoids interval loops", () => {
  assert.ok(APP_SOURCE.includes("AUTOMATIC_ANALYSIS_TERMINAL_STATES"));
  assert.ok(APP_SOURCE.includes('new Set(["analyzed", "failed", "not_requested"])'));
  assert.ok(APP_SOURCE.includes("stopAutomaticAnalysisPolling(mediaId)"));
  assert.ok(APP_SOURCE.includes("if (AUTOMATIC_ANALYSIS_TERMINAL_STATES.has(payload.state))"));
  assert.ok(APP_SOURCE.includes("maybeTrackAutomaticAnalysisAfterCatalog(snapshot)"));
  assert.equal(APP_SOURCE.includes("setInterval(pollAutomaticAnalysis"), false);
});

test("cataloged upload copy mentions automatic analysis only when enabled", () => {
  const catalogedBranch = APP_SOURCE.slice(
    APP_SOURCE.indexOf('if (snapshot.state === "cataloged") {'),
    APP_SOURCE.indexOf('if (snapshot.state === "received") {'),
  );
  assert.match(catalogedBranch, /Automatic AI analysis may follow/);
  assert.match(catalogedBranch, /automaticAnalysisCapability\.automatic_analysis_enabled/);
});
