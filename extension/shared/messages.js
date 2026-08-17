(function (root, factory) {
  const api = factory();
  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  }
  root.FrameNestCompanion = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  const PROTOCOL = "framenest.companion.v1";
  const API_VERSION = "framenest-companion.v1";
  const MAX_ATTACH_BYTES = 32 * 1024 * 1024;
  const FETCH_TIMEOUT_MS = 60 * 1000;
  const CHUNK_BYTES = 24 * 1024;
  const UUID_PATTERN =
    /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
  const POST_ID_PATTERN = /^[0-9]{1,19}$/;
  const HANDLE_PATTERN = /^[A-Za-z0-9_]{1,64}$/;
  const X_HOSTS = new Set(["x.com", "www.x.com", "twitter.com", "www.twitter.com"]);
  const TS_ORIGIN_PATTERN = /^https:\/\/[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?)+\.ts\.net$/;
  const TYPES = Object.freeze({
    SAVE_POST: "save_post",
    POLL_CLAIM: "poll_claim",
    RECOVER_INFLIGHT: "recover_inflight",
    PICKER_QUERY: "picker_query",
    ATTACH_BEGIN: "attach_begin",
    CONFIGURE_ORIGIN: "configure_origin",
    RESET: "reset",
    IDENTITY: "identity",
    ACK: "ack",
    ERROR: "error",
    CANONICAL_TAGS: "canonical_tags",
  });

  function isProtocolMessage(value) {
    return Boolean(
      value &&
        typeof value === "object" &&
        value.v === PROTOCOL &&
        typeof value.type === "string" &&
        Object.values(TYPES).includes(value.type)
    );
  }

  function dropUnknown(value) {
    if (!isProtocolMessage(value)) {
      return null;
    }
    return value;
  }

  function isUuid(value) {
    return typeof value === "string" && UUID_PATTERN.test(value);
  }

  function acceptXPostUrl(url) {
    if (typeof url !== "string" || url.trim() !== url || url.length === 0 || url.length > 2048) {
      return null;
    }
    let parsed;
    try {
      parsed = new URL(url);
    } catch {
      return null;
    }
    if (parsed.protocol !== "https:") {
      return null;
    }
    if (parsed.username || parsed.password || parsed.search || parsed.hash) {
      return null;
    }
    const host = parsed.hostname.toLowerCase();
    if (!X_HOSTS.has(host)) {
      return null;
    }
    if (parsed.port && parsed.port !== "443") {
      return null;
    }
    const parts = parsed.pathname.split("/").filter(Boolean);
    if (parts.length !== 3 || parts[1] !== "status") {
      return null;
    }
    const handle = parts[0];
    const postId = parts[2];
    if (!HANDLE_PATTERN.test(handle) || handle.startsWith("i") || !POST_ID_PATTERN.test(postId)) {
      return null;
    }
    return {
      postId,
      submittedUrl: url,
      canonicalUrl: "https://x.com/" + handle.replace(/_+$/, "") + "/status/" + postId,
    };
  }

  function acceptFrameNestOrigin(value) {
    return typeof value === "string" && TS_ORIGIN_PATTERN.test(value);
  }

  function pathFor(name, ids) {
    const safe = ids || {};
    switch (name) {
      case "identity":
        return "/api/identity/me";
      case "companionMedia":
        return "/api/x/companion/media";
      case "xRequests":
        return "/api/x/requests";
      case "xRequest":
        if (!isUuid(safe.claimId)) {
          return null;
        }
        return "/api/x/requests/" + safe.claimId;
      case "xRetry":
        if (!isUuid(safe.claimId)) {
          return null;
        }
        return "/api/x/requests/" + safe.claimId + "/retry";
      case "canonicalTags":
        return "/api/canonical-tags";
      case "content":
        if (!isUuid(safe.mediaId) || !isUuid(safe.locationId)) {
          return null;
        }
        return (
          "/api/media/" +
          safe.mediaId +
          "/locations/" +
          safe.locationId +
          "/content"
        );
      case "preview":
        if (!isUuid(safe.mediaId) || !isUuid(safe.locationId)) {
          return null;
        }
        return (
          "/api/media/" +
          safe.mediaId +
          "/locations/" +
          safe.locationId +
          "/gallery-preview"
        );
      default:
        return null;
    }
  }

  function bytesFromBase64(chunk) {
    const binary = atob(chunk);
    const bytes = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i += 1) {
      bytes[i] = binary.charCodeAt(i);
    }
    return bytes;
  }

  function concatChunks(chunks, total) {
    const out = new Uint8Array(total);
    let offset = 0;
    for (const chunk of chunks) {
      out.set(chunk, offset);
      offset += chunk.byteLength;
    }
    return out;
  }

  return {
    PROTOCOL,
    API_VERSION,
    MAX_ATTACH_BYTES,
    FETCH_TIMEOUT_MS,
    CHUNK_BYTES,
    TYPES,
    isProtocolMessage,
    dropUnknown,
    isUuid,
    acceptXPostUrl,
    acceptFrameNestOrigin,
    pathFor,
    bytesFromBase64,
    concatChunks,
  };
});
