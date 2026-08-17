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

test("adapter contract exposes frozen action-bar, Share, and media-host selectors", () => {
  assert.equal(contract.adapterVersion, 1);
  assert.ok(Object.isFrozen(contract.actionGroupSelectors));
  assert.ok(Object.isFrozen(contract.actionBarSignals));
  assert.ok(Object.isFrozen(contract.shareSelectors));
  assert.ok(Object.isFrozen(contract.mediaHostSelectors));
  assert.ok(Object.isFrozen(contract.composerChromeSelectors));
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
  assert.deepEqual(contract.mediaHostSelectors, [
    "[data-testid='tweetPhoto']",
    "[data-testid='videoPlayer']",
    "[data-testid='videoComponent']",
    "[data-framenest-media]",
  ]);
  assert.deepEqual(contract.composerChromeSelectors, ["[data-framenest-composer-chrome]"]);
});

test("in-feed Save is a per-media hover overlay, not an action-row control", () => {
  const fixture = fs.readFileSync(
    path.join(REPO, "tests/support/x_fixtures/composer.html"),
    "utf8"
  );
  assert.match(fixture, /role="group"/);
  assert.match(fixture, /data-testid="reply"/);
  assert.match(fixture, /data-testid="retweet"/);
  assert.match(fixture, /data-testid="like"/);
  assert.match(fixture, /aria-label="Share post"/);
  assert.match(fixture, /data-testid="tweetPhoto"/);
  assert.match(fixture, /data-framenest-media/);
  assert.doesNotMatch(fixture, /data-framenest-companion/);

  assert.doesNotMatch(adapterSource, /writing-mode/);
  assert.doesNotMatch(adapterSource, /addButton\(\s*postRoot/);
  assert.doesNotMatch(adapterSource, /postRoot\.appendChild/);
  assert.doesNotMatch(adapterSource, /textContent\s*=\s*result/);
  assert.doesNotMatch(adapterSource, /textContent\s*=\s*["']Save to FrameNest["']/);
  assert.doesNotMatch(adapterSource, /textContent\s*=\s*["']Saving/);
  assert.doesNotMatch(adapterSource, /ownActionGroup/);
  assert.doesNotMatch(adapterSource, /shareActionColumn/);
  assert.doesNotMatch(adapterSource, /SAVE_DOWN_NUDGE/);
  assert.doesNotMatch(adapterSource, /insertAdjacentElement\("afterend"/);
  assert.doesNotMatch(adapterSource, /return "missing_bar"/);
  assert.doesNotMatch(adapterSource, /return "missing_share"/);
  assert.doesNotMatch(adapterSource, /adapter_drift/);
  assert.doesNotMatch(adapterSource, /style\.background = "transparent"/);
  assert.doesNotMatch(
    adapterSource,
    /\[data-framenest-companion='save'\][\s\S]{0,500}background:\s*transparent/
  );
  assert.match(adapterSource, /setAttribute\("data-framenest-companion", "save"\)/);
  assert.match(adapterSource, /setAttribute\("aria-label", name\)/);
  assert.match(adapterSource, /stopImmediatePropagation/);
  assert.match(adapterSource, /ownMediaHosts/);
  assert.match(adapterSource, /mediaHostSelectors/);
  assert.match(adapterSource, /data-framenest-media-host/);
  assert.match(adapterSource, /data-framenest-companion-style/);
  assert.match(adapterSource, /position: absolute/);
  assert.match(adapterSource, /top: 0/);
  assert.match(adapterSource, /left: 0/);
  assert.match(adapterSource, /opacity: 0/);
  assert.match(adapterSource, /pointer-events: none/);
  assert.match(adapterSource, /background: #000000/);
  assert.match(adapterSource, /style\.position = "relative"/);
  assert.match(adapterSource, /return "no_media"/);
  assert.match(adapterSource, /TYPES\.SAVE_POST/);
  assert.match(adapterSource, /accepted\.submittedUrl/);
  assert.doesNotMatch(adapterSource, /pbs\.twimg\.com/);
  assert.match(adapterSource, /data-framenest-companion"\) === "save"/);
  assert.match(adapterSource, /Save to FrameNest failed/);
});

test("companion surfaces copy FrameNest gallery visual tokens", () => {
  const pickerCss = fs.readFileSync(path.join(REPO, "extension/ui/picker.css"), "utf8");
  const pickerHtml = fs.readFileSync(path.join(REPO, "extension/ui/picker.html"), "utf8");
  const pickerJs = fs.readFileSync(path.join(REPO, "extension/ui/picker.js"), "utf8");
  const tokenNames = [
    "--background",
    "--surface",
    "--surface-input",
    "--text",
    "--text-muted",
    "--text-soft",
    "--accent",
    "--accent-strong",
    "--accent-soft",
    "--accent-border",
    "--accent-glow",
    "--danger",
    "--focus",
    "--radius-sm",
    "--font-mono",
  ];
  tokenNames.forEach((token) => {
    assert.match(pickerCss, new RegExp(token.replace(/-/g, "\\-")));
  });
  assert.match(pickerCss, /#00ff41/);
  assert.match(pickerCss, /#39ff14/);
  assert.match(adapterSource, /#00ff41/);
  assert.match(adapterSource, /#39ff14/);
  assert.doesNotMatch(adapterSource, /copyActionColor/);
  assert.doesNotMatch(adapterSource, /getComputedStyle\([^)]+\)\.color/);
  assert.doesNotMatch(adapterSource, /rgba\(127, 127, 127, 0\.12\)/);
  assert.match(adapterSource, /GALLERY_ACCENT/);
  assert.match(pickerHtml, /header-search__control/);
  assert.match(pickerHtml, /header-search__prompt/);
  assert.match(pickerHtml, /id="preview"/);
  assert.match(pickerHtml, /id="preview-prev"/);
  assert.match(pickerHtml, /id="preview-next"/);
  assert.doesNotMatch(pickerJs, /innerHTML/);
  assert.doesNotMatch(pickerJs, /form\.submit/);
});

test("Attach is flush in the composer chrome corner, not a disclosure sibling", () => {
  const fixture = fs.readFileSync(
    path.join(REPO, "tests/support/x_fixtures/composer.html"),
    "utf8"
  );
  assert.ok(Object.isFrozen(contract.composerToolbarSelectors));
  assert.deepEqual(contract.composerToolbarSelectors, [
    "[data-testid='toolBar']",
    "[data-framenest-composer-toolbar]",
  ]);
  assert.ok(Object.isFrozen(contract.contentDisclosureSelectors));
  assert.deepEqual(contract.contentDisclosureSelectors, [
    "[aria-label='Content disclosure']",
    "[data-framenest-content-disclosure]",
  ]);
  assert.ok(Object.isFrozen(contract.bookmarkSelectors));
  assert.match(fixture, /data-testid="toolBar"/);
  assert.match(fixture, /data-framenest-composer-toolbar/);
  assert.match(fixture, /data-framenest-composer-chrome/);
  assert.match(fixture, /data-testid="bookmark"/);
  assert.match(fixture, /aria-label="Content disclosure"/);
  assert.match(fixture, /data-framenest-content-disclosure/);
  assert.doesNotMatch(adapterSource, /addButton\(/);
  assert.doesNotMatch(adapterSource, /composerRoot\.appendChild/);
  assert.doesNotMatch(adapterSource, /insertAttachAfterDisclosure/);
  assert.doesNotMatch(adapterSource, /findContentDisclosure/);
  assert.doesNotMatch(adapterSource, /disclosureActionColumn/);
  assert.doesNotMatch(adapterSource, /tweetButton/);
  assert.doesNotMatch(adapterSource, /form\.submit/);
  assert.doesNotMatch(adapterSource, /dispatchEvent\(new Event\(["']submit/);
  assert.match(adapterSource, /findComposerChrome/);
  assert.match(adapterSource, /composerChromeSelectors/);
  assert.match(adapterSource, /setAttribute\("data-framenest-companion", "attach"\)/);
  assert.match(adapterSource, /setAttribute\("aria-label", ATTACH_NAME\)/);
  assert.match(adapterSource, /right: 0/);
  assert.match(adapterSource, /bottom: 0/);
  assert.doesNotMatch(adapterSource, /textContent\s*=\s*["']Attach from FrameNest["']/);
  assert.doesNotMatch(adapterSource, /textContent\s*=\s*ATTACH_NAME/);
});

test("picker is search-first with a Settings Origin sheet", () => {
  const pickerHtml = fs.readFileSync(path.join(REPO, "extension/ui/picker.html"), "utf8");
  const pickerJs = fs.readFileSync(path.join(REPO, "extension/ui/picker.js"), "utf8");
  const pickerCss = fs.readFileSync(path.join(REPO, "extension/ui/picker.css"), "utf8");
  assert.doesNotMatch(pickerHtml, /Search titles/);
  assert.doesNotMatch(pickerJs, /Search titles/);
  assert.doesNotMatch(pickerHtml, /class="picker-brand"/);
  assert.doesNotMatch(pickerHtml, /class="brand-mark"/);
  assert.doesNotMatch(pickerHtml, /<h1>FrameNest<\/h1>/);
  assert.doesNotMatch(pickerHtml, />FN<\/span>/);
  assert.match(pickerHtml, /Search memes/);
  assert.match(pickerHtml, /aria-label="Settings"/);
  assert.match(pickerHtml, /id="settings-tab-origin"/);
  assert.match(pickerHtml, /id="settings-dialog"/);
  assert.match(pickerHtml, /class="settings-dialog"/);
  assert.match(pickerHtml, /role="tablist"/);
  assert.match(pickerCss, /--surface-solid:/);
  assert.match(pickerCss, /--line:/);
  assert.match(pickerCss, /--radius-lg:/);
  assert.match(pickerCss, /--shadow-deep:/);
  assert.match(pickerCss, /--danger-soft:/);
  assert.match(pickerCss, /--transition-fast:/);
  assert.match(pickerCss, /\.settings-dialog__tab--active/);
  assert.match(pickerJs, /showModal/);
  assert.match(pickerJs, /openSettings/);
  assert.match(pickerJs, /closeSettings/);
  assert.match(pickerJs, /renderConnection/);
  assert.doesNotMatch(pickerJs, /innerHTML/);
  assert.doesNotMatch(pickerJs, /form\.submit/);
  assert.doesNotMatch(adapterSource, /tweetButton/);
});
