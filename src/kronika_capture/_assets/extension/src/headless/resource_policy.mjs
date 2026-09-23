// Bounded resource policy for headless jobs.
//
// Purpose: reduce telemetry/media/font bandwidth without touching the
// composer, submit, observation, extraction, or login. The policy is
// fail-open: when Network or Fetch setup fails, the function logs one
// bounded line and the job continues unchanged.
//
// Mechanism:
//   - deny-by-URL: Network.enable + Network.setBlockedURLs with the fixed
//     POLICY_BLOCKED_URLS list (analytics/ads/trackers);
//   - media/font: Fetch.enable with exactly the Media and Font resource types;
//     every paused request is failed with Fetch.failRequest
//     (errorReason "BlockedByClient"); if that call errors, the request is
//     continued instead, so every paused request receives exactly one
//     continuation and a handler error always continues. Document, Script,
//     XHR, Fetch, WebSocket, Stylesheet, and Image are never intercepted.
//
// Evidence is metadata only: the startup line and the per-job counters
// blocked_by_denylist, blocked_media, blocked_fonts, and policy_errors.
// There is no external canary request. Attachment upload traffic is not
// blocked.

export const POLICY_BLOCKED_URLS = Object.freeze([
  "*://www.google-analytics.com/*",
  "*://*.google-analytics.com/*",
  "*://www.googletagmanager.com/*",
  "*://*.googletagmanager.com/*",
  "*://*.doubleclick.net/*",
  "*://*.googleadservices.com/*",
  "*://connect.facebook.net/*",
  "*://*.facebook.net/*",
  "*://*.hotjar.com/*",
  "*://*.nr-data.net/*",
  "*://*.newrelic.com/*",
  "*://*.sentry-cdn.com/*",
]);

export const POLICY_BLOCK_MEDIA = true;
export const POLICY_BLOCK_FONTS = true;

export const FETCH_BLOCK_PATTERNS = Object.freeze([
  Object.freeze({ urlPattern: "*", resourceType: "Media" }),
  Object.freeze({ urlPattern: "*", resourceType: "Font" }),
]);

// Network.loadingFailed blockedReason values that prove this policy, not DNS,
// blocked the request.
export const POLICY_BLOCKED_REASONS = Object.freeze(["inspector"]);

const PENDING_URL_LIMIT = 512;

export const COUNTER_KEYS = Object.freeze([
  "blocked_by_denylist",
  "blocked_media",
  "blocked_fonts",
  "policy_errors",
]);

function matchHostPattern(hostPattern, hostname) {
  const host = String(hostname || "").toLowerCase();
  const pattern = String(hostPattern || "").toLowerCase();
  if (pattern === "*") return true;
  if (pattern.startsWith("*.")) {
    const base = pattern.slice(2);
    return host === base || host.endsWith(`.${base}`);
  }
  return host === pattern;
}

function matchPathPattern(pathPattern, pathname, search) {
  const target = `${pathname || "/"}${search || ""}`;
  const escaped = String(pathPattern || "/*")
    .replace(/[.+?^${}()|[\]\\]/g, "\\$&")
    .replace(/\*/g, ".*");
  return new RegExp(`^${escaped}$`).test(target);
}

// Match a Chromium-style URL pattern (`*://host/path`, `*` wildcard allowed)
// against an absolute URL. Unknown or malformed input never matches.
export function urlMatchesPattern(pattern, rawUrl) {
  const match = /^(\*|https?|ws|wss|ftp|file):\/\/([^/]*)(\/.*)$/.exec(
    String(pattern || "")
  );
  if (!match) return false;
  let parsed = null;
  try {
    parsed = new URL(String(rawUrl));
  } catch {
    return false;
  }
  const scheme = match[1];
  if (scheme !== "*" && scheme !== parsed.protocol.replace(/:$/, "")) {
    return false;
  }
  if (!matchHostPattern(match[2], parsed.hostname)) return false;
  return matchPathPattern(match[3], parsed.pathname, parsed.search);
}

// Deny-by-URL classifier: a URL is denied when it matches any policy pattern.
// Anything unknown is allowed (fail-open by construction).
export function isDeniedUrl(rawUrl) {
  return POLICY_BLOCKED_URLS.some((pattern) => urlMatchesPattern(pattern, rawUrl));
}

// Media/font classifier: only the two configured resource types are blocked;
// every other (or unknown) type stays allowed.
export function isBlockedResourceType(resourceType) {
  if (POLICY_BLOCK_MEDIA && resourceType === "Media") return true;
  if (POLICY_BLOCK_FONTS && resourceType === "Font") return true;
  return false;
}

function errorCode(error) {
  return error && typeof error.code === "string" && error.code
    ? error.code
    : "E_INTERNAL";
}

function boundedLog(log, line) {
  try {
    log(line);
  } catch {
    // logging must never mask the primary result
  }
}

