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
const CREATE_CONFIRMATION_MESSAGE = "FrameNest will start the acquisition in the background. Closing the cockpit will not cancel it. Acquired media remains unpublished until it is reviewed and published in Manage media.";

function extractFunction(source, name) {
  const markers = [`async function ${name}(`, `function ${name}(`];
  let start = -1;
  for (const marker of markers) {
    start = source.indexOf(marker);
    if (start !== -1) break;
  }
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

function extractMarkupElementById(source, id) {
  const escapedId = id.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const pattern = new RegExp(
    `<([a-z][a-z0-9-]*)\\b([^>]*\\bid="${escapedId}"[^>]*)>([\\s\\S]*?)<\\/\\1>`,
    "i",
  );
  const match = source.match(pattern);
  assert.ok(match, `missing markup element ${id}`);
  return {
    tagName: match[1].toLowerCase(),
    attributes: match[2],
    content: match[3],
    markup: match[0],
  };
}

function markupAttribute(attributes, name) {
  const escapedName = name.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const match = attributes.match(new RegExp(`(?:^|\\s)${escapedName}="([^"]*)"`, "i"));
  return match ? match[1] : null;
}

function createClaimElement(tagName = "div") {
  const attributes = new Map();
  const listeners = new Map();
  return {
    tagName: String(tagName).toUpperCase(),
    attributes,
    listeners,
    dataset: {},
    hidden: false,
    disabled: false,
    textContent: "",
    value: "",
    valid: true,
    focusCount: 0,
    setAttribute(name, value) {
      attributes.set(String(name).toLowerCase(), String(value));
    },
    getAttribute(name) {
      const key = String(name).toLowerCase();
      return attributes.has(key) ? attributes.get(key) : null;
    },
    removeAttribute(name) {
      attributes.delete(String(name).toLowerCase());
    },
    addEventListener(type, listener) {
      if (!listeners.has(type)) listeners.set(type, []);
      listeners.get(type).push(listener);
    },
    dispatchEvent(event) {
      event.target = event.target || this;
      event.currentTarget = this;
      event.defaultPrevented = false;
      event.preventDefault = () => {
        event.defaultPrevented = true;
      };
      for (const listener of [...(listeners.get(event.type) || [])]) listener(event);
      return !event.defaultPrevented;
    },
    checkValidity() {
      return this.valid;
    },
    focus() {
      this.focusCount += 1;
    },
  };
}

function createYouTubeAccessibilityHarness({ confirmationAccepted = true } = {}) {
  const youtubeClaimUrlInput = createClaimElement("input");
  const youtubeClaimUrlError = createClaimElement("p");
  youtubeClaimUrlError.hidden = true;
  const elements = {
    youtubeClaimForm: createClaimElement("form"),
    youtubeClaimUrlInput,
    youtubeClaimUrlError,
    youtubeClaimRow: createClaimElement("section"),
    youtubeClaimStateLabel: createClaimElement("h3"),
    youtubeClaimMessage: createClaimElement("p"),
    youtubeClaimDetails: createClaimElement("div"),
    youtubeClaimMetadata: createClaimElement("p"),
    youtubeClaimPublication: createClaimElement("p"),
    youtubeClaimFailure: createClaimElement("p"),
    youtubeClaimSubmitButton: createClaimElement("button"),
    youtubeClaimRetryButton: createClaimElement("button"),
    youtubeClaimResetButton: createClaimElement("button"),
    youtubeClaimManageMediaButton: createClaimElement("button"),
    youtubeClaimDialogTitle: createClaimElement("h2"),
  };
  const state = {
    generation: 0,
    claimId: null,
    snapshot: null,
    requestOwner: null,
    pollOwner: null,
    pollTimer: null,
    pollRetryDelayMs: 1000,
    submitting: false,
    retrying: false,
    recoveryAttempted: false,
    submissionResult: null,
    message: "",
    errorMessage: "",
    urlError: "",
  };
  const fetchCalls = [];
  const confirmationRequests = [];
  const context = {
    console,
    Set,
    Array,
    String,
    Boolean,
    Object,
    Number,
    Math,
    Promise,
    encodeURIComponent,
    clearTimeout,
    setTimeout,
    youtubeClaimState: state,
    YOUTUBE_CLAIMS_ENDPOINT: "/api/admin/youtube/claims",
    identityAllowsAdminWorkflow: () => true,
    identityAllowsYouTubeClaim: () => true,
    framenestMutationHeaders: (headers) => Object.assign({ "X-FrameNest-Request": "1" }, headers),
    saveYouTubeClaimRecovery() {},
    stopYouTubeClaimPolling() {
      state.pollOwner = null;
      state.pollTimer = null;
    },
    scheduleYouTubeClaimPolling() {},
    requestConfirmation: async (options) => {
      context.confirmationCalls += 1;
      confirmationRequests.push(options);
      return confirmationAccepted;
    },
    confirmationCalls: 0,
    fetch: async (url, options) => {
      fetchCalls.push({ url: String(url), options });
      return {
        ok: true,
        status: 201,
        json: async () => ({
          claim_id: "claim-accepted-1",
          state: "cataloged",
          phase: "cataloged",
          catalog_state: "cataloged",
          metadata_state: "unknown",
          publication_state: "unpublished",
        }),
      };
    },
    ...elements,
  };
  context.claimYouTubeRequest = (kind) => {
    if (state.requestOwner) return null;
    state.generation += 1;
    const owner = { generation: state.generation, claimId: state.claimId, kind };
    state.requestOwner = owner;
    return owner;
  };
  context.releaseYouTubeRequest = (owner) => {
    if (state.requestOwner !== owner) return false;
    state.requestOwner = null;
    return true;
  };
  context.youtubeClaimContextStillCurrent = (owner) => Boolean(
    owner
      && state.generation === owner.generation
      && (!owner.claimId || state.claimId === owner.claimId),
  );
  context.youtubeClaimContext = (claimId = state.claimId) => ({
    generation: state.generation,
    claimId: claimId || null,
  });

  const functions = [
    extractFunction(APP_SOURCE, "youtubeClaimStateIsTerminal"),
    extractFunction(APP_SOURCE, "youtubeClaimShouldPoll"),
    extractFunction(APP_SOURCE, "normalizeYouTubeClaimSnapshot"),
    extractFunction(APP_SOURCE, "youtubeClaimPhaseLabel"),
    extractFunction(APP_SOURCE, "youtubeClaimStatusMessage"),
    extractFunction(APP_SOURCE, "youtubeClaimMetadataLabel"),
    extractFunction(APP_SOURCE, "youtubeClaimPublicationLabel"),
    extractFunction(APP_SOURCE, "renderYouTubeClaimCockpit"),
    extractFunction(APP_SOURCE, "applyYouTubeClaimSnapshot"),
    extractFunction(APP_SOURCE, "submitYouTubeClaim"),
  ].join("\n");
  context.globalThis = context;
  vm.createContext(context);
  vm.runInContext(functions, context);
  const eventWiringStart = APP_SOURCE.lastIndexOf("if (youtubeClaimForm) {");
  const eventWiringEnd = APP_SOURCE.indexOf("if (youtubeClaimRetryButton) {", eventWiringStart);
  assert.ok(eventWiringStart >= 0);
  assert.ok(eventWiringEnd > eventWiringStart);
  vm.runInContext(APP_SOURCE.slice(eventWiringStart, eventWiringEnd), context);
  context.renderYouTubeClaimCockpit = vm.runInContext("renderYouTubeClaimCockpit", context);
  context.submitYouTubeClaim = vm.runInContext("submitYouTubeClaim", context);
  context.renderYouTubeClaimCockpit();
  return { context, elements, state, fetchCalls, confirmationRequests };
}

test("YouTube cockpit opener has exact visible and accessible identity", () => {
  const opener = extractMarkupElementById(INDEX_SOURCE, "youtube-claim-open-button");
  assert.equal(opener.tagName, "button");
  assert.equal(markupAttribute(opener.attributes, "type"), "button");
  assert.equal(markupAttribute(opener.attributes, "aria-label"), "Acquire YouTube media");
  assert.match(opener.attributes, /(?:^|\s)hidden(?:\s|$)/);
  assert.doesNotMatch(opener.attributes, /(?:^|\s)disabled(?:\s|$|=)/);
  assert.doesNotMatch(opener.attributes, /(?:^|\s)tabindex="-1"/);
  assert.doesNotMatch(opener.content, /<[^>]+>/);
  assert.equal(opener.content.trim().replace(/\s+/g, " "), "YouTube");
  assert.doesNotMatch(opener.markup, /Claim YouTube/);
  assert.match(
    APP_SOURCE,
    /youtubeClaimOpenButton\.addEventListener\("click", openYouTubeClaimDialog\)/,
  );
});

test("YouTube cockpit markup is administrator-gated and accessible", () => {
  assert.match(INDEX_SOURCE, /id="youtube-claim-open-button"[^>]*hidden/);
  assert.match(INDEX_SOURCE, /id="youtube-claim-dialog"[^>]*aria-labelledby="youtube-claim-dialog-title"/);
  assert.match(INDEX_SOURCE, /id="youtube-claim-form"/);
  assert.match(INDEX_SOURCE, /id="youtube-claim-url"[^>]*type="url"/);
  assert.match(INDEX_SOURCE, /id="youtube-claim-url-error"[^>]*role="alert"[^>]*hidden/);
  assert.match(INDEX_SOURCE, /id="youtube-claim-message"[^>]*role="status"/);
  assert.match(INDEX_SOURCE, /id="youtube-claim-failure"[^>]*role="alert"/);
  assert.match(INDEX_SOURCE, /id="youtube-claim-manage-media-button"/);
  assert.match(APP_SOURCE, /capabilities\.has\("youtube\.acquire"\)/);
  assert.match(APP_SOURCE, /function identityAllowsYouTubeClaim\(\)/);
  assert.match(APP_SOURCE, /aria-invalid/);
  assert.match(APP_SOURCE, /youtube-claim-url-note youtube-claim-url-error/);

  const harness = createYouTubeAccessibilityHarness();
  const { context, elements, state, fetchCalls, confirmationRequests } = harness;
  const input = elements.youtubeClaimUrlInput;
  const error = elements.youtubeClaimUrlError;
  assert.equal(input.getAttribute("aria-invalid"), "false");
  assert.equal(input.getAttribute("aria-describedby"), "youtube-claim-url-note");
  assert.equal(error.hidden, true);

  input.value = "https://www.youtube.com/watch?v=private-test-value";
  input.valid = false;
  const invalidEvent = { type: "invalid" };
  input.dispatchEvent(invalidEvent);
  assert.equal(invalidEvent.defaultPrevented, true);
  assert.equal(input.getAttribute("aria-invalid"), "true");
  assert.equal(
    input.getAttribute("aria-describedby"),
    "youtube-claim-url-note youtube-claim-url-error",
  );
  assert.equal(error.hidden, false);
  assert.equal(error.textContent, "Enter a valid YouTube URL before submitting the claim.");
  assert.equal(error.textContent.includes(input.value), false);

  input.valid = true;
  input.dispatchEvent({ type: "input" });
  assert.equal(input.getAttribute("aria-invalid"), "false");
  assert.equal(input.getAttribute("aria-describedby"), "youtube-claim-url-note");
  assert.equal(error.hidden, true);

  input.value = "not a URL";
  input.valid = false;
  const pointerSubmit = { type: "submit" };
  elements.youtubeClaimForm.dispatchEvent(pointerSubmit);
  assert.equal(pointerSubmit.defaultPrevented, true);
  assert.equal(context.confirmationCalls, 0);
  assert.equal(fetchCalls.length, 0);
  assert.equal(input.getAttribute("aria-invalid"), "true");

  const keyboardSubmit = { type: "submit", submitter: elements.youtubeClaimSubmitButton };
  elements.youtubeClaimForm.dispatchEvent(keyboardSubmit);
  assert.equal(keyboardSubmit.defaultPrevented, true);
  assert.equal(context.confirmationCalls, 0);
  assert.equal(fetchCalls.length, 0);

  const submittedUrl = "https://www.youtube.com/watch?v=accepted-test-value";
  input.value = submittedUrl;
  input.valid = true;
  return context.submitYouTubeClaim().then(() => {
    assert.equal(confirmationRequests.length, 1);
    assert.equal(confirmationRequests[0].message, CREATE_CONFIRMATION_MESSAGE);
    assert.match(confirmationRequests[0].message, /acquisition in the background/);
    assert.match(confirmationRequests[0].message, /Closing the cockpit will not cancel it/);
    assert.match(confirmationRequests[0].message, /media remains unpublished/);
    assert.match(confirmationRequests[0].message, /reviewed and published in Manage media/);
    assert.equal(confirmationRequests[0].message.includes(submittedUrl), false);
    assert.equal(confirmationRequests[0].focusReturn, elements.youtubeClaimSubmitButton);
    assert.equal(fetchCalls.length, 1);
    assert.deepEqual(
      JSON.parse(fetchCalls[0].options.body),
      { url: "https://www.youtube.com/watch?v=accepted-test-value", confirmation_method: "interactive" },
    );
    assert.equal(input.value, "");
    assert.equal(state.urlError, "");
    assert.equal(input.getAttribute("aria-invalid"), "false");
    assert.equal(input.getAttribute("aria-describedby"), "youtube-claim-url-note");
    assert.equal(error.hidden, true);
    context.renderYouTubeClaimCockpit();
    assert.equal(input.value, "");
  });
});

test("cancelling create confirmation preserves URL privacy and sends no request", async () => {
  const { context, elements, fetchCalls, confirmationRequests } = createYouTubeAccessibilityHarness({
    confirmationAccepted: false,
  });
  const submittedUrl = "https://www.youtube.com/watch?v=private-cancelled-value";
  elements.youtubeClaimUrlInput.value = submittedUrl;
  elements.youtubeClaimUrlInput.valid = true;

  await context.submitYouTubeClaim();

  assert.equal(confirmationRequests.length, 1);
  assert.equal(confirmationRequests[0].message, CREATE_CONFIRMATION_MESSAGE);
  assert.equal(confirmationRequests[0].message.includes(submittedUrl), false);
  assert.doesNotMatch(confirmationRequests[0].message, /https?:\/\//);
  assert.doesNotMatch(confirmationRequests[0].message, /video ID|claim ID|media ID|metadata|AI analysis/i);
  assert.equal(fetchCalls.length, 0);
});

test("terminal claim copy distinguishes duplicate reuse and unpublished catalog media", () => {
  const statusMessage = extractFunction(APP_SOURCE, "youtubeClaimStatusMessage");
  const context = evaluate(
    statusMessage,
    "let youtubeClaimState = { message: \"\" };",
  );
  assert.match(
    vm.runInContext(
      'youtubeClaimStatusMessage({ state: "duplicate_resolved" })',
      context,
    ),
    /No new download was required.*no second catalog item was created/,
  );
  assert.match(
    vm.runInContext(
      'youtubeClaimStatusMessage({ state: "duplicate_resolved", submission_result: "terminal_duplicate_reuse" })',
      context,
    ),
    /No new download was required.*no second catalog item was created/,
  );
  assert.match(
    vm.runInContext(
      'youtubeClaimStatusMessage({ state: "cataloged", publication_state: "unpublished" })',
      context,
    ),
    /not visible to ordinary Gallery users.*published in Manage media/,
  );
  assert.match(
    vm.runInContext(
      'youtubeClaimStatusMessage({ state: "cataloged", publication_state: "published" })',
      context,
    ),
    /available in Gallery/,
  );
});

test("YouTube capability fails closed until exact identity resolution", () => {
  const functions = [
    extractFunction(APP_SOURCE, "identityAllowsYouTubeClaim"),
    extractFunction(APP_SOURCE, "applyIdentityCapabilities"),
  ].join("\n");
  const context = evaluate(
    functions,
    `let identityState = {
      resolved: false,
      available: false,
      capabilities: new Set(),
    };
    const uploadOpenButton = null;
    const detailsEditButton = null;
    const adminMediaOpenButton = null;
    const youtubeClaimOpenButton = { hidden: false };
    const youtubeClaimDialog = null;
    const adminMediaBrowser = null;
    function identityHasCapability() { return false; }
    function identityAllowsAdminWorkflow() { return false; }
    function closeYouTubeClaimDialog() {}
    function closeAdminMediaBrowser() {}
    function updateMetadataControls() {}`,
  );
  assert.equal(vm.runInContext("identityAllowsYouTubeClaim()", context), false);
  vm.runInContext("applyIdentityCapabilities()", context);
  assert.equal(vm.runInContext("youtubeClaimOpenButton.hidden", context), true);
  vm.runInContext("identityState = { resolved: true, available: true, capabilities: new Set() }", context);
  assert.equal(vm.runInContext("identityAllowsYouTubeClaim()", context), false);
  vm.runInContext("applyIdentityCapabilities()", context);
  assert.equal(vm.runInContext("youtubeClaimOpenButton.hidden", context), true);
  vm.runInContext('identityState.capabilities.add("youtube.acquire")', context);
  assert.equal(vm.runInContext("identityAllowsYouTubeClaim()", context), true);
  vm.runInContext("applyIdentityCapabilities()", context);
  assert.equal(vm.runInContext("youtubeClaimOpenButton.hidden", context), false);
});

test("retry confirmation keeps its existing copy and focus return", async () => {
  const context = evaluate(
    extractFunction(APP_SOURCE, "retryYouTubeClaim"),
    `let youtubeClaimState = {
      snapshot: { claim_id: "claim-retry-test", state: "failed" },
      requestOwner: null,
    };
    const youtubeClaimRetryButton = { marker: "retry-button" };
    let retryConfirmation = null;
    async function requestConfirmation(options) {
      retryConfirmation = options;
      return false;
    }
    function identityAllowsYouTubeClaim() { return true; }`,
  );

  await vm.runInContext("retryYouTubeClaim()", context);

  assert.equal(vm.runInContext("retryConfirmation.title", context), "Retry YouTube claim");
  assert.equal(
    vm.runInContext("retryConfirmation.message", context),
    "Retry the failed claim using the same server-owned claim context?",
  );
  assert.equal(vm.runInContext("retryConfirmation.dismissLabel", context), "Cancel");
  assert.equal(vm.runInContext("retryConfirmation.confirmLabel", context), "Retry claim");
  assert.equal(
    vm.runInContext("retryConfirmation.focusReturn === youtubeClaimRetryButton", context),
    true,
  );
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
