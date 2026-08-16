const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");

const REPO = path.resolve(__dirname, "..");
const companion = require(path.join(REPO, "extension/shared/messages.js"));
const contract = require(path.join(REPO, "extension/content/x_adapter_contract_v1.js"));
const adapterSource = fs.readFileSync(
  path.join(REPO, "extension/content/x_adapter.js"),
  "utf8"
);
const workerSource = fs.readFileSync(
  path.join(REPO, "extension/background/service_worker.js"),
  "utf8"
);
const manifest = JSON.parse(
  fs.readFileSync(path.join(REPO, "extension/manifest.json"), "utf8")
);

test("unknown protocol versions and types are dropped", () => {
  assert.equal(companion.dropUnknown({ v: "other", type: companion.TYPES.SAVE_POST }), null);
  assert.equal(companion.dropUnknown({ v: companion.PROTOCOL, type: "proxy_fetch" }), null);
  assert.equal(companion.dropUnknown({ url: "https://evil.example" }), null);
  assert.ok(
    companion.dropUnknown({
      v: companion.PROTOCOL,
      type: companion.TYPES.SAVE_POST,
      payload: { url: "https://x.com/a/status/1" },
    })
  );
});

test("service worker path templates reject caller-supplied URLs and ids", () => {
  assert.equal(companion.pathFor("content", { mediaId: "https://evil.example", locationId: "x" }), null);
  assert.equal(companion.pathFor("xRequest", { claimId: "../etc/passwd" }), null);
  assert.equal(
    companion.pathFor("content", {
      mediaId: "11111111-1111-4111-8111-111111111111",
      locationId: "22222222-2222-4222-8222-222222222222",
    }),
    "/api/media/11111111-1111-4111-8111-111111111111/locations/22222222-2222-4222-8222-222222222222/content"
  );
  assert.equal(companion.pathFor("identity"), "/api/identity/me");
  assert.match(workerSource, /pathFor\(/);
  assert.doesNotMatch(workerSource, /fetch\(payload\.url\)/);
  assert.doesNotMatch(workerSource, /fetch\(message\.url\)/);
});

test("X URL allowlist accepts only public https post permalinks", () => {
  assert.ok(companion.acceptXPostUrl("https://x.com/fixture/status/123456789"));
  assert.equal(companion.acceptXPostUrl("https://evil.example/fixture/status/123456789"), null);
  assert.equal(companion.acceptXPostUrl("https://x.com/i/web/status/123456789"), null);
  assert.equal(companion.acceptXPostUrl("https://x.com/fixture/status/123456789?foo=1"), null);
});

test("adapter contract has no Post-button or auto-submit path", () => {
  const serialized = JSON.stringify(contract);
  assert.equal(serialized.includes("tweetButton"), false);
  assert.equal("postButton" in contract, false);
  assert.doesNotMatch(adapterSource, /tweetButton/);
  assert.doesNotMatch(adapterSource, /form\.submit/);
  assert.doesNotMatch(adapterSource, /dispatchEvent\(new Event\(["']submit/);
  assert.match(adapterSource, /DataTransfer/);
  assert.match(adapterSource, /pollClaim/);
  assert.match(adapterSource, /RECOVER_INFLIGHT/);
});

test("manifest permissions stay minimized and omit X host access", () => {
  assert.deepEqual(manifest.permissions.sort(), ["sidePanel", "storage"]);
  assert.deepEqual(manifest.optional_permissions, ["downloads"]);
  assert.deepEqual(manifest.optional_host_permissions, ["https://*.ts.net/*"]);
  assert.equal("host_permissions" in manifest, false);
  assert.equal("externally_connectable" in manifest, false);
  assert.equal((manifest.permissions || []).includes("tabs"), false);
  assert.equal((manifest.permissions || []).includes("alarms"), false);
  assert.equal((manifest.permissions || []).includes("cookies"), false);
  const matches = manifest.content_scripts[0].matches.sort();
  assert.deepEqual(matches, ["https://twitter.com/*", "https://x.com/*"]);
});

test("chunk reassembly stays bounded", () => {
  const first = companion.bytesFromBase64(Buffer.from("abc").toString("base64"));
  const second = companion.bytesFromBase64(Buffer.from("def").toString("base64"));
  const joined = companion.concatChunks([first, second], 6);
  assert.equal(Buffer.from(joined).toString(), "abcdef");
  assert.equal(companion.MAX_ATTACH_BYTES, 32 * 1024 * 1024);
});

test("service worker recovers inflight claim ids from storage", () => {
  assert.match(workerSource, /inflightClaims/);
  assert.match(workerSource, /RECOVER_INFLIGHT/);
  assert.doesNotMatch(workerSource, /setInterval/);
});

test("adapter contract exposes frozen action-bar and Share selectors", () => {
  assert.equal(contract.adapterVersion, 1);
  assert.ok(Object.isFrozen(contract.actionGroupSelectors));
  assert.ok(Object.isFrozen(contract.actionBarSignals));
  assert.ok(Object.isFrozen(contract.shareSelectors));
  assert.deepEqual(contract.actionGroupSelectors, ["[role='group']"]);
  assert.deepEqual(contract.actionBarSignals, [
    "[data-testid='reply']",
    "[data-testid='retweet']",
    "[data-testid='like']",
  ]);
  assert.deepEqual(contract.shareSelectors, [
    "[data-testid='share']",
    "[aria-label='Share post']",
    "[aria-label='Share']",
  ]);
});

test("in-feed Save is an action-row icon and never a labeled article button", () => {
  const fixture = fs.readFileSync(
    path.join(REPO, "tests/support/x_fixtures/composer.html"),
    "utf8"
  );
  assert.match(fixture, /role="group"/);
  assert.match(fixture, /data-testid="reply"/);
  assert.match(fixture, /data-testid="retweet"/);
  assert.match(fixture, /data-testid="like"/);
  assert.match(fixture, /aria-label="Share post"/);
  assert.doesNotMatch(fixture, /data-framenest-companion/);

  assert.doesNotMatch(adapterSource, /writing-mode/);
  assert.doesNotMatch(adapterSource, /addButton\(\s*postRoot/);
  assert.doesNotMatch(adapterSource, /postRoot\.appendChild/);
  assert.doesNotMatch(adapterSource, /textContent\s*=\s*result/);
  assert.doesNotMatch(adapterSource, /textContent\s*=\s*["']Save to FrameNest["']/);
  assert.doesNotMatch(adapterSource, /textContent\s*=\s*["']Saving/);
  assert.match(adapterSource, /setAttribute\("data-framenest-companion", "save"\)/);
  assert.match(adapterSource, /setAttribute\("aria-label", name\)/);
  assert.match(adapterSource, /insertAdjacentElement\("afterend"/);
  assert.match(adapterSource, /stopImmediatePropagation/);
  assert.match(adapterSource, /ownActionGroup/);
  assert.match(adapterSource, /shareActionColumn/);
  assert.match(adapterSource, /return "missing_bar"/);
  assert.match(adapterSource, /return "missing_share"/);
  assert.match(adapterSource, /adapter_drift/);
  assert.match(adapterSource, /data-framenest-companion"\) === "save"/);
  assert.match(adapterSource, /Save to FrameNest failed/);
});