export async function applyResourcePolicy({ driver, log = () => {} } = {}) {
  const counters = {
    blocked_by_denylist: 0,
    blocked_media: 0,
    blocked_fonts: 0,
    policy_errors: 0,
  };
  const pendingUrls = new Map();
  const fetchFailed = new Set();
  const offs = [];
  const handle = {
    blocked_url_count: POLICY_BLOCKED_URLS.length,
    deny_mode: "none",
    block_media: false,
    block_fonts: false,
    counters,
    snapshot: () => ({ ...counters }),
    dispose: () => {
      for (const off of offs.splice(0)) {
        try {
          off();
        } catch {
          // unsubscribing is best-effort
        }
      }
    },
  };

  const rememberUrl = (requestId, url) => {
    if (typeof requestId !== "string" || typeof url !== "string") return;
    pendingUrls.set(requestId, url);
    if (pendingUrls.size > PENDING_URL_LIMIT) {
      pendingUrls.delete(pendingUrls.keys().next().value);
    }
  };
  const rememberFetchFailed = (requestId) => {
    if (typeof requestId !== "string") return;
    fetchFailed.add(requestId);
    if (fetchFailed.size > PENDING_URL_LIMIT) {
      fetchFailed.delete(fetchFailed.values().next().value);
    }
  };

  const onRequestWillBeSent = (params) => {
    if (!params) return;
    rememberUrl(
      params.requestId,
      params.request && params.request.url
    );
  };

  const onLoadingFailed = (params) => {
    if (!params) return;
    const requestId = params.requestId;
    const url = typeof requestId === "string" ? pendingUrls.get(requestId) : null;
    if (typeof requestId === "string") pendingUrls.delete(requestId);
    if (typeof requestId === "string" && fetchFailed.has(requestId)) {
      // already counted as a media/font block; the policy caused this failure
      fetchFailed.delete(requestId);
      return;
    }
    if (!POLICY_BLOCKED_REASONS.includes(params.blockedReason)) return;
    if (typeof url === "string" && isDeniedUrl(url)) {
      counters.blocked_by_denylist += 1;
    }
  };

  const continueOnce = (requestId) => {
    try {
      return driver
        .send("Fetch.continueRequest", { requestId })
        .catch(() => {
          counters.policy_errors += 1;
        });
    } catch (error) {
      counters.policy_errors += 1;
      return Promise.resolve();
    }
  };

  const failThenContinue = (requestId) => {
    try {
      return driver
        .send("Fetch.failRequest", {
          requestId,
          errorReason: "BlockedByClient",
        })
        .catch(() => {
          // the fail answer errored; the request is continued instead so it
          // never stays paused
          counters.policy_errors += 1;
          return continueOnce(requestId);
        });
    } catch (error) {
      counters.policy_errors += 1;
      return continueOnce(requestId);
    }
  };

  const handlePaused = (params) => {
    const requestId = params && params.requestId;
    if (typeof requestId !== "string") return;
    const resourceType = params.resourceType;
    if (!isBlockedResourceType(resourceType)) {
      // defensive: only Media/Font are ever intercepted; anything else is
      // released immediately
      continueOnce(requestId);
      return;
    }
    if (resourceType === "Media") counters.blocked_media += 1;
    else counters.blocked_fonts += 1;
    rememberFetchFailed(requestId);
    failThenContinue(requestId);
  };

  const onRequestPaused = (params) => {
    try {
      handlePaused(params);
    } catch (error) {
      counters.policy_errors += 1;
      if (params && typeof params.requestId === "string") {
        continueOnce(params.requestId);
      }
    }
  };

  // 1. Deny-by-URL through the Network domain. The request/failure events also
  // feed the canary rule and the denylist counter.
  try {
    await driver.send("Network.enable");
    await driver.send("Network.setBlockedURLs", { urls: POLICY_BLOCKED_URLS });
    handle.deny_mode = "Network.setBlockedURLs";
    if (typeof driver.on === "function") {
      offs.push(driver.on("Network.requestWillBeSent", onRequestWillBeSent));
      offs.push(driver.on("Network.loadingFailed", onLoadingFailed));
    }
  } catch (error) {
    counters.policy_errors += 1;
    boundedLog(
      log,
      `resource_policy network setup failed (${errorCode(error)}); continuing without it`
    );
  }

  // 2. Media/font blocking through the Fetch domain (Media and Font only).
  try {
    await driver.send("Fetch.enable", { patterns: FETCH_BLOCK_PATTERNS });
    handle.block_media = POLICY_BLOCK_MEDIA;
    handle.block_fonts = POLICY_BLOCK_FONTS;
    if (typeof driver.on === "function") {
      offs.push(driver.on("Fetch.requestPaused", onRequestPaused));
    }
  } catch (error) {
    counters.policy_errors += 1;
    boundedLog(
      log,
      `resource_policy fetch setup failed (${errorCode(error)}); continuing without it`
    );
  }

  if (handle.deny_mode !== "none") {
    boundedLog(log, `resource_policy deny mechanism=${handle.deny_mode}`);
  }
  if (handle.deny_mode !== "none" && handle.block_media && handle.block_fonts) {
    boundedLog(
      log,
      `resource_policy active blocked_urls=${POLICY_BLOCKED_URLS.length} media=on fonts=on`
    );
  } else {
    boundedLog(
      log,
      `resource_policy degraded blocked_urls=${
        handle.deny_mode === "none" ? 0 : POLICY_BLOCKED_URLS.length
      } media=${handle.block_media ? "on" : "off"} fonts=${
        handle.block_fonts ? "on" : "off"
      } (fail-open)`
    );
  }

  return handle;
}
