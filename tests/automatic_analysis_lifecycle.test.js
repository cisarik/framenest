const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");

const APP_PATH = path.resolve(__dirname, "../src/framenest/adapters/api/web/app.js");
const INDEX_PATH = path.resolve(__dirname, "../src/framenest/adapters/api/web/index.html");
const APP_SOURCE = fs.readFileSync(APP_PATH, "utf8");
const INDEX_SOURCE = fs.readFileSync(INDEX_PATH, "utf8");

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

function extractAsyncFunction(name) {
  const marker = `async function ${name}(`;
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
  assert.match(analyzed, /Saved AI suggestion ready for review/i);
  assert.match(failed, /unavailable|failed/i);
  assert.doesNotMatch(pending, /ready for review/i);
  assert.doesNotMatch(analyzing, /ready for review/i);
  assert.doesNotMatch(failed, /ready for review/i);
  assert.doesNotMatch(analyzed, /AI analysis ready for review/i);
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

test("metadata editor exposes durable Load AI suggestion without Apply endpoint", () => {
  assert.match(INDEX_SOURCE, /id="metadata-load-ai-suggestion-button"/);
  assert.match(INDEX_SOURCE, />Load AI suggestion</);
  assert.match(INDEX_SOURCE, /id="metadata-durable-ai-suggestion"/);
  assert.match(APP_SOURCE, /async function handleLoadDurableAiSuggestion/);
  assert.match(APP_SOURCE, /async function refreshMetadataDurableAnalysis/);
  assert.match(APP_SOURCE, /function aiSuggestionFromAutomaticAnalysisResult/);
  assert.match(APP_SOURCE, /automaticAnalysisEndpoint\(mediaId\)/);
  assert.equal(APP_SOURCE.includes("/apply"), false);
  assert.equal(APP_SOURCE.includes("handleApplyDurable"), false);
});

test("durable suggestion mapping keeps only title description tags and display filename", () => {
  const context = {};
  vm.runInNewContext(extractFunction("aiSuggestionFromAutomaticAnalysisResult"), context);
  const mapped = context.aiSuggestionFromAutomaticAnalysisResult({
    title: "Durable title",
    description: "Durable description",
    collection: "Must not map",
    tags: ["alpha", "beta"],
    suggested_filename: "durable.mp4",
    confidence: 0.9,
    evidence: ["frame"],
    uncertainties: ["maybe"],
  });
  assert.equal(mapped.title, "Durable title");
  assert.equal(mapped.description, "Durable description");
  assert.deepEqual([...mapped.tags], ["alpha", "beta"]);
  assert.equal(mapped.suggestedFilename, "durable.mp4");
  assert.equal("collection" in mapped, false);
  assert.equal(context.aiSuggestionFromAutomaticAnalysisResult(null), null);
  assert.equal(context.aiSuggestionFromAutomaticAnalysisResult({ title: "x" }), null);
});

test("durable load path reads automatic-analysis and never calls interactive Analyze", () => {
  const loadBody = extractAsyncFunction("handleLoadDurableAiSuggestion");
  assert.match(loadBody, /automaticAnalysisEndpoint\(mediaId\)/);
  assert.match(loadBody, /headers: \{ Accept: "application\/json" \}/);
  assert.equal(loadBody.includes("method:"), false);
  assert.equal(loadBody.includes("ai-suggestion-preview"), false);
  assert.equal(loadBody.includes("confirm_cloud_upload"), false);
  assert.equal(loadBody.includes("mediaAiSuggestionEndpoint"), false);
  assert.equal(loadBody.includes("handleAnalyzeMetadataByAi"), false);
  assert.match(loadBody, /applyResolvedAiSuggestionToMetadataWorkspace\(suggestion, tagKeys\)/);
  assert.equal(loadBody.includes("handleSaveMetadata"), false);
  assert.equal(loadBody.includes("metadataEndpoint("), false);
  assert.match(loadBody, /Replace current draft\?/);
  assert.match(loadBody, /Keep editing/);
  assert.match(loadBody, /Replace draft/);
  assert.match(loadBody, /destructive: false/);
  assert.match(loadBody, /requestConfirmation\(/);
  assert.equal(loadBody.includes("window.confirm"), false);
  assert.equal(/confirmLabel:\s*"Load suggestion"/.test(loadBody), false);
  assert.equal(/destructive:\s*true/.test(loadBody), false);
});

test("durable load reuses existing apply helper and excludes collection mutation", () => {
  const applyBody = extractFunction("applyResolvedAiSuggestionToMetadataWorkspace");
  assert.match(applyBody, /metadataWorkspace\.current\.displayTitle = suggestion\.title/);
  assert.match(applyBody, /metadataWorkspace\.current\.description = suggestion\.description/);
  assert.match(applyBody, /metadataWorkspace\.current\.tagKeys = tagKeys/);
  assert.match(applyBody, /metadataWorkspace\.suggestedFilename = suggestion\.suggestedFilename/);
  assert.equal(applyBody.includes("collectionKey"), false);
  assert.equal(applyBody.includes("collection"), false);
  assert.match(applyBody, /Review the updated fields, then Save\./);
});

test("saved suggestion terminology avoids Durable label and contradictory provider-unavailable copy", () => {
  assert.match(INDEX_SOURCE, />Saved AI suggestion</);
  assert.equal(INDEX_SOURCE.includes("Durable AI suggestion"), false);
  assert.match(APP_SOURCE, /Saved AI suggestion ready for review\./);
  assert.equal(APP_SOURCE.includes("AI analysis ready for review."), false);
  const panelBody = extractFunction("renderMetadataAiPanel");
  assert.match(
    panelBody,
    /A previously generated suggestion is ready to review\. New AI analysis is currently unavailable\./,
  );
  assert.match(panelBody, /durableAnalysisLoadAvailable\(\)/);
});

test("suggested filename is display-only in metadata HTML and AI panel render", () => {
  assert.match(INDEX_SOURCE, /id="metadata-ai-filename-display"/);
  assert.equal(INDEX_SOURCE.includes("metadata-ai-filename-input"), false);
  const aiSuggestionBlock = INDEX_SOURCE.slice(
    INDEX_SOURCE.indexOf('id="metadata-ai-suggestion"'),
    INDEX_SOURCE.indexOf('id="metadata-save-button"'),
  );
  assert.equal(aiSuggestionBlock.includes("<input"), false);
  const panelBody = extractFunction("renderMetadataAiPanel");
  assert.match(panelBody, /metadataAiFilenameDisplay\.textContent/);
  assert.equal(panelBody.includes("metadataAiFilenameInput"), false);
  assert.equal(APP_SOURCE.includes("metadataAiFilenameInput.addEventListener"), false);
});
