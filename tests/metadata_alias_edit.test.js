const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");

const APP_PATH = path.resolve(__dirname, "../src/framenest/adapters/api/web/app.js");
const INDEX_PATH = path.resolve(__dirname, "../src/framenest/adapters/api/web/index.html");
const APP_SOURCE = fs.readFileSync(APP_PATH, "utf8");
const INDEX_SOURCE = fs.readFileSync(INDEX_PATH, "utf8");

function extractFunction(name) {
  const markers = [`async function ${name}(`, `function ${name}(`];
  let start = -1;
  for (const marker of markers) {
    start = APP_SOURCE.indexOf(marker);
    if (start !== -1) break;
  }
  assert.notEqual(start, -1, `missing ${name}`);
  const headerOpen = APP_SOURCE.indexOf("(", start);
  assert.notEqual(headerOpen, -1, `missing parameter list for ${name}`);
  let depth = 0;
  let headerClose = -1;
  for (let index = headerOpen; index < APP_SOURCE.length; index += 1) {
    const character = APP_SOURCE[index];
    if (character === "(") depth += 1;
    else if (character === ")") {
      depth -= 1;
      if (depth === 0) {
        headerClose = index;
        break;
      }
    }
  }
  assert.notEqual(headerClose, -1, `unterminated parameter list for ${name}`);
  const bodyOpen = APP_SOURCE.indexOf("{", headerClose);
  assert.notEqual(bodyOpen, -1, `missing body for ${name}`);
  depth = 0;
  for (let index = bodyOpen; index < APP_SOURCE.length; index += 1) {
    const character = APP_SOURCE[index];
    if (character === "{") depth += 1;
    else if (character === "}") {
      depth -= 1;
      if (depth === 0) return APP_SOURCE.slice(start, index + 1);
    }
  }
  assert.fail(`unterminated ${name}`);
}

test("ordinary Edit is gated by alias or canonical write in a workspace audience", () => {
  const editBody = extractFunction("identityAllowsMetadataEdit");
  assert.match(editBody, /isWorkspaceAudience\(\)/);
  assert.match(editBody, /metadata\.alias\.write/);
  assert.match(editBody, /metadata\.canonical\.write/);
  const detailsBody = extractFunction("applyIdentityCapabilities");
  assert.match(detailsBody, /identityAllowsMetadataEdit\(\)/);
  const cardBody = extractFunction("renderCatalogCard");
  assert.match(cardBody, /identityAllowsMetadataEdit\(\)/);
});

test("ordinary load seeds Current from a non-empty alias overlay", () => {
  const openBody = extractFunction("handleOpenMetadataWorkspace");
  assert.match(openBody, /mediaAliasEndpoint\(mediaId\)/);
  assert.match(openBody, /aliasOverlayIsNonEmpty\(aliasPayload\)/);
  assert.match(openBody, /applyAliasOverlayToWorkspace\(aliasPayload\)/);
  assert.match(openBody, /editMode: identityUsesCanonicalMetadataWrite\(\) \? "canonical" : "alias"/);
  assert.match(openBody, /previewSuggestion/);
  assert.match(openBody, /presentPreviewSuggestionInMetadataWorkspace/);
  assert.equal(openBody.includes("applyResolvedAiSuggestionToMetadataWorkspace"), false);
  const overlayBody = extractFunction("aliasOverlayIsNonEmpty");
  assert.match(overlayBody, /display_title/);
  assert.match(overlayBody, /description/);
  assert.match(overlayBody, /tag_keys/);
});

test("ordinary Save uses alias PUT only and never companion apply", () => {
  const saveBody = extractFunction("handleSaveMetadata");
  assert.match(saveBody, /mediaAliasEndpoint\(saveOwner\.mediaId\)/);
  assert.match(saveBody, /saveOwner\.editMode === "alias"/);
  assert.equal(saveBody.includes("/apply"), false);
  const claimBody = extractFunction("claimMetadataSaveOwner");
  assert.match(claimBody, /display_title: normalized.displayTitle/);
  assert.match(claimBody, /tag_keys: normalized.tagKeys/);
  assert.match(claimBody, /editMode: aliasMode \? "alias" : "canonical"/);
  assert.equal(APP_SOURCE.includes("/apply"), false);
});

test("ordinary alias Edit hides classification chrome and canonical tag create", () => {
  const createBody = extractFunction("createAndSelectMetadataTag");
  assert.match(createBody, /identityUsesCanonicalMetadataWrite\(\)/);
  const classification = extractFunction("syncClassificationControlsFromWorkspace");
  assert.match(classification, /classificationRow\.hidden = true/);
  assert.doesNotMatch(classification, /classificationRow\.hidden = aliasMode/);
  const loadChrome = extractFunction("identityAllowsAiSuggestionLoadChrome");
  assert.match(loadChrome, /metadata\.alias\.write/);
  assert.match(loadChrome, /metadata\.canonical\.write/);
  assert.doesNotMatch(loadChrome, /companionWebHosted\(\)/);
  assert.doesNotMatch(loadChrome, /media\.workflow\.read/);
  const analyze = extractFunction("identityAllowsAiAnalyze");
  assert.match(analyze, /analysis\.run/);
  assert.match(analyze, /companionWebHosted\(\)/);
  assert.match(analyze, /metadataWorkspaceIsAliasMode\(\)/);
});

test("per-field copy does not persist and Load does not bulk-apply", () => {
  const copyBody = extractFunction("copySuggestionFieldToCurrent");
  assert.equal(copyBody.includes("fetch("), false);
  assert.equal(copyBody.includes("handleSaveMetadata"), false);
  assert.equal(copyBody.includes("method:"), false);
  const loadBody = extractFunction("handleLoadDurableAiSuggestion");
  assert.equal(loadBody.includes("applyResolvedAiSuggestionToMetadataWorkspace"), false);
  assert.equal(loadBody.includes("requestConfirmation("), false);
  assert.match(INDEX_SOURCE, /id="metadata-ai-title-strip"/);
  assert.match(INDEX_SOURCE, />Load</);
});

test("Load chrome is available in alias mode and hosted companion web", () => {
  const loadChrome = extractFunction("identityAllowsAiSuggestionLoadChrome");
  assert.match(loadChrome, /isWorkspaceAudience\(\)/);
  assert.doesNotMatch(loadChrome, /metadataWorkspaceIsAliasMode\(\)/);
  assert.doesNotMatch(loadChrome, /companionWebHosted\(\)/);
  const panel = extractFunction("renderMetadataAiPanel");
  assert.match(panel, /identityAllowsAiSuggestionLoadChrome\(\)/);
  const controls = extractFunction("updateMetadataControls");
  assert.match(controls, /identityAllowsAiSuggestionLoadChrome\(\)/);
  assert.match(controls, /identityAllowsAiAnalyze\(\)/);
});

test("mapped suggested tags are buttons and unmapped tags are not", () => {
  const strips = extractFunction("renderMetadataSuggestionStrips");
  assert.match(strips, /metadata-suggestion-tag--mapped/);
  assert.match(strips, /copySuggestionFieldToCurrent\("tag", tag\.key\)/);
  assert.match(strips, /metadata-suggestion-tag--unmapped/);
  assert.match(strips, /document\.createElement\("button"\)/);
});
